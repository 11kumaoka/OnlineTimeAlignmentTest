# Seven-plane barrel Geometry feasibility

The installed EICrecon provider and legacy ACTS converter **can construct and
navigate this sparse seven-plane barrel**, with explicit, physically correct
DD4hep discovery and sensor-axis metadata. No ACTS Core, installed library,
production provider, fitter, or alignment code was changed.

This is a Geometry feasibility result. It is **not** a successful radial-beam
Reconstruction or alignment test. An important measured limitation is that
Navigator does not enter this annular TrackingGeometry from an outside-world
starting point. Production integration remains deliberately unimplemented.

## Checkpoint and environment

Phase 0 preserved the preceding Blueprint removal/endcap investigation in the
separate local commit `f3e93df8793a4951146f4283b33540220f76912e`,
`Remove optional blueprint provider and diagnose legacy endcap construction`.
Parent: `020a29d81173097f2a0f03b8d08020e70eefb5a3`.
Branch: `feature/upstream-acts-geometry`. The working tree was clean immediately
after that commit. There was no push, merge, or Geometry activation. The new
barrel diagnostics and this report remain uncommitted.

Measured evidence: `result/barrel_geometry_20261023_01/`.
Final isolated build: `build/barrel_validation_20261023_01/`.
The earlier pilot build and failed fixtures remain intact in their separate
build/result paths.

The fixed `sweet_mahavira` container provides ACTS 45.3.0, EICrecon commit
`195966d41899800eaeca6fbafd63cd53735e6543`, DD4hep 1.36 and ROOT 6.38.
The ACTS source basis is `d1323a298569942d98ff46ee413031ebd604290d`,
including the already-installed patches documented in the preceding audit.
"Unmodified" here means that installed, pinned environment, not a newly built
pristine upstream release. No private endcap converter is loaded by this test.
`linkage.log`, `dynamic.log`, and `installed_final.json` record the installed
library linkage and eight unchanged installed header/library fingerprints.

## Exact physical fixture

`validation/barrel_geometry/prepare.py` writes new experimental XML files;
canonical `geometry/nominal/seven_layer_telescope.xml` is unchanged, SHA-256
`8807380ffdb277b747f052a0b2b451c87fbc4cb4ea08a3f6960f4e7b35defee4`.

The nominal fixture is the following proper rigid transformation of the actual
seven sensitive sensors, using column vectors and mm:

```text
p_barrel = Q p_original + b
Q = [ 0  0  1 ]       b = (250, 0, 0) mm
    [-1  0  0 ]
    [ 0 -1  0 ]
```

Thus the original beam direction +Z becomes +X; Global Z remains the nominal
EIC beam axis. Sensor centers are `(250 + 50*layer, 0, 0)` mm, layers 0–6.
All seven active rectangles remain 100 x 100 mm. Normal thicknesses remain
0.05 mm for SiMAPS, 3 mm for MPGD, and 0.35 mm for AC-LGAD. The sensor-local
X/Y/Z dimensions remain 100/thickness/100 mm, preserving the original
CartesianGridXZ/XY segmentation definitions and materials verbatim. The
checker compares complete readout definitions structurally.

The fixture uses the **installed `DD4hep_SiTrackerBarrel`**, not an endcap with
changed flags. Each actual layer has a Tube air envelope, one real module, and
one sensitive Box. Three logical `DD4hep_SubdetectorAssembly` compounds precede
their children: Vertex (25), Tracker (40), TOF (44). Their real children retain
system IDs 31, 100 and 92 respectively. This gives the converter's normal
ID-based radial build order without changing the detector system IDs. The
assemblies contain no artificial sensitive surface or material layer.

The barrel constructor sets the CellID `barrel` field to 0, versus 1 in the
original endcap. Other ID field layouts, layer/module/sensor IDs and segmentation
parameters are preserved. Consequently this XML is not compatible with the
production endcap-specific hardcoded CellID lookup without a future adapter.

The barrel constructor's native module axes at phi=0 are X=-Global Y,
Y=-Global Z, Z=Global X. The component uses an explicit zero position and XML
rotation `x=-pi/2, y=-pi/2, z=0`; its measured matrix, together with
`axis_definitions=zXy`, gives ACTS u=-Global Y, v=-Global Z, n=Global X.
The unusual component `length`/`thickness` attribute assignment preserves the
original sensor/readout frame; physical normal thickness is verified from the
DD4hep solid and official detector element, not inferred from an attribute name.

Air module envelopes are 100.5 x 100.5 x (normal-thickness+0.6) mm in the
constructor's module frame. Layer Tube envelopes are derived from the actual
rectangle/module corners, with positive inner radius and finite clearance.
Air already fills the canonical world; these envelopes add no fake silicon or
material surface. The checker verifies sensor containment in each module,
module containment in each Tube, and non-overlapping ACTS radial layer bounds.

Additional fixtures are explicitly separate tests:

- `translated`: all sensors move by `(0,-0.2,-0.1)` mm in Global coordinates.
- `tilted`: each sensor rotates by 5 mrad about its own center around the native
  module X axis (Global -Y). Centers and sensor dimensions stay fixed. This is
  a physical relative-orientation test, not a single rigid rotation of the
  complete telescope.

No Simulation was generated for these fixtures.

## Discovery metadata and constructor limitations

The diagnostic applies `TRACKER|BARREL` only to the three real barrel detectors,
`layer_pattern=^layer[0-6]$` to their actual layer parents, and `zXy` to the
actual sensitive DetElements. It applies no fake detector flags to assemblies,
endcaps or sensors and changes no placement during conversion.

This is an explicit **process-local DD4hep metadata adapter in a diagnostic**.
It is not a production Geometry provider. The official provider and converter
remain unchanged. XML construction alone is not claimed to be sufficient:
the measured `official none nominal` control exits 2 with
`Unable to construct tracking geometry: no tracking volume`.
The standard barrel constructor does not itself install the needed flags and
VariantParameters. A production fixture would need to persist those correct
metadata through supported initialization or a small constructor extension.
No such production extension was added here.

Early failed fixtures are retained. The first used an incorrect physical
component orientation and generated oversized radial extents, ending at
`CylinderVolumeBuilder`'s overlap check. A rotation-only XML attempt produced
an identity component placement in this environment; explicitly specifying
position and checking the complete Transform3D avoided reliance on that path.
An isolated copy of the official constructor (different factory name only,
then additional diagnostic printing) reproduced that placement observation;
it is retained under result/ and is **not** a dependency of the final fixture.
The final XML's actual matrices were verified rather than trusting assumed
Euler multiplication order. No installed constructor was edited. The precise
underlying cause of the rotation-only overload observation is not established
by this study; it is not attributed to ACTS.

The initial probe builds also exposed missing diagnostic-only includes; a later
DD4hep element audit initially used the deprecated `associatedDetectorElement()`
and found no element. It was corrected to the official ACTS-45
`surfacePlacement()` interface, and all three cases were rerun into fresh
`*_completed.json` files. Partial builds and failed/empty gate reports remain
available. An exploratory PyROOT raw-matrix inspection crashed (exit 137);
all acceptance measurements use the compiled C++ probe instead.

## Source basis and actual call path

Primary source references, pinned to the investigated versions:

- [EICrecon ActsGeometryProvider::initialize](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/ActsGeometryProvider.cc):
  equidistant phi/r/z binning, 1 mm converter envelopes, ID sorting, ordinary
  conversion, and DD4hep VolumeManager lookup when constructing SurfaceMap.
- [ACTS ConvertDD4hepDetector.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/DD4hep/src/ConvertDD4hepDetector.cpp):
  `collectSubDetectors_dd4hep`, `collectCompounds_dd4hep`,
  `collectLayers_dd4hep`, `volumeBuilder_dd4hep`. Compound barrel-only children
  avoid the paired-endcap restriction; `collectLayers` matches actual immediate
  child names against the parent's pattern.
- [DD4hepLayerBuilder::centralLayers / resolveSensitive / createSensitiveSurface](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/DD4hep/src/DD4hepLayerBuilder.cpp):
  Global surface ProtoLayer extents; Tube envelope extraction and layer creation;
  `axis_definitions` belongs to the sensitive DetElement. The problematic
  sensitive-layer special branch is not used: these are real non-sensitive
  Tube layers containing sensitive descendants.
- [LayerCreator::cylinderLayer](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/LayerCreator.cpp),
  [SurfaceArrayCreator](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/SurfaceArrayCreator.cpp):
  layer radius/thickness from ProtoLayer extents, automatic phi/z binning,
  single-key equidistant handling, and surface lookup. Equidistant phi binning
  with optimization supplies one closed full-phi bin, not full physical sensor
  coverage. The arbitrary-phi implementation accesses a second key and is not
  established as usable for a single sensor; the official provider uses
  equidistant binning.
- [CylinderLayer](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/CylinderLayer.cpp),
  [CylinderVolumeBuilder](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/CylinderVolumeBuilder.cpp):
  real cylindrical approach surfaces, positive inner/outer radii, volume
  wrapping and overlap checks. The cylinder is a navigation envelope, not a
  physical cylindrical sensitive sensor.
- [DD4hepDetectorElement](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/DD4hep/src/DD4hepDetectorElement.cpp):
  uses the real placement, nominal world transform, selected TGeo axes and
  DD4hep Volume ID; individual converted sensitive surfaces remain planes.
- [DD4hep SiTrackerBarrel constructor](https://github.com/AIDASoft/DD4hep/blob/v01-36/DDDetectors/src/SiTrackerBarrel_geo.cpp):
  Box components, genuine Tube layer hierarchy, rphi/z layouts and physical
  sensor/module/layer IDs. No source changes are required by the final fixture.

Matching source copies and hashes are retained in this study and the preceding
`upstream_acts_geometry_20261023_01` / `legacy_endcap_20261023_01` evidence.

```text
prepare.py -> independent barrel XML
BarrelGeometryProbe::main
  -> DD4hep Detector::fromXML -> installed SiTrackerBarrel constructor
  -> DD4hepVolumeManager
  -> experimentalMetadata (correct flags / discovery / sensor axes only)
  -> installed ActsGeometryProvider::initialize
     -> convertDD4hepDetector
        -> compound discovery -> DD4hepLayerBuilder::centralLayers
           -> DD4hepDetectorElement -> PlaneSurface
           -> LayerCreator / SurfaceArrayCreator -> CylinderLayer
        -> CylinderVolumeBuilder / helper -> TrackingGeometry
     -> visitSurfaces -> surfacePlacement / VolumeManager -> SurfaceMap
  -> Acts::Navigator::initialize / nextTarget / handleSurfaceReached
     (straight stepping through actual targets and boundaries)
```

There is **no call from this path to BeamTestACTSFitter**. The unchanged production
path is RawHit Reconstruction -> BeamTestACTSFitter factory/init -> local
DD4hep sensor-frame extraction -> PlaneSurface sequence -> DirectNavigator ->
Kalman fitter. No geometry from this experiment is passed to it.

## Measured acceptance gates

Final evidence is `fixtures_v2/{nominal,translated,tilted}.xml`,
`{nominal,translated,tilted}_completed.{json,log}`, and
`{nominal,translated,tilted}_completed_gates.json` under the evidence root.

| Gate | Result in all three fixtures |
|---|---|
| Seven DD4hep placements, physical bounds, readouts, containment | PASS |
| Planar sensitive surfaces; correct axes and normal thickness | PASS |
| Seven legal CylinderLayers, radial bounds and separation | PASS |
| Returned complete TrackingGeometry | PASS |
| Seven unique nonzero sensitive GeometryIdentifiers | PASS |
| Exactly seven SurfaceMap entries; actual DD4hep identifiers match | PASS |
| Real Navigator, central and off-axis +X rays | PASS: L0, L1, L2, L3, L4, L5, L6 |
| Sparse-coverage negative controls | PASS: zero sensitive hits at opposite phi or z=51.5 mm |
| Translated / tilted geometry and traversal | PASS for these specified perturbations |
| Outside-world entry from upstream | NOT SUPPORTED by the tested Navigator initialization |
| Radial-beam Reconstruction / alignment | NOT RUN / NOT ENABLED |

Maximum center disagreement is below 4e-17 mm, matrix-element disagreement below
6.2e-17, and local/global round-trip error below 2e-15 mm. The physically large
radii are intentional: sensor radii 250, 300, 350, 400, 450, 500, 550 mm ensure
positive and well-separated cylindrical envelopes for 100 mm rectangles.

Nominal ACTS layer values (mm):

| Layer | Physical center radius | Cylinder radius | Cylinder thickness |
|---|---:|---:|---:|
| L0 | 250 | 252.700822 | 7.451644 |
| L1 | 300 | 302.290874 | 6.631748 |
| L2 | 350 | 351.995812 | 6.041625 |
| L3 | 400 | 401.773445 | 5.596890 |
| L4 | 450 | 451.599928 | 5.249857 |
| L5 | 500 | 501.457107 | 7.914215 |
| L6 | 550 | 551.346453 | 5.042905 |

Cylinder thickness includes rectangular corner radial extent and air envelope
clearance; it is **not silicon/material thickness**. All actual sensitive
normal thicknesses match the original values. No material map was supplied;
all seven sensitive surfaces report no assigned ACTS surface material. This
study does not certify material/process-noise modeling or replace DD4hep
physical material by a cylindrical material sheet.

The nominal highest TrackingVolume is an annulus with r approximately
[247.975,554.867905] mm and z half-length 52 mm. A ray starting at
r_min+0.001 mm traverses seven sensitive planes in 17 Navigator targets,
including approach and boundary targets. The off-axis ray starts with
Y=20 mm, Z=15 mm and gives the same sequence. Opposite phi gives zero sensitive
hits in 10 targets, and z=51.5 mm gives zero in three targets. These controls
show that a full-phi lookup bin does not fabricate cylindrical sensitive hits.

A starting point at r_min-10 mm immediately reaches end-of-world with no target.
The rigidly transformed old gun at original z=-500 mm would be at Global
X=-250 mm, and an existing seed 10 mm before the first plane would also lie
outside the positive-side annular entry boundary. This study does not claim
those starts are supported. A future integration must explicitly solve and
validate entry/seed handling; no dummy beam pipe or detector was added to hide
that limitation. Negative-side / central-hole transport is not demonstrated.

## Implications for the maintained alignment framework

These are source-based implications and future requirements, not implemented
changes or validated statistical results:

- `localDetEICrecon/geometry/SurfacePlacements.h` assumes the endcap `barrel=1`
  CellID. It would fail before fitting the experimental barrel `barrel=0`
  geometry. Correct lookup must become explicit metadata, not a silent ID hack.
- `BeamTestACTSFitter::fitSelected` sorts by **layer ID**, not z. That sequence
  remains increasing radius here. Its Global-coordinate seed direction is
  already inferred from first/last points, but its Global-to-local reference
  direction is fixed +Z. Its local-coordinate fallback reconstructs seed
  points using `m_zmm`; its layer identification fallback uses mean Global z,
  and EDM reference placement also uses stored z. These are not valid generic
  radial-beam assumptions.
- Seed angular/bound covariance and downstream phi/theta output must remain in
  a documented physical Global frame; rotating positions alone is insufficient.
  A transformation of bound covariances needs the appropriate Jacobian.
- `TrackerHitReconstruction` explicitly stores uncertainties in sensor-local
  dimensions. The fitter has a fixed SiMAPS axis swap. Those frame semantics
  must be retained/projected consistently; treating them as a Global diagonal
  covariance after rotation would be incorrect.
- `BeamTestMilleProcessor::Process` copies Global position x/y/z and uses err.xx
  / err.yy directly. `BeamTestMilleWriter::writeTrackRecord` and its tilted
  local fits use z-zRef as the independent variable, local parameters
  (x0,y0,tx,ty), and Global translation/rotation derivatives. A +X radial beam
  has nearly constant Global z; sending those hits unchanged would invalidate
  the local straight-line model and observability assumptions.
- Current Geometry preparation/correction is ring/endcap-specific, including
  Global placement attributes. Its SO(3) composition remains mathematically
  useful but the Geometry writer and parameter-frame contract require an
  explicit adapter. No current supported alignment mode gains radial support
  from this Geometry result.
- The Python Controller verifies RawHit digests, Geometry versions, supported
  modes and explicit activation. A radial case must preserve those checks and
  same-RawHit reconstruction invariants. It cannot reuse old z-beam RawHits as
  evidence of a newly simulated physical radial run without an explicit,
  validated coordinate/readout contract.

A well-defined beam-local frame could preserve the four-parameter equations:

```text
p_beam = Q^T (p_global - b),    direction_beam = Q^T direction_global
s = p_beam.z,                 C_beam = Q^T C_global Q
translation_global = Q translation_beam
rotation_global = Q rotation_beam Q^T
pivot_global = Q pivot_beam + b
```

The covariance formula applies to an actual Global Cartesian covariance,
not directly to the current sensor-local EDM uncertainty components.
Translation and rotation-vector components transform as
`(a_x,a_y,a_z)_beam -> (a_z,-a_x,-a_y)_global`.
Existing label names such as Global X/Rz cannot silently change meaning.
SO(3) correction composition, pivots, parameter units/signs, and end-to-end
finite-difference derivatives would need independent revalidation after such
an adapter. This is a plausible limited next step, not a demonstrated drop-in
replacement and not a reason to rewrite the numerical fitter now.

## Approach comparison and recommendation

| Approach | Current evidence | Main remaining issue |
|---|---|---|
| Legacy Endcap / DiscLayer | Official complete conversion failed in preceding documented tests | Paired-endcap requirement, zero-inner radial boundaries, layer-frame mismatch |
| Real radial Barrel / CylinderLayer | Official installed conversion, closed mapping and internal Navigation pass in this study | Explicit metadata; annular-world entry; production beam-frame/CellID contracts; no material validation |
| Local PlaneSurface / DirectNavigator | Existing maintained Reconstruction/alignment regressions; unchanged here | Telescope-specific surface sequence and frame conventions; no official volume-navigation integration |

Keep the validated local path as production. Preserve this isolated official
barrel test as a Geometry feasibility milestone. If radial-beam development is
chosen later, first specify the beam-local/Global contract and solve entry with
real Geometry boundaries; then validate a minimal adapter using unchanged
numerical fitting and same-RawHit tests before any alignment inference. No
Blueprint, new production provider, fake detector, or ACTS Core modification
is justified by these results.

## Files and validation

New maintained files only:

- `validation/barrel_geometry/CMakeLists.txt`: independent diagnostic build.
- `validation/barrel_geometry/prepare.py`: exclusive new-directory fixture writer.
- `validation/barrel_geometry/BarrelGeometryProbe.cc`: installed-provider,
  placement, mapping, layer and Navigator observations.
- `validation/barrel_geometry/check.py`: independent acceptance assertions.
- `docs/BARREL_GEOMETRY_FEASIBILITY.md`: this report.

No existing maintained source was edited after the Phase-0 commit. All 234
previously fingerprinted maintained files match the preceding final source
manifest. Preservation checks passed for 46,691 historical files/links plus the
221 baseline and 2,046 relocated-file checks. The external EICrecon checkout is
unchanged. Eight installed library/header fingerprints are unchanged.

Executed: isolated CMake configure/build, all three verified Geometry probes
and gate checks, `validation/verify_preservation.py`, `validation/check_safety.py`,
and all 46 existing unit tests inside the fixed container. Unit tests report
existing SQLite ResourceWarnings but pass. A preliminary host unittest run had
one error because host NumPy is unavailable; it is not reported as passing.
No new Simulation, numerical Reconstruction, Millepede solve or statistical
campaign was run. Historical physics regressions remain protected, not
relabelled as freshly executed radial regressions.

## Independent commands

Run from the repository root. These templates use fresh names; the evidence
paths above already exist and must not be reused for writes.

**CHECK-ONLY** — existing final evidence, no Geometry activation:

```bash
for scenario in nominal translated tilted; do
  PYTHONDONTWRITEBYTECODE=1 python3 validation/barrel_geometry/check.py \
    --report result/barrel_geometry_20261023_01/${scenario}_completed.json \
    --fixture result/barrel_geometry_20261023_01/fixtures_v2/${scenario}.xml
done
PYTHONDONTWRITEBYTECODE=1 python3 validation/verify_preservation.py
git status --short
git log -1 --oneline
```

**WRITES OUTPUT** — independent fresh fixture generation and build:

```bash
python3 validation/barrel_geometry/prepare.py \
  --output-dir result/barrel_manual_01/fixtures
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/validation/barrel_geometry -B /work/build/barrel_manual_01
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/barrel_manual_01 -j2
```

**WRITES OUTPUT** — any one fixture can be tested independently (replace
`nominal` consistently with `translated` or `tilted` for the other tests):

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  /work/build/barrel_manual_01/BarrelGeometryProbe \
  /work/result/barrel_manual_01/fixtures/nominal.xml \
  /work/result/barrel_manual_01/nominal.json \
  official discovery-and-flags nominal
PYTHONDONTWRITEBYTECODE=1 python3 validation/barrel_geometry/check.py \
  --report result/barrel_manual_01/nominal.json \
  --fixture result/barrel_manual_01/fixtures/nominal.xml
```

**WRITES OUTPUT** — metadata-negative control; expected exit status **2**:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  /work/build/barrel_manual_01/BarrelGeometryProbe \
  /work/result/barrel_manual_01/fixtures/nominal.xml \
  /work/result/barrel_manual_01/no_metadata.json official none nominal
```

**WRITES OUTPUT** — tests may create temporary safety artifacts:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s validation -p 'test_*.py'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 validation/check_safety.py
```

The actual final probe commands used the same arguments with build directory
`/work/build/barrel_validation_20261023_01`, input directory
`/work/result/barrel_geometry_20261023_01/fixtures_v2`, and outputs
`/work/result/barrel_geometry_20261023_01/${scenario}_completed.json`.
Final build log: `build_final_sources.log`; final configure log:
`final_configure.log`; unit log: `unit_container.log`; preservation/safety logs:
`preservation.log`, `preservation_full.log`, `safety.log`.
