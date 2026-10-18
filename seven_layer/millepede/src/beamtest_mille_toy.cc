// Origin: local implementation for seven-layer beam-test framework
// Local purpose: generate synthetic five-plane tracks and write official Mille binary for closure tests

#include "BeamTestMilleWriter.h"

#include <array>
#include <cmath>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace {

struct ToyConfig {
  std::string outputDat;
  int nTracks{2000};
  double zRefMm{100.0};
  double sigmaMm{0.01};
  double axL1{0.0};
  double ayL1{0.0};
  double axL2{0.0};
  double ayL2{0.0};
  double axL3{0.0};
  double ayL3{0.0};
  uint64_t seed{123456789ULL};
};

bool startsWith(const std::string& s, const std::string& p) {
  return s.rfind(p, 0) == 0;
}

ToyConfig parseArgs(int argc, char** argv) {
  ToyConfig cfg;
  for (int i = 1; i < argc; ++i) {
    const std::string a(argv[i]);
    auto nextDouble = [&](double& x) {
      if (i + 1 < argc) {
        x = std::stod(argv[++i]);
      }
    };
    auto nextInt = [&](int& x) {
      if (i + 1 < argc) {
        x = std::stoi(argv[++i]);
      }
    };
    auto nextStr = [&](std::string& x) {
      if (i + 1 < argc) {
        x = argv[++i];
      }
    };

    if (a == "--output") {
      nextStr(cfg.outputDat);
    } else if (a == "--tracks") {
      nextInt(cfg.nTracks);
    } else if (a == "--zref") {
      nextDouble(cfg.zRefMm);
    } else if (a == "--sigma") {
      nextDouble(cfg.sigmaMm);
    } else if (a == "--axL1") {
      nextDouble(cfg.axL1);
    } else if (a == "--ayL1") {
      nextDouble(cfg.ayL1);
    } else if (a == "--axL2") {
      nextDouble(cfg.axL2);
    } else if (a == "--ayL2") {
      nextDouble(cfg.ayL2);
    } else if (a == "--axL3") {
      nextDouble(cfg.axL3);
    } else if (a == "--ayL3") {
      nextDouble(cfg.ayL3);
    } else if (a == "--seed") {
      if (i + 1 < argc) {
        cfg.seed = static_cast<uint64_t>(std::stoull(argv[++i]));
      }
    }
  }
  return cfg;
}

} // namespace

int main(int argc, char** argv) {
  auto cfg = parseArgs(argc, argv);
  if (cfg.outputDat.empty()) {
    std::cerr << "Usage: beamtest_mille_toy --output <file.dat> [--tracks N] [--sigma mm]"
                 " [--axL1 mm --ayL1 mm --axL2 mm --ayL2 mm --axL3 mm --ayL3 mm] [--seed N]"
              << std::endl;
    return 2;
  }

  std::array<double, 5> zmm{0.0, 50.0, 100.0, 150.0, 200.0};
  std::array<double, 5> ax{0.0, cfg.axL1, cfg.axL2, cfg.axL3, 0.0};
  std::array<double, 5> ay{0.0, cfg.ayL1, cfg.ayL2, cfg.ayL3, 0.0};

  local_eicrecon::BeamTestMilleWriter::Config wcfg;
  wcfg.outputPath = cfg.outputDat;
  wcfg.zRefMm = cfg.zRefMm;
  local_eicrecon::BeamTestMilleWriter writer(wcfg);

  std::mt19937_64 rng(cfg.seed);
  std::normal_distribution<double> dX0(0.0, 0.20);
  std::normal_distribution<double> dY0(0.0, 0.20);
  std::normal_distribution<double> dTx(0.0, 0.020);
  std::normal_distribution<double> dTy(0.0, 0.020);
  std::normal_distribution<double> dNoise(0.0, cfg.sigmaMm);

  for (int it = 0; it < cfg.nTracks; ++it) {
    const double x0 = dX0(rng);
    const double y0 = dY0(rng);
    const double tx = dTx(rng);
    const double ty = dTy(rng);

    std::array<local_eicrecon::BeamTestMilleWriter::Hit2D, 5> hits;
    for (int layer = 0; layer < 5; ++layer) {
      const double dz = zmm[layer] - cfg.zRefMm;
      const double xMeas = x0 + tx * dz + ax[layer] + dNoise(rng);
      const double yMeas = y0 + ty * dz + ay[layer] + dNoise(rng);
      hits[layer] = local_eicrecon::BeamTestMilleWriter::Hit2D{
          layer, xMeas, yMeas, zmm[layer], cfg.sigmaMm, cfg.sigmaMm};
    }
    writer.writeTrackRecord(hits);
  }

  writer.flush();

  std::cout << "[beamtest_mille_toy] wrote tracks=" << cfg.nTracks
            << " records=" << writer.recordsWritten()
            << " measurements=" << writer.measurementsWritten() << std::endl;
  std::cout << "[beamtest_mille_toy] injected offsets mm: "
            << "ax(L1,L2,L3)=(" << cfg.axL1 << "," << cfg.axL2 << "," << cfg.axL3 << ") "
            << "ay(L1,L2,L3)=(" << cfg.ayL1 << "," << cfg.ayL2 << "," << cfg.ayL3 << ")"
            << std::endl;

  return 0;
}
