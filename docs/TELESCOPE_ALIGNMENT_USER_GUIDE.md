# Native ePIC telescope calibration: practical guide

This experimental offline workflow transports electrons with npsim/Geant4,
digitizes real DD4hep SimTrackerHits with installed EICrecon algorithms, fits
immutable RawHits with native ACTS, writes official Mille Binary records, runs
Millepede-II, and evaluates a physically checked Geometry Correction with a
fresh reconstruction. Candidates remain unapproved and are never activated.

The public entry is `python3 -B -m calibration.workflow`. Detailed historical
synthetic protocols are preserved in [the fixture manual](NATIVE_FIXTURE_PROTOCOLS.md).
Use [the code map](TELESCOPE_ALIGNMENT_CODE_MAP.md) for source ownership and
[the Geant4 audit](NATIVE_GEANT4_WORKFLOW.md) for earlier numerical evidence.
The current integration results are recorded separately in
[the workflow milestone](NATIVE_WORKFLOW_VALIDATION.md).

## Scope and prerequisites

The seven real planar sensors use the validated barrel-compatible DD4hep
representation so that the installed EICrecon `ActsGeometryProvider` constructs
TrackingGeometry and SurfaceMap. This is a telescope along Global +X at
X=250–550 mm, not the older +Z endcap telescope. The native workflow refuses
incompatible Geometry/CellIDs. Never reuse old +Z RawHits as radial-beam data.

Full reconstruction currently supports **1 GeV gun energy, electrons, zero
magnetic field and material-free ACTS tracking**. Its existing seed prior and
measurement uncertainties are unchanged. Geant4 transport includes the configured
material and physical interactions; those effects are not modeled by this ACTS
fit. Alternative particles/energies are available in `simulation.native` alone;
the complete workflow rejects them before producing data. This prevents a silent
mismatch with the existing electron seed.

Required software is supplied by the fixed Docker image in `environment/run.sh`:
EICrecon `195966d41899800eaeca6fbafd63cd53735e6543`, ACTS 45.3.0,
DD4hep 1.36, Geant4, npsim, ROOT/PyROOT, podio/EDM4hep/EDM4eic,
NumPy, CMake and C++20. Millepede-II and `libMille2.so` must already be under
`external/install/`. On a fresh clone only, prepare these dependencies:

```bash
bash environment/run.sh python3 environment/setup_dependencies.py
```

Do not run setup over an existing installation. Dependency revisions are in
`environment/dependencies.json`. No private reference ROOT file is needed for
these new simulations. Historical preservation/regression checks additionally
need the local datasets listed in `validation/README.md` and the preservation
manifests; Git does not contain those datasets.

## Build and run

Run from the repository root. `environment/run.sh` creates a fixed-image container
or uses `TESTBENCH_CONTAINER` when an existing compatible container mounts this
checkout at `/work`. Existing output directories are refused. Choose new build
and result names for a rerun.

```bash
# Optional: use an already running compatible container.
export TESTBENCH_CONTAINER=sweet_mahavira

bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_telescope \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_telescope -j2

# Small, nonzero single-L1 Global Y displacement; explicit offline diagnostic mode.
bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_smoke.json \
  --output-dir result/native_smoke \
  --build build/native_telescope --validation-mode diagnostic

# Independent larger example using the same public interface.
bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_example.json \
  --output-dir result/native_example \
  --build build/native_telescope --validation-mode diagnostic
```

The examples inject L1 Global Y +0.080 mm in simulation Truth Geometry; initial
reconstruction uses a nominal Survey Geometry. Controller inference receives no
Truth coordinates. The positive recovered parameter moves the candidate toward
positive Global Y. The example's capture cut 1000 is explicit and identical in
all reconstruction passes; default 15 remains in the independent benchmark.
Errors, Kalman weights, Mille equations and Pede steering are unchanged.

Run `python3 -B -m calibration.workflow run --help` inside Docker for overrides:
Geometry, initial Geometry, particle/energy/distribution, event count/seed,
alignment configuration, output, build/environment and maximum iterations.
Configuration snapshots record effective values after overrides. The maximum
iteration setting counts applied corrections (1–3), followed by an additional
fresh verification fit using the same RawHit bytes.

## Stages, inputs and outputs

| Stage | Input | Principal output / success evidence |
| --- | --- | --- |
| Preparation | Example configuration or explicit compatible XML; initial Survey XML | `preparation/{truth,initial}.xml`, actual DD4hep/ACTS identities and containment audits |
| Simulation | Truth XML; explicit gun settings, N and seed | `simulation/transport/events.edm4hep.root`, generator QA, software and exact command records |
| Official Digitization | Verified completed Simulation producer | `raw/digitization/digitized.root`, official factory/library provenance |
| Raw projection | Digitized ROOT and readout identities | `raw/projection/channels.root`, producer receipt and every exclusion reason |
| Initial reconstruction | Survey Geometry, immutable channels, selected parameters | Controller iteration000: `reco.root`, `audit.json`, `mille.dat`, physical derivative audit |
| Alignment | Native Mille Binary; unchanged Pede settings | `.res`, `.end`, logs, independently checked information/estimates/errors |
| Geometry Correction | Finite identifiable update; current Geometry | Unapproved `candidate.xml`, XML whitelist and physical containment checks |
| Fresh reconstruction | Candidate Geometry; identical channels | Further Controller iteration, updated residuals/chi2 and estimates |
| Reporting | Verified Controller history | `report/{summary.json,report.md,diagnostics.root}`, `run_manifest.json` |

Projection requires exactly one valid digitized cell per SiMAPS L0–L4. It does
not select on Truth or fitted residuals. Full digitization and excluded events
remain available. Controller requires stable track/measurement identities;
rejected or changing reconstruction samples are not silently discarded.

Inspect `run_manifest.json` for important artifacts and actual stage commands.
`configuration/` contains the requested/effective configuration, source/build
identities and software versions. Controller stores every request, log, solver
file, Geometry version and sealed checkpoint. Raw bytes and channel payload
checksums are verified across iterations.

## Independent execution and debugging

Each public step can run separately with the same sealed configuration:

```bash
bash environment/run.sh python3 -B -m calibration.workflow prepare \
  --config calibration/config/native_workflow_smoke.json \
  --output-dir result/native_steps \
  --build build/native_telescope --validation-mode diagnostic
bash environment/run.sh python3 -B -m calibration.workflow simulate --run-dir result/native_steps
bash environment/run.sh python3 -B -m calibration.workflow digitize --run-dir result/native_steps
bash environment/run.sh python3 -B -m calibration.workflow calibrate --run-dir result/native_steps
bash environment/run.sh python3 -B -m calibration.workflow report --run-dir result/native_steps
```

For lower-level debugging, `simulation.native`, `digitization.native` and
`calibration.native_controller` retain their independent CLIs. Digitization
requires `--simulation-stage` pointing to the completed producer parent, not
its `transport/` subdirectory. Controller requests also allow independent stage
execution with `stage --request PATH`; copy the request to a fresh output path
before replaying a failed operation. Never reuse or edit a sealed artifact.

An interrupted Controller can resume its last completed checkpoint:

```bash
bash environment/run.sh python3 -B -m calibration.native_controller resume \
  --run result/native_steps/controller
```

Resume requires unchanged input, source set, runtime libraries and build bytes.
Partial attempts are preserved. Diagnose the first failing `exit.json`,
`failure.json`, `stdout.log` or Geometry audit. Use a new public run when inputs
or implementation change. Explicit stale-lock recovery is documented in
[the Controller guide](NATIVE_CALIBRATION_CONTROLLER.md).

## Change sensors and inspect results

Use `calibration/config/native_workflow_multi.json` for the existing five-parameter
L1 Y/Rx/Ry/Rz plus L2 Y scope. It changes configuration, not the implementation.
Its wider beam/2304 events support the declared rotation parameters. Other
maintained explicit-sensor configurations require their own observability and
containment checks. The public workflow rejects unknown configurations rather
than enabling unvalidated degrees of freedom.

```bash
bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_multi.json \
  --output-dir result/native_multi \
  --build build/native_telescope --validation-mode diagnostic

root --web=off -l 'visualization/browse.C("result/native_smoke/report/diagnostics.root")'
```

The ROOT file contains native alignment/chi2/residual histories and Geometry
comparison objects. Use `TBrowser` to inspect saved objects; individual
reconstruction ROOT files remain indexed by the run manifest. No HTML viewer or
additional visualization package is required.

## Interpret completion correctly

**Engineering success** means every stage completed, estimates were numerically
interpretable and identifiable, a physically contained candidate was produced,
and fresh reconstruction used unchanged channels. **Physics validation** also
requires demonstrated bias/coverage, justified material/covariance models and
acceptable statistical quality; this milestone does not establish those claims.
**Integrity failure** includes wrong IDs, corrupted inputs, invalid Geometry,
nonfinite estimates, rank failure or invalid solver output and always stops.

Strict validation remains the default Controller policy. It refuses Pede
warnings and unmet established precision targets. Explicit `--validation-mode
diagnostic` permits only the recognized high-chi2 advisory when Pede exits
successfully, rejects no local fits, and agrees with independently profiled
normal equations. Nominal errors and every warning are retained. No suggested
error scale is applied. Diagnostic candidates are unapproved, even if the
same-data convergence criteria pass. A bounded iteration limit may complete an
engineering demonstration while remaining nonconverged and scientifically
unvalidated; the report exposes both facts.

ACTS chi2/stored-NDF uses the stored measurement dimensionality (10 per complete
five-plane track). It is not a statistical reduced chi2. The independent
four-parameter straight-line Mille fit instead has 6 local residual degrees of
freedom per track; Pede subtracts the fitted global-parameter count from the
ensemble total. Reported ACTS and Pede ratios therefore have different meanings.

A trajectory missing the finite active bounds of an unused detector may have
fewer holes. The opt-in public path verifies the actual filtered tangent with
the installed ACTS Navigator and independent bounded intersections. Wrong,
missing or duplicate crossings still fail. The old synthetic default observer
and its historical two-hole expectation remain available for regressions.

The same opt-in audit distinguishes intrinsic pixel coordinates from serialized
EDM positions. Official Hit Reconstruction stores global positions as float32;
measurement conversion stores local coordinates as float32 again. After a
rotation, identical Raw channels can therefore produce adjacent local float32
values. The Controller requires exact intrinsic segmentation-coordinate and
pixel-dimension identity plus exact per-Geometry serialization checks. It does
not increase the old universal coordinate tolerance or modify measurements.
The intrinsic coordinate is the pixel center decoded from CellID, not a
Simulation Truth position.
