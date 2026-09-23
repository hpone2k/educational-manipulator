"""Connected, native-driver TTL harness for EDU06 R06 (coordinates in mm).

build_wiring(B) accepts the already-built builder module/namespace. Motor bodies
are located by official-CAD metadata. Every spline control point follows a real
object transform; no frame handler, external add-on, or trusted Python startup
script is needed to keep connector endpoints attached after reopening Blender.

This is a kinematic routing model, not a flexible-cable dynamics solver. See
wiring-notes.md for provisional connector datums and electrical limitations.
"""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector, Matrix
import blender_lib as L

ROOT = Path(__file__).resolve().parent
PINOUT = [('GND', 'black'), ('VDD', 'red'), ('DATA', 'yellow')]
CHAIN = ['J1_BASE', 'S_XM', 'E_XM', 'J4_AX', 'J5_AX', 'GRIP']
SOURCES = {
    'AX': 'https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/#connector-information',
    'XM': 'https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#connector-information',
    'U2D2': 'https://emanual.robotis.com/docs/en/parts/interface/u2d2/',
}


def _empty(name, parent=None, xyz=(0, 0, 0), rotation=None):
    o = bpy.data.objects.new(name, None)
    L.cables.objects.link(o)
    o.empty_display_type = 'PLAIN_AXES'
    o.empty_display_size = 2.5
    o.parent = parent
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = L.T(*xyz) @ (rotation or Matrix.Identity(4))
    o['wiring_object'] = True
    return o


def _world_driver(data, path, index, target):
    d = data.driver_add(path, index).driver
    d.type = 'SCRIPTED'
    v = d.variables.new()
    v.name = 'p'
    v.type = 'TRANSFORMS'
    v.targets[0].id = target
    v.targets[0].transform_type = ['LOC_X', 'LOC_Y', 'LOC_Z'][index]
    v.targets[0].transform_space = 'WORLD_SPACE'
    d.expression = 'p'


def _curve(name, anchors, radius, material, harness_id, conductor, hidden=False):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 16
    data.bevel_depth = radius
    data.bevel_resolution = 3
    data.use_fill_caps = True
    spline = data.splines.new('NURBS')
    spline.points.add(len(anchors)-1)
    spline.order_u = min(4, len(anchors))
    spline.use_endpoint_u = True
    for i, anchor in enumerate(anchors):
        spline.points[i].co = (*anchor.matrix_world.translation, 1)
        for axis in range(3):
            _world_driver(data, f'splines[0].points[{i}].co', axis, anchor)
    o = bpy.data.objects.new(name, data)
    L.cables.objects.link(o)
    if material:
        data.materials.append(material)
    o.hide_render = hidden
    o['wiring_object'] = True
    o['harness_id'] = harness_id
    o['conductor'] = conductor
    o['wire_radius_mm'] = radius
    o['reference_only'] = True
    o['curve_anchor_names_json'] = json.dumps([a.name for a in anchors])
    o['attachment_method'] = 'Native WORLD_SPACE transform drivers on every NURBS control point'
    return o


def _orientation(width, outward):
    """Connector local X is pin-row width; local +Z points out of the case."""
    x = Vector(width).normalized()
    z = Vector(outward).normalized()
    y = z.cross(x).normalized()
    return Matrix((x, y, z)).transposed().to_4x4()


def _connector(case, side, mat):
    model = case['motor_type']
    is_ax = model == 'AX-12A'
    if is_ax:
        xyz = (-4.95 if side == 0 else 5.05, -15.17, -33.7)
        rot = _orientation((1,0,0), (0,0,-1))
        family = 'MOLEX 50-37-5033'
        provenance = 'AX separate official STEP header bounds; rear-facing mouth at Z-33.7. Plug envelope is provisional.'
        envelope = (8.3, 4.2, 7.0)
    else:
        sign = -1 if side == 0 else 1
        xyz = (sign*14.25, -14.55, -29.875)
        rot = _orientation((0,1,0), (sign,0,0))
        family = 'JST EHR-03'
        provenance = 'Official XM side-cover opening at X+/-14.25, Y-14.55, Z-32.2..-27.55. Hidden socket contact depth and plug fit are provisional.'
        envelope = (8.3, 4.0, 7.0)
    name = case['motor_id'] + (' PORT A' if side == 0 else ' PORT B')
    port = _empty(name, case, xyz, rot)
    port['port_role'] = 'motor_ttl_connector'
    port['motor_id'] = case['motor_id']
    port['connector_family'] = family
    port['pinout'] = '1 GND / 2 VDD / 3 DATA; physical polarity must be confirmed on supplied hardware'
    port['datum_source'] = provenance
    port['electrical_contact_depth_verified'] = False
    # The final unused gripper port remains a socket; do not invent a loose plug.
    used = not (case['motor_id'] == 'GRIP' and side == 1)
    if used:
        plug = L.cube(name+' / cable housing envelope', envelope, (0,0,envelope[2]/2), mat, .45)
        L.reference(plug, port, collision=False,
                    note=family+' purchased plug envelope only; verify exact supplied connector/crimp and keyed polarity.')
        plug['wiring_object'] = True
        plug['connector_envelope_provisional'] = True
    wire_end = _empty(name+' / wire exit', port, (0,0,envelope[2] if used else 0))
    wire_end['wiring_role'] = 'cable_endpoint'
    wire_end['connector_port'] = port.name
    straight = _empty(name+' / straight strain relief', port, (0,0,27))
    # Rearward free space keeps the bundle behind the horn/pinion tooth plane.
    if is_ax:
        if case['motor_id']=='J1_BASE':
            straight.location.z=18.3
            far = _empty(name+' / rear service guide', case,
                         (xyz[0],-23.17,-52.7),rot)
            turn = _empty(name+' / horizontal base exit',case,(xyz[0],-45.17,-52.7),rot)
        else:
            straight.location.z=15
            if case['motor_id']=='GRIP':
                straight.location.z=19
                far = _empty(name+' / rear service guide',port,(-8,12,31.3))
                turn = _empty(name+' / broad rear bend',port,(-8,45,31.3))
            else:
                far = _empty(name+' / rear service guide',port,(0,12,23))
                turn = _empty(name+' / broad rear bend',port,(0,45,23))
    else:
        sign=-1 if side==0 else 1
        straight.location.z=14
        ydir=-1 if case['motor_id']=='E_XM' and side==1 else 1
        fy,ty=(70,100) if ydir==-1 else (10,55)
        far = _empty(name+' / side rear service guide',case,(sign*42,ydir*fy,-29.875),rot)
        turn = _empty(name+' / broad side bend',case,(sign*42,ydir*ty,-90),rot)
    return dict(port=port, end=wire_end, straight=straight, far=far, turn=turn, family=family)


def _bridge_anchor(name, a, b, fraction, offset=(0,0,0), frame=None):
    """Weighted moving endpoints plus a rotating route offset, all native drivers."""
    o = _empty(name)
    offset_origin = _empty(name+' / offset origin', frame)
    offset_tip = _empty(name+' / offset vector', frame, offset)
    for axis in range(3):
        d = o.driver_add('location', axis).driver
        d.type = 'SCRIPTED'
        for variable, obj in [('a',a), ('b',b), ('r',offset_origin), ('s',offset_tip)]:
            v = d.variables.new();v.name=variable;v.type='TRANSFORMS'
            v.targets[0].id=obj;v.targets[0].transform_type=['LOC_X','LOC_Y','LOC_Z'][axis]
            v.targets[0].transform_space='WORLD_SPACE'
        d.expression = f'a*{1-fraction:.8f}+b*{fraction:.8f}+s-r'
    return o


def _bundle(hid, source, dest, guides, mats, manifest):
    anchors = [source['end'], source['straight'], source['far']]
    if source.get('turn'):anchors.append(source['turn'])
    anchors.extend(guides)
    if dest.get('turn'):anchors.append(dest['turn'])
    anchors.extend([dest['far'],dest['straight'],dest['end']])
    centre = _curve(hid+' / route centre', anchors, 0, None, hid, 'CENTRE', True)
    # Two native parallel-transport chains remove guide-axis flips. Both chains
    # share the local Y tangent and differ only in twist; interpolate that twist
    # to satisfy the actual pin-row orientation at both purchased connectors.
    tangents=[]
    for j,guide in enumerate(anchors):
        tangent=_empty(hid+f' / conductor tangent {j:02d}')
        for axis in range(3):
            d=tangent.driver_add('location',axis).driver;d.type='SCRIPTED'
            for key,target in [('p',guide),('a',anchors[max(0,j-1)]),('b',anchors[min(len(anchors)-1,j+1)])]:
                v=d.variables.new();v.name=key;v.type='TRANSFORMS';v.targets[0].id=target
                v.targets[0].transform_type=['LOC_X','LOC_Y','LOC_Z'][axis];v.targets[0].transform_space='WORLD_SPACE'
            d.expression='p+b-a'
        tangents.append(tangent)
    def copy_rotation(owner,target,influence=1.0):
        c=owner.constraints.new('COPY_ROTATION');c.target=target
        c.target_space='WORLD';c.owner_space='WORLD';c.mix_mode='REPLACE';c.influence=influence
    def transport(reverse):
        frames=[None]*len(anchors);last=dest['port'] if reverse else source['port']
        for j in (reversed(range(len(anchors))) if reverse else range(len(anchors))):
            frame=_empty(hid+f' / transport {"back" if reverse else "forward"} {j:02d}',anchors[j])
            copy_rotation(frame,last)
            track=frame.constraints.new('DAMPED_TRACK');track.target=tangents[j];track.track_axis='TRACK_Y'
            frames[j]=frame;last=frame
        return frames
    forward,back=transport(False),transport(True)
    sections=[]
    for j,guide in enumerate(anchors):
        section=_empty(hid+f' / conductor section {j:02d}',guide)
        if j==0:copy_rotation(section,source['port'])
        elif j==len(anchors)-1:copy_rotation(section,dest['port'])
        else:
            copy_rotation(section,forward[j]);copy_rotation(section,back[j],j/(len(anchors)-1))
        sections.append(section)
    wires=[]
    for i,(signal,color) in enumerate(PINOUT):
        pin_anchors=[]
        for j,guide in enumerate(sections):
            # 2.5 mm connector pitch; intermediate default1.8 with explicit
            # per-guide wider layup where actual strand clearance requires it.
            pitch=2.5 if j in [0,len(anchors)-1] else float(anchors[j].get('bundle_pitch_mm',1.8))
            pin_anchors.append(_empty(hid+f' / {signal} anchor {j:02d}',guide,((i-1)*pitch,0,0)))
        wires.append(_curve(hid+' / '+signal,pin_anchors,.72,mats[color],hid,signal))
    adapter = source['family'] != dest['family']
    entry=dict(id=hid,source_port=source['port'].name,destination_port=dest['port'].name,
               source_motor_id=source['port'].get('motor_id','U2D2' if source['port'].name.startswith('U2D2') else 'POWER_INJECTION'),
               destination_motor_id=dest['port'].get('motor_id','POWER_INJECTION'),
               source_endpoint=source['end'].name,destination_endpoint=dest['end'].name,
               source_connector=source['family'],destination_connector=dest['family'],
               adapter_required=adapter,curve=centre.name,wires=[o.name for o in wires],
               pinout={'1':'GND','2':'VDD','3':'DATA'},wire_diameter_model_mm=1.44,
               wire_gauge_reference='ROBOTIS 21 AWG; insulation diameter is a provisional routing assumption',
               route_anchor_names=[a.name for a in anchors],provisional_cut_length_mm=None,
               guide_bundle_pitch_mm=[2.5 if i in [0,len(anchors)-1] else float(a.get('bundle_pitch_mm',1.8)) for i,a in enumerate(anchors)],
               conductor_frame_method='Native forward/backward parallel transport using COPY_ROTATION and DAMPED_TRACK constraints; endpoint pin rows retained',
               status='Kinematic routing reference; connector plug engagement and selected cable bend specification provisional')
    manifest['harnesses'].append(entry)
    return centre


def _fixed_port(name, xyz, outward, family='JST EHR-03'):
    width=(0,1,0) if abs(outward[0])>.5 else (1,0,0)
    p=_empty(name,None,xyz,_orientation(width,outward))
    p['port_role']='electronics_ttl_connector';p['connector_family']=family
    p['datum_source']='Base-layout service datum; exact selected electronics socket depth must be measured'
    end=_empty(name+' / wire exit',p,(0,0,5))
    straight=_empty(name+' / straight',p,(0,0,18))
    far=_empty(name+' / free bend',p,(0,0,38))
    return dict(port=p,end=end,straight=straight,far=far,family=family)


def _fixed_jacket(hid,points,radius,mat,signal):
    anchors=[_empty(hid+f' guide{i}',None,p) for i,p in enumerate(points)]
    return _curve(hid,anchors,radius,mat,hid,signal)


def build_wiring(B):
    """Call after base and arm; optional B.WIRING_GUIDES overrides bridge paths.

    WIRING_GUIDES[harness_id] = [(parent_object, (local_x,local_y,local_z)),...]
    is an explicit set of interior control points, between the source and
    destination connector service guides. The caller owns physical channel
    attachments; base-module split saddles are already modelled separately.
    """
    # Delete the old decorative cable collection contents only, not purchased
    # motor meshes, studio labels, or the new base's printable clamp parts.
    for o in list(bpy.context.scene.objects):
        if not (o.get('wiring_object') or o.name in L.cables.objects):continue
        bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.view_layer.update()
    cases={o['motor_id']:o for o in bpy.context.scene.objects
           if o.get('interface_role')=='case' and o.get('motor_id') in CHAIN}
    assert set(cases)==set(CHAIN),f'Missing actual motor case: {set(CHAIN)-set(cases)}'
    ports={key:[_connector(cases[key],side,B.M['ivory']) for side in [0,1]] for key in CHAIN}
    # Elbow cable clears the full output cheek before bending to the rear.
    ports['E_XM'][1]['far'].location=(101.83,-45.56,-29.875)
    ports['E_XM'][1]['straight'].location.z=18
    ports['E_XM'][1]['turn'].location=(17.17,-121.88,-145.99)
    ports['J4_AX'][0]['far'].location=(0,7.03,26.31)
    ports['J4_AX'][0]['turn'].location=(0,27.65,42.52)
    manifest=dict(revision='R06',topology='Parallel half-duplex 3-pin TTL electrical bus with serial physical daisy-chain routing',
                  controller='U2D2 USB-to-TTL communication master; not a motor power supply',
                  motor_order=CHAIN,pinout={'1':'GND','2':'VDD','3':'DATA'},
                  source_urls=SOURCES,harnesses=[],connector_datums=[])
    for key in CHAIN:
        for port in ports[key]:
            p=port['port']
            manifest['connector_datums'].append(dict(name=p.name,motor=key,
                local_matrix=[list(row) for row in p.matrix_basis],source=p['datum_source'],
                family=p['connector_family'],hidden_contact_depth_verified=False))

    # Base electronics are kept clear of the separate front accessory reserve.
    u2d2=_fixed_port('U2D2 TTL 3-pin',(-84,59,15.45),(0,1,0))
    u2d2['straight'].location.z=12
    u2d2['far'].location.z=22
    hub_input=_fixed_port('POWER INJECTION / TTL IN',(72,70,24),(-1,0,0))
    hub_output=_fixed_port('POWER INJECTION / TTL OUT',(72,52,24),(-1,0,0))
    yaw=L.JOINTS.get('J1')
    base_routes={}
    if (ROOT/'base_wiring_guides.py').exists():
        from base_wiring_guides import configure_base_routes
        base_routes=configure_base_routes(ports,u2d2,hub_input,hub_output,yaw,B)
    gripper_routes={}
    if (ROOT/'upper_link_wiring_guides.py').exists():
        from upper_link_wiring_guides import configure_upper_link_route
        gripper_routes['H03_J2_J3']=configure_upper_link_route(ports,cases,B)
    if (ROOT/'wrist_wiring_guides.py').exists():
        from wrist_wiring_guides import configure_wrist_route
        gripper_routes['H05_J4_J5']=configure_wrist_route(ports,cases,B)
    if (ROOT/'gripper_wiring_guides.py').exists():
        from gripper_wiring_guides import configure_gripper_route
        gripper_routes['H06_J5_GRIP']=configure_gripper_route(ports,cases,B)
    proxy=L.cube('POWER INJECTION / unselected module envelope',(24,30,10),(84,60,24),B.M['black'],1)
    L.reference(proxy,collision=False,note='Generic power-junction visual envelope, not selected or manufacturer-certified hardware. Separate base plate reserves45x35x22mm; actual fuse, current rating, connector and mounting dimensions must be selected.')
    proxy['wiring_object']=True;proxy['electrical_hardware_provisional']=True
    fixed=[_empty('Hub data route rear-left',None,(-62,84,24)),
           _empty('Hub data route rear cross',None,(0,84,24)),
           _empty('Hub data route rear-right',None,(34,84,24))]
    _bundle('H00_U2D2_POWER',u2d2,hub_input,base_routes.get('H00_U2D2_POWER',fixed),B.M,manifest)
    _bundle('H01_POWER_J1',hub_output,ports['J1_BASE'][0],
            base_routes.get('H01_POWER_J1',[_empty('Power bus right corridor',None,(65,15,20)),
             _empty('Power bus J1 approach',None,(56,-45,12.3))]),B.M,manifest)

    names=['H02_J1_J2','H03_J2_J3','H04_J3_J4','H05_J4_J5','H06_J5_GRIP']
    overrides=getattr(B,'WIRING_GUIDES',{})
    for n,(a,b,hid) in enumerate(zip(CHAIN[:-1],CHAIN[1:],names)):
        src,dst=ports[a][1],ports[b][0]
        if hid in overrides:
            guides=[_empty(hid+f' channel guide{i}',parent,xyz)
                    for i,(parent,xyz) in enumerate(overrides[hid])]
        elif hid in base_routes:
            guides=base_routes[hid]
        elif hid in gripper_routes:
            guides=gripper_routes[hid]
        elif n==0:
            # Fixed-to-yaw transition travels through the real Ø14 hollow shaft.
            guides=[_empty(hid+' floor loop 1',None,(15,-58,13)),
                    _empty(hid+' floor loop 2',None,(-28,-45,15)),
                    _empty(hid+' below shaft',None,(-28,0,16)),
                    _empty(hid+' shaft lower',None,(-28,0,38)),
                    _empty(hid+' shaft lower tangent 1',None,(-28,0,50)),
                    _empty(hid+' shaft lower tangent 2',None,(-28,0,65)),
                    _empty(hid+' shaft middle',yaw,(0,0,90)),
                    _empty(hid+' shaft upper tangent',yaw,(0,0,118)),
                    _empty(hid+' shaft upper',yaw,(0,0,133)),
                    _empty(hid+' yaw service loop',yaw,(-65,85,149))]
        elif hid=='H04_J3_J4':
            guides=[_bridge_anchor(hid+' outer forearm loop 1',src['turn'],dst['turn'],.33,(-45.37,-130,-20.01),cases['J4_AX']),
                    _bridge_anchor(hid+' outer forearm loop 2',src['turn'],dst['turn'],.67,(-45.37,-130,-20.01),cases['J4_AX'])]
        elif hid=='H05_J4_J5':
            guides=[_bridge_anchor(hid+' pitch service loop 1',src['turn'],dst['turn'],.33,(0,0,-65),cases['J4_AX']),
                    _bridge_anchor(hid+' pitch service loop 2',src['turn'],dst['turn'],.67,(0,0,-65),cases['J4_AX'])]
        else:
            frame=cases[a]
            guides=[_bridge_anchor(hid+' service loop 1',src['turn'],dst['turn'],.33,(0,10,-14),frame),
                    _bridge_anchor(hid+' service loop 2',src['turn'],dst['turn'],.67,(0,10,-14),frame)]
        if hid=='H04_J3_J4':
            for guide in [src['straight'],src['far'],src['turn'],*guides,dst['turn'],dst['far'],dst['straight']]:
                guide['bundle_pitch_mm']=2.4
        _bundle(hid,src,dst,guides,B.M,manifest)

    # Cable jackets pass through the two actual split saddle centres and ports.
    # Repeated collinear controls keep the straight clamp/port spans straight.
    usb=[(-84,11,15.45),(-84,-12,15.45),(-108,-12,18),(-108,52,25),
         (-84,79,28),(-84,93,28),(-84,98,28),(-84,108,28),(-84,118,28),(-84,139,28),(-116,160,7)]
    power=[(84,72,24),(84,86,24),(84,93,24),(84,98,24),(84,108,24),(84,118,24),(84,142,24),(120,162,7)]
    if (ROOT/'fixed_jacket_guides.py').exists():
        from fixed_jacket_guides import configure_fixed_jackets
        jackets=configure_fixed_jackets()
        usb=jackets.get('USB',usb);power=jackets.get('EXTERNAL_DC',power)
    _fixed_jacket('USB cable / PC to U2D2',usb,2.35,B.M['black'],'USB')
    _fixed_jacket('External DC supply / fused injection',power,2.8,B.M['black'],'EXTERNAL_DC')
    bpy.context.view_layer.update()
    manifest['electrical_design_notes']=[
        'All motors are parallel electrical loads/addressed peers; physical cable order is not series electrical power.',
        'AX defaults Protocol1; XM defaults Protocol2. Use unique IDs and common baud; send model-specific packets sequentially.',
        'U2D2 does not supply motor power. External regulated supply, protective fuse/current limit and shared GND are required.',
        '12V sum of published stalls is10.6A. This is not a cable/connector continuous rating; a single21AWG trunk must not be assumed adequate.',
        'Connector plug envelopes and hidden mating depths need physical measurement; side/rear exits follow official CAD.',
        'Routing is kinematic and variable-length; provisional cable cut lengths come from sampled maximum route length plus slack, not a flex-life proof.']
    (ROOT/'wiring-connectivity.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    text=bpy.data.texts.get('WIRING CONNECTIVITY — R06') or bpy.data.texts.new('WIRING CONNECTIVITY — R06')
    text.clear();text.write(json.dumps(manifest,indent=2))
    return manifest


def sample_nurbs(spline,count=121):
    """Clamped uniform unit-weight B-spline samples matching our route curves."""
    points=[Vector(p.co[:3]) for p in spline.points]
    degree=spline.order_u-1;n=len(points)-1
    knots=[0.]*(degree+1)+[float(i) for i in range(1,n-degree+1)]+[float(n-degree+1)]*(degree+1)
    end=knots[-1];result=[]
    for j in range(count):
        t=end*j/(count-1)
        if j==count-1:result.append(points[-1].copy());continue
        k=next(i for i in range(degree,n+1) if knots[i]<=t<knots[i+1])
        d=[points[k-degree+i].copy() for i in range(degree+1)]
        for r in range(1,degree+1):
            for i in range(degree,r-1,-1):
                left=knots[k-degree+i];right=knots[k+1+i-r]
                alpha=(t-left)/(right-left) if right!=left else 0
                d[i]=d[i-1]*(1-alpha)+d[i]*alpha
        result.append(d[degree])
    return result


def audit_wiring(scene=None,frames=None,output=None):
    """Check native driver endpoints, path length and geometric bend radii.

    Collision checks use actual printed-part and motor-case triangles separately
    from the rigid assembly auditor. This report does not infer cable fatigue.
    """
    from mathutils.bvhtree import BVHTree
    import numpy as np
    scene=scene or bpy.context.scene
    frames=frames or [round(1+i*359/30) for i in range(31)]
    curves=[o for o in scene.objects if o.type=='CURVE' and o.get('conductor') in ['CENTRE','GND','VDD','DATA']]
    structures=[o for o in scene.objects if o.type=='MESH' and
                (o.get('part_id') or o.get('interface_role')=='case')]
    records={o.name:dict(harness=o['harness_id'],conductor=o['conductor'],lengths_mm=[],minimum_bend_radius_mm=1e9,
                        endpoint_max_error_mm=0.,gear_surface_clearance_mm=1e9,gear_intrusions=[],structural_contacts=[],
                        minimum_structural_surface_clearance_mm=1e9,
                        minimum_strand_center_spacing_mm=1e9 if o['conductor']=='CENTRE' else None) for o in curves}
    oldframe=scene.frame_current
    for frame in frames:
        scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
        gear_trees=[]
        for gear in structures:
            g=gear.evaluated_get(deps);m=g.to_mesh();m.calc_loop_triangles()
            verts=[g.matrix_world@v.co for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles]
            lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)))
            hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
            local_lo=Vector(tuple(min(v.co[i] for v in m.vertices) for i in range(3)))
            local_hi=Vector(tuple(max(v.co[i] for v in m.vertices) for i in range(3)))
            isgear=any(s in gear.name.lower() for s in ['pinion','module','yaw_60','yaw_gear'])
            gear_trees.append((gear.name,BVHTree.FromPolygons(verts,faces,all_triangles=True),lo,hi,isgear,
                               g.matrix_world.inverted(),local_lo,local_hi))
            g.to_mesh_clear()
        for o in curves:
            ev=o.evaluated_get(deps);s=ev.data.splines[0]
            points=sample_nurbs(s,121);rec=records[o.name]
            names=json.loads(o['curve_anchor_names_json'])
            for p,name in [(points[0],names[0]),(points[-1],names[-1])]:
                expected=bpy.data.objects[name].evaluated_get(deps).matrix_world.translation
                rec['endpoint_max_error_mm']=max(rec['endpoint_max_error_mm'],(p-expected).length)
            rec['lengths_mm'].append(sum((b-a).length for a,b in zip(points,points[1:])))
            for i,(a,b,c) in enumerate(zip(points,points[1:],points[2:])):
                cross=(b-a).cross(c-a).length
                if cross>1e-8:
                    r=(a-b).length*(b-c).length*(c-a).length/(2*cross)
                    if r<rec['minimum_bend_radius_mm']:
                        rec['minimum_bend_radius_mm']=r
                        rec['minimum_bend_location']=dict(frame=frame,sample=i+1,xyz=list(b))
            if o['conductor']=='CENTRE':
                siblings=[c for c in curves if c['harness_id']==o['harness_id'] and c['conductor'] in ['GND','VDD','DATA']]
                conductor_paths=[sample_nurbs(c.evaluated_get(deps).data.splines[0],121) for c in siblings]
                spacing_paths=[np.asarray(sample_nurbs(c.evaluated_get(deps).data.splines[0],241)) for c in siblings]
                for a in range(len(spacing_paths)):
                    for b in range(a+1,len(spacing_paths)):
                        for p,q in [(spacing_paths[a],spacing_paths[b]),(spacing_paths[b],spacing_paths[a])]:
                            segment=q[1:]-q[:-1];delta=p[:,None,:]-q[None,:-1,:]
                            fraction=np.clip(np.einsum('ijk,jk->ij',delta,segment)/np.maximum(np.einsum('ij,ij->i',segment,segment),1e-12),0,1)
                            distances=np.linalg.norm(delta-fraction[:,:,None]*segment[None,:,:],axis=2)
                            index=np.unravel_index(distances.argmin(),distances.shape);distance=float(distances[index])
                            if distance<rec['minimum_strand_center_spacing_mm']:
                                rec['minimum_strand_center_spacing_mm']=distance
                                rec['minimum_strand_spacing_location']=dict(frame=frame,point=[float(v) for v in p[index[0]]],
                                    closest=[float(v) for v in q[index[1]]+fraction[index]*segment[index[1]]],
                                    conductor_pair=[siblings[a]['conductor'],siblings[b]['conductor']])
                bundle_radii=[max(((path[i]-p).length+.72 for path in conductor_paths),default=2.52)
                              for i,p in enumerate(points)]
                endpoint_exclusions=[]
                for endpoint_name in [names[0],names[-1]]:
                    endpoint=bpy.data.objects[endpoint_name]
                    port=endpoint.parent
                    case=port.parent if port else None
                    if case and case.get('interface_role')=='case':
                        pm=port.evaluated_get(deps).matrix_world
                        endpoint_exclusions.append((case.name,endpoint.evaluated_get(deps).matrix_world.translation,
                                                    pm.translation,pm.to_3x3()@Vector((0,0,1))))
                for gearname,tree,lo,hi,isgear,inverse,local_lo,local_hi in gear_trees:
                    for i,p in enumerate(points):
                        # The purchased dummy CAD does not resolve the internal
                        # plug/socket engagement. Exclude only the measured
                        # endpoint's immediate connector service region.
                        endpoint_region=any(gearname==case_name and (p-exit_point).length<18 and
                                            (p-mouth).dot(outward)>=-.001
                                            for case_name,exit_point,mouth,outward in endpoint_exclusions)
                        if endpoint_region:continue
                        boxdist=math.sqrt(sum(max(lo[k]-p[k],0,p[k]-hi[k])**2 for k in range(3)))
                        if boxdist>8:continue
                        result=tree.find_nearest(p)
                        if not result or result[0] is None:continue
                        closest,normal,_,distance=result
                        signed=(p-closest).dot(normal)
                        inside=False
                        local_p=inverse@p
                        if all(local_lo[k]<local_p[k]<local_hi[k] for k in range(3)):
                            votes=[]
                            for direction in [( .873,.373,.313),(.277,.919,.280),(.199,.301,.932)]:
                                ray=Vector(direction).normalized();origin=p.copy();hits=0
                                for _ in range(60):
                                    hit=tree.ray_cast(origin,ray,5000)
                                    if hit[0] is None:break
                                    hits+=1;origin=hit[0]+ray*.001
                                votes.append(hits%2==1)
                            inside=sum(votes)>=2
                        clearance=distance-bundle_radii[i]
                        rec['minimum_structural_surface_clearance_mm']=min(rec['minimum_structural_surface_clearance_mm'],clearance)
                        if isgear:rec['gear_surface_clearance_mm']=min(rec['gear_surface_clearance_mm'],clearance)
                        if inside or clearance<.5:
                            contact=dict(frame=frame,part=gearname,sample=i,
                                    clearance_mm=clearance,bundle_radius_mm=bundle_radii[i],signed_distance_mm=signed,inside=inside,xyz=list(p))
                            if len(rec['structural_contacts'])<30:rec['structural_contacts'].append(contact)
                            if isgear and len(rec['gear_intrusions'])<12:rec['gear_intrusions'].append(contact)
    scene.frame_set(oldframe);bpy.context.view_layer.update()
    for rec in records.values():
        lengths=rec.pop('lengths_mm')
        rec['length_min_mm']=min(lengths);rec['length_max_mm']=max(lengths)
        rec['variation_mm']=max(lengths)-min(lengths)
        rec['provisional_cut_length_mm']=math.ceil((max(lengths)*1.12+20)/10)*10
        rec['bend_radius_target_mm']=12.0
        rec['bend_target_met']=rec['minimum_bend_radius_mm']>=12
        rec['structural_screen_method']='Enclosing evaluated three-conductor bundle' if rec['conductor']=='CENTRE' else 'Included in its harness enclosing-bundle screen'
        if rec['conductor']!='CENTRE':
            rec['minimum_structural_surface_clearance_mm']=None
            rec['gear_surface_clearance_mm']=None
    report=dict(revision='R06',frames=frames,curves=records,
                connector_exclusion_scope='Only the actual source/destination manufacturer case, within18mm of that case connector wire exit and in the outward half-space of that port mouth. No printed parts or other motor cases are excluded.',
                collision_bundle_radius='At each sampled station: maximum actual evaluated conductor offset from centreline plus0.72mm insulation radius. Terminal pitch is2.5mm (3.22mm endpoint radius); intermediate pitch defaults to1.8mm with explicit per-guide overrides up to3.0mm. Exact pitches are recorded in wiring-connectivity.json.',
                endpoints_attached=all(r['endpoint_max_error_mm']<.02 for r in records.values()),
                gear_route_clear=all(not r['gear_intrusions'] for r in records.values()),
                structure_route_clear=all(not r['structural_contacts'] for r in records.values()),
                all_bends_at_least_12mm=all(r['bend_target_met'] for r in records.values()),
                strands_separated=all(r['minimum_strand_center_spacing_mm']>=1.44 for r in records.values() if r['conductor']=='CENTRE'),
                strand_spacing_scope='Within each harness: minimum bidirectional sampled point-to-polyline distance at241 stations per conductor pair; insulation outside diameter1.44mm. Different harnesses and exhaustive continuous/self-contact cable dynamics are not covered by this metric.',
                screened_mesh_categories='Printed parts and official motor case meshes. Interior classification requires evaluated local bounds and majority of three independent ray-parity directions. Standard fastener meshes are covered by the separate mechanical auditor, not this TTL bundle screen.',
                limitation='Discrete kinematic route screen only; connector keying, plug fit, continuous swept collision, constant cable length, strain and flex life require physical checks.')
    (Path(output) if output else ROOT/'wiring-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report







