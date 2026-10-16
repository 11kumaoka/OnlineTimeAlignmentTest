#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot


def arr(tree, name):
    return tree[name].array(library="ak")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    t = uproot.open(args.input)["events"]

    central_meas = arr(t, "CentralTrackerMeasurements/CentralTrackerMeasurements.surface")
    central_seeds = arr(t, "CentralTrackSeeds/CentralTrackSeeds.quality")
    central_tracks = arr(t, "CentralCKFTracks/CentralCKFTracks.chi2")
    central_ndf = arr(t, "CentralCKFTracks/CentralCKFTracks.ndf")
    central_tracks_unfiltered = arr(t, "CentralCKFTracksUnfiltered/CentralCKFTracksUnfiltered.chi2")
    central_truth_tracks = arr(t, "CentralCKFTruthSeededTracks/CentralCKFTruthSeededTracks.chi2")
    central_truth_tracks_unfiltered = arr(t, "CentralCKFTruthSeededTracksUnfiltered/CentralCKFTruthSeededTracksUnfiltered.chi2")
    b0_tracks = arr(t, "B0TrackerCKFTracks/B0TrackerCKFTracks.chi2")

    n_events = int(len(central_meas))
    n_meas = ak.to_numpy(ak.num(central_meas))
    n_seeds = ak.to_numpy(ak.num(central_seeds))
    n_ctrk = ak.to_numpy(ak.num(central_tracks))
    n_b0trk = ak.to_numpy(ak.num(b0_tracks))
    n_ctrk_unf = ak.to_numpy(ak.num(central_tracks_unfiltered))
    n_ctrk_truth = ak.to_numpy(ak.num(central_truth_tracks))
    n_ctrk_truth_unf = ak.to_numpy(ak.num(central_truth_tracks_unfiltered))

    chi2 = ak.to_numpy(ak.flatten(central_tracks, axis=None)) if ak.sum(ak.num(central_tracks)) > 0 else np.array([])
    ndf = ak.to_numpy(ak.flatten(central_ndf, axis=None)) if ak.sum(ak.num(central_ndf)) > 0 else np.array([])

    summary = {
        "input_file": str(args.input),
        "n_events": n_events,
        "central_measurements": {
            "mean_per_event": float(np.mean(n_meas)),
            "min_per_event": int(np.min(n_meas)),
            "max_per_event": int(np.max(n_meas)),
        },
        "central_track_seeds": {
            "mean_per_event": float(np.mean(n_seeds)),
            "min_per_event": int(np.min(n_seeds)),
            "max_per_event": int(np.max(n_seeds)),
        },
        "central_ckf_tracks": {
            "mean_per_event": float(np.mean(n_ctrk)),
            "min_per_event": int(np.min(n_ctrk)),
            "max_per_event": int(np.max(n_ctrk)),
            "total": int(np.sum(n_ctrk)),
        },
        "central_ckf_tracks_unfiltered": {
            "mean_per_event": float(np.mean(n_ctrk_unf)),
            "min_per_event": int(np.min(n_ctrk_unf)),
            "max_per_event": int(np.max(n_ctrk_unf)),
            "total": int(np.sum(n_ctrk_unf)),
        },
        "central_ckf_truth_seeded_tracks": {
            "mean_per_event": float(np.mean(n_ctrk_truth)),
            "min_per_event": int(np.min(n_ctrk_truth)),
            "max_per_event": int(np.max(n_ctrk_truth)),
            "total": int(np.sum(n_ctrk_truth)),
        },
        "central_ckf_truth_seeded_tracks_unfiltered": {
            "mean_per_event": float(np.mean(n_ctrk_truth_unf)),
            "min_per_event": int(np.min(n_ctrk_truth_unf)),
            "max_per_event": int(np.max(n_ctrk_truth_unf)),
            "total": int(np.sum(n_ctrk_truth_unf)),
        },
        "b0_ckf_tracks": {
            "mean_per_event": float(np.mean(n_b0trk)),
            "min_per_event": int(np.min(n_b0trk)),
            "max_per_event": int(np.max(n_b0trk)),
            "total": int(np.sum(n_b0trk)),
        },
        "central_track_fit_quality": {
            "chi2_mean": float(np.mean(chi2)) if chi2.size else None,
            "chi2_median": float(np.median(chi2)) if chi2.size else None,
            "ndf_mean": float(np.mean(ndf)) if ndf.size else None,
            "chi2_over_ndf_mean": float(np.mean(chi2 / np.maximum(ndf, 1e-9))) if chi2.size and ndf.size else None,
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
