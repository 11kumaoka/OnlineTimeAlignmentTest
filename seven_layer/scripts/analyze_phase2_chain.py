#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot


def decode_layer(cellids):
    arr = np.asarray(cellids, dtype=np.uint64)
    return ((arr >> 11) & ((1 << 6) - 1)).astype(int)


def has_branch(tree, branch):
    return branch in tree.keys()


def flatten(arr):
    if ak.sum(ak.num(arr)) == 0:
        return np.array([])
    return ak.to_numpy(ak.flatten(arr, axis=None))


def counts_per_event(tree, coll, field):
    branch = f"{coll}/{coll}.{field}"
    if not has_branch(tree, branch):
        return None, None
    data = tree[branch].array(library="ak")
    n = ak.to_numpy(ak.num(data))
    return n, data


def summarize_collection(tree, coll):
    n, data = counts_per_event(tree, coll, "cellID")
    if n is None:
        return {
            "present": False,
            "events": 0,
            "total": 0,
            "mean_per_event": 0.0,
            "min_per_event": 0,
            "max_per_event": 0,
            "layers": {},
        }
    flat = flatten(data)
    out = {
        "present": True,
        "events": int(len(n)),
        "total": int(np.sum(n)),
        "mean_per_event": float(np.mean(n)) if len(n) else 0.0,
        "min_per_event": int(np.min(n)) if len(n) else 0,
        "max_per_event": int(np.max(n)) if len(n) else 0,
        "layers": {},
    }
    if flat.size:
        layers = decode_layer(flat)
        for lid in sorted(np.unique(layers).tolist()):
            out["layers"][str(int(lid))] = int(np.sum(layers == lid))
    return out


def nearest_residuals(tree, sim_coll, rec_coll):
    sx_branch = f"{sim_coll}/{sim_coll}.position.x"
    rx_branch = f"{rec_coll}/{rec_coll}.position.x"
    if not has_branch(tree, sx_branch) or not has_branch(tree, rx_branch):
        return {"present": False, "layers": {}}

    sx = tree[f"{sim_coll}/{sim_coll}.position.x"].array(library="ak")
    sy = tree[f"{sim_coll}/{sim_coll}.position.y"].array(library="ak")
    sz = tree[f"{sim_coll}/{sim_coll}.position.z"].array(library="ak")
    sc = tree[f"{sim_coll}/{sim_coll}.cellID"].array(library="ak")

    rx = tree[f"{rec_coll}/{rec_coll}.position.x"].array(library="ak")
    ry = tree[f"{rec_coll}/{rec_coll}.position.y"].array(library="ak")
    rz = tree[f"{rec_coll}/{rec_coll}.position.z"].array(library="ak")
    rc = tree[f"{rec_coll}/{rec_coll}.cellID"].array(library="ak")

    result = {}

    n_events = len(sx)
    for iev in range(n_events):
        sim_layer = decode_layer(np.asarray(ak.to_numpy(sc[iev]), dtype=np.uint64)) if len(sc[iev]) else np.array([], dtype=int)
        rec_layer = decode_layer(np.asarray(ak.to_numpy(rc[iev]), dtype=np.uint64)) if len(rc[iev]) else np.array([], dtype=int)

        sxi = ak.to_numpy(sx[iev]) if len(sx[iev]) else np.array([])
        syi = ak.to_numpy(sy[iev]) if len(sy[iev]) else np.array([])
        szi = ak.to_numpy(sz[iev]) if len(sz[iev]) else np.array([])
        rxi = ak.to_numpy(rx[iev]) if len(rx[iev]) else np.array([])
        ryi = ak.to_numpy(ry[iev]) if len(ry[iev]) else np.array([])
        rzi = ak.to_numpy(rz[iev]) if len(rz[iev]) else np.array([])

        for lid in sorted(set(sim_layer.tolist()) | set(rec_layer.tolist())):
            sm = np.where(sim_layer == lid)[0]
            rm = np.where(rec_layer == lid)[0]
            if len(sm) == 0 or len(rm) == 0:
                continue
            for ridx in rm:
                d2 = (sxi[sm] - rxi[ridx]) ** 2 + (syi[sm] - ryi[ridx]) ** 2 + (szi[sm] - rzi[ridx]) ** 2
                j = sm[int(np.argmin(d2))]
                result.setdefault(str(int(lid)), {"dx": [], "dy": [], "dz": []})
                result[str(int(lid))]["dx"].append(float(rxi[ridx] - sxi[j]))
                result[str(int(lid))]["dy"].append(float(ryi[ridx] - syi[j]))
                result[str(int(lid))]["dz"].append(float(rzi[ridx] - szi[j]))

    stats = {}
    for lid, vals in result.items():
        dx = np.array(vals["dx"])
        dy = np.array(vals["dy"])
        dz = np.array(vals["dz"])
        stats[lid] = {
            "n_matches": int(len(dx)),
            "dx_mean_mm": float(np.mean(dx)),
            "dx_std_mm": float(np.std(dx, ddof=1)) if len(dx) > 1 else 0.0,
            "dy_mean_mm": float(np.mean(dy)),
            "dy_std_mm": float(np.std(dy, ddof=1)) if len(dy) > 1 else 0.0,
            "dz_mean_mm": float(np.mean(dz)),
            "dz_std_mm": float(np.std(dz, ddof=1)) if len(dz) > 1 else 0.0,
        }
    return {"present": True, "layers": stats}


def summarize_tracks(tree):
    chi2_branch = "CentralCKFTruthSeededTracks/CentralCKFTruthSeededTracks.chi2"
    if not has_branch(tree, chi2_branch):
        return {
            "present": False,
            "events": 0,
            "total_tracks": 0,
            "mean_per_event": 0.0,
            "min_per_event": 0,
            "max_per_event": 0,
            "chi2_mean": None,
            "ndf_mean": None,
            "chi2_over_ndf_mean": None,
        }

    tchi2 = tree["CentralCKFTruthSeededTracks/CentralCKFTruthSeededTracks.chi2"].array(library="ak")
    tndf = tree["CentralCKFTruthSeededTracks/CentralCKFTruthSeededTracks.ndf"].array(library="ak")
    n = ak.to_numpy(ak.num(tchi2))
    chi2 = flatten(tchi2)
    ndf = flatten(tndf)
    return {
        "present": True,
        "events": int(len(n)),
        "total_tracks": int(np.sum(n)),
        "mean_per_event": float(np.mean(n)) if len(n) else 0.0,
        "min_per_event": int(np.min(n)) if len(n) else 0,
        "max_per_event": int(np.max(n)) if len(n) else 0,
        "chi2_mean": float(np.mean(chi2)) if len(chi2) else None,
        "ndf_mean": float(np.mean(ndf)) if len(ndf) else None,
        "chi2_over_ndf_mean": float(np.mean(chi2 / np.maximum(ndf, 1e-9))) if len(chi2) and len(ndf) else None,
    }


def summarize_measurements(tree):
    surf_branch = "CentralTrackerMeasurements/CentralTrackerMeasurements.surface"
    if not has_branch(tree, surf_branch):
        return {
            "present": False,
            "events": 0,
            "total_measurements": 0,
            "mean_per_event": 0.0,
            "min_per_event": 0,
            "max_per_event": 0,
            "n_unique_surfaces": 0,
            "loc_a_std": 0.0,
            "loc_b_std": 0.0,
        }

    surf = tree["CentralTrackerMeasurements/CentralTrackerMeasurements.surface"].array(library="ak")
    loc_a = tree["CentralTrackerMeasurements/CentralTrackerMeasurements.loc.a"].array(library="ak")
    loc_b = tree["CentralTrackerMeasurements/CentralTrackerMeasurements.loc.b"].array(library="ak")

    n = ak.to_numpy(ak.num(surf))
    flat_s = flatten(surf)
    return {
        "present": True,
        "events": int(len(n)),
        "total_measurements": int(np.sum(n)),
        "mean_per_event": float(np.mean(n)) if len(n) else 0.0,
        "min_per_event": int(np.min(n)) if len(n) else 0,
        "max_per_event": int(np.max(n)) if len(n) else 0,
        "n_unique_surfaces": int(len(np.unique(flat_s))) if len(flat_s) else 0,
        "loc_a_std": float(np.std(flatten(loc_a), ddof=1)) if ak.sum(ak.num(loc_a)) > 1 else 0.0,
        "loc_b_std": float(np.std(flatten(loc_b), ddof=1)) if ak.sum(ak.num(loc_b)) > 1 else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    t = uproot.open(args.input)["events"]

    collections = {
        "sim": ["SiMAPSHits", "MPGDHits", "ACLGADHits"],
        "raw": ["SiMAPSRawHits", "MPGDRawHits", "ACLGADRawHits"],
        "rec": ["SiMAPSRecHits", "MPGDRecHits", "ACLGADRecHits"],
    }

    out = {"input": str(args.input), "collections": {}, "residuals": {}, "measurements": {}, "tracks": {}}

    for stage, names in collections.items():
        out["collections"][stage] = {}
        for name in names:
            out["collections"][stage][name] = summarize_collection(t, name)

    out["residuals"]["SiMAPSRec_vs_SiMAPSHits"] = nearest_residuals(t, "SiMAPSHits", "SiMAPSRecHits")
    out["residuals"]["MPGDRec_vs_MPGDHits"] = nearest_residuals(t, "MPGDHits", "MPGDRecHits")
    out["residuals"]["ACLGADRec_vs_ACLGADHits"] = nearest_residuals(t, "ACLGADHits", "ACLGADRecHits")

    out["measurements"] = summarize_measurements(t)
    out["tracks"]["CentralCKFTruthSeededTracks"] = summarize_tracks(t)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
