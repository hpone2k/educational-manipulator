"""Dimensioned DYNAMIXEL references and separately printable captured cradles.

All coordinates are millimetres.  Origin is the front face of the installed horn,
with the motor output axis along local +Z; the case height follows local Y.
Purchased motor surfaces are tessellated directly from official ROBOTIS STEP CAD.
XM internal case/horn separation is added solely to animate the vendor dummy exterior.
"""
import math, bmesh, bpy, gzip, json
from pathlib import Path
from mathutils import Matrix, Euler
import blender_lib as L


MOTOR_UNITS=[]


SPECS = {
    'AX': dict(model='AX-12A', width=32.0, height=50.0, top=11.5,
               case_front=-5.0, case_back=-37.0, rear=-40.0, rear_seat=-37.0,
               horn_depth=5.0, horn_diameter=22.0, horn_count=4, horn_pcd=16.0,
               mass=54.6, bezel_back=-4.65, bezel_front=-1.05, rear_shim=3.30),
    'XM': dict(model='XM430-W350-T', width=28.5, height=46.5, top=11.25,
               case_front=-2.0, case_back=-36.0, rear=-36.2, rear_seat=-36.0,
               horn_depth=2.0, horn_diameter=19.5, horn_count=8, horn_pcd=16.0,
               mass=82.0, bezel_back=-1.65, bezel_front=-.25, rear_shim=.50),
}


def _label(name, body, pos, size, mat, parent, tf, rotation=(0, 0, 0)):
    o=L.text(name,body,(0,0,0),size,mat)
    o.parent=parent
    o.matrix_parent_inverse=Matrix.Identity(4)
    o.matrix_basis=tf @ L.T(*pos) @ Euler(rotation).to_matrix().to_4x4()
    o['reference_only']=True
    return o


_CAD_CACHE={}
_VENDOR_MESH_CACHE={}


def _vendor_close_tessellation(o):
    # Weld analytic-face boundaries within ONE vendor solid. Never weld two
    # touching purchased components together: that creates nonmanifold edges.
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()
    return o


def _retain_ax_front_seating_piece(o):
    """Remove only disconnected upper-corner chips from the AX front shim.

    The Ø34 access opening leaves one functional U-shaped front seating piece
    and two tiny isolated corner remnants. The retained vertices are unchanged;
    this does not bridge the opening or alter the motor clearance.
    """
    bm=bmesh.new();bm.from_mesh(o.data)
    before=bm.calc_volume(signed=True)
    remaining=set(bm.verts);components=[]
    while remaining:
        seed=remaining.pop();component={seed};pending=[seed]
        while pending:
            vertex=pending.pop()
            for edge in vertex.link_edges:
                neighbour=edge.other_vert(vertex)
                if neighbour in remaining:
                    remaining.remove(neighbour);component.add(neighbour);pending.append(neighbour)
        components.append(component)
    if len(components)>1:
        def surface_area(component):
            return sum(face.calc_area() for face in {f for v in component for f in v.link_faces})
        retained=max(components,key=surface_area)
        discarded=[v for component in components if component is not retained for v in component]
        bmesh.ops.delete(bm,geom=discarded,context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    after=bm.calc_volume(signed=True)
    bm.to_mesh(o.data);bm.free();o.data.update()
    o['disconnected_nonfunctional_corners_removed']=max(0,len(components)-1)
    o['removed_corner_volume_mm3']=before-after
    o['front_seating_shape']='Single connected U; side and lower case flange contact; upper casing remains open.'
    return o


def _rounded_outline(width,height,radius,centre=(0,0),segments=8):
    """CCW rounded rectangle; keeps the original width/height envelope."""
    points=[];cx,cy=centre
    for x,y,start in [(width/2-radius,height/2-radius,0),
                      (-width/2+radius,height/2-radius,90),
                      (-width/2+radius,-height/2+radius,180),
                      (width/2-radius,-height/2+radius,270)]:
        for i in range(segments+1):
            a=math.radians(start+90*i/segments)
            points.append((cx+x+radius*math.cos(a),cy+y+radius*math.sin(a)))
    return points


def _sculpted_column(name,x,y,back,front,mat):
    """Continuous M3 load column with full end bosses and a tapered waist."""
    rings=[(back,4.6),(back+3.2,4.6),(back+8.2,3.6),
           (front-9.0,3.6),(front-4.8,4.6),(front,4.6)]
    n=40;vertices=[];faces=[]
    for z,r in rings:
        vertices.extend((x+r*math.cos(2*math.pi*i/n),y+r*math.sin(2*math.pi*i/n),z) for i in range(n))
    faces.append(tuple(reversed(range(n))))
    for j in range(len(rings)-1):
        for i in range(n):
            k=(i+1)%n;faces.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i))
    faces.append(tuple((len(rings)-1)*n+i for i in range(n)))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);mesh.materials.append(mat)
    return o


def _sculpted_side_arch(name,x,y0,y1,z,mat):
    """Rounded structural rib in a YZ side plane, outside the motor envelope.

    The rib bows axially across the open side, joins both mounting columns,
    and does not enclose the case with a cosmetic shroud. Cross-section is
    2.4 mm across X by 2.8 mm normal to the arch centreline.
    """
    half=1.4;left=[];right=[];normals=[];centres=[]
    for i in range(17):
        t=i/16;yc=y0+(y1-y0)*t;zc=z-4+9*math.sin(math.pi*t)
        dy=y1-y0;dz=9*math.pi*math.cos(math.pi*t);length=math.hypot(dy,dz)
        normal=(-dz/length,dy/length);normals.append(normal);centres.append((yc,zc))
        left.append((yc+half*normal[0],zc+half*normal[1]))
        right.append((yc-half*normal[0],zc-half*normal[1]))
    points=list(left)
    a=math.atan2(normals[-1][1],normals[-1][0]);yc,zc=centres[-1]
    for i in range(1,9):
        q=a-math.pi*i/8;points.append((yc+half*math.cos(q),zc+half*math.sin(q)))
    points.extend(reversed(right[:-1]))
    a=math.atan2(normals[0][1],normals[0][0])+math.pi;yc,zc=centres[0]
    for i in range(1,8):
        q=a-math.pi*i/8;points.append((yc+half*math.cos(q),zc+half*math.sin(q)))
    o=L.poly(name,points,x-1.2,2.4,mat)
    # poly(X,Y,Z extrusion) -> arch(Y,Z,X extrusion).
    o.data.transform(Matrix(((0,0,1,0),(1,0,0,0),(0,1,0,0),(0,0,0,1))))
    o.data.update();return o


def _vendor_mesh(name, vertices, faces, mat):
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],faces);data.update()
    o=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(o)
    data.materials.append(mat)
    _vendor_close_tessellation(o)
    # STEP tessellation retains vertices split at analytic surface boundaries.
    for p in data.polygons:p.use_smooth=True
    return o


def _join_vendor(objects,name):
    target=objects[0];L.active(target)
    for o in objects:o.select_set(True)
    bpy.ops.object.join();target.name=name
    return target


def _xm_partition(o,upper):
    """Partition the closed vendor exterior, retaining all external vertices."""
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        dist=.00001,plane_co=(0,0,-2),plane_no=(0,0,1),
        clear_inner=upper,clear_outer=not upper)
    if upper:
        # Coplanar front-case triangles belong to the fixed casing. Removing
        # them from the rotor leaves only the actual Ø19.5 horn above the plane.
        flat=[f for f in bm.faces if all(abs(v.co.z+2)<.00001 for v in f.verts)]
        bmesh.ops.delete(bm,geom=flat,context='FACES')
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
    bmesh.ops.triangle_fill(bm,edges=[e for e in bm.edges if e.is_boundary],
                           use_beauty=True,use_dissolve=False)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if any(not e.is_manifold for e in bm.edges):
        bm.free();raise RuntimeError('XM vendor partition must remain closed')
    bm.to_mesh(o.data);bm.free();o.data.update()


def _official_motor(kind,name,parent,tf,mats):
    """Keep vendor exterior; add only an internal plane separating XM rotor.

    ROBOTIS publishes simplified assembly CAD, not motor internal geartrain CAD.
    The XM exterior is one fused dummy body. A plane partition and internal caps
    at the front case plane form CLOSED case and rotor surfaces for animation and
    collision containment. No exterior dimensions or mounting holes are moved.
    """
    if kind not in _CAD_CACHE:
        src=Path(__file__).resolve().parent/'motor-references'/(kind+'-official-mm.json.gz')
        with gzip.open(src,'rt',encoding='utf-8') as f:_CAD_CACHE[kind]=json.load(f)
    cad=_CAD_CACHE[kind]
    # Keep one completed, LOCAL-space mesh template for each kind/material set.
    # Template meshes are independent copies, so changing one motor instance or
    # parenting its horn cannot affect future instances. Native mesh.copy()
    # preserves exact vertices, polygons, normals, sharp edges and materials.
    cache_key=(kind,mats['black'].as_pointer(),mats['steel'].as_pointer())
    cached=cache_key in _VENDOR_MESH_CACHE
    if cached:
        templates=_VENDOR_MESH_CACHE[cache_key]
        created=[]
        for entry in templates:
            o=bpy.data.objects.new(name+entry['suffix'],entry['mesh'].copy())
            bpy.context.scene.collection.objects.link(o)
            for key,value in entry['properties'].items():o[key]=value
            created.append(o)
        body,horn,*internal_rotating=created
    else:
        stock=bpy.data.materials.get('ROBOTIS purchased light polymer')
        if stock is None:stock=L.material('ROBOTIS purchased light polymer',(.62,.63,.61),rough=.29)
        xmmetal=bpy.data.materials.get('ROBOTIS purchased anodized casing')
        if xmmetal is None:xmmetal=L.material('ROBOTIS purchased anodized casing',(.115,.125,.13),metal=.62,rough=.31)
        fixed=[];rotating=[];internal_rotating=[]
        for p in cad['parts']:
            source_name=p['name'];role=p['role']
            mat=stock if role in ('connector','stock_horn') else mats['steel']
            if role in ('case','cable_cover'):mat=xmmetal if kind=='XM' and role=='case' else mats['black']
            o=_vendor_mesh(name+' | vendor '+source_name,p['vertices'],p['faces'],mat)
            o['vendor_component']=source_name
            if kind=='XM' and role=='case':
                # Closing the internal separation matters to point-inside collision
                # tests. Never leave the vendor dummy as a single rotating case.
                rotor=o.copy();rotor.data=o.data.copy();bpy.context.scene.collection.objects.link(rotor)
                rotor.name=name+' | XM split rotor'
                _xm_partition(rotor,True);_xm_partition(o,False)
                rotor.data.materials.clear();rotor.data.materials.append(mats['steel'])
                rotor['internal_separation_note']='Plane at case-front z=-2 mm added to fused vendor dummy; exact exterior unchanged.'
                rotating.append(rotor);fixed.append(o)
            elif kind=='AX' and source_name=='DC04_B01_HORN2_DUMMY':
                rotating.append(o)
            elif kind=='AX' and source_name in ('BHS_M2_6X8','ASSY_GEAR-WHEEL___DUMMY'):
                # Vendor dummy case does not model the internal gearbox cavity;
                # its centre screw/shaft intentionally overlap that solid dummy.
                # Keep real geometry and animation, but no internal motor fit claim.
                internal_rotating.append(o)
            else:fixed.append(o)
        body=_join_vendor(fixed,name+' | '+SPECS[kind]['model']+' dimensioned case')
        horn=_join_vendor(rotating,name+' | installed stock horn')
        for o in (body,horn):
            for polygon in o.data.polygons:polygon.use_smooth=True
            if hasattr(o.data,'set_sharp_from_angle'):o.data.set_sharp_from_angle(angle=.55)
        _VENDOR_MESH_CACHE[cache_key]=[
            {'suffix':o.name[len(name):],'mesh':o.data.copy(),
             'properties':{key:o[key] for key in o.keys()}}
            for o in (body,horn,*internal_rotating)]
    for o,role,mass in [(body,'case',SPECS[kind]['mass']),(horn,'horn',0)]:
        L.reference(o,parent,tf,mass=mass,collision=True,
                    note='Official ROBOTIS STEP exterior, 0.01 mm chord tolerance; purchased motor, not printable. '+
                         ('XM fused dummy partitioned at internal case-front plane for closed rotating horn.' if kind=='XM' else 'Vendor AX assembly components preserved.'))
        o['motor_id']=name;o['interface_role']=role;o['source_step']=cad['source_step']
        o['vendor_geometry']=True;o['tessellation_chord_mm']=.01
    for o in internal_rotating:
        L.reference(o,horn,Matrix.Identity(4),collision=False,
            note='Official purchased internal rotor/retaining screw. Vendor envelope dummy lacks internal gearbox cavity; excluded from motor-internal collision inference. External screw-head allowance is documented in interface schedule.')
        o['motor_id']=name;o['interface_role']='internal_rotating_hardware';o['vendor_geometry']=True
    return body,horn


def make_motor(kind, name, parent, tf, mats, cradle=True,
               attachment_depth=0, attachment_nut_recess=0,front_fasteners=False,
               style='standard'):
    """Build one reference motor and a keyed, mechanically captured cradle.

    `body` alone carries motor mass. Official vendor exterior meshes include
    actual case holes, fasteners and connector access geometry. Source STEP
    remains the authoritative curved geometry; imported meshes are references.
    `mounting_points` are the verified-in-this-design M3 cradle-post centres;
    the cradle deliberately does not guess vendor body-hole datums.
    `style='sculpted'` rounds the outer saddle, tapers column waists and replaces
    long corner rails with end locating pads and open bowed side ribs. Motor
    datums, mounting axes, rear-cap planes and screw stacks are unchanged.
    Omit style to preserve the original base cradle geometry exactly.
    """
    kind=kind.upper()
    if kind not in SPECS: raise ValueError('Motor kind must be AX or XM')
    if style not in ('standard','sculpted'):raise ValueError('Cradle style must be standard or sculpted')
    s=SPECS[kind].copy(); tf=tf or Matrix.Identity(4)
    attachment_depth=float(attachment_depth)
    attachment_nut_recess=float(attachment_nut_recess)
    if attachment_depth<0 or attachment_nut_recess<0:
        raise ValueError('Attachment depth and nut recess must be nonnegative')
    if front_fasteners:
        if kind!='AX' or abs(attachment_depth-6)>1e-6:
            raise ValueError('Front-fastener option is dimensioned for AX with a 6 mm rear palm only')
        s['bezel_front']=-2.05
    # Retained as an API compatibility argument; rear-inserted screws now use
    # captive nuts at the front, so a rear attachment nut recess is not used.
    w,h,top=s['width'],s['height'],s['top']; bottom=top-h; cy=top-h/2
    front,back,rear=s['case_front'],s['case_back'],s['rear']
    black,steel,ivory=mats['black'],mats['steel'],mats['ivory']
    def ref(o, mass=0, collision=False, note='Visual detail; not a mounting datum'):
        return L.reference(o,parent,tf,mass=mass,note=note,collision=collision)
    body,horn=_official_motor(kind,name,parent,tf,mats)
    body['motor_type']=s['model'];body['envelope_width_height_depth_mm']=[w,h,front-back]
    body['output_axis_offset_from_top_mm']=top
    body['horn_front_datum_local_mm']=[0,0,0]
    hole_centres=[(8*math.cos(2*math.pi*i/s['horn_count']),
                   8*math.sin(2*math.pi*i/s['horn_count'])) for i in range(s['horn_count'])]
    # Labels are presentation overlays only, not holes or substituted case geometry.
    label_z=-1.82 if kind=='AX' else front+.18
    _label(name+' | model marking',s['model'],(0,cy-7.0,label_z),
           1.65 if kind=='XM' else 2.0,mats.get('text',ivory),parent,tf)
    _label(name+' | manufacturer marking','DYNAMIXEL',(0,cy-3.0,label_z),
           1.6,mats.get('text',ivory),parent,tf)

    mount=[(x,y) for x in (-(w/2+5),w/2+5) for y in (top+4,bottom-4)]
    result=dict(body=body,horn=horn,cradle=None,rear_cap=None,shim=None,
                mounting_points=mount,body_dimensions=(w,h,front-back),
                installed_depth=-rear,horn_dimensions=(s['horn_diameter'],s['horn_depth']),
                horn_hole_centres=hole_centres,horn_pcd_mm=16.0,
                body_top=top,body_bottom=bottom,body_front=front,body_rear=rear,
                rear_cap_front=rear-.35,rear_cap_back=rear-4.95,
                front_bezel_front=s['bezel_front'],front_bezel_back=s['bezel_back'],
                axial_clearance_mm=.40+s['rear_shim'],recommended_shims_mm=[.30,s['rear_shim']])
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
            horn_diameter_reference_mm=s['horn_diameter'],horn_depth_mm=s['horn_depth'],
            horn_hole_thread='M2 x 0.4',horn_hole_count=s['horn_count'],horn_pcd_mm=16.0,
            horn_hole_centres_motor_xy_mm=[[float(x),float(y)] for x,y in hole_centres],
            horn_max_thread_depth_mm=4.0 if kind=='AX' else 2.0,
            central_projection_from_horn_mm=.04545 if kind=='AX' else 4.7,
            suggested_adapter_centre_clearance='AX: diameter6.0 depth0.30; XM: diameter8.5 depth2.5 then diameter5.0 depth5.0',
            rear_case_seating_z_mm=s['rear_seat'],
            rear_idler_included=(kind=='XM'),
            body_holes_used=False,
            interface_note='Exterior and body holes imported from official ROBOTIS STEP at 0.01 mm chord tolerance. '
                           'XM CAD horn face offset 2.0 mm differs from 2.2 mm on the older drawing. '
                           'XM rear idler retained; actual supplied revision and physical fit require confirmation.'),
        has_printed_cradle=bool(cradle),
        cradle_style=style,
        front_fasteners=bool(front_fasteners),
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
    if style=='sculpted':
        frame=L.poly(name+'_cradle',_rounded_outline(w+5.9,h+5.9,3.2,(0,cy)),
                     bz0,bz1-bz0,mats['green'])
    else:
        frame=L.cube(name+'_cradle',(w+5.9,h+5.9,bz1-bz0),
                     (0,cy,(bz0+bz1)/2),mats['green'])
    L.boolean(frame,L.cube('_front window',(w-4.5,h-6.0,8),(0,cy,(bz0+bz1)/2),bevel=.8))
    front_window=34.0 if kind=='AX' else 26.0
    L.hole(frame,(0,0,(bz0+bz1)/2),front_window,8)
    if kind=='AX':
        for x,y in [(-9.5,8.5),(9.5,8.5),(-10.5,-33),(10.5,-33)]:
            L.hole(frame,(x,y,(bz0+bz1)/2),5.0,8)
    # Posts carry clamping load; ribs locate corners without a heavy solid box.
    for x,y in mount:
        column=(_sculpted_column('_tapered M3 column',x,y,rz,bz1,mats['green'])
                if style=='sculpted' else
                L.cyl('_M3 standoff',4.6,bz1-rz,(x,y,(bz1+rz)/2),mat=mats['green'],n=40))
        L.union(frame,column)
    depth=bz1-rz
    for signx in (-1,1):
        gx=signx*(w/2+.35+1.2)
        for yside in (top-2.65,bottom+2.65):
            if style=='sculpted':
                for endz in (rz+3.1,bz1-3.1):
                    L.union(frame,L.cube('_rounded locating pad',(2.4,10,5.8),
                                 (gx,yside,endz),mats['green'],.45))
            else:
                L.union(frame,L.cube('_corner guide',(2.4,10,depth-.4),
                                     (gx,yside,(bz1+rz)/2),mats['green']))
        # Short top/bottom fingers restrain case Y while leaving the centre open.
        for sy,ycase in ((1,top),(-1,bottom)):
            gx2=signx*(w/2-5.1)
            if style=='sculpted':
                for endz in (rz+3.1,bz1-3.1):
                    L.union(frame,L.cube('_rounded end seating finger',(14.0,2.4,5.4),
                         (gx2,ycase+sy*(.35+1.2),endz),mats['green'],.45))
            else:
                L.union(frame,L.cube('_corner lip',(14.0,2.4,depth-.8),
                           (gx2,ycase+sy*(.35+1.2),(bz1+rz)/2),mats['green']))
        if style=='sculpted':
            L.union(frame,_sculpted_side_arch('_bowed side rib',gx,bottom-4,top+4,
                                             (bz1+rz)/2,mats['green']))
    for x,y in mount:
        L.hole(frame,(x,y,(bz1+rz)/2),3.4,depth+4)
        if front_fasteners:L.hole(frame,(x,y,-3.825),6.2,3.65)
        elif style=='sculpted':
            # Same 2.8 mm physical recess; cutter overrun avoids a face exactly
            # coplanar with the lathed post cap and leaking Boolean seams.
            L.hexhole(frame,(x,y,bz1-1.30),af=5.8,depth=3.0)
        else:L.hexhole(frame,(x,y,bz1-1.4),af=5.8,depth=2.8)
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
        note=s['model']+' cradle: 0.35 mm per side; '+str(front_window)+' mm front access window; 4 M3 posts. '
             +('Front M3x45 socket screws into separate rear palm captive nuts. ' if front_fasteners else 'Front captive M3 nuts: 5.8 AF x 2.8 mm recess in 9.2 mm bosses. ')+
             'Case is located by corners and front/rear lips; no invented motor-body holes. '+
             ('Sculpted open saddle: 7.2 mm column waists, 9.2 mm end bosses, rounded end locating pads and bowed side ribs.' if style=='sculpted' else 'Standard base-compatible frame.'),
        orient=[180,0,0])

    cap_thickness=4.6
    if style=='sculpted':
        cap=L.poly(name+'_rear_cap',_rounded_outline(w+5.9,h+5.9,3.2,(0,cy)),
                   rz-cap_thickness,cap_thickness,mats['ivory'])
    else:
        cap=L.cube(name+'_rear_cap',(w+5.9,h+5.9,cap_thickness),
                   (0,cy,rz-cap_thickness/2),mats['ivory'],.65)
    for x,y in mount:
        L.union(cap,L.cyl('_cap ear',4.6,cap_thickness,
                          (x,y,rz-cap_thickness/2),mat=mats['ivory'],n=40))
    # Large rear access aperture keeps both daisy-chain sockets usable.
    L.boolean(cap,L.cube('_rear access',(w-5.5,h-7.0,8),
                         (0,cy,rz-cap_thickness/2),bevel=1.2))
    if kind=='XM':L.hole(cap,(0,0,rz-cap_thickness/2),21.0,8)
    for x,y in mount:
        L.hole(cap,(x,y,rz-cap_thickness/2),3.4,8)
    cap=L.part(cap,name+'_C02_Connector_access_rear_cap',parent,tf,
        note='4.6 mm rear cap; 4 M3 clearance bores matched to cradle. '
             'Screws insert from the rear supporting wall and engage front captive nuts. '
             'Rear window clears the connector envelope; actual plugs must be checked.',
        orient=[0,0,0])
    shims=[]
    # Exact STEP seating datums: AX z-40 is a local rear protrusion, while
    # its load-bearing perimeter is z-37. Preserve rear mounting interface by
    # making a 3.30 mm rear seating spacer. XM's rear plane z-36 needs 0.50 mm.
    shim_specs=[(front+.175,.30),
                ((s['rear_seat']+rz)/2,s['rear_shim'])]
    for index,(shim_z,thickness) in enumerate(shim_specs,1):
        shim=L.cube(name+'_shim',(w-.1,h-.1,thickness),(0,cy,shim_z),mats['ivory'])
        opening=(w-4.5,h-6.0) if index==1 else (w-5.5,h-7.0)
        L.boolean(shim,L.cube('_shim window',(*opening,thickness+2),(0,cy,shim_z)))
        if index==1:L.hole(shim,(0,0,shim_z),front_window,thickness+2)
        elif kind=='XM':L.hole(shim,(0,0,shim_z),21,thickness+2)
        if kind=='AX' and index==1:
            for x,y in [(-9.5,8.5),(9.5,8.5),(-10.5,-33),(10.5,-33)]:
                L.hole(shim,(x,y,shim_z),5.0,thickness+2)
            _retain_ax_front_seating_piece(shim)
        suffix='030' if index==1 else ('330' if kind=='AX' else '050')
        shim=L.part(shim,name+'_C04_'+str(index)+'_Axial_fit_shim_'+suffix,parent,tf,
            note='Printed motor seating spacer %.2f mm. Uses official STEP seating face; '
                 'rear aperture clears vendor protrusions. Nominal total endplay 0.10 mm; '
                 'confirm actual hardware seating and adjust thickness after fit coupon. '
                 'AX front spacer is one connected U at the side/lower seating flange; '
                 'nonfunctional upper corner remnants are removed.' % thickness)
        shims.append(shim)
    # Rear-inserted screws keep heads and spacers out of the front gear plane.
    # Select a standard 5 mm length increment and put the exact remaining stack
    # behind the supporting wall as a separately printable annular spacer.
    cap_back=rz-cap_thickness
    rear_wall=cap_back-attachment_depth
    if front_fasteners:
        head_z=-5.65;length=45.0;shaft_tip=-50.65;spacer_height=0.0;spacers=[]
        stack=dict(diameter_mm=3,length_mm=length,spacer_mm=0,qty=4,
            insertion_direction='-LOCAL_Z',under_head_z_mm=head_z,shaft_tip_z_mm=shaft_tip,
            cap_back_z_mm=cap_back,attachment_depth_mm=attachment_depth,
            attachment_far_face_z_mm=rear_wall,front_nut_qty=0,rear_nut_qty=4,
            rear_nut_top_z_mm=-48.35,rear_nut_bottom_z_mm=-50.75,
            rear_nut_pocket_top_z_mm=-48.15,rear_nut_pocket_bottom_z_mm=-51.05,
            socket_head_top_z_mm=-2.65,front_counterbore_diameter_mm=6.2,
            front_counterbore_seat_z_mm=head_z,
            assembly_note='Front screws engage rear palm captive nuts created by gripper module; no front nut or rear spacer.')
        for i,(x,y) in enumerate(mount,1):
            L.bolt(name+' | M3x45 front cradle screw '+str(i),parent,
                   tf @ L.T(x,y,head_z),45,steel)
    else:
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
                  style=style,
                  axial_clearance_with_shims_mm=.10,
                  cradle_screw=stack,
                  notes='Official motor exterior CAD. Keep rear cable access; fit coupon required. '
                        'Front seating shim 0.30 mm; rear AX3.30 or XM0.50 mm. Confirm hardware revision.')
    schedule['cradle']=dict(
        style=style,
        body_clearance_per_side_mm=.35,
        front_bezel_back_z_mm=bz0,front_bezel_front_z_mm=bz1,
        rear_cap_front_z_mm=rz,rear_cap_back_z_mm=cap_back,rear_cap_thickness_mm=cap_thickness,
        horn_window_diameter_mm=front_window,post_radius_mm=4.6,
        m3_clearance_diameter_mm=3.4,
        front_nut_pocket_af_mm=None if front_fasteners else 5.8,
        front_nut_pocket_depth_mm=None if front_fasteners else 2.8,
        front_socket_counterbore_diameter_mm=6.2 if front_fasteners else None,
        axial_clearance_without_shims_mm=.40+s['rear_shim'],printed_axial_shim_thickness_mm=[.30,s['rear_shim']],
        axial_clearance_with_nominal_shims_mm=.10,
        part_ids=[frame['part_id'],cap['part_id']]+[o['part_id'] for o in shims+spacers])
    schedule['fastener_stack']=dict(stack)
    if front_fasteners:
        schedule['assembly_notes']=[
            'Attach rear palm to the J6 adapter before installing the gripper motor.',
            'Install the rear captive M3 nuts in palm pockets before seating the motor.',
            'Seat motor and rear3.30/front0.30 spacers; insert four M3x45 screws from the front.',
            'Front socket heads sit at z-2.65 and clear the moving gripper transmission.',
            'Retain supplied motor horn and central retaining screw; verify driver access before printing.'
        ]
    MOTOR_UNITS.append(schedule)
    return result
