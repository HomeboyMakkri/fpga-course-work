from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
w='{'+ns['w']+'}'
out=Path('documents');out.mkdir(exist_ok=True)
theme='Разработка устройства формирования импульсных сигналов на ПЛИС и его конструкторской документации'
for f in Path('C:/Users/mkkr/Desktop').glob('*КР*docx'):
 task=f.name.startswith('Задание')
 changes={33:theme,42:'Проработать структуру и схемотехнические решения устройства на ПЛИС.',43:'Обосновать выбор элементной базы и разработать электрическую схему.',44:'Разработать проект печатной платы средствами выбранной САПР.',45:'Разработать и исследовать HDL-модель формирования импульсов и управления.',46:'Оценить проектные решения и оформить конструкторскую документацию.',47:'Ориентиры: внешняя опора 10 МГц; режимы 1, 10 и 100 импульсов в секунду.',48:'Состав каналов и параметры интерфейса уточняются в ходе проектирования.',49:'Проверка — моделированием и средствами САПР; изготовление не требуется.',54:'Схема, перечень элементов, материалы проекта платы и моделирования; выводы.',61:'Дата выдачи задания «___» ____________ 2026 г.'} if task else {22:theme,37:'Анализ исходных данных и выбор элементной базы',45:'Проработка структуры и электрической схемы устройства',53:'Разработка проекта печатной платы в выбранной САПР',61:'Разработка и исследование HDL-модели устройства',69:'Оценка проектных решений и оформление документации'}
 with ZipFile(f) as z:
  r=E.fromstring(z.read('word/document.xml')); ps=r.xpath('//w:body//w:p',namespaces=ns)
  for i,t in changes.items():
   p=ps[i]; ts=p.xpath('.//w:t',namespaces=ns)
   if ts:
    ts[0].text=t
    for q in ts[1:]:q.text=''
   else:
    run=E.SubElement(p,w+'r');E.SubElement(run,w+'t').text=t
  if task:
   for i in [55,56,57,58,59]:
    p=ps[i];parent=p.getparent()
    if parent.tag==w+'tc':
     row=parent.getparent();row.getparent().remove(row)
    else:parent.remove(p)
  target=out/('Задание_КР_ПЛИС.docx' if task else 'Календарный_план_КР_ПЛИС.docx')
  with ZipFile(target,'w') as zz:
   for entry in z.infolist(): zz.writestr(entry,E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True) if entry.filename=='word/document.xml' else z.read(entry))
  print(target)
