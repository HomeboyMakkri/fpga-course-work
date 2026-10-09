# ГОСТ-подготовка библиотек ARTIX — 9 октября 2026

**Состояние: три сохранённых символа проверены и подключены к ARTIX; модели разрешены из проекта.** Для HR911130A остаётся механическое ограничение исходного footprint; пригодность к изготовлению не подтверждена.

Адаптированы три существующих native SchLib. Все70 выводов имеют Power; исходно все были Passive. Номера, имена и identity pin-to-pad maps прошли финальное native save/reopen. Параметры сохранены, включая Description, который native checkpoint первоначально опустил; его восстановление нативно вернуло saved=true для всех трёх и затем проверено после повторного открытия. Все три модели повторно разрешены из контекста ARTIX в соответствующие рабочие PcbLib.

В процессе финального чтения Altium завершился с ошибкой0xc0000374 вntdll.dll. Причина не установлена. Пользователь открыл Altium обычным способом; health probe снял блокировку исполнителя. После этого все финальные readback и resolution прошли. Автоматический перезапуск и повтор записей не выполнялись. Журнал сохранён вaltium-crash-event.txt.

| Компонент | Части/выводы | Footprint |
|---|---:|---|
| HR911130A | 2/16 | HR911130A |
| SPX3819M5-L-3-3 | 1/5 | SOT95P280X145-5N |
| RTL8211E-VB-CG | 5/49 | QFN40P600X600X100-49N |

## Файлы и оригиналы

### HR911130A

- SchLib: [HR911130A.SchLib](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/ARTIX/ARTIX/libraries/HR911130A/new/HR911130A.SchLib)
- PcbLib: [HR911130A.PcbLib](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/ARTIX/ARTIX/libraries/HR911130A/new/HR911130A.PcbLib)
- Неизменённые копии исходников: `C:\Users\makarlistkov\Documents\Work\Engineering\FPGA-COURSE-WORK\ARTIX\ARTIX\libraries\HR911130A\original`. Исходные файлы также оставлены на прежних местах.

### SPX3819M5-L-3-3

- SchLib: [SPX3819M5-L-3-3.SchLib](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/ARTIX/ARTIX/libraries/LDO SPX3819M5-L-3-3/new/SPX3819M5-L-3-3.SchLib)
- PcbLib: [SPX3819M5-L-3-3.PcbLib](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/ARTIX/ARTIX/libraries/LDO SPX3819M5-L-3-3/new/SPX3819M5-L-3-3.PcbLib)
- Неизменённые копии исходников: `C:\Users\makarlistkov\Documents\Work\Engineering\FPGA-COURSE-WORK\ARTIX\ARTIX\libraries\LDO SPX3819M5-L-3-3\original`. Исходные файлы также оставлены на прежних местах.

### RTL8211E-VB-CG

- SchLib: [RTL8211E-VB-CG.SchLib](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/ARTIX/ARTIX/libraries/RTL8211E-VB-CG/new/RTL8211E-VB-CG.SchLib)
- PcbLib: [RTL8211E-VB-CG.PcbLib](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/ARTIX/ARTIX/libraries/RTL8211E-VB-CG/new/RTL8211E-VB-CG.PcbLib)
- Неизменённые копии исходников: `C:\Users\makarlistkov\Documents\Work\Engineering\FPGA-COURSE-WORK\ARTIX\ARTIX\libraries\RTL8211E-VB-CG\original`. Исходные файлы также оставлены на прежних местах.

## Оформление и проверки

Генератор навыка использован для рабочих копий. Чёрные линии и текст; GOST Common regular10pt; выводы5мм, электрическая сетка1мм, вспомогательная0.5мм, строки6мм. Поля расширены по длине названий. Старые контуры заменены. HR — функциональное двухчастное представление разъёма: пары магнитики/CT/TERM и LED/shield; числовые имена сохранены, их повторное отображение скрыто. RTL — POWER, RGMII, MDIO/CTRL, XTAL, MDI в одной микросхеме с одним footprint.

Native save/reopen и readback подтвердили части, выводы, Power, координаты, длины, шрифты, цвета, контуры, делители и надписи. Максимальная погрешность подключения к1мм сетке1.38e-6мм — менее одного внутреннего шага2.54e-6мм. Карты проверены по каждому выводу/площадке. PcbLib побайтно совпадают с оригиналами; native readback рабочих footprint совпадает по всем проверенным площадкам. Смешанных библиотек среди источников нет: по одному символу и footprint. Параметры сохранены по именам и значениям, шрифты regular подтверждены сохранённой таблицей.

Перед подключением создана disk backup и native live checkpoint ARTIX. Добавлено6 относительных путей; существующие saved/live ссылки сохранены, дубликатов нет. IntegratedLibraryManager.MakeCurrentProject(ARTIX) и GetComponentDatafileLocation вернули exact `new/*.PcbLib` для всех трёх символов. Никаких глобальных установок библиотек.

Проверки и первичные native ответы: [validation.json](validation.json), [исходные типы и карта](pin-types-and-map.csv), [источники и SHA256](sources.json), [native resolution](model-resolution-result.json).

## Ограничения

- Historical Altium crash (Windows Application event1000, 11:55:34 Moscow, ntdll.dll exception0xc0000374) recovered after user opened Altium normally. Cause unknown. Final native reopening of all3 saved libraries and all3 ARTIX model resolutions then passed; no active CAD blocker remains.
- HR911130A source footprint differs from HanRun REV B recommended drilling: signal holes 0.99 vs 0.89 mm; NPTH mounting holes 3.25 vs 3.5 mm; shield-hole spacing 16.10 vs 15.49 mm. Original geometry deliberately preserved. Mechanical fit not approved.
- HR911130A pads17/18 are unplated mounting holes, not electrical pins; pads15/16 are plated shield contacts. All16 electrical pins have identity maps.
- SPX3819 pin4 name ADJ/BYP preserved from source; in fixed3.3V variant its function is BYP, not adjustable feedback.
- RTL8211E pin13 source name RXCTL/PHY_AD preserved; manufacturer function includes PHY_AD2. EP49 is GND. Supply suffixes distinguish repeated physical pins.
- No STEP/3D models exist in the three supplied PcbLib model stores (embedded/external counts0). No models were invented.
- Previews reconstruct saved native graphics and readback pins; they are not Altium screenshots. Exact UI text offsets may differ.
- Existing schematic sheets were not rebuilt or updated. Placed pin-net connectivity and ERC have not been tested by this library task. All-Power type is the requested ERC override.
- ActiveBOM.VirtualBOM exists in live project references as a generated virtual document; native project save does not add it as a source document. Its live reference was retained.
- RTL manufacturer PDF origin is the existing checkout; acquisition URL is unavailable.

## Предпросмотры

Изображения ниже — реконструкция сохранённой native геометрии, не скриншоты Altium.

![HR911130A-part-01](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/HR911130A-part-01.png)

![HR911130A-part-02](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/HR911130A-part-02.png)

![SPX3819M5-L-3-3-part-01](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/SPX3819M5-L-3-3-part-01.png)

![RTL8211E-VB-CG-part-01](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/RTL8211E-VB-CG-part-01.png)

![RTL8211E-VB-CG-part-02](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/RTL8211E-VB-CG-part-02.png)

![RTL8211E-VB-CG-part-03](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/RTL8211E-VB-CG-part-03.png)

![RTL8211E-VB-CG-part-04](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/RTL8211E-VB-CG-part-04.png)

![RTL8211E-VB-CG-part-05](C:/Users/makarlistkov/Documents/Work/Engineering/FPGA-COURSE-WORK/output/altium/gost-library-preparation/previews/RTL8211E-VB-CG-part-05.png)