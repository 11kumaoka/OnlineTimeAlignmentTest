> Historical baseline before the RawHit execution split. Current commands and
> architecture are in [WORKFLOW.md](WORKFLOW.md) and [RAWHIT_BOUNDARY.md](RAWHIT_BOUNDARY.md).

# Final Architecture and Publication Audit

Date: 2026-10-21. This report records the source audit and validation performed
before committing the modular implementation. The development branch is
`seven-layer-alignment` in `11kumaoka/OnlineTimeAlignmentTest`. The starting local
and fetched remote commit was `3034eb1f4a43dfa925992e4a9000ea115dcb63a3`, with no
divergence. Publication uses a normal commit/push, without rewriting history.

## Maintained structure and configuration ownership

| Directory/file | Purpose | Configuration or entry point |
|---|---|---|
| `localDetEICrecon/` | C++ Plugin, factories, processors, algorithms, in-process Mille Writer and build support | `CMakeLists.txt`, `build.sh`; Plugin name remains `BeamTestReco` |
| `geometry/` | Nominal Detector Geometry, scenarios, independent preparation and placement verification | `nominal/seven_layer_telescope.xml`, `scenarios/L2_x200um.json`, `scenarios/L1_x100um_L2_x200um.json`; `prepare_geometry.sh` |
| `simulation/` | DDSim execution; particle, energy, events, vertex, widths, angles and seed | `configs/electron_1GeV.json`, `configs/muon_5GeV.json`; `simulate.sh --config PATH` |
| `reconstruction/` | EICrecon command construction and execution | `configs/electron_1GeV.json`, `configs/muon_5GeV.json`; `reconstruct.sh`, `reconstruct_corrected.sh` |
| `alignment/` | External Millepede-II process, template expansion and parameter parsing | `pede_template.txt`; `align.sh --steering PATH` |
| `correction/` | Existing L2 Global X Geometry Correction | saved scenario and label 1002; `correct_geometry.sh`; no generalized correction config |
| `validation/` | Numerical Hit Residuals, Closure metrics, regression and integrity checks | `reference_metrics.json`; `validate.sh --reference PATH` is optional |
| `visualization/` | ROOT rendering and browsing | `closure.py`, `browse.C`; saved summary/Geometry are explicit inputs; plot definitions remain in code |
| `environment/` | Pinned Docker runtime, dependency setup, shared build implementation | `run.sh`, `dependencies.json`, `container.env.example`, `build.sh` |
| `research_common.py` | Paths, CLI safety, hashes, completion markers and execution records | infrastructure only, no physics model |
| `docs/` | Current guides, integration explanation and explicitly historical reports | [Workflow Guide](WORKFLOW.md), [architecture/migration report](TASK_ARCHITECTURE.md) |
| `result/` | New generated runs using step1–step7 | ignored, preserved locally |
| `results/` | Historical outputs and local regression inputs | ignored, untouched |
| `external/`, `build/` | Dependency sources/installations and generated Plugin builds | ignored, preserved locally |

The complete tree and per-file migration inventory are in
[TASK_ARCHITECTURE.md](TASK_ARCHITECTURE.md). Python package markers are maintained
where needed for `python3 -m` entry points. There is one processing implementation
per task, with two reconstruction wrappers sharing the same module.

`BeamTestMilleProcessor` selects Track measurements inside EICrecon and calls
`BeamTestMilleWriter`. The writer supplies the existing straight-line Local and
Global derivatives to the official Mille API in `libMille2.so`. It writes the
Mille Binary, then EICrecon exits. `alignment/align.py` launches the separate
`pede` executable, reads its result/status, and never implements a replacement
solver. See [the integration document](EICRECON_MILLEPEDE_INTEGRATION.md).

## Cleanup decisions and recovery

The pending migration already removed the obsolete `local_detector_testbench/`
and `examples/` directories from the active filesystem. Their tracked deletions
are included with the new destinations in this publication:

- C++ Plugin and writer moved into `localDetEICrecon/` with byte-identical `.cc`
  and `.h` contents, including the validated electron hypothesis.
- Nominal XML and Geometry scenarios moved into `geometry/` unchanged in content.
- The combined electron/muon cases were split into Simulation and Reconstruction
  JSONs with unchanged numerical values; the steering template moved unchanged.
- The old central `scripts/workflow.py` was replaced by the independent modules.
  Task-specific wrappers moved with their stages. No compatibility Python package
  or old-path execution tree remains.
- This final audit removed only the unused `browse_alignment()` forwarding alias
  from `visualization/browse.C`, after confirming that no maintained command or
  source calls it. The supported `browse()` macro remains. No additional source
  file or research data directory was deleted during this final audit.
- Stale active integration-document output paths were corrected to step3. Earlier
  reports are labeled historical. A link into untracked historical audit output
  was changed to a plain local-data path so it is not a broken GitHub hyperlink.

The following apparent redundancies were deliberately retained:

| Item | Reason |
|---|---|
| Task shell wrappers | Independent documented entry points; they contain no duplicated processing logic. |
| `reconstruct_corrected.sh` | Selects step6 through `--after` on the shared implementation. |
| `validation/run_closure.sh` | Optional shell-only sequential calls; preflights unsupported correction before Simulation. |
| `validation/run_regression.sh` | Supplies the specific local reference input/tolerances; not a second workflow implementation. |
| `localDetEICrecon/build.sh` and `environment/build.sh` | Plugin-facing entry point delegates to the one build implementation. |
| `localDetEICrecon/alignment/CMakeLists.txt` | Can build the same writer as a reusable static library; does not duplicate its source or algorithms. |
| `--run-dir` CLI spelling | Still documented and checked by safety tests; it does not restore an old directory layout. |
| Historical reports, checksum manifests and electron patch | Research provenance, data recovery, and source/data integrity verification. |
| Existing ignored builds, bytecode, ROOT/Mille files and logs | Preserved local artifacts, excluded from publication; no broad cleanup was attempted. |

A checksum-verified source recovery archive was created **outside the working tree**:

```text
/Users/tkumaoka/eic/OnlineTimeAlignmentTest_archives/finalize_architecture_20261021_01/
```

It contains `maintained_before.tar.gz`, initial Git status/diffs, and the protected
file inventory. Archive SHA-256:

```text
debd39c1eeda8194fb14169ab4206683314ce278da02f67862829fb0f3850e53
```

This is a maintainer-local recovery location, not an execution dependency. The
previous persistent external archive was not changed. Local test logs and a
second recovery copy are under `result/finalize_architecture_20261021_01/`.

## Seven independently executed commands

Run from the repository root with dependencies installed and the Plugin built:

```bash
bash environment/run.sh bash localDetEICrecon/build.sh
```

Use a new result name. These seven commands do not launch subsequent stages:

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/manual_001 --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh bash simulation/simulate.sh --result-dir result/manual_001 --config simulation/configs/electron_1GeV.json
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/manual_001 --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/manual_001 --steering alignment/pede_template.txt
bash environment/run.sh bash correction/correct_geometry.sh --result-dir result/manual_001
bash environment/run.sh bash reconstruction/reconstruct_corrected.sh --result-dir result/manual_001
bash environment/run.sh bash validation/validate.sh --result-dir result/manual_001
```

| Step | Inputs | Main outputs under `result/manual_001/` |
|---|---|---|
| 1 | nominal XML + scenario | `step1/nominal.xml`, `misaligned.xml`, scenario snapshot, placement report and GDML QA |
| 2 | step1 + Simulation config, or imported ROOT | `step2/events.edm4hep.root`, `config.json` |
| 3 | step2 + nominal + Reconstruction config + Plugin | `step3/reco.root`, `mille.dat`, `config.json` |
| 4 | step3 Mille Binary + steering template | `step4/pede.txt`, template snapshot, `millepede.res`, logs/status |
| 5 | nominal + scenario + step4 | `step5/corrected.xml` |
| 6 | step2 + corrected Geometry + same Plugin/config | `step6/reco.root`, `mille.dat`, `config.json` |
| 7 | complete prior steps | `step7/summary.json`, `alignment.root` |

Subprocesses retain command/stdout/exit records; completed steps have checksums in
`complete.json`. Existing outputs are refused. Pure XML correction and Simulation
reuse have no subprocess command to record. Full option/record details are in
[WORKFLOW.md](WORKFLOW.md). Select the matching Simulation/Reconstruction muon
configs explicitly for a muon study. Current electron generation uses z=−500 mm;
the imported historical regression sample actually uses z=0 mm.

## Final validation actually executed

All outputs are new. The clean build command was:

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh env TESTBENCH_BUILD_DIR=/work/build/finalize_architecture_20261021_01 bash localDetEICrecon/build.sh
```

It completed with exit 0, producing `BeamTestReco.so`. Every stage wrapper was
invoked independently, in order, with result directory
`result/finalize_architecture_20261021_01/regression`. The commands above were used
with that name and these explicit selections:

- step2: `--sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root`;
- steps3/6: `--build-dir build/finalize_architecture_20261021_01`;
- step7: `--reference validation/reference_metrics.json`.

All seven stages completed with exit 0. Observed metrics:

| Metric | Before | After |
|---|---:|---:|
| Events | 100 | 100 |
| Accepted tracks | 99 | 99 |
| Pooled L2 Rec−Sim [μm] | −199.571375548 | −0.821364508 |
| Σχ² / Σstored ACTS nDoF | 45.592234848 | 1.981039768 |

Applied L2 correction: **+198.75 μm**; reference comparison passed. The entire
summary, both Mille Binaries, and nominal/misaligned/corrected XML match the prior
validated top-level-architecture regression. Pede status is `1 Ended with warnings
(bad measurements)`, accepted by the established workflow; this is not a
warning-free fit.

The new two-layer result at
`result/finalize_architecture_20261021_01/two_layer_geometry_only` contains only
step1. Exported DD4hep placements verify L1 +0.100 mm and L2 +0.200 mm in Global X,
with all other X positions and all Y/Z positions unchanged. Its real correction
preflight was rejected explicitly without writing any additional files. No
new two-layer Simulation, reconstruction, pede fit, or Closure was run.

Additional executed checks:

- All maintained Python imports in the configured Docker runtime: PASS.
- Python compilation, shell syntax and independent wrapper help: PASS.
- Official `inspectMilleBinary -c` decoded before/after binaries: **99 records and
  990 scalar measurements each**, with no decoding errors.
- `validation/check_root_outputs.py`: PASS, three canvases, at least 20 residual
  histograms and Closure graphs.
- `validation/verify_preservation.py`: PASS, 221 baseline records, 2046 relocated
  files and the validated fitter hash.
- `validation/check_safety.py`: PASS, overwrite, prerequisite, tamper, output-root,
  scenario type/layer and unsupported multi-layer correction refusals.
- All 4327 inventoried existing files under `result/`, `results/`, and `external/`
  retained their initial SHA-256 values. No existing data were overwritten.
- No active import, Shell command, CMake path or Docker path depends on
  `local_detector_testbench/` or the old example layout.

No new Geant4 events were needed: step2 reuse was exercised. No new muon fit or
interactive ROOT GUI session was tested.

## Publication scope and remaining limitations

Only maintained source, configuration, documentation, validation scripts and Git
metadata are staged. Generated `result/`, `results/`, `build/`, `external/`, ROOT,
Mille Binary, log, bytecode, temporary and backup files are excluded by `.gitignore`.
The staged tree is checked for binary/large files, credential patterns, accidental
absolute execution paths and missing maintained documentation targets. Historical
local archive paths are explicitly identified as provenance, not runtime inputs.
The minimum local regression dataset and SHA-256 are documented in
[validation/README.md](../validation/README.md); it is not distributed by Git.

There is no physics-model expansion. Geometry scenarios support finite SiMAPS
Global X shifts in the current origin-centered, unrotated seven-plane hierarchy.
Pede retains its L1–L3 X/Y fit and fixed L0/L4. Only L2 Global X is applied during
Geometry Correction; a scenario with nonzero shifts outside L2 cannot complete
Closure. The writer contract remains five 2D SiMAPS measurements per accepted
track. Optional detector inclusion, covariance/material modeling, manual ACTS
surfaces and other fitter assumptions still require separate scientific work.

The legacy standalone C++ writer output default `results/manual/mille.dat` remains
unchanged; every maintained Reconstruction command supplies an explicit
`result/<name>/step3|step6/mille.dat` instead. The known standard DD4hep-to-ACTS
conversion diagnostic remains visible. Stored ACTS nDoF semantics, uncertainties,
seeds, alignment signs, derivatives, Geometry dimensions/materials, and electron
hypothesis were not changed.
