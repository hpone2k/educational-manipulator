"""Embed reports and save inspection state; no manufacturing geometry edits."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
scene=next(s for s in bpy.data.scenes if 'Engineering assembly' in s.name)
bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
def fingerprint():
    records=[]
    for o in sorted(scene.objects,key=lambda x:x.name):
        if o.type=='MESH' and (o.get('part_id') or o.get('reference_only')):
            records.append({'name':o.name,'vertices':[list(v.co) for v in o.data.vertices],
              'polygons':[list(p.vertices) for p in o.data.polygons],
              'matrix_world':[list(row) for row in o.matrix_world]})
    return hashlib.sha256(json.dumps(records,separators=(',',':')).encode()).hexdigest()
before=fingerprint()
for name in ['README.md','engineering-review.md','motor-and-fastener-guide.md','structural-fasteners.md']:
    previous=bpy.data.texts.get(name)
    if previous:bpy.data.texts.remove(previous)
    text=bpy.data.texts.new(name);text.write((ROOT/name).read_text(encoding='utf-8'))
scene['STATUS']='Dimensioned prototype: 179 STL checks;18 pose samples;31 animation snapshots. No physical payload, strength or thermal validation.'
scene['PRINT_FIRST']='F01 hole/nut coupon; F02 AX/XM horn coupons; one cradle and journal fit pair.'
scene['UNITS']='mm; STL files also mm, import at100%scale.'
scene['MODEL_USAGE']='Select CONTROL custom properties; six joints plus gripper. Timeline360frames. See README text datablock.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.overlay.show_overlays=False;space.shading.type='MATERIAL'
            space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=10
        elif area.type=='PROPERTIES':area.spaces.active.context='OBJECT'
after=fingerprint();assert before==after,'Metadata pass must not change manufacturing geometry or home pose'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
(ROOT/'delivery-integrity.json').write_text(json.dumps({
 'assembly_geometry_sha256':after,'geometry_unchanged_by_report_embedding':before==after,
 'printed_parts_in_assembly':sum(bool(o.get('part_id')) for o in scene.objects),
 'source_geometry_audit':'mass-load-audit.json, native geometry build 2026-09-23 13:57:01 local',
 'presentation_only_save':True,'physical_function_validated':False},indent=2))
print('Final reports embedded; geometry unchanged')
