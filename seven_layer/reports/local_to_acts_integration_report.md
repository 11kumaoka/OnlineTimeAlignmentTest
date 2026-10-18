# Local-to-ACTS Integration Report

Date: 2026-10-16
Workspace: OnlineTimeAlignmentTest

## 1. Scope and objective

This report documents integration of local EICrecon-like reconstruction outputs with standalone ACTS tracking under:

- local reconstruction: [seven_layer/local_eicrecon](seven_layer/local_eicrecon)
- standalone ACTS: [seven_layer/standalone_acts](seven_layer/standalone_acts)

Target workflow:

DD4hep / Geant4 -> local JANA2 reconstruction plugin -> Local Raw/Rec collections -> standalone ACTS tracking

## 2. Implemented source changes

### 2.1 Standalone ACTS application

Updated file:

- [seven_layer/standalone_acts/src/standalone_acts_fit.cpp](seven_layer/standalone_acts/src/standalone_acts_fit.cpp)

Key updates:

1. T1 collection integration
- Default input switched to local reconstruction output file:
  - `seven_layer/results/local_simaps_reco.root`
- ACTS input collections switched to local names:
  - SiMAPS: `LocalSiMAPSRecHits`
  - MPGD: `LocalMPGDRecHits`
  - AC-LGAD: `LocalACLGADRecHits`
- Added explicit startup config log line proving collection names used at runtime.

2. T2 all-event processing
- Removed one-event break; processes all events in file.
- Added event-by-event logging and fit status.
- Added CSV output for per-event tracking statistics:
  - [seven_layer/results/local_to_acts_event_stats.csv](seven_layer/results/local_to_acts_event_stats.csv)

3. Geometry/coordinate handling improvements
- Plane z positions are derived from detector configuration constants used in XML:
  - SiMAPS: 0, 50, 100, 150, 200 mm
  - MPGD: 250 mm
  - AC-LGAD: 300 mm
- Added automatic mode inference (`global` vs `local`) by checking RecHit z consistency vs expected layer z.
- Uses `globalToLocal` only when data is inferred as global; otherwise uses local values directly.

4. T3 MPGD extrapolation
- Extrapolates fitted SiMAPS track to MPGD plane and stores residuals (`dx`, `dy`) per event in CSV.

5. T4 MPGD inclusion in fit
- Adds MPGD hit as sixth measurement and runs augmented fit.
- Records augmented-fit success per event.

6. T5 AC-LGAD extrapolation
- Extrapolates SiMAPS track to AC-LGAD plane and stores residuals (`dx`, `dy`) per event in CSV.
- AC-LGAD is treated as provisional spatial residual target; 1D readout caveat retained.

7. Seed policy
- Non-truth seeding only (from reconstructed SiMAPS hits / beamline direction).
- Truth-assist switch is present as diagnostic flag but disabled by default.
- In zero field, `q/p` remains a weak prior, not a measurement.

### 2.2 Standalone ACTS run script

Updated file:

- [seven_layer/scripts/run_standalone_acts_fit.sh](seven_layer/scripts/run_standalone_acts_fit.sh)

Changes:
- Now runs ACTS app on local reconstruction output file.
- Passes local collection name and CSV output path arguments.
- Prints all generated artifact paths.

## 3. Build and run commands

### 3.1 Local reconstruction production (input to ACTS)

Command:

- `bash seven_layer/scripts/build_and_run_local_eicrecon_simaps.sh`

Primary output used by ACTS:

- [seven_layer/results/local_simaps_reco.root](seven_layer/results/local_simaps_reco.root)

### 3.2 Standalone ACTS build/run

Command:

- `bash seven_layer/scripts/run_standalone_acts_fit.sh`

Generated artifacts:

- [seven_layer/logs/standalone_acts_cmake.log](seven_layer/logs/standalone_acts_cmake.log)
- [seven_layer/logs/standalone_acts_build.log](seven_layer/logs/standalone_acts_build.log)
- [seven_layer/logs/standalone_acts_fit.log](seven_layer/logs/standalone_acts_fit.log)
- [seven_layer/results/local_to_acts_event_stats.csv](seven_layer/results/local_to_acts_event_stats.csv)

## 4. Runtime evidence and milestone status

## T1: Standalone ACTS reads LocalSiMAPSRecHits

Status: achieved.

Evidence in [seven_layer/logs/standalone_acts_fit.log](seven_layer/logs/standalone_acts_fit.log):
- `config input=seven_layer/results/local_simaps_reco.root`
- `simaps_collection=LocalSiMAPSRecHits`
- `mpgd_collection=LocalMPGDRecHits`
- `aclgad_collection=LocalACLGADRecHits`

No fallback to legacy `SiMAPSRecHits` is used by the ACTS app.

## T2: All-event SiMAPS tracking with fit-quality output

Status: achieved.

From [seven_layer/logs/standalone_acts_fit.log](seven_layer/logs/standalone_acts_fit.log):
- `events_processed=80`
- `seeds=80`
- `fit_success=80`
- `fit_fail=0`

From [seven_layer/results/local_to_acts_event_stats.csv](seven_layer/results/local_to_acts_event_stats.csv):
- 80 event rows
- valid per-event fields including:
  - event index
  - per-layer hit counts
  - seed count
  - fit success
  - nMeasurements
  - chi2, ndf, chi2/ndf
  - reference-surface position/direction

Aggregated values:
- fit_ok events: 80/80
- mean chi2/ndf: 0.313505
- measurement usage: nMeas=5 for all successful SiMAPS fits

### Why previous demo used 4 measurements and now 5

Root cause in earlier version:
- Fit sequence/seed/surface handling and reference-target setup resulted in one measurement not being retained in the fit summary.

Current resolution:
- Ordered source-link/surface sequence by z.
- Seeded before first surface and used stable reference surface handling.
- Result: all five SiMAPS measurements are used consistently (`nMeas=5`).

## T3: Extrapolate SiMAPS tracks to MPGD and compute residuals

Status: achieved.

Residuals are computed per event and written to CSV.

Aggregate (fit_ok events):
- MPGD dx: count=80, mean=3.64e-17 mm, sigma=5.32e-17 mm
- MPGD dy: count=80, mean=-0.0296 mm, sigma=0.1638 mm

## T4: Incorporate MPGD into ACTS fit

Status: achieved (provisional model).

Implementation:
- Added sixth measurement from `LocalMPGDRecHits` and executed augmented fit.

Runtime summary:
- `fit_success_mpgd_augmented=80`

Important limitation:
- Current local MPGD chain uses SiliconTrackerDigi/TrackerHitReconstruction approximation, not MPGD-specific response model.
- These results demonstrate framework integration, not final detector-response fidelity.

## T5: Extrapolate tracks to AC-LGAD and validate measured coordinate

Status: achieved for spatial extrapolation diagnostics.

Residuals are computed per event and written to CSV.

Aggregate (fit_ok events):
- AC-LGAD dx: count=80, mean=6.35e-17 mm, sigma=9.28e-17 mm
- AC-LGAD dy: count=80, mean=0.0285 mm, sigma=0.3670 mm

Readout/model caveat:
- AC-LGAD is currently represented with coarse second coordinate in geometry (`grid_size_y=100 mm`).
- Treat y residual as provisional; x is the physically meaningful measured coordinate in this approximation.

## 5. Coordinate and covariance diagnostics (current)

Quick checks on local RecHit collections (same input file):

- `LocalSiMAPSRecHits`:
  - z means by layer approximately {0, 50, 100, 150, 200} mm
  - covariance means: exx~1e-4 mm^2, eyy~1e-4 mm^2
- `LocalMPGDRecHits`:
  - layer 5 z mean ~249.94 mm, z sigma ~0.383 mm
  - covariance means: exx~0.0225 mm^2, eyy~0.0225 mm^2
- `LocalACLGADRecHits`:
  - layer 6 z mean 300 mm
  - covariance means: exx~0.02083 mm^2, eyy~833.33 mm^2

Interpretation:
- Current local RecHits are mostly in global coordinates for these collections.
- AC-LGAD covariance strongly reflects the intended 1D-like approximation (very large unresolved coordinate variance).

## 6. Limitations and remaining issues

1. Full DD4hep-to-ACTS surface mapping for each CellID is not yet implemented.
- Current ACTS planes are explicit telescope planes whose transforms are derived from the detector configuration constants.
- This is acceptable for current telescope milestone but not yet a full generalized mapper.

2. MPGD and AC-LGAD response models are still provisional in local chain.
- MPGD currently uses silicon-like digitization path.
- AC-LGAD timing/electronics modeling is not yet integrated.

3. Momentum in B=0 remains weakly constrained.
- `q/p` seed prior is not interpreted as a momentum measurement.

## 7. Success summary

- T1: complete
- T2: complete
- T3: complete (residual diagnostics)
- T4: complete (provisional augmented fit)
- T5: complete (spatial extrapolation diagnostics, with 1D caveat)

All milestones above are supported by runtime logs and per-event CSV outputs under seven_layer.
