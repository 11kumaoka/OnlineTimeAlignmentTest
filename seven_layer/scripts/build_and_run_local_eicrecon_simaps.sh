#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

mkdir -p "$ROOT_DIR/seven_layer/logs" "$ROOT_DIR/seven_layer/results"

docker run --rm --platform "$PLATFORM" -v "$ROOT_DIR:/work" -w /work "$IMAGE" bash -lc '
  set -euo pipefail
  source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1

  cmake -S seven_layer/local_eicrecon -B seven_layer/local_eicrecon/build -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    > seven_layer/logs/local_eicrecon_cmake.log 2>&1

  cmake --build seven_layer/local_eicrecon/build -j \
    > seven_layer/logs/local_eicrecon_build.log 2>&1

  export JANA_PLUGIN_PATH=/opt/local/lib/EICrecon/plugins:/opt/local/lib/JANA/plugins:/work/seven_layer/local_eicrecon/build

  eicrecon \
    -Pplugins=log,dd4hep,evaluator,acts,algorithms_init,podio,janatop,BeamTestReco \
    -Pplugins_to_ignore=BVTX,MPGD,BTOF,tracking \
    -Pdd4hep:xml_files=seven_layer/geometry/seven_layer_telescope.xml \
    -Pjana:nevents=80 \
    -Ppodio:output_file=seven_layer/results/local_simaps_reco.root \
    -Ppodio:output_collections=EventHeader,SiMAPSHits,MPGDHits,ACLGADHits,LocalSiMAPSRawHits,LocalSiMAPSRawHitLinks,LocalSiMAPSRawHitAssociations,LocalSiMAPSRecHits,LocalMPGDRawHits,LocalMPGDRawHitLinks,LocalMPGDRawHitAssociations,LocalMPGDRecHits,LocalACLGADRawHits,LocalACLGADRawHitLinks,LocalACLGADRawHitAssociations,LocalACLGADRecHits,LocalBeamTestTrajectories,LocalBeamTestTrackParameters,LocalBeamTestTracks,LocalBeamTestFitMeasurements,LocalBeamTestPredictedMeasurements,LocalBeamTestFilteredMeasurements,LocalBeamTestSmoothedMeasurements,LocalBeamTestPredictedSegments,LocalBeamTestFilteredSegments,LocalBeamTestSmoothedSegments \
    seven_layer/results/phase2_sim_quick.edm4hep.root \
    > seven_layer/logs/local_eicrecon_runtime.log 2>&1
'

echo "Build log:   seven_layer/logs/local_eicrecon_build.log"
echo "Runtime log: seven_layer/logs/local_eicrecon_runtime.log"
echo "Output:      seven_layer/results/local_simaps_reco.root"
