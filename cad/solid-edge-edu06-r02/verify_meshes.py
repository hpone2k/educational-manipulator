import pathlib,json,struct,collections,math,zipfile
root=pathlib.Path(__file__).parent
data=json.loads((root/'design.json').read_text())
cad={x['name']:x for x in json.loads((root/'cad-verification.json').read_text())}
reports=[]
for part in data['parts']:
 path=root/'stl_mm'/(part['name']+'.stl')
 if not path.exists():continue
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,80)[0]
 assert len(raw)==84+50*n,(path,'length')
 edges=collections.Counter();verts=set();volume=0.;areas=[];lo=[math.inf]*3;hi=[-math.inf]*3
 for i in range(n):
  a=struct.unpack_from('<12fH',raw,84+50*i);pts=[tuple(a[j:j+3]) for j in (3,6,9)]
  keys=[tuple(round(q,4) for q in p) for p in pts];verts.update(keys)
  for j in range(3):edges[tuple(sorted((keys[j],keys[(j+1)%3])))]+=1
  for p in pts:
   for j in range(3):lo[j]=min(lo[j],p[j]);hi[j]=max(hi[j],p[j])
  x,y,z=pts
  volume+=(x[0]*(y[1]*z[2]-y[2]*z[1])+x[1]*(y[2]*z[0]-y[0]*z[2])+x[2]*(y[0]*z[1]-y[1]*z[0]))/6
 bad=sum(v!=2 for v in edges.values());dims=[hi[i]-lo[i] for i in range(3)]
 record={'name':part['name'],'triangles':n,'bounds_mm':[lo,hi],'dimensions_mm':dims,'nonmanifold_edges':bad,'signed_volume_mm3':volume,'category':part['category']}
 if part['name'] in cad:
  nominal=cad[part['name']];record['volume_error_percent']=100*abs(volume-nominal['volume_mm3'])/nominal['volume_mm3']
  record['max_bound_error_mm']=max(abs((hi if side else lo)[i]-nominal['bounds_max_m' if side else 'bounds_min_m'][i]*1000) for side in (0,1) for i in range(3))
 record['mesh_pass']=bad==0 and volume>0 and record.get('max_bound_error_mm',999)<.05 and record.get('volume_error_percent',999)<1
 reports.append(record)
(root/'mesh-verification.json').write_text(json.dumps(reports,indent=2))
fits=[p for p in data['parts'] if p['category']=='fit coupon']
if all((root/'stl_mm'/(p['name']+'.stl')).exists() for p in fits):
 with zipfile.ZipFile(root/'PRINT_FIRST_fit_coupons_mm.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in fits:z.write(root/'stl_mm'/(p['name']+'.stl'),p['name']+'.stl')
print(json.dumps({'checked':len(reports),'passed':sum(r['mesh_pass'] for r in reports),'failed':[r['name'] for r in reports if not r['mesh_pass']]},indent=2))
