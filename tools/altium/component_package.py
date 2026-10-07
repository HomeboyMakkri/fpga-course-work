"""Preserve downloaded CAD originals and prepare an editable native-library copy."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[2] / 'ARTIX/ARTIX/libraries'
MAX_BYTES = 200 * 1024 * 1024
CAD = {'.schlib', '.pcblib', '.intlib', '.libpkg', '.step', '.stp'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(mpn, manufacturer, source_url, downloaded_path, root=ROOT):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._ -]{0,119}', mpn) or mpn.endswith(('.', ' ')):
        raise ValueError('MPN must be a single valid Windows folder name')
    if mpn.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}:
        raise ValueError('Reserved Windows folder name')
    if urlsplit(source_url).scheme != 'https' or not urlsplit(source_url).hostname:
        raise ValueError('Record the actual HTTPS download/source URL')
    source = Path(downloaded_path).resolve()
    if not source.is_file() or source.stat().st_size > MAX_BYTES:
        raise ValueError('Missing or oversized downloaded file')
    target = Path(root).resolve() / mpn
    if target.exists():
        raise FileExistsError('Component folder already exists; do not overwrite original or new')
    # Stage before publishing so failed ZIP validation does not leave a usable-looking package.
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent, prefix='.cad-package-') as staging:
        stage = Path(staging)
        original, new = stage / 'original', stage / 'new'
        original.mkdir(); new.mkdir()
        shutil.copy2(source, original / source.name)
        if zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                entries = archive.infolist()
                if len(entries) > 5000 or sum(i.file_size for i in entries) > MAX_BYTES:
                    raise ValueError('Archive exceeds extraction limits')
                for entry in entries:
                    name = PurePosixPath(entry.filename.replace('\\', '/'))
                    if name.is_absolute() or '..' in name.parts or any(':' in part for part in name.parts):
                        raise ValueError('Unsafe archive path')
                    if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError('Archive symbolic links are unsupported')
                    if not entry.is_dir():
                        dest = original / 'extracted' / Path(*name.parts)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(entry) as stream, dest.open('xb') as out:
                            shutil.copyfileobj(stream, out)
            copy_root = original / 'extracted'
        else:
            copy_root = original
        files = [p for p in copy_root.rglob('*') if p.is_file()]
        if not any(p.suffix.lower() in CAD for p in files):
            raise ValueError('Download has no Altium library or linked CAD assets; HTML/PDF is not a CAD model')
        for path in files:
            dest = new / path.relative_to(copy_root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        hashes = {str(p.relative_to(original)): sha(p) for p in original.rglob('*') if p.is_file()}
        report = {'mpn': mpn, 'manufacturer': manufacturer, 'source_url': source_url,
                  'download_sha256': sha(source), 'original_hashes': hashes,
                  'status': 'COPIED_UNVERIFIED', 'native_schlibs': [str(p.relative_to(new)) for p in new.rglob('*') if p.suffix.lower() == '.schlib'],
                  'note': 'Exact MPN, pin map, footprint/model links and GOST rendering require verification. Extract IntLib through Altium if no SchLib is supplied.'}
        (stage / 'component.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        # mkdir is exclusive; avoids overwriting a concurrent package.
        target.mkdir()
        for p in stage.iterdir():
            shutil.move(str(p), str(target / p.name))
    return {'success': True, 'path': str(target), **report}


def download_and_prepare(mpn, manufacturer, url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('A public HTTPS CAD download URL without credentials is required')
    with tempfile.TemporaryDirectory() as temp:
        with urlopen(url, timeout=30) as response:
            if urlsplit(response.url).scheme != 'https':
                raise ValueError('Download redirected away from HTTPS')
            name = Path(urlsplit(response.url).path).name or 'cad-download.zip'
            dest = Path(temp) / name
            total = 0
            with dest.open('xb') as out:
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError('Download exceeds size limit')
                    out.write(chunk)
        return prepare(mpn, manufacturer, url, str(dest))


def verify_original(package_path):
    target = Path(package_path).resolve()
    report = json.loads((target / 'component.json').read_text(encoding='utf-8'))
    original = target / 'original'
    actual = {str(p.relative_to(original)): sha(p) for p in original.rglob('*') if p.is_file()}
    return {'success': actual == report['original_hashes'], 'original_unchanged': actual == report['original_hashes'],
            'package_path': str(target)}
