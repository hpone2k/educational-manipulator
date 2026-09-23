"""Read-only reproducible native harness audit: blender -b --python audit_wiring.py.

Optional: -- --blend relative-or-absolute.blend --frames 1,60,360 --output path
"""
from pathlib import Path
import argparse,sys,json,traceback
import bpy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from wiring_module import audit_wiring
p=argparse.ArgumentParser();p.add_argument('--blend',default=str(ROOT/'EDU06_R06.blend'))
p.add_argument('--frames',default='');p.add_argument('--output',default=str(ROOT/'wiring-audit.json'))
p.add_argument('--operating-range',action='store_true',help='Read-only named operating poses from the independent assembly auditor, excluding diagnostic poses outside declared limits.')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
try:
    src=Path(a.blend);src=src if src.is_absolute() else ROOT/src
    bpy.ops.wm.open_mainfile(filepath=str(src))
    scene=next(s for s in bpy.data.scenes if s.name.startswith('EDU06 R06 |') or s.name.startswith('EDU06 R05 |'))
    bpy.context.window.scene=scene
    if a.operating_range:
        from audit_assembly import find_controls,make_poses,outside_limits,set_pose
        controller,joints=find_controls();poses,limits=make_poses(controller,joints)
        controller.animation_data_clear()
        records=[]
        for name,pose in poses:
            if outside_limits(pose,limits):continue
            set_pose(controller,pose)
            row=audit_wiring(scene,[scene.frame_current],str(a.output)+'.working.json')
            records.append(dict(name=name,control_values=pose,report=row))
        report=dict(revision='R06',limits=limits,poses=records,
                    endpoints_attached=all(r['report']['endpoints_attached'] for r in records),
                    gear_route_clear=all(r['report']['gear_route_clear'] for r in records),
                    structure_route_clear=all(r['report']['structure_route_clear'] for r in records),
                    all_bends_at_least_12mm=all(r['report']['all_bends_at_least_12mm'] for r in records),
                    strands_separated=all(r['report']['strands_separated'] for r in records),
                    limitation='Discrete named operating poses, not continuous or exhaustive cable flex/clearance validation. Source native file was not saved.')
        Path(a.output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    else:
        report=audit_wiring(scene,[int(x) for x in a.frames.split(',')] if a.frames else None,a.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ['curves','poses']}),flush=True)
except Exception:
    Path(str(a.output)+'.error.txt').write_text(traceback.format_exc());raise
