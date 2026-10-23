//==========================================================================
//  AIDA Detector description implementation 
//--------------------------------------------------------------------------
// Copyright (C) Organisation europeenne pour la Recherche nucleaire (CERN)
// All rights reserved.
//
// For the licensing terms see $DD4hepINSTALL/LICENSE.
// For the list of contributors see $DD4hepINSTALL/doc/CREDITS.
//
// Author     : M.Frank
//
//==========================================================================
//
// Specialized generic detector constructor
// 
//==========================================================================
// Adapted from DD4hep v01-36 DDDetectors/src/SiTrackerEndcap2_geo.cpp.
// Adds Global Y translation and center-preserving SiMAPS L1/L2/L3 Global Z rotation.
#include "DD4hep/DetFactoryHelper.h"
#include <map>
#include <cmath>

using namespace std;
using namespace dd4hep;
using namespace dd4hep::detail;

static Ref_t create_detector(Detector& description, xml_h e, SensitiveDetector sens)  {
  typedef vector<PlacedVolume> Placements;
  xml_det_t   x_det     = e;
  Material    vacuum    = description.vacuum();
  int         det_id    = x_det.id();
  string      det_name  = x_det.nameStr();
  bool        reflect   = x_det.reflect(false);
  DetElement  sdet        (det_name,det_id);
  Assembly    assembly    (det_name);
  //Volume      assembly    (det_name,Box(10000,10000,10000),vacuum);
  Volume      motherVol = description.pickMotherVolume(sdet);
  int         c_id=0, n_sensor=0;
  map<string,Volume> modules;
  map<string, Placements>  sensitives;
  PlacedVolume pv;

  assembly.setVisAttributes(description.invisible());
  sens.setType("tracker");

  for(xml_coll_t mi(x_det,_U(module)); mi; ++mi)  {
    xml_comp_t x_mod   = mi;
    string     m_nam   = x_mod.nameStr();
    xml_comp_t trd     = x_mod.trd();
    double     posY;
    double     x1      = trd.x1();
    double     x2      = trd.x2();
    double     z       = trd.z();
    double     y1, y2, total_thickness=0.;
    xml_coll_t ci(x_mod,_U(module_component));
    for(ci.reset(), total_thickness=0.0; ci; ++ci)
      total_thickness += xml_comp_t(ci).thickness();
      
    y1 = y2 = total_thickness / 2;
    Volume  m_volume(m_nam, Trapezoid(x1, x2, y1, y2, z), vacuum);      
    m_volume.setVisAttributes(description.visAttributes(x_mod.visStr()));

    for(ci.reset(), n_sensor=1, c_id=0, posY=-y1; ci; ++ci, ++c_id)  {
      xml_comp_t c       = ci;
      double     c_thick = c.thickness();
      Material   c_mat   = description.material(c.materialStr());
      string     c_name  = _toString(c_id,"component%d");
      Volume     c_vol(c_name, Trapezoid(x1,x2,c_thick/2e0,c_thick/2e0,z), c_mat);

      c_vol.setVisAttributes(description.visAttributes(c.visStr()));
      pv = m_volume.placeVolume(c_vol,Position(0,posY+c_thick/2,0));
      if ( c.isSensitive() ) {
        sdet.check(n_sensor > 2,"SiTrackerEndcap2::fromCompact: "+c_name+" Max of 2 modules allowed!");
        pv.addPhysVolID("sensor",n_sensor);
        c_vol.setSensitiveDetector(sens);
        sensitives[m_nam].push_back(pv);
        ++n_sensor;
      }
      posY += c_thick;
    }
    modules[m_nam] = m_volume;
  }
  
  for(xml_coll_t li(x_det,_U(layer)); li; ++li)  {
    xml_comp_t  x_layer(li);
    int l_id    = x_layer.id();
    int mod_num = 1;
    for(xml_coll_t ri(x_layer,_U(ring)); ri; ++ri)  {
      xml_comp_t x_ring = ri;
      double r        = x_ring.r();
      double phi0     = x_ring.phi0(0);
      double zstart   = x_ring.zstart();
      double dz       = x_ring.dz(0);
      int    nmodules = x_ring.nmodules();
      string m_nam    = x_ring.moduleStr();
      Volume m_vol    = modules[m_nam];
      double iphi     = 2*M_PI/nmodules;
      double phi      = phi0;
      Placements& sensVols = sensitives[m_nam];

      for(int k=0; k<nmodules; ++k) {
        string m_base = _toString(l_id,"layer%d") + _toString(mod_num,"_module%d");
        double x = -r*std::cos(phi);
        double y = -r*std::sin(phi);
        if (x_ring.hasAttr(_Unicode(global_y))) y += x_ring.attr<double>(_Unicode(global_y));
        DetElement module(sdet,m_base+"_pos",det_id);
        // Left-compose Global +Z orientation about the module center; do not rotate its position.
        double globalRz = x_ring.hasAttr(_Unicode(global_rz)) ? x_ring.attr<double>(_Unicode(global_rz)) : 0.;
        if (globalRz != 0. && ((l_id < 1 || l_id > 3) || nmodules != 1 || phi != 0.))
          throw std::runtime_error("Global Rz currently supports the single SiMAPS L1/L2/L3 modules only");
        const double globalRx=x_ring.hasAttr(_Unicode(global_rx))?x_ring.attr<double>(_Unicode(global_rx)):0.;
        const double globalRy=x_ring.hasAttr(_Unicode(global_ry))?x_ring.attr<double>(_Unicode(global_ry)):0.;
        Rotation3D correction=Rotation3D(RotationZ(globalRz))*Rotation3D(RotationY(globalRy))*Rotation3D(RotationX(globalRx));
        const char* matrixNames[9]={"global_r00","global_r01","global_r02","global_r10","global_r11","global_r12","global_r20","global_r21","global_r22"};
        double matrix[9];int count=0;
        for(int i=0;i<9;++i)if(x_ring.hasAttr(xml::Strng_t(matrixNames[i]))) {
          matrix[i]=x_ring.attr<double>(xml::Strng_t(matrixNames[i]));++count;
        }
        if(count) {
          if(count!=9 || x_ring.hasAttr(_Unicode(global_rx)) || x_ring.hasAttr(_Unicode(global_ry)) || x_ring.hasAttr(_Unicode(global_rz)))
            throw std::runtime_error("Expected a complete, unmixed Global rotation matrix");
          for(int i=0;i<9;++i)if(!std::isfinite(matrix[i]))throw std::runtime_error("Non-finite Global rotation matrix");
          for(int i=0;i<3;++i)for(int j=0;j<3;++j) {
            double dot=0.;for(int k=0;k<3;++k)dot+=matrix[3*k+i]*matrix[3*k+j];
            if(std::abs(dot-(i==j?1.:0.))>1.e-12)throw std::runtime_error("Non-orthonormal Global rotation matrix");
          }
          const double determinant=matrix[0]*(matrix[4]*matrix[8]-matrix[5]*matrix[7])-matrix[1]*(matrix[3]*matrix[8]-matrix[5]*matrix[6])+matrix[2]*(matrix[3]*matrix[7]-matrix[4]*matrix[6]);
          if(std::abs(determinant-1.)>1.e-12)throw std::runtime_error("Improper Global rotation matrix");
          correction=Rotation3D(matrix[0],matrix[1],matrix[2],matrix[3],matrix[4],matrix[5],matrix[6],matrix[7],matrix[8]);
        }
        if((count || globalRx!=0. || globalRy!=0.) && (det_name!="SiMAPS" || (l_id<1 || l_id>3) || nmodules!=1 || phi!=0. || reflect || sensVols.size()!=1 || sensVols.front().position().Mag2()>1.e-24))
          throw std::runtime_error("Tilt placement requires one centered sensitive SiMAPS L1/L2/L3 module without reflection");
        if(std::abs(globalRx)>.1 || std::abs(globalRy)>.1)throw std::runtime_error("Tilt placement exceeds 0.1 rad validation envelope");
        // Global correction acts about the current centered sensitive element.
        Rotation3D orientation = correction * Rotation3D(RotationZYX(0,-M_PI/2-phi,-M_PI/2));
        pv = assembly.placeVolume(m_vol,Transform3D(orientation,Position(x,y,zstart+dz+(x_ring.hasAttr(_Unicode(global_z)) ? x_ring.attr<double>(_Unicode(global_z)) : 0.))));
        pv.addPhysVolID("barrel",1).addPhysVolID("layer", l_id).addPhysVolID("module",mod_num);
        module.setPlacement(pv);
        for(size_t ic=0; ic<sensVols.size(); ++ic)  {
          PlacedVolume sens_pv = sensVols[ic];
          DetElement comp_elt(module,sens_pv.volume().name(),mod_num);
          comp_elt.setPlacement(sens_pv);
        }

        if ( reflect ) {
          pv = assembly.placeVolume(m_vol,Transform3D(RotationZYX(M_PI,-M_PI/2-phi,-M_PI/2),Position(x,y,-zstart-dz)));
          pv.addPhysVolID("barrel",2).addPhysVolID("layer",l_id).addPhysVolID("module",mod_num);
          DetElement r_module(sdet,m_base+"_neg",det_id);
          r_module.setPlacement(pv);
          for(size_t ic=0; ic<sensVols.size(); ++ic)  {
            PlacedVolume sens_pv = sensVols[ic];
            DetElement comp_elt(r_module,sens_pv.volume().name(),mod_num);
            comp_elt.setPlacement(sens_pv);
          }
        }
        dz   = -dz;
        phi += iphi;
        ++mod_num;
      }
    }
  }
  pv = motherVol.placeVolume(assembly);
  pv.addPhysVolID("system",det_id);
  sdet.setPlacement(pv);
  return sdet;
}

DECLARE_DETELEMENT(Local_SiTrackerEndcap2XY,create_detector)

