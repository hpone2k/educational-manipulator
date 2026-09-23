"""Refresh wrist on a saved lower assembly for independent clearance diagnostics."""
import sys,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Matrix
import build_edu06 as B
import blender_lib as L
from wrist_module import build_wrist
from gear_math import pair_spec
matnames={k:v.name for k,v in B.M.items()}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'BUILD_DEBUG.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R04 | Engineering'))
bpy.context.window.scene=scene
B.scene=scene;B.M={k:(bpy.data.materials.get(n) or L.material(n,(.018,.038,.031),rough=.5)) for k,n in matnames.items()}
B.control=next(o for o in scene.objects if o.name.startswith('CONTROL'));B.control.animation_data_clear()
for attr,prefix in [('printed','01 PRINTED'),('hardware','02 PURCHASED'),('controls','03 JOINT'),('cables','04 CABLE'),('studio','05 STUDIO')]:setattr(L,attr,next(c for c in scene.collection.children if c.name.startswith(prefix)))
old=next(o for o in scene.objects if o.name.startswith('J4 ') and 'DATUM' in o.name)
parent=old.parent;tf=old.matrix_basis.copy()
def beneath(o,a):
 while o:
  if o==a:return True
  o=o.parent
 return False
for o in [o for o in scene.objects if beneath(o,old)]:bpy.data.objects.remove(o,do_unlink=True)
st3=next(o for o in scene.objects if o.name.startswith('J3 ') and 'DATUM' in o.name)
if not bpy.data.objects.get('J3 fixed gearbox clocked 90deg'):
 fixed=L.empty('J3 fixed gearbox clocked 90deg',st3,L.R('Z',90))
 for o in list(st3.children):
  if o==fixed or o.get('axis')=='LOCAL Z':continue
  mat=o.matrix_basis.copy();o.parent=fixed;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=mat
  if o.get('rigid_group')==st3.name:o['rigid_group']=fixed.name
L.PRINT=[o for o in scene.objects if o.get('part_id')]
L.REFS=[o for o in scene.objects if o.get('reference_only')]
L.JOINTS={k:next(o for o in scene.objects if o.name.startswith(k+' ') and o.get('axis')) for k in ['J1','J2','J3']}
from motor_models import _retain_ax_front_seating_piece
for o in L.PRINT:
 if o.name.endswith('_C04_1_Axial_fit_shim_030') and ('XM' not in o.name):_retain_ax_front_seating_piece(o)
try:
 j6,grip,pair=build_wrist(parent,tf,B.control,B.M,B.HOME)
 B.animate();bpy.context.view_layer.update()
 specs=[]
 for key,nt,m in [('J1',60,1.5),('J2',100,1.25),('J3',80,1.25)]:
  pin=next(o for o in scene.objects if o.name.startswith(key+' ') and ('pinion' in o.name))
  specs.append({'name':key,'pinion':pin.name,'wheel':L.JOINTS[key].name,**pair_spec(20,nt,m)})
 specs.append(pair)
 (ROOT/'gear-pairs.json').write_text(json.dumps(specs,indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CHECK_ASSEMBLY.blend'))
 L.ROOT=ROOT/'preview-export';L.ROOT.mkdir(exist_ok=True);L.export_parts()
 (ROOT/'PREVIEW_READY.json').write_text(json.dumps({'ok':True}))
except Exception:(ROOT/'PREVIEW_ERROR.txt').write_text(traceback.format_exc())
