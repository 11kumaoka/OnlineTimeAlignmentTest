#!/usr/bin/env bash
# Convenience orchestration only: every implementation lives in its own stage module.
set -euo pipefail
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd "$script_dir/.." && pwd)
cd "$repo"
result_dir=""
geometry_args=()
simulation_config_args=()
reconstruction_config_args=()
simulation_args=()
reconstruction_args=()
validation_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --result-dir|--run-dir) result_dir=${2:?Missing result directory}; shift 2 ;;
    --geometry-config) geometry_args+=("$1" "${2:?Missing Geometry scenario}"); shift 2 ;;
    --simulation-config) simulation_config_args+=(--config "${2:?Missing Simulation configuration}"); shift 2 ;;
    --reconstruction-config) reconstruction_config_args+=(--config "${2:?Missing Reconstruction configuration}"); shift 2 ;;
    --sim-input) simulation_args+=("$1" "${2:?Missing Simulation input}"); shift 2 ;;
    --build-dir) reconstruction_args+=("$1" "${2:?Missing build directory}"); shift 2 ;;
    --reference) validation_args+=("$1" "${2:?Missing reference}"); shift 2 ;;
    -h|--help)
      echo 'Usage: run_closure.sh --result-dir result/NEW [--simulation-config JSON] [--reconstruction-config JSON] [--geometry-config JSON] [--sim-input ROOT] [--build-dir DIR] [--reference JSON]'
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$result_dir" ]]; then echo 'A --result-dir is required' >&2; exit 2; fi
if [[ -e "$result_dir" || -L "$result_dir" ]]; then echo 'all requires a new run directory' >&2; exit 1; fi
bash "$repo/geometry/prepare_geometry.sh" --result-dir "$result_dir" "${geometry_args[@]}"
# Reject unsupported full Closure before starting Simulation.
bash "$repo/correction/correct_geometry.sh" --result-dir "$result_dir" --check-only
bash "$repo/simulation/simulate.sh" --result-dir "$result_dir" "${simulation_args[@]}" "${simulation_config_args[@]}"
bash "$repo/reconstruction/reconstruct.sh" --result-dir "$result_dir" "${reconstruction_args[@]}" "${reconstruction_config_args[@]}"
bash "$repo/alignment/align.sh" --result-dir "$result_dir"
bash "$repo/correction/correct_geometry.sh" --result-dir "$result_dir"
bash "$repo/reconstruction/reconstruct_corrected.sh" --result-dir "$result_dir" "${reconstruction_args[@]}" "${reconstruction_config_args[@]}"
bash "$repo/validation/validate.sh" --result-dir "$result_dir" "${validation_args[@]}"
