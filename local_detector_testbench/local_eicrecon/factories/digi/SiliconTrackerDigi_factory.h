// Origin: EICrecon/src/factories/digi/SiliconTrackerDigi_factory.h
// Source revision: 67a00864dd47c709c98b4afc2c210c3faee100b1
// Local purpose: seven-layer beam-test reconstruction
// Adaptation: local namespace/factory naming to avoid symbol collisions

// SPDX-License-Identifier: LGPL-3.0-or-later
// Copyright (C) 2023 Wouter Deconinck

#pragma once

#include <edm4eic/EDM4eicVersion.h>
#include "algorithms/digi/SiliconTrackerDigi.h"
#include "services/algorithms_init/AlgorithmsInit_service.h"
#include "extensions/jana/JOmniFactory.h"

namespace local_eicrecon {

class LocalSiliconTrackerDigi_factory
  : public JOmniFactory<LocalSiliconTrackerDigi_factory, SiliconTrackerDigiConfig> {

public:
  using AlgoT = local_eicrecon::SiliconTrackerDigi;

private:
  std::unique_ptr<AlgoT> m_algo;

  PodioInput<edm4hep::EventHeader> m_event_headers_input{this};
  PodioInput<edm4hep::SimTrackerHit> m_sim_hits_input{this};

  PodioOutput<edm4eic::RawTrackerHit> m_raw_hits_output{this};
  PodioOutput<edm4eic::MCRecoTrackerHitLink> m_links_output{this};
  PodioOutput<edm4eic::MCRecoTrackerHitAssociation> m_assoc_output{this};

  ParameterRef<double> m_threshold{this, "threshold", config().threshold};
  ParameterRef<double> m_timeResolution{this, "timeResolution", config().timeResolution};

public:
  void Configure() {
    m_algo = std::make_unique<AlgoT>(GetPrefix());
    m_algo->level(static_cast<algorithms::LogLevel>(logger()->level()));
    m_algo->applyConfig(config());
    m_algo->init();
  }

  void Process(int32_t /* run_number */, uint64_t /* event_number */) {
    m_algo->process({m_event_headers_input(), m_sim_hits_input()},
                    {m_raw_hits_output().get(), m_links_output().get(), m_assoc_output().get()});
  }
};

} // namespace local_eicrecon
