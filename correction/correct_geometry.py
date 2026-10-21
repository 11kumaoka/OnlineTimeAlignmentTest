"""Independent stage; invoke with python3 -m correction.correct_geometry."""
import json
from research_common import cli_parser, run, require, stage, done
from geometry.prepare import modified_xml
from alignment.align import read_pede


def ensure_l2_correction_supported(result):
    require(result, 'step1')
    scenario = result/'step1/geometry_config.json'
    if scenario.is_file():
        config = json.loads(scenario.read_text())
        if config.get('detector') != 'SiMAPS':
            raise ValueError('Only SiMAPS L2 Global X correction is supported')
        shifts = config['global_x_shifts_mm']
    else:
        raise ValueError('Missing step1 Geometry scenario')
    if any(int(layer) != 2 and float(value) != 0.0 for layer, value in shifts.items()):
        raise ValueError('Multi-layer Geometry Correction and full Closure are unsupported: only SiMAPS L2 Global X is implemented')


def correct(a):
    if getattr(a, "check_only", False):
        ensure_l2_correction_supported(a.run_dir)
        return
    require(a.run_dir,'step4')
    ensure_l2_correction_supported(a.run_dir)
    p=stage(a.run_dir,'step5')
    value=-read_pede(a.run_dir/'step4/millepede.res')[1002]
    modified_xml(a.run_dir/'step1/nominal.xml',p/'corrected.xml',2,value)
    done(p,layer=2,axis='global_x',applied_mm=value,measurement_bias_mm=-value,
         note='Apply only L2 X, matching the saved physical closure; other fitted components are not applied')


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--check-only', action='store_true', help='Check Geometry support without applying a correction or requiring alignment')
    run(correct, parser)
