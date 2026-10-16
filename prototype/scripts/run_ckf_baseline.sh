#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$ROOT_DIR/artifacts" "$ROOT_DIR/logs"

IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

# This run is isolated in Docker and does not modify host eic-shell.
docker run --rm --platform "$PLATFORM" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1

    ddsim \
      --compactFile $DETECTOR_PATH/epic_craterlake_tracking_only.xml \
      --outputFile artifacts/sim_tracking.edm4hep.root \
      --numberOfEvents 20 \
      --enableGun \
      --gun.particle mu- \
      --gun.energy 5*GeV \
      --gun.thetaMin 1.5708 --gun.thetaMax 1.5708 \
      --gun.phiMin 0.0 --gun.phiMax 0.0 \
      --gun.distribution uniform \
      2>&1 | tee logs/03_ddsim_tracking.log

    eicrecon \
      -Pjana:nevents=20 \
      artifacts/sim_tracking.edm4hep.root \
      2>&1 | tee logs/04_eicrecon_tracking_only.log
  '
