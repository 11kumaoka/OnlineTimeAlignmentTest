"""Focused rotation placement, composition and scope safety tests."""
import math
import tempfile
import unittest
from pathlib import Path
from geometry.prepare import DEFAULT_NOMINAL,write_shifted_xml,load_geometry_config
from geometry.placements import placement_transforms
from geometry.transforms import axis_rotation
from correction.scope import verify_scope
import xml.etree.ElementTree as ET
import json

class Rotation(unittest.TestCase):
    def test_center_sign_inverse_and_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'rotated.xml'
            write_shifted_xml(DEFAULT_NOMINAL,p,{1:1.25},{1:-.75},rz_rad={1:.02})
            t=placement_transforms(p)[1]
            self.assertEqual(t.translation,(1.25,-.75,50.))
            self.assertGreater(t.apply((1,0,0))[1],t.translation[1])
            composed=t.updated(rotation=axis_rotation('z',-.03),pivot=t.translation)
            self.assertAlmostEqual(math.atan2(composed.rotation[1][0],composed.rotation[0][0]),-.01)
            for a,b in zip(composed.translation,t.translation):self.assertAlmostEqual(a,b)
            self.assertEqual(composed.inverse().apply(composed.apply((0,0,0))),(0.,0.,0.))
    def test_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'rotated.xml'
            write_shifted_xml(DEFAULT_NOMINAL,p,{},rz_rad={1:-.02})
            verify_scope(DEFAULT_NOMINAL,p,(1,),('rz',))
            with self.assertRaises(ValueError):verify_scope(DEFAULT_NOMINAL,p,(1,),('x',))
            with self.assertRaises(ValueError):write_shifted_xml(DEFAULT_NOMINAL,Path(directory)/'bad.xml',{},rz_rad={4:.02})
    def test_angular_policy_has_separate_units(self):
        from calibration.convergence import evaluate_rotation
        policy={'delta_tolerance_mm':.005,'max_update_mm':.5,'delta_tolerance_rad':1e-5,
                'max_update_rad':.05,'min_tracks':20,'max_track_chi2_ratio':1000.,'policy_label':'test'}
        self.assertFalse(evaluate_rotation(.001,2.,98,policy)['converged'])
        self.assertTrue(evaluate_rotation(1e-7,2.,98,policy)['converged'])
        for angle in (.1,float('nan')):
            with self.assertRaises(RuntimeError):evaluate_rotation(angle,2.,98,policy)
        with self.assertRaises(RuntimeError):evaluate_rotation(0.,2.,1,policy)

    def test_controller_requires_matching_derivative_evidence(self):
        from calibration.settings import load
        from research_common import REPO,digest
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);build=directory/'build';build.mkdir()
            (build/'BeamTestReco.so').write_bytes(b'test plugin fingerprint only')
            proof=directory/'proof.json';proof.write_text(json.dumps({'passed':True,'actual_binary_entries':2,'label':3001}))
            gate=directory/'gate.json';evidence={'passed':True,'plugin_sha256':digest(build/'BeamTestReco.so'),
                'derivative_report':str(proof),'derivative_report_sha256':digest(proof)}
            gate.write_text(json.dumps(evidence))
            c=json.loads((REPO/'calibration/config/l1_rz_demo.json').read_text())
            c['build_dir']=str(build);c['calibration']['rotation_derivative_report']=str(gate)
            cfg=directory/'config.json';cfg.write_text(json.dumps(c));load(cfg)
            evidence['plugin_sha256']='0'*64;gate.write_text(json.dumps(evidence))
            with self.assertRaisesRegex(ValueError,'different plugin'):load(cfg)
            evidence['plugin_sha256']=digest(build/'BeamTestReco.so');gate.write_text(json.dumps(evidence))
            c['calibration']['correction_mode']='l1_l2_rz';cfg.write_text(json.dumps(c))
            with self.assertRaisesRegex(ValueError,'Missing selected'):load(cfg)

    def test_merging_label_gates_preserves_provenance(self):
        from validation.validate_rz_derivatives import merge_gate
        from research_common import digest
        with tempfile.TemporaryDirectory() as temp:
            gates=[]
            for layer in (1,2):
                report=Path(temp)/f'label{layer}.json';report.write_text(json.dumps({'passed':True,'label':3000+layer}))
                gates.append({'passed':True,'plugin_sha256':'metadata-only test','derivative_report':str(report),'derivative_report_sha256':digest(report)})
            merged=merge_gate(gates[1],gates[0]);self.assertEqual(len(merged['derivative_reports']),2)
            self.assertEqual(merged['derivative_reports'][0]['sha256'],gates[0]['derivative_report_sha256'])
            changed=dict(gates[0],plugin_sha256='another build')
            with self.assertRaises(ValueError):merge_gate(gates[1],changed)
            Path(gates[0]['derivative_report']).write_text('{}')
            with self.assertRaises(ValueError):merge_gate(gates[1],gates[0])

    def test_unsupported_axes(self):
        with tempfile.TemporaryDirectory() as directory:
            for field in ('global_rx_rad','global_ry_rad'):
                p=Path(directory)/'scenario.json'
                p.write_text(json.dumps({'detector':'SiMAPS','global_x_shifts_mm':{},field:{'4':.01}}))
                with self.assertRaises(ValueError):load_geometry_config(p,ET.parse(DEFAULT_NOMINAL).getroot())

if __name__=='__main__':unittest.main()
