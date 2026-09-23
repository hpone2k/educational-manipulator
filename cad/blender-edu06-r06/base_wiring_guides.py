"""Native route anchors for the enlarged base; geometry is never hidden.

The J1-to-J2 route uses the actual hollow yaw shaft and the matching Ø16
pedestal passage. Prototype cable envelopes and bend radii remain measurable
assumptions rather than purchased cable ratings.
"""
from pathlib import Path


def configure_base_routes(ports, u2d2, hub_input, hub_output, yaw, B):
    from wiring_module import _empty

    def guides(harness, coordinates, parent=None):
        result=[_empty(harness+f' / base routing guide {index:02d}',parent,point)
                for index,point in enumerate(coordinates)]
        for obj in result:
            obj['control_polygon_only']=True
        return result

    # Broad rear-side sweep between fixed electronics, away from the controller
    # tray reserve at the front of the enclosure.
    u2d2['straight'].location.z=14
    u2d2['far'].location=(8,0,24)
    h00=guides('H00_U2D2_POWER',[(-55,85,18),(-25,83,23),(10,70,24)])

    # Use the open space under the base motor between its four floor spacers.
    # End/port datums stay fixed; only free-service guide locations are changed.
    for port in ports['J1_BASE']:
        x=port['port'].location.x
        port['straight'].location.z=21.3
        port['far'].location=(x,15,-59)
        port['turn'].location=(x,50,-49)
    base_input=ports['J1_BASE'][0]
    # These are non-interpolated NURBS control coordinates, not physical cable
    # clips. Clearance/bend checks use the evaluated curve, including the floor
    # clearance; a control point need not itself lie on the cable centreline.
    base_input['straight'].location.z=20.1203
    base_input['far'].location=(-4.95,12.528,-61.2406)
    base_input['turn'].location=(-4.95,32.8051,-45.4048)
    hub_output['far'].location=(-5.8986,4.0509,34.2136)
    h01=[]

    # S_XM A has a clear sideways approach between its bridge posts. The old
    # rising guide crossed the upper bridge leg; keep the first approach at the
    # actual socket height, then turn outside the complete support envelope.
    shoulder=ports['S_XM'][0]
    shoulder['straight'].location.z=14
    shoulder['far'].location=(-40,-14.55,-29.875)
    shoulder['turn'].location=(-65,-14.55,-60)
    fixed=guides('H02_J1_J2',[(37.05,70,16),(12,83,16),(-28,80,16),(-40,55,16),(-28,35,16),
                             (-28,0,16),(-28,0,50),(-28,0,65),(-28,0,85)])
    moving=guides('H02_J1_J2 yaw',[(0,0,95),(0,0,120),(0,0,144),
                                  (38,0,148),(52,30,148),(38,66,148),
                                  (-60,70,148),(-125,65,157),(-142,42,171.45)],yaw)
    return {'H00_U2D2_POWER':h00,'H01_POWER_J1':h01,'H02_J1_J2':fixed+moving}


def _test():
    """Development-only fresh-load test copy; never overwrites the source."""
    import sys,json,traceback
    from types import SimpleNamespace
    import bpy
    root=Path(__file__).resolve().parent
    sys.path.insert(0,str(root))
    import blender_lib as L
    import wiring_module as W
    out=root/'base-wire-test';out.mkdir(exist_ok=True)
    try:
        bpy.ops.wm.open_mainfile(filepath=str(root/'EDU06_R06.blend'))
        scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'))
        bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
        L.scene=scene
        for attr,start in [('printed','01'),('hardware','02'),('controls','03'),('cables','04'),('studio','05')]:
            setattr(L,attr,next(c for c in scene.collection.children if c.name.startswith(start)))
        L.JOINTS={o.name[:2]:o for o in scene.objects if o.get('axis') and o.name[:2] in ['J1','J2','J3','J4','J5']}
        matnames={'ivory':'FDM • warm ivory','black':'DYNAMIXEL • black polymer','red':'Cable red',
                  'yellow':'Cable yellow','green':'FDM • deep forest green','steel':'Purchased screws and nuts','text':'Light markings'}
        B=SimpleNamespace(M={k:bpy.data.materials[v] for k,v in matnames.items()},
                          control=next(o for o in scene.objects if o.name.startswith('CONTROL')))
        W.build_wiring(B);bpy.context.view_layer.update()
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'WIRING_BASE_TEST.blend'))
        bpy.ops.wm.open_mainfile(filepath=str(out/'WIRING_BASE_TEST.blend'))
        scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'))
        bpy.context.window.scene=scene
        report=W.audit_wiring(scene,frames=[1,155,245],output=out/'audit.json')
        summary={k:{'minimum_bend_radius_mm':v['minimum_bend_radius_mm'],
                    'endpoint_error_mm':v['endpoint_max_error_mm'],
                    'contact_parts':sorted(set(x['part'] for x in v['structural_contacts'])),
                    'contacts':v['structural_contacts']}
                 for k,v in report['curves'].items() if v['conductor']=='CENTRE' and k.startswith(('H00','H01','H02'))}
        (out/'summary.json').write_text(json.dumps(summary,indent=2))
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc());raise


if __name__=='__main__':
    _test()
