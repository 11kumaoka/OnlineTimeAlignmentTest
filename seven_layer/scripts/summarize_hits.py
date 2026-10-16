#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot


def decode_cellid(cellids):
    arr = np.asarray(cellids, dtype=np.uint64)
    system = arr & ((1 << 8) - 1)
    barrel = (arr >> 8) & ((1 << 3) - 1)
    layer = (arr >> 11) & ((1 << 6) - 1)
    module = (arr >> 17) & ((1 << 10) - 1)
    sensor = (arr >> 27) & ((1 << 4) - 1)
    return system.astype(int), barrel.astype(int), layer.astype(int), module.astype(int), sensor.astype(int)


def summarize_collection(tree, name):
    prefix = f"{name}/{name}"
    cell = tree[f"{prefix}.cellID"].array(library="ak")
    x = tree[f"{prefix}.position.x"].array(library="ak")
    y = tree[f"{prefix}.position.y"].array(library="ak")
    z = tree[f"{prefix}.position.z"].array(library="ak")

    n_per_event = ak.to_numpy(ak.num(cell))

    flat_cell = ak.to_numpy(ak.flatten(cell, axis=None)) if ak.sum(ak.num(cell)) > 0 else np.array([], dtype=np.uint64)
    flat_x = ak.to_numpy(ak.flatten(x, axis=None)) if ak.sum(ak.num(x)) > 0 else np.array([], dtype=float)
    flat_y = ak.to_numpy(ak.flatten(y, axis=None)) if ak.sum(ak.num(y)) > 0 else np.array([], dtype=float)
    flat_z = ak.to_numpy(ak.flatten(z, axis=None)) if ak.sum(ak.num(z)) > 0 else np.array([], dtype=float)

    if flat_cell.size == 0:
        return {
            "events": int(len(n_per_event)),
            "hits_total": 0,
            "hits_per_event": {
                "mean": float(np.mean(n_per_event)) if len(n_per_event) else 0.0,
                "min": int(np.min(n_per_event)) if len(n_per_event) else 0,
                "max": int(np.max(n_per_event)) if len(n_per_event) else 0,
            },
            "layers": {},
        }

    system, barrel, layer, module, sensor = decode_cellid(flat_cell)

    layer_summary = {}
    for lid in sorted(np.unique(layer).tolist()):
        m = layer == lid
        layer_summary[str(int(lid))] = {
            "n_hits": int(np.sum(m)),
            "system_ids": sorted(np.unique(system[m]).astype(int).tolist()),
            "module_ids": sorted(np.unique(module[m]).astype(int).tolist()),
            "sensor_ids": sorted(np.unique(sensor[m]).astype(int).tolist()),
            "z_mean_mm": float(np.mean(flat_z[m])),
            "z_std_mm": float(np.std(flat_z[m])),
            "x_mean_mm": float(np.mean(flat_x[m])),
            "y_mean_mm": float(np.mean(flat_y[m])),
        }

    return {
        "events": int(len(n_per_event)),
        "hits_total": int(flat_cell.size),
        "hits_per_event": {
            "mean": float(np.mean(n_per_event)),
            "min": int(np.min(n_per_event)),
            "max": int(np.max(n_per_event)),
        },
        "layers": layer_summary,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    tree = uproot.open(args.input)["events"]

    collections = ["SiMAPSHits", "MPGDHits", "ACLGADHits"]
    summary = {
        "input": str(args.input),
        "collections": {},
    }

    for c in collections:
        summary["collections"][c] = summarize_collection(tree, c)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
