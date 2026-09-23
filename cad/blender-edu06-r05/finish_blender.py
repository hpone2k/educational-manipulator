"""Fresh-load presentation pass. Does not change engineering part geometry."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector, Matrix, Euler
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R05.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R05'))
bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
control=next(o for o in scene.objects if o.name.startswith('CONTROL'))
control.id_properties_ui('J2').update(min=45.0,max=90.0,soft_min=45.0,soft_max=90.0,description='Shoulder output degrees;45–90 provisional range from geometry/gravity screening')
j2=next(o for o in scene.objects if o.name.startswith('J2 ') and o.get('axis'))
j2['limits_deg']=[45.0,90.0]
panel=bpy.data.objects.get('B03_service_front_panel')
if panel:panel.location.z=-6.5
bpy.context.view_layer.update()
base=bpy.data.objects.get('B01_open_front_base_240x190')
if base:base['description']='4 mm walls, 5 mm floor; four M4 fasteners attach printed feet. External bench attachment must be provided separately. M3 captive nuts in top posts.'
camera=scene.camera
# Re-frame actual, evaluated assembly after drivers have been evaluated on load.
objects=[o for o in scene.objects if o.type=='MESH' and o.get('part_id') and not o.name.startswith('F0')]
points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
lo=Vector(tuple(min(v[i] for v in points) for i in range(3)));hi=Vector(tuple(max(v[i] for v in points) for i in range(3)))
target=(lo+hi)/2
camera.location=target+Vector((730,-1060,580));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
rot=camera.rotation_euler.to_matrix();right=rot@Vector((1,0,0));up=rot@Vector((0,1,0));toward=rot@Vector((0,0,1))
xs=[(p-target).dot(right) for p in points];ys=[(p-target).dot(up) for p in points]
target+=right*((max(xs)+min(xs))/2)+up*((max(ys)+min(ys))/2)
camera.location=target+Vector((730,-1060,580));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
aspect=1800/1350;camera.data.ortho_scale=max(max(xs)-min(xs),(max(ys)-min(ys))*aspect)*1.28
height=camera.data.ortho_scale/aspect
centre=target+toward*420
for name,y,size in [('Presentation title',height*.445,14),('Presentation subtitle',height*.406,5.4),('Presentation note',-height*.46,4.6)]:
    o=bpy.data.objects.get(name)
    if o:o.location=centre+up*y;o.rotation_euler=camera.rotation_euler;o.data.size=size
scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
scene.cycles.samples=48
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.clip_end=10000;space.shading.type='MATERIAL'
            space.region_3d.view_rotation=camera.rotation_euler.to_quaternion();space.region_3d.view_location=target;space.region_3d.view_distance=camera.data.ortho_scale*1.3
            space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=10
            space.overlay.show_overlays=False
        elif area.type=='PROPERTIES':area.spaces.active.context='OBJECT'
for o in scene.objects:o.select_set(False)
control.select_set(True);bpy.context.view_layer.objects.active=control
# Standalone, millimetre print-layout scene with each part at Z=0.
for old_scene in list(bpy.data.scenes):
    if old_scene.name.startswith('EDU06 R05 | Individual print parts'):
        for old_obj in list(old_scene.objects):bpy.data.objects.remove(old_obj,do_unlink=True)
        bpy.data.scenes.remove(old_scene)
layout=bpy.data.scenes.new('EDU06 R05 | Individual print parts')
layout.unit_settings.system='METRIC';layout.unit_settings.scale_length=.001;layout.unit_settings.length_unit='MILLIMETERS'
col=bpy.data.collections.new('PRINT LAYOUT — one occurrence per exported STL');layout.collection.children.link(col)
parts=sorted([o for o in scene.objects if o.get('part_id')],key=lambda o:o.name)
for i,source in enumerate(parts):
    o=source.copy();o.data=source.data;o.parent=None;o.animation_data_clear();o.matrix_world=Matrix.Identity(4);o.name='LAYOUT | '+source['part_id'];col.objects.link(o)
    rotation=Euler(tuple(math.radians(v) for v in source.get('print_rotation_deg',[0,0,0]))).to_matrix()
    coords=[rotation@v.co for v in o.data.vertices]
    bmin=Vector(tuple(min(v[j] for v in coords) for j in range(3)));bmax=Vector(tuple(max(v[j] for v in coords) for j in range(3)))
    x=(i%10)*285;y=-(i//10)*285
    o.matrix_world=Matrix.Translation((x-(bmin.x+bmax.x)/2,y-(bmin.y+bmax.y)/2,-bmin.z))@rotation.to_4x4()
    o.hide_render=False;o.hide_viewport=False
    o['README']='One manufacturing mesh, same local dimensions as STL. Not an assembled robot. Check prototype status before printing.'
    font=bpy.data.curves.new(source['part_id']+' label','FONT');font.body=source['part_id'];font.size=9
    label=bpy.data.objects.new(source['part_id']+' label',font);col.objects.link(label);label.location=(x-125,y-126,.5)
    font.materials.append(bpy.data.materials.get('Light markings'))
layout['README']='All individual printable prototypes arranged on a285mm pitch. Each fits one256mm A1 build cube as checked in stl-audit.json; this is not an automatic slicer plate arrangement.'
bpy.context.window.scene=scene
note=bpy.data.objects.get('Presentation note')
if note:note.hide_render=True
for name in ['README.md','engineering-review.md','motor-and-fastener-guide.md','structural-fasteners.md','build_edu06.py','blender_lib.py','motor_models.py','gear_math.py']:
    if (ROOT/name).exists():
        old=bpy.data.texts.get(name)
        if old:bpy.data.texts.remove(old)
        tx=bpy.data.texts.new(name);tx.write((ROOT/name).read_text(encoding='utf-8'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'EDU06_R05.blend'))
# The hero is a rendering of the actual editable geometry, not an AI image.
scene.render.filepath=str(ROOT/'assembled-preview.png');bpy.ops.render.render(write_still=True,scene=scene.name)
home_cam=camera.matrix_world.copy();home_scale=camera.data.ortho_scale
titles=[bpy.data.objects.get(n) for n in ['Presentation title','Presentation subtitle','Presentation note']]
for o in titles:
    if o:o.hide_render=True
# Base detail, with removable lid/deck hidden only in the render process.
hidden=[]
for o in scene.objects:
    if o.name.startswith(('B02_','B10_')):hidden.append(o);o.hide_render=True
camera.location=(310,-500,285);target2=Vector((-5,0,56));camera.rotation_euler=(target2-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=310
scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.filepath=str(ROOT/'base-detail.png');bpy.ops.render.render(write_still=True,scene=scene.name)
for o in hidden:o.hide_render=False
camera.matrix_world=home_cam;camera.data.ortho_scale=home_scale
for o in titles:
    if o:o.hide_render=False
scene.render.resolution_x=1800;scene.render.resolution_y=1350
(ROOT/'PRESENTATION_COMPLETE.json').write_text(json.dumps({'ok':True,'hero':'assembled-preview.png','base':'base-detail.png','parts_scene_count':len(parts)},indent=2))
