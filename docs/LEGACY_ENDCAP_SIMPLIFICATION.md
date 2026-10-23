# Geometry simplification and legacy one-sided endcap experiment

## Decision and scope

Starting HEAD: `020a29d81173097f2a0f03b8d08020e70eefb5a3`, branch
`feature/upstream-acts-geometry`; task-start working tree was clean.

The optional Blueprint provider and its reconstruction selection/injection have
been removed. They were not required by the local fitter, Mille Writer, SO(3)
corrections, RawHit stages or Controller. No replacement provider was added.
The established local implementation is restored byte-for-byte to the relevant
files at checkpoint `7fd70f34bbf3761f13a8938ed4ba23f926f1adbe`.

A private converter experiment directly invokes the **installed EICrecon
ActsGeometryProvider**. Relaxing the ACTS paired-endcap guard is insufficient
for this telescope: subsequent layer construction fails. Corrected radial
metadata exposes a second, precisely located ACTS exception and an independently
visible layer-frame inconsistency. The official integration gate remains
**failed**. No experimental reconstruction or new official Navigation success
is claimed. Further provider development stopped at this boundary.

All installed libraries, external source checkouts, nominal Geometry, physical
settings and historical outputs remain unchanged. No commit, push, merge or
Geometry activation is part of this task. Documentation and code comments are
English; no eic-shell/environment upgrade or new Simulation campaign is used.

## Removed code and retained evidence

| File/function | Change |
|---|---|
| `localDetEICrecon/geometry/ConvertedTelescopeGeometry.h` | Removed `ConvertedTelescopeGeometry` and `closeTelescopeGeometry`; the committed historical version remains at starting HEAD. |
| `localDetEICrecon/CMakeLists.txt` | Removed `TESTBENCH_ENABLE_BLUEPRINT_PROVIDER` and its PluginDD4hep link/definition for BeamTestReco. The optional isolated official Geometry probe remains. |
| `algorithms/tracking/BeamTestACTSFitter.cc/.h` under `localDetEICrecon/` | Removed optional converted-surface injection/owner and restored `init()` surface creation. All numerical functions and electron hypothesis remain checkpoint-identical. |
| `BeamTestACTSFitterConfig.h`, `factories/tracking/BeamTestACTSFitter_factory.h` under that root | Removed geometryProvider parameter, conditional include and Configure branch. |
| `reconstruction/reconstruct.py` | Removed `--geometry-provider`, provider command argument and metadata inheritance. Restored checkpoint implementation. |
| `localDetEICrecon/geometry/OfficialGeometryProbe.cc` | Removed Blueprint construction/navigation branch and includes. Retained local, official and official-elements diagnostic modes. |
| `validation/official_geometry.py` | Removed Blueprint choice and deleted-header fingerprint. |
| `validation/merge_so3_evidence.py` | Removed deleted-header pin; retained fitter/factory/reconstruction source pins. |
| `validation/validated_sources.json`, `validated_sources_history.json` | Restore the exact validated local fitter hash after regression; append provenance without changing historical reference values. |
| `validation/legacy_endcap_experiment.py` | New isolated-build diagnostic, with strict upstream-source hash and exclusive build/output directories; not a provider or production build option. |

The Phase 1 and complete Blueprint integration audit documents remain historical
records with a current-status notice. Their complete local results/builds and
source-only handoff archive are preserved. `validation/compare_geometry_providers.py`
remains a read-only archived-output comparison tool: its `--blueprint` argument
names an input directory and does not select or initialize a provider.
README, validation guide and the architecture guide now describe the current
local-only reconstruction path and this experiment.

## Installed official path and exact source basis

Environment remains EICrecon `195966d41899800eaeca6fbafd63cd53735e6543`, ACTS
45.3.0 based on `d1323a298569942d98ff46ee413031ebd604290d`, DD4hep 1.36 and the
previously pinned Docker image. The three installed ACTS packaging patches
are recorded in the Phase 1 evidence; none changes the converter or the Core
.cpp functions identified below. PR5192 does change relevant header declarations;
the experiment compiles against the **actual installed headers**, not substitutes.

Matching source references:

- [EICrecon ActsGeometryProvider.cc](https://github.com/eic/EICrecon/blob/195966d41899800eaeca6fbafd63cd53735e6543/src/algorithms/tracking/ActsGeometryProvider.cc),
  initialize at line 130, converter call around 197 and surface-map population
  around 235–266.
- [ConvertDD4hepDetector.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/DD4hep/src/ConvertDD4hepDetector.cpp),
  `volumeBuilder_dd4hep`, paired guard at 349–355.
- [DD4hepLayerBuilder.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Plugins/DD4hep/src/DD4hepLayerBuilder.cpp),
  `endcapLayers` lines 85–93: raw module transform/inverse and ProtoLayer;
  lines 215–222: disc-layer creation; lines 396–423: sensitive-axis conversion
  and raw layer `convertTransform` are separate operations.
- [LayerCreator.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/LayerCreator.cpp),
  automatic `discLayer` around 274–338: radial bounds at 325–327 and DiscLayer
  construction around 331.
- [SurfaceArrayCreator.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/SurfaceArrayCreator.cpp),
  `surfaceArrayOnDisc` lines 250–256: enveloped Rmin/Rmax are passed to the
  DiscSurface lookup grid; this is the first negative-radius throw caller.
- [RadialBounds.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Surfaces/RadialBounds.cpp),
  `checkConsistency` lines 24–26 rejects negative inner radius.
- [DiscLayer.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/DiscLayer.cpp),
  `buildApproachDescriptor` lines 86–94 unconditionally accesses inner cover.
- [CylinderVolumeBounds.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/CylinderVolumeBounds.cpp),
  `orientedSurfaces` around 130–136 omits the inner cylinder when rmin=0.
- [CylinderVolumeBuilder.cpp](https://github.com/acts-project/acts/blob/d1323a298569942d98ff46ee413031ebd604290d/Core/src/Geometry/CylinderVolumeBuilder.cpp),
  `trackingVolume` builds layers before volumes; optional endcaps are handled
  around 400–460. That source support alone is not proof of a valid telescope.

The unmodified converter translation unit SHA-256 is
`1ee6b01aa7de2d6357781e1bcdaef366480bd6aa63fa1e1c9a83fde645e93231`.
The new runner refuses any other input. Matching source copies/URLs and logs
are retained under `result/legacy_endcap_20261023_01/`.

## What the private experiment changes

`validation.legacy_endcap_experiment` creates an executable containing a private
copy of the converter translation unit. `--export-dynamic` lets the installed
provider call that copy. A unique runtime marker and readelf/ldd audit prove
interposition. The helper functions in that translation unit are the same
upstream source. Installed DD4hepLayerBuilder, ACTS Core and EICrecon libraries
remain in use; nothing is installed or preloaded into reconstruction.

Control: only a diagnostic entry marker is added. Singleton case: the exact
paired-endcap exception is replaced by a warning, with no other converter
behavior change. The separate zero-inner case changes only process-local
`envelope_r_min` metadata from .01 mm to zero in a generated probe copy.
No bounds or consistency checks are removed downstream.

The experiment needs the already established discovery prerequisites. An
assembly-first diagnostic XML reorders the existing logical assembly declarations
before detector construction. The physical definitions are unchanged. A fresh
check from the canonical nominal confirms all seven centers/rotation matrices,
bounds and sensitive Volume IDs are exactly unchanged. Process-local metadata
sets the real module-name pattern, TRACKER|ENDCAP for the actual planar tracking
detectors, explicit zXy sensitive axes and .01 mm layer envelopes. No BARREL
flag, negative detector, new sensor, dummy volume or physical displacement is
introduced. The original nominal XML and persistent flags are not edited.
Without these prerequisites the original empty-assembly/no-layer failure occurs
before the paired-endcap check, as established in Phase 1.

## Observed failures and scientific stopping point

| Case | Actual result | Interpretation |
|---|---|---|
| Private control, guard intact | Exit 2, paired-endcap exception | Control reproduces installed converter restriction through the actual EICrecon provider. |
| Singleton guard relaxed | Exit 2, `RadialBounds: invalid radial setup` | Reaches CylinderVolumeBuilder → positive layer builder → LayerCreator. ProtoLayer inner R=0 minus .01 mm envelope produces negative radial bounds; no TrackingGeometry returns. |
| Singleton + zero inner envelope | Exit 2, `vector::_M_range_check: __n (which is 3) >= this->size() (which is 3)` | Binning consistency passes, then DiscLayer approach construction accesses missing optional inner cylinder. |

The first exception trace (`radial_exception_trace.log`) confirms the call
through SurfaceArrayCreator::surfaceArrayOnDisc → DiscSurface/RadialBounds,
before LayerCreator constructs its final representing layer.

The second exception trace resolves the latter to
`Acts::DiscLayer::buildApproachDescriptor() [clone .cold]`, offset 0x2087bd in
the installed libActsCore.so. The matching source calls
`bSurfaces.at(tubeInnerCover)` at line 93; the installed enum assigns inner
cover index 3. At zero inner radius `CylinderVolumeBounds::orientedSurfaces`
returns only the two discs and outer cylinder (three entries). The trace also
shows DiscLayer constructor → LayerCreator::discLayer →
DD4hepLayerBuilder::endcapLayers/positiveLayers →
CylinderVolumeBuilder::trackingVolume → TrackingGeometryBuilder → private
converter → installed ActsGeometryProvider::initialize. This is an observed
Core defect for this zero-inner-radius construction, not a hypothesis about
Pede or the local fit.

GDB was attempted but cannot read registers in the existing emulated container;
that failed attempt is retained. A tiny diagnostic-only __cxa_throw interposer
was then compiled and preloaded **only for the isolated probe**, recording the
actual exception stack without changing libraries. It is not a framework or
reconstruction dependency.

A separate confirmed frame inconsistency is visible before either failure:
DD4hepLayerBuilder uses the raw module frame for the layer ProtoLayer, while
sensitive conversion uses zXy. The raw module is thin in local Y, not local Z.
Its reported local Z extent is −50…+50 mm and resulting disc thickness is
100.02 mm, although the SiMAPS sensitive thickness is .05 mm. This frame is not
a valid disc-layer representation of the selected sensor. Successful binning
alone would not repair its normal or enclosing volume geometry.

Therefore minimal **guard-only** support is disproven for the actual telescope.
At least radial-envelope handling, optional inner-boundary handling and a
physically consistent layer frame/extent convention need correction before
volume wrapping can be assessed. Tilted/translated layer and Volume navigation
would still need independent validation. CylinderVolumeBuilder's optional-endcap
code suggests that singleton topology is not intrinsically impossible, but its
complete wrapping path was **not reached successfully** here. No claim is made
that all one-sided Geometries are unsupported by ACTS.

No closed TrackingGeometry is returned, no final EICrecon SurfaceMap is populated,
and generated GeometryIdentifier uniqueness/navigation cannot be certified for
this experiment. Individual DD4hep components still match all 28 surfaces, with
unclosed IDs zero. Those checks are separate from complete Geometry. No
experimental reconstruction was run after the failed gate.

## Actual call paths after simplification

Production reconstruction:

```text
reconstruction.reconstruct → eicrecon, BeamTestReco profile=raw
  → DD4hep_service (selected XML) → CellIDPositionConverter
  → TrackerHitReconstructionNoAssoc_factory → channel positions/RecHits
  → BeamTestACTSFitter_factory::Configure
      → surfacePlacements(actual sensitive contexts, fixed seven slots)
      → BeamTestACTSFitter::setPlacements → init(manual PlaneSurfaces/IDs)
      → fitSelected(globalToLocal, covariance permutation, FitSourceLink)
      → EigenStepper + zero B + DirectNavigator + KalmanFitter
  → BeamTestMilleProcessor (track-associated five SiMAPS hits)
      → BeamTestMilleWriter → official Mille → Pede
      → scope/sign-controlled SO(3) candidate → same-RawHit refit
```

Official experiment, Geometry only:

```text
TelescopeLegacyEndcapProbe → installed ActsGeometryProvider::initialize
  → private exact-version convertDD4hepDetector/volumeBuilder_dd4hep
  → installed TrackingGeometryBuilder/CylinderVolumeBuilder
  → installed DD4hepLayerBuilder → LayerCreator/DiscLayer
  → FAIL before complete TrackingGeometry, SurfaceMap population or Navigation
```

In the intended official path, closure decorates ACTS IDs (including the detector
extra field), then provider visitSurfaces maps each DD4hepDetectorElement's
identifier through VolumeManager to sensitive Volume ID → Surface. The retained
probe audits that map only if initialization succeeds. The local fitter instead
has a GeometryIdentifier → Surface map and source-index → layer association;
it does not consume the official SurfaceMap/TrackingGeometry. This remaining
independent implementation and the seven-slot CellID/bounds assumptions are
explicit. The standard acts plugin can still be registered by reconstruction,
but its failing legacy Geometry initialization is not the fitter's Geometry
source and its error was not suppressed.

## Independent manual commands

Run at repository root using the existing container. Every named build/result
must be new when repeating these commands. The following command interfaces
were actually exercised; full command vectors, patches, source hashes and logs
are in the evidence root. No commands below activate Geometry or run a new
Simulation.

CHECK-ONLY — source/default/CLI inspection; no Truth:

```sh
git diff -- localDetEICrecon reconstruction validation
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -m validation.legacy_endcap_experiment --help
```

WRITES OUTPUT — local build, existing dependencies; no Truth:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env TESTBENCH_BUILD_DIR=/work/build/legacy_local_20261023_01 \
  bash environment/build.sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh cmake \
  -S /work/localDetEICrecon -B /work/build/legacy_local_20261023_01 \
  -DTESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE=ON
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh cmake \
  --build /work/build/legacy_local_20261023_01 --target TelescopeGeometryProbe -j 2
```

WRITES OUTPUT — isolated control/guard/zero-inner experiments, Geometry only;
no Simulation Truth. Required converter source is the SHA-pinned original named
above, obtained in Phase 1. Its upstream download URL is the converter source
link above with raw.githubusercontent.com and the same pinned commit. Required
assembly-first XML is the preserved Phase 1 diagnostic. This is not a modified
nominal file. Each command returns **2 as the expected failure**, and writes
geometry.json/exit.json/configure/build/probe logs and private source/patch.
Do not interpret expected-failure reproduction as a Geometry pass.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.legacy_endcap_experiment \
  --converter-source result/upstream_acts_geometry_20261023_01/acts_source/ConvertDD4hepDetector.cpp \
  --geometry result/upstream_acts_geometry_20261023_01/hierarchy_ordered.xml \
  --geometry-build-dir build/l3_six_dof_20261023_01 \
  --build-dir build/legacy_endcap_control_20261023_01 \
  --output-dir result/legacy_endcap_20261023_01/control --metadata discovery-and-flags
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.legacy_endcap_experiment \
  --converter-source result/upstream_acts_geometry_20261023_01/acts_source/ConvertDD4hepDetector.cpp \
  --geometry result/upstream_acts_geometry_20261023_01/hierarchy_ordered.xml \
  --geometry-build-dir build/l3_six_dof_20261023_01 \
  --build-dir build/legacy_endcap_single_20261023_01 \
  --output-dir result/legacy_endcap_20261023_01/single \
  --metadata discovery-and-flags --allow-single-endcap
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.legacy_endcap_experiment \
  --converter-source result/upstream_acts_geometry_20261023_01/acts_source/ConvertDD4hepDetector.cpp \
  --geometry result/upstream_acts_geometry_20261023_01/hierarchy_ordered.xml \
  --geometry-build-dir build/l3_six_dof_20261023_01 \
  --build-dir build/legacy_endcap_zero_inner_20261023_01 \
  --output-dir result/legacy_endcap_20261023_01/zero_inner \
  --metadata discovery-and-flags --allow-single-endcap --zero-inner-envelope
```

WRITES OUTPUT — individual-surface checks, local and official component modes;
28 official component comparisons across four saved physical fixtures. Expect
passed=true and tracking_geometry_available=false, not closed IDs/navigation:

```sh
for CASE in nominal translations rotations six_dof; do
  for PROVIDER in local official-elements; do
    TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
      -m validation.official_geometry \
      --geometry "result/upstream_acts_geometry_20261023_01/geometries/$CASE.xml" \
      --build-dir build/legacy_local_20261023_01 \
      --geometry-build-dir build/legacy_local_20261023_01 --provider "$PROVIDER" \
      --output-dir "result/legacy_endcap_20261023_01/${CASE}_$PROVIDER"
  done
done
```

WRITES OUTPUT — existing required historical closure regression, local Geometry;
saved Simulation is reused, Truth only in post-fit residual validation:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env TESTBENCH_BUILD_DIR=/work/build/legacy_local_20261023_01 \
  bash validation/run_regression.sh result/legacy_endcap_20261023_01/l2_regression \
  build/legacy_local_20261023_01
```

The independent exact six-DOF RawHit replay, derivative/noiseless controls,
Controller configuration check and preservation commands are recorded with the
regression results below. They do not use the failed official Geometry.

## Regression and preservation results

Results are reported independently of the failed official Geometry gate.

| Check | Executed result |
|---|---|
| Fresh local Plugin build and retained audit target | Passed; no Blueprint header, compile definition or production PluginDD4hep dependency. |
| Historical complete closure | 99 tracks; correction +198.75 µm; L2 pooled Rec−Sim −199.571375548 → −0.821364508 µm; ACTS chi2/stored-NDF 45.5922348485 → 1.98103976780. |
| Historical initial/corrected exact replay | All 281 PODIO branches and Mille bytes identical at each stage. |
| Six-DOF saved RawHit replay | 95 tracks/950 scalars; all 281 PODIO branches and Mille bytes exact. |
| Retained component audit | 28/28 official component comparisons, four physical Geometries; explicitly not complete Geometry. |
| Fresh derivatives | All 18 labels; 39 physical contexts, 162 vector comparisons, 324 actual binary components passed. |
| Existing noiseless SO(3) controls | All 11 cases passed using the same declared capture-range controls. |
| Existing unit/safety tests | 46 unit tests passed; existing SQLite ResourceWarnings retained; safety refusal checks passed. |
| Controller | Strict configuration load passed with new matching local gate; no Controller iteration or activation run. |
| ROOT/baseline preservation | Regression ROOT canvases/histograms/graphs read back; 221 baseline records and 2046 relocated files checked unchanged, plus preserved electron source pin. |

Fresh build/source fingerprints are in `gate.json` and final preservation/source
manifests under `result/legacy_endcap_20261023_01/`. The earlier Pede/uncertainty
and capture-range limitations remain, not reclassified by these regressions.
The official expected-failure experiment is not an alignment result.

WRITES OUTPUT — independent six-DOF RawHit replay, no Truth used for inference;
inputs are the protected saved RawHits, provenance contract and Survey XML:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m reconstruction.reconstruct \
  --result-dir result/legacy_endcap_20261023_01/default_six_replay \
  --raw-input result/l3_six_dof_20261023_01/three_plane_smoke/step2_digitization/rawhits.edm4eic.root \
  --raw-metadata result/l3_six_dof_20261023_01/three_plane_smoke/step3/rawhit_contract.json \
  --geometry result/l3_six_dof_20261023_01/survey/step1/misaligned.xml \
  --build-dir build/legacy_local_20261023_01 --alignment-mode l1_l2_l3_six_dof
```

CHECK-ONLY — compare that output against the saved sample, no Truth; no output
file is changed. This function and exact Mille checks were exercised in
`replay_default_six.py` and its report:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c \
  'from pathlib import Path; from validation.compare_raw_paths import compare_files; old=Path("result/l3_six_dof_20261023_01/three_plane_smoke/step3"); new=Path("result/legacy_endcap_20261023_01/default_six_replay/step3"); print(compare_files(old/"reco.root",new/"reco.root")); assert (old/"mille.dat").read_bytes()==(new/"mille.dat").read_bytes()'
```

WRITES OUTPUT — existing derivative and noiseless regression commands. The
finite differences use fresh fixed-channel DD4hep queries; mathematical fixture
Truth is only for controlled generation/post-fit comparison, never data
corrections. Expected results are the counts above.

```sh
for LAYER in 1 2 3; do
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m validation.validate_tilt_derivatives --coupled --representative \
    --layer "$LAYER" --build-dir build/legacy_local_20261023_01 \
    --output "result/legacy_endcap_20261023_01/derivatives_L$LAYER"
done
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.so3_closure \
  --writer-fixture result/legacy_endcap_20261023_01/derivatives_L1/writer_fixture \
  --output result/legacy_endcap_20261023_01/noiseless \
  --translation-scale 0.25 --three-layer-survey-fraction 0.5
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.merge_so3_evidence --build-dir build/legacy_local_20261023_01 \
  --derivative-report result/legacy_endcap_20261023_01/derivatives_L1/report.json \
  --derivative-report result/legacy_endcap_20261023_01/derivatives_L2/report.json \
  --derivative-report result/legacy_endcap_20261023_01/derivatives_L3/report.json \
  --noiseless result/legacy_endcap_20261023_01/noiseless \
  --output result/legacy_endcap_20261023_01/gate.json
```

CHECK-ONLY — strict Controller configuration/evidence load, no Truth and no
Controller state modification. The config is a new local copy of the previous
policy, changing only build/gate references; the loader was exercised:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c \
  'from pathlib import Path; from calibration.settings import load; load(Path("result/legacy_endcap_20261023_01/controller_local_config.json")); print("PASS current local configuration; no Controller execution")'
```

CHECK-ONLY — baseline/source and ROOT integrity, no file writes; Truth is not
used by these checks. Safety tests/unit tests below WRITES OUTPUT because they
create disposable new state/diagnostic directories, preserving failures.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 validation/verify_preservation.py
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 validation/check_root_outputs.py \
  --result-dir result/legacy_endcap_20261023_01/l2_regression
# WRITES OUTPUT: existing tests, no physics campaign or activation.
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s validation -p 'test_*.py'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env PYTHONDONTWRITEBYTECODE=1 python3 validation/check_safety.py
```

Additional diagnostic-only commands actually used: `gdb -batch` with catch throw
failed due emulated register access; `addr2line -C -f -e
/opt/local/lib/libActsCore.so 0x2087bd` resolved the throw; `ldd`/`readelf -Ws`
verified private converter exports and installed downstream libraries. The
preserved `ExceptionTrace.cc` was compiled with `g++ -shared -fPIC -g ... -ldl`
and preloaded only for a fresh isolated probe output. See
`zero_inner_backtrace.log`, `exception_trace.log`, `symbol_audit.log` and the
private converter patches. These artifacts are diagnostic evidence, not a
production dependency or a claimed successful Navigation test.

## Minimum follow-up, not implemented

Retain the working local planes. A separate upstream-compatible change would
need (1) an explicit layer-frame/axis contract for these actual module placements,
(2) legal radial/Global extents, (3) optional inner-boundary handling at r=0,
and only then (4) asymmetric Volume wrapping, closed mapping and real Navigator
validation across nominal/translated/tilted cases. Do not insert a tiny fake
central hole, fake endcap or BARREL classification to bypass these defects.

Only after those Geometry gates pass should an official-style Volume-ID
SurfaceMap and measurement/SourceLink interface be connected to the unchanged
fitter. Replacing DirectNavigator, adding detector measurements or certifying
statistical performance is outside this task. No alternative provider has been
added to conceal the failed legacy gate.

Final preservation check: **46,691** pre-existing output/dependency/build files
and symlinks unchanged; the external EICrecon checkout and both Git checkpoints
are unchanged. Eight previously fingerprinted installed library/header files
also match. Syntax checks passed for 66 Python files, 14 shell scripts and ten
documented shell blocks. The obsolete reconstruction provider option is refused
before creating any output stage.

Current local BeamTestReco.so SHA-256:
`57b09ad3d45ba4acddb00079d32b6730aae5992454feb79c16b085e23d4c843b`.
Current local Geometry factory SHA-256:
`4d8700a135f85a6be405a8d9e0eb92dc5211d13d3cfaec3334bef6f2b04f0e6b`.
These are new build fingerprints, not relabeled historical proof. All generated
builds, private sources/patches, partial failures and new regression outputs
remain under fresh build/result directories and are excluded from Git.
