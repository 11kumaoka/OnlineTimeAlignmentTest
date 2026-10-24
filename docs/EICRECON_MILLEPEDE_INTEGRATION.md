> RawHit boundary update: the maintained command now uses separate Digitization
> and truth-independent RawHit Reconstruction. See [RAWHIT_BOUNDARY.md](RAWHIT_BOUNDARY.md)
> for profiles, input/conditions contract and combined/split equivalence results.
> The mathematical writer and solver implementation below is unchanged.

> Architecture update (2026-10-21): task implementations and configurations are
> now top-level directories; new runs use `result/<name>/step1`–`step7`.
> See [the current architecture](TASK_ARCHITECTURE.md) and [Workflow Guide](WORKFLOW.md).
> Historical datasets and quoted historical command paths retain their provenance.
> Beam and Reconstruction configs are now independent selections at steps 2 and 3.

# EICrecon–Millepede-II Integration

This document explains the integration validated at commit
`3034eb1f4a43dfa925992e4a9000ea115dcb63a3`, with stage-entry references updated
for the subsequent independent-stage refactoring. It was checked against the committed
local code, the pinned upstream sources available under `external/src/`, and
saved validation outputs. It describes the supported five-SiMAPS alignment path,
not a generic ACTS alignment interface. See the [Workflow Guide](WORKFLOW.md)
for the broader Simulation and reconstruction procedure.

## 1. Architecture and ownership

```text
EDM4hep Simulation + nominal DD4hep Detector Geometry
                         |
                  EICrecon / JANA2
                         |
      local Digitization -> optional RawHit file -> Hit Reconstruction
                         |
      BeamTestACTSFitter: in-process ACTS Kalman fit
                         |
      LocalBeamTestTracks -> Measurement2D -> TrackerHit
                         |
               BeamTestMilleProcessor
           selection, coordinates, uncertainties
                         |
                BeamTestMilleWriter
       straight-line model and Local/Global derivatives
                         |
           official Mille API in libMille2.so
                         |
            result/<name>/step3/mille.dat
                         |
                EICrecon process ends
                         |
        separate official pede process + pede.txt
                         |
       step4/millepede.res, .log, .his, .end
                         |
          local L2 Global X Geometry Correction
                         |
       same Simulation -> corrected reconstruction
                         |
                 ROOT Closure Validation
```

| Component | Origin and responsibility |
|---|---|
| EICrecon / JANA2 | Upstream event processing, factories, configuration, and collection access. |
| DD4hep, PODIO, EDM4hep/EDM4eic | Upstream Detector Geometry and event-data infrastructure. |
| ACTS | Upstream propagation and Kalman fitting algorithms. |
| `BeamTestReco` / `BeamTestACTSFitter` | Local Plugin registration and adapter using manually constructed surfaces and `Acts::DirectNavigator`. |
| `BeamTestMilleProcessor` | Local JANA processor selecting associated hits and preparing Mille measurements. |
| `BeamTestMilleWriter` | Local four-parameter straight-line model, label convention, and official API calls. |
| Mille / `libMille2.so` | Official DESY library implementing record encoding, writing, reading, and inspection. |
| Millepede-II / `pede` | Official independent solver estimating shared Global Parameters while eliminating per-track Local Parameters. |
| Independent stage modules, example template, ROOT Closure | Local orchestration, constraints, restricted Geometry Correction, and validation. |

**The official solver was not modified.** The project adds a local producer of
Mille records and a workflow around the official packages. It does not embed a
replacement solver in EICrecon. The inspected upstream checkouts matched their
pinned revisions and had no tracked source modifications.

## 2. Installation, linkage, and executable boundaries

### 2.1 Official sources and pinned revisions

The source-of-truth lock file is
[`environment/dependencies.json`](../environment/dependencies.json):

| Package | Official repository | Pinned Git revision |
|---|---|---|
| Mille | `https://gitlab.desy.de/millepede/Mille.git` | `cec2e880ecaab3d255e08e21c8f70f248c6098d8` |
| Millepede-II | `https://gitlab.desy.de/millepede/millepede-ii.git` | `7e3f4f57d993e0e0098d1a40da72823ac9c3207b` |

[`setup_dependencies.py`](../environment/setup_dependencies.py) creates a new
workspace, clones Mille first and Millepede-II second, checks out these commits
in detached mode, and verifies each resulting HEAD. It configures, builds, and
installs each package with CMake. For local source clones, `--local-sources PATH`
requires clean clones named `Mille` and `millepede-ii` and verifies the same commits.

The upstream projects require CMake 3.26.2 or newer and C++/Fortran compilers;
Millepede-II also enables C. The local Plugin requires C++20. The pinned EIC
container supplies the compilers, CMake, ROOT, zlib, EICrecon/JANA, ACTS,
DD4hep, PODIO, EDM4hep/EDM4eic, algorithms, fmt, spdlog, and Microsoft.GSL.
Setup requests ROOT support for both upstream packages and LAPACK/OpenMP support
for Millepede-II. Upstream configuration determines availability of optional
features; use the pinned environment rather than assuming every host has them.

The effective CMake options used by setup are:

```text
Both packages:
  -DCMAKE_INSTALL_PREFIX=/work/external/install
  -DSUPPORT_ROOT=ON -DBUILD_TESTS=OFF -DCMAKE_BUILD_TYPE=Release
Millepede-II additionally:
  -DMille_DIR=/work/external/install/cmake
  -DSUPPORT_LAPACK=ON -DSUPPORT_OPENMP=ON
```

### 2.2 Fresh installation versus an existing installation

From a **fresh checkout where `external/` does not exist**, run on the host:

```bash
bash environment/run.sh python3 environment/setup_dependencies.py
bash environment/run.sh bash environment/build.sh
```

These are reproduction instructions, not commands executed for this document.
No dependency was reinstalled during the documentation task.

For an **existing complete installation**, skip setup:

```bash
bash environment/run.sh bash environment/build.sh
```

Setup intentionally refuses an existing workspace. Do not delete or replace an
installation to repeat the instructions. For a separate installation, use a new
`--workspace`, then consistently set `MILLEPEDE_PREFIX` for build and workflow
commands. If using a custom Plugin build directory through `TESTBENCH_BUILD_DIR`,
pass the same directory with `--build-dir` to reconstruction/all.

Default locations inside the container (`/work` is the repository mount):

| Location | Contents |
|---|---|
| `external/src/Mille/`, `external/src/millepede-ii/` | Pinned official source trees. |
| `external/build/Mille/`, `external/build/millepede-ii/` | Upstream CMake build trees. |
| `external/install/include/Mille/` | Official C++ record interfaces. |
| `external/install/cmake/MilleConfig.cmake` | Installed package and imported target configuration. |
| `external/install/lib/libMille2.so` | Shared record I/O implementation. |
| `external/install/bin/pede` | Independent Millepede-II executable. |
| `external/install/bin/inspectMilleBinary` | Official record inspection utility. |
| `build/local_eicrecon_external/BeamTestReco.so` | Local EICrecon Plugin. |

### 2.3 How the local code links to Mille

[`environment/build.sh`](../environment/build.sh) requires the installed package
configuration, `libMille2.so`, and `pede` before configuring the Plugin. The
[Plugin CMake file](../localDetEICrecon/CMakeLists.txt)
pins `Mille_DIR` under the selected prefix, calls `find_package(Mille CONFIG
REQUIRED ... NO_DEFAULT_PATH)`, compiles `BeamTestMilleWriter.cc` into the Plugin,
and links the imported `Mille2` target. This supplies the implementation of
`spawnMilleRecord`, record methods, and binary I/O. Disabling `ENABLE_MILLEPEDE`
is explicitly rejected by this backend.

The former standalone writer CMake entry was removed during the consolidation
because no maintained workflow used it. The normal Plugin build and the telescope
legacy-equivalence executable still compile the same
[writer source](../localDetEICrecon/alignment/src/BeamTestMilleWriter.cc) directly.
No writer mathematics or legacy alignment capability was removed.

`pede` is a different executable with upstream reader interfaces and solver
code. It does not load `BeamTestReco.so` or call JANA. Its only connection to
this reconstruction is the completed Mille Binary plus steering information.
The workflow prepends the selected prefix's `lib/` to `LD_LIBRARY_PATH` for
reconstruction and pede. Standalone upstream utilities also need this runtime
library path in the inspected installation; see the tested inspector command below.

The stage architecture and independent Geometry scenario files are documented in
the [Workflow Guide](WORKFLOW.md#geometry-scenario-selection). Multi-layer Simulation
Geometry can be prepared, but correction/full Closure explicitly reject scenarios
with nonzero shifts outside L2. No solver or writer model was extended.

## 3. JANA registration, lifecycle, and selection

### 3.1 Registration and collections

[`plugins/BeamTestReco.cc`](../localDetEICrecon/plugins/BeamTestReco.cc)
registers the local Digitization, Hit Reconstruction, and Track Fitting factories,
then adds the processors:

```cpp
app->Add(new local_eicrecon::BeamTestEventProcessor());
app->Add(new local_eicrecon::BeamTestMilleProcessor());
```

The factory tagged `LocalBeamTestTracks` produces the following relevant EDM4eic
collections:

| Collection | Type and use |
|---|---|
| `LocalSiMAPSRecHits` | `edm4eic::TrackerHit`; existence is required by the Mille processor. |
| `LocalBeamTestTracks` | `edm4eic::Track`; source of associated measurements. |
| `LocalBeamTestFitMeasurements` | `edm4eic::Measurement2D`; attached to Tracks and linked to original reconstructed Hits. |
| `LocalBeamTestPredictedMeasurements` | ACTS diagnostic predicted states; not read by the Mille writer. |
| `LocalBeamTestFilteredMeasurements` | ACTS diagnostic filtered states; not read by the Mille writer. |
| `LocalBeamTestSmoothedMeasurements` | ACTS diagnostic smoothed states; not read by the Mille writer. |
| `LocalBeamTestTrajectories`, `LocalBeamTestTrackParameters` | Reconstruction products; their numerical fit parameters are not exported as Mille Local Parameters. |

The local fitter creates each fit measurement, associates its original
`TrackerHit` through `m.addToHits(...)`, and attaches it using
`trk.addToMeasurements(m)`. The Mille processor traverses these relations:

```cpp
for (const auto& meas : trk.getMeasurements()) {
  for (const auto& h : meas.getHits()) {
    // Decode the layer and collect unique associated hits.
```

It does not select hits by scanning the entire `LocalSiMAPSRecHits` collection.
That collection is retrieved as a prerequisite; the actual values come from
Track → Measurement2D → TrackerHit relations. Measurement local coordinates,
ACTS fitted parameters, and predicted/filtered/smoothed residuals are not read.

### 3.2 Lifecycle

Source:
[`BeamTestMilleProcessor.h`](../localDetEICrecon/processors/BeamTestMilleProcessor.h)
and [`.cc`](../localDetEICrecon/processors/BeamTestMilleProcessor.cc).

- **`Init()`** registers parameters. If disabled, it logs that state and returns.
  If enabled, it constructs one writer with the chosen output path and reference
  Z, single-precision storage, and zero-derivative omission.
- **`Process()`** does nothing when disabled. Otherwise it increments the event
  counter, requests the Track and Hit collections, applies the selection below,
  constructs five ordered `Hit2D` values, and asks the writer for one record.
- **`Finish()`** flushes the writer and prints enabled state, event/selection
  counters, record/scalar counters, and the output path. The writer destructor
  also attempts to flush. Flush does not append an additional track record.

The writer serializes complete record construction using a mutex; processor
counters are atomic. The validated workflow nevertheless uses `-Pnthreads=1`.
This is not a claim that every part of the local fitter supports arbitrary
multi-threaded operation.

### 3.3 Exact processor selection

1. Missing Track collection, zero Tracks, or absent `LocalSiMAPSRecHits` is
   counted as `no_track`. The Hit collection is not independently tested for
   emptiness at this initial check.
2. With `milleRequireSingleTrack=1`, a Track count other than one is counted as
   `ambiguous_track`. If disabled, only `tracks->at(0)` is used; the code does not
   loop over all Tracks or choose the best one.
3. Associated Hits are grouped using `(cellID >> 11) & 63`, the six-bit layer
   field after `system:8,barrel:3`. Hits outside layers 0–4 are ignored.
4. Repeated references to the same PODIO Hit are deduplicated using its
   `(collectionID,index)` pair. Distinct Hits in the same layer are not merged.
5. Every layer L0–L4 must have exactly one distinct associated Hit. A missing
   layer increments `missing_layer`; multiple Hits increment
   `ambiguous_layer_hit`. Either condition rejects the event immediately.
6. The processor copies the Hit position and diagonal position errors, applies
   the uncertainty floor and optional measurement-only injection, and writes
   one record. Successful calls increment `accepted`, `records`, and ten scalar
   `measurements`.

There is no additional processor cut on ACTS χ², momentum, PDG, nDoF, or residual.
It does not inspect ACTS outlier weights or check detector-system IDs beyond the
layer field. The expected SiMAPS relations are supplied by the current factory
chain; these assumptions need review before adding other detectors.
Counters reflect calls to the writer, not an independent binary-integrity test.
Use the official decoder and pede diagnostics as additional checks.

Upstream of this processor, the
[local fitter](../localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc)
already requires all five SiMAPS layers and exactly one representative Hit per
layer; `pickRepresentative()` rejects any multiplicity other than one. ACTS fit
failure produces no Track. With optional MPGD/AC-LGAD fitting, an ambiguous
nonempty optional layer also rejects the fit; a missing optional layer is not
added. The default electron case disables both optional detectors. Excluding a
SiMAPS layer from the fit can leave incomplete associations and is incompatible
with the writer's required five-layer coverage.

### 3.4 Exact configuration parameters

These names are case-sensitive; use `-P<name>=<value>` with EICrecon.

| Parameter | Processor default | Meaning |
|---|---:|---|
| `beamtstreco:milleEnabled` | `false` | Enable writing; the formal workflow passes `1`. |
| `beamtstreco:milleOutputPath` | `results/manual/mille.dat` | Output file; the workflow supplies an absolute, new stage-specific path. |
| `beamtstreco:milleZRefMm` | `100.0` | Local parameter reference Z in mm. |
| `beamtstreco:milleSigmaFloorMm` | `0.005` | Minimum scalar uncertainty in mm (5 μm). |
| `beamtstreco:milleRequireSingleTrack` | `true` | Require exactly one Track. |
| `beamtstreco:milleInjectedShiftLayer` | `-1` | Disabled; otherwise add an artificial shift to this layer during Mille writing only. |
| `beamtstreco:milleInjectedShiftXmm` | `0.0` | Measurement-only X shift in mm. |
| `beamtstreco:milleInjectedShiftYmm` | `0.0` | Measurement-only Y shift in mm. |

For the physical L2 test the workflow explicitly disables measurement-stage
injection. The physical misalignment is already in the Simulation Geometry;
combining it with measurement-only injection would be a different test.
The fitter has separately named `alignmentTestShiftLayer` and
`alignmentTestShiftXmm` parameters; these are not the Mille injection parameters.

The workflow's electron reconstruction also sets
`BeamTestReco:LocalBeamTestTracks:useMPGD=0`, `useACLGAD=0`, `outputTrackPDG=11`,
and `seedQOverP=-1.0` under that same factory prefix. It loads
`log,dd4hep,evaluator,acts,algorithms_init,beam,podio,BeamTestReco` with default
plugins ignored. Keep these dependencies; this document does not propose
removing the standard ACTS plugin because the local fitter uses manual surfaces.

## 4. Measurement equations and official writer calls

Source:
[`BeamTestMilleWriter.h`](../localDetEICrecon/alignment/src/BeamTestMilleWriter.h)
and [`.cc`](../localDetEICrecon/alignment/src/BeamTestMilleWriter.cc).

### 4.1 Model, units, and unknowns

For track/event $t$ and SiMAPS layer $i$, the writer supplies the linear model

$$
x^{\mathrm{rec}}_{t,i}=x_{0,t}+t_{x,t}(z_i-z_{\mathrm{ref}})+a_{x,i}+\epsilon_{x,t,i},
$$

$$
y^{\mathrm{rec}}_{t,i}=y_{0,t}+t_{y,t}(z_i-z_{\mathrm{ref}})+a_{y,i}+\epsilon_{y,t,i}.
$$

The requested equations without the noise term are the corresponding predicted
measurements. **Here $a_{x,i},a_{y,i}$ are measurement biases in the nominal
reconstruction frame, not directly positive physical detector displacements.**

| Quantity | Definition and unit |
|---|---|
| `x_mm`, `y_mm`, `z_mm` | `TrackerHit::getPosition()` components, interpreted in global mm by the current chain. |
| $x_0,y_0$ | Per-track intercepts at $z_{\mathrm{ref}}$, in mm. |
| $t_x,t_y$ | Per-track slopes $dx/dz,dy/dz$, dimensionless. |
| $a_{x,i},a_{y,i}$ | Shared layer biases, in mm. |
| $z_{\mathrm{ref}}$ | `milleZRefMm`, normally 100 mm, at nominal L2. |
| $\sigma_x,\sigma_y$ | Scalar standard deviations in mm, not variances or inverse weights. |

The processor calculates

$$
\sigma_x=\max\left(0.005\ \mathrm{mm},\sqrt{\max(0,C_{xx})}\right),\qquad
\sigma_y=\max\left(0.005\ \mathrm{mm},\sqrt{\max(0,C_{yy})}\right),
$$

using the configured floor in place of 0.005 when overridden. `Cxx` and `Cyy`
are `getPositionError().xx` and `.yy`, interpreted in mm². The current inspected
sample has 0.01 mm uncertainties, above the floor. XY correlations, Z uncertainty,
and process-noise correlations are not encoded by this scalar model. There is
no explicit processor finiteness check on coordinates.

Pede fits four **Local Parameters per record** independently of the ACTS seed
or fitted track values. They are not copied from `LocalBeamTestTrackParameters`:

| Local index | Parameter | X derivative | Y derivative |
|---:|---|---:|---:|
| 1 | $x_0$ | 1 | 0 |
| 2 | $y_0$ | 0 | 1 |
| 3 | $t_x$ | $z_i-z_{\mathrm{ref}}$ | 0 |
| 4 | $t_y$ | 0 | $z_i-z_{\mathrm{ref}}$ |

Intercept and bias derivatives are dimensionless; slope derivatives have units
of mm. The shared labels are `1000 + layer` for X and `2000 + layer` for Y, with
one Global derivative `+1` for each scalar measurement.

With independent Gaussian errors the data term is the sum of squared
`(coordinate − straight-line prediction − layer bias) / sigma` over tracks,
layers, and X/Y. Pede eliminates the Local Parameters and solves the coupled
Global Parameters using its configured constraints and numerical controls.

The 100 mm reference Z defines the intercept location; it is unrelated to the
Particle Gun's current z=−500 mm source position and does not move any detector.

### 4.2 API sequence

The boundary uses `Mille::spawnMilleRecord()` and the official
`Mille::MilleRecord::addData()`, `writeRecord()`, and `flushOutputFile()` methods.
The constructor calls:

```cpp
m_record = Mille::spawnMilleRecord(m_cfg.outputPath,
                                 m_cfg.doublePrecision,
                                 m_cfg.writeZeroDerivatives);
```

`Init()` fixes these booleans to `false,false`: single-precision payload and
omission of zero derivatives. For each ordered Hit, X is followed by Y:

```cpp
std::vector<float> dLocalX{1.0F, 0.0F, static_cast<float>(dz), 0.0F};
std::vector<int> gLabelX{labelAx(h.layer)};
std::vector<float> dGlobalX{1.0F};
m_record->addData(h.x_mm, h.sigma_x_mm, localIdx, dLocalX, gLabelX, dGlobalX);
```

The Y call uses `h.y_mm`, `h.sigma_y_mm`, local derivatives
`{0,1,0,dz}`, label `2000+layer`, and Global derivative `{1}`.
`localIdx` is `{1,2,3,4}`. The upstream API accepts double-valued measurement/error
arguments and float derivative arrays; the selected record stores floating-point
values in single precision.

After all five Hits, `m_record->writeRecord()` writes **one track record containing
ten scalar measurements**, then prepares its buffers for the next track.
`BeamTestMilleWriter::flush()` calls `m_record->flushOutputFile()` to flush the
output stream. Neither flush nor writing a scalar measurement invokes pede.

### 4.3 Worked example: L2 X

For nominal L2, `z_mm=100` and `zRefMm=100`, hence `dz=0`. The logical API inputs
are local indices `{1,2,3,4}`, derivatives `{1,0,0,0}`, Global label `{1002}`, and
Global derivative `{1}`. Record 0 of the saved 99-track validation binary decodes as:

```text
Measurement 5 (L2 X):
    Value:       -0.242487 mm
    Uncertainty:  0.010000 mm
    Local:        index 1 -> 1
    Global:       label 1002 -> 1
```

Thus its equation is `−0.242487 mm = x0 + a_x,L2 + noise`. The three zero Local
derivatives are omitted from the encoded record, not missing parameters.
A single equation cannot determine both unknowns; all layers determine the
track intercept/slopes, and all records constrain the shared layer bias.

**The encoded value is the reconstructed Hit coordinate.** It is not
`hit − ACTS prediction`, and the writer exports no ACTS residual Jacobian.
Using coordinates is valid here because the supplied model is linear and the
Local track parameters are refitted by pede. A nonlinear or curved-track model
would need a deliberately defined linearization/residual interface.

## 5. What `mille.dat` contains and how to inspect it

`step3/mille.dat` **is the Mille Binary output**. There is no separate binary
that must accompany it. The extension is a format-selection hint in the pinned
Mille factory: `.dat` and `.bin` select C binary, `.txt`/`.csv` select text, and
`.root` selects ROOT when supported. Renaming a file does not convert its bytes.
Do not use a text output extension with this factory and assume it is still binary.

The verified upstream `MilleRecordC::writeRecord()` writes a signed integer
header followed by a floating-point buffer and an integer buffer of matching
entry count. The header is `2*N` for single precision and `−2*N` for double
precision. Paired entries encode the initial record marker, a measurement,
nonzero Local derivatives, its uncertainty, and Global derivatives; label/index
zero separates measurement/error blocks. The writer supplies no special blocks.
The integer representation and byte ordering follow the compiled C++ binary I/O;
this document does not claim an arbitrary portable text or fixed-size record layout.
Record length depends on the derivative content, so do not hard-code offsets.

The official `inspectMilleBinary` reads through `spawnMilleReader` and
`MilleDecoder`; no custom decoder is necessary. This command was actually run
read-only against the saved file during documentation verification:

```bash
bash environment/run.sh bash -c '
  export LD_LIBRARY_PATH="/work/external/install/lib:${LD_LIBRARY_PATH:-}"
  exec /work/external/install/bin/inspectMilleBinary -c \
    /work/results/final_simplification_20261021_01/regression/before/mille.dat 0 1
'
```

It printed record 0, ten scalar measurements, and the L2 values above. In this
version the range is zero-based with an exclusive upper bound when positive;
`0 1` prints only the first record. The runtime library path is necessary in the
inspected installation: a direct invocation without it failed to locate Mille2.
For another analysis, substitute its `result/<name>/step3/mille.dat` path.

The same official package includes `convertMilleFormats` and reader APIs for
format conversion. They are optional diagnostics; the supported alignment path
consumes the original C binary directly. Source links for the exact encoding
and inspector implementation appear at the end of this document.

## 6. Steering generation and independent pede execution

### 6.1 Template expansion and working directory

[`align.sh`](../alignment/align.sh) forwards to
[`alignment/align.py`](../alignment/align.py), function `align()`.
It first verifies the `step3/complete.json` hashes and exclusively creates
`step4/`. It snapshots the selected steering template (default below), then loads
[`pede_template.txt`](../alignment/pede_template.txt)
and replaces `@MILLE_FILE@` with the absolute path to `step3/mille.dat`:

```python
(p/'pede.txt').write_text(template.replace('@MILLE_FILE@',str(a.run_dir/'step3/mille.dat')))
```

For `--result-dir result/mille_demo_001`, the beginning of the generated file
inside the container is:

```text
Cfiles
/work/result/mille_demo_001/step3/mille.dat

entries 5
method inversion 3 0.001
```

The invoked command is `/work/external/install/bin/pede pede.txt`, with working
directory `/work/result/mille_demo_001/step4/`. The selected prefix's `lib/`
is prepended to `LD_LIBRARY_PATH`. Pede's fixed-name outputs are therefore local
to that alignment directory. Its absolute binary path remains valid after changing
the working directory. EICrecon has already exited: this is a new process.

### 6.2 Verified meanings of the directives

| Directive | Meaning in the pinned implementation |
|---|---|
| `Cfiles` | Subsequent data files use the upstream Mille reader path rather than Fortran-record input; the current file is C binary. It does not request another output binary. |
| `Parameter` | Begins records of `label initial_value presigma`. Units follow the derivatives/model, not a solver-wide choice. |
| `entries 5` | Sets `mreqenf=5`, the minimum binary-file entries for an active Global Parameter. It does not mean five detector layers or five records to read. The unspecified accepted-fit threshold `mreqena` remains 10, confirmed in the saved log. |
| `method inversion 3 0.001` | Uses full matrix inversion, sets iteration control `mitera=3` and convergence threshold `dflim=0.001` in objective-function decrease. The pinned driver reports/enforces 3 as the maximum iteration count and can finish earlier; 0.001 is not a millimetre accuracy target. |
| `printcounts` | Requests accepted-fit parameter counts in the result file with its default setting of 1. |
| `end` | Terminates steering input, after which the configured fit is executed. It is not an instruction to stop after writing the steering file. |

The template fixes both X/Y endpoint biases to zero with negative pre-sigmas:

```text
Parameter
1000 0.0 -1.0
2000 0.0 -1.0
1004 0.0 -1.0
2004 0.0 -1.0
1001 0.0 1.0
2001 0.0 1.0
1002 0.0 1.0
2002 0.0 1.0
1003 0.0 1.0
2003 0.0 1.0
```

L0 and L4 anchor the reference frame, removing the overall offset/tilt freedom
of each projection. Six Global Parameters, X/Y on L1–L3, remain variable.
A negative pre-sigma fixes a parameter at its initial value; zero allows variation
without a specified stabilizing pre-weight. Positive pre-sigmas add diagonal
pre-weights, here numerically `1/(1 mm)^2`, to stabilize the numerical solution.
They are **not a literal 1 mm survey measurement** in this template. The upstream
manual explains that stabilization should not bias converged values, although
errors can be affected. Explicit regularization is a separate option; it is not
enabled by this template, and the saved run reports `regularization: no`.

## 7. Files, diagnostics, and Geometry Correction

The exact relative layout under `result/mille_demo_001/` is:

| File | Producer / consumer and interpretation |
|---|---|
| `step2/events.edm4hep.root` | DDSim output or link to preserved Simulation; Digitization input. |
| `step2_digitization/rawhits.edm4eic.root` | Standalone common RawHit input; no MC event collections required downstream. |
| `step1/nominal.xml`, `step1/misaligned.xml` | Local Geometry Preparation; nominal reconstruction and displaced Simulation configurations. |
| `step3/reco.root` | EICrecon Tracks, Hits, and diagnostic measurements. |
| `step3/mille.dat` | Official Mille C-binary records; input to pede. |
| `step3/stdout.log` | EICrecon and Mille Writer counters. |
| `step4/pede.txt` | Local template expansion; pede input. |
| `step4/millepede.res` | Fitted Global Parameter values and associated information, not corrected Geometry. |
| `step4/millepede.log` | Solver iterations, input counts, fit quality, rejection/conditioning diagnostics. |
| `step4/millepede.his` | Upstream text histogram archive, not a ROOT file. Inspect as text; the installed official `readPedeHists` offers optional conversion/visualization. |
| `step4/millepede.end` | Solver status and message. |
| `step4/stdout.log` | Captured pede console output, including warnings. |
| `step5/corrected.xml` | Local application of only the L2 Global X correction. |
| `step6/reco.root`, `step6/mille.dat` | Reconstruction and a new writer output using corrected Geometry; the default workflow does not run a second alignment on this binary. |
| `step7/alignment.root`, `summary.json` | Local ROOT Closure plots and numerical comparisons. |

Each workflow stage also records its command, exit status, completion information,
and relevant output hashes. Unix process exit status and `millepede.end` are separate
checks: `execute()` requires a zero subprocess return, then `align()` accepts an
end-file code of 0 (normal) or 1 (warnings). It rejects other end-file codes and
requires the L2 label to be present. The inspected historical run ends with
`1 Ended with warnings (bad measurements)`; do not describe that as warning-free.

### 7.1 Reading the result file

In the inspected variable rows, the columns are label, fitted value, pre-sigma,
last correction, uncertainty from inversion, and the count requested by
`printcounts`. Fixed rows have fewer numerical fields. Do not assume an uncertainty
exists for every row or parse a universal fixed-column schema independent of options.
The local `read_pede()` deliberately reads only the first two fields; it is implemented in
[`alignment/align.py`](../alignment/align.py).

For the historical sample, an actual row is:

```text
1002  -0.19875  1.0000  -0.19875  0.12309E-02  99
```

Label 1002 is the L2 X bias: `−0.19875 mm = −198.75 μm`. The uncertainty in this
row is `0.0012309 mm`, with the upstream pre-sigma/error caveat described above.
Labels 2000–2004 are Y biases, not rotation angles or a second track collection.

### 7.2 Sign and physical interpretation

Simulation places L2 at Global X `+0.200 mm`, while initial reconstruction uses
nominal Geometry. This produces approximately `−0.200 mm` Rec−Sim bias. With the
writer's `+1` bias derivative, pede estimates a negative measurement bias.
The supported Geometry Correction in
[`correction/correct_geometry.py`](../correction/correct_geometry.py) negates it:

```python
value=-read_pede(a.run_dir/'alignment/millepede.res')[1002]
modified_xml(a.run_dir/'geometry/nominal.xml',p/'corrected.xml',2,value)
```

Thus `a_x,L2 = −0.19875 mm` gives a placement correction `+0.19875 mm`.
For this DD4hep driver's `phi0=0` ring, `x=−r`, so the XML ring attribute becomes
`r="-0.19875000*mm"`. This sign conversion is driver-specific, not a universal
rule for detector translations or rotations. The original nominal XML is not edited.

Although pede fits all six variable biases, the current correction applies only
label 1002. Other X/Y solutions are not propagated into Geometry.

### 7.3 Validated Closure and distinct χ² quantities

The saved physical +200 μm test demonstrates:

| Metric | Historical z=0 mm, 100 events | Fresh z=−500 mm, 100 events |
|---|---:|---:|
| Accepted Tracks before / after | 99 / 99 | 98 / 98 |
| Geometry Correction | +198.75 μm | +201.13 μm |
| L2 mean Rec−Sim before → after | −199.571→−0.821 μm | −198.922→+2.208 μm |
| ΣACTS χ² / Σstored nDoF before → after | 45.592→1.981 | 33.274→1.244 |
| Writer records / scalar measurements, before | 99 / 990 | 98 / 980 |

These are different Simulation inputs. Only the historical dataset is compared
against [`reference_metrics.json`](../validation/reference_metrics.json).
The final verification files are under
`results/final_simplification_20261021_01/{regression,fresh_electron_100}/`.

Pede's fit diagnostic is not the ACTS ratio in this table. With ten scalar
measurements and four independent straight-line Local Parameters, the nominal
local statistical degrees of freedom are six per track. For 99 accepted records
and six fitted Global Parameters, the saved pede log reports
`1883.321285 / (594 − 6) = 3.202927`. Its denominator is 588, whereas the ACTS
stored measurement-dimensionality sum for these 99 Tracks is 990.
Outlier rejection, rank, parameter fixing, or a different model can change solver
counting; use the actual log rather than applying that formula indiscriminately.

The objectives can also differ: ACTS uses its Kalman states, seed covariance,
and fitting settings; Mille refits the raw coordinates with the explicit local
straight-line model and scalar errors. Pede fits six shared biases, while the
subsequent Geometry update applies only L2 X. Neither the optimized χ² values nor
the displayed ratios are expected to be identical. Solver suggestions to rescale
uncertainties are diagnostic; the workflow does not apply them automatically.

## 8. How to reproduce and inspect the connection

The commands below use example result names for a future run. They were checked
against the source and saved command records. The subsequent independent-stage
validation is recorded in [Stage Refactoring](STAGE_REFACTORING.md). Use a new
result name and do not rerun tools against existing output paths.

### 8.1 Produce a binary with EICrecon, without a new Simulation

After dependency setup/build, use the preserved historical input:

```bash
bash environment/run.sh bash geometry/prepare_geometry.sh \
  --result-dir result/mille_demo_001
bash environment/run.sh bash simulation/simulate.sh \
  --result-dir result/mille_demo_001 \
  --sim-input results/reference/physical_alignment_L2_x200um/sim_electron_L2x200um_100.edm4hep.root
bash environment/run.sh bash digitization/digitize.sh \
  --result-dir result/mille_demo_001
bash environment/run.sh bash reconstruction/reconstruct.sh \
  --result-dir result/mille_demo_001
```

Here `simulate.sh --sim-input` links existing data and **does not run DDSim**.
The actual vertices remain z=0 mm despite the current case's z=−500 mm setting.
See [local reference data requirements](../validation/README.md) if the input
is absent. For a fresh test, omit `--sim-input`; that intentionally runs Simulation.

`reconstruct.sh` executes EICrecon, with these exact Mille-related arguments
(the path below illustrates the resolved path for this result):

```text
-Pbeamtstreco:milleEnabled=1
-Pbeamtstreco:milleOutputPath=/work/result/mille_demo_001/step3/mille.dat
-Pbeamtstreco:milleZRefMm=100.0
-Pbeamtstreco:milleRequireSingleTrack=1
-Pbeamtstreco:milleInjectedShiftLayer=-1
```

The complete invocation, plugin set, electron parameters, output collections,
and `step3/` working directory are recorded in `step3/command.json`.
Using the wrapper rather than repeating its raw command preserves completion
markers and avoids truncating the writer's existing output file.

```bash
cat result/mille_demo_001/step3/command.json
grep 'BeamTestMilleProcessor::Finish' result/mille_demo_001/step3/stdout.log
```

The saved 99-track run prints `events=100 accepted=99 no_track=1`, zero ambiguity/
missing-layer counters, and `records=99 measurements=990`. `reconstruct()` requires
record count equal to accepted Track count and scalar count equal to ten times
record count. The default workflow therefore fails a stage if writer/Track
selection diverges, rather than quietly declaring a usable alignment sample.

### 8.2 Run the independent solver through the maintained stage

```bash
bash environment/run.sh bash alignment/align.sh \
  --result-dir result/mille_demo_001
cat result/mille_demo_001/step4/pede.txt
cat result/mille_demo_001/step4/millepede.res
cat result/mille_demo_001/step4/millepede.end
sed -n '1,60p' result/mille_demo_001/step4/millepede.log
sed -n '1,20p' result/mille_demo_001/step4/millepede.his
```

The shell wrapper launches the independent Millepede stage, which starts the separate
`pede` executable; it does not rerun EICrecon. Read the `.end` message and full
log, not just whether a `.res` file exists.

### 8.3 Optional manual pede replay in a separate new directory

This demonstrates the external boundary without modifying the maintained
alignment result. It uses the same template replacement as `align()`:

```bash
bash environment/run.sh python3 -c '
from pathlib import Path
binary = Path("result/mille_demo_001/step3/mille.dat").resolve()
assert binary.is_file()
replay = Path("result/pede_replay_001")
replay.mkdir()  # Exclusive: an existing directory is an error.
template = Path("alignment/pede_template.txt").read_text()
(replay / "pede.txt").write_text(template.replace("@MILLE_FILE@", str(binary)))
'
bash environment/run.sh bash -c '
  set -euo pipefail
  cd /work/result/pede_replay_001
  export LD_LIBRARY_PATH="/work/external/install/lib:${LD_LIBRARY_PATH:-}"
  /work/external/install/bin/pede pede.txt > stdout.log 2>&1
'
cat result/pede_replay_001/millepede.res
cat result/pede_replay_001/millepede.end
```

Run the second command only once in the newly created directory. Upstream pede
uses fixed output names and can rotate/replace existing files; the local workflow
avoids that by exclusive stage creation. This replay has no workflow completion
marker and is not silently substituted for `alignment/`. Use the maintained
alignment stage above for the subsequent correction steps.

### 8.4 Apply the supported correction and validate

```bash
bash environment/run.sh bash correction/correct_geometry.sh \
  --result-dir result/mille_demo_001
bash environment/run.sh bash reconstruction/reconstruct_corrected.sh \
  --result-dir result/mille_demo_001
bash environment/run.sh bash validation/validate.sh \
  --result-dir result/mille_demo_001 --reference validation/reference_metrics.json
bash environment/run.sh python3 validation/check_root_outputs.py \
  --result-dir result/mille_demo_001
```

The before/after Simulation and Plugin hashes must agree. The standard sequence
creates a second binary under `step6/`, but does not overwrite the input to the
first pede fit. For an all-in-one historical regression use
`bash environment/run.sh bash validation/run_regression.sh result/regression_001`.
For fresh z=−500 mm events use `validation/run_closure.sh --result-dir result/electron_001`
through the same launcher, without applying the historical reference.

## 9. Limitations and extension points

| Current boundary | Required extension, not implemented here |
|---|---|
| Exactly five 2D SiMAPS layers | Replace the fixed `std::array<Hit2D,5>`, hard-coded layer loop/coverage rules, ten-scalar counters, and workflow's `10*records` assertion with a validated detector/measurement model. |
| Four-parameter straight-line Local model | Define the appropriate residuals, Local Parameters, derivatives, and correlations for a curved or material-aware trajectory. ACTS states are not automatically such an interface. |
| X/Y layer translations only | Introduce rotation-sensitive derivatives in an explicit coordinate convention, update labels and units, and validate nonlinear linearization when needed. |
| L0/L4 fixed | Redesign reference-frame constraints and weak-mode treatment for the intended detector. Do not simply release every endpoint. |
| L1–L3 X/Y fitted, only L2 X applied | Extend `correct()`, `modified_xml()`, geometry validation, and Closure plotting/metrics before applying other labels or multiple corrections. |
| One selected Track per event | Define multi-track record handling and hit-sharing rules; disabling `milleRequireSingleTrack` currently selects only the first Track. |
| Diagonal scalar Hit errors | Add justified covariance/whitening or other supported modeling if correlations and scattering are required. Do not rescale errors solely to force χ²/NDF to one. |
| Layer-only CellID grouping | Add detector-system/collection identification before combining detectors with overlapping layer IDs. |

MPGD/AC-LGAD Hits may participate in optional local Track Fitting, but their
measurements are not exported by this writer. There is no general rotational
alignment implementation, no generic ACTS residual/Jacobian bridge, and no claim
that manually constructed ACTS surfaces follow arbitrary DD4hep alignment updates.
Such changes require coordinated reconstruction, model, steering, Geometry, and
validation work; changing only the template is insufficient.

## 10. Source references and verification boundary

Local entry points are linked throughout this document. Upstream definitions
were checked in the pinned source trees; the corresponding official links are:

- [Mille factory and extension selection](https://gitlab.desy.de/millepede/Mille/-/blob/cec2e880ecaab3d255e08e21c8f70f248c6098d8/src/MilleFactory.cc).
- [Mille record API](https://gitlab.desy.de/millepede/Mille/-/blob/cec2e880ecaab3d255e08e21c8f70f248c6098d8/Mille/MilleRecord.h) and [measurement encoding](https://gitlab.desy.de/millepede/Mille/-/blob/cec2e880ecaab3d255e08e21c8f70f248c6098d8/Mille/MilleRecord.ixx).
- [C-binary writer implementation](https://gitlab.desy.de/millepede/Mille/-/blob/cec2e880ecaab3d255e08e21c8f70f248c6098d8/src/MilleRecordC.cc).
- [Official binary inspector](https://gitlab.desy.de/millepede/Mille/-/blob/cec2e880ecaab3d255e08e21c8f70f248c6098d8/util/inspectMilleBinary.cc).
- [Pede steering options](https://gitlab.desy.de/millepede/millepede-ii/-/blob/7e3f4f57d993e0e0098d1a40da72823ac9c3207b/doc/options.md), [manual](https://gitlab.desy.de/millepede/millepede-ii/-/blob/7e3f4f57d993e0e0098d1a40da72823ac9c3207b/doc/draftManual.md), and [status codes](https://gitlab.desy.de/millepede/millepede-ii/-/blob/7e3f4f57d993e0e0098d1a40da72823ac9c3207b/doc/exitCodes.md).
- [Pinned pede parser and fitting driver](https://gitlab.desy.de/millepede/millepede-ii/-/blob/7e3f4f57d993e0e0098d1a40da72823ac9c3207b/src/pede.f90). Its stopping conditions and saved output resolve the generic options page's ambiguous description of iteration count.

The original documentation audit executed the official binary inspector with an
explicit library path and source-checked reproduction commands without launching
physics jobs or modifying results. Subsequent independent-stage work executed a
clean Plugin build and L2-only Closure validations; see
[Stage Refactoring](STAGE_REFACTORING.md) for exact commands and results. It did not
change the C++ integration or upstream packages. The new two-layer scenario was
validated only through Geometry Preparation, not Simulation or Closure.
