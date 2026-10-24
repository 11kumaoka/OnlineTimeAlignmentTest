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
