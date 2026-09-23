"""Render the saved EDU06 demonstration in a fresh, separate Blender process.

Never saves changes to the .blend. Output is an actual kinematic preview, not
a load simulation. Run with Blender --background --python this_file.py.
"""
import bpy,json,traceback,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FRAME_DIR=ROOT/'motion-preview-frames'
FRAME_DIR.mkdir(exist_ok=True)
log=(ROOT/'motion-preview-render.log').open('w',encoding='utf-8',buffering=1)
report={'status':'running','frames':[],'input_blend':'EDU06_R06.blend'}
def save_report():
    (ROOT/'motion-preview-render.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
try:
    blend=ROOT/'EDU06_R06.blend'
    report['input_modified']=blend.stat().st_mtime
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 | Engineering'))
    bpy.context.window.scene=scene
    scene.render.resolution_x=720;scene.render.resolution_y=540;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
    # Presentation text is too small at this preview size. Product geometry,
    # lighting, materials, joint drivers, and camera are the saved model's own.
    for name in ['Presentation title','Presentation subtitle','Presentation note']:
        o=bpy.data.objects.get(name)
        if o:o.hide_render=True
    control=next(o for o in bpy.data.objects if o.name.startswith('CONTROL'))
    indices=[1+round(359*i/23) for i in range(24)]
    report['resolution']=[720,540];report['frame_indices']=indices
    save_report()
    for index,frame in enumerate(indices):
        start=time.time();scene.frame_set(frame);bpy.context.view_layer.update()
        path=FRAME_DIR/f'frame-{index:02d}.png'
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True,scene=scene.name)
        item={'index':index,'timeline_frame':frame,'path':str(path),'seconds':round(time.time()-start,2),
              'controls':{key:control.get(key) for key in ['J1','J2','J3','J4','J5','GRIP']},
              'units':{'J1-J5':'degrees','GRIP':'mm'}}
        report['frames'].append(item);save_report();log.write(json.dumps(item)+'\n')
    report['status']='complete';report['saved_model_modified']=False
except Exception:
    report['status']='error';report['error']=traceback.format_exc();log.write(report['error'])
finally:
    save_report();log.close()
