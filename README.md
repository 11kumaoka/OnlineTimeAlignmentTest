# Local Detector Alignment Research

An experimental, offline ePIC telescope calibration workflow:

```text
npsim / Geant4 -> DD4hep SimTrackerHits -> official EICrecon Digitization
-> immutable RawHits -> native ACTS tracking -> native Mille Binary
-> official Millepede-II -> physically checked Geometry Correction
-> fresh reconstruction of the same RawHits -> Controller JSON / ROOT report
```

Start with the **[practical telescope user guide](docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md)**.
The [code map](docs/TELESCOPE_ALIGNMENT_CODE_MAP.md) identifies upstream components
and every remaining telescope adapter. The [workflow validation report](docs/NATIVE_WORKFLOW_VALIDATION.md)
separates technical completion, physics quality and integrity failures.

## Quick start

Use the fixed Docker image selected by `environment/run.sh`; this checkout is
mounted at `/work`. Dependencies include EICrecon, ACTS 45.3.0, DD4hep, Geant4,
npsim, ROOT/PyROOT, podio and NumPy. Millepede-II must be in `external/install/`.
On a **new checkout only**, run
`bash environment/run.sh python3 environment/setup_dependencies.py`.
Do not reinstall over existing dependencies.

All build/result names must be unused. An existing compatible container can be
selected with `TESTBENCH_CONTAINER`; otherwise the wrapper launches the pinned image.

```bash
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_workflow_20261025_02 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_workflow_20261025_02 -j2
bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_smoke.json \
  --output-dir result/native_workflow_smoke_20261025_03 \
  --build build/native_workflow_20261025_02 --validation-mode diagnostic
```

This example uses 64 independent Geant4 events with a 1 GeV electron gun along
Global +X and a physical +0.080 mm L1 Global Y displacement. The existing native
seed supports this particle/energy contract; other full-reconstruction contracts
are rejected explicitly. The 256-event broad-beam example is
`calibration/config/native_workflow_example.json`. A five-parameter L1/L2 example
uses `native_workflow_multi.json` through the same interface.

Read `run_manifest.json` and `report/{report.md,summary.json,diagnostics.root}`.
Open the ROOT file with `visualization/browse.C` and TBrowser. The public CLI also
provides independent `prepare`, `simulate`, `digitize`, `calibrate` and `report`
commands. Each underlying Controller operation remains independently executable.
See the guide for overrides, I/O, debugging, restart and exact commands.

## Validation boundary

Technical completion is **not physics-quality validation**. Geant4 models
transport through the configured material; this ACTS reconstruction remains
zero-field and material-free. Bias, nominal-error coverage and material/covariance
adequacy are not certified by same-data convergence.

The Controller's default strict policy remains available. Explicit offline
`diagnostic` mode may evaluate an unapproved candidate after a recognized high-chi2
Pede advisory. It retains all warnings and nominal errors, never applies the
suggested error scaling and never activates Geometry. Requested-parameter rank,
finite solver output, detector associations, unchanged RawHits and physical
containment remain mandatory. Unknown warnings or genuine integrity failures stop.
Actual finite sensitive-surface crossings are checked with the installed ACTS
Navigator, rather than assuming a fixed number of unused-detector holes.

## Repository map

| Path | Responsibility |
| --- | --- |
| `localDetEICrecon/` | Native telescope plugins and retained BeamTestReco source |
| `geometry/` | Physical transforms, nominal Geometry and legacy scenarios |
| `simulation/`, `digitization/` | Independent transport and official RawHit production |
| `reconstruction/`, `alignment/`, `correction/` | Retained independent stages and shared alignment utilities |
| `calibration/` | Public workflow, native Controller, policy and shared operations |
| `validation/` | Unit/integration tests, sensor configurations and preservation manifests |
| `visualization/` | ROOT visualization and browser macro |
| `environment/` | Fixed Docker launcher and dependency/build setup |
| `docs/` | Practical guide, architecture and detailed research records |
| `result/`, `build/`, `external/` | Ignored generated runs, local builds and dependencies |
| `results/` | Ignored historical reference data; preserved unchanged |

New simulations need no private ROOT input. Historical regressions require local
reference datasets described in [validation/README.md](validation/README.md);
they are not stored in Git. Generated ROOT, Mille, logs, builds and installations
are excluded from version control. Maintained comments and technical documents
use English.

The original +Z BeamTestReco workflow remains separately supported, with the
[legacy Workflow Guide](docs/WORKFLOW.md), [RawHit contract](docs/RAWHIT_BOUNDARY.md)
and [legacy Controller guide](calibration/README.md). Do not reinterpret its data
as the native +X telescope input. The preserved 99-track regression and later
z=-500mm electron results retain their original meaning.

Historical native synthetic closure, signed rotations/SO(3), multi-sensor scopes
and manual protocols are retained in the [fixture manual](docs/NATIVE_FIXTURE_PROTOCOLS.md)
and linked numerical reports. The [initial npsim audit](docs/NATIVE_GEANT4_WORKFLOW.md)
preserves earlier failed attempts as well as successful integration evidence.
