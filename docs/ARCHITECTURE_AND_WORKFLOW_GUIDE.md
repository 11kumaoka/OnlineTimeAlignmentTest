# Source-based architecture and workflow handoff

This guide describes the maintained implementation on
`feature/upstream-acts-geometry`, based on checkpoint
`7fd70f34bbf3761f13a8938ed4ba23f926f1adbe`. It was checked against the actual
Python modules, C++ factories/algorithms/processors, CMake and configuration
files before the integration commit. It describes a seven-sensor telescope
framework, not a detector-general ePIC reconstruction implementation.

## 1. Directory and configuration map

All paths below are relative to the repository root. The Docker mount is
`/work`. Source-only archives do not include the locally installed dependencies
or reference datasets.

| Directory/file | Purpose and main source/entry points | Principal input → output; ownership |
|---|---|---|
| `environment/` | Maintained launcher `run.sh`, build implementation `build.sh`, dependency installer `setup_dependencies.py`; pins in `dependencies.json` | Host checkout + pinned container + external prefix → command execution/project builds. Installer is only for an absent dependency tree; not needed for this handoff. |
| `localDetEICrecon/` | Maintained C++ Plugin; `CMakeLists.txt`, delegating `build.sh`, `plugins/BeamTestReco.cc`; `algorithms/`, `factories/`, `processors/`, `alignment/src/`, `geometry/` | PODIO hits + selected DD4hep XML → RawHits/RecHits/tracks/states/Mille. Build produces `BeamTestReco.so`, local Geometry factory and optional probe under `build/`. |
| `geometry/` | Maintained `prepare.py`, `prepare_geometry.sh`, `placements.py`, `transforms.py`; immutable `nominal/seven_layer_telescope.xml`; `scenarios/*.json` | Nominal XML + physical scenario → step1 nominal/misaligned XML, GDML and placement QA. Scenario owns injected shifts; it is not an inference input. |
| `simulation/` | Maintained `simulate.py`, `simulate.sh`, `configs/electron_1GeV.json`, `configs/muon_5GeV.json` | step1 physical XML + beam/events/seed JSON → step2 EDM4hep events; optional existing Simulation import. |
| `digitization/` | Maintained `digitize.py`, `digitize.sh`, `contract.py` | Simulation + physical readout → step2_digitization RawHit-only ROOT and v2 contract. C++ factory defaults own digitizer thresholds/timing; contract records them. |
| `reconstruction/` | Maintained `reconstruct.py`, `runtime.py`, `reconstruct.sh`, `reconstruct_corrected.sh`, `configs/*.json` | RawHits + contract + current fit Geometry + particle settings → step3/step6 reco.root and mille.dat. `--after` shares the same implementation and frozen inputs/settings. |
| `alignment/` | Maintained `align.py`, `align.sh`, `pede_*.txt` | step3 Mille + selected steering → step4 Pede result/log/end status. This directory runs the external solver; C++ writing lives in the Plugin. |
| `correction/` | Maintained `correct_geometry.py`, wrapper, `scope.py` | Pede labels + current/reference XML + explicit scope → step5 inactive corrected.xml. Scope/sign conventions are centralized here. |
| `validation/` | Maintained `validate.py`, `metrics.py`, `run_closure.sh`, derivative/observability/Geometry checks, unit tests, reference and preservation manifests | Completed stages → step7 numerical summary; independent diagnostics → exclusive report directories. Historical reference values are not fitted or retuned. |
| `visualization/` | Maintained ROOT-only `closure.py`, `tilt_alignment.py`, `z_alignment.py`, `rz_statistics.py`, `browse.C` | Explicit Geometry/fit/validation inputs → ROOT histograms, canvases, graphs and PDFs. Truth is optional post-fit validation, not correction inference. |
| `calibration/` | Maintained `controller.py`, `iteration.py`, `settings.py`, `input_monitor.py`, `queue_manager.py`, `geometry_manager.py`, `convergence.py`, `runner.py`, `config/*.json` | Ordered immutable RawHit deliveries + Survey + policy/evidence → sequential attempts, SQLite state, immutable Geometry candidates and reports. Review/activation are explicit actions. |
| `input/` | Only `README.md` is maintained; incoming deliveries are ignored | RawHit files/sidecars and ready protocol → Controller discovery. Delivery data are local inputs, not source. |
| `docs/` | Maintained technical guides and explicitly historical reports | Source/API/evidence explanation; current Geometry commands are in `ACTS_GEOMETRY_INTEGRATION.md`. Historical reports retain their original scope. |
| `external/` | Ignored dependency sources/builds/installations | Pinned Mille and Millepede-II source → `install/bin/pede`, `install/lib/libMille2.so`, CMake package. Preserve existing installation. |
| `build/` | Ignored generated project builds | CMake inputs → libraries/executables/cache/link metadata. Use new build directories; old caches embed paths. |
| `result/` | Ignored generated current runs, Controller states, diagnostic and handoff artifacts | Independent stages normally use step1–step7; failed attempts remain immutable. Full validation evidence stays local. |
| `results/` | Ignored protected historical data/reference datasets | Saved Simulation/reconstruction/reference results; never overwritten by commands here. |
| `research_common.py` | Maintained infrastructure | `stage`, `done`, `require`, `execute`, `digest`, CLI output-path checks and dependency prefix validation; no numerical alignment model. |
| `README.md`, `.gitignore`, `.gitattributes` | Maintained project entry and Git policy | Sources/docs/configurations tracked; builds, ROOT/Mille/log/archive/dependency/input deliveries excluded. `__pycache__/` is generated and ignored. |

Exact new Geometry files: `localDetEICrecon/geometry/ConvertedTelescopeGeometry.h`,
`localDetEICrecon/geometry/OfficialGeometryProbe.cc`,
`validation/official_geometry.py`, and
`validation/compare_geometry_providers.py`. Provider plumbing is in
`BeamTestACTSFitterConfig.h`, `BeamTestACTSFitter_factory.h`,
`BeamTestACTSFitter.h/.cc`, `reconstruction/reconstruct.py` and CMake.

## 2. Independent data flow

Each Python stage is callable with `python3 -m PACKAGE.MODULE`; shell wrappers
delegate to it. `stage()` creates outputs exclusively; `done()` fingerprints
outputs; `require()` refuses altered/incomplete stages. Do not reuse partial
output directories.

| Step | Actual implementation | Inputs → outputs and checks |
|---|---|---|
| Environment/build | `environment/run.sh`; `environment/build.sh` via `localDetEICrecon/build.sh`; `localDetEICrecon/CMakeLists.txt` | Existing pinned Docker + external/install → new build. Optional blueprint/probe options default OFF. |
| Geometry preparation | `geometry.prepare.prepare`, `write_shifted_xml`, `verify_positions`; `geometry/prepare_geometry.sh` | Nominal + scenario → step1 nominal.xml/misaligned.xml, configuration snapshot, geoConverter QA and complete.json. Nominal is copied unchanged. |
| Simulation | `simulation.simulate.simulate`; `simulation/simulate.sh` | step1/misaligned.xml + Simulation JSON → step2/events.edm4hep.root, command/config/complete records. `--sim-input` links existing input instead of running Geant4. |
| Digitization | `digitization.digitize.digitize`; `LocalSiliconTrackerDigi_factory` → `SiliconTrackerDigi::process` | Simulation hits → LocalSiMAPS/MPGD/ACLGADRawHits. `profile=digitization` excludes reconstruction. Saved ROOT contains only EventHeader + RawHits, with contract and checksum. |
| RawHit reconstruction | `reconstruction.reconstruct.reconstruct`; `LocalTrackerHitReconstructionNoAssoc_factory` → `TrackerHitReconstruction::process`; `BeamTestACTSFitter_factory` → `BeamTestACTSFitter::fitSelected/process` | Explicit RawHit file + validated contract + selected Geometry → step3/reco.root. `profile=raw` does not redigitize or require Truth associations. Particle/settings JSON and provider selection are recorded. |
| Mille production | `BeamTestMilleProcessor::Process`, `BeamTestMilleWriter::writeTrackRecord` | Accepted track-associated SiMAPS RecHits → step3/mille.dat in the same EICrecon process. Exactly one selected hit per L0–L4 is required; ambiguous/missing layers are rejected. |
| Solver | `alignment.align.align`, `read_pede`; `alignment/align.sh` | step3/mille.dat + canonical mode steering → step4/pede.txt, millepede.res/.log/.end and completion. Process exit and solver end status are distinct. |
| Geometry correction | `correction.correct_geometry.correct/correct_so3`, `correction.scope.parameter_spec` | Selected Pede parameters + current Survey/reference → step5/corrected.xml and signed increment/version hashes. No Truth is used; candidate remains inactive. |
| Same-RawHit refit | `reconstruction.reconstruct` with `--after`; `reconstruct_corrected.sh` | step3 frozen source/settings + step5 corrected.xml → step6/reco.root and mille.dat. Provider is explicit or inherited from step3 metadata. |
| Validation | `validation.validate.validate`, `metrics.calculate`; `visualization.closure`; SO(3) information and `visualization.tilt_alignment` are independent diagnostics | Supported standard closure → step7 summary/ROOT/PDF. General SO(3) manual runs use the explicit information/plotting interfaces, not an invented generic validate mode. |
| Optional iterations | `calibration.controller.process` → `calibration.iteration.iterate` → independent stage subprocesses | One fixed RawHit file per attempt; current Geometry changes between solves. Policy, derivative/binary/source gates, information bounds and immutable parent chain are enforced; activation is separate. |

Importing existing RawHits can skip Simulation and Digitization entirely.
With `--raw-input`, `--raw-metadata` and `--geometry`, reconstruction also needs
no step1. Correction still needs the applicable nominal/scenario/reference
provenance; the manual six-DOF commands prepare that without rerunning Simulation.
The RawHit contract checks readout/topology/units/producer/checksum. Simulation
provenance hashes are not Truth positions and do not supply corrections.

### Runnable independent commands and execution status

The following is a **runnable fresh-run recipe**, traced to current CLI parsers;
it was not executed as a new Simulation campaign in this commit/handoff task.
For exact previously executed saved-RawHit/Geometry/Pede/refit commands and
success evidence, use [ACTS_GEOMETRY_INTEGRATION.md](ACTS_GEOMETRY_INTEGRATION.md).
Do not apply the old 99-track reference to a newly generated z=-500 mm sample.

CHECK-ONLY: CLI inspection, no new analysis outputs; no Truth.

```sh
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh python3 -m reconstruction.reconstruct --help
bash environment/run.sh python3 -m validation.official_geometry --help
bash environment/run.sh python3 -m calibration.controller --help
```

WRITES OUTPUT: fresh project build using existing dependencies; no Truth.
This enables optional components but **does not select the blueprint provider**.
Expected outputs are BeamTestReco.so, libLocalTelescopeGeometry.so and the probe.

```sh
BUILD=build/manual_source_handoff_001
RUN=result/manual_source_handoff_001
bash environment/run.sh cmake -S localDetEICrecon -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DMILLEPEDE_PREFIX=/work/external/install \
  -DMille_DIR=/work/external/install/cmake \
  -DTESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE=ON \
  -DTESTBENCH_ENABLE_BLUEPRINT_PROVIDER=ON
bash environment/run.sh cmake --build "$BUILD" -j 2
```

WRITES OUTPUT: independent L2 X demonstration, Geometry through ROOT validation.
Simulation uses the physical misaligned Geometry; reconstruction explicitly uses
local nominal/corrected Geometry. The current electron JSON owns 100 events,
1 GeV, z=-500 mm, angular range, transverse width and seed. Truth creates the
Simulation and is used in final residual validation only. Inference uses RawHits.
Expected success evidence: exclusive complete.json records in each stage,
matching before/after RawHit hashes, successful solver status inspection and
step7/alignment.root. Review warnings, not only process exit codes.

```sh
bash environment/run.sh python3 -m geometry.prepare --result-dir "$RUN" \
  --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh python3 -m simulation.simulate --result-dir "$RUN" \
  --config simulation/configs/electron_1GeV.json
bash environment/run.sh python3 -m digitization.digitize --result-dir "$RUN" \
  --build-dir "$BUILD"
bash environment/run.sh python3 -m reconstruction.reconstruct --result-dir "$RUN" \
  --build-dir "$BUILD" --geometry-provider local \
  --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh python3 -m alignment.align --result-dir "$RUN" \
  --steering alignment/pede_template.txt
bash environment/run.sh python3 -m correction.correct_geometry --result-dir "$RUN" \
  --mode l2_x
bash environment/run.sh python3 -m reconstruction.reconstruct --result-dir "$RUN" \
  --after --build-dir "$BUILD" --geometry-provider local
bash environment/run.sh python3 -m validation.validate --result-dir "$RUN" \
  --correction-mode l2_x
```

For an existing compatible RawHit delivery, WRITES OUTPUT to a separate fresh
`--result-dir`: substitute `reconstruction.reconstruct --raw-input FILE
--raw-metadata CONTRACT --geometry SURVEY --build-dir BUILD`. Those uppercase
names are required local input substitutions, not default files. Choose an
explicit matching alignment mode/steering before fitting additional parameters.
To test blueprint, first pass the complete-Geometry probe for the selected XML,
then explicitly pass `--geometry-provider blueprint`. The integration report
provides the fully specified, actually tested dataset and commands.

Optional Controller example (WRITES OUTPUT; documented interface, **not executed
in this handoff**):

```sh
bash environment/run.sh python3 -m calibration.controller once \
  --config result/complete_acts_geometry_20261023_01/controller_local_config.json \
  --input-dir input --state-dir result/manual_controller_handoff_001
```

This local-only configuration was checked with the strict loader during the
integration. It requires the fresh matching plugin/evidence and the local
reference Survey. `once` processes the discovered ordered deliveries;
`watch` monitors sequentially. Do not point this example at deliveries you do
not intend to process. No Controller `review` or `activate` command is run by
this handoff. Controller state/evidence fingerprints prohibit silently resuming
old state after changing implementation/configuration. Experimental provider
selection is not exposed by the Controller.

## 3. Geometry and measurement implementation

`DD4hep_service` loads the explicitly selected XML and supplies the DDRec
CellIDPositionConverter. `geometry/SurfacePlacements.h::surfacePlacements`
resolves seven sensitive contexts in fixed layer-slot order. The template
CellID uses systems 31 (SiMAPS L0–L4), 100 (MPGD L5), 92 (AC-LGAD L6), layer
bits beginning at 11 and the existing module/sensor fields. Channel variants
must map to the same sensitive Volume ID. This is telescope-specific decoding,
not a general ePIC sensor-discovery service.

Local mode derives center and basis from the actual sensitive localToWorld
transform, then `BeamTestACTSFitter::init` creates seven PlaneSurfaces with
50 mm half bounds and manual IDs. In either mode u = -sensor Z, v = sensor X,
n = u cross v. DD4hep units are converted to ACTS mm. Tiny nominal-axis
roundoff is snapped only by the maintained local placement adapter.

Blueprint mode in `ConvertedTelescopeGeometry` owns seven
`ActsPlugins::DD4hepDetectorElement` objects, using official `zXy` TGeo axis
conversion and `Acts::UnitConstants::cm` length scaling. Converted surfaces are
checked against the maintained physical frame; Volume IDs must agree. It
passes those actual shared surfaces to `closeTelescopeGeometry`:

```text
Blueprint root
  └─ StaticBlueprintNode: Telescope TrackingVolume
       ├─ seven DD4hep-converted sensitive PlaneSurfaces
       └─ cuboid bounds from converted corners + 10 mm envelope
```

The root constructs an enclosing World with another 10 mm envelope.
`Blueprint::construct` connects/registers portals and closes Geometry IDs.
`TryAllNavigationPolicy` supplies candidates. `visitSurfaces` and `findSurface`
verify exactly seven unique sensitive associations. Numeric manual/closed IDs
may differ; semantic layer-slot mapping is retained. There is no sensor sort,
second placement model, fake paired endcap or false barrel classification.
The installed automatic `LayerBlueprintNode::LayerType::Plane` route is marked
unimplemented, so it is not used.

`BeamTestACTSFitter_factory::Configure` always receives selected physical
placements; only explicit `geometryProvider=blueprint` constructs/injects the
converted surfaces/context/shared owner. Both CMake options default OFF; an
unavailable or unknown requested provider throws rather than falling back.
Ownership is retained by `m_geometryOwner` in the algorithm. Detector elements,
surfaces and TrackingGeometry remain alive while fitting; the DD4hep service
must also remain alive. GeometryContext is static for the immutable per-process
XML; live alignment payloads are not implemented.

`TrackerHitReconstruction` derives channel positions and pixel variances through
DDRec. `BeamTestACTSFitter::fitSelected` projects Global RecHits onto the selected
surfaces, uses the existing sensor-X/Z to plane-u/v variance permutation and
constructs `FitSourceLink{geometryId,index}` plus calibrated measurements.
The surface accessor maps the ID to the actual selected Surface; source indices
associate states back to layer/hit slots. Serialized Measurement2D and
predicted/filtered/smoothed outputs retain hit relations and selected IDs.

Reconstruction uses **EigenStepper + ConstantBField(0) + DirectNavigator + ACTS
KalmanFitter**. It does not use the complete TrackingGeometry navigator to find
fit measurements. The independent probe instead calls installed
`Acts::Navigator::initialize/nextTarget/handleSurfaceReached` and checks surface
and volume traversal against bounded ray intersections. Passing those tests is
not a full official EICrecon tracking-chain validation.

## 4. Official reuse versus local responsibility

References [E-installed] and [E-copy] identify different EICrecon revisions:
installed APIs are from 195966d4…, whereas copied-source provenance comments
identify 67a00864…. They must not be silently treated as identical revisions.
ACTS base [A] is supplemented by the exact applied patches recorded in the
Phase 1 report, particularly [A-patch].

| Component | Exact local source / upstream reference | Status and reason | Telescope assumptions / broader ePIC work |
|---|---|---|---|
| EICrecon/JANA2 registration and services | `localDetEICrecon/plugins/BeamTestReco.cc`, `factories/tracking/BeamTestACTSFitter_factory.h`; [E-copy] `src/detectors/BVTX/BVTX.cc`; [E-installed] `src/extensions/jana/`, `src/services/geometry/dd4hep/` | Adapted registration with installed JOmniFactory/JANA/DD4hep service; local profiles separate stages | Explicit collections and three detector types; wider use needs production detector configuration and compatible factories. |
| DD4hep physical Geometry | `geometry/nominal/seven_layer_telescope.xml`, `localDetEICrecon/geometry/SiTrackerEndcap2XY_geo.cpp`; [D] `DDDetectors/src/SiTrackerEndcap2_geo.cpp` | Nominal official builder, focused copied extension for physical Global corrections | Seven placements and supported ring attributes; general use needs detector-specific sensitive hierarchy/conditions support. |
| Local Geometry provider | `localDetEICrecon/geometry/SurfacePlacements.h`, `algorithms/tracking/BeamTestACTSFitter.cc` under the same C++ root; [A] PlaneSurface API | Independent placement adapter/manual surfaces retained as default | Fixed seven slots, 50 mm half bounds; replace assumptions only with sensor/readout-specific validation. |
| Blueprint provider | `localDetEICrecon/geometry/ConvertedTelescopeGeometry.h`; [A] `Core/include/Acts/Geometry/{Blueprint,StaticBlueprintNode,TrackingVolume}.hpp`; [A-patch] DD4hep blueprint components | Custom project provider reusing official conversion/closure/policy APIs | Single cuboid, seven known sensors, all-candidate navigation; ePIC needs scalable topology, mapping, material and conditions. |
| Installed legacy provider | `localDetEICrecon/geometry/OfficialGeometryProbe.cc` invokes [E-installed] `src/algorithms/tracking/ActsGeometryProvider.cc`; [A] `Plugins/DD4hep/src/ConvertDD4hepDetector.cpp` | Direct reuse only in diagnostic; incompatible one-sided endcap conversion | Requires a supported asymmetric conversion route, not fake detector classifications. |
| RawHit Digitization | `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.cc`, `factories/digi/SiliconTrackerDigi_factory.h`; [E-copy] `src/algorithms/digi/SiliconTrackerDigi.cc` | Copied/adapted installed-framework integration with local profiles and diagnostics | MPGD currently uses a temporary pixel-like path; detector-specific response/timing validation remains. |
| RecHit reconstruction | `localDetEICrecon/algorithms/tracking/TrackerHitReconstruction.cc`, `factories/tracking/TrackerHitReconstructionNoAssoc_factory.h`; [E-copy] `src/algorithms/tracking/TrackerHitReconstruction.cc` | Adapted algorithm with truth-free factory; optional Truth diagnostic is separate | Pixel covariance and current segmentation; broader use needs correlated/strip/timing measurement models. |
| Measurements/SourceLinks | `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.h/.cc`; contrast [E-installed] `src/algorithms/tracking/TrackerMeasurementFromHits.cc` | Independent narrow adapter; official measurement factory is not substituted | Seven-slot ID map and SiMAPS covariance basis; first unify sensor mapping and covariance contracts before adopting production converters. |
| Track fitting/navigation | `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc`; [A] `Core/include/Acts/TrackFitting/KalmanFitter.hpp`, `Propagator/{DirectNavigator,Navigator}.hpp`; contrast [E-installed] `src/algorithms/tracking/CKFTrackingFunction.cc` | Local fitter wiring to official numerical components; independent complete-Navigator test | Ordered telescope hits, zero field, no ACTS material; full ePIC CKF/navigation is not validated. |
| PODIO/EDM persistence | `digitization/contract.py`, `reconstruction/reconstruct.py`, `localDetEICrecon/plugins/BeamTestReco.cc`; [P], [E-installed] PODIO integration | Reused PODIO/EDM and EICrecon I/O; independent checksum/sidecar contract | Current collection names/units/topology; broader delivery schemas and measurement semantics need agreement. |
| Mille records | `localDetEICrecon/processors/BeamTestMilleProcessor.cc`, `localDetEICrecon/alignment/src/{BeamTestMilleWriter.cc,TiltMeasurementModel.h}`; [M] | Independent residual/derivative model using official Mille library | Five 2D SiMAPS hits, four local line parameters; other detectors need new validated equations, not just more labels. |
| Pede | `alignment/align.py`, `alignment/pede_*.txt`, pins in `environment/dependencies.json`; [MP] | Official executable, local orchestration/steering/status guards | Present constrained scopes and capture range; generalization requires observability/scientific validation. |
| SO(3) correction | `correction/correct_geometry.py`, `correction/scope.py`, `geometry/transforms.py` | Independent Global retraction and immutable XML update, no upstream replacement claimed | Explicit SiMAPS selected scopes/current sensor pivots; general detector conditions writer not implemented. |
| Controller | `calibration/controller.py`, `iteration.py`, `settings.py`, `geometry_manager.py`, `queue_manager.py` | Independent Python sequential orchestration, no upstream analogue claimed | Fixed RawHits, explicit model/evidence policy; broader operation needs validated detector inputs and supported scopes. |

[E-installed]: https://github.com/eic/EICrecon/tree/195966d41899800eaeca6fbafd63cd53735e6543
[E-copy]: https://github.com/eic/EICrecon/tree/67a00864dd47c709c98b4afc2c210c3faee100b1
[A]: https://github.com/acts-project/acts/tree/d1323a298569942d98ff46ee413031ebd604290d
[A-patch]: https://github.com/acts-project/acts/pull/5193.patch?full_index=1
[D]: https://github.com/AIDASoft/DD4hep/tree/v01-36
[P]: https://github.com/AIDASoft/podio
[M]: https://gitlab.desy.de/millepede/Mille/-/tree/cec2e880ecaab3d255e08e21c8f70f248c6098d8
[MP]: https://gitlab.desy.de/millepede/millepede-ii/-/tree/7e3f4f57d993e0e0098d1a40da72823ac9c3207b

## 5. Alignment equations and data boundaries

`BeamTestMilleProcessor::Process` uses ACTS Track → Measurement2D → RecHit
relations to identify the selected SiMAPS hits. It does **not** export ACTS
Kalman residuals/derivatives directly. It decodes layer bits, rejects ambiguous
or missing hits, and constructs five `BeamTestMilleWriter::Hit2D` entries from
Global positions. Sigma is sqrt(RecHit position-error xx/yy), bounded by the
configured `milleSigmaFloorMm`. No Truth coordinate enters the writer.

The independent Mille local track model is
`x(z)=x0+tx*(z-zref)`, `y(z)=y0+ty*(z-zref)`, with zref=100 mm in the maintained
reconstruction command. Local indices 1–4 mean (x0,y0,tx,ty). For the untilted
legacy model, addData receives measured x/y, sigma and local derivative rows
(1,0,dz,0)/(0,1,0,dz). The binary stores the measured right-hand side; the
residual is formed by the local fit, not an ACTS residual copied into the file.
For sign explanations use F=prediction+bias−measurement; its square is
unchanged by the opposite residual convention.

The coupled model in `BeamTestMilleWriter::writeTrackRecord` profiles the same
four line parameters with iterated covariance whitening, then freezes that
reference for one Global linear solve. `TiltMeasurementModel.h` computes
H=dF/d(u,v), C=H diag(sigma_u²,sigma_v²) H^T and W=Cholesky(C)^−1. The actual
rows written are W times the measured coordinates and local/global derivative
rows, with scalar sigma=1. Here sigma_u is sensor-Z sigma, sigma_v sensor-X
sigma. These whitened residuals are dimensionless. This is not a full material-
aware track covariance exported from ACTS.

`physicalRotationDerivative(axis,offset,tx,ty)` computes dm=axis cross
(measurement−current sensitive center), then (tx*dm_z−dm_x,
ty*dm_z−dm_y). Global Z uses the frozen reference slopes. In untilted Rz mode,
the bias derivatives reduce to (−offset_y,+offset_x). Fresh physical finite
differences and actual serialized binary entries test these signs and units.

| Label family + layer | Meaning and units | Physical Geometry increment |
|---|---|---|
| 1000 | Global X measurement bias, mm | −Pede parameter |
| 2000 | Global Y measurement bias, mm | −Pede parameter |
| 3000 | Global Z rotation bias, rad | −Pede parameter |
| 4000 | Global Z translation, mm | +Pede parameter |
| 5000 | Global X rotation, rad | +Pede parameter |
| 6000 | Global Y rotation, rad | +Pede parameter |

`Mille::spawnMilleRecord` and `addData` are official library APIs. The writer
uses single precision with zero derivatives omitted. It adds ten scalar rows
(two per SiMAPS plane), then calls `writeRecord()` **once per accepted track**.
A mutex protects records, and `flush()` closes out buffered writing. Processor
counters report accepted records/scalars separately from event counters.

Pede eliminates these four per-track local parameters and solves selected Global
labels with the constraints in the chosen `pede_*.txt`. The three-layer six-DOF
steering fixes L0/L4 X/Y and frees all six families on L1/L2/L3. Other mode
steerings can retain different historical nuisance parameters: do not assume
that the corrected scope equals every label appearing in a legacy solve.
`correction.scope` and canonical steering must agree.

`correct_so3` uses Rnew=Exp([delta_rx,delta_ry,delta_rz]) Rcurrent about the
current sensitive center, then Global translation. Matrices are state;
cumulative orientation diagnostics use Log(Rnew Rsurvey^T), not summed Euler
angles. All before/after reconstructions reuse the exact same RawHit bytes.
Geometry versions are SHA-derived immutable candidates with explicit parents.

Positions and translation corrections are mm; angles rad; fit q/p is GeV^-1;
ACTS time is ns; RawHit timestamp contract is ps and charge is keV-equivalent.
The current electron reconstruction explicitly selects PDG 11 and seed q/p=-1
for 1 GeV. Zero field and existing seed covariance remain unchanged. No ACTS
surface/volume material or process-noise model is introduced by blueprint
conversion; physical DD4hep solid thickness alone is not such a model.
SiMAPS supplies five 2D tracking/alignment measurements. MPGD/AC-LGAD RawHits,
RecHits and physical surfaces exist, but the electron configuration disables
them in fitting and neither is an alignment measurement in these modes.
ACTS stored nDoF counts calibrated dimensions (10 per five-plane track here),
not the straight-line statistical 10−4 degrees of freedom. Pede has additional
Global fitted parameters; its chi2/NDF need not equal ACTS chi2/stored-NDF.

## 6. Evidence, scope and source fingerprints

The integration report contains tested commands, tolerances, all changed files
and detailed results. Full evidence is intentionally **not in Git**:

- Phase 1: `result/upstream_acts_geometry_20261023_01/`, including pinned
  environment, installed patch contents, legacy-provider failures and 28
  unclosed component checks.
- Complete integration: `result/complete_acts_geometry_20261023_01/`, including
  four `*_final/geometry.json` reports, geometry_gate_final.json,
  reconstruction_comparison.json, corrected_comparison.json, alignment_pair.json,
  fit_metrics.json, gate.json, derivatives_L1/L2/L3/, noiseless/,
  l2_exact_replay.json, l2_regression/, blueprint_root/, and preservation reports.
- Saved input RawHits:
  `result/l3_six_dof_20261023_01/three_plane_smoke/step2_digitization/rawhits.edm4eic.root`,
  SHA-256 `1b54c7b5d91cc59fce1fb6dd1e5b9338c1d930db41369f7728f165d78942582e`.
  Its contract and Survey inputs are fully named in the integration report.
- Historical reference Simulation:
  `results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root`,
  SHA-256 `947fee1308b8aa27516c12711c9cdb5e4b4160da2371b7094491418e276ee7a0`.

Matched tested build: `build/complete_acts_geometry_20261023_01/`.
SHA-256 of BeamTestReco.so:
`cd9ab63b5126417c7cb273ed46297a83e68afcd39a28eed4b17dba3900bdbe41`;
of libLocalTelescopeGeometry.so:
`ddd1f02ad7dfe580800bdf25348707d317ecd420ba140f31b2333dff570c7c98`.
`gate.json` pins current implementation sources, physical derivative reports
and both binaries. `sources_final_sha256.json` in the integration evidence
contains the maintained source snapshot; the handoff separately checks it
before adding this guide. New documentation does not change those binaries.

Technically executed: 28/28 closed-surface comparisons, 16/16 installed-Navigator
rays, 95-track initial/refit comparison of 281 PODIO branches, identical initial
and corrected Mille bytes, equal Pede parameters and corrected XML. ACTS
chi2/stored-NDF changes 25.2814412 → 1.26428839 for either provider. Historical
local closure retains 99 tracks, +198.75 µm correction and exact PODIO/Mille
comparisons. Both optional-ON and default-OFF builds passed; unavailable
provider requests fail explicitly. Fresh tests cover all 18 derivative columns,
39 physical contexts/324 actual binary components, 11 noiseless SO(3) controls,
46 unit tests, syntax, safety and preservation. The previous report verified
45,469 protected artifacts unchanged. Source/plugin fingerprints were checked
again for this handoff; no new physics campaign was run.

Pede exits process 0 but reports end status 1, **bad-measurements warning**;
chi2/NDF=1167.4850613/552=2.11500917, with zero rejected local fits in the recorded
iteration history. This warning remains visible. Small chi2 and full numerical
rank do not certify Rx/Ry precision or nominal uncertainty coverage. Existing
L1/L2 uncertainty limitations, technically checked L1/L2/L3 prototype status,
the nonconverged three-iteration Controller pilot and large-initial-offset Pede
rejection remain. Old fixed-Global `l1_rx_ry` / `l1_l2_rx_ry` modes remain
disabled; no MPGD/AC-LGAD alignment or general ePIC tracking support is claimed.
No candidate is activated by the validation or this commit.

## 7. Next smallest useful milestone — recommendation only

First, use the existing manual local-versus-blueprint commands to inspect one
selected dataset's mapped sensor IDs, anisotropic measurement covariances,
state outputs and Mille rows. The next small code milestone should consolidate
the sensor association/measurement contract shared by the two providers:
explicit CellID→Volume ID→Surface ownership, local basis, covariance and
SourceLink identity. Retain exact local regression and semantic experimental
comparisons. That reduces duplicated telescope assumptions before attempting
broader ePIC measurement factories, which have their own detector-specific
initialization and covariance conventions.

Replacing DirectNavigator is supported as a **candidate investigation** by the
installed Gen3 Navigator and the independent traversal tests. It is not yet a
validated reconstruction change and is not necessary merely to consume the
converted surfaces. After association/measurement commonality, a narrowly
scoped TrackingGeometry-backed propagation/fitter comparison could test the
existing fixed-hit sample and predicted/filtered/smoothed states, holes,
material flags and Mille equivalence. Do not substitute the full official CKF
chain immediately or assume the legacy EICrecon provider is repaired.

MPGD/AC-LGAD integration depends first on detector-appropriate Digitization,
readout/uncertainty/timing and measurement dimensionality validation; the
present pixel-like MPGD path and seven-surface Geometry checks are insufficient.
Only then assess added tracking measurements and their observability/alignment
models. The researcher should perform the independent seed/statistics,
uncertainty coverage, weak-mode/correlation, capture-range and material/physics
studies. These scientific gates remain prerequisites for precision or detector-
general claims. None of these recommended developments is implemented in this
handoff.
