# Legacy/native telescope alignment parity

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
