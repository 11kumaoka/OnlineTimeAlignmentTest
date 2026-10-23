# Coupled SO(3) alignment validation

This checkpoint resolves the finite-rotation model identified in
[TILT_ALIGNMENT_VALIDATION.md](TILT_ALIGNMENT_VALIDATION.md). Evidence is
retained under `result/rotation_resolution_20261023_01/`; fresh builds are
`build/rotation_resolution_20261023_01/` and
`build/rotation_resolution_20261023_02/`. Historical reports and failed outputs
remain unchanged. No Geometry is automatically activated; no commit or push
is authorized for this work.

## Cause and model decision

The previous update `Ry(dy) Rx(dx) Rcurrent` was a correct left Global rigid
rotation about the sensitive center. Its infinitesimal fixed-Global derivatives
were also correct. The mismatch was between those generators and the intended
finite two-coordinate family `Ry(beta) Rx(alpha) Rreference`.
`[Kx,Ky]=Kz`; repeated fixed-Global increments leave that family. A two-component
stationary point can retain unfitted twist and compensate with incorrect tilt.
The complete orientation error was 357.389 urad, not merely the 16.307 urad
ordered-Rz diagnostic. More events cannot fix this noiseless defect.

A precisely constrained ordered chart is sufficient for targets in that chart,
provided its alpha axis is transported by the current Ry factor. Unit tests
check its exact finite retraction, transported differential, nonzero reference
Rz, repeated updates and rejection of off-chart orientations. It is not exposed
as an alignment mode: it would change the meaning of the previous Global-Rx
parameter and exclude generic orientations.

The general model instead releases all three Global infinitesimal rotations
and uses `Rnew=Exp([w]x) Rcurrent`. All three components are fitted together;
none is discarded after fitting. Existing label signs are preserved. See
[Geometry conventions](GEOMETRY_CONVENTIONS.md#coupled-global-rotations-so3-increments)
for the residual derivative, pivot, units, relative matrix and XML contract.
The numerical ACTS KF, electron hypothesis, uncertainty settings, material,
Digitization, official Pede steering settings and existing correction branches
are preserved.

## Mandatory mathematical controls

`validation.so3_closure` generates fixed continuous sensor-local coordinates
from straight lines, using the unchanged 0.01 mm physical uncertainty. This is
an explicitly noiseless mathematical fixture, not a Geant4 sample or uncertainty
coverage experiment. Only the current Geometry and fixed local coordinates enter
the production writer and official Pede. Truth is used in the fixture generator
and after inference to compare complete matrices.

The pre-simulation source-pinned run is `noiseless_final/`; the final helper revalidation is `noiseless_release/`. It exercises the maintained
Geometry Correction stage, rather than a separate correction implementation.
Cases include individual Rx/Ry, positive and negative coupled tilts, reverse
rotation order, nonzero initial Rz, translated sensor centers, two-layer
rotations and both six-DOF scopes. Repeated corrections serialize/reload full
matrices; all unselected placements remain fixed. Closure tolerances are
1 urad in relative SO(3) angle and 0.00002 mm in center distance. These account
for official float32 Mille input precision; no measurement errors are rescaled.

The exact previous fixed-point file was also replayed in
`same_fixture_recovery/`, starting from its saved failed Geometry. Its unchanged
SHA-256 is recorded in `report.json`. Five three-rotation corrections reduce
357.388796 urad to 0.122704 urad. Small remaining variations are at the float32
writer floor. The input-coordinate and actual-float32-row profiled chi2 are
different diagnostics and must not be interchanged.

The first large-offset L1/L2 six-DOF fixture was aborted by official Pede with
status 26, “too many rejects”. It remains in
`noiseless/two_six_dof/iteration-001/`. The same model, errors and rejection
settings close at one-quarter of the declared translation offsets. This is a
capture-range control, not a repair by steering adjustment. The failed
large-offset case is outside the demonstrated capture range from that initial
Survey; full rank does not guarantee acceptance of a distant starting Geometry.

## Physical derivatives and provenance gates

`validation.validate_tilt_derivatives --coupled` checks all six Global columns
against fresh-process DD4hep fixed-channel finite differences and actual binary
entries written by the production C++ writer linked to `external/install/lib/libMille2.so`.
The reference trajectory and covariance whitening are frozen within each
finite-difference comparison. Independent NumPy profiling verifies the writer's
reference slopes. Both L1 and L2 use nonzero centers, positive/negative tilts,
a combined orientation with existing Rz, three channels, three slopes and
three finite-difference step sizes. Rotational steps are in radians;
translation steps are in mm. Existing physical material and readout are retained.

The Controller requires a same-plugin/factory sealed derivative report, actual
binary checks, fresh contexts, canonical constrained steering and the mandatory
noiseless cases. It pins every proof and the mathematical/correction/writer
sources. Before each fit it profiles the **actual** weighted Mille rows over
four local track parameters, verifies selected rank and applies explicit
angular/linear information bounds. These are configurable demonstration
sensitivity bounds, not statistical coverage certification.

## Interpretation limits

A passed Geometry transformation, finite-difference derivative, information-rank
or noiseless closure test establishes its own property. None alone certifies
noisy physical Geometry recovery or the Pede uncertainty model. Initial-fit
errors and cumulative corrections from the same fixed RawHits must not be
combined as independent measurements. The prior Rz ensemble's broad pulls and
Pede chi2 findings remain unresolved; this model correction does not calibrate
them. MPGD and AC-LGAD measurements and additional sensors are not released by
the six-DOF SiMAPS L1/L2 implementation.

### Numerical derivative precision

The final L1/L2 suites pass **444 fresh contexts**, **1,944 two-component
physical comparisons**, and **1,296 decoded binary components**, including
implicit zeros. There are 949 nonzero stored selected coefficients (472/477
for L1/L2); these are distinguished from decoded zero components. Largest
whitened binary absolute error is 5.604e-5, consistent with float32 coefficient
precision. Frozen-reference/covariance and physical-sign checks pass for every
selected family.

| Step (rad for rotations; mm for translations) | Max rotational derivative error [mm/rad] | Max translational derivative error [mm/mm] |
|---:|---:|---:|
| 1e-3 | 1.7432e-6 | 9.4680e-13 |
| 1e-4 | 1.7430e-8 | 7.9350e-12 |
| 1e-5 | 1.8261e-10 | 6.8242e-11 |

Evidence: `derivative_stored_precision.json` and `derivative_precision.json`.
Immutable raw reports used legacy `epsilon_rad`/`*_per_rad` keys for translation
rows too; their numbers are in mm/mm, as explicitly normalized in the supplement.
The maintained validator now emits parameter-unit fields. No raw proof or
physical result was overwritten to correct that metadata naming issue.

## Executed controlled samples and scope

Five independent Geant4 samples were generated: **1,400 events**, seeds
2035033002–2035033006. The first four contain 100 events each; the fifth is one
scientifically justified independent 1,000-event cross-check of the anomalous
two-layer six-DOF pilot. Reconstructed replays and outer iterations are not
additional independent samples. Every sample retains identical RawHit bytes
across all its iterations; all candidates remain inactive.

The initial physical constructor is `Rz(gamma) Ry(beta) Rx(alpha)`. L1 uses
(alpha,beta,gamma)=(+30,-25,+17) mrad; L2, when selected, uses
(-25,+20,-12) mrad. Six-DOF cases additionally inject L1 (+0.0375,-0.0300,+0.5000)
mm and L2 (+0.0500,+0.0225,-0.3750) mm. These declared small offsets are separate
from the preserved larger-offset capture failure. Canonical 1 GeV electron
physics, mean source (0,0,-500) mm, beam widths/angles, material and errors are
unchanged. Only the declared placements, recorded seeds and the separate
1,000-event count differ.

| Case / seed | Tracks before/after | Iterations | ACTS chi2/stored-NDF before → exact final | Full-matrix orientation error L1/L2 [mrad] | Center error L1/L2 [mm] |
|---|---:|---:|---:|---:|---:|
| L1 rotations / 2035033002 | 99/99 | 7 | 30.354835 → 1.424435 | 4.6689 / — | 0 / — |
| L1/L2 rotations / 2035033003 | 98/98 | 7 | 61.691912 → 1.310673 | 9.0265 / 6.4789 | 0 / 0 |
| L1 six-DOF / 2035033004 | 95/95 | 7 | 31.176129 → 1.189007 | 2.5037 / — | 0.05617 / — |
| L1/L2 six-DOF, 100 / 2035033005 | 98/98 | 6 | 64.382490 → 1.425805 | 7.5522 / 15.0389 | 0.10625 / 0.33114 |
| L1/L2 six-DOF, 1,000 / 2035033006 | 955/955 | 5 | 62.990432 → 1.395316 | 2.5377 / 2.5962 | 0.05630 / 0.03608 |

All geometric/derivative/observability/serialization/tracking gates passed for
these explicit scopes. **The 100-event two-layer six-DOF pilot does not establish
precise Geometry recovery**: its L2 Z error is -0.33112 mm, about 4.4 final
nominal standard errors. The independent higher-statistics sample reduces that
error to -0.03608 mm; L1 Z error remains -0.05629 mm. This rules out the previous
fixed 357-urad noiseless parameterization defect as the explanation, but does
not establish an unbiased statistical estimator or calibrated confidence
intervals. No candidate has been approved for activation.

For comparison, the injected **relative SO(3) vectors** are L1
(30.2102,-24.7425,17.3728) and L2 (-24.8789,20.1487,-11.7490) mrad. They differ
from the ordered constructor angles and must not be compared componentwise as
though they were the same parameters.

| Case | Recovered L1 relative vector [mrad] | Recovered L2 relative vector [mrad] |
|---|---|---|
| L1 rotations | (29.451,-29.345,17.170) | — |
| L1/L2 rotations | (36.177,-31.516,17.276) | (-28.450,14.743,-11.789) |
| L1 six-DOF | (32.657,-24.216,17.434) | — |
| L1/L2 six-DOF, 100 | (27.618,-31.836,17.317) | (-36.900,29.183,-11.959) |
| L1/L2 six-DOF, 1,000 | (31.827,-26.699,17.389) | (-26.338,22.293,-11.641) |

The 1,000-event recovered translations are L1
(+0.03773783,-0.02977623,+0.44370550) mm and L2
(+0.04969531,+0.02298969,-0.41108024) mm, relative to Nominal centers.
Complete matrices, centers, initial/final fit values, nominal errors,
correlations, seeds, input hashes and Geometry chains are in
`scientific_summary_final.json`; individual stages retain exact argv and logs.
No correction reads Simulation Truth.

### Geometry, reconstruction and Survey checks

Each of the five cases, plus a separate approximate-Survey replay, passed
fresh-process DD4hep position/basis checks against actual initial-correction
and exact-final reconstructed outputs. RecHit XYZ agrees at float32 precision;
ACTS local measurements, covariance permutations, Global TrackPoint covariance
and predicted/filtered/smoothed intersections pass. Independently imported
physical, first and final GDML matches all seven matrices/centers and has zero
illegal overlaps/extrusions at 0.0001 mm tolerance.

The Survey is declared independently as small fixed center offsets and rotation
vectors, with no MC or fitted values used to construct it. Using the same
1,000-event RawHit bytes, it converges in five iterations to within
0.0703/0.1044 urad and 0.00000119/0.00000012 mm of the Nominal-start L1/L2
solution. Both version chains retain their respective initial active Geometry.
Evidence: `survey_replay.json` and `survey_six_dof_validation/passed.json`.

Three off-plane SimHits in the 1,000-event sample and one in the L1 six-DOF
sample are preserved and reported; **none belongs to an accepted event** in
before/after checks. No input event is filtered. Because unaccepted anomalous
hits can dominate all-event validation RMS, final ROOT files retain the
all-unique-pair distributions and additionally show clearly labeled
accepted-track distributions. Those post-fit selections do not affect inference.
For 1,000 events, accepted L1/L2 normal residual RMS improves
0.59846/0.47329 → 0.06013/0.04292 mm. The corresponding final means are
-0.05627/-0.03588 mm, consistent with the reported residual center offsets,
not exact zero closure. These fixtures use plane-local u/v coordinates, not the
DD4hep sensor X/Y/Z basis; physical channel finite differences separately check
that basis conversion.

### Rank, correlations and warnings

Initial column-normalized information conditions are 1.096 (L1 rotations),
1.976 (two-layer rotations), 5.248 (L1 six-DOF) and 7.957 (two-layer six-DOF
100). Their ranks are 3/3, 6/6, 6/6 and 12/12. The higher-statistics final design
is rank 12/12 with condition 7.558. Initial X–Ry and Y–Rx correlations reach
about 0.63; final Z–tilt and Rz–tilt correlations remain material. Full matrices,
column-normalized eigenvalues and weak eigenvectors are retained per iteration.
All unselected sensors are fixed; this is relative alignment with reference
planes, not a freely floating detector.

Every controlled solver process exited zero and retained Pede status 1
(chi2 warning). Pede chi2/NDF initial → last is respectively
2.4553→2.3828, 2.3699→2.2071, 2.0346→2.0019, 2.4855→2.4225 and
2.3710→2.3300 for the table's five cases. Pede's suggestion to multiply input
errors was **not applied**. Maximum internal rejected-local-fit counts are
0,18,0,19,169; the nonzero counts occur in early evaluations of the first solve,
and later evaluations return to zero. Final NDF includes every accepted ACTS
track (6*Ntracks minus released globals). Do not sum repeated evaluation
counts as distinct rejected tracks.

The correlated nominal tangent quadratic diagnostics are 5.56/3, 15.01/6,
2.66/6, 38.15/12 and 25.81/12. Their formal chi2 tail probabilities are
0.135,0.020,0.850,0.000145 and 0.0114. These use the final-iteration input
information, not combined errors from successive fits; they are **not calibrated
coverage probabilities**. The two-layer pilot is unusual, and the 1,000-event
result remains in a nominal tail. With only two independent samples of that
Geometry and the established nonunit chi2/Rz pull findings, a persistent small
bias cannot be excluded. Existing process/material/error-model limitations
must be investigated without arbitrary rescaling.

### Support decision and further layers

The finite-rotation defect is resolved. Three-rotation and six-DOF matrix
inference on selected SiMAPS L1/L2 is mathematically supported with fixed
reference planes, demonstrated derivatives, the stated small-angle/offset
capture range and controlled physical reconstruction. Modes are **explicitly
gated demonstrations**, disabled by default. They are not a production
precision-calibration certification. The large-offset two-layer capture case,
arbitrary layouts, unconstrained all-sensor alignment, MPGD/AC-LGAD fitting and
statistically calibrated six-DOF uncertainties remain unsupported.

A read-only extension design suggests rank 18/18, normalized condition 8.824
for hypothetical L1/L2/L3 six-DOF with L0/L4 fixed. The all-five-free noisy
linearized design is rank 25/30 and requires explicit gauge treatment. Its
numerical null count must not be interpreted as the exact physical gauge count:
frozen whitening and nonzero residuals can spuriously lift rotational gauge
directions in a Gauss–Newton information matrix. Neither design releases new
writer/factory/Controller scopes or substitutes for physical derivatives and
closure. Evidence: `generalization_design.json`. No additional detector
parameters or simulation campaign was launched from this diagnostic.

## Regression and preservation results

Both fresh CMake builds passed. The final Plugin loads
`/work/external/install/lib/libMille2.so`; no old installation fallback appears
in its cache/link command. The entire numerical ACTS fitter, electron hypothesis,
Nominal XML and legacy writer suffix are byte-identical to task start.

- Nine historical X/Y/Rz/Z writer replays retain exact Mille bytes and ACTS metrics.
- All four previously validated Rx/Ry samples retain exact initial/final Mille bytes and ACTS metrics (eight replays).
- Historical X, XY, Survey, three Rz and three Z/XYZ Controller runs retain their exact final candidate IDs.
- Fresh legacy X/Y/Rz/Z physical/actual-Mille derivatives pass against the final build.
- Combined/split RawHit equivalence passes, including downstream ROOT branches, Mille bytes and Pede parameters.
- The seven-stage reference retains 99 tracks, +198.75 um L2 correction, -199.571→-0.821 um mean residual and ACTS 45.592→1.981.
- Final execution passes 44 unit tests, existing safety checks, seven new real gate refusals, 63 Python AST checks, 14 Bash syntax checks, baseline ROOT checks and `git diff --check`.
- Preservation verifies the previous **16,412** baseline and **30,138** total pre-task data files unchanged, 762 completed-stage markers, 68 fixed-RawHit Controller iterations and 17 inactive version chains.
- Six final ROOT files contain 572 inspected nonempty objects; all previous ROOT outputs remain untouched.

No historical reference, measurement error, material, physics setting or
external installation was changed. No commit/push or candidate activation was
performed. Retained partial failures include the first large-offset noiseless
Pede abort, the old unsupported-scope unit assertion (updated for the new explicit
mode and covered by new safety tests), and a syntax error in the first ignored
Survey diagnostic harness; its `_v2` retry passed. A host syntax-check attempt
with the default macOS cache path was denied; checks using a writable temporary
cache and final container AST checks passed.

## Outputs and recommended checkpoint

Primary report: `result/rotation_resolution_20261023_01/scientific_summary_final.json`.
Exact commands are in that directory's `COMMANDS.md`, helper source, Controller
`driver.log`, derivative `commands.json`, `final_root_commands.json` and each
stage's `command.json`/exit/stdout files. Final ROOT directories are
`l1_rotations_root_final/`, `two_rotations_root_final/`, `l1_six_dof_root_final/`,
`two_six_dof_root_final/`, `two_six_dof_1000_root_final/` and
`survey_six_dof_root_final/`, each containing `tilt_alignment.root` and PDFs.

```sh
root -l result/rotation_resolution_20261023_01/two_six_dof_1000_root_final/tilt_alignment.root
// In ROOT:
new TBrowser;
```

The next scientific checkpoint should be a focused independent-seed study of
coupled longitudinal/tilt recovery and nominal errors before a further
parameter expansion. Investigate the observed nominal tails and existing
process/error model without changing historical references or forcing unit
chi2. A closer independently surveyed starting Geometry is required before
claiming the failed larger-offset capture range. Additional layers need actual
factory/writer derivatives, explicit references/gauges and controlled closure;
linear rank alone is not sufficient.

## Maintained-source changes relative to task start

The task-start archive includes all pre-existing uncommitted work. No source
file was removed. The exact task-only inventory is
`changes_from_task_start.json`; full pre/post source archives include maintained
untracked files. The numerical ACTS fitter and existing physics configs are
unchanged.

| Change | Files |
|---|---|
| Modified | `README.md` |
| Modified | `alignment/align.py` |
| Modified | `calibration/README.md` |
| Modified | `calibration/iteration.py` |
| Modified | `calibration/settings.py` |
| Modified | `correction/correct_geometry.py` |
| Modified | `correction/scope.py` |
| Modified | `docs/GEOMETRY_CONVENTIONS.md` |
| Modified | `docs/WORKFLOW.md` |
| Modified | `geometry/transforms.py` |
| Modified | `localDetEICrecon/alignment/src/BeamTestMilleWriter.cc` |
| Modified | `localDetEICrecon/processors/BeamTestMilleProcessor.cc` |
| Modified | `reconstruction/reconstruct.py` |
| Modified | `validation/README.md` |
| Modified | `validation/run_closure.sh` |
| Modified | `validation/test_tilt_alignment.py` |
| Modified | `validation/tilt_observability.py` |
| Modified | `validation/tilt_writer_fixture.cc` |
| Modified | `validation/validate_tilt_derivatives.py` |
| Modified | `visualization/tilt_alignment.py` |
| Created | `alignment/pede_l1_l2_rotations.txt` |
| Created | `alignment/pede_l1_l2_six_dof.txt` |
| Created | `alignment/pede_l1_rotations.txt` |
| Created | `alignment/pede_l1_six_dof.txt` |
| Created | `calibration/config/l1_l2_rotations_demo.json` |
| Created | `calibration/config/l1_l2_six_dof_demo.json` |
| Created | `calibration/config/l1_rotations_demo.json` |
| Created | `calibration/config/l1_six_dof_demo.json` |
| Created | `docs/SO3_ALIGNMENT_VALIDATION.md` |
| Created | `geometry/scenarios/L1_L2_rotations.json` |
| Created | `geometry/scenarios/L1_L2_six_dof.json` |
| Created | `geometry/scenarios/L1_rotations.json` |
| Created | `geometry/scenarios/L1_six_dof.json` |
| Created | `geometry/scenarios/l1_l2_rotations_reference.json` |
| Created | `geometry/scenarios/l1_l2_six_dof_reference.json` |
| Created | `geometry/scenarios/l1_rotations_reference.json` |
| Created | `geometry/scenarios/l1_six_dof_reference.json` |
| Created | `validation/merge_so3_evidence.py` |
| Created | `validation/so3_closure.py` |
| Created | `validation/test_so3.py` |
| Created | `validation/test_so3_alignment.py` |

The final validation-helper audit replaced container-root literals with the
existing repository/dependency discovery and normalized relative output paths
before invoking Pede from its iteration directory. This changes validation I/O
only. All nine noiseless cases were rerun using the documented relative CLI
paths in `noiseless_release/`. **Use `gate_release.json` for the final sources**;
earlier gates remain historical evidence and deliberately fail source matching
after a pinned helper changes. A fresh twelve-parameter Controller replay with
the final gate reproduced the same candidate ID and every iteration/final Mille
file byte-for-byte; see `release_gate_validation.json`.

Final executable/source evidence is `release_checks.json`,
`release_data_audit.json`, `release_gate_validation.json`,
`source_audit_final.json` and `source_final_sha256.json`. The pre-existing Git
HEAD and empty index are preserved; the working tree intentionally retains both
pre-existing and new uncommitted source changes.
