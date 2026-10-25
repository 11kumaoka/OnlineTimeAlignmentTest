# Native Geant4-to-calibration workflow: technical validation

This report separates executed engineering checks from physics-quality
validation. The public interface is `python3 -B -m calibration.workflow`;
practical instructions are in [the user guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md).
The final three examples pass technical workflow and integrity checks. Physics
quality remains unvalidated because all six Pede fits retain high-chi2 warnings.
All candidate Geometry remains **unapproved**. No production Geometry is
activated, and a successful same-data correction is not an uncertainty-coverage
or material-aware tracking result.

## Source and execution authorities

The starting commit is `eaabd7e2dd68d429fb52fabfd216d74aaffd2729` on
`feature/upstream-acts-geometry`. The existing nine modified and six untracked
Geant4 integration files were preserved before this work. Their exact backup,
patch and manifest are in
`result/native_workflow_20261025_01_audit/working_tree_snapshot/`.
The initial maintained-source inventory contains 345 files and 3,008,475 bytes.

The first executed public workflow used **source freeze v1**, containing 277
execution-source files:

- `result/native_workflow_20261025_01_audit/execution_source_freeze/sources.json`
- SHA256: `a5b40d5bf5c6ffcd33ad3bc253631d7e81b4548c5faeb4e4b410b3b9d0fd6c06`
- Build: `build/native_workflow_20261025_01`

Here, v1/v2 identify development source freezes. They are not alternative
physics models, independent statistical samples, or changes to the on-disk
schema names. A later observer correction and its fresh execution freeze must
be recorded separately; the v1 results below must not be relabeled as v2 tests.
The v1 runs, including the failed multi-sensor attempt, remain preserved.

The fixed Docker image is
`sha256:67c914295a92396040c3051360d70786df9c1ee8458264ad0b83cd1a8ccf3d05`.
The audited environment contains npsim 1.4.7, DD4hep 1.36, Geant4 11.3.2.east,
ACTS 45.3.0, ROOT 6.38.00, EDM4hep 1.0.0 and podio 1.7.0. Installed EICrecon
revision is `195966d41899800eaeca6fbafd63cd53735e6543`. Each public run snapshots
actual executable/source/configuration hashes, version-command output, build
identities and invoked commands. No installed package was modified.

## Data and control flow

The public orchestrator invokes the maintained independent stages:

1. Prepare distinct nominal/initial and displaced Truth XML files. Reload each
   through the real DD4hep/ACTS geometry audit and check sensor identities and
   physical containment.
2. Run installed npsim/DDSim/Geant4, preserving Air and Silicon materials,
   FTFP_BERT and the installed optical configuration.
3. Register the installed official `SiliconTrackerDigi_factory` for SiMAPS,
   MPGD and AC-LGAD. Preserve every original event and source collection in the
   complete digitized ROOT file.
4. Project exactly one valid SiMAPS RawTrackerHit on each L0--L4 into the
   existing native input contract. Preserve complete EventHeaders and exact
   CellID/charge/timestamp values. Record every multiplicity rejection.
5. Run the existing native Controller, official EICrecon-style hit/measurement
   conversion, ACTS CKF and `NativeMilleModel`. Execute official Pede, apply
   existing physical Geometry Correction, and reconstruct the same immutable
   RawHits with the candidate Geometry.
6. Publish an unapproved candidate and a JSON/Markdown/ROOT report only after
   the declared technical protocol completes. No activation operation exists
   in the public workflow.

The full reconstruction interface currently requires electrons and 1 GeV gun
energy because the seed prior remains fixed. `simulation.native` exposes other
Geant4 particles/energies for simulation-only use; the public complete workflow
refuses unsupported particle/energy combinations before producing data. The
native radial beam travels along +X through x250--550 mm. Original +Z endcap
RawHits are never relabeled as barrel data.

Simulation Truth determines transport and may be plotted after inference. It
is not passed as an alignment observation, update target or convergence test.
The Controller receives RawHits, their producer provenance, an initial Survey
Geometry and the requested alignment configuration. Provenance can contain
Truth Geometry identities/poses; storing that record does not make it a fit
constraint. The projection itself uses only valid RawHit identities and
multiplicities, without MCParticle, SimHit, fitted-track or residual selection.

The retained telescope-specific adapters are XML fixture preparation and
metadata, the five-plane RawHit projection/seed contract, native Mille record
export, the physical correction adapter and integrity observers. The installed
Geometry service/SurfaceMap and the maintained EICrecon-source measurement
conversion and ACTS CKF remain the tracking path. No replacement simulator, fitter, navigator or alignment solver is added.

## Provenance and immutable stage contracts

| Record | Schema | Responsibility |
| --- | --- | --- |
| Public configuration | `native-workflow-v1` | Explicit Geometry, gun, seed, event count, aligned parameters, environment and mode |
| Simulation configuration | `native-npsim-v1` | Actual npsim gun/command, executed XML and software identities |
| Simulation producer binding | `native-npsim-binding-v1` | ROOT checksum, producer completion/configuration, command/XML, gun, seed, events, readouts and seven real sensor IDs |
| Digitization provenance | `native-geant4-digitization-v1` | Official producer, conditions, complete source events and RawHit collections |
| Projected input provenance | `native-geant4-input-v1` | Exact Raw ROOT/payload identities, selected source indices, full rejection ledger and producer binding |
| Controller manifest/checkpoint | `native-calibration-v1` / `native-iteration-v1` | Frozen execution/build/input identities and verified Geometry parent/child chain |
| Public result/index | `native-public-workflow-result-v1` / `native-public-artifact-index-v1` | Engineering/quality/integrity statuses and discoverable generated artifacts |

A different digitization Survey XML must preserve the actual barrel
constructors, complete readout definitions and all seven audited
VolumeID/GeometryIdentifier pairs. Pose differences are recorded explicitly.
Reusing a completed Simulation in the public workflow additionally requires
exact declared gun settings, event count, seed and all actual Truth sensor
poses. A matching filename or similar CellIDs alone is insufficient.

Completed stage hashes are verified before reuse. Controller checkpoints are
published only after supervised stages finish; the Raw ROOT bytes and channel
payload remain identical across corrections. Iterative fits share RawHits, so
their uncertainties are never combined as independent measurements. A changed
execution-source set correctly refuses restart under an old source identity;
use the corresponding preserved source environment or start a fresh run.

## Strict, diagnostic and integrity outcomes

Strict validation retains its established quality policy. Offline diagnostic
mode can retain a recognized high-chi2 Pede advisory and unmet declared
resolution targets while evaluating a finite, identifiable physical update.
It does not authorize rejected local fits, unknown solver warnings, wrong
associations, corrupt RawHits, nonfinite results, rank deficiency, invalid
Geometry or containment violations. No error rescaling or steering change is
applied.

Engineering success requires at least one physically audited correction and a
fresh reconstruction/solve of the resulting Geometry, followed by a terminal
verified checkpoint. A diagnostic iteration limit can therefore be an
engineering success without convergence. All such reports retain
`physics_quality: not_validated` and `approval_status: unapproved`.

## Executed source-v1 single-parameter demonstrations

Both examples inject **L1 Global Y +0.080 mm** and fit only label 700102. They
use the unchanged 1 GeV electron configuration, official digitization
conditions, material-free ACTS model, measurement uncertainties, selection cut
1000, native equations and Pede steering. Each applies one correction and
performs a second fit using exactly the same projected RawHits.

| Quantity | Pencil smoke | Broad example |
| --- | ---: | ---: |
| Generated events / seed | 64 / 2026102511 | 256 / 2026102512 |
| Projected and reconstructed tracks | 63 | 248 |
| Raw-only multiplicity rejections | 1 | 8 |
| Initial Pede Y correction [mm] | +0.078865 | +0.079499 |
| Initial printed nominal Pede error [mm] | 0.0015058 | 0.00075897 |
| Selected rank / scaled condition | 1 / 1.0 | 1 / 1.0 |
| Remaining correction after fresh fit [mm] | +2.2638e-7 | -4.5342e-7 |
| ACTS chi2/stored-NDF, initial | 5.643925909012083 | 5.872847889315698 |
| ACTS chi2/stored-NDF, corrected | 1.2900174523156787 | 1.4487344351747344 |
| Initial Pede chi2 / NDF | 812.6993289610494 / 377 | 3592.7927078838793 / 1487 |
| Initial Pede chi2/NDF | 2.1557011378277173 | 2.416134975039596 |
| Corrected Pede chi2/NDF | 2.155701141848409 | 2.4161355832926956 |
| Process exit / Pede end status, both fits | 0 / 1 | 0 / 1 |
| Rejected local fits | 0 | 0 |
| Applied corrections / completed fit evaluations | 1 / 2 | 1 / 2 |
| Technical / physics-quality result | passed / not validated | passed / not validated |

The corrected Geometry uses the printed Pede correction, not the independent
normal-equation estimate or the injected displacement. The listed remaining
updates are approximately +0.22638 nm and -0.45342 nm; they are same-data
remaining corrections, not demonstrated absolute calibration precision.

The local smoothed-state residual RMS values are:

| Local coordinate [mm] | Pencil initial -> corrected | Broad initial -> corrected |
| --- | --- | --- |
| u | 0.031532258938929913 -> 0.011114111935752707 | 0.03216380804588745 -> 0.0122355602855201 |
| v | 0.011596382438327777 -> 0.011596381948422024 | 0.011833492681313978 -> 0.011833508028257002 |

These are fitted local Hit Residuals, not the historical `Rec - Sim` statistic.
The ACTS denominator is its stored scalar measurement dimensionality (10 per
track); Pede uses the profiled statistical NDF, `6*Ntracks - 1` here. The two
ratios must not be interpreted interchangeably; the ACTS ratio is not a
statistical reduced chi2.

Pede returned `1 Ended with warnings (bad measurements)` in both examples.
Its suggested error factors 1.47 and 1.55 were **not applied**. The pencil sample
also misses the declared 1 micrometre nominal resolution target. Positive
information rank and a successful correction are not evidence of adequate
uncertainty coverage. Geant4 transports through material whereas the existing
ACTS fit has no assigned material/process noise. Scattering, energy loss,
bremsstrahlung, secondary deposits and the current response approximations are
possible contributors; this task does not isolate their relative effects or
validate an improved uncertainty model.

Source-v1 outputs and independent receipts:

- `result/native_workflow_smoke_20261025_01/`
- `result/native_workflow_example_20261025_01/`
- `result/native_workflow_20261025_01_audit/public_smoke_independent_04/report.json`
- `result/native_workflow_20261025_01_audit/public_example_independent_03/report.json`

Each successful public result contains `report/report.md`, `summary.json`,
`diagnostics.root` and root-level `run_manifest.json`. The independent audits
reopened the ROOT objects, reloaded all six relevant Geometry XMLs, inspected
both official Mille binaries and checked unchanged complete headers/RawHit
values. Their classifications are technical integration passed, physics
quality not validated, safety/integrity passed.

## Source-v1 multi-sensor attempt and observer defect

`result/native_workflow_multi_20261025_01/` explicitly reused the completed
2304-event producer at
`result/native_geant4_scope_a_20261025_01/simulation/`. No new 2304-event campaign
was launched. All 2218 projected events were reconstructed. Scope A fits L1/L2
Y and L1 Rx/Ry/Rz; it injects Y shifts +0.080/-0.060 mm and L1 rotation vector
(+0.001,+0.0005,-0.0005) rad.

The first Pede solve had rank 5, scaled condition 1.867007950851166,
chi2/NDF 30939.298032245755/13303 = 2.325738407295028, zero rejected local fits,
process exit 0 and the retained high-chi2 end status 1. Its printed estimates
were:

| Parameter | Estimate | Nominal printed error | Unit |
| --- | ---: | ---: | --- |
| L1 Y | +0.080319 | 0.0002661 | mm |
| L1 Rx | +0.0010172 | 0.000016366 | rad |
| L1 Ry | +0.00048706 | 0.00036983 | rad |
| L1 Rz | -0.00085807 | 0.0003297 | rad |
| L2 Y | -0.060369 | 0.00024636 | mm |

One physically audited candidate was created and freshly reconstructed, but
the Controller then stopped at its cross-iteration local-coordinate observer.
It did **not** publish a final engineering-success result or approve Geometry.
All failed outputs and the first valid checkpoint remain available.

The observer assumed every unchanged intrinsic measurement must retain its
serialized local coordinates within a universal 2e-6 mm absolute difference.
The official conversion stores world positions and local measurements in
float32. Rotating Geometry and transforming the rounded world position back
to local coordinates can change the final float32 by one ULP while the
intrinsic segmented measurement remains identical.

The two actual reconstruction audits contain exactly 11 scalar violations of
that universal bound. Each is exactly one float32 ULP; the maximum difference
is 3.814697265625e-6 mm. For source event 2, CellID 283727292193048607, local u
changes from -34.918128967285156 to -34.91812515258789 mm. The maximum covariance
difference is 1.3877775340328552e-21 mm2, with no covariance violation of the
existing 1e-12 mm2 comparison. Raw channel payload SHA256 remains
`1bf9714cb4068a8e1fd75cc891280be57ba675ad2c983637760126b31f631af3`.

This is a demonstrated observer-contract defect, not evidence that the CKF,
measurement errors, RawHits or physical alignment equations changed. The
source-v1 initial fit also reproduces all 2218 prior native Mille records and
the actual Mille binary exactly; see
`result/native_workflow_20261025_01_audit/public_multi_fitter_identity/summary.json`.
The source-v2 audit below validates the exact official serialization pipeline
and unchanged intrinsic segmentation instead of enlarging a universal coordinate
tolerance. Its implementation and executions are separate from the preserved
v1 result.

## Navigation, regressions and preservation

The opt-in Geometry-aware observer uses the installed ACTS Navigator and
independent bounded SurfaceMap intersections. A track outside an unused
finite sensitive rectangle need not produce a hole on that sensor. Real
crossing/association inconsistencies still fail. This observer change does
not alter CKF selection or fitted states. The historical five legitimate
one-hole edge trajectories are accepted by the observer; their initial native
Mille outputs remain byte-identical. Separate positive and negative Geometry
controls are recorded in
`result/native_workflow_20261025_01_audit/navigation_geometry_controls_02/`.
The historical default synthetic path retains its original checks.

Source-v1 validation completed the 18-command consolidated suite, including
217 Python unit tests, official Geometry conversion, one-track reconstruction,
physical/analytical derivatives, official binary/native-versus-legacy
mathematics, safety and preservation checks. The fresh 32-track regression
retained corrections +0.14914/+0.20318 mm and ACTS chi2/stored-NDF
37.16731567382813 -> 0.6908491410315036. Scientific report fields, fitted/native
outputs and corrected XML matched their preserved reference.

An actual SIGTERM interrupted the second reconstruction of a diagnostic
Controller run. Resume used a fresh attempt, preserved 138 prior immutable
files, did not promote the partial iteration, and recovered the same completed
fit states, residuals, information and Mille binaries as the reference run.
The receipt is
`result/native_workflow_20261025_01_audit/diagnostic_restart/report.json`.

The pre-edit preservation baseline and its completed read-only verification
cover **49,783 unique files, 24,053,458,194 bytes, 94 exact trees and 9 symlinks**,
including older Geant4 outputs/builds and failed artifacts. Separate installed
software verification checks nine ACTS libraries, 13 older local binaries,
seven Controller binaries, five programs, seven simulation Python files and
four simulation libraries. Formal `external/install` Mille2/pede remain
unchanged. Receipts are `final_preservation/` and `final_software/` under the
audit root; their timestamps identify the source-v1 verification checkpoint.
Later source-v2 checks must retain the same historical protections.

No historical reference, detector uncertainty, material, nominal Geometry,
Mille derivative, Pede steering or SO(3) correction was changed to obtain a
passing result. The tracked numerical sources and compiled CKF, measurement,
Mille model/export, metadata and digitization objects are independently pinned
in `cpp_library_identity_02/summary.json`. The tracking Plugin itself changes
when its observer is rebuilt; it is not claimed byte-identical as a whole.

## Commands actually executed for source v1

From the repository root, with the fixed existing container:

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_smoke.json \
  --output-dir result/native_workflow_smoke_20261025_01 \
  --build build/native_workflow_20261025_01 --validation-mode diagnostic

bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_example.json \
  --output-dir result/native_workflow_example_20261025_01 \
  --build build/native_workflow_20261025_01 --validation-mode diagnostic

bash environment/run.sh python3 -B -m calibration.workflow prepare \
  --config calibration/config/native_workflow_multi.json \
  --output-dir result/native_workflow_multi_20261025_01 \
  --build build/native_workflow_20261025_01 --validation-mode diagnostic \
  --simulation-stage result/native_geant4_scope_a_20261025_01/simulation
bash environment/run.sh python3 -B -m calibration.workflow simulate \
  --run-dir result/native_workflow_multi_20261025_01
bash environment/run.sh python3 -B -m calibration.workflow digitize \
  --run-dir result/native_workflow_multi_20261025_01
bash environment/run.sh python3 -B -m calibration.workflow calibrate \
  --run-dir result/native_workflow_multi_20261025_01
```

The two complete single-parameter commands returned exit 0. The last
multi-sensor calibration command returned nonzero at the observer defect
explained above. These are execution records, not commands to overwrite the
preserved directories; choose fresh output names when reproducing them.
Exact inner commands, working directories and exit statuses are retained in
each run's `execution/`, Geometry audit and Controller job directories.

## Completed source-v2 public workflows

Source v2 fixes only the opt-in observer/Controller representation check; it
adds no tracking, covariance, solver or Geometry-correction mathematics. The
279-file manifest is `execution_source_freeze_v2/sources.json` under the audit
root (SHA256 `27b0651f57440ea9941fc8aa451a09aa17ba5ce510fa243f56fcb8e55d42b3aa`).
Its separately sealed content archive is `execution_source_freeze_v2/files/`.
The complete 277-file source-v1 content archive is also retained at
`source_v1_content_snapshot/`. All original source-v1 results remain untouched.

The clean build is `build/native_workflow_20261025_02`. The actual measurement
converter, CKF, NativeMilleModel and Mille plugin objects, metadata and
Digitization plugin still match the earlier build byte-for-byte. The new
observer Plugin itself changes as intended. All fourteen recorded runtime
library checks passed; actual Mille2 resolves to `external/install/lib` and
all nine installed ACTS libraries remain unchanged.

All three source-v2 public workflows completed successfully:

| Example / output directory under `result/` | Generated / projected / tracks per fit | Initial printed corrections | ACTS chi2/stored-NDF before -> after | Pede chi2/NDF before -> after |
| --- | --- | --- | --- | --- |
| Pencil: `native_workflow_smoke_20261025_02/` | 64 / 63 / 63 | L1 Y +78.865 um | 5.643925909 -> 1.290017452 | 2.155701138 -> 2.155701142 |
| Broad: `native_workflow_example_20261025_02/` | 256 / 248 / 248 | L1 Y +79.499 um | 5.872847889 -> 1.448734435 | 2.416134975 -> 2.416135583 |
| Multi-sensor: `native_workflow_multi_20261025_02/` | 2304 / 2218 / 2218 | L1 Y +80.319 um, Rx +1.0172 mrad, Ry +0.48706 mrad, Rz -0.85807 mrad; L2 Y -60.369 um | 10.957180611 -> 1.394974462 | 2.325738407 -> 2.325784234 |

Each run applied exactly one correction, completed two fresh fit evaluations,
and met the unchanged same-data convergence gates. Every final candidate is
**unapproved**, `geometry_activated` is false, and physics-quality validation
remains **not validated**. All six actual Pede processes exited zero with the
recognized high-chi2 end status 1 and zero rejected local fits. No input errors,
nominal Pede uncertainties or steering values were rescaled.

The 64- and 256-event source-v2 examples regenerated Geant4 data from scratch
with the same explicit seeds 2026102511 and 2026102512. These are repeated
technical reproductions, not new independent statistical samples. The
multi-sensor example explicitly reused the completed, matching 2304-event
producer at `result/native_geant4_scope_a_20261025_01/simulation` (seed 2026102503).
Its producer ROOT, command, gun, readouts and all seven Truth poses were checked
before reuse; no additional large simulation campaign was started. A new
collaborator can omit `--simulation-stage` to generate that configured sample.
No private reference data is needed for the two from-scratch examples.

The multi-sensor initial nominal errors are, in parameter order,
L1 Y 0.26610 um, Rx 0.016366 mrad, Ry 0.36983 mrad, Rz 0.32970 mrad and
L2 Y 0.24636 um. The final remaining updates are -0.26561 nm, +0.036039 urad,
-15.901 urad, +2.2302 urad and -0.39507 nm respectively. Initial covariance is
retained for the stopping rule; successive covariances are never combined.
These values describe same-data consistency, not demonstrated absolute accuracy.

The multi-sensor residual RMS is u 0.04501008873373748 -> 0.01155109386787832 mm
and v 0.012865111064970394 -> 0.012064880253819615 mm. Pede's optimum chi2 changes
little because it already fits the global correction in the first solve; a
Geometry update does not remove the underlying straight-line model mismatch.
For the broad single-Y sample, corrected ACTS chi2 is 3592.861399233341 with
stored NDF 2480, while Pede chi2 is 3592.7936123562386 with statistical NDF 1487.
The similar chi2 sums and different denominators explain the different ratios;
there is no justification for tuning errors until both displayed ratios equal 1.
Material/process-noise mismatch and electron interactions remain plausible
contributors, not experimentally isolated causes. Bias and coverage require a
separate physics study.

## Source-v2 integrity, regression and restart checks

The exact source-v2 observer validation includes 20 actual official
Hit Reconstruction/measurement conversions in nominal and rotated Geometry and
10 tampering refusals. Direct pixel centers and pitches remain exact across
Geometry versions. Wrong global/local/covariance values by one float32 ULP,
wrong pixel variance and wrong CellID are rejected. The original 2e-6 mm legacy
comparison and all covariance/model thresholds are unchanged.

The actual multi-sensor pair has 2218 tracks in each fit, with 2213 two-hole and
five legitimate one-hole tracks. The same five historical edge events miss
AC-LGAD's finite sensitive bounds and cross MPGD. Both actual installed
Navigator targets and independent bounded intersections agree. All 11 original
one-ULP local-coordinate differences remain present and are correctly checked
against their exact per-Geometry serialization; no measurements were changed.
Both full native records and the entire official Mille binaries match the
preserved failed source-v1 pair. The independently sealed evidence is
`public_multi_navigation_serialization_v2/` under the audit root.

The new fresh 32-track reference exactly retains L1/L2 +149.14/+203.18 um and
ACTS 37.16731567382813 -> 0.6908491410315036. The consolidated suite executed
18/18 commands and 231 unit tests successfully, including fresh Geometry and
benchmark builds, one-event official reconstruction, native/legacy and
mathematical Mille checks, safety and preservation. Its independent seal checks
73 stage outputs and all 279 frozen sources. The exact commands/reports are
`regression_v2/`, `full_suite_v2/` and `full_suite_v2_independent_seal/` under the
audit root; the public 32-track result is
`result/native_workflow_regression_l1_l2_y_20261025_02/`.

Python AST checks passed for 104 maintained files, Shell syntax for 13 files and
five actual CLI-help commands (`syntax_and_help_v2/`). No physics algorithm was
modified, so the 28-case historical statistical campaign was not repeated.
Historical test definitions and results remain intact.

A real SIGTERM interrupted the second source-v2 eicrecon process after a valid
first correction checkpoint. Explicit resume used a new attempt, preserved all
138 prior immutable files and 285 reference-run files, and recovered identical
XML/Mille bytes, fitted states, new serialization proofs, residuals, metrics,
convergence and Pede information. Only the verified fresh derivative-gate
pathname differs. Evidence is `diagnostic_restart_v2/` under the audit root;
`result/native_workflow_restart_20261025_02/` is a separate Controller run.

Independent full-file public audits passed for the source-v2 pencil and broad
samples: `public_smoke_v2_independent/` and `public_example_v2_independent/`.
They reopen ROOT, inspect every official Mille record, check actual Raw/headers,
finite/PD information, nominal errors, exact canonical invariance and actual
Geometry reloads. The multi-sensor full-file audit also passed with actual exit 0
at `public_multi_v2_independent/`: 4,436 track records, 44,360 scalar Mille
measurements, 66,540 actual-Geometry derivative vectors, full-rank positive-definite
5x5 information, 11,090 invariant channel records, six XML reloads and 43 ROOT
objects. All 504 run files (193,304,004 bytes) and all 279 sources remained exact.

The sealed consolidation at `public_v2_consolidated/` freshly verifies all
three public audits and the real restart: 2,624 source events, 2,529 immutable
Raw events, 5,058 fitted track records across six fits, 50,580 scalar Mille
measurements, 68,406 actual-Geometry derivative vectors, 18 XML reloads and
121 ROOT objects. All 1,074 existing public-run files (224,241,076 bytes) and
all 279 frozen sources were preserved. Its `report.json` records the exact
independent audit and restart commands.

The final source-v2 preservation checks rehashed all 49,783 protected files
(24,053,458,194 bytes), 94 exact trees and 9 symlinks with zero mismatches.
Installed-library checks also pass again. Receipts are `final_preservation_v2/`
and `final_software_v2/`. All original 15 modified/untracked files, source-v1
archive, failed attempts, old data/builds and reference results remain preserved.

## Exact source-v2 public commands

Run from the repository root; choose unused names for a later reproduction:

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/native_workflow_20261025_02 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/native_workflow_20261025_02 -j2

bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_smoke.json \
  --output-dir result/native_workflow_smoke_20261025_02 \
  --build build/native_workflow_20261025_02 --validation-mode diagnostic
bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_example.json \
  --output-dir result/native_workflow_example_20261025_02 \
  --build build/native_workflow_20261025_02 --validation-mode diagnostic

bash environment/run.sh python3 -B -m calibration.workflow prepare \
  --config calibration/config/native_workflow_multi.json \
  --output-dir result/native_workflow_multi_20261025_02 \
  --build build/native_workflow_20261025_02 --validation-mode diagnostic \
  --simulation-stage result/native_geant4_scope_a_20261025_01/simulation
bash environment/run.sh python3 -B -m calibration.workflow simulate \
  --run-dir result/native_workflow_multi_20261025_02
bash environment/run.sh python3 -B -m calibration.workflow digitize \
  --run-dir result/native_workflow_multi_20261025_02
bash environment/run.sh python3 -B -m calibration.workflow calibrate \
  --run-dir result/native_workflow_multi_20261025_02
bash environment/run.sh python3 -B -m calibration.workflow report \
  --run-dir result/native_workflow_multi_20261025_02
```

The two single-parameter `run` commands and all five independent multi-sensor
commands exited zero. Exact outer/inner argv, working directories and exits are
under the audit's `public_*_v2` wrappers and each run's `execution/`, simulation
producer and Controller jobs. Each public `run_manifest.json` indexes important
artifacts. ROOT outputs contain 39 keys for each single-Y example and 43 for the
multi-sensor example; use `visualization/browse.C` and TBrowser to inspect them.

Development failures remain documented in their original directories: initial
DD4hep component-registry loading, two serialization-fixture header/API compile
attempts and independent auditor assumptions about float accumulation and
NumPy-versus-ACTS zero rounding. The actual official CKF uses forward float32
chi2 accumulation; ActsToTracks sums persisted state contributions in double
before one float32 export. The independent audit reproduces both exactly.
These were validation/build defects, not a basis for changing scientific errors,
tracking states or historical assertions.


## Final launcher prerequisite check: source v3

Final review found a startup defect before committing: the fixed Docker launcher
records the bare image ID when executing in an existing container, but the full
`eicweb/eic_xl@sha256:...` reference when starting a fresh container. Both refer
to the same cached immutable image, verified with `docker image inspect`.
The public prerequisite previously accepted only the former spelling.

The final change accepts exactly those two pinned forms and refuses tags,
other repositories and other digests. Only `calibration/workflow.py` and its
seven-case unit method in `validation/test_native_workflow.py` differ from
source v2. No numerical module, C++ source, build output or earlier result was
modified. The final 279-file content archive is `execution_source_freeze_v3/`
under the audit root; its `sources.json` SHA256 is
`8b3e003500a2df6e7f63cb9b8fb8d9c14650932c034628890a74aefd31abfa26`.
The targeted Docker suite passed **79/79 tests with no skips** at
`prereq_v3_units/`. The earlier 231-test consolidated suite and exact 32-track
regression remain source-v2 evidence, rather than being relabeled as v3 tests.

A real fresh-container public `run` then regenerated all 64 Geant4 events and
completed the entire workflow at `result/native_workflow_smoke_20261025_03/`.
The host driver explicitly removed all three launcher overrides before invoking
`environment/run.sh`; the new container used the default pinned reference.
Its command was:

```bash
python3 -B result/native_workflow_20261025_01_audit/run_fresh_container_v3.py
```

This ignored evidence driver invokes the following public command with
`TESTBENCH_CONTAINER`, `TESTBENCH_IMAGE` and `TESTBENCH_PLATFORM` unset:

```bash
bash environment/run.sh python3 -B -m calibration.workflow run \
  --config calibration/config/native_workflow_smoke.json \
  --output-dir result/native_workflow_smoke_20261025_03 \
  --build build/native_workflow_20261025_02 --validation-mode diagnostic
```

The driver and public workflow both exited zero. The wrapper receipt is
`public_smoke_fresh_container_v3/`. Both fits accepted 63 tracks; initial
L1 Y was +78.865 um, ACTS chi2/stored-NDF was
5.643925909012083 -> 1.2900174523156787, and Pede chi2/NDF was
2.1557011378277173 -> 2.155701141848409. These exactly reproduce the source-v2
smoke values with the same seed. This is a startup/integration regression,
not another independent statistical sample. Engineering and integrity pass;
physics quality remains unvalidated and the candidate remains unapproved.
The README and practical guide now point to this final smoke execution.

The independent source-v3 audit also passed with process exit 0 at
`public_smoke_v3_independent/`: both fits, all 1,260 scalar Mille measurements,
finite positive rank-one information, nominal Pede errors, exact immutable
Raw channels, six actual XML reloads and 39 ROOT objects. All 285 run files
(7,184,614 bytes) and all 279 final sources remained exact.

A separate numerical read-back of the three source-v2 ROOT reports passed at
`root_numeric_v2/`: all 66 histograms with 55,638 entries (every bin, including
underflow/overflow), all 52 graphs with 215 points, parameter error bars,
cumulative corrections, Geometry centers and saved canvas graphs agree with
the actual reconstruction, solver and Geometry records. Its 45 consumed files
remain unchanged. This verifies plot contents, without adding a physics-quality
or uncertainty-coverage claim.
