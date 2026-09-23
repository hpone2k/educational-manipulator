"""EDU06 R02: enclosure + assembled, driven CAD study. Millimetres throughout.
Every occurrence belongs to a rigid link; transformations follow the joint tree.
This is a geometry study, not proof of printed strength or continuous motor torque.
"""
import json,math,pathlib,importlib.util
import numpy as np
ROOT=pathlib.Path(__file__).parent
# Reuse only mathematical profile primitives, not R01 part dimensions or placements.
source=(ROOT.parent/'solid-edge-edu06/define_design.py').read_text().split('# Print first:')[0]
ns={'__file__':str(ROOT/'unused.py')};exec(source,ns)
circle,poly,rect,hexagon,pcd,gear=[ns[k] for k in ('circle','poly','rect','hexagon','pcd','gear')]
parts=[];items=[];joints=[];connections=[]
def op(z,h,shapes,kind='add',plane=1):return dict(z=z,depth=h,shapes=shapes,kind=kind,plane=plane)
def part(name,ops,notes='',category='prototype'):
 parts.append(dict(name=name,ops=ops,notes=notes,category=category));return name
def T(x=0,y=0,z=0):
 a=np.eye(4);a[:3,3]=[x,y,z];return a
def R(axis,deg):
 a=np.eye(4);c,s=math.cos(math.radians(deg)),math.sin(math.radians(deg))
 if axis=='x':a[:3,:3]=[[1,0,0],[0,c,-s],[0,s,c]]
 if axis=='y':a[:3,:3]=[[c,0,s],[0,1,0],[-s,0,c]]
 if axis=='z':a[:3,:3]=[[c,-s,0],[s,c,0],[0,0,1]]
 return a
def matrix(m):
 m=m.copy();m[:3,3]/=1000;return m.T.flatten().tolist()
def add(p,node='fixed',m=None,label=None):
 name=label or p+'_'+str(len(items)+1);items.append(dict(part=p,node=node,local=(np.eye(4) if m is None else m).tolist(),label=name));return name
def holes(points,d=3.4):return [circle(x,y,d/2) for x,y in points]
def corners(w,h):return [(x,y) for x in (-w/2,w/2) for y in (-h/2,h/2)]
def boltpattern(a,b,points,desc):connections.append(dict(a=a,b=b,centres_mm=points,description=desc))
mount=[(-23,-43),(23,-43),(-23,18),(23,18)]

# Fixed base shell: open at the top; separate lid. Top-access captive nuts.
lidpoints=[(x,y) for x in (-102,102) for y in (-82,82)]+[(0,-82),(0,82)]
floorholes=corners(172,132)
caseops=[op(0,4,[rect(-110,-90,220,180)]+holes(floorholes,6.5)),op(4,88,[rect(-110,-90,220,180),rect(-107,-87,214,174)])]
for x,y in lidpoints:caseops.append(op(4,88,[circle(x,y,7)]))
caseops += [op(84,8,holes(lidpoints),'cut'),op(89.3,2.7,[hexagon(x,y,5.8) for x,y in lidpoints],'cut'),op(16,20,[rect(-91,-92,66,8)],'cut')]
base=part('B01b_open_base_box',caseops,'220x180x92,3mm walls,4mm floor. Six top-loaded M3 nut pockets5.8AFx2.7. Cable opening66x20mm. Anchor holes172x132.')
lid=part('B02c_removable_structural_lid',[op(0,5,[rect(-110,-90,220,180),circle(-20,0,32.3)]+holes(lidpoints)+[circle(-20+s['x'],s['y'],1.7) for s in pcd(4,74,3.4,math.pi/4)]+ [circle(40+s['x'],s['y'],1.7) for s in pcd(4,32,3.4,math.pi/4)] + [rect(x,58,5,20) for x in (-80,-68,-56,-44,-32)])],'6xM3x10 lid screws. Central cartridge clearance64.6, four3.4 holes on74PCD45degree phase; fourpinion-support holes32PCD at40,0.')
add(base,label='FIXED open electronics case');add(lid,m=T(z=92),label='SERVICE removable lid')
boltpattern(base,lid,lidpoints,'Six coaxial M3 lid screws; lid92..97; nuts89.3..92; M3x10 underhead97 ->87; blind bore begins84.')

# Two 61806/6806 bearings: 30x42x7,22mm centre separation.
bh=[(27*math.cos(i*math.pi/2),27*math.sin(i*math.pi/2)) for i in range(4)]
housing=part('B03b_yaw_bearing_cartridge',[op(0,7.15,[circle(0,0,32),circle(0,0,21.1)]+holes(bh)),op(7.15,14.7,[circle(0,0,32),circle(0,0,17.5)]+holes(bh)),op(21.85,7.15,[circle(0,0,32),circle(0,0,21.1)]+holes(bh)),op(18.5,5,[circle(0,0,42),circle(0,0,17.5)]+holes(bh)+pcd(4,74,3.4,math.pi/4)),op(21.85,7.15,[circle(0,0,21.1)],'cut'),op(18.5,5,[circle(60,0,21.5)],'cut')],'Insert bearings from opposite ends then fit caps. Both seats42.20mm; fit coupon required. Flange mates underside of lid87..92. Pinion-hanger clearance notch.')
cap=part('B04_bearing_outer_race_cap',[op(0,2,[circle(0,0,32),circle(0,0,17.5)]+holes(bh))],'Retains outer race only; bore35 clears34mm rotating inner-race collar.')
bear=part('H01_61806_30x42x7',[op(0,7,[circle(0,0,21),circle(0,0,15)])],'Purchased steel61806/6806. Envelope, no balls modelled.','hardware reference')
add(housing,m=T(-20,0,68.5));add(cap,m=T(-20,0,66.5));add(cap,m=T(-20,0,97.5))
add(bear,m=T(-20,0,68.5));add(bear,m=T(-20,0,90.5))
gear60=part('B05_yaw_gear_60T',[op(0,8,[gear(60,1.5,.16),circle(0,0,7)]+pcd(4,22,3.4)+pcd(6,66,10,math.pi/6))],'M1.5,20deg,60 teeth; PD90;20T pinion60mm centre distance. Four through M3 bolts couple to spindle on22PCD.')
spindle=part('B06_hollow_yaw_spindle',[op(0,4,[circle(0,0,17),circle(0,0,7)]+pcd(4,22,3.4)),op(4,29,[circle(0,0,14.925),circle(0,0,7)]+pcd(4,22,3.4)),op(33,3.5,[circle(0,0,17),circle(0,0,7)]+pcd(4,22,3.4)),op(36.5,6,[circle(0,0,35),circle(0,0,7)]+pcd(4,22,3.4)+pcd(4,54,3.4,math.pi/4))],'29.85 journal for30mm bearings. Through cable14mm. Top flange starts101,1.5mm above fixed bearing cap; M3 bolts physically couple gear/shaft.')
add(gear60,'J1',T(z=-50.5));add(spindle,'J1',T(z=-42.5))
# J1 node origin is platform mounting face107mm, rotation around its vertical centreline.

# All motor pods use a removable rear cap and keyed rectangular body supports.
# No invented motor-side hole coordinates. The supplied horns retain their real mounting patterns.
pods={}
for typ,w,h,d,top,front,n in [('AX',32,50,40,11.5,5,4),('XM',28.5,46.5,36.2,11.25,2.2,8)]:
 bottom=top-h
 casing=part('H_'+typ+'_motor_case',[op(-d,d-front,[rect(-w/2,bottom,w,h)])],f'{typ} manufacturer nominal envelope; XM34mm body plus2.2horn protrusion.','motor reference')
 horn=part('H_'+typ+'_motor_horn',[op(-front,front,[circle(0,0,11),circle(0,0,2.5)]+pcd(n,16,2))],'Reference tapped holes shown at nominal2mm; actual revision must match.','motor reference')
 frameops=[op(-front,4,[rect(-28,-49,56,73),circle(0,0,12.2)]+holes(mount))]
 for x,y in mount:frameops.append(op(-d,d-front,[circle(x,y,4.3),circle(x,y,1.7)]))
 # Guide walls outside the motor body, joining the fixed front plate.
 for side in (-1,1):
  x= w/2+.35 if side==1 else -w/2-3.35
  frameops.append(op(-d,d-front,[rect(x,bottom+.5,3,h-1)]))
 frame=part('M_'+typ+'_keyed_cradle',frameops,'Motorcase clearance0.35 each side. Four long M3 throughbolts tie front to rear cap; body retained by front/back shoulders. Direct clamp requires fit coupon and thermal test.')
 back=part('M_'+typ+'_rear_cap',[op(0,6.5,[rect(-28,-49,56,73),rect(-10,bottom+8,20,20)]+holes(mount))],'Removable vented back cap. Same46x61mm mounting centres as front.')
 fops=[op(0,4,[circle(0,0,21),circle(0,0,4)]+pcd(n,16,2.3)+pcd(4,32,3.4,math.pi/4))] if typ=='AX' else [op(0,2.2,[circle(0,0,11),circle(0,0,4)]+pcd(n,16,2.3)),op(2.2,4,[circle(0,0,21),circle(0,0,4)]+pcd(n,16,2.3)+pcd(4,32,3.4,math.pi/4))]
 flange=part('M_'+typ+'_output_flange'+('_b' if typ=='XM' else ''),fops,'AX:M2x6 gives2mm projection. XM:M2x8 with0.3mm washer gives1.5mm projection;2.2mm standoff clears fixed front plate. Outer4M3 on32PCD.')
 pods[typ]=dict(case=casing,horn=horn,frame=frame,back=back,flange=flange,d=d)
def pod(typ,node,m,label):
 p=pods[typ]
 add(p['case'],node,m,label+' motor body');add(p['horn'],node,m,label+' horn reference')
 add(p['frame'],node,m,label+' fixed cradle');add(p['back'],node,m@T(z=-p['d']-6.5),label+' rear cap')
 return p
pod('AX','fixed',T(40,0,56),'J1 base yaw')
pinion=part('B07b_supported_yaw_pinion_20T',[op(0,8,[gear(20,1.5,.16),circle(0,0,4)]+pcd(4,16,2.3)),op(8,2,[circle(0,0,6),circle(0,0,1.7)]),op(10,17.5,[circle(0,0,3.95),circle(0,0,1.7)])],'M1.5 20T. M2x10 gives2mm horn projection through8mm hub.7.9mm upper journal supported in608 bearing; case-bearing alignment requires coupon. Axial retention provided by horn bolts.')
add(pinion,'pinion',T(z=.5))
support=part('B11_pinion_bearing_hanger',[op(0,7,[circle(0,0,21),circle(0,0,11.1)]+pcd(4,32,3.4,math.pi/4)),op(7,10,[circle(0,0,21),circle(0,0,6)]+pcd(4,32,3.4,math.pi/4))],'608seat22.2mm; top face92mateslid. Four through M3 clamp hanger and lower bearing cap to lid; selected boltsM3x30 plusnuts.')
supportcap=part('B12_pinion_bearing_cap',[op(0,2,[circle(0,0,21),circle(0,0,6)]+pcd(4,32,3.4,math.pi/4))],'ID12 clears8mm rotating journal; retains outer race.')
b608=part('H02_608_8x22x7',[op(0,7,[circle(0,0,11),circle(0,0,4)])],'Purchased608 nominal8x22x7.','hardware reference')
add(support,m=T(40,0,75));add(supportcap,m=T(40,0,73));add(b608,m=T(40,0,75))
foot=part('B08_motor_floor_spacer',[op(0,5.5,[circle(0,0,4.3),circle(0,0,1.7)])],'Four5.5mm motor mounting spacers, coaxial with floor holes.')
for x,y in mount:add(foot,m=T(40+x,y,4))
parts[0]['ops']+=[op(0,4,holes([(40+x,y) for x,y in mount]),'cut')]

traypoints=corners(58,26)
tray=part('B09b_U2D2_service_tray',[op(0,3,[rect(-34,-17,68,34)]+holes(traypoints)),op(3,6,[rect(-26,-11,52,22),rect(-24.5,-9.5,49,19)]),op(3,15.9,[circle(0,-13,3.5),circle(0,-13,1.7),circle(0,13,3.5),circle(0,13,1.7)]),op(16.2,2.7,[hexagon(0,-13,5.8),hexagon(0,13,5.8)],'cut')],'U2D2 cavity49x19:0.5mm clearance/side. Strap on matched26mm centres captures twoM3nuts;1mm pad gap above case.')
strap=part('B10_U2D2_retaining_strap',[op(0,2,[rect(-4,-17,8,34)]+holes([(0,-13),(0,13)]))],'Strap uses separate standoffs; foam pad thickness must match actual case. Leave ends open for USB and TTL.')
u2d2=part('H_U2D2_48x18x14p9',[op(0,14.9,[rect(-24,-9,48,18)])],'Manufacturer48x18x14.9mm. Cable connector geometry represented by service clearance, not exact connector revision.','electronics reference')
add(tray,m=T(-55,-57,4));add(u2d2,m=T(-55,-57,7));add(strap,m=T(-55,-57,22.9))
parts[0]['ops'] +=[op(0,4,holes([(-55+x,-57+y) for x,y in traypoints]),'cut')]

# Printed shoulder pedestal: foot and vertical backplate are bolted as a rigid unit.
platform=part('A01_rotating_platform',[op(0,6,[rect(-44,-40,88,80),circle(0,0,7)]+pcd(4,54,3.4,math.pi/4)+holes([(-20,30),(20,30)]))],'Four M3 on54PCD match spindle flange. Two M3 pedestal bolt centres40x0.')
pedestal=part('A02b_shoulder_pedestal',[op(0,6,[rect(-40,-63,80,87)]+holes(mount)),op(6,24,[rect(-40,-63,80,8)]),op(6,20,[poly([[-40,-55],[-32,-55],[-40,-20]])]),op(6,20,[poly([[40,-55],[32,-55],[40,-20]])])],'One-piece backplate, foot and gussets placed outside motor envelope. Two orthogonal M3 mounting holes.')
parts[-1]['ops'].append(op(55,8,holes([(-20,18.7),(20,18.7)]),'cut',3))
add(platform,'J1');add(pedestal,'J1',T(0,48.7,69)@R('x',90))
pod('XM','J1',T(0,0,69)@R('x',90),'J2 shoulder')

# Link plates share an explicit horn flange and four standoffs, not floating motor blocks.
spacer=part('A03_output_spacer_4',[op(0,4,[circle(0,0,3.3),circle(0,0,1.7)])],'Four per output flange; M3 throughbolts. Pin axes matched from one shared PCD definition.')
def output(node,typ):
 add(pods[typ]['flange'],node,label=node+' output flange')
 for s in pcd(4,32,3.4,math.pi/4):add(spacer,node,T(s['x'],s['y'],6.2 if typ=='XM' else 4))
def bone(name,L):
 o=[op(8,4,[circle(0,0,21),circle(0,0,12)]+pcd(4,32,3.4,math.pi/4)),op(8,4,[rect(12,-12,L-24,24)]),op(8,4,[rect(L-28,-49,56,73)]+holes([(L+x,y) for x,y in mount]))]
 o.append(op(8,4,pcd(4,32,3.4,math.pi/4)+holes([(L+x,y) for x,y in mount]),'cut'))
 return part(name,o,'4mm plate. Proximal4M3 on32PCD matches horn flange via4mm standoffs. Distal46x61motor mounting rectangle matches rear cap. Needs sandwich stiffener/strength validation.')
upper=bone('A04b_upper_link_100',100);fore=bone('A05b_forearm_link_85',85)
output('J2','XM');add(upper,'J2',T(z=2.2))
M3=T(100,0,10.2-pods['XM']['d']-6.5)@R('x',180)
pod('XM','J2',M3,'J3 elbow');output('J3','XM');add(fore,'J3',T(z=2.2))

# Wrist brackets: orthogonal motor mounts built as real perpendicular plates.
# Rectangular windows preserve motor rear ventilation; all M3 patterns share mount[].
corner=part('A06b_wrist_right_angle_bracket',[op(0,6,[rect(-28,-49,68,73)]+holes(mount)),op(6,56,[rect(34,-49,6,73)])],'Integral right-angle bracket. Orthogonal46x61mount holes. Wall offset keeps floor screws accessible.')
parts[-1]['ops'].append(op(34,6,holes([(y,34-x) for x,y in mount]),'cut',2))
add(corner,'J3',T(85,0,14.2))
M4=T(85+40+pods['AX']['d']+6.5,0,14.2+34)@R('y',90)
pod('AX','J3',M4,'J4 forearm roll');output('J4','AX')
# Roll-to-pitch conversion: the next bracket follows the flange via same four32PCD holes.
wristbase=part('A07b_wrist_rotor_platform',[op(8,4,[rect(-28,-49,68,73),circle(0,0,12)]+pcd(4,32,3.4,math.pi/4)),op(12,56,[rect(34,-49,6,73)])],'Rigid right-angle output carrier, four proximalM3 holes on32PCD. Orthogonal pod attachment pattern.')
parts[-1]['ops'].append(op(34,6,holes([(y,40-x) for x,y in mount]),'cut',2))
add(wristbase,'J4');M5=T(40+pods['AX']['d']+6.5,0,40)@R('y',90)
pod('AX','J4',M5,'J5 wrist pitch');output('J5','AX')
leftbase=part('A09_left_wrist_rotor_platform',[op(8,4,[rect(-40,-49,68,73),circle(0,0,12)]+pcd(4,32,3.4,math.pi/4)),op(12,56,[rect(-40,-49,6,73)]),op(-40,6,holes([(y,40-x) for x,y in mount]),'cut',2)],'Mirrored bracket places J6 roll axis parallel to J4 at neutral J5; avoids folding tool back along upper link.')
add(leftbase,'J5');M6=T(-40-pods['AX']['d']-6.5,0,40)@R('y',-90)
pod('AX','J5',M6,'J6 tool roll');output('J6','AX')
toolplate=part('A08_tool_mount',[op(8,4,[rect(-28,-49,56,73),circle(0,0,12)]+pcd(4,32,3.4,math.pi/4)+holes(mount))],'Proximal32PCD flange and distal46x61motor cradle pattern.')
add(toolplate,'J6');MG=T(z=12+pods['AX']['d']+6.5)
pod('AX','J6',MG,'G geared gripper')

# Geared gripper: opposed sliding racks with integral fingers; no unmatched jaw bolts.
gp=part('G01_fixed_gripper_guide_plate',[op(-1,4,[rect(-53,-49,106,81),circle(0,0,12.2)]+holes(mount)+holes([(-45,-25),(45,-25),(-45,25),(45,25)])),op(3,7.3,[rect(-53,-31.4,106,8)]+holes([(-45,-25),(45,-25)])),op(3,7.3,[rect(-53,23.4,106,8)]+holes([(-45,25),(45,25)]))],'Fixed via shared motor mount46x61pattern. Guide rails have0.4mm rack-side clearance, cover has0.4mm axial gap.')
pinG=part('G02_gripper_pinion_20T',[op(0,3.5,[circle(0,0,12),circle(0,0,4)]+pcd(4,16,2.3)),op(3.5,6,[gear(20,1.5,.16),circle(0,0,4)]+pcd(4,16,2.3))],'M1.5,20teeth,PD30. M2x12 with1mm washer gives1.5mm AX horn projection. Gear phase9degrees at centred jaw position.')
pitch=math.pi*1.5;th=pitch/2-.16;t=math.tan(math.radians(20));pts=[[-38,-8],[38,-8],[38,-1.875]]
for i in range(7,-8,-1):
 c=i*pitch;pts +=[[c+th/2+1.875*t,-1.875],[c+th/2-1.5*t,1.5],[c-th/2+1.5*t,1.5],[c-th/2-1.875*t,-1.875]]
pts.append([-38,-1.875])
rack=part('G03_integral_rack_and_finger',[op(0,6,[poly(pts)]),op(0,36,[rect(-38,-8,8,8)]),op(30,6,[rect(-38,-8,14,8)])],'Integral rack/finger eliminates unmatched screw interfaces. Stroke is limited in simulation;30mm nominal jaw opening. Finger-pad fit not specified.')
cover=part('G04_guide_cover',[op(0,3,[rect(-53,-49,106,81),rect(-50,-23.4,100,46.8)]+holes([(-45,-25),(45,-25),(-45,25),(45,25)]))],'3mm retaining frame,0.4mm nominal axial clearance. FourM3 screws on90x50.100mm long slot clears entire jaw travel.')
add(gp,'J6',MG);add(cover,'J6',MG@T(z=10.3));add(pinG,'Gpinion');add(rack,'jawL');add(rack,'jawR')

# Shared transformation tree. Values are commanded CAD angles, not live motor commands.
joints=[dict(name='J1',parent='fixed',origin=T(-20,0,107).tolist(),axis='z',home=0,limits=[-45,45],motor='AX12A',ratio=3),dict(name='J2',parent='J1',origin=(T(0,0,69)@R('x',90)).tolist(),axis='z',home=80,limits=[55,105],motor='XM430-W350-T',ratio=1),dict(name='J3',parent='J2',origin=M3.tolist(),axis='z',home=15,limits=[-30,55],motor='XM430-W350-T',ratio=1),dict(name='J4',parent='J3',origin=M4.tolist(),axis='z',home=0,limits=[-60,60],motor='AX12A',ratio=1),dict(name='J5',parent='J4',origin=M5.tolist(),axis='z',home=0,limits=[-45,45],motor='AX12A',ratio=1),dict(name='J6',parent='J5',origin=M6.tolist(),axis='z',home=0,limits=[-60,60],motor='AX12A',ratio=1)]
def frames(q):
 f={'fixed':np.eye(4)}
 for j in joints:f[j['name']]=f[j['parent']]@np.array(j['origin'])@R(j['axis'],q[j['name']])
 f['pinion']=T(40,0,56)@R('z',9-3*q['J1'])
 opening=q.get('grip',60);theta=(60-opening)/2/15*180/math.pi
 f['Gpinion']=f['J6']@MG@R('z',9+theta)
 f['jawL']=f['J6']@MG@T((60-opening)/2,-15,3.9)
 f['jawR']=f['J6']@MG@T(-(60-opening)/2,15,3.9)@R('z',180)
 return f
home={j['name']:j['home'] for j in joints};home['grip']=60
def pose(q):
 f=frames(q);return [dict(part=i['part'],label=i['label'],node=i['node'],matrix=matrix(f[i['node']]@np.array(i['local']))) for i in items]
poses=[dict(name='home',q=home)]
for j in joints:
 for side,v in zip(('min','max'),j['limits']):
  q=home.copy();q[j['name']]=v;poses.append(dict(name=j['name']+'_'+side,q=q))
for v in (45,75):q=home.copy();q['grip']=v;poses.append(dict(name='grip_'+str(v),q=q))
for p in poses:p['placements']=pose(p['q'])
ROOT.joinpath('design.json').write_text(json.dumps(dict(revision='R02',parts=parts,placements=pose(home),items=items,joints=joints,connections=connections,home=home,poses=poses,gripperOrigin=MG.tolist()),indent=2))
ROOT.joinpath('PARTS.csv').write_text('name,category,notes\n'+'\n'.join(','.join('"'+str(p[k]).replace('"','""')+'"' for k in ('name','category','notes')) for p in parts))
print(len(parts),'native parts',len(items),'occurrences',len(poses),'test poses')
