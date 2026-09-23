"""External H05 service loop from fixed wrist pitch to moving tool roll.

The guide empties are virtual spline controls, not physical cable clips. The
source exits away from the elbow support. The destination arc passes outside
the fixed heel; H06 retains its separate route through the heel bore. Routes
are kinematic references and require physical slack/bend/connector validation.
"""
from pathlib import Path

def configure_wrist_route(ports,cases,B):
    from wiring_module import _bridge_anchor,_empty
    src=ports['J4_AX'][1];dst=ports['J5_AX'][0]
    for port in (src,dst):
        port['straight'].location.z=16
        port['far'].location=(0,-14,25)
        port['turn'].location=(0,-45,25)
    # Numerically fitted in millimetres, then checked against actual meshes;
    # precision here stabilizes the spline and is not a print-fit tolerance.
    dst['far'].location=(2.49245,2.16111,19.21413)
    dst['straight'].location.z=10.96914
    dst['turn'].location=(14.03212,11.66154,24.25260)
    # Keep the pin-row spacing through the short terminal tangent; an abrupt
    # 2.5 -> 1.8 mm fan-out there bends the outside strand too tightly.
    dst['straight']['bundle_pitch_mm']=2.5
    dst['far']['bundle_pitch_mm']=2.5
    dst['turn']['bundle_pitch_mm']=2.2
    guides=[_bridge_anchor('H05_J4_J5 service loop 1',src['turn'],dst['turn'],.25,(0,30,-70),cases['J4_AX']),
            _empty('H05_J4_J5 outer radius guide',dst['port'],(110,75,19.5)),
            _empty('H05_J4_J5 destination long tangent',dst['port'],(33.56867,54.95985,22.54037)),
            _empty('H05_J4_J5 destination arc tangent',dst['port'],(37.32494,25.52937,18.07505))]
    for guide in guides[:2]:guide['bundle_pitch_mm']=3.0
    guides[2]['bundle_pitch_mm']=2.1
    return guides

def _test():
    import sys,json,bpy
    from types import SimpleNamespace
    root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
    import blender_lib as L
    import wiring_module as W
    out=root/'wrist-wire-test';out.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(root/'EDU06_R06.blend'))
    scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'))
    bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update();L.scene=scene
    for attr,start in [('printed','01'),('hardware','02'),('controls','03'),('cables','04'),('studio','05')]:
        setattr(L,attr,next(c for c in scene.collection.children if c.name.startswith(start)))
    L.JOINTS={o.name[:2]:o for o in scene.objects if o.get('axis') and o.name[:2] in ['J1','J2','J3','J4','J5']}
    names={'ivory':'FDM • warm ivory','black':'DYNAMIXEL • black polymer','red':'Cable red','yellow':'Cable yellow','green':'FDM • deep forest green','steel':'Purchased screws and nuts','text':'Light markings'}
    B=SimpleNamespace(M={k:bpy.data.materials[v] for k,v in names.items()},control=next(o for o in scene.objects if o.name.startswith('CONTROL')))
    W.build_wiring(B);bpy.context.view_layer.update()
    for o in scene.objects:
        if o.type=='CURVE' and o.get('harness_id')!='H05_J4_J5':o['conductor']='TEST_EXCLUDED'
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'WRIST_WIRE_TEST.blend'))
    if '--diagnostic' in sys.argv:
        from audit_assembly import find_controls,make_poses,set_pose,world_matrix
        from mathutils import Vector
        c,j=find_controls();c.animation_data_clear();poses,limits=make_poses(c,j)
        rows=[]
        for name,pose in poses:
            if name not in ['home','J3_min','J3_max','J4_min','J4_max','combined_low','combined_high']:continue
            set_pose(c,pose)
            result=W.audit_wiring(scene,[scene.frame_current],out/'working.json')
            cases={o['motor_id']:o for o in scene.objects if o.get('interface_role')=='case' and o.get('motor_id')}
            for row in result['curves'].values():
                for contact in row['structural_contacts']:
                    point=Vector(contact['xyz'])
                    for mid in ['J4_AX','J5_AX']:
                        contact['in_'+mid]=list(world_matrix(cases[mid]).inverted()@point)
                    contact['in_part']=list(world_matrix(bpy.data.objects[contact['part']]).inverted()@point)
            rows.append({'name':name,'pose':pose,'report':result})
        (out/'diagnostic.json').write_text(json.dumps(rows,indent=2))
        return
    report=W.audit_wiring(scene,frames=[1,60,155,200,245,300,360],output=out/'audit.json')
    summary={k:{'bend':v['minimum_bend_radius_mm'],'bend_location':v['minimum_bend_location'],'contacts':v['structural_contacts']} for k,v in report['curves'].items()}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    import traceback
    try:_test()
    except Exception:
        (Path(__file__).resolve().parent/'wrist-wire-test'/'error.txt').write_text(traceback.format_exc())
        raise
