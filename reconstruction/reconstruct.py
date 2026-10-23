"""Independent stage; invoke with python3 -m reconstruction.reconstruct."""
import json
from pathlib import Path
from correction.scope import SO3_MODES
import re
from research_common import REPO, cli_parser, run, require, stage, done, digest, execute, write_json
from reconstruction.runtime import runtime
from digitization.contract import validate_contract

def reconstruct(a):
    if a.after: require(a.run_dir,'step3')
    previous = json.loads((a.run_dir/'step3/complete.json').read_text()) if a.after else None
    config = a.config or (a.run_dir/'step3/config.json' if a.after else REPO/'reconstruction/configs/electron_1GeV.json')
    c = json.loads(config.read_text())
    if a.geometry:
        geom = a.geometry
    else:
        require(a.run_dir,'step5' if a.after else 'step1')
        geom = a.run_dir/('step5/corrected.xml' if a.after else 'step1/nominal.xml')
    import xml.etree.ElementTree as ET
    tilt_attributes={'global_rx','global_ry'}|{f'global_r{i}{j}' for i in range(3) for j in range(3)}
    if any(tilt_attributes.intersection(node.attrib) for node in ET.parse(geom).iter()) and a.alignment_mode not in (*SO3_MODES,'l1_rx','l1_ry','l1_rx_ry','l1_l2_rx_ry'):
        raise ValueError('Tilted Geometry requires the experimental covariance-aware tilt writer; historical modes remain restricted')
    if a.input_mode == 'combined':
        if a.raw_input: raise ValueError('--raw-input requires the raw profile')
        require(a.run_dir,'step2')
        source = a.run_dir/'step2/events.edm4hep.root'
        cfg = json.loads((a.run_dir/'step2/config.json').read_text())
        events = a.events if a.events is not None else (previous['events'] if previous else cfg['events'])
        metadata = None
    else:
        if a.raw_input:
            source = a.raw_input
        elif a.after:
            source = Path(previous['input_source'])
        else:
            require(a.run_dir,'step2_digitization')
            source = a.run_dir/'step2_digitization/rawhits.edm4eic.root'
        metadata = a.raw_metadata or (a.run_dir/'step3/rawhit_contract.json' if a.after and not a.raw_input else source.parent/'rawhit_contract.json')
        contract, report = validate_contract(source,metadata,geom)
        events = a.events if a.events is not None else (previous['events'] if previous else report['events'])
        if events <= 0 or events > report['events']: raise ValueError('Invalid requested RawHit event count')
    if events <= 0: raise ValueError('events must be positive')
    plugin, env = runtime(a.build_dir)
    a.run_dir.mkdir(parents=True,exist_ok=True)
    p=stage(a.run_dir,'step6' if a.after else 'step3')
    write_json(p/'config.json',c)
    if metadata: write_json(p/'rawhit_contract.json',contract)
    coll='EventHeader,LocalSiMAPSRawHits,LocalMPGDRawHits,LocalACLGADRawHits,LocalSiMAPSRecHits,LocalMPGDRecHits,LocalACLGADRecHits,LocalBeamTestTracks,LocalBeamTestTrajectories,LocalBeamTestTrackParameters,LocalBeamTestFitMeasurements,LocalBeamTestPredictedMeasurements,LocalBeamTestFilteredMeasurements,LocalBeamTestSmoothedMeasurements,LocalBeamTestPredictedSegments,LocalBeamTestFilteredSegments,LocalBeamTestSmoothedSegments'
    if a.input_mode == 'combined': coll+=',SiMAPSHits,MPGDHits,ACLGADHits'
    cmd=['eicrecon','-Pplugins_to_ignore=default','-Pplugins=log,dd4hep,evaluator,acts,algorithms_init,beam,podio,BeamTestReco',
         f'-Pbeamtstreco:profile={a.input_mode}','-Pnthreads=1',f'-Pjana:nevents={events}',f'-Pdd4hep:xml_files={geom}',
         f"-PBeamTestReco:LocalBeamTestTracks:useMPGD={int(c['use_mpgd'])}",
         f"-PBeamTestReco:LocalBeamTestTracks:useACLGAD={int(c['use_aclgad'])}",
         f"-PBeamTestReco:LocalBeamTestTracks:outputTrackPDG={c['pdg']}",
         f"-PBeamTestReco:LocalBeamTestTracks:seedQOverP={c['q_over_p']}",
         '-Pbeamtstreco:milleEnabled=1',f'-Pbeamtstreco:milleOutputPath={p}/mille.dat',
         '-Pbeamtstreco:milleZRefMm=100.0','-Pbeamtstreco:milleRequireSingleTrack=1',
         '-Pbeamtstreco:milleInjectedShiftLayer=-1',f'-Ppodio:output_file={p}/reco.root',
         f'-Ppodio:output_collections={coll}',source]
    if a.alignment_mode!='legacy':cmd.insert(-1,f'-Pbeamtstreco:milleAlignmentMode={a.alignment_mode}')
    execute(cmd,p,env=env)
    log=(p/'stdout.log').read_text(); match=re.search(r'BeamTestMilleProcessor::Finish[^\n]*records=(\d+)[^\n]*measurements=(\d+)',log)
    evt=re.search(r'BeamTestEventProcessor::Finish events=(\d+)[^\n]*tracks_total=(\d+)',log)
    if not match or not evt or int(evt[1])!=events or int(evt[2])==0:raise RuntimeError('Missing/empty reconstruction counters')
    if int(match[1])!=int(evt[2]) or int(match[2])!=10*int(match[1]):raise RuntimeError('Mille counters do not match accepted tracks')
    if a.input_mode == 'raw' and 'SiliconTrackerDigi::process' in log: raise RuntimeError('RawHit reconstruction unexpectedly ran Digitization')
    done(p,input_mode=a.input_mode,input_source=str(source),input_sha256=digest(source),
         raw_input_sha256=digest(source) if metadata else None,
         config_sha256=digest(p/'config.json'),events=int(evt[1]),tracks=int(evt[2]),records=int(match[1]),scalars=int(match[2]),
         plugin_sha256=digest(plugin),simulation_sha256=digest(source) if not metadata else contract['producer'].get('simulation_sha256'),geometry_sha256=digest(geom))


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--alignment-mode',choices=[*SO3_MODES,'legacy','l1_ry','l1_rx','l1_rz','l1_l2_rz','l1_l2_xy_rz','l1_z','l1_l2_z','l1_l2_xyz'],default='legacy',help='Opt-in experimental rotation derivatives; default preserves Mille bytes')
    parser.add_argument('--raw-input',type=Path,help='Explicit RawHit PODIO ROOT input; no Simulation stages required')
    parser.add_argument('--raw-metadata',type=Path,help='RawHit contract JSON; defaults to input sibling rawhit_contract.json')
    parser.add_argument('--geometry',type=Path,help='Explicit reconstruction Geometry, independent of the data source')
    parser.add_argument('--events',type=int,help='Events to process; defaults to all RawHit events')
    parser.add_argument('--input-mode',choices=['raw','combined'],default='raw',help='combined is the preserved Simulation diagnostic profile')
    parser.add_argument('--config', type=Path, help='Reconstruction settings; corrected reconstruction defaults to the step3 snapshot')
    parser.add_argument('--after', action='store_true', help='Use corrected Geometry and write step6/')
    parser.add_argument('--build-dir', type=Path, default=REPO/'build/local_eicrecon_external')
    run(reconstruct, parser)
