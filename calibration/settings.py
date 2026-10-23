"""Strict, snapshotted configuration for the single-worker prototype."""
import hashlib
import json
import math
from pathlib import Path
from research_common import REPO, digest
from correction.scope import SO3_MODES,parameter_spec


def load(path):
    config=json.loads(path.read_text())
    expected={'fallback_geometry','nominal_geometry','reconstruction_config','build_dir','steering','scenario',
              'poll_seconds','ordering','first_sequence','gap_policy','max_attempts','calibration'}
    if set(config)!=expected: raise ValueError('Unknown/missing controller configuration keys')
    for key in ('fallback_geometry','nominal_geometry','reconstruction_config','build_dir','steering','scenario'):
        config[key]=str((REPO/config[key]).resolve())
    cal=config['calibration']
    mode=cal.pop('correction_mode','l2_x')
    from correction.scope import layers_for
    layers_for(mode)
    z_policy={}
    if mode in ('l1_z','l1_l2_z','l1_l2_xyz'):
        for key in ('z_derivative_report','z_max_nominal_sigma_mm'):
            if key not in cal:raise ValueError('Z alignment requires explicit '+key)
            z_policy[key]=cal.pop(key)
    tilt={}
    if mode in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry'):
        for key in ('delta_tolerance_rad','max_update_rad','tilt_derivative_report','tilt_max_nominal_sigma_rad'):
            if key not in cal:raise ValueError('Tilt alignment requires explicit '+key)
            tilt[key]=cal.pop(key)
        if mode in SO3_MODES and mode.endswith('six_dof'):
            if 'tilt_max_nominal_sigma_mm' not in cal:raise ValueError('Coupled six-DOF requires an explicit translation information bound')
            tilt['tilt_max_nominal_sigma_mm']=cal.pop('tilt_max_nominal_sigma_mm')
    angular={}
    if mode in ('l1_rz','l1_l2_rz','l1_l2_xy_rz'):
        for key in ('delta_tolerance_rad','max_update_rad','rotation_derivative_report'):
            if key not in cal:raise ValueError('Rotation requires explicit '+key)
            angular[key]=cal.pop(key)
    cal.setdefault('measured_geometry',None)
    if set(cal)!={'enabled','measured_geometry','min_tracks','max_iterations','delta_tolerance_mm',
                 'max_update_mm','max_track_chi2_ratio','policy_label'}:raise ValueError('Invalid calibration policy keys')
    from correction.scope import layers_for
    layers_for(mode)
    cal['correction_mode']=mode
    extra_pins={}
    if tilt:
        for key in ('delta_tolerance_rad','max_update_rad','tilt_max_nominal_sigma_rad',*(['tilt_max_nominal_sigma_mm'] if 'tilt_max_nominal_sigma_mm' in tilt else [])):
            value=tilt[key]
            if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError('Invalid tilt policy bound')
        evidence_path=(REPO/tilt['tilt_derivative_report']).resolve();evidence=json.loads(evidence_path.read_text())
        plugin=Path(config['build_dir'])/'BeamTestReco.so';factory=Path(config['build_dir'])/'libLocalTelescopeGeometry.so'
        from correction.scope import axes_for
        needed={family+l for l in layers_for(mode) for _,family,_ in parameter_spec(mode)}
        linearization='so3_profiled_covariance_v1' if mode in SO3_MODES else 'tilt_profiled_covariance_v1'
        if evidence.get('passed') is not True or evidence.get('linearization')!=linearization or not needed<=set(evidence.get('labels',[])) or evidence.get('actual_binary_entries',0)<=0 or evidence.get('fresh_physical_contexts',0)<=0:
            raise ValueError('Missing compatible physical/actual-Mille tilt derivative validation')
        if evidence.get('plugin_sha256')!=digest(plugin) or evidence.get('geometry_plugin_sha256')!=digest(factory):raise ValueError('Tilt evidence belongs to a different plugin or Geometry factory')
        if digest(Path(config['steering']))!=digest(REPO/f'alignment/pede_{mode}.txt'):raise ValueError('Tilt requires canonical constrained steering')
        extra_pins.update({str(evidence_path):digest(evidence_path),str(factory):digest(factory)})
        implementation=evidence.get('implementation_sources_sha256',{})
        if mode in ('l3_six_dof','l1_l2_l3_six_dof'):
            from validation.merge_so3_evidence import IMPLEMENTATION_SOURCES
            if not set(IMPLEMENTATION_SOURCES)<=implementation.keys() or not evidence.get('derivative_reports'):
                raise ValueError('L3 requires explicit source-pinned selected derivative evidence')
        if any(digest(REPO/p)!=sha for p,sha in implementation.items()):raise ValueError('Tilt evidence belongs to different implementation sources')
        extra_pins.update({str(REPO/p):sha for p,sha in implementation.items()})
        if 'derivative_reports' in evidence:
            found=set()
            for entry in evidence['derivative_reports']:
                proof=Path(entry['path'])
                if digest(proof)!=entry['sha256']:raise ValueError('Tilt derivative proof changed')
                report=json.loads(proof.read_text())
                if report.get('passed') is not True or report.get('linearization')!=linearization or report.get('actual_binary_entries',0)<=0 or report.get('fresh_physical_contexts',0)<=0:raise ValueError('Incomplete tilt derivative proof')
                if report.get('plugin_sha256')!=digest(plugin) or report.get('geometry_plugin_sha256')!=digest(factory):raise ValueError('Stale tilt derivative proof')
                found.update(report.get('labels',[]));extra_pins[str(proof)]=digest(proof)
            if not needed<=found:raise ValueError('Missing selected tilt derivative proof')
        if mode in SO3_MODES:
            writer=REPO/'localDetEICrecon/alignment/src/BeamTestMilleWriter.cc'
            if evidence.get('writer_source_sha256')!=digest(writer):raise ValueError('Coupled rotation proof belongs to a different writer source')
            required={'l3_six_dof':'l3_six_dof','l1_l2_l3_six_dof':'three_six_dof'}.get(mode) or ('two_six_dof' if mode=='l1_l2_six_dof' else ('l1_six_dof' if mode=='l1_six_dof' else ('two_rotations' if mode=='l1_l2_rotations' else 'xy_positive')))
            found=set()
            for entry in evidence.get('noiseless_reports',[]):
                proof=Path(entry['path'])
                if digest(proof)!=entry['sha256']:raise ValueError('Noiseless rotation proof changed')
                report=json.loads(proof.read_text())
                if report.get('passed') is not True or report.get('writer_source_sha256')!=digest(writer):raise ValueError('Unvalidated noiseless rotation closure')
                model_hashes=report.get('model_sources_sha256',{})
                if not model_hashes or any(digest(REPO/p)!=sha for p,sha in model_hashes.items()):raise ValueError('Noiseless closure belongs to different model sources')
                extra_pins.update({str(REPO/p):sha for p,sha in model_hashes.items()})
                found.add(report['fixture']);extra_pins[str(proof)]=digest(proof)
            if not {required,'rx','ry','xy_positive','xy_negative','reverse_order','existing_rz'}<=found:raise ValueError('Missing mandatory noiseless SO(3) closure cases')
        tilt['tilt_derivative_report']=str(evidence_path);cal.update(tilt)
    if angular:
        for key in ('delta_tolerance_rad','max_update_rad'):
            value=angular[key]
            if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError('Invalid angular policy bound')
        evidence_path=(REPO/angular['rotation_derivative_report']).resolve()
        evidence=json.loads(evidence_path.read_text())
        proofs=evidence.get('derivative_reports',[{'path':evidence.get('derivative_report'),'sha256':evidence.get('derivative_report_sha256')}])
        found=set();extra_pins={str(evidence_path):digest(evidence_path)}
        for entry in proofs:
            proof_path=Path(entry['path'])
            if digest(proof_path)!=entry['sha256']:raise ValueError('Rotation derivative evidence changed')
            proof=json.loads(proof_path.read_text())
            if proof.get('passed') is not True or proof.get('actual_binary_entries',0)<=0:raise ValueError('Rotation derivatives have not passed independent Geometry checks')
            found.add(proof.get('label'));extra_pins[str(proof_path)]=digest(proof_path)
        needed={3001} if mode=='l1_rz' else {3001,3002}
        if evidence.get('passed') is not True or not needed<=found:raise ValueError('Missing selected rotation derivative validation')
        if evidence['plugin_sha256']!=digest(Path(config['build_dir'])/'BeamTestReco.so'):raise ValueError('Rotation derivative evidence belongs to a different plugin')
        if digest(Path(config['steering']))!=digest(REPO/f'alignment/pede_{mode}.txt'):raise ValueError('Rotation requires constrained mode-specific steering')
        angular['rotation_derivative_report']=str(evidence_path)
        cal.update(angular)
    if z_policy:
        value=z_policy['z_max_nominal_sigma_mm']
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError('Invalid Z information bound')
        evidence_path=(REPO/z_policy['z_derivative_report']).resolve();evidence=json.loads(evidence_path.read_text())
        if evidence.get('passed') is not True or evidence.get('linearization')!='profiled_local_slopes_v1':raise ValueError('Missing compatible Z derivative validation')
        plugin=Path(config['build_dir'])/'BeamTestReco.so';factory=Path(config['build_dir'])/'libLocalTelescopeGeometry.so'
        if evidence.get('plugin_sha256')!=digest(plugin) or evidence.get('geometry_plugin_sha256')!=digest(factory):raise ValueError('Z evidence belongs to a different plugin or Geometry factory')
        found=set();extra_pins[str(evidence_path)]=digest(evidence_path);extra_pins[str(factory)]=digest(factory)
        for entry in evidence.get('derivative_reports',[]):
            proof_path=Path(entry['path'])
            if digest(proof_path)!=entry['sha256']:raise ValueError('Z derivative evidence changed')
            proof=json.loads(proof_path.read_text())
            if proof.get('passed') is not True or proof.get('actual_binary_entries',0)<=0 or proof.get('linearization')!='profiled_local_slopes_v1':raise ValueError('Unvalidated Z derivative report')
            if proof.get('plugin_sha256')!=digest(plugin) or proof.get('geometry_plugin_sha256')!=digest(factory):raise ValueError('Stale Z derivative report')
            found.add(proof.get('label'));extra_pins[str(proof_path)]=digest(proof_path)
        needed={4001} if mode=='l1_z' else {4001,4002}
        if not needed<=found:raise ValueError('Missing selected Z derivative proof')
        if digest(Path(config['steering']))!=digest(REPO/f'alignment/pede_{mode}.txt'):raise ValueError('Z requires canonical constrained steering')
        z_policy['z_derivative_report']=str(evidence_path);cal.update(z_policy)
    if cal['measured_geometry']:cal['measured_geometry']=str((REPO/cal['measured_geometry']).resolve())
    if config['ordering'] not in ('sequence','identity') or config['gap_policy'] not in ('wait','error','skip'):
        raise ValueError('Unsupported ordering/gap policy')
    if type(cal['enabled']) is not bool:raise ValueError('enabled must be boolean')
    for key in ('first_sequence','max_attempts'):
        if type(config[key]) is not int:raise ValueError(key+' must be an integer')
    for key in ('min_tracks','max_iterations'):
        if type(cal[key]) is not int:raise ValueError(key+' must be an integer')
    for value in [config['poll_seconds'],*[cal[k] for k in ('delta_tolerance_mm','max_update_mm','max_track_chi2_ratio')]]:
        if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Policy values must be finite numbers')
    if config['poll_seconds']<=0 or config['max_attempts']<1 or config['first_sequence']<0:
        raise ValueError('Invalid polling, attempt or sequence limit')
    if any(cal[k]<=0 for k in ('min_tracks','max_iterations','delta_tolerance_mm','max_update_mm','max_track_chi2_ratio')):
        raise ValueError('Calibration policy limits must be positive')
    # Pin dependencies as well as path strings; changing a source/config under an old state is refused.
    pins={str(p):digest(p) for p in [Path(config['nominal_geometry']),Path(config['fallback_geometry']),Path(config['reconstruction_config']),
                                   Path(config['steering']),Path(config['scenario']),Path(config['build_dir'])/'BeamTestReco.so']}
    pins.update(extra_pins)
    if cal['measured_geometry']:pins[cal['measured_geometry']]=digest(cal['measured_geometry'])
    return config,hashlib.sha256(json.dumps({'config':config,'pins':pins},sort_keys=True).encode()).hexdigest()
