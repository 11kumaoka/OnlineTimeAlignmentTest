# ROOT Visualization

## Primary native reports

The maintained `calibration.workflow` writes
`result/<run>/report/diagnostics.root` together with `summary.json`, `report.md`
and the root-level `run_manifest.json`. Its ROOT implementation is
`calibration.workflow.root_report`; it plots actual fit residuals, ACTS/Pede
chi2, Pede updates/errors, cumulative Global Y corrections and audited Geometry
centers. Truth Geometry is displayed only for validation, never used to calculate
corrections. See the [practical User Guide](../docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md).

```bash
root --web=off -l 'visualization/browse.C("result/NATIVE_RUN/report/diagnostics.root")'
```

Replace `NATIVE_RUN` with a completed run. ROOT GUI/X11 is required for interactive
browsing; the validation checks batch serialization and numerical object
contents, not interactive GUI operation. No interactive GUI test was performed.

## Retained legacy +Z plots

`closure.py` renders Detector Geometry, Hit Residuals, and Alignment Closure from
numerical metrics produced by `validation/metrics.py`. It does not execute physics
stages. Its legacy validation entry point is `validation/validate.sh`.

Completed legacy runs store `result/<name>/step7/summary.json` and `alignment.root`.
The ROOT file contains three TCanvases, residual TH1Ds, and Closure TGraphs.
Standalone rendering from an existing summary uses a new output directory:

```bash
bash environment/run.sh python3 -m visualization.closure --nominal result/example/step1/nominal.xml --misaligned result/example/step1/misaligned.xml --corrected result/example/step5/corrected.xml --summary result/example/step7/summary.json --outdir result/example/render_again
root --web=off -l 'visualization/browse.C("result/example/step7/alignment.root")'
```

Use `validation/check_root_outputs.py --result-dir result/example` for batch checks.
Interactive browsing requires ROOT GUI/X11; Docker/XQuartz users can enter
`environment/root_shell.sh`, then `cd /work`. The geometry view is a schematic
for the current unrotated seven-layer detector. No interactive GUI test was run.
