#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
mkdir -p results/.environment

# Match the XQuartz access setup used by the working eic-shell.
xhost +localhost

docker run --rm -it \
  --platform linux/amd64 \
  -e DISPLAY=host.docker.internal:0 \
  -v /tmp:/tmp \
  -v "$PWD:/work" \
  -w /work/results/.environment \
  "${TESTBENCH_IMAGE:-eicweb/eic_xl@sha256:67c914295a92396040c3051360d70786df9c1ee8458264ad0b83cd1a8ccf3d05}" \
  bash -l
