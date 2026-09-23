import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EDU06_R03.blend'))
scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06'))
bpy.context.window.scene=scene
scene.frame_set(1)
bpy.context.view_layer.update()
scene.render.resolution_percentage=50
scene.cycles.samples=12
scene.render.filepath=str(ROOT/'driver-freshload-preview.png')
bpy.ops.render.render(write_still=True,scene=scene.name)
(ROOT/'driver-render-done.json').write_text(json.dumps({'done':True,'filepath':scene.render.filepath}),encoding='utf-8')
