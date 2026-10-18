// Origin: local implementation for seven-layer beam-test framework
// Local purpose: write official Mille binary records for five-layer SiMAPS alignment

#pragma once

#include <array>
#include <cstddef>
#include <memory>
#include <mutex>
#include <string>

namespace Mille {
class MilleRecord;
}

namespace local_eicrecon {

class BeamTestMilleWriter {
public:
  struct Hit2D {
    int layer{-1};
    double x_mm{0.0};
    double y_mm{0.0};
    double z_mm{0.0};
    double sigma_x_mm{0.01};
    double sigma_y_mm{0.01};
  };

  struct Config {
    std::string outputPath{"seven_layer/results/local_beamtest_mille.dat"};
    double zRefMm{100.0};
    bool doublePrecision{false};
    bool writeZeroDerivatives{false};
  };

  explicit BeamTestMilleWriter(const Config& cfg);
  ~BeamTestMilleWriter();

  BeamTestMilleWriter(const BeamTestMilleWriter&) = delete;
  BeamTestMilleWriter& operator=(const BeamTestMilleWriter&) = delete;

  bool writeTrackRecord(const std::array<Hit2D, 5>& hits);
  void flush();

  std::size_t recordsWritten() const { return m_recordsWritten; }
  std::size_t measurementsWritten() const { return m_measurementsWritten; }

  static int labelAx(int layer);
  static int labelAy(int layer);

private:
  Config m_cfg;
  std::unique_ptr<Mille::MilleRecord> m_record;
  std::mutex m_mutex;
  std::size_t m_recordsWritten{0};
  std::size_t m_measurementsWritten{0};
};

} // namespace local_eicrecon
