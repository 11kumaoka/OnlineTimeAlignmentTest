"""Validate production tilt Mille entries against fresh physical DD4hep rotations.

This diagnostic does not enable solver modes. The covariance factor and reference
trajectory are frozen for each derivative test, exactly as in one linear solve.
"""
import argparse,json,os,re,subprocess,sys,concurrent.futures
from pathlib import Path
import numpy as np
from geometry.prepare import write_shifted_xml,DEFAULT_NOMINAL
from geometry.transforms import axis_rotation,multiply
from research_common import REPO,digest,write_json
from validation.z_observability import measurements


def whitening(basis,tx,ty,sx=.01,sy=.01):
    u=-np.asarray(basis[2]);v=np.asarray(basis[0])
    h=np.array([[tx*u[2]-u[0],tx*v[2]-v[0]],[ty*u[2]-u[1],ty*v[2]-v[1]]])
    c=h@np.diag([sy**2,sx**2])@h.T
    return np.linalg.inv(np.linalg.cholesky(c)),c


def profile(points,contexts):
    p=np.zeros(4)
    for _ in range(16):
        aa=[];bb=[]
        for l,m in enumerate(points):
            w,_=whitening(contexts[str(l)]['sensor_basis_columns'],p[2],p[3])
            a=np.array([[1,0,m[2]-100,0],[0,1,0,m[2]-100]])
            aa.extend(w@a);bb.extend(w@m[:2])
        nxt=np.linalg.lstsq(np.array(aa),np.array(bb),rcond=None)[0]
        if np.max(np.abs(nxt-p))<1e-12:return nxt
        p=nxt
    raise ValueError('Independent reference fit did not converge')


def validate(a):
    layer=a.layer
    coupled=getattr(a,'coupled',False)
    specifications=[('x',5000+layer,1),('y',6000+layer,1)]
    if coupled:specifications += [('z',3000+layer,-1),('tx',1000+layer,-1),('ty',2000+layer,-1),('tz',4000+layer,1)]
    a.output.mkdir(parents=True,exist_ok=False);os.environ['TESTBENCH_BUILD_DIR']=str(a.build_dir.resolve())
    commands=[]
    def call(command,log):
        commands.append(list(map(str,command)))
        with log.open('x') as output:subprocess.run(list(map(str,command)),stdout=output,stderr=subprocess.STDOUT,check=True)
    binary=a.output/'writer_fixture'
    flags=(a.build_dir/'CMakeFiles/BeamTestReco.dir/flags.make').read_text()
    eigen=re.search(r'-isystem (\S*eigen[^\s]*)',flags)
    eigen_path=eigen[1] if eigen else '/opt/local/include/eigen3'
    call(['g++','-std=c++20','-O1','-I'+str(REPO/'localDetEICrecon/alignment/src'),'-I'+str(REPO/'external/install/include'),'-I'+eigen_path,
          REPO/'validation/tilt_writer_fixture.cc',REPO/'localDetEICrecon/alignment/src/BeamTestMilleWriter.cc',
          '-L'+str(REPO/'external/install/lib'),'-lMille2','-Wl,-rpath,'+str(REPO/'external/install/lib'),'-o',binary],a.output/'compile.log')
    rows=[];binary_checks=[];covariance_checks=[]
    cases=[('horizontal',np.eye(3)),('rx_positive',axis_rotation('x',.03)),('rx_negative',axis_rotation('x',-.03)),
           ('ry_positive',axis_rotation('y',.03)),('ry_negative',axis_rotation('y',-.03)),
           ('combined',multiply(axis_rotation('z',.017),multiply(axis_rotation('y',-.025),axis_rotation('x',.02))))]
    if getattr(a,'representative',False):cases=[cases[-1]]
    steps=(1e-4,) if getattr(a,'representative',False) else (1e-3,1e-4,1e-5)
    def query(directory,name,matrix,translation=(0.,0.,0.)):
        xml=directory/(name+'.xml');out=directory/(name+'.json')
        write_shifted_xml(DEFAULT_NOMINAL,xml,{layer:1.25+translation[0]},{layer:-.75+translation[1]},z_shifts={layer:2.+translation[2]},rotations={layer:matrix})
        call([sys.executable,'-m','validation.geometry_probe','--geometry',xml,'--output',out],directory/(name+'.log'))
        return json.loads(out.read_text())
    for name,matrix in cases:
        directory=a.output/name;directory.mkdir();base=query(directory,'base',matrix)
        contexts=base['layers'];samples=base['samples'];points=[]
        for key,m in samples.items():
            if not key.startswith(f'L{layer}_'):continue
            for tx,ty in ((-.02,.015),(0.,0.),(.025,-.018)):
                m=np.array(m);track=[]
                for l in range(5):
                    z=contexts[str(l)]['center_mm'][2]
                    track.append(m.copy() if l==layer else np.array([m[0]+tx*(z-m[2]),m[1]+ty*(z-m[2]),z]))
                points.append((key,track))
        text=[]
        for l in range(5):
            c=contexts[str(l)];basis=np.array(c['sensor_basis_columns'])
            text.extend(map(str,[*c['center_mm'],*(-basis[2]),*basis[0]]))
        text.append(str(len(points)))
        for _,track in points:
            for m in track:text.extend(map(str,[*m,.01,.01]))
        inp=directory/'fixture.txt';inp.write_text(' '.join(text)+'\n')
        call([binary,inp,directory/'mille.dat',str(layer)]+(['six_dof'] if coupled else []),directory/'writer.log')
        blocks=list(measurements(directory/'mille.dat'))
        refs=re.findall(r'BeamTestTiltReference record=(\d+) tx=(\S+) ty=(\S+)',(directory/'writer.log').read_text())
        if len(blocks)!=len(points) or len(refs)!=len(points):raise AssertionError('Fixture record count mismatch')
        for record,(key,track) in enumerate(points):
            p=profile(track,contexts);logged=np.array(list(map(float,refs[record][1:])))
            if not np.allclose(logged,p[2:],rtol=0,atol=1e-12):raise AssertionError('Independent reference trajectory mismatch')
            m=track[layer];center=np.array(contexts[str(layer)]['center_mm']);w,c=whitening(contexts[str(layer)]['sensor_basis_columns'],*p[2:])
            if not np.allclose(w@c@w.T,np.eye(2),rtol=0,atol=1e-12):raise AssertionError('Residual whitening mismatch')
            covariance_checks.append({'case':name,'record':record,'covariance':c.tolist(),'whitening':w.tolist()})
            for axis,label,sign in specifications:
                dm=np.eye(3)['xyz'.index(axis[-1])] if axis.startswith('t') else np.cross(np.eye(3)['xyz'.index(axis)],m-center)
                d=np.array([p[2]*dm[2]-dm[0],p[3]*dm[2]-dm[1]])
                expected=sign*w@d;actual=np.array([blocks[record][2*layer][3].get(label,0.),blocks[record][2*layer+1][3].get(label,0.)])
                if not np.allclose(actual,expected,rtol=1e-6,atol=2e-6):raise AssertionError('Actual Mille tilt derivative mismatch')
                binary_checks.append({'case':name,'record':record,'label':label,'max_abs_error':float(np.max(np.abs(actual-expected)))})
        for axis,label,sign in specifications:
            for eps in steps:
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    if axis.startswith('t'):
                        direction=np.eye(3)['xyz'.index(axis[-1])]*eps
                        positive=pool.submit(query,directory,f'{axis}_{eps}_plus',matrix,direction)
                        negative=pool.submit(query,directory,f'{axis}_{eps}_minus',matrix,-direction)
                    else:
                        positive=pool.submit(query,directory,f'{axis}_{eps}_plus',multiply(axis_rotation(axis,eps),matrix))
                        negative=pool.submit(query,directory,f'{axis}_{eps}_minus',multiply(axis_rotation(axis,-eps),matrix))
                    plus,minus=positive.result(),negative.result()
                for record,(key,track) in enumerate(points):
                    p=profile(track,contexts);m=track[layer];center=np.array(contexts[str(layer)]['center_mm'])
                    dm=np.eye(3)['xyz'.index(axis[-1])] if axis.startswith('t') else np.cross(np.eye(3)['xyz'.index(axis)],m-center)
                    analytic=np.array([p[2]*dm[2]-dm[0],p[3]*dm[2]-dm[1]])
                    def residual(point):
                        x,y,z=point
                        return np.array([p[0]+p[2]*(z-100)-x,p[1]+p[3]*(z-100)-y])
                    fd=(residual(plus['samples'][key])-residual(minus['samples'][key]))/(2*eps)
                    w,_=whitening(contexts[str(layer)]['sensor_basis_columns'],*p[2:]);actual=np.array([blocks[record][2*layer][3].get(label,0.),blocks[record][2*layer+1][3].get(label,0.)])
                    if not np.allclose(fd,analytic,rtol=5e-6,atol=2e-8):raise AssertionError('Physical DD4hep finite difference mismatch')
                    if not np.allclose(sign*w@fd,actual,rtol=6e-6,atol=3e-6):raise AssertionError('Actual binary/physical derivative mismatch')
                    rows.append({'case':name,'label':label,'record':record,'epsilon':eps,'parameter_unit':'mm' if axis.startswith('t') else 'rad','analytic_xy_mm_per_parameter':analytic.tolist(),'fd_xy_mm_per_parameter':fd.tolist(),
                        'max_abs_error':float(np.max(np.abs(fd-analytic))), 'max_relative_error':float(np.max(np.abs(fd-analytic)/np.maximum(np.abs(analytic),1e-6)))})
    report={'passed':True,'linearization':'so3_profiled_covariance_v1' if coupled else 'tilt_profiled_covariance_v1','labels':[label for _,label,_ in specifications],
        'plugin_sha256':digest(a.build_dir/'BeamTestReco.so'),'geometry_plugin_sha256':digest(a.build_dir/'libLocalTelescopeGeometry.so'),
        'actual_binary_entries':len(binary_checks)*2,'fresh_physical_contexts':len(cases)*(1+2*len(steps)*len(specifications)),
        'physical_checks':rows,'binary_checks':binary_checks,'covariance_checks':covariance_checks,
        'max_abs_physical_error':max(r['max_abs_error'] for r in rows),'max_relative_physical_error':max(r['max_relative_error'] for r in rows),
        'max_abs_binary_error':max(r['max_abs_error'] for r in binary_checks),
        'scope':'Production-writer fixture and fresh fixed-channel physical contexts; not a Simulation closure or solver authorization'}
    write_json(a.output/'report.json',report);write_json(a.output/'commands.json',commands)
    print('PASS',len(rows),'physical comparisons;',report['actual_binary_entries'],'actual binary components')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coupled',action='store_true',help='Validate all six Global differential columns in the whitened writer; does not enable an inference mode')
    parser.add_argument('--representative',action='store_true',help='Limited combined-orientation implementation check at epsilon 1e-4; full suite remains the default')
    parser.add_argument('--layer',type=int,choices=[1,2,3],default=1)
    parser.add_argument('--build-dir',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    validate(parser.parse_args())
