# Reconstruction-based barrel alignment closure

## Result and scope

The complete readout-level loop passed with **32 deterministic tracks**:
Truth sensors → quantized channels → nominal JANA reconstruction → native
TrackStates/Mille → official Pede → new DD4hep Geometry → a second JANA
reconstruction of the **same channel ROOT file**. A separate 32-event
no-misalignment control also passed.

| Quantity | L1 | L2 |
|---|---:|---:|
| Injected physical Global Y shift [um] | +150.000 | +200.000 |
| Recovered/applied shift [um] | +149.140 | +203.180 |
| Remaining Geometry bias relative to Truth [um] | -0.860 | +3.180 |
| Formal nominal uncertainty [um] | 2.193 | 2.051 |
| Declared closure tolerance: 5 nominal errors [um] | 10.963 | 10.255 |
| RecHit minus physical intersection Global Y mean, nominal [um] | -149.982 | -203.932 |
| Same mean, corrected [um] | -0.842 | -0.752 |
| Remaining Pede correction after reconstruction [um] | -0.000449 | +0.002877 |
| No-misalignment control correction [um] | -2.415 | +0.750 |

Nominal, corrected and control passes each processed/accepted **32/32 events**,
with five SiMAPS measurements, zero outliers and two expected MPGD/AC-LGAD
holes per track. Each produced 32 official Mille records / 320 scalar equations.

| Reconstruction | ACTS chi2 sum | ACTS stored NDF sum | chi2 / stored NDF |
|---|---:|---:|---:|
| Nominal Geometry | 11893.541016 | 320 | 37.167316 |
| Corrected Geometry | 221.071725 | 320 | 0.690849 |
| Nominal no-misalignment control | 205.203155 | 320 | 0.641260 |

All 32 individual chi2 values decreased in this sample; only aggregate
improvement is required. The corrected physical placements agree with Truth
within the declared finite-sample tolerance. Near-zero subsequent corrections
show self-consistency of the fitted Geometry, not exact knowledge of Truth.

This is **synthetic quantized-channel, zero-field, material-free closure**.
It is not Geant4, electronics, material/scattering or uncertainty-coverage
validation. No additional alignment degrees of freedom are enabled.

## Preservation and environment

The previous native Mille milestone was reviewed/revalidated and committed
locally as `f0d15a97aed49386021ea6b6d980b19bfcdfe970`
(`Validate native ACTS measurement equations and Mille integration`).
Its one-event reconstruction/read-back, derivative evidence, historical writer
comparison, 16-ray mathematical fixture, 46 tests and preservation checks passed.
This milestone's changes remain uncommitted. Nothing was pushed or merged.

The fixed Docker environment remains EICrecon
`195966d41899800eaeca6fbafd63cd53735e6543`, ACTS 45.3.0 and DD4hep 1.36.
Installed packages and the separate upstream checkout were not edited.
The production endcap/BeamTestReco alignment, Controller, SO(3), nominal source
Geometry and historical 99-track/other results remain preserved. Corrected
Geometry exists only in the new result directory; no production activation
or conditions update occurs.

## Actual data and processing flow

1. The existing barrel fixture builder writes a fresh nominal seven-plane XML.
   L1/L2 module definitions are cloned only in the new Truth XML, allowing
   their sensitive components to move independently. L0/L3/L4 and both
   unmeasured detectors stay fixed.
2. `BarrelChannels` runs offline against the **Truth DD4hep Geometry**. For each
   ray and sensor it obtains the actual sensitive-frame transform, intersects
   the physical plane, converts to sensor-local coordinates and calls the real
   `SiMAPSHits` CartesianGridXZ segmentation's `cellID`. It checks the bounded
   sensitive area, sensor identity and half-pixel quantization bounds.
3. Python packs only `EventHeader` and `TelescopeChannels`
   (`edm4eic::RawTrackerHitCollection`) into PODIO ROOT. CellID, charge and
   timestamp are the channel payload. Truth trajectories/intersections are
   stored in a **separate offline JSON**, never in the reconstruction input.
4. In a fresh installed `eicrecon` process, the unchanged official
   `TrackerHitReconstruction_factory` decodes those CellIDs using **nominal
   Reconstruction Geometry** and preserves RawHit relations. Its standard
   pitch/sqrt(12) covariance convention is retained.
5. The same maintained EICrecon-style factories run TrackerHit → adapted
   TrackerMeasurementFromHits → TelescopeSeed → adapted CKFTracking → installed
   ACTS CKF/Navigator/smoothing → unchanged ActsToTracks. The seed uses only
   reconstructed endpoint hits and the established 1 GeV electron beam prior.
6. The existing native TelescopeMille observer consumes actual accepted
   TrackStates, SourceLinks and calibrated measurement covariance. It writes
   one record per accepted event using the unchanged NativeMilleModel,
   ACTS transport/surface derivatives, whitening and local elimination.
7. Official Pede fits only physical Global Y labels **700102 / 700202**. The
   correction reads its actual text results and nominal XML; it never reads
   Truth. It writes a separate corrected XML.
8. A **new clean eicrecon process** rebuilds DD4hep Geometry, TrackingGeometry
   and SurfaceMap from corrected XML, then decodes/reconstructs the original
   immutable channels again. A further Pede solve diagnoses the remaining
   corrections. The no-misalignment control uses its own nominal-channel file.

The input ROOT file SHA256 is
`4ebc637926ee7e107877c53ad424dc16c41cf8afa10e20612a52f451f1bd6950`.
Its canonical event/channel payload SHA256 is
`d0c1be6ec40aa9bfa95e0e9c2bf42aaf1b05fa5b4147c3fddf272c2d5871c6b1`.
Both nominal/corrected completion records contain these identical hashes.
ROOT read-back verifies exact CellID/charge/timestamp/event identity and the
RawHit, Measurement, Seed and Track/Trajectory relations. It separately checks
that seed position/direction follow reconstructed hits, not Truth.

The 32 rays have varied transverse positions (within +/-12 mm Y, +/-10 mm Z)
and slopes (within +/-8 mrad dy/dx, +/-6 mrad dz/dx). Their deterministic recipe
is recorded in source and the offline channel JSON. Pixel pitch remains
**0.034641 mm** in both SiMAPS readout coordinates. Charge=1 and timestamp=0
are synthetic placeholders; electronics behavior is not modeled.

## Geometry correction and conventions

Only L1/L2 physical Global Y center translations are free. All other poses
and alignment degrees of freedom are fixed. VolumeIDs and closed ACTS
GeometryIdentifiers are unchanged across all three Geometries.

The existing Controller/correction path targets the original endcap hierarchy
and established labels/sign conventions. Forcing this barrel XML/physical
label pair through that path would require unrelated changes. Instead, the
bounded experimental adapter reuses `geometry.transforms.matvec/transpose`
and `alignment.align.read_pede`.

The validated barrel module frame is module X = -Global Y, module Y = -Global Z,
module Z = Global X. A positive Global Y correction therefore becomes a
negative module-X sensitive-component translation. There is no sign reversal
of the Pede parameter itself and no rotation/pivot update for this translation.

Independent DD4hep/ACTS placement audits confirm the applied sensor-center
changes, unchanged references/rotations and identical IDs. An XML whitelist
check includes attributes **and text**, preserving dimensions, materials,
segmentation, CellID encoding, rotations and all nonselected placements.
Per-event validation confirms identical local measurements/covariances and
that only the intended reconstructed global hit positions move.

## Selection, mathematical checks and solver diagnostics

A four-event pilot with the upstream default measurement-selector chi2 cut
15 accepted **0/4** misaligned tracks. Its outputs are retained. The controlled
closure therefore uses an explicit capture window **1000**, identically in
nominal, corrected and control passes:

```text
-PTelescopeTracking:TelescopeCKF:Chi2CutOff=1000
```

This changes selection only, not measurement errors, Kalman weights, seeding,
fitting or Pede settings. Each plane has one candidate hit, so no extra
combinatorial ambiguity is introduced. The default one-event benchmark still
uses cut 15. The driver refuses mixing selection cuts between closure passes.

The two-parameter profiled information matrix has rank 2 and condition number
**1.75814**. All local designs have rank 4. Native Jacobian/FD gates are rerun
for nominal and corrected Geometry. An independent absolute-coordinate
straight-line GLS calculation, using reconstructed measurements and current
Geometry only, agrees with the native Mille Schur solution for all three
passes. This oracle is validation-only; its values are never applied to Geometry.

Nominal native-record Schur solutions are +0.1491395075/+0.2031828718 mm;
standard Pede text gives +0.14914/+0.20318 mm. Comparisons allow its text
precision (6e-6 mm); the few-nanometer post-correction result includes this
round-trip and float-coordinate precision.

Official Pede uses unchanged `entries 5` and `method inversion 3 0.001`:

- Nominal and post-correction solves: process exit 0, end status **1 (warnings)**.
  Final chi2/NDF is approximately **221.068691 / 190 = 1.163519**. The log
  suggests multiplying input errors by 1.08; **no scaling was applied**.
- No-misalignment control: process exit 0, end status **0**, normally ended.
- Every solve reports no rank defect and **zero rejected local fits**.
- The official Mille decoder independently reads all 32 nominal records.

ACTS stored NDF=10 counts measured scalar coordinates per track. A four-local-
parameter spatial model has six statistical reference degrees per track;
Pede additionally fits two shared parameters, giving 32*6-2=190. Finite CKF
seed priors and numerical linearization explain small chi2-sum differences;
the native Mille equations use original measurement covariance and freely
profiled locals, not diagonal smoothed-residual errors.

The acceptance tolerance was declared as five unrescaled nominal errors,
10.963/10.255 um. An independent deterministic worst-case quantization bound
is +/-34.641 um for these corrections, and both checks pass. The zero-shift
control is within about 1.1/0.4 nominal errors of zero. A single deterministic
32-track cohort does not certify confidence coverage or a general uncertainty
model. Residuals and per-track chi2 arrays are retained; no errors or Truth
values were adjusted to improve closure.

## Files and reuse

| Source | Change / purpose |
|---|---|
| `localDetEICrecon/experimental/barrel/TelescopeTracking.cc` | Opt-in `channelInput` registers unchanged official TrackerHitReconstruction and empty association collector; original benchmark input remains default |
| `FactoryAudit.h` in that tree | Opt-in multi-event accounting, per-event diagnostics and reconstructed global positions; original single-event checks retained |
| `alignment/TelescopeMille.cc` | Opt-in multi-event append/flush, one record per accepted event, rejection accounting; numerical NativeMilleModel unchanged |
| `CMakeLists.txt` | Offline BarrelChannels validation target and private include path for a missing installed helper |
| `upstream_support/algorithms/meta/CollectionCollector.h` | Exact unchanged pinned upstream header, absent from installation but needed by its installed factory; license retained |
| `provenance.json`, `upstream_diffs/` | Source revision/hash and reproducible empty diff for that unchanged helper |
| `validation/barrel_alignment/BarrelMilleDerivatives.cc` | Additional geometry-only probe reference, avoiding any Truth/event-data dependency for the gate; previous audit-input mode retained |
| `validation/barrel_factories/prepare.py` | Fix unsupported Python Writer.finish call using the underlying pinned C++ ROOTWriter finalization API; fresh fixture generation now exits successfully |
| `validation/barrel_closure/BarrelChannels.cc` | Offline physical DD4hep readout fixture generation and actual pose/ID audit |
| `validation/barrel_closure/closure.py` | Focused independent stages using existing execution/preservation helpers; explicit two-sensor correction, matrix/read-back checks, ROOT output and consolidated regressions |
| This report, README links | Commands, evidence and scope |

No source was retired or deleted. Official Geometry services/provider,
TrackerHitReconstruction, ActsToTracks, native CKF, propagation and smoothing
are reused unchanged. Existing source-level measurement/CKF adaptations and
the Telescope seed producer retain their previous roles. Remaining unique
code is the telescope fixture/seed/configuration, narrowly bounded barrel XML
translation adapter and diagnostic observers. No replacement provider,
navigator, fitter, Controller or generalized framework is added.

## Actual outputs and regressions

Main run: `result/barrel_closure_20261024_03/`.
Fresh plugin build: `build/barrel_closure_20261024_01/`.

| Stage | Main output |
|---|---|
| geometry | `geometry/fixtures/nominal.xml`, `geometry/truth.xml` |
| data | `data/shifted.root`, `data/control.root`; separate offline Truth JSON and input hashes |
| nominal | `nominal/reco.root`, `audit.json`, `mille.dat`, `mille.json`, source-bound derivative gate |
| solve | `solve/millepede.res`, logs/status, independent Schur report |
| correction | `correction/corrected.xml`, provenance and actual DD4hep/ACTS placement audit |
| corrected | `corrected/reco.root`, native records/diagnostics from the same input |
| postsolve/control/controlsolve | Remaining-correction and zero-misalignment checks |
| final validation | `final_closure/report.json`, `final_closure/closure.root` |
| consolidated regressions | `final_regressions/complete.json`, per-command argv/log/exit records |

All **18 consolidated regression commands** passed: fresh builds of preserved
Geometry and standalone one-track sources, full Geometry/navigation/material
inventory checks, original one-track current JANA mode and ROOT read-back,
native/legacy writer equivalence, the separate historical mathematical fixture,
46 unit tests, safety and preservation checks. The fixed fixture writer exited
0. The original one-track CKF result remains unchanged. Protected checks cover
221 baseline records and 2046 relocated files, including the electron fitter
change. Historical 99-track data are preserved, not claimed as the new sample.

Earlier attempts remain intact: `_01` retains the partial writer-API failure;
`_02` retains the default-cut pilot and strict rejection of a wrongly qualified
CLI parameter; the first regression orchestration attempt used a colliding
fixture/log directory name. These software/orchestration errors were corrected,
and fresh result/build paths were used. Final suite evidence is
`final_regressions/`, not the incomplete earlier suite. Existing data, failed
outputs and checkpoints were never deleted or reused as write destinations.

## Reproducible commands and input/output

Run from the repository root. Choose fresh build/result names. The full closure
requires only maintained source plus the fixed software/Mille installation;
it does not use an old simulation or the previous mathematical fixture as input.
Historical preservation regressions additionally require the preserved local
reference datasets, as described by their existing manifests.

**WRITES OUTPUT** — isolated build:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake -S /work/localDetEICrecon/experimental/barrel \
  -B /work/build/barrel_closure_manual_01 -DCMAKE_BUILD_TYPE=Release \
  -DTELESCOPE_BUILD_MILLE_PROBE=ON
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  cmake --build /work/build/barrel_closure_manual_01 -j2
```

**WRITES OUTPUT** — complete readout-level closure and no-misalignment control:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_closure/closure.py \
  --build build/barrel_closure_manual_01 \
  --result result/barrel_closure_manual_01 \
  --events 32 --chi2-cut 1000 --step all
```

Default validation output for a fresh all-step run is
`result/barrel_closure_manual_01/validation/report.json` and `closure.root`.
The actual development run's latest independently repeated checks are in
`final_closure/`. `--validation-name NAME` selects a **new** check output;
for `--step regressions` it selects `NAME_regressions`. Existing stages refuse
reuse, including partial failures. Keep the chosen selector cut identical.

Every stage can instead be executed independently, using the same arguments:

```bash
# WRITES OUTPUT: use a fresh result directory instead of one already completed.
for stage_name in geometry data nominal solve correct corrected postsolve control controlsolve check; do
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
    python3 validation/barrel_closure/closure.py \
    --build build/barrel_closure_manual_01 \
    --result result/barrel_closure_steps_manual_01 \
    --events 32 --chi2-cut 1000 --step "$stage_name" || break
done
```

| Step | Inputs | Outputs / success evidence |
|---|---|---|
| geometry | Maintained nominal source and barrel builder | Fresh nominal/Truth XML; immutable hashes |
| data | Those XML files; deterministic ray recipe | Two channel ROOT files and separate offline Truth JSON; quantization/ID checks |
| nominal | Shifted channel ROOT + nominal XML | 32 accepted native tracks/records, PODIO output and diagnostics |
| solve | Actual nominal native Mille records | Pede results/status and independent rank-two Schur solve |
| correct | Nominal XML + actual Pede results | Fresh corrected XML, hashes and real pose/ID audit |
| corrected | **Same shifted channel ROOT** + corrected XML | New-process reconstruction/records with equal channel checksums |
| postsolve | Corrected native records | Small remaining corrections |
| control/controlsolve | Nominal-channel ROOT + nominal XML | Independent zero-shift reconstruction/solver check |
| check | All above stages and offline Truth for evaluation only | Geometry whitelist, data/EDM/seed/covariance checks, closure tolerances, ROOT diagnostics |

`--events` accepts 16–64; 32 is the executed cohort. No larger campaign is
launched automatically. `--step pilot` processes four events and can omit
`--chi2-cut` to demonstrate upstream-default capture behavior in a fresh result
containing completed geometry/data stages. Preserve its rejected outputs.

**WRITES OUTPUT** — consolidated source-based regressions after closure:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/barrel_closure/closure.py \
  --build build/barrel_closure_manual_01 \
  --result result/barrel_closure_manual_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name final
```

This creates separate fresh Geometry/benchmark build directories automatically.
It does not overwrite the plugin build or historical results. Each command's
argv, working directory, stdout and exit code are retained. The historical
16-ray fixture is run only as a separate regression, never substituted for the
32 reconstructed-track closure.

**CHECK-ONLY** — existing results and official binary structure:

```bash
git status --short
git diff --check
python3 validation/verify_preservation.py
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/external/install/lib:$LD_LIBRARY_PATH
  exec /work/external/install/bin/inspectMilleBinary \
    /work/result/barrel_closure_manual_01/nominal/mille.dat'
```

**CHECK-ONLY** — GUI inspection, on a ROOT-enabled graphical session:

```text
root -l result/barrel_closure_manual_01/validation/closure.root
root [0] new TBrowser;
```

`closure.root` contains nominal/Truth/corrected sensor-center graphs, per-layer
u/v and offline RecHit-minus-Truth distributions, saved canvases and per-track
chi2/stored-NDF histograms. Batch creation and object read-back were tested;
interactive GUI display was not exercised. Exact per-event arrays and mean/RMS
statistics are also in `report.json`.

## Remaining limitations

This closes the requested two-translation, synthetic readout-level loop through
real reconstructed tracks. It preserves the production workflow rather than
promoting the experiment automatically. Full Geant4/RawHit electronics studies,
material/process noise, magnetic-field alignment, additional parameters,
Controller integration and statistical uncertainty coverage remain separate
validation milestones. The present signal is not based on the earlier
standalone mathematical fixture, and no Truth information is used for
reconstruction, alignment inference or Geometry correction.
