// Optional static Gen3 telescope provider using installed ACTS/DD4hep APIs.
#pragma once
#include <Acts/Geometry/Blueprint.hpp>
#include <Acts/Geometry/StaticBlueprintNode.hpp>
#include <Acts/Geometry/CuboidVolumeBounds.hpp>
#include <Acts/Navigation/TryAllNavigationPolicy.hpp>
#include <ActsPlugins/DD4hep/DD4hepDetectorElement.hpp>
#include "SurfacePlacements.h"
#include <Acts/Surfaces/PlaneSurface.hpp>
#include <set>
#include <iostream>
#include <stdexcept>

namespace local_eicrecon {
using ConvertedElements=std::vector<std::shared_ptr<ActsPlugins::DD4hepDetectorElement>>;
// Detector elements must outlive the TrackingGeometry and all fitted tracks.
inline std::unique_ptr<Acts::TrackingGeometry> closeTelescopeGeometry(
    const Acts::GeometryContext& context, const ConvertedElements& elements) {
  if(elements.size()!=7)throw std::runtime_error("Exactly seven converted telescope elements are required");
  // Navigation envelope is derived from converted sensor corners, not a
  // second detector placement model. No material is assigned.
  Acts::Vector3 lo=Acts::Vector3::Constant(1e100),hi=-lo;
  for(const auto& element:elements) {
    const auto* surface=&element->surface();
    const auto t=surface->localToGlobalTransform(context);
    const auto b=surface->bounds().values();
    for(double x:{b[0],b[2]})for(double y:{b[1],b[3]}) {
      Acts::Vector3 point=surface->localToGlobal(context,{x,y},t.linear().col(2));
      lo=lo.cwiseMin(point);hi=hi.cwiseMax(point);
    }
  }
  lo.array()-=10.;hi.array()+=10.;
  Acts::Transform3 transform=Acts::Transform3::Identity();transform.translation()=(hi+lo)/2.;
  const Acts::Vector3 half=(hi-lo)/2.;
  auto volume=std::make_unique<Acts::TrackingVolume>(transform,
      std::make_shared<Acts::CuboidVolumeBounds>(half.x(),half.y(),half.z()),"Telescope");
  for(auto& element:elements)volume->addSurface(element->surface().getSharedPtr());
  Acts::Experimental::Blueprint::Config cfg;
  for(auto axis:{Acts::AxisDirection::AxisX,Acts::AxisDirection::AxisY,Acts::AxisDirection::AxisZ})cfg.envelope.set(axis,{10.,10.});
  Acts::Experimental::Blueprint root(cfg);root.addStaticVolume(std::move(volume));
  Acts::Experimental::BlueprintOptions options;
  options.defaultNavigationPolicyFactory=Acts::NavigationPolicyFactory{}.add<Acts::TryAllNavigationPolicy>().asUniquePtr();
  return root.construct(options,context);

}
// Static immutable XML context: no live alignment payload or material map.
struct ConvertedTelescopeGeometry {
  Acts::GeometryContext context=Acts::GeometryContext::dangerouslyDefaultConstruct();
  ConvertedElements elements;
  std::unique_ptr<Acts::TrackingGeometry> tracking;
  std::array<std::shared_ptr<Acts::PlaneSurface>,7> surfaces;
  std::array<uint64_t,7> volumeIds{};
  explicit ConvertedTelescopeGeometry(const dd4hep::rec::CellIDPositionConverter& converter) {
    const auto reference=surfacePlacements(converter,false);
    std::set<uint64_t> volumes,ids;
    for(int layer=0;layer<7;++layer) {
      const uint64_t system=layer<5?31:(layer==5?100:92);
      const uint64_t cell=system|(1ULL<<8)|(uint64_t(layer)<<11)|(1ULL<<22)|(1ULL<<28);
      const auto* volume=converter.findContext(cell);
      if(!volume || !volume->element.volume().isSensitive() || !volumes.insert(volume->identifier).second)
        throw std::runtime_error("Missing or duplicated sensitive Volume ID");
      auto element=std::make_shared<ActsPlugins::DD4hepDetectorElement>(volume->element,
          ActsPlugins::TGeoAxes::parse("zXy"),Acts::UnitConstants::cm);
      if(element->identifier()!=volume->identifier)throw std::runtime_error("Converted Volume ID mismatch");
      surfaces[layer]=std::dynamic_pointer_cast<Acts::PlaneSurface>(element->surface().getSharedPtr());
      if(!surfaces[layer])throw std::runtime_error("Converted sensor is not a plane");
      const auto t=surfaces[layer]->localToGlobalTransform(context);
      if((t.translation()-reference[layer].translation()).norm()>1e-10 ||
          (t.linear()-reference[layer].linear()).cwiseAbs().maxCoeff()>1e-12)
        throw std::runtime_error("Converted local coordinates do not match the maintained measurement basis");
      volumeIds[layer]=volume->identifier;elements.push_back(std::move(element));
    }
    tracking=closeTelescopeGeometry(context,elements);
    std::set<const Acts::Surface*> contained;
    tracking->visitSurfaces([&](const Acts::Surface* surface){contained.insert(surface);});
    if(contained.size()!=7)throw std::runtime_error("TrackingGeometry does not contain exactly seven sensitive surfaces");
    for(const auto& surface:surfaces)
      if(!surface->geometryId().value() || !ids.insert(surface->geometryId().value()).second)
        throw std::runtime_error("Unclosed or duplicated sensitive GeometryIdentifier");
    for(int layer=0;layer<7;++layer) {
      if(!contained.contains(surfaces[layer].get()) || tracking->findSurface(surfaces[layer]->geometryId())!=surfaces[layer].get())
        throw std::runtime_error("TrackingGeometry sensitive association mismatch");
      std::cerr << "ConvertedGeometryMapping layer=" << layer << " volume_id=" << volumeIds[layer]
                << " geometry_id=" << surfaces[layer]->geometryId().value() << std::endl;
    }
  }
};
} // namespace local_eicrecon
