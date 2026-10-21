// Origin: local extension for seven-layer framework
// Local purpose: event-level monitoring for local reconstruction outputs

#include "processors/BeamTestEventProcessor.h"

#include <JANA/JEvent.h>
#include <edm4eic/RawTrackerHitCollection.h>
#include <edm4eic/Measurement2DCollection.h>
#include <edm4eic/TrackCollection.h>
#include <edm4eic/TrackerHitCollection.h>
#include <edm4eic/TrajectoryCollection.h>
#include <iostream>
#include <set>

namespace local_eicrecon {

void BeamTestEventProcessor::Init() {
  std::cerr << "[local_eicrecon] BeamTestEventProcessor::Init" << std::endl;
}

void BeamTestEventProcessor::Process(const std::shared_ptr<const JEvent>& event) {
  auto n_raw = [&](const char* tag) -> uint64_t {
    auto coll = event->GetCollection<edm4eic::RawTrackerHit>(tag, false);
    return coll ? static_cast<uint64_t>(coll->size()) : 0ULL;
  };
  auto n_rec = [&](const char* tag) -> uint64_t {
    auto coll = event->GetCollection<edm4eic::TrackerHit>(tag, false);
    return coll ? static_cast<uint64_t>(coll->size()) : 0ULL;
  };

  const auto simaps_raw = n_raw("LocalSiMAPSRawHits");
  const auto simaps_rec = n_rec("LocalSiMAPSRecHits");
  const auto mpgd_raw = n_raw("LocalMPGDRawHits");
  const auto mpgd_rec = n_rec("LocalMPGDRecHits");
  const auto aclgad_raw = n_raw("LocalACLGADRawHits");
  const auto aclgad_rec = n_rec("LocalACLGADRecHits");

  auto tracks = event->GetCollection<edm4eic::Track>("LocalBeamTestTracks", false);
  auto trajectories = event->GetCollection<edm4eic::Trajectory>("LocalBeamTestTrajectories", false);
  auto fit_measurements = event->GetCollection<edm4eic::Measurement2D>("LocalBeamTestFitMeasurements", false);

  uint64_t n_tracks = tracks ? static_cast<uint64_t>(tracks->size()) : 0ULL;
  uint64_t n_traj = trajectories ? static_cast<uint64_t>(trajectories->size()) : 0ULL;

  uint64_t traj_nmeas_sum = 0;
  uint64_t nmeas5 = 0;
  uint64_t nmeas6plus = 0;
  uint64_t unique_surface_ok = 0;
  uint64_t unique_surface_bad = 0;
  double chi2_sum_evt = 0.0;
  double ndf_sum_evt = 0.0;
  double classical_ndf_sum_evt = 0.0;

  if (tracks) {
    for (const auto& trk : *tracks) {
      chi2_sum_evt += trk.getChi2();
      ndf_sum_evt += trk.getNdf();

      std::set<std::uint64_t> surfaces;
      for (const auto& m : trk.getMeasurements()) {
        surfaces.insert(m.getSurface());
      }
      if (trk.measurements_size() > 0 && surfaces.size() == trk.measurements_size()) {
        ++unique_surface_ok;
      } else {
        ++unique_surface_bad;
      }
    }
  }

  if (trajectories) {
    for (const auto& traj : *trajectories) {
      auto nmeas = static_cast<uint64_t>(traj.getNMeasurements());
      traj_nmeas_sum += nmeas;
      if (nmeas == 5) {
        ++nmeas5;
      }
      if (nmeas >= 6) {
        ++nmeas6plus;
      }
      classical_ndf_sum_evt += static_cast<double>(std::max<int>(0, static_cast<int>(2 * nmeas) - 4));
    }
  }

  m_events.fetch_add(1, std::memory_order_relaxed);
  m_simaps_raw_total.fetch_add(simaps_raw, std::memory_order_relaxed);
  m_simaps_rec_total.fetch_add(simaps_rec, std::memory_order_relaxed);
  m_mpgd_raw_total.fetch_add(mpgd_raw, std::memory_order_relaxed);
  m_mpgd_rec_total.fetch_add(mpgd_rec, std::memory_order_relaxed);
  m_aclgad_raw_total.fetch_add(aclgad_raw, std::memory_order_relaxed);
  m_aclgad_rec_total.fetch_add(aclgad_rec, std::memory_order_relaxed);
  m_tracks_total.fetch_add(n_tracks, std::memory_order_relaxed);
  if (n_tracks > 0) {
    m_events_with_tracks.fetch_add(1, std::memory_order_relaxed);
  } else {
    m_events_without_tracks.fetch_add(1, std::memory_order_relaxed);
  }
  m_traj_nmeas_total.fetch_add(traj_nmeas_sum, std::memory_order_relaxed);
  m_traj_nmeas_5.fetch_add(nmeas5, std::memory_order_relaxed);
  m_traj_nmeas_6plus.fetch_add(nmeas6plus, std::memory_order_relaxed);
  m_tracks_unique_surface_ok.fetch_add(unique_surface_ok, std::memory_order_relaxed);
  m_tracks_unique_surface_bad.fetch_add(unique_surface_bad, std::memory_order_relaxed);
  m_chi2_sum.fetch_add(chi2_sum_evt, std::memory_order_relaxed);
  m_ndf_sum.fetch_add(ndf_sum_evt, std::memory_order_relaxed);
  m_classical_ndf_sum.fetch_add(classical_ndf_sum_evt, std::memory_order_relaxed);

  auto ev = m_events.load(std::memory_order_relaxed);
  if (ev <= 3) {
    std::cerr << "[local_eicrecon] BeamTestEventProcessor::Process event=" << ev
              << " simaps(raw/rec)=" << simaps_raw << "/" << simaps_rec
              << " mpgd(raw/rec)=" << mpgd_raw << "/" << mpgd_rec
              << " aclgad(raw/rec)=" << aclgad_raw << "/" << aclgad_rec
              << " tracks/traj=" << n_tracks << "/" << n_traj
              << " fit_meas=" << (fit_measurements ? fit_measurements->size() : 0)
              << " traj_nmeas_sum=" << traj_nmeas_sum
              << std::endl;
  }
}

void BeamTestEventProcessor::Finish() {
  const auto ev = m_events.load(std::memory_order_relaxed);
  std::cerr << "[local_eicrecon] BeamTestEventProcessor::Finish events=" << ev
            << " simaps(raw/rec)=" << m_simaps_raw_total.load(std::memory_order_relaxed)
            << "/" << m_simaps_rec_total.load(std::memory_order_relaxed)
            << " mpgd(raw/rec)=" << m_mpgd_raw_total.load(std::memory_order_relaxed)
            << "/" << m_mpgd_rec_total.load(std::memory_order_relaxed)
            << " aclgad(raw/rec)=" << m_aclgad_raw_total.load(std::memory_order_relaxed)
            << "/" << m_aclgad_rec_total.load(std::memory_order_relaxed)
            << " tracks_total=" << m_tracks_total.load(std::memory_order_relaxed)
            << " events_with_tracks=" << m_events_with_tracks.load(std::memory_order_relaxed)
            << " events_without_tracks=" << m_events_without_tracks.load(std::memory_order_relaxed)
            << " traj_nmeas_total=" << m_traj_nmeas_total.load(std::memory_order_relaxed)
            << " traj_nmeas_5=" << m_traj_nmeas_5.load(std::memory_order_relaxed)
            << " traj_nmeas_6plus=" << m_traj_nmeas_6plus.load(std::memory_order_relaxed)
            << " tracks_unique_surface_ok=" << m_tracks_unique_surface_ok.load(std::memory_order_relaxed)
            << " tracks_unique_surface_bad=" << m_tracks_unique_surface_bad.load(std::memory_order_relaxed)
            << " chi2_sum=" << m_chi2_sum.load(std::memory_order_relaxed)
            << " ndf_sum=" << m_ndf_sum.load(std::memory_order_relaxed)
            << " classical_ndf_sum=" << m_classical_ndf_sum.load(std::memory_order_relaxed)
            << std::endl;
}

} // namespace local_eicrecon
