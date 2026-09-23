"""Isolated actual-CAD motor/cradle fit and rotor partition verification."""
from pathlib import Path
import sys,json,traceback,math
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import bpy,bmesh
from mathutils import Matrix,Vector
import blender_lib as L
import motor_models as MM
import audit_assembly as A

try:
    scene=L.setup()
    M={k:L.material(k,c) for k,c in {'black':(.02,.025,.03),'steel':(.35,.38,.4),
        'ivory':(.77,.75,.65),'green':(.03,.10,.065),'text':(.7,.9,.8)}.items()}
    motors=[]
    for k,x in [('AX',-40),('XM',40)]:
        motors.append((k,MM.make_motor(k,'TEST_'+k,None,L.T(x,0,0),M)))
    motors.append(('AX_FRONT',MM.make_motor('AX','TEST_AX_FRONT',None,L.T(120,0,0),M,attachment_depth=6,front_fasteners=True)))
    bpy.context.view_layer.update()
    result={'meshes':[],'fits':[],'schedule':MM.MOTOR_UNITS}
    for o in L.PRINT+[m[key] for _,m in motors for key in ['body','horn']]:
        bm=bmesh.new();bm.from_mesh(o.data)
        result['meshes'].append({'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
            'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'volume_mm3':bm.calc_volume(signed=True)})
        bm.free()
    dg=bpy.context.evaluated_depsgraph_get()
    for kind,m in motors:
        for fixed in [m['body'],m['cradle'],m['rear_cap'],*m['shims']]:
            a=A.prepare_world_collision(fixed,A.geometry(fixed,dg))
            for test in [m['body'],m['horn']]:
                if fixed==test:continue
                b=A.prepare_world_collision(test,A.geometry(test,dg))
                p=A.sampled_penetration(a,b,160);q=A.sampled_penetration(b,a,160)
                result['fits'].append({'first':fixed.name,'second':test.name,
                    'depth_mm':max(p['maximum_sampled_depth_mm'],q['maximum_sampled_depth_mm']),
                    'forward':p,'reverse':q})
    (ROOT/'motor-import-test.json').write_text(json.dumps(result,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'motor-import-test.blend'))
    print('DONE MOTOR IMPORT TEST',[(x['name'],x['nonmanifold_edges']) for x in result['meshes']])
except Exception:
    (ROOT/'motor-import-error.txt').write_text(traceback.format_exc());raise
