# JANA2 Integrated ACTS Report

Date: 2026-10-16
Workspace: OnlineTimeAlignmentTest

## 1) Objective

Implemented single-process integrated reconstruction chain inside one JANA2/eicrecon invocation:

PODIO input -> local digitization factories -> local hit reconstruction factories -> local ACTS tracking factory -> PODIO output

No separate ACTS executable is required for the production chain.

## 2) New local ACTS components

Added under local framework:

- [seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitterConfig.h](seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitterConfig.h)
- [seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.h](seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.h)
- [seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.cc](seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.cc)
- [seven_layer/local_eicrecon/factories/tracking/BeamTestACTSFitter_factory.h](seven_layer/local_eicrecon/factories/tracking/BeamTestACTSFitter_factory.h)

Integration updates:

- plugin registration in [seven_layer/local_eicrecon/plugins/BeamTestReco.cc](seven_layer/local_eicrecon/plugins/BeamTestReco.cc)
- build linkage in [seven_layer/local_eicrecon/CMakeLists.txt](seven_layer/local_eicrecon/CMakeLists.txt)
- event-level monitoring extension in:
  - [seven_layer/local_eicrecon/processors/BeamTestEventProcessor.h](seven_layer/local_eicrecon/processors/BeamTestEventProcessor.h)
  - [seven_layer/local_eicrecon/processors/BeamTestEventProcessor.cc](seven_layer/local_eicrecon/processors/BeamTestEventProcessor.cc)

## 3) Plugin registration and collection flow

Within BeamTestReco plugin, registered local chain:

1. SiMAPS local digi/rec
- `SiMAPSHits -> LocalSiMAPSRawHits -> LocalSiMAPSRecHits`

2. MPGD local digi/rec (temporary silicon-based approximation)
- `MPGDHits -> LocalMPGDRawHits -> LocalMPGDRecHits`

3. AC-LGAD local digi/rec (temporary silicon-based approximation)
- `ACLGADHits -> LocalACLGADRawHits -> LocalACLGADRecHits`

4. Integrated local ACTS fitting factory
- Inputs:
  - `LocalSiMAPSRecHits`
  - `LocalMPGDRecHits`
  - `LocalACLGADRecHits`
- Outputs:
  - `LocalBeamTestTrajectories`
  - `LocalBeamTestTrackParameters`
  - `LocalBeamTestTracks`
  - `LocalBeamTestFitMeasurements`
  - `LocalBeamTestPredictedMeasurements`
  - `LocalBeamTestFilteredMeasurements`
  - `LocalBeamTestSmoothedMeasurements`
  - `LocalBeamTestPredictedSegments`
  - `LocalBeamTestFilteredSegments`
  - `LocalBeamTestSmoothedSegments`

Factory metadata defaults now match beam-test simulation assumptions:

- particle hypothesis: muon (`useMuonHypothesis=true`)
- output PDG: `-13`
- q/p seed retained as prior only (`seedQOverP=-0.2` in 1/GeV)

5. BeamTestEventProcessor (monitoring only)
- Reads local raw/rec/track outputs and prints event and summary diagnostics.

## 4) Single-process command used

Command (scripted):

- `bash seven_layer/scripts/build_and_run_local_eicrecon_simaps.sh`

Isolated known-shift validation command (scripted):

- `bash seven_layer/scripts/run_local_eicrecon_alignment_shifttest.sh`

Script path:

- [seven_layer/scripts/build_and_run_local_eicrecon_simaps.sh](seven_layer/scripts/build_and_run_local_eicrecon_simaps.sh)
- [seven_layer/scripts/run_local_eicrecon_alignment_shifttest.sh](seven_layer/scripts/run_local_eicrecon_alignment_shifttest.sh)

This command performs, in one eicrecon process:

- input file: `seven_layer/results/phase2_sim_quick.edm4hep.root`
- local plugin load: `BeamTestReco.so`
- plugin exclusions: `BVTX,MPGD,BTOF,tracking`
- output file: `seven_layer/results/local_simaps_reco.root`
- output collections include local raw/rec and local ACTS track products.

## 5) Build and runtime logs

- Build log: [seven_layer/logs/local_eicrecon_build.log](seven_layer/logs/local_eicrecon_build.log)
- Runtime log: [seven_layer/logs/local_eicrecon_runtime.log](seven_layer/logs/local_eicrecon_runtime.log)
- Output ROOT: [seven_layer/results/local_simaps_reco.root](seven_layer/results/local_simaps_reco.root)

Build result:
- `Built target BeamTestReco`

## 6) Runtime evidence of same-process execution

From runtime log:

1. Local plugin loaded
- `Loading plugin 'BeamTestReco' from '/work/seven_layer/local_eicrecon/build/BeamTestReco.so'`

2. Local detector plugins excluded
- `Excluding plugin BVTX`
- `Excluding plugin MPGD`
- `Excluding plugin BTOF`
- `Excluding plugin tracking`

3. Local digi/rec executed
- local SiliconTrackerDigi and TrackerHitReconstruction markers for SiMAPS/MPGD/ACLGAD

4. Local ACTS factory executed
- `[local_eicrecon] BeamTestACTSFitter::init surfaces=7 useMPGD=1 useACLGAD=0`
- `[local_eicrecon] BeamTestACTSFitter::process event=1 ...`

5. PODIO writer persisted tracking outputs
- `podio:output_collections` includes `LocalBeamTestTrajectories`, `LocalBeamTestTrackParameters`, `LocalBeamTestTracks`

## 7) Output collection content checks

In [seven_layer/results/local_simaps_reco.root](seven_layer/results/local_simaps_reco.root):

Present and non-empty local track products:

- `LocalBeamTestTracks` (18 branches)
- `LocalBeamTestTrackParameters` (10 branches)
- `LocalBeamTestTrajectories` (16 branches)

Present and non-empty alignment diagnostics products:

- `LocalBeamTestFitMeasurements` (14 branches)
- `LocalBeamTestPredictedMeasurements` (14 branches)
- `LocalBeamTestFilteredMeasurements` (14 branches)
- `LocalBeamTestSmoothedMeasurements` (14 branches)
- `LocalBeamTestPredictedSegments` (4 branches)
- `LocalBeamTestFilteredSegments` (4 branches)
- `LocalBeamTestSmoothedSegments` (4 branches)

Counts over 80 events:

- `LocalBeamTestTracks`: total 80 (mean 1.0/event)
- `LocalBeamTestTrackParameters`: total 80
- `LocalBeamTestTrajectories`: total 80
- `LocalBeamTestFitMeasurements`: total 480 (mean 6/event)
- `LocalBeamTestPredictedMeasurements`: total 480 (mean 6/event)
- `LocalBeamTestFilteredMeasurements`: total 480 (mean 6/event)
- `LocalBeamTestSmoothedMeasurements`: total 480 (mean 6/event)
- `LocalBeamTestPredictedSegments`: total 80
- `LocalBeamTestFilteredSegments`: total 80
- `LocalBeamTestSmoothedSegments`: total 80

Local rec-hit collections in same file:

- `LocalSiMAPSRecHits`: total 403
- `LocalMPGDRecHits`: total 90
- `LocalACLGADRecHits`: total 83

## 8) Integrated track statistics (80-event run)

From local event processor summary and ROOT checks:

- events: 80
- tracks_total: 80
- events_with_tracks: 80
- events_without_tracks: 0
- fit failures: 0
- trajectory nMeasurements:
  - unique: {6}
  - nMeasurements >= 6: 80
- measurement-to-surface uniqueness per track:
  - unique surfaces OK: 80
  - unique surfaces BAD: 0
- chi2/ndf:
  - chi2_sum: 347.896
  - ndf_sum: 960
  - mean chi2/ndf: 0.36239

## 8.1 NDF interpretation (ACTS NDF vs classical straight-line NDF)

Observed per-track values in this run:

- ACTS-reported NDF: 12 (sum over 80 tracks: 960)
- Classical 2D straight-line estimate for 6 hits with 4 free parameters: 8 (sum: 640)

Reason for discrepancy:

- In ACTS v45.3.0, the NDF reported on the fitted track follows ACTS track-quantity accumulation and includes calibrated measurement dimensionality contributions (for this setup effectively 2 per 2D measurement), yielding 12 for 6 measurements.
- This differs from the conventional straight-line residual-count denominator `2*Nmeas - 4` (=8 for 6 planes).

Action for physics validation:

- keep reporting both ACTS NDF and classical reference NDF in diagnostics.
- avoid interpreting chi2/NDF as final physics-quality metric until NDF convention is fixed and documented against ACTS internals for this exact fitter configuration.

## 9) Geometry and covariance limitations

1. Geometry setup
- Current local ACTS fitter uses explicit 7 plane surfaces with z positions consistent with [seven_layer/geometry/seven_layer_telescope.xml](seven_layer/geometry/seven_layer_telescope.xml).
- Full DD4hep CellID-to-ACTS-surface mapping service is not yet generalized; current setup is telescope-specific.

2. Coordinate convention
- explicit configuration parameter `inputHitsAreGlobal` is now used in the integrated ACTS fitter configuration.
- no per-event coordinate guessing is used for final coordinate selection.
- z-consistency checks are retained only as sanity diagnostics.

3. Residual diagnostics
- fit/predicted/filtered/smoothed local measurement coordinates are persisted in dedicated Measurement2D collections.
- residuals are computed from explicit coordinate differences, not from `Measurement2D.weights`.
- `Measurement2D.weights` is left empty for these diagnostics (verified total entries = 0 for all four diagnostics collections).
- baseline residual summaries from persisted local coordinates are:
  - predicted residual a: mean 2.63e-17 mm, sigma 4.04e-17 mm
  - predicted residual b: mean -3.91e-3 mm, sigma 7.09e-2 mm
  - filtered residual a: mean 1.21e-17 mm, sigma 2.66e-17 mm
  - filtered residual b: mean -4.89e-3 mm, sigma 6.76e-2 mm
  - smoothed residual a: mean 4.53e-5 mm, sigma 9.92e-4 mm
  - smoothed residual b: mean -4.73e-3 mm, sigma 6.80e-2 mm

Known-shift response validation:

- isolated test input copy: `phase2_sim_quick_shifttest_input.edm4hep.root`
- applied shift: `+0.5 mm` in local-a on layer 2 via
  - `BeamTestReco:LocalBeamTestTracks:alignmentTestShiftLayer=2`
  - `BeamTestReco:LocalBeamTestTracks:alignmentTestShiftXmm=0.5`
- observed residual mean shifts (shifted - baseline):
  - predicted residual mean a: `-6.196e-2 mm`
  - filtered residual mean a: `-4.131e-2 mm`
  - smoothed residual mean a: `-1.708e-2 mm`

This confirms local-a residuals are not intrinsically zero and respond to controlled misalignment perturbations.

3.1 Investigation of near-zero local-a residuals

Observed in baseline:

- SiMAPS reconstructed-hit x values are concentrated near zero across layers (means ~1e-17 mm scale, very small spread).
- ACTS fit/predicted/filtered local-a coordinates are also near zero with tiny spread.

Numerical check (baseline file):

- `LocalSiMAPSRecHits` x by layer (std, mm):
  - L0: 1.33e-17
  - L1: 4.40e-17
  - L2: 8.49e-17
  - L3: 2.75e-16
  - L4: 2.00e-16
- `LocalBeamTestFitMeasurements.loc.a`: std 1.28e-16 mm
- `LocalBeamTestPredictedMeasurements.loc.a`: std 1.61e-16 mm
- `LocalBeamTestFilteredMeasurements.loc.a`: std 1.47e-16 mm

Interpretation:

- the tiny baseline local-a residuals are driven by the current near-axis beam/hit geometry and coordinate convention in this setup.
- they must not be interpreted as proof of alignment quality.
- the controlled shift test demonstrates measurable response and is therefore used as the practical sanity check.

4. Covariance export semantics
- measurement covariance: exported in `LocalBeamTestFitMeasurements.covariance`
- predicted-state covariance: exported in `LocalBeamTestPredictedMeasurements.covariance`
- filtered-state covariance: exported in `LocalBeamTestFilteredMeasurements.covariance`
- smoothed-state covariance: exported in `LocalBeamTestSmoothedMeasurements.covariance`
- these categories are distinct and non-zero in the persisted output.

3. Detector response approximations
- MPGD and AC-LGAD local digi/rec remain temporary silicon-based approximations.
- AC-LGAD is still treated as provisional 1D-like measurement in detector modeling terms.

4. Momentum interpretation
- zero-field fit uses seeded qOverP as weak prior only; not interpreted as direct momentum measurement.

## 10) Coordinate issue investigation and source correction

### 10.1 Root-cause tracing

The original issue was confirmed: SiMAPS reconstructed x was near-constant while y carried most transverse variation.

Tracing path:

1. SimTrackerHit global coordinates showed expected x spread growing with z.
2. DD4hep field decoding (using decoder, not manual shifts) showed for the old setup:
   - `x` field strongly correlated with Sim y
   - second segmented field effectively degenerate
3. For the telescope compact readout, the decoded field description was inspected directly from DD4hep.

Updated SiMAPS readout now uses:

- segmentation: `CartesianGridXZ`
- ID description: `system:0:8,barrel:8:3,layer:11:6,wedge:17:5,module:22:6,sensor:28:4,x:32:-16,z:48:-16`

This removes the axis degeneracy for the present seven-plane setup.

### 10.2 Separation of normal and truth-assisted modes

`TrackerHitReconstruction` now has two explicit modes:

- normal mode (default):
  - `useTruthPositionForDiagnostics=false`
  - rec-hit coordinates from raw hit + CellID + segmentation + geometry converter only
- optional truth-assisted diagnostic mode:
  - `useTruthPositionForDiagnostics=true`
  - association-weighted SimTrackerHit barycenter for debugging only

Plugin wiring:

- default outputs (`LocalSiMAPSRecHits`, `LocalMPGDRecHits`, `LocalACLGADRecHits`) run in normal mode.
- optional clearly-labeled truth outputs (`LocalSiMAPSRecHitsTruthDiag`, etc.) are created only when `beamtstreco:enableTruthDiagnosticRecHits=true`.

### 10.3 Revalidation in normal mode (truth-independent)

Input/output files used:

- sim: `seven_layer/results/phase2_sim_quick_normal_recofix.edm4hep.root`
- reco: `seven_layer/results/local_simaps_reco_normal_recofix.root`
- runtime log: `seven_layer/logs/local_eicrecon_runtime_normal_recofix.log`

Normal-mode confirmation in log:

- `TrackerHitReconstruction::process ... mode=normal`

Per-layer (SiMAPS) summary, matched by CellID:

- layer 0:
  - sim x std 0.1836 mm, rec x std 0.1847 mm
  - sim y std 0.1693 mm, rec y std 0.1706 mm
  - corr(sim,rec): x 0.9984, y 0.9985
  - residual mean/rms: x +4.78e-4 / 1.04e-2 mm, y -9.89e-4 / 9.46e-3 mm
- layer 1:
  - sim x std 0.7633 mm, rec x std 0.7636 mm
  - sim y std 0.7126 mm, rec y std 0.7115 mm
  - corr(sim,rec): x 0.9999, y 0.9999
  - residual mean/rms: x -1.53e-4 / 1.03e-2 mm, y +1.03e-3 / 9.57e-3 mm
- layer 2:
  - sim x std 1.4845 mm, rec x std 1.4840 mm
  - sim y std 1.5413 mm, rec y std 1.5413 mm
  - corr(sim,rec): x 0.99998, y 0.99998
  - residual mean/rms: x +4.28e-5 / 9.43e-3 mm, y +7.97e-4 / 9.86e-3 mm
- layer 3:
  - sim x std 2.2908 mm, rec x std 2.2928 mm
  - sim y std 3.9573 mm, rec y std 3.9566 mm
  - corr(sim,rec): x 0.99999, y 0.999997
  - residual mean/rms: x -3.12e-4 / 1.01e-2 mm, y +1.48e-4 / 9.68e-3 mm
- layer 4:
  - sim x std 3.5471 mm, rec x std 3.5452 mm
  - sim y std 3.5183 mm, rec y std 3.5191 mm
  - corr(sim,rec): x 0.999996, y 0.999996
  - residual mean/rms: x -2.10e-4 / 9.99e-3 mm, y -7.81e-4 / 9.41e-3 mm

Pixel pitch and expected resolution:

- SiMAPS pitch: 0.034641 mm
- expected digitization sigma: pitch/sqrt(12) = 0.0100 mm
- observed mean sqrt(positionError.xx/yy): ~0.0100 mm

Coordinate conversion success:

- rec/sim counts per layer were matched one-to-one (success fraction 1.0 for this sample).

### 10.4 Controlled-direction tests in normal mode

Single-event tests with fixed directions (`theta=20 mrad`):

- phi=0:
  - rec x by layer: 0.0, +1.0046, +2.0092, +3.0138, +4.0184 mm
- phi=pi:
  - rec x by layer: 0.0, -1.0046, -2.0092, -3.0138, -3.9837 mm

This demonstrates physically correct x response in truth-independent reconstruction.

### 10.5 VolumeManager / converter status

- no `Failed to get position and dimension` messages in normal-mode runtime logs.
- generic startup `acts` DD4hep-tracking-volume warning remains, but local one-process chain executes and writes outputs correctly.

## 11) Shift-test interpretation (measurement sanity vs alignment closure)

`excludeLayerFromFit` is used for independent-reference tests.

Matched-condition runs (same excluded layer):

- baseline: `excludeLayerFromFit=2`, no shift
- shift-config run: `excludeLayerFromFit=2`, `alignmentTestShiftLayer=2`, `alignmentTestShiftXmm=0.5`

Because the shifted layer is excluded from the fit, the shift-config run is expected to leave the fitted reference unchanged (verified: delta mean residual = 0 within precision).

To demonstrate explicit measurement-shift sensitivity, a separate analysis-only perturbation was applied to the excluded-layer measurement:

- baseline mean dx: -0.01362 mm
- analysis-only +0.5 mm perturbation on excluded measurement: mean dx 0.48638 mm
- delta mean dx: +0.50000 mm

Interpretation:

- this is a measurement-shift sanity test.
- it is not an alignment closure test and is labeled as such.

## 12) Remaining issues before Millepede-II integration

1. Promote the current diagnostics collections to a finalized alignment I/O contract (field-level schema notes and versioning for Millepede-II tools).
2. Centralize detector-surface mapping in a dedicated geometry adapter service (current explicit 7-plane telescope setup is correct for this beam-test but not yet generalized).
3. Upgrade MPGD and AC-LGAD digitization/reco to detector-specific algorithms while preserving current factory interfaces.
4. Add explicit unbiased-residual mode preparation and derivative containers for later Millepede-II interfacing (without introducing solver inputs yet).

## 13) Acceptance criterion status

Primary criterion:
- Sim -> Raw -> Rec -> ACTS Track Fit occurs within one JANA2 process and results are saved in same PODIO output file.

Status:
- achieved.
