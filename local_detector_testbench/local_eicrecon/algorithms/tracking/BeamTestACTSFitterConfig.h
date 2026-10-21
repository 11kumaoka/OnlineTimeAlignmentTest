// Origin: local implementation for seven-layer beam-test framework
// Local purpose: configure in-process ACTS fitting in JANA2 factory

#pragma once

namespace local_eicrecon {

struct BeamTestACTSFitterConfig {
  bool useMPGD = true;
  bool useACLGAD = false;
  bool inputHitsAreGlobal = true;
  bool useMuonHypothesis = true;
  int outputTrackPDG = 13;
  double seedQOverP = -0.2; // 1/GeV, weak prior in zero-field setup
  double timeResolution = 1.0;
  int excludeLayerFromFit = -1;
  int alignmentTestShiftLayer = -1;
  double alignmentTestShiftXmm = 0.0;
};

} // namespace local_eicrecon
