"""Isolated R05 wrist/gripper build, mesh and sampled motion checks."""
import bpy,sys,json,traceback,itertools
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import blender_lib as L
import audit_assembly as A
import numpy as np
from wrist_module import build_wrist
from mesh_repair import clean_object,prepare_export_bmesh
OUT=ROOT/'wrist-test';OUT.mkdir(exist_ok=True)

try:
    L.setup();L.ROOT=OUT
    mats={k:L.material(k,c,metal=.7 if k=='steel' else 0,rough=.36) for k,c in {
        'green':(.09,.22,.155),'ivory':(.76,.77,.67),'steel':(.38,.40,.41),
        'black':(.018,.023,.022),'text':(.8,.8,.8),'red':(.7,.06,.04),
        'yellow':(.8,.56,.07)}.items()}
    control=L.empty('CONTROL');home={'J1':0,'J2':70,'J3':55,'J4':0,'J5':0,'GRIP':45}
    for key,value in home.items():control[key]=value
    j5,grip,pair=build_wrist(None,Matrix.Identity(4),control,mats,home)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'WRIST_R05_TEST.blend'))
    rows=[]
    for o in L.PRINT:
        try:
            clean_object(o);bm=prepare_export_bmesh(o,list(o['print_rotation_deg']))
            bad=sum(not e.is_manifold for e in bm.edges);bm.free()
            vol,centre,rawbad=L.mesh_stats(o)
            rows.append({'name':o.name,'passed':not bad and vol>0,'solid_PLA_mass_g':vol*.00124,'volume_mm3':vol,'nonmanifold':bad})
        except Exception as e:rows.append({'name':o.name,'passed':False,'error':str(e)})
    (OUT/'mesh-check.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    good={r['name'] for r in rows if r['passed']}
    L.PRINT=[o for o in L.PRINT if o.name in good];L.export_parts()
    deps=bpy.context.evaluated_depsgraph_get()
    cache={o:A.geometry(o,deps) for o in bpy.context.scene.objects if o.type=='MESH' and
           (o.get('part_id') or o.get('collision_check'))}
    poses=[{'J4':0,'J5':0,'GRIP':45},
           *[{'J4':q,'J5':0,'GRIP':45} for q in (-25,25)],
           *[{'J4':0,'J5':q,'GRIP':45} for q in (-60,60)],
           *[{'J4':0,'J5':0,'GRIP':q} for q in (20,70)],
           *[{'J4':q,'J5':r,'GRIP':g} for q in (-25,25) for r in (-60,60) for g in (20,70)]]
    reports=[]
    A.set_pose(control,home)
    world=[A.prepare_world_collision(o,d) for o,d in cache.items()]
    fixed_intersections=[]
    for a,b in itertools.combinations(world,2):
        overlap=np.minimum(a['upper'],b['upper'])-np.maximum(a['lower'],b['lower'])
        if (overlap < -.002).any():continue
        one=A.sampled_penetration(a,b,128);two=A.sampled_penetration(b,a,128)
        depth=max(one['maximum_sampled_depth_mm'],two['maximum_sampled_depth_mm'])
        if depth>.02:fixed_intersections.append({'objects':[a['object'].name,b['object'].name],'depth_mm':depth,'first':one,'second':two})
    (OUT/'all-groups-home-check.json').write_text(json.dumps(fixed_intersections,indent=2),encoding='utf-8')
    for p in poses:
        A.set_pose(control,p)
        report=A.collision_screen(list(cache.items()))
        right=A.world_matrix(bpy.data.objects['GRIP right contact']).translation
        left=A.world_matrix(bpy.data.objects['GRIP left contact']).translation
        reports.append({'pose':p,'measured_pad_gap_mm':(right-left).length,'collision':report})
        (OUT/'collision-check.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    A.set_pose(control,home)
    total=sum(r.get('solid_PLA_mass_g',0) for r in rows)
    (OUT/'summary.json').write_text(json.dumps({'printed_parts':len(rows),'mesh_failures':[r for r in rows if not r['passed']],
        'printed_solid_PLA_mass_g':total,'AX_motor_count':3,'AX_motor_mass_g':163.8,
        'motion_poses':len(reports),'poses_requiring_review':[r['pose'] for r in reports if not r['collision']['clear_of_reported_crossings_or_penetrations']],
        'all_group_home_penetrations':fixed_intersections,'pair':pair},indent=2),encoding='utf-8')
    (OUT/'DONE.txt').write_text('Isolated R05 wrist/gripper audit completed.',encoding='utf-8')
except Exception:
    (OUT/'ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
