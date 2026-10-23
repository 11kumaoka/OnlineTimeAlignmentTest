// DD4hep sensor frames -> ACTS plane frames, in mm and a right-handed basis.
#pragma once
#include <Acts/Definitions/Algebra.hpp>
#include <Acts/Definitions/Units.hpp>
#include <DDRec/CellIDPositionConverter.h>
#include <DD4hep/VolumeManager.h>
#include <Evaluator/DD4hepUnits.h>
#include <array>
#include <cmath>
#include <iostream>
#include <iomanip>
#include <stdexcept>

namespace local_eicrecon {
inline std::array<Acts::Transform3,7> surfacePlacements(const dd4hep::rec::CellIDPositionConverter& converter, bool diagnostics=true) {
  std::array<Acts::Transform3,7> result;
  for (int layer=0; layer<7; ++layer) {
    const uint64_t system=layer<5 ? 31 : (layer==5 ? 100 : 92);
    const uint64_t id=system|(1ULL<<8)|(uint64_t(layer)<<11)|(1ULL<<22)|(1ULL<<28);
    const auto* context=converter.findContext(id);
    if (!context) throw std::runtime_error("No DD4hep sensitive context for telescope layer");
    auto world=[&](double x,double y,double z) -> Acts::Vector3 {
      const auto p=context->localToWorld(dd4hep::Position(x,y,z));
      return Acts::Vector3(p.x(),p.y(),p.z())/dd4hep::mm*Acts::UnitConstants::mm;
    };
    const Acts::Vector3 origin=world(0,0,0);
    // Installed Endcap2 sensor axes: sensor X -> global Y, sensor Z -> -global X.
    Acts::Vector3 u=(origin-world(0,0,dd4hep::mm)).normalized();
    Acts::Vector3 v=(world(dd4hep::mm,0,0)-origin).normalized();
    Acts::Vector3 n=u.cross(v).normalized();
    Acts::RotationMatrix3 rotation;
    rotation.col(0)=u;rotation.col(1)=v;rotation.col(2)=n;
    // Remove trig roundoff for exact nominal/translation-only basis equivalence.
    for(int row=0;row<3;++row)for(int col=0;col<3;++col) {
      if(std::abs(rotation(row,col))<1e-12)rotation(row,col)=0;
      if(std::abs(rotation(row,col)-1)<1e-12)rotation(row,col)=1;
      if(std::abs(rotation(row,col)+1)<1e-12)rotation(row,col)=-1;
    }
    result[layer]=Acts::Transform3::Identity();
    result[layer].linear()=rotation;result[layer].translation()=origin;
    if (diagnostics) {
    const auto precision = std::cerr.precision();
    std::cerr << std::setprecision(17) << "BeamTestGeometry layer=" << layer << " center_mm=" << origin.transpose()
              << " u=" << rotation.col(0).transpose() << " v=" << rotation.col(1).transpose()
              << " n=" << rotation.col(2).transpose() << std::endl;
    std::cerr.precision(precision);
    }
  }
  return result;
}
} // namespace local_eicrecon
