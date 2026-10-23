> Historical audit: retained results and commands describe their recorded source/build state. The Blueprint reconstruction implementation was later removed; current status and commands are in [LEGACY_ENDCAP_SIMPLIFICATION.md](LEGACY_ENDCAP_SIMPLIFICATION.md). Use preserved builds or the recorded commit when reproducing historical Blueprint commands.

# Official EICrecon ACTS Geometry integration: Phase 1

## Outcome and safety boundary

The installed official provider is ABI-compatible with a small standalone probe
and can be reused through its exported CMake target. The current telescope
**cannot produce a complete TrackingGeometry through that provider's legacy
DD4hep conversion path**. The diagnostic option fails explicitly and remains
unavailable for reconstruction or calibration. The production local Geometry
path, numerical fitter, electron hypothesis, RawHits, Mille model, SO(3)
correction and Python Controller are unchanged.

An isolated official detector-element conversion reproduces all seven sensitive
plane frames and bounds in four physical Geometries. This is a useful component
compatibility result, **not** a successful TrackingGeometry/navigation test.
No official-path track fit or alignment closure is claimed.

Work starts from clean checkpoint
`7fd70f34bbf3761f13a8938ed4ba23f926f1adbe` on the new local branch
`feature/upstream-acts-geometry`. The checkpoint branch remains untouched.
No commit, push, merge, candidate activation, new Simulation or external-source
modification is part of this task. Evidence is under
`result/upstream_acts_geometry_20261023_01/`.

## Installed implementation and pinned sources

The compatible environment is the existing `sweet_mahavira` container, mounted
at `/work`. `environment.json` records package specifications, installation
hashes, image ID, resolved libraries and header SHA-256 values.

| Component | Installed revision/version |
|---|---|
| EICrecon | `195966d41899800eaeca6fbafd63cd53735e6543` |
| ACTS | 45.3.0; upstream tag commit `d1323a298569942d98ff46ee413031ebd604290d`, with recorded Spack patches below |
| DD4hep | 1.36 with recorded packaging/DDSim patches |
| PODIO | 1.7 (CMake 1.7.0) |
| EDM4hep | 1.0 (CMake 1.0.0) |
| EDM4eic | Git `7d7705d9bbd4794b1b875c04258e7d986aea8a47` (exported CMake version 8.9.0) |
| algorithms / cppgsl | Spack 1.3.0 / 4.2.0; their exported CMake package versions use separate version strings |
| ROOT | 6.38.00 |

The separate host EICrecon checkout is at
`67a00864dd47c709c98b4afc2c210c3faee100b1` and has a pre-existing
TimeframeSplitter modification and ROOT files. It was inspected read-only,
not used as a substitute for the installed revision. Git history contains the
installed commit. Its provider, service and measurement headers match installed
headers byte-for-byte (`upstream_header_match.json`).

Primary source references:

- [ActsGeometryProvider at the installed EICrecon commit](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/ActsGeometryProvider.cc): initialize/converter call, identifier hook, Volume-ID surface map and material setup.
- [ACTSGeo_service](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/services/geometry/acts/ACTSGeo_service.cc): lazy provider initialization from DD4hep_service and material-map parameters.
- [TrackerMeasurementFromHits](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/TrackerMeasurementFromHits.cc): CellID → VolumeManager context → Volume ID → surfaceMap → local coordinates and EDM surface ID.
- [CKFTrackingFunction](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/CKFTrackingFunction.cc): TrackingGeometry-backed Navigator with sensitive/material resolution.
- [ACTS converter](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/DD4hep/src/ConvertDD4hepDetector.cpp): collectSubDetectors, collectLayers, compound hierarchy and paired-endcap requirement.
- [ACTS DD4hepLayerBuilder](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/DD4hep/src/DD4hepLayerBuilder.cpp): VariantParameters, sensitive resolution, axis_definitions and surface creation.
- [DD4hep assembly constructor](https://github.com/AIDASoft/DD4hep/blob/v01-36/DDDetectors/src/SubdetectorAssembly_geo.cpp), [DetectorImp](https://github.com/AIDASoft/DD4hep/blob/v01-36/DDCore/src/DetectorImp.cpp), and [Endcap2 constructor](https://github.com/AIDASoft/DD4hep/blob/v01-36/DDDetectors/src/SiTrackerEndcap2_geo.cpp): parent declaration/registration and missing detector-flag application in Endcap2.

The installed ACTS package is not assumed to be an unpatched tag. Its three
applied patches were downloaded and matched to the exact recorded SHA-256:
PR5193 `bee084dd…` (Gen3 DD4hep/ROOT blueprint conversion), PR5244 `3238f9c1…`
(Extent API), and PR5192 `36726a66…` (navigation/header fixes and DD4hep field
adapter). `applied_acts_patches.json` contains full hashes and affected paths.
They do not change the legacy ConvertDD4hepDetector/LayerBuilder implementation
used by the installed EICrecon provider. The unused archived pr4620/pr5010 recipe
patch files were distinguished from applied patches. DD4hep's applied patches
cover a DDSim particle-handler notice and installation of plugin headers, not
the detector hierarchy constructors audited here.

## Local versus official architecture

| Concern | Maintained local path | Installed official path |
|---|---|---|
| Geometry source | Selected immutable DD4hep XML; CellIDPositionConverter sensitive contexts | Same DD4hep detector, passed through ACTSGeo_service to ActsGeometryProvider |
| Surface construction | Seven PlaneSurfaces from SurfacePlacements; 50×50 mm half bounds | convertDD4hepDetector creates a complete volume/layer hierarchy and associated DD4hepDetectorElements |
| Local axes | u = minus sensor Z, v = sensor X, n = u cross v | axis_definitions; default XYZ is incompatible with these thin-Y TGeoTrd2 sensors; zXy matches the maintained plane frame |
| Mapping | Explicit seven-slot layer sequence, manually assigned ACTS IDs | CellID → VolumeManagerContext identifier → provider surfaceMap → converter GeometryIdentifier, with detector extra field |
| Measurements | Global RecHits projected into maintained surfaces; SiMAPS sensor X/Z covariance permuted to u/v | TrackerMeasurementFromHits projects onto mapped surfaces; its detector-specific initialization and covariance assumptions need separate adaptation |
| GeometryContext | Static context for the selected per-process immutable XML | Run-scoped provider context; must accompany its actual surfaces |
| Navigation | DirectNavigator; supplied ordered surfaces; zero field | Navigator over closed TrackingGeometry; sensitive/material resolution and volume/layer bounds required |
| Material | No assigned ACTS surface material; unchanged local process-noise assumptions | Optional JSON/CBOR decorator; DD4hep solid material alone does not establish ACTS process-noise modeling |
| Alignment | Same RawHits reinterpreted in each current Geometry; independent Mille/official Pede/SO(3) correction | Not a replacement alignment algorithm; a valid associated Geometry must first exist |

Both paths in these checks use the DD4hep nominal transform instantiated from
the selected immutable XML. Live conditions/alignment payload updates and
context-dependent in-process Geometry changes were not validated. All seven
planes participate in the Geometry audit; only the existing five SiMAPS planes
participate in the saved-data tracking regressions.

The local RecHit factories obtain actual channel positions through DDRec and
keep their existing sensor covariance convention. SurfacePlacements already
uses all seven actual centers/bases and no new nominal positions are needed.
Mille receives Global RecHit points and current sensitive pivots; it does not
need a complete TrackingGeometry for the existing model. Its numerical code
and all steering files remain unchanged.

The official TrackerMeasurementFromHits is not a detector-agnostic drop-in:
it initializes an EPIC B0 constant and OuterMPGD readout logic. Even after a
Geometry conversion succeeds, its covariance basis must be validated for this
sensor X/Z segmentation. Equal current SiMAPS errors can conceal a swapped
basis. No official measurement/tracking factory was substituted in this phase.

## Confirmed conversion blockers

1. **Empty logical assemblies.** The nominal runtime world contains three empty
   compound DetElements, while SiMAPS/MPGD/ACLGAD are world children. The XML
   places the assembly declarations after the detectors they name.
   DD4hep_SubdetectorAssembly calls declareParent for future construction;
   pickMotherVolume/addDetector had already attached the earlier detectors to
   world. The generated assembly-first XML verifies this explanation: all
   detector children move under their intended logical assemblies while all
   seven physical frames and sensitive Volume IDs remain unchanged.
2. **Zero detector type flags.** All three actual detector typeFlag values are
   zero despite XML type_flags. The installed Endcap2 constructor and copied
   local factory do not call xml::setDetectorTypeFlag. XML flags alone therefore
   do not establish the TRACKER/ENDCAP metadata expected by the converter.
3. **No matching layers.** The configured patterns SiMAPS_layer\\d and equivalent
   names do not match actual layer0_module1_pos … layer6_module1_pos DetElements.
   There is no separate layer DetElement hierarchy in this builder.
4. **Missing layer/sensitive conversion metadata.** Selected layer candidates
   need VariantParameters (including envelope information for these non-tube
   module shapes); sensitive elements need explicit zXy axes. The native XYZ
   attempt rejects TGeoTrd2 conversion with the installed converter's plane-axis
   restriction. This is not a small numeric rotation discrepancy.
5. **Legacy topology limitation after those repairs.** With assembly order,
   discovery, flags and axes/envelopes repaired only in the diagnostic setup,
   the official provider throws: "Only one Endcap is given for the current
   hierarchy! Endcaps should always occur in pairs." The telescope is a
   one-sided planar sequence, not the expected paired barrel/endcap structure.

The empty hierarchy, zero flags and unmatched names are runtime observations.
The axis failure is independently demonstrated by the installed component.
Layer-envelope metadata is a source-established later requirement; the full
provider stops at the paired-endcap guard before that layer-building step.
These later requirements are not mislabeled as the immediate cause of the
original no-volume exception.

The original failure is therefore not missing plugins or an incompatible ACTS
ABI. The official provider and dependencies load and run. Its original compounds
have no collected layers and return nullptr volumes, ending in "no tracking
volume". Adding only the correct flags/discovery while retaining the original
empty assemblies still fails. A standalone top-level ENDCAP is also not one of
this legacy converter's accepted volume-builder cases.

No dummy negative detector, false barrel flag, moved sensor, relaxed check or
suppressed conversion exception was introduced to force success. DDRec
VolSurface objects are not a prerequisite of the audited ACTS sensitive-surface
construction: it uses TGeo placement/shape via DD4hepDetectorElement. Creating
DDRec surfaces alone would not repair these hierarchy/topology failures.

## Implemented isolated option

`TESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE=ON` adds only TelescopeGeometryProbe.
It reuses `EICrecon::algorithms_tracking_library` from the installed exported
CMake configuration, Acts::PluginDD4hep and existing dependencies. It does not
copy the official provider or service implementation. The export check and final
probe build succeeded with the installed compatible dependency set.

`python3 -m validation.official_geometry` selects:

- local (default): audit the established placement/plane convention.
- official: initialize the installed ActsGeometryProvider with the same selected
  DD4hep detector and an explicitly empty material map. Failure returns nonzero
  and retains diagnostics; there is no silent fallback.
- official-elements: convert seven sensitive contexts through the official
  DD4hepDetectorElement component with zXy; report native XYZ failure separately.
  It has no TrackingGeometry and no closed converter IDs, and is explicitly
  ineligible for reconstruction or calibration.

The metadata option is process-local and never edits input XML or physical
placements. The assembly-first diagnostic XML is generated under result/ only.
No production provider switch is exposed while the complete-Geometry gate fails.

## Executed Geometry checks

Final executable build: `build/upstream_acts_geometry_20261023_02/`.
`geometry_suite_final/geometry_comparison.json` and per-case geometry.json files
record every plane's complete center/matrix/u/v/n, bounds, round trips, CellID,
Volume ID, context element path, material association and ACTS ID. The local
manual IDs and unclosed component IDs are not compared for numeric equality.
Association uses the sensitive Volume ID and checks multiple channel CellIDs;
layer order is explicitly 0…6 and never inferred by sorting surface IDs.

| Selected XML | Planes | Max center difference [mm] | Max rotation element difference | Max component round trip [mm] |
|---|---:|---:|---:|---:|
| Nominal | 7 | 0 | 6.13e-17 | 0 |
| X/Y/Z translations | 7 | 0 | 6.13e-17 | 0 |
| Rx/Ry/Rz rotations | 7 | 0 | 1.16e-14 | 3.98e-15 |
| Combined six-DOF | 7 | 0 | 1.16e-14 | 3.67e-15 |

All 28 adapted component comparisons pass: bounds are [-50,-50,50,50] mm in
both local coordinates, interior corners agree, and normals have the same sign.
Sensitive thicknesses are 0.05 mm for L0–L4, 3 mm for L5 and 0.35 mm for L6.
These are extracted from the selected solid by the official component; the
local mathematical plane itself has no physical thickness/material assignment.
No ACTS surface material is assigned in this controlled comparison.

Full official TrackingGeometry remains unavailable for all four original XMLs.
The assembly-first experiment preserves all seven local frames/Volume IDs and
reaches the explicit paired-endcap rejection. Thus full converter-generated IDs,
closed-volume navigation and official-path reconstruction equivalence are
**not established**. Component IDs equal zero because no geometry closure ran;
they must not be used as reconstruction IDs.

## Reconstruction, derivative and preservation checks

Only the unchanged local production plugin/factory from the validated checkpoint
are used for saved-data regression. The probe-only build does not produce a new
BeamTestReco.so. No stale proof is assigned to the experimental official option.
Fresh representative L1/L2/L3 DD4hep/actual-Mille reports and a local-only gate
are generated under this task; source-matched unchanged noiseless controls are
referenced explicitly rather than relabeled. They do not authorize official-path
alignment. Final executed results and preservation counts are summarized in
`validation_summary.json` and `preservation_final.json` in the task directory.

Executed results:

| Check | Result |
|---|---|
| Official exported-target probe configure/build | passed in fresh build directory 02; actual installed libraries verified with ldd/readelf |
| Existing unit suite | 46 tests passed |
| Python/shell syntax | 64 Python files parsed; 14 shell scripts passed bash -n |
| Existing safety and preservation checkers | passed; 221 baseline and 2,046 relocated entries preserved |
| Historical L2-only closure | 99 tracks, +198.75 um correction; -199.571376 → -0.821365 um residual; ACTS chi2/stored-NDF 45.592235 → 1.981040 |
| Historical L2 Mille bytes | both before/after exactly match the checkpoint reference replay |
| Default L1/L2/L3 six-DOF RawHit replay | all 281 shared PODIO fields/relation branches and Mille bytes exactly match |
| Fresh local physical derivative evidence | 39 fresh DD4hep contexts; 162 two-component comparisons; 324 decoded official-Mille components; all six families on each L1/L2/L3 |
| Official-provider reconstruction comparison | not executed: complete Geometry gate failed |
| Output immutability | existing diagnostic directories refused; prior contents unchanged |

The strict PODIO comparison covers Measurement2D positions/covariances, track
parameters and chi2, predicted/filtered/smoothed measurements and segments,
RawHits and named relation targets. No event selection, uncertainty or particle
hypothesis changed. The official-versus-local comparison requested after a
successful full Geometry gate is deliberately not inferred from this local
regression. The local-only derivative gate reuses mathematical controls solely
because all their pinned model sources still match; it contains newly executed
physical reports and the unchanged production binary hashes.

The initial missing JSON dependency/API build attempts and the first native-XYZ
diagnostic exception are retained. The native exception is now a recorded
expected incompatibility within the component test, not a reason to skip the
adapted comparison. No historical failure output was overwritten.

## Independent commands

From the repository root on the host:

```sh
# CHECK-ONLY (disable Python cache writes for inspection).
export PYTHONDONTWRITEBYTECODE=1
cat docs/OFFICIAL_ACTS_GEOMETRY_PHASE1.md
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -m validation.official_geometry --help

# WRITES OUTPUT: start an initialized container shell.
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash
```

Inside the container, use fresh paths. The wrapper creates result/.environment;
no existing scientific result is overwritten.

```sh
# CHECK-ONLY: select unused paths and inspect checkpoint identity.
export PYTHONDONTWRITEBYTECODE=1
export STUDY=result/manual_official_geometry_001
export BUILD=build/manual_official_geometry_001
test ! -e "$STUDY" && test ! -e "$BUILD"
git status --short
git log -1 --oneline

# WRITES OUTPUT: isolated targets only, never the numerical fitter.
cmake -S localDetEICrecon -B "$BUILD" -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DMILLEPEDE_PREFIX=/work/external/install \
  -DTESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE=ON
cmake --build "$BUILD" --target TelescopeGeometryProbe LocalTelescopeGeometry -j2
# WRITES OUTPUT: reserve diagnostic directory exclusively.
mkdir "$STUDY"

# WRITES OUTPUT: four experimental XML copies through the maintained writer.
python3 - <<'PY'
import os,shutil
from pathlib import Path
from geometry.prepare import DEFAULT_NOMINAL,write_shifted_xml
root=Path(os.environ['STUDY'])/'geometries';root.mkdir()
shutil.copyfile(DEFAULT_NOMINAL,root/'nominal.xml')
x={1:.02,2:-.025,3:.03};y={1:-.015,2:.02,3:-.02};z={1:.2,2:-.15,3:.2}
angles=dict(rx_rad={1:.015,2:-.012,3:.012},ry_rad={1:-.012,2:.01,3:-.01},rz_rad={1:.008,2:-.006,3:.007})
write_shifted_xml(DEFAULT_NOMINAL,root/'translations.xml',x,y,z_shifts=z)
write_shifted_xml(DEFAULT_NOMINAL,root/'rotations.xml',{},**angles)
write_shifted_xml(DEFAULT_NOMINAL,root/'six_dof.xml',x,y,z_shifts=z,**angles)
PY

# WRITES OUTPUT: independent local and official-component checks.
# Repeat with translations.xml, rotations.xml and six_dof.xml using NEW outputs.
python3 -m validation.official_geometry --geometry "$STUDY/geometries/nominal.xml" \
  --build-dir "$BUILD" --geometry-build-dir "$BUILD" \
  --provider local --output-dir "$STUDY/nominal_local"
python3 -m validation.official_geometry --geometry "$STUDY/geometries/nominal.xml" \
  --build-dir "$BUILD" --geometry-build-dir "$BUILD" \
  --provider official-elements --output-dir "$STUDY/nominal_elements"
# CHECK-ONLY: inspect complete plane records and status before any inference.
cat "$STUDY/nominal_elements/geometry.json"

# WRITES OUTPUT: the actual official-provider attempt; expected NONZERO failure
# for this telescope. Run separately: set -e shells will stop here.
python3 -m validation.official_geometry --geometry "$STUDY/geometries/nominal.xml" \
  --build-dir "$BUILD" --geometry-build-dir "$BUILD" \
  --provider official --output-dir "$STUDY/nominal_official"
# CHECK-ONLY after the expected failure:
cat "$STUDY/nominal_official/geometry.json"

# WRITES OUTPUT: metadata-only experiment; still fails with original hierarchy.
python3 -m validation.official_geometry --geometry "$STUDY/geometries/nominal.xml" \
  --build-dir "$BUILD" --geometry-build-dir "$BUILD" --provider official \
  --metadata discovery-and-flags --output-dir "$STUDY/metadata_experiment"
```

The exact executed commands for all four cases and the assembly-order experiment
are in the task's geometry_comparison.json and per-invocation command.json files.
The tested combined XML was a byte-identical copy of the existing three-plane
physical sample Geometry. The manual generator above uses those same values.
Do not run a track comparison if full official Geometry construction fails.
Do not use this diagnostic build for calibration or assign its new factory
binary an old alignment gate; build-matched physical evidence is required.

For the unchanged local default's historical regression, with the protected
input installed as documented in validation/README.md:

```sh
# WRITES OUTPUT: saved data only, fresh directory; no Geant4 campaign.
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env TESTBENCH_BUILD_DIR=/work/build/l3_six_dof_20261023_01 \
  bash validation/run_closure.sh --result-dir result/official_phase1_local_regression_001 \
  --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root \
  --build-dir build/l3_six_dof_20261023_01 --reference validation/reference_metrics.json
```

## Next integration milestone

First choose an honest volume/navigation representation for a one-sided planar
telescope. Investigate the installed Gen3 DD4hep blueprint APIs (PR5193) as a
separate small prototype, or an explicitly supported beam-test layer/volume
builder; the installed EICrecon provider currently invokes the legacy converter.
Do not fake a second physical endcap or mislabel planar sensors as barrels.
Then validate a closed seven-surface association map, contexts, axes, covariances,
material-disabled navigation and saved-RawHit reconstruction before exposing a
production provider switch. Material and the full official tracking chain remain
separate later milestones. Logical hierarchy changes also affect RawHit topology
fingerprints; existing contracts must not be weakened to accept them blindly.
