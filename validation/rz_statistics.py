"""Summarize an independent-seed Rz ensemble; Truth is used only here.

Run in the EIC container: python3 -m validation.rz_statistics --study result/STUDY.
All analysis outputs are created exclusively in a new analysis directory.
"""
import argparse
from collections import Counter
import json
import math
import re
from pathlib import Path
import awkward as ak
import numpy as np
import uproot
from scipy import stats
from research_common import digest
from visualization.rz_statistics import plot
from geometry.placements import placement_transforms


def exclusive_json(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)


def track_metrics(path):
    with uproot.open(path) as root:
        tree=root['events'];prefix='LocalBeamTestTracks/LocalBeamTestTracks.'
        chi=np.asarray(ak.flatten(tree[prefix+'chi2'].array()))
        ndf=np.asarray(ak.flatten(tree[prefix+'ndf'].array()))
        return {'tracks':len(chi),'chi2':float(chi.sum()),'stored_ndf':int(ndf.sum()),
                'chi2_over_stored_ndf':float(chi.sum()/ndf.sum())}


def pede_metrics(directory):
    complete=json.loads((directory/'complete.json').read_text())
    log=(directory/'millepede.log').read_text()
    match=re.search(r'Sum\(Chi\^2\)/Sum\(Ndf\)\s*=\s*([\d.Ee+\-]+)\s*/\s*\(\s*(\d+)\s*-\s*(\d+)\s*\)\s*=\s*([\d.Ee+\-]+)',log)
    if not match:raise ValueError('Unparsed Pede chi2: '+str(directory))
    rows=[]
    for line in log.splitlines():
        m=re.match(r'^\s*(\d+)\s+(\d+)\s+.*?\s+(\d+)\s+\d{5,6}\s+([FMS ]*)$',line)
        if m:rows.append({'iteration':int(m[1]),'calls':int(m[2]),'rejected_local_fits':int(m[3]),'flags':m[4].strip()})
    if not rows:raise ValueError('Unparsed Pede rejection history: '+str(directory))
    warnings=[line.strip() for line in log.splitlines() if re.search(r'warn|reject|bad measurement|rank defect',line,re.I)]
    stdout=(directory/'stdout.log').read_text()
    stdout_warnings=[line.strip() for line in stdout.splitlines() if re.search(r'warn|reject|bad|should be|large.*chi',line,re.I)]
    return {'status':complete['status'],'process_exit':json.loads((directory/'exit.json').read_text()),
            'chi2':float(match[1]),'ndf':int(match[2])-int(match[3]),'chi2_ndf':float(match[4]),
            'rejection_history':rows,'final_rejection_reasons':log.split('Data records rejected in last iteration:')[-1].split('\n\n')[0].strip() if 'Data records rejected in last iteration:' in log else None,'max_rejected_local_fits':max(r['rejected_local_fits'] for r in rows),
            'final_rejected_local_fits':rows[-1]['rejected_local_fits'],'diagnostic_lines':warnings,'stdout_warning_lines':stdout_warnings,
            'parameters':complete['parameters_by_label'],'sigma_rad':complete['rotation_sigma_rad']}


def summarize(values):
    x=np.asarray(values,dtype=float);n=len(x);mean=float(x.mean());sd=float(x.std(ddof=1))
    half=float(stats.t.ppf(.975,n-1)*sd/math.sqrt(n))
    return {'n':n,'mean':mean,'sample_sd':sd,'rms_about_zero':float(np.sqrt(np.mean(x*x))),'rms_about_mean':float(np.sqrt(np.mean((x-mean)**2))),
            'mean_95ci':[mean-half,mean+half],
            'sd_95ci_normal_assumption':[sd*math.sqrt((n-1)/stats.chi2.ppf(.975,n-1)),sd*math.sqrt((n-1)/stats.chi2.ppf(.025,n-1))],
            'min':float(x.min()),'max':float(x.max())}


def collect(base):
    success=json.loads((base/'success.json').read_text());report=json.loads(Path(success['report']).read_text())
    iterations=[]
    for iteration in report['iterations']:
        stage=Path(iteration['run']);pede=pede_metrics(stage/'step4')
        done=json.loads((stage/'step3/complete.json').read_text())
        assert done['raw_input_sha256']==success['raw_sha256']==iteration['raw_sha256']
        iterations.append({'controller':iteration,'pede':pede,'acts':track_metrics(stage/'step3/reco.root')})
    raw=base/'input/rawhits.edm4eic.root';assert digest(raw)==success['raw_sha256']
    transforms=placement_transforms(Path(success['candidate']))
    final_angles={f'L{layer}':math.atan2(transforms[layer].rotation[1][0],transforms[layer].rotation[0][0]) for layer in [1,2]}
    for layer,angle in final_angles.items():
        assert abs(angle-report['iterations'][-1]['applied_rad_by_component'][layer+'_rz'])<1e-12

    return {**success,'directory':str(base),'converged':report['converged'],'iterations':iterations,'events_without_tracks':100-iterations[0]['acts']['tracks'],
            'final_acts':track_metrics(base/'final_reco/step3/reco.root'),
            'final_serialized_geometry_rad':final_angles,'source_config':json.loads((base/'beam.json').read_text()),
            'simulation_sha256':digest(base/'physical/step2/events.edm4hep.root'),
            'geometry_versions':{'initial':report['initial_geometry'],'candidate':report['candidate_geometry']}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);a=p.parse_args()
    out=a.study/'analysis';out.mkdir()
    design=json.loads((a.study/'study.json').read_text())
    records=[collect(path.parent) for path in sorted(a.study.glob('sample_*/success.json')) if json.loads(path.read_text())['independent']]
    assert len({r['seed'] for r in records})==len(records)
    assert {r['seed'] for r in records}==set(design['seeds']),'Ensemble incomplete'
    summary={'samples':len(records),'seeds':[r['seed'] for r in records],'layers':{},'track_counts':summarize([r['iterations'][0]['acts']['tracks'] for r in records])}
    rng=np.random.default_rng(design['bootstrap_seed'])
    for layer,truth in design['truth_rad'].items():
        label=str(3000+int(layer[1:]));component=layer+'_rz'
        estimate=np.array([-r['iterations'][0]['pede']['parameters'][label] for r in records])
        errors=np.array([r['iterations'][0]['pede']['sigma_rad'][label] for r in records])
        pull=(estimate-truth)/errors
        final=np.array([r['final_serialized_geometry_rad'][layer] for r in records])
        counts=np.array([r['iterations'][0]['acts']['tracks'] for r in records]);reject=np.array([r['iterations'][0]['pede']['max_rejected_local_fits'] for r in records])
        boot=rng.integers(0,len(records),size=(20000,len(records)))
        def correlation(x,y):
            if np.ptp(x)==0 or np.ptp(y)==0:return None
            v=stats.pearsonr(x,y);ci=v.confidence_interval()
            return {'r':float(v.statistic),'p_value':float(v.pvalue),'95ci':[float(ci.low),float(ci.high)]}
        summary['layers'][layer]={'truth_rad':truth,'initial_estimate_rad':summarize(estimate),'initial_bias_rad':summarize(estimate-truth),
            'nominal_sigma_rad':summarize(errors),'pull':summarize(pull),'final_cumulative_rad':summarize(final),
            'final_bias_rad':summarize(final-truth),'pull_sd_bootstrap_95ci':np.quantile(pull[boot].std(axis=1,ddof=1),[.025,.975]).tolist(),
            'bias_bootstrap_95ci_rad':np.quantile((estimate[boot]-truth).mean(axis=1),[.025,.975]).tolist(),
            'bias_vs_tracks':correlation(estimate-truth,counts),'absolute_pull_vs_tracks':correlation(np.abs(pull),counts),'pull_vs_tracks':correlation(pull,counts),'sigma_vs_tracks':correlation(errors,counts),'pull_vs_max_rejects':correlation(pull,reject),
            'coverage_1sigma':int(np.sum(np.abs(pull)<=1)),'coverage_1_96sigma':int(np.sum(np.abs(pull)<=1.96)),
            'coverage_1_96sigma_95ci':list(map(float,stats.binomtest(int(np.sum(np.abs(pull)<=1.96)),len(pull)).proportion_ci())),
            'unusual_pulls':[{'seed':r['seed'],'pull':float(v),'tracks':int(c),'max_rejected_local_fits':int(j),'status':r['iterations'][0]['pede']['status']} for r,v,c,j in zip(records,pull,counts,reject) if abs(v)>3]}
        for r,e,s,v,f in zip(records,estimate,errors,pull,final):r.setdefault('statistics',{})[layer]={'initial_estimate_rad':float(e),'initial_sigma_rad':float(s),'pull':float(v),'final_cumulative_rad':float(f)}
    summary['diagnostics']={
        'converged_samples':sum(r['converged'] for r in records),
        'iteration_counts':dict(Counter(len(r['iterations']) for r in records)),
        'initial_status_counts':dict(Counter(r['iterations'][0]['pede']['status'] for r in records)),
        'last_status_counts':dict(Counter(r['iterations'][-1]['pede']['status'] for r in records)),
        'initial_pede_chi2_ndf':summarize([r['iterations'][0]['pede']['chi2_ndf'] for r in records]),
        'last_pede_chi2_ndf':summarize([r['iterations'][-1]['pede']['chi2_ndf'] for r in records]),
        'acts_before':summarize([r['iterations'][0]['acts']['chi2_over_stored_ndf'] for r in records]),
        'acts_after':summarize([r['final_acts']['chi2_over_stored_ndf'] for r in records]),
        'initial_max_rejects':summarize([r['iterations'][0]['pede']['max_rejected_local_fits'] for r in records]),
        'samples_with_initial_rejects':sum(r['iterations'][0]['pede']['max_rejected_local_fits']>0 for r in records),
        'events_without_tracks':sum(r['events_without_tracks'] for r in records)}
    for layer in design['truth_rad']:
        groups={}
        for rejected in [False,True]:
            values=[r['statistics'][layer]['pull'] for r in records if (r['iterations'][0]['pede']['max_rejected_local_fits']>0)==rejected]
            groups['with_rejects' if rejected else 'without_rejects']=summarize(values) if len(values)>1 else {'n':len(values),'values':values}
        summary['layers'][layer]['pull_by_rejection_group']=groups
    exclusive_json(out/'samples.json',records);exclusive_json(out/'summary.json',summary)
    plot(out,records,design)
    print(json.dumps(summary,indent=2))



if __name__=='__main__':main()
