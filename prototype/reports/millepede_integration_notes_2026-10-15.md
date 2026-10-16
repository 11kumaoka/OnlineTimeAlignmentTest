# Millepede-II integration notes (parallel task)

## What is available in this container now

- ACTS installation is present (v45.3.0 headers/libraries), including alignment-related APIs:
  - `Acts/Definitions/Alignment.hpp`
  - `Acts/Geometry/detail/AlignablePortalVisitor.hpp`
  - `Acts/Surfaces/detail/AlignmentHelper.hpp`
  - `ActsExamples/TGeoDetector/AlignedTGeoDetectorElement.hpp`
  - `python/acts/examples/alignment.py`
- Millepede-II executable is **not** installed in `eicweb/eic_xl:nightly`:
  - `which pede` -> not found
  - `which mille` -> not found

## EICrecon outputs relevant to alignment handoff

From `podio_output.root`, these collections exist and are suitable as alignment input candidates:

- `CentralTrackerMeasurements` (`edm4eic::Measurement2D`)
- `CentralTrackSeeds` (`edm4eic::TrackSeed`)
- `CentralCKFTracks` / `CentralCKFTracksUnfiltered` (`edm4eic::Track`)
- `CentralCKFTruthSeededTracks` / `...Unfiltered` (`edm4eic::Track`)
- `B0TrackerMeasurements` and `B0TrackerCKFTracks`

These are enough to construct per-hit residual equations externally (Mille records), once a geometry parameterization and local-to-global derivative mapping are fixed.

## Proposed connection strategy (without delaying current prototype)

1. Freeze reconstruction outputs:
   - Keep using EICrecon CKF output (`Measurement2D` + fitted track states/parameters).
2. Build a lightweight exporter:
   - New standalone tool to read PODIO and emit Mille binary records per track/hit.
   - Local residual vector from measurement frame (`loc.a`, `loc.b`).
   - Global derivatives from chosen alignment DoF basis (`dx, dy, dz, rx, ry, rz`) per alignable surface.
3. Solve with Millepede-II (in a dedicated alignment image where `pede` is installed).
4. Feed back alignment constants:
   - Apply to reconstruction geometry (separate from simulation geometry).
5. Re-run EICrecon CKF and compare residual stats before/after.

## Required constraints for first alignment fit

- Fix reference DoF to remove rigid-body degeneracies:
  - At minimum lock one layer fully and constrain global translations/rotations.
- Keep simulation and reconstruction geometry separated:
  - Inject shifts only in reconstruction geometry for closure tests.
- Report separately:
  - injected truth shifts,
  - fitted corrections,
  - post-fit residual means/widths.

## Immediate next implementation item

Create a small `podio -> mille` exporter for `CentralTrackerMeasurements + CentralCKFTracks` and test on the existing `podio_output.root` from this prototype.
