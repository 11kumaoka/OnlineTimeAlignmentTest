# One material-free track with official EICrecon/ACTS components

The isolated test reconstructs **one ACTS track candidate**, with five SiMAPS
measurements on the validated seven-plane barrel TrackingGeometry, using the
installed EICrecon CKF factory and standard ACTS measurement/calibration,
filtering and smoothing components. No replacement provider, navigator or fitter
was written. The maintained production reconstruction/alignment path is unchanged.

This is a deterministic synthetic-input integration test, not a Geant4 event,
RawHit production chain, material-aware reconstruction, efficiency measurement,
or statistical closure test.

## Preservation and source changes

The previous barrel integration milestone was reviewed against its six saved
source hashes and its three Geometry/Propagation/material acceptance reports.
Its existing 46-test result was checked. It was committed locally as:

```text
c8f18ed7cec152c229cd9d8a9a817772ac52f68f
Initialize barrel metadata through DD4hep and validate ACTS transport
```

The working tree was clean after that commit. Branch:
`feature/upstream-acts-geometry`. No push or merge occurred. This subsequent
one-track work remains uncommitted.

Only three new maintained files are needed:

- `validation/barrel_one_track/CMakeLists.txt`: separate diagnostic executable;
  reuses the preceding DD4hep metadata hook without copying it.
- `validation/barrel_one_track/BarrelOneTrack.cc`: one explicit input/conversion/
  seed/factory invocation/state-reporting flow, with acceptance checks.
- `docs/BARREL_ONE_TRACK_RECONSTRUCTION.md`: this report.

No existing maintained source was changed for this test. BeamTestACTSFitter,
RawHit reconstruction, Mille Writer, Pede integration, alignment derivatives,
SO(3) corrections, Controller, particle configurations and nominal Geometry
remain unchanged. No experimental Geometry was activated.

Evidence: `result/barrel_one_track_20261023_01/`.
Fresh build: `build/barrel_one_track_20261023_01/`.
The fixed `sweet_mahavira` Docker environment was used: ACTS 45.3.0 with its
already installed patches and EICrecon commit
`195966d41899800eaeca6fbafd63cd53735e6543`.

## Why not call the two upper-level algorithms unchanged?

The smallest adaptation was proposed before implementing the harness: keep the
installed algorithms intact, use the public native CKF factory, and prepare
only the fixture-specific measurement and seed inputs.

The installed
[TrackerMeasurementFromHits::init](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/TrackerMeasurementFromHits.cc)
unconditionally looks up `B0Tracker_Station_1_ID`. This actual telescope has no
B0 detector/constant. The test calls the installed init method after initializing
the official algorithm services and records its actual exception:
`getRefChild: Failed to find child with name: B0Tracker_Station_1_ID`.
It never calls process on that partially initialized object and adds no fake
B0 detector or constant.

That converter also normally copies the packed xx/yy input variances directly
into ACTS loc0/loc1. The telescope's readout X/Z and ACTS u/v require an explicit
permutation/sign transform. Equal SiMAPS variances can conceal an axis mistake,
so an independent anisotropic correlated covariance probe validates the transform.
This is a mathematical diagnostic only; those probe errors are not used in the
fit and do not rescale its uncertainties.

The installed
[CKFTracking::process](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/CKFTracking.cc)
reconstructs each input seed on an origin-centered PerigeeSurface, uses a pion
hypothesis there, and later extrapolates accepted tracks to the origin-centered
output perigee. For a +X-directed radial track, that input reference convention
cannot represent the required interior seed at x=249 mm. Changing only a seed's
position field cannot override those hardcoded references. The test therefore
uses the already public
[CKFTracking::makeCKFTrackingFunction](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/CKFTrackingFunction.cc),
which accepts real native ACTS bound parameters/options without those upper-level
reference conversions. This invokes the actual installed EICrecon implementation;
it does not copy or reimplement that factory.

The anonymous EDM4eic calibrator inside CKFTracking.cc is not a public reusable
class. Standard installed `ActsExamples::PassThroughCalibrator` and
`MeasurementCalibratorAdapter` provide the required calibration interface for
native measurements instead. There is no new local calibrator class.

`ACTSGeo_service`'s JANA service-locator wrapper is not instantiated in this
standalone executable. Its actual ActsGeometryProvider is initialized directly
and registered with the installed `algorithms::ActsSvc`; the installed
`algorithms::GeoSvc` supplies the real detector and CellIDPositionConverter.
No JANA input factory chain or full `eicrecon` executable workflow is claimed.
Using those official public algorithm-service interfaces avoids adding a new
service/provider solely for this one-track test.

## Small new input and coordinate/covariance contract

The newly prepared nominal XML is byte-identical to the preceding validated
barrel XML (`geometry_provenance.json`). Its seven physical sensor centers are
at x=250,300,350,400,450,500,550 mm. It uses the normal XML metadata initializer;
there is no diagnostic metadata injection.

A deterministic reference ray defines fresh pixel inputs:

```text
at x=250 mm: y=2 mm, z=-3 mm
 dy/dx = +0.003
 dz/dx = -0.002
```

For SiMAPS L0–L4 the harness:

1. Forms the actual barrel Volume ID: system=31, barrel=0, layer=0–4,
   module=1, sensor=1, wedge=0.
2. Transforms the ray point into that real DD4hep sensor frame and calls the
   installed `CartesianGridXZ` segmentation to encode its channel CellID.
3. Resolves that complete CellID through the official GeoSvc converter and
   checks the returned Volume ID against the base sensitive context.
4. Uses the converter's pixel-center position to construct a new
   `edm4eic::TrackerHit`; it does not use the unquantized ray point as a measurement.
5. Looks up the real surface in the installed provider's SurfaceMap, checks
   uniqueness and bounded on-surface consistency, and converts the pixel center
   with the official `Surface::globalToLocal` API using the same 0.1 um tolerance
   as the upper-level converter.

There is no read of old Simulation, endcap RawHits or old Reconstruction files.
The reference ray generates the input only. Seed direction and position are
computed from the first/last **quantized hit positions**, not taken from the ray.
There is no random seed: input generation is deterministic.

`cellDimensions` for this CartesianGridXZ readout returns **two readout-ordered
widths**, X and Z, not a three-coordinate XYZ vector. The harness follows the
existing EICrecon TrackerHit convention: `positionError.xx/yy` pack the readout
X/Z variances; zz is zero. Each variance is pitch^2/12, with the actual
0.034641 mm pitch, approximately 0.0001 mm^2. An initial three-coordinate
interpretation was rejected with a bounds exception and corrected; the failed
`one_track.json` and build/run logs remain preserved.

In this geometry:

```text
ACTS (u,v) = (-sensor Z, sensor X)
J = [0 -1; 1 0]
C_acts = J C_readout J^T
```

J is measured from the actual DD4hep sensor axes and ACTS surface basis, rather
than assumed when constructing the covariance. Coordinates are independently
checked in the native sensor frame. The report includes J, pixel pitches,
packed input variances, output local covariance and real IDs. The covariance
probe verifies that a nonzero readout correlation changes sign appropriately;
the actual fit uses only the pitch-derived pixel covariance.

Only the five SiMAPS X/Z readouts supply measurements. The retained MPGD and
AC-LGAD CartesianGridXY definitions in this fixture do not establish a validated
two-coordinate transverse measurement model for their thin-Y sensor frames.
They are not silently promoted to extra 2D hits. Their actual sensitive surfaces
remain in the official TrackingGeometry and Navigator.

## Official code flow

```text
new barrel XML
  -> DD4hep normal constructor + existing metadata initialization hook
  -> installed algorithms::GeoSvc / CellIDPositionConverter
  -> installed ActsGeometryProvider::initialize(empty material filename)
     -> unmodified legacy DD4hep converter -> TrackingGeometry + SurfaceMap
  -> installed algorithms::ActsSvc::init(provider)

new ray -> DD4hep segmentation CellID -> pixel-center TrackerHit
  -> fixture-only bounded coordinate conversion + X/Z covariance projection
  -> ACTS MeasurementContainer + IndexSourceLink multiset
  -> installed PassThroughCalibrator / MeasurementCalibratorAdapter
  -> ACTS TrackStateCreator + MeasurementSelector + GainMatrixUpdater
  -> installed EICrecon CKFTracking::makeCKFTrackingFunction
     -> ACTS EigenStepper + Navigator + CombinatorialKalmanFilter::findTracks
  -> ACTS smoothTrack
  -> native track/state checks and JSON output
```

The selector uses the pinned EICrecon defaults: chi2 cutoff 15 and at most ten
measurements per surface. There is one supplied measurement on each SiMAPS
surface. No alternative finder/fitter fallback is used.

The curvilinear bound seed lies at x=249 mm inside the real TrackingGeometry
and before L0. The harness explicitly checks start-volume resolution and zero
field from the official field provider. Its q/p is -1 GeV^-1 and its hypothesis
is electron. The demonstration bound-covariance diagonal is
`[1,1,0.001,0.001,0.0001,1]` in ACTS bound units. Those seed values are recorded;
they do not change production configuration. No origin extrapolation is
requested. Final positions/directions are reported on the actual smoothed
measurement surfaces.

All telescope-specific work remaining in this harness is explicit: selecting
the five known SiMAPS layers/IDs/readout; generating the fixed input ray;
projecting its X/Z readout covariance; placing the interior seed; excluding
unvalidated MPGD/AC-LGAD measurements; and checking/reporting the resulting
states. The metadata initializer is the previously validated small DD4hep hook.
JSON serialization and CMake wiring add no tracking behavior.

## Measured reconstruction result

Final evidence: `one_track_final.json` and `one_track_final.log`.

| Quantity | Result |
|---|---:|
| CKF candidates | 1 |
| Measurements | 5 two-dimensional SiMAPS measurements |
| Outliers | 0 |
| Holes | 2, exactly the MPGD and AC-LGAD surfaces without supplied measurements |
| ACTS chi2 | 8.4002752304 |
| ACTS stored nDoF | 10 |
| Smoothed measurement states | 5 |
| Maximum absolute smoothed local residual | 0.0138569193 mm = 13.8569 um |
| Official magnetic field at seed | (0,0,0) T |

The two holes are retained and checked against the real system IDs 100 and 92.
They are not suppressed, relabelled or used to claim complete seven-readout
reconstruction. All five fitted states and covariances are finite; each local
2x2 smoothed covariance is positive definite. There is one unique Volume ID
and GeometryIdentifier per supplied measurement. Smoothing succeeded.

The seed is approximately `(249,2.00623344,-3.01186175)` mm with direction
`(0.9999938501,0.0029444668,-0.0019052436)`. For example, the L0 smoothed state
is approximately `(250,2.00225020,-2.99991145)` mm, with a forward radial
unit direction. Each measurement residual and local covariance is recorded.

The residuals come from fitting quantized pixel centers; they are not forced
to zero. Stored nDoF retains ACTS's convention. A single deterministic sample
cannot establish a chi2 distribution, uncertainty calibration, momentum
resolution or efficiency. In zero field with no material, q/p is not
constrained by these position measurements; the supplied momentum must not be
presented as a measured momentum.

## Material and limitations

The material filename is explicitly empty, and the independent Geometry audit
confirms 56 distinct surfaces and five volumes have no ACTS material assignment.
There is no material map creation or implicit import of the unrelated ePIC map.
The native CKF's standard material-effect defaults need not be disabled: absent
material assignments, they do not supply physical scattering/energy loss.
DD4hep Silicon and physical thickness are unchanged and remain distinct from
ACTS material. This test is explicitly **material-free**.

This milestone does not produce a full EDM Track output stage, integrate JANA
factories, digitize a Geant4 event, validate MPGD/AC-LGAD measurements, modify
Mille/alignment/Controller processing, or demonstrate physics/statistical closure.
The full upper-level EICrecon algorithms are not claimed to have run successfully.

A future minimal upstream-facing adaptation would guard optional detector-specific
initialization in TrackerMeasurementFromHits, make the readout-to-bound covariance
contract explicit, and let the upper CKF process honor a usable seed/output
reference and particle hypothesis. Those changes are proposals, not implemented
here. The present native public factory path demonstrates the reconstruction
without changing any installed component or building a generalized abstraction.

## Validation and independent commands

Executed: isolated configure/build; successful one-track reconstruction and
ACTS smoothing; independent normal-initialization Geometry/entry/material gate
suite; 46 existing unit tests; existing safety and preservation checks.
`official_symbols.log` records dynamic references to the installed EICrecon
factory and ACTS calibration classes; `linkage.log` records library resolution.
No BeamTestReco fitter is linked as the numerical track finder for this test.
Initial compile/type and input-dimension failures are retained in separate logs.

Run from the repository root. The following fresh-name examples reproduce the
actual interfaces used; do not reuse existing output directories/files.

**WRITES OUTPUT** — new fixture and isolated build:

```bash
python3 validation/barrel_geometry/prepare.py --initialize-metadata \
  --output-dir result/barrel_one_track_manual_01/fixtures
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/validation/barrel_one_track -B /work/build/barrel_one_track_manual_01
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/barrel_one_track_manual_01 -j2
```

**WRITES OUTPUT** — one deterministic track, output file must be new:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc \
  'export LD_LIBRARY_PATH=/work/build/barrel_one_track_manual_01:$LD_LIBRARY_PATH; exec /work/build/barrel_one_track_manual_01/BarrelOneTrack /work/result/barrel_one_track_manual_01/fixtures/nominal.xml /work/result/barrel_one_track_manual_01/one_track.json'
```

**CHECK-ONLY** — completed result and preservation:

```bash
python3 -c 'import json; r=json.load(open("result/barrel_one_track_20261023_01/one_track_final.json")); assert r["passed"] and r["candidate_count"]==1; print(r["track"]); print(r["maximum_abs_residual_mm"])'
PYTHONDONTWRITEBYTECODE=1 python3 validation/barrel_geometry/check.py \
  --report result/barrel_one_track_20261023_01/geometry_regression.json \
  --fixture result/barrel_one_track_20261023_01/fixtures/nominal.xml --integration
PYTHONDONTWRITEBYTECODE=1 python3 validation/verify_preservation.py
git status --short
```

**WRITES OUTPUT** — existing tests may create temporary safety artifacts:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s validation -p 'test_*.py'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 validation/check_safety.py
```

Actual build: `/work/build/barrel_one_track_20261023_01`; actual input:
`/work/result/barrel_one_track_20261023_01/fixtures/nominal.xml`; actual final
output: `/work/result/barrel_one_track_20261023_01/one_track_final.json`.
Logs: `configure.log`, `build_final.log`, `one_track_final.log`,
`geometry_gates.log`, `unit.log`, `safety.log`, `preservation.log`.
