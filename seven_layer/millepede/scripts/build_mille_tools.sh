#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BUILD_DIR="$ROOT_DIR/seven_layer/millepede/build/tools"
INSTALL_MP2="$ROOT_DIR/seven_layer/millepede/install/millepede-ii"

mkdir -p "$BUILD_DIR" "$ROOT_DIR/seven_layer/logs"

cmake -S "$ROOT_DIR/seven_layer/millepede" -B "$BUILD_DIR" \
  -DMILLEPEDE_PREFIX="$INSTALL_MP2" \
  > "$ROOT_DIR/seven_layer/logs/mille_tools_cmake.log" 2>&1

cmake --build "$BUILD_DIR" -j \
  > "$ROOT_DIR/seven_layer/logs/mille_tools_build.log" 2>&1

echo "Built: $BUILD_DIR/beamtest_mille_toy"
