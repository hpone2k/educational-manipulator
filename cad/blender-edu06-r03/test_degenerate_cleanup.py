import bpy,bmesh,json,traceback,sys,struct,math,collections
from pathlib import Path
from mathutils import Euler,Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import mesh_repair
out={}
def stats(bm):
    points=[v.co for v in bm.verts];lo=Vector(tuple(min(v[i] for v in points) for i in range(3)));hi=Vector(tuple(max(v[i] for v in points) for i in range(3)));shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
    zero=[];ec=collections.Counter()
    for face in bm.faces:
        vs=[tuple(struct.unpack('<3f',struct.pack('<3f',*(v.co+shift)))) for v in face.verts]
        if len(vs)!=3:continue
        a,b,c=[Vector(v) for v in vs]
        x1,y1,z1=(float(b[i])-float(a[i]) for i in range(3));x2,y2,z2=(float(c[i])-float(a[i]) for i in range(3));cross=(y1*z2-z1*y2,z1*x2-x1*z2,x1*y2-y1*x2)
        area=math.sqrt(sum(v*v for v in cross))/2
        if area<=5e-11:zero.append(vs)
        cs=[tuple(round(c,4) for c in v) for v in vs]
        for v1,v2 in zip(cs,cs[1:]+cs[:1]):ec[tuple(sorted((v1,v2)))]+=1
    return {'triangles':len(bm.faces),'bad_edges':sum(v!=2 for v in ec.values()),'zero_triangles':len(zero),'zero_examples':zero[:8]}
try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
    o=bpy.data.objects['E_01_rear_support']
    for mode in ['BEAUTY','EAR_CLIP']:
        for dist in [0,1e-7,1e-6,1e-5,.00005,.0001]:
            bm=bmesh.new();bm.from_mesh(o.data);mesh_repair.remove_duplicate_faces(bm)
            bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method=mode)
            if dist:
                bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=dist)
                bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method=mode)
            rot=Euler(tuple(math.radians(v) for v in o['print_rotation_deg'])).to_matrix()
            for v in bm.verts:v.co=rot@v.co
            out[mode+'_'+str(dist)]=stats(bm);bm.free()
except Exception:out['error']=traceback.format_exc()
(ROOT/'mesh-degenerate-tests.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
