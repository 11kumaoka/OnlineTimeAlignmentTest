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


def _to_np(x):
    return ak.to_numpy(x) if len(x) else np.array([], dtype=float)


def assoc_residuals(tree, prefix, sim_coll, raw_coll, rec_coll):
    assoc_coll = raw_coll.replace("RawHits", "RawHitAssociations")
    # Rec hit content
    rec_x = tree[f"{rec_coll}/{rec_coll}.position.x"].array(library="ak")
    rec_y = tree[f"{rec_coll}/{rec_coll}.position.y"].array(library="ak")
    rec_z = tree[f"{rec_coll}/{rec_coll}.position.z"].array(library="ak")
    rec_cell = tree[f"{rec_coll}/{rec_coll}.cellID"].array(library="ak")

    # Rec -> Raw relation
    rec_raw_idx = tree[f"_{rec_coll}_rawHit/_{rec_coll}_rawHit.index"].array(library="ak")

    # Raw -> Sim association
    assoc_raw_idx = tree[f"_{assoc_coll}_rawHit/_{assoc_coll}_rawHit.index"].array(library="ak")
    assoc_sim_idx = tree[f"_{assoc_coll}_simHit/_{assoc_coll}_simHit.index"].array(library="ak")

    # Sim content
    sim_x = tree[f"{sim_coll}/{sim_coll}.position.x"].array(library="ak")
    sim_y = tree[f"{sim_coll}/{sim_coll}.position.y"].array(library="ak")
    sim_z = tree[f"{sim_coll}/{sim_coll}.position.z"].array(library="ak")

    per_layer = {}
    per_layer_unique = {}
    n_events = len(rec_x)
    unmatched_rec = 0
    ambiguous_raw_links = 0

    for ev in range(n_events):
        rxi = _to_np(rec_x[ev])
        ryi = _to_np(rec_y[ev])
        rzi = _to_np(rec_z[ev])
        rci = np.asarray(_to_np(rec_cell[ev]), dtype=np.uint64)
        rraw = np.asarray(_to_np(rec_raw_idx[ev]), dtype=np.int64)

        ar = np.asarray(_to_np(assoc_raw_idx[ev]), dtype=np.int64)
        asi = np.asarray(_to_np(assoc_sim_idx[ev]), dtype=np.int64)

        sxi = _to_np(sim_x[ev])
        syi = _to_np(sim_y[ev])
        szi = _to_np(sim_z[ev])

        # map raw-hit index -> first linked sim-hit index (deterministic)
        raw_to_sim = {}
        raw_to_sim_count = {}
        for k in range(len(ar)):
            ridx = int(ar[k])
            raw_to_sim_count[ridx] = raw_to_sim_count.get(ridx, 0) + 1
            if ridx not in raw_to_sim:
                raw_to_sim[ridx] = int(asi[k])

        layers = decode_layer(rci) if len(rci) else np.array([], dtype=int)

        for i in range(len(rxi)):
            ridx = int(rraw[i]) if i < len(rraw) else -1
            if ridx not in raw_to_sim:
                unmatched_rec += 1
                continue
            sidx = raw_to_sim[ridx]
            if sidx < 0 or sidx >= len(sxi):
                unmatched_rec += 1
                continue

            lid = int(layers[i]) if i < len(layers) else -1
            if lid < 0:
                unmatched_rec += 1
                continue

            d = per_layer.setdefault(str(lid), {"dx": [], "dy": [], "dz": []})
            d["dx"].append(float(rxi[i] - sxi[sidx]))
            d["dy"].append(float(ryi[i] - syi[sidx]))
            d["dz"].append(float(rzi[i] - szi[sidx]))

            if raw_to_sim_count.get(ridx, 0) == 1:
                du = per_layer_unique.setdefault(str(lid), {"dx": [], "dy": [], "dz": []})
                du["dx"].append(float(rxi[i] - sxi[sidx]))
                du["dy"].append(float(ryi[i] - syi[sidx]))
                du["dz"].append(float(rzi[i] - szi[sidx]))
            else:
                ambiguous_raw_links += 1

    def stats_map(src):
        out = {}
        for lid, vals in src.items():
            dx = np.asarray(vals["dx"])
            dy = np.asarray(vals["dy"])
            dz = np.asarray(vals["dz"])
            out[lid] = {
                "n_matches": int(len(dx)),
                "dx_mean_mm": float(np.mean(dx)) if len(dx) else None,
                "dx_std_mm": float(np.std(dx, ddof=1)) if len(dx) > 1 else 0.0,
                "dy_mean_mm": float(np.mean(dy)) if len(dy) else None,
                "dy_std_mm": float(np.std(dy, ddof=1)) if len(dy) > 1 else 0.0,
                "dz_mean_mm": float(np.mean(dz)) if len(dz) else None,
                "dz_std_mm": float(np.std(dz, ddof=1)) if len(dz) > 1 else 0.0,
            }
        return out

    out_all = stats_map(per_layer)
    out_unique = stats_map(per_layer_unique)

    return {
        "matches_per_layer": out_all,
        "unique_assoc_matches_per_layer": out_unique,
        "unmatched_rec_hits": int(unmatched_rec),
        "ambiguous_raw_links": int(ambiguous_raw_links),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    t = uproot.open(args.input)["events"]

    result = {
        "input": args.input,
        "association_residuals": {
            "SiMAPS": assoc_residuals(t, "SiMAPS", "SiMAPSHits", "SiMAPSRawHits", "SiMAPSRecHits"),
            "MPGD": assoc_residuals(t, "MPGD", "MPGDHits", "MPGDRawHits", "MPGDRecHits"),
            "ACLGAD": assoc_residuals(t, "ACLGAD", "ACLGADHits", "ACLGADRawHits", "ACLGADRecHits"),
        },
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
