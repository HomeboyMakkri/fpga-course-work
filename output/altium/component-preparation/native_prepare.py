"""Sequential native CAD operations for this request. No binary CAD editing."""
from pathlib import Path
import argparse, hashlib, json, shutil, sys, zipfile
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/altium'))
import cad_bridge as bridge
from library_api import q, checked, target_block, snapshot_script, DECL, HELPERS, transact, index_pins, _same_except

def save(name,data):
    (OUT/'evidence').mkdir(parents=True,exist_ok=True)
    (OUT/'evidence'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data

def run(name,body,decl='',helpers='',timeout=30):
    save(name+'-request',{'body':body,'declarations':decl,'helpers':helpers})
    # Only emit a request. Execute using the available native MCP tool;
    # sandbox-launched CLI failed to start scripts in this desktop session.
    request={'body':body,'declarations':decl,'helpers':helpers,'timeout':timeout}
    print(json.dumps(request,ensure_ascii=True))
    return request

def copy_sources():
    files={
      'fpga':('ARTIX/ARTIX/libraries/X7', ['XC7A50T-2FGG484I.SchLib','BGA484C100P22X22_2300X2300X260.PcbLib']),
      'asv':('ARTIX/ARTIX/libraries/ASV-50MHz',['Schlib1.SchLib','PcbLib1.PcbLib']),
      'flash':('ARTIX/ARTIX/libraries/W25Q128JV/source',['W25Q128JVSIQ.SchLib','SOIC127P790X216-8N.PcbLib'])}
    evidence=[]
    for key,(folder,names) in files.items():
        src=ROOT/folder
        if key=='fpga': dest=ROOT/'ARTIX/ARTIX/libraries/project'
        elif key=='asv': dest=src/'new'
        else: dest=src.parent/'new'
        dest.mkdir(parents=True,exist_ok=True)
        archive=OUT/'evidence'/f'{key}-source-checkpoint.zip'
        archive.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
            for name in names: z.write(src/name,name)
        for name in names:
            target=dest/({'XC7A50T-2FGG484I.SchLib':'ARTIX.SchLib','BGA484C100P22X22_2300X2300X260.PcbLib':'ARTIX.PcbLib'}.get(name,name) if key=='fpga' else name)
            if target.exists(): raise FileExistsError(target)
            shutil.copy2(src/name,target)
            evidence.append({'source':str(src/name),'destination':str(target),'source_sha256':hashlib.sha256((src/name).read_bytes()).hexdigest(),'destination_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    save('source-checkpoints',evidence)
    print(json.dumps(evidence,ensure_ascii=True))

def isolate_asv_sch():
    path=str(ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib')
    comp='ASV-50.000MHZ-LRS-T'
    body=target_block(path,comp,"""
LogStep('isolate selected ASV component');
Map := TStringList.Create; LI := L.SchLibIterator_Create; LI.AddFilter_ObjectSet(MkSet(eSchComponent)); LC := LI.FirstSchObject;
while LC <> Nil do begin Map.Add(LC.LibReference); LC := LI.NextSchObject; end; L.SchIterator_Destroy(LI);
SchServer.ProcessControl.PreProcess(L,'');
try
for K := 0 to Map.Count-1 do begin
  if Map[K] <> 'ASV-50.000MHZ-LRS-T' then begin
    LI := L.SchLibIterator_Create; LI.AddFilter_ObjectSet(MkSet(eSchComponent)); LC := LI.FirstSchObject; Other := Nil;
    while LC <> Nil do begin if LC.LibReference = Map[K] then Other := LC; LC := LI.NextSchObject; end; L.SchIterator_Destroy(LI);
    if Other <> Nil then L.RemoveSchComponent(Other);
  end;
end;
finally SchServer.ProcessControl.PostProcess(L,'Isolate ASV'); end;
Map.Free; SD.SetModified(True); L.GraphicallyInvalidate; LogStep('save isolated ASV');
if SD.DoFileSave('') then ResultText := '{"saved":true}' else ResultText := '{"error":"SAVE_FAILED"}';
""")
    run('asv-isolate-sch',body,DECL+' Map:TStringList; K:Integer; Other:ISch_Component;')

def pcb_snapshot(path,name):
    body=f"""
LogStep('open exact PCB library'); SD := Client.OpenDocument('PCBLIB',{q(path)}); Client.ShowDocument(SD);
PL := PCBServer.GetPCBLibraryByPath({q(path)});
if PL <> Nil then begin
ResultText := '{{"footprints":['; Count := 0;
LI := PL.LibraryIterator_Create; LI.SetState_FilterAll; C := LI.FirstPCBObject;
while C <> Nil do begin
 if Count > 0 then ResultText := ResultText+',';
 ResultText := ResultText+'{{"name":'+JQ(C.Name)+',"pads":['; N := 0;
 GI := C.GroupIterator_Create; GI.AddFilter_ObjectSet(MkSet(ePadObject)); P := GI.FirstPCBObject;
 while P <> Nil do begin
  if N > 0 then ResultText := ResultText+',';
  ResultText := ResultText+'{{"name":'+JQ(P.Name)+',"x_coord":'+IntToStr(P.X)+',"y_coord":'+IntToStr(P.Y)+',"x_size_coord":'+IntToStr(P.TopXSize)+',"y_size_coord":'+IntToStr(P.TopYSize)+',"hole_coord":'+IntToStr(P.HoleSize)+',"rotation":'+FloatToStr(P.Rotation)+'}}';
  N := N+1; P := GI.NextPCBObject;
 end; C.GroupIterator_Destroy(GI); ResultText := ResultText+'],"pad_count":'+IntToStr(N)+'}}';
 Count := Count+1; C := LI.NextPCBObject;
end; PL.LibraryIterator_Destroy(LI); ResultText := ResultText+'],"count":'+IntToStr(Count)+'}}';
end else ResultText := '{{"error":"NO_PCB_LIBRARY"}}';
"""
    return run(name,body,'SD:IServerDocument; PL:IPCB_Library; LI:IPCB_LibraryIterator; GI:IPCB_GroupIterator; C:IPCB_LibComponent; P:IPCB_Pad; N,Count:Integer;',HELPERS)

def isolate_asv_pcb():
    path=str(ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/new/PcbLib1.PcbLib')
    body=f"""
LogStep('open exact ASV PCB working copy'); SD := Client.OpenDocument('PCBLIB',{q(path)}); Client.ShowDocument(SD); PL := PCBServer.GetPCBLibraryByPath({q(path)});
if PL <> Nil then begin
 Map := TStringList.Create; LI := PL.LibraryIterator_Create; LI.SetState_FilterAll; C := LI.FirstPCBObject;
 while C <> Nil do begin Map.Add(C.Name); C := LI.NextPCBObject; end; PL.LibraryIterator_Destroy(LI);
 LogStep('remove foreign footprints from working copy');
 for K := 0 to Map.Count-1 do begin
   if Map[K] <> 'ASV25000MHZEJT' then begin C := PL.GetComponentByName(Map[K]); if C <> Nil then PL.RemoveComponent(C); end;
 end;
 Map.Free; SD.SetModified(True); LogStep('save isolated ASV footprint');
 if SD.DoFileSave('') then ResultText := '{{"saved":true}}' else ResultText := '{{"error":"SAVE_FAILED"}}';
end else ResultText := '{{"error":"NO_PCB_LIBRARY"}}';
"""
    return run('asv-isolate-pcb',body,'SD:IServerDocument; PL:IPCB_Library; LI:IPCB_LibraryIterator; C:IPCB_LibComponent; Map:TStringList; K:Integer;')

def coord(mm):
    return round(mm/0.0254*10000)

def make_layout(key):
    before=json.loads((OUT/'evidence'/f'{key}-native-before.json').read_text(encoding='utf-8'))['result']
    if key=='fpga':
        path=ROOT/'ARTIX/ARTIX/libraries/project/ARTIX.SchLib'; component='XC7A50T-2FGG484I'
        labels=['CONFIG / XADC / JTAG','BANK 14','BANK 15','BANK 16','BANK 34','BANK 35','GTP 216','GND','POWER','NC']
        parts=[]
        for part_id in range(1,11):
            source=[p for p in before['pins'] if p['part']==part_id]
            width=100 if part_id in [1,7] else 80 if part_id in [2,3,4,5,6] else 60
            pins=[]; nrows=0
            for orientation in [2,0]:
                side=sorted([p for p in source if p['orientation']==orientation],key=lambda p:(-p['y_coord'],p['designator']))
                nrows=max(nrows,len(side))
                for i,p in enumerate(side): pins.append({'designator':p['designator'],'name':p['name'],'x_mm':0 if orientation==2 else width,'y_mm':-5-4*i,'orientation':orientation})
            parts.append({'id':part_id,'label':labels[part_id-1],'body_mm':[0,-5-4*(nrows-1)-3,width,2],'label_mm':[width/2,-1],'pins':pins})
    elif key=='asv':
        path=ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib'; component='ASV-50.000MHZ-LRS-T'
        layout={'4':(0,-6,2),'1':(0,-12,2),'3':(65,-6,0),'2':(65,-12,0)}
        parts=[{'id':1,'label':'G','body_mm':[0,-17,65,2],'label_mm':[32.5,-1],'pins':[{'designator':p['designator'],'name':p['name'],'x_mm':layout[p['designator']][0],'y_mm':layout[p['designator']][1],'orientation':layout[p['designator']][2]} for p in before['pins']]}]
    elif key=='flash':
        path=ROOT/'ARTIX/ARTIX/libraries/W25Q128JV/new/W25Q128JVSIQ.SchLib'; component='W25Q128JVSIQ'
        layout={'1':(0,-6,2),'6':(0,-12,2),'5':(0,-18,2),'2':(0,-24,2),'3':(50,-18,0),'7':(50,-24,0),'8':(50,-6,0),'4':(50,-12,0)}
        parts=[{'id':1,'label':'FLASH','body_mm':[0,-29,50,2],'label_mm':[25,-1],'pins':[{'designator':p['designator'],'name':p['name'],'x_mm':layout[p['designator']][0],'y_mm':layout[p['designator']][1],'orientation':layout[p['designator']][2]} for p in before['pins']]}]
    else: raise ValueError(key)
    data={'component':component,'path':str(path),'units':'mm','snap_grid_mm':1,'auxiliary_grid_mm':0.5,'length_mm':5,'font_name':'GOST Common','font_size_pt':10,'parts':parts,'source_snapshot':f'evidence/{key}-native-before.json'}
    save(key+'-layout-mm',data)
    rows=[]
    for part in parts:
        for p in part['pins']: rows.append(f"{p['designator']}={part['id']},{coord(p['x_mm'])},{coord(p['y_mm'])},{p['orientation']}")
    mapping=OUT/'evidence'/f'{key}-layout-internal.txt'; mapping.write_text('\n'.join(rows),encoding='ascii')
    body=["LogStep('load exact mm-to-internal layout'); Map:=TStringList.Create; V:=TStringList.Create;",f'Map.LoadFromFile({q(mapping)});',"F:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common');", "SchServer.ProcessControl.PreProcess(L,'');",'try',f'C.PartCount:={len(parts)}; C.DisplayMode:=0;',f'L.DisplayUnit:=eMM; L.SnapGridOn:=True; L.SnapGridSize:={coord(1)}; L.VisibleGridOn:=True; L.VisibleGridSize:={coord(0.5)}; L.HotSpotGridSize:={coord(0.5)}; L.SystemFont:=F;',
          'I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject;',
          f'while P<>Nil do begin V.CommaText:=Map.Values[P.Designator]; P.OwnerPartId:=StrToInt(V[0]); P.OwnerPartDisplayMode:=0; P.Location:=Point(StrToInt(V[1]),StrToInt(V[2])); P.Orientation:=StrToInt(V[3]); P.PinLength:={coord(5)}; P.SetState_Name_CustomFontID(F); P.SetState_Designator_CustomFontID(F); P.SetState_Name_FontMode(1); P.SetState_Designator_FontMode(1); P:=I.NextSchObject; end; C.SchIterator_Destroy(I);',
          "LogStep('mm pin geometry applied; remove old graphic body'); N:=0; repeat I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eRectangle,eLabel,ePolyLine,eLine)); O:=I.FirstSchObject; C.SchIterator_Destroy(I); if O<>Nil then begin C.RemoveSchObject(O); L.RemoveSchObject(O); N:=N+1; end; until (O=Nil) or (N>=1000);",
          'if N<1000 then begin']
    for part in parts:
        x0,y0,x1,y1=part['body_mm']; tx,ty=part['label_mm']
        body += [f"C.CurrentPartID:={part['id']}; R:=SchServer.SchObjectFactory(eRectangle,eCreate_Default); R.OwnerPartId:={part['id']}; R.OwnerPartDisplayMode:=0; R.Location:=Point({coord(x0)},{coord(y0)}); R.Corner:=Point({coord(x1)},{coord(y1)}); R.Color:=0; R.IsSolid:=False; R.LineWidth:=eSmall; C.AddSchObject(R);",
                 f"T:=SchServer.SchObjectFactory(eLabel,eCreate_Default); T.OwnerPartId:={part['id']}; T.OwnerPartDisplayMode:=0; T.Text:={q(part['label'])}; T.Location:=Point({coord(tx)},{coord(ty)}); T.FontId:=F; T.Color:=0; T.Justification:=eJustify_Center; C.AddSchObject(T);"]
    body += ['end;',f'C.Designator.FontId:=F; C.Comment.FontId:=F; C.Designator.Location:=Point(0,{coord(5)}); C.Comment.Location:=Point({coord(15)},{coord(5)}); C.Designator.IsHidden:=False; C.Comment.IsHidden:=True;',
             "C.CurrentPartID:=1; C.PartIdLocked:=True; finally SchServer.ProcessControl.PostProcess(L,'Millimetre library layout'); end;",
             "Map.Free; V.Free; SD.SetModified(True); L.GraphicallyInvalidate; LogStep('save mm symbol'); if N<1000 then begin if SD.DoFileSave('') then ResultText:='{\"saved\":true}' else ResultText:='{\"error\":\"SAVE_FAILED\"}'; end else ResultText:='{\"error\":\"BODY_REMOVAL_LIMIT\"}';"]
    return run(key+'-grid-mutation',target_block(str(path),component,'\n'.join(body)),DECL+' Map,V:TStringList; F:Integer; O:ISch_GraphicalObject; R:ISch_Rectangle; T:ISch_Label;')

def repair_model_link():
    path=str(ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib')
    body=target_block(path,'ASV-50.000MHZ-LRS-T',"""
LogStep('repair exact ASV model location only');
I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eImplementation)); IM:=I.FirstSchObject; N:=0;
while IM<>Nil do begin
 if (IM.ModelName='ASV25000MHZEJT') and (IM.ModelType='PCBLIB') then begin
  for K:=0 to IM.DatafileLinkCount-1 do begin DL:=IM.DatafileLink[K]; DL.Location:='PcbLib1.PcbLib'; end;
  N:=N+1;
 end;
 IM:=I.NextSchObject;
end; C.SchIterator_Destroy(I); SD.SetModified(True);
if N=1 then begin if SD.DoFileSave('') then ResultText:='{"saved":true,"changed_model_count":1}' else ResultText:='{"error":"SAVE_FAILED"}'; end else ResultText:='{"error":"MODEL_COUNT_MISMATCH"}';
""")
    return run('asv-model-link-repair',body,DECL+' IM:ISch_Implementation; DL:ISch_ModelDatafileLink; K:Integer;')

def correct_flash_source_defect():
    path=str(ROOT/'ARTIX/ARTIX/libraries/W25Q128JV/new/W25Q128JVSIQ.SchLib')
    body=target_block(path,'W25Q128JVSIQ',"""
LogStep('documented Winbond Rev M source defect correction');
SchServer.ProcessControl.PreProcess(L,'');
try
I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject; N:=0;
while P<>Nil do begin
 if (P.Designator='1') or (P.Designator='6') then P.Electrical:=eElectricInput
 else if (P.Designator='2') or (P.Designator='3') or (P.Designator='5') or (P.Designator='7') then P.Electrical:=eElectricIO
 else if (P.Designator='4') or (P.Designator='8') then P.Electrical:=eElectricPower;
 if P.Designator='7' then P.Name:='IO3';
 N:=N+1; P:=I.NextSchObject;
end; C.SchIterator_Destroy(I);
finally SchServer.ProcessControl.PostProcess(L,'Correct verified Flash source defect'); end;
SD.SetModified(True); L.GraphicallyInvalidate;
if N=8 then begin if SD.DoFileSave('') then ResultText:='{"saved":true,"source_defects_corrected":true}' else ResultText:='{"error":"SAVE_FAILED"}'; end else ResultText:='{"error":"PIN_COUNT_MISMATCH"}';
""")
    return run('flash-source-defect-correction',body,DECL)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('action'); ap.add_argument('--path'); ap.add_argument('--name',default='pcb-snapshot'); a=ap.parse_args()
    if a.action=='copy': copy_sources()
    elif a.action=='isolate-sch': isolate_asv_sch()
    elif a.action=='isolate-pcb': isolate_asv_pcb()
    elif a.action=='pcb-snapshot': pcb_snapshot(a.path,a.name)
    elif a.action=='layout': make_layout(a.name)
    elif a.action=='model-link': repair_model_link()
    elif a.action=='flash-correct': correct_flash_source_defect()
    elif a.action=='reload-snapshot':
        configs={'asv':('ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib','ASV-50.000MHZ-LRS-T'),'fpga':('ARTIX/ARTIX/libraries/project/ARTIX.SchLib','XC7A50T-2FGG484I'),'flash':('ARTIX/ARTIX/libraries/W25Q128JV/new/W25Q128JVSIQ.SchLib','W25Q128JVSIQ')}
        p,c=configs[a.name]; run(a.name+'-reloaded',*snapshot_script(str(ROOT/p),c,reload=True))
    else: raise ValueError(a.action)
if __name__=='__main__': main()
