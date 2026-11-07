# Пункт7: результат реализации и проверки

Последующее обновление: [прошивка загружена в SRAM, DONE=1](PROGRAMMING.md), Flash не изменён. Сетевой обмен и PPS на плате остаются непроверенными.

Дата: 7 ноября 2026, Smart Artix, Vivado2019.1 build2552052,
`xc7a50tfgg484-2`, top `smart_artix_top`. Это программная проверка новой
Ethernet-прошивки; аппаратная работоспособность пока не подтверждена.

## Что реализовано

RGMII DDR MAC с frame FIFO, ARP/IPv4/UDP; независимые OFF/1/10/100 PPS;
проверка двухбайтовых команд, чтение состояния и ответ после применения;
один атомарный request/ack command slot; PHY reset/MDIO init с проверкой
ID/TA, RMW/readback задержек, отключением EEE и autonegotiation full duplex.
PHY reset тянется вниз, затем отпускается в Z через штатные R52/C670.
Старт всех каналов OFF; выбранный канал перезапускается, первый импульс
через полный период, длительность один такт опоры10 МГц.

Инструкция, формат пакетов, адреса и воспроизведение:
[README](../../README.md). Исходный Git был чистым; процессов Vivado не было.
GUI не закрывался принудительно, несохранённые редакторы не изменялись.
Старый bitstream и измерения сохранены. Схема сверена по изображениям листов2/5,
назначения подтверждены также `io.rpt`; чужой pin XDC не использован.

## Моделирование

| Проверка | Результат / доказательство |
|---|---|
| Все12 SET (3 канала ×4 режима), GET каждого, независимость фазы | PASS, cycle scoreboard каждого ref-такта |
| Настоящие RGMII preamble/FCS, ARP, IPv4, UDP | PASS, модель125 МГц; Python независимо проверяет2 ARP и20 ответов, FCS/IP/UDP checksum/адреса/payload |
| Некорректные channel/mode/length, wrong MAC/IP/порт, MF/offset, checksum/FCS | PASS, число команд не изменяется; кадры дрейнятся/отбрасываются |
| UDP checksum0, ненулевой правильный, неверный | PASS, прикладной checksum verifier |
| Повтор SET | PASS, повторное применение и перезапуск выбранного канала |
| Остановка/возврат net и ref, full, reset pending | PASS, bundle не искажается, второй ref-pending запрос отклоняется, reset не воспроизводит старую команду |
| Stalls header/payload ответа, AXIS bubbles, ранний tuser, длинный payload | PASS, данные держатся под backpressure, busy-команда не выполняется |
| MDIO по проводам | PASS, ID, TA, RMW/readback, EEE disable, AN, link loss/recovery, wrong ID/нет PHY fail closed |
| Реальные коэффициенты PPS10 МГц | PASS, периоды10000000/1000000/100000 тактов, неизменённый pps_generator |
| Полная оболочка с UNISIM | PASS, MMCM/reset/mailbox/PPS; команды введены на вход mailbox |

Icarus Verilog12.0 devel (s20150603-1539-g2693dd32b), XSim2019.1.
В интеграции21 request,17 SET выполнены,3 GET,1 pending SET отменён reset;
20 ответов. Конечные invalid/overflow в stdout равны0 из-за последующего
reset; отбрасывания проверяются до него, overflow отдельно проверяется равным1.
Логи: `icarus_tests.txt`, `xsim_tests.txt`, `xsim_top.txt`, `pps_real_period_icarus.txt`.
Реальный PPS-тест выполнен до интеграционного прогона; сам PPS RTL не менялся.
XSim и Icarus используют функциональную PHY-модель; это не аналоговый
sign-off PHY/PCB, не тест10/100 и не аппаратное автосогласование.

## Синтез, implementation, ограничения

Фактический `.xpr` собран через `project_build.tcl`, после closed-GUI
`update_project.tcl`. Non-project flow также проверен при разработке.
Финальная команда: `vivado.bat -mode batch -nojournal -log tmp/ethernet-release.log -source vivado/project_build.tcl -tclargs tmp/ethernet-release`.
Лицензии Synthesis/Implementation/part получены; коммерческого Ethernet IP нет.
Сторонний RTL byte-exact из закреплённого Git commit, без плавающих зависимостей,
MIT/axis лицензии и SHA256 сохранены. `.gitattributes` предотвращает смену
концов строк vendor на Windows; в build_manifest дизайн нормализован к LF.

| Проверка | Финальный результат |
|---|---|
| DRC | 0 нарушений |
| Setup WNS / TNS | 0.228 нс / 0.000 нс |
| Hold WHS / THS | 0.037 нс / 0.000 нс |
| Pulse-width slack | 0.264 нс, нарушений0 |
| RX DDR setup / hold | 0.228 / 0.273 нс |
| TX DDR setup / hold | 0.490 / 0.443 нс |
| CDC Critical | 0 |
| Нет clock / unconstrained internal endpoints | 0 / 0 |
| Нет input/output delays без документированного исключения | 0 / 0 |
| Bus skew | все4 ограничения выполнены, см. `bus_skew.rpt` |

`cdc.rpt` содержит21 предупреждение, без blanket waiver:
5 CDC-15 — held_command→ref_command, удержание до request/ack;
2 CDC-17 — held_result→result_data, захват после ack;
13 CDC-15 — frame FIFO commit bundle, upstream update/ack удерживает bundle;
1 CDC-6 — Gray read pointer, upstream max_delay/bus_skew.
Синхронизаторы помечены ASYNC_REG; command/result routes ограничены8 нс.
Нет blanket asynchronous clock_groups. MDIO routing bound256 нс меньше
полупериода512 нс; первые MDIO/RDY/request/ack stages и async reset исключены
по назначению, остальные стадии проверяются обычным timing.
`check_timing` отдельно показывает исключённые reset_n/MDIO и асинхронные
PPS/PHY-reset outputs. Unconstrained table содержит только clock-only MMCM
feedback, IDELAY REFCLK и forwarded TX clock, без незаданных data paths.
Обычные synthesis warnings относятся к неиспользуемым выходам/константам
универсального стека и литералам ширины; Critical Warnings/Errors финальной
сборки отсутствуют. Подробности сохранены в полных логах.

## Файлы и границы результата

Новый [bitstream](../../bitstream/smart_artix_ethernet.bit):
SHA256 `c5202dbf9f283cfe54e223d6187e36ec05e81b4c82327805c49e911cc6e81cd9`.
Старая автономная PPS-конфигурация не изменена:
SHA256 `70bd92555e1eeea93d9aec32a41df9dad6eb32528ab6b457f1a56afe978dfef4`.
Контрольные суммы исходников, схемы, PHY PDF и тестовых кадров —
`build_manifest.json`. Routed DCP остаётся в локальном `tmp/ethernet-release`
и воспроизводится сборкой; в Git публикуются исходники, bitstream и отчёты.

**Не подтверждено на железе:** физические link/ARP/UDP, MDIO readback,
режимы10/100/1000, восстановление link, реальные периоды/ширина новой прошивки,
ревизия платы, корпус/speed grade, питание и RGMII skew/duty/PVT.
TX internal delay+2 нс и allowance дорожек±0,2 нс — предварительный бюджет;
численный STA выполнен относительно него. PHY datasheet integrated-delay
setup/hold не заменяет проверку реальных задержек/дорожек. Окончательный
внешний timing sign-off остаётся открытым; нарушения не скрывались RGMII
false-path исключениями.

Read-only JTAG обнаружил `xc7a50t_0`, PART `xc7a50t`, target
`localhost:3121/xilinx_tcf/Xilinx/26SH168A`. На этом этапе до отдельного указания пользователя SRAM и Flash не программировались; последующая SRAM-загрузка описана в [PROGRAMMING.md](PROGRAMMING.md).
Нужны Ethernet/USB-Ethernet или проводная сеть, кабель к J3, подтверждение
маркировки/ревизии и анализатор/осциллограф. Windows сейчас видит Wi-Fi,
Bluetooth, WSL, туннель и VirtualBox Host-Only; физического RJ45-адаптера нет.

Временные решения: IP/MAC/порт, старт OFF, перезапуск фазы, один command slot,
ограниченный UDP-протокол. Нет transaction ID/дедупликации/аутентификации,
watchdog, внешней опоры или гарантии доставки. При остановке ref высокий
PPS может остаться высоким до возврата такта; pending ждёт.
