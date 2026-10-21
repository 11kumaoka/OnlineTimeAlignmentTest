# Validation and Local Reference Data

The repository tracks validation code, expected metrics, checksums, and migration
metadata. It does not distribute ROOT datasets, Mille Binary files, analysis logs,
external dependencies, build outputs, or backups.

## Historical 99-track regression

The minimum external input is:

`results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root`

SHA-256:
`947fee1308b8aa27516c12711c9cdb5e4b4160da2371b7094491418e276ee7a0`

Request this byte-identical file from the project maintainer and place it at the
path above. The original source position was z=0 mm. With dependencies installed
and the Plugin built, run from the repository root:

```bash
bash environment/run.sh bash validation/run_regression.sh results/regression_001
bash environment/run.sh python3 validation/check_root_outputs.py --result-dir results/regression_001
```

Expected results are 99 accepted tracks before/after, L2 Geometry Correction
+198.75 μm, L2 Rec−Sim −199.571→−0.821 μm, and Σχ²/Σstored ACTS nDoF
45.592→1.981. Tolerances are in `reference_metrics.json`.

## Fresh electron Closure

A fresh checkout can generate new events without the historical dataset:

```bash
bash environment/run.sh bash local_detector_testbench/scripts/run_closure.sh \
  --result-dir results/electron_001
```

The current electron case uses 1 GeV electrons at mean z=−500 mm. The validated
100-event sample yielded 98 tracks before/after and +201.13 μm correction;
this is a distinct sample, not the 99-track regression reference.
The original local result is `results/vertex_zminus500_20261019_01/closure100/`.
The final cleanup verification results are under
`results/final_simplification_20261021_01/{regression,fresh_electron_100}/`.
These result directories are intentionally excluded from Git.

## Full local preservation audit

`verify_preservation.py` requires the complete retained local dataset, not just
the one regression input. Restore the 221 baseline entries, 2,046 relocated data
files, and seven input links using `preserved_files.json`,
`relocated_data_sha256.json`, and `path_migration.json`. Historical records can
refer to former locations; follow the migration map without editing data content.
The persistent external archive is documented in `docs/FINAL_SIMPLIFICATION.md`.
It is a maintainer-local recovery source, not a path required by the workflow.
A clean Git clone without the local data cannot pass this complete audit.

The checker also verifies `validated_sources.json`, which pins the exact validated
ACTS fitter source including the electron hypothesis. This works with unstaged,
staged, and committed source. `electron_hypothesis_before.patch` retains the
original change as provenance; validation does not require an uncommitted diff.
Update the source checksum only after intentionally changing and validating that
source. Do not remove checksum entries to bypass missing or changed data.

```bash
python3 validation/verify_preservation.py
python3 validation/check_safety.py
```

The safety checker creates a new temporary result subdirectory and exercises CLI
refusal paths. It does not execute reconstruction or overwrite reference data.
