// Origin reference: EICrecon/src/detectors/BVTX/BVTX.cc
// Source revision: 67a00864dd47c709c98b4afc2c210c3faee100b1
// Local purpose: seven-layer beam-test reconstruction plugin
// Adaptation: local namespace/factory integration for SiMAPS/MPGD/ACLGAD and local processor registration

// Local plugin host for copied EICrecon-like SiMAPS reconstruction chain.

#include <Evaluator/DD4hepUnits.h>
#include <JANA/JApplication.h>
#include <JANA/JApplicationFwd.h>
#include <iostream>
#include <memory>

#include "extensions/jana/JOmniFactoryGeneratorT.h"
#include "factories/digi/SiliconTrackerDigi_factory.h"
#include "factories/tracking/BeamTestACTSFitter_factory.h"
#include "factories/tracking/TrackerHitReconstructionNoAssoc_factory.h"
#include "factories/tracking/TrackerHitReconstruction_factory.h"
#include "processors/BeamTestEventProcessor.h"
#include "processors/BeamTestMilleProcessor.h"

extern "C" {
void InitPlugin(JApplication* app) {
  InitJANAPlugin(app);

    std::cerr << "[local_eicrecon] InitPlugin(BeamTestReco) loaded from local shared object" << std::endl;

    using namespace local_eicrecon;

  bool enabled = true;
  app->SetDefaultParameter("beamtstreco:enabled", enabled,
                           "Enable local BeamTestReco plugin chain");

  bool enableTruthDiagnosticRecHits = false;
  app->SetDefaultParameter("beamtstreco:enableTruthDiagnosticRecHits", enableTruthDiagnosticRecHits,
                           "Enable truth-assisted diagnostic TrackerHit reconstruction outputs");

    app->Add(new JOmniFactoryGeneratorT<LocalSiliconTrackerDigi_factory>(
      "LocalSiMAPSRawHits", {"EventHeader", "SiMAPSHits"},
      {"LocalSiMAPSRawHits", "LocalSiMAPSRawHitLinks", "LocalSiMAPSRawHitAssociations"},
      {
          .threshold = 0.54 * dd4hep::keV,
      },
      app));

    app->Add(new JOmniFactoryGeneratorT<LocalTrackerHitReconstructionNoAssoc_factory>(
      "LocalSiMAPSRecHits", {"LocalSiMAPSRawHits"}, {"LocalSiMAPSRecHits"},
      {
        .useTruthPositionForDiagnostics = false,
      },
      app));

      // MPGD one-layer local chain (temporary pixel-like digi path via SiliconTrackerDigi).
      app->Add(new JOmniFactoryGeneratorT<LocalSiliconTrackerDigi_factory>(
        "LocalMPGDRawHits", {"EventHeader", "MPGDHits"},
        {"LocalMPGDRawHits", "LocalMPGDRawHitLinks", "LocalMPGDRawHitAssociations"},
        {
          .threshold = 100 * dd4hep::eV, .timeResolution = 10,
        },
        app));

      app->Add(new JOmniFactoryGeneratorT<LocalTrackerHitReconstructionNoAssoc_factory>(
        "LocalMPGDRecHits", {"LocalMPGDRawHits"}, {"LocalMPGDRecHits"},
        {
          .timeResolution = 10, .useTruthPositionForDiagnostics = false,
        },
        app));

      // AC-LGAD one-layer local chain. Keep detector's approximate 1D behavior from geometry/readout settings.
      app->Add(new JOmniFactoryGeneratorT<LocalSiliconTrackerDigi_factory>(
        "LocalACLGADRawHits", {"EventHeader", "ACLGADHits"},
        {"LocalACLGADRawHits", "LocalACLGADRawHitLinks", "LocalACLGADRawHitAssociations"},
        {
          .threshold = 0.0,
          .timeResolution = 0.025,
        },
        app));

      app->Add(new JOmniFactoryGeneratorT<LocalTrackerHitReconstructionNoAssoc_factory>(
        "LocalACLGADRecHits", {"LocalACLGADRawHits"}, {"LocalACLGADRecHits"},
        {
          .timeResolution = 0.025,
          .useTruthPositionForDiagnostics = false,
        },
        app));

      if (enableTruthDiagnosticRecHits) {
        app->Add(new JOmniFactoryGeneratorT<LocalTrackerHitReconstruction_factory>(
          "LocalSiMAPSRecHitsTruthDiag", {"LocalSiMAPSRawHits", "LocalSiMAPSRawHitAssociations"},
          {"LocalSiMAPSRecHitsTruthDiag"},
          {
            .useTruthPositionForDiagnostics = true,
          },
          app));

        app->Add(new JOmniFactoryGeneratorT<LocalTrackerHitReconstruction_factory>(
          "LocalMPGDRecHitsTruthDiag", {"LocalMPGDRawHits", "LocalMPGDRawHitAssociations"},
          {"LocalMPGDRecHitsTruthDiag"},
          {
            .timeResolution = 10, .useTruthPositionForDiagnostics = true,
          },
          app));

        app->Add(new JOmniFactoryGeneratorT<LocalTrackerHitReconstruction_factory>(
          "LocalACLGADRecHitsTruthDiag", {"LocalACLGADRawHits", "LocalACLGADRawHitAssociations"},
          {"LocalACLGADRecHitsTruthDiag"},
          {
            .timeResolution = 0.025, .useTruthPositionForDiagnostics = true,
          },
          app));
      }

      app->Add(new JOmniFactoryGeneratorT<BeamTestACTSFitter_factory>(
          "LocalBeamTestTracks",
          {"LocalSiMAPSRecHits", "LocalMPGDRecHits", "LocalACLGADRecHits"},
          {"LocalBeamTestTrajectories", "LocalBeamTestTrackParameters", "LocalBeamTestTracks",
           "LocalBeamTestFitMeasurements", "LocalBeamTestPredictedMeasurements",
             "LocalBeamTestFilteredMeasurements", "LocalBeamTestSmoothedMeasurements",
             "LocalBeamTestPredictedSegments", "LocalBeamTestFilteredSegments",
             "LocalBeamTestSmoothedSegments"},
          {
              .useMPGD = true, .useACLGAD = false,
              .inputHitsAreGlobal = true, .useMuonHypothesis = true,
              .outputTrackPDG = 13, .seedQOverP = -0.2, .excludeLayerFromFit = -1,
              .alignmentTestShiftLayer = -1, .alignmentTestShiftXmm = 0.0,
          },
          app));

      // Event-level local monitoring (does not produce reconstruction collections).
      app->Add(new local_eicrecon::BeamTestEventProcessor());
      // Optional in-process Mille binary writer for alignment.
      app->Add(new local_eicrecon::BeamTestMilleProcessor());

    std::cerr << "[local_eicrecon] Registered local factories: "
          << "LocalSiliconTrackerDigi_factory -> LocalSiMAPSRawHits, "
          << "LocalTrackerHitReconstruction_factory -> LocalSiMAPSRecHits, "
          << "LocalSiliconTrackerDigi_factory -> LocalMPGDRawHits, "
          << "LocalTrackerHitReconstruction_factory -> LocalMPGDRecHits, "
          << "LocalSiliconTrackerDigi_factory -> LocalACLGADRawHits, "
          << "LocalTrackerHitReconstruction_factory -> LocalACLGADRecHits, "
          << "BeamTestACTSFitter_factory -> LocalBeamTestTracks" << std::endl;
}
}
