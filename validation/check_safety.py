#!/usr/bin/env python3
"""Exercise real CLI refusal paths without executing physics or touching baseline data."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
runner=repo/'local_detector_testbench/scripts/workflow.py'
(repo/'results').mkdir(exist_ok=True)
base=Path(tempfile.mkdtemp(prefix='safety_',dir=repo/'results'))
def rejected(*args,contains):
 p=subprocess.run([sys.executable,str(runner),*map(str,args)],cwd=repo,text=True,capture_output=True)
 assert p.returncode==1 and contains in p.stderr, (p.returncode,p.stdout,p.stderr)
 print('PASS refusal:',contains)
existing=base/'existing';existing.mkdir();(existing/'sentinel').write_text('preserve')
rejected('all','--result-dir',existing,contains='new run directory')
assert (existing/'sentinel').read_text()=='preserve'
rejected('all','--run-dir',existing,contains='new run directory')
assert (existing/'sentinel').read_text()=='preserve'
rejected('align','--result-dir',base/'missing',contains='Complete before first')
assert not (base/'missing').exists()
cfg=json.loads((repo/'examples/seven_layer_telescope/cases/electron_1GeV_L2_x200um.json').read_text())
cfg['alignment_layer']=1;unsupported=base/'unsupported.json';unsupported.write_text(json.dumps(cfg))
rejected('prepare','--result-dir',base/'unsupported','--case',unsupported,contains='supports SiMAPS L2 X only')
assert not (base/'unsupported').exists()
modified=base/'modified';(modified/'alignment').mkdir(parents=True)
(modified/'alignment/result.res').write_text('modified')
(modified/'alignment/complete.json').write_text(json.dumps({'output_hashes':{'result.res':hashlib.sha256(b'original').hexdigest()}}))
rejected('correct','--result-dir',modified,contains='Modified stage output')
assert not (modified/'correction').exists()
print('Safety artifacts retained:',base)

# Result paths cannot escape the maintained output tree.
outside=repo/'unsafe_output_test'
p=subprocess.run([sys.executable,str(runner),'all','--result-dir',str(outside)],cwd=repo,text=True,capture_output=True)
assert p.returncode==2 and 'result directory must be a child of results/' in p.stderr
assert not outside.exists()
print('PASS refusal: result directory must be a child of results/')
