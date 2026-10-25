# Native EICrecon telescope plugins

This directory supplies the C++ plugins for the primary public workflow:
`python3 -B -m calibration.workflow run`. The historical `experimental/telescope`
path remains stable. Follow the [practical user guide](../../../docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md)
for setup, native CMake commands, example configurations, inputs/outputs and ROOT
diagnostics. The [code map](../../../docs/TELESCOPE_ALIGNMENT_CODE_MAP.md) identifies
upstream components and telescope-specific adapters; the
[current validation report](../../../docs/NATIVE_WORKFLOW_VALIDATION.md) records
executed tests and limitations.

The public chain uses `TelescopeDigitization`, `TelescopeTracking` and
`TelescopeMille`: npsim/Geant4 input, official digitization, immutable RawHits,
native ACTS tracking, official Pede, checked Geometry Correction and fresh
reconstruction. Configure this directory with `TELESCOPE_BUILD_MILLE_PROBE=ON`
for the complete chain. ACTS remains zero-field and material-free; technical
completion does not establish physics-quality validation. Candidate Geometry
remains unapproved and is never activated automatically.

The retained +Z `BeamTestReco` backend has its own
[build and workflow](../../README.md). Its historical inputs and coordinate
conventions remain separate from this native +X telescope.

## Source provenance

These plugins follow pinned EICrecon source-level module boundaries.

Copied modules retain their upstream headers. `LICENSE.LGPL3` and `NOTICE.md`
are copied from EICrecon revision
`195966d41899800eaeca6fbafd63cd53735e6543`.
`provenance.json` pins the original file hashes; `upstream_diffs/` contains
reproducible unified diffs, including an empty diff for the unchanged,
non-installed covariance-unit helper. Installed components are linked rather
than duplicated. Local classes use `eicrecon::telescope` to avoid symbol clashes.

## Historical fixtures and validation

The reports below describe their original milestones. The
[fixture manual](../../../docs/NATIVE_FIXTURE_PROTOCOLS.md) preserves independent
synthetic closure and signed-rotation/SO(3) protocols. Current supported parameter
scopes and validation limits are listed in the practical guide; no general
six-DOF scope is implied by this directory name.

See [the original factory validation](../../../docs/BARREL_FACTORY_RECONSTRUCTION.md)
and [early alignment reproduction record](../../../docs/BARREL_ALIGNMENT_VALIDATION.md)
for their exact commands, provenance and collection contracts. The earlier L1
Global Rx and combined Y/Rx milestones are retained in the
[parity report](../../../docs/TELESCOPE_ALIGNMENT_LEGACY_PARITY.md).

The original `TELESCOPE_BUILD_MILLE_PROBE=ON` development milestone introduced
the native-state Mille observer and mathematical tests; see the
[native Mille integration report](../../../docs/BARREL_NATIVE_MILLE_INTEGRATION.md).
The option now builds the native Mille components required by the public workflow
alongside those retained tests.

The [channel-based alignment closure](../../../docs/BARREL_CHANNEL_ALIGNMENT_CLOSURE.md)
reconstructs 32 immutable five-SiMAPS channel events through nominal and corrected
DD4hep Geometry, using the installed official TrackerHitReconstruction factory.
`TelescopeTracking:channelInput=true` and the explicit multi-event observer modes
select this workflow; the original one-event benchmark remains the default.

## Geometry terminology

This is a beam-test telescope study, not an ePIC barrel detector. The pinned
ACTS DD4hep converter requires a paired endcap and cannot build this single-sided
telescope through its endcap path. The current representation therefore uses
real Tube layer envelopes and `DD4hep_SiTrackerBarrel` with one real planar module
per layer. Installed `ActsGeometryProvider` builds the TrackingGeometry and
SurfaceMap through its barrel conversion. `TestbenchBarrelMetadata` retains its
technical name because it supplies metadata specific to those envelopes.
No dummy detector, replacement provider, navigator or fitter is introduced.
Historical `BARREL_*` reports and result paths retain their original names.
