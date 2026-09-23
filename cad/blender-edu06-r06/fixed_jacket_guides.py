"""Fixed USB/DC reference routes and an independent read-only jacket screen."""
from pathlib import Path


def configure_fixed_jackets():
    return {
        'USB':[(-84,11,15.45),(-84,-20,15.45),(-112,-20,45),(-110,42,48),
               (-84,79,28),(-84,93,28),(-84,98,28),(-84,108,28),(-84,118,28),
               (-84,139,28),(-116,160,7)],
        'EXTERNAL_DC':[(84,72,24),(84,86,24),(84,93,24),(84,98,24),(84,108,24),
                       (84,118,24),(84,142,24),(120,162,7)],
    }


def audit_fixed_jackets(scene,output):
    import json,math
    from datetime import datetime,timezone
    import bpy
    import numpy as np
    import audit_assembly as A
    from wiring_module import sample_nurbs
    scene.frame_set(1);bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get()
    objects=[o for o in scene.objects if o.type=='MESH' and not o.get('wiring_object') and
             (o.get('part_id') or o.get('collision_check') or o.get('fastener_kind') or 'socket head' in o.name) and
             not o.name.startswith(('F0','B03_service_front_panel'))]
    solids=[A.prepare_world_collision(o,A.geometry(o,graph)) for o in objects]
    rows=[]
    for conductor,radius,centre,nominal_gap in [('USB',2.35,(-84.,98.,28.),.25),('EXTERNAL_DC',2.8,(84.,98.,24.),.4)]:
        candidates=[o for o in scene.objects if o.type=='CURVE' and o.get('conductor')==conductor]
        if len(candidates)!=1:
            raise RuntimeError(f'Expected one {conductor} reference curve, got {len(candidates)}')
        obj=candidates[0];evaluated=obj.evaluated_get(graph)
        points=[evaluated.matrix_world@p for p in sample_nurbs(evaluated.data.splines[0],501)]
        events=[];clamp_contacts=[];lowest=1e9;minimum_bend=1e9;bend_location=None
        for index,(a,b,c) in enumerate(zip(points,points[1:],points[2:]),1):
            cross=(b-a).cross(c-a).length
            if cross>1e-8:
                bend=(a-b).length*(b-c).length*(c-a).length/(2*cross)
                if bend<minimum_bend:
                    minimum_bend=bend;bend_location={'sample':index,'xyz':list(b)}
        for solid in solids:
            name=solid['object'].name
            for index,point in enumerate(points):
                # Exact provisional U2D2 face only; no other object is exempt.
                if conductor=='USB' and name.startswith('U2D2 USB') and (point-points[0]).length<10 and point.y<=11.001:
                    continue
                boxdist=math.sqrt(sum(max(solid['lower'][i]-point[i],0,point[i]-solid['upper'][i])**2 for i in range(3)))
                if boxdist>radius+.55:
                    continue
                near,normal,_,distance=solid['tree'].find_nearest(point)
                if near is None:
                    continue
                inside=False
                if A.local_bounds_mask(np.array([point[:]]),solid)[0] and distance>.02 and (point-near).dot(normal)<-.01:
                    inside,_=A.is_inside(solid['tree'],point)
                clearance=float(distance)-radius
                lowest=min(lowest,clearance)
                clamp=(name.startswith('B22_') or name.startswith('B01_')) and abs(point.x-centre[0])<=.1 and abs(point.z-centre[2])<=.1 and 89<=point.y<=107
                if clamp and not inside and clearance>=nominal_gap-.01:
                    clamp_contacts.append({'part':name,'sample':index,'clearance_mm':clearance,'nominal_radial_gap_mm':nominal_gap})
                    continue
                if inside or clearance<.5:
                    events.append({'part':name,'sample':index,'xyz':list(point),'centre_inside_solid':inside,
                                   'jacket_surface_clearance_mm':clearance,'at_true_clamp_axis':clamp})
        row={'curve':obj.name,'conductor':conductor,'radius_mm':radius,'sample_count':len(points),
             'length_mm':sum((b-a).length for a,b in zip(points,points[1:])),
             'minimum_bend_radius_mm':minimum_bend,'minimum_bend_location':bend_location,
             'bend_target_12mm_met':minimum_bend>=12.,'lowest_near_structure_surface_clearance_mm':lowest,
             'accepted_printed_clamp_bore_samples':clamp_contacts,'unresolved_contacts':events,
             'structure_screen_passed':not events}
        row['pass']=row['structure_screen_passed'] and row['bend_target_12mm_met'];rows.append(row)
    report={'audit':'R06_fixed_USB_and_external_DC_jacket_geometry_screen_v1',
            'created_utc':datetime.now(timezone.utc).isoformat(),'native_file':bpy.data.filepath,
            'fixed_world_routes':True,'frame':1,'structural_mesh_count_including_tagged_hardware':len(solids),
            'all_passed':all(row['pass'] for row in rows),'jackets':rows,
            'scope':'501 centreline samples per actual evaluated jacket with its own radius. Same-body structure and tagged hardware included. The real printed saddle-axis fit accepts only its nominal 0.25/0.4 mm radial clearance with 0.01 mm numerical/facet allowance; other structure needs 0.5 mm. Only the immediate outward U2D2 USB face is provisional. No electrical rating, continuous collision, flexible-cable stress, plug fit or fatigue validation.'}
    Path(output).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return report


def main():
    import sys,traceback
    from types import SimpleNamespace
    import bpy
    root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
    out=root/'fixed-jacket-test';out.mkdir(exist_ok=True)
    try:
        bpy.ops.wm.open_mainfile(filepath=str(root/'EDU06_R06.blend'))
        scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'))
        bpy.context.window.scene=scene
        if '--audit-final' in sys.argv:
            return audit_fixed_jackets(scene,root/'fixed-jacket-audit.json')
        import blender_lib as L
        import wiring_module as W
        scene.frame_set(1);bpy.context.view_layer.update();L.scene=scene
        for attr,start in [('printed','01'),('hardware','02'),('controls','03'),('cables','04'),('studio','05')]:
            setattr(L,attr,next(c for c in scene.collection.children if c.name.startswith(start)))
        L.JOINTS={o.name[:2]:o for o in scene.objects if o.get('axis') and o.name[:2] in ['J1','J2','J3','J4','J5']}
        matnames={'ivory':'FDM • warm ivory','black':'DYNAMIXEL • black polymer','red':'Cable red',
                  'yellow':'Cable yellow','green':'FDM • deep forest green','steel':'Purchased screws and nuts','text':'Light markings'}
        B=SimpleNamespace(M={k:bpy.data.materials[v] for k,v in matnames.items()},
                          control=next(o for o in scene.objects if o.name.startswith('CONTROL')))
        W.build_wiring(B);bpy.context.view_layer.update()
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'FIXED_JACKET_TEST.blend'))
        bpy.ops.wm.open_mainfile(filepath=str(out/'FIXED_JACKET_TEST.blend'))
        scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'));bpy.context.window.scene=scene
        return audit_fixed_jackets(scene,out/'audit.json')
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc());raise


if __name__=='__main__':
    main()
