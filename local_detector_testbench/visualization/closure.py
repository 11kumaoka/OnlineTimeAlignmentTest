#!/usr/bin/env python3
"""ROOT geometry, hit-residual and one-update closure visualization.
All six input files and a NEW output directory must be supplied; see --help.
PyROOT draws and stores objects; uproot/awkward decode PODIO split branches.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import math
import xml.etree.ElementTree as ET

import awkward as ak
import numpy as np
import uproot
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadLeftMargin(0.15)
ROOT.gStyle.SetPadBottomMargin(0.14)

BLUE, GREEN = ROOT.kAzure + 1, ROOT.kGreen + 2
HOLD = []  # Keep PyROOT-owned graphics objects alive until TCanvas.Write().


def hold(obj):
    HOLD.append(obj)
    return obj


def xml_number(expr, constants):
    """Evaluate only arithmetic/constants used by this specific compact XML."""
    units = {"mm": 1., "cm": 10., "m": 1000., "um": .001, "pi": math.pi}

    def walk(node, stack):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id in units:
                return units[node.id]
            if node.id not in constants or node.id in stack:
                raise ValueError(f"Unsupported or recursive XML symbol: {node.id}")
            return walk(ast.parse(constants[node.id], mode="eval").body, stack | {node.id})
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = walk(node.operand, stack)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = walk(node.left, stack), walk(node.right, stack)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            return a / b
        raise ValueError(f"Unsupported XML arithmetic: {expr}")

    return walk(ast.parse(expr, mode="eval").body, set())


def geometry(path):
    """Validated for this telescope's DD4hep_SiTrackerEndcap2, phi0=0, nmodules=1.

    The DD4hep detector builder places a ring module at global x = -r at phi0=0.
    This is a placement preview, NOT a generic GDML/TGeo geometry converter.
    """
    root = ET.parse(path).getroot()
    constants = {c.attrib["name"]: c.attrib["value"] for c in root.findall("./define/constant")}
    result = {}
    for det in root.findall("./detectors/detector"):
        name = det.get("name")
        if name not in ("SiMAPS", "MPGDPlane", "ACLGADPlane"):
            continue
        if det.get("type") != "DD4hep_SiTrackerEndcap2":
            raise RuntimeError(f"Unexpected detector builder: {name}")
        for layer in det.findall("layer"):
            for ring in layer.findall("ring"):
                if ring.get("nmodules") != "1":
                    raise RuntimeError("Viewer supports only a single module per layer")
                phi = xml_number(ring.get("phi0", "0"), constants)
                if abs(phi) > 1e-12:
                    raise RuntimeError("Viewer assumes phi0=0")
                z = xml_number(ring.attrib["zstart"], constants) + xml_number(ring.get("dz", "0"), constants)
                x = -xml_number(ring.attrib["r"], constants)
                lid = int(layer.attrib["id"])
                result[lid] = (x, z, name)
    if set(result) != set(range(7)):
        raise RuntimeError(f"Expected seven layers L0..L6 in {path}, got {sorted(result)}")
    return result


def root_branch(tree, coll, field):
    key = f"{coll}/{coll}.{field}"
    if key not in tree:
        raise RuntimeError(f"Missing PODIO branch {key}")
    return tree[key].array(library="ak")


def measurements(path):
    """Keep historical pooled means AND uniquely matched per-hit distributions."""
    with uproot.open(path) as f:
        t = f["events"]
        sc = root_branch(t, "SiMAPSHits", "cellID")
        rc = root_branch(t, "LocalSiMAPSRecHits", "cellID")
        coords = {a: (root_branch(t,"SiMAPSHits","position."+a),
                      root_branch(t,"LocalSiMAPSRecHits","position."+a)) for a in ("x","y")}
        chi2 = root_branch(t, "LocalBeamTestTracks", "chi2")
        ndf = root_branch(t, "LocalBeamTestTracks", "ndf")
    sl, rl = (sc >> 11) & 63, (rc >> 11) & 63
    result = {"events":len(sc), "tracks":int(ak.sum(ak.num(chi2))),
              "chi2":float(ak.sum(chi2)), "stored_ndf":float(ak.sum(ndf))}
    if result["stored_ndf"]<=0: raise RuntimeError("No fitted track dimensions")
    result["chi2ndf"]=result["chi2"]/result["stored_ndf"]
    for axis,(sim,rec) in coords.items():
        pairs=[[] for _ in range(5)]; pooled=[]; skipped=[]
        for layer in range(5):
            sv=ak.to_numpy(ak.flatten(sim[sl==layer]));rv=ak.to_numpy(ak.flatten(rec[rl==layer]))
            if not len(sv) or not len(rv):raise RuntimeError("Empty layer")
            pooled.append(float(1000*(rv.mean()-sv.mean())))
            excluded=0
            for ev in range(len(sc)):
                a=ak.to_numpy(sim[ev][sl[ev]==layer]);b=ak.to_numpy(rec[ev][rl[ev]==layer])
                if len(a)==len(b)==1:pairs[layer].append(float(1000*(b[0]-a[0])))
                else:excluded+=1
            if not pairs[layer]:raise RuntimeError("No unique hit pairs")
            skipped.append(excluded)
        result["deltas" if axis=="x" else "deltas_y"]=[np.asarray(v) for v in pairs]
        result["pooled_mean_"+axis+"_um"]=pooled
        result["excluded_"+axis+"_by_layer"]=skipped
    result["skipped"]=sum(result["excluded_x_by_layer"])
    return result


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


def mean_error(a):
    return float(a.mean()), float(a.std(ddof=1) / math.sqrt(len(a))) if len(a)>1 else 0.


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


def serializable(data):
    return {k: ([a.tolist() for a in v] if k in ("deltas","deltas_y") else v) for k,v in data.items()}


def main():
    import json
    ap=argparse.ArgumentParser(description="ROOT geometry, hit residual and one-update alignment closure")
    for key in ("nominal","misaligned","corrected","before","after","pede"):
        ap.add_argument("--"+key,type=Path,required=True)
    ap.add_argument("--outdir",type=Path,required=True,help="New directory; refuses overwrite")
    ap.add_argument("--reference",type=Path,help="Optional numerical regression reference")
    args=ap.parse_args()
    for key in ("nominal","misaligned","corrected","before","after","pede"):
        if not getattr(args,key).is_file():raise FileNotFoundError(getattr(args,key))
    args.outdir.mkdir(parents=True,exist_ok=False)
    nominal,simulated,corrected=[geometry(getattr(args,k)) for k in ("nominal","misaligned","corrected")]
    before,after=measurements(args.before),measurements(args.after)
    bias=None
    for line in args.pede.read_text().splitlines():
        fields=line.split()
        if fields and fields[0]=="1002":bias=float(fields[1])*1000
    if bias is None:raise RuntimeError("Missing L2 pede bias")
    applied=(corrected[2][0]-nominal[2][0])*1000
    if abs(applied+bias)>0.01:raise RuntimeError("Geometry/pede correction sign mismatch")
    summary={"before":serializable(before),"after":serializable(after),
             "pede_l2_bias_um":bias,"applied_geometry_correction_um":applied,
             "note":"Geometry update step, not internal pede iteration. stored ACTS nDoF convention retained.",
             "metric_definition":"Historical pooled Rec mean minus Sim mean; per-hit plots use unique event/layer pairs."}
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
    if args.reference:
        ref=json.loads(args.reference.read_text());checks=[]
        for side in ("before","after"):
            d=summary[side];target=ref[side]
            checks.extend([d["tracks"]==target["tracks"],d["events"]==target["events"],
                           abs(d["pooled_mean_x_um"][2]-target["l2_mean_um"])<=ref["tolerance_residual_um"],
                           abs(d["chi2ndf"]-target["chi2ndf"])<=ref["tolerance_chi2ndf"]])
        checks.append(abs(applied-ref["correction_um"])<=ref["tolerance_correction_um"])
        summary["reference_passed"]=all(checks)
    with (args.outdir/"summary.json").open("x") as out:json.dump(summary,out,indent=2);out.write("\n")
    for side in ("before","after"):
        d=summary[side];print(f"{side}: events={d['events']} tracks={d['tracks']} L2={d['pooled_mean_x_um'][2]:.6f} um chi2/storedNDF={d['chi2ndf']:.6f}")
    print(f"Applied L2 X correction: {applied:.6f} um; ROOT file: {args.outdir/'alignment.root'}")
    if summary.get("reference_passed") is False:raise SystemExit("Reference comparison FAILED; inspect retained summary")

if __name__=="__main__":main()
