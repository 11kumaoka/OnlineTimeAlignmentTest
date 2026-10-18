#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$ROOT_DIR/seven_layer"
IMAGE="eicweb/eic_xl:nightly"
PLATFORM="linux/amd64"

mkdir -p "$OUT_DIR/results" "$OUT_DIR/logs"

SIM_FILE="seven_layer/results/phase2_sim_beam.edm4hep.root"
RECO_SIMAPS_FILE="seven_layer/results/phase2_reco_simaps.root"
RECO_SIMAPS_MPGD_FILE="seven_layer/results/phase2_reco_simaps_mpgd.root"
COLLECTIONS="EventHeader,MCParticles,SiMAPSHits,MPGDHits,ACLGADHits,SiMAPSRawHits,SiMAPSRawHitLinks,SiMAPSRawHitAssociations,SiMAPSRecHits,MPGDRawHits,MPGDRawHitLinks,MPGDRawHitAssociations,MPGDRecHits,ACLGADRawHits,ACLGADRawHitLinks,ACLGADRawHitAssociations,ACLGADRecHits,CentralTrackingRecHits,CentralTrackingRawHitLinks,CentralTrackingRawHitAssociations,CentralTrackerMeasurements,TrackerTruthSeeds,TrackerTruthSeedParameters,CentralTrackerTruthSeeds,CentralCKFTruthSeededActsTrackStatesUnfiltered,CentralCKFTruthSeededActsTracksUnfiltered,CentralCKFTruthSeededActsTrackStates,CentralCKFTruthSeededActsTracks,CentralCKFTruthSeededTrajectories,CentralCKFTruthSeededTrackParameters,CentralCKFTruthSeededTracks,CentralCKFTruthSeededTrackLinks,CentralCKFTruthSeededTrackAssociations,CentralTrackSeeds,CentralTrackSeedParameters,CentralCKFActsTrackStatesUnfiltered,CentralCKFActsTracksUnfiltered,CentralCKFTrajectoriesUnfiltered,CentralCKFTrackParametersUnfiltered,CentralCKFTracksUnfiltered,CentralCKFTrackUnfilteredLinks,CentralCKFTrackUnfilteredAssociations,CentralCKFActsTrackStates,CentralCKFActsTracks,CentralCKFTrajectories,CentralCKFTrackParameters,CentralCKFTracks,CentralCKFTrackLinks,CentralCKFTrackAssociations"

# Phase 2 simulation with segmented readout geometry.
docker run --rm --platform "$PLATFORM" \
  -e COLLECTIONS="$COLLECTIONS" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    ddsim \
      --compactFile seven_layer/geometry/seven_layer_telescope.xml \
      --outputFile seven_layer/results/phase2_sim_beam.edm4hep.root \
      --numberOfEvents 500 \
      --enableGun \
      --gun.particle mu- \
      --gun.energy 5*GeV \
      --gun.thetaMin 0.010 --gun.thetaMax 0.030 \
      --gun.phiMin 0.0 --gun.phiMax 6.283185307179586 \
      --gun.distribution uniform \
      --vertexSigma 0.2 0.2 0.0 0.0 \
      2>&1 | tee seven_layer/logs/phase2_ddsim.log
  '

# Run 1: full Sim->Raw->Rec->Measurement->CKF with SiMAPS-only tracking input.
docker run --rm --platform "$PLATFORM" \
  -e COLLECTIONS="$COLLECTIONS" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1

    eicrecon \
      -Pplugins=log,dd4hep,evaluator,acts,algorithms_init,BVTX,MPGD,BTOF,tracking,podio \
      -Pjana:nevents=500 \
      -Pdd4hep:xml_files=seven_layer/geometry/seven_layer_telescope.xml \
      -Ppodio:output_file=seven_layer/results/phase2_reco_simaps.root \
      -Ppodio:output_collections="$COLLECTIONS" \
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
      seven_layer/results/phase2_sim_beam.edm4hep.root \
      2>&1 | tee seven_layer/logs/phase2_eicrecon_simaps.log
  '

# Run 2: add MPGD reconstructed hits into the central tracking hit merger.
docker run --rm --platform "$PLATFORM" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    source /opt/software/linux-x86_64_v2/epic-26.05.0-2ixc5forg4ihbpragwu2m6422njxulk3/bin/thisepic.sh >/dev/null 2>&1

    eicrecon \
      -Pplugins=log,dd4hep,evaluator,acts,algorithms_init,BVTX,MPGD,BTOF,tracking,podio \
      -Pjana:nevents=500 \
      -Pdd4hep:xml_files=seven_layer/geometry/seven_layer_telescope.xml \
      -Ppodio:output_file=seven_layer/results/phase2_reco_simaps_mpgd.root \
      -Ppodio:output_collections="$COLLECTIONS" \
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
      -Ptracking:centraltrackingrechits:inputtags=SiMAPSRecHits,MPGDRecHits \
      -Ptracking:centraltrackingrechits:outputtags=CentralTrackingRecHits \
      -Ptracking:centraltrackermeasurements:inputtags=CentralTrackingRecHits \
      -Ptracking:centraltrackermeasurements:outputtags=CentralTrackerMeasurements \
      -Ptracking:trackertruthseeds:maxetaforward=10 \
      -Ptracking:trackertruthseeds:maxetabackward=10 \
      -Ptracking:trackertruthseeds:minmomentum=0.01 \
      seven_layer/results/phase2_sim_beam.edm4hep.root \
      2>&1 | tee seven_layer/logs/phase2_eicrecon_simaps_mpgd.log
  '

docker run --rm --platform "$PLATFORM" \
  -v "$ROOT_DIR:/work" -w /work "$IMAGE" \
  bash -lc '
    set -euo pipefail
    python seven_layer/scripts/analyze_phase2_chain.py \
      --input seven_layer/results/phase2_reco_simaps.root \
      --out seven_layer/results/phase2_chain_summary_simaps.json

    python seven_layer/scripts/analyze_phase2_chain.py \
      --input seven_layer/results/phase2_reco_simaps_mpgd.root \
      --out seven_layer/results/phase2_chain_summary_simaps_mpgd.json
  '

echo "Phase 2 reconstruction pipeline completed."