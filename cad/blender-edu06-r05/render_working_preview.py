"""Read-only render of the current complete assembly for visual review."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'BUILD_DEBUG.blend'))
scene=next(s for s in bpy.data.scenes if 'Engineering assembly' in s.name)
bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
points=[o.matrix_world@Vector(c) for o in scene.objects if o.type=='MESH' and o.get('part_id') and not o.name.startswith('F0') for c in o.bound_box]
lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
target=(lo+hi)/2;cam=scene.camera;cam.location=target+Vector((730,-1060,580))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
rot=cam.rotation_euler.to_matrix();right=rot@Vector((1,0,0));up=rot@Vector((0,1,0))
xs=[(p-target).dot(right) for p in points];ys=[(p-target).dot(up) for p in points]
cam.data.ortho_scale=max(max(xs)-min(xs),(max(ys)-min(ys))*4/3)*1.18
for o in scene.objects:
    if o.name.startswith('Presentation '):o.hide_render=True
scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.filepath=str(ROOT/'working-preview.png');bpy.ops.render.render(write_still=True)
