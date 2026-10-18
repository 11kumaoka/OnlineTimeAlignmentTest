# Local EICrecon-like Implementation Report

Date: 2026-10-16
Scope: Milestones L1 and L2 (SiMAPS local chain)

## 1. Goal and status

Implemented a locally editable and buildable reconstruction package at:

- [seven_layer/local_eicrecon](seven_layer/local_eicrecon)

Current L1/L2 status:

- L1 structure and build system: complete
- L2 local SiMAPS algorithm copy and local plugin execution: complete

Current extension status:

- Local MPGD chain (Sim -> Raw -> Rec): implemented and executing
- Local AC-LGAD chain (Sim -> Raw -> Rec): implemented and executing
- Local JEventProcessor for event-level monitoring: implemented and executing

## 2. Local package structure

- [seven_layer/local_eicrecon/algorithms/digi](seven_layer/local_eicrecon/algorithms/digi)
- [seven_layer/local_eicrecon/algorithms/tracking](seven_layer/local_eicrecon/algorithms/tracking)
- [seven_layer/local_eicrecon/factories/digi](seven_layer/local_eicrecon/factories/digi)
- [seven_layer/local_eicrecon/factories/tracking](seven_layer/local_eicrecon/factories/tracking)
- [seven_layer/local_eicrecon/plugins](seven_layer/local_eicrecon/plugins)
- [seven_layer/local_eicrecon/config](seven_layer/local_eicrecon/config)
- [seven_layer/local_eicrecon/CMakeLists.txt](seven_layer/local_eicrecon/CMakeLists.txt)
- [seven_layer/local_eicrecon/README.md](seven_layer/local_eicrecon/README.md)

## 3. Source provenance (copied from read-only reference)

Read-only reference checkout:

- /Users/tkumaoka/eic/EICrecon
- revision used for inspection: 67a00864dd47c709c98b4afc2c210c3faee100b1

Copied files and purpose:

1. Local file: [seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigi.h](seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigi.h)
- Original: /Users/tkumaoka/eic/EICrecon/src/algorithms/digi/SiliconTrackerDigi.h
- Purpose: SiMAPS SimTrackerHit to RawTrackerHit digitization algorithm interface

2. Local file: [seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigi.cc](seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigi.cc)
- Original: /Users/tkumaoka/eic/EICrecon/src/algorithms/digi/SiliconTrackerDigi.cc
- Purpose: SiMAPS digitization implementation
- Local modifications: explicit runtime marker to stderr for execution proof

3. Local file: [seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigiConfig.h](seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigiConfig.h)
- Original: /Users/tkumaoka/eic/EICrecon/src/algorithms/digi/SiliconTrackerDigiConfig.h
- Purpose: configuration struct for local SiMAPS digitization

4. Local file: [seven_layer/local_eicrecon/factories/digi/SiliconTrackerDigi_factory.h](seven_layer/local_eicrecon/factories/digi/SiliconTrackerDigi_factory.h)
- Original: /Users/tkumaoka/eic/EICrecon/src/factories/digi/SiliconTrackerDigi_factory.h
- Purpose: PODIO/JANA binding for local copied digitization algorithm

5. Local file: [seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.h](seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.h)
- Original: /Users/tkumaoka/eic/EICrecon/src/algorithms/tracking/TrackerHitReconstruction.h
- Purpose: RawTrackerHit to TrackerHit reconstruction interface

6. Local file: [seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.cc](seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.cc)
- Original: /Users/tkumaoka/eic/EICrecon/src/algorithms/tracking/TrackerHitReconstruction.cc
- Purpose: RawTrackerHit to TrackerHit reconstruction implementation (uses DD4hep CellIDPositionConverter)
- Local modifications: explicit runtime marker to stderr for execution proof

7. Local file: [seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstructionConfig.h](seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstructionConfig.h)
- Original: /Users/tkumaoka/eic/EICrecon/src/algorithms/tracking/TrackerHitReconstructionConfig.h
- Purpose: configuration struct for local hit reconstruction

8. Local file: [seven_layer/local_eicrecon/factories/tracking/TrackerHitReconstruction_factory.h](seven_layer/local_eicrecon/factories/tracking/TrackerHitReconstruction_factory.h)
- Original: /Users/tkumaoka/eic/EICrecon/src/factories/tracking/TrackerHitReconstruction_factory.h
- Purpose: PODIO/JANA binding for local copied tracker-hit reconstruction

9. Local file: [seven_layer/local_eicrecon/plugins/BeamTestReco.cc](seven_layer/local_eicrecon/plugins/BeamTestReco.cc)
- Original reference pattern: /Users/tkumaoka/eic/EICrecon/src/detectors/BVTX/BVTX.cc
- Purpose: local plugin registration for SiMAPS-only chain
- Local modifications: local collection names and explicit plugin/factory registration markers

## 4. Local build and run commands

Build and run script:

- [seven_layer/scripts/build_and_run_local_eicrecon_simaps.sh](seven_layer/scripts/build_and_run_local_eicrecon_simaps.sh)

Script behavior:

1. Configure local build
2. Compile BeamTestReco shared library
3. Run eicrecon host with local plugin path appended
4. Exclude original BVTX plugin
5. Write local SiMAPS outputs to dedicated collection names

## 5. Artifacts

- Local compiled plugin:
  - [seven_layer/local_eicrecon/build/BeamTestReco.so](seven_layer/local_eicrecon/build/BeamTestReco.so)
- Build log:
  - [seven_layer/logs/local_eicrecon_build.log](seven_layer/logs/local_eicrecon_build.log)
- Runtime log:
  - [seven_layer/logs/local_eicrecon_runtime.log](seven_layer/logs/local_eicrecon_runtime.log)
- Local output file:
  - [seven_layer/results/local_simaps_reco.root](seven_layer/results/local_simaps_reco.root)

Additional runtime evidence (all local chains active):

- [seven_layer/logs/local_eicrecon_runtime.log](seven_layer/logs/local_eicrecon_runtime.log)
  - local plugin loaded from local build path
  - BVTX/MPGD/BTOF preinstalled plugins excluded
  - local SiMAPS/MPGD/ACLGAD raw+rec collections requested and produced
  - local BeamTestEventProcessor per-event and final summaries

## 6. Runtime proof points

Proof that local plugin is loaded:

- Runtime log line shows local shared object path:
  - Loading plugin BeamTestReco from /work/seven_layer/local_eicrecon/build/BeamTestReco.so

Proof that original BVTX is excluded:

- Runtime log includes exclusion marker for BVTX plugin via plugins_to_ignore

Proof that local factory outputs are produced:

- Runtime call trace includes local collection names:
  - LocalSiMAPSRawHits
  - LocalSiMAPSRecHits

Proof that local copied algorithm code executed:

- Runtime stderr markers from local source files:
  - [local_eicrecon] SiliconTrackerDigi::process call=1 (local copied source)
  - [local_eicrecon] TrackerHitReconstruction::process call=1 (local copied source)
  - Repeated call markers observed for calls 2 and 3 in the same run.

  Proof that all requested local detector chains execute:

  - Runtime markers include local algorithm instance names:
    - BeamTestReco:LocalSiMAPSRawHits / BeamTestReco:LocalSiMAPSRecHits
    - BeamTestReco:LocalMPGDRawHits / BeamTestReco:LocalMPGDRecHits
    - BeamTestReco:LocalACLGADRawHits / BeamTestReco:LocalACLGADRecHits

  Event-level processor summary (same run):

  - BeamTestEventProcessor::Finish events=80
  - simaps(raw/rec)=403/403
  - mpgd(raw/rec)=90/90
  - aclgad(raw/rec)=83/83

Proof that local collections are produced with non-zero occupancy:

- In [seven_layer/results/local_simaps_reco.root](seven_layer/results/local_simaps_reco.root):
  - SiMAPSHits: 80 events, total 403
  - LocalSiMAPSRawHits: 80 events, total 403
  - LocalSiMAPSRecHits: 80 events, total 403

## 7. Notes and constraints

- Original reference tree /Users/tkumaoka/eic/EICrecon was not modified.
- Build and runtime are contained in seven_layer workspace.
- This report covers L1 and L2 only; L3 validation and coordinate-system root-cause analysis are next.
