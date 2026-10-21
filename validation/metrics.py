"""Numerical residual and Closure metrics; no ROOT rendering dependency."""
import json
import math
import awkward as ak
import numpy as np
import uproot
from geometry.placements import geometry

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


def mean_error(a):
    return float(a.mean()), float(a.std(ddof=1) / math.sqrt(len(a))) if len(a)>1 else 0.


def serializable(data):
    return {k: ([a.tolist() for a in v] if k in ("deltas","deltas_y") else v) for k,v in data.items()}


def calculate(args):
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
    if args.reference:
        ref=json.loads(args.reference.read_text());checks=[]
        for side in ("before","after"):
            d=summary[side];target=ref[side]
            checks.extend([d["tracks"]==target["tracks"],d["events"]==target["events"],
                           abs(d["pooled_mean_x_um"][2]-target["l2_mean_um"])<=ref["tolerance_residual_um"],
                           abs(d["chi2ndf"]-target["chi2ndf"])<=ref["tolerance_chi2ndf"]])
        checks.append(abs(applied-ref["correction_um"])<=ref["tolerance_correction_um"])
        summary["reference_passed"]=all(checks)
    return summary
