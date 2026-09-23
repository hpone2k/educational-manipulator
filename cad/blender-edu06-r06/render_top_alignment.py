"""Render actual R06 geometry from above, with centreline evidence. Read-only."""
import bpy, sys, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R06.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 | Engineering'))
bpy.context.window.scene=scene
scene.frame_set(1)
control=next(o for o in scene.objects if o.name.startswith('CONTROL'))
control.animation_data_clear()
for key in ('J1','J4','J5'):control[key]=0.
control.update_tag();bpy.context.view_layer.update()
for o in scene.objects:
    parent=o;hidden=False
    while parent:
        if parent.name.startswith(('B03_service_front_panel','F01','F02')):hidden=True;break
        parent=parent.parent
    if o.type=='FONT' or hidden:o.hide_render=True
objects=[o for o in scene.objects if o.type=='MESH' and o.get('part_id') and not o.hide_render]
points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
lo=Vector(tuple(min(v[i] for v in points) for i in range(3)))
hi=Vector(tuple(max(v[i] for v in points) for i in range(3)))
target=Vector(((lo.x+hi.x)/2,0,150))
cam=scene.camera;cam.location=target+Vector((0,0,1600));cam.rotation_euler=(0,0,0)
cam.data.type='ORTHO';cam.data.ortho_scale=max(hi.x-lo.x+85, (hi.y-lo.y+140)*1.8)
scene.render.resolution_x=1800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.cycles.samples=32
label=bpy.data.materials.new('Alignment overlay');label.use_nodes=True
label.node_tree.nodes.clear()
em=label.node_tree.nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.75,.95,.84,1)
out=label.node_tree.nodes.new('ShaderNodeOutputMaterial');label.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
scene.view_settings.exposure=-.25
def text(name,body,x,y,size):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.align_x='CENTER';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=(x,y,950);d.materials.append(label)
def line(name,pts,r=.33):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2
    s=d.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);d.materials.append(label)
height=cam.data.ortho_scale/1.8
text('Top title','R06 / CENTRED ARM + BILATERAL SUPPORT',target.x,height*.435,12)
text('Top subtitle','ACTUAL BLENDER GEOMETRY  |  J1, J4, J5 = 0 DEG',target.x,height*.390,5.5)
for i in range(int((hi.x+25-lo.x)/16)):
    x=lo.x+16*i
    line('Centreline',[(x,0,900),(x+8,0,900)],.35)
joints={o.name[:2]:o for o in scene.objects if o.get('axis') and o.name[:2] in ('J2','J3','J4','J5')}
rows=[]
for key,o in joints.items():
    c=o.matrix_world.translation;rows.append({'joint':key,'world_xyz_mm':list(c)})
    line(key+' leader',[(c.x,0,920),(c.x,-82,920)],.3)
    text(key+' label',key,c.x,-92,7)
text('Base dimension','241 x 240 mm BASE ENVELOPE',0,136,6)
text('Footnote','PAIRED PRINTED LOAD PATHS  /  GEARED EXTERNAL PIVOTS  /  SIX MOTORS',target.x,-height*.45,5)
scene.render.filepath=str(ROOT/'top-alignment-preview.png')
bpy.ops.render.render(write_still=True)
(ROOT/'top-alignment-render.json').write_text(json.dumps({'pose':{k:float(control[k]) for k in ('J1','J2','J3','J4','J5')},'joint_centres':rows,'note':'View of modelled geometry; not proof of stiffness or load sharing.'},indent=2),encoding='utf-8')
