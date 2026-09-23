import bpy,bmesh,json,traceback,collections,sys,math,struct
from pathlib import Path
from mathutils import Euler
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import mesh_repair
out={}
def stats(bm):
    counts=collections.Counter();fs=collections.Counter()
    for f in bm.faces:
        cs=[tuple(round(float(c),4) for c in v.co) for v in f.verts]
        fs[tuple(sorted(cs))]+=1
        for a,b in zip(cs,cs[1:]+cs[:1]):counts[tuple(sorted((a,b)))]+=1
    return {'native_bad':sum(not e.is_manifold for e in bm.edges),'coordinate_bad':sum(v!=2 for v in counts.values()),
        'duplicate_faces':sum(v-1 for v in fs.values()),'faces':len(bm.faces)}
try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
    for name in ['B03_service_front_panel','G04_front_pivot_bridge']:
        o=bpy.data.objects[name];out[name]={}
        before=[tuple(v.co) for v in o.data.vertices]
        out[name]['cleanup']=mesh_repair.clean_object(o)
        out[name]['vertex_coordinates_identical']=before==[tuple(v.co) for v in o.data.vertices]
        bm=mesh_repair.prepare_export_bmesh(o,o.get('print_rotation_deg',[0,0,0]))
        out[name]['corrected_export']=stats(bm);bm.free()
        # Reproduce old pipeline for comparison.
        bm=bmesh.new();bm.from_mesh(o.data)
        rot=Euler(tuple(math.radians(v) for v in o.get('print_rotation_deg',[0,0,0]))).to_matrix()
        for v in bm.verts:v.co=rot@v.co
        bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00005)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00005);bmesh.ops.triangulate(bm,faces=list(bm.faces))
        out[name]['old_export']=stats(bm);bm.free()
except Exception:out['error']=traceback.format_exc()
(ROOT/'mesh-export-repair-tests.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
