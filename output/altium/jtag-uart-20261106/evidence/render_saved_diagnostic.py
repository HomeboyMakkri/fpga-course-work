from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
OUT=Path(__file__).resolve().parent
D=json.loads((OUT.parent/'main-saved-records.json').read_text(encoding='utf-8'))
R=D['records']['FileHeader']
S=6
W,H=3600,2520
im=Image.new('RGB',(W,H),'white');dr=ImageDraw.Draw(im)
fontpath='C:/Windows/Fonts/arial.ttf'
f=ImageFont.truetype(fontpath,20);small=ImageFont.truetype(fontpath,16)
def v(r,k):return (float(r.get(k,0))+float(r.get(k+'_Frac',0))/100000)*.254
def xy(x,y):return (x*S,H-y*S)
def pos(r):return xy(v(r,'Location.X'),v(r,'Location.Y'))
def line(a,b,fill='black',width=2):dr.line([a,b],fill=fill,width=width)
def text(p,s,fill='black',font=f,anchor='ls'):dr.text(p,str(s),fill=fill,font=font,anchor=anchor)
for r in R:
 t=r.get('RECORD')
 if t in ['6','27']:
  ps=[xy(v(r,'X'+str(i)),v(r,'Y'+str(i))) for i in range(1,int(r.get('LocationCount',0))+1)]
  if len(ps)>1:dr.line(ps,fill='#850000' if t=='27' else 'black',width=2)
 if t=='29':
  x,y=pos(r);dr.ellipse([x-3,y-3,x+3,y+3],fill='#850000')
 if t=='22':
  x,y=pos(r);line((x-5,y-5),(x+5,y+5),'#cc0000');line((x-5,y+5),(x+5,y-5),'#cc0000')
 if t=='18':
  x,y=pos(r);w=v(r,'Width')*S;h=14
  dr.line([(x,y-h),(x+w-10,y-h),(x+w,y),(x+w-10,y+h),(x,y+h),(x,y-h)],fill='black',width=2);text((x+5,y+6),r.get('Name',''),font=small)
 if t=='17':
  x,y=pos(r);line((x,y),(x,y-20),'#850000');line((x-12,y-20),(x+12,y-20),'#850000');text((x-14,y-26),r.get('Text',''),font=small)
for r in R:
 t=r.get('RECORD')
 if t in ['4','25','34','41'] and r.get('IsHidden')!='T' and r.get('Text') and ('Location.X' in r):
  text(pos(r),r['Text'],fill='#850000' if t=='25' else 'black')
 if t=='2':
  x,y=pos(r);n=int(r.get('PinConglomerate',24));ori=n&3;ln=v(r,'PinLength')*S
  dx,dy=[(1,0),(0,-1),(-1,0),(0,1)][ori];tip=(x+dx*ln,y+dy*ln)
  line((x,y),tip,'#000000')
  name=r.get('Name','');number=r.get('Designator','')
  if ori==0:text((x-7,y+6),name,font=small,anchor='rs');text((x+ln/2,y-4),number,font=small,anchor='ms')
  elif ori==2:text((x+7,y+6),name,font=small);text((x-ln/2,y-4),number,font=small,anchor='ms')
  else:text((x+5,y-4),number,font=small)
dr.rectangle([2,2,W-3,H-3],outline='#777777',width=2)
im.save(OUT/'07-saved-geometry-before-repair.png')
print(OUT/'07-saved-geometry-before-repair.png')
