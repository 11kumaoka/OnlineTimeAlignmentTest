# Calibration entry points

## Primary native workflow

Use `python3 -B -m calibration.workflow run` for the maintained npsim -> official
Digitization -> native ACTS/Mille -> Pede -> Geometry Correction chain. Start with
`config/native_workflow_smoke.json` and the
[practical User Guide](../docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md).
`native_controller.py` manages one immutable native RawHit dataset and its
verified correction checkpoints. Its strict/diagnostic policies never approve
or activate candidate Geometry. See the
[native Controller guide](../docs/NATIVE_CALIBRATION_CONTROLLER.md).

## Retained legacy +Z queue Controller

Everything below describes `calibration.controller`, the separate BeamTestReco
queue/registry interface. It retains sequential delivery, once/watch, retry and
explicit review/activation capabilities and legacy alignment scopes that the
native one-file Controller does not replace. Its lock and process-supervision
helpers are also reused by the native path. Historical commands and limits are
retained here; do not use this configuration schema for `calibration.workflow`.

This single-worker prototype discovers complete RawHit deliveries, reconstructs each file, and optionally runs fixed-dataset selected SiMAPS alignment iterations. It invokes the existing C++ Plugin and official Millepede-II through the independent stage modules. It does not implement numerical tracking or solving in Python.

## Environment and configuration

For this retained +Z path, use the initialized EIC container and compiled `BeamTestReco.so`. Start with `calibration/config/demo.json`. Set `build_dir` to the validated build directory. Paths in this JSON resolve against the repository root. Configuration and dependency checksums are pinned to a controller state: changed settings or binaries require a **new** state directory.

Calibration is disabled by default. Enable it only with an explicit reference/survey fallback and compatible RawHit readout/channel definitions. **No true physical Geometry is required.** `calibration.measured_geometry` is retained solely as an optional legacy simulation-provenance check; leave it null for truth-free operation. It never provides correction values.

`calibration.correction_mode` defaults to `l2_x`; explicit `l1_l2_x` and `l1_l2_xy` support the selected SiMAPS L1/L2 components. The XY mode composes all four residual updates with the current Geometry and preserves fixed surveyed placements elsewhere. Survey placement changes must retain the validated hierarchy, readout and plane orientations; arbitrary rotated or restructured XML remains unsupported. Each selected component must satisfy the configured convergence tolerance. Global Z and individual L1 Rx/Ry require the explicit gated modes below. Old fixed-Global two-axis Rx/Ry modes remain disabled. Explicit coupled SO(3) scopes use the additional gates below; material, MPGD and AC-LGAD alignment remain unsupported.

Demonstration track-count, update, chi2 and convergence cuts are configurable and **not scientifically established calibration criteria**. The chi2 ratio follows the existing stored EDM track ndf convention. Read [Geometry conventions](../docs/GEOMETRY_CONVENTIONS.md) for sensor axes, survey/reference semantics, gauge constraints and the six-DOF mathematical foundation.

## Atomic delivery protocol

`input/` contains incoming data only. The controller never moves or deletes deliveries. The producer must finish and close each file, atomically rename ROOT and metadata files to final names on the same filesystem, then publish `NAME.ready.json` **last** by atomic rename. Names and transport are not assumptions about E0: this manifest is the prototype adapter interface.

```json
{
  "schema": "rawhit-delivery-v1",
  "input_id": "run42-part1",
  "sequence": 1,
  "raw_file": "part1.root",
  "raw_sha256": "SHA256_OF_ROOT",
  "metadata_file": "part1.metadata.json",
  "metadata_sha256": "SHA256_OF_METADATA"
}
```

The metadata must satisfy [the RawHit contract](../docs/RAWHIT_BOUNDARY.md). Checksums, collection types, Cell IDs and EventHeader identities are checked before acceptance. Files without a marker are ignored; invalid markers appear in queue issues. Input paths must remain inside the input directory. Producer files must remain immutable and available while their processing history is retained.

`ordering: sequence` requires unique upstream integer sequences and starts at `first_sequence`. A gap is recorded; `gap_policy: wait` holds later jobs, `error` stops, and explicit `skip` journals the omitted range. An older late sequence is refused, requiring operator resolution in a separate state. `ordering: identity` is an explicit fallback sorted by input identifier; it rejects manifests containing sequence numbers rather than ignoring acquisition order. Once mode captures eligible inputs at startup; deliveries discovered during execution remain queued for the next invocation. Watch mode accepts later arrivals continuously. Duplicate identifiers, raw checksums or sequences are rejected.

## Commands

Run these inside the container using `bash environment/run.sh COMMAND ...` from the host. Supply the same configuration, input directory and state directory to state-changing commands.

```sh
python3 -m calibration.controller once --config calibration/config/demo.json --input-dir input --state-dir result/controller_demo
python3 -m calibration.controller watch --config calibration/config/demo.json --input-dir input --state-dir result/controller_demo
python3 -m calibration.controller queue --state-dir result/controller_demo
python3 -m calibration.controller geometry --state-dir result/controller_demo
python3 -m calibration.controller retry --config calibration/config/demo.json --input-dir input --state-dir result/controller_demo --input-id run42-part1 --reason 'Transient failure resolved'
python3 -m calibration.controller calibrate --config calibration/config/demo.json --input-dir input --state-dir result/controller_demo --input-id run42-part1
```

`queue` and `geometry` are **check-only** and do not initialize state. All other commands change state. Normal writers acquire both an atomic directory guard and an exclusive Unix file lock; the directory guard is necessary because advisory locks were not reliable across processes on the tested Docker bind mount. Stop a foreground controller with Ctrl-C or SIGTERM: the current stage finishes, and no next stage starts. Restart the same command; completed inputs are verified and skipped. Interrupted attempts require explicit `retry`, followed by `once` or `watch`. Retries use fresh attempt directories and the original pinned Geometry; `max_attempts` bounds ingestion attempts. Manual calibration requires a completed input and enabled policy and creates another explicitly requested attempt. No automatic retries occur.

The SQLite queue records input provenance, readiness, sequence, status, attempts, outputs, selected Geometry and failures; its event journal records lifecycle changes. Results live below `result/STATE/jobs/INPUT/attempt-NNN/`. Original bytes are copied to an immutable-by-contract input snapshot and hash checked. Iterations use this same snapshot, produce separate output directories and compose the selected Global X residual corrections with their current Geometry. Per-file reconstruction Geometry remains pinned; iterative candidate versions are recorded separately. Active Geometry never changes automatically, including on failure or nonconvergence. No cross-file accumulation is implemented.

A polling thread discovers File B while File A's subprocesses run; there is exactly one processing worker. Child stage processes retain the state lock if the controller dies. After an abrupt kill, the atomic guard remains. Wait for children to finish, then explicitly run `python3 -m calibration.controller recover-lock --state-dir result/controller_demo --input-dir input --reason "Owner killed; recovery inspected"`. This state-changing command refuses recovery if the recorded owner or any recorded stage process group remains alive, or if the owner belongs to another host/container. An incomplete guard record or a different host requires operator inspection; it is not automatically removed. Then restart and explicitly retry interrupted inputs. Partial directories are retained, never reused. Registry creation interrupted before its database record is committed requires operator inspection; the controller refuses to overwrite an orphaned version directory.

## Candidate review and activation

Geometry XML snapshots are content-addressed below `STATE/geometries/geo-SHA256/`. The initial active version is the explicitly configured nominal/survey fallback. A converged candidate is **not** validated merely because its fit converged. Run independent held-out validation, inspect residuals, pulls, tracking behavior and the physical adequacy of the model, and record an operator review. This prototype verifies report identities and checksums; it cannot certify the scientific validity of an operator's claims.

An independent JSON report must contain `geometry_sha256`, `raw_sha256` identifying a distinct held-out dataset, and `passed: true`. The review JSON is:

```json
{
  "version_id": "geo-FULL_GEOMETRY_SHA256",
  "approved": true,
  "reviewer": "Operator name",
  "rationale": "Explain independent checks and their limits",
  "independent_validation": {"path": "/work/result/heldout/report.json", "sha256": "REPORT_SHA256"}
}
```

Stop watch mode before changing registry state. Review and activation are separate, explicit state changes:

```sh
python3 -m calibration.controller review --config calibration/config/demo.json --input-dir input --state-dir result/controller_demo --version-id geo-SHA256 --evidence result/review.json
python3 -m calibration.controller activate --config calibration/config/demo.json --input-dir input --state-dir result/controller_demo --version-id geo-SHA256
```

Review copies the independent report and operator statement into registry history. Activation verifies evidence checksums and records the previous active pointer; older Geometry bytes and per-file selections remain available. Subsequent inputs select the newly active version. No validity-interval, automatic activation, E0 network adapter, daemon, concurrent physics/calibration scheduler or distributed execution is implemented.

Executed checks and known prototype limits are recorded in [the validation report](../docs/CALIBRATION_CONTROLLER_VALIDATION.md).

## Simultaneous L1/L2 Global X

Use `calibration/config/l1_l2_x_demo.json` as the template for a **new** controller state. Set `build_dir`, enable calibration, and optionally supply `calibration.measured_geometry` only to verify known simulation provenance. The shipped template remains disabled until configured. Its canonical simulation scenario is L1 +0.150 mm / L2 +0.200 mm; that scenario does not provide the inferred corrections. Both residual updates must satisfy the demonstration tolerance before the candidate is declared converged; neither update activates it. Changing correction mode requires a new state because the configuration fingerprint changes. See [executed validation and commands](../docs/L1_L2_ITERATIVE_VALIDATION.md).

## Survey-based L1/L2 X/Y

Use `calibration/config/l1_l2_xy_demo.json` with an explicitly selected `fallback_geometry`, enabled policy and validated build directory. Its zero-displacement scenario is a hierarchy/scope preparation input, **not physical truth**. RawHit schema v2 checks readout and topology without requiring simulation truth. Existing v1 simulation sidecars remain readable without reinterpretation of their legacy field. The queue, locking, once/watch, retries and explicit review/activation interfaces are unchanged. Candidate Geometry remains inactive after convergence.

When correcting independently from a noncanonical survey, pass the same reference used by the fit:

```sh
python3 -m correction.correct_geometry --result-dir result/RUN --mode l1_l2_xy --base-geometry result/CURRENT.xml --reference-geometry result/SURVEY.xml
```

Only L1/L2 X/Y are updated; fixed surveyed centers are preserved. See [the XY validation report](../docs/XY_FOUNDATION_VALIDATION.md) for executed truth-excluded, simulation-backed tests and limitations. These tests are not actual DAQ validation.

## Experimental Global Z rotation modes

Rotation support is staged: `l1_rz`, `l1_l2_rz`, and `l1_l2_xy_rz`.
The default remains `l2_x`. Use `config/l1_rz_demo.json`, `config/l1_l2_rz_demo.json`, or
`config/l1_l2_xy_rz_demo.json` as a disabled example;
set the build, input/state paths and a **matching derivative-validation gate**
before enabling calibration. The same `once`/`watch` worker, readiness protocol,
SQLite queue and Geometry registry are used. No candidate is activated by
iteration or by passing a demonstration convergence cut.

A rotation policy additionally requires `delta_tolerance_rad`, `max_update_rad`
and `rotation_derivative_report`. The example tolerances are demonstration
values (1e-5 rad and 0.05 rad), independent of the existing mm limits. Mixed
X/Y/Rz mode checks both unit families. All selected components must converge.
The gate pins the tested plugin and the fresh-DD4hep finite-difference report(s);
missing labels, changed reports, another plugin or unconstrained steering are
refused. A rebuild requires validation against that build. Mode-specific steering
is in `alignment/pede_<mode>.txt`; historical steering is unchanged.

Use a zero-displacement scope scenario for controller preparation, rather than
Simulation Truth offsets. The selected immutable Geometry supplies sensor centers
and orientations. Updates compose with the current matrix about each current
sensitive center. Labels 3001/3002 are rotational measurement biases in radians;
physical corrections negate them. Controller reports distinguish angular updates
from translations and record pivots and parameter units.

See [rotation validation](../docs/ROTATION_ALIGNMENT_VALIDATION.md) for results,
limitations and the independent Simulation, derivative, fit and correction commands.

## Opt-in Z and XYZ calibration

Use `config/l1_z_demo.json`, `l1_l2_z_demo.json`, or `l1_l2_xyz_demo.json` only
after building and validating the selected plugin. Templates remain disabled.
Set `build_dir`, `calibration.enabled`, and `calibration.z_derivative_report` to
new, explicitly recorded paths. Z evidence must include fresh physical DD4hep
finite differences and actual Mille entries for every selected 4000+layer label,
and must match both `BeamTestReco.so` and `libLocalTelescopeGeometry.so`.
Missing, changed, or incompatible evidence is refused before processing.

The existing sequential Controller then runs the independent modules. Before
each Pede solve, `validation.z_observability` profiles each actual track's four
local parameters and checks the selected global information matrix. The explicit
`z_max_nominal_sigma_mm` gate is a sensitivity bound, not a calibrated error
model. The demonstration bound is 0.5 mm. Zero/narrow-slope designs and rank-
deficient XYZ fits are refused. The new Z templates use a 5 mm maximum update
bound for the declared millimeter-scale injections; the existing 0.005 mm
convergence tolerance and historical policies are unchanged.

4001/4002 are physical Z increments applied with positive sign. The writer's
reference slopes come from current reconstructed associated hits and are frozen
within each Pede solve, then recomputed after Geometry Correction. Cumulative
updates start from the current Geometry. RawHits remain byte-identical; candidates
remain inactive. `applied_mm_by_component` stores absolute centers, while step5
`global_z_offsets_mm` records placement offsets. No successive-fit uncertainty
quadrature is valid for the same RawHits.

The convenience `validation/run_closure.sh` refuses Z modes because it does not
supply the required derivative/information gates. Use this Controller or the
explicit independent stages for controlled validation. Exact validated commands
and limitations are in [Z validation](../docs/Z_ALIGNMENT_VALIDATION.md).

## Individual Global X and Y tilts

Use the disabled `config/l1_rx_demo.json` or `config/l1_ry_demo.json` template
with a **new** state. Set the validated build, explicitly enable calibration,
and point `tilt_derivative_report` to same-plugin/same-Geometry-library evidence
from `validation.validate_tilt_derivatives`. The report must contain successful
fresh physical tests and actual production Mille entries for selected label
5001 or 6001. The Controller pins the report and dependencies; changed or
mismatched evidence is refused. Defaults remain `l2_x` and calibration disabled.

Additional keys are `delta_tolerance_rad`, `max_update_rad`,
`tilt_derivative_report` and `tilt_max_nominal_sigma_rad`. Shipped demonstration
values are 1e-5 rad, 0.1 rad and 0.01 rad maximum formal information error.
They are configurable validation bounds, not calibrated statistical criteria.
The new individual-tilt templates permit six iterations; historical policies
are unchanged. Before each Pede call, actual covariance-whitened Mille rows
profile the four local parameters of every track and must pass the information
gate. Reference slopes and weights are frozen in each solve and recomputed
after Geometry Correction. No MC slopes, injected corrections or Truth Geometry
are needed. Keep `measured_geometry` null for truth-excluded operation.

Run the unchanged worker interface:

```sh
python3 -m calibration.controller once --config result/NEW_RX/controller.json --input-dir input/NEW_RX --state-dir result/NEW_RX_STATE
```

5001 and 6001 are positive physical Global rotation increments in radians,
about the current sensitive center. The current rotation matrix is left-composed;
Euler angles are not added as state. RawHit snapshots, readiness, queue order,
locks, retries, version parent chains and explicit review/activation are unchanged.
A converged candidate remains inactive. All components must meet the applicable
unit-specific convergence cuts, which alone do not establish scientific closure.

Combined `l1_rx_ry`/`l1_l2_rx_ry` configurations are retained only as **disabled
experimental records**. Loading them is intentionally refused after a noiseless
finite-rotation closure failure. Numerical convergence, rank and a passed
infinitesimal derivative test did not resolve that modeling defect. The isolated
Rz diagnostic is not a released mixed-rotation mode. See [the tilt report](../docs/TILT_ALIGNMENT_VALIDATION.md).

After convergence, reconstruct the exact inactive candidate with the same
RawHits in a fresh result directory. The Controller report names the Geometry
version; numerical iteration quality alone does not replace that independent
final-candidate check. `visualization.tilt_alignment --report REPORT --candidate
XML --final-reconstruction RUN/step3 --case SIM_CASE --output NEW_ROOT_DIR`
consumes maintained outputs directly. Its optional archived-study shorthand
does not define a second workflow.

## Coupled SO(3) rotations and six-DOF scopes

The explicit coupled modes use the same queue, sequential worker, fixed RawHits,
version store, review and activation APIs. They do not introduce a second
Controller. Templates remain disabled; ordinary reconstruction without an
explicit alignment mode retains the historical writer path.

`l1_rotations` and `l1_l2_rotations` fit Rx/Ry/Rz together.
`l1_six_dof` and `l1_l2_six_dof` also fit X/Y/Z on the selected sensors.
Global incremental rotations are three components of an SO(3) exponential,
not additive Euler angles. See [conventions](../docs/GEOMETRY_CONVENTIONS.md#coupled-global-rotations-so3-increments)
and [validation status](../docs/SO3_ALIGNMENT_VALIDATION.md).

The existing tilt policy keys are required, including
`tilt_derivative_report`, `tilt_max_nominal_sigma_rad`,
`delta_tolerance_rad` and `max_update_rad`. Coupled six-DOF policies also require
`tilt_max_nominal_sigma_mm`, independently of `max_update_mm`. Shipped values
(0.01 rad, 0.5 mm information limits; 1e-5 rad and 0.005 mm convergence limits)
are demonstration sensitivity/stop thresholds. They are not calibrated error
coverage criteria. Six-DOF examples allow at most 1 mm per-component updates;
the correction additionally bounds each physical rotation-vector norm to 0.1 rad.

The sealed evidence includes actual-Mille/fresh-DD4hep derivatives and all
mandatory noiseless cases, with the relevant scope's rotation or six-DOF
fixture. Plugin, Geometry library, proofs, canonical steering and model sources
are pinned. A stale or absent proof is rejected before processing inputs.
Every solve separately checks profiled rank and nominal sensitivity using actual
Mille rows. End-to-end convergence remains distinct from independent Geometry
validation; approval and activation remain explicit. The convenience
`validation/run_closure.sh` refuses these scopes to avoid bypassing their gates.

## L3 and three-layer implementation scopes

`l3_six_dof_demo.json` and `l1_l2_l3_six_dof_demo.json` in `config/` are disabled by default. The explicit scope registry in `correction/scope.py` selects layers (3) or (1,2,3), respectively. All six components per selected layer participate in the existing mm/rad convergence checks, same-RawHit iteration and immutable parent chain. L0/L4 remain fixed; activation still requires explicit independent validation and review. Gates must include physical/actual-binary evidence for every selected label and source-matched noiseless cases for the selected scope. Historical gates cannot be relabeled for changed binaries. See the [manual guide](../docs/L3_SIX_DOF_MANUAL.md) for independent stages, proof generation, delivery, once/watch and output inspection. These scopes have implementation checks, not statistical certification.
