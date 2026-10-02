"""Reversible isolation of the two explicitly user-authorized Altium add-ons."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

BASE = Path(__file__).resolve().parent
BACKUP = BASE / 'runtime/addon-backup'
GOST = Path(r'C:\ProgramData\Altium\Altium Designer {A05D34BC-9351-489A-A352-B954DF52075E}\Extensions\GOST BOM\GOSTBOM2.ins')
LOADER = Path.home()/'Documents/AltiumLL/AltiumLL.vbs'

def isolate():
    BACKUP.mkdir(parents=True, exist_ok=True)
    if (BACKUP / 'state.json').exists():
        raise RuntimeError('Isolation already recorded; restore before repeating')
    records = []
    for source in [GOST, LOADER]:
        saved = BACKUP / source.name
        shutil.copy2(source, saved)
        records.append({'path': str(source), 'backup': str(saved), 'sha256': hashlib.sha256(saved.read_bytes()).hexdigest()})
    raw = LOADER.read_bytes()
    marker = b'Sub Prechecks'
    start = raw.lower().find(marker.lower())
    if start < 0:
        raise RuntimeError('Library Loader entry point not found')
    end = raw.find(b'\n', start)
    raw = raw[:end+1] + b"    ' Temporarily disabled by Codex at user request.\r\n    Exit Sub\r\n" + raw[end+1:]
    LOADER.write_bytes(raw)
    records[1]['disabled_sha256'] = hashlib.sha256(raw).hexdigest()
    GOST.rename(GOST.with_suffix('.ins.codex-disabled'))
    (BACKUP / 'state.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(json.dumps({'isolated': records}, indent=2))

def restore():
    records = json.loads((BACKUP / 'state.json').read_text(encoding='utf-8'))
    for r in records:
        r['backup'] = str(BACKUP / Path(r['backup']).name)
        if hashlib.sha256(Path(r['backup']).read_bytes()).hexdigest() != r['sha256']:
            raise RuntimeError('Backup checksum mismatch')
    loader = Path(records[1]['path'])
    if loader.exists() and hashlib.sha256(loader.read_bytes()).hexdigest() != records[1]['disabled_sha256']:
        raise RuntimeError('Library Loader changed after isolation; review before restoring')
    for r in records:
        shutil.copy2(r['backup'], r['path'])
    disabled = Path(records[0]['path']).with_suffix('.ins.codex-disabled')
    if disabled.exists():
        disabled.unlink()
    print('Restored original add-on files; restart Altium normally')

if __name__ == '__main__':
    import sys
    {'isolate': isolate, 'restore': restore}[sys.argv[1]]()
