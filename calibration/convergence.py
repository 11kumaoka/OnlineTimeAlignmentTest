"""Provisional demonstration gates; not detector-calibration certification."""
import math


def evaluate(delta_mm,chi2_ratio,tracks,policy):
    if not all(math.isfinite(x) for x in (delta_mm,chi2_ratio)):raise RuntimeError('Non-finite calibration metric')
    if abs(delta_mm)>policy['max_update_mm']:raise RuntimeError('L2 update exceeds configured demonstration bound')
    if tracks<policy['min_tracks']:raise RuntimeError('Insufficient tracks for configured demonstration policy')
    if chi2_ratio>policy['max_track_chi2_ratio']:raise RuntimeError('Track chi2 ratio exceeds configured demonstration bound')
    return {'converged':abs(delta_mm)<=policy['delta_tolerance_mm'],
            'delta_mm':delta_mm,'track_chi2_ratio':chi2_ratio,'tracks':tracks,
            'policy_label':policy['policy_label']}


def evaluate_rotation(delta_rad,chi2_ratio,tracks,policy):
    """Apply angular bounds in radians; never compare angles with an mm tolerance."""
    if not math.isfinite(delta_rad):raise RuntimeError('Non-finite angular update')
    if abs(delta_rad)>policy['max_update_rad']:raise RuntimeError('Rotation update exceeds configured demonstration bound')
    metrics=evaluate(0.,chi2_ratio,tracks,policy)
    metrics.pop('delta_mm')
    metrics.update(converged=abs(delta_rad)<=policy['delta_tolerance_rad'],delta_rad=delta_rad)
    return metrics
