# Global Z translation alignment: scientific validation

Completed locally on 2026-10-22, extending the uncommitted working tree. All study data, commands, retained failures and source snapshots are under `result/z_alignment_20261022_01/`. New build: `build/z_alignment_20261022_01/`. No commit, push, automatic Geometry activation, historical-data replacement or external-installation modification was performed.

## Outcome and scope

**L1 Z-only passed first**, including positive/negative physical injections, fresh physical derivatives, actual Mille entries, profiled observability, iterative correction and actual corrected Reconstruction. L1/L2 Z passed next. The separate XYZ design was then found identifiable and its six-translation controlled correction was tested. All four cases converged in three iterations. These are controlled Geometry/model demonstrations, not statistical certification of parameter errors.

No Rx/Ry, unrestricted all-layer fitting or combined XYZ/Rz alignment is enabled. Existing default `l2_x` correction and `legacy` writer behavior are unchanged. All old X/Y/Rz outputs and the 30-seed Rz statistical findings are retained. Templates remain disabled by default; candidates remain inactive.

## Geometry conventions and physical placement

Coordinates use mm, right-handed active rotations and `p_global = R p_sensor + t`. The measured nominal axes are sensor X → Global +Y, sensor Y → Global −Z, sensor Z → Global −X. Thus a positive Global Z displacement is opposite sensor-local +Y. The ACTS basis remains u = −sensor Z, v = sensor X, n = u×v.

The focused DD4hep factory adds independent per-ring `global_z` to `zstart + dz`. It preserves X/Y, orientation, dimensions, materials, segmentation and Cell IDs; ring radius, phi and Rz are not reused for Z. Only the current centered sensitive component, non-reflected, one-module-per-layer seven-plane hierarchy is validated. Generated XML selects the local factory; nominal XML is unchanged.

Geometry Correction calls the existing frame-aware `RigidTransform.updated(translation=(dx,dy,dz))` on the current placement. It accumulates the independent `global_z` offset from the current XML, rather than repeatedly correcting the original nominal file. `applied_mm_by_component` contains absolute sensitive-center coordinates; step5 `global_z_offsets_mm` contains serialized offsets in mm.

The ±2 mm controlled L1 displacements were chosen before fitting: at |tx|/|ty| ≈ 0.01–0.03 they give 20–60 micrometers transverse response, resolvable with the unchanged ≈10 micrometer measurement errors. L1/L2 injections +2/−1.5 mm leave 46.5 mm between their 0.05 mm-thick SiMAPS planes. All four physical GDML exports passed ROOT overlap/extrusion checks at **0.0001 mm** tolerance (zero overlaps). The representation bounds L1/L2 Z offsets to ±10 mm, preserving plane order and clearance.

## Mille equations, signs and linearization

For the current reconstructed hit `(m_x,m_y,z_g)`, local parameters are `(x0,y0,tx,ty)` about the unchanged numerical coordinate origin `zref=100 mm`. This origin is not a fixed layer placement. For physical Z increment c,

```text
F_x(p,c,a_x) = x0 + tx*(z_g + c - zref) + a_x - m_x
F_y(p,c,a_y) = y0 + ty*(z_g + c - zref) + a_y - m_y
```

At the current Geometry c=0, expand about reconstructed reference slopes:

```text
F_x ≈ F_x(p_ref,0) + delta_x0 + (z_g-zref)*delta_tx + tx_ref*c + a_x
F_y ≈ F_y(p_ref,0) + delta_y0 + (z_g-zref)*delta_ty + ty_ref*c + a_y
```

The second-order products `delta_tx*c` and `delta_ty*c` are omitted in this linear solve. Because the c=0 prediction is linear in p, rewriting local parameters as absolute p cancels the reference constant: the existing Mille RHS remains `m_x/m_y`, with its unchanged four local derivatives. There is no unvalidated bilinear product inside Pede.

| Family | Fitted quantity | Derivative X/Y | Physical correction |
|---|---|---|---|
| 1000+layer | Global X measurement bias, mm | +1 / 0 | negative fitted bias |
| 2000+layer | Global Y measurement bias, mm | 0 / +1 | negative fitted bias |
| 3000+layer | Existing Rz measurement bias, rad | existing definitions unchanged | negative fitted bias |
| **4000+layer** | **Physical Global Z increment, mm** | **tx_ref / ty_ref**, mm/mm | **positive fitted value** |

The new writer path profiles the existing weighted four-local-parameter straight-line model on the **current ACTS-associated reconstructed hits**, with the same per-hit variances and sigma floor used by Mille. This estimates reference trajectories for the alignment linearization, not a new tracking model. It never reads MCParticles or Truth slopes. Slopes are logged at full precision and frozen for each Pede solve. Each external Geometry/reconstruction iteration recomputes them, accounting for the omitted coupling through relinearization. The numerical ACTS fitter, seed covariance, particle hypothesis, process-noise/material assumptions and measurement errors are unchanged.

Legacy and Rz branches do not calculate Z slopes or emit Z labels. XYZ releases X/Y/Z only for L1/L2, keeps L0/L4 anchors and all other placements fixed (including L3). Unlike the older XY steering, XYZ deliberately has no fitted L3 X/Y nuisance parameters; the effect of releasing them is reported as a design-only diagnostic, not used to tune the fit.

## Derivative evidence and Controller gates

Before Controller calibration, each label was checked against physical central differences in fresh DD4hep processes. Fixed channel positions were recomputed with VolumeManager, and fixed reference trajectories were evaluated at the perturbed physical Z. Tests used offsets ±2 mm; epsilon = 0.01, 0.001, 0.0001 mm; positive/negative/zero tx and ty; several impact positions; centers X=+1.25/Y=−0.75 mm; and Rz=0/+0.017 rad. Pure Z changed only Global Z, including for the nonzero Rz case.

| Layer | Fresh-context derivative checks | Actual Mille entries | Zero-slope checks | Max absolute error [mm/mm] | Max relative error |
|---|---:|---:|---:|---:|---:|
| L1 | 756 | 192 | 108 | 1.497e-11 | 7.484e-10 |
| L2 | 756 | 182 | 108 | 2.056e-11 | 1.028e-09 |

Actual float32 derivatives were checked against full-precision writer slope logs and independently rederived weighted slopes from reconstructed hits. Additional binary checks covered all four cases, including both layers in XYZ (`extra_diagnostics.json`). Zero-slope derivatives vanished.

The existing Controller requires `z_derivative_report` and `z_max_nominal_sigma_mm`. Evidence pins both `BeamTestReco.so` and `libLocalTelescopeGeometry.so`, report checksums, selected 4001/4002 labels, successful physical checks and nonempty actual-Mille checks, and the declared linearization. Missing/stale/wrong-plugin/wrong-factory/incomplete evidence is refused before processing. Mode-specific canonical Pede steering is required.

Before every Pede call, `validation.z_observability` forms actual weighted local matrices A and global matrices B from official Mille bytes, profiles the four local parameters of **each track**, and sums `B.T @ (I - A @ pinv(A)) @ B`. Rank is checked on the column-normalized information spectrum (threshold 1e-9). The explicit maximum predicted Z error is 0.5 mm; this is an information/sensitivity guard, not statistical uncertainty calibration.

The new Z templates use a declared 5 mm update guard for the 2 mm injections. Existing historical policies are unchanged. The original 0.005 mm convergence tolerance and maximum three iterations were retained. Pede inversion/rejection settings and errors were not tuned. The convenience closure runner refuses Z modes rather than bypassing these gates.

## Angular coverage and observability

The two-layer sample had 91 accepted tracks. Reference tx/ty means were -0.001243/-0.001248, sample SDs 0.015717/0.013072. Full slope values, covariance, extrema, parameter information/correlation matrices and weak eigenvectors are saved in `two_z_observability.json` and `reference_sensitivity.json`.

Selected Z rank was 2/2, with predicted errors 0.063716/0.059601 mm and correlation +0.2673. Column-normalized eigenvalues were 0.732739–1.267261. Joint XYZ rank was 6/6, eigenvalues 0.669490–1.376650. Adding hypothetical L3 X/Y nuisances retained rank 8/8. The separate actual XYZ sample also passed rank 6/6 before correction.

Z sensitivity is proportional to trajectory slope; X/Y versus Z separation additionally requires angular diversity. For design-only reference sensitivity, releasing Z3 while keeping L0/L4 fixed changes predicted L1/L2 errors to 0.06548/0.06291 mm, versus 0.06372/0.05960 mm with Z3 fixed. Hypothetical L0/L3 references give 0.06407/0.06407 mm. These diagnostics do not change the production references or enable extra fitted DOFs. All-five-Z-free rank is 3/5: common/linear-Z gauges are not identifiable with free straight-line locals.

Negative controls were generated through the **production C++ Mille writer**, not merely a global-column Gram matrix: exact zero slopes were refused at rank 0 (official Pede also aborted with status 22); tiny diverse slopes retained rank but failed the 0.5 mm information guard; a common fixed nonzero angle gave XYZ rank 4/6 and was refused. These are exact synthetic mathematical controls, not claims that a material-traversing Geant4 electron has exactly zero reconstructed slope. No extra angular-distribution Simulation was needed.

## Controlled recovery

All four scenarios used the unchanged canonical 100-event 1 GeV electron configuration, including seed **2035032807**, vertex (0,0,−500) mm, angles, beam widths and material. These are controlled geometries, not a new independent-seed ensemble. Separate output directories were used.

| Case | Component | Injected [mm] | Initial physical estimate ± nominal sigma [mm] | Initial normalized difference | Final cumulative [mm] | Final error [mm] |
|---|---|---:|---:|---:|---:|---:|
| l1 | L1_z | +2.000000 | +1.993600 ± 0.056784 | -0.113 | +1.98573875 | -0.01426125 |
| l1_negative | L1_z | -2.000000 | -2.079900 ± 0.059635 | -1.340 | -2.08861624 | -0.08861624 |
| two_z | L1_z | +2.000000 | +1.955900 ± 0.063579 | -0.694 | +1.94832726 | -0.05167274 |
| two_z | L2_z | -1.500000 | -1.498600 ± 0.059487 | +0.024 | -1.49277772 | +0.00722228 |
| xyz | L1_x | +0.150000 | +0.148360 ± 0.001302 | -1.260 | +0.14778517 | -0.00221483 |
| xyz | L2_x | +0.200000 | +0.194270 ± 0.001218 | -4.706 | +0.19474633 | -0.00525367 |
| xyz | L1_y | -0.120000 | -0.116850 ± 0.001304 | +2.416 | -0.11639739 | +0.00360261 |
| xyz | L2_y | +0.090000 | +0.094366 ± 0.001220 | +3.580 | +0.09399315 | +0.00399315 |
| xyz | L1_z | +2.000000 | +1.942800 ± 0.063814 | -0.896 | +1.93527490 | -0.06472510 |
| xyz | L2_z | -1.500000 | -1.600700 ± 0.059707 | -1.687 | -1.59462174 | -0.09462174 |

The initial normalized difference uses only the corresponding initial-fit nominal error. It is not an ensemble Pull validation. Final cumulative values come from saved XML matrices, not sums with independent-error assumptions. Successive fits share RawHits; their uncertainties were not combined in quadrature. XYZ coordinates demonstrate identifiable correction and small physical offsets, but several transverse differences are multiple nominal sigmas: they are explicitly **not** certified unbiased/covered at the nominal precision.

| Case | Accepted tracks | ACTS chi2/stored-NDF before → exact final | Pede chi2/NDF initial → last solve |
|---|---:|---:|---:|
| l1 | 96 | 2.400801 → 1.118366 | 1.863899 → 1.863846 |
| l1_negative | 93 | 2.641991 → 1.339137 | 2.234034 → 2.233967 |
| two_z | 91 | 3.707230 → 1.346348 | 2.251676 → 2.251559 |
| xyz | 91 | 57.811968 → 1.370499 | 2.306319 → 2.306213 |

ACTS stored-NDF is 10 per accepted five-plane track, not the four-local-parameter statistical NDF. Pede subtracts local parameters and the selected global count. All 12 controlled iterative Pede calls had process exit code 0, status **1 (warnings: bad measurements)** and zero rejected local fits at every recorded function evaluation. Warning status is retained: chi2/NDF is significantly above one. Full errors and rejection tables are in the ROOT summaries and original logs. No error rescaling was applied.

Per-iteration physical increments [mm] (X/Y signs already converted from biases):

| Case / iteration | Applied increment by component |
|---|---|
| l1 / 1 | `L1_z=+1.9936` |
| l1 / 2 | `L1_z=-0.0078615` |
| l1 / 3 | `L1_z=+2.4812e-07` |
| l1_negative / 1 | `L1_z=-2.0799` |
| l1_negative / 2 | `L1_z=-0.0087162` |
| l1_negative / 3 | `L1_z=-3.9291e-08` |
| two_z / 1 | `L1_z=+1.9559, L2_z=-1.4986` |
| two_z / 2 | `L1_z=-0.0075704, L2_z=+0.0058216` |
| two_z / 3 | `L1_z=-2.3431e-06, L2_z=+6.7719e-07` |
| xyz / 1 | `L1_x=+0.14836, L1_y=-0.11685, L1_z=+1.9428, L2_x=+0.19427, L2_y=+0.094366, L2_z=-1.6007` |
| xyz / 2 | `L1_x=-0.00057485, L1_y=+0.00045264, L1_z=-0.0075205, L2_x=+0.00047635, L2_y=-0.00037283, L2_z=+0.0060743` |
| xyz / 3 | `L1_x=+1.6102e-08, L1_y=-2.6595e-08, L1_z=-4.5963e-06, L2_x=-1.9572e-08, L2_y=-1.6861e-08, L2_z=+3.9564e-06` |

## DD4hep, GDML, ACTS and residual validation

VolumeManager probes and independent ROOT GDML imports verified all seven centers/orientations. The first corrected Geometry and exact final candidate were both reconstructed and checked against fresh contexts: RecHit XYZ equals the converter’s float32 position, ACTS surface centers/bases follow the selected sensitive contexts, local Measurement2D coordinates round-trip correctly, and the existing sensor-X/Z to plane-u/v covariance interpretation remains unchanged. The physical, first and final GDML matrices all passed. Unselected placements and orientations were preserved.

The fitter obtains its per-layer Z from `SurfacePlacements.h`, seeds from current global hit positions on the validated input path, and propagates using the existing DirectNavigator/Kalman model. It does not substitute nominal layer spacing. Layer-index traversal remains geometrically ordered for the bounded offsets. No numerical fitter code was edited.

ROOT outputs are under `l1_root_v2/`, `l1_negative_root/`, `two_z_root/`, and `xyz_root/`: `z_alignment.root`, `geometry.root`, PDF canvases and numerical summaries. Supplemental `observability.root` files contain tx/ty distributions, joint angular coverage and profiled XYZ correlation matrices. Plots include G0/physical/final placements, matched RecHit−SimHit X/Y/Z, profiled local track residuals, cumulative Z positions and ACTS quality. Truth is loaded only after inference for these validation plots. For pure Z, unchanged transverse Rec−Sim is expected: channel centers keep X/Y while their Z changes. Track residuals and Hit Residuals in Z carry the relevant correction signature.

An explicitly retained anomaly occurs in negative-case event 58: an L1-tagged SimHit is at Z=74 mm, has path length 0.099311 mm, and no L2 SimHit is present; nominal physical centers are Z=48 and 100 mm. The unchanged DDSim action is `Geant4TrackerWeightedAction` with `HitPositionCombination=2`, `CollectSingleDeposits=False`. The midpoint/doubled-length observation is consistent with hit aggregation, but its precise sensitive-action lifecycle cause was not established here. Fresh physical Geometry is not at 74 mm. This event has **no accepted track**, so it did not enter Mille alignment. It is not removed from residual plots. Its presence changes the unfiltered matched L1 Z mean from +1.737374 to −0.351242 mm; the median is +2.000000 → −0.088615 mm, consistent with the final physical offset. Other cases’ matched Z means follow their reported physical errors. See `negative_hit_event58.json`, `negative_truth_z_anomaly.log`, and `extra_diagnostics.json`. A future hit-aggregation/association investigation is separate from this Z correction task.

### Residual response

These are RMS values about zero for the profiled four-local-parameter straight-line residuals (RecHit minus prediction), in micrometers; they are computed from selected reconstructed measurements without Truth.

| Case | Layer | Track residual RMS X before → after [um] | Y before → after [um] |
|---|---|---:|---:|
| l1 | L1 | 23.869 → 10.994 | 22.948 → 9.009 |
| l1_negative | L1 | 23.558 → 10.931 | 24.235 → 10.420 |
| two_z | L1 | 27.529 → 9.821 | 24.813 → 10.907 |
| two_z | L2 | 29.403 → 15.438 | 24.262 → 12.726 |
| xyz | L1 | 72.441 → 10.358 | 100.881 → 8.980 |
| xyz | L2 | 128.053 → 16.253 | 99.454 → 12.777 |

Pede chi2 is evaluated after solving its local/global model, while the initial ACTS quality uses uncorrected G0. They are not the same before/after statistic. The two fitting models and seed treatment also differ; no equality was imposed.

Z alignment is relative to the fixed surveyed reference planes. A common Z translation or longitudinal scale cannot be established from unconstrained straight-track intercepts/slopes alone; no new beam-vertex constraint was introduced.

## Regression and safety results

- Clean dedicated CMake configure/build completed. `ldd` resolves `/work/external/install/lib/libMille2.so`; RUNPATH includes that official prefix. Existing build trees/installations were not reused as outputs.
- Historical L2 X full seven-stage closure and ROOT checks passed: **99 tracks**, correction +0.19875 mm, L2 residual −199.571 → −0.821 micrometers, ACTS ratio 45.592 → 1.981.
- Historical L1/L2 X, XY and truth-free survey Controllers converged to exactly the previous candidate Geometry IDs.
- L1 Rz, L1/L2 Rz and L1/L2 XY/Rz Controllers likewise reproduced their previous candidate IDs using fresh same-build derivative evidence.
- Legacy X/XY and all three Rz replays produced byte-identical Mille files. Existing X/Y finite differences passed (36 checks); existing Rz finite differences passed for each layer (108 physical checks / 196 actual entries each).
- Combined-versus-split RawHit/PODIO downstream comparison, Mille byte comparison and Pede parameter comparison passed.
- **31 tests passed**, covering old transforms, correction, RawHit, Controller and Rz behavior plus Z signs, composition, scope, evidence freshness and weak-design refusal. Unit-test ResourceWarnings about existing test-fixture file handles were retained; tests exited successfully.
- Real CLI safety/refusal checks passed. The former blanket unsupported-Z fixture now tests unsupported Z layers and Rx/Ry; an explicit ungated-Z convenience-runner refusal was added.
- Preservation checks passed: 221 baseline records and 2,046 relocated files, including the electron-fitter source pin. Full task-start data/source audits and completed-stage integrity checks are recorded in `final_audit.json`.
- Python compilation, Shell syntax and `git diff --check` passed. No existing source/data manifest was weakened or edited.

## Changed and new maintained files

Modified relative to task start:

- `README.md`
- `alignment/align.py`
- `calibration/README.md`
- `calibration/iteration.py`
- `calibration/settings.py`
- `correction/correct_geometry.py`
- `correction/scope.py`
- `docs/GEOMETRY_CONVENTIONS.md`
- `docs/WORKFLOW.md`
- `geometry/placements.py`
- `geometry/prepare.py`
- `localDetEICrecon/alignment/src/BeamTestMilleWriter.cc`
- `localDetEICrecon/alignment/src/BeamTestMilleWriter.h`
- `localDetEICrecon/geometry/SiTrackerEndcap2XY_geo.cpp`
- `localDetEICrecon/processors/BeamTestMilleProcessor.cc`
- `reconstruction/reconstruct.py`
- `validation/README.md`
- `validation/check_safety.py`
- `validation/run_closure.sh`
- `validation/test_rotation.py`

New maintained files:

- `docs/Z_ALIGNMENT_VALIDATION.md`
- `alignment/pede_l1_l2_xyz.txt`
- `alignment/pede_l1_l2_z.txt`
- `alignment/pede_l1_z.txt`
- `calibration/config/l1_l2_xyz_demo.json`
- `calibration/config/l1_l2_z_demo.json`
- `calibration/config/l1_z_demo.json`
- `geometry/scenarios/L1_L2_xyz.json`
- `geometry/scenarios/L1_L2_xyz_reference.json`
- `geometry/scenarios/L1_L2_z.json`
- `geometry/scenarios/L1_L2_z_reference.json`
- `geometry/scenarios/L1_z2mm.json`
- `geometry/scenarios/L1_z_reference.json`
- `geometry/scenarios/L1_zminus2mm.json`
- `validation/test_z_alignment.py`
- `validation/validate_z_derivatives.py`
- `validation/z_observability.py`
- `visualization/z_alignment.py`

The final source snapshot and exact changes from task start are saved under the study root. Prior uncommitted work, the electron hypothesis, the empty user `bash` file and user scenarios remain. The external EICrecon source tree is untouched.

## Exact commands, configuration and outputs

Run host commands from the repository root; the container sees it at `/work`. Every maintained stage also saves `command.json`, stdout and exit status. New orchestration/check harnesses below are study artifacts using the existing modules and Controller, not a second controller. They refuse preexisting case/output directories.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/z_alignment_20261022_01 BUILD_JOBS=2 bash environment/build.sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/z_alignment_20261022_01 python3 -m geometry.prepare --result-dir result/z_alignment_20261022_01/l1 --geometry-config geometry/scenarios/L1_z2mm.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_l1_stages.py
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/z_alignment_20261022_01 python3 -m validation.validate_z_derivatives --geometry geometry/nominal/seven_layer_telescope.xml --mille result/z_alignment_20261022_01/l1/step3/mille.dat --reco result/z_alignment_20261022_01/l1/step3/reco.root --output result/z_alignment_20261022_01/l1_derivatives --layer 1
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m validation.z_observability --mille result/z_alignment_20261022_01/l1/step3/mille.dat --mode l1_z --output result/z_alignment_20261022_01/l1_observability.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m alignment.align --result-dir result/z_alignment_20261022_01/l1 --steering alignment/pede_l1_z.txt
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/l1_correct_reconstruct.py
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_controller_case.py l1_controller /work/result/z_alignment_20261022_01/l1 l1_z /work/result/z_alignment_20261022_01/l1_derivatives/gate.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_data_case.py l1_negative geometry/scenarios/L1_zminus2mm.json l1_z
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_controller_case.py l1_negative_controller /work/result/z_alignment_20261022_01/l1_negative l1_z /work/result/z_alignment_20261022_01/l1_derivatives/gate.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_data_case.py two_z geometry/scenarios/L1_L2_z.json l1_l2_z
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/z_alignment_20261022_01 python3 -m validation.validate_z_derivatives --geometry geometry/nominal/seven_layer_telescope.xml --mille result/z_alignment_20261022_01/two_z/step3/mille.dat --reco result/z_alignment_20261022_01/two_z/step3/reco.root --output result/z_alignment_20261022_01/l2_derivatives --layer 2 --additional-gate result/z_alignment_20261022_01/l1_derivatives/gate.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_controller_case.py two_z_controller /work/result/z_alignment_20261022_01/two_z l1_l2_z /work/result/z_alignment_20261022_01/l2_derivatives/gate.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_data_case.py xyz geometry/scenarios/L1_L2_xyz.json l1_l2_xyz
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m validation.z_observability --mille result/z_alignment_20261022_01/xyz/step3/mille.dat --mode l1_l2_xyz --output result/z_alignment_20261022_01/xyz_observability.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/z_alignment_20261022_01/run_controller_case.py xyz_controller /work/result/z_alignment_20261022_01/xyz l1_l2_xyz /work/result/z_alignment_20261022_01/l2_derivatives/gate.json
```

Underlying controlled Controller command:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m calibration.controller once --config result/z_alignment_20261022_01/two_z_controller/controller.json --input-dir result/z_alignment_20261022_01/two_z_controller/input --state-dir result/z_alignment_20261022_01/two_z_controller/state
```

That existing state is completed and must not be repurposed. For a new study use fresh paths and an explicitly configured copy of `calibration/config/l1_z_demo.json`, `l1_l2_z_demo.json` or `l1_l2_xyz_demo.json`. Set `build_dir`, enable calibration, and point the derivative gate to evidence from that exact build. Input manifests are `rawhit-delivery-v1`; the driver creates closed RawHit and Truth-excluded metadata copies before writing readiness. Source Simulation and digitized files stay intact.

| Stage | Input | New output |
|---|---|---|
| Geometry | unchanged nominal + scenario JSON | CASE/step1 XML, GDML, placement QA |
| Simulation | CASE/step1/misaligned.xml + canonical electron JSON | CASE/step2/events.edm4hep.root |
| Digitization | Simulation + physical readout Geometry | CASE/step2_digitization/rawhits.edm4eic.root + contract |
| Initial reconstruction | saved RawHits + nominal/reference + explicit mode | CASE/step3 reco.root + official mille.dat |
| Controller delivery | identical RawHit bytes + Truth-excluded contract + ready manifest | STATE/input snapshot and persistent queue |
| Iteration | current immutable Geometry + fixed RawHits | iteration-NNN/step3, z_observability.json, step4, step5 |
| Final reconstruction | exact inactive candidate + same RawHits | CONTROLLER/final/step3 |
| Validation | before/final + optional Truth | ROOT directories, scientific_summary.json, Geometry proofs |

Additional exact commands for all regressions, exports, previews and safety checks are in `COMMANDS.md` and case harnesses/logs. Open ROOT files with `root -l result/z_alignment_20261022_01/two_z_root/z_alignment.root` and `new TBrowser;`; `geometry.root` contains the explicit G0/Simulation/final comparison. ROOT PNG previews are supplemental exports only.

Retained partial failures: the first standalone GDML export omitted `geometry_environment`, aborted before export, and was retried in new `_v2` directories using the maintained factory environment. The first Z plotting attempt reused a Rz-only error parser, failed after partial plotting, and remains in `l1_root/`; the Z-aware parser succeeded in fresh `l1_root_v2/`. Expected negative-control Pede/observability failures remain. No failed output was overwritten or silently counted as a pass.

## Limitations and next milestone

This validates physical Z placement, sign, slope-dependent local linearization, selected-mode observability, fixed-RawHit iterative Geometry composition and compatibility with prior modes. It does not validate arbitrary layouts, tilts, reflected placements, anisotropic rotated Mille covariances, or a full six-DOF fit. It does not statistically validate errors: the retained 30-seed Rz widths 1.433/1.661 and mean Pede chi2/NDF ≈2.340 remain known limitations. Z/XYZ chi2 and multiple-nominal-sigma transverse offsets reinforce the need to keep physical accuracy separate from formal precision. No errors or Pede settings were changed to improve agreement.

The next development priority is a separately scoped uncertainty/error-model and hit-aggregation/association investigation before claiming nominal precision or adding tilt DOFs. A future independent-data Z stability check would be informative, but no new 30-seed or muon campaign was launched here. Geometry activation still requires independent validation and explicit operator approval.
