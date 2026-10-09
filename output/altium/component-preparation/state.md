# Состояние для продолжения — 2026-10-08

Работа выполнялась только в основном checkout:
`C:\Users\makarlistkov\Documents\Work\Engineering\FPGA-COURSE-WORK`.
Существующие пользовательские изменения сохранены. Commit/push не выполнялись. Исходные схемные листы и ARTIX.PrjPcb этой задачей не изменялись.

**Статус: неполный комплект;0 полностью готовых и подтверждённо подключённых новых компонентов.** Две рабочие SchLib прошли native save/reopen и488 endpoint/grid checks; новая Flash layout сохранена, correction не завершилась. Native executor blocked. Не начинать CAD-записи до read-only восстановления и проверки unsaved состояния.

## Сначала открыть эти отчёты

1. `components.md` — отбор блоков, точные MPN, источники и текущее состояние.
2. `transfer-plan.md` — что переносить/переработать и обязательные зависимости.
3. `validation.json` — численные проверки, hashes, model records и фактическое отсутствие new project connection.
4. `blockers.md` — главное действие пользователя Run→Stop, provider downloads и неподтверждённые MPN.
5. `evidence/qa-preview.md` — visual FAIL ASV, visual pending FPGA, BGA ball geometry pass.

## Завершённые независимые этапы

- Прочитаны user attachment, AGENTS.md, tools/altium/README.md, canonical altium-library/acquisition/native/failure guidance.
- Просмотрен PDF на стр.2/3/5/6/7/8 текстом и визуально, точные refs/rails/passives/maps сохранены в `evidence/pdf-review.md` и `evidence/pdf`.
- Official current AMD pinout совпал с484/484 native balls;291 exact name и193 допустимых aliases; unexplained mismatches0. Current DS181/UG470/UG483 и Winbond RevM сохранены с SHA256.
- Источники питания: TI export blocked CAPTCHA/terms; official SPX /TR BXL скачан; installed converter read-only check не подтвердил BXL support. Ethernet exact variants и готовые CAD listings подтверждены, native download login blocked. HanRun REV B PDF/crops и local Realtek vendor evidence сохранены.
- Из исходных native файлов созданы6 рабочих копий;6source SHA256 unchanged. `evidence/*-source-checkpoint.zip` содержит baseline native sources; `source-checkpoints.json` связывает пути/hashes.
- FPGA: центральная pair создана из exact existing X7 model, native pins оформлены и повторно открыты.484pins/10parts,5mm/GOST10pt,1mm electrical endpoints,0.5mm graphical anchors; model records/maps unchanged. FullPCB model resolution/compile не выполнены.
- ASV: selected LRS-T native extracted из10-entry SchLib; PCB isolated из8-entry PcbLib; SchLib save/reopen4pins;5mm/GOST10pt/1mm endpoints. Ссылка чужого FX3U-проекта заменена нативно на portable `PcbLib1.PcbLib`, model name/map сохранены. Остались4 eLine oldbody; footprint readback after prune pending.
- Flash: из существующей W25Q128JVSIQ/SOIC pair создан `new`; mm geometry native saved. Attempted electrical/name correction blocked, no verified after snapshot. Source allPower и pin7RESET — документированные дефекты; исправленная программа существует, не выполнялась повторно.

## Рабочие candidate файлы (не подключены)

| Path under repository | Статус |
|---|---|
| `ARTIX/ARTIX/libraries/project/ARTIX.SchLib` | Только FPGA. Native reload passed; visual pitch3mm pending. Generator now proposes4mm, not applied |
| `ARTIX/ARTIX/libraries/project/ARTIX.PcbLib` | Только BGA484, exact source copy, native484pad read. No project resolution |
| `ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib` | Только LRS-T; relative model link; old4eLine remain |
| `ARTIX/ARTIX/libraries/ASV-50MHz/new/PcbLib1.PcbLib` | Только ASV25000MHZEJT saved; native geometry after reopen pending |
| `ARTIX/ARTIX/libraries/W25Q128JV/new/W25Q128JVSIQ.SchLib` | Disk mm-layout saved. Unsaved editor state unknown after failed correction; do not close/reload blindly |
| `ARTIX/ARTIX/libraries/W25Q128JV/new/SOIC127P790X216-8N.PcbLib` | Exact existing footprint source copy |

Originals under X7, ASV-50MHz root and W25Q128JV/source remain unchanged. Existing inaccessible ASV exact-MPN folder untouched. Candidate reports are companions, not fabricated successful component.json packages.

## Последний CAD сбой — не повторять старую запись

Mutation job `0b5f9f78b4034984a80b45aaa67e5ac6` started but not finished; recovery `c58f4e3aefe640ef98c37e45496bf9f1` failed. Evidence includes exact requests/scripts/logs. User must dismiss error and Run→Stop; user editor is not killed. Source generator enum names corrected from `eInput/eIO/ePower` to documented `eElectricInput/eElectricIO/eElectricPower`; actual dialog not read, unsaved edits unknown.

Before this, shell-launched open jobs61a4.../bcaca... were NOT_STARTED and bounded recovery succeeded; same native MCP path worked. No more shell CAD execution. Cause of transport difference not proven. `native_prepare.py` now **emits** JSON requests only; it does not launch CAD. Action `copy` writes copies once and refuses existing files; do not rerun it.

## Продолжение после действия пользователя

1. `altium_recover_executor` bounded read-only health. If it fails, stop and use blockersB01; do not loop.
2. Snapshot actual open Flash including unsaved edits with `altium_inspect_library_component`; compare to disk checkpoint and source. Checkpoint deliberately only after current state established.
3. Fix observed Flash source defect with documented eElectric enums and IO3, native save/reopen, compare designators/pads/model map/geometry; source originals remain preserved. No automatic replay of failed request.
4. Apply ASV old-eLine removal and FPGA4mm candidate layout only after backups/checkpoint; native reload, numeric+visual QA. Generator complete484map based on exact existing pin identities. Do not use ballmap for another device.
5. Verify ASV PCB after save/reopen and complete native model resolution. Merge only verified components/dependencies into central pair; collision checks; no unrelated components.
6. Backup/checkpoint ARTIX.PrjPcb, inspect current refs/live dirty state, add appropriate project-relative references natively, verify actual model resolution. Existing user refs must be preserved; no silent overwrite.
7. Acquire native power/Ethernet packages through authorised ordinary provider path; temporary explicit destinations, original/native archive, isolate, GOST/mm, save/reopen, maps, project resolution. No MPS claims without actual export evidence.
8. Select missing interface/passive-special MPNs based on requirements; final power/startup/PDN and directional ERC. Dedicated compiler fixtures can validate pins/nets separately from board design. Do not modify six existing user sheets just to make a test.

## Проверки, которые можно повторять без CAD

From repository root:
```powershell
& '.\tools\altium\.venv\Scripts\python.exe' '.\output\altium\component-preparation\validate_saved_work.py'
```
Это **read-only CAD audit**, пишет только JSON отчёт. Оно сравнивает saved snapshots, модели, sources и project refs; не читает unsaved editor state и не вызывает ERC. Current successful result: fpga_pin_count484, fpga_grid_pass=true, asv_grid_pass=true, source_files_unchanged=true, ready_connected0, old_asv_lines4.

`render_native_previews.py` строит реконструкцию сохранённой геометрии с GOST font; это не Altium screenshot. Native requests must be executed through MCP only, sequentially, after recovery and established state. Do not infer new4mm layout from old successful3mm snapshot.

## Ограничения объёма

DDR3/HDMI/LCD/TF/SD/USB/FTDI/UART не включены. SMA не проектировались; port count, level/load/50Ω and final GPIO remain unspecified. R/C custom libraries not created. PCB не разводилась. Ethernet retained in requested scope and explicitly pending, not silently excluded.
