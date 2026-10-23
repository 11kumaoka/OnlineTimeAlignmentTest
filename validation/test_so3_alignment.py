"""Coupled correction scope and evidence guards; no statistical closure claim."""
import json
import tempfile
import unittest
from pathlib import Path
from correction.scope import SO3_MODES,layers_for,axes_for,parameter_spec,verify_scope,verify_survey
from calibration.settings import load
from geometry.prepare import DEFAULT_NOMINAL,write_shifted_xml
from geometry.transforms import rotation_exp
from research_common import REPO


class CoupledTests(unittest.TestCase):
    def test_explicit_scopes_and_signs(self):
        for mode in SO3_MODES:
            self.assertEqual(layers_for(mode),{'l3_six_dof':(3,),'l1_l2_l3_six_dof':(1,2,3)}.get(mode,(1,2) if mode.startswith('l1_l2_') else (1,)))
            spec={a:(label,sign) for a,label,sign in parameter_spec(mode)}
            self.assertEqual(spec['rz'],(3000,-1));self.assertEqual(spec['rx'],(5000,1));self.assertEqual(spec['ry'],(6000,1))
            self.assertEqual(len(spec),6 if mode.endswith('six_dof') else 3)

    def test_centers_and_unselected_sensors_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.xml'
            write_shifted_xml(DEFAULT_NOMINAL,p,{},rotations={1:rotation_exp((.03,-.025,.017))})
            verify_scope(DEFAULT_NOMINAL,p,(1,),axes_for('l1_rotations'))
            verify_survey(DEFAULT_NOMINAL,p,orientation_layers=(1,))
            p=Path(tmp)/'b.xml'
            write_shifted_xml(DEFAULT_NOMINAL,p,{1:.1},{1:.2},z_shifts={1:.5},rotations={1:rotation_exp((.03,-.025,.017))})
            with self.assertRaises(ValueError):verify_scope(DEFAULT_NOMINAL,p,(1,),axes_for('l1_rotations'))
            verify_scope(DEFAULT_NOMINAL,p,(1,),axes_for('l1_six_dof'))
            with self.assertRaises(ValueError):verify_scope(DEFAULT_NOMINAL,p,(2,),axes_for('l1_l2_six_dof'))

    def test_l3_steering_matches_scope_and_reference_constraints(self):
        from correction.scope import selected_labels,fixed_layers_for
        for mode in ('l3_six_dof','l1_l2_l3_six_dof'):
            entries=[]
            for line in (REPO/f'alignment/pede_{mode}.txt').read_text().splitlines():
                fields=line.split()
                if len(fields)==3 and fields[0].isdigit():entries.append((int(fields[0]),float(fields[2])))
            self.assertEqual(len(entries),len(dict(entries)))
            free={label for label,presigma in entries if presigma>0}
            self.assertEqual(free,set(selected_labels(mode)))
            self.assertTrue({0,4}<=set(fixed_layers_for(mode)))
            self.assertFalse(any(label%1000 in fixed_layers_for(mode) for label in free))
        self.assertEqual(len(selected_labels('l1_l2_l3_six_dof')),18)
        self.assertEqual(set(selected_labels('l3_six_dof')),{1003,2003,3003,4003,5003,6003})

    def test_three_layer_correction_composes_current_geometry_and_preserves_anchors(self):
        import shutil
        from types import SimpleNamespace
        from geometry.placements import placement_transforms
        from geometry.transforms import orientation_distance
        from correction.correct_geometry import correct
        from research_common import done
        for mode in ('l3_six_dof','l1_l2_l3_six_dof'):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp);base=root/'survey.xml'
                write_shifted_xml(DEFAULT_NOMINAL,base,{l:.01*l for l in layers_for(mode)},
                    {l:-.02*l for l in layers_for(mode)},z_shifts={l:.05*l for l in layers_for(mode)},
                    rotations={l:rotation_exp((.01,-.02,.005)) for l in layers_for(mode)})
                survey=base
                for iteration in range(2):
                    run=root/str(iteration);(run/'step1').mkdir(parents=True);(run/'step4').mkdir()
                    shutil.copyfile(DEFAULT_NOMINAL,run/'step1/nominal.xml')
                    (run/'step1/geometry_config.json').write_text('{"detector":"SiMAPS","global_x_shifts_mm":{}}')
                    done(run/'step1')
                    params={family+l:value for l in layers_for(mode) for family,value in
                        ((1000,.001),(2000,-.002),(4000,.003),(5000,.004),(6000,-.005),(3000,.006))}
                    (run/'step4/millepede.res').write_text(''.join(f'{k} {v}\n' for k,v in params.items()));done(run/'step4')
                    before=placement_transforms(base)
                    correct(SimpleNamespace(run_dir=run,mode=mode,base_geometry=base,reference_geometry=survey))
                    base=run/'step5/corrected.xml';after=placement_transforms(base)
                    for l in range(7):
                        if l not in layers_for(mode):self.assertEqual(after[l],before[l]);continue
                        expected=before[l].updated(rotation=rotation_exp((.004,-.005,-.006)),
                            translation=(-.001,.002,.003),pivot=before[l].translation)
                        self.assertLess(orientation_distance(expected.rotation,after[l].rotation),1e-14)
                        for a,b in zip(expected.translation,after[l].translation):self.assertAlmostEqual(a,b,places=12)
                    verify_scope(survey,base,layers_for(mode),axes_for(mode))

    def test_missing_proof_refused_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in SO3_MODES:
                config=json.loads((REPO/f'calibration/config/{mode}_demo.json').read_text())
                config['calibration'].pop('tilt_derivative_report')
                path=Path(tmp)/(mode+'.json');path.write_text(json.dumps(config))
                with self.assertRaisesRegex(ValueError,'explicit tilt_derivative_report'):load(path)
            mode='l1_l2_six_dof';config=json.loads((REPO/f'calibration/config/{mode}_demo.json').read_text())
            config['calibration'].pop('tilt_max_nominal_sigma_mm');path=Path(tmp)/'missing.json';path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'translation information bound'):load(path)


if __name__=='__main__':unittest.main()
