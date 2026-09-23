import bpy,bmesh,sys,json,traceback,textwrap,math,struct
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import blender_lib as L
from blender_lib import cube,cyl,union,hole,hexhole,boolean,T,R
from mesh_repair import clean_object,prepare_export_bmesh
out={}
def pcd(n,r,phase=0):return [(r*math.cos(phase+2*math.pi*i/n),r*math.sin(phase+2*math.pi*i/n)) for i in range(n)]
def holes(o,points,z,d=3.4,depth=300):
    for x,y in points:hole(o,(x,y,z),d,depth)
    return o
def add_part(o,code,node=None,tf=None,note='',orient=None):return L.part(o,code,node,tf,note,orient)
def screw_pattern(*a,**k):pass
try:
    source=(ROOT/'build_edu06.py').read_text(encoding='utf-8')
    snippet=textwrap.dedent(source[source.index("    floor=cube('Base floor'"):source.index('    # Lower stand:')])
    for mode in ['through_cap']:
        L.setup();M={'green':L.material(mode,(.1,.2,.1))}
        code=snippet
        if mode=='through_cap':code=code.replace('hexhole(floor,(x,y,88.6),5.8,2.8)','hexhole(floor,(x,y,88.7),5.8,3.0)')
        env=dict(globals());env['M']=M
        exec(code,env)
        floor=env['floor'];bm=bmesh.new();bm.from_mesh(floor.data)
        out[mode]={'native_bad':sum(not e.is_manifold for e in bm.edges),'vertices':len(bm.verts),'faces':len(bm.faces)};bm.free()
        out[mode]['cleanup']=clean_object(floor)
        bm=prepare_export_bmesh(floor,[0,0,0]);out[mode]['export_bad']=sum(not e.is_manifold for e in bm.edges)
        out[mode]['export_bad_details']=[{'length':e.calc_length(),'face_count':len(e.link_faces)} for e in bm.edges if not e.is_manifold]
        lo=Vector(tuple(min(v.co[i] for v in bm.verts) for i in range(3)));hi=Vector(tuple(max(v.co[i] for v in bm.verts) for i in range(3)))
        shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
        with (ROOT/'mesh-repair-verification'/'B01_open_front_base_240x190.stl').open('wb') as f:
            f.write(b'EDU06 cap cutter verification'.ljust(80,b' '));f.write(struct.pack('<I',len(bm.faces)))
            for face in bm.faces:
                vs=[v.co+shift for v in face.verts];n=(vs[1]-vs[0]).cross(vs[2]-vs[0]);n.normalize()
                f.write(struct.pack('<12fH',*n,*vs[0],*vs[1],*vs[2],0))
        bm.free()
except Exception:out['error']=traceback.format_exc()
(ROOT/'base-cap-test.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
