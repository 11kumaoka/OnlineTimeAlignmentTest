# Full Chain Validation Report

Date: 2026-10-16

## Environment

Workspace: /Users/tkumaoka/eic/OnlineTimeAlignmentTest/seven_layer

Runtime container: eicweb/eic_xl:nightly

Versions:

- EICrecon v1.37.0-14-g195966d4
- JANA 2026.2.0
- ACTS 45.3.0
- DD4hep 1.36
- PODIO 1.7
- EDM4hep 1.0
- EDM4eic git.7d7705d9...
- Millepede-II 05.01.06 (local build)

## V1 — Build and plugin loading

Command:

- cmake configure/build for local_eicrecon with Mille enabled

Evidence:

- build log: seven_layer/logs/local_eicrecon_build_audit.log
- target: BeamTestReco.so built successfully

Result: PASS

## V2 — Truth-independent SiMAPS reconstruction

Command:

- Integrated run baseline script
- no-association-normal test command with:
  - beamtestreco:localsimapsrechits:inputtags=LocalSiMAPSRawHits

Evidence:

- normal mode execution lines in log:
  - TrackerHitReconstruction mode=normal for SiMAPS/MPGD/ACLGAD
- finish counters for no-association test:
  - events=5, simaps(raw/rec)=25/25

Logs:

- seven_layer/logs/local_eicrecon_runtime_mille_integrated.log
- seven_layer/logs/local_eicrecon_runtime_missingassoc_normal_minimal.log

Result: PASS

## V3 — Coordinate and layer consistency

Checks:

- SiMAPS readout uses CartesianGridXZ with x/z segmented fields in geometry
- layer decoding in local code uses layer bits [11..16)
- reconstructed hit positions and covariances remain finite and non-zero

Evidence files:

- seven_layer/geometry/seven_layer_telescope.xml
- seven_layer/results/local_simaps_reco_normal_recofix.root
- seven_layer/reports/jana2_integrated_acts_report.md

Result: PASS

## V4 — Integrated ACTS tracking

Command:

- integrated baseline script

Evidence:

- tracks produced
- event processor finish summary with track/trajectory counts

Log:

- seven_layer/logs/local_eicrecon_runtime_mille_integrated.log

Result: PASS

## V5 — Hit association integrity

Change validated:

- removed min-abs(x) representative selection
- strict unambiguous-per-layer selection with explicit skip diagnostics

Evidence:

- fit_skip messages for ambiguous events/layers
- reduced accepted events in integrated run reflects explicit ambiguity rejection

Logs:

- seven_layer/logs/local_eicrecon_runtime_mille_integrated.log
- seven_layer/logs/local_eicrecon_runtime_mille_integrated_milleInjL2x0.2.log

Representative counts (post-audit run):

- events=80
- accepted=68
- no_track=12
- records=68
- measurements=680

Result: PASS

## V6 — Millepede-II toy closure

Command:

- seven_layer/millepede/scripts/run_toy_closure.sh

Evidence:

- injected +0.200 mm (L2 x) recovered ~ +0.19976 mm
- injected -0.200 mm (L2 x) recovered ~ -0.20024 mm
- injected +0.150 mm (L2 y) recovered ~ +0.15009 mm

Artifacts:

- seven_layer/millepede/results/toy
- seven_layer/logs/mille_toy_closure.log

Result: PASS

## V7 — Integrated Mille baseline

Commands:

- seven_layer/millepede/scripts/run_integrated_mille_baseline.sh
- seven_layer/millepede/scripts/run_pede_from_dat.sh ... integrated_postaudit_base

Artifacts:

- DAT: seven_layer/millepede/results/integrated/local_beamtest_mille_integrated.dat
- ROOT: seven_layer/results/local_simaps_reco_mille_integrated.root
- RES: seven_layer/millepede/results/integrated/integrated_postaudit_base_millepede.res

Solver status:

- no rank defect reported

Result: PASS

## V8 — Mille measurement-shift closure

Commands:

- INJ_LAYER=2 INJ_X_MM=0.2 INJ_Y_MM=0.0 seven_layer/millepede/scripts/run_integrated_mille_injected.sh
- seven_layer/millepede/scripts/run_pede_from_dat.sh ... integrated_postaudit_inj
- summarize script against baseline

Result summary:

- label 1002 (L2 x bias):
  - baseline: -7.6413e-4 mm
  - injected: +1.9924e-1 mm
  - delta: +2.0000413e-1 mm
- other active labels remain unchanged within precision in this test.

Artifacts:

- seven_layer/millepede/results/integrated/integrated_postaudit_base_millepede.res
- seven_layer/millepede/results/integrated/integrated_postaudit_inj_millepede.res

Result: PASS

## V9 — Robustness checks

1. Missing associations in normal mode:
- local SiMAPS rec configured with raw-hit-only input tag
- run succeeds and produces rec hits/tracks for tested events
- PASS

2. Missing associations in truth-diagnostic mode:
- truthdiag SiMAPS input set to missing association tag
- PODIO reports omission of LocalSiMAPSRecHitsTruthDiag due to missing collection
- run completes for normal outputs; truthdiag output fails explicitly
- PASS (expected explicit failure)

3. Repeatability:
- repeated baseline/injected integrated runs reproduce closure behavior and sign
- PASS

## Known limitations

1. Full ePIC default plugin stack on seven-layer custom geometry still emits many unrelated subsystem warnings/errors unless plugins are ignored.
2. MPGD and AC-LGAD chains are still provisional silicon-derived approximations for this phase.
3. ACTS NDF accounting differs from classical straight-line residual-DOF counting; both are tracked separately in logs.

## Readiness for applying alignment corrections

Status: READY FOR NEXT PHASE

Rationale:

- P0 items found in this stage were addressed or isolated.
- Integrated baseline and injected closure with real Millepede-II remain successful after code corrections.
- Truth-independent normal reconstruction remains functional and explicit truth-diagnostic behavior is separated.
