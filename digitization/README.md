# Independent Digitization

Run `bash environment/run.sh bash digitization/digitize.sh --result-dir result/NEW`
after steps1/2. Select a nondefault build with `--build-dir BUILD`.
Output: `step2_digitization/rawhits.edm4eic.root`, contract/config snapshots and
command/stdout/exit/completion records. No later stage is executed.
C++ algorithms remain in `localDetEICrecon/`; this task only controls execution.
The production file contains EventHeader and the three standard Local RawHit
collections without SimHits/MC truth. See [the contract and commands](../docs/RAWHIT_BOUNDARY.md).
