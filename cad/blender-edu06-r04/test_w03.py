import sys,json,textwrap,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy,bmesh
import blender_lib as L
from wrist_module import *
L.setup();j5=empty('test');forward=41.
mats={k:L.material(k,(.1,.2,.1)) for k in ['green','ivory','steel']}
s=(ROOT/'wrist_module.py').read_text(encoding='utf-8')
s=s[s.index('    rear=-forward'):s.index('    for sign in [-1,1]:\n        stub=')]
exec(textwrap.dedent(s))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'W03_TEST.blend'))
try:
 L.ROOT=ROOT/'w03-test';L.ROOT.mkdir(exist_ok=True);L.export_parts()
 (ROOT/'W03_TEST_OK.json').write_text(json.dumps({'ok':True}))
except Exception:(ROOT/'W03_TEST_ERROR.txt').write_text(traceback.format_exc())
