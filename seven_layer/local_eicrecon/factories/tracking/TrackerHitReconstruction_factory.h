// Origin: EICrecon/src/factories/tracking/TrackerHitReconstruction_factory.h
// Source revision: 67a00864dd47c709c98b4afc2c210c3faee100b1
// Local purpose: seven-layer beam-test reconstruction
// Adaptation: local namespace/factory naming to avoid symbol collisions

// SPDX-License-Identifier: LGPL-3.0-or-later
// Copyright (C) 2023 - 2025 Wouter Deconinck

#pragma once

#include "algorithms/tracking/TrackerHitReconstruction.h"
#include "services/geometry/dd4hep/DD4hep_service.h"
#include "extensions/jana/JOmniFactory.h"

namespace local_eicrecon {

class LocalTrackerHitReconstruction_factory
  : public JOmniFactory<LocalTrackerHitReconstruction_factory, TrackerHitReconstructionConfig> {

public:
  using AlgoT = local_eicrecon::TrackerHitReconstruction;

private:
  std::unique_ptr<AlgoT> m_algo;

  PodioInput<edm4eic::RawTrackerHit> m_raw_hits_input{this};
  PodioInput<edm4eic::MCRecoTrackerHitAssociation> m_raw_hit_assocs_input{this};
  PodioOutput<edm4eic::TrackerHit> m_rec_hits_output{this};

  ParameterRef<float> m_timeResolution{this, "timeResolution", config().timeResolution};
  ParameterRef<bool> m_useTruthPositionForDiagnostics{
      this, "useTruthPositionForDiagnostics", config().useTruthPositionForDiagnostics};

  Service<DD4hep_service> m_geoSvc{this};

public:
  void Configure() {
    m_algo = std::make_unique<AlgoT>(GetPrefix());
    m_algo->level(static_cast<algorithms::LogLevel>(logger()->level()));
    m_algo->applyConfig(config());
    m_algo->init();
  }

  void Process(int32_t /* run_number */, uint64_t /* event_number */) {
    m_algo->process({m_raw_hits_input(), m_raw_hit_assocs_input()}, {m_rec_hits_output().get()});
  }
};

} // namespace local_eicrecon
