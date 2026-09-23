import sys, json, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
OUT=ROOT/'motor-test';OUT.mkdir(exist_ok=True)
try:
    import blender_lib as L
    from motor_models import make_motor
    from mathutils import Matrix
    L.ROOT=OUT
    L.setup()
    colors={'green':(.06,.21,.16),'ivory':(.7,.73,.63),'black':(.015,.02,.025),
            'steel':(.55,.59,.62),'text':(.8,.9,.85),'red':(.6,.03,.02),'yellow':(.8,.4,.01)}
    mats={k:L.material('TEST '+k,v) for k,v in colors.items()}
    returns={}
    for kind,x in [('AX',-70),('XM',70)]:
        node=L.empty(kind+' test reference')
        result=make_motor(kind,kind+'_TEST',node,L.T(x,0,0),mats)
        returns[kind]={k:v for k,v in result.items() if isinstance(v,(str,int,float,tuple,dict))}
    metrics=L.export_parts()
    (OUT/'results.json').write_text(json.dumps({'parts':metrics,'metadata':returns},indent=2))
    import bpy
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'motor_test.blend'))
    (OUT/'complete.txt').write_text('PASS' if all(p['nonmanifold_edges']==0 and p['volume_mm3']>0 for p in metrics) else 'FAIL')
except Exception:
    (OUT/'error.txt').write_text(traceback.format_exc())
    (OUT/'complete.txt').write_text('ERROR')
    raise
