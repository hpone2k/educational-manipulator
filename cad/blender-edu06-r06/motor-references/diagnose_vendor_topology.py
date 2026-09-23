from pathlib import Path
import gzip,json,bpy,bmesh
ROOT=Path(__file__).resolve().parent
report=[]
for kind in ['AX','XM']:
    data=json.loads(gzip.decompress((ROOT/(kind+'-official-mm.json.gz')).read_bytes()))
    for part in data['parts']:
        if part['name'].endswith('_2') and part['role']!='case':continue
        mesh=bpy.data.meshes.new('probe');mesh.from_pydata(part['vertices'],[],part['faces']);mesh.update()
        for tol in [.0000001,.000001,.000005,.00005]:
            bm=bmesh.new();bm.from_mesh(mesh)
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=tol)
            bad=[e for e in bm.edges if not e.is_manifold]
            report.append(dict(kind=kind,name=part['name'],tol=tol,bad=len(bad),
                boundary=sum(e.is_boundary for e in bad),noncontiguous=sum(not e.is_contiguous for e in bm.edges),
                volume=bm.calc_volume(signed=True),examples=[[[round(c,6) for c in v.co] for v in e.verts] for e in bad[:8]]))
            bm.free()
        bpy.data.meshes.remove(mesh)
(ROOT/'vendor-topology-diagnosis.json').write_text(json.dumps(report,indent=2))
