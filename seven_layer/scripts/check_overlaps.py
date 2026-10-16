#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gdml", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    ROOT.TGeoManager.Import(str(args.gdml))
    geo = ROOT.gGeoManager

    geo.CheckOverlaps(0.001)
    overlaps = geo.GetListOfOverlaps()
    n_overlaps = int(overlaps.GetEntries()) if overlaps else 0

    names = []
    if overlaps:
        for i in range(min(n_overlaps, 20)):
            names.append(str(overlaps.At(i).GetName()))

    result = {
        "gdml": str(args.gdml),
        "n_overlaps": n_overlaps,
        "sample_overlap_names": names,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
