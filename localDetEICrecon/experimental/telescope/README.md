> Start here: [alignment user guide](../../../docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md),
> [code and upstream map](../../../docs/TELESCOPE_ALIGNMENT_CODE_MAP.md), and
> [reproduction record](../../../docs/BARREL_ALIGNMENT_VALIDATION.md).
> The earlier reports below describe their historical milestones; the current
> original validated channel closure uses L1/L2 Global Y, zero field and no ACTS material.
> The selected native L1 Global Rx and combined Y/Rx milestone is described in the
> [parity report](../../../docs/TELESCOPE_ALIGNMENT_LEGACY_PARITY.md); no general six-DOF scope is implied.

# Experimental EICrecon telescope factory chain

This isolated plugin follows pinned EICrecon source-level module boundaries.
It is not the production BeamTestReco/Alignment path.

See [the validation and source comparison](../../../docs/BARREL_FACTORY_RECONSTRUCTION.md)
for exact commands, provenance, collection contracts, results and limitations.

Copied modules retain their upstream headers. `LICENSE.LGPL3` and `NOTICE.md`
are copied from EICrecon revision
`195966d41899800eaeca6fbafd63cd53735e6543`.
`provenance.json` pins the original file hashes; `upstream_diffs/` contains
reproducible unified diffs, including an empty diff for the unchanged,
non-installed covariance-unit helper. Installed components are linked rather
than duplicated. Local classes use `eicrecon::telescope` to avoid symbol clashes.

The optional `TELESCOPE_BUILD_MILLE_PROBE=ON` targets add a separate native-state
Mille observer and mathematical tests. See [the native Mille integration report](../../../docs/BARREL_NATIVE_MILLE_INTEGRATION.md).
This does not enable alignment in the production plugin or activate Geometry.

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
