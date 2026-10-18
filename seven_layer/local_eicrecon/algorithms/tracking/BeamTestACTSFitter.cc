// Origin: refactored from seven_layer/standalone_acts/src/standalone_acts_fit.cpp
// Source revision: local workspace 2026-10-16
// Local purpose: run ACTS fitting in-process inside JANA2 / local_eicrecon plugin
// Adaptation: algorithm interface for local JOmniFactory and EDM4eic outputs

#include "algorithms/tracking/BeamTestACTSFitter.h"

#include <Acts/Definitions/Algebra.hpp>
#include <Acts/TrackFitting/GainMatrixSmoother.hpp>
#include <Acts/TrackFitting/GainMatrixUpdater.hpp>
#include <edm4eic/Cov2f.h>
#include <edm4eic/Cov3f.h>
#include <edm4eic/Cov6f.h>
#include <edm4eic/TrackPoint.h>
#include <edm4hep/Vector2f.h>
#include <edm4hep/Vector3f.h>
#include <edm4hep/utils/vector_utils.h>

#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <set>
#include <unordered_map>

namespace local_eicrecon {

namespace {

double sqr(double x) { return x * x; }

edm4eic::Cov3f makeCov3(float c00, float c11, float ctt) {
  return edm4eic::Cov3f(c00, c11, ctt, 0.0f, 0.0f, 0.0f);
}

} // namespace

BeamTestACTSFitter::BeamTestACTSFitter(std::string_view name)
    : BeamTestACTSFitterAlgorithm{
          name,
          {"inputSiMAPSHits", "inputMPGDHits", "inputACLGADHits"},
          {"outputTrajectories", "outputTrackParameters", "outputTracks",
           "outputFitMeasurements", "outputPredictedMeasurements", "outputFilteredMeasurements",
           "outputSmoothedMeasurements", "outputPredictedSegments", "outputFilteredSegments",
           "outputSmoothedSegments"},
          "In-process ACTS beam-test fitting from local reconstructed TrackerHits"} {}

const Acts::Surface* BeamTestACTSFitter::SurfaceAccessor::operator()(const Acts::SourceLink& sl) const {
  const auto& fsl = sl.get<FitSourceLink>();
  const auto it = map->find(fsl.geometryId().value());
  if (it == map->end()) {
    return nullptr;
  }
  return it->second;
}

void BeamTestACTSFitter::Calibrator::calibrate(const Acts::GeometryContext&, const Acts::CalibrationContext&,
                                               const Acts::SourceLink& sl,
                                               Acts::VectorMultiTrajectory::TrackStateProxy trackState) const {
  const auto& fsl = sl.get<FitSourceLink>();
  const auto& m = measurements->at(fsl.index);
  trackState.setUncalibratedSourceLink(Acts::SourceLink{sl});
  trackState.allocateCalibrated(m.loc, m.cov);
  std::array<uint8_t, 2> idx = {static_cast<uint8_t>(Acts::eBoundLoc0),
                                static_cast<uint8_t>(Acts::eBoundLoc1)};
  trackState.setProjectorSubspaceIndices(idx);
}

int BeamTestACTSFitter::decodeLayer(uint64_t cellid) {
  return static_cast<int>((cellid >> 11) & ((1ULL << 6) - 1ULL));
}

std::optional<BeamTestACTSFitter::LayerHit>
BeamTestACTSFitter::pickRepresentative(const std::vector<LayerHit>& hits) {
  if (hits.size() != 1) {
    return std::nullopt;
  }
  return hits.front();
}

bool BeamTestACTSFitter::inferGlobalCoordsFromZ(const std::array<std::vector<LayerHit>, 5>& simaps) const {
  int checked = 0;
  int matchGlobal = 0;
  for (int l = 0; l < 5; ++l) {
    if (simaps[l].empty()) {
      continue;
    }
    ++checked;
    double meanz = 0.0;
    for (const auto& h : simaps[l]) {
      meanz += h.z;
    }
    meanz /= static_cast<double>(simaps[l].size());
    if (std::abs(meanz - m_zmm[l]) < 5.0) {
      ++matchGlobal;
    }
  }
  if (checked == 0) {
    return m_cfg.inputHitsAreGlobal;
  }
  // Use explicit configuration as primary policy; keep this check only as sanity for warnings.
  return m_cfg.inputHitsAreGlobal;
}

void BeamTestACTSFitter::init() {
  m_surfaces.clear();
  m_surfaceMap.clear();
  m_surfaceSequence.clear();

  m_surfaces.reserve(7);
  m_surfaceSequence.reserve(7);

  for (int i = 0; i < 7; ++i) {
    Acts::Transform3 tr = Acts::Transform3::Identity();
    tr.translation() = Acts::Vector3(0.0, 0.0, m_zmm[i] * Acts::UnitConstants::mm);
    auto bounds = std::make_shared<const Acts::RectangleBounds>(
        m_halfXmm * Acts::UnitConstants::mm, m_halfYmm * Acts::UnitConstants::mm);
    auto s = Acts::Surface::makeShared<Acts::PlaneSurface>(tr, bounds);
    auto gid = Acts::GeometryIdentifier().withVolume(1).withLayer(i + 1).withSensitive(1);
    s->assignGeometryId(gid);
    m_surfaceMap.emplace(gid.value(), s.get());
    m_surfaceSequence.push_back(s.get());
    m_surfaces.push_back(std::move(s));
  }

  m_bfield = std::make_shared<Acts::ConstantBField>(Acts::Vector3(0.0, 0.0, 0.0));

  Stepper stepper(m_bfield);
  Navigator navigator;
  Propagator propagator(std::move(stepper), std::move(navigator));
  auto logger = Acts::getDefaultLogger("LocalBeamTestACTS", Acts::Logging::INFO);
  m_fitter = std::make_unique<Fitter>(std::move(propagator), logger->clone("LocalBeamTestKF"));

  std::cerr << "[local_eicrecon] BeamTestACTSFitter::init surfaces=7 useMPGD="
            << (m_cfg.useMPGD ? 1 : 0)
            << " useACLGAD=" << (m_cfg.useACLGAD ? 1 : 0)
            << " inputHitsAreGlobal=" << (m_cfg.inputHitsAreGlobal ? 1 : 0)
            << " useMuonHypothesis=" << (m_cfg.useMuonHypothesis ? 1 : 0)
            << " outputTrackPDG=" << m_cfg.outputTrackPDG
            << " seedQOverP=" << m_cfg.seedQOverP
            << " excludeLayerFromFit=" << m_cfg.excludeLayerFromFit
            << " shiftLayer=" << m_cfg.alignmentTestShiftLayer
            << " shiftXmm=" << m_cfg.alignmentTestShiftXmm
            << std::endl;
}

std::optional<BeamTestACTSFitter::FitResultBundle>
BeamTestACTSFitter::fitSelected(const std::vector<LayerHit>& selected, bool useGlobalCoords) const {
  FitResultBundle bundle;
  auto& out = bundle.summary;

  if (selected.size() < 2) {
    out.error = "insufficient selected hits";
    return bundle;
  }

  std::vector<FitMeas> measData;
  std::vector<Acts::SourceLink> sourceLinks;
  std::vector<Acts::Vector3> seedPoints;
  std::vector<const Acts::Surface*> fitSurfaces;
  measData.reserve(selected.size());
  sourceLinks.reserve(selected.size());
  seedPoints.reserve(selected.size());
  fitSurfaces.reserve(selected.size());

  std::vector<LayerHit> ordered = selected;
  std::sort(ordered.begin(), ordered.end(), [](const LayerHit& a, const LayerHit& b) {
    return a.layer < b.layer;
  });

  for (const auto& h : ordered) {
    if (h.layer < 0 || h.layer >= static_cast<int>(m_surfaceSequence.size())) {
      out.error = "layer index out of range";
      return bundle;
    }
    const auto* surf = m_surfaceSequence[h.layer];

    FitMeas m;
    if (useGlobalCoords) {
      const Acts::Vector3 gpos(h.x * Acts::UnitConstants::mm,
                               h.y * Acts::UnitConstants::mm,
                               h.z * Acts::UnitConstants::mm);
      const Acts::Vector3 refDir(0.0, 0.0, 1.0);
      auto lres = surf->globalToLocal(m_gctx, gpos, refDir, 5.0 * Acts::UnitConstants::mm);
      if (!lres.ok()) {
        out.error = "globalToLocal failed";
        return bundle;
      }
      m.loc = lres.value();
      seedPoints.emplace_back(gpos);
    } else {
      m.loc[0] = h.x * Acts::UnitConstants::mm;
      m.loc[1] = h.y * Acts::UnitConstants::mm;
      seedPoints.emplace_back(m.loc[0], m.loc[1], m_zmm[h.layer] * Acts::UnitConstants::mm);
    }

    const double sx2 = std::max(1e-8, static_cast<double>(h.exx)) * sqr(Acts::UnitConstants::mm);
    const double sy2 = std::max(1e-8, static_cast<double>(h.eyy)) * sqr(Acts::UnitConstants::mm);
    m.cov(0, 0) = sx2;
    m.cov(1, 1) = sy2;
    m.cov(0, 1) = 0.0;
    m.cov(1, 0) = 0.0;

    const std::size_t idx = measData.size();
    measData.push_back(m);
    sourceLinks.emplace_back(FitSourceLink{surf->geometryId(), idx});
    fitSurfaces.push_back(surf);
  }

  const auto& p0 = seedPoints.front();
  const auto& pN = seedPoints.back();
  Acts::Vector3 dir = (pN - p0).normalized();
  Acts::Vector3 seedPos = p0 - 10.0 * Acts::UnitConstants::mm * dir;

  Acts::BoundMatrix seedCov = Acts::BoundMatrix::Zero();
  seedCov(Acts::eBoundLoc0, Acts::eBoundLoc0) = sqr(1.0 * Acts::UnitConstants::mm);
  seedCov(Acts::eBoundLoc1, Acts::eBoundLoc1) = sqr(1.0 * Acts::UnitConstants::mm);
  seedCov(Acts::eBoundPhi, Acts::eBoundPhi) = 1e-3;
  seedCov(Acts::eBoundTheta, Acts::eBoundTheta) = 1e-3;
  seedCov(Acts::eBoundQOverP, Acts::eBoundQOverP) = 1e-4;
  seedCov(Acts::eBoundTime, Acts::eBoundTime) = sqr(m_cfg.timeResolution * Acts::UnitConstants::ns);

  const double qOverP = m_cfg.seedQOverP / Acts::UnitConstants::GeV;
  Acts::Vector4 pos4(seedPos.x(), seedPos.y(), seedPos.z(), 0.0);
  auto particleHypothesis = m_cfg.useMuonHypothesis ? Acts::ParticleHypothesis::muon()
                                                     : Acts::ParticleHypothesis::pion();
  auto seed = Acts::BoundTrackParameters::createCurvilinear(
      pos4, dir, qOverP, seedCov, particleHypothesis);

  SurfaceAccessor surfaceAccessor{&m_surfaceMap};
  Calibrator calibrator{&measData};
  Acts::GainMatrixUpdater updater;
  Acts::GainMatrixSmoother smoother;

  Acts::KalmanFitterExtensions<Traj> ext;
  ext.surfaceAccessor.connect<&SurfaceAccessor::operator()>(&surfaceAccessor);
  ext.calibrator.template connect<&Calibrator::calibrate>(&calibrator);
  ext.updater.template connect<&Acts::GainMatrixUpdater::operator()<Traj>>(&updater);
  ext.smoother.template connect<&Acts::GainMatrixSmoother::operator()<Traj>>(&smoother);

  Acts::PropagatorPlainOptions pOptions(m_gctx, m_mctx);
  pOptions.maxSteps = 10000;

  Acts::KalmanFitterOptions<Traj> fitOptions(m_gctx, m_mctx, std::cref(m_cctx), ext, pOptions,
                                             fitSurfaces.front(), false, false, false, 1.0,
                                             Acts::FreeToBoundCorrection(false));

  auto tc = std::make_shared<Acts::VectorTrackContainer>();
  auto tm = std::make_shared<Acts::VectorMultiTrajectory>();
  TrackContainer tracks(tc, tm);

  auto fitResult = m_fitter->fit(sourceLinks.begin(), sourceLinks.end(), seed, fitOptions,
                                 fitSurfaces, tracks);

  if (!fitResult.ok()) {
    out.error = fitResult.error().message();
    return bundle;
  }

  auto trk = fitResult.value();
  out.ok = true;
  out.nMeasurements = static_cast<int>(trk.nMeasurements());
  out.nStates = static_cast<int>(trk.nTrackStates());
  out.nOutliers = static_cast<int>(trk.nOutliers());
  out.nHoles = static_cast<int>(trk.nHoles());
  out.nSharedHits = static_cast<int>(trk.nSharedHits());
  out.chi2 = trk.chi2();
  out.ndf = trk.nDoF();
  out.chi2ndf = (out.ndf > 0.0) ? out.chi2 / out.ndf : -1.0;
  out.loc0_mm = trk.loc0() / Acts::UnitConstants::mm;
  out.loc1_mm = trk.loc1() / Acts::UnitConstants::mm;
  out.phi = trk.phi();
  out.theta = trk.theta();
  out.qOverP = trk.qOverP() * Acts::UnitConstants::GeV;
  out.time_ns = trk.time() / Acts::UnitConstants::ns;
  out.pGeV = trk.absoluteMomentum() / Acts::UnitConstants::GeV;
  out.covariance = trk.covariance();
  out.dirx = std::cos(out.phi) * std::sin(out.theta);
  out.diry = std::sin(out.phi) * std::sin(out.theta);
  out.dirz = std::cos(out.theta);

  std::unordered_map<std::size_t, int> idxToLayer;
  for (std::size_t i = 0; i < ordered.size(); ++i) {
    idxToLayer[i] = ordered[i].layer;
  }

  for (const auto& state : trk.trackStatesReversed()) {
    if (!state.hasUncalibratedSourceLink()) {
      continue;
    }

    StateDiag d;
    d.surface = state.referenceSurface().geometryId().value();

    const auto& fsl = state.getUncalibratedSourceLink().template get<FitSourceLink>();
    d.sourceIndex = fsl.index;

    auto itLayer = idxToLayer.find(d.sourceIndex);
    d.layer = (itLayer != idxToLayer.end()) ? itLayer->second : -1;

    if (d.sourceIndex < measData.size()) {
      d.hasMeasurement = true;
      d.measLoc = measData[d.sourceIndex].loc;
      d.measCov = measData[d.sourceIndex].cov;
    }

    if (state.hasPredicted()) {
      d.hasPredicted = true;
      const auto& pred = state.predicted();
      d.predLoc[0] = pred[Acts::eBoundLoc0];
      d.predLoc[1] = pred[Acts::eBoundLoc1];
      const auto& predCov = state.predictedCovariance();
      d.predCov(0, 0) = predCov(Acts::eBoundLoc0, Acts::eBoundLoc0);
      d.predCov(1, 1) = predCov(Acts::eBoundLoc1, Acts::eBoundLoc1);
      d.predCov(0, 1) = predCov(Acts::eBoundLoc0, Acts::eBoundLoc1);
      d.predCov(1, 0) = predCov(Acts::eBoundLoc1, Acts::eBoundLoc0);
    }

    if (state.hasFiltered()) {
      d.hasFiltered = true;
      const auto& filt = state.filtered();
      d.filtLoc[0] = filt[Acts::eBoundLoc0];
      d.filtLoc[1] = filt[Acts::eBoundLoc1];
      d.time_ns = static_cast<float>(filt[Acts::eBoundTime] / Acts::UnitConstants::ns);
      const auto& filtCov = state.filteredCovariance();
      d.filtCov(0, 0) = filtCov(Acts::eBoundLoc0, Acts::eBoundLoc0);
      d.filtCov(1, 1) = filtCov(Acts::eBoundLoc1, Acts::eBoundLoc1);
      d.filtCov(0, 1) = filtCov(Acts::eBoundLoc0, Acts::eBoundLoc1);
      d.filtCov(1, 0) = filtCov(Acts::eBoundLoc1, Acts::eBoundLoc0);
    }

    if (state.hasSmoothed()) {
      d.hasSmoothed = true;
      const auto& smooth = state.smoothed();
      d.smoothLoc[0] = smooth[Acts::eBoundLoc0];
      d.smoothLoc[1] = smooth[Acts::eBoundLoc1];
      const auto& smoothCov = state.smoothedCovariance();
      d.smoothCov(0, 0) = smoothCov(Acts::eBoundLoc0, Acts::eBoundLoc0);
      d.smoothCov(1, 1) = smoothCov(Acts::eBoundLoc1, Acts::eBoundLoc1);
      d.smoothCov(0, 1) = smoothCov(Acts::eBoundLoc0, Acts::eBoundLoc1);
      d.smoothCov(1, 0) = smoothCov(Acts::eBoundLoc1, Acts::eBoundLoc0);
    }

    if (d.hasMeasurement && d.hasPredicted) {
      d.residualPred = d.measLoc - d.predLoc;
    }
    if (d.hasMeasurement && d.hasFiltered) {
      d.residualFilt = d.measLoc - d.filtLoc;
    }
    if (d.hasMeasurement && d.hasSmoothed) {
      d.residualSmooth = d.measLoc - d.smoothLoc;
    }

    bundle.states.push_back(d);
  }

  return bundle;
}

void BeamTestACTSFitter::process(const Input& input, const Output& output) const {
  const auto [simapsHits, mpgdHits, aclgadHits] = input;
  auto [trajectories, trackParameters, tracks,
        fitMeasurements, predictedMeasurements, filteredMeasurements,
      smoothedMeasurements, predictedSegments, filteredSegments,
      smoothedSegments] = output;

  std::array<std::vector<LayerHit>, 5> perLayer;
  std::array<std::vector<edm4eic::TrackerHit>, 5> perLayerHitObj;

  for (const auto& h : *simapsHits) {
    const int layer = decodeLayer(static_cast<uint64_t>(h.getCellID()));
    if (layer < 0 || layer > 4) {
      continue;
    }
    LayerHit lh;
    lh.layer = layer;
    lh.x = h.getPosition().x;
    lh.y = h.getPosition().y;
    lh.z = h.getPosition().z;
    lh.exx = h.getPositionError().xx;
    lh.eyy = h.getPositionError().yy;
    perLayer[layer].push_back(lh);
    perLayerHitObj[layer].push_back(h);
  }

  bool allFive = true;
  for (int l = 0; l < 5; ++l) {
    if (perLayer[l].empty()) {
      allFive = false;
    }
  }

  ++m_eventCounter;
  if (!allFive) {
    ++m_fitFail;
    if (m_eventCounter <= 3) {
      std::cerr << "[local_eicrecon] BeamTestACTSFitter::process event=" << m_eventCounter
                << " status=missing_simaps_layers" << std::endl;
    }
    return;
  }

  std::vector<LayerHit> selected;
  std::vector<edm4eic::TrackerHit> selectedHitObjects;
  selected.reserve(7);
  selectedHitObjects.reserve(7);

  for (int l = 0; l < 5; ++l) {
    auto picked = pickRepresentative(perLayer[l]);
    if (!picked.has_value()) {
      ++m_fitFail;
      if (m_fitFail <= 3) {
        std::cerr << "[local_eicrecon] BeamTestACTSFitter::fit_skip event=" << m_eventCounter
                  << " reason=ambiguous_or_missing_simaps_layer layer=" << l
                  << " nhits=" << perLayer[l].size() << std::endl;
      }
      return;
    }
    selected.push_back(*picked);
    selectedHitObjects.push_back(perLayerHitObj[l].front());
  }

  if (m_cfg.useMPGD) {
    std::vector<LayerHit> mpgdLayerHits;
    std::vector<edm4eic::TrackerHit> mpgdLayerObjs;
    for (const auto& h : *mpgdHits) {
      const int layer = decodeLayer(static_cast<uint64_t>(h.getCellID()));
      if (layer != 5) {
        continue;
      }
      LayerHit lh;
      lh.layer = layer;
      lh.x = h.getPosition().x;
      lh.y = h.getPosition().y;
      lh.z = h.getPosition().z;
      lh.exx = h.getPositionError().xx;
      lh.eyy = h.getPositionError().yy;
      mpgdLayerHits.push_back(lh);
      mpgdLayerObjs.push_back(h);
    }
    auto picked = pickRepresentative(mpgdLayerHits);
    if (picked.has_value()) {
      selected.push_back(*picked);
      selectedHitObjects.push_back(mpgdLayerObjs.front());
    } else if (!mpgdLayerHits.empty()) {
      ++m_fitFail;
      if (m_fitFail <= 3) {
        std::cerr << "[local_eicrecon] BeamTestACTSFitter::fit_skip event=" << m_eventCounter
                  << " reason=ambiguous_mpgd_layer nhits=" << mpgdLayerHits.size() << std::endl;
      }
      return;
    }
  }

  if (m_cfg.useACLGAD) {
    std::vector<LayerHit> aclgadLayerHits;
    std::vector<edm4eic::TrackerHit> aclgadLayerObjs;
    for (const auto& h : *aclgadHits) {
      const int layer = decodeLayer(static_cast<uint64_t>(h.getCellID()));
      if (layer != 6) {
        continue;
      }
      LayerHit lh;
      lh.layer = layer;
      lh.x = h.getPosition().x;
      lh.y = h.getPosition().y;
      lh.z = h.getPosition().z;
      lh.exx = h.getPositionError().xx;
      lh.eyy = h.getPositionError().yy;
      aclgadLayerHits.push_back(lh);
      aclgadLayerObjs.push_back(h);
    }
    auto picked = pickRepresentative(aclgadLayerHits);
    if (picked.has_value()) {
      selected.push_back(*picked);
      selectedHitObjects.push_back(aclgadLayerObjs.front());
    } else if (!aclgadLayerHits.empty()) {
      ++m_fitFail;
      if (m_fitFail <= 3) {
        std::cerr << "[local_eicrecon] BeamTestACTSFitter::fit_skip event=" << m_eventCounter
                  << " reason=ambiguous_aclgad_layer nhits=" << aclgadLayerHits.size() << std::endl;
      }
      return;
    }
  }

  std::set<int> uniqueLayers;
  for (const auto& h : selected) {
    uniqueLayers.insert(h.layer);
  }

  if (m_cfg.alignmentTestShiftLayer >= 0 && std::abs(m_cfg.alignmentTestShiftXmm) > 0.0) {
    for (auto& h : selected) {
      if (h.layer == m_cfg.alignmentTestShiftLayer) {
        h.x += m_cfg.alignmentTestShiftXmm;
      }
    }
  }
  if (uniqueLayers.size() != selected.size()) {
    std::cerr << "[local_eicrecon] BeamTestACTSFitter::warning duplicate layers in selected measurements"
              << " event=" << m_eventCounter
              << " selected=" << selected.size()
              << " unique_layers=" << uniqueLayers.size()
              << std::endl;
  }

  std::vector<LayerHit> selectedForFit;
  selectedForFit.reserve(selected.size());
  for (const auto& h : selected) {
    if (m_cfg.excludeLayerFromFit >= 0 && h.layer == m_cfg.excludeLayerFromFit) {
      continue;
    }
    selectedForFit.push_back(h);
  }

  const bool useGlobalCoords = inferGlobalCoordsFromZ(perLayer);
  auto fitBundle = fitSelected(selectedForFit, useGlobalCoords);
  if (!fitBundle.has_value() || !fitBundle->summary.ok) {
    ++m_fitFail;
    if (m_fitFail <= 3) {
      std::cerr << "[local_eicrecon] BeamTestACTSFitter::fit_fail event=" << m_eventCounter
                << " error=" << (fitBundle.has_value() ? fitBundle->summary.error : std::string("no_fit_result"))
                << std::endl;
    }
    return;
  }

  const auto& fit = fitBundle->summary;
  ++m_fitSuccess;

  auto traj = trajectories->create();
  traj.setType(0);
  traj.setNStates(static_cast<uint32_t>(fit.nStates));
  traj.setNMeasurements(static_cast<uint32_t>(fit.nMeasurements));
  traj.setNOutliers(static_cast<uint32_t>(fit.nOutliers));
  traj.setNHoles(static_cast<uint32_t>(fit.nHoles));
  traj.setNSharedHits(static_cast<uint32_t>(fit.nSharedHits));
  traj.addToMeasurementChi2(static_cast<float>(fit.chi2));

  auto pars = trackParameters->create();
  pars.setType(0);
  pars.setLoc(edm4hep::Vector2f{static_cast<float>(fit.loc0_mm), static_cast<float>(fit.loc1_mm)});
  pars.setTheta(static_cast<float>(fit.theta));
  pars.setPhi(static_cast<float>(fit.phi));
  pars.setQOverP(static_cast<float>(fit.qOverP));
  pars.setTime(static_cast<float>(fit.time_ns));

  edm4eic::Cov6f cov;
  for (std::size_t i = 0; i < 6; ++i) {
    for (std::size_t j = 0; j < 6; ++j) {
      cov(i, j) = static_cast<float>(fit.covariance(i, j));
    }
  }
  pars.setCovariance(cov);
  traj.addToTrackParameters(pars);

  auto trk = tracks->create();
  trk.setType(pars.getType());
  trk.setPosition(edm4hep::Vector3f{static_cast<float>(fit.loc0_mm),
                                    static_cast<float>(fit.loc1_mm),
                                    static_cast<float>(m_zmm[0])});
  trk.setMomentum(edm4hep::utils::sphericalToVector(fit.pGeV, fit.theta, fit.phi));
  trk.setPositionMomentumCovariance(edm4eic::Cov6f());
  trk.setTime(static_cast<float>(fit.time_ns));
  const float terr = (fit.covariance(Acts::eBoundTime, Acts::eBoundTime) > 0)
                         ? static_cast<float>(std::sqrt(fit.covariance(Acts::eBoundTime, Acts::eBoundTime)) /
                                              Acts::UnitConstants::ns)
                         : 0.0f;
  trk.setTimeError(terr);
  const float charge = (std::isfinite(fit.qOverP) && std::abs(fit.qOverP) > std::numeric_limits<float>::epsilon())
                           ? static_cast<float>(std::copysign(1.0, fit.qOverP))
                           : 0.0f;
  trk.setCharge(charge);
  trk.setChi2(static_cast<float>(fit.chi2));
  trk.setNdf(static_cast<uint32_t>(std::max(0.0, fit.ndf)));
  trk.setPdg(m_cfg.outputTrackPDG);
  trk.setTrajectory(traj);

  auto predSeg = predictedSegments->create();
  predSeg.setTrack(trk);
  predSeg.setLength(std::numeric_limits<float>::quiet_NaN());
  predSeg.setLengthError(std::numeric_limits<float>::quiet_NaN());

  auto filtSeg = filteredSegments->create();
  filtSeg.setTrack(trk);
  filtSeg.setLength(std::numeric_limits<float>::quiet_NaN());
  filtSeg.setLengthError(std::numeric_limits<float>::quiet_NaN());

  auto smoothSeg = smoothedSegments->create();
  smoothSeg.setTrack(trk);
  smoothSeg.setLength(std::numeric_limits<float>::quiet_NaN());
  smoothSeg.setLengthError(std::numeric_limits<float>::quiet_NaN());

  std::unordered_map<int, edm4eic::TrackerHit> layerToHit;
  for (std::size_t i = 0; i < selected.size() && i < selectedHitObjects.size(); ++i) {
    layerToHit[selected[i].layer] = selectedHitObjects[i];
  }

  for (const auto& s : fitBundle->states) {
    edm4eic::Cov3f measCov = makeCov3(static_cast<float>(s.measCov(0, 0)),
                      static_cast<float>(s.measCov(1, 1)),
                      sqr(static_cast<float>(m_cfg.timeResolution)));

    edm4eic::Cov3f predCov = makeCov3(static_cast<float>(s.predCov(0, 0)),
                      static_cast<float>(s.predCov(1, 1)),
                      sqr(static_cast<float>(m_cfg.timeResolution)));

    edm4eic::Cov3f filtCov = makeCov3(static_cast<float>(s.filtCov(0, 0)),
                      static_cast<float>(s.filtCov(1, 1)),
                      sqr(static_cast<float>(m_cfg.timeResolution)));

    edm4eic::Cov3f smoothCov = makeCov3(static_cast<float>(s.smoothCov(0, 0)),
                      static_cast<float>(s.smoothCov(1, 1)),
                      sqr(static_cast<float>(m_cfg.timeResolution)));

    if (s.hasMeasurement) {
      auto m = fitMeasurements->create();
      m.setSurface(s.surface);
      m.setLoc(edm4hep::Vector2f{static_cast<float>(s.measLoc[0] / Acts::UnitConstants::mm),
                                 static_cast<float>(s.measLoc[1] / Acts::UnitConstants::mm)});
      m.setTime(s.time_ns);
      m.setCovariance(measCov);
      if (layerToHit.contains(s.layer)) {
        m.addToHits(layerToHit.at(s.layer));
      }
      trk.addToMeasurements(m);
      traj.addToMeasurements_deprecated(m);
    }

    if (s.hasPredicted) {
      auto pm = predictedMeasurements->create();
      pm.setSurface(s.surface);
      pm.setLoc(edm4hep::Vector2f{static_cast<float>(s.predLoc[0] / Acts::UnitConstants::mm),
                                  static_cast<float>(s.predLoc[1] / Acts::UnitConstants::mm)});
      pm.setTime(s.time_ns);
      pm.setCovariance(predCov);
      if (layerToHit.contains(s.layer)) {
        pm.addToHits(layerToHit.at(s.layer));
      }

      edm4eic::TrackPoint tp{};
      tp.surface = s.surface;
      tp.system = (s.layer >= 0) ? static_cast<uint32_t>(s.layer) : 0U;
      const auto* surf = m_surfaceMap.at(s.surface);
      const Acts::Vector3 dirPred = Acts::makeDirectionFromPhiTheta(fit.phi, fit.theta);
      auto g = surf->localToGlobal(m_gctx, s.predLoc, dirPred);
      tp.position = edm4hep::Vector3f{static_cast<float>(g.x() / Acts::UnitConstants::mm),
                                      static_cast<float>(g.y() / Acts::UnitConstants::mm),
                                      static_cast<float>(g.z() / Acts::UnitConstants::mm)};
      tp.positionError = predCov;
      tp.momentum = edm4hep::utils::sphericalToVector(fit.pGeV, fit.theta, fit.phi);
      tp.momentumError = edm4eic::Cov3f(std::numeric_limits<float>::quiet_NaN(),
                                        std::numeric_limits<float>::quiet_NaN(),
                                        std::numeric_limits<float>::quiet_NaN());
      tp.time = s.time_ns;
      tp.timeError = static_cast<float>(m_cfg.timeResolution);
      tp.theta = static_cast<float>(fit.theta);
      tp.phi = static_cast<float>(fit.phi);
      tp.directionError = edm4eic::Cov2f(std::numeric_limits<float>::quiet_NaN(),
                                         std::numeric_limits<float>::quiet_NaN(),
                                         std::numeric_limits<float>::quiet_NaN());
      tp.pathlength = std::numeric_limits<float>::quiet_NaN();
      tp.pathlengthError = std::numeric_limits<float>::quiet_NaN();
      predSeg.addToPoints(tp);
    }

    if (s.hasFiltered) {
      auto fm = filteredMeasurements->create();
      fm.setSurface(s.surface);
      fm.setLoc(edm4hep::Vector2f{static_cast<float>(s.filtLoc[0] / Acts::UnitConstants::mm),
                                  static_cast<float>(s.filtLoc[1] / Acts::UnitConstants::mm)});
      fm.setTime(s.time_ns);
      fm.setCovariance(filtCov);
      if (layerToHit.contains(s.layer)) {
        fm.addToHits(layerToHit.at(s.layer));
      }

      edm4eic::TrackPoint tp{};
      tp.surface = s.surface;
      tp.system = (s.layer >= 0) ? static_cast<uint32_t>(s.layer) : 0U;
      const auto* surf = m_surfaceMap.at(s.surface);
      const Acts::Vector3 dirFilt = Acts::makeDirectionFromPhiTheta(fit.phi, fit.theta);
      auto g = surf->localToGlobal(m_gctx, s.filtLoc, dirFilt);
      tp.position = edm4hep::Vector3f{static_cast<float>(g.x() / Acts::UnitConstants::mm),
                                      static_cast<float>(g.y() / Acts::UnitConstants::mm),
                                      static_cast<float>(g.z() / Acts::UnitConstants::mm)};
      tp.positionError = filtCov;
      tp.momentum = edm4hep::utils::sphericalToVector(fit.pGeV, fit.theta, fit.phi);
      tp.momentumError = edm4eic::Cov3f(std::numeric_limits<float>::quiet_NaN(),
                                        std::numeric_limits<float>::quiet_NaN(),
                                        std::numeric_limits<float>::quiet_NaN());
      tp.time = s.time_ns;
      tp.timeError = static_cast<float>(m_cfg.timeResolution);
      tp.theta = static_cast<float>(fit.theta);
      tp.phi = static_cast<float>(fit.phi);
      tp.directionError = edm4eic::Cov2f(std::numeric_limits<float>::quiet_NaN(),
                                         std::numeric_limits<float>::quiet_NaN(),
                                         std::numeric_limits<float>::quiet_NaN());
      tp.pathlength = std::numeric_limits<float>::quiet_NaN();
      tp.pathlengthError = std::numeric_limits<float>::quiet_NaN();
      filtSeg.addToPoints(tp);
    }

    if (s.hasSmoothed) {
      auto sm = smoothedMeasurements->create();
      sm.setSurface(s.surface);
      sm.setLoc(edm4hep::Vector2f{static_cast<float>(s.smoothLoc[0] / Acts::UnitConstants::mm),
                                  static_cast<float>(s.smoothLoc[1] / Acts::UnitConstants::mm)});
      sm.setTime(s.time_ns);
      sm.setCovariance(smoothCov);
      if (layerToHit.contains(s.layer)) {
        sm.addToHits(layerToHit.at(s.layer));
      }

      edm4eic::TrackPoint tp{};
      tp.surface = s.surface;
      tp.system = (s.layer >= 0) ? static_cast<uint32_t>(s.layer) : 0U;
      const auto* surf = m_surfaceMap.at(s.surface);
      const Acts::Vector3 dirSmooth = Acts::makeDirectionFromPhiTheta(fit.phi, fit.theta);
      auto g = surf->localToGlobal(m_gctx, s.smoothLoc, dirSmooth);
      tp.position = edm4hep::Vector3f{static_cast<float>(g.x() / Acts::UnitConstants::mm),
                                      static_cast<float>(g.y() / Acts::UnitConstants::mm),
                                      static_cast<float>(g.z() / Acts::UnitConstants::mm)};
      tp.positionError = smoothCov;
      tp.momentum = edm4hep::utils::sphericalToVector(fit.pGeV, fit.theta, fit.phi);
      tp.momentumError = edm4eic::Cov3f(std::numeric_limits<float>::quiet_NaN(),
                                        std::numeric_limits<float>::quiet_NaN(),
                                        std::numeric_limits<float>::quiet_NaN());
      tp.time = s.time_ns;
      tp.timeError = static_cast<float>(m_cfg.timeResolution);
      tp.theta = static_cast<float>(fit.theta);
      tp.phi = static_cast<float>(fit.phi);
      tp.directionError = edm4eic::Cov2f(std::numeric_limits<float>::quiet_NaN(),
                                         std::numeric_limits<float>::quiet_NaN(),
                                         std::numeric_limits<float>::quiet_NaN());
      tp.pathlength = std::numeric_limits<float>::quiet_NaN();
      tp.pathlengthError = std::numeric_limits<float>::quiet_NaN();
      smoothSeg.addToPoints(tp);
    }
  }

  const int classicalNdf = std::max(0, 2 * fit.nMeasurements - 4);

  if (m_eventCounter <= 3) {
    std::cerr << "[local_eicrecon] BeamTestACTSFitter::process event=" << m_eventCounter
              << " mode=" << (useGlobalCoords ? "global" : "local")
              << " nHits=" << selected.size()
              << " nHitsFit=" << selectedForFit.size()
              << " excludeLayerFromFit=" << m_cfg.excludeLayerFromFit
              << " nMeas=" << fit.nMeasurements
              << " actsNDF=" << fit.ndf
              << " classicalNDF=" << classicalNdf
              << " chi2/actsNDF=" << fit.chi2ndf
              << std::endl;
  }
}

} // namespace local_eicrecon
