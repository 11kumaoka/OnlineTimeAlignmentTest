> Retained +Z BeamTestReco validation. Start native +X studies with
> [the telescope guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md).
> Fresh replays use `geometry/scenarios/L1_x150um_L2_x200um.json`, whose values
> equal the historical `my_first_test.json` used below. The original bytes remain
> recoverable from commit `a45164c3d9efbc24bdc9833954407e0cb7cf9fd4` and the
> cleanup source backup; historical result files and quoted commands are unchanged.

# Simultaneous SiMAPS L1/L2 Global X Alignment

## Supported scope

The explicit `l1_l2_x` correction mode extends the Python controller to simultaneous SiMAPS L1 and L2 Global X. `l2_x` remains the default. No tracking, digitization, uncertainty, material, nominal Geometry, or solver steering changes were made. Existing pede labels 1001/1002 describe measurement biases; their negatives are added to the corresponding current Global X positions. Existing L1–L3 X/Y parameters are still fitted, but only the selected L1/L2 X components are applied.

`correction/scope.py` rejects Geometry differences outside the selected layers' ring-radius placement attributes. The controller requires the measured Geometry checksum to match the RawHit contract, uses the same copied RawHit bytes in every iteration, and requires **both** residual updates to satisfy the configurable demonstration tolerance. Candidates remain inactive until independent validation and explicit approval/activation. Validation on the calibration dataset below is not independent scientific approval.

## Configuration and public commands

Copy `calibration/config/l1_l2_x_demo.json` to a new local configuration. Set `build_dir`, `calibration.enabled: true`, and `calibration.measured_geometry` to the exact measured Geometry associated with the incoming RawHits. The template's canonical scenario is `geometry/scenarios/L1_x150um_L2_x200um.json`; the shipped template is disabled pending local configuration. Publish the usual readiness manifests in `input/`, then run:

```sh
bash environment/run.sh python3 -m calibration.controller once --config result/CONFIG.json --input-dir input --state-dir result/NEW_STATE
bash environment/run.sh python3 -m calibration.controller watch --config result/CONFIG.json --input-dir input --state-dir result/NEW_STATE
bash environment/run.sh python3 -m calibration.controller queue --state-dir result/NEW_STATE
```

Use one operating mode at a time. All existing locking, queue ordering, readiness, retries and review gates remain in use. A changed correction mode requires a new state/configuration fingerprint. To correct a single existing fit:

```sh
bash environment/run.sh python3 -m correction.correct_geometry --result-dir result/RUN --mode l1_l2_x --base-geometry result/CURRENT.xml
```

The Geometry must be from the fit producing that run's Mille Binary. Omitting `--base-geometry` starts from nominal. Existing stage directories are never overwritten.

Full saved-simulation closure supports an explicit mode:

```sh
bash environment/run.sh bash validation/run_closure.sh --result-dir result/NEW_CLOSURE --geometry-config geometry/scenarios/L1_x150um_L2_x200um.json --correction-mode l1_l2_x --sim-input result/my_geometry_001/step2/events.edm4hep.root --build-dir build/rawhit_boundary_20261021_01
```

The simulation and build paths above are local prerequisites, not Git payloads. The historical L2 reference must not be supplied for a different two-layer dataset.

## Executed results (2026-10-22)

Artifacts: `result/l1_l2_iterative_20261022_01/`. Reused saved simulation from `result/my_geometry_001/step2/events.edm4hep.root` and saved RawHits from `result/rawhit_boundary_20261021_01/digitized/step2_digitization/`. Their source simulation SHA256 is `f5fbe3a76acc3abc4515cc0ed7d6cb748f858b155988224965047075514d677c`; RawHit SHA256 is `cf7b036f1b44baf475bc0c97c79238f2fcc21bfda2726b7dec44d889e1cfb5ec`. No new Geant4 events were generated.

| Iteration | Tracks | L1 update (mm) | L2 update (mm) | chi2 / stored ACTS ndf | Demonstration convergence |
|---|---:|---:|---:|---:|---|
| 1, nominal base | 98 | +0.15058 | +0.20113 | 37.060296 | No |
| 2, composed base | 98 | +0.0000023112 | −0.00000011202 | 1.239162 | Yes, both components |

Exact final candidate XML positions: **L1 +0.15058231 mm, L2 +0.20112989 mm**, including the existing XML eight-decimal-place precision. A separate Reconstruction of that candidate produced 98 tracks and chi2/stored-NDF **1.23916477**. All seven actual DD4hep GDML positions matched the expected XML placements to 1e-8 mm; unselected positions remained unchanged. The active Geometry remained the initial fallback.

Full one-update Closure results:

| Quantity | Before | After |
|---|---:|---:|
| Tracks | 98 | 98 |
| L1 pooled Rec − Sim (μm) | −149.910354 | +0.669832 |
| L2 pooled Rec − Sim (μm) | −198.922108 | +2.207910 |
| chi2 / stored ACTS ndf | 37.060296 | 1.239162 |

One-update corrections were +150.58 μm / +201.13 μm. The small remaining biases are measured outcomes; no errors or thresholds were retuned to force closure. Exact final-candidate residuals were +0.671970 μm / +2.207865 μm. Stored ndf retains the existing convention.

The historical L2-only regression passed separately: **99/99 tracks**, **+198.75 μm**, residual **−199.571376 → −0.821365 μm**, chi2/stored-NDF **45.592235 → 1.981040**, `reference_passed: true`.

## Executed commands and checks

The following commands ran in the existing container `sweet_mahavira` through `environment/run.sh` and exited zero:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m calibration.controller once --config result/l1_l2_iterative_20261022_01/config.json --input-dir result/l1_l2_iterative_20261022_01/input --state-dir result/l1_l2_iterative_20261022_01/state
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash validation/run_closure.sh --result-dir result/l1_l2_iterative_20261022_01/closure --geometry-config geometry/scenarios/my_first_test.json --correction-mode l1_l2_x --sim-input result/my_geometry_001/step2/events.edm4hep.root --build-dir build/rawhit_boundary_20261021_01
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash validation/run_closure.sh --result-dir result/l1_l2_iterative_20261022_01/l2_regression --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root --build-dir build/rawhit_boundary_20261021_01 --reference validation/reference_metrics.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m validation.check_root_outputs --result-dir result/l1_l2_iterative_20261022_01/l2_regression
```

The executed `my_first_test.json` scenario contains the same +0.150/+0.200 mm shifts as the new canonical scenario; that user's existing file was preserved. The initial candidate-check harness misinterpreted the placement preview tuple `(x,z,detector_name)` as XYZ and failed after Reconstruction/GDML export. A subsequent read-only verifier mapped it correctly to `(x,0,z)` and passed; no Reconstruction or physics failure was hidden.

`two_layer_plots/alignment.root` was rendered with `python3 -m visualization.closure` using the closure's nominal/misaligned/corrected XML and saved summary. ROOT checks confirmed L1/L2 residual graphs, both correction graphs, and the three maintained canvases. ROOT residual histograms already cover all SiMAPS layers. Stage `command.json`, `stdout.log`, `exit.json`, completion hashes and queue records retain the detailed commands.

Host checks passed:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache python3 -m unittest validation.test_geometry_correction validation.test_calibration_controller -q
PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache python3 validation/verify_preservation.py
PYTHONPYCACHEPREFIX=/private/tmp/testbench_pycache python3 validation/check_safety.py
bash -n validation/run_closure.sh
git diff --check
```

Seven unit tests cover the prior control-plane invariants plus simultaneous cumulative composition and refusal of unsupported scope. The existing safety tests continue to reject a two-layer scenario in default L2-only mode. All 5,630 inventoried pre-existing data/dependency/selected-source checksums were preserved. No C++ rebuild was needed or claimed; the existing validated Plugin was used. No commit or push was performed.

The earlier [controller validation report](CALIBRATION_CONTROLLER_VALIDATION.md) records the initial L2-only scope and remains historical; this document supersedes its scope limitation. No support for additional layers, Y/Z, rotations, MPGD or AC-LGAD alignment is implied.
