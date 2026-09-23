import bpy, json, traceback, math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
report={}
def capture(label):
    dg=bpy.context.evaluated_depsgraph_get()
    data={"scene":bpy.context.scene.name,"window_scene":bpy.context.window.scene.name if bpy.context.window else None,
          "frame":bpy.context.scene.frame_current,"autoexec":bpy.context.preferences.filepaths.use_scripts_auto_execute,
          "autoexec_fail":bpy.app.autoexec_fail,"autoexec_fail_message":bpy.app.autoexec_fail_message,
          "control":{k:control.get(k) for k in ['J1','J2','J3','J4','J5','J6','GRIP']},"objects":[]}
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.drivers:
            item={"name":o.name,"rotation_mode":o.rotation_mode,"rotation":list(o.rotation_euler),
                  "eval_rotation":list(o.evaluated_get(dg).rotation_euler),"world":list(o.matrix_world.translation),
                  "eval_world":list(o.evaluated_get(dg).matrix_world.translation),"drivers":[]}
            for fc in o.animation_data.drivers:
                d=fc.driver
                dd={"path":fc.data_path,"index":fc.array_index,"expression":d.expression,"valid":d.is_valid,
                    "simple":d.is_simple_expression,"muted":fc.mute,"vars":[]}
                for v in d.variables:
                    targets=[]
                    for t in v.targets:
                        try: resolved=t.id.path_resolve(t.data_path)
                        except Exception as e: resolved=str(e)
                        targets.append({"id":t.id.name if t.id else None,"id_type":t.id_type,"path":t.data_path,"resolved":resolved})
                    dd['vars'].append({"name":v.name,"type":v.type,"targets":targets})
                item['drivers'].append(dd)
            data['objects'].append(item)
    report[label]=data
    (ROOT/'driver-diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
    control=next(o for o in bpy.data.objects if o.name.startswith('CONTROL'))
    capture('loaded')
    bpy.context.scene.frame_set(2);bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    capture('frame_cycle')
    control.update_tag();bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
    capture('control_tag')
    for o in bpy.data.objects:
        if o.animation_data:
            for fc in o.animation_data.drivers:
                fc.driver.expression=fc.driver.expression+' '
    bpy.context.view_layer.update();bpy.context.scene.frame_set(1)
    capture('expression_reset')
    for o in bpy.data.objects:
        if o.name.startswith('J2') and o.animation_data:
            fc=o.animation_data.drivers[0];fc.driver.expression='1.1344640137963142'
    bpy.context.view_layer.update()
    capture('constant_expression')
    # Brand new object with identical driver in the active scene.
    test=bpy.data.objects.new('diagnostic_probe',None);bpy.context.scene.collection.objects.link(test)
    fc=test.driver_add('rotation_euler',2);d=fc.driver;d.type='SCRIPTED';v=d.variables.new();v.name='q';v.type='SINGLE_PROP';v.targets[0].id=control;v.targets[0].data_path='["J2"]';d.expression='q*pi/180'
    bpy.context.view_layer.update()
    capture('new_driver')
except Exception:
    report['error']=traceback.format_exc()
finally:
    (ROOT/'driver-diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
