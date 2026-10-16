## EICrecon Beam-Test Tracking and Calibration Prototype

Validated outputs and status are documented in:

- `prototype/reports/prototype_status_2026-10-15.md`
- `prototype/reports/millepede_integration_notes_2026-10-15.md`

Primary run scripts:

- `prototype/scripts/run_ckf_baseline.sh`
- `prototype/scripts/run_analysis_bundle.sh`
- `prototype/scripts/run_all_validated.sh`

Key generated artifacts:

- `logs/03_ddsim_tracking.log`
- `logs/04_eicrecon_tracking_only.log`
- `logs/06_ddsim_five_layer_barrel.log`
- `prototype/results/ckf_summary.json`
- `prototype/results/five_layer_residual_stats.json`
- `prototype/results/five_layer_residual_histograms.png`
- `prototype/results/five_layer_track_display.png`



How to run
docker run --rm --platform linux/amd64 \
  -v /Users/tkumaoka/eic/OnlineTimeAlignmentTest:/work \
  -w /work \
  eicweb/eic_xl:nightly \
  bash -lc 'bash prototype/scripts/run_analysis_bundle.sh'


