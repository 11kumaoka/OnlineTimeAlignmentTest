#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TOOLS_BIN="$ROOT_DIR/seven_layer/millepede/build/tools/beamtest_mille_toy"
PEDE_BIN="$ROOT_DIR/seven_layer/millepede/install/millepede-ii/bin/pede"
PEDE_LIB="$ROOT_DIR/seven_layer/millepede/install/millepede-ii/lib"

OUT_DIR="$ROOT_DIR/seven_layer/millepede/results/toy"
mkdir -p "$OUT_DIR" "$ROOT_DIR/seven_layer/logs"

if [[ ! -x "$TOOLS_BIN" ]]; then
  echo "Missing tool: $TOOLS_BIN"
  echo "Run: seven_layer/millepede/scripts/build_mille_tools.sh"
  exit 2
fi

if [[ ! -x "$PEDE_BIN" ]]; then
  echo "Missing pede: $PEDE_BIN"
  exit 2
fi

run_case() {
  local name="$1"
  local ax1="$2" ay1="$3" ax2="$4" ay2="$5" ax3="$6" ay3="$7"

  local dat="$OUT_DIR/${name}.dat"
  local str="$OUT_DIR/${name}.txt"
  local log="$OUT_DIR/${name}_pede.log"
  local genlog="$OUT_DIR/${name}_gen.log"

  "$TOOLS_BIN" \
    --output "$dat" \
    --tracks 3000 \
    --sigma 0.01 \
    --zref 100.0 \
    --axL1 "$ax1" --ayL1 "$ay1" \
    --axL2 "$ax2" --ayL2 "$ay2" \
    --axL3 "$ax3" --ayL3 "$ay3" \
    > "$genlog" 2>&1

  sed "s#__MILLE_BINARY__#${dat}#g" \
    "$ROOT_DIR/seven_layer/millepede/config/beamtest_pede_5layer_template.txt" > "$str"

  (
    cd "$OUT_DIR"
    export LD_LIBRARY_PATH="$PEDE_LIB:${LD_LIBRARY_PATH:-}"
    "$PEDE_BIN" "$str" > "$log" 2>&1
    cp millepede.res "${name}.res"
    cp millepede.log "${name}.millepede.log"
  )

  echo "CASE=$name"
  echo "  injected ax(mm): L1=$ax1 L2=$ax2 L3=$ax3"
  echo "  injected ay(mm): L1=$ay1 L2=$ay2 L3=$ay3"
  awk 'NR>1 && ($1==1001||$1==1002||$1==1003||$1==2001||$1==2002||$1==2003){print "  solved",$1,$2,$3,$4}' "$OUT_DIR/${name}.res"
}

run_case toy_posx_l2 0 0 0.200 0 0 0
run_case toy_negx_l2 0 0 -0.200 0 0 0
run_case toy_posy_l2 0 0 0 0.150 0 0
run_case toy_multi 0.080 -0.050 0.200 0.120 -0.100 0.040

echo "Toy closure outputs: $OUT_DIR"
