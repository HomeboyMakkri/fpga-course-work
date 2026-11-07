# Загрузка Ethernet-прошивки в Smart Artix

7 ноября 2026, по указанию пользователя прошивка загружена в SRAM FPGA.
Это последующая аппаратная операция после программных проверок в [RESULTS.md](RESULTS.md).

| Проверка | Результат |
|---|---|
| Целевой JTAG | `localhost:3121/xilinx_tcf/Xilinx/26SH168A` |
| Устройство | единственное `xc7a50t_0`, PART `xc7a50t` |
| IDCODE | `0362C093` |
| Файл | `vivado/bitstream/smart_artix_ethernet.bit` |
| SHA-256 перед загрузкой | `c5202dbf9f283cfe54e223d6187e36ec05e81b4c82327805c49e911cc6e81cd9` |
| Startup | `HIGH`, EOS=1, GWE=1 |
| DONE pin / internal | 1 / 1 |
| CRC / IDCODE / security error | 0 / 0 / 0 |
| Flash | не записывалась |

Команда выполнена Vivado 2019.1 через [program_sram.tcl](../../program_sram.tcl).
Перед записью сверены SHA-256, точный кабель, число устройств в цепочке и PART.
После записи выполнен `refresh_hw_device`, прочитаны configuration registers.
Журнал: [program_sram.txt](program_sram.txt).

Все PPS после загрузки OFF; включение — UDP-командой с ПК.
Сетевая связь, PHY MDIO, реальные периоды и ширина PPS **не проверены** этой
загрузкой. Физического проводного сетевого адаптера Windows не обнаружено;
нужны Ethernet/USB-Ethernet либо доступная проводная сеть и измерительный прибор.
Окончательный внешний RGMII timing sign-off остаётся открытым.

SRAM-конфигурация теряется при отключении питания; повторная загрузка по
[корневой инструкции](../../../SMART_ARTIX_START.md). Содержимое Flash сохранено.
