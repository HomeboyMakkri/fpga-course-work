"""Task driver: saved-file readers and serialized native Altium operations only."""
from pathlib import Path
import json, sys, hashlib, configparser
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/altium'))
sys.path.insert(0,str(ROOT/'output/altium/component-preparation'))
import cad_bridge as bridge
from read_native_inventory import inspect
from library_api import HELPERS
from manifest import q

def save(name,data):
    (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data

def run(name,body,decl='',helpers=HELPERS,timeout=40):
    request={'body':body,'declarations':decl,'helpers':helpers,'timeout':timeout}
    save(name+'-request',request)
    result=save(name,bridge.run_script(**request))
    print(json.dumps(result,ensure_ascii=True,indent=2))
    return result

def inventory():
    paths=list((ROOT/'ARTIX/ARTIX').glob('*.SchDoc'))
    paths+=list((ROOT/'ARTIX/ARTIX/libraries').rglob('*.SchLib'))
    data=[]
    for p in paths:
        if 'original' in p.parts or 'History' in p.parts: continue
        try: data.append(inspect(p))
        except Exception as e: data.append({'path':str(p),'error':str(e)})
    save('saved-inventory',data)
    for row in data:
        cs=[]
        for recs in row.get('records',{}).values():
            for r in recs:
                u={k.upper():v for k,v in r.items()}
                if u.get('RECORD')=='1':
                    cs.append({k:v for k,v in u.items() if k in {'LIBREFERENCE','DESIGNATOR','COMMENT','COMPONENTDESCRIPTION','LOCATION.X','LOCATION.Y'}})
        print(json.dumps({'path':row['path'],'components':cs},ensure_ascii=True))

def preflight():
    body=f'''WS:=GetWorkspace; Prj:=WS.DM_OpenProject({q(str(ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb'))},True);
if Prj<>Nil then begin ResultText:='{{"documents":[';
for I:=0 to Prj.DM_LogicalDocumentCount-1 do begin
 D:=Prj.DM_LogicalDocuments(I); if I>0 then ResultText:=ResultText+',';
 SD:=Client.GetDocumentByPath(D.DM_FullPath);
 ResultText:=ResultText+'{{"path":'+JQ(D.DM_FullPath)+',"open":';
 if SD=Nil then ResultText:=ResultText+'false,"modified":false}}'
 else begin ResultText:=ResultText+'true,"modified":'; if SD.Modified then ResultText:=ResultText+'true}}' else ResultText:=ResultText+'false}}'; end;
end; ResultText:=ResultText+']}}'; end else ResultText:='{{"error":"PROJECT_NOT_OPEN"}}';'''
    run('live-project-before',body,'WS:IWorkspace; Prj:IProject; D:IDocument; SD:IServerDocument; I:Integer;')

SOURCES={
 'usb':('libraries/type-c/type-c/2345986-1.SchLib','2345986-1'),
 'esd':('libraries/PUSB3FR4Z/PUSB3FR4Z.SchLib','PUSB3FR4Z'),
 'ft':('libraries/FT(uart)/FT2232HL-REEL/FT2232HL-REEL.SchLib','FT2232HL-REEL'),
 'ee':('libraries/93lc(eeprom)/93LC66B-I_SN/93LC66B-I_SN.SchLib','93LC66B-I/SN'),
 'xtal':('libraries/25MHz/new/HKC3225SX-25MHZ-26594-R4V1.SchLib','HKC3225SX-25MHZ-26594-R4V1'),
 'fb':('libraries/FB BLM18SG121TN1D/FB.SchLib','CMP-0686-00602-4'),
 'diode':('libraries/ASV-50MHz/Schlib1.SchLib','SS24-E3_5BT')}

CAD_DECL='''SD,LS:IServerDocument; Doc,SrcDoc:ISch_Document; L:ISch_Lib; SRC,C,LC:ISch_Component; I,J,LI:ISch_Iterator; P,CP:ISch_Pin; N,F,X,Y,DX,DY:Integer; V:TStringList;'''
CAD_HELPERS=HELPERS+r'''
function LibSource(Path,Ref:String):ISch_Component;
var D:IServerDocument; L:ISch_Lib; I:ISch_Iterator; C,S:ISch_Component;
begin
 Result:=Nil; D:=Client.OpenDocument('SCHLIB',Path); L:=SchServer.GetSchDocumentByPath(Path);
 if L<>Nil then begin S:=Nil; I:=L.SchLibIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject;
 while C<>Nil do begin if C.LibReference=Ref then S:=C; C:=I.NextSchObject; end; L.SchIterator_Destroy(I);
 if S<>Nil then begin if L.CurrentSchComponent.LibReference<>Ref then L.CurrentSchComponent:=S; Result:=L.CurrentSchComponent; end; end;
end;
procedure CopyGraphics(D:ISch_Document; C:ISch_Component; Path,Ref:String);
var S:ISch_Component; I,J:ISch_Iterator; G,H:ISch_GraphicalObject; N:Integer;
begin
 N:=0; J:=C.SchIterator_Create; J.AddFilter_ObjectSet(MkSet(eRectangle,eLine,eLabel,ePolyline,eArc)); G:=J.FirstSchObject;
 while G<>Nil do begin N:=N+1; G:=J.NextSchObject; end; C.SchIterator_Destroy(J);
 if N=0 then begin
  S:=LibSource(Path,Ref);
  if S<>Nil then begin I:=S.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eRectangle,eLine,eLabel,ePolyline,eArc)); G:=I.FirstSchObject;
   while G<>Nil do begin
    if (G.OwnerPartId=0) or (G.OwnerPartId=S.CurrentPartID) then begin
     H:=G.Replicate; H.MoveByXY(C.Location.X-S.Location.X,C.Location.Y-S.Location.Y); C.AddSchObject(H);
    end;
    G:=I.NextSchObject;
   end; S.SchIterator_Destroy(I);
  end;
 end;
end;
function CloneComplete(S:ISch_Component):ISch_Component;
var C:ISch_Component; I,J:ISch_Iterator; P,Q,R:ISch_Pin; Found:Boolean;
begin
 C:=S.Replicate;
 I:=S.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject;
 while P<>Nil do begin
  Found:=False; J:=C.SchIterator_Create; J.AddFilter_ObjectSet(MkSet(ePin)); Q:=J.FirstSchObject;
  while Q<>Nil do begin if (Q.Designator=P.Designator) and (Q.OwnerPartId=P.OwnerPartId) then Found:=True; Q:=J.NextSchObject; end; C.SchIterator_Destroy(J);
  if not Found then begin R:=P.Replicate; C.AddSchObject(R); end;
  P:=I.NextSchObject;
 end; S.SchIterator_Destroy(I); Result:=C;
end;
function FromLib(Path,Ref:String):ISch_Component;
var D:IServerDocument; L:ISch_Lib; I:ISch_Iterator; C,S:ISch_Component;
begin
 Result:=Nil; D:=Client.OpenDocument('SCHLIB',Path); L:=SchServer.GetSchDocumentByPath(Path);
 if L<>Nil then begin
  S:=Nil; I:=L.SchLibIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject;
  while C<>Nil do begin if C.LibReference=Ref then S:=C; C:=I.NextSchObject; end; L.SchIterator_Destroy(I);
  if S<>Nil then begin if L.CurrentSchComponent.LibReference<>Ref then L.CurrentSchComponent:=S; S:=L.CurrentSchComponent; Result:=CloneComplete(S); end;
 end;
end;
function FromSheet(Path,Ref:String):ISch_Component;
var D:IServerDocument; S:ISch_Document; I:ISch_Iterator; C:ISch_Component;
begin
 Result:=Nil; D:=Client.OpenDocument('SCH',Path); S:=SchServer.GetSchDocumentByPath(Path);
 if S<>Nil then begin I:=S.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject;
  while C<>Nil do begin if C.Designator.Text=Ref then Result:=CloneComplete(C); C:=I.NextSchObject; end; S.SchIterator_Destroy(I);
 end;
end;
procedure AddWire(D:ISch_Document; X1,Y1,X2,Y2:Integer);
var W:ISch_Wire;
begin
 W:=SchServer.SchObjectFactory(eWire,eCreate_Default); W.InsertVertex:=1; W.SetState_Vertex(1,Point(X1,Y1));
 W.InsertVertex:=2; W.SetState_Vertex(2,Point(X2,Y2)); W.Color:=128; D.RegisterSchObjectInContainer(W);
end;
procedure LabelPin(D:ISch_Document; C:ISch_Component; Num,NetName:String);
var I:ISch_Iterator; P:ISch_Pin; N:ISch_NetLabel; X,Y,EX,EY:Integer;
begin
 I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject;
 while P<>Nil do begin if (P.Designator=Num) and ((P.OwnerPartId=C.CurrentPartID) or (P.OwnerPartId=0)) then begin
  X:=P.Location.X; Y:=P.Location.Y;
  case P.Orientation of 0:X:=X+P.PinLength; 1:Y:=Y+P.PinLength; 2:X:=X-P.PinLength; 3:Y:=Y-P.PinLength; end;
  EX:=X; EY:=Y; case P.Orientation of 0:EX:=X+MilsToCoord(12/0.0254); 1:EY:=Y+MilsToCoord(7/0.0254); 2:EX:=X-MilsToCoord(35/0.0254); 3:EY:=Y-MilsToCoord(7/0.0254); end;
  AddWire(D,X,Y,EX,EY); N:=SchServer.SchObjectFactory(eNetLabel,eCreate_Default); N.Text:=NetName;
  N.Location:=Point(EX,EY); N.FontID:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common'); N.Color:=128;
  D.RegisterSchObjectInContainer(N);
 end; P:=I.NextSchObject; end; C.SchIterator_Destroy(I);
end;
procedure Note(D:ISch_Document; X,Y:Integer; Text:String);
var N:ISch_Label;
begin N:=SchServer.SchObjectFactory(eLabel,eCreate_Default); N.Text:=Text; N.Location:=Point(MilsToCoord(X/0.0254),MilsToCoord(Y/0.0254));
 N.FontID:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common'); N.Color:=0; D.RegisterSchObjectInContainer(N); end;
procedure NC(D:ISch_Document; C:ISch_Component; Num:String);
var I:ISch_Iterator; P:ISch_Pin; G:ISch_GraphicalObject; X,Y:Integer;
begin I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject;
 while P<>Nil do begin if P.Designator=Num then begin
  X:=P.Location.X; Y:=P.Location.Y; case P.Orientation of 0:X:=X+P.PinLength; 1:Y:=Y+P.PinLength; 2:X:=X-P.PinLength; 3:Y:=Y-P.PinLength; end;
  G:=SchServer.SchObjectFactory(eNoERC,eCreate_Default); G.Location:=Point(X,Y); D.RegisterSchObjectInContainer(G);
 end; P:=I.NextSchObject; end; C.SchIterator_Destroy(I); end;
procedure AddNamedPort(D:ISch_Document; Name:String; X,Y:Integer);
var P:ISch_Port; N:ISch_NetLabel;
begin
 P:=SchServer.SchObjectFactory(ePort,eCreate_Default); P.Name:=Name; P.Location:=Point(X,Y); P.Width:=MilsToCoord(32/0.0254);
 P.Style:=ePortRight; P.ConnectedEnd:=ePortConnectedEnd_Origin; P.IOType:=ePortBidirectional; P.Color:=0; P.TextColor:=0; P.AreaColor:=16777215; D.RegisterSchObjectInContainer(P);
 AddWire(D,X-MilsToCoord(25/0.0254),Y,X,Y); N:=SchServer.SchObjectFactory(eNetLabel,eCreate_Default); N.Text:=Name;
 N.Location:=Point(X-MilsToCoord(25/0.0254),Y); N.FontID:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common'); N.Color:=128; D.RegisterSchObjectInContainer(N);
end;
procedure BankPin(D:ISch_Document; C:ISch_Component; Num:String; BusY:Integer);
var I:ISch_Iterator; P:ISch_Pin; X,Y:Integer;
begin I:=C.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(ePin)); P:=I.FirstSchObject;
 while P<>Nil do begin if P.Designator=Num then begin X:=P.Location.X; Y:=P.Location.Y;
 case P.Orientation of 0:X:=X+P.PinLength; 1:Y:=Y+P.PinLength; 2:X:=X-P.PinLength; 3:Y:=Y-P.PinLength; end;
 AddWire(D,X,Y,X,BusY); end; P:=I.NextSchObject; end; C.SchIterator_Destroy(I); end;
procedure NameAt(D:ISch_Document; NetName:String; X,Y:Integer; Power:Boolean);
var N:ISch_NetLabel; P:ISch_PowerObject;
begin N:=SchServer.SchObjectFactory(eNetLabel,eCreate_Default); N.Text:=NetName; N.Location:=Point(X,Y); N.Color:=128; N.FontID:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common'); D.RegisterSchObjectInContainer(N);
 if Power then begin P:=SchServer.SchObjectFactory(ePowerObject,eCreate_Default); P.Text:=NetName; P.Location:=Point(X,Y); D.RegisterSchObjectInContainer(P); end;
end;
'''

def create_header(path):
    assert not path.exists(),path
    return f'''LogStep('create explicit NEW sheet'); SD:=Client.OpenNewDocument('SCH',{q(str(path))},{q(path.name)},False);
if SD<>Nil then begin SD.SetFileName({q(str(path))}); Client.ShowDocument(SD); Doc:=SchServer.GetSchDocumentByPath({q(str(path))});
if Doc<>Nil then begin
 Doc.UseCustomSheet:=True; Doc.CustomX:=MilsToCoord(600/0.0254); Doc.CustomY:=MilsToCoord(420/0.0254);
 Doc.SnapGridSize:=MilsToCoord(1/0.0254); Doc.VisibleGridSize:=MilsToCoord(5/0.0254);
 F:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common');
 SchServer.ProcessControl.PreProcess(Doc,'JTAG UART transfer'); try
'''

def place(c):
    import uuid
    if c['source'] in SOURCES:
        p,r=SOURCES[c['source']]; get=f'FromLib({q(str(ROOT/"ARTIX/ARTIX"/p))},{q(r)})'
    else: get=f'FromSheet({q(str(ROOT/"ARTIX/ARTIX/01_Power.SchDoc"))},{q(c["source"])})'
    s=f'''LogStep({q('place '+c['ref'])}); C:={get}; if C<>Nil then begin
C.UniqueId:={q(uuid.uuid4().hex[:8].upper())};
C.Designator.Text:={q(c['ref'])}; C.Comment.Text:={q(c['value'])};
C.MoveByXY(MilsToCoord({c['x']}/0.0254)-C.Location.X,MilsToCoord({c['y']}/0.0254)-C.Location.Y);
C.Designator.FontID:=F; C.Comment.FontID:=F; C.Designator.IsHidden:=False; C.Comment.IsHidden:=False;
C.Designator.Location:=Point(C.Location.X,C.Location.Y+MilsToCoord(3/0.0254)); C.Comment.Location:=Point(C.Location.X,C.Location.Y+MilsToCoord(7/0.0254));
Doc.RegisterSchObjectInContainer(C);
'''
    if c['source'] in SOURCES:
        s+=f'C.LibraryPath:={q(str(ROOT/"ARTIX/ARTIX"/SOURCES[c["source"]][0]))};\n'
    for num,net in c['nets'].items():
        if 'bank' in c:
            s+=f'BankPin(Doc,C,{q(num)},MilsToCoord({c["y"]+(15 if num=="2" else -8)}/0.0254));\n'
        elif net:s+=f'LabelPin(Doc,C,{q(num)},{q(net)});\n'
        else:s+=f'NC(Doc,C,{q(num)});\n'
    if c['source'] in ['R1','C1']:
        s+='C.Designator.Location:=Point(C.Location.X+MilsToCoord(4/0.0254),C.Location.Y+MilsToCoord(9/0.0254)); C.Comment.Location:=Point(C.Location.X+MilsToCoord(4/0.0254),C.Location.Y+MilsToCoord(5/0.0254));\n'
    return s+"end;\n"

def footer():
    return '''finally SchServer.ProcessControl.PostProcess(Doc,'JTAG UART transfer'); end;
Doc.GraphicallyInvalidate; SD.SetModified(True); LogStep('native save new sheet');
if SD.DoFileSave('') then begin Client.CloseDocument(SD); SD:=Client.OpenDocument('SCH',Doc.DocumentName); ResultText:='{"saved_and_reopened":true}'; end else ResultText:='{"error":"SAVE_FAILED"}';
end; end;'''

def fixture():
    path=ROOT/'tools/altium/runtime/JTAG_UART_Placement_Probe.SchDoc'
    cs=[{'source':'usb','ref':'J901','value':'2345986-1','x':60,'y':350,'nets':{'A6':'USB_DP','A7':'USB_DN','A4':'USB_POWER'}},
        {'source':'R1','ref':'R901','value':'5.1k','x':180,'y':330,'nets':{'1':'CC1','2':'GND'}},
        {'source':'C1','ref':'C901','value':'0.1uF','x':210,'y':330,'nets':{'1':'3V3','2':'GND'}},
        {'source':'ft','ref':'U901','value':'FT2232HL','x':290,'y':350,'nets':{'7':'USB_DN','8':'USB_DP'}},
        {'source':'diode','ref':'D901','value':'SS24','x':180,'y':270,'nets':{'1':'5V','2':'USB_POWER'}}]
    body=create_header(path)+''.join(place(c) for c in cs)
    body+=footer().replace("SD:=Client.OpenDocument('SCH',Doc.DocumentName)",f"SD:=Client.OpenDocument('SCH',{q(str(path))})")
    run('placement-probe',body,CAD_DECL,CAD_HELPERS)

def verify_fixture():
    from manifest import inspect_body
    path=ROOT/'tools/altium/runtime/JTAG_UART_Placement_Probe.SchDoc'
    r=save('placement-probe-readback',bridge.run_script(*inspect_body(str(path))))
    print('readback',r.get('success'),[(c['ref'],len(c['pins'])) for c in r.get('result',{}).get('components',[])])
    pr=path.with_suffix('.PrjPcb')
    assert not pr.exists()
    pr.write_text('[Design]\nVersion=1.0\n[Document1]\nDocumentPath='+path.name+'\nAnnotationEnabled=1\n',encoding='utf-8')
    r=save('placement-probe-compile',bridge.compile_project(str(pr)))
    print('compile',r.get('success'),r.get('result',{}).get('net_source'))
    a=r.get('result',{}).get('pins',[])
    checks={('J901','A6'):'USB_DP',('J901','A7'):'USB_DN',('U901','7'):'USB_DN',('U901','8'):'USB_DP',('R901','1'):'CC1',('R901','2'):'GND',('D901','1'):'5V',('D901','2'):'USB_POWER'}
    actual={(p['ref'],p['pin']):p['net'] for p in a}
    print('checks',[(r,p,n,actual.get((r,p)),actual.get((r,p))==n) for (r,p),n in checks.items()])

def utility_probe():
    path=ROOT/'tools/altium/runtime/JTAG_UART_Placement_Probe.SchDoc'
    body=f'''SD:=Client.GetDocumentByPath({q(str(path))}); Doc:=SchServer.GetSchDocumentByPath({q(str(path))});
if (SD<>Nil) and (Doc<>Nil) then begin
Doc.UseCustomSheet:=True; Doc.CustomX:=MilsToCoord(600/0.0254); Doc.CustomY:=MilsToCoord(420/0.0254);
LogStep('probe native ports, power, and intended NC');
AddNamedPort(Doc,'USB_DP',MilsToCoord(430/0.0254),MilsToCoord(200/0.0254));
NameAt(Doc,'GND',MilsToCoord(430/0.0254),MilsToCoord(180/0.0254),True);
I:=Doc.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject;
while C<>Nil do begin if C.Designator.Text='J901' then NC(Doc,C,'A2'); C:=I.NextSchObject; end; Doc.SchIterator_Destroy(I);
SD.SetModified(True); if SD.DoFileSave('') then ResultText:='{{"saved":true}}'; end;'''
    run('utility-probe',body,CAD_DECL,CAD_HELPERS)

def graphics_probe():
    path=ROOT/'tools/altium/runtime/JTAG_UART_Placement_Probe.SchDoc'
    body=f"SD:=Client.OpenDocument('SCH',{q(str(path))}); Doc:=SchServer.GetSchDocumentByPath({q(str(path))}); if (SD<>Nil) and (Doc<>Nil) then begin\n"
    body+='I:=Doc.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject; while C<>Nil do begin\n'
    for ref,src in [('J901','usb'),('U901','ft'),('D901','diode')]:
        p,r=SOURCES[src];body+=f'if C.Designator.Text={q(ref)} then begin LogStep({q("copy native graphics "+ref)}); CopyGraphics(Doc,C,{q(str(ROOT/"ARTIX/ARTIX"/p))},{q(r)}); end;\n'
    body+="C:=I.NextSchObject; end; Doc.SchIterator_Destroy(I); SD.SetModified(True); if SD.DoFileSave('') then ResultText:='{\"saved\":true}'; end;"
    run('graphics-probe',body,CAD_DECL,CAD_HELPERS)
    saved=save('graphics-probe-saved',inspect(path));rr=saved['records']['FileHeader'];print('saved_graphics',len([r for r in rr if r.get('RECORD') in ['4','6','12','13','14']]))

def manifest():
    u=json.loads((OUT/'usb-review.json').read_text(encoding='utf-8'))
    f=json.loads((OUT/'ft-review.json').read_text(encoding='utf-8'))
    aliases={'VCC3V3':'3V3','5V_DC':'5V','FTDI_RESET_N':'FT_RESET_N','FTDI_REF':'FT_REF',
             'TCK_FPGA':'FPGA_TCK','TDI_FPGA':'FPGA_TDI','TDO_FPGA':'FPGA_TDO','TMS_FPGA':'FPGA_TMS'}
    norm=lambda n: aliases.get(n,n)
    cs=[]
    def add(ref,source,value,x,y,nets,**kw):
        cs.append(dict(ref=ref,source=source,value=value,x=x,y=y,nets={str(p):norm(n) for p,n in nets.items()},**kw))
    add('U14','usb','2345986-1',55,355,{p['pin']:p['net'] for p in u['connector']['physical_pins']})
    add('U30','esd','PUSB3FR4Z',65,200,{p['pin']:p['net'] for p in u['protection']['physical_pins']})
    add('U23','ft','FT2232HL-REEL',290,355,{p['physical_pin']:p['source_expected_net'] for p in f['pins']})
    add('U3','ee','93LC66B-I/SN',60,140,{'1':'EECS','2':'EECLK','3':'EEDATA','4':'EEPROM_DO','5':'GND','6':'3V3','7':None,'8':'3V3'})
    add('D22','diode','SS24',175,365,{'1':'5V','2':'USB_POWER'})
    add('X5','xtal','12MHz, CL=10pF',175,220,{'1':'FT_OSCI','2':'GND','3':'FT_OSCO','4':'GND'})
    specs=[('R448','5.1k',160,310,'USB_CC2','GND'),('R449','5.1k',195,310,'USB_CC1','GND'),
           ('R456','1k',215,270,'3V3','FT_RESET_N'),('R457','12k',215,245,'FT_REF','GND'),
           ('R225','10k',55,65,'3V3','EECS'),('R226','10k',90,65,'3V3','EECLK'),
           ('R227','10k',125,65,'3V3','EEPROM_DO'),('R228','2k',170,65,'EEDATA','EEPROM_DO')]
    for ref,v,x,y,top,bottom in specs:add(ref,'R1',v,x,y,{'1':bottom,'2':top})
    for ref,v,x,y,ends in [('FB3','BLM18SG121TN1D',430,280,('3V3','VPHY')),('FB4','BLM18SG121TN1D',515,280,('3V3','VPLL'))]:
        add(ref,'fb',v,x,y,dict(zip(['1','2'],ends)))
    banks=[('5V',355,[(160,'C851','10uF/10V'),(190,'C852','10uF/10V'),(220,'C853','0.1uF')]),
           ('3V3',350,[(430,'C324','4.7uF'),(455,'C325','0.1uF'),(480,'C301','0.1uF'),(505,'C302','0.1uF'),(530,'C303','0.1uF'),(555,'C304','0.1uF')]),
           ('VCC1V8_FT2232',305,[(430,'C291','4.7uF'),(465,'C298','0.1uF'),(500,'C299','0.1uF'),(535,'C300','0.1uF')]),
           ('VPHY',250,[(430,'C294','4.7uF'),(465,'C296','0.1uF')]),
           ('VPLL',250,[(515,'C295','4.7uF'),(550,'C297','0.1uF')]),
           ('3V3',115,[(175,'C308','0.1uF')]),
           ('FT_OSCI',160,[(175,'C326','27pF')]),('FT_OSCO',160,[(220,'C327','27pF')])]
    for i,(net,y,caps) in enumerate(banks):
        for x,ref,value in caps:add(ref,'C1',value,x,y,{'1':'GND','2':net},bank=i)
    assert len(cs)==36 and len(set(c['ref'] for c in cs))==36
    baseline=json.loads((OUT/'compile-before.json').read_text(encoding='utf-8'))
    assert not set(c['ref'] for c in cs)&set(p['ref'] for p in baseline['result']['pins'])
    save('manifest',{'source':'datasheets/Schematic_Smart_Artix_251120.pdf page7','aliases':aliases,'components':cs,'banks':banks,'notes':[
      'Source labels on physical FT2232HL pins26/27 and48/52 retained as FT_UART1/3 but are ACBUS/BCBUS, not additional UARTs.',
      'U30 pins6/7 internally NC, external same-net copper retained as in source; no internal feedthrough assumed.',
      'U3 pin6 NC tied3V3 as source; not ORG on B variants. EEPROM contents/programming not verified.',
      'X5 reuses passive four-pad crystal symbol/land pattern; 12MHz part selection and CL qualification pending.',
      '3V3/5V/GND use existing project power names; local1V8_FT2232 is separate from FPGA1V8.']})
    import csv
    with (OUT/'expected-pin-nets.csv').open('w',newline='',encoding='utf-8-sig') as st:
        w=csv.writer(st); w.writerow(['component','physical_pin','expected_project_net','source_sheet'])
        for c in cs:
            for p,n in c['nets'].items():w.writerow([c['ref'],p,n or 'NC','7'])
    print('manifest',len(cs),'components',sum(len(c['nets']) for c in cs),'pins')

def create_main():
    m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    path=ROOT/'ARTIX/ARTIX/07_JTAG_UART.SchDoc'
    body=create_header(path)
    notes=[(20,400,'JTAG & UART - Smart Artix reference, page 7'),(20,392,'FT2232HL: channel A JTAG / channel B UART. Physical pin numbers retained.'),
           (430,390,'FT2232HL power filtering / decoupling'),(20,375,'USB 2.0 Type-C'),(145,390,'USB power input'),
           (25,225,'USB ESD protection'),(25,160,'Microwire EEPROM'),(160,238,'12MHz crystal'),(430,205,'To FPGA / matching ports on sheets 02 and 03'),
           (20,42,'U30.6/7: internally NC; USB_DN/DP copper connected externally, per source and Nexperia pass-through layout.'),
           (20,34,'U3.6: internally NC on 93LC66B; source tie to 3V3 retained. R228 separates DI and DO.'),
           (20,26,'U23.26/27 and .48/52 retain PDF UART1/3 labels; on FT2232HL these are ACBUS/BCBUS, not extra UARTs.'),
           (20,18,'Only channel B UART (38/39) connects to FPGA R16/P15. X5 12MHz selection/CL and board layout remain to qualify.')]
    for x,y,s in notes:body+=f'Note(Doc,{x},{y},{q(s)});\n'
    for c in m['components']:body+=place(c)
    for net,y,caps in m['banks']:
        x1=caps[0][0]; x2=caps[-1][0]
        for yy,nn in [(y+15,net),(y-8,'GND')]:
            # Include a short extension for a single-capacitor bank.
            body+=f'AddWire(Doc,MilsToCoord({x1-5}/0.0254),MilsToCoord({yy}/0.0254),MilsToCoord({x2+5}/0.0254),MilsToCoord({yy}/0.0254));\n'
            body+=f'NameAt(Doc,{q(nn)},MilsToCoord({x1-5}/0.0254),MilsToCoord({yy}/0.0254),'+('True' if nn in ['3V3','5V','GND'] else 'False')+');\n'
    for i,net in enumerate(['FPGA_TCK','FPGA_TDI','FPGA_TDO','FPGA_TMS','FT_UART2_TX','FT_UART2_RX']):
        body+=f'AddNamedPort(Doc,{q(net)},MilsToCoord(465/0.0254),MilsToCoord({185-i*12}/0.0254));\n'
    body+=footer().replace("SD:=Client.OpenDocument('SCH',Doc.DocumentName)",f"SD:=Client.OpenDocument('SCH',{q(str(path))})")
    run('create-main',body,CAD_DECL,CAD_HELPERS,60)

def cross_ports():
    assert (OUT/'backups.json').exists()
    p2=ROOT/'ARTIX/ARTIX/02_FPGA_IO_Config.SchDoc';p3=ROOT/'ARTIX/ARTIX/03_FPGA_IO_Clock.SchDoc'
    body=''
    for path,kind in [(p2,'JTAG'),(p3,'UART')]:
        body+=f'''LogStep({q('checkpoint state '+path.name)}); SD:=Client.OpenDocument('SCH',{q(str(path))}); Doc:=SchServer.GetSchDocumentByPath({q(str(path))});
if (SD<>Nil) and (Doc<>Nil) then begin if not SD.Modified then begin
SchServer.ProcessControl.PreProcess(Doc,'JTAG UART ports'); try
'''
        if kind=='JTAG':
            for i,net in enumerate(['FPGA_TCK','FPGA_TDI','FPGA_TDO','FPGA_TMS']):
                body+=f'AddNamedPort(Doc,{q(net)},MilsToCoord(180/0.0254),MilsToCoord({175-i*12}/0.0254));\n'
            body+="Note(Doc,150,190,'JTAG to 07_JTAG_UART - existing FPGA_T* nets');\n"
        else:
            body+='''I:=Doc.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject; N:=0;
while C<>Nil do begin if (C.Designator.Text='U1') and (C.CurrentPartID=2) then begin
LogStep('connect UART only to verified U1B R16 and P15');
LabelPin(Doc,C,'R16','FT_UART2_TX'); LabelPin(Doc,C,'P15','FT_UART2_RX'); N:=N+1;
end; C:=I.NextSchObject; end; Doc.SchIterator_Destroy(I);
'''
            for i,net in enumerate(['FT_UART2_TX','FT_UART2_RX']):
                body+=f'AddNamedPort(Doc,{q(net)},MilsToCoord(180/0.0254),MilsToCoord({95-i*12}/0.0254));\n'
            body+="Note(Doc,150,108,'UART channel B to 07_JTAG_UART');\n"
        body+=f'''finally SchServer.ProcessControl.PostProcess(Doc,'JTAG UART ports'); end;
Doc.GraphicallyInvalidate; SD.SetModified(True); LogStep({q('save '+path.name)});
if SD.DoFileSave('') then begin Client.CloseDocument(SD); SD:=Client.OpenDocument('SCH',{q(str(path))}); end;
end else ResultText:='{{"error":"USER_DOCUMENT_MODIFIED"}}'; end;
'''
    body+="if ResultText='' then ResultText:='{\"ports_added\":6,\"uart_component_instances\":'+IntToStr(N)+'}';"
    run('cross-sheet-ports',body,CAD_DECL,CAD_HELPERS)

def publish():
    p=ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb'; s=ROOT/'ARTIX/ARTIX/07_JTAG_UART.SchDoc'
    body=f'''WS:=GetWorkspace; Prj:=WS.DM_OpenProject({q(str(p))},True);
if Prj<>Nil then begin Prj.DM_SetAsCurrentProject;
LogStep('add explicit verified sheet to MAIN ARTIX project');
if Prj.DM_IndexOfSourceDocument({q(str(s))})<0 then Prj.DM_AddSourceDocument({q(str(s))});
LogStep('native save MAIN ARTIX project only');
SD:=Client.GetDocumentByPath({q(str(p))});
if SD<>Nil then begin SD.SetModified(True); SD.DoFileSave(''); end
else begin ResetParameters; AddStringParameter('ObjectKind','FocusedProject'); AddStringParameter('SaveMode','Standard'); AddStringParameter('FileName',{q(str(p))}); RunProcess('WorkspaceManager:SaveObject'); end;
ResultText:='{{"source_index":'+IntToStr(Prj.DM_IndexOfSourceDocument({q(str(s))}))+',"logical_count":'+IntToStr(Prj.DM_LogicalDocumentCount)+'}}'; end;'''
    run('publish-main',body,'WS:IWorkspace; Prj:IProject; SD:IServerDocument;')

def compile_main():
    from project_api import compile_body
    b,d,h=compile_body(str(ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb'))
    b=b.replace("JStr(Pin.DM_FlattenedNetName)+'}'", "JStr(Pin.DM_FlattenedNetName)+',\"flat_index\":'+IntToStr(Pin.DM_NetIndex_Flat)+',\"document\":'+JStr(Doc.DM_FullPath)+'}'")
    req={'body':b,'declarations':d,'helpers':h,'timeout':60};save('compile-main-request',req)
    r=save('compile-main',bridge.run_script(**req))
    if not r.get('success'):print(json.dumps(r));return
    res=r['result'];print('net_source',res['net_source'],'DM_Compile',res['compiled'],'pins',len(res['pins']))
    m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    actual={(p['ref'],p['pin']):p for p in res['pins'] if p['document'].endswith('07_JTAG_UART.SchDoc')}
    checks=[]
    for c in m['components']:
        for p,n in c['nets'].items():
            a=actual.get((c['ref'],p)); found=a['net'] if a else None
            checks.append({'ref':c['ref'],'pin':p,'expected':n,'actual':found,'pass':(found==n if n else found in ['',None]) and a is not None})
    links=[]
    for ft,fpga in [('16','V12'),('17','R13'),('18','U13'),('19','T13'),('38','R16'),('39','P15')]:
        a=next((p for p in res['pins'] if p['ref']=='U23' and p['pin']==ft),None)
        z=next((p for p in res['pins'] if p['ref']=='U1' and p['pin']==fpga),None)
        links.append({'ft_pin':ft,'fpga_ball':fpga,'ft':a,'fpga':z,'pass':bool(a and z and a['flat_index']>=0 and a['flat_index']==z['flat_index'] and a['net']==z['net'])})
    stats=save('connectivity-check',{'net_source':res['net_source'],'pins_expected':len(checks),'connected_expected':sum(bool(x['expected']) for x in checks),'pin_checks':checks,'cross_sheet_checks':links,'all_pass':all(x['pass'] for x in checks+links)})
    print('mismatches',json.dumps([x for x in checks if not x['pass']]))
    print('crosslinks',[(x['ft_pin'],x['fpga_ball'],x['pass']) for x in links])
    print('messages',len(res['messages']));print(json.dumps([x for x in res['messages'] if x['document'].endswith('07_JTAG_UART.SchDoc') or x['class'] not in ['[Warning]','[Info]']],ensure_ascii=True))

def readback():
    from manifest import inspect_body
    r=save('main-readback',bridge.run_script(*inspect_body(str(ROOT/'ARTIX/ARTIX/07_JTAG_UART.SchDoc'))))
    print(r.get('success'),[(c['ref'],len(c['pins'])) for c in r.get('result',{}).get('components',[])])
    save('main-saved-records',inspect(ROOT/'ARTIX/ARTIX/07_JTAG_UART.SchDoc'))

def repair_main():
    path=ROOT/'ARTIX/ARTIX/07_JTAG_UART.SchDoc'
    save('before-graphics-repair-backup',{'path':bridge.backup_document(str(path))})
    m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    for c in m['components']:
        if c['ref']=='R457':c['y']=225
        if c['ref']=='U30':c['x']=55;c['y']=160
        if c['ref']=='U3':c['x']=50;c['y']=110
        if c['ref'] in ['R225','R226','R227']:c['y']=55
        if c['ref']=='D22':c['x']=180;c['y']=380
    save('manifest',m)
    body=f'''SD:=Client.OpenDocument('SCH',{q(str(path))}); Doc:=SchServer.GetSchDocumentByPath({q(str(path))});
if (SD<>Nil) and (Doc<>Nil) then begin if not SD.Modified then begin
N:=0; I:=Doc.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject;
while C<>Nil do begin N:=N+1; C:=I.NextSchObject; end; Doc.SchIterator_Destroy(I);
if N=36 then begin
SchServer.ProcessControl.PreProcess(Doc,'Repair owned generated sheet'); try
LogStep('remove only generated top-level wires labels power ports NC and notes');
I:=Doc.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eWire,eNetLabel,ePowerObject,ePort,eNoERC,eLabel)); G:=I.FirstSchObject; N:=0;
while (G<>Nil) and (N<2000) do begin H:=I.NextSchObject; if G.OwnerPartId=-1 then begin Doc.RemoveSchObject(G); N:=N+1; end; G:=H; end; Doc.SchIterator_Destroy(I);
LogStep('restore exact native library graphics and reflow components');
F:=SchServer.FontManager.GetFontID(10,0,False,False,False,False,'GOST Common');
I:=Doc.SchIterator_Create; I.AddFilter_ObjectSet(MkSet(eSchComponent)); C:=I.FirstSchObject;
while C<>Nil do begin
'''
    for c in m['components']:
        body+=f'''if C.Designator.Text={q(c['ref'])} then begin
C.MoveByXY(MilsToCoord({c['x']}/0.0254)-C.Location.X,MilsToCoord({c['y']}/0.0254)-C.Location.Y);
'''
        if c['source'] in SOURCES:
            p,r=SOURCES[c['source']];body+=f'CopyGraphics(Doc,C,{q(str(ROOT/"ARTIX/ARTIX"/p))},{q(r)});\n'
        for num,net in c['nets'].items():
            if 'bank' in c:body+=f'BankPin(Doc,C,{q(num)},MilsToCoord({c["y"]+(15 if num=="2" else -8)}/0.0254));\n'
            elif net:body+=f'LabelPin(Doc,C,{q(num)},{q(net)});\n'
            else:body+=f'NC(Doc,C,{q(num)});\n'
        body+='end;\n'
    body+='C:=I.NextSchObject; end; Doc.SchIterator_Destroy(I);\n'
    original=json.loads((OUT/'create-main-request.json').read_text(encoding='utf-8'))['body']
    for line in original.splitlines():
        if line.startswith(('Note(Doc,','AddWire(Doc,','NameAt(Doc,','AddNamedPort(Doc,')):
            if 'USB power input' in line:continue
            line=line.replace("Note(Doc,25,225,", "Note(Doc,25,175,").replace("Note(Doc,25,160,", "Note(Doc,25,125,")
            body+=line+'\n'
    body+=f'''finally SchServer.ProcessControl.PostProcess(Doc,'Repair owned generated sheet'); end;
Doc.GraphicallyInvalidate; SD.SetModified(True); LogStep('save repaired native main sheet');
if SD.DoFileSave('') then begin Client.CloseDocument(SD); SD:=Client.OpenDocument('SCH',{q(str(path))}); ResultText:='{{"saved_and_reopened":true}}'; end;
end else ResultText:='{{"error":"UNEXPECTED_COMPONENT_COUNT"}}';
end else ResultText:='{{"error":"USER_DOCUMENT_MODIFIED"}}'; end;'''
    run('repair-main',body,CAD_DECL+'G,H:ISch_GraphicalObject;',CAD_HELPERS,60)

def sources():
    from library_api import inspect_library
    for k,(p,c) in SOURCES.items():
        r=save('source-native-'+k,inspect_library(bridge,str(ROOT/'ARTIX/ARTIX'/p),c))
        print(k, json.dumps({a:b for a,b in r.items() if a!='result'}))
        if not r.get('success'): break

if __name__=='__main__':
    if sys.argv[1]=='inventory': inventory()
    elif sys.argv[1]=='preflight': preflight()
    elif sys.argv[1]=='sources': sources()
    elif sys.argv[1]=='fixture': fixture()
    elif sys.argv[1]=='verify-fixture': verify_fixture()
    elif sys.argv[1]=='utility-probe': utility_probe()
    elif sys.argv[1]=='graphics-probe': graphics_probe()
    elif sys.argv[1]=='manifest': manifest()
    elif sys.argv[1]=='create-main': create_main()
    elif sys.argv[1]=='cross-ports': cross_ports()
    elif sys.argv[1]=='publish': publish()
    elif sys.argv[1]=='compile-main': compile_main()
    elif sys.argv[1]=='readback': readback()
    elif sys.argv[1]=='repair-main': repair_main()
    elif sys.argv[1]=='compile-before':
        r=save('compile-before',bridge.compile_project(str(ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb')))
        print(json.dumps({k:v for k,v in r.items() if k!='result'})); print(json.dumps({k:v for k,v in r.get('result',{}).items() if k!='pins'}))
    elif sys.argv[1]=='request':
        p=Path(sys.argv[2]); req=json.loads(p.read_text(encoding='utf-8')); run(p.stem+'-result',**{'body':req['body'],'decl':req.get('declarations',''),'helpers':req.get('helpers',HELPERS),'timeout':req.get('timeout',40)})
