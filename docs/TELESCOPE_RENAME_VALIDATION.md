# Telescope naming refactor: validation record

## Scope and source preservation

The starting branch was `feature/upstream-acts-geometry`, clean at
`7a588e3bc79ea2d42edfe08c105c95454227f178`, preceded by
`288e80e934b0acb09ef8eb7001398baea565dcf6`.
This is a source naming/documentation refactor, not a change of detector physics.
No production branch, installed library, Geometry activation or historical output
was modified. No files were deleted for cleanup. All 50 moves used `git mv`.

The intended application is beam-test telescope alignment. The pinned DD4hep-to-ACTS
converter's paired-endcap requirement currently motivates a barrel-compatible
representation. It still uses actual DD4hep modules, Tube envelopes, SurfaceMap,
TrackingGeometry and native ACTS navigation, not the official endcap conversion.
This representation is distinct from standard ePIC barrel reconstruction.

## Before and after

```text
localDetEICrecon/experimental/barrel/  -> experimental/telescope/
validation/barrel_geometry/          -> validation/telescope_geometry/
validation/barrel_one_track/         -> validation/telescope_one_track/
validation/barrel_factories/         -> validation/telescope_factories/
validation/barrel_alignment/         -> validation/telescope_alignment/
validation/barrel_closure/           -> validation/telescope_closure/
docs/BARREL_ALIGNMENT_USER_GUIDE.md   -> docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md
docs/BARREL_ALIGNMENT_CODE_MAP.md     -> docs/TELESCOPE_ALIGNMENT_CODE_MAP.md
```

## Complete move inventory

| Original path | Current path |
|---|---|
| `docs/BARREL_ALIGNMENT_CODE_MAP.md` | `docs/TELESCOPE_ALIGNMENT_CODE_MAP.md` |
| `docs/BARREL_ALIGNMENT_USER_GUIDE.md` | `docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md` |
| `localDetEICrecon/experimental/barrel/CMakeLists.txt` | `localDetEICrecon/experimental/telescope/CMakeLists.txt` |
| `localDetEICrecon/experimental/barrel/FactoryAudit.h` | `localDetEICrecon/experimental/telescope/FactoryAudit.h` |
| `localDetEICrecon/experimental/barrel/LICENSE.LGPL3` | `localDetEICrecon/experimental/telescope/LICENSE.LGPL3` |
| `localDetEICrecon/experimental/barrel/NOTICE.md` | `localDetEICrecon/experimental/telescope/NOTICE.md` |
| `localDetEICrecon/experimental/barrel/README.md` | `localDetEICrecon/experimental/telescope/README.md` |
| `localDetEICrecon/experimental/barrel/TelescopeTracking.cc` | `localDetEICrecon/experimental/telescope/TelescopeTracking.cc` |
| `localDetEICrecon/experimental/barrel/algorithms/TelescopeSeed.h` | `localDetEICrecon/experimental/telescope/algorithms/TelescopeSeed.h` |
| `localDetEICrecon/experimental/barrel/algorithms/tracking/CKFTracking.cc` | `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTracking.cc` |
| `localDetEICrecon/experimental/barrel/algorithms/tracking/CKFTracking.h` | `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTracking.h` |
| `localDetEICrecon/experimental/barrel/algorithms/tracking/CKFTrackingConfig.h` | `localDetEICrecon/experimental/telescope/algorithms/tracking/CKFTrackingConfig.h` |
| `localDetEICrecon/experimental/barrel/algorithms/tracking/TrackerMeasurementFromHits.cc` | `localDetEICrecon/experimental/telescope/algorithms/tracking/TrackerMeasurementFromHits.cc` |
| `localDetEICrecon/experimental/barrel/algorithms/tracking/TrackerMeasurementFromHits.h` | `localDetEICrecon/experimental/telescope/algorithms/tracking/TrackerMeasurementFromHits.h` |
| `localDetEICrecon/experimental/barrel/alignment/NativeMilleModel.cc` | `localDetEICrecon/experimental/telescope/alignment/NativeMilleModel.cc` |
| `localDetEICrecon/experimental/barrel/alignment/NativeMilleModel.h` | `localDetEICrecon/experimental/telescope/alignment/NativeMilleModel.h` |
| `localDetEICrecon/experimental/barrel/alignment/TelescopeMille.cc` | `localDetEICrecon/experimental/telescope/alignment/TelescopeMille.cc` |
| `localDetEICrecon/experimental/barrel/extensions/edm4eic/EDM4eicToActs.h` | `localDetEICrecon/experimental/telescope/extensions/edm4eic/EDM4eicToActs.h` |
| `localDetEICrecon/experimental/barrel/factories/SyntheticTrackerHits_factory.h` | `localDetEICrecon/experimental/telescope/factories/SyntheticTrackerHits_factory.h` |
| `localDetEICrecon/experimental/barrel/factories/TelescopeSeed_factory.h` | `localDetEICrecon/experimental/telescope/factories/TelescopeSeed_factory.h` |
| `localDetEICrecon/experimental/barrel/factories/tracking/CKFTracking_factory.h` | `localDetEICrecon/experimental/telescope/factories/tracking/CKFTracking_factory.h` |
| `localDetEICrecon/experimental/barrel/factories/tracking/TrackerMeasurementFromHits_factory.h` | `localDetEICrecon/experimental/telescope/factories/tracking/TrackerMeasurementFromHits_factory.h` |
| `localDetEICrecon/experimental/barrel/provenance.json` | `localDetEICrecon/experimental/telescope/provenance.json` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/algorithms__tracking__CKFTracking.cc.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/algorithms__tracking__CKFTracking.cc.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/algorithms__tracking__CKFTracking.h.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/algorithms__tracking__CKFTracking.h.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/algorithms__tracking__CKFTrackingConfig.h.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/algorithms__tracking__CKFTrackingConfig.h.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/algorithms__tracking__TrackerMeasurementFromHits.cc.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/algorithms__tracking__TrackerMeasurementFromHits.cc.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/algorithms__tracking__TrackerMeasurementFromHits.h.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/algorithms__tracking__TrackerMeasurementFromHits.h.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/extensions__edm4eic__EDM4eicToActs.h.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/extensions__edm4eic__EDM4eicToActs.h.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/factories__tracking__CKFTracking_factory.h.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/factories__tracking__CKFTracking_factory.h.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/factories__tracking__TrackerMeasurementFromHits_factory.h.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/factories__tracking__TrackerMeasurementFromHits_factory.h.patch` |
| `localDetEICrecon/experimental/barrel/upstream_diffs/upstream_support__algorithms__meta__CollectionCollector.h.patch` | `localDetEICrecon/experimental/telescope/upstream_diffs/upstream_support__algorithms__meta__CollectionCollector.h.patch` |
| `localDetEICrecon/experimental/barrel/upstream_support/algorithms/meta/CollectionCollector.h` | `localDetEICrecon/experimental/telescope/upstream_support/algorithms/meta/CollectionCollector.h` |
| `validation/barrel_alignment/BarrelMilleDerivatives.cc` | `validation/telescope_alignment/TelescopeMilleDerivatives.cc` |
| `validation/barrel_alignment/BarrelMilleFixture.cc` | `validation/telescope_alignment/TelescopeMilleFixture.cc` |
| `validation/barrel_alignment/LegacyBarrelCrosscheck.cc` | `validation/telescope_alignment/LegacyTelescopeCrosscheck.cc` |
| `validation/barrel_alignment/check.py` | `validation/telescope_alignment/check.py` |
| `validation/barrel_alignment/l1_l2_global_y.json` | `validation/telescope_alignment/l1_l2_global_y.json` |
| `validation/barrel_closure/BarrelChannels.cc` | `validation/telescope_closure/TelescopeChannels.cc` |
| `validation/barrel_closure/closure.py` | `validation/telescope_closure/closure.py` |
| `validation/barrel_factories/check.py` | `validation/telescope_factories/check.py` |
| `validation/barrel_factories/prepare.py` | `validation/telescope_factories/prepare.py` |
| `validation/barrel_factories/upstream_diff.py` | `validation/telescope_factories/upstream_diff.py` |
| `validation/barrel_geometry/BarrelGeometryProbe.cc` | `validation/telescope_geometry/TelescopeGeometryProbe.cc` |
| `validation/barrel_geometry/BarrelMetadata.cc` | `validation/telescope_geometry/BarrelMetadata.cc` |
| `validation/barrel_geometry/CMakeLists.txt` | `validation/telescope_geometry/CMakeLists.txt` |
| `validation/barrel_geometry/check.py` | `validation/telescope_geometry/check.py` |
| `validation/barrel_geometry/prepare.py` | `validation/telescope_geometry/prepare.py` |
| `validation/barrel_one_track/BarrelOneTrack.cc` | `validation/telescope_one_track/TelescopeOneTrack.cc` |
| `validation/barrel_one_track/CMakeLists.txt` | `validation/telescope_one_track/CMakeLists.txt` |

## Additional edits and deliberately retained names

- Renamed six validation executable targets/files and their usage text to
  TelescopeChannels, TelescopeGeometryProbe, TelescopeOneTrack,
  TelescopeMilleDerivatives, TelescopeMilleFixture and LegacyTelescopeCrosscheck.
- Updated CMake dependencies, Python imports, runtime config paths, upstream
  diff labels and the regeneration tool. Original upstream hashes/licenses remain
  unchanged; all nine patches regenerate exactly with the new labels.
- Rewrote the two entry guides in English, removing repeated narrative while
  keeping stage contracts, commands, source functions, limitations and comparison
  with actual official EICrecon. Root and experimental README links are updated.
- Only the relocated guide link changed in each of the historical
  BARREL_ALIGNMENT_VALIDATION and BARREL_CHANNEL_ALIGNMENT_CLOSURE reports.
  Their execution commands, result paths and numerical records remain intact.
- Technical `BarrelMetadata.cc`, `initializeBarrelMetadata`,
  `TestbenchBarrelMetadata`, `DD4hep_SiTrackerBarrel`, `barrel_envelope`, actual
  official ePIC barrel constants and the existing `barrel_field` output key remain.
  They describe the actual conversion implementation or preserve its data contract.
- There is no new wrapper, provider, navigator, fitter, controller or abstraction.
  The original benchmark input producer and historical writer remain useful
  independent references; neither is redundant with the channel closure.

The numerical CKF, measurement, seed, audit, native Mille model and observer
sources are byte-identical after relocation. Geometry preparation changes only
its explanatory docstring; the metadata hook changes only its explanatory comment.
Validation executable changes are names/usage text, not numerical operations.
Production sources, canonical Geometry, historical alignment and SO(3)/Controller
code are unchanged. Preservation manifests require no path updates because their
protected source paths did not move.

Remaining old active-path references are in historical reports describing old
executions or in this explicit before/after move inventory; active sources, patches and entry guides use only current paths.
Historical build directories must not be reconfigured as the new source tree;
use a fresh build as documented below.

## Actual commands

From the repository root, in the existing fixed Docker environment:

```bash
export TESTBENCH_CONTAINER=sweet_mahavira
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/telescope_rename_20261024_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/telescope_rename_20261024_01 -j2
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_rename_20261024_01 --result result/telescope_rename_20261024_01 \
  --events 32 --chi2-cut 1000 --step all
bash environment/run.sh python3 validation/telescope_closure/closure.py \
  --build build/telescope_rename_20261024_01 --result result/telescope_rename_20261024_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name rename
python3 validation/telescope_factories/upstream_diff.py \
  --source /Users/tkumaoka/eic/EICrecon \
  --output result/telescope_rename_20261024_01_audit/upstream_diffs
python3 validation/verify_preservation.py
git diff --check
```

These names record this actual execution. Use fresh build/result names to repeat.
The [user guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md) provides independent stages,
JSON/ROOT inspection and official Mille decoder commands. The [code map](TELESCOPE_ALIGNMENT_CODE_MAP.md)
provides the exact file/function map and unchanged/modified/telescope/reference
component classification. Geometry/data generation and Pede/XML correction run
outside eicrecon; hit reconstruction, measurement conversion, seeding, CKF,
ActsToTracks and native Mille observers execute inside it.

## Closure results

Fresh outputs: `result/telescope_rename_20261024_01/`.
Audit logs and baseline comparison: `result/telescope_rename_20261024_01_audit/`.
All scientific fields in `validation/report.json` match the historical
`result/barrel_closure_20261024_03/final_closure/report.json` **exactly**.
Nominal, Truth and corrected XML and all three native Mille binaries are also
byte-identical to that baseline. Regenerated ROOT file metadata can differ;
canonical channel payload and within-run immutable file checks remain enforced.

| Quantity | Actual result |
|---|---:|
| Accepted nominal / corrected / control | 32 / 32 / 32 |
| Measurements / outliers / holes per track | 5 / 0 / 2 |
| Official Mille records per pass | 32 (320 scalar equations) |
| Injected L1 / L2 Global Y | +150 / +200 um |
| Recovered L1 / L2 Global Y | +149.14 / +203.18 um |
| Nominal ACTS chi2/stored-NDF | 37.16731567382813 |
| Corrected ACTS chi2/stored-NDF | 0.6908491410315036 |
| Control ACTS chi2/stored-NDF | 0.6412598587572574 |
| Pede nominal/postsolve end status | 1: warnings (bad measurements); process exit 0 |
| Pede control end status | 0: ended normally |
| Rejected local fits | 0 in every iteration |
| Solved rank | 2 |

The proposed Pede error rescaling was not applied. Same immutable channels,
corrected XML application, local/global coordinates, covariance and ROOT read-back
passed the existing closure gates. This is zero-field, no assigned ACTS material,
quantized synthetic-channel validation, not statistical uncertainty coverage or
material-aware physics performance. Graphical TBrowser interaction is not claimed;
batch ROOT object generation/read-back is tested.

## Completed consolidated regressions

All 18 established subprocess commands exited 0; the suite's
`rename_regressions/complete.json` records `passed: true`. The unit-test subprocess
ran all 46 tests successfully. Fresh `TelescopeGeometryProbe` integration checked
7 sensitive surfaces, explicit boundary transport and the complete 56-surface /
5-volume inventory (no assigned ACTS material). Fresh standalone CKF and the
current default one-event plugin agreed with chi2 difference 0 and maximum
smoothed-position difference 5.4787285819202225e-12 mm.

Native/legacy Mille equivalence, derivative finite differences, the separate
16-ray Pede fixture, safety refusal tests and preservation all passed. The latter
verified 221 baseline records and 2046 relocated files, including the protected
electron hypothesis source. Documented ROOT batch inspection found 42 objects;
the official decoder read 32 nominal Mille records. No GUI session was run.
Existing CMake policy warnings, non-interactive stty messages and SQLite
ResourceWarnings were retained; no scientific gate or warning was suppressed.

The stage command/exit logs are authoritative for the 18 independent commands;
`result/telescope_rename_20261024_01_audit/baseline_equivalence.json` records exact
baseline comparisons. All nine upstream patches reproduce. Python syntax,
current documentation links, active source path references and `git diff --check`
passed. Only source moves, names, path references and explanatory documents are
included in the local commit; ignored results, builds, external installations and
logs remain local. No push or merge was performed.
