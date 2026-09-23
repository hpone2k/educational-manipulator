"""Read-only independent Blender mass/kinematic/collision screening of EDU06 R06.

Launch with Blender --background --python audit_assembly.py. Does not save the
opened .blend and never edits the builder. Optional args after --: --blend PATH,
--output PATH, --home-only (quick collision diagnostic, not full pose coverage).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import itertools
import json
import math
from pathlib import Path
import re
import sys
import time
import traceback

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parent
PLA_DENSITY_G_MM3 = 0.00124
GRAVITY_M_S2 = 9.81
ALLOWANCE = 1.10
MOTOR_SCREEN = {
    'J2': {'motor': 'XM430-W350-T', 'ratio': None, 'efficiency': .65, 'comparison_nm': .82},
    'J3': {'motor': 'XM430-W350-T', 'ratio': None, 'efficiency': .65, 'comparison_nm': .82},
    'J4': {'motor': 'AX-12A', 'ratio': None, 'efficiency': .65, 'comparison_nm': .30},
    'J5': {'motor': 'AX-12A', 'ratio': 1, 'efficiency': .85, 'comparison_nm': .30},
}


def select_assembly_scene():
    scenes = [scene for scene in bpy.data.scenes if 'Engineering assembly' in scene.name]
    if len(scenes) == 1:
        bpy.context.window.scene = scenes[0]


def actuator_inventory_check():
    motors = [obj for obj in bpy.context.scene.objects if obj.type=='MESH' and
              obj.get('interface_role')=='case' and obj.get('motor_type')]
    rows = [{'object': obj.name, 'motor_id': obj.get('motor_id'), 'model': str(obj['motor_type']),
             'assigned_mass_g': float(obj.get('mass_g', 0))} for obj in motors]
    counts = {model: sum(row['model']==model for row in rows) for model in ('AX-12A','XM430-W350-T')}
    axes = sorted(obj.name for obj in bpy.context.scene.objects if obj.get('axis')=='LOCAL Z' and 'DATUM' not in obj.name)
    controls = [obj for obj in bpy.context.scene.objects if obj.name.startswith('CONTROL')]
    stale_j6 = any('J6' in obj for obj in controls) or any(name.startswith('J6 ') for name in axes)
    return {'pass': len(rows)==6 and counts=={'AX-12A':4,'XM430-W350-T':2} and len(axes)==5 and not stale_j6,
            'expected_total_motors': 6, 'actual_total_motors': len(rows), 'counts': counts,
            'expected_arm_DOF': 5, 'actual_arm_joint_objects': axes,
            'powered_gripper_separate_from_arm_DOF': True, 'stale_J6_control_or_joint': stale_j6,
            'motors': rows,
            'scope': 'Counts actual manufacturer case-reference objects by model, not a title or declared BOM total.'}


def say(message):
    print(message, flush=True)


def descendants_of(obj, ancestor):
    current = obj
    while current is not None:
        if current == ancestor:
            return True
        current = current.parent
    return False


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        vertices = np.array([v.co[:] for v in mesh.vertices], dtype=np.float64)
        triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
    finally:
        evaluated.to_mesh_clear()
    if not len(vertices) or not len(triangles):
        raise ValueError(f'{obj.name}: empty evaluated mesh')
    if not np.isfinite(vertices).all():
        raise ValueError(f'{obj.name}: nonfinite coordinates')
    local_reference = (vertices.min(axis=0) + vertices.max(axis=0)) * .5
    local = vertices[triangles] - local_reference
    volumes = np.einsum('ij,ij->i', local[:, 0],
                       np.cross(local[:, 1], local[:, 2])) / 6.0
    volume = float(volumes.sum())
    centroid = (np.einsum('i,ij->j', volumes, local.sum(axis=1)) / (4 * volume)
                + local_reference) if abs(volume) > 1e-8 else vertices.mean(axis=0)
    return {'vertices': vertices, 'triangles': triangles,
            'signed_volume_local_mm3': volume, 'centroid_local': Vector(centroid)}


def critical_fastener(obj):
    prefixes = ('A01 front root','A01 rear root','A03 front root','A03 rear root',
                'Elbow bilateral ear','Elbow cheek tie','Forearm crossmember','S M4x','E M4x')
    return obj.name.startswith(prefixes) and (bool(obj.get('fastener_kind')) or 'socket head' in obj.name)


def find_controls(keys=('J1', 'J2', 'J3', 'J4', 'J5')):
    controllers = [obj for obj in bpy.data.objects if obj.name.startswith('CONTROL')
                   and all(key in obj for key in keys)]
    if len(controllers) != 1:
        raise RuntimeError(f'Expected one CONTROL with J1-J5 properties, found {len(controllers)}')
    joints = {}
    for key in keys:
        candidates = [obj for obj in bpy.data.objects if obj.name.startswith(key + ' ')
                      and obj.get('axis') == 'LOCAL Z' and 'DATUM' not in obj.name]
        if len(candidates) != 1:
            raise RuntimeError(f'Cannot uniquely identify {key} actual output axis: {len(candidates)}')
        joints[key] = candidates[0]
    return controllers[0], joints


def set_pose(controller, pose):
    for key, value in pose.items():
        controller[key] = float(value)
    controller.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
    bpy.context.evaluated_depsgraph_get().update()


def world_matrix(obj):
    return obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()


def make_poses(controller, joints):
    home = {key: float(joints[key].get('home_deg', controller[key])) for key in joints}
    if 'GRIP' in controller:
        home['GRIP'] = float(controller['GRIP'])
    limits = {key: [float(x) for x in joints[key].get('limits_deg', [-180, 180])]
              for key in joints}
    if 'GRIP' in controller:
        ui = controller.id_properties_ui('GRIP').as_dict()
        limits['GRIP'] = [float(ui.get('min', 20)), float(ui.get('max', 70))]
    horizontal = {**home, **{key: 0. for key in joints}}
    poses = [('home', home), ('horizontal_stress_case', horizontal)]
    for key in limits:
        for end, value in zip(('min', 'max'), limits[key]):
            poses.append((key + '_' + end, {**home, key: value}))
    for name, lo_hi in [('combined_low', 0), ('combined_high', 1)]:
        poses.append((name, {**home, **{key: bounds[lo_hi] for key, bounds in limits.items()}}))
    # Rectangular palm corners can approach the pitch motor most closely near
    # intermediate tool roll, even when its roll endpoints are clear.
    for pitch in limits['J4']:
        for roll in (-30., 30.):
            poses.append((f'palm_corner_pitch_{pitch:g}_roll_{roll:g}',
                          {**home, 'J4': pitch, 'J5': roll, 'GRIP': 70.}))
    return poses, limits


def outside_limits(pose, limits):
    return {key: value for key, value in pose.items()
            if key in limits and not (limits[key][0] - 1e-8 <= value <= limits[key][1] + 1e-8)}


def audit_marker(role, exact_name):
    candidates = [obj for obj in bpy.context.scene.objects if obj.get('audit_role') == role]
    if not candidates:
        candidates = [obj for obj in bpy.context.scene.objects if obj.name == exact_name]
    if len(candidates) != 1:
        raise RuntimeError(f'Expected exactly one {role} marker ({exact_name}), found {len(candidates)}')
    return candidates[0]


def fingertip_midpoint(cache):
    # R06 records true flat-pad contact markers; do not substitute mesh extrema
    # or the old pivoting-jaw names when assessing a parallel rack gripper.
    tips = []
    for side in ('left', 'right'):
        obj = audit_marker('grip_contact_' + side, 'GRIP ' + side + ' contact')
        point = world_matrix(obj).translation
        tips.append({'object': obj.name, 'point_world_mm': list(point)})
    midpoint = sum((Vector(tip['point_world_mm']) for tip in tips), Vector()) / len(tips)
    return midpoint, tips


def payload_tip_point():
    # The gap markers lie on real flat pad lands near the fingers' roots.
    # Use the separate distal tip marker for the load case, otherwise R06's
    # longer fingers would incorrectly disappear from the payload lever arm.
    marker = audit_marker('tool_centreline', 'GRIP tool centreline tip')
    return world_matrix(marker).translation


def neutral_centreline_check(controller, joints, cache, home):
    """R06: transverse J4 pitch, followed by inline J5 tool roll and jaws."""
    neutral = {**home, 'J4': 0., 'J5': 0., 'GRIP': 45.}
    if 'J1' in joints:
        neutral['J1'] = 0.
    set_pose(controller, neutral)
    pitch_matrix = world_matrix(joints['J4'])
    roll_matrix = world_matrix(joints['J5'])
    origin = pitch_matrix.translation
    pitch_axis = (pitch_matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
    axis = (roll_matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
    tool = audit_marker('tool_centreline', 'GRIP tool centreline tip')
    tool_matrix = world_matrix(tool)
    tool_axis = (tool_matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
    midpoint, tips = fingertip_midpoint(cache)
    mount = audit_marker('wrist_fixed_mount', 'WRIST fixed flange datum')
    mount_matrix = world_matrix(mount)
    mount_axis = (mount_matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
    points = {'J5_tool_roll_origin': roll_matrix.translation,
              'fixed_tool_tip_marker': tool_matrix.translation,
              'mean_grip_contact': midpoint,
              'fixed_forearm_wrist_mount': mount_matrix.translation}
    distances = {name: float((point-origin).cross(axis).length) for name,point in points.items()}
    stations = {name: float((point-origin).dot(axis)) for name,point in points.items()}
    axes = {'J5_roll_dot_tool': float(axis.dot(tool_axis)),
            'J5_roll_dot_J4_pitch': float(axis.dot(pitch_axis)),
            'J5_roll_dot_fixed_forearm_mount': float(axis.dot(mount_axis))}
    passed = (max(distances.values()) <= .05 and axes['J5_roll_dot_tool'] >= 1-1e-5
              and abs(axes['J5_roll_dot_J4_pitch']) <= 1e-5
              and axes['J5_roll_dot_fixed_forearm_mount'] >= 1-1e-5
              and stations['fixed_forearm_wrist_mount'] < 0
              and stations['J5_tool_roll_origin'] > 0
              and stations['fixed_tool_tip_marker'] > stations['J5_tool_roll_origin'])
    result = {'pass': passed, 'neutral_controls': neutral,
              'J4_pitch_origin_world_mm': list(origin), 'tool_axis_unit_world': list(axis),
              'distance_from_neutral_tool_axis_mm': distances,
              'axial_stations_from_J4_pitch_mm': stations, 'axis_dot_products': axes,
              'neutral_fixed_mount_to_distal_tool_tip_mm': stations['fixed_tool_tip_marker'] - stations['fixed_forearm_wrist_mount'],
              'position_tolerance_mm': .05,
              'scope': 'Checks fixed forearm mount, neutral J4 pitch centre, J5 tool roll and gripper centreline; five arm joints, no forearm-roll actuator.'}
    if all(key in joints for key in ('J1','J2','J3')):
        yaw = world_matrix(joints['J1'])
        normal = (yaw.to_3x3() @ Vector((0,1,0))).normalized()
        plane_origin = yaw.translation
        full_points = {key + '_axis_centre': world_matrix(joints[key]).translation for key in ('J2','J3','J4','J5')}
        full_points.update({'wrist_fixed_mount': mount_matrix.translation,
                            'tool_tip': tool_matrix.translation, 'grip_midpoint': midpoint})
        offsets = {key: float((point-plane_origin).dot(normal)) for key,point in full_points.items()}
        full_pass = max(abs(value) for value in offsets.values()) <= .05
        result['full_arm_top_view_alignment'] = {'pass': full_pass,
            'plane_origin_world_mm': list(plane_origin), 'plane_normal_world': list(normal),
            'signed_lateral_offsets_mm': offsets, 'tolerance_mm': .05,
            'scope': 'J1/J4/J5 zero; shoulder/elbow retain home bends. Actual joint centres, wrist mount, tool tip and jaw midpoint must share the yaw-centred fore-aft plane.'}
        result['pass'] = result['pass'] and full_pass
    set_pose(controller, home)
    return result


def bilateral_link_check(joints, cache):
    stages = []
    for stage,key in (('upper_arm','J2'),('forearm','J3')):
        objects = [obj for obj in cache if obj.get('part_id') and obj.get('bilateral_stage')==stage]
        rows = []
        inverse = np.array(world_matrix(joints[key]).inverted(), dtype=np.float64)
        for obj in objects:
            matrix = inverse @ np.array(world_matrix(obj), dtype=np.float64)
            vertices = cache[obj]['vertices'] @ matrix[:3,:3].T + matrix[:3,3]
            low,high = float(vertices[:,2].min()),float(vertices[:,2].max())
            side = int(obj.get('bilateral_side',0))
            centroid = matrix[:3,:3] @ np.array(cache[obj]['centroid_local']) + matrix[:3,3]
            rows.append({'object': obj.name, 'side': side, 'claimed_driven_joint': obj.get('driven_joint'),
                         'actual_rigid_group': canonical_rigid_group(obj),
                         'actual_descendant_of_output_joint': descendants_of(obj,joints[key]),
                         'local_Z_bounds_mm': [low,high], 'local_Z_bounds_midplane_mm': (low+high)/2,
                         'signed_volume_mm3': cache[obj]['signed_volume_local_mm3'],
                         'mass_centroid_in_joint_frame_mm': centroid.tolist(),
                         'on_declared_side': (side==-1 and high<=.05) or (side==1 and low>=-.05)})
        both_sides = len(rows)==2 and sorted(row['side'] for row in rows)==[-1,1]
        shared_drive = all(row['actual_descendant_of_output_joint'] and
                           row['actual_rigid_group']==joints[key].name and row['claimed_driven_joint']==key for row in rows)
        symmetry = abs(sum(row['local_Z_bounds_midplane_mm'] for row in rows)) if both_sides else None
        passed = both_sides and shared_drive and all(row['on_declared_side'] and row['signed_volume_mm3']>0 for row in rows)
        stages.append({'stage':stage,'joint':key,'pass':passed,'parts':rows,
                       'opposing_bounds_midplane_sum_mm':symmetry,
                       'opposing_bounds_midplanes_symmetric_within_0p05mm':symmetry is not None and symmetry<=.05})
    return {'pass': all(row['pass'] for row in stages), 'stages': stages,
            'scope':'Checks two actual printed meshes on opposite sides of each output centre plane and their common driven hierarchy. Reports geometric symmetry separately. Does not establish fastener engagement, stiffness or equal load sharing.'}


def read_gear_specs(blend_path):
    path = blend_path.parent / 'gear-pairs.json'
    specs = json.loads(path.read_text(encoding='utf-8'))
    by_name = {item['name']: item for item in specs}
    for key in ('J2', 'J3', 'J4'):
        teeth = by_name[key]['teeth']
        if len(teeth) != 2 or not all(float(value) > 0 for value in teeth):
            raise ValueError(f'{key}: invalid tooth counts in {path}')
        MOTOR_SCREEN[key]['ratio'] = float(teeth[1]) / float(teeth[0])
    return by_name, {
        'path': str(path.resolve()),
        'modified_utc': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        'specifications': specs,
        'note': 'Mass torque reductions read from this sidecar; evaluated driver checks below verify its ratio against the opened blend.',
    }


def audit_controls(controller, joints, cache, home, limits, gear_specs):
    """Sample three numerical values for each control, including actual output."""
    palm = audit_marker('gripper_fixed_datum', 'GRIPPER')
    rows = []
    for key, bounds in limits.items():
        samples = []
        for value in (bounds[0], (bounds[0] + bounds[1]) * .5, bounds[1]):
            set_pose(controller, {**home, key: value})
            midpoint, tips = fingertip_midpoint(cache)
            matrix = world_matrix(palm)
            sample = {
                'requested_value': value, 'requested_units': 'mm' if key == 'GRIP' else 'deg',
                'grip_contact_midpoint_world_mm': list(midpoint),
                'fingertip_gap_mm': float((Vector(tips[0]['point_world_mm']) - Vector(tips[1]['point_world_mm'])).length),
                'tool_origin_world_mm': list(matrix.translation),
                'tool_orientation_quaternion': list(matrix.to_quaternion()),
            }
            if key in joints:
                actual = math.degrees(joints[key].evaluated_get(bpy.context.evaluated_depsgraph_get()).rotation_euler.z)
                sample['actual_output_degrees'] = actual
                sample['output_angle_error_degrees'] = actual - value
            if key in ('J1', 'J2', 'J3', 'J4'):
                spec = gear_specs[key]
                motor_node = bpy.data.objects.get(spec['pinion'])
                if motor_node is None:
                    raise RuntimeError(f'{key}: pinion object from sidecar is missing')
                ratio = float(spec['teeth'][1]) / float(spec['teeth'][0])
                phase = math.degrees(float(spec['pinion_phase_rad']))
                measured = math.degrees(motor_node.evaluated_get(bpy.context.evaluated_depsgraph_get()).rotation_euler.z)
                expected = phase - ratio * value
                sample.update({'gear_ratio_from_teeth': ratio, 'actual_pinion_degrees': measured,
                               'expected_pinion_degrees': expected, 'pinion_angle_error_degrees': measured - expected})
            if key == 'GRIP':
                pinion = audit_marker('grip_pinion', 'GRIP pinion rotation')
                graph = bpy.context.evaluated_depsgraph_get()
                actual_radians = float(pinion.evaluated_get(graph).rotation_euler.z)
                expected_radians = (value - 45.) / 30.
                sample.update({'actual_grip_pinion_degrees': math.degrees(actual_radians),
                               'expected_grip_pinion_degrees': math.degrees(expected_radians),
                               'pinion_angle_error_degrees': math.degrees(actual_radians - expected_radians),
                               'gripper_clear_gap_error_mm': sample['fingertip_gap_mm'] - value})
            samples.append(sample)
        start, finish = samples[0], samples[-1]
        positional_change = float((Vector(start['grip_contact_midpoint_world_mm']) - Vector(finish['grip_contact_midpoint_world_mm'])).length)
        from mathutils import Quaternion
        q_start = Quaternion(start['tool_orientation_quaternion'])
        q_finish = Quaternion(finish['tool_orientation_quaternion'])
        angular_change = math.degrees(q_start.rotation_difference(q_finish).angle)
        gap_change = abs(start['fingertip_gap_mm'] - finish['fingertip_gap_mm'])
        follows_requested_angles = all(abs(sample.get('output_angle_error_degrees', 0)) < .001 and
                                      abs(sample.get('pinion_angle_error_degrees', 0)) < .001 and
                                      abs(sample.get('gripper_clear_gap_error_mm', 0)) < .01 for sample in samples)
        if key == 'GRIP':
            follows_requested_angles = follows_requested_angles and positional_change < .01
        affects_tool = gap_change > .01 if key == 'GRIP' else (positional_change > .01 or angular_change > .001)
        ax_span = None
        if key in ('J1', 'J4', 'J5', 'GRIP'):
            field = ('actual_grip_pinion_degrees' if key == 'GRIP' else
                     'actual_pinion_degrees' if key in ('J1', 'J4') else 'actual_output_degrees')
            span = max(s[field] for s in samples) - min(s[field] for s in samples)
            ax_span = {'required_motor_span_deg': span, 'joint_mode_nominal_available_deg': 300.,
                       'remaining_nominal_travel_deg': 300. - span,
                       'span_feasible_in_AX_position_mode': span <= 300. + .001,
                       'source': 'https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/#goal-position-30',
                       'note': 'Only checks required travel span. Actual installed horn indexing, calibrated encoder offsets and end margins must also be set. AX wheel mode is not absolute position control.'}
        rows.append({'control': key, 'samples': samples,
                     'grip_contact_midpoint_change_mm': positional_change,
                     'tool_orientation_change_degrees': angular_change,
                     'fingertip_gap_change_mm': gap_change,
                     'evaluated_angles_follow_requested_control_and_gear_ratio': follows_requested_angles,
                     'affects_end_effector_pose_or_grip': affects_tool,
                     'AX_position_mode_travel_check': ax_span,
                     'pass': follows_requested_angles and affects_tool and (ax_span is None or ax_span['span_feasible_in_AX_position_mode'])})
    set_pose(controller, home)
    return {'all_passed': all(row['pass'] for row in rows), 'control_count': len(rows),
            'samples_per_control': 3, 'tests': rows,
            'scope': 'Checks evaluated numerical motion and gear-driver ratios; does not establish contact mechanics, free movement or motor capability.'}


def mass_inventory(cache, joints):
    inventory = []
    for obj, data in cache.items():
        is_printed = bool(obj.get('part_id'))
        if obj.name.startswith(('F0', 'B03_')):
            continue
        if not is_printed and float(obj.get('mass_g', 0)) <= 0:
            continue
        scale = abs(world_matrix(obj).to_3x3().determinant())
        volume = data['signed_volume_local_mm3'] * scale
        mass = abs(volume) * PLA_DENSITY_G_MM3 if is_printed else float(obj['mass_g'])
        inventory.append({
            'object': obj.name, 'obj': obj, 'mass_g': mass,
            'source': 'solid_mesh_PLA_1.24g_per_cm3' if is_printed else 'motor_or_electronics_reference_mass',
            'printed': is_printed, 'signed_solid_volume_mm3': volume if is_printed else None,
            'positive_mesh_volume': volume > 0,
            'centroid_local_mm': list(data['centroid_local']),
            'descendant_of': [key for key, joint in joints.items() if descendants_of(obj, joint)],
            'rigid_group': str(obj.get('rigid_group', 'UNSTAMPED')),
        })
    return inventory


def load_case(inventory, joints, payload_g, payload_point):
    rows = {}
    for key, screening in MOTOR_SCREEN.items():
        if key not in joints:
            continue
        axis_matrix = world_matrix(joints[key])
        origin = axis_matrix.translation
        axis = (axis_matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
        torque_vector = Vector()
        unallowed_torque_vector = Vector()
        mass_first_moment_kg_m = Vector()
        mass_g = 0.
        for item in inventory:
            if key not in item['descendant_of']:
                continue
            centre = world_matrix(item['obj']) @ Vector(item['centroid_local_mm'])
            force = Vector((0, 0, -GRAVITY_M_S2 * item['mass_g'] / 1000.))
            moment = ((centre - origin) / 1000.).cross(force)
            unallowed_torque_vector += moment
            torque_vector += moment * ALLOWANCE
            mass_first_moment_kg_m += (centre-origin) * (item['mass_g'] * ALLOWANCE / 1e6)
            mass_g += item['mass_g']
        payload_moment = ((payload_point - origin) / 1000.).cross(
            Vector((0, 0, -GRAVITY_M_S2 * payload_g / 1000.)))
        torque_vector += payload_moment
        mass_first_moment_kg_m += (payload_point-origin) * (payload_g / 1e6)
        worst_orientation_axis = GRAVITY_M_S2 * axis.cross(mass_first_moment_kg_m).length
        actual_axis_torque = float(torque_vector.dot(axis))
        gravity_motor = abs(actual_axis_torque) / (screening['ratio'] * screening['efficiency'])
        dynamic_screen = gravity_motor * 1.5
        rows[key] = {
            **screening, 'axis_origin_world_mm': list(origin), 'axis_unit_world': list(axis),
            'descendant_mass_g_before_allowance': mass_g,
            'descendant_mass_g_with_10percent_allowance': mass_g * ALLOWANCE,
            'gravity_axis_torque_without_allowance_or_payload_nm': float(unallowed_torque_vector.dot(axis)),
            'payload_axis_torque_nm': float(payload_moment.dot(axis)),
            'gravity_axis_torque_with_allowance_and_payload_nm': actual_axis_torque,
            'total_gravity_bending_vector_nm': list(torque_vector),
            'total_gravity_bending_vector_magnitude_nm': float(torque_vector.length),
            'moving_mass_first_moment_world_kg_m': list(mass_first_moment_kg_m),
            'gravity_axis_torque_bound_over_all_base_orientations_nm': float(worst_orientation_axis),
            'motor_gravity_torque_bound_over_all_base_orientations_nm': float(worst_orientation_axis / (screening['ratio'] * screening['efficiency'])),
            'orientation_bound_note': 'Worst gravity direction for this relative pose; may not be reachable in the declared full-arm limits. An upper bound, not the actual world-pose torque.',
            'estimated_motor_gravity_torque_nm': gravity_motor,
            'motor_gravity_to_comparison_ratio': gravity_motor / screening['comparison_nm'],
            'gravity_exceeds_estimated_motor_comparison': gravity_motor > screening['comparison_nm'],
            'motor_torque_with_arbitrary_1p5_allowance_nm': dynamic_screen,
            'one_point_five_case_exceeds_comparison': dynamic_screen > screening['comparison_nm'],
        }
    return {'payload_g': payload_g, 'payload_point_world_mm': list(payload_point), 'joints': rows}


def collision_objects(cache):
    return [(obj, data) for obj, data in cache.items()
            if not obj.name.startswith(('F0', 'B03_')) and
            (bool(obj.get('part_id')) or bool(obj.get('collision_check', False)) or critical_fastener(obj))]


def support_foot_polygon():
    feet = [obj for obj in bpy.context.scene.objects if obj.name.startswith('B15_printed_foot_')
            or obj.get('audit_role') == 'support_foot']
    points = sorted(set((round(world_matrix(obj).translation.x, 6),
                         round(world_matrix(obj).translation.y, 6)) for obj in feet))
    if len(points) < 3:
        raise RuntimeError('At least three actual support-foot centres are required for stability screening')
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for point in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],point)<=0:
            lower.pop()
        lower.append(point)
    for point in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],point)<=0:
            upper.pop()
        upper.append(point)
    polygon = lower[:-1]+upper[:-1]
    if len(polygon) < 3:
        raise RuntimeError('Support-foot centres are collinear')
    return polygon, [{'object': obj.name, 'origin_world_mm': list(world_matrix(obj).translation)} for obj in feet]


def static_stability(inventory, payload_point, payload_g=25.0):
    total_mass = payload_g
    moment = payload_point * payload_g
    for item in inventory:
        factor = ALLOWANCE if item['descendant_of'] else 1.0
        mass = item['mass_g'] * factor
        centre = world_matrix(item['obj']) @ Vector(item['centroid_local_mm'])
        total_mass += mass
        moment += centre * mass
    centre = moment / total_mass
    polygon, feet = support_foot_polygon()
    edges = []
    for i,first in enumerate(polygon):
        second = polygon[(i+1)%len(polygon)]
        dx,dy = second[0]-first[0], second[1]-first[1]
        margin = (dx*(centre.y-first[1])-dy*(centre.x-first[0]))/math.hypot(dx,dy)
        edges.append({'from_xy_mm': first, 'to_xy_mm': second, 'signed_inside_margin_mm': float(margin)})
    margin = min(row['signed_inside_margin_mm'] for row in edges)
    return {
        'payload_g': payload_g, 'total_modelled_mass_g': total_mass,
        'combined_COM_world_mm': list(centre),
        'support_polygon_foot_centres_world_xy_mm': polygon,
        'actual_support_foot_objects': feet,
        'signed_distances_to_support_edges_mm': edges,
        'minimum_signed_margin_mm': margin, 'static_projection_inside_support_polygon': margin >= 0,
        'smallest_gravity_restoring_moment_about_support_edge_nm': total_mass / 1000 * GRAVITY_M_S2 * margin / 1000,
        'bench_anchorage_assumed': False,
        'note': 'Static level-table model only. Polygon is the convex hull of actual foot centres, excluding their extra contact radius. Solid PLA mass and moving 10% allowance; no acceleration, cable pull, friction/sliding, compliance or reduced-infill mass model. Removed service panel and fit coupons excluded. Reserved unselected electronics have no assigned mass.',
    }


def canonical_rigid_group(obj):
    """Nearest actuated transform owns a body; includes translating R06 jaws."""
    current = obj
    while current is not None:
        animation = current.animation_data
        if animation and any(curve.data_path in ('location', 'rotation_euler', 'rotation_quaternion', 'scale')
                             for curve in animation.drivers):
            return current.name
        current = current.parent
    return 'FIXED'


def prepare_world_collision(obj, data):
    matrix = np.array(world_matrix(obj), dtype=np.float64)
    vertices = data['vertices'] @ matrix[:3, :3].T + matrix[:3, 3]
    triangles = data['triangles']
    tree = BVHTree.FromPolygons([tuple(v) for v in vertices], [tuple(t) for t in triangles],
                               all_triangles=True, epsilon=0.0)
    triangle_vertices = vertices[triangles]
    normals = np.cross(triangle_vertices[:, 1] - triangle_vertices[:, 0],
                       triangle_vertices[:, 2] - triangle_vertices[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    normals = normals / np.maximum(lengths[:, None], 1e-15)
    return {'object': obj, 'vertices': vertices, 'triangles': triangles, 'normals': normals,
            'tree': tree, 'lower': vertices.min(axis=0), 'upper': vertices.max(axis=0),
            'world_to_local': np.linalg.inv(matrix),
            'local_lower': data['vertices'].min(axis=0), 'local_upper': data['vertices'].max(axis=0),
            'group': canonical_rigid_group(obj)}


RAY_DIRECTIONS = [Vector(value).normalized() for value in
                  ((1., .37139067, .17320508), (-.219381, 1., .419771), (.349273, -.167281, 1.))]


def is_inside(tree, point):
    """Majority parity of three rays; 0.005 mm advances avoid float32 re-hits."""
    votes = 0
    any_limited = False
    for direction in RAY_DIRECTIONS:
        origin = Vector(point)
        hits = 0
        limited = True
        for _ in range(160):
            hit, normal, index, distance = tree.ray_cast(origin, direction)
            if hit is None:
                limited = False
                votes += int(bool(hits % 2))
                break
            hits += 1
            origin = hit + direction * .005
        any_limited |= limited
    return votes >= 2, any_limited


def test_ray_parity():
    vertices = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
    triangles = [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                 (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=0.0)
    for point in ((.5,.5,.5),(.1,.2,.3),(.95,.99,.01)):
        assert is_inside(tree, point) == (True, False), ('cube inside', point)
    for point in ((-1,.5,.5),(2,.5,.5),(.5,.5,2),(.5,.5,-2)):
        assert is_inside(tree, point) == (False, False), ('cube outside', point)
    # Closed annular prism: the central bore is empty despite lying inside AABB.
    n = 40
    verts = [(radius*math.cos(2*math.pi*i/n), radius*math.sin(2*math.pi*i/n), z)
             for z in (0., 2.) for radius in (2., 1.) for i in range(n)]
    quads = []
    for i in range(n):
        k = (i+1) % n
        quads += [(i,k,2*n+k,2*n+i),(n+k,n+i,3*n+i,3*n+k),
                  (i,n+i,n+k,k),(2*n+k,3*n+k,3*n+i,2*n+i)]
    ring = BVHTree.FromPolygons(verts, quads, all_triangles=False, epsilon=0.0)
    assert is_inside(ring, (0.,0.,1.)) == (False, False), 'ring bore must be empty'
    assert is_inside(ring, (1.5,0.,1.)) == (True, False), 'ring wall must be solid'
    from mathutils import Matrix
    for degrees in (-85, -40, 40, 85):
        transform = Matrix.Translation((120., -80., 310.)) @ Matrix.Rotation(math.radians(degrees),4,'Z') @ Matrix.Rotation(.632,4,'X')
        moved = BVHTree.FromPolygons([transform @ Vector(vertex) for vertex in verts], quads,
                                     all_triangles=False, epsilon=0.0)
        for point, expected in (((0.,0.,1.), False), ((1.5,0.,1.), True), ((3.,0.,1.), False)):
            assert is_inside(moved, transform @ Vector(point)) == (expected, False), ('rotated ring',degrees,point)
        # Regression: thin solids with genuine 0.25 mm face separation can
        # share a world AABB after rotation. They must fail local containment.
        matrix = np.array(transform, dtype=np.float64)
        thin = {'world_to_local': np.linalg.inv(matrix),
                'local_lower': np.array([-3., -3., 0.]),
                'local_upper': np.array([3., 3., .1])}
        local_points = np.array([[0., 0., .05], [0., 0., .35], [0., 0., -.25]])
        world_points = local_points @ matrix[:3,:3].T + matrix[:3,3]
        assert local_bounds_mask(world_points, thin).tolist() == [True, False, False], ('thin rotated gap', degrees)
    say('PASS: cube, hollow sleeve, rotated sleeve, and rotated thin-solid 0.25 mm gap regression tests')


def local_bounds_mask(world_points, solid):
    inverse = solid['world_to_local']
    local_points = world_points @ inverse[:3, :3].T + inverse[:3, 3]
    return ((local_points >= solid['local_lower'] - .005) &
            (local_points <= solid['local_upper'] + .005)).all(axis=1)


def measured_XM_gear_cradle_gaps(cache):
    """Independent separating-plane evidence from the actual saved meshes."""
    rows = []
    for prefix in ('S', 'E'):
        wheels = [obj for obj in cache if re.fullmatch(prefix + r'_05_output_\d+T', obj.name)]
        cradles = [obj for obj in cache if obj.name == prefix + '_XM_C01_Keyed_motor_cradle']
        if len(wheels) != 1 or len(cradles) != 1:
            continue
        wheel, cradle = wheels[0], cradles[0]
        relative = np.linalg.inv(np.array(world_matrix(cradle), dtype=np.float64)) @ np.array(world_matrix(wheel), dtype=np.float64)
        in_cradle = cache[wheel]['vertices'] @ relative[:3,:3].T + relative[:3,3]
        cradle_max_z = float(cache[cradle]['vertices'][:,2].max())
        wheel_min_z = float(in_cradle[:,2].min())
        gap = wheel_min_z - cradle_max_z
        rows.append({'wheel': wheel.name, 'cradle': cradle.name,
                     'cradle_maximum_local_Z_mm': cradle_max_z,
                     'wheel_minimum_in_cradle_local_Z_mm': wheel_min_z,
                     'separating_plane_gap_mm': gap,
                     'all_wheel_vertices_in_front_of_cradle': gap > .02,
                     'note': 'Positive gap between entire mesh coordinate bounds proves separation along the motor-local Z direction in this pose; not a general minimum-distance or deflection rating.'})
    return rows


def sampled_penetration(first, second, sample_limit=64):
    vertices = first['vertices']
    eligible = vertices[((vertices >= second['lower'] - .005) &
                         (vertices <= second['upper'] + .005)).all(axis=1)]
    # World AABBs become loose after a rotation. A point outside the actual
    # local bounds cannot be inside the solid, regardless of noisy ray parity
    # near thin/copanar faces. This also preserves the real 0.25 mm face gaps.
    eligible = eligible[local_bounds_mask(eligible, second)]
    if not len(eligible):
        return {'maximum_sampled_depth_mm': 0., 'inside_samples': 0, 'samples_tested': 0,
                'ray_iteration_limit_count': 0}
    if len(eligible) > sample_limit:
        eligible = eligible[np.linspace(0, len(eligible) - 1, sample_limit, dtype=int)]
    deepest = 0.
    deepest_sample = None
    inside_count = 0
    capped = 0
    for coordinates in eligible:
        point = Vector(coordinates)
        nearest, normal, index, distance = second['tree'].find_nearest(point)
        if nearest is None or distance <= .02:
            continue
        # Closed outward-oriented meshes must also agree with the nearest-face
        # signed distance. This rejects parity accidents on exterior points.
        if (point - nearest).dot(normal) >= -.01:
            continue
        inside, limited = is_inside(second['tree'], point)
        capped += int(limited)
        if inside:
            inside_count += 1
            if float(distance) > deepest:
                deepest = float(distance)
                deepest_sample = {
                    'vertex_world_mm': list(point),
                    'nearest_surface_world_mm': list(nearest),
                    'nearest_normal_world': list(normal),
                    'vertex_in_first_object_local_mm': list(world_matrix(first['object']).inverted() @ point),
                    'vertex_in_second_object_local_mm': list(world_matrix(second['object']).inverted() @ point),
                    'signed_nearest_normal_distance_mm': float((point-nearest).dot(normal)),
                }
    return {'maximum_sampled_depth_mm': deepest, 'inside_samples': inside_count,
            'samples_tested': len(eligible), 'ray_iteration_limit_count': capped,
            'deepest_sample': deepest_sample}


def minimum_axis_overlap(first, second):
    """A separating coordinate plane proves zero solid-volume intersection."""
    axes = [np.eye(3), first['world_to_local'][:3,:3], second['world_to_local'][:3,:3]]
    result = None
    for axis in np.vstack(axes):
        axis = axis / np.linalg.norm(axis)
        a = first['vertices'] @ axis
        b = second['vertices'] @ axis
        bounds_a, bounds_b = [float(a.min()), float(a.max())], [float(b.min()), float(b.max())]
        overlap = min(bounds_a[1], bounds_b[1]) - max(bounds_a[0], bounds_b[0])
        if result is None or overlap < result['interval_overlap_mm']:
            result = {'axis_unit_world': axis.tolist(), 'first_projection_interval_mm': bounds_a,
                      'second_projection_interval_mm': bounds_b, 'interval_overlap_mm': overlap,
                      'tolerance_mm': .001,
                      'note': 'If interval overlap is at most 0.001 mm, a separating/touching plane rules out finite-volume overlap beyond this numerical tolerance. A larger value supplies no contact exemption.'}
    return result


def test_projection_contact_proof():
    vertices = np.array([[x,y,z] for x in (0.,10.) for y in (0.,10.) for z in (0.,10.)])
    for angle in (0., .6):
        c, s = math.cos(angle), math.sin(angle)
        rotation = np.array([[c,-s,0],[s,c,0],[0,0,1]])
        inverse = np.eye(4)
        inverse[:3,:3] = rotation.T
        first = {'vertices': vertices @ rotation.T, 'world_to_local': inverse}
        for shift, expected in ((10.,0.), (9.8,.2), (10.2,-.2)):
            second = {'vertices': (vertices + [shift,0,0]) @ rotation.T, 'world_to_local': inverse}
            measured = minimum_axis_overlap(first, second)['interval_overlap_mm']
            assert abs(measured-expected)<1e-8, (angle,shift,measured)


def exact_intersection_volume(first, second):
    """Independent EXACT Boolean for ambiguous nested static mating surfaces.

    Temporary geometry uses the first solid's local frame to reduce float32
    world-coordinate noise. Nothing is saved to the source model.
    """
    created_objects, created_meshes = [], []
    evaluated = None
    try:
        inverse = first['world_to_local']
        for solid in (first, second):
            points = solid['vertices'] @ inverse[:3,:3].T + inverse[:3,3]
            mesh = bpy.data.meshes.new('AUDIT temporary intersection mesh')
            created_meshes.append(mesh)
            mesh.from_pydata(points.tolist(), [], solid['triangles'].tolist())
            mesh.update()
            obj = bpy.data.objects.new('AUDIT temporary intersection object', mesh)
            created_objects.append(obj)
            bpy.context.scene.collection.objects.link(obj)
        modifier = created_objects[0].modifiers.new('AUDIT exact overlap', 'BOOLEAN')
        modifier.operation = 'INTERSECT'
        modifier.solver = 'EXACT'
        modifier.object = created_objects[1]
        bpy.context.view_layer.update()
        evaluated = created_objects[0].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        points = np.array([v.co[:] for v in mesh.vertices], dtype=np.float64)
        triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
        volume = 0.
        if len(triangles):
            local = points[triangles] - points.mean(axis=0)
            volume = abs(float(np.einsum('ij,ij->i', local[:,0], np.cross(local[:,1],local[:,2])).sum()/6))
            volume /= abs(float(np.linalg.det(inverse[:3,:3])))
        return {'completed': True, 'intersection_volume_mm3': volume,
                'output_triangle_count': len(triangles), 'numerical_volume_tolerance_mm3': .01,
                'zero_volume_within_numerical_tolerance': volume <= .01,
                'method': 'Independent Blender EXACT INTERSECT of triangle meshes in the first solid local frame; signed tetrahedral enclosed volume. Temporary objects removed; source never saved. Numerical tolerance is not a print-fit allowance.'}
    except Exception as exc:
        return {'completed': False, 'error': repr(exc), 'zero_volume_within_numerical_tolerance': False}
    finally:
        if evaluated is not None:
            evaluated.to_mesh_clear()
        for obj in created_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        for mesh in created_meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)


def test_exact_intersection_volume():
    vertices = np.array([(0,0,0),(10,0,0),(10,10,0),(0,10,0),
                         (0,0,10),(10,0,10),(10,10,10),(0,10,10)], dtype=float)
    triangles = np.array([(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                          (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)])
    rows = []
    for angle in (0.,.6):
        c,s=math.cos(angle),math.sin(angle)
        matrix=np.eye(4)
        matrix[:3,:3]=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        matrix[:3,3]=[120.,-80.,310.]
        first = {'vertices': vertices @ matrix[:3,:3].T + matrix[:3,3],
                 'triangles': triangles, 'world_to_local': np.linalg.inv(matrix)}
        for shift, expected in ((10.,0.),(9.8,20.),(10.2,0.)):
            second = {**first, 'vertices': (vertices+[shift,0,0]) @ matrix[:3,:3].T + matrix[:3,3]}
            result = exact_intersection_volume(first,second)
            assert result['completed'] and abs(result['intersection_volume_mm3']-expected)<.001, (angle,shift,result)
            rows.append({'cube_rotation_rad':angle,'cube_shift_mm':shift,'expected_overlap_volume_mm3':expected,**result})
    # A nested solid can share all AABB intervals yet lie entirely in a bore.
    # Check the same geometry pattern as a printed journal inside its sleeve,
    # and deliberately enlarge it so the sleeve wall is truly penetrated.
    n=32
    ring_points=np.array([(radius*math.cos(2*math.pi*i/n),radius*math.sin(2*math.pi*i/n),z)
                          for z in (0.,2.) for radius in (2.,1.) for i in range(n)])
    ring_triangles=[]
    for i in range(n):
        k=(i+1)%n
        for a,b,c,d in ((i,k,2*n+k,2*n+i),(n+k,n+i,3*n+i,3*n+k),
                        (i,n+i,n+k,k),(2*n+k,3*n+k,3*n+i,2*n+i)):
            ring_triangles.extend(((a,b,c),(a,c,d)))
    sleeve={'vertices':ring_points,'triangles':np.array(ring_triangles),'world_to_local':np.eye(4)}
    for radius in (.8,1.2):
        points=np.array([(radius*math.cos(2*math.pi*i/n),radius*math.sin(2*math.pi*i/n),z)
                         for z in (.25,1.75) for i in range(n)])
        faces=[]
        for i in range(n):
            k=(i+1)%n
            faces.extend(((i,k,n+k),(i,n+k,n+i)))
        for i in range(1,n-1):
            faces.extend(((0,i+1,i),(n,n+i,n+i+1)))
        shaft={'vertices':points,'triangles':np.array(faces),'world_to_local':np.eye(4)}
        expected=max(0.,radius*radius-1)*n*math.sin(2*math.pi/n)/2*1.5
        result=exact_intersection_volume(sleeve,shaft)
        assert result['completed'] and abs(result['intersection_volume_mm3']-expected)<.001, (radius,result)
        rows.append({'nested_sleeve_bore_radius_mm':1.,'shaft_radius_mm':radius,
                     'expected_overlap_volume_mm3':expected,**result})
    return rows


def collision_screen(objects, case_printed_only=False, target_object=None, verify_zero_depth=False):
    if target_object is not None and not any(obj.name == target_object for obj, _ in objects):
        raise ValueError(f'Targeted assembly interface is missing: {target_object}')
    world = [prepare_world_collision(obj, data) for obj, data in objects]
    events = []
    broad_pairs = 0
    ignored_same_group = 0
    checked_same_group = 0
    for first, second in itertools.combinations(world, 2):
        if target_object is not None and target_object not in (first['object'].name, second['object'].name):
            continue
        if case_printed_only:
            a, b = first['object'], second['object']
            is_selected_pair = ((a.get('interface_role') == 'case' and bool(b.get('part_id'))) or
                                (b.get('interface_role') == 'case' and bool(a.get('part_id'))))
            if not is_selected_pair:
                continue
        if first['group'] == second['group'] and not case_printed_only and target_object is None:
            ignored_same_group += 1
            continue
        overlap = np.minimum(first['upper'], second['upper']) - np.maximum(first['lower'], second['lower'])
        if (overlap < -.002).any():
            continue
        broad_pairs += 1
        checked_same_group += int(first['group'] == second['group'])
        triangle_pairs = first['tree'].overlap(second['tree'])
        # BVH intersections alone miss a completely enclosed solid. Interior
        # probes are retained for all AABB candidates, including zero crossings.
        first_inside = sampled_penetration(first, second)
        second_inside = sampled_penetration(second, first)
        depth = max(first_inside['maximum_sampled_depth_mm'], second_inside['maximum_sampled_depth_mm'])
        if not triangle_pairs and depth <= .02:
            continue
        crossings = 0
        for ia, ib in triangle_pairs[:256]:
            cosine = abs(float(np.dot(first['normals'][ia], second['normals'][ib])))
            crossings += int(cosine < .98)
        plane_proof = minimum_axis_overlap(first, second) if depth <= .02 and triangle_pairs else None
        if depth > .25:
            category = 'gross_interpenetration_sampled'
        elif depth > .02:
            category = 'small_interpenetration_sampled'
        elif plane_proof and plane_proof['interval_overlap_mm'] <= .001:
            category = 'surface_contact_candidate'
        elif crossings:
            category = 'surface_crossing_requires_review'
        else:
            category = 'surface_contact_candidate'
        names = [first['object'].name, second['object'].name]
        same_motor_prefix = names[0].split(' | ')[0] == names[1].split(' | ')[0]
        known_motor_interface = (same_motor_prefix and depth <= .02 and
                                 any('dimensioned case' in name for name in names) and
                                 any('installed stock horn' in name for name in names))
        if known_motor_interface:
            category = 'matching_motor_case_horn_interface_candidate'
        volume_proof = None
        if verify_zero_depth and category == 'surface_crossing_requires_review':
            volume_proof = exact_intersection_volume(first, second)
            if volume_proof['zero_volume_within_numerical_tolerance']:
                category = 'surface_contact_candidate'
        events.append({
            'objects': names,
            'rigid_groups': [first['group'], second['group']], 'classification': category,
            'known_interface_note': 'Matching purchased motor case and installed stock horn, zero sampled interior depth; retained for review' if known_motor_interface else None,
            'triangle_intersection_pairs': len(triangle_pairs),
            'nonparallel_pairs_in_first_256': crossings,
            'aabb_overlap_extents_mm': overlap.tolist(), 'maximum_sampled_depth_mm': depth,
            'tightest_coordinate_projection_bound': plane_proof,
            'independent_exact_intersection_volume': volume_proof,
            'first_vertices_in_second': first_inside, 'second_vertices_in_first': second_inside,
        })
    counts = {category: sum(e['classification'] == category for e in events) for category in (
        'gross_interpenetration_sampled', 'small_interpenetration_sampled',
        'surface_crossing_requires_review', 'surface_contact_candidate',
        'matching_motor_case_horn_interface_candidate')}
    return {'object_count': len(objects), 'aabb_candidate_pairs': broad_pairs,
            'pairs_ignored_same_rigid_group': ignored_same_group, 'classification_counts': counts,
            'same_group_aabb_pairs_checked': checked_same_group,
            'pair_scope': (f'{target_object} versus every included structural mesh and motor reference, including same-body and fixed-to-fixed pairs.' if target_object is not None else
                           'Every purchased motor case versus every printed structural part, including same-body and fixed-to-fixed pairs; removed panel and fit coupons excluded. No named motor or cradle exclusion.' if case_printed_only else
                           'Different actuated rigid bodies; same-body and fixed-to-fixed pairs excluded.'),
            'events': events,
            'clear_of_reported_crossings_or_penetrations': not any(
                counts[key] for key in counts if key not in ('surface_contact_candidate', 'matching_motor_case_horn_interface_candidate'))}


def electronics_keepout_check(cache):
    envelopes = [obj for obj in bpy.context.scene.objects if obj.get('audit_role')=='electronics_keepout']
    hardware = [obj for obj in bpy.context.scene.objects if obj.type=='MESH' and
                (obj.get('fastener_kind') or 'socket head' in obj.name) and obj not in cache]
    graph = bpy.context.evaluated_depsgraph_get()
    physical = [*collision_objects(cache), *((obj,geometry(obj,graph)) for obj in hardware)]
    vertices = np.array([[x,y,z] for x in (-1.,1.) for y in (-1.,1.) for z in (-1.,1.)])
    triangles = np.array([(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),
                          (2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)],dtype=np.int32)
    data = {'vertices':vertices,'triangles':triangles,'signed_volume_local_mm3':8.,'centroid_local':Vector((0,0,0))}
    rows = []
    for obj in envelopes:
        result = collision_screen([*physical,(obj,data)],target_object=obj.name)
        measured = [2*world_matrix(obj).to_3x3().col[i].length for i in range(3)]
        declared = [float(value) for value in obj.get('service_envelope_mm',[])]
        dimensions_match = len(declared)==3 and max(abs(a-b) for a,b in zip(declared,measured))<=.01
        rows.append({'object':obj.name,'component_name':obj.get('component_name'),
                     'reserved_only':bool(obj.get('reserved_only',False)),
                     'declared_service_envelope_mm':declared,'evaluated_box_edge_lengths_mm':measured,
                     'dimensions_match_transform':dimensions_match,'collision_screen':result,
                     'pass': dimensions_match and bool(obj.get('reserved_only',False)) and result['clear_of_reported_crossings_or_penetrations']})
    return {'pass':len(rows)>=3 and all(row['pass'] for row in rows),
            'envelope_count':len(rows),'expected_minimum_envelopes':3,'envelopes':rows,
            'additional_fastener_reference_meshes_checked':len(hardware),
            'scope':'Checks declared controller, unselected power-module and USB withdrawal boxes against installed structural meshes and tagged fasteners/socket heads, including same-body pairs. Boxes are reservations, not purchased electronics or added mass; wire bend radii, selected board interfaces and electrical suitability are not validated.'}


def bilateral_assembly_interfaces(cache):
    targets = ('S_03_independent_output_shaft','E_03_independent_output_shaft',
               'E_01_rear_support','E_01_front_support','A05_centred_wrist_crossmember')
    rows = [{'object':name,'collision_screen':collision_screen(collision_objects(cache),target_object=name,verify_zero_depth=True)}
            for name in targets]
    return {'pass':all(row['collision_screen']['clear_of_reported_crossings_or_penetrations'] for row in rows),
            'interfaces':rows,
            'scope':'Targeted assembled-home checks of both keyed shafts, stationary elbow cheeks and centred wrist crossmember against all included solids, including same-body pairs. Relative same-body fits are invariant with motion; different-body motion is checked separately in the pose sweep. Checks geometry only, not fastening preload or structural capacity.'}


def wiring_kinematics_check():
    """Check the saved native bus graph and actual evaluated curve drivers."""
    text = bpy.data.texts.get('WIRING CONNECTIVITY — R06')
    if text is None:
        return {'pass': False, 'error': 'Missing native wiring connectivity document'}
    document = json.loads(text.as_string())
    order = ['J1_BASE','S_XM','E_XM','J4_AX','J5_AX','GRIP']
    expected = [('U2D2','POWER_INJECTION'),('POWER_INJECTION','J1_BASE'),*zip(order,order[1:])]
    actual = [(row.get('source_motor_id'),row.get('destination_motor_id')) for row in document.get('harnesses',[])]
    graph = bpy.context.evaluated_depsgraph_get()
    rows, errors = [], []
    for harness in document.get('harnesses',[]):
        for name in [harness.get('curve'),*harness.get('wires',[])]:
            obj = bpy.context.scene.objects.get(name or '')
            if obj is None or obj.type != 'CURVE':
                errors.append(f'Missing native route curve: {name}')
                continue
            anchors = json.loads(obj.get('curve_anchor_names_json','[]'))
            evaluated = obj.evaluated_get(graph)
            splines = evaluated.data.splines
            if len(splines)!=1 or len(splines[0].points)!=len(anchors) or not anchors:
                errors.append(f'Anchor/control-point count mismatch: {name}')
                continue
            distances = []
            for point,anchor_name in zip(splines[0].points,anchors):
                anchor = bpy.context.scene.objects.get(anchor_name)
                if anchor is None:
                    errors.append(f'Missing anchor {anchor_name} for {name}')
                    continue
                world_point = evaluated.matrix_world @ Vector(point.co[:3])
                distances.append(float((world_point-world_matrix(anchor).translation).length))
            maximum = max(distances,default=None)
            endpoint_mode = bool(splines[0].use_endpoint_u)
            row_pass = len(distances)==len(anchors) and maximum is not None and maximum<=.01 and endpoint_mode
            centre_endpoints = None
            if name==harness.get('curve'):
                centre_endpoints = [anchors[0],anchors[-1]]==[harness.get('source_endpoint'),harness.get('destination_endpoint')]
                row_pass &= centre_endpoints
            animation=obj.data.animation_data
            invalid_drivers=[curve.data_path for curve in animation.drivers if not curve.driver.is_valid] if animation else []
            row_pass &= not invalid_drivers
            rows.append({'curve':name,'harness_id':harness['id'],'conductor':obj.get('conductor'),
                         'anchor_count':len(anchors),'maximum_world_control_point_anchor_error_mm':maximum,
                         'first_last_anchor_error_mm':[distances[0],distances[-1]] if distances else [],
                         'spline_interpolates_endpoint_controls':endpoint_mode,
                         'centreline_matches_declared_endpoint_objects':centre_endpoints,
                         'invalid_driver_data_paths':invalid_drivers,'pass':row_pass})
    motor_ids = sorted(str(obj['motor_id']) for obj in bpy.context.scene.objects
                       if obj.get('interface_role')=='case' and obj.get('motor_type'))
    topology_pass = actual==expected and document.get('motor_order')==order and motor_ids==sorted(order)
    return {'pass':topology_pass and not errors and len(rows)==28 and all(row['pass'] for row in rows),
            'native_document':'WIRING CONNECTIVITY — R06','topology_matches_six_actual_motor_cases':topology_pass,
            'expected_physical_bus_edges':expected,'actual_physical_bus_edges':actual,
            'curve_count':len(rows),'expected_curve_count':28,'errors':errors,'curves':rows,
            'scope':'Verifies seven saved physical bus edges, six installed motor IDs, and evaluated control-point/anchor tracking for seven route centres plus 21 conductors. Does not establish cable clearance, bend radius, plug engagement, cut length, conductor suitability, power design or communication configuration.'}


def audit_wiring_only(args):
    """Fast independent refresh check after reference-only wire edits."""
    bpy.ops.wm.open_mainfile(filepath=str(args.blend))
    select_assembly_scene()
    scene=bpy.context.scene
    controller,joints=find_controls()
    if controller.animation_data is None or controller.animation_data.action is None:
        raise RuntimeError('Saved CONTROL animation missing')
    action=controller.animation_data.action.name
    poses,limits=make_poses(controller,joints)
    rows=[]
    for frame in [*range(1,361,12),360]:
        scene.frame_set(frame);bpy.context.view_layer.update()
        result=wiring_kinematics_check()
        rows.append({'frame':frame,'kind':'saved_animation','wiring_kinematics':result})
    controller.animation_data_clear()
    for name,pose in poses:
        if outside_limits(pose,limits):
            continue
        set_pose(controller,pose)
        rows.append({'pose':name,'kind':'operating_assembly','control_values':pose,
                     'wiring_kinematics':wiring_kinematics_check()})
    output={'audit':'R06_fresh_native_wire_graph_and_driver_response_v1',
            'created_utc':datetime.now(timezone.utc).isoformat(),'blend':str(args.blend.resolve()),
            'blend_modified_utc':datetime.fromtimestamp(args.blend.stat().st_mtime,timezone.utc).isoformat(),
            'saved_action_evaluated_before_in_memory_pose_overrides':action,
            'read_only_source_not_resaved':True,'sample_count':len(rows),
            'animation_snapshots':31,'operating_poses':len(rows)-31,'samples':rows,
            'all_passed':all(row['wiring_kinematics']['pass'] for row in rows),
            'scope':'Independent graph, actual motor IDs, complete evaluated control-point/anchor agreement and driver validity. No cable collision/bend or electrical inference.'}
    args.output.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return 0


def audit_wrist_debug(args):
    """Partial-build diagnostic; does not substitute for full assembly audit."""
    test_ray_parity()
    test_projection_contact_proof()
    test_exact_intersection_volume()
    bpy.ops.wm.open_mainfile(filepath=str(args.blend))
    controller, joints = find_controls(('J4', 'J5'))
    controller.animation_data_clear()
    home = {key: float(joint.get('home_deg', 0)) for key, joint in joints.items()}
    home['GRIP'] = 45.
    limits = {key: [float(x) for x in joint['limits_deg']] for key, joint in joints.items()}
    limits['GRIP'] = [20., 70.]
    poses = [('home', home)]
    for key, bounds in limits.items():
        for end, value in zip(('min', 'max'), bounds):
            poses.append((key + '_' + end, {**home, key: value}))
    for index, name in enumerate(('combined_low', 'combined_high')):
        poses.append((name, {key: bounds[index] for key, bounds in limits.items()}))
    # A rectangular palm reaches its greatest projected width inside a roll
    # interval, so endpoint tests alone miss the known palm/motor concern.
    for pitch in limits['J4']:
        for roll in (-30., 30.):
            poses.append((f'palm_corner_pitch_{pitch:g}_roll_{roll:g}',
                          {**home, 'J4': pitch, 'J5': roll, 'GRIP': 70.}))
    upstream_controls = {}
    ratio_sources = {}
    # A failed STL export still leaves useful complete assembly geometry. This
    # diagnostic can screen its upstream loads without pretending the complete
    # joint range or independent gear sidecar checks have run.
    for key, prefix in (('J2', 'S'), ('J3', 'E')):
        candidates = [obj for obj in bpy.context.scene.objects if obj.name.startswith(key + ' ')
                      and obj.get('axis') == 'LOCAL Z' and 'DATUM' not in obj.name]
        wheels = [(obj, re.fullmatch(prefix + r'_05_output_(\d+)T', obj.name))
                  for obj in bpy.context.scene.objects]
        wheels = [(obj, match) for obj, match in wheels if match]
        if len(candidates) == 1 and len(wheels) == 1:
            joints[key] = candidates[0]
            upstream_controls[key] = float(controller[key])
            MOTOR_SCREEN[key]['ratio'] = int(wheels[0][1].group(1)) / 20.
            ratio_sources[key] = {'ratio': MOTOR_SCREEN[key]['ratio'], 'source_part_name': wheels[0][0].name,
                                 'diagnostic_only': 'Part-name tooth count; final audit requires sidecar and evaluated driver verification'}
    set_pose(controller, home)
    graph = bpy.context.evaluated_depsgraph_get()
    cache = {obj: geometry(obj, graph) for obj in bpy.context.scene.objects if obj.type == 'MESH'
             and (obj.get('part_id') or obj.get('collision_check', False) or critical_fastener(obj) or float(obj.get('mass_g', 0)) > 0)}
    collidables = collision_objects(cache)
    inventory = mass_inventory(cache, joints)
    MOTOR_SCREEN['J4']['ratio'] = 3.
    output = {'diagnostic': 'Wrist sweep only; upstream held at saved pose when present. Full joint-range and sidecar verification not performed.',
              'fixed_upstream_controls_deg': upstream_controls, 'diagnostic_upstream_ratio_sources': ratio_sources,
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'blend_modified_utc': datetime.fromtimestamp(args.blend.stat().st_mtime, timezone.utc).isoformat(),
              'blend': str(args.blend),
              'mass_inventory': [{k: v for k, v in row.items() if k != 'obj'} for row in inventory],
              'neutral_centreline_alignment': neutral_centreline_check(controller, joints, cache, home),
              'poses': [], 'complete': False}
    if args.home_only:
        poses = poses[:1]
    for name, pose in poses:
        set_pose(controller, pose)
        result = collision_screen(collidables)
        output['poses'].append({'name': name, 'control_values': pose, 'collision_screen': result,
                                'motor_case_to_printed_screen': collision_screen(collidables, case_printed_only=True),
                                'load_cases': [load_case(inventory, joints, p, payload_tip_point()) for p in (0,25,50)]})
        args.output.write_text(json.dumps(output, indent=2, allow_nan=False), encoding='utf-8')
        say(name + ': ' + json.dumps(result['classification_counts']))
    output['complete'] = True
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False), encoding='utf-8')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blend', type=Path, default=ROOT / 'EDU06_R06.blend')
    parser.add_argument('--output', type=Path, default=ROOT / 'mass-load-audit.json')
    parser.add_argument('--home-only', action='store_true')
    parser.add_argument('--wrist-debug', action='store_true', help='Partial wrist-only diagnostic, not final verification')
    parser.add_argument('--wiring-only', action='store_true', help='Fresh native graph/driver checks across31animation and19operating samples; separate from cable clearance')
    parser.add_argument('--home-j3', type=float, default=None,
                        help='Diagnostic home-pose override; recorded in report, never saved to blend')
    parser.add_argument('--diagnostic-j2-limits', type=float, nargs=2, default=None,
                        help='Diagnostic in-memory shoulder range for proposed workspace screening')
    parser.add_argument('--repair-control-drivers', action='store_true',
                        help='Diagnostic in-memory repair of known old TRANSFORMS variable bug')
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    args = parser.parse_args(arguments)
    if not args.blend.exists():
        say(f'NOT READY: {args.blend} does not exist. No waiting or geometry claim made.')
        return 2
    if args.wrist_debug:
        return audit_wrist_debug(args)
    if args.wiring_only:
        if args.output==ROOT/'mass-load-audit.json':
            args.output=ROOT/'wiring-kinematics-audit.json'
        return audit_wiring_only(args)
    start = time.monotonic()
    test_ray_parity()
    test_projection_contact_proof()
    boolean_regression = test_exact_intersection_volume()
    say(f'Opening independently for read-only audit: {args.blend}')
    bpy.ops.wm.open_mainfile(filepath=str(args.blend))
    select_assembly_scene()
    controller, joints = find_controls()
    gear_specs, gear_reference = read_gear_specs(args.blend)
    diagnostic_changes = []
    if args.diagnostic_j2_limits is not None:
        original = [float(value) for value in joints['J2']['limits_deg']]
        if not args.diagnostic_j2_limits[0] < args.diagnostic_j2_limits[1]:
            raise ValueError('Diagnostic shoulder lower limit must be below upper limit')
        joints['J2']['limits_deg'] = args.diagnostic_j2_limits
        diagnostic_changes.append({'change': 'proposed_J2_limits_override', 'old': original,
                                   'new': args.diagnostic_j2_limits,
                                   'note': 'Diagnostic sampling only; saved native and builder are unchanged.'})
    poses, limits = make_poses(controller, joints)
    motor_results = actuator_inventory_check()
    say(f"Actual motor inventory: {motor_results['pass']}")
    if args.home_j3 is not None:
        original = poses[0][1]['J3']
        for name, pose in poses:
            if name != 'horizontal_stress_case' and name not in ('J3_min', 'J3_max', 'combined_low', 'combined_high'):
                pose['J3'] = args.home_j3
        diagnostic_changes.append({'change': 'home_J3_override', 'old': original, 'new': args.home_j3})
    if args.repair_control_drivers:
        for obj in bpy.data.objects:
            animation = obj.animation_data
            if not animation:
                continue
            for fcurve in animation.drivers:
                for variable in fcurve.driver.variables:
                    if variable.type == 'SINGLE_PROP':
                        continue
                    match = re.match(r'^(J[1-5]|GRIP)', obj.name)
                    if not match:
                        raise RuntimeError(f'Cannot infer diagnostic control driver property: {obj.name}')
                    key = match.group(1)
                    old_type = variable.type
                    variable.type = 'SINGLE_PROP'
                    variable.targets[0].id = controller
                    variable.targets[0].data_path = '["' + key + '"]'
                    diagnostic_changes.append({'change': 'driver_variable_type', 'object': obj.name,
                                               'old': old_type, 'new': 'SINGLE_PROP', 'property': key})
    # Clear animation only in this audit process so F-curves cannot overwrite
    # requested numerical poses. The source .blend is never saved or modified.
    controller.animation_data_clear()
    set_pose(controller, poses[0][1])
    depsgraph = bpy.context.evaluated_depsgraph_get()
    selected = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and
                (obj.get('part_id') or obj.get('collision_check', False) or critical_fastener(obj) or float(obj.get('mass_g', 0)) > 0)]
    cache = {obj: geometry(obj, depsgraph) for obj in selected}
    control_results = audit_controls(controller, joints, cache, poses[0][1], limits, gear_specs)
    centreline_results = neutral_centreline_check(controller, joints, cache, poses[0][1])
    bilateral_results = bilateral_link_check(joints,cache)
    electronics_results = electronics_keepout_check(cache)
    bilateral_interfaces = bilateral_assembly_interfaces(cache)
    inventory = mass_inventory(cache, joints)
    movable = [item for item in inventory if item['descendant_of']]
    output = {
        'audit': 'R06_independent_Blender_world_mesh_mass_and_collision_screen_v2',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'blend': str(args.blend.resolve()),
        'blend_file_bytes': args.blend.stat().st_size,
        'blend_modified_utc': datetime.fromtimestamp(args.blend.stat().st_mtime, timezone.utc).isoformat(),
        'units': {'mesh_length': 'mm', 'mass': 'g', 'gravity_m_s2': GRAVITY_M_S2, 'torque': 'Nm'},
        'PLA_solid_density_g_cm3': 1.24, 'moving_wiring_fastener_multiplier': ALLOWANCE,
        'joint_limits_deg': {key: bounds for key, bounds in limits.items() if key != 'GRIP'},
        'gripper_clear_gap_limits_mm': limits.get('GRIP'),
        'control_limits': limits,
        'diagnostic_in_memory_changes_not_saved': diagnostic_changes,
        'model_filename_is_final_native': args.blend.name == 'EDU06_R06.blend',
        'gear_specification_reference': gear_reference,
        'actual_actuator_inventory': motor_results,
        'control_response_checks': control_results,
        'neutral_centreline_alignment': centreline_results,
        'bilateral_link_geometry': bilateral_results,
        'reserved_electronics_service_space': electronics_results,
        'bilateral_structural_assembly_interfaces': bilateral_interfaces,
        'measured_XM_gear_cradle_separating_planes': measured_XM_gear_cradle_gaps(cache),
        'control_units': {key: ('mm clear pad gap' if key == 'GRIP' else 'deg') for key in limits},
        'collision_classifier_reference_checks': {
            'passed': True,
            'independent_EXACT_intersection_regressions': boolean_regression,
            'cases': 'Inside/outside cube, hollow sleeve bore/wall, four translated/rotated sleeves, four rotated thin solids with positive interior samples and negative samples 0.25 mm beyond each face, and aligned/rotated projection-plane tests for exact contact, a real 0.2 mm overlap and a real 0.2 mm gap',
            'method': 'World and object-local bounds, nearest outward-normal agreement, then majority odd/even parity of three rays; ray advances 0.005 mm',
            'local_bounds_regression_reason': 'Early world-space ray probes misclassified two gear-face points as inside XM cradles at global yaw extremes. In motor-local coordinates the points were Z≈0 while the cradle maximum was Z=-0.25, proving genuine 0.25 mm separation. Rigid rotation cannot create penetration. Local solid bounds now reject such impossible containment before ray testing; actual triangle crossings are still retained independently.',
        },
        'mass_summary': {
            'total_printed_structural_solid_mass_g': sum(x['mass_g'] for x in inventory if x['printed']),
            'total_assigned_purchased_reference_mass_g': sum(x['mass_g'] for x in inventory if not x['printed']),
            'moving_mass_g_before_allowance': sum(x['mass_g'] for x in movable),
            'moving_mass_g_with_10percent_allowance': sum(x['mass_g'] for x in movable) * ALLOWANCE,
            'fixed_mass_g': sum(x['mass_g'] for x in inventory if not x['descendant_of']),
            'printed_parts_with_nonpositive_signed_volume': [x['object'] for x in inventory if x['printed'] and not x['positive_mesh_volume']],
        },
        'mass_inventory': [{k: v for k, v in item.items() if k != 'obj'} for item in inventory],
        'poses': [],
        'limitations': [
            'Printed mass is the complete solid mesh at PLA 1.24 g/cm3; slicer shells/infill and actual print weights can differ.',
            'Motor mass is counted once from reference mass_g. Its COM is approximated by a uniform external case mesh, not measured internal mass distribution.',
            'A 10% proportional allowance adds moving cable/fastener weight. This is a planning allowance, not measured hardware accounting.',
            'Gravity uses world-axis dot cross(position difference, force). These calculations do not establish deformation, fatigue, thermal stability, friction or dynamic control.',
            'Motor comparison values 0.82/0.30 Nm derive from 20% of stall. The stated efficiencies and 1.5 factor are assumptions, not guaranteed continuous ratings or measured dynamics.',
            'Horizontal stress case may be outside declared joint limits or obstructed; it is explicitly marked and must not be interpreted as an attainable operating pose.',
            'Collision tests include printable meshes, explicitly marked references and the bilateral-link/root/retention fasteners identified by critical_fastener(). Other hardware, cables, fit coupons and the removed service panel are excluded. Hardware meshes use simplified nominal geometry.',
            'Motion collision groups use the nearest ancestor with an actuated transform, including translating gripper jaws. Fixed DATUM transforms inherit their parent body. The motion pass excludes same-body/fixed-to-fixed pairs. Separate motor-case-to-print and explicitly reported shaft/cheek/crossmember/bridge passes include same-body pairs. Other self-assembly interfaces are not exhaustively checked.',
            'BVH triangle intersections can include intended mating contacts and gear contacts. Classified contacts/crossings require engineering review; none are silently discarded.',
            'Sampled vertex interior depths are lower-bound indicators, not exact maximum penetration. Up to 64 vertices per direction are sampled; no continuous collision guarantee is provided.',
            'Interior samples require nearest-face normal agreement and three-direction majority ray parity. This relies on consistently outward-oriented closed meshes; invalid meshes require separate repair.',
            'Local-coordinate solid bounds reject impossible interior probes before ray parity; this preserves real submillimetre gaps after rigid rotations without exempting any named assembly pair.',
            'Ambiguous zero-depth targeted structural contacts receive an independent EXACT Boolean intersection-volume check; at most 0.01 mm3 is treated as numerical zero. This is not a manufacturing fit tolerance or an assurance of structural capacity.',
            'Native wiring checks verify the declared bus graph and actual evaluated curve-anchor drivers only. Flexible cable physics, clearance, bend radius, connectors and electrical performance require separate review.',
            'The source .blend is opened read-only in a separate process and never resaved by this audit.',
        ],
    }
    collidables = collision_objects(cache)
    set_pose(controller, poses[0][1])
    output['elbow_pinion_support_assembly_interfaces'] = collision_screen(collidables, target_object='E_07_pinion_journal_bridge')
    selected_poses = poses[:2] if args.home_only else poses
    for name, pose in selected_poses:
        say(f'Audit pose: {name}')
        set_pose(controller, pose)
        midpoint, tips = fingertip_midpoint(cache)
        payload_point = payload_tip_point()
        record = {'name': name, 'control_values': pose,
                  'joint_angles_deg': {key: value for key, value in pose.items() if key != 'GRIP'},
                  'gripper_clear_gap_mm': pose.get('GRIP'),
                  'outside_declared_limits': outside_limits(pose, limits),
                  'joint_origins_world_mm': {key: list(world_matrix(obj).translation) for key, obj in joints.items()},
                  'gripper_contact_samples': tips,
                  'gripper_contact_marker_note': 'Markers measure true pad gap near the roots; separate distal tool-tip marker is used for payload moment.',
                  'payload_application_point_world_mm': list(payload_point),
                  'wiring_kinematics': wiring_kinematics_check(),
                  'static_stability_25g': static_stability(inventory, payload_point, 25.0),
                  'load_cases': [load_case(inventory, joints, p, payload_point) for p in (0, 25, 50)]}
        if args.home_only and name != 'home':
            record['collision_screen'] = {'not_run': 'home-only diagnostic mode'}
        else:
            record['collision_screen'] = collision_screen(collidables)
            record['motor_case_to_printed_screen'] = collision_screen(collidables, case_printed_only=True)
            say(f"  collision classifications: {record['collision_screen']['classification_counts']}")
            say(f"  motor-case/printed classifications: {record['motor_case_to_printed_screen']['classification_counts']}")
        output['poses'].append(record)
        # Save incrementally so an interrupted audit retains completed results.
        output['complete'] = False
        args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    evaluated_rows = [(pose, case, key, row) for pose in output['poses']
                      for case in pose['load_cases'] for key, row in case['joints'].items()]
    output['summary'] = {
        'pose_count': len(output['poses']),
        'operating_pose_count_within_declared_limits': sum(not p['outside_declared_limits'] for p in output['poses']),
        'diagnostic_poses_outside_declared_limits': [p['name'] for p in output['poses'] if p['outside_declared_limits']],
        'full_declared_sampling_plan_completed': not args.home_only,
        'load_cases_exceeding_gravity_motor_comparison': [
            {'pose': p['name'], 'payload_g': c['payload_g'], 'joint': k,
             'motor_torque_nm': r['estimated_motor_gravity_torque_nm'],
             'comparison_nm': r['comparison_nm'], 'outside_declared_limits': bool(p['outside_declared_limits'])}
            for p, c, k, r in evaluated_rows if r['gravity_exceeds_estimated_motor_comparison']],
        'poses_with_sampled_gross_interpenetration': [p['name'] for p in output['poses'] if
            p['collision_screen'].get('classification_counts', {}).get('gross_interpenetration_sampled', 0)],
        'poses_requiring_collision_review': [p['name'] for p in output['poses'] if
            not p['collision_screen'].get('clear_of_reported_crossings_or_penetrations', True)],
        'operating_poses_requiring_collision_review': [p['name'] for p in output['poses'] if not p['outside_declared_limits'] and
            not p['collision_screen'].get('clear_of_reported_crossings_or_penetrations', True)],
        'poses_requiring_motor_case_to_printed_interface_review': [p['name'] for p in output['poses'] if
            not p.get('motor_case_to_printed_screen', {}).get('clear_of_reported_crossings_or_penetrations', True)],
        'elapsed_seconds': time.monotonic() - start,
        'physical_function_validated': False,
        'control_response_all_passed': control_results['all_passed'],
        'neutral_centreline_alignment_passed': centreline_results['pass'],
        'bilateral_link_geometry_passed': bilateral_results['pass'],
        'reserved_electronics_service_space_clear': electronics_results['pass'],
        'bilateral_structural_assembly_interfaces_clear': bilateral_interfaces['pass'],
        'actual_six_motor_five_arm_DOF_inventory_passed': motor_results['pass'],
        'poses_with_wiring_driver_or_topology_errors': [p['name'] for p in output['poses'] if not p['wiring_kinematics']['pass']],
        'elbow_pinion_support_assembly_interfaces_clear': output['elbow_pinion_support_assembly_interfaces']['clear_of_reported_crossings_or_penetrations'],
        'poses_with_25g_COM_outside_support_polygon': [p['name'] for p in output['poses']
            if not p['static_stability_25g']['static_projection_inside_support_polygon']],
    }
    output['complete'] = True
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    say(json.dumps(output['mass_summary'], indent=2))
    say(f"Finished audit: {args.output}; {len(output['summary']['load_cases_exceeding_gravity_motor_comparison'])} load/joint cases exceed the planning motor comparison")
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        (ROOT / 'assembly-audit-error.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
