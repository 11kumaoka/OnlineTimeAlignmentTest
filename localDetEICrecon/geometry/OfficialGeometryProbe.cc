// Isolated installed-provider audit. No tracking, alignment, or Geometry activation.
#include <Acts/ActsVersion.hpp>
#include <Acts/Geometry/Blueprint.hpp>
#include <Acts/Geometry/StaticBlueprintNode.hpp>
#include <Acts/Geometry/CuboidVolumeBounds.hpp>
#include <Acts/Navigation/TryAllNavigationPolicy.hpp>
#include <Acts/Propagator/Navigator.hpp>
#include <Acts/Surfaces/PlaneSurface.hpp>
#include <Acts/Surfaces/RectangleBounds.hpp>
#include <ActsPlugins/DD4hep/DD4hepConversionHelpers.hpp>
#include <ActsPlugins/DD4hep/DD4hepDetectorElement.hpp>
#include <DD4hep/Detector.h>
#include <DD4hep/DetType.h>
#include <DDRec/DetectorData.h>
#include <algorithms/tracking/ActsGeometryProvider.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <nlohmann/json.hpp>
#include <fcntl.h>
#include <unistd.h>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include "SurfacePlacements.h"
#include "ConvertedTelescopeGeometry.h"

using Json = nlohmann::json;
namespace {
Json matrix(const Acts::Transform3& t) {
  Json r=Json::array();
  for(int i=0;i<3;++i)r.push_back({t.linear()(i,0),t.linear()(i,1),t.linear()(i,2)});
  return r;
}
Json vector(const Acts::Vector3& v) { return {v[0],v[1],v[2]}; }
Json surfaceInfo(const Acts::Surface& s,const Acts::GeometryContext& ctx) {
  const auto t=s.localToGlobalTransform(ctx);
  double error=0.;
  for(const Acts::Vector2 point : {Acts::Vector2(0.,0.),Acts::Vector2(10.,-7.)}) {
    const auto world=s.localToGlobal(ctx,point,t.linear().col(2));
    const auto local=s.globalToLocal(ctx,world,t.linear().col(2));
    if(!local.ok())throw std::runtime_error("Surface local/global round trip failed");
    error=std::max(error,(local.value()-point).norm());
  }
  Json corners=Json::array();
  for(double x : {-49.999,49.999})for(double y : {-49.999,49.999})
    corners.push_back(s.bounds().inside(Acts::Vector2(x,y)));
  return {{"center_mm",vector(t.translation())},{"rotation",matrix(t)},
    {"u",vector(t.linear().col(0))},{"v",vector(t.linear().col(1))},
    {"normal",vector(t.linear().col(2))},{"bounds_type",int(s.bounds().type())},
    {"bounds_values",s.bounds().values()},{"square_interior_corner_checks",corners},
    {"round_trip_error_mm",error},{"geometry_id",s.geometryId().value()},
    {"material_assigned",s.surfaceMaterial()!=nullptr}};
}
Json hierarchy(dd4hep::DetElement element) {
  Json children=Json::array(),params=Json::array();
  for(const auto& [_,child] : element.children())children.push_back(hierarchy(child));
  if(auto* p=element.extension<dd4hep::rec::VariantParameters>(false))
    for(const auto& [key,_] : p->variantParameters)params.push_back(key);
  return {{"name",element.name()},{"path",element.path()},{"type",element.type()},
    {"type_flags",element.typeFlag()},{"volume_id",element.volumeID()},
    {"sensitive",element.volume().isSensitive()},
    {"layer_pattern",ActsPlugins::getParamOr<std::string>("layer_pattern",element,"$^")},
    {"parameter_keys",params},{"children",children}};
}
dd4hep::rec::VariantParameters& params(dd4hep::DetElement element) {
  auto* p=element.extension<dd4hep::rec::VariantParameters>(false);
  if(!p) {p=new dd4hep::rec::VariantParameters();element.addExtension<dd4hep::rec::VariantParameters>(p);}
  return *p;
}
void experimentalMetadata(dd4hep::Detector& detector,bool flags) {
  // Process-local discovery experiment only. No placement, shape or XML edits.
  for(const char* name : {"SiMAPS","MPGDPlane","ACLGADPlane"}) {
    auto det=detector.detector(name);
    params(det).set<std::string>("layer_pattern","^layer[0-6]_module[0-9]+_(pos|neg)$");
    if(flags)det.setTypeFlag(dd4hep::DetType::TRACKER|dd4hep::DetType::ENDCAP);
    for(const auto& [_,module] : det.children()) {
      auto& p=params(module);
      for(const char* key : {"envelope_r_min","envelope_r_max","envelope_z_min","envelope_z_max"})p.set<double>(key,.01);
      for(const auto& [__,sensor] : module.children())params(sensor).set<std::string>("axis_definitions","zXy");
    }
  }
}
void writeExclusive(const std::filesystem::path& path,const Json& report) {
  const int fd=::open(path.c_str(),O_WRONLY|O_CREAT|O_EXCL,0644);
  if(fd<0)throw std::runtime_error("Output must be a new writable file: "+path.string());
  const auto data=report.dump(2)+"\n";std::size_t offset=0;
  while(offset<data.size()) {
    const auto n=::write(fd,data.data()+offset,data.size()-offset);
    if(n<=0) {::close(fd);throw std::runtime_error("Cannot write Geometry report");}
    offset+=n;
  }
  ::close(fd);
}
} // namespace

int main(int argc,char** argv) {
  if(argc!=5) {
    std::cerr<<"Usage: TelescopeGeometryProbe XML OUTPUT_JSON local|official|official-elements|blueprint none|discovery|discovery-and-flags\n";
    return 64;
  }
  const std::string provider=argv[3],metadata=argv[4];
  if((provider!="local" && provider!="official" && provider!="official-elements" && provider!="blueprint") ||
     (metadata!="none" && metadata!="discovery" && metadata!="discovery-and-flags"))return 64;
  if(std::filesystem::exists(argv[2])) {std::cerr<<"Refusing existing output\n";return 64;}
  Json report={{"provider",provider},{"experimental_metadata",metadata},
    {"acts_version",{Acts::VersionMajor,Acts::VersionMinor,Acts::VersionPatch}},
    {"tracking_geometry_available",false},{"inference_enabled",false},{"component_axis_definitions","zXy"},
    {"material_map","disabled for zero-material/process-noise comparison"}};
  try {
    auto& detector=dd4hep::Detector::getInstance();
    detector.fromXML(argv[1]);detector.apply("DD4hepVolumeManager",0,nullptr);
    dd4hep::rec::CellIDPositionConverter converter(detector);
    const auto local=local_eicrecon::surfacePlacements(converter,false);
    report["original_hierarchy"]=hierarchy(detector.world());
    if(metadata!="none")experimentalMetadata(detector,metadata=="discovery-and-flags");
    report["selected_hierarchy"]=hierarchy(detector.world());
    Acts::GeometryContext context=Acts::GeometryContext::dangerouslyDefaultConstruct();
    std::shared_ptr<ActsGeometryProvider> upstream;
    std::vector<std::shared_ptr<ActsPlugins::DD4hepDetectorElement>> elements;
    std::array<const Acts::Surface*,7> surfaces{};
    std::vector<std::shared_ptr<Acts::PlaneSurface>> localSurfaces;
    std::string conversionError;
    if(provider=="official") {
      upstream=std::make_shared<ActsGeometryProvider>();
      auto log=spdlog::stdout_color_mt("official_geometry");log->set_level(spdlog::level::trace);
      try {
        upstream->initialize(&detector,"",log,log);
        if(!upstream->trackingGeometry())throw std::runtime_error("Official provider returned no TrackingGeometry");
        context=upstream->getActsGeometryContext();report["tracking_geometry_available"]=true;
      } catch(const std::exception& e) {conversionError=e.what();report["conversion_error"]=conversionError;}
    }
    std::set<uint64_t> volumeIds,geometryIds;
    for(int layer=0;layer<7;++layer) {
      const uint64_t system=layer<5?31:(layer==5?100:92);
      const uint64_t cell=system|(1ULL<<8)|(uint64_t(layer)<<11)|(1ULL<<22)|(1ULL<<28);
      const auto* volume=converter.findContext(cell);
      if(!volume || !volumeIds.insert(volume->identifier).second)throw std::runtime_error("Missing/duplicate sensitive Volume ID association");
      auto reference=Acts::Surface::makeShared<Acts::PlaneSurface>(local[layer],std::make_shared<Acts::RectangleBounds>(50.,50.));
      reference->assignGeometryId(Acts::GeometryIdentifier().withVolume(1).withLayer(layer+1).withSensitive(1));
      Json row={{"layer",layer},{"cell_id",cell},{"volume_id",volume->identifier},
        {"context_element",volume->element.path()},{"local",surfaceInfo(*reference,context)}};
      for(const uint64_t channel : {uint64_t(0),uint64_t(1)<<32,uint64_t(1)<<48})
        if(converter.findContext(cell|channel)->identifier!=volume->identifier)throw std::runtime_error("CellID channels map to different sensitive contexts");
      if(provider=="local") {
        surfaces[layer]=reference.get();localSurfaces.push_back(reference);
      } else if(provider=="official-elements" || provider=="blueprint") {
        if(!volume->element.volume().isSensitive())throw std::runtime_error("Volume context is not a sensitive DetElement");
        // Record the native missing-metadata default separately, never use it as
        // an equivalent surface for tracking or alignment.
        try {
          auto native=std::make_shared<ActsPlugins::DD4hepDetectorElement>(volume->element,ActsPlugins::TGeoAxes::parse("XYZ"),Acts::UnitConstants::cm);
          row["native_default_XYZ"]=surfaceInfo(native->surface(),context);
          row["native_default_XYZ"]["thickness_mm"]=native->thickness();
        } catch(const std::exception& e) {
          row["native_default_XYZ"]={{"conversion_error",e.what()}};
        }
        auto element=std::make_shared<ActsPlugins::DD4hepDetectorElement>(volume->element,ActsPlugins::TGeoAxes::parse("zXy"),Acts::UnitConstants::cm);
        if(element->identifier()!=volume->identifier)throw std::runtime_error("Official detector-element/Volume ID mismatch");
        surfaces[layer]=&element->surface();row["sensitive_thickness_mm"]=element->thickness();elements.push_back(element);
      } else if(conversionError.empty()) {
        const auto found=upstream->surfaceMap().find(volume->identifier);
        if(found==upstream->surfaceMap().end())throw std::runtime_error("Official TrackingGeometry has no surface for a telescope Volume ID");
        surfaces[layer]=found->second;
        if(!geometryIds.insert(surfaces[layer]->geometryId().value()).second)throw std::runtime_error("Official GeometryIdentifiers are not unique");
      }
      if(surfaces[layer]) {
        const auto& s=*surfaces[layer];row["selected"]=surfaceInfo(s,context);
        const auto t=s.localToGlobalTransform(context);
        row["center_difference_mm"]=(t.translation()-local[layer].translation()).norm();
        row["max_rotation_difference"]=(t.linear()-local[layer].linear()).cwiseAbs().maxCoeff();
        const auto a=reference->bounds().values(),b=s.bounds().values();
        bool equalBounds=a.size()==b.size() && reference->bounds().type()==s.bounds().type();
        if(equalBounds)for(std::size_t j=0;j<a.size();++j)equalBounds=equalBounds && std::abs(a[j]-b[j])<1e-12;
        row["bounds_equivalent"]=equalBounds;
        row["equivalent"]=(equalBounds && double(row["center_difference_mm"])<1e-10 && double(row["max_rotation_difference"])<1e-12 && double(row["selected"]["round_trip_error_mm"])<1e-10);
      }
      report["planes"].push_back(row);
    }
    if(provider=="blueprint") {
      auto tracking=local_eicrecon::closeTelescopeGeometry(context,elements);
      Acts::Vector3 lo=Acts::Vector3::Constant(1e100),hi=-lo;
      for(const auto* surface:surfaces) {
        const auto t=surface->localToGlobalTransform(context);
        for(double x:{-50.,50.})for(double y:{-50.,50.}) {
          const Acts::Vector3 point=surface->localToGlobal(context,{x,y},t.linear().col(2));
          lo=lo.cwiseMin(point);hi=hi.cwiseMax(point);
        }
      }
      lo.array()-=10.;hi.array()+=10.;
      std::set<const Acts::Surface*> contained;
      tracking->visitSurfaces([&](const Acts::Surface* surface){contained.insert(surface);});
      if(contained.size()!=7)throw std::runtime_error("TrackingGeometry sensitive count is not seven");
      for(const auto* surface:surfaces)
        if(!contained.contains(surface) || tracking->findSurface(surface->geometryId())!=surface)
          throw std::runtime_error("TrackingGeometry sensitive map mismatch");
      report["tracking_geometry_sensitive_count"]=contained.size();
      report["tracking_geometry_available"]=true;
      std::set<uint64_t> ids;
      for(int i=0;i<7;++i) {
        const auto id=surfaces[i]->geometryId().value();
        if(!id || !ids.insert(id).second)throw std::runtime_error("Unclosed or duplicate blueprint sensitive ID");
        report["planes"][i]["selected"]=surfaceInfo(*surfaces[i],context);
      }
      report["blueprint_world_bounds"]=tracking->highestTrackingVolume()->volumeBounds().values();
      std::shared_ptr<const Acts::TrackingGeometry> sharedTracking(std::move(tracking));
      Acts::Navigator navigator({sharedTracking,true,false,false});
      for(const auto& ray:std::vector<std::pair<Acts::Vector3,Acts::Vector3>>{
          {{0.,0.,lo.z()-5.},{0.,0.,1.}},
          {{49.,0.,lo.z()-5.},{.01,0.,1.}},
          {{hi.x()+5.,0.,lo.z()-5.},{0.,0.,1.}},
          {{0.,0.,hi.z()+5.},{0.,0.,-1.}}}) {
        auto position=ray.first;const Acts::Vector3 direction=ray.second.normalized();
        Json trial={{"start_mm",vector(position)},{"direction",vector(direction)}};
        // Independent bounded intersections determine the expected sensor order.
        std::vector<std::pair<double,int>> expected;
        for(int i=0;i<7;++i) {
          auto intersections=surfaces[i]->intersect(context,position,direction,Acts::BoundaryTolerance::None());
          const auto hit=intersections.closest();
          if(hit.isValid() && hit.pathLength()>0.)expected.emplace_back(hit.pathLength(),i);
        }
        std::sort(expected.begin(),expected.end());
        std::vector<int> expectedLayers,actualLayers;
        for(auto [_,layer]:expected)expectedLayers.push_back(layer);
        Acts::Navigator::Options navOptions(context);auto state=navigator.makeState(navOptions);
        auto initialized=navigator.initialize(state,position,direction,Acts::Direction::Forward());
        if(!initialized.ok())throw std::runtime_error("Navigator initialization failed");
        Json steps=Json::array();bool exhausted=false;
        for(int step=0;step<32;++step) {
          const auto target=navigator.nextTarget(state,position,direction);
          if(!target.isValid()) {exhausted=true;break;}
          const auto* before=navigator.currentVolume(state);
          position=target.position();
          int layer=-1;for(int i=0;i<7;++i)if(&target.surface()==surfaces[i])layer=i;
          if(layer>=0)actualLayers.push_back(layer);
          navigator.handleSurfaceReached(state,position,direction,target.surface());
          const auto* after=navigator.currentVolume(state);
          steps.push_back({{"layer",layer},{"position_mm",vector(position)},
            {"from",before?before->volumeName():"outside"},{"to",after?after->volumeName():"outside"}});
        }
        trial["expected_layers"]=expectedLayers;trial["actual_layers"]=actualLayers;
        trial["steps"]=steps;trial["exhausted"]=exhausted;
        std::set<int> uniqueLayers(actualLayers.begin(),actualLayers.end());
        bool entered=false,left=false;
        for(const auto& step:steps) {
          entered=entered || (step["from"]=="World" && step["to"]=="Telescope");
          left=left || (step["from"]=="Telescope" && step["to"]=="World");
        }
        const bool transitions=expectedLayers.empty() || (entered && left);
        trial["passed"]=exhausted && expectedLayers==actualLayers && uniqueLayers.size()==actualLayers.size()
          && transitions && !steps.empty() && steps.back()["to"]=="outside";
        report["navigation"].push_back(trial);
        if(!bool(trial["passed"]))throw std::runtime_error("Complete-geometry navigation gate failed; reconstruction prohibited");
      }
      report["status"]="Closed Gen3 TrackingGeometry; seven DD4hep surfaces and four installed-Navigator rays validated";
    }
    if(!conversionError.empty()) {
      report["passed"]=false;report["status"]="Official TrackingGeometry unavailable; production local path unchanged";
      writeExclusive(argv[2],report);return 2;
    }
    bool passed=true;for(const auto& row:report["planes"])passed=passed && bool(row["equivalent"]);
    report["passed"]=passed;
    if(provider!="blueprint")report["status"]=provider=="official-elements"?"Component surface conversion only; identifiers remain unclosed; NOT a TrackingGeometry provider":"Geometry probe only; no numerical fitter or navigation replacement";
    writeExclusive(argv[2],report);return passed?0:3;
  } catch(const std::exception& e) {
    report["passed"]=false;report["error"]=e.what();
    try {writeExclusive(argv[2],report);}catch(...){}
    std::cerr<<e.what()<<'\n';return 1;
  }
}
