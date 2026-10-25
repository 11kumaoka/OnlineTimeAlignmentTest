> This guide covers the retained endcap/BeamTestReco capability backend.
> Start new native EICrecon telescope studies with the
> [Telescope Alignment User Guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md).
> See the [implementation audit](TELESCOPE_IMPLEMENTATION_AUDIT.md) for the exact
> unique legacy alignment scopes, input contracts and queue lifecycle.

# Independent Research Workflow

Run commands from the repository root. Docker mounts it at `/work`.
`environment/run.sh` selects the pinned EIC image; `TESTBENCH_CONTAINER` selects
an existing container with that mount. Runtime login assets are isolated in
`result/.environment/`. ACTS 45.3.0, DD4hep 1.36, ROOT 6.38, EICrecon, JANA,
PODIO, EDM4hep/EDM4eic, NumPy, awkward, and uproot were used in validation.
See `validation/validated_environment.json` for recorded versions.

## Build and dependencies

```bash
bash environment/run.sh python3 environment/setup_dependencies.py
bash environment/run.sh bash environment/build.sh
```

The first command is only for a new checkout without `external/`. The setup
refuses overwrite and verifies source commits in `environment/dependencies.json`.
Offline clean clones can be selected with `--local-sources PATH`. Existing
`external/install/` provides `bin/pede`, `lib/libMille2.so`, and
`cmake/MilleConfig.cmake`; no legacy fallback is used.

The Plugin output defaults to `build/local_eicrecon_external/BeamTestReco.so`.
Use a **new** `TESTBENCH_BUILD_DIR` after moving sources; old CMake caches embed
source paths. Pass the chosen directory as `--build-dir` to both reconstruction
commands. `MILLEPEDE_PREFIX` selects a complete dependency installation;
`BUILD_JOBS` sets compilation concurrency. Disabling Mille support is unsupported.
`environment/build.sh` is the single build entry for this retained backend;
it configures `localDetEICrecon/CMakeLists.txt`.

## Ownership and configuration

| Task | Implementation | Editable configuration |
|---|---|---|
| Geometry Preparation | `geometry/prepare.py` | `--nominal geometry/nominal/seven_layer_telescope.xml`, `--geometry-config geometry/scenarios/L2_x200um.json` |
| Simulation | `simulation/simulate.py` | `--config simulation/configs/electron_1GeV.json` |
| Digitization | `digitization/digitize.py` | saved step2 input; unchanged factory defaults with provenance sidecar |
| Reconstruction before/after | `reconstruction/reconstruct.py` (`--after` for step6) | `--config reconstruction/configs/electron_1GeV.json`; step6 defaults to saved step3 settings |
| External Millepede-II | `alignment/align.py` | `--steering alignment/pede_template.txt` |
| Geometry Correction | `correction/correct_geometry.py` | saved scenario; L2 X default or explicit L1/L2 X |
| Numerical Validation | `validation/validate.py`, `validation/metrics.py` | optional `--reference validation/reference_metrics.json` |
| ROOT rendering | `visualization/closure.py`, `visualization/browse.C` | explicit Geometry/summary inputs; existing plot definitions |

The C++ Plugin and its in-process `BeamTestMilleProcessor` / `BeamTestMilleWriter`
are exclusively under `localDetEICrecon/`. The external solver is under
`alignment/`. `research_common.py` contains infrastructure only, with no detector
or physics model. Each wrapper executes its own Python module; direct module
invocation such as `python3 -m geometry.prepare --help` is also supported.
This retained backend uses independent stage modules rather than the native
`calibration.workflow` entry. No old-path compatibility package remains.

### Geometry

The unchanged nominal XML is independent of the scenario. The default is:

```json
{"detector":"SiMAPS","global_x_shifts_mm":{"2":0.2}}
```

The Geometry-only two-layer test uses:

```json
{"detector":"SiMAPS","global_x_shifts_mm":{"1":0.1,"2":0.2}}
```

Only canonical layer IDs `0`–`4` and finite numeric SiMAPS Global X shifts with
at most eight decimal places in mm are supported. Omitted layers stay nominal.
Unknown fields, unsupported axes/layers, non-finite values and booleans are
rejected. The placement sign remains Global X = −ring r. Preparation copies
nominal XML, edits only the Simulation copy, runs geoConverter on both, and checks
actual exported GDML module placements. The verifier requires the present
origin-centered, unrotated, single-module-per-layer hierarchy.

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/two_layer_001 --geometry-config geometry/scenarios/L1_x100um_L2_x200um.json
```

Preparation does not run Geant4 or fitting. Default correction remains L2-only
and rejects this two-layer scenario. To proceed with simultaneous L1/L2 X, select
`--mode l1_l2_x` for correction and `--correction-mode l1_l2_x` for validation or
the full closure wrapper. The validated +0.150/+0.200 mm scenario is
`geometry/scenarios/L1_x150um_L2_x200um.json`; see the saved-input commands in
[L1/L2 validation](L1_L2_ITERATIVE_VALIDATION.md). The wrapper preflights the
selected scope before Simulation and only routes independent stage calls.

### Simulation

Edit `events` and `beam` in `simulation/configs/{electron_1GeV,muon_5GeV}.json`.
Fields preserve particle, energy_GeV, seed, theta/phi min/max (radians),
position_mm, and vertex_sigma_mm_ns (x/y/z/time). The gun distribution remains
uniform. Electron defaults: 100 events, 1 GeV, source (0,0,−500) mm, X/Y sigma
0.2 mm, theta 0.010–0.030, phi 0–2π, seed 2035032807. Muon defaults: 80 events,
5 GeV, otherwise the same gun conditions. No seed or physics changes were made.

`simulate.sh --sim-input PATH` reuses a ROOT file by link and records its checksum,
source, event count, and reuse mode. It creates no fictitious DDSim command record.
The saved config is the requested processing/generation configuration, **not proof
of the imported file's actual beam or Geometry**. The researcher must establish
provenance. In particular the historical 99-track input starts at z=0 mm.

### Digitization and common RawHit input

`digitization/digitize.sh` consumes step2 and stops after writing
`step2_digitization/rawhits.edm4eic.root`. It preserves EventHeader and three
RawTrackerHit collections, with no SimHit/MC event payload. It records commands,
exit status, file hashes, conditions, readout signature and Geometry provenance.
It registers only local digitizers; no RecHit/fitter/Mille processors run.
The standard `acts` service Plugin must still load because the installed
`algorithms_init` library depends on its symbols; this is not local Track Fitting.

The default Reconstruction profile is now `raw`: no digitizer is registered.
With no explicit input it consumes step2_digitization. For an external file use
`--raw-input PATH --geometry XML`, with no step1/step2 requirement. Select
`--raw-metadata PATH` if the contract sidecar is not the input sibling
`rawhit_contract.json`. `--events N` selects a positive prefix, default all events.
The sidecar must describe the exact supported Cell IDs, calibrated charge/time
units and conditions. Simulation provenance is optional in the common command.
See [the complete contract and equivalence report](RAWHIT_BOUNDARY.md).

`--input-mode combined` is the original diagnostic SimHit-to-Track execution,
using step2. The same C++ algorithms are shared by both profiles. Corrected
Reconstruction defaults to step3's saved RawHit source and config; it does not
redigitize. An explicit `--geometry XML` also supports independent repeated
Reconstruction of the same external RawHits with another Geometry.

### Reconstruction

Edit `pdg`, `q_over_p`, `use_mpgd`, and `use_aclgad` in
`reconstruction/configs/{electron_1GeV,muon_5GeV}.json`. They map to the existing
`outputTrackPDG`, `seedQOverP`, `useMPGD`, and `useACLGAD` Plugin parameters.
Electron uses PDG 11, q/p −1, SiMAPS-only fitting. Muon uses PDG 13, q/p −0.2,
MPGD enabled, AC-LGAD disabled. Select the matching Simulation and Reconstruction
configs explicitly; step1 no longer selects a particle case.

Unchanged command constants include single-thread execution, the Plugin list,
output collections, writer z reference 100 mm, single-track requirement, and
injected writer shift −1 (disabled). The CLI checks 10 scalar Mille measurements
per accepted track, so configurations changing accepted measurement dimensionality
need a separate validation change before use. Preserving the muon settings does
not claim a new muon/Mille regression. Internal ACTS surfaces, seed covariance,
material handling, residual uncertainties, and derivatives remain C++ assumptions.
The in-process writer's standalone default `results/manual/mille.dat` is preserved
as a C++ default; every maintained reconstruction command explicitly overrides it
with the new step-specific path. No new workflow output uses that default.

### Alignment and correction

`alignment/pede_template.txt` keeps the existing labels: 1000+layer for X and
2000+layer for Y. L0/L4 are fixed; L1–L3 X/Y are varied. No added constraints or
parameter definitions were introduced. The template contains `@MILLE_FILE@`;
the selected template is snapshotted into step4, then expanded with an absolute
step3 Mille Binary path. Pede runs in step4 and writes its own reports there.

Correction negates the fitted measurement bias: label 1002 for default L2 X,
or labels 1001 and 1002 for explicit `--mode l1_l2_x`. Mode `l1_l2_xy` also applies labels 2001 and 2002. Only the selected X
components are applied; existing L1–L3 X/Y steering is unchanged. The full
workflow accepts `--correction-mode l1_l2_x`. With `--base-geometry`, each
selected residual correction is added to its current Global X position; the
Python controller uses this path for fixed-RawHit iteration. Convergence requires
every selected component to pass the configured demonstration tolerance.
Only selected alignment components are changed; fixed survey placements are retained. Global Z and individual L1 tilt alignment require their explicit gated modes, described below. The old fixed-Global two-axis modes remain disabled; explicit coupled SO(3) scopes use the separate gates below.
See [executed two-layer validation](L1_L2_ITERATIVE_VALIDATION.md).

## Manual commands: seven steps plus independent Digitization

Use a new child of `result/` without whitespace. `--result-dir` is the documented
convention (`--run-dir` is retained as a CLI spelling alias only).

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/manual_001 --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh bash simulation/simulate.sh --result-dir result/manual_001 --config simulation/configs/electron_1GeV.json
bash environment/run.sh bash digitization/digitize.sh --result-dir result/manual_001
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/manual_001 --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/manual_001 --steering alignment/pede_template.txt
bash environment/run.sh bash correction/correct_geometry.sh --result-dir result/manual_001
bash environment/run.sh bash reconstruction/reconstruct.sh --after --result-dir result/manual_001
bash environment/run.sh bash validation/validate.sh --result-dir result/manual_001
```

The shell wrapper for step6 supplies `--after` to the shared reconstruction module.
It defaults to the immutable step3 config. Validation requires the same simulation,
Plugin, and reconstruction config hashes before comparing outputs.

| Step | Inputs | Outputs under `result/<name>/` | Success evidence |
|---|---|---|---|
| 1 | nominal XML and Geometry scenario | `step1/nominal.xml`, `misaligned.xml`, `geometry_config.json`, `placement_check.json`, `nominal_qa/`, `misaligned_qa/` | geoConverter succeeds; all seven placements verified |
| 2 | step1 misaligned XML; Simulation config or imported ROOT | `step2/events.edm4hep.root`, `config.json` | sufficient events; SiMAPS/MPGD/AC-LGAD hit collections |
| 2_digitization | step2; measured Geometry; unchanged digitizer conditions | `step2_digitization/rawhits.edm4eic.root`, contract/config snapshots | required collections/EventHeaders, no MC event payload |
| 3 | RawHit file and contract; nominal or explicit Geometry; Plugin and Reconstruction config | `step3/reco.root`, `mille.dat`, `config.json` | nonzero tracks; event and Mille counters agree |
| 4 | step3 Mille Binary; steering template | `step4/steering_template.txt`, `pede.txt`, `millepede.res`, `.log`, `.his`, `.end` | pede status 0/1; L2 solution present |
| 5 | step4 fit; step1 nominal/scenario | `step5/corrected.xml` | supported capability and parsed XML |
| 6 | same RawHits as step3; step5 corrected XML; same Plugin/config | `step6/reco.root`, `mille.dat`, `config.json` | counters; provenance matches step3 |
| 7 | steps1–6 | `step7/summary.json`, `alignment.root` | metrics; optional reference test; ROOT objects |

Every completed stage has `complete.json` with checksums. Every executed subprocess
has `command.json`, `stdout.log`, and `exit.json`. Geometry subprocess records live
in their respective QA directories. Pure correction and imported Simulation have
no subprocess records. All completed regular output files, including nested QA
files, are hashed; dependent stages verify them. Source config changes cannot
silently alter existing snapshots. Missing prerequisites are refused; nothing
executes later stages automatically. Partial failures are retained; retry in a
new result directory rather than overwrite or fabricate completion markers.

## Regression and visualization

```bash
bash environment/run.sh bash validation/run_regression.sh result/regression_001
bash environment/run.sh python3 validation/check_root_outputs.py --result-dir result/regression_001
python3 validation/verify_preservation.py
python3 validation/check_safety.py
root --web=off -l 'visualization/browse.C("result/manual_001/step7/alignment.root")'
```

`run_regression.sh` optionally accepts a second BUILD_DIR argument. It reuses the
local historical input documented in `validation/README.md`. Expected: 99 tracks
before/after, L2 correction +198.75 μm, pooled L2 Rec−Sim −199.571 → −0.821 μm,
and Σχ² / Σstored ACTS nDoF 45.592 → 1.981. Reference tolerances are in
`validation/reference_metrics.json`. Do not apply this reference to fresh events.

Step7 stores `c_geometry`, `c_hit_residuals`, `c_closure`, at least 20 residual
histograms, and Closure TGraphs. ROOT rendering consumes numerical metrics from
`validation/metrics.py`; it does not run Simulation, reconstruction, or fitting.
Simulation Hit Residual validation reads truth from step2 separately and verifies
run/event identity; common Reconstruction does not consume truth. These plots
are not an experimental-data validation method. Hit distributions use unique event/layer pairs, while reference means retain the
historical pooled Rec mean minus Sim mean. The χ² ratio retains ACTS's stored
measurement-dimension convention; it is not statistical reduced χ².
For a Docker/XQuartz GUI use `bash environment/root_shell.sh`, then `cd /work`.
Batch checks do not require X11. Interactive TBrowser operation was not tested.

## Historical data and troubleshooting

`results/` is immutable legacy data for this migration. No historical XML, ROOT,
Mille Binary, log, symlink, or command record was moved or edited. This includes
`results/reference/physical_alignment_L2_x200um/`, the latest source-position study
`results/vertex_zminus500_20261019_01/closure100/`, and the previous stage-refactoring
results. Historical manifests retain those paths. The nominal/source pins are
retargeted to their new maintained paths with unchanged hashes.

- Missing dependencies: install a complete prefix; never reuse an old source-path
  CMake cache. Upstream source/installations are not changed by this refactor.
- Missing reference data: obtain the checksum-identical dataset from the maintainer
  or persistent archive; generated data and external installations are not in Git.
- Existing/partial step: inspect its records, then select a new result directory.
- Standard DD4hep-to-ACTS conversion diagnostics remain visible; the custom manual
  surface fitter is independent. This refactor does not solve that conversion.
- Arbitrary layouts, fits outside the explicitly validated coupled scopes, corrections beyond the selected SiMAPS scope, material
  changes, error rescaling, or revised statistical nDoF are outside scope.

See [TASK_ARCHITECTURE.md](TASK_ARCHITECTURE.md) for executed commands, migration
inventory, and results. [STAGE_REFACTORING.md](STAGE_REFACTORING.md) records the
preceding architecture and is historical, not the current command guide.

The current RawHit development and its exact tests are documented in
[RAWHIT_BOUNDARY.md](RAWHIT_BOUNDARY.md). Earlier architecture/publication reports
remain historical records of their respective validated baselines.

## Sequential RawHit calibration

The optional [Python controller](../calibration/README.md) provides once/watch ingestion, persistent queue state, fixed-dataset L2 iterations, and explicit candidate review and activation. Incoming files belong in `input/`; outputs belong in a dedicated `result/` state directory. Demonstration calibration cuts are provisional, and calibration is disabled in the shipped configuration.

## General transform foundation and survey-based X/Y

`geometry/transforms.py` provides proper rigid transforms with frame-aware composition and pivots. The transform library alone does not certify six-DOF fitting; explicit coupled scopes require the gates below. `geometry/scenarios/L1_L2_xy.json` is a separate controlled simulation (+150/−120 μm on L1, +200/+90 μm on L2). Generated XY Geometry loads the local `LocalTelescopeGeometry` library built by the existing CMake project. The default build is discovered automatically; for a custom build, set `TESTBENCH_BUILD_DIR` when preparing or simulating Geometry. The closure wrapper propagates its `--build-dir`; the controller propagates the configured build directory.

```sh
bash environment/run.sh bash validation/run_closure.sh --result-dir result/NEW_XY --geometry-config geometry/scenarios/L1_L2_xy.json --correction-mode l1_l2_xy
```

This executes a new Simulation using unchanged default beam parameters. To use saved data, add `--sim-input ROOT`. For sequential data-driven iteration use `calibration/config/l1_l2_xy_demo.json`, enable the demonstration policy, select the explicit survey fallback and use the existing controller once/watch commands. No Simulation Truth Geometry is required. See [Geometry conventions](GEOMETRY_CONVENTIONS.md), [the RawHit v2 contract](RAWHIT_BOUNDARY.md), and [executed validation](XY_FOUNDATION_VALIDATION.md).


## Sensor in-plane rotation

Use `l1_rz`, `l1_l2_rz`, or `l1_l2_xy_rz` explicitly. The default remains `l2_x`.
The scenario field `global_rz_rad` supplies physical Global +Z angles in radians
for L1/L2; the dedicated placement attribute rotates about each sensor center.
Do not use ring phi for this correction. `geometry/scenarios/L1_rz10mrad.json`,
`L1_L2_rz.json`, and `L1_L2_xy_rz.json` are separate controlled examples.

The existing one-shot wrapper selects the matching Mille derivatives, steering,
correction and ROOT validation. For a custom build:

```sh
bash environment/run.sh bash validation/run_closure.sh --result-dir result/NEW_RZ --geometry-config geometry/scenarios/L1_L2_rz.json --correction-mode l1_l2_rz --build-dir build/YOUR_VALIDATED_BUILD
```

For independent stages, add `--alignment-mode MODE` only to Reconstruction,
use `--steering alignment/pede_MODE.txt` for Alignment, and `--mode MODE` for
Geometry Correction. Digitization has no alignment-mode option. Pass the same
RawHit input across iterations; correction uses current Geometry, not truth.

Controller use additionally requires plugin-matched fresh-DD4hep derivative
validation, explicit angular bounds and mode-specific steering. Start from the
disabled `calibration/config/l1_rz_demo.json`; use a zero-displacement preparation
scenario and an explicit fallback/survey. Candidates remain inactive pending
independent validation and explicit approval. See [the complete rotation audit](ROTATION_ALIGNMENT_VALIDATION.md)
for independent commands, all tested cases, warnings and observability limits.
The separate `simulation/configs/electron_1GeV_rotation_1000.json` changes only
the event count for a statistics study; the historical beam configuration is unchanged.

## Experimental Z workflow

For `l1_z`, `l1_l2_z`, or `l1_l2_xyz`, use the existing Python Controller with
explicit Z derivative evidence and the per-iteration local/global information
gate. The convenience closure runner refuses these modes to prevent bypassing
the gates. Independent Geometry Preparation, Simulation, Digitization,
Reconstruction, Alignment and Geometry Correction modules remain available for
controlled testing. Use matching mode-specific `alignment/pede_MODE.txt` and
`--alignment-mode MODE` in Reconstruction; correction `--mode MODE` composes
with `--base-geometry CURRENT.xml`. Never negate the 4000+layer Z parameter;
X/Y bias parameters retain their historical negative correction sign.
See [the executed Z study](Z_ALIGNMENT_VALIDATION.md) for exact stage commands,
new output paths, inactive-candidate lifecycle and scientific limitations.

## Individually validated L1 Rx/Ry

Use `l1_rx` or `l1_ry` consistently in Reconstruction, Pede steering, Geometry
Correction and the existing Python Controller. Physical preparation scenarios
are `geometry/scenarios/L1_rx.json`, `L1_ry.json` and `L1_ry_negative.json`.
They retain canonical beam, material, readout and uncertainties. The nominal XML
is never edited. Simulation and Digitization use the physical Geometry;
alignment reconstructs fixed RawHits with its selected survey/current Geometry.

Example independent stages inside the initialized container (all output paths
must be new):

```sh
export TESTBENCH_BUILD_DIR=/work/build/YOUR_VALIDATED_BUILD
python3 -m geometry.prepare --result-dir result/NEW_RX --geometry-config geometry/scenarios/L1_rx.json
python3 -m simulation.simulate --result-dir result/NEW_RX
python3 -m digitization.digitize --result-dir result/NEW_RX --build-dir build/YOUR_VALIDATED_BUILD
python3 -m reconstruction.reconstruct --result-dir result/NEW_RX --build-dir build/YOUR_VALIDATED_BUILD --alignment-mode l1_rx
python3 -m validation.validate_tilt_derivatives --build-dir build/YOUR_VALIDATED_BUILD --layer 1 --output result/NEW_RX_DERIVATIVES
python3 -m validation.tilt_observability --mille result/NEW_RX/step3/mille.dat --mode l1_rx --max-sigma-rad .01 --output result/NEW_RX/initial_information.json
```

For iterations, configure a copy of `calibration/config/l1_rx_demo.json` with
that build, its passed derivative report, explicit fallback Geometry, input
readiness protocol and a fresh state. The Controller invokes the existing
Alignment and Geometry Correction stages, applies physical 5001/6001 increments
with positive sign, and reconstructs the same RawHits at each iteration. After convergence, independently reconstruct the exact final candidate in a new result directory.
No Truth input supplies correction values. See [Controller options](../calibration/README.md#individual-global-x-and-y-tilts).

`l1_rx_ry` and `l1_l2_rx_ry` are deliberately refused by the Plugin,
Reconstruction, Alignment, Geometry Correction and Controller. Their archived
experiments and disabled configurations are not maintained execution routes.
Read-only information diagnostics and ROOT plotting can inspect those results.
Do not infer support for combined rotations or six-DOF fitting from a full-rank
design alone. See [the scientific stop decision](TILT_ALIGNMENT_VALIDATION.md).

For exact final-candidate validation, use the inactive XML reported by the
Controller and the same closed RawHit input. No study-specific helper is needed:

```sh
python3 -m reconstruction.reconstruct --result-dir result/NEW_RX_FINAL --raw-input input/NEW_RX/rawhits.edm4eic.root --raw-metadata input/NEW_RX/rawhit_contract.json --geometry result/NEW_RX_STATE/geometries/geo-HASH/geometry.xml --build-dir build/YOUR_VALIDATED_BUILD --alignment-mode l1_rx
python3 -m visualization.tilt_alignment --case result/NEW_RX --report result/NEW_RX_STATE/jobs/INPUT_ID/attempt-001/calibration/calibration_report.json --candidate result/NEW_RX_STATE/geometries/geo-HASH/geometry.xml --final-reconstruction result/NEW_RX_FINAL/step3 --output result/NEW_RX_ROOT
```

Replace `geo-HASH` and `INPUT_ID` with the recorded identifiers. The visualization
reads Simulation Truth only for post-fit validation, checks Geometry/RawHit
provenance, and writes `tilt_alignment.root`, PDF canvases and `summary.json`.
Open the ROOT file with `root -l result/NEW_RX_ROOT/tilt_alignment.root` and
`new TBrowser;`. Real RawHit data without Simulation Truth need separate
truth-free residual diagnostics; this RecHit-minus-SimHit plotting command is
specifically for controlled Simulation closure.

## Explicit coupled SO(3) scopes

Use the mode-specific Controller templates `l1_rotations_demo.json`,
`l1_l2_rotations_demo.json`, `l1_six_dof_demo.json` or
`l1_l2_six_dof_demo.json` under `calibration/config/`. They are disabled by
default. The first two fit three rotations per selected sensor; the latter two
also fit X/Y/Z. All other sensors remain fixed. The old `l1_rx_ry` and
`l1_l2_rx_ry` names remain refused because their old finite model failed.
Read [the scientific report](SO3_ALIGNMENT_VALIDATION.md) before using a scope;
mathematical support is distinct from controlled physical and statistical
validation.

Inside the EIC environment, use fresh paths for every command:

```sh
export TESTBENCH_BUILD_DIR=/work/build/YOUR_SO3_BUILD
bash environment/build.sh
python3 -m validation.validate_tilt_derivatives --coupled --layer 1 --build-dir "$TESTBENCH_BUILD_DIR" --output result/NEW_DERIVATIVES_L1
python3 -m validation.validate_tilt_derivatives --coupled --layer 2 --build-dir "$TESTBENCH_BUILD_DIR" --output result/NEW_DERIVATIVES_L2
python3 -m validation.so3_closure --writer-fixture /work/result/NEW_DERIVATIVES_L1/writer_fixture --translation-scale .25 --output result/NEW_NOISELESS
python3 -m validation.merge_so3_evidence --build-dir "$TESTBENCH_BUILD_DIR" --derivative-report result/NEW_DERIVATIVES_L1/report.json --derivative-report result/NEW_DERIVATIVES_L2/report.json --noiseless result/NEW_NOISELESS --output result/NEW_SO3_GATE.json
```

Both layers are checked so one gate can support either selected scope. The
noiseless command uses known nonzero survey centers and explicit synthetic
translations; `.25` is the declared translation-scale capture-range control,
not an uncertainty scale. Its default large-offset two-layer fixture preserves
a known Pede rejection failure. Do not bypass that failure by changing steering.

For example, prepare a separately declared physical L1 rotation sample:

```sh
python3 -m geometry.prepare --result-dir result/NEW_L1 --geometry-config geometry/scenarios/L1_rotations.json
python3 -m simulation.simulate --result-dir result/NEW_L1 --config simulation/configs/electron_1GeV.json
python3 -m digitization.digitize --result-dir result/NEW_L1 --build-dir "$TESTBENCH_BUILD_DIR"
```

The other physical examples are `L1_L2_rotations.json`, `L1_six_dof.json` and
`L1_L2_six_dof.json`. Copy a beam config to a fresh result path to set and record
an independent seed without editing canonical physics. For actual research
inference, deliver the resulting RawHit file using the existing
`rawhit-delivery-v1` readiness contract under `input/`, as described in the
[Controller guide](../calibration/README.md). Alignment needs no Truth Geometry.

Copy the matching disabled Controller template to a new configuration file,
set `build_dir`, set `calibration.tilt_derivative_report` to the sealed gate,
and explicitly set `calibration.enabled=true`. Retain `measured_geometry=null`.
If using a Survey, set `fallback_geometry` to its XML; selected full orientations
and surveyed centers are allowed by these coupled scopes. Unselected placements,
materials and readout remain protected. Run the existing worker:

```sh
python3 -m calibration.controller once --config result/YOUR_CONTROLLER.json --input-dir input/YOUR_DELIVERY --state-dir result/NEW_STATE
```

No candidate is automatically activated. Reconstruct the exact reported final
candidate using the same RawHit bytes, `--alignment-mode MODE`, and
`--build-dir "$TESTBENCH_BUILD_DIR"`. Then use the existing explicit ROOT CLI:

```sh
python3 -m visualization.tilt_alignment --case result/NEW_L1 --report result/NEW_STATE/jobs/INPUT_ID/attempt-001/calibration/calibration_report.json --candidate result/NEW_STATE/geometries/geo-HASH/geometry.xml --final-reconstruction result/NEW_FINAL/step3 --output result/NEW_SO3_ROOT
```

The output contains `tilt_alignment.root`, PDF canvases and `summary.json`,
including complete-matrix orientation distances, selected-layer Hit Residuals,
Global relative rotation-vector histories, translations when fitted, ACTS/Pede
quality and actual information matrices. Geometry Truth is used only for these
post-fit comparisons. Do not interpret the last Controller iteration's input
quality as the quality of its newly produced final candidate.

## Manual three-layer six-DOF development workflow

Use [L3_SIX_DOF_MANUAL.md](L3_SIX_DOF_MANUAL.md) for separately executable Geometry, Simulation, Digitization, RawHit reconstruction/Mille, information checks, Pede, current-Geometry correction, corrected reconstruction and ROOT visualization. The optional existing Controller accepts disabled-by-default `l3_six_dof` and `l1_l2_l3_six_dof` templates after version-matched evidence. These are technically checked prototypes awaiting detailed physical/statistical validation. The convenience closure runner refuses these gated modes.
