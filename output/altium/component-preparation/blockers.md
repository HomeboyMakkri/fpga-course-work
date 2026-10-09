# Незавершённые этапы и действия

## B01 — исполнитель Altium остановлен на неопределённой записи

Факты: запись исправления Flash начала исполняться (`START`, `select exact library component`, `documented Winbond Rev M source defect correction`), но не создала `result.txt`/`FINISHED` за30 секунд. Job: `tools/altium/runtime/jobs/0b5f9f78b4034984a80b45aaa67e5ac6`. Состояние `STARTED_WITHOUT_COMPLETION`, редактор PID13464 остаётся жив. Пятисекундная read-only recovery probe job `c58f4e3aefe640ef98c37e45496bf9f1` тоже не стартовала; executor_recovered=false. Никакая следующая CAD-запись не запускалась.

В моём генераторе использовались неверные имена enum `eInput/eIO/ePower`. [Официальный Altium TPinElectrical](https://www.altium.com/documentation/altium-dxp-developer/schematic-api-types-reference) определяет `eElectricInput/eElectricIO/eElectricPower`. Генератор уже исправлен **без повторного исполнения**. Это доказанное несоответствие кода API; точный текст модальной ошибки не прочитан, поэтому нельзя утверждать, что им объясняется всё состояние редактора. VPN/версия/аккаунт причиной не установлены.

Остановка дальнейших записей следует текущему запросу пользователя, AGENTS.md и [altium-library SKILL.md](../../../../.agents/skills/altium-library/SKILL.md): "Never replay a mutation blindly." Ошибка кода исправлена агентом; человеку требуется только освободить недоступный native executor, а не исправлять скрипт.

**Действие пользователя:** посмотреть ошибку Altium, закрыть её и выполнить `Run → Stop` для скрипта. Сохранить собственные документы обычным способом. Рабочую `libraries/W25Q128JV/new/W25Q128JVSIQ.SchLib` не закрывать/не перезагружать вслепую: в ней могут быть частичные несохранённые изменения. После Stop сообщить агенту. Далее агент делает read-only recovery, snapshot несохранённой Flash, сравнение с `evidence/flash-ondisk-after-timeout.SchLib` и безопасный checkpoint; только после установления состояния выполняет исправленный код. Если Stop не освобождает исполнитель — сохранить документы и нормально перезапустить Altium самостоятельно. Принудительный restart не разрешён и не выполнялся.

**Доступный обходной путь ИИ до освобождения:** сохранённые файлы, SHA256, документация, карты и отчёты уже проверены. Бинарное редактирование CAD или новый CAD-исполнитель не используется. Следующий исправленный код готов в `native_prepare.py`, но не подтверждён native run.

## B02 — визуальная проверка FPGA/ASV не завершена

ASV: определённые4 старые `eLine` остались рядом с новым прямоугольником; они вне миллиметровой сетки. Генератор уже дополнен удалением `eLine`; запись не повторялась из-за B01. Нужно удалить только в `ASV-50MHz/new`, save/reopen, проверить old_line_count=0 и повторно просмотреть символ.

FPGA: сохранён шаг3 mm с GOST Common10 pt. Реконструкция сохранённой геометрии показывает риск наложения глифов; это не native screenshot. Генератор изменён на4 mm, **ещё не применён**. Нужно native применить и проверить всю10-part геометрию/читаемость, не потеряв484 pins/models. Исходные all-Passive types сохранены как запрошено; для содержательной directional ERC требуется отдельная документированная классификация.

Рабочий ASV footprint сохранён после выделения единственного ASV25000MHZEJT. Selected Data stream и GUID streams изменились при native save, поэтому пока нет подтверждения pad/3D invariants после reopen. Не выводить изменение геометрии только из разницы hash и не считать неизменность доказанной.

## B03 — модели не разрешены из целевого проекта

Новая центральная pair создана, пока содержит только FPGA. Новые ASV и Flash candidate pairs остаются отдельно. Они **не подключены** к ARTIX.PrjPcb. Нативное объединение, проверка коллизий, portable links и actual project model resolution не выполнялись после B01. Исходные user references X7 и mixed ASV сохранены.

Пользовательских действий сверх B01 не требуется для обычных агентских исправлений. После восстановления агент завершает изоляцию/визуальные checks, создаёт backup/checkpoint целевого проекта, добавляет проверенные компоненты/модели и относительные references, проверяет resolution; затем отдельный compiler fixture. Не добавлять непроверенные модели только ради видимого подключения.

## B04 — готовые native power/Ethernet модели требуют провайдера

| Компонент | Что реально доступно | Что требуется |
|---|---|---|
| TPS563210ADDFR (предложенный order code) | Официальный TI CAD link; UL symbol TPS563210ADDF + DDF0008A_N/L/M. Native export показал reCAPTCHA/terms | Пользователь обычным образом проходит CAPTCHA/terms на CAD-ссылке [TI](https://www.ti.com/product/TPS563210A) и скачивает Altium ZIP; либо экспортирует готовую модель из MPS, подтвердив её наличие и destinations |
| SPX3819M5-L-3-3/TR | Официальный83,675-byte BXL скачан и hash записан; /TR Active, bulk PDF OBS | Поддерживаемый BXL→Altium импорт или готовый Altium ZIP после авторизации. Локальный Ultra Librarian converter не найден в проверенных местах; Altium Library Loader2.2 не доказывает поддержку BXL |
| RTL8211E-VB-CG | UL listing symbol+footprint для exact MPN; Realtek datasheet/pinmap | Обычная авторизация и native ZIP с [UL exact page](https://app.ultralibrarian.com/details/73517a83-7c9f-11ea-8c00-0ad2c9526b44/Realtek/RTL8211E-VB-CG) или подтверждённый MPS export |
| HR911130A | UL listing; HanRun REV B datasheet скачан, магнитика/pinout/drill drawing просмотрены | Обычная авторизация и Altium ZIP с [UL exact page](https://app.ultralibrarian.com/details/2ea77810-e93a-11eb-9033-0a34d6323d74/HanRun/HR911130A) или подтверждённый MPS export |

CSE branch остановлена после трёх разных наблюдений: web cache miss, browser `net::ERR_BLOCKED_BY_CLIENT`, Cloudflare JS/cookie challenge. SnapMagic download был недоступен/403. Ни VPN, ни запрет пользователя причиной не объявлялись. CAPTCHA/credentials не обходились; новых аккаунтов не создавалось. Другие доступные ветки выполнены.

До Library Loader требуется **отдельная временная пара** с полными SchLib/PcbLib destinations, проверенными до импорта. Не использовать открытые рабочие библиотеки или remembered foreign path. Native originals сохранить отдельно, извлечь только exact MPN и модели, проверить затем добавить в проект. BXL/EPW/webpage не считать готовым Altium компонентом; custom replacement symbols не рисовались.

## B05 — отсутствуют исходные MPN/нагрузки

- FPGA grade/temperature для закупки (existing exact library -2FGG484I не выбирает grade автоматически).
- Входной5V источник/разъём и ток, XPE/startup/PDN; VCCO15/34 и резерв будущих SMA; схема PG→EN без DDR rail.
- Дроссели2.2 µH: точный MPN/корпус/DCR/Isat; кварц25 MHz: MPN/CL/ESR/drive; совместимый с реальным кабелем JTAG-разъём; button/LED MPN/корпуса.

Это пункты выбора, а не доказательство отсутствия готовых моделей. Можно предложить конкретные совместимые order codes по требованиям, но нельзя выдавать их за MPN PDF. R/C — перечень исходных номиналов и назначения готов, свои библиотеки не создавались. Уровни/SMA-порты/50Ω нагрузки не назначать.

## B06 — старый пакет ASV недоступен

`ARTIX/ARTIX/libraries/ASV-50.000MHZ-LRS-T/{original,new,component.json}` возвращает `Access denied` в чтении. Причина ACL/файловой системы не установлена; каталог не перемещался, права не менялись. Использованы доступные существующие native source `ASV-50MHz/Schlib1.SchLib`, `PcbLib1.PcbLib`; их hashes сохранены и unchanged. Скачать заново не потребовалось. Проверка старого download archive/provenance остаётся pending; рабочая копия не объявляется подтверждённым повторным импортом старого пакета.

**Итог:** fully ready + connected новых компонентов0, полный комплект не готов. Результаты по каждой проверке и точная степень достоверности записаны в validation.json.
