"""Render six labelled actual motor cases without saving or changing the native file.

Run with Blender --background --python render_motor_map.py -- [--blend path]
The default input is the final EDU06_R06.blend; --blend BUILD_DEBUG.blend is
available for a provisional layout check. Labels are camera-facing Blender
geometry. Leader endpoints are orthogonal projections of case bounding centres.
"""
from pathlib import Path
import argparse
import json
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--blend', default=str(ROOT / 'EDU06_R06.blend'))
parser.add_argument('--output', default=str(ROOT / 'motor-map.png'))
parser.add_argument('--samples', type=int, default=32)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
source = Path(args.blend)
if not source.is_absolute():
    source = ROOT / source
stamp = (source.stat().st_size, source.stat().st_mtime_ns)
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 | Engineering'))
bpy.context.window.scene = scene
scene.frame_set(1)
bpy.context.view_layer.update()

specs = [
    ('J1_BASE', 'J1  BASE ROTATION', 'AX-12A  /  3:1 reduction', 'left'),
    ('S_XM', 'J2  SHOULDER', 'XM430-W350-T  /  5:1 reduction', 'left'),
    ('E_XM', 'J3  ELBOW', 'XM430-W350-T  /  4:1 reduction', 'left'),
    ('J4_AX', 'J4  WRIST PITCH', 'AX-12A  /  3:1 reduction', 'right'),
    ('J5_AX', 'J5  TOOL ROLL', 'AX-12A  /  direct drive', 'right'),
    ('GRIP', 'POWERED GRIPPER', 'AX-12A  /  opposed rack drive', 'right'),
]
cases = [o for o in scene.objects if o.get('interface_role') == 'case']
assert len(cases) == 6, f'Expected six actual motor cases; found {[o.name for o in cases]}'
assert sum(o.get('motor_type') == 'AX-12A' for o in cases) == 4
assert sum(o.get('motor_type') == 'XM430-W350-T' for o in cases) == 2

cam = scene.camera
assert cam is not None
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 1030.0
cam.data.clip_end = 6000
right = cam.rotation_euler.to_matrix() @ Vector((1, 0, 0))
up = cam.rotation_euler.to_matrix() @ Vector((0, 1, 0))
toward = cam.rotation_euler.to_matrix() @ Vector((0, 0, 1))
# Match the original hero camera aim. The overlay plane is close to the camera
# and well in front of the assembly, so annotations cannot be occluded by it.
centre = Vector((115, 0, 220))
overlay = cam.location - toward * 200
for o in scene.objects:
    if o.name.startswith('Presentation '):
        o.hide_render = True

collection = bpy.data.collections.new('MOTOR MAP / render annotations only')
scene.collection.children.link(collection)

def emission(name, color, strength=1):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    e = mat.node_tree.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = (*color, 1)
    e.inputs[1].default_value = strength
    out = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(e.outputs[0], out.inputs['Surface'])
    return mat

white = emission('Map / warm white type', (.91, 1.0, .96), 1.0)
muted = emission('Map / secondary type', (.60, .79, .68), .9)
accent = emission('Map / mint linework', (.30, .61, .46), .9)
foot = emission('Map / footer ink', (.022, .071, .043), .8)
fonts = {}
for role, filename in [('regular', 'segoeui.ttf'), ('bold', 'seguisb.ttf')]:
    path = Path('C:/Windows/Fonts') / filename
    if path.exists():
        fonts[role] = bpy.data.fonts.load(str(path))

def screen_point(x, y, depth=0):
    return overlay + right*x + up*y + toward*depth

def text(body, x, y, size, mat=white, bold=False):
    font = bpy.data.curves.new('Map text / ' + body, 'FONT')
    font.body = body
    font.size = size
    font.align_x = 'LEFT'
    font.space_character = 1.05
    font.resolution_u = 12
    role = 'bold' if bold else 'regular'
    if role in fonts:
        font.font = fonts[role]
    obj = bpy.data.objects.new(font.name, font)
    collection.objects.link(obj)
    obj.location = screen_point(x, y, .5)
    obj.rotation_euler = cam.rotation_euler
    font.materials.append(mat)
    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = False
    return obj

def line(name, points, radius=.40, mat=accent, closed=False):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, xy in zip(spline.points, points):
        point.co = (*screen_point(*xy), 1)
    spline.use_cyclic_u = closed
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    curve.materials.append(mat)
    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = False
    return obj

def marker(name, x, y):
    import math
    circle = [(x+3.2*math.cos(i*math.tau/32), y+3.2*math.sin(i*math.tau/32)) for i in range(32)]
    line(name+' / motor centre ring', circle, .5, white, True)
    line(name+' / motor centre dot', [(x-.55, y), (x+.55, y)], 1.0, white)

located = []
for prefix, title, detail, side in specs:
    case = next(o for o in cases if o.get('motor_id') == prefix)
    world_points = [case.matrix_world @ Vector(c) for c in case.bound_box]
    world_centre = sum(world_points, Vector()) / 8
    # Reuse the actual camera optical axis, so the projected leader endpoints
    # stay correct if the supplied saved hero camera's location is adjusted.
    delta = world_centre - cam.location
    xy = (delta.dot(right), delta.dot(up))
    located.append(dict(prefix=prefix, title=title, detail=detail, side=side,
                        xy=xy, object=case.name, centre=list(world_centre)))

text('EDU06 / MOTOR MAP', -467, 310, 21, white, True)
text('4 × AX-12A  +  2 × XM430-W350-T', -467, 283, 12, muted)
text('FIVE ARM AXES + POWERED GRIPPER', 239, 308, 10, muted)
line('Map / header rule', [(-467, 268), (467, 268)], .27, muted)

for side in ['left', 'right']:
    group = sorted((r for r in located if r['side'] == side), key=lambda r:r['xy'][1], reverse=True)
    # Left follows the rising base/shoulder/elbow; right fans out the compact
    # wrist/gripper group. Sorting the leader anchors avoids line crossings.
    rows = [185, 30, -130] if side == 'left' else [206, 79, -48]
    for row, item in zip(rows, group):
        lx = -467 if side == 'left' else 285
        text(item['title'], lx, row+5, 14.5, white, True)
        text(item['detail'], lx, row-14, 10.5, muted)
        px, py = item['xy']
        edge = -265 if side == 'left' else 269
        elbow = -236 if side == 'left' else 239
        route = [(lx, row-28), (edge, row-28), (elbow, py), (px, py)]
        if side == 'right':
            route = [(lx, row-28), (elbow, row-28), (px+15, py), (px, py)]
        line('Map / leader ' + item['prefix'], route, .38)
        marker(item['prefix'], px, py)

line('Map / footer rule', [(-467, -306), (467, -306)], .27, muted)
text('ACTUAL ASSEMBLED MOTOR GEOMETRY', -467, -328, 11, white, True)
text('Leaders locate motor-case centres · Official ROBOTIS CAD · Dimensions in millimetres', -467, -347, 9.5, white)
text('EDU06 / R06', 375, -329, 11, foot)

scene.render.engine = 'CYCLES'
scene.cycles.samples = args.samples
scene.cycles.use_denoising = True
scene.render.resolution_x = 2400
scene.render.resolution_y = 1700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.filepath = str(Path(args.output).resolve())
bpy.ops.render.render(write_still=True, scene=scene.name)
assert stamp == (source.stat().st_size, source.stat().st_mtime_ns), 'Source file unexpectedly changed during render'
print('MOTOR_MAP_COMPLETE ' + json.dumps(dict(source=str(source), output=scene.render.filepath, motors=located)))
