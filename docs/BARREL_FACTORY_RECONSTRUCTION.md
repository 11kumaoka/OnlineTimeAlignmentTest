# Source-based EICrecon telescope reconstruction

## Status and scope

The experimental `TelescopeTracking` JANA plugin now executes the actual
EICrecon module sequence through EDM Track conversion. This replaces neither
the validated production BeamTestReco/Alignment path nor its scientific results.
The earlier standalone CKF executable is retained as a comparison benchmark.
No replacement Geometry Provider, navigator, fitter, or event-processing
framework was introduced.

The baseline is EICrecon `195966d41899800eaeca6fbafd63cd53735e6543`, installed
with ACTS 45.3.0 in the existing fixed Docker environment. Local adaptations
live entirely in `localDetEICrecon/experimental/barrel/`. They are built
independently of production. The preceding three-file standalone milestone
was reviewed and committed locally as `281881957849c5a1a3fe6c946a435afc18cf51b3`
(`Demonstrate one barrel track with the installed EICrecon CKF`). New work
in this report has not been committed, pushed, merged or activated.

This test is **synthetic, zero-field and material-free**. It consumes no old
endcap RawHits and no Simulation Truth. It does not demonstrate Digitization,
RawHit Reconstruction, alignment closure, momentum resolution, or a validated
uncertainty/material model. MPGD and AC-LGAD remain unmeasured surfaces, giving
two expected holes. The XY covariance control below is an interface test,
not validation of their physical readout models.

## Actual processing flow and contracts

The structure follows pinned `src/global/tracking/tracking.cc`: register
`JOmniFactoryGeneratorT` instances, request typed collections, and let JANA
resolve dependencies. The configured PODIO output and audit processor request
the resulting collections; the audit processor does not perform fitting.

```text
Installed eicrecon / JEventSourcePODIO (one EventHeader)
  DD4hep_service -> nominal barrel XML / installed DD4hep barrel constructor
  ACTSGeo_service -> ActsGeometryProvider -> convertDD4hepDetector
    -> real TrackingGeometry / VolumeID-keyed SurfaceMap / field contexts
  AlgorithmsInit_service -> algorithms::GeoSvc and ActsSvc
  SyntheticTrackerHits_factory                 [telescope test input]
    -> TrackerHitCollection + genuinely empty MCRecoTrackerHitAssociationCollection
  TrackerMeasurementFromHits_factory -> TrackerMeasurementFromHits::process
    -> Measurement2DCollection                  [adapted official files]
  TelescopeSeed_factory -> TelescopeSeed::process
    -> TrackSeedCollection + TrackParametersCollection
  CKFTracking_factory -> CKFTracking::process    [adapted official files]
    -> installed CKFTracking::makeCKFTrackingFunction
      -> ACTS EigenStepper / Navigator / CombinatorialKalmanFilter
    -> official measurement-source-link calibrator / GainMatrixUpdater
    -> ACTS smoothTrack
    -> ACTS extrapolateTrackToReferenceSurface (seed reference)
    -> ConstVectorMultiTrajectory + ConstVectorTrackContainer
  Installed ActsToTracks_factory -> installed ActsToTracks::process
    -> Trajectory / TrackParameters / Track / empty MC links and associations
  Installed JEventProcessorPODIO -> persisted event ROOT
  FactoryAudit -> independent collection/state assertions and JSON
```

Factory registration is in `TelescopeTracking.cc`. The ordinary official
flow differs only in its detector hit producers/collector, helix seeder and
unadapted measurement/CKF wrappers; its native tracking and conversion stages
are the components used here.

| Factory prefix | Inputs | Outputs |
|---|---|---|
| TelescopeSyntheticHits | No event-data input; official Geometry service | `TelescopeHits`, `TelescopeHitAssociations` |
| TelescopeMeasurements | `TelescopeHits` | `TelescopeMeasurements` |
| TelescopeSeeds | `TelescopeHits` | `TelescopeSeeds`, `TelescopeSeedParameters` |
| TelescopeCKF | `TelescopeSeeds`, `TelescopeMeasurements` | `TelescopeActsStates`, `TelescopeActsTracks` |
| TelescopeTracks | Measurements, Seeds, native States, native Tracks, HitAssociations | `TelescopeTrajectories`, `TelescopeTrackParameters`, `TelescopeTracks`, `TelescopeTrackLinks`, `TelescopeTrackAssociations` |

Each PODIO input/output uses the same EDM4eic collection type as its official
counterpart. The CKF factory's native ACTS output types and dynamic `seed`
column are unchanged. The standard ActsToTracks factory consumes those
containers directly. TrackSeed references its separate TrackParameters object;
Track references its Trajectory and Measurement2D objects. These relationships
are checked again after reading the output ROOT file.

## Source comparison

Paths in the first column are relative to pinned upstream `src/`; local paths
are relative to `localDetEICrecon/experimental/barrel/`.

| Official source | Local source | Why changed | Exact behavioral difference | Replacement path for ePIC |
|---|---|---|---|---|
| `algorithms/tracking/TrackerMeasurementFromHits.{h,cc}` | Same paths | Optional B0; telescope X/Z packing | Check actual B0 constant presence before its special tolerance; fail explicitly for missing Volume context; for SiMAPS system 31 with CartesianGridXZ project native X/Z covariance into actual ACTS u/v; other XY/UV behavior retained | Use upstream once optional detector handling and explicit readout-to-bound covariance contract are supported |
| `factories/tracking/TrackerMeasurementFromHits_factory.h` | Same path | Isolated local copy | Namespace and algorithm include/type only; collection types and services unchanged | Replace factory type with official type when algorithm is compatible |
| `algorithms/tracking/CKFTracking.{h,cc}` | Same paths | Seed reference and particle assumptions | Honor TrackSeed.perigee; extrapolate each fitted track to that seed's reference; selectable electron hypothesis with upstream pion default; alias installed CKF function interface and call its actual factory; calibration, selection, filtering, smoothing and output sequence retained | Replace with official wrapper when it honors seed reference and configurable particle hypothesis |
| `algorithms/tracking/CKFTrackingConfig.h` | Same path | Explicit particle choice | Add `electronHypothesis=false`; experimental registration explicitly sets true | Match upstream particle configuration if adopted |
| `factories/tracking/CKFTracking_factory.h` | Same path | Expose above choice | Add `ElectronHypothesis` ParameterRef; namespace/include/type changes; identical native input/output contracts | Replace with official factory when wrapper is compatible |
| `extensions/edm4eic/EDM4eicToActs.h` | Same path | Header absent from installation | **No content changes**; exact pinned unit/index conversion helper | Use installed header once packaged |
| `algorithms/tracking/TrackSeeding.{h,cc}`, factory and `OrthogonalTrackSeedingConfig.h` | `algorithms/TelescopeSeed.h`, `factories/TelescopeSeed_factory.h` | Official algorithm fundamentally unsuitable for zero-field beam seed | Minimal first/last-hit straight direction and known beam q/p prior; retain TrackerHit input and TrackSeed/TrackParameters outputs | Replace with official seeder for a suitable field/beam topology; no architectural conversion needed |

All copied algorithm/config/factory symbols are scoped to
`eicrecon::telescope`; they do not replace installed `eicrecon` symbols.
The unchanged helper retains its original internal-linkage constant.
Applicable upstream copyright headers, `LICENSE.LGPL3`, and `NOTICE.md` are
preserved. `provenance.json` records the revision, original hashes, all reviewed
sources (including services/provider/seeder/ActsToTracks), and direct reuse.
`upstream_diffs/` records per-file unified diffs. Reproduce them read-only:

```bash
python3 validation/barrel_factories/upstream_diff.py \
  --source /path/to/EICrecon \
  --output result/barrel_source_diff_manual_01
```

This reads pinned Git objects, not the checkout's working files, and verifies
upstream content hashes. No checkout modifications or network access occur.
The helper's diff is empty because it is copied unchanged.

### Direct reuse and remaining telescope code

DD4hep_service, ACTSGeo_service, AlgorithmsInit_service, ActsGeometryProvider,
its SurfaceMap and TrackingGeometry construction, CKFTrackingFunction.cc's
installed implementation, ACTS tracking/smoothing/extrapolation,
ActsToTracks.{h,cc}, its factory, JANA and PODIO IO are reused unchanged.
ActsToTracks is not copied.

The pinned ActsToTracks factory requires a hit-association collection, and its
algorithm dereferences that collection while building optional MC matches.
The synthetic-hit factory publishes an actually empty collection because
there are no simulated/raw hits or MC matches. No association objects or
MCParticles are fabricated. Output MC associations/links are also empty.
Real data can similarly have no MC associations; a future missing-collection
interface should be fixed upstream rather than inventing MC relationships.

The official TrackSeeding implementation fits an XY circle, estimates
`pt = R * bFieldInZ`, then `qOverP = charge / p`, and sets an origin perigee.
A straight zero-field trajectory cannot supply this curvature-derived
momentum. TelescopeSeed is explicitly not a momentum estimator: it derives
direction from the first/last pixel hits and uses the existing electron beam
prior q/p = -1 /GeV. It places the reference at x=249 mm, inside the real
annular TrackingGeometry and immediately before L0. Its covariance diagonal
is the previous benchmark's `[1,1,1e-3,1e-3,1e-4,1]` in the standard bound/EDM
ordering. The particle choice is made explicitly by the experimental plugin.
When seed.perigee is zero and ElectronHypothesis is false, the adapted CKF
reference/hypothesis expressions reduce to the upstream assumptions; a full
ePIC collision reconstruction was not run here.

Remaining unique code is the deterministic synthetic input factory, this
small seed producer/factory, the experimental registration, and the
validation-only FactoryAudit. The previously validated BarrelMetadata XML
initialization hook is compiled unchanged. The system-31 CartesianGridXZ
branch is the sole telescope-specific measurement transform. No generic
adapter hierarchy or alternative tracking implementation is added.

## Validation results

Actual outputs: `result/barrel_factories_20261023_01/`.
Actual isolated build: `build/barrel_factories_20261023_01/`.

| Check | Result |
|---|---|
| Isolated CMake build | Passed; `build08.log` is the final build |
| Real EICrecon/JANA event processing | One completed event; `reco03.log` |
| Native CKF candidates / measurements / outliers / holes | 1 / 5 / 0 / 2 |
| CKF chi2 / ACTS stored NDF | 8.400275230407715 / 10 |
| EDM Track chi2 / NDF | 8.400276184082031 / 10 (trajectory accumulation/float representation) |
| Electron PDG magnitude / charge | 11 / -1 |
| Expected hole geometry IDs | 360288107628593500 (AC-LGAD), 288230513590665572 (MPGD) |
| Maximum absolute smoothed local residual | Approximately 0.0138569193 mm |
| Native chi2 difference from standalone | 0 |
| Maximum smoothed position difference from standalone | 5.48e-12 mm |
| CellID → DD4hep VolumeID → official ACTS Surface | All five checked |
| Bound positions/covariances and smoothed states | Checked against independent geometry and preserved standalone reference |
| Unequal X/Z covariance transformation | Passed actual adapted converter control |
| Normal XY covariance branch | Passed actual unchanged-branch control |
| Seed reference / field | Inside TrackingGeometry; zero field |
| ROOT read-back / EDM links / empty MC associations | Passed |
| Independent Geometry/navigation/material inventory | Passed, `geometry_check.log`; 56 surfaces, five volumes, no assigned ACTS material |
| Existing unit regressions | 46 tests passed, `unit_tests.log` |
| Existing safety / preservation checks | Passed, `safety.log`, `preservation_final.log`; 221 baseline records and 2046 relocated files unchanged |
| Installed environment / separate upstream checkout | Eight audited installed headers/libraries unchanged; external checkout HEAD, status and modified-file hash unchanged |

The deterministic ray and quantized CellIDs are identical to the standalone
benchmark. Fit errors remain pitch/sqrt(12), with no uncertainty rescaling.
The seed passes through the standard float-valued EDM contract and uses a
PerigeeSurface rather than the standalone curvilinear reference; numerical
comparisons allow explicit small representation tolerances. The measured
chi2 difference is zero. The output Track Cartesian position/momentum
covariance is zero-filled by the **unchanged official ActsToTracks** code;
its TrackParameters covariance and native smoothed covariances are the
available fitted covariance products. Do not interpret that zero-filled
Cartesian covariance as a physical uncertainty estimate.

No B0 or OuterMPGD UV detector was added. Their full ePIC-specific branches
were not exercised; B0-present tolerance and UV conversion remain copied
upstream code. Successful geometry/derivative validation from earlier
milestones is not statistical validation of this material-free fit.

Initial build failures (modern PODIO compile definition, omitted upstream
header, header shadowing, and audit container ownership) are retained in
`build.log` and `build02.log` through `build05.log`. First successful outputs
and intermediate audit revisions are retained separately. No historical
outputs were reused as destinations.

## Independent manual commands

Run from the repository root; choose **new** result/build names every time.
Use the existing fixed Docker container. None of these commands installs
libraries or activates Geometry.

```bash
python3 validation/barrel_geometry/prepare.py --initialize-metadata \
  --output-dir result/barrel_factory_manual_01/fixtures
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/localDetEICrecon/experimental/barrel \
  -B /work/build/barrel_factory_manual_01 -DCMAKE_BUILD_TYPE=Release
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/barrel_factory_manual_01 -j2
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_factories/prepare.py \
  --output result/barrel_factory_manual_01/input.root
```

Actual standard event processing (the explicit output collection list prevents
requests for unrelated ePIC defaults):

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/build/barrel_factory_manual_01:$LD_LIBRARY_PATH
  export JANA_PLUGIN_PATH=/work/build/barrel_factory_manual_01:$JANA_PLUGIN_PATH
  test ! -e /work/result/barrel_factory_manual_01/reco.root || exit 2
  exec eicrecon -Pplugins_to_ignore=default \
    -Pplugins=log,dd4hep,evaluator,acts,algorithms_init,beam,podio,TelescopeTracking \
    -Pnthreads=1 -Pjana:nevents=1 \
    -Pdd4hep:xml_files=/work/result/barrel_factory_manual_01/fixtures/nominal.xml \
    -Pacts:MaterialMap= \
    -PTelescopeAudit:output=/work/result/barrel_factory_manual_01/audit.json \
    -Ppodio:output_file=/work/result/barrel_factory_manual_01/reco.root \
    -Ppodio:output_collections=EventHeader,TelescopeHits,TelescopeHitAssociations,TelescopeMeasurements,TelescopeSeeds,TelescopeSeedParameters,TelescopeTrajectories,TelescopeTrackParameters,TelescopeTracks,TelescopeTrackLinks,TelescopeTrackAssociations \
    /work/result/barrel_factory_manual_01/input.root'
```

Read-back and comparison against a preserved benchmark (or a fresh standalone
run made with the commands in BARREL_ONE_TRACK_RECONSTRUCTION.md):

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_factories/check.py \
  --audit result/barrel_factory_manual_01/audit.json \
  --root result/barrel_factory_manual_01/reco.root \
  --reference result/barrel_one_track_20261023_01/one_track_final.json \
  --output result/barrel_factory_manual_01/comparison.json
```

Independent Geometry-only validation uses the existing probe (build it using
BARREL_RECONSTRUCTION_READINESS.md if unavailable):

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/build/barrel_factory_manual_01:$LD_LIBRARY_PATH
  exec /work/build/barrel_integration_20261023_01/BarrelGeometryProbe \
    /work/result/barrel_factory_manual_01/fixtures/nominal.xml \
    /work/result/barrel_factory_manual_01/geometry.json official none nominal'
python3 validation/barrel_geometry/check.py --integration \
  --report result/barrel_factory_manual_01/geometry.json \
  --fixture result/barrel_factory_manual_01/fixtures/nominal.xml
```

Existing regressions, independently runnable:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -m unittest discover -s validation -p 'test_*.py'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 validation/check_safety.py
python3 validation/verify_preservation.py
```

The result files and standalone reference JSON are local artifacts, not Git
source dependencies. A clean clone can regenerate the reference using its
maintained standalone source and fresh paths. ROOT/PODIO read-back requires
the fixed container. Do not set PYTHONPATH to an incompatible host Python.

## Future alignment attachment and limits

The appropriate native alignment inputs are `TelescopeActsTracks` and
`TelescopeActsStates`, together with Measurement2D source-link indices,
`TelescopeMeasurements` → TrackerHit CellIDs and the **same official provider's**
SurfaceMap/Geometry context. The smoothed state contains the bound coordinates,
direction and covariance at each real detector surface; hole/outlier flags
must be retained. The EDM Track/Trajectory products are useful for persisted
quality summaries and relation traversal; they do not serialize the full
native per-surface fitted state. The perigee Track alone is insufficient for
surface-local alignment derivatives.

No attachment has been implemented. The production Mille Writer, derivatives,
SO(3) corrections, Controller, protected data and existing alignment results
remain unchanged. A physical radial-beam simulation, validated MPGD/AC-LGAD
measurement contracts, material treatment and scientific statistical studies
remain separate milestones. The current result establishes source and factory
compatibility through one material-free reconstructed track, not alignment or
physics equivalence of the two reconstruction paths.
