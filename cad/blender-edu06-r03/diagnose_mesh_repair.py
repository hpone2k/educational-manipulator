import bpy,bmesh,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NAMES=['B01_open_front_base_240x190','B03_service_front_panel','B05_lower_journal_support','G04_front_pivot_bridge']
out={}
def stats(bm):
    bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
    return {'v':len(bm.verts),'e':len(bm.edges),'f':len(bm.faces),
        'bad':[{'length':e.calc_length(),'coords':[list(v.co) for v in e.verts],
                'faces':[{'area':f.calc_area(),'normal':list(f.normal),'verts':[list(v.co) for v in f.verts]} for f in e.link_faces]}
               for e in bm.edges if not e.is_manifold]}
try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
    for name in NAMES:
        o=bpy.data.objects.get(name)
        bm=bmesh.new();bm.from_mesh(o.data)
        out[name]={'native':stats(bm)}
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0001)
        out[name]['weld']=stats(bm)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        out[name]['triangulate']=stats(bm)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.001)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.001)
        out[name]['weld_001']=stats(bm)
        bm.free()
except Exception:
    out['error']=traceback.format_exc()
(ROOT/'mesh-repair-diagnosis.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
