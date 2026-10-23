# Global sensor tilt alignment: scientific checkpoint

Completed locally on 2026-10-22 using the existing EIC container `sweet_mahavira`. All artifacts, failed attempts and exact commands are retained in `result/tilt_alignment_20261022_01/`. Final fresh build: `build/tilt_alignment_20261022_05/`. No commit, push, automatic Geometry activation, historical-data replacement or external-installation modification was performed.

## Outcome and scientific stop

| Milestone | Outcome |
|---|---|
| A: L1 Global Rx | Controlled validation passed; 100 events plus one justified independent 1,000-event cross-check |
| B: L1 Global Ry | Controlled positive/negative 100-event validation passed |
| C: L1 Rx/Ry, then L1/L2 Rx/Ry | Tested; finite-rotation scientific closure failed. Public entry points are disabled |
| D: combined six-DOF inference | Not enabled or executed; design-only information diagnostic is reported below |
| E: additional layers / MPGD / AC-LGAD | Planning only; their measurements do not participate in these fits |

The maintained new inference modes are **`l1_rx` and `l1_ry` separately**. Defaults and all nine historical correction scopes remain available. A full rotation matrix, a passed infinitesimal derivative check, full linear rank and tiny iteration updates each establish different properties; none alone establishes a valid finite joint-rotation model. Nominal uncertainty calibration is not certified by this checkpoint.

## Conditions, samples and fixed-input provenance

Canonical physics is unchanged: 1 GeV electrons, gun mean (0,0,-500) mm, the existing angular distribution and 0.2 mm X/Y source width, existing materials/thicknesses, hit errors, zero-field ACTS KF, seed covariance, electron hypothesis and official Pede inversion/rejection settings. Only the declared physical placements, seeds and the one 1,000-event count differ. There are six new Geant4 samples, 1,500 events and five distinct seeds; Rx100 and Ry-positive intentionally share the canonical seed across different physical geometries. Replays of saved RawHits are not additional independent samples.

| Case | Events | Seed | ACTS tracks before/after | RawHit SHA-256 prefix |
|---|---:|---:|---:|---|
| rx_positive | 100 | 2035032807 | 94/94 | `6a7d1cf99ee5fdd2` |
| rx_1000 | 1000 | 2035032907 | 935/935 | `5ca0b99200bf5614` |
| ry_positive | 100 | 2035032807 | 95/95 | `ef0bd1363a4df317` |
| ry_negative | 100 | 2035032911 | 97/97 | `c27bb15d0525c7be` |
| l1_tilts | 100 | 2035032921 | 98/98 | `1401227c30ded4bc` |
| two_tilts | 100 | 2035032922 | 91/91 | `831c1bce2f22dfac` |

Full seed/configuration/Geometry/RawHit checksums, Pede parameters/errors/statuses, rejection histories, track metrics, all iterations and version chains are in `scientific_summary.json`. Every inference delivery strips optional Truth Geometry and producer Simulation checksums, sets `measured_geometry` to null, and retains only the compatible RawHit/readout contract. The saved file bytes are reused at every iteration. Truth is used for Simulation, synthetic input generation and independent post-fit validation only.

The initial 100-event Rx design predicted 6.325 mrad formal precision for a 30 mrad injection. Its final offset of 6.94 mrad justified one separate 1,000-event cross-check, with no coverage/error/physics change. No muon or 30-seed campaign was launched.

## Physical Geometry, frames and reconstruction consistency

Lengths are mm; angles are radians. Rotations are right-handed active Global transforms. Nominal sensor X/Y/Z map to Global +Y/-Z/-X; ACTS u/v/n map to Global X/Y/Z. Thus Global +Rx corresponds nominally to negative sensor-Z rotation, and Global +Ry to positive sensor-X rotation. For a nominal normal, Rx gives `(0,-sin(alpha),cos(alpha))`, and Ry gives `(sin(beta),0,cos(beta))`. These conventions were checked with actual DD4hep contexts.

The focused factory adds dedicated `global_rx`/`global_ry` attributes; initial constructors use `Rz(gamma) Ry(beta) Rx(alpha)`. It can serialize a complete proper matrix using `global_r00` through `global_r22`, excluding mixed matrix/axis attributes. The existing single centered sensitive SiMAPS L1/L2 module, phi0=0, non-reflected hierarchy is required. Materials, readout, thickness and IDs are unchanged. Axis preparation is bounded to 0.1 rad; tested physical tilts are 30 mrad and the declared combined cases. Matrix representation does not validate arbitrary-angle tracking or arbitrary layouts.

A current-frame update is `p_new = Q(p_current-c)+c+d`, with the actual sensitive center c. Pure tilts keep c fixed. A supplied Global translation occurs after rotation. Corrections left-compose the current matrix; no Euler-angle accumulation is used as state. Composition/inverse/serialization tests include nonzero X/Y/Z/Rz and simultaneous mathematical rotations.

Fresh VolumeManager contexts and independently imported GDML verify complete matrices, centers, u/v/n, fixed channels and all seven placements. Actual RecHit XYZ agrees exactly at float32 precision; Measurement2D local positions and sensor-X/Z-to-u/v covariance mapping agree. Predicted/filtered/smoothed intersections lie on the selected planes. Physical and corrected exports have zero illegal overlaps/extrusions at 0.0001 mm tolerance. The tested small tilts retain layer order and DirectNavigator assumptions; tracking limits were not changed.

Evidence: `*_geometry_final05/passed.json`, their first/final DD4hep and GDML reports, physical overlap reports, and `archived_combined_geometry_checks_05/report.json`. The latter checks rejected combined orientations using single-Rx diagnostic Reconstruction only; it does not enable a combined solve.

## Covariance and post-fit serialization

RecHit error entries retain the existing sensor X/Z segmentation contract. ACTS uses u=-sensor Z and v=sensor X, with the corresponding variance permutation. For residual F and local basis u,v, `H=[[tx*u_z-u_x,tx*v_z-v_x],[ty*u_z-u_y,ty*v_z-v_y]]`, and `S=H C_uv H^T`. The tilt writer profiles the existing four-local-parameter straight-line reference, freezes slopes and `W=chol(S)^-1` for one Pede solve, and writes `W*m`, `W*A` and `W*B` together. Scalar sigma=1 is dimensionless algebraic whitening of the unchanged physical uncertainties. It is not an empirical rescaling. Each external iteration recomputes the current reference and Geometry. No bilinear local/global product is solved inside Pede, and no MC slope is used.

A pre-existing diagnostic defect stored local u/v and time variances in Global `TrackPoint.positionError`. The final serializer writes `[u v] C_uv [u v]^T`, with physical Global XYZ cross terms. Measurement2D retains local u/v/time covariance and the u/v cross term. Both output representations use the same symmetric projection of ACTS floating-point covariance; the internal KF state is untouched. Historical output files are preserved and should not be reinterpreted as containing the corrected Global diagnostic covariance.

A strict intermediate-state check exposed tiny covariance asymmetry after the first output fix. The symmetric output fix was validated in a fresh fifth build. Float32 comparisons propagate local and output half-ULPs through the rotation, including cancellation, plus the separately checked basis precision. Failed checks and all intermediate builds remain. The numerical fitter prefix and electron hypothesis are byte-identical to the task-start snapshot; old Mille branches are byte-identical, and all historical numerical outputs match. Original and intermediate source pins remain in `validation/validated_sources_history.json`; only the validated full-source pin advanced.

## Mille conventions, labels and derivatives

With current `r=m-c`, `F=(x0+tx*(mz-zref)-mx, y0+ty*(mz-zref)-my)`, and frozen reconstructed reference slopes, a physical infinitesimal Global rotation gives `dm=k cross r` and `dF=(tx*dm_z-dm_x,ty*dm_z-dm_y)`. The numerical z reference remains 100 mm; it is not a layer placement.

| Label family | Meaning / physical correction | Physical residual derivative before whitening |
|---|---|---|
| 1000+layer | X measurement bias; negate fitted value | (1,0) |
| 2000+layer | Y measurement bias; negate fitted value | (0,1) |
| 3000+layer | Existing Rz bias; negate fitted value | (-r_y,r_x), mm/rad |
| 4000+layer | Existing physical Z increment, positive | (tx,ty), mm/mm |
| 5000+layer | Physical Global Rx increment, positive | (tx*r_y, ty*r_y+r_z), mm/rad |
| 6000+layer | Physical Global Ry increment, positive | (-tx*r_x-r_z, -ty*r_x), mm/rad |

The supported tilt writer releases only 5001 or 6001 through its canonical steering. Other families retain their existing modes and conventions; mixed translation/tilt or six-DOF inference is not released. Horizontal-plane limits use r_z=0; nonzero orientations require the actual current point and pivot.

The final same-plugin/factory proof is `derivatives_05_L1/report.json`: 78 fresh contexts, 324 two-component physical comparisons, and 216 decoded binary components, including implicit zeros. The supplemental precision analysis counts 144 nonzero stored entries. Tests include positive/negative Rx/Ry, epsilon 1e-3/1e-4/1e-5 rad, multiple channels/slopes, nonzero center (1.25,-0.75,52) mm, nonzero existing Rz, and combined orientations. The production C++ writer is compiled against the official Mille library; no Python-only derivative assertion substitutes for the binary checks.

| Epsilon [rad] | Max physical absolute error [mm/rad] | Max relative error, nonzero components |
|---:|---:|---:|
| 1e-03 | 8.902e-08 | 1.667e-07 |
| 1e-04 | 8.958e-10 | 1.803e-09 |
| 1e-05 | 1.268e-10 | 2.824e-09 |

Max whitened binary absolute error: 1.870e-06 per rad; max relative nonzero error: 5.657e-08. Relative comparisons exclude magnitudes below 1e-6; zero components use absolute checks. The epsilon scan shows central-difference convergence followed by numerical precision. L2 mathematical/physical derivative evidence is retained under `derivatives_03_L2/`, without a released L2 tilt inference mode.

The Controller refuses missing, stale, mismatched or incomplete evidence; it pins plugin, Geometry library, report/checksums and canonical steering. Before every supported tilt solve, actual weighted Mille local/global rows are profiled separately per track. Templates remain disabled by default.

## Supported controlled closure results

All values below are mrad. Initial errors are the corresponding initial Pede nominal errors. Final values are cumulative physical Geometry orientations; successive fits use the same RawHits, so their errors are not combined as independent measurements.

| Case | Injected | Initial physical fit ± nominal error | Final physical angle | Iterations |
|---|---:|---:|---:|---:|
| rx_positive | +30.000 | +39.20500 ± 6.32460 | +36.942089 | 3 |
| rx_1000 | +30.000 | +29.35800 ± 2.01290 | +30.908966 | 3 |
| ry_positive | +30.000 | +30.33200 ± 6.65910 | +33.868436 | 4 |
| ry_negative | -30.000 | -19.63600 ± 6.16280 | -27.769744 | 6 |

| Case | ACTS chi2/stored-NDF before → exact final | Pede chi2/NDF initial → last | Max rejected local fits, initial / across solves |
|---|---|---|---|
| rx_positive | 1.441469 → 1.381047 | 2.338156 → 2.305914 | 0 / 0 |
| rx_1000 | 1.628211 → 1.592146 | 2.436568 → 2.416419 | 1 / 1 |
| ry_positive | 1.256694 → 1.219347 | 2.059853 → 2.034798 | 0 / 0 |
| ry_negative | 1.617524 → 1.592928 | 2.682012 → 2.659106 | 0 / 0 |

ACTS stored-NDF is 10 per five-plane track; the four-local-parameter straight-line model has six statistical local degrees of freedom before global parameters and rejections. Pede chi2 is already evaluated after its global fit and uses its recorded accepted-local-fit NDF; ACTS initial chi2 uses the uncorrected Geometry and KF conventions. These are different quantities. All solver process statuses, warnings and rejection histories remain in the machine summary; status 1 means the retained Pede end warning, not a failed process exit. No warnings or rejection thresholds were suppressed.

| Case | L1 normal RecHit−SimHit mean before → after [um] | L1 normal residual RMS about zero before → after [um] |
|---|---|---|
| rx_positive | +8.103 → -1.875 | 244.059 → 56.484 |
| rx_1000 | -6.316 → +0.191 | 245.762 → 7.447 |
| ry_positive | +5.912 → -0.762 | 239.169 → 30.845 |
| ry_negative | -38.190 → -2.855 | 248.958 → 18.524 |

Residual plots use unique event/layer pairs and retain unfiltered matched values; they are validation summaries, not Truth-based corrections. RMS is especially useful for rotations whose symmetric spatial coverage can give a small mean. Full X/Y/Z/normal means, RMS and pair counts are recorded in JSON.

## Observability and design-only six-DOF diagnostic

The Rx100 initial selected design has rank 1/1 and sigma 6.325 mrad; the independent Rx1000 design predicts 2.013 mrad. The combined L1 design has rank 2/2 with errors 6.687/5.752 mrad and correlation +0.0114. The L1/L2 design has rank 4/4 with errors 6.926/7.079/5.937/6.075 mrad; same-axis cross-layer correlations are about +0.2673. Coverage values, covariance, extrema, normalized eigenspectra, weak eigenvectors and parameter correlations are saved in `*_observability.json` and `rx_1000_design_v2.json`.

Actual production-Mille negative controls refuse zero slopes at horizontal planes and zero impact at the pivot (rank zero), a tiny-impact design (nonzero rank but unusable precision), and collinear two-tilt information (rank 1/2). The declared 0.01 rad information bound is a configurable demonstration sensitivity threshold, not calibrated coverage.

The Rx1000 design-only augmentation uses actual weighted local rows/current reconstructed points and frozen reference slopes, with all unselected sensors fixed. It is not an actual six-DOF binary/solver/closure test:

| Hypothetical selected design | Rank | Column-normalized condition | Formal tilt error range [mrad] |
|---|---:|---:|---:|
| L1_six_dof | 6/6 | 4.4539 | 2.549–2.597 |
| L1_L2_six_dof | 12/12 | 7.7024 | 2.267–2.695 |

This suggests useful information under the fixed references and existing coverage. Full L1/L2 six-DOF fitting is **not scientifically validated or enabled** because the prior joint-rotation gate failed. Releasing every sensor would also require an explicit gauge strategy; the current relative alignment retains fixed reference planes. MPGD/AC-LGAD do not contribute measurements here.

## Combined-rotation failure, rerun and causal control

The L1 experiment converged numerically in six iterations to ordered-XYZ diagnostics (Rx,Ry,Rz) = (36.060,-23.219,+0.220) mrad for the declared (30,-25,0) mrad orientation. The L1/L2 experiment reached its eight-iteration cap. A separate fresh-state rerun with identical RawHits, cuts, errors and solver, allowing up to twenty iterations, converged after fourteen. Its diagnostics were L1 (33.366,-13.366,+0.443) and L2 (-20.127,+25.234,-0.451) mrad for injected (30,-25,0) and (-25,20,0). Both experiments remain scientifically rejected.

The isolated noiseless fixture keeps continuous sensor-local points fixed, uses the canonical 0.01 mm errors, the production writer, official Pede and the maintained correction implementation. After ten two-axis iterations, tiny updates coexist with a total orientation error of 357.389 urad and an ordered-Rz diagnostic drift of 16.307 urad. An isolated control adding the already established Rz derivative to the same scalar rows removes the missing direction; it is not a released mixed-rotation or six-DOF mode.

| Noiseless validation/control | Total orientation error [urad] | Profiled local chi2 |
|---|---:|---:|
| truth_validation_only | 0.000000 | 4.082319e-20 |
| two_global_axes | 357.388796 | 2.975005e-02 |
| isolated_rz_release | 0.120097 | 1.255890e-09 |

The mathematical cause is finite update parameterization: `[Kx,Ky]=Kz`, so repeated fixed-Global `Ry(delta_y) Rx(delta_x)` increments do not remain in the declared two-coordinate finite family `Ry(beta) Rx(alpha)`. An unfitted twist accumulates, and a two-component gradient can settle with nonzero orientation error. The linear derivatives and DD4hep/ACTS placement are correct; the finite joint-mode contract is not closed. The noiseless failure rules out an event-count explanation for this defect.

Milestone C therefore fails its scientific closure gate even where numerical convergence occurs. The Plugin, Reconstruction, Alignment, Geometry Correction and Controller refuse `l1_rx_ry` and `l1_l2_rx_ry`. Disabled prototype configurations/steering and archived code remain for audit, not as maintained execution routes. D/E are not advanced. More statistics, error rescaling or suppressing Rz after a solve would not establish the missing finite-model validation. A future model must define a consistent retraction and its Jacobians, such as a constrained two-coordinate chart with transported generators or a separately validated three-rotation model.

## Regressions, warnings, anomalies and limits

The final build passed all nine representative historical writer replays with exact Mille bytes and exact ACTS metrics. Controller replays reproduce historical candidate IDs for L1/L2 X, X/Y, approximate Survey, three Rz scopes and three Z/XYZ scopes. The saved L2-only seven-stage regression gives 99 tracks, +198.75 um correction, L2 Rec−Sim -199.571 → -0.821 um, and ACTS chi2/stored-NDF 45.592 → 1.981. RawHit combined/split equivalence and ROOT output checks passed. All existing X/Y/Rz/Z physical derivative tests were rerun against the final build. The 36 unit tests include Controller safety, metadata, transforms and scope; actual Plugin/CLI combined-mode refusals and safety checks passed. Initial host unit execution lacked NumPy; container tests passed.

The preservation audit verifies **16,412 historical files unchanged**, 755 completed-stage checksums, 139 fixed-RawHit iterations and 120 post-fit accepted-hit anomaly checks. Every state retains its initial active Geometry. The unchanged baseline checker also verifies 221 baseline and 2,046 relocated records. Source pins retain original hashes/history; numerical KF/electron and old writer branches were compared directly with the task-start snapshot. All maintained untracked sources are included in the source archive. No generated data or installation was staged.

The Rx1000 Simulation contains four additional off-plane SimHits: event indices 137 (L2), 418 (L3), 437 (L2), 508 (L2), each 25 mm from its decoded plane. All are in unaccepted events throughout the audited reconstructions. No event was silently filtered. Historical Z-event-58 evidence remains unchanged; the precise Geant4 sensitive-hit aggregation/association cause remains unresolved.

The retained Rz ensemble pull widths about 1.43/1.66 and mean Pede chi2/NDF about 2.340 remain uncertainty-model limitations. These controlled tilt samples do not certify formal error coverage. Material/process noise and electron radiation modeling were not changed. The ACTS surfaces follow DD4hep placement but do not automatically gain a new material model. MPGD/AC-LGAD remain outside the five-plane alignment model.

Retained failed attempts include the initial host NumPy test, a Path serialization error after successful initial checks, a float32-Mille coordinate-recovery design diagnostic, the eight-iteration combined run, noiseless combined closure, first Rz diagnostic loader failure (libMilleC search path), and intermediate covariance checks. Corrections/reruns use new directories; failed data/logs remain. SQLite ResourceWarnings in existing test fixtures and Pede warnings were recorded, not hidden.

## Artifacts and commands

Primary evidence root: `result/tilt_alignment_20261022_01/`. Numerical machine report: `scientific_summary.json`; preservation/parent-chain/RawHit checks: `final_data_audit.json`; precision: `derivative_precision_summary.json`; exact-model diagnosis: `combined_model_comparison.json`; maintained-source changes: `changes_from_task_start.json`; backups: `source_before.tar.gz`, `experimental_combined_source.tar.gz`, `source_final.tar.gz`. Builds 01–05 and every partial failure remain.

ROOT output directories are `validated_rx_root/`, `validated_rx_1000_root/`, `validated_ry_positive_root/`, `validated_ry_negative_root/`. Each contains `tilt_alignment.root`, residual/quality/Geometry canvases and summary JSON. Archived rejected experiments are in `l1_tilts_experimental_root/` and `two_tilts_experimental_root/`, explicitly showing unfitted Rz drift. Open, for example:

```sh
root -l result/tilt_alignment_20261022_01/validated_rx_root/tilt_alignment.root
// In ROOT:
new TBrowser;
```

Exact executed host commands are listed in `COMMANDS.md`, with stage-level `command.json`, stdout and exit records under each output. Do not rerun those occupied paths. Current reusable examples are in [the Workflow guide](WORKFLOW.md#individually-validated-l1-rxry) and [Controller guide](../calibration/README.md#individual-global-x-and-y-tilts). The ROOT CLI accepts maintained report, candidate XML and final Reconstruction outputs directly; no ignored study helper is required.

The saved 99-track regression Simulation remains a local non-Git dataset at `results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root`. New Simulation/RawHit/Reco/Mille files remain under the evidence root and are also excluded from Git. Their checksums/provenance are in the machine summary and output inventory. Reproduction requires those reference bytes or a separately labeled regenerated sample with its exact software and seed.

## Next development steps

1. Define one finite joint-rotation parameterization and validate its retraction/Jacobians in the noiseless fixture before new detector degrees of freedom. Retain the existing individual Rx/Ry and all historical modes.
2. After that gate passes, repeat coupled physical derivative, rank/correlation, fixed-RawHit iterative and independent Geometry closure tests. A full-rank six-DOF design is a starting diagnostic, not a release criterion.
3. Keep uncertainty validation separate: use independent samples after the model is correct, retain existing pull findings, and investigate the process/error model without ad hoc rescaling.
4. Extend to other SiMAPS sensors with explicit reference constraints only after the coupled model is validated. For MPGD/AC-LGAD, validate their actual measurement dimensionality, local axes, position/time covariance and ACTS association, include those measurements in the existing writer, then repeat weighted rank/gauge and closure tests. Seven placements alone provide no seven-layer alignment claim.

## Files created and modified relative to task start

The task-start snapshot includes the pre-existing uncommitted work. The authoritative complete list is `changes_from_task_start.json`; all formal files, including untracked ones, are in the final source archive. No source file was removed. The table below records this task’s changes, independently of the larger pre-existing Git diff.

| File | Task change | Git tracking |
|---|---|---|
| `README.md` | modified | tracked |
| `alignment/align.py` | modified | tracked |
| `alignment/pede_l1_l2_rx_ry.txt` | created | untracked |
| `alignment/pede_l1_rx.txt` | created | untracked |
| `alignment/pede_l1_rx_ry.txt` | created | untracked |
| `alignment/pede_l1_ry.txt` | created | untracked |
| `calibration/README.md` | modified | untracked |
| `calibration/config/l1_l2_rx_ry_demo.json` | created | untracked |
| `calibration/config/l1_rx_demo.json` | created | untracked |
| `calibration/config/l1_rx_ry_demo.json` | created | untracked |
| `calibration/config/l1_ry_demo.json` | created | untracked |
| `calibration/iteration.py` | modified | untracked |
| `calibration/settings.py` | modified | untracked |
| `correction/correct_geometry.py` | modified | tracked |
| `correction/scope.py` | modified | untracked |
| `docs/GEOMETRY_CONVENTIONS.md` | modified | untracked |
| `docs/TILT_ALIGNMENT_VALIDATION.md` | created | untracked |
| `docs/WORKFLOW.md` | modified | tracked |
| `geometry/placements.py` | modified | tracked |
| `geometry/prepare.py` | modified | tracked |
| `geometry/scenarios/L1_L2_rx_ry.json` | created | untracked |
| `geometry/scenarios/L1_L2_rx_ry_reference.json` | created | untracked |
| `geometry/scenarios/L1_rx.json` | created | untracked |
| `geometry/scenarios/L1_rx_reference.json` | created | untracked |
| `geometry/scenarios/L1_rx_ry.json` | created | untracked |
| `geometry/scenarios/L1_rx_ry_reference.json` | created | untracked |
| `geometry/scenarios/L1_ry.json` | created | untracked |
| `geometry/scenarios/L1_ry_negative.json` | created | untracked |
| `geometry/scenarios/L1_ry_reference.json` | created | untracked |
| `localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc` | modified | tracked |
| `localDetEICrecon/alignment/src/BeamTestMilleWriter.cc` | modified | tracked |
| `localDetEICrecon/alignment/src/BeamTestMilleWriter.h` | modified | tracked |
| `localDetEICrecon/alignment/src/TiltMeasurementModel.h` | created | untracked |
| `localDetEICrecon/geometry/SiTrackerEndcap2XY_geo.cpp` | modified | untracked |
| `localDetEICrecon/processors/BeamTestMilleProcessor.cc` | modified | tracked |
| `reconstruction/reconstruct.py` | modified | tracked |
| `validation/README.md` | modified | tracked |
| `validation/check_safety.py` | modified | tracked |
| `validation/gdml_geometry_probe.py` | modified | untracked |
| `validation/geometry_probe.py` | modified | untracked |
| `validation/run_closure.sh` | modified | tracked |
| `validation/test_rotation.py` | modified | untracked |
| `validation/test_tilt_alignment.py` | created | untracked |
| `validation/tilt_hit_audit.py` | created | untracked |
| `validation/tilt_observability.py` | created | untracked |
| `validation/tilt_writer_fixture.cc` | created | untracked |
| `validation/validate_tilt_derivatives.py` | created | untracked |
| `validation/validated_sources.json` | modified | tracked |
| `validation/validated_sources_history.json` | modified | untracked |
| `visualization/tilt_alignment.py` | created | untracked |
| `visualization/z_alignment.py` | modified | untracked |
