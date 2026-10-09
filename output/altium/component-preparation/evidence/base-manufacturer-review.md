# Проверка базовых компонентов по документации производителей

Дата проверки: 2026-10-08. Эта ветка выполняла исследование и сохраняла источники; записи в Altium и изменения рабочих библиотек не выполнялись. Фактическое сохранение, сетку символов, модельные ссылки и ERC проверяет основной исполнитель.

## FPGA и карта выводов

Существующий LibReference `XC7A50T-2FGG484I` проверен по текущему официальному архиву [AMD Artix-7 pinout files](https://www.amd.com/en/developer/resources/adaptive-socs-and-fpgas/package-pinout-files/artix-7-package-device-pinout-files.html). Сохранены `manufacturer/a7all.zip`, `xc7a50tfgg484pkg.csv`, `xc7a50tfgg484pkg.txt`. Внутренняя дата карты производителя: 2013-10-04; архив получен с официального сайта в текущей проверке.

Сопоставление с `fpga-native-before.json`: 484 вывода, 484 уникальных обозначения шаров, нет пропущенных и лишних. 291 имя совпадает точно; 193 отличаются только нумерованными алиасами GND/NC/питания и `PROGRAM_B_0` → `PROGRAM_B`. Функциональные имена I/O не нормализовались. Необъяснённых расхождений нет. Машинный результат: `fpga-manufacturer-pin-crosscheck.json`.

Это подтверждает физическую идентичность выводов существующей модели. Это **не выбор** speed grade/температурного исполнения для закупки. В задании указан только `XC7A50T-FGG484`; использовать существующую точную модель допустимо с явной записью её идентичности, а окончательный заказной код остаётся неизвестным.

Обнаруженный дефект исходного символа: все 484 вывода имеют `Electrical=4`, то есть Passive. По [Altium Schematic API Types / TPinElectrical](https://www.altium.com/documentation/altium-dxp-developer/schematic-api-types-reference?version=3.2) порядок: 0 Input, 1 IO, 2 Output, 3 OpenCollector, 4 Passive, 5 HiZ, 6 OpenEmitter, 7 Power. Сохранение этих типов при перерисовке подтверждает отсутствие регрессии, но не делает электрическую классификацию верной. Исправление типов должно быть отдельной документированной операцией по исходным функциям.

Локальная UG475 v1.8/2012, рис.4-8, стр.230: FGG484 имеет корпус 23×23 мм, полную матрицу 22×22, шаг 1 мм, шар 0.60 мм номинально (0.50–0.70), высоту 2.20 мм номинально (2.00–2.60). Это геометрия корпуса, а не готовые размеры площадок PCB. Изображение сохранено как `manufacturer/UG475-v1.8-FGG484-page230.png`. Текущая официальная [UG475 v1.20](https://docs.amd.com/v/u/en-US/ug475_7Series_Pkg_Pinout) найдена; прямое web-чтение PDF не удалось. Pin-to-pad mapping и геометрию footprint нужно проверить нативно.

## Обязательные питания и последовательность

Актуальная [AMD DS181 v1.27.1](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet) сохранена как `manufacturer/DS181-v1.27.1.pdf`. Для обычного -2: VCCINT=VCCBRAM=1.00 В ±5%, VCCAUX=1.80 В ±5%; VCCO выбирается по стандарту банка. Низковольтные grades меняют требования: поэтому 1.00 В нельзя автоматически назначить неизвестному полному заказному коду.

При одинаковом номинале INT/BRAM используют общий источник. Рекомендуемый порядок: INT/BRAM, AUX, затем VCCO; выключение в обратном порядке. Нарастание до 90%: 0.2–50 мс. Для XC7A50T сверх ICCQ при запуске: INT+120 мА, AUX+40 мА, VCCO+40 мА/банк, BRAM+60 мА. Это не рабочий бюджет нагрузки; он требует XPE/реальной логики/переключений и внешних нагрузок. VCCBATT нужен для ключа шифрования; без батареи подключается к GND либо VCCAUX.

Локальная DS181 v1.5/2013 является preliminary и не содержит нужной строки XC7A50T по току; она не использовалась как окончательное основание выбора мощности.

## Развязка и неиспользуемые выводы

Актуальная [AMD UG483 v1.14](https://docs.amd.com/v/u/en-US/ug483_7Series_PCB) сохранена; таблица2-2, стр.16, прочитана также визуально (`manufacturer/UG483-page16.png`). Производитель даёт следующий ориентир для XC7A50T FGG484:

| Шина | Развязка по UG483 |
|---|---|
| VCCINT | 1×330 мкФ + 3×4.7 мкФ + 5×0.47 мкФ |
| VCCBRAM | 1×100 мкФ + 1×0.47 мкФ |
| VCCAUX | 1×47 мкФ + 2×4.7 мкФ + 5×0.47 мкФ |
| VCCO Bank0 | 1×47 мкФ |
| VCCO прочие банки, на банк | 1×47/100 мкФ + 2×4.7 мкФ + 4×0.47 мкФ |

Один bulk 47/100 мкФ может обслуживать до четырёх банков одного напряжения. Это baseline PDN, а не подбор точных конденсаторов без ESR/ESL, derating и компоновки. Стандартные R/C переиспользовать; кастомные символы не требуются. Банки, сохранённые для будущих SMA, нельзя считать окончательно неиспользуемыми.

[UG482 v1.9](https://docs.amd.com/v/u/en-US/ug482_7Series_GTP_Transceivers), табл.5-4, стр.223, допускает для полностью неиспользуемой группы питания GTP: MGTAVCC/MGTAVTT/MGTRREF→GND, RX→GND, TX/REFCLK оставить floating. Если используется часть группы/Quad, правила меняются: обязательны рабочие MGT питания, MGTRREF через 100 Ω к MGTAVTT. Заземления на стр.2 Smart Artix применимы только к первому случаю. RGMII Ethernet не требует GTP.

[UG480 v1.11](https://www.amd.com/content/dam/xilinx/support/documents/user_guides/ug480_7Series_XADC.pdf), табл.1-1: VCCADC→VCCAUX 1.8 В даже без XADC; никогда GND. GNDADC→GND. Без внешней опоры VREFP→GNDADC, VREFN→GND; VP/VN→GND если не используются. Производительский PDF доступен через индекс web, но прямой HTTP download этого старого адреса вернул 404; копия актуальной английской UG480 в этой ветке не сохранена.

## Конфигурация и возможность программирования

Актуальная [UG470 v1.17](https://docs.amd.com/v/u/en-US/ug470_7Series_Config) сохранена как `manufacturer/UG470-v1.17.pdf`. Master SPI x1/x2/x4: M[2:0]=001. Mode straps напрямую либо через ≤1 кΩ к VCCO0/GND. При VCCO0 2.5/3.3 В CFGBVS→VCCO0; при ≤1.8 В CFGBVS→GND. Используемые при конфигурировании banks14/15 согласуются с Bank0.

PROGRAM_B/INIT_B: внешние pull-up ≤4.7 кΩ к VCCO0. PUDC_B: к VCCO14 или GND напрямую/через ≤1 кΩ, не floating. High отключает внутренние pull-ups SelectIO. DONE по умолчанию open-drain и имеет внутренний pull-up около10 кΩ; внешний330 Ω допустим, но необязателен. LED-ветка с240 Ω в Smart Artix требует проверки нагрузки/режима DONE при переносе.

Нужно вывести TCK/TMS/TDI/TDO, GND и VREF=VCCO0 на выбранный JTAG-разъём/контактную группу. Предложение для минимальной платы: внешний адаптер JTAG и доступ к PROGRAM_B/INIT_B/DONE; FT2232/4232 и USB/UART не нужны лишь для этого пути. Конкретный разъём с MPN ещё не выбран; наличие стандартного разъёма не подтверждает доступность модели MPS. Flash можно программировать через indirect JTAG; путь требует проверенного Vivado flow и совместимого кабеля.

## Загрузочная Flash

Точный исходник стр.6: `W25Q128JVSIQTR`; существующий LibReference `W25Q128JVSIQ`. Актуальная [Winbond W25Q128JV Rev M, 2024-12-24](https://www.winbond.com/resource-files/W25Q128JV%20RevM%2012242024%20Plus.pdf) скачана и визуально прочитана. S=8-pin SOIC208mil; I=−40…+85°C; VCC=2.7–3.6 В. Вариант Q имеет QE=1 **фиксированно**, /HOLD отключён. Функции: 1 /CS; 2 DO/IO1; 3 /WP/IO2; 4 GND; 5 DI/IO0; 6 CLK; 7 IO3; 8 VCC. Нет отдельного аппаратного reset у этого SOIC8.

Дефекты `flash-native-before.json`: pin7=`RESET` не отражает IO3; все восемь Electrical=7 (Power). Требуются отдельные исправления: pin1/6 Input; pin2/3/5/7 IO; pin4/8 Power (инженерная классификация по функциям документа). Нельзя объявлять неизменённую готовую модель электрически проверенной.

Корпус §10.1: шаг1.27 мм, размах H7.90 мм номинально, максимальная высота2.16 мм; название `SOIC127P790X216-8N` согласуется с ними, но правильность площадок требует нативного чтения. Сохранены изображения стр.6/69/76. Обвязка **из PDF Smart Artix**, проверенная в `pdf-review.md`: C18=0.1мкФ VCC–GND; R655=4.7кΩ /CS pull-up; R151=4.7кΩ DQ2 pull-up; R656=4.7кΩ DQ3 pull-up; все pull-ups к3.3В. Номинал series-резистора CCLK в этой проверке не вводится. Частота CCLK, возможная терминация и длины соединений требуют отдельной инженерной проверки по timing/signal integrity.

## Генератор 50 МГц

[Abracon ASV datasheet](https://abracon.com/Oscillators/ASV.pdf): ASV без25/18 в корне=3.3 В ±10%. `ASV-50.000MHZ-LRS-T`: 50 МГц, L −40…+85°C, R ±25ppm, S45/55%, T reel. Pin1 Tri-State Enable/Disable, pin2 GND/Case, pin3 Output, pin4 Vdd. High или open pin1 разрешает генерацию; low переводит выход в Hi-Z. Поэтому pin1 открытый в PDF допустим для этой модели, но его функция OE не превращается в NC.

Корпус7.0×5.08×1.8 мм, рекомендуемые площадки1.8×2.0 мм, центры5.08×4.0 мм, рекомендуемый рядом bypass10нФ. Все размеры проверены по локальному исходному ASV datasheet и изображению `output/altium/asv-outline.png`. Flash/QSPI и вывод FPGA с этим генератором требуют банка3.3 В; ввод непосредственно в1.8 В банк без согласования недопустим. Готовая библиотека существует; повторная загрузка/создание не нужны. Нативная сетка/портативность существующей модели остаются проверкой основного исполнителя.

Повторная read-only проверка LRS: нет опции нагрузки50, значит15пФ; T=1000шт/reel. OE: VIH≥0.7×Vdd, VIL<0.3×Vdd (при3.3В: ≥2.31В / <0.99В). Питание2.97–3.63В. Для50МГц: Idd max30мА, rise/fall max4нс, запуск max5мс. Расчётные следствия параметров: ±25ppm=±1.25кГц; при20нс периоде S даёт high9–11нс. VOH≥0.9×Vdd, VOL≤0.4В.

**Инженерная проверка границ:** DS181 Table8 для LVCMOS33 даёт VIHmin2.0В, VILmax0.8В и верхний рекомендуемый вход3.450В. При номинальном общем3.3В питании запас по High≥0.97В, по Low≥0.40В. Полные3.63В допустимого питания ASV сами по себе не гарантируют соблюдение FPGA input limits. Требуется общий согласованный3.3В источник, контроль его пределов и overshoot/undershoot. OE открытый не требует управления1.8В GPIO; такое управление не подтверждено как подходящее. Эти расчёты не заменяют проверку реального питания и clock signal integrity.

## Преобразователи питания из Smart Artix

Источник PDF стр.7: U36/U40/U41/U42=`TPS563210A` без суффикса. [TI TPS563210A](https://www.ti.com/product/TPS563210A) подтверждает SOT23-THIN DDF8, Vin4.5–17 В, Iout3 А, Vout0.76–7 В, adjustable SS и open-drain PG. Функции: 1GND,2SW,3VIN,4PG,5SS,6VFB,7EN,8VBST; VBST–SW требует100нФ. [TI order details](https://www.ti.com/product/TPS563210A/part-details/TPS563210ADDFR) подтверждает DDFR large tape/reel, DDFT small tape/reel с тем же устройством. DDFR предлагается как точный CAD-заказной вариант, а не прочитанный суффикс PDF.

Публичная TI ссылка [Ultra Librarian embedded](https://vendor.ultralibrarian.com/TI/embedded/?gpn=TPS563210A&package=DDF&pin=8) показала точный `TPS563210ADDFR`, символ `TPS563210ADDF`, footprints `DDF0008A_N/L/M`, форматы script/native Altium. Экспорт требует видимые reCAPTCHA и acceptance of terms; он остановлен. Подтверждены listing/preview, **native package не скачан**. Сохранены HTML источники.

По source_pdf ветке rail outputs: U36 1.0 В, U41 1.8 В, U40 1.5 В, U42 3.3 В; EN chain1.0→1.8→1.5→3.3. U51 получает PG3V3. L3/L7/L8/L9 лишь2.2мкГн2А без MPN: требуются точные inductors с достаточными Isat, Irms, DCR, корпусом; номинальная3А микросхема не доказывает пригодность2А дросселя. Rail1.5 В связан с DDR bank34 в источнике и может стать необязательным после выбора VCCO всех банков; питание и выводы bank34 удалять нельзя.

U51 исходника=`SPX3819M5-L-3-3` (fixed3.3 В Bank15/VCCIO_ADJ, не регулируемый вариантом резисторов). [MaxLinear SPX3819](https://www.maxlinear.com/product/power-management/power-conversion/ldos-and-regulators/linear-regulators-ldos/spx3819) подтверждает500мА, SOT23-5, EN и bypass. Pin1VIN,2GND,3EN,4BYP для fixed,5VOUT. Точный bulk MPN имеет OBS; `/TR` Active. `/TR` предлагается как packaging update. Проверять dropout, тепловыделение (Vin−3.3)×Iload и запуск;500мА не гарантируются любому PCB/входу.

Скачан официальный [SPX3819M5-L-3-3/TR CAD BXL](https://www.maxlinear.com/Document/index?id=22911&languageid=1033&type=Symbols%20%26%20Footprints&partnumber=SPX3819), 83,675 bytes, сохранён в `manufacturer/SPX3819M5-L-3-3_TR.bxl`. BXL требует поддерживаемой конвертации Ultra Librarian; это **не SchLib/PcbLib** и не пройденный native import. Альтернативный [SnapMagic listing](https://www.snapeda.com/parts/SPX3819M5-L-3-3/MaxLinear/view-part/) найден, но Altium package через него не получен. MPS наличие не проверялось.

Read-only проверка локального конвертера: в трёх uninstall registry ветках HKLM/HKLM WOW6432Node/HKCU найден только **Altium Library Loader2.2** (SamacSys). В `C:\Program Files`, `C:\Program Files (x86)`, `%LOCALAPPDATA%\Programs` не найдены имена файлов Ultra Librarian/UltraLib/BXL/Accelerated Designs/EMA Design. Стандартные `C:\UltraLibrarian`, `C:\Ultra Librarian`, `C:\UltraLib` и одноимённые папки Program Files отсутствуют. Поддерживаемая установка BXL-конвертера **не обнаружена в проверенных местах**; наличие portable copy вне них/у другого пользователя не исключено. Library Loader не считается доказательством поддержки BXL. Приложения не запускались; CAD-вызовов не было. Полный результат: `bxl-converter-local-check.json`.

## Неизвестные требования / конкретные незавершённые действия

- Полный заказной код FPGA, расчёт нагрузки XPE, входной5В источник/разъём и power-off handling.
- Окончательные VCCO bank13/14/15/16/34/35 и резерв для SMA. Bank0/14 для3.3 В Flash подтверждены как инженерная зависимость выбранного boot path; future SMA не фиксируют уровень/нагрузку/число портов.
- Точные MPN силовых дросселей и JTAG-разъёма; проверка PDN с реальными номиналами/derating.
- Исправление выявленных Electrical типов FPGA/Flash и pin7 Flash с отдельными native before/after invariants, затем ERC.
- TPS: пользователь проходит reCAPTCHA/terms и скачивает native Altium ZIP для `TPS563210ADDFR` с official embedded link; либо использует в Altium MPS экспорт с проверенными destinations.
- SPX: поддерживаемый импорт полученного manufacturer BXL в отдельную временную пару SchLib/PcbLib; если конвертер отсутствует, скачать готовый Altium export после обычной авторизации провайдера.

Перечень не объявляет базовую плату готовой: footprint mapping, электрические типы, модели питания, сетка и разрешение рабочих библиотек ещё требуют результатов основного исполнителя.
