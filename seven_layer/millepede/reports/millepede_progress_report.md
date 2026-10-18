# Millepede-II Integration Progress Report

Date: 2026-10-16
Workspace: OnlineTimeAlignmentTest

## 1) Official software source and build

Official sources cloned locally under workspace:

- Millepede-II: `seven_layer/millepede/third_party/millepede-ii`
  - URL: https://gitlab.desy.de/millepede/millepede-ii
- Mille C++ writer: `seven_layer/millepede/third_party/Mille`
  - URL: https://gitlab.desy.de/millepede/Mille

Local builds/install (no global install):

- Mille install prefix: `seven_layer/millepede/install/mille`
- Millepede-II install prefix: `seven_layer/millepede/install/millepede-ii`

Build logs:

- `seven_layer/logs/mille_cmake.log`
- `seven_layer/logs/mille_build.log`
- `seven_layer/logs/mille_install.log`
- `seven_layer/logs/millepede_cmake.log`
- `seven_layer/logs/millepede_build.log`
- `seven_layer/logs/millepede_install.log`

## 2) M1: real pede execution

`pede` executable runs from local install.

- startup test (`pede -t`) confirmed binary execution and version banner.
- official internal BRLF test (`pede -t=BRLF`) completed with exit code 0.

Logs:

- `seven_layer/logs/pede_test_t.log`
- `seven_layer/logs/pede_test_brlf.log`

## 3) Alignment model and sign convention

Model used for five SiMAPS layers (L0..L4):

- local track parameters: `(x0, y0, tx, ty)` at `zref = 100 mm`
- global parameters: `a_x[layer]`, `a_y[layer]`

Measurement equations:

- `x_meas = x0 + tx*(z-zref) + a_x[layer] + noise_x`
- `y_meas = y0 + ty*(z-zref) + a_y[layer] + noise_y`

Derivatives:

- x row local derivs: `(1, 0, z-zref, 0)`
- y row local derivs: `(0, 1, 0, z-zref)`
- global derivs: `+1` for matching layer/bias parameter

Sign convention:

- solved `a_x`, `a_y` are additive measurement biases
- coordinate correction to apply to measurements is `-a_x`, `-a_y`

Gauge fixing:

- fixed references: L0 and L4 in both x and y
- active globals: `1001,1002,1003,2001,2002,2003`

Label mapping:

- `1000+layer` -> `a_x[layer]`
- `2000+layer` -> `a_y[layer]`

## 4) Reusable official Mille writer module

Added:

- `seven_layer/millepede/src/BeamTestMilleWriter.h`
- `seven_layer/millepede/src/BeamTestMilleWriter.cc`

Implementation uses official Mille C++ API (`MilleRecord`) and writes one record per accepted track.
Each record includes x/y measurements for all five layers with:

- measurement value
- positive sigma
- 4 local derivatives
- 1 global derivative per row

## 5) M2: toy closure with real Mille + real pede

Toy generator and scripts:

- `seven_layer/millepede/src/beamtest_mille_toy.cc`
- `seven_layer/millepede/scripts/build_mille_tools.sh`
- `seven_layer/millepede/scripts/run_toy_closure.sh`
- steering template: `seven_layer/millepede/config/beamtest_pede_5layer_template.txt`

Toy output directory:

- `seven_layer/millepede/results/toy`

Closure summary (selected):

- Inject `a_x[L2]=+0.200 mm` -> solved `1002 ≈ +0.19976 mm`
- Inject `a_x[L2]=-0.200 mm` -> solved `1002 ≈ -0.20024 mm`
- Inject `a_y[L2]=+0.150 mm` -> solved `2002 ≈ +0.15009 mm`
- Multi-layer injected case recovered all injected signs/magnitudes within expected precision.

## 6) M3: in-process JANA2 Mille integration

Integrated processor added (same event loop as reco/tracking):

- `seven_layer/local_eicrecon/processors/BeamTestMilleProcessor.h`
- `seven_layer/local_eicrecon/processors/BeamTestMilleProcessor.cc`

Plugin registration:

- `seven_layer/local_eicrecon/plugins/BeamTestReco.cc`

Build integration:

- `seven_layer/local_eicrecon/CMakeLists.txt` links to official `Mille2`

Data sources used by processor:

- `LocalSiMAPSRecHits`
- `LocalBeamTestTracks`

Selection policy (first pass):

- require exactly one selected track per event
- require exactly one associated SiMAPS hit per layer for layers 0..4
- skip ambiguous/missing events with explicit counters

No SimTrackerHit positions are used for Mille measurement writing.

## 7) M4: integrated baseline Mille solve

Integrated run produced both outputs from one JANA2 process:

- PODIO ROOT: `seven_layer/results/local_simaps_reco_mille_integrated.root`
- Mille binary: `seven_layer/millepede/results/integrated/local_beamtest_mille_integrated.dat`

Run diagnostics:

- events processed: 80
- accepted tracks: 80
- rejected/ambiguous: 0
- records written: 80
- measurements written: 800 (10 per record)

Runtime log:

- `seven_layer/logs/local_eicrecon_runtime_mille_integrated.log`

Pede baseline solve artifacts:

- steering: `seven_layer/millepede/results/integrated/beamtest_integrated_pede.txt`
- solver log: `seven_layer/millepede/results/integrated/integrated_pede.log`
- result: `seven_layer/millepede/results/integrated/integrated_millepede.res`
- full Millepede log copy: `seven_layer/millepede/results/integrated/integrated_millepede.log`

Solver status:

- `No rank defect of the symmetric matrix`

Recovered active parameters (baseline, mm scale):

- `1001=-3.3309e-4`
- `1002=+2.2207e-4`
- `1003=+3.3310e-4`
- `2001=+1.8875e-3`
- `2002=+1.5544e-3`
- `2003=+1.2213e-3`

These are small and compatible with a baseline sample without a known injected misalignment.

## 8) M5: injected-shift closure

Important distinction:

- old ACTS fitter shift option affected fitter internals but did not alter the measurements consumed by the Mille processor.
- therefore it produced no change in solved Mille parameters.

To perform a genuine closure, explicit measurement-stage injection was added in the Mille processor:

- parameters:
  - `beamtstreco:milleInjectedShiftLayer`
  - `beamtstreco:milleInjectedShiftXmm`
  - `beamtstreco:milleInjectedShiftYmm`

Injected integrated run (+0.200 mm on layer-2 x at Mille writing stage):

- Mille binary: `seven_layer/millepede/results/integrated/local_beamtest_mille_integrated_milleInjL2x0200.dat`
- log: `seven_layer/logs/local_eicrecon_runtime_mille_integrated_milleInjL2x0200.log`
- counters: events 80, accepted 80, records 80, measurements 800

Injected pede solve artifacts:

- steering: `seven_layer/millepede/results/integrated/beamtest_integrated_milleInj_pede.txt`
- solver log: `seven_layer/millepede/results/integrated/integrated_milleInj_pede.log`
- result: `seven_layer/millepede/results/integrated/integrated_milleInj_millepede.res`
- full Millepede log copy: `seven_layer/millepede/results/integrated/integrated_milleInj_millepede.log`

Recovered closure signal:

- baseline `1002 = +2.2207e-4`
- injected `1002 = +2.0022e-1`
- delta `~ +0.199998 mm`

Other active parameters remain unchanged within precision, as expected for a single-layer x injection.

This matches the injected sign and magnitude for `a_x[L2]`.
The corresponding measurement correction sign remains `-a_x[L2]`.

## 9) Helper scripts

Added reproducible scripts:

- `seven_layer/millepede/scripts/run_integrated_mille_baseline.sh`
- `seven_layer/millepede/scripts/run_integrated_mille_injected.sh`
- `seven_layer/millepede/scripts/run_pede_from_dat.sh`
- `seven_layer/millepede/scripts/summarize_pede_res.py`

## 10) Remaining limitations and next steps

Current status:

- M1 complete
- M2 complete
- M3 complete
- M4 complete
- M5 complete for measurement-stage injected closure

Remaining work to extend toward full geometry-alignment closure:

1. Feed solved corrections back into reconstruction geometry/measurement model and rerun tracking to verify post-correction residual improvement quantitatively.
2. Add robust multi-track/hit association handling using explicit source links/associations if event complexity increases.
3. Expand model to include rotations and additional detector layers (MPGD/AC-LGAD) after SiMAPS baseline is stabilized.
4. Add automated comparison report (baseline vs injected vs corrected) in one command.
