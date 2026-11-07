# Smart Artix: проект, загрузка и управление PPS

Все файлы находятся в этом репозитории `fpga-course-work`.
7 ноября 2026 Ethernet-прошивка загружена в SRAM FPGA, DONE=1; Flash сохранена.
[Протокол загрузки](vivado/reports/ethernet_step7/PROGRAMMING.md). Ethernet/PPS на плате ещё не измерены.

| Что открыть | Расположение |
|---|---|
| Проект Vivado 2019.1 | [vivado/ethernet_generator.xpr](vivado/ethernet_generator.xpr) |
| Готовая Ethernet-прошивка | [vivado/bitstream/smart_artix_ethernet.bit](vivado/bitstream/smart_artix_ethernet.bit) |
| Полная инструкция, протокол, контакты | [vivado/README.md](vivado/README.md) |
| Отчёты сборки и моделирования | [RESULTS.md](vivado/reports/ethernet_step7/RESULTS.md) |
| План работ | [VIVADO_IMPLEMENTATION_PLAN.md](VIVADO_IMPLEMENTATION_PLAN.md) |

Проект: `xc7a50tfgg484-2`, top `smart_artix_top`. После включения/сброса
все три канала OFF. Для каждого независимо доступны 1/10/100 PPS.
Импульс высокий, номинально 100 нс; опора — внутренние 10 МГц от генератора
платы 50 МГц. После SET перезапускается только выбранный канал.

## Загрузка в FPGA

Из корня репозитория, при закрытом Vivado/Hardware Manager:

```powershell
& C:/Xilinx/Vivado/2019.1/bin/vivado.bat -mode batch -nojournal -log tmp/program-sram.log -source vivado/program_sram.tcl -tclargs C:/Users/mkkr/Documents/Codex/fpga-course-work/vivado/bitstream/smart_artix_ethernet.bit 26SH168A
```

Путь и serial кабеля относятся к текущему стенду; на другом ПК их нужно
заменить после read-only обнаружения `vivado/probe_hardware.tcl`.
Скрипт проверяет точный кабель, единственное устройство и PART `xc7a50t`.
Записывается только SRAM FPGA. Flash не меняется; после выключения питания
эта загрузка теряется, повторяется загрузка из существующей Flash.
Загрузка bitstream сама по себе не проверяет сетевой обмен и физические PPS.

## Команды с ПК

Подключить J3 RJ45 к физическому Ethernet/USB-Ethernet или коммутатору.
Проводному интерфейсу ПК назначить `192.168.1.10/24`; адрес FPGA —
`192.168.1.128`, UDP порт `1234`. Wi-Fi и VirtualBox Host-Only не заменяют
проводное соединение с платой. После загрузки дождаться link/autonegotiation.

```powershell
python vivado/pps_control.py 1 1 --bind 192.168.1.10
python vivado/pps_control.py 2 10 --bind 192.168.1.10
python vivado/pps_control.py 3 100 --bind 192.168.1.10
python vivado/pps_control.py 2 get --bind 192.168.1.10
python vivado/pps_control.py 2 off --bind 192.168.1.10
```

Нужен Python 3 со стандартной библиотекой. Клиент ждёт подтверждение из домена
PPS. При тайм-ауте команда могла исполниться: перед повтором прочитать режим.
ICMP ping не реализован. Контакты PPS на J5: 7/9/11, земля 5/6; сначала сверить
ориентацию разъёма и допустимые 3,3 В для прибора.

## Повторная сборка

Сохранить правки и закрыть Vivado. Выходной каталог должен быть пустым:

```powershell
./vivado/build.ps1 -Project -OutputDirectory C:/path/to/new-build
```

Исходники, XDC, закреплённые MIT-зависимости и тесты находятся в `vivado`.
Внешние RGMII timing-бюджеты предварительные; аппаратные измерения и проверка
Ethernet/PPS описаны в полной инструкции и отчёте.
