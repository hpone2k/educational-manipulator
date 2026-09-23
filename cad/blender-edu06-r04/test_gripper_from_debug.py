"""Read-only audit of gripper from WRIST_DEBUG; exports only to gripper-test."""
import bpy, sys, json, itertools, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import blender_lib as L
import audit_assembly as A
from mesh_repair import clean_object,prepare_export_bmesh
import numpy as np
OUT=ROOT/'gripper-test';OUT.mkdir(exist_ok=True)
try:
    if '--rebuild' in sys.argv:
        from mathutils import Matrix
        from gripper_module import build_gripper
        L.setup()
        mats={k:L.material(k,c) for k,c in {
            'green':(.08,.2,.13),'ivory':(.8,.78,.65),'steel':(.32,.34,.36),
            'black':(.02,.025,.027),'text':(.8,.8,.8),'red':(.8,.05,.03),
            'yellow':(.9,.65,.08)}.items()}
        control=L.empty('CONTROL')
        result=build_gripper(None,Matrix.Identity(4),control,mats,{'GRIP':45})
        fixed=result['fixed']
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'GRIPPER_DEBUG.blend'))
    else:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'WRIST_DEBUG.blend'))
        fixed=bpy.data.objects['GRIPPER']
        control=next(o for o in bpy.data.objects if o.name.startswith('CONTROL') and 'GRIP' in o)
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH' and A.descendants_of(o,fixed)]
    printed=[o for o in objs if o.get('part_id')]
    mesh=[]
    for o in printed:
        try:
            clean_object(o)
            bm=prepare_export_bmesh(o,list(o['print_rotation_deg']))
            n=len(bm.faces);bad=sum(not e.is_manifold for e in bm.edges);bm.free()
            volume,centre,rawbad=L.mesh_stats(o)
            mesh.append({'name':o.name,'passed':bad==0 and volume>0,'triangles':n,'volume_mm3':volume,'nonmanifold_edges':bad})
        except Exception as e:mesh.append({'name':o.name,'passed':False,'error':str(e)})
    (OUT/'mesh-check.json').write_text(json.dumps(mesh,indent=2))
    (OUT/'mass-summary.json').write_text(json.dumps({
        'printed_solid_PLA_mass_g':sum(v.get('volume_mm3',0)*.00124 for v in mesh),
        'AX_motor_mass_g':54.6,
        'total_without_screws_g':sum(v.get('volume_mm3',0)*.00124 for v in mesh)+54.6,
        'complete':all(v['passed'] for v in mesh),'note':'Solid PLA mesh mass, excludes screws, nuts and cable.'},indent=2))
    print('PRINT MESH CHECK',len(mesh),'failures',[v['name'] for v in mesh if not v['passed']],flush=True)
    if all(v['passed'] for v in mesh):
        L.PRINT=printed;L.ROOT=OUT;L.export_parts()
    dep=bpy.context.evaluated_depsgraph_get()
    cache={o:A.geometry(o,dep) for o in objs}
    reports=[]
    for gap in [20,45,70]:
        A.set_pose(control,{'GRIP':gap})
        moving=A.collision_screen([(o,d) for o,d in cache.items()
            if o.get('part_id') or o.get('collision_check')])
        # Supplement motion audit: do not skip same-rigid-group manufactured
        # pieces or screw stacks. Surface contact is expected at bolted seats;
        # report sampled interior depth, not coplanar BVH matches alone.
        world=[A.prepare_world_collision(o,d) for o,d in cache.items()]
        overlaps=[];candidates=0
        for a,b in itertools.combinations(world,2):
            overlap=np.minimum(a['upper'],b['upper'])-np.maximum(a['lower'],b['lower'])
            if (overlap < -.002).any():continue
            candidates+=1
            one=A.sampled_penetration(a,b,128);two=A.sampled_penetration(b,a,128)
            depth=max(one['maximum_sampled_depth_mm'],two['maximum_sampled_depth_mm'])
            if depth>.02:
                overlaps.append({'objects':[a['object'].name,b['object'].name],
                    'maximum_sampled_depth_mm':depth,'first':one,'second':two})
        reports.append({'gap_mm':gap,'motion_screen':moving,
                        'all_groups_candidates':candidates,'all_groups_penetrations':overlaps})
        (OUT/'collision-check.json').write_text(json.dumps(reports,indent=2))
        print('GAP',gap,'motion',moving['classification_counts'],'all group penetrations',len(overlaps),flush=True)
    (OUT/'DONE.txt').write_text('Gripper isolated read-only debug-model test completed.')
except Exception:
    (OUT/'ERROR.txt').write_text(traceback.format_exc());raise
