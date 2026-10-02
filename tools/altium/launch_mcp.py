"""Bootstrap dependencies, then hand unchanged stdio to the native MCP server."""
from pathlib import Path
import os
import subprocess
import sys

base = Path(__file__).resolve().parent
result = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(base/'setup.ps1')],
                        stdin=subprocess.DEVNULL,stdout=sys.stderr,stderr=sys.stderr,
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
if result.returncode:
    raise SystemExit(result.returncode)
python = base/'.venv/Scripts/python.exe'
os.execv(str(python),[str(python),str(base/'cad_bridge.py'),'serve'])
