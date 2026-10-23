"""Independent stage; invoke with python3 -m correction.correct_geometry."""
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
from geometry.placements import geometry,placement_transforms
from research_common import digest
from research_common import cli_parser, run, require, stage, done
from geometry.prepare import modified_xml, write_shifted_xml
from correction.scope import layers_for,verify_scope,axes_for,verify_survey,SO3_MODES,parameter_spec
from alignment.align import read_pede


def ensure_correction_supported(result, mode="l2_x"):
    layers=layers_for(mode)
    require(result, 'step1')
    scenario = result/'step1/geometry_config.json'
    if scenario.is_file():
        config = json.loads(scenario.read_text())
        if config.get('detector') != 'SiMAPS':
            raise ValueError('Only SiMAPS Global X correction is supported')
        shifts = config['global_x_shifts_mm']
    else:
        raise ValueError('Missing step1 Geometry scenario')
    if 'z' in axes_for(mode) and 'x' not in axes_for(mode) and any(v!=0 for v in config['global_x_shifts_mm'].values()):raise ValueError('Z-only scenario cannot contain X shifts')
    z_shifts=config.get('global_z_shifts_mm',{})
    if any(v!=0 for v in z_shifts.values()) and ('z' not in axes_for(mode) or any(int(k) not in layers and v!=0 for k,v in z_shifts.items())):raise ValueError('Global Z exceeds explicit selected scope')
    if any(axis in axes_for(mode) for axis in ('rx','ry')) and 'x' not in axes_for(mode) and any(v!=0 for v in config['global_x_shifts_mm'].values()):raise ValueError('Tilt-only scenario cannot contain X shifts')
    for axis in ('rx','ry'):
        values=config.get('global_'+axis+'_rad',{})
        if any(v!=0 for v in values.values()) and (axis not in axes_for(mode) or any(int(k) not in layers and v!=0 for k,v in values.items())):raise ValueError('Tilt exceeds selected correction scope')
    rotations=config.get('global_rz_rad',{})
    if any(v!=0 for v in rotations.values()) and 'rz' not in axes_for(mode):raise ValueError('Rotation requires explicit l1_rz mode')
    if mode in ('l1_rz','l1_l2_rz') and (any(v!=0 for v in config['global_x_shifts_mm'].values()) or any(v!=0 for v in config.get('global_y_shifts_mm',{}).values()) or any(int(k) not in layers and v!=0 for k,v in rotations.items())):raise ValueError('L1 rotation-only scenario required')
    y_shifts=config.get('global_y_shifts_mm',{})
    if any(v!=0 for v in y_shifts.values()) and 'y' not in axes_for(mode):raise ValueError('Y corrections require explicit l1_l2_xy mode')
    if any(int(layer) not in layers and float(value) != 0.0 for layer, value in shifts.items()):
        raise ValueError('Multi-layer Geometry Correction and full Closure are unsupported for this mode: select an explicit validated L1/L2 mode; other layers are unsupported')


def correct(a):
    if getattr(a, "check_only", False):
        ensure_correction_supported(a.run_dir,getattr(a,"mode","l2_x"))
        return
    require(a.run_dir,'step4')
    ensure_correction_supported(a.run_dir,getattr(a,"mode","l2_x"))
    mode=getattr(a,'mode','l2_x')
    if mode in SO3_MODES:
        correct_so3(a,mode)
        return
    if mode in ('l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry'):
        from geometry.transforms import axis_rotation,multiply,transpose,IDENTITY
        axes=axes_for(mode);layers=layers_for(mode)
        nominal=a.run_dir/'step1/nominal.xml';base=getattr(a,'base_geometry',None) or nominal
        reference=getattr(a,'reference_geometry',None) or nominal
        verify_survey(nominal,reference,rotation_layers=layers);verify_scope(reference,base,layers,axes)
        current=placement_transforms(base);survey=placement_transforms(reference);parameters=read_pede(a.run_dir/'step4/millepede.res')
        selected={family+l for l in layers for axis,family in (('rx',5000),('ry',6000)) if axis in axes}
        if not selected<=parameters.keys() or any(value!=0 and k not in selected for k,value in parameters.items()):raise ValueError('Unsupported fitted parameter in selected tilt correction')
        delta={f'L{l}_{axis}':parameters[family+l] for l in layers for axis,family in (('rx',5000),('ry',6000)) if axis in axes}
        if any(not math.isfinite(v) or abs(v)>.1 for v in delta.values()):raise ValueError('Invalid physical tilt increment')
        updated={};applied={};orientation={}
        for l in layers:
            # Apply Global Rx, then Global Ry, about the current sensitive center.
            q=multiply(axis_rotation('y',delta.get(f'L{l}_ry',0.)),axis_rotation('x',delta.get(f'L{l}_rx',0.)))
            updated[l]=current[l].updated(rotation=q,pivot=current[l].translation)
            relative=multiply(updated[l].rotation,transpose(survey[l].rotation))
            # Diagnostic ordered-XYZ coordinates only; the matrix is the alignment state.
            angles={'rx':math.atan2(relative[2][1],relative[2][2]),'ry':math.asin(max(-1.,min(1.,-relative[2][0]))),'rz':math.atan2(relative[1][0],relative[0][0])}
            orientation[str(l)]=angles
            applied.update({f'L{l}_{axis}':angles[axis] for axis in axes})
        p=stage(a.run_dir,'step5');write_shifted_xml(base,p/'corrected.xml',{},rotations={l:t.rotation for l,t in updated.items()})
        done(p,mode=mode,delta_rad_by_component=delta,applied_rad_by_component=applied,
             rotation_matrices={str(l):t.rotation for l,t in updated.items()},diagnostic_ordered_xyz_rad=orientation,
             pivots_mm={str(l):current[l].translation for l in layers},
             base_geometry_sha256=digest(base),reference_geometry_sha256=digest(reference),
             convention='5000/6000+layer physical Global increments (+); Q=Ry*Rx left-composes the current matrix; ordered angles are diagnostics, never additive state')
        return
    if 'z' in axes_for(mode):
        from geometry.placements import xml_number
        layers=layers_for(mode);axes=axes_for(mode)
        nominal=a.run_dir/'step1/nominal.xml';base=getattr(a,'base_geometry',None) or nominal
        reference=getattr(a,'reference_geometry',None) or nominal
        verify_survey(nominal,reference,rotation_layers=layers);verify_scope(reference,base,layers,axes)
        current=placement_transforms(base);parameters=read_pede(a.run_dir/'step4/millepede.res')
        selected={4000+l for l in layers}
        if mode=='l1_l2_xyz':selected|={label+l for label in (1000,2000) for l in layers}
        if any(abs(value)>0 and label not in selected for label,value in parameters.items()):raise ValueError('Unsupported fitted parameter in Z correction')
        delta={f'L{l}_{axis}':parameters[label+l]*(1 if axis=='z' else -1) for l in layers for axis,label in (('x',1000),('y',2000),('z',4000)) if axis in axes}
        if any(not math.isfinite(v) for v in delta.values()):raise ValueError('Non-finite Z-mode update')
        updated={l:current[l].updated(translation=tuple(delta.get(f'L{l}_{axis}',0.) for axis in 'xyz')) for l in layers}
        root=ET.parse(base).getroot();constants={c.get('name'):c.get('value') for c in root.findall('./define/constant')}
        offsets={l:xml_number(root.find(f"./detectors/detector[@name='SiMAPS']/layer[@id='{l}']/ring").get('global_z','0*mm'),constants)+delta[f'L{l}_z'] for l in layers}
        p=stage(a.run_dir,'step5')
        write_shifted_xml(base,p/'corrected.xml',{l:t.translation[0] for l,t in updated.items()} if 'x' in axes else {},
                          {l:t.translation[1] for l,t in updated.items()} if 'y' in axes else None,z_shifts=offsets)
        done(p,mode=mode,delta_mm_by_component=delta,applied_mm_by_component={f'L{l}_{axis}':t.translation[i] for l,t in updated.items() for i,axis in enumerate('xyz') if axis in axes},
             global_z_offsets_mm=offsets,base_geometry_sha256=digest(base),reference_geometry_sha256=digest(reference),
             convention='4000+layer is physical Global Z correction (+); X/Y labels remain biases (-)')
        return
    if 'rz' in axes_for(mode):
        from geometry.transforms import axis_rotation
        layers=layers_for(mode);axes=axes_for(mode)
        nominal=a.run_dir/'step1/nominal.xml';base=getattr(a,'base_geometry',None) or nominal
        reference=getattr(a,'reference_geometry',None) or nominal
        verify_survey(nominal,reference,rotation_layers=layers)
        verify_scope(reference,base,layers,axes)
        current=placement_transforms(base);parameters=read_pede(a.run_dir/'step4/millepede.res')
        angular={f'L{l}_rz':-parameters[3000+l] for l in layers}
        linear={f'L{l}_{axis}':-parameters[label+l] for l in layers for axis,label in (('x',1000),('y',2000))} if 'x' in axes else {}
        if any(not math.isfinite(v) or abs(v)>.1 for v in angular.values()):raise ValueError('Invalid angular update')
        updated={l:current[l].updated(rotation=axis_rotation('z',angular[f'L{l}_rz']),pivot=current[l].translation,
                   translation=(linear.get(f'L{l}_x',0.),linear.get(f'L{l}_y',0.),0.)) for l in layers}
        angles={l:math.atan2(t.rotation[1][0],t.rotation[0][0]) for l,t in updated.items()}
        p=stage(a.run_dir,'step5')
        write_shifted_xml(base,p/'corrected.xml',{l:t.translation[0] for l,t in updated.items()} if linear else {},
                          {l:t.translation[1] for l,t in updated.items()} if linear else None,rz_rad=angles)
        info=dict(mode=mode,delta_rad_by_component=angular,applied_rad_by_component={f'L{l}_rz':v for l,v in angles.items()},
                  axis='global_positive_z',pivots_mm={str(l):list(current[l].translation) for l in layers},
                  base_geometry_sha256=digest(base),reference_geometry_sha256=digest(reference),
                  note='Current-matrix composition about each selected sensitive center; angular units rad; candidates inactive')
        if linear:info.update(delta_mm_by_component=linear,applied_mm_by_component={f'L{l}_{axis}':t.translation[i] for l,t in updated.items() for i,axis in enumerate(('x','y'))})
        done(p,**info)
        return
    if getattr(a,'mode','l2_x')=='l1_l2_xy':
        nominal=a.run_dir/'step1/nominal.xml';base=getattr(a,'base_geometry',None) or nominal
        reference=getattr(a,'reference_geometry',None) or nominal
        verify_survey(nominal,reference)
        verify_scope(reference,base,(1,2),('x','y'))
        current=placement_transforms(base);parameters=read_pede(a.run_dir/'step4/millepede.res')
        deltas={str(layer):{'x':-parameters[1000+layer],'y':-parameters[2000+layer]} for layer in (1,2)}
        updated={layer:current[layer].updated(translation=(deltas[str(layer)]['x'],deltas[str(layer)]['y'],0.)) for layer in (1,2)}
        p=stage(a.run_dir,'step5')
        write_shifted_xml(base,p/'corrected.xml',{layer:t.translation[0] for layer,t in updated.items()},
                          {layer:t.translation[1] for layer,t in updated.items()})
        done(p,mode='l1_l2_xy',delta_mm_by_component={f'L{layer}_{axis}':value for layer,d in deltas.items() for axis,value in d.items()},
             applied_mm_by_component={f'L{layer}_{axis}':t.translation[index] for layer,t in updated.items() for index,axis in enumerate(('x','y'))},
             base_geometry_sha256=digest(base),reference_geometry_sha256=digest(reference),note='Only selected SiMAPS L1/L2 Global X/Y updates are composed')
        return
    if getattr(a,'mode','l2_x')=='l1_l2_x':
        nominal=a.run_dir/'step1/nominal.xml'
        base=getattr(a,'base_geometry',None) or nominal
        verify_scope(nominal,base,(1,2))
        positions=geometry(base);parameters=read_pede(a.run_dir/'step4/millepede.res')
        deltas={layer:-parameters[1000+layer] for layer in (1,2)}
        values={layer:positions[layer][0]+deltas[layer] for layer in (1,2)}
        if not all(math.isfinite(v) for v in values.values()):raise ValueError('Non-finite Geometry correction')
        p=stage(a.run_dir,'step5')
        write_shifted_xml(nominal,p/'corrected.xml',values)
        done(p,mode='l1_l2_x',axis='global_x',applied_mm_by_layer=values,delta_mm_by_layer=deltas,
             base_geometry_sha256=digest(base),note='Apply only SiMAPS L1/L2 X; other fitted components are not applied')
        return
    p=stage(a.run_dir,'step5')
    delta=-read_pede(a.run_dir/'step4/millepede.res')[1002]
    base=getattr(a,'base_geometry',None)
    base_x=0.0
    if base:
        # Composition is opt-in and restricted to the same nominal model with only L2 X changed.
        nominal_root=ET.parse(a.run_dir/'step1/nominal.xml').getroot()
        base_root=ET.parse(base).getroot()
        for root in (nominal_root,base_root):
            root.find("./detectors/detector[@name='SiMAPS']/layer[@id='2']/ring").set('r','L2_PLACEHOLDER')
        if ET.tostring(nominal_root)!=ET.tostring(base_root):
            raise ValueError('Cumulative correction supports only L2 X changes from the nominal Geometry')
        base_x=geometry(base)[2][0]
    value=base_x+delta
    if not math.isfinite(value): raise ValueError('Non-finite L2 correction')
    modified_xml(a.run_dir/'step1/nominal.xml',p/'corrected.xml',2,value)
    if base:
        done(p,layer=2,axis='global_x',applied_mm=value,delta_mm=delta,base_x_mm=base_x,
             base_geometry_sha256=digest(base),note='Cumulative L2 X only; other fitted components are not applied')
        return
    done(p,layer=2,axis='global_x',applied_mm=value,measurement_bias_mm=-value,
         note='Apply only L2 X, matching the saved physical closure; other fitted components are not applied')


def correct_so3(a,mode):
    """Apply one frozen linear solve using Global rotation-vector retraction."""
    from geometry.transforms import rotation_exp,rotation_log,multiply,transpose
    from geometry.placements import xml_number
    layers=layers_for(mode);axes=axes_for(mode);spec=parameter_spec(mode)
    nominal=a.run_dir/'step1/nominal.xml';base=getattr(a,'base_geometry',None) or nominal
    reference=getattr(a,'reference_geometry',None) or nominal
    verify_survey(nominal,reference,orientation_layers=layers)
    verify_scope(reference,base,layers,axes)
    current=placement_transforms(base);survey=placement_transforms(reference)
    params=read_pede(a.run_dir/'step4/millepede.res')
    selected={family+l for l in layers for _,family,_ in spec}
    if not selected<=params.keys() or any(not math.isfinite(v) or (v!=0 and k not in selected) for k,v in params.items()):
        raise ValueError('Invalid coupled alignment parameter scope')
    angular={f'L{l}_{axis}':sign*params[family+l] for l in layers for axis,family,sign in spec if axis.startswith('r')}
    linear={f'L{l}_{axis}':sign*params[family+l] for l in layers for axis,family,sign in spec if not axis.startswith('r')}
    if any(abs(v)>.1 for v in angular.values()):raise ValueError('Coupled rotation increment exceeds 0.1 rad component bound')
    updated={};applied={}
    for l in layers:
        vector=tuple(angular[f'L{l}_r{axis}'] for axis in 'xyz')
        if math.sqrt(sum(v*v for v in vector))>.1:raise ValueError('Coupled rotation vector exceeds 0.1 rad norm bound')
        updated[l]=current[l].updated(rotation=rotation_exp(vector),pivot=current[l].translation,
            translation=tuple(linear.get(f'L{l}_{axis}',0.) for axis in 'xyz'))
        relative=rotation_log(multiply(updated[l].rotation,transpose(survey[l].rotation)))
        applied.update({f'L{l}_r{axis}':relative[i] for i,axis in enumerate('xyz')})
    root=ET.parse(base).getroot();constants={c.get('name'):c.get('value') for c in root.findall('./define/constant')}
    z_offsets={l:xml_number(root.find(f"./detectors/detector[@name='SiMAPS']/layer[@id='{l}']/ring").get('global_z','0*mm'),constants)+linear[f'L{l}_z'] for l in layers} if linear else None
    p=stage(a.run_dir,'step5')
    write_shifted_xml(base,p/'corrected.xml',{l:t.translation[0] for l,t in updated.items()} if linear else {},
        {l:t.translation[1] for l,t in updated.items()} if linear else None,z_shifts=z_offsets,
        rotations={l:t.rotation for l,t in updated.items()})
    info=dict(mode=mode,delta_rad_by_component=angular,applied_rad_by_component=applied,
        rotation_matrices={str(l):t.rotation for l,t in updated.items()},
        pivots_mm={str(l):current[l].translation for l in layers},
        base_geometry_sha256=digest(base),reference_geometry_sha256=digest(reference),
        convention='Rnew=Exp([physical Global rx,ry,rz]) Rcurrent about current sensitive center; translation after rotation; cumulative vectors are Log(Rnew Rsurvey^T), never Euler state')
    if linear:info.update(delta_mm_by_component=linear,applied_mm_by_component={f'L{l}_{axis}':t.translation[i] for l,t in updated.items() for i,axis in enumerate('xyz')})
    done(p,**info)


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--reference-geometry',type=Path,help='Explicit fixed survey/reference for selected scope checks; unselected placements are preserved')
    parser.add_argument('--mode',choices=[*SO3_MODES,'l1_rx','l1_ry','l2_x','l1_l2_x','l1_l2_xy','l1_rz','l1_l2_rz','l1_l2_xy_rz','l1_z','l1_l2_z','l1_l2_xyz'],default='l2_x',help='Explicit validated correction scope; default preserves L2-only behavior')
    parser.add_argument('--base-geometry',type=Path,help='Opt-in cumulative selected update from current reconstruction Geometry; default remains nominal-based')
    parser.add_argument('--check-only', action='store_true', help='Check Geometry support without applying a correction or requiring alignment')
    run(correct, parser)
