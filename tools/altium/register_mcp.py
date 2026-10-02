"""Point the user MCP registration at this repo; preserve unrelated settings."""
from pathlib import Path
import os
import re
import shutil
import time
import tomllib

BASE = Path(__file__).resolve().parent
cfg = Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'config.toml'
text = cfg.read_text(encoding='utf-8-sig') if cfg.exists() else ''
before = tomllib.loads(text)
sections = re.split(r'(?m)(?=^\[)',text)
kept = []
for section in sections:
    header = section.splitlines()[0].strip() if section else ''
    if re.match(r'^\[mcp_servers\.altium_local(?:\]|\.)',header):
        continue
    kept.append(section)
addition = f"""

[mcp_servers.altium_local]
command = 'py'
args = ['-3.13', '{BASE / 'launch_mcp.py'}']
cwd = '{BASE.parents[1]}'
enabled = true
startup_timeout_sec = 240
tool_timeout_sec = 120
"""
updated = ''.join(kept).rstrip()+'\n'+addition
after = tomllib.loads(updated)
for parsed in (before,after):
    parsed.get('mcp_servers',{}).pop('altium_local',None)
    if not parsed.get('mcp_servers'):
        parsed.pop('mcp_servers',None)
if before != after:
    raise RuntimeError('Unrelated settings would change; registration stopped')
backup = BASE/'runtime/config-backups'/('codex-'+time.strftime('%Y%m%d-%H%M%S')+'.toml')
backup.parent.mkdir(parents=True,exist_ok=True)
if cfg.exists():
    shutil.copy2(cfg,backup)
cfg.parent.mkdir(parents=True,exist_ok=True)
temporary = cfg.with_suffix('.altium-tmp')
temporary.write_text(updated,encoding='utf-8')
temporary.replace(cfg)
print('Registered altium_local from repository:',BASE)
print('Private config backup (git ignored):',backup)
