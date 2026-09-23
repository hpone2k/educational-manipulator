"""Render actual assembled wrist orthographically; no geometric alterations."""
from pathlib import Path
import bpy,json,sys
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R04.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R04 | Engineering'))
bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
ctrl=next(o for o in scene.objects if o.name.startswith('CONTROL'))
ctrl.animation_data_clear()
for key in ['J4','J5','J6']:ctrl[key]=0.0
ctrl['GRIP']=45.0;ctrl.update_tag(refresh={'OBJECT'});bpy.context.view_layer.update()
j4=next(o for o in scene.objects if o.name.startswith('J4 ') and o.get('axis'))
def below(o):
    while o:
        if o==j4.parent:return True
        o=o.parent
    return False
objs=[o for o in scene.objects if below(o) and o.type=='MESH' and not o.name.startswith('LAYOUT')]
pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box]
right=(j4.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
up=(j4.matrix_world.to_3x3()@Vector((0,-1,0))).normalized()
normal=right.cross(up).normalized()
origin=j4.matrix_world.translation
xs=[(p-origin).dot(right) for p in pts];ys=[(p-origin).dot(up) for p in pts]
centre=origin+right*((min(xs)+max(xs))/2)+up*((min(ys)+max(ys))/2)
cam=scene.camera;cam.location=centre+normal*800
cam.rotation_euler=Matrix((right,up,normal)).transposed().to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=max(max(xs)-min(xs)+40,(max(ys)-min(ys)+95)*1.65)
for o in scene.objects:
    if o.type=='FONT' and not below(o):o.hide_render=True
    if o.type=='MESH' and not below(o):o.hide_render=True
mat=bpy.data.materials.new('Inspection label emission');mat.use_nodes=True
nodes=mat.node_tree.nodes;nodes.clear();em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.65,.9,.77,1);em.inputs[1].default_value=.8
out=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
def label(body,station,y,size):
    font=bpy.data.curves.new(body,'FONT');font.body=body;font.align_x='CENTER';font.size=size
    o=bpy.data.objects.new(body,font);scene.collection.objects.link(o);o.location=origin+right*station+up*y+normal*140;o.rotation_euler=cam.rotation_euler;font.materials.append(mat)
for body,station,dy in [('J4 / ROLL',0,14),('J5 / PITCH 3:1',78,33),('J6 / ROLL',119,14),('PARALLEL GRIPPER',241,25)]:label(body,station,max(ys)+dy,5.4)
label('CENTRED WRIST  |  75 mm FINGERS  |  20–70 mm OPENING',(min(xs)+max(xs))/2,min(ys)-26,5.5)
# A controlled neutral background isolates the straight wrist; actual original lighting remains.
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.05,.04,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'wrist-straight-preview.png')
bpy.ops.render.render(write_still=True)
(ROOT/'INSPECTION_COMPLETE.json').write_text(json.dumps({'ok':True,'file':'wrist-straight-preview.png'}))
