# Upstream EICrecon Comparison

Date: 2026-10-16

## 1. Reference and runtime versions

Reference checkout (read-only target):

- Repo: /Users/tkumaoka/eic/EICrecon
- Branch: timeframe_splitting_dev
- Revision: 67a00864dd47
- Note: checkout has unrelated local modifications and untracked files; this audit did not modify that repository.

Runtime inside Docker (eicweb/eic_xl:nightly):

- EICrecon: v1.37.0-14-g195966d4
- JANA: 2026.2.0
- ACTS: 45.3.0
- DD4hep: 1.36
- PODIO: 1.7
- EDM4hep: 1.0
- EDM4eic: git.7d7705d9...

Key mismatch:

- Local reference checkout revision (67a00864dd47) is not the same as runtime EICrecon revision (195966d4).
- Therefore, exact behavior parity with installed runtime cannot be assumed; local copied sources are tracked to the explicit reference revision where identified.

## 2. File-by-file comparison map

| Local file | Upstream source | Classification | Significant local differences | Reason |
|---|---|---|---|---|
| seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigi.cc | src/algorithms/digi/SiliconTrackerDigi.cc @ 67a00864dd47 | copied+modified | local namespace/plugin wiring; execution diagnostics | keep editable local chain |
| seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigi.h | src/algorithms/digi/SiliconTrackerDigi.h @ 67a00864dd47 | copied+modified | local namespace | symbol isolation |
| seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigiConfig.h | src/algorithms/digi/SiliconTrackerDigiConfig.h @ 67a00864dd47 | copied+modified | local thresholds/time settings by subdetector | telescope tuning |
| seven_layer/local_eicrecon/factories/digi/SiliconTrackerDigi_factory.h | src/factories/digi/SiliconTrackerDigi_factory.h @ 67a00864dd47 | copied+modified | local factory type names and plugin integration | local plugin architecture |
| seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.cc | src/algorithms/tracking/TrackerHitReconstruction.cc @ 67a00864dd47 | copied+modified | explicit truth-diagnostic branch; normal mode independent of truth; runtime mode logging | preserve data validity and debug mode separation |
| seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.h | src/algorithms/tracking/TrackerHitReconstruction.h @ 67a00864dd47 | copied+modified | local namespace; diagnostic config path | local integration |
| seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstructionConfig.h | src/algorithms/tracking/TrackerHitReconstructionConfig.h @ 67a00864dd47 | copied+modified | adds useTruthPositionForDiagnostics (default false) | explicit mode separation |
| seven_layer/local_eicrecon/factories/tracking/TrackerHitReconstruction_factory.h | src/factories/tracking/TrackerHitReconstruction_factory.h @ 67a00864dd47 | copied+modified | kept association-based path for truth-diagnostic factories | preserve explicit diagnostics |
| seven_layer/local_eicrecon/factories/tracking/TrackerHitReconstructionNoAssoc_factory.h | none (local) | independently implemented | raw-hit-only normal reconstruction path | data-like operation without associations |
| seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.cc | refactored from seven_layer/standalone_acts/src/standalone_acts_fit.cpp (local) | independently implemented (EICrecon-inspired) | in-process fitter, fixed telescope surfaces, EDM4eic outputs, exclusion and test-shift controls, strict ambiguous-hit rejection | telescope-specific geometry/tracking scope |
| seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.h | local refactor source | independently implemented | same as above | same |
| seven_layer/local_eicrecon/factories/tracking/BeamTestACTSFitter_factory.h | none direct; similar concept to CKFTracking_factory/ActsToTracks_factory | independently implemented | single algorithm/factory for local telescope tracks | compact local architecture |
| seven_layer/local_eicrecon/plugins/BeamTestReco.cc | src/detectors/BVTX/BVTX.cc style at 67a00864dd47 | adapted | local detector chain registration; optional truthdiag outputs; Mille processor registration | maintain one-process telescope chain |
| seven_layer/local_eicrecon/processors/BeamTestEventProcessor.* | none | local extension | event-level counters and diagnostics | local QA |
| seven_layer/local_eicrecon/processors/BeamTestMilleProcessor.* | none | local extension | in-process Mille record generation from rec hits + tracks | required for integrated Mille workflow |
| seven_layer/millepede/src/BeamTestMilleWriter.* | official Mille API | local wrapper around official API | label mapping and derivative model for 5-plane straight-line alignment | explicit project alignment model |

## 3. Relevant upstream algorithms reviewed

Reviewed upstream candidate reuse paths in reference checkout:

- src/algorithms/digi/MPGDTrackerDigi.cc
- src/algorithms/tracking/MPGDHitReconstruction.cc
- src/algorithms/tracking/LGADHitClustering.cc
- src/algorithms/tracking/TrackerMeasurementFromHits.cc
- src/algorithms/tracking/TrackSeeding.cc
- src/algorithms/tracking/CKFTracking.cc
- src/algorithms/tracking/ActsToTracks.cc
- corresponding factory headers under src/factories

## 4. Why local telescope-specific code remains

1. Geometry/service assumptions:
- Upstream detector plugins assume ePIC subsystem IDs and detector inventory that are absent in the custom seven-layer compact geometry.

2. Tracking scope:
- For this beam-test telescope, straight-track ACTS fitting with fixed known layer surfaces is currently the validated path; upstream full seeding/CKF chain is heavier and geometry-assumption sensitive.

3. Editable local iteration:
- Project requirements prefer locally compiled editable algorithms/factories instead of opaque prebuilt detector plugins.

## 5. Reuse opportunities and current decisions

1. Silicon digitization and tracker-hit reconstruction:
- Reuse maintained via copied-and-tracked upstream sources.

2. ACTS-to-EDM conversion semantics:
- Local BeamTestACTSFitter should continue borrowing conventions from ActsToTracks for covariance/parameter semantics; current report identifies this as a P1 area for continued tightening.

3. MPGD and AC-LGAD:
- Current chain still uses silicon-derived approximation for first-pass integration; upstream detector-specific implementations are identified for staged adoption.

## 6. Source provenance status

Provenance comments are now present at the top of EICrecon-derived local source files and local custom files, including:

- origin path
- source revision where identifiable
- local purpose
- important adaptation notes

No provenance claims were invented where source revision was not directly identifiable.
