// Origin: local extension for seven-layer framework
// Local purpose: event-level monitoring for local reconstruction outputs

#pragma once

#include <JANA/JEventProcessor.h>
#include <atomic>
#include <cstdint>

namespace local_eicrecon {

class BeamTestEventProcessor : public JEventProcessor {
public:
  BeamTestEventProcessor() { SetTypeName(NAME_OF_THIS); }

  void Init() override;
  void Process(const std::shared_ptr<const JEvent>& event) override;
  void Finish() override;

private:
  std::atomic<uint64_t> m_events{0};
  std::atomic<uint64_t> m_simaps_raw_total{0};
  std::atomic<uint64_t> m_simaps_rec_total{0};
  std::atomic<uint64_t> m_mpgd_raw_total{0};
  std::atomic<uint64_t> m_mpgd_rec_total{0};
  std::atomic<uint64_t> m_aclgad_raw_total{0};
  std::atomic<uint64_t> m_aclgad_rec_total{0};
  std::atomic<uint64_t> m_tracks_total{0};
  std::atomic<uint64_t> m_events_with_tracks{0};
  std::atomic<uint64_t> m_events_without_tracks{0};
  std::atomic<uint64_t> m_traj_nmeas_total{0};
  std::atomic<uint64_t> m_traj_nmeas_5{0};
  std::atomic<uint64_t> m_traj_nmeas_6plus{0};
  std::atomic<double> m_chi2_sum{0.0};
  std::atomic<double> m_ndf_sum{0.0};
  std::atomic<double> m_classical_ndf_sum{0.0};
  std::atomic<uint64_t> m_tracks_unique_surface_ok{0};
  std::atomic<uint64_t> m_tracks_unique_surface_bad{0};
};

} // namespace local_eicrecon
