# Telescope alignment: source and processing map

Start with the [user guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md).
This map describes the actual opt-in telescope chain. It is distinct from the
production/reference BeamTestReco path and from standard ePIC reconstruction.
Official source comparisons use pinned EICrecon Git objects at
`195966d41899800eaeca6fbafd63cd53735e6543`, not the external checkout's current HEAD.

## Directory roles

| Directory | Role |
|---|---|
| `localDetEICrecon/experimental/telescope/` | JANA plugins, adapted official modules, telescope producers, provenance and patches |
| `validation/telescope_geometry/` | barrel-compatible telescope XML builder, technical metadata hook, geometry/navigation audit |
| `validation/telescope_one_track/` | independent standalone native CKF reference; not the event-processing path |
| `validation/telescope_factories/` | one-event PODIO fixture, EDM read-back, upstream patch regeneration |
| `validation/telescope_alignment/` | derivative gate, native/legacy comparison, mathematical Mille fixture and label map |
| `validation/telescope_closure/` | offline channels, bounded selected translation/SO(3) XML correction, stage driver and final validation |
| `localDetEICrecon/alignment/` | preserved historical BeamTestMilleWriter, used only for independent equivalence checks here |
| `geometry/`, `reconstruction/`, `alignment/`, `calibration/` | original stages and Python Controller; not replaced or activated |
| `environment/` | fixed Docker bridge and external dependency setup |
| `result/`, `build/` | ignored execution artifacts; historical names remain unchanged |

## Actual processing flow

```mermaid
flowchart TD
  G[Offline: nominal and displaced Truth XML] --> D[TelescopeChannels: actual sensor intersection and segmentation]
  D --> R[RawTrackerHit ROOT: immutable channels]
  R --> J[Fresh eicrecon: nominal Geometry]
  J --> H[Installed TrackerHitReconstruction]
  H --> M[Adapted TrackerMeasurementFromHits]
  H --> S[TelescopeSeed]
  M --> K[Adapted CKF wrapper]
  S --> K
  K --> A[Installed CKF, Navigator, filter and smoother]
  A --> E[Installed ActsToTracks and PODIO output]
  A --> N[TelescopeMille: native TrackStates]
  N --> B[Official Mille records]
  B --> P[External official Pede]
  P --> C[External bounded XML Geometry Correction]
  C --> F[Fresh eicrecon: corrected Geometry]
  R --> F
  F --> V[Closure checks and ROOT diagnostics]
  G -. Offline Truth for evaluation only .-> V
```

## Source, principal function and execution boundary

Paths below are relative to the repository root. `T/` means
`localDetEICrecon/experimental/telescope/`, `V/` means `validation/`.

| Source | Principal function / role | Execution |
|---|---|---|
| `V/telescope_geometry/prepare.py` | `prepare`: independent XML fixtures, real modules, metadata declarations | external Python |
| `V/telescope_geometry/BarrelMetadata.cc` | `initializeBarrelMetadata`: Tube layer metadata, sensor axis definitions, actual tracker/barrel flags | DD4hep XML initialization in each geometry process |
| `V/telescope_closure/TelescopeChannels.cc` | `main`: actual VolumeContext transforms, ray/sensor intersection, segmentation and ID checks | separate offline executable |
| `V/telescope_closure/closure.py` | `geometry_step`, `data_step`, `pack`: Truth XML and RawTrackerHit ROOT, separate Truth JSON | external Python |
| `T/TelescopeTracking.cc` | `InitPlugin`: JOmniFactoryGeneratorT collection wiring | eicrecon |
| installed `factories/tracking/TrackerHitReconstruction_factory.h` | official algorithm `process`: channels to TrackerHit, pitch/sqrt(12) errors and RawHit relations | eicrecon |
| `T/algorithms/tracking/TrackerMeasurementFromHits.{h,cc}` | `init`, `process`: SurfaceMap association, local Measurement2D and covariance | eicrecon |
| `T/factories/tracking/TrackerMeasurementFromHits_factory.h` | adapted official factory contract | eicrecon |
| `T/algorithms/TelescopeSeed.h`, `T/factories/TelescopeSeed_factory.h` | `process`: first/last reconstructed hits, outward direction and seed perigee at X=249 mm | eicrecon |
| `T/algorithms/tracking/CKFTracking.{h,cc}`, `CKFTrackingConfig.h`, corresponding factory | `init`, `process`: seed reference and hypothesis adapter to installed CKF | eicrecon |
| installed `ActsToTracks` and factory | native states/tracks to EDM trajectories, parameters, tracks and relations | eicrecon |
| `T/upstream_support/algorithms/meta/CollectionCollector.h` | official unchanged empty subset collector, no Truth association input | eicrecon |
| `T/FactoryAudit.h` | `Process`, `Finish`: actual native and EDM consistency, event diagnostics | eicrecon observer |
| `T/alignment/TelescopeMille.cc` | `TelescopeMilleProcessor::Process`, `Finish`: native measurement states to one Mille record per accepted track | eicrecon observer |
| `T/alignment/NativeMilleModel.{h,cc}` | `nativeEquation`: real ACTS propagation and transport/alignment derivatives | called inside observer and external derivative tests |
| `V/telescope_alignment/TelescopeMilleDerivatives.cc` | `main`: analytical/finite-difference gates on actual surfaces | external executable |
| `V/telescope_alignment/l1_l2_global_y.json` | labels 700102/700202 and explicit supported physical Global Y scope | observer configuration |
| `V/telescope_alignment/l1_global_rx.json`, `l1_y_rx_l2_y.json` | selected physical labels, rad unit, current-center pivot, Global left composition and actual L1 IDs | observer configuration |
| `V/telescope_closure/rotation.py` | `rotate_component`, `pose_checks`, `physical_derivatives`, `correct`, `check`: restricted SO(3) serialization and actual-Geometry/native-row validation | external selected-mode helpers |
| `alignment/pede.py` | `read_pede`: shared text parser, no legacy stage/scope imports | external Python, both workflows |
| `V/telescope_closure/closure.py` | `solve`: official Pede execution and independent Schur comparison | external Python/Pede |
| same | `correct`, `displaced_xml`: Pede text + nominal XML to separate corrected XML, no Truth | external Python |
| same | `reconstruct`: new OS process for each nominal/corrected/control pass | launches eicrecon |
| same | `check`: immutable channels, XML whitelist, data-only GLS, final Truth comparison and ROOT | external Python/PyROOT |
| same | `regressions`: 18 independent commands with separate logs and fresh reference builds | external driver |
| `V/telescope_one_track/TelescopeOneTrack.cc` | `main`: standalone native CKF benchmark | validation only |
| `V/telescope_factories/prepare.py`, `check.py` | minimal PODIO event and native/EDM reference comparison | validation only |
| `V/telescope_alignment/LegacyTelescopeCrosscheck.cc` | `main`: original writer in equivalent coordinates | validation only |
| `V/telescope_alignment/TelescopeMilleFixture.cc` | `main`: separate 16-ray mathematical fixture | validation only |
| `T/factories/SyntheticTrackerHits_factory.h` | benchmark-only synthetic producer; default original one-event path | validation only |

The dependency graph, not factory registration order, controls JANA execution.
Audit and Mille observers request the output collections. Channel closure explicitly
sets `channelInput=true` and both observers' `multipleEvents=true`; the default
one-event benchmark remains independent. Reproducible commands use one thread.

## Official versus local

| Category | Components and reasons |
|---|---|
| Reused unchanged, installed | DD4hep_service, ACTSGeo_service, ActsGeometryProvider, DD4hep converter, TrackingGeometry, SurfaceMap; TrackerHitReconstruction factory/algorithm; actual CKFTrackingFunction with EigenStepper/Navigator/filter/smoother; ActsToTracks; JOmniFactory/JOmniFactoryGeneratorT |
| Unchanged pinned header copies | `extensions/edm4eic/EDM4eicToActs.h` and `upstream_support/algorithms/meta/CollectionCollector.h`; installation lacks these headers. Replace with installed includes when provided and regression-tested |
| Official measurement copy, locally modified | optional B0 constant lookup avoids inventing an absent detector; missing VolumeContext guard; system31/SiMAPSHits CartesianGridXZ covariance projection maps packed sensor X/Z variances into ACTS u/v through J C J^T. Upstream needs equivalent optional detector handling and covariance semantics before direct replacement |
| Official CKF wrapper copy, locally modified | namespace/includes and installed interface adaptation; each seed's perigee is honored instead of assuming origin; electronHypothesis option defaults false, explicitly true for this telescope. Installed numerical CKF is reused. Replace when upstream respects the same seed reference and particle hypothesis |
| Telescope-specific | collection wiring, metadata hook, reconstructed-endpoint seed, native Mille observer, offline channel fixture, bounded two-sensor correction and validation |
| Historical/reference | BeamTestReco, BeamTestACTSFitter, BeamTestMilleWriter, tilt/SO(3) model, original stages/Controller. Preserved unchanged; the new native chain does not substitute these for official tracking |

Official seeding assumes beamline/circle-curvature information and cannot directly
supply this radial, zero-field telescope seed. `TelescopeSeed` is a deliberately
small adaptation, not a new fitter. q/p=-1/GeV is a 1 GeV electron beam prior,
not a measured momentum. Replacing a module requires matching coordinates,
covariance, hypothesis, reference surface and collection contracts, not just types.

Provenance, licenses and reproducible patches live under `T/`. Regenerate patches
using the read-only upstream Git checkout and a new output directory:

```bash
python3 validation/telescope_factories/upstream_diff.py \
  --source /Users/tkumaoka/eic/EICrecon --output result/telescope_upstream_review_fresh
```

The checkout path is an explicit local argument, not a build dependency. Compare
the generated files with `localDetEICrecon/experimental/telescope/upstream_diffs/`.

## Measurement equations and Geometry Correction

The actual native TrackState SourceLink indexes Measurement2D; its hit relation
leads to CellID, converter VolumeID and official SurfaceMap. VolumeID and closed
ACTS GeometryIdentifier are checked for consistency and are not assumed identical.
The earliest accepted smoothed state supplies the common bound reference.
`nativeEquation` repropagates with ACTS, takes transport derivatives for four local
parameters (loc0,loc1,phi,theta), and uses Surface::alignmentToBoundDerivative
including path correction. Local right rotation increments map to Global left
increments through R^T. Enabled scopes are two Global Y translations, separate
L1 Rx/Ry/Rz, L1 Y/Rx plus L2 Y, coupled L1 Ry/Rz, bounded L1 Rx/Ry/Rz, and
bounded L1 Global Y plus Rx/Ry/Rz. The contained four-parameter fixture has six
completed closures; the original wider fixture retains its 5/6 result and one
physical refusal. The new simultaneous L1 four-parameter plus L2 Y scope is
validated experimentally for one prospective cohort, as described below. Other
free translations are not established by that scope. The eight-parameter L1/L2
Y/Rx/Ry/Rz route has passed full closure for four signed fixtures from two
independent seeds. This is validated experimental functionality for the stated
material-free synthetic-channel conditions, not arbitrary six-DOF support.

The equation is measured-minus-prediction = A*localDelta + G*alignmentDelta.
Whitening uses the original calibrated covariance C=L L^T and W=L^-1 for residual
and both Jacobians; official Mille receives scalar sigma=1. Smoothed covariance
is not substituted for measurement errors, and no seed-prior equations are added.
Pede profiles four local parameters per track and solves the shared global
labels in the selected explicitly whitelisted scope.
Nonzero field, assigned material and observable q/p/time contributions are guarded
as unsupported. Derivative validation alone does not establish general six-DOF closure.

`correct` reuses `alignment.pede.read_pede`; `displaced_xml` reuses
`geometry.transforms.matvec/transpose` to map physical Global Y into module axes.
Only selected module references, sensitive-component translations and the selected
sensitive-component orientation serialization change; all
other XML attributes/text are whitelisted. Same channel bytes are decoded again
in a fresh process. No Controller registry or Geometry activation is involved.
The historical writer remains an independent straight-line equivalence reference.

ACTS stored NDF counts measured dimensions (10 per track). Pede statistical NDF
is N*(10-4)-G for N accepted tracks and G free global parameters; the original
32-track/two-Y reference has 32*(10-4)-2=190. Native CKF includes the seed prior;
profiled Pede does not.
Their chi2 values and denominators therefore have distinct meanings. No covariance
rescaling or uncertainty-coverage claim follows from the successful closure.

## Historical terminology

Historical `BARREL_*` report filenames and `result/barrel_*` directories record
past executions and remain intact. Their old source commands refer to that revision;
this guide and code map provide current paths. Technical names retained include
`BarrelMetadata.cc`, `TestbenchBarrelMetadata`, `initializeBarrelMetadata`,
`DD4hep_SiTrackerBarrel`, XML `barrel_envelope`, ACTS CylinderLayer and unchanged
official ePIC barrel detector constants. The existing manifest key `barrel_field`
is retained for output-schema compatibility. None implies that the physical
beam-test telescope is the ePIC barrel detector.

## Consolidation boundary

The [implementation audit](TELESCOPE_IMPLEMENTATION_AUDIT.md) inventories retained
modules, dependencies and deleted duplicate build entries. This synthetic-channel
closure is the active EICrecon-based development workflow. The old endcap backend
remains a capability/reference implementation: its validated rotations, SO(3),
Geant4/digitization and sequential Controller lifecycle are not yet replaced by
these selected material-free native fixtures. Do not infer that those features are
available in this native chain. No automatic Geometry activation is provided.

The Pede text parser now lives in `alignment/pede.py`; it has no dependency on the
legacy solver CLI or correction scopes. `alignment.align.read_pede` remains an
import-compatible alias for external callers. Pede itself is still the official
external executable, not Python numerical inference.

## Native rotation milestone

The [parity report](TELESCOPE_ALIGNMENT_LEGACY_PARITY.md) distinguishes the legacy
fixed-ordered Rx/Ry failure, later SO(3) controlled results, incomplete three-layer
claims and the native tests. `TelescopeMilleProcessor::Init` accepts only the
explicit label sets; `Process` selects column 1 (Y) or columns 3/4/5 (Rx/Ry/Rz) from
the **unchanged** `NativeMilleModel` after its original whitening. Config parameters
and decoded Mille labels are authoritative for a multi-parameter sensor; the old
scalar equation `label` field remains for the original Y-only comparison.

`TelescopeChannels::main` now also reports actual DD4hep basis columns.
`closure.py::displaced_xml` permits selected L1/L2 sensitive-component rotations
for bounded geometry validation and preserves untouched
XML attributes in rotation fixtures. `geometry_step` generates test Truth;
`rotation.correct` reads Pede and nominal XML only. The same native reconstruction
is then restarted with corrected Geometry. `rotation.physical_derivatives` is an
independent finite-difference validator of actual sensor poses and frozen native
references; it is never an inference model. Existing generic mathematical gates,
standalone CKF and legacy-equivalence tests remain independent.

Single-axis routes retain their restricted charts; coupled routes compute a
full SO(3) target matrix before XML serialization. Arbitrary Survey Geometry,
fitted Global X/Z combined with tilts, multi-layer six-DOF, sequential Controller
operation and original Geant4/RawHit compatibility remain unrestored. The retained legacy implementation is unchanged.

## Bounded three-rotation extension

`rotation.py` routes `l1_rx_ry_rz` and its negative fixture through the same
native channel/CKF/Mille chain. `TelescopeMille::Init` admits exactly labels
700104/700105/700106 for this scope; `NativeMilleModel` still supplies physical
Global rotation columns 3/4/5 without modification. Translations and other
sensor poses remain fixed. The XML serializer computes the full left-Global
target matrix before extracting the verified DD4hep component chart. It is
restricted to this telescope mounting and bounded poses, not arbitrary Survey
Geometry. See the [three-axis validation](TELESCOPE_ALIGNMENT_LEGACY_PARITY.md#three-axis-native-so3-milestone)
for prospective gates, actual results, regressions and remaining legacy gaps.

## Explicit L1 Y plus SO(3) validation

This remains experimental: the six-case checkpoint is 5/6 complete closures, with
one physically invalid fitted module candidate correctly refused. No native
full-six-DOF or unconditional four-parameter support is claimed.

The exact four-label configuration `l1_global_y_rx_ry_rz.json` enables Global Y
(column 1, mm) alongside the existing rotation columns 3/4/5 (rad). Other physical
parameters remain fixed. `rotation_labels` separates the angular coordinates
from translation; `fixture_shifts` supplies the world displacement. The existing
native matrix, transport, whitening, fitter and selector are unchanged.

`rotation.refine` implements an explicitly requested second Geometry correction
for bounded selected Y/SO(3) scopes. It reads the completed first post-correction Pede result,
updates the current center and left-multiplies its current orientation, and
reloads the XML for actual surface checks. Exclusive immutable stages limit this
to one additional correction. `closure.main --refine-once` connects its separate
reconstruction/derivative/Pede stages. It does not extend the Controller or
activate Geometry. `rotation.check` retains the initial covariance, scores the
final pose and updates using unchanged gates, and records the initial one-step
outcome independently. See the parity report for the scope amendment and limits.

## Unchanged-envelope fixture and permanent physical refusal

`rotation.is_four` recognizes two additional **fixture aliases**,
`l1_y_rx_ry_rz_contained` and its negative form. They select the same four labels
and native equations; only their physical injection is different. Original mode
amplitudes and numerical baselines remain unchanged. New fixtures compare
like-signed Euler products with their joint Exp(w); historical diagnostic values
are retained. This changes no fit or SO(3) update primitive.

`validation/telescope_closure/containment.py` is a validation utility, not an
alignment constraint or tracking component. `corners_in_module` independently
transforms all eight silicon corners into the parent frame. `preflight` uses
prior joint information for a geometry-only design and actual constructor
reloads. `expected_refusal` re-solves the preserved original Mille Binary,
verifies the original fit byte-for-byte, reloads its candidate, and requires
`pose_checks` to refuse it before any corrected tracking. It also verifies that
the original failed fit remains in the initial statistical summary.
The permanent classification is `EXPECTED_PHYSICAL_CONTAINMENT_REFUSAL`, with
`physical_closure_passed=false`. Three new beam recipes provide independent
seeds without changing the existing angular distribution. Four unit tests cover
parent-frame invariance, first-order extent, joint-error sampling, and original
fixture/label preservation. No runtime provider, navigator, fitter or solver is
added; the numerical C++ tree is unchanged from the starting uncommitted feature.

## Bounded L1/L2 selection: five-parameter development scope

Scope A selects L1 Global Y/Rx/Ry/Rz and L2 Global Y together. Its explicit mode
is `l1_y_rx_ry_rz_l2_y`, with `_negative` selecting the opposite L1 rotation
vector while retaining both translations. This section describes the implemented
route; full closure passed for one prospective 4096-track cohort and
is recorded separately in the parity report. It does not declare eight-parameter
or arbitrary six-DOF alignment support.

| Maintained module | Responsibility |
|---|---|
| `localDetEICrecon/experimental/telescope/alignment/TelescopeMille.cc` | Validate the selected configuration, identify each actual native measurement sensor, and write only that sensor's selected global columns to official Mille Binary. |
| `validation/telescope_alignment/l1_y_rx_ry_rz_l2_y.json` | Declare five physical labels, units, pivots, composition and distinct actual sensor identities. |
| `validation/telescope_closure/multi_sensor.py` | Decode the bounded label selection, define signed fixtures, separate per-sensor increments, check XML changes and validate physical composition/inverse operations. |
| `validation/telescope_closure/multi_information.py` | Profile four local parameters from actual native equations; report accumulated information, covariance, cross-sensor correlations, sample-size/beam subsets, omitted-X/Z diagnostics and reference-release gauge directions. |
| `validation/telescope_closure/multi_preflight.py` | Read unchanged module/layer bounds and earlier native information; sample a joint-error design before new recovery, then reload actual DD4hep/ACTS poses. |
| `validation/telescope_closure/closure.py` | Keep the existing independent geometry, data, reconstruction and official Pede stages; dispatch the selected scope and enforce observability before Pede. |
| `validation/telescope_closure/rotation.py` | Reuse matrix-first correction, actual pose/containment checks, finite-difference validation, optional single additional correction, native coefficient auditing and ROOT closure output. |
| `validation/test_native_multi_sensor.py` | Test label/sensor separation, shared-module isolation, independent translations, noncommuting composition, fixed-sensor protection and refusal of unrelated XML changes. |

The actual association remains:

```
native TrackState SourceLink
  -> Measurement2D index -> associated hit CellID
  -> DD4hep converter Volume context -> official SurfaceMap
  -> the identical native reference Surface and GeometryIdentifier
  -> selected configuration entries for that physical sensor
  -> original native global derivative columns -> original whitening -> Mille
```

The L1 VolumeID/ACTS GeometryIdentifier pair is
`272631839 / 216173056991691039`; the independently discovered L2 pair is
`272633887 / 216173194430644511`. These are different identifier spaces and
different sensors. Labels 700102/700104/700105/700106 map to L1 columns 1/3/4/5;
700202 maps to L2 column 1. Columns are zero-based Global X/Y/Z/Rx/Ry/Rz.
Fixed L0/L3/L4 measurements retain local track information and have no selected
free global coefficients. Native SourceLinks, CellIDs, SurfaceMap associations
and configured identities are checked at runtime rather than inferred from the
label value alone.

The installed EICrecon geometry service/`ActsGeometryProvider`, DD4hep conversion,
official SurfaceMap, native measurement conversion and installed ACTS CKF path
are unchanged. `NativeMilleModel` equations, calibrated covariance/whitening,
four-local-parameter model, electron hypothesis, CKF selection and official
Millepede-II steering are also unchanged. No provider, navigator, fitter or
solver is added by these Python validation helpers.

Both sensors' corrections come from one simultaneous Pede result. Each selected
sensitive component is isolated by cloning its placed shared module definition;
unrelated module templates, placements and material/segmentation/envelope nodes
remain exact. For each sensor the update is
`c_new=c_current+(0,dY,0)` and `R_new=Exp(dw_global) R_current`, about its current
physical sensitive center. L2 has no rotation increment in Scope A. The current
orientation is serialized from the target matrix, then freshly loaded DD4hep
and ACTS matrices, IDs and all eight sensitive corners are checked before
corrected reconstruction can start. An invalid candidate is preserved and
refused rather than clipped or accommodated by enlarging its mother.

Gauge handling is explicit fixed-reference selection, not a hidden prior:
L0/L3/L4 poses and L1/L2 X/Z stay fixed. Actual local rank must be four per track;
individual tracks need not resolve every global parameter. The accumulated
selected design must have rank five and satisfy the existing scaled-condition
and sensitivity gates before Pede. Releasing all reference poses is a separate
diagnostic that exposes common rigid gauge directions; those extra columns are
never fitted or used to regularize the selected model. Prospective ellipsoid
sampling is engineering evidence, not uncertainty coverage. The optional
`--refine-once` stage retains the existing 20 nm translation and quarter-initial-
sigma angular post-update gates and permits at most one additional correction.
No Controller iteration, Geometry activation or full six-DOF mode is introduced.

The Scope A audit uses the following manual inputs. Existing output directories
are immutable: use a new suffix for each output path when reproducing these
commands. The fixed Docker container name is an explicit local environment
choice.

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_multi_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/native_multi_20261024_01 -j2

TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B validation/telescope_closure/multi_preflight.py \
  --build build/native_multi_20261024_01 \
  --prior-run result/native_containment_seed1_positive_20261024_01 \
  --output-dir result/native_multi_20261024_01_audit/geometry_preflight \
  --mode l1_y_rx_ry_rz_l2_y

TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B validation/telescope_closure/closure.py \
  --build build/native_multi_20261024_01 \
  --result result/native_multi_scope_a_seed1_positive_20261024_01 \
  --mode l1_y_rx_ry_rz_l2_y --events 4096 \
  --beam validation/telescope_alignment/multi_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

The same invocation accepts each independent `--step` in place of `all`:
`geometry`, `data`, `nominal`, `solve`, `correct`, `corrected`, `postsolve`,
`refine`, `refined`, `refinesolve`, `control`, `controlsolve`, `check`.
Each requires complete, unmodified preceding artifacts and creates fresh stage
outputs. `solve` also performs the real-geometry derivative/pose gates. The
read-only `multi_information.py --native RUN/nominal/mille.json --output NEW.json`
command exposes the selected and diagnostic designs independently. The final
`validation/report.json` and `validation/rotation.root` retain closure metrics
and ROOT histograms; they distinguish initial nominal covariance from final
cumulative geometry without combining correlated successive-fit errors.

## Eight-parameter L1/L2 development scope

Scope B uses `l1_l2_y_rx_ry_rz` and its `_negative` fixture. Its implementation
reuses the Scope A helpers and native path; all four selected signed fixtures
passed full reconstruction closure. The additional explicit configuration is
`validation/telescope_alignment/l1_l2_y_rx_ry_rz.json`. No new geometry provider,
navigation, fitter, derivative model or solver is introduced.

| Physical sensor | Global Y [mm] | Global Rx [rad] | Global Ry [rad] | Global Rz [rad] |
|---|---:|---:|---:|---:|
| L1, VolumeID 272631839 / ACTS ID 216173056991691039 | 700102 | 700104 | 700105 | 700106 |
| L2, VolumeID 272633887 / ACTS ID 216173194430644511 | 700202 | 700204 | 700205 | 700206 |

`multi_sensor.labels`, `mapping` and `pose_increments` keep each sensor's three
rotation components together and reject incomplete or nonfinite updates. The
runtime observer still verifies the actual SourceLink/CellID/VolumeID/SurfaceMap
association before selecting columns 1/3/4/5 for that sensor. Fixed reference
layers L0/L3/L4 retain no free global labels, and both sensors' X/Z stay fixed.
The Scope A label list and physical fixture remain unchanged.

One eight-parameter Pede solution updates both sensitive components in separate
placed module clones. Each update uses its own current center and current
orientation: world Y translation followed by the independent active left-Global
`Exp(dw)` multiplication. The shared original template and unrelated XML remain
exact; matrix serialization, actual DD4hep/ACTS reloads and all eight daughter
corners in both unchanged mothers/layers are checked. The actual-geometry
finite-difference gate selects all eight sensor/column pairs at three step sizes
per parameter, using each event's frozen native reference and the corresponding
sensor's original ACTS derivative. Cross-sensor coefficient auditing separately
checks every scalar official Mille record.

The fitted information matrix is eight by eight after profiling four local
track parameters independently per event. Its full covariance, axis and
cross-sensor correlations, prefix sample sizes and slope/impact subsets come
from the original calibrated measurement covariance. A separate twelve-column
L1/L2 diagnostic adds omitted pose components including X/Z; a thirty-column
diagnostic releases all five SiMAPS reference poses and tests rigid gauge
directions. Those diagnostic columns do not enter Pede or supply priors.
Accumulated rank eight, the existing scaled-condition/sensitivity limits and
fixed-reference/gauge consistency are required before the eight-label Pede fit.

The independent information calculation and Pede both profile data-only local
track corrections; no CKF seed-prior equations are added to Mille. Initial
nominal Pede errors must agree with the unscaled inverse information from the
same initial native equations. Later relinearized errors describe their current
linearization and remain separate from the initial errors; same-channel fit
uncertainties are never combined as independent measurements. Geometry closure
and stable post-updates alone do not establish uncertainty coverage or absence
of statistical bias. Pede's statistical NDF is `6*N-8`; ACTS stored NDF remains
ten measured dimensions per track.

The prospective fixture keeps L1 (Y,Rx,Ry,Rz) at
(+0.080 mm,+1.0,+0.5,-0.5 mrad), and sets L2 to
(-0.060 mm,-1.2,+0.6,+0.6 mrad). The negative fixture reverses both rotation
vectors while retaining the translations. Both signed fixtures are checked
before new Pede recovery, using the recorded earlier information and unchanged
physical bounds. These are bounded geometry-validation fixtures, not a claim
of arbitrary detector-motion support.

The primary Scope B run uses seed 2026102701 with the same bounded broad-angle
recipe. The current reconstruction build, including the observer-only precision
correction described below, is `build/native_multi_precision_20261024_01`;
the primary retry is `result/native_multi_scope_b_seed1_positive_20261024_02`.
The following is a **fresh reproduction recipe**, not the command history of
that retry. It uses the unused example output
`result/native_multi_scope_b_reproduce_01` and the recorded final build path;
choose a fresh build suffix when rebuilding rather than replacing that build.
The preflight output is also a new example. The actual prospective preflight
was executed earlier with `build/native_multi_20261024_01`, using the unchanged
`TelescopeChannels` geometry probe. All independent stage names remain available
through `closure.py --step`.

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_multi_precision_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/native_multi_precision_20261024_01 -j2

TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B validation/telescope_closure/multi_preflight.py \
  --build build/native_multi_precision_20261024_01 \
  --prior-run result/native_containment_seed1_positive_20261024_01 \
  --output-dir result/native_multi_scope_b_preflight_reproduce_01 \
  --mode l1_l2_y_rx_ry_rz

TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B validation/telescope_closure/closure.py \
  --build build/native_multi_precision_20261024_01 \
  --result result/native_multi_scope_b_reproduce_01 \
  --mode l1_l2_y_rx_ry_rz --events 4096 \
  --beam validation/telescope_alignment/multi_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

The actual primary retry did **not** execute `--step all`. It copied the
hash-verified immutable inputs and completed geometry, nominal/first-corrected,
derivative, solver and refinement checkpoints from the original `_01` attempt
to `_02`; their original command records were retained. It then executed only
the following five stages with the corrected observer. The source attempt and
its partial failure remain intact. This is the same seed/sample, not new
simulation or another independent statistical observation. The copy hashes and
stage inventory are recorded in
`result/native_multi_20261024_01_audit/primary_retry_provenance.json`.
The loop below records the executed invocations; the completed `_02` stages
must not be rerun in place.

```bash
for step in refined refinesolve control controlsolve check; do
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
    python3 -B validation/telescope_closure/closure.py \
    --build build/native_multi_precision_20261024_01 \
    --result result/native_multi_scope_b_seed1_positive_20261024_02 \
    --mode l1_l2_y_rx_ry_rz --events 4096 \
    --beam validation/telescope_alignment/multi_beam_seed1.json \
    --chi2-cut 1000 --refine-once --step "$step"
done
```

The prospective plan and all validation artifacts reside under
`result/native_multi_20261024_01_audit/` and the separate Scope B run directory.
No candidate is activated, the Controller is unchanged, and no additional
sensor, X/Z fit or full six-DOF scope is enabled by this development.

The final Scope B checkpoint contains four passing signed fixtures, each with
4096 accepted tracks, from seeds 2026102701/2026102702. The two signs share their
seed's rays; there are two independent cohorts, not four. Initial selected rank
is eight and scaled conditions span 3.1652–3.2946. ACTS chi2/stored-NDF improves
from 10.1045–10.1756 to 0.5931–0.6048. All 16 Pede stages terminate normally with
zero rejected local fits and no error rescaling. All proposed updates retain
the unchanged physical containment and original post-update gates. The twelve
real-geometry derivative gates total 1179648 two-coordinate vector checks;
maximum errors are 3.310e-8 mm/rad and 5.460e-10 mm/mm. Results, initial mixed-unit
covariances, cross-sensor correlations and cumulative geometry are retained in
`result/native_multi_20261024_01_audit/scope_b_four_fixture_summary/summary.json`.
These are geometry/derivative/observability/closure results, not statistical
coverage or a material-aware performance validation.

## Observer precision contract and independent geometry check

`FactoryAudit::Process` is an observer; it does not fit tracks or mutate event
data. An initial Scope B refined-reconstruction attempt was stopped by its
fixed `1e-6 mm` local-coordinate difference-norm assertion. The retained event
355 L2 measurement has legitimate double-to-binary32 rounding with norm
`1.019234011353496e-6 mm`, although each coordinate is within half its float ULP.
Actual partial ROOT output confirms the stored coordinates. The original
failure and its diagnostic artifacts remain under the original `_01` run and
`result/native_multi_20261024_01_audit/measurement_precision_diagnosis/`.

The corrected observer checks the official converter's exact contract:
`static_cast<float>(local[0]) == measurement.getLoc().a` and the corresponding
`local[1]`/`.b` identity, together with finite coordinates and the unchanged
Surface identity check. The converter already
performs this explicit cast when creating `Measurement2D`. This detects a
one-ULP corrupt value even where its absolute difference is below the old
threshold; it does not add an adjustable tolerance. Installed ACTS PlaneSurface
conversion ignores the momentum direction, so the observer and converter use
the same coordinate transform.

A separate strict geometry check now starts from the unrounded DD4hep CellID
channel-center position: convert it to ACTS local coordinates and back to
global coordinates, requiring the full round-trip error below `1e-6 mm`.
This tests the physical DD4hep/ACTS plane correspondence before EDM rounding.
It does not require a float-serialized global hit position to have double
precision. Covariance checks, all-eight-corner containment, fitted states,
measurement conversion, tracking algorithms, Mille equations and physics
settings are unchanged. The actual ROOT/EDM unit test retains the failed
coordinate pair and demonstrates that legitimate rounding and one-ULP
corruption remain distinguishable.

The fresh precision build passed the complete 18-command regression suite at
`result/native_multi_regression_l1_l2_y_20261024_01/precision_complete_regressions/`:
all 18 recorded exit codes are zero and the immutable completion marker is
present. This includes fresh standalone geometry/CKF builds, geometry and EDM
comparisons, native/legacy mathematical equivalence, official Pede, all 91 unit
tests (17 multi-sensor tests), and safety/preservation checks. Existing SQLite
ResourceWarnings remain visible in the test log. Preservation verifies 221
baseline records, 2046 relocated files, maintained input links and pinned
validated sources. Safety checks retain their refusal cases for overwrites,
incomplete/modified stages, escaped paths, invalid scenarios and ungated legacy
alignment entry points. These software checks do not by themselves declare
full Scope B reconstruction closure or statistical validity.

The following checks can also be run independently in the fixed container.
The consolidated command uses the completed original two-Y baseline and creates
a fresh validation stage and fresh standalone build directories; change
`--validation-name` before repeating it.

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B -m unittest discover -s validation -p 'test_*.py'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B -m unittest validation.test_native_multi_sensor -v
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B validation/check_safety.py
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B validation/verify_preservation.py
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 -B validation/telescope_closure/closure.py \
  --build build/native_multi_precision_20261024_01 \
  --result result/native_multi_regression_l1_l2_y_20261024_01 \
  --mode l1_l2_y --events 32 --chi2-cut 1000 \
  --step regressions --validation-name precision_complete
```

Every consolidated subcommand has its exact arguments, working directory,
stdout/stderr and exit code in its own `command.json`, `stdout.log` and
`exit.json`. The audit-only correction is isolated in `FactoryAudit.h`; it
does not change an installed EICrecon/ACTS component or replace the retained
failed reconstruction outputs.

The twelve historical modes and six contained L1 four-parameter fixtures also
passed complete closure using the Scope A build, with protected XML/Mille bytes
and scientific reports unchanged except regenerated ROOT container metadata.
The final precision-build plugins were then executed over every event of those
18 final-geometry datasets plus Scope A: 19 separate replay jobs and 49280
events. Every full Mille Binary is byte-identical, and all ACTS fitted states
and audit values match. Only the explicitly verified fresh `derivative_gate`
output-path metadata is excluded when comparing the native equation JSON; no
numerical field is excluded. This final-build replay complements the earlier
full closure reruns; it is not described as nineteen new complete closures.
Evidence is recorded in
`result/native_multi_20261024_01_audit/baseline_identity.json` and
`result/native_multi_20261024_01_audit/final_plugin_full_replay_summary.json`.
