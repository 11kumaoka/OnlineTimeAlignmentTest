# Phase 2 reconstruction report

Date: 2026-10-16
Workspace: OnlineTimeAlignmentTest

## 1) Implemented pipeline and scope

Implemented under seven_layer only:

- Geometry updates for segmentation and tracker metadata:
  - [seven_layer/geometry/seven_layer_telescope.xml](seven_layer/geometry/seven_layer_telescope.xml)
- Phase 2 orchestration script:
  - [seven_layer/scripts/run_phase2_reconstruction.sh](seven_layer/scripts/run_phase2_reconstruction.sh)
- Phase 2 chain analyzer:
  - [seven_layer/scripts/analyze_phase2_chain.py](seven_layer/scripts/analyze_phase2_chain.py)
  - [seven_layer/scripts/validate_rec_positions_assoc.py](seven_layer/scripts/validate_rec_positions_assoc.py)
- Standalone ACTS fitter application (outside EICrecon tracking plugin chain):
  - [seven_layer/standalone_acts/CMakeLists.txt](seven_layer/standalone_acts/CMakeLists.txt)
  - [seven_layer/standalone_acts/src/standalone_acts_fit.cpp](seven_layer/standalone_acts/src/standalone_acts_fit.cpp)
  - [seven_layer/scripts/run_standalone_acts_fit.sh](seven_layer/scripts/run_standalone_acts_fit.sh)
- New logs and outputs:
  - [seven_layer/logs/phase2_ddsim.log](seven_layer/logs/phase2_ddsim.log)
  - [seven_layer/logs/phase2_eicrecon_simaps.log](seven_layer/logs/phase2_eicrecon_simaps.log)
  - [seven_layer/logs/phase2_eicrecon_trace.log](seven_layer/logs/phase2_eicrecon_trace.log)
  - [seven_layer/logs/phase2_stageAB.log](seven_layer/logs/phase2_stageAB.log)
  - [seven_layer/results/phase2_sim_beam.edm4hep.root](seven_layer/results/phase2_sim_beam.edm4hep.root)
  - [seven_layer/results/phase2_reco_simaps.root](seven_layer/results/phase2_reco_simaps.root)

No five-layer artifacts were modified.

## 2) Installed software versions used

From container image eicweb/eic_xl:nightly:

- EICrecon: v1.37.0-14-g195966d4
- JANA2: 2026.2.0
- ACTS install detected: acts-45.3.0
- EDM4eic install detected: edm4eic-git.7d7705d9...
- EDM4hep install detected: edm4hep-1.0

Local source inspection baseline (read-only):

- Local EICrecon checkout used for code inspection:
  - path: /Users/tkumaoka/eic/EICrecon
  - revision: 67a00864dd47c709c98b4afc2c210c3faee100b1
  - branch: timeframe_splitting_dev

Version comparison artifact:

- [seven_layer/results/eicrecon_revision_compare.txt](seven_layer/results/eicrecon_revision_compare.txt)

Compatibility note:

- Local source revision and Docker runtime revision differ.
- Runtime chain/debugging and all builds/tests in this phase were executed against the Docker-installed ABI (EICrecon v1.37.0-14-g195966d4 and ACTS 45.3.0).
- Local source was used strictly as read-only implementation reference.

## 3) Factory collection mapping attempted (Sim -> Raw -> Rec -> Measurement -> CKF)

Sim collections (input)

- SiMAPSHits
- MPGDHits
- ACLGADHits

Digitization and hit reconstruction reuse

- BVTX Si chain:
  - bvtx:sibarrelvertexrawhits:inputtags = EventHeader,SiMAPSHits
  - bvtx:sibarrelvertexrawhits:outputtags = SiMAPSRawHits,SiMAPSRawHitLinks,SiMAPSRawHitAssociations
  - bvtx:sibarrelvertexrechits:inputtags = SiMAPSRawHits
  - bvtx:sibarrelvertexrechits:outputtags = SiMAPSRecHits

- MPGD chain:
  - mpgd:mpgdbarrelrawhits:inputtags = EventHeader,MPGDHits
  - mpgd:mpgdbarrelrawhits:outputtags = MPGDRawHits,MPGDRawHitLinks,MPGDRawHitAssociations
  - mpgd:mpgdbarrelrechits:inputtags = MPGDRawHits
  - mpgd:mpgdbarrelrechits:outputtags = MPGDRecHits

- AC-LGAD temporary TOF-compatible chain:
  - btof:tofbarrelrawhits:inputtags = EventHeader,ACLGADHits
  - btof:tofbarrelrawhits:outputtags = ACLGADRawHits,ACLGADRawHitLinks,ACLGADRawHitAssociations
  - btof:tofbarrelrechits:inputtags = ACLGADRawHits
  - btof:tofbarrelrechits:outputtags = ACLGADRecHits

Revised architecture used now

- Keep EICrecon chain through reconstructed hits (Sim -> Raw -> Rec).
- Do not require EICrecon ACTS geometry conversion or EICrecon CKF chain for Phase 2 progress.
- Run standalone ACTS tracking application on RecHits:
  - input: SiMAPSRecHits from PODIO/EDM4eic
  - geometry: local five-plane ACTS telescope surfaces
  - fitter: ACTS KalmanFitter (existing ACTS implementation)

## 4) Segmentation implementation

Updated readouts in [seven_layer/geometry/seven_layer_telescope.xml](seven_layer/geometry/seven_layer_telescope.xml):

- SiMAPSHits: CartesianGridXY with 0.034641 mm x 0.034641 mm
- MPGDHits: CartesianGridXY with 0.519615 mm x 0.519615 mm (temporary simplified model)
- ACLGADHits: CartesianGridXY with x pitch 0.5 mm and very coarse y bin 100 mm to preserve 1D-strip-like intent
- Added x and y fields in CellID descriptor to satisfy Cartesian segmentation decoding

Additional compatibility adjustments applied:

- Readout bit allocation corrected to fit 64-bit CellID layout (avoid overflow)
- Endcap ring radius test was reverted back to 0 mm after introducing measurable position bias during validation
- Added DD4hep layer-pattern plugin metadata for custom detector components

## 5) Commands executed

Primary Phase 2 pipeline

- bash seven_layer/scripts/run_phase2_reconstruction.sh

Policy-compliant reproducible scripts added and used:

- Revision comparison:
  - bash seven_layer/scripts/check_eicrecon_revision.sh
- Stage A/B independent validation (no ACTS tracking plugin load):
  - bash seven_layer/scripts/run_phase2_stageAB_minimal.sh
- Stage C/D quick ACTS+CKF probe:
  - bash seven_layer/scripts/run_phase2_stageCD_quick.sh
- Standalone ACTS fit:
  - bash seven_layer/scripts/run_standalone_acts_fit.sh

Focused debug commands (executed)

- EICrecon with custom dd4hep XML and plugin ignores to isolate chain
- EICrecon with acts trace log level for geometry conversion diagnostics
- Config/factory extraction with eicrecon --configs and --list-factories

## 6) Verification results by milestone

Milestone A: SimTrackerHit -> RawTrackerHit

- Status: achieved in independent Stage A/B run
- Evidence:
  - [seven_layer/results/phase2_stageAB_summary.json](seven_layer/results/phase2_stageAB_summary.json)
- Example counts (80-event quick validation):
  - SiMAPS: sim 404 -> raw 404
  - MPGD: sim 94 -> raw 91
  - ACLGAD: sim 84 -> raw 83
- Raw-hit production uses existing EICrecon factories (BVTX/MPGD/BTOF), not Python copying.

Milestone B: RawTrackerHit -> TrackerHit

- Status: achieved in independent Stage A/B run
- Evidence:
  - [seven_layer/results/phase2_stageAB_summary.json](seven_layer/results/phase2_stageAB_summary.json)
- Example counts (80-event quick validation):
  - SiMAPS rec: 404
  - MPGD rec: 91
  - ACLGAD rec: 83
- Remaining quality caveat:
  - Rec-hit coordinates are not in the same frame as SimTrackerHit coordinates for all layers; direct residual interpretation required strict association and coordinate-frame checks.

Reconstructed-hit position validation (immediate-priority task)

- Added strict association-based validator:
  - [seven_layer/scripts/validate_rec_positions_assoc.py](seven_layer/scripts/validate_rec_positions_assoc.py)
- Output artifact:
  - [seven_layer/results/phase2_assoc_residuals_quick.json](seven_layer/results/phase2_assoc_residuals_quick.json)
- Key findings:
  - Matching quality is complete for SiMAPS (unmatched rec hits = 0, ambiguous raw links = 0).
  - The previous large systematic discrepancy was partly due to frame-mixing assumptions.
  - For SiMAPS, RecHit x means are approximately zero while SimHit x means drift with layer, indicating a coordinate-frame/placement interpretation mismatch that must be accounted for in validation and alignment.

Milestone C: DD4hep -> ACTS conversion and Measurement2D

- Status: failed
- Reproducible errors observed:
  - Unable to construct tracking geometry: no tracking volume
- Evidence:
  - [seven_layer/logs/phase2_stageCD_quick.log](seven_layer/logs/phase2_stageCD_quick.log)
  - [seven_layer/logs/phase2_eicrecon_trace.log](seven_layer/logs/phase2_eicrecon_trace.log)

Milestone D: ACTS CKF tracking

- Status in EICrecon CKF chain: failed (unchanged, blocked by ACTS geometry conversion inside EICrecon plugin path)

Milestone D-revised (standalone ACTS fit from RecHits)

- Status: achieved for first SiMAPS five-layer event
- Evidence:
  - [seven_layer/logs/standalone_acts_fit.log](seven_layer/logs/standalone_acts_fit.log)
- First successful fit line:
  - input_hits=5, fitted_tracks=1, nMeasurements=4, chi2=3.60006, ndf=8, chi2/ndf=0.450008, p_GeV=5
- Implementation notes:
  - zero magnetic field via Acts::ConstantBField(0,0,0)
  - multiple scattering and energy loss disabled for initial straight-track beam-test validation
  - RecHits used as measurements (no truth-position substitution)

Success criterion check

- Required (original full EICrecon chain): at least one verified EICrecon ACTS CKF track via Sim->Raw->Rec->Measurement->CKF
- Current result for original chain: not met
- Revised architecture immediate target: at least one standalone ACTS fitted track from five SiMAPS RecHits
- Current result for revised target: met

## 7) Current failures and root causes

1. ACTS tracking geometry conversion fails on custom geometry
- Error chain progresses from no volume builders to no tracking volume
- Indicates unresolved compatibility gap between custom seven-layer DD4hep structure and EICrecon ACTS geometry builder assumptions

2. TrackerHit position-context decoding errors remain in Stage A/B
- Repeated errors in BVTX/MPGD/BTOF rec-hit factories:
  - VolumeManager lookupContext failed for many generated cell IDs
- Effect:
  - Rec-hit counts are produced, but geometry lookup quality is inconsistent.
- Evidence:
  - [seven_layer/logs/phase2_stageAB.log](seven_layer/logs/phase2_stageAB.log)

3. SiliconTrackerDigi exceptions are observed when ACTS/tracking path fails early
- In ACTS-enabled runs, repeated SiliconTrackerDigi exceptions appear after tracking geometry failure
- In Stage A/B minimal run, raw hit production proceeds and file output is stable

4. Default plugin stack introduces broad detector expectations
- Even with plugin filtering, algorithms_init and default plugin wiring enforce dependencies that assume EPIC detector constants and subassemblies

## 8) Issues table (required items)

1. Missing readout segmentation in original geometry
- Status: addressed
- Evidence: segmentation and x/y CellID fields added in geometry file

2. DD4hep CellID-to-ACTS surface mapping
- Status: blocked
- Root cause: ACTS tracking geometry not constructed

3. Existing EICrecon hard-coded EPIC detector constants
- Status: observed as contributing factor
- Evidence: multiple plugin lookups for EPIC IDs reported in logs

4. JANA2 plugin/factory registration and collection names
- Status: partially addressed
- Remapping implemented, but chain still blocked upstream by tracking geometry construction

5. Beam-test-specific seeding and near-z-axis trajectories
- Status: prepared but untested in CKF due earlier blocker
- Note: local source confirms truth-seed split at 50 mrad in tracking plugin (central vs B0 split)

6. Zero magnetic field and ACTS covariance stability
- Status: unverified in CKF due earlier blocker

7. Simplified MPGD geometry currently using silicon material
- Status: known temporary simplification retained from Phase 1 portability constraints

8. AC-LGAD one-dimensional spatial measurement and deferred timing response
- Status: explicitly approximated for spatial chain preparation; timing still deferred

9. Correct position uncertainties and covariance propagation
- Status: partially addressed
- Stage A/B rec hits exist and standalone ACTS fit is operational; full uncertainty model validation and material model realism remain open.

10. Multiple SimTrackerHits per layer and potential secondary contamination
- Status: not fully analyzed in Phase 2 due missing stable reco output

11. Wide z-position distribution observed previously for SiMAPS layer 2
- Status: still open, not re-evaluated in successful phase2 reco output (none produced)

12. Compatibility with exact installed software versions
- Status: documented; compatibility issue remains with custom geometry and ACTS volume builder expectations

13. Reproducible Docker configuration and external files
- Status: documented; all commands executed in Docker; no host eic-shell modifications

14. Distinguishing simulation truth geometry vs reconstruction geometry
- Status: maintained conceptually; no alignment-geometry split implemented yet in this phase

## 9) Reused vs new code

Reused EICrecon components (attempted)

- BVTX SiliconTrackerDigi and TrackerHitReconstruction via bvtx factories
- MPGD digitization and hit reconstruction via mpgd factories
- BTOF raw/rec hit path for temporary AC-LGAD compatibility test
- (revised) tracking plugin chain is no longer required for immediate Phase 2 progression

Inspected local EICrecon source files (read-only)

- /Users/tkumaoka/eic/EICrecon/src/algorithms/tracking/ActsGeometryProvider.cc
- /Users/tkumaoka/eic/EICrecon/src/services/geometry/acts/ACTSGeo_service.cc
- /Users/tkumaoka/eic/EICrecon/src/global/tracking/tracking.cc
- /Users/tkumaoka/eic/EICrecon/src/algorithms/tracking/TrackerMeasurementFromHits.cc
- /Users/tkumaoka/eic/EICrecon/src/algorithms/digi/SiliconTrackerDigi.cc
- /Users/tkumaoka/eic/EICrecon/src/detectors/BVTX/BVTX.cc

What was copied and locally modified in OnlineTimeAlignmentTest

- New local scripts only (no copied C++ factory code yet):
  - [seven_layer/scripts/check_eicrecon_revision.sh](seven_layer/scripts/check_eicrecon_revision.sh)
  - [seven_layer/scripts/run_phase2_stageAB_minimal.sh](seven_layer/scripts/run_phase2_stageAB_minimal.sh)
  - [seven_layer/scripts/run_phase2_stageCD_quick.sh](seven_layer/scripts/run_phase2_stageCD_quick.sh)
  - [seven_layer/scripts/analyze_phase2_chain.py](seven_layer/scripts/analyze_phase2_chain.py)
  - [seven_layer/scripts/validate_rec_positions_assoc.py](seven_layer/scripts/validate_rec_positions_assoc.py)
  - [seven_layer/scripts/run_standalone_acts_fit.sh](seven_layer/scripts/run_standalone_acts_fit.sh)
- Geometry modifications only in:
  - [seven_layer/geometry/seven_layer_telescope.xml](seven_layer/geometry/seven_layer_telescope.xml)

New standalone ACTS code added under seven_layer

- [seven_layer/standalone_acts/CMakeLists.txt](seven_layer/standalone_acts/CMakeLists.txt)
- [seven_layer/standalone_acts/src/standalone_acts_fit.cpp](seven_layer/standalone_acts/src/standalone_acts_fit.cpp)

New local implementation

- Segmentation and metadata updates in custom geometry
- Phase 2 orchestration script and analyzer under seven_layer/scripts
- Phase 2 report and evidence collation under seven_layer/reports and seven_layer/logs

## 10) Narrowly scoped next step toward a working Phase 2 chain

1. Keep EICrecon for Sim->Raw->Rec only and iterate standalone ACTS app for fitting quality and seeding strategy.
2. Improve standalone fit output to process many events and produce aggregate metrics (efficiency, chi2/ndf distributions, per-layer residuals).
3. Add MPGD layer incrementally to standalone fit after SiMAPS-only baseline is stable.
4. Add AC-LGAD as 1D measurement (single constrained coordinate, realistic unconstrained counterpart handling).
5. Add export hooks for Millepede-II inputs: residual vectors, covariance blocks, local/global derivative matrices, and alignment parameter indexing.

## 11) Conclusion

Phase 2 implementation has been revised and partially achieved under the new architecture. EICrecon is successfully reused through reconstructed hits (Sim->Raw->Rec), reconstructed-hit discrepancy analysis now uses strict association matching, and the first standalone ACTS fitted track from five SiMAPS RecHits has been demonstrated reproducibly. The legacy EICrecon-internal ACTS/CKF chain remains blocked by custom-geometry conversion, but this no longer blocks immediate Phase 2 progression toward Millepede-compatible standalone tracking.
