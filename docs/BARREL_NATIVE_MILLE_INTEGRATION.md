# Native EICrecon TrackStates to Millepede-II: limited integration

## Scope

This milestone connects the experimental EICrecon/JANA barrel reconstruction
chain to the existing official Mille library. It leaves production
BeamTestReco, BeamTestMilleWriter, the Controller, SO(3) correction, and
historical results unchanged. No Geometry is corrected or activated.

The completed reconstruction milestone was locally committed as
`1541fa89e6ec94e78762ef3e7215c3e6d59fa3f6`
(`Integrate source-based EICrecon barrel reconstruction factories`), after
ROOT read-back, 46 existing unit tests and preservation checks passed again.
The new alignment work remains uncommitted. No push or merge was performed.

Support demonstrated here is deliberately narrow: five accepted SiMAPS
loc0/loc1 measurements, the validated zero-field/material-free barrel fixture,
and physical **L1/L2 Global Y translations** with all other poses fixed.
This is transverse to the new +X beam. It is not a reuse or relabeling of the
old L1/L2 Global X alignment mode. Six surface derivative columns are checked,
but fitting six-DOF alignment is not enabled by this milestone.

## Exact data flow

```text
Unchanged TelescopeTracking JANA plugin
  official DD4hep_service / ACTSGeo_service / ActsGeometryProvider
  TrackerHits -> Measurement2D -> TrackSeed -> official native CKF -> smoothing
  -> TelescopeActsTracks + TelescopeActsStates
  -> unchanged ActsToTracks -> persisted EDM Track/Trajectory

Separate opt-in TelescopeMille JANA processor
  native tracks/states + TelescopeMeasurements
  -> measurement state / IndexSourceLink.index()
  -> Measurement2D -> TrackerHit.CellID -> DD4hep Volume context
  -> official SurfaceMap -> same actual reference Surface pointer / GeometryID
  -> earliest measured smoothed state as common reference
  -> installed ACTS Propagator(EigenStepper, Navigator), reference to each surface
  -> measurement predictions and consistent reference-to-surface Jacobians
  -> installed Surface::alignmentToBoundDerivative
  -> physical Global rotation-basis conversion
  -> covariance whitening and explicit local/global Mille rows
  -> external/install/lib/libMille2.so -> one official double-precision record
```

`TelescopeMilleProcessor` is a normal `JEventProcessor`, like the existing
alignment observer. It requests existing factory outputs. It neither fits a
track nor constructs replacement tracking surfaces/provider/navigation.
Repropagation supplies derivatives around one consistent common reference;
it is not an additional tracking fit. No EDM Track is converted back into
an experiment-specific hit array for alignment inference.

| Input | Type / fields used |
|---|---|
| TelescopeActsTracks | `Acts::ConstVectorTrackContainer`; accepted track, tip/state links, hypothesis, counts, chi2 |
| TelescopeActsStates | `Acts::ConstVectorMultiTrajectory`; flags, path length, smoothed bound parameters/covariance, actual reference Surface, calibratedSize, calibrated measurements/covariance, projector, IndexSourceLink |
| TelescopeMeasurements | `edm4eic::Measurement2DCollection`; source-link index, GeometryID, local coordinates and TrackerHit relation |
| Associated TrackerHit | CellID, including actual DD4hep VolumeID context and SiMAPS layer identity |
| Official Geometry service | Same `ActsGeometryProvider`, SurfaceMap, GeometryContext, magnetic/calibration environment |
| Explicit alignment configuration | `validation/barrel_alignment/l1_l2_global_y.json`; physical units, labels and fixed poses |
| Derivative gate | Successful report with matching compiled NativeMilleModel source fingerprint and matching surface/volume IDs |

Predicted/filtered states, transport Jacobians and smoothed covariances remain
available in the native interface. This prototype does not blindly multiply
stored Jacobians evaluated at differing filtered states: it repropagates the
common reference using the installed ACTS components. The first measurement's
smoothed covariance enables ACTS covariance transport/Jacobian calculation;
it is **not** used as a measurement error or an additional Mille prior.

## Mathematics and statistical assumptions

Let `m_i` be the native two-coordinate calibrated measurement and `V_i` its
calibrated measurement covariance. Let `h_i(q,a)` predict the same local
coordinates on the real sensitive surface. At the current linearization:

```text
r_i = m_i - h_i(q0,a0)
A_i = partial h_i / partial q
G_i = partial h_i / partial a
r_i = A_i delta_q + G_i delta_a + epsilon_i   (linearized measurement equation)
```

The residual derivative itself is `partial r_i / partial a = -G_i`.
Mille receives the **prediction** derivatives `A_i,G_i` on the right hand
side, not this oppositely signed residual derivative.

For the tested deterministic zero-field trajectory, unmeasured q/p and time
cannot affect the two-coordinate predictions. The local unknowns are the
first measurement's bound `(loc0,loc1,phi,theta)`. ACTS supplies the full bound
transport Jacobian; its corresponding first four columns give `A_i`.
The code checks that q/p and time columns do not contribute. The local design
has rank four. This conclusion is derived for this fixture, not assumed from
the old writer's four-parameter model. Nonzero field and ACTS material
assignments are rejected; endpoint field checks supplement the known fixed
zero-field fixture and do not certify arbitrary magnetic maps.

`G_i` uses installed ACTS `Surface::alignmentToBoundDerivative`, including
its path-length correction. In zero field the relevant free position path
derivative is the direction. For a curved track the direction path derivative
also contains the magnetic deflection, and material introduces further
stochastic/energy-loss terms. The present calculation must not be used for
those configurations.

ACTS v45.3 uses Global center translations and infinitesimal rotations about
the current **local** surface axes. For a physical Global left rotation
increment `delta_w`, the local increment is `R^T delta_w`. Therefore:

```text
G_global_translation = G_ACTS_translation
G_global_rotation    = G_ACTS_local_rotation R^T
```

Rotations are about the actual sensitive-surface center. These derivative
columns are checked geometrically, not connected to the existing Controller's
finite SO(3) updates or declared as supported fit modes.

With `V_i=L_i L_i^T`, the writer uses `W_i=L_i^-1` and writes
`W_i r_i`, `W_i A_i`, `W_i G_i` with scalar sigma=1. Thus within-hit covariance
is retained without treating correlated local axes as independent errors.
All ten coordinates from a track share one Mille record and four local
parameters. There is no independent-observation treatment of smoothed states.

The smoothed residuals are biased/data-dependent and mutually correlated.
Using their diagonal errors, or `V_i-H_i C_i H_i^T` independently per state,
would be invalid. Here the fitted state is only a common reference for the
**original measurement likelihood**, with original `V_i`, and all local
corrections are subsequently eliminated by Millepede. In whitened notation:

```text
P = I - A (A^T A)^-1 A^T
N_global = G^T P G
b_global = G^T P r
```

Consequently choosing a fitted q0 does not fix that trajectory or count it as
an independent observation; the local parameters can move freely. In the
linear deterministic limit this equals fitting the absolute measurements.
A finite CKF seed prior is not written into Mille, so CKF chi2 and the
unconstrained profiled measurement chi2 need not be identical.

For stochastic transport one must include process-noise nuisance parameters
and their constraints, or correctly use the joint state/residual covariance.
The deterministic four-local-parameter elimination is not sufficient then.

## Actual ACTS facilities audited

Sources are pinned to ACTS v45.3.0, not current main:

- [Surface.cpp](https://github.com/acts-project/acts/blob/v45.3.0/Core/src/Surfaces/Surface.cpp): `alignmentToBoundDerivative` combines the coordinate and path-length terms; translations refer to Global center coordinates.
- [AlignmentHelper.cpp](https://github.com/acts-project/acts/blob/v45.3.0/Core/src/Surfaces/detail/AlignmentHelper.cpp): local right-increment rotation convention.
- [AlignmentEngine.hpp](https://github.com/acts-project/acts/blob/v45.3.0/Alignment/include/ActsAlignment/Kernel/detail/AlignmentEngine.hpp): uses complete smoothed cross-state covariance, `V-H C H^T`, and warns that its simplified path derivative neglects magnetic curvature.
- Installed `Acts/TrackFitting/detail/KalmanGlobalCovariance.hpp`: `Acts::detail::globalTrackParametersCovariance` reconstructs cross-state covariance from smoothed/filtered/predicted covariances and stored Jacobians. Per-state diagonal blocks alone are insufficient.
- Installed `GlobalChiSquareFitter.hpp`: native measurement accumulation uses calibrated measurement covariance, a measurement projector and transport from a common starting state.

The full `ActsAlignment` kernel/library is not installed in this fixed
container. Its audit does not imply it ran here. Core ACTS surface derivatives
and propagator Jacobians **are** installed and are directly reused. No
separate production analytical derivative system or copied alignment solver
was introduced. The independent analytic ray/plane intersection is strictly
a validation oracle. Downloads and installed-header excerpts are retained
under the new result directory, not installed or maintained as another solver.

## Parameters, gauge and historical comparison

| Physical parameter | New label | Unit | Surface GeometryID |
|---|---:|---|---:|
| SiMAPS L1 Global Y center correction | 700102 | mm | 216173056991691039 |
| SiMAPS L2 Global Y center correction | 700202 | mm | 216173194430644511 |

All other parameters, including all L0/L3/L4 poses, are fixed by absence from
the global unknown vector. With all five Y positions free there are two line
gauge freedoms (offset and slope): the profiled global rank is three out of
five. The chosen two-column system has rank two. No weak six-DOF solution is
forced through a solver.

For comparison only, the unchanged BeamTestMilleWriter is compiled into a
separate validation executable. The **proper** world rotation is
`(old X,old Y,old Z)=(-new Z,new Y,new X)`, mapping the old +Z beam to new +X.
In the nominal radial basis, old X measurement is ACTS v and old Y measurement
is -ACTS u. Legacy Ay denotes measurement bias; the new parameter is physical
Geometry displacement, so `delta Global Y = -legacy Ay`.
The old labels are never copied into the new binary or silently reinterpreted.

The comparison uses old zRef=250 mm, a nuisance-coordinate reparameterization only.
The old source writes absolute coordinates with local `(x0,y0,tx,ty)`; the
new source writes linearized native measurements with local bound corrections.
Their profiled likelihood and Global Y information are equivalent in this
controlled limit. The comparison is not an assertion that the historical
99-track electron/endcap sample was reconstructed through the new geometry.

## Executed results

All new artifacts: `result/barrel_alignment_20261023_01/`.
Fresh build: `build/barrel_alignment_20261023_01/`.

Final artifacts are `derivatives_source_bound.json`, `native_source_bound.dat`,
`native_source_bound.json`, `reconstruction_source_bound.json`,
`reco_source_bound.root`, `validation_final.json`, and
`reconstruction_final_comparison.json`. Final build log: `integration_build04.log`.
The 16-ray solver outputs remain in `noiseless_fixture/`.
Earlier reports, build failures and the intentionally rejected source-gate run
are retained. In particular, `derivatives_final.json` predates the compiled
fingerprint and is **not** the final source-bound gate. A CMake source-path
lookup failure in `integration_build03.log` was corrected using explicit
source-directory paths. No old files were deleted or overwritten.

- Phase 0: preceding one-event CKF/ROOT read-back, 46 tests and protected-data checks passed; 31 milestone file hashes matched before commit.
- Derivatives: five surfaces, four local and six physical Global derivative columns, at two step sizes (100 vector comparisons). Maximum absolute errors: local `2.7821e-8`, Global `3.7193e-10`. The independent oracle uses ray/perturbed-plane intersections.
- Actual JANA native record: one accepted track, five measurements, zero outliers, two expected holes; one double-precision official Mille record, ten scalar equations. Official `inspectMilleBinary` reads it. Native extraction verifies every source-link/VolumeID/GeometryID/Surface association.
- Native CKF chi2 remains `8.400275230407715`, stored NDF=10. The four-local-parameter profiled measurement chi2 is `8.4000295447`; old-writer comparison gives `8.4000301969`. The small old/new difference is compatible with legacy single-precision serialization. The seed prior is not part of the Mille likelihood.
- Profiled Global information agrees with the old writer (maximum absolute difference `0.0006212` on elements of order 7000–8000). The sign-adjusted RHS difference is `1.08e-5`.
- Separate noiseless mathematical fixture: 16 synthetic straight rays; physical L1/L2 Y center shifts +0.150/+0.200 mm used only to generate sensor measurements. Nominal references are inferred from the unchanged L0/L4 measurement endpoints. Official Pede recovers +0.15000/+0.20000 mm; an independent Schur solve agrees.
- Pede preserves `entries 5` and `method inversion 3 0.001`. It reports no rank defect and zero rejected local fits. Process exit code is 0; `millepede.end` is **status 1, warnings**, because noiseless data give approximately `8.96e-17 / 94` chi2/NDF. Its printed error-rescaling recommendation was **not applied**. Nominal errors are approximately 0.0031009/0.0029006 mm, not statistically validated coverage estimates.
- Final 46 unit tests, workflow safety tests, and preservation checks passed (`regressions_final.log`): 221 baseline records and 2046 relocated files are unchanged; the electron fitter source is preserved. The final source audit also confirms preexisting reconstruction source hashes. A deliberately wrong model fingerprint was refused before any Mille output (`gate_refusal.log`). Eight installed ACTS/EICrecon files and the separate upstream checkout were verified unchanged.
- `ldd` resolves the serializer to `/work/external/install/lib/libMille2.so`. No installed dependency is modified.

The 16-ray test is **not** a new simulation campaign, CKF ensemble, RawHit
closure or material-aware performance claim. It verifies the measured-equation
sign, local elimination, selected gauge constraints and actual solver IO.
The one-track native test alone makes no alignment closure claim.

## Files and justification

| File(s) | Purpose |
|---|---|
| `localDetEICrecon/experimental/barrel/CMakeLists.txt` | Default-OFF `TELESCOPE_BUILD_MILLE_PROBE`; new isolated targets; formal Mille dependency; mathematical source fingerprint |
| `alignment/NativeMilleModel.{h,cc}` within that tree | Small deterministic native prediction/derivative helper; actual ACTS APIs; rejects unsupported transport; independent FD oracle |
| `alignment/TelescopeMille.cc` within that tree | Opt-in JANA observer, exact native associations, covariance whitening, official Mille serialization, audit report; no track fitting |
| `validation/barrel_alignment/l1_l2_global_y.json` | Explicit experiment-specific physical labels and fixed-pose scope |
| `validation/barrel_alignment/BarrelMilleDerivatives.cc` | Independent finite-difference mathematical gate |
| `validation/barrel_alignment/LegacyBarrelCrosscheck.cc` | Compile/run unchanged historical writer with explicit coordinate transform, only for comparison |
| `validation/barrel_alignment/BarrelMilleFixture.cc` | Separate noiseless 16-ray mathematical solver fixture |
| `validation/barrel_alignment/check.py` | Exact binary decode, whitening/derivative equality, local/global ranks, old-writer Schur comparison and Pede checks |
| This report and experimental README link | Flow, limitations and reproducible commands |

No official source module needed an additional copy or patch for this
milestone. No existing numerical CKF code, measurement converter, production
writer, alignment derivative, Controller or Geometry file was changed.

## Reproducible manual commands

Run from the repository root. Each example uses a new result/build directory.
The native reference audit is a local result, not Git data: regenerate it with
[BARREL_FACTORY_RECONSTRUCTION.md](BARREL_FACTORY_RECONSTRUCTION.md) if absent.
Replace its path explicitly; no historical data are overwritten.

**CHECK-ONLY** — inspect scope and existing prerequisite:

```bash
git status --short
git log -1 --oneline
cat validation/barrel_alignment/l1_l2_global_y.json
test -f result/barrel_factories_20261023_01/audit03.json
```

**WRITES OUTPUT** — fresh fixture, optional build and EventHeader input:

```bash
python3 validation/barrel_geometry/prepare.py --initialize-metadata \
  --output-dir result/barrel_mille_manual_01/fixtures
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/localDetEICrecon/experimental/barrel \
  -B /work/build/barrel_mille_manual_01 -DCMAKE_BUILD_TYPE=Release \
  -DTELESCOPE_BUILD_MILLE_PROBE=ON
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/barrel_mille_manual_01 -j2
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_factories/prepare.py \
  --output result/barrel_mille_manual_01/input.root
```

**WRITES OUTPUT** — independent mathematical gate, before loading the writer:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/build/barrel_mille_manual_01:$LD_LIBRARY_PATH
  exec /work/build/barrel_mille_manual_01/BarrelMilleDerivatives \
    /work/result/barrel_mille_manual_01/fixtures/nominal.xml \
    /work/result/barrel_factories_20261023_01/audit03.json \
    /work/result/barrel_mille_manual_01/derivatives.json'
```

**WRITES OUTPUT** — actual JANA reconstruction plus native record:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/build/barrel_mille_manual_01:/work/external/install/lib:$LD_LIBRARY_PATH
  export JANA_PLUGIN_PATH=/work/build/barrel_mille_manual_01:$JANA_PLUGIN_PATH
  test ! -e /work/result/barrel_mille_manual_01/reco.root || exit 2
  exec eicrecon -Pplugins_to_ignore=default \
    -Pplugins=log,dd4hep,evaluator,acts,algorithms_init,beam,podio,TelescopeTracking,TelescopeMille \
    -Pnthreads=1 -Pjana:nevents=1 \
    -Pdd4hep:xml_files=/work/result/barrel_mille_manual_01/fixtures/nominal.xml \
    -Pacts:MaterialMap= \
    -PTelescopeAudit:output=/work/result/barrel_mille_manual_01/reconstruction.json \
    -PTelescopeMille:output=/work/result/barrel_mille_manual_01/native.dat \
    -PTelescopeMille:report=/work/result/barrel_mille_manual_01/native.json \
    -PTelescopeMille:config=/work/validation/barrel_alignment/l1_l2_global_y.json \
    -PTelescopeMille:derivativeGate=/work/result/barrel_mille_manual_01/derivatives.json \
    -Ppodio:output_file=/work/result/barrel_mille_manual_01/reco.root \
    -Ppodio:output_collections=EventHeader,TelescopeHits,TelescopeHitAssociations,TelescopeMeasurements,TelescopeSeeds,TelescopeSeedParameters,TelescopeTrajectories,TelescopeTrackParameters,TelescopeTracks,TelescopeTrackLinks,TelescopeTrackAssociations \
    /work/result/barrel_mille_manual_01/input.root'
```

**CHECK-ONLY** — official decoder and dynamic library resolution:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/external/install/lib:$LD_LIBRARY_PATH
  /work/external/install/bin/inspectMilleBinary /work/result/barrel_mille_manual_01/native.dat
  ldd /work/build/barrel_mille_manual_01/TelescopeMille.so'
```

**WRITES OUTPUT** — unchanged legacy-writer comparison record:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  /work/build/barrel_mille_manual_01/LegacyBarrelCrosscheck \
  /work/result/barrel_mille_manual_01/native.json \
  /work/result/barrel_mille_manual_01/legacy_rotated.dat
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_alignment/check.py \
  --native result/barrel_mille_manual_01/native.dat \
  --report result/barrel_mille_manual_01/native.json \
  --legacy result/barrel_mille_manual_01/legacy_rotated.dat \
  --gate result/barrel_mille_manual_01/derivatives.json \
  --output result/barrel_mille_manual_01/record_comparison.json
```

**WRITES OUTPUT** — separate noiseless mathematical fixture and official Pede:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  /work/build/barrel_mille_manual_01/BarrelMilleFixture \
  /work/result/barrel_mille_manual_01/fixtures/nominal.xml \
  /work/result/barrel_mille_manual_01/native.json \
  /work/result/barrel_mille_manual_01/noiseless_fixture
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/external/install/lib:$LD_LIBRARY_PATH
  cd /work/result/barrel_mille_manual_01/noiseless_fixture
  exec /work/external/install/bin/pede pede.txt'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_alignment/check.py \
  --native result/barrel_mille_manual_01/native.dat \
  --report result/barrel_mille_manual_01/native.json \
  --legacy result/barrel_mille_manual_01/legacy_rotated.dat \
  --gate result/barrel_mille_manual_01/derivatives.json \
  --fixture result/barrel_mille_manual_01/noiseless_fixture \
  --output result/barrel_mille_manual_01/solver_comparison.json
```

The checks read existing inputs but write their explicitly new reports, hence
the WRITES OUTPUT label. Pede itself does not protect existing output files:
run it once in each fresh fixture directory. Keep warnings and failed outputs.
Do not feed a one-track file into the production workflow and interpret a
solver estimate as closure.

**WRITES OUTPUT** — recheck the persisted reconstruction and existing regressions:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_factories/check.py \
  --audit result/barrel_mille_manual_01/reconstruction.json \
  --root result/barrel_mille_manual_01/reco.root \
  --reference result/barrel_one_track_20261023_01/one_track_final.json \
  --output result/barrel_mille_manual_01/reconstruction_comparison.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -m unittest discover -s validation -p 'test_*.py'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 validation/check_safety.py
```

The existing unit/safety suites create isolated temporary artifacts.

**CHECK-ONLY** — historical-data preservation:

```bash
python3 validation/verify_preservation.py
```

## Remaining work before physical closure or ePIC reuse

The native interfaces are sufficient for the deterministic test; no missing
TrackState field blocks the record demonstrated here. The full supported
production alignment is intentionally not replaced. There is currently no
RawHit-based multi-event radial-beam closure through this processor, no
candidate Geometry application/reconstruction iteration, and no Controller
adapter for the new physical labels. Those are the next integration gates.

General magnetic-field tracking requires observable local parameter selection,
correct field-dependent transport/alignment response and validated covariance
elimination. Material/process noise requires a complete statistical treatment,
not shrinking smoothed-state errors. ACTS supplies useful covariance helpers,
but their availability does not establish statistical equivalence or validate
uncertainty coverage. A full-field/material method is not implemented here.

The useful future common alignment boundary is native ACTS TrackContainer /
MultiTrajectory plus calibrated measurements, source links and the official
Geometry context/SurfaceMap. Keep detector-specific labels, fixed poses and
beam seeding outside the measurement mathematics. Extend this one experimental
boundary after validation rather than creating another competing production
tracking/alignment framework.
