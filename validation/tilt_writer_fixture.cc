// Validation fixture: exercise the production writer with fresh-DD4hep points.
#include "BeamTestMilleWriter.h"
#include <fstream>
#include <stdexcept>
int main(int argc,char** argv) {
  if(argc<3 || argc>5)throw std::runtime_error("Usage: fixture INPUT_TEXT OUTPUT_MILLE [LAYER [rotations|six_dof|two_rotations|two_six_dof]]");
  const int layer=argc>=4?std::stoi(argv[3]):1;
  if(layer<1 || layer>3)throw std::runtime_error("Unsupported fixture layer");
  std::ifstream input(argv[1]);local_eicrecon::BeamTestMilleWriter::Config cfg;
  cfg.outputPath=argv[2];cfg.tiltMeasurementModel=true;cfg.rxEnabled[layer]=true;cfg.ryEnabled[layer]=true;
  if(argc==5) {
    const std::string mode=argv[4];
    if(mode!="rotations" && mode!="six_dof" && mode!="two_rotations" && mode!="two_six_dof" && mode!="three_six_dof")throw std::runtime_error("Unsupported diagnostic fixture mode");
    const bool two=mode=="two_rotations" || mode=="two_six_dof";
    const bool six=mode=="six_dof" || mode=="two_six_dof" || mode=="three_six_dof";
    for(int l=1;l<=3;++l)if(l==layer || (two && l<=2) || mode=="three_six_dof") {
      cfg.rxEnabled[l]=true;cfg.ryEnabled[l]=true;cfg.rotationEnabled[l]=true;cfg.zEnabled[l]=six;
    }
  }
  for(int l=0;l<5;++l) {
    for(double& value:cfg.sensitiveCenterMm[l])input>>value;
    for(double& value:cfg.surfaceU[l])input>>value;
    for(double& value:cfg.surfaceV[l])input>>value;
  }
  int count=0;input>>count;
  if(count<=0)throw std::runtime_error("Empty fixture");
  local_eicrecon::BeamTestMilleWriter writer(cfg);
  for(int record=0;record<count;++record) {
    std::array<local_eicrecon::BeamTestMilleWriter::Hit2D,5> hits;
    for(int l=0;l<5;++l) {
      auto& h=hits[l];h.layer=l;
      input>>h.x_mm>>h.y_mm>>h.z_mm>>h.sigma_x_mm>>h.sigma_y_mm;
    }
    if(!input)throw std::runtime_error("Incomplete fixture");
    writer.writeTrackRecord(hits);
  }
}
