from pathlib import Path
import bpy,sys,json,itertools,traceback
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));import wiring_module as W;import audit_assembly as A
OUT=ROOT/'gripper-wire-test'
try:
 bpy.ops.wm.open_mainfile(filepath=str(OUT/'H06_TEST.blend'));s=bpy.context.scene;c=next(o for o in s.objects if o.name.startswith('CONTROL'));c.animation_data_clear()
 curves=[o for o in s.objects if o.type=='CURVE' and o.get('harness_id')=='H06_J5_GRIP'];best={o.name:{'radius_mm':1e9} for o in curves};count=0
 spacing={'distance_mm':1e9}
 for pitch,roll in itertools.product(range(-25,26,5),range(-60,61,5)):
  A.set_pose(c,{'J1':0,'J2':65,'J3':55,'J4':pitch,'J5':roll,'GRIP':45});d=bpy.context.evaluated_depsgraph_get()
  paths={}
  for o in curves:
   pts=W.sample_nurbs(o.evaluated_get(d).data.splines[0],401);paths[o.get('conductor')]=pts
   for i,(a,b,z) in enumerate(zip(pts,pts[1:],pts[2:])):
    cross=(b-a).cross(z-a).length
    if cross<1e-8:continue
    r=(a-b).length*(b-z).length*(z-a).length/(2*cross)
    if r<best[o.name]['radius_mm']:best[o.name]=dict(radius_mm=r,pitch_deg=pitch,roll_deg=roll,sample=i+1)
  for an,bn in [('GND','VDD'),('VDD','DATA'),('GND','DATA')]:
   aa,bb=paths[an],paths[bn];tree=KDTree(len(bb))
   for j,p in enumerate(bb):tree.insert(p,j)
   tree.balance()
   for i,p in enumerate(aa):
    for _,j,_ in tree.find_n(p,2):
     for k in [j-1,j]:
      if k<0 or k>=len(bb)-1:continue
      edge=bb[k+1]-bb[k];t=max(0,min(1,(p-bb[k]).dot(edge)/edge.length_squared));dist=(p-(bb[k]+edge*t)).length
      if dist<spacing['distance_mm']:spacing=dict(distance_mm=dist,pitch_deg=pitch,roll_deg=roll,pair=[an,bn],sample=i,segment=k)
  count+=1
 (OUT/'dense-bend-audit.json').write_text(json.dumps(dict(pose_count=count,curve_samples=401,passed=all(v['radius_mm']>=12 for v in best.values()),curves=best,minimum_strand_distance=spacing,insulation_diameter_mm=1.44,strand_clearance_passed=spacing['distance_mm']>=1.44),indent=2),encoding='utf-8')
except Exception:(OUT/'DENSE_ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8')
