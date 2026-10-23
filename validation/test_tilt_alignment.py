"""Physical tilt composition, serialization and policy safety checks."""
import json,math,tempfile,unittest
from pathlib import Path
from geometry.prepare import write_shifted_xml,DEFAULT_NOMINAL,load_geometry_config
from geometry.placements import placement_transforms
from geometry.transforms import axis_rotation,multiply,transpose
from correction.scope import verify_scope,layers_for
import xml.etree.ElementTree as ET


class Tilt(unittest.TestCase):
    def test_full_matrix_composition_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.xml';b=Path(tmp)/'b.xml'
            write_shifted_xml(DEFAULT_NOMINAL,a,{1:1.25},{1:-.75},rz_rad={1:.017},z_shifts={1:2.},rx_rad={1:.03},ry_rad={1:-.025})
            before=placement_transforms(a)
            updated=before[1].updated(rotation=axis_rotation('x',-.02),translation=(.2,-.1,.3),pivot=before[1].translation)
            write_shifted_xml(a,b,{1:updated.translation[0]},{1:updated.translation[1]},z_shifts={1:2.3},rotations={1:updated.rotation})
            after=placement_transforms(b)
            for i in range(3):
                self.assertAlmostEqual(after[1].translation[i],updated.translation[i],places=12)
                for j in range(3):self.assertAlmostEqual(after[1].rotation[i][j],updated.rotation[i][j],places=14)
            for layer in (0,2,3,4,5,6):self.assertEqual(before[layer],after[layer])
            p=(2.,-3.,.5)
            for x,y in zip(updated.inverse().apply(updated.apply(p)),p):self.assertAlmostEqual(x,y,places=12)
            ring=ET.parse(b).find("./detectors/detector[@name='SiMAPS']/layer[@id='1']/ring")
            self.assertFalse(any(k in ring.attrib for k in ('global_rx','global_ry','global_rz')))

    def test_rx_scope_does_not_allow_other_rotations_or_centers(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=[]
            for name,kwargs in [('rx',{'rx_rad':{1:.03}}),('ry',{'ry_rad':{1:.03}}),('wrong_layer',{'rx_rad':{2:.03}}),('moved',{'rx_rad':{1:.03},'z_shifts':{1:2.}})]:
                path=Path(tmp)/(name+'.xml');write_shifted_xml(DEFAULT_NOMINAL,path,{},**kwargs);paths.append(path)
            verify_scope(DEFAULT_NOMINAL,paths[0],(1,),('rx',))
            for path in paths[1:]:
                with self.assertRaises(ValueError):verify_scope(DEFAULT_NOMINAL,path,(1,),('rx',))
            with self.assertRaises(ValueError):layers_for('l1_l2_ry')
            with self.assertRaises(ValueError):layers_for('l0_six_dof')

    def test_incomplete_and_mixed_rotation_states_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.xml';write_shifted_xml(DEFAULT_NOMINAL,a,{},rotations={1:axis_rotation('x',.02)})
            text=a.read_text();a.write_text(text.replace('global_r00="1"','global_r00="1" global_rx="0.01"'))
            with self.assertRaises(ValueError):placement_transforms(a)

    def test_combined_modes_remain_disabled_after_failed_scientific_closure(self):
        from calibration.settings import load
        from research_common import REPO
        for mode in ('l1_rx_ry','l1_l2_rx_ry'):
            with self.assertRaisesRegex(ValueError,'Combined Rx/Ry disabled'):layers_for(mode)
            with self.assertRaisesRegex(ValueError,'Combined Rx/Ry disabled'):load(REPO/'calibration/config'/f'{mode}_demo.json')

    def test_controller_refuses_unproved_tilts(self):
        from calibration.settings import load
        from research_common import REPO
        with tempfile.TemporaryDirectory() as tmp:
            config=json.loads((REPO/'calibration/config/l1_rx_demo.json').read_text());config['calibration'].pop('tilt_derivative_report')
            p=Path(tmp)/'config.json';p.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'explicit tilt_derivative_report'):load(p)


if __name__=='__main__':unittest.main()
