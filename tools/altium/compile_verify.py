"""Verify reconstructed pin/net mapping using Altium's own project compiler."""
import json
import sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
import cad_bridge
from manifest import q
root=BASE.parents[1]/'ARTIX/ARTIX'
sheet=sys.argv[1] if len(sys.argv)>1 else 'Clock_Flash.SchDoc'
project=root/('CodexGenerated/ARTIX_Codex'+('_Verified' if len(sys.argv)>1 else '')+'.PrjPcb')
if not project.exists():
    original=(root/'ARTIX.PrjPcb').read_text(encoding='utf-8-sig')
    if '[Document1]' in original: raise RuntimeError('Source project is no longer empty')
    project.write_text(original+'\n[Document1]\nDocumentPath='+sheet+'\nAnnotationEnabled=1\nDoLibraryUpdate=1\n',encoding='utf-8')
decl='WS: IWorkspace; Prj: IProject; Doc: IDocument; Comp: IComponent; Pin: IPin; I,J,K: Integer; S: String; OK: Boolean;'
helpers='''function JStr(S: String): String;
begin S := StringReplace(S, '\\', '\\\\', 1); S := StringReplace(S, '"', '\\"', 1); Result := '"'+S+'"'; end;'''
body=f'''
LogStep('open dedicated generated project');
WS := GetWorkspace; Prj := WS.DM_OpenProject({q(str(project))},True);
if Prj = Nil then Exit;
LogStep('compile dedicated generated project'); OK := Prj.DM_Compile;
LogStep('read compiled nets'); S := '[';
for I := 0 to Prj.DM_PhysicalDocumentCount-1 do begin
  Doc := Prj.DM_PhysicalDocuments(I);
  for J := 0 to Doc.DM_ComponentCount-1 do begin
    Comp := Doc.DM_Components(J);
    for K := 0 to Comp.DM_PinCount-1 do begin
      Pin := Comp.DM_Pins(K);
      if S <> '[' then S := S+',';
      S := S+'{{"ref":'+JStr(Comp.DM_PhysicalDesignator)+',"pin":'+JStr(Pin.DM_PinNumber)+',"net":'+JStr(Pin.DM_FlattenedNetName)+'}}';
    end;
  end;
end;
S := S+']';
if OK then ResultText := '{{"compiled":true,"pins":'+S+'}}' else ResultText := '{{"compiled":false,"pins":'+S+'}}';
'''
result=cad_bridge.run_script(body,decl,helpers)
manifest=json.loads((Path(__file__).parent/'manifests/clock_flash.json').read_text())
if result['success']:
    actual={(p['ref'],p['pin']):p['net'] for p in result['result']['pins']}
    checks=[]
    for c in manifest['components']:
        for p in c['pins']:
            if p.get('net'):
                found=actual.get((c['ref'],str(p['number'])))
                checks.append({'ref':c['ref'],'pin':str(p['number']),'expected':p['net'],'actual':found,'pass':found==p['net']})
    result['checks']=checks
    result['all_nets_match']=bool(checks) and all(p['pass'] for p in checks)
(BASE/'runtime/compiler-connectivity-test.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
