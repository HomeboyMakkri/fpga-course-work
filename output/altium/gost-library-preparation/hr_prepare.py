from prepare import *
from gost_symbol import coord,q
c='HR911130A'; folder=c
before=json.loads((OUT/(c+'-before.json')).read_text()); by={p['designator']:p for p in before['result']['pins']}
groups=[('RJ45 / MAGNETICS',[18,38,18],['2','3','4','7','5','6','8','9'],['1','10']),('LED / SHIELD',[18,38,18],['11','12','14','13'],['15','16'])]
parts=[]
for i,(f,w,l,r) in enumerate(groups,1): parts.append({'id':i,'function':f,'column_widths_mm':w,'pins':[{'designator':n,'name':by[n]['name'],'side':s} for s,ns in [('left',l),('right',r)] for n in ns]})
manifest={'component':c,'source':'HanRun REV B manufacturer schematic pages 1 and 3, preserved local PDF','electrical_policy':'power','parts':parts}
dump(OUT/(c+'-manifest.json'),manifest)
if not (OUT/c).exists(): prepare('redraw',OUT/(c+'-manifest.json'),ROOT/'ARTIX/ARTIX/libraries'/folder/'new'/(c+'.SchLib'),OUT/c,before=OUT/(c+'-before.json'))
# Connector-specific functional legends; pin names/numbers and maps stay unchanged.
legends={1:[('BI_DA+',8,-6),('BI_DA-',8,-12),('BI_DB+',8,-18),('BI_DB-',8,-24),('BI_DC+',8,-30),('BI_DC-',8,-36),('BI_DD+',8,-42),('BI_DD-',8,-48),('CT',66,-6),('TERM',66,-12),('4 x 1:1',37,-18),('MAGNETICS',37,-24),('RJ45',37,-36)],2:[('GREEN A',9,-6),('GREEN K',9,-12),('YELLOW A',9,-18),('YELLOW K',9,-24),('SHIELD',65,-6),('SHIELD',65,-12),('LED',37,-12)]}
code=[]; expected=[]
for part,labels in legends.items():
 for text,x,y in labels:
  code.append(f"T:=SchServer.SchObjectFactory(eLabel,eCreate_Default); T.OwnerPartId:={part}; T.OwnerPartDisplayMode:=0; T.Text:={q(text)}; T.Location:=Point({coord(x)},{coord(y)}); T.FontId:=F; T.Color:=0; T.Justification:=eJustify_Center; C.AddSchObject(T);")
  expected.append({'part':part,'text':text,'x':coord(x),'y':coord(y),'color':0,'font':'GOST Common','size':10})
req=json.loads((OUT/c/'mutation.json').read_text()); req['body']=req['body'].replace("finally SchServer.ProcessControl.PostProcess(L,'GOST symbol');",'\n'.join(code)+"\nfinally SchServer.ProcessControl.PostProcess(L,'GOST symbol');")
dump(OUT/c/'mutation.json',req); dump(OUT/c/'connector-legends.json',expected)
