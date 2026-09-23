"""Verify only disconnected AX front-shim corner chips are removed.

Loads the prior isolated motor test, never the user's final assembly. Retained
coordinates are compared exactly. Emits one repaired shim STL for independent
cross-checking, not the final arm's print export.
"""
from pathlib import Path
import sys,json,struct,traceback
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import bpy,bmesh
from mathutils import Vector
import motor_models as MM
import mesh_repair
import audit_assembly as A


def components(mesh):
    bm=bmesh.new();bm.from_mesh(mesh);pending=set(bm.verts);sizes=[]
    while pending:
        found={pending.pop()};todo=list(found)
        while todo:
            for edge in todo.pop().link_edges:
                for v in edge.verts:
                    if v in pending:pending.remove(v);found.add(v);todo.append(v)
        sizes.append(len(found))
    result={'components':len(sizes),'bad_edges':sum(not e.is_manifold for e in bm.edges),
            'volume_mm3':bm.calc_volume(signed=True),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
    bm.free();return result


try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'motor-import-test.blend'))
    report=[]
    for o in list(bpy.context.scene.objects):
        if not o.name.startswith('TEST_AX') or '_C04_1_Axial_fit_shim_030' not in o.name:continue
        before=components(o.data);oldcoords={tuple(v.co) for v in o.data.vertices}
        MM._retain_ax_front_seating_piece(o)
        after=components(o.data)
        assert after['components']==1 and after['bad_edges']==0 and after['zero_area_faces']==0
        unchanged=all(tuple(v.co) in oldcoords for v in o.data.vertices);assert unchanged
        body=bpy.data.objects.get(o.name.split('_C04')[0]+' | AX-12A dimensioned case')
        bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
        a=A.prepare_world_collision(o,A.geometry(o,dg));b=A.prepare_world_collision(body,A.geometry(body,dg))
        penetration=max(A.sampled_penetration(a,b,256)['maximum_sampled_depth_mm'],
                        A.sampled_penetration(b,a,256)['maximum_sampled_depth_mm'])
        row={'name':o.name,'before':before,'after':after,'retained_vertices_exactly_unchanged':unchanged,
             'removed_volume_mm3':before['volume_mm3']-after['volume_mm3'],
             'removed_solid_PLA_mass_g':(before['volume_mm3']-after['volume_mm3'])*.00124,
             'remaining_solid_PLA_mass_g':after['volume_mm3']*.00124,
             'maximum_sampled_motor_penetration_mm':penetration}
        report.append(row)
        bm=mesh_repair.prepare_export_bmesh(o,(0,0,0))
        lo=Vector(tuple(min(v.co[i] for v in bm.verts) for i in range(3)))
        hi=Vector(tuple(max(v.co[i] for v in bm.verts) for i in range(3)))
        shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
        path=ROOT/'AX_front_shim_single_U_verification.stl'
        with path.open('wb') as f:
            f.write(b'AX front shim retained single U; mm'.ljust(80,b' '));f.write(struct.pack('<I',len(bm.faces)))
            for face in bm.faces:
                vs=[v.co+shift for v in face.verts];n=(vs[1]-vs[0]).cross(vs[2]-vs[0]);n.normalize()
                f.write(struct.pack('<12fH',*n,*vs[0],*vs[1],*vs[2],0))
        bm.free()
    (ROOT/'ax-shim-connectivity-test.json').write_text(json.dumps(report,indent=2))
except Exception:
    (ROOT/'ax-shim-connectivity-error.txt').write_text(traceback.format_exc());raise
