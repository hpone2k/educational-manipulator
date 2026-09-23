"""Wide external shoulder-to-elbow service loop, with native anchor drivers."""
from pathlib import Path


def configure_upper_link_route(ports,cases,B):
    from wiring_module import _bridge_anchor
    src=ports['S_XM'][1]
    dst=ports['E_XM'][0]
    src['straight'].location.z=23
    src['far'].location=(50,10,-29.875)
    src['turn'].location=(50,55,-90)
    dst['straight'].location.z=20
    dst['far'].location=(-50,-14.55,-29.875)
    dst['turn'].location=(-95,-14.55,-50)
    return [_bridge_anchor('H03_J2_J3 / broad outer loop 1',src['turn'],dst['turn'],.33,(-60,10,-15),cases['S_XM']),
            _bridge_anchor('H03_J2_J3 / broad outer loop 2',src['turn'],dst['turn'],.67,(-60,10,-15),cases['S_XM'])]


def _test():
    import sys,json,traceback
    from types import SimpleNamespace
    import bpy
    root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
    import blender_lib as L
    import wiring_module as W
    out=root/'upper-link-wire-test';out.mkdir(exist_ok=True)
    try:
        bpy.ops.wm.open_mainfile(filepath=str(root/'EDU06_R06.blend'))
        scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'))
        bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update();L.scene=scene
        for attr,start in [('printed','01'),('hardware','02'),('controls','03'),('cables','04'),('studio','05')]:
            setattr(L,attr,next(c for c in scene.collection.children if c.name.startswith(start)))
        L.JOINTS={o.name[:2]:o for o in scene.objects if o.get('axis') and o.name[:2] in ['J1','J2','J3','J4','J5']}
        matnames={'ivory':'FDM • warm ivory','black':'DYNAMIXEL • black polymer','red':'Cable red',
                  'yellow':'Cable yellow','green':'FDM • deep forest green','steel':'Purchased screws and nuts','text':'Light markings'}
        B=SimpleNamespace(M={k:bpy.data.materials[v] for k,v in matnames.items()},
                          control=next(o for o in scene.objects if o.name.startswith('CONTROL')))
        W.build_wiring(B);bpy.context.view_layer.update()
        for o in scene.objects:
            if o.type=='CURVE' and o.get('harness_id')!='H03_J2_J3':o['conductor']='TEST_EXCLUDED'
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'WIRING_UPPER_TEST.blend'))
        bpy.ops.wm.open_mainfile(filepath=str(out/'WIRING_UPPER_TEST.blend'))
        scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'));bpy.context.window.scene=scene
        W.audit_wiring(scene,frames=[1,60,155,200,245,300,360],output=out/'audit.json')
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc());raise


if __name__=='__main__':
    _test()
