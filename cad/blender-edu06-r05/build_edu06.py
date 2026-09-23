"""Build EDU06 R05 in a separate Blender process. All coordinates in mm.
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

def base():
    say('Building serviceable base, printed plain bearings and 3:1 yaw drive')
    floor=cube('Base floor',(240,190,5),(0,0,2.5),M['green'],2)
    # Rear and side walls form an open-front case. Separate front panel stays removed in scene.
    for dims,loc in [((4,190,85.5),(-118,0,47.25)),((4,190,85.5),(118,0,47.25)),((240,4,85.5),(0,93,47.25))]:union(floor,cube('_wall',dims,loc,bevel=1))
    lidpts=[(-110,-85),(110,-85),(-110,85),(110,85),(0,85)]
    for x,y in lidpts:
        union(floor,cyl('_lid post',7,85.5,(x,y,47.25)))
        hole(floor,(x,y,86),3.4,14);hexhole(floor,(x,y,86.6),5.8,2.8)
        # Side-loaded nuts retain 2 mm of post material above the pocket.
        # A top-open pocket would let the nut pull against only the lid.
        if x:
            inward=1 if x<0 else -1
            boolean(floor,cube('_lid nut side entry',(10,6.4,2.8),(x+inward*5,y,86.6)))
        else:
            boolean(floor,cube('_lid nut side entry',(6.4,10,2.8),(x,y-5,86.6)))
        nut('Base lid side captive M3',None,T(x,y,85.4),M['steel'])
    for x in [-108,108]:
        for y in [-73,73]:hole(floor,(x,y,2.5),4.5,9)
    motorpts=[(32+x,y) for x in (-21,21) for y in (-42.5,15.5)]
    holes(floor,motorpts,2.5)
    # Lower journal support is bolted to four floor holes; separate printable column.
    lowerpts=[(-28+x,y) for x in (-26,26) for y in (-24,24)]
    holes(floor,lowerpts,2.5)
    for y in [-40,-22,-4,14,32]:boolean(floor,cube('_vent',(8,10,22),(118,y,63),bevel=2))
    for x in [-84,-76,-68]:boolean(floor,cube('_cable',(5,9,18),(x,93,26),bevel=1))
    add_part(floor,'B01_open_front_base_240x190',note='4 mm walls, 5 mm floor; four M4 fasteners attach printed feet. External bench attachment must be provided separately. M3 captive nuts in top posts.')
    deck=cube('Deck',(240,190,5),(0,0,92.5),M['green'],2)
    holes(deck,lidpts,92.5);hole(deck,(-28,0,92.5),42.4,12)
    holes(deck,[(-28+x,y) for x,y in pcd(4,36,math.pi/4)],92.5)
    holes(deck,[(32,-15),(32,15)],92.5)
    for x in [62,74,86]:boolean(deck,cube('_vent',(5,42,12),(x,49,92.5),bevel=1))
    add_part(deck,'B02_structural_lid',note='Remove to access drive. Hole Ø42.4 captures upper printed journal bushing.')
    screw_pattern('Base lid M3x12 ',None,T(z=95),lidpts,12)
    front=cube('Front',(230,3,85),(0,0,42.5),M['green'],.8)
    for x in [-103,103]:
        for z in [5,68]:hole(front,(x,0,z),3.4,10,'Y')
    for x in [-55,-40,-25,-10,5,20,35,50]:boolean(front,cube('_vent',(5,12,26),(x,0,39),bevel=.7))
    panel=add_part(front,'B03_service_front_panel',tf=T(28,-140,-6.5)@R('X',90),note='Removable front panel; shown lying in front. Assembly transform: translation(0,-93.5,5) with no rotation.',orient=[90,0,0])
    # Four internal tabs share front panel attachment holes.
    for si,x in enumerate([-103,103]):
        for zi,z in enumerate([10,73]):
            tab=cube('_tab',(22,10,12),(x,-87,z),M['green'],1)
            hole(tab,(x,-87,z),3.4,20,'Y');hexhole(tab,(x,-83.3,z),5.8,2.8,'Y')
            # Support arm reaches fixed side wall without leaving an unconnected island.
            union(tab,cube('_arm',(17,10,12),((-112 if x<0 else 112),-87,z)))
            union(floor,tab)
            bolt('Service panel M3x16',panel,T(x,-1.5,z-5)@R('X',90),16,M['steel'])
            nut('Service tab M3 nut',None,T(x,-82.2,z)@R('X',90),M['steel'])
    L.finish(floor)
    # Lower stand: ring + four columns + foot. No metal bearing.
    stand=ring('_lower stand',27,21.15,8,38,M['green'])
    baseplate=cube('_stand foot',(64,62,5),(0,0,2.5),M['green'],2);hole(baseplate,(0,0,2.5),33,8);union(stand,baseplate)
    pts=[(x,y) for x in [-26,26] for y in [-24,24]]
    for x,y in pts:union(stand,cyl('_post',5,39,(x,y,21.5)))
    # Connect the upper ring to each post using short radial ribs.
    for x,y in pts:union(stand,cube('_rib',(18,17,8),(x*.8,y*.8,42)))
    holes(stand,pts,23)
    hole(stand,(0,0,23),33,50)
    hole(stand,(0,0,42),42.3,8.2)
    add_part(stand,'B05_lower_journal_support',tf=T(-28,0,5),note='Four M3 floor bolts; lower sleeve seat Ø42.3. Printed support carries overturning load.')
    screw_pattern('Lower journal stand M3x55 ',None,T(-28,0,51),pts,55)
    for x,y in pts:nut('Lower journal stand M3nut',None,T(-28+x,y,-2.4),M['steel'])
    lower=ring('_lower sleeve',21,16.25,10,43,M['ivory'])
    union(lower,ring('_flange',26,16.25,2,51,M['ivory']))
    add_part(lower,'B06_replaceable_lower_bushing',tf=T(-28,0,0),note='Ø32.5 running bore for Ø32 shaft. Trial clearance 0.25 radial.')
    upper=ring('_upper sleeve',21,16.25,11,84,M['ivory'])
    union(upper,ring('_thrust flange',45,16.25,3,95,M['ivory']))
    holes(upper,pcd(4,36,math.pi/4),96)
    add_part(upper,'B07_upper_bushing_and_thrust_ring',tf=T(-28,0),note='Replaceable polymer plain bearing, not a ball bearing. Printed thrust surface; friction unmeasured.')
    screw_pattern('Upper bushing M3 ',None,T(-28,0,98),pcd(4,36,math.pi/4),12)
    for x,y in pcd(4,36,math.pi/4):nut('Upper bushing underside M3nut',None,T(-28+x,y,87.6),M['steel'])
    station,j1=L.joint('J1 • base yaw',None,T(-28,0,0),control,'J1',-40,40,HOME['J1'])
    shaft=ring('_shaft',16,7,74,32,M['green'])
    union(shaft,ring('_coupling',31,7,6.5,75,M['green']))
    union(shaft,ring('_thrust collar',32,7,7.7,98.3,M['green']))
    union(shaft,ring('_top flange',38,7,6,106,M['green']))
    holes(shaft,pcd(4,25,math.pi/4),79,3.4,9);holes(shaft,pcd(4,29,math.pi/4),109,3.4,9)
    for x,y in pcd(4,29,math.pi/4):
        # Radial nut entry at Z106.8..109.6 leaves a 2.4 mm load-bearing roof.
        hexhole(shaft,(x,y,108.2),5.8,2.8)
        a=math.atan2(y,x)
        entry=cube('_deck nut radial entry',(12,6.4,2.8),
                   (x+6*math.cos(a),y+6*math.sin(a),108.2))
        entry.rotation_euler[2]=a;boolean(shaft,entry)
    add_part(shaft,'B08_printed_hollow_yaw_shaft',j1,note='Ø32 journal; 14 mm cable bore. Radial gap0.25, axial running allowance0.3. No metal shaft.')
    collar=ring('_yaw clamp',19,16.25,10,32.7,M['green'])
    union(collar,cube('_clamp ears',(12,9,10),(23,0,37.7),M['green']))
    boolean(collar,cube('_split',(16,1,12),(23,0,37.7)))
    hole(collar,(23,0,37.7),3.4,16,'Y');hexhole(collar,(23,3.05,37.7),5.8,3.1,'Y')
    add_part(collar,'B17_split_yaw_retaining_collar',j1,note='Split printed collar under lower sleeve;0.3 axial gap prevents lifting without clamping the bearing.')
    bolt('Yaw collar M3x10',j1,T(23,-4.5,37.7)@R('X',90),10,M['steel'])
    nut('Yaw collar M3nut',j1,T(23,1.7,37.7)@R('X',-90),M['steel'])
    wheel=gear('_yaw60',60,1.5,10,65);hole(wheel,(0,0,70),32.5,14);holes(wheel,pcd(4,25,math.pi/4),70)
    for x,y in pcd(8,36):hole(wheel,(x,y,70),9,14)
    add_part(wheel,'B09_yaw_60T_module1p5',j1,note='60 teeth, pitch Ø90, 20° involute. 60 mm centre distance.')
    for i,(x,y) in enumerate(pcd(4,25,math.pi/4)):
        washer=ring('_yaw gear washer',3.5,1.7,.5,81.5,M['ivory']);add_part(washer,f'B18_yaw_gear_screw_spacer_{i}',j1,T(x,y))
        nut('Yaw gear M3nut',j1,T(x,y,62.6),M['steel'])
    screw_pattern('Yaw gear coupling M3 ',j1,T(z=82),pcd(4,25,math.pi/4),20)
    rotordeck=cube('_rotor deck',(160,108,6),(-23,0,115),M['green'],8)
    hole(rotordeck,(0,0,115),14,10);holes(rotordeck,pcd(4,29,math.pi/4),115)
    footpts=[(x,y) for x in [-76,44] for y in [-20,20]];holes(rotordeck,footpts,115)
    add_part(rotordeck,'B10_rotating_pedestal_deck',j1,note='Structural deck 160×108×6; keyed bolt patterns to yaw flange and shoulder stand.')
    screw_pattern('Deck flange M3x12 ',j1,T(z=118.8),pcd(4,29,math.pi/4),12)
    for i,(x,y) in enumerate(pcd(4,29,math.pi/4)):
        spacer=ring('_deck screw spacer',3.5,1.7,.8,118,M['ivory'])
        add_part(spacer,f'B19_deck_screw_spacer_{i}',j1,T(x,y))
        nut('Deck flange side captive M3',j1,T(x,y,107.0),M['steel'])
    for x,y in footpts:
        bolt('Pedestal to deck M3x25',j1,T(x,y,132),25,M['steel']);nut('Pedestal deck M3nut',j1,T(x,y,109.6),M['steel'])
    motor=make_motor('AX','J1_BASE',None,T(32,0,65),M,attachment_depth=20.05)
    pin=empty('J1 pinion • minus three times yaw',None,T(32,0,65));L.drive(pin,control,'J1','(9-3*q)*pi/180')
    rotating_horn(motor,pin)
    pinion=gear('_pin20',20,1.5,10);holes(pinion,pcd(4,8),5,2.3)
    for x,y in pcd(4,8):hole(pinion,(x,y,8),4.3,8)
    union(pinion,ring('_pinion journal',4,1.7,11,10,M['ivory']))
    hole(pinion,(0,0,.1),6.0,.4)
    add_part(pinion,'B11_yaw_20T_pinion',pin,note='M2×6 through 4 mm counterbore floor into AX horn (2 mm). External printed Ø8 journal support.')
    screw_pattern('J1 horn M2x6 ',pin,T(z=4),pcd(4,8),6,2)
    PAIRS.append({'name':'J1','pinion':pin.name,'wheel':j1.name,**pair_spec(20,60,1.5)})
    # Tall printed pinion journal bracket tied to underside of lid.
    support=ring('_pin support',11,4.25,6,79,M['ivory'])
    for y in [-15,15]:union(support,cube('_ear',(12,10,6),(0,y,82)))
    for y in [-15,15]:union(support,cyl('_leg',4,8,(0,y,86)))
    holes(support,[(0,-15),(0,15)],86)
    add_part(support,'B12_yaw_pinion_journal_support',tf=T(32,0),note='Ø8.5 printed bearing bore; 0.25 mm radial gap. Top ears attach underside deck.')
    for i,y in enumerate([-15,15]):
        washer=ring('_pin support screw spacer',3.5,1.7,1.5,95,M['ivory']);add_part(washer,f'B19_pinion_support_screw_spacer_{i}',tf=T(32,y))
        bolt('Yaw pinion support M3x20',None,T(32,y,96.5),20,M['steel']);nut('Yaw pinion support underside M3nut',None,T(32,y,76.6),M['steel'])
    # Motor floor spacers derive from rear-cap datum, not a guessed motor mounting hole.
    capz=float(motor['rear_cap_back'])+65
    for i,(x,y) in enumerate(motorpts):
        sp=ring('_motor standoff',5,1.7,capz-5,5,M['green']);add_part(sp,f'B13_motor_floor_standoff_{i+1}',tf=T(x,y))
    for i,(x,y) in enumerate([(x,y) for x in [-108,108] for y in [-73,73]]):
        foot=ring('_base foot',12,2.25,8,-8,M['green']);hexhole(foot,(0,0,-6.25),7.3,3.5)
        add_part(foot,f'B15_printed_foot_{i}',tf=T(x,y),note='Printed 8mm foot clears underside motor screw heads; captive M4 nut, no rubber or metal bearing.')
        washer=ring('_anchor stack spacer',5,2.25,3.1,5,M['ivory']);add_part(washer,f'B16_foot_bolt_spacer_{i}',tf=T(x,y))
        bolt('Base foot M4x16',None,T(x,y,8.1),16,M['steel'],4);nut('Base foot M4nut',None,T(x,y,-7.8),M['steel'],4)
    # U2D2 tray — true envelope, separate power entry.
    tray=cube('_tray',(60,30,3),(0,0,1.5),M['green'],2)
    for x in [-26,26]:union(tray,cube('_tray rim',(3,23,8),(x,0,5)))
    for y in [-11.5,11.5]:union(tray,cube('_tray rim',(54,3,7),(0,y,5)))
    holes(tray,[(-27,-11),(-27,11),(27,-11),(27,11)],1.5)
    for x,y in [(-27,-11),(-27,11),(27,-11),(27,11)]:
        hole(tray,(x,y,9),6.2,12)
        hole(floor,(-61+x,-64+y,2.5),3.4,9)
        bolt('U2D2 tray M3x12',None,T(-61+x,-64+y,8),12,M['steel']);nut('U2D2 tray underside M3nut',None,T(-61+x,-64+y,-2.4),M['steel'])
    add_part(tray,'B14_U2D2_tray',tf=T(-61,-64,5),note='Cavity49×20, U2D2 nominal48×18×14.9. USB connector revision must be checked.')
    u=cube('U2D2 USB–TTL converter',(48,18,14.9),(0,0,7.45),M['black'],1.1);reference(u,None,T(-61,-64,8),mass=9,collision=True)
    L.text('U2D2 marking','U2D2',(-61,-65,23.1),4,M['text'])
    L.cable('USB to computer',[(-86,-64,16),(-105,-76,17),(-130,-100,6),(-166,-116,3)],2.3,M['black'])
    for i,mat in enumerate([M['red'],M['black'],M['yellow']]):L.cable('Base TTL loom '+str(i),[(-34,-63+i*2,17),(-18,-69+i*2,18),(52,-59+i*2,32),(48,-24+i*2,42)],.85,mat)
    return j1

def reducer(prefix,parent,tf,prop,ratio,module,home,limits):
    teeth=20*ratio;C=module*(20+teeth)/2;face=12 if prop=='J2' else 10
    # Elbow columns stay above/below the full motor envelope, including its cradle.
    bridge_pts=[(-30,-25),(-30,15)] if prop=='J2' else [(0,-44),(0,21)]
    station,j=L.joint(prop+' • '+('shoulder pitch' if prop=='J2' else 'elbow pitch'),parent,tf,control,prop,*limits,home)
    if prop=='J3':station=empty('J3 fixed gearbox clocked 90deg',station,R('Z',90))
    # Independent printed output pivot carries the link; offset motor drives the teeth.
    jr=12 if prop=='J2' else 10;seat=jr+5;front=25
    for side,z in [('rear',-25),('front',19)]:
        cheek=ring('_bearing cheek',27,jr+5.15,6,z,M['green'])
        # Web to motor mount and pedestal / link attachment, with circular reliefs.
        if side=='rear':
            union(cheek,poly('_curved reducer spine',L.hull_circles([(-C+15,-27,9),(-12,-22,9)]),z,6,M['green']))
            mount_bosses=[(-C+x,y,5.5) for x in [-19.25,19.25] for y in [-39.25,15.25]]+[(-C+x,y,6) for x,y in bridge_pts]
            flange=poly('_sculpted motor mounting web',L.hull_circles(mount_bosses),z,6,M['green'])
            window=cyl('_elliptical motor access',1,9,(-C,-12,z+3));window.scale=(12,17,1);boolean(flange,window)
            union(cheek,flange)
            holes(cheek,[(-C+x,y) for x in [-19.25,19.25] for y in [-39.25,15.25]],z+3)
            holes(cheek,[(-C+x,y) for x,y in bridge_pts],z+3)
            for x,y in bridge_pts:hexhole(cheek,(-C+x,y,-23.7),5.8,3.0)
        # Window respects the motor case envelope where it crosses the front cheek.
        if side=='front':boolean(cheek,cube('_motor clearance',(49,65,12),(-C,-12,z+3),bevel=1))
        holes(cheek,pcd(4,22,math.pi/4),z+3)
        if prop=='J3' and side=='front':
            for x,y in pcd(4,22,math.pi/4):hexhole(cheek,(x,y,23.7),5.8,3.0)
        # Neck stiffness behind bearing and foot attachment at shoulder only.
        if prop=='J2':
            web=poly('_curved pedestal web',L.hull_circles([(-25,-58.5,4.5),(25,-58.5,4.5),(-15,-16,9),(15,-16,9)]),z,6,M['green'])
            relief=cyl('_pedestal oval window',1,8,(0,-43,z+3));relief.scale=(14,8,1);boolean(web,relief);union(cheek,web)
            holes(cheek,pcd(4,22,math.pi/4),z+3)
            holes(cheek,[(-25,-58.5),(25,-58.5)],z+3)
        hole(cheek,(0,0,z+3),2*(jr+5.15),8)
        add_part(cheek,f'{prefix}_01_{side}_support',station,note='Stationary cheek with replaceable polymer journal sleeve; two separate sides carry bending moment.')
    if prop=='J3':
        for i,(x,y) in enumerate(pcd(4,22,math.pi/4)):
            spacer=ring('_elbow cheek tie',3.4,1.7,38,-19,M['green'])
            add_part(spacer,f'E_12_front_cheek_tie_{i}',station,T(x,y),note='38mm stationary tie between bearing cheeks, shared M3x70 through upper-link mount; front nut recessed clear of rotating flange.')
            nut('Elbow front support captive M3',station,T(x,y,22.4),M['steel'])
    for side,z in [('rear',-25),('front',15)]:
        bush=ring('_bush',seat,jr+.25,10,z,M['ivory'])
        union(bush,ring('_lip',seat+2,jr+.25,2,(-19 if side=='rear' else 17),M['ivory']))
        add_part(bush,f'{prefix}_02_{side}_plain_bushing',station,note=f'Printed running bore Ø{2*jr+.5}; journal Ø{2*jr}. Fit coupon first.')
    # Shaft held by rear cap and front flange. Cross-bolted flanges couple to wheel.
    shaft=ring('_output shaft',jr,4,51.3,-25.3,M['green'])
    union(shaft,ring('_flange',25,2.25,6,25.5,M['green']))
    holes(shaft,pcd(4,18,math.pi/4),28.5,3.4,8)
    for x,y in pcd(4,18,math.pi/4):hexhole(shaft,(x,y,26.9),5.8,2.8)
    hexhole(shaft,(0,0,29.3),7.3,4.4)
    add_part(shaft,f'{prefix}_03_independent_output_shaft',j,note='External printed pivot, independent of motor shaft. Shoulder flanges provide axial clearance, not clamped rotating cheeks.')
    cap=ring('_retaining cap',jr+4,2.25,3,-28.3,M['ivory'])
    add_part(cap,f'{prefix}_04_shaft_retainer',j,note='0.3 mm nominal clearance to rear cheek. Central M4 clamp preloads only rotating shaft and cap.')
    washer=ring('_retainer washer',5.5,2.25,1.1,-29.4,M['ivory']);add_part(washer,f'{prefix}_10_retainer_screw_spacer',j)
    bolt(prefix+' M4x60 pivot retainer',j,T(z=-29.4)@R('X',180),60,M['steel'],4)
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
        add_part(foot,f'{prefix}_08_pedestal_foot',station,note='Bears on rotating deck; four matching vertical M3 holes at120×40mm.')
        for x in [-25,25]:
            bolt('Pedestal cheek M3x65',station,T(x,-58.5,31),65,M['steel']);nut('Pedestal cheek M3nut',station,T(x,-58.5,-33.4),M['steel'])
    return station,j,31.5+face

def link(prefix,node,length,outface,distal=True):
    # Root plate couples directly to gear and output flange; large relief permits rear shaft cap.
    root=ring('_root ring',26,13,6,outface,M['green']);holes(root,pcd(4,18,math.pi/4),outface+3)
    beam=poly('_rounded structural link',L.rounded_profile(length-30,36,10,((length+6)/2,0)),outface,24,M['green'])
    boolean(beam,poly('_rounded internal lightening',L.rounded_profile(length-37,29,6.5,((length+6)/2,0)),outface+3.5,17))
    # Root transverse closure and branch overlap make a single solid.
    union(root,beam)
    if distal:
        end=ring('_elbow mount',28,18.5,6,outface,M['green']);end.location.x=length;union(root,end)
        holes(root,[(length+x,y) for x,y in pcd(4,22,math.pi/4)],outface+3)
    # Windows leave continuous corner rails and generous material at both load-transfer ends.
    for x in [length*.43,length*.67]:
        opening=cyl('_oval side window',1,55,(x,0,outface+12),'Y');opening.scale=(8.5,1,5.2);boolean(root,opening)
    add_part(root,prefix+'_hollow_ribbed_link',node,note=f'{length} mm pivot spacing; rounded structural envelope, oval windows and 3.5 mm nominal walls. Continuous top/bottom rails. Orient link flat with layer paths across root.')
    for i,(x,y) in enumerate(pcd(4,18,math.pi/4)):
        spacer=ring('_link screw spacer',3.5,1.7,50.6-(outface+6),outface+6,M['ivory'])
        add_part(spacer,prefix+f'_root_bolt_spacer_{i}',node,T(x,y))
    screw_pattern(prefix+' root M3x25 ',node,T(z=50.6),pcd(4,18,math.pi/4),25)
    return outface+12

def arm(j1):
    say('Building real 5:1 shoulder and 4:1 elbow stages')
    _,j2,f2=reducer('S',j1,T(0,0,186)@R('X',90),'J2',5,1.25,HOME['J2'],(45,90))
    link('A01',j2,100,f2)
    # Reversed elbow gearbox keeps output on the opposite side, reducing cumulative lateral offset.
    elbow_tf=T(100,0,f2-31)@R('X',180)
    _,j3,f3=reducer('E',j2,elbow_tf,'J3',4,1.25,HOME['J3'],(30,75))
    # Attach gearbox rear cheek to upper link with six-millimetre spacers.
    for i,(x,y) in enumerate(pcd(4,22,math.pi/4)):
        sp=ring('_elbow spacer',3.4,1.7,6,f2-6,M['ivory']);add_part(sp,f'A02_elbow_spacer_{i}',j2,T(100+x,y))
        sp=ring('_elbow bolt spacer',3.4,1.7,8.1,f2+6,M['ivory']);add_part(sp,f'A04_elbow_bolt_spacer_{i}',j2,T(100+x,y))
        bolt('Elbow gearbox and front support M3x70',j2,T(100+x,y,f2+14.1),70,M['steel'])
    z=link('A03',j3,85,f3,False)
    # A fixed circular flange replaces the entire old forearm-roll motor.
    mount_tf=T(78.8,0,z)@R('Y',90)
    end=ring('_fixed wrist flange',30,13,10,-10,M['green'])
    for x,y in pcd(4,24):
        hole(end,(x,y,-5),3.4,14)
        hexhole(end,(x,y,-5.35),5.8,2.9)
        a=math.atan2(y,x)
        entry=cube('_radial nut insertion',(12,6.4,2.9),(x+6*math.cos(a),y+6*math.sin(a),-5.35));entry.rotation_euler[2]=a;boolean(end,entry)
        nut('Fixed wrist flange captive M3',j3,mount_tf@T(x,y,-6.8),M['steel'])
    L.bake(end);end.matrix_world=mount_tf
    forearm=next(o for o in L.PRINT if o.name=='A03_hollow_ribbed_link');union(forearm,end);L.finish(forearm)
    forearm['description']='85mm rounded forearm with integral Ø60 circular fixed wrist flange. Front x78.8;10mm axial thickness,Ø26 access, fourM3 on48PCD with radial nut insertion. No forearm-roll motor.'
    from wrist_module import build_wrist
    j5,grip,pair=build_wrist(j3,mount_tf,control,M,HOME)
    PAIRS.append(pair)
    # Fixed-to-moving service loops are visual references, not validated bend-radius sweeps.
    for prop,Ln in [('J2',100),('J3',85)]:
        node=L.JOINTS[prop]
        for i,mat in enumerate([M['black'],M['red'],M['yellow']]):
            L.cable(prop+' service lead '+str(i),[(8,22+i*2,58),(28,26+i*2,71),(Ln-18,25+i*2,71),(Ln+5,19+i*2,50)],.85,mat,node)
    return j5,grip

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
    L.text('Presentation subtitle','5 ARM AXES + POWERED GRIPPER    |    SIX MOTORS / R05',centre+up*212,5.5,M['text'],cam.rotation_euler,col=L.studio)
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
        root=base();arm(root);coupon();animate();bpy.context.view_layer.update()
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
        for fn in ['build_edu06.py','blender_lib.py','motor_models.py','gear_math.py','wrist_module.py','gripper_module.py']:
            tx=bpy.data.texts.new(fn);tx.write((ROOT/fn).read_text(encoding='utf-8'))
        notes=bpy.data.texts.new('START HERE — R05 status and controls');notes.write('EDU06 R05. Geometry in millimetres.\nSelect CONTROL; Custom Properties contain J1…J5 output angles and GRIP clear jaw gap in mm.\nTimeline has a 360-frame kinematic demonstration. Drivers enforce ratios J1 3:1 /J2 5:1 /J3 4:1 /J4 3:1 and opposed linear rack jaws.\nIndividual printable meshes: collection01. Purchased references: collection02, exclude from printing.\nThis file is an engineering prototype. Consult engineering-review.md and validation JSON files; no physical load test or full stress/thermal validation is claimed.\nPrint F01 fit coupon before committing. Filament, horn revision, actual screws and mounting details require physical measurement.\n')
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'EDU06_R05.blend'))
        say('SAVED native .blend. Render in a fresh process to evaluate all joint drivers.')
        (ROOT/'BUILD_COMPLETE.json').write_text(json.dumps({'ok':True,'printed_meshes':len(metrics),'blend':'EDU06_R05.blend'},indent=2));say('BUILD COMPLETE')
    except Exception:
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'BUILD_DEBUG.blend'))
        say(traceback.format_exc());(ROOT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
    finally:log.close()

if __name__=='__main__':run()
