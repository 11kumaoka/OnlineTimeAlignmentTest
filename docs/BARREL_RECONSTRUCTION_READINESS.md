# Barrel Geometry initialization, entry and material audit

The seven-plane barrel now loads its ACTS discovery metadata through normal
DD4hep XML initialization. The installed official EICrecon provider builds the
same TrackingGeometry and SurfaceMap with the diagnostic metadata adapter
**disabled**. Actual zero-field ACTS propagation crosses all seven planes from
an interior seed before L0. Material is still missing from ACTS; this milestone
does not establish material-aware Reconstruction or alignment closure.

## Scope, checkpoint and evidence

The five preceding feasibility files were checked against their saved hashes;
all three existing Geometry gate suites passed when reread. They were committed
locally as:

```text
831dc4c75366b872c576bba16d0794eab36f3ae0
Validate sparse barrel geometry with the official ACTS converter
```

The working tree was clean immediately after that Phase-0 commit. Branch:
`feature/upstream-acts-geometry`. This milestone's subsequent changes remain
uncommitted. No push, merge, Geometry activation, Simulation campaign, numerical
track fit, Millepede solve or alignment-model change was performed.

Evidence root: `result/barrel_integration_20261023_01/`.
Fresh independent build: `build/barrel_integration_20261023_01/`.
Installed EICrecon commit: `195966d41899800eaeca6fbafd63cd53735e6543`.
ACTS: 45.3.0, base `d1323a298569942d98ff46ee413031ebd604290d` with the
previously audited installed patches. DD4hep: 1.36. Fixed Docker container:
`sweet_mahavira`. Installed ePIC: `3f1260f93e6230d24a7adffd6afcfa25c33bb8b9`.
Current-upstream ePIC scripts were initially inspected, then the material audit
was repeated against this installed commit. Current-upstream scripts are not
being substituted for the pinned environment.

## Normal metadata initialization

The fixture retains the installed `DD4hep_SiTrackerBarrel` constructor. It now
optionally includes ordinary DD4hep XML initialization plugins, enabled with
`prepare.py --initialize-metadata`:

1. `TestbenchBarrelMetadata`: a small local **DD4hep metadata initialization
   plugin**, built with its normal `.components` registration. It checks for
   real Tube layer envelopes and real sensitive descendants, sets the real
   detector's TRACKER|BARREL flags, ensures each real layer has a
   `VariantParameters` extension, and attaches `axis_definitions=zXy` to real
   sensitive descendants. It constructs no volumes, surfaces, ACTS provider,
   or material.
2. Installed `DD4hep_ParametersPlugin`: sets
   `layer_pattern: str=^layer[0-6]$` on each real detector.

The library is discovered through the isolated build directory on
`LD_LIBRARY_PATH`. There is no installation into the container or production
Plugin. XML without that library is not a self-contained new production setup;
the required build/discovery command is explicit below.

This differs from the preceding diagnostic adapter: initialization occurs as
part of `Detector::fromXML`, before calling the provider. The probe is invoked
with `official none`, so it makes no metadata edits. Its original and selected
hierarchies are identical. All seven sensor axes, detector flags and layer
extensions are already present when the provider starts.

This choice avoids copying the full standard detector constructor merely to
add metadata. ePIC's own constructor normally supplies analogous metadata
inside construction. In the pinned
[BarrelTrackerWithFrame constructor](https://github.com/eic/epic/blob/3f1260f93e6230d24a7adffd6afcfa25c33bb8b9/src/BarrelTrackerWithFrame_geo.cpp),
lines 63–64 set flags and ensure detector parameters, line 273 ensures layer
parameters, and lines 313–314 ensure sensor parameters and axes. The stock
DD4hep barrel constructor does not do those things. The local hook supplies
that metadata through DD4hep's supported XML initialization mechanism instead;
it is not a substitute ACTS provider.

The standard
[addVariantParameters plugin](https://github.com/AIDASoft/DD4hep/blob/v01-36/DDRec/src/plugins/addVariantParameters.cpp)
attaches typed key/value extensions to a named detector. It does not set the
physical detector flags or recursively initialize these sensitive descendants.
`DD4hep_DetectorTypes` is a detector-type cache/dump plugin, not a flag setter.
The local hook is limited to the missing work; layer discovery still uses the
standard parameter plugin.

An initial normal-initialization test failed at
`DD4hepLayerBuilder::centralLayers` with `Detector Element has no
VariantParameters`: registering sensor parameters alone was insufficient.
Ensuring the real Tube layers' empty parameter extensions fixed this
configuration error. The failed `normal_init.{json,log}` is retained. A
C++ vexing-parse error in the first Propagator build was also corrected; its
build log is retained. Neither issue required an ACTS change.

## Geometry acceptance

`fixtures/{nominal,translated,tilted}.xml` differs from the prior accepted
physical fixtures only in initialization plugins. Sensitive dimensions,
placements, readouts, material names, IDs and air-envelope bounds are preserved.
The canonical nominal endcap XML is unchanged. The proper rigid transform,
positive sensor radii 250–550 mm, 50 mm spacing, component-axis convention,
and explicit translated/tilted test perturbations remain as documented in
[BARREL_GEOMETRY_FEASIBILITY.md](BARREL_GEOMETRY_FEASIBILITY.md).

All three final tests pass the original Geometry checker plus the new
`--integration` checks:

| Acceptance gate | Measured result |
|---|---|
| Correct physical bounds, transforms, readouts and containment | PASS |
| Seven planar sensitive surfaces, axes and physical normal thickness | PASS |
| Seven positive, non-overlapping CylinderLayer bounds | PASS |
| Complete official TrackingGeometry | PASS |
| Seven unique sensitive GeometryIdentifiers | PASS |
| Seven correct Volume-ID SurfaceMap entries | PASS |
| Diagnostic metadata adapter disabled | PASS; hierarchy unchanged across provider call |
| Internal Navigator central/off-axis traversal and sparse-coverage misses | PASS |
| Full EigenStepper + Navigator propagation before L0 | PASS |
| Translated and tilted cases | PASS for the specified perturbations |
| ACTS material description complete | NO |
| Production Reconstruction / radial alignment / statistical closure | NOT RUN |

Final reports: `{nominal,translated,tilted}_final.json` and `.log`.
Independent acceptance outputs: `{nominal,translated,tilted}_gates.log`.
`legacy_adapter_regression.json` separately confirms the previously supported
adapter-based diagnostic still passes with the original saved fixture. The
normal-initialization acceptance does not rely on that adapter.

## Navigator entry and seed tests

This phase uses the actual installed
`Propagator<EigenStepper<>, Navigator>`, a zero ConstantBField,
`SurfaceCollector`, and `EndOfWorldReached`. Seeds use ACTS curvilinear bound
parameters, electron hypothesis and q/p=-1 GeV^-1. There are no measurements,
fit, covariance inference, or MaterialInteractor in these transport tests.
A curvilinear parameter reference is a mathematical seed surface, not a dummy
physical detector. The diagnostic retains `resolveSensitive=true`,
`resolveMaterial=false`, `resolvePassive=false`; the official CKF separately uses
`resolveMaterial=true`. With the measured empty material inventory these tests
do not exercise material navigation or interactions.

Nominal results (all seven hits means L0, L1, L2, L3, L4, L5, L6):

| Start / transport | Result | Path length mm |
|---|---|---:|
| Inside annulus, x=247.976 | Seven hits | 306.891905 |
| Before first sensitive plane, x=249 | Seven hits | 305.867905 |
| Inside central hole, x=240 | Initialization fails: `No start volume could be resolved` | — |
| Rigidly transformed old gun, x=-250, direction +X | Seven hits | 804.867905 |
| VoidNavigator to actual positive inner boundary, x=240 → 247.975 | Reaches actual target boundary | 7.975 |
| Resume normal Navigator at that boundary | Seven hits | 306.892905 |
| Resume with 0.001 mm interior seed margin | Seven hits | 306.891905 |

The same sequence succeeds for the translated and tilted fixtures. The
boundary-target stage uses the **existing inner world Cylinder boundary**;
no detector, material, volume or geometry bound is inserted. This deliberately
material-free entry transport does not certify transport/material modeling
through arbitrary uninstrumented upstream regions.

Independent bounded `Surface::intersect` calls from x=240 find all seven
sensitive planes, at nominal distances 10, 60, 110, 160, 210, 260, 310 mm.
A z=70 mm ray misses every plane. Thus a surface being intersectable does not
imply that volume-navigation initialization is valid at the starting point.

The expected constraint is in
[Navigator::initialize](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Navigation/Navigator.cpp):
when the seed has no associated real layer/start volume, Gen1 navigation calls
`TrackingGeometry::lowestTrackingVolume`. A null result returns
`NavigatorError::NoStartVolume`. The installed `Propagator.ipp::initialize`
propagates that failure. The prior manual diagnostic correctly recorded failed
initialization outside the annulus; it was not a full transport test.
The new actual Propagator test confirms the failure at x=240. This is an
expected starting-volume constraint for this annular TrackingGeometry, not
evidence that it should be filled with fictitious central detector material.

Important clarification of the earlier report's gun implication: after the
rigid coordinate transformation, x=-250 has radius 250 mm and **is inside the
negative-azimuth portion of the annulus**, rather than in its central hole.
The full Propagator and an added manual Navigator ray both reach the seven
positive-X planes from there in these tests. The previous study did not test
that trajectory. This is transport evidence for this zero-field, unassigned-
material fixture; it is not a validated material-aware particle-gun workflow.

Recommended future Reconstruction convention: initialize a seed in known air
inside a real TrackingVolume, before the first measurement, e.g. x=249 mm for
this unchanged fixture, with explicit +X beam direction. Check start-volume
resolution, first-plane ordering, and normal/tangential bounds. The current
production rule "10 mm before the first hit" would produce x=240 and is not
a valid generic radial convention. A measured track seed must supply its own
state/covariance; using truth or arbitrary seed changes to improve fit quality
is not implied. An explicit exterior-to-real-boundary stage is technically
possible, as tested, but its state/covariance/material handling requires
validation before production use. Exact-boundary starts passed here; the
interior margin is an optional numerical convention, not changed Geometry.

## Material inventory: actual missing assignments

Full inventories are retained without inventing properties:

- `material_surfaces.csv`: all 56 distinct surface objects, actual IDs, bounds,
  assignment status, roles and owners.
- `material_layers.csv`: each real detector layer's sensitive and approach
  identifiers, DD4hep material and physical thickness.
- `material_volumes.json`: all five TrackingVolumes and assignment status.
- Each final JSON includes the same underlying `material_inventory` observations.

| Layer | DD4hep sensitive material | Physical normal thickness mm | ACTS sensitive | ACTS approaches | ACTS layer representation |
|---|---|---:|---|---|---|
| L0 | Silicon | 0.05 | Missing | Both missing | Missing |
| L1 | Silicon | 0.05 | Missing | Both missing | Missing |
| L2 | Silicon | 0.05 | Missing | Both missing | Missing |
| L3 | Silicon | 0.05 | Missing | Both missing | Missing |
| L4 | Silicon | 0.05 | Missing | Both missing | Missing |
| L5 (MPGD model) | Silicon | 3.0 | Missing | Both missing | Missing |
| L6 (AC-LGAD model) | Silicon | 0.35 | Missing | Both missing | Missing |

These are the existing simulated material models, not newly inferred realistic
MPGD gas/foil or AC-LGAD construction stacks. No composition or thickness was
changed to make a material description appear complete.

There are 7 sensitive roles, 14 approach roles, 17 layer-representation roles
(including ten navigation layers), and 20 volume-boundary roles. Two boundary
objects have shared roles, giving 58 role references on 56 distinct surfaces.
**None has surface material.** All five volume materials are also null:
Vertex::Barrel, Tracker::Barrel, TOF::Barrel and the two enclosing containers.
Absence on an air-only navigation boundary is not itself a defect; absence of
all sensor/support material means this is not a physically complete tracking
material model.

The CylinderLayer thickness includes the radial envelope of rectangular
corners and air clearance. It must never be interpreted as that many mm of
Silicon. DD4hep/Geant4 material attached to actual solids is distinct from
`ISurfaceMaterial`/`IVolumeMaterial` used by ACTS transport.

## Official EICrecon / ePIC material handling

Source references use installed commits; matching source/header copies are
under the evidence root's `source/` directory.

1. [ACTSGeo_service::actsGeoProvider](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/services/geometry/acts/ACTSGeo_service.cc)
   reads the DD4hep `material-map` constant, or defaults to
   `calibrations/materials-map.cbor`, and exposes `acts:MaterialMap`. It passes
   that filename into the provider. This audit directly calls the official
   provider with an explicit empty filename; it does not claim a complete JANA
   service/factory execution. Future integration must explicitly select a valid
   telescope map, rather than accidentally loading an unrelated ePIC default.
2. [ActsGeometryProvider::initialize and EpicJsonMaterialDecorator](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/ActsGeometryProvider.cc)
   create a JSON/CBOR decorator only for a nonempty material filename and pass
   it into DD4hep conversion/Geometry closure. Its wrapper logs assignments and
   checks whether visited (volume,layer) pairs receive any **approach** material;
   it does not require every sensitive surface to have a separate assignment.
   Critical missing-approach logs are diagnostics, not proof of complete physics.
3. [JsonMaterialDecorator](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/Json/src/JsonMaterialDecorator.cpp)
   reads JSON or CBOR material maps and assigns surface/volume material by
   GeometryIdentifier. Default clearing removes old surface/volume material
   before lookup. The mechanism is not restricted to sensitive surfaces:
   configured sensitive, approach, boundary or layer surfaces can receive
   material, and volumes use the separate volume map. Validate the actual
   closed identifiers and map coverage rather than assuming a successful file
   read proves a valid correspondence.
4. The pinned [ePIC material configuration helper](https://github.com/eic/epic/blob/3f1260f93e6230d24a7adffd6afcfa25c33bb8b9/scripts/material_map/materialmap_config.py)
   selects layer approaches and the real ePIC beam-pipe surface for mapping.
   Its [mapping instructions](https://github.com/eic/epic/blob/3f1260f93e6230d24a7adffd6afcfa25c33bb8b9/scripts/material_map/readme.md)
   describe entrance/exit-layer mapping, Geant4 geantino recording, material
   mapping and comparison plots. Sensitive measurement planes may legitimately
   have no individual slab if material is represented on the selected approach
   surfaces. Assigning both without accounting for splitting would double count.
   The installed definitions_craterlake.xml uses `epic_FileLoader` to obtain
   `calibrations/materials-map.cbor`. Existing maps were read only, never altered.
5. [CKFTrackingFunction](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/CKFTrackingFunction.cc)
   uses EigenStepper + Navigator, with `resolveMaterial=true`,
   `resolveSensitive=true`, `resolvePassive=false`.
   [CKFTracking::process](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/CKFTracking.cc)
   constructs standard CKF options without disabling their default multiple
   scattering and energy loss. Installed `CombinatorialKalmanFilter.hpp` has
   both enabled and calls pointwise pre/post material interactions, including
   passive material states. Its explicit extrapolator also has
   `ActorList<MaterialInteractor,EndOfWorldReached>`.
   Installed `MaterialInteractor.hpp` defaults to multipleScattering=true,
   energyLoss=true, recordInteractions=false and implements surface/volume
   interaction handling. A flag being enabled does not create material where
   assignments are null, and an actor used in explicit extrapolation is not
   evidence that every CKF transport step uses that same actor.
6. The barrel probe's empty material-file argument leaves the JSON decorator
   absent. The fixture has no `layer_material`/`boundary_material` mapping
   metadata, and sensor conversion passes a null surface-material argument.
   Thus DD4hep Silicon/physical thickness is not automatically an ACTS material
   slab. This explains the measured null inventory. No new material or material
   interactions were silently enabled by the metadata initializer.

The generic material-aware mechanisms do not establish an adequate electron
uncertainty model or reproduce full Geant4 electron interactions by themselves.
No such statistical/physics claim is made here.

## Establishing a valid telescope material description

Future prerequisites, not executed in this milestone:

1. Confirm the intended physical component/support stack and material definitions,
   including which current simplified MPGD/AC-LGAD materials are appropriate.
   Keep the chosen DD4hep Geometry version immutable and record its hash.
2. Choose material-carrying surfaces and granularity explicitly. A full cylindrical
   navigation envelope must not become a uniformly Silicon-filled cylinder.
   Sparse phi coverage, local incidence, corners, support structures and
   material-free regions require adequate binning and directional validation.
3. Record material with geantinos in that actual Geometry; export the corresponding
   ACTS Geometry/closed IDs and mapping configuration using the same converter,
   flags, ordering, axes and software versions. Map onto the chosen surfaces or
   volumes, avoiding duplicate sensitive/approach assignments.
4. Validate independent ray samples: integrated X/X0 and interaction-length budget,
   crossing positions, angular dependence, sparse-phi misses, and upstream/downstream
   accounting. Compare mapped propagation against Geant4 recording and inspect
   discrepancies and empty bins before using it for a fit.
5. Bind the validated map, Geometry hash, software/configuration hashes and coverage
   report into the future immutable Geometry-version provenance. Only then test
   material-aware Reconstruction, pulls and closure with unchanged uncertainties.

The pinned ePIC `run_material_map_validation.sh` describes this workflow but
fetches ACTS v44.4.0 helper scripts and applies patches. Current-upstream ePIC
uses a different helper version. **Neither script was run or installed here.**
A future telescope campaign must use compatible pinned ACTS-45.3 tooling in an
isolated workspace, and its own physical Geometry and output paths; copying
those ePIC helper commands verbatim is not a validated recipe for this fixture.

When alignment changes Geometry, matching IDs alone do not make an old map
valid. The pinned ePIC instructions require updating material maps for Geometry
or thickness changes. A local material slab rigidly attached to a sensor might
be reusable under an explicitly validated frame transform, but binned cylindrical
approach maps can depend on radius, phi/z support, orientation and redistributed
material. Sensor shifts/rotations may change those supports or ID numbering.
Rebuild/remap or demonstrate a validated transformed-map approximation, validate
integrated budgets and crossings again, and retain separate map provenance for
each Geometry candidate. Never use an unchanged map simply because it loads,
move material twice, or activate a candidate automatically.

## Next connection to the existing fitter

Do not switch production from this diagnostic alone. Minimal next gates are:

- Put the normal XML metadata library and explicit material-map policy into a
  reviewed experimental Reconstruction case, without changing installed services.
- Replace endcap-specific Volume-ID lookup with explicit real DD4hep IDs, then
  resolve SourceLinks/measurements through the official SurfaceMap and closed IDs.
- Specify beam-local versus Global positions, directions, covariance projections,
  alignment labels and SO(3) pivots. Preserve sensor-local RawHit/RecHit semantics
  and same-RawHit checks; do not silently reinterpret Global X/Rz labels.
- Validate the interior, pre-L0 seed convention and covariance transport using
  measured hits. Separately test using official Geometry in the numerical fitter;
  a Geometry-only Propagator is not that integration test.
- Establish material coverage before claiming material-aware physics performance.
  Keep existing production fitter, Mille Writer, supported alignment modes and
  Controller activation gates unchanged until their explicit regression gates pass.

## Changes and executed checks

Modified: `validation/barrel_geometry/{CMakeLists.txt,prepare.py,
BarrelGeometryProbe.cc,check.py}`. Added:
`validation/barrel_geometry/BarrelMetadata.cc` and this report.
The numerical fitter, RawHit processing, Mille/Pede integration, SO(3) corrections,
Controller, nominal Geometry, particle settings and installed libraries were not
edited. The previous milestone's report remains a historical record.

Executed successfully: fresh isolated CMake configure/build; three normal-XML
Geometry/Propagation/material inventory suites; old-adapter Geometry regression;
46 existing unit tests in the fixed Docker environment; existing safety and
preservation checks. Eight previously fingerprinted installed headers/libraries
match. Historical data/source preservation is independently checked; old physics
closure outputs were preserved, not represented as newly run material-aware
regressions. No production BeamTestReco rebuild was needed for these separately
built validation-only targets, and none is claimed.

## Independent commands

Run from the repository root. Existing evidence paths must not be reused for
writes. The fresh-name examples below use the exact interfaces tested above.

**CHECK-ONLY** — existing completed evidence:

```bash
for scenario in nominal translated tilted; do
  PYTHONDONTWRITEBYTECODE=1 python3 validation/barrel_geometry/check.py \
    --report result/barrel_integration_20261023_01/${scenario}_final.json \
    --fixture result/barrel_integration_20261023_01/fixtures/${scenario}.xml \
    --integration
done
PYTHONDONTWRITEBYTECODE=1 python3 validation/verify_preservation.py
git status --short
```

**WRITES OUTPUT** — normal-initialization fixture preparation and separate build:

```bash
python3 validation/barrel_geometry/prepare.py --initialize-metadata \
  --output-dir result/barrel_readiness_manual_01/fixtures
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/validation/barrel_geometry -B /work/build/barrel_readiness_manual_01
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/barrel_readiness_manual_01 -j2
```

**WRITES OUTPUT** — independently run any one fixture; replace `nominal`
consistently with `translated` or `tilted` for the other cases:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc \
  'export LD_LIBRARY_PATH=/work/build/barrel_readiness_manual_01:$LD_LIBRARY_PATH; exec /work/build/barrel_readiness_manual_01/BarrelGeometryProbe /work/result/barrel_readiness_manual_01/fixtures/nominal.xml /work/result/barrel_readiness_manual_01/nominal.json official none nominal'
PYTHONDONTWRITEBYTECODE=1 python3 validation/barrel_geometry/check.py \
  --report result/barrel_readiness_manual_01/nominal.json \
  --fixture result/barrel_readiness_manual_01/fixtures/nominal.xml --integration
```

The probe's `propagation`, `entry_transport`, `sensitive_intersections` and
`material_inventory` sections are separate observations. This one command
reproduces the transport distinctions and complete material inventory; the
CSV files are convenience exports of that inventory, not additional physics.
To manually inspect just the material result, use **CHECK-ONLY**:

```bash
python3 -c 'import json; r=json.load(open("result/barrel_integration_20261023_01/nominal_final.json")); print(json.dumps(r["material_inventory"],indent=2))'
```

**WRITES OUTPUT** — tests can create temporary safety artifacts:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s validation -p 'test_*.py'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 validation/check_safety.py
```

Actual executed build paths were `/work/build/barrel_integration_20261023_01`;
actual probe inputs were `/work/result/barrel_integration_20261023_01/fixtures/`;
actual final outputs were `${scenario}_final.{json,log}` in that result root.
Configure/build logs: `configure.log`, `build_final.log`. Regression and safety
logs: `unit.log`, `safety.log`, `preservation.log`, `legacy_adapter_gates.log`.
The existing successful and failed outputs were not overwritten.
