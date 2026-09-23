"""Create the reproducible prototype package, excluding temporary/debug files."""
from pathlib import Path
import csv, hashlib, json, zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parent
assert json.loads((ROOT/'delivery-integrity.json').read_text())['status'] == 'PASS'
assert json.loads((ROOT/'motion-preview-render.json').read_text())['status'] == 'complete'
frames = [Image.open(p).convert('RGB') for p in sorted((ROOT/'motion-preview-frames').glob('frame-*.png'))]
assert len(frames) == 24
frames[0].save(ROOT/'motion-preview.gif', save_all=True, append_images=frames[1:], duration=180, loop=0)
parts = json.loads((ROOT/'part-metrics.json').read_text())
assert len(parts) == 186
with (ROOT/'print-parts.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.writer(fp)
    writer.writerow(['Part ID','X mm','Y mm','Z mm','Solid PLA mass g','Description'])
    for part in parts:
        writer.writerow([part['id'],*[round(v,3) for v in part['dimensions_mm']],round(part['solid_PLA_mass_g'],3),part['description']])
with (ROOT/'hardware-bom.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.writer(fp);writer.writerow(['Hardware','Diameter mm','Length mm','Quantity'])
    for row in json.loads((ROOT/'hardware-bom.json').read_text()):
        writer.writerow([row['kind'],row['diameter_mm'],row['length_mm'],row['quantity']])
names = '''EDU06_R04.blend README.md engineering-review.md assembled-preview.png base-detail.png
wrist-straight-preview.png motion-preview.gif print-parts.csv hardware-bom.csv
build_edu06.py blender_lib.py motor_models.py wrist_module.py gripper_module.py gear_math.py mesh_repair.py
verify_exports.py audit_assembly.py audit_demo_trajectory.py finish_blender.py render_inspection.py
render_motion_preview.py finalize_delivery.py package_delivery.py
part-metrics.json hole-features.json hardware-bom.json gear-pairs.json motor-interface-schedule.json
gripper-design-notes.json wrist-dimensions.json gear-profile-audit.json gripper-math-check.json
stl-audit.json mass-load-audit.json demo-trajectory-audit.json delivery-integrity.json motion-preview-render.json'''.split()
references = '''AX-12A.pdf AX-12A.stp XM_H-430_idler.pdf XM_H-430_idler.stp AX-official-mm.json.gz
XM-official-mm.json.gz README-official-cad.md official-downloads.json cad-conversion-report.json
normalized-mesh-summary.json motor-import-test.json vendor-cache-test.json ax-shim-connectivity-test.json
test_vendor_motor_import.py test_vendor_cache.py test_ax_shim_connectivity.py
convert_official_cad.py normalize_motor_meshes.py AX-12A-drawing.png XM_H-430_idler-drawing.png'''.split()
names += ['motor-references/'+name for name in references]
names += ['prototype_stl/'+part['id']+'.stl' for part in parts]
assert len(names) == len(set(names))
entries=[]
for name in names:
    path=ROOT/name
    assert path.is_file(),name
    entries.append({'path':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'package-manifest.json').write_text(json.dumps({'files':entries,'prototype_only':True},indent=2),encoding='utf-8')
zip_path = ROOT/'EDU06_R04_Blender_and_Print_Prototype.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in names+['package-manifest.json']: z.write(ROOT/name,'EDU06_R04/'+name)
with zipfile.ZipFile(zip_path) as z: assert z.testzip() is None
result={'status':'PASS','archive':str(zip_path),'bytes':zip_path.stat().st_size,'files':len(names)+1,'printable_parts':len(parts),'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest()}
(ROOT/'PACKAGE_COMPLETE.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
