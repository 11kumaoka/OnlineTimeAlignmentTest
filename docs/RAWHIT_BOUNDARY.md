> Historical +Z BeamTestReco contract and validation. The current native
> Geant4 workflow is documented in [the telescope guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md).
> The former `reconstruct_corrected.sh` alias is now `reconstruct.sh --after`;
> the archived scenario `my_first_test.json` is equivalent to the maintained
> `geometry/scenarios/L1_x150um_L2_x200um.json`. Quoted historical executions
> and their preserved artifacts below retain their original provenance.

# Common RawHit Boundary: Architecture, Contract, and Validation

Date: 2026-10-21. Starting commit: `2fff299a1958718694cad116cbf767894ed3b363`,
branch `seven-layer-alignment`. No commit or push was performed for this development.
The pre-existing untracked `bash` file and `geometry/scenarios/my_first_test.json`
were preserved unchanged. Existing results, dependency installations, and archives
were not edited. Source and data-hash inventories were saved before implementation
under `result/rawhit_boundary_20261021_01/`.

## Data flow and ownership

```text
Simulation: Geant4 -> SimHits -> Digitization ---+
                                               |
Future experiment: DAQ -> [adapter not built] ---+-> RawTrackerHits
                                                    |
                        same normal RecHit Reconstruction
                                                    |
                                same ACTS Track Fitting
                                                    |
                           same in-process Mille Writer
                                                    |
                             same external pede process
```

Offline execution may persist RawHits in a PODIO ROOT file. The C++ factories
remain reusable in memory: no algorithm reads intermediate files. The combined
profile still performs the entire in-process chain. This is not a DAQ decoder,
conditions service, or claim of compatibility with actual detector electronics.

| Object | Meaning |
|---|---|
| SimHit (`edm4hep::SimTrackerHit`) | Geant4 energy deposit, time, physical position and readout Cell ID, optionally linked to MCParticles. |
| RawHit (`edm4eic::RawTrackerHit`) | Encoded channel, integer charge and timestamp; no reconstructed spatial position. |
| RecHit (`edm4eic::TrackerHit`) | Cell position/dimensions decoded with reconstruction Geometry; position in mm, covariance in mm², time in ns and energy-equivalent signal in GeV. |
| ACTS / EDM Measurement2D | Existing calibrated fit coordinates/covariance with associations to reconstructed TrackerHits. |
| Track / TrackParameters / Trajectory | Existing ACTS fit results and reference parameters, stored chi2 and measurement dimensionality; unchanged model. |
| Mille Binary measurement | Existing writer's scalar Global X/Y hit values, sigmas, four straight-line Local derivatives and layer Global labels. These are not copied ACTS chi2 contributions. |

`localDetEICrecon/` owns C++ factories, algorithms and processors. `digitization/`
owns the upstream Simulation-to-RawHit command and file-contract checks.
`reconstruction/` owns one common RawHit-to-Track command. `alignment/` still runs
the external solver. Geometry, correction, validation and ROOT rendering retain
their independent task directories. There is no new monolithic workflow.

## Source findings and registration profiles

The original digitizer factory takes EventHeader and SimTrackerHits and produces
RawHits plus truth links/associations. Its algorithm seeds a local generator from
the EventHeader and unchanged factory name. Normal
`TrackerHitReconstructionNoAssoc_factory` takes only RawHits; it supplies an empty
internal association collection to the shared algorithm, with truth positions
forced off. It does not request a truth collection from the input file.
`BeamTestACTSFitter_factory` takes three TrackerHit collections, and the Mille
processor takes Tracks and SiMAPS RecHits. Their algorithms were not changed.

Only `plugins/BeamTestReco.cc` registration was changed, using
`beamtstreco:profile`:

| Profile | Registered local components | Truth dependencies |
|---|---|---|
| `combined` (Plugin default) | Existing digitizers, normal RecHits, fitter and processors | SimHits/EventHeader needed upstream; truth diagnostics remain optional. |
| `digitization` | Only the three existing digitizer factories | SimHits/EventHeader inputs; no local RecHit/fitter/Mille/event-monitor processor registered. |
| `raw` | Normal RecHits, the same fitter, the same Mille/event-monitor processors | No digitizer or truth diagnostic factory registered. |

Unknown profiles and truth-diagnostic requests outside `combined` are rejected.
Factory names, input/output names, numeric configs and algorithm implementations
remain unchanged. RawHit mode does not merely hope that JANA selects persisted
collections: there is **no local Digitization factory registered to fall back to**.

An initial Digitization-only test omitted the standard `acts` Plugin and failed
at library loading: `algorithms_init.so` has an undefined `ACTSGeo_service` type
symbol without it in the installed runtime. The failed attempt is retained.
The supported Digitization command therefore loads `acts` before `algorithms_init`.
This can initialize the standard ACTS Geometry service and show its existing
conversion diagnostic, but it does not register or execute the local ACTS fitter.
The `beam` Plugin was not needed for Digitization. Reconstruction preserves its
original standard Plugin dependencies. No upstream installation was modified.

## Independent commands and output layout

Run from the repository root after building the Plugin. Use new result names:

```bash
bash environment/run.sh bash environment/build.sh
bash environment/run.sh bash geometry/prepare_geometry.sh --result-dir result/raw_study_001 --geometry-config geometry/scenarios/L2_x200um.json
bash environment/run.sh bash simulation/simulate.sh --result-dir result/raw_study_001 --config simulation/configs/electron_1GeV.json
bash environment/run.sh bash digitization/digitize.sh --result-dir result/raw_study_001
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/raw_study_001 --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/raw_study_001 --steering alignment/pede_template.txt
```

Each command stops after its stage. Existing outputs are refused. For saved
Simulation add `--sim-input PATH` to `simulate.sh`. Use `--build-dir BUILD` on
Digitization and both reconstruction commands for a nondefault Plugin build.

```text
result/<name>/
  step1/                 existing Geometry preparation
  step2/                 existing Simulation
  step2_digitization/    NEW; no existing step renumbered
    rawhits.edm4eic.root
    rawhit_contract.json
    config.json
    command.json
    stdout.log
    exit.json
    complete.json
  step3/                 common RawHit-to-Track Reconstruction and Mille Binary
  step4/                 external pede
  step5/                 existing L2-only correction
  step6/                 corrected Reconstruction of the same saved RawHits
  step7/                 existing Simulation Closure metrics and ROOT plots
```

Digitization normally loads the measured step1 XML. `digitize.sh --geometry XML`
can select another initialization Geometry with an identical readout signature;
measured and loaded Geometry hashes are recorded separately. The current digitizer
uses SimHit Cell IDs and deposits directly, not the DD4hep position converter.
The strict comparison below additionally loads the same nominal XML in both
executions; it does not rely only on this source observation.

The production RawHit file stores exactly these event collections:

- `EventHeader`: `edm4hep::EventHeaderCollection`;
- `LocalSiMAPSRawHits`, `LocalMPGDRawHits`, `LocalACLGADRawHits`:
  `edm4eic::RawTrackerHitCollection`.

PODIO file/schema metadata and EventHeader's primitive weight-vector storage are
also present. EDM type definitions mentioning MC types are not MC event data.
There are no SimHits, MCParticles, truth links, or truth associations in the
production event payload. Optional truth-diagnostic associations remain available
in the in-memory combined profile; they are not part of the common input contract.

For an external RawHit file, neither step1 nor step2 nor step2_digitization is
required. Select the reconstruction Geometry explicitly:

```bash
bash environment/run.sh bash reconstruction/reconstruct.sh --result-dir result/imported_raw_001 --raw-input result/raw_study_001/step2_digitization/rawhits.edm4eic.root --geometry geometry/nominal/seven_layer_telescope.xml --config reconstruction/configs/electron_1GeV.json
bash environment/run.sh bash alignment/align.sh --result-dir result/imported_raw_001
```

`--raw-metadata PATH` selects a sidecar; otherwise it is the input sibling
`rawhit_contract.json`. `--events N` selects a positive prefix within the file;
default is all events. The same command applies to a future adapter's output if
it satisfies the contract. There is no experimental mode or invented DAQ format.
`--input-mode combined` retains the original Simulation diagnostic execution for
comparison; it requires step2 and does not constitute another tracking algorithm.

`reconstruct_corrected.sh` reuses the same implementation with `--after`, reading
step3's saved RawHit path and reconstruction config. Explicit `--geometry` can also
be used for an independent repeat with another Geometry. RecHit positions change
with that Geometry; saved channel IDs/charge/time do not. Completion records
include RawHit, config, Plugin and reconstruction Geometry hashes. The sidecar is
snapshotted in the reconstruction output. Optional Simulation producer metadata
is recorded if present but is not required.

## RawHit contract: local-telescope-rawhits-v1

The contract is intentionally specific to the supported detector/readout and
signal conventions, not a generic promise for arbitrary EDM4eic RawTrackerHits.
The validator checks schema/type, file checksum, reconstruction readout signature,
event IDs, expected system/layer IDs, nonnegative charges and units. A valid file
alone cannot prove correct experimental calibration.

### Collections, Cell IDs and units

All three named RawHit collections are mandatory, even when a detector is inactive.
Represent inactivity or no hits by an explicit empty collection in each event.
A missing collection or wrong type is an error; no digitizer fills it implicitly.
An empty-hit event is allowed. A whole file with no accepted tracks cannot satisfy
the current nonempty reconstruction/Mille success checks.

| Collection | System | Layer IDs | Readout |
|---|---:|---|---|
| LocalSiMAPSRawHits | 31 | 0–4 | SiMAPSHits, CartesianGridXZ |
| LocalMPGDRawHits | 100 | 5 | MPGDHits, CartesianGridXY |
| LocalACLGADRawHits | 92 | 6 | ACLGADHits, existing strip-like CartesianGridXY |

The exact encodings and pitches are in `geometry/nominal/seven_layer_telescope.xml`:

```text
SiMAPS: system:8,barrel:3,layer:6,wedge:5,module:6,sensor:4,x:32:-16,z:-16
MPGD/AC-LGAD: system:8,barrel:3,layer:6,wedge:5,module:6,sensor:4,x:32:-16,y:-16
```

Layer occupies bits 11–16; the system is bits 0–7; signed channel coordinates
occupy bits 32–47 and 48–63. The full detector hierarchy, barrel/wedge/module/sensor
conventions, segmentation axes and pitches must agree with DD4hep, not just layer
numbers. The current validator is not a complete channel/cabling validator.

- `charge`: nonnegative integer **keV-equivalent**, because the existing digitizer
  computes `round(edep_GeV * 1e6)` and RecHit Reconstruction divides by `1e6`.
  This is not elementary electric charge, raw ADC units, or arbitrary electronics
  counts. A future adapter must provide a justified calibration into this encoding
  or a separately validated conversion layer. No such conversion was invented.
- `timeStamp`: signed integer **ps**, from truncation of `(SimHit time + smearing)
  in ns times 1000. RecHits convert back to ns. Adapter time origins, offsets,
  wrapping, resolution and range must be documented and compatible; do not silently
  overflow or assume this is a DAQ wall-clock timestamp.
- Reconstruction errors/dimensions and time resolution remain the existing model.
  Hardware uncertainties, noise, thresholds, saturation, clustering and correlations
  have not been calibrated or validated for real data.

### Event identity and conditions

Exactly one EDM4hep EventHeader is required per event. `(runNumber,eventNumber)`
must be unique within a file; ordering and all Header fields are preserved through
Digitization. The Header timestamp is preserved in its producer-defined EDM4hep
convention, not converted into RawHit ps. A future timeframe-based adapter must
state how readout windows/triggers map to these events and document timestamp
units/epochs; no timeframe decoder exists here. Conditions should include this
mapping and any run-dependent time origins.

A mandatory JSON sidecar has these fields:

| Field | Requirement |
|---|---|
| `schema` | `local-telescope-rawhits-v1` |
| `raw_sha256` | Exact ROOT-file SHA-256 |
| `readout_signature_sha256` | Hash of serialized XML readouts plus detector/system mapping; must match reconstruction Geometry |
| `measured_geometry_sha256` | Identity of measured/Simulation Geometry; distinct from reconstruction Geometry |
| `charge_unit`, `timestamp_unit` | `keV_equivalent`, `ps` |
| `source_kind` | `simulation` or `daq`; declaring `daq` does not validate electronics or implement an adapter |
| `producer` | Nonempty object identifying producer/version; Plugin hash for the simulated producer; Simulation hash optional |
| `conditions` | Nonempty object identifying calibration, thresholds/time resolutions, timestamp/event conventions and conditions provenance |
| `inspection` | Optional producer report: counts, type inventory and event-identifier hash |

The simulated producer records factory defaults and source/Plugin identities.
Default SiMAPS time smearing is 8 ns; MPGD 10 ns; AC-LGAD 0.025 ns. Thresholds remain
0.54*dd4hep::keV, 100*dd4hep::eV, and zero, respectively. Source/config-definition
hashes identify those defaults; no new physics configuration was introduced.
A future producer must identify Geometry/readout and calibration versions and
retain the supporting conditions files. Hash checks authenticate declared bytes,
not the scientific correctness of those declarations. Readout signatures are
conservative and formatting-sensitive; use the same canonical compact definition.

RawHits are not independent of all Geometry: Geant4 used the measured segmentation
to form channel IDs, and hardware requires cabling/channel mapping and calibration.
Digitization consumes those IDs and does not reconstruct positions. Normal RecHit
Reconstruction calls the DD4hep converter's `position(cellID)` and
`cellDimensions(cellID)` using the selected reconstruction Geometry. This is why
the same saved RawHits can be reconstructed before/after a placement correction.
No nominal material, dimension, sign, seed or uncertainty was changed.

## Validation performed

All test outputs are under `result/rawhit_boundary_20261021_01/`. A clean build in
`build/rawhit_boundary_20261021_01` completed successfully. The first Digitization
attempt without `acts` failed at dynamic linking, was retained under
`combined/step2_digitization`, and was retried successfully in `digitized/`.
No partial stage was overwritten. No new Geant4 events were generated.

### Saved L1 +0.150 mm / L2 +0.200 mm study

The saved `result/my_geometry_001/step2/events.edm4hep.root` was reused. Test runs:

- `combined/`: original in-process execution, 100 events;
- `digitized/step2_digitization/`: independent RawHit production;
- `raw_only/`: separate-process RawHit Reconstruction with explicit nominal XML,
  containing no step1/step2 Simulation metadata or directories;
- `identical_geometry/`: a second split chain with nominal XML loaded during
  Digitization as well, exactly matching the combined initialization Geometry;
- `no_simulation_metadata/`: additional RawHit Reconstruction after omitting the
  optional Simulation producer hash from the sidecar; still correctly labeled as
  simulated input, not fake experimental data.

The maintained `validation/compare_raw_paths.py` checks all RawHit/Header values,
collection/branch types, downstream fields and relation branches. PODIO collection
IDs are resolved through file metadata to collection names before comparison;
relation target indices are also compared. No numerical tolerance was needed:

| Comparison | Result |
|---|---|
| EventHeader + RawHit Cell IDs, charge, timestamp | Exact; 15 field/storage branches per comparison |
| Downstream RecHit positions/covariance/time/energy, fit parameters, tracks, trajectories, measurements, segments and associations | Exact; 281 branches across 17 common collections |
| RawHit counts | SiMAPS 502, MPGD 114, AC-LGAD 103 across 100 events |
| Accepted tracks | 98 in both paths |
| ACTS chi2 sum | 36319.08984375 in both paths |
| Mille Binary | Byte-identical, including values, sigmas, Local/Global derivatives and labels; 98 records / 980 scalar measurements |
| Pede fitted values | Identical across all labels |

Pede chi2/NDF remains 1203.1236697375468 / (588−6) = 2.0672228002363346,
with zero reported local-fit rejections in the iteration table. Pede X biases remain L1 −0.15058 mm, L2 −0.20113 mm, L3 −0.0028278 mm. The warning
about input uncertainties and existing fit quality were not tuned away. The new
Mille Binary also matches the saved original study. No Geometry Correction or full
Closure was attempted for this multi-layer scenario.

The production RawHit payload is exactly the four required collections and has
no SimHits, MCParticles or truth links. Raw-profile logs contain no digitizer
execution marker, and the registration log confirms digitizers are absent. The
absence of MC data was tested by actual reconstruction, not inferred from counts.

To reproduce the detailed comparison after running and aligning both paths:

```bash
bash environment/run.sh python3 -m validation.compare_raw_paths --combined result/rawhit_boundary_20261021_01/combined --split result/rawhit_boundary_20261021_01/raw_only --raw result/rawhit_boundary_20261021_01/digitized/step2_digitization/rawhits.edm4eic.root --output result/raw_comparison_NEW.json
```

The existing comparison reports are retained; use a new output filename.

### Historical L2-only Closure

The historical 100-event input was processed through independent Digitization,
RawHit Reconstruction, unchanged pede/correction, and corrected Reconstruction
of the **same RawHits**, followed by ROOT validation:

- 99 accepted tracks before and after;
- applied L2 correction +198.75 μm;
- L2 pooled Rec−Sim −199.571375548 → −0.821364508 μm;
- stored ACTS chi2 ratio 45.592234848 → 1.981039768;
- reference comparison passed.

Truth-based Hit Residual validation now reads SimHits from the separate saved
Simulation file, checking run/event identity before matching. Common RawHit
Reconstruction does not request or export truth. Simulation Closure/Rec−Sim plots
remain a Simulation-only validation procedure; they are not claimed for DAQ data.

## Files and limitations

New: `digitization/{__init__.py,contract.py,digitize.py,digitize.sh}`,
`reconstruction/runtime.py`, `validation/compare_raw_paths.py`, and this document.
Changed: Plugin registration, `reconstruction/reconstruct.py`,
`validation/{metrics.py,validate.py,run_closure.sh}`, README, Workflow Guide and
relevant architecture/integration/validation documentation. All numerical C++
algorithms, factory interfaces, Mille Writer/processor and nominal Geometry remain
unchanged. `simulation/simulate.py` was inspected and needed no implementation
change. Configurations, including the user's untracked scenario, were preserved.

No detector-specific DAQ conversion, calibration loader, channel remapping,
timeframe handling, clustering or experimental noise model exists. The current
7-plane manual ACTS surfaces, five-SiMAPS Mille contract and uncertainty model
remain scientific limitations. Only L2 Global X Geometry Correction/full Closure
is implemented. Intermediate ROOT serialization is optional at the C++ factory
level; an online scheduler or DAQ adapter is a separate future integration task.

External RawHit inputs currently support common Reconstruction, Mille writing and
external pede. Automatic Geometry Correction still requires the prepared step1
scenario and remains L2-only; Simulation Rec−Sim validation still requires step2.
Neither is presented as a general experimental-data correction/validation tool.
The output collection selection now also persists the three existing TrackSegment
collections in both comparison profiles, so their association targets can be
inspected; this does not change their producer or numerical values.

## Exact maintained-file inventory

Created:

```text
digitization/__init__.py
digitization/contract.py
digitization/digitize.py
digitization/digitize.sh
digitization/README.md
reconstruction/runtime.py
validation/compare_raw_paths.py
docs/RAWHIT_BOUNDARY.md
```

Modified:

```text
README.md
docs/WORKFLOW.md
docs/EICRECON_MILLEPEDE_INTEGRATION.md
docs/TASK_ARCHITECTURE.md
docs/FINAL_ARCHITECTURE_AUDIT.md
localDetEICrecon/plugins/BeamTestReco.cc
reconstruction/reconstruct.py
validation/README.md
validation/metrics.py
validation/validate.py
validation/run_closure.sh
```

The two earlier architecture/publication reports were labeled historical rather
than rewriting their recorded measurements. No maintained file was deleted.
The official Mille inspector decoded the split sample as 98 records / 980 scalar
measurements. Final ROOT object checks, existing safety/preservation checks,
Python/Shell syntax, help commands and documentation-link checks passed. Six
negative contract checks rejected incorrect checksum, timestamp unit, charge unit,
readout signature, empty producer and empty conditions records.

Final preservation audit: all **4462** inventoried pre-existing result/dependency
files and user files remained byte-identical. All C++ algorithms and factory
interfaces except Plugin registration match the committed baseline. Nominal XML
and Pede steering are unchanged. The final historical L2 run at `l2_final/` has
byte-identical before/after Mille Binaries, corrected XML and complete summary JSON
relative to the preceding validated reference. The data-origin-independent
restart has byte-identical Mille output before and after re-execution with the
same explicit Geometry. No unresolved numerical discrepancy was observed.

The stricter `identical_geometry/` comparison also passed with the same 15 RawHit
and 281 downstream branches, exact Mille bytes and identical Pede values. This
loads nominal XML in both the combined process and the split Digitization process;
measured Geometry provenance remains the saved L1/L2 Simulation configuration.
The default measured-Geometry Digitization comparison passed as well. ROOT file
bytes need not match because file UUIDs/metadata and numeric PODIO collection IDs
can change; the comparator checks exact field types/values and named relation
targets instead, with no floating-point tolerance.

## Current v2 metadata: readout is not physical truth

New Digitization outputs use `local-telescope-rawhits-v2`. The existing ROOT collections, Cell IDs, numeric charge/time encoding and algorithms are unchanged. Required sidecar fields are `schema`, `raw_sha256`, `readout_signature_sha256`, `topology_signature_sha256`, `charge_unit`, `timestamp_unit`, `source_kind`, nonempty `producer`, and nonempty `conditions`.

`readout_signature_sha256` identifies segmentation, Cell ID fields and detector/readout mappings. `topology_signature_sha256` additionally identifies layer/module/sensor topology while excluding physical positions. The selected Reconstruction Geometry must match these fingerprints, and its own full checksum is separately recorded in every stage/queue attempt. The configured survey fallback identifies G0; it need not equal unknown physical placement.

`simulation_truth_geometry_sha256` is optional simulation provenance. `digitization_geometry_sha256` records the Geometry used by the producer when known. Neither is an input to Geometry Correction. The controller's legacy `calibration.measured_geometry` option, when non-null, explicitly verifies known simulation provenance; null is valid and expected for truth-free calibration.

All v1 fields documented above retain their original meaning. A legacy simulation `measured_geometry_sha256` is not silently relabeled as survey Geometry or used to infer corrections. Existing saved v1 simulation inputs remain accepted for the validated telescope topology; incompatible legacy topology requires an explicit metadata migration. New truth-excluded test metadata uses `source_kind: simulation_test_without_truth` and must be described as simulation-backed testing, not real DAQ. Real producers may use `daq` with their actual producer and conditions records, but no hardware decoder or electronics calibration is implemented here. This prototype still requires the documented energy-equivalent charge and ps timestamp encoding.

See [Geometry conventions](GEOMETRY_CONVENTIONS.md) and [executed XY validation](XY_FOUNDATION_VALIDATION.md).
