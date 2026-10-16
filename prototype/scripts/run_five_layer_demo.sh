#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$ROOT_DIR/prototype/results"

python "$ROOT_DIR/prototype/scripts/five_layer_residual_demo.py" \
  --config "$ROOT_DIR/prototype/config/five_layer_telescope.json" \
  --n-tracks 5000 \
  --seed 12345 \
  --out-dir "$ROOT_DIR/prototype/results"
