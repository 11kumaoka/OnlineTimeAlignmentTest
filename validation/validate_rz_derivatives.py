"""Fresh DD4hep finite differences and actual official-Mille Rz derivative checks.

F = track prediction + bias - global measurement. Bias a_rz is opposite
physical correction c_rz, so dF/da_rz = (-(y-cy), x-cx) in mm/rad.
"""
import argparse
import json
import math
import struct
import subprocess
import sys
from pathlib import Path
from geometry.prepare import write_shifted_xml
from geometry.environment import geometry_environment
from research_common import REPO,write_json,digest,require


def records(path):
    with path.open('rb') as stream:
        while header:=stream.read(4):
            words=struct.unpack('<i',header)[0]
            if words<=0 or words%2:raise ValueError('Expected official single-precision records')
            n=words//2
            yield zip(struct.unpack('<'+'f'*n,stream.read(4*n)),struct.unpack('<'+'i'*n,stream.read(4*n)))


def check_binary(path,reco,pivot,layer=1):
    import uproot,awkward as ak,numpy as np
    with uproot.open(reco) as f:
        tree=f['events'];fields={s:ak.to_list(tree[f'LocalSiMAPSRecHits/LocalSiMAPSRecHits.{s}'].array()) for s in ['cellID','position.x','position.y']}
        accepted=ak.to_list(tree['LocalBeamTestTracks/LocalBeamTestTracks.ndf'].array())
    expected=[]
    for event,tracks in enumerate(accepted):
        if not tracks:continue
        hits=[i for i,c in enumerate(fields['cellID'][event]) if (c>>11)&63==layer]
        if len(hits)!=1:raise AssertionError('Ambiguous L1 track hit')
        i=hits[0];expected.extend([float(np.float32(-(fields['position.y'][event][i]-pivot[1]))),float(np.float32(fields['position.x'][event][i]-pivot[0]))])
    actual=[value for record in records(path) for value,label in record if label==3000+layer]
    if actual!=expected:raise AssertionError('Actual Mille rotation derivatives differ from associated hit/pivot')
    return len(actual)


def merge_gate(current,previous):
    """Combine immutable, successful label evidence from the same plugin."""
    if current.get('passed') is not True or previous.get('passed') is not True or previous['plugin_sha256']!=current['plugin_sha256']:
        raise ValueError('Additional derivative gate belongs to another plugin or failed validation')
    entries=previous.get('derivative_reports') or [{'path':previous['derivative_report'],'sha256':previous['derivative_report_sha256']}]
    for entry in entries:
        if digest(Path(entry['path']))!=entry['sha256'] or json.loads(Path(entry['path']).read_text()).get('passed') is not True:
            raise ValueError('Additional derivative report changed/failed')
    return dict(current,derivative_reports=entries+[{'path':current['derivative_report'],'sha256':current['derivative_report_sha256']}])


def validate(a):
    a.output.mkdir(parents=True,exist_ok=False)
    layer=a.layer;count=check_binary(a.mille,a.reco,(0.,0.),layer);checks=[]
    # Nonzero centers test rotation about the sensor center, rather than the world origin.
    for angle in (0.,.017,-.023):
        paths={}
        for epsilon in (1e-3,1e-4,1e-5,1e-6):
            probes=[]
            for sign in (-1,0,1):
                key=(angle,epsilon,sign)
                xml=a.output/f'angle_{angle}_eps_{epsilon}_sign_{sign}.xml'
                write_shifted_xml(a.geometry,xml,{layer:1.25},{layer:-.75},rz_rad={layer:angle-sign*epsilon})
                output=xml.with_suffix('.json')
                with xml.with_suffix('.log').open('x') as log:
                    subprocess.run([sys.executable,'-m','validation.geometry_probe','--geometry',str(xml),'--output',str(output)],cwd=REPO,
                                   env=geometry_environment(xml),stdout=log,stderr=subprocess.STDOUT,check=True)
                probes.append(json.loads(output.read_text()))
            minus,zero,plus=probes
            for p in probes:
                c=p['layers'][str(layer)]['center_mm']
                if max(abs(c[i]-v) for i,v in enumerate((1.25,-.75,50.*layer)))>1e-10:raise AssertionError('Pure rotation moved sensor center')
            for key,m in zero['samples'].items():
                if not key.startswith(f'L{layer}_'):continue
                analytic=(-(m[1]+.75),m[0]-1.25)
                for tx,ty,x0,y0 in [(-.03,.01,-5,8),(0.,0.,0.,0.),(.025,-.02,7,-4)]:
                    def residual(q):return (x0+tx*(q[2]-100)-q[0],y0+ty*(q[2]-100)-q[1])
                    rm,rp=residual(minus['samples'][key]),residual(plus['samples'][key])
                    numeric=[(rp[i]-rm[i])/(2*epsilon) for i in range(2)]
                    errors=[abs(numeric[i]-analytic[i]) for i in range(2)]
                    if max(errors)>3e-6:raise AssertionError('Physical DD4hep derivative disagrees with bias convention')
                    checks.append(dict(angle_rad=angle,epsilon_rad=epsilon,sample=key,slopes=[tx,ty],impact=[x0,y0],analytic=analytic,numeric=numeric,absolute_errors=errors,
                                       relative_errors=[errors[i]/abs(analytic[i]) if abs(analytic[i])>1e-8 else None for i in range(2)]))
    write_json(a.output/'report.json',dict(passed=True,actual_binary_entries=count,checks=checks,units='mm/rad',pivot_mm=[1.25,-.75,50.*layer],
        max_absolute_error=max(max(c['absolute_errors']) for c in checks),max_relative_error=max(v for c in checks for v in c['relative_errors'] if v is not None),
        convention='F=prediction+bias-measurement; physical correction=-bias',label=3000+layer))
    import os
    require(a.reco.parent.parent,'step3')
    metadata=json.loads((a.reco.parent/'complete.json').read_text())
    plugin=Path(os.environ.get('TESTBENCH_BUILD_DIR',REPO/'build/local_eicrecon_external'))/'BeamTestReco.so'
    if metadata['plugin_sha256']!=digest(plugin):raise ValueError('Derivative input belongs to a different build')
    if metadata['output_hashes'].get(a.mille.name)!=digest(a.mille) or metadata['output_hashes'].get(a.reco.name)!=digest(a.reco):raise ValueError('Derivative files do not match their reconstruction record')
    proof=a.output/'report.json'
    gate={'passed':True,'plugin_sha256':digest(plugin),'derivative_report':str(proof.resolve()),
        'derivative_report_sha256':digest(proof),'actual_mille_sha256':digest(a.mille),'actual_reco_sha256':digest(a.reco)}
    if a.additional_gate:gate=merge_gate(gate,json.loads(a.additional_gate.read_text()))
    write_json(a.output/'gate.json',gate)
    print('PASS',len(checks),'fresh physical Geometry derivative checks;',count,'actual Mille entries')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--additional-gate',type=Path,help='Merge already passed label checks from this same plugin into the output gate')
    parser.add_argument('--layer',type=int,choices=[1,2],default=1)
    for name in ('geometry','mille','reco','output'):parser.add_argument('--'+name,type=Path,required=True)
    validate(parser.parse_args())
