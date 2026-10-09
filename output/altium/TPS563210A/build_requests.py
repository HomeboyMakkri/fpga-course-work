"""Emit native Altium requests. CAD execution is through altium_local MCP only."""
from pathlib import Path
import json,sys,hashlib,shutil
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/altium'))
from library_api import q, snapshot_script, HELPERS
LIB=ROOT/'ARTIX/ARTIX/libraries/TPS563210A/TPS563210A.SchLib'
PCB=LIB.with_suffix('.PcbLib'); PROJECT=ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb'
COMP='TPS563210A'; MODEL='SOT65P280X110-8N'
def coord(mm): return round(mm/0.0254*10000)
PINS=[
 {'designator':'3','name':'VIN','x_mm':0,'y_mm':-6,'orientation':2,'electrical':7,'enum':'eElectricPower'},
 {'designator':'7','name':'EN','x_mm':0,'y_mm':-12,'orientation':2,'electrical':7,'enum':'eElectricPower'},
 {'designator':'5','name':'SS','x_mm':0,'y_mm':-18,'orientation':2,'electrical':7,'enum':'eElectricPower'},
 {'designator':'6','name':'VFB','x_mm':0,'y_mm':-24,'orientation':2,'electrical':7,'enum':'eElectricPower'},
 {'designator':'8','name':'VBST','x_mm':35,'y_mm':-6,'orientation':0,'electrical':7,'enum':'eElectricPower'},
 {'designator':'2','name':'SW','x_mm':35,'y_mm':-12,'orientation':0,'electrical':7,'enum':'eElectricPower'},
 {'designator':'4','name':'PG','x_mm':35,'y_mm':-18,'orientation':0,'electrical':7,'enum':'eElectricPower'},
 {'designator':'1','name':'GND','x_mm':35,'y_mm':-24,'orientation':0,'electrical':7,'enum':'eElectricPower'}]
def emit(name,body,decl,helpers=''):
    req={'body':body,'declarations':decl,'helpers':helpers,'timeout':30}
    (OUT/(name+'-request.json')).write_text(json.dumps(req,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(req,ensure_ascii=True))
def create():
    if LIB.exists(): raise FileExistsError('Refuse overwrite: '+str(LIB))
    manifest={'component':COMP,'manufacturer':'Texas Instruments','device':'TPS563210A','package':'DDF 8-pin SOT-23','procurement_suffix':'not selected','source':'https://www.ti.com/lit/ds/symlink/tps563210a.pdf','source_pin_table_page':3,'working_schlib':str(LIB),'existing_pcblib':str(PCB),'footprint':MODEL,'units':'mm','pin_length_mm':5,'snap_grid_mm':1,'auxiliary_grid_mm':0.5,'font':'GOST Common','font_pt':10,'body_mm':[0,-30,35,0],'pins':PINS,'pin_map':','.join(f'({n}:{n})' for n in range(1,9)),'authoring':'User explicitly requested new schematic symbol; existing user footprint retained.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f"LogStep('create exact new SCHLIB'); SD:=Client.OpenNewDocument('SCHLIB',{q(LIB)},{q(LIB.name)},False);",
           'if SD<>Nil then begin',f'SD.SetFileName({q(LIB)}); Client.ShowDocument(SD); L:=SchServer.GetSchDocumentByPath({q(LIB)});',
           'if L<>Nil then begin',"LogStep('create single TPS component'); C:=L.CurrentSchComponent; if C=Nil then begin C:=SchServer.SchObjectFactory(eSchComponent,eCreate_Default); L.AddSchComponent(C); L.CurrentSchComponent:=C; end;",'C:=L.CurrentSchComponent; C.OverideColors:=False; C.PinColor:=0;',
           f'C.LibReference:={q(COMP)}; C.ComponentDescription:={q("Texas Instruments TPS563210A synchronous buck regulator, DDF 8-pin; custom GOST-style schematic symbol")}; C.PartCount:=1; C.CurrentPartID:=1; C.DisplayMode:=0; C.PartIdLocked:=True;',
           "F:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common');",f'L.DisplayUnit:=eMM; L.SnapGridOn:=True; L.SnapGridSize:={coord(1)}; L.VisibleGridOn:=True; L.VisibleGridSize:={coord(.5)}; L.HotSpotGridOn:=True; L.HotSpotGridSize:={coord(.5)}; L.SystemFont:=F;',
           "SchServer.ProcessControl.PreProcess(L,''); try",'R:=SchServer.SchObjectFactory(eRectangle,eCreate_Default); R.OwnerPartId:=1; R.OwnerPartDisplayMode:=0;',f'R.Location:=Point(0,{coord(-30)}); R.Corner:=Point({coord(35)},0); R.IsSolid:=False; R.Color:=0; R.LineWidth:=eSmall; C.AddSchObject(R);',
           "T:=SchServer.SchObjectFactory(eLabel,eCreate_Default); T.OwnerPartId:=1; T.OwnerPartDisplayMode:=0; T.Text:='DC/DC'; T.FontId:=F; T.Color:=0; T.Justification:=eJustify_Center;",f'T.Location:=Point({coord(17.5)},{coord(-3)}); C.AddSchObject(T);']
    for x_mm in [12,23]:
        lines += ['G:=SchServer.SchObjectFactory(eLine,eCreate_Default); G.OwnerPartId:=1; G.OwnerPartDisplayMode:=0; G.Color:=0; G.LineWidth:=eSmall;',f'G.Location:=Point({coord(x_mm)},0); G.Corner:=Point({coord(x_mm)},{coord(-30)}); C.AddSchObject(G);']
    for pin in PINS:
        lines += ['P:=SchServer.SchObjectFactory(ePin,eCreate_Default);',f"P.Name:={q(pin['name'])}; P.Designator:={q(pin['designator'])}; P.OwnerPartId:=1; P.OwnerPartDisplayMode:=0; P.Location:=Point({coord(pin['x_mm'])},{coord(pin['y_mm'])}); P.Orientation:={pin['orientation']}; P.PinLength:={coord(5)}; P.Electrical:={pin['enum']}; P.Color:=0; P.ShowName:=True; P.ShowDesignator:=True;",'P.SetState_Name_CustomFontID(F); P.SetState_Designator_CustomFontID(F); P.SetState_Name_FontMode(1); P.SetState_Designator_FontMode(1); C.AddSchObject(P);']
    for name,value in [('Manufacturer','Texas Instruments'),('MPN','TPS563210A'),('Package','DDF'),('Datasheet','https://www.ti.com/lit/ds/symlink/tps563210a.pdf'),('Source','TI datasheet pin functions page 3; user-requested native symbol'),('OrderingSuffix','DDFR/DDFT packaging not selected')]:
        lines += ['A:=SchServer.SchObjectFactory(eParameter,eCreate_Default);',f'A.Name:={q(name)}; A.Text:={q(value)}; A.IsHidden:=True; A.FontId:=F; A.Color:=0; A.Location:=Point(0,0); C.AddSchObject(A);']
    lines += ["LogStep('bind exact existing footprint and identity map'); IM:=C.AddSchImplementation;",f'IM.ModelName:={q(MODEL)}; IM.ModelType:=\'PCBLIB\'; IM.IsCurrent:=True; IM.MapAsString:={q(manifest["pin_map"])}; IM.AddDataFileLink({q(MODEL)},{q(PCB.name)},\'PCBLIB\');',
              f"C.Designator.Text:='DA?'; C.Designator.FontId:=F; C.Designator.Color:=0; C.Designator.IsHidden:=False; C.Designator.Location:=Point(0,{coord(5)}); C.Comment.Text:={q(COMP)}; C.Comment.FontId:=F; C.Comment.Color:=0; C.Comment.IsHidden:=False; C.Comment.Location:=Point({coord(10)},{coord(5)});",
              "finally SchServer.ProcessControl.PostProcess(L,'Create TPS563210A symbol'); end; L.GraphicallyInvalidate; SD.SetModified(True); LogStep('save TPS native SchLib'); if SD.DoFileSave('') then ResultText:='{\"saved\":true,\"component\":\"TPS563210A\"}' else ResultText:='{\"error\":\"SAVE_FAILED\"}';",
              "end else ResultText:='{\"error\":\"NO_LIBRARY_API\"}'; end else ResultText:='{\"error\":\"CREATE_FAILED\"}';"]
    emit('create','\n'.join(lines),'SD:IServerDocument; L:ISch_Lib; C:ISch_Component; P:ISch_Pin; R:ISch_Rectangle; G:ISch_Line; T:ISch_Label; A:ISch_Parameter; IM:ISch_Implementation; F:Integer;')
def main():
    action=sys.argv[1]
    if action=='create': create()
    elif action=='snapshot': emit('reloaded',*snapshot_script(str(LIB),COMP,reload=True))
    elif action=='backup':
        dest=OUT/'backups'; dest.mkdir(exist_ok=True)
        result=[]
        for p in [PCB,PROJECT]:
            d=dest/p.name
            if d.exists(): raise FileExistsError(d)
            shutil.copy2(p,d); result.append({'source':str(p),'backup':str(d),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        (OUT/'backups.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result))
    else: raise ValueError(action)
if __name__=='__main__': main()
