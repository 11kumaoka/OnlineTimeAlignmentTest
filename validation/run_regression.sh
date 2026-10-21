#!/usr/bin/env bash
# Inside the container: uses the preserved local sample, never overwrites a run.
set -euo pipefail
if [[ $# -lt 1 || $# -gt 2 ]]; then echo 'Usage: validation/run_regression.sh NEW_RESULT_DIR [BUILD_DIR]' >&2; exit 2; fi
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
build_args=()
if [[ $# == 2 ]]; then build_args=(--build-dir "$2"); fi
exec bash "$repo/validation/run_closure.sh" \
  --result-dir "$1" "${build_args[@]}" \
  --sim-input "$repo/results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root" \
  --reference "$repo/validation/reference_metrics.json"
