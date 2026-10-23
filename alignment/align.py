"""Independent stage; invoke with python3 -m alignment.align."""
import os
import math
import re
from pathlib import Path
from correction.scope import SO3_MODES,parameter_spec
from research_common import REPO, cli_parser, run, require, stage, done, prefix, execute, digest

def read_pede(path):
    out={}
    for line in path.read_text().splitlines():
        fields=line.split()
        if len(fields)>1:
            try:out[int(fields[0])]=float(fields[1])
            except ValueError:pass
    return out

def align(a):
    if any(digest(a.steering)==digest(REPO/f'alignment/pede_{mode}.txt') for mode in ('l1_rx_ry','l1_l2_rx_ry')):
        raise ValueError('Combined Rx/Ry disabled after failed finite-rotation closure; see docs/TILT_ALIGNMENT_VALIDATION.md')
    require(a.run_dir,'step3');p=stage(a.run_dir,'step4')
    template=a.steering.read_text()
    (p/'steering_template.txt').write_text(template)
    (p/'pede.txt').write_text(template.replace('@MILLE_FILE@',str(a.run_dir/'step3/mille.dat')))
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(prefix()/'lib')+':'+env.get('LD_LIBRARY_PATH','')
    execute([prefix()/'bin/pede','pede.txt'],p,cwd=p,env=env)
    end=(p/'millepede.end').read_text().strip()
    if not re.match(r'^[01]\b',end):raise RuntimeError(f'pede status: {end}')
    params=read_pede(p/'millepede.res')
    if 1002 not in params:raise RuntimeError('Missing L2 solution')
    rotations={int(label) for label in re.findall(r'^\s*(3[0-9]{3})\s+\S+\s+(?!-)\S+',template,re.M)}
    if any(3000<=label<4000 for label in params) and not rotations:raise RuntimeError('Rotation derivatives require explicit mode-specific steering')
    if 3003 in rotations and not any(digest(a.steering)==digest(REPO/f'alignment/pede_{mode}.txt') for mode in ('l3_six_dof','l1_l2_l3_six_dof')):
        raise RuntimeError('L3 rotation requires canonical six-DOF steering')
    if rotations:
        if not rotations<={3001,3002,3003} or not rotations<=params.keys():raise RuntimeError('Unsupported/missing rotation solution')
        log=(p/'millepede.log').read_text()
        if 'No rank defect of the symmetric matrix' not in log:raise RuntimeError('Unobservable rotation solution: rank defect or missing rank diagnostic')
        errors={}
        for line in (p/'millepede.res').read_text().splitlines():
            fields=line.split()
            if fields and fields[0].isdigit() and int(fields[0]) in rotations:
                if len(fields)<5:raise RuntimeError('Unobservable rotation solution: missing uncertainty')
                error=float(fields[4])
                if not math.isfinite(error) or error<=0:raise RuntimeError('Unobservable rotation solution: invalid uncertainty')
                errors[int(fields[0])]=error
        if set(errors)!=rotations:raise RuntimeError('Unobservable rotation solution: missing uncertainty')
    if any(5000<=label<7000 for label in params):
        modes=(*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry')
        matched=[mode for mode in modes if digest(a.steering)==digest(REPO/f'alignment/pede_{mode}.txt')]
        if len(matched)!=1:raise RuntimeError('Tilt alignment requires canonical constrained mode-specific steering')
        from correction.scope import layers_for,axes_for
        free={family+l for l in layers_for(matched[0]) for _,family,_ in parameter_spec(matched[0])}
        if not free<=params.keys() or any(v!=0 and k not in free for k,v in params.items()):raise RuntimeError('Unsupported tilt parameter scope')
        if 'No rank defect of the symmetric matrix' not in (p/'millepede.log').read_text():raise RuntimeError('Unobservable tilt solution')
        errors={}
        for line in (p/'millepede.res').read_text().splitlines():
            fields=line.split()
            if fields and fields[0].isdigit() and int(fields[0]) in free:
                if len(fields)<5 or not math.isfinite(float(fields[4])) or float(fields[4])<=0:raise RuntimeError('Invalid tilt nominal error')
                errors[int(fields[0])]=float(fields[4])
        if set(errors)!=free:raise RuntimeError('Missing tilt nominal error')
        info=dict(tilt_sigma_rad=errors,parameters_by_label=params,parameter_units={str(k):('rad' if 3000<=k<4000 or k>=5000 else 'mm') for k in params},status=end)
        if matched[0] in SO3_MODES:
            info['nominal_sigma_by_label']=errors
            info['tilt_sigma_rad']={k:v for k,v in errors.items() if 3000<=k<4000 or k>=5000}
        done(p,**info)
    elif any(4000<=label<5000 for label in params):
        if not any(digest(a.steering)==digest(REPO/f'alignment/pede_{mode}.txt') for mode in ('l1_z','l1_l2_z','l1_l2_xyz')):
            raise RuntimeError('Z requires canonical constrained mode-specific steering')
        if 'No rank defect of the symmetric matrix' not in (p/'millepede.log').read_text():raise RuntimeError('Unobservable Z matrix')
        errors={}
        free={int(m[0]) for m in re.findall(r'^\s*(\d+)\s+\S+\s+([0-9.]+)\s*$',template,re.M)}
        for line in (p/'millepede.res').read_text().splitlines():
            fields=line.split()
            if fields and fields[0].isdigit() and int(fields[0]) in free:
                if len(fields)<5:raise RuntimeError('Missing Z-mode uncertainty')
                value=float(fields[4])
                if not math.isfinite(value) or value<=0:raise RuntimeError('Invalid Z-mode uncertainty')
                errors[int(fields[0])]=value
        if set(errors)!=free:raise RuntimeError('Missing selected Z-mode fit')
        done(p,z_sigma_mm={k:v for k,v in errors.items() if k>=4000},nominal_sigma_by_label=errors,
             parameters_by_label=params,parameter_units={str(k):'mm' for k in params},status=end)
    elif any(3000<=label<4000 for label in params):
        done(p,rotation_sigma_rad=errors,parameters_by_label=params,parameter_units={str(label):('rad' if 3000<=label<4000 else 'mm') for label in params},status=end)
    else:
        done(p,parameters_mm=params,status=end)


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--steering', type=Path, default=REPO/'alignment/pede_template.txt', help='Pede template with @MILLE_FILE@ placeholder')
    run(align, parser)
