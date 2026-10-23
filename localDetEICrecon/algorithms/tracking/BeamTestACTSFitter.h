// Origin: refactored from seven_layer/standalone_acts/src/standalone_acts_fit.cpp
// Source revision: local workspace 2026-10-16
// Local purpose: run ACTS fitting in-process inside JANA2 / local_eicrecon plugin
// Adaptation: algorithm interface for local JOmniFactory and EDM4eic outputs

#pragma once

#include <Acts/Definitions/TrackParametrization.hpp>
#include <Acts/Definitions/Units.hpp>
#include <Acts/EventData/SourceLink.hpp>
#include <Acts/EventData/TrackContainer.hpp>
#include <Acts/EventData/VectorMultiTrajectory.hpp>
#include <Acts/EventData/VectorTrackContainer.hpp>
#include <Acts/Geometry/GeometryContext.hpp>
#include <Acts/Geometry/GeometryIdentifier.hpp>
#include <Acts/MagneticField/ConstantBField.hpp>
#include <Acts/Propagator/DirectNavigator.hpp>
#include <Acts/Propagator/EigenStepper.hpp>
#include <Acts/Propagator/Propagator.hpp>
#include <Acts/Surfaces/RectangleBounds.hpp>
#include <Acts/Surfaces/PlaneSurface.hpp>
#include <Acts/TrackFitting/KalmanFitter.hpp>
#include <Acts/Utilities/Logger.hpp>
#include <algorithms/algorithm.h>
#include <edm4eic/Measurement2DCollection.h>
#include <edm4eic/TrackCollection.h>
#include <edm4eic/TrackParametersCollection.h>
#include <edm4eic/TrackSegmentCollection.h>
#include <edm4eic/TrackerHitCollection.h>
#include <edm4eic/TrajectoryCollection.h>

#include <array>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "BeamTestACTSFitterConfig.h"
#include "algorithms/interfaces/WithPodConfig.h"

namespace local_eicrecon {

using BeamTestACTSFitterAlgorithm = algorithms::Algorithm<
    algorithms::Input<edm4eic::TrackerHitCollection, edm4eic::TrackerHitCollection,
                      edm4eic::TrackerHitCollection>,
  algorithms::Output<edm4eic::TrajectoryCollection, edm4eic::TrackParametersCollection,
             edm4eic::TrackCollection, edm4eic::Measurement2DCollection,
             edm4eic::Measurement2DCollection, edm4eic::Measurement2DCollection,
                       edm4eic::Measurement2DCollection, edm4eic::TrackSegmentCollection,
                       edm4eic::TrackSegmentCollection, edm4eic::TrackSegmentCollection>>;

class BeamTestACTSFitter : public BeamTestACTSFitterAlgorithm,
                           public eicrecon::WithPodConfig<BeamTestACTSFitterConfig> {
public:
  BeamTestACTSFitter(std::string_view name);

  void init() final;
  void setPlacements(const std::array<Acts::Transform3,7>& placements) { m_placements=placements; }
  // Optional converted surfaces retain their detector-element/Geometry owner.
  void setConvertedSurfaces(const std::array<std::shared_ptr<Acts::PlaneSurface>,7>& surfaces,
                            const Acts::GeometryContext& context, std::shared_ptr<void> owner) {
    m_convertedSurfaces=surfaces; m_gctx=context; m_geometryOwner=std::move(owner);
  }
  void process(const Input&, const Output&) const final;

private:
  std::optional<std::array<std::shared_ptr<Acts::PlaneSurface>,7>> m_convertedSurfaces;
  std::shared_ptr<void> m_geometryOwner;
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

  struct LayerHit {
    int layer{-1};
    double x{0};
    double y{0};
    double z{0};
    double exx{0};
    double eyy{0};
  };

  struct FitResultSummary {
    bool ok{false};
    std::string error;
    int nMeasurements{0};
    int nStates{0};
    int nOutliers{0};
    int nHoles{0};
    int nSharedHits{0};
    double chi2{0.0};
    double ndf{0.0};
    double chi2ndf{-1.0};
    double loc0_mm{0.0};
    double loc1_mm{0.0};
    double phi{0.0};
    double theta{0.0};
    double qOverP{0.0};
    double time_ns{0.0};
    Acts::BoundMatrix covariance{Acts::BoundMatrix::Zero()};
    double dirx{0.0};
    double diry{0.0};
    double dirz{0.0};
    double pGeV{0.0};
  };

  struct StateDiag {
    int layer{-1};
    std::uint64_t surface{0};
    std::size_t sourceIndex{0};
    bool hasMeasurement{false};
    bool hasPredicted{false};
    bool hasFiltered{false};
    bool hasSmoothed{false};
    Acts::Vector2 measLoc{Acts::Vector2::Zero()};
    Acts::SquareMatrix2 measCov{Acts::SquareMatrix2::Zero()};
    Acts::Vector2 predLoc{Acts::Vector2::Zero()};
    Acts::Vector2 filtLoc{Acts::Vector2::Zero()};
    Acts::Vector2 smoothLoc{Acts::Vector2::Zero()};
    Acts::SquareMatrix2 predCov{Acts::SquareMatrix2::Zero()};
    Acts::SquareMatrix2 filtCov{Acts::SquareMatrix2::Zero()};
    Acts::SquareMatrix2 smoothCov{Acts::SquareMatrix2::Zero()};
    Acts::Vector2 residualPred{Acts::Vector2::Zero()};
    Acts::Vector2 residualFilt{Acts::Vector2::Zero()};
    Acts::Vector2 residualSmooth{Acts::Vector2::Zero()};
    float time_ns{0.F};
  };

  struct FitResultBundle {
    FitResultSummary summary;
    std::vector<StateDiag> states;
  };

  struct SurfaceAccessor {
    const std::unordered_map<uint64_t, const Acts::Surface*>* map{nullptr};
    const Acts::Surface* operator()(const Acts::SourceLink& sl) const;
  };

  struct Calibrator {
    const std::vector<FitMeas>* measurements{nullptr};
    void calibrate(const Acts::GeometryContext&, const Acts::CalibrationContext&, const Acts::SourceLink&,
                   Acts::VectorMultiTrajectory::TrackStateProxy) const;
  };

  using Stepper = Acts::EigenStepper<>;
  using Navigator = Acts::DirectNavigator;
  using Propagator = Acts::Propagator<Stepper, Navigator>;
  using Traj = Acts::VectorMultiTrajectory;
  using TrackContainer =
      Acts::TrackContainer<Acts::VectorTrackContainer, Acts::VectorMultiTrajectory, std::shared_ptr>;
  using Fitter = Acts::KalmanFitter<Propagator, Traj>;

  std::optional<FitResultBundle> fitSelected(const std::vector<LayerHit>& selected,
                                             bool useGlobalCoords) const;
  static int decodeLayer(uint64_t cellid);
  static std::optional<LayerHit> pickRepresentative(const std::vector<LayerHit>& hits);
  bool inferGlobalCoordsFromZ(const std::array<std::vector<LayerHit>, 5>& simaps) const;

private:
  Acts::GeometryContext m_gctx{Acts::GeometryContext::dangerouslyDefaultConstruct()};
  Acts::MagneticFieldContext m_mctx{};
  Acts::CalibrationContext m_cctx{};

  std::optional<std::array<Acts::Transform3,7>> m_placements;
  std::array<double, 7> m_zmm{{0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0}};
  double m_halfXmm{50.0};
  double m_halfYmm{50.0};

  std::vector<std::shared_ptr<Acts::PlaneSurface>> m_surfaces;
  std::unordered_map<uint64_t, const Acts::Surface*> m_surfaceMap;
  std::vector<const Acts::Surface*> m_surfaceSequence;

  std::shared_ptr<Acts::ConstantBField> m_bfield;
  std::unique_ptr<Fitter> m_fitter;

  mutable std::size_t m_eventCounter{0};
  mutable std::size_t m_fitSuccess{0};
  mutable std::size_t m_fitFail{0};
};

} // namespace local_eicrecon
