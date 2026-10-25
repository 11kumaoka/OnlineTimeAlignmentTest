# Maintained workflow and conservative source cleanup

Starting commit: `a45164c3d9efbc24bdc9833954407e0cb7cf9fd4`, branch
`feature/upstream-acts-geometry`. The working tree was initially clean.
This cleanup changes no numerical algorithm, Geometry definition, measurement
covariance, particle hypothesis, material setting, Pede steering or policy gate.

## Primary execution path

Start with [the user guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md) and
[the native code map](TELESCOPE_ALIGNMENT_CODE_MAP.md). The public entry is
`python3 -B -m calibration.workflow run`. Its stages are independently callable.

| Responsibility | Maintained modules | Upstream or local boundary |
| --- | --- | --- |
| Configuration, provenance, stage orchestration and final ROOT report | `calibration/workflow.py`; `calibration/config/native_workflow_*.json` | Thin local public interface; no numerical fitter or solver |
| Geometry preparation and identity checks | `validation/telescope_geometry/`; actual Geometry audits in `calibration/native_operations.py` | Real DD4hep construction; installed EICrecon ActsGeometryProvider and ACTS conversion/SurfaceMap |
| Simulation | `simulation/native.py` | Installed npsim/DDSim and Geant4, unchanged physical settings |
| Digitization and immutable input | `digitization/native.py`; `TelescopeDigitization.cc` | Installed official SiliconTrackerDigi factories; local collection registration and Raw-only five-plane projection |
| Hit Reconstruction, measurements and Track Fitting | `localDetEICrecon/experimental/telescope/` | Installed TrackerHitReconstruction and ACTS numerical CKF; pinned official-source wrappers and explicit telescope seed/association adapters |
| Mille Binary and Pede | native `alignment/NativeMilleModel.*`, `TelescopeMille.cc`; `calibration/native_operations.py`; `alignment/pede.py` | Native ACTS derivatives, official Mille library and official `external/install/bin/pede` |
| Geometry Correction | shared `validation/telescope_closure/{closure,rotation,multi_sensor}.py`; `geometry/transforms.py` | Existing selected-sensor physical correction and SO(3) gates |
| Controller and safety | `calibration/native_{controller,operations,policy}.py`; `convergence.py`, `runner.py`, `queue_manager.py` | Existing bounded Controller, locks, process supervision, immutable channels and strict/diagnostic separation |
| Reporting and ROOT inspection | `calibration/workflow.py::root_report`; `visualization/browse.C` | ROOT histograms, graphs and canvas; no separate visualization backend |

Modules under `validation/telescope_closure/` are also runtime dependencies.
Their directory name is not evidence that they can be deleted. In particular,
`rotation.pose_checks` imports `closure.MODULE_TO_GLOBAL`; the native solver and
Controller use `validation/telescope_alignment/check.py::records/profile`.

## Files removed

Both were tracked source/configuration files, backed up before deletion and
recoverable from the starting commit. No symlink target or generated file was
removed.

| Removed path | Evidence and replacement | Effect |
| --- | --- | --- |
| `reconstruction/reconstruct_corrected.sh` | Only `cd` plus `exec python3 -m reconstruction.reconstruct --after`; its sole executable caller was `validation/run_closure.sh` | Caller now uses existing `reconstruct.sh --after`; recorded execution proves identical Python arguments and working directory, including arguments containing spaces |
| `geometry/scenarios/my_first_test.json` | Parsed configuration exactly equals `geometry/scenarios/L1_x150um_L2_x200um.json`, already used by the legacy Controller example | Removes an unused alternate spelling/format of the same +0.150/+0.200 mm L1/L2 Global X scenario; no physical parameter changes |

Current operation instructions use the canonical command. Dated reports retain
their actual executed paths and data provenance, with explicit replay notes.
Archive migration/checksum manifests are unchanged: similarly named paths inside
historical source workspaces identify real retained copies, not deleted data.
For byte-exact recovery, `git show a45164c:PATH` reads either original source.

## Intentionally retained

| Component | Why it stays |
| --- | --- |
| All 53 C++ sources/headers | Every file has a build, include, runtime or independent-test dependency; no exact duplicate implementation group was found |
| Legacy BeamTestReco, manual-surface fitter, digitization and +Z Geometry | Unique retained +Z workflows, 99-track and z=-500 mm references; not interchangeable with the native +X Geometry/input contract |
| BeamTestMilleWriter and TiltMeasurementModel | Independent mathematical reference used by native equivalence tests; legacy signed six-DOF capabilities |
| `calibration/controller.py`, `settings.py`, `iteration.py`, `input_monitor.py`, `geometry_manager.py` | Unique sequential queue/ordering/retry/review lifecycle and legacy alignment scopes; the bounded native one-file Controller does not replace them |
| `queue_manager.py`, `runner.py`, `convergence.py` | Direct native Controller dependencies, not obsolete legacy helpers |
| Synthetic channels, one-track executable, derivative and Mille fixtures | Independent Geometry/association, analytical/finite-difference and native-versus-legacy regression coverage |
| `OfficialGeometryProbe`, barrel Geometry probe and `legacy_endcap_experiment.py` | Different Geometry contracts; reproduce the historical converter failure and current successful native conversion without altering installed ACTS |
| Pinned official-source headers, provenance, licenses and patches | Required installed-interface adapters and reproducible source comparison; not disposable duplicate upstream code |
| Legacy simulation, steering, scenarios and ROOT diagnostics | Distinct +Z scopes, dynamic mode/steering lookup, historical bias/coverage/weak-mode diagnostics and failed-mode reproducibility |

No `seven_layer/`, `prototype/`, standalone ACTS tree or Blueprint provider
implementation exists in the starting tracked tree; none was reintroduced or
counted as a new deletion. No Python implementation was removed merely because
it lacked a direct public import. No source directories were moved.

The primary README and package READMEs distinguish current native commands,
retained +Z capabilities and historical evidence. The older architecture guide
is explicitly labeled as the legacy endcap description; its converter failure
is not a claim that the current native Geometry fails.

## Generated data: proposal only

No generated file was deleted. Measurements below describe the pre-cleanup
local workspace, not files distributed through Git. Allocated disk usage from
`du -sk` differs from logical file sizes because of allocation and metadata.

| Root | Allocated usage (KiB) | Treatment |
| --- | ---: | --- |
| `result/` | 42,485,896 | Scientific runs, checkpoints, failed attempts, frozen sources and detailed audits: retain |
| `results/` | 181,324 | Historical reference datasets and relocation provenance: retain |
| `build/` | 1,994,964 | Reproducible in principle, but old binaries are pinned by evidence/checkpoints: retain pending specific review |
| `external/` | 23,256 | Dependency sources/builds/installations: retain; `external/install/` remains required |

The inventory covers 139,065 files in 492 groups, totaling 44,525,568,785 logical
bytes. Categories are separated in the local generated-data inventory:

- **Safe reproducible cache proposal:** 13 active Python bytecode directories,
  912,520 logical bytes (about 0.87 MiB). No deletion performed.
- **Historical cache requiring review:** two old bytecode directories, 40,874
  bytes, potentially containing code whose original source is no longer present.
- **Byte-identical scientific outputs:** 160 protected ROOT/Mille duplicate
  groups. Keep their paths and immutable provenance; duplicate bytes alone do
  not justify deleting an independent run or checkpoint artifact.
- **Scientific reference data:** protected baselines, original 99-track closure,
  z=-500 mm results and newer native examples. Keep.
- **Historical diagnostics:** failed runs, source freezes and restart evidence.
  Keep. Old build directories require a file-specific dependency/recovery review;
  no blanket disk-space recovery is claimed.

Immediately proposed cache recovery is therefore only 912,520 logical bytes;
actual recovered disk allocation may differ. Protected or ambiguous generated
artifacts require explicit approval. The inventory does not grant deletion
permission or weaken any preservation manifest.

The exact active-cache proposal is below. All 71 cache filenames have a
corresponding retained Python source path. These directories are ignored,
and remain untouched pending approval.

| Proposed cache directory | Logical bytes |
| --- | ---: |
| `__pycache__/` | 6,887 |
| `alignment/__pycache__/` | 12,287 |
| `calibration/__pycache__/` | 193,673 |
| `correction/__pycache__/` | 43,524 |
| `digitization/__pycache__/` | 16,119 |
| `geometry/__pycache__/` | 51,758 |
| `reconstruction/__pycache__/` | 11,572 |
| `simulation/__pycache__/` | 4,739 |
| `validation/__pycache__/` | 263,441 |
| `validation/telescope_alignment/__pycache__/` | 14,719 |
| `validation/telescope_closure/__pycache__/` | 199,123 |
| `validation/telescope_geometry/__pycache__/` | 6,235 |
| `visualization/__pycache__/` | 88,443 |

The two historical bytecode directories remain **REVIEW / KEEP**:

- `result/architecture_20261021_01/previous_package_bytecode/stages/__pycache__/`: 39,280 bytes.
- `result/rawhit_boundary_20261021_01/__pycache__/`: 1,594 bytes.

No generated disk space was reclaimed during this cleanup.

## Validation and local evidence

Executed checks:

- Fresh native configure/build in `build/native_telescope`: both exit 0; all
  targets, including isolated navigation/serialization tests, built successfully.
- All 53 C++ files equal the starting commit. Eight compared plugins/numerical
  artifacts are byte-identical to the validated previous native build.
  Fourteen `ldd`/`readelf` checks pass; actual Mille2 resolves to
  `/work/external/install/lib/libMille2.so`. Nine installed ACTS libraries remain
  unchanged. No installed software was modified.
- Full Python unit discovery: **232 tests, zero skips, all passed**. Public
  CLI/help, changed-shell syntax/help and canonical reconstruction help passed.
- Canonical preservation check passed without editing its manifests: 221 baseline
  and 2,046 relocated records plus the validated electron-hypothesis source.
  All 18 canonical safety refusals passed; only a fresh safety directory was made.
- A fresh 64-event Geant4 run through official Digitization, native ACTS/Mille,
  official Pede, physical correction, fresh reconstruction and ROOT reporting
  completed with exit 0 at `result/native_smoke/`.

| Fresh smoke result | Before correction | After correction |
| --- | ---: | ---: |
| Accepted tracks | 63 | 63 |
| Pede L1 Global Y update (mm) | +0.078865 | +0.00000022638 |
| ACTS chi2/stored-NDF | 5.643925909012083 | 1.2900174523156787 |
| Pede chi2/statistical NDF | 2.1557011378277173 | 2.155701141848409 |
| Residual u RMS (mm) | 0.031532258938929913 | 0.011114111935752707 |
| Residual v RMS (mm) | 0.011596382438327777 | 0.011596381948422024 |

These reproduce the prior smoke metrics exactly. This is a same-seed software
regression, not a new independent statistical sample. Both Pede fits retain
end status 1, the recognized high-chi2 warning, with zero rejected local fits.
No error scaling is applied. Engineering and integrity pass, but physics quality
remains unvalidated and the candidate remains unapproved/unactivated. ROOT
serialization is tested in batch; no interactive GUI operation is claimed.

Controller code and numerical behavior are unchanged. The source identity now
contains 277 files instead of 279. An actual read-only call against an older
checkpoint correctly raises `Implementation source set or contents changed since
run creation`; all 212 old Controller files remain exact. No historical resume,
checkpoint rewrite or source-guard exception was attempted. Start new runs under
the new source identity, or restore the corresponding archived source environment
when investigating old checkpoints. The previous real interruption/resume evidence
is preserved; a new interruption campaign was not needed for this caller-only
change.

The fresh run's independent audit passed: both official Mille binaries contain
63 records/630 scalar measurements, six Geometry XMLs were actually reloaded,
all 39 ROOT objects were read, and all 285 public-run files remain unchanged.
`validate_run_inputs()` passes against the 277-source identity and fresh build;
input/final seals and the two-checkpoint chain pass, converged after one correction.

Final preservation independently rehashed **139,076 existing files/links**
(139,023 regular files, 53 symlinks; 44,525,701,542 logical bytes). Content,
kind, size, mtime and link targets are unchanged. The original 49,783-file
constraint, 94 exact tree sets, nine original link identities and nominal
Geometry remain intact. Exactly 474 new files appeared only in the explicitly
allowed fresh build (176), smoke run (285) and safety output (13); the new audit
root was excluded consistently from its own baseline. No generated file was
removed or overwritten and no preservation manifest was weakened.

No 28-case historical numerical campaign was repeated because shared numerical
implementations are unchanged. The old 99-track and native 32-track reference
results were preserved byte-for-byte; they were not rerun or relabeled as new
closure executions in this cleanup.

Recorded public commands (use unused names for a later reproduction):

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_telescope \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_telescope -j2
bash environment/run.sh env PYTHONDONTWRITEBYTECODE=1 python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_smoke.json \
  --output-dir result/native_smoke --build build/native_telescope \
  --validation-mode diagnostic

bash environment/run.sh env PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s validation -p 'test_*.py' -v
bash environment/run.sh env PYTHONDONTWRITEBYTECODE=1 python3 -B validation/verify_preservation.py
bash environment/run.sh env PYTHONDONTWRITEBYTECODE=1 python3 -B validation/check_safety.py
```

The optional existing-container selection uses the same pinned image as the
wrapper default. Bytecode writing was disabled in validation processes to
preserve existing caches. Effective physics settings and CLI arguments are
unchanged. Each stage records its actual command, working directory and exit.

The local audit root is `result/repository_cleanup_20261025_01_audit/`:
`source_baseline/` backs up all 360 original tracked files and Git identities;
`alias_equivalence/` records the exact delegation/configuration checks;
`cxx_source_audit/` contains the 53-file dependency inventory; and
`generated_cleanup_proposal/` contains the detailed CSV/cache/disk inventory.
These are ignored local research evidence, not inputs required by a fresh clone.

Additional receipts under the same audit root: `python_dependency_audit_v2/`,
`execution_source_freeze/`, `focused_checks/`, `native_build/`,
`native_smoke_command/`, `old_checkpoint_source_guard/`, `protected_before/`
and `all_generated_before_v2/`. The earlier incomplete generated enumeration
was retained; the successful physical-walk baseline explicitly includes nested
historical Git repositories rather than silently omitting their contents.

Final acceptance receipts: `public_smoke_independent/`,
`fresh_checkpoint_identity/` and `all_generated_after/`. The full source/config
inventory is in `python_dependency_audit_v2/inventory.json`; the generated-data
proposal includes `generated_groups.csv`, `cache_inventory.json` and `report.json`.
The current tree is suitable for one local source-cleanup commit; no push,
merge, automatic approval or Geometry activation is part of this task.
