# Fast rectangular GOST-style IC symbols

Use this mode for rectangular ICs like the accepted TPS563210A. This is the user's accepted visual profile, not formal certification against every GOST clause. Keep the regular acquisition workflow for requested ready-made models. Do not apply this IC template to R/C, connectors or non-rectangular symbols by default.

## Maintained helper and accepted example

Use `scripts/gost_symbol.py`, which imports the single implementation in `<repo>/tools/altium/gost_symbol.py`. It emits JSON native requests and validates responses; it never launches the editor or edits CAD binary data. Execute emitted requests sequentially through `altium_run_delphiscript` MCP. No new MCP registration/add-on is needed. Shell is for preparing requests and verification: shell-launched CAD returned NOT_STARTED in this session while MCP worked.

The exact approved reference is `<repo>/tools/altium/manifests/gost-tps563210a-approved.json`. Reuse it only for TPS563210A. Other devices need their own verified physical pin table; do not infer a pinout/order suffix from this example. Existing verified models/provenance need not be downloaded/imported again for typography edits.

## Profile and manifest

Three fields separated by two full-height black vertical `eLine` objects; function label at the top of the middle field. Black GOST Common regular10 pt; pins5 mm; electrical grid1 mm, auxiliary0.5 mm. Defaults: row pitch6 mm, first row y−6 mm, header y−3 mm. Increase field widths for long labels. The approved TPS example has widths12/11/12 mm and body35×30 mm.

Set every text colour explicitly, including Designator, Comment, parameters and free labels; font selection alone left the text navy. Set pin colour0 and disable component colour override. Convert mm directly to integer internal coordinates with `round(mm/0.00000254)`, not integer mils.

Minimal schema (pins abbreviated, not a complete component):

```json
{
  "component": "EXACT_LIBREFERENCE",
  "source": "manufacturer pin-table URL/document/page or verified provenance",
  "electrical_policy": "preserve",
  "font_name": "GOST Common",
  "font_size_pt": 10,
  "pin_length_mm": 5,
  "parts": [{
    "id": 1,
    "function": "DC/DC",
    "column_widths_mm": [12, 11, 12],
    "pitch_mm": 6,
    "row_start_mm": 6,
    "label_y_mm": -3,
    "pins": [
      {"designator": "3", "name": "VIN", "side": "left"},
      {"designator": "2", "name": "SW", "side": "right"}
    ]
  }]
}
```

Provide all physical pins exactly once; multipart IDs consecutive from1. Existing names must match the native before snapshot. Supported sides are left/right, with row order following the manifest. Repeated names are allowed; repeated physical designators are rejected.

`electrical_policy`: `preserve` defaults for redraw; `pins` uses explicit per-pin `electrical`0..7; `power` sets every pin to Power7. Power is an ERC setting, not a universal GOST rule; require the user's instruction or explicit choice of the approved TPS preset. Creation requires `pins` or authorized `power`. Types0..7: Input, IO, Output, OpenCollector, Passive, HiZ, OpenEmitter, Power. The helper emits documented `eElectric…` constants, never the incorrect `eInput/eIO/ePower` that previously stopped execution.

## Create

User must request native authoring; do not synthesize a substitute for a requested ready-made model. Verify the manufacturer's pinout/package and the supplied PcbLib's internal footprint name. Use the given working paths. The helper refuses overwrites and targets under `original`.

```powershell
& '.\tools\altium\.venv\Scripts\python.exe' '.\.agents\skills\altium-library\scripts\gost_symbol.py' prepare `
  --mode create --manifest '<absolute manifest JSON>' `
  --path '<absolute NEW SchLib>' --pcblib '<absolute existing PcbLib>' `
  --footprint '<exact internal footprint name>' --out '<absolute fresh bundle directory>'
```

1. Start `altium_status(live=True)`; use the established bounded recovery workflow if blocked.
2. Prepare the bundle; read `mutation.json` and pass its fields unchanged to `altium_run_delphiscript`. Save the complete response; require success and saved=true.
3. Run `readback.json` through MCP, saving its response. It closes/reopens only a clean target and reads pins, fonts, colours, body/dividers/header, and models.
4. Verify with the command below and visually inspect the saved symbol. The footprint file is hash-tracked and unchanged. Creation generates an explicit relative model link and identity pin-to-pad map; if physical labels require a different map, use the native mapping workflow instead.

## Redraw

Read the exact component once with `altium_inspect_library_component`; persist its complete response as `before-native.json`. Build the complete manifest from it. This mode explicitly replaces body/free labels/lines while preserving pin objects, parameters, models and unrelated components. Use a narrower appearance edit if full-body replacement was not requested.

```powershell
& '.\tools\altium\.venv\Scripts\python.exe' '.\.agents\skills\altium-library\scripts\gost_symbol.py' prepare `
  --mode redraw --manifest '<absolute manifest JSON>' --before '<absolute before-native.json>' `
  --path '<absolute working SchLib>' --out '<absolute fresh bundle directory>'
```

1. Prepare backs up the disk file and emits `checkpoint.json`, `mutation.json`, `readback.json`.
2. Run checkpoint through MCP and persist its response. It saves the user's current editor state before editing.
3. Run `capture-checkpoint --bundle '<absolute bundle>' --result '<absolute checkpoint response JSON>'`. This backs up the saved editor state and fingerprints models/maps/unrelated components. The mutation checks this checkpoint exists and refuses a document modified after it.
4. Run mutation and readback sequentially through MCP, saving both responses. Proceed only on verified success. Never replay an uncertain write.
5. Verify and visually review. Redraw removes old `eRectangle/eLine/ePolyLine/eLabel` from both component and editor containers, bounded at1000. Including `eLine` matters: omitting it left an old contour in the previous ASV edit. Other graphic kinds require inspection and a supported specific operation.

## Verify and publish

```powershell
& '.\tools\altium\.venv\Scripts\python.exe' '.\.agents\skills\altium-library\scripts\gost_symbol.py' verify `
  --bundle '<absolute bundle>' --result '<absolute readback response JSON>'
```

Require `verification.json` success=true. It checks every pin's name/part/type/root/orientation/length, fonts/modes, black colours, one body/two dividers/header per part, document grids, and endpoints within one internal step. Maps are compared by pairs independent of order—Altium reordered identity maps on save. Missing/renamed pins, unexpected model or unrelated-component changes, wrong colours or off-grid results are incomplete.

Visual review still checks label fit, overlap and residual contours. A reconstruction from saved graphics/native pins is allowed when honestly labelled; do not call it an Altium screenshot. This helper does not certify all GOST clauses or prove project connection/placed ERC.

Only when connection was requested: back up/checkpoint the current live project, preserve its existing references, add exact local SchLib/PcbLib references natively, and verify model resolution from that project. Do not install temporary libraries globally. For placed parts, update only requested instances and use the project compiler; pin movement changes electrical endpoints.

## Speed and failures

Component-specific work is the manifest. Reuse this implementation rather than writing new Pascal, editing pins one call at a time, duplicating models, or repeating provider searches for styling. Creation needs two native requests after health; redraw needs inspect/checkpoint/mutation/readback, with local backups/verification between them.

After timeout inspect exact job/saved and unsaved state, stop dependent writes, and continue independent checks. Fix code/input errors autonomously. Modal editor/provider steps require human action; do not restart/kill Altium or change VPN/accounts. Existing AGENTS and failure-recovery limits apply.
