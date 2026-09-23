"""EDU06 R01 dimensional development model. All inputs in millimetres.
Not a manufacturing release. Rebuilds definitions, not existing native parts.
"""
import json, math, pathlib
ROOT=pathlib.Path(__file__).parent
parts=[]; placements=[]
def circle(x,y,r): return dict(type='circle',x=x,y=y,r=r)
def poly(pts): return dict(type='poly',points=pts)
def rect(x,y,w,h):return poly([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])
def hexagon(x,y,af):return poly([[x+af/math.sqrt(3)*math.cos(i*math.pi/3),y+af/math.sqrt(3)*math.sin(i*math.pi/3)] for i in range(6)])
def pcd(n,d,hole,phase=0):return [circle(d/2*math.cos(phase+2*math.pi*i/n),d/2*math.sin(phase+2*math.pi*i/n),hole/2) for i in range(n)]
def op(depth,shapes,z=0,label=''):return dict(depth=depth,z=z,shapes=shapes,label=label)
def part(name,ops,notes='',category='development print'):
 parts.append(dict(name=name,ops=ops,notes=notes,category=category));return name
def place(p,pos,rot=(0,0,0),label=''):placements.append(dict(part=p,position=pos,rotation=rot,label=label or p))
def capsule(L,r):
 return poly([[L+r*math.cos(-math.pi/2+i*math.pi/24),r*math.sin(-math.pi/2+i*math.pi/24)] for i in range(25)]+[[r*math.cos(math.pi/2+i*math.pi/24),r*math.sin(math.pi/2+i*math.pi/24)] for i in range(25)])
def gear(z,m,backlash=.16):
 rp=z*m/2;rb=rp*math.cos(math.radians(20));ra=rp+m;rr=rp-1.25*m
 inv=lambda r: math.sqrt(max(0,(r/rb)**2-1))-math.acos(min(1,rb/r))
 half=math.pi/(2*z)-backlash/(2*rp);ip=inv(rp);pts=[]
 for i in range(z):
  c=2*math.pi*i/z
  a0=half+ip-inv(max(rr,rb));at=half+ip-inv(ra)
  seq=[(rr,c-math.pi/z),(rr,c-a0)]
  for k in range(7):
   r=max(rr,rb)+(ra-max(rr,rb))*k/6;seq.append((r,c-(half+ip-inv(r))))
  for k in range(1,4):seq.append((ra,c-at+2*at*k/3))
  for k in range(5,-1,-1):
   r=max(rr,rb)+(ra-max(rr,rb))*k/6;seq.append((r,c+(half+ip-inv(r))))
  seq.append((rr,c+a0))
  for r,a in seq:
   q=[r*math.cos(a),r*math.sin(a)]
   if not pts or math.dist(q,pts[-1])>1e-7:pts.append(q)
 return poly(pts)

# Print first: exact nominal centres; only clearances are varied.
coupon=part('C01_clearance_and_M3_nut_coupon',[op(1.5,[rect(0,0,82,36)]+[circle(8+i*10,9,d/2) for i,d in enumerate([2.2,2.3,2.4,2.7,2.8,2.9,3.3,3.4])]+[circle(x,26,1.7) for x in (12,32,52,72)]),op(2.7,[rect(0,0,82,36)]+[circle(8+i*10,9,d/2) for i,d in enumerate([2.2,2.3,2.4,2.7,2.8,2.9,3.3,3.4])]+[hexagon(x,26,af) for x,af in zip((12,32,52,72),(5.6,5.7,5.8,5.9))],1.5)],'Hole row left to right: 2.2,2.3,2.4,2.7,2.8,2.9,3.3,3.4. Nut AF row:5.6,5.7,5.8,5.9. Nut pocket depth2.7.','fit coupon')
axhorn=part('P01_AX_horn_adapter',[op(4,[circle(0,0,17),circle(0,0,4)]+pcd(4,16,2.3)+pcd(4,26,3.4,math.pi/4))],'Four M2 clearance holes on16PCD. Verify screw engagement <=4mm and actual horn.','fit coupon')
xmhorn=part('P02_XM_horn_adapter',[op(4,[circle(0,0,17),circle(0,0,4)]+pcd(8,16,2.3)+pcd(4,26,3.4,math.pi/4))],'Eight M2 clearance holes on16PCD. Inspected horn depth2mm maximum; verify actual horn.','fit coupon')
xmplate=part('P03_XM_side_mount_coupon',[op(4,[rect(-12,-19,24,38)]+[circle(x,y,1.4) for x in (-6,6) for y in (-12,12)])],'12x24mm local pattern. NOT centred on output axis. M2.5 max3mm engagement.','fit coupon')
axplate=part('P04_AX_body_mount_plate',[op(4,[rect(-20,-8,40,47)]+[circle(x,y,1.15) for x in (-13.5,13.5) for y in (6.5,14.5,22.5,30.5)]+[circle(x,-3,1.7) for x in (-14,14)])],'AX frame nut/bolt mounting; verify body revision and access. Output axis local0,0. Motor extends y=-11.5..38.5.')
base=part('P05_base_plate',[op(5,[rect(-100,-90,200,180),circle(0,0,22)]+[circle(x,y,3.25) for x in (-85,85) for y in (-75,75)]+pcd(8,140,1.7*2)+[circle(x,y,15) for x in (-67,67) for y in (-48,48)])],'200x180x5. Anchor6.5dia,170x150pattern. 140PCD is modular plate pattern, NOT a selected turntable bearing pattern.')
turn=part('P06_turntable_interface_ring_PROVISIONAL',[op(6,[circle(0,0,80),circle(0,0,30)]+pcd(8,140,3.4)+pcd(6,80,3.4))],'Bearing unselected. This is a modular interface plate, not a raceway. Do not print for fit until bearing chosen.')
basegear=part('P07_base_gear_60T_M2',[op(8,[gear(60,2),circle(0,0,30)]+pcd(6,80,3.4)+pcd(6,99,12,math.pi/6))],'20degree involute, module2,60teeth; PD120; mesh80mm with20T. Backlash0.16 per gear at pitch. Root transition not strength-validated.')
g20=part('P08_base_pinion_20T_M2',[op(8,[gear(20,2),circle(0,0,4.1)]+pcd(4,16,2.3))],'PD40; separate shaft bearing support required; coupling/hub retention not released.')
g80=part('P09_shoulder_gear_80T_M1p5',[op(8,[gear(80,1.5),circle(0,0,4.1)]+pcd(4,32,3.4)+pcd(6,80,25,math.pi/6))],'4:1 with20T,75mm centres.8.2bore requires shaft/coupling design; not a friction-fit torque connection.')
g40=part('P10_elbow_gear_40T_M1p5',[op(8,[gear(40,1.5),circle(0,0,4.1)]+pcd(4,32,3.4)+pcd(4,44,7,math.pi/4))],'2:1 with20T,45mmcentres; hub/shaft retention pending.')
g20xm=part('P11_XM_pinion_20T_M1p5',[op(8,[gear(20,1.5),circle(0,0,4.1)]+pcd(8,16,2.3))],'PD30; independent pinion bearing support and screw access must be detailed.')
cheek=part('P12_shoulder_bearing_cheek',[op(6,[poly([[-60,-75],[48,-75],[48,15],[28,30],[-30,30],[-60,0]]),circle(0,0,11.1),circle(-45,-60,4.1)]+[circle(x,-64,1.7) for x in (-25,25)]+[circle(x,-24,1.7) for x in (-25,25)])],'Trial608seat22.2dia. Gear shaft/split bearing retention pending. Not a validated shoulder housing.')
upper=part('P13_upper_link_cheek_120',[op(4,[capsule(120,19),circle(0,0,4.1),circle(120,0,11.1),rect(27,-10,66,20)]+[circle(x,y,1.7) for x in (16,104) for y in (-12,12)])],'120mm exact pivot spacing. Requires two cheeks, four cross ties and skins. Drive flange fastening remains a release gate.')
fore=part('P14_forearm_cheek_100',[op(4,[capsule(100,19),circle(0,0,4.1),circle(100,0,4.1),rect(27,-10,46,20)]+[circle(x,y,1.7) for x in (16,84) for y in (-12,12)])],'100mm pivot spacing; trial wrist interface not fully resolved.')
tie=part('P15_cross_tie_50',[op(50,[rect(-6,-8,12,16),circle(0,0,1.7)])],'M3 throughbolt and two end washers; no printed structural thread.')
skin120=part('P16_upper_box_skin',[op(2.4,[rect(16,-25,88,50)]+[circle(x,y,1.7) for x in (22,98) for y in (-19,19)])],'Skin closure fastening must be detailed; current placement is development geometry.')
skin100=part('P17_forearm_box_skin',[op(2.4,[rect(16,-25,68,50)]+[circle(x,y,1.7) for x in (22,78) for y in (-19,19)])],'Development closure panel.')
bearing=part('R03_608_bearing_REFERENCE',[op(7,[circle(0,0,11),circle(0,0,4)])],'Purchased6088x22x7 envelope only; not selection/approval.','purchased reference; do not print')
ax=part('R01_AX12A_body_REFERENCE',[op(40,[rect(-16,-38.5,32,50)])],'Exact nominal body envelope32x50x40; connectors/horn/case details omitted.','motor envelope; do not print')
xm=part('R02_XM430_body_REFERENCE',[op(34,[rect(-14.25,-35.25,28.5,46.5)])],'Exact nominal body28.5x46.5x34; connector/horn offsets omitted.','motor envelope; do not print')
bridge=part('P18_AX_wrist_bridge',[op(4,[rect(-25,-25,50,50),rect(-16.4,-17,32.8,34)]+[circle(x,y,1.7) for x in (-20,20) for y in (-20,20)])],'Trial motor clearance0.4per side on width. Wrist assembly brackets and clearances pending.')

# Opposed racks; module1.5,20degree,20T pinion. Slider guide dimensions are trial values.
gripplate=part('P19_gripper_base_plate',[op(4,[rect(-46,-28,92,56),circle(0,0,4.5)]+pcd(4,16,2.3)+[circle(x,y,1.7) for x in (-40,40) for y in (-22,22)])],'Separate seventh AX motor. Two opposed racks plus guides. Motor fixed body bracket not yet released.')
grippinion=part('P20_gripper_pinion_20T_M1p5',[op(6,[gear(20,1.5),circle(0,0,4.1)]+pcd(4,16,2.3))],'Pitch radius15mm; nominal rack pitch lines30mm apart;0.16mm tooth backlash per gear.')
pitch=math.pi*1.5;th=pitch/2-.16;tan=math.tan(math.radians(20));rackpts=[[-38,-6],[38,-6],[38,-1.875]]
for i in range(7,-8,-1):
 c=i*pitch
 rackpts.extend([[c+th/2+1.875*tan,-1.875],[c+th/2-1.5*tan,1.5],[c-th/2+1.5*tan,1.5],[c-th/2-1.875*tan,-1.875]])
rackpts.append([-38,-1.875])
rack=part('P21_gripper_rack',[op(6,[poly(rackpts)]+[circle(x,-4,1.2) for x in (-31,31)])],'M1.5 rack. Oppose second rack with180deg rotation. Guide clearance must be coupon-tuned.')
guide=part('P22_gripper_guide_rail',[op(8,[rect(-45,-4,90,8)]+[circle(x,0,1.7) for x in (-40,40)])],'Trial rail; retained sliders need cover/spacer stack verification.')
finger=part('P23_gripper_finger',[op(6,[poly([[0,0],[12,0],[12,40],[25,40],[25,48],[0,48]]),circle(6,8,1.2),circle(6,18,1.2)])],'Rigid prototype jaw. Fastening to rack end needs revised match and pad selection before assembly.')

# Assembly is explicitly a static dimensional layout; it is not a solved mechanism.
place(base,(0,0,0));place(turn,(0,0,14));place(basegear,(0,0,22));place(g20,(80,0,22));place(ax,(80,0,-20))
place(cheek,(0,-30,112),(90,0,0));place(cheek,(0,36,112),(90,0,0))
place(g80,(0,-40,112),(90,0,0));place(g20xm,(-45,-40,52),(90,0,0));place(xm,(-45,14,52),(90,0,0))
# Raised upper link65deg, horizontal forearm. Local2D x along link, localy in sagittal plane.
a=math.radians(65);el=(120*math.cos(a),0,112+120*math.sin(a));end=(el[0]+100,0,el[2])
for y in (-25,29):place(upper,(0,y,112),(90,-65,0))
for t in (16,104):
 for offset in (-12,12):place(tie,(t*math.cos(a)-offset*math.sin(a),25,112+t*math.sin(a)+offset*math.cos(a)),(90,-65,0))
place(g40,(el[0],-40,el[2]),(90,0,0));place(g20xm,(el[0]-45,-40,el[2]),(90,0,0));place(xm,(el[0]-45,12,el[2]),(90,0,0))
for y in (-25,29):place(fore,(el[0],y,el[2]),(90,0,0))
for t in (16,84):
 for offset in (-12,12):place(tie,(el[0]+t,25,el[2]+offset),(90,0,0))
for x,z in ((0,112),(el[0],el[2])):
 for y in (-25,25):place(bearing,(x,y,z),(90,0,0))
# Wrist motor envelopes spaced to avoid visually shrinking servos. Packaging differs from L01 torque study.
place(ax,(end[0],0,end[2]),(0,90,0),label='J4 roll envelope')
place(bridge,(end[0]-5,0,end[2]),(0,90,0))
place(ax,(end[0]+65,20,end[2]),(90,0,0),label='J5 pitch envelope')
place(axplate,(end[0]+65,-24,end[2]),(90,0,0))
place(ax,(end[0]+110,0,end[2]),(0,90,0),label='J6 roll envelope')
place(axhorn,(end[0]+152,0,end[2]),(0,90,0))
place(ax,(end[0]+160,0,end[2]),(0,90,0),label='Gripper motor envelope')
place(gripplate,(end[0]+202,0,end[2]),(0,90,0));place(grippinion,(end[0]+207,0,end[2]),(0,90,0))
place(rack,(end[0]+207,15,end[2]),(0,90,180));place(rack,(end[0]+207,-15,end[2]),(0,90,0))
place(guide,(end[0]+206,24,end[2]),(0,90,0));place(guide,(end[0]+206,-24,end[2]),(0,90,0))
# Separate fit/print layout for components not installed in the static assembly.
ROOT.joinpath('design.json').write_text(json.dumps(dict(parts=parts,placements=placements),indent=2))
ROOT.joinpath('PARTS.csv').write_text('name,category,notes\n'+'\n'.join(','.join('"'+str(p[k]).replace('"','""')+'"' for k in ('name','category','notes')) for p in parts))
print(len(parts),'unique parts;',len(placements),'assembly occurrences')
