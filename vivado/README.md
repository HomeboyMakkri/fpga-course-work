# Генератор PPS для Smart Artix

Открыть `ethernet_generator.xpr` в Vivado 2019.1. Проект использует `xc7a50tfgg484-2`, верхний модуль `smart_artix_top`, локальные исходники и XDC из `codex_sources`. Временные директории Vivado не хранятся в Git.

Стендовая версия формирует 10 МГц из встроенного такта платы 50 МГц через MMCM. При включении выходы автоматически задаются на 1, 10 и 100 PPS; Ethernet-управление ещё не реализовано. Импульсы активны высоким уровнем, номинальная ширина 100 нс. KEY3 выполняет сброс. Назначение контактов и подключение анализатора — в `codex_sources/SMART_ARTIX_README.md`.

`codex_sources/pps_generator.v` реализует три независимых канала. Интерфейс `cmd_valid`, `cmd_channel` (1–3) и `cmd_mode` (0=OFF, 1=1 PPS, 2=10 PPS, 3=100 PPS) синхронен `clk_ref`. Каждая команда перезапускает только выбранный канал; первый импульс возникает через полный период. Передача команд из домена Ethernet ещё не выполнена. При остановке опоры синхронная логика не обновляется и высокий выход может остаться высоким.

`bitstream/smart_artix_pps.bit` — копия тестовой конфигурации, загруженной на плату; SHA-256 `70bd92555e1eeea93d9aec32a41df9dad6eb32528ab6b457f1a56afe978dfef4`. `measurements/check.sr` и `check.pvs` — захват PulseView и его настройки. По измерению 50 млн отсчётов при 24 Мвыб/с обнаружены периоды около 1,000057 с, 100,00566 мс и 10,00056 мс. Пользователь подтвердил, что при первом захвате провода C2 и E1 были переставлены. Ширина 2–3 отсчёта согласуется со 100 нс с ограниченной точностью анализатора.

Проверка из корня репозитория с Icarus Verilog:

```powershell
iverilog -g2012 -s pps_generator_tb -o "$env:TEMP\pps-test.vvp" vivado/codex_sources/pps_generator.v vivado/codex_sources/pps_generator_tb.v
vvp "$env:TEMP\pps-test.vvp"
iverilog -g2012 -s smart_artix_top_tb -o "$env:TEMP\smart-artix-test.vvp" vivado/codex_sources/sim_mmcm_model.v vivado/codex_sources/pps_generator.v vivado/codex_sources/smart_artix_top.v vivado/codex_sources/smart_artix_top_tb.v
vvp "$env:TEMP\smart-artix-test.vvp"
```

Модель MMCM в тесте оболочки упрощённая и не проверяет аналоговые параметры MMCM. Реальные периоды 10 000 000, 1 000 000 и 100 000 тактов отдельно проверяются тестом `pps_real_period_tb.v`. Ранее выполненный Vivado implementation завершился без DRC-ошибок, внутренние setup/hold выполнены; output delays для асинхронного анализатора не задавались.

Для сборки вне GUI из пустой директории: `vivado -mode batch -source vivado/build.tcl -tclargs <пустая_папка_для_результатов>`.
