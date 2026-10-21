// Origin: EICrecon/src/algorithms/tracking/TrackerHitReconstruction.h
// Source revision: 67a00864dd47c709c98b4afc2c210c3faee100b1
// Local purpose: seven-layer beam-test reconstruction
// Adaptation: optional truth-diagnostic pathway retained only for explicit debug mode

// SPDX-License-Identifier: LGPL-3.0-or-later
// Copyright (C) 2022 - 2025 Whitney Armstrong, Sylvester Joosten, Wouter Deconinck, Dmitry Romanov

#pragma once

#include <DDRec/CellIDPositionConverter.h>
#include <algorithms/algorithm.h>
#include <algorithms/geo.h>
#include <edm4eic/MCRecoTrackerHitAssociationCollection.h>
#include <edm4eic/RawTrackerHitCollection.h>
#include <edm4eic/TrackerHitCollection.h>
#include <gsl/pointers>
#include <string>
#include <string_view>

#include "TrackerHitReconstructionConfig.h"
#include "algorithms/interfaces/WithPodConfig.h"

namespace local_eicrecon {

using TrackerHitReconstructionAlgorithm =
  algorithms::Algorithm<algorithms::Input<edm4eic::RawTrackerHitCollection,
                      edm4eic::MCRecoTrackerHitAssociationCollection>,
                          algorithms::Output<edm4eic::TrackerHitCollection>>;

/**
 * Produces edm4eic::TrackerHit with geometric info from edm4eic::RawTrackerHit
 */
class TrackerHitReconstruction : public TrackerHitReconstructionAlgorithm,
                                 public eicrecon::WithPodConfig<TrackerHitReconstructionConfig> {

public:
  TrackerHitReconstruction(std::string_view name)
      : TrackerHitReconstructionAlgorithm{
        name, {"inputRawHits", "inputRawHitAssociations"}, {"outputHits"},
        "reconstruct raw hits into tracker hits."} {}

  /// Once in a lifetime initialization
  void init() final {};

  /// Processes RawTrackerHit and produces a TrackerHit
  void process(const Input&, const Output&) const final;

private:
  const algorithms::GeoSvc& m_geo{algorithms::GeoSvc::instance()};
  const dd4hep::rec::CellIDPositionConverter* m_converter{m_geo.cellIDPositionConverter()};
};

} // namespace local_eicrecon
