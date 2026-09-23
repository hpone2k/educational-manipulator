import bpy,bmesh,json,traceback,collections,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
out={}
def stats(bm):
    counts=collections.Counter();fs=collections.Counter();zero=0
    for f in bm.faces:
        cs=[tuple(round(float(c),5) for c in v.co) for v in f.verts]
        fs[tuple(sorted(cs))]+=1
        for a,b in zip(cs,cs[1:]+cs[:1]):counts[tuple(sorted((a,b)))]+=1
        zero+=f.calc_area()<1e-10
    return {'native_bad':sum(not e.is_manifold for e in bm.edges),'coordinate_bad':sum(v!=2 for v in counts.values()),
        'duplicate_faces':sum(v-1 for v in fs.values()),'zero_faces':zero,'faces':len(bm.faces)}
def unique(bm):
    seen=set();dup=[]
    for f in bm.faces:
        k=tuple(sorted(tuple(round(float(c),5) for c in v.co) for v in f.verts))
        if k in seen:dup.append(f)
        else:seen.add(k)
    bmesh.ops.delete(bm,geom=dup,context='FACES_ONLY')
    return len(dup)
try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
    for name in ['B03_service_front_panel','G04_front_pivot_bridge']:
        o=bpy.data.objects[name];out[name]={}
        for label in ['beauty','ear_clip','unique_ear','dissolve_ear','unique_dissolve_ear']:
            bm=bmesh.new();bm.from_mesh(o.data)
            if label.startswith('unique'):unique(bm)
            if 'dissolve' in label:bmesh.ops.dissolve_limit(bm,angle_limit=.00001,verts=list(bm.verts),edges=list(bm.edges),delimit={'NORMAL'})
            bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method='BEAUTY' if label=='beauty' else 'EAR_CLIP')
            out[name][label]=stats(bm)
            unique(bm);out[name][label+'_postunique']=stats(bm)
            bm.free()
        me=o.data.copy();me.calc_loop_triangles();bm=bmesh.new()
        vs=[bm.verts.new(v.co) for v in me.vertices]
        for tri in me.loop_triangles:
            try:bm.faces.new([vs[i] for i in tri.vertices])
            except ValueError:pass
        out[name]['mesh_loop_tri']=stats(bm);bm.free()
except Exception:out['error']=traceback.format_exc()
(ROOT/'mesh-cleanup-tests.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
