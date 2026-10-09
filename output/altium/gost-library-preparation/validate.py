from prepare import *
from gost_symbol import verify
import re
def symbol_checks():
 allchecks={}
 for folder,c in CONFIG:
  bundle=OUT/(c+'-v2') if c.startswith('RTL') else OUT/c; p=bundle/'readback-result.json'; native=json.loads(p.read_text(encoding='utf-8-sig'))
  if c=='HR911130A':
   extra=json.loads((bundle/'connector-legends.json').read_text()); graphics=native['result']['graphics']; expected={(g['part'],g['text'],g['x'],g['y']) for g in extra}
   selected=[g for g in graphics if g['kind']=='label' and (g['part'],g['text'],g['x'],g['y']) in expected]
   assert len(selected)==len(extra) and all(g['color']==0 and g['font']=='GOST Common' and g['size']==10 for g in selected)
   native['result']['graphics']=[g for g in graphics if g not in selected]
   dump(bundle/'base-readback-result.json',native)
   v=verify(bundle,bundle/'base-readback-result.json'); v['connector_legends_verified']=True; v['complete_native_readback']=str(p); dump(bundle/'verification.json',v)
  else: v=verify(bundle,p)
  assert v['success'],v
  pins={p['designator'] for p in native['result']['pins']}; pcb=json.loads((OUT/(c+'-pcb.json')).read_text())['result']['footprints']
  assert len(pcb)==1
  pads={p['name'] for p in pcb[0]['pads']}
  pairs=re.findall(r'\(([^:]+):([^\)]+)\)',native['result']['models'][0]['map'])
  assert {a for a,b in pairs}==pins and all(b in pads for a,b in pairs)
  v['pin_pad_mapping_verified']=True;v['footprint']=pcb[0]['name'];v['unused_pads']=sorted(pads-{b for a,b in pairs})
  d=ROOT/'ARTIX/ARTIX/libraries'/folder
  v['pcblib_unchanged']=(d/'new'/(c+'.PcbLib')).read_bytes()==(d/'original'/(c+'.PcbLib')).read_bytes()
  assert v['pcblib_unchanged'];allchecks[c]=v
 for x in json.loads((OUT/'original-hashes.json').read_text()):
  assert hashlib.sha256(Path(x['source']).read_bytes()).hexdigest()==x['sha256']
  assert hashlib.sha256(Path(x['original']).read_bytes()).hexdigest()==x['sha256']
 dump(OUT/'symbol-validation.json',allchecks)
 print({c:v['success'] for c,v in allchecks.items()})
def previews():
 import render_native_previews as r
 r.EVIDENCE=OUT; r.PREVIEWS=OUT/'previews';r.PREVIEWS.mkdir(exist_ok=True);r.LINE_COLOR='black'
 checks=[]
 for folder,c in CONFIG:
  bundle=OUT/(c+'-v2') if c.startswith('RTL') else OUT/c
  native=json.loads((bundle/'readback-result.json').read_text(encoding='utf-8-sig'));dump(OUT/(c+'-after.json'),native)
  checks.append(r.render_component(c,ROOT/'ARTIX/ARTIX/libraries'/folder/'new'/(c+'.SchLib')))
 dump(OUT/'preview-validation.json',checks)
 print('Rendered',sum(len(c['parts']) for c in checks),'parts')
if __name__=='__main__': globals()[sys.argv[1]]()
