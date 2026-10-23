// Origin: local implementation for seven-layer beam-test framework
// Local purpose: expose in-process ACTS fitting as JOmniFactory

#pragma once

#include "algorithms/tracking/BeamTestACTSFitter.h"
#include "extensions/jana/JOmniFactory.h"
#include "services/geometry/dd4hep/DD4hep_service.h"
#include "geometry/SurfacePlacements.h"

namespace local_eicrecon {

class BeamTestACTSFitter_factory
    : public JOmniFactory<BeamTestACTSFitter_factory, BeamTestACTSFitterConfig> {
public:
  using AlgoT = local_eicrecon::BeamTestACTSFitter;

private:
  std::unique_ptr<AlgoT> m_algo;
  Service<DD4hep_service> m_geometry{this};

  PodioInput<edm4eic::TrackerHit> m_simaps_hits_input{this};
  PodioInput<edm4eic::TrackerHit> m_mpgd_hits_input{this};
  PodioInput<edm4eic::TrackerHit> m_aclgad_hits_input{this};

  PodioOutput<edm4eic::Trajectory> m_trajectories_output{this};
  PodioOutput<edm4eic::TrackParameters> m_track_parameters_output{this};
  PodioOutput<edm4eic::Track> m_tracks_output{this};
  PodioOutput<edm4eic::Measurement2D> m_fit_measurements_output{this};
  PodioOutput<edm4eic::Measurement2D> m_predicted_measurements_output{this};
  PodioOutput<edm4eic::Measurement2D> m_filtered_measurements_output{this};
  PodioOutput<edm4eic::Measurement2D> m_smoothed_measurements_output{this};
  PodioOutput<edm4eic::TrackSegment> m_predicted_segments_output{this};
  PodioOutput<edm4eic::TrackSegment> m_filtered_segments_output{this};
  PodioOutput<edm4eic::TrackSegment> m_smoothed_segments_output{this};

  ParameterRef<bool> m_useMPGD{this, "useMPGD", config().useMPGD};
  ParameterRef<bool> m_useACLGAD{this, "useACLGAD", config().useACLGAD};
  ParameterRef<bool> m_inputHitsAreGlobal{this, "inputHitsAreGlobal", config().inputHitsAreGlobal};
  ParameterRef<bool> m_useMuonHypothesis{this, "useMuonHypothesis", config().useMuonHypothesis};
  ParameterRef<int> m_outputTrackPDG{this, "outputTrackPDG", config().outputTrackPDG};
  ParameterRef<double> m_seedQOverP{this, "seedQOverP", config().seedQOverP};
  ParameterRef<int> m_excludeLayerFromFit{this, "excludeLayerFromFit", config().excludeLayerFromFit};
  ParameterRef<int> m_alignmentTestShiftLayer{this, "alignmentTestShiftLayer", config().alignmentTestShiftLayer};
  ParameterRef<double> m_alignmentTestShiftXmm{this, "alignmentTestShiftXmm", config().alignmentTestShiftXmm};

public:
  void Configure() {
    m_algo = std::make_unique<AlgoT>(GetPrefix());
    m_algo->level(static_cast<algorithms::LogLevel>(logger()->level()));
    m_algo->applyConfig(config());
    m_algo->setPlacements(surfacePlacements(*m_geometry().converter()));
    m_algo->init();
  }

  void Process(int32_t /* run_number */, uint64_t /* event_number */) {
    m_algo->process({m_simaps_hits_input(), m_mpgd_hits_input(), m_aclgad_hits_input()},
                    {m_trajectories_output().get(), m_track_parameters_output().get(),
                     m_tracks_output().get(), m_fit_measurements_output().get(),
                     m_predicted_measurements_output().get(),
                     m_filtered_measurements_output().get(),
                     m_smoothed_measurements_output().get(),
                     m_predicted_segments_output().get(),
                     m_filtered_segments_output().get(),
                     m_smoothed_segments_output().get()});
  }
};

} // namespace local_eicrecon
