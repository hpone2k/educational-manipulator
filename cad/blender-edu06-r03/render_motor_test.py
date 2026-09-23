import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'motor-test/motor_test.blend'))
s=bpy.context.scene
bpy.ops.object.camera_add(location=(120,-190,-240))
cam=bpy.context.object;cam.rotation_euler=(Vector((0,-13,-16))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=245;s.camera=cam
for p,e in [((20,-70,-180),800),((-150,60,-130),600),((160,70,-60),450)]:
 bpy.ops.object.light_add(type='AREA',location=p);l=bpy.context.object;l.data.energy=e*10000;l.data.shape='DISK';l.data.size=150
 l.rotation_euler=(Vector((0,-13,-16))-l.location).to_track_quat('-Z','Y').to_euler()
s.world=bpy.data.worlds.new('Motor Test World');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.14,1)
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1400;s.render.resolution_y=800;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'motor-test/motor-rear-preview.png')
bpy.ops.render.render(write_still=True)
(ROOT/'motor-test/render-complete.txt').write_text('done')
