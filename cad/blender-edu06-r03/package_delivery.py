"""Create an explicit delivery package, excluding intermediate diagnostics."""
import json,csv,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
metrics=json.loads((ROOT/'part-metrics.json').read_text())
for p in metrics:
    if p['id']=='B01_open_front_base_240x190':
        p['description']='240x190 nominal floor; actual241x190 envelope includes tab ends. Four M4 screws attach feet; bench anchoring separate. Side-loaded M3 top-post nuts.'
(ROOT/'part-metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
with (ROOT/'print-parts.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Part ID','X mm','Y mm','Z mm','Solid PLA estimate g','Description'])
    for p in metrics:w.writerow([p['id'],*[round(x,3) for x in p['dimensions_mm']],round(p['solid_PLA_mass_g'],2),p['description']])
files=['EDU06_R03.blend','README.md','engineering-review.md','motor-and-fastener-guide.md','structural-fasteners.md',
 'assembled-preview.png','base-detail.png','motion-preview.gif','print-parts.csv','part-metrics.json','hole-features.json',
 'motor-interface-schedule.json','gear-pairs.json','gear-profile-audit.json','stl-audit.json','mass-load-audit.json',
 'demo-trajectory-audit.json','motion-preview-verification.json','delivery-integrity.json','research-motors.md','research-mechanics.md',
 'build_edu06.py','blender_lib.py','motor_models.py','gear_math.py','mesh_repair.py','verify_exports.py','audit_assembly.py',
 'audit_demo_trajectory.py','finish_blender.py','render_motion_preview.py','finalize_delivery.py','write_engineering_review.py','package_delivery.py']
paths=[ROOT/f for f in files]+sorted((ROOT/'prototype_stl').glob('*.stl'))
assert all(p.is_file() for p in paths)
stl=json.loads((ROOT/'stl-audit.json').read_text())
assert stl['summary']['all_checks_passed'] and stl['summary']['parts_found']==len(metrics)
audit=json.loads((ROOT/'mass-load-audit.json').read_text())
assert audit['complete'] and not audit['summary']['poses_requiring_collision_review']
demo=json.loads((ROOT/'demo-trajectory-audit.json').read_text())
assert demo['summary']['all_sampled_frames_clear_of_unresolved_crossings_or_penetrations']
output=ROOT/'EDU06_R03_Blender_and_print_prototypes.zip'
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    for p in paths:z.write(p,Path('EDU06_R03')/p.relative_to(ROOT))
with zipfile.ZipFile(output) as z:assert z.testzip() is None
manifest={'zip':output.name,'bytes':output.stat().st_size,'files':len(paths),'printed_parts':len(metrics),
 'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'zip_crc_test':'pass','status':'engineering prototype; physical validation outstanding'}
(ROOT/'package-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
