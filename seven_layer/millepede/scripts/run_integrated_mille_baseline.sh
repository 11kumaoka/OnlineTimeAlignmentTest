#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

OUT_DAT="seven_layer/millepede/results/integrated/local_beamtest_mille_integrated.dat"
OUT_ROOT="seven_layer/results/local_simaps_reco_mille_integrated.root"
OUT_LOG="seven_layer/logs/local_eicrecon_runtime_mille_integrated.log"

mkdir -p "$ROOT_DIR/seven_layer/millepede/results/integrated" "$ROOT_DIR/seven_layer/logs" "$ROOT_DIR/seven_layer/results"

docker run --rm --platform "$PLATFORM" -v "$ROOT_DIR:/work" -w /work "$IMAGE" bash -lc '
  set -euo pipefail
  source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1
  export LD_LIBRARY_PATH=/work/seven_layer/millepede/install/millepede-ii/lib:${LD_LIBRARY_PATH:-}
  export JANA_PLUGIN_PATH=/opt/local/lib/EICrecon/plugins:/opt/local/lib/JANA/plugins:/work/seven_layer/local_eicrecon/build

  rm -f seven_layer/millepede/results/integrated/local_beamtest_mille_integrated.dat seven_layer/results/local_simaps_reco_mille_integrated.root

  eicrecon \
    -Pplugins=log,dd4hep,evaluator,acts,algorithms_init,podio,janatop,BeamTestReco \
    -Pplugins_to_ignore=BVTX,MPGD,BTOF,tracking \
    -Pdd4hep:xml_files=seven_layer/geometry/seven_layer_telescope.xml \
    -Pjana:nevents=80 \
    -Pbeamtstreco:milleEnabled=1 \
    -Pbeamtstreco:milleOutputPath=seven_layer/millepede/results/integrated/local_beamtest_mille_integrated.dat \
    -Pbeamtstreco:milleZRefMm=100.0 \
    -Pbeamtstreco:milleRequireSingleTrack=1 \
    -Ppodio:output_file=seven_layer/results/local_simaps_reco_mille_integrated.root \
    -Ppodio:output_collections=EventHeader,SiMAPSHits,MPGDHits,ACLGADHits,LocalSiMAPSRawHits,LocalSiMAPSRawHitLinks,LocalSiMAPSRawHitAssociations,LocalSiMAPSRecHits,LocalMPGDRawHits,LocalMPGDRawHitLinks,LocalMPGDRawHitAssociations,LocalMPGDRecHits,LocalACLGADRawHits,LocalACLGADRawHitLinks,LocalACLGADRawHitAssociations,LocalACLGADRecHits,LocalBeamTestTrajectories,LocalBeamTestTrackParameters,LocalBeamTestTracks,LocalBeamTestFitMeasurements,LocalBeamTestPredictedMeasurements,LocalBeamTestFilteredMeasurements,LocalBeamTestSmoothedMeasurements,LocalBeamTestPredictedSegments,LocalBeamTestFilteredSegments,LocalBeamTestSmoothedSegments \
    seven_layer/results/phase2_sim_quick_normal_recofix.edm4hep.root \
    > seven_layer/logs/local_eicrecon_runtime_mille_integrated.log 2>&1
'

echo "Wrote $OUT_DAT"
echo "Wrote $OUT_ROOT"
echo "Log:   $OUT_LOG"
