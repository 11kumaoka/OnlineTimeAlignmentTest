#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

mkdir -p "$ROOT_DIR/seven_layer/logs"

# Build and run standalone ACTS fit on SiMAPS RecHits produced by Stage A/B.
docker run --rm --platform "$PLATFORM" -v "$ROOT_DIR:/work" -w /work "$IMAGE" bash -lc '
  set -euo pipefail
  source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1
  cmake -S seven_layer/standalone_acts -B seven_layer/standalone_acts/build -DCMAKE_BUILD_TYPE=Release \
    > seven_layer/logs/standalone_acts_cmake.log 2>&1
  cmake --build seven_layer/standalone_acts/build -j \
    > seven_layer/logs/standalone_acts_build.log 2>&1
  ./seven_layer/standalone_acts/build/seven_layer_acts_fit \
    seven_layer/results/local_simaps_reco.root \
    LocalSiMAPSRecHits \
    seven_layer/results/local_to_acts_event_stats.csv \
    > seven_layer/logs/standalone_acts_fit.log 2>&1
'

echo "Wrote logs:"
echo "  seven_layer/logs/standalone_acts_cmake.log"
echo "  seven_layer/logs/standalone_acts_build.log"
echo "  seven_layer/logs/standalone_acts_fit.log"
echo "  seven_layer/results/local_to_acts_event_stats.csv"
