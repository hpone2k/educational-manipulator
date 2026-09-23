"""EDU06 R04: captured parallel-rack gripper, dimensions in millimetres.

Local +Z is the AX output axis. The installed horn front is Z0; the rear palm
interface is Z-50.95. GRIP is the actual gap between the flat pad contact lands.
Only build_gripper imports Blender, so the tooth/clearance math is testable alone.
"""
import json
import math
from pathlib import Path
from gear_math import gear_profile, polygons_overlap, transform_polygon

MIN_GAP, MAX_GAP, HOME_GAP = 20.0, 70.0, 45.0
MODULE, TEETH, PITCH_RADIUS, BACKLASH = 1.5, 20, 15.0, .20
REAR_FACE, PALM_FRONT = -50.95, -44.95
JAW_HOME = 31.5
TOOL_TIP_Z, CONTACT_Z = 100.0, 30.0
END_Y, FRAME_END_Y = 56.35, 60.35


def rack_profile():
    """Right rack: teeth face -X and the rack translates along +Y."""
    pitch = math.pi * MODULE
    root, tip = PITCH_RADIUS + 1.25 * MODULE, PITCH_RADIUS - MODULE
    half_pitch = pitch / 4 - BACKLASH / 4
    hr = half_pitch + 1.25 * MODULE * math.tan(math.radians(20))
    ht = half_pitch - MODULE * math.tan(math.radians(20))
    points = [(24, -30.5), (root, -30.5)]
    for k in range(-6, 8):
        y = (k + .5) * pitch
        points.extend([(root, y-hr), (tip, y-ht), (tip, y+ht), (root, y+hr)])
    points.extend([(root, 39.5), (24, 39.5)])
    return points


def math_check():
    gear, rack = gear_profile(TEETH, MODULE, BACKLASH), rack_profile()
    penetrations = []
    for index in range(101):
        gap = MIN_GAP + (MAX_GAP-MIN_GAP) * index / 100
        travel = (gap-HOME_GAP)/2
        pinion = transform_polygon(gear, travel/PITCH_RADIUS)
        right = transform_polygon(rack, centre=(0, travel))
        left = transform_polygon(rack, math.pi, (0, -travel))
        if polygons_overlap(pinion, right) or polygons_overlap(pinion, left):
            penetrations.append(gap)
        assert abs((JAW_HOME+travel-9)*2-gap) < 1e-9
        assert JAW_HOME+travel-8 >= 10.65+.35-1e-8
        assert JAW_HOME+travel+8 <= 52.35-.35+1e-8
    bad_phase = polygons_overlap(transform_polygon(gear, math.pi/TEETH), rack)
    assert bad_phase, 'Negative control did not catch a half-tooth phase error'
    assert not penetrations, penetrations
    return {
        'tested_gaps':101, 'gap_range_mm':[MIN_GAP,MAX_GAP],
        'tooth_polygon_penetrations':penetrations,
        'negative_control_overlap_detected':bad_phase,
        'pinion_teeth':TEETH,'module_mm':MODULE,'pressure_angle_deg':20,
        'pitch_radius_mm':PITCH_RADIUS,'total_mesh_backlash_mm':BACKLASH,
        'pinion_radians':'(GRIP - 45) / 30',
        'right_carriage_y_mm':'(GRIP - 45) / 2',
        'left_carriage_y_mm':'-(GRIP - 45) / 2',
        'ax_total_angle_range_deg':math.degrees((MAX_GAP-MIN_GAP)/30),
        'nominal_commanded_end_stop_clearance_mm':.35,
        'slide_vertical_clearance_each_face_mm':.35,
        'rack_backbone_to_slide_upright_clearance_mm':.35,
        'opposite_rack_to_crossbar_axial_gap_mm':5,
        'cradle_front_to_fixed_guide_back_clearance_mm':2.35,
        'scope':'Analytical polygon interference and nominal dimensions only; no printed friction, strength or motor-load validation.'
    }


def build_gripper(parent, tf, control, mats, HOME=None):
    import bpy, bmesh
    from mathutils import Matrix
    import blender_lib as L
    from motor_models import make_motor

    green, ivory, steel = mats['green'], mats['ivory'], mats['steel']
    fixed = L.empty('GRIPPER', parent, tf)
    fixed['datum'] = 'AX installed horn front; +Z toward fingers; palm back Z-50.95 mm'
    fixed['audit_role'] = 'gripper_fixed_datum'
    gap_home = float((HOME or {}).get('GRIP', HOME_GAP))
    if not MIN_GAP <= gap_home <= MAX_GAP:
        gap_home = HOME_GAP
    control['GRIP'] = gap_home
    control.id_properties_ui('GRIP').update(min=MIN_GAP,max=MAX_GAP,
        soft_min=MIN_GAP,soft_max=MAX_GAP,
        description='Parallel jaw clear opening at flat pad lands, in mm')
    right = L.empty('GRIP right jaw carriage', fixed)
    left = L.empty('GRIP left jaw carriage', fixed, L.R('Z',180))
    pinion_node = L.empty('GRIP pinion rotation', fixed)
    pinion_node['audit_role'] = 'grip_pinion'
    pinion_node['kinematic_expression'] = '(GRIP-45)/30 radians'
    L.drive(pinion_node,control,'GRIP','(q-45)/30')
    for node, direction in ((right,1),(left,-1)):
        d=node.driver_add('location',1).driver;d.type='SCRIPTED'
        v=d.variables.new();v.name='q';v.type='SINGLE_PROP'
        v.targets[0].id=control;v.targets[0].data_path='["GRIP"]'
        d.expression=('' if direction==1 else '-')+'(q-45)/2'
        node['travel_axis']='LOCAL ASSEMBLY Y'
        node['gap_range_mm']=[MIN_GAP,MAX_GAP]
    # This DOF is linear, so it is intentionally absent from angular L.JOINTS.

    motor=make_motor('AX','GRIP',fixed,Matrix.Identity(4),mats,attachment_depth=6,
                     front_fasteners=True)
    motor['horn'].parent=pinion_node
    motor['horn'].matrix_parent_inverse=Matrix.Identity(4)
    motor['horn'].matrix_basis=Matrix.Identity(4)
    motor['horn']['rigid_group']=pinion_node.name

    def part(o,code,node=fixed,note='',orient=None):
        o=L.part(o,code,node,note=note,orient=orient)
        # Exact Booleans can leave wire-only remnants on a cutter boundary.
        # Removing geometry with no faces changes no printable surface.
        bm=bmesh.new();bm.from_mesh(o.data)
        wires=[e for e in bm.edges if not e.link_faces]
        if wires:bmesh.ops.delete(bm,geom=wires,context='EDGES')
        loose=[v for v in bm.verts if not v.link_edges]
        if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
        bm.to_mesh(o.data);bm.free()
        return o
    def box(name,size,loc,mat=green):
        return L.cube(name,size,loc,mat)
    def bores(o,points,z,depth,d=3.4):
        for x,y in points:L.hole(o,(x,y,z),d,depth)
    def washer(code,x,y,z,height,node=fixed,ro=3.5):
        w=L.cyl(code,ro,height,(x,y,z+height/2),mat=ivory,n=40)
        L.hole(w,(x,y,z+height/2),3.4,height+2)
        return part(w,code,node,note='Printed axial stack spacer; 3.4 mm M3 clearance bore.')
    end_points=[(x,y) for x in (-32,32) for y in (-END_Y,END_Y)]
    motor_points=[(x,y) for x in (-21,21) for y in (15.5,-42.5)]
    interface=[(24,0),(0,24),(-24,0),(0,-24)]

    # Four-mm open frame/ribs; only the real bolted interfaces retain6 mm.
    palm=box('rear palm perimeter',(74,122.7,4),(0,0,-48.95))
    L.boolean(palm,box('_open perimeter',(66,114.7,8),(0,0,-48.95)))
    L.union(palm,L.cyl('central access rim',17,4,(0,0,-48.95),mat=green))
    L.union(palm,box('interface cross rib X',(58,10,4),(0,0,-48.95)))
    L.union(palm,box('interface cross rib Y',(10,58,4),(0,0,-48.95)))
    for sx in (-1,1):
        L.union(palm,box('motor mounting rib',(7,67.2,4),(sx*21,-13.5,-48.95)))
        for y_motor,y_corner in [(15.5,END_Y),(-42.5,-END_Y)]:
            ax,ay,bx,by=sx*21,y_motor,sx*32,y_corner
            length=math.hypot(bx-ax,by-ay);nx,ny=-(by-ay)*2/length,(bx-ax)*2/length
            outline=[(ax+nx,ay+ny),(bx+nx,by+ny),(bx-nx,by-ny),(ax-nx,ay-ny)]
            L.union(palm,L.poly('diagonal rear rib',outline,REAR_FACE,4,green))
    for x,y in end_points+motor_points+interface:
        L.union(palm,L.cyl('six mm interface boss',5.5,6,(x,y,-47.95),mat=green,n=48))
    bores(palm,motor_points+interface+end_points,-47.95,10)
    L.hole(palm,(0,0,-47.95),26,10)
    for x,y in motor_points:
        L.hexhole(palm,(x,y,-49.6),5.8,2.9)
        L.nut('GRIP palm AX cradle rear M3 nut',fixed,L.T(x,y,-50.75),steel)
    for x,y in end_points:
        L.hexhole(palm,(x,y,-49.6),5.8,2.9)
        L.nut('GRIP palm M3 captive nut',fixed,L.T(x,y,-50.75),steel)
    part(palm,'G01_Windowed_rear_palm',note='75 x123.7 mm open rear frame,4 mm ribs and6 mm local bolted bosses; rear datum -50.95. Four PCD48 phase-zero M3 interface holes, full6 mm seats and M3x12 interface screws supplied by wrist builder. CentreØ26 driver-access opening. Four AX cradle rear captive nuts accept front-inserted M3x45. Four long frame-tie nut pockets also open rearward.')

    # Fixed guide base lies 2.35 mm in front of the updated AX cradle post tips.
    # Start from one closed frame, not four coplanar rail unions. Positive
    # 0.05 mm overlap of the upper rail prevents coincident internal faces.
    base=box('single guide frame',(74,120.7,3),(0,0,1.8))
    L.boolean(base,box('_frame centre',(48.7,108.7,8),(0,0,1.8)))
    for sy in (-1,1):
        L.boolean(base,box('_end crossbar outer relief',(48.7,3,8),(0,sy*59.85,1.8)))
    for sx in (-1,1):
        upper=box('one piece upper guide',(12.65,120.7,5.75),(sx*30.675,0,6.125))
        for sy in (-1,1):
            L.boolean(upper,box('_open slide bay',(9.6,41.7,8),(sx*29.05,sy*31.5,7.3)))
        L.union(base,upper)
    for sx in (-1,1):
        for sy in (-1,1):
            L.boolean(base,box('_floor bearing-land relief',(3.15,41.7,8),(sx*28.925,sy*31.5,1.8)))
    bores(base,end_points+[(-32,0),(32,0)],5,20)
    part(base,'G02_Captured_slide_lower_frame',note='3 mm guide floor with two3 mm-wide bearing lands under each foot. Rails start X±24.35 to clear rack backbones X±24.00. Guide floor Z3.30; slide foot bottom3.65, top8.65; fixed retaining lips startZ9.00. Central stops endY±10.65; outer stops startY±52.35.')

    for i,(x,y) in enumerate(end_points,1):
        col=L.cyl('frame spacer',5,45.25,(x,y,(-44.95+.3)/2),mat=green,n=48)
        L.hole(col,(x,y,-22),3.4,49)
        part(col,'G03_'+str(i)+'_Rear_frame_standoff',note='45.25 mm long, OD10/ID3.4 printed standoff; clamped by M3x65 between rear palm and retained front rail.')
        washer('G04_'+str(i)+'_Frame_tie_spacer',x,y,12,2.15)
        L.bolt('GRIP frame M3x65 tie '+str(i),fixed,L.T(x,y,14.15),65,steel)
    for side,x in [('R',32.5),('L',-32.5)]:
        cap=box('guide retainer',(9,120.7,3),(x,0,10.5),ivory)
        bores(cap,[(math.copysign(32,x),y) for y in (-END_Y,0,END_Y)],10.5,8)
        part(cap,'G05_'+side+'_Slide_retaining_lip',note='Removable 3 mm printed upper guide; 0.35 mm vertical running clearance over carriage feet. Fixed wall clearance at carriage outer edge0.35 mm.')

    # The outboard journal is printed and retained axially by the real horn screws.
    gear=L.poly('rack pinion',gear_profile(TEETH,MODULE,BACKLASH),0,8,ivory)
    L.union(gear,L.cyl('pinion front journal',4,14.5,(0,0,15.25),mat=ivory))
    L.hole(gear,(0,0,11.25),3.4,26)
    L.hole(gear,(0,0,.10),6.0,.4)  # Stock AX centre screw rises0.045 above horn face.
    for i in range(4):
        a=i*math.pi/2;x,y=8*math.cos(a),8*math.sin(a)
        L.hole(gear,(x,y,4),2.3,12)
        L.hole(gear,(x,y,6.1),4.3,4.2)
        L.bolt('GRIP pinion AX horn M2x6 '+str(i+1),pinion_node,L.T(x,y,4),6,steel,diam=2)
    part(gear,'G06_20T_m1p5_AX_rack_pinion',pinion_node,
        note='20T module1.5,20deg,8 mm face,total tangential backlash0.20. Four M2x6 on16 PCD through4 mm floor leave2 mm horn engagement. Retain supplied centre screw; Ø6x0.3 rear clearance recess. Printed OD8 outboard journal, no added metal bearing.')
    bridge=box('pinion front bridge',(74,8,6),(0,0,18.3),green)
    L.union(bridge,L.cyl('continuous journal boss',7.5,6,(0,0,18.3),mat=green))
    for x in (-32,32):
        L.union(bridge,box('bridge foot',(8,8,3.3),(x,0,13.65)))
    L.hole(bridge,(0,0,18.3),8.5,10)
    bores(bridge,[(-32,0),(32,0)],16,16)
    part(bridge,'G07_Pinion_outboard_journal_bridge',note='Integral OD15 boss containsØ8.5 plain bearing forØ8 journal:0.25 mm radial allowance,3.25 mm bearing wall. Bolted to guide centre blocks, above rack teeth. Hand-fit and wear tests required.')
    for i,x in enumerate((-32,32),1):
        washer('G08_'+str(i)+'_Bridge_screw_spacer',x,0,21.3,.5)
        L.bolt('GRIP bridge M3x25 '+str(i),fixed,L.T(x,0,21.8),25,steel)
        L.nut('GRIP bridge M3 underside nut '+str(i),fixed,L.T(x,0,-2.1),steel)

    for tag,node in [('R',right),('L',left)]:
        c=JAW_HOME
        carriage=L.poly('rack carriage',rack_profile(),0,8,green)
        for sx in (-1,1):
            L.union(carriage,box('slide foot',(9.15,16,5),(sx*28.925,c,6.15)))
            L.union(carriage,box('raised moving upright',(3.15,16,5.6),(sx*25.925,c,11.2)))
        L.union(carriage,box('raised crossbar',(55,16,5),(0,c,15.5)))
        L.union(carriage,box('owned rack riser',(10.125,12,6.5),(21.9375,c,10.75)))
        L.boolean(carriage,box('_crossbar lightening',(18,10,8),(0,c,15.5)))
        for x in (-16,16):
            L.hole(carriage,(x,c,15.5),3.4,12)
            L.hexhole(carriage,(x,c,13.6),5.8,2.8)
            L.nut('GRIP '+tag+' finger root captive M3',node,L.T(x,c,12.4),steel)
        part(carriage,'G09_'+tag+'_Rack_and_raised_slide',node,
            note='14 analytic rack teeth; pitch line X15. Raised crossbar bottomZ13 lets opposite rack pass belowZ8 throughout20–70 mm gap. Captured slide feet run Z3.65..8.65 with0.35 mm each-side vertical allowance.')

        finger=box('finger body',(24,12,75),(0,c,59.5),green)
        L.union(finger,box('finger root flange',(42,16,4),(0,c,20)))
        # Open-back T slot: the pad slides axially from the removable tip cap.
        L.boolean(finger,box('_key neck',(9.6,2.15,73),(0,c-5.425,61.5)))
        L.boolean(finger,box('_key head',(13.6,2.0,73),(0,c-3.65,61.5)))
        # Open rear pocket keeps3 mm wall to the female key and each side.
        # It has no sealed inner shell that could invert STL cavity normals.
        L.boolean(finger,box('_finger rear lightening',(18,6.65,60.5),(0,c+3.675,57.25)))
        for x in (-16,16):
            L.hole(finger,(x,c,20),3.4,12)
            L.bolt('GRIP '+tag+' finger root M3x10',node,L.T(x,c,22),10,steel)
        # Side-loaded tip nut has a3.7mm roof toward the retaining screw head.
        L.hole(finger,(0,c+2,93),3.4,12)
        L.hexhole(finger,(0,c+2,91.9),5.8,2.8)
        L.boolean(finger,box('_tip nut side loading',(6.7,7.5,2.8),(0,c+4.25,91.9)))
        L.nut('GRIP '+tag+' tip cap captive M3',node,L.T(0,c+2,90.7),steel)
        part(finger,'G10_'+tag+'_Long_finger_75x24x12',node,
            note='75 mm finger body (Z22..97),24 mm width,12 mm thickness; keyed replaceable pad. Root flange4 mm with two M3x10 and captive nuts in carriage. Open rear relief leaves3 mm walls behind key and at each side. Tip M3 nut loads through outer-side slot and bears under3.7 mm roof. Print on outer back with key slot up; preview removable supports in open rear pocket and inspect short slot-roof bridges.',orient=[-90,0,0])

        pad=box('replaceable pad',(24,3,71.65),(0,c-7.5,60.825),ivory)
        for z0 in (25,53,82.65):
            L.union(pad,box('pad key neck',(9,1.7,14),(0,c-5.25,z0+7),ivory))
            L.union(pad,box('pad key head',(13,1.5,14),(0,c-3.75,z0+7),ivory))
        groove=L.poly('_shallow V',[(-7*1.3/1.2,c-9.1),(0,c-7.8),(7*1.3/1.2,c-9.1)],35,50)
        L.boolean(pad,groove)
        part(pad,'G11_'+tag+'_Flat_and_V_keyed_contact_pad',node,
            note='3 mm replaceable printed pad; flat lands maintain specified gap. Central14 mm-wide,1.2 mm-deep V overZ35..85 supports round objects.3 mm front pad plus integral T key slides into finger with0.3 mm side allowance; remove tip cap to replace.',orient=[90,0,0])
        cap=box('finger tip cap',(24,15,3),(0,c-1.5,98.5),ivory)
        L.hole(cap,(0,c+2,98.5),3.4,7)
        part(cap,'G12_'+tag+'_Removable_pad_tip_stop',node,
            note='3 mm printed axial pad stop. One M3x10 atX0,Yfinger-centre+2 into side-loaded captive nut. Slide pad from tip only after cap removal;0.35 mm nominal pad endplay.')
        L.bolt('GRIP '+tag+' pad stop M3x10',node,L.T(0,c+2,100),10,steel)
        contact=L.empty('GRIP '+('right' if tag=='R' else 'left')+' contact',node,L.T(0,c-9,CONTACT_Z))
        contact['audit_role']='grip_contact_'+('right' if tag=='R' else 'left')
        contact['datum']='True flat pad land atZ30, outside the shallow V region'

    tip=L.empty('GRIP tool centreline tip',fixed,L.T(0,0,TOOL_TIP_Z))
    tip['audit_role']='tool_centreline'
    tip['datum']='Geometric centreline at printed retaining-cap tip plane; screw heads extend3 mm farther locally.'
    notes={
        'revision':'R04','units':'mm','control_property':'GRIP','home_gap_mm':gap_home,
        'gripper_datum':'AX installed horn front, +Z toward fingers',
        'rear_interface_z_mm':REAR_FACE,'rear_interface_pcd_mm':48,
        'rear_interface_holes_mm':[[x,y] for x,y in interface],
        'rear_interface_screw':'4 x M3x12 from full6 mm palm seats; four captive nuts in J6 flange; wrist builder provides these references',
        'rear_interface_central_access_diameter_mm':26,
        'motor':'Dynamixel AX-12A official STEP reference; mechanically captured with four front-inserted M3x45 into rear-palm nuts',
        'motor_stack':motor['cradle_screw'],
        'finger_body_mm':[24,12,75],'finger_body_z_mm':[22,97],
        'pad_thickness_mm':3,'pad_v_depth_mm':1.2,'tool_tip_z_mm':TOOL_TIP_Z,
        'physical_screw_head_front_z_mm':103,'contact_marker_z_mm':CONTACT_Z,
        'rear_frame_size_xy_mm':[75,123.7],
        'rear_frame_web_thickness_mm':4,'rear_frame_bolted_boss_thickness_mm':6,
        'nodes':{'fixed':fixed.name,'right':right.name,'left':left.name,'pinion':pinion_node.name,'tip':tip.name,
                 'contacts':['GRIP right contact','GRIP left contact']},
        'fasteners_excluding_motor_and_wrist':[
            {'size':'M3x65','qty':4,'purpose':'front-to-rear frame ties','under_head_z':14.15,'tip_z':-50.85,'nut_z':[-50.75,-48.35],'spacer_mm':2.15},
            {'size':'M3x25','qty':2,'purpose':'outboard bearing bridge','under_head_z':21.8,'tip_z':-3.2,'nut_z':[-2.1,.3],'spacer_mm':.5},
            {'size':'M3x10','qty':4,'purpose':'finger root flanges','under_head_z':22,'tip_z':12,'nut_z':[12.4,14.8]},
            {'size':'M3x10','qty':2,'purpose':'removable pad tip stops','under_head_z':100,'tip_z':90,'nut_z':[90.7,93.1]},
            {'size':'M2x6','qty':4,'purpose':'pinion to AX horn','under_head_z':4,'tip_z':-2,'printed_floor_mm':4}
        ],
        'assembly_sequence':[
            'Print a short rail/foot and T-key fit coupon first; the nominal0.35 mm slide and0.3 mm key clearances are not measured printer accuracy.',
            'Insert rear palm frame-tie nuts and motor-cradle nuts before attaching palm to wrist. With AX absent, install four PCD48 interface M3x12 from front with a straight driver; the centreØ26 opening exposes J6 stock-horn M2 screws.',
            'Place AX rear cap, seating shims, motor and front cradle onto the palm fromfront. Tighten four front-inserted M3x45 into palm captive nuts before installing pinion and guide frame. Do not substitute rear-inserted cradle bolts here.',
            'Seat gear on stock horn, retaining its centre screw; install four M2x6. Verify tip does not bottom in actual horn.',
            'Assemble lower frame and standoffs, lower each rack-foot carriage fromabove into its open guide bay before fastening upper retaining lips and journal bridge. Phase pinion angle0 and gap45 as modeled; fixed end stops prevent horizontal insertion from the rail ends.',
            'Install finger root captive nuts, bolt fingers to carriages, slide pads in from tips, and secure printed cap into side-loaded tip nut.',
            'Hand-cycle20–70 mm without motor torque first. No rubbing, axial lock, tooth climbing or wire pinch is acceptable. Then commission current/torque-limited motion and measure actual holding force.'
        ],
        'limitations':['Geometric prototype, not validated payload or fatigue rating.','PLA sliding surfaces require fit and wear trials; no added metal bearings assumed.','Round-object grip depends on measured pad friction and sphere size; no secure grip is claimed from geometry alone.'],
        'math_check':math_check()
    }
    (Path(__file__).resolve().parent/'gripper-design-notes.json').write_text(json.dumps(notes,indent=2))
    return {'fixed':fixed,'right':right,'left':left,'pinion':pinion_node,'motor':motor,
            'tip':tip,'metadata':notes,'tool_tip_z_mm':TOOL_TIP_Z,
            'jaw_nodes':[right,left],'contact_names':notes['nodes']['contacts']}


if __name__=='__main__':
    result=math_check()
    out=Path(__file__).resolve().parent/'gripper-math-check.json'
    out.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
