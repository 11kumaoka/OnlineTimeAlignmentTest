# Seven-layer software reuse inspection (2026-10-15)

## Environment inspected

- Container image: eicweb/eic_xl:nightly
- EICrecon plugins present (relevant): acts.so, tracking.so, BVTX.so, MPGD.so, BTOF.so

## EPIC detector references inspected

- Silicon example:
  - /opt/software/linux-x86_64_v2/epic-26.05.0-*/share/epic/compact/tracking/vertex_barrel.xml
  - Observed: silicon sensitive module components, stable layer IDs, dedicated readout naming.

- MPGD example:
  - /opt/software/linux-x86_64_v2/epic-26.05.0-*/share/epic/compact/tracking/mpgd_barrel.xml
  - Observed: MPGD-specific detector type usage in EPIC and distinct readout/collection conventions.

- AC-LGAD TOF example:
  - /opt/software/linux-x86_64_v2/epic-26.05.0-*/share/epic/compact/tracking/tof_barrel.xml
  - Observed: TOF-specific geometry constants and distinct readout naming (BTOF plugin path).

## EICrecon wiring references inspected

- From EICrecon config dump in-container:
  - Tracking chain keys include CKF trajectory and track factories, ambiguity solver, and seed/measurement paths.
  - Central collections include:
    - CentralTrackingRecHits
    - CentralTrackSeeds
    - CentralTrackerMeasurements
    - CentralCKFTracks / CentralCKFTruthSeededTracks
  - MPGD collections include:
    - MPGDBarrelRecHits, OuterMPGDBarrelRecHits, associated raw links/associations
  - TOF collections include:
    - TOFBarrelRecHits, TOFEndcapRecHits, associated raw links/associations

## Reuse direction for next milestone

- Keep ACTS + CKF reconstruction in existing EICrecon chain.
- Map seven-layer outputs to EICrecon-compatible hit collection naming where feasible.
- Prefer using existing TrackerMeasurementFromHits and CKFTracking factories through plugin configuration before writing new tracking code.
- If required, add a local JANA plugin under seven_layer to adapt collection naming without modifying main EICrecon source tree.
