"""Validate physical Global Z derivatives in fresh DD4hep contexts and Mille bytes."""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
import numpy as np
import awkward as ak
import uproot
from geometry.prepare import write_shifted_xml
from geometry.environment import geometry_environment
from research_common import REPO,write_json,digest,require
from validation.z_observability import measurements


def validate(a):
    a.output.mkdir(parents=True,exist_ok=False);layer=a.layer;label=4000+layer
    require(a.reco.parent.parent,'step3');meta=json.loads((a.reco.parent/'complete.json').read_text())
    build=Path(os.environ['TESTBENCH_BUILD_DIR']);plugin=build/'BeamTestReco.so';factory=build/'libLocalTelescopeGeometry.so'
    if digest(plugin)!=meta['plugin_sha256']:raise ValueError('Mismatched derivative build')
    if digest(a.mille)!=meta['output_hashes'][a.mille.name]:raise ValueError('Mille input changed')
    blocks=list(measurements(a.mille));log=(a.reco.parent/'stdout.log').read_text()
    refs=[(int(i),float(x),float(y)) for i,x,y in re.findall(r'BeamTestZReference record=(\d+) tx=(\S+) ty=(\S+)',log)]
    assert len(refs)==len(blocks) and [v[0] for v in refs]==list(range(len(blocks)))
    with uproot.open(a.reco) as root:
        tree=root['events'];get=lambda key:ak.to_list(tree['LocalSiMAPSRecHits/LocalSiMAPSRecHits.'+key].array())
        ids=get('cellID');xs=get('position.x');ys=get('position.y');zs=get('position.z');ex=get('positionError.xx');ey=get('positionError.yy')
        accepted=ak.to_list(tree['LocalBeamTestTracks/LocalBeamTestTracks.ndf'].array())
    expected=[]
    for event,tr in enumerate(accepted):
        if not tr:continue
        order=sorted(range(len(ids[event])),key=lambda i:ids[event][i]>>11&63)
        assert [ids[event][i]>>11&63 for i in order]==list(range(5))
        z=np.array([zs[event][i]-100 for i in order]);slopes=[]
        for positions,errors in [(xs,ex),(ys,ey)]:
            m=np.array([positions[event][i] for i in order]);w=1/np.maximum(.005**2,np.array([errors[event][i] for i in order]))
            zbar=np.sum(w*z)/sum(w);mbar=np.sum(w*m)/sum(w)
            slopes.append(float(sum(w*(z-zbar)*(m-mbar))/sum(w*(z-zbar)**2)))
        expected.append(slopes)
    assert np.allclose(expected,[r[1:] for r in refs],rtol=0,atol=1e-12)
    for rows,(_,tx,ty) in zip(blocks,refs):
        for row,slope in [(rows[2*layer],tx),(rows[2*layer+1],ty)]:assert row[3].get(label,0.)==float(np.float32(slope))
    checks=[];zero_checks=[]
    for offset in (-2.,2.):
        for angle in (0.,.017):
            for epsilon in (.01,.001,.0001):
                probes=[]
                for sign in (-1,1):
                    stem=f'z{offset}_rz{angle}_eps{epsilon}_sign{sign}';xml=a.output/(stem+'.xml');out=a.output/(stem+'.json')
                    write_shifted_xml(a.geometry,xml,{layer:1.25},{layer:-.75},rz_rad={layer:angle},z_shifts={layer:offset+sign*epsilon})
                    with (a.output/(stem+'.log')).open('x') as log:
                        subprocess.run([sys.executable,'-m','validation.geometry_probe','--geometry',str(xml),'--output',str(out)],env=geometry_environment(xml),cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
                    probes.append(json.loads(out.read_text()))
                minus,plus=probes
                for l in range(7):
                    m,p=[v['layers'][str(l)] for v in probes]
                    assert np.allclose(m['sensor_basis_columns'],p['sensor_basis_columns'],rtol=0,atol=1e-12)
                    expected_move=[0,0,2*epsilon if l==layer else 0]
                    assert np.allclose(np.array(p['center_mm'])-m['center_mm'],expected_move,rtol=0,atol=1e-10)
                for key,qm in minus['samples'].items():
                    if not key.startswith(f'L{layer}_'):continue
                    qp=plus['samples'][key]
                    for tx,ty in [(0,0),(.03,.02),(-.03,-.02),(.03,-.02),(-.03,.02),(.02,0),(0,-.02)]:
                        for x0,y0 in [(0,0),(-5,8),(7,-4)]:
                            fm=np.array([x0+tx*(qm[2]-100)-qm[0],y0+ty*(qm[2]-100)-qm[1]])
                            fp=np.array([x0+tx*(qp[2]-100)-qp[0],y0+ty*(qp[2]-100)-qp[1]])
                            numeric=(fp-fm)/(2*epsilon);analytic=np.array([tx,ty]);error=np.abs(numeric-analytic)
                            assert max(error)<1e-9
                            row={'z_offset_mm':offset,'rz_rad':angle,'epsilon_mm':epsilon,'sample':key,'reference_slopes':[tx,ty],'intercept_mm':[x0,y0],'numeric':numeric.tolist(),'analytic':analytic.tolist(),'absolute_errors':error.tolist(),'relative_errors':[float(e/abs(v)) if v else None for e,v in zip(error,analytic)]}
                            checks.append(row)
                            if tx==ty==0:zero_checks.append(row)
    report={'passed':True,'label':label,'units':'mm/mm','linearization':'profiled_local_slopes_v1','actual_binary_entries':2*len(blocks),
        'plugin_sha256':digest(plugin),'geometry_plugin_sha256':digest(factory),'actual_mille_sha256':digest(a.mille),'actual_reco_sha256':digest(a.reco),
        'checks':checks,'zero_slope_checks':len(zero_checks),'max_absolute_error':max(max(c['absolute_errors']) for c in checks),
        'max_relative_error':max(v for c in checks for v in c['relative_errors'] if v is not None),
        'convention':'F=prediction(z+delta_z)-measurement; physical correction=+fitted 4000+layer'}
    write_json(a.output/'report.json',report)
    proofs=[]
    if a.additional_gate:
        old=json.loads(a.additional_gate.read_text());assert old['plugin_sha256']==digest(plugin) and old['geometry_plugin_sha256']==digest(factory)
        proofs=old['derivative_reports']
        for proof in proofs:assert digest(Path(proof['path']))==proof['sha256']
    proofs.append({'path':str((a.output/'report.json').resolve()),'sha256':digest(a.output/'report.json')})
    write_json(a.output/'gate.json',{'passed':True,'plugin_sha256':digest(plugin),'geometry_plugin_sha256':digest(factory),'linearization':'profiled_local_slopes_v1','derivative_reports':proofs})
    print('PASS',len(checks),'fresh-context derivatives;',2*len(blocks),'actual Mille entries')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('geometry','mille','reco','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--layer',type=int,choices=[1,2],default=1);p.add_argument('--additional-gate',type=Path)
    validate(p.parse_args())
