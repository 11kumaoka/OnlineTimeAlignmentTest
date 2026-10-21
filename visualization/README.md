# ROOT Visualization

`closure.py` renders Detector Geometry, Hit Residuals, and Alignment Closure from
numerical metrics produced by `validation/metrics.py`. It does not execute physics
stages. The supported validation entry point is `validation/validate.sh`.

Completed runs store `result/<name>/step7/summary.json` and `alignment.root`.
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
