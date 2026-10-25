# EICrecon-based telescope alignment user guide

The bounded native Calibration Controller is described in the
[Controller guide](NATIVE_CALIBRATION_CONTROLLER.md). It uses the shared native
numerical operations without Truth and preserves the manual closure protocols
below. Statements about missing Controller support in earlier milestone
sections describe their historical scope.

Start here for the opt-in, 32-track channel-based Alignment Closure Test on
`feature/upstream-acts-geometry`. See the [code map](TELESCOPE_ALIGNMENT_CODE_MAP.md)
for the actual source flow and the [historical closure report](BARREL_CHANNEL_ALIGNMENT_CLOSURE.md)
for the original numerical validation. The [rename validation record](TELESCOPE_RENAME_VALIDATION.md)
contains the complete move inventory and post-rename regression evidence. Historical reports describe their original
source paths and executions; use this guide for current commands.

## Telescope versus barrel-compatible representation

The intended detector is a seven-plane beam-test telescope, not an ePIC barrel.
The pinned ACTS DD4hep endcap converter assumes paired endcaps. This single-sided
fixture instead uses the installed `DD4hep_SiTrackerBarrel` constructor with real
Tube envelopes and one planar module per layer. Official `ActsGeometryProvider`
therefore uses its barrel conversion to construct TrackingGeometry and SurfaceMap.
`TestbenchBarrelMetadata` supplies actual envelope/axis metadata and retains its
technical name. No dummy detector or replacement geometry provider is used.
The standard ePIC detector and its normal event reconstruction remain separate.

The fixture beam is along Global +X through sensors at X=250–550 mm. ACTS local
u=-Global Y, v=-Global Z. The injected physical Global Y translations are L1
+0.150 mm and L2 +0.200 mm; labels 700102 and 700202 are physical translations in mm.
Positive Global Y corresponds to negative module-local X. No signs, labels,
placements, segmentation or numerical settings were changed by the naming refactor.

## Environment and prerequisites

Run from the repository root. The fixed Docker container mounts this checkout at
`/work`; the validated container is `sweet_mahavira`. Set `TESTBENCH_CONTAINER` to
your existing compatible container. The wrapper uses its existing image; it does
not repin it. The example image pin is recorded in `environment/container.env.example`.
Pinned software: EICrecon `195966d41899800eaeca6fbafd63cd53735e6543`, ACTS 45.3.0,
DD4hep 1.36; ROOT/PyROOT, podio, numpy, CMake, C++20 and algorithms are required.
Mille and Millepede-II are installed under `external/install`; dependency revisions
are in `environment/dependencies.json`. A new installation can use
`environment/setup_dependencies.py` only when `external/` does not already exist.
Do not overwrite an existing installation.

The closure generates its own deterministic channel input. Historical preservation
regressions additionally require local data inventoried in
`validation/preserved_files.json`, `relocated_data_sha256.json`,
`validated_sources.json` and `path_migration.json`. These ignored datasets cannot
be recovered from Git alone. Existing results, logs and failed attempts are retained.
This test is material-free in ACTS, zero-field and synthetic: it does not simulate
Geant4 energy loss, scattering or electronics and does not validate uncertainty coverage.
The original BeamTestReco/Controller workflow remains independently supported.

## Build and complete closure

All output names below must be unused. Change the common build/result name for
each rerun; do not delete or reuse existing outputs. The wrapper can also create
`result/.environment`. Commands below write new outputs, not production installations.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/telescope_closure_manual_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/telescope_closure_manual_01 -j2
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_closure_manual_01 --result result/telescope_closure_manual_01 \
  --events 32 --chi2-cut 1000 --step all
```

Targets include `TelescopeTracking.so`, `TelescopeMille.so`,
`libTestbenchBarrelMetadata.so`, `TelescopeChannels`, `TelescopeMilleDerivatives`,
`TelescopeMilleFixture` and `LegacyTelescopeCrosscheck`. The driver sets plugin and
library paths. Do not install over the production plugin.

The deliberately displaced fixture needs the explicit capture window
`-PTelescopeTracking:TelescopeCKF:Chi2CutOff=1000`. All passes use the same value;
the driver refuses inconsistent cuts. This changes selection, not covariance or
Kalman weights. Default cut 15 remains in the independent one-event regression.
No Pede uncertainty scaling is applied.

## Read results and ROOT diagnostics

Read-only report inspection (host Python is sufficient):

```bash
python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path('result/telescope_closure_manual_01/validation/report.json').read_text())
for key in ('passed', 'events', 'recovered_global_y_mm', 'remaining_geometry_bias_mm',
            'post_correction_mm', 'control_correction_mm', 'input_channel_sha256'):
    print(key, r[key])
for name, row in r['summaries'].items():
    print(name, {k:v for k,v in row.items() if k not in ('per_track_chi2','residuals_mm')})
print(r['pede_diagnostics'])
PY
```

In a graphical ROOT environment:

```text
root -l result/telescope_closure_manual_01/validation/closure.root
root [0] new TBrowser;
```

Batch ROOT read-back (the wrapper may create its environment directory):

```bash
bash environment/run.sh python3 -c 'import ROOT; ROOT.gROOT.SetBatch(True); f=ROOT.TFile.Open("/work/result/telescope_closure_manual_01/validation/closure.root"); assert f and not f.IsZombie(); names=["sensor_centers","L0_residuals","L4_residuals","nominal_acts_chi2_stored_ndf","corrected_acts_chi2_stored_ndf"]; assert all(f.Get(n) for n in names); print(f.GetListOfKeys().GetEntries()); f.Close()'
```

`L0_residuals` through `L4_residuals` contain local u/v residuals and Hit Residuals
relative to offline Truth. `sensor_centers` compares nominal, Truth and corrected
Geometry. Truth is used only for fixture generation and final evaluation.
Official Mille Binary inspection:

```bash
bash environment/run.sh bash -lc 'export LD_LIBRARY_PATH=/work/external/install/lib:$LD_LIBRARY_PATH; exec /work/external/install/bin/inspectMilleBinary /work/result/telescope_closure_manual_01/nominal/mille.dat'
```

## Independent stages and Input/Output

Use the same arguments as above and replace `--step all` with one row below.
Stages refuse existing outputs. Each subprocess retains `command.json`,
`stdout.log`, `exit.json`; completed stages record artifact hashes in `complete.json`.

| Step | Input | Output / success criterion |
|---|---|---|
| geometry | canonical XML and fixture builder | separate nominal/Truth XML, L1/L2 shifts verified |
| data | XML and `TelescopeChannels` | shifted/control ROOT with only EventHeader and RawTrackerHit channels; separate Truth JSON and checksums |
| nominal | immutable shifted channels, nominal XML | fresh eicrecon, reco.root, audit.json, mille.dat/json, derivative gate |
| solve | native Mille records | official Pede result/log/status; rank-two independent Schur comparison |
| correct | nominal XML and Pede text only | new corrected.xml, provenance and real Geometry/ID audit |
| corrected | same shifted channels, corrected XML | fresh eicrecon and second native reconstruction; unchanged input checksum |
| postsolve | corrected Mille records | diagnostic remaining correction |
| control | separately generated nominal channels and nominal XML | independent zero-shift reconstruction |
| controlsolve | control Mille records | correction consistent with zero |
| check | all stages; offline Truth for evaluation | validation/report.json and closure.root; XML whitelist, EDM, seed, covariance, hash and closure gates |
| regressions | nominal/data/geometry stages, fresh build, historical data | NAME_regressions/complete.json, 18 successful commands |

`pilot` runs four events after geometry/data; it is diagnostic and does not replace
the full closure. `--events` accepts 16–64; the reference cohort is 32.
Extra checks require a fresh `--validation-name` to preserve previous reports.

## Regression commands

```bash
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_closure_manual_01 --result result/telescope_closure_manual_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name manual
python3 validation/verify_preservation.py
git diff --check
```

The 18 commands include fresh geometry and standalone CKF builds, official
Geometry/navigation checks, one-event JANA reconstruction/read-back, native/legacy
Mille equivalence, the separate 16-ray mathematical fixture and Pede, 46 unit tests,
safety refusals and preservation checks. Read each subprocess exit record.
Existing SQLite ResourceWarnings may appear; preserve them in the logs.

## Reference values and limits

| Quantity | Reference |
|---|---:|
| Accepted nominal / corrected / control | 32 / 32 / 32 |
| Per-track measurements / outliers / holes | 5 / 0 / 2 |
| Per-pass Mille records / scalar equations | 32 / 320 |
| L1 / L2 recovered Global Y | +149.14 / +203.18 um |
| L1 / L2 corrected minus Truth | -0.86 / +3.18 um |
| ACTS chi2/stored-NDF nominal / corrected | 37.167316 / 0.690849 |
| Control ACTS chi2/stored-NDF | 0.641260 |
| Pede rank / rejected local fits | 2 / 0 |
| Nominal/postsolve process exit / end status | 0 / 1 (warning) |
| Nominal Pede chi2/statistical-NDF | 221.06869 / 190 = 1.163519 |

Pede recommends approximately 1.08 error scaling; it is deliberately not applied.
ACTS stored NDF is 10 per track (measurement dimensions); Pede profiles four local
parameters per track and two shared parameters, giving 32*(10-4)-2=190.
The finite seed prior also means native CKF and profiled Pede chi2 need not match.
Geometry/derivative closure is not validation of a statistical uncertainty model.
ROOT file timestamps may change between runs; immutable input bytes within a run
and canonical channel payload equivalence are checked separately.

For troubleshooting, inspect the first failing subprocess and preserve its output.
Missing dependencies, incorrect fully qualified JANA parameters or reused output
names must be repaired rather than bypassing validation. No Geometry activation
is performed. Historical `BARREL_*` reports refer to the temporary conversion
representation; their result paths and numerical records remain unchanged.

## Consolidation boundary

The [implementation audit](TELESCOPE_IMPLEMENTATION_AUDIT.md) inventories retained
modules, dependencies and deleted duplicate build entries. This synthetic-channel
closure is the active EICrecon-based development workflow. The old endcap backend
remains a capability/reference implementation: its validated rotations, SO(3),
Geant4/digitization and sequential Controller lifecycle are not yet replaced by
this two-Global-Y, material-free fixture. Do not infer that those features are
available in this native chain. No automatic Geometry activation is provided.

The Pede text parser now lives in `alignment/pede.py`; it has no dependency on the
legacy solver CLI or correction scopes. `alignment.align.read_pede` remains an
import-compatible alias for external callers. Pede itself is still the official
external executable, not Python numerical inference.

## Selected native rotation closure

The next validated scope is **L1 physical Global X rotation** (in-plane for this
+X telescope), alone or together with L1/L2 physical Global Y translations.
See the [legacy/native parity and rotation results](TELESCOPE_ALIGNMENT_LEGACY_PARITY.md).
This is distinct from legacy +Z-beam Global Rz labels. The original `l1_l2_y`
default, capture cut 1000, covariance, seed prior and Pede settings are unchanged.
No native general six-DOF or Controller migration is implied.

Build as above with `TELESCOPE_BUILD_MILLE_PROBE=ON`, then use **new** result names:

```bash
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_closure_manual_01 --result result/telescope_rx_manual_01 \
  --events 32 --chi2-cut 1000 --mode l1_rx --step all
# Run the combined case only after the single-rotation gates pass.
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_closure_manual_01 --result result/telescope_y_rx_manual_01 \
  --events 32 --chi2-cut 1000 --mode l1_y_rx_l2_y --step all
```

The fixed fixture injects L1 Rx +1.8 mrad; the combined case additionally injects
L1 Y +0.150 mm and L2 Y +0.200 mm. This amplitude gives nontrivial pixel changes
while keeping sensitive corners inside the unchanged module envelope. Truth is
used only to make channels and evaluate closure. Pede solves label 700104 in rad;
Y labels 700102/700202 remain mm. The physical pivot is the current sensitive
center, with `Rnew=Exp([dx,0,0]) Rcurrent`. All other pose components stay fixed.

The real DD4hep constructor's selected chart maps decreasing component XML `y`
to increasing Global Rx. Correction composes SO(3) first and serializes that
one-axis subgroup; it is not an additive Euler implementation of arbitrary
rotations. Fresh actual DD4hep and ACTS matrices verify the result independently.
Selected rotations are restricted to the proven chart and sensor; no new geometry
provider, navigator, fitter, derivative model, material map or numerical solver
is introduced.

Each `solve` runs `physical_derivatives/`: actual native references are frozen and
compared against real sensor geometries reloaded in fresh processes at ±1e-4,
±1e-5 and ±1e-6 rad. `postsolve` repeats this for corrected Geometry in
`corrected_physical_derivatives/`. Rank, conditioning and original-error sensitivity
are checked without adding fit constraints. Numerical sensitivity guards are
explicit engineering gates (scaled condition <100, angular sigma <1 mrad,
translation sigma <0.02 mm for the earlier scopes). Coupled rotations require
selected and nuisance-marginalized angular sigma <0.5 mrad before Pede. These
are not uncertainty-coverage certification.

The new modes share all existing step names except that `regressions` must run
with the original `l1_l2_y` baseline. Rotation-mode `check` writes
`validation/report.json` and `validation/rotation.root` (9 ROOT histograms).
To rerun checks on completed outputs, supply a fresh `--validation-name`.
The report includes units, actual IDs, full relative orientation error,
initial-fit nominal errors/correlations, center biases, per-layer residuals,
Pede chi2/NDF and rejection diagnostics. Read JSON or open `rotation.root` with
ROOT/TBrowser as for the original diagnostics. GUI operation is not part of the
batch validation claim.

Geometric recovery uses a predeclared five-initial-nominal-error tolerance;
actual XML-to-DD4hep/ACTS pose serialization is checked at 1e-9 mm / 2e-12 matrix
entry precision. Remaining Y and single-Rx increments must be below 2e-5 mm/rad;
signed tilts and coupled rotations require each update below one quarter its
initial nominal sigma. See the parity report for the exact scope-specific gates. Successive fits reuse the same channels: their uncertainties are not
combined as independent measurements. No Pede error rescaling is applied.

## Selected native SO(3) study

The bounded three-axis L1 study uses `--mode l1_rx_ry_rz` or
`l1_rx_ry_rz_negative`, the existing explicit broad-angle beam recipe, 4096
channels/events and the same capture window. It does not change the default
32-track translation workflow above. Its Truth is one physical rotation vector,
not an ordered Euler product. Fit inputs contain immutable channels only.
See the [three-axis milestone](TELESCOPE_ALIGNMENT_LEGACY_PARITY.md#three-axis-native-so3-milestone)
for exact fresh build/stage commands, mathematical scope and validation evidence.
The historical fixed-ordered Rx/Ry case is separate and has not been resolved
by changing its parameter definition. No general six-DOF, native Controller or
Geant4 migration is implied by this selected scope.

## Explicit L1 Global Y plus three rotations

**Experimental, not a promoted robust alignment mode:** five of six declared
fixtures close with the explicit additional correction; seed 2026102502 with the
negative vector stops because its first fitted candidate exceeds the unchanged
module box. The containment guard must not be bypassed. See the parity report.

The bounded validation mode `l1_y_rx_ry_rz` selects only labels 700102 (mm)
and 700104/700105/700106 (rad). The negative fixture reverses all three rotations
while retaining Y=+0.150 mm. Global X/Z and other sensors are fixed. These are
material-free synthetic channel studies, not Geant4 performance or statistical
coverage measurements.

Use a fresh result path and a freshly configured native build as described
above. The explicit additional correction requires `--refine-once`; the default
workflow still performs one correction. It is limited to these four-parameter
modes, immutable data and at most one additional correction:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/telescope_closure/closure.py \
  --build build/native_y_rotations_20261024_01 \
  --result result/my_l1_y_rotations_seed1 \
  --mode l1_y_rx_ry_rz --events 4096 \
  --beam validation/telescope_alignment/y_rotation_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

The exact same capture window applies to every pass. Do not reuse a result
path. Replace the mode with `l1_y_rx_ry_rz_negative` and select beam seed2/3 for
the other declared cohorts; paired signs share rays and are not independent.
The explicit protocol contains `refine`, `refined` and `refinesolve` between
`postsolve` and `control`. Every stage can also be invoked independently using
`--step STEP` with the same arguments. `--validation-name NAME` permits a fresh
check report without modifying previous reports.

The report separates initial Pede parameters/covariance/Pulls from cumulative
Geometry and final post-updates. Covariance uses
`nominal_covariance_mixed_units` with parameter units mm/rad/rad/rad. The
rotation-only schemas retain rad2. Success after the extra correction must not
be described as one-step success. No covariance is combined across these
correlated same-channel fits, and no candidate Geometry is activated. Read the
[parity report](TELESCOPE_ALIGNMENT_LEGACY_PARITY.md) for the predeclared gates,
first one-step failure, user-approved refinement amendment and actual results.

## Reproducing the unchanged-envelope containment study

The declared smaller fixture has six successful controlled closures. This
validates only that fixture/range; uncertainty coverage and arbitrary poses
are not certified. The original experiment remains a separate 5/6 result.

The original +150 um/(+1.8,+2.5,-2.5) mrad experiment remains 5/6 and must not be
reported as 6/6. Its negative seed 2026102502 is a permanent expected **physical
refusal**, not a completed physical closure. The separate smaller fixture uses
Y=+150 um and rotations(+1.8,+1.0,-1.0) mrad, or the opposite rotation vector.
The module, silicon, detector material and existing containment checks are
unchanged. Read the latest parity-report section for preflight and outcomes.

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
# Geometry-only design, before fitting. Output directories must be new.
bash environment/run.sh python3 validation/telescope_closure/containment.py \
  --step preflight \
  --original-run result/native_y_rotations_seed2_negative_20261024_01 \
  --prior-checkpoint result/native_y_rotations_20261024_01_audit/final_checkpoint.json \
  --build build/native_containment_20261024_01 \
  --output-dir result/my_containment_preflight

# Permanent safety regression: reproduces Pede, never starts invalid tracking.
bash environment/run.sh python3 validation/telescope_closure/containment.py \
  --step expected-refusal \
  --original-run result/native_y_rotations_seed2_negative_20261024_01 \
  --build build/native_containment_20261024_01 \
  --output-dir result/my_expected_physical_refusal

# New, independent closure experiment; same four-label inference configuration.
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/native_containment_20261024_01 \
  --result result/my_contained_positive_seed1 \
  --mode l1_y_rx_ry_rz_contained --events 4096 \
  --beam validation/telescope_alignment/contained_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

Use `l1_y_rx_ry_rz_contained_negative` for the opposite signed fixture and
`contained_beam_seed2.json`/`contained_beam_seed3.json` for the other declared
seeds. `--step` can execute each independent stage, as documented above.
Preflight and the permanent regression require the preserved original local
run, its original initial-summary JSON and the previous `final_checkpoint.json`.
These are reference datasets excluded from Git; copy them explicitly from the original local research storage when using
another checkout. This milestone does not verify external-archive coverage. A new closure regenerates
its own segmented channels from its explicit seed and physically displaced XML.
Use `cohort_summary.py --runs ... --output-dir result/NEW` to retain **all**
attempted fits in ROOT and JSON summaries, including physically refused fits.
No command activates a Geometry or adjusts an uncertainty to force closure.


## Bounded multi-sensor native alignment

The `l1_y_rx_ry_rz_l2_y` fixture selects L1 Global Y/Rx/Ry/Rz and L2
Global Y together. L0/L3/L4 remain fixed reference sensors; both sensors'
Global X/Z remain fixed. The configuration is
`validation/telescope_alignment/l1_y_rx_ry_rz_l2_y.json`. This is an opt-in,
zero-field, material-free synthetic-channel validation, not a production
Geometry activation or an uncertainty-coverage measurement.

The prospective fixture uses L1 Y = +0.080 mm, L2 Y = -0.060 mm and a
single active L1 rotation vector (+1.0, +0.5, -0.5) mrad. The `_negative`
fixture reverses the rotation vector while retaining the translations.
The bounded beam recipe is unchanged; `multi_beam_seed1.json` records seed
2026102701. No Simulation Truth enters the Pede equations or corrections.

Run from the repository root in the fixed container. Choose unused build,
result and preflight directories when repeating these commands:

```sh
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_multi_20261024_01 -DCMAKE_BUILD_TYPE=Release \
  -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_multi_20261024_01 -j2
bash environment/run.sh python3 -B validation/telescope_closure/multi_preflight.py \
  --build build/native_multi_20261024_01 \
  --prior-run result/native_containment_seed1_positive_20261024_01 \
  --output-dir result/native_multi_20261024_01_audit/geometry_preflight
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build build/native_multi_20261024_01 \
  --result result/native_multi_scope_a_seed1_positive_20261024_01 \
  --mode l1_y_rx_ry_rz_l2_y --events 4096 \
  --beam validation/telescope_alignment/multi_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

The Geometry-only preflight uses a previous native cohort solely for its
calibrated-covariance information matrix. It samples a correlated nominal
5-sigma ellipsoid with a 10% engineering margin and reloads the worst sampled
poses through real DD4hep/ACTS. This is a prospective engineering test, not a
proof of containment for every point of the ellipsoid or calibrated coverage.
It must pass before new fitted recovery is inspected. It does not resize
modules, alter errors, impose fit constraints or select successful seeds.

Each stage can also run independently with the same arguments and `--step`:
`geometry`, `data`, `nominal`, `solve`, `correct`, `corrected`, `postsolve`,
`refine`, `refined`, `refinesolve`, `control`, `controlsolve`, `check`.
`solve`, `postsolve` and `refinesolve` independently perturb each selected
sensor/parameter through real Geometry at three step sizes, then check
accumulated observability before calling official Pede. The extra correction
requires the explicit `--refine-once` option and is limited to one.

Inputs are the generated nominal XML, fixed physical fixture, recorded beam
recipe and packed `data/shifted.root` channels. Outputs include actual native
`mille.json`, official `mille.dat`, `solve/millepede.res`, full covariance and
gauge diagnostics in `solve/observability.json`, per-sensor corrected XML and
Geometry audits, and `validation/report.json` plus `validation/rotation.root`.
The latter contains nine ROOT histograms for nominal/corrected/control ACTS
chi2 and local residuals and can be opened with TBrowser. The same immutable
channel file is read in every correction pass. Initial nominal uncertainties
are reported separately from final cumulative poses and are never combined
across successive fits of the same channels.

Scope A passed its prospective 4096-track cohort: rank 5, scaled condition
1.980128, zero rejected local fits, and ACTS chi2/stored-NDF
9.946553319 -> 0.597247931. Full numerical evidence and limitations are in
`TELESCOPE_ALIGNMENT_LEGACY_PARITY.md`. This is Geometry/derivative closure,
not statistical validation of the nominal uncertainty model.


### Eight-parameter L1/L2 validation scope

`l1_l2_y_rx_ry_rz` selects Y/Rx/Ry/Rz on both L1 and L2. Its configuration is
`validation/telescope_alignment/l1_l2_y_rx_ry_rz.json`, with eight unique labels
and separate actual surface IDs. The prospective L2 rotation is
(-1.2,+0.6,+0.6) mrad; L1 and both translations retain Scope A values.
`_negative` reverses both sensors' rotation vectors. Both signs passed the
Geometry-only engineering preflight before the first fit. Full reconstruction
support is declared only by the completed cohort results in the parity report.

Both scopes have now passed full native closure: Scope A's positive cohort and
Scope B's four paired signed fixtures from two independent seeds, all with 4096
accepted tracks. Scope B retains rank 8 and scaled condition 3.16497–3.29605
across sixteen normal Pede fits, with no rejected local fits. These are validated
experimental zero-field channel fixtures; arbitrary six-DOF fitting and
statistical uncertainty coverage remain unvalidated. The complete numerical
results, including the less precise tilt components, are in the parity report.

The following historical first-attempt commands used fresh Scope B paths. That
attempt stopped in the validation observer during refined reconstruction; it
is preserved as a diagnostic and is not a completed closure. The corrected
current-source reproduction recipe follows this block.

```sh
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_multi_b_20261024_01 -DCMAKE_BUILD_TYPE=Release \
  -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_multi_b_20261024_01 -j2
# The unchanged fresh Scope A geometry probe was used for this pre-fit check.
bash environment/run.sh python3 -B validation/telescope_closure/multi_preflight.py \
  --build build/native_multi_20261024_01 \
  --prior-run result/native_containment_seed1_positive_20261024_01 \
  --output-dir result/native_multi_20261024_01_audit/scope_b_geometry_preflight \
  --mode l1_l2_y_rx_ry_rz
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build build/native_multi_b_20261024_01 \
  --result result/native_multi_scope_b_seed1_positive_20261024_01 \
  --mode l1_l2_y_rx_ry_rz --events 4096 \
  --beam validation/telescope_alignment/multi_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

For an independent repeated validation use `multi_beam_seed2.json` (2026102702)
and an unused result directory. Paired negative fixtures use
`--mode l1_l2_y_rx_ry_rz_negative` and their own unused directories. Signs of one
seed share rays; they are not independent samples. No larger campaign, automatic
Controller loop or production Geometry activation is implied.

Current multi-sensor reports distinguish data-only covariance from Pede's
expected stabilized inversion covariance. Maintained positive pre-sigmas (1.0)
provide solver diagonal stabilization while Pede regularization is disabled.
The data-only rank and sensitivity gates run before Pede; no stabilization term
is used to force observability. The parity report documents the very small
current numerical effect and its limits.

The completed primary retry is
`result/native_multi_scope_b_seed1_positive_20261024_02`. It reused only the
byte-verified completed `_01` checkpoint stages and ran `refined`, `refinesolve`,
`control`, `controlsolve`, and `check` individually with
`build/native_multi_precision_20261024_01`. The checkpoint copies, original
commands and retry commands are recorded in
`result/native_multi_20261024_01_audit/primary_retry_provenance.json` and the
`primary_retry_*` audit stages. No sample, failed stage, or scientific assertion
was overwritten. The float-serialization observer correction changes neither
measurements nor the fit; see the parity report for the reproduced failure.

For a fresh reproduction from the maintained source, use the final build and a
new result directory. The following is a reproduction recipe, not a claim that
the already populated primary retry was run again with `--step all`:

```sh
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_multi_precision_reproduce_01 -DCMAKE_BUILD_TYPE=Release \
  -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_multi_precision_reproduce_01 -j2
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build build/native_multi_precision_reproduce_01 \
  --result result/native_multi_scope_b_reproduce_01 \
  --mode l1_l2_y_rx_ry_rz --events 4096 \
  --beam validation/telescope_alignment/multi_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

Use a different unused directory for each seed/sign. The executed additional
cohort commands use the final `build/native_multi_precision_20261024_01`,
`--events 4096 --chi2-cut 1000 --refine-once --step all`, and the following
mode/beam/result combinations; their completion status is recorded in the
parity report:

| Seed | Mode | Beam JSON | Result directory below `result/` |
|---|---|---|---|
| 2026102701 | `l1_l2_y_rx_ry_rz_negative` | `multi_beam_seed1.json` | `native_multi_scope_b_seed1_negative_20261024_01` |
| 2026102702 | `l1_l2_y_rx_ry_rz` | `multi_beam_seed2.json` | `native_multi_scope_b_seed2_positive_20261024_01` |
| 2026102702 | `l1_l2_y_rx_ry_rz_negative` | `multi_beam_seed2.json` | `native_multi_scope_b_seed2_negative_20261024_01` |

Beam JSON paths are relative to `validation/telescope_alignment/`. The retained
old contained-cohort native audit required by the prospective preflight is a
local reference dataset, not a Git asset. It can be regenerated with the exact
contained-fixture commands in the preceding milestone documentation. The
preflight reads its calibrated covariance and native design, not fitted Truth
corrections. Once the fixed prospective fixture has been validated, `--step all`
generates its own nominal XML and immutable channels and needs no external
simulation dataset. Each candidate is independently checked for actual module
and layer containment before reconstruction; Geometry activation is never
part of this validation workflow.

Inspect `validation/rotation.root` with ROOT TBrowser, for example:

```sh
bash environment/run.sh root -l \
  result/native_multi_scope_b_seed1_positive_20261024_02/validation/rotation.root
# In an interactive ROOT session: new TBrowser;
```

The nine histograms are nominal/corrected/control chi2 and local u/v residuals.
The chi2 histograms use ACTS stored NDF (ten measurement coordinates per track),
while the independently profiled Pede model has four local track parameters
and eight selected global parameters. Their denominators must not be confused.

## Configured three-sensor alignment

Scope C, `l1_l2_y_rx_ry_rz_l3_y`, has passed nine-parameter native closure:
L1/L2 Y/Rx/Ry/Rz plus L3 Y, with L0/L4 fixed and every Global X/Z fixed.
Scope D, `l1_l2_l3_y_rx_ry_rz`, has now also passed the four prospectively
fixed signed fixtures described below. Both scopes remain experimental
zero-field tests with no assigned ACTS material.

The corresponding JSON files in `validation/telescope_alignment/` explicitly
declare `aligned_sensors`, component lists, actual VolumeID/GeometryIdentifier,
fixed references, coordinate/pivot conventions and unchanged containment rules.
Parameter rows retain the established Mille labels. Actual L3 identity is
VolumeID 272635935 and ACTS GeometryIdentifier 216173331869597983. Its labels
are 700302 (Y), 700304/700305/700306 (Rx/Ry/Rz); only Y is free in C.
The processor still verifies these declarations against actual native sensor
associations. No Truth injection values are passed in the alignment JSON.

The physical fixtures retain L1/L2 values and add L3 Y=+0.050 mm. For the positive Scope D fixture,
L3's rotation vector is (+0.8,-0.4,+0.4) mrad. New beam JSON files
`three_sensor_beam_seed1.json` and `three_sensor_beam_seed2.json` declare seeds
2026102801/2026102802 with the unchanged bounded recipe. The initial N=4096,
strict sensitivity/containment gates, chi2 cut 1000 and one explicit additional
correction were declared before fitting. Negative fixtures reverse rotations
only and share rays within a seed. No seed is replaced after seeing its fit.

These exact commands were executed for Scope C; outputs already exist. Choose
unused build/result/preflight names before repeating them:

```sh
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_three_sensor_c_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_three_sensor_c_20261024_01 -j2
# The unchanged existing geometry executable was used for the prospective check.
bash environment/run.sh python3 -B validation/telescope_closure/multi_preflight.py \
  --build build/native_multi_precision_20261024_01 \
  --prior-run result/native_multi_scope_b_seed1_positive_20261024_02 \
  --output-dir result/native_three_sensor_20261024_01_audit/geometry_preflight_c \
  --mode l1_l2_y_rx_ry_rz_l3_y
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build build/native_three_sensor_c_20261024_01 \
  --result result/native_three_sensor_scope_c_seed1_positive_20261024_01 \
  --mode l1_l2_y_rx_ry_rz_l3_y --events 4096 \
  --beam validation/telescope_alignment/three_sensor_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

The preflight's local prior native dataset is not a Git asset; the previous
Scope B recipe can regenerate it under a fresh path. It supplies original
calibrated covariance and derivatives for the engineering preflight, not Truth
corrections. New high-dimensional checks use sensor-marginal covariance samples
lifted into the full correlated ellipsoid. Old 5/8 sampling is unchanged. This
is sampled engineering validation, not exhaustive containment or coverage.
The optional `--target-events` forecast is engineering-only and was not used
for C: actual N=4096 passed. Every actual solve must separately pass the strict
native information/sensitivity gates before Pede.

Inputs/outputs and independent stage commands remain those of the multi-sensor
workflow above. All three sensors use the same correction implementation and
actual fresh Geometry reload; no new provider, fitter, navigator or solver is
introduced. C's `validation/report.json` contains all nine estimates, original
nominal uncertainties, full covariance, actual cumulative matrices, Geometry
errors, hashes and solver diagnostics. `validation/rotation.root` contains the
same nine TBrowser histograms. C recovered Y=(80.007625,-59.906822,50.174805) um,
with ACTS chi2/stored-NDF 12.237088→0.604573. The parity report records the weak
tilt components as well as the successful closure gates; numerical convergence
does not establish exact Truth/sign recovery or uncertainty coverage.

### Scope D reproduction and cohort accounting

All four prospectively fixed Scope D fixtures have passed full closure and
independent audits. See the parity report for the final regression and
preservation status. Scope D is a bounded experimental capability; the preset does not
license arbitrary unvalidated sensor/component selections.

The primary twelve-parameter command uses the same build as C:

```sh
bash environment/run.sh python3 -B validation/telescope_closure/multi_preflight.py \
  --build build/native_three_sensor_c_20261024_01 \
  --prior-run result/native_three_sensor_scope_c_seed1_positive_20261024_01 \
  --output-dir result/native_three_sensor_20261024_01_audit/geometry_preflight_d \
  --mode l1_l2_l3_y_rx_ry_rz
bash environment/run.sh python3 -B validation/telescope_closure/closure.py \
  --build build/native_three_sensor_c_20261024_01 \
  --result result/native_three_sensor_scope_d_seed1_positive_20261024_01 \
  --mode l1_l2_l3_y_rx_ry_rz --events 4096 \
  --beam validation/telescope_alignment/three_sensor_beam_seed1.json \
  --chi2-cut 1000 --refine-once --step all
```

The prospective cohort table fixes the other commands by substituting the
listed result path, mode and beam file. Run these only after the primary
cohort's full validation succeeds; never replace a failed seed. These paths
are execution records, so choose fresh names when reproducing the experiment.

| Fixture | Result directory under `result/` | Mode | Beam JSON under `validation/telescope_alignment/` |
|---|---|---|---|
| seed1 positive, primary | `native_three_sensor_scope_d_seed1_positive_20261024_01` | `l1_l2_l3_y_rx_ry_rz` | `three_sensor_beam_seed1.json` |
| seed1 negative, paired | `native_three_sensor_scope_d_seed1_negative_20261024_01` | `l1_l2_l3_y_rx_ry_rz_negative` | `three_sensor_beam_seed1.json` |
| seed2 positive | `native_three_sensor_scope_d_seed2_positive_20261024_01` | `l1_l2_l3_y_rx_ry_rz` | `three_sensor_beam_seed2.json` |
| seed2 negative, paired | `native_three_sensor_scope_d_seed2_negative_20261024_01` | `l1_l2_l3_y_rx_ry_rz_negative` | `three_sensor_beam_seed2.json` |

The seeds are 2026102801 and 2026102802. There are two independent ray samples,
not four: signed pairs share the same rays, and C shares seed1 rays with D.
Each fixture has its own immutable shifted RawHit ROOT file. Identity is
required across alignment iterations within that fixture, not between
different physical injections. Only rotations change sign; Y stays
(+0.080,-0.060,+0.050) mm on L1/L2/L3. No Truth collection is supplied to
the alignment reconstruction.

Each closure can also run stage by stage using the existing `--step` interface:
`geometry`, `data`, `nominal`, `solve`, `correct`, `corrected`, `postsolve`,
`refine`, `refined`, `refinesolve`, `control`, `controlsolve`, `check`.
Keep all other arguments identical, including `--refine-once`. Every stage
refuses to reuse its own output directory; a failed stage remains evidence
and must be investigated before a new run. `solve` checks the actual native
information matrix and real-Geometry derivatives before executing Pede.

The ROOT output remains `validation/rotation.root` inside each run. The final
`corrected_*` histograms use the refined reconstruction when refinement was
requested; the report separately retains the first corrected pass. ACTS
stored NDF counts ten calibrated coordinates per track. The Pede model has
four local parameters per track and twelve selected global parameters, giving
statistical NDF `6*N-12`. Neither denominator is changed to force a ratio of one.

The four Scope D fixtures accept 4096 tracks each in every reconstruction.
Their ACTS chi2/stored-NDF changes are 12.360223→0.607925 (seed1 positive),
12.503304→0.602174 (seed1 negative), 12.426350→0.612096 (seed2 positive), and
12.441506→0.598861 (seed2 negative). Sixteen Pede solves finish normally,
without rejected local fits or error scaling. The parity report contains all
48 parameter estimates and the complete primary 12x12 covariance; every run's
`validation/report.json` retains its full initial covariance and actual final
Geometry matrices. Independent consolidated evidence is under
`result/native_three_sensor_20261024_01_audit/scope_d_four_fixture_summary/`.

The limiting nuisance-profiled sigma is 0.499646454 mrad, close to the unchanged
0.5 mrad sensitivity bound. Some weak Ry/Rz estimates have signs opposite to
Truth. These two independent seeds validate the declared technical closure,
not component-sign precision, bias or uncertainty coverage. No general six-DOF
fit or automatic Controller is enabled. No Geometry is activated.

The final regression receipt passes all 23 historical cases and an independent
artifact/field seal, the separate 18-command suite with 102 unit tests, the
historical 99-track reference, expected containment refusal and nine pinned
upstream patch reproductions. Final safety and frozen preservation checks
also pass. The parity report retains the resolved audit-wrapper marker-boundary
incident and both its failed and corrected receipts. Existing data, numerical
tracking/alignment sources, measurement settings and installed libraries are
preserved; only the three technical documents change after the C implementation
commit. All generated outputs stay local under `result/`.

## Native iterative Calibration Controller

The bounded native implementation is available through
`python3 -m calibration.native_controller`, separately from the retained legacy
`calibration.controller`. Use the [complete Controller guide](NATIVE_CALIBRATION_CONTROLLER.md)
for build/start/status/verify/resume commands and independently executable
manual-equivalence, real interruption/restart and physical-refusal tests.
It requires only immutable native channel data, an initial Geometry and a
validated sensor/parameter configuration; Truth is read only by independent
post-completion validation. It does not activate Geometry.

The four existing configured scopes A/B/C/D are accepted. Scope D fits L1/L2/L3
Y/Rx/Ry/Rz with fixed L0/L4 and fixed X/Z translations. The default maximum is
three corrections, with one final fresh evaluation needed to certify the last
candidate. Default minimum one stops the 4,096-event reference after one
correction; an explicit minimum-two validation protocol matches the manual
two-correction contract. Their final chi2/stored-NDF values are respectively
`0.607925838664596` and `0.6079249182432249`, starting at `12.360222868341953`.
Both preserve 4,096 tracks and exact manual states/Mille/Geometry equivalence.

Initial data-only information, covariance and formal errors remain fixed for
convergence; no Euler-angle or successive-fit covariance summation is used.
Remaining-update consistency is distinct from Truth accuracy and uncertainty
coverage. The Controller guide records the thresholds, complete pose matrices,
weak-angle limitations and actual interrupted/failed outputs.
