"""Independent manual equivalence, real refusal and interruption checks.

Only this validation module reads injected Geometry. Operational calibration
never imports it. Failure injection substitutes a historical invalid proposal,
not a fitted result, and is explicitly recorded as a control-plane test.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

from research_common import REPO, digest, write_json
from calibration import native_controller as controller


def compare(run, manual, output):
    import numpy as np
    from calibration.native_operations import channel_values, channel_digest
    from geometry.transforms import orientation_distance
    from validation.telescope_closure.multi_sensor import injection
    output.mkdir()
    manifest = json.loads((run / 'manifest.json').read_text()); controller.validate_run_inputs(manifest)
    chain = controller.checkpoints(run)
    if not chain or chain[-1]['termination'] != 'converged': raise AssertionError('Controller has not converged')
    controller.verify(run / 'final')
    names = [('nominal', 'solve', 'geometry/fixtures/nominal.xml'),
             ('corrected', 'postsolve', 'correction/corrected.xml'),
             ('refined', 'refinesolve', 'refinement/refined.xml')]
    if len(chain) > len(names):
        raise ValueError('The historical manual contract has only two corrections; no equivalent fourth-fit checkpoint exists')
    results = []
    for checkpoint in chain:
        index = checkpoint['sequence']; name, solver, geometry = names[index]
        directory = Path(checkpoint['marker']['path']).parent
        reconstructed = directory / 'reconstruct/artifacts'; solved = directory / 'solve/artifacts'
        if json.loads((reconstructed / 'audit.json').read_text()) != json.loads((manual / name / 'audit.json').read_text()):
            raise AssertionError('Fitted states/residuals differ from manual checkpoint: ' + name)
        if (reconstructed / 'mille.dat').read_bytes() != (manual / name / 'mille.dat').read_bytes():
            raise AssertionError('Mille bytes differ: ' + name)
        if json.loads((solved / 'independent.json').read_text()) != json.loads((manual / solver / 'independent.json').read_text()):
            raise AssertionError('Pede/profiled information differs: ' + solver)
        if Path(checkpoint['geometry']['path']).read_bytes() != (manual / geometry).read_bytes():
            raise AssertionError('Physical XML differs: ' + geometry)
        raw = channel_values(reconstructed / 'reco.root')
        if channel_digest(raw) != manifest['channel_payload_sha256']: raise AssertionError('Raw channels changed')
        metrics = json.loads(Path(checkpoint['metrics']).read_text())
        decision = json.loads((directory / 'convergence.json').read_text())
        results.append({'checkpoint': index, 'manual_reconstruction': name, 'tracks': metrics['tracks'],
            'chi2_per_stored_ndf': metrics['chi2_ratio'], 'pede': metrics['pede'],
            'joint_remaining_sigma': decision['joint_correction_sigma'],
            'maximum_remaining_over_initial_sigma': max(abs(v['correction_over_initial_sigma']) for v in decision['per_parameter'].values()),
            'geometry_sha256': checkpoint['geometry']['sha256'], 'mille_sha256': digest(reconstructed / 'mille.dat'),
            'raw_payload_sha256': channel_digest(raw), 'states_mille_information_xml_exact': True})
    # Independent Truth comparison starts only after operational completion.
    truth = json.loads((manual / 'data/shifted/channels_truth.json').read_text())['sensors']
    initial = chain[0]; info = json.loads(Path(initial['current_information']['path']).read_text())
    values = info['parameters']; expected = injection(manifest['mode'])
    labels = [p['label'] for p in manifest['parameters']]
    error = np.array([values[str(k)] - expected[k] for k in labels])
    information = np.array(info['normal']); truth_significance = float(error @ information @ error)
    if truth_significance >= 25: raise AssertionError('Historical initial-fit Truth gate failed')
    pose_errors = []
    for sensor in manifest['fixed_reference_sensors']:
        if chain[0]['sensor_poses'][sensor] != chain[-1]['next_sensor_poses'][sensor]:
            raise AssertionError('Reference sensor moved')
    for sensor in sorted({p['layer'] for p in manifest['parameters']}):
        final = chain[-1]['next_sensor_poses'][sensor]; target = truth[sensor]
        pose_errors.append({'layer': sensor,
            'center_bias_mm': (np.array(final['center_mm']) - target['center_mm']).tolist(),
            'orientation_error_rad': orientation_distance(target['acts_rotation'], final['acts_rotation'])})
    report = {'passed': True, 'manual_reference': str(manual), 'controller_run': str(run),
        'operational_truth_used': False, 'truth_used_only_after_completion': True,
        'initial_truth_error_mahalanobis_squared': truth_significance, 'final_pose_errors': pose_errors,
        'checkpoints': results, 'raw_sha256': manifest['input']['raw']['sha256'],
        'applied_corrections': chain[-1]['applied_corrections'], 'geometry_activated': False}
    write_json(output / 'report.json', report)
    import ROOT
    ROOT.gROOT.SetBatch(True)
    root = ROOT.TFile.Open(str(output / 'controller.root'), 'NEW')
    if not root or root.IsZombie(): raise RuntimeError('Cannot create ROOT validation file')
    for checkpoint in chain:
        directory = Path(checkpoint['marker']['path']).parent
        audit = json.loads((directory / 'reconstruct/artifacts/audit.json').read_text())
        index = checkpoint['sequence']
        histogram = ROOT.TH1D(f'iteration_{index}_chi2', f'Iteration {index};ACTS chi2/stored-NDF;Tracks', 100, 0, 30 if index == 0 else 3)
        for event in audit['events']: histogram.Fill(event['chi2'] / event['stored_ndf'])
        histogram.Write()
        for component, label in enumerate(('u', 'v')):
            h = ROOT.TH1D(f'iteration_{index}_residual_{label}', f'Iteration {index};Local {label} residual [mm];Measurements', 160, -.15, .15)
            for event in audit['events']:
                for state in event['smoothed_states']: h.Fill(state['residual_mm'][component])
            h.Write()
    root.Close(); controller.seal(output, passed=True)
    print(json.dumps(report, indent=2))


def start_arguments(args, minimum=2):
    return SimpleNamespace(run=args.run, raw=args.manual / 'data/shifted.root',
        geometry=args.manual / 'geometry/fixtures/nominal.xml',
        config=REPO / 'validation/telescope_alignment/l1_l2_l3_y_rx_ry_rz.json',
        build=args.build, events=4096, chi2_cut=1000., minimum_corrections=minimum,
        maximum_corrections=3, max_abs_y_mm=2e-5, max_angular_sigma_ratio=.25,
        max_joint_sigma=.25, max_scaled_condition=100.)


def interruption(args):
    """Interrupt an actual second reconstruction; then explicitly resume."""
    output = args.output; output.mkdir()
    command = [sys.executable, '-B', '-m', 'calibration.native_controller', 'start',
        '--run', str(args.run), '--raw', str(args.manual / 'data/shifted.root'),
        '--geometry', str(args.manual / 'geometry/fixtures/nominal.xml'),
        '--config', 'validation/telescope_alignment/l1_l2_l3_y_rx_ry_rz.json',
        '--build', str(args.build), '--events', '4096', '--chi2-cut', '1000', '--minimum-corrections', '2']
    write_json(output / 'start-command.json', {'argv': command, 'cwd': str(REPO)})
    target = args.run / 'jobs/attempt_000/iteration_001/reconstruct/process.json'
    with (output / 'interrupted.log').open('x') as stream:
        process = subprocess.Popen(command, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 1800
        process_evidence = None
        while process_evidence is None:
            if process.poll() is not None: raise RuntimeError('Controller ended before interruption checkpoint')
            if time.monotonic() >= deadline:
                process.send_signal(signal.SIGTERM); process.wait()
                raise RuntimeError('Interruption test exceeded declared30-minute bound')
            if target.exists():
                group = json.loads(target.read_text())['process_group']
                rows = subprocess.check_output(['ps', '-eo', 'pid,pgid,comm,args'], text=True)
                for row in rows.splitlines()[1:]:
                    columns = row.split(maxsplit=3)
                    if len(columns) >= 3 and columns[1] == str(group) and columns[2] == 'eicrecon':
                        process_evidence = {'ps_argv': ['ps', '-eo', 'pid,pgid,comm,args'], 'matching_process': row,
                                            'supervised_process_group': group}
            time.sleep(.05)
        write_json(output / 'live-eicrecon-evidence.json', process_evidence)
        process.send_signal(signal.SIGTERM); code = process.wait(timeout=60)
    write_json(output / 'interrupted-exit.json', {'exit_code': code, 'signal': 'SIGTERM', 'target': str(target)})
    first_chain = controller.checkpoints(args.run)
    if len(first_chain) != 1 or first_chain[0]['termination'] != 'continue': raise AssertionError('Lost the valid first candidate')
    incomplete = target.parent.parent
    if (incomplete / 'complete.json').exists(): raise AssertionError('Interrupted iteration was promoted')
    before = {str(p): digest(p) for p in args.run.rglob('*') if p.is_file()}
    if (args.run / 'controller.guard').exists():
        # Explicit test recovery still checks dead owner and all process groups.
        controller.recover_guard(args.run, 'Validation-only SIGTERM test; owner exited and process-group safety checks apply')
    resumed = [sys.executable, '-B', '-m', 'calibration.native_controller', 'resume', '--run', str(args.run)]
    write_json(output / 'resume-command.json', {'argv': resumed, 'cwd': str(REPO)})
    with (output / 'resumed.log').open('x') as stream:
        resume_code = subprocess.call(resumed, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT)
    if resume_code != 0: raise RuntimeError('Actual Controller resume failed; see resumed.log')
    preserved = {path: sha for path, sha in before.items()
                 if '/jobs/attempt_000/' in path or '/input/' in path or Path(path).name.startswith('manifest')}
    if any(digest(Path(path)) != sha for path, sha in preserved.items()): raise AssertionError('Resume changed prior immutable output')
    chain = controller.checkpoints(args.run)
    if len(chain) != 3 or chain[-1]['applied_corrections'] != 2 or chain[-1]['termination'] != 'converged':
        raise AssertionError('Unexpected resumed correction protocol')
    if not (args.run / 'jobs/attempt_001/iteration_001').is_dir(): raise AssertionError('Resume did not use a fresh attempt')
    write_json(output / 'report.json', {'passed': True, 'actual_reconstruction_interrupted': True,
        'incomplete_iteration_not_promoted': True, 'last_valid_candidate_preserved': first_chain[0]['next_geometry'],
        'prior_files_verified': len(preserved), 'fresh_attempt_used': True, 'applied_corrections': 2,
        'raw_snapshot_reused': True, 'geometry_activated': False})
    controller.seal(output, passed=True)


def refusal(args):
    """Inject the real historical invalid XML at the proposal boundary only."""
    output = args.output; output.mkdir()
    historical = args.historical.resolve()
    run = controller.initialize(start_arguments(args, minimum=1))
    original = controller.run_stage
    def operation(directory, action, manifest, lock_fd, **arguments):
        if action != 'correct': return original(directory, action, manifest, lock_fd, **arguments)
        # The actual fitted values remain in the solver artifacts and request.
        request = dict(action='geometry', build=manifest['build_dir'],
            output=str(directory / 'correct/artifacts'), geometry=str(historical))
        request_path = directory / 'historical-negative-request.json'; write_json(request_path, request)
        write_json(directory / 'fault-injection.json', {'kind': 'validation_only_historical_invalid_proposal',
            'historical_xml': controller.identity(historical), 'actual_fit_parameters': arguments['parameters'],
            'historical_fit': controller.identity(historical.parent.parent / 'solve/millepede.res')})
        controller.supervised_stage('calibration.native_controller', ['stage', '--request', request_path],
            directory / 'correct', lock_fd, controller.threading.Event(), lambda _: None)
        raise AssertionError('Historical invalid proposal was accepted')
    try:
        with patch.object(controller, 'run_stage', operation): controller.calibrate(run)
    except RuntimeError: pass
    else: raise AssertionError('Controller did not stop on historical invalid proposal')
    report = json.loads((run / 'jobs/attempt_000/report.json').read_text())
    safety = json.loads((run / 'jobs/attempt_000/iteration_000/correct/artifacts/geometry_safety.json').read_text())
    if report['status'] != 'failed' or report['applied_corrections'] != 0 or report['last_checkpoint'] is not None:
        raise AssertionError('Invalid candidate was promoted')
    if report['last_valid_geometry']['sha256'] != digest(args.manual / 'geometry/fixtures/nominal.xml'):
        raise AssertionError('Initial verified Geometry was not retained')
    if not any('module containment' in text for text in safety['failures']): raise AssertionError('Wrong safety refusal')
    if list(run.glob('jobs/**/iteration_001')) or (run / 'final').exists(): raise AssertionError('Invalid candidate reached reconstruction')
    if controller.checkpoints(run): raise AssertionError('Failed iteration has a valid completion marker')
    write_json(output / 'report.json', {'passed': True, 'scope': 'validation-only proposal fault injection after real Scope D fit',
        'historical_candidate': controller.identity(historical), 'physical_safety': safety,
        'candidate_reconstructed': False, 'failed_iteration_promoted': False,
        'last_valid_geometry': report['last_valid_geometry'], 'fit_and_logs_retained': True, 'geometry_activated': False})
    controller.seal(output, passed=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step', choices=('compare', 'interruption', 'refusal'), required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--manual', type=Path, required=True)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--historical', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for key, value in vars(args).items():
        if isinstance(value, Path): setattr(args, key, value.resolve())
    for name in ('run', 'output'):
        value = getattr(args, name)
        if not value.is_relative_to(REPO / 'result') or value == REPO / 'result': parser.error('Outputs must be children of result/')
    if args.step != 'compare' and args.build is None: parser.error('--build is required')
    if args.step == 'compare': compare(args.run, args.manual, args.output)
    elif args.step == 'interruption': interruption(args)
    else:
        if args.historical is None: parser.error('--historical is required for refusal')
        refusal(args)


if __name__ == '__main__': main()
