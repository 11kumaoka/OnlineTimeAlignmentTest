> Historical audit: retained results and commands describe their recorded source/build state. The Blueprint reconstruction implementation was later removed; current status and commands are in [LEGACY_ENDCAP_SIMPLIFICATION.md](LEGACY_ENDCAP_SIMPLIFICATION.md). Use preserved builds or the recorded commit when reproducing historical Blueprint commands.

# Converted ACTS telescope Geometry integration

## Scope and implementation

The experimental `blueprint` provider is a **project-specific provider using
installed official ACTS/DD4hep components**. It is not the installed EICrecon
`ActsGeometryProvider`, which still invokes the legacy converter and rejects
this asymmetric telescope. The default `local` provider remains available and
selected unless explicitly requested otherwise. The Phase 1 investigation is
preserved in [OFFICIAL_ACTS_GEOMETRY_PHASE1.md](OFFICIAL_ACTS_GEOMETRY_PHASE1.md).

The installed environment is unchanged: EICrecon
`195966d41899800eaeca6fbafd63cd53735e6543`, ACTS 45.3.0 upstream commit
`d1323a298569942d98ff46ee413031ebd604290d` plus the three recorded packaging
patches, DD4hep 1.36, ROOT 6.38.00, PODIO 1.7 and EDM4hep 1.0. See the Phase 1
report and `result/upstream_acts_geometry_20261023_01/environment.json` for exact
prefixes, EDM4eic revision, library hashes and applied patch contents. No
external installation was upgraded or edited. Use the existing Docker launcher;
eic-shell is outside this milestone.

Installed `Acts/Geometry/LayerBlueprintNode.hpp` explicitly marks automatic
`LayerType::Plane` construction unimplemented. Instead, the supported
`StaticBlueprintNode` wraps an ordinary `TrackingVolume` with cuboid bounds.
The bounds are derived from the **converted physical sensor corners**, with a
10 mm navigation envelope. `Blueprint::construct` creates the enclosing World,
connects portals, registers surfaces and assigns closed GeometryIdentifiers.
`TryAllNavigationPolicy` provides the candidate policy; the installed
`Acts::Navigator` traverses this Gen3 TrackingGeometry. This small all-surface
policy is appropriate for seven sensors; it is not a large-detector accelerator.
No fake endcaps, detector flags, XML hierarchy repairs or dummy sensors are used.

The official DD4hep conversion component is
`ActsPlugins::DD4hepDetectorElement` with `TGeoAxes::parse("zXy")` and the DD4hep
cm-to-ACTS-mm length scale. Sensor placements come only from the selected
DDRec sensitive contexts. The seven explicit CellID slots retain their original
order. Channel bits resolve to their sensitive Volume ID; each Volume ID maps
to the corresponding converted Surface. TrackingGeometry closure assigns actual
unique nonzero IDs; numerical equality with the manual IDs is not required.
The local axes remain u = minus sensor Z, v = sensor X. The existing SiMAPS
covariance permutation and all measurement uncertainties remain unchanged.

The provider owns detector elements, converted surfaces and TrackingGeometry.
The fitter retains a shared owner through its entire lifetime. GeometryContext
is static for one immutable XML/process; dynamic conditions payloads have not
been integrated. The DD4hep service outlives reconstruction. Sensitive solid
thicknesses remain 0.05 mm for SiMAPS, 3 mm for MPGD and 0.35 mm for AC-LGAD;
these are physical shape dimensions, **not an ACTS material model**. No surface
or volume material map is assigned. Zero field and existing material/process-
noise assumptions are preserved.

The numerical fitter functions remain byte-identical. Only `init()` surface
injection and factory/configuration plumbing changed. Reconstruction still uses
**DirectNavigator** with the existing ordered measurement surfaces. The separate
complete-Geometry test uses `Acts::Navigator`; reconstruction does not validate
the full official EICrecon tracking/navigation chain. MPGD/AC-LGAD Geometry is
checked, but their tracking/alignment is not enabled by this study.

Installed source/API references used for this route:

- `Acts/Geometry/Blueprint.hpp`, `StaticBlueprintNode.hpp`, `TrackingVolume.hpp`,
  `NavigationPolicyFactory.hpp`, and `Acts/Propagator/Navigator.hpp` from the
  pinned installation define construction, closure and Gen3 navigation.
- [ACTS at the installed base commit](https://github.com/acts-project/acts/tree/d1323a298569942d98ff46ee413031ebd604290d)
  supplies the base implementation; the exact applied
  [PR5193 patch](https://github.com/acts-project/acts/pull/5193.patch?full_index=1)
  supplies the DD4hep blueprint backend and matching OpenDataDetector examples.
  The preserved patch was inspected for `addStaticVolume` and
  `root.construct(BlueprintOptions{}, gctx, logger())` usage. It is a multi-commit
  patch, not a claim that every intermediate example is the final installed API.
  The actual installed headers and successfully executed tests select the API
  used here. No newer upstream-main interface was substituted.

## Comparison criteria

Criteria were saved before reconstruction in
`result/complete_acts_geometry_20261023_01/criteria.json`:

- Surface center and round trip: absolute 1e-10 mm; rotation elements: 1e-12;
  bounds: 1e-12 mm. Exactly seven sensitive surfaces and unique closed IDs.
- Navigation: exact bounded-intersection sensor sequence, no repeated sensitive
  traversal, telescope entry/exit and World exit, maximum 32 targets per ray.
- Default local replay: exact PODIO branch values/relations and Mille bytes.
- Experimental comparison: exact event/track counts, integers and named relation
  targets; surface IDs mapped by sensor. Floating values use absolute 1e-6 in
  stored units plus relative 1e-5. Positions/local coordinates are mm, position
  covariance mm², angles rad, q/p GeV^-1, time ns, chi2 dimensionless. Report
  absolute differences separately; this integration tolerance is not a physics
  precision claim.
- Mille: exact labels and record structure, the same floating tolerances in
  native residual/derivative units, with byte equality reported separately.
- Correction comparison: same labels and canonical steering/status; differences
  at most 1e-6 mm for translations and 1e-8 rad for rotations.

No errors, steering, rejection thresholds, alignment scopes or convergence
criteria were changed. Corrections use reconstructed RawHits and current Survey
Geometry, never Simulation Truth. Truth is used only by the independent
noiseless diagnostic fixtures and historical residual/closure validation.

## Independent commands

Run from the repository root. Every output directory must be new. The exact
executed commands and retained logs are under
`result/complete_acts_geometry_20261023_01/`. Examples below name those executed
outputs; choose unused names when repeating them. Existing outputs are refused.
All commands use the existing `sweet_mahavira` Docker container.

### Environment and build

CHECK-ONLY: inspect installed versions, explicit options and library resolution.
No Truth is used. Inputs are installed headers and the completed build.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -c \
  'cat /opt/local/include/Acts/ActsVersion.hpp; grep TESTBENCH_ /work/build/complete_acts_geometry_20261023_01/CMakeCache.txt; ldd /work/build/complete_acts_geometry_20261023_01/BeamTestReco.so'
```

WRITES OUTPUT: configure/build only project components. Inputs are maintained
sources and pinned external installations; no Truth. Expect the Geometry probe,
local detector factory and BeamTestReco targets to build successfully.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh cmake \
  -S /work/localDetEICrecon -B /work/build/complete_acts_geometry_20261023_01 \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DMILLEPEDE_PREFIX=/work/external/install \
  -DMille_DIR=/work/external/install/cmake \
  -DTESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE=ON \
  -DTESTBENCH_ENABLE_BLUEPRINT_PROVIDER=ON
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh cmake \
  --build /work/build/complete_acts_geometry_20261023_01 -j 2
```

Both options default OFF. An OFF build rejects a requested `blueprint` provider;
unknown providers also fail. There is no automatic fallback.

### Seven-surface and complete-navigation gate

WRITES OUTPUT: selected immutable physical XML, provider `blueprint`; no Truth
used for inference. Four saved input fixtures were created in Phase 1 using
`geometry.prepare.write_shifted_xml`; their placements and hashes are recorded
there. They are local diagnostic inputs, not required Git datasets. Expect
`passed: true`, `tracking_geometry_available: true`, seven sensitive surfaces,
and four successful Navigator rays in each geometry.json. Surface equivalence
and navigation are reported separately in the same diagnostic invocation.

```sh
for CASE in nominal translations rotations six_dof; do
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m validation.official_geometry \
    --geometry "result/upstream_acts_geometry_20261023_01/geometries/$CASE.xml" \
    --build-dir build/complete_acts_geometry_20261023_01 \
    --geometry-build-dir build/l3_six_dof_20261023_01 \
    --provider blueprint \
    --output-dir "result/complete_acts_geometry_20261023_01/${CASE}_final"
done
```

`local` selects the original individual-plane diagnostic; `official-elements`
selects individual converted elements with unclosed IDs; neither mode claims
complete Geometry/navigation validation. `official` invokes the installed
legacy EICrecon provider and still fails explicitly for this telescope.
`--metadata none` is the default; no metadata repair is needed for `blueprint`.

### Existing RawHits, independent reconstruction and comparison

Local reference inputs (not committed):

- RawHits: `result/l3_six_dof_20261023_01/three_plane_smoke/step2_digitization/rawhits.edm4eic.root`,
  SHA-256 `1b54c7b5d91cc59fce1fb6dd1e5b9338c1d930db41369f7728f165d78942582e`.
- Contract: `result/l3_six_dof_20261023_01/three_plane_smoke/step3/rawhit_contract.json`.
- Survey: `result/l3_six_dof_20261023_01/survey/step1/misaligned.xml`.
- Historical reconstruction: `result/l3_six_dof_20261023_01/three_plane_smoke/step3/`.

The contract contains Simulation provenance hashes, but no Truth positions or
misalignments enter inference. Reconstruction uses only the same RawHit bytes,
Survey XML, electron configuration and existing `l1_l2_l3_six_dof` scope.
WRITES OUTPUT for each provider: expect step3 complete.json with 100 events,
95 tracks/records and 950 scalar measurements. Geometry preparation copies the
canonical nominal unchanged; its misaligned XML is not used as fit Geometry.

```sh
for PROVIDER in local blueprint; do
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
    env TESTBENCH_BUILD_DIR=/work/build/complete_acts_geometry_20261023_01 \
    python3 -m geometry.prepare \
    --result-dir "result/complete_acts_geometry_20261023_01/$PROVIDER" \
    --geometry-config geometry/scenarios/l1_l2_l3_six_dof.json
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m reconstruction.reconstruct \
    --result-dir "result/complete_acts_geometry_20261023_01/$PROVIDER" \
    --raw-input result/l3_six_dof_20261023_01/three_plane_smoke/step2_digitization/rawhits.edm4eic.root \
    --raw-metadata result/l3_six_dof_20261023_01/three_plane_smoke/step3/rawhit_contract.json \
    --geometry result/l3_six_dof_20261023_01/survey/step1/misaligned.xml \
    --build-dir build/complete_acts_geometry_20261023_01 \
    --geometry-provider "$PROVIDER" --alignment-mode l1_l2_l3_six_dof
done
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.compare_geometry_providers \
  --local result/complete_acts_geometry_20261023_01/local/step3 \
  --blueprint result/complete_acts_geometry_20261023_01/blueprint/step3 \
  --geometry-report result/complete_acts_geometry_20261023_01/nominal_final/geometry.json \
  --output result/complete_acts_geometry_20261023_01/reconstruction_comparison.json
```

The comparison WRITES only a new JSON report; it reads all measurement,
track/state and relation branches plus every official Mille record. The four
Geometry cases verify stable sensor semantics across different poses; the
mapping report supplies generated IDs, not forced manual IDs.

### Fresh derivative evidence and Pede/correction/refit

WRITES OUTPUT: before alignment, generate new build-matched derivative evidence.
These small fixed-channel physical finite differences use DD4hep transforms and
an independent mathematical trajectory fixture, not Geant4 Truth for a data
correction. Expect 54 physical comparisons and 108 actual binary components per
layer. The existing noiseless mathematical controls use known targets only for
fixture generation and validation. Their previously declared capture-range
settings are unchanged; this is not a new Simulation campaign.

```sh
for LAYER in 1 2 3; do
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m validation.validate_tilt_derivatives --coupled --representative \
    --layer "$LAYER" --build-dir build/complete_acts_geometry_20261023_01 \
    --output "result/complete_acts_geometry_20261023_01/derivatives_L$LAYER"
done
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.so3_closure \
  --writer-fixture result/complete_acts_geometry_20261023_01/derivatives_L1/writer_fixture \
  --output result/complete_acts_geometry_20261023_01/noiseless \
  --translation-scale 0.25 --three-layer-survey-fraction 0.5
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.merge_so3_evidence --build-dir build/complete_acts_geometry_20261023_01 \
  --derivative-report result/complete_acts_geometry_20261023_01/derivatives_L1/report.json \
  --derivative-report result/complete_acts_geometry_20261023_01/derivatives_L2/report.json \
  --derivative-report result/complete_acts_geometry_20261023_01/derivatives_L3/report.json \
  --noiseless result/complete_acts_geometry_20261023_01/noiseless \
  --output result/complete_acts_geometry_20261023_01/gate.json
```

The gate fingerprints the actual plugin, Geometry factory, physical reports and
implementation sources, including the new provider/factory/fitter plumbing.
The physical derivative fixture checks the unchanged writer model; the separate
RawHit experiment checks its invariance under provider selection. These are
complementary checks, not a statistical uncertainty-coverage certification.
Independent stage commands do not enforce all Controller gates automatically;
inspect the fresh gate and information report before applying a candidate.

WRITES OUTPUT: official Pede, the unchanged rank/resolution diagnostic, an
inactive candidate and reconstruction with that candidate. No Simulation Truth
is used. Inputs are step3 Mille, the canonical 18-parameter steering and the
same initial Survey. The 0.01 rad / 0.5 mm information bounds are the existing
provisional demonstration values, not newly tuned acceptance criteria.
Expect process exit 0, Pede end status 1 (retained warning), rank 18/18 and
step5/step6 complete markers. Provider is explicitly selected at each refit.

```sh
for PROVIDER in local blueprint; do
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m alignment.align \
    --result-dir "result/complete_acts_geometry_20261023_01/$PROVIDER" \
    --steering alignment/pede_l1_l2_l3_six_dof.txt
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m validation.tilt_observability \
    --mille "result/complete_acts_geometry_20261023_01/$PROVIDER/step3/mille.dat" \
    --mode l1_l2_l3_six_dof --max-sigma-rad .01 --max-sigma-mm .5 \
    --output "result/complete_acts_geometry_20261023_01/${PROVIDER}_information.json"
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m correction.correct_geometry \
    --result-dir "result/complete_acts_geometry_20261023_01/$PROVIDER" \
    --mode l1_l2_l3_six_dof \
    --base-geometry result/l3_six_dof_20261023_01/survey/step1/misaligned.xml \
    --reference-geometry result/l3_six_dof_20261023_01/survey/step1/misaligned.xml
  TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
    -m reconstruction.reconstruct \
    --result-dir "result/complete_acts_geometry_20261023_01/$PROVIDER" \
    --after --build-dir build/complete_acts_geometry_20261023_01 \
    --alignment-mode l1_l2_l3_six_dof --geometry-provider "$PROVIDER"
done
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 \
  -m validation.compare_geometry_providers \
  --local result/complete_acts_geometry_20261023_01/local/step6 \
  --blueprint result/complete_acts_geometry_20261023_01/blueprint/step6 \
  --geometry-report result/complete_acts_geometry_20261023_01/nominal_final/geometry.json \
  --output result/complete_acts_geometry_20261023_01/corrected_comparison.json
```

The first reconstruction defaults to local if selection is omitted. Corrected
reconstruction inherits the recorded provider when selection is omitted;
explicit selection is recommended for independent manual studies. Snapshot
metadata records the provider. There is no new Controller provider switch:
experimental reconstruction/alignment remains an explicit manual workflow.

CHECK-ONLY: the existing Controller configuration loader was exercised against
`result/complete_acts_geometry_20261023_01/controller_local_config.json`, which
copies the earlier policy and changes only build/evidence references. It
accepted the fresh compatible gate. No Controller run, state-directory change,
convergence claim or activation was performed in this milestone.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh python3 -c \
  'from pathlib import Path; from calibration.settings import load; load(Path("result/complete_acts_geometry_20261023_01/controller_local_config.json")); print("PASS fresh local Controller configuration; no execution or activation")'
```

### ROOT validation and historical regression

WRITES OUTPUT: reuse the existing ROOT visualization. The copied information
report belongs to this exact run; copying does not change any stage record.
Simulation Truth is read **only for these post-fit residual/Geometry plots**.
Expect `tilt_alignment.root`, PDFs and `summary.json`. The ROOT file can be
opened with TBrowser in a ROOT session.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash -c \
  'set -eu; cp /work/result/complete_acts_geometry_20261023_01/blueprint_information.json /work/result/complete_acts_geometry_20261023_01/blueprint/tilt_observability.json; python3 -m visualization.tilt_alignment --case result/l3_six_dof_20261023_01/three_plane_smoke --manual-run result/complete_acts_geometry_20261023_01/blueprint --survey result/l3_six_dof_20261023_01/survey/step1/misaligned.xml --output result/complete_acts_geometry_20261023_01/blueprint_root'
```

WRITES OUTPUT: default-local historical closure, using the saved Simulation
input (documented in validation/README.md). The Simulation stage copies the
saved input; no new Geant4 events are generated. Truth is used only for the
historical validation residuals. Expect the unchanged 99-track reference and
step7 ROOT outputs.

```sh
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh \
  env TESTBENCH_BUILD_DIR=/work/build/complete_acts_geometry_20261023_01 \
  bash validation/run_closure.sh \
  --result-dir result/complete_acts_geometry_20261023_01/l2_regression \
  --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root \
  --build-dir build/complete_acts_geometry_20261023_01 \
  --reference validation/reference_metrics.json
```

## Executed results

Evidence root: `result/complete_acts_geometry_20261023_01/`.

| Criterion | Result | Evidence |
|---|---|---|
| Optional and production-default builds | Both passed in fresh directories | build_final.log, build_default.log |
| Seven-surface equivalence | 28/28; maximum center difference 0 mm, rotation-element difference 1.158e-14, round trip 3.973e-15 mm | geometry_gate_final.json; four `*_final/geometry.json` files |
| Complete TrackingGeometry | Seven unique, closed, mapped sensitive surfaces per case | same reports; visitSurfaces/findSurface checks |
| Installed Navigator | 16/16 rays; forward/reverse, partial/all sensor misses, portals and world exit | per-case navigation arrays |
| Default local replay, both optional-ON and OFF builds | All 281 PODIO branches and Mille bytes exact | local_replay.json, default_build_checks.json |
| Explicit unavailable-provider failure | Passed; failure artifacts retained, no complete marker or fallback | disabled_provider_refusal/ |
| Converted initial reconstruction | 95 tracks, 950 scalars; all 281 branches equivalent; maximum floating difference 2.911e-11 stored units; Mille bytes exact | reconstruction_comparison.json |
| Pede and correction | Parameters exactly equal; corrected XML byte-identical; rank 18/18, normalized condition 13.7103 | alignment_pair.json, `*_information.json` |
| Fixed-RawHit refit | Same RawHit SHA; 95 tracks; all 281 branches equivalent, same maximum difference; Mille bytes exact | corrected_comparison.json |
| Fresh derivatives | 39 physical contexts, 162 vector comparisons, 324 actual binary components, all 18 parameter labels | derivatives_L1/L2/L3/report.json; gate.json |
| Noiseless SO(3) controls | All 11 cases passed with existing capture-range settings | noiseless/report.json |
| Existing unit regressions | 46 passed; pre-existing SQLite ResourceWarnings retained in log | unit.log |
| Syntax | 65 Python AST parses, 14 bash syntax checks passed | syntax.json |
| Safety and preservation | Maintained refusal tests passed; baseline data/electron checks passed; 45,469 protected artifacts unchanged | safety.log, preservation_check.log, protected_check.json |

Initial and corrected provider fits agree:

| Quantity | Before | After one correction |
|---|---:|---:|
| Accepted tracks, either provider | 95 | 95 |
| ACTS chi2 sum | 24017.369140625 | 1201.073974609375 |
| Stored ACTS NDF sum | 950 | 950 |
| ACTS chi2 / stored NDF | 25.2814412007 | 1.26428839433 |

The initial Pede solve is identical for both providers: chi2/NDF =
1167.485061314763 / 552 = 2.11500916905, process exit 0, end status
`1 Ended with warnings (bad measurements)`. Its reported local-fit rejection
count is zero at each recorded iteration. Warning lines and complete logs are
retained; the warning was not suppressed or reclassified as statistical success.

The historical L2-only regression remains 99 tracks, +198.75 µm correction,
pooled L2 Rec−Sim −199.571375548 → −0.821364508 µm, ACTS chi2/stored-NDF
45.5922348485 → 1.98103976780. Initial and corrected Mille bytes exactly match
the Phase 1 reference, as do all 281 PODIO branches at each stage. Historical
reference values were not edited. The source-preservation pin was advanced only
for the init surface-construction substitution; its old hash and
numerical-function integrity proof are retained in validated_sources_history.

## Files, preservation and remaining limits

New maintained files for this continuation:

- `localDetEICrecon/geometry/ConvertedTelescopeGeometry.h`: shared complete-
  Geometry construction, actual detector-element ownership and association checks.
- `validation/compare_geometry_providers.py`: semantic PODIO/Mille comparison.
- This document.

Extended files: the existing Phase 1 C++ probe and Python diagnostic, CMake,
fitter header/init/configuration and factory, reconstruction CLI/stage metadata,
source-pinned evidence merger, validated-source pin/history, README and
validation guide. Phase 1 files and all original uncommitted changes were
preserved. No numerical writer/fitter function, Geometry, hypothesis,
uncertainty, steering, material model or external source was changed.

The task-start archive contains all 229 maintained files and the original diff.
Protected artifacts include all 44,888 original files plus Phase 1 outputs and
builds. New results, expected refusal artifacts and fresh builds remain local
and ignored by Git. The development branch/checkpoint and index remain intact;
no commit, push, merge or Geometry activation was performed.

This is a successful Geometry/navigation and narrow reconstruction/alignment
**compatibility** milestone. It does not certify physical performance or nominal
uncertainty coverage. The earlier L1/L2 uncertainty limitations, technically
checked L1/L2/L3 prototype status, three-iteration nonconverged Controller pilot
and large-initial-offset Pede rejection remain unchanged. Small chi2 alone does
not establish accurate Rx/Ry inference: the reused finite sample retains its
previous tilt-estimate limitations. No statistical campaign, additional degree
of freedom or material/process-noise tuning was undertaken.

The next concrete integration step is a separately scoped comparison of
TrackingGeometry-backed navigation inside reconstruction against the retained
DirectNavigator path, with the same fixed-RawHit/state/Mille gates. Direct reuse
of the installed official EICrecon provider still requires an upstream converter
route compatible with asymmetric telescopes; this custom Gen3 provider does
not make that legacy API compatible. Material modeling and statistical
uncertainty validation remain separate future studies.

Exact maintained-file changes relative to the Phase 1 task-start snapshot:

```text
MODIFIED README.md
MODIFIED localDetEICrecon/CMakeLists.txt
MODIFIED localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc
MODIFIED localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.h
MODIFIED localDetEICrecon/algorithms/tracking/BeamTestACTSFitterConfig.h
MODIFIED localDetEICrecon/factories/tracking/BeamTestACTSFitter_factory.h
MODIFIED localDetEICrecon/geometry/OfficialGeometryProbe.cc
MODIFIED reconstruction/reconstruct.py
MODIFIED validation/README.md
MODIFIED validation/merge_so3_evidence.py
MODIFIED validation/official_geometry.py
MODIFIED validation/validated_sources.json
MODIFIED validation/validated_sources_history.json
ADDED    docs/ACTS_GEOMETRY_INTEGRATION.md
ADDED    localDetEICrecon/geometry/ConvertedTelescopeGeometry.h
ADDED    validation/compare_geometry_providers.py
```

No maintained files were deleted. The pre-existing Phase 1 report is unchanged.
