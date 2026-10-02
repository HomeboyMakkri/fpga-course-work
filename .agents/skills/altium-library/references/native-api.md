# Verified native SchLib workflow (Altium 25.8.1)

The deterministic implementation is `<installation>/library_api.py`. Prefer the MCP commands to rewriting DelphiScript. The script bridge runs `ScriptingSystem:RunScript` via a secondary launcher and reads each isolated job result; it never edits native CAD binary files.

## Pin API that worked

```pascal
F := SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common');
P.PinLength := MilsToCoord(5/0.0254);
P.SetState_Name_CustomFontID(F);
P.SetState_Designator_CustomFontID(F);
P.SetState_Name_FontMode(1);
P.SetState_Designator_FontMode(1);
```

Read using `GetState_Name_CustomFontID`, `GetState_Designator_CustomFontID`, `GetState_Name_FontMode`, `GetState_Designator_FontMode` and `SchServer.FontManager.GetFontSpec`. Both custom modes must be 1; assigning a font ID alone leaves the system font enabled. Do not assume a pin exposes a label's `FontId` property. Windows family name was confirmed as `GOST Common`.

`1 mil = 10000` internal coordinates. `5 mm` rounds to `1968504` coordinates (Altium resolution), approximately `196.8504 mil`. Read back internal coordinates; do not compare only rounded UI text.

```pascal
I := C.SchIterator_Create;
I.AddFilter_ObjectSet(MkSet(ePin));
P := I.FirstSchObject;
while P <> Nil do begin
  P.OwnerPartId := PartId;
  P.OwnerPartDisplayMode := 0;
  P.Location := Point(MilsToCoord(XMils),MilsToCoord(YMils));
  P.Orientation := Rotation;
  P := I.NextSchObject;
end;
C.SchIterator_Destroy(I);
```

Bracket edits with `SchServer.ProcessControl.PreProcess(L,'')` / `PostProcess` in `try/finally`, then `SD.SetModified(True); L.GraphicallyInvalidate; SD.DoFileSave('')`. For readback, close/reopen the saved target through `Client.CloseDocument(SD)` and `Client.OpenDocument('SCHLIB',path)`, then select the exact component via `L.SchLibIterator_Create` / `MkSet(eSchComponent)` and `L.CurrentSchComponent := C`. Never close a dirty document; checkpoint user edits first.

## Multipart manifest

```json
{
  "component": "EXACT_LibReference",
  "parts": [
    {
      "id": 1,
      "label": "BANK 14",
      "pins": [
        {"designator":"P20","name":"IO_0_14","x_mils":2200,"y_mils":0,"orientation":0},
        {"designator":"P22","name":"IO_L1P_T0_D00_MOSI_14","x_mils":2200,"y_mils":-100,"orientation":0}
      ]
    }
  ]
}
```

This abbreviated example is a schema illustration; real manifests must list all original pins. `ball` is accepted instead of `designator` for the saved FPGA manifest. Part IDs are consecutive from 1; all designators unique; original names must match. Coordinate values are integer mils; orientation is 0=right, 1=up, 2=left, 3=down. Existing fonts and lengths remain unchanged in repartitioning.

For `replace_body=true`, the tool replaces all rectangles/free labels with one body and title per part. Titles use the original component Comment font. User parameters, component Designator/Comment, pins and model objects are not removed. Default `false` is appropriate for moving pins inside an already designed multipart symbol.

## Failures learned from the actual editor

- Removing an active editor rectangle with `C.RemoveSchObject(R)` alone left it in the component iterator. An unbounded remove loop consequently hung Altium. Remove from both containers: `C.RemoveSchObject(R); L.RemoveSchObject(R);` (likewise for free labels). Keep a bounded loop and return a structured failure when the limit is reached. This was confirmed by counting rectangles before and after on a disposable library.
- The installed DelphiScript interpreter did not accept the attempted `raise Exception.Create(...)` guard. Use ordinary verified API calls and explicit result values; an unsupported guard can itself wedge the script runner before execution starts.
- SchLib pin `UniqueId` changes on every `SD.DoFileLoad`, even without edits (confirmed for all 484 pins). Use the persistent physical Designator/ball for round-trip identity checks. Saved model/map records and separate model streams are also compared; drawing container offsets are ignored.
- Repeated `SD.DoFileLoad` on an already open SchLib accumulated a duplicate `XC7A50T-2FGG484I_1` in the disposable MCP test; the next save persisted it and changed the active component. Do not use it for recurring library refresh. Close/reopen only after successful save, select by exact LibReference, and compare the complete model-record key set so unexpected duplicate components are detected.
- Use the library iterator to select a component, then re-fetch `C := L.CurrentSchComponent` before editing. The library entry and editor component can differ. Avoid needlessly assigning CurrentSchComponent when the correct one is already selected.

- `OwnerPartId` is not on `ISch_BasicContainer`; declare the iterator result `ISch_Pin` for pin editing, or the correct graphical subtype. Wrong interface declarations previously caused a compiler error.
- A standalone `TLocation` variable with `Pt.X := ...` produced `Undeclared identifier X` in this installed interpreter and wedged execution. Use `Location := Point(...)`; reading `P.Location.X` worked.
- `Exit` in the bridge entrypoint skips writing `result.txt` and looks like a timeout. Use nested guards and a result/error value, as in `target_block`.
- Never invent constants (`eSheetCustom` did not exist); `Doc.UseCustomSheet := True` worked for the compiler fixture.
- `C.PartCount` reports 10 real parts; the saved header's 11 includes part 0. Do not add an extra visible part from the serialized count.
- `C.Replicate` on the active library component omitted the current part's pins (463 copied, 21 missing). Before placing compiler fixtures, enumerate the original's 484 pins and add missing replicated pins to the detached source; re-count each placed clone.
- The library pin Location was confirmed as the body-side root, with the electrical endpoint displaced by PinLength along Orientation. A fixture with wires at those calculated endpoints produced 484 matched compiled pin/nets. Do not reuse a hardcoded 200 mil wire offset after changing length to 5 mm.
- Two Altium editor processes make launcher targeting ambiguous. The bridge now refuses multiple instances. It never forcibly terminates the user's editor.
- The full packaged forward test passed, but a later additional read while switching back to the previously open disposable library caused the editor to exit before the script started. Its exact cause remains unresolved. Do not treat successful operation readback as proof of editor stability; inspect process/job state after a failure, and validate unfamiliar workflows on copies.
- GOST BOM/Library Loader were temporarily disabled during older diagnostics, with restoration documented in README. This did not prove they caused the failures; do not toggle them automatically for future library edits.

Verified outcome before packaging: 484 existing pins, 10 parts, 5 mm length, GOST Common 10 pt for both Name and Designator; native save/reload and pin identity/part/type/location comparison passed. The compiler fixture's one-pin nets have ERC warnings, so it is connectivity evidence, not a clean design.
