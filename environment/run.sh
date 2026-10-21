#!/usr/bin/env bash
# Host: run a command in the EIC container. Arguments are passed without shell eval.
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ $# == 0 ]]; then echo 'Usage: environment/run.sh COMMAND [ARG ...]' >&2; exit 2; fi
# Isolate links created by the container login environment from the repository root.
mkdir -p "$repo/results/.environment"
if [[ -n ${TESTBENCH_CONTAINER:-} ]]; then
  image_id=$(docker inspect --format '{{.Image}}' "$TESTBENCH_CONTAINER")
  exec docker exec -e TESTBENCH_IMAGE="$image_id" -w /work/results/.environment "$TESTBENCH_CONTAINER" bash -lc 'cd /work; exec "$@"' testbench "$@"
fi
image_ref=${TESTBENCH_IMAGE:-eicweb/eic_xl@sha256:67c914295a92396040c3051360d70786df9c1ee8458264ad0b83cd1a8ccf3d05}
exec docker run --rm -e TESTBENCH_IMAGE="$image_ref" --platform "${TESTBENCH_PLATFORM:-linux/amd64}" \
  -v "$repo:/work" -w /work/results/.environment "$image_ref" \
  bash -lc 'cd /work; exec "$@"' testbench "$@"
