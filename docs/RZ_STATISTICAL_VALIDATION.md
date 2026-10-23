# Focused statistical validation of L1/L2 Rz alignment

Completed on 2026-10-22 in the existing `sweet_mahavira` EIC container. No commit, push, Geometry activation, physics/configuration change, or historical-data replacement was performed.

## Ensemble and fixed conditions

The primary ensemble contains **30 independent Simulation seeds × 100 events** of the canonical 1 GeV electron sample, with physical L1 Rz +10 mrad and L2 Rz −8 mrad. The first three seeds formed the pilot. One additional same-seed 100-event repeat checked reproducibility and is excluded from every ensemble statistic. No new 1,000-event or muon sample was generated.

The canonical gun remains at (0, 0, −500) mm. Geometry, material, segmentation, measurement errors, ACTS fitter and official Pede steering are unchanged. Per-sample beam JSON differs from `simulation/configs/electron_1GeV.json` only in random seed. The correction mode is `l1_l2_rz`; the Controller uses the zero-rotation reference scenario, not injected Truth. Truth enters only Simulation and this statistical comparison.

Build: `build/rz_alignment_20261022_02`, ACTS 45.3.0; official Pede 05.01.06. The plugin SHA-256 is `827fedac780454bb649c41a5a86ff976ca9b99afe0ccd1025644dfbcab505c7e`. The existing source-matched finite-difference gate is `result/rz_alignment_20261022_01/rotation_derivative_gate_v2.json`.

Each sample has its own physical stages, RawHit delivery, Controller state, Geometry registry, and exact final-candidate reconstruction. Input RawHit file checksums are identical across that sample’s iterations and final reconstruction. Saved Geometry remains an inactive candidate; the active Geometry stays nominal. Completed stage hashes are verified and an output inventory is saved. Filesystem permissions were not changed.

The repeat matched all 66 simulated particle/hit branches, all nine RawHit branches, initial Mille bytes, initial Pede parameters/errors, and final ACTS metrics. EventHeader wall-clock timestamps and whole-file ROOT hashes need not match between separate simulations; no timestamp field was excluded from the within-sample input checksum checks. Digitization retains its existing run/event/name-based timing RNG. The spatial fit uses two position coordinates, not hit timestamps. This is an independent Geant4-seed ensemble conditional on the unchanged Digitization implementation.

## Primary initial-fit statistics

Pede labels 3001/3002 represent measurement rotation **bias** a in radians. The physical correction estimate is c = −a. The primary pull is `(−a_initial − c_injected) / sigma_initial`, using the corresponding initial-fit nominal error. Positive means an overestimated physical correction. No final-fit error is substituted and no errors are rescaled.

All rotation quantities below are in **mrad**. Spread is the sample standard deviation (n−1 denominator); the population RMS about the ensemble mean and RMS about zero are also saved in JSON.

| Layer | Mean initial correction | Mean bias | Across-seed spread | Mean nominal sigma | Pull mean | Pull sample SD |
|---|---:|---:|---:|---:|---:|---:|
| L1 | +10.00606 | +0.00606 | 0.15939 | 0.11062 | +0.055 | 1.433 |
| L2 | -8.03362 | -0.03362 | 0.15859 | 0.09486 | -0.347 | 1.661 |

| Layer | Bias 95% t interval [mrad] | Pull mean 95% t interval | Pull SD 95% bootstrap interval | Nominal sigma min–max [mrad] | Coverage within 1 / 1.96 sigma |
|---|---|---|---|---|---|
| L1 | [-0.0535, +0.0656] | [-0.4799, +0.5900] | [+1.0182, +1.7608] | 0.10419–0.12091 | 18/30; 24/30 |
| L2 | [-0.0928, +0.0256] | [-0.9670, +0.2734] | [+1.2307, +2.0391] | 0.08938–0.10367 | 15/30; 21/30 |

Mean intervals use Student t; SD bootstrap intervals use 20,000 independent resamplings of the **30 seeds**, with analysis RNG seed 20261023. Gaussian chi-square SD intervals, bias bootstrap intervals, and exact binomial coverage intervals are also saved. These are finite-ensemble estimates, not certified tail probabilities. The two layer estimates share tracks and are correlated. ROOT histogram statistics display the n-denominator RMS about the mean (1.409 for L1 and 1.633 for L2 pulls); the tables use the requested n−1 sample standard deviation.

- L1: the bias interval includes zero. The pull-SD bootstrap interval excludes one. The empirical spread/mean nominal error ratio is 1.441.
- L2: the bias interval includes zero. The pull-SD bootstrap interval excludes one. The empirical spread/mean nominal error ratio is 1.672.

## Final cumulative Geometry corrections

These are extracted from the saved final XML rotation matrices and cross-checked against Controller cumulative updates. Their ensemble spread is evaluated separately. Successive fits use the same RawHits and are correlated: their nominal errors are **not** added in quadrature or presented as a final cumulative uncertainty.

| Layer | Mean final correction [mrad] | Final mean bias [mrad] | Final sample spread [mrad] |
|---|---:|---:|---:|
| L1 | +10.00664 | +0.00664 | 0.15955 |
| L2 | -8.03345 | -0.03345 | 0.15859 |

## Solver, tracks and convergence

Converged: 30/30 under the existing demonstration tolerance (10 microrad); iteration counts: `{'2': 30}`. This numerical stopping rule is not statistical certification.

Initial accepted tracks: mean 95.43, range 91–100, total 2863. There were 137 events without an accepted track. This count includes selection/multiplicity effects and must not be labeled entirely as numerical fitter failures.

Initial Pede statuses: `{'1   Ended with warnings (bad measurements)': 30}`. Last statuses: `{'1   Ended with warnings (bad measurements)': 30}`. Every stage's process exit code, Pede end status, warning lines and rejection history are in `analysis/samples.json` and the original stage logs.

4/30 samples had at least one rejected local fit during the initial Pede solve. Maximum rejection count per initial solve ranged 0–1. Counts at successive function evaluations are not summed as distinct rejected tracks.

| Quantity | Ensemble mean | Min–max |
|---|---:|---:|
| Initial Pede chi2/NDF | 2.34024 | 1.64201–4.78197 |
| Last iterative Pede chi2/NDF | 2.33895 | 1.64055–4.77856 |
| Initial ACTS chi2/stored-NDF | 23.69301 | 20.62292–26.01530 |
| Exact final Geometry ACTS chi2/stored-NDF | 1.59636 | 0.98183–4.63853 |

The last iterative Pede solve uses the penultimate Geometry and produces the final candidate. ACTS after-alignment metrics above come from a separate reconstruction of the **exact final** candidate. ACTS stored-NDF is 10 per accepted five-plane track, not the four-local-parameter statistical NDF. Pede uses its recorded accepted-local-fit NDF minus two free global rotations; local-fit rejections can change that sample.

Pede’s `bad measurements` status is a warning, not a shell failure. Installed source `external/src/millepede-ii/src/pede.f90:9167–9203` sets a warning for chi2/NDF outside approximately 0.9–1.1, or an excessive rejected-fit fraction, and prints the reasons to stdout. Thus a zero-rejection fit can still warn. The printed recommendation to multiply input errors was **not applied**. Existing rejection and matrix-reuse defaults are unchanged.

| Layer | Pull vs tracks r (95% CI) | Absolute pull vs tracks r | Nominal error vs tracks r | Pull SD: no rejects / with rejects |
|---|---|---|---|---|
| L1 | +0.226 [-0.1457, +0.5425] | -0.109 | -0.344 | 1.461 (n=26) / 0.509 (n=4) |
| L2 | -0.106 [-0.4492, +0.2642] | +0.261 | -0.342 | 1.707 (n=26) / 1.074 (n=4) |

These are exploratory Pearson correlations, not causal tests. Narrow count ranges and small rejection groups limit power; absence of significance does not prove independence. All warning cases are retained.

| Layer | Seed with absolute pull > 3 | Pull | ACTS tracks | Maximum initial Pede rejects |
|---|---:|---:|---:|---:|
| L1 | 370545797 | +3.411 | 97 | 0 |
| L1 | 1337907878 | -3.123 | 92 | 0 |
| L2 | 370545797 | +3.987 | 97 | 0 |
| L2 | 518791119 | -3.084 | 98 | 0 |

All four absolute-pull-above-three layer/seed cases had **zero** initial local-fit rejections; their initial Pede chi2/NDF ranged 2.242–2.467. All samples warned, so the warning flag itself cannot discriminate unusual pulls. Absolute pull versus initial Pede chi2 had Pearson r = 0.122 (L1, p = 0.522) and 0.018 (L2, p = 0.926); no association is resolved by these 30 seeds. The largest Pede chi2/NDF sample (seed 415398481, 4.782) had one rejected local fit but pulls only +1.692/+1.714. This does not establish a causal mechanism or exclude tail effects. Detailed associations are in `analysis_checks.json`.

ROOT integrity checks passed: 12 TH1D histograms, six graphs (two TGraphErrors), and 18 canvases, each distribution/graph containing 30 samples. All **60** iterative Pede process exit codes were zero and every reported Pede NDF matched `6 × (ACTS tracks − final rejected local fits) − 2`. The preservation audit found 150 original source/build files and 8,260 historical data files unchanged, and inventoried 5,239 completed output files.

## Interpretation and limitations

A successful DD4hep/ACTS Geometry transformation, derivative gate and iterative closure establishes the supported correction convention and numerical implementation. It does **not** establish that Pede nominal covariance describes this electron ensemble. Pull widths and their intervals above are the direct statistical diagnostic. Elevated chi2 and broad pulls motivate scrutiny of the existing effective error model; this study does not uniquely separate multiple scattering, electron tails, track correlations, selection and matrix/rejection effects. No fitter, derivative, material model, measurement uncertainty or steering was changed.

With 30 seeds, a Gaussian sample SD alone has roughly 13% relative sampling uncertainty; non-Gaussian tails can be less stable. Bootstrap intervals also cannot reveal tails absent from these 30 seeds. Any nonzero mean-bias indication should be treated with the shown finite-ensemble intervals and the shared-layer correlation, not extrapolated to unsupported DOFs.

A limited, separately reported independently seeded 1,000-event cross-check could help examine event-count scaling and sensitivity to rare tracks. A single larger sample would not calibrate coverage. No such campaign was launched; the independent 100-event ensemble is the primary result.

## Artifacts, commands and preservation

All outputs are under `result/rz_statistics_20261022_01/`:

- `study.json`: exact seed list, injection and analysis seed; `sample_NNN_v2/`: immutable-by-workflow sample stages, input checksums, Controller records and inactive Geometry versions.
- `analysis/summary.json`, `analysis/samples.json`: machine-readable statistics and full per-seed diagnostics.
- `analysis/rz_statistics.root`: TBrowser histograms, graphs and canvases; `analysis/*.pdf`: ROOT-rendered rotation estimates, pulls, nominal errors, count/rejection dependence and Pede/ACTS chi2 distributions.
- `pilot_event_reproducibility.json`, `pilot_fit_reproducibility.json`: reproducibility checks; `sample_001_repeat/` is excluded.
- `sample_001/`–`sample_003/`: retained pre-simulation launch failures caused by an overwritten PYTHONPATH. Retried in fresh `_v2` directories after restoring the container environment.
- `COMMANDS.md`, `run_samples.py`, sample `driver.log`, stage `command.json`/`exit.json`/`stdout.log`: exact launch and underlying software commands.
- `preserved_sources.json`, `historical_data_sha256.json`, `final_preservation_audit.json`, `completed_outputs_sha256.json`: source/build/data preservation and output integrity.

Executed primary commands (from repository root):

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/rz_statistics_20261022_01/run_samples.py 1 2 3
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/rz_statistics_20261022_01/run_samples.py repeat
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/rz_statistics_20261022_01/check_pilot.py
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/rz_statistics_20261022_01/run_samples.py 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -m validation.rz_statistics --study result/rz_statistics_20261022_01
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 result/rz_statistics_20261022_01/final_audit.py
python3 validation/verify_preservation.py
```

Analysis requires the container’s existing NumPy, SciPy, uproot and PyROOT. Re-execution requires a new study directory; completed output directories must not be overwritten. Open the plots with ROOT `TBrowser`, e.g. `root -l result/rz_statistics_20261022_01/analysis/rz_statistics.root`, then `new TBrowser;`.

The initial and final preservation audits retain the uncommitted electron hypothesis, numerical fitter, nominal Geometry, prior L2-only and Rz results and historical data. New maintained files are the statistical analysis module, ROOT plotting module, and this report; no existing numerical source file was edited. The pinned validated Plugin was reused; no rebuild or historical L2-only reconstruction rerun was performed in this statistics-only task. Python syntax checks and `git diff --check` passed.

### Exact independent Simulation seeds

1459750402, 757227434, 1244008654, 607641966, 1833699784, 370545797, 104186860, 2023881840, 1768689040, 518791119, 494881634, 503713357, 6283025, 1532578546, 1772746774, 1174225171, 282759267, 126896957, 427031124, 415328459, 662572180, 1372524430, 1507644553, 1781926977, 1412318779, 1337907878, 228919551, 1589519046, 415398481, 1624513301
