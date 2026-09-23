import bpy,bmesh,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import mesh_repair as M
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'gripper-test'/'GRIPPER_DEBUG.blend'))
out={}
for name in ['G01_Windowed_rear_palm','G02_Captured_slide_lower_frame']:
    o=bpy.data.objects[name];out[name]={}
    for method in ['raw','EAR_CLIP','BEAUTY']:
        bm=bmesh.new();bm.from_mesh(o.data);M.remove_duplicate_faces(bm)
        if method!='raw':bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method=method)
        M.remove_duplicate_faces(bm)
        out[name][method]={'verts':len(bm.verts),'faces':len(bm.faces),
          'bad_edges':[{'verts':[list(v.co) for v in e.verts],'faces':len(e.link_faces)} for e in bm.edges if not e.is_manifold][:12],
          'degenerate':[{'verts':[list(v.co) for v in f.verts],'area':f.calc_area()} for f in bm.faces if f.calc_area()<1e-10][:12]}
        bm.free()
(ROOT/'gripper-test'/'mesh-diagnostic.json').write_text(json.dumps(out,indent=2))
