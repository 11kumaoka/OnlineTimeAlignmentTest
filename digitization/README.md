# Independent Digitization

## Primary native path

The maintained `calibration.workflow` uses `digitization.native` to register
installed official EICrecon digitizers, preserve the complete Geant4 source and
project the declared five-plane RawHit input. Run
`python3 -B -m digitization.native --help` inside the fixed container for its
independent digitize/project operations. A completed `--simulation-stage` receipt
binds the input ROOT to its executed Geometry, gun, readouts and real sensor IDs.

Public-run outputs are `raw/digitization/digitized.root`,
`raw/projection/channels.root` and `raw/provenance.json`. Projection uses only
valid RawHit identities/multiplicities; all excluded events remain in the full
digitized output and selection ledger. See the
[practical User Guide](../docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md).

## Retained legacy +Z path

Run `bash environment/run.sh bash digitization/digitize.sh --result-dir result/NEW`
after steps1/2. Select a nondefault build with `--build-dir BUILD`.
Output: `step2_digitization/rawhits.edm4eic.root`, contract/config snapshots and
command/stdout/exit/completion records. No later stage is executed.
C++ algorithms remain in `localDetEICrecon/`; this task only controls execution.
The legacy production file contains EventHeader and the three standard Local RawHit
collections without SimHits/MC truth. See [the contract and commands](../docs/RAWHIT_BOUNDARY.md).
