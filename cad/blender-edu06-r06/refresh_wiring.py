"""Rebuild only wiring on a saved R06; all engineering meshes are fingerprinted.

blender --background --python refresh_wiring.py [-- --input file --output file]
Default output replaces EDU06_R06.blend. Never run against an unsaved GUI scene.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,struct,argparse,traceback
import bpy
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import blender_lib as L
from wiring_module import build_wiring
p=argparse.ArgumentParser();p.add_argument('--input',default=str(ROOT/'EDU06_R06.blend'))
p.add_argument('--output',default=str(ROOT/'EDU06_R06.blend'))
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
def fingerprint(scene):
    h=hashlib.sha256();count=0
    for o in sorted(scene.objects,key=lambda o:o.name):
        if o.type!='MESH' or o.get('wiring_object'):continue
        count+=1;h.update(o.name.encode());h.update((o.parent.name if o.parent else '').encode())
        for row in o.matrix_basis:h.update(struct.pack('<4f',*row))
        for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
        for poly in o.data.polygons:h.update(struct.pack('<I',len(poly.vertices)));h.update(struct.pack('<'+'I'*len(poly.vertices),*poly.vertices))
    return {'meshes':count,'sha256':h.hexdigest()}
try:
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.input)))
    scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |'))
    bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
    before=fingerprint(scene);L.scene=scene
    for attr,start in [('printed','01'),('hardware','02'),('controls','03'),('cables','04'),('studio','05')]:
        setattr(L,attr,next(c for c in scene.collection.children if c.name.startswith(start)))
    L.JOINTS={o.name[:2]:o for o in scene.objects if o.get('axis') and o.name[:2] in ['J1','J2','J3','J4','J5']}
    matnames={'ivory':'FDM • warm ivory','black':'DYNAMIXEL • black polymer','red':'Cable red','yellow':'Cable yellow','green':'FDM • deep forest green','steel':'Purchased screws and nuts','text':'Light markings'}
    B=SimpleNamespace(M={k:bpy.data.materials[v] for k,v in matnames.items()},control=next(o for o in scene.objects if o.name.startswith('CONTROL')))
    build_wiring(B);bpy.context.view_layer.update()
    after=fingerprint(scene)
    assert before==after,f'Engineering mesh mutation rejected: {before} != {after}'
    for name in ['wiring_module.py','base_wiring_guides.py','upper_link_wiring_guides.py','wrist_wiring_guides.py','gripper_wiring_guides.py','fixed_jacket_guides.py','refresh_wiring.py','audit_wiring.py','wiring-notes.md']:
        path=ROOT/name
        if path.exists():
            text=bpy.data.texts.get(name) or bpy.data.texts.new(name);text.clear();text.write(path.read_text(encoding='utf-8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.output)))
    (ROOT/'WIRING_REFRESH_COMPLETE.json').write_text(json.dumps({'input':a.input,'output':a.output,'engineering_before':before,'engineering_after':after},indent=2))
except Exception:
    (ROOT/'WIRING_REFRESH_ERROR.txt').write_text(traceback.format_exc());raise

