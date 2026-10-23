#!/usr/bin/env python3
"""Exercise real CLI refusal paths without executing physics or touching baseline data."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
scripts=repo
(repo/'result').mkdir(exist_ok=True)
base=Path(tempfile.mkdtemp(prefix='safety_',dir=repo/'result'))
def rejected(*args,contains):
 entry={'all':'validation/run_closure','align':'alignment/align','prepare':'geometry/prepare_geometry','correct':'correction/correct_geometry'}[args[0]]
 p=subprocess.run(['bash',str(scripts/(entry+'.sh')),*map(str,args[1:])],cwd=repo,text=True,capture_output=True)
 assert p.returncode==1 and contains in p.stderr, (p.returncode,p.stdout,p.stderr)
 print('PASS refusal:',contains)
existing=base/'existing';existing.mkdir();(existing/'sentinel').write_text('preserve')
rejected('all','--result-dir',existing,contains='new run directory')
assert (existing/'sentinel').read_text()=='preserve'
rejected('all','--run-dir',existing,contains='new run directory')
assert (existing/'sentinel').read_text()=='preserve'
rejected('align','--result-dir',base/'missing',contains='Complete step3 first')
assert not (base/'missing').exists()
modified=base/'modified';(modified/'step4').mkdir(parents=True)
(modified/'step4/result.res').write_text('modified')
(modified/'step4/complete.json').write_text(json.dumps({'output_hashes':{'result.res':hashlib.sha256(b'original').hexdigest()}}))
rejected('correct','--result-dir',modified,contains='Modified stage output')
assert not (modified/'step5').exists()
print('Safety artifacts retained:',base)

# Result paths cannot escape the maintained output tree.
outside=repo/'unsafe_output_test'
p=subprocess.run(['bash',str(scripts/'geometry/prepare_geometry.sh'),'--result-dir',str(outside)],cwd=repo,text=True,capture_output=True)
assert p.returncode==2 and 'result directory must be a child of result/' in p.stderr
assert not outside.exists()
print('PASS refusal: result directory must be a child of result/')

# Invalid scenario definitions fail before creating a Geometry stage or launching tools.
invalid_scenarios = [
    ({'detector':'SiMAPS','global_x_shifts_mm':{'5':0.1}}, 'Unsupported SiMAPS layer identifier'),
    ({'detector':'SiMAPS','global_x_shifts_mm':{},'global_z_shifts_mm':{'4':0.1}}, 'Global Z supports finite L1/L2'),
    ({'detector':'SiMAPS','global_x_shifts_mm':{},'global_rx_rad':{'4':0.1}}, 'Physical tilt preparation supports'),
    ({'detector':'SiMAPS','global_x_shifts_mm':{},'global_ry_rad':{'4':0.1}}, 'Physical tilt preparation supports'),
    ({'detector':'MPGD','global_x_shifts_mm':{'2':0.1}}, 'Only a SiMAPS'),
    ({'detector':'SiMAPS','global_x_shifts_mm':{'2':True}}, 'finite number'),
    ({'detector':'SiMAPS','global_x_shifts_mm':{'2':float('nan')}}, 'finite number'),
]
for index, (scenario, message) in enumerate(invalid_scenarios):
    path = base/f'invalid_geometry_{index}.json';path.write_text(json.dumps(scenario))
    output = base/f'invalid_geometry_{index}'
    rejected('prepare','--result-dir',output,'--geometry-config',path,contains=message)
    assert not output.exists()

# These are synthetic markers, not a two-layer Simulation or alignment run.
multi=base/'multi_layer';(multi/'step1').mkdir(parents=True)
scenario=(repo/'geometry/scenarios/L1_x100um_L2_x200um.json').read_bytes()
(multi/'step1/geometry_config.json').write_bytes(scenario)
(multi/'step1/complete.json').write_text(json.dumps({'output_hashes':{'geometry_config.json':hashlib.sha256(scenario).hexdigest()}}))
rejected('correct','--result-dir',multi,'--check-only',contains='Multi-layer Geometry Correction and full Closure are unsupported')
assert not (multi/'step5').exists()
(multi/'step4').mkdir();(multi/'step4/complete.json').write_text(json.dumps({'output_hashes':{}}))
rejected('correct','--result-dir',multi,contains='Multi-layer Geometry Correction and full Closure are unsupported')
assert not (multi/'step5').exists()

# The convenience runner must not bypass the Controller Z derivative/information gates.
z_output=base/'ungated_z'
p=subprocess.run(['bash',str(scripts/'validation/run_closure.sh'),'--result-dir',str(z_output),'--correction-mode','l1_z'],cwd=repo,text=True,capture_output=True)
assert p.returncode==2 and 'requires derivative and observability gates' in p.stderr
assert not z_output.exists()
print('PASS refusal: ungated convenience-runner Z calibration')

# Tilt calibration must not bypass the derivative/information gates either.
tilt_output=base/'ungated_rx'
p=subprocess.run(['bash',str(scripts/'validation/run_closure.sh'),'--result-dir',str(tilt_output),'--correction-mode','l1_rx'],cwd=repo,text=True,capture_output=True)
assert p.returncode==2 and 'requires derivative and observability gates' in p.stderr
assert not tilt_output.exists()
print('PASS refusal: ungated convenience-runner Rx calibration')

# New three-layer and L3-only convenience paths cannot bypass evidence gates.
for mode in ('l3_six_dof','l1_l2_l3_six_dof'):
    output=base/('ungated_'+mode)
    p=subprocess.run(['bash',str(scripts/'validation/run_closure.sh'),'--result-dir',str(output),'--correction-mode',mode],cwd=repo,text=True,capture_output=True)
    assert p.returncode==2 and 'requires derivative and observability gates' in p.stderr
    assert not output.exists()
    print('PASS refusal: ungated '+mode)
