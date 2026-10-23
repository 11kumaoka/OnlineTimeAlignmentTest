"""Profile actual covariance-whitened Mille rows for an experimental tilt mode."""
import argparse
import math
import json,re
import numpy as np
from geometry.placements import placement_transforms
from pathlib import Path
from research_common import write_json,digest
from validation.z_observability import measurements,information
from correction.scope import SO3_MODES,parameter_spec,layers_for


def diagnose(mille,labels=(5001,)):
    blocks=list(measurements(mille))
    if not blocks:raise ValueError('No accepted tracks in tilt design')
    selected=information(blocks,list(labels))
    selected['nominal_sigma_by_label']=selected.pop('sigma_mm')
    if all(3000<=k<4000 or k>=5000 for k in labels):selected['nominal_sigma_rad']=selected['nominal_sigma_by_label']
    report={'tracks':len(blocks),'mille_sha256':digest(mille),'selected':selected,
            'parameter_units':{str(label):('rad' if 3000<=label<4000 or label>=5000 else 'mm') for label in labels},
            'method':'Actual whitened Mille rows; four local parameters profiled independently per track',
            'uncertainty_model':'Formal information only; not statistically calibrated'}
    eigen=selected['column_normalized_eigenvalues']
    selected['column_normalized_condition']=max(eigen)/min(eigen) if min(eigen)>1e-9 else None
    command=mille.parent/'command.json';log=mille.parent/'stdout.log'
    if command.exists() and log.exists():
        arguments=json.loads(command.read_text())['argv']
        geometries=[v.split('=',1)[1] for v in arguments if v.startswith('-Pdd4hep:xml_files=')]
        if len(geometries)!=1:raise ValueError('Missing unique selected Geometry')
        placements=placement_transforms(Path(geometries[0]))
        refs=re.findall(r'BeamTestTiltReference record=(\d+) tx=(\S+) ty=(\S+)',log.read_text())
        if len(refs)!=len(blocks):raise ValueError('Reference trajectories do not match Mille records')
        import uproot,awkward as ak
        with uproot.open(mille.parent/'reco.root') as file:
            tree=file['events'];read=lambda key:ak.to_list(tree['LocalSiMAPSRecHits/LocalSiMAPSRecHits.'+key].array())
            ids=read('cellID');xyz=[read('position.'+axis) for axis in 'xyz']
            accepted=ak.to_list(ak.num(tree['LocalBeamTestTracks/LocalBeamTestTracks.chi2'].array()))
        source_points=[]
        for event,count in enumerate(accepted):
            if not count:continue
            points=[]
            for l in range(5):
                choices=[j for j,cell in enumerate(ids[event]) if (cell>>11)&63==l]
                if len(choices)!=1:raise ValueError('Ambiguous accepted source RecHits in tilt design')
                points.append(np.array([xyz[k][event][choices[0]] for k in range(3)]))
            source_points.append(points)
        if len(source_points)!=len(blocks):raise ValueError('Accepted source RecHits do not match Mille records')
        slopes=[];coverage={str(l):[] for l in range(5)};augmented=[]
        for index,rows in enumerate(blocks):
            if int(refs[index][0])!=index:raise ValueError('Reference trajectory order mismatch')
            tx,ty=map(float,refs[index][1:]);slopes.append([tx,ty]);newrows=[]
            for l in range(5):
                pair=rows[2*l:2*l+2]
                w=np.array([[r[2].get(1,0.),r[2].get(2,0.)] for r in pair])
                m=source_points[index][l]
                if not np.allclose(w@m[:2],[r[0] for r in pair],rtol=2e-6,atol=1e-4):raise ValueError('Mille measurement/source RecHit mismatch')
                offset=m-np.array(placements[l].translation);coverage[str(l)].append(m.tolist())
                columns={1000+l:np.array([1.,0.]),2000+l:np.array([0.,1.]),4000+l:np.array([tx,ty])}
                for axis,label,sign in [(0,5000,1),(1,6000,1),(2,3000,-1)]:
                    dm=np.cross(np.eye(3)[axis],offset)
                    columns[label+l]=sign*np.array([tx*dm[2]-dm[0],ty*dm[2]-dm[1]])
                columns={k:w@v for k,v in columns.items()}
                for component,r in enumerate(pair):
                    globals=dict(r[3])
                    for label,values in columns.items():
                        if label in globals and not np.isclose(globals[label],values[component],rtol=3e-5,atol=3e-5):raise ValueError('Actual Mille/global differential design mismatch')
                        globals[label]=float(values[component])
                    newrows.append((r[0],r[1],r[2],globals))
            augmented.append(newrows)
        values=np.array(slopes)
        report['reference_slopes']={'values':slopes,'mean':values.mean(0).tolist(),'sample_sd':values.std(0,ddof=1).tolist(),'min':values.min(0).tolist(),'max':values.max(0).tolist(),'covariance':np.cov(values.T).tolist()}
        report['spatial_coverage_mm']={l:{'mean':np.mean(v,axis=0).tolist(),'sample_sd':np.std(v,axis=0,ddof=1).tolist(),'min':np.min(v,axis=0).tolist(),'max':np.max(v,axis=0).tolist()} for l,v in coverage.items()}
        design={}
        for name,layers in [('L1_six_dof',[1]),('L1_L2_six_dof',[1,2]),
                            ('L1_L2_L3_six_dof_fixed_L0_L4',[1,2,3]),
                            ('all_SiMAPS_six_dof_no_fixed_sensor',list(range(5)))]:
            info=information(augmented,[base+l for l in layers for base in (1000,2000,4000,5000,6000,3000)])
            info['nominal_sigma_by_label']=info.pop('sigma_mm');e=info['column_normalized_eigenvalues']
            info['column_normalized_condition']=max(e)/min(e) if min(e)>1e-9 else None
            design[name]=info
        report['six_dof_design_only']={'warning':'Hypothetical additional columns derived from current points and frozen reference slopes; not a released six-DOF writer/solver or closure validation',
            'reference_constraints':'All unselected sensors fixed; four local trajectory parameters profiled per track. The all-sensor design has no fixed references and requires an explicit gauge strategy regardless of its noisy numerical rank' ,
            'units':'1000/2000/4000 parameters mm; 3000/5000/6000 parameters rad',**design}
    return report



def enforce(report,max_sigma_rad,max_sigma_mm=None):
    info=report['selected'];errors=info['nominal_sigma_by_label']
    if info['rank']!=len(info['labels']) or errors is None:raise ValueError('Unobservable selected tilt design')
    if not math.isfinite(max_sigma_rad) or max_sigma_rad<=0:raise ValueError('Invalid tilt sensitivity bound')
    for label,value in errors.items():
        angular=3000<=int(label)<4000 or int(label)>=5000
        bound=max_sigma_rad if angular else max_sigma_mm
        if bound is None or not math.isfinite(bound) or bound<=0 or value>bound:raise ValueError('Insufficient coupled information for declared parameter resolution')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mille',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mode',choices=[*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry'],default='l1_rx')
    p.add_argument('--max-sigma-rad',type=float,required=True)
    p.add_argument('--max-sigma-mm',type=float,help='Required for mixed translation/rotation designs')
    a=p.parse_args()
    # Read-only design diagnostics remain available for archived, disabled modes.
    labels={'l1_rx':(5001,),'l1_ry':(6001,),'l1_rx_ry':(5001,6001),'l1_l2_rx_ry':(5001,6001,5002,6002)}.get(a.mode)
    if a.mode in SO3_MODES:labels=tuple(family+l for l in layers_for(a.mode) for _,family,_ in parameter_spec(a.mode))
    report=diagnose(a.mille,labels)
    if a.mode in ('l1_rx_ry','l1_l2_rx_ry'):report['mode_status']='Unsupported for inference; this is a read-only information diagnostic'
    try:enforce(report,a.max_sigma_rad,a.max_sigma_mm)
    except ValueError as error:
        write_json(a.output,dict(report,passed=False,reason=str(error)));raise
    write_json(a.output,dict(report,passed=True,max_sigma_rad=a.max_sigma_rad))
    print('PASS',report['tracks'],'tracks',report['selected']['nominal_sigma_by_label'])


if __name__=='__main__':main()
