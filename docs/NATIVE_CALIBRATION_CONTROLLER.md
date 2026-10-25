# Bounded native Calibration Controller

For the maintained complete npsim-to-calibration command, start with the
[practical user guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md). The new public
`calibration.workflow` entry calls this Controller; it does not replace it.
The configured `l1_y` example selects only Global Y on SiMAPS L1.

The established strict policy remains the default. Explicit
`start --validation-mode diagnostic --geometry-aware-holes` enables an offline
investigation: actual finite sensitive crossings replace the synthetic-only
hole expectation, and a recognized high-chi2 Pede advisory can be retained while
evaluating an unapproved physical candidate. Zero local-fit rejection, exact
detector associations, RawHit integrity, finite/full-rank information,
independent Pede agreement and containment remain hard requirements. Precision
targets are reported as quality warnings; no error scaling is performed.
Unknown solver warnings and statuses still stop.

Diagnostic terminal reports distinguish `engineering_success` from
`physics_validation: not_validated`. A bounded `iteration_limit` can publish an
unapproved technical candidate only after at least one correction and a fresh
completed reconstruction. No diagnostic candidate is activated. Same-data
convergence alone does not establish accuracy or uncertainty coverage. The
[current workflow report](NATIVE_WORKFLOW_VALIDATION.md) is separate from the
historical numerical protocols retained below.

The native Controller operates on one immutable `EventHeader,TelescopeChannels`
ROOT file, an initial DD4hep XML file, and an already validated alignment
configuration. It does not read injected displacements, generate channels,
implement a track fitter, or activate Geometry. This milestone is a sequential,
offline technical prototype, with zero field and no assigned ACTS material.
It does not establish beam-test input compatibility or uncertainty coverage.

The independent [native npsim/Digitization adapter](NATIVE_GEANT4_WORKFLOW.md)
can now supply explicitly selected Geant4-derived RawHits. Pass its receipt
with `--input-provenance`: the Controller verifies the exact ROOT/payload hashes,
snapshots and seals the receipt, and marks subsequent reconstruction audits as
Geant4 input. Its metadata is not an alignment observation or stopping target.
The numerical operations and established strict acceptance gates are retained. The linked
report distinguishes actual transport/integration results from successful
calibration and records any refusal; earlier sections retain their original
synthetic milestone scope.

## Executable flow

`python3 -m calibration.native_controller start` first checks the native
collection contract and reads all channel payloads before creating the run
directory. Startup can therefore take time before any run directory appears.
It then snapshots the three inputs, records implementation/build/runtime
hashes, and acquires the retained `queue_manager.exclusive` lock. The retained
`runner.stage` starts a separate Python process group for every operation,
inherits the lock descriptor, and preserves its command, PID/group, output log
and exit status under `jobs/`. It terminates the whole stage group on a handled
interruption. The process layout remains compatible with `recover_guard`.

Each evaluation invokes the following functions. Operations are shared through
`calibration.native_operations`; metrics and policy remain in their explicitly
named Controller/convergence modules:

1. `geometry_audit`: zero-event `TelescopeChannels` constructor audit. No events
   are generated; the actual seven DD4hep/ACTS poses and IDs are read back.
2. `reconstruct`: derivative gate and fresh `eicrecon` process with installed
   `dd4hep`, `acts`, `algorithms_init`, `beam`, `podio`, `TelescopeTracking` and
   `TelescopeMille`. The actual installed geometry service, SurfaceMap,
   measurement conversion and CKF path are unchanged. The copied official
   factory/algorithm adaptations remain those documented in the Code Map.
3. `physical_derivatives`: the existing actual DD4hep/ACTS central-difference
   checks at three step sizes per selected component, holding the native
   reference line fixed. This runs before Pede on every evaluated Geometry.
4. `solve`: the existing native Mille decoding, four-local-parameter profiling,
   selected/full-design information gates, official `external/install/bin/pede`,
   printed-precision solution and nominal-error checks. Steering remains
   `entries 5`, `method inversion 3 0.001`, and positive pre-sigmas of one.
5. `native_controller.summarize`: check all official binary coefficients, calibrated covariance,
   track/measurement identities, residuals, solver status/rejections and profiled
   chi2. It never uses Truth residuals.
6. `calibration.convergence.evaluate_native`: decide same-data consistency or bounded exhaustion.
7. If another correction is required, `correct` applies world Y translation and
   `R_new = Exp(delta_omega_global) R_current`, then checks the selected-node XML
   whitelist, actual constructor poses, unchanged IDs, and original module and
   cylindrical-layer containment. Only a physically valid candidate can become
   an internal checkpoint for the next fresh reconstruction.

The manual closure wrappers now call the same numerical operations. They retain
fixture creation, Truth checks, mode/event/selection guards and the original
explicit one-extra-correction contract. The extraction preserves numerical
accumulation order, equations, steering, serializers and fitter settings.

## Supported selection and input

`--config` must equal one of the maintained explicit configured native scopes:

| Configuration in `validation/telescope_alignment/` | Free components |
| --- | --- |
| `l1_global_y.json` | L1 Global Y only |
| `l1_y_rx_ry_rz_l2_y.json` | L1 Y/Rx/Ry/Rz; L2 Y |
| `l1_l2_y_rx_ry_rz.json` | L1/L2 Y/Rx/Ry/Rz |
| `l1_l2_y_rx_ry_rz_l3_y.json` | L1/L2 Y/Rx/Ry/Rz; L3 Y |
| `l1_l2_l3_y_rx_ry_rz.json` | L1/L2/L3 Y/Rx/Ry/Rz |

No arbitrary parameter selection is enabled. L0/L4 remain reference sensors;
Scope A/B also retain L3 as a fixed reference.
Global X/Z translations remain fixed. Units, labels, sensitive-center pivots,
VolumeIDs and GeometryIdentifiers must agree with the maintained configuration.
The current native input adapter requires five SiMAPS channels per event and
exactly `EventHeader,TelescopeChannels` collections. It is distinct from the
legacy Geant4/RawHit delivery contract. A real-data adapter is future work.

## Commands

Use unused build/result names. The local reference datasets below are excluded
from Git and must be supplied separately with their recorded checksums.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_controller_20261025_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_controller_20261025_01 -j2

bash environment/run.sh python3 -B -m calibration.native_controller start \
  --run result/native_controller_scope_d_default_20261025_02 \
  --raw result/native_three_sensor_scope_d_seed1_positive_20261024_01/data/shifted.root \
  --geometry result/native_three_sensor_scope_d_seed1_positive_20261024_01/geometry/fixtures/nominal.xml \
  --config validation/telescope_alignment/l1_l2_l3_y_rx_ry_rz.json \
  --build build/native_controller_20261025_01 --events 4096 --chi2-cut 1000

bash environment/run.sh python3 -B -m calibration.native_controller status \
  --run result/native_controller_scope_d_default_20261025_02
bash environment/run.sh python3 -B -m calibration.native_controller verify \
  --run result/native_controller_scope_d_default_20261025_02
```

`status` verifies sealed input/checkpoint artifacts. `verify` additionally checks
original inputs, source-set identity and build/runtime files. `resume` performs
the same integrity checks and starts a new attempt, never overwriting an
incomplete iteration. Changed data/configuration/implementation/binaries require
a new run. Completed terminal checkpoints can repair interrupted final
publication without rerunning numerical operations.

```bash
bash environment/run.sh python3 -B -m calibration.native_controller resume \
  --run result/MY_INTERRUPTED_RUN
```

A stale `controller.guard` deliberately prevents reuse after abrupt process
death. Inspect the retained owner and all stage process groups. Explicit
`recover-lock --run ... --reason "..."` refuses a live owner, another host, or
any live recorded group. It does not clear a guard merely because time elapsed.

## Convergence and iteration convention

`iteration` counts **applied corrections**. The initial fit has count zero.
Defaults are minimum one, maximum three corrections. Certifying the last
candidate requires another fresh reconstruction/Pede evaluation, so the hard
bound is four evaluations for three corrections. The maximum never silently
becomes an unlimited iteration loop.

Initial data-only profiled information `H0`, its inverse covariance and formal
errors `sigma0` stay fixed throughout the run. Every fit's own information,
errors, covariance and correlations are saved separately. They are not summed
as independent estimates. Cumulative orientation is calculated from actual
matrices; reported rotation logs are not sums of Euler angles.

The existing strict remaining-update limits are retained:

- Y: `abs(deltaY) < 2e-5 mm`.
- Angular components: `abs(deltaR) < 0.25 sigma0`.

The new, explicitly declared demonstration criterion is
`sqrt(delta.T H0 delta) < 0.25`, evaluated jointly in mixed physical units.
Every `delta/sigma0` is also reported, including Y. This is a **remaining-update
significance**, not the validation-only Truth-error Mahalanobis bound of 25.
CLI flags `--max-abs-y-mm`, `--max-angular-sigma-ratio`, `--max-joint-sigma` and
`--max-scaled-condition` can tighten, but cannot relax, these validated bounds.

The current selected design must retain full rank and diagonal-scaled condition
below 100. The unchanged solve also checks the omitted-X/Z diagnostic design,
rigid gauge, fixed-reference rows, and original sensitivity bounds before Pede.
All accepted/rejected counts and the event/CellID/VolumeID/GeometryIdentifier/
state associations must remain unchanged. Measurement local coordinates and
covariance use the original regression tolerances. Pede must exit normally
without warnings or rejected local fits. All outputs and inputs must be intact.

After at least one correction, reconstruction chi2 and the norm of the two
local residual RMS values may not worsen relative to the initial Geometry;
strict improvement is required for convergence. This new operational quality
check compares with the fixed initial pass, not noisy monotonic changes between
successive passes. A failed safety gate stops, rather than changing errors,
clipping Geometry or adding hidden constraints. Exhaustion is an explicit
nonconverged status. Small remaining updates establish same-data consistency,
not exact physical recovery or calibrated uncertainty coverage.

## Immutable outputs and failure safety

```text
calibration_run/
  manifest.json, manifest.seal.json
  input/{channels.root,initial.xml,alignment.json,complete.json}
  initial-verified.json
  jobs/attempt_000/
    start.json
    iteration_000/
      start.json
      geometry/, reconstruct/, derivatives/, solve/, correct/
      metrics.json, parameter_information.json, convergence.json
      checkpoint.json, complete.json
    report.json
  jobs/attempt_001/...                 # explicit restart only
  final/{candidate.xml,report.json,complete.json}
```

Requests are stored at the iteration root. Each action child directory contains
its command, process and exit records, log and `artifacts/`. The reconstruction
artifacts retain the Mille Binary; solver artifacts retain steering and official
Pede outputs referencing that same immutable binary.
Current/proposed centers and rotation matrices, IDs, selected labels, initial
and current information, all relevant hashes, and parent/child version edges
are recorded. A Geometry version ID is `geo-<XML SHA256>`; the iteration edge
remains explicit even if XML bytes happen to repeat. No production active
pointer is created or updated.

Atomic exclusive completion publication uses a flushed temporary JSON file and
same-filesystem hard link; the temporary name is retained if publication fails.
An iteration seal hashes its entire tree, including nested completion markers,
after every child process exits. A partial stage's historical `complete.json`
alone is never authority for a native Controller checkpoint. Final publication
uses a fully sealed pending directory and atomic directory rename. Abandoned
pending directories remain intact. Resume checks the complete ordered Geometry
chain, source/configuration/build identity and all saved artifacts.

On a numerical-iteration failure, incomplete files and logs remain in that
attempt; that iteration has no valid completion seal. A later final-publication
failure may leave an intact terminal checkpoint, from which resume can publish
the final directory without another fit. The report identifies the last verified candidate,
or the actual verified initial Geometry if failure preceded the first candidate.
An unverified initial Geometry is never reported as valid. The retained legacy
Geometry registry's review/activation lifecycle remains separate.
`last_valid_geometry` denotes the last independently checked physical/ID-safe
candidate, not production approval or an independent statistical validation.
The candidate itself may not yet have been reconstructed. Its measured parent
and all preceding checkpoints remain available if the next reconstruction fails.

## Validation commands

The default operational protocol stops whenever its gates pass. A separate,
prospectively declared `--minimum-corrections 2` validation protocol matches the
manual Scope D driver's two-correction endpoint. Compare equivalent checkpoints:
manual `corrected/` is the first candidate; the historical validation report's
summary named `corrected` actually describes `refined/` in that protocol.

```bash
bash environment/run.sh python3 -B -m validation.native_controller_checks \
  --step compare --run result/native_controller_scope_d_default_20261025_02 \
  --manual result/native_three_sensor_scope_d_seed1_positive_20261024_01 \
  --output result/native_controller_default_comparison_20261025_02

bash environment/run.sh python3 -B -m validation.native_controller_checks \
  --step interruption --run result/native_controller_scope_d_restart_20261025_02 \
  --manual result/native_three_sensor_scope_d_seed1_positive_20261024_01 \
  --build build/native_controller_20261025_01 \
  --output result/native_controller_interruption_check_20261025_02
bash environment/run.sh python3 -B -m validation.native_controller_checks \
  --step compare --run result/native_controller_scope_d_restart_20261025_02 \
  --manual result/native_three_sensor_scope_d_seed1_positive_20261024_01 \
  --output result/native_controller_restart_comparison_20261025_02

bash environment/run.sh python3 -B -m validation.native_controller_checks \
  --step refusal --run result/native_controller_historical_refusal_20261025_02 \
  --manual result/native_three_sensor_scope_d_seed1_positive_20261024_01 \
  --build build/native_controller_20261025_01 \
  --historical result/native_y_rotations_seed2_negative_20261024_01/correction/corrected.xml \
  --output result/native_controller_refusal_check_20261025_02

bash environment/run.sh python3 -B -m unittest discover -s validation -p 'test_*.py'
```

The interruption check waits for a real EICrecon child in the second evaluation's
recorded process group before sending SIGTERM, preserves the incomplete attempt,
and explicitly resumes from the sealed first candidate in a new attempt. The
negative test injects the immutable historical invalid XML at the proposal
boundary after a real Scope D fit. It labels this intervention, retains both
the real current fit and historical fit identity, invokes actual Geometry
validation, and checks that no invalid Geometry reaches reconstruction. It is
a control-plane refusal test, not a new twelve-parameter physical failure fit.

`compare` reads Truth only after operational completion and checks fitted-state,
Mille byte, information, XML and raw-channel identity with manual checkpoints.
It writes `report.json` and ROOT chi2/residual histograms in `controller.root`.
No Truth value influences operational convergence. Existing manual two-update
references do not define a fourth-fit comparison.

## Retained legacy functionality and limits

The original `calibration/controller.py` queue/watch delivery ordering, SQLite
event journal, legacy Geant4 RawHit adapter, explicit retry and independent
review/activation commands remain unchanged. The native Controller reuses its
locking and process supervision but does not claim queue/watch parity or online
real-time calibration. Its atomic checkpoint protocol does not replace or
silently change the legacy registry. Integrating real Geant4/beam-test RawHits
through the same numerical operations is the next milestone.

## Executed Scope D default protocol

The fresh Release build is `build/native_controller_20261025_01`. Its native
TelescopeMille SHA256 is unchanged from Scope C/D:
`0b4fc9b4b379c81d6e960264643c17c63b675bf07b964cea2ccb2a7843ae04b5`.
It uses the formal `external/install/lib/libMille2.so`, SHA256
`6f756ba1c62b45b19df360fe6af1847823d6f19e82f5ef5643dd42bd7b0a544e`,
and the unchanged nine installed ACTS 45.3.0 libraries.

The default run and independent comparison above completed successfully.
Raw ROOT SHA256 is
`7a698db69b5d1f693111eb3b58766d94fd5c2581b2f7389a620cbc18ac8c81bb`;
channel payload SHA256 is
`03d62713fda155271524aba138d5f711146f1cc41bfd4ad3d5cb89f89814c477`.
No RawHit was regenerated. Both evaluations accept all 4,096 tracks, with zero
rejected tracks or local fits, no Pede warning, and normal Pede exit status 0.

| Evaluated Geometry | ACTS chi2/stored-NDF | Pede chi2/NDF | Joint remaining significance | Maximum abs(delta/sigma0) |
| --- | ---: | ---: | ---: | ---: |
| Initial | 12.360222868341953 | 1.0136617747165375 | 693.8080243118991 | 391.74433489698976 |
| First candidate | 0.607925838664596 | 1.0136895255694884 | 0.17677795358280826 | 0.16977521866276546 |

ACTS retains its stored NDF of 10 per five two-dimensional measurements. Pede
uses the four-local-parameter profiled model and `6*4096 - 12 = 24564` global
fit NDF. Its initial reported chi2 already includes the fitted global update;
it is not the initial unaligned ACTS chi2. No uncertainty rescaling is applied.
The norm of the two local residual RMS values improves from
0.04971953877697794 to 0.011026485927371392 mm.

The selected information has rank 12 (initial diagonal-scaled condition
5.209146070620243); the unchanged nuisance-design and physical derivative gates
also pass. The first candidate XML SHA256 is
`da0c576ac5bf1f71097f42dfc3b9a7f75e81da9c405cc92a2ab6ab0f59b0814f`.
Every fitted state/residual, complete Mille Binary, independent information/Pede
result and physical XML equals the equivalent manual checkpoint. The official
decoder reads 4,096 records and 40,960 scalar measurements per evaluated pass.

The first official Pede estimates, before any Truth validation, are:

| Sensor | Y [um] | Rx [mrad] | Ry [mrad] | Rz [mrad] |
| --- | ---: | ---: | ---: | ---: |
| L1 | +80.001 | +0.98512 | -0.10036 | -0.16701 |
| L2 | -59.916 | -1.22500 | +0.87684 | +0.59141 |
| L3 | +50.144 | +0.78102 | +0.13395 | +0.55354 |

Formal errors and correlations are recorded without rounding in each
`solve/artifacts/independent.json` and `parameter_information.json`. Their
data-only covariance is retained separately from the unchanged Pede diagonal
stabilization. The independent post-completion Truth comparison reports
initial-fit error Mahalanobis squared 11.240213635317549 under the historical
bound of 25. Weak angular components can have signs opposite to the injection;
this checkpoint validates the numerical chain and same-data consistency, not
component-sign precision, unbiasedness or uncertainty coverage.

## Executed interruption and two-correction protocol

`result/native_controller_scope_d_restart_20261025_02` uses the predeclared
minimum of two corrections. The test records a live EICrecon PID and its actual
supervised process group, sends SIGTERM during the second evaluation, and
verifies that its incomplete iteration has no successful completion marker.
The first physically verified candidate remains the last checkpoint. Resume
uses `attempt_001`, the same input snapshot, initial information and parent XML;
all 467 prior attempt/input/manifest files remain byte-identical.

The resumed chain completes two corrections and three evaluations. Every
evaluated state/residual, Mille Binary, information/Pede result and XML is
exactly equivalent to the manual nominal/corrected/refined checkpoint. Final
XML SHA256 is
`1ae105fd4b0f9f0f9d5e3e0dfad1d02a10612830c5fa4acfd55cd6549ef3f3e4`.
All passes retain 4,096 tracks, normal Pede exit 0, no warnings/rejected local
fits, unchanged RawHits/measurement associations, physical containment and IDs.

| Final two-correction metric | Value |
| --- | ---: |
| ACTS chi2/stored-NDF | 0.6079249182432249 |
| Pede chi2/NDF | 24900.263047578333 / 24564 = 1.0136892626436385 |
| Local residual RMS norm [mm] | 0.011026477580155998 |
| Joint remaining significance | 0.001216376157777717 |
| Maximum abs(delta/sigma0) | 0.0008664032236462719 |

Actual cumulative poses relative to the initial Geometry are:

| Sensor | World Y [um] | Rotation-log Rx [mrad] | Rotation-log Ry [mrad] | Rotation-log Rz [mrad] |
| --- | ---: | ---: | ---: | ---: |
| L1 | +80.0013842 | +0.9849626762 | -0.1434193607 | -0.1717615834 |
| L2 | -59.916019133 | -1.2250001494 | +0.8150492558 | +0.5893289575 |
| L3 | +50.1457376 | +0.7809790274 | +0.1215832451 | +0.5490219263 |

These are logs of the actual composed matrices, not sums of fitted Euler
angles. All matrices, centers and tiny serialization roundoff in fixed axes are
retained at full precision in `final/report.json`.

Independent Truth validation illustrates the limit of same-data convergence:
L1's orientation error changes from 0.686685 to 0.722465 mrad after the second
correction even though the remaining-update significance becomes much smaller.
L2/L3 errors become 0.216760/0.542788 mrad. No Truth value was available to the
operational decision, and no correlated-fit covariance was added to manufacture
a smaller uncertainty. Neither protocol claims independent uncertainty
calibration or that every iteration moves closer to Truth.

## Executed physical refusal and control-plane tests

The historical invalid proposal has SHA256
`7ae952a74dd554b4891c475354c317115e84d1ac2347b5b3afe1c3194dc2216a`.
After a real, normally completed 4,096-track Scope D fit, the validation harness
substitutes this proposal only at the candidate boundary. Actual constructor
reload reports `module containment failure on layer 1`: minimum world-box
module clearance is `-0.002311986569322577 mm`. Layer containment independently
passes. The original local-frame diagnostic is `-0.002311986569327462 mm`; this
roundoff difference does not change either original strict physical gate.

The Controller correctly terminates with `status: failed`, zero promoted
iterations/corrections, no candidate reconstruction and no activation. The last
verified Geometry remains the initial XML, SHA256
`34a4ce8faae9f9fed73d920c22bffe2d98b52ce8451dc21e69d670c33f3f1e2e`.
The current real fit, historical fitted-result identity, unsafe actual poses,
corner diagnostics, failure type/traceback and subprocess log remain available.
The validation report marks the **refusal test** passed; it does not relabel
the invalid physical candidate as successful alignment.

The actual refusal run is
`result/native_controller_historical_refusal_20261025_02`; the independently
readable result is `result/native_controller_refusal_check_20261025_02`.
The sequential integration receipt is
`result/native_controller_20261025_01_audit/controller_integration_v2`.
Twenty-five additional structural Controller tests use explicitly labeled mock
data to cover corrupt/missing outputs, source/runtime/input changes, invalid
chains, atomic publication, refusal, exhaustion and terminal publication
recovery. They make no physical-fit claim; the real runs above provide that
integration evidence.

Both comparison ROOT files can be inspected with an interactive ROOT setup:

```cpp
// After opening the comparison's controller.root with ROOT:
new TBrowser;
```

Independent batch inspection verifies six default and nine restart TH1D keys:
each chi2 histogram contains 4,096 entries, and each u/v residual histogram
contains 20,480 entries. The source and all command receipts remain local and
readable even when no graphical display is available.

## Consolidated technical validation

The independent integration seal reopens all six completed reconstruction
outputs, including the normally completed fit preceding the negative proposal.
All channel payloads match the immutable source, and all states, complete Mille
binaries, information and XML match the corresponding manual checkpoints.
It verifies 261 frozen execution sources and pins 2,661 integration artifacts.
The physical derivative reports cover 884,736 two-component vectors; maximum
differences are `3.940547443903597e-8 mm/rad` and
`7.260008150211661e-10 mm/mm`. These are technical equivalence/derivative tests,
not an independent statistical campaign.

The separate 18-command regression suite passed with all 154 unit tests:
102 retained tests, 20 native-convergence tests, 25 Controller tests and seven
shared-operation tests. It also executes fresh Geometry/benchmark builds,
actual one-event JANA reconstruction, native/legacy mathematical comparisons,
safety and preservation checks. Existing SQLite ResourceWarnings remain in the
unit-test log; they are not hidden or counted as failures. The exact command
was:

```bash
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build /work/build/native_controller_20261025_01 \
  --result /work/result/native_controller_regression_l1_l2_y_20261025_02 \
  --step regressions --validation-name native_controller_full_suite
```

The historical electron reference also passed using the preserved legacy build:

```bash
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/native_controller_legacy99_20261025_01 \
  /work/build/native_three_rotation_legacy_20261024_01

bash environment/run.sh python3 -B validation/telescope_closure/containment.py \
  --step expected-refusal \
  --original-run result/native_y_rotations_seed2_negative_20261024_01 \
  --build build/native_controller_20261025_01 \
  --output-dir result/native_controller_expected_refusal_20261025_01
```

The former retains 99 tracks, L2 `+198.75 um`, mean Rec-Sim
`-199.57137554842703 -> -0.8213645075978979 um`, and ACTS chi2/stored-NDF
`45.59223484848485 -> 1.9810397677951388`. This is an executed legacy regression,
not a fresh legacy compilation. All nine copied upstream-source patches also
reproduce byte-identically against the pinned read-only EICrecon checkout.

Independent receipts are under
`result/native_controller_20261025_01_audit/`:

| Receipt | What it establishes |
| --- | --- |
| `controller_integration_independent_seal/` | Actual output rereads, checkpoint chain, immutable channels and manual equivalence |
| `controller_integration_schema_and_ROOT/` | Exact producer-specific artifact sets, nested completion markers and 15 ROOT histograms |
| `controller_default_i{0,1}_v2_{native_root,official_binary}/` | Both default passes, native audit/ROOT and official Mille decoding |
| `controller_restart_independent_driver_v2/` | All three restart passes, actual finite differences, information and official binary identity |
| `controller_historical_negative_independent_v2_02/` | Valid initial fit followed by exact historical-proposal physical refusal |
| `full_suite_v2_independent_seal/` | All 18 command exits, 154 tests and sealed scientific reports |

Recorded development diagnostics remain preserved. The first regression exposed an
overstrict new XML whitelist: the unchanged translation-only serializer writes
fixed zero coordinates as `0*mm` rather than `0`. The adapter now requires exact
physical equality before normalizing that spelling; tests reject even
`1e-30 mm` nonselected movement. The original candidate XML, states, Mille and
Pede already matched the historical reference. No numerical serializer or
scientific tolerance changed. The interrupted pilot and first regression
outputs are separately pinned (387 files, 119,307,925 bytes); their planned
campaign totals are explicitly distinguished from the actual four
reconstructions/128 accepted records.

A later read-only audit mistakenly applied the native Controller seal schema
to a `research_common.done` wrapper. The latter excludes all nested
`complete.json` names, whereas native seals include child markers. The failed
audit and exact four-marker diagnosis remain intact. A fresh audit verifies
each producer's exact artifact set and every child marker independently; no
maintained implementation, output or scientific assertion changed.

An initial preservation inventory also compared component-sorted `Path` objects
with sorted relative-path strings and falsely reported a changed tree. The
`baseline_tree_order_diagnosis/` receipt proves the same 172-file set in the
first affected tree. `preservation_baseline_v2/` then repeats the entire hash
inventory with consistent ordering: 25,805 files, 13,778,666,326 bytes, 28 exact
reference trees and seven symlinks, with zero mismatches. Both the failed
`preservation_baseline_driver/` and successful
`preservation_baseline_v2_driver/` receipts remain available. This changed only
the audit's ordering convention, not any dataset or maintained scientific check.

## Completed historical regression campaign

The frozen v2 campaign passes **28/28 cases**, including the 23 historical cases,
the additional Scope C fixture and all four Scope D fixtures. It executes 100
fresh reconstruction passes and accepts 323,968 track records, including
controls and repeated processing. The 86,144 input-event count sums reused
fixture events across cases; it is not a count of independent new simulations.
No Simulation is generated by this campaign. All scientific report fields and
400 protected artifacts match exactly. The full native JSON comparison permits
only the derivative-gate path substitution, after checking its actual command;
no numerical field or diagnostic is excluded or added to obtain agreement.

The 100 historical Pede solves retain 94 status-0 exits and six original
status-1 `Ended with warnings (bad measurements)` exits. The latter are the
initial/postsolve passes of the old 32-event `l1_l2_y`, `l1_rx` and
`l1_y_rx_l2_y` cases. Their complete `.res` and `.end` bytes match the reference.
The test drivers pass their unchanged historical contracts; this is not a claim
that every historical solver is warning-free. All six completed fits in the new
Scope D Controller integrations separately have status 0, no warnings and no
rejected local fits. The native operational Controller continues to refuse
solver warnings.

The generated local audit drivers are execution receipts, not new maintained
workflow entry points. Their inner driver invocations were:

```bash
bash environment/run.sh python3 -B \
  result/native_controller_20261025_01_audit/regression_v2/regression_full_driver.py
bash environment/run.sh python3 -B \
  result/native_controller_20261025_01_audit/regression_v2/seal_full_regression.py
```

The per-case public stage commands, input checksums and comparisons are recorded
under `result/native_controller_20261025_01_audit/regression_v2/` in
`full_regression_case_*/{nominal,solve,correct,corrected,postsolve,refine,refined,refinesolve,control,controlsolve,check}/command.json`,
where applicable. `regression_cases.json` pins every original fixture and
`full_regression_summary.json` separates planned counts from completed counts.
Use the maintained closure driver's `--step` interface with fresh output names
for reproduction; the source fixture/build requirements remain those in the
User Guide. The local regression/reference ROOT files and audit drivers are
intentionally excluded from Git.

The independent disk-level seal also passes: all 28 cases, 100 reconstruction
passes, 323,968 accepted records, 400 protected-artifact comparisons and 272
complete stage hash sets. Its report is
`regression_v2/full_regression_independent_seal/report.json` under the audit
root. It independently verifies zero scientific-field exclusions, unchanged
execution-source/build identities and zero new simulations. Literal host
recording-wrapper commands, inner argv/cwd/exit codes, per-case seeds/counts
and all 100 solver statuses are in
`regression_v2/final_execution_receipt/report.json`. The host commands are
recorded as `host_campaign_command_exact` and
`host_independent_seal_command_exact`; the wrappers preserve the driver
commands and logs without altering the numerical stages.

## Final preservation and source boundary

The final host check passes with zero mismatches: 25,805 pre-existing historical
files (13,778,666,326 bytes), all 28 exact reference trees and seven symlinks.
It separately verifies the 387 quiescent failed-development files
(119,307,925 bytes) in nine trees. Of 332 baseline maintained files, 326 remain
byte-identical; the only changes are the three documented Python files and
three existing guides, plus the seven explicitly reviewed new maintained files.
All 261 frozen execution-source hashes, 38 legacy function ASTs, the complete
old convergence byte prefix, four moved-helper ASTs and two numerical suffixes
match their authorities. All C++/XML/configuration/core source bytes are intact.

The separate fixed-Docker library check confirms unchanged hashes for all nine
installed ACTS 45.3.0 libraries and 13 prior local binaries. New native builds
select the formal `external/install/lib/libMille2.so`; its hash is
`6f756ba1c62b45b19df360fe6af1847823d6f19e82f5ef5643dd42bd7b0a544e`.
The newly built native Mille plugin also matches the preserved C/D authority,
SHA256 `0b4fc9b4b379c81d6e960264643c17c63b675bf07b964cea2ccb2a7843ae04b5`.

Exact executed final-check argv/cwd records and sealed summaries are in
`result/native_controller_20261025_01_audit/final_preservation/` and
`final_installed_libraries/` under that audit root. The repository-relative
equivalents below add `-B` to prevent bytecode-cache writes; `command.json`
retains the actual interpreter path and arguments:

```bash
python3 -B result/native_controller_20261025_01_audit/final_preservation_verify.py \
  --mode full --output result/native_controller_20261025_01_audit/final_preservation
bash environment/run.sh python3 -B \
  result/native_controller_20261025_01_audit/final_preservation_verify.py \
  --mode libraries \
  --output result/native_controller_20261025_01_audit/final_installed_libraries
```

These local audit scripts and datasets are excluded from Git. No installed
software, historical data, legacy scientific capability or production Geometry
is modified. Final documentation hashes are recorded separately after these
English result paragraphs are completed; no numerical source changes after
the frozen campaign.

The default staged whitespace check reports one nonfunctional style warning:
`calibration/native_operations.py:416: new blank line at EOF`. The earlier
unstaged check did not inspect new untracked files. That final empty line is
intentionally retained to preserve the exact execution-source hashes used by
the completed runs and their strict restart checks. The staged review records
the default check's exit 2 and this exact sole warning, rather than claiming a
clean default whitespace check. No scientific assertion is changed.
