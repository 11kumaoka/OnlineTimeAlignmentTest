#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

mkdir -p "$ROOT_DIR/seven_layer/results" "$ROOT_DIR/seven_layer/logs"

# Stage A/B: SimTrackerHit -> RawTrackerHit -> TrackerHit only, with minimal plugin set.
docker run --rm --platform "$PLATFORM" -v "$ROOT_DIR:/work" -w /work "$IMAGE" bash -lc '
  set -euo pipefail
  source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1
  eicrecon \
    -Pplugins=log,dd4hep,evaluator,BVTX,MPGD,BTOF,podio,janatop \
    -Pjana:nevents=300 \
    -Pdd4hep:xml_files=seven_layer/geometry/seven_layer_telescope.xml \
    -Ppodio:output_file=seven_layer/results/phase2_stageAB.root \
    -Ppodio:output_collections=EventHeader,MCParticles,SiMAPSHits,MPGDHits,ACLGADHits,SiMAPSRawHits,SiMAPSRawHitLinks,SiMAPSRawHitAssociations,SiMAPSRecHits,MPGDRawHits,MPGDRawHitLinks,MPGDRawHitAssociations,MPGDRecHits,ACLGADRawHits,ACLGADRawHitLinks,ACLGADRawHitAssociations,ACLGADRecHits \
    -Pbvtx:sibarrelvertexrawhits:inputtags=EventHeader,SiMAPSHits \
    -Pbvtx:sibarrelvertexrawhits:outputtags=SiMAPSRawHits,SiMAPSRawHitLinks,SiMAPSRawHitAssociations \
    -Pbvtx:sibarrelvertexrechits:inputtags=SiMAPSRawHits \
    -Pbvtx:sibarrelvertexrechits:outputtags=SiMAPSRecHits \
    -Pmpgd:mpgdbarrelrawhits:inputtags=EventHeader,MPGDHits \
    -Pmpgd:mpgdbarrelrawhits:outputtags=MPGDRawHits,MPGDRawHitLinks,MPGDRawHitAssociations \
    -Pmpgd:mpgdbarrelrechits:inputtags=MPGDRawHits \
    -Pmpgd:mpgdbarrelrechits:outputtags=MPGDRecHits \
    -Pbtof:tofbarrelrawhits:inputtags=EventHeader,ACLGADHits \
    -Pbtof:tofbarrelrawhits:outputtags=ACLGADRawHits,ACLGADRawHitLinks,ACLGADRawHitAssociations \
    -Pbtof:tofbarrelrechits:inputtags=ACLGADRawHits \
    -Pbtof:tofbarrelrechits:outputtags=ACLGADRecHits \
    seven_layer/results/phase2_sim_beam.edm4hep.root \
    2>&1 | tee seven_layer/logs/phase2_stageAB.log
'

docker run --rm --platform "$PLATFORM" -v "$ROOT_DIR:/work" -w /work "$IMAGE" bash -lc '
  set -euo pipefail
  python seven_layer/scripts/analyze_phase2_chain.py \
    --input seven_layer/results/phase2_stageAB.root \
    --out seven_layer/results/phase2_stageAB_summary.json
'

echo "Wrote seven_layer/results/phase2_stageAB.root and phase2_stageAB_summary.json"
