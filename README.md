# Local Detector Alignment Research

Independent DD4hep/EICrecon research tasks: Detector Geometry → Simulation →
Digitization → saved RawHits → Hit Reconstruction / Track Fitting → Mille Binary → Millepede-II →
Geometry Correction → reconstruction of the same events → Closure Validation.

The supported example is a seven-plane telescope: five SiMAPS planes, MPGD, and
AC-LGAD. Geometry Preparation supports SiMAPS Global X scenarios. Geometry
Correction and full Closure support **L2 Global X** by default and **simultaneous L1/L2 Global X or X/Y** through explicit `l1_l2_x` or `l1_l2_xy` modes. A reusable six-DOF transform foundation is available. Opt-in `l1_rz`, `l1_l2_rz`, and `l1_l2_xy_rz` modes add validated SiMAPS L1/L2 Global Z rotation. Explicit `l1_z`, `l1_l2_z`, and `l1_l2_xyz` modes support Global Z translation. Individually validated `l1_rx` and `l1_ry` support SiMAPS L1 sensor tilts. The old fixed-Global two-axis modes remain disabled. New explicit coupled SO(3) modes have separate mathematical, derivative and controlled-closure gates; see [the SO(3) checkpoint](docs/SO3_ALIGNMENT_VALIDATION.md) for their validated scope and capture-range limits. See [rotation validation](docs/ROTATION_ALIGNMENT_VALIDATION.md), [Z validation](docs/Z_ALIGNMENT_VALIDATION.md), and [the tilt validation checkpoint](docs/TILT_ALIGNMENT_VALIDATION.md).

## Setup

Run from the repository root, mounted at `/work` inside the EIC Docker image:

```bash
# Only on a new checkout without external/:
bash environment/run.sh python3 environment/setup_dependencies.py
bash environment/run.sh bash localDetEICrecon/build.sh
```

Skip dependency installation when `external/install/` already exists. The pinned
image is in `environment/run.sh`; dependency commits are in
`environment/dependencies.json`. `TESTBENCH_CONTAINER` can select an existing
container with this repository mounted at `/work`.

## Independent commands

Choose a new result directory. Stop and inspect after any command:

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/electron_001 --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh bash simulation/simulate.sh --result-dir result/electron_001 --config simulation/configs/electron_1GeV.json
bash environment/run.sh bash digitization/digitize.sh --result-dir result/electron_001
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/electron_001 --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/electron_001 --steering alignment/pede_template.txt
bash environment/run.sh bash correction/correct_geometry.sh --result-dir result/electron_001
bash environment/run.sh bash reconstruction/reconstruct_corrected.sh --result-dir result/electron_001
bash environment/run.sh bash validation/validate.sh --result-dir result/electron_001
```

Each command runs only its stage. Existing step directories are never overwritten.
New outputs are `result/electron_001/step1/` through `step7/`, plus
`step2_digitization/rawhits.edm4eic.root`; existing steps are not renumbered. Historical
`results/` stays intact and is not a destination for new runs.

The default Simulation generates 100 events of 1 GeV electrons at mean
(0,0,−500) mm, toward +z with the configured angular spread and 0.2 mm X/Y width.
The original electron/muon settings, seeds, nominal Geometry, ACTS hypotheses,
and alignment model are preserved. Simulation and Reconstruction configurations
are now separate; select the matching pair explicitly for a muon study.

## Layout

```text
localDetEICrecon/    C++ Plugin, processors, factories, algorithms, in-process Mille Writer, CMake/build
geometry/           nominal XML, independent scenarios, preparation and placement verification
simulation/         editable beam configs and DDSim execution
digitization/       independent SimHit-to-RawHit execution and RawHit contract
reconstruction/     editable fit settings and EICrecon command construction
alignment/          Pede steering and external solver execution/parsing
correction/         L2 or explicit L1/L2 Global X Geometry Correction
validation/         numerical metrics, regression references, safety/preservation checks
visualization/      ROOT rendering and browser macro
environment/        Docker launcher, dependency setup, runtime/build support
docs/               architecture, workflow, integration notes and historical reports
research_common.py  small shared path, checksum, execution-record and CLI utilities
external/           ignored dependency source/build/install
build/              ignored generated Plugin builds
result/             ignored new runs, each with step1–step7
results/            untouched, ignored historical results and reference data
```

## Two-layer Geometry and alignment

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/two_layer_001 --geometry-config geometry/scenarios/L1_x100um_L2_x200um.json
```

Inspect `step1/placement_check.json` and `step1/misaligned.xml`. L1 is shifted
+0.100 mm and L2 +0.200 mm. No Simulation runs during preparation. Full Closure can explicitly select
`--correction-mode l1_l2_x`; the validated simultaneous dataset uses
`geometry/scenarios/L1_x150um_L2_x200um.json` (+0.150/+0.200 mm).
See [two-layer validation](docs/L1_L2_ITERATIVE_VALIDATION.md) for saved-input commands.
Pede's existing L1–L3 X/Y parameter model is unchanged.

## Regression and ROOT

```bash
bash environment/run.sh bash validation/run_regression.sh result/regression_001
bash environment/run.sh python3 validation/check_root_outputs.py --result-dir result/regression_001
python3 validation/verify_preservation.py
python3 validation/check_safety.py
root --web=off -l 'visualization/browse.C("result/electron_001/step7/alignment.root")'
```

The historical input is local data, not supplied by a Git clone. Its 99-track
reference gives +198.75 μm L2 correction, residual −199.571 → −0.821 μm, and
Σχ² / Σstored ACTS nDoF 45.592 → 1.981. It must not be applied to fresh z=−500 mm
events. See [local dataset requirements](validation/README.md).

See the [Workflow Guide](docs/WORKFLOW.md) for I/O, parameters, and troubleshooting;
[architecture and validation report](docs/TASK_ARCHITECTURE.md) for migration and
executed checks; and [EICrecon–Millepede-II integration](docs/EICRECON_MILLEPEDE_INTEGRATION.md)
for the mathematical model and library integration.

Maintained comments, CLI help, labels, and technical documents use English.

The [final publication audit](docs/FINAL_ARCHITECTURE_AUDIT.md) records cleanup
decisions, configuration ownership, and the validation performed before publication.

## Common RawHit input

Simulation-generated RawHits and future DAQ-adapter RawHits share the same
truth-independent RecHit, ACTS and Mille implementations. The production PODIO
file contains only EventHeader and LocalSiMAPS/MPGD/ACLGADRawHits, plus file metadata.
No DAQ decoder is implemented. The mandatory sidecar defines readout, units,
Geometry and calibration provenance; a RawTrackerHit type alone is insufficient.
See [RawHit contract, profiles and equivalence tests](docs/RAWHIT_BOUNDARY.md).

An external RawHit file needs no prior Simulation stages:

```bash
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/imported_raw_001 --raw-input result/electron_001/step2_digitization/rawhits.edm4eic.root --geometry geometry/nominal/seven_layer_telescope.xml --config reconstruction/configs/electron_1GeV.json
```

The sibling `rawhit_contract.json` is used by default; `--raw-metadata PATH` selects
another sidecar. Only the `raw` factory profile is registered downstream, so no
digitizer can run again. `--input-mode combined` retains the original Simulation
comparison profile. Offline RawHit files are optional boundaries for reusable
in-memory C++ factories, not a requirement for a future online pipeline.

For sequential external RawHit delivery and fixed-dataset iterative alignment, see the [Python Calibration Controller](calibration/README.md). This optional foreground prototype does not replace the independent workflow stages.

For the survey-based Geometry foundation, actual DD4hep-to-ACTS surface mapping, optional simulation-truth metadata, and validated simultaneous L1/L2 X/Y, see [Geometry conventions](docs/GEOMETRY_CONVENTIONS.md) and [XY validation](docs/XY_FOUNDATION_VALIDATION.md). Existing nominal Geometry and historical regressions remain preserved.

### Experimental Global Z alignment

The opt-in `l1_z`, `l1_l2_z`, and `l1_l2_xyz` modes extend the existing Controller;
default X/Y/Rz workflows remain unchanged. Use a dedicated build and new result
directories, validate same-build physical/Mille derivatives, and supply the Z
evidence and observability policy before Controller processing. RawHit input is
fixed across iterations and candidates are never activated automatically.
See [Global Z validation and exact commands](docs/Z_ALIGNMENT_VALIDATION.md),
[Geometry conventions](docs/GEOMETRY_CONVENTIONS.md), and
[Controller configuration](calibration/README.md#opt-in-z-and-xyz-calibration).
Geometric closure does not certify nominal parameter errors; the retained
[30-seed Rz study](docs/RZ_STATISTICAL_VALIDATION.md) found broad pulls.

### Individually validated L1 sensor tilts

`l1_rx` and `l1_ry` use the existing independent stages and Python Controller,
with same-build DD4hep/Mille derivative evidence and a per-iteration angular
information gate. Start from the disabled `calibration/config/l1_rx_demo.json`
or `l1_ry_demo.json`, select a validated build and fresh input/state paths, and
set `tilt_derivative_report` before explicitly enabling calibration. RawHits
remain fixed and candidates remain inactive. The convenience closure runner
refuses these modes because it does not provide their scientific gates.

The final local validation build is `build/tilt_alignment_20261022_05`; its
evidence is `result/tilt_alignment_20261022_01/derivatives_05_L1/report.json`.
These local artifacts are not Git dependencies; a rebuild requires new evidence.
ROOT plots, commands, numerical results and the reason combined tilt modes are
refused are documented in [the tilt report](docs/TILT_ALIGNMENT_VALIDATION.md).
Geometric validation does not certify the nominal uncertainty model.

The explicit SiMAPS `l3_six_dof` and `l1_l2_l3_six_dof` prototypes extend the same SO(3) model to L3 with L0/L4 fixed. They remain disabled by default and require matching technical evidence. See the [independent-stage manual](docs/L3_SIX_DOF_MANUAL.md) and [implementation checkpoint](docs/L3_SIX_DOF_IMPLEMENTATION.md); statistical accuracy and uncertainty coverage are not certified.

Geometry uses the maintained local DD4hep-placement → manual ACTS PlaneSurface path. The optional Blueprint implementation and its reconstruction selector have been removed. The [legacy endcap experiment](docs/LEGACY_ENDCAP_SIMPLIFICATION.md) directly exercises the installed EICrecon provider with a private exact-version converter; relaxing the paired-endcap guard still fails during layer construction. No replacement provider is enabled. The [earlier integration audit](docs/ACTS_GEOMETRY_INTEGRATION.md) remains a historical record with preserved results.

For a code-level handoff, see the [source-based architecture and workflow guide](docs/ARCHITECTURE_AND_WORKFLOW_GUIDE.md), including component provenance, independent stages, alignment equations and remaining validation limits.
