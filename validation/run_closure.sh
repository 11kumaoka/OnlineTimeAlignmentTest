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
digitization_args=()
validation_args=()
correction_args=()
alignment_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --result-dir|--run-dir) result_dir=${2:?Missing result directory}; shift 2 ;;
    --geometry-config) geometry_args+=("$1" "${2:?Missing Geometry scenario}"); shift 2 ;;
    --simulation-config) simulation_config_args+=(--config "${2:?Missing Simulation configuration}"); shift 2 ;;
    --reconstruction-config) reconstruction_config_args+=(--config "${2:?Missing Reconstruction configuration}"); shift 2 ;;
    --sim-input) simulation_args+=("$1" "${2:?Missing Simulation input}"); shift 2 ;;
    --build-dir) export TESTBENCH_BUILD_DIR="${2:?Missing build directory}"; reconstruction_args+=("$1" "$2"); digitization_args+=("$1" "$2"); shift 2 ;;
    --correction-mode)
      if [[ ${2:?Missing correction mode} == l1_rx_ry || $2 == l1_l2_rx_ry ]]; then
        echo 'Combined Rx/Ry disabled after failed finite-rotation closure; see docs/TILT_ALIGNMENT_VALIDATION.md.' >&2
        exit 2
      fi
      if [[ $2 == l1_rx || $2 == l1_ry || $2 == l1_rotations || $2 == l1_l2_rotations || $2 == l1_six_dof || $2 == l1_l2_six_dof || $2 == l3_six_dof || $2 == l1_l2_l3_six_dof ]]; then
        echo 'Tilt calibration requires derivative and observability gates: use calibration.controller; independent stage modules remain available.' >&2
        exit 2
      fi
      if [[ $2 == l1_z || $2 == l1_l2_z || $2 == l1_l2_xyz ]]; then
        echo 'Z calibration requires derivative and observability gates: use calibration.controller; independent stage modules remain available.' >&2
        exit 2
      fi
      if [[ ${2:?Missing correction mode} == l1_rz || $2 == l1_l2_rz || $2 == l1_l2_xy_rz ]]; then
        reconstruction_args+=(--alignment-mode "$2")
        alignment_args+=(--steering "$repo/alignment/pede_$2.txt")
      fi
      correction_args+=(--mode "${2:?Missing correction mode}"); validation_args+=("$1" "$2"); shift 2 ;;
    --reference) validation_args+=("$1" "${2:?Missing reference}"); shift 2 ;;
    -h|--help)
      echo 'Usage: run_closure.sh --result-dir result/NEW [--simulation-config JSON] [--reconstruction-config JSON] [--geometry-config JSON] [--sim-input ROOT] [--build-dir DIR] [--reference JSON] [--correction-mode l2_x|l1_l2_x|l1_l2_xy|l1_rz|l1_l2_rz|l1_l2_xy_rz]'
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$result_dir" ]]; then echo 'A --result-dir is required' >&2; exit 2; fi
if [[ -e "$result_dir" || -L "$result_dir" ]]; then echo 'all requires a new run directory' >&2; exit 1; fi
bash "$repo/geometry/prepare_geometry.sh" --result-dir "$result_dir" "${geometry_args[@]}"
# Reject unsupported full Closure before starting Simulation.
bash "$repo/correction/correct_geometry.sh" --result-dir "$result_dir" "${correction_args[@]}" --check-only
bash "$repo/simulation/simulate.sh" --result-dir "$result_dir" "${simulation_args[@]}" "${simulation_config_args[@]}"
bash "$repo/digitization/digitize.sh" --result-dir "$result_dir" "${digitization_args[@]}"
bash "$repo/reconstruction/reconstruct.sh" --result-dir "$result_dir" "${reconstruction_args[@]}" "${reconstruction_config_args[@]}"
bash "$repo/alignment/align.sh" --result-dir "$result_dir" "${alignment_args[@]}"
bash "$repo/correction/correct_geometry.sh" --result-dir "$result_dir" "${correction_args[@]}"
bash "$repo/reconstruction/reconstruct.sh" --after --result-dir "$result_dir" "${reconstruction_args[@]}" "${reconstruction_config_args[@]}"
bash "$repo/validation/validate.sh" --result-dir "$result_dir" "${validation_args[@]}"
