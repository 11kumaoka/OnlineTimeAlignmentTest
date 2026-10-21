#!/usr/bin/env bash
# Build the local EICrecon Plugin inside the EIC container using a dedicated build tree.
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
prefix=${MILLEPEDE_PREFIX:-$repo/external/install}
build_dir=${TESTBENCH_BUILD_DIR:-$repo/build/local_eicrecon_external}
if [[ ! -f $prefix/cmake/MilleConfig.cmake || ! -f $prefix/lib/libMille2.so || ! -x $prefix/bin/pede ]]; then
  echo "Incomplete dependency installation: $prefix. Run environment/setup_dependencies.py; no legacy fallback is used." >&2
  exit 2
fi
cmake -S "$repo/localDetEICrecon" -B "$build_dir" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DMILLEPEDE_PREFIX="$prefix" -DMille_DIR="$prefix/cmake"
cmake --build "$build_dir" -j "${BUILD_JOBS:-2}"
