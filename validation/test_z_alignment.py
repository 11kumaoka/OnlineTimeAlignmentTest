"""Physical Z sign/composition, scope, evidence freshness, and weak-design refusal."""
import json,shutil,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from geometry.prepare import DEFAULT_NOMINAL,write_shifted_xml
from geometry.placements import placement_transforms
from correction.correct_geometry import correct
from correction.scope import verify_scope,layers_for
from research_common import done,digest,REPO


class ZAlignment(unittest.TestCase):
    def test_global_z_preserves_xy_orientation_and_unselected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);base=p/'base.xml';updated=p/'updated.xml'
            write_shifted_xml(DEFAULT_NOMINAL,base,{1:1.25},{1:-.75},rz_rad={1:.017})
            write_shifted_xml(base,updated,{},z_shifts={1:2.})
            a,b=placement_transforms(base),placement_transforms(updated)
            self.assertEqual(b[1].translation,(1.25,-.75,52.))
            self.assertEqual(a[1].rotation,b[1].rotation)
            for l in (0,2,3,4,5,6):self.assertEqual(a[l],b[l])
            verify_scope(base,updated,(1,),('z',))
            with self.assertRaises(ValueError):verify_scope(base,updated,(2,),('z',))
            for layer in (0,4,5,6):
                with self.assertRaises(ValueError):write_shifted_xml(base,p/f'bad{layer}.xml',{},z_shifts={layer:1.})
    def test_physical_positive_and_negative_cumulative_sign(self):
        for shift in (2.,-2.):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);(p/'step1').mkdir();(p/'step4').mkdir()
                nominal=p/'step1/nominal.xml';shutil.copyfile(DEFAULT_NOMINAL,nominal)
                (p/'step1/geometry_config.json').write_text(json.dumps({'detector':'SiMAPS','global_x_shifts_mm':{},'global_z_shifts_mm':{'1':0}}));done(p/'step1')
                (p/'step4/millepede.res').write_text(f'4001 {shift}\n');done(p/'step4')
                base=p/'base.xml';write_shifted_xml(nominal,base,{},z_shifts={1:1.})
                correct(SimpleNamespace(run_dir=p,mode='l1_z',base_geometry=base))
                self.assertAlmostEqual(placement_transforms(p/'step5/corrected.xml')[1].translation[2],51+shift)
    def test_zero_and_narrow_information_refusal(self):
        import numpy as np
        from validation.z_observability import information,enforce
        blocks=[]
        for slope in (-1e-7,1e-7):
            rows=[]
            for layer in range(5):
                rows.extend([(0.,.01,{1:1.,3:50.*layer-100},{4001:slope if layer==1 else 0}),
                             (0.,.01,{2:1.,4:50.*layer-100},{4001:-slope if layer==1 else 0})])
            blocks.append(rows)
        with self.assertRaises(ValueError):enforce({'selected':information(blocks,[4001],0.)},.5)
        with self.assertRaises(ValueError):enforce({'selected':information(blocks,[4001])},.5)
    def test_gate_requires_matching_plugin_and_geometry_factory(self):
        from calibration.settings import load
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);build=p/'build';build.mkdir()
            for name in ('BeamTestReco.so','libLocalTelescopeGeometry.so'):(build/name).write_bytes(name.encode())
            proof=p/'proof.json';proof.write_text(json.dumps({'passed':True,'actual_binary_entries':2,'label':4001,'linearization':'profiled_local_slopes_v1','plugin_sha256':digest(build/'BeamTestReco.so'),'geometry_plugin_sha256':digest(build/'libLocalTelescopeGeometry.so')}))
            gate=p/'gate.json';evidence={'passed':True,'linearization':'profiled_local_slopes_v1','plugin_sha256':digest(build/'BeamTestReco.so'),'geometry_plugin_sha256':digest(build/'libLocalTelescopeGeometry.so'),'derivative_reports':[{'path':str(proof),'sha256':digest(proof)}]};gate.write_text(json.dumps(evidence))
            cfg=json.loads((REPO/'calibration/config/demo.json').read_text());cfg['build_dir']=str(build);cfg['steering']='alignment/pede_l1_z.txt';cfg['scenario']='geometry/scenarios/L1_z_reference.json';cfg['calibration'].update(correction_mode='l1_z',z_derivative_report=str(gate),z_max_nominal_sigma_mm=.5)
            path=p/'cfg.json';path.write_text(json.dumps(cfg));load(path)
            original=json.loads(json.dumps(cfg))
            cfg['calibration']['z_derivative_report']=str(p/'missing.json');path.write_text(json.dumps(cfg))
            with self.assertRaises(FileNotFoundError):load(path)
            cfg=json.loads(json.dumps(original));cfg['calibration']['correction_mode']='l1_l2_z';path.write_text(json.dumps(cfg))
            with self.assertRaisesRegex(ValueError,'Missing selected Z'):load(path)
            cfg=json.loads(json.dumps(original));path.write_text(json.dumps(cfg))
            evidence['plugin_sha256']='0'*64;gate.write_text(json.dumps(evidence))
            with self.assertRaisesRegex(ValueError,'different plugin'):load(path)
            evidence['plugin_sha256']=digest(build/'BeamTestReco.so');gate.write_text(json.dumps(evidence))
            original_proof=proof.read_bytes();proof.write_text('{}')
            with self.assertRaisesRegex(ValueError,'evidence changed'):load(path)
            proof.write_bytes(original_proof)
            (build/'libLocalTelescopeGeometry.so').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'different plugin or Geometry'):load(path)
    def test_unsupported_dofs(self):
        for mode in ('rx','ry','all_dof','l1_l2_xyz_rz'):
            with self.assertRaises(ValueError):layers_for(mode)


if __name__=='__main__':unittest.main()
