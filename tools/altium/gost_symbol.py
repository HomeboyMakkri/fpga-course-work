"""Reproducible rectangular GOST-style symbols via native Altium requests.

This CLI writes manifests, backups and JSON requests, never CAD binary data.
Execute emitted requests sequentially with altium_local MCP, then verify.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import uuid

from library_api import q, target_block, snapshot_script, DECL, HELPERS, fingerprint_models
from job_diagnostics import preflight

ROOT = Path(__file__).resolve().parents[2]
STEP_MM = 0.0254 / 10000
ELECTRICAL = ['eElectricInput','eElectricIO','eElectricOutput','eElectricOpenCollector',
              'eElectricPassive','eElectricHiZ','eElectricOpenEmitter','eElectricPower']

def coord(mm):
    return round(mm / STEP_MM)

def number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
        raise ValueError(f'{label}: finite number required')
    if abs(value) > 1000 or (positive and value <= 0):
        raise ValueError(f'{label}: outside supported dimensions')
    return float(value)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def payload(value):
    if 'content' in value:
        if value.get('isError'): raise ValueError('MCP returned an error')
        value=json.loads(next(c['text'] for c in value['content'] if c['type']=='text'))
    if not value.get('success') or not isinstance(value.get('result'),dict) or value['result'].get('error'):
        raise ValueError('A successful native result is required')
    return value['result']

def absolute(path, suffix=None, exists=False):
    p=Path(path)
    if not p.is_absolute(): raise ValueError('Use an explicit absolute path')
    p=p.resolve()
    if suffix and p.suffix.lower()!=suffix: raise ValueError(f'Expected {suffix}: {p}')
    if exists and not p.is_file(): raise ValueError(f'Missing file: {p}')
    return p

def normalize(data, mode, before=None):
    """Validate identity/completeness before producing any CAD request."""
    component=data['component']
    if not isinstance(component,str) or not component.strip(): raise ValueError('Exact component required')
    policy=data.get('electrical_policy','preserve')
    if policy not in {'preserve','pins','power'}: raise ValueError('Unknown electrical policy')
    if mode=='create' and policy=='preserve': raise ValueError('Creation requires pins or explicit power policy')
    original={}
    if mode=='redraw':
        if before is None or before['component']!=component: raise ValueError('Exact before-native snapshot required')
        original={str(p['designator']):p for p in before['pins']}
        if not original or len(original)!=len(before['pins']): raise ValueError('Duplicate/empty original pins')
    length=number(data.get('pin_length_mm',5),'pin_length_mm',True)
    if abs(length-round(length))>1e-9: raise ValueError('Pin length must be whole mm for 1mm endpoints')
    font=data.get('font_name','GOST Common'); size=data.get('font_size_pt',10)
    if not isinstance(font,str) or not font: raise ValueError('Font name required')
    if not isinstance(size,int) or isinstance(size,bool) or not 4<=size<=30: raise ValueError('Font size must be 4..30 pt')
    parts=data['parts']
    if not parts or [p['id'] for p in parts]!=list(range(1,len(parts)+1)):
        raise ValueError('Parts must be consecutive from 1')
    result={'component':component,'mode':mode,'electrical_policy':policy,'pin_length_mm':length,
            'font_name':font,'font_size_pt':size,'parts':[],'pins':[],
            'designator':data.get('designator','DA?'),'comment':data.get('comment',component),
            'description':data.get('description',component),'parameters':data.get('parameters',{}),
            'source':data.get('source','')}
    if mode=='create' and not result['source']: raise ValueError('Record manufacturer/source evidence for creation')
    seen=set(); folded=set()
    for part in parts:
        widths=part.get('column_widths_mm',[12,11,12])
        if len(widths)!=3: raise ValueError('Three column widths required')
        widths=[number(x,'column width',True) for x in widths]
        if any(abs(x-round(x))>1e-9 for x in widths): raise ValueError('Column boundaries must be on 1mm grid')
        pitch=number(part.get('pitch_mm',6),'pitch_mm',True)
        first=number(part.get('row_start_mm',6),'row_start_mm',True)
        if abs(pitch-round(pitch))>1e-9 or abs(first-round(first))>1e-9 or pitch<4:
            raise ValueError('Whole-mm pitch >=4 and row start required')
        pins=part['pins']
        if not pins: raise ValueError('Empty part')
        rows={'left':0,'right':0}; width=sum(widths); normalized=[]
        for pin in pins:
            designator=str(pin['designator']); name=pin['name']; side=pin['side']
            if side not in rows: raise ValueError('Supported pin sides are left/right')
            if not designator or designator in seen or designator.casefold() in folded:
                raise ValueError('Duplicate/empty physical pin designator')
            if any(ord(c)<33 or ord(c)>126 or c in '=,' for c in designator):
                raise ValueError('Physical designator must be ASCII without comma/= or spaces')
            if not isinstance(name,str) or not name: raise ValueError('Pin name required')
            seen.add(designator); folded.add(designator.casefold())
            if original and (designator not in original or name!=original[designator]['name']):
                raise ValueError(f'Physical identity/name mismatch: {designator}')
            electrical=7 if policy=='power' else original[designator]['electrical'] if policy=='preserve' else pin['electrical']
            if not isinstance(electrical,int) or isinstance(electrical,bool) or electrical not in range(8):
                raise ValueError('Electrical type must be 0..7')
            y=-first-pitch*rows[side]; rows[side]+=1
            n={'designator':designator,'name':name,'part':part['id'],'x_mm':0 if side=='left' else width,
               'y_mm':y,'orientation':2 if side=='left' else 0,'electrical':electrical}
            normalized.append(n); result['pins'].append(n)
        height=first+pitch*(max(rows.values())-1)+6
        if any(abs(coord(x))>2_147_480_000 for x in [width+length,height,length]):
            raise ValueError('Layout exceeds Altium signed internal coordinate range')
        function=part.get('function','')
        if not isinstance(function,str): raise ValueError('Function label must be text')
        label_y=number(part.get('label_y_mm',-3),'label_y_mm')
        if abs(label_y*2-round(label_y*2))>1e-9 or not -first<label_y<0:
            raise ValueError('Function label needs a 0.5mm-grid anchor above first pin')
        result['parts'].append({'id':part['id'],'function':function,'width_mm':width,'height_mm':height,
            'dividers_mm':[widths[0],widths[0]+widths[1]],'label_mm':[widths[0]+widths[1]/2,label_y],'pins':normalized})
    if original and seen!=original.keys(): raise ValueError('Manifest must include every original pin exactly once')
    return result

def extra_readback(path, component):
    content="""
ResultText:=Copy(ResultText,1,Length(ResultText)-1)+',"graphics":['; N:=0;
I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eRectangle)); R:=I.FirstSchObject;
while R<>Nil do begin if N>0 then ResultText:=ResultText+',';
ResultText:=ResultText+'{"kind":"rectangle","part":'+IntToStr(R.OwnerPartId)+',"color":'+IntToStr(R.Color)+',"x":'+IntToStr(R.Location.X)+',"y":'+IntToStr(R.Location.Y)+',"cx":'+IntToStr(R.Corner.X)+',"cy":'+IntToStr(R.Corner.Y)+'}'; N:=N+1; R:=I.NextSchObject; end; C.SchIterator_Destroy(I);
I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eLine)); G:=I.FirstSchObject;
while G<>Nil do begin if N>0 then ResultText:=ResultText+',';
ResultText:=ResultText+'{"kind":"line","part":'+IntToStr(G.OwnerPartId)+',"color":'+IntToStr(G.Color)+',"x":'+IntToStr(G.Location.X)+',"y":'+IntToStr(G.Location.Y)+',"cx":'+IntToStr(G.Corner.X)+',"cy":'+IntToStr(G.Corner.Y)+'}'; N:=N+1; G:=I.NextSchObject; end; C.SchIterator_Destroy(I);
I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eLabel)); T:=I.FirstSchObject;
while T<>Nil do begin if N>0 then ResultText:=ResultText+',';
SchServer.FontManager.GetFontSpec(T.FontId,Sz,Rot,U,It,B,S,FN);
ResultText:=ResultText+'{"kind":"label","part":'+IntToStr(T.OwnerPartId)+',"color":'+IntToStr(T.Color)+',"text":'+JQ(T.Text)+',"x":'+IntToStr(T.Location.X)+',"y":'+IntToStr(T.Location.Y)+',"font":'+JQ(FN)+',"size":'+IntToStr(Sz)+'}'; N:=N+1; T:=I.NextSchObject; end; C.SchIterator_Destroy(I);
ResultText:=ResultText+'],"pin_colors":['; N:=0; I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject;
while P<>Nil do begin if N>0 then ResultText:=ResultText+','; ResultText:=ResultText+'{"designator":'+JQ(P.Designator)+',"color":'+IntToStr(P.Color)+'}'; N:=N+1; P:=I.NextSchObject; end; C.SchIterator_Destroy(I);
ResultText:=ResultText+'],"designator_color":'+IntToStr(C.Designator.Color)+',"comment_color":'+IntToStr(C.Comment.Color)+',"models":['; N:=0;
I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eImplementation)); IM:=I.FirstSchObject;
while IM<>Nil do begin if N>0 then ResultText:=ResultText+','; ResultText:=ResultText+'{"name":'+JQ(IM.ModelName)+',"type":'+JQ(IM.ModelType)+',"map":'+JQ(IM.MapAsString)+',"links":[';
for K:=0 to IM.DatafileLinkCount-1 do begin if K>0 then ResultText:=ResultText+','; DL:=IM.DatafileLink[K]; ResultText:=ResultText+'{"location":'+JQ(DL.Location)+',"entity":'+JQ(DL.EntityName)+'}'; end;
ResultText:=ResultText+']}'; N:=N+1; IM:=I.NextSchObject; end; C.SchIterator_Destroy(I);
ResultText:=ResultText+'],"snap_grid_coord":'+IntToStr(L.SnapGridSize)+',"visible_grid_coord":'+IntToStr(L.VisibleGridSize)+'}';
"""
    return target_block(str(path),component,content)

EXT_DECL=' R:ISch_Rectangle; G:ISch_Line; T:ISch_Label; A:ISch_Parameter; IM:ISch_Implementation; DL:ISch_ModelDatafileLink; K:Integer;'

def readback_request(path, component):
    body,decl,helpers=snapshot_script(str(path),component,reload=True)
    return {'body':body+extra_readback(path,component),'declarations':decl+EXT_DECL,'helpers':helpers,'timeout':30}

def artwork(layout):
    lines=[]
    for part in layout['parts']:
        pid=part['id']; w=coord(part['width_mm']); h=coord(-part['height_mm'])
        lines += [f'C.CurrentPartID:={pid}; R:=SchServer.SchObjectFactory(eRectangle,eCreate_Default);',
            f'R.OwnerPartId:={pid}; R.OwnerPartDisplayMode:=0; R.Location:=Point(0,{h}); R.Corner:=Point({w},0); R.Color:=0; R.IsSolid:=False; R.LineWidth:=eSmall; C.AddSchObject(R);']
        for x in part['dividers_mm']:
            lines += ['G:=SchServer.SchObjectFactory(eLine,eCreate_Default);',f'G.OwnerPartId:={pid}; G.OwnerPartDisplayMode:=0; G.Location:=Point({coord(x)},0); G.Corner:=Point({coord(x)},{h}); G.Color:=0; G.LineWidth:=eSmall; C.AddSchObject(G);']
        tx,ty=part['label_mm']
        lines += ['T:=SchServer.SchObjectFactory(eLabel,eCreate_Default);',f'T.OwnerPartId:={pid}; T.OwnerPartDisplayMode:=0; T.Text:={q(part["function"])}; T.FontId:=F; T.Color:=0; T.Justification:=eJustify_Center; T.Location:=Point({coord(tx)},{coord(ty)}); C.AddSchObject(T);']
    return lines

def mutation_request(layout,path,mapping,pcblib=None,footprint=None):
    create=layout['mode']=='create'
    lines=[f"F:=SchServer.FontManager.GetFontID({layout['font_size_pt']},0,False,False,False,False,{q(layout['font_name'])});",
        f'L.DisplayUnit:=eMM; L.SnapGridOn:=True; L.SnapGridSize:={coord(1)}; L.VisibleGridOn:=True; L.VisibleGridSize:={coord(.5)}; L.HotSpotGridSize:={coord(.5)}; L.SystemFont:=F;',
        "LogStep('apply rectangular GOST layout'); SchServer.ProcessControl.PreProcess(L,''); try",
        f"C.PartCount:={len(layout['parts'])}; C.DisplayMode:=0; C.OverideColors:=False; C.PinColor:=0; BodyOK:=True;"]
    if create:
        for p in layout['pins']:
            lines += ['P:=SchServer.SchObjectFactory(ePin,eCreate_Default);',f"P.Name:={q(p['name'])}; P.Designator:={q(p['designator'])}; C.AddSchObject(P);"]
    else:
        lines += ["N:=0; repeat I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eRectangle,eLine,ePolyLine,eLabel)); O:=I.FirstSchObject; C.SchIterator_Destroy(I); if O<>Nil then begin C.RemoveSchObject(O); L.RemoveSchObject(O); N:=N+1; end; until (O=Nil) or (N>=1000); BodyOK:=N<1000;"]
    lines += [f'Map:=TStringList.Create; V:=TStringList.Create; Map.LoadFromFile({q(mapping)});',
        'I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject;',
        'while P<>Nil do begin V.CommaText:=Map.Values[P.Designator]; P.OwnerPartId:=StrToInt(V[0]); P.OwnerPartDisplayMode:=0; P.Location:=Point(StrToInt(V[1]),StrToInt(V[2])); P.Orientation:=StrToInt(V[3]);',
        f'P.PinLength:={coord(layout["pin_length_mm"])}; P.Color:=0; P.ShowName:=True; P.ShowDesignator:=True; P.SetState_Name_CustomFontID(F); P.SetState_Designator_CustomFontID(F); P.SetState_Name_FontMode(1); P.SetState_Designator_FontMode(1);',
        'case StrToInt(V[4]) of']
    lines += [f'{i}: P.Electrical:={enum};' for i,enum in enumerate(ELECTRICAL)]
    lines += ['end; P:=I.NextSchObject; end; C.SchIterator_Destroy(I); Map.Free; V.Free;', 'if BodyOK then begin']+artwork(layout)+['end;']
    if create:
        for name,value in layout['parameters'].items():
            lines += ['A:=SchServer.SchObjectFactory(eParameter,eCreate_Default);',f'A.Name:={q(name)}; A.Text:={q(value)}; A.IsHidden:=True; A.FontId:=F; A.Color:=0; A.Location:=Point(0,0); C.AddSchObject(A);']
        import os
        location=os.path.relpath(pcblib,path.parent)
        identity=','.join(f'({p["designator"]}:{p["designator"]})' for p in layout['pins'])
        lines += ["LogStep('bind provided footprint'); IM:=C.AddSchImplementation;",f'IM.ModelName:={q(footprint)}; IM.ModelType:=\'PCBLIB\'; IM.IsCurrent:=True; IM.MapAsString:={q(identity)}; IM.AddDataFileLink({q(footprint)},{q(location)},\'PCBLIB\');',
            f'C.Designator.Text:={q(layout["designator"])}; C.Comment.Text:={q(layout["comment"])}; C.Designator.IsHidden:=False; C.Comment.IsHidden:=False;']
    lines += ['I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eParameter)); A:=I.FirstSchObject; while A<>Nil do begin A.Color:=0; A.FontId:=F; A:=I.NextSchObject; end; C.SchIterator_Destroy(I);',
        'I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eDesignator)); A:=I.FirstSchObject; while A<>Nil do begin A.Color:=0; A.FontId:=F; A.Location:=Point(0,1968504); A:=I.NextSchObject; end; C.SchIterator_Destroy(I);',
        f'C.Designator.FontId:=F; C.Comment.FontId:=F; C.Designator.Color:=0; C.Comment.Color:=0; C.Designator.Location:=Point(0,{coord(5)}); C.Comment.Location:=Point({coord(10)},{coord(5)}); C.CurrentPartID:=1; C.PartIdLocked:=True;',
        "finally SchServer.ProcessControl.PostProcess(L,'GOST symbol'); end; L.GraphicallyInvalidate; SD.SetModified(True); LogStep('save GOST symbol');",
        "if BodyOK then begin if SD.DoFileSave('') then ResultText:='{\"saved\":true}' else ResultText:='{\"error\":\"SAVE_FAILED\"}'; end else ResultText:='{\"error\":\"BODY_REMOVAL_LIMIT\"}';"]
    decl=DECL+EXT_DECL+' F:Integer; Map,V:TStringList; O:ISch_GraphicalObject; BodyOK:Boolean;'
    if create:
        body=f"if not FileExists({q(path)}) then begin LogStep('create new explicit SchLib'); SD:=Client.OpenNewDocument('SCHLIB',{q(path)},{q(path.name)},False); if SD<>Nil then begin SD.SetFileName({q(path)}); Client.ShowDocument(SD); L:=SchServer.GetSchDocumentByPath({q(path)}); if L<>Nil then begin C:=L.CurrentSchComponent; if C=Nil then begin C:=SchServer.SchObjectFactory(eSchComponent,eCreate_Default); L.AddSchComponent(C); L.CurrentSchComponent:=C; end; C:=L.CurrentSchComponent; C.LibReference:={q(layout['component'])}; C.ComponentDescription:={q(layout['description'])};"+'\n'.join(lines)+" end else ResultText:='{\"error\":\"NO_LIBRARY\"}'; end else ResultText:='{\"error\":\"CREATE_FAILED\"}'; end else ResultText:='{\"error\":\"TARGET_EXISTS\"}';"
    else:
        gate=mapping.parent/'before-editor-checkpoint.SchLib'
        guarded=f"if FileExists({q(gate)}) then begin if not SD.Modified then begin "+'\n'.join(lines)+" end else ResultText:='{\"error\":\"TARGET_MODIFIED_AFTER_CHECKPOINT\"}'; end else ResultText:='{\"error\":\"CHECKPOINT_REQUIRED\"}';"
        body=target_block(str(path),layout['component'],guarded)
    return {'body':body,'declarations':decl,'helpers':'','timeout':30}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def others(path,component):
    """Saved non-target component streams; read-only OLE access."""
    import olefile
    result={}
    with olefile.OleFileIO(str(path)) as ole:
        for stream in ole.listdir():
            if len(stream)!=2 or stream[-1]!='Data': continue
            raw=ole.openstream(stream).read()
            if len(raw)<4: continue
            size=struct.unpack_from('<I',raw)[0]&0xffffff
            fields=dict(x.split('=',1) for x in raw[4:4+size].rstrip(b'\0').decode('latin1').split('|') if '=' in x)
            ref=next((v for k,v in fields.items() if k.upper()=='LIBREFERENCE'),None)
            if ref and ref!=component:
                for entry in ole.listdir():
                    if entry[0]==stream[0]: result['/'.join(entry)]=hashlib.sha256(ole.openstream(entry).read()).hexdigest()
    return result

def write_json(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def prepare(mode,manifest,path,out,before=None,pcblib=None,footprint=None):
    path=absolute(path,'.schlib',exists=mode=='redraw'); out=absolute(out)
    if 'original' in [p.lower() for p in path.parts]: raise ValueError('Use a working copy outside original')
    if mode=='create' and path.exists(): raise FileExistsError(path)
    data=load(absolute(manifest,exists=True)); native=payload(load(before)) if before else None
    layout=normalize(data,mode,native)
    if mode=='create':
        pcblib=absolute(pcblib,'.pcblib',exists=True)
        if not footprint: raise ValueError('Exact existing footprint name required')
        import olefile
        with olefile.OleFileIO(str(pcblib)) as ole:
            if not ole.exists([footprint,'Data']): raise ValueError('Footprint not found in saved PcbLib')
    elif pcblib: pcblib=absolute(pcblib,'.pcblib',exists=True)
    if out.exists(): raise FileExistsError('Use a fresh bundle directory')
    out.mkdir(parents=True); path.parent.mkdir(parents=True,exist_ok=True)
    mapping=out/'layout-internal.txt'
    mapping.write_text('\n'.join(f"{p['designator']}={p['part']},{coord(p['x_mm'])},{coord(p['y_mm'])},{p['orientation']},{p['electrical']}" for p in layout['pins']),encoding='ascii')
    mutation=mutation_request(layout,path,mapping,pcblib,footprint)
    readback=readback_request(path,layout['component'])
    for req in [mutation,readback]:
        if preflight(req['body'],req['declarations'],req['helpers']): raise ValueError('Native preflight rejected generated request')
    state={'path':str(path),'pcblib':str(pcblib) if pcblib else None,'footprint':footprint,'layout':layout,
           'before':native,'checkpoint_captured':mode=='create','pcblib_sha256':sha(pcblib) if pcblib else None}
    if mode=='redraw':
        shutil.copy2(path,out/'before-disk.SchLib')
        checkpoint={'body':target_block(str(path),layout['component'],"LogStep('save editor checkpoint'); if SD.DoFileSave('') then ResultText:='{\"saved\":true}' else ResultText:='{\"error\":\"CHECKPOINT_FAILED\"}';"),'declarations':DECL,'helpers':'','timeout':15}
        write_json(out/'checkpoint.json',checkpoint)
    write_json(out/'state.json',state); write_json(out/'normalized-mm.json',layout)
    write_json(out/'mutation.json',mutation); write_json(out/'readback.json',readback)
    return {'bundle':str(out),'mode':mode,'pins':len(layout['pins']),'parts':len(layout['parts']),
            'requests':[str(out/x) for x in (['checkpoint.json'] if mode=='redraw' else [])+['mutation.json','readback.json']]}

def capture_checkpoint(bundle,result):
    bundle=absolute(bundle,exists=False); state=load(bundle/'state.json')
    if state['layout']['mode']!='redraw' or state['checkpoint_captured']: raise ValueError('Checkpoint already captured or not needed')
    if payload(load(result)).get('saved') is not True: raise ValueError('Checkpoint save not confirmed')
    path=Path(state['path']); shutil.copy2(path,bundle/'before-editor-checkpoint.SchLib')
    state.update(checkpoint_captured=True,models_before=fingerprint_models(path),others_before=others(path,state['layout']['component']))
    write_json(bundle/'state.json',state)
    return {'checkpoint_captured':True,'path':str(path)}

def verify(bundle,result):
    bundle=absolute(bundle); state=load(bundle/'state.json'); after=payload(load(result)); expected=state['layout']
    if not state['checkpoint_captured']: raise ValueError('Capture the saved editor checkpoint before mutating')
    pins={p['designator']:p for p in after['pins']}; checks={}
    checks['identity']=after['component']==expected['component'] and after['part_count']==len(expected['parts']) and len(pins)==len(after['pins']) and set(pins)=={p['designator'] for p in expected['pins']}
    checks['pins']=checks['identity'] and all((pins[p['designator']]['name'],pins[p['designator']]['part'],pins[p['designator']]['orientation'],pins[p['designator']]['x_coord'],pins[p['designator']]['y_coord'],pins[p['designator']]['electrical'],pins[p['designator']]['length_coord'])==(p['name'],p['part'],p['orientation'],coord(p['x_mm']),coord(p['y_mm']),p['electrical'],coord(expected['pin_length_mm'])) for p in expected['pins'])
    checks['fonts']=all(p['name_font']==p['designator_font']==expected['font_name'] and p['name_size']==p['designator_size']==expected['font_size_pt'] and p['name_font_mode']==p['designator_font_mode']==1 for p in after['pins'])
    checks['black']=after['designator_color']==after['comment_color']==0 and len(after['pin_colors'])==len(pins) and {p['designator'] for p in after['pin_colors']}==set(pins) and all(p['color']==0 for p in after['pin_colors']+after['graphics'])
    graphics=after['graphics']; good=True
    for part in expected['parts']:
        g=[x for x in graphics if x['part']==part['id']]; rectangles=[x for x in g if x['kind']=='rectangle']; lines=[x for x in g if x['kind']=='line']; labels=[x for x in g if x['kind']=='label']
        good &= len(rectangles)==1 and len(lines)==2 and len(labels)==1
        good &= {(x['x'],x['y'],x['cx'],x['cy']) for x in rectangles}=={(0,coord(-part['height_mm']),coord(part['width_mm']),0)}
        good &= {(x['x'],x['y'],x['cx'],x['cy']) for x in lines}=={(coord(d),0,coord(d),coord(-part['height_mm'])) for d in part['dividers_mm']}
        good &= all((x['text'],x['x'],x['y'],x['font'],x['size'])==(part['function'],coord(part['label_mm'][0]),coord(part['label_mm'][1]),expected['font_name'],expected['font_size_pt']) for x in labels)
    checks['body_dividers_header']=bool(good)
    checks['document_grids']=after['snap_grid_coord']==coord(1) and after['visible_grid_coord']==coord(.5)
    errors=[]
    for p in after['pins']:
        dx,dy={0:(1,0),1:(0,1),2:(-1,0),3:(0,-1)}[p['orientation']]
        for value in [p['x_coord']+dx*p['length_coord'],p['y_coord']+dy*p['length_coord']]:
            errors.append(abs(value*STEP_MM-round(value*STEP_MM)))
    checks['endpoint_grid']=max(errors,default=math.inf)<=STEP_MM+1e-10
    path=Path(state['path'])
    if expected['mode']=='redraw':
        checks['models_and_maps_unchanged']=fingerprint_models(path)==state['models_before']
        checks['other_components_unchanged']=others(path,expected['component'])==state['others_before']
    else:
        models=[m for m in after['models'] if m['type'].upper()=='PCBLIB']; expected_map={(p['designator'],p['designator']) for p in expected['pins']}
        import re
        checks['model_binding']=len(models)==1 and models[0]['name']==state['footprint'] and set(re.findall(r'\(([^:(),]+):([^:(),]+)\)',models[0]['map']))==expected_map
    if state['pcblib']: checks['footprint_file_unchanged']=sha(state['pcblib'])==state['pcblib_sha256']
    report={'success':all(checks.values()),'checks':checks,'component':expected['component'],'pins':len(pins),'parts':after['part_count'],
        'electrical_policy':expected['electrical_policy'],'max_endpoint_grid_error_mm':max(errors,default=None),
        'path':str(path),'sha256':sha(path),'native_result_file':str(Path(result).resolve()),
        'visual_review':'Native/saved-geometry visual review still required; this validates geometry and typography, not formal GOST certification.',
        'project_resolution':'Separate step when project connection is requested; never inferred from a model name.',
        'erc':'Separate step for placed components; not proved by symbol readback.'}
    write_json(bundle/'verification.json',report)
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare'); p.add_argument('--mode',choices=['create','redraw'],required=True); p.add_argument('--manifest',required=True); p.add_argument('--path',required=True); p.add_argument('--out',required=True); p.add_argument('--before'); p.add_argument('--pcblib'); p.add_argument('--footprint')
    for name in ['capture-checkpoint','verify']:
        p=sub.add_parser(name); p.add_argument('--bundle',required=True); p.add_argument('--result',required=True)
    a=ap.parse_args()
    if a.command=='prepare': result=prepare(a.mode,a.manifest,a.path,a.out,a.before,a.pcblib,a.footprint)
    elif a.command=='capture-checkpoint': result=capture_checkpoint(a.bundle,a.result)
    else: result=verify(a.bundle,a.result)
    print(json.dumps(result,ensure_ascii=True)); return 0 if result.get('success',True) else 1

if __name__=='__main__': raise SystemExit(main())
