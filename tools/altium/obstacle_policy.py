"""Separate code repairs from suspected external constraints; never replay writes."""
from functools import wraps
from urllib.error import HTTPError, URLError


def failure_in(value):
    if isinstance(value, dict):
        if (value.get('success') is False or value.get('error') or
                value.get('compiled') is False or value.get('executor_blocked') is True):
            return value
        for child in value.values():
            failed = failure_in(child)
            if failed is not None:
                return failed
    return None


def handoff(result, action, source_url=None):
    failed = failure_in(result)
    if failed is None or result.get('user_decision_required'):
        return result
    result = dict(result)
    error = failed.get('error') or ('EXECUTOR_RECOVERY_REQUIRED' if failed.get('executor_blocked')
                                  else 'OPERATION_NOT_VERIFIED')
    evidence = [str(error)]
    for key in ('message', 'last_step', 'state', 'job_dir', 'exception_type', 'http_status'):
        if key in failed:
            evidence.append(f'{key}: {failed[key]}')
    download = action in {'download_and_prepare', 'prepare', 'download-component', 'prepare-component'}
    if download:
        ai = 'Evaluate another public CAD source for the same MPN after your choice; no component substitution.'
        human = 'Open the provider page, download the Altium symbol and footprint, then provide the local file path.'
        unknown = 'HTTP/network errors alone do not establish VPN, proxy, account or provider restrictions.'
    elif error == 'WINDOWS_DESKTOP_UNAVAILABLE':
        ai = 'Use saved-file readers for the available read-only work after your choice.'
        human = 'Unlock the Windows desktop, then confirm readiness to resume.'
        unknown = 'The bridge cannot unlock Windows or confirm unsaved editor state.'
    else:
        ai = 'Review local logs and saved copies, then propose a specific code/API correction or saved-file route after your choice.'
        human = 'Inspect the Altium error and version; save unsaved work and stop the failed script if needed, then report the outcome.'
        unknown = 'A failed CAD call does not establish version incompatibility; partial unsaved changes may exist.'
    external = error in {'HTTP_DOWNLOAD_BLOCKED', 'NETWORK_DOWNLOAD_FAILED',
                        'WINDOWS_DESKTOP_UNAVAILABLE', 'ALTIUM_EXE_MISSING',
                        'ALTIUM_NOT_RUNNING', 'MULTIPLE_ALTIUM_EDITORS',
                        'SCRIPT_FAILED_OR_BLOCKED', 'EXECUTOR_RECOVERY_REQUIRED'}
    result.update(status='EXTERNAL_CONSTRAINT_SUSPECTED' if external else 'CODE_REPAIR_REQUIRED',
                  user_decision_required=external, notify_user=external,
                  failure_category='external_or_ambiguous' if external else 'code_or_input',
                  automatic_retry_allowed=False, action=action,
                  obstacle={'evidence': evidence, 'uncertainty': unknown},
                  next_steps=[{'id': 'ai_workaround', 'description': ai},
                              {'id': 'human_handoff', 'description': human}],
                  resume_condition=('Explain evidence and uncertainty; wait if human action or a new strategy is required.'
                                    if external else 'Diagnose and correct code autonomously; verify state before retrying. Stop after 3 attempts without new evidence or 10 minutes without progress.'))
    if not external:
        result['next_steps'] = [{'id': 'ai_code_repair', 'description':
                                'Correct code or input autonomously; no permission question for routine repairs.'}]
    if source_url:
        result['source_url'] = source_url
    return result


def guard_action(function):
    """One invocation only; convert exceptions and failed outcomes at tool boundaries."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
        except Exception as exc:
            result = {'success': False, 'error': type(exc).__name__,
                      'exception_type': type(exc).__name__}
            if isinstance(exc, HTTPError):
                result.update(error='HTTP_DOWNLOAD_BLOCKED', http_status=exc.code,
                              message=f'Provider returned HTTP {exc.code}; no retry was performed.')
            elif isinstance(exc, URLError):
                result.update(error='NETWORK_DOWNLOAD_FAILED',
                              message='The HTTPS request failed; the cause is not established.')
            else:
                result['message'] = str(exc)[:1500]
        source_url = None
        if function.__name__ in {'prepare', 'download_and_prepare'}:
            source_url = kwargs.get('url', kwargs.get('source_url'))
            if source_url is None and len(args) > 2:
                source_url = args[2]
        return handoff(result, function.__name__, source_url)
    return wrapped
