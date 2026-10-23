# Calibration Controller Implementation and Validation

Validated on 2026-10-22 in the existing EIC container `sweet_mahavira`, mounted at `/work`. No commit or push was performed. No Geant4 events were generated.

## Implemented scope

- `calibration/controller.py`: shared once/watch worker and explicit queue, Geometry, manual calibration, retry, review, activation and guard-recovery commands.
- `input_monitor.py`: final readiness manifests, confined relative paths, checksums and the existing typed RawHit/EventHeader contract.
- `queue_manager.py`: persistent SQLite queue/event journal, deterministic sequence or explicit identity fallback, gap policies, bounded explicit retries, atomic directory guard plus advisory lock.
- `geometry_manager.py`: content-addressed immutable XML snapshots, fallback selection, candidate history, explicit independent-review and activation gates.
- `iteration.py`, `runner.py`, `convergence.py`, `settings.py`: fixed-input stage orchestration, retained subprocess logs and completion records, provisional quality cuts and pinned configuration/dependencies.
- `input/README.md`, `.gitignore`: input-only delivery directory; payloads, metadata, manifests and temporary files excluded from Git.
- `correction/correct_geometry.py`: opt-in `--base-geometry` composes the residual L2 X update with the Geometry used for Reconstruction. The existing nominal-based default is preserved.

The controller creates a fresh input snapshot and output directory per attempt, records a compatibility fingerprint without merging datasets, and verifies completed attempt hashes on restart. It retains failures and partial results. Each dataset's initial reconstruction Geometry stays pinned; iteration-specific candidates are recorded separately. Candidate convergence never activates Geometry automatically.

Calibration is an **L2 Global X prototype**. It requires explicitly supplied measured Geometry matching RawHit metadata and checks that only L2 differs from nominal. Demonstration thresholds are not scientifically established criteria. Human review is represented by an explicit operator statement and checksummed held-out report; the software validates their identities, not their scientific adequacy. Automatic activation, conditions validity intervals, cross-file accumulation, E0 transport, concurrent physics/calibration and distributed scheduling remain future work.

## Executed validation

All artifacts are local and ignored under `result/calibration_controller_20261022_01/`. The prior implementation and working diff were backed up there before editing. Existing local datasets are required and are not stored in Git.

The saved source was `result/rawhit_boundary_20261021_01/l2_final/step2_digitization/rawhits.edm4eic.root` with its RawHit contract and measured Geometry. PODIO copied disjoint event ranges `[0,70)`, `[70,80)`, `[80,100)` into A, B and C while preserving EventHeader identifiers and simulation provenance. No fabricated DAQ data were used.

| Check | Executed result |
|---|---|
| Six standard-library unit tests | Passed: readiness, checksums/mutation, duplicates, ordering/gap policies, locking, interrupted-state recovery and quality gates |
| Watch with A then B arriving during A calibration | Passed twice, including the final atomic-guard implementation (`v3_watch_state`) |
| Fixed input during A iterations | Same A checksum in both iterations; 69 tracks; delta +0.19856 mm then −0.0000018041 mm |
| Sequential processing | B discovered before A finished; B processing started only after A finished |
| Insufficient statistics | B reconstructed 10 tracks and skipped calibration under the provisional 20-track threshold |
| No readiness marker | An incomplete payload never entered the queue |
| Actual invalid metadata | Valid delivery checksums with unsupported RawHit charge units were rejected before Reconstruction |
| Completed restart | Once mode skipped completed inputs; no added attempts; output checksums verified |
| Explicit lifecycle | Unreviewed activation refused; explicit provisional held-out review then activation succeeded; subsequent C selected that version; A/B selections and original XML remained unchanged |
| Held-out C | 20 disjoint events; chi2/stored-NDF 1.32252; used only as an explicitly provisional lifecycle smoke test |
| Calibration failure/retry | Real reconstruction and pede executed; a strict 0.1 mm update bound rejected the +0.19856 mm update; active fallback unchanged; two attempts retained; third retry refused |
| Manual calibration | Completed a separately requested A attempt using its original RawHit and pinned Geometry |
| Concurrent controller and graceful stop | Final `v3_restart_state`: second controller refused; current stage finished on SIGTERM; interrupted attempt retained; explicit retry completed; next restart skipped it |
| Abrupt-owner recovery | Unit-tested conservative recovery with a synthetic dead owner and refusal for a live owner; a real SIGKILL/reboot recovery was **not** claimed as tested |
| Existing preservation/safety scripts | Passed |
| Additional protection inventory | All 4,763 pre-existing protected data/dependency/user-file checksums unchanged |
| Python compilation and whitespace | Passed with a writable temporary bytecode cache; `git diff --check` passed |

An initial Docker concurrency test exposed that advisory `flock` alone did not prevent two processes from entering the queue on this bind mount. That test failed and was stopped gracefully. The implementation now also uses atomic directory creation, and the corrected test passed. Two intermediate test-harness runs failed on startup-database timing and reused output filenames; their artifacts were retained and fresh-directory harnesses passed. These failures were not reported as successful tests.

After an abrupt death, the guard remains. Explicit `recover-lock --reason ...` checks the recorded host, owner PID and stage process groups and refuses ambiguous recovery. Different hosts/containers, incomplete owner records, surviving processes and orphaned registry directories require operator inspection. This is a conservative local prototype, not a distributed lease service.

## Exact commands and results

Host checks:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache python3 -m unittest validation.test_calibration_controller -v
PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache python3 -m compileall -q calibration correction validation/test_calibration_controller.py
PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache python3 validation/verify_preservation.py
PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache python3 validation/check_safety.py
git diff --check
```

The preservation script reported 221 baseline records and 2,046 relocated files unchanged. The additional task inventory reported 4,763 unchanged checksums. The initial host compilation attempt could not write the host's default bytecode cache; setting `PYTHONPYCACHEPREFIX` resolved that environment issue.

Container integration harnesses, all writing new test paths:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c 'import sys,runpy;sys.path.insert(0,"/work");runpy.run_path("result/calibration_controller_20261022_01/prepare_deliveries.py",run_name="__main__")'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c 'import sys,runpy;sys.path.insert(0,"/work");runpy.run_path("result/calibration_controller_20261022_01/watch_test_v3.py",run_name="__main__")'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c 'import sys,runpy;sys.path.insert(0,"/work");runpy.run_path("result/calibration_controller_20261022_01/lifecycle_test.py",run_name="__main__")'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c 'import sys,runpy;sys.path.insert(0,"/work");runpy.run_path("result/calibration_controller_20261022_01/restart_test_v3.py",run_name="__main__")'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c 'import sys,runpy;sys.path.insert(0,"/work");runpy.run_path("result/calibration_controller_20261022_01/contract_test.py",run_name="__main__")'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m calibration.controller calibrate --config result/calibration_controller_20261022_01/test_config.json --input-dir result/calibration_controller_20261022_01/watch_input --state-dir result/calibration_controller_20261022_01/watch_state --input-id A
```

These local harnesses are validation artifacts, not maintained workflow entry points; they use exclusive output creation and must not be rerun over existing test directories. Public commands and the delivery schema are documented in [the controller guide](../calibration/README.md). `lifecycle_commands.log`, controller queue databases, stage `command.json`/`stdout.log`/`exit.json` and completion hashes retain exact subprocess evidence.

Historical full closure regression:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash validation/run_closure.sh --result-dir result/calibration_controller_20261022_01/regression --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root --build-dir build/rawhit_boundary_20261021_01 --reference validation/reference_metrics.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m validation.check_root_outputs --result-dir result/calibration_controller_20261022_01/regression
```

Both exited zero. Before/after: **99/99 tracks**, **+198.75 μm** L2 correction, historical pooled L2 Rec − Sim **−199.571 → −0.821 μm**, chi2/stored-NDF **45.59223485 → 1.98103977**. Reference comparison passed. ROOT checks confirmed three canvases, at least 20 residual histograms and closure graphs.

The existing validated `build/rawhit_boundary_20261021_01/BeamTestReco.so` was used (SHA256 `caa4b88fa94c4b98087f337eb610d535801510a0c6deb6fe917da3e8ea0137b7`). No C++ source changed during this controller task; no additional C++ build was executed. The earlier RawHit refactoring and electron-hypothesis changes were preserved. Detector Geometry, hit uncertainties, ACTS fitting, Mille derivatives and pede steering were not changed.
