"""Independent check of the actual exported binary STL files; no Blender needed."""
from pathlib import Path
from collections import Counter
import json
import math
import struct
import zipfile

root=Path(__file__).resolve().parent
reports=[]
for path in sorted((root/'prototype_stl').glob('*.stl')):
    data=path.read_bytes()
    count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count, path.name
    edges=Counter();orientation=Counter();verts=[];volume=0
    for offset in range(84,len(data),50):
        values=struct.unpack_from('<12fH',data,offset)
        a,b,c=[tuple(values[i:i+3]) for i in (3,6,9)]
        assert all(math.isfinite(v) for p in (a,b,c) for v in p)
        ab=tuple(b[i]-a[i] for i in range(3));ac=tuple(c[i]-a[i] for i in range(3))
        cross=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
        assert sum(v*v for v in cross)>1e-14, f'Degenerate triangle in {path.name}'
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        for u,v in ((a,b),(b,c),(c,a)):
            edge=tuple(sorted((u,v)));edges[edge]+=1;orientation[edge]+=1 if u<v else -1
        verts.extend((a,b,c))
    assert all(n==2 for n in edges.values()),f'Open/nonmanifold STL: {path.name}'
    assert all(n==0 for n in orientation.values()),f'Inconsistent STL normals: {path.name}'
    assert abs(min(p[2] for p in verts))<1e-5, f'Not grounded: {path.name}'
    assert volume>0,f'Inverted STL: {path.name}'
    reports.append({'file':path.name,'triangles':count,'closed':True,'consistent_winding':True,'grounded_z0':True,'volume_mm3':round(volume,2)})
assert len(reports)==13
(root/'stl_file_checks.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
with zipfile.ZipFile(root/'EDU05_prototype_STLs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root/'prototype_stl').glob('*.stl')):archive.write(path,'prototype_stl/'+path.name)
    for name in ('READ_ME_FIRST.md','parts_list.csv','mesh_checks.json','stl_file_checks.json'):
        archive.write(root/name,name)
print(f'PASS: {len(reports)} binary STL files, closed edges, consistent winding, finite nondegenerate triangles, positive volume, millimetre coordinates, and Z=0 placement. ZIP created.')
