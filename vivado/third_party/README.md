# Закреплённые зависимости Ethernet

Включён необходимый поднабор Verilog и timing Tcl из
[alexforencich/verilog-ethernet](https://github.com/alexforencich/verilog-ethernet/tree/77320a9471d19c7dd383914bc049e02d9f4f1ffb),
commit `77320a9471d19c7dd383914bc049e02d9f4f1ffb`.
Вложенный `lib/axis` — subtree этого же commit, tree
`bf008992b8ce4ebb1d6c9f56f2a591d1246254f4`. Отдельной плавающей загрузки axis нет.
Полный перечень включённых файлов и SHA-256: `verilog-ethernet/manifest.json`.
`run_tests.py` проверяет все суммы до моделирования.

Все включённые сторонние файлы сохранены без изменений. Модули и Tcl выбраны
по списку зависимостей upstream-примера `example/NexysVideo/fpga/fpga/Makefile`;
XDC назначения чужой платы не включён. `codex_sources/ethernet_core.v` адаптирован
из `example/NexysVideo/fpga/rtl/fpga_core.v`: удалены UART/GPIO/echo, добавлено
управление PPS, отключён FPGA TX clk90, включена синхронизация RX enable.
Заголовок лицензии оригинала сохранён.

Лицензии Ethernet и axis — MIT; тексты `COPYING` включены для обоих. При
распространении сохранять copyright и разрешение; гарантий нет. Платного
Ethernet IP не используется. Синтез/implementation/bitgen для указанного part
получили стандартные лицензии Vivado 2019.1 на этой машине.

Upstream объявлен устаревшим в пользу Taxi. Версия намеренно закреплена;
автоматического обновления нет. Совместимость этого поднабора проверена
Vivado 2019.1 (синтез и реализация) и XSim 2019.1/Icarus (тесты проекта),
а не предполагается по названию платы в примере.

Особенность 2019.1: vendor timing Tcl надо выполнять как Tcl (`source` после
синтеза в non-project build; тип `TCL` в constrs_1 в .xpr). Обычный `read_xdc`
не выполняет используемые там циклы `foreach`. Собственный pin XDC содержит
явные назначения, без Tcl-циклов.

Для независимой реализации управления задержками RTL8211E сверены факты из
[официального драйвера Linux](https://github.com/torvalds/linux/blob/master/drivers/net/phy/realtek/realtek_main.c)
(`rtl8211e_config_init`, страница 7, расширенная страница 0xa4, регистр 0x1c).
Код драйвера и GPL-зависимости в проект не копировались. Оба бита задержек
установлены вместе с force: OR 0x3800 с сохранением остальных битов.
