"""Independent stage; invoke with python3 -m validation.validate."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from correction.correct_geometry import ensure_correction_supported
from research_common import REPO, cli_parser, run, require, stage, done, execute, write_json

def validate(a):
    from validation.metrics import calculate
    for s in ['step2','step3','step4','step6','step5']:require(a.run_dir,s)
    ensure_correction_supported(a.run_dir,a.correction_mode)
    p=stage(a.run_dir,'step7')
    before=json.loads((a.run_dir/'step3/complete.json').read_text());after=json.loads((a.run_dir/'step6/complete.json').read_text())
    if before['input_sha256']!=after['input_sha256'] or before['plugin_sha256']!=after['plugin_sha256'] or before['config_sha256']!=after['config_sha256']:
        raise RuntimeError('Before/after inputs or plugin differ')
    inputs=SimpleNamespace(nominal=a.run_dir/'step1/nominal.xml', misaligned=a.run_dir/'step1/misaligned.xml',
                           corrected=a.run_dir/'step5/corrected.xml', before=a.run_dir/'step3/reco.root',
                           after=a.run_dir/'step6/reco.root', pede=a.run_dir/'step4/millepede.res', reference=a.reference, correction_mode=a.correction_mode, simulation=a.run_dir/'step2/events.edm4hep.root')
    summary=calculate(inputs)
    write_json(p/'summary.json',summary)
    cmd=[sys.executable,'-m','visualization.closure',
         '--nominal',inputs.nominal,'--misaligned',inputs.misaligned,'--corrected',inputs.corrected,
         '--summary',p/'summary.json','--outdir',p/'plots']
    execute(cmd,p,cwd=REPO)
    for output in (p/'plots').iterdir(): output.rename(p/output.name)
    (p/'plots').rmdir()
    if summary.get('reference_passed') is False: raise RuntimeError('Reference comparison FAILED; inspect retained summary')
    done(p,summary=str(p/'summary.json'))


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--correction-mode',choices=['l2_x','l1_l2_x','l1_l2_xy','l1_rz','l1_l2_rz','l1_l2_xy_rz'],default='l2_x')
    parser.add_argument('--reference', type=Path, help='Reference metrics to compare with saved tolerances')
    run(validate, parser)
