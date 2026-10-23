# Incoming RawHit deliveries

This directory is input-only. No reconstruction or calibration results belong here.
ROOT files, sidecars, temporary files and readiness manifests are ignored by Git.

The prototype controller accepts a ROOT file, its existing RawHit contract, and a
final `*.ready.json` delivery manifest. Producers close files, atomically rename
them to final names, then atomically publish the manifest last. Existence alone
is not readiness. Published files must remain immutable and retained.

This is a local prototype delivery interface, not an assumed E0 transport protocol.
See [the controller guide](../calibration/README.md) for schema, commands and limits.
