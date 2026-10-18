# EICrecon Beam-Test Tracking and Alignment Prototype

**Development branch:** [`seven-layer-alignment`](https://github.com/11kumaoka/OnlineTimeAlignmentTest/tree/seven-layer-alignment)\
**Documentation baseline:** commit [`21008aedd46a`](https://github.com/11kumaoka/OnlineTimeAlignmentTest/commit/21008aedd46ae28123728fb4606213865b7a3b9e) (2026-10-18)

> **Status:** Research prototype, not yet a fully reproducible one-command installation. The locally validated chain reaches SiMAPS alignment-parameter estimation with real Millepede-II. Applying the solved corrections to reconstruction/geometry and timing calibration are **not implemented**.

## Purpose

This repository develops a compact seven-plane beam-test telescope for investigating detector reconstruction and spatial alignment using DD4hep/Geant4 (`ddsim`), EICrecon/JANA2, ACTS, PODIO/EDM4eic, and the official Mille/Millepede-II implementation.

The telescope comprises five SiMAPS planes at z = 0, 50, 100, 150, and 200 mm; one MPGD plane at 250 mm; and one AC-LGAD plane at 300 mm. Current validation uses 5 GeV negative muons in zero magnetic field. Its initial global alignment model is **SiMAPS-only**, with x/y translational measurement biases and a four-parameter straight-line model. The two endpoint SiMAPS planes (L0, L4) are fixed to remove global gauge freedoms.

## Current software flow

```text
DD4hep geometry + ddsim (Geant4)
              |
              v
EDM4hep / SimTrackerHit ROOT
              |
              v
EICrecon / JANA2 (local BeamTestReco plugin)
  Silicon-derived digitization -> RawTrackerHits
  truth-independent hit reconstruction -> TrackerHits
  telescope-specific ACTS Kalman fit -> Tracks / Trajectories
  BeamTestMilleProcessor -> official Mille binary
              |                           |
              v                           v
        EDM4eic ROOT                Mille .dat
                                          |
                                          v
                              standalone global pede solve
                                          |
                                          v
                                    millepede.res
```

The **reconstruction, ACTS fit, and Mille binary generation** are integrated into one JANA2 process. Global `pede` runs afterward as a separate solver. Geant4 simulation is a preceding separate execution.

## What works and what remains

| Capability | Current status |
| --- | --- |
| Seven-plane DD4hep geometry and Geant4 simulation | Demonstrated |
| Truth-independent SiMAPS digitization / hit reconstruction | Demonstrated; pixel-position RMS approximately 10 µm in prior validation |
| Local ACTS fit in JANA2 | Demonstrated for unambiguous single-track events |
| Track, trajectory and measurement PODIO output | Produced; EDM4eic semantics require further cross-checking |
| In-process official Mille binary writer | Demonstrated |
| Real `pede` global fit for five SiMAPS x/y offsets | Demonstrated |
| Injected measurement-bias closure | Demonstrated; +0.200 mm injection produced +0.20000413 mm fitted *change* in post-audit sample |
| Multi-hit / multi-track finding | Not implemented; ambiguous layers may cause rejection |
| MPGD and AC-LGAD detector-specific response | Provisional silicon-derived models |
| Apply fitted alignment constants and rerun ACTS | Not implemented |
| Geometry-misalignment closure, rotations, 7-plane alignment | Not implemented |
| Timing calibration | Not implemented |

The post-audit 80-event run accepted **68 tracks**, wrote **68 Mille records** and **680 coordinates**. These are example sample-specific counts, **not a general tracking-efficiency measurement**. See [`seven_layer/reports/full_chain_validation_report.md`](seven_layer/reports/full_chain_validation_report.md).

## Requirements

- Git and Docker with ability to run `linux/amd64` containers (including emulation on Apple Silicon).
- `eicweb/eic_xl:nightly`; the source audit recorded EICrecon `v1.37.0-14-g195966d4`, JANA `2026.2.0`, ACTS `45.3.0`, DD4hep `1.36`, PODIO `1.7` and Millepede-II `05.01.06`. **The mutable `nightly` tag is not a reproducible version pin.**
- Official [Mille C++ writer](https://gitlab.desy.de/millepede/Mille) and [Millepede-II / pede](https://gitlab.desy.de/millepede/millepede-ii) installed within this workspace. Their sources, build products and installation are excluded from Git.

**Important:** This commit does **not** include a complete script to clone, build and install the official Mille/Millepede-II dependencies. `seven_layer/millepede/scripts/build_mille_tools.sh` compiles the **local toy tool**, not the external dependencies. A new contributor must first satisfy the installation layout specified in [WORKFLOW.md](seven_layer/docs/WORKFLOW.md). Do not assume `git clone` alone is enough to compile the Mille-enabled plugin.

## Quick navigation

- **[Detailed workflow](seven_layer/docs/WORKFLOW.md)** — simulation, local plugin build, ACTS, Mille, `pede`, outputs, verification, and currently missing bootstrap steps.
- **[Directory structure](seven_layer/docs/DIRECTORY_STRUCTURE.md)** — directory map and important source and script roles.
- [Local plugin README](seven_layer/local_eicrecon/README.md) — local factory/algorithm background; some examples refer to earlier runs.
- [Code audit](seven_layer/reports/full_chain_code_audit.md), [validation report](seven_layer/reports/full_chain_validation_report.md), [upstream EICrecon comparison](seven_layer/reports/upstream_eicrecon_comparison.md).
- [Millepede-II development report](seven_layer/millepede/reports/millepede_progress_report.md) — original M1–M5 integration milestones (some counts predate the post-audit 68/80 acceptance policy).

## Starting point

```bash
git clone --branch seven-layer-alignment https://github.com/11kumaoka/OnlineTimeAlignmentTest.git
cd OnlineTimeAlignmentTest
bash seven_layer/scripts/run_phase1_ddsim.sh
```

The command above invokes the **Phase-1 simulation and geometry checks** under Docker; it does not build the Mille-enabled reconstruction chain. For the current alignment prototype, follow the prerequisites and staged commands in [WORKFLOW.md](seven_layer/docs/WORKFLOW.md). On a fresh checkout, the integrated scripts expect a generated Simulation ROOT file which is intentionally not tracked in Git.

## Data and software provenance

Original EICrecon algorithms were copied/adapted into locally editable code; the comparison and provenance notes are in [`seven_layer/reports/upstream_eicrecon_comparison.md`](seven_layer/reports/upstream_eicrecon_comparison.md). The installed Docker EICrecon revision and the separate reference checkout revision are different; do not assume source-level parity. Retain upstream copyright and license notices.

Generated `.root`, Mille `.dat`, `.res`, compiled `.so`, logs, and external tool installations are typically ignored by Git. A public repository should not contain credentials, private datasets, or machine-specific configuration secrets.

## Limitations of these instructions

These documents were drafted by inspecting the **published source at commit `21008ae`**. They were **not** exercised end-to-end in a clean Docker environment in this review. Commands described as reference or proposed must be validated on a clean clone before describing this project as fully reproducible.
