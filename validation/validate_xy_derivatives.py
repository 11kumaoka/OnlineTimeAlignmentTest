"""Compare actual Mille derivatives with fresh-DD4hep geometry finite differences."""
import argparse,json,os,struct,subprocess,sys
from pathlib import Path
from geometry.prepare import write_shifted_xml
from geometry.placements import placement_transforms
from geometry.environment import geometry_environment
from research_common import REPO,write_json


def binary_derivatives(path):
    found={label:[] for label in (1001,2001,1002,2002)}
    with path.open('rb') as stream:
        while header:=stream.read(4):
            words=struct.unpack('<i',header)[0]
            if words<=0 or words%2:raise ValueError('Derivative probe supports the validated single-precision Mille record format only')
            count=words//2
            values=struct.unpack('<'+'f'*count,stream.read(count*4))
            labels=struct.unpack('<'+'i'*count,stream.read(4*count))
            for label,value in zip(labels,values):
                if label in found:found[label].append(value)
    if not all(found.values()):raise ValueError('Missing supported derivative labels in actual Mille Binary')
    for values in found.values():
        if any(value!=1 for value in values):raise ValueError('Unexpected analytic Mille derivative')
    return found


def validate(args):
    args.output.mkdir(parents=True,exist_ok=False)
    positions=placement_transforms(args.geometry);epsilon=.001;checks=[]
    derivatives=binary_derivatives(args.mille)
    for layer in (1,2):
        for axis,index,label in [('x',0,1000+layer),('y',1,2000+layer)]:
            probes=[]
            for sign in (-1,1):
                # a is measurement bias; its physical Geometry correction is -a.
                shifts={lid:positions[lid].translation[0] for lid in (1,2)}
                y_shifts={lid:positions[lid].translation[1] for lid in (1,2)}
                (shifts if axis=='x' else y_shifts)[layer]-=sign*epsilon
                geometry=args.output/f'L{layer}_{axis}_{sign}.xml'
                write_shifted_xml(args.geometry,geometry,shifts,y_shifts)
                output=geometry.with_suffix('.json')
                with geometry.with_suffix('.log').open('x') as log:
                    subprocess.run([sys.executable,'-m','validation.geometry_probe','--geometry',str(geometry),'--output',str(output)],
                        cwd=REPO,env=geometry_environment(geometry),stdout=log,stderr=subprocess.STDOUT,check=True)
                probes.append(json.loads(output.read_text()))
            minus,plus=probes
            for key,p in minus['samples'].items():
                if not key.startswith(f'L{layer}_'):continue
                for tx,ty,x0,y0 in [(-.03,.01,-5,8),(0.,0.,0.,0.),(.025,-.02,7,-4)]:
                    def residual(point):return (x0+tx*(point[2]-100)-point[0],y0+ty*(point[2]-100)-point[1])
                    rminus=residual(p);rplus=residual(plus['samples'][key])
                    numeric=(rplus[index]-rminus[index])/(2*epsilon)
                    cross=(rplus[1-index]-rminus[1-index])/(2*epsilon)
                    if abs(numeric-derivatives[label][0])>1e-8 or abs(cross)>1e-8:raise AssertionError('Finite-difference derivative mismatch')
                    checks.append({'label':label,'sample':key,'tx':tx,'ty':ty,'analytic':derivatives[label][0],'numeric':numeric,'cross':cross})
    write_json(args.output/'report.json',{'passed':True,'epsilon_mm':epsilon,'tolerance':1e-8,'units':'dimensionless dr/da; residual mm, a mm',
        'residual':'track prediction + bias - global RecHit coordinate; physical correction = -bias',
        'actual_binary_entries_by_label':{str(k):len(v) for k,v in derivatives.items()},'checks':checks})
    print('PASS:',len(checks),'fresh-Geometry derivative checks against actual Mille Binary')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('geometry','mille','output'):parser.add_argument('--'+name,type=Path,required=True)
    validate(parser.parse_args())
