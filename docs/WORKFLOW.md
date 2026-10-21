# Independent Research Workflow

Run commands from the repository root. Docker mounts it at `/work`.
`environment/run.sh` selects the pinned EIC image; `TESTBENCH_CONTAINER` selects
an existing container with that mount. Runtime login assets are isolated in
`result/.environment/`. ACTS 45.3.0, DD4hep 1.36, ROOT 6.38, EICrecon, JANA,
PODIO, EDM4hep/EDM4eic, NumPy, awkward, and uproot were used in validation.
See `validation/validated_environment.json` for recorded versions.

## Build and dependencies

```bash
bash environment/run.sh python3 environment/setup_dependencies.py
bash environment/run.sh bash localDetEICrecon/build.sh
```

The first command is only for a new checkout without `external/`. The setup
refuses overwrite and verifies source commits in `environment/dependencies.json`.
Offline clean clones can be selected with `--local-sources PATH`. Existing
`external/install/` provides `bin/pede`, `lib/libMille2.so`, and
`cmake/MilleConfig.cmake`; no legacy fallback is used.

The Plugin output defaults to `build/local_eicrecon_external/BeamTestReco.so`.
Use a **new** `TESTBENCH_BUILD_DIR` after moving sources; old CMake caches embed
source paths. Pass the chosen directory as `--build-dir` to both reconstruction
commands. `MILLEPEDE_PREFIX` selects a complete dependency installation;
`BUILD_JOBS` sets compilation concurrency. Disabling Mille support is unsupported.
`environment/build.sh` is the build implementation delegated to by
`localDetEICrecon/build.sh`; both configure `localDetEICrecon/CMakeLists.txt`.

## Ownership and configuration

| Task | Implementation | Editable configuration |
|---|---|---|
| Geometry Preparation | `geometry/prepare.py` | `--nominal geometry/nominal/seven_layer_telescope.xml`, `--geometry-config geometry/scenarios/L2_x200um.json` |
| Simulation | `simulation/simulate.py` | `--config simulation/configs/electron_1GeV.json` |
| Reconstruction before/after | `reconstruction/reconstruct.py` (`--after` for step6) | `--config reconstruction/configs/electron_1GeV.json`; step6 defaults to saved step3 settings |
| External Millepede-II | `alignment/align.py` | `--steering alignment/pede_template.txt` |
| Geometry Correction | `correction/correct_geometry.py` | saved scenario and label 1002; only L2 Global X |
| Numerical Validation | `validation/validate.py`, `validation/metrics.py` | optional `--reference validation/reference_metrics.json` |
| ROOT rendering | `visualization/closure.py`, `visualization/browse.C` | explicit Geometry/summary inputs; existing plot definitions |

The C++ Plugin and its in-process `BeamTestMilleProcessor` / `BeamTestMilleWriter`
are exclusively under `localDetEICrecon/`. The external solver is under
`alignment/`. `research_common.py` contains infrastructure only, with no detector
or physics model. Each wrapper executes its own Python module; direct module
invocation such as `python3 -m geometry.prepare --help` is also supported.
No central Python workflow or old-path compatibility package remains.

### Geometry

The unchanged nominal XML is independent of the scenario. The default is:

```json
{"detector":"SiMAPS","global_x_shifts_mm":{"2":0.2}}
```

The Geometry-only two-layer test uses:

```json
{"detector":"SiMAPS","global_x_shifts_mm":{"1":0.1,"2":0.2}}
```

Only canonical layer IDs `0`–`4` and finite numeric SiMAPS Global X shifts with
at most eight decimal places in mm are supported. Omitted layers stay nominal.
Unknown fields, Y/Z shifts, rotations, booleans, and unsupported layers are
rejected. The placement sign remains Global X = −ring r. Preparation copies
nominal XML, edits only the Simulation copy, runs geoConverter on both, and checks
actual exported GDML module placements. The verifier requires the present
origin-centered, unrotated, single-module-per-layer hierarchy.

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/two_layer_001 --geometry-config geometry/scenarios/L1_x100um_L2_x200um.json
```

Stop here for the two-layer study. Preparation does not run Geant4 or fitting.
`correction/correct_geometry.sh --result-dir result/two_layer_001 --check-only`
rejects unsupported correction without writing outputs. Full correction and
Validation enforce the same guard. The optional `validation/run_closure.sh`
preflights it before Simulation; it contains only shell argument routing and
sequential stage calls. Manual steps do not depend on that wrapper.

### Simulation

Edit `events` and `beam` in `simulation/configs/{electron_1GeV,muon_5GeV}.json`.
Fields preserve particle, energy_GeV, seed, theta/phi min/max (radians),
position_mm, and vertex_sigma_mm_ns (x/y/z/time). The gun distribution remains
uniform. Electron defaults: 100 events, 1 GeV, source (0,0,−500) mm, X/Y sigma
0.2 mm, theta 0.010–0.030, phi 0–2π, seed 2035032807. Muon defaults: 80 events,
5 GeV, otherwise the same gun conditions. No seed or physics changes were made.

`simulate.sh --sim-input PATH` reuses a ROOT file by link and records its checksum,
source, event count, and reuse mode. It creates no fictitious DDSim command record.
The saved config is the requested processing/generation configuration, **not proof
of the imported file's actual beam or Geometry**. The researcher must establish
provenance. In particular the historical 99-track input starts at z=0 mm.

### Reconstruction

Edit `pdg`, `q_over_p`, `use_mpgd`, and `use_aclgad` in
`reconstruction/configs/{electron_1GeV,muon_5GeV}.json`. They map to the existing
`outputTrackPDG`, `seedQOverP`, `useMPGD`, and `useACLGAD` Plugin parameters.
Electron uses PDG 11, q/p −1, SiMAPS-only fitting. Muon uses PDG 13, q/p −0.2,
MPGD enabled, AC-LGAD disabled. Select the matching Simulation and Reconstruction
configs explicitly; step1 no longer selects a particle case.

Unchanged command constants include single-thread execution, the Plugin list,
output collections, writer z reference 100 mm, single-track requirement, and
injected writer shift −1 (disabled). The CLI checks 10 scalar Mille measurements
per accepted track, so configurations changing accepted measurement dimensionality
need a separate validation change before use. Preserving the muon settings does
not claim a new muon/Mille regression. Internal ACTS surfaces, seed covariance,
material handling, residual uncertainties, and derivatives remain C++ assumptions.
The in-process writer's standalone default `results/manual/mille.dat` is preserved
as a C++ default; every maintained reconstruction command explicitly overrides it
with the new step-specific path. No new workflow output uses that default.

### Alignment and correction

`alignment/pede_template.txt` keeps the existing labels: 1000+layer for X and
2000+layer for Y. L0/L4 are fixed; L1–L3 X/Y are varied. No added constraints or
parameter definitions were introduced. The template contains `@MILLE_FILE@`;
the selected template is snapshotted into step4, then expanded with an absolute
step3 Mille Binary path. Pede runs in step4 and writes its own reports there.

Correction still negates the label-1002 measurement bias and applies only L2
Global X to the nominal XML. Other fitted components are not applied. A nonzero
scenario displacement outside L2 explicitly blocks Geometry Correction and full
Closure. Multi-layer fitting may be studied manually in a later task; it has not
been executed for the new two-layer scenario.

## Seven manual commands

Use a new child of `result/` without whitespace. `--result-dir` is the documented
convention (`--run-dir` is retained as a CLI spelling alias only).

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/manual_001 --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh bash simulation/simulate.sh --result-dir result/manual_001 --config simulation/configs/electron_1GeV.json
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/manual_001 --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/manual_001 --steering alignment/pede_template.txt
bash environment/run.sh bash correction/correct_geometry.sh --result-dir result/manual_001
bash environment/run.sh bash reconstruction/reconstruct_corrected.sh --result-dir result/manual_001
bash environment/run.sh bash validation/validate.sh --result-dir result/manual_001
```

The shell wrapper for step6 supplies `--after` to the shared reconstruction module.
It defaults to the immutable step3 config. Validation requires the same simulation,
Plugin, and reconstruction config hashes before comparing outputs.

| Step | Inputs | Outputs under `result/<name>/` | Success evidence |
|---|---|---|---|
| 1 | nominal XML and Geometry scenario | `step1/nominal.xml`, `misaligned.xml`, `geometry_config.json`, `placement_check.json`, `nominal_qa/`, `misaligned_qa/` | geoConverter succeeds; all seven placements verified |
| 2 | step1 misaligned XML; Simulation config or imported ROOT | `step2/events.edm4hep.root`, `config.json` | sufficient events; SiMAPS/MPGD/AC-LGAD hit collections |
| 3 | step2; step1 nominal; Plugin and Reconstruction config | `step3/reco.root`, `mille.dat`, `config.json` | nonzero tracks; event and Mille counters agree |
| 4 | step3 Mille Binary; steering template | `step4/steering_template.txt`, `pede.txt`, `millepede.res`, `.log`, `.his`, `.end` | pede status 0/1; L2 solution present |
| 5 | step4 fit; step1 nominal/scenario | `step5/corrected.xml` | supported capability and parsed XML |
| 6 | step2; step5 corrected XML; same Plugin/config | `step6/reco.root`, `mille.dat`, `config.json` | counters; provenance matches step3 |
| 7 | steps1–6 | `step7/summary.json`, `alignment.root` | metrics; optional reference test; ROOT objects |

Every completed stage has `complete.json` with checksums. Every executed subprocess
has `command.json`, `stdout.log`, and `exit.json`. Geometry subprocess records live
in their respective QA directories. Pure correction and imported Simulation have
no subprocess records. All completed regular output files, including nested QA
files, are hashed; dependent stages verify them. Source config changes cannot
silently alter existing snapshots. Missing prerequisites are refused; nothing
executes later stages automatically. Partial failures are retained; retry in a
new result directory rather than overwrite or fabricate completion markers.

## Regression and visualization

```bash
bash environment/run.sh bash validation/run_regression.sh result/regression_001
bash environment/run.sh python3 validation/check_root_outputs.py --result-dir result/regression_001
python3 validation/verify_preservation.py
python3 validation/check_safety.py
root --web=off -l 'visualization/browse.C("result/manual_001/step7/alignment.root")'
```

`run_regression.sh` optionally accepts a second BUILD_DIR argument. It reuses the
local historical input documented in `validation/README.md`. Expected: 99 tracks
before/after, L2 correction +198.75 μm, pooled L2 Rec−Sim −199.571 → −0.821 μm,
and Σχ² / Σstored ACTS nDoF 45.592 → 1.981. Reference tolerances are in
`validation/reference_metrics.json`. Do not apply this reference to fresh events.

Step7 stores `c_geometry`, `c_hit_residuals`, `c_closure`, at least 20 residual
histograms, and Closure TGraphs. ROOT rendering consumes numerical metrics from
`validation/metrics.py`; it does not run Simulation, reconstruction, or fitting.
Hit distributions use unique event/layer pairs, while reference means retain the
historical pooled Rec mean minus Sim mean. The χ² ratio retains ACTS's stored
measurement-dimension convention; it is not statistical reduced χ².
For a Docker/XQuartz GUI use `bash environment/root_shell.sh`, then `cd /work`.
Batch checks do not require X11. Interactive TBrowser operation was not tested.

## Historical data and troubleshooting

`results/` is immutable legacy data for this migration. No historical XML, ROOT,
Mille Binary, log, symlink, or command record was moved or edited. This includes
`results/reference/physical_alignment_L2_x200um/`, the latest source-position study
`results/vertex_zminus500_20261019_01/closure100/`, and the previous stage-refactoring
results. Historical manifests retain those paths. The nominal/source pins are
retargeted to their new maintained paths with unchanged hashes.

- Missing dependencies: install a complete prefix; never reuse an old source-path
  CMake cache. Upstream source/installations are not changed by this refactor.
- Missing reference data: obtain the checksum-identical dataset from the maintainer
  or persistent archive; generated data and external installations are not in Git.
- Existing/partial step: inspect its records, then select a new result directory.
- Standard DD4hep-to-ACTS conversion diagnostics remain visible; the custom manual
  surface fitter is independent. This refactor does not solve that conversion.
- Arbitrary layouts, Global Y/Z shifts, rotations, multi-layer correction, material
  changes, error rescaling, or revised statistical nDoF are outside scope.

See [TASK_ARCHITECTURE.md](TASK_ARCHITECTURE.md) for executed commands, migration
inventory, and results. [STAGE_REFACTORING.md](STAGE_REFACTORING.md) records the
preceding architecture and is historical, not the current command guide.
