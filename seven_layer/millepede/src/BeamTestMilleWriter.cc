// Origin: local implementation for seven-layer beam-test framework
// Local purpose: write official Mille binary records for five-layer SiMAPS alignment

#include "BeamTestMilleWriter.h"

#include <Mille/MilleFactory.h>
#include <Mille/MilleRecord.h>

#include <cmath>
#include <iostream>
#include <vector>

namespace local_eicrecon {

namespace {

constexpr unsigned int kLocalIndices[4] = {1U, 2U, 3U, 4U};

} // namespace

BeamTestMilleWriter::BeamTestMilleWriter(const Config& cfg) : m_cfg(cfg) {
  m_record = Mille::spawnMilleRecord(m_cfg.outputPath, m_cfg.doublePrecision, m_cfg.writeZeroDerivatives);
  if (!m_record) {
    throw std::runtime_error("failed to create Mille writer for output: " + m_cfg.outputPath);
  }
}

BeamTestMilleWriter::~BeamTestMilleWriter() {
  try {
    flush();
  } catch (...) {
  }
}

int BeamTestMilleWriter::labelAx(int layer) {
  // Stable global labels for layer-x alignment bias parameters.
  return 1000 + layer;
}

int BeamTestMilleWriter::labelAy(int layer) {
  // Stable global labels for layer-y alignment bias parameters.
  return 2000 + layer;
}

bool BeamTestMilleWriter::writeTrackRecord(const std::array<Hit2D, 5>& hits) {
  std::lock_guard<std::mutex> lock(m_mutex);
  if (!m_record) {
    return false;
  }

  std::vector<unsigned int> localIdx(std::begin(kLocalIndices), std::end(kLocalIndices));

  for (const auto& h : hits) {
    const double dz = h.z_mm - m_cfg.zRefMm;

    // x measurement equation:
    // x_meas = x0 + tx*(z-zref) + a_x[layer] + noise
    // local derivatives wrt (x0, y0, tx, ty): (1, 0, dz, 0)
    // global derivative wrt a_x[layer]: +1
    std::vector<float> dLocalX{1.0F, 0.0F, static_cast<float>(dz), 0.0F};
    std::vector<int> gLabelX{labelAx(h.layer)};
    std::vector<float> dGlobalX{1.0F};

    m_record->addData(h.x_mm, h.sigma_x_mm, localIdx, dLocalX, gLabelX, dGlobalX);

    // y measurement equation:
    // y_meas = y0 + ty*(z-zref) + a_y[layer] + noise
    // local derivatives wrt (x0, y0, tx, ty): (0, 1, 0, dz)
    // global derivative wrt a_y[layer]: +1
    std::vector<float> dLocalY{0.0F, 1.0F, 0.0F, static_cast<float>(dz)};
    std::vector<int> gLabelY{labelAy(h.layer)};
    std::vector<float> dGlobalY{1.0F};

    m_record->addData(h.y_mm, h.sigma_y_mm, localIdx, dLocalY, gLabelY, dGlobalY);
  }

  m_record->writeRecord();
  ++m_recordsWritten;
  m_measurementsWritten += 10;
  return true;
}

void BeamTestMilleWriter::flush() {
  std::lock_guard<std::mutex> lock(m_mutex);
  if (m_record) {
    m_record->flushOutputFile();
  }
}

} // namespace local_eicrecon
