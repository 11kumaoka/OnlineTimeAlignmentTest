# SiMAPS L3 and three-layer six-DOF implementation checkpoint

## Status and scope

`l3_six_dof` and `l1_l2_l3_six_dof` are implemented, opt-in prototypes.
Basic build, Geometry, derivative, rank and independent-stage integration
checks passed. The new three-layer mode has **not** passed a complete noisy
physical alignment closure or a statistical accuracy/uncertainty study.
Templates remain disabled; no candidate was activated. No commit or push was
performed. Detailed studies are deliberately left to the researcher.

Evidence: `result/l3_six_dof_20261023_01/`. Fresh build:
`build/l3_six_dof_20261023_01/`. The [manual guide](L3_SIX_DOF_MANUAL.md)
contains individually executable commands, inputs/outputs, inspection points,
CHECK-ONLY/WRITES OUTPUT labels and optional existing Controller use.

## Implementation

`correction/scope.py` now holds an explicit SO(3) mode-to-layer registry,
`layers_for`, `fixed_layers_for`, `selected_labels`, and the existing per-axis
parameter specification. The registered three-layer scope is `(1,2,3)` and its
fixed SiMAPS references are `(0,4)`; L3-only fixes `(0,1,2,4)`. Arbitrary detectors
or all-plane fitting are not exposed. Historical scopes and defaults are retained.

The production C++ writer already uses five-element per-layer arrays. Its
numerical code and derivative model are **unchanged in this task**. The Processor
selects the explicit supported layer range, clears default Rx/Ry flags before
coupled selection, and populates poses from actual DD4hep sensitive contexts.
New canonical steering fixes unselected X/Y columns and releases each selected
label exactly once. No additional L3 nuisance parameters are accidentally
released. Historical `pede_template.txt` and all existing steering files remain
byte-identical to task start, including their historical L3 X/Y nuisance choices.
Official Pede method/rejection settings are unchanged.

Geometry preparation and the focused local factory extend their placement
bounds from L1/L2 to L1/L2/L3. The single centered sensitive module, nonreflection,
readout, matrix orthonormality and finite-value guards remain. No nominal L3
position constant was introduced. `SurfacePlacements.h` and the numerical ACTS
fitter are unchanged; the selected Geometry supplies centers and bases.

Correction reuses the same current-Geometry algorithm:
`Rnew=Exp([w]x) Rcurrent` about the current sensitive center, followed by Global
translation. Full matrices are serialized/reloaded; selected scope checks preserve
unselected placements and the material/readout hierarchy. No Euler-angle sums
or restart-from-nominal updates were introduced.

### Labels, signs and units

The sign column converts a Pede estimate to a **physical Geometry increment**.

| Component | L1 label | L2 label | L3 label | Physical increment | Unit |
|---|---:|---:|---:|---|---|
| Global X | 1001 | 1002 | 1003 | negative fitted bias | mm |
| Global Y | 2001 | 2002 | 2003 | negative fitted bias | mm |
| Global Rz | 3001 | 3002 | 3003 | negative fitted bias | rad |
| Global Z | 4001 | 4002 | 4003 | positive fitted value | mm |
| Global Rx | 5001 | 5002 | 5003 | positive fitted value | rad |
| Global Ry | 6001 | 6002 | 6003 | positive fitted value | rad |

Thus `w=(p5000,p6000,-p3000)`, `d=(-p1000,-p2000,+p4000)` per layer.
All five SiMAPS planes enter tracking, with four local straight-line parameters
profiled per track. L0/L4 are fixed reference sensors, not released globals.
MPGD/AC-LGAD hits do not enter these fits. Reference constraints and rank tests
apply to this telescope and sample; no generic six-DOF observability is claimed.

### Controller and evidence

The existing once/watch Controller, RawHit delivery, Survey fallback, sequential
worker, iteration stages, immutable candidate registry and explicit activation
interface are reused. The new scopes automatically enter the same parameter
loops: nine angular and nine linear components must all satisfy their separate
rad/mm thresholds for convergence. Templates retain explicitly labeled
provisional demonstration bounds, not certified acceptance criteria.

New evidence is `gate.json`, generated from three physical derivative reports
and eleven source-pinned mathematical controls. It pins the plugin, factory,
writer and implementation sources, including the selection/placement adapters.
Every selected label must be covered by the underlying physical reports.
The new L3 scopes reject absent source pins; any changed pinned source is
refused even before a binary rebuild. The old release gate remains historical.
`evidence_guards.json` verifies acceptance of matched L3 and existing L1/L2
scopes, rejection of the old gate, missing L3 proof and stale source fingerprints.
No activation behavior was changed.

## Executed limited checks

Container: `sweet_mahavira`, repository `/work`. Commands were invoked from the
host using `TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh ...`.
`build.log`, per-stage `command.json`/`exit.json`, and the task helper command
records retain the exact executed arguments. Helpers under this ignored result
directory are reproducibility records, not new framework entry points.

### Build and static/unit checks

- Fresh configure/build via `env TESTBENCH_BUILD_DIR=/work/build/l3_six_dof_20261023_01 bash environment/build.sh`: exit 0.
- 46 unit tests: pass, including new exact label/steering/reference checks and
  repeated current-Geometry corrections on L3 and all three layers.
- 63 Python files parse; 14 shell scripts pass `bash -n`; `git diff --check` passes.
- Existing safety and preservation checks pass, including new refusal checks
  for ungated L3 convenience-runner requests.
- `ldd` resolves `libMille2.so` to `/work/external/install/lib/libMille2.so`;
  CMake cache/link command contain no old `seven_layer/millepede` fallback.

Earlier host unit execution lacked NumPy and exposed tests that still expected
L3 to be unsupported. They remain in `unit_host.log`. Unsupported-sensor tests
now use fixed L4; historical mode scope checks are retained. The first safety
attempt similarly had old L3 rejection cases; its failure is retained in
`safety_release.log`. Final container checks are `release_checks.json`
and `*_final.log`.

### Physical derivatives and Geometry

Each layer was checked using:

```sh
python3 -m validation.validate_tilt_derivatives --layer 3 --coupled \
  --representative --build-dir build/l3_six_dof_20261023_01 \
  --output result/l3_six_dof_20261023_01/derivatives_L3
```

L1 and L2 used the same command with their own new output paths. This checks
all six physical columns in a mixed orientation at three channels and three
slopes, freezing the reference trajectory and covariance within each finite
difference. Epsilon is 1e-4 mm/rad as appropriate. The full historical suite is
still the default when `--representative` is omitted.

| Scope | Fresh DD4hep contexts | Two-component FD comparisons | Decoded binary components |
|---|---:|---:|---:|
| L1 | 13 | 54 | 108 |
| L2 | 13 | 54 | 108 |
| L3 | 13 | 54 | 108 |

Largest physical derivative absolute difference: 1.7430e-8 (rotation mm/rad;
translation comparisons use mm/mm). Largest whitened float32 coefficient
absolute difference: 5.1857e-5; existing relative/absolute checks pass. Decoded
components include implicit zeros, not solely stored nonzero entries.

`survey_geometry.json` and `corrected_geometry.json` verify actual RecHit float32
coordinates, all seven ACTS surface centers/bases, local/global round trips,
475 Measurement2D coordinates and covariances per reconstruction, and 475 each
predicted/filtered/smoothed points and Global covariance transformations.
Each checks 506 SiMAPS RecHits. Point distances/covariances pass the established
propagated float32 bounds; no tolerances were loosened.

### Mathematical control and preserved capture failure

`noiseless/three_six_dof/iteration-001/` preserves the initial official Pede
status-26 failure (“too many rejects”). Its selected rank was full. The target
used existing large coupled angles from the prior fixture with nominal starting
orientations. Rejection before successful inference is not mathematical closure
and is not reported as a pass.

A declared closer-Survey control uses half the target orientation in the
three-layer fixture only; fixed continuous local coordinates, uncertainties,
production writer and Pede settings are unchanged. This is selected explicitly:

```sh
python3 -m validation.so3_closure \
  --writer-fixture result/l3_six_dof_20261023_01/derivatives_L3/writer_fixture \
  --output result/l3_six_dof_20261023_01/noiseless_survey \
  --translation-scale .25 --three-layer-survey-fraction .5
```

All eleven current-source mathematical cases passed, including both new scopes.
The three-layer case required three corrections: final orientation errors
L1/L2/L3 = 0.386/0.191/0.201 urad, largest center error = 5.44e-6 mm.
This establishes the tested algebra/serialization/correction behavior from that
Survey, **not** a general capture range or noisy physical closure. The failed
and successful starts are both preserved; errors and solver steering were not tuned.

### One physical 100-event integration sample

Only **one new Geant4 sample**, 100 events, 1 GeV electrons, seed **2035102301**,
was generated. Other physics settings match `simulation/configs/electron_1GeV.json`.
The physical and approximate Survey scenarios are those in the manual guide.
The independent stages completed Geometry, Simulation, Digitization, RawHit-only
reconstruction/Mille, rank check, official Pede, current-Geometry correction,
corrected reconstruction and ROOT rendering. See `integration.py`,
`*_command.json`, `integration.json` and `three_plane_smoke/`.

- 95 accepted tracks before and after; 95 Mille records/950 scalar measurements.
- Actual selected rank **18/18**, column-normalized information condition **13.7103**.
  This uses actual emitted columns, not the old hypothetical L3 augmentation.
- ACTS chi2/stored-NDF: **25.2814 → 1.26429** after one correction.
- Pede process exit 0, end status **1: warnings (bad measurements)**.
- RawHit SHA-256 before/after:
  `1b54c7b5d91cc59fce1fb6dd1e5b9338c1d930db41369f7728f165d78942582e`.
- ROOT output: `manual_root/tilt_alignment.root`, PDFs and `summary.json`.
  Detector Geometry, all selected-layer Hit Residuals, physical corrections,
  relative orientation and chi2 diagnostics are available in TBrowser.

This is one correction, not convergence or an unbiased-parameter result. In
particular, low chi2 does not establish accurate Rx/Ry recovery at 100 events.
Reported nominal errors and weak modes remain formal model diagnostics.

### Existing Controller integration pilot

`controller.json` explicitly enables the new mode for this task only, uses a
truth-free copy of the same RawHits under `input/l3_six_dof_20261023_01/`, and
caps iterations at **three**. `controller_once_command.json` records the actual
once command. All three iterations completed with rank 18, 18 convergence
components, unchanged RawHit hashes and verified immutable candidate parents.

The pilot **did not converge at its declared cap**. The Controller correctly
marked it `not_converged`, retained its artifacts/candidates and exited **1**.
The final assessed update still had maximum 2.232 mrad and 0.0408 mm components;
ACTS chi2/stored-NDF at that reconstruction was 1.2371. No continuation or relaxed
threshold was used to obtain a passing closure. `controller_audit.json` verifies
integration invariants separately from the retained failure outcome.
The active Survey remains
`geo-76791852facfe5570bd6295010d4da26e63d3e6e7861169c165401fddaa130e2`.
Watch mode's existing shared processing path was preserved; no new live-watch
campaign was run.

### Essential regressions

| Check | Result |
|---|---|
| Historical L2-only accepted tracks | 99 |
| Historical L2 physical correction | +198.75 um |
| Historical L2 pooled Rec-Sim X mean | -199.571376 → -0.821365 um |
| Historical ACTS chi2/stored-NDF | 45.592235 → 1.981040 |
| Existing L1/L2 six-DOF first/final reconstruction | 98 tracks, exact Mille bytes and ACTS metrics |
| Existing L1/L2 initial Pede/correction | byte-identical Pede result and identical corrected poses |

The L2 replay used the existing protected 100-event ROOT input; its seven-stage
runner, reference comparison and ROOT output verification passed. L1/L2 reused
its compatible saved RawHits, actual Geometries and initial/final outputs.
Evidence: `l2_x_regression/step7/summary.json`, `old_six_regression.json`.
No extra 1,000-event simulation, ensemble, muon study or uncertainty tuning ran.

## Preservation, files and remaining work

`source_before.tar.gz` plus `preexisting_unmodified_supplement.tar.gz` protect all
215 pre-task maintained files, including untracked implementations. Git status
and the full pre-task diff are retained. `protected_data_sha256.json` inventories
41,028 pre-existing files under result/results/test/external/install; the final
preservation audit records their comparison. Previous snapshots, builds,
failed tests and historical validation studies were not removed or reused.
The numerical fitter/electron hypothesis, nominal Geometry, writer numerical
implementation and existing steering retain their task-start bytes.

The machine-readable `changes_from_task_start.json` lists created/modified files.
Changes concern scope selection, placement bounds, dedicated steering, disabled
configuration/scenario examples, versioned evidence/fixtures, safety/unit checks,
manual ROOT access and documentation. No new tracking algorithm, Controller,
solver, measurement uncertainty, external installation or detector type was added.

Next scientific work: investigate capture range and Pede rejection/selection,
complete iterative noisy closure from independent Surveys, evaluate all full
matrix/center errors, inspect actual weak-mode correlations, then study initial
nominal-error coverage across independent seeds. Until then these new modes
remain **implementation prototypes with limited integration evidence**.
