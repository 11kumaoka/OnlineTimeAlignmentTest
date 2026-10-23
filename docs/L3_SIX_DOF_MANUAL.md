# Manual SiMAPS L1/L2/L3 six-DOF test

The explicit modes are `l3_six_dof` (six parameters, all other planes fixed)
and `l1_l2_l3_six_dof` (18 parameters, L0/L4 fixed). These are implementation
prototypes for controlled manual studies, **not statistically certified alignment**.
Only five SiMAPS measurements enter tracking. MPGD/AC-LGAD placements remain
unchanged and their hits do not enter the fit. Existing modes/defaults remain available.
See [the implementation checkpoint](L3_SIX_DOF_IMPLEMENTATION.md) for executed
checks and [Geometry conventions](GEOMETRY_CONVENTIONS.md) for frames and signs.

## Shell and immutable output directories

Commands below run inside the initialized EIC container. From the host:

```sh
# WRITES OUTPUT: initializes the wrapper's result/.environment directory.
TESTBENCH_CONTAINER=sweet_mahavira bash environment/run.sh bash
```

Use an available container name or the pinned image documented in the main README.
Inside that shell:

```sh
# CHECK-ONLY: choose unused paths; prevent Python import-cache writes.
export PYTHONDONTWRITEBYTECODE=1
export STUDY=result/manual_l3_001
export BUILD=build/manual_l3_001
export TESTBENCH_BUILD_DIR=/work/$BUILD
export MODE=l1_l2_l3_six_dof
export CASE=$STUDY/data
export SURVEY=$STUDY/survey/step1/misaligned.xml
export GATE=$STUDY/gate.json
set -euo pipefail
test ! -e "$STUDY" && test ! -e "$BUILD"
# WRITES OUTPUT: new build only; requires EICrecon/DD4hep/ACTS and external/install.
bash environment/build.sh
# WRITES OUTPUT: reserve the study directory. mkdir refuses existing paths.
mkdir "$STUDY"
```

Each stage creates its own output directory exclusively and refuses existing
complete **or partial** stages. Never delete a failed stage to retry: choose a
new study directory. Changing a pinned Controller dependency requires a new state.
All commands below generate outputs unless explicitly marked CHECK-ONLY.

## 1. Geometry Preparation

```sh
# WRITES OUTPUT: physical input scenario and DD4hep GDML placement QA.
python3 -m geometry.prepare --result-dir "$CASE" \
  --geometry-config geometry/scenarios/l1_l2_l3_six_dof.json
# WRITES OUTPUT: approximate Survey, independently prepared from nominal.
python3 -m geometry.prepare --result-dir "$STUDY/survey" \
  --geometry-config geometry/scenarios/l1_l2_l3_six_dof_survey.json
# CHECK-ONLY
cat "$CASE/step1/geometry_config.json" "$CASE/step1/placement_check.json"
cat "$STUDY/survey/step1/placement_check.json"
```

`step1/nominal.xml` is an unchanged copy; `misaligned.xml` is the selected
physical placement. Each preparation includes `*_qa/geometry.gdml` and an
immutable `complete.json`. Scenario angles specify initial `Rz Ry Rx` in
radians; subsequent corrections use full matrices and SO(3), never Euler sums.

The combined example uses `(X,Y,Z,Rx,Ry,Rz)`:

| Layer | X [mm] | Y [mm] | Z offset [mm] | Rx [rad] | Ry [rad] | Rz [rad] |
|---|---:|---:|---:|---:|---:|---:|
| L1 | .020 | -.015 | .200 | .015 | -.012 | .008 |
| L2 | -.025 | .020 | -.150 | -.012 | .010 | -.006 |
| L3 | .030 | -.020 | .200 | .012 | -.010 | .007 |

Survey examples use X=.005/Y=-.005/Z=.05 mm and Rx=.001/Ry=-.001/Rz=.0005 rad
on selected layers only. These are deliberately smaller than previous controlled
six-DOF offsets. Their use does not establish a general capture range. Empty
`*_reference.json` configurations are scope/reference inputs, not physical Truth.
For L3-only testing set MODE=l3_six_dof and replace both scenario filenames with
`l3_six_dof.json` and `l3_six_dof_survey.json`; keep the same independent stages.

## 2. Simulation

```sh
# WRITES OUTPUT: 100 electrons, 1 GeV, gun mean (0,0,-500) mm.
python3 -m simulation.simulate --result-dir "$CASE" \
  --config simulation/configs/electron_1GeV.json
# CHECK-ONLY: inspect exact seed and physics input snapshot.
cat "$CASE/step2/config.json" "$CASE/step2/complete.json"
```

Output: `step2/events.edm4hep.root`, `command.json`, `stdout.log`. To change
statistics or seed, copy the configuration into the **new** study and edit only
those declared fields before invoking Simulation. Record the copy as the input.
Do not reuse a ROOT file generated with different physical placements.

## 3. Digitization and RawHits

```sh
# WRITES OUTPUT: unchanged Digitization using the physical Geometry.
python3 -m digitization.digitize --result-dir "$CASE" --build-dir "$BUILD"
# CHECK-ONLY
cat "$CASE/step2_digitization/complete.json"
sha256sum "$CASE/step2_digitization/rawhits.edm4eic.root"
```

Output: `step2_digitization/rawhits.edm4eic.root` and `rawhit_contract.json`.
Keep these bytes fixed throughout all corrections. The contract checks readout,
CellIDs, topology and producer conditions; physical Truth provenance is optional
and never supplies alignment corrections.

## 4. Version-matched derivative gate (before inference)

An existing gate can be reused only with its **exact** source, plugin and factory.
The historical SO(3) `gate_release.json` is not valid for an L3 build.
To generate limited implementation evidence for this build:

```sh
# WRITES OUTPUT: representative mixed-orientation, six-column physical checks.
for layer in 1 2 3; do
  python3 -m validation.validate_tilt_derivatives --coupled --representative \
    --layer "$layer" --build-dir "$BUILD" --output "$STUDY/derivatives_L$layer"
done
# WRITES OUTPUT: mathematical fixture only, official writer/Pede/correction.
# This is not a Geant4 campaign. Scale controls injected translations, not errors.
python3 -m validation.so3_closure \
  --writer-fixture "$STUDY/derivatives_L3/writer_fixture" \
  --output "$STUDY/noiseless" --translation-scale .25 \
  --three-layer-survey-fraction .5
# WRITES OUTPUT: immutable evidence, pinned to this source and build.
python3 -m validation.merge_so3_evidence --build-dir "$BUILD" \
  --derivative-report "$STUDY/derivatives_L1/report.json" \
  --derivative-report "$STUDY/derivatives_L2/report.json" \
  --derivative-report "$STUDY/derivatives_L3/report.json" \
  --noiseless "$STUDY/noiseless" --output "$GATE"
# WRITES OUTPUT: explicit local policy; shipped templates remain disabled.
python3 - <<'PY'
import json,os
from pathlib import Path
mode=os.environ['MODE'];study=Path(os.environ['STUDY'])
c=json.loads(Path(f'calibration/config/{mode}_demo.json').read_text())
c['build_dir']=os.environ['BUILD'];c['fallback_geometry']=os.environ['SURVEY']
c['calibration']['tilt_derivative_report']=os.environ['GATE']
with (study/'controller.json').open('x') as f:json.dump(c,f,indent=2)
PY
# CHECK-ONLY: settings.load verifies proof hashes, selected labels, canonical
# steering and source/plugin/factory consistency; no Controller state is opened.
python3 -c 'import os; from pathlib import Path; from calibration.settings import load; c,h=load(Path(os.environ["STUDY"])/"controller.json"); print(c["calibration"],h)'
```

Inspect every report's `passed`, checked labels, physical/binary errors and
source hashes. Missing/stale evidence must stop the study. `--representative`
checks one mixed orientation, three channels, three slopes and epsilon=1e-4
(mm for translations, rad for rotations). Omit it for the full pre-existing suite.
The three-layer mathematical fixture explicitly starts from half of the target orientation in its approximate Survey; the nominal-orientation start has a preserved Pede rejection failure. This controls capture range without changing errors or steering. The gate establishes technical consistency, not accuracy or uncertainty coverage.

## 5. Survey reconstruction and Mille Binary

```sh
# WRITES OUTPUT: RawHit-only Hit Reconstruction, ACTS fitting and official Mille.
python3 -m reconstruction.reconstruct --result-dir "$CASE" \
  --geometry "$SURVEY" --build-dir "$BUILD" --alignment-mode "$MODE"
# WRITES OUTPUT: actual-row rank/information diagnostic; stop if it fails.
python3 -m validation.tilt_observability --mille "$CASE/step3/mille.dat" \
  --mode "$MODE" --max-sigma-rad .01 --max-sigma-mm .5 \
  --output "$CASE/tilt_observability.json"
# WRITES OUTPUT: actual DD4hep/RecHit/ACTS/covariance consistency report.
python3 -m validation.geometry_probe --geometry "$SURVEY" \
  --reco "$CASE/step3/reco.root" --log "$CASE/step3/stdout.log" \
  --check-track-points --output "$STUDY/survey_geometry.json"
# CHECK-ONLY
cat "$CASE/step3/complete.json" "$CASE/tilt_observability.json"
```

Outputs: `step3/reco.root`, `mille.dat`, stdout and immutable provenance. Expect
one record and ten scalar measurements per accepted five-plane track. Inspect
accepted tracks, the selected **actual** rank (18 or 6), eigenvalues, correlations,
weak vectors and nominal sigma by label. Formal sigma limits here are provisional
sensitivity guards, not calibrated confidence intervals. A full rank at one
sample/Geometry does not guarantee universal observability or robust closure.

## 6. Official Millepede-II

```sh
# WRITES OUTPUT: dedicated constrained steering; unchanged official solver settings.
python3 -m alignment.align --result-dir "$CASE" --steering "alignment/pede_$MODE.txt"
# CHECK-ONLY
cat "$CASE/step4/millepede.end" "$CASE/step4/millepede.res"
grep -E 'rank defect|reject|Chi|chi' "$CASE/step4/millepede.log"
```

Output: `step4/millepede.res`, `.log`, `.end`, complete marker. Check process exit,
Pede end status/warnings, local rejections and all selected finite nominal errors.
Inspect residual/pull behavior yourself; no error scaling is performed.

## 7. Geometry Correction

```sh
# WRITES OUTPUT: one correction of the CURRENT reconstruction Geometry.
python3 -m correction.correct_geometry --result-dir "$CASE" --mode "$MODE" \
  --base-geometry "$SURVEY" --reference-geometry "$SURVEY"
# CHECK-ONLY
cat "$CASE/step5/complete.json"
```

Output: `step5/corrected.xml`. Physical `(dx,dy,dz)=(-p1000,-p2000,+p4000)` mm,
`w=(+p5000,+p6000,-p3000)` rad; `Rnew=Exp([w]x) Rcurrent`, center becomes
`c+d`. Full matrices are serialized; unselected placements/material/readout
remain fixed. For another independent iteration use a **new** result directory,
prepare its reference/scope stage, reuse the exact same RawHits with
`--raw-input`/`--raw-metadata`, and use this corrected XML as the next current
Geometry. Never restart each correction from nominal or sum Euler angles.

## 8. Corrected reconstruction

```sh
# WRITES OUTPUT: same RawHit bytes, config snapshot and exact corrected XML.
python3 -m reconstruction.reconstruct --result-dir "$CASE" --after \
  --build-dir "$BUILD" --alignment-mode "$MODE"
# CHECK-ONLY: input hashes must agree; Geometry hashes must match the selected XMLs.
cat "$CASE/step3/complete.json" "$CASE/step6/complete.json"
sha256sum "$CASE/step2_digitization/rawhits.edm4eic.root"
```

Output: `step6/reco.root` and `mille.dat`. A single correction is an integration
step, not necessarily convergence. Never add successive-fit nominal errors as
though repeated fits of these RawHits were statistically independent.

## 9. Validation and ROOT visualization

```sh
# WRITES OUTPUT: exact corrected surface/RecHit/covariance consistency.
python3 -m validation.geometry_probe --geometry "$CASE/step5/corrected.xml" \
  --reco "$CASE/step6/reco.root" --log "$CASE/step6/stdout.log" \
  --check-track-points --output "$STUDY/corrected_geometry.json"
# WRITES OUTPUT: existing ROOT renderer, independent-stage interface.
python3 -m visualization.tilt_alignment --case "$CASE" --manual-run "$CASE" \
  --survey "$SURVEY" --output "$STUDY/root_comparison"
# CHECK-ONLY: inspect numerical summary.
cat "$STUDY/root_comparison/summary.json"
# CHECK-ONLY with respect to research outputs: interactive ROOT may save user preferences.
root -l "$STUDY/root_comparison/tilt_alignment.root"
# At the ROOT prompt: new TBrowser;
```

The ROOT file contains Detector Geometry, per-selected-layer Hit Residuals before/
after correction, separate accepted-track residuals, full SO(3) orientation error,
translation corrections, ACTS chi2/stored-NDF and Pede diagnostics. Truth appears
only in these post-fit comparisons. The stored ACTS NDF convention is preserved.
Manual plots represent **one** independent correction; the existing report-based
interface plots a full Controller history.

## 10. Optional existing sequential Python Controller

Complete the same evidence preflight first. A delivery directory can be nested
under the maintained top-level `input/`. Publish a marker only after files close:

```sh
# WRITES OUTPUT: new delivery and enabled local policy (templates stay disabled).
export DELIVERY=input/manual_l3_001
export STATE=$STUDY/controller_state
python3 - <<'PY'
import json,os,shutil
from pathlib import Path
from research_common import digest
study=Path(os.environ['STUDY']);incoming=Path(os.environ['DELIVERY'])
incoming.mkdir(exist_ok=False)
source=Path(os.environ['CASE'])/'step2_digitization'
shutil.copyfile(source/'rawhits.edm4eic.root',incoming/'sample.root')
# Truth provenance is optional; remove it here to demonstrate truth-free inference.
m=json.loads((source/'rawhit_contract.json').read_text())
m.pop('simulation_truth_geometry_sha256',None);m['producer'].pop('simulation_sha256',None)
m['source_kind']='simulation_test_without_truth'
with (incoming/'sample.metadata.json').open('x') as f:json.dump(m,f,indent=2)
ready={'schema':'rawhit-delivery-v1','input_id':'sample','sequence':1,
       'raw_file':'sample.root','raw_sha256':digest(incoming/'sample.root'),
       'metadata_file':'sample.metadata.json','metadata_sha256':digest(incoming/'sample.metadata.json')}
tmp=incoming/'sample.ready.tmp'
with tmp.open('x') as f:json.dump(ready,f,indent=2)
tmp.rename(incoming/'sample.ready.json')
c=json.loads((study/'controller.json').read_text());c['calibration']['enabled']=True
with (study/'controller_enabled.json').open('x') as f:json.dump(c,f,indent=2)
PY
# WRITES OUTPUT: immutable snapshots, queue, inactive candidates and parent chain.
python3 -m calibration.controller once --config "$STUDY/controller_enabled.json" \
  --input-dir "$DELIVERY" --state-dir "$STATE"
# CHECK-ONLY
python3 -m calibration.controller queue --state-dir "$STATE"
python3 -m calibration.controller geometry --state-dir "$STATE"
# WRITES OUTPUT: optional alternative to once, sequentially monitors new deliveries.
# python3 -m calibration.controller watch --config "$STUDY/controller_enabled.json" \
#   --input-dir "$DELIVERY" --state-dir "$STATE"
```

Inspect `jobs/sample/attempt-001/calibration/calibration_report.json`. Every one
of the 18 components must pass its corresponding mm/rad convergence threshold;
all iterations must preserve the RawHit checksum. Active Geometry stays the
Survey version. Candidate activation requires held-out validation, operator
review and a separate explicit activation command; none is part of this guide.
See [Controller documentation](../calibration/README.md).

## Scientific work still required

Check capture range versus initial Survey, biased track selection/rejections,
noisy physical closure of every parameter, spatial/angular coverage and weak
modes, electron material/bremsstrahlung effects, residual/pull distributions,
and independent-seed uncertainty coverage. Compare initial nominal errors with
injected physical corrections using the signs above. No supported MPGD/AC-LGAD
alignment or universal full-detector six-DOF inference is implied.
