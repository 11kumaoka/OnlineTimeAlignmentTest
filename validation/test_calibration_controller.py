"""Control-plane invariants; physics execution is tested separately with saved RawHits."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from calibration.controller import select,recover
from calibration.input_monitor import scan,verify_input
from calibration.queue_manager import Queue,exclusive,recover_guard
from calibration.geometry_manager import Geometries
from calibration.convergence import evaluate
from research_common import REPO,digest


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.queue=Queue(self.root);self.incoming=self.root/'incoming';self.incoming.mkdir()
        self.config={'ordering':'sequence','first_sequence':1,'gap_policy':'wait',
                     'fallback_geometry':str(REPO/'geometry/nominal/seven_layer_telescope.xml')}
    def tearDown(self):self.temp.cleanup()
    def delivery(self,name,sequence,payload=None):
        raw=self.incoming/(name+'.root');raw.write_text(payload or name)
        meta=self.incoming/(name+'.json');meta.write_text('{}')
        marker=self.incoming/(name+'.ready.json')
        marker.write_text(json.dumps({'schema':'rawhit-delivery-v1','input_id':name,'sequence':sequence,
            'raw_file':raw.name,'raw_sha256':digest(raw),'metadata_file':meta.name,'metadata_sha256':digest(meta)}))
        return raw,marker
    @patch('calibration.input_monitor.validate_contract')
    def test_readiness_order_gap_and_duplicates(self,contract):
        (self.incoming/'unfinished.root').write_text('partial')
        scan(self.queue,self.incoming,Path(self.config['fallback_geometry']),'sequence')
        self.assertEqual(self.queue.jobs(),[])
        self.delivery('B',2);scan(self.queue,self.incoming,Path(self.config['fallback_geometry']),'sequence')
        self.assertIsNone(select(self.queue,self.config))
        self.delivery('A',1);scan(self.queue,self.incoming,Path(self.config['fallback_geometry']),'sequence')
        self.assertEqual(select(self.queue,self.config)['id'],'A')
        self.delivery('copy',3,payload='A');scan(self.queue,self.incoming,Path(self.config['fallback_geometry']),'sequence')
        self.assertEqual(len(self.queue.jobs()),2);self.assertTrue(self.queue.issues())
    @patch('calibration.input_monitor.validate_contract')
    def test_mutation_and_checksum_rejected(self,contract):
        raw,marker=self.delivery('A',1);raw.write_text('changed')
        scan(self.queue,self.incoming,Path(self.config['fallback_geometry']),'sequence')
        self.assertFalse(self.queue.jobs());self.assertTrue(self.queue.issues())
        raw.write_text('A');scan(self.queue,self.incoming,Path(self.config['fallback_geometry']),'sequence')
        raw.write_text('mutated after acceptance')
        with self.assertRaises(RuntimeError):verify_input(self.queue.job('A'))
    @patch('calibration.input_monitor.validate_contract')
    def test_gap_policies_and_interrupted_recovery(self,contract):
        self.delivery('A',2);scan(self.queue,self.incoming,Path(self.config['fallback_geometry']),'sequence')
        self.config['gap_policy']='error'
        with self.assertRaises(RuntimeError):select(self.queue,self.config)
        self.config['gap_policy']='skip';self.assertEqual(select(self.queue,self.config)['id'],'A')
        registry=Geometries(self.queue,self.config);registry.initialize()
        job=self.queue.job('A');directory=self.root/'jobs/A/attempt-001';directory.mkdir(parents=True)
        job.update(status='running',geometry=registry.active(),attempts=[{'directory':str(directory),'status':'running'}])
        self.queue.update(job);recover(self.queue,registry)
        self.assertEqual(self.queue.job('A')['status'],'interrupted')
        self.assertTrue(directory.is_dir())

    def test_lock_and_explicit_activation(self):
        with exclusive(self.root):
            with self.assertRaises(RuntimeError):
                with exclusive(self.root):pass
        registry=Geometries(self.queue,self.config);registry.initialize();original=registry.active()
        with self.assertRaises(ValueError):registry.activate(original['id'])
        self.assertEqual(registry.active()['id'],original['id'])
        self.assertEqual(digest(Path(original['path'])),original['sha256'])
    def test_abrupt_owner_requires_explicit_guard_recovery(self):
        import os,socket
        guard=self.root/'controller.guard';guard.mkdir()
        (guard/'owner.json').write_text(json.dumps({'pid':os.getpid(),'host':socket.gethostname()}))
        with self.assertRaises(RuntimeError):recover_guard(self.root,'Owner still running')
        (guard/'owner.json').write_text(json.dumps({'pid':99999999,'host':socket.gethostname()}))
        with self.assertRaises(ValueError):recover_guard(self.root,'')
        recover_guard(self.root,'Synthetic dead-owner recovery test')
        self.assertFalse(guard.exists())
        with exclusive(self.root):self.assertTrue(guard.is_dir())

    def test_quality_does_not_accept_invalid_fits(self):
        policy={'min_tracks':20,'delta_tolerance_mm':.005,'max_update_mm':.5,'max_track_chi2_ratio':1000,'policy_label':'demonstration'}
        self.assertTrue(evaluate(.001,2,99,policy)['converged'])
        for delta,chi,tracks in [(float('nan'),2,99),(.6,2,99),(.001,2,1)]:
            with self.assertRaises(RuntimeError):evaluate(delta,chi,tracks,policy)


if __name__=='__main__':unittest.main()
