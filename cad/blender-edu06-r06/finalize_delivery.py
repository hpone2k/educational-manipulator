"""Embed the final documentation; verify geometry and evaluated motion are unchanged."""
from pathlib import Path
from array import array
import bpy, hashlib, json, traceback

ROOT = Path(__file__).resolve().parent
BLEND = ROOT / 'EDU06_R06.blend'

def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def model_fingerprint():
    h = hashlib.sha256()
    def add(value):
        h.update(json.dumps(value, sort_keys=True, default=lambda v: v.to_list() if hasattr(v,'to_list') else v.to_dict() if hasattr(v,'to_dict') else str(v)).encode())
    for mesh in sorted(bpy.data.meshes, key=lambda m:m.name):
        add([mesh.name, len(mesh.vertices), len(mesh.polygons)])
        coords = array('f', [0]) * (3 * len(mesh.vertices))
        mesh.vertices.foreach_get('co', coords)
        h.update(coords.tobytes())
        add([list(p.vertices) for p in mesh.polygons])
    scene = next(s for s in bpy.data.scenes if 'Engineering assembly' in s.name)
    bpy.context.window.scene = scene
    control = next(o for o in scene.objects if o.name.startswith('CONTROL'))
    add([scene.frame_start, scene.frame_end, scene.render.fps, scene.unit_settings.scale_length])
    for obj in sorted(bpy.data.objects, key=lambda o:o.name):
        add([obj.name, obj.type, obj.parent.name if obj.parent else None, dict(obj.items())])
        for constraint in obj.constraints:
            add([obj.name,constraint.name,constraint.type,
                 {p.identifier: getattr(getattr(constraint,p.identifier),'name',None) if p.type=='POINTER' else list(getattr(constraint,p.identifier)) if getattr(p,'is_array',False) else getattr(constraint,p.identifier)
                  for p in constraint.bl_rna.properties if p.identifier!='rna_type' and p.type!='COLLECTION'}])
        if obj.animation_data:
            add([(f.data_path, f.array_index, f.driver.expression,
                  [(v.name, v.type, [(t.id.name if t.id else None, t.data_path) for t in v.targets])
                   for v in f.driver.variables]) for f in obj.animation_data.drivers])
    for key in ['J1','J2','J3','J4','J5','GRIP']:
        add([key, control.id_properties_ui(key).as_dict()])
    for curve in sorted(bpy.data.curves,key=lambda c:c.name):
        if not hasattr(curve,'splines'):continue
        add([curve.name,curve.dimensions,curve.bevel_depth,curve.resolution_u])
        if curve.animation_data:
            add([(f.data_path,f.array_index,f.driver.expression,
                  [(v.name,v.type,[(t.id.name if t.id else None,t.data_path,t.transform_type,t.transform_space) for t in v.targets]) for v in f.driver.variables]) for f in curve.animation_data.drivers])
    for frame in list(range(1,361,12)) + [360]:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        add([frame, {key:round(float(control[key]),8) for key in ['J1','J2','J3','J4','J5','GRIP']}])
        for obj in sorted(scene.objects, key=lambda o:o.name):
            add([obj.name, [round(v,6) for row in obj.matrix_world for v in row]])
            if obj.type=='CURVE':
                data=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
                add([obj.name,[[[round(v,6) for v in p.co] for p in s.points] for s in data.splines]])
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return h.hexdigest()

try:
    original = {'sha256':checksum(BLEND), 'bytes':BLEND.stat().st_size, 'mtime':BLEND.stat().st_mtime}
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    before = model_fingerprint()
    names = ['README.md','engineering-review.md','build_edu06.py','blender_lib.py',
             'motor_models.py','wrist_module.py','gripper_module.py','gear_math.py','mesh_repair.py',
             'base_module.py','arm_module.py','wiring_module.py','base_wiring_guides.py','refresh_wiring.py','reducer_cheek.py','palm_profile.py','wiring-notes.md','wiring-evidence.md','wiring-final-summary.json','base-layout.json',
             'upper_link_wiring_guides.py','wrist_wiring_guides.py','gripper_wiring_guides.py','fixed_jacket_guides.py',
             'gear-profile-audit.json','gripper-math-check.json','wrist-dimensions.json',
             'motor-interface-schedule.json','hardware-bom.json','motor-references/README-official-cad.md']
    for name in names:
        old = bpy.data.texts.get(name)
        if old: bpy.data.texts.remove(old)
        text = bpy.data.texts.new(name)
        text.write((ROOT/name).read_text(encoding='utf-8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    after = model_fingerprint()
    assert before == after, 'Geometry/control/evaluated-animation fingerprint changed'
    result = {'status':'PASS', 'operation':'Documentation-only embedding and resave',
              'audited_native_before_document_embedding':original,
              'delivered_native':{'sha256':checksum(BLEND),'bytes':BLEND.stat().st_size,'mtime':BLEND.stat().st_mtime},
              'model_fingerprint_before':before,'model_fingerprint_after':after,
              'fingerprint_scope':'All mesh vertices/polygons, object parents/custom properties/constraints, object and curve driver expressions/targets, control limits, scene units and31 evaluated full-scene transform and cable-control-point snapshots',
              'embedded_documents':names,
              'embedded_document_sha256':{name:checksum(ROOT/name) for name in names}}
except Exception:
    result = {'status':'ERROR','traceback':traceback.format_exc()}
(ROOT/'delivery-integrity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
