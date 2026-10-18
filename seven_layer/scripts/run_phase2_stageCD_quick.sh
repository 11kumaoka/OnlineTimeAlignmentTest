#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

mkdir -p "$ROOT_DIR/seven_layer/results" "$ROOT_DIR/seven_layer/logs"

# Stage C/D quick test: Measurement2D + truth-seeded CKF attempt on custom geometry.
docker run --rm --platform "$PLATFORM" -v "$ROOT_DIR:/work" -w /work "$IMAGE" bash -lc '
  set -euo pipefail
  source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1
  eicrecon \
    -Pplugins=log,dd4hep,evaluator,acts,algorithms_init,BVTX,MPGD,BTOF,tracking,podio,janatop \
    -Pjana:nevents=80 \
    -Pdd4hep:xml_files=seven_layer/geometry/seven_layer_telescope.xml \
    -Ppodio:output_file=seven_layer/results/phase2_stageCD_quick.root \
    -Ppodio:output_collections=EventHeader,MCParticles,SiMAPSHits,SiMAPSRawHits,SiMAPSRawHitLinks,SiMAPSRawHitAssociations,SiMAPSRecHits,CentralTrackingRecHits,CentralTrackingRawHitLinks,CentralTrackingRawHitAssociations,TrackerTruthSeeds,TrackerTruthSeedParameters,CentralTrackerTruthSeeds,CentralTrackerMeasurements,CentralCKFTruthSeededTracks,CentralCKFTruthSeededTrackParameters,CentralCKFTruthSeededTrackLinks,CentralCKFTruthSeededTrackAssociations \
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
    -Ptracking:centraltrackingrechits:inputtags=SiMAPSRecHits \
    -Ptracking:centraltrackingrechits:outputtags=CentralTrackingRecHits \
    -Ptracking:centraltrackermeasurements:inputtags=CentralTrackingRecHits \
    -Ptracking:centraltrackermeasurements:outputtags=CentralTrackerMeasurements \
    -Ptracking:trackertruthseeds:maxetaforward=10 \
    -Ptracking:trackertruthseeds:maxetabackward=10 \
    -Ptracking:trackertruthseeds:minmomentum=0.01 \
    seven_layer/results/phase2_sim_quick.edm4hep.root \
    > seven_layer/logs/phase2_stageCD_quick.log 2>&1 || true
'

echo "Wrote seven_layer/results/phase2_stageCD_quick.root and seven_layer/logs/phase2_stageCD_quick.log"
