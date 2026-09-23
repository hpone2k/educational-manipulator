"""Create the reproducible prototype package, excluding temporary/debug files."""
from pathlib import Path
import csv, hashlib, json, zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parent
delivery=json.loads((ROOT/'delivery-integrity.json').read_text(encoding='utf-8'))
assert delivery['status'] == 'PASS'
assert delivery['delivered_native']['sha256']==hashlib.sha256((ROOT/'EDU06_R06.blend').read_bytes()).hexdigest(), 'Native file changed after delivery integrity check'
assert json.loads((ROOT/'motion-preview-render.json').read_text())['status'] == 'complete'
assembly=json.loads((ROOT/'mass-load-audit.json').read_text(encoding='utf-8'))
assert assembly['complete'] and not assembly['summary']['operating_poses_requiring_collision_review']
for key in ['neutral_centreline_alignment_passed','bilateral_link_geometry_passed','bilateral_structural_assembly_interfaces_clear','reserved_electronics_service_space_clear','actual_six_motor_five_arm_DOF_inventory_passed']:
    assert assembly['summary'][key],key
motion=json.loads((ROOT/'demo-trajectory-audit.json').read_text(encoding='utf-8'))
assert motion['complete'] and motion['summary']['all_sampled_frames_clear_of_unresolved_crossings_or_penetrations']
wire=json.loads((ROOT/'wiring-audit.json').read_text(encoding='utf-8'))
for key in ['endpoints_attached','gear_route_clear','structure_route_clear','all_bends_at_least_12mm','strands_separated']:
    assert wire[key],key
operating_wire=json.loads((ROOT/'wiring-operating-range-audit.json').read_text(encoding='utf-8'))
for key in ['endpoints_attached','gear_route_clear','structure_route_clear','all_bends_at_least_12mm','strands_separated']:
    assert operating_wire[key], 'Operating cable range: '+key
for name in ['wiring-kinematics-audit.json','fixed-jacket-audit.json']:
    assert json.loads((ROOT/name).read_text(encoding='utf-8'))['all_passed'],name
refresh=json.loads((ROOT/'WIRING_REFRESH_COMPLETE.json').read_text(encoding='utf-8'))
assert refresh['engineering_before']==refresh['engineering_after'], 'Cable refresh changed engineering meshes'
frames = [Image.open(p).convert('RGB') for p in sorted((ROOT/'motion-preview-frames').glob('frame-*.png'))]
assert len(frames) == 24
frames[0].save(ROOT/'motion-preview.gif', save_all=True, append_images=frames[1:], duration=180, loop=0)
parts = json.loads((ROOT/'part-metrics.json').read_text())
stl_summary=json.loads((ROOT/'stl-audit.json').read_text())['summary']
assert stl_summary['all_checks_passed'] and len(parts)==stl_summary['parts_found']
with (ROOT/'print-parts.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.writer(fp)
    writer.writerow(['Part ID','X mm','Y mm','Z mm','Solid PLA mass g','Description'])
    for part in parts:
        writer.writerow([part['id'],*[round(v,3) for v in part['dimensions_mm']],round(part['solid_PLA_mass_g'],3),part['description']])
with (ROOT/'hardware-bom.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.writer(fp);writer.writerow(['Hardware','Diameter mm','Length mm','Quantity'])
    for row in json.loads((ROOT/'hardware-bom.json').read_text()):
        writer.writerow([row['kind'],row['diameter_mm'],row['length_mm'],row['quantity']])
names = '''EDU06_R06.blend README.md engineering-review.md assembled-preview.png base-detail.png
wrist-straight-preview.png motor-map.png motion-preview.gif print-parts.csv hardware-bom.csv
top-alignment-preview.png top-alignment-render.json wiring-notes.md wiring-evidence.md wiring-final-summary.json base-layout.json WIRING_REFRESH_COMPLETE.json
build_edu06.py blender_lib.py motor_models.py wrist_module.py gripper_module.py gear_math.py mesh_repair.py
base_module.py arm_module.py wiring_module.py base_wiring_guides.py refresh_wiring.py reducer_cheek.py palm_profile.py audit_wiring.py render_top_alignment.py
upper_link_wiring_guides.py wrist_wiring_guides.py gripper_wiring_guides.py fixed_jacket_guides.py
verify_exports.py audit_assembly.py audit_demo_trajectory.py finish_blender.py render_inspection.py
render_motion_preview.py render_motor_map.py finalize_delivery.py package_delivery.py
part-metrics.json hole-features.json hardware-bom.json gear-pairs.json motor-interface-schedule.json
gripper-design-notes.json wrist-dimensions.json gear-profile-audit.json gripper-math-check.json
stl-audit.json export-manifest-audit.json mass-load-audit.json demo-trajectory-audit.json delivery-integrity.json motion-preview-render.json wiring-audit.json wiring-connectivity.json wiring-operating-range-audit.json wiring-kinematics-audit.json fixed-jacket-audit.json'''.split()
references = '''AX-12A.pdf AX-12A.stp XM_H-430_idler.pdf XM_H-430_idler.stp AX-official-mm.json.gz
XM-official-mm.json.gz README-official-cad.md official-downloads.json cad-conversion-report.json
normalized-mesh-summary.json motor-import-test.json vendor-cache-test.json ax-shim-connectivity-test.json
test_vendor_motor_import.py test_vendor_cache.py test_ax_shim_connectivity.py
convert_official_cad.py normalize_motor_meshes.py AX-12A-drawing.png XM_H-430_idler-drawing.png'''.split()
names += ['motor-references/'+name for name in references]
names += ['H06-route-evidence.json']
names += ['gripper-wire-test/'+name for name in ['test_h06.py','test_dense_bends.py','audit.json','operating-audit.json','dense-bend-audit.json']]
names += ['prototype_stl/'+part['id']+'.stl' for part in parts]
assert len(names) == len(set(names))
entries=[]
for name in names:
    path=ROOT/name
    assert path.is_file(),name
    entries.append({'path':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'package-manifest.json').write_text(json.dumps({'files':entries,'prototype_only':True},indent=2),encoding='utf-8')
zip_path = ROOT/'EDU06_R06_Blender_and_Print_Prototype.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in names+['package-manifest.json']: z.write(ROOT/name,'EDU06_R06/'+name)
with zipfile.ZipFile(zip_path) as z: assert z.testzip() is None
result={'status':'PASS','archive':str(zip_path),'bytes':zip_path.stat().st_size,'files':len(names)+1,'printable_parts':len(parts),'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest()}
(ROOT/'PACKAGE_COMPLETE.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
