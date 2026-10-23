> Historical baseline before the RawHit execution split. Current commands and
> architecture are in [WORKFLOW.md](WORKFLOW.md) and [RAWHIT_BOUNDARY.md](RAWHIT_BOUNDARY.md).

# Top-Level Research Task Architecture

Migration report, 2026-10-21. Commit/push statements below describe that
pre-publication task. The subsequent publication audit is recorded in
[FINAL_ARCHITECTURE_AUDIT.md](FINAL_ARCHITECTURE_AUDIT.md).

This architecture supersedes the layout in
[STAGE_REFACTORING.md](STAGE_REFACTORING.md). No commit or push was performed.

## Ownership

```text
/work/
├── localDetEICrecon/
│   ├── algorithms/                 existing Digitization and Track Fitting C++
│   ├── factories/                  existing JANA factories
│   ├── plugins/                    BeamTestReco registration
│   ├── processors/                 event counters and BeamTestMilleProcessor
│   ├── alignment/src/              in-process BeamTestMilleWriter
│   ├── CMakeLists.txt
│   ├── README.md
│   └── build.sh
├── geometry/
│   ├── nominal/seven_layer_telescope.xml
│   ├── scenarios/{L2_x200um,L1_x100um_L2_x200um}.json
│   ├── prepare.py                  XML generation and DD4hep GDML verification
│   ├── placements.py               supported compact-XML placement reader
│   └── prepare_geometry.sh
├── simulation/
│   ├── configs/{electron_1GeV,muon_5GeV}.json
│   ├── simulate.py
│   └── simulate.sh
├── reconstruction/
│   ├── configs/{electron_1GeV,muon_5GeV}.json
│   ├── reconstruct.py
│   ├── reconstruct.sh
│   └── reconstruct_corrected.sh
├── alignment/{pede_template.txt,align.py,align.sh}
├── correction/{correct_geometry.py,correct_geometry.sh}
├── validation/
│   ├── validate.py                 provenance checks and step7 execution
│   ├── metrics.py                  unchanged residual/numerical calculations
│   ├── validate.sh
│   ├── run_closure.sh              optional sequential shell calls only
│   ├── run_regression.sh
│   └── reference metrics, preservation manifests and check scripts
├── visualization/{closure.py,browse.C,README.md}
├── environment/                    Docker, dependencies, runtime/build support
├── research_common.py              shared infrastructure only
├── docs/
├── result/                         new generated outputs, ignored by Git
├── results/                        untouched legacy outputs, ignored by Git
├── build/                          generated Plugin builds, ignored by Git
├── external/                       existing dependencies, ignored by Git
└── README.md
```

Python task packages also have small `__init__.py` markers. No Python workflow,
Geometry Preparation, external solver, correction, validation, or plotting code
remains inside `localDetEICrecon`. The former nested `local_eicrecon` level was
flattened. All C++ and header files are byte-identical to the pre-migration
snapshot, including the electron hypothesis and Mille Writer derivatives. Only
CMake source/include/dependency paths were adjusted.

The writer runs **inside EICrecon** and produces official Mille Binary records.
The solver runs **outside EICrecon** through `alignment/align.py`. No upstream
EICrecon, Mille, or Millepede-II source or installation was modified.

## Stage implementations and configuration

| Step | Implementation | Configuration and dependency |
|---|---|---|
| 1 | `geometry/prepare.py` | `--nominal geometry/nominal/seven_layer_telescope.xml`; `--geometry-config geometry/scenarios/L2_x200um.json` |
| 2 | `simulation/simulate.py` | step1; `--config simulation/configs/electron_1GeV.json`; optional `--sim-input ROOT` |
| 3 | `reconstruction/reconstruct.py` | steps1/2; `--config reconstruction/configs/electron_1GeV.json`; `--build-dir BUILD` |
| 4 | `alignment/align.py` | step3; `--steering alignment/pede_template.txt` |
| 5 | `correction/correct_geometry.py` | steps1/4; fixed existing L2 Global X algorithm |
| 6 | `reconstruction/reconstruct.py --after` | steps1/2/3/5; saved step3 config and same Plugin |
| 7 | `validation/validate.py`, `validation/metrics.py` | steps1–6; optional `--reference validation/reference_metrics.json` |

`visualization/closure.py` consumes a saved numerical summary, reads Geometry for
its schematic, and draws ROOT objects. PODIO extraction and numerical comparisons
are now under validation; the extracted functions were checked by Python AST
comparison against the previous implementation. There is no second numerical
implementation in the renderer.

`research_common.py` provides paths, CLI checks, exclusive output directories,
SHA-256 validation, execution records, and completion markers. It contains no
placement, fitting, derivative, or solver model. Each task has its own guarded
Python CLI and shell entry point; importing helpers does not execute a stage.

The former combined electron/muon cases were split without changing their parsed
values: event count and beam settings are under Simulation; PDG, q/p, MPGD and
AC-LGAD flags are under Reconstruction. Geometry no longer snapshots or selects
a particle case. The same source-position, energy, angular ranges, beam widths,
seed, and hypotheses are preserved. A muon study must select both muon configs.

## Seven independently executed commands

Run from the repository root. These examples require a new output name and a
Plugin built with `bash environment/run.sh bash localDetEICrecon/build.sh`:

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/manual_001 --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh bash simulation/simulate.sh --result-dir result/manual_001 --config simulation/configs/electron_1GeV.json
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/manual_001 --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/manual_001 --steering alignment/pede_template.txt
bash environment/run.sh bash correction/correct_geometry.sh --result-dir result/manual_001
bash environment/run.sh bash reconstruction/reconstruct_corrected.sh --result-dir result/manual_001
bash environment/run.sh bash validation/validate.sh --result-dir result/manual_001
```

Each command stops after its selected stage. The `--result-dir` convention is
consistent; `--run-dir` remains a spelling alias, not an old-layout interface.
The optional shell-only Closure convenience runner is not required for these
commands and contains no separate processing implementation.

For reuse, add `--sim-input PATH` to step2. Config snapshots describe requested
processing settings, not necessarily an imported file's actual generation
conditions. A checksum and hit/event checks cannot prove external Geometry
provenance. Step6 defaults to the immutable step3 config; step7 verifies matching
Simulation, Plugin, and config hashes.

## Outputs and records

For `--result-dir result/manual_001`:

| Directory | Principal outputs |
|---|---|
| `step1/` | `nominal.xml`, `misaligned.xml`, `geometry_config.json`, `placement_check.json`, `nominal_qa/geometry.gdml`, `misaligned_qa/geometry.gdml` |
| `step2/` | `events.edm4hep.root`, Simulation `config.json` |
| `step3/` | `reco.root`, `mille.dat`, Reconstruction `config.json` |
| `step4/` | `steering_template.txt`, `pede.txt`, `millepede.res`, `millepede.log`, `millepede.his`, `millepede.end` |
| `step5/` | `corrected.xml` |
| `step6/` | `reco.root`, `mille.dat`, Reconstruction `config.json` |
| `step7/` | `summary.json`, `alignment.root` |

Each completed step has `complete.json`. Executed subprocesses have
`command.json`, `stdout.log`, and `exit.json`; Geometry conversion records are
inside each QA directory. Reused Simulation and pure XML correction have no
subprocess to record. Completion markers hash all regular output files,
including nested QA outputs. Required inputs are verified before processing.
Existing or partially written steps are refused, and failures are retained.

Both `result/` and legacy `results/` are ignored. The old data directory and
its historical paths, command records, and symlinks were not edited. Preservation
manifest edits only retarget the moved nominal XML and validated fitter path;
the expected SHA-256 values are unchanged. The persistent external archive was
not touched.

## Executed validation

All new task artifacts are under `result/architecture_20261021_01/`. Before moving
files, the maintained tree (including prior uncommitted changes), Git status,
staged/unstaged diffs, and a layout inventory were saved. The archive is
`maintained_before.tar.gz`; `protected_before.json` inventories existing results
and external dependencies. Obsolete package bytecode was retained in the task
artifacts rather than deleted. No destructive directory cleanup was performed.

### Clean Plugin build

Actually executed, exit 0, in a new build directory:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/architecture_20261021_01 bash localDetEICrecon/build.sh
```

The output is `build/architecture_20261021_01/BeamTestReco.so`; full log:
`result/architecture_20261021_01/build.log`.

### Geometry-only checks

Both commands completed with exit 0:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/architecture_20261021_01/l2_regression
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/architecture_20261021_01/two_layer_geometry_only --geometry-config geometry/scenarios/L1_x100um_L2_x200um.json
```

The two-layer result contains **only step1**. Actual exported DD4hep placements:

| Layer | Nominal X [mm] | Shifted X [mm] | Unchanged Z [mm] |
|---|---:|---:|---:|
| SiMAPS L0 | 0 | 0 | 0 |
| SiMAPS L1 | 0 | +0.100 | 50 |
| SiMAPS L2 | 0 | +0.200 | 100 |
| SiMAPS L3 | 0 | 0 | 150 |
| SiMAPS L4 | 0 | 0 | 200 |
| MPGD L5 | 0 | 0 | 250 |
| AC-LGAD L6 | 0 | 0 | 300 |

All Y positions remain zero. Scenario JSONs and nominal Geometry are unchanged
in content. No two-layer Simulation, reconstruction, pede, or Closure was run.

### L2-only regression

The initial independently invoked run reached steps1–6 successfully, but step7
failed because the newly extracted metrics module lacked an `uproot` import.
That import was fixed. The failed result and logs remain at `l2_regression/`;
its step7 is intentionally incomplete and must not be treated as validated.

A full rerun in a **new** directory completed with exit 0:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash validation/run_regression.sh result/architecture_20261021_01/l2_regression_verified build/architecture_20261021_01
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 validation/check_root_outputs.py --result-dir result/architecture_20261021_01/l2_regression_verified
```

| Metric | Before | After |
|---|---:|---:|
| Events | 100 | 100 |
| Accepted tracks | 99 | 99 |
| Pooled L2 Rec−Sim [μm] | −199.571375548 | −0.821364508 |
| Σχ² / Σstored ACTS nDoF | 45.592234848 | 1.981039768 |

Applied L2 correction: **+198.75 μm**. `reference_passed` is true. The entire
summary JSON equals the previous validated regression summary. Before/after
Mille Binaries and misaligned/corrected XML are byte-identical to the preceding
stage-refactor regression. ROOT checks passed: three canvases, at least 20
residual TH1Ds, and Closure graphs.

No new Geant4 events were generated in this task; Simulation reuse was tested.
No new muon fit or interactive TBrowser test was performed.

### Preservation and static checks

- `python3 validation/verify_preservation.py`: PASS, 221 baseline records,
  2046 relocated files, validated electron fitter hash.
- `python3 validation/check_safety.py`: PASS, overwrite refusal, prerequisites,
  tampering, output-root confinement, scenario schema/types, multi-layer guards.
- Python compilation, Shell syntax, and independent wrapper `--help`: PASS.
- Extracted numerical and ROOT-rendering functions match their prior ASTs.
- All C++/header files, nominal XML, and steering template match pre-move bytes.
- Simulation and Reconstruction configs match their original case values.
- All 4161 inventoried pre-existing results/dependency files match original hashes.
- Git index was not changed. No commit or push was performed.

## Limitations

Only the present seven-plane, unrotated, origin-centered hierarchy is verified.
Geometry scenarios support SiMAPS Global X only. Multiple shifts can be prepared,
but full correction/Closure rejects nonzero shifts outside L2. Existing Pede
parameters and fixed endpoints are unchanged; only label 1002 is applied.

The writer/counter contract still requires five 2D SiMAPS measurements (10 scalar
measurements per accepted track). Changing detector inclusion or measurement
model requires separate validation. Single-thread execution, collection names,
writer z reference and selection settings, ACTS manual surfaces, covariance,
material approximations, and uncertainties remain unchanged implementation
assumptions. The preserved standalone C++ writer default mentions
`results/manual/mille.dat`; maintained Reconstruction always overrides it with
`result/<name>/step3|step6/mille.dat`.

The known standard DD4hep-to-ACTS conversion diagnostic remains visible. No
fitter, material, statistical nDoF, derivative, sign, or seed changes were made.
Old CMake trees and old result layouts remain historical artifacts; active code
does not resume them. Reference datasets are local, not part of a Git clone;
see [validation/README.md](../validation/README.md).

## Complete source migration inventory

The table compares the task's starting uncommitted snapshot, not just Git HEAD.
“Moved and edited” covers path/import/layout/config plumbing; physics C++ sources
are unchanged. The prior combined cases were replaced by two independent configs
per particle. The obsolete empty Python package marker was retired after backup.
Generated build/results are excluded from this source table and remain ignored.

| Change | Previous path | Current path |
|---|---|---|
| modified | `README.md` | `README.md` |
| modified | `.gitignore` | `.gitignore` |
| modified | `environment/build.sh` | `environment/build.sh` |
| modified | `environment/root_shell.sh` | `environment/root_shell.sh` |
| modified | `environment/run.sh` | `environment/run.sh` |
| moved unchanged | `local_detector_testbench/alignment/CMakeLists.txt` | `localDetEICrecon/alignment/CMakeLists.txt` |
| moved unchanged | `local_detector_testbench/alignment/src/BeamTestMilleWriter.cc` | `localDetEICrecon/alignment/src/BeamTestMilleWriter.cc` |
| moved unchanged | `local_detector_testbench/alignment/src/BeamTestMilleWriter.h` | `localDetEICrecon/alignment/src/BeamTestMilleWriter.h` |
| moved and edited | `local_detector_testbench/local_eicrecon/CMakeLists.txt` | `localDetEICrecon/CMakeLists.txt` |
| moved and edited | `local_detector_testbench/local_eicrecon/README.md` | `localDetEICrecon/README.md` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/digi/SiliconTrackerDigi.cc` | `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.cc` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/digi/SiliconTrackerDigi.h` | `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/digi/SiliconTrackerDigiConfig.h` | `localDetEICrecon/algorithms/digi/SiliconTrackerDigiConfig.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.cc` | `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.h` | `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/tracking/BeamTestACTSFitterConfig.h` | `localDetEICrecon/algorithms/tracking/BeamTestACTSFitterConfig.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.cc` | `localDetEICrecon/algorithms/tracking/TrackerHitReconstruction.cc` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.h` | `localDetEICrecon/algorithms/tracking/TrackerHitReconstruction.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/algorithms/tracking/TrackerHitReconstructionConfig.h` | `localDetEICrecon/algorithms/tracking/TrackerHitReconstructionConfig.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/factories/digi/SiliconTrackerDigi_factory.h` | `localDetEICrecon/factories/digi/SiliconTrackerDigi_factory.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/factories/tracking/BeamTestACTSFitter_factory.h` | `localDetEICrecon/factories/tracking/BeamTestACTSFitter_factory.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/factories/tracking/TrackerHitReconstructionNoAssoc_factory.h` | `localDetEICrecon/factories/tracking/TrackerHitReconstructionNoAssoc_factory.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/factories/tracking/TrackerHitReconstruction_factory.h` | `localDetEICrecon/factories/tracking/TrackerHitReconstruction_factory.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/plugins/BeamTestReco.cc` | `localDetEICrecon/plugins/BeamTestReco.cc` |
| moved unchanged | `local_detector_testbench/local_eicrecon/processors/BeamTestEventProcessor.cc` | `localDetEICrecon/processors/BeamTestEventProcessor.cc` |
| moved unchanged | `local_detector_testbench/local_eicrecon/processors/BeamTestEventProcessor.h` | `localDetEICrecon/processors/BeamTestEventProcessor.h` |
| moved unchanged | `local_detector_testbench/local_eicrecon/processors/BeamTestMilleProcessor.cc` | `localDetEICrecon/processors/BeamTestMilleProcessor.cc` |
| moved unchanged | `local_detector_testbench/local_eicrecon/processors/BeamTestMilleProcessor.h` | `localDetEICrecon/processors/BeamTestMilleProcessor.h` |
| moved and edited | `local_detector_testbench/scripts/align.sh` | `alignment/align.sh` |
| moved and edited | `local_detector_testbench/scripts/correct_geometry.sh` | `correction/correct_geometry.sh` |
| moved and edited | `local_detector_testbench/scripts/prepare_geometry.sh` | `geometry/prepare_geometry.sh` |
| moved and edited | `local_detector_testbench/scripts/reconstruct.sh` | `reconstruction/reconstruct.sh` |
| moved and edited | `local_detector_testbench/scripts/reconstruct_corrected.sh` | `reconstruction/reconstruct_corrected.sh` |
| moved and edited | `local_detector_testbench/scripts/run_closure.sh` | `validation/run_closure.sh` |
| moved and edited | `local_detector_testbench/scripts/simulate.sh` | `simulation/simulate.sh` |
| moved and edited | `local_detector_testbench/scripts/validate.sh` | `validation/validate.sh` |
| retired package marker | `local_detector_testbench/stages/__init__.py` | — |
| moved and edited | `local_detector_testbench/stages/common.py` | `research_common.py` |
| moved and edited | `local_detector_testbench/stages/correction.py` | `correction/correct_geometry.py` |
| moved and edited | `local_detector_testbench/stages/geometry.py` | `geometry/prepare.py` |
| moved and edited | `local_detector_testbench/stages/millepede.py` | `alignment/align.py` |
| moved and edited | `local_detector_testbench/stages/reconstruction.py` | `reconstruction/reconstruct.py` |
| moved and edited | `local_detector_testbench/stages/simulation.py` | `simulation/simulate.py` |
| moved and edited | `local_detector_testbench/stages/validation.py` | `validation/validate.py` |
| moved and edited | `local_detector_testbench/visualization/README.md` | `visualization/README.md` |
| moved and edited | `local_detector_testbench/visualization/browse.C` | `visualization/browse.C` |
| moved and edited | `local_detector_testbench/visualization/closure.py` | `visualization/closure.py` |
| moved unchanged | `examples/seven_layer_telescope/alignment/pede_template.txt` | `alignment/pede_template.txt` |
| split configuration | `examples/seven_layer_telescope/cases/electron_1GeV_L2_x200um.json` | `simulation/configs/electron_1GeV.json`, `reconstruction/configs/electron_1GeV.json` |
| split configuration | `examples/seven_layer_telescope/cases/muon_5GeV.json` | `simulation/configs/muon_5GeV.json`, `reconstruction/configs/muon_5GeV.json` |
| moved unchanged | `examples/seven_layer_telescope/geometry/nominal.xml` | `geometry/nominal/seven_layer_telescope.xml` |
| moved unchanged | `examples/seven_layer_telescope/geometry/scenarios/L1_x100um_L2_x200um.json` | `geometry/scenarios/L1_x100um_L2_x200um.json` |
| moved unchanged | `examples/seven_layer_telescope/geometry/scenarios/L2_x200um.json` | `geometry/scenarios/L2_x200um.json` |
| modified | `validation/README.md` | `validation/README.md` |
| modified | `validation/check_root_outputs.py` | `validation/check_root_outputs.py` |
| modified | `validation/check_safety.py` | `validation/check_safety.py` |
| modified | `validation/preserved_files.json` | `validation/preserved_files.json` |
| modified | `validation/run_regression.sh` | `validation/run_regression.sh` |
| modified | `validation/validated_sources.json` | `validation/validated_sources.json` |
| modified | `docs/EICRECON_MILLEPEDE_INTEGRATION.md` | `docs/EICRECON_MILLEPEDE_INTEGRATION.md` |
| modified | `docs/STAGE_REFACTORING.md` | `docs/STAGE_REFACTORING.md` |
| modified | `docs/WORKFLOW.md` | `docs/WORKFLOW.md` |
| created | — | `localDetEICrecon/build.sh` |
| created | — | `geometry/__init__.py` |
| created | — | `geometry/placements.py` |
| created | — | `simulation/__init__.py` |
| created | — | `reconstruction/__init__.py` |
| created | — | `alignment/__init__.py` |
| created | — | `correction/__init__.py` |
| created | — | `validation/metrics.py` |
| created | — | `validation/__init__.py` |
| created | — | `visualization/__init__.py` |
| created | — | `docs/TASK_ARCHITECTURE.md` |

## Current Geometry and survey extension

The maintained controller now supports explicit SiMAPS L1/L2 X/Y in addition to legacy X modes. `geometry/transforms.py` is the six-DOF mathematical foundation; `geometry/prepare.py` and the focused DD4hep factory serialize only validated translations. `SurfacePlacements.h` maps selected DD4hep sensitive contexts into the existing ACTS fitter. RawHit v2 separates readout/topology from optional simulation-truth provenance. Survey G0 and selected reconstruction versions belong to the registry/configuration, not to assumed physical truth. See [conventions](GEOMETRY_CONVENTIONS.md) and [executed XY validation](XY_FOUNDATION_VALIDATION.md). Earlier scope statements in historical reports describe their original validation phase.
