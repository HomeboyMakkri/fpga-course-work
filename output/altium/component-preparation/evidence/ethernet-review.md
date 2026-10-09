# Ethernet: сверка компонентов и зависимостей

Дата проверки: 2026-10-08. Область: отдельный запрошенный интерфейс управления, после базового FPGA-комплекта. CAD-вызовы, импорт, создание символов, изменение библиотек и проекта этим исследованием не выполнялись.

## Состояние

Точные RTL8211E-VB-CG и HR911130A установлены по визуальной странице 5 Smart Artix. Для обоих подтверждены страницы провайдеров с **Altium symbol + footprint**, но сами CAD-пакеты не получены. X4 — 25 MHz кварц, точный MPN/корпус в PDF отсутствует. Число готовых и подключённых Ethernet-компонентов по результату этого исследования: **0**. Manufacturer Part Search не проверялся и доступность модели в MPS не заявляется.

| Блок | Обозначение и PDF | Точный компонент | Назначение | Зависимости | Модель/решение |
|---|---|---|---|---|---|
| Ethernet PHY | U24, Smart Artix p5 | Realtek RTL8211E-VB-CG | 10/100/1000 PHY с RGMII | Внешнее питание 1.0 V, 3.3 V, 25 MHz, reset, straps, MDIO/MDC, MAC в FPGA | Ultra Librarian и CSE имеют готовую модель; загрузка/импорт/ГОСТ/публикация не пройдены |
| RJ45 с магнитикой | J3, p5 | HanRun HR911130A | Гальваническая развязка четырёх пар и LED | Полярность четырёх MDI-пар, центр. отводы, LED-резисторы, shield/chassis | UL подтверждает Altium symbol+footprint; SnapMagic также объявляет модель. Пакет не скачан |
| Опорный кварц | X4, p5 | Только 25 MHz; **MPN неизвестен** | Опора PHY | Кварцевые выводы 1/3, GND 2/4, C680/C681=27 pF | Не выбирать корпус/MPN по рисунку. Готовая точная модель не определена |
| Ethernet пассивы | p5, перечень ниже | Номиналы подтверждены PDF, procurement MPN не заданы | Питание/reset/straps/LED | Выбор допуска, voltage rating, ESR, CL и корпус по окончательным нагрузкам | Переиспользовать готовые R/C; кастомные библиотеки не создавать |

## Подтверждено документацией Realtek

Локальный `datasheets/Datasheets/NET/rtl8211e.pdf` — Realtek rev 1.6, 03 April 2012, 79 файловых страниц. Обложка содержит обозначение `CONFIDENTIAL: Development Partners Only`; это уже предоставленный локальный файл, его происхождение за пределами checkout не установлено. В отчёте используются сведения производителя, а не коммерческие параметрические карточки. Отдельно различены физический индекс PDF и напечатанный номер документа:

- Package: QFN-48, 6.00 × 6.00 mm, шаг 0.40 mm; exposed pad является аналоговой/цифровой землёй. В Smart Artix он имеет номер 49. Geometric EP nominal 4.4 × 4.4 mm — размер корпуса, а не разрешение автоматически задать land pattern. См. PDF p75–76 / printed p66–67; ordering PDF p79 / printed p70.
- **VB и VL не взаимозаменяемы по I/O**. RTL8211E-VB-CG поддерживает RGMII 3.3/2.5 V; VL — 1.5/1.8 V. `RTL8211EG-VB-CG` — другой 64-pin вариант с GMII. Для U24 нужны именно E-VB-CG, QFN-48, EP.
- AVDD10/DVDD10 operating range 0.95–1.09 V; analog/digital 3.3 V 2.97–3.63 V. Digital I/O power pins 15,21 должны соответствовать SELRGV и выбранному FPGA VCCO. См. PDF p21 / printed p12, PDF p65 / printed p56.
- Источник опоры: фундаментальный параллельный AT-cut кварц 25 MHz; стабильность ±30 ppm, начальный допуск ±50 ppm, ESR ≤30 Ω, drive ≤0.5 mW. Для внешнего oscillator допускаются 25/50 MHz с параметрами таблицы 59. CKXTAL1=42 вход; CKXTAL2=43 выход; при внешнем oscillator CKXTAL2 должен быть GND. Поэтому X4 нельзя автоматически заменить уже имеющимся ASV без отдельной проверки топологии и полного clock-spec. См. PDF p17 / printed p8, p66 / printed p57.
- PHY reset и доступ к регистрам: документ описывает ≥10 ms low и последующую задержку 30 ms для внутреннего регулятора. Для выбранного в Smart Artix внешнего 1 V нужен пересмотр power/reset sequence и app note; RC на схеме не является подтверждённым контролем последовательности. См. PDF p38 / printed p29, p64 / printed p55.
- PHY обеспечивает физический уровень. Ethernet MAC, RGMII DDR timing, MDIO-management, MAC address и нужная прикладная протокольная логика должны быть реализованы/предусмотрены в FPGA. Сам PHY не делает плату готовым интерфейсом управления. RTL8211E-VB использует RGMII; GMII относится к EG-VB. См. PDF p28 / printed p19.

## Обвязка Smart Artix p5: установленное состояние

**Внутренний DC/DC отключён:** ENSWREG pin38=GND; REG_OUT pin48=NC. Внешняя VCC1V0 идёт через R42=0 Ω на AVDD10/DVDD10. VDDREG pins44/45 подключены к AVDD33. Дроссель внутреннего PHY-преобразователя отсутствует; нельзя включать его в обязательную BOM при этой архитектуре. Требуемый ток и rail budget совместно с FPGA остаются инженерной проверкой, а не выводом из факта наличия VCC1V0.

| Обозначения | Значение PDF | Назначение/сеть |
|---|---|---|
| R42 | 0 Ω | VCC1V0 → AVDD10/DVDD10 |
| C662 | 22 µF | Bulk VCC1V0 перед R42 |
| C663 | 0.1 µF | VCC1V0 перед R42 |
| C664, C665, C666 | 0.1 µF каждый | AVDD10 local decoupling |
| C668, C669 | 0.1 µF каждый | DVDD10 local decoupling |
| C660 + C661 | 22 µF + 0.1 µF | AVDD33/VDDREG |
| C672 + C673 | 22 µF + 0.1 µF | VCC3V3 bulk/decoupling |
| C679, C674, C675 | 0.1 µF каждый | AVDD33 local decoupling |
| C676, C677 | 0.1 µF каждый | DVDD33 local decoupling |
| R39 | 2.49 kΩ | RSET39 → GND, PHY bias/reference |
| R43, R454, R55, R56 | 4.7 kΩ каждый | RXD0..3 pull-up; SELRGV/TXDLY/AN straps |
| R57 | 4.7 kΩ | RXCTL/PHY_AD2 pull-down |
| R58, R59 | 4.7 kΩ каждый | LED0/PHY_AD0 и LED1/PHY_AD1 pull-up |
| R60 | 4.7 kΩ | LED2/RXDLY pull-down |
| R455 | 1.5 kΩ | MDIO pull-up к DVDD33 |
| R52 + C670 | 4.7 kΩ + 1 µF | ETH_RST pull-up/RC; активный PHYRSTB29 также идёт в FPGA |
| C680, C681 | 27 pF каждый | Два load-cap кварца X4, к GND |
| R61, R62 | 330 Ω каждый | Ограничение тока LED J3 |
| C678 | 0.1 µF | P1 J3 → GND, P10 J3 прямо GND; перепроверить reference termination |
| R63 | 0 Ω | Shield/chassis к общей GND в исходнике |

По straps исходника: SELRGV=1 → RGMII 3.3 V; TXDLY=1, RXDLY=0; AN1/AN0=11; PHY_AD2:0=011 (адрес 3). Это **поведение схемы-источника**, не окончательные настройки собственной платы. Задержки RGMII должны соответствовать выбранной MAC, constraint timing и PCB; PHY default/straps нельзя копировать без согласования. FPGA-выходы не должны мешать sampled straps во время reset.

PMEB33, CLK12546 и NC12 в p5 оставлены неподключёнными. INTB20 идёт к FPGA, MDIO31/MDC30 — в management interface. В p5 отдельный ESD-array или внешний Ethernet transformer отсутствует. HR911130A уже содержит magnetics/common-mode structures, их повторная покупка как отдельного блока не обоснована. Дополнительная ESD/EMC защита и стратегия chassis/земли — открытые требования, а не подтверждённые MPN.

## HR911130A: источник и проверенные соответствия

Даташит HanRun REV B, 4 страницы скачан с публичного зеркала [LCSC](https://atta.szlcsc.com/upload/public/pdf/source/20250812/A9B443FB770AA42A34C92B1A15093C54.pdf). Это документ производителя на зеркале, не CAD-пакет. Сохранены PDF и четыре PNG, страница 1 сверена визуально со Smart Artix.

MDI0+/− идут на P2/P3, MDI1+/− — P4/P7, MDI2+/− — P5/P6, MDI3+/− — P8/P9. Green LED anode/cathode=11/12, Yellow=14/13. P1 — центр. отводы chip-side, P10 — common termination. Shield крепления необходимо учитывать отдельно от signal contacts. Для будущей проверки footprint сохранён vendor component-side drill drawing p3: 10 signal holes, 4 LED holes, два shield holes, два mounting holes. Доступный здесь report не подтверждает конкретный PcbLib.

## Источники готовых моделей и блокировки

- [Ultra Librarian RTL8211E-VB-CG](https://app.ultralibrarian.com/details/73517a83-7c9f-11ea-8c00-0ad2c9526b44/Realtek/RTL8211E-VB-CG): страница точного MPN показывает Altium Designer symbol + footprint + 3D и `Login to Download`. Модель объявлена провайдером; содержание native package ещё не проверено.
- [Ultra Librarian HR911130A](https://app.ultralibrarian.com/details/2ea77810-e93a-11eb-9033-0a34d6323d74/HanRun/HR911130A): Altium Designer symbol + footprint, 3D отсутствует, `Login to Download`.
- [SnapMagic HR911130A](https://www.snapeda.com/parts/HR911130A/HanRun/view-part/): страница/поисковый снимок показывает символ и footprint с Altium форматом, но предупреждает о стороннем происхождении модели. Прямой fetch вернул 403. Нативный пакет не получен.
- [CSE RTL8211E-VB-CG](https://componentsearchengine.com/part-view/RTL8211E-VB-CG/Realtek): найден из [таблицы RTL82](https://componentsearchengine.com/search?term=RTL82) с `Download Model`. Exact-page web fetch: cache miss; IAB: `net::ERR_BLOCKED_BY_CLIENT`; обычный HTTP fetch: Cloudflare `Enable JavaScript and cookies to continue`. После трёх релевантных методов ветка остановлена. Эти факты не доказывают проблему VPN.
- Browser к SnapMagic из subagent дополнительно сообщил `IAB visibility is not supported in a subagent thread`; главный агент может проверить браузер в своей ветке. Авторизация провайдера/terms/CAPTCHA не обходились, аккаунты не создавались.
- [Официальная HanRun product-page](https://en.hanrun.com/rj45_1000/203.html) индексируется как HR911130A, однако live web fetch три раза возвращал error/timeout; скачать REV B удалось с независимого зеркала. Из этого нельзя делать вывод о доступности official CAD.

Следующий конкретный путь: пользователь/главный агент получает exact Altium zip от Ultra Librarian (native option, без запуска legacy scripts), либо CSE package через обычную авторизованную browser session. После этого последовательно сохранить original, настроить **оба** абсолютных temporary SchLib/PcbLib пути, выполнить штатный import/extraction и только затем ГОСТ/сетка/native save+reopen/model verification/publish. X4 требует выбора exact crystal MPN с CL и корпусом; 27 pF из Smart Artix не доказывает нужную CL нового изделия.

## Файлы и контрольные суммы

| Файл | SHA256 | Происхождение |
|---|---|---|
| `datasheets/Datasheets/NET/rtl8211e.pdf` | `B081006E6619BA24B38BE4959675E36748AD3F80053F27E9319B38A44620FA3C` | Предоставленный checkout; Realtek document rev1.6 |
| `evidence/ethernet/HR911130A-Hanrun-LCSC.pdf` | `99BD6AC77D8B46BBF4764056C3FBA8B18B5180DE9488052ED1204C85B27FD3B0` | HanRun REV B, публичное LCSC mirror URL выше |

Дополнительно: `evidence/ethernet/rtl8211e-local-text.txt`, `HR911130A-text.txt`, `HR911130A-page-01.png` … `04.png`, `sources.json`. Исходная Smart Artix p5: `evidence/pdf/page-05.png`, `page-05-plain.txt`. Библиотечных/CAD файлов в Ethernet evidence пока нет. Сохранённость ранее существовавших библиотек обеспечена отсутствием любых записей в них; их native-инварианты данным исследованием не измерялись.
