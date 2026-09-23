"""Dimensioned DYNAMIXEL references and separately printable captured cradles.

All coordinates are millimetres.  Origin is the front face of the installed horn,
with the motor output axis along local +Z; the case height follows local Y.
References reproduce verified envelopes/horn patterns, not vendor STEP detail.
"""
import math, bmesh
from mathutils import Matrix, Euler
import blender_lib as L


MOTOR_UNITS=[]


SPECS = {
    'AX': dict(model='AX-12A', width=32.0, height=50.0, top=11.5,
               case_front=-4.0, case_back=-36.0, rear=-40.0,
               horn_depth=4.0, horn_count=4, horn_pcd=16.0,
               mass=54.6, bezel_back=-3.65, bezel_front=-1.05),
    'XM': dict(model='XM430-W350-T', width=28.5, height=46.5, top=11.25,
               case_front=-2.2, case_back=-36.2, rear=-36.2,
               horn_depth=2.2, horn_count=8, horn_pcd=16.0,
               mass=82.0, bezel_back=-1.85, bezel_front=-.25),
}


def _label(name, body, pos, size, mat, parent, tf, rotation=(0, 0, 0)):
    o=L.text(name,body,(0,0,0),size,mat)
    o.parent=parent
    o.matrix_parent_inverse=Matrix.Identity(4)
    o.matrix_basis=tf @ L.T(*pos) @ Euler(rotation).to_matrix().to_4x4()
    o['reference_only']=True
    return o


def make_motor(kind, name, parent, tf, mats, cradle=True,
               attachment_depth=0, attachment_nut_recess=0):
    """Build one reference motor and a keyed, mechanically captured cradle.

    `body` is the only object assigned the motor mass.  Decorative panel seams,
    screws and connectors are illustrative; do not use them as drill templates.
    `mounting_points` are the verified-in-this-design M3 cradle-post centres;
    the cradle deliberately does not guess vendor body-hole datums.
    """
    kind=kind.upper()
    if kind not in SPECS: raise ValueError('Motor kind must be AX or XM')
    s=SPECS[kind].copy(); tf=tf or Matrix.Identity(4)
    attachment_depth=float(attachment_depth)
    attachment_nut_recess=float(attachment_nut_recess)
    if attachment_depth<0 or attachment_nut_recess<0:
        raise ValueError('Attachment depth and nut recess must be nonnegative')
    # Retained as an API compatibility argument; rear-inserted screws now use
    # captive nuts at the front, so a rear attachment nut recess is not used.
    w,h,top=s['width'],s['height'],s['top']; bottom=top-h; cy=top-h/2
    front,back,rear=s['case_front'],s['case_back'],s['rear']
    black,steel,ivory=mats['black'],mats['steel'],mats['ivory']
    def ref(o, mass=0, collision=False, note='Visual detail; not a mounting datum'):
        return L.reference(o,parent,tf,mass=mass,note=note,collision=collision)
    body=L.cube(name+' | '+s['model']+' dimensioned case',
                (w,h,front-back),(0,cy,(front+back)/2),black,1.15)
    if kind=='AX':
        # Rear protrusion is contained in the official 40 mm overall envelope.
        L.union(body,L.cube('_AX rear case',(w-2.0,h-2.0,4.15),
                           (0,cy,-37.925),black,.65))
    for connector_x in (-5.7,5.7):
        L.boolean(body,L.cube('_rear socket recess',(8.9,6.4,3.5),
                  (connector_x,bottom+7.5,rear+1.35)))
    ref(body,mass=s['mass'],collision=True,
        note='Manufacturer envelope, offset output axis; bought motor incl. horn. '
             'Case surface details illustrative. Mass counted once.')
    body['motor_type']=s['model'];body['envelope_width_height_depth_mm']=[w,h,front-back]
    body['output_axis_offset_from_top_mm']=top
    body['horn_front_datum_local_mm']=[0,0,0]

    # Real motor colour/parting lines; keep seams inside the collision envelope.
    for z in (front-.7,back+.8):
        ref(L.cube(name+' | moulded case seam',(w+.015,h-1.5,.35),
                   (0,cy,z),black,.15))
    # Label on the front-facing lower case, visible through the cradle window.
    label_w=min(w-6,25.0)
    ref(L.cube(name+' | manufacturer label plate',(label_w,13.5,.16),
               (0,cy-4.2,front+.05),black,.5))
    _label(name+' | ROBOTIS label','DYNAMIXEL',(0,cy-.7,front+.16),
           2.65 if kind=='AX' else 2.35,ivory,parent,tf)
    _label(name+' | model label',s['model'],(0,cy-4.8,front+.16),
           2.4 if kind=='AX' else 1.75,ivory,parent,tf)
    _label(name+' | voltage label','12 V  /  TTL',(0,cy-8.2,front+.16),
           1.7,ivory,parent,tf)

    # The stock horn is bought with the actuator. The central retaining screw
    # remains accessible through every printed output adapter.
    horn=L.cyl(name+' | installed stock horn',11.0,s['horn_depth'],
               (0,0,-s['horn_depth']/2),mat=ivory if kind=='AX' else steel,n=80)
    hole_centres=[]
    for i in range(s['horn_count']):
        angle=2*math.pi*i/s['horn_count']
        x,y=8*math.cos(angle),8*math.sin(angle);hole_centres.append((x,y))
        L.hole(horn,(x,y,-s['horn_depth']/2),2.0,s['horn_depth']+1)
    L.hole(horn,(0,0,-s['horn_depth']/2),3.5,s['horn_depth']+1)
    ref(horn,collision=True,note='Installed stock horn; M2 holes on verified 16 mm PCD')
    head=L.cyl(name+' | original retaining screw',2.8,.7,(0,0,-.4),mat=steel,n=40)
    L.boolean(head,L.cube('_screw slot',(3.7,.7,.6),(0,0,-.02)))
    ref(head)
    # The rear panel and sockets are part of the purchased motor, not added
    # fabricated metal components. Connector geometry is an access envelope.
    for x in (-w/2+3.5,w/2-3.5):
        for y in (top-4,bottom+4):
            screw=L.cyl(name+' | case screw',1.6,.24,(x,y,front+.10),mat=steel,n=24)
            L.boolean(screw,L.cyl('_socket',.7,.4,(x,y,front+.18),n=6))
            ref(screw)
    socket_y=bottom+7.5
    for x in (-5.7,5.7):
        sock=L.cube(name+' | TTL socket',(8.5,6.0,2.4),
                    (x,socket_y,rear+1.4),ivory,.35)
        L.boolean(sock,L.cube('_socket opening',(6.6,3.5,2.5),
                            (x,socket_y,rear+.4)))
        ref(sock,note='Illustrative TTL connector; allow cable/service space behind motor')
        for dx in (-2.05,0,2.05):
            ref(L.cyl(name+' | connector contact',.35,.8,
                       (x+dx,socket_y,rear+.55),mat=steel,n=12))
    if kind=='XM':
        for y in (cy+9,cy+6,cy+3,cy,cy-3):
            ref(L.cube(name+' | case cooling rib',(.25,1.0,front-back-3),
                       (w/2+.012,y,(front+back)/2),black,.08))

    mount=[(x,y) for x in (-(w/2+5),w/2+5) for y in (top+4,bottom-4)]
    result=dict(body=body,horn=horn,cradle=None,rear_cap=None,shim=None,
                mounting_points=mount,body_dimensions=(w,h,front-back),
                installed_depth=-rear,horn_dimensions=(22.0,s['horn_depth']),
                horn_hole_centres=hole_centres,horn_pcd_mm=16.0,
                body_top=top,body_bottom=bottom,body_front=front,body_rear=rear,
                rear_cap_front=rear-.35,rear_cap_back=rear-4.95,
                front_bezel_front=s['bezel_front'],front_bezel_back=s['bezel_back'],
                axial_clearance_mm=.70,recommended_shims_mm=[.30,.30])
    schedule=dict(
        name=name,kind=kind,model=s['model'],motor_mass_g=s['mass'],
        parent_object=parent.name if parent else None,
        transform_parent_from_motor_mm=[[float(v) for v in row] for row in tf],
        datum='Installed horn front face at origin; output axis local +Z; case height local Y',
        manufacturer_interfaces=dict(
            published_width_height_depth_mm=[w,h,40.0 if kind=='AX' else 34.0],
            main_case_width_height_depth_mm=[w,h,front-back],
            case_top_y_mm=top,case_bottom_y_mm=bottom,
            main_case_front_z_mm=front,main_case_back_z_mm=back,
            rearmost_case_z_mm=rear,installed_reference_depth_to_horn_front_mm=-rear,
            output_axis_from_top_mm=top,
            horn_diameter_reference_mm=22.0,horn_depth_mm=s['horn_depth'],
            horn_hole_thread='M2 x 0.4',horn_hole_count=s['horn_count'],horn_pcd_mm=16.0,
            horn_hole_centres_motor_xy_mm=[[float(x),float(y)] for x,y in hole_centres],
            horn_max_thread_depth_mm=4.0 if kind=='AX' else 2.0,
            body_holes_used=False,
            interface_note='Horn PCD and motor envelope are manufacturer references; '
                           'case surface/socket details are illustrative; physical fit confirmation required.'),
        has_printed_cradle=bool(cradle),
        cradle_mounting_points_motor_xy_mm=[[float(x),float(y)] for x,y in mount],
        cradle=None,fastener_stack=None,
        assembly_notes=[
            'Retain the supplied motor horn and central retaining screw.',
            'Screw heads face rearward; shafts point along local +Z toward front captive M3 nuts.',
            'Keep rear service access for screw tightening and motor daisy-chain connectors.',
            'For the base motor, preserve the separately designed 8 mm printed-foot clearance beneath the floor.'
        ])
    if not cradle:
        MOTOR_UNITS.append(schedule)
        return result

    bz0,bz1=s['bezel_back'],s['bezel_front'];rz=rear-.35
    # Thin perimeter capture lip: 0.35 mm front gap, 0.35 mm side gap.
    frame=L.cube(name+'_cradle',(w+5.9,h+5.9,bz1-bz0),
                 (0,cy,(bz0+bz1)/2),mats['green'])
    L.boolean(frame,L.cube('_front window',(w-4.5,h-6.0,8),(0,cy,(bz0+bz1)/2),bevel=.8))
    L.hole(frame,(0,0,(bz0+bz1)/2),26.0,8)
    # Posts carry clamping load; ribs locate corners without a heavy solid box.
    for x,y in mount:
        L.union(frame,L.cyl('_M3 standoff',4.6,bz1-rz,(x,y,(bz1+rz)/2),mat=mats['green'],n=40))
    depth=bz1-rz
    for signx in (-1,1):
        gx=signx*(w/2+.35+1.2)
        for yside in (top-2.65,bottom+2.65):
            L.union(frame,L.cube('_corner guide',(2.4,10,depth-.4),
                                 (gx,yside,(bz1+rz)/2),mats['green']))
        # Short top/bottom fingers restrain case Y while leaving the centre open.
        for sy,ycase in ((1,top),(-1,bottom)):
            gx2=signx*(w/2-5.1)
            L.union(frame,L.cube('_corner lip',(14.0,2.4,depth-.8),
                       (gx2,ycase+sy*(.35+1.2),(bz1+rz)/2),mats['green']))
    for x,y in mount:
        L.hole(frame,(x,y,(bz1+rz)/2),3.4,depth+4)
        L.hexhole(frame,(x,y,bz1-1.4),af=5.8,depth=2.8)
    # Boolean intersections can leave sub-micron coincident vertices where
    # straight corner rails meet the post cylinders. Weld only this numerical
    # noise, then dissolve coplanar subdivisions before the STL triangulation.
    bm=bmesh.new();bm.from_mesh(frame.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.001)
    # Freeze valid local-space pocket tessellation before the 180-degree print
    # orientation transform; float32 rotation of n-gons with holes otherwise
    # permits overlapping fan triangles along the bore diameter.
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(frame.data);bm.free();frame.data.update()
    frame=L.part(frame,name+'_C01_Keyed_motor_cradle',parent,tf,
        note=s['model']+' cradle: 0.35 mm per side; 26 mm horn window; 4 M3 posts. '
             'Front captive M3 nuts: 5.8 AF x 2.8 mm recess in 9.2 mm diameter bosses. '
             'Case is located by corners and front/rear lips; no invented motor-body holes.',
        orient=[180,0,0])

    cap_thickness=4.6
    cap=L.cube(name+'_rear_cap',(w+5.9,h+5.9,cap_thickness),
               (0,cy,rz-cap_thickness/2),mats['ivory'],.65)
    for x,y in mount:
        L.union(cap,L.cyl('_cap ear',4.6,cap_thickness,
                          (x,y,rz-cap_thickness/2),mat=mats['ivory'],n=40))
    # Large rear access aperture keeps both daisy-chain sockets usable.
    L.boolean(cap,L.cube('_rear access',(w-5.5,h-7.0,8),
                         (0,cy,rz-cap_thickness/2),bevel=1.2))
    for x,y in mount:
        L.hole(cap,(x,y,rz-cap_thickness/2),3.4,8)
    cap=L.part(cap,name+'_C02_Connector_access_rear_cap',parent,tf,
        note='4.6 mm rear cap; 4 M3 clearance bores matched to cradle. '
             'Screws insert from the rear supporting wall and engage front captive nuts. '
             'Rear window clears the connector envelope; actual plugs must be checked.',
        orient=[0,0,0])
    shims=[]
    # Removable printed shims take up most of the intentional axial fit gap.
    # Leave 0.025 mm either side of each nominal 0.30 mm shim in this ideal CAD
    # pose, rather than hiding intersecting meshes to make the fit look tight.
    for index,shim_z in enumerate((front+.175,rear-.175),1):
        shim=L.cube(name+'_shim',(w-.1,h-.1,.30),(0,cy,shim_z),mats['ivory'])
        opening=(w-4.5,h-6.0) if index==1 else (w-5.5,h-7.0)
        L.boolean(shim,L.cube('_shim window',(*opening,2),(0,cy,shim_z)))
        if index==1:L.hole(shim,(0,0,shim_z),26,2)
        shim=L.part(shim,name+'_C04_'+str(index)+'_Axial_fit_shim_030',parent,tf,
            note='Removable 0.30 mm printed motor shim. Two nominal shims reduce '
                 'total designed endplay from 0.70 to 0.10 mm. Adjust only after '
                 'physical fit measurement; use fine layer height for this part.')
        shims.append(shim)
    # Rear-inserted screws keep heads and spacers out of the front gear plane.
    # Select a standard 5 mm length increment and put the exact remaining stack
    # behind the supporting wall as a separately printable annular spacer.
    cap_back=rz-cap_thickness
    rear_wall=cap_back-attachment_depth
    nut_top=bz1-.2;nut_bottom=nut_top-2.4;shaft_tip=nut_top+.1
    length=math.ceil((shaft_tip-rear_wall)/5.0)*5.0
    head_z=shaft_tip-length;spacer_height=rear_wall-head_z
    stack=dict(diameter_mm=3,length_mm=length,spacer_mm=spacer_height,qty=4,
               insertion_direction='+LOCAL_Z',under_head_z_mm=head_z,shaft_tip_z_mm=shaft_tip,
               cap_back_z_mm=cap_back,attachment_depth_mm=attachment_depth,
               attachment_far_face_z_mm=rear_wall,
               rear_spacer_front_z_mm=rear_wall,rear_spacer_back_z_mm=head_z,
               attachment_nut_recess_mm=0,deprecated_nut_recess_argument_mm=attachment_nut_recess,
               front_nut_top_z_mm=nut_top,front_nut_bottom_z_mm=nut_bottom,
               front_nut_qty=4,nominal_tip_beyond_nut_mm=.1,
               front_nut_boss_radius_mm=4.6,front_nut_pocket_depth_mm=2.8,
               front_nut_pocket_af_mm=5.8)
    spacers=[]
    for i,(x,y) in enumerate(mount,1):
        if spacer_height>1e-6:
            spacer=L.cyl(name+'_spacer',3.4,spacer_height,
                         (x,y,(head_z+rear_wall)/2),mat=mats['ivory'],n=40)
            L.hole(spacer,(x,y,(head_z+rear_wall)/2),3.4,spacer_height+2)
            spacer=L.part(spacer,name+'_C03_'+str(i)+'_Screw_stack_spacer',parent,tf,
                note='Printed rear '+str(round(spacer_height,3))+' mm spacer for standard M3x'+str(int(length))+
                     ' rear-inserted screw; attachment stack depth '+str(attachment_depth)+' mm.')
            spacers.append(spacer)
        L.bolt(name+' | M3x'+str(int(length))+' cradle screw '+str(i),
               parent,tf @ L.T(x,y,head_z) @ L.R('X',180),length,steel)
        L.nut(name+' | M3 front captive nut '+str(i),parent,
              tf @ L.T(x,y,nut_bottom),steel)

    result.update(cradle=frame,rear_cap=cap,shim=shims[0],shims=shims,spacers=spacers,
                  axial_clearance_with_shims_mm=.10,
                  cradle_screw=stack,
                  notes='Fit coupon required. Rear connector dimensions are clearance illustrations. '
                        'Two 0.30 mm shims may be needed after measuring actual motor/case seating.')
    schedule['cradle']=dict(
        body_clearance_per_side_mm=.35,
        front_bezel_back_z_mm=bz0,front_bezel_front_z_mm=bz1,
        rear_cap_front_z_mm=rz,rear_cap_back_z_mm=cap_back,rear_cap_thickness_mm=cap_thickness,
        horn_window_diameter_mm=26.0,post_radius_mm=4.6,
        m3_clearance_diameter_mm=3.4,front_nut_pocket_af_mm=5.8,front_nut_pocket_depth_mm=2.8,
        axial_clearance_without_shims_mm=.70,printed_axial_shim_thickness_mm=[.30,.30],
        axial_clearance_with_nominal_shims_mm=.10,
        part_ids=[frame['part_id'],cap['part_id']]+[o['part_id'] for o in shims+spacers])
    schedule['fastener_stack']=dict(stack)
    MOTOR_UNITS.append(schedule)
    return result
