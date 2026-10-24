# Telescope implementation audit and consolidation

## Decision and limits

Baseline: clean `feature/upstream-acts-geometry` at
`43ca1f667374894381a5df254821edd09499fcd5`.
The active development entry is the [EICrecon telescope guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md).
Its synthetic, quantized-channel, zero-field, no assigned ACTS material closure is
not a production-ready online calibration service. The retained endcap chain is
not presented as an interchangeable second implementation of that same fixture:
it still owns demonstrated capabilities not ported to the native chain.

Only two redundant build entries are deleted. No reconstruction algorithm,
alignment equation, Geometry setting, detector flag, covariance, seed prior,
particle hypothesis, selector cut or steering is changed. No scientific feature
is retired. No result, reference XML, manifest, installed dependency or partial
failure artifact is deleted. The new shared parser is the existing function moved
unchanged, not a new mathematical or orchestration abstraction.

## Final tree and responsibilities

```text
alignment/
  pede.py                   shared result parsing (no solver or correction imports)
  align.py, pede_*.txt       retained guarded solver CLI and mode steering
geometry/
  transforms.py             shared rigid-frame/SO(3) mathematics
  prepare.py, placements.py retained endcap injection / XML placement handling
  nominal/, scenarios/      protected source Geometry and test scenarios
correction/                 retained endcap physical updates / scope guards
calibration/                retained input queue, iteration, version/review lifecycle
reconstruction/             retained BeamTestReco RawHit-based stage
localDetEICrecon/
  CMakeLists.txt             retained plugin; Writer compiled directly
  algorithms/, factories/, processors/, plugins/, geometry/
  alignment/src/            retained Writer and tilt model (no standalone CMake)
  experimental/telescope/   active official-services/native-CKF/native-Mille chain
validation/
  telescope_geometry/       actual barrel-compatible representation and checks
  telescope_closure/        bounded synthetic fixture and automatic closure test
  telescope_alignment/      derivatives, rank/profile, legacy writer equivalence
  telescope_one_track/, telescope_factories/ independent reference gates
  test_*.py, other probes   retained legacy/scientific/safety/preservation tests
environment/build.sh        single retained BeamTestReco build entry
```

No steering file was renamed.

**Geometry** defines physical poses and frame transformations, and can inject
known displacements to generate test data. It does not estimate alignment from
tracks. **Alignment** consists of residual/Jacobian equations, Mille records and
an official Pede solve; the Python `alignment/align.py` is a guarded solver stage,
not the derivative implementation. **Geometry Correction** maps the inferred
parameters into a new reconstruction XML. **Calibration** schedules input files,
repeated reconstruction/solve/correction, convergence and explicit candidate review.
It manages the lifecycle rather than defining a second derivative model.

## A–E classification and actual dependency evidence

- **A:** required by the current native EICrecon telescope pipeline, including its
  offline fixture and validation gates.
- **B:** shared utility/package or protected common input.
- **C:** distinct legacy capability not yet replaced; removing it loses a maintained
  workflow, mathematical scope, Geometry adapter or lifecycle interface.
- **D:** independent reference/regression/diagnostic evidence generator; not a
  replacement tracking pipeline.
- **E:** no unique computation; removed duplicate entry with callers redirected.

The inventory below lists each source/configuration module in the requested areas,
plus `correction/`, which is essential to the audit. Imported callers come from
Python ASTs; executable/configuration references and C++ includes/CMake source
links were also inspected. Empty static-caller lists do **not** prove dead code:
CLI entry points, dynamic Controller stage names and historical experiments are
explicitly retained. Manifest contents and historical datasets are excluded from
the source table and remain protected by the unchanged preservation checks.
A category C row is not a claim that every configuration is enabled: existing
failed-mode refusal gates remain authoritative.

The complete 208-module inventory is in the appendix below.

### Key cross-module call sites

| Caller | Actual dependency and consequence |
|---|---|
| `validation/telescope_closure/closure.py` | imports `geometry.transforms.matvec/transpose`, `alignment.pede.read_pede`, fixture `prepare`, and independent `records/profile`; its inference no longer imports the legacy solver or `correction.scope` |
| same `regressions` | builds standalone Geometry/CKF references and current one-event JANA; invokes LegacyTelescopeCrosscheck, original Writer, mathematical fixture, unit tests, safety, preservation |
| `localDetEICrecon/experimental/telescope/CMakeLists.txt` | directly compiles `../../alignment/src/BeamTestMilleWriter.cc` for the small legacy-equivalence executable; not the entire old plugin |
| `localDetEICrecon/CMakeLists.txt` | directly compiles Writer into BeamTestReco, alongside digitization/RecHit/fitter/processors and actual endcap geometry extension |
| `BeamTestMilleProcessor::Init/Process` | owns Writer and maps selected hits to its equations; requires Writer header/source and tilt helpers |
| `correction/correct_geometry.py` | `modified_xml/write_shifted_xml`, placement transforms, scope/Survey checks and shared Pede parser; preserves physical sign and full-matrix composition |
| `calibration/iteration.py::iterate` | dynamically invokes geometry.prepare, reconstruction.reconstruct, alignment.align, correction.correct_geometry; observability gates and immutable RawHit contract |
| `calibration/controller.py` | queue, input verification, runner, iteration, geometry version/review lifecycle and recovery |
| `validation/test_*.py` | exercises transforms, Geometry Correction, rotation/Z/tilt/SO(3), RawHit metadata and Controller safeguards |
| historical conversion probes | original endcap provider comparisons/paired-endcap experiment; distinct negative/technical diagnostics, not active reconstruction |

All maintained Pede parser callers now import `alignment.pede`; the old
`alignment.align.read_pede` name remains a compatible alias. Original function AST
is identical, three actual Pede result files were checked, and a clean interpreter
imports the shared reader without loading `alignment.align` or `correction.scope`.

## Misalignment injection versus inferred correction

| Property | Retained endcap chain | Current native telescope closure |
|---|---|---|
| Intended beam/placement hierarchy | original +Z telescope, endcap/ring XML | +X telescope, real one-module Tube layer representation |
| Injection | `geometry.prepare.write_shifted_xml`: Global X for SiMAPS L0–L4; bounded Y/Z and Rx/Ry/Rz for L1/L2/L3; full rotation matrices | `closure.displaced_xml`: finite physical Global Y translations for L1/L2 only |
| Rotation state | shared rigid transforms and left Global SO(3) increments; guarded supported modes | rotations unchanged; no rotation correction mode enabled |
| Channel generation | Geant4/DD4hep simulation and independent digitization/RawHit contract | `TelescopeChannels`: real displaced DD4hep sensor intersections and segmentation, no Geant4 or electronics |
| Correction | `correction.correct_geometry.correct/correct_so3`: actual Pede parameters, retained conventions and Survey/reference checks | `closure.correct`: actual Pede text + nominal XML, physical Global Y to negative module-local X |
| Rebuild Geometry | actual endcap constructor and manually fitted ACTS surfaces from poses | fresh process, installed services/provider/converter, official SurfaceMap and TrackingGeometry |
| Lifecycle | sequential input Controller, candidate version chain, convergence/recovery/explicit review | bounded automatic test stages, no registry/activation or continuous service |

Injection and correction have different inputs and purposes even when they reuse
an XML placement function. In the native closure, `geometry_step` writes separate
Truth XML from declared +0.150/+0.200 mm test shifts; `data_step` generates channels
from it. `correct` reads only nominal XML and Pede output, never Truth. `check`
uses offline Truth only for evaluation. The same shifted ROOT is reconstructed in
fresh nominal/corrected processes without changing channel bytes.

The two XML adapters are **not** interchangeable duplicated transforms: one edits
endcap ring/custom matrix attributes and the other clones barrel-constructor
modules and edits sensitive local positions. They share `geometry.transforms`
mathematics. Combining their hierarchy edits now would either lose rotation,
Survey, precision/sign/whitelist guarantees or introduce a new abstraction. No
such consolidation is attempted. Future migration must independently validate
each old degree of freedom in actual official Geometry/RawHit tracking first.

The old fixed ordered Rx/Ry scheme remains disabled after failed finite-rotation
closure. Its mathematical helpers/tests and refusal steering fingerprints are
retained; they are scientific negative evidence, not disposable unused utilities.
Full mode support is determined by existing scope and evidence gates, not merely
by the availability of six-column derivatives or an injection function.

## Deletions and duplication decisions

| E file deleted with git rm | Evidence / replacement | Loss / validation |
|---|---|---|
| `localDetEICrecon/build.sh` | four-line shim delegates unchanged arguments to `environment/build.sh`; all maintained operating guides now call that implementation directly; no runtime/test dependency | removes only obsolete command spelling; historical executions remain documented |
| `localDetEICrecon/alignment/CMakeLists.txt` | isolated static Writer build not used by either maintained CMake chain or Controller/tests; both build required Writer source directly | removes optional standalone static-library build convenience, not Writer source/API/equations or scientific coverage |

No category C algorithm was deleted. In particular, deleting the old fitter,
digitizer, Writer or Controller would remove real Geant4/RawHit endcap workflows,
validated rotations/SO(3)/multi-plane scopes and sequential calibration safeguards
that the two-Y native fixture does not replace. This migration is incomplete.

The category D equivalence test already uses a small executable plus Writer/tilt
sources, not the complete old production plugin. It is therefore retained rather
than rewriting an independent oracle to delete the same Writer that category C
still needs. Standalone CKF, finite-difference derivatives, data-only GLS/Schur,
mathematical fixture, negative converter and historical statistical diagnostics
remain distinct scientific checks. They are not competing alignment services.

`closure.py` mixes test-data setup, two-parameter orchestration and verification
because it is a bounded integration-test driver. Its inference stages use real
JANA/native ACTS/Mille/Pede, but the surrounding Truth generator and ROOT checks
are test-only. Existing named stage functions/CLI already make this boundary
explicit. Splitting them into another service/framework adds no benefit in this
cleanup and could misrepresent production readiness, so the driver is retained.

## Official EICrecon versus retained local components

Unchanged installed components are DD4hep/ACTS geometry services,
ActsGeometryProvider, converter, SurfaceMap/TrackingGeometry, TrackerHitReconstruction,
actual CKF function with Navigator/filter/smoother and ActsToTracks. The locally
copied measurement wrapper handles optional B0 metadata, missing VolumeContext,
and the telescope's CartesianGridXZ covariance projection. The copied CKF wrapper
honors the seed perigee and explicit electron hypothesis. Telescope-specific pieces
are input fixtures, endpoint seed, collection wiring, audit and native Mille
observer/model. Unchanged upstream helper headers compensate for installation
omissions. Exact source/provenance/patch comparisons remain in the
[code map](TELESCOPE_ALIGNMENT_CODE_MAP.md). None of these modules changed here.

## Execution and validation commands

All outputs below are fresh, ignored local artifacts; reruns require new names.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/telescope_consolidation_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/telescope_consolidation_20261024_01 -j2
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_consolidation_20261024_01 \
  --result result/telescope_consolidation_20261024_01 \
  --events 32 --chi2-cut 1000 --step all
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_consolidation_20261024_01 \
  --result result/telescope_consolidation_20261024_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name consolidation
python3 validation/verify_preservation.py
git diff --check
```

The preserved legacy plugin can be built through its single entry with a fresh
`TESTBENCH_BUILD_DIR`; see WORKFLOW.md. Legacy endcap build aliases and historical
static-writer instructions in past audit reports refer to those past revisions;
current operating guides and integration explanation are updated. No historical
execution command or dataset is silently rewritten.

## Executed validation results

All commands completed successfully in the fixed `sweet_mahavira` container.
Fresh build/result roots are named `telescope_consolidation_20261024_01`;
command/stdout/exit records for each stage remain under that result root.
Top-level build logs, parser AST proof, exact baseline comparison and official
Mille decoder output are in `result/telescope_consolidation_20261024_01_audit/`.

| Gate | Actual result |
|---|---|
| Fresh native plugin configure/build | exit 0 |
| Complete nominal → solve → correct → corrected/control reconstruction and check | passed |
| Nominal / corrected / control accepted | 32 / 32 / 32 |
| Per track measurements / outliers / expected holes | 5 / 0 / 2 |
| Per pass official Mille records / scalar equations | 32 / 320 |
| L1 / L2 recovered physical Global Y | +149.14 / +203.18 um |
| Nominal ACTS chi2/stored-NDF | 37.16731567382813 |
| Corrected ACTS chi2/stored-NDF | 0.6908491410315036 |
| Channel identity | same immutable ROOT within passes; canonical payload matches baseline |
| Actual XML and native Mille equations | nominal/Truth/corrected XML and all three Mille binaries byte-identical to pre-cleanup baseline |
| Scientific report fields | exact match to `result/telescope_rename_20261024_01/validation/report.json` (except regenerated ROOT full-file hash) |
| Derivative, surface-ID, XML whitelist and covariance gates | passed unchanged |
| Official Mille Binary decoder | 32 records |
| ROOT batch read-back | 42 objects |
| Consolidated regression suite | all 18 command exits 0 |
| Existing unit tests | all 46 passed |
| Independent standalone CKF versus one-event native plugin | chi2 difference 0; max position difference 5.4787285819202225e-12 mm |
| Safety and preservation | passed; 221 baseline and 2046 relocated files unchanged |
| Upstream patch reproducibility | all 9 unchanged |
| Shared parser | original AST identical; compatibility alias and clean-import isolation verified |
| Python / shell syntax | passed; all 13 remaining tracked shell scripts checked |
| Source scope review | only the two named E deletions; no C++/XML/numeric configuration edit |

Pede nominal/postsolve keeps end status 1 (warnings about bad measurements), process
exit 0, rank 2 and zero rejected local fits; control ends with status 0. No error
rescaling or scientific assertion was changed. Existing CMake policy warnings,
non-interactive stty messages and SQLite ResourceWarnings remain in the logs.
No GUI TBrowser interaction or new uncertainty-coverage validation is claimed.
An initial ad-hoc source guard incorrectly counted the explicitly approved deleted
CMakeLists.txt as a numeric edit; the corrected audit separately asserts the exact
two deletions and rejects any numeric/Geometry edits among retained files. No
scientific regression failed or assertion was relaxed.

### Retained endcap capability regression

The retained backend was also configured/built through the single build entry,
then tested against saved 100-event simulation in a new result directory:

```bash
bash environment/run.sh env \
  TESTBENCH_BUILD_DIR=/work/build/telescope_consolidation_legacy_20261024_01 \
  bash environment/build.sh
bash environment/run.sh bash validation/run_regression.sh \
  /work/result/telescope_consolidation_legacy_20261024_01 \
  /work/build/telescope_consolidation_legacy_20261024_01
bash environment/run.sh bash -lc 'export LD_LIBRARY_PATH=/work/external/install/lib:$LD_LIBRARY_PATH; exec /work/external/install/bin/inspectMilleBinary /work/result/telescope_consolidation_20261024_01/nominal/mille.dat'
```

Both build and regression exited 0. Reference comparison passed: 100 events,
99 accepted tracks before/after; L2 applied correction +198.75 um; mean residual
-199.57137554842703 → -0.8213645075978979 um; ACTS chi2/stored-NDF
45.59223484848485 → 1.9810397677951388. The old simulation was reused read-only,
not regenerated, reinterpreted or overwritten. Outputs are under
`result/telescope_consolidation_legacy_20261024_01/`, with logs in the audit root.
This representative regression plus existing rotation/SO(3)/Controller unit/safety
tests confirms preservation for this refactor; historical multi-DOF simulation
campaigns were not rerun and no new native six-DOF support is claimed.


## Appendix: complete retained module inventory

| Exact module | Class | Principal definitions / entry | Role and retention consequence | Static callers / build evidence |
|---|---|---|---|---|
| `alignment/__init__.py` | B | package marker / documentation | Retained guarded official Pede stage/steering (not derivative computation) | CLI / package / historical test entry; not proven obsolete |
| `alignment/align.py` | C | align | Retained guarded official Pede stage/steering (not derivative computation) | `calibration/iteration.py` |
| `alignment/align.sh` | C | exec python3 -m alignment.align "$@" | Retained guarded official Pede stage/steering (not derivative computation) | `validation/run_closure.sh` |
| `alignment/pede.py` | B | read_pede | Shared Pede text reader; new closure and retained callers | `alignment/align.py`, `calibration/iteration.py`, `correction/correct_geometry.py`, `validation/compare_raw_paths.py`, `validation/metrics.py`, `validation/so3_closure.py`, `validation/telescope_closure/closure.py` |
| `alignment/pede_l1_l2_l3_six_dof.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_l2_rotations.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_l2_rx_ry.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_l2_rz.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_l2_six_dof.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_l2_xy_rz.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_l2_xyz.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_l2_z.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_rotations.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_rx.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_rx_ry.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_ry.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_rz.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_six_dof.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_l1_z.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)`, `validation/test_z_alignment.py` |
| `alignment/pede_l3_six_dof.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py (canonical/dynamic mode steering)` |
| `alignment/pede_template.txt` | C | configuration / fixed reference (no function) | Retained guarded official Pede stage/steering (not derivative computation) | `alignment/align.py`, `alignment/align.py (canonical/dynamic mode steering)` |
| `calibration/__init__.py` | C | package marker / documentation | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | `calibration/controller.py`, `validation/test_z_alignment.py` |
| `calibration/config/l1_l2_l3_six_dof_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_rotations_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_rx_ry_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_rz_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_six_dof_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_x_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_xy_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_xy_rz_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_xyz_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_l2_z_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_rotations_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_rx_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | `validation/test_tilt_alignment.py` |
| `calibration/config/l1_rx_ry_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_ry_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_rz_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | `validation/test_rotation.py` |
| `calibration/config/l1_six_dof_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l1_z_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/config/l3_six_dof_demo.json` | C | configuration / fixed reference (no function) | Retained sequential/iterative lifecycle; no alignment derivative computation | CLI / package / historical test entry; not proven obsolete |
| `calibration/controller.py` | C | select, process, recover, main | Retained sequential/iterative lifecycle; no alignment derivative computation | `validation/test_calibration_controller.py` |
| `calibration/convergence.py` | C | evaluate, evaluate_rotation | Retained sequential/iterative lifecycle; no alignment derivative computation | `calibration/iteration.py`, `validation/test_calibration_controller.py`, `validation/test_rotation.py` |
| `calibration/geometry_manager.py` | C | l2_scope, Geometries | Retained sequential/iterative lifecycle; no alignment derivative computation | `calibration/controller.py`, `validation/test_calibration_controller.py` |
| `calibration/input_monitor.py` | C | inspect_manifest, verify_input, scan | Retained sequential/iterative lifecycle; no alignment derivative computation | `calibration/controller.py`, `validation/test_calibration_controller.py` |
| `calibration/iteration.py` | C | reconstruction_args, verify_outputs, iterate | Retained sequential/iterative lifecycle; no alignment derivative computation | `calibration/controller.py` |
| `calibration/queue_manager.py` | C | exclusive, recover_guard, Queue | Retained sequential/iterative lifecycle; no alignment derivative computation | `calibration/controller.py`, `validation/test_calibration_controller.py` |
| `calibration/runner.py` | C | stage | Retained sequential/iterative lifecycle; no alignment derivative computation | `calibration/controller.py`, `calibration/iteration.py` |
| `calibration/settings.py` | C | load | Retained sequential/iterative lifecycle; no alignment derivative computation | `validation/merge_so3_evidence.py`, `validation/test_rotation.py`, `validation/test_so3_alignment.py`, `validation/test_tilt_alignment.py`, `validation/test_z_alignment.py` |
| `correction/__init__.py` | C | package marker / documentation | Retained endcap Pede-to-XML update, scopes and Survey/SO(3) checks | CLI / package / historical test entry; not proven obsolete |
| `correction/correct_geometry.py` | C | ensure_correction_supported, correct, correct_so3 | Retained endcap Pede-to-XML update, scopes and Survey/SO(3) checks | `calibration/iteration.py`, `validation/merge_so3_evidence.py`, `validation/so3_closure.py`, `validation/test_geometry_correction.py`, `validation/test_so3_alignment.py`, `validation/test_z_alignment.py`, `validation/validate.py` |
| `correction/correct_geometry.sh` | C | exec python3 -m correction.correct_geometry "$@" | Retained endcap Pede-to-XML update, scopes and Survey/SO(3) checks | `validation/run_closure.sh` |
| `correction/scope.py` | C | fixed_layers_for, selected_labels, parameter_spec, layers_for, verify_scope, axes_for, verify_survey | Retained endcap Pede-to-XML update, scopes and Survey/SO(3) checks | `alignment/align.py`, `calibration/geometry_manager.py`, `calibration/iteration.py`, `calibration/settings.py`, `correction/correct_geometry.py`, `reconstruction/reconstruct.py`, `validation/merge_so3_evidence.py`, `validation/metrics.py`, `validation/so3_closure.py`, `validation/test_geometry_correction.py`, `validation/test_rotation.py`, `validation/test_so3_alignment.py`, `validation/test_tilt_alignment.py`, `validation/test_z_alignment.py`, `validation/tilt_observability.py`, `visualization/tilt_alignment.py` |
| `geometry/__init__.py` | C | package marker / documentation | Rigid transforms shared (B); otherwise retained endcap Geometry preparation/placement/QA | CLI / package / historical test entry; not proven obsolete |
| `geometry/environment.py` | C | geometry_environment | Rigid transforms shared (B); otherwise retained endcap Geometry preparation/placement/QA | `geometry/prepare.py`, `simulation/simulate.py`, `validation/legacy_endcap_experiment.py`, `validation/official_geometry.py`, `validation/validate_rz_derivatives.py`, `validation/validate_xy_derivatives.py`, `validation/validate_z_derivatives.py` |
| `geometry/nominal/seven_layer_telescope.xml` | B | configuration / fixed reference (no function) | Rigid transforms shared (B); otherwise retained endcap Geometry preparation/placement/QA | `digitization/contract.py`, `geometry/prepare.py`, `validation/telescope_geometry/check.py`, `validation/telescope_geometry/prepare.py`, `validation/test_calibration_controller.py`, `validation/test_geometry_correction.py`, `validation/test_raw_metadata.py` |
| `geometry/placements.py` | C | xml_number, geometry, placement_transforms | Rigid transforms shared (B); otherwise retained endcap Geometry preparation/placement/QA | `calibration/geometry_manager.py`, `correction/correct_geometry.py`, `correction/scope.py`, `validation/gdml_geometry_probe.py`, `validation/merge_so3_evidence.py`, `validation/metrics.py`, `validation/rz_statistics.py`, `validation/so3_closure.py`, `validation/test_geometry_correction.py`, `validation/test_rotation.py`, `validation/test_so3_alignment.py`, `validation/test_tilt_alignment.py`, `validation/test_z_alignment.py`, `validation/tilt_observability.py`, `validation/validate_xy_derivatives.py`, `visualization/closure.py`, `visualization/tilt_alignment.py`, `visualization/z_alignment.py` |
| `geometry/prepare.py` | C | ring, load_geometry_config, write_shifted_xml, modified_xml, gdml_positions, verify_positions, prepare | Rigid transforms shared (B); otherwise retained endcap Geometry preparation/placement/QA | `calibration/iteration.py`, `correction/correct_geometry.py`, `validation/merge_so3_evidence.py`, `validation/so3_closure.py`, `validation/test_geometry_correction.py`, `validation/test_rotation.py`, `validation/test_so3_alignment.py`, `validation/test_tilt_alignment.py`, `validation/test_z_alignment.py`, `validation/validate_rz_derivatives.py`, `validation/validate_tilt_derivatives.py`, `validation/validate_xy_derivatives.py`, `validation/validate_z_derivatives.py` |
| `geometry/prepare_geometry.sh` | C | exec python3 -m geometry.prepare "$@" | Rigid transforms shared (B); otherwise retained endcap Geometry preparation/placement/QA | `validation/check_safety.py`, `validation/run_closure.sh` |
| `geometry/scenarios/L1_L2_rotations.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_rx_ry.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_rx_ry_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_rz.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_rz_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_six_dof.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_xy.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_xy_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_xy_rz.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_xy_rz_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_xyz.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_xyz_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_z.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_L2_z_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_rotations.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_rx.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_rx_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_rx_ry.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_rx_ry_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_ry.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_ry_negative.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_ry_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_rz10mrad.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_rz_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_six_dof.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_x100um_L2_x200um.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | `validation/check_safety.py` |
| `geometry/scenarios/L1_x150um_L2_x200um.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_z2mm.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L1_z_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | `validation/test_z_alignment.py` |
| `geometry/scenarios/L1_zminus2mm.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/L2_x200um.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | `geometry/prepare.py` |
| `geometry/scenarios/l1_l2_l3_six_dof.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l1_l2_l3_six_dof_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l1_l2_l3_six_dof_survey.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l1_l2_rotations_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l1_l2_six_dof_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l1_rotations_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l1_six_dof_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l3_six_dof.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l3_six_dof_reference.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/l3_six_dof_survey.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/scenarios/my_first_test.json` | C | configuration / fixed reference (no function) | Deliberate endcap Truth displacement configuration, not inferred corrections | CLI / package / historical test entry; not proven obsolete |
| `geometry/transforms.py` | B | matvec, add, multiply, transpose, RigidTransform, axis_rotation, rotation_exp, rotation_log, orientation_distance, ordered_xy_axes, ordered_xy_increment | Rigid transforms shared (B); otherwise retained endcap Geometry preparation/placement/QA | `correction/correct_geometry.py`, `correction/scope.py`, `geometry/placements.py`, `geometry/prepare.py`, `validation/merge_so3_evidence.py`, `validation/so3_closure.py`, `validation/telescope_closure/closure.py`, `validation/test_rotation.py`, `validation/test_so3.py`, `validation/test_so3_alignment.py`, `validation/test_tilt_alignment.py`, `validation/test_transforms.py`, `validation/validate_tilt_derivatives.py`, `visualization/tilt_alignment.py` |
| `localDetEICrecon/CMakeLists.txt` | C | BeamTestReco, LocalTelescopeGeometry, TelescopeGeometryProbe | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | CLI / package / historical test entry; not proven obsolete |
| `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.cc` | C | SiliconTrackerDigi::init, SiliconTrackerDigi::process, std::hypot, std::llround, std::min | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `digitization/digitize.py`, `localDetEICrecon/CMakeLists.txt` |
| `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.h` | C | SiliconTrackerDigi, UniqueIDGenSvc::instance | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.cc`, `localDetEICrecon/factories/digi/SiliconTrackerDigi_factory.h` |
| `localDetEICrecon/algorithms/digi/SiliconTrackerDigiConfig.h` | C | SiliconTrackerDigiConfig | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `digitization/digitize.py`, `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.cc`, `localDetEICrecon/algorithms/digi/SiliconTrackerDigi.h` |
| `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc` | C | init, fitSelected, process, Calibrator::calibrate, SurfaceAccessor::operator() | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/CMakeLists.txt`, `validation/merge_so3_evidence.py` |
| `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.h` | C | BeamTestACTSFitter, FitSourceLink, FitMeas, LayerHit, FitResultSummary, StateDiag, FitResultBundle, SurfaceAccessor, Calibrator, Vector2::Zero, SquareMatrix2::Zero, BoundMatrix::Zero, GeometryContext::dangerouslyDefaultConstruct | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc`, `localDetEICrecon/factories/tracking/BeamTestACTSFitter_factory.h`, `validation/merge_so3_evidence.py` |
| `localDetEICrecon/algorithms/tracking/BeamTestACTSFitterConfig.h` | C | BeamTestACTSFitterConfig | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.h`, `validation/merge_so3_evidence.py` |
| `localDetEICrecon/algorithms/tracking/TrackerHitReconstruction.cc` | C | Acc, TrackerHitReconstruction::process, std::runtime_error, std::size | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/CMakeLists.txt` |
| `localDetEICrecon/algorithms/tracking/TrackerHitReconstruction.h` | C | TrackerHitReconstruction, GeoSvc::instance | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/algorithms/tracking/TrackerHitReconstruction.cc`, `localDetEICrecon/factories/tracking/TrackerHitReconstructionNoAssoc_factory.h`, `localDetEICrecon/factories/tracking/TrackerHitReconstruction_factory.h` |
| `localDetEICrecon/algorithms/tracking/TrackerHitReconstructionConfig.h` | C | TrackerHitReconstructionConfig | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/algorithms/tracking/TrackerHitReconstruction.h` |
| `localDetEICrecon/alignment/src/BeamTestMilleWriter.cc` | C | BeamTestMilleWriter::BeamTestMilleWriter, Mille::spawnMilleRecord, std::runtime_error, BeamTestMilleWriter::labelAx, BeamTestMilleWriter::labelAy, BeamTestMilleWriter::writeTrackRecord, std::begin, std::end, Vector4d::Zero, Matrix4d::Zero, Eigen::Vector3d, Eigen::Vector2d, std::setprecision, Vector3d::UnitZ, Vector3d::UnitX, Vector3d::UnitY, std::a | Distinct endcap writer/tilt model, also independent native-equivalence reference | `calibration/settings.py`, `localDetEICrecon/CMakeLists.txt`, `localDetEICrecon/experimental/telescope/CMakeLists.txt`, `validation/merge_so3_evidence.py`, `validation/so3_closure.py`, `validation/validate_tilt_derivatives.py` |
| `localDetEICrecon/alignment/src/BeamTestMilleWriter.h` | C | MilleRecord, BeamTestMilleWriter, Hit2D, Config | Distinct endcap writer/tilt model, also independent native-equivalence reference | `localDetEICrecon/alignment/src/BeamTestMilleWriter.cc`, `localDetEICrecon/processors/BeamTestMilleProcessor.cc`, `localDetEICrecon/processors/BeamTestMilleProcessor.h`, `validation/merge_so3_evidence.py`, `validation/so3_closure.py`, `validation/telescope_alignment/LegacyTelescopeCrosscheck.cc`, `validation/tilt_writer_fixture.cc` |
| `localDetEICrecon/alignment/src/TiltMeasurementModel.h` | C | Eigen::Vector2d, std::runtime_error, Matrix2d::Identity, tiltResidualJacobian, tiltWhitening, physicalRotationDerivative | Distinct endcap writer/tilt model, also independent native-equivalence reference | `localDetEICrecon/alignment/src/BeamTestMilleWriter.cc`, `validation/merge_so3_evidence.py`, `validation/so3_closure.py` |
| `localDetEICrecon/experimental/telescope/CMakeLists.txt` | A | TestbenchBarrelMetadata, TelescopeTracking, NativeMilleModel, TelescopeMille, TelescopeChannels, TelescopeMilleFixture, LegacyTelescopeCrosscheck, TelescopeMilleDerivatives | Active official/adapted factory chain or required support/configuration | CLI / package / historical test entry; not proven obsolete |
| `localDetEICrecon/experimental/telescope/FactoryAudit.h` | A | FactoryAudit, json::array, filesystem::exists, std::runtime_error, GeoSvc::instance, Vector3::UnitX, Acts::Vector2, std::abs, Acts::makeDirectionFromPhiTheta, std::max | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/TelescopeTracking.cc` |
| `localDetEICrecon/experimental/telescope/TelescopeTracking.cc` | A | InitPlugin | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `localDetEICrecon/experimental/telescope/algorithms/TelescopeSeed.h` | A | TelescopeSeed, std::runtime_error, Acts::Vector3, std::atan2, std::acos | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/factories/TelescopeSeed_factory.h` |
| `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTracking.cc` | A | EDM4eicMeasurementSourceLinkCalibrator, Vector2::Zero, CKFTracking::init, Acts::getDefaultLogger, eicrecon::SpdlogToActsLevel, Acts::GeometryIdentifier, CKFTracking::makeCKFTrackingFunction, CKFTracking::process, Acts::ConstVectorMultiTrajectory, Acts::ConstVectorTrackContainer, BoundMatrix::Zero, BoundSquareMatrix::Zero, Acts::Vector3, ParticleHyp | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTracking.h` | A | CKFTracking, ActsSvc::instance | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTracking.cc`, `localDetEICrecon/experimental/telescope/factories/tracking/CKFTracking_factory.h`, `validation/telescope_one_track/TelescopeOneTrack.cc` |
| `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTrackingConfig.h` | A | CKFTrackingConfig | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTracking.h`, `localDetEICrecon/experimental/telescope/factories/tracking/CKFTracking_factory.h` |
| `localDetEICrecon/experimental/telescope/algorithms/tracking/TrackerMeasurementFromHits.cc` | A | TrackerMeasurementFromHits::init, GeoSvc::instance, std::runtime_error, TrackerMeasurementFromHits::process, SquareMatrix2::Zero, dd4hep::Position, Vector2::Zero | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `localDetEICrecon/experimental/telescope/algorithms/tracking/TrackerMeasurementFromHits.h` | A | TrackerMeasurementFromHits, GeoSvc::instance, ActsSvc::instance | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/algorithms/tracking/TrackerMeasurementFromHits.cc`, `localDetEICrecon/experimental/telescope/factories/tracking/TrackerMeasurementFromHits_factory.h`, `validation/telescope_one_track/TelescopeOneTrack.cc` |
| `localDetEICrecon/experimental/telescope/alignment/NativeMilleModel.cc` | A | nativeEquation, rayMeasurement | Native TrackState residual/Jacobian equations and official Mille observer | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `localDetEICrecon/experimental/telescope/alignment/NativeMilleModel.h` | A | NativeEquation, nativeEquation | Native TrackState residual/Jacobian equations and official Mille observer | `localDetEICrecon/experimental/telescope/CMakeLists.txt`, `localDetEICrecon/experimental/telescope/alignment/NativeMilleModel.cc`, `localDetEICrecon/experimental/telescope/alignment/TelescopeMille.cc`, `validation/telescope_alignment/TelescopeMilleDerivatives.cc`, `validation/telescope_alignment/TelescopeMilleFixture.cc` |
| `localDetEICrecon/experimental/telescope/alignment/TelescopeMille.cc` | A | Derived, TelescopeMilleProcessor, Row, json::array, std::runtime_error, filesystem::exists, json::parse, std::ifstream, std::sort, GeoSvc::instance, Acts::Vector2, SquareMatrix2::Identity, std::move, Mille::spawnMilleRecord, InitPlugin, nativeEquation | Native TrackState residual/Jacobian equations and official Mille observer | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `localDetEICrecon/experimental/telescope/extensions/edm4eic/EDM4eicToActs.h` | A | typed configuration / native helper definitions | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTracking.cc` |
| `localDetEICrecon/experimental/telescope/factories/SyntheticTrackerHits_factory.h` | A | SyntheticTrackerHits_factory, GeoSvc::instance, std::runtime_error, std::pow | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/TelescopeTracking.cc` |
| `localDetEICrecon/experimental/telescope/factories/TelescopeSeed_factory.h` | A | TelescopeSeed_factory | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/TelescopeTracking.cc` |
| `localDetEICrecon/experimental/telescope/factories/tracking/CKFTracking_factory.h` | A | CKFTracking_factory | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/TelescopeTracking.cc` |
| `localDetEICrecon/experimental/telescope/factories/tracking/TrackerMeasurementFromHits_factory.h` | A | TrackerMeasurementFromHits_factory | Active official/adapted factory chain or required support/configuration | `localDetEICrecon/experimental/telescope/TelescopeTracking.cc` |
| `localDetEICrecon/experimental/telescope/provenance.json` | A | configuration / fixed reference (no function) | Active official/adapted factory chain or required support/configuration | CLI / package / historical test entry; not proven obsolete |
| `localDetEICrecon/experimental/telescope/upstream_support/algorithms/meta/CollectionCollector.h` | A | T, CollectionCollector | Active official/adapted factory chain or required support/configuration | CLI / package / historical test entry; not proven obsolete |
| `localDetEICrecon/factories/digi/SiliconTrackerDigi_factory.h` | C | LocalSiliconTrackerDigi_factory | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/plugins/BeamTestReco.cc` |
| `localDetEICrecon/factories/tracking/BeamTestACTSFitter_factory.h` | C | BeamTestACTSFitter_factory, surfacePlacements | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/plugins/BeamTestReco.cc`, `validation/merge_so3_evidence.py` |
| `localDetEICrecon/factories/tracking/TrackerHitReconstructionNoAssoc_factory.h` | C | LocalTrackerHitReconstructionNoAssoc_factory | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/plugins/BeamTestReco.cc` |
| `localDetEICrecon/factories/tracking/TrackerHitReconstruction_factory.h` | C | LocalTrackerHitReconstruction_factory | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/experimental/telescope/TelescopeTracking.cc`, `localDetEICrecon/plugins/BeamTestReco.cc` |
| `localDetEICrecon/geometry/OfficialGeometryProbe.cc` | C | main | Endcap placement/builder or historical official-converter diagnostic | `localDetEICrecon/CMakeLists.txt`, `validation/legacy_endcap_experiment.py`, `validation/official_geometry.py` |
| `localDetEICrecon/geometry/SiTrackerEndcap2XY_geo.cpp` | C | std::cos, std::sin, std::runtime_error, xml::Strng_t, std::isfinite, std::abs | Endcap placement/builder or historical official-converter diagnostic | `localDetEICrecon/CMakeLists.txt`, `validation/merge_so3_evidence.py` |
| `localDetEICrecon/geometry/SurfacePlacements.h` | C | std::runtime_error, dd4hep::Position, Acts::Vector3, std::abs, Transform3::Identity, std::setprecision, surfacePlacements | Endcap placement/builder or historical official-converter diagnostic | `localDetEICrecon/factories/tracking/BeamTestACTSFitter_factory.h`, `localDetEICrecon/geometry/OfficialGeometryProbe.cc`, `localDetEICrecon/processors/BeamTestMilleProcessor.cc`, `validation/merge_so3_evidence.py` |
| `localDetEICrecon/plugins/BeamTestReco.cc` | C | std::runtime_error, local_eicrecon::BeamTestEventProcessor, local_eicrecon::BeamTestMilleProcessor, InitPlugin | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `digitization/digitize.py`, `localDetEICrecon/CMakeLists.txt` |
| `localDetEICrecon/processors/BeamTestEventProcessor.cc` | C | BeamTestEventProcessor::Init, BeamTestEventProcessor::Process, BeamTestEventProcessor::Finish | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/CMakeLists.txt` |
| `localDetEICrecon/processors/BeamTestEventProcessor.h` | C | BeamTestEventProcessor | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/plugins/BeamTestReco.cc`, `localDetEICrecon/processors/BeamTestEventProcessor.cc` |
| `localDetEICrecon/processors/BeamTestMilleProcessor.cc` | C | BeamTestMilleProcessor::decodeLayer, BeamTestMilleProcessor::Init, std::runtime_error, BeamTestMilleProcessor::Process, std::max, std::sqrt, BeamTestMilleProcessor::Finish, surfacePlacements | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/CMakeLists.txt`, `validation/merge_so3_evidence.py` |
| `localDetEICrecon/processors/BeamTestMilleProcessor.h` | C | BeamTestMilleProcessor | Retained endcap digitization/RecHit/manual-surface fitter and JANA registration/build | `localDetEICrecon/plugins/BeamTestReco.cc`, `localDetEICrecon/processors/BeamTestMilleProcessor.cc` |
| `reconstruction/__init__.py` | C | package marker / documentation | Retained BeamTestReco invocation, RawHit contract and runtime setup | CLI / package / historical test entry; not proven obsolete |
| `reconstruction/configs/electron_1GeV.json` | C | configuration / fixed reference (no function) | Retained BeamTestReco invocation, RawHit contract and runtime setup | `reconstruction/reconstruct.py` |
| `reconstruction/configs/muon_5GeV.json` | C | configuration / fixed reference (no function) | Retained BeamTestReco invocation, RawHit contract and runtime setup | CLI / package / historical test entry; not proven obsolete |
| `reconstruction/reconstruct.py` | C | reconstruct | Retained BeamTestReco invocation, RawHit contract and runtime setup | `calibration/controller.py`, `calibration/iteration.py`, `validation/merge_so3_evidence.py` |
| `reconstruction/reconstruct.sh` | C | exec python3 -m reconstruction.reconstruct "$@" | Retained BeamTestReco invocation, RawHit contract and runtime setup | `validation/run_closure.sh` |
| `reconstruction/reconstruct_corrected.sh` | C | exec python3 -m reconstruction.reconstruct --after "$@" | Retained BeamTestReco invocation, RawHit contract and runtime setup | `validation/run_closure.sh` |
| `reconstruction/runtime.py` | C | runtime | Retained BeamTestReco invocation, RawHit contract and runtime setup | `digitization/digitize.py`, `reconstruction/reconstruct.py` |
| `validation/__init__.py` | D | package marker / documentation | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/check_root_outputs.py` | D | package marker / documentation | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/check_safety.py` | D | rejected | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/telescope_closure/closure.py` |
| `validation/compare_geometry_providers.py` | D | compare, main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/compare_raw_paths.py` | D | collections, id_names, canonical, compare_files, main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/compare_geometry_providers.py` |
| `validation/gdml_geometry_probe.py` | D | validate | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/geometry_probe.py` | D | probe | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/validate_rz_derivatives.py`, `validation/validate_tilt_derivatives.py`, `validation/validate_xy_derivatives.py`, `validation/validate_z_derivatives.py` |
| `validation/legacy_endcap_experiment.py` | D | main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/merge_so3_evidence.py` | D | merge, main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `calibration/settings.py` |
| `validation/metrics.py` | D | root_branch, measurements, mean_error, serializable, calculate | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/validate.py`, `visualization/closure.py`, `visualization/z_alignment.py` |
| `validation/official_geometry.py` | D | main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/reference_metrics.json` | D | configuration / fixed reference (no function) | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/run_regression.sh` |
| `validation/rotation_observability.py` | D | information | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/run_closure.sh` | D | shell stage driver | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/check_safety.py`, `validation/run_regression.sh` |
| `validation/run_regression.sh` | D | exec bash "$repo/validation/run_closure.sh" \ | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/rz_statistics.py` | D | exclusive_json, track_metrics, pede_metrics, summarize, collect, main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `visualization/tilt_alignment.py`, `visualization/z_alignment.py` |
| `validation/so3_closure.py` | D | generate_local, run_case, main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/telescope_alignment/LegacyTelescopeCrosscheck.cc` | D | main | Independent benchmark, derivative, provenance or writer-equivalence validation | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `validation/telescope_alignment/TelescopeMilleDerivatives.cc` | D | main | Independent benchmark, derivative, provenance or writer-equivalence validation | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `validation/telescope_alignment/TelescopeMilleFixture.cc` | D | main | Independent benchmark, derivative, provenance or writer-equivalence validation | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `validation/telescope_alignment/check.py` | D | records, profile, main | Independent benchmark, derivative, provenance or writer-equivalence validation | `validation/telescope_closure/closure.py` |
| `validation/telescope_alignment/l1_l2_global_y.json` | D | configuration / fixed reference (no function) | Independent benchmark, derivative, provenance or writer-equivalence validation | `validation/telescope_closure/closure.py` |
| `validation/telescope_closure/TelescopeChannels.cc` | A | main | Current bounded synthetic channel closure: fixture, inference and checks | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `validation/telescope_closure/closure.py` | A | displaced_xml, environment, channel_values, channel_digest, pack, geometry_step, data_step, reconstruct, solve, correct, check, regressions, main | Current bounded synthetic channel closure: fixture, inference and checks | CLI / package / historical test entry; not proven obsolete |
| `validation/telescope_factories/check.py` | D | main | Independent benchmark, derivative, provenance or writer-equivalence validation | `validation/telescope_closure/closure.py` |
| `validation/telescope_factories/prepare.py` | D | main | Independent benchmark, derivative, provenance or writer-equivalence validation | `validation/telescope_closure/closure.py` |
| `validation/telescope_factories/upstream_diff.py` | D | main | Independent benchmark, derivative, provenance or writer-equivalence validation | CLI / package / historical test entry; not proven obsolete |
| `validation/telescope_geometry/BarrelMetadata.cc` | A | std::runtime_error, rec::VariantParameters, initializeBarrelMetadata | Current fixture construction/metadata and real Geometry audit | `localDetEICrecon/experimental/telescope/CMakeLists.txt`, `validation/telescope_geometry/CMakeLists.txt`, `validation/telescope_one_track/CMakeLists.txt` |
| `validation/telescope_geometry/CMakeLists.txt` | A | TelescopeGeometryProbe, TestbenchBarrelMetadata | Current fixture construction/metadata and real Geometry audit | CLI / package / historical test entry; not proven obsolete |
| `validation/telescope_geometry/TelescopeGeometryProbe.cc` | A | main | Current fixture construction/metadata and real Geometry audit | `validation/telescope_geometry/CMakeLists.txt` |
| `validation/telescope_geometry/check.py` | A | check, check_integration | Current fixture construction/metadata and real Geometry audit | `validation/telescope_closure/closure.py` |
| `validation/telescope_geometry/prepare.py` | A | prepare | Current fixture construction/metadata and real Geometry audit | `validation/telescope_closure/closure.py` |
| `validation/telescope_one_track/CMakeLists.txt` | D | TestbenchBarrelMetadata, TelescopeOneTrack | Independent benchmark, derivative, provenance or writer-equivalence validation | CLI / package / historical test entry; not proven obsolete |
| `validation/telescope_one_track/TelescopeOneTrack.cc` | D | main | Independent benchmark, derivative, provenance or writer-equivalence validation | `validation/telescope_one_track/CMakeLists.txt` |
| `validation/test_calibration_controller.py` | D | ControllerTests | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_geometry_correction.py` | D | CorrectionTests | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_raw_metadata.py` | D | MetadataTests | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_rotation.py` | D | Rotation | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_so3.py` | D | SO3Tests | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_so3_alignment.py` | D | CoupledTests | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_tilt_alignment.py` | D | Tilt | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_transforms.py` | D | TransformTests, GaugeTests | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/test_z_alignment.py` | D | ZAlignment | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/tilt_hit_audit.py` | D | audit | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/tilt_observability.py` | D | diagnose, enforce, main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `calibration/iteration.py` |
| `validation/tilt_writer_fixture.cc` | D | main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/so3_closure.py`, `validation/validate_tilt_derivatives.py` |
| `validation/validate.py` | D | validate | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/validate.sh` | D | exec python3 -m validation.validate "$@" | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/run_closure.sh` |
| `validation/validate_rz_derivatives.py` | D | records, check_binary, merge_gate, validate | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/compare_geometry_providers.py`, `validation/test_rotation.py`, `validation/z_observability.py` |
| `validation/validate_tilt_derivatives.py` | D | whitening, profile, validate | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/validate_xy_derivatives.py` | D | binary_derivatives, validate | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/validate_z_derivatives.py` | D | validate | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/validated_environment.json` | D | configuration / fixed reference (no function) | Retained scientific test, observability/statistics/closure diagnostic or preservation input | CLI / package / historical test entry; not proven obsolete |
| `validation/verify_preservation.py` | D | package marker / documentation | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `validation/telescope_closure/closure.py` |
| `validation/z_observability.py` | D | measurements, information, diagnose, enforce, main | Retained scientific test, observability/statistics/closure diagnostic or preservation input | `calibration/iteration.py`, `validation/so3_closure.py`, `validation/test_z_alignment.py`, `validation/tilt_observability.py`, `validation/validate_tilt_derivatives.py`, `validation/validate_z_derivatives.py`, `visualization/z_alignment.py` |
