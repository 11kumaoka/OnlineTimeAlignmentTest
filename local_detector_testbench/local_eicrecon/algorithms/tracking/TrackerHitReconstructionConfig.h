// Origin: EICrecon/src/algorithms/tracking/TrackerHitReconstructionConfig.h
// Source revision: 67a00864dd47c709c98b4afc2c210c3faee100b1
// Local purpose: seven-layer beam-test reconstruction
// Adaptation: adds explicit truth-diagnostic switch, defaulting to normal mode

// SPDX-License-Identifier: LGPL-3.0-or-later
// Copyright (C) 2022 Whitney Armstrong, Sylvester Joosten, Wouter Deconinck, Dmitry Romanov

#pragma once

namespace local_eicrecon {
struct TrackerHitReconstructionConfig {
  float timeResolution = 10;
  bool useTruthPositionForDiagnostics = false;
};
} // namespace local_eicrecon
