import bpy,bmesh,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from mesh_repair import prepare_export_bmesh
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'BUILD_DEBUG.blend'))
o=bpy.data.objects['W03_moving_pitch_cradle'];report=[]
original=o.data.copy()
for method in ['dissolve_limit','post_tri_degenerate','dissolve_verts']:
 o.data=original.copy();b=bmesh.new();b.from_mesh(o.data)
 if method=='dissolve_limit':bmesh.ops.dissolve_limit(b,angle_limit=1e-6,verts=list(b.verts),edges=list(b.edges),use_dissolve_boundaries=False)
 elif method=='post_tri_degenerate':
  bmesh.ops.triangulate(b,faces=list(b.faces),ngon_method='BEAUTY');bmesh.ops.dissolve_degenerate(b,dist=1e-6,edges=list(b.edges))
 elif method=='dissolve_verts':
  vs=[v for v in b.verts if len(v.link_edges)==2 and (v.link_edges[0].other_vert(v).co-v.co).normalized().dot((v.link_edges[1].other_vert(v).co-v.co).normalized())<-.99999999]
  bmesh.ops.dissolve_verts(b,verts=vs,use_face_split=False,use_boundary_tear=False)
 b.to_mesh(o.data);b.free()
 try:bm=prepare_export_bmesh(o);bm.free();ok=True
 except Exception as e:ok=str(e)
 report.append({'method':method,'result':ok,'vertices':len(o.data.vertices),'faces':len(o.data.polygons)})
(ROOT/'cradle-tessellation-results.json').write_text(json.dumps(report,indent=2))
