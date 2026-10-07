"""Reversible isolation of the two explicitly user-authorized Altium add-ons."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid


def restore_loader():
    """Restore only the explicitly requested loader; preserve other add-on state."""
    records = json.loads((BACKUP / 'state.json').read_text(encoding='utf-8'))
    record = next(r for r in records if Path(r['path']).name == 'AltiumLL.vbs')
    saved = BACKUP / 'AltiumLL.vbs'
    loader = Path(record['path'])
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if digest(saved) != record['sha256']:
        raise RuntimeError('Library Loader backup checksum mismatch')
    current = digest(loader)
    if current not in {record['sha256'], record['disabled_sha256']}:
        raise RuntimeError('Library Loader changed after isolation; review before restoring')
    if current != record['sha256']:
        checkpoint = BASE / 'runtime/backups' / ('enable-loader-' + uuid.uuid4().hex)
        checkpoint.mkdir(parents=True)
        shutil.copy2(loader, checkpoint / loader.name)
        shutil.copy2(saved, loader)
    if digest(loader) != record['sha256']:
        raise RuntimeError('Library Loader restore readback failed')
    record['loader_restored'] = True
    (BACKUP / 'state.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(json.dumps({'success': True, 'loader_enabled_on_disk': True,
                      'path': str(loader), 'sha256': digest(loader),
                      'editor_restarted': False, 'other_addons_modified': False}, indent=2))

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
    allowed = {records[1]['disabled_sha256']}
    if records[1].get('loader_restored'):
        allowed.add(records[1]['sha256'])
    if loader.exists() and hashlib.sha256(loader.read_bytes()).hexdigest() not in allowed:
        raise RuntimeError('Library Loader changed after isolation; review before restoring')
    for r in records:
        shutil.copy2(r['backup'], r['path'])
    disabled = Path(records[0]['path']).with_suffix('.ins.codex-disabled')
    if disabled.exists():
        disabled.unlink()
    print('Restored original add-on files; restart Altium normally')

if __name__ == '__main__':
    import sys
    {'isolate': isolate, 'restore': restore, 'restore-loader': restore_loader}[sys.argv[1]]()
