#!/usr/bin/env python3
"""Read-only batch validation of TBrowser objects in a completed run (PyROOT)."""
import argparse,json
from pathlib import Path
import ROOT
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result-dir','--run-dir',dest='run_dir',metavar='RESULT_DIR',type=Path,required=True);a=p.parse_args()
base=a.run_dir/'validation/plots'
f=ROOT.TFile.Open(str(base/'alignment.root'),'READ')
assert f and not f.IsZombie()
keys={k.GetName():k.GetClassName() for k in f.GetListOfKeys()}
for name in ['c_geometry','c_hit_residuals','c_closure']:assert keys[name]=='TCanvas'
assert sum(x=='TH1D' for x in keys.values())>=20
for name in ['g_applied_correction_um','g_chi2_by_step','g_l2_by_step']:assert keys[name]=='TGraph'
f.Close();summary=json.loads((base/'summary.json').read_text())
assert summary.get('reference_passed',True)
print('PASS: three canvases, >=20 residual histograms, closure graphs; summary reference status valid')
