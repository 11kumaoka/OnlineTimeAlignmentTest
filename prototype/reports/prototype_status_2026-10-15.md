# EICrecon beam-test tracking/alignment prototype status (2026-10-15)

## Scope and environment

- Workspace: `OnlineTimeAlignmentTest`
- Host eic-shell: not modified
- Runtime isolation: Docker only (`eicweb/eic_xl:nightly`, platform `linux/amd64`)
- Image ID: `sha256:67c914295a92396040c3051360d70786df9c1ee8458264ad0b83cd1a8ccf3d05`
- EICrecon version: `v1.37.0-14-g195966d4`
- Python: `3.13.12`

## What was validated successfully

### 1) Five-layer detector geometry in DD4hep

- Custom compact geometry file created: `prototype/geometry/five_layer_telescope_barrel.xml`
- DDSim smoke test ran successfully and produced EDM4hep output:
  - output: `artifacts/sim_five_layer_barrel.edm4hep.root`
  - log: `logs/06_ddsim_five_layer_barrel.log`
- `TelescopeHits` collection present and populated (1-event smoke test).

### 2) Simulated measurements + known injected displacement + residual estimation

- Config with explicit layer z positions and measurement resolutions:
  - `prototype/config/five_layer_telescope.json`
- Residual/alignment demo (leave-one-out straight-line fit):
  - script: `prototype/scripts/five_layer_residual_demo.py`
  - outputs:
    - `prototype/results/five_layer_residual_stats.json`
    - `prototype/results/five_layer_residual_histograms.png`
    - `prototype/results/five_layer_track_display.png`
- Injected displacement on layer 2:
  - `dx = +0.08000 mm`, `dy = -0.04000 mm`
- Estimated correction from residual mean:
  - `dx = -0.07991 mm`, `dy = +0.03985 mm`

### 3) Existing EICrecon ACTS CKF execution (no new tracking implementation)

- Baseline CKF run script:
  - `prototype/scripts/run_ckf_baseline.sh`
- Validated run artifacts:
  - simulation: `artifacts/sim_tracking.edm4hep.root`
  - reconstruction: `podio_output.root`
  - logs: `logs/03_ddsim_tracking.log`, `logs/04_eicrecon_tracking_only.log`
- CKF summary extraction script:
  - `prototype/scripts/summarize_ckf_output.py`
- Summary output:
  - `prototype/results/ckf_summary.json`

Key validated CKF metrics (20 events):
- Central measurements mean/event: `4.4`
- Central seeds mean/event: `0.6`
- Central CKF tracks total: `8` (mean/event `0.4`)
- Central truth-seeded CKF tracks total: `12`
- Mean chi2/ndf (central): `0.5595`

## What is not yet complete

- Direct EICrecon CKF reconstruction on the custom five-layer geometry in `prototype/geometry/five_layer_telescope_barrel.xml` is not yet wired.
  - Reason: EICrecon tracking chain expects detector naming/mapping conventions that are already satisfied by EPIC geometries; custom telescope naming requires additional reconstruction configuration/plumbing.
- Residual extraction currently uses:
  - EICrecon CKF summary from EPIC tracking-only run, and
  - standalone five-layer alignment closure demo.

## Command sequence used

1. Run CKF baseline in isolated Docker:
   - `bash prototype/scripts/run_ckf_baseline.sh`
2. Run analysis bundle:
   - `docker run --rm --platform linux/amd64 -v /Users/tkumaoka/eic/OnlineTimeAlignmentTest:/work -w /work eicweb/eic_xl:nightly bash -lc 'bash prototype/scripts/run_analysis_bundle.sh'`
3. Validate custom five-layer DD4hep geometry:
   - `docker run --rm --platform linux/amd64 -v /Users/tkumaoka/eic/OnlineTimeAlignmentTest:/work -w /work eicweb/eic_xl:nightly bash -lc 'ddsim --compactFile prototype/geometry/five_layer_telescope_barrel.xml --outputFile artifacts/sim_five_layer_barrel.edm4hep.root --numberOfEvents 1 --enableGun --gun.particle mu- --gun.energy 5*GeV --gun.thetaMin 1.5708 --gun.thetaMax 1.5708 --gun.phiMin 0 --gun.phiMax 0 --gun.distribution uniform > logs/06_ddsim_five_layer_barrel.log 2>&1'`

## Parallel Millepede task status

- Investigation documented in:
  - `prototype/reports/millepede_integration_notes_2026-10-15.md`
- Result:
  - ACTS alignment APIs are present.
  - Millepede-II binaries are not installed in this image.
  - Proposed path is a separate `podio -> mille` exporter and a dedicated alignment container for `pede`.
