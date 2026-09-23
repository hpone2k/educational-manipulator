import bpy,bmesh,json,sys,struct,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from mesh_repair import prepare_export_bmesh
out={};folder=ROOT/'mesh-repair-verification';folder.mkdir(exist_ok=True)
try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
    parts=[o for o in bpy.data.objects if o.type=='MESH' and 'part_id' in o]
    for o in parts:
        bm=prepare_export_bmesh(o,list(o.get('print_rotation_deg',[0,0,0])))
        lo=Vector(tuple(min(v.co[i] for v in bm.verts) for i in range(3)))
        hi=Vector(tuple(max(v.co[i] for v in bm.verts) for i in range(3)))
        shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
        with (folder/(o['part_id']+'.stl')).open('wb') as f:
            f.write(b'EDU06 independent repair verification'.ljust(80,b' '));f.write(struct.pack('<I',len(bm.faces)))
            for face in bm.faces:
                vs=[v.co+shift for v in face.verts];n=(vs[1]-vs[0]).cross(vs[2]-vs[0]);n.normalize()
                f.write(struct.pack('<12fH',*n,*vs[0],*vs[1],*vs[2],0))
        bm.free()
    out={'done':True,'parts':len(parts),'blend_modified':(ROOT/'EDU06_R03.blend').stat().st_mtime}
except Exception:out={'error':traceback.format_exc()}
(ROOT/'mesh-repair-export-complete.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
