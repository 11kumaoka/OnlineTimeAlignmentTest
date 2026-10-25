# Legacy/native telescope alignment parity

Latest controlled validated fixture: [unchanged-envelope four-parameter study](#unchanged-envelope-four-parameter-containment-milestone).
Previous validated scope: [three-axis native SO(3)](#three-axis-native-so3-milestone).
Original experimental checkpoint: [L1 Y plus three rotations](#l1-global-y-plus-three-axis-native-so3-milestone),
5/6 closures; a physical candidate-containment failure prevents promotion.
Previous coupled baseline: [Ry/Rz](#coupled-native-ryrz-so3-milestone).
Previous signed baseline: [single-axis Ry/Rz](#signed-single-axis-ryrz-completion).

Baseline: clean `feature/upstream-acts-geometry` at
`1d4696bea597893c9afb7de237e9094dbfcc6f91`. This document separates implemented
code, enabled configuration, numerical tests, actual reconstructed closure and
statistical accuracy. Native results for this milestone are recorded below only
after execution. No legacy algorithm, source Geometry or historical evidence is changed.

## Verified historical capability matrix

The legacy beam is +Z; the native barrel-compatible fixture beam is +X. These
are different world frames. Legacy in-plane Global Rz is physically analogous
to native Global Rx, not an assertion that their Global labels are interchangeable.

| Mode / capability | Legacy implementation/configuration | Actual historical evidence and limit | Native at milestone start / missing |
|---|---|---|---|
| L2 X | enabled `l2_x`, original writer/correction | 100-event Geant4 reference, 99 tracks, +198.75 um; rerun at consolidation | native uses physical Y instead; original endcap compatibility missing |
| L1/L2 X, XY | explicit `l1_l2_x`, `l1_l2_xy` | controlled reconstructed/iterative closure; XY_FOUNDATION_VALIDATION and saved `result/xy_foundation_20261022_01/` | L1/L2 physical Global Y only, 32 quantized-channel tracks |
| L1 Rz, L1/L2 Rz, XY+Rz | enabled explicit modes/steering | ROTATION_ALIGNMENT_VALIDATION, controlled positive/negative/mixed closures | no native rotation-enabled configuration at start |
| Rz uncertainty statistics | 30 independent 100-event seeds | RZ_STATISTICAL_VALIDATION: initial Pull sample SD 1.433/1.661; nominal coverage not certified | no native coverage claim |
| L1 Z, L1/L2 Z, XYZ | guarded explicit modes | Z_ALIGNMENT_VALIDATION: real DD4hep/GDML, derivatives, controlled reconstruction/iteration; transverse multi-sigma biases remain | no native longitudinal translation fit |
| L1 Rx alone / Ry alone | enabled `l1_rx`, `l1_ry` | TILT_ALIGNMENT_VALIDATION: positive Rx and positive/negative Ry, justified independent 1000-event Rx check | native tilt fits missing; in-plane Rx investigated first here |
| Fixed ordered L1 or L1/L2 Rx/Ry | code/config artifacts retained, public scopes disabled | finite-rotation closure **failed**; 357.389 urad full orientation error. Full rank and infinitesimal derivative success did not establish closure | not enabled or ported |
| L1 rotations / L1/L2 rotations | enabled SO(3) modes, all three left-Global increments | SO3_ALIGNMENT_VALIDATION: exact mathematical recovery and controlled Geant4 reconstruction/iteration, full-matrix evaluation; noisy orientation errors remain | native six columns exist but no such solved scope |
| L1 six-DOF / L1/L2 six-DOF | enabled guarded modes, fixed references | SO3_ALIGNMENT_VALIDATION: controlled 100/1000-event cases, Survey replay, immutable RawHits; large-offset capture failure retained; no unbiased/coverage claim | missing native combined multi-DOF scopes |
| L3 / L1/L2/L3 six-DOF | opt-in implementations, templates disabled | L3_SIX_DOF_IMPLEMENTATION: geometry/derivative/rank/stage checks; **no complete noisy physical closure** | missing; not counted as validated parity |
| SO(3) Geometry updates | `Exp(w) Rcurrent`, current sensitive-center pivot, matrix serialization | mandatory noiseless cases, previous failed fixed-point replay and Survey-start tests | native translations only at start; selected center-preserving Rx added in this milestone |
| Observability guards | actual weighted-row profiling, scope-dependent rad/mm bounds and evidence pins | Z/tilt/SO(3) gates, weak-design refusal, current unit/safety tests | current two-Y rank checks; selected rotation/translation correlations needed |
| Sequential/iterative Controller | queue/lock/recovery, immutable inputs, version chains, explicit review | saved once/watch/iteration/Survey replays plus Controller unit/safety tests; demo convergence thresholds | native driver is a bounded integration test, not an online Controller |
| Geant4/Digitization/RawHit compatibility | original BeamTestReco independent stages | saved 99-track and later electron workflows, RawHit equivalence tests | native inputs are deterministic physical-surface intersections and pixel CellIDs; no Geant4 migration claimed |

Historical source authority: `correction/scope.py`, mode steering in `alignment/`,
`geometry.prepare.write_shifted_xml`, `correction.correct_geometry.correct_so3`,
`calibration/iteration.py`, and original C++ Writer/Processor. Configuration existence
alone is not closure evidence. The cited reports retain exact sample/log/result
paths; original failures remain available. No inference uses Truth corrections.

## Native model audit and selected convention

`NativeMilleModel::nativeEquation` already uses official ACTS transport and
`Surface::alignmentToBoundDerivative`, with Global left rotation columns obtained
from ACTS local right increments through R^T. Whitening remains the original
calibrated covariance Cholesky. Four local track parameters are eliminated by
Pede; seed-prior rows and Truth are not added. The model remains zero-field and
without assigned ACTS material/process noise.

The first investigated mode is L1 physical Global X rotation about its current
sensitive center. The selected three-parameter follow-up is L1 Global Y, L1 Global
Rx, L2 Global Y. Other poses remain fixed. Numerical gates, actual profiled rank,
Pede recovery and full fresh-process reconstruction closure are distinct statuses.

## Configuration availability is not activation

The legacy source exposes the explicitly guarded CLI scopes in the matrix and
historical per-run configurations exercised them. Supplied SO(3) Controller demo
templates, including L1/L2 and L3 scopes, still contain `enabled: false`.
An available canonical steering/CLI is not a running or approved Controller.
L3 templates remain disabled and do not have a complete noisy closure.
Actual machine evidence was also read from
`result/rotation_resolution_20261023_01/scientific_summary_final.json` and
`same_fixture_recovery/report.json`: the preserved failure is Pede status 26 for
the larger-offset six-DOF fixture; the prior failed orientation is
0.000357388796 rad. Source hashes/keys are recorded in
`result/native_rotation_20261024_01_audit/legacy_evidence.json`.

## Native physical parameter contract

| Parameter | Label | Unit | Sensor |
|---|---:|---|---|
| L1 Global Y | 700102 | mm | SiMAPS L1 |
| L1 Global Rx | 700104 | rad | VolumeID 272631839, GeometryIdentifier 216173056991691039 |
| L2 Global Y | 700202 | mm | SiMAPS L2 |

The allowed label sets are exactly `{700102,700202}`, `{700104}`, and
`{700102,700104,700202}`. Unselected parameters are fixed; L0/L3/L4 are reference
sensors and L2 orientation is fixed. The original two-Y JSON is byte-identical.
No external constraint, error rescaling, different selection, seed prior or
covariance was added to make the rotation observable. Pede's `entries 5` and
`method inversion 3 0.001` remain unchanged; only selected free labels differ.

Rx is an active physical left-Global increment about the **current sensitive
center**, `Rnew=Exp([dx,0,0]) Rcurrent`; translations move that center separately.
The existing ACTS global derivative column 3 is selected; Y uses column 1.
The residual equation remains measured-minus-predicted = A*localDelta + G*physicalDelta.
Positive fitted Rx is applied with the same positive physical sign.

Fresh XML-axis probes established that increasing component XML `y` by 0.01 rad
produces -0.01 rad physical Global X in this actual constructor. The restricted
serializer forms the SO(3) target matrix first, then encodes the proven subgroup
as `y=-pi/2-Rx`, keeping the original component `x=-pi/2,z=0`. It rejects other
charts rather than inventing a general Euler updater. Actual DD4hep and ACTS
matrices, centers and IDs independently verify every update. Pivot/identity
fields are explicit in both new JSON configurations.

The +1.8 mrad test amplitude changes 15/32 L1 CellIDs in the rotation-only case.
It produces a measurable signal and remains inside the original 100.5 mm module
and 102 mm layer envelopes even with the combined Y translations. Half-square
corner projections and actual sensor poses are checked; no envelope, pitch,
material or detector position constants were altered.

## Final native validation status

| Scope | Implemented | Derivatives validated | Pede recovery | Full fresh-process reconstruction closure |
|---|---|---|---|---|
| Original L1/L2 Y | yes, unchanged | existing gates rerun | exact baseline | passed, all original scientific values exact |
| L1 Global Rx | yes, restricted one-axis scope | actual nominal/corrected DD4hep surfaces and original ACTS gates | passed | passed, +1.8 mrad fixture |
| L1 Y/Rx + L2 Y | yes, three explicit parameters | actual nominal/corrected DD4hep surfaces and original ACTS gates | passed, rank 3 | passed |
| Native X/Z translations, Ry/Rz, other sensors/general six-DOF | not enabled | six columns alone do not certify a scope | unsupported | not established |
| Native iterative/online Controller and original Geant4 compatibility | not ported | not applicable | not established | missing; legacy remains |

The one-axis subgroup is closed under repeated Rx increments, but this milestone
is a one-correction closure plus post-fit diagnostic, not an iterative Controller
validation or general SO(3) recovery claim. Only the declared positive full
rotation fixture was fitted; positive/negative finite differences are not a
negative-amplitude reconstruction closure.

## Actual statistical and geometric results

These are two configurations of the same 32 deterministic rays, not independent
statistical ensembles. Repeated execution directories add no independent events.
All nominal/corrected/control passes accept 32 tracks with five SiMAPS measurements,
zero outliers and two expected holes, and write 32 official records / 320 scalars.
No Truth is provided to eicrecon or native Mille. Inference reads RawTrackerHit
channels, current reconstruction Geometry and the explicit selected fit scope;
correction reads actual Pede text and nominal XML. Truth is used for generation
and final evaluation only.

| Quantity | L1 Rx only | L1 Y/Rx + L2 Y |
|---|---:|---:|
| Injected Rx [mrad] | +1.8000 | +1.8000 |
| Initial recovered Rx [mrad] | +1.6622 | +1.7632 |
| Rotation difference [mrad] | -0.1378 | -0.0368 |
| Initial nominal Rx sigma [mrad] | 0.232641 | 0.233332 |
| L1 Y recovered / error [um] | fixed zero | +148.99 / -1.01 |
| L2 Y recovered / error [um] | fixed zero | +203.18 / +3.18 |
| Rank | 1/1 | 3/3 |
| Raw condition (mixed mm/rad units) | 1 | 106.4851 |
| Diagonal-scaled condition | 1 | 1.766902 |
| ACTS chi2/stored-NDF nominal | 0.8287644781 | 37.4973357201 |
| ACTS chi2/stored-NDF corrected | 0.6692536891 | 0.7044985697 |
| Initial Pede chi2/statistical NDF | 214.152558/191 = 1.121218 | 225.129536/189 = 1.191162 |
| Remaining Rx update [mrad] | -0.00025248 | -0.0050079 |
| Remaining Y updates L1/L2 [um] | not fitted | -0.0015166 / +0.0028774 |
| L1 residual RMS u/v nominal [mm] | 0.0105003 / 0.0125053 | 0.0654561 / 0.0125054 |
| L1 residual RMS u/v corrected [mm] | 0.0083370 / 0.0092452 | 0.0081567 / 0.0093234 |

Combined order is `[L1 Y, L1 Rx, L2 Y]`. Correlations are
Y1–Rx1=-0.0740186, Y1–Y2=+0.2665281, Rx1–Y2 consistent with zero.
The pre-implementation actual-track design also had rank 3 and scaled condition
1.76686; rank/condition were recalculated using the new actual binary rows.

Engineering recovery tolerances were declared as five initial unscaled nominal
errors. Angular tolerances are 1.163205/1.166658 mrad, while combined translation
tolerances are 10.9934/10.2552 um. Actual relative matrix orientation errors are
0.1378/0.0368 mrad; centers differ only by the reported Y errors. Serialization
consistency separately requires 1e-9 mm centers and 2e-12 matrix-entry agreement.
Post-correction updates must be below 2e-5 mm or rad per selected parameter.
Sensitivity guards require scaled condition <100, angular sigma <1 mrad and
linear sigma <0.02 mm; these refuse weak designs and do not constrain a fit.

Nominal and postsolve Pede processes exit 0 with end status 1 (bad-measurement
warnings). Controls exit/end 0. Every local-fit rejection count is zero. Error
rescaling recommendations are recorded but never applied. Reported Pede nominal
errors agree with the unchanged-covariance inverse information to printed
precision; decoded-Mille profiling independently agrees with Pede chi2/NDF.
ACTS stored NDF remains 10 per track; statistical Pede NDF is 32*(10-4)-1=191 or
32*(10-4)-3=189. Initial linearized Pede chi2 and post-correction chi2 need not
be identical; they evaluate different surface linearizations. No claimed
confidence coverage follows from either closure or the engineering tolerances.

## Geometry and derivative evidence

For each final case, nominal and corrected physical gates freeze all 32 actual
native reference states and reload real DD4hep/ACTS sensor geometries at
±1e-4, ±1e-5 and ±1e-6 rad. Each gate makes 96 two-component comparisons: 384
vectors / 768 components across the two cases and two poses. Maximum absolute
rotation derivative error is 1.977e-8 mm/rad (gate tolerance 2e-5 mm/rad). Current corrected
Geometry is perturbed as well as nominal. Both DD4hep native bases and ACTS bases
must transform by the requested Global Exp increment, with unchanged centers,
VolumeIDs and closed GeometryIdentifiers. No virtual-only surface perturbation
is substituted for this gate. The original six-column ACTS/ray tests also run
on every nominal/corrected/control geometry.

Strict independent XML whitelists preserve materials, dimensions, segmentation,
readout, unselected poses and all attributes except selected module references,
component X translation and L1 component Y rotation. RawHit bytes and local
measurements/covariances remain unchanged; reconstructed global points follow
actual corrected poses. PODIO collections contain no Truth, seed relations and
endpoint-derived seed values are verified, and native calibrated coordinates
round-trip through actual SurfaceMap transforms.

## Files and principal functions changed

- `TelescopeMille.cc::Init/Process`: explicit selected scopes, ACTS column routing,
  actual ID checks and frozen native reference audit; no equation/whitening change.
- `TelescopeChannels.cc::main`: report actual DD4hep basis columns in addition to
  ACTS poses; actual sensor intersections and segmentation are unchanged.
- `closure.py::displaced_xml/geometry_step/reconstruct/solve/correct/check/main`:
  selected-mode routing, restricted physical injection, shared Pede solve dimensions,
  printed-precision/error checks; default two-Y branch retained.
- `rotation.py::rotate_component/pose_checks/physical_derivatives/correct/check`:
  one-axis SO(3) serialization, real-Geometry derivatives, correction application
  and independent integration gates. No new reconstruction or numerical solver.
- New `l1_global_rx.json` and `l1_y_rx_l2_y.json`; original two-Y JSON unchanged.
- User guide, code map, experimental README and root README explain the scope.

`NativeMilleModel.{h,cc}`, numerical tracking, measurement covariance, seed prior,
particle hypothesis, CKF selector, legacy SO(3), Controller and canonical Geometry
remain unchanged. The derivative model fingerprint remains
`1622cc80327fe08dd6c943bb57e537a8fea86a95233389065efa91739028843f`.


## Reproducible commands and artifact paths

Run from the repository root with the fixed Docker mount `/work`. These are the
actual execution names; repeating any writer command requires new build/result
names. `--step all` already performs geometry, data, nominal, solve, correction,
corrected, postsolve, control, controlsolve and check. Use the same arguments and
one `--step` name to run a stage independently. Rotation physical derivatives
are mandatory before the initial and post-correction Pede solve.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_rotation_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_rotation_20261024_01 -j2
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_rotation_20261024_01 --result result/native_rotation_single_20261024_03 \
  --events 32 --chi2-cut 1000 --mode l1_rx --step all
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_rotation_20261024_01 --result result/native_rotation_single_20261024_03 \
  --events 32 --chi2-cut 1000 --mode l1_rx --step check --validation-name final
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_rotation_20261024_01 --result result/native_rotation_combined_20261024_02 \
  --events 32 --chi2-cut 1000 --mode l1_y_rx_l2_y --step all
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_rotation_20261024_01 --result result/native_rotation_baseline_20261024_01 \
  --events 32 --chi2-cut 1000 --step all
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_rotation_20261024_01 --result result/native_rotation_baseline_20261024_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name rotation
bash environment/run.sh python3 -m unittest discover -s validation -p 'test_*.py'
bash environment/run.sh python3 validation/check_safety.py
python3 validation/verify_preservation.py
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/native_rotation_legacy_20261024_01 \
  /work/build/telescope_consolidation_legacy_20261024_01
bash environment/run.sh bash -lc 'export LD_LIBRARY_PATH=/work/external/install/lib:$LD_LIBRARY_PATH; exec /work/external/install/bin/inspectMilleBinary /work/result/native_rotation_single_20261024_03/nominal/mille.dat'
```

The historical regression deliberately uses the unchanged existing legacy binary;
only the native plugin was rebuilt for this milestone. No old build is overwritten.
It passes the saved 100-event/99-track reference with +198.75 um L2 correction,
residual -199.57137555 → -0.82136451 um and ACTS ratio
45.59223485 → 1.98103977. The actual saved dataset, not a newly simulated or
reinterpreted radial sample, is used.

Final scientific JSON and ROOT files:

- `result/native_rotation_single_20261024_03/final/report.json` and `rotation.root`.
- `result/native_rotation_combined_20261024_02/validation/report.json` and `rotation.root`.
- `result/native_rotation_baseline_20261024_01/final/report.json` and `closure.root`.
- Per-case `physical_derivatives/report.json` and
  `corrected_physical_derivatives/report.json`; each has 96 comparisons.
- Baseline `rotation_regressions/complete.json` and all 18 command/exit logs.
- `result/native_rotation_20261024_01_audit/` contains configure/build logs, design
  matrix, exact-baseline comparison, source/evidence audits, official Mille decode
  logs, final unit/safety logs and inverse-composition/refusal tests.

Read-only inspection examples:

```bash
python3 -c 'import json; from pathlib import Path; r=json.loads(Path("result/native_rotation_single_20261024_03/final/report.json").read_text()); print(r["parameters"], r["errors"], r["summaries"], r["pede_diagnostics"])'
root -l result/native_rotation_combined_20261024_02/validation/rotation.root
# In graphical ROOT: new TBrowser;
```

Each rotation ROOT file contains nine batch-verified histograms (u/v residuals
and ACTS chi2/stored-NDF for nominal/corrected/control). No GUI session was tested.
All 18 established regression commands passed, including standalone Geometry/
CKF, original derivative gates, native/legacy Writer equivalence, the separate
16-ray Pede fixture, 46 existing unit tests, safety and preservation. All 46 tests
and safety checks were also rerun after the final serialization fix. Preservation
verified 221 baseline and 2046 relocated files. Three official decodes each read
32 records. Four selected-rotation refusal controls and two actual DD4hep inverse
composition tests passed. Existing warnings were retained, not suppressed.

## Retained failures, limitations and next steps

The first source-header lookup found no usable installed source and container
`rg` was unavailable; logs remain under the audit root. A host fixture-import
attempt lacked numpy, so actual validation used the required container. Initial
0.01-rad XML-axis probes were zero-event convention diagnostics, not claimed
contained physical reconstruction fixtures; all fitted 1.8-mrad fixtures and
finite-difference samples have explicit containment checks.

Stronger independent XML whitelisting rejected the first successful physical
runs (`native_rotation_single_20261024_02/final` and
`native_rotation_combined_20261024_01/final`): the old placement helper rewrote
zero displacement attributes from `0` to `0*mm`. Geometry was physically unchanged,
but the new rotation path violated exact attribute preservation. The generator
now skips zero-offset attribute edits only for rotation fixtures. Assertions were
not loosened, original two-Y serialization remains exact, and fresh final cases
passed. Earlier runs, their valid initial numerical diagnostics, failed final
checks and all logs remain untouched.

The original baseline's 32 accepted tracks, +149.14/+203.18 um and ratios
37.16731567382813 → 0.6908491410315036 match exactly. Nominal/Truth/corrected XML and
all three baseline Mille binaries match the previous consolidation byte-for-byte.
The legacy fixed-ordered failure and statistical anomalies remain historical
facts, not problems fixed by this selected one-axis milestone.

Remaining work is explicit: native additional translations/rotations and sensor
scopes require their own actual-Geometry derivatives, observability and physical
reconstruction closure before release; Controller/Geant4 integration is separate.
No general six-DOF, material-aware performance, unbiased estimator or calibrated
uncertainty coverage is claimed. No candidate is activated and no legacy source
is deleted. The next scientifically justified step is an independently scoped
native mode, not automatic enablement of the six available derivative columns.

## Signed Rx and native tilt milestone (2026-10-24)

Starting commit: `27f2ed7f93349117457eb5ad235555e62d46a7de`. This adds
one **experimental L1 Global Ry** scope, not arbitrary rotation or six-DOF
alignment. The CKF, seed, particle hypothesis, calibrated errors, transport,
`NativeMilleModel`, legacy correction, and Controller are unchanged.

### Physical frame mapping, including sensor roll

Actual VolumeManager contexts, rather than beam directions alone, give

```
Dlegacy = [ 0  0 -1 ]     Dnative = [ 0 -1  0 ]
          [ 1  0  0 ]               [ 0  0  1 ]
          [ 0 -1  0 ]               [-1  0  0 ]

Q = Dnative Dlegacy^T = [ 0  0  1 ]
                       [-1  0  0 ]
                       [ 0 -1  0 ]
p_native = Q p_legacy + (250,0,0) mm
```

The columns of D are the DD4hep sensitive X/Y/Z axes in world coordinates.
The native parent module axes and nominal ACTS u/v/normal are the columns
of Q: `(-Global Y, -Global Z, +Global X)`. Native sensitive X/Y/Z are
`(-Global Z, -Global X, +Global Y)`. The native ACTS-to-sensitive matrix is
`[[0,1,0],[0,0,-1],[-1,0,0]]`.

For active right-handed rotations, `Q Exp(w) Q^T = Exp(Q w)`. Consequently:

| Legacy physical rotation | Native physical rotation |
|---|---|
| +Rx (tilt) | -Ry (tilt) |
| +Ry (tilt) | -Rz (tilt) |
| +Rz (in-plane) | +Rx (in-plane) |

All rotations use radians and the corresponding **current sensitive center**
as pivot. The actual-pose conjugation check at both signs has maximum error
`1.231e-16`. Source poses and checksums are in
`result/native_tilt_observability_20261024_01/frame_mapping.json`.

Do not confuse Q with the Writer-equivalence helper's comparison-only rotation
`[[0,0,1],[0,1,0],[-1,0,0]]`. That helper deliberately permutes/signs the two
transverse measurement coordinates. It preserves the beam direction but uses
a different roll. It remains a valid mathematical comparison; it does not define
the physical sensor-to-sensor migration. `prepare.py`'s recorded rotation agrees
with the actual physical Q above.

### Prospective gates and observability

The new negative Rx uses the existing gates: recovery within five initial
unscaled nominal sigmas, post-correction update below 20 urad, actual matrix
agreement within `2e-12`, center agreement within `1e-9 mm`, and unchanged IDs.
These are engineering gates, not coverage claims.

Before the Ry fit, the declared fixture was **+5 mrad**, with required angular
sensitivity below **1 mrad**, diagonal-scaled condition below 100, and full
profiled rank. The corresponding prefit diagnostic includes Y/Z/Rx/Ry/Rz on
L1 as nuisance/design columns; only Ry is written as a free Pede parameter.
A separate six-column matrix checks correlations with longitudinal X as well;
no six-DOF Pede configuration is enabled. Per-track four-parameter nuisance
states are QR-profiled out using original calibrated covariance and actual
ACTS derivatives. No seed-prior equations or smoothed-state covariance replace
the measurement errors.

| Actual nominal control cohort | Ry sigma [mrad], Y/Z/Rx/Rz also profiled | Rz sigma [mrad] | Scaled condition |
|---|---:|---:|---:|
| Original deterministic 32 | 64.774 | 56.273 | 2.061 |
| Independent broad 64, seed 2026102401 | 3.808 | 3.426 | 2.317 |
| Broad 1024, seed 2026102402 | 0.9452 | 0.8138 | 1.713 |

The exact matrices and five-column values are recorded in `baseline32.json`.
Full rank alone clearly did not resolve the original tilt. The bounded broad
recipe draws independent uniform intercepts `Y in [-12,12]`, `Z in [-10,10] mm`
at X=250 mm and slopes `dy/dx,dz/dx in [-0.08,0.08]`, using `mt19937_64` and
explicit seeds. Even at X=550 mm the bounds are 36 mm in Y and 34 mm in Z,
inside the real sensors. This is an intentionally divergent **synthetic,
material-free geometric validation beam**, not a measured beam distribution
or a Geant4 electron-physics performance claim. The baseline recipe is unchanged.

In the independent 1024 cohort, prefix Ry sigmas at N=32/64/128/256/512/1024
are 4.680/3.788/2.392/1.751/1.309/0.945 mrad. Prefixes share tracks and are
not independent experiments. The higher-slope half supplies 3.39 times the
Ry information per track of the lower half; the higher-impact-radius half
supplies 3.49 times that of the lower half. With all three translations included,
Ry sigma is 0.9456 mrad, scaled condition 1.718, and correlations with
X/Y/Z are +0.0293/+0.0061/+0.2622. These diagnostics are in
`all_translation_correlations.json` under the observability result directory.

Pixel pitch remains 0.034641 mm, sigma approximately 0.010 mm. The coherent
worst-case bounded-pixel error on Ry is about 94 mrad; it is **not** a statistical
error bar. Uniformly distributed intercepts/slopes improve phase sampling but
one realization does not establish independence of all quantization errors.
The nominal unshifted control's five-column inferred Ry fluctuation is
-1.391 mrad. No error rescaling was applied. A statistically validated uncertainty
model requires an independent ensemble, beyond this milestone.

### Restricted serializer and actual reconstruction closure

`l1_ry` selects label **700105**, ACTS physical Global rotation column 4.
Existing labels/modes remain unchanged. In the installed DD4hep constructor's
verified component chart:

- Pure Rx: `x=-pi/2`, `y=-pi/2-Rx`, `z=0`.
- Pure Ry: `x=-pi/2-Ry`, `y=-pi/2`, `z=0`.

Updates compute `Exp(dw_global) Rcurrent` and serialize only their separate
one-axis subgroup. Coupled Rx/Ry, Rz serialization, nonfinite updates and
unsupported parameter combinations are rejected. All eight sensitive-box
corners are checked against the unchanged module and cylindrical layer
envelopes for Ry. At +5 mrad the normal half extent is about 0.275 mm, below
the existing 0.325 mm module half thickness. Centers, sensitive VolumeID
272631839, and ACTS GeometryIdentifier 216173056991691039 are preserved.

Actual DD4hep/ACTS perturbations of +/-1e-4, 1e-5, 1e-6 rad, at both nominal
and corrected poses, are compared with the unchanged official ACTS derivative
using frozen native track references. Nominal Ry maximum discrepancy is
`8.964e-9 mm/rad` over 3072 vector comparisons; the gate is `2e-5 mm/rad`.
No analytic legacy tilt derivative replaces the native model.

| Fixture | Injection [mrad] | Pede [mrad] | Nominal sigma [mrad] | Post-update [urad] | ACTS chi2/stored-NDF before -> after |
|---|---:|---:|---:|---:|---:|
| Positive Rx, 32 | +1.8 | +1.6622 | 0.23264 | -0.25248 | 0.828764 -> 0.669254 |
| Independent negative Rx, 32 | -1.8 | -2.1773 | 0.23266 | +0.040135 | 0.922513 -> 0.648842 |
| Ry, 1024 | +5.0 | +3.8135 | 0.91215 | -14.044 | 0.602587 -> 0.600885 |

Negative Rx error is -0.3773 mrad (about -1.62 nominal sigma). Ry error is
-1.1865 mrad (about -1.30 nominal sigma). These are finite quantized-sample
results, not exact truth recovery. The Ry post-update gate was prospectively
one quarter of its initial nominal sigma; the observed update also meets the
older 20 urad Rx threshold. Existing Rx assertions were not relaxed.

Ry control/nominal/corrected passes each accept 1024 tracks, five measurements,
zero outliers and two holes. There are 1024 official Mille records and 10240
scalar equations. The unchanged RawTrackerHit tuples and input-file checksum
are verified across fresh processes; only EventHeader/TelescopeChannels enter
reconstruction. Seventy L1 channel IDs differ from the unrotated control.
The tilt-specific nontrivial-channel gate is N/32 (small normal-tilt projection),
while the original in-plane Rx gate remains N/4.

Ry aggregate local residual RMS (u,v) changes from (7.775,7.750) to
(7.756,7.747) um. Aggregate Global X RecHit-minus-Truth RMS changes from
13.985 to 3.319 um. Full orientation error is 1.1865 mrad; the pivot stays fixed.
Truth is used only for generation and these accuracy checks. Pede status is
0 in initial/post/control fits, with zero rejected local fits. Initial Pede
chi2/NDF is 6152.921788/6143=1.001615; post-correction is 1.001624.
The small ACTS improvement is appropriate to a weak, approximately five-sigma
initial signal; ACTS stored NDF and profiled Pede statistical NDF differ.

### Parity and retained limits

| Legacy capability | Native status after this milestone |
|---|---|
| Single-plane in-plane rotation | Positive/negative Rx full actual-channel reconstruction closure |
| Legacy Rx tilt | Native Ry is the same physical axis with opposite sign; +5 mrad native closure validated, at a different amplitude/cohort from legacy |
| Legacy Ry tilt | Native Rz remains unavailable; generic ACTS derivative gate alone is not closure |
| Coupled tilt rotations / SO(3) | Not enabled natively; old failed ordered-Euler cases remain failed historical evidence |
| Full legacy rotation/6-DOF/Controller/Geant4 parity | Not established; legacy code retained |

### Reproduction and evidence

All commands run from the repository root in the existing fixed container.
Use new build/result paths when repeating them; stages refuse existing outputs.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_tilt_20261024_02 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_tilt_20261024_02 -j2

# Each step can instead be invoked separately, in the order printed here:
# geometry data nominal solve correct corrected postsolve control controlsolve check
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_tilt_20261024_02 --result result/native_tilt_ry_20261024_02 \
  --events 1024 --beam validation/telescope_alignment/tilt_beam_validation.json \
  --chi2-cut 1000 --mode l1_ry --step all

for mode in l1_l2_y l1_rx l1_rx_negative l1_y_rx_l2_y; do
  bash environment/run.sh python3 validation/telescope_closure/closure.py \
    --build build/native_tilt_20261024_02 \
    --result result/native_tilt_final_${mode}_20261024_01 \
    --events 32 --chi2-cut 1000 --mode "$mode" --step all
done
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_tilt_20261024_02 --result result/native_tilt_final_l1_l2_y_20261024_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name tilt
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/native_tilt_legacy_20261024_01 \
  /work/build/telescope_consolidation_legacy_20261024_01

# Read-only study of already reconstructed native states, independent of Pede:
bash environment/run.sh python3 validation/telescope_closure/observability.py \
  --native result/native_tilt_broad1024_20261024_01/control/mille.json \
  --output result/native_tilt_observability_20261024_01/all_translation_correlations.json
# Repeat with the baseline control or broad64 control to compare sensitivity.
bash environment/run.sh python3 validation/geometry_probe.py \
  --geometry result/native_rotation_legacy_20261024_01/step1/nominal.xml \
  --output result/native_tilt_observability_20261024_01/legacy_actual_geometry.json
bash environment/run.sh python3 validation/telescope_closure/observability.py \
  --native result/native_rotation_baseline_20261024_01/control/mille.json \
  --legacy-geometry result/native_tilt_observability_20261024_01/legacy_actual_geometry.json \
  --native-geometry result/native_tilt_broad64_20261024_01/data/control/channels_truth.json \
  --output result/native_tilt_observability_20261024_01/frame_mapping.json
```

The broad64/broad1024 control studies used build `native_tilt_20261024_01`:
run `--step geometry`, then `data`, then `control` using `--events 64` and
`--beam validation/telescope_alignment/tilt_beam.json`, or `--events 1024`
and `tilt_beam_validation.json`, respectively. Their source distributions/seeds
are embedded in the immutable generator reports. Re-run with the latest build
in new directories. The weak32 Ry case uses `--mode l1_ry --events 32` without
`--beam`; running through `solve` must refuse before creating Pede steering.

Final closure JSON and TBrowser-readable `rotation.root` are under each
rotation run's `validation/`. Build 01's initial Ry closure remains preserved
at `result/native_tilt_ry_20261024_01/`. Build 02 is the final complete replay.
Every stage saves command, exit code, stdout and output hashes. Official binary
inspection logs are in the observability directory's `decode_ry/` and
`decode_negative_rx/` stages. Existing failed combined development output
`result/native_tilt_regression_l1_y_rx_l2_y_20261024_01/` is retained: changing
Python helper signatures during that process caused an import/signature mismatch.
The final replay used fixed sources and a separate output directory. An early
control invocation was also correctly refused before data preparation completed;
no stage was overwritten.

The final fresh-build replay and the full **18-command** consolidated suite
passed. It includes fresh standalone Geometry/CKF builds, original one-event
JANA/default-cut check, ACTS finite differences, native/legacy Writer comparison,
official mathematical Pede fixture, **49 unit tests** (46 existing plus three
new one-axis boundary tests), safety and preservation. Evidence:
`result/native_tilt_final_l1_l2_y_20261024_01/tilt_regressions/complete.json`.
The weak32 Ry run was correctly rejected by its sensitivity gate before Pede;
its partial outputs remain at `result/native_tilt_weak32_20261024_01/`.

The original Y result remains 32 tracks, +149.14/+203.18 um, and ACTS
37.16731567382813 -> 0.6908491410315036. The combined result remains
Y1=+148.99 um, Rx1=+1.7632 mrad, Y2=+203.18 um. For all three existing
cohorts, nominal/Truth/corrected XML and nominal/corrected/control Mille binaries
are byte-identical to the prior successful milestone, as recorded in
`result/native_tilt_observability_20261024_01/scientific_identity_complete.json`.
The historical 99-track regression also passed: +198.75 um correction,
-199.571 -> -0.821 um residual, ACTS 45.592 -> 1.981.
Preservation verified 221 baseline records and 2046 relocated files unchanged,
including the protected electron-hypothesis diff. ROOT batch write/read-back
passed; interactive TBrowser GUI operation was not tested.

| Maintained file / functions | Change in this milestone |
|---|---|
| `TelescopeMille.cc::Init/Process` | Explicit additional Ry label whitelist and selection of existing ACTS column 4 |
| `TelescopeChannels.cc::main` | Optional bounded angular recipe and explicit seed; baseline generation untouched |
| `closure.py::geometry_step/data_step/solve/main` | Negative Rx and single Ry fixtures, optional study input, pre-Pede sensitivity refusal |
| `closure.py::displaced_xml` | Pass the explicitly selected one-axis chart |
| `rotation.py` | Selected-axis configuration, restricted SO(3)/XML serialization, real-surface finite differences, full tilt-envelope/identity/closure checks |
| `observability.py` | Read-only actual weighted-row profiling, sample/slope/position/quantization diagnostics, actual-pose frame mapping |
| `l1_global_ry.json`, `tilt_beam*.json` | Explicit parameter scope and reproducible beam recipes |
| `test_native_rotation_scope.py` | Signed incremental update, coupled-chart refusal, invalid-update refusal |

The actual inference path remains calibrated native ACTS states -> unchanged
`NativeMilleModel::nativeEquation` -> selected whitened official Mille rows ->
official Pede -> restricted physical SO(3) correction -> fresh DD4hep loading ->
installed ActsGeometryProvider/SurfaceMap -> unchanged JANA measurements and
ACTS CKF/smoothing. No replacement provider, navigator, fitter or material map
was introduced. No legacy scientific code was deleted. Candidates stay inactive;
no merge or push is performed.

## Signed single-axis Ry/Rz completion

This milestone starts at `6b8136428fc81fbbbfad483f75319e9311e68fc1` on
`feature/upstream-acts-geometry`. All earlier results above are retained.
The numerical NativeMilleModel, installed CKF/Navigator/smoother, seeds,
particle hypothesis, calibrated covariance, whitening and selector settings
are unchanged. All new technical evidence is in fresh `result/native_signed_tilt*`
directories; the fresh build is `build/native_signed_tilt_20261024_01`.

### Restricted Rz chart: physical Geometry first

The retained DD4hep 1.36 constructor source is
`result/barrel_geometry_20261023_01/source/SiTrackerBarrel_geo.cpp`.
Lines 58–64 pass `RotationZYX(x_rot.z(0),x_rot.y(0),x_rot.x(0))` to the real
component placement; line 128 places the parent module. XML attribute names
alone therefore do not establish physical Global axes. Source hash and calls
are recorded in `native_signed_tilt_20261024_01_audit/source_reference.json`.

Fresh-process actual sensitive-context and ACTS matrices establish an alternate
zero chart, physically equivalent to the original nominal component:

```
Original zero:   x=-pi/2, y=-pi/2,     z=0
Rz-only chart:   x=0,     y=-pi/2-Rz,  z=+pi/2
Rnew = Exp([0,0,dRz_global]) Rcurrent
```

The alternate zero and +/-5 mrad charts preserve centers, VolumeID and
GeometryIdentifier and agree with the corresponding active Global rotation
on **both DD4hep and ACTS bases**. The initial probes are in
`result/native_signed_tilt_20261024_01_audit/rz_chart_*/`; their independent
verdict is `rz_chart_validation.json`. The separate component-identity probe
is solely a parent-frame diagnostic, not a contained physical closure input.
Only the zero chart and this pure-Rz subgroup are accepted. Rx/Ry combinations,
arbitrary Euler decompositions and unsupported charts are rejected.

`rotate_component` composes the selected SO(3) increment before serializing
this restricted chart. Real-surface finite differences subsequently verify it
at +/-1e-4, 1e-5 and 1e-6 rad around both nominal and corrected poses. The
XML whitelist permits only the L1 module reference/clone and the three L1
rotation attributes required by this equivalent chart; all unrelated
attributes, shapes, materials, segmentation, envelopes and other layers are
compared exactly. Actual eight-corner containment is checked against the
unchanged module box and layer cylinder. The sensitive-center pivot, VolumeID
272631839 and GeometryIdentifier 216173056991691039 remain fixed.

The verified physical migration is unchanged: legacy +Rx -> native -Ry,
legacy +Ry -> native -Rz, and legacy +Rz -> native +Rx. Thus negative native
Ry and Rz test the physically mapped legacy-positive directions. A valid
one-axis chart is not a general SO(3) serializer.

### Prospective inference gates and beam

The declared tilt injections are +/-5 mrad. Gates were declared before fitting:
full profiled design rank, diagonal-scaled condition below 100, formal angular
sigma below 1 mrad, recovery within five initial unscaled nominal sigmas,
post-correction update below one quarter of that initial sigma, original pose
and ID tolerances, and at least N/32 nontrivially changed L1 channel IDs.
Existing Rx and translation gates were not relaxed. Geometry containment is
an additional hard requirement, including derivative perturbations.

The native Rz uncertainty, with Y/Z/Rx/Ry also profiled as diagnostic columns,
is 56.273 mrad for the narrow32 cohort, 3.426 mrad for broad64, and 0.814 mrad
for broad1024. Narrow32 is full rank but cannot resolve a 5 mrad tilt. Its
actual Rz run was refused before Pede steering was created:
`result/native_signed_tilt_weak_rz32_20261024_01/driver/`.
The refused design has sigma 56.273 mrad, with all output/logs preserved.
No tighter covariance, seed constraint or Pede steering change was used.

The beam remains the previously declared bounded uniform recipe: intercepts
Y +/-12 mm and Z +/-10 mm at X=250 mm; independent slopes dy/dx and dz/dx
within +/-0.08. All trajectories fit inside the real seven-plane envelope.
Seeds 2026102402, 2026102403 and 2026102404 are explicitly recorded. The first
is the established comparison cohort; the latter two are newly generated
independent cohorts. Each contains 1024 rays. Four sign/axis fixtures within
a seed share those rays intentionally; they are **three independent cohorts,
not twelve independent experiments**. Pixel pitch, original uncertainties,
geometry and fit settings remain fixed. Inputs contain only EventHeader and
immutable quantized TelescopeChannels. This is a material-free synthetic
geometric test, not migrated Geant4 physics or statistical coverage validation.

Read-only actual weighted ACTS-row studies are in the audit directory's
`design_narrow32/`, `design_broad64/` and `rz_observability.json`. They include
sample-size prefixes, slope/impact-position splits, all translation and
rotation correlations, and bounded-pixel quantization effects. Truth is used
only by the generator and offline accuracy evaluation, never to infer the
corrections.

### Baseline signed closures (seed 2026102402)

| Mode | Injection [mrad] | Initial Pede [mrad] | Formal sigma [mrad] | Post-update [urad] | ACTS chi2/stored-NDF before -> after |
|---|---:|---:|---:|---:|---:|
| Positive Ry, preserved/replayed | +5 | +3.8135 | 0.91215 | -14.044 | 0.602587 -> 0.600885 |
| Negative Ry | -5 | -5.8213 | 0.91213 | -48.826 | 0.603172 -> 0.599151 |
| Negative Rz, legacy-positive direction | -5 | -3.5964 | 0.79965 | +12.239 | 0.599422 -> 0.597452 |
| Positive Rz | +5 | +5.7680 | 0.79966 | -5.112 | 0.602704 -> 0.597618 |

Each case passes full actual-channel, native JANA/ACTS, official Mille/Pede,
physical XML correction and fresh corrected reconstruction closure. All accept
1024 tracks, five measurements, zero outliers and two holes. Initial Pede
rank is one; the diagnostic nuisance matrix has rank five, while the optional
six-column correlation study is not an enabled fit. Initial/final Pede statuses
and rejected-fit diagnostics are retained in each validation report.
The negative Ry, negative Rz and positive Rz physical fixtures change 55, 62
and 77 L1 channel IDs, respectively. The same input-file checksum and channel
tuples are verified across nominal and corrected reconstruction. Full matrices
and poses, not XML angle names or chi2 alone, establish physical correction.

The native stages remain channel-based official Hit Reconstruction -> adapted
official Measurement conversion -> official CKF/smoothing -> unchanged native
ACTS derivative/transport rows -> official Mille Binary/Pede -> restricted
physical SO(3) XML update -> fresh installed ActsGeometryProvider/SurfaceMap
and reconstruction. No provider, navigator, fitter or material map was added.

### Current capability table

| Native parameters | Sensors | Enabled scope | Actual demonstrated closure | Remaining restriction |
|---|---|---|---|---|
| Global Y translations | L1 and L2 | `l1_l2_y`, labels 700102/700202 together | 32-track +0.150/+0.200 mm baseline | No arbitrary translation subset or native X/Z mode |
| In-plane Global Rx | L1 | `l1_rx`, `l1_rx_negative`, label 700104 | Both +/-1.8 mrad | L1 only; pure-Rx chart |
| Y1/Rx1/Y2 | L1/L2 | `l1_y_rx_l2_y` | Existing +Y/+Rx/+Y three-parameter fixture | No simultaneous multiple rotation axes |
| Tilt Global Ry | L1 | `l1_ry`, `l1_ry_negative`, label 700105 | Both +/-5 mrad | Pure-Ry chart, observability and containment gates |
| Tilt Global Rz | L1 | `l1_rz_negative`, `l1_rz`, label 700106 | Both -/+5 mrad | Alternate pure-Rz chart, same gates |
| X/Z, other-layer rotations | Numerical ACTS columns available | No native fit/correction scope | None claimed | Derivative implementation alone is not enabled closure |
| Coupled rotations, arbitrary six-DOF | Legacy implementation retained | Not enabled natively | None claimed | Requires general validated SO(3) serializer and inference gates |
| Sequential/iterative Controller | Legacy stages retained | No native Controller migration | Legacy tests preserved | Native test driver is not an online Controller |
| Geant4/endcap RawHit input | Legacy workflow retained | Native synthetic radial channels only | Historical 99-track regression retained | No silent endcap-to-radial reinterpretation |
| Uncertainty coverage | Formal original-error model | Not statistically certified | Handful of seeds only | Requires adequately powered independent ensemble |

This restores both independent physical legacy tilt axes in the native frame
at the stated bounded synthetic scope. It does not establish full legacy
rotation, multi-layer, six-DOF, material, Geant4 or Controller parity. Original
failed fixed-ordered Rx/Ry finite-rotation evidence remains failed historical
evidence; no scientific assertion was weakened to relabel it as success.

### Independent-cohort diagnostic results

All 12 planned fixtures passed: three independent 1024-ray cohorts per mode.
The sign/axis variants within each seed are paired, not independent trials.
No broad-cohort failure was omitted. The separate narrow32 sensitivity refusal
is reported above and was never sent to Pede.

Error below is **injected minus fitted**; Pull is **(fitted minus injected)/sigma**.
The sigma is the initial unscaled covariance result, checked against the actual
Pede printed nominal error. Post-updates are not combined as independent fits.

| Mode | Seed | Injection [mrad] | Fit [mrad] | Truth-minus-fit [mrad] | Nominal sigma [mrad] | Pull | Tracks |
|---|---:|---:|---:|---:|---:|---:|---:|
| l1_ry | 2026102402 | +5.0 | +3.8135 | +1.1865 | 0.91215 | -1.301 | 1024 |
| l1_ry | 2026102403 | +5.0 | +5.1314 | -0.1314 | 0.87768 | +0.150 | 1024 |
| l1_ry | 2026102404 | +5.0 | +3.9707 | +1.0293 | 0.91740 | -1.122 | 1024 |
| l1_ry_negative | 2026102402 | -5.0 | -5.8213 | +0.8213 | 0.91213 | -0.900 | 1024 |
| l1_ry_negative | 2026102403 | -5.0 | -4.2160 | -0.7840 | 0.87768 | +0.893 | 1024 |
| l1_ry_negative | 2026102404 | -5.0 | -5.5136 | +0.5136 | 0.91740 | -0.560 | 1024 |
| l1_rz | 2026102402 | +5.0 | +5.7680 | -0.7680 | 0.79966 | +0.960 | 1024 |
| l1_rz | 2026102403 | +5.0 | +5.0928 | -0.0928 | 0.78074 | +0.119 | 1024 |
| l1_rz | 2026102404 | +5.0 | +5.4945 | -0.4945 | 0.78053 | +0.634 | 1024 |
| l1_rz_negative | 2026102402 | -5.0 | -3.5964 | -1.4036 | 0.79965 | +1.755 | 1024 |
| l1_rz_negative | 2026102403 | -5.0 | -4.6456 | -0.3544 | 0.78075 | +0.454 | 1024 |
| l1_rz_negative | 2026102404 | -5.0 | -4.3078 | -0.6922 | 0.78052 | +0.887 | 1024 |

| Mode | Mean truth-minus-fit [mrad] | Sample SD [mrad] | Mean nominal sigma [mrad] | Pull mean | Pull sample SD |
|---|---:|---:|---:|---:|---:|
| l1_ry | +0.6948 | 0.7198 | 0.9024 | -0.758 | 0.791 |
| l1_ry_negative | +0.1836 | 0.8520 | 0.9024 | -0.189 | 0.953 |
| l1_rz_negative | -0.8167 | 0.5356 | 0.7870 | +1.032 | 0.663 |
| l1_rz | -0.4518 | 0.3396 | 0.7870 | +0.571 | 0.424 |

These are three-point sample moments (only two degrees of freedom for each
sample variance), not calibrated uncertainty or coverage estimates. Both Rz
signs have positive initial pulls in these three paired cohorts. This is a
trend worth checking with more independent seeds; the present sample cannot
separate a systematic bias from finite quantization/sample fluctuations.
Neither errors, priors, selection nor steering were changed to improve it.
No larger campaign was launched. The next statistical study should keep the
same recipe and inferential settings and use a prospectively chosen, adequately
powered number of independent seeds.

Each row's full generated slope range/RMS, seed, ray-cohort hash, immutable
channel checksum, initial Pede status, post-update, accepted count and nominal/
corrected ACTS chi2 are in
`result/native_signed_tilt_20261024_01_audit/cohort_summary/output/report.json`.
`cohorts.root` next to it contains eight TBrowser-readable estimate/Pull objects;
ROOT batch read-back verifies all graph point and histogram entry counts.
Per-run `validation/rotation.root` preserves the full chi2 and residual plots.
No interactive TBrowser GUI test is claimed.

### Regression and preservation results

The fresh Plugin build and all five established modes passed. For two-Y,
positive Rx, negative Rx, combined Y/Rx/Y and positive Ry, the nominal/Truth/
corrected XML and nominal/corrected/control Mille binaries are **byte-identical**
to their existing successful references. Evidence:
`result/native_signed_tilt_20261024_01_audit/baseline_identity.json`.
The original Y result remains +149.14/+203.18 um and ACTS
37.16731567382813 -> 0.6908491410315036; the protected positive Ry replay
remains +3.8135 mrad and 0.6025865641314022 -> 0.6008848699318217.

The **18-command** consolidated suite passed, including fresh standalone
Geometry/CKF builds, installed-component one-event reconstruction, actual ACTS
finite differences, native/legacy Mille equivalence, official mathematical Pede
fixture, **51 unit tests** (49 existing plus two new Rz chart tests), safety and
preservation. Logs:
`result/native_signed_tilt_regression_l1_l2_y_20261024_01/signed_tilt_regressions/`.
Preservation confirms 221 baseline records and 2046 relocated files unchanged,
including the protected electron-hypothesis implementation. The historical
99-track workflow passed in `result/native_signed_tilt_legacy_20261024_01/`,
retaining +198.75 um correction, -199.571 -> -0.821 um residual and
45.592 -> 1.981 ACTS chi2/stored-NDF.

Pinned upstream patch reproduction regenerated all nine local adaptation
patches byte-for-byte, with no changes to the external EICrecon checkout.
Actual official `inspectMilleBinary` logs for negative Ry and both Rz signs
are in the audit directory's `decode_l1_*/` stages. Every closure independently
checks decoded native coefficients against the actual covariance-whitened ACTS
column. Each signed tilt initial/corrected finite-difference gate checks 3072
vectors. The primary Rz maximum error is 1.106e-8 mm/rad, well below the
unchanged 2e-5 gate. Full matrices, center pivots, bounds and ID preservation
are checked at each perturbation, not just at the nominal pose.

All 12 signed-cohort initial/post/control Pede fits ended normally (status 0),
with zero rejected local fits. Pede warnings/logs remain unsuppressed and
unmodified. No error rescaling was applied. Unsuccessful developmental test
setup and the expected weak-design refusal do not represent successful physics
runs; existing partial and historical outputs remain preserved.

### Changed source and reproduction

- `TelescopeMille.cc::Init/Process`: explicit label 700106/Global Rz whitelist
  and selection of the unchanged ACTS rotation column 5. No new equations.
- `rotation.py::axis/rotation_label/labels/config_name/injected_rotation`:
  explicit signed Ry/Rz fixtures and scope routing.
- `rotation.py::rotate_component/pose_checks/physical_derivatives/check`:
  pure-Rz chart, actual three-dimensional containment, exact XML whitelist,
  sign-specific real-Geometry finite differences and closure checks.
- `closure.py::geometry_step/solve/main`: signed modes and the actual chosen
  tilt's pre-Pede sensitivity guard. Failed-design evidence is saved before
  refusal. Existing fit settings and numerical acceptance thresholds remain.
- `observability.py::analyze`: adds Rz information to slope/position subsets.
- `cohort_summary.py`: offline independent-cohort accounting and ROOT export;
  includes any valid initial fits even if later closure fails, rather than
  conditioning initial-fit statistics on closure success.
- `l1_global_rz.json`, `tilt_beam_seed3.json`, `tilt_beam_seed4.json`: explicit
  parameter scope and two additional independent seeds, same angular recipe.
- `test_native_rotation_scope.py`: Rz chart/composition tests, all cross-axis
  composition refusals, and invalid-axis safety with the new supported axis.

The following are the executed build/run interfaces. Set new output paths when
repeating them: all existing stages and result directories must remain immutable.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_signed_tilt_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_signed_tilt_20261024_01 -j2

# In this order: negative Ry, legacy-positive-direction Rz, opposite Rz.
for mode in l1_ry_negative l1_rz_negative l1_rz; do
  bash environment/run.sh python3 validation/telescope_closure/closure.py \
    --build build/native_signed_tilt_20261024_01 \
    --result result/native_signed_tilt_primary_${mode}_20261024_01 \
    --events 1024 --beam validation/telescope_alignment/tilt_beam_validation.json \
    --chi2-cut 1000 --mode "$mode" --step all
done
# Each --step is also independently runnable, in order:
# geometry data nominal solve correct corrected postsolve control controlsolve check
# solve/postsolve include actual nominal/corrected Geometry finite differences.

for seed in 3 4; do
  for mode in l1_ry l1_ry_negative l1_rz_negative l1_rz; do
    bash environment/run.sh python3 validation/telescope_closure/closure.py \
      --build build/native_signed_tilt_20261024_01 \
      --result result/native_signed_tilt_seed${seed}_${mode}_20261024_01 \
      --events 1024 --beam validation/telescope_alignment/tilt_beam_seed${seed}.json \
      --chi2-cut 1000 --mode "$mode" --step all
  done
done
# The actual cohort drivers additionally retain stdout and exit codes even on
# failure; see each run's driver/command.json, stdout.log and exit.json.

for mode in l1_l2_y l1_rx l1_rx_negative l1_y_rx_l2_y; do
  bash environment/run.sh python3 validation/telescope_closure/closure.py \
    --build build/native_signed_tilt_20261024_01 \
    --result result/native_signed_tilt_regression_${mode}_20261024_01 \
    --events 32 --chi2-cut 1000 --mode "$mode" --step all
done
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_signed_tilt_20261024_01 \
  --result result/native_signed_tilt_regression_l1_ry_20261024_01 \
  --events 1024 --beam validation/telescope_alignment/tilt_beam_validation.json \
  --chi2-cut 1000 --mode l1_ry --step all
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_signed_tilt_20261024_01 \
  --result result/native_signed_tilt_regression_l1_l2_y_20261024_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name signed_tilt
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/native_signed_tilt_legacy_20261024_01 \
  /work/build/telescope_consolidation_legacy_20261024_01

# This one must refuse at solve, before Pede:
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_signed_tilt_20261024_01 \
  --result result/native_signed_tilt_weak_rz32_20261024_01 \
  --events 32 --chi2-cut 1000 --mode l1_rz_negative --step all

bash environment/run.sh python3 validation/telescope_closure/observability.py \
  --native result/native_tilt_broad1024_20261024_01/control/mille.json \
  --output result/native_signed_tilt_20261024_01_audit/rz_observability.json
bash environment/run.sh python3 -m unittest discover -s validation -p 'test_*.py'
bash environment/run.sh python3 validation/check_safety.py
python3 validation/verify_preservation.py

# Read-only external source audit; use the pinned local checkout, never edit it.
python3 validation/telescope_factories/upstream_diff.py \
  --source /Users/tkumaoka/eic/EICrecon \
  --output result/native_signed_tilt_20261024_01_audit/upstream_diffs
# Compare every generated patch with the same filename under:
# localDetEICrecon/experimental/telescope/upstream_diffs/
```

To reproduce the cohort summary, run
`python3 validation/telescope_closure/cohort_summary.py --runs RUN1 ... RUN12 --output-dir NEW_RESULT_DIR`
in the container. The exact 12 paths, order and output location are recorded in
`result/native_signed_tilt_20261024_01_audit/cohort_summary/command.json`.
The four seed-2026102402 inputs are the positive Ry regression and three primary
signed runs; the other eight are the seed3/seed4 runs above. Repeated runs with
the same seed within one mode are rejected as independent observations.
All datasets, ROOT outputs and detailed logs remain local and excluded from Git.
Only maintained source, configurations, tests and this report belong in the
milestone commit. No push, merge, production activation or legacy removal occurs.

## Coupled native Ry/Rz SO(3) milestone

Starting commit: `6d772125b78930f7e8751786b8932281bdee3534`, branch
`feature/upstream-acts-geometry`, initially clean. The scope is **SiMAPS L1
Global Ry and Rz increments only**, labels 700105 and 700106. No free Rx,
translations, other-layer rotations or arbitrary six-DOF scope was enabled.
The numerical NativeMilleModel and official ACTS derivatives/transport,
CKF/Navigator/filter/smoother, seed, electron hypothesis, covariance, whitening
and existing selection are unchanged. No legacy code or results were removed.

### Pose definition and actual XML representation

Truth is defined by a **single rotation vector**, not an ordered Euler product:

```
w_truth = (0, +0.0025, -0.0025) rad, or its negative
D_truth = Exp(w_truth) D_nominal
D_new = Exp((0, deltaRy, deltaRz)) D_current
```

D is the sensitive-to-world matrix; the sensitive-center position is held
fixed. Updates are active left-Global SO(3) rotations. They act on the full
current matrix: their commutator-generated Rx terms are retained, never reset
to zero. The two-dimensional increment set is **not a closed subgroup**.
Rx is not an additional independent fitted parameter.

The pinned `SiTrackerBarrel_geo.cpp` component call remains
`RotationZYX(x_rot.z(0),x_rot.y(0),x_rot.x(0))`. Actual converter contexts fix
the parent module basis in this telescope to
`M=[[0,0,1],[-1,0,0],[0,-1,0]]`. In its verified effective convention,
`D=M C`, where `C=Rx(xml_x) Ry(xml_y) Rz(xml_z)`. This statement is checked
against actual DD4hep/ACTS matrices rather than inferred from XML axis names.
It applies to this fixed barrel module mounting, not an arbitrary detector.

`rotation.py::rotate_coupled_component` first computes the target world matrix,
then `C_target=M^T D_target`. For `cy=hypot(C00,C01)>=1e-6`, it extracts a
deterministic chart using

```
x = atan2(-C12, C22)
y = atan2(C02, cy)
z = atan2(-C01, C00)
```

It reconstructs that matrix and requires agreement within `5e-13` **before
mutating XML**. Near a singular chart, only identity, exact pure-Ry and exact
pure-Rz targets use their previously validated one-axis charts. Other mixed
near-singular targets are refused, not guessed. Current pose norm is bounded
by 10 mrad, with known Rx commutator terms bounded by 0.1 mrad; increments
must have exactly two finite components and norm at most 10 mrad. Actual
unchanged module/layer containment is an additional stricter physical gate.
This is a bounded telescope serializer, not general six-DOF Geometry support.

The real-constructor forward -> nonparallel update -> inverse update -> inverse
forward chain verifies both DD4hep and ACTS matrices, all centers and IDs.
The single-vector pose differs from `Ry(2.5 mrad) Rz(-2.5 mrad)` by about
3.125 urad, explicitly demonstrating why those Truth definitions cannot be
interchanged. At the chosen two-axis injection, the normal half extent is
about 0.275 mm inside the existing 0.325 mm module half thickness. All eight
sensor corners are checked against the actual module box and cylindrical
layer envelope. XML comparisons permit only the L1 module reference/clone and
required L1 rotation attributes; materials, shapes, positions, segmentation,
envelopes and other layers remain exact. L1 VolumeID 272631839 and ACTS ID
216173056991691039 are preserved.

### Observability and scope of the rank condition

Original covariance-weighted ACTS rows are locally profiled as
`N=sum(G_i^T P_i G_i)`, with `P_i=I-Q_i Q_i^T` from the four-column local
track design. Local rank four remains mandatory. Same-plane Ry/Rz columns
can constrain just **one global combination per track**: every one of the
4096 nominal pilot tracks has global rank one, while their accumulated
information has rank two because impact positions vary. Repeating an identical
weak track does not create the missing combination.

The previous validation helper assumed per-track global full rank. That was
appropriate for its existing translation tests but incorrectly blocked the
new same-sensor scope. `validation/telescope_alignment/check.py::profile`
now has an explicit `require_global_rank=True` default. **Only the selected
coupled callers** set it false while retaining the unchanged global full-rank
assertion on the summed matrix. No equations, track weights, local profiling
or fit parameters were altered. New unit tests prove rank-one track sums can
be full rank with diverse impact ratios, and remain rank deficient when the
same weak information is merely repeated. Old assertions stay enabled by default.

Prospective gates and seeds are recorded in
`result/native_coupled_tilt_20261024_01_audit/prospective_plan.json`:

- +/- `(Ry,Rz)=(2.5,-2.5)` mrad; one exponential per Truth pose.
- Formal sigmas below **0.5 mrad** for both selected axes, including the
  diagnostic marginalization over unselected X/Y/Z/Rx columns.
- Global full rank and diagonal-scaled condition below 100 before Pede.
- Each initial truth error below five nominal sigmas, joint squared
  Mahalanobis error below 25, and full-matrix orientation error below
  `5 sqrt(max eigenvalue(covariance))` and below its original misalignment.
- Each remaining fitted update below one quarter of its **initial** nominal
  sigma; unchanged matrix/pivot/ID, residual, chi2 and immutable-channel gates.
- At least N/32 nontrivially changed L1 channels, with unchanged pixel pitch.

The original broad1024 cohort predicts two-parameter sigmas 0.912/0.800 mrad,
rank two, correlation -0.00195 and condition 1.0039. Full rank is insufficient
for the declared amplitude/precision target. The actual coupled 1024 run is
refused before Pede in `result/native_coupled_tilt_weak1024_20261024_02/`.
Its diagnostic marginal sigmas are 0.945/0.814 mrad. No steering is created.

Four times as many independent rays from the **same** bounded angular recipe
were justified by the predicted factor-two sensitivity improvement, then
checked using actual native tracks before solving. The pilot4096 two-parameter
matrix has sigmas 0.44424/0.38665 mrad, correlation -0.01476 and condition
1.02997. Including all unselected translation/Rx nuisance columns gives
0.46125/0.39514 mrad and condition about 1.74: the result is not forced by
hiding a strongly degenerate component. All other sensor poses, including
L0/L2/L3/L4 references, and independent L1 translation/Rx increments are held
fixed as the explicitly declared two-parameter model.

The unchanged intercept/slope recipe is Y +/-12 mm, Z +/-10 mm at X=250 mm,
and slopes +/-0.08. Only the optional bounded-study event limit was extended
from 1024 to 4096; baseline generation and the no-recipe limit remain unchanged.
Seeds 2026102402/03/04 define three independent ray cohorts. Opposite poses
share rays within each seed. The first 1024 rays are shared with earlier signed
studies; larger prefixes and reruns are not extra independent experiments.
No larger Geant4 campaign, material map or measurement-error change was made.

Read-only matrices, prefix sensitivities, slope/impact splits and quantization
bounds are in `rank_and_sensitivity_4096_02.json` under the audit directory.
Per-track rank counts are explicitly recorded. Finite-pixel, finite-sample
errors and original nominal uncertainties are reported without rescaling.

### Full actual reconstruction closure

The architecture remains actual tilted DD4hep Truth -> segmented immutable
TelescopeChannels -> nominal installed EICrecon geometry service/SurfaceMap ->
current Hit/Measurement conversion -> official ACTS CKF and smoothing ->
unchanged native derivative/transport -> selected whitened Mille rows ->
official Pede -> physical matrix/XML update -> fresh corrected eicrecon process
on the same channels. Truth enters only generation and offline validation.

Each nominal/corrected derivative gate perturbs **both** physical columns 4/5
at +/-1e-4, 1e-5 and 1e-6 rad, reloads the actual constructor, and compares
frozen native-ray intersections against the official ACTS matrix. It also
checks the current full pose, sensitive pivot, IDs and physical containment.
Each gate makes 24576 vector comparisons for 4096 tracks, with the original
`2e-5 mm/rad` tolerance. Nonparallel current-pose updates preserve generated
cross-axis terms. No legacy analytical derivative replaces the official one.

The pilot recovers `(Ry,Rz)=(+1.5298,-1.7425) mrad` from injection
`(+2.5,-2.5) mrad`, with formal errors `(0.44424,0.38665) mrad`.
Full truth-to-corrected matrix distance is **1.23089 mrad**, versus 3.53553 mrad
initially; centers do not move. Squared Mahalanobis error is 8.4834.
Remaining updates are `(-13.745,-8.154) urad`. These small post-updates are
self-consistency, not exact Truth recovery: the initial pulls are approximately
`(-2.18,+1.96)`. ACTS chi2/stored-NDF improves 0.59939283 -> 0.59861842;
local RMS (u,v) changes (7.7664,7.7175) -> (7.7635,7.7104) um.
Pede chi2/NDF is 24519.078877/24574=0.9977651, status 0, zero rejected fits.
All 4096 tracks have five measurements, zero outliers and two holes.
The opposite pilot recovers `(-2.8432,+2.9356) mrad`, with full orientation
error 0.55456 mrad and post-updates `(+7.309,+29.788) urad`.

### Development failures retained

The following are preserved, not represented as successful closures:

- `native_coupled_tilt_seed2_l1_ry_rz_20261024_01`: nominal 1 urad pure-Rz
  perturbation was incorrectly refused by the new chart guard. Reusing the
  existing validated pure-Rz chart fixed this demonstrated omission; mixed
  near-singular targets remain refused.
- The corresponding `_02` and `native_coupled_tilt_weak1024_20261024_01`:
  stopped at the obsolete per-track global-rank assumption, before Pede.
- `native_coupled_tilt_seed4_l1_ry_rz_20261024_01`: a newly added diagnostic
  JSON rank counter contained a NumPy integer. Explicit Python integer
  conversion fixed export; the data and physics were unchanged. A fresh `_02`
  is used for its replay. The initial partial diagnostic JSON is also retained.

Final successful seed2 pilots use `_03`; no failed directory was overwritten,
reused or deleted. Scientific tolerances, injected amplitudes, errors and
selection were not changed in response to these failures.

### Independent coupled-cohort results

All six planned scientific fixtures passed: three independent 4096-ray cohorts
with paired opposite rotation vectors. Technical retries use the same seed and
channel payload and are not additional independent samples. Errors below use
**fit minus injection**; pulls are the marginal initial error divided by its
initial unscaled nominal sigma. Both components belong to one joint Pede fit.

| Mode / seed | Fit Ry / Rz [mrad] | Sigma Ry / Rz [mrad] | Pull Ry / Rz | Correlation | Full pose error [mrad] |
|---|---:|---:|---:|---:|---:|
| l1_ry_rz / 2026102402 | +1.5298 / -1.7425 | 0.44424 / 0.38665 | -2.184 / +1.959 | -0.01476 | 1.23089 |
| l1_ry_rz_negative / 2026102402 | -2.8432 / +2.9356 | 0.44423 / 0.38666 | -0.773 / +1.127 | -0.01476 | 0.55456 |
| l1_ry_rz / 2026102403 | +2.7483 / -2.3224 | 0.44364 / 0.38131 | +0.560 / +0.466 | -0.00165 | 0.30528 |
| l1_ry_rz_negative / 2026102403 | -2.5690 / +2.7642 | 0.44365 / 0.38131 | -0.156 / +0.693 | -0.00166 | 0.27306 |
| l1_ry_rz / 2026102404 | +2.2995 / -2.8231 | 0.45295 / 0.38164 | -0.443 / -0.847 | -0.00068 | 0.38025 |
| l1_ry_rz_negative / 2026102404 | -2.6245 / +2.4294 | 0.45295 / 0.38163 | -0.275 / -0.185 | -0.00070 | 0.14312 |

| Marginal series (N=3) | Mean fit-minus-truth [mrad] | Error sample SD [mrad] | Mean nominal sigma [mrad] | Pull mean / sample SD |
|---|---:|---:|---:|---:|
| l1_ry_rz_Ry | -0.3075 | 0.6163 | 0.4469 | -0.689 / 1.388 |
| l1_ry_rz_Rz | +0.2040 | 0.5408 | 0.3832 | +0.526 / 1.404 |
| l1_ry_rz_negative_Ry | -0.1789 | 0.1450 | 0.4469 | -0.401 / 0.327 |
| l1_ry_rz_negative_Rz | +0.2097 | 0.2575 | 0.3832 | +0.545 / 0.668 |

The machine-readable summary keeps **truth minus fit** as its error field and
explicitly states the opposite Pull convention; the display table above flips
that field to fit minus Truth. No initial/post uncertainties are added together.
Four marginal series are not twelve independent statistical experiments.
The observed Pull sample SD ranges from about 0.33 to 1.40, and one pilot has
a relatively large joint error despite a very small remaining update.
The Rz trend is not universally positive in these larger cohorts. These
three-point moments neither establish nor rule out bias or uncertainty
miscalibration. Successful Geometry/derivative/reconstruction closure is
**not** a statistically calibrated uncertainty model.

Each final `validation/report.json` records the injected vector and its full
physical increment matrix (`injected_matrix`), recovered vector, initial
covariance/correlation, joint error, actual full-matrix orientation distance,
pivot/center differences, reconstruction metrics and complete Pede diagnostics.
Actual Truth and corrected DD4hep/ACTS matrices are in the independent sensor
audit JSON files, not inferred from serialized Euler attributes. All six runs
have 4096 accepted tracks and initial/post/control fits, with no scientific
closure failure, sensitivity refusal or non-convergence in the admitted 4096
cohorts. The separate 1024 refusal and technical retries are listed explicitly.

The cohort summary is
`result/native_coupled_tilt_20261024_01_audit/cohort_summary/output/report.json`;
`cohorts.root` beside it contains eight TBrowser-readable marginal estimate/Pull
objects, with all point/entry counts checked by ROOT batch read-back. Individual
`validation/rotation.root` files retain full residual/chi2 distributions. GUI
TBrowser operation itself was not tested.

### Separate prospective single-axis uncertainty study (not executed)

A larger study should be a separate campaign, not automatic continuation of
this Geometry milestone. A concrete initial design is 800 independent seeds
2026110001 through 2026110800, 1024 rays each, the same fixed broad recipe and
original single-axis +/-5 mrad Ry/Rz configurations. Four sign/axis fixtures
share rays within each seed; only the 800 seed cohorts are independent.

Score **initial** Pede estimates and unscaled sigmas, before correction or
closure selection. Predeclare marginal 68.27%/95% interval coverage, Pull
mean/SD and bias as endpoints; report simultaneous Wilson coverage intervals
with an eight-endpoint family-wise adjustment. At nominal 68% binomial coverage,
800 independent cases give roughly a 4.5 percentage-point adjusted half-width;
this is a precision target, not a guarantee of correct coverage or power for
arbitrarily small bias. Record inference availability and conditional coverage
separately, retaining every refusal, solver warning and failure. Do not
silently drop missing fits or use correction-success selection. If inference
availability is materially reduced, investigate that selection before making
coverage claims. No rescaling, steering changes or post-hoc seed replacement
belongs in that preregistered study.

This would be 3200 physical fixtures (about 3.28 million synthetic events before
reconstruction passes), requiring a separate storage/runtime budget. It has
**not** been launched and no production Geometry is activated.

### Preserved regressions and current capability limits

All eight established native modes were rerun: two-Y, +/-Rx, Y/Rx/Y, +/-Ry and
+/-Rz. Nominal/Truth/corrected XML, nominal/corrected/control Mille binaries,
and input channel payloads are exact matches to the preceding successful
references (`audit/baseline_identity.json`). The old signed-cohort summary was
also reproduced with unchanged statistics for all 12 historical fixtures.
The final **18-command** suite and **57 tests** (51 existing plus six added
matrix/rank tests) passed, including standalone Geometry/CKF, actual derivatives,
native/legacy mathematical equivalence, Pede, safety and preservation. Final
logs are under
`result/native_coupled_tilt_regression_l1_l2_y_20261024_01/coupled_final_regressions/`.
The earlier successful `coupled_tilt_regressions/` is retained as well.

The preserved Y result is +149.14/+203.18 um with ACTS
37.16731567382813 -> 0.6908491410315036. The historical 99-track regression
passed in `result/native_coupled_tilt_legacy_20261024_01/`, retaining +198.75 um,
-199.571 -> -0.821 um residual and 45.592 -> 1.981 ACTS chi2/stored-NDF.
The nine pinned upstream adaptation patches reproduce byte-for-byte without
changing the external checkout. Preservation confirms 221 baseline records,
2046 relocated files and the protected electron implementation unchanged.
Official `inspectMilleBinary` output is in
`result/native_coupled_tilt_20261024_01_audit/official_binary_inspection/`;
all fitted native coefficients are independently checked against original
whitened ACTS columns. No warning or unsuccessful output was suppressed.

| Capability | Status after this milestone |
|---|---|
| Existing translations and all signed single-axis rotations | Preserved, scientific artifacts equivalent |
| Coupled L1 Ry/Rz | Implemented, enabled, actual derivatives and joint Pede validated, full reconstruction closure for both declared vectors and three seeds |
| Matrix update of a known bounded current pose | Noncommuting forward/inverse actual-Geometry chain validated |
| General free Rx/Ry/Rz or six-DOF fitting | Not enabled; current Rx terms are known composition effects, not a free parameter |
| Translations plus coupled tilts, or additional aligned sensors | Unsupported native scope |
| Arbitrary Survey Geometry/chart/import | Unsupported; fixed telescope parent mounting and explicit chart bounds remain |
| Native iterative Controller, recovery and version-chain migration | Not implemented; current closure driver makes one correction and separately evaluates remaining updates |
| Original Geant4/endcap RawHit compatibility | Legacy retained; not migrated or silently reinterpreted |
| Statistical unbiasedness/nominal coverage | Not established; small-cohort diagnostics only |

This matches the **physical matrix-update principle** of legacy general SO(3)
for a narrower native parameter subset. It does not establish full legacy
functional parity. The historical failed fixed-ordered Rx/Ry finite-rotation
case remains failed evidence; it was neither rerun with weaker assertions nor
relabelled as resolved by the new native test. The legacy scientific code and
Controller remain available and unchanged.

### Source changes and exact reproduction

- `rotation.py::is_coupled/injected_rotation/labels/config_name`: explicit
  coupled vectors and labels; all existing single-axis routes preserved.
- `component_matrix/rotate_coupled_component`: target-first, bounded physical
  matrix composition and verified constructor-compatible XML extraction.
- `pose_checks/coupled_pose_gate/coupled_physical_derivatives`: real pose,
  corner/ID, noncommutativity/inverse and both-column finite differences.
- `correct/check`: one simultaneous physical update, full-matrix and joint
  covariance error evaluation, independent fresh reconstruction validation.
- `closure.py::geometry_step/solve/main`: explicit vector provenance, selected
  precision/refusal gate and optional manually runnable pose gate.
- `TelescopeMille.cc::Init`: only the additional exact {700105,700106} set;
  existing numerical columns, local model and whitening unchanged.
- `TelescopeChannels.cc`: only the optional bounded-cohort count limit increased.
- `check.py::profile`: explicit partial per-track information option, default
  strict behavior preserved; summed full rank still mandatory.
- `observability.py`: selected two-column matrices and per-track rank diagnostics.
- `cohort_summary.py`: paired-vector marginal summaries, correlations and ROOT
  export without treating components or signs as independent experiments.
- `test_native_rotation_scope.py`: six new matrix/chart/rank tests.
- `l1_global_ry_rz.json`: exact physical two-parameter scope, no new equation model.

All commands run from the repository root. Change result/build names when
repeating them; existing directories and failed artifacts remain immutable.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_coupled_tilt_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_coupled_tilt_20261024_01 -j2

for mode in l1_ry_rz l1_ry_rz_negative; do
  bash environment/run.sh python3 validation/telescope_closure/closure.py \
    --build build/native_coupled_tilt_20261024_01 \
    --result result/native_coupled_tilt_seed2_${mode}_20261024_03 \
    --events 4096 --beam validation/telescope_alignment/tilt_beam_validation.json \
    --chi2-cut 1000 --mode "$mode" --step all
done
# Each stage is independently runnable with --step, in this order:
# geometry data [coupled_pose] nominal solve correct corrected postsolve control controlsolve check
# coupled_pose is automatically required before the first coupled derivative gate.

for seed in 3 4; do
  for mode in l1_ry_rz l1_ry_rz_negative; do
    # Seed4 positive uses suffix _02 for the successful diagnostic-export replay.
    suffix=01
    if [[ $seed == 4 && $mode == l1_ry_rz ]]; then suffix=02; fi
    bash environment/run.sh python3 validation/telescope_closure/closure.py \
      --build build/native_coupled_tilt_20261024_01 \
      --result result/native_coupled_tilt_seed${seed}_${mode}_20261024_${suffix} \
      --events 4096 --beam validation/telescope_alignment/tilt_beam_seed${seed}.json \
      --chi2-cut 1000 --mode "$mode" --step all
  done
done
# Actual driver/command.json, stdout.log and exit.json also retain every failure.

# Expected sensitivity refusal before Pede:
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_coupled_tilt_20261024_01 \
  --result result/native_coupled_tilt_weak1024_20261024_02 \
  --events 1024 --beam validation/telescope_alignment/tilt_beam_validation.json \
  --chi2-cut 1000 --mode l1_ry_rz --step all

# Read-only actual weighted information, independent of the solver:
bash environment/run.sh python3 validation/telescope_closure/observability.py \
  --native result/native_coupled_tilt_seed2_l1_ry_rz_20261024_03/nominal/mille.json \
  --output result/native_coupled_tilt_20261024_01_audit/rank_and_sensitivity_4096_02.json

for mode in l1_l2_y l1_rx l1_rx_negative l1_y_rx_l2_y l1_ry l1_ry_negative l1_rz_negative l1_rz; do
  extra=(--events 32)
  if [[ $mode == l1_ry || $mode == l1_ry_negative || $mode == l1_rz || $mode == l1_rz_negative ]]; then
    extra=(--events 1024 --beam validation/telescope_alignment/tilt_beam_validation.json)
  fi
  bash environment/run.sh python3 validation/telescope_closure/closure.py \
    --build build/native_coupled_tilt_20261024_01 \
    --result result/native_coupled_tilt_regression_${mode}_20261024_01 \
    --chi2-cut 1000 --mode "$mode" --step all "${extra[@]}"
done
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_coupled_tilt_20261024_01 \
  --result result/native_coupled_tilt_regression_l1_l2_y_20261024_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name coupled_final
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/native_coupled_tilt_legacy_20261024_01 \
  /work/build/telescope_consolidation_legacy_20261024_01
bash environment/run.sh python3 -m unittest discover -s validation -p 'test_*.py'
bash environment/run.sh python3 validation/check_safety.py
python3 validation/verify_preservation.py
python3 validation/telescope_factories/upstream_diff.py \
  --source /Users/tkumaoka/eic/EICrecon \
  --output result/native_coupled_tilt_20261024_01_audit/upstream_diffs
```

The cohort-summary command is retained verbatim with all six paths in
`audit/cohort_summary/command.json`. It uses the maintained interface
`python3 validation/telescope_closure/cohort_summary.py --runs RUN1 ... RUN6 --output-dir NEW_RESULT_DIR`.
All audit paths in this section are below
`result/native_coupled_tilt_20261024_01_audit/` unless fully specified.
The large single-axis uncertainty design above is prospective only, not an
executed or passing test. No push, merge or Geometry activation is performed.

## Three-axis native SO(3) milestone

Starting commit `34a9da9d8848b2b8b1a54eb0f0b2572d3517e959`, branch
`feature/upstream-acts-geometry`, initially clean. This extension admits only
SiMAPS L1 physical Global Rx/Ry/Rz, labels 700104/700105/700106 in radians,
using original ACTS derivative columns 3/4/5. All L1 translations and other
sensor poses, including reference L0/L2/L3/L4, remain fixed. This is not a
six-DOF or multiple-aligned-sensor fit. NativeMilleModel, official geometry
services, CKF/Navigator/filter/smoother, seed, electron hypothesis, covariance,
Cholesky whitening and capture window remain unchanged.

### Contract, constructor and prospective gates

Truth is one active left-Global rotation vector about the sensitive center:

```
w = (+0.0018, +0.0025, -0.0025) rad, or its exact negative
Dtruth = Exp(w) Dnominal
Dnew = Exp([dRx,dRy,dRz]) Dcurrent
```


The prospectively fixed positive-vector matrix `Exp(w)` is

```
[0.9999937500081979, 0.002502243438720573, 0.002497743444623082]
[-0.002497743444623082, 0.9999952550062239, -0.001803120273904751]
[-0.002502243438720573, 0.001796870282102681, 0.9999952550062239]
```

The opposite-vector matrix is its transpose; both multiply the actual nominal
sensitive basis on the left.

All three components are nonzero; the magnitude is about 3.967 mrad.
No independent Euler-angle additions are used. Full current matrices retain
all cross-axis commutators. The target is computed first, then serialized
through the same pinned `SiTrackerBarrel_geo.cpp` component constructor
`RotationZYX(z,y,x)`, lines 58–64, with its actual module placement at line128.
Source: `result/barrel_geometry_20261023_01/source/SiTrackerBarrel_geo.cpp`.
The verified fixed telescope mapping remains `D=M Rx(xml_x) Ry(xml_y) Rz(xml_z)`,
with `M=[[0,0,1],[-1,0,0],[0,-1,0]]`. The nonsingular extraction and 5e-13
matrix-before-mutation requirement are unchanged. The explicit full-vector
entry permits three finite components and a current/increment norm up to
10 mrad, while the old two-axis entry still refuses free Rx. Near-singular
mixed charts remain refused; only exact validated one-axis charts are used,
including pure Rx for the nominal finite-difference probes. Actual module
and cylindrical layer containment impose stricter physical bounds.

Before any three-parameter Pede fit, the selected fixture's sensitive half
extents were checked as approximately (0.274999,50.089981,50.089669) mm,
within the unchanged module half extents (0.325,50.25,50.25) mm. All eight
actual DD4hep corners, positions, pivots, VolumeID and ACTS GeometryIdentifier
are checked after reload; unrelated XML/material/segmentation changes are
forbidden. L1 IDs remain VolumeID 272631839 and GID 216173056991691039.

Prospective plan and matrix are recorded in
`result/native_three_rotation_20261024_01_audit/prospective_plan.json`:
4096 events, seeds 2026102402/03/04 with unchanged broad beam recipes and
paired opposite vectors. Signs share rays within a seed and are not independent.
These seeds reuse prior-study ray prefixes; independence is across the three
seeds within this study, not from all historical studies. The initial fit gates
are rank 3, diagonal-scaled condition<100, all marginal sigma<0.5 mrad,
including independently marginalized six-column diagnostic rotations; each
error<5 nominal sigma, joint squared Mahalanobis error<25, orientation distance
below both the original vector norm and 5*sqrt(max eigenvalue of initial
covariance), and each remaining update<one quarter its initial sigma.
The original actual-surface derivative tolerance2e-5 mm/rad and all existing
scientific assertions are retained. No steering/errors are rescaled.

### Information and mathematical rank

A read-only calculation from previous actual 4096-track native states, performed
before enabling the new fit, found selected rank 3, normalized condition 1.062803,
conditional sigma=(0.0194247,0.4443931,0.3866550) mrad and correlation

```
[ 1,          0.0266260,  0.0002066 ]
[ 0.0266260,  1,         -0.0147529 ]
[ 0.0002066, -0.0147529,  1         ]
```

Full six-column diagnostic sigmas were approximately
(0.0194279,0.4612499,0.3951432) mrad for Rx/Ry/Rz, with normalized condition 1.7415.
This diagnostic does not enable free translations. Original calibrated rows
are whitened and QR-profiled over exactly four local parameters. Local rank 4
remains mandatory. The explicit coupled caller permits partial per-track
global rank; the summed selected design must be full rank. No pseudo-data or
tight survey priors supply missing information. Track-prefix, slope/impact
splits and pixel-response bounds remain diagnostic outputs. Repeated copies
of the same rank-deficient track cannot create a missing global direction.

### Changed responsibilities and reproduction commands

Exactly ten maintained files are changed or added:

| File | Responsibility |
|---|---|
| `localDetEICrecon/experimental/telescope/alignment/TelescopeMille.cc` | Additional exact three-label whitelist |
| `validation/telescope_closure/rotation.py` | Bounded full-vector routing, matrix serialization and real Geometry gates |
| `validation/telescope_closure/closure.py` | Mode selection, provenance and before-Pede observability guards |
| `validation/telescope_closure/observability.py` | Selected three-rotation information/rank diagnostics |
| `validation/telescope_closure/cohort_summary.py` | Three-component covariance, marginal statistics and ROOT plots |
| `validation/telescope_alignment/l1_global_rx_ry_rz.json` | New exact L1 parameter scope |
| `validation/test_native_rotation_scope.py` | Five additional matrix, refusal and rank tests |
| `docs/TELESCOPE_ALIGNMENT_LEGACY_PARITY.md` | Scientific report, evidence, limits and commands |
| `docs/TELESCOPE_ALIGNMENT_CODE_MAP.md` | Current source flow and supported scopes |
| `docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md` | Scope-specific operation and gate descriptions |


- `rotation.py::is_three/axis/injected_rotation/injected_vector/labels/config_name`
  provide the exact three-axis scope and vector provenance.
- `rotate_component/rotate_coupled_component/component_matrix` reuse target-first
  SO(3) serialization, with an explicit full-vector entry and unchanged old
  two-axis/single-axis refusal boundaries.
- `pose_checks/coupled_pose_gate/coupled_physical_derivatives` verify actual
  poses, three-column physical perturbations and inverse/noncommuting chains.
- `correct/check` compose all selected Pede increments simultaneously and
  score individual, joint-covariance and full orientation errors separately.
- `closure.py::geometry_step/solve/main` route the new modes and enforce
  actual selected/nuisance sensitivity before Pede.
- `TelescopeMille.cc::Init` adds only the exact three-label set; native numerical
  derivatives and transport remain untouched.
- `observability.py::analyze` adds selected three-column prefix matrices and
  per-track rank counts; six-column omitted-translation diagnostics stay read-only.
- `cohort_summary.py::read_run/main` retains joint covariance and separates
  marginal plots without treating axes/signs as independent seed cohorts.
- `l1_global_rx_ry_rz.json` declares labels, units, center pivot, composition and
  fixed references. Five new unit tests cover matrix chains, one-axis probes,
  atomic refusals, old-scope protection and accumulated rank 3.
- The Code Map and User Guide link to this bounded scientific scope.

Run in the repository root with unused output names. Command/exit/log records
are retained by every stage; directories are never reused or overwritten.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_three_rotation_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_three_rotation_20261024_01 -j2

for seed in 2 3 4; do
  beam=validation/telescope_alignment/tilt_beam_seed${seed}.json
  if [[ $seed == 2 ]]; then beam=validation/telescope_alignment/tilt_beam_validation.json; fi
  for mode in l1_rx_ry_rz l1_rx_ry_rz_negative; do
    bash environment/run.sh python3 validation/telescope_closure/closure.py \
      --build build/native_three_rotation_20261024_01 \
      --result result/native_three_rotation_seed${seed}_${mode}_20261024_01 \
      --events 4096 --beam "$beam" --chi2-cut 1000 --mode "$mode" --step all
  done
done
# Independent manual steps, in order, in a NEW result directory:
# geometry data coupled_pose nominal solve correct corrected postsolve control controlsolve check
# Replace --step all by a single stage name each time, retaining identical arguments.
# solve performs the real nominal DD4hep finite differences before Pede;
# postsolve performs the independent corrected-pose finite differences.
# Coupled pose checks are also automatically required by the first derivative gate.

for mode in l1_l2_y l1_rx l1_rx_negative l1_y_rx_l2_y l1_ry l1_ry_negative l1_rz_negative l1_rz l1_ry_rz l1_ry_rz_negative; do
  extra=(--events 32)
  if [[ $mode == l1_ry || $mode == l1_ry_negative || $mode == l1_rz || $mode == l1_rz_negative ]]; then
    extra=(--events 1024 --beam validation/telescope_alignment/tilt_beam_validation.json)
  elif [[ $mode == l1_ry_rz || $mode == l1_ry_rz_negative ]]; then
    extra=(--events 4096 --beam validation/telescope_alignment/tilt_beam_validation.json)
  fi
  bash environment/run.sh python3 validation/telescope_closure/closure.py \
    --build build/native_three_rotation_20261024_01 \
    --result result/native_three_rotation_regression_${mode}_20261024_01 \
    --chi2-cut 1000 --mode "$mode" --step all "${extra[@]}"
done
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_three_rotation_20261024_01 \
  --result result/native_three_rotation_regression_l1_l2_y_20261024_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name three_axis_final
bash environment/run.sh python3 -m unittest discover -s validation -p 'test_*.py'
bash environment/run.sh python3 validation/check_safety.py
python3 validation/verify_preservation.py
python3 validation/telescope_factories/upstream_diff.py \
  --source /Users/tkumaoka/eic/EICrecon \
  --output result/native_three_rotation_20261024_01_audit/upstream_diffs
```

The external checkout is read only. It is available on the host, not under
`/EICrecon` in this container. The initial container-side patch reproduction
failed for that path and is retained under `audit/upstream_reproduction/`;
the host invocation succeeded, reproducing all nine patches byte-for-byte.
This was an environment/path failure, not a Geometry or fit result.

For the new positive pilot's actual nominal design, the selected uncertainties
in mrad versus track count are:

| Tracks | Rx | Ry | Rz | Diagonal-scaled condition |
|---:|---:|---:|---:|---:|
| 16 | 0.34498 | 8.80260 | 7.30122 | 3.90536 |
| 64 | 0.15800 | 3.66835 | 3.15684 | 1.41958 |
| 256 | 0.07691 | 1.68501 | 1.61209 | 1.20260 |
| 1024 | 0.03948 | 0.91215 | 0.79977 | 1.03518 |
| 2048 | 0.02757 | 0.63859 | 0.54591 | 1.04700 |
| 4096 | 0.01942 | 0.44438 | 0.38666 | 1.06285 |

Rank is three for every accumulated prefix, but full rank alone is insufficient:
the smaller samples would fail the declared0.5 mrad sensitivity threshold.
Using the diagnostic rank cutoff1e-9 times the full per-track information norm,
4092 tracks have selected rank 2 and four have numerical rank 1; no track is
required to constrain all three rotations alone. The matrix raw condition is
about 524, reflecting different angular sensitivities; the normalized condition
is 1.063. Local track rank 4 is never relaxed.

The median slope magnitude is 0.06256. Equal2048-track lower/upper-slope halves
have five-column nuisance-marginalized Ry/Rz errors approximately
(1.0011,0.8352)/(0.5263,0.4529) mrad. The lower/upper-impact halves, split at
8.9001 mm, give approximately(0.9650,0.9053)/(0.5467,0.4523) mrad. Wider slopes
and larger impacts provide appreciably more tilt information; these splits are
diagnostics, not cohort selection or changes to the beam.

The retained five-column worst-case independent-pixel response bound for
Rx/Ry/Rz is approximately(4.316,91.293,77.749) mrad. It is an adversarial
absolute-error bound, not a standard deviation, and is much larger than the
formal stochastic errors. Actual quantized channels are used throughout,
with original calibrated covariance near1e-4 mm2 per coordinate; neither pitch
nor errors are adjusted. This bound and the small exploratory seed count do
not establish nominal uncertainty coverage.

### First complete three-axis result

The positive pilot accepted all 4096 tracks before and after correction. The
initial Pede result was(1.8029,1.8739,-2.2391) mrad with nominal sigmas
(0.01942436,0.44438430,0.38665617) mrad. The initial covariance, in mrad², is

```
[0.000377305699029, 0.000229695825417, 1.64522030862e-06]
[0.000229695825417, 0.197477404924, -0.00254706773857]
[1.64522030862e-06, -0.00254706773857, 0.149502990253]
```

The complete information and correlation matrices are in
`result/native_three_rotation_seed2_l1_rx_ry_rz_20261024_01/solve/independent.json`.
The joint squared Mahalanobis error is 2.447454. Actual corrected-to-Truth
orientation distance is 0.678291 mrad, versus the injected 3.967367 mrad;
all sensor centers are unchanged. Initial and corrected actual-surface
derivative maxima are 2.647e-8 and 2.648e-8 mm/rad, below the unchanged 2e-5
threshold. Each gate checks 36864 two-coordinate vectors, at three step sizes
(1e-4,1e-5,1e-6 rad) for all three axes.

ACTS chi2/stored-NDF is 0.812356724 ->0.601112072; the nominal control is
0.598045214. Stored NDF is 10 per track, not the statistical fitted-track NDF.
Pede initial/post/control chi2/NDF are 1.001984599/1.001961623/0.996773735
with 24573 NDF each. All statuses are 0, rejected local fits zero, and no
error rescaling is recommended or applied. Post updates are
(0.37112,36.952,-25.484) urad, evaluated separately from the finite-sample
Truth error. They are not combined with initial errors as independent fits.

The real forward/nonparallel/inverse chain returns to the original matrix
exactly at serialized precision. The declared one-vector Truth differs from
`Rx(1.8 mrad) Ry(2.5 mrad) Rz(-2.5 mrad)` by 4.461202 urad. The pilot actual
Truth matrices equal the pre-Pede real forward-pose fixture exactly
(`audit/pilot_truth_preflight_identity.json`). Later cases directly enforce
their own actual Truth preflight before the pose chain and Pede.

### Capability boundary and remaining legacy/native gaps

| Capability | Native status / retained legacy capability |
|---|---|
| Two Global Y translations; signed L1 Rx/Ry/Rz; Y/Rx plus L2 Y | Preserved existing native scopes; original scientific baselines retained |
| Coupled L1 Ry/Rz | Previous two-parameter scope retained with its stricter Rx restriction |
| L1 Rx/Ry/Rz rotation-vector fit | Implemented three-label scope, actual derivative and complete corrected-Geometry reconstruction validation; bounded physical fixtures only |
| Full physical SO(3) matrix composition | All current cross-axis terms retained; actual forward/nonparallel/inverse tests and center/ID/envelope checks |
| Original fixed-ordered Rx/Ry failure | **Not independently resolved or rerun here**. A free three-component rotation vector is a different model; its success does not repair or relabel the old two-coordinate failure |
| L1 translations plus full rotation / arbitrary six-DOF | Unsupported native fit; full-six-column information is diagnostic only |
| Other aligned sensors / multi-layer rotations | Unsupported native scope; reference poses fixed |
| Arbitrary Survey Geometry | Unsupported; fixed telescope mounting, small current-pose bounds and explicit singular-chart refusals |
| Controller iteration, convergence/recovery and version chains | Legacy implementation retained; not migrated into the native closure driver |
| Original Geant4/RawHit input | Legacy retained; radial synthetic channels are not a silent reinterpretation of old endcap data |
| Nonzero field / assigned ACTS material / six local parameters | Outside this guarded zero-field, material-free, four-local-parameter model |
| Bias / nominal uncertainty coverage | Not validated by this small exploratory cohort; no 800-seed campaign launched |

This restores another bounded portion of the legacy SO(3) capability without
claiming complete legacy/native parity. A small remaining Pede update is a
same-data self-consistency diagnostic, not evidence of exact Truth recovery.
The initial joint Mahalanobis calculation uses the initial rotation-vector
coordinates and initial covariance about the same nominal base; the full
matrix distance is evaluated independently. No successive-fit covariance sum
is interpreted as independent information. No legacy scientific code, historical
outputs, installed library or production Geometry is changed or removed.

The next steps remain separately gated translation-plus-rotation and multi-layer
studies, then Controller and original Geant4 migration. They were not enabled
as part of this milestone.

### Warnings and unsuccessful technical invocations

Two audit commands initially failed, with their outputs retained:

1. `audit/upstream_reproduction/`: exit1, the host EICrecon checkout was not
   mounted at the attempted container path. Host-side patch reproduction and
   nine-file byte-identity checks succeeded without modifying that checkout.
2. `audit/official_binary_inspection/`: exit127, missing `libMille2.so` search
   environment in the standalone decoder invocation. The retry uses the same
   `environment(build)` as the workflow and passed in
   `audit/official_binary_inspection_02/`, decoding 4096 records and 40960 scalar
   measurements with all three selected labels present. Input files and Pede
   steering were not changed.

The complete unit suite also emitted SQLite unclosed-connection ResourceWarnings
from existing test lifetimes; all 62 tests passed and the warnings remain in
`three_axis_final_regressions/unit_tests/stdout.log`. Fixed-container login
`stty` messages and CMake developer warnings are likewise retained. These are
separate from the scientific Pede status/rejection diagnostics. No warning
was suppressed and no uncertainty or physics assertion was weakened.

### Complete independent-cohort results

All six prospectively specified fixtures passed on their first scientific
attempt: three independent seeds, with the opposite vectors sharing rays within
each seed. Each reconstruction pass accepts 4096 tracks, five measurements,
zero outliers and two holes. There were no failed, sensitivity-refused or
non-convergent scientific cases in this six-fixture cohort. The technical audit
command failures above are not extra samples.

Vectors below are ordered (Rx,Ry,Rz). Sigmas and Pulls refer only to the initial
Pede solve; signs denote +w or -w, not three independently chosen signs.

| Seed | Vector | Initial fit [mrad] | Initial sigma [mrad] | Initial Pulls | Joint error squared | Pose error [mrad] |
|---:|:---:|---|---|---|---:|---:|
| 2026102402 | +w | (1.8029, 1.8739, -2.2391) | (0.0194244, 0.444384, 0.386656) | (0.149297, -1.40892, 0.67476) | 2.447454 | 0.678291 |
| 2026102402 | -w | (-1.7842, -2.6573, 2.8865) | (0.0194246, 0.444382, 0.386644) | (0.813402, -0.353975, 0.999628) | 1.790917 | 0.417582 |
| 2026102403 | +w | (1.81, 1.6282, -2.8157) | (0.0193338, 0.44366, 0.381496) | (0.517229, -1.96502, -0.827531) | 4.809842 | 0.927254 |
| 2026102403 | -w | (-1.8225, -2.4532, 2.5729) | (0.0193338, 0.443646, 0.381478) | (-1.16376, 0.10549, 0.191099) | 1.391577 | 0.089504 |
| 2026102404 | +w | (1.8014, 1.8381, -3.0932) | (0.0194027, 0.453026, 0.381663) | (0.072155, -1.46106, -1.55425) | 4.562079 | 0.888819 |
| 2026102404 | -w | (-1.8057, -1.9351, 2.0654) | (0.0194029, 0.453024, 0.381659) | (-0.29377, 1.24695, -1.13871) | 2.958153 | 0.712756 |

The full initial 3x3 covariance (rad²) and correlation matrices for **every**
case are retained in `audit/cohort_summary/output/report.json`, under `runs`,
and independently in each case
`solve/independent.json` / `validation/report.json`. They are not replaced
by diagonal-only errors. The positive-pilot matrix is printed above.

| Seed | Vector | Correlation(Rx,Ry; Rx,Rz; Ry,Rz) | Remaining update [urad] | ACTS chi2/stored-NDF before -> after |
|---:|:---:|---|---|---|
| 2026102402 | +w | (0.0266102, 0.000219055, -0.0148237) | (0.37112, 36.952, -25.484) | 0.812356724 -> 0.601112072 |
| 2026102402 | -w | (0.0265589, 0.000204626, -0.0146767) | (0.5693, -16.818, -13.378) | 0.809954595 -> 0.602310727 |
| 2026102403 | +w | (0.00783806, -0.0309361, -0.00199485) | (0.39953, 4.6833, -5.7952) | 0.817483394 -> 0.602791965 |
| 2026102403 | -w | (0.00777319, -0.0309948, -0.00180185) | (0.43046, -20.13, 10.047) | 0.821469318 -> 0.603580658 |
| 2026102404 | +w | (0.0188798, -0.0111271, -0.00107236) | (0.45611, -19.165, 16.12) | 0.811214184 -> 0.599420619 |
| 2026102404 | -w | (0.0188124, -0.0110799, -0.000788764) | (0.38223, 18.93, -36.077) | 0.810804396 -> 0.598752370 |

| Seed | Vector | Local residual RMS(u,v) before [um] | After [um] | Pede chi2/NDF(initial; post; control) |
|---:|:---:|---|---|---|
| 2026102402 | +w | (8.88632, 9.13793) | (7.77248, 7.73364) | (1.00198, 1.00196, 0.996774) |
| 2026102402 | -w | (8.85263, 9.14435) | (7.77848, 7.7431) | (1.00396, 1.00396, 0.996774) |
| 2026102403 | +w | (8.90345, 9.17728) | (7.7901, 7.73763) | (1.00477, 1.00476, 1.00042) |
| 2026102403 | -w | (8.82944, 9.2915) | (7.77634, 7.76163) | (1.0061, 1.00608, 1.00042) |
| 2026102404 | +w | (8.78219, 9.22568) | (7.74778, 7.73656) | (0.999126, 0.999143, 0.999844) |
| 2026102404 | -w | (8.84203, 9.16387) | (7.74808, 7.72761) | (0.998007, 0.998029, 0.999844) |

All 18 Pede fits have status 0, zero rejected local fits and 24573 NDF. No
error rescaling is applied. The complete chi2 numerators, warning flags,
per-iteration rejection counts and original-covariance comparisons remain in
each `validation/report.json`. Sensor center differences remain exactly zero
in every case; VolumeID/GID and XML whitelist checks pass.

Marginal exploratory statistics (three independent seeds per row) are:

| Vector/axis | N | Mean fit-minus-Truth [mrad] | Sample SD [mrad] | Mean nominal sigma [mrad] | Pull mean | Pull sample SD |
|---|---:|---:|---:|---:|---:|---:|
| +w / Rx | 3 | 0.004767 | 0.004594 | 0.019387 | 0.246227 | 0.237843 |
| +w / Ry | 3 | -0.719933 | 0.132733 | 0.447023 | -1.611666 | 0.307121 |
| +w / Rz | 3 | -0.216000 | 0.435691 | 0.383272 | -0.569007 | 1.136770 |
| -w / Rx | 3 | -0.004133 | 0.019198 | 0.019387 | -0.214710 | 0.990951 |
| -w / Ry | 3 | 0.151467 | 0.372303 | 0.447017 | 0.332823 | 0.824321 |
| -w / Rz | 3 | 0.008267 | 0.414348 | 0.383261 | 0.017338 | 1.079707 |

The machine-readable summary stores Truth-minus-fit with the opposite sign
to the mean-error column above. Pull uses (fit-Truth)/initial nominal sigma.
Each marginal sample SD has only two degrees of freedom; paired signs and
axes cannot be pooled into 18 independent experiments. This is not evidence
of calibrated nominal coverage or unbiased estimation. Observed offsets/scatter
are reported without tuning amplitudes, covariances or steering. Prefix designs
share tracks and likewise do not constitute independent repeated experiments.

ROOT output `audit/cohort_summary/output/cohorts.root` contains six estimate
graphs with nominal errors and six Pull histograms. Each case also retains
`validation/rotation.root` with nine ACTS chi2/local-residual histograms and
batch read-back validation. Open these with ROOT/TBrowser; a GUI session is
not part of the batch-test claim.

A diagnostic concern deserves explicit follow-up: **positive-vector Ry is low
in all three seeds**, with mean fit-minus-Truth -0.719933 mrad, sample SD
0.132733 mrad, mean nominal sigma 0.447023 mrad and Pull mean/SD
-1.611666/0.307121. Every individual error and joint error meets the declared
gates, but passing these gates does not explain that coherent direction.
There are no rejected tracks, solver warnings, non-convergence or differing
accepted counts that explain it. Three seeds and correlated axis/sign comparisons
are insufficient to establish a systematic bias or a calibrated error model;
this observation should neither be hidden nor presented as proof of unbiasedness.
A separately planned bias/discretization/linearization study would be informative
before uncertainty-performance claims. None was launched here, and no settings
were tuned in response. Full Geometry and derivative validation is stronger
than the statistical claims supported by this small ensemble.

### Consolidated regression and preservation evidence

- Fresh native build: `build/native_three_rotation_20261024_01`.
- Fresh unchanged legacy build: `build/native_three_rotation_legacy_20261024_01`.
- Fresh standalone Geometry/CKF builds are suffixed
  `_three_axis_final_regressions_geometry` and `_benchmark`.
- All eight existing modes and both existing coupled Ry/Rz signs passed in
  `result/native_three_rotation_regression_{mode}_20261024_01/`.
  All 60 nominal/Truth/corrected XML and nominal/corrected/control Mille artifacts
  are byte-identical to their preceding baselines. Input channel payloads are
  identical. Every scientific validation-report field also matches exactly;
  only the newly generated ROOT container's file checksum is excluded from that
  report comparison, with immutable payload checks performed independently.
  Evidence: `audit/baseline_identity.json` and `scientific_report_identity.json`.
- The old six-case coupled-cohort summary replay preserves every previous
  marginal statistic exactly (`audit/previous_coupled_summary_replay/`).
- Native/legacy writer equivalence uses the established mathematical/reference
  fixture; it is not a claim of original-endcap/radial three-axis input parity.
- Complete 18-command suite passed in
  `result/native_three_rotation_regression_l1_l2_y_20261024_01/three_axis_final_regressions/`,
  including all 57 existing tests plus five new tests, standalone Geometry/CKF,
  native/legacy writer mathematics, official Pede, safety and preservation.
- Historical 99-track reference passed after the fresh legacy build in
  `result/native_three_rotation_legacy_20261024_01/`: correction +198.75 um,
  L2 residual -199.5713755 -> -0.8213645 um,
  ACTS chi2/stored-NDF 45.59223485 ->1.981039768.
- Native 32-track Y baseline remains +149.14/+203.18 um and
  ACTS 37.16731567382813 ->0.6908491410315036.
- All nine upstream patches reproduce byte-for-byte; 221 baseline records and
  2046 relocated files are unchanged, with the electron diff preserved.
- `audit/final_validation.json` confirms immutable stage checksums for all six
  cases, all 18 normal Pede fits, paired ray identity, 62 tests and prior baselines.
  Maintained source/configuration hashes are in `final_source_snapshot.json`.
  Numerical NativeMilleModel hash remains
  `1622cc80327fe08dd6c943bb57e537a8fea86a95233389065efa91739028843f`.

Additional exact commands (use new output names for any repeat):

```bash
bash environment/run.sh env \
  TESTBENCH_BUILD_DIR=/work/build/native_three_rotation_legacy_20261024_01 \
  bash environment/build.sh
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/native_three_rotation_legacy_20261024_01 \
  /work/build/native_three_rotation_legacy_20261024_01

runs=()
for seed in 2 3 4; do
  for mode in l1_rx_ry_rz l1_rx_ry_rz_negative; do
    runs+=("result/native_three_rotation_seed${seed}_${mode}_20261024_01")
  done
done
bash environment/run.sh python3 validation/telescope_closure/cohort_summary.py \
  --runs "${runs[@]}" \
  --output-dir result/native_three_rotation_20261024_01_audit/cohort_summary/output
# Full actual decoder argv is in audit/official_binary_inspection_02/command.json;
# use the workflow environment(build) to resolve external/install/lib/libMille2.so.
bash environment/run.sh python3 -c 'import subprocess; from pathlib import Path; from validation.telescope_closure.closure import environment; subprocess.run(["/work/external/install/bin/inspectMilleBinary", "/work/result/native_three_rotation_seed2_l1_rx_ry_rz_20261024_01/nominal/mille.dat"], env=environment(Path("/work/build/native_three_rotation_20261024_01")), check=True)'
```

Here `audit/` abbreviates `result/native_three_rotation_20261024_01_audit/`.
All six original driver commands, subprocess stdout, exit codes, Geometry XML,
Mille/Pede files, failed technical invocations and ROOT outputs remain locally
preserved. Generated artifacts remain ignored; the local commit contains only
maintained source, configuration, tests and documentation. No push, merge,
production activation, external installation modification or legacy deletion
is performed.

## Targeted Ry diagnostic before the L1 Y/rotation extension

Starting branch `feature/upstream-acts-geometry`, clean at
`b37d9e3ce44af3553cdd3957de05e80f2eb68185`. This phase adds a read-only
analysis, not a numerical model correction or an additional alignment solver.
No existing fit, covariance, selection, Geometry or result is changed.

### Frozen-design attribution

`validation/telescope_closure/bias.py` reads the six existing three-rotation
fixtures and verifies immutable input/reconstruction/solver/derivative stages.
For each actual native reference and original whitening W, it profiles the
same four local columns A using P=I-QQ^T. With selected whitened rotation
columns G and H=sum(G^T P G), the original estimate is decomposed as:

```
r = pixel + exact_finite_geometry + true_ray_minus_native_reference
error = H^-1 sum G^T P [W pixel
                       + (W exact_finite_geometry - G injected_vector)
                       + W reference_difference]
```

Truth is used solely for this offline attribution: the true physical ray is
intersected with the actual nominal sensor, and the unquantized local hit is
computed from the actual displaced DD4hep local coordinates. No Truth is sent
to reconstruction, Mille, Pede or a correction file. The middle term includes
finite-pose and native-design linearization effects. The last term tests the
reference-state/local-profile contribution. Their sum agrees to2e-11 rad; the
full diagnostic estimate agrees with the existing unrounded Schur solution
to1e-10 rad. These are analytical checks on the existing official Pede result.

| Seed | Vector | Ry error [mrad] | Pixel contribution [mrad] | Finite-pose/design remainder [mrad] |
|---:|:---:|---:|---:|---:|
| 2026102402 | +w | -0.626145714 | -0.627575963 | 0.001430249 |
| 2026102402 | -w | -0.157313215 | -0.159078833 | 0.001765617 |
| 2026102403 | +w | -0.871776424 | -0.871450373 | -0.000326051 |
| 2026102403 | -w | 0.046766279 | 0.047306430 | -0.000540151 |
| 2026102404 | +w | -0.661892655 | -0.664340290 | 0.002447635 |
| 2026102404 | -w | 0.564910975 | 0.562746293 | 0.002164682 |

Reference contributions are numerical zero (below1e-10 mrad). In particular,
the positive Ry deficit is explained sample by sample by the realized pixel
rounding scores, not by a missing finite SO(3) term or an observed derivative
defect. Existing nominal/corrected real-surface finite differences remain
consistent; the existing post-correction updates are much smaller than the
initial Ry Truth errors. This does **not** show whether the population mean
of the quantized estimator is zero. Three seeds do not establish unbiasedness
or nominal coverage, and no errors or steering are rescaled.

### Phase, slope, impact and prefix diagnostics

The output contains all five layers: actual pixel phases,10-bin phase
histograms, mean/RMS rounding errors, residual correlations with slope and
impact, equal-count slope/impact/phase splits and prefix estimates. Phase
histograms are broadly populated; an unweighted nearly uniform phase histogram
does not force the covariance-weighted alignment score to zero. For positive
seed2026102402, the Ry prefix errors at64/256/1024/2048/4096 tracks are
-0.140/+1.372/+0.396/-0.523/-0.626 mrad. The largest-prefix deficit is not
present at every earlier prefix. The three seeds use independent RNG streams;
reusing their deterministic prefixes in earlier studies does not create new
independent evidence. Prefixes within one stream remain correlated.

For that case, lower/upper slope halves give Ry errors -1.335/-0.450 mrad;
lower/upper impact halves give -1.337/-0.428 mrad. Conditioning on the L1
sensor-X phase half gives about+5.357/-6.529 mrad: these subsets deliberately
select one-sided rounding errors and are not unbiased validation cohorts.
All hits are retained in the full fit. The opposite-vector cases have different
rounding phases despite sharing rays, explaining why signs cannot be treated
as independent repetitions or expected to cancel event by event.

No demonstrated numerical or Geometry defect was identified. The exact
attribution supports a finite-sample pixel-realization explanation for the
observed offsets, while leaving possible population/discretization bias
unresolved. A separate preregistered coverage/bias study remains necessary
for stronger statistical claims. No800-seed campaign or new three-axis-only
simulation was launched here. New four-parameter robustness samples will use
fresh declared seeds and will not be presented as a direct coverage test of
the earlier three-axis scope.

### Evidence, tests and geometry-only preflight

- `result/native_y_rotations_20261024_01_audit/guarded_bias_diagnostic/report.json`
  contains all six decompositions, subset and prefix statistics, input hashes
  and actual finite-difference diagnostics. The guarded replay exactly matches
  the initial read-only report.
- Three independent tests in `validation/test_native_bias_diagnostics.py`
  check invariance to local offsets, equality with joint least squares and
  refusal of local rank defects. All65 tests pass in `audit/diagnostic_tests/`.
- Actual preflight with Y=+0.150 mm and both previous rotation vectors passes
  in `audit/geometry_preflight_02/`. The positive-vector sensitive half extents
  are(0.274999,50.089981,50.089669) mm; adding the Y shift leaves about10.019 um
  in the module-Y half-envelope. All eight corners, cylindrical layer bounds,
  centers, rotations, IDs and actual DD4hep/ACTS agreement pass. Envelopes,
  materials and pitch are unchanged. No smaller displacement is required.
- The initial geometry preflight failed before conversion because a relative
  XML path was interpreted from the per-stage directory. Its failure is kept
  under `audit/geometry_preflight/`; the absolute-path retry is separate.

The maintained additions are the read-only `bias.py`, its independent tests
and this report. They are committed separately from four-parameter feature
changes. `audit/` here abbreviates
`result/native_y_rotations_20261024_01_audit/`.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
runs=()
for seed in 2 3 4; do
  for mode in l1_rx_ry_rz l1_rx_ry_rz_negative; do
    runs+=("result/native_three_rotation_seed${seed}_${mode}_20261024_01")
  done
done
bash environment/run.sh python3 validation/telescope_closure/bias.py \
  --runs "${runs[@]}" --output result/NEW_DIAGNOSTIC/ry_attribution.json
bash environment/run.sh python3 -m unittest discover -s validation -p "test_*.py"
```

## L1 Global Y plus three-axis native SO(3) milestone

**Checkpoint status: experimental, five of six complete closures.** The final
negative-vector seed 2026102502 is stopped by the unchanged physical module-box
containment gate. The requested all-fixture validation is not complete, so the
four-parameter implementation is not promoted or committed as validated. The
separate read-only diagnostic commit remains valid.

Audit root: `result/native_y_rotations_20261024_01_audit/` (abbreviated
`audit/` in this section). Result and build products are local, excluded from Git.

The feature follows the separate read-only Ry diagnostic commit. It enables
exactly L1 Global Y (700102, mm) and Global Rx/Ry/Rz (700104/700105/700106, rad).
L1 X/Z and all other sensor poses remain fixed. The physical contract is

```
c_new = c_current + (0, dY, 0)
R_new = Exp([dRx,dRy,dRz]) R_current
```

These are world coordinates and active left-Global rotations about the actual
current sensitive center. The center is not rotated about the world origin,
and no independent Euler increments are added. Full target matrices are
serialized with the existing bounded constructor-compatible SO(3) charts.
Parent mounting, detector flags, envelope, material, pitch and segmentation
are unchanged. No provider, navigator, fitter or inference solver is added.
NativeMilleModel, ACTS transport/alignment columns, covariance whitening,
electron seed/hypothesis and CKF selection are unchanged.

### Geometry feasibility, scope and prospective gates

Actual geometry-only preflight `audit/geometry_preflight_02/` validates the
previous +150 um displacement with both rotation vectors. All eight sensitive
corners fit the unchanged module box and cylindrical layer envelopes, and
DD4hep/ACTS centers, matrices, VolumeID and GeometryIdentifier agree. The
minimum module-Y margin is approximately 10 um, so the displacement is not
reduced. This decision precedes four-parameter Pede recovery.

The fixed fixtures are `(Y,Rx,Ry,Rz)=(+0.150 mm,+1.8,+2.5,-2.5 mrad)` and
`(+0.150 mm,-1.8,-2.5,+2.5 mrad)`. Only the rotation vector changes sign.
4096 rays per fixture use fresh independent seeds 2026102501/02/03, declared
in `validation/telescope_alignment/y_rotation_beam_seed{1,2,3}.json` with the
same bounded uniform beam distribution. Paired signs share rays within each
seed and are not independent repetitions.

`audit/prospective_plan.json` fixes the gates before the first fit: accumulated
selected rank 4; diagonal-scaled condition<100 for the selected and omitted-X/Z
six-column diagnostic; marginal Y sigma<1 um and angular sigmas<0.5 mrad,
including the six-column diagnostic; each recovery error<5 initial nominal
sigmas and full-four-coordinate squared Mahalanobis error<25. Actual center
error must be below both 150 um and five Y sigmas; actual orientation error
must be below both the injected rotation norm and five times the square root
of the largest eigenvalue of the **angular covariance sub-block**. Mixed
mm/rad eigenvalues are never used for an angular tolerance. Remaining Y must
be below 2e-5 mm and rotations below one quarter their initial sigma. Existing
scientific gates remain unchanged for all previous modes.

A prospective calculation from previous actual native rows gives selected
rank 4, normalized condition 1.5190, Y sigma 0.19083 um, and Rx/Ry/Rz sigmas
(0.019424,0.444386,0.395084) mrad. The largest translation/rotation correlation
is approximately-0.20544 for Y/Rz. This is an initial feasibility check, not the
new fit; the actual new native states are rechecked before Pede. Original
four-local-parameter rank 4 is mandatory for every track. Individual tracks
need not have full global rank; the summed selected matrix must.

### Source responsibilities and mixed-unit diagnostics

- `localDetEICrecon/experimental/telescope/alignment/TelescopeMille.cc::Init`
  admits one additional exact label set; original physical columns 1/3/4/5
  and numerical equation construction remain unchanged.
- `validation/telescope_alignment/l1_global_y_rx_ry_rz.json` records the exact
  units, center pivot, update contract and fixed references.
- `rotation.py::is_four/rotation_labels/fixture_shifts` separate translation
  from the three-component rotation vector; old routes remain explicit.
- `correct/check` apply the center and matrix updates, score full mixed-unit
  covariance, and use its angular sub-block for orientation bounds.
- `coupled_pose_gate` checks nonparallel translation/rotation composition and
  inverse-center recovery using actual reloaded DD4hep/ACTS poses.
- `coupled_physical_derivatives` checks Y at 1e-3/1e-4/1e-5 mm and rotations
  at 1e-4/1e-5/1e-6 rad around nominal and corrected poses. The small Y steps
  respect the unchanged tight box margin. The original 2e-5 absolute derivative
  tolerance is retained, with mm/mm and mm/rad errors reported separately.
- `closure.py::geometry_step/solve/main` records the new fixture and enforces
  selected-four and diagnostic-six sensitivity before Pede.
- `observability.py::analyze` adds four-coordinate prefix matrices, covariance,
  correlations and per-track ranks while retaining all existing diagnostics.
- `cohort_summary.py` keeps full mixed-unit covariance, labels and units, and
  draws Y estimates in um and angular estimates in mrad. Existing rotational
  summaries retain their original field semantics.
- `validation/test_native_y_rotations.py` independently checks center-preserving
  composition/inversion, three-versus-four parameter routing and exact units.

All full-four covariance entries have explicit parameter units: mm2 for Y/Y,
mm*rad for Y/angle, and rad2 for angle/angle. The feature uses
`nominal_covariance_mixed_units`, retaining the old `nominal_covariance_rad2`
key only for rotation-only scopes. The first development run was started before
this diagnostic-key correction; it is preserved separately and not counted as
an independent cohort. The identical-seed retry uses fresh outputs and unchanged
physics, amplitudes and engineering gates. This is an output-label correction,
not a numerical-model correction.

### Explicit one-time relinearization amendment

The first positive four-parameter fit did **not** pass the original one-step
closure gate: its post-correction Ry update was -117.32 urad, or 0.26054 of the
initial 450.2924 urad nominal sigma. The predeclared quarter-sigma bound was
112.5731 urad. This failure is retained; the bound is not relaxed. Initial Y,
Rx and Rz post-updates were +6.1337 nm, +0.99082 urad and -17.827 urad.

The user explicitly authorized at most one additional correction. The amendment
is recorded prospectively in `audit/prospective_refinement_plan.json`, before
executing it. The declared protocol for every four-parameter cohort is the same:
initial fit/correction, same-channel reconstruction/Pede, **one** simultaneous
Y/SO(3) update, and a fresh reconstruction/Pede evaluation using the original
thresholds. A Geometry failure stops the case before further reconstruction;
five cases complete the protocol and one stops at its first candidate. This is
an explicit validation operation, not an automatic
Calibration Controller loop. No Geometry version is activated.

`--refine-once` is refused outside the four-parameter modes. `rotation.refine`
verifies immutable completed parents and creates an exclusive `refinement/`
stage; an existing or partial stage cannot be reused. The corrected XML is
reloaded through actual DD4hep/ACTS and checked at its current sensitive center.
`refined`, `refined_physical_derivatives` and `refinesolve` are separate stages.
Initial and final Pede diagnostics remain separate. The final pose is composed
as matrices; cumulative rotations are `Log(R_final R_nominal^T)`, never summed
Euler angles. Initial-fit uncertainties and Pulls remain initial-fit quantities;
uncertainties from fits on the same channels are not combined.

### Independent commands for the four-parameter milestone

The following commands use the fixed Docker container. Build and output paths
must be new for a repeat; the paths below identify the actual recorded run.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake \
  -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_y_rotations_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_y_rotations_20261024_01 -j2

# All stages for a new case; never reuse an existing result directory.
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_y_rotations_20261024_01 \
  --result result/my_four_parameter_positive_seed1 \
  --mode l1_y_rx_ry_rz --events 4096 \
  --beam validation/telescope_alignment/y_rotation_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all

# Alternatively, invoke each independent stage with identical arguments.
for step in geometry data nominal solve correct corrected postsolve refine refined refinesolve control controlsolve check; do
  bash environment/run.sh python3 validation/telescope_closure/closure.py \
    --build build/native_y_rotations_20261024_01 \
    --result result/my_four_parameter_stagewise_seed1 \
    --mode l1_y_rx_ry_rz --events 4096 \
    --beam validation/telescope_alignment/y_rotation_beam_seed1.json \
    --chi2-cut 1000 --refine-once --step "$step" || break
done

# Unit tests, safety and historical-data preservation are independent.
bash environment/run.sh python3 -m unittest discover -s validation -p 'test_*.py'
bash environment/run.sh python3 validation/check_safety.py
bash environment/run.sh python3 validation/verify_preservation.py

# Consolidated suite: use a completed original two-Y closure and a fresh name.
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_y_rotations_20261024_01 \
  --result result/native_y_rotations_regression_l1_l2_y_20261024_01 \
  --mode l1_l2_y --events 32 --chi2-cut 1000 \
  --step regressions --validation-name my_four_parameter_regressions

# Standalone official decoder, with the same dependency environment as tracking.
bash environment/run.sh python3 -c 'import subprocess; from pathlib import Path; from validation.telescope_closure.closure import environment; subprocess.run(["/work/external/install/bin/inspectMilleBinary", "/work/result/native_y_rotations_seed1_positive_20261024_02/nominal/mille.dat"], env=environment(Path("/work/build/native_y_rotations_20261024_01")), check=True)'
```

The existing 12 modes use the same stagewise driver without `--refine-once`:
32 events for `l1_l2_y`, `l1_rx`, `l1_rx_negative`, `l1_y_rx_l2_y`; 1024 events
for `l1_ry`, `l1_ry_negative`, `l1_rz`, `l1_rz_negative`; 4096 for
`l1_ry_rz`, `l1_ry_rz_negative`, `l1_rx_ry_rz`, `l1_rx_ry_rz_negative`.
For the last eight, add `--beam validation/telescope_alignment/tilt_beam_validation.json`.
All recorded runs use `--chi2-cut 1000`. Their exact arguments, outputs and exit
codes are preserved under each result's `driver/`. The diagnostic module has
its own `--help` and consumes only the original completed three-rotation runs;
`audit/guarded_bias_diagnostic/command.json` records all six exact inputs.

### Preserved unsuccessful invocations and warning policy

- `audit/geometry_preflight/positive/` failed because the technical probe received
  a relative XML path from its own stage directory. The absolute-path retry in
  `geometry_preflight_02/` passed before four-parameter fits. No Geometry
  envelope or physical amplitude was changed.
- `native_y_rotations_seed1_positive_20261024_01/` is a development execution
  started before the mixed-unit covariance key was corrected. It is retained,
  and its numerical fit agrees with the identical-seed fresh execution `_02`.
  It is not another independent seed. Both original one-step drivers report the
  Ry gate failure; neither result is relabeled as one-step success.
- The fresh `_02/validation/` remains an unsuccessful original check. Approved
  additional stages and `refined_validation/` preserve that separation; the
  original driver exit remains1. Its successful refinement has its own
  `refinement_driver/` commands, exit codes and immutable markers.
- `audit/refinement_refusals/` intentionally records exit 1 for an attempted
  duplicate refinement and exit 2 for an unsupported-mode CLI request. Parent
  and final-stage hashes remain intact. These are expected safety successes.
- Existing SQLite unclosed-connection ResourceWarnings, fixed-container `stty`
  messages and CMake developer warnings remain in logs. Tests are not altered
  to suppress them, and no input-error rescaling is performed.

### Representative full covariance and correlations

For seed 2026102501, positive injection, the initial four-coordinate covariance
is shown below. Row/column units are explicit; entries have the product of the
corresponding units. This is the original unscaled nominal covariance, not a
covariance for the cumulative two-correction pose.

| Coordinate | Y [mm] | Rx [rad] | Ry [rad] | Rz [rad] |
|---|---:|---:|---:|---:|
| Y [mm] | 3.679816222e-08 | 7.919222823e-12 | -1.287961812e-11 | -1.718244153e-08 |
| Rx [rad] | 7.919222823e-12 | 3.803909120e-10 | -1.426979876e-11 | -4.859617754e-11 |
| Ry [rad] | -1.287961812e-11 | -1.426979876e-11 | 2.027632445e-07 | -2.746609063e-09 |
| Rz [rad] | -1.718244153e-08 | -4.859617754e-11 | -2.746609063e-09 | 1.537336144e-07 |

Its marginal sigmas are (0.191828 um,0.019504,0.450292,0.392089 mrad).
The accumulated selected rank is 4; diagonal-scaled condition is 1.594324.
The largest cross-correlation is Y/Rz=-0.228448. The complete correlation
matrix, omitted-X/Z six-column diagnostic, prefix track-count scaling,
slope/impact subsets and per-track rank counts are in each case's
`solve/observability.json`. Every selected and omitted-axis sensitivity gate
is checked before Pede; no prior is introduced and no extra column is fitted.

### Completed historical regression evidence

All 12 original native modes passed fresh reconstruction closures using the new
native build. Every mode was then checked again with the final Python source,
writing `final_source_validation/` independently. All 72 comparison artifacts
(12 times nominal/Truth/corrected XML and nominal/corrected/control Mille Binary)
are byte-identical to the previous three-axis milestone's corresponding runs.
Scientific report JSON values are also identical after excluding only
`immutable_input_file_sha256`: regenerated ROOT container metadata changes that
whole-file checksum. Actual channel-payload checksums remain identical, and each
new ROOT input remains immutable within its own run. No numerical assertion or
reference value was weakened. Full hashes and exclusions are recorded in
`audit/all_twelve_final_baseline_identity.json`.

The final 18-command suite passed in
`result/native_y_rotations_regression_l1_l2_y_20261024_01/y_rotations_complete_regressions/`.
It uses fresh standalone Geometry and benchmark builds, actual Geometry reload
and integration checks, standalone ACTS reconstruction, one-event official-style
plugin reconstruction, original/native mathematical and official-Pede checks,
all 70 unit tests (62 original, 3 diagnostic, 5 four-parameter/safety), safety and
preservation checks. Its command/exit record is
`audit/complete_regression_driver/`. An earlier full suite also passed and is
retained separately. `audit/official_binary_inspection/` successfully decodes
4096 new native records with 40960 scalar measurements and all four labels.

`audit/historical99/` reruns the original electron reference with the unchanged
existing legacy build `build/native_three_rotation_legacy_20261024_01`; it is
not described as a new legacy compilation. It reproduces 99 tracks, +198.75 um,
L2 mean Rec-Sim -199.5713755 to -0.8213645 um and ACTS chi2/stored-NDF
45.59223485 to 1.981039768. Output is
`result/native_y_rotations_legacy_20261024_01/`. The independent command is:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash validation/run_regression.sh \
  /work/result/my_four_parameter_historical99 \
  /work/build/native_three_rotation_legacy_20261024_01
```

All nine maintained upstream patches were reproduced on the host against the
pinned read-only EICrecon checkout and are byte-identical; see
`audit/upstream_patch_identity.json`. The numerical source/Geometry/configuration
contract additionally verifies 160 files byte-identical to the starting commit,
with the exact Mille whitelist as the sole C++ exception
(`audit/protected_source_identity.json`). New beam recipes change only seeds
and descriptions. No installed library, historical result or Controller is
modified; no push, merge or Geometry activation is performed.

### Final six-case checkpoint: five closures, one physical stop

Exactly three independent beam seeds were attempted: 2026102501,2026102502 and
2026102503. Each has both signed rotation vectors, 4096 reconstructed nominal
tracks per fixture. The paired signs share identical ray cohorts. The failed
case remains in every initial-fit statistic; there is no seed replacement or
selection on closure success. Development duplicates are excluded.

Initial Pede estimates (Y in um, rotations in mrad):

| Seed | Sign | Y | Rx | Ry | Rz | Full closure |
|---|---|---:|---:|---:|---:|---|
| 2026102501 | + | 150.130000 | 1.796600 | 2.489500 | -2.404600 | pass after explicit refinement |
| 2026102501 | - | 149.990000 | -1.801700 | -2.864700 | 1.565500 | pass after explicit refinement |
| 2026102502 | + | 149.660000 | 1.800300 | 2.398800 | -1.717900 | pass after explicit refinement |
| 2026102502 | - | 150.020000 | -1.803700 | -3.042000 | 3.004300 | STOP: module containment |
| 2026102503 | + | 149.940000 | 1.779900 | 2.000700 | -3.449500 | pass after explicit refinement |
| 2026102503 | - | 149.960000 | -1.781500 | -1.930400 | 1.709200 | pass after explicit refinement |

Final cumulative **matrix-composed** corrections and actual geometry errors:

| Seed | Sign | Y [um] | Rx/Ry/Rz [mrad] | Center Y error [um] | Orientation error [mrad] | ACTS chi2/stored-NDF before -> final |
|---|---|---:|---|---:|---:|---|
| 2026102501 | + | 150.136134 | +1.797754/+2.372165/-2.422320 | +0.136134 | 0.149602 | 16.523508 -> 0.594524 |
| 2026102501 | - | 149.987070 | -1.802387/-2.787245/+1.572531 | -0.012930 | 0.970934 | 16.590451 -> 0.594702 |
| 2026102502 | + | 149.664388 | +1.801307/+2.254635/-1.724453 | -0.335612 | 0.813436 | 16.467526 -> 0.605707 |
| 2026102502 | - | — | — | — | — | 16.619498 -> not reconstructed |
| 2026102503 | + | 149.937720 | +1.780877/+1.892339/-3.441292 | -0.062280 | 1.120557 | 16.461419 -> 0.600650 |
| 2026102503 | - | 149.953595 | -1.781412/-1.819033/+1.723960 | -0.046405 | 1.032618 | 16.600795 -> 0.606527 |

The initial one-step post-update gate fails for seed 2501 positive, 2502 positive
and 2503 negative; it passes for 2501 negative and 2503 positive. Seed2502 negative
never reaches that stage. The five valid cases use the same explicitly approved
one-extra-correction protocol. Their initial failures remain visible.
The final post-update maxima are recorded per coordinate in the checkpoint;
they are same-data consistency checks, not independent Truth-recovery evidence.

There are 16 completed physical derivative gates (nominal for all six cases,
first-corrected and refined poses for the five valid cases), totaling 786432
two-coordinate derivative-vector checks. Maximum errors are 2.659e-8 mm/rad
and 3.166e-10 mm/mm, against the unchanged 2e-5 gate. The numerical model SHA
is unchanged. All six initial selected ranks are 4; diagonal-scaled conditions
range 1.56642–1.59699. Diagnostic six-column ranks are 6, conditions 1.66660–1.73808,
and maximum diagnostic Y/angular sigmas are 0.191865 um/0.466416 mrad.
Full covariance, correlation, prefix scaling, slope/impact diagnostics and
fixed-reference scope remain in each `solve/observability.json`.

Across all 21 executed Pede stages (including the blocked case's initial fit),
status is normal, rejected local fits are 0, and chi2/NDF spans 0.991021–1.011089.
No error rescaling is recommended or applied. Initial-fit NDF is 6*4096-4=24572;
ACTS stored NDF is 10 per track, so its displayed ratio is a different quantity.
Input ROOT hashes are unchanged in all six cases. Actual CellID/VolumeID/
GeometryIdentifier associations and local measurement/covariance equality are
checked across all available reconstruction passes. L1 retains VolumeID
272631839 and GeometryIdentifier 216173056991691039.

### Physical blocker and minimal next decision

Seed 2026102502, negative rotation, yields an initial estimate within the declared nominal-error engineering
gates: `(Y,Rx,Ry,Rz)=(0.15002 mm,-1.8037,-3.0420,+3.0043 mrad)`.
Its initial joint squared nominal-error distance is 3.40038, selected rank 4,
condition 1.56645, Pede chi2/NDF 24483.8475462/24572=0.9964125 and zero rejected
local fits. This is not a demonstrated rank or solver failure.

However, actual reloaded DD4hep sensitive corners in the **module frame** have
maximum absolute coordinates `(50.2397444,50.0901765,0.3273120) mm`. The unchanged
module half-lengths are `(50.25,50.25,0.325) mm`: thickness containment fails
by 2.311987 um. The injected Truth pose is valid, with maxima
`(50.2396688,50.0899812,0.2749992) mm`, leaving 50.0008 um in that direction.
The original sensor is a 100 x 0.05 x 100 mm box; the module is 100.5 x 100.5 x 0.65 mm.

The independent all-eight-corner calculation is in
`audit/failed_candidate_containment.json`. The constructor source
`result/barrel_geometry_20261023_01/source/SiTrackerBarrel_geo.cpp:41` builds the
module Box from its envelope dimensions; line55 builds the sensitive Box,
lines58–64 apply its component transform, and line128 applies the fixed module
mounting. `rotation.py::pose_checks` correctly refuses the candidate at its
module-box assertion. Independent matrix checks find maximum DD4hep/ACTS
serialization errors 2.65e-14/1.39e-14, with unchanged center contract and IDs
(`audit/failed_candidate_pose_identity.json`). A successful converter reload
alone does not certify daughter containment.

The partial `correction/` is preserved without a completion marker. There is
no corrected reconstruction, second correction, activation or substituted seed
for this case. Do not clamp the fit, invent a prior, relax containment, enlarge
the envelope or claim 6/6 success. The fixed tight computational module box
does not cover this otherwise ordinary noisy estimate. This establishes a
physical candidate-feasibility limitation for the declared fixture ensemble;
it does not demonstrate incorrect derivatives or an unconstrained model.

The smallest next design decision is to review, explicitly, whether the air
module envelope should accommodate a prospectively specified admissible pose
and uncertainty range, or whether a new, smaller physical fixture should be
preregistered and all cohorts rerun. Either changes this milestone's preserved
Geometry/fixture contract and is not implemented. Moving the entire module
instead of the sensitive component would change correction semantics and
requires a separate design/validation. An additional reconstruction of the
invalid candidate is not an acceptable substitute.

### Limited initial-fit statistics, including the stopped case

Each row below has N=3 independent seeds. Bias is **initial fit minus injected
parameter**, sample SD is across seeds, and Pull uses the original corresponding
unscaled initial covariance. The Y row uses um; angular rows use mrad.

| Sign | Parameter/unit | Mean bias | Sample SD | Mean nominal sigma | Pull mean | Pull sample SD |
|---|---|---:|---:|---:|---:|---:|
| + | Y [um] | -0.090000 | 0.236432 | 0.191624 | -0.470735 | 1.234875 |
| + | Rx [mrad] | -0.007733 | 0.010868 | 0.019463 | -0.398235 | 0.560220 |
| + | Ry [mrad] | -0.203667 | 0.260011 | 0.448392 | -0.458514 | 0.588859 |
| + | Rz [mrad] | -0.024000 | 0.871953 | 0.390848 | -0.063067 | 2.234684 |
| - | Y [um] | -0.010000 | 0.030000 | 0.191622 | -0.052090 | 0.156594 |
| - | Rx [mrad] | +0.004367 | 0.012281 | 0.019463 | +0.225406 | 0.632493 |
| - | Ry [mrad] | -0.112367 | 0.597217 | 0.448395 | -0.240152 | 1.337043 |
| - | Rz [mrad] | -0.407000 | 0.792473 | 0.390842 | -1.040135 | 2.026845 |

These three-seed results do not certify bias, unbiasedness or nominal-error
coverage. Rz Pull sample SDs around 2 merit a separately designed uncertainty
study; they do not justify rescaling the errors here. Comparing this new Ry
mean with the previous three-axis mean cannot isolate a model effect: seeds
and fitted scope differ. The earlier exact frozen-row diagnostic attributes
that existing sample's Ry offset mainly to its realized pixel rounding, not
to a demonstrated numerical defect. Population quantization bias remains an
open statistical question. Finite differences and valid geometry composition
are validated independently of any statistical uncertainty-model claim.

ROOT plots: `audit/cohort_summary/output/cohorts.root` has 16 estimate/Pull
objects for all initial fits, including the blocked fit. Each of the five
completed cases has 9 chi2/residual histograms in `validation/rotation.root`
(the first positive case uses `refined_validation/rotation.root`). Read these
with ROOT/TBrowser. `audit/cohort_summary/output/report.json` contains the
complete raw covariance, labels and units; `audit/final_checkpoint.json`
records every input checksum, all actual completed derivative gates, selected
and diagnostic information matrices, final poses, solver diagnostics and the
explicit checkpoint failure. No cumulative-fit uncertainties are combined.

All run commands are preserved under the six case directories' `driver/`;
the first positive case has a separate `refinement_driver/`. The summary is
independently reproducible with `cohort_summary.py --runs` listing those six
directories and `--output-dir` pointing to a **new** result directory. Final
post-failure safety/preservation checks passed in `audit/final_safety/`.

### Source and commit status at this checkpoint

The read-only investigation is committed locally as
`f38b70428b41f52c24c50ab73c88067847fda70a`
(`Diagnose native Ry offsets with read-only pixel attribution`). The feature
and its documentation remain uncommitted because the requested six-fixture
validation gate did not pass. Existing supported modes and their complete
regressions remain successful. No push, merge or production activation occurs.

The uncommitted files are the exact Mille whitelist, `rotation.py`, `closure.py`,
`observability.py`, `cohort_summary.py`, the four-label configuration, three
beam recipes, five focused new unit tests, and this report/User Guide/Code Map.
No numerical fitter, NativeMilleModel, covariance, detector envelope, SO(3)
primitive, Controller or existing scientific assertion is changed. Native
Global X/Z fitting, full six-DOF/multi-layer inference, Geant4 migration and
statistical coverage remain separately gated future work.

## Unchanged-envelope four-parameter containment milestone

This is a new experiment, not a relabeling of the original 5/6 result. Its audit
root is `result/native_containment_20261024_01_audit/`. Before edits, all 13
uncommitted files were copied byte-for-byte with SHA256 hashes under
`working_tree_snapshot/`; index and unstaged patches were saved separately.
`original_six_runs_manifest.json` pins all 2838 files from the previous six cases.
Nothing is reset, stashed, deleted or overwritten.

### Physical meaning and independently reproduced cause

The installed constructor source copied in
`result/barrel_geometry_20261023_01/source/SiTrackerBarrel_geo.cpp` defines
`Material air = description.air()` and constructs the module as an Air Box
(line41), the silicon sensitive Box (line55), the component placement
(lines58–64), and the parent mounting (line128). The fixture generator
`validation/telescope_geometry/prepare.py::prepare` explicitly chooses module
thickness `sensor_thickness + 0.6 mm`. Each SiMAPS module contains exactly one
100 x 0.05 x 100 mm silicon component, inside a 100.5 x 100.5 x 0.65 mm Air mother.
There is no support, frame, cooling, cable or mechanical assembly in this XML.
Thus the source establishes a **computational Air mother (Option B in the
classification)**, not a measured mechanical thickness. It still defines a real
DD4hep/Geant4 containment boundary: successful ACTS conversion alone does not
validate a daughter outside that boundary.

Module centers are 50 mm apart along native Global X, with one module per
cylindrical layer. The layer mothers are Air Tubes, z half-length 51 mm. Their
explicit inner/outer radii and the detector hierarchy are unchanged. For L1,
inner/outer radii are 298.975/305.606747504 mm. Module world half-lengths are
(0.325,50.25,50.25) mm; its sensitive half-lengths before the fixed mounting
are (50,0.025,50) mm. All eight corners, not just the tracking surface, must fit.
The canonical +Z geometry and the +X barrel fixture are distinct configurations.
No mechanical allowed-motion specification is available; the actual box,
cylinder and existing 10 mrad chart limits define this study's admissible poses.

Let Q=Exp(w) and let R0 be the nominal silicon-to-world rotation. The exact
world-X half-extent is `sum_j abs((Q R0)[0,j])*h_j`. To first order,

```
e_X = 0.025 + 50*(abs(Ry)+abs(Rz)) mm + O(|w|^2)
```

so the approximate thickness requirement is `abs(Ry)+abs(Rz)<6 mrad`.
Global Rx mostly consumes tangential clearance; at Y=+0.150 mm the first-order
requirement is `0.150+50*abs(Rx)<0.250 mm`. The bounds are coupled, not independent
hard alignment constraints. Actual matrix/corner checks remain authoritative.
The old candidate's |-3.0420|+|3.0043|=6.0463 mrad explains the overflow:
exact half-extent 0.327311987 mm exceeds 0.325 mm by 0.002311987 mm. Truth's
0.274999188 mm is contained. The nominal-error distance 3.40038 and normal Pede
status do not imply geometric feasibility.

### Options and chosen scope

| Option | Scientific implication | Decision |
|---|---|---|
| A: unchanged mother, smaller prospective fixture | Same detector, material, segmentation, reconstruction and inference; explicitly different physical injection and fresh seeds | Chosen |
| B: separately enlarged computational mother | Silicon and sensitive surface might remain unchanged, but Air occupancy, volume boundaries/hierarchy, Geant4 stepping and ACTS volume construction need independent checks; no demonstrated mechanical specification justifies treating it as harmless | Not implemented; never size it from the single 2.312 um excess |
| C: constrain/clamp the fit | Hard pose constraints create boundary-dependent estimates and invalidate ordinary unconstrained inverse-Hessian uncertainty interpretation; priors change inference | Not implemented; no clipping, prior or rescaling |

Changing module placement instead of the sensitive component would change the
existing physical correction semantics and requires a separate study. Option A
resolves the test-design problem without making any detector-design change.
The original 5/6 experiment and its stopped candidate remain permanent evidence.

### Prospective unchanged-Geometry test

The new explicit modes are `l1_y_rx_ry_rz_contained` and
`l1_y_rx_ry_rz_contained_negative`. They share the exact existing four-label
configuration, fitter, covariance, whitening, local parameters, CKF cut 1000,
electron hypothesis and Pede steering. Positive injection is
(Y,Rx,Ry,Rz)=(+0.150 mm,+1.8,+1.0,-1.0 mrad); the negative fixture keeps Y and
reverses the whole rotation vector. This is a single Exp(w), never an Euler sum.
Other sensors and L1 X/Z remain fixed.

Before new data/Pede, `geometry_only_preflight/` evaluates 528 joint-error
points per sign using all six previous initial covariances. Directions lie on
the joint 5-sigma ellipsoid, with a further 10% engineering design margin.
This margin is **not** applied to any measurement uncertainty or fitted covariance.
Exact corner calculations pass all 1056 sampled poses. The worst sampled pose
for each module axis/sign is independently reloaded through actual DD4hep/ACTS,
with pivot, rotation, CellID-derived identifiers, cylinder and box checks.
This is sampled engineering evidence, not an exhaustive ellipsoid proof or
statistical coverage. Every actual fitted candidate is checked again.
The smallest sampled clearance is approximately 4.7 um tangentially and 36.9 um
in thickness. No fit result selected the amplitudes.

`prospective_plan.json` declares seeds 2026102601/02/03, 4096 tracks per signed
fixture, all six cases retained without replacement, the unchanged original
four-parameter gates, and at most one explicit additional correction. No
Controller loop or Geometry activation is introduced. `contained_beam_seed*.json`
changes only seed/description from the previous bounded uniform beam recipe.
The original mode strings and their amplitudes remain unchanged.

### Executed new experiment: six complete physical closures

Seeds 2026102601,2026102602,2026102603 each supply 4096 rays and both rotation
signs. These are three independent cohorts, not six independent ray samples.
All initial fits are retained. The new experiment achieves numerical initial
fit success 6/6, initial-candidate feasibility 6/6, every-update feasibility 12/12,
and complete fresh-reconstruction closure 6/6. The **original** experiment still
has numerical success 6/6, initial physical feasibility 5/6 and full closure 5/6.

| Seed | Sign | Initial Y [um] | Initial Rx/Ry/Rz [mrad] | Final cumulative Y [um] | Final cumulative Rx/Ry/Rz [mrad] |
|---|---|---:|---|---:|---|
| 2026102601 | + | 149.890000 | +1.782300/+0.303000/-0.897490 | 149.888684 | +1.782358/+0.186807/-0.889733 |
| 2026102601 | - | 149.880000 | -1.790400/-1.923700/+1.515300 | 149.876559 | -1.790610/-1.834275/+1.515126 |
| 2026102602 | + | 150.070000 | +1.800900/+0.565770/-0.747600 | 150.071001 | +1.800526/+0.451590/-0.758804 |
| 2026102602 | - | 150.200000 | -1.830400/-1.251000/+0.969980 | 150.203933 | -1.829636/-1.119659/+0.968267 |
| 2026102603 | + | 150.210000 | +1.808700/+0.980180/-0.911580 | 150.206800 | +1.808931/+0.876510/-0.911315 |
| 2026102603 | - | 150.120000 | -1.794300/-1.434500/+0.799270 | 150.124086 | -1.794560/-1.331696/+0.794542 |

The positive target is (150 um,+1.8,+1.0,-1.0 mrad); the negative target
is (150 um,-1.8,-1.0,+1.0 mrad). Final vectors are Log(Rfinal Rnominal^T), not
sums of Euler coordinates or naïvely summed Pede vectors.

| Seed | Sign | Final center Y error [um] | Orientation error [mrad] | ACTS chi2/stored-NDF before -> final | Initial/final Pede chi2/NDF |
|---|---|---:|---:|---|---|
| 2026102601 | + | -0.111316 | 0.820825 | 16.587242 -> 0.599812 | 0.999847/0.999835 |
| 2026102601 | - | -0.123441 | 0.980539 | 16.489810 -> 0.598732 | 0.998143/0.998036 |
| 2026102602 | + | +0.071001 | 0.599107 | 16.611793 -> 0.601481 | 1.002766/1.002617 |
| 2026102602 | - | +0.203933 | 0.127293 | 16.579375 -> 0.594059 | 0.990252/0.990246 |
| 2026102603 | + | +0.206800 | 0.152297 | 16.562774 -> 0.599992 | 1.000182/1.000136 |
| 2026102603 | - | +0.124086 | 0.390211 | 16.615728 -> 0.595641 | 0.992991/0.992884 |

Actual L1 X/Z centers remain fixed. VolumeID 272631839 and ACTS
GeometryIdentifier 216173056991691039 remain unchanged. All five SiMAPS local
measurements and calibrated covariance matrices match across reconstruction
passes, as do their raw segmented payloads. The initial ROOT input is immutable
within every case. Fresh EICrecon processes use each corrected XML through the
same official geometry service and native tracking components. No candidate
is activated as production Geometry.

The original quarter-initial-sigma angular and 20 nm Y remaining-update gates
are unchanged. Initial one-step post-updates fail for positive seed 2601,
positive 2602 and negative 2602; the other three pass. All six follow the same
prospectively fixed maximum-one-extra-correction protocol. Final maximum absolute
post-updates are 0.035971 nm for Y and (0.0013824,1.1567,0.39766) urad for Rx/Ry/Rz.
These demonstrate same-data consistency, **not** exact Truth recovery. Initial
covariance/Pulls and final cumulative poses remain separate; correlated fit
uncertainties are never added in quadrature.

There are 18 completed actual DD4hep/ACTS physical derivative gates: nominal,
first-corrected and refined for all six cases, totaling 884736 two-coordinate
derivative-vector checks at the established three step sizes for each column.
The maximum angular error is 2.645e-8 mm/rad; translation error 3.182e-10 mm/mm,
both below the unchanged 2e-5 threshold. Pivot, matrix and identifier contracts
pass every actual reload. The smallest independent module-frame corner
clearance across the 12 actual proposed updates is 8.393428 um.

All 24 official Pede stages terminate normally with zero rejected local fits.
Pede chi2/NDF ranges 0.990246–1.002766. No error rescaling is recommended or
applied. Initial Pede NDF is 24572=6*4096-4; ACTS stores 10 measurement dimensions
per track, so its displayed ratio is not the statistical reduced chi2 for the
four-local-parameter line. Official before/after `inspectMilleBinary` reads
4096 records/40960 scalar equations in each binary and finds all four labels.

### Formal covariance and limited statistics

The initial positive seed 2601 covariance below uses coordinate order
(Y[mm],Rx[rad],Ry[rad],Rz[rad]); entries carry the product of row/column units.
All six full covariance/correlation matrices, individual nominal errors, prefix
track-count scaling, slope/impact subsets, ranks and conditions are retained in
each `solve/observability.json` and the cohort report. None is rescaled.

| Coordinate | Y [mm] | Rx [rad] | Ry [rad] | Rz [rad] |
|---|---:|---:|---:|---:|
| Y [mm] | 3.674153978e-08 | -7.695681706e-11 | -1.995323155e-09 | -1.685203263e-08 |
| Rx [rad] | -7.695681706e-11 | 3.763006989e-10 | -1.937056471e-10 | 3.950626000e-11 |
| Ry [rad] | -1.995323155e-09 | -1.937056471e-10 | 1.947080909e-07 | 3.417055091e-09 |
| Rz [rad] | -1.685203263e-08 | 3.950626000e-11 | 3.417055091e-09 | 1.546677052e-07 |

The following statistics use **initial Pede fit minus injected physical
parameter**, with the corresponding initial unscaled nominal sigma. Each row
has N=3 independent seeds; paired signs share rays. Y uses um, angles mrad.

| Sign | Parameter/unit | Mean bias | Across-seed sample SD | Mean nominal sigma | Pull mean | Pull sample SD |
|---|---|---:|---:|---:|---:|---:|
| + | Y [um] | +0.056667 | 0.160416 | 0.191629 | +0.295599 | 0.836634 |
| + | Rx [mrad] | -0.002700 | 0.013563 | 0.019405 | -0.140255 | 0.697749 |
| + | Ry [mrad] | -0.383683 | 0.341408 | 0.446889 | -0.867686 | 0.774212 |
| + | Rz [mrad] | +0.147777 | 0.090880 | 0.392911 | +0.377819 | 0.236697 |
| - | Y [um] | +0.066667 | 0.166533 | 0.191629 | +0.348152 | 0.869316 |
| - | Rx [mrad] | -0.005033 | 0.022055 | 0.019405 | -0.263916 | 1.142701 |
| - | Ry [mrad] | -0.536400 | 0.347734 | 0.446894 | -1.203993 | 0.793987 |
| - | Rz [mrad] | +0.094850 | 0.373991 | 0.392915 | +0.242537 | 0.949063 |

A negative Ry offset remains in these paired initial estimates. Three seeds
cannot establish a calibrated bias correction, unbiasedness or uncertainty
coverage. The original Rz Pull sample SDs 2.2347/2.0268 remain unchanged and
visible in `original_summary_replay/`; the new smaller-fixture spreads do not
invalidate that earlier finding or demonstrate improved calibration. Detector
containment, actual derivatives and reconstruction closure are validated
separately from the still-unvalidated statistical uncertainty model. No further
statistical campaign or new detector degree of freedom is launched here.

`cohort_summary/output/cohorts.root` contains 16 estimate/Pull ROOT objects.
Each case has 9 ACTS chi2/residual histograms in `validation/rotation.root`,
created and reopened successfully for ROOT/TBrowser inspection. The full
initial estimates, covariances and warning/rejection diagnostics are in
`cohort_summary/output/report.json`. `scientific_summary.json` records all raw
input hashes, 12 actual candidate corner checks and 18 physical derivative
gates. Its scientific six-case result is distinct from final regression status.

### Final regression, preservation and source evidence

All 12 established native modes were rerun with the fresh native build. All 72
protected nominal/Truth/corrected XML and nominal/corrected/control Mille Binary
artifacts are byte-identical to the preceding milestone. Scientific report JSON
is identical, excluding only the regenerated whole-ROOT-file metadata checksum;
channel-payload checksums remain identical. See `protected_72_identity.json`.
The original six run directories retain all 2838 file hashes, and the original 13
working-file snapshots retain their starting hashes (`final_preservation_identity.json`).
The original statistical summary was rerun and compares equal in every field,
including its failed fit and unchanged 5/6 status (`original_summary_replay/`).

The fresh 18-command suite passed in
`result/native_containment_regression_l1_l2_y_20261024_01/containment_complete_regressions/`:
new standalone geometry/CKF builds, actual navigation/measurement checks,
native/legacy Mille and mathematical equivalence, official Pede, all 74 unit tests
(70 existing plus 4 new), safety and preservation. Final unit tests were also
recorded independently in `final_unit_tests/`, and post-campaign safety and
preservation in `final_safety/`. Historical 99-track regression passed in
`result/native_containment_legacy_20261024_01/` using the unchanged existing
legacy build, not a new legacy compilation: 99 tracks, L2 +198.75 um,
Rec-Sim -199.5713755 -> -0.8213645 um, ACTS 45.59223485 -> 1.981039768.
All nine upstream patches reproduce identically against the read-only pinned
EICrecon checkout. No installed software is edited.

The numerical/geometry/configuration source contract verifies 161 files unchanged
from this phase's starting state, including its preserved uncommitted Mille
whitelist (`protected_source_identity.json`). The NativeMilleModel SHA remains
`1622cc80327fe08dd6c943bb57e537a8fea86a95233389065efa91739028843f`.
No fitter, particle hypothesis, hit error, whitening, selected degree of freedom,
Pede steering, SO(3) primitive, canonical Geometry or Controller is changed.

The exploratory preflight's first invocation failed with `research_common`
missing from its script import path. No geometry or fit output was created.
The corrected invocation and maintained CLI passed with identical preflight
numbers; the incident is retained in `technical_incidents.json`. Existing
SQLite connection ResourceWarnings, CMake developer warnings and container
`stty` messages remain in logs. No warning is suppressed and no scientific
assertion is weakened. The expected original physical refusal remains distinct
from these technical messages and from the six successful **new** cases.

`final_checkpoint.json` records the completed milestone and all numerical,
physical and regression rates. Research data, logs, builds and snapshots stay
outside Git. The local feature commit includes the preserved four-parameter
implementation and the new bounded-fixture/safety validation; diagnostic commit
`f38b70428b41f52c24c50ab73c88067847fda70a` remains separate. No push, merge or
production Geometry activation is performed.

### Reproducible commands and retained limits

Use fresh build/output paths for a repeat. These are the actual build arguments:

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake \
  -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_containment_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_containment_20261024_01 -j2
```

The User Guide gives independent preflight and permanent-refusal commands.
A complete new six-case repetition uses the unchanged driver:

```bash
(
for seed in 1 2 3; do
  for sign in positive negative; do
    mode=l1_y_rx_ry_rz_contained
    if [[ "$sign" == negative ]]; then mode=l1_y_rx_ry_rz_contained_negative; fi
    bash environment/run.sh python3 validation/telescope_closure/closure.py \
      --build build/native_containment_20261024_01 \
      --result "result/my_contained_seed${seed}_${sign}" \
      --mode "$mode" --events 4096 \
      --beam "validation/telescope_alignment/contained_beam_seed${seed}.json" \
      --chi2-cut 1000 --refine-once --step all || exit 1
  done
done
)
```

The actual paths are `result/native_containment_seed{1,2,3}_{positive,negative}_20261024_01/`.
Their `driver/command.json`, exit codes and immutable markers record each
executed invocation. Every stage is independently callable through `--step`.
For a fresh consolidated suite, use a completed original two-Y run:

```bash
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_containment_20261024_01 \
  --result result/native_containment_regression_l1_l2_y_20261024_01 \
  --events 32 --chi2-cut 1000 --mode l1_l2_y \
  --step regressions --validation-name MY_NEW_CHECK
bash environment/run.sh python3 -m unittest discover -s validation -p 'test_*.py'
bash environment/run.sh python3 validation/check_safety.py
bash environment/run.sh python3 validation/verify_preservation.py
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/my_containment_historical99 \
  /work/build/native_three_rotation_legacy_20261024_01
```

All 12 individual native modes use the unchanged commands/event counts listed
in the preceding milestone; substitute the new native build and fresh result
names. The nine upstream patches are independently reproduced on the host:

```bash
python3 -B validation/telescope_factories/upstream_diff.py \
  --source /Users/tkumaoka/eic/EICrecon --output result/NEW_upstream_diffs
```

Official decoder commands are recorded in `official_binary_nominal/` and
`official_binary_refined/`; they use `environment(build)` to load the maintained
Mille installation. The new cohort summary command is in
`cohort_summary/command.json`; list all six actual run directories with
`cohort_summary.py --runs ... --output-dir result/NEW_summary` to reproduce it.
The preserved original dataset and checkpoint are prerequisites for the
preflight/refusal regression; they are intentionally excluded from Git.

This completes a **controlled unchanged-envelope four-parameter fixture**,
not arbitrary pose support. Statistical coverage, the earlier negative Ry
behavior and Rz Pull spread remain unresolved. More translations, full six-DOF,
multiple free layers/gauge handling, native Controller integration and original
Geant4/experimental-input migration remain separately gated. No additional
physics campaign, constrained estimation or envelope redesign is implemented.

The historical negative three-axis `ordered_vs_joint_distance_rad` diagnostic
retains its fixed-positive ordered comparator for value stability. It is not
cited as a like-signed order test. New contained fixtures compare their own
signed vector with its corresponding ordered product; actual pivot, inverse,
constructor, derivative and closure checks provide the physical validation.


## Native multi-sensor milestone: L1 four parameters plus L2 Y

This milestone starts from `9f75da6dfe161d65896edf80e996779fbb748803` on
`feature/upstream-acts-geometry`. Scope A selects five simultaneous global
parameters: L1 Y/Rx/Ry/Rz and L2 Y. Scope B is a later validation gate, not implied
by the read-only eight-column sensitivity diagnostic.

The existing NativeMilleModel equations, four local track parameters,
calibrated-covariance whitening, electron hypothesis, CKF selection, official
Pede steering method and detector envelopes remain unchanged. No provider,
fitter, navigator, solver, activation policy or Controller is added.

### Selection, associations and physical correction

The actual native SourceLink points to an EDM measurement and its RawHit-derived
CellID. The DD4hep converter and official ACTS SurfaceMap resolve the physical
surface. The existing C++ processor verifies these associations before selecting
global columns by sensor. New configuration entries carry the actual distinct
IDs, not a reused L1 identity:

| Sensor | DD4hep VolumeID | ACTS GeometryIdentifier | Enabled labels in Scope A |
|---|---:|---:|---|
| L1 | 272631839 | 216173056991691039 | 700102, 700104, 700105, 700106 |
| L2 | 272633887 | 216173194430644511 | 700202 |

Columns 1/3/4/5 of the existing six-column ACTS physical derivative correspond to
Y/Rx/Ry/Rz. Fixed L0/L3/L4 contribute measurements and four-local-parameter
constraints, but no free global labels. Both sensors' X/Z translations are fixed.

`closure.displaced_xml` now permits a selected L2 component rotation using the
same existing matrix serializer. Shared module templates are cloned per sensor;
references and all unrelated XML are checked independently. Each simultaneous
Pede result updates each selected physical center by world Y and each selected
orientation by `Exp(dw_global) R_current`, about its current sensitive center.
Actual DD4hep and ACTS matrices, all seven surface identities, module boxes and
layer envelopes are checked after every reload. At most one extra explicitly
requested correction uses the same immutable channel bytes. Initial unscaled
nominal errors are never summed across these dependent fits.

### Prospective fixture and observability

The fixture was fixed before inspecting new recovery: L1 Y +80 um, L2 Y -60 um,
L1 rotation vector (+1.0,+0.5,-0.5) mrad; negative reverses rotations only.
The 4096-event cohort uses seed 2026102701 and the unchanged bounded broad-angle
recipe. Before generating its data, both signs passed 252 correlated joint
5-sigma sampled error directions with a 10% design-only engineering margin and
fourteen real DD4hep/ACTS constructor reloads. The smallest module clearance was
90.703 um. Sampling is an engineering preflight, not proof over a continuum or
statistical coverage.

`multi_information.analyze` profiles the four locals separately for every actual
native track. It records accumulated rank, dimensionless condition, complete
mixed-unit covariance/correlation, cross-sensor correlations, sample-size
prefixes, slope/impact subsets, and omitted-X/Z diagnostics. Per-track full
global rank is deliberately not required. A separate thirty-column diagnostic
releases reference sensors to verify common rigid gauge directions; it does not
add parameters or constraints to Pede. Six common rigid directions are null;
the nominal parallel-plane diagnostic has rank 21/30, including three additional
unclassified null directions outside this selected scope. With references fixed,
the prior five-column design has rank 5 and condition 2.0342; the eight-column
read-only design has rank 8 and condition 3.2761. Neither establishes uncertainty
coverage or unrestricted six-DOF support.

Every solve independently profiles the decoded official Mille records, compares
their information with the native rows, checks sensitivity before Pede, and
compares the result and nominal errors with official unscaled Pede output.
Y errors must be below 1 um; angular errors below 0.5 mrad; scaled condition below
100. Recovery retains the existing five-sigma marginal and joint squared-error
<25 gates. Final post-fit updates retain the 20 nm Y and quarter-initial-sigma
angular gates. No gate, measurement error or steering setting is relaxed.

### Reproduction and evidence

The executable fresh-build, prospective-preflight and complete-closure commands
are in the multi-sensor section of `TELESCOPE_ALIGNMENT_USER_GUIDE.md`.
Independent stages remain available through `closure.py --step`.
The audit root is `result/native_multi_20261024_01_audit/`; the Scope A cohort is
`result/native_multi_scope_a_seed1_positive_20261024_01/`. All old results and
partial failures remain untouched. `protected_manifest.json` records 3347 files
from the protected six contained fixtures and original refused case.

The fixed container build succeeded. All 84 tests (74 existing plus ten new)
passed. Nine official upstream patches reproduced exactly. Safety/preservation
checks passed, including 221 baseline records and 2046 relocated files.
The 18-command consolidated suite and historical 99-track regression use fresh
output directories; the historical test reuses its unchanged existing legacy
plugin build, rather than claiming a new legacy compilation. The original
expected physical-containment refusal remains a separate negative regression.
The first four old native modes already reproduce all six protected XML/Mille
artifacts and scientific reports exactly, except independently regenerated ROOT
container metadata hashes. Final cohort recovery and remaining regression
results are recorded below only after their actual completion.

### Scope A completed result

The independently executed Scope A cohort passed full closure: **1/1**, 4096
accepted tracks in each reconstruction, zero outliers and zero Pede rejected
local fits. Its initial five-parameter fit and final cumulative pose are:

| Parameter | Injected | Initial Pede | Nominal sigma | Final cumulative correction |
|---|---:|---:|---:|---:|
| L1 Y [um] | 80 | 79.965 | 0.197643 | 79.964975471 |
| L1 Rx [mrad] | 1.0 | 1.021 | 0.0195943 | 1.020794647 |
| L1 Ry [mrad] | 0.5 | 0.23909 | 0.452627 | 0.201299218 |
| L1 Rz [mrad] | -0.5 | -0.71327 | 0.398090 | -0.706804032 |
| L2 Y [um] | -60 | -60.136 | 0.181287 | -60.136047501 |

The actual selected information has rank 5 and diagonal-scaled condition
1.980128. Every recorded sample-size prefix (16 through 4096) and all six
slope/impact subsets have rank 5. L1/L2 Y correlation is 0.262071. The complete
5x5 covariance, axis correlations and omitted-component diagnostics are saved
in each solver's `observability.json`. The common rigid gauge residual norm
ratios are below 7.08e-16; the released-reference diagnostic changes rank from
21 to 23 after physical rotation, while the six rigid null directions remain.
Extra nullity is Geometry dependent and is not an enabled alignment mode.

ACTS chi2/stored-NDF improves **9.946553319 -> 0.597247931** (control
0.596316760). Final orientation error is 0.363899 mrad on L1; L2 orientation is
unchanged as required. Center biases are -0.035025 um and -0.136048 um.
Both physical updates pass unchanged all-eight-corner/module/layer gates and
actual DD4hep/ACTS matrix and ID checks. All unrelated XML is identical under
the independent placement whitelist.

The first correction already passes the existing post-update gate; the explicit
fixed protocol also exercised its one allowed extra correction. Final updates
are at most 0.031999 nm in Y and 0.10244 urad in angle. This extra fit uses the
same RawHit bytes and supplies no independent uncertainty to add in quadrature.
Three real-Geometry finite-difference gates each check 61440 two-coordinate
vectors across all five parameters and three step sizes. Angular differences
remain below 2.64e-8 mm/rad. Official independent decoding confirms both nominal
and final files contain 4096 records, 40960 scalar measurements, precisely the
five labels, and no free labels on fixed sensors.

Scope A's numerical validation and 84 unit tests are complete. Remaining
historical native-cohort reruns continue separately and will be reported at the
end of this milestone; they are not represented as complete by this checkpoint.
This demonstrates selected Geometry/derivative/reconstruction closure. One seed
cannot validate bias, coverage or the nominal uncertainty model.


### Scope B prospective development record

Scope A was committed locally as `b3b4cc922aaae0d20de20cd96294053acebc3e37`
before enabling Scope B. No push, merge or Geometry activation was performed.
Scope B adds L2 Rx/Ry/Rz labels 700204/700205/700206 to the five existing labels.
Their actual L2 VolumeID/GeometryIdentifier are the same independently verified
L2 IDs listed above, rather than L1 IDs. Native equations and local parameters
remain unchanged; only bounded selection/validation and config entries expand.

Before inspecting any Scope B fit, the fixture was fixed as the same L1 pose and
translations as Scope A, with L2 rotation vector (-1.2,+0.6,+0.6) mrad. Both
signed fixtures reverse both rotation vectors and retain both translations.
Seeds 2026102701 and 2026102702 use the unchanged bounded angular recipe;
signs within a seed share rays and are not independent statistical experiments.
The prospective plan is `scope_b_prospective_plan.json` under the audit root.

A Geometry-only preflight using the unchanged fresh Scope A geometry probe
passed 6576 correlated joint 5-sigma sampled directions per sign, plus the same
10% design-only margin. Fourteen actual constructor reloads verify both signed
truth poses and each sensor's worst sampled module-axis poses. The smallest
module clearance is 85.298 um. All boxes, layer envelopes, IDs and unrelated
XML remain unchanged. No new recovery estimate was used to select amplitudes.
Scope B full reconstruction is reported below only after completion.

The current pre-Pede gate also checks the full twelve-column L1/L2 nuisance
diagnostic: rank 12, scaled condition below 100, and the same selected-component
sensitivity limits after X/Z (and any other fixed diagnostic components) are
released. No such columns are enabled in Pede. All four Scope A fits separately
pass this conservative diagnostic; their worst selected error/limit is 0.965117.
The recorded prefix study first passes the tested sensitivity gate at 4096
tracks. The prior Scope B design needs approximately 3669 tracks under a fixed
1/sqrt(N) sensitivity extrapolation, so no larger cohort is currently justified.

### Maintained Pede pre-sigma semantics

The steering remains `Parameter label 0.0 1.0`, `entries 5`, and
`method inversion 3 0.001`; no new prior, constraint or regularization command
has been added. Official Pede reports `regularization: no`. The local official
manual (`external/src/millepede-ii/doc/draftManual.md`, lines 1399-1408) and
`pede.f90` show that positive pre-sigmas still add diagonal solver stabilization.
With regularization disabled, the objective/gradient contain no prior penalty;
finite iteration can retain damping effects, and matrix-inversion nominal errors
retain `(H+W)^-1`. Here every maintained pre-sigma is 1.0 and W is the identity
in the declared mixed physical units. This is distinct from the data-only
covariance `H^-1`, which supplies the observability/rank tests before Pede.

All twenty Scope A printed errors agree with the stabilized covariance at
printed precision. The maximum relative sigma difference from `H^-1` is
1.02474e-7. All parameter estimates also pass the existing printed-precision
comparison to the unpenalized data-only solution; exact unbiasedness after
finite iterations is not claimed. Full source hashes and quantitative evidence
are in `pede_presigma_source_note/` under the audit root. Current multi-sensor
reports label the data-only covariance and expected Pede stabilized covariance
separately. Neither is a statistically calibrated coverage measurement.


### Demonstrated observer defect and preserved primary retry

The first Scope B primary attempt completed nominal/corrected reconstruction,
all initial/corrected physical derivatives, the simultaneous eight-parameter Pede
fit and first post-fit gate. Its optional refined reconstruction then stopped at
event 355, L2, in the validation-only `FactoryAudit`.

The actual failed ROOT output and an independent reconstruction from immutable
CellIDs and real refined Geometry agree exactly. Double local coordinates are
(-17.112654700154234, -9.422352232365252) mm; official `Measurement2D` stores
binary32 (-17.112655639648438, -9.422351837158203) mm. Legitimate rounding has
norm 1.019234e-6 mm (**1.019234 nm**), exceeding the observer's fixed
1e-6 mm (**1 nm**) double-versus-float comparison. Each component is within
half an ULP; the joint half-ULP norm bound is 1.066240e-6 mm. This is an
observer representation defect, not a wrong surface or physical Geometry.

`FactoryAudit.h::Process` now requires exact componentwise agreement with the
official converter's `static_cast<float>` serialization and finite doubles.
Surface identity remains exact. Independently, the unrounded DD4hep channel
center must map to and back from its real ACTS plane within the unchanged
1e-6 mm geometric threshold. The hit-to-surface membership tolerance, official
measurement converter, calibrated covariance, CKF, Mille equations and physics
are unchanged. This is not an arbitrary increase of a tolerance: it also rejects
a deliberately corrupted one-ULP value at 0.25 mm whose 2.98e-8 mm difference
would have passed the old guard. A regression using the actual installed
`edm4hep::Vector2f` type passes; the total unit suite now has 91 tests.

All 597 files from the interrupted first attempt remain protected by
`failed_primary_manifest.json`. Fresh build `build/native_multi_precision_20261024_01`
contains the observer fix. Retry `result/native_multi_scope_b_seed1_positive_20261024_02`
retains byte-identical copies of the original Geometry, RawHits and completed
scientific checkpoints, including their original command records. Only the
failed refined reconstruction and downstream stages are newly executed.
This is the same seed/cohort, not a replacement or additional independent
sample. `primary_retry_provenance.json` explicitly distinguishes reused and
reexecuted stages. No additional correction is applied: the retry reconstructs
the same already-proposed refined XML and keeps the one-extra-correction limit.
The failed attempt is not reclassified as a successful full closure.

Detailed independent evidence is under `measurement_precision_diagnosis/`,
`scope_b_measurement_precision_review/` and `primary_retry_provenance.json`.
The earlier independent decoder text-parser mismatch is separately retained in
`official_binary_scope_b_nominal/parser_incident.json`; official output and
scientific data were unchanged.

### Scope B primary eight-parameter closure — completed

The independently validated primary cohort is seed 2026102701, 4096 tracks,
`result/native_multi_scope_b_seed1_positive_20261024_02`. The earlier `_01`
attempt and its observer failure remain intact. The retry copied only completed
byte-verified checkpoint stages, then executed refined reconstruction, final
Pede, control reconstruction/Pede and validation with the fresh precision build.
It did not regenerate channels or apply an additional third correction.

Initial Pede corrections and data-only marginal nominal errors are distinct
from cumulative poses, which are read from the actual final matrices. Rotation
components below are rotation-vector components in mrad, not Euler angles.
Y values are in micrometers. The small Pede inversion stabilization described
above remains unchanged; it is not used in the reported data-only covariance.

| Parameter | Injected | Initial Pede | Initial nominal sigma | Final cumulative |
|---|---:|---:|---:|---:|
| L1 Y | +80.000000 | +79.961000 | 0.197914 | +79.960389 |
| L1 Rx | +1.000000 | +1.018000 | 0.020273 | +1.017837 |
| L1 Ry | +0.500000 | +0.362890 | 0.467939 | +0.318919 |
| L1 Rz | -0.500000 | -0.673120 | 0.412032 | -0.667791 |
| L2 Y | -60.000000 | -60.084000 | 0.194368 | -60.084070 |
| L2 Rx | -1.200000 | -1.229700 | 0.016425 | -1.229801 |
| L2 Ry | +0.600000 | +0.667800 | 0.353325 | +0.610818 |
| L2 Rz | +0.600000 | +0.786860 | 0.343284 | +0.790271 |

The initial data-only correlation matrix, in the same row/column order, is:

```text
 1.000000  0.000911 -0.011859 -0.202086  0.262949  0.000343 -0.002758 -0.052168
 0.000911  1.000000 -0.003446 -0.002018  0.001194  0.256569 -0.000712 -0.000705
-0.011859 -0.003446  1.000000 -0.020645 -0.002440 -0.000897  0.253675 -0.002750
-0.202086 -0.002018 -0.020645  1.000000 -0.092931 -0.001058 -0.006473  0.257944
 0.262949  0.001194 -0.002440 -0.092931  1.000000  0.005357 -0.007175 -0.360379
 0.000343  0.256569 -0.000897 -0.001058  0.005357  1.000000 -0.003205 -0.004682
-0.002758 -0.000712  0.253675 -0.006473 -0.007175 -0.003205  1.000000 -0.017611
-0.052168 -0.000705 -0.002750  0.257944 -0.360379 -0.004682 -0.017611  1.000000
```

The full eight-by-eight covariance in mixed mm/rad units is retained in
`solve/observability.json` and `validation/report.json`. The cross-sensor
same-axis correlations are approximately 0.254–0.263; the largest absolute
off-diagonal correlation is 0.360379 (L2 Y/Rz). Each track has global rank 4,
which is allowed: the accumulated rank is 8 with diagonal-scaled condition
3.165386. All recorded prefixes (16–4096 tracks) and the slope/impact subsets
retain rank 8. The released L1/L2 twelve-component diagnostic has rank 12 and
scaled condition 3.464460; the selected marginal errors also pass the unchanged
sensitivity thresholds when X/Z are included as diagnostic nuisance columns.
These columns are not enabled in the actual fit.

Holding L0/L3/L4 fixed removes the selected-scope gauges. When all five sensors
are released in the separate 30-column diagnostic, the six common rigid
directions have projected design norm ratios below 3.12e-16. The released
design has rank 21 at nominal Geometry and rank 23 after rotation. Its remaining
null directions are not resolved by priors or interpreted as support for an
arbitrary thirty-parameter fit.

Both sensitive centers remain fixed in X/Z. Final Y biases relative to Truth
are -0.039611 and -0.084070 micrometers; L1/L2 orientation distances are
0.247513 and 0.192894 mrad. Both are smaller than their injected rotation-vector
norms. All actual eight-corner module/layer checks and unrelated XML whitelist
checks pass. The actual IDs are preserved independently:

| Sensor | DD4hep Volume ID | ACTS GeometryIdentifier |
|---|---:|---:|
| L1 | 272631839 | 216173056991691039 |
| L2 | 272633887 | 216173194430644511 |

All 4096 tracks are accepted before/after correction and in the control, with
five measurements, zero outliers and the same two expected holes. ACTS
chi2/stored-NDF improves from 10.104523004 to 0.593123052; the control is
0.596316760. Local residual RMS (u,v) improves from (43.955,9.427) to
(7.704,7.699) micrometers. The first one-step post-fit gate already passes.
The explicitly selected one extra correction gives a largest final increment
of 0.000319764 initial nominal sigma; successive-fit uncertainties are never
combined. Initial joint error Mahalanobis squared is 6.128952, below the
existing 25 gate.

| Pede stage | chi2 | NDF | chi2/NDF |
|---|---:|---:|---:|
| solve | 24293.257615 | 24568 | 0.988817063 |
| postsolve | 24293.986926 | 24568 | 0.988846749 |
| refinesolve | 24293.990347 | 24568 | 0.988846888 |
| controlsolve | 24419.280297 | 24568 | 0.993946609 |

All four Pede executions exit normally with zero rejected local fits, no
warnings, and no recommended/applied error rescaling. Independent profiled
chi2 agrees with official Pede. Actual native finite differences check all eight
columns at three step sizes: 98,304 two-component vector checks per Geometry
stage. Across nominal, first-corrected and refined stages the maximum angular
error is 3.290e-8 mm/rad and translation error 4.547e-10 mm/mm, below the
unchanged 2e-5 gate. The official decoder reads 4096 records/40960 scalar
measurements with exactly eight selected labels, each occurring 8192 times.
Fixed layers carry no unintended global labels.

The identical shifted RawHit ROOT file SHA-256 is
`46a19f92c3ac4e23baefe6698014c0b144fae0862700f1800db4dcd10ced3f99`;
the channel payload SHA-256 is
`64dac26410d8572e0c5e2f90a7087196de29e9f4a99a72399720823fe9f38ba0`.
All three alignment reconstructions read those same bytes. The input frame
contains only EventHeader and TelescopeChannels; Simulation Truth is used only
for the independent validation. `validation/rotation.root` contains nine ROOT
histograms for ACTS chi2 and local residual comparisons.

Read-only summaries and raw command/exit evidence are in
`result/native_multi_20261024_01_audit/scope_b_primary_final_summary/`.
Additional predeclared seed/sign results are reported separately below.
This establishes Geometry, derivative and reconstruction closure; it does not
establish unbiasedness or nominal-error coverage.

### Consolidated protected regression results

All twelve prior native modes completed their full nominal/Pede/correction/fresh
reconstruction/control closure, and all six protected contained L1 fixtures
completed their full one-extra-correction workflow in fresh result directories.
Their nominal/truth/corrected XML and nominal/corrected/control official Mille
bytes are exactly identical to the prior protected references. The six contained
cases also have byte-identical refined XML/Mille records. Scientific reports
are identical except for the independently checked ROOT container file hash;
the packed channel payload itself remains identical. ROOT container metadata
makes newly written ROOT files unsuitable for cross-generation byte identity.
Within each individual fixture the original input ROOT bytes are immutable.

The 18-case comparison is
`result/native_multi_20261024_01_audit/baseline_identity.json`; its command was:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -B \
  result/native_multi_20261024_01_audit/baseline_identity.py
```

Full old-mode closures used the fresh Scope A build. Separately, the final
precision plugin passes all 18 configuration checks on four events, producing
exact existing native Mille prefixes. Full-event final-plugin reconstruction
replays are recorded separately; their status must be read from
`final_plugin_full_replay_summary.json`, not inferred from the pilot checks.
Those replays compare the entire Mille Binary and all fitted-state/audit values;
only the verified new derivative-gate output path differs in equation-report
metadata. The first replay comparison stopped on that expected path metadata;
its original driver and diagnostic are retained without weakening numerical
comparisons or rerunning its completed reconstruction stage.

The final fresh precision build also completed every command of the independent
18-command consolidated suite in
`result/native_multi_regression_l1_l2_y_20261024_01/precision_complete_regressions/`.
All exit codes are zero: fresh standalone Geometry/CKF builds, actual one-event
JANA reconstruction, native/legacy mathematical equivalence, official Pede
mathematical fixture, 91 unit tests (74 existing plus 17 multi-sensor/precision
tests), safety and preservation. SQLite ResourceWarnings in pre-existing tests
remain visible in the saved stdout; they did not fail tests. No test result is
inferred from source inspection.

The historical Geant4/BeamTestReco 100-event regression also executed successfully
in `result/native_multi_legacy_20261024_01`: 99 accepted tracks, L2 correction
+198.75 micrometers, L2 Rec-Sim -199.571 to -0.821 micrometers, ACTS
chi2/stored-NDF 45.592234848 to 1.981039768. It reused the unchanged prior legacy
build; a new legacy compilation is not claimed. The saved simulation dataset
under `results/reference/physical_alignment_L2_x200um/` remains a local reference
and is not added to Git.

The original wider negative fixture still produces
`EXPECTED_PHYSICAL_CONTAINMENT_REFUSAL`, with the same 2.311987-micrometer parent
overflow. Its fitted result is reproduced exactly, but its invalid candidate is
not reconstructed or activated. The protected negative test is in
`result/native_multi_expected_refusal_20261024_01/report.json`; physical closure
is explicitly false and safety is true. It is not counted as a successful
physical closure and was not replaced by an enlarged envelope.

Final independent source/preservation evidence is in
`result/native_multi_20261024_01_audit/final_source_preservation/`: 3347 historical
files and 597 failed-primary files rehash exactly. Of 161 protected sources,
159 are byte-identical and exactly two adapters change intentionally:
`TelescopeMille.cc` selection guards and the `FactoryAudit.h` validation observer.
NativeMilleModel numerical equations, copied official tracking modules, original
Geometry/SO(3), legacy fitter/electron hypothesis and Controller are unchanged.
All nine pinned upstream patches reproduce byte-identically. Separately executed
safety/preservation commands confirm 221 baseline records plus 2046 relocated
files and the protected electron change. No external source tree, installed
library, historical result, or Geometry activation was modified.

The completed final-plugin full-event replay summary now confirms **19/19 cases,
49,280 events**: the twelve old modes, all six contained fixtures, and Scope A.
Every official Mille Binary is byte-identical and every fitted-state/audit value
is exactly equal, with only the independently verified fresh derivative-gate
path excluded from equation-report metadata. This closes the final-build
compatibility check rather than relying solely on four-event pilots. Executed
command:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -B \
  result/native_multi_20261024_01_audit/final_plugin_full_replay_v2.py
```

Evidence is `final_plugin_full_replay_summary.json` and each `full_replay_*`
audit stage. The original path-comparison incident and first driver remain
available in the same audit directory. These are current-milestone validation
replays of fresh regression cases, not modifications of historical references.

### Scope B four-fixture validation — completed

All four predeclared fixtures pass, with 4096 accepted tracks per fixture.
There are **two independent seeds (2026102701 and 2026102702), not four
independent statistical samples**: opposite rotation signs share the same
generated rays within each seed. The translations stay +80/-60 micrometers;
negative fixtures reverse both rotation vectors. The 8192 distinct ray draws
produce 16384 signed-fixture events; repeated reconstruction/control records
are not counted as additional independent data. Scope A has one full positive
cohort, plus both signs of its prospective Geometry-only preflight.

All four initial one-step post-update gates pass. Each follows the same
predeclared protocol with one explicit additional correction and no further
iteration. Maximum final increment is 0.000673995 initial sigma (maximum
fraction of an angular final gate 0.00269598). No successive-fit covariance is
added. The original observer-failed primary attempt remains one retained
failed execution of the same seed, not an extra sample or a failed physical
closure after the demonstrated software fix. No additional fixture failed.

| Seed | Sign | ACTS chi2/stored-NDF before → final | L1/L2 orientation error [mrad] | L1/L2 center Y bias [um] | Min fitted module clearance [um] |
|---|---|---|---|---|---|
| 2026102701 | positive | 10.104523004 → 0.593123052 | 0.247513 / 0.192894 | -0.039611 / -0.084070 | 119.153319 |
| 2026102701 | negative | 10.151074565 → 0.601026869 | 0.418621 / 0.221817 | -0.065317 / -0.092541 | 120.241183 |
| 2026102702 | positive | 10.120347257 → 0.604577774 | 0.194667 / 0.334748 | -0.127122 / -0.337961 | 120.285504 |
| 2026102702 | negative | 10.175597063 → 0.604759650 | 0.855724 / 0.296875 | +0.004390 / +0.041115 | 119.403935 |

All sixteen Pede fits exit 0 with zero rejected local fits, no warnings or error
rescaling. Their chi2/NDF spans 0.9888170635–1.0082473763, with NDF=24568.
Selected accumulated rank is 8 in every solve; the diagonal-scaled condition
spans 3.16497465–3.29604556. The twelve-column diagnostic retains rank 12 and
passes the inherited selected-sensitivity bounds. Six released common rigid
motions have maximum norm ratio 7.10e-16. No gauge prior is added.

The twelve actual-Geometry finite-difference gates cover 1179648 two-component
vectors across four fixtures and three Geometry stages. Maximum errors are
3.309721208e-8 mm/rad and 5.459127594e-10 mm/mm. All eight sensitive corners
remain within the unchanged actual parent boxes and cylindrical layer bounds;
minimum fitted-pose module clearance is 119.153319 micrometers. Every input
file/channel SHA matches across the three alignment reconstructions of its
fixture. All four ROOT files reopen with nine histograms each: 4096 chi2
entries and 20480 residual entries per relevant histogram.

The full eight-parameter initial estimates and original nominal uncertainties
for the three additional fixtures are retained below. Units are mm/rad, and
cumulative rotations are actual matrix-log values, not sums of fit vectors.
The primary table above uses micrometers/mrad instead.

#### Seed 2026102701, negative rotations

| Parameter | Initial Pede | Initial nominal sigma | Final cumulative | Unit |
|---|---:|---:|---:|---|
| L1 Y | +0.079934 | 0.000197911838698 | +0.07993468274 | mm |
| L1 Rx | -0.00099698 | 2.02726831405e-05 | -0.000996730327978 | rad |
| L1 Ry | -0.0006306 | 0.000467941251798 | -0.000589358994729 | rad |
| L1 Rz | +9.9087e-05 | 0.000412026095449 | +9.10409780758e-05 | rad |
| L2 Y | -0.060093 | 0.00019436619453 | -0.06009254131 | mm |
| L2 Rx | +0.00119 | 1.64250446116e-05 | +0.00119010404238 | rad |
| L2 Ry | -0.00055499 | 0.000353329063259 | -0.000500979057898 | rad |
| L2 Rz | -0.00039488 | 0.00034328517176 | -0.000401758769205 | rad |

Run: `result/native_multi_scope_b_seed1_negative_20261024_01`.

#### Seed 2026102702, positive rotations

| Parameter | Initial Pede | Initial nominal sigma | Final cumulative | Unit |
|---|---:|---:|---:|---|
| L1 Y | +0.079873 | 0.000198894026102 | +0.07987287807 | mm |
| L1 Rx | +0.00099691 | 2.03291008456e-05 | +0.000997039354926 | rad |
| L1 Ry | +0.00074675 | 0.000466112353184 | +0.000693402123935 | rad |
| L1 Rz | -0.00048226 | 0.000417956866842 | -0.00047804016219 | rad |
| L2 Y | -0.060336 | 0.000195749744763 | -0.0603379609 | mm |
| L2 Rx | -0.0011941 | 1.63528975533e-05 | -0.00119415105565 | rad |
| L2 Ry | +0.00061003 | 0.000350935209256 | +0.000553360373447 | rad |
| L2 Rz | +0.00092368 | 0.000345093847846 | +0.0009314311572 | rad |

Run: `result/native_multi_scope_b_seed2_positive_20261024_01`.

#### Seed 2026102702, negative rotations

| Parameter | Initial Pede | Initial nominal sigma | Final cumulative | Unit |
|---|---:|---:|---:|---|
| L1 Y | +0.080003 | 0.000198895375536 | +0.0800043895 | mm |
| L1 Rx | -0.0010131 | 2.03290557574e-05 | -0.00101301873612 | rad |
| L1 Ry | -0.00071513 | 0.000466118283947 | -0.000662886372334 | rad |
| L1 Rz | +0.0013551 | 0.000417963359174 | +0.00133997743926 | rad |
| L2 Y | -0.05996 | 0.000195751299859 | -0.0599588848 | mm |
| L2 Rx | +0.001212 | 1.6352843653e-05 | +0.00121186421965 | rad |
| L2 Ry | -0.00053435 | 0.0003509400544 | -0.000475999160388 | rad |
| L2 Rz | -0.00032862 | 0.000345097424703 | -0.000330523426501 | rad |

Run: `result/native_multi_scope_b_seed2_negative_20261024_01`.

The complete English read-only audit is
`result/native_multi_20261024_01_audit/scope_b_four_fixture_summary/`: `SUMMARY.md`,
`summary.json` (all eight-by-eight covariance/correlation matrices, actual IDs,
RawHit hashes, Geometry chains, prefixes/subsets and all sixteen solver logs)
and `containment.json`. Every executed command has its exit status and stdout.
These local generated datasets are excluded from Git; the maintained CLI,
beam/configuration JSON and generation source reproduce them in fresh paths.

The executed additional commands use the exact flags/mode/beam/result table in
`TELESCOPE_ALIGNMENT_USER_GUIDE.md`; the primary checkpoint retry is explicitly
distinguished from a fresh `--step all` reproduction. No original data, partial
failure, checkpoint, install or external archive was deleted or overwritten.

#### Changed code paths and supported boundary

| Maintained path/function | Change |
|---|---|
| `TelescopeMille.cc::Init` | Exact five/eight-label whitelists and L2 rotation validation; `Process`/native equations unchanged |
| `FactoryAudit.h::Process` | Demonstrated double/float observer defect fixed with exact serialization plus independent strict geometric check |
| `closure.py::displaced_xml`, `solve`, `main` | Selected L2 correction, explicit new modes, accumulated native rank/sensitivity gates, original Pede steering and covariance conventions |
| `rotation.py` selection, `physical_derivatives`, `correct`, `refine`, `check` | Both sensors use the existing SO(3) implementation and original correction gates |
| `multi_sensor.py` | Bounded label/sensor mappings, fixed fixtures, pose increments and independent XML whitelist |
| `multi_information.py::analyze` | Read-only local-four-parameter elimination, covariance, gauge, prefix and slope/impact diagnostics |
| `multi_preflight.py` | Prospective correlated engineering perturbations, actual DD4hep/ACTS reload and module/layer containment |
| Four alignment/beam JSON files | Explicit actual L1/L2 identities and two fixed seeds; unchanged beam recipe |
| `test_native_multi_sensor.py` | Seventeen tests including actual EDM precision, sensor isolation and two-sensor composition |
| User Guide, Code Map, this parity report | Actual commands, provenance, numerical results and limitations |

The SourceLink/CellID → DD4hep VolumeContext → official SurfaceMap → native ACTS
state path is unchanged. Configuration selects labels for the actual matched
sensor; fixed layers contribute local tracking information but no selected
global columns. Both selected physical sensitive centers/rotations are updated
from one Pede result using the original left-Global matrix update and fresh
Geometry reload. Shared module definitions are cloned independently and the
unrelated XML, segmentation, material and reference sensors remain unchanged.

Scope A and Scope B are validated **experimental** capabilities within the
existing zero-field, quantized-channel, unassigned-ACTS-material test. The
largest final orientation error is 0.855724 mrad and the Ry/Rz nominal errors
are of order 0.35–0.48 mrad: numerical convergence is not proof of exact Truth
recovery. Two seeds and paired signs do not validate bias or uncertainty
coverage. No arbitrary six-DOF, additional free layer, material-aware physics
performance, original Geant4-channel compatibility, automatic Controller loop
or production Geometry activation is claimed. Those remain separate gated
development/validation steps. The legacy scientific implementation is retained.
