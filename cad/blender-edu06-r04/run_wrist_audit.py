import sys,runpy,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
(ROOT/'wrist-audit-started.txt').write_text('Started')
sys.argv=['blender','--','--blend',str(ROOT/'WRIST_DEBUG.blend'),'--output',str(ROOT/'wrist-debug-audit.json'),'--wrist-debug']
try:runpy.run_path(str(ROOT/'audit_assembly.py'),run_name='__main__')
except Exception:(ROOT/'wrist-audit-error.txt').write_text(traceback.format_exc())
