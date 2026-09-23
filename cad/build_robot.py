"""Generate the EDU-05 Blender concept, prototype STLs, and two preview renders.

Run in a NEW Blender background process. The script creates new scenes and never
deletes an existing scene. Geometry uses millimetres: 1 Blender unit = 1 mm.
All mounting dimensions are placeholders until the real hardware is measured.
"""
import bpy
import bmesh
import csv
import json
import math
import os
import struct
import traceback
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
STL = OUT / 'prototype_stl'
STL.mkdir(exist_ok=True)
PARAM = {
    'upper_arm_mm': 180, 'forearm_mm': 150, 'wrist_mm': 52,
    'base_radius_mm': 90, 'housing_radius_mm': 56,
    'pivot_bore_mm': 8.4, 'm3_clearance_mm': 3.4,
    'm4_clearance_mm': 4.4, 'anchor_clearance_mm': 6.6,
    'upper_plate_mm': 7, 'forearm_plate_mm': 7,
    'upper_gap_mm': 46, 'forearm_gap_mm': 30,
    'pose_degrees': [18, 65, -80, -20, 15], 'gripper_opening_mm': 34,
    'dimension_status': 'PROVISIONAL — NOT MATCHED TO USER HARDWARE',
}
if (OUT / 'parameters.json').exists():
    PARAM.update(json.loads((OUT / 'parameters.json').read_text(encoding='utf-8')))
(OUT / 'parameters.json').write_text(json.dumps(PARAM, indent=2), encoding='utf-8')

log = open(OUT / 'build.log', 'w', encoding='utf-8', buffering=1)
def report(message):
    print(message, flush=True)
    log.write(str(message) + '\n')

assembly = bpy.data.scenes.new('EDU-05 | Assembled')
bpy.context.window.scene = assembly
assembly.unit_settings.system = 'METRIC'
assembly.unit_settings.scale_length = .001
assembly.unit_settings.length_unit = 'MILLIMETERS'
assembly['README'] = 'Concept geometry. Use the five JOINT empties to rotate the arm. STL files are provisional fit-test parts.'
parts_collection = bpy.data.collections.new('01 | Printed structure')
hardware_collection = bpy.data.collections.new('02 | Reference hardware — not for printing')
rig_collection = bpy.data.collections.new('03 | Joint controls — rotate these empties')
labels_collection = bpy.data.collections.new('04 | Joint labels')
presentation_collection = bpy.data.collections.new('05 | Studio')
source_collection = bpy.data.collections.new('00 | Part masters — hidden')
for col in (parts_collection, hardware_collection, rig_collection, labels_collection, presentation_collection, source_collection):
    assembly.collection.children.link(col)

def mat(name, color, metallic=0, roughness=.35):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    return material

shell = mat('Printed | porcelain polymer', (.67,.76,.73), .18, .3)
mint = mat('Printed | mint polymer', (.13,.57,.40), .12, .32)
dark = mat('Reference | motor housing', (.027,.045,.05), .55, .25)
steel = mat('Reference | brushed steel', (.42,.51,.53), .82, .22)
rubber = mat('Reference | rubber / leadscrew', (.012,.019,.022), .05, .7)
text_mat = mat('Labels | light', (.72,.91,.84), .0, .7)
text_shader=text_mat.node_tree.nodes.get('Principled BSDF')
text_shader.inputs['Emission Color'].default_value=(.72,.91,.84,1)
text_shader.inputs['Emission Strength'].default_value=.7
ground_mat = mat('Studio | graphite', (.045,.065,.067), .1, .65)
masters = {}
instances = []
part_report = []

def recollect(obj, collection):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    collection.objects.link(obj)

def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply(obj, modifier):
    active(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)

def cube(name, size, loc=(0,0,0), material=None, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=size
    active(obj)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new('Rounded printable edges','BEVEL')
        mod.width=bevel
        mod.segments=3
        apply(obj,mod)
    if material:
        obj.data.materials.append(material)
    return obj

def cylinder(name,radius,depth,loc=(0,0,0),axis='Z',material=None,vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    obj=bpy.context.object
    obj.name=name
    if axis=='X': obj.rotation_euler[1]=math.pi/2
    if axis=='Y': obj.rotation_euler[0]=math.pi/2
    active(obj)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if material: obj.data.materials.append(material)
    return obj

def boolean(obj,tool,operation='DIFFERENCE'):
    mod=obj.modifiers.new('Machined feature','BOOLEAN')
    mod.operation=operation
    mod.solver='EXACT'
    mod.object=tool
    apply(obj,mod)
    bpy.data.objects.remove(tool,do_unlink=True)
    finish(obj)
    return obj

def hole(obj,xyz,diameter,depth=100,axis='Z'):
    return boolean(obj,cylinder('Temporary hole',diameter/2,depth,xyz,axis))

def finish(obj):
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj

def record(code,obj,description,orientation='Largest flat face on the bed'):
    finish(obj)
    # Bake the construction location into vertices. Part masters share origin 0.
    obj.data.transform(obj.matrix_world)
    obj.matrix_world=Matrix.Identity(4)
    obj.name=code
    recollect(obj,source_collection)
    obj['part_id']=code
    obj['status']='PROTOTYPE — hardware dimensions unverified'
    obj['description']=description
    obj['print_orientation']=orientation
    masters[code]=obj
    return obj

def transform(loc=(0,0,0),rot=(0,0,0)):
    from mathutils import Euler
    return Matrix.Translation(Vector(loc)) @ Euler(rot,'XYZ').to_matrix().to_4x4()

def instance(code,parent=None,loc=(0,0,0),rot=(0,0,0),suffix=''):
    obj=masters[code].copy()
    obj.data=masters[code].data
    obj.name=code + (' | '+suffix if suffix else '')
    parts_collection.objects.link(obj)
    obj.parent=parent
    obj.matrix_parent_inverse=Matrix.Identity(4)
    obj.matrix_basis=transform(loc,rot)
    instances.append((code,obj))
    return obj

def ref(obj,parent=None):
    recollect(obj,hardware_collection)
    obj.parent=parent
    obj['status']='Reference only — replace with measured hardware'
    return obj

def pivot(name,parent,loc,axis,angle):
    obj=bpy.data.objects.new(name,None)
    rig_collection.objects.link(obj)
    obj.empty_display_type='ARROWS'
    obj.empty_display_size=24
    obj.parent=parent
    obj.location=loc
    obj.rotation_mode='XYZ'
    obj.rotation_euler['XYZ'.index(axis)]=math.radians(angle)
    obj['axis']=axis
    obj['nominal_angle_degrees']=angle
    obj['instructions']='Rotate this empty about its named LOCAL axis; all downstream parts follow.'
    return obj

def motor(parent,r=22,length=46):
    ref(cylinder('REFERENCE | joint motor',r,length,axis='Y',material=dark),parent)
    for sign in (-1,1):
        ref(cylinder('REFERENCE | motor face',r*.88,3,(0,sign*(length/2+1.5),0),'Y',steel),parent)
        ref(cylinder('REFERENCE | pivot shaft',4,length+18,axis='Y',material=steel),parent) if sign==1 else None

def build_parts():
    report('Creating separate structural parts…')
    base=cylinder('base',PARAM['base_radius_mm'],12,(0,0,6),material=mint)
    hole(base,(0,0,6),24.4)
    for angle in (45,135,225,315):
        t=math.radians(angle)
        hole(base,(74*math.cos(t),74*math.sin(t),6),PARAM['anchor_clearance_mm'])
    for x in (-32,32):
        for y in (-32,32):hole(base,(x,y,6),PARAM['m4_clearance_mm'])
    record('P01_base_plate',base,'180 mm base plate with four anchor holes and cable bore')

    housing=cylinder('housing',PARAM['housing_radius_mm'],64,(0,0,32),material=shell)
    boolean(housing,cylinder('motor cavity',PARAM['housing_radius_mm']-8,62,(0,0,39)))
    hole(housing,(0,0,4),24.4)
    for x in (-32,32):
        for y in (-32,32):hole(housing,(x,y,4),PARAM['m4_clearance_mm'])
    # Provisional 31 mm square mounting pattern; no real motor compatibility implied.
    for x in (-15.5,15.5):
        for y in (-15.5,15.5):hole(housing,(x,y,4),PARAM['m3_clearance_mm'])
    record('P02_motor_housing',housing,'Open cup, 8 mm floor and 8 mm walls; provisional motor mounting')

    deck=cylinder('deck',56,10,(0,0,-5),material=mint)
    hole(deck,(0,0,-5),PARAM['pivot_bore_mm'])
    bracket_foot_y=PARAM['upper_gap_mm']/2+PARAM['upper_plate_mm']-8
    for x in (-14,14):
        for y in (-bracket_foot_y,bracket_foot_y):hole(deck,(x,y,-5),PARAM['m4_clearance_mm'])
    for angle in (0,90,180,270):
        t=math.radians(angle)
        hole(deck,(42*math.cos(t),42*math.sin(t),-5),PARAM['m3_clearance_mm'])
    record('P03_rotating_deck',deck,'Yaw deck; coupling and bearing arrangement require hardware design')

    cheek=cube('cheek',(50,64,8),(0,32,4),shell,2)
    boolean(cheek,cube('mounting foot',(50,10,26),(0,5,13),shell,1),'UNION')
    hole(cheek,(0,44,4),PARAM['pivot_bore_mm'])
    for x in (-14,14):hole(cheek,(x,5,17),PARAM['m4_clearance_mm'],50,'Y')
    for x in (-8,8):
        for y in (36,52):hole(cheek,(x,y,4),PARAM['m3_clearance_mm'])
    record('P04_shoulder_bracket',cheek,'Reversible shoulder bracket with integral mounting foot')

    def link(code,length,width,thickness):
        plate=cube(code,(length+width,width,thickness),(length/2,0,thickness/2),shell,2)
        relief=cube('central relief',(length-68,16,thickness+16),(length/2,0,thickness/2),bevel=3)
        boolean(plate,relief)
        for x in (0,length):
            hole(plate,(x,0,thickness/2),PARAM['pivot_bore_mm'])
            for dx in (-8,8):
                for dy in (-8,8):hole(plate,(x+dx,dy,thickness/2),PARAM['m3_clearance_mm'])
        for x in (27,length-27):hole(plate,(x,0,thickness/2),PARAM['m4_clearance_mm'])
        record(code,plate,f'{length} mm pivot spacing; two side plates form one link')
    link('P05_upper_link_plate',PARAM['upper_arm_mm'],46,PARAM['upper_plate_mm'])
    link('P06_forearm_plate',PARAM['forearm_mm'],38,PARAM['forearm_plate_mm'])

    for code,length in [('P07_upper_spacer',PARAM['upper_gap_mm']),('P08_forearm_spacer',PARAM['forearm_gap_mm'])]:
        obj=cylinder(code,8,length,(0,0,length/2),material=mint)
        hole(obj,(0,0,length/2),PARAM['m4_clearance_mm'],length+10)
        record(code,obj,'Link cross spacer with through-bolt bore','Stand on one annular end; verify hole tolerance')

    wrist_length=PARAM['wrist_mm']
    bridge=cube('wrist link',(wrist_length+30,38,7),(wrist_length/2,0,3.5),shell,2)
    for x in (0,wrist_length):hole(bridge,(x,0,3.5),PARAM['pivot_bore_mm'])
    hole(bridge,(wrist_length/2,0,3.5),PARAM['m4_clearance_mm'])
    for z in (-14,14):hole(bridge,(wrist_length+7,z,3.5),PARAM['m3_clearance_mm'])
    record('P09_wrist_side_plate',bridge,f'{wrist_length} mm wrist bridge; print two')

    collar=cube('roll carrier',(42,56,26),(0,0,13),mint,2)
    hole(collar,(0,0,13),22.4,40)
    for x in (-14,14):
        for y in (-14,14):hole(collar,(x,y,13),PARAM['m3_clearance_mm'],40)
    for x in (-14,14):hole(collar,(x,0,7),PARAM['m3_clearance_mm'],70,'Y')
    record('P10_roll_carrier',collar,'Generic 22.4 mm bore; final bearing and motor mount unspecified')

    palm=cube('palm',(76,28,12),(0,0,6),shell,2)
    hole(palm,(0,0,6),PARAM['pivot_bore_mm'],30)
    for x in (-14,14):hole(palm,(x,0,6),PARAM['m3_clearance_mm'],30)
    for y in (-7,7):hole(palm,(0,y,6),4.4,100,'X')
    record('P11_gripper_palm',palm,'Concept parallel-gripper palm; transmission and drive not yet designed')

    finger=cube('finger',(48,10,16),(24,5,0),mint,1)
    boolean(finger,cube('grip lip',(12,8,16),(42,0,0),mint,1),'UNION')
    for x in (7,18):hole(finger,(x,5,0),4.4,40,'Y')
    record('P12_gripper_finger',finger,'Mirrored parallel finger; provisional rail and actuator interface')

    # Small test coupon for assessing printed clearances before any arm parts.
    coupon=cube('coupon',(58,26,6),(0,0,3),mint,1)
    for x,d in [(-18,3.4),(-6,4.4),(8,8.4),(23,6.6)]:hole(coupon,(x,0,3),d,20)
    record('P13_clearance_coupon',coupon,'Hole diameters left to right: 3.4, 4.4, 8.4, 6.6 mm')

def assemble():
    report('Assembling the five-joint hierarchy…')
    instance('P01_base_plate')
    instance('P02_motor_housing',loc=(0,0,12))
    ref(cube('REFERENCE | base stepper — 42 mm placeholder',(42,42,40),(0,0,40),dark,2))
    ref(cylinder('REFERENCE | yaw shaft',4,40,(0,0,73),material=steel))
    bearing=cylinder('REFERENCE | yaw bearing',53,3,(0,0,77),material=steel)
    hole(bearing,(0,0,77),96,20)
    ref(bearing)
    angles=PARAM['pose_degrees']
    j1=pivot('JOINT 1 | Base yaw | local Z',None,(0,0,88),'Z',angles[0])
    instance('P03_rotating_deck',j1)
    cheek_offset=PARAM['upper_gap_mm']/2+PARAM['upper_plate_mm']+9
    instance('P04_shoulder_bracket',j1,(0,cheek_offset,0),(math.pi/2,0,0),'right')
    instance('P04_shoulder_bracket',j1,(0,-cheek_offset,0),(math.pi/2,0,math.pi),'left')
    j2=pivot('JOINT 2 | Shoulder pitch | local -Y',j1,(0,0,44),'Y',-angles[1])
    motor(j2,22,PARAM['upper_gap_mm'])
    for y in (PARAM['upper_gap_mm']/2+PARAM['upper_plate_mm'],-PARAM['upper_gap_mm']/2):instance('P05_upper_link_plate',j2,(0,y,0),(math.pi/2,0,0))
    for x in (27,PARAM['upper_arm_mm']-27):instance('P07_upper_spacer',j2,(x,PARAM['upper_gap_mm']/2,0),(math.pi/2,0,0))
    j3=pivot('JOINT 3 | Elbow pitch | local -Y',j2,(PARAM['upper_arm_mm'],0,0),'Y',-angles[2])
    motor(j3,19,PARAM['forearm_gap_mm'])
    for y in (PARAM['forearm_gap_mm']/2+PARAM['forearm_plate_mm'],-PARAM['forearm_gap_mm']/2):instance('P06_forearm_plate',j3,(0,y,0),(math.pi/2,0,0))
    for x in (27,PARAM['forearm_mm']-27):instance('P08_forearm_spacer',j3,(x,PARAM['forearm_gap_mm']/2,0),(math.pi/2,0,0))
    j4=pivot('JOINT 4 | Wrist pitch | local -Y',j3,(PARAM['forearm_mm'],0,0),'Y',-angles[3])
    motor(j4,16,56)
    for y in (35,-28):instance('P09_wrist_side_plate',j4,(0,y,0),(math.pi/2,0,0))
    # The carrier belongs to the wrist; only the shaft, palm and fingers roll.
    instance('P10_roll_carrier',j4,(PARAM['wrist_mm'],0,0),(0,math.pi/2,0))
    j5=pivot('JOINT 5 | Wrist roll | local X',j4,(PARAM['wrist_mm'],0,0),'X',angles[4])
    ref(cylinder('REFERENCE | roll shaft',10,42,(15,0,0),'X',steel),j5)
    instance('P11_gripper_palm',j5,(31,0,0),(math.pi/2,0,math.pi/2))
    opening=PARAM['gripper_opening_mm']
    for sign in (-1,1):
        instance('P12_gripper_finger',j5,(30,sign*(opening/2+4),0),(math.pi if sign<0 else 0,0,0))
    for z in (-7,7):ref(cylinder('REFERENCE | gripper guide',2,88,(37,0,z),'Y',steel),j5)
    source_collection.hide_render=True
    source_collection.hide_viewport=True
    return [j1,j2,j3,j4,j5]

def export_stls():
    report('Exporting grounded part meshes and validating topology…')
    for code,obj in masters.items():
        mesh=obj.data.copy()
        bm=bmesh.new();bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0001)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        nonmanifold=sum(not edge.is_manifold for edge in bm.edges)
        volume=bm.calc_volume(signed=True)
        # Count connected vertex components. Separate shells are not printable parts.
        unseen=set(bm.verts);components=0
        while unseen:
            components+=1;stack=[unseen.pop()]
            while stack:
                for edge in stack.pop().link_edges:
                    for vert in edge.verts:
                        if vert in unseen: unseen.remove(vert);stack.append(vert)
        if nonmanifold or components!=1 or volume<=0:
            raise ValueError(f'{code}: {nonmanifold} non-manifold edges, {components} shells, volume {volume}')
        verts=[v.co for v in bm.verts]
        lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)))
        hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
        offset=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
        with open(STL/(code+'.stl'),'wb') as file:
            file.write(b'EDU05 PROTOTYPE. Units: mm. Hardware fit unverified.'.ljust(80,b' '))
            file.write(struct.pack('<I',len(bm.faces)))
            for face in bm.faces:
                points=[v.co+offset for v in face.verts]
                file.write(struct.pack('<12fH',*face.normal,*points[0],*points[1],*points[2],0))
        dims=list(hi-lo)
        quantity=sum(c==code for c,_ in instances)
        part_report.append({'part_id':code,'quantity':quantity if quantity else 1,'dimensions_mm':[round(v,3) for v in dims],'volume_mm3':round(volume,2),'triangles':len(bm.faces),'nonmanifold_edges':nonmanifold,'connected_components':components,'description':obj['description'],'print_orientation':obj['print_orientation'],'status':'Prototype — motor fit and strength unverified'})
        report(f'{code}: OK, 1 closed shell, {len(bm.faces)} triangles, {tuple(round(d,1) for d in dims)} mm')
        bm.free();bpy.data.meshes.remove(mesh)
    (OUT/'mesh_checks.json').write_text(json.dumps(part_report,indent=2),encoding='utf-8')
    with open(OUT/'parts_list.csv','w',newline='',encoding='utf-8') as file:
        writer=csv.writer(file);writer.writerow(['Part','Quantity','X mm','Y mm','Z mm','Description','Status'])
        for p in part_report:writer.writerow([p['part_id'],p['quantity'],*p['dimensions_mm'],p['description'],p['status']])

def text(name,body,loc,size,rotation=(0,0,0),collection=labels_collection,align='LEFT'):
    data=bpy.data.curves.new(name,'FONT');data.body=body;data.size=size;data.align_x=align;data.extrude=.015
    obj=bpy.data.objects.new(name,data);collection.objects.link(obj);obj.location=loc;obj.rotation_euler=rotation;obj.data.materials.append(text_mat);return obj

def camera_for(scene,loc,target,scale,collection):
    data=bpy.data.cameras.new(scene.name+' camera');data.type='ORTHO';data.ortho_scale=scale;data.clip_end=10000
    cam=bpy.data.objects.new('Camera | '+scene.name,data);collection.objects.link(cam);cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam;return cam

def light(collection,name,loc,power,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def render_settings(scene):
    scene.render.engine='CYCLES'
    scene.cycles.samples=48
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    world=bpy.data.worlds.new(scene.name+' world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.16,.17,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
    scene.view_settings.view_transform='AgX'

def studio(joints):
    report('Creating studio view and joint annotations…')
    ground=cube('Studio floor',(10000,10000,4),(140,0,-5),ground_mat)
    recollect(ground,presentation_collection)
    cam=camera_for(assembly,(740,-940,630),(110,0,150),690,presentation_collection)
    light(presentation_collection,'Key softbox',(0,-350,700),12000000,500,(120,0,150))
    light(presentation_collection,'Rim softbox',(350,280,570),9000000,400,(120,0,150))
    light(presentation_collection,'Fill softbox',(-450,-100,240),4000000,350,(100,0,150))
    bpy.context.view_layer.update()
    # Place labels in camera coordinates so they remain legible in the saved view.
    q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));toward=q@Vector((0,0,1));center=Vector((110,0,150))
    slots=[(-300,-175),(-300,-85),(-300,85),(175,155),(180,-50)]
    names=['J1  BASE YAW','J2  SHOULDER','J3  ELBOW','J4  WRIST PITCH','J5  WRIST ROLL']
    for joint,slot,title in zip(joints,slots,names):
        anchor=center+right*slot[0]+up*slot[1]+toward*500
        label=text('LABEL | '+title,title,anchor,10.5,cam.rotation_euler)
        point=joint.matrix_world.translation.copy()
        end=anchor+right*(112 if slot[0]<0 else -5)-up*3
        curve=bpy.data.curves.new('Leader','CURVE');curve.dimensions='3D';curve.bevel_depth=.35;curve.bevel_resolution=2
        spline=curve.splines.new('POLY');spline.points.add(1);spline.points[0].co=(*point,1);spline.points[1].co=(*end,1)
        obj=bpy.data.objects.new('Leader | '+title,curve);labels_collection.objects.link(obj);curve.materials.append(text_mat)
    text('Title','EDU—05 / ROBOT ARM',center+right*(-300)+up*230+toward*500,17,cam.rotation_euler)
    text('Subtitle','FIVE JOINTS + PARALLEL GRIPPER',center+right*(-300)+up*210+toward*500,7,cam.rotation_euler)
    text('Concept notice','CONCEPT 01   /   MOTOR FIT & LOAD CAPACITY NOT VERIFIED',center+right*(-300)-up*235+toward*500,7,cam.rotation_euler)
    render_settings(assembly)
    # Save a useful material-mode viewport, with the rig ready for selection.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
                area.spaces.active.region_3d.view_distance=650
                area.spaces.active.region_3d.view_location=Vector((110,0,150))
                area.spaces.active.clip_end=10000
                area.spaces.active.shading.type='MATERIAL'
                area.spaces.active.region_3d.view_perspective='CAMERA'
    active(joints[1])

def layout_scene():
    report('Creating separate parts-layout scene…')
    layout=bpy.data.scenes.new('EDU-05 | Parts layout')
    layout.unit_settings.system='METRIC';layout.unit_settings.scale_length=.001;layout.unit_settings.length_unit='MILLIMETERS'
    col=bpy.data.collections.new('Parts | individual masters on display');layout.collection.children.link(col)
    labels=bpy.data.collections.new('Part labels');layout.collection.children.link(labels)
    for index,(code,source) in enumerate(masters.items()):
        column=index%4;row=index//4;x=column*270;y=-row*220
        obj=source.copy();obj.data=source.data.copy();col.objects.link(obj);obj.name=code+' | layout';obj.hide_viewport=False;obj.hide_render=False
        lo=Vector(tuple(min(v.co[i] for v in obj.data.vertices) for i in range(3)));hi=Vector(tuple(max(v.co[i] for v in obj.data.vertices) for i in range(3)))
        obj.location=(x-(lo.x+hi.x)/2,y-(lo.y+hi.y)/2,-lo.z)
        p=next(p for p in part_report if p['part_id']==code)
        text(code+' label',code.replace('_',' ').upper(),(x-118,y-93,1),8,collection=labels)
        text(code+' quantity',f"QTY {p['quantity']}  |  "+' × '.join(str(round(v,1)) for v in p['dimensions_mm'])+' mm',(x-118,y-110,1),6,collection=labels)
    bpy.context.window.scene=layout
    floor=cube('Layout floor',(1180,1030,4),(405,-330,-5),ground_mat);recollect(floor,col)
    text('Layout title','EDU—05 / INDIVIDUAL PROTOTYPE PARTS',(-118,180,1),19,collection=labels)
    text('Layout subtitle','MILLIMETRES   •   HARDWARE FIT UNVERIFIED   •   CLOSED MESHES CHECKED',(-118,150,1),8,collection=labels)
    camera_for(layout,(405,-330,1300),(405,-330,0),1190,col)
    light(col,'Layout softbox',(200,-200,650),16000000,700,(400,-300,0))
    render_settings(layout);layout.render.resolution_y=1450;layout.render.resolution_x=1600
    return layout

try:
    build_parts()
    joints=assemble()
    export_stls()
    studio(joints)
    layout=layout_scene()
    # Embed the editable generator and the project notes in the native file.
    for filename in ('build_robot.py','parameters.json'):
        block=bpy.data.texts.new(filename);block.write((OUT/filename).read_text(encoding='utf-8'))
    notes=bpy.data.texts.new('START HERE — prototype status')
    notes.write('EDU-05 educational arm concept.\nScenes: Assembled and Parts layout.\n13 unique prototype STL meshes, millimetres, one connected closed shell each.\nSelect the five JOINT empties in collection 03 to pose the arm.\nReference hardware is not printable.\nMounts, motor types, bearing fits, transmissions, fasteners and strength are NOT validated.\nDo not treat these files as a finished functional robot.\nStart with P13 clearance coupon; adapt parameters once hardware is measured.\nSee build_robot.py and parameters.json for regeneration.\n')
    bpy.context.window.scene=assembly
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'EDU05_robot_arm_concept.blend'))
    report('Saved Blender assembly. Rendering previews…')
    assembly.render.filepath=str(OUT/'assembled_preview.png')
    bpy.ops.render.render(write_still=True,scene=assembly.name)
    layout.render.filepath=str(OUT/'parts_preview.png')
    bpy.ops.render.render(write_still=True,scene=layout.name)
    bpy.context.window.scene=assembly
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'success':True,'unique_stl_files':len(part_report),'structural_instances':len(instances),'blend_file':'EDU05_robot_arm_concept.blend'},indent=2),encoding='utf-8')
    report('BUILD COMPLETE')
    if (OUT/'BUILD_ERROR.txt').exists(): (OUT/'BUILD_ERROR.txt').unlink()
except Exception:
    report(traceback.format_exc())
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8')
    raise
finally:
    log.close()
