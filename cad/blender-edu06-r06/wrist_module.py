"""Centred fixed-mount pitch-roll prototype, exactly two wrist AX motors. Coordinates mm, separate printed pivots."""
import math,json,bmesh
from pathlib import Path
from mathutils import Matrix
import blender_lib as L
from blender_lib import T,R,cube,cyl,ring,union,hole,hexhole,boolean,part,empty,bolt,nut
from motor_models import make_motor
from gear_math import gear_profile,pair_spec

def pcd(n,r,phase=0):
    return [(r*math.cos(phase+2*math.pi*i/n),r*math.sin(phase+2*math.pi*i/n)) for i in range(n)]

def rounded_rect(w,h,r,cx=0,cy=0):
    pts=[]
    for x,y,start in [(cx+w/2-r,cy-h/2+r,-90),(cx+w/2-r,cy+h/2-r,0),
                      (cx-w/2+r,cy+h/2-r,90),(cx-w/2+r,cy-h/2+r,180)]:
        pts.extend((x+r*math.cos(math.radians(start+i*90/10)),
                    y+r*math.sin(math.radians(start+i*90/10))) for i in range(11))
    return pts

def hull(points):
    pts=sorted(set(points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[];upper=[]
    for p in pts:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]

def rounded_link(a,b,ra,rb=None):
    rb=ra if rb is None else rb
    return hull([(x+r*math.cos(2*math.pi*i/48),y+r*math.sin(2*math.pi*i/48))
                 for x,y,r in [(a[0],a[1],ra),(b[0],b[1],rb)] for i in range(48)])

def yz_profile(name,points,x,depth,mat):
    o=L.poly(name,points,x,depth,mat)
    o.data.transform(Matrix(((0,0,1,0),(1,0,0,0),(0,1,0,0),(0,0,0,1))))
    return o

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
        # Carry sleeve bending directly into all four cradle bolt bosses,
        # rather than relying on the thin front saddle rim alone.
        union(fixed,L.poly('_rounded bearing load rib',rounded_link(
            (math.copysign(21.5,x),-42.5),(math.copysign(21.5,x),15.5),4),-4.85,2.8,mats['green']))
    # The cradle is already parented into the arm. Solve these final Boolean
    # operations at its exact local datum: converting the cutters through a
    # long rotated arm chain introduces float32 seams into coplanar nut seats.
    # Restore the original matrices verbatim; this changes no nominal geometry.
    parent=cradle.parent
    basis=cradle.matrix_basis.copy()
    inverse=cradle.matrix_parent_inverse.copy()
    cradle.parent=None
    cradle.matrix_world=Matrix.Identity(4)
    try:
        union(cradle,fixed)
        for x,y in motor['mounting_points']:
            hole(cradle,(x,y,-20),3.4,50)
            hexhole(cradle,(x,y,motor['front_bezel_front']-1.3),5.8,3.0)
        L.finish(cradle)
    finally:
        cradle.parent=parent
        cradle.matrix_parent_inverse=inverse
        cradle.matrix_basis=basis
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
    D=35.;forward=41.;C=60.;face=8.;wheelz=42.6
    mount=L.empty('WRIST fixed flange datum',parent,tf)
    mount['audit_role']='wrist_fixed_mount'
    mount['interface']='Local+Z tool axis; rear mating faceZ0; front heel faceZ5; fourM3 on48PCD phase0.'
    st4,j4=L.joint('J4 • geared wrist pitch',mount,T(0,0,D)@R('Y',90),control,'J4',-25,25,float(home['J4']))
    # All fixed fork geometry is expressed in pitch-axis coordinates. Local Z is lateral.
    base_x=D-2.5
    fork=cyl('_fork heel',30,5,(base_x,0,0),'X',mats['green'])
    union(fork,yz_profile('_rounded heel spine',rounded_rect(14,72.6,5),base_x-2.5,5,mats['green']))
    # Four axial heel screws mate the stationary forearm flange.
    for side,z in [('left',-36.3),('right',30.3)]:
        cheek=L.poly('_teardrop pitch cheek',rounded_link((0,0),(base_x,0),22,9),z,6,mats['green'])
        hole(cheek,(0,0,z+3),20.5,10)
        hole(cheek,(19,0,z+3),10,10)
        union(fork,cheek)
        if side=='left':
            union(fork,L.poly('_curved rear motor support leg',rounded_link((base_x-10,-2),(base_x-10,-84),5),z,6,mats['green']))
    # Low crossmember joins the motor flange to both fork walls outside the moving bay.
    union(fork,cube('_lower rear motor crossmember',(10,6,36.95),(base_x-10,-84,-17.825),mats['green'],1))
    motorcap=wheelz-44.95
    plate=L.poly('_rounded pitch motor rear plate',rounded_rect(70,54,6,13.5,-C),motorcap-5,5,mats['green'])
    boolean(plate,cube('_motor connector access',(43,26,12),(13.5,-C,motorcap-2.5),bevel=2))
    union(fork,plate)
    # A direct rear-plane rib supports the upper motor flange from the heel.
    # It stays behind the real motor case; the front side is left open.
    union(fork,L.poly('_heel to motor flange rear rib',rounded_link((D-4.2,-23),(D-4.2,-43),4),motorcap-5,5,mats['green']))
    for x,y in [(-15,-91),(50,-91)]:
        union(fork,L.poly('_rounded journal foot attachment',rounded_link((x,-84),(x,y),6),motorcap-5,5,mats['green']))
    boolean(fork,cube('_moving roll clearance',(12,32,12),(-27.5,-31,motorcap-2.5)))
    # Re-cut after all webs, avoiding filled-in mounting holes.
    for x,y in pcd(4,24):hole(fork,(base_x,y,x),3.4,10,'X')
    hole(fork,(base_x,0,0),26,12,'X')
    for z in [-33.3,33.3]:hole(fork,(0,0,z),20.5,6.2)
    # The rear plate follows AX case clocking90deg about its output.
    mp=[(-y,x-C) for x in [-21,21] for y in [15.5,-42.5]]
    holes(fork,mp,motorcap-2.5)
    part(fork,'W02_centred_fixed_pitch_fork',st4,note='Neutral roll/pitch axes intersect on centreline. Side cheeks haveØ20.5 journal bores and6mm bearing length. Motor rear mounting42×58mm pattern rotated90°. Continuous curved printed webs join both cheeks to the fixed forearm flange.')
    for x,y in pcd(4,24):bolt('Fixed wrist flange M3x12',mount,T(x,y,5),12,mats['steel'])
    # Moving motor cradle straddles pitch axis; two removable trunnions avoid a shaft through motor.
    rear=-forward+44.95
    cradle=yz_profile('_rounded moving rear wall',rounded_rect(68,60,8,13.5,0),rear,5,mats['green'])
    boolean(cradle,cube('_connector window',(12,43,28),(rear+2.5,13.5,0),bevel=2))
    for sign in [-1,1]:
        z=sign*27
        disk=cyl('_trunnion seat',13,6,(0,0,z),mat=mats['green'])
        # Upper AX rear-post bosses pass just inside the trunnion-seat corner.
        # Cut the seat before joining its rear wall, preserving the full motor
        # mounting plane while giving Ø9.2 bosses0.4 mm radial clearance.
        boolean(disk,cyl('_motor post clearance',5,40,(0,-15.5,sign*21),'X'))
        union(cradle,disk)
        union(cradle,L.poly('_rounded trunnion web',rounded_rect(rear+18,20,2,(rear+5-13)/2,0),z-3,6,mats['green']))
    # Rear cradle bolts are along tool axis, pitched with the whole moving carrier.
    for y in [-15.5,42.5]:
        for z in [-21,21]:hole(cradle,(rear+2.5,y,z),3.4,12,'X')
    for sign in [-1,1]:
        for x,y in pcd(4,7,math.pi/4):
            hole(cradle,(x,y,sign*27),3.4,14)
            hexhole(cradle,(x,y,sign*25.35),5.8,2.9)
            nt=T(x,y,24.2) if sign>0 else T(x,y,-24.2)@R('X',180)
            nut('J4 trunnion captive M3',j4,nt,mats['steel'])
    # Remove only sub-micron duplicate intersection vertices introduced where
    # the post-clearance cylinders meet the trunnion-seat/rear-wall union.
    bm=bmesh.new();bm.from_mesh(cradle.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.001)
    bmesh.ops.dissolve_limit(bm,angle_limit=.000001,verts=list(bm.verts),edges=list(bm.edges))
    bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method='BEAUTY')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(cradle.data);bm.free()
    part(cradle,'W03_moving_pitch_cradle',j4,note='Two removable side trunnions leave central motor bay open. J5 horn41mm ahead of pitch axis; rear capture plate5mm. Four M3 bolted trunnions per side,14PCD,45°.')
    bm=bmesh.new();bm.from_mesh(cradle.data)
    wires=[e for e in bm.edges if not e.link_faces]
    if wires:bmesh.ops.delete(bm,geom=wires,context='EDGES')
    loose=[v for v in bm.verts if not v.link_edges]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    bm.to_mesh(cradle.data);bm.free()
    for sign in [-1,1]:
        stub=ring('_trunnion shaft',10,2,6.6,30.0,mats['ivory'])
        union(stub,ring('_trunnion flange',22 if sign>0 else 14,2,6,36.6,mats['ivory']))
        holes(stub,pcd(4,7,math.pi/4),35)
        if sign>0:
            holes(stub,pcd(4,16,math.pi/4),38)
            for x,y in pcd(4,16,math.pi/4):hexhole(stub,(x,y,37.95),5.8,2.9)
        tfstub=Matrix.Identity(4) if sign>0 else R('X',180)
        part(stub,'W04_'+('drive' if sign>0 else 'idler')+'_removable_trunnion',j4,tfstub,note='Ø20 journal throughØ20.5 fork bore;0.3mm axial gap. Four M3×20 into moving cradle; flange does not clamp fixed fork.')
        for x,y in pcd(4,7,math.pi/4):bolt('J4 trunnion M3x20',j4,tfstub@T(x,y,42.6),20,mats['steel'])
    wheel=L.poly('_pitch60',gear_profile(60,1.5),wheelz,face,mats['ivory'])
    hole(wheel,(0,0,44.6),8,12)
    holes(wheel,pcd(4,7,math.pi/4),44.6,6.2)
    holes(wheel,pcd(4,16,math.pi/4),44.6)
    for x,y in pcd(4,16,math.pi/4):hole(wheel,(x,y,49.65),6.2,2.1)
    for centre in [0,90,180,270]:
        angles=[math.radians(centre-35+i*70/16) for i in range(17)]
        window=[(39*math.cos(a),39*math.sin(a)) for a in angles]+[(23*math.cos(a),23*math.sin(a)) for a in reversed(angles)]
        boolean(wheel,L.poly('_spoke window',window,wheelz-.2,face+.4))
    part(wheel,'W05_pitch_60T_module1p5',j4,note='60T /20T,20° involute;60mm centres;8mm face. Printed output trunnion carries bending independently from motor horn.')
    for x,y in pcd(4,16,math.pi/4):
        bolt('J4 wheel M3x12',j4,T(x,y,48.6),12,mats['steel']);nut('J4 wheel captive M3',j4,T(x,y,36.8),mats['steel'])
    mt=T(0,-C,wheelz)@R('Z',90)
    motor=make_motor('AX','J4_AX',st4,mt,mats,attachment_depth=5,style='sculpted')
    pin=empty('J4 pinion • minus three times pitch',st4,T(0,-C,wheelz))
    L.drive(pin,control,'J4','(9-3*q)*pi/180');rotate_horn(motor,pin)
    pinion=L.poly('_pitch20',gear_profile(20,1.5),0,face,mats['ivory'])
    holes(pinion,pcd(4,8),4,2.3)
    for x,y in pcd(4,8):hole(pinion,(x,y,6),4.3,4.2)
    union(pinion,ring('_pitch pinion journal',4,1.7,8.5,face,mats['ivory']))
    hole(pinion,(0,0,.1),6.0,.4)
    part(pinion,'W06_pitch_20T_pinion',pin,note='FourM2×6 at16PCD through4mm floor =>2mm horn engagement. ExternalØ8 printed front journal.')
    for x,y in pcd(4,8):bolt('J4 pinion M2x6',pin,T(x,y,4),6,mats['steel'],2)
    # Removable bridge attaches to two extended front cradle posts, outside pinion.
    bridge=ring('_pitch pinion support',9,4.25,5,wheelz+11,mats['green'])
    union(bridge,L.poly('_journal bridge roof',[(-30,-36),(55,-36),(55,-27),(8,7),(-8,7),(-30,-27)],wheelz+11,5,mats['green']))
    for polypts in [[(-20,-28),(-7,-28),(-7,-10),(-18,-16)],[(8,-28),(40,-28),(22,-15),(10,-7)]]:
        boolean(bridge,L.poly('_bridge relief',polypts,wheelz+10.8,5.4))
    for x,y in [(-15,-31),(50,-31)]:
        union(bridge,cyl('_support column',4.5,54.95,(x,y,wheelz-16.475),mat=mats['green']))
        hole(bridge,(x,y,wheelz-10),3.4,100)
    hole(bridge,(0,0,wheelz+13.5),8.5,8)
    part(bridge,'W07_pitch_pinion_journal_bridge',st4,T(0,-C),note='Ø8.5 running bore; two independent columns attach motor rear plate using M3×70 through1 mm foot spacers and1.45 mm head spacers. Install after horn screws.')
    # Bracket foot elevations exactly match motor rear flange front.
    # Columns endZ-1.35; motor flange spans-7.35..-2.35;1mm feet bridge the gap.
    for x,y in [(-15,-31),(50,-31)]:
        hole(fork,(x,y-C,motorcap-2.5),3.4,12)
        sp=ring('_bridge foot spacer',4.5,1.7,1,motorcap,mats['ivory']);part(sp,'W08_pinion_bridge_foot_'+str(x),st4,T(x,y-C))
        # HeadZ60.05 and70mm screw give tipZ-9.95,0.2mm beyond nutZ-9.75.
        spacer=ring('_bridge screw spacer',3.5,1.7,1.45,wheelz+16,mats['ivory']);part(spacer,'W09_bridge_head_spacer_'+str(x),st4,T(x,y-C))
        bolt('J4 pinion bridge M3x70',st4,T(x,y-C,wheelz+17.45),70,mats['steel'])
        nut('J4 bridge underside M3',st4,T(x,y-C,motorcap-7.4),mats['steel'])
    # Case clocked180° puts its larger height above the low pitch-drive motor.
    st5,j5=L.joint('J5 • tool roll',j4,T(-forward,0,0)@R('Y',-90)@R('Z',180),control,'J5',-60,60,float(home['J5']))
    roll_motor=make_motor('AX','J5_AX',st5,Matrix.Identity(4),mats,attachment_depth=5,style='sculpted')
    rotate_horn(roll_motor,j5);supported_roll('W10',st5,j5,roll_motor,mats,gripper_relief=True)
    # The tool frame shares J5 local axis; its XY orientation merely clocks the parallel jaws.
    from gripper_module import build_gripper
    # Open20mm gap behind the palm allows its rear AX cables to turn radially
    # before the roll flange; the roll journal itself remains structurally intact.
    grip=build_gripper(j5,T(0,0,94.45),control,mats,home)
    for i,(x,y) in enumerate(pcd(4,24)):
        post=ring('_open cable service standoff',4.5,1.7,20,23.5,mats['green'])
        part(post,'W12_palm_service_gap_post_'+str(i),j5,T(x,y),note='20mm open axial gap between roll output flange and palm for rear connector cable bends. Four separateOD9posts preserve radial cable exits.')
        sp=ring('_palm screw spacer',3.5,1.7,4,49.5,mats['ivory']);part(sp,'W11_palm_screw_spacer_'+str(i),j5,T(x,y))
        bolt('J5 palm interface M3x35',j5,T(x,y,53.5),35,mats['steel'])
    metadata={'fixed_mount_to_J4_pitch_mm':D,'J4_pitch_to_J5_roll_horn_mm':forward,'J5_roll_to_gripper_horn_mm':94.45,
              'open_palm_cable_service_gap_mm':20,
              'roll_bearing_length_mm':16,'neutral_axis':'Fixed flange local+Z; J4 pitch pivot, J5 roll axis and tool centreline collinear at zero pose',
              'J4':pair_spec(20,60,1.5),'radial_journal_clearance_mm':.25,'nominal_pitch_range_deg':[-25,25],
              'fixed_mount':{'face_z_mm':0,'heel_thickness_mm':5,'pcd_mm':48,'phase_deg':0,'centre_access_diameter_mm':26,
                             'screws':'Four M3x12, under-headZ5, tipZ-7; forearm supplies nutsZ-6.8..-4.4.'},
              'trunnion_to_motor_post_radial_clearance_mm':.4,
              'assembly_sequence':[
                  'Load radial-entry nuts in the forearm flange, then bolt the empty fixed fork to it using four M3x12 from the front. The moving carrier must be absent for straight driver access.',
                  'Assemble the J5 AX, its rear capture plate and supported roll sleeve as a separate moving unit; tighten its rear motor screws before sliding the unit into the fixed fork.',
                  'Insert the assembled moving unit from the front between the fork cheeks; insert removable trunnions from the sides and fasten their four M3x20 screws per side.',
                  'Install the60T pitch wheel and fixed J4 motor/pinion. Tighten rear motor screws from the open back; install the removable outboard pinion bridge last.',
                  'Attach the gripper palm to J5 output flange with the gripper AX absent, then install its front-loaded AX cradle and fingers as described in gripper-design-notes.json.',
                  'Hand-fit printed journals and slide coupons before powered tests; these clearances and load paths are a geometric prototype, not a measured payload rating.']}
    (Path(__file__).parent/'wrist-dimensions.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return j5,grip,{'name':'J4','pinion':pin.name,'wheel':j4.name,**pair_spec(20,60,1.5)}
