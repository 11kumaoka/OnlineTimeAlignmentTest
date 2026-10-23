# Source-based architecture and workflow guide

Current Geometry reconstruction uses the original local surface path.
The optional Blueprint implementation and `--geometry-provider` selector were
removed after checkpoint `020a29d81173097f2a0f03b8d08020e70eefb5a3`. The guide
at that commit and the retained integration audits document the previous tested
experiment; they are not current provider instructions. See
[LEGACY_ENDCAP_SIMPLIFICATION.md](LEGACY_ENDCAP_SIMPLIFICATION.md) for the
source-grounded failure diagnosis, tested commands and new regression evidence.
No substitute provider or tracking/alignment expansion was added.

## Maintained directory map

| Path | Responsibility, inputs and outputs |
|---|---|
| `environment/` | `run.sh` launches the pinned Docker environment; `build.sh` configures/builds the Plugin; `dependencies.json` pins Mille/Pede; installer is for absent dependencies only. |
| `localDetEICrecon/` | C++ Plugin, copied/adapted EICrecon hit factories/algorithms, local ACTS fitter, processors, official-Mille writer adapter and Geometry factory. `CMakeLists.txt` builds BeamTestReco.so and libLocalTelescopeGeometry.so. Optional `TESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE` builds only a diagnostic executable. |
| `geometry/` | Immutable nominal XML, scenario JSONs, `prepare.py`, placement and SO(3) transform helpers. Nominal + scenario → exclusive step1 XML/GDML/QA. |
| `simulation/` | `simulate.py`/wrapper; beam/events/seed JSON + physical XML → step2 EDM4hep events. `--sim-input` reuses saved data instead of Geant4. |
| `digitization/` | `digitize.py`, `contract.py`, wrapper; Simulation + readout → step2_digitization RawHit-only ROOT and v2 checksum/provenance/units/topology contract. |
| `reconstruction/` | `reconstruct.py`, before/after wrappers, `runtime.py`, particle-setting JSONs; RawHits + contract + selected XML → step3 or step6 reco.root and mille.dat. |
| `alignment/` | `align.py`, wrapper and canonical mode-specific steering; Mille → official Pede output/log/end status under step4. The writer is in the C++ Plugin. |
| `correction/` | `correct_geometry.py`, `scope.py`, wrapper; Pede + current/reference XML + explicit signed scope → inactive step5/corrected.xml. |
| `validation/` | Historical reference/preservation manifests, unit/derivative/information/Geometry diagnostics, `run_regression.sh`, `run_closure.sh`, `validate.py` and metrics. Standard closure produces step7 summary and invokes ROOT rendering. |
| `visualization/` | ROOT-only closure/tilt/Z/Rz plots and browse.C; explicit fit/Geometry/validation inputs → ROOT canvases/histograms/graphs and PDFs. |
| `calibration/` | Python Controller, independent-stage runner, input monitor/queue, immutable Geometry manager, strict source/binary policy and convergence checks; sequential RawHit delivery → attempts/candidates/reports. |
| `input/` | Delivery protocol README is tracked; incoming RawHits/sidecars are ignored local data. |
| `docs/` | Current guides plus explicitly historical audits and research records. |
| `external/` | Ignored dependency sources/builds/installations; external/install remains the dependency prefix. |
| `build/` | Ignored generated Plugin/probe executables, libraries, CMake caches and link records; fresh directories avoid stale caches. |
| `result/`, `results/` | Ignored new runs/Controller states/evidence and protected historical/reference data respectively. Never overwrite successful or failed runs. |
| `research_common.py` | Infrastructure only: paths, exclusive stages, hashes, completion checks, command logs and dependency validation. |
| `README.md`, `.gitignore`, `.gitattributes` | Maintained project entry and tracking policy; ROOT/Mille/logs, dependencies, builds, archives and caches remain local. |

## Independent workflow and configuration ownership

1. `environment/run.sh` enters the existing fixed Docker environment. Build via
   `environment/build.sh` (also delegated to by localDetEICrecon/build.sh).
2. `geometry.prepare.prepare/write_shifted_xml/verify_positions` reads unchanged
   nominal plus scenario; writes step1 nominal/misaligned XML and placement QA.
3. `simulation.simulate.simulate` snapshots beam/events/seed JSON and generates
   or imports step2/events.edm4hep.root using step1/misaligned.xml.
4. `digitization.digitize` invokes BeamTestReco `profile=digitization`:
   `LocalSiliconTrackerDigi_factory` → `SiliconTrackerDigi::process`. Only
   EventHeader and RawHits are persisted with the v2 contract.
5. `reconstruction.reconstruct` uses `profile=raw`:
   `LocalTrackerHitReconstructionNoAssoc_factory` →
   `TrackerHitReconstruction::process` → `BeamTestACTSFitter_factory` and fitter.
   Particle settings belong to reconstruction/configs/*.json; default electron
   configuration selects PDG 11, q/p=-1, no MPGD/AC-LGAD fit measurements.
6. `BeamTestMilleProcessor::Process` follows Track→Measurement→RecHit relations,
   selects exactly one hit per SiMAPS L0–L4 and calls
   `BeamTestMilleWriter::writeTrackRecord`; Mille is a reconstruction output.
7. `alignment.align.align` expands selected canonical steering and runs
   external/install/bin/pede. Inspect process exit and millepede.end separately.
8. `correction.correct_geometry.correct/correct_so3` applies the supported signed
   parameters to current Geometry; step5 is an inactive immutable candidate.
9. `reconstruction.reconstruct --after` uses the same step3 RawHit source and
   saved settings with step5 XML, producing step6. It does not redigitize.
10. `validation.validate`/metrics and `visualization.closure` support the stated
    standard closure modes. Coupled SO(3) manual runs use the separate
    tilt_observability and tilt_alignment interfaces; do not invent a generic
    six-DOF validate option.
11. Optional `calibration.controller` calls these independent stages sequentially
    through `iteration.py`. Matching derivative/source/binary evidence, rank,
    policy and immutable parent-chain checks remain. Review and activation are
    explicit separate actions, not automatic iteration consequences.

Existing RawHit imports skip Simulation/Digitization. With explicit
`--raw-input FILE --raw-metadata CONTRACT --geometry XML`, reconstruction does
not require step1. Correction still needs nominal/scenario/reference provenance.
The contract may contain Simulation hash provenance; it supplies no Truth
position or correction. Inference uses RawHits/current Geometry only.

Each module is callable via `python3 -m`; shell wrappers delegate to it.
`research_common.stage` refuses existing output stages and `require` verifies
completion/output hashes. Old Controller state cannot silently resume after
implementation/configuration fingerprints change.

## Actual Geometry → fitter path

```text
DD4hep_service(selected XML)
  → DDRec CellIDPositionConverter sensitive contexts
  → geometry/SurfacePlacements.h::surfacePlacements (seven fixed layer slots)
  → BeamTestACTSFitter_factory::Configure → setPlacements
  → BeamTestACTSFitter::init (manual PlaneSurfaces, bounds and IDs)
  → fitSelected: Global RecHit → local measurement/covariance → FitSourceLink
  → EigenStepper + ConstantBField(0) + DirectNavigator + ACTS KalmanFitter
```

The local axes are u=-sensor Z, v=sensor X, n=u cross v; units are ACTS mm.
Sensitive positions/orientations come from the selected DD4hep placement.
Telescope-specific parts remain: system IDs 31/100/92, layer-field decoding,
seven slots, 50 mm half bounds, ordered fitting, SiMAPS sensor-X/Z covariance
permutation and five-plane Mille selection. GeometryContext is static for one
immutable XML/process. No ACTS material/process-noise model was added; DD4hep
physical thickness alone is not such a model.

The fitter's map is GeometryIdentifier→Surface plus source-index→layer/hit
association, not the official provider's Volume-ID SurfaceMap. The local path
does not consume a closed TrackingGeometry. The standard acts plugin can still
be registered by the workflow; its legacy initialization error was not hidden
or converted into a successful local Geometry result.

The retained official diagnostic instead invokes installed
ActsGeometryProvider::initialize → convertDD4hepDetector →
TrackingGeometryBuilder/CylinderVolumeBuilder → DD4hepLayerBuilder/LayerCreator.
On success the official provider would close IDs and visit DD4hep-backed surfaces
to map VolumeManager sensitive Volume IDs to Surfaces. The private singleton
experiment fails before that point. Consequently no successful new official
SurfaceMap, TrackingGeometry, Navigation or reconstruction integration is claimed.
Individual official surface conversion remains independently testable.

## Official components and local model

- Copied/adapted EICrecon sources retain provenance comments at revision
  67a00864…; installed services/provider interfaces are at 195966d4…. JANA2,
  DD4hep, PODIO/EDM and ACTS numerical libraries are reused unchanged.
- The local fitter wiring is independent, with official KalmanFitter/Stepper/
  DirectNavigator components. It is not the official EICrecon CKF chain.
- `BeamTestMilleWriter` is an independent four-local-parameter straight-line
  model, using the official Mille library. It does not serialize ACTS Kalman
  derivatives. Local indices are x0,y0,tx,ty at zref=100 mm; each accepted track
  writes ten scalar measurements followed by one writeRecord boundary.
- Legacy rows store measured x/y, sigma and line derivatives. Coupled rows use
  `TiltMeasurementModel.h` covariance Jacobian/Cholesky whitening with frozen
  profiled reference slopes, then write whitened measurements/derivatives and
  scalar sigma=1. Processor sigmas come from RecHit errors with the existing
  floor. No Truth residual is used for inference.
- Label families 1000/2000/3000+layer represent X/Y/Rz biases with physical
  correction sign minus; 4000/5000/6000 represent Z/Rx/Ry with sign plus. Units
  are mm/rad. `scope.py` and canonical steering define fixed reference layers;
  the three-layer mode fixes L0/L4. Legacy nuisance labels must not be changed
  merely to match the applied correction scope.
- SO(3) state uses matrices, Rnew=Exp(delta)Rcurrent about the current sensitive
  center, followed by Global translation. Pede/Controller remain independent
  of Blueprint or any new Geometry provider.

Existing L1/L2 nominal-uncertainty limitations, three-layer prototype status,
large-offset rejection and the prior nonconverged Controller pilot remain.
Old fixed-Global two-axis modes are disabled. MPGD/AC-LGAD alignment and full
ePIC tracking/material support are unvalidated, regardless of surface counts.

## Commands and evidence

[LEGACY_ENDCAP_SIMPLIFICATION.md](LEGACY_ENDCAP_SIMPLIFICATION.md) gives tested,
independent CHECK-ONLY/WRITES OUTPUT commands and exact failure locations.
[WORKFLOW.md](WORKFLOW.md) retains the independent standard stage commands;
[L3_SIX_DOF_MANUAL.md](L3_SIX_DOF_MANUAL.md) explains the explicit technical
six-DOF gates. Current reconstruction has no `--geometry-provider` option.
Do not run historical Blueprint commands against current sources; use the
preserved commit/build/results if reviewing that earlier experiment.

The next minimum step is upstream-compatible layer-frame/envelope/optional-
boundary fixes followed by real volume/navigation validation, not another
substitute provider. Keep the working manual planes until those gates pass.
Any future interface commonality should follow the official sensitive Volume
ID→Surface and measurement/SourceLink conventions without changing the numerical
fitter or alignment model merely to bypass Geometry failures.
