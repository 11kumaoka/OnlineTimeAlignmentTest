#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$ROOT_DIR/seven_layer"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

mkdir -p "$OUT_DIR/results" "$OUT_DIR/logs"

# 1) One-event straight beam check (must cross all seven planes).
docker run --rm --platform "$PLATFORM" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    ddsim \
      --compactFile seven_layer/geometry/seven_layer_telescope.xml \
      --outputFile seven_layer/results/sim_seven_layer_single.edm4hep.root \
      --numberOfEvents 1 \
      --enableGun \
      --gun.particle mu- \
      --gun.energy 5*GeV \
      --gun.thetaMin 0.0 --gun.thetaMax 0.0 \
      --gun.phiMin 0.0 --gun.phiMax 0.0 \
      --gun.distribution uniform \
      2>&1 | tee seven_layer/logs/phase1_ddsim_single.log
  '

# 2) Beam run with small spread.
docker run --rm --platform "$PLATFORM" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    ddsim \
      --compactFile seven_layer/geometry/seven_layer_telescope.xml \
      --outputFile seven_layer/results/sim_seven_layer_beam.edm4hep.root \
      --numberOfEvents 200 \
      --enableGun \
      --gun.particle mu- \
      --gun.energy 5*GeV \
      --gun.thetaMin 0.0 --gun.thetaMax 0.003 \
      --gun.phiMin 0.0 --gun.phiMax 6.283185307179586 \
      --gun.distribution uniform \
      --vertexSigma 0.2 0.2 0.0 0.0 \
      2>&1 | tee seven_layer/logs/phase1_ddsim_beam.log
  '

# 3) Summaries and overlap checks.
docker run --rm --platform "$PLATFORM" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    python seven_layer/scripts/summarize_hits.py \
      --input seven_layer/results/sim_seven_layer_single.edm4hep.root \
      --out seven_layer/results/phase1_hits_single_summary.json

    python seven_layer/scripts/summarize_hits.py \
      --input seven_layer/results/sim_seven_layer_beam.edm4hep.root \
      --out seven_layer/results/phase1_hits_beam_summary.json

    geoConverter \
      -compact2gdml \
      -input seven_layer/geometry/seven_layer_telescope.xml \
      -output seven_layer/results/seven_layer_telescope.gdml \
      > seven_layer/logs/phase1_geoconverter.log 2>&1

    python seven_layer/scripts/check_overlaps.py \
      --gdml seven_layer/results/seven_layer_telescope.gdml \
      --out seven_layer/results/phase1_overlap_summary.json

    python seven_layer/scripts/plot_layout.py \
      --config seven_layer/config/seven_layer_layout.json \
      --out seven_layer/results/seven_layer_layout.png
  '

echo "Phase 1 complete."
