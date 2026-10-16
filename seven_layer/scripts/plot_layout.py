#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


COLOR = {
    "SiMAPS": "#d62728",
    "MPGD": "#1f77b4",
    "ACLGAD": "#2ca02c",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    planes = cfg["planes"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)

    for p in planes:
        det = p["detector"]
        z = p["z_mm"]
        sx, sy = p["active_size_mm"]
        c = COLOR.get(det, "#666666")

        ax1.plot([z, z], [-sx / 2.0, sx / 2.0], color=c, linewidth=3)
        ax1.text(z, sx / 2.0 + 4, f"L{p['global_layer_id']} {det}", rotation=90, va="bottom", ha="center", fontsize=8)

        rect = plt.Rectangle((-sx / 2.0, -sy / 2.0), sx, sy, fill=False, edgecolor=c, linewidth=2)
        ax2.add_patch(rect)
        ax2.text(0, 0, "beam axis", fontsize=8, ha="center", va="center", color="#444444")

    ax1.set_title("Seven-layer telescope layout: z vs active x extent")
    ax1.set_xlabel("z [mm]")
    ax1.set_ylabel("x [mm]")
    ax1.grid(True, alpha=0.3)

    ax2.set_title("Transverse active area (all planes: 100 mm x 100 mm)")
    ax2.set_xlabel("x [mm]")
    ax2.set_ylabel("y [mm]")
    ax2.set_aspect("equal")
    ax2.set_xlim(-60, 60)
    ax2.set_ylim(-60, 60)
    ax2.grid(True, alpha=0.3)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=170)


if __name__ == "__main__":
    main()
