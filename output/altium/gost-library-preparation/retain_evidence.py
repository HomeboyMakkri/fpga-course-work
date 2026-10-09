from prepare import *
from datetime import datetime
for folder,c in CONFIG:
 bundle=OUT/(c+'-v2') if c.startswith('RTL') else OUT/c
 failed=bundle/'readback-result.json';shutil.copy2(failed,bundle/'final-reopen-failed.json')
 candidates=sorted((ROOT/'tools/altium/runtime/jobs').glob('*/result.txt'),key=lambda p:p.stat().st_mtime,reverse=True)
 for p in candidates:
  try:r=json.loads(p.read_text(encoding='utf-8-sig'))
  except (ValueError,UnicodeError):continue
  if isinstance(r,dict) and r.get('component')==c and 'graphics' in r and all(x['electrical']==7 for x in r['pins']):
   dump(failed,{'success':True,'result':r,'job_dir':str(p.parent),'retained_last_successful_native_readback':True,'final_reopen_after_description_restore':False});print(c,p.parent);break
 else:raise RuntimeError(c)
