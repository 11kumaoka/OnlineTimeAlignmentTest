// Origin: local extension for seven-layer framework
// Local purpose: write official Mille Binary records from Hit Reconstruction and Track Fitting outputs

#pragma once

#include <JANA/JEventProcessor.h>

#include "BeamTestMilleWriter.h"

#include <array>
#include <atomic>
#include <cstdint>
#include <memory>
#include <string>

namespace local_eicrecon {

class BeamTestMilleProcessor : public JEventProcessor {
public:
  BeamTestMilleProcessor() { SetTypeName(NAME_OF_THIS); }

  void Init() override;
  void Process(const std::shared_ptr<const JEvent>& event) override;
  void Finish() override;

private:
  int decodeLayer(uint64_t cellid) const;

  bool m_enabled{false};
  std::string m_outputPath{"results/manual/mille.dat"};
  double m_zRefMm{100.0};
  double m_sigmaFloorMm{0.005};
  bool m_requireSingleTrack{true};
  int m_injectedShiftLayer{-1};
  double m_injectedShiftXmm{0.0};
  double m_injectedShiftYmm{0.0};

  std::unique_ptr<BeamTestMilleWriter> m_writer;

  std::atomic<uint64_t> m_events{0};
  std::atomic<uint64_t> m_eventsAccepted{0};
  std::atomic<uint64_t> m_eventsNoTrack{0};
  std::atomic<uint64_t> m_eventsAmbiguousTrack{0};
  std::atomic<uint64_t> m_eventsMissingLayer{0};
  std::atomic<uint64_t> m_eventsAmbiguousLayerHit{0};
  std::atomic<uint64_t> m_recordsWritten{0};
  std::atomic<uint64_t> m_measurementsWritten{0};
};

} // namespace local_eicrecon
