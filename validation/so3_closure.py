"""Noiseless production-Mille/Pede closure gate; never activates Geometry.

Simulation Truth creates fixed continuous local coordinates and is used only
for post-fit matrix comparisons. Inference receives current coordinates only.
This is a mathematical diagnostic, not Geant4 or RawHit statistical validation.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import shutil
from types import SimpleNamespace
import numpy as np
from alignment.pede import read_pede
from geometry.prepare import DEFAULT_NOMINAL,write_shifted_xml
from geometry.placements import placement_transforms
from geometry.transforms import (RigidTransform,axis_rotation,multiply,rotation_exp,
                                 orientation_distance,rotation_log)
from research_common import digest,write_json,done,REPO,prefix
from correction.correct_geometry import correct
from validation.z_observability import measurements,information


def generate_local(target,seed,count=100):
    rng=np.random.default_rng(seed);points=[]
    for _ in range(count):
        theta=rng.uniform(.01,.03);phi=rng.uniform(0,2*np.pi)
        direction=np.array([np.tan(theta)*np.cos(phi),np.tan(theta)*np.sin(phi),1.])
        origin=np.r_[rng.normal(0,.2,2),-500.];track=[]
        for l in range(5):
            t=target[l];r=np.array(t.rotation);c=np.array(t.translation);n=r[:,2]
            world=origin+np.dot(n,c-origin)/np.dot(n,direction)*direction
            track.append((r.T@(world-c)).tolist())
        points.append(track)
    return points


def run_case(output,binary,name,target_rotations,translations=None,two=False,six=False,initial_rotations=None,scope_mode=None):
    output.mkdir();translations=translations or {}
    from correction.scope import layers_for
    correction_mode=scope_mode or (('l1_l2_' if two else 'l1_')+('six_dof' if six else 'rotations'))
    layers=layers_for(correction_mode)
    model_files=('geometry/transforms.py','correction/correct_geometry.py','correction/scope.py','localDetEICrecon/alignment/src/BeamTestMilleWriter.cc','localDetEICrecon/alignment/src/BeamTestMilleWriter.h','localDetEICrecon/alignment/src/TiltMeasurementModel.h','validation/tilt_writer_fixture.cc','validation/so3_closure.py')
    model_hashes={p:digest(REPO/p) for p in model_files}
    survey=output/'survey.xml'
    # Nonzero known centers exercise the pivot without supplying injected shifts.
    known={l:(1.25,-.75,2.) for l in sorted({1,2,*layers})}
    write_shifted_xml(DEFAULT_NOMINAL,survey,{l:v[0] for l,v in known.items()},
                      {l:v[1] for l,v in known.items()},z_shifts={l:v[2] for l,v in known.items()},rotations=initial_rotations)
    initial=placement_transforms(survey);target=dict(initial)
    for l,r in target_rotations.items():
        target[l]=RigidTransform(r,tuple(a+b for a,b in zip(initial[l].translation,translations.get(l,(0.,0.,0.)))))
    local=generate_local(target,2035033001);fixed=output/'fixed_local_points.json'
    write_json(fixed,{'kind':'Noiseless continuous-channel fixture; physical sigma 0.01 mm unchanged','points':local})
    checksum=digest(fixed);current=survey;history=[]
    families=(1000,2000,4000,5000,6000,3000) if six else (5000,6000,3000)
    selected=[base+l for l in layers for base in families]
    for iteration in range(1,21):
        d=output/f'iteration-{iteration:03d}';d.mkdir();placements=placement_transforms(current);text=[]
        for l in range(5):
            t=placements[l];r=np.array(t.rotation);text.extend(map(str,[*t.translation,*r[:,0],*r[:,1]]))
        text.append(str(len(local)))
        for track in local:
            for l in range(5):text.extend(map(str,[*placements[l].apply(track[l]),.01,.01]))
        inp=d/'fixture.txt';inp.write_text(' '.join(text)+'\n')
        mode='three_six_dof' if len(layers)==3 else (('two_' if len(layers)==2 else '')+('six_dof' if six else 'rotations'))
        command=[str(binary),str(inp),str(d/'mille.dat'),str(layers[0]),mode]
        with (d/'writer.log').open('x') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
        blocks=list(measurements(d/'mille.dat'));info=information(blocks,selected)
        if info['rank']!=len(selected):raise ValueError(f'Rank deficient {name}: {info["rank"]}/{len(selected)}')
        labels=sorted({label for rows in blocks for row in rows for label in row[3]})
        steering='Cfiles\n'+str(d/'mille.dat')+'\n\nentries 5\nmethod inversion 3 0.001\n\nParameter\n'
        steering+=''.join(f'{label} 0.0 {1.0 if label in selected else -1.0}\n' for label in labels)+'\nprintcounts\nend\n'
        (d/'pede.txt').write_text(steering)
        with (d/'pede_stdout.log').open('x') as log:
            process=subprocess.run([str(prefix()/'bin/pede'),'pede.txt'],cwd=d,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,LD_LIBRARY_PATH=str(prefix()/'lib')+':'+os.environ.get('LD_LIBRARY_PATH','')))
        status=(d/'millepede.end').read_text().strip()
        if process.returncode or status.split()[0] not in ('0','1'):raise ValueError('Official solver failure '+status)
        params=read_pede(d/'millepede.res');updated={};errors={};centers={};increments={}
        for l in layers:
            vector=(params[5000+l],params[6000+l],-params[3000+l])
            delta=(-params[1000+l],-params[2000+l],params[4000+l]) if six else (0.,0.,0.)
            updated[l]=placements[l].updated(rotation=rotation_exp(vector),translation=delta,pivot=placements[l].translation)
            increments[str(l)]={'rotation_vector_rad':vector,'translation_mm':delta}
        # Only post-fit validation accesses target transforms.
        for l in layers:
            errors[str(l)]=orientation_distance(target[l].rotation,updated[l].rotation)
            centers[str(l)]=float(np.linalg.norm(np.array(target[l].translation)-updated[l].translation))
        # Exercise the maintained correction stage as well as the independent algebra.
        (d/'step1').mkdir();(d/'step4').mkdir()
        shutil.copyfile(DEFAULT_NOMINAL,d/'step1/nominal.xml')
        write_json(d/'step1/geometry_config.json',{'detector':'SiMAPS','global_x_shifts_mm':{}})
        done(d/'step1',kind='Noiseless scope fixture; no DD4hep QA claimed')
        shutil.copyfile(d/'millepede.res',d/'step4/millepede.res');done(d/'step4',status=status)
        correct(SimpleNamespace(run_dir=d,mode=correction_mode,base_geometry=current,reference_geometry=survey,check_only=False))
        new=d/'step5/corrected.xml'
        reloaded=placement_transforms(new)
        if any(reloaded[l]!=placements[l] for l in range(7) if l not in layers):raise ValueError('Unselected placement changed')
        if any(orientation_distance(t.rotation,reloaded[l].rotation)>1e-12 for l,t in updated.items()):raise ValueError('Matrix serialization changed the orientation')
        history.append({'iteration':iteration,'orientation_error_rad':errors,'center_error_mm':centers,
            'increments':increments,'information':info,'solver_status':status,'pede_exit':process.returncode,
            'fixed_local_sha256':checksum,'command':command,'geometry_sha256':digest(new)})
        current=new
        if max(errors.values())<1e-6 and max(centers.values())<2e-5:break
    passed=max(history[-1]['orientation_error_rad'].values())<1e-6 and max(history[-1]['center_error_mm'].values())<2e-5
    if digest(fixed)!=checksum:raise ValueError('Fixed local coordinates changed')
    if any(digest(REPO/p)!=sha for p,sha in model_hashes.items()):raise ValueError('Model source changed during the noiseless validation')
    report={'model_sources_sha256':model_hashes,'passed':passed,'fixture':name,'events':len(local),'iterations':history,'final_geometry':str(current),
            'writer_source_sha256':digest(REPO/'localDetEICrecon/alignment/src/BeamTestMilleWriter.cc'),
            'fixture_source_sha256':digest(REPO/'validation/tilt_writer_fixture.cc'),
            'initial_rotations':initial_rotations,'target_rotations':target_rotations,'physical_translations_mm':translations,'seed':2035033001,
            'note':'All target comparisons occur after inference. No noise or uncertainty coverage claim.'}
    write_json(output/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--writer-fixture',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--translation-scale',type=float,default=1.,help='Declared synthetic displacement scale for capture-range controls; does not change uncertainties or steering')
    p.add_argument('--three-layer-survey-fraction',type=float,default=0.,help='Declared fraction of target orientation in the three-layer fixture Survey only; 0 retains the nominal-start capture test')
    p.add_argument('--case',choices=['all','two_six_dof','l3_six_dof','three_six_dof'],default='all')
    a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    xy=multiply(axis_rotation('y',-.025),axis_rotation('x',.03))
    negative=multiply(axis_rotation('y',.025),axis_rotation('x',-.03))
    reverse=multiply(axis_rotation('x',.03),axis_rotation('y',-.025))
    rz=multiply(axis_rotation('z',.017),xy)
    r2=multiply(axis_rotation('z',-.012),multiply(axis_rotation('y',.02),axis_rotation('x',-.025)))
    cases=[('rx',{1:axis_rotation('x',.03)},{}),('ry',{1:axis_rotation('y',-.03)},{}),
           ('xy_positive',{1:xy},{}),('xy_negative',{1:negative},{}),('reverse_order',{1:reverse},{}),
           ('existing_rz',{1:rz},{'initial_rotations':{1:axis_rotation('z',.017)}}),
           ('two_rotations',{1:rz,2:r2},{'two':True}),
           ('l1_six_dof',{1:rz},{'six':True,'translations':{1:(.15,-.12,2.)}}),
           ('two_six_dof',{1:rz,2:r2},{'two':True,'six':True,'translations':{1:(.15,-.12,2.),2:(.2,.09,-1.5)}}),
           ('l3_six_dof',{3:rz},{'six':True,'scope_mode':'l3_six_dof','translations':{3:(.12,-.08,.8)}}),
           ('three_six_dof',{1:rz,2:r2,3:rz},{'six':True,'scope_mode':'l1_l2_l3_six_dof','translations':{1:(.08,-.06,.8),2:(-.1,.08,-.6),3:(.12,-.08,.8)}})]
    if not 0<=a.three_layer_survey_fraction<1:raise ValueError('Survey fraction must be in [0,1)')
    if a.three_layer_survey_fraction:
        for name,rotations,options in cases:
            if name=='three_six_dof':options['initial_rotations']={l:rotation_exp(tuple(a.three_layer_survey_fraction*v for v in rotation_log(r))) for l,r in rotations.items()}
    if a.case!='all':cases=[case for case in cases if case[0]==a.case]
    reports=[]
    for name,rotations,options in cases:
        if 'translations' in options:options['translations']={l:tuple(a.translation_scale*v for v in shift) for l,shift in options['translations'].items()}
        report=run_case(a.output/name,a.writer_fixture.resolve(),name,rotations,**options);reports.append(report)
        print(name,report['passed'],len(report['iterations']),report['iterations'][-1]['orientation_error_rad'],flush=True)
        if not report['passed']:break
    write_json(a.output/'report.json',{'passed':len(reports)==len(cases) and all(r['passed'] for r in reports),'cases':reports,
        'writer_fixture_sha256':digest(a.writer_fixture),'parameterization':'Left Global SO(3) exponential, physical vector (5000+,6000+,-3000+), current sensitive-center pivot'})
    if not all(r['passed'] for r in reports):raise SystemExit(1)


if __name__=='__main__':main()
