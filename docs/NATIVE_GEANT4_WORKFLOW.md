# Native telescope input from npsim and official EICrecon Digitization

This document preserves the initial integration audit and its failed operational
attempts. For the later public workflow and explicit offline diagnostic policy,
use the [practical guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md) and
[workflow milestone](NATIVE_WORKFLOW_VALIDATION.md). The historical numbers and
failure artifacts below remain unchanged; they are not the current interface.

This experimental input path uses genuine Geant4 SimTrackerHits in the existing
radial seven-plane telescope. It leaves the legacy +Z simulation and all
synthetic technical tests available. Transport through material and successful
software integration do not establish alignment resolution or uncertainty
coverage. Execution results and any operational refusal are reported below.

Historical checkpoint: genuine Simulation -> Digitization -> RawHits -> native CKF ->
official Pede is executed. Geant4 Geometry Correction and corrected
reconstruction have **not** passed the existing Controller contract. Only
Scope A has been attempted with Geant4 input. The two independently confirmed
refusal reasons are documented below; no gate was relaxed and no candidate was
activated. The declared full integration milestone is incomplete.

## Historical transition

The original `435bac7` simulation runner used DDSim/Geant4 with the custom
seven-layer detector. `21008ae` added segmented readouts and an EICrecon
Digitization/reconstruction runner. The latter's presence does not establish
that every attempted tracking configuration worked. Consolidation in
`3034eb1` removed obsolete runners while retaining the maintained independent
Geant4 stages. The original nominal XML remains unchanged.

The native barrel investigation began in `831dc4c`. `2818819` introduced one
synthetic track to isolate installed DD4hep-to-ACTS conversion and CKF
contracts. `1541fa8` connected synthetic TrackerHits to actual EICrecon tracking
sources. `288e80e` introduced real DD4hep plane intersections and segmentation,
followed by synthetic RawTrackerHits, the installed hit reconstruction factory
and native Mille equations. The later rename in `43ca1f6` and bounded Python
Controller in `eaabd7e` retained that explicit technical input model. Geant4 was
not removed from the repository; the native validation deliberately isolated
Geometry, channel mapping, tracking and alignment mathematics from transport.

The two paths use different physical placements and CellIDs. The legacy beam
travels along +Z through planes at z0--300 mm. The native beam travels along +X
through planes at x250--550 mm. SiMAPS occupies L0--L4; MPGD and AC-LGAD occupy
L5/L6. Old endcap RawHits cannot be relabeled as native barrel data.

## Software and physics contract

Use the fixed Docker image through `environment/run.sh`, optionally setting
`TESTBENCH_CONTAINER=sweet_mahavira` for the existing container. No eic-shell
environment or installed-software modification is required. The initial
software audit pins npsim 1.4.7, DD4hep 1.36, Geant4 11.3.2.east, ACTS 45.3.0,
ROOT 6.38.00, EDM4hep 1.0.0 and podio 1.7.0. Installed EICrecon source revision is
`195966d41899800eaeca6fbafd63cd53735e6543`.

npsim wraps DDSim and is the preferred ePIC entry point; it adds optical
configuration and retains the standard DDSim gun/output interface.
See the [official ePIC simulation tutorial](https://eic.github.io/tutorial-simulations-using-npsim-and-geant4/instructor/02-physics-event-simulations.html)
and [npsim source](https://github.com/eic/npsim). This milestone uses the pinned
installed version and does not upgrade the environment or silently fall back
to ddsim.

`simulation.native` fixes one electron per event at 1 GeV gun energy and uses
FTFP_BERT plus the installed npsim optical additions. The existing world is
Air. Sensor material/thickness remains Silicon: SiMAPS 0.05 mm, MPGD 3 mm and
AC-LGAD 0.35 mm. The latter two are historical pixel-like Silicon approximations,
not a realistic gas detector or AC-LGAD response model. ACTS reconstruction
remains zero-field with no assigned material map/process noise. Geant4
scattering, energy loss, bremsstrahlung and secondaries therefore need not be
described by the existing material-free four-local-parameter fit.

Two explicit gun recipes are available:

| Recipe | Vertex | Direction |
| --- | --- | --- |
| `pencil` | (249,0,0)mm | fixed +X |
| `broad` | x249 mm; independent Gaussian y/z sigma 12/10 mm | DDSim uniform theta in pi/2+-0.08 rad, phi in +-0.08 rad |

The broad recipe is not identical to the synthetic uniform-intercept,
uniform-slope recipe. Do not claim event-by-event equivalence. Each Simulation
seed is supplied explicitly and saved with the actual command. Digitization
uses the installed official EventHeader/algorithm-identity seeding service.

The legacy nominal XML's `tracker_region_rmax=120mm` does not enclose the
radial sensors. The new simulation stage writes a private XML with only
particle-retention bookkeeping constants rmax 600 mm/zmax 100 mm. It verifies an
exact two-attribute whitelist and independently reloads both XML files through
DD4hep/ACTS, requiring all seven physical sensor poses and IDs to agree.
Canonical Geometry, physical sensor dimensions, materials and alignment
correction rules are unchanged.

## Independent stage commands

Build in an unused directory. The official digitizer registration is a separate
Plugin; the maintained tracking and Mille targets retain their numerical code.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake \
  -S localDetEICrecon/experimental/telescope -B build/MY_GEANT4_BUILD \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build build/MY_GEANT4_BUILD -j2

# Prepare an independent native nominal fixture with normal XML metadata.
bash environment/run.sh python3 -B -m validation.telescope_geometry.prepare \
  --output-dir result/MY_GEOMETRY --initialize-metadata

# Five-event transport smoke test; use a new output directory and recorded seed.
bash environment/run.sh python3 -B -m simulation.native \
  --output-dir result/MY_SIMULATION --geometry result/MY_GEOMETRY/nominal.xml \
  --build build/MY_GEANT4_BUILD --events 5 --seed 2026102501 --beam pencil

bash environment/run.sh python3 -B -m digitization.native \
  --operation all --output-dir result/MY_DIGITIZATION \
  --simulation result/MY_SIMULATION/transport/events.edm4hep.root \
  --geometry result/MY_SIMULATION/simulation.xml \
  --geometry-audit result/MY_SIMULATION/simulation_geometry_audit/geometry.json \
  --build build/MY_GEANT4_BUILD
```

Every output directory must be unused. Failed and partially completed stages
are retained; use new directories for retries. `--operation digitize` can run
Digitization independently. `--operation project --digitized PATH` projects a
previously completed, hash-verified Digitization stage into another fresh
output directory. The legacy commands in the User Guide remain available.

| Stage | Input | Output / success check |
| --- | --- | --- |
| Simulation | actual native XML, seed, gun recipe, metadata library | `transport/events.edm4hep.root`, `configuration.json`, `simulation_qa.json`; requested events, primary electrons and real SimTrackerHits |
| Digitization | Simulation, native readout XML, completed zero-event audit | `digitization/digitized.root`; every source event/collection plus official RawHits/links/associations |
| Raw projection | complete Digitization stage | `projection/channels.root`, `projection/selection.json`, top-level `provenance.json`; exact Raw values, read-back hash, complete event ledger |
| Calibration | projected RawHits, provenance, approximate nominal XML, validated alignment config | immutable snapshots, per-stage diagnostics/checkpoints, explicit convergence or refusal; no activation |

`TelescopeDigitization.so` registers the installed official
`SiliconTrackerDigi_factory`/algorithm for the three readouts. SiMAPS retains
threshold 0.54keV/time resolution8 ns; MPGD retains 0.1keV/10 ns; AC-LGAD retains
0keV/0.025 ns. Collection tags differ from the legacy Plugin, so the factory-tag
dependent timing random stream is not promised to match legacy timing bytes.
The full algorithm identities include the Plugin prefix, for example
`TelescopeDigitization:TelescopeSiMAPSRawHits`; the corresponding actual parameter
keys are `TelescopeDigitization:TelescopeSiMAPSRawHits:threshold` and
`:timeResolution`. Source, library, Plugin hashes and executed collection tags
pin that identity. No algorithm is copied or substituted.

The Raw-only adapter is telescope-specific. The existing seed consumes exactly
five ordered hits, while official Digitization can produce multiple pixels and
unordered cells. The adapter accepts exactly one valid SiMAPS cell per L0--L4,
sorts by decoded layer and clones complete EventHeader/RawTrackerHit objects.
It preserves CellID, charge and timestamp exactly. It decodes the actual XML
readout and matches real audited VolumeIDs; it never transforms endcap IDs.
Every rejected event and layer multiplicity remains in a ledger and the full
Digitization output. No Truth, track-quality or residual selection is used.
This limited topology acceptance is not general clustering or real-data support.

## Existing Controller

For a statistically adequate input with broad angular/position coverage, use
one of the four already validated scopes. Scope A is the smallest (five global
parameters). A five-event smoke test cannot establish its angular precision.

```bash
bash environment/run.sh python3 -B -m calibration.native_controller start \
  --run result/MY_CALIBRATION \
  --raw result/MY_DIGITIZATION/projection/channels.root \
  --input-provenance result/MY_DIGITIZATION/provenance.json \
  --geometry result/MY_GEOMETRY/nominal.xml \
  --config validation/telescope_alignment/l1_y_rx_ry_rz_l2_y.json \
  --build build/MY_GEANT4_BUILD --events ACCEPTED_EVENT_COUNT --chi2-cut 1000
```

Replace `ACCEPTED_EVENT_COUNT` with the complete projected count. Simulation
Truth Geometry may contain known validation displacements, but supply only the
approximate starting Geometry to calibration. Truth is used separately after
inference. The optional provenance receipt must identify both the exact Raw
ROOT bytes and channel payload; it is snapshotted and sealed. Geant4-origin
reconstruction audits explicitly say `synthetic_input:false`; `material_free`
still refers only to the unchanged ACTS reconstruction model.

To reproduce the existing displaced Scope A Geometry, reuse the maintained
Geometry-only stage. Its `--events 32` satisfies the legacy fixture CLI contract;
this stage generates no particles or channels. Choose unused output names:

```bash
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build build/MY_GEANT4_BUILD --result result/MY_SCOPE_A_CASE \
  --mode l1_y_rx_ry_rz_l2_y --events 32 --step geometry

bash environment/run.sh python3 -B -m simulation.native \
  --output-dir result/MY_SCOPE_A_SIMULATION \
  --geometry result/MY_SCOPE_A_CASE/geometry/truth.xml \
  --build build/MY_GEANT4_BUILD --events 2304 --seed 2026102503 --beam broad
```

Then run the same independent Digitization command with that Simulation's
`transport/events.edm4hep.root`, `simulation.xml` and
`simulation_geometry_audit/geometry.json`. Supply the resulting Raw/provenance
to the Controller, with starting XML
`result/MY_SCOPE_A_CASE/geometry/fixtures/nominal.xml` and the complete projected
event count. The actual milestone's Pede/Controller refusal below is expected
under its unchanged contract; these commands do not promise successful closure.

Always use the matching native Simulation output. The adapter's generic CLI
checks readout/actual IDs and records source hashes, but does not itself consume
the `simulation.native` producer receipt or prove every supplied SimHit's
global position against the sensitive volume. The recorded fresh npsim commands
and independent Geometry checks establish that association for these runs.
Producer-receipt binding is a future misuse-prevention improvement; it must not
be replaced by relabeling/reinterpreting old endcap channels.

The Controller retains unchanged information, derivative, solver, association,
containment and convergence gates. Pede warnings/rejected local fits or
inadequate angular information cause a recorded refusal. Additional statistics
cannot in general repair a missing process-noise model. Do not lower gates,
rescale errors, filter on fitted quality or retune seeds to manufacture closure.
The synthetic technical baseline remains the numerical regression authority;
different Geant4 physics does not imply identical chi2 or parameter estimates.

## Execution record

The milestone's baseline and exact command receipts are under
`result/native_geant4_20261025_01_audit/`. The source audit starts at
`eaabd7e2dd68d429fb52fabfd216d74aaffd2729` and freezes 339 maintained files.
The protected data audit verifies 46,239 files/23,276,331,949 bytes across 75 tree
inventories, with no mismatch. Installed software and previous binaries are
separately pinned. New results are kept under distinct `result/native_geant4*`
directories. These local data, audit drivers and builds are excluded from Git.

The five-event smoke uses seed 2026102501. Every event has a measured primary
vertex (249,0,0)mm and +X momentum. The installed gun's `energy=1*GeV` produces
measured momentum magnitude1 GeV/c, mass0.00051099891 GeV/c2, total energy
1.0000001305599342 GeV and kinetic energy0.9994891316499342 GeV. No generator
setting was retuned to change this convention. The original pilot protocol's
`kinetic_energy_GeV:1` label was imprecise; the separate
`gun_energy_semantics_clarification/` receipt retains and corrects that label
without rewriting the prospective record.

| Executed input | Seed | Generated | SimTrackerHits L0--L6 | Raw-only accepted / rejected |
| --- | ---: | ---: | --- | ---: |
| Nominal pencil smoke | 2026102501 | 5 | 5,6,6,5,5,6,5 | 3 / 2 |
| Existing Scope A Truth, broad pilot | 2026102502 | 128 | 129,130,128,129,129,164,142 | 125 / 3 |

Both samples' excluded events are documented double-cell multiplicities, with no invalid
CellIDs. The smoke's full Digitization output retains 38 RawTrackerHits, and
the pilot retains 938 RawTrackerHits from 951 SimTrackerHits, including 13
same-cell merges. Independent validation reproduces charges with the official
per-SimHit threshold/rounding rule; verifies both link types (76 smoke and 1,902
pilot links/associations), original MC/SimHit/Header columns, complete projected
headers and exact Raw values; and checks actual DD4hep contexts against audited
ACTS surface identities. Neither sample exercises a threshold-rejected SimHit.
Timing values are verified unchanged, rather than regenerated independently.

The smoke ROOT diagnostics are
`result/native_geant4_20261025_01_smoke_validation2/geant4_digitization_qa.root`
(15 TH1D and one TCanvas). The pilot independent audit is
`result/native_geant4_pilot_transport_validation_20261025_01/`; its Digitization
and transport-physics ROOT files reopen successfully. All primary-linked
SimHits, including duplicates and tails, remain in the transport diagnostic.
The L4 y/z central16--84% ray-departure intervals are approximately
[-66.3,+76.7]um and[-71.3,+64.4]um. DD4hep can combine secondary deposits into
primary-linked hits; these are transported departures, not an isolated
multiple-scattering resolution measurement.

The actual pilot Controller is
`result/native_geant4_pilot_controller_20261025_01`. It reconstructs 125/125
tracks with five measurements, no outliers/rejections and two expected
unmeasured-plane holes. Every measurement is associated with its real
VolumeID/ACTS GeometryIdentifier and retains the original pitch-derived
covariance. All 1,875 actual-Geometry finite-difference vectors pass; maximum
differences are 6.24e-8 mm/rad and 3.17e-10 mm/mm. Raw ROOT SHA256 is
`92c9dda3fa9efa39abf2cb6909d7ade7915b70073c8671be07fc4258d07e4495`;
payload SHA256 is
`4598ca56048a2854925f1677ebcb489493c022fd24b6146f9cd674d624cdf244`.

The pilot correctly stops with exit 1 before Pede at the unchanged precision
gate: selected rank 5/condition 1.989, extended diagnostic rank 12/condition 3.708,
but worst selected/extended angular nominal errors 1.745/1.811 mrad exceed 0.5 mrad.
There is no correction, successful iteration, checkpoint or activation. ACTS
initial chi2/stored-NDF is 13491.512256622314/1250=10.7932098053, including the
injected misalignment. Separate data-only profiling over five globals and
four locals per track gives1803.9894197/745=2.4214623, with a substantial tail.
This is an independent diagnostic, not an executed Pede result or a bypass of
the information gate.

The actual pilot information forecasts1,640 accepted tracks for the existing
precision gate, assuming unchanged information per track. One prospectively
declared 2,304-event sample with seed 2026102503 is used to test that gate and
actual solver behavior; there is no ensemble or seed/quality-based sample
tuning. Its predicted2,250 accepted events and 0.427 mrad worst extended error
are engineering forecasts, not certified uncertainties or guaranteed outcomes.
The protocol is
`result/native_geant4_scope_a_20261025_01/prospective_protocol.json`.

Fresh Release CMake configure/build passes for all targets in
`build/native_geant4_20261025_01`. Actual dynamic linkage uses installed official
`libalgorithms_digi.so` at revision 195966 and the formal
`external/install/lib/libMille2.so`. All nine installed ACTS libraries match the
baseline. `NativeMilleModel` archive/object, CKF and measurement-conversion
objects, and complete `TelescopeMille.so` are byte-identical to the prior build;
the tracking Plugin differs for observer provenance only. The audit explicitly
normalizes only the new origin metadata plumbing and verifies the complete old
reconstruction/calibration numerical ASTs, plus unchanged correction, solver,
convergence, seed and alignment model sources.

The fresh32-track historical closure passes with exact baseline values:
L1+149.14 um/L2+203.18 um and ACTS chi2/stored-NDF
37.16731567382813 ->0.6908491410315036. Whole default-synthetic audit JSON,
Mille Binary, Pede values/errors, profiled information and corrected XML match.
The actual Controller/provenance/PODIO tests pass 40/40 in the fixed Docker
environment, including all new clone/descriptor/selection safety cases.

## Adequate-statistics Scope A result and precise stopping point

The declared 2,304-event sample completes npsim and official Digitization. The
Raw-only projection accepts 2,218 events and rejects86 for multiple-cell
multiplicities, including triple/quadruple cases; no invalid CellID is present.
It retains all original source events in the full Digitization file. Projected
ROOT SHA256 is
`d78537be3db85029d8aef963e7ac1f1b67da0857ee65cbb2e1b5300045d5d016`;
payload SHA256 is
`1bf9714cb4068a8e1fd75cc891280be57ba675ad2c983637760126b31f631af3`.
Its SimTrackerHit counts on L0--L6 are
2,312/2,325/2,337/2,330/2,341/2,704/2,424, respectively.

An independent source-binding and sensitive-volume check covers all 17,762
SimTrackerHits in the three samples(2,437 generated events). Every recorded
global hit position is inverse-transformed with the actual DD4hep pose and
checked against the actual XML sensor half dimensions. Maximum outward face
excursion is 3.05e-14 mm, below the predeclared1e-6 mm navigation roundoff bound.
Every CellID pixel mask matches the audited VolumeID. Each Simulation ROOT is
bound to its actual npsim `--compactFile`/`--outputFile`, XML/ROOT hashes,
event/seed configuration and completed producer/audit/Digitization receipts.
The report is `geant4_sensitive_volume_consistency/report.json` under the audit
root. This is a Geometry/transport check, separate from fitted-state checks.

The actual Controller run is
`result/native_geant4_scope_a_controller_20261025_01`. Native CKF reconstructs
all 2,218 tracks, each with five measured SiMAPS states and zero outliers. Native
Mille writes 2,218 official records/22,180 scalar measurements. All 33,270
physical-Geometry finite-difference vectors pass, with maximum differences
6.385e-8 mm/rad and 3.174e-10 mm/mm. Selected information has rank 5/condition 1.867;
the extended12-column diagnostic has rank 12/condition 2.862. Worst selected and
extended angular nominal errors 0.370/0.388 mrad pass the original 0.5 mrad gate.

Two independent barriers prevent a qualified correction:

1. `FactoryAudit::Process` retains the original hardcoded requirement
   `track.nHoles()==2`. Five source events(506,913,1083,1330,2053) have one hole,
   while still having all five measured SiMAPS states and no outliers. Their
   fitted lines cross MPGD but pass the AC-LGAD plane at global Y approximately
   +52.537,-52.689,+50.306,+50.950,+52.627 mm, outside its actual+-50 mm sensor.
   Thus the observer marks2,213 accepted/five rejected and `passed:false`.
   This is a bounded-synthetic-beam audit assumption, not five failed CKF fits
   or missing SiMAPS measurements. It was neither removed nor relaxed.
2. Official Pede processes all 2,218 valid Mille records, with process exit 0 and
   zero rejected local fits. Its actual `.end` status is
   `1 Ended with warnings (bad measurements)`: chi2 is 30939.298032245755 and
   NDF is 6*2218-5=13303, giving2.3257384072950278. The warning specifically
   concerns high chi2/NDF and suggests multiplying errors by 1.53. That advice
   was not applied. All values, nominal errors and independent Schur equations
   agree at the original printed-precision criteria. Even if the hole audit
   were addressed, the unchanged Controller warning/status gate would refuse
   this result independently.

Actual initial Pede estimates are shown solely as diagnostic fit results.
Injection values are consulted only for this separate post-run comparison;
they are not calibration observations, corrections or stopping targets.

| Parameter | Injected | Pede estimate | Pede nominal error |
| --- | ---: | ---: | ---: |
| L1 Global Y [um] | +80 | +80.319 | 0.26610 |
| L1 Global Rx [mrad] | +1 | +1.0172 | 0.016366 |
| L1 Global Ry [mrad] | +0.5 | +0.48706 | 0.36983 |
| L1 Global Rz [mrad] | -0.5 | -0.85807 | 0.32970 |
| L2 Global Y [um] | -60 | -60.369 | 0.24636 |

ACTS initial chi2 over all 2,218 reconstructed tracks is 243030.26595687866,
with stored-NDF 22180, or 10.95718061122086. This includes misalignment. Pede's
chi2 is after fitting the five globals and four local parameters per track;
its denominator is different. No corrected-Geometry chi2 or residual is
available: the Controller exits 1 in `summarize` with
`Reconstruction audit failed`, zero promoted iterations/corrections and the
initial XML retained as the last valid Geometry. There is no final candidate,
Geometry activation or Geant4 closure-success claim. The Pede warning would
also fail the subsequent unchanged solver-quality check.

The installed official `inspectMilleBinary` also executes with exit 0 on this
genuine Geant4 binary: 2,218 records, 22,180 scalar measurements and the five
expected labels, each appearing 4,436 times. This validates binary decoding,
not the separate observer acceptance or statistical model. Its actual command
and output are retained under `official_g4_primary_binary/` in the audit root.

The measured transport departures and chi2 excess are consistent with missing
material/process-noise treatment and other Geant4/measurement effects; this
study does not uniquely separate scattering, bremsstrahlung, energy-weighted
hit positions or non-Gaussian tails. A statistically adequate information
matrix does not validate that nominal covariance model. More events do not
remove the demonstrated hole-acceptance assumption or high mean chi2. No
additional sample, seed search, fit-based event filtering, uncertainty scaling
or steering change was used to evade these barriers.

## Regression, preservation and follow-up boundary

The 18-command consolidated suite passes, including 169 unit tests, fresh
Geometry/standalone builds, actual one-event reconstruction, native/legacy
equivalence, noiseless Pede, safety and preservation. The separately executed
legacy 100-event saved-Simulation regression accepts 99 tracks in both passes,
with L2 correction+198.75 um, Rec-Sim
-199.57137554842703 ->-0.8213645075978979 um and ACTS chi2/stored-NDF
45.59223484848485 ->1.9810397677951388. Its fresh output is
`result/native_geant4_legacy99_20261025_01`.

The existing synthetic Scope D Controller regression also passes with the new
build. The default protocol converges after one correction/two fits; the actual
SIGTERM/restart protocol converges after two corrections/three fits. Every fit
retains 4,096 tracks, immutable channels, zero rejected local fits and normal
Pede status 0. States, entire Mille binaries, information and candidate XML
match the historical manual nominal/corrected/refined stages exactly. ACTS
chi2/stored-NDF is 12.360222868341953 ->0.607925838664596 ->0.6079249182432249.
The interrupted second evaluation remains unsealed; resume preserves 467 prior
files and uses a fresh attempt. Both independent comparisons generate readable
ROOT diagnostics. These are synthetic regression results, separate from the
Geant4 refusals above. Exact commands, exits and comparisons are sealed under
`scope_d_controller_regressions/` in the audit root.

Final historical preservation rehashes the exact 46,239 files/75 directory
inventories/eight symlinks with zero mismatch. Pinned installed simulation
software, all nine ACTS libraries, formal Mille/Pede and all prior protected
binaries remain unchanged. Numerical code is unchanged, so the complete old
28-case numerical campaign is not repeated; the 32-track, consolidated,
Controller and legacy regressions test the affected execution paths.

Previously sealed Controller runs correctly refuse verify/resume under the
changed implementation identity(261 ->266 execution-source paths). Their
source commit, builds, inputs and outputs remain preserved. Reproduce a
historical restart with its original frozen implementation/environment, or
start a new run; do not weaken its identity checks or rewrite old manifests.

Completing Geant4 closure requires a separately reviewed follow-up. The
smallest acceptance adaptation is a truth-free check of actual intersections
with unmeasured sensor bounds, retaining the five-measurement/outlier gates;
another prospectively bounded standard gun recipe could avoid the demonstrated
edge trajectories. Neither resolves the independent chi2/model warning.
Material/process-noise and uncertainty validation must be considered separately
before changing solver/Controller quality policy. No such change is implemented
here, and no local commit is made because the requested full integration
milestone has not succeeded. There is no push or merge.

A successful transport/Geometry/derivative test is not a statistically
validated uncertainty model. The software input chain is demonstrated;
Geant4 Alignment Closure remains unaccepted under the preserved contract.

## Maintained changes and independently runnable checks

| Files | Functions / responsibility |
| --- | --- |
| `simulation/native.py`(new) | `simulation_geometry`, `gun_arguments`, `simulate`, `inspect_simulation`: installed npsim execution and separate post-transport QA |
| `digitization/native.py`(new) | `digitize`, `geometry_contract`, `select_channels`, `project`: actual official factories, exact Raw-only topology projection and provenance |
| `localDetEICrecon/experimental/telescope/TelescopeDigitization.cc`(new), its `CMakeLists.txt` | `InitPlugin` and isolated target registration; no copied Digitization algorithm |
| `localDetEICrecon/experimental/telescope/FactoryAudit.h` | `Init`, `Process`: explicit origin metadata; all old selection/validation conditions retained |
| `calibration/native_operations.py` | `reconstruct`: optional origin argument adds only the observer's provenance parameter |
| `calibration/native_controller.py` | `input_provenance`, `initialize`, `worker`, `calibrate`, `main`: receipt identity/snapshot and origin forwarding; no numerical/acceptance change |
| `validation/test_native_geant4.py`, `validation/test_native_digitization.py`(new), `validation/test_native_controller.py` | producer safety, actual PODIO cloning/identity, decoded-layer selection, Controller receipt sealing and changed-input refusal |
| `README.md`, `docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md`, `docs/TELESCOPE_ALIGNMENT_CODE_MAP.md`, `docs/NATIVE_CALIBRATION_CONTROLLER.md`, this new guide | current commands, data/control flow, limitations and actual results |

The 15 maintained paths comprise nine modified and six new files. No source or
historical file is deleted. New output and audit directories are ignored;
the local source snapshot described in the final handoff is not a Git commit.

Targeted checks can run independently:

```bash
bash environment/run.sh python3 -B -m unittest -v \
  validation.test_native_controller validation.test_native_geant4 \
  validation.test_native_digitization

# After a separate synthetic l1_l2_y closure has created its immutable inputs:
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build build/MY_GEANT4_BUILD --result result/MY_SYNTHETIC_CLOSURE \
  --step regressions --validation-name NEW_CHECK_NAME

bash environment/run.sh bash validation/run_regression.sh \
  /work/result/MY_LEGACY99_REGRESSION \
  /work/build/native_three_rotation_legacy_20261024_01
```

The last command requires the preserved legacy build and local reference
datasets; it is not a fresh legacy compilation. Full native default/restart
commands and manual comparison contracts remain in the Controller guide.
Actual argv/cwd, exit codes, solver warning files and audit hashes are recorded
under the new audit root rather than inferred from successful source builds.

All 15 maintained working-tree files, including the six untracked new sources
and guide, are copied with checksums into
`result/native_geant4_20261025_01_audit/maintained_working_tree_snapshot/`.
The snapshot also records the tracked patch and exact Git status. It preserves
this incomplete milestone locally without creating a commit or modifying the
persistent external archive. Starting HEAD remains
`eaabd7e2dd68d429fb52fabfd216d74aaffd2729`.
