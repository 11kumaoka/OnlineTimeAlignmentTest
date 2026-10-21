# Local Detector Alignment Research

Independent DD4hep/EICrecon research tasks: Detector Geometry → Simulation →
Digitization / Hit Reconstruction / Track Fitting → Mille Binary → Millepede-II →
Geometry Correction → reconstruction of the same events → Closure Validation.

The supported example is a seven-plane telescope: five SiMAPS planes, MPGD, and
AC-LGAD. Geometry Preparation supports SiMAPS Global X scenarios. Geometry
Correction and full Closure remain limited to **L2 Global X**.

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

## Seven independent commands

Choose a new result directory. Stop and inspect after any command:

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/electron_001 --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh bash simulation/simulate.sh --result-dir result/electron_001 --config simulation/configs/electron_1GeV.json
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/electron_001 --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/electron_001 --steering alignment/pede_template.txt
bash environment/run.sh bash correction/correct_geometry.sh --result-dir result/electron_001
bash environment/run.sh bash reconstruction/reconstruct_corrected.sh --result-dir result/electron_001
bash environment/run.sh bash validation/validate.sh --result-dir result/electron_001
```

Each command runs only its stage. Existing step directories are never overwritten.
New outputs are `result/electron_001/step1/` through `step7/`. Historical
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
reconstruction/     editable fit settings and EICrecon command construction
alignment/          Pede steering and external solver execution/parsing
correction/         L2 Global X Geometry Correction
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

## Two-layer Geometry only

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/two_layer_001 --geometry-config geometry/scenarios/L1_x100um_L2_x200um.json
```

Inspect `step1/placement_check.json` and `step1/misaligned.xml`. L1 is shifted
+0.100 mm and L2 +0.200 mm. No Simulation runs during preparation. Do not continue
this study to multi-layer Closure yet: correction and validation reject nonzero
shifts outside L2. Pede's existing L1–L3 X/Y parameter model is unchanged.

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
