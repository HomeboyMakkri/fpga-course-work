# Комплект базовой платы Artix-7 — проверенное состояние

Дата: 2026-10-08. Исходник: `datasheets/Schematic_Smart_Artix_251120.pdf`.
Полностью готовых и подтверждённо подключённых новых компонентов: **0**. Комплект **не завершён**. Три существующие native модели использованы для рабочих копий; две SchLib прошли save/reopen и численную проверку488 точек подключения, но визуальная проверка/публикация ещё не пройдены. Не путать эти результаты с ERC или готовностью платы.

| Блок | Обозначение, страница PDF | Точный компонент | Назначение | Зависимости | Готовая модель / существующая библиотека | Решение |
|---|---|---|---|---|---|---|
| FPGA | U37A–J, 2/3/8 | PDF: XC7A50T-FGG484; локально XC7A50T-2FGG484I | Базовая FPGA | Все 484 вывода, 10 частей, питание всех банков, JTAG/конфигурация | `libraries/X7`, SchLib + PcbLib | Переиспользовать существующую модель; grade PDF не установлен |
| Конфигурация | U37A, 2 | Выводы той же FPGA | Master SPI и программирование | M0–M2, CFGBVS, PROGRAM_B, INIT_B, DONE, PUDC_B, JTAG | Часть FPGA | Не создавать отдельную микросхему; разъём/strap требуют выбора |
| QSPI | J2, 6 | W25Q128JVSIQTR | Загрузка bitstream | 3.3 V; /CS, IO0…3, CCLK; C18 = 100 nF; R655 (/CS), R151 (IO2), R656 (IO3) по 4.7 kΩ | `libraries/W25Q128JV/source`, W25Q128JVSIQ + SOIC | Q имеет fixed QE = 1, /HOLD отключён; pin7 = IO3; correction не завершена |
| 50 МГц | X6, 6 | PDF только 50 MHz; предложен ASV-50.000MHZ-LRS-T | Локальный такт | 3.3 V, OE, C827 100 nF, R657 22 Ω | `libraries/ASV-50MHz/Schlib1.SchLib` содержит готовый LRS-T среди 10 компонентов | В `new` выделены только LRS-T и ASV25000MHZEJT; ссылка исправлена на PcbLib1.PcbLib; старые4 eLine ещё удалить |
| DC/DC | U36/U40/U41/U42, 7 | TPS563210A, order suffix отсутствует | U36 = 1.0 V, U41 = 1.8 V, U42 = 3.3 V; U40 = 1.5 V DDR/VCCO34 в PDF | Дроссели, FB/EN/PG, расчёт нагрузок/запуска | Готовая модель заявлена TI/UL; native export CAPTCHA/terms | После выбора VCCO34 решить об U40 и перепроектировать PG→EN U42 |
| LDO | U51, 7 | SPX3819M5-L-3-3 | VCCIO_ADJ исходной платы | Тепловой расчёт и нужное VCCO | Требуется готовая модель | Решить после бюджета I/O |
| Феррит | FB9, 2 | BLM18SG121TN1D | Фильтрация питания XADC | 1.8 V → VCC_ADC; C824 1 µF, C823 100 nF, C848 4.7 µF | `libraries/FB BLM18SG121TN1D`, готовые модели | Источник найден; native save/reopen и model resolution пока не проверены |
| Ethernet PHY | U24, 5 | RTL8211E-VB-CG | Интерфейс управления | MAC FPGA, RGMII/MDIO/reset/straps, внешние 1.0/3.3 V, 25 MHz | CAD listing подтверждён; archive не скачан: login/challenge | Отдельный обязательный интерфейсный блок после основы |
| Ethernet разъём | J3, 5 | HR911130A | RJ45 с магнитикой | MDI/CT/LED, shield/ESD по требованиям | Готовая модель у провайдеров, локальной нет | Сохранить точный вариант; не подменять RJ45 без магнитики |
| 25 МГц | X4, 5 | MPN не указан; 4-pad кварц | Опорная частота PHY | XI/XO, нагрузочные C по кварцу | Не выбран | Не подменять активным генератором |
| Сброс/индикация | KEY3/LED1/LED2, 6; LED5, 2; LED4, 7 | MPN отсутствуют | RESET_N логики и индикация DONE/питания | KEY3: R663 = 10 kΩ, C828 = 4.7 µF; LED1/2: R50/R51 по 330 Ω; LED4: R452 = 330 Ω; DONE: R522/R642 по 240 Ω требуют проверки | MPS не доступен через bridge | Готовые модели после выбора MPN; KEY3 не PROGRAM_B; custom R/C не создавать |

Подтверждённое в PDF, предложения и неизвестные требования разделены в строках. DDR3, HDMI, LCD, TF/SD, USB исключены; SMA-тракты, число портов и уровни не назначаются.

## Что фактически сделано в библиотеках

| Рабочий файл | Проверено | Остаётся |
|---|---|---|
| `ARTIX/ARTIX/libraries/project/ARTIX.SchLib` | XC7A50T-2FGG484I;484pin/10parts; save/reopen; имена/типы/части сохранены;5mm/GOST Common10pt;1mm endpoints;0.5mm текст/корпус; model records/maps неизменны | Шаг3mm тесен по preview:4mm предложено в генераторе, не применено; all484Passive в источнике ограничивают ERC; target project resolution не проверен |
| `ARTIX/ARTIX/libraries/project/ARTIX.PcbLib` | Копия готовой BGA-модели без изменения;484pads;22×22;1mm pitch; все ball labels | Native model-map/project resolution/footprint land/3D release review; библиотека не подключена |
| `ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib` | Только1 exact LRS-T,4pins;5mm/10pt;save/reopen;1mm endpoints; ModelName и1:1 map сохранены; foreign model location заменён на `PcbLib1.PcbLib` | Остались4eLine старого корпуса, потому визуальный FAIL; project resolution pending |
| `ARTIX/ARTIX/libraries/ASV-50MHz/new/PcbLib1.PcbLib` | Нативно удалены7посторонних footprints, сохранён только ASV25000MHZEJT | После native save выбранный Data stream изменился; геометрию нельзя подтвердить только hashes; save/reopen native pad/3D compare pending |
| `ARTIX/ARTIX/libraries/W25Q128JV/new/W25Q128JVSIQ.SchLib` | Рабочая копия готовой модели;mm-layout native save succeeded | Исправление IO3/electrical остановилось: STARTED_WITHOUT_COMPLETION; unsaved неизвестно. Reopen/grid/type validation pending |
| `ARTIX/ARTIX/libraries/W25Q128JV/new/SOIC127P790X216-8N.PcbLib` | Копия готовой модели;8pads native read; source hash сохранён | Mapped resolution из проекта/3D review pending |

Никаких новых ссылок в ARTIX.PrjPcb не добавлялось, схемные листы не изменялись. Из существующих пользовательских references X7 и смешанный ASV уже были в проекте; их наличие не засчитывается как проверка6 новых рабочих копий. Центральная pair пока содержит только FPGA, ASV/Flash остаются отдельными кандидатами, не объединёнными с ней.

Источники6 native файлов сохранили SHA256. Checkpoint архивы в `evidence/*-source-checkpoint.zip`; baseline provenance и hashes в `evidence/source-checkpoints.json`, per-library companion reports. Старый `ASV-50.000MHZ-LRS-T/original/new` имеет `Access denied`; его содержимое и оригинальный download archive не проверены и не изменялись. Новые рабочие копии не являются повторно скачанными моделями.

## Обвязка и зависимости

Полный список refs/номиналовR/C исходника сохранён в `evidence/pdf-review.md`: boot pullups, oscillator, DC/DCFB/PG/EN, bank decoupling, XADC, Ethernet, reset/LED. Резисторы/конденсаторы не превращались в custom-компоненты.

Обязательные специальные позиции: TPS563210A (DDF, suffix не указан PDF), дроссели L8/L7/L9 (2.2 µH, точный MPN/Isat неизвестен), при независимом VCCO15 SPX3819M5-L-3-3/TR (документированное предложение tape/reel вместо OBS bulk), FB9, JTAG-разъём совместимый с используемым кабелем, кварц 25 MHz с согласованным CL/ESR, RTL8211E-VB-CG, HR911130A, выбранные buttons/LED. В PDF вход 5V_DC подтверждён; источник питания, разъём и ток собственной платы не установлены.

Источник PDF использует1.0/1.8/1.5/3.3V;1.5V относится к DDRbank34. Новая схема требует решения о VCCO15/34 и пересчётаPG→EN. Нельзя удалять питание bank13 только потому, что нет егоGPIO; нельзя оставлять NC служебное питание. Полная rail table и предложенный current-AMD PDN baseline сохранены отдельно от исходных номиналов.

## Сохранённые источники

- PDF schematic, SHA256`a198469eabd1abe7a504667ca2bf17a7595e5017d6f4830a380dd04bf8923230`: `datasheets/Schematic_Smart_Artix_251120.pdf` и визуальные crop в `evidence/pdf`.
- [AMD DS181](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet), [UG470](https://docs.amd.com/v/u/en-US/ug470_7Series_Config), [UG483](https://docs.amd.com/v/u/en-US/ug483_7Series_PCB), [Artix pinout files](https://www.amd.com/en/developer/resources/adaptive-socs-and-fpgas/package-pinout-files/artix-7-package-device-pinout-files.html): current PDFs/pinouts сохранены с hashes в `evidence/manufacturer-source-manifest.json`.
- [Winbond W25Q128JV RevM](https://www.winbond.com/resource-files/W25Q128JV%20RevM%2012242024%20Plus.pdf): downloaded PDF и страницы pin/function/package; IO3 fixedQE подтверждён.
- [Abracon ASV](https://abracon.com/Oscillators/ASV.pdf): local manufacturer PDF; описание pins и selected-variant review в `evidence/base-manufacturer-review.md`.
- [TI TPS563210A](https://www.ti.com/product/TPS563210A): официальный CAD link для TPS563210ADDFR/DDF0008A; native export остановлен на CAPTCHA/terms.
- [MaxLinear SPX3819](https://www.maxlinear.com/product/power-management/power-conversion/ldos-and-regulators/linear-regulators-ldos/spx3819): точный /TR BXL сохранён, native формат не получен; source/hashes в manifest.
- Realtek local vendor PDF и HanRun REV B vendor-authored PDF с archive URL/hash/crops в `evidence/ethernet/sources.json`. [RTL8211E-VB-CG CAD](https://app.ultralibrarian.com/details/73517a83-7c9f-11ea-8c00-0ad2c9526b44/Realtek/RTL8211E-VB-CG), [HR911130A CAD](https://app.ultralibrarian.com/details/2ea77810-e93a-11eb-9033-0a34d6323d74/HanRun/HR911130A): listings symbol+footprint подтверждены, download требует login.

Наличие страниц CAD не является native package download или доступностьюMPS. Полный stage-by-stage результат — `validation.json`; следующий шаг — `blockers.md`/`state.md`.
