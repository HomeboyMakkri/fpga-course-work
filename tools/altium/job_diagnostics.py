"""Offline job diagnosis and conservative DelphiScript preflight."""
import json
import re
from pathlib import Path


def preflight(body, declarations='', helpers=''):
    # Only reject demonstrated interpreter hazards, not unfamiliar CAD APIs.
    source = '\n'.join((declarations, helpers, body))
    source = re.sub(r"'(?:''|[^'])*'|\{[^}]*\}|\(\*.*?\*\)|//[^\n]*", ' ', source, flags=re.S)
    hazards = [
        (r'\braise\s+Exception\.Create\b', 'Use a structured error result; this interpreter rejected raise Exception.Create.'),
        (r'\bDoFileLoad\b', 'Use checkpoint/save and close/reopen of the non-dirty target; DoFileLoad duplicated library components.'),
        (r'\beSheetCustom\b', 'Use the verified UseCustomSheet property.'),
    ]
    return [{'pattern': pattern, 'reason': reason} for pattern, reason in hazards
            if re.search(pattern, source, re.I)]


def diagnose(job, editor_alive=None):
    job = Path(job)
    steps = (job / 'steps.txt').read_text(encoding='cp1251', errors='replace').splitlines() if (job / 'steps.txt').exists() else []
    output = job / 'result.txt'
    if output.exists() and steps and steps[-1] == 'FINISHED':
        state = 'FINISHED'
    elif editor_alive is False:
        state = 'EDITOR_EXITED'
    elif not steps:
        state = 'NOT_STARTED'
    elif 'EXCEPTION' in steps:
        state = 'RUNTIME_EXCEPTION'
    else:
        state = 'STARTED_WITHOUT_COMPLETION'
    result = {'job_dir': str(job), 'state': state, 'last_step': steps[-1] if steps else 'NOT_STARTED',
              'steps': steps, 'result_exists': output.exists(), 'editor_alive': editor_alive,
              'automatic_replay_safe': False,
              'files': [str(p) for p in job.iterdir() if p.is_file()]}
    if output.exists():
        raw = output.read_text(encoding='cp1251', errors='replace').strip()
        try:
            result['result'] = json.loads(raw)
        except ValueError:
            result['result'] = raw
    return result
