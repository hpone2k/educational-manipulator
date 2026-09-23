"""Centred roll-pitch-roll prototype. Coordinates mm, separate printed pivots."""
import math,json
from pathlib import Path
from mathutils import Matrix
import blender_lib as L
from blender_lib import T,R,cube,cyl,ring,union,hole,hexhole,boolean,part,empty,bolt,nut
from motor_models import make_motor
from gear_math import gear_profile,pair_spec

def pcd(n,r,phase=0):
    return [(r*math.cos(phase+2*math.pi*i/n),r*math.sin(phase+2*math.pi*i/n)) for i in range(n)]

def holes(o,pts,z,d=3.4,depth=100):
    for x,y in pts:hole(o,(x,y,z),d,depth)

def rotate_horn(motor,node):
    h=motor['horn'];h.parent=node;h.matrix_parent_inverse=Matrix.Identity(4);h.matrix_basis=Matrix.Identity(4);h['rigid_group']=node.name

def supported_roll(prefix,station,joint,motor,mats,gripper_relief=False):
    """Outer polymer sleeve transfers bending around the motor's output horn."""
    cradle=motor['cradle']
    fixed=ring('_annular roll sleeve',24,20.25,16,2,mats['green'])
    for x in [-25,25]:
        union(fixed,cyl('_support strut',4,21.5,(x,0,7.25),mat=mats['green']))
        union(fixed,cube('_cradle bridge',(10,12,2.8),(math.copysign(21.5,x),0,-3.45),mats['green']))
    # Integrated into the fixed cradle: no unsupported bearing floating in space.
    union(cradle,fixed);L.finish(cradle)
    cradle['description']+=' Integral front annular sleeve Ø40.5, sixteen mm bearing length. Polymer fit/friction trial required.'
    rotor=ring('_roll horn plate',20,4,4,0,mats['ivory'])
    union(rotor,ring('_rotating journal',20,16,15,3.5,mats['ivory']))
    union(rotor,ring('_output flange',30,16,5,18.5,mats['ivory']))
    for x,y in pcd(4,23,math.pi/4):hole(rotor,(x,y,21),9,6)
    holes(rotor,pcd(4,8),2,2.3)
    holes(rotor,pcd(4,24),21)
    for x,y in pcd(4,24):
        hexhole(rotor,(x,y,19.85),5.8,2.9)
        nut(prefix+' output captive M3',joint,T(x,y,18.7),mats['steel'])
    part(rotor,prefix+'_supported_roll_output',joint,note='Ø40 printed journal / Ø40.5 fixed sleeve;0.25 radial,0.5 front axial clearance. Four M2×6 on16PCD engage stock horn2mm. Output M3 on48PCD at0°; rear captive nuts.')
    for x,y in pcd(4,8):bolt(prefix+' horn M2x6',joint,T(x,y,4),6,mats['steel'],2)
    return rotor

def build_wrist(parent,tf,control,mats,home):
    D=78.;forward=41.;C=60.;face=8.;wheelz=42.6
    st4,j4=L.joint('J4 • forearm roll',parent,tf,control,'J4',-40,40,float(home['J4']))
    m4=make_motor('AX','J4_AX',st4,Matrix.Identity(4),mats,attachment_depth=6)
    rotate_horn(m4,j4);supported_roll('W01',st4,j4,m4,mats)
    st5,j5=L.joint('J5 • geared wrist pitch',j4,T(0,0,D)@R('Y',90),control,'J5',-25,25,float(home['J5']))
    # All fixed fork geometry is expressed in pitch-axis coordinates. Local Z is lateral.
    base_x=D-26
    fork=cyl('_fork heel',30,5,(base_x,0,0),'X',mats['green'])
    union(fork,cube('_fork heel ears',(5,14,72.6),(base_x,0,0),mats['green']))
    # Four axial heel screws mate the annular J4 output flange.
    for side,z in [('left',-36.3),('right',30.3)]:
        cheek=ring('_pitch cheek',22,10.25,6,z,mats['green']);union(fork,cheek)
        union(fork,cube('_fork rail',(base_x+3,14,6),(base_x/2,0,z+3),mats['green'],1))
        union(fork,cube('_motor support leg',(10,90,6),(base_x-10,-39,z+3),mats['green'],1))
    # Low crossmember joins the motor flange to both fork walls outside the moving bay.
    union(fork,cube('_lower motor crossmember',(10,6,72.6),(base_x-10,-84,0),mats['green'],1))
    motorcap=wheelz-44.95
    plate=cube('_pitch motor rear plate',(80,61,5),(13.5,-C-3.5,motorcap-2.5),mats['green'],1.2)
    boolean(plate,cube('_motor connector access',(43,26,12),(13.5,-C,motorcap-2.5),bevel=2))
    union(fork,plate)
    for x,y in [(-15,-91),(50,-91)]:union(fork,cyl('_journal support foot',6,5,(x,y,motorcap-2.5),mat=mats['green']))
    boolean(fork,cube('_moving roll clearance',(12,32,12),(-27.5,-31,motorcap-2.5)))
    # Re-cut after all webs, avoiding filled-in mounting holes.
    for x,y in pcd(4,24):hole(fork,(base_x,y,x),3.4,10,'X')
    hole(fork,(base_x,0,0),26,12,'X')
    for z in [-33.3,33.3]:hole(fork,(0,0,z),20.5,6.2)
    # The rear plate follows AX case clocking90deg about its output.
    mp=[(-y,x-C) for x in [-21,21] for y in [15.5,-42.5]]
    holes(fork,mp,motorcap-2.5)
    part(fork,'W02_centred_fixed_pitch_fork',st5,note='Neutral roll/pitch axes intersect on centreline. Side cheeks haveØ20.5 journal bores and6mm bearing length. Motor rear mounting42×58mm pattern rotated90°. Continuous printed webs join both cheeks to J4 flange.')
    for x,y in pcd(4,24):bolt('J4 fork M3x10',j4,T(x,y,28.5),10,mats['steel'])
    # Moving motor cradle straddles pitch axis; two removable trunnions avoid a shaft through motor.
    rear=-forward+44.95
    cradle=cube('_moving rear wall',(5,68,60),(rear+2.5,13.5,0),mats['green'])
    boolean(cradle,cube('_connector window',(12,43,28),(rear+2.5,13.5,0),bevel=2))
    for sign in [-1,1]:
        z=sign*27
        disk=cyl('_trunnion seat',13,6,(0,0,z),mat=mats['green'])
        union(cradle,disk)
        union(cradle,cube('_trunnion web',(rear+18,20,6),((rear+5-13)/2,0,z),mats['green']))
    # Rear cradle bolts are along tool axis, pitched with the whole moving carrier.
    for y in [-15.5,42.5]:
        for z in [-21,21]:hole(cradle,(rear+2.5,y,z),3.4,12,'X')
    for sign in [-1,1]:
        for x,y in pcd(4,7,math.pi/4):
            hole(cradle,(x,y,sign*27),3.4,14)
            hexhole(cradle,(x,y,sign*25.35),5.8,2.9)
            nt=T(x,y,24.2) if sign>0 else T(x,y,-24.2)@R('X',180)
            nut('J5 trunnion captive M3',j5,nt,mats['steel'])
    part(cradle,'W03_moving_pitch_cradle',j5,note='Two removable side trunnions leave central motor bay open. J6 horn41mm ahead of pitch axis; rear capture plate5mm. Four M3 bolted trunnions per side,14PCD,45°.')
    for sign in [-1,1]:
        stub=ring('_trunnion shaft',10,2,6.6,30.0,mats['ivory'])
        union(stub,ring('_trunnion flange',22 if sign>0 else 14,2,6,36.6,mats['ivory']))
        holes(stub,pcd(4,7,math.pi/4),35)
        if sign>0:
            holes(stub,pcd(4,16,math.pi/4),38)
            for x,y in pcd(4,16,math.pi/4):hexhole(stub,(x,y,37.95),5.8,2.9)
        tfstub=Matrix.Identity(4) if sign>0 else R('X',180)
        part(stub,'W04_'+('drive' if sign>0 else 'idler')+'_removable_trunnion',j5,tfstub,note='Ø20 journal throughØ20.5 fork bore;0.3mm axial gap. Four M3×20 into moving cradle; flange does not clamp fixed fork.')
        for x,y in pcd(4,7,math.pi/4):bolt('J5 trunnion M3x20',j5,tfstub@T(x,y,42.6),20,mats['steel'])
    wheel=L.poly('_pitch60',gear_profile(60,1.5),wheelz,face,mats['ivory'])
    hole(wheel,(0,0,44.6),8,12)
    holes(wheel,pcd(4,7,math.pi/4),44.6,6.2)
    holes(wheel,pcd(4,16,math.pi/4),44.6)
    for x,y in pcd(4,16,math.pi/4):hole(wheel,(x,y,49.65),6.2,2.1)
    for centre in [0,90,180,270]:
        angles=[math.radians(centre-35+i*70/16) for i in range(17)]
        window=[(39*math.cos(a),39*math.sin(a)) for a in angles]+[(23*math.cos(a),23*math.sin(a)) for a in reversed(angles)]
        boolean(wheel,L.poly('_spoke window',window,wheelz-.2,face+.4))
    part(wheel,'W05_pitch_60T_module1p5',j5,note='60T /20T,20° involute;60mm centres;8mm face. Printed output trunnion carries bending independently from motor horn.')
    for x,y in pcd(4,16,math.pi/4):
        bolt('J5 wheel M3x12',j5,T(x,y,48.6),12,mats['steel']);nut('J5 wheel captive M3',j5,T(x,y,36.8),mats['steel'])
    mt=T(0,-C,wheelz)@R('Z',90)
    motor=make_motor('AX','J5_AX',st5,mt,mats,attachment_depth=5)
    pin=empty('J5 pinion • minus three times pitch',st5,T(0,-C,wheelz))
    L.drive(pin,control,'J5','(9-3*q)*pi/180');rotate_horn(motor,pin)
    pinion=L.poly('_pitch20',gear_profile(20,1.5),0,face,mats['ivory'])
    holes(pinion,pcd(4,8),4,2.3)
    for x,y in pcd(4,8):hole(pinion,(x,y,6),4.3,4.2)
    union(pinion,ring('_pitch pinion journal',4,1.7,8.5,face,mats['ivory']))
    hole(pinion,(0,0,.1),6.0,.4)
    part(pinion,'W06_pitch_20T_pinion',pin,note='FourM2×6 at16PCD through4mm floor =>2mm horn engagement. ExternalØ8 printed front journal.')
    for x,y in pcd(4,8):bolt('J5 pinion M2x6',pin,T(x,y,4),6,mats['steel'],2)
    # Removable bridge attaches to two extended front cradle posts, outside pinion.
    bridge=ring('_pitch pinion support',9,4.25,5,wheelz+11,mats['green'])
    union(bridge,L.poly('_journal bridge roof',[(-30,-36),(55,-36),(55,-27),(8,7),(-8,7),(-30,-27)],wheelz+11,5,mats['green']))
    for polypts in [[(-20,-28),(-7,-28),(-7,-10),(-18,-16)],[(8,-28),(40,-28),(22,-15),(10,-7)]]:
        boolean(bridge,L.poly('_bridge relief',polypts,wheelz+10.8,5.4))
    for x,y in [(-15,-31),(50,-31)]:
        union(bridge,cyl('_support column',4.5,54.95,(x,y,wheelz-16.475),mat=mats['green']))
        hole(bridge,(x,y,wheelz-10),3.4,100)
    hole(bridge,(0,0,wheelz+13.5),8.5,8)
    part(bridge,'W07_pitch_pinion_journal_bridge',st5,T(0,-C),note='Ø8.5 running bore; two independent columns attach motor rear plate using M3×65. Install after horn screws.')
    # Bracket foot elevations exactly match motor rear flange front.
    # Its rear columns terminate at z=-3.35; matching flange spans-9.35..-4.35, use1mm feet below.
    for x,y in [(-15,-31),(50,-31)]:
        hole(fork,(x,y-C,motorcap-2.5),3.4,12)
        sp=ring('_bridge foot spacer',4.5,1.7,1,motorcap,mats['ivory']);part(sp,'W08_pinion_bridge_foot_'+str(x),st5,T(x,y-C))
        # Upper head plane56.6 gives65mm screw down to-8.4; external nut below flange requireslonger.
        spacer=ring('_bridge screw spacer',3.5,1.7,1.45,wheelz+16,mats['ivory']);part(spacer,'W09_bridge_head_spacer_'+str(x),st5,T(x,y-C))
        bolt('J5 pinion bridge M3x70',st5,T(x,y-C,wheelz+17.45),70,mats['steel'])
        nut('J5 bridge underside M3',st5,T(x,y-C,motorcap-7.4),mats['steel'])
    # Case clocked180° puts its larger height above the low pitch-drive motor.
    st6,j6=L.joint('J6 • tool roll',j5,T(-forward,0,0)@R('Y',-90)@R('Z',180),control,'J6',-60,60,float(home['J6']))
    m6=make_motor('AX','J6_AX',st6,Matrix.Identity(4),mats,attachment_depth=5)
    rotate_horn(m6,j6);supported_roll('W10',st6,j6,m6,mats,gripper_relief=True)
    # The tool frame shares J6 local axis; its XY orientation merely clocks the parallel jaws.
    from gripper_module import build_gripper
    grip=build_gripper(j6,T(0,0,74.45),control,mats,home)
    for i,(x,y) in enumerate(pcd(4,24)):
        sp=ring('_palm screw spacer',3.5,1.7,1,29.5,mats['ivory']);part(sp,'W11_palm_screw_spacer_'+str(i),j6,T(x,y))
        bolt('J6 palm interface M3x12',j6,T(x,y,30.5),12,mats['steel'])
    metadata={'J4_to_J5_mm':D,'J5_to_J6_horn_mm':forward,'J6_to_gripper_horn_mm':74.45,'roll_bearing_length_mm':16,'neutral_axis':'J4 local+Z; all wrist and tool centres collinear','J5':pair_spec(20,60,1.5),'radial_journal_clearance_mm':.25,'nominal_pitch_range_deg':[-25,25]}
    (Path(__file__).parent/'wrist-dimensions.json').write_text(json.dumps(metadata,indent=2))
    return j6,grip,{'name':'J5','pinion':pin.name,'wheel':j5.name,**pair_spec(20,60,1.5)}
