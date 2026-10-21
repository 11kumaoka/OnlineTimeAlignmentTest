// Origin: local implementation for seven-layer beam-test framework
// Local purpose: normal truth-independent TrackerHit reconstruction from raw hits only

#pragma once

#include "algorithms/tracking/TrackerHitReconstruction.h"
#include "extensions/jana/JOmniFactory.h"

namespace local_eicrecon {

class LocalTrackerHitReconstructionNoAssoc_factory
  : public JOmniFactory<LocalTrackerHitReconstructionNoAssoc_factory, TrackerHitReconstructionConfig> {

public:
  using AlgoT = local_eicrecon::TrackerHitReconstruction;

private:
  std::unique_ptr<AlgoT> m_algo;
  std::unique_ptr<edm4eic::MCRecoTrackerHitAssociationCollection> m_empty_assocs;

  PodioInput<edm4eic::RawTrackerHit> m_raw_hits_input{this};
  PodioOutput<edm4eic::TrackerHit> m_rec_hits_output{this};

  ParameterRef<float> m_timeResolution{this, "timeResolution", config().timeResolution};

public:
  void Configure() {
    // This factory is explicitly normal mode: never use truth-derived positions.
    config().useTruthPositionForDiagnostics = false;

    m_algo = std::make_unique<AlgoT>(GetPrefix());
    m_algo->level(static_cast<algorithms::LogLevel>(logger()->level()));
    m_algo->applyConfig(config());
    m_algo->init();
    m_empty_assocs = std::make_unique<edm4eic::MCRecoTrackerHitAssociationCollection>();
  }

  void Process(int32_t /* run_number */, uint64_t /* event_number */) {
    m_empty_assocs->clear();
    m_algo->process({m_raw_hits_input(), m_empty_assocs.get()}, {m_rec_hits_output().get()});
  }
};

} // namespace local_eicrecon
