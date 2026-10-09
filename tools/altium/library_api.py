"""Reusable native SchLib operations. Never writes the binary CAD format.

Altium 25.8.1: verified ISch_Pin font methods, Point() coordinates,
checkpoint/backups, native save/load and invariant checks.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import uuid
from obstacle_policy import guard_action


def q(value):
    return "'" + str(value).replace("'", "''") + "'"


HELPERS = r'''
function JQ(S: WideString): String;
var K,V: Integer;
begin
  Result := '"';
  for K := 1 to Length(S) do begin
    V := Ord(S[K]);
    if (V < 32) or (V > 126) or (V = 34) or (V = 92) then
      Result := Result + '\u' + IntToHex(V,4)
    else Result := Result + S[K];
  end;
  Result := Result + '"';
end;
'''

DECL = "SD: IServerDocument; L: ISch_Lib; C,LC: ISch_Component; I,LI: ISch_Iterator; P: ISch_Pin; N, Sz, Rot: Integer; U,It,B,S: Boolean; FN: WideString;"


def target_block(path, component, content, reload=False):
    """Nested guards deliberately avoid Exit in the job entrypoint."""
    refresh = f"if not SD.Modified then begin Client.CloseDocument(SD); SD := Nil; SD := Client.OpenDocument('SCHLIB',{q(path)}); if SD <> Nil then Client.ShowDocument(SD); end else SD := Nil;" if reload else ''
    return f"""
SD := Client.GetDocumentByPath({q(path)});
if SD <> Nil then begin
  {refresh}
  L := Nil; if SD <> Nil then L := SchServer.GetSchDocumentByPath({q(path)});
  if L <> Nil then begin
    C := Nil; LI := L.SchLibIterator_Create;
    LI.AddFilter_ObjectSet(MkSet(eSchComponent)); LC := LI.FirstSchObject;
    while LC <> Nil do begin if LC.LibReference = {q(component)} then C := LC; LC := LI.NextSchObject; end;
    L.SchIterator_Destroy(LI);
    if C <> Nil then begin
      LogStep('select exact library component');
      if L.CurrentSchComponent.LibReference <> {q(component)} then L.CurrentSchComponent := C;
      C := L.CurrentSchComponent;
      if C.LibReference = {q(component)} then begin
        {content}
      end else ResultText := '{{"error":"WRONG_ACTIVE_COMPONENT"}}';
    end else ResultText := '{{"error":"COMPONENT_NOT_FOUND"}}';
  end else ResultText := '{{"error":"NO_LIBRARY"}}';
end else ResultText := '{{"error":"DOCUMENT_NOT_OPEN"}}';
"""


def snapshot_script(path, component, reload=False):
    content = """
ResultText := '{"component":'+JQ(C.LibReference)+',"part_count":'+IntToStr(C.PartCount)+',"current_part":'+IntToStr(C.CurrentPartID)+',"pins":[';
I := C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P := I.FirstSchObject; N := 0;
while P <> Nil do begin
  if N > 0 then ResultText := ResultText+',';
  ResultText := ResultText+'{"designator":'+JQ(P.Designator)+',"name":'+JQ(P.Name)+',"unique_id":'+JQ(P.UniqueId)
    +',"part":'+IntToStr(P.OwnerPartId)+',"display_mode":'+IntToStr(P.OwnerPartDisplayMode)
    +',"x_coord":'+IntToStr(P.Location.X)+',"y_coord":'+IntToStr(P.Location.Y)
    +',"orientation":'+IntToStr(P.Orientation)+',"electrical":'+IntToStr(P.Electrical)
    +',"show_name":'+LowerCase(BoolToStr(P.ShowName,True))+',"show_designator":'+LowerCase(BoolToStr(P.ShowDesignator,True))
    +',"length_coord":'+IntToStr(P.PinLength)+',"name_font_mode":'+IntToStr(P.GetState_Name_FontMode)
    +',"designator_font_mode":'+IntToStr(P.GetState_Designator_FontMode);
  SchServer.FontManager.GetFontSpec(P.GetState_Name_CustomFontID,Sz,Rot,U,It,B,S,FN);
  ResultText := ResultText+',"name_font":'+JQ(FN)+',"name_size":'+IntToStr(Sz);
  SchServer.FontManager.GetFontSpec(P.GetState_Designator_CustomFontID,Sz,Rot,U,It,B,S,FN);
  ResultText := ResultText+',"designator_font":'+JQ(FN)+',"designator_size":'+IntToStr(Sz)+'}';
  N := N+1; P := I.NextSchObject;
end; C.SchIterator_Destroy(I);
ResultText := ResultText+'],"pin_count":'+IntToStr(N)+'}';
"""
    return target_block(path, component, content, reload), DECL, HELPERS


def target_path(path):
    target = Path(path)
    if not target.is_absolute() or target.suffix.lower() != '.schlib' or not target.is_file():
        raise ValueError('An explicit absolute path to an existing .SchLib is required')
    return target.resolve()


def checked(result):
    if not result.get('success'):
        raise RuntimeError(json.dumps(result, ensure_ascii=True))
    payload = result.get('result')
    if not isinstance(payload, dict) or payload.get('error'):
        raise RuntimeError(json.dumps(result, ensure_ascii=True))
    return payload


@guard_action
def inspect_library(bridge, path, component):
    target = target_path(path)
    with bridge.operation_lock():
        opened = bridge.open_document(str(target))
        if not opened.get('success') or opened.get('result') != 'OPENED':
            return opened
        result = bridge.run_script(*snapshot_script(str(target), component))
        if isinstance(result.get('result'), dict) and result['result'].get('error'):
            result['success'] = False
        result['path'] = str(target)
        result['source'] = 'native_editor_including_unsaved_changes'
        return result


def fingerprint_models(path):
    """Read-only hashes of model streams. No binary reconstruction or writes."""
    import olefile
    import struct
    with olefile.OleFileIO(str(path)) as ole:
        result = {'/'.join(s): hashlib.sha256(ole.openstream(s).read()).hexdigest()
                  for s in ole.listdir() if any('model' in x.lower() for x in s)}
        # SchLib also embeds model/map records directly in component Data.
        for stream in ole.listdir():
            if len(stream) != 2 or stream[-1] != 'Data':
                continue
            data = ole.openstream(stream).read(); pos = 0; models = []
            while pos+4 <= len(data):
                header = struct.unpack_from('<I',data,pos)[0]
                length = header & 0xFFFFFF
                if pos+4+length > len(data):
                    raise ValueError('Truncated saved library record')
                payload = data[pos+4:pos+4+length]; pos += 4+length
                if header >> 24:
                    continue
                fields = dict(part.split('=',1) for part in payload.rstrip(b'\0').decode('latin1').split('|') if '=' in part)
                record = fields.get('RECORD',fields.get('Record',''))
                if record in {'44','45','46','47','48'}:
                    models.append({k:v for k,v in fields.items() if k.upper() not in {'OWNERINDEX','INDEXINSHEET','UNIQUEID'}})
            result['/'.join(stream)+':implementation_records'] = sorted(json.dumps(m,sort_keys=True) for m in models)
        return result


def index_pins(snapshot):
    pins = snapshot['pins']
    indexed = {p['designator']: p for p in pins}
    if not pins or len(indexed) != len(pins) or '' in indexed:
        raise ValueError('Empty or duplicate pin designators; component needs inspection')
    return indexed


def transact(bridge, path, component, builder, verify):
    target = target_path(path)
    for parent in target.parents:
        if parent.name.lower() == 'original' and (parent.parent / 'component.json').exists():
            raise ValueError('Downloaded original is immutable; edit the corresponding new library')
    report = {'success': False, 'path': str(target), 'component': component}
    # One reentrant cross-process lock covers snapshot, checkpoint, edit and readback.
    with bridge.operation_lock():
        try:
            opened = bridge.open_document(str(target))
            report['open'] = opened
            if not opened.get('success') or opened.get('result') != 'OPENED':
                return report
            before_result = bridge.run_script(*snapshot_script(str(target), component))
            report['before_job'] = before_result.get('job_dir')
            before = checked(before_result)
            index_pins(before)
            script = builder(str(target), before)  # validate the complete request before saving/editing
            report['disk_backup'] = bridge.backup_document(str(target))
            checkpoint = bridge.run_script(target_block(str(target), component,
                "if SD.DoFileSave('') then ResultText := '{\"saved\":true}' else ResultText := '{\"error\":\"CHECKPOINT_SAVE_FAILED\"}';"), DECL)
            report['checkpoint'] = checkpoint
            checked(checkpoint)
            report['editor_checkpoint_backup'] = bridge.backup_document(str(target))
            before_models = fingerprint_models(target)
            mutation = bridge.run_script(*script, timeout=30)
            report['mutation'] = mutation
            checked(mutation)
            readback = bridge.run_script(*snapshot_script(str(target), component, reload=True))
            report['readback_job'] = readback.get('job_dir')
            after = checked(readback)
            index_pins(after)
            verify(before, after)
            if before_models != fingerprint_models(target):
                raise ValueError('Model stream changed unexpectedly')
            report.update(success=True, saved_and_reloaded=True, pin_count=after['pin_count'],
                          part_count=after['part_count'], model_streams_unchanged=True,
                          sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        except Exception as exc:
            report['error'] = str(exc)
            report['recovery'] = 'Inspect jobs and current document before retrying. No automatic overwrite or rollback of editor state.'
        dest = bridge.STATE / 'library-reports' / (uuid.uuid4().hex+'.json')
        dest.parent.mkdir(parents=True, exist_ok=True)
        report['report_path'] = str(dest)
        dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def _same_except(before, after, changed):
    a, b = index_pins(before), index_pins(after)
    if a.keys() != b.keys():
        raise ValueError('Pin designators/count changed')
    for ball in a:
        # Native SchLib regenerates UniqueId on each DoFileLoad, without edits.
        ignored = set(changed) | {'unique_id'}
        if {k:v for k,v in a[ball].items() if k not in ignored} != {k:v for k,v in b[ball].items() if k not in ignored}:
            raise ValueError(f'Unexpected pin change: {ball}')


def installed_font(font):
    # GDI+ installed families avoids substitution of a misspelled Windows font.
    import subprocess
    command = 'Add-Type -AssemblyName System.Drawing; (New-Object System.Drawing.Text.InstalledFontCollection).Families.Name | ConvertTo-Json -Compress'
    proc = subprocess.run(['powershell.exe','-NoProfile','-Command',command], capture_output=True, text=True, check=True,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    names = json.loads(proc.stdout)
    if font.casefold() not in {x.casefold() for x in names}:
        raise ValueError(f'Font is not installed: {font}')
    return next(x for x in names if x.casefold() == font.casefold())


@guard_action
def format_pins(bridge, path, component, length_mm=5.0, font_name='GOST Common', font_size=10):
    length_mm = float(length_mm)
    if not math.isfinite(length_mm) or not 0 < length_mm <= 100:
        raise ValueError('Pin length must be finite and between 0 and 100 mm')
    if not isinstance(font_size, int) or isinstance(font_size, bool) or not 1 <= font_size <= 100:
        raise ValueError('Font size must be an integer from 1 to 100 pt')
    font_name = installed_font(font_name)
    coord = round(length_mm / 0.0254 * 10000)
    def builder(target, before):
        content = f"""
F := SchServer.FontManager.GetFontID({font_size},0,False,False,False,False,{q(font_name)});
LogStep('begin native pin formatting');
SchServer.ProcessControl.PreProcess(L,'');
try I := C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P := I.FirstSchObject;
while P <> Nil do begin
  P.PinLength := {coord};
  P.SetState_Name_CustomFontID(F); P.SetState_Designator_CustomFontID(F);
  P.SetState_Name_FontMode(1); P.SetState_Designator_FontMode(1);
  P := I.NextSchObject;
end; C.SchIterator_Destroy(I);
finally SchServer.ProcessControl.PostProcess(L,'Format library pins'); end;
SD.SetModified(True); L.GraphicallyInvalidate;
LogStep('save formatted library');
if SD.DoFileSave('') then ResultText := '{{"saved":true}}' else ResultText := '{{"error":"SAVE_FAILED"}}';
"""
        return target_block(target, component, content), DECL+' F: Integer;', ''
    def verify(before, after):
        changed = {'length_coord','name_font_mode','designator_font_mode','name_font','name_size','designator_font','designator_size'}
        _same_except(before, after, changed)
        if before['part_count'] != after['part_count']:
            raise ValueError('Part count changed')
        for p in after['pins']:
            if (p['length_coord'],p['name_font_mode'],p['designator_font_mode'],p['name_font'],p['name_size'],p['designator_font'],p['designator_size']) != (coord,1,1,font_name,font_size,font_name,font_size):
                raise ValueError(f'Pin format did not persist: {p["designator"]}')
    report = transact(bridge, path, component, builder, verify)
    report['requested_format'] = dict(length_mm=length_mm,font_name=font_name,font_size=font_size)
    return report


@guard_action
def repartition(bridge, path, component, manifest_path, replace_body=False):
    """Manifest defines existing pins by physical designator, not PDF aliases."""
    manifest_file = Path(manifest_path)
    if not manifest_file.is_absolute():
        raise ValueError('Manifest path must be absolute')
    data = json.loads(manifest_file.read_text(encoding='utf-8-sig'))
    if data['component'] != component:
        raise ValueError('Manifest component mismatch')
    parts = data['parts']
    if not parts or sorted(p['id'] for p in parts) != list(range(1,len(parts)+1)):
        raise ValueError('Part IDs must be unique consecutive integers starting at 1')
    expected = {}
    for part in parts:
        if not part['pins']:
            raise ValueError('Empty part')
        for pin in part['pins']:
            ball = str(pin.get('designator',pin.get('ball','')))
            if not ball or ball in expected:
                raise ValueError(f'Empty or duplicate pin: {ball}')
            for key in ['x_mils','y_mils','orientation']:
                if not isinstance(pin[key],int) or isinstance(pin[key],bool):
                    raise ValueError(f'{ball}: {key} must be integer')
            if pin['orientation'] not in range(4):
                raise ValueError(f'{ball}: invalid orientation')
            expected[ball] = dict(pin,part=part['id'])
    def builder(target, before):
        observed = index_pins(before)
        if observed.keys() != expected.keys():
            raise ValueError('Manifest must list every existing pin exactly once')
        for ball,pin in expected.items():
            if pin['name'] != observed[ball]['name']:
                raise ValueError(f'Pin name mismatch at {ball}')
        auxiliary = bridge.STATE/'library-inputs'/uuid.uuid4().hex
        auxiliary.mkdir(parents=True)
        rows = []
        for ball,pin in expected.items():
            if any(ord(c)<33 or ord(c)>126 or c=='=' for c in ball):
                raise ValueError('Manifest designators must be printable ASCII without =')
            rows.append(f"{ball}={pin['part']},{pin['x_mils']},{pin['y_mils']},{pin['orientation']}")
        mapping = auxiliary/'layout.txt'
        mapping.write_text('\n'.join(rows),encoding='ascii')
        (auxiliary/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        lines = [f"Map := TStringList.Create; V := TStringList.Create; Map.LoadFromFile({q(mapping)}); BodyOK := True;", "LogStep('layout loaded');", "SchServer.ProcessControl.PreProcess(L,'');", 'try', f'C.PartCount := {len(parts)}; C.DisplayMode := 0;',
                 'I := C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P := I.FirstSchObject;', 'while P <> Nil do begin']
        lines += ["V.CommaText := Map.Values[P.Designator]; P.OwnerPartId := StrToInt(V[0]); P.OwnerPartDisplayMode := 0; P.Location := Point(MilsToCoord(StrToInt(V[1])),MilsToCoord(StrToInt(V[2]))); P.Orientation := StrToInt(V[3]);",
                  "P := I.NextSchObject; end; C.SchIterator_Destroy(I); LogStep('pins moved');"]
        if replace_body:
            # Explicit opt-in: replaces rectangles and free labels, not parameters/models/pins.
            for kind,var in [('eRectangle','R'),('eLabel','T')]:
                lines.append(f"N := 0; repeat I := C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet({kind})); {var} := I.FirstSchObject; C.SchIterator_Destroy(I); if {var} <> Nil then begin C.RemoveSchObject({var}); L.RemoveSchObject({var}); N := N+1; end; until ({var} = Nil) or (N >= 1000); BodyOK := BodyOK and (N < 1000); LogStep('{kind} removed');")
            lines.append('if BodyOK then begin')
            for part in parts:
                xs = [p['x_mils'] for p in part['pins']]; ys = [p['y_mils'] for p in part['pins']]
                x0,x1 = min(xs),max(xs)
                if x0 == x1:
                    x0,x1 = (x0-2200,x1) if part['pins'][0]['orientation'] == 0 else (x0,x1+2200)
                y0,y1 = min(ys)-200,max(ys)+200
                lines += [f"C.CurrentPartID := {part['id']}; R := SchServer.SchObjectFactory(eRectangle,eCreate_Default);",
                          f'R.Location := Point(MilsToCoord({x0}),MilsToCoord({y0})); R.Corner := Point(MilsToCoord({x1}),MilsToCoord({y1}));',
                          f"R.OwnerPartId := {part['id']}; R.OwnerPartDisplayMode := 0; R.Color := 0; R.IsSolid := False; R.LineWidth := eSmall; C.AddSchObject(R);",
                          'T := SchServer.SchObjectFactory(eLabel,eCreate_Default);',
                          f"T.Text := {q(part.get('label',''))}; T.OwnerPartId := {part['id']}; T.OwnerPartDisplayMode := 0; T.Color := 0; T.FontId := C.Comment.FontId; T.Location := Point(MilsToCoord({x0+500}),MilsToCoord({y1-100})); C.AddSchObject(T);"]
            lines.append('end;')
        lines += ["C.CurrentPartID := 1; C.PartIdLocked := True;",
                  "finally SchServer.ProcessControl.PostProcess(L,'Repartition library component'); end;",
                  'SD.SetModified(True); L.GraphicallyInvalidate;',
                  "if BodyOK then begin if SD.DoFileSave('') then ResultText := '{\"saved\":true}' else ResultText := '{\"error\":\"SAVE_FAILED\"}'; end else ResultText := '{\"error\":\"BODY_REMOVAL_LIMIT\"}'; Map.Free; V.Free;"]
        return target_block(target,component,'\n'.join(lines)), DECL+' R: ISch_Rectangle; T: ISch_Label; Map,V: TStringList; BodyOK: Boolean;', ''
    def verify(before, after):
        _same_except(before,after,{'part','display_mode','x_coord','y_coord','orientation'})
        if after['part_count'] != len(parts):
            raise ValueError('Part count mismatch after reload')
        for ball,pin in index_pins(after).items():
            e = expected[ball]
            if (pin['part'],pin['x_coord'],pin['y_coord'],pin['orientation'],pin['display_mode']) != (e['part'],e['x_mils']*10000,e['y_mils']*10000,e['orientation'],0):
                raise ValueError(f'Layout mismatch at {ball}')
    return transact(bridge,path,component,builder,verify)
