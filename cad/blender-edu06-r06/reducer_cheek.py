"""Planar reducer cheeks built by constrained triangulation, then extruded.

All dimensions and original interface centres are unchanged. A single planar
region avoids coplanar-face Boolean unions at intersecting circular support webs.
Blender's bundled CDT computes intersections; no external package is required.
"""
import math
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
import blender_lib as L


def circle(x,y,rx,ry=None,n=72):
    ry=rx if ry is None else ry
    return [(x+rx*math.cos(2*math.pi*i/n),y+ry*math.sin(2*math.pi*i/n)) for i in range(n)]


def _inside(point,polygon):
    x,y=point;inside=False
    for i,(ax,ay) in enumerate(polygon):
        bx,by=polygon[(i+1)%len(polygon)]
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:
            inside=not inside
    return inside


def _extrude_region(name,regions,predicate,z,depth,mat):
    """Triangulate all boundaries once; keep precisely the intended 2D solid."""
    vertices=[];faces=[]
    for polygon in regions.values():
        start=len(vertices)
        vertices.extend(Vector(p) for p in polygon)
        faces.append(list(range(start,len(vertices))))
    points,_,triangles,_,_,_=delaunay_2d_cdt(vertices,[],faces,0,1e-6,False)
    selected=[]
    for triangle in triangles:
        centre=tuple(sum(points[v][i] for v in triangle)/len(triangle) for i in range(2))
        if predicate({key:_inside(centre,polygon) for key,polygon in regions.items()}):
            selected.append(tuple(triangle))
    used=sorted({v for triangle in selected for v in triangle})
    remap={old:new for new,old in enumerate(used)}
    points=[points[v] for v in used]
    selected=[tuple(remap[v] for v in triangle) for triangle in selected]
    n=len(points)
    mesh_vertices=[(float(p.x),float(p.y),zz) for zz in (z,z+depth) for p in points]
    mesh_faces=[];edge_count={};oriented={}
    for triangle in selected:
        a,b,c=[points[v] for v in triangle]
        if (b-a).cross(c-a)<0:triangle=tuple(reversed(triangle))
        mesh_faces.extend([tuple(reversed(triangle)),tuple(v+n for v in triangle)])
        for a,b in zip(triangle,triangle[1:]+triangle[:1]):
            key=tuple(sorted((a,b)));edge_count[key]=edge_count.get(key,0)+1;oriented[key]=(a,b)
    for key,count in edge_count.items():
        if count==1:
            a,b=oriented[key];mesh_faces.append((a,b,b+n,a+n))
        elif count!=2:raise ValueError('Nonmanifold planar boundary: '+str(key))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(mesh_vertices,[],mesh_faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj)
    if mat:mesh.materials.append(mat)
    return obj


def make_reducer_cheek(prop,side,z,C,bridge_pts,elbow_ears,mat):
    """Return raw 6mm cheek mesh; caller assigns part ID, parent and note."""
    name='_planar '+prop+' '+side+' cheek'
    regions={'main':circle(0,0,27)}
    positive=['main'];holes=[]
    if side=='rear':
        regions['spine']=L.hull_circles([(-C+15,-27,9),(-12,-22,9)])
        regions['mount']=L.hull_circles([(-C+x,y,5.5) for x in [-19.25,19.25] for y in [-39.25,15.25]]+
                                      [(-C+x,y,6) for x,y in bridge_pts])
        regions['motor_window']=circle(-C,-12,12,17)
        positive.extend(['spine','mount'])
        holes.extend([(-C+x,y,3.4) for x in [-19.25,19.25] for y in [-39.25,15.25]])
        holes.extend([(-C+x,y,3.4) for x,y in bridge_pts])
    else:
        regions['motor_clearance']=L.rounded_profile(49,65,1,(-C,-12),steps=3)
    if prop=='J3':
        for i,(ex,ey) in enumerate(elbow_ears):
            key='ear'+str(i);regions[key]=L.hull_circles([(0,-21,9),(ex,ey,8)])
            positive.append(key);holes.append((ex,ey,3.4))
    if prop=='J2':
        regions['pedestal']=L.hull_circles([(-25,-58.5,4.5),(25,-58.5,4.5),(-15,-16,9),(15,-16,9)])
        regions['pedestal_window']=circle(0,-43,14,8)
        positive.append('pedestal');holes.extend([(-25,-58.5,3.4),(25,-58.5,3.4)])
    pcd=[(22*math.cos(math.pi/4+i*math.pi/2),22*math.sin(math.pi/4+i*math.pi/2),3.4) for i in range(4)]
    holes.extend(pcd)
    holes.append((0,0,34.3 if prop=='J2' else 30.3))
    for i,(x,y,d) in enumerate(holes):
        regions['hole'+str(i)]=circle(x,y,d/2,n=48)
        L.FEATURES.append({'part':name,'centre_mm':[x,y,z+3],'diameter_mm':d,'axis':'Z'})
    def solid(inside):
        main=inside['main'] and not inside.get('motor_clearance',False)
        mount=inside.get('mount',False) and not inside.get('motor_window',False)
        pedestal=inside.get('pedestal',False) and not inside.get('pedestal_window',False)
        structural=main or mount or pedestal or inside.get('spine',False) or any(inside.get('ear'+str(i),False) for i in range(len(elbow_ears)))
        return structural and not any(inside['hole'+str(i)] for i in range(len(holes)))
    cheek=_extrude_region(name,regions,solid,z,6,mat)
    # Only depth-limited captive pockets remain 3D subtractions; there are no
    # coplanar positive-solid unions to introduce internal duplicate patches.
    if side=='rear':
        for x,y in bridge_pts:L.hexhole(cheek,(-C+x,y,-23.7),5.8,3.0)
    if prop=='J3' and side=='front':
        for x,y,_ in pcd:L.hexhole(cheek,(x,y,23.7),5.8,3.0)
    return cheek
