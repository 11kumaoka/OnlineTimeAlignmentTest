"""Fixed-dataset selected SiMAPS alignment iterations invoking the existing reconstruction, pede and correction CLIs."""
import json
import shutil
from pathlib import Path
from alignment.align import read_pede
from calibration.convergence import evaluate
from correction.scope import layers_for,verify_scope,axes_for,verify_survey,SO3_MODES,parameter_spec
from calibration.runner import stage as run_stage
from digitization.contract import validate_contract
from research_common import digest,write_json,require


def reconstruction_args(config,raw,metadata,geometry,run):
    args=['--result-dir',run,'--raw-input',raw,'--raw-metadata',metadata,
            '--geometry',geometry,'--config',config['reconstruction_config'],'--build-dir',config['build_dir']]
    if 'rz' in config['calibration'].get('correction_mode','') or config['calibration'].get('correction_mode','') in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry','l1_z','l1_l2_z','l1_l2_xyz'):args+=['--alignment-mode',config['calibration']['correction_mode']]
    return args


def verify_outputs(directory):
    for marker in directory.rglob('complete.json'):
        require(marker.parent.parent,marker.parent.name)


def iterate(config,queue,geometries,raw,metadata,initial,directory,lock_fd,stop,progress):
    policy=config['calibration']
    measured=policy['measured_geometry']
    mode=policy.get('correction_mode','l2_x');layers=layers_for(mode)
    reference=Path(config['fallback_geometry']) if mode in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry','l1_l2_xy','l1_rz','l1_l2_rz','l1_l2_xy_rz','l1_z','l1_l2_z','l1_l2_xyz') else Path(config['nominal_geometry'])
    if mode in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry','l1_l2_xy','l1_rz','l1_l2_rz','l1_l2_xy_rz','l1_z','l1_l2_z','l1_l2_xyz'):verify_survey(Path(config['nominal_geometry']),reference,rotation_layers=layers if 'rz' in axes_for(mode) or 'z' in axes_for(mode) or 'rx' in axes_for(mode) or 'ry' in axes_for(mode) else (),orientation_layers=layers if mode in SO3_MODES else ())
    verify_scope(reference,Path(initial['path']),layers,axes_for(mode))
    scenario=json.loads(Path(config['scenario']).read_text())
    if scenario.get('detector')!='SiMAPS' or any(int(k) not in layers and v!=0 for k,v in scenario.get('global_x_shifts_mm',{}).items()):
        raise ValueError('Scenario exceeds selected alignment scope')
    for axis in ('rx','ry'):
        values=scenario.get('global_'+axis+'_rad',{})
        if any(v!=0 for v in values.values()) and (axis not in axes_for(mode) or any(int(k) not in layers and v!=0 for k,v in values.items())):raise ValueError('Tilt scenario exceeds selected calibration scope')
    if any(axis in axes_for(mode) for axis in ('rx','ry')) and 'x' not in axes_for(mode) and any(v!=0 for v in scenario.get('global_x_shifts_mm',{}).values()):raise ValueError('Tilt-only calibration requires a rotation-only scope scenario')
    if any(v!=0 for v in scenario.get('global_y_shifts_mm',{}).values()) and 'y' not in axes_for(mode):raise ValueError('Y calibration requires l1_l2_xy')
    if any(v!=0 for v in scenario.get('global_rz_rad',{}).values()) and 'rz' not in axes_for(mode):raise ValueError('Rotation requires explicit l1_rz mode')
    if mode in ('l1_rz','l1_l2_rz') and (any(v!=0 for v in scenario.get('global_x_shifts_mm',{}).values()) or any(v!=0 for v in scenario.get('global_y_shifts_mm',{}).values())):raise ValueError('Rotation-only scenario required')
    record,_=validate_contract(raw,metadata,Path(initial['path']))
    # Legacy measured_geometry is an optional simulation-provenance check, never a correction input.
    if measured:
        truth=record.get('simulation_truth_geometry_sha256')
        if record['schema']=='local-telescope-rawhits-v1' and record['source_kind']=='simulation':truth=record['measured_geometry_sha256']
        if truth!=digest(Path(measured)):raise ValueError('Optional simulation Geometry provenance checksum mismatch')
    directory.mkdir(parents=True,exist_ok=False)
    current=initial;iterations=[]
    for number in range(1,policy['max_iterations']+1):
        run=directory/f'iteration-{number:03d}'
        calls=directory/f'commands-{number:03d}';calls.mkdir()
        run_stage('geometry.prepare',['--result-dir',run,'--nominal',config['nominal_geometry'],
                  '--geometry-config',config['scenario']],calls/'geometry',lock_fd,stop,progress)
        run_stage('reconstruction.reconstruct',reconstruction_args(config,raw,metadata,Path(current['path']),run),
                  calls/'reconstruction',lock_fd,stop,progress)
        if mode in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry'):
            run_stage('validation.tilt_observability',['--mille',run/'step3/mille.dat',
                '--mode',mode,'--max-sigma-rad',policy['tilt_max_nominal_sigma_rad'],'--output',run/'tilt_observability.json',*(['--max-sigma-mm',policy['tilt_max_nominal_sigma_mm']] if mode in SO3_MODES and 'z' in axes_for(mode) else [])],
                calls/'observability',lock_fd,stop,progress)
        if 'z' in axes_for(mode) and mode not in SO3_MODES:
            run_stage('validation.z_observability',['--mille',run/'step3/mille.dat','--mode',mode,
                '--max-sigma-mm',policy['z_max_nominal_sigma_mm'],'--output',run/'z_observability.json'],
                calls/'observability',lock_fd,stop,progress)
        run_stage('alignment.align',['--result-dir',run,'--steering',config['steering']],calls/'alignment',lock_fd,stop,progress)
        run_stage('correction.correct_geometry',['--result-dir',run,'--mode',mode,'--base-geometry',current['path'],*(['--reference-geometry',reference] if mode in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry','l1_l2_xy','l1_rz','l1_l2_rz','l1_l2_xy_rz','l1_z','l1_l2_z','l1_l2_xyz') else [])],
                  calls/'correction',lock_fd,stop,progress)
        import uproot
        import awkward as ak
        with uproot.open(run/'step3/reco.root') as file:
            tree=file['events'];chi2=float(ak.sum(tree['LocalBeamTestTracks/LocalBeamTestTracks.chi2'].array()))
            ndf=float(ak.sum(tree['LocalBeamTestTracks/LocalBeamTestTracks.ndf'].array()))
        reco=json.loads((run/'step3/complete.json').read_text())
        correction=json.loads((run/'step5/complete.json').read_text())
        if 'rz' in axes_for(mode) or 'rx' in axes_for(mode) or 'ry' in axes_for(mode):
            from calibration.convergence import evaluate_rotation
            deltas=correction['delta_rad_by_component']
            checks=[evaluate_rotation(delta,chi2/ndf,reco['tracks'],policy) for delta in deltas.values()]
            linear=correction.get('delta_mm_by_component',{})
            checks += [evaluate(v,chi2/ndf,reco['tracks'],policy) for v in linear.values()]
            metrics=dict(checks[0]);metrics['converged']=all(check['converged'] for check in checks)
            metrics.update(delta_rad_by_component=deltas,applied_rad_by_component=correction['applied_rad_by_component'],
                           max_abs_delta_rad=max(abs(v) for v in deltas.values()),pivots_mm=correction['pivots_mm'],
                           iteration=number,geometry_used=current['id'],raw_sha256=digest(raw),
                           fit_parameters_by_label=read_pede(run/'step4/millepede.res'),
                           parameter_units={'3000+layer':'rad','1000+layer':'mm','2000+layer':'mm'},run=str(run))
            if mode in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry'):metrics.update(parameter_units={str(family+l):('rad' if family in (3000,5000,6000) else 'mm') for l in layers for axis,family,_ in parameter_spec(mode)},linearization='so3_profiled_covariance_v1' if mode in SO3_MODES else 'tilt_profiled_covariance_v1',observability=str(run/'tilt_observability.json'))
            if linear:metrics.update(delta_mm_by_component=linear,applied_mm_by_component=correction['applied_mm_by_component'],max_abs_delta_mm=max(abs(v) for v in linear.values()))
        else:
            deltas=correction.get('delta_mm_by_layer',{'2':correction.get('delta_mm')})
            if mode=='l1_l2_xy' or 'z' in axes_for(mode):deltas=correction['delta_mm_by_component']
            checks=[evaluate(delta,chi2/ndf,reco['tracks'],policy) for delta in deltas.values()]
            metrics=dict(checks[0]);metrics['converged']=all(check['converged'] for check in checks)
            metrics['delta_mm_by_component' if mode=='l1_l2_xy' or 'z' in axes_for(mode) else 'delta_mm_by_layer']=deltas
            metrics['max_abs_delta_mm']=max(abs(value) for value in deltas.values())
            if mode=='l1_l2_xy' or 'z' in axes_for(mode):metrics['applied_mm_by_component']=correction['applied_mm_by_component']
            if mode!='l1_l2_xy' and 'z' not in axes_for(mode):metrics['applied_mm_by_layer']=correction.get('applied_mm_by_layer',{'2':correction.get('applied_mm')})
            metrics.update(iteration=number,geometry_used=current['id'],raw_sha256=digest(raw),
                           fit_parameters_mm=read_pede(run/'step4/millepede.res'),run=str(run))
        if 'z' in axes_for(mode) and mode not in SO3_MODES:metrics.update(parameter_units={'4000+layer':'mm physical correction','1000+layer':'mm measurement bias','2000+layer':'mm measurement bias'},linearization='profiled_local_slopes_v1',observability=str(run/'z_observability.json'))
        write_json(run/'calibration_quality.json',metrics)
        candidate=geometries.register(run/'step5/corrected.xml','candidate',parent=current['id'])
        metrics['candidate_geometry']=candidate['id'];iterations.append(metrics)
        queue.event('calibration_iteration',**metrics)
        current=candidate
        if metrics['converged']:break
    report={'iterations':iterations,'converged':iterations[-1]['converged'],
            'raw_sha256':digest(raw),'initial_geometry':initial['id'],'candidate_geometry':current['id'],
            'activation':'never automatic','independent_validation':'required before explicit review/activation'}
    report_path=directory/'calibration_report.json';write_json(report_path,report)
    verify_outputs(directory)
    if report['converged']:
        current=geometries.register(Path(current['path']),'candidate',evidence={
            'converged':True,'report_path':str(report_path),'report_sha256':digest(report_path),'raw_sha256':digest(raw)})
    return report
