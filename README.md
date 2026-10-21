# Local Detector Testbench

A reproducible local DD4hep/EICrecon Alignment Closure Test:
Detector Geometry → Simulation → Digitization / Hit Reconstruction → Track Fitting
→ Mille Binary → Millepede-II → Geometry Correction → reconstruction of the same
simulated events → ROOT validation.

The working example is a seven-plane telescope: five SiMAPS planes, MPGD, and
AC-LGAD. The current alignment model fits five SiMAPS planes and applies only
the L2 Global X correction. This backend does not claim support for arbitrary
geometries, rotations, or material models.

## Quick start

Requirements: Git, Docker with Linux amd64 support, disk space, and network
access for the pinned image and dependency sources. Run from the repository root:

```bash
# Once, on a new checkout without external/:
bash environment/run.sh python3 environment/setup_dependencies.py
bash environment/run.sh bash environment/build.sh

# Use a new result directory for every analysis:
bash environment/run.sh bash local_detector_testbench/scripts/run_closure.sh \
  --result-dir results/electron_001
bash environment/run.sh python3 validation/check_root_outputs.py \
  --result-dir results/electron_001
```

On this development checkout, `external/install/` already exists: skip dependency
setup and run the build. Setup refuses to overwrite an existing dependency workspace.
`TESTBENCH_CONTAINER` may select an existing container mounted at `/work`;
otherwise the launcher uses the pinned image in `environment/run.sh`.

The default electron case generates 100 events of 1 GeV electrons at mean
(0, 0, −500) mm, toward +z with the configured angular spread, 50 cm upstream of
L0. X/Y widths are 0.2 mm. L2 is displaced by +200 μm during Simulation;
reconstruction first uses the unchanged nominal Detector Geometry.

## Layout

```text
environment/                  container launcher, dependency setup, Plugin build, ROOT GUI shell
local_detector_testbench/
  local_eicrecon/              C++ BeamTestReco Plugin and processors
  alignment/                  BeamTestMilleWriter library
  scripts/                    staged workflow and orchestration
  visualization/              supported PyROOT Closure and ROOT browser macro
examples/seven_layer_telescope/  nominal Geometry, detector cases, pede constraints
external/                     pinned dependency source/build/install (not tracked)
validation/                   references, preservation checks, safety and ROOT checks
docs/                         workflow guide and final migration report
results/                      all analyses, reference data, migrated results (not tracked)
build/                        generated Plugin build (not tracked)
```

Old implementations and reports are archived outside the repository. There is
no supported legacy execution path and no `runs/` compatibility directory.
See [the final migration report](docs/FINAL_SIMPLIFICATION.md) and
[old-to-new paths](validation/path_migration.json).

## Independent stages

```bash
bash environment/run.sh bash local_detector_testbench/scripts/prepare_geometry.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/simulate.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/reconstruct.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/align.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/correct_geometry.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/reconstruct_corrected.sh --result-dir results/manual_001
bash environment/run.sh bash local_detector_testbench/scripts/validate.sh --result-dir results/manual_001
```

Existing stage outputs are never overwritten. `--run-dir` remains an argument
alias for `--result-dir`; it does not restore the removed directory layout.
See [the Workflow Guide](docs/WORKFLOW.md) for inputs, outputs, settings, and checks.

## Regression and ROOT

The preserved historical input is local data, not part of a Git clone. See
[required local datasets and checksum verification](validation/README.md):

```bash
bash environment/run.sh bash validation/run_regression.sh results/regression_001
bash environment/run.sh python3 validation/check_root_outputs.py --result-dir results/regression_001
```

That z=0 mm sample must reproduce 99 accepted tracks before/after, L2 correction
+198.75 μm, L2 Rec−Sim −199.571→−0.821 μm, and Σχ²/Σstored ACTS nDoF
45.592→1.981. The current z=−500 mm sample is a different reference, previously
98 tracks and +201.13 μm. The historical reference is not applied to fresh events.

Each result stores `validation/plots/alignment.root` with Detector Geometry,
Hit Residuals, and Alignment Closure Test canvases. On a ROOT GUI host:

```bash
root --web=off -l 'local_detector_testbench/visualization/browse.C("results/electron_001/validation/plots/alignment.root")'
```

For the Docker/XQuartz shell, use `bash environment/root_shell.sh`, then `cd /work`
and open the same macro. Batch generation does not require X11.

## Physics conventions and language

The electron hypothesis, manual zero-field ACTS surfaces, seed covariance,
selection, material limitations, alignment derivatives, and constraints are
preserved. The displayed χ² ratio uses stored ACTS measurement dimensions;
it is not redefined statistical reduced χ². The known standard DD4hep-to-ACTS
geometry conversion diagnostic remains visible. No input errors are rescaled.

Use English for maintained comments, docstrings, configuration comments, CLI
help, visualization labels, and technical reports. Use these terms consistently:
Detector Geometry, Simulation, Digitization, Hit Reconstruction, Track Fitting,
Alignment Parameters, Local and Global Parameters, Mille Binary, Millepede-II,
Geometry Correction, Alignment Closure Test, and Hit Residuals.
