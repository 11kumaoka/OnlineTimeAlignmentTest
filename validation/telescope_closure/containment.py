"""Read-only physical box diagnostics; never constrain or change a Pede fit."""
import itertools
import numpy as np


def corners_in_module(center, rotation, module_center, module_rotation,
                      sensitive_half, module_half):
    """Transform all eight sensitive corners into the actual parent frame."""
    corners=np.array(list(itertools.product((-1.,1.),repeat=3)))*sensitive_half
    world=corners@np.asarray(rotation).T+center
    local=(world-module_center)@np.asarray(module_rotation)
    maximum=np.max(np.abs(local),axis=0)
    return {'global_corners_mm':world.tolist(),'module_corners_mm':local.tolist(),
            'maximum_absolute_module_mm':maximum.tolist(),
            'clearance_mm':(np.asarray(module_half)-maximum).tolist(),
            'contained':bool(np.all(maximum<module_half))}


def ellipsoid_offsets(covariance, radius=5.):
    """Deterministic sampled joint-error directions plus coordinate extrema.

    Sampling is an engineering preflight, not proof of containment everywhere
    in the ellipsoid or a statement of calibrated statistical coverage.
    """
    covariance=np.asarray(covariance)
    if covariance.shape!=(4,4) or not np.isfinite(covariance).all():
        raise ValueError('Expected finite four-parameter covariance')
    root=np.linalg.cholesky(covariance)
    directions=[np.array(v,dtype=float) for v in itertools.product((-1,0,1),repeat=4) if any(v)]
    for i in range(4):
        # Maximize each physical coordinate, retaining covariance correlations.
        directions.extend([root[i],-root[i]])
    return [radius*root@(v/np.linalg.norm(v)) for v in directions]


def expected_refusal(original, build, output):
    """Reproduce the original fit and refuse its invalid pose before tracking."""
    import json
    from pathlib import Path
    from research_common import stage,execute,done,require,write_json,digest,prefix
    from alignment.pede import read_pede
    from geometry.transforms import rotation_exp
    from validation.telescope_closure.closure import displaced_xml,environment,MODULE_TO_GLOBAL
    from validation.telescope_closure.rotation import pose_checks
    for name in ('geometry','data','nominal','physical_derivatives','solve'):require(original,name)
    fixture=json.loads((original/'geometry/rotation_fixture.json').read_text())
    source=json.loads((original/'data/shifted/channels_truth.json').read_text())
    if fixture['mode']!='l1_y_rx_ry_rz_negative' or source['beam_recipe']['seed']!=2026102502:
        raise ValueError('This safety regression pins the original stopped fixture')
    output.mkdir()  # Exclusive: preserve previous failures and successful audits.
    q=stage(output,'pede');steering=(original/'solve/pede.txt').read_text()
    (q/'pede.txt').write_text(steering)
    execute([prefix()/'bin/pede','pede.txt'],q,env=environment(build))
    assert (q/'millepede.res').read_bytes()==(original/'solve/millepede.res').read_bytes()
    values=read_pede(q/'millepede.res')
    summary=json.loads((original.parent/'native_y_rotations_20261024_01_audit/cohort_summary/output/report.json').read_text())
    rows=[r for r in summary['runs'] if r['seed']==2026102502 and r['mode']==fixture['mode']]
    assert len(rows)==1 and not rows[0]['passed_closure']
    assert rows[0]['fitted_mixed_units']==[values[k] for k in (700102,700104,700105,700106)]
    w=[values[k] for k in (700104,700105,700106)]
    displaced_xml(original/'geometry/fixtures/nominal.xml',output/'candidate.xml',{1:values[700102]},rotations={1:w},rotation_axis='xyz')
    probe=stage(output,'actual_geometry')
    execute([build/'TelescopeChannels',output/'candidate.xml',0,probe/'geometry.json'],probe,env=environment(build))
    before=json.loads((original/'data/control/channels_truth.json').read_text())['sensors']
    actual=json.loads((probe/'geometry.json').read_text())['sensors']
    a,b=before[1],actual[1];q=np.array(rotation_exp(w))
    for key in ('acts_rotation','dd4hep_rotation'):
        np.testing.assert_allclose(b[key],q@a[key],atol=2e-12,rtol=0)
    np.testing.assert_allclose(b['center_mm'],np.array(a['center_mm'])+[0,values[700102],0],atol=1e-9,rtol=0)
    assert (a['volume_id'],a['geometry_id'])==(b['volume_id'],b['geometry_id'])
    bounds=corners_in_module(np.array(b['center_mm']),np.array(b['dd4hep_rotation']),np.array([300.,0.,0.]),np.array(MODULE_TO_GLOBAL),np.array([50.,.025,50.]),np.array([50.25,50.25,.325]))
    truth=source['sensors'][1]
    truth_bounds=corners_in_module(np.array(truth['center_mm']),np.array(truth['dd4hep_rotation']),np.array([300.,0.,0.]),np.array(MODULE_TO_GLOBAL),np.array([50.,.025,50.]),np.array([50.25,50.25,.325]))
    assert not bounds['contained'] and truth_bounds['contained']
    try:pose_checks(before,actual,{1:values[700102]},{1:w},axis='xyz')
    except AssertionError:pass
    else:raise AssertionError('Expected physical containment refusal was bypassed')
    assert not (original/'corrected').exists()
    write_json(output/'report.json',{'classification':'EXPECTED_PHYSICAL_CONTAINMENT_REFUSAL',
        'safety_regression_passed':True,'physical_closure_passed':False,'candidate_reconstructed':False,
        'pede_reproduced_byte_identically':True,'failed_fit_retained_in_initial_statistics':True,'candidate_bounds':bounds,'truth_bounds':truth_bounds,
        'input_sha256':digest(original/'data/shifted.root'),'original_candidate_sha256':digest(original/'correction/corrected.xml'),
        'first_order_radial_half_extent_mm':.025+50*(abs(w[1])+abs(w[2])),
        'nominal_module_half_thickness_mm':.325,'geometry_activated':False})
    done(output,passed=True,classification='EXPECTED_PHYSICAL_CONTAINMENT_REFUSAL',physical_closure_passed=False)



def preflight(original, build, output, prior_checkpoint):
    """Geometry-only prior-information design; never reads new fitted estimates."""
    import json
    from research_common import stage,execute,done,write_json,digest
    from validation.telescope_closure.closure import displaced_xml,environment,MODULE_TO_GLOBAL
    from validation.telescope_closure.rotation import pose_checks
    from geometry.transforms import rotation_exp
    output.mkdir()
    nominal=original/'geometry/fixtures/nominal.xml'
    base=json.loads((original/'data/control/channels_truth.json').read_text())['sensors']
    previous=json.loads(prior_checkpoint.read_text())['cases'];reports=[]
    for sign in (1,-1):
        w=sign*np.array([.0018,.001,-.001]);q=stage(output,'positive' if sign==1 else 'negative')
        displaced_xml(nominal,q/'truth.xml',{1:.150},rotations={1:w},rotation_axis='xyz')
        execute([build/'TelescopeChannels',q/'truth.xml',0,q/'geometry.json'],q,env=environment(build))
        actual=json.loads((q/'geometry.json').read_text())['sensors']
        pose_checks(base,actual,{1:.150},{1:w},axis='xyz');candidates=[]
        for case in previous:
            for delta in ellipsoid_offsets(case['initial_selected_design']['covariance_mixed_units']):
                values=np.r_[.150,w]+1.1*delta
                rotation=np.array(rotation_exp(values[1:]))@base[1]['dd4hep_rotation']
                box=corners_in_module(np.array([300.,values[0],0.]),rotation,np.array([300.,0.,0.]),np.array(MODULE_TO_GLOBAL),np.array([50.,.025,50.]),np.array([50.25,50.25,.325]))
                assert box['contained'],(sign,values,box)
                candidates.append({'parameters':values.tolist(),'clearance_mm':box['clearance_mm'],'prior_seed':case['seed']})
        worst=[]
        for axis in range(3):
            selected=min(candidates,key=lambda v:v['clearance_mm'][axis]);v=selected['parameters'];probe=stage(q,'worst_axis_'+str(axis))
            displaced_xml(nominal,probe/'geometry.xml',{1:v[0]},rotations={1:v[1:]},rotation_axis='xyz')
            execute([build/'TelescopeChannels',probe/'geometry.xml',0,probe/'geometry.json'],probe,env=environment(build))
            poses=json.loads((probe/'geometry.json').read_text())['sensors']
            pose_checks(base,poses,{1:v[0]},{1:v[1:]},axis='xyz');worst.append(selected)
        reports.append({'sign':sign,'injection_mm_rad':[.150,*w],'samples':len(candidates),'minimum_clearance_module_mm':np.min([v['clearance_mm'] for v in candidates],axis=0).tolist(),'worst_sampled_poses':worst})
    write_json(output/'report.json',{'passed':True,'option':'A: unchanged geometry','joint_nominal_radius':5,'design_only_sigma_margin':1.1,'coverage_claim':False,'all_covariances_from_previous_six_initial_fits':True,'reports':reports,'prior_checkpoint_sha256':digest(prior_checkpoint)})
    done(output,passed=True)


def main():
    import argparse
    from pathlib import Path
    from research_common import REPO
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step',choices=['preflight','expected-refusal'],default='expected-refusal')
    parser.add_argument('--prior-checkpoint',type=Path,default=REPO/'result/native_y_rotations_20261024_01_audit/final_checkpoint.json')
    parser.add_argument('--original-run',type=Path,required=True)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();output=args.output_dir.resolve()
    if not output.is_relative_to(REPO/'result') or output==REPO/'result':parser.error('Use a new child of result/')
    if args.step=='preflight':preflight(args.original_run.resolve(),args.build.resolve(),output,args.prior_checkpoint.resolve())
    else:expected_refusal(args.original_run.resolve(),args.build.resolve(),output)


if __name__=='__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    main()
