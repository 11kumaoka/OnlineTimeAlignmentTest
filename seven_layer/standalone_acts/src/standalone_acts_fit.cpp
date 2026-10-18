#include <Acts/Definitions/TrackParametrization.hpp>
#include <Acts/Definitions/Units.hpp>
#include <Acts/EventData/SourceLink.hpp>
#include <Acts/EventData/TrackContainer.hpp>
#include <Acts/EventData/TrackParameters.hpp>
#include <Acts/EventData/VectorMultiTrajectory.hpp>
#include <Acts/EventData/VectorTrackContainer.hpp>
#include <Acts/Geometry/GeometryContext.hpp>
#include <Acts/Geometry/GeometryIdentifier.hpp>
#include <Acts/MagneticField/ConstantBField.hpp>
#include <Acts/Propagator/DirectNavigator.hpp>
#include <Acts/Propagator/EigenStepper.hpp>
#include <Acts/Propagator/Propagator.hpp>
#include <Acts/Surfaces/PlaneSurface.hpp>
#include <Acts/Surfaces/RectangleBounds.hpp>
#include <Acts/TrackFitting/GainMatrixSmoother.hpp>
#include <Acts/TrackFitting/GainMatrixUpdater.hpp>
#include <Acts/TrackFitting/KalmanFitter.hpp>
#include <Acts/Utilities/Logger.hpp>

#include <edm4eic/TrackerHitCollection.h>

#include <podio/Frame.h>
#include <podio/Reader.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

struct FitSourceLink {
  Acts::GeometryIdentifier gid{};
  std::size_t index{0};
  FitSourceLink() = default;
  FitSourceLink(Acts::GeometryIdentifier g, std::size_t i) : gid(g), index(i) {}
  Acts::GeometryIdentifier geometryId() const { return gid; }
};

struct FitMeas {
  Acts::Vector2 loc{Acts::Vector2::Zero()};
  Acts::SquareMatrix2 cov{Acts::SquareMatrix2::Zero()};
};

struct SurfaceAccessor {
  const std::unordered_map<uint64_t, const Acts::Surface*>* map{nullptr};
  const Acts::Surface* operator()(const Acts::SourceLink& sl) const {
    const auto& fsl = sl.get<FitSourceLink>();
    const auto it = map->find(fsl.geometryId().value());
    if (it == map->end()) {
      return nullptr;
    }
    return it->second;
  }
};

struct Calibrator {
  const std::vector<FitMeas>* measurements{nullptr};
  void calibrate(const Acts::GeometryContext&, const Acts::CalibrationContext&,
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
};

int decode_layer(uint64_t cellid) {
  return static_cast<int>((cellid >> 11) & ((1ULL << 6) - 1ULL));
}

struct LayerHit {
  int layer{-1};
  double x{0};
  double y{0};
  double z{0};
  double exx{0};
  double eyy{0};
};

struct FitSummary {
  bool ok{false};
  int nMeasurements{0};
  double chi2{0.0};
  double ndf{0.0};
  double chi2ndf{-1.0};
  double loc0_mm{0.0};
  double loc1_mm{0.0};
  double phi{0.0};
  double theta{0.0};
  double dirx{0.0};
  double diry{0.0};
  double dirz{0.0};
  std::string error;
};

double sqr(double x) { return x * x; }

bool near(double a, double b, double tol) { return std::abs(a - b) < tol; }

std::optional<LayerHit> pickRepresentative(const std::vector<LayerHit>& hits) {
  if (hits.empty()) {
    return std::nullopt;
  }
  auto best = std::min_element(hits.begin(), hits.end(), [](const LayerHit& a, const LayerHit& b) {
    return std::abs(a.x) < std::abs(b.x);
  });
  return *best;
}

bool inferGlobalCoordsFromZ(const std::array<std::vector<LayerHit>, 5>& simaps,
                           const std::array<double, 5>& z_mm) {
  int checked = 0;
  int matchGlobal = 0;
  int nearZero = 0;
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
    if (near(meanz, z_mm[l], 5.0)) {
      ++matchGlobal;
    }
    if (std::abs(meanz) < 5.0) {
      ++nearZero;
    }
  }
  // If most layers line up with expected z positions, treat positions as global.
  // Otherwise fall back to local-coordinate interpretation.
  if (checked == 0) {
    return true;
  }
  if (matchGlobal >= 3) {
    return true;
  }
  return !(nearZero >= 4);
}

template <typename FitterT, typename TrajT, typename TrackContainerT>
FitSummary runFit(FitterT& fitter,
                  const std::vector<const Acts::Surface*>& surface_sequence,
                  const std::unordered_map<uint64_t, const Acts::Surface*>& surface_map,
                  const std::vector<LayerHit>& selected,
                  bool useGlobalCoords,
                  const Acts::GeometryContext& gctx,
                  const Acts::MagneticFieldContext& mctx,
                  const Acts::CalibrationContext& cctx,
                  const std::array<double, 7>& z_mm,
                  TrackContainerT& tracks) {
  FitSummary out;
  if (selected.size() < 2) {
    out.error = "insufficient selected hits";
    return out;
  }

  std::vector<FitMeas> meas_data;
  std::vector<Acts::SourceLink> source_links;
  std::vector<Acts::Vector3> seed_points;
  meas_data.reserve(selected.size());
  source_links.reserve(selected.size());
  seed_points.reserve(selected.size());

  for (const auto& h : selected) {
    if (h.layer < 0 || h.layer >= static_cast<int>(surface_sequence.size())) {
      out.error = "layer index out of surface range";
      return out;
    }
    const auto* surf = surface_sequence[h.layer];

    FitMeas m;
    if (useGlobalCoords) {
      const Acts::Vector3 gpos(h.x * Acts::UnitConstants::mm,
                               h.y * Acts::UnitConstants::mm,
                               h.z * Acts::UnitConstants::mm);
      const Acts::Vector3 ref_dir(0.0, 0.0, 1.0);
      auto lres = surf->globalToLocal(gctx, gpos, ref_dir, 5.0 * Acts::UnitConstants::mm);
      if (!lres.ok()) {
        out.error = "globalToLocal failed";
        return out;
      }
      m.loc = lres.value();
    } else {
      m.loc[0] = h.x * Acts::UnitConstants::mm;
      m.loc[1] = h.y * Acts::UnitConstants::mm;
    }

    const double sx2 = std::max(1e-8, static_cast<double>(h.exx)) * sqr(Acts::UnitConstants::mm);
    const double sy2 = std::max(1e-8, static_cast<double>(h.eyy)) * sqr(Acts::UnitConstants::mm);
    m.cov(0, 0) = sx2;
    m.cov(1, 1) = sy2;
    m.cov(0, 1) = 0.0;
    m.cov(1, 0) = 0.0;

    const std::size_t idx = meas_data.size();
    meas_data.push_back(m);
    source_links.emplace_back(FitSourceLink{surf->geometryId(), idx});

    // Use geometry-derived plane z positions for seed line definition.
    seed_points.emplace_back(m.loc[0], m.loc[1], z_mm[h.layer] * Acts::UnitConstants::mm);
  }

  // Order by increasing z to keep propagation sequence stable.
  std::vector<std::size_t> order(seed_points.size());
  for (std::size_t i = 0; i < order.size(); ++i) {
    order[i] = i;
  }
  std::sort(order.begin(), order.end(), [&](std::size_t a, std::size_t b) {
    return seed_points[a].z() < seed_points[b].z();
  });

  std::vector<Acts::SourceLink> ordered_links;
  std::vector<FitMeas> ordered_meas;
  ordered_links.reserve(order.size());
  ordered_meas.reserve(order.size());
  std::vector<const Acts::Surface*> ordered_surfaces;
  ordered_surfaces.reserve(order.size());
  std::vector<Acts::Vector3> ordered_points;
  ordered_points.reserve(order.size());

  for (auto idx : order) {
    const auto& sl = source_links[idx];
    const auto& fsl = sl.get<FitSourceLink>();
    auto it = surface_map.find(fsl.geometryId().value());
    if (it == surface_map.end()) {
      out.error = "source link surface lookup failed";
      return out;
    }
    ordered_links.push_back(sl);
    ordered_meas.push_back(meas_data[idx]);
    ordered_surfaces.push_back(it->second);
    ordered_points.push_back(seed_points[idx]);
  }

  const auto& p0 = ordered_points.front();
  const auto& pN = ordered_points.back();
  Acts::Vector3 dir = (pN - p0).normalized();

  // Seed before first measurement surface to avoid starting exactly on a measurement.
  Acts::Vector3 seed_pos = p0 - 10.0 * Acts::UnitConstants::mm * dir;

  Acts::BoundMatrix seed_cov = Acts::BoundMatrix::Zero();
  seed_cov(Acts::eBoundLoc0, Acts::eBoundLoc0) = sqr(1.0 * Acts::UnitConstants::mm);
  seed_cov(Acts::eBoundLoc1, Acts::eBoundLoc1) = sqr(1.0 * Acts::UnitConstants::mm);
  seed_cov(Acts::eBoundPhi, Acts::eBoundPhi) = 1e-3;
  seed_cov(Acts::eBoundTheta, Acts::eBoundTheta) = 1e-3;
  // In B=0 this is a weak prior only, not a measurement.
  seed_cov(Acts::eBoundQOverP, Acts::eBoundQOverP) = 1e-4;
  seed_cov(Acts::eBoundTime, Acts::eBoundTime) = sqr(1.0 * Acts::UnitConstants::ns);

  const double qOverP = -1.0 / (5.0 * Acts::UnitConstants::GeV);
  Acts::Vector4 pos4(seed_pos.x(), seed_pos.y(), seed_pos.z(), 0.0);
  auto seed = Acts::BoundTrackParameters::createCurvilinear(
      pos4, dir, qOverP, seed_cov, Acts::ParticleHypothesis::pion());

  SurfaceAccessor surface_accessor{&surface_map};
  Calibrator calibrator{&ordered_meas};
  Acts::GainMatrixUpdater updater;
  Acts::GainMatrixSmoother smoother;

  Acts::KalmanFitterExtensions<TrajT> ext;
  ext.surfaceAccessor.template connect<&SurfaceAccessor::operator()>(&surface_accessor);
  ext.calibrator.template connect<&Calibrator::calibrate>(&calibrator);
  ext.updater.template connect<&Acts::GainMatrixUpdater::operator()<TrajT>>(&updater);
  ext.smoother.template connect<&Acts::GainMatrixSmoother::operator()<TrajT>>(&smoother);

  Acts::PropagatorPlainOptions pOptions(gctx, mctx);
  pOptions.maxSteps = 10000;

  Acts::KalmanFitterOptions<TrajT> fit_options(gctx, mctx, std::cref(cctx), ext, pOptions,
                                               ordered_surfaces.front(),
                                               false,
                                               false,
                                               false,
                                               1.0,
                                               Acts::FreeToBoundCorrection(false));

  auto fit_result = fitter.fit(ordered_links.begin(), ordered_links.end(), seed, fit_options,
                               ordered_surfaces, tracks);

  if (!fit_result.ok()) {
    out.error = fit_result.error().message();
    return out;
  }

  auto trk = fit_result.value();
  out.ok = true;
  out.nMeasurements = static_cast<int>(trk.nMeasurements());
  out.chi2 = trk.chi2();
  out.ndf = trk.nDoF();
  out.chi2ndf = (out.ndf > 0.0) ? out.chi2 / out.ndf : -1.0;
  out.loc0_mm = trk.loc0() / Acts::UnitConstants::mm;
  out.loc1_mm = trk.loc1() / Acts::UnitConstants::mm;
  out.phi = trk.phi();
  out.theta = trk.theta();
  out.dirx = std::cos(out.phi) * std::sin(out.theta);
  out.diry = std::sin(out.phi) * std::sin(out.theta);
  out.dirz = std::cos(out.theta);
  return out;
}

} // namespace

int main(int argc, char** argv) {
  std::string input = "seven_layer/results/local_simaps_reco.root";
  std::string simaps_collection = "LocalSiMAPSRecHits";
  std::string mpgd_collection = "LocalMPGDRecHits";
  std::string aclgad_collection = "LocalACLGADRecHits";
  std::string event_csv = "seven_layer/results/local_to_acts_event_stats.csv";
  bool truth_assist_seed = false;
  if (argc > 1) {
    input = argv[1];
  }
  if (argc > 2) {
    simaps_collection = argv[2];
  }
  if (argc > 3) {
    event_csv = argv[3];
  }

  std::cout << "config input=" << input
            << " simaps_collection=" << simaps_collection
            << " mpgd_collection=" << mpgd_collection
            << " aclgad_collection=" << aclgad_collection
            << " truth_assist_seed=" << (truth_assist_seed ? 1 : 0)
            << "\n";

  // Geometry constants derived from seven_layer_telescope.xml.
  const std::array<double, 7> z_mm = {0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0};
  const double half_x_mm = 50.0;
  const double half_y_mm = 50.0;

#if Acts_VERSION_MAJOR >= 45
  Acts::GeometryContext gctx = Acts::GeometryContext::dangerouslyDefaultConstruct();
#else
  Acts::GeometryContext gctx;
#endif
  Acts::MagneticFieldContext mctx;
  Acts::CalibrationContext cctx;

  std::vector<std::shared_ptr<Acts::PlaneSurface>> surfaces;
  std::unordered_map<uint64_t, const Acts::Surface*> surface_map;
  std::vector<const Acts::Surface*> surface_sequence;

  surfaces.reserve(7);
  for (int i = 0; i < 7; ++i) {
    Acts::Transform3 tr = Acts::Transform3::Identity();
    tr.translation() = Acts::Vector3(0.0, 0.0, z_mm[i] * Acts::UnitConstants::mm);
    auto bounds = std::make_shared<const Acts::RectangleBounds>(half_x_mm * Acts::UnitConstants::mm,
                                                                half_y_mm * Acts::UnitConstants::mm);
    auto s = Acts::Surface::makeShared<Acts::PlaneSurface>(tr, bounds);
    auto gid = Acts::GeometryIdentifier().withVolume(1).withLayer(i + 1).withSensitive(1);
    s->assignGeometryId(gid);
    surface_map.emplace(gid.value(), s.get());
    surface_sequence.push_back(s.get());
    surfaces.push_back(std::move(s));
  }

  auto bfield = std::make_shared<Acts::ConstantBField>(Acts::Vector3(0.0, 0.0, 0.0));
  using Stepper = Acts::EigenStepper<>;
  using Navigator = Acts::DirectNavigator;
  using Propagator = Acts::Propagator<Stepper, Navigator>;
  using Traj = Acts::VectorMultiTrajectory;
  using TrackContainer = Acts::TrackContainer<Acts::VectorTrackContainer, Acts::VectorMultiTrajectory, std::shared_ptr>;

  Stepper stepper(bfield);
  Navigator navigator;
  Propagator propagator(std::move(stepper), std::move(navigator));
  auto logger = Acts::getDefaultLogger("SevenLayerStandaloneKF", Acts::Logging::INFO);
  Acts::KalmanFitter<Propagator, Traj> fitter(std::move(propagator), logger->clone("SevenLayerKF"));

  podio::Reader reader = podio::makeReader(input);
  const auto nEvents = reader.getEntries("events");

  std::ofstream csv(event_csv);
  csv << "event,n_simaps_l0,n_simaps_l1,n_simaps_l2,n_simaps_l3,n_simaps_l4,n_mpgd,n_aclgad,seeds,fit_ok,fit_ok_mpgd,n_meas,chi2,ndf,chi2_ndf,loc0_mm,loc1_mm,dirx,diry,dirz,mpgd_dx_mm,mpgd_dy_mm,aclgad_dx_mm,aclgad_dy_mm,error" << "\n";

  std::size_t events_processed = 0;
  std::size_t events_with_seed = 0;
  std::size_t fit_ok = 0;
  std::size_t fit_fail = 0;
  std::size_t fit_ok_mpgd = 0;
  std::size_t meas4 = 0;
  std::size_t meas5 = 0;
  std::size_t meas6 = 0;
  double chi2_sum = 0.0;
  std::size_t chi2_count = 0;

  for (std::size_t iev = 0; iev < nEvents; ++iev) {
    podio::Frame frame = reader.readFrame("events", iev, {simaps_collection, mpgd_collection, aclgad_collection});
    const auto& simaps_hits = frame.get<edm4eic::TrackerHitCollection>(simaps_collection);

    const auto* mpgd_base = frame.get(mpgd_collection);
    const auto* aclgad_base = frame.get(aclgad_collection);
    const auto* mpgd_hits = dynamic_cast<const edm4eic::TrackerHitCollection*>(mpgd_base);
    const auto* aclgad_hits = dynamic_cast<const edm4eic::TrackerHitCollection*>(aclgad_base);

    ++events_processed;

    std::array<std::vector<LayerHit>, 5> per_layer;
    for (const auto& h : simaps_hits) {
      const int layer = decode_layer(static_cast<uint64_t>(h.getCellID()));
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
      per_layer[layer].push_back(lh);
    }

    std::vector<LayerHit> mpgd_layer_hits;
    if (mpgd_hits != nullptr) {
      for (const auto& h : *mpgd_hits) {
        const int layer = decode_layer(static_cast<uint64_t>(h.getCellID()));
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
        mpgd_layer_hits.push_back(lh);
      }
    }

    std::vector<LayerHit> aclgad_layer_hits;
    if (aclgad_hits != nullptr) {
      for (const auto& h : *aclgad_hits) {
        const int layer = decode_layer(static_cast<uint64_t>(h.getCellID()));
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
        aclgad_layer_hits.push_back(lh);
      }
    }

    const bool useGlobalCoords = inferGlobalCoordsFromZ(per_layer, {z_mm[0], z_mm[1], z_mm[2], z_mm[3], z_mm[4]});

    bool all_layers = true;
    for (int l = 0; l < 5; ++l) {
      if (per_layer[l].empty()) {
        all_layers = false;
      }
    }
    if (!all_layers) {
      csv << iev << ","
          << per_layer[0].size() << "," << per_layer[1].size() << "," << per_layer[2].size() << ","
          << per_layer[3].size() << "," << per_layer[4].size() << ","
          << mpgd_layer_hits.size() << "," << aclgad_layer_hits.size() << ","
          << 0 << "," << 0 << "," << 0
          << ",0,0,0,0,0,0,0,0,0,0,0,0,missing_simaps_layers"
          << "\n";
      continue;
    }

    std::vector<LayerHit> selected;
    selected.reserve(5);
    for (int l = 0; l < 5; ++l) {
      auto picked = pickRepresentative(per_layer[l]);
      if (!picked.has_value()) {
        all_layers = false;
        break;
      }
      selected.push_back(*picked);
    }
    auto tc = std::make_shared<Acts::VectorTrackContainer>();
    auto tm = std::make_shared<Acts::VectorMultiTrajectory>();
    TrackContainer tracks(tc, tm);

    ++events_with_seed;

    // T2: SiMAPS-only fit
    std::vector<const Acts::Surface*> simaps_surfaces(surface_sequence.begin(), surface_sequence.begin() + 5);
    FitSummary simaps_fit = runFit<decltype(fitter), Traj>(
        fitter, simaps_surfaces, surface_map, selected, useGlobalCoords,
        gctx, mctx, cctx, z_mm, tracks);

    bool mpgd_augmented_ok = false;
    FitSummary mpgd_fit;

    // T3: extrapolate SiMAPS track to MPGD plane and compute residuals.
    double mpgd_dx = 0.0;
    double mpgd_dy = 0.0;
    bool has_mpgd_residual = false;
    auto mpgd_pick = pickRepresentative(mpgd_layer_hits);

    // T5: extrapolate to AC-LGAD and validate measured coordinate.
    double aclgad_dx = 0.0;
    double aclgad_dy = 0.0;
    bool has_aclgad_residual = false;
    auto aclgad_pick = pickRepresentative(aclgad_layer_hits);

    if (simaps_fit.ok) {
      ++fit_ok;
      chi2_sum += simaps_fit.chi2ndf;
      ++chi2_count;
      if (simaps_fit.nMeasurements == 4) {
        ++meas4;
      } else if (simaps_fit.nMeasurements == 5) {
        ++meas5;
      } else if (simaps_fit.nMeasurements >= 6) {
        ++meas6;
      }

      // Reference surface: SiMAPS layer-0 plane at z=0.
      const double x0 = simaps_fit.loc0_mm;
      const double y0 = simaps_fit.loc1_mm;
      const double z0 = z_mm[0];

      if (std::abs(simaps_fit.dirz) > 1e-6) {
        if (mpgd_pick.has_value()) {
          const double t = (z_mm[5] - z0) / simaps_fit.dirz;
          const double x_pred = x0 + t * simaps_fit.dirx;
          const double y_pred = y0 + t * simaps_fit.diry;
          mpgd_dx = mpgd_pick->x - x_pred;
          mpgd_dy = mpgd_pick->y - y_pred;
          has_mpgd_residual = true;

          // T4: include MPGD as sixth measurement (provisional 2D model).
          std::vector<LayerHit> selected6 = selected;
          selected6.push_back(*mpgd_pick);
          auto tc6 = std::make_shared<Acts::VectorTrackContainer>();
          auto tm6 = std::make_shared<Acts::VectorMultiTrajectory>();
          TrackContainer tracks6(tc6, tm6);
          std::vector<const Acts::Surface*> simaps_mpgd_surfaces(surface_sequence.begin(), surface_sequence.begin() + 6);
          mpgd_fit = runFit<decltype(fitter), Traj>(
              fitter, simaps_mpgd_surfaces, surface_map, selected6, useGlobalCoords,
              gctx, mctx, cctx, z_mm, tracks6);
          if (mpgd_fit.ok) {
            mpgd_augmented_ok = true;
            ++fit_ok_mpgd;
          }
        }

        if (aclgad_pick.has_value()) {
          const double t = (z_mm[6] - z0) / simaps_fit.dirz;
          const double x_pred = x0 + t * simaps_fit.dirx;
          const double y_pred = y0 + t * simaps_fit.diry;
          aclgad_dx = aclgad_pick->x - x_pred;
          aclgad_dy = aclgad_pick->y - y_pred;
          has_aclgad_residual = true;
        }
      }
    } else {
      ++fit_fail;
    }

    csv << iev << ","
        << per_layer[0].size() << "," << per_layer[1].size() << "," << per_layer[2].size() << ","
        << per_layer[3].size() << "," << per_layer[4].size() << ","
        << mpgd_layer_hits.size() << "," << aclgad_layer_hits.size() << ","
        << 1 << "," << (simaps_fit.ok ? 1 : 0) << "," << (mpgd_augmented_ok ? 1 : 0) << ","
        << simaps_fit.nMeasurements << ","
        << std::setprecision(10) << simaps_fit.chi2 << "," << simaps_fit.ndf << ","
        << simaps_fit.chi2ndf << ","
        << simaps_fit.loc0_mm << "," << simaps_fit.loc1_mm << ","
        << simaps_fit.dirx << "," << simaps_fit.diry << "," << simaps_fit.dirz << ","
        << (has_mpgd_residual ? mpgd_dx : 0.0) << ","
        << (has_mpgd_residual ? mpgd_dy : 0.0) << ","
        << (has_aclgad_residual ? aclgad_dx : 0.0) << ","
        << (has_aclgad_residual ? aclgad_dy : 0.0) << ","
        << (simaps_fit.ok ? "ok" : simaps_fit.error)
        << "\n";

    if (iev < 3) {
      std::cout << "event=" << iev
                << " mode=" << (useGlobalCoords ? "global" : "local")
                << " simaps_hits=5"
                << " seeds=1"
                << " fit_ok=" << (simaps_fit.ok ? 1 : 0)
                << " nMeas=" << simaps_fit.nMeasurements
                << " chi2ndf=" << simaps_fit.chi2ndf
                << " mpgd_hit=" << (mpgd_pick.has_value() ? 1 : 0)
                << " mpgd_aug_fit_ok=" << (mpgd_augmented_ok ? 1 : 0)
                << " aclgad_hit=" << (aclgad_pick.has_value() ? 1 : 0)
                << "\n";
    }
  }

  csv.close();

  std::cout << "summary events_processed=" << events_processed
            << " seeds=" << events_with_seed
            << " fit_fail=" << fit_fail
            << " fit_success=" << fit_ok
            << " fit_success_mpgd_augmented=" << fit_ok_mpgd
            << " meas4=" << meas4
            << " meas5=" << meas5
            << " meas6plus=" << meas6
            << " mean_chi2ndf=" << (chi2_count > 0 ? chi2_sum / static_cast<double>(chi2_count) : -1.0)
            << " output_csv=" << event_csv
            << "\n";

  if (fit_ok == 0) {
    return 2;
  }
  return 0;
}
