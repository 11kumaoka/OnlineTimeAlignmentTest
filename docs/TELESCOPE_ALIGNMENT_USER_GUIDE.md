# EICrecon-based telescope alignment user guide

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
