#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def fit_line(z, u):
    a, b = np.polyfit(z, u, 1)
    return a, b


def predict(a, b, z):
    return a * z + b


def run_demo(config_path, n_tracks, seed, out_dir):
    rng = np.random.default_rng(seed)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    layers = cfg["layers"]
    z = np.array([layer["z_mm"] for layer in layers], dtype=float)
    sig_x = np.array([layer["sigma_x_mm"] for layer in layers], dtype=float)
    sig_y = np.array([layer["sigma_y_mm"] for layer in layers], dtype=float)

    inj = cfg["alignment_injection"]
    inj_layer = int(inj["layer_id"])
    inj_dx = float(inj["dx_mm"])
    inj_dy = float(inj["dy_mm"])

    x0 = rng.uniform(-1.0, 1.0, size=n_tracks)
    y0 = rng.uniform(-1.0, 1.0, size=n_tracks)
    tx = rng.normal(0.0, 1.5e-3, size=n_tracks)
    ty = rng.normal(0.0, 1.5e-3, size=n_tracks)

    x_true = x0[:, None] + tx[:, None] * z[None, :]
    y_true = y0[:, None] + ty[:, None] * z[None, :]

    x_meas = x_true + rng.normal(0.0, sig_x[None, :], size=(n_tracks, len(z)))
    y_meas = y_true + rng.normal(0.0, sig_y[None, :], size=(n_tracks, len(z)))

    x_meas[:, inj_layer] += inj_dx
    y_meas[:, inj_layer] += inj_dy

    resid_x = {i: [] for i in range(len(z))}
    resid_y = {i: [] for i in range(len(z))}

    for itrk in range(n_tracks):
        for ilayer in range(len(z)):
            mask = np.ones(len(z), dtype=bool)
            mask[ilayer] = False

            ax, bx = fit_line(z[mask], x_meas[itrk, mask])
            ay, by = fit_line(z[mask], y_meas[itrk, mask])

            rx = x_meas[itrk, ilayer] - predict(ax, bx, z[ilayer])
            ry = y_meas[itrk, ilayer] - predict(ay, by, z[ilayer])

            resid_x[ilayer].append(rx)
            resid_y[ilayer].append(ry)

    stats = []
    for ilayer in range(len(z)):
        rx = np.array(resid_x[ilayer])
        ry = np.array(resid_y[ilayer])
        stats.append(
            {
                "layer_id": ilayer,
                "z_mm": float(z[ilayer]),
                "resid_x_mean_mm": float(np.mean(rx)),
                "resid_x_std_mm": float(np.std(rx, ddof=1)),
                "resid_y_mean_mm": float(np.mean(ry)),
                "resid_y_std_mm": float(np.std(ry, ddof=1)),
            }
        )

    est_dx = -stats[inj_layer]["resid_x_mean_mm"]
    est_dy = -stats[inj_layer]["resid_y_mean_mm"]

    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "five_layer_residual_stats.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": cfg,
                "n_tracks": n_tracks,
                "seed": seed,
                "leave_one_out_residuals": stats,
                "alignment_estimate": {
                    "target_layer": inj_layer,
                    "injected_dx_mm": inj_dx,
                    "injected_dy_mm": inj_dy,
                    "estimated_correction_dx_mm": est_dx,
                    "estimated_correction_dy_mm": est_dy,
                },
            },
            f,
            indent=2,
        )

    fig, axes = plt.subplots(2, len(z), figsize=(3.6 * len(z), 6), sharey="row")
    for i in range(len(z)):
        rx = np.array(resid_x[i])
        ry = np.array(resid_y[i])
        axes[0, i].hist(rx, bins=50, color="#1f77b4", alpha=0.85)
        axes[0, i].set_title(f"Layer {i} z={z[i]:.0f} mm")
        axes[0, i].set_xlabel("x residual [mm]")
        axes[1, i].hist(ry, bins=50, color="#d62728", alpha=0.85)
        axes[1, i].set_xlabel("y residual [mm]")

    axes[0, 0].set_ylabel("Entries")
    axes[1, 0].set_ylabel("Entries")
    fig.suptitle("Five-layer leave-one-out residuals")
    fig.tight_layout()
    fig.savefig(out_dir / "five_layer_residual_histograms.png", dpi=160)
    plt.close(fig)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(projection="3d")
    n_draw = min(30, n_tracks)
    for itrk in range(n_draw):
        ax.plot(x_meas[itrk], z, y_meas[itrk], alpha=0.35, color="#2ca02c")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("z [mm]")
    ax.set_zlabel("y [mm]")
    ax.set_title("Measured hits (subset of tracks)")
    fig.tight_layout()
    fig.savefig(out_dir / "five_layer_track_display.png", dpi=160)
    plt.close(fig)

    print("Five-layer demo complete")
    print(f"Tracks: {n_tracks}")
    print(f"Injected layer: {inj_layer}")
    print(f"Injected dx, dy [mm]: {inj_dx:.5f}, {inj_dy:.5f}")
    print(f"Estimated correction dx, dy [mm]: {est_dx:.5f}, {est_dy:.5f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--n-tracks", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    run_demo(args.config, args.n_tracks, args.seed, args.out_dir)


if __name__ == "__main__":
    main()
