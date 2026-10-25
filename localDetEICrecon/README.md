# EICrecon telescope backends

The primary workflow is `python3 -B -m calibration.workflow run`. Its native
plugins and CMake project live in [experimental/telescope/](experimental/telescope/);
the directory name is retained for compatibility. Start with the
[practical user guide](../docs/TELESCOPE_ALIGNMENT_USER_GUIDE.md) and
[code map](../docs/TELESCOPE_ALIGNMENT_CODE_MAP.md).

Build the primary workflow from the repository root in the fixed Docker
environment, using an unused build directory:

```bash
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/telescope \
  -B /work/build/NEW_NATIVE_BUILD -DCMAKE_BUILD_TYPE=Release \
  -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/NEW_NATIVE_BUILD -j2
```

## Retained +Z BeamTestReco backend

This is the existing locally adapted EICrecon/JANA2 plugin. Its name, collections,
electron hypothesis change, hit selection, manual ACTS surfaces, digitization,
material options and five-SiMAPS Mille model are preserved. It supports historical
+Z data and capability/reference tests. The [implementation audit](../docs/TELESCOPE_IMPLEMENTATION_AUDIT.md)
documents the capabilities retained separately from the native +X workflow.

The CMake project in this directory builds this retained backend. Its existing
build command, run from the repository root, is:

```bash
bash environment/run.sh bash environment/build.sh
```

CMake uses `MILLEPEDE_PREFIX` (external/install by default; no legacy fallback) and discovers EICrecon
headers with `EICRECON_INCLUDE_DIR`. `ENABLE_MILLEPEDE=OFF` now fails explicitly:
the existing plugin source requires the writer. It was never a supported
Mille-free build. Build artifact: build/local_eicrecon_external/BeamTestReco.so.

Use the retained [Workflow Guide](../docs/WORKFLOW.md). Its Python reconstruction
commands live in `reconstruction/` and solver operations in `alignment/`.
Archived source provenance and earlier audits are recorded in
[FINAL_SIMPLIFICATION.md](../docs/FINAL_SIMPLIFICATION.md).
No separate upstream EICrecon checkout is needed or modified.
