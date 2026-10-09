"""Read-only inventory of saved Altium libraries; never writes CAD files."""
from pathlib import Path
import hashlib, json, struct, sys
import olefile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def records(data):
    pos = 0
    result = []
    while pos + 4 <= len(data):
        header = struct.unpack_from('<I', data, pos)[0]
        length = header & 0xFFFFFF
        if pos + 4 + length > len(data):
            break
        payload = data[pos+4:pos+4+length]
        pos += 4 + length
        if header >> 24:
            continue
        fields = dict(p.split('=',1) for p in payload.rstrip(b'\0').decode('latin1').split('|') if '=' in p)
        if fields:
            result.append(fields)
    return result

def inspect(path):
    row = {'path':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'size':path.stat().st_size}
    with olefile.OleFileIO(str(path)) as ole:
        row['streams'] = ['/'.join(s) for s in ole.listdir()]
        row['records'] = {}
        for s in ole.listdir():
            if s[-1].lower() in {'data','header','fileheader','sectionkeys','library'}:
                rec = records(ole.openstream(s).read())
                if rec:
                    row['records']['/'.join(s)] = rec
    return row

def main():
    paths = [ROOT/'ARTIX/ARTIX/libraries/X7/XC7A50T-2FGG484I.SchLib',
             ROOT/'ARTIX/ARTIX/libraries/X7/BGA484C100P22X22_2300X2300X260.PcbLib',
             ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/Schlib1.SchLib',
             ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/ASV-50MHz-GOST.SchLib',
             ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/PcbLib1.PcbLib',
             ROOT/'ARTIX/ARTIX/libraries/W25Q128JV/source/W25Q128JVSIQ.SchLib',
             ROOT/'ARTIX/ARTIX/libraries/W25Q128JV/source/SOIC127P790X216-8N.PcbLib',
             ROOT/'ARTIX/ARTIX/libraries/FB BLM18SG121TN1D/FB.SchLib',
             ROOT/'ARTIX/ARTIX/libraries/FB BLM18SG121TN1D/FB.PcbLib']
    data = [inspect(p) for p in paths]
    (OUT/'evidence').mkdir(parents=True,exist_ok=True)
    (OUT/'evidence/saved-library-inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in data:
        components = []
        models = []
        for key, recs in row['records'].items():
            for rec in recs:
                upper = {k.upper():v for k,v in rec.items()}
                if upper.get('RECORD') == '1': components.append({k:v for k,v in upper.items() if k in {'LIBREFERENCE','PARTCOUNT','COMPONENTDESCRIPTION','DESIGNATOR','COMMENT'}})
                if upper.get('RECORD') == '45': models.append(upper)
        print(json.dumps({'path':row['path'],'components':components,'models':models,'streams':row['streams'] if not components else None},ensure_ascii=True))

if __name__ == '__main__': main()
