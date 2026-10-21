"""Independent stage; invoke with python3 -m alignment.align."""
import os
import re
from pathlib import Path
from research_common import REPO, cli_parser, run, require, stage, done, prefix, execute

def read_pede(path):
    out={}
    for line in path.read_text().splitlines():
        fields=line.split()
        if len(fields)>1:
            try:out[int(fields[0])]=float(fields[1])
            except ValueError:pass
    return out

def align(a):
    require(a.run_dir,'step3');p=stage(a.run_dir,'step4')
    template=a.steering.read_text()
    (p/'steering_template.txt').write_text(template)
    (p/'pede.txt').write_text(template.replace('@MILLE_FILE@',str(a.run_dir/'step3/mille.dat')))
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(prefix()/'lib')+':'+env.get('LD_LIBRARY_PATH','')
    execute([prefix()/'bin/pede','pede.txt'],p,cwd=p,env=env)
    params=read_pede(p/'millepede.res')
    if 1002 not in params:raise RuntimeError('Missing L2 solution')
    end=(p/'millepede.end').read_text().strip()
    if not re.match(r'^[01]\b',end):raise RuntimeError(f'pede status: {end}')
    done(p,parameters_mm=params,status=end)


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--steering', type=Path, default=REPO/'alignment/pede_template.txt', help='Pede template with @MILLE_FILE@ placeholder')
    run(align, parser)
