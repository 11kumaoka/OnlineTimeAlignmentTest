#!/usr/bin/env python3
"""Offline Truth-assisted residual attribution; never used to infer corrections.

Freeze the existing native design and decompose its initial Schur estimate into
pixel rounding, finite-pose linearization, and reference-state contributions.
No reconstruction, covariance, steering or historical artifact is modified.
"""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from research_common import REPO,write_json,digest,require


def projected_parts(a,g,parts):
    """Use the existing four-local-parameter QR projection for offline attribution."""
    assert np.linalg.matrix_rank(a)==4
    q,_=np.linalg.qr(a);p=np.eye(len(a))-q@q.T
    return g.T@p@g,{name:g.T@p@value for name,value in parts.items()}


def analyze(run):
    for name in ('data','nominal','solve','postsolve','physical_derivatives','corrected_physical_derivatives','validation'):require(run,name)
    native=json.loads((run/'nominal/mille.json').read_text())
    truth=json.loads((run/'data/shifted/channels_truth.json').read_text())
    nominal=json.loads((run/'data/control/channels_truth.json').read_text())
    fixture=json.loads((run/'geometry/rotation_fixture.json').read_text())
    assert fixture['mode'] in ('l1_rx_ry_rz','l1_rx_ry_rz_negative')
    assert len(native['events'])==len(truth['events'])
    injection=np.array(fixture['injected_rotation_vector_rad'])
    h=[];scores=[];positions=[];slopes=[];quant=[];phases=[];residuals=[]
    for event,source in zip(native['events'],truth['events']):
        a=[];g=[];parts={k:[] for k in ('pixel','finite_pose','reference','observed')}
        event_quant=[];event_phase=[];event_residual=[]
        origin=np.array(source['origin_mm']);direction=np.array(source['direction'])
        for e in event['equations']:
            layer=e['layer'];sensor=nominal['sensors'][layer];channel=source['channels'][layer]
            rotation=np.array(sensor['acts_rotation']);center=np.array(sensor['center_mm'])
            normal=rotation[:,2];point=origin+direction*(normal@(center-origin))/(normal@direction)
            unrotated=(rotation.T@(point-center))[:2]
            mapping=rotation.T@np.array(sensor['dd4hep_rotation'])
            x,z=channel['sensor_x_z_mm'];exact=(mapping@np.array([x,0.,z]))[:2]
            measured=np.array(e['measurement']).ravel();prediction=np.array(e['prediction']).ravel()
            pixel=measured-exact;finite=exact-unrotated;reference=unrotated-prediction
            w=np.array(e['whitening']);global_=np.array(e['global'])[:,3:6] if layer==1 else np.zeros((2,3))
            a.extend(w@e['local']);g.extend(w@global_)
            for key,value in [('pixel',pixel),('finite_pose',finite-global_@injection),('reference',reference),('observed',measured-prediction)]:parts[key].extend(w@value)
            pitch=np.array(channel['pitch_x_z_mm']);sensor_error=(mapping.T@np.r_[pixel,0.])[[0,2]]
            assert np.all(np.abs(sensor_error)<=pitch/2+3e-6)
            event_quant.append(pixel);event_phase.append(np.mod(np.array([x,z])/pitch,1.));event_residual.append(measured-prediction)
        matrix,rhs=projected_parts(np.array(a),np.array(g),{k:np.array(v) for k,v in parts.items()})
        h.append(matrix);scores.append(rhs);positions.append(source['channels'][1]['sensor_x_z_mm'])
        slopes.append(direction[1:]/direction[0]);quant.append(event_quant);phases.append(event_phase);residuals.append(event_residual)
    h=np.array(h);positions=np.array(positions);slopes=np.array(slopes);quant=np.array(quant);phases=np.array(phases);residuals=np.array(residuals)
    def summarize(mask):
        n=h[mask].sum(axis=0);assert np.linalg.matrix_rank(n)==3
        sums={name:sum((row[name] for row,take in zip(scores,mask) if take),np.zeros(3)) for name in scores[0]}
        attributed={name:np.linalg.solve(n,value) for name,value in sums.items()}
        assert np.allclose(attributed['observed']-injection,sum(attributed[k] for k in ('pixel','finite_pose','reference')),atol=2e-11,rtol=0)
        return {'tracks':int(mask.sum()),'initial_estimate_rad':attributed['observed'].tolist(),
            'error_rad':(attributed['observed']-injection).tolist(),
            'pixel_contribution_rad':attributed['pixel'].tolist(),'finite_pose_contribution_rad':attributed['finite_pose'].tolist(),
            'reference_contribution_rad':attributed['reference'].tolist(),'sigma_rad':np.sqrt(np.diag(np.linalg.inv(n))).tolist()}
    count=len(h);full=summarize(np.ones(count,dtype=bool))
    solver=json.loads((run/'solve/independent.json').read_text())
    assert np.allclose(full['initial_estimate_rad'],solver['schur_solution'],atol=1e-10,rtol=0)
    prefix={str(n):summarize(np.arange(count)<n) for n in (64,256,1024,2048,count)}
    subsets={}
    for name,v in [('slope',np.linalg.norm(slopes,axis=1)),('impact',np.linalg.norm(positions,axis=1)),('phase_x',phases[:,1,0]),('phase_z',phases[:,1,1])]:
        middle=float(np.median(v))
        for side,mask in [('lower',v<=middle),('upper',v>middle)]:subsets[name+'_'+side]={'median_split':middle,**summarize(mask)}
    layers={}
    for layer in range(5):
        correlations={}
        for axis in range(2):
            for name,v in [('position_x',positions[:,0]),('position_z',positions[:,1]),('slope_y',slopes[:,0]),('slope_z',slopes[:,1])]:
                correlations[f'residual_{axis}_vs_{name}']=float(np.corrcoef(residuals[:,layer,axis],v)[0,1])
        layers[layer]={'pixel_mean_uv_mm':quant[:,layer].mean(axis=0).tolist(),
            'pixel_rms_uv_mm':np.sqrt(np.mean(quant[:,layer]**2,axis=0)).tolist(),
            'phase_histogram_x_z':[np.histogram(phases[:,layer,j],bins=10,range=(0.,1.))[0].tolist() for j in range(2)],
            'residual_correlations':correlations}
    return {'run':str(run),'mode':fixture['mode'],'seed':truth['beam_recipe']['seed'],'injection_rad':injection.tolist(),
        'full':full,'prefixes':prefix,'subsets':subsets,'layers':layers,
        'initial_and_post_parameters':{'initial':solver['parameters'],'post':json.loads((run/'postsolve/independent.json').read_text())['parameters']},
        'nominal_and_corrected_fd_max':[json.loads((run/s/'report.json').read_text())['maximum_error_mm_per_rad'] for s in ('physical_derivatives','corrected_physical_derivatives')],
        'input_sha256':digest(run/'data/shifted.root'),'native_sha256':digest(run/'nominal/mille.json'),
        'method':'Exact frozen-native-design decomposition, all five sensors; Truth used only for offline validation, no correction inference',
        'statistical_coverage_validated':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.output.resolve().is_relative_to(REPO/'result'):p.error('Use a new result/ output')
    if a.output.exists():p.error('Output must be a new file')
    reports=[analyze(run.resolve()) for run in a.runs];a.output.parent.mkdir(exist_ok=True,parents=True)
    write_json(a.output,{'runs':reports,'independent_seeds':sorted({r['seed'] for r in reports}),'truth_used_for_alignment':False})

if __name__=='__main__':main()
