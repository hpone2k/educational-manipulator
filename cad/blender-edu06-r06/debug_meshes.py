import bpy,sys,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from mesh_repair import prepare_export_bmesh,_zero_area_after_stl_grounding
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'BUILD_DEBUG.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06'))
bpy.context.window.scene=scene
fail=[]
for o in scene.objects:
    if not o.get('part_id'):continue
    try:
        bm=prepare_export_bmesh(o,list(o['print_rotation_deg']));bm.free()
    except Exception as e:
        bm=bmesh.new();bm.from_mesh(o.data)
        row={'name':o.name,'bad_edges':sum(not e.is_manifold for e in bm.edges),'vertices':len(bm.verts),'details':[]}
        for method in ['EAR_CLIP','BEAUTY']:
            b=bm.copy();bmesh.ops.triangulate(b,faces=list(b.faces),ngon_method=method)
            row['details'].append({'method':method,'zero_tri':_zero_area_after_stl_grounding(b),'bad_edges':sum(not e.is_manifold for e in b.edges)})
            b.free()
        row['bad_edge_coordinates']=[[list(v.co) for v in e.verts] for e in bm.edges if not e.is_manifold][:20]
        fail.append(row);bm.free()
(ROOT/'debug-mesh-report.json').write_text(json.dumps(fail,indent=2),encoding='utf-8')
print(json.dumps(fail,indent=2),flush=True)
scene.frame_set(1);bpy.context.view_layer.update();scene.cycles.samples=8
scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'debug-preview.png');bpy.ops.render.render(write_still=True)
