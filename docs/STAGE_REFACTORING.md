# Independent Stages and Geometry Scenarios

> Historical report of the preceding refactor. Current paths and commands are in
> [TASK_ARCHITECTURE.md](TASK_ARCHITECTURE.md) and [WORKFLOW.md](WORKFLOW.md).

Date: 2026-10-21. Both requested phases are implemented. No commit or push was
performed. The pre-existing uncommitted README link and Millepede integration
document were preserved; their stage references were updated to the new layout.

## Architecture

```text
local_detector_testbench/
  stages/
    __init__.py
    common.py
    geometry.py
    simulation.py
    reconstruction.py
    millepede.py
    correction.py
    validation.py
  scripts/
    prepare_geometry.sh
    simulate.sh
    reconstruct.sh
    align.sh
    correct_geometry.sh
    reconstruct_corrected.sh
    validate.sh
    run_closure.sh
```

The old `scripts/workflow.py` was removed after its implementations were extracted.
There is no replacement central dispatcher or compatibility implementation.
Each wrapper runs exactly one module using `python3 -m`; the optional Closure
runner contains only argument routing and sequential wrapper calls.

| Module | Responsibility |
|---|---|
| `common.py` | Repository/result paths, shared CLI safety, checksums, config snapshots, execution records, completion markers, dependency-prefix checks. No detector physics or XML placement model. |
| `geometry.py` | Scenario schema/layer validation, nominal copy, Global X Simulation placement edits, DD4hep conversion, exported-placement checks. Its single-layer placement helper is also used by the existing correction. |
| `simulation.py` | Saved beam settings → DDSim, or reuse an existing Simulation ROOT input. |
| `reconstruction.py` | Saved reconstruction settings → EICrecon, before/after Geometry choice, writer/event counter checks. |
| `millepede.py` | Existing steering template expansion, independent pede command/status, parameter reading. |
| `correction.py` | Check that L2-only correction is supported; preserve the existing label-1002 sign conversion and nominal-based L2 update. |
| `validation.py` | Require complete compatible inputs, reject unsupported full Closure, invoke existing ROOT validation. |

`reconstruct_corrected.sh` reuses `reconstruction.py --after`; there is no copied
reconstruction implementation. Inter-module imports expose only reusable helpers
(e.g. parameter reading and XML placement); importing a module does not execute a
stage. Every module has its own guarded CLI entry point.

## Configurations and stage contracts

- Beam cases retain event count, particle/gun settings, reconstruction settings,
  backend, and nominal layout reference. Both existing electron/muon filenames
  remain usable. Only their former `alignment_layer` and `injected_x_mm` fields
  were removed; all other parsed settings are unchanged.
- Geometry scenario JSON defines numerical SiMAPS Global X displacements. It is
  selected only during preparation via `--geometry-config`, independently of
  `--case`. The default is the existing L2 +200 μm condition.
- The Pede template remains unchanged. It still defines X/Y parameters on L0–L4,
  fixes L0/L4, and varies L1–L3. Scenarios do not redefine the fit model.

Each result retains `geometry/`, `simulation/`, `before/`, `alignment/`,
`correction/`, `after/`, and `validation/` as stages are explicitly executed.
Each subprocess retains `command.json`, `stdout.log`, and `exit.json`; stages
retain `complete.json`. Geometry's nominal/misaligned conversion records remain
in their own QA directories. Reusing a Simulation writes source/hash metadata and
a link, not a fictitious DDSim command record.

New Geometry outputs include `geometry/geometry_config.json` and
`geometry/placement_check.json`. Completion hashes now cover JSON outputs
uniformly, including scenario snapshots and placement verification. Existing
completed results retain their original markers and are still readable; they
are not rewritten. Minimal support for their original case-based L2 metadata
allows correction capability checks on previously prepared results.

Individual CLIs accept only their own options. An existing stage is rejected
before overwriting output. The Closure runner requires a new result root and
preflights correction support after preparation, before launching Simulation.

## Manual commands

Run from the repository root. The container launcher provides the EIC runtime;
inside an already configured environment the wrapper commands work directly.
Use a new result directory. `--run-dir` remains the previously supported argument
alias; no old filesystem layout or workflow dispatcher is restored.

```bash
bash environment/run.sh bash local_detector_testbench/scripts/prepare_geometry.sh \
  --result-dir results/manual_001 \
  --case examples/seven_layer_telescope/cases/electron_1GeV_L2_x200um.json \
  --geometry-config examples/seven_layer_telescope/geometry/scenarios/L2_x200um.json
bash environment/run.sh bash local_detector_testbench/scripts/simulate.sh \
  --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/reconstruct.sh \
  --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/align.sh \
  --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/correct_geometry.sh \
  --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/reconstruct_corrected.sh \
  --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/validate.sh \
  --result-dir results/manual_001
```

Stop after any command and inspect its stage. To reuse existing Simulation, add
`--sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root`
only to `simulate.sh`. To choose a Plugin build, pass `--build-dir` to each of the
two reconstruction wrappers. Reference comparison belongs to `validate.sh` via
`--reference validation/reference_metrics.json` and should only be applied to the
matching historical sample. All stages can be inspected with `--help` without
loading the fitting Plugin or running physics.

## Scenario files

[`L2_x200um.json`](../geometry/scenarios/L2_x200um.json):

```json
{"detector":"SiMAPS","global_x_shifts_mm":{"2":0.2}}
```

[`L1_x100um_L2_x200um.json`](../geometry/scenarios/L1_x100um_L2_x200um.json):

```json
{"detector":"SiMAPS","global_x_shifts_mm":{"1":0.1,"2":0.2}}
```

Unspecified layers remain nominal. Only canonical SiMAPS layer IDs 0–4, finite
numeric Global X shifts, and the two declared schema fields are supported.
Other detector/displacement types, invalid layers, booleans, non-finite values,
and unsupported numerical precision are rejected before creating a stage.
The XML retains the current sign convention, `Global X = −ring r`, and eight
decimal places in mm. Nominal Geometry is never changed.

## Verification order and results

All new outputs are under `results/stage_refactor_20261021_01/`. A backup of
maintained files, initial diffs/status, and SHA inventory was taken before editing.

### Phase A: extraction without changing physics

AST comparison confirmed 18 extracted functions were unchanged before scenarios
were introduced. Shared CLI parsing and shell-only orchestration replaced the
old central dispatcher. A clean Plugin build and both original Closure tests
completed with exit code 0:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env TESTBENCH_BUILD_DIR=/work/build/stage_refactor_20261021_01 bash environment/build.sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash local_detector_testbench/scripts/prepare_geometry.sh \
  --result-dir results/stage_refactor_20261021_01/phase_a_geometry_only
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash local_detector_testbench/scripts/run_closure.sh \
  --result-dir results/stage_refactor_20261021_01/phase_a_regression \
  --build-dir build/stage_refactor_20261021_01 \
  --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root \
  --reference validation/reference_metrics.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash local_detector_testbench/scripts/run_closure.sh \
  --result-dir results/stage_refactor_20261021_01/phase_a_fresh \
  --build-dir build/stage_refactor_20261021_01
```

The build used a new, previously absent directory. The isolated preparation
produced only `geometry/`. The fresh test actually ran DDSim, reconstruction,
Mille writing, pede, correction, corrected reconstruction, and ROOT validation.

| Metric | Phase A historical 100-event input | Phase A fresh 100-event electron input |
|---|---:|---:|
| Tracks before / after | 99 / 99 | 98 / 98 |
| L2 correction [μm] | +198.75 | +201.13 |
| L2 Rec−Sim [μm] | −199.571376 → −0.821365 | −198.922108 → +2.207910 |
| Σχ² / Σstored ACTS nDoF | 45.592235 → 1.981040 | 33.273539 → 1.244249 |

Both ROOT output checks passed. Only after these successes was Phase B implemented.

### Phase B: new Geometry only, plus final L2 compatibility check

The two-layer command actually executed was:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash local_detector_testbench/scripts/prepare_geometry.sh \
  --result-dir results/stage_refactor_20261021_01/two_layer_geometry_only \
  --geometry-config examples/seven_layer_telescope/geometry/scenarios/L1_x100um_L2_x200um.json
```

DD4hep exported both nominal and shifted GDML successfully. The verifier inspected
actual module positions in that export, not just the requested JSON or XML sign.
The parent hierarchy is required to be origin-centered and unrotated.

| Layer | Nominal Global X [mm] | Shifted Global X [mm] | Z before / after [mm] |
|---|---:|---:|---:|
| L0 | 0 | 0 | 0 / 0 |
| L1 | 0 | +0.100 | 50 / 50 |
| L2 | 0 | +0.200 | 100 / 100 |
| L3 | 0 | 0 | 150 / 150 |
| L4 | 0 | 0 | 200 / 200 |
| MPGD L5 | 0 | 0 | 250 / 250 |
| AC-LGAD L6 | 0 | 0 | 300 / 300 |

All Y positions remain zero. XML comparison confirmed that only the L1/L2 ring
placements differ anywhere in the two-layer XML. The result root contains only
`geometry/`, including case/scenario snapshots, nominal/misaligned XML, QA GDML,
placement check, and completion marker. No two-layer Simulation, reconstruction,
Mille Binary, pede fit, Geometry Correction, or full Closure was run.

The actual two-layer result was passed to `correct_geometry.sh --check-only`:
it failed explicitly with the unsupported multi-layer message and left every
Geometry output unchanged. The same guard is enforced before actual correction
and full validation. No partial L2-only result is presented as two-layer Closure.

A final **L2-only**, existing-input regression also completed after the new schema
and guards were added:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash local_detector_testbench/scripts/run_closure.sh \
  --result-dir results/stage_refactor_20261021_01/phase_b_l2_regression \
  --geometry-config examples/seven_layer_telescope/geometry/scenarios/L2_x200um.json \
  --build-dir build/stage_refactor_20261021_01 \
  --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root \
  --reference validation/reference_metrics.json
```

It reproduced the 99-track metrics in the table and passed ROOT checks. Its
misaligned and corrected XML files match Phase A byte-for-byte. The C++ source,
nominal Geometry, Pede template, ACTS electron hypothesis, and writer/model logic
were not modified. Beam/reconstruction case values were compared with the initial
snapshot after removing only the two deliberately migrated misalignment fields.

### Other checks

- All independent module/wrapper help commands and Python/Shell syntax passed.
- Three ROOT checks passed (Phase A regression/fresh and final L2 regression).
- Existing baseline/data preservation checks passed; old results were not overwritten.
- Safety checks cover overwrite refusal, missing prerequisites, legacy-field
  conflicts, invalid scenario schemas/layers/types, and unsupported multi-layer
  correction. Synthetic completion markers in safety tests did not run physics.
- Existing prepared L2 results remain readable. The repository's previous
  uncommitted technical document remains present; no Git index change, commit,
  or push was performed.

## Limitations

The Geometry verifier is specific to the current seven-plane, one-module-per-layer,
origin-centered DD4hep hierarchy. It is not a generic geometry alignment engine.
SiMAPS Global Y/Z shifts and rotations are unsupported. The solver still fits its
existing L1–L3 X/Y parameters; only L2 Global X Geometry Correction is implemented.
A multi-layer scenario cannot be reported as a completed Closure by this workflow.

The muon settings are preserved and schema-compatible, but no new muon Simulation
or fit was performed. Imported Simulation data retain their actual generation
conditions; event/collection checks do not independently prove that an external
ROOT file matches a chosen Geometry scenario. Interactive TBrowser operation was
not tested. No material, fitter, uncertainty, derivative, or constraint extension
was made.

## Modified and added files

The list includes the intentionally updated, previously uncommitted integration
document. `scripts/workflow.py` is the only removed implementation file; its
pre-edit content is preserved in the task backup under the result directory.

- `README.md`
- `docs/EICRECON_MILLEPEDE_INTEGRATION.md`
- `docs/STAGE_REFACTORING.md`
- `docs/WORKFLOW.md`
- `examples/seven_layer_telescope/cases/electron_1GeV_L2_x200um.json`
- `examples/seven_layer_telescope/cases/muon_5GeV.json`
- `examples/seven_layer_telescope/geometry/scenarios/L1_x100um_L2_x200um.json`
- `examples/seven_layer_telescope/geometry/scenarios/L2_x200um.json`
- `local_detector_testbench/scripts/align.sh`
- `local_detector_testbench/scripts/correct_geometry.sh`
- `local_detector_testbench/scripts/prepare_geometry.sh`
- `local_detector_testbench/scripts/reconstruct.sh`
- `local_detector_testbench/scripts/reconstruct_corrected.sh`
- `local_detector_testbench/scripts/run_closure.sh`
- `local_detector_testbench/scripts/simulate.sh`
- `local_detector_testbench/scripts/validate.sh`
- `local_detector_testbench/scripts/workflow.py`
- `local_detector_testbench/stages/__init__.py`
- `local_detector_testbench/stages/common.py`
- `local_detector_testbench/stages/correction.py`
- `local_detector_testbench/stages/geometry.py`
- `local_detector_testbench/stages/millepede.py`
- `local_detector_testbench/stages/reconstruction.py`
- `local_detector_testbench/stages/simulation.py`
- `local_detector_testbench/stages/validation.py`
- `local_detector_testbench/visualization/README.md`
- `validation/README.md`
- `validation/check_safety.py`
- `validation/run_regression.sh`
