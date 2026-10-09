# TPS563210A — создание символа и подключение к ARTIX

Создан по прямому запросу пользователя собственный native Altium символ TPS563210A; готовый чужой символ не подменялся. Использована существующая пользовательская PCB library, без изменения footprint.

## Результат

- `ARTIX/ARTIX/libraries/TPS563210A/TPS563210A.SchLib`: единственный компонент **TPS563210A**, одна часть, 8 выводов. Default designator **DA?**, видимый Comment **TPS563210A**, функциональная надпись DC/DC.
- `ARTIX/ARTIX/libraries/TPS563210A/TPS563210A.PcbLib`: existing footprint **SOT65P280X110-8N**, площадки 1–8. Original SHA256 `e79085bf6cae8f2ad77f42ab562f367dc8a559b13efa7efa69152cbf7ca8ae7b` сохранён.
- В `ARTIX/ARTIX/ARTIX.PrjPcb` добавлены ровно две относительные ссылки: `libraries\TPS563210A\TPS563210A.PcbLib` и `libraries\TPS563210A\TPS563210A.SchLib`. Все предыдущие references открытого пользовательского проекта сохранены. Дубликатов нет.
- Native IntegratedLibraryManager разрешает модель из точного проектного `TPS563210A.PcbLib`; глобальные временные библиотеки не устанавливались.
- SchLib сохранена и повторно открыта; проверены имена, номера, электрические типы, шрифты, длины и координаты. PcbLib повторно открыта после проверки отсутствия unsaved изменений; native pad snapshots совпали полностью.

## Распиновка и исходная ERC-классификация

**Обновление по следующему прямому запросу пользователя:** всем 8 выводам задан Electrical = Power (7). Таблица ниже описывает первоначальную классификацию, теперь переопределённую пользователем. Electrical в Altium является настройкой электрической проверки; графическое оформление хранится отдельно. Текущие значения проверены после native save/reopen в `gost-edit/after-native.json`.

Источник: [TI TPS563210A datasheet](https://www.ti.com/lit/ds/symlink/tps563210a.pdf), раздел Pin Configuration and Functions, страница 3. Локальная копия `datasheets/Datasheets/POWER/TPS563210A.pdf`, pin table просмотрена визуально в `pinout-page3.png`. Устройство TPS563210A, корпус DDF (8-pin SOT-23); упаковочный суффикс DDFR/DDFT не выбирался по догадке.

| Физический вывод | Имя | Altium Electrical | Роль |
|---:|---|---|---|
| 1 | GND | Power | Общий вывод силовой/управляющей части |
| 2 | SW | Output | Коммутируемый силовой узел |
| 3 | VIN | Power | Вход питания |
| 4 | PG | Open Collector | Открытый сток Power Good; Altium использует этот тип для open-drain сигнала |
| 5 | SS | Input | Управление soft-start внешним конденсатором; инженерная ERC-классификация |
| 6 | VFB | Input | Обратная связь |
| 7 | EN | Input | Разрешение работы |
| 8 | VBST | Power | Питание bootstrap драйвера |

Позиции выводов сгруппированы по функции, номера не переставлены. PG = 4 и SS = 5 соответствуют pin table TI; ошибки/перестановки в отдельных layout illustration не использовались как pinout source. Карта 1→1 ... 8→8 прочитана нативно после reopen; порядок записей карты Altium нормализует по порядку объектов, он не влияет на соответствие.

## Геометрия символа

Корпус 35 × 30 мм; основные точки подключения на сетке 1 мм, вспомогательная сетка 0.5 мм; горизонтальные выводы 5 мм, шаг строк 6 мм. GOST Common, regular, 10 pt для имён/номеров/надписей. Исходный manifest хранит размеры в мм, преобразование в internal coordinates выполняется только при генерации API-запроса.

**Текущее оформление после запроса:** все тексты, номера/имена выводов и линии чёрные (native Color = 0). DC/DC перемещена с y = −15 мм на y = −3 мм, в верх центрального поля. Добавлены две вертикальные разделительные линии x = 12 мм и x = 23 мм, от y = 0 до −30 мм. Карта площадок и геометрия выводов не изменены. Native colors/coordinates проверены в `gost-edit/appearance-after-native.json`; точные состояния перед правкой сохранены в disk/editor-checkpoint backups. Предпросмотр обновлён.

Сохранённые точки подключения проверены с допуском одного внутреннего шага Altium = 0.00000254 мм. Все 8 проходят. Предпросмотр `symbol-preview.png` восстановлен из сохранённых графических записей и native pin snapshot с установленным GOST font, визуально просмотрен; наложений имён нет. Это реконструкция геометрии, не скриншот Altium.

## Сохранность и границы проверки

До записи сделаны backup existing PcbLib и ARTIX.PrjPcb в `backups`. В live ARTIX были несохранённые references (в частности, X7/new); их состояние сохранено нативно и отдельно скопировано в `backups/ARTIX.live-checkpoint.PrjPcb` до добавления TPS. Пользовательские references не заменены старой дисковой версией.

Схемные листы не изменялись, TPS на них не размещался. Поэтому библиотечная проверка и project model resolution пройдены, но ERC конкретного преобразователя/питания не выполнялся и не заявляется. User footprint не перерабатывался: проверены identity, все 8 pad names, native pad geometry invariants и доступность модели; manufacturer land-pattern manufacturing release review не подменяется этой операцией.

Полная машиночитаемая проверка — `validation.json`. Manifest, native requests/results, baseline/reopen pad snapshots и model-resolution/map reports сохранены рядом. Companion audit `preparation-20261008.json` лежит рядом с библиотекиными файлами; он не содержит выдуманного downloaded SchLib source.

## Повторная проверка без изменения CAD

```powershell
& 'C:\Users\makarlistkov\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.\output\altium\TPS563210A\render_validate.py'
```

Создание и подключение выполнены последовательно через `altium_local`. Генератор `build_requests.py` только формирует JSON native requests; он не редактирует бинарные CAD-файлы. Повторно запускать create при существующем SchLib нельзя; generator откажется перезаписывать.
