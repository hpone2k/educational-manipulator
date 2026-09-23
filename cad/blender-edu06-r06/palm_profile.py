"""Single planar, layered gripper palm; avoids coplanar rib-union artifacts."""
import math
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
import blender_lib as L
from reducer_cheek import circle,_inside


def make_palm(rear,end_y,rounded_rect,mat):
    ends=[(x,y) for x in (-32,32) for y in (-end_y,end_y)]
    motors=[(x,y) for x in (-21,21) for y in (15.5,-42.5)]
    interface=[(24,0),(0,24),(-24,0),(0,-24)]
    mounts=ends+motors+interface
    regions={'outer':rounded_rect(74,122.7,6),'inner':rounded_rect(66,114.7,3),
             'rim':circle(0,0,17),'ribX':rounded_rect(58,10,5),'ribY':rounded_rect(10,58,5),
             'centre':circle(0,0,13,n=48),
             'service':L.rounded_profile(20,10,1,(0,-15))}
    ribs=['rim','ribX','ribY']
    for sx in (-1,1):
        key='motor'+str(sx)
        regions[key]=[(sx*21-3.5,-47.1),(sx*21+3.5,-47.1),(sx*21+3.5,20.1),(sx*21-3.5,20.1)]
        ribs.append(key)
        for i,(ym,yc) in enumerate([(15.5,end_y),(-42.5,-end_y)]):
            ax,ay,bx,by=sx*21,ym,sx*32,yc
            length=math.hypot(bx-ax,by-ay);nx,ny=-(by-ay)*2/length,(bx-ax)*2/length
            key='diagonal'+str(sx)+'_'+str(i)
            regions[key]=[(ax+nx,ay+ny),(bx+nx,by+ny),(bx-nx,by-ny),(ax-nx,ay-ny)]
            # CDT expects counterclockwise face loops.
            regions[key].reverse();ribs.append(key)
        key='bypass'+str(sx)
        regions[key]=L.hull_circles([(0,-24,5.5),(sx*21,-33,4)]);ribs.append(key)
    for i,(x,y) in enumerate(mounts):
        regions['boss'+str(i)]=circle(x,y,5.5,n=48)
        regions['hole'+str(i)]=circle(x,y,1.7,n=48)
    vertices=[];faces=[]
    for polygon in regions.values():
        # Normalize winding independently for every constraint loop.
        area=sum(polygon[i][0]*polygon[(i+1)%len(polygon)][1]-polygon[(i+1)%len(polygon)][0]*polygon[i][1] for i in range(len(polygon)))
        polygon=polygon if area>0 else list(reversed(polygon))
        start=len(vertices);vertices.extend(Vector(p) for p in polygon);faces.append(list(range(start,len(vertices))))
    coords,_,triangles,_,_,_=delaunay_2d_cdt(vertices,[],faces,0,1e-6,False)
    selected=[]
    for tri in triangles:
        centre=tuple(sum(coords[v][i] for v in tri)/len(tri) for i in range(2))
        inside={key:_inside(centre,p) for key,p in regions.items()}
        if inside['centre'] or inside['service'] or any(inside['hole'+str(i)] for i in range(len(mounts))):continue
        boss=any(inside['boss'+str(i)] for i in range(len(mounts)))
        frame=(inside['outer'] and not inside['inner']) or any(inside[k] for k in ribs)
        if not (boss or frame):continue
        tri=tuple(tri);a,b,c=[coords[v] for v in tri]
        if (b-a).cross(c-a)<0:tri=tuple(reversed(tri))
        selected.append((tri,2 if boss else 1))
    levels=[rear,rear+4,rear+6];mesh_vertices=[];mesh_faces=[];lookup={};edges={}
    def vertex(index,level):
        key=(index,level)
        if key not in lookup:
            lookup[key]=len(mesh_vertices);p=coords[index];mesh_vertices.append((float(p.x),float(p.y),levels[level]))
        return lookup[key]
    for tri,height in selected:
        mesh_faces.append(tuple(vertex(v,0) for v in reversed(tri)))
        mesh_faces.append(tuple(vertex(v,height) for v in tri))
        for a,b in zip(tri,tri[1:]+tri[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append((a,b,height))
    for adjacent in edges.values():
        if len(adjacent)>2:raise ValueError('Invalid planar palm edge multiplicity')
        adjacent.sort(key=lambda edge:edge[2]);high=adjacent[-1]
        low=adjacent[0][2] if len(adjacent)==2 else 0
        a,b,height=high
        for level in range(low,height):
            mesh_faces.append((vertex(a,level),vertex(b,level),vertex(b,level+1),vertex(a,level+1)))
    mesh=bpy.data.meshes.new('layered gripper palm');mesh.from_pydata(mesh_vertices,[],mesh_faces);mesh.update()
    palm=bpy.data.objects.new('layered gripper palm',mesh);bpy.context.scene.collection.objects.link(palm)
    mesh.materials.append(mat)
    for x,y in motors+ends:L.hexhole(palm,(x,y,-49.6),5.8,2.9)
    for x,y in mounts:L.FEATURES.append({'part':palm.name,'centre_mm':[x,y,-47.95],'diameter_mm':3.4,'axis':'Z'})
    return palm
