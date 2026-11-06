from pathlib import Path
from zipfile import ZipFile,is_zipfile
from lxml import etree as E
from copy import deepcopy
import io
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
backup=Path('.work-docs/update-20260925');backup.mkdir(parents=True,exist_ok=True)
for f in list(Path('documents').glob('*.docx')):
 if not is_zipfile(f):continue
 raw=f.read_bytes();(backup/f.name).write_bytes(raw)
 with ZipFile(io.BytesIO(raw)) as z:
  r=E.fromstring(z.read('word/document.xml'))
  p=next(p for p in r.xpath('//w:p',namespaces=ns) if 'Рогозин' in ''.join(p.xpath('.//w:t/text()',namespaces=ns)))
  row=p.getparent().getparent(); assistant=deepcopy(row); caption=deepcopy(row.getnext())
  ts=p.xpath('.//w:t',namespaces=ns);ts[0].text='Сергеева А.А.'
  for t in ts[1:]:t.text=''
  first=assistant.xpath('./w:tc',namespaces=ns)[0];ts=first.xpath('.//w:t',namespaces=ns);ts[0].text='Ассистент'
  for t in ts[1:]:t.text=''
  anchor=row.getnext();anchor.addnext(assistant);assistant.addnext(caption)
  result=io.BytesIO()
  with ZipFile(result,'w') as zz:
   for entry in z.infolist():zz.writestr(entry,E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True) if entry.filename=='word/document.xml' else z.read(entry))
  try:f.write_bytes(result.getvalue())
  except PermissionError:
   f=f.with_stem(f.stem+'_обновлено');f.write_bytes(result.getvalue())
  print(str(f).encode('ascii','backslashreplace').decode())
