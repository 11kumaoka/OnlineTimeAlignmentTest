# Sensor in-plane rotation alignment validation

Validated locally on 2026-10-22 using the existing container `sweet_mahavira`.
All new numerical artifacts, retained failures, source snapshot and command
harnesses are under `result/rz_alignment_20261022_01/`. No commit, push,
Geometry activation, historical-data replacement or external installation change
was performed. The local working tree, including the uncommitted electron
hypothesis and XY foundation, was the starting point.

## Scope and conventions

Validation proceeded in order: **L1 Rz**, **L1/L2 Rz**, then **L1/L2 X/Y/Rz**.
The new explicit modes are `l1_rz`, `l1_l2_rz`, and `l1_l2_xy_rz`.
Existing `l2_x`, `l1_l2_x`, `l1_l2_xy`, the default correction mode, the
historical steering, the nominal XML and the numerical ACTS fitter are unchanged.
Global Z translation, X/Y tilts, other sensor rotations, MPGD/AC-LGAD alignment
and production E0 interfaces remain unsupported.

All rotations are right-handed active rotations around **Global +Z**, in radians:

```text
Qz(theta) = [[cos(theta), -sin(theta), 0],
             [sin(theta),  cos(theta), 0],
             [0,           0,          1]]
```

The measured nominal sensor axes are X → Global +Y, Y → Global −Z,
Z → Global −X. Therefore positive Global Z rotation is **negative sensor-Y
rotation**. The ACTS basis remains u = −sensor Z, v = sensor X, n = u × v.
The normal stays Global +Z for the supported in-plane rotations.

Each pivot is its **current physical sensitive-plane center**, in Global mm.
A pure rotation preserves that center. Correction calls the existing
`RigidTransform.updated(rotation=Qz, pivot=current.translation, translation=d)`;
this left-composes the current matrix and adds the selected Global X/Y update.
It does not restart from nominal or add Euler angles as a general operation.
`atan2(R[1][0],R[0][0])` only serializes the resulting SO(2) orientation.
XML translations retain eight decimal places in mm; angles use fourteen decimal
places in radians.

The focused DD4hep factory adds `global_rz` to the original module orientation,
about its center. It does **not** change ring phi or rotate the center around the
world origin. The existing `Local_SiTrackerEndcap2XY` registration is retained.
This is restricted to the current non-reflected, one-module-per-layer telescope,
with its centered sensitive component. It is not arbitrary-layout support.
Materials, segmentation, Cell IDs and unselected placements are retained.

## Mille equations, labels and derivative validation

For each five-plane track, four local parameters describe two straight lines:
`(x0, y0, tx, ty)`, with z reference 100 mm. Measurements are Global X/Y.
The residual convention is `F = prediction + bias - measurement`.

| Label | Quantity | Units | Physical correction |
|---|---|---|---|
| 1000 + layer | Global X measurement bias | mm | −bias |
| 2000 + layer | Global Y measurement bias | mm | −bias |
| 3000 + layer, only 3001/3002 enabled | Global Z rotational measurement bias | rad | −bias |

For physical angle c and pivot `(cx,cy)`, `dm/dc = (-(y-cy), x-cx)`.
Since c = −a for the fitted bias, the actual Mille derivatives are
`dF/da_rz = (-(y-cy), x-cx)` in **mm/rad**. The selected DD4hep context supplies
the pivot; Simulation Truth is not read by the writer or correction.
Default `legacy` writing retains its old bytes. The final L1-only binary was
also byte-identical to the first validated L1 implementation for the same input.

`validation.validate_rz_derivatives` launches a fresh DD4hep process for every
physical perturbation. It checks both residual coordinates at:

- Current angles 0, +0.017 and −0.023 rad.
- Angular steps 1e-3, 1e-4, 1e-5 and 1e-6 rad, with both signs.
- Three signed channel-coordinate pairs and three slope/impact sets.
- Nonzero pivots `(1.25,−0.75,50)` and `(1.25,−0.75,100)` mm.

There were **108 vector residual checks per layer**, 216 total, with both
coordinate derivatives checked in each vector. Separately, every actual binary
entry matched its associated RecHit/pivot expression at float32 precision:
**196 entries for each label**. Nonzero current centers and both angle signs
were additionally checked in reconstructed binaries; the combined corrected
sample passed 196 entries for each label using its fresh DD4hep pivots.

| Angular step (rad) | Maximum absolute derivative error (mm/rad), either layer |
|---:|---:|
| 1e-3 | 1.74358e-6 |
| 1e-4 | 1.74318e-8 |
| 1e-5 | 2.70433e-10 |
| 1e-6 | 1.13251e-9 |

The maximum relative error was 1.66667e-7. The expected central-difference
quadratic convergence gives way to cancellation at the smallest step. Cross
coordinates, zero angle and fixed-center behavior passed. No stale RecHit or
cached nominal surface was used for the physical perturbations.

The controller requires a matching tested BeamTestReco checksum, immutable
finite-difference report checksums, coverage of all selected labels and the
constrained mode-specific steering. A different plugin, missing label or changed
report is refused. Angular convergence/update bounds are separate from mm bounds.

## DD4hep, GDML, ACTS and covariance checks

Independent ROOT import of exported GDML verified all seven module centers and
plane matrices, in explicit ROOT Geant4 units (mm). Matrix tolerance was 1e-10;
center tolerance was 1e-8 mm. This tests actual GDML rotations, rather than
interpreting near-gimbal-lock Euler numbers as an in-plane angle.

Fresh sensitive VolumeManager contexts verified selected ACTS centers, u/v/n,
CellID positions and local/global transformations. For each 100-event corrected
sample, **502 RecHits** matched fresh converter positions exactly at stored
float32 precision; **490 Measurement2D coordinates and covariances** passed.
All 14 actual surface instances (two JANA factory initializations) passed the
C++ local/global round-trip check at 1e-10 mm. The 1,000-event final candidate
also passed all of its RecHit/measurement checks; counts are in
`large_candidate/geometry_check.json`.

The initial L1 writer also called the shared placement diagnostic helper, giving
21 context diagnostics but only 14 actual surfaces. The probe distinguishes
context reads from surface construction and checks every actual round trip.
The final writer reads pivots without emitting extra surface diagnostics.

RecHit variance entries describe sensor segmentation axes. ACTS plane covariance
is the sensor X/Z covariance permuted to −Z/X. Equal SiMAPS pitches make the
Global X/Y covariance isotropic, so the Global-coordinate Mille equations remain
valid under Rz without new error scaling. Anisotropic correlated Mille
measurements, tilted planes, material/process noise and momentum inference are
not established by these tests. The KF, DirectNavigator, seed covariance,
particle hypothesis and stored Track NDF semantics were not changed.

## Controlled samples and recovery

The standard 1 GeV electron seed, z=−500 mm mean vertex, angular distribution,
X/Y source width, material and hit errors were retained. New physical Geant4
samples used separate scenarios. The dedicated 1,000-event configuration changes
**only the event count**, preserving the standard configuration file.

| Sample | Events / tracks | Injected Rz L1/L2 (mrad) | First physical correction L1/L2 (mrad) | First pede nominal errors (mrad) |
|---|---:|---:|---:|---:|
| L1 only | 100 / 98 | +10 / 0 | +10.283 / fixed | 0.11096 / — |
| L1/L2 Rz | 100 / 98 | +10 / −8 | +10.321 / −7.6109 | 0.11514 / 0.098739 |
| L1/L2 X/Y/Rz | 100 / 98 | +10 / −8 | +10.218 / −7.8382 | 0.15115 / 0.12954 |
| L1/L2 Rz, larger sample | 1000 / 954 | +10 / −8 | +9.9709 / −7.9862 | 0.035319 / 0.030285 |

The combined injection also used L1 `(X,Y)=(+0.150,−0.120)` mm and L2
`(+0.200,+0.090)` mm. First inferred translations were
`(+0.150950,−0.119540)` and `(+0.201190,+0.089855)` mm.
The final serialized G2 centers were `(0.15097032,−0.11950761)` and
`(0.20120605,0.08986551)` mm, with angles
`+0.01021706989` and `−0.00784791770` rad.

| Sample | ACTS chi2 / stored NDF before → after first update | L1 matched residual RMS X/Y before → after (μm) | L2 matched residual RMS X/Y before → after (μm) |
|---|---:|---:|---:|
| L1 | 10.07658 → 1.27133 | 78.28/78.03 → 9.94/10.51 | 10.43/10.41 → unchanged |
| L1/L2 Rz | 20.76230 → 1.27318 | 78.28/78.03 → 9.98/10.54 | 66.15/67.05 → 9.73/10.68 |
| Combined | 75.78002 → 1.17277 | 161.74/142.94 → 10.26/9.38 | 215.53/112.00 → 10.50/10.35 |
| Larger sample | 22.78610 → 1.38282 | 80.99/82.13 → 10.17/10.09 | 70.59/70.54 → 10.03/10.09 |

These residual distributions use unique event/layer SimHit–RecHit pairs, as in
the maintained ROOT plots, including events without an accepted track. Coverage
and information diagnostics instead use the accepted track sample. In the larger
sample there were 993 unique L1 pairs and 989 L2 pairs. Its final matched means
were L1 `(−0.230,−0.151)` μm, L2 `(−0.591,−0.102)` μm. The historical
**pooled** L2 X mean was +29.829 μm because SimHit/RecHit multiplicities differ;
that statistic is not a matched residual. It was retained, not silently changed
or omitted. Multiplicity-aware truth associations remain a useful future study.

## Observability, statistics and retained warnings

The 98 accepted L1 tracks had X/Y RMS coverage 7.737/7.687 mm, ranges
`[−15.90,+16.21]` / `[−13.75,+16.56]` mm, and transverse slope RMS
0.01410/0.01396. A narrow gun vertex does not imply a narrow plane impact spot
with the unchanged angular cone and 500 mm flight distance.

Independent straight-line Fisher diagnostics gave full joint rank 3 for L1
X/Y/Rz, 6 for L1/L2 X/Y/Rz, and 8 when including the established L3 X/Y nuisance
parameters. The combined column-normalized eigenvalues ranged 0.5376–1.3819;
Rz1–Rz2 correlation was about 0.267. The largest same-layer translation–rotation
correlation was about 0.084. The full matrices are saved, rather than inferred
from a good chi2 alone.

L1 rotation-only nominal sigma was 0.11096 mrad, versus 0.11127 mrad with its
translations hypothetically free. Reducing transverse coverage by factors 10
and 100 in a **design-only sensitivity calculation** increased sigma by those
factors. At zero coverage the rotational information vanished. An offset point
spot also made rotation degenerate with free translations. These calculations
are not additional narrow-beam Geant4 tests; existing coverage was adequate.

Actual 20/50-event, fresh-frame RawHit-only subsets converged in two controller
iterations with 19/49 tracks. Their angular updates were respectively
`(+0.0099663,+0.0000031695)` and
`(+0.010253,+0.0000010446)` rad. These small-statistics demonstrations explicitly
used minimum 10 tracks; the main policy retained minimum 20. No physical
uncertainty, seed or geometry condition was loosened.

The 100-event two-layer L2 estimate differed from truth by 3.94 nominal sigma.
The track-cluster sandwich error diagnostic was 0.1801 mrad instead of 0.09874
mrad (2.16 diagnostic sigma). L1-only sandwich sigma was 0.1429 mrad instead of
0.1110 mrad. These are **uncertainty diagnostics**, not rescaled production
measurement errors. The new 1,000-event result was within one nominal sigma of
both injected rotations; it supports finite-sample fluctuations rather than a
persistent sign/pivot bias, without certifying the complete error model.

Pede status **1, warnings (bad measurements)** was retained. L1 gave
`1246.94161/(588−1)=2.12426`. The old XY warning near 2.011 was preserved in
regression. Multiple scattering, electron tails, missing ACTS material/process
noise and the finite seed remain relevant limitations. ACTS stores measurement
dimensionality (10 per accepted track); this ratio is not the classical
four-parameter fit's reduced chi2.

The combined first pede pass initially rejected 24 local fits as unreasonable,
then ended with zero rejects. Its first covariance therefore differs from the
all-track Fisher matrix. The unchanged installed pede defaults have
`chhuge=50`, `matrit=0` (`external/src/millepede-ii/src/mpmod.f90`), reject huge
local chi2 in `pede.f90` around lines 4107–4132, and only recalculate matrices
for `iterat < matrit` around lines 8982–8990. Its log shows matrix calculation
only at the initial FMS row. Subsequent corrected-Geometry passes used all tracks;
Rz errors became **0.11550/0.099008 mrad**, matching the independent all-track
design. No steering, rejection default or error was changed to improve agreement.

## Iteration and Geometry lifecycle

All main cases converged in two fixed-RawHit iterations using provisional
`delta_tolerance_rad=1e-5`, `max_update_rad=0.05`, and unchanged mm/track-quality
demonstration gates. The six combined components must all pass their own units.

| Case | G0→G1 angles L1/L2 (rad) | G1→G2 angles L1/L2 (rad) |
|---|---|---|
| L1 | +0.010283 / — | −1.5477e-8 / — |
| L1/L2 Rz | +0.010321 / −0.0076109 | +9.7194e-7 / +1.0049e-6 |
| Combined | +0.010218 / −0.0078382 | −9.3011e-7 / −9.7177e-6 |
| Larger sample | +0.0099709 / −0.0079862 | +1.2513e-7 / +3.5559e-7 |

The combined second translations were L1 `(+2.0317e-5,+3.2390e-5)` mm,
L2 `(+1.6047e-5,+1.0513e-5)` mm. Every iteration recorded the same input
checksum and an immutable current-Geometry parent chain. Exact G2 candidates
were separately reconstructed and probed. Additional G2 pede fits confirmed
negligible remaining updates; those were diagnostic fits, not activated updates.

A separate survey start used L1 `(0.04,−0.03,+0.003)` and L2
`(−0.02,+0.01,−0.002)` in mm/mm/rad. Fresh PODIO frames contained only
EventHeader and RawHits, exactly matching all 15 raw branches, with no Simulation
frames, truth hashes or truth-Geometry configuration key. The same Python
controller converged in two iterations. Final nominal-start versus survey-start
differences were at most **1e-8 mm and 5e-9 rad**. No truth parameter was supplied
to inference. This is a simulation-backed test fixture, not a DAQ interface.

All candidates remain **inactive**. Convergence is not approval. Independent
validation with a different input and explicit review/activation are still
required; no such activation was performed.

## Regression, safety, builds and ROOT

- Final build: `build/rz_alignment_20261022_02/`, ACTS 45.3.0, DD4hep 1.36.
  Both BeamTestReco and the focused Geometry library built successfully.
  `ldd` resolves `libMille2.so` to `/work/external/install/lib/libMille2.so`.
- A final correction to an outdated factory comment was rebuilt. Executable
  `.text` and `.rodata` section hashes were identical before/after; the
  BeamTestReco binary and derivative gate remained unchanged. Fresh final-library
  DD4hep/ACTS checks passed afterward.
- Historical final-build L2 regression: **99 tracks, +198.75 μm**;
  residual **−199.571376 → −0.821365 μm**;
  ACTS chi2/stored-NDF **45.592235 → 1.981040**; saved reference passed.
- L1/L2 X and XY controller regressions passed; the XY and strict truth-free
  survey runs reached the same historical G2 checksum.
- Combined/split equivalence passed exactly for 281 downstream branches,
  identical Mille bytes and identical pede parameters.
- Existing XY finite differences passed both nominal and rotated Geometry.
- Transform, correction composition, units, controller/version-chain/schema
  tests passed; unsupported Z/Rx/Ry and unsupported layers were refused.
- A synthetic zero-rotation-information fixture was rejected by official pede
  with status **22: no variable global parameters**. A real 98-track delivery
  under a minimum-101 policy performed no calibration and left active Geometry
  unchanged. Expected failure artifacts were retained.
- Saved ROOT outputs passed canvas, 20 residual-histogram and per-layer angular
  graph checks. Open each `step7/alignment.root` in ROOT/TBrowser. Combined
  outputs additionally include the established Y views.

The first factory compile required explicit ROOT Rotation3D conversions. A
nonzero-pivot test first used decimal −0.75 instead of actual DD4hep
−0.75000000000000011, causing one float32 tie mismatch; the corrected test uses
the actual center and retains exact equality. The first 1,000-event wrapper
attempt forwarded `--alignment-mode` to Digitization; the option lists were
separated. Its successful Simulation and failed logs remain in `two_rz_1000/`;
`two_rz_1000_retest/` is the successful fresh workflow using the same saved
Simulation. None of these failed attempts was counted as a pass.

## Maintained files changed in this phase

These changes are additional to the already-uncommitted XY/controller work.
The complete task-start comparison is saved as `changes_from_task_start.json`.

| Area | Files |
|---|---|
| Physical placement | `geometry/prepare.py`, `placements.py`, `environment.py`; `localDetEICrecon/geometry/SiTrackerEndcap2XY_geo.cpp` |
| Placement diagnostics | `localDetEICrecon/geometry/SurfacePlacements.h` |
| Official Mille derivatives | `localDetEICrecon/alignment/src/BeamTestMilleWriter.{h,cc}`, `localDetEICrecon/processors/BeamTestMilleProcessor.{h,cc}` |
| Reconstruction option | `reconstruction/reconstruct.py` |
| Steering/status/units | `alignment/align.py`; new `pede_l1_rz.txt`, `pede_l1_l2_rz.txt`, `pede_l1_l2_xy_rz.txt` |
| Composition and scope | `correction/correct_geometry.py`, `scope.py` |
| Existing controller | `calibration/settings.py`, `iteration.py`, `convergence.py`; new disabled `config/{l1_rz,l1_l2_rz,l1_l2_xy_rz}_demo.json` |
| Separate scenarios | New `geometry/scenarios/{L1_rz10mrad,L1_L2_rz,L1_L2_xy_rz,L1_rz_reference,L1_L2_rz_reference,L1_L2_xy_rz_reference}.json` |
| Larger-statistics input | New `simulation/configs/electron_1GeV_rotation_1000.json` |
| Numerical validation | New `validation/validate_rz_derivatives.py`, `rotation_observability.py`, `gdml_geometry_probe.py`, `test_rotation.py`; modified `geometry_probe.py`, `test_geometry_correction.py`, `metrics.py`, `validate.py`, `run_closure.sh` |
| ROOT | `visualization/closure.py` adds selected-layer outlines and angular correction graphs |
| Documentation | `README.md`, `docs/WORKFLOW.md`, `GEOMETRY_CONVENTIONS.md`, this report, `calibration/README.md`, `validation/README.md` |

No CMake restructuring, fitter algorithm, EDM schema, baseline configuration,
source removal, parameter-family replacement or uncertainty change was needed.
`BeamTestACTSFitter.cc` remained byte-identical to the task-start snapshot,
including its electron-hypothesis change. All 6,953 pre-existing protected
checksums passed, along with the maintained 221 baseline / 2,046 relocated
checks. The final unit suite passed **26 tests**, Python compilation, shell
syntax and `git diff --check` passed. Existing partial failures and all newly
created negative fixtures remain available.

## Inputs and outputs

| Stage | Input | Output in a new result directory |
|---|---|---|
| Geometry Preparation | unchanged nominal XML, selected scenario | `step1/{nominal,misaligned}.xml`, exported GDML, placement checks |
| Simulation | physical misaligned XML, beam configuration | `step2/events.edm4hep.root` |
| Digitization | Simulation and physical readout placement | `step2_digitization/rawhits.edm4eic.root`, `rawhit_contract.json` |
| Reconstruction | fixed RawHits, selected Geometry, reconstruction config, alignment mode | `step3/reco.root`, official `mille.dat` |
| Alignment | Mille Binary, constrained mode steering | `step4/millepede.res`, `.end`, full logs |
| Geometry Correction | fitted biases and current Geometry | `step5/corrected.xml`, unit/pivot/update metadata |
| Corrected Reconstruction | same RawHits, corrected Geometry | `step6/reco.root`, new Mille Binary |
| Closure Validation | before/after outputs and optional Simulation Truth for evaluation | `step7/summary.json`, `alignment.root` |
| Controller iteration | ready RawHits, explicit fallback/survey, policy and derivative gate | queue records, immutable G0→G1→G2 candidates, calibration report; no activation |

Simulation Truth is used only by the evaluation row, not by alignment inference.
Local datasets and `result/` outputs are not intended for Git. To repeat the
historical L2 regression, retain the documented local file
`results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root`.
Saved X/XY regressions additionally use the prior RawHit result directories
listed in their validation reports. New rotation datasets can be regenerated
from the maintained scenarios and beam configurations.

## Independent commands

Run inside the EIC container at `/work`, or prefix each command with
`TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh`. Use **new** build,
result, input and state paths. The following is a reusable recipe, not permission
to overwrite the validated example directories.

```sh
export TESTBENCH_BUILD_DIR=/work/build/NEW_RZ
bash environment/build.sh

python3 -m geometry.prepare --result-dir result/NEW_L1 --geometry-config geometry/scenarios/L1_rz10mrad.json
python3 -m simulation.simulate --result-dir result/NEW_L1
python3 -m digitization.digitize --result-dir result/NEW_L1 --build-dir "$TESTBENCH_BUILD_DIR"
python3 -m reconstruction.reconstruct --result-dir result/NEW_L1 --build-dir "$TESTBENCH_BUILD_DIR" --alignment-mode l1_rz

# Validate derivatives before enabling automated calibration.
python3 -m validation.validate_rz_derivatives --geometry geometry/nominal/seven_layer_telescope.xml --mille result/NEW_L1/step3/mille.dat --reco result/NEW_L1/step3/reco.root --layer 1 --output result/NEW_L1_DERIVATIVES

python3 -m alignment.align --result-dir result/NEW_L1 --steering alignment/pede_l1_rz.txt
python3 -m correction.correct_geometry --result-dir result/NEW_L1 --mode l1_rz
python3 -m reconstruction.reconstruct --result-dir result/NEW_L1 --after --build-dir "$TESTBENCH_BUILD_DIR" --alignment-mode l1_rz
python3 -m validation.validate --result-dir result/NEW_L1 --correction-mode l1_rz

python3 -m validation.geometry_probe --geometry result/NEW_L1/step5/corrected.xml --reco result/NEW_L1/step6/reco.root --log result/NEW_L1/step6/stdout.log --output result/NEW_L1_CONTEXTS.json
python3 -m validation.gdml_geometry_probe --geometry result/NEW_L1/step1/misaligned.xml --gdml result/NEW_L1/step1/misaligned_qa/geometry.gdml --output result/NEW_L1_GDML.json
python3 -m validation.rotation_observability --reco result/NEW_L1/step3/reco.root --mode l1_rz --output result/NEW_L1_INFORMATION.json
```

After L1 validation, produce a separate L1/L2 diagnostic reconstruction using
`--alignment-mode l1_l2_rz`. Validate both labels with `--layer 1` and `--layer 2`;
the latter invocation can supply `--additional-gate PATH_TO_LAYER1/gate.json`.
This combines immutable reports for the **same plugin** into the second output's
`gate.json`. The metadata merge and stale/mismatched evidence refusals have unit
tests; the executed final physical sweeps used separate per-layer gates and an
explicit aggregate manifest with both report checksums.

Copy the corresponding disabled controller JSON to a new local configuration,
set the validated build and gate paths, enable its demonstration policy, and
publish a ready RawHit delivery using the existing [controller guide](../calibration/README.md).
Use its zero-displacement reference scenario and explicit fallback/survey:

```sh
python3 -m calibration.controller once --config result/NEW_CONFIG.json --input-dir input/NEW_DELIVERIES --state-dir result/NEW_STATE
# Same worker and queue, sequential file monitoring:
python3 -m calibration.controller watch --config result/NEW_CONFIG.json --input-dir input/NEW_DELIVERIES --state-dir result/NEW_STATE
```

`once` was executed in the new physical tests. The unchanged watch/queue and
version-lifecycle behavior is covered by the existing controller tests; no new
long-running watch daemon was left running.

For a previously derivative-validated build, the maintained one-shot wrapper
also supports each explicit mode, including saved Simulation reuse:

```sh
bash validation/run_closure.sh --result-dir result/NEW_TWO_RZ --geometry-config geometry/scenarios/L1_L2_rz.json --correction-mode l1_l2_rz --build-dir "$TESTBENCH_BUILD_DIR"
bash validation/run_closure.sh --result-dir result/NEW_COMBINED --geometry-config geometry/scenarios/L1_L2_xy_rz.json --correction-mode l1_l2_xy_rz --build-dir "$TESTBENCH_BUILD_DIR"
# Optional larger sample: add --simulation-config simulation/configs/electron_1GeV_rotation_1000.json
# Saved data: add --sim-input PATH_TO_COMPATIBLE_SIMULATION_ROOT
root -l result/NEW_COMBINED/step7/alignment.root
# In ROOT: new TBrowser;
```

### Exact executed audit entry points

These commands refer to retained local harnesses and artifacts. Each harness
contains the exact independent module calls; logs and `complete.json` markers
record their actual inputs, checksums and results. Do not rerun them into the
same existing output directories.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -c 'export TESTBENCH_BUILD_DIR=/work/build/rz_alignment_20261022_01; bash environment/build.sh > result/rz_alignment_20261022_01/build.log 2>&1'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -c 'cmake --build build/rz_alignment_20261022_01 -j 2 > result/rz_alignment_20261022_01/build_fixed.log 2>&1 && TESTBENCH_BUILD_DIR=/work/build/rz_alignment_20261022_01 python3 result/rz_alignment_20261022_01/start.py > result/rz_alignment_20261022_01/start.log 2>&1'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -c 'export TESTBENCH_BUILD_DIR=/work/build/rz_alignment_20261022_02; bash environment/build.sh > result/rz_alignment_20261022_01/build_extended.log 2>&1'
```

Additional executed Python entry points, run through the same wrapper with
`TESTBENCH_BUILD_DIR=/work/build/rz_alignment_20261022_02`, were:

```sh
python3 result/rz_alignment_20261022_01/derivative_extended.py 1
python3 result/rz_alignment_20261022_01/derivative_extended.py 2
python3 result/rz_alignment_20261022_01/make_two_rz.py
python3 result/rz_alignment_20261022_01/two_followup.py
python3 result/rz_alignment_20261022_01/combined_followup.py
python3 result/rz_alignment_20261022_01/statistics.py
python3 result/rz_alignment_20261022_01/final_iterations.py
python3 result/rz_alignment_20261022_01/negative_checks.py
python3 result/rz_alignment_20261022_01/root_and_final_checks.py
python3 result/rz_alignment_20261022_01/final_regressions/regressions.py
python3 result/rz_alignment_20261022_01/final_regressions/additional_regressions.py
bash validation/run_regression.sh result/rz_alignment_20261022_01/final_regressions/l2_regression build/rz_alignment_20261022_02
bash validation/run_closure.sh --result-dir result/rz_alignment_20261022_01/two_rz_1000_retest --geometry-config geometry/scenarios/L1_L2_rz.json --simulation-config simulation/configs/electron_1GeV_rotation_1000.json --sim-input result/rz_alignment_20261022_01/two_rz_1000/step2/events.edm4hep.root --correction-mode l1_l2_rz --build-dir build/rz_alignment_20261022_02
python3 -m validation.validate_xy_derivatives --geometry result/rz_alignment_20261022_01/combined_xy_rz/step5/corrected.xml --mille result/rz_alignment_20261022_01/combined_xy_rz/step6/mille.dat --output result/rz_alignment_20261022_01/xy_derivatives_rotated
```

Host checks used `PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache`:

```sh
python3 -m unittest validation.test_rotation validation.test_transforms validation.test_geometry_correction validation.test_raw_metadata validation.test_calibration_controller
python3 -m compileall -q geometry simulation digitization reconstruction alignment correction calibration validation visualization
python3 validation/verify_preservation.py
python3 validation/check_safety.py
git diff --check
```

## Remaining limitations and next work

This establishes numerical and controlled-simulation in-plane rotation recovery
for the stated telescope, not a production calibration certificate. Keep all
new candidates inactive until independent validation and explicit approval.
Priorities are an independently justified material/process-noise and uncertainty
study, robust treatment of electron tails, multiplicity-aware truth validation,
and sensitivity studies with independent seeds/beam configurations. A physically
narrow-beam Geant4 test and the original 5 GeV muon path were not separately run
in this phase. No support is claimed for anisotropic correlated Mille errors,
arbitrary detector hierarchies, Rx/Ry tilts, Z translation or all-layer gauges.

The information/rank and cluster-error diagnostics remain explicit validation
steps. The prototype controller's finite-error/rank, track-count, step and chi2
gates alone are not a certificate for weak but nonzero rotation information.
This is another reason candidates require independent validation and approval.

Git remains on `seven-layer-alignment`, with an empty index: 28 tracked modified
files and 62 untracked files (90 entries with `-uall`), including pre-existing
work. This phase changed or added 45 maintained files. No deletion, commit or
push was performed. New data/build artifacts remain ignored. The task-start and
validated-source snapshots are retained in the new result directory.
