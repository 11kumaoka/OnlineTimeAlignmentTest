#!/usr/bin/env python3
"""Summarize independent signed-tilt cohorts without selecting on closure success.

Truth is read only for this offline validation, never for alignment inference.
Paired signs/axes share rays within a seed and are not independent experiments.
"""
import argparse
import hashlib
import json
import statistics
import math
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_common import REPO, write_json, digest
from alignment.pede import read_pede
from validation.telescope_closure.rotation import rotation_label,labels,is_coupled,is_three


def read_run(run):
    fixture = json.loads((run/'geometry/rotation_fixture.json').read_text())
    mode = fixture['mode']
    coupled = is_coupled(mode)
    selected = labels(mode)
    label = None if coupled else rotation_label(mode)
    if not coupled and selected != [label]:raise ValueError('Cohort summary requires a selected single or coupled rotation scope')
    injection = fixture['injected_rotation_vector_rad'][(0 if is_three(mode) else 1):] if coupled else next(v['1'] for k, v in fixture.items() if k.startswith('injected_global_r'))
    truth = json.loads((run/'data/shifted/channels_truth.json').read_text())
    recipe = dict(truth['beam_recipe'])
    seed = recipe.pop('seed')
    recipe.pop('description', None)
    rays = [(e['origin_mm'], e['direction']) for e in truth['events']]
    item = {'run': str(run), 'mode': mode, 'seed': seed, 'angular_recipe': recipe,
            'ray_cohort_sha256': hashlib.sha256(json.dumps(rays).encode()).hexdigest(),
            'channel_sha256': json.loads((run/'data/shifted_input.json').read_text())['channel_payload_sha256'],
            'injected_rad': injection, 'passed_closure': False}
    slopes = [[d[1][j]/d[1][0] for j in (1,2)] for d in rays]
    item['generated_slopes'] = {'min': [min(p[j] for p in slopes) for j in (0,1)],
        'max': [max(p[j] for p in slopes) for j in (0,1)],
        'rms': [math.sqrt(statistics.mean(p[j]**2 for p in slopes)) for j in (0,1)]}
    audit = run/'nominal/audit.json'
    if audit.exists():item['accepted_tracks'] = json.loads(audit.read_text())['accepted']
    if (run/'solve/independent.json').exists():
        solution = json.loads((run/'solve/independent.json').read_text())
        parameters = read_pede(run/'solve/millepede.res')
        if coupled:
            value = [parameters[k] for k in selected]
            sigma = solution['nominal_sigma']
            item.update(fitted_rad=value, nominal_sigma_rad=sigma,
                pede_reported_sigma_rad=solution['pede_reported_sigma'],
                truth_minus_fit_rad=[a-b for a,b in zip(injection,value)],
                pull=[(b-a)/s for a,b,s in zip(injection,value,sigma)],
                correlation=solution['correlation'],covariance_rad2=np.linalg.inv(solution['normal']).tolist())
        else:
            value = parameters[label]
            sigma = solution['nominal_sigma'][0]
            item.update(fitted_rad=value, nominal_sigma_rad=sigma,
                        pede_reported_sigma_rad=solution['pede_reported_sigma'][0],
                        truth_minus_fit_rad=injection-value, pull=(value-injection)/sigma)
        item['pede_status'] = (run/'solve/millepede.end').read_text().strip()
    final = run/'validation/report.json'
    if final.exists():
        report = json.loads(final.read_text())
        item.update(passed_closure=report['passed'], accepted_tracks=report['summaries']['nominal']['accepted'],
                    post_update_rad=([report['post_correction'][str(k)] for k in selected] if coupled else report['post_correction'][str(label)]),
                    acts_before=report['summaries']['nominal']['chi2_per_stored_ndf'],
                    acts_after=report['summaries']['corrected']['chi2_per_stored_ndf'],
                    report_sha256=digest(final), pede_diagnostics=report['pede_diagnostics'])
        if coupled:item.update(orientation_error_rad=report['orientation_error_rad'],initial_error_mahalanobis_squared=report['initial_error_mahalanobis_squared'])
    else:
        item['missing_completed_stages'] = [s for s in ('solve','correction','corrected','postsolve','control','controlsolve','validation')
                                             if not (run/s/'complete.json').exists()]
        design = run/'solve/observability.json'
        if design.exists():
            item['refusal_design'] = json.loads(design.read_text())['prefix_designs'][str(len(truth['events']))]
    return item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, nargs='+', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if not output.is_relative_to(REPO/'result') or output == REPO/'result':
        parser.error('Output must be a new child directory of result/')
    items = [read_run(p.resolve()) for p in args.runs]
    groups = {}
    for item in items:
        if is_coupled(item['mode']):
            for index,parameter in enumerate(('Rx','Ry','Rz') if is_three(item['mode']) else ('Ry','Rz')):
                row=dict(item)
                for key in ('injected_rad','fitted_rad','nominal_sigma_rad','pede_reported_sigma_rad',
                            'truth_minus_fit_rad','pull','post_update_rad'):
                    if key in row:row[key]=row[key][index]
                groups.setdefault(item['mode']+'_'+parameter,[]).append(row)
        else:groups.setdefault(item['mode'], []).append(item)
    summaries = {}
    for mode, group in groups.items():
        assert len({r['seed'] for r in group}) == len(group), 'Repeated seeds are not independent'
        assert len({r['ray_cohort_sha256'] for r in group}) == len(group)
        assert all(r['angular_recipe'] == group[0]['angular_recipe'] for r in group)
        fitted = [r for r in group if 'fitted_rad' in r]
        errors = [r['truth_minus_fit_rad'] for r in fitted]
        pulls = [r['pull'] for r in fitted]
        summaries[mode] = {'attempted': len(group), 'initial_fits': len(fitted),
                          'successful_closures': sum(r['passed_closure'] for r in group),
                          'truth_minus_fit_mean_rad': statistics.mean(errors) if errors else None,
                          'truth_minus_fit_sample_sd_rad': statistics.stdev(errors) if len(errors)>1 else None,
                          'mean_nominal_sigma_rad': statistics.mean(r['nominal_sigma_rad'] for r in fitted) if fitted else None,
                          'pull_mean': statistics.mean(pulls) if pulls else None,
                          'pull_sample_sd': statistics.stdev(pulls) if len(pulls)>1 else None}
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'report.json', {'runs': items, 'summaries': summaries,
               'pull_convention': '(initial Pede fit - injected physical rotation) / initial unscaled nominal sigma',
               'independent_seeds': sorted({r['seed'] for r in items}),
               'paired_signs_and_axes_are_independent': False,
               'failed_closures_excluded_from_initial_fit_statistics': False,
               'coverage_validated': False})
    import ROOT
    ROOT.gROOT.SetBatch(True)
    root = ROOT.TFile.Open(str(output/'cohorts.root'), 'NEW')
    assert root and not root.IsZombie()
    for mode, group in groups.items():
        graph = ROOT.TGraphErrors()
        graph.SetName(mode+'_estimates')
        graph.SetTitle(mode+';Seed suffix (2026102400 + x);Initial Pede rotation [mrad]')
        pulls = ROOT.TH1D(mode+'_pulls', mode+';Initial-fit Pull;Cohorts', 40, -5, 5)
        for row in group:
            if 'fitted_rad' not in row:
                continue
            i = graph.GetN()
            graph.SetPoint(i, row['seed']-2026102400, row['fitted_rad']*1000)
            graph.SetPointError(i, 0, row['nominal_sigma_rad']*1000)
            pulls.Fill(row['pull'])
        graph.Write(); pulls.Write()
    root.Close()
    root = ROOT.TFile.Open(str(output/'cohorts.root'))
    assert root.GetListOfKeys().GetEntries() == 2*len(groups)
    for mode, group in groups.items():
        count = sum('fitted_rad' in r for r in group)
        assert root.Get(mode+'_estimates').GetN() == count
        assert root.Get(mode+'_pulls').GetEntries() == count
    root.Close()
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    main()
