"""Build EDU06 R06 in a separate Blender process. All coordinates in mm.
Never run over a user's unsaved scene; use --background --python.
"""
import sys, math, json, traceback, csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import bpy, bmesh
from mathutils import Matrix, Vector
import blender_lib as L
from blender_lib import T,R,cube,cyl,poly,hole,hexhole,ring,union,boolean,part,reference,empty,bolt,nut
from gear_math import gear_profile,pair_spec
from motor_models import make_motor,MOTOR_UNITS

log=(ROOT/'build.log').open('w',encoding='utf-8',buffering=1)
def say(s):print(s,flush=True);log.write(str(s)+'\n')
scene=L.setup()
M={
 'green':L.material('FDM • deep forest green',(.032,.092,.058),rough=.45,layers=True),
 'ivory':L.material('FDM • warm ivory',(.77,.73,.56),rough=.39,layers=True),
 'black':L.material('DYNAMIXEL • black polymer',(.018,.022,.023),rough=.28),
 'steel':L.material('Purchased screws and nuts',(.32,.36,.38),metal=.85,rough=.24),
 'text':L.material('Light markings',(.76,.9,.83),rough=.6),
 'red':L.material('Cable red',(.45,.025,.018),rough=.33),
 'yellow':L.material('Cable yellow',(.75,.45,.04),rough=.36),
 'floor':L.material('Studio green graphite',(.018,.038,.031),rough=.5)
}
control=empty('CONTROL • angles in degrees — edit custom properties')
control.empty_display_type='CIRCLE';control.empty_display_size=22;control.location=(-125,0,6)
control['README']='Angles animate rigid links and actual gear ratios. Animation is kinematic; not a physical proof of load capacity.'
HOME={'J1':0,'J2':65,'J3':55,'J4':0,'J5':0,'GRIP':45.0}
PAIRS=[];FASTENERS=[]

def pcd(n,r,phase=0):return [(r*math.cos(phase+2*math.pi*i/n),r*math.sin(phase+2*math.pi*i/n)) for i in range(n)]
def holes(o,points,z,d=3.4,depth=300):
    for x,y in points:hole(o,(x,y,z),d,depth)
    return o
def gear(name,n,m,thickness,z=0,phase=0):
    points=gear_profile(n,m)
    if phase:
        a=math.radians(phase);points=[(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)) for x,y in points]
    return poly(name,points,z,thickness,M['ivory'])
def screw_pattern(name,node,tf,pts,length,diam=3):
    for i,(x,y) in enumerate(pts):bolt(name+str(i+1),node,tf@T(x,y),length,M['steel'],diam)
    FASTENERS.append({'joint':name,'size':'M'+str(diam),'length_mm':length,'count':len(pts),'note':'Length includes engagement; confirm actual nut/screw stock before printing.'})
def add_part(o,name,node=None,tf=None,note='',orient=None):return part(o,name,node,tf,note,orient)
def rotating_horn(motor,node):
    horn=motor['horn'];horn.parent=node;horn.matrix_parent_inverse=Matrix.Identity(4);horn.matrix_basis=Matrix.Identity(4);horn['rigid_group']=node.name

def reducer(prefix,parent,tf,prop,ratio,module,home,limits):
    teeth=20*ratio;C=module*(20+teeth)/2;face=12 if prop=='J2' else 10
    # Elbow columns stay above/below the full motor envelope, including its cradle.
    bridge_pts=[(-30,-25),(-30,15)] if prop=='J2' else [(0,-44),(0,21)]
    station,j=L.joint(prop+' • '+('shoulder pitch' if prop=='J2' else 'elbow pitch'),parent,tf,control,prop,*limits,home)
    if prop=='J3':station=empty('J3 fixed gearbox clocked 90deg',station,R('Z',90))
    # Independent printed output pivot carries the link; offset motor drives the teeth.
    rail_inner=54.5 if prop=='J2' else 41.5
    key_af=20 if prop=='J2' else 17
    elbow_ears=[(-40,-60),(-12,-68)] # RZ90 gearbox coordinates; unclocked datum (60,-40),(68,-12)
    jr=12 if prop=='J2' else 10;seat=jr+5;front=25
    for side,z in [('rear',-25),('front',19)]:
        from reducer_cheek import make_reducer_cheek
        cheek=make_reducer_cheek(prop,side,z,C,bridge_pts,elbow_ears,M['green'])
        add_part(cheek,f'{prefix}_01_{side}_support',station,note='Stationary cheek with replaceable polymer journal sleeve; two separate sides carry bending moment.')
    if prop=='J3':
        for i,(x,y) in enumerate(pcd(4,22,math.pi/4)):
            spacer=ring('_elbow cheek tie',3.4,1.7,38,-19,M['green'])
            add_part(spacer,f'E_12_front_cheek_tie_{i}',station,T(x,y),note='38mm stationary tie between bearing cheeks. M3x50 head is flush with rear cheek; nut recessed clear of rotating flange.')
            # New independent cheek tie: original mounting bolt no longer crosses moving link plates.
            bolt('Elbow cheek tie M3x50',station,T(x,y,-25)@R('X',180),50,M['steel'])
            nut('Elbow front support captive M3',station,T(x,y,22.4),M['steel'])
    for side,z in [('rear',-25),('front',15)]:
        bush=ring('_bush',seat,jr+.25,10,z,M['ivory'])
        union(bush,ring('_lip',seat+2,jr+.25,2,(-19 if side=='rear' else 17),M['ivory']))
        add_part(bush,f'{prefix}_02_{side}_plain_bushing',station,note=f'Printed running bore Ø{2*jr+.5}; journal Ø{2*jr}. Fit coupon first.')
    # Shaft held by rear cap and front flange. Cross-bolted flanges couple to wheel.
    shaft=ring('_output shaft',jr,4,51.3,-25.3,M['green'])
    key_start=-rail_inner+4.2
    key=cyl('_positive hex drive',key_af/math.sqrt(3),-25.1-key_start,(0,0,(key_start-25.1)/2),mat=M['green'],n=6)
    hole(key,(0,0,(key_start-25.1)/2),4.5,60);union(shaft,key)
    union(shaft,ring('_flange',25,2.25,6,25.5,M['green']))
    holes(shaft,pcd(4,18,math.pi/4),28.5,3.4,8)
    for x,y in pcd(4,18,math.pi/4):hexhole(shaft,(x,y,26.9),5.8,2.8)
    hexhole(shaft,(0,0,29.3),7.3,4.4)
    add_part(shaft,f'{prefix}_03_independent_output_shaft',j,note='External printed pivot, independent of motor shaft. Shoulder flanges provide axial clearance, not clamped rotating cheeks.')
    cap=ring('_bilateral rear keyed flange',26,2.25,6,-rail_inner,M['green'])
    union(cap,ring('_flange neck',jr+4,2.25,rail_inner-30.3,-rail_inner+5,M['green']))
    hexhole(cap,(0,0,(-rail_inner+4-25.1)/2),key_af+.4,rail_inner-29.1)
    holes(cap,pcd(4,18,math.pi/4),-rail_inner+3,3.4,9)
    for x,y in pcd(4,18,math.pi/4):
        hexhole(cap,(x,y,-rail_inner+4.4),5.8,2.8)
        a=math.atan2(y,x)
        slot=cube('_rear flange radial nut insertion',(16,6.7,2.8),(x+8*math.cos(a),y+8*math.sin(a),-rail_inner+4.4))
        slot.rotation_euler[2]=a;boolean(cap,slot)
    add_part(cap,f'{prefix}_04_shaft_retainer',j,note=f'Positively keyed rear output flange; male hex{key_af}AF/female{key_af+.4}AF. Supports second link plate. 0.3mm axial clearance at stationary cheek. Fit and torsion testing required.')
    retain_length=90 if prop=='J2' else 80
    retain_head=30.5-retain_length
    washer=ring('_retainer washer',5.5,2.25,-rail_inner-retain_head,retain_head,M['ivory']);add_part(washer,f'{prefix}_10_retainer_screw_spacer',j)
    bolt(prefix+f' M4x{retain_length} pivot retainer',j,T(z=retain_head)@R('X',180),retain_length,M['steel'],4)
    nut(prefix+' M4 pivot captive nut',j,T(z=27.3),M['steel'],4)
    for x,y in pcd(4,18,math.pi/4):nut(prefix+' output M3 captive',j,T(x,y,25.7),M['steel'])
    wheel=gear('_wheel',teeth,module,face,31.5);hole(wheel,(0,0,36),8,face+8)
    holes(wheel,pcd(4,18,math.pi/4),36)
    if teeth>=60:
        outer=teeth*module/2-7.5
        for centre in [0,90,180,270]:
            angles=[math.radians(centre-35+i*70/20) for i in range(21)]
            pts=[(outer*math.cos(a),outer*math.sin(a)) for a in angles]+[(25*math.cos(a),25*math.sin(a)) for a in reversed(angles)]
            boolean(wheel,poly('_spoke opening',pts,31.3,face+.4))
    add_part(wheel,f'{prefix}_05_output_{teeth}T',j,note=f'{ratio}:1 reduction, module{module}, 20 degree pressure angle, pitch diameter{teeth*module}.')
    # Motor centre is left of output by C, at the SAME gear-face plane.
    motor=make_motor('XM',prefix+'_XM',station,T(-C,0,31.5),M,attachment_depth=15.35,style='sculpted')
    for i,(x,y) in enumerate(motor['mounting_points']):
        spacer=ring('_mount spacer',4.1,1.7,9.35,-19,M['green'])
        add_part(spacer,f'{prefix}_09_motor_mount_standoff_{i}',station,T(-C+x,y),note='9.35mm rear support gap; shared coaxial M3 mounting stack.')
    pin=empty(prop+' motor/pinion rotation',station,T(-C,0,31.5));L.drive(pin,control,prop,f'(9-{ratio}*q)*pi/180')
    rotating_horn(motor,pin)
    p=gear('_pinion',20,module,face);holes(p,pcd(8,8),face/2,2.3)
    for x,y in pcd(8,8):hole(p,(x,y,(face+4.5)/2),4.1,face-4.5+.02)
    union(p,ring('_journal',4,1.7,10,face,M['ivory']))
    hole(p,(0,0,1.2),8.5,2.6)
    hole(p,(0,0,2.45),5.0,5.1)
    add_part(p,f'{prefix}_06_XM_pinion_20T',pin,note='Eight M2×6 with 4.5 mm floor =1.5 mm nominal engagement into XM horn. Check screw length.')
    screw_pattern(prefix+' XM horn M2x6 ',pin,T(z=4.5),pcd(8,8),6,2)
    PAIRS.append({'name':prop,'pinion':pin.name,'wheel':j.name,**pair_spec(20,teeth,module)})
    # Front outboard journal for pinion: no bending load is deliberately sent to servo horn.
    hz=31.5+face+2
    outline=L.hull_circles([(0,0,10)]+[(x,y,6) for x,y in bridge_pts])
    hanger=poly('_pinion bridge',outline,hz,6,M['ivory'])
    hole(hanger,(0,0,hz+3),8.5,9)
    for x,y in bridge_pts:
        union(hanger,cyl('_support leg',5,hz+20,(x,y,(hz-18)/2),mat=M['green']))
        hole(hanger,(x,y,10),3.4,100)
    add_part(hanger,f'{prefix}_07_pinion_journal_bridge',station,T(-C,0),note='External Ø8.5 polymer bearing; two long legs lie outside both gear sweeps and bolt to rear support plate.')
    length=5*math.ceil((hz+6+24.9)/5);head=length-24.9
    for i,(x,y) in enumerate(bridge_pts):
        spacer=ring('_bridge fastener spacer',3.5,1.7,head-(hz+6),hz+6,M['ivory'])
        add_part(spacer,f'{prefix}_11_bridge_screw_spacer_{i}',station,T(-C+x,y))
        bolt(prefix+' bridge M3x'+str(length),station,T(-C+x,y,head),length,M['steel']);nut(prefix+' bridge M3nut',station,T(-C+x,y,-24.8),M['steel'])
    if prop=='J2':
        foot=cube('_pedestal foot',(152,14,62),(-24,-61,0),M['green'],2)
        for x in [-76,44]:
            for z in [-20,20]:hole(foot,(x,-61,z),3.4,18,'Y')
        # Attach cheeks with transverse bolts; no fused hidden metal bracket.
        for x in [-25,25]:hole(foot,(x,-58.5,0),3.4,80)
        for zc in [-22,22]:boolean(foot,cube('_cheek seating slot',(92,9.4,6.4),(0,-58.5,zc)))
        hole(foot,(0,-61,0),16,18,'Y')
        add_part(foot,f'{prefix}_08_pedestal_foot',station,note='Bears on rotating deck; four matching vertical M3 holes at120×40mm. CentralØ16vertical cable passage continues hollow yaw shaft through the pedestal.')
        for x in [-25,25]:
            bolt('Pedestal cheek M3x65',station,T(x,-58.5,31),65,M['steel']);nut('Pedestal cheek M3nut',station,T(x,-58.5,-33.4),M['steel'])
    return station,j,31.5+face

def coupon():
    c=cube('_fit coupon',(92,46,5),(0,0,2.5),M['ivory'],2)
    for x,d in [(-32,3.2),(-21,3.4),(-10,3.6),(3,8.3),(17,8.5),(33,8.7)]:hole(c,(x,-6,2.5),d,8)
    for x,af in [(-30,5.6),(-15,5.8),(0,6.0)]:hexhole(c,(x,12,3.6),af,2.8)
    o=add_part(c,'F01_hole_and_nut_coupon',tf=T(-172,38,2),note='Print first. Ø3.2/3.4/3.6; Ø8.3/8.5/8.7; nut5.6/5.8/6.0AF. Not structural.')
    o.hide_render=True
    for kind,n in [('AX',4),('XM',8)]:
        test=ring('_horn coupon',13,4,4 if kind=='AX' else 4.5,0,M['ivory']);holes(test,pcd(n,8),2,2.3)
        o=add_part(test,'F02_'+kind+'_16PCD_horn_coupon',tf=T(-172,70+(0 if kind=='AX' else 32),2),note=f'{n} M2 clearances2.3 on16PCD. Verify against supplied horn using M2x6. Not structural.');o.hide_render=True

def animate():
    scene.frame_start=1;scene.frame_end=360;scene.render.fps=30
    poses=[(1,HOME),(60,{**HOME,'J1':28}),(110,{**HOME,'J1':-28}), (155,{**HOME,'J2':77,'J3':66}),(200,{**HOME,'J4':18,'J5':30}),(245,{**HOME,'J5':35,'GRIP':20.0}),(300,{**HOME,'J4':-18,'J5':-25,'GRIP':70.0}),(360,HOME)]
    for frame,pose in poses:
        for key,value in pose.items():control[key]=float(value);control.keyframe_insert(data_path='["'+key+'"]',frame=frame)
    for frame,pose in poses:scene.timeline_markers.new('HOME' if frame in (1,360) else 'POSE '+str(frame),frame=frame)
    scene.frame_set(1)

def presentation():
    say('Preparing physical materials, studio lighting and saved inspection cameras')
    floor=cube('Studio floor',(4000,4000,4),(0,0,-10),M['floor']);L.recollect(floor,L.studio)
    bpy.ops.object.camera_add(location=(720,-980,650));cam=bpy.context.object;cam.name='CAMERA • hero assembly';L.recollect(cam,L.studio)
    target=Vector((115,0,220));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=690;cam.data.clip_end=6000;scene.camera=cam
    for name,loc,energy,size,color in [('Key',(-200,-500,850),13000000,650,(.85,1,.92)),('Rim',(200,550,720),20000000,520,(.65,.9,.82)),('Warm',(600,-100,480),8000000,420,(1,.82,.62)),('Base fill',(-300,-350,130),2500000,300,(.72,.85,1))]:
        d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);L.studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector((60,0,160))-o.location).to_track_quat('-Z','Y').to_euler()
    world=bpy.data.worlds.new('Dark green studio world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.18,.15,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
    scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    # Label board as 3D text beside base (real geometry, separate from printable parts).
    right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0));toward=cam.rotation_euler.to_matrix()@Vector((0,0,1))
    centre=target+toward*380
    title=L.text('Presentation title','EDU06 / POLYMER ROBOT',centre+up*232,14,M['text'],cam.rotation_euler,col=L.studio)
    L.text('Presentation subtitle','5 ARM AXES + POWERED GRIPPER    |    SIX MOTORS / R06',centre+up*212,5.5,M['text'],cam.rotation_euler,col=L.studio)
    L.text('Presentation note','PRINTED STRUCTURE • PRINTED PLAIN BEARINGS • OFFICIAL ROBOTIS MOTOR CAD',centre-up*240,5.1,M['text'],cam.rotation_euler,col=L.studio)
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                a.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion();a.spaces.active.region_3d.view_distance=700;a.spaces.active.region_3d.view_location=target
                a.spaces.active.clip_end=6000;a.spaces.active.shading.type='MATERIAL'
    L.active(control)

def run():
    for name in ['BUILD_COMPLETE.json','BUILD_ERROR.txt']:(ROOT/name).unlink(missing_ok=True)
    try:
        from base_module import build_base
        from arm_module import build_arm
        global BASE_ROOT
        BASE_ROOT=build_base(sys.modules[__name__]);build_arm(sys.modules[__name__]);coupon()
        from wiring_module import build_wiring
        build_wiring(sys.modules[__name__])
        animate();bpy.context.view_layer.update()
        (ROOT/'gear-pairs.json').write_text(json.dumps(PAIRS,indent=2));(ROOT/'fasteners.json').write_text(json.dumps(FASTENERS,indent=2))
        (ROOT/'motor-interface-schedule.json').write_text(json.dumps(MOTOR_UNITS,indent=2))
        counts={kind:sum(unit['kind']==kind for unit in MOTOR_UNITS) for kind in ['AX','XM']}
        assert counts=={'AX':4,'XM':2}, f'Expected exactly4 AX and2 XM motors, got {counts}'
        bom={}
        for o in L.REFS:
            if 'fastener_kind' not in o:continue
            key=(o['fastener_kind'],float(o['nominal_diameter_mm']),float(o.get('under_head_length_mm',0)))
            if key not in bom:bom[key]={'kind':key[0],'diameter_mm':key[1],'length_mm':key[2] or None,'quantity':0,'instances':[]}
            bom[key]['quantity']+=1;bom[key]['instances'].append(o.name)
        (ROOT/'hardware-bom.json').write_text(json.dumps(list(bom.values()),indent=2))
        presentation()
        metrics=L.export_parts()
        say(f'Exported {len(metrics)} printable meshes. Nonmanifold parts: '+str([p['id'] for p in metrics if p['nonmanifold_edges']]))
        for fn in ['build_edu06.py','blender_lib.py','motor_models.py','gear_math.py','wrist_module.py','gripper_module.py','base_module.py','arm_module.py','wiring_module.py','base_wiring_guides.py','upper_link_wiring_guides.py','wrist_wiring_guides.py','gripper_wiring_guides.py','reducer_cheek.py','palm_profile.py']:
            tx=bpy.data.texts.new(fn);tx.write((ROOT/fn).read_text(encoding='utf-8'))
        notes=bpy.data.texts.new('START HERE — R06 status and controls');notes.write('EDU06 R06. Geometry in millimetres.\nSelect CONTROL; Custom Properties contain J1…J5 output angles and GRIP clear jaw gap in mm.\nTimeline has a 360-frame kinematic demonstration. Drivers enforce ratios J1 3:1 /J2 5:1 /J3 4:1 /J4 3:1 and opposed linear rack jaws.\nIndividual printable meshes: collection01. Purchased references: collection02, exclude from printing.\nThis file is an engineering prototype. Consult engineering-review.md and validation JSON files; no physical load test or full stress/thermal validation is claimed.\nPrint F01 fit coupon before committing. Filament, horn revision, actual screws and mounting details require physical measurement.\n')
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'EDU06_R06.blend'))
        say('SAVED native .blend. Render in a fresh process to evaluate all joint drivers.')
        (ROOT/'BUILD_COMPLETE.json').write_text(json.dumps({'ok':True,'printed_meshes':len(metrics),'blend':'EDU06_R06.blend'},indent=2));say('BUILD COMPLETE')
    except Exception:
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'BUILD_DEBUG.blend'))
        say(traceback.format_exc());(ROOT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
    finally:log.close()

if __name__=='__main__':run()
