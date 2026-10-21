# BeamTestReco backend

This is the existing locally adapted EICrecon/JANA2 plugin. Its name, collections,
electron hypothesis change, hit selection, manual ACTS surfaces, digitization,
material options and five-SiMAPS Mille model are preserved.

From the repository root (host):

```
bash environment/run.sh bash environment/build.sh
```

CMake uses `MILLEPEDE_PREFIX` (external/install by default; no legacy fallback) and discovers EICrecon
headers with `EICRECON_INCLUDE_DIR`. `ENABLE_MILLEPEDE=OFF` now fails explicitly:
the existing plugin source requires the writer. It was never a supported
Mille-free build. Build artifact: build/local_eicrecon_external/BeamTestReco.so.

Use the staged workflow in docs/WORKFLOW.md. Archived source provenance and
earlier audits are recorded in docs/FINAL_SIMPLIFICATION.md.
No separate upstream EICrecon checkout is needed or modified.
