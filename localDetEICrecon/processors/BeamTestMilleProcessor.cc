// Origin: local extension for seven-layer framework
// Local purpose: write official Mille binary records from integrated local rec+track outputs

#include "processors/BeamTestMilleProcessor.h"

#include "BeamTestMilleWriter.h"
#include "services/geometry/dd4hep/DD4hep_service.h"
#include "geometry/SurfacePlacements.h"

#include <JANA/JApplication.h>
#include <JANA/JEvent.h>
#include <edm4eic/Measurement2DCollection.h>
#include <edm4eic/TrackCollection.h>
#include <edm4eic/TrackerHitCollection.h>

#include <algorithm>
#include <cmath>
#include <iostream>
#include <set>
#include <unordered_map>

namespace local_eicrecon {

int BeamTestMilleProcessor::decodeLayer(uint64_t cellid) const {
  return static_cast<int>((cellid >> 11) & ((1ULL << 6) - 1ULL));
}

void BeamTestMilleProcessor::Init() {
  auto* app = GetApplication();
  app->SetDefaultParameter("beamtstreco:milleEnabled", m_enabled,
                           "Enable in-process Mille binary writer from LocalSiMAPSRecHits and LocalBeamTestTracks");
  app->SetDefaultParameter("beamtstreco:milleOutputPath", m_outputPath,
                           "Output path for Mille binary file");
  app->SetDefaultParameter("beamtstreco:milleZRefMm", m_zRefMm,
                           "Reference z for local track parameterization in Mille derivatives");
  app->SetDefaultParameter("beamtstreco:milleSigmaFloorMm", m_sigmaFloorMm,
                           "Minimum measurement uncertainty used for Mille records");
  app->SetDefaultParameter("beamtstreco:milleRequireSingleTrack", m_requireSingleTrack,
                           "Require exactly one selected track per event for Mille writing");
  app->SetDefaultParameter("beamtstreco:milleInjectedShiftLayer", m_injectedShiftLayer,
                           "Optional measurement-stage shift injection layer for Mille closure tests (-1 disables)");
  app->SetDefaultParameter("beamtstreco:milleInjectedShiftXmm", m_injectedShiftXmm,
                           "Optional x shift in mm applied only in Mille measurement writing stage");
  app->SetDefaultParameter("beamtstreco:milleInjectedShiftYmm", m_injectedShiftYmm,
                           "Optional y shift in mm applied only in Mille measurement writing stage");

  if (!m_enabled) {
    std::cerr << "[local_eicrecon] BeamTestMilleProcessor::Init disabled" << std::endl;
    return;
  }

  app->SetDefaultParameter("beamtstreco:milleAlignmentMode",m_alignmentMode,
                           "Mille derivative scope: legacy, validated Rz/Z/Rx/Ry modes or explicit coupled SO(3) modes; old two-axis tilts remain disabled");
  if(m_alignmentMode=="l1_rx_ry" || m_alignmentMode=="l1_l2_rx_ry")
    throw std::runtime_error("Combined Rx/Ry disabled after failed finite-rotation closure; see docs/TILT_ALIGNMENT_VALIDATION.md");
  const bool coupled=m_alignmentMode=="l3_six_dof" || m_alignmentMode=="l1_l2_l3_six_dof" || m_alignmentMode=="l1_rotations" || m_alignmentMode=="l1_l2_rotations" || m_alignmentMode=="l1_six_dof" || m_alignmentMode=="l1_l2_six_dof";
  if (!coupled && m_alignmentMode != "l1_ry" && m_alignmentMode != "l1_rx_ry" && m_alignmentMode != "l1_l2_rx_ry" && m_alignmentMode != "l1_rx" && m_alignmentMode != "legacy" && m_alignmentMode != "l1_rz" && m_alignmentMode != "l1_l2_rz" && m_alignmentMode != "l1_l2_xy_rz" && m_alignmentMode != "l1_z" && m_alignmentMode != "l1_l2_z" && m_alignmentMode != "l1_l2_xyz")
    throw std::runtime_error("Unsupported Mille alignment mode");
  BeamTestMilleWriter::Config cfg;
  if (m_alignmentMode == "l1_rz" || m_alignmentMode == "l1_l2_rz" || m_alignmentMode == "l1_l2_xy_rz") {
    const auto placements = surfacePlacements(*app->GetService<DD4hep_service>()->converter(),false);
    cfg.rotationEnabled[1] = true;
    cfg.rotationEnabled[2] = m_alignmentMode != "l1_rz";
    for (int layer=1; layer<=2; ++layer)
      cfg.pivotMm[layer] = {placements[layer].translation().x(),placements[layer].translation().y()};
  }
  if(m_alignmentMode=="l1_z" || m_alignmentMode=="l1_l2_z" || m_alignmentMode=="l1_l2_xyz") {
    cfg.zEnabled[1]=true;cfg.zEnabled[2]=m_alignmentMode!="l1_z";
  }
  if(coupled || m_alignmentMode=="l1_rx" || m_alignmentMode=="l1_ry" || m_alignmentMode=="l1_rx_ry" || m_alignmentMode=="l1_l2_rx_ry") {
    cfg.tiltMeasurementModel=true;
    cfg.rxEnabled[1]=m_alignmentMode!="l1_ry";
    cfg.ryEnabled[1]=m_alignmentMode!="l1_rx";
    cfg.rxEnabled[2]=cfg.ryEnabled[2]=m_alignmentMode=="l1_l2_rx_ry";
    if(coupled) {
      // Explicit supported SiMAPS scopes; no detector-general inference is implied.
      cfg.rxEnabled.fill(false);cfg.ryEnabled.fill(false);
      const int first=m_alignmentMode=="l3_six_dof"?3:1;
      const int last=(m_alignmentMode=="l3_six_dof" || m_alignmentMode=="l1_l2_l3_six_dof")?3:
        ((m_alignmentMode=="l1_l2_rotations" || m_alignmentMode=="l1_l2_six_dof")?2:1);
      const bool six=m_alignmentMode.find("six_dof")!=std::string::npos;
      for(int layer=first;layer<=last;++layer) {
        cfg.rxEnabled[layer]=cfg.ryEnabled[layer]=cfg.rotationEnabled[layer]=true;
        cfg.zEnabled[layer]=six;
      }
    }
    const auto placements=surfacePlacements(*app->GetService<DD4hep_service>()->converter(),false);
    for(int layer=0;layer<5;++layer)for(int i=0;i<3;++i) {
      cfg.sensitiveCenterMm[layer][i]=placements[layer].translation()[i];
      cfg.surfaceU[layer][i]=placements[layer].linear()(i,0);
      cfg.surfaceV[layer][i]=placements[layer].linear()(i,1);
    }
  }
  cfg.outputPath = m_outputPath;
  cfg.zRefMm = m_zRefMm;
  cfg.doublePrecision = false;
  cfg.writeZeroDerivatives = false;
  m_writer = std::make_unique<BeamTestMilleWriter>(cfg);

  std::cerr << "[local_eicrecon] BeamTestMilleProcessor::Init enabled output=" << m_outputPath
            << " zRefMm=" << m_zRefMm
            << " injectedShiftLayer=" << m_injectedShiftLayer
            << " injectedShiftXmm=" << m_injectedShiftXmm
            << " injectedShiftYmm=" << m_injectedShiftYmm
            << std::endl;
}

void BeamTestMilleProcessor::Process(const std::shared_ptr<const JEvent>& event) {
  if (!m_enabled || !m_writer) {
    return;
  }

  m_events.fetch_add(1, std::memory_order_relaxed);

  auto tracks = event->GetCollection<edm4eic::Track>("LocalBeamTestTracks", false);
  auto recHits = event->GetCollection<edm4eic::TrackerHit>("LocalSiMAPSRecHits", false);
  if (!tracks || tracks->empty() || !recHits) {
    m_eventsNoTrack.fetch_add(1, std::memory_order_relaxed);
    return;
  }

  if (m_requireSingleTrack && tracks->size() != 1) {
    m_eventsAmbiguousTrack.fetch_add(1, std::memory_order_relaxed);
    return;
  }

  const auto& trk = tracks->at(0);

  std::unordered_map<int, std::vector<edm4eic::TrackerHit>> perLayerHits;
  std::set<uint64_t> seenHitKeys;

  auto hitKey = [](const edm4eic::TrackerHit& h) -> uint64_t {
    const auto oid = h.getObjectID();
    return (static_cast<uint64_t>(oid.collectionID) << 32) | static_cast<uint32_t>(oid.index);
  };

  // Use ACTS-associated track measurements to identify hits; reject ambiguity explicitly.
  for (const auto& meas : trk.getMeasurements()) {
    for (const auto& h : meas.getHits()) {
      const auto layer = decodeLayer(static_cast<uint64_t>(h.getCellID()));
      if (layer < 0 || layer > 4) {
        continue;
      }
      const auto key = hitKey(h);
      if (seenHitKeys.insert(key).second) {
        perLayerHits[layer].push_back(h);
      }
    }
  }

  std::array<BeamTestMilleWriter::Hit2D, 5> orderedHits;
  for (int layer = 0; layer < 5; ++layer) {
    auto it = perLayerHits.find(layer);
    if (it == perLayerHits.end() || it->second.empty()) {
      m_eventsMissingLayer.fetch_add(1, std::memory_order_relaxed);
      return;
    }
    if (it->second.size() != 1) {
      m_eventsAmbiguousLayerHit.fetch_add(1, std::memory_order_relaxed);
      return;
    }

    const auto& h = it->second.front();
    const auto pos = h.getPosition();
    const auto err = h.getPositionError();

    BeamTestMilleWriter::Hit2D mh;
    mh.layer = layer;
    mh.x_mm = pos.x;
    mh.y_mm = pos.y;
    mh.z_mm = pos.z;
    mh.sigma_x_mm = std::max(m_sigmaFloorMm, std::sqrt(std::max(0.0, static_cast<double>(err.xx))));
    mh.sigma_y_mm = std::max(m_sigmaFloorMm, std::sqrt(std::max(0.0, static_cast<double>(err.yy))));

    if (m_injectedShiftLayer >= 0 && layer == m_injectedShiftLayer) {
      mh.x_mm += m_injectedShiftXmm;
      mh.y_mm += m_injectedShiftYmm;
    }

    orderedHits[layer] = mh;
  }

  if (m_writer->writeTrackRecord(orderedHits)) {
    m_eventsAccepted.fetch_add(1, std::memory_order_relaxed);
    m_recordsWritten.fetch_add(1, std::memory_order_relaxed);
    m_measurementsWritten.fetch_add(10, std::memory_order_relaxed);
  }
}

void BeamTestMilleProcessor::Finish() {
  if (m_writer) {
    m_writer->flush();
  }

  std::cerr << "[local_eicrecon] BeamTestMilleProcessor::Finish"
            << " enabled=" << (m_enabled ? 1 : 0)
            << " events=" << m_events.load(std::memory_order_relaxed)
            << " accepted=" << m_eventsAccepted.load(std::memory_order_relaxed)
            << " no_track=" << m_eventsNoTrack.load(std::memory_order_relaxed)
            << " ambiguous_track=" << m_eventsAmbiguousTrack.load(std::memory_order_relaxed)
            << " missing_layer=" << m_eventsMissingLayer.load(std::memory_order_relaxed)
            << " ambiguous_layer_hit=" << m_eventsAmbiguousLayerHit.load(std::memory_order_relaxed)
            << " records=" << m_recordsWritten.load(std::memory_order_relaxed)
            << " measurements=" << m_measurementsWritten.load(std::memory_order_relaxed)
            << " output=" << m_outputPath
            << std::endl;
}

} // namespace local_eicrecon
