#!/usr/bin/env python3
"""ROOT geometry, hit-residual and one-update closure visualization.
Geometry inputs, a saved metrics summary, and a NEW output directory are required.
Numerical PODIO extraction belongs to validation/metrics.py; PyROOT renders objects.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import math

import numpy as np
import ROOT
import json
from geometry.placements import geometry
from validation.metrics import mean_error

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadLeftMargin(0.15)
ROOT.gStyle.SetPadBottomMargin(0.14)

BLUE, GREEN = ROOT.kAzure + 1, ROOT.kGreen + 2
HOLD = []  # Keep PyROOT-owned graphics objects alive until TCanvas.Write().


def hold(obj):
    HOLD.append(obj)
    return obj










def style_graph(g, color, marker):
    hold(g)
    g.SetMarkerStyle(marker)
    g.SetMarkerColor(color)
    g.SetLineColor(color)
    g.SetLineWidth(2)
    g.SetMarkerSize(1.5)
    return g


def make_geometry(geo, truegeo, corrected):
    c = hold(ROOT.TCanvas("c_geometry", "Seven-layer geometry", 1300, 550))
    c.Divide(2, 1)
    c.cd(1)
    frame = hold(ROOT.TH2F("frame_xz", "Seven-layer telescope;z [mm];Global x [mm]",
                           100, -15, 320, 100, -60, 60))
    frame.SetStats(0)
    frame.Draw("AXIS")
    colors = {"SiMAPS": ROOT.kRed+1, "MPGDPlane": ROOT.kBlue+1, "ACLGADPlane": ROOT.kGreen+2}
    for layer in range(7):
        x, z, name = geo[layer]
        line = hold(ROOT.TLine(z, x-50, z, x+50))
        line.SetLineColor(colors[name])
        line.SetLineWidth(5)
        line.Draw()
        tag = hold(ROOT.TLatex(z+2, 53, f"L{layer}"))
        tag.SetTextSize(.035)
        tag.Draw()

    c.cd(2)
    centers=[d[2][0]*1000 for d in (geo,truegeo,corrected)]
    pad=max(20.,(max(centers)-min(centers))*0.15)
    frame2 = hold(ROOT.TH2F("frame_l2", "L2 center position;Global x [#mum];Geometry",
                            100, min(centers)-pad, max(centers)+pad, 3, 0.5, 3.5))
    for i, label in enumerate(("Nominal reco", "True (Geant4)", "Corrected reco"), 1):
        frame2.GetYaxis().SetBinLabel(i, label)
    frame2.GetYaxis().SetLabelSize(.052)
    frame2.Draw("AXIS")
    for i, (name, g, color) in enumerate((("Nominal", geo, ROOT.kGray+2),
                                          ("Simulated", truegeo, ROOT.kRed+1),
                                          ("Corrected", corrected, GREEN)), 1):
        value = g[2][0] * 1000.
        point = style_graph(ROOT.TGraph(1), color, 20)
        point.SetName("g_l2_" + name.lower())
        point.SetPoint(0, value, float(i))
        point.Draw("P SAME")
        label = hold(ROOT.TLatex(value+5, i+.08, f"{value:.2f} #mum"))
        label.SetTextSize(.037)
        label.SetTextColor(color)
        label.Draw()
    return c




def make_closure(before, after, applied):
    c = hold(ROOT.TCanvas("c_closure", "One geometry-update closure", 1430, 490))
    c.Divide(3, 1)
    c.cd(1)
    g = style_graph(ROOT.TGraph(2), BLUE, 20)
    g.SetName("g_l2_by_step")
    g.SetTitle("L2 bias after one Geometry Correction;Geometry Correction step;Mean #Delta x [#mum]")
    for i, data in enumerate((before, after)):
        g.SetPoint(i, i, mean_error(data["deltas"][2])[0])
    g.Draw("ALP")
    means=[mean_error(d["deltas"][2])[0] for d in (before,after)]
    pad=max(20.,abs(means[0]-means[1])*.15)
    g.SetMinimum(min(means)-pad); g.SetMaximum(max(means)+pad)
    g.GetXaxis().SetLimits(-.2, 1.2)
    g.GetXaxis().SetNdivisions(502)
    zero = hold(ROOT.TLine(-.2, 0, 1.2, 0))
    zero.SetLineStyle(2)
    zero.Draw()

    c.cd(2)
    q = style_graph(ROOT.TGraph(2), ROOT.kOrange+7, 21)
    q.SetName("g_chi2_by_step")
    q.SetTitle("Track Fitting quality;Geometry Correction step;#Sigma #chi^{2} / #Sigma stored ACTS nDoF")
    for i, data in enumerate((before, after)):
        q.SetPoint(i, i, data["chi2ndf"])
    q.Draw("ALP")
    q.SetMinimum(0); q.SetMaximum(1.15*max(before["chi2ndf"], after["chi2ndf"]))
    q.GetXaxis().SetLimits(-.2, 1.2)
    q.GetXaxis().SetNdivisions(502)

    c.cd(3)
    correction=style_graph(ROOT.TGraph(2),GREEN,21)
    correction.SetName("g_applied_correction_um")
    correction.SetTitle("Applied L2 X Geometry Correction;Geometry Correction step;Correction [#mum]")
    correction.SetPoint(0,0,0);correction.SetPoint(1,1,applied)
    correction.Draw("ALP")

    return c


def make_residual_distributions(before,after):
    c=hold(ROOT.TCanvas("c_hit_residuals","Unique event/layer hit pairs",1500,650))
    c.Divide(5,2)
    for row,key in enumerate(("deltas","deltas_y")):
        for layer in range(5):
            c.cd(row*5+layer+1)
            arrays=[before[key][layer],after[key][layer]]
            lo=min(float(a.min()) for a in arrays)-20;hi=max(float(a.max()) for a in arrays)+20
            hs=[]
            for label,arr,color in zip(("before","after"),arrays,(BLUE,GREEN)):
                h=hold(ROOT.TH1D(f"h_{label}_L{layer}_{row}",f"L{layer};Rec-Sim {'x' if row==0 else 'y'} [#mum];Pairs",80,lo,hi))
                h.SetLineColor(color);h.SetLineWidth(2)
                for v in arr:h.Fill(float(v))
                hs.append(h)
            hs[0].SetMaximum(max(h.GetMaximum() for h in hs)*1.2)
            hs[0].Draw("HIST");hs[1].Draw("HIST SAME")
    return c






def main():
    ap=argparse.ArgumentParser(description="Render saved Closure metrics with ROOT")
    for key in ("nominal","misaligned","corrected","summary"):
        ap.add_argument("--"+key,type=Path,required=True)
    ap.add_argument("--outdir",type=Path,required=True,help="New output directory")
    args=ap.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=False)
    nominal,simulated,corrected=[geometry(getattr(args,k)) for k in ("nominal","misaligned","corrected")]
    summary=json.loads(args.summary.read_text())
    before,after=summary['before'],summary['after']
    for data in (before,after):
        for key in ('deltas','deltas_y'):data[key]=[np.asarray(a) for a in data[key]]
    applied=summary['applied_geometry_correction_um']
    f=ROOT.TFile(str(args.outdir/"alignment.root"),"CREATE")
    if not f or f.IsZombie():raise RuntimeError("Cannot create ROOT output")
    try:
        canvases=[make_geometry(nominal,simulated,corrected),make_residual_distributions(before,after),make_closure(before,after,applied)]
        for c in canvases:c.Modified();c.Update();c.Write()
        seen=set()
        for obj in HOLD:
            if (obj.InheritsFrom("TH1") or obj.InheritsFrom("TGraph")) and obj.GetName() not in seen:
                obj.Write();seen.add(obj.GetName())
    finally:f.Close()
    print(f"ROOT output: {args.outdir/'alignment.root'}")

if __name__=="__main__":main()
