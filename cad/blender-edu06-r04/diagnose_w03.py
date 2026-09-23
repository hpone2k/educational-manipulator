import bpy,bmesh,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from mesh_repair import remove_duplicate_faces,_zero_area_after_stl_grounding
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'BUILD_DEBUG.blend'))
o=bpy.data.objects['W03_moving_pitch_cradle'];result={}
for method in ['SOURCE','EAR_CLIP','BEAUTY']:
 b=bmesh.new();b.from_mesh(o.data);remove_duplicate_faces(b)
 if method!='SOURCE':bmesh.ops.triangulate(b,faces=list(b.faces),ngon_method=method)
 bad=[e for e in b.edges if not e.is_manifold]
 zero=[f for f in b.faces if f.calc_area()<1e-10]
 result[method]={'bad_edges':len(bad),'zero_faces':len(zero),'edgecoords':[[list(v.co) for v in e.verts] for e in bad[:20]],'zerocoords':[[list(v.co) for v in f.verts] for f in zero[:20]]}
 b.free()
(ROOT/'W03-topology.json').write_text(json.dumps(result,indent=2))
