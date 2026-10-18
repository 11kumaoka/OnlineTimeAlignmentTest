# Full Chain Code Audit

Date: 2026-10-16
Scope: seven_layer local framework, integrated JANA2/ACTS/Mille pipeline

## 1. Source inventory summary

Primary implementation areas audited:

- Geometry and readout:
  - seven_layer/geometry/seven_layer_telescope.xml
- Local reconstruction plugin:
  - seven_layer/local_eicrecon/algorithms/**
  - seven_layer/local_eicrecon/factories/**
  - seven_layer/local_eicrecon/processors/**
  - seven_layer/local_eicrecon/plugins/BeamTestReco.cc
- Mille integration:
  - seven_layer/millepede/src/**
  - seven_layer/millepede/scripts/**
  - seven_layer/millepede/config/**
- Reports and validation artifacts:
  - seven_layer/reports/**
  - seven_layer/logs/**
  - seven_layer/results/**

## 2. Findings and actions

### P0 (physics/data integrity/runtime critical)

P0-1: Ambiguous hit selection bias in ACTS fitter

- Location:
  - seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.cc
- Previous behavior:
  - representative hit selected by min(abs(x)) in each layer
- Expected:
  - no arbitrary x-axis bias in track/hit selection
- Consequence:
  - potential systematic bias in track fit and Mille inputs
- Fix applied:
  - strict unambiguous layer policy: require exactly one candidate per required layer; otherwise skip event with explicit diagnostic
- Verification:
  - fit_skip diagnostics appear for ambiguous events
  - integrated run still produces valid tracks/records
- Status: RESOLVED

P0-2: Truth-independent reconstruction path integrity when associations are absent

- Location:
  - seven_layer/local_eicrecon/factories/tracking/TrackerHitReconstructionNoAssoc_factory.h
  - seven_layer/local_eicrecon/plugins/BeamTestReco.cc
- Previous behavior:
  - normal and truthdiag shared association-dependent factory path
  - optional-association experiments triggered instability/unreliable behavior
- Expected:
  - normal mode must not require association input
- Consequence:
  - data-like runs without associations could fail or behave ambiguously
- Fix applied:
  - introduced dedicated no-association normal factory (raw hits only)
  - retained association-based factory only for truth diagnostic outputs
- Verification:
  - normal-mode no-association run succeeds and writes rec hits/tracks
  - truthdiag missing-association output fails explicitly and is omitted by PODIO
- Status: RESOLVED

P0-3: Integrated scripts failing due shell variable scope under set -u

- Location:
  - seven_layer/millepede/scripts/run_integrated_mille_baseline.sh
  - seven_layer/millepede/scripts/run_integrated_mille_injected.sh
- Previous behavior:
  - unbound variable failures in container shell
- Expected:
  - reproducible script execution
- Consequence:
  - workflow breaks and can mask physics regressions
- Fix applied:
  - explicit in-container paths and env passing for injected script vars
- Verification:
  - scripts execute end-to-end and regenerate baseline/injected artifacts
- Status: RESOLVED

### P1 (important algorithmic/architectural)

P1-1: Provenance coverage incomplete on some derived headers

- Location:
  - SiliconTrackerDigi.h/config
  - TrackerHitReconstruction.h/config
- Fix applied:
  - added origin/revision/local-purpose/adaptation comments preserving SPDX headers
- Status: RESOLVED

P1-2: Clear separation of normal and truthdiag reconstruction modes

- Location:
  - BeamTestReco plugin factory wiring
  - TrackerHitReconstruction processing
- Fix applied:
  - default rec collections now use no-association normal factory
  - truthdiag remains opt-in via beamtstreco:enabletruthdiagnosticrechits
  - explicit failure message path retained for truthdiag association requirements
- Status: RESOLVED

P1-3: MPGD/AC-LGAD detector realism

- Location:
  - local_eicrecon digi/reco chain and plugin registration
- Current behavior:
  - provisional silicon-derived approximations
- Consequence:
  - not yet representative of detector-specific response for real data
- Action now:
  - retained modular architecture and explicit documentation; no risky rewrite in this audit phase
- Status: OPEN (documented limitation)

P1-4: ACTS EDM4eic semantics parity with upstream ActsToTracks

- Location:
  - BeamTestACTSFitter output conversion code
- Current behavior:
  - local conversion works for current validation but remains custom
- Action now:
  - kept stable validated path; documented as follow-up area for deeper parity tightening
- Status: OPEN (documented follow-up)

### P2 (maintainability/documentation/cleanup)

P2-1: Distinct report structure and reproducibility commands

- Actions:
  - added/upgraded scripts for baseline/injected/pede/summary
  - produced dedicated audit/comparison/validation reports
- Status: RESOLVED

P2-2: Existing logs include unrelated default-plugin warnings for custom geometry

- Action:
  - retained known behavior; scoped validation commands around local chain outputs
- Status: OPEN (non-blocking)

## 3. Verification matrix (post-fix)

- Build local plugin with Mille enabled: PASS
- Normal no-association reconstruction test: PASS
- Truthdiag missing-association explicit failure (output omission): PASS
- Integrated baseline Mille generation and solve: PASS
- Integrated injected +0.2 mm closure recovery: PASS

## 4. Risks remaining

1. MPGD/AC-LGAD response realism remains provisional.
2. Full upstream ACTS conversion parity is not complete; local fitter remains telescope-specific by design.
3. Running full default ePIC plugin set on custom seven-layer geometry still produces many unrelated subsystem warnings/errors.

## 5. Conclusion

Audit-stage acceptance criteria for this phase are met for the SiMAPS-centered alignment pipeline:

- critical selection bias removed
- truth-independent normal reconstruction path hardened
- real Millepede-II baseline and injected closure still pass after corrections
- provenance and upstream comparison documentation significantly improved

No alignment-constant application back into geometry/reconstruction was performed in this stage.
