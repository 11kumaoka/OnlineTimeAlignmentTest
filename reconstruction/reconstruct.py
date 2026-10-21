"""Independent stage; invoke with python3 -m reconstruction.reconstruct."""
import json
import os
from pathlib import Path
import re
from research_common import REPO, cli_parser, run, require, stage, done, digest, prefix, execute, write_json

def reconstruct(a):
    require(a.run_dir,'step1')
    require(a.run_dir,'step2')
    cfg=json.loads((a.run_dir/'step2/config.json').read_text())
    config=a.config or (a.run_dir/'step3/config.json' if a.after else REPO/'reconstruction/configs/electron_1GeV.json')
    if a.after: require(a.run_dir,'step3')
    c=json.loads(config.read_text())
    if a.after:require(a.run_dir,'step5')
    p=stage(a.run_dir,'step6' if a.after else 'step3')
    write_json(p/'config.json',c)
    geom=a.run_dir/('step5/corrected.xml' if a.after else 'step1/nominal.xml')
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
         f'-Ppodio:output_collections={coll}',a.run_dir/'step2/events.edm4hep.root']
    execute(cmd,p,env=env)
    log=(p/'stdout.log').read_text(); match=re.search(r'BeamTestMilleProcessor::Finish[^\n]*records=(\d+)[^\n]*measurements=(\d+)',log)
    evt=re.search(r'BeamTestEventProcessor::Finish events=(\d+)[^\n]*tracks_total=(\d+)',log)
    if not match or not evt or int(evt[1])!=cfg['events'] or int(evt[2])==0:raise RuntimeError('Missing/empty reconstruction counters')
    if int(match[1])!=int(evt[2]) or int(match[2])!=10*int(match[1]):raise RuntimeError('Mille counters do not match accepted tracks')
    done(p,config_sha256=digest(p/'config.json'),events=int(evt[1]),tracks=int(evt[2]),records=int(match[1]),scalars=int(match[2]),
         plugin_sha256=digest(plugin),simulation_sha256=digest(a.run_dir/'step2/events.edm4hep.root'),geometry_sha256=digest(geom))


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--config', type=Path, help='Reconstruction settings; corrected reconstruction defaults to the step3 snapshot')
    parser.add_argument('--after', action='store_true', help='Use corrected Geometry and write step6/')
    parser.add_argument('--build-dir', type=Path, default=REPO/'build/local_eicrecon_external')
    run(reconstruct, parser)
