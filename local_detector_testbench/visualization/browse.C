#include <TBrowser.h>
#include <TFile.h>
#include <TError.h>

// ROOT GUI browser: root --web=off -l 'browse.C("results/regression_001/validation/plots/alignment.root")'
void browse(const char* filename = "results/regression_001/validation/plots/alignment.root") {
  TFile *f = TFile::Open(filename, "READ");
  if (!f || f->IsZombie()) {
    ::Error("browse_alignment", "Cannot open %s", filename);
    return;
  }
  new TBrowser("alignment_browser", f, "EIC alignment ROOT plots");
}

// Compatibility with the former macro filename.
void browse_alignment(const char* filename) { browse(filename); }
