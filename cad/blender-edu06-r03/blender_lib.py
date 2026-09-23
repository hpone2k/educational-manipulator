"""EDU06 model utilities. Geometry coordinates and binary STL exports use mm."""
import bpy, bmesh, math, json, struct
from pathlib import Path
from mathutils import Vector, Matrix, Euler

ROOT=Path(__file__).resolve().parent
PRINT=[]; REFS=[]; JOINTS={}; FEATURES=[]

def collection(name):
    c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); return c

def setup():
    global scene, printed, hardware, controls, studio, cables
    scene=bpy.data.scenes.new('EDU06 R03 | Engineering assembly')
    bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=.001
    scene.unit_settings.length_unit='MILLIMETERS'
    printed=collection('01 PRINTED PARTS — individual manufacturing meshes')
    hardware=collection('02 PURCHASED — motors, nuts, screws, electronics')
    controls=collection('03 JOINT CONTROLS — custom properties on CONTROL')
    cables=collection('04 CABLE ROUTING — reference only')
    studio=collection('05 STUDIO — not printable')
    return scene

def recollect(o,c):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o); return o

def active(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o

def apply(o,m):
    active(o); bpy.ops.object.modifier_apply(modifier=m.name)

def T(x=0,y=0,z=0): return Matrix.Translation((x,y,z))
def R(axis,degrees): return Matrix.Rotation(math.radians(degrees),4,axis.upper())

def material(name,color,metal=0,rough=.42,layers=False):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    if layers:
        n=m.node_tree.nodes; l=m.node_tree.links
        tex=n.new('ShaderNodeTexCoord');wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Z'
        wave.inputs['Scale'].default_value=250;wave.inputs['Distortion'].default_value=.08
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.045
        l.new(tex.outputs['Generated'],wave.inputs['Vector']);l.new(wave.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m

def cube(name,size,loc=(0,0,0),mat=None,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Edge radii','BEVEL');b.width=bevel;b.segments=3;apply(o,b)
    if mat:o.data.materials.append(mat)
    return o

def cyl(name,r,d,loc=(0,0,0),axis='Z',mat=None,n=72):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=d,location=loc)
    o=bpy.context.object;o.name=name
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    active(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if mat:o.data.materials.append(mat)
    return o

def poly(name,points,z,depth,mat=None):
    n=len(points);verts=[(x,y,z) for x,y in points]+[(x,y,z+depth) for x,y in points]
    area=sum(points[i][0]*points[(i+1)%n][1]-points[(i+1)%n][0]*points[i][1] for i in range(n))
    if area<0:return poly(name,list(reversed(points)),z,depth,mat)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o)
    if mat:o.data.materials.append(mat)
    return o

def bake(o):
    o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4);return o

def boolean(o,c,kind='DIFFERENCE'):
    if o.get('part_id'):
        c.matrix_world=o.matrix_world@c.matrix_world
    m=o.modifiers.new(kind,'BOOLEAN');m.operation=kind;m.solver='EXACT';m.object=c;apply(o,m)
    bpy.data.objects.remove(c,do_unlink=True);return o

def union(o,c): return boolean(o,c,'UNION')
def hole(o,xyz,d,depth=400,axis='Z'):
    FEATURES.append({'part':o.name,'centre_mm':list(xyz),'diameter_mm':d,'axis':axis})
    return boolean(o,cyl('_cut',d/2,depth,xyz,axis,n=48))
def hexhole(o,xyz,af=5.8,depth=2.8,axis='Z'):
    c=cyl('_nut',af/math.sqrt(3),depth,xyz,axis,n=6); return boolean(o,c)

def ring(name,ro,ri,d,z=0,mat=None):
    o=cyl(name,ro,d,(0,0,z+d/2),mat=mat);return hole(o,(0,0,z+d/2),2*ri,d+2)

def finish(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00005)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00005)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();return o

def attach(o,node=None,tf=None):
    bake(o)
    if node:o.parent=node;o.matrix_parent_inverse=Matrix.Identity(4)
    o.matrix_basis=tf or Matrix.Identity(4);return o

def part(o,code,node=None,tf=None,note='',orient=None):
    finish(o);attach(o,node,tf);o.name=code;recollect(o,printed)
    o['part_id']=code;o['manufacturing']='FDM prototype; fit/strength testing required'
    o['description']=note;o['print_rotation_deg']=orient or [0,0,0];o['rigid_group']=node.name if node else 'FIXED'
    PRINT.append(o);return o

def reference(o,node=None,tf=None,mass=0,note='',collision=False):
    attach(o,node,tf);recollect(o,hardware);o['mass_g']=mass;o['reference_only']=True;o['description']=note;o['collision_check']=collision
    o['rigid_group']=node.name if node else 'FIXED';REFS.append(o);return o

def empty(name,parent=None,tf=None):
    o=bpy.data.objects.new(name,None);controls.objects.link(o);o.empty_display_type='ARROWS';o.empty_display_size=12
    o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=tf or Matrix.Identity(4);return o

def joint(name,parent,tf,controller,prop,lo,hi,home):
    station=empty(name+' DATUM',parent,tf);o=empty(name,station)
    controller[prop]=home;controller.id_properties_ui(prop).update(min=lo,max=hi,soft_min=lo,soft_max=hi,description='Output angle in degrees')
    drive(o,controller,prop,'q*pi/180')
    o['axis']='LOCAL Z';o['limits_deg']=[lo,hi];o['home_deg']=home;JOINTS[prop]=o;return station,o

def drive(o,controller,prop,expression):
    d=o.driver_add('rotation_euler',2).driver;d.type='SCRIPTED';v=d.variables.new();v.name='q';v.type='SINGLE_PROP';v.targets[0].id=controller;v.targets[0].data_path='["'+prop+'"]';d.expression=expression

def bolt(name,node,tf,length,mat,diam=3):
    # Under-head datum z=0, shaft points along -Z. Reference threads intentionally simplified.
    o=cyl(name+' shaft',diam/2,length,(0,0,-length/2),mat=mat,n=24)
    reference(o,node,tf)
    head_d={2:3.8,3:5.5,4:7.0}.get(diam,diam*1.8);head_h=float(diam)
    h=cyl(name+' socket head',head_d/2,head_h,(0,0,head_h/2),mat=mat,n=36)
    boolean(h,cyl('_socket',diam*.45,head_h*.6,(0,0,head_h*.9),n=6));reference(h,node,tf)

def nut(name,node,tf,mat,diam=3):
    af={2:4,3:5.5,4:7}.get(diam,5.5);h={2:1.6,3:2.4,4:3.2}.get(diam,2.4)
    o=cyl(name,af/math.sqrt(3),h,(0,0,h/2),mat=mat,n=6);hole(o,(0,0,h/2),diam,h+1)
    reference(o,node,tf)

def text(name,body,pos,size,mat,rotation=(0,0,0),node=None,col=None):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size;c.extrude=.006;c.align_x='CENTER'
    o=bpy.data.objects.new(name,c);(col or hardware).objects.link(o);o.location=pos;o.rotation_euler=rotation;o.data.materials.append(mat)
    if node:o.parent=node
    return o

def cable(name,points,radius,mat,node=None):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=16;c.bevel_depth=radius;c.bevel_resolution=3
    p=c.splines.new('BEZIER');p.bezier_points.add(len(points)-1)
    for v,co in zip(p.bezier_points,points):v.co=co;v.handle_left_type='AUTO';v.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);cables.objects.link(o);o.data.materials.append(mat);o.parent=node;return o

def mesh_stats(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table()
    vol=0.;cm=Vector((0,0,0))
    for f in bm.faces:
        a,b,c=[v.co for v in f.verts];v=a.dot(b.cross(c))/6;vol+=v;cm+=(a+b+c)*(v/4)
    if abs(vol)>1e-8:cm/=vol
    bad=sum(not e.is_manifold for e in bm.edges);bm.free()
    return vol,cm,bad

def export_parts():
    from mesh_repair import clean_object, prepare_export_bmesh
    folder=ROOT/'prototype_stl';folder.mkdir(exist_ok=True);report=[]
    for o in PRINT:
        clean_object(o)
        bm=prepare_export_bmesh(o,list(o['print_rotation_deg']))
        lo=Vector(tuple(min(v.co[i] for v in bm.verts) for i in range(3)));hi=Vector(tuple(max(v.co[i] for v in bm.verts) for i in range(3)))
        shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
        with (folder/(o['part_id']+'.stl')).open('wb') as f:
            f.write(b'EDU06 R03 millimetres prototype'.ljust(80,b' '));f.write(struct.pack('<I',len(bm.faces)))
            for face in bm.faces:
                vs=[v.co+shift for v in face.verts];n=(vs[1]-vs[0]).cross(vs[2]-vs[0]);n.normalize()
                f.write(struct.pack('<12fH',*n,*vs[0],*vs[1],*vs[2],0))
        bm.free();vol,cm,bad=mesh_stats(o)
        o['solid_PLA_mass_g']=round(vol*.00124,3)
        report.append({'id':o['part_id'],'dimensions_mm':list(hi-lo),'volume_mm3':vol,'solid_PLA_mass_g':vol*.00124,'centroid_local_mm':list(cm),'nonmanifold_edges':bad,'description':o['description']})
    (ROOT/'part-metrics.json').write_text(json.dumps(report,indent=2));(ROOT/'hole-features.json').write_text(json.dumps(FEATURES,indent=2))
    return report
