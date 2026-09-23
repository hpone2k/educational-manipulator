"""Exact mesh-copy equivalence and repeated-import timing; isolated Blender."""
from pathlib import Path
import sys,time,json,hashlib,traceback
from array import array
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import bpy,bmesh
from mathutils import Matrix
import blender_lib as L
import motor_models as MM


def signature(o):
    mesh=o.data
    positions=array('f',[0.0])*(len(mesh.vertices)*3)
    indices=array('i',[0])*len(mesh.loops)
    starts=array('i',[0])*len(mesh.polygons)
    sizes=array('i',[0])*len(mesh.polygons)
    materials=array('i',[0])*len(mesh.polygons)
    smooth=array('b',[0])*len(mesh.polygons)
    mesh.vertices.foreach_get('co',positions)
    mesh.loops.foreach_get('vertex_index',indices)
    mesh.polygons.foreach_get('loop_start',starts)
    mesh.polygons.foreach_get('loop_total',sizes)
    mesh.polygons.foreach_get('material_index',materials)
    mesh.polygons.foreach_get('use_smooth',smooth)
    h=hashlib.sha256()
    for part in [positions,indices,starts,sizes,materials,smooth]:h.update(part.tobytes())
    h.update(json.dumps([m.name for m in mesh.materials]).encode())
    bm=bmesh.new();bm.from_mesh(mesh)
    topology={'bad_edges':sum(not e.is_manifold for e in bm.edges),
              'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
              'volume_mm3':bm.calc_volume(signed=True)}
    bm.free()
    return {'sha256':h.hexdigest(),'vertices':len(mesh.vertices),'faces':len(mesh.polygons),
            'properties':{k:o[k] for k in ('mass_g','reference_only','collision_check','interface_role','source_step','vendor_geometry','tessellation_chord_mm')},
            **topology}


try:
    L.setup()
    mats={k:L.material(k,c) for k,c in {'black':(.02,.025,.03),'steel':(.35,.38,.4),
         'ivory':(.77,.75,.65),'green':(.03,.10,.065),'text':(.7,.9,.8)}.items()}
    report=[]
    for kind in ['AX','XM']:
        row={'kind':kind,'runs':[]}
        for i in range(3):
            start=time.perf_counter()
            result=MM.make_motor(kind,kind+str(i),None,Matrix.Identity(4),mats,cradle=False)
            elapsed=time.perf_counter()-start
            row['runs'].append({'seconds':elapsed,'body':signature(result['body']),'horn':signature(result['horn'])})
        row['exact_equal']=all(row['runs'][0][key]==run[key] for run in row['runs'][1:] for key in ('body','horn'))
        row['speedup']=row['runs'][0]['seconds']/min(r['seconds'] for r in row['runs'][1:])
        assert row['exact_equal'],row
        report.append(row)
    (ROOT/'vendor-cache-test.json').write_text(json.dumps(report,indent=2))
except Exception:
    (ROOT/'vendor-cache-error.txt').write_text(traceback.format_exc());raise
