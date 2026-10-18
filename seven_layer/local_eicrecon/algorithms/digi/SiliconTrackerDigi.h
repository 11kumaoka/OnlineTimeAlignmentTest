// Origin: EICrecon/src/algorithms/digi/SiliconTrackerDigi.h
// Source revision: 67a00864dd47c709c98b4afc2c210c3faee100b1
// Local purpose: seven-layer beam-test reconstruction
// Adaptation: local namespace/plugin wiring; behavior aligned with upstream SiliconTrackerDigi

// SPDX-License-Identifier: LGPL-3.0-or-later
// Copyright (C) 2022 Whitney Armstrong, Wouter Deconinck, Sylvester Joosten, Dmitry Romanov

#pragma once

#include <algorithms/algorithm.h>
#include <edm4eic/MCRecoTrackerHitAssociationCollection.h>
#include <edm4eic/MCRecoTrackerHitLinkCollection.h>
#include <edm4eic/RawTrackerHitCollection.h>
#include <edm4hep/EventHeaderCollection.h>
#include <edm4hep/SimTrackerHitCollection.h>
#include <string>
#include <string_view>

#include "SiliconTrackerDigiConfig.h"
#include "algorithms/interfaces/UniqueIDGenSvc.h"
#include "algorithms/interfaces/WithPodConfig.h"

namespace local_eicrecon {

using SiliconTrackerDigiAlgorithm = algorithms::Algorithm<
    algorithms::Input<edm4hep::EventHeaderCollection, edm4hep::SimTrackerHitCollection>,
    algorithms::Output<edm4eic::RawTrackerHitCollection, edm4eic::MCRecoTrackerHitLinkCollection,
                       edm4eic::MCRecoTrackerHitAssociationCollection>>;

class SiliconTrackerDigi : public SiliconTrackerDigiAlgorithm,
                           public eicrecon::WithPodConfig<SiliconTrackerDigiConfig> {

public:
  SiliconTrackerDigi(std::string_view name)
      : SiliconTrackerDigiAlgorithm{
            name,
            {"eventHeaderCollection", "inputHitCollection"},
            {"outputRawHitCollection", "outputHitLinks", "outputHitAssociations"},
            "Apply threshold, digitize within ADC range, "
            "convert time with smearing resolution."} {}

  void init() final;
  void process(const Input&, const Output&) const final;

private:
  const algorithms::UniqueIDGenSvc& m_uid = algorithms::UniqueIDGenSvc::instance();
};

} // namespace local_eicrecon
