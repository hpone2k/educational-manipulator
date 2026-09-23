import runpy,traceback
from pathlib import Path
root=Path(__file__).resolve().parent
try:runpy.run_path(str(root/'rebuild_preview.py'),run_name='__main__')
except Exception:(root/'PREVIEW_EARLY_ERROR.txt').write_text(traceback.format_exc())
