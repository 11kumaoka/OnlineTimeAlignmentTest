#!/usr/bin/env python3
"""Run the seven-layer Alignment Closure Test in isolated stages without overwriting outputs.
Execute inside the EIC container using environment/run.sh. No shell eval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CASE = REPO / 'examples/seven_layer_telescope/cases/electron_1GeV_L2_x200um.json'

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def write_json(path, value):
    with Path(path).open('x') as f: json.dump(value, f, indent=2); f.write('\n')

def prefix():
    selected = Path(os.environ.get('MILLEPEDE_PREFIX', str(REPO/'external/install'))).resolve()
    for resource in ('cmake/MilleConfig.cmake','lib/libMille2.so','bin/pede'):
        if not (selected/resource).is_file():
            raise FileNotFoundError(f'Incomplete dependency installation: {selected/resource}; no legacy fallback is used')
    return selected

def execute(command, directory, cwd=None, env=None):
    cwd = directory if cwd is None else cwd
    write_json(directory/'command.json', {'argv':list(map(str,command)), 'cwd':str(cwd)})
    with (directory/'stdout.log').open('x') as f:
        rc = subprocess.call(list(map(str,command)), cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT)
    write_json(directory/'exit.json', {'exit_code':rc})
    if rc: raise RuntimeError(f'Command exited {rc}; see {directory}/stdout.log')

def stage(run, name):
    p = run/name
    p.mkdir()  # Exclusive: never reuse partial or completed output directories.
    return p

def done(p, **info):
    info['output_hashes']={q.name:digest(q) for q in p.iterdir() if q.is_file() and (q.suffix in {'.root','.xml','.dat','.res'} or q.name=='case.json')}
    write_json(p/'complete.json', info)

def snapshot(run):
    require(run,'geometry')
    return json.loads((run/'geometry/case.json').read_text())

def require(run, name):
    marker=run/name/'complete.json'
    if not marker.is_file(): raise RuntimeError(f'Complete {name} first')
    for filename,expected in json.loads(marker.read_text()).get('output_hashes',{}).items():
        if digest(run/name/filename)!=expected:raise RuntimeError(f'Modified stage output: {name}/{filename}')

def ring(root, lid):
    det = root.find("./detectors/detector[@name='SiMAPS']")
    if det is None or det.get('type') != 'DD4hep_SiTrackerEndcap2': raise ValueError('Unsupported detector builder')
    matches = det.findall(f"./layer[@id='{lid}']/ring")
    if len(matches)!=1 or matches[0].get('nmodules')!='1' or float(matches[0].get('phi0','0'))!=0:
        raise ValueError('Only a single phi0=0 SiMAPS module is supported')
    return matches[0]

def modified_xml(source, dest, layer, x_mm):
    # Preserve the nominal Detector Geometry; edit only the requested layer placement.
    text = Path(source).read_text()
    parsed = ET.fromstring(text); ring(parsed, layer)
    det = re.search(r'<detector\b[^>]*name="SiMAPS"[\s\S]*?</detector>', text)
    if not det: raise ValueError('SiMAPS XML block not found')
    block = det.group(); pattern = rf'(<layer\s+id="{layer}"[^>]*>[\s\S]*?<ring\b[^>]*\br=")[^"]*(")'
    block, count = re.subn(pattern, lambda m:m[1]+f'{-x_mm:.8f}*mm'+m[2], block)
    if count != 1: raise ValueError('Expected exactly one placement edit')
    with Path(dest).open('x') as f: f.write(text[:det.start()]+block+text[det.end():])
    ET.parse(dest)

def prepare(a):
    cfg = json.loads(a.case.read_text())
    if cfg['backend']!='seven_layer_telescope' or cfg['alignment_layer']!=2:
        raise ValueError('Current correction/closure backend supports SiMAPS L2 X only')
    if cfg['events']<=0: raise ValueError('events must be positive')
    nominal = REPO/cfg['nominal']
    root=ET.parse(nominal).getroot(); r=ring(root,2)
    if r.get('r')!='plane_ring_r' or root.find("./define/constant[@name='plane_ring_r']").get('value')!='0*mm':
        raise ValueError('This backend requires the existing zero-centered nominal telescope')
    a.run_dir.mkdir(parents=True, exist_ok=True)
    p=stage(a.run_dir,'geometry')
    shutil.copyfile(nominal,p/'nominal.xml')
    write_json(p/'case.json',cfg)
    modified_xml(nominal,p/'misaligned.xml',2,cfg['injected_x_mm'])
    for name in ('nominal','misaligned'):
        qa=p/(name+'_qa');qa.mkdir()
        execute(['geoConverter','-compact2gdml','-input',p/(name+'.xml'),'-output',qa/'geometry.gdml'],qa)
    version={}
    for key in ['Acts','DD4hep','EICrecon','JANA']:
        path=Path('/opt/local/include')/key
        if path.exists(): version[key]=str(path.resolve())
    done(p, nominal_sha256=digest(nominal), source=str(nominal), installed_paths=version,
         git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
         git_status=subprocess.check_output(['git','status','--short'],cwd=REPO,text=True),
         dirty_plugin_sources={str(q.relative_to(REPO)):digest(q) for q in (REPO/'local_detector_testbench').rglob('*') if q.is_file() and q.suffix in {'.h','.cc','.txt','.py'}},
         image=os.environ.get('TESTBENCH_IMAGE','record image ID on host: docker image inspect'))

def check_simulation(out,events):
    import uproot
    with uproot.open(out) as f:
        tree=f['events']
        for name in ('SiMAPSHits','MPGDHits','ACLGADHits'):
            if name not in tree:raise RuntimeError(f'Missing simulation collection {name}')
        if tree.num_entries<events:raise RuntimeError('Simulation has fewer events than requested')
        return tree.num_entries


def simulate(a):
    require(a.run_dir,'geometry'); cfg=snapshot(a.run_dir);p=stage(a.run_dir,'simulation')
    out=p/'events.edm4hep.root'
    if a.sim_input:
        if not a.sim_input.is_file():raise FileNotFoundError(a.sim_input)
        out.symlink_to(a.sim_input.resolve())
        done(p,source=str(a.sim_input.resolve()),sha256=digest(out),input_events=check_simulation(out,cfg['events']),mode='existing simulation; no Geant4 run')
        return
    b=cfg['beam']
    cmd=['ddsim','--compactFile',a.run_dir/'geometry/misaligned.xml','--outputFile',out,
         '--numberOfEvents',str(cfg['events']),'--enableGun','--gun.particle',b['particle'],
         '--gun.energy',f"{b['energy_GeV']}*GeV",'--gun.thetaMin',str(b['theta_min']),
         '--gun.thetaMax',str(b['theta_max']),'--gun.phiMin',str(b['phi_min']),
         '--gun.phiMax',str(b['phi_max']),'--gun.distribution','uniform',
         '--gun.position='+' '.join(f'{v}*mm' for v in b.get('position_mm',[0.0,0.0,0.0])),
         '--vertexSigma',*map(str,b['vertex_sigma_mm_ns']),'--random.seed',str(b['seed'])]
    execute(cmd,p)
    if not out.is_file() or out.stat().st_size==0:raise RuntimeError('Missing simulation output')
    done(p,sha256=digest(out),input_events=check_simulation(out,cfg['events']),mode='Geant4')

def reconstruct(a):
    require(a.run_dir,'simulation');cfg=snapshot(a.run_dir)
    if a.after:require(a.run_dir,'correction')
    p=stage(a.run_dir,'after' if a.after else 'before'); c=cfg['reconstruction']
    geom=a.run_dir/('correction/corrected.xml' if a.after else 'geometry/nominal.xml')
    plugin=a.build_dir/'BeamTestReco.so'
    if not plugin.is_file():raise FileNotFoundError(f'Build plugin first: {plugin}')
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(prefix()/'lib')+':'+env.get('LD_LIBRARY_PATH','')
    env['JANA_PLUGIN_PATH']=f"{a.build_dir}:/opt/local/lib/EICrecon/plugins:/opt/local/lib/JANA/plugins"
    coll='EventHeader,SiMAPSHits,MPGDHits,ACLGADHits,LocalSiMAPSRecHits,LocalMPGDRecHits,LocalACLGADRecHits,LocalBeamTestTracks,LocalBeamTestTrajectories,LocalBeamTestTrackParameters,LocalBeamTestFitMeasurements,LocalBeamTestPredictedMeasurements,LocalBeamTestFilteredMeasurements,LocalBeamTestSmoothedMeasurements'
    cmd=['eicrecon','-Pplugins_to_ignore=default','-Pplugins=log,dd4hep,evaluator,acts,algorithms_init,beam,podio,BeamTestReco',
         '-Pnthreads=1',f"-Pjana:nevents={cfg['events']}",f'-Pdd4hep:xml_files={geom}',
         f"-PBeamTestReco:LocalBeamTestTracks:useMPGD={int(c['use_mpgd'])}",
         f"-PBeamTestReco:LocalBeamTestTracks:useACLGAD={int(c['use_aclgad'])}",
         f"-PBeamTestReco:LocalBeamTestTracks:outputTrackPDG={c['pdg']}",
         f"-PBeamTestReco:LocalBeamTestTracks:seedQOverP={c['q_over_p']}",
         '-Pbeamtstreco:milleEnabled=1',f'-Pbeamtstreco:milleOutputPath={p}/mille.dat',
         '-Pbeamtstreco:milleZRefMm=100.0','-Pbeamtstreco:milleRequireSingleTrack=1',
         '-Pbeamtstreco:milleInjectedShiftLayer=-1',f'-Ppodio:output_file={p}/reco.root',
         f'-Ppodio:output_collections={coll}',a.run_dir/'simulation/events.edm4hep.root']
    execute(cmd,p,env=env)
    log=(p/'stdout.log').read_text(); match=re.search(r'BeamTestMilleProcessor::Finish[^\n]*records=(\d+)[^\n]*measurements=(\d+)',log)
    evt=re.search(r'BeamTestEventProcessor::Finish events=(\d+)[^\n]*tracks_total=(\d+)',log)
    if not match or not evt or int(evt[1])!=cfg['events'] or int(evt[2])==0:raise RuntimeError('Missing/empty reconstruction counters')
    if int(match[1])!=int(evt[2]) or int(match[2])!=10*int(match[1]):raise RuntimeError('Mille counters do not match accepted tracks')
    done(p,events=int(evt[1]),tracks=int(evt[2]),records=int(match[1]),scalars=int(match[2]),
         plugin_sha256=digest(plugin),simulation_sha256=digest(a.run_dir/'simulation/events.edm4hep.root'),geometry_sha256=digest(geom))

def align(a):
    require(a.run_dir,'before');p=stage(a.run_dir,'alignment')
    template=(REPO/'examples/seven_layer_telescope/alignment/pede_template.txt').read_text()
    (p/'pede.txt').write_text(template.replace('@MILLE_FILE@',str(a.run_dir/'before/mille.dat')))
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(prefix()/'lib')+':'+env.get('LD_LIBRARY_PATH','')
    execute([prefix()/'bin/pede','pede.txt'],p,cwd=p,env=env)
    params=read_pede(p/'millepede.res')
    if 1002 not in params:raise RuntimeError('Missing L2 solution')
    end=(p/'millepede.end').read_text().strip()
    if not re.match(r'^[01]\b',end):raise RuntimeError(f'pede status: {end}')
    done(p,parameters_mm=params,status=end)

def read_pede(path):
    out={}
    for line in path.read_text().splitlines():
        fields=line.split()
        if len(fields)>1:
            try:out[int(fields[0])]=float(fields[1])
            except ValueError:pass
    return out

def correct(a):
    require(a.run_dir,'alignment');p=stage(a.run_dir,'correction')
    value=-read_pede(a.run_dir/'alignment/millepede.res')[1002]
    modified_xml(a.run_dir/'geometry/nominal.xml',p/'corrected.xml',2,value)
    done(p,layer=2,axis='global_x',applied_mm=value,measurement_bias_mm=-value,
         note='Apply only L2 X, matching the saved physical closure; other fitted components are not applied')

def validate(a):
    for s in ['before','after','correction']:require(a.run_dir,s)
    p=stage(a.run_dir,'validation')
    before=json.loads((a.run_dir/'before/complete.json').read_text());after=json.loads((a.run_dir/'after/complete.json').read_text())
    if before['simulation_sha256']!=after['simulation_sha256'] or before['plugin_sha256']!=after['plugin_sha256']:
        raise RuntimeError('Before/after inputs or plugin differ')
    cmd=[sys.executable,REPO/'local_detector_testbench/visualization/closure.py',
         '--nominal',a.run_dir/'geometry/nominal.xml','--misaligned',a.run_dir/'geometry/misaligned.xml',
         '--corrected',a.run_dir/'correction/corrected.xml','--before',a.run_dir/'before/reco.root',
         '--after',a.run_dir/'after/reco.root','--pede',a.run_dir/'alignment/millepede.res','--outdir',p/'plots']
    if a.reference:cmd+=['--reference',a.reference]
    execute(cmd,p)
    done(p,summary=str(p/'plots/summary.json'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step',choices=['prepare','simulate','reconstruct','align','correct','validate','all'])
    parser.add_argument('--result-dir','--run-dir',dest='run_dir',metavar='RESULT_DIR',type=Path,required=True,help='New per-result directory; --run-dir is a compatibility alias; existing stages are never overwritten')
    parser.add_argument('--case',type=Path,default=DEFAULT_CASE,help='Used only by prepare/all; later stages read the snapshot')
    parser.add_argument('--sim-input',type=Path,help='simulate/all: reuse existing ROOT, without rerunning Geant4')
    parser.add_argument('--after',action='store_true',help='reconstruct with corrected geometry')
    parser.add_argument('--build-dir',type=Path,default=REPO/'build/local_eicrecon_external')
    parser.add_argument('--reference',type=Path,help='validate/all: compare against saved metrics and fail outside tolerances')
    a=parser.parse_args()
    for k in ['run_dir','case','build_dir','sim_input','reference']:
        if getattr(a,k) is not None:setattr(a,k,getattr(a,k).resolve())
    if not a.run_dir.is_relative_to(REPO/'results') or a.run_dir == REPO/'results':
        parser.error('result directory must be a child of results/')
    if any(x.isspace() for x in str(a.run_dir)):parser.error('pede run directories must not contain whitespace')
    os.chdir(REPO)
    try:
        if a.step=='all':
            if a.run_dir.exists():raise FileExistsError('all requires a new run directory')
            prepare(a);simulate(a);a.after=False;reconstruct(a);align(a);correct(a);a.after=True;reconstruct(a);validate(a)
        else:globals()[a.step](a)
    except (OSError,ValueError,RuntimeError,KeyError) as e:
        parser.exit(1,f'ERROR: {e}\nPartial results retained; use a NEW run directory to retry.\n')
    print(f'Completed {a.step}: {a.run_dir}')
if __name__=='__main__':main()
