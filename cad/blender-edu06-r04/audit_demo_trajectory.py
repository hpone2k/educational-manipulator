"""Fresh-load read-only screening of the delivered animation, sampled every 12 frames.

Keeps CONTROL keyframes intact. Calls the independently tested mesh collision
checker; does not replace the assembly model, animation or output .blend.
"""
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import audit_assembly as audit


def run():
    path = ROOT / 'EDU06_R04.blend'
    output_path = ROOT / 'demo-trajectory-audit.json'
    if not path.exists():
        raise RuntimeError('Native model is not ready')
    start = time.monotonic()
    audit.test_ray_parity()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scenes = [scene for scene in bpy.data.scenes if 'Engineering assembly' in scene.name]
    if len(scenes) != 1:
        raise RuntimeError('Cannot uniquely select engineering assembly scene')
    bpy.context.window.scene = scenes[0]
    scene = scenes[0]
    controller, joints = audit.find_controls()
    if controller.animation_data is None or controller.animation_data.action is None:
        raise RuntimeError('CONTROL animation is missing; cannot audit delivered trajectory')
    limits = {key: [float(x) for x in obj['limits_deg']] for key, obj in joints.items()}
    ui = controller.id_properties_ui('GRIP').as_dict()
    limits['GRIP'] = [float(ui.get('min', 20)), float(ui.get('max', 70))]
    scene.frame_set(1)
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    selected = [obj for obj in scene.objects if obj.type == 'MESH' and
                (obj.get('part_id') or obj.get('collision_check', False))]
    cache = {obj: audit.geometry(obj, graph) for obj in selected}
    collidables = audit.collision_objects(cache)
    frames = list(range(1, 361, 12)) + [360]
    output = {
        'audit': 'fresh_load_delivered_animation_collision_sampling_v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'blend': str(path.resolve()), 'blend_bytes': path.stat().st_size,
        'blend_modified_utc': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        'animation_action': controller.animation_data.action.name,
        'scene': scene.name, 'sampled_frames': frames, 'fps': scene.render.fps,
        'controller_animation_preserved': True, 'complete': False,
        'frames': [],
        'limitations': [
            'This checks 31 discrete snapshots, not every frame or continuous swept collision.',
            'The actual CONTROL keyframe animation is evaluated; its action is never cleared or replaced.',
            'Same-rigid-body pairs and removed service panel/coupons are excluded as in the assembly audit.',
            'Matching motor case/stock-horn zero-depth contacts are explicitly identified and retained.',
            'The mesh classifier cannot establish strength, friction, cable flex, dynamics or physical buildability.',
        ],
    }
    for frame in frames:
        scene.frame_set(frame)
        controller.update_tag(refresh={'OBJECT'})
        bpy.context.view_layer.update()
        bpy.context.evaluated_depsgraph_get().update()
        angles = {key: float(controller[key]) for key in limits}
        midpoint, tips = audit.fingertip_midpoint(cache)
        result = audit.collision_screen(collidables)
        row = {'frame': frame, 'time_seconds': (frame - 1) / scene.render.fps,
               'evaluated_CONTROL_values': angles,
               'control_units': {key: ('mm clear pad gap' if key == 'GRIP' else 'deg') for key in limits},
               'angles_outside_declared_limits': audit.outside_limits(angles, limits),
               'grip_contact_midpoint_world_mm': list(midpoint),
               'tool_tip_world_mm': list(audit.payload_tip_point()), 'collision_screen': result}
        output['frames'].append(row)
        output_path.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        audit.say(f"Demo frame {frame}: {result['classification_counts']}")
    output['complete'] = True
    output['summary'] = {
        'sample_count': len(output['frames']),
        'frames_with_unresolved_crossings_or_penetrations': [row['frame'] for row in output['frames'] if not row['collision_screen']['clear_of_reported_crossings_or_penetrations']],
        'frames_outside_declared_joint_limits': [row['frame'] for row in output['frames'] if row['angles_outside_declared_limits']],
        'all_sampled_frames_clear_of_unresolved_crossings_or_penetrations': all(row['collision_screen']['clear_of_reported_crossings_or_penetrations'] for row in output['frames']),
        'elapsed_seconds': time.monotonic() - start,
        'continuous_motion_validated': False,
        'physical_function_validated': False,
    }
    output_path.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    audit.say(json.dumps(output['summary'], indent=2))


if __name__ == '__main__':
    run()
