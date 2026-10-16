# Phase 1 report: seven-layer DD4hep simulation validation (2026-10-15)

## 1. What was implemented

Implemented a separate seven-layer development area under seven_layer with:

- Geometry:
  - seven_layer/geometry/seven_layer_telescope.xml
- Configuration metadata:
  - seven_layer/config/seven_layer_layout.json
- Validation scripts:
  - seven_layer/scripts/run_phase1_ddsim.sh
  - seven_layer/scripts/summarize_hits.py
  - seven_layer/scripts/check_overlaps.py
  - seven_layer/scripts/plot_layout.py

Detector composition implemented:

- Five SiMAPS planes at z = 0, 50, 100, 150, 200 mm
- One MPGD plane at z = 250 mm
- One AC-LGAD plane at z = 300 mm
- Active area target: 100 mm x 100 mm per plane
- Beam: 5 GeV mu- along +z, with small angular spread and vertex spread in beam run

Readout/uncertainty assumptions documented:

- SiMAPS: provisional 10 um in both transverse coordinates
- MPGD: provisional 150 um in both transverse coordinates
- AC-LGAD: documented as 1D strip-like assumption in config (pitch-based u estimate, v unresolved for this phase)

## 2. Exact execution commands

Primary command used:

- bash seven_layer/scripts/run_phase1_ddsim.sh

This script executes:

- 1-event straight-through run:
  - ddsim --compactFile seven_layer/geometry/seven_layer_telescope.xml --outputFile seven_layer/results/sim_seven_layer_single.edm4hep.root --numberOfEvents 1 --enableGun --gun.particle mu- --gun.energy 5*GeV --gun.thetaMin 0.0 --gun.thetaMax 0.0 --gun.phiMin 0.0 --gun.phiMax 0.0 --gun.distribution uniform

- 200-event small-spread beam run:
  - ddsim --compactFile seven_layer/geometry/seven_layer_telescope.xml --outputFile seven_layer/results/sim_seven_layer_beam.edm4hep.root --numberOfEvents 200 --enableGun --gun.particle mu- --gun.energy 5*GeV --gun.thetaMin 0.0 --gun.thetaMax 0.003 --gun.phiMin 0.0 --gun.phiMax 6.283185307179586 --gun.distribution uniform --vertexSigma 0.2 0.2 0.0 0.0

- Hit summaries:
  - python seven_layer/scripts/summarize_hits.py --input seven_layer/results/sim_seven_layer_single.edm4hep.root --out seven_layer/results/phase1_hits_single_summary.json
  - python seven_layer/scripts/summarize_hits.py --input seven_layer/results/sim_seven_layer_beam.edm4hep.root --out seven_layer/results/phase1_hits_beam_summary.json

- Geometry conversion + overlap check:
  - geoConverter -compact2gdml -input seven_layer/geometry/seven_layer_telescope.xml -output seven_layer/results/seven_layer_telescope.gdml
  - python seven_layer/scripts/check_overlaps.py --gdml seven_layer/results/seven_layer_telescope.gdml --out seven_layer/results/phase1_overlap_summary.json

- Geometry layout visualization:
  - python seven_layer/scripts/plot_layout.py --config seven_layer/config/seven_layer_layout.json --out seven_layer/results/seven_layer_layout.png

## 3. Tests passed or failed

Passed:

- Geometry loads successfully in DDSim
- Seven intended layer IDs are present across SiMAPS + MPGD + AC-LGAD collections
- Single event crossing check records one hit in each intended layer:
  - SiMAPS layers 0-4 each have 1 hit
  - MPGD layer 5 has 1 hit
  - AC-LGAD layer 6 has 1 hit
- Hit summaries include valid detector IDs (system IDs 201/202/203), layer IDs, module ID, sensor ID, and positions
- Overlap check reports no overlaps:
  - n_overlaps = 0
- Layer z positions in summaries agree with intended placement (within thickness/step effects)

Failed:

- No blocking Phase 1 failures remain after fixes.

## 4. Relevant plots and numerical results

Files:

- seven_layer/results/phase1_hits_single_summary.json
- seven_layer/results/phase1_hits_beam_summary.json
- seven_layer/results/phase1_overlap_summary.json
- seven_layer/results/seven_layer_layout.png
- seven_layer/results/seven_layer_telescope.gdml

Key numerical checks:

- Single-event run:
  - SiMAPSHits total = 5 (layers 0..4)
  - MPGDHits total = 1 (layer 5)
  - ACLGADHits total = 1 (layer 6)

- Beam run (200 events):
  - SiMAPSHits total = 1015
  - MPGDHits total = 228
  - ACLGADHits total = 210
  - overlap count = 0

## 5. Current limitations

- Geometry is intentionally simplified and does not yet model full EPIC detector-specific mechanical details.
- MPGD and AC-LGAD are represented as simplified planar sensitive volumes for this milestone.
- AC-LGAD timing behavior is not modeled yet (timing calibration is deferred by plan).
- This phase validates simulation geometry and hit production only; it does not yet demonstrate EICrecon CKF reconstruction on this exact geometry.

## 6. Recommended next step

Proceed to Phase 2: connect this exact seven-layer geometry output to EICrecon ACTS tracking chain.

- Start with SiMAPS-only reconstruction path (layers 0..4)
- Add MPGD and AC-LGAD measurements incrementally
- Reuse TrackerMeasurementFromHits and CKFTracking factory chain, introducing only local adapter plugin/config where needed
- Validate collection wiring, CellID-to-ACTS surface mapping, and zero-field seeding/fitting behavior
