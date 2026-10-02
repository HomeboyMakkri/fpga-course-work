"""Native project compiler with real pin nets and compiler messages."""
from manifest import q

def compile_body(path):
    decl='WS: IWorkspace; Prj: IProject; Doc: IDocument; SD: IServerDocument; Comp: IComponent; Pin: IPin; M: IMessagesManager; MI: IMessageItem; I,J,K,N: Integer; S,T,U: String; OK: Boolean;'
    helpers=r'''function JStr(S: String): String;
begin
S := StringReplace(S, '\', '\\', 1);
S := StringReplace(S, '"', '\"', 1);
S := StringReplace(S, #13, '\r', 1); S := StringReplace(S, #10, '\n', 1);
Result := '"'+S+'"';
end;'''
    body=f'''
LogStep('open explicit project');
WS := GetWorkspace; Prj := WS.DM_OpenProject({q(path)},True);
if Prj = Nil then Exit;
LogStep('load project schematic documents');
for I := 0 to Prj.DM_LogicalDocumentCount-1 do begin
  Doc := Prj.DM_LogicalDocuments(I);
  if UpperCase(ExtractFileExt(Doc.DM_FullPath)) = '.SCHDOC' then SD := Client.OpenDocument('SCH',Doc.DM_FullPath);
end;
LogStep('compile explicit project'); OK := Prj.DM_Compile;
LogStep('read compiled nets'); S := '[';
N := Prj.DM_PhysicalDocumentCount; U := 'physical';
if N = 0 then begin N := Prj.DM_LogicalDocumentCount; U := 'logical'; end;
for I := 0 to N-1 do begin
  if U = 'physical' then Doc := Prj.DM_PhysicalDocuments(I) else Doc := Prj.DM_LogicalDocuments(I);
  for J := 0 to Doc.DM_ComponentCount-1 do begin
    Comp := Doc.DM_Components(J);
    for K := 0 to Comp.DM_PinCount-1 do begin
      Pin := Comp.DM_Pins(K); if S <> '[' then S := S+',';
      S := S+'{{"ref":'+JStr(Comp.DM_PhysicalDesignator)+',"pin":'+JStr(Pin.DM_PinNumber)+',"net":'+JStr(Pin.DM_FlattenedNetName)+'}}';
    end;
  end;
end;
S := S+']'; T := '['; M := WS.DM_MessagesManager;
for I := 0 to M.MessagesCount-1 do begin
  MI := M.Messages(I); if T <> '[' then T := T+',';
  T := T+'{{"class":'+JStr(MI.MsgClass)+',"text":'+JStr(MI.Text)+',"document":'+JStr(MI.Document)+'}}';
end;
T := T+']';
if OK then ResultText := '{{"compiled":true,"net_source":'+JStr(U)+',"document_count":'+IntToStr(N)+',"pins":'+S+',"messages":'+T+'}}' else ResultText := '{{"compiled":false,"net_source":'+JStr(U)+',"document_count":'+IntToStr(N)+',"pins":'+S+',"messages":'+T+'}}';
'''
    return body,decl,helpers
