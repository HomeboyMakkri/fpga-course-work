from html import escape
from pathlib import Path

W, H = 3700, 2260
ink = '#111111'
blue = '#0755a4'
red = '#bb2525'
muted = '#555555'
parts = []

def add(s): parts.append(s)
def line(x1,y1,x2,y2,color=ink,width=4):
    add(f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>')
def path(d,color=ink,width=4):
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')
def rect(x,y,w,h,stroke=ink,fill='white',sw=3,rx=0):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def circle(x,y,r=7,fill=ink,stroke='none',sw=1):
    add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def txt(x,y,s,size=29,color=ink,weight='normal',anchor='start'):
    add(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, DejaVu Sans, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>')
def ground(x,y):
    line(x,y,x,y+17)
    line(x-17,y+17,x+17,y+17)
    line(x-12,y+25,x+12,y+25)
    line(x-6,y+33,x+6,y+33)
    txt(x+26,y+30,'GND',23,blue)
def pwr(x,y):
    line(x,y,x,y-31,red)
    path(f'M{x-13} {y-31} L{x} {y-48} L{x+13} {y-31}',red,4)
    txt(x+22,y-31,'+3V3',26,red,'bold')
def res_h(x1,x2,y,des,val,sub=None):
    mid=(x1+x2)/2; boxw=75
    line(x1,y,mid-boxw/2,y); rect(mid-boxw/2,y-16,boxw,32,ink,'white',4)
    line(mid+boxw/2,y,x2,y)
    txt(mid,y-53,des,28,ink,'bold','middle')
    txt(mid,y+69,val,27,ink,'normal','middle')
    if sub: txt(mid,y+107,sub,24,muted,'normal','middle')
def res_v(x,y1,y2,des,val,label_x=None):
    mid=(y1+y2)/2; bx=label_x if label_x is not None else x+32
    line(x,y1,x,mid-34); rect(x-16,mid-34,32,68,ink,'white',4); line(x,mid+34,x,y2)
    txt(bx,mid-6,des,24,ink,'bold')
    txt(bx,mid+28,val,23)
def cap_h(x1,x2,y,des,val,sub=None):
    mid=(x1+x2)/2
    line(x1,y,mid-12,y); line(mid-12,y-31,mid-12,y+31)
    line(mid+12,y-31,mid+12,y+31); line(mid+12,y,x2,y)
    txt(mid,y-60,des,28,ink,'bold','middle'); txt(mid,y+75,val,26,ink,'normal','middle')
    if sub: txt(mid,y+113,sub,24,muted,'normal','middle')
def cap_v(x,y1,y2,des,val,label_x=None):
    mid=(y1+y2)/2; bx=label_x if label_x is not None else x+32
    line(x,y1,x,mid-13); line(x-29,mid-13,x+29,mid-13)
    line(x-29,mid+13,x+29,mid+13); line(x,mid+13,x,y2)
    txt(bx,mid-10,des,24,ink,'bold'); txt(bx,mid+27,val,23)
def tp(x,y,name,up=True):
    stem=-82 if up else 82
    circle(x,y,7)
    line(x,y,x,y+stem)
    circle(x,y+stem,13,'white',ink,4)
    txt(x+24,y+stem+9,name,27,ink,'bold')
def block(x,w,n,title):
    rect(x,180,w,1350,'#9b9b9b','none',2,12)
    rect(x,180,w,76,ink,'#f0f0f0',2,12)
    txt(x+24,232,f'{n}. {title}',32,ink,'bold')

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
rect(0,0,W,H,'white','white',0)
txt(60,82,'Схема электрическая принципиальная — прототип формирователя 1/10/100 PPS',43,ink,'bold')
txt(60,128,'Опора 10 МГц · два независимо выбираемых выхода · Tang Nano 20K',30,muted)
block(50,560,1,'Источник сигнала')
block(630,740,2,'Вход и согласование')
block(1390,1040,3,'Компаратор и опора')
block(2450,610,4,'Отладочная плата')
block(3080,570,5,'Выходы')

# 1. External generator, supply, and coaxial cable.
rect(125,495,310,280,ink,'white',4)
txt(152,545,'XG1',34,ink,'bold')
txt(152,589,'Генератор ГК199-ТС',25)
txt(152,639,'Выход SIN',28)
txt(152,682,'Частота 10 МГц',25)
txt(152,720,'Амплитуда > 300 мВ',25)
txt(152,757,'Нагрузка 50 Ом ±5%',25)
line(300,775,300,955); circle(300,775,7)
txt(158,895,'+5 / +12 В',23,red)
line(435,620,694,620)
circle(435,620,6)
txt(448,460,'Центральная жила коаксиала',23,muted)
line(435,760,695,760)
circle(435,760,6)
line(550,760,550,777); line(533,777,567,777); line(538,785,562,785); line(544,793,556,793)
txt(460,840,'Экран → GND',23,muted)
rect(125,955,420,172,ink,'white',4)
txt(151,1003,'PS1 · источник питания',29,ink,'bold')
txt(151,1052,'Питание генератора:',27)
txt(151,1090,'5 В или 12 В;',24)
txt(151,1120,'проверить исполнение',24)
line(420,955,420,870); ground(420,870)

# 2. Input connector, termination, coupling, series resistance.
rect(694,584,82,220,ink,'white',3)
txt(735,557,'J1',29,ink,'bold','middle')
circle(694,620,7,'white',ink,3); circle(694,760,7,'white',ink,3)
txt(790,600,'J1.1',25)
txt(790,735,'J1.2',25)
line(776,620,980,620)
line(776,760,835,760)
line(835,760,835,777); line(818,777,852,777); line(823,785,847,785); line(829,793,841,793)
txt(790,838,'GND',23,blue)
txt(809,540,'RF_IN',30,blue,'bold')
tp(946,620,'TP1')
circle(885,620,7)
res_v(885,620,945,'R1','49,9 Ом · 1%',914)
ground(885,945)
txt(695,1065,'R1 — входная терминация 50 Ом',25,muted)
cap_h(980,1125,620,'C1','100 нФ','Керамика; AC-развязка')
res_h(1125,1305,620,'R2','1 кОм')
line(1305,620,1435,620)
txt(1310,559,'VIN_BIAS',29,blue,'bold')

# 3. VIN_BIAS injection, divider, comparator and decoupling.
line(1435,620,1705,620); circle(1485,620,7)
res_v(1485,620,1045,'R3','10 кОм',1510)
line(1705,620,1705,590); line(1705,590,1820,590)
line(1485,1045,1790,1045); circle(1485,1045,7); circle(1595,1045,7); circle(1720,1045,7)
txt(1815,1105,'VREF ≈ 1,65 В',28,blue,'bold')
line(1760,1045,1760,952); circle(1760,952,13,'white',ink,4); circle(1760,1045,7)
txt(1815,962,'TP2',25,ink,'bold')
res_v(1595,820,1045,'R4','10 кОм',1618); pwr(1595,820)
res_v(1595,1045,1280,'R5','10 кОм',1618); ground(1595,1280)
cap_v(1720,1045,1280,'C2','1 мкФ',1749); ground(1720,1280)
line(1790,1045,1790,710); line(1790,710,1820,710)

# Comparator triangle and explicit pin numbers.
path('M1820 505 L1820 795 L2095 650 Z',ink,4)
txt(1872,616,'U1',34,ink,'bold')
txt(1853,656,'TLV3511DBVR',27)
txt(1860,692,'SOT-23-5',25)
txt(1832,578,'3 IN+',25)
txt(1832,744,'4 IN−',25)
line(1930,505,1930,447); pwr(1930,447)
txt(1950,486,'5 V+',25)
line(1930,795,1930,856); ground(1930,856)
txt(1950,825,'2 V−',25)
txt(2098,612,'1 OUT',23)
line(2095,650,2160,650)
res_h(2160,2270,650,'R6','33 Ом')
line(2270,650,2490,650)
txt(2270,598,'REF_CLK',27,blue,'bold')
tp(2355,650,'TP3',False)
txt(2020,907,'Выход push-pull · питание 3,3 В',25,muted)

# Independent local supply capacitors; all rail flags have the same net name.
cap_v(2140,990,1150,'C3','100 нФ',2168); pwr(2140,990); ground(2140,1150)
cap_v(2300,990,1150,'C4','1 мкФ',2328); pwr(2300,990); ground(2300,1150)
txt(2020,1288,'C3 разместить непосредственно',23,muted)
txt(2020,1324,'около выводов 5 и 2 U1.',23,muted)

# 4. Complete Tang Nano 20K board as a single functional module.
rect(2490,328,530,1015,ink,'white',4)
txt(2524,387,'U2 · Tang Nano 20K',34,ink,'bold')
line(2508,415,3003,415,ink,2)
line(2450,468,2490,468,red)
line(2450,468,2450,433,red); path('M2437 433 L2450 416 L2463 433',red,4)
txt(2514,480,'+3V3 — выход питания',26,red,'bold')
line(2450,555,2490,555)
line(2450,555,2450,572); line(2433,572,2467,572); line(2438,580,2462,580); line(2444,588,2456,588)
txt(2514,565,'GND — общий провод',26,blue)
txt(2514,657,'GPIO_CLK — вход',27,blue,'bold')
circle(2490,650,7)
rect(2535,718,440,115,ink,'#f6f6f6',2)
txt(2558,762,'USB-C',29,ink,'bold')
txt(2558,804,'Питание и программирование',26)
line(3020,900,3100,900)
txt(2514,909,'GPIO_PPS1 — выход',27,blue,'bold')
line(3020,1100,3100,1100)
txt(2514,1109,'GPIO_PPS2 — выход',27,blue,'bold')
txt(2514,1191,'KEY1: 1 → 10 → 100 → 1 PPS',25)
txt(2514,1231,'KEY2: 1 → 10 → 100 → 1 PPS',25)
txt(2514,1273,'Выбор каналов независим',25,muted)
txt(2480,1392,'Точные номера GPIO назначить по pinout',24,muted)
txt(2480,1428,'конкретной ревизии платы.',24,muted)

# 5. Two series-damped output channels and grounded coax shields.
res_h(3100,3290,900,'R7','33 Ом')
line(3290,900,3475,900)
txt(3295,845,'PPS_CH1',27,blue,'bold')
line(3440,900,3440,775); circle(3440,775,13,'white',ink,4)
circle(3440,900,7)
txt(3465,767,'TP4',25,ink,'bold')
rect(3475,866,96,114,ink,'white',3)
circle(3475,900,7,'white',ink,3)
txt(3515,846,'J2',29,ink,'bold')
txt(3508,921,'центр',23)
line(3475,955,3420,955)
line(3420,955,3420,972); line(3403,972,3437,972); line(3408,980,3432,980); line(3414,988,3426,988)
txt(3345,1005,'GND',23,blue)
txt(3508,970,'экран',23)
res_h(3100,3290,1100,'R8','33 Ом')
line(3290,1100,3475,1100)
txt(3295,1045,'PPS_CH2',27,blue,'bold')
line(3330,1100,3330,1260); circle(3330,1260,13,'white',ink,4)
circle(3330,1100,7)
txt(3355,1270,'TP5',25,ink,'bold')
rect(3475,1066,96,114,ink,'white',3)
circle(3475,1100,7,'white',ink,3)
txt(3515,1046,'J3',29,ink,'bold')
txt(3508,1121,'центр',23)
line(3475,1155,3420,1155)
line(3420,1155,3420,1172); line(3403,1172,3437,1172); line(3408,1180,3432,1180); line(3414,1188,3426,1188)
txt(3345,1205,'GND',23,blue)
txt(3508,1170,'экран',23)
txt(3110,1350,'Осциллограф: вход 1 МОм,',25)
txt(3110,1390,'связь по постоянному току.',25)
txt(3110,1430,'Режим 50 Ом выключить.',25,ink,'bold')

# Notes and simple title block.
rect(50,1565,3600,540,ink,'white',3)
rect(50,1565,3600,62,ink,'#f0f0f0',2)
txt(76,1607,'Примечания и контроль',31,ink,'bold')
notes=[
  '1. Земли генератора, Tang Nano, компаратора, разъёмов и осциллографа объединены.',
  '2. R1 является нагрузкой 50 Ом для генератора.',
  '3. R6, R7 и R8 — последовательные демпфирующие резисторы, не нагрузки 50 Ом.',
  '4. Не подавать синус 10 МГц непосредственно на GPIO FPGA.',
  '5. Проверка: TP2 ≈ 1,65 В; TP1 — синусоида 10 МГц; TP3 — прямоугольный сигнал 10 МГц;',
  '    TP4 и TP5 — выбранные сигналы PPS.'
]
for i,s in enumerate(notes): txt(85,1685+i*65,s,29)
txt(60,2166,'Прототип на готовой отладочной плате · электрические связи показаны условно по именованным цепям',26,muted)
txt(3635,2166,'Лист 1 / 1',25,muted,anchor='end')
add('</svg>')

out = Path(__file__).with_name('tang_nano_20k_pps_schematic.svg')
out.write_text('\n'.join(parts), encoding='utf-8')
print(out)
