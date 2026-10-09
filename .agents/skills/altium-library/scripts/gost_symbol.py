"""Skill entrypoint; implementation maintained only in repository tools/altium."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/altium'))
from gost_symbol import main
if __name__=='__main__': raise SystemExit(main())
