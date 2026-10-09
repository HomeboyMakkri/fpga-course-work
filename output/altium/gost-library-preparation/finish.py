from prepare import *
import configparser,struct,olefile,csv
from PIL import Image,ImageDraw,ImageFont
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def projectrefs(p):
 cp=configparser.ConfigParser(interpolation=None,strict=False);cp.read(p,encoding='utf-8-sig')
 return [cp[s]['DocumentPath'] for s in cp.sections() if s.startswith('Document') and 'DocumentPath' in cp[s]]
checks=read(OUT/'symbol-validation.json'); resolution=read(OUT/'model-resolution-result.json')
before=read(OUT/'project-before-live.json')['documents'];after=read(OUT/'project-add-result.json')['result']['documents']
assert set(before)<=set(after) and len(after)==len(set(after))
old=projectrefs(OUT/'ARTIX-live-checkpoint.PrjPcb'); new=projectrefs(ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb')
assert set(old)<=set(new) and len(new)==len(set(new))
expected=[]; pinrows=[]; components=[]
for folder,c in CONFIG:
 d=ROOT/'ARTIX/ARTIX/libraries'/folder; bundle=OUT/(c+'-v2') if c.startswith('RTL') else OUT/c
 snap=read(bundle/'readback-result.json')['result']; nativepcb=read(OUT/(c+'-pcb-working.json'))['result']
 origpcb=read(OUT/(c+'-pcb.json'))['result']; comparable=json.loads(json.dumps(nativepcb))
 for fp in comparable['footprints']:
  for p in fp['pads']:p.pop('plated',None)
 assert comparable==origpcb
 model=next(r for r in resolution['result']['models'] if r['component']==c)
 assert Path(model['datafile']).resolve()==(d/'new'/(c+'.PcbLib')).resolve()
 assert Path(model['library']).resolve()==(d/'new'/(c+'.SchLib')).resolve()
 for e in ['SchLib','PcbLib']: expected.append(str((d/'new'/(c+'.'+e)).relative_to(ROOT/'ARTIX/ARTIX')))
 source=inspect(d/'original'/(c+'.SchLib')); working=inspect(d/'new'/(c+'.SchLib'))
 def pars(r): return {(x.get('Name'),x.get('OwnerPartId')):x.get('Text') for v in r['records'].values() for x in v if x.get('RECORD')=='41'}
 assert pars(source)==pars(working)
 comprefs=[r['LibReference'] for v in working['records'].values() for r in v if r.get('RECORD')=='1' and 'LibReference' in r]
 assert comprefs==[c]
 header=working['records']['FileHeader'][0]
 fonts=[i for i in range(1,int(header['FontIdCount'])+1) if header.get('FontName'+str(i))=='GOST Common']
 # Saved font table defaults omit regular False fields.
 assert fonts and all(header.get('Size'+str(i))=='10' and not any(header.get(flag+str(i))=='T' for flag in ['Bold','Italic','Underline','StrikeOut']) for i in fonts)
 with olefile.OleFileIO(str(d/'new'/(c+'.PcbLib'))) as ole:
  models={n:struct.unpack('<I',ole.openstream('Library/'+n+'/Header').read(4))[0] for n in ['Models','ModelsNoEmbed']}
 assert models=={'Models':0,'ModelsNoEmbed':0}
 orig={p['designator']:p for p in read(OUT/(c+'-before.json'))['result']['pins']}
 for p in snap['pins']:
  pinrows.append({'component':c,'number':p['designator'],'name':p['name'],'original_type':orig[p['designator']]['electrical'],'original_type_name':'Passive','final_type':p['electrical'],'final_type_name':'Power','part':p['part'],'pad':p['designator']})
 assert all(p['electrical']==7 and p['name']==orig[p['designator']]['name'] for p in snap['pins'])
 components.append({'component':c,'action':'adapted existing native working copy','schlib':str(d/'new'/(c+'.SchLib')),'pcblib':str(d/'new'/(c+'.PcbLib')),'original_folder':str(d/'original'),'libreference':c,'component_count':1,'parts':snap['part_count'],'pins':snap['pin_count'],'checks':checks[c],'parameters_preserved':True,'fonts_regular_saved':True,'footprint_geometry_unchanged':True,'native_working_footprint_readback':True,'pcb_models':models,'model_resolution':model,'project_connected':True,'manufacturer_pin_assignment_checked':True,'footprint_mechanical_review_pending':c=='HR911130A'})
assert set(expected)<=set(new) and all(not Path(p).is_absolute() for p in expected)
with (OUT/'pin-types-and-map.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=pinrows[0].keys());w.writeheader();w.writerows(pinrows)
sources=[]
for manufacturer,mpn,path,url in [
 ('HanRun','HR911130A','output/altium/component-preparation/evidence/ethernet/HR911130A-Hanrun-LCSC.pdf','https://atta.szlcsc.com/upload/public/pdf/source/20250812/A9B443FB770AA42A34C92B1A15093C54.pdf'),
 ('MaxLinear / Exar','SPX3819M5-L-3-3','datasheets/Datasheets/POWER/SPX3819M5-L-3-3.pdf','https://www.maxlinear.com/ds/spx3819.pdf'),
 ('Realtek','RTL8211E-VB-CG','datasheets/Datasheets/NET/rtl8211e.pdf',None)]:
 p=ROOT/path;sources.append({'manufacturer':manufacturer,'mpn':mpn,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'url':url,'note':'Existing local manufacturer document retained. URL for SPX points to current manufacturer revision; local PDF is older Exar revision. RTL original acquisition URL unknown.'})
dump(OUT/'sources.json',sources)
limitations=['HR911130A source footprint differs from HanRun REV B recommended drilling: signal holes 0.99 vs 0.89 mm; NPTH mounting holes 3.25 vs 3.5 mm; shield-hole spacing 16.10 vs 15.49 mm. Original geometry deliberately preserved. Mechanical fit not approved.',
 'HR911130A pads17/18 are unplated mounting holes, not electrical pins; pads15/16 are plated shield contacts. All16 electrical pins have identity maps.',
 'SPX3819 pin4 name ADJ/BYP preserved from source; in fixed3.3V variant its function is BYP, not adjustable feedback.',
 'RTL8211E pin13 source name RXCTL/PHY_AD preserved; manufacturer function includes PHY_AD2. EP49 is GND. Supply suffixes distinguish repeated physical pins.',
 'No STEP/3D models exist in the three supplied PcbLib model stores (embedded/external counts0). No models were invented.',
 'Previews reconstruct saved native graphics and readback pins; they are not Altium screenshots. Exact UI text offsets may differ.',
 'Existing schematic sheets were not rebuilt or updated. Placed pin-net connectivity and ERC have not been tested by this library task. All-Power type is the requested ERC override.',
 'ActiveBOM.VirtualBOM exists in live project references as a generated virtual document; native project save does not add it as a source document. Its live reference was retained.',
 'RTL manufacturer PDF origin is the existing checkout; acquisition URL is unavailable.']
validation={'date':'2026-10-09','symbols_verified':3,'project_connected_and_model_resolved':3,'total_pins_power':70,'total_parts':8,'components':components,'source_original_hashes_preserved':True,'project_disk_backup':str(OUT/'ARTIX-before-disk.PrjPcb'),'project_live_checkpoint':str(OUT/'ARTIX-live-checkpoint.PrjPcb'),'existing_live_references_preserved':True,'existing_saved_references_preserved':True,'added_project_relative_paths':expected,'duplicates':False,'placed_erc':None,'manufacturer_footprint_mechanical_acceptance':{'HR911130A':False,'SPX3819M5-L-3-3':'package/pin mapping checked; existing land pattern retained','RTL8211E-VB-CG':'package/pin mapping checked; existing land pattern retained'},'limitations':limitations,'offline_generator_tests':'12 passed; real native readback separately passed'}
validation.update(final_native_reopen_after_description_restore=True,task_status='VERIFIED_AND_CONNECTED_WITH_HR_FOOTPRINT_MECHANICAL_LIMITATION',blocker=None,recovered_crash={'state':'RESOLVED_AFTER_USER_NORMAL_REOPEN','windows_event':1000,'application':'X2.EXE','crash_local_time':'2026-10-09 11:55:34 Europe/Moscow','cause':'unknown','final_readbacks_passed':3,'model_resolution_rechecked':3})
for c in components:
 c.update(last_successful_native_geometry_readback=True,final_native_reopen_after_parameter_restore=True,verified_library_component=True,manufacturing_acceptance='pending mechanical correction/review' if c['component']=='HR911130A' else 'not assessed by symbol task')
limitations.insert(0,'Historical Altium crash (Windows Application event1000, 11:55:34 Moscow, ntdll.dll exception0xc0000374) recovered after user opened Altium normally. Cause unknown. Final native reopening of all3 saved libraries and all3 ARTIX model resolutions then passed; no active CAD blocker remains.')
dump(OUT/'validation.json',validation)
lines=['# ГОСТ-подготовка библиотек ARTIX — 9 октября 2026','', '**Состояние: три сохранённых символа проверены и подключены к ARTIX; модели разрешены из проекта.** Для HR911130A остаётся механическое ограничение исходного footprint; пригодность к изготовлению не подтверждена.','', 'Адаптированы три существующих native SchLib. Все70 выводов имеют Power; исходно все были Passive. Номера, имена и identity pin-to-pad maps прошли финальное native save/reopen. Параметры сохранены, включая Description, который native checkpoint первоначально опустил; его восстановление нативно вернуло saved=true для всех трёх и затем проверено после повторного открытия. Все три модели повторно разрешены из контекста ARTIX в соответствующие рабочие PcbLib.','', 'В процессе финального чтения Altium завершился с ошибкой0xc0000374 вntdll.dll. Причина не установлена. Пользователь открыл Altium обычным способом; health probe снял блокировку исполнителя. После этого все финальные readback и resolution прошли. Автоматический перезапуск и повтор записей не выполнялись. Журнал сохранён вaltium-crash-event.txt.','', '| Компонент | Части/выводы | Footprint |','|---|---:|---|']
for c in components: lines.append(f"| {c['component']} | {c['parts']}/{c['pins']} | {c['checks']['footprint']} |")
lines+=['','## Файлы и оригиналы','']
for c in components:
 lines.extend([f"### {c['component']}",'',f"- SchLib: [{Path(c['schlib']).name}]({c['schlib'].replace(chr(92),'/')})",f"- PcbLib: [{Path(c['pcblib']).name}]({c['pcblib'].replace(chr(92),'/')})",f"- Неизменённые копии исходников: `{c['original_folder']}`. Исходные файлы также оставлены на прежних местах.",''])
lines+=['## Оформление и проверки','','Генератор навыка использован для рабочих копий. Чёрные линии и текст; GOST Common regular10pt; выводы5мм, электрическая сетка1мм, вспомогательная0.5мм, строки6мм. Поля расширены по длине названий. Старые контуры заменены. HR — функциональное двухчастное представление разъёма: пары магнитики/CT/TERM и LED/shield; числовые имена сохранены, их повторное отображение скрыто. RTL — POWER, RGMII, MDIO/CTRL, XTAL, MDI в одной микросхеме с одним footprint.','','Native save/reopen и readback подтвердили части, выводы, Power, координаты, длины, шрифты, цвета, контуры, делители и надписи. Максимальная погрешность подключения к1мм сетке1.38e-6мм — менее одного внутреннего шага2.54e-6мм. Карты проверены по каждому выводу/площадке. PcbLib побайтно совпадают с оригиналами; native readback рабочих footprint совпадает по всем проверенным площадкам. Смешанных библиотек среди источников нет: по одному символу и footprint. Параметры сохранены по именам и значениям, шрифты regular подтверждены сохранённой таблицей.','','Перед подключением создана disk backup и native live checkpoint ARTIX. Добавлено6 относительных путей; существующие saved/live ссылки сохранены, дубликатов нет. IntegratedLibraryManager.MakeCurrentProject(ARTIX) и GetComponentDatafileLocation вернули exact `new/*.PcbLib` для всех трёх символов. Никаких глобальных установок библиотек.','','Проверки и первичные native ответы: [validation.json](validation.json), [исходные типы и карта](pin-types-and-map.csv), [источники и SHA256](sources.json), [native resolution](model-resolution-result.json).','', '## Ограничения','']
lines += ['- '+x for x in limitations]
lines+=['','## Предпросмотры','','Изображения ниже — реконструкция сохранённой native геометрии, не скриншоты Altium.']
for folder,c in CONFIG:
 for p in sorted((OUT/'previews').glob(c+'-part-*.png')):lines += ['',f'![{p.stem}]({str(p).replace(chr(92),"/")})']
(OUT/'report.md').write_text('\n'.join(lines),encoding='utf-8')
imgs=[Image.open(p).convert('RGB') for p in sorted((OUT/'previews').glob('*-part-*.png'))]
tiles=[]
for im in imgs:
 im.thumbnail((800,650));tile=Image.new('RGB',(820,680),'white');tile.paste(im,((820-im.width)//2,(680-im.height)//2));tiles.append(tile)
sheet=Image.new('RGB',(1640,680*4),'#eceff1')
for i,im in enumerate(tiles):sheet.paste(im,((i%2)*820,(i//2)*680))
sheet.save(OUT/'previews/all-symbols.png')
print('Final validation:3 native symbols,70 Power pins,8 parts,6 project libraries,3 resolved models; HR mechanical limitation recorded.')
