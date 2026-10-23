"""Geometry composition and scope tests using synthetic parameter files, not physics fits."""
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from correction.correct_geometry import correct
from correction.scope import verify_scope,layers_for
from geometry.prepare import write_shifted_xml
from geometry.placements import geometry,placement_transforms
from research_common import REPO,done


class CorrectionTests(unittest.TestCase):
    def test_simultaneous_composition_and_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp);(run/'step1').mkdir();(run/'step4').mkdir()
            nominal=run/'step1/nominal.xml'
            shutil.copyfile(REPO/'geometry/nominal/seven_layer_telescope.xml',nominal)
            (run/'step1/geometry_config.json').write_text(json.dumps({'detector':'SiMAPS','global_x_shifts_mm':{'1':.15,'2':.2}}))
            done(run/'step1')
            (run/'step4/millepede.res').write_text('1001 -0.001\n1002 0.002\n')
            done(run/'step4')
            base=run/'base.xml';write_shifted_xml(nominal,base,{1:.15,2:.2})
            with self.assertRaises(ValueError):verify_scope(nominal,base,(2,))
            correct(SimpleNamespace(run_dir=run,mode='l1_l2_x',base_geometry=base))
            positions=geometry(run/'step5/corrected.xml')
            self.assertAlmostEqual(positions[1][0],.151)
            self.assertAlmostEqual(positions[2][0],.198)
            for layer in (0,3,4,5,6):self.assertEqual(positions[layer],geometry(nominal)[layer])
            bad=run/'bad.xml';write_shifted_xml(nominal,bad,{3:.1})
            with self.assertRaises(ValueError):verify_scope(nominal,bad,(1,2))
            with self.assertRaises(ValueError):layers_for('all_dof')

    def test_xy_survey_composition_preserves_fixed_anchors(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp);(run/'step1').mkdir();(run/'step4').mkdir()
            nominal=run/'step1/nominal.xml'
            shutil.copyfile(REPO/'geometry/nominal/seven_layer_telescope.xml',nominal)
            (run/'step1/geometry_config.json').write_text(json.dumps({'detector':'SiMAPS','global_x_shifts_mm':{'1':0,'2':0},'global_y_shifts_mm':{'1':0,'2':0}}))
            done(run/'step1')
            (run/'step4/millepede.res').write_text('1001 -0.11\n2001 0.09\n1002 -0.22\n2002 -0.08\n')
            done(run/'step4')
            survey=run/'survey.xml';write_shifted_xml(nominal,survey,{0:.02,1:.04,2:-.02},{0:.03,1:-.03,2:.01})
            before=placement_transforms(survey)
            correct(SimpleNamespace(run_dir=run,mode='l1_l2_xy',base_geometry=survey,reference_geometry=survey))
            after=placement_transforms(run/'step5/corrected.xml')
            for layer,xy in ((1,(.15,-.12)),(2,(.2,.09))):
                for index in range(2):self.assertAlmostEqual(after[layer].translation[index],xy[index])
            for layer in (0,3,4,5,6):self.assertEqual(after[layer],before[layer])

    def test_xy_rz_composes_about_current_centers(self):
        import math
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp);(run/'step1').mkdir();(run/'step4').mkdir()
            nominal=run/'step1/nominal.xml';shutil.copyfile(REPO/'geometry/nominal/seven_layer_telescope.xml',nominal)
            (run/'step1/geometry_config.json').write_text(json.dumps({'detector':'SiMAPS','global_x_shifts_mm':{},'global_y_shifts_mm':{},'global_rz_rad':{'1':0.,'2':0.}}))
            done(run/'step1')
            (run/'step4/millepede.res').write_text('1001 0.001\n2001 -0.002\n3001 0.003\n1002 -0.003\n2002 0.004\n3002 -0.004\n')
            done(run/'step4')
            survey=run/'survey.xml';write_shifted_xml(nominal,survey,{0:.02,1:.15,2:.2},{0:.03,1:-.12,2:.09},rz_rad={1:.02,2:-.03})
            before=placement_transforms(survey)
            correct(SimpleNamespace(run_dir=run,mode='l1_l2_xy_rz',base_geometry=survey,reference_geometry=survey))
            after=placement_transforms(run/'step5/corrected.xml')
            for l,expected,angle in [(1,(.149,-.118,50.),.017),(2,(.203,.086,100.),-.026)]:
                for actual,target in zip(after[l].translation,expected):self.assertAlmostEqual(actual,target)
                self.assertAlmostEqual(math.atan2(after[l].rotation[1][0],after[l].rotation[0][0]),angle)
            for l in (0,3,4,5,6):self.assertEqual(after[l],before[l])


if __name__=='__main__':unittest.main()
