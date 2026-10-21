# Final Repository Simplification

Date: 2026-10-21. The working repository now contains only the current local
detector workflow, its dependencies, verification tools, and preserved data.
No commit, push, or index staging was performed.

## Final top-level tree

```text
OnlineTimeAlignmentTest/
├── README.md
├── environment/
├── local_detector_testbench/
│   ├── local_eicrecon/
│   ├── alignment/
│   ├── scripts/
│   └── visualization/
├── examples/
├── external/
├── validation/
├── docs/
├── results/
└── build/
```

`.git/` and `.gitignore` remain for version control. No other top-level directory
is retained. `external/` contains the pinned dependency workspace and unchanged
installation; `build/` contains only the new default Plugin build. Generated data
are excluded from Git by `/results/`, `/build/`, and `/external/` ignore rules.

## Complete external archive

Before destructive changes, a complete repository snapshot, including ignored,
untracked, tracked, and Git metadata files, was archived at:

`/Users/tkumaoka/eic/OnlineTimeAlignmentTest_archives/final_cleanup_20261021_01/`

The archive is `repository_before.tar.gz`. All 5,874 file/symlink entries were
verified by SHA-256 or symlink target. The archive checksum is:

`ddc2a6d14cf76ba4e5e5e967e7614f53124d303210dae54da5b35e724bb55bda`

`files_before.json`, `VERIFIED.json`, the checksum file, original Git status,
and staged/unstaged patches accompany the archive. This is a persistent path
outside the repository, not a temporary-directory backup. The post-cleanup maintained-source snapshot is `maintained_after.tar.gz`,
with its own checksum inventory, stored there after validation.

## Removed implementations and relocated results

| Former location | Treatment and reason |
|---|---|
| `seven_layer/` | Removed completely. Local Plugin, writer, Geometry, scripts, and constraints already have canonical maintained locations. Standalone ACTS, StageAB/StageCD/CKF, injected/toy experiments, old installs, source caches, and reports are in the external archive. Data/results/logs needed for preservation were relocated below `results/`. |
| `prototype/` | Removed. The distinct five-layer CKF algorithms, settings, and reports are archived externally; preserved geometry reference bytes and result data were relocated. |
| `test/` | Removed. The physical 99-track dataset moved to `results/reference/physical_alignment_L2_x200um/`; other useful Simulation/reconstruction/Mille/log data moved to `results/legacy_data/`. Unused diagnostics and source copies are archived. |
| `artifacts/`, `logs/` | Removed from the root; existing output data moved to `results/legacy_data/`. |
| `calibrations/`, `fieldmaps/`, `gdml/` | Removed. These were container asset links, not the telescope's Detector Geometry inputs. The nominal XML loads elements/materials/detector definitions from `${DD4hepINSTALL}`. Full build and fresh Simulation/reconstruction passed with these root directories absent. Their link records remain in the archive. |
| `tmp/`, old `build/`, `.vscode/`, root `.DS_Store` | Archived and removed. The Plugin was built from scratch in a new default build tree. |
| `local_detector_testbench/visualization/experimental/` | Archived and removed, including distinct historical plotting comparisons. Only supported ROOT visualization remains. |
| Old reports in `docs/` | Archived and removed. The maintained documents are the Workflow Guide and this English report. |
| Old toy C++ target and duplicate alignment template | Archived and removed. The writer library remains; the canonical model template is in the telescope example. No derivatives or constraints changed. |
| Root Millepede/PODIO output files | Moved to `results/legacy_root/`. No generated Pede or PODIO output remains at the root. |
| `openModifyEicShell.sh` | Moved to `environment/root_shell.sh`; uses a repository-relative mount and the pinned image while preserving the XQuartz DISPLAY/xhost configuration. |

The archive-only inventory contains 1,479 file/link paths. The migration records
2,054 moved file/link paths, including the GUI launcher. The exact per-file lists
are [archived_paths.json](../results/final_simplification_20261021_01/archived_paths.json)
and [path_migration.json](../validation/path_migration.json).
Directory removals were performed only after every remaining file/link under
them matched the verified archive. Symlink targets in container installations
were never deleted.

## Data preservation and migration

Every existing run directory moved from `runs/` to `results/`; there is no
compatibility directory or symlink at the former root. Regular-file bytes were
not edited. Existing JSON/log/command records retain historical paths as
provenance and are not replay scripts for the new layout.

Seven existing Simulation input links were retargeted to the relocated,
byte-identical reference input. This includes a historical source-only workspace
link whose former `/work/input` binding no longer exists. Its saved input SHA
matched the retained reference before retargeting. No new compatibility link
was created.

The original 221 preservation entries retain exactly their original hashes.
Their keys were relocated using the explicit mapping; no baseline entry was
removed. The checker now additionally validates all 2,046 relocated data files
and all seven input links independently. The moved GUI script is intentionally
excluded from the data-file checksum list because its source paths were updated.

The 99-track data are at `results/reference/physical_alignment_L2_x200um/`.
The pre-cleanup z=−500 mm Closure remains at
`results/vertex_zminus500_20261019_01/closure100/`. Neither data content nor
recorded numerical results were changed. Earlier run snapshots can contain
historical directory names inside `results/`; these are preserved evidence,
not active dependencies.

## Workflow changes

- `--result-dir` is the documented option. `--run-dir` remains a CLI alias only.
  Result paths must be new child directories of `results/`; whitespace is refused.
- Each process executes in its stage directory. Pede still runs in `alignment/`
  with an absolute input Mille path, so relative steering lookup remains correct.
- Container login setup starts in `results/.environment/` before returning to
  the repository for command dispatch. This isolates potential startup asset links.
- Standalone writer defaults now use `results/manual/mille.dat`. The supported
  workflow always supplies a stage-specific path. Standalone users must create
  that parent directory explicitly.
- The toy executable target was removed from the optional writer-library CMake
  project. The Plugin still compiles the same BeamTestMilleWriter implementation.
- Validation paths, browser default path, README, Workflow Guide, and ignore
  rules now use `results/`. No maintained runtime dependency points into a removed
  directory. Origin comments and relocation records retain historical names.

Physics source hashes and AST comparison verified that all workflow physics
functions are unchanged. C++ writer/processor header changes are output-path
literals only. Nominal Geometry, detector cases (including z=−500 mm), fitting,
electron hypothesis, hit selection, alignment mathematics, and constraints are
unchanged.

## Executables and libraries

The host checkout is mounted as `/work` inside the EIC container.

| Component | Runtime location |
|---|---|
| DDSim | `/opt/local/bin/ddsim` |
| Geometry QA | `/opt/local/bin/geoConverter` |
| EICrecon | `/opt/local/bin/eicrecon` |
| ROOT | `/opt/local/bin/root` |
| Python / CMake | `/opt/local/bin/python3`, `/opt/local/bin/cmake` |
| Local Plugin | `/work/build/local_eicrecon_external/BeamTestReco.so` |
| Millepede-II | `/work/external/install/bin/pede` |
| Mille shared library | `/work/external/install/lib/libMille2.so` |
| Writer implementation | `local_detector_testbench/alignment/src/BeamTestMilleWriter.{cc,h}` |
| Processors | `local_detector_testbench/local_eicrecon/processors/` |

Exact resolved container package paths are recorded in
`results/final_simplification_20261021_01/executable_locations.json`. An ldd check
with `LD_LIBRARY_PATH` unset resolves Mille2 to the canonical external install,
with no missing libraries. Old `seven_layer` installations are absent.

## Validation performed

These commands ran from the repository root using existing container
`sweet_mahavira` with the pinned EIC environment. All completed with exit code 0.
Logs are in `results/final_simplification_20261021_01/`.

```bash
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -lc \
  'test ! -e build/local_eicrecon_external && bash environment/build.sh'
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash validation/run_regression.sh results/final_simplification_20261021_01/regression
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  bash local_detector_testbench/scripts/run_closure.sh \
  --result-dir results/final_simplification_20261021_01/fresh_electron_100
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/check_root_outputs.py \
  --result-dir results/final_simplification_20261021_01/regression
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  python3 validation/check_root_outputs.py \
  --result-dir results/final_simplification_20261021_01/fresh_electron_100
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env -u LD_LIBRARY_PATH ldd build/local_eicrecon_external/BeamTestReco.so
python3 validation/verify_preservation.py
python3 validation/check_safety.py
git diff --check
git diff --cached --check
```

Both Closure runs completed Geometry QA, reconstruction, official Mille Binary
generation, pede, Geometry Correction, corrected reconstruction, and existing ROOT
visualization. The fresh test also generated 100 new Geant4 events. It verified
100 Primary MCParticles at z=−500 mm with +z momentum and hits in all seven layers
in all 100 events.

| Metric | Historical 100-event regression | Fresh z=−500 mm 100-event test |
|---|---:|---:|
| Accepted tracks, before / after | 99 / 99 | 98 / 98 |
| L2 correction [μm] | +198.75 | +201.13 |
| L2 Rec − Sim [μm] | −199.571376 → −0.821365 | −198.922108 → +2.207910 |
| Σχ² / Σstored ACTS nDoF | 45.592235 → 1.981040 | 33.273539 → 1.244249 |
| Historical reference comparison | PASS | Different source condition; not applied |

ROOT checks passed for three canvases, at least 20 residual histograms, and
closure TGraphs in each result. Safety checks cover existing outputs, the old
CLI alias, missing prerequisites, unsupported alignment cases, changed stage
outputs, and output-directory escape. Python and Shell syntax checks passed.
The original electron patch and original 221 baseline records passed preservation,
as did all relocated data and input links.

Major outputs under either new result directory:

```text
geometry/{nominal,misaligned}.xml
simulation/events.edm4hep.root
before/{reco.root,mille.dat}
alignment/{pede.txt,millepede.res,millepede.log,millepede.his,millepede.end}
correction/corrected.xml
after/{reco.root,mille.dat}
validation/plots/{alignment.root,summary.json}
```

The checks also confirmed that actual command working directories are contained
inside each result, steering inputs resolve to its own before/Mille Binary,
and no removed top-level directory or generated root output was recreated.

## Limitations and Git status

Interactive ROOT/TBrowser and XQuartz GUI operation were not executed; batch
ROOT readback passed. The known standard ACTS conversion diagnostic and manual
surface/material/nDoF limitations remain unchanged. The muon configuration is
preserved but was not rerun during this cleanup.

The existing staged patch was preserved byte-for-byte. New moves, deletions, and
source/documentation edits remain unstaged or untracked as appropriate; the
index was not rewritten. Earlier staged renames can therefore show `RD` when
the newly archived toy/config destination is absent. This is expected pending
review of the combined changes. Current status is recorded in
`results/final_simplification_20261021_01/git_status_after.txt`.
No external EICrecon source tree was edited. No commit or push was performed.

Final independent checks also confirmed 1,810 unaffected original file/link paths
(including the current external installation) remained unchanged. The exact
root-directory set, per-stage working directories, pede steering references,
English maintained text, unchanged index patch, and syntax checks are recorded
in `results/final_simplification_20261021_01/final_checks.json`.
