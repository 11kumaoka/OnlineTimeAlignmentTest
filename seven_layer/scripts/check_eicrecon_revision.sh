#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCAL_EICRECON="/Users/tkumaoka/eic/EICrecon"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

mkdir -p "$ROOT_DIR/seven_layer/results" "$ROOT_DIR/seven_layer/logs"

{
  echo "=== Local EICrecon (read-only inspection) ==="
  cd "$LOCAL_EICRECON"
  echo "path: $PWD"
  git rev-parse HEAD
  git log -1 --oneline
  git status -sb

  echo
  echo "=== Docker EICrecon runtime ==="
  docker run --rm --platform "$PLATFORM" "$IMAGE" bash -lc '
    eicrecon --version
    eicrecon --janaversion
    ls -d /opt/software/linux-x86_64_v2/acts-* | sort | tail -n 1
    ls -d /opt/software/linux-x86_64_v2/edm4eic-* 2>/dev/null | sort | tail -n 1
    ls -d /opt/software/linux-x86_64_v2/edm4hep-* 2>/dev/null | sort | tail -n 1
  '
} | tee "$ROOT_DIR/seven_layer/results/eicrecon_revision_compare.txt"

echo "Wrote seven_layer/results/eicrecon_revision_compare.txt"
