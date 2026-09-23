import sys,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy,bmesh
from mathutils import Matrix
import build_edu06 as B
import blender_lib as L
from wrist_module import build_wrist
build_wrist(None,Matrix.Identity(4),B.control,B.M,B.HOME)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'WRIST_DEBUG.blend'))
try:
    L.export_parts()
except Exception:
    (ROOT/'WRIST_DEBUG_ERROR.txt').write_text(traceback.format_exc())
