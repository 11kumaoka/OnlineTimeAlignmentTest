#!/usr/bin/env python3
"""Prospective geometry-only containment check for the bounded L1/L2 study.

Use an earlier native equation audit to sample a nominal joint-error ellipsoid.
This fixture-design check neither reads a new fitted correction nor establishes
statistical coverage. It never changes or activates a Geometry version.
"""
import argparse
import itertools
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from geometry.transforms import rotation_exp
from research_common import REPO, digest, done, execute, stage, write_json
from validation.telescope_closure.closure import (
    MODULE_TO_GLOBAL, displaced_xml, environment)
from validation.telescope_closure.containment import corners_in_module
from validation.telescope_closure.multi_information import analyze
from validation.telescope_closure.multi_sensor import (
    fixture, injection, labels, mapping, pose_increments, xml_identity)
from validation.telescope_closure.rotation import pose_checks


def sampled_offsets(covariance, radius=5.):
    """Sample deterministic joint directions and covariance coordinate extrema."""
    covariance = np.asarray(covariance, dtype=float)
    if (covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1]
            or not np.isfinite(covariance).all()):
        raise ValueError('Expected a finite square covariance')
    root = np.linalg.cholesky(covariance)
    n = len(root)
    directions = [np.asarray(v, dtype=float)
                  for v in itertools.product((-1, 0, 1), repeat=n) if any(v)]
    for i in range(n):
        # In whitened coordinates these maximize each correlated physical axis.
        directions.extend((root[i], -root[i]))
    return [radius * root @ (v / np.linalg.norm(v)) for v in directions]


def _mm(value):
    """Read the numeric millimetre literals in the fixed telescope fixture."""
    return float(value.removesuffix('*mm'))


def _bounds(nominal, base, selected):
    """Read the actual unchanged boxes and cylindrical layer envelopes."""
    detector = ET.parse(nominal).getroot().find(
        "./detectors/detector[@name='SiMAPS']")
    result = {}
    for layer in sorted({mapping(k)[0] for k in selected}):
        placement = detector.find(f"./layer[@id='{layer}']")
        module = detector.find(f"./module[@name='{placement.get('module')}']")
        component = module.find('./module_component')
        parent = module.find('./module_envelope')
        barrel = placement.find('./barrel_envelope')
        layout = placement.find('./rphi_layout')
        zlayout = placement.find('./z_layout')
        # The existing barrel fixture has one module at phi=0 and z=0. These
        # checks make its fixed parent-to-world transform explicit.
        assert float(layout.get('phi0')) == float(layout.get('phi_tilt')) == 0
        assert int(layout.get('nphi')) == int(zlayout.get('nz')) == 1
        assert _mm(zlayout.get('z0')) == 0
        assert all(_mm(component.find('./position').get(axis)) == 0
                   for axis in 'xyz')
        center = np.asarray(base[layer]['center_mm'])
        np.testing.assert_allclose(center, [_mm(layout.get('rc')), 0., 0.],
                                   atol=1e-9, rtol=0)
        result[layer] = {
            'module_center_mm': center,
            'module_rotation': np.asarray(MODULE_TO_GLOBAL),
            'sensitive_half_mm': np.asarray([
                _mm(component.get(key)) / 2
                for key in ('width', 'length', 'thickness')]),
            'module_half_mm': np.asarray([
                _mm(parent.get(key)) / 2
                for key in ('width', 'length', 'thickness')]),
            'layer_inner_radius_mm': _mm(barrel.get('inner_r')),
            'layer_outer_radius_mm': _mm(barrel.get('outer_r')),
            'layer_half_z_mm': _mm(barrel.get('z_length')) / 2}
    return result


def _pose_bounds(center, rotation, bounds):
    box = corners_in_module(
        np.asarray(center), np.asarray(rotation), bounds['module_center_mm'],
        bounds['module_rotation'], bounds['sensitive_half_mm'],
        bounds['module_half_mm'])
    corners = np.asarray(box['global_corners_mm'])
    radii = np.linalg.norm(corners[:, :2], axis=1)
    layer_clearance = [
        float(radii.min() - bounds['layer_inner_radius_mm']),
        float(bounds['layer_outer_radius_mm'] - radii.max()),
        float(bounds['layer_half_z_mm'] - np.abs(corners[:, 2]).max())]
    box['layer_clearance_inner_outer_z_mm'] = layer_clearance
    box['contained_in_layer'] = bool(min(layer_clearance) > 0)
    return box


def _candidate(vector, selected, base, bounds):
    values = dict(zip(selected, map(float, vector)))
    shifts, rotations = pose_increments(values)
    report = {}
    for layer, physical in bounds.items():
        center = np.asarray(base[layer]['center_mm']) + [0., shifts.get(layer, 0.), 0.]
        q = np.asarray(rotation_exp(rotations.get(layer, [0., 0., 0.])))
        rotation = q @ np.asarray(base[layer]['dd4hep_rotation'])
        report[str(layer)] = _pose_bounds(center, rotation, physical)
    return {'parameters_mixed_units': list(map(float, vector)), 'sensors': report}


def preflight(build, prior_run, output, mode):
    """Validate both signed fixtures before generating their new channel data."""
    output.mkdir()  # Exclusive, including preservation of partial failures.
    selected = labels(mode)
    nominal = prior_run / 'geometry/fixtures/nominal.xml'
    native = prior_run / 'nominal/mille.json'
    source_geometry = prior_run / 'data/control/channels_truth.json'
    base = json.loads(source_geometry.read_text())['sensors']
    bounds = _bounds(nominal, base, selected)
    design = analyze(native, selected)
    write_json(output / 'prior_information.json', design)
    if design['selected']['rank'] != len(selected):
        raise ValueError('Prospective selected design is not full rank')
    covariance = np.asarray(design['selected']['covariance_mixed_units'])
    offsets = sampled_offsets(covariance)
    plan = {
        'mode': mode, 'labels': selected, 'parameters': design['parameter_definitions'],
        'nominal_sha256': digest(nominal), 'prior_native_sha256': digest(native),
        'prior_geometry_sha256': digest(source_geometry),
        'joint_nominal_radius': 5., 'design_only_engineering_margin': 1.1,
        'sampled_directions_per_sign': len(offsets),
        'coverage_claim': False, 'new_fit_estimates_used': False,
        'geometry_activated': False}
    write_json(output / 'prospective_plan.json', plan)
    reports = []
    positive = mode.removesuffix('_negative')
    for sign, signed_mode in ((1, positive), (-1, positive + '_negative')):
        q = stage(output, 'positive' if sign == 1 else 'negative')
        injected = np.asarray([injection(signed_mode)[k] for k in selected])
        candidates = []
        for index, delta in enumerate(offsets):
            candidate = _candidate(injected + 1.1 * delta, selected, base, bounds)
            candidate['sample_index'] = index
            candidates.append(candidate)
        write_json(q / 'sampled_poses.json', candidates)
        failures = [candidate for candidate in candidates
                    if any(not sensor['contained'] or not sensor['contained_in_layer']
                           for sensor in candidate['sensors'].values())]
        if failures:
            write_json(q / 'refusal.json', {'passed': False,
                'classification': 'PROSPECTIVE_PHYSICAL_CONTAINMENT_REFUSAL',
                'failed_sampled_poses': len(failures), 'first_failure': failures[0]})
            raise ValueError('Prospective joint-error poses exceed fixed physical bounds')
        truth = stage(q, 'truth')
        dy, dw = fixture(signed_mode)
        displaced_xml(nominal, truth / 'geometry.xml', dy, rotations=dw, rotation_axis='xyz')
        xml_identity(nominal, truth / 'geometry.xml', selected)
        execute([build / 'TelescopeChannels', truth / 'geometry.xml', 0,
                 truth / 'geometry.json'], truth, env=environment(build))
        actual = json.loads((truth / 'geometry.json').read_text())['sensors']
        pose_checks(base, actual, dy, dw, axis='xyz')
        truth_checks = {str(layer): _pose_bounds(
            actual[layer]['center_mm'], actual[layer]['dd4hep_rotation'], physical)
            for layer, physical in bounds.items()}
        assert all(item['contained'] and item['contained_in_layer']
                   for item in truth_checks.values())
        worst = []
        for layer in bounds:
            for axis in range(3):
                key = str(layer)
                selected_pose = min(candidates,
                    key=lambda item: item['sensors'][key]['clearance_mm'][axis])
                probe = stage(q, f'worst_layer_{layer}_axis_{axis}')
                values = dict(zip(selected, selected_pose['parameters_mixed_units']))
                dy, dw = pose_increments(values)
                displaced_xml(nominal, probe / 'geometry.xml', dy,
                              rotations=dw, rotation_axis='xyz')
                xml_identity(nominal, probe / 'geometry.xml', selected)
                execute([build / 'TelescopeChannels', probe / 'geometry.xml', 0,
                         probe / 'geometry.json'], probe, env=environment(build))
                actual = json.loads((probe / 'geometry.json').read_text())['sensors']
                pose_checks(base, actual, dy, dw, axis='xyz')
                for sensor_layer, physical in bounds.items():
                    actual_bounds = _pose_bounds(actual[sensor_layer]['center_mm'],
                        actual[sensor_layer]['dd4hep_rotation'], physical)
                    assert actual_bounds['contained'] and actual_bounds['contained_in_layer']
                    predicted = selected_pose['sensors'][str(sensor_layer)]
                    np.testing.assert_allclose(actual_bounds['clearance_mm'],
                        predicted['clearance_mm'], atol=1e-9, rtol=0)
                worst.append({'layer': layer, 'axis': axis,
                              'sample_index': selected_pose['sample_index'],
                              'parameters_mixed_units': selected_pose['parameters_mixed_units']})
        reports.append({'sign': sign, 'mode': signed_mode,
            'injected_parameters_mixed_units': injected.tolist(),
            'sampled_poses': len(candidates), 'truth_bounds': truth_checks,
            'minimum_module_clearance_mm': {str(layer): np.min([
                sample['sensors'][str(layer)]['clearance_mm'] for sample in candidates],
                axis=0).tolist() for layer in bounds},
            'minimum_layer_clearance_inner_outer_z_mm': {str(layer): np.min([
                sample['sensors'][str(layer)]['layer_clearance_inner_outer_z_mm']
                for sample in candidates], axis=0).tolist() for layer in bounds},
            'actual_worst_pose_reloads': worst})
    write_json(output / 'report.json', dict(plan, passed=True,
        reports=reports, all_boxes_and_layers_unchanged=True,
        actual_dd4hep_acts_pose_and_identity_checks=True))
    done(output, passed=True, geometry_only=True, geometry_activated=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--prior-run', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--mode', default='l1_y_rx_ry_rz_l2_y')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if not output.is_relative_to(REPO / 'result') or output == REPO / 'result':
        parser.error('Use a fresh child of result/')
    preflight(args.build.resolve(), args.prior_run.resolve(), output, args.mode)


if __name__ == '__main__':
    main()
