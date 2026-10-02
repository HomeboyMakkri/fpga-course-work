"""Deterministic native Altium sheets from explicit, reviewable pin-net data."""
from __future__ import annotations

import json
import re


def q(value):
    return "'" + str(value).replace("'", "''") + "'"


def point(x, y):
    return f"Point(MilsToCoord({int(x)}), MilsToCoord({int(y)}))"


HELPERS = r'''
procedure WireToLabel(Doc: ISch_Document; X, Y, DX: Integer; NetName: String);
var W: ISch_Wire; N: ISch_NetLabel;
begin
  W := SchServer.SchObjectFactory(eWire, eCreate_Default);
  W.InsertVertex := 1; W.SetState_Vertex(1, Point(MilsToCoord(X), MilsToCoord(Y)));
  W.InsertVertex := 2; W.SetState_Vertex(2, Point(MilsToCoord(X+DX), MilsToCoord(Y)));
  Doc.RegisterSchObjectInContainer(W);
  N := SchServer.SchObjectFactory(eNetLabel, eCreate_Default);
  N.Text := NetName;
  N.Location := Point(MilsToCoord(X+DX), MilsToCoord(Y));
  Doc.RegisterSchObjectInContainer(N);
end;
procedure AddNote(Doc: ISch_Document; X, Y: Integer; S: String);
var L: ISch_Label;
begin
  L := SchServer.SchObjectFactory(eLabel, eCreate_Default);
  L.Text := S; L.Location := Point(MilsToCoord(X), MilsToCoord(Y));
  Doc.RegisterSchObjectInContainer(L);
end;
'''


def validate(data):
    used = set()
    for comp in data["components"]:
        ref = comp["ref"]
        if not re.fullmatch(r"[A-Za-z]+\d+", ref) or ref in used:
            raise ValueError(f"Invalid or duplicate component designator: {ref}")
        used.add(ref)
        pin_nums = [str(p["number"]) for p in comp["pins"]]
        if len(pin_nums) != len(set(pin_nums)):
            raise ValueError(f"Duplicate pin number in {ref}")
        for pin in comp["pins"]:
            if pin.get("net") and not re.fullmatch(r"[\w+./#-]+", pin["net"]):
                raise ValueError(f"Unexpected net name: {pin['net']}")


def build_sheet(data, path):
    validate(data)
    decl = "SD: IServerDocument; Doc: ISch_Document; C: ISch_Component; P: ISch_Pin; R: ISch_Rectangle; Param: ISch_Parameter;"
    lines = [
        "LogStep('create native SCH document');",
        f"SD := Client.OpenNewDocument('SCH', {q(path)}, {q(path.split(chr(92))[-1])}, False);",
        "if SD = Nil then Exit;",
        "LogStep('set document path');",
        f"SD.SetFileName({q(path)}); Client.ShowDocument(SD);",
        "LogStep('get SCH API document');",
        f"Doc := SchServer.GetSchDocumentByPath({q(path)});",
        "if Doc = Nil then Exit;",
        "Doc.SnapGridSize := MilsToCoord(5); Doc.VisibleGridSize := MilsToCoord(100);",
        "LogStep('begin SCH transaction');",
        "SchServer.ProcessControl.PreProcess(Doc, '');",
        "try",
        f"AddNote(Doc, 300, 7200, {q(data['title'])});",
        f"AddNote(Doc, 300, 7000, {q(data.get('note','PDF reconstruction draft - review connectivity and footprints'))});",
    ]
    for index, comp in enumerate(data["components"]):
        x = int(comp.get("x", 1600 + (index % 3) * 2400))
        y = int(comp.get("y", 6000 - (index // 3) * 1500))
        left = [p for p in comp["pins"] if p.get("side", "left") == "left"]
        right = [p for p in comp["pins"] if p.get("side", "left") == "right"]
        width = int(comp.get("width", 600))
        height = max(250, max(len(left), len(right)) * 120)
        lines += [f"LogStep({q('place ' + comp['ref'])});",
                  "C := SchServer.SchObjectFactory(eSchComponent, eCreate_Default);",
                  "C.CurrentPartID := 1; C.DisplayMode := 0; C.PartCount := 1;",
                  f"C.LibReference := {q(comp.get('symbol',comp['value']))};",
                  f"C.ComponentDescription := {q(comp.get('description','Reconstructed from Smart Artix reference PDF'))};",
                  f"C.Designator.Text := {q(comp['ref'])}; C.Comment.Text := {q(comp['value'])};",
                  f"C.Location := {point(x,y)};",
                  "R := SchServer.SchObjectFactory(eRectangle, eCreate_Default);",
                  f"R.Location := {point(x-width//2,y-height)}; R.Corner := {point(x+width//2,y)};",
                  "R.OwnerPartId := 1; R.OwnerPartDisplayMode := 0; R.IsSolid := False; C.AddSchObject(R);",
                  f"C.Designator.Location := {point(x-width//2,y+120)};",
                  f"C.Comment.Location := {point(x-width//2,y+240)};",
                  "Param := SchServer.SchObjectFactory(eParameter, eCreate_Default);",
                  "Param.Name := 'Source';",
                  f"Param.Text := {q(data.get('source','Schematic_Smart_Artix_251120.pdf'))}; Param.IsHidden := True; C.AddSchObject(Param);",
                  "Param := SchServer.SchObjectFactory(eParameter, eCreate_Default);",
                  "Param.Name := 'ReviewStatus'; Param.Text := 'DRAFT - pin/net verification required; footprint not assigned'; Param.IsHidden := True; C.AddSchObject(Param);"]
        pin_geometry = []
        for side, pin_group in [("left", left), ("right", right)]:
            for pin_index, pin in enumerate(pin_group):
                # Altium Pin.Location is the body-side end. The connection
                # point is PinLength further along its orientation.
                px = -width//2 if side == "left" else width//2
                py = -120 * (pin_index+1)
                orient = "eRotate180" if side == "left" else "eRotate0"
                electrical = pin.get("electrical","passive")
                elec = {"input":"eElectricInput","output":"eElectricOutput","io":"eElectricIO","power":"eElectricPower","passive":"eElectricPassive"}[electrical]
                lines += ["P := SchServer.SchObjectFactory(ePin, eCreate_Default);",
                          f"P.Name := {q(pin.get('name',pin['number']))}; P.Designator := {q(pin['number'])};",
                          f"P.Location := {point(x+px,y+py)}; P.PinLength := MilsToCoord(200); P.Orientation := {orient};",
                          f"P.Electrical := {elec}; P.ShowName := True; P.ShowDesignator := True;",
                          "P.OwnerPartId := 1; P.OwnerPartDisplayMode := 0; C.AddSchObject(P);"]
                hotx = x+px+(-200 if side == "left" else 200)
                hoty = y+py
                pin_geometry.append((pin, hotx, hoty, -300 if side == "left" else 300))
        lines += ["Doc.RegisterSchObjectInContainer(C);"]
        for pin, hx, hy, dx in pin_geometry:
            if pin.get("net"):
                lines.append(f"WireToLabel(Doc, {hx}, {hy}, {dx}, {q(pin['net'])});")
    lines += ["finally SchServer.ProcessControl.PostProcess(Doc, ''); end;",
              "Doc.GraphicallyInvalidate;",
              "LogStep('save native SCH document');",
              "SD.SetModified(True); SD.DoFileSave('');",
              f"ResultText := {q(json.dumps({'created':path,'components':len(data['components']),'pins':sum(len(c['pins']) for c in data['components'])}))};"]
    return "\n".join(lines), decl, HELPERS


def inspect_body(path):
    declarations = "SD: IServerDocument; Doc: ISch_Document; It, PI: ISch_Iterator; O: ISch_GraphicalObject; C: ISch_Component; P: ISch_Pin; N: ISch_NetLabel; W: ISch_Wire; L: TStringList; Count: Integer;"
    helpers = r'''
function J(S: String): String;
begin
  S := StringReplace(S, '\', '\\', 1);
  S := StringReplace(S, '"', '\"', 1);
  Result := '"' + S + '"';
end;
'''
    body = f"""
LogStep('open target for inspection');
SD := Client.OpenDocument('SCH', {q(path)}); if SD = Nil then Exit;
Client.ShowDocument(SD); Doc := SchServer.GetSchDocumentByPath({q(path)});
if Doc = Nil then Exit;
L := TStringList.Create; L.Add('{{"components":['); Count := 0;
It := Doc.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eSchComponent));
C := It.FirstSchObject;
while C <> Nil do begin
  if Count > 0 then L.Add(','); Count := Count + 1;
  L.Add('{{"ref":'+J(C.Designator.Text)+',"value":'+J(C.Comment.Text)+',"x":'+IntToStr(CoordToMils(C.Location.X))+',"y":'+IntToStr(CoordToMils(C.Location.Y))+',"pins":[');
  PI := C.SchIterator_Create; PI.AddFilter_ObjectSet(MkSet(ePin)); P := PI.FirstSchObject;
  while P <> Nil do begin
    L.Add('{{"number":'+J(P.Designator)+',"name":'+J(P.Name)+',"x":'+IntToStr(CoordToMils(P.Location.X))+',"y":'+IntToStr(CoordToMils(P.Location.Y))+',"orientation":'+IntToStr(P.Orientation)+',"length":'+IntToStr(CoordToMils(P.PinLength))+'}}');
    P := PI.NextSchObject; if P <> Nil then L.Add(',');
  end;
  C.SchIterator_Destroy(PI); L.Add(']}}'); C := It.NextSchObject;
end;
Doc.SchIterator_Destroy(It); L.Add('],"net_labels":[');
It := Doc.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eNetLabel)); N := It.FirstSchObject;
while N <> Nil do begin
  L.Add('{{"net":'+J(N.Text)+',"x":'+IntToStr(CoordToMils(N.Location.X))+',"y":'+IntToStr(CoordToMils(N.Location.Y))+'}}');
  N := It.NextSchObject; if N <> Nil then L.Add(',');
end;
Doc.SchIterator_Destroy(It); L.Add('],"wires":[');
It := Doc.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eWire)); W := It.FirstSchObject;
while W <> Nil do begin
  L.Add('{{"x1":'+IntToStr(CoordToMils(W.GetState_Vertex(1).X))+',"y1":'+IntToStr(CoordToMils(W.GetState_Vertex(1).Y))+',"x2":'+IntToStr(CoordToMils(W.GetState_Vertex(2).X))+',"y2":'+IntToStr(CoordToMils(W.GetState_Vertex(2).Y))+'}}');
  W := It.NextSchObject; if W <> Nil then L.Add(',');
end;
Doc.SchIterator_Destroy(It); L.Add(']}}'); ResultText := L.Text; L.Free;
LogStep('inspection complete');
"""
    return body, declarations, helpers


def parameter_body(path, designator, parameter, value):
    decl = "SD: IServerDocument; Doc: ISch_Document; It: ISch_Iterator; C: ISch_Component; P: ISch_Parameter;"
    body = f"""
SD := Client.OpenDocument('SCH', {q(path)}); if SD = Nil then Exit;
Client.ShowDocument(SD); Doc := SchServer.GetSchDocumentByPath({q(path)});
if Doc = Nil then Exit;
It := Doc.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eSchComponent)); C := It.FirstSchObject;
while C <> Nil do begin
  if C.Designator.Text = {q(designator)} then begin
    LogStep('component located'); SchServer.ProcessControl.PreProcess(Doc, '');
    try
      if {q(parameter)} = 'Comment' then C.Comment.Text := {q(value)}
      else begin
        P := C.GetState_SchParameterByName({q(parameter)});
        if P = Nil then begin
          P := SchServer.SchObjectFactory(eParameter, eCreate_Default);
          P.Name := {q(parameter)}; P.IsHidden := True; C.AddSchObject(P);
        end;
        P.Text := {q(value)};
      end;
    finally SchServer.ProcessControl.PostProcess(Doc, ''); end;
    SD.SetModified(True); SD.DoFileSave(''); Doc.GraphicallyInvalidate;
    ResultText := 'UPDATED'; break;
  end;
  C := It.NextSchObject;
end;
Doc.SchIterator_Destroy(It);
if ResultText = '' then ResultText := 'COMPONENT_NOT_FOUND';
"""
    return body, decl, ""
