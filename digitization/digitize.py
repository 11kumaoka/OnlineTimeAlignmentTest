"""Run only Digitization and persist the common, truth-free RawHit input."""
import json
from pathlib import Path
from digitization.contract import RAW_COLLECTIONS, inspect_raw, readout_signature, topology_signature
from reconstruction.runtime import runtime
from research_common import REPO, cli_parser, run, require, stage, done, digest, execute, write_json


def digitize(a):
    require(a.run_dir,'step1'); require(a.run_dir,'step2')
    cfg = json.loads((a.run_dir/'step2/config.json').read_text())
    measured_geometry = a.run_dir/'step1/misaligned.xml'
    geometry = a.geometry or measured_geometry
    if readout_signature(geometry) != readout_signature(measured_geometry):
        raise ValueError('Digitization Geometry must retain the measured readout definition')
    source = a.run_dir/'step2/events.edm4hep.root'
    plugin, env = runtime(a.build_dir)
    p = stage(a.run_dir,'step2_digitization')
    command = ['eicrecon','-Pplugins_to_ignore=default',
               '-Pplugins=log,dd4hep,evaluator,acts,algorithms_init,podio,BeamTestReco',
               '-Pbeamtstreco:profile=digitization','-Pnthreads=1',f"-Pjana:nevents={cfg['events']}",
               f'-Pdd4hep:xml_files={geometry}',f'-Ppodio:output_file={p}/rawhits.edm4eic.root',
               '-Ppodio:output_collections='+','.join(('EventHeader',*RAW_COLLECTIONS)),source]
    write_json(p/'config.json',{'profile':'digitization','events':cfg['events'],
                              'conditions':'unchanged factory defaults; see rawhit_contract.json'})
    execute(command,p,env=env)
    output = p/'rawhits.edm4eic.root'
    report = inspect_raw(output)
    if report['events'] != cfg['events']: raise RuntimeError('Digitization event count mismatch')
    if set(report['collections']) != {'EventHeader',*RAW_COLLECTIONS}:
        raise RuntimeError('Production RawHit output contains unexpected collections')
    log = (p/'stdout.log').read_text()
    if 'BeamTestACTSFitter::process' in log or 'TrackerHitReconstruction::process' in log or 'BeamTestMilleProcessor::Init' in log:
        raise RuntimeError('Digitization-only profile unexpectedly executed reconstruction')
    write_json(p/'rawhit_contract.json',{
        'schema':'local-telescope-rawhits-v2','raw_sha256':digest(output),
        'readout_signature_sha256':readout_signature(geometry),'simulation_truth_geometry_sha256':digest(measured_geometry),'topology_signature_sha256':topology_signature(geometry),
        'digitization_geometry_sha256':digest(geometry),
        'charge_unit':'keV_equivalent','timestamp_unit':'ps','source_kind':'simulation',
        'producer':{'plugin_sha256':digest(plugin),'simulation_sha256':digest(source)},
        'conditions':{'digitizer':'unchanged SiliconTrackerDigi factory defaults',
                      'registration_sha256':digest(REPO/'localDetEICrecon/plugins/BeamTestReco.cc'),
                      'algorithm_sha256':digest(REPO/'localDetEICrecon/algorithms/digi/SiliconTrackerDigi.cc'),
                      'config_definition_sha256':digest(REPO/'localDetEICrecon/algorithms/digi/SiliconTrackerDigiConfig.h'),
                      'simaps_threshold':'0.54*dd4hep::keV','simaps_time_resolution_ns':8,
                      'mpgd_threshold':'100*dd4hep::eV','mpgd_time_resolution_ns':10,
                      'aclgad_threshold':0,'aclgad_time_resolution_ns':0.025,
                      'event_header_timestamp':'preserved EDM4hep producer field; not RawHit ps'},
        'inspection':report})
    done(p,**report,plugin_sha256=digest(plugin),simulation_sha256=digest(source),geometry_sha256=digest(geometry))


if __name__ == '__main__':
    parser = cli_parser(__doc__)
    parser.add_argument('--geometry',type=Path,help='Geometry loaded by EICrecon; default measured step1 XML; readout must match')
    parser.add_argument('--build-dir',type=Path,default=REPO/'build/local_eicrecon_external')
    run(digitize,parser)
