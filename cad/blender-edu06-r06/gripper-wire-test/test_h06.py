from pathlib import Path
from types import SimpleNamespace
import sys,json,traceback
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import blender_lib as L
import wiring_module as W
from gripper_wiring_guides import configure_gripper_route
OUT=ROOT/'gripper-wire-test'
try:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R06.blend'))
 scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'));bpy.context.window.scene=scene
 L.scene=scene
 for attr,start in [('printed','01'),('hardware','02'),('controls','03'),('cables','04'),('studio','05')]:setattr(L,attr,next(c for c in scene.collection.children if c.name.startswith(start)))
 L.JOINTS={o.name[:2]:o for o in scene.objects if o.get('axis') and o.name[:2] in ['J1','J2','J3','J4','J5']}
 scene.frame_set(1);bpy.context.view_layer.update()
 matnames={'ivory':'FDM • warm ivory','black':'DYNAMIXEL • black polymer','red':'Cable red','yellow':'Cable yellow','green':'FDM • deep forest green','steel':'Purchased screws and nuts','text':'Light markings'}
 B=SimpleNamespace(M={k:bpy.data.materials[v] for k,v in matnames.items()},control=next(o for o in scene.objects if o.name.startswith('CONTROL')))
 # Existing authoritative native wiring has connector datums; replace H06 only.
 cases={o['motor_id']:o for o in scene.objects if o.get('interface_role')=='case'}
 ports={}
 for key in ['J5_AX','GRIP']:
  ports[key]=[]
  for letter in ['A','B']:
   name=key+' PORT '+letter
   ports[key].append(dict(port=bpy.data.objects[name],end=bpy.data.objects[name+' / wire exit'],straight=bpy.data.objects[name+' / straight strain relief'],far=bpy.data.objects[name+' / rear service guide'],turn=bpy.data.objects[name+' / broad rear bend'],family='MOLEX 50-37-5033'))
 for o in list(scene.objects):
  if o.name.startswith('H06_J5_GRIP'):bpy.data.objects.remove(o,do_unlink=True)
 guides=configure_gripper_route(ports,cases,B)
 W._bundle('H06_J5_GRIP',ports['J5_AX'][1],ports['GRIP'][0],guides,B.M,{'harnesses':[]})
 for o in scene.objects:
  if o.type=='CURVE' and o.get('harness_id')!='H06_J5_GRIP':o['conductor']='OTHER'
 bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'H06_TEST.blend'))
 report=W.audit_wiring(scene,frames=[round(1+i*359/30) for i in range(31)],output=OUT/'audit.json')
 summary={k:{'bend':v['minimum_bend_radius_mm'],'endpoint_error':v['endpoint_max_error_mm'],'contacts':v['structural_contacts'],'bend_location':v.get('minimum_bend_location')} for k,v in report['curves'].items()}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
except Exception:
 (OUT/'ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8')
