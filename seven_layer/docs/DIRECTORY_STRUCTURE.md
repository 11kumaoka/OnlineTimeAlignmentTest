# Directory structure and source guide

This map is based on the **tracked files** at commit [`21008ae`](https://github.com/11kumaoka/OnlineTimeAlignmentTest/tree/21008aedd46ae28123728fb4606213865b7a3b9e) on `seven-layer-alignment`. Ignored build artifacts and runtime data are shown as `(generated / local)` even though absent in a fresh clone.

## High-level layout

```text
OnlineTimeAlignmentTest/
├── README.md                         Project entry point (replace old prototype-only README)
├── .gitignore                        Generated outputs / local dependencies exclusions
├── prototype/                        Earlier 5-layer demonstrator and CKF experiments
│   ├── config/, geometry/
│   ├── scripts/, reports/, results/
└── seven_layer/                      Current 7-layer telescope development
    ├── config/                        Layout metadata (JSON)
    ├── geometry/                      DD4hep compact XML
    ├── local_eicrecon/                Locally built JANA2 BeamTestReco.so plugin
    │   ├── CMakeLists.txt
    │   ├── README.md
    │   ├── algorithms/
    │   │   ├── digi/                   Local Si-derived digitization
    │   │   └── tracking/               TrackerHit reconstruction and ACTS fitter
    │   ├── factories/
    │   │   ├── digi/                   Digitization factory
    │   │   └── tracking/               Hit/ACTS factories
    │   ├── plugins/                    BeamTestReco plugin registration
    │   ├── processors/                 Monitoring and Mille binary output
    │   └── build/                      (generated / ignored)
    ├── millepede/                     Global spatial-alignment component
    │   ├── CMakeLists.txt
    │   ├── src/                         Local Mille wrapper and toy generator
    │   ├── scripts/                     Toy, integrated and pede scripts
    │   ├── config/                      Pede steering template
    │   ├── reports/                     Mille integration notes
    │   ├── third_party/                 (local cloned official sources / ignored)
    │   ├── install/                     (local official builds / ignored)
    │   ├── build/                       (generated / ignored)
    │   └── results/                     (generated / ignored)
    ├── scripts/                        Simulation, reconstruction, analysis helpers
    ├── reports/                        Code/physics validation history
    ├── results/                        (mostly generated / ignored)
    ├── logs/                           (generated / ignored)
    ├── standalone_acts/                Earlier independent ACTS regression harness
    └── docs/                           Workflow and directory documentation (new)
```

## Source responsibilities

| Path | Responsibility |
| --- | --- |
| `seven_layer/geometry/seven_layer_telescope.xml` | Actual DD4hep detector geometry and readout segmentation for 5 SiMAPS + MPGD + AC-LGAD; authoritative for current runtime |
| `seven_layer/config/seven_layer_layout.json` | Illustrative layout/readout assumptions; **not synchronized in all fields** with the geometry and current gun settings |
| `seven_layer/local_eicrecon/algorithms/digi/SiliconTrackerDigi.*` | EICrecon-derived algorithm, currently used as provisional digitization for all three detector types |
| `seven_layer/local_eicrecon/algorithms/tracking/TrackerHitReconstruction.*` | Reconstructed tracker positions from local raw data and DD4hep segmentation; optional distinct truth diagnostic path |
| `seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitter.*` | ACTS fitting and EDM4eic track/measurement outputs; single-hit-per-required-layer policy |
| `seven_layer/local_eicrecon/algorithms/tracking/BeamTestACTSFitterConfig.h` | `useMPGD=true`, `useACLGAD=false`, μ⁻ hypothesis and other default parameters |
| `seven_layer/local_eicrecon/factories/digi/` | JANA2 factory wrapping digitization algorithm |
| `seven_layer/local_eicrecon/factories/tracking/` | Factories for truth-independent hit reconstruction, truth-diagnostic mode and ACTS fit |
| `seven_layer/local_eicrecon/plugins/BeamTestReco.cc` | Registers factory graph, collection names and event processors in the local plugin |
| `seven_layer/local_eicrecon/processors/BeamTestEventProcessor.*` | Event counters and reconstruction diagnostics |
| `seven_layer/local_eicrecon/processors/BeamTestMilleProcessor.*` | Gets fitted-track-associated SiMAPS hits; enforces five unambiguous layers; optional injected measurement shift; writes Mille records |
| `seven_layer/millepede/src/BeamTestMilleWriter.*` | Official Mille API wrapper; straight-line derivatives and parameter labels |
| `seven_layer/millepede/src/beamtest_mille_toy.cc` | Toy-model alignment tests independent of reconstruction |
| `seven_layer/millepede/config/beamtest_pede_5layer_template.txt` | Steering template fixing endpoint SiMAPS layers and solving L1–L3 x/y |

## Main scripts: which one should I run?

| Script | Purpose / status |
| --- | --- |
| `seven_layer/scripts/run_phase1_ddsim.sh` | **Simulation entry point:** 1-event and 200-event Geant4 samples plus geometry QA |
| `seven_layer/scripts/run_phase2_reconstruction.sh` | **Older experimental EICrecon default-plugin / CKF flow**, including a 500-event simulation; not the current local alignment entry point |
| `seven_layer/scripts/run_phase2_stageAB_minimal.sh` | Earlier native ePIC digitization/reco diagnostic |
| `seven_layer/scripts/run_phase2_stageCD_quick.sh` | Earlier native CKF experiment; explicit `|| true` can hide unsuccessful `eicrecon` execution |
| `seven_layer/scripts/build_and_run_local_eicrecon_simaps.sh` | Builds/runs the local plugin for earlier input `phase2_sim_quick.edm4hep.root`; not the current Mille-enabled baseline runner |
| `seven_layer/scripts/run_local_eicrecon_alignment_shifttest.sh` | Legacy fitter-internal shift; **not** the actual Mille measurement-injection closure |
| `seven_layer/millepede/scripts/build_mille_tools.sh` | Compiles **local toy** tools only; does not install official Mille/`pede` |
| `seven_layer/millepede/scripts/run_toy_closure.sh` | Official Mille/`pede` closure tests with a toy data generator |
| `seven_layer/millepede/scripts/run_integrated_mille_baseline.sh` | **Current primary JANA2/ACTS + Mille baseline**, needs pre-existing input ROOT and installed dependencies |
| `seven_layer/millepede/scripts/run_integrated_mille_injected.sh` | Same process, injecting an offset in the Mille measurement writer only |
| `seven_layer/millepede/scripts/run_pede_from_dat.sh` | Runs official `pede` on a Mille `.dat` and archives `.res` and logs |
| `seven_layer/millepede/scripts/summarize_pede_res.py` | Compares `pede` parameter solutions (baseline/injected) |
| `seven_layer/scripts/validate_rec_positions_assoc.py` | Position resolution diagnostic using associations for validation; not standard position reconstruction |
| `seven_layer/scripts/analyze_phase2_chain.py` | Collection/count summary for earlier Phase-2 reconstruction tests |
| `seven_layer/scripts/run_standalone_acts_fit.sh` | Old standalone ACTS regression path; not main integrated execution |

Additional `seven_layer/scripts/` files include `check_eicrecon_revision.sh`, `check_overlaps.py`, `plot_layout.py` and `summarize_hits.py`.

## Data products and their provenance

| Product | Generated by | Used by |
| --- | --- | --- |
| `sim_seven_layer_single.edm4hep.root` / `sim_seven_layer_beam.edm4hep.root` | `run_phase1_ddsim.sh` | Simulation / geometry diagnostics |
| `phase2_sim_beam.edm4hep.root` | Simulation step of `run_phase2_reconstruction.sh` | Earlier CKF tests |
| `phase2_sim_quick_normal_recofix.edm4hep.root` | Previous development run **not yet reproducibly scripted under this exact name** | Current integrated baseline/injected Mille scripts |
| `local_simaps_reco_mille_integrated.root` | Current baseline JANA2 script | ROOT-based tracking/QA |
| `local_beamtest_mille_integrated.dat` | `BeamTestMilleProcessor` during baseline JANA2 run | Official `pede` global fit |
| `<tag>_millepede.res` | `run_pede_from_dat.sh` | Alignment parameter inspection and comparison |
| `milleInjL2x0.2.dat`-tagged artifact | Integrated injection script | Controlled Mille measurement-bias closure |

Outputs are not version-controlled by default. Do not confuse the absence of ignored files in a fresh clone with missing tracked source code.

## Documents and validation history

- `seven_layer/reports/full_chain_code_audit.md`: priority-ranked findings and modifications.
- `seven_layer/reports/full_chain_validation_report.md`: V1–V9 status; post-audit accepted 68/80.
- `seven_layer/reports/upstream_eicrecon_comparison.md`: origin and adaptations; ACTS EDM conversion parity remains P1.
- `seven_layer/reports/phase1_dd4hep_simulation_report_2026-10-15.md`: simulation geometry validation.
- `seven_layer/reports/phase2_reconstruction_report.md`: legacy reconstruction stages.
- `seven_layer/reports/jana2_integrated_acts_report.md`: local ACTS validation notes.
- `seven_layer/millepede/reports/millepede_progress_report.md`: original milestones M1–M5; some counters predate later strict hit selection.
- `prototype/`: older reference/development path; keep separate from the `seven_layer/` primary workflow.

## Known mismatches to repair

- `seven_layer/config/seven_layer_layout.json` describes θ = 0–3 mrad, while the committed Phase-2 simulation uses 10–30 mrad; the JSON `identifier_schema` also differs from the actual XML bit-field schema.
- `README.md` on the old branch described `prototype/`; this new README redirects contributors to `seven_layer/`.
- The external Mille and `pede` build is not scripted in the committed tools.
- The current integrated runners assume an input filename not generated by a committed primary simulation runner.
- A pinned Docker image digest, deterministic simulation seed, clean-clone validation script, and ACTS/EDM output semantics review are outstanding.

See [WORKFLOW.md](WORKFLOW.md) before attempting an end-to-end run from a fresh clone.
