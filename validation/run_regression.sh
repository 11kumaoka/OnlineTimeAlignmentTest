#!/usr/bin/env bash
# Inside the container: uses the preserved local sample, never overwrites a run.
set -euo pipefail
if [[ $# != 1 ]]; then echo 'Usage: validation/run_regression.sh NEW_RESULT_DIR' >&2; exit 2; fi
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
exec python3 "$repo/local_detector_testbench/scripts/workflow.py" all \
  --result-dir "$1" \
  --sim-input "$repo/results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root" \
  --reference "$repo/validation/reference_metrics.json"
