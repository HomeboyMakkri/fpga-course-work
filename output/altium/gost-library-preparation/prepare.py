from pathlib import Path
import sys,json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/altium'))
sys.path.insert(0,str(ROOT/'output/altium/component-preparation'))
from read_native_inventory import inspect
from gost_symbol import readback_request,prepare
CONFIG=[('HR911130A','HR911130A'),('LDO SPX3819M5-L-3-3','SPX3819M5-L-3-3'),('RTL8211E-VB-CG','RTL8211E-VB-CG')]
def dump(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def inventory():
 rows=[]
 template=json.loads((ROOT/'output/altium/component-preparation/evidence/tps-pcb-request.json').read_text())
 for folder,c in CONFIG:
  d=ROOT/'ARTIX/ARTIX/libraries'/folder
  for ext in ['SchLib','PcbLib']:
   p=d/(c+'.'+ext); r=inspect(p); rows.append(r)
   if ext=='SchLib': dump(OUT/(c+'-scene-request.json'),readback_request(str(p),c))
   else:
    req=dict(template); req['body']=req['body'].replace(str(ROOT/'ARTIX/ARTIX/libraries/TPS563210A/TPS563210A.PcbLib'),str(p)); dump(OUT/(c+'-pcb-request.json'),req)
 dump(OUT/'inventory-saved.json',rows)
 for r in rows:
  print(r['path'])
  for k,v in r['records'].items():
   for rec in v:
    if rec.get('RECORD') in ['1','45','46','47','48']: print(k,rec)
def copies():
 rows=[]
 for folder,c in CONFIG:
  d=ROOT/'ARTIX/ARTIX/libraries'/folder
  (d/'original').mkdir(exist_ok=True); (d/'new').mkdir(exist_ok=True)
  for p in d.iterdir():
   if p.is_file():
    dst=d/'original'/p.name
    if dst.exists(): assert dst.read_bytes()==p.read_bytes()
    else: shutil.copy2(p,dst)
    if p.suffix.lower() in ['.schlib','.pcblib']:
     new=d/'new'/p.name
     if new.exists(): raise FileExistsError(new)
     shutil.copy2(p,new)
    rows.append({'source':str(p),'original':str(dst),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 dump(OUT/'original-hashes.json',rows)
def bundles():
 for folder,c in CONFIG[1:]:
  before=json.loads((OUT/(c+'-before.json')).read_text()); pins=before['result']['pins']; by={p['designator']:p for p in pins}
  if c.startswith('SPX'):
   groups=[('LDO 3.3V',[12,20,16],['1','3','2'],['5','4'])]
  else:
   groups=[('POWER',[20,18,20],['3','9','40','6','41','15','21','37'],['28','36','44','45','48','47','49']),('RGMII',[24,18,24],['22','23','24','25','26','27'],['19','13','14','16','17','18']),('MDIO / CTRL',[24,24,24],['30','31','29','38'],['20','33','34','35','32','12']),('XTAL',[18,18,18],['42','39'],['43','46']),('MDI',[18,18,18],['1','4','7','10'],['2','5','8','11'])]
  parts=[]
  for i,(f,w,l,r) in enumerate(groups,1):
   parts.append({'id':i,'function':f,'column_widths_mm':w,'pins':[{'designator':n,'name':by[n]['name'],'side':side} for side,ns in [('left',l),('right',r)] for n in ns]})
  manifest={'component':c,'source':'Existing exact native library; manufacturer datasheet crosscheck stored in report','electrical_policy':'power','parts':parts}
  dump(OUT/(c+'-manifest.json'),manifest)
  print(prepare('redraw',OUT/(c+'-manifest.json'),ROOT/'ARTIX/ARTIX/libraries'/folder/'new'/(c+'.SchLib'),OUT/c,before=OUT/(c+'-before.json')))
if __name__=='__main__': globals()[sys.argv[1]]()
