# XC7A50T library divided into parts A-J

The user's library was edited and saved through Altium's native API:

`C:\Users\makarlistkov\Documents\Work\Engineering\FPGA-COURSE-WORK\ARTIX\ARTIX\libraries\X7\XC7A50T-2FGG484I.SchLib`

`XC7A50T-2FGG484I.SchLib` in this folder is a copy of that saved result.
`XC7A50T-before-split.SchLib` is the backup taken after the user's restart, before editing.

| Part | Block | Pins | Source PDF page |
| --- | --- | ---: | ---: |
| A | Configuration, XADC, JTAG | 21 | 2 |
| B | Bank 14 | 50 | 2 |
| C | Bank 15 | 50 | 2 |
| D | Bank 16 | 50 | 2 |
| E | Bank 34 | 50 | 3 |
| F | Bank 35 | 50 | 2 |
| G | MGT bank 216 | 32 | 2 |
| H | GND | 87 | 8 |
| I | Power | 59 | 8 |
| J | NC | 35 | 2 |

Source: `Schematic_Smart_Artix_251120.pdf`. Physical BGA ball identifiers, pin names and electrical types were preserved. Some repeated GND/power/NC aliases have different numeric suffixes in the PDF. These were matched by physical ball and original library names were retained. `XC7A50T-pin-map.csv` records both names, side and vertical order.

After saving and native reloading, all 484 pins matched the layout manifest by ball, name, part, position, orientation and electrical type. The shared footprint model remains `BGA484C100P22X22_2300X2300X260`.

`FPGA_Library_Check_Complete.PrjPcb` is an isolated connectivity fixture, not a generator design. The native project compiler reported 484 unique physical pin/net matches, all with the expected `VERIFY_<ball>` net. `compiler-check.json` contains the compiler result. Compilation reports errors because those fixture nets deliberately contain one pin; this is not a clean ERC result for an actual circuit. `FPGA_Library_Check.PrjPcb` without `_Complete` is an earlier incomplete diagnostic fixture.

Altium scripting details found during this work:

- Use `ISch_Pin` / `ISch_GraphicalObject` to access OwnerPartId, not ISch_BasicContainer.
- In this DelphiScript runtime use `Point(X, Y)` for assignments to Location and Corner. Field assignment to a standalone TLocation variable caused an undeclared-identifier error.
- Replicate of an active library component omitted the current part's pins. An isolated snapshot supplemented those missing pins before placing the verification fixture. All final library pins were checked independently after save/reload.
- The editor closed repeatedly during this session. The saved library and backup remain available; a successful script invocation alone was not treated as verification.

Final library after pin formatting: all 484 pins are 5 mm; Name and Designator use GOST Common 10 pt. SHA256: `24eac977e2736357616f97e7a85e55cf54aa2682d7ff6ee8de8eec6363d70425`.

`library-workflow-mcp-test.json` records the packaged multipart/formatting forward test. `repository-mcp-test.json` records the subsequent launch test from this repository's root and a subdirectory. Older reports contain historical job paths; executable tools now resolve all paths from this repository.
