"""Foreground single-worker controller; numerical work remains in independent stage CLIs."""
import argparse
import os
import hashlib
import json
import shutil
import signal
import threading
import time
from pathlib import Path
from calibration import settings
from calibration.geometry_manager import Geometries
from calibration.input_monitor import scan, verify_input
from calibration.iteration import iterate, reconstruction_args, verify_outputs
from calibration.queue_manager import Queue, exclusive, recover_guard
from calibration.runner import stage
from research_common import REPO, digest, write_json, require


def select(queue, config, allowed=None):
    pending=[j for j in queue.jobs() if j['status']=='pending' and (allowed is None or j['id'] in allowed)]
    if not pending:return None
    if config['ordering']=='identity':return min(pending,key=lambda j:j['id'])
    expected=queue.get('next_sequence',config['first_sequence'])
    retries=[j for j in pending if j['sequence']<expected and j.get('retry_requested')]
    if retries:return min(retries,key=lambda j:j['sequence'])
    job=min(pending,key=lambda j:j['sequence'])
    if job['sequence']<expected:raise RuntimeError('Late sequence requires explicit operator resolution')
    if job['sequence']!=expected:
        gap={'expected':expected,'available':job['sequence'],'policy':config['gap_policy']}
        queue.put('sequence_gap',gap)
        if config['gap_policy']=='wait':return None
        if config['gap_policy']=='error':raise RuntimeError('Missing upstream sequence: '+str(expected))
        queue.event('sequence_gap_skipped',**gap)
    queue.put('sequence_gap',None)
    return job


def process(queue,config,geometries,job,lock_fd,stop,manual=False):
    verify_input(job)
    if not manual and len(job['attempts'])>=config['max_attempts']:raise RuntimeError('Attempt limit reached')
    version=geometries.verify(job['geometry']) if job['geometry'] else geometries.active()
    job['geometry']=version
    number=len(job['attempts'])+1
    directory=queue.state/'jobs'/job['id']/f'attempt-{number:03d}'
    directory.mkdir(parents=True,exist_ok=False)
    attempt={'directory':str(directory),'started_at':time.time(),'manual_calibration':manual,'status':'running'}
    job['attempts'].append(attempt);job['status']='running';queue.update(job)
    def progress(phase):
        job['phase']=phase;queue.update(job)
        queue.event('stage_started',input_id=job['id'],phase=phase,attempt=number)
    try:
        snapshot=directory/'input';snapshot.mkdir()
        raw=snapshot/'rawhits.root';metadata=snapshot/'rawhit_contract.json'
        for source,target,sha in [(job['raw_path'],raw,job['raw_sha256']),
                                  (job['metadata_path'],metadata,job['metadata_sha256']),
                                  (job['marker_path'],snapshot/'ready.json',job['marker_sha256'])]:
            shutil.copyfile(source,target)
            if digest(target)!=sha:raise RuntimeError('Input changed while snapshotting')
        verify_input(job)
        contract=json.loads(metadata.read_text())
        compatibility={key:contract[key] for key in ('readout_signature_sha256','conditions')}
        compatibility['topology_signature_sha256']=contract.get('topology_signature_sha256')
        compatibility.update(geometry_sha256=version['sha256'],reconstruction_config_sha256=digest(config['reconstruction_config']),
                             plugin_sha256=digest(Path(config['build_dir'])/'BeamTestReco.so'))
        compatibility_sha=hashlib.sha256(json.dumps(compatibility,sort_keys=True).encode()).hexdigest()
        write_json(directory/'provenance.json',{'input_id':job['id'],'raw_sha256':job['raw_sha256'],
            'compatibility':compatibility,'compatibility_sha256':compatibility_sha,
            'geometry':version,'configuration_fingerprint':queue.get('config_fingerprint'),
            'accumulation':'none; each input is a fixed independent dataset'})
        run=directory/'reconstruction'
        stage('reconstruction.reconstruct',reconstruction_args(config,raw,metadata,Path(version['path']),run),
              directory/'commands'/'reconstruction',lock_fd,stop,progress)
        require(run,'step3');result=json.loads((run/'step3/complete.json').read_text());job['reconstruction_status']='completed'
        policy=config['calibration']
        if manual and not policy['enabled']:raise ValueError('Manual calibration requires an enabled policy')
        if policy['enabled'] and result['tracks']>=policy['min_tracks']:
            job['calibration_status']='running';queue.update(job)
            report=iterate(config,queue,geometries,raw,metadata,version,directory/'calibration',lock_fd,stop,progress)
            job['calibration_status']='converged' if report['converged'] else 'not_converged'
            if not report['converged']:raise RuntimeError('Calibration reached its iteration limit without convergence')
        else:job['calibration_status']='insufficient_tracks' if policy['enabled'] else 'disabled'
        verify_outputs(directory)
        integrity={str(p.relative_to(directory)):digest(p) for p in directory.rglob('*') if p.is_file()}
        write_json(directory/'integrity.json',integrity);attempt['integrity_sha256']=digest(directory/'integrity.json')
        job['status']='completed';attempt['status']='completed';job['outputs'].append(str(directory))
    except InterruptedError as error:
        job['status']='interrupted';attempt.update(status='interrupted',error=str(error))
    except Exception as error:
        job['status']='failed';attempt.update(status='failed',error=str(error))
        if job['calibration_status']=='running':job['calibration_status']='failed'
        elif job['reconstruction_status']!='completed':job['reconstruction_status']='failed'
    finally:
        attempt['finished_at']=time.time();queue.update(job)
        queue.event('attempt_finished',input_id=job['id'],status=job['status'],attempt=number)
    if job['status']!='interrupted' and config['ordering']=='sequence':
        queue.put('next_sequence',max(queue.get('next_sequence',config['first_sequence']),job['sequence']+1))


def recover(queue,geometries):
    geometries.active()
    for version in queue.geometries():geometries.verify(version)
    for job in queue.jobs():
        verify_input(job)
        if job['geometry']:geometries.verify(job['geometry'])
        for attempt in job['attempts']:
            directory=Path(attempt['directory'])
            verify_outputs(directory)
            if attempt.get('integrity_sha256'):
                marker=directory/'integrity.json'
                if digest(marker)!=attempt['integrity_sha256']:raise RuntimeError('Attempt integrity record changed')
                for filename,sha in json.loads(marker.read_text()).items():
                    if digest(directory/filename)!=sha:raise RuntimeError('Attempt output changed: '+filename)
        if job['status']=='running':
            job['status']='interrupted';job['attempts'][-1].update(status='interrupted',error='Recovered unfinished attempt; explicit retry required')
            queue.update(job);queue.event('interrupted_recovered',input_id=job['id'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['once','watch','queue','geometry','retry','calibrate','review','activate','recover-lock'])
    parser.add_argument('--config',type=Path,default=REPO/'calibration/config/demo.json')
    parser.add_argument('--state-dir',type=Path,required=True)
    parser.add_argument('--input-dir',type=Path,default=REPO/'input')
    parser.add_argument('--input-id');parser.add_argument('--version-id');parser.add_argument('--evidence',type=Path)
    parser.add_argument('--reason',help='Required explicit retry justification')
    args=parser.parse_args();state=args.state_dir.resolve();incoming=args.input_dir.resolve()
    if args.action in ('queue','geometry'):
        queue=Queue(state,readonly=True)
        print(json.dumps({'jobs':queue.jobs(),'issues':queue.issues(),'sequence_gap':queue.get('sequence_gap')} if args.action=='queue'
                         else queue.geometry(queue.get('active_geometry')),indent=2));return
    if not state.is_relative_to(REPO/'result') or state==REPO/'result':
        parser.error('State must be a dedicated subdirectory under result/')
    if state.is_relative_to(incoming) or incoming.is_relative_to(state):parser.error('Input and state must be disjoint')
    if not incoming.is_dir():parser.error('Input directory does not exist')
    if args.action=='recover-lock':
        recover_guard(state,args.reason);return
    config,fingerprint=settings.load(args.config)
    os.environ['TESTBENCH_BUILD_DIR']=config['build_dir']
    stop=threading.Event();monitor_stop=threading.Event();monitor_errors=[]
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
    with exclusive(state) as lock_fd:
        queue=Queue(state)
        previous_input=queue.get('input_directory')
        if previous_input and previous_input!=str(incoming):raise RuntimeError('Input directory changed; use the original directory or a new state')
        queue.put('input_directory',str(incoming))
        previous=queue.get('config_fingerprint')
        if previous and previous!=fingerprint:raise RuntimeError('Configuration/dependency changed; use a new state directory')
        if not previous:
            write_json(state/'config.json',config);queue.put('config_fingerprint',fingerprint)
        geometries=Geometries(queue,config);geometries.initialize();recover(queue,geometries)
        if args.action=='retry':
            job=queue.job(args.input_id)
            if not job or job['status'] not in ('failed','interrupted') or not args.reason:raise ValueError('Retry requires failed/interrupted input and --reason')
            if len(job['attempts'])>=config['max_attempts']:raise ValueError('Bounded retry limit reached')
            job.update(status='pending',retry_requested=True);queue.update(job)
            queue.event('retry_requested',input_id=job['id'],reason=args.reason);return
        if args.action=='review':
            if not args.evidence or not args.version_id:parser.error('review requires --version-id and --evidence')
            geometries.review(args.version_id,args.evidence.resolve());return
        if args.action=='activate':
            if not args.version_id:parser.error('activate requires --version-id')
            geometries.activate(args.version_id);return
        if args.action=='calibrate':
            job=queue.job(args.input_id)
            if not job or job['status']!='completed':raise ValueError('Manual calibration requires a completed input')
            process(queue,config,geometries,job,lock_fd,stop,manual=True)
            if job['status']!='completed':raise RuntimeError('Manual calibration failed; inspect queue')
            return
        def discover():scan(queue,incoming,Path(config['fallback_geometry']),config['ordering'])
        discover();allowed={j['id'] for j in queue.jobs()} if args.action=='once' else None
        def monitor():
            while not monitor_stop.wait(config['poll_seconds']):
                try:discover()
                except Exception as error:monitor_errors.append(str(error));stop.set();return
        thread=threading.Thread(target=monitor,daemon=True);thread.start()
        try:
            while not stop.is_set():
                job=select(queue,config,allowed)
                if job:process(queue,config,geometries,job,lock_fd,stop)
                elif args.action=='once':break
                else:stop.wait(config['poll_seconds'])
        finally:monitor_stop.set();thread.join()
        if monitor_errors:raise RuntimeError('Input monitor failed: '+monitor_errors[0])
        if any(j['status'] in ('failed','interrupted') for j in queue.jobs()):raise RuntimeError('Queue contains failed/interrupted jobs; inspect and explicitly retry')


if __name__=='__main__':main()
