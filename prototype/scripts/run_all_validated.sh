#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 1) Baseline CKF run on EPIC tracking-only geometry (inside Docker).
bash "$ROOT_DIR/prototype/scripts/run_ckf_baseline.sh"

# 2) Post-processing: CKF summary + five-layer residual/alignment demo.
docker run --rm --platform linux/amd64 \
  -v "$ROOT_DIR:/work" -w /work eicweb/eic_xl:nightly \
  bash -lc 'bash prototype/scripts/run_analysis_bundle.sh'

# 3) Five-layer DD4hep geometry smoke test.
docker run --rm --platform linux/amd64 \
  -v "$ROOT_DIR:/work" -w /work eicweb/eic_xl:nightly \
  bash -lc 'ddsim --compactFile prototype/geometry/five_layer_telescope_barrel.xml --outputFile artifacts/sim_five_layer_barrel.edm4hep.root --numberOfEvents 1 --enableGun --gun.particle mu- --gun.energy 5*GeV --gun.thetaMin 1.5708 --gun.thetaMax 1.5708 --gun.phiMin 0 --gun.phiMax 0 --gun.distribution uniform > logs/06_ddsim_five_layer_barrel.log 2>&1'

echo "All validated steps completed."
