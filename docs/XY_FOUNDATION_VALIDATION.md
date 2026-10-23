# Six-DOF Geometry Foundation and SiMAPS L1/L2 X/Y Validation

Validated locally on 2026-10-22. All new artifacts are under `result/xy_foundation_20261022_01/`; existing research outputs and installations were retained. No commit or push was performed.

## Implementation and changed files

The numerical ACTS Kalman fitter, beam configuration, uncertainties, material assumptions, particle hypothesis, Mille equations, parameter labels and official pede steering were preserved. The Geometry interface now provides the selected physical plane placement instead of fixed nominal centers.

| Area | Created or modified maintained files |
|---|---|
| Mathematical placement | New `geometry/transforms.py`; modified `geometry/placements.py` |
| DD4hep preparation | New `geometry/environment.py`, `geometry/scenarios/L1_L2_xy.json`, `geometry/scenarios/L1_L2_xy_reference.json`; modified `geometry/prepare.py`, `simulation/simulate.py` |
| Focused detector factory | New `localDetEICrecon/geometry/SiTrackerEndcap2XY_geo.cpp`, `DD4hep_LICENSE`; modified `localDetEICrecon/CMakeLists.txt` |
| Selected ACTS surfaces | New `localDetEICrecon/geometry/SurfacePlacements.h`; modified fitter `.cc`/`.h` and its factory header |
| Correction | Modified `correction/scope.py`, `correction/correct_geometry.py` |
| RawHit semantics | Modified `digitization/contract.py`, `digitization/digitize.py`, `reconstruction/runtime.py` |
| Existing Python controller | Modified `calibration/controller.py`, `iteration.py`, `settings.py`; new `calibration/config/l1_l2_xy_demo.json` |
| Validation | New `validation/test_transforms.py`, `test_raw_metadata.py`, `geometry_probe.py`, `validate_xy_derivatives.py`; modified `test_geometry_correction.py`, `check_safety.py`, `metrics.py`, `validate.py`, `run_closure.sh` |
| Source validation records | Advanced `validation/validated_sources.json` after regression; retained the original pin in new `validated_sources_history.json` |
| ROOT | Modified `visualization/closure.py` with additional Y Geometry/residual/correction views |
| Documentation | README, workflow, architecture, RawHit contract, calibration and validation guides; new `GEOMETRY_CONVENTIONS.md` and this report |

Earlier uncommitted profiles, reconstruction changes and user files remain. A source snapshot and initial Git status were saved before work. The electron-hypothesis and numerical fitting suffix of `BeamTestACTSFitter.cc` was compared byte-for-byte with that snapshot and is unchanged. Only surface initialization and the sensor-to-plane covariance permutation changed inside that source. The validated-source pin change records this deliberately validated source revision; it does not remove or relax any baseline data check.

## Transform and Geometry conventions

See [the detailed conventions](GEOMETRY_CONVENTIONS.md). The reusable rigid transform uses a proper right-handed rotation matrix R and translation t in mm: `p_parent = R p_child + t`. Angles supplied to axis constructors are radians. `A @ B` applies B first, with explicit parent/child frame checks. Inverse uses R transpose. Parent-frame corrections about pivot c are left-composed; sensor-local corrections are right-composed. Rotation matrices are composed, never added as Euler angles. Immutable tuple storage avoids aliasing caller-owned input arrays.

The mathematical foundation supports all six rigid-body degrees of freedom. XML/solver updates enable only `l2_x`, `l1_l2_x`, and `l1_l2_xy`. Z and all rotations remain disabled for alignment. No claim of six-DOF observability follows from the transform class.

The existing DD4hep Endcap2 builder maps the nominal SiMAPS sensor axes as sensor X → global Y, sensor Y → −global Z, sensor Z → −global X. The sensitive readout is CartesianGridXZ. This mapping was measured from the installed DD4hep VolumeManager, rather than inferred from axis names or Euler-angle arguments.

The focused factory is adapted from the [official DD4hep v01-36 builder](https://github.com/AIDASoft/DD4hep/blob/v01-36/DDDetectors/src/SiTrackerEndcap2_geo.cpp), with upstream notices/license retained. It adds only independent `global_y` to a ring's placement. It does not use phi to imitate Y motion; the sensor orientation and original materials, IDs and segmentation remain unchanged. The nominal XML is untouched. CMake builds its shared library and components map alongside BeamTestReco.

The ACTS adapter obtains actual sensitive contexts from the same DD4hep converter used for RecHits. It defines plane u = −sensor Z, v = sensor X, n = u×v, giving nominal global X/Y/Z axes. It uses actual sensitive centers and orientations. RecHit covariance is permuted from sensor X/Z to plane u/v; equal SiMAPS pitches make this numerically unchanged for the baseline. The adapter does not add material/process noise or replace DirectNavigator/Kalman fitting. Unsupported rotation corrections remain disabled even though the interface reads full orientation matrices.

## Readout, survey, selected Geometry and truth

These are separate concepts:

- **Readout/channel mapping:** segmentation, IDs, layer/module/sensor topology and units needed to decode RawHits.
- **Reference/survey G0:** explicit approximate fallback, with an independently recorded full checksum. It is not required to equal the unknown physical detector.
- **Reconstruction/alignment Geometry:** the immutable version selected for RecHits, ACTS and each dataset/iteration.
- **Simulation Truth Geometry:** optional provenance used outside inference for simulation closure.

RawHit v2 requires file checksum, readout and topology fingerprints, units, producer and conditions. It optionally records `simulation_truth_geometry_sha256`. Existing v1 remains accepted with its original `measured_geometry_sha256` meaning and checks; compatibility is restricted to the validated telescope topology. A v2 record cannot silently carry the legacy measured field. No old sidecar was rewritten. A v1-to-v2 migration must be explicit, preserve the original, identify topology, and identify simulation provenance only when actually known.

`calibration.measured_geometry` is optional and may be null or omitted. If supplied, it explicitly verifies legacy/known simulation provenance; it is never used to calculate corrections. The selected G0 and candidate hashes remain mandatory in queue/stage records. Fingerprint and RawHit structure validation were not removed.

XY correction composes all four residual updates with current placement. With `--reference-geometry`, fixed surveyed centers outside L1/L2 are preserved; changes during iteration must remain within the selected scope. Survey serialization currently retains the validated hierarchy, materials, readouts and unrotated single-module representation. It is not arbitrary DD4hep-layout support. Fixed anchor locations define the relative alignment gauge, not presumed physical truth.

## Controlled Simulation and full closure

The separate scenario is:

| Layer | Injected Global X | Injected Global Y |
|---|---:|---:|
| L1 | +0.150 mm | −0.120 mm |
| L2 | +0.200 mm | +0.090 mm |

The existing 100-event 1 GeV electron configuration, seed, angular distribution, X/Y vertex widths and z=−500 mm mean vertex were unchanged. A new Geant4 run was appropriate for this new Y scenario. DD4hep/GDML verified all seven actual centers before Simulation.

The maintained pipeline ran Simulation → Digitization → saved RawHits → Reconstruction → official pede → Geometry Correction → corrected Reconstruction → ROOT validation. There were 100 events, 502 SiMAPS RawHits/RecHits and **98 accepted tracks**, giving 98 Mille records / 980 scalar measurements. MPGD/AC-LGAD RawHit counts were 114/103; they were not included in the unchanged electron Track Fitting configuration.

| Component | Injected (μm) | First inferred correction (μm) | Pede nominal error (μm) |
|---|---:|---:|---:|
| L1 X, label 1001 | +150 | +150.58 | 1.2877 |
| L1 Y, label 2001 | −120 | −117.97 | 1.2877 |
| L2 X, label 1002 | +200 | +201.13 | 1.2372 |
| L2 Y, label 2002 | +90 | +91.021 | 1.2372 |

These are measured outcomes, not injected values used by the algorithm. The errors are the solver's model-dependent nominal errors, not proof of complete physics/systematic coverage.

| Quantity | Nominal reconstruction | After first correction | Exact final G2 reconstruction |
|---|---:|---:|---:|
| Tracks | 98 | 98 | 98 |
| ACTS chi2 / stored ndf | 57.93045679 | 1.20169752 | 1.20169902 |
| L1 pooled Rec − Sim X (μm) | −149.910354 | +0.669832 | +0.671970 |
| L2 pooled Rec − Sim X (μm) | −198.922108 | +2.207910 | +2.207865 |
| L1 pooled Rec − Sim Y (μm) | +118.566250 | +0.596141 | +0.592267 |
| L2 pooled Rec − Sim Y (μm) | −89.325268 | +1.695793 | +1.695793 |

The historical pooled residual definition was retained; unique event/layer pairs are used in the residual distributions. No uncertainty rescaling, seed tuning, altered physics settings or relaxed historical tolerances were used.

Pede completed with its existing accepted status **1: warnings (bad measurements)**. Its log identifies high reduced chi2: **1170.40544 / (588−6) = 2.01101**, with zero rejected tracks and no rank defect. This warning was not suppressed. ACTS stores 980 measurement dimensions; pede uses 588 straight-line local-fit degrees of freedom minus six fitted global parameters. Their chi2 numerators also differ slightly because the finite ACTS seed/Kalman treatment differs from independent straight-line fits. Neither stored-NDF ratios near one nor convergence establish a fully validated physical error model; material/process-noise limitations remain.

## Fixed-data iteration and Geometry chain

The controller used the same RawHit checksum every iteration and did not receive truth offsets as correction inputs. Its zero-displacement preparation scenario identifies the supported hierarchy/scope. Track-count, update and chi2 cuts remain the same configurable demonstration values.

| Update | L1 X (mm) | L1 Y (mm) | L2 X (mm) | L2 Y (mm) |
|---|---:|---:|---:|---:|
| G0 → G1 | +0.15058 | −0.11797 | +0.20113 | +0.091021 |
| G1 → G2 | +0.0000023112 | −0.0000037952 | −0.00000011202 | −0.000000002756 |

Both iterations used 98 tracks; all four remaining updates passed the provisional 0.005 mm tolerance in iteration two. Exact final XML positions, after the existing eight-decimal mm serialization, are **L1 (+0.15058231, −0.11797380) mm** and **L2 (+0.20112989, +0.09102100) mm**. Unselected placements were retained.

The nominal chain in `xy_state_v2` is:

- G0: `8807380ffdb277b747f052a0b2b451c87fbc4cb4ea08a3f6960f4e7b35defee4`
- G1: `b5202a83dad248478c34e7a53886e6b30a365ce3d23d7687807a43c1727c35a0`
- G2: `7601757397a06bc19a76c4a52e90a308f4f179a40f7e4043680890c263813d22`

Registry IDs prefix these hashes with `geo-`. G2 remains a **candidate**, not validated or active. Separate exact-G2 Reconstruction and Geometry probes passed. Training-sample MC closure is not independent scientific approval; activation still requires the existing explicit independent-review/approval commands.

## Derivative and geometry consistency validation

Mille writes `m_x = x0 + tx(z−zref) + a_x` and the analogous Y equation. Define residual `F = prediction + a − m_global`; the analytic partial derivative with respect to measurement bias a is +1. The physical placement correction is c=−a, so the corresponding physical-coordinate derivative is −1. This distinction avoids reversing the correction sign.

`validation/validate_xy_derivatives.py` reads actual derivative entries from the official Mille Binary (98 entries for each supported label). It creates ±0.001 mm bias perturbations as opposite physical Geometry translations, launches a fresh DD4hep process for every Geometry, recomputes global cell positions, and keeps local track parameters fixed. It covers L1/L2 X/Y, three signed channel-coordinate pairs and three slope/intercept sets: **36 checks**. Analytic and numerical derivatives agreed with maximum error **1.23e−12**, below the declared **1e−8** dimensionless tolerance; cross-coordinate derivatives were zero. Perturbations are 1 μm, residuals and alignment parameters are mm. This is an independent Geometry-based partial derivative, not a refit with stale hit positions.

Fresh DD4hep probes of both the one-update and exact final Geometry verified:

- All seven selected ACTS surface centers and orientations against sensitive contexts. Log center comparison uses 1e−6 mm because logs print six significant digits; basis comparison uses 1e−12.
- Every actual ACTS plane's local/global round trip and transform application within 1e−10 mm. JANA initialized the factory twice, so all 14 instances were checked rather than ignoring duplicates.
- All **502 RecHit positions exactly at stored float32 precision** against fresh CellIDPositionConverter results.
- All **490 fitted Measurement2D coordinates** against their selected plane's u/v frame, with a two-float32-ULP comparison allowance.

These checks validate the supported translation modes. They do not validate rotation derivatives, rotated-fit systematics, material descriptions or MPGD/AC-LGAD alignment.

## Survey-only, truth-excluded test

A separate approximate survey started L1 at (+0.040,−0.030) mm and L2 at (−0.020,+0.010) mm. The input contained the same simulated RawHit values, but all truth/digitization Geometry hashes and simulation source identifiers were excluded from its v2 metadata. The file contained only EventHeader and the three RawHit collections. It was explicitly labeled `simulation_test_without_truth`—not DAQ.

With only this survey, compatible readout/topology and data-driven cuts, `survey_state_v2` converged in two iterations. The first residual updates differed appropriately from the nominal-start updates, and composed with survey G0. The final Geometry had **the same G2 checksum** as the nominal-start calibration. Its active pointer remained the original survey fallback. A restart with the truth-Geometry configuration key omitted verified outputs and skipped the completed input. A stricter fixture additionally rebuilt fresh PODIO frames with only EventHeader/RawHit collections, excluded carried-through Simulation runs/metadata/meta frames and event-frame parameters, and verified the copied RawHit/EventHeader values exactly. Its ROOT file contains only events and required PODIO schema metadata. This fixture converged in two iterations to the identical G2 checksum without any truth-Geometry configuration key (`strict_survey_checks.json`); all RawHit/EventHeader branch values matched exactly.

The actual v2 RawHit contract passed; a changed segmentation pitch/readout was rejected. Saved v1 simulation RawHits also passed the final compatibility checks. No assumption of known physical placement was needed for inference. This does not validate a real DAQ decoder or real electronics calibration: the test remains simulation-backed with the prototype's documented energy-equivalent charge and ps encoding.

## Regression and mathematical tests

| Check | Executed result |
|---|---|
| Historical full L2 closure | 99 tracks, +198.75 μm; residual −199.571376 → −0.821365 μm; chi2/stored-ndf 45.592235 → 1.981040; existing reference passed |
| Saved L1/L2 X iteration | 98 tracks, two iterations; final +0.15058231/+0.20112989 mm; chi2/stored-ndf 37.060296 → 1.239162 |
| Combined versus split RawHits | Exact equality for 281 downstream branches, identical Mille bytes, identical pede parameters; 98 tracks |
| Mathematical/control/schema tests | 19 unit tests passed: identity, translations, X/Y/Z rotations, noncommutative composition, inverse/round trip, pivots, small angles, frame/rotation validity, immutable inputs, preserved anchors, metadata semantics and existing controller invariants |
| Gauge rank test | Unconstrained transverse translation system has two null modes per projection; fixed L0/L4 removes them |
| DD4hep actual placement | Seven nominal/misaligned GDML centers passed preparation checks; corrected/final contexts and ACTS checks passed |
| ROOT | Maintained Geometry/residual/closure objects plus Y views/graphs passed object checks |
| Preservation and safety | Existing scripts passed; 5,904 pre-existing protected checksums unchanged |
| Syntax and diff | Python compilation, shell syntax and `git diff --check` passed |

The full five-SiMAPS fit retains fixed L0/L4 and fitted L1–L3 X/Y steering. Only selected L1/L2 components are applied. Global translation and linear-in-z displacement modes are absorbed by free intercepts/slopes without anchors. Z and rotations introduce angular/impact-position sensitivities and weak modes; see the conventions document. No all-seven-layer or six-parameter fit is enabled.

The new local Measurement2D values are now relative to actual selected surface centers; corrected local coordinates therefore intentionally differ from the former nominal-centered representation. Historical global track quality/residual baselines remain equivalent, and nominal combined/split outputs remain exact. The original 5 GeV muon configuration/hypothesis path was preserved but not separately rerun in this phase.

## Build, commands and retained failures

The final tested build is `build/xy_foundation_20261022_02/`. ACTS is **45.3.0**, DD4hep **1.36**. `linkage.txt` verifies `/work/external/install/lib/libMille2.so` and the installed ACTS/DDRec libraries. No external source checkout or installation was edited.

The initial build began while adapter edits were still in progress, so a second fresh build tree was used for final validation. Its first compile found the incorrect JOmniFactory service-access syntax; installed headers established that `m_geometry()` is the correct accessor. The corrected build succeeded. Initial read-only probes failed because the local factory was not explicitly loaded in PyROOT and because the harness assumed one factory initialization; these were fixed without changing physics tolerances. A host-side configuration check using container-absolute `/work` paths failed as expected outside its environment and passed inside the container. All partial files and failure logs remain. No failed attempt was counted as passing.

Representative exact commands executed through the existing container wrapper:

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -c 'export TESTBENCH_BUILD_DIR=/work/build/xy_foundation_20261022_02; bash environment/build.sh > result/xy_foundation_20261022_01/build_clean_adapter.log 2>&1'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -c 'cmake --build build/xy_foundation_20261022_02 -j 2 > result/xy_foundation_20261022_01/build_adapter_fixed.log 2>&1'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/xy_foundation_20261022_01 python3 -m geometry.prepare --result-dir result/xy_foundation_20261022_01/xy --geometry-config geometry/scenarios/L1_L2_xy.json
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/xy_foundation_20261022_01 python3 -m simulation.simulate --result-dir result/xy_foundation_20261022_01/xy
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m digitization.digitize --result-dir result/xy_foundation_20261022_01/xy --build-dir build/xy_foundation_20261022_02
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m calibration.controller once --config result/xy_foundation_20261022_01/xy_config.json --input-dir result/xy_foundation_20261022_01/xy_input --state-dir result/xy_foundation_20261022_01/xy_state_v2
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m calibration.controller once --config result/xy_foundation_20261022_01/survey_config.json --input-dir result/xy_foundation_20261022_01/survey_input --state-dir result/xy_foundation_20261022_01/survey_state_v2
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/xy_foundation_20261022_02 python3 -m validation.validate_xy_derivatives --geometry result/xy_foundation_20261022_01/xy/step1/misaligned.xml --mille result/xy_foundation_20261022_01/xy/step3/mille.dat --output result/xy_foundation_20261022_01/derivatives
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash validation/run_closure.sh --result-dir result/xy_foundation_20261022_01/l2_regression --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root --build-dir build/xy_foundation_20261022_02 --reference validation/reference_metrics.json
```

Preparation/Simulation used the first tree's identical Geometry-factory source; all tracking validation used the final second-tree Plugin. `run_xy.py`, `regressions.py`, `survey_test.py`, `final_candidate.py`, `strict_survey_test.py` and `check_metadata.py` under the new result directory retain the integration harnesses. Stage `command.json`, `stdout.log`, `exit.json`, `complete.json`, queue journals, derivative reports and fresh-process probe files preserve exact subprocess evidence. These local harnesses are validation artifacts, not additional maintained framework entry points, and must not overwrite their existing outputs.

Public reproduction uses a new result directory:

```sh
bash environment/run.sh bash environment/build.sh
bash environment/run.sh bash validation/run_closure.sh --result-dir result/NEW_XY --geometry-config geometry/scenarios/L1_L2_xy.json --correction-mode l1_l2_xy
python3 -m unittest validation.test_transforms validation.test_raw_metadata validation.test_geometry_correction validation.test_calibration_controller
```

For fixed-RawHit survey calibration use the [existing controller commands](../calibration/README.md) with `calibration/config/l1_l2_xy_demo.json` as a disabled-until-configured template. Once/watch, atomic readiness, deterministic queueing, locking, retries, immutable versions and explicit review/activation remain the same implementation. No new controller or scheduler was introduced.

The standard DD4hep-to-ACTS TrackingGeometry conversion issue is not solved or suppressed by this work. The local fitter still uses DirectNavigator, now with sensitive-context-derived surfaces. Rotation/Z derivatives, arbitrary detector backends, material/process-noise refinement, real DAQ decoding, six-DOF/all-seven-layer observability, independent experimental validation and automatic activation remain future work.
