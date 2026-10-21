# ROOT Visualization

The supported batch entry is `closure.py --help`, normally invoked by
`workflow.py validate`. It reads PODIO split branches with uproot/awkward and
writes PyROOT TCanvas, TH1D, and TGraph objects. No browser or OpenGL viewer is used.

A NEW `--outdir` receives `alignment.root` and `summary.json`. Existing directories
are refused. The maintained workflow places them under
`results/<name>/validation/plots/`.

Three canvases are saved: `c_geometry`, `c_hit_residuals`, and `c_closure`.
Hit Residual histograms contain before/after x/y distributions for five SiMAPS
layers. Closure displays actual before/after measurements and the applied
Geometry Correction, not internal pede iterations. The geometry view is a
placement schematic restricted to the supported single-module telescope.

`summary.json` retains historical pooled Rec mean minus Sim mean metrics and
records unique event/layer residual arrays and ambiguity counts. The Track
Fitting quality ratio uses stored ACTS measurement dimensions, not a redefined
statistical degree of freedom.

On a ROOT GUI host:

```bash
root --web=off -l 'local_detector_testbench/visualization/browse.C("results/electron_001/validation/plots/alignment.root")'
```

Batch checks use `validation/check_root_outputs.py --result-dir results/electron_001`.
Historical experimental viewers are stored only in the external archive described
in `docs/FINAL_SIMPLIFICATION.md`.
