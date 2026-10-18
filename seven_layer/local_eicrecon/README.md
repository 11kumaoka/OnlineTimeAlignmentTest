# local_eicrecon

This directory contains a locally editable, independently buildable EICrecon-like reconstruction package for the seven-layer beam-test workflow.

## Scope (current)

Milestone L1/L2 implementation:

- Local SiMAPS, MPGD, and AC-LGAD chains compiled locally from copied/adapted EICrecon-style source.
- Plugin: `BeamTestReco.so`
- Chain:
  - `SiMAPSHits` -> local `SiliconTrackerDigi` -> `LocalSiMAPSRawHits`
  - `LocalSiMAPSRawHits` -> local `TrackerHitReconstruction` -> `LocalSiMAPSRecHits`
  - `MPGDHits` -> local `SiliconTrackerDigi` -> `LocalMPGDRawHits`
  - `LocalMPGDRawHits` -> local `TrackerHitReconstruction` -> `LocalMPGDRecHits`
  - `ACLGADHits` -> local `SiliconTrackerDigi` -> `LocalACLGADRawHits`
  - `LocalACLGADRawHits` -> local `TrackerHitReconstruction` -> `LocalACLGADRecHits`
  - local `BeamTestEventProcessor` for event-level monitoring summaries

## Build

Run inside Docker image `eicweb/eic_xl:nightly`:

```bash
cmake -S seven_layer/local_eicrecon -B seven_layer/local_eicrecon/build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build seven_layer/local_eicrecon/build -j
```

## Runtime

Use `eicrecon` as JANA host and load local plugin by `JANA_PLUGIN_PATH`.

Example:

```bash
export JANA_PLUGIN_PATH=/work/seven_layer/local_eicrecon/build

eicrecon \
  -Pplugins=log,dd4hep,evaluator,algorithms_init,podio,janatop,BeamTestReco \
  -Pplugins_to_ignore=BVTX,MPGD,BTOF \
  -Pdd4hep:xml_files=seven_layer/geometry/seven_layer_telescope.xml \
  -Pjana:nevents=80 \
  -Ppodio:output_file=seven_layer/results/local_simaps_reco.root \
  -Ppodio:output_collections=EventHeader,SiMAPSHits,MPGDHits,ACLGADHits,LocalSiMAPSRawHits,LocalSiMAPSRawHitLinks,LocalSiMAPSRawHitAssociations,LocalSiMAPSRecHits,LocalMPGDRawHits,LocalMPGDRawHitLinks,LocalMPGDRawHitAssociations,LocalMPGDRecHits,LocalACLGADRawHits,LocalACLGADRawHitLinks,LocalACLGADRawHitAssociations,LocalACLGADRecHits \
  seven_layer/results/phase2_sim_quick.edm4hep.root
```

## Notes

- Original reference source tree remains read-only at `/Users/tkumaoka/eic/EICrecon`.
- Copied file provenance and local modifications are documented in:
  - `seven_layer/reports/local_eicrecon_implementation_report.md`
