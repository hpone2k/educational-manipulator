from pathlib import Path
import gzip,json,bpy,bmesh,traceback
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
try:
    data=json.loads(gzip.decompress((ROOT/'XM-official-mm.json.gz').read_bytes()))
    part=next(p for p in data['parts'] if p['role']=='case')
    report=[]
    for upper in [True,False]:
        mesh=bpy.data.meshes.new('probe');mesh.from_pydata(part['vertices'],[],part['faces']);mesh.update()
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,
            plane_co=Vector((0,0,-2)),plane_no=Vector((0,0,1)),clear_inner=upper,clear_outer=not upper)
        if upper:
            flat=[f for f in bm.faces if all(abs(v.co.z+2)<.00001 for v in f.verts)]
            bmesh.ops.delete(bm,geom=flat,context='FACES')
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
        boundaries=[e for e in bm.edges if e.is_boundary]
        r={'upper':upper,'boundaries_before':len(boundaries),'before_faces':len(bm.faces),
            'bounds_before':[[min(v.co[i] for v in bm.verts) for i in range(3)],[max(v.co[i] for v in bm.verts) for i in range(3)]]}
        bmesh.ops.triangle_fill(bm,edges=boundaries,use_beauty=True,use_dissolve=False)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        r.update(bad=sum(not e.is_manifold for e in bm.edges),boundary=sum(e.is_boundary for e in bm.edges),
            volume=bm.calc_volume(signed=True),zero=sum(f.calc_area()<1e-12 for f in bm.faces))
        bm.to_mesh(mesh);bm.free()
        obj=bpy.data.objects.new('upper' if upper else 'lower',mesh);bpy.context.scene.collection.objects.link(obj)
        report.append(r)
    (ROOT/'xm-partition-diagnosis.json').write_text(json.dumps(report,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'xm-partition-test.blend'))
except Exception:(ROOT/'xm-partition-error.txt').write_text(traceback.format_exc());raise
