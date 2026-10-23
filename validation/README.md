# Validation and Local Reference Data

The repository tracks validation code, expected metrics, checksums, and migration
metadata. It does not distribute ROOT datasets, Mille Binary files, analysis logs,
external dependencies, build outputs, or backups.

## Historical 99-track regression

The minimum external input is:

`results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root`

SHA-256:
`947fee1308b8aa27516c12711c9cdb5e4b4160da2371b7094491418e276ee7a0`

Request this byte-identical file from the project maintainer and place it at the
path above. The original source position was z=0 mm. With dependencies installed
and the Plugin built, run from the repository root:

```bash
bash environment/run.sh bash validation/run_regression.sh result/regression_001
bash environment/run.sh python3 validation/check_root_outputs.py --result-dir result/regression_001
```

Expected results are 99 accepted tracks before/after, L2 Geometry Correction
+198.75 μm, L2 Rec−Sim −199.571→−0.821 μm, and Σχ²/Σstored ACTS nDoF
45.592→1.981. Tolerances are in `reference_metrics.json`.

## Fresh electron Closure

A fresh checkout can generate new events without the historical dataset:

```bash
bash environment/run.sh bash validation/run_closure.sh \
  --result-dir result/electron_001
```

The current electron case uses 1 GeV electrons at mean z=−500 mm. The validated
100-event sample yielded 98 tracks before/after and +201.13 μm correction;
this is a distinct sample, not the 99-track regression reference.
The original local result is `results/vertex_zminus500_20261019_01/closure100/`.
The final cleanup verification results are under
`results/final_simplification_20261021_01/{regression,fresh_electron_100}/`.
These result directories are intentionally excluded from Git.

## Full local preservation audit

`verify_preservation.py` requires the complete retained local dataset, not just
the one regression input. Restore the 221 baseline entries, 2,046 relocated data
files, and seven input links using `preserved_files.json`,
`relocated_data_sha256.json`, and `path_migration.json`. Historical records can
refer to former locations; follow the migration map without editing data content.
The persistent external archive is documented in `docs/FINAL_SIMPLIFICATION.md`.
It is a maintainer-local recovery source, not a path required by the workflow.
A clean Git clone without the local data cannot pass this complete audit.

The checker also verifies `validated_sources.json`, which pins the exact validated
ACTS fitter source including the electron hypothesis. This works with unstaged,
staged, and committed source. `electron_hypothesis_before.patch` retains the
original change as provenance; validation does not require an uncommitted diff.
Update the source checksum only after intentionally changing and validating that
source. Do not remove checksum entries to bypass missing or changed data.

```bash
python3 validation/verify_preservation.py
python3 validation/check_safety.py
```

The safety checker creates a new temporary result subdirectory and exercises CLI
refusal paths. It does not execute reconstruction or overwrite reference data.


## Current task architecture

New runs use `result/<name>/step1` through `step7`. Numerical extraction is in
`validation/metrics.py`; `validate.py` compares provenance and runs the ROOT
renderer in `visualization/`. Historical `results/` remains untouched. See the
[Workflow Guide](../docs/WORKFLOW.md) for seven independent commands and the
[architecture report](../docs/TASK_ARCHITECTURE.md) for migration validation.

## RawHit split validation

The historical Closure helper now inserts `digitization/digitize.sh` between
steps2/3 and reconstructs the same saved RawHits at steps3/6. Simulation Hit
Residuals use the separate step2 truth file after event-identity checks.
`python3 -m validation.compare_raw_paths --help` documents the detailed
combined/split comparator, including named PODIO relation targets, all shared
fields, exact Mille Binary bytes and Pede parameters. See
[the RawHit validation report](../docs/RAWHIT_BOUNDARY.md).

Controller control-plane tests: `python3 -m unittest validation.test_calibration_controller -v`. These tests isolate orchestration invariants; real saved-RawHit execution and limits are recorded in [the controller validation report](../docs/CALIBRATION_CONTROLLER_VALIDATION.md).

Simultaneous L1/L2 X composition and scope tests: `python3 -m unittest validation.test_geometry_correction -v`. See [two-layer iterative validation](../docs/L1_L2_ITERATIVE_VALIDATION.md) for executed saved-data closure and the preserved default L2 regression.

Geometry foundation and metadata tests:

```sh
python3 -m unittest validation.test_transforms validation.test_raw_metadata validation.test_geometry_correction validation.test_calibration_controller
```

Run fresh-DD4hep and Mille finite-difference probes inside the EIC container; see [XY validation](../docs/XY_FOUNDATION_VALIDATION.md) for executed commands and results. Global Z translation and individual L1 tilts use their explicit gated modes, documented below; opt-in L1/L2 Rz modes are documented in [rotation validation](../docs/ROTATION_ALIGNMENT_VALIDATION.md). [Geometry conventions](../docs/GEOMETRY_CONVENTIONS.md) distinguish sensor axes, ACTS planes, reference/survey Geometry and optional simulation truth.

## Global Z checks

`python3 -m unittest validation.test_z_alignment` tests Global Z placement,
physical correction sign/composition, unsupported scopes, evidence freshness and
weak-information refusal. `python3 -m validation.validate_z_derivatives --help`
checks actual Mille reference slopes and fresh-process DD4hep finite differences.
`python3 -m validation.z_observability --help` profiles the actual weighted
per-track local design before assessing selected global rank, weak modes and
correlations. It is a diagnostic/gate, not a replacement fit or uncertainty
rescaling. `python3 -m visualization.z_alignment --help` produces ROOT-only
Geometry, matched X/Y/Z Hit Residuals, profiled track residuals and closure plots.
Truth is read only by post-fit validation. See [Z validation](../docs/Z_ALIGNMENT_VALIDATION.md).

## Tilt checkpoint

`test_tilt_alignment.py` covers matrix composition/serialization, selected scope
and refusal of scientifically unsupported combined modes.
`validate_tilt_derivatives.py` uses the production C++ writer and fresh DD4hep
contexts; `tilt_observability.py` profiles actual Mille local matrices;
`tilt_hit_audit.py` records off-plane SimHits without filtering data.
`geometry_probe.py --check-track-points` additionally checks actual intersections
and Global XYZ diagnostic covariances. `gdml_geometry_probe.py
--check-overlaps-mm .0001` checks independently exported physical matrices and
overlaps/extrusions. `visualization.tilt_alignment` writes ROOT objects for
supported results or explicitly labeled archived combined experiments.

Read [the tilt checkpoint report](../docs/TILT_ALIGNMENT_VALIDATION.md) for exact
commands, final build, preserved failure evidence, numerical regressions and the
historical scientific stop at fixed-Global two-axis rotations. The successor explicit SO(3) scopes and their evidence are documented in [the coupled-rotation checkpoint](../docs/SO3_ALIGNMENT_VALIDATION.md).

## L3 implementation checkpoint

`validate_tilt_derivatives --layer 3 --coupled` extends the same physical-DD4hep/production-Mille check to all six L3 columns. Optional `--representative` restricts the diagnostic to one mixed orientation and one finite-difference step, retaining the full suite as default. `test_so3_alignment` checks explicit selected labels, fixed references and repeated current-Geometry composition. `so3_closure` additionally includes L3-only and three-layer six-DOF noiseless mathematical fixtures; these are not Geant4/statistical certification. Follow the [manual guide](../docs/L3_SIX_DOF_MANUAL.md) for proof generation and actual-row rank checks.

## Optional official Geometry audit

`python3 -m validation.official_geometry --help` describes the isolated local, official-provider and official-element modes. The latter is a component comparison, not a TrackingGeometry suitable for reconstruction. The official provider fails explicitly for the current one-sided telescope. See [the pinned-source audit and independent commands](../docs/OFFICIAL_ACTS_GEOMETRY_PHASE1.md). The production fitter and Controller defaults are unchanged.

The optional `blueprint` diagnostic now closes a Gen3 TrackingGeometry and runs
four independent installed-Navigator rays for each selected XML. See
[the integration checks and tested manual workflow](../docs/ACTS_GEOMETRY_INTEGRATION.md)
for the separate surface, complete-Geometry, navigation, reconstruction and
fixed-RawHit alignment gates. `validation.compare_geometry_providers` compares
all PODIO values and Mille records with semantic sensor-ID mapping and fixed
numerical tolerances; it does not weaken historical exact local-path regression.
Fresh derivative evidence must match the affected plugin and source files.
