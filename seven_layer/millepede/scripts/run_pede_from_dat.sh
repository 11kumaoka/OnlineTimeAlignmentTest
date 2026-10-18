#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <input.dat> <tag>"
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

INPUT_DAT="$1"
TAG="$2"
OUT_DIR="$ROOT_DIR/seven_layer/millepede/results/integrated"
STEER="$OUT_DIR/${TAG}_pede.txt"
LOG="$OUT_DIR/${TAG}_pede.log"
RES="$OUT_DIR/${TAG}_millepede.res"
MLOG="$OUT_DIR/${TAG}_millepede.log"

mkdir -p "$OUT_DIR"

cat > "$STEER" <<EOF
Cfiles
/work/${INPUT_DAT}
entries 5
method inversion 3 0.001
Parameter
1000 0.0 -1.0
2000 0.0 -1.0
1004 0.0 -1.0
2004 0.0 -1.0
1001 0.0 1.0
2001 0.0 1.0
1002 0.0 1.0
2002 0.0 1.0
1003 0.0 1.0
2003 0.0 1.0
printcounts
end
EOF

docker run --rm --platform "$PLATFORM" -v "$ROOT_DIR:/work" -w /work "$IMAGE" bash -lc '
  set -euo pipefail
  export LD_LIBRARY_PATH=/work/seven_layer/millepede/install/millepede-ii/lib:${LD_LIBRARY_PATH:-}
  cd seven_layer/millepede/results/integrated
  /work/seven_layer/millepede/install/millepede-ii/bin/pede "'"${TAG}_pede.txt"'" > "'"${TAG}_pede.log"'" 2>&1
  cp millepede.res "'"${TAG}_millepede.res"'"
  cp millepede.log "'"${TAG}_millepede.log"'"
'

echo "Steer: $STEER"
echo "Log:   $LOG"
echo "Res:   $RES"
echo "Mlog:  $MLOG"
