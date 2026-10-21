# Workflow Guide

Run host commands from the repository root. `environment/run.sh` mounts the
checkout at `/work` and uses the immutable image pinned in `environment/run.sh`.
`environment/dependencies.json` pins dependency source commits;
`validation/validated_environment.json` records observed package versions.
The validated environment includes ACTS 45.3.0, DD4hep 1.36, ROOT 6.38,
EICrecon, JANA, PODIO, EDM4hep/EDM4eic, NumPy, uproot, and awkward.

## Setup and build

```bash
# A new checkout only; external/ must not exist:
bash environment/run.sh python3 environment/setup_dependencies.py
bash environment/run.sh bash environment/build.sh
```

The setup script clones pinned Mille and Millepede-II sources and installs
`external/install/bin/pede`, `external/install/lib/libMille2.so`, and
`external/install/cmake/MilleConfig.cmake`. An existing local installation can
be used directly. For an offline setup, `--local-sources PATH` accepts clean
clones named as in `environment/dependencies.json`; it verifies their commits.
No removed legacy directory is needed.

Build output: `build/local_eicrecon_external/BeamTestReco.so`.
`TESTBENCH_BUILD_DIR` selects another build tree; pass the same path with
`--build-dir` to the workflow. `MILLEPEDE_PREFIX` selects a complete dependency
installation with no legacy fallback. `BUILD_JOBS` controls compilation jobs.
The Plugin requires Mille support; `ENABLE_MILLEPEDE=OFF` is unsupported.

`TESTBENCH_CONTAINER` selects an existing container mounted at `/work`.
Otherwise Docker launches the pinned image. Login-environment asset links are
isolated in `results/.environment/`. Each physics process runs in its stage
subdirectory, so implicit outputs do not pollute the repository root.

## Case settings

The default case is
`examples/seven_layer_telescope/cases/electron_1GeV_L2_x200um.json`.
Pass `--case PATH` to prepare/all. Later stages read `geometry/case.json` from
the result directory, not the current source file.

- Electron: 100 events, 1 GeV, mean source (0,0,−500) mm, PDG 11, seed q/p=−1,
  five SiMAPS measurements. MPGD and AC-LGAD hits are simulated but not fitted.
- Muon case: 80 events, 5 GeV, mean source (0,0,−500) mm, PDG 13, q/p=−0.2,
  MPGD fitting enabled, AC-LGAD fitting disabled.
- Both: X/Y vertex sigma 0.2 mm, zero z/time width, theta 0.010–0.030,
  phi 0–2π, uniform gun distribution, recorded seed 2035032807, and L2 +0.2 mm
  Global X injection in the Simulation Geometry.

`beam.position_mm` is passed to DDSim `--gun.position` with mm units.
Archived case snapshots without the key retain the original (0,0,0) default.
The unchanged nominal XML is `examples/seven_layer_telescope/geometry/nominal.xml`.
Only the single-module, phi0=0, five-SiMAPS L2 Global X backend is supported.

## Steps and inputs/outputs

Choose a NEW child directory of `results/` without whitespace; pede steering
cannot accept whitespace in these paths. The supported CLI is `--result-dir`; `--run-dir` is a temporary alias.
Stages refuse existing outputs and use no force option.

| Step / script | Input | Output under the result directory | Success check |
|---|---|---|---|
| Geometry Preparation / `prepare_geometry.sh` | nominal XML, case JSON | `geometry/{nominal,misaligned}.xml`, `case.json`, GDML QA | geoConverter exits 0, completion marker and hashes |
| Simulation / `simulate.sh` | misaligned Geometry, case | `simulation/events.edm4hep.root` | requested event count and all three hit collections |
| Reconstruction / `reconstruct.sh` | same simulated events, nominal Geometry, Plugin | `before/reco.root`, `before/mille.dat` | nonzero tracks, matching Mille counters |
| Alignment / `align.sh` | before Mille Binary, example pede template | `alignment/pede.txt`, `millepede.{res,log,his,end}` | pede status 0/1 and L2 parameter present |
| Geometry Correction / `correct_geometry.sh` | L2 pede parameter, nominal XML | `correction/corrected.xml` | XML parsed, correction recorded |
| Corrected Reconstruction / `reconstruct_corrected.sh` | same Simulation, corrected Geometry, same Plugin | `after/reco.root`, `after/mille.dat` | counters and input/plugin hashes match |
| Validation / `validate.sh` | before/after ROOT, three Geometries, pede | `validation/plots/{alignment.root,summary.json}` | metrics and optional reference comparison |

Every stage records `command.json`, `stdout.log`, `exit.json`, and `complete.json`.
Nominal XML is copied, never edited. The model fixes endpoints L0/L4 and solves
SiMAPS x/y Alignment Parameters; the supported update applies only L2 Global X.
Pede's L2 measurement bias has the opposite sign to the placement correction.

Pede runs with its working directory set to `alignment/`. Its steering file uses
an absolute Mille Binary path, so changing the working directory does not change
which measurements are fitted. DDSim, EICrecon, geoConverter, and PyROOT likewise
run in their own stage directories and receive absolute input/output paths.

## Run all steps

```bash
bash environment/run.sh bash local_detector_testbench/scripts/run_closure.sh \
  --result-dir results/electron_001
```

Independent commands:

```bash
bash environment/run.sh bash local_detector_testbench/scripts/prepare_geometry.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/simulate.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/reconstruct.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/align.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/correct_geometry.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/reconstruct_corrected.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/validate.sh --result-dir results/manual_001
```

To reuse a Simulation, pass `--sim-input PATH` to simulate/all. The input is linked
without changing its bytes. Its actual MCParticles vertices define the sample;
current case beam settings only describe newly generated events.
The Plugin's standalone writer default is `results/manual/mille.dat`; standalone
users must create the parent directory. The formal workflow always supplies a
new stage-specific path and should be preferred.

## References and checks

```bash
bash environment/run.sh bash validation/run_regression.sh results/regression_001
bash environment/run.sh python3 validation/check_root_outputs.py --result-dir results/regression_001
python3 validation/verify_preservation.py
python3 validation/check_safety.py
```

`results/reference/physical_alignment_L2_x200um/` contains the preserved z=0 mm
Simulation and original 99-track outputs. The expected metrics and tolerances
are in `validation/reference_metrics.json`. These data are local, not distributed
by Git clone; request them from the project maintainer before running regression.

All old runs moved to `results/` without altering regular-file contents. The latest
pre-cleanup source-position study is
`results/vertex_zminus500_20261019_01/closure100/`. Path relocation is documented
in `validation/path_migration.json`; the preservation checker validates both the
original 221 baseline entries and every relocated data file in
`validation/relocated_data_sha256.json`. Historical JSON, logs, archived scripts,
and command records retain old provenance strings and are not current instructions.
Existing Simulation input links now point to the relocated reference data.

## ROOT visualization

`validation/plots/alignment.root` contains `c_geometry`, `c_hit_residuals`,
`c_closure`, residual histograms for x/y on all five SiMAPS layers, and closure
TGraphs. Open with a ROOT GUI installation:

```bash
root --web=off -l 'local_detector_testbench/visualization/browse.C("results/electron_001/validation/plots/alignment.root")'
```

`environment/root_shell.sh` retains the XQuartz DISPLAY and xhost setup using the
pinned image and a repository-relative mount. It starts in the environment cache;
run `cd /work` before the macro command. Interactive GUI operation requires ROOT
GUI/X11 support and is separate from the batch ROOT-file checks.

The geometry view is a placement schematic, not a generic rotated-detector viewer.
Hit Residual histograms use unique event/layer pairs; summary means retain the
historical pooled Rec mean minus Sim mean definition. The χ² ratio is
Σχ² / Σstored ACTS nDoF (measurement dimensions), not statistical reduced χ².

## Troubleshooting and scope

- Missing dependencies: use a complete `external/install/`; never reuse a legacy
  CMake cache. A failed setup is retained; retry with a new `--workspace`.
- Incomplete or existing stage: inspect its stdout and exit status, then use a new
  result directory. The workflow never silently replaces existing data.
- Missing reference data: restore the byte-identical files from the external
  archive or project data store, using the migration map and checksum manifests.
- Standard ACTS conversion diagnostics: the known DD4hep-to-ACTS conversion failure
  remains visible. The local manual-surface fitter operates independently; required
  plugins remain enabled. This cleanup does not solve that geometry conversion.
- Electron material effects and statistical nDoF conventions are unchanged. No
  uncertainties, fitted parameters, alignment derivatives, or constraints were tuned.

Write maintained code comments, help, labels, and new technical reports in English.
