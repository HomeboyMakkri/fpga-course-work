"""Offline regression checks: provenance, copies, ZIP boundaries and failure guards."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from component_package import prepare, verify_original
from job_diagnostics import diagnose, preflight
import cad_bridge


class WorkflowTests(unittest.TestCase):
    def test_code_repair_is_autonomous_and_network_not_assumed_vpn(self):
        from obstacle_policy import guard_action
        from urllib.error import HTTPError
        @guard_action
        def broken_code():
            raise ValueError('Wrong local path')
        result = broken_code()
        self.assertFalse(result['user_decision_required'])
        self.assertEqual(result['status'], 'CODE_REPAIR_REQUIRED')
        calls = []
        @guard_action
        def download_and_prepare():
            calls.append(1)
            raise HTTPError('https://example.org', 403, 'Forbidden', {}, None)
        result = download_and_prepare()
        self.assertEqual(len(calls), 1)
        self.assertTrue(result['notify_user'])
        self.assertEqual(result['http_status'], 403)
        self.assertIn('do not establish VPN', result['obstacle']['uncertainty'])

    def test_nested_cad_failure_and_success(self):
        from obstacle_policy import handoff
        result = handoff({'live_check': {'success': False, 'error': 'SCRIPT_FAILED_OR_BLOCKED'}}, 'status')
        self.assertTrue(result['notify_user'])
        self.assertFalse(result['automatic_retry_allowed'])
        okay = {'success': True, 'result': {'pin_count': 4}}
        self.assertEqual(handoff(okay, 'inspect'), okay)

    def test_copy_keeps_links_and_detects_original_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'download.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('library/device.SchLib', b'native-test-fixture')
                z.writestr('library/models/device.PcbLib', b'footprint-test-fixture')
                z.writestr('library/models/device.step', b'step-test-fixture')
            result = prepare('TEST-1', 'Vendor', 'https://example.org/model.zip', str(archive), root / 'libraries')
            package = Path(result['path'])
            self.assertTrue(verify_original(package)['original_unchanged'])
            self.assertEqual((package / 'new/library/models/device.PcbLib').read_bytes(), b'footprint-test-fixture')
            (package / 'new/library/device.SchLib').write_bytes(b'formatted')
            self.assertTrue(verify_original(package)['original_unchanged'])
            with self.assertRaises(FileExistsError):
                prepare('TEST-1', 'Vendor', 'https://example.org/model.zip', str(archive), root / 'libraries')
            (package / 'original/extracted/library/device.SchLib').write_bytes(b'tampered')
            self.assertFalse(verify_original(package)['original_unchanged'])

    def test_zip_traversal_and_html_are_not_imported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('../outside.SchLib', b'x')
            with self.assertRaises(ValueError):
                prepare('TEST', 'Vendor', 'https://example.org/model.zip', str(archive), root / 'libraries')
            self.assertFalse((root / 'libraries/TEST').exists())
            html = root / 'login.html'; html.write_text('<html>Login</html>')
            with self.assertRaises(ValueError):
                prepare('TEST', 'Vendor', 'https://example.org/login', str(html), root / 'libraries')
            self.assertFalse((root / 'libraries/TEST').exists())

    def test_diagnosis_preserves_uncertainty_and_late_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            job = Path(temp)
            self.assertEqual(diagnose(job, True)['state'], 'NOT_STARTED')
            (job / 'steps.txt').write_text('START\ncreate pad\n')
            self.assertEqual(diagnose(job, True)['state'], 'STARTED_WITHOUT_COMPLETION')
            self.assertEqual(diagnose(job, False)['state'], 'EDITOR_EXITED')
            (job / 'steps.txt').write_text('START\nFINISHED\n')
            (job / 'result.txt').write_text('{"saved":true}')
            self.assertEqual(diagnose(job, True)['result'], {'saved': True})
            self.assertFalse(diagnose(job, True)['automatic_replay_safe'])

    def test_preflight_ignores_comments_and_strings(self):
        self.assertFalse(preflight("ResultText := 'DoFileLoad'; // eSheetCustom\n"))
        self.assertTrue(preflight('SD.DoFileLoad;'))
        self.assertTrue(preflight('raise Exception.Create(\'error\');'))
        self.assertFalse(preflight('Doc.UseCustomSheet := True;'))

    def test_breaker_clears_only_after_exact_success(self):
        from contextlib import nullcontext
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp); block = state / 'blocked-job.json'; block.write_text('{}')
            with patch.object(cad_bridge, 'STATE', state), patch.object(cad_bridge, 'operation_lock', nullcontext):
                with patch.object(cad_bridge, 'run_script', return_value={'success': False}):
                    self.assertFalse(cad_bridge.recover_executor()['executor_recovered'])
                    self.assertTrue(block.exists())
                with patch.object(cad_bridge, 'run_script', return_value={'success': True, 'result': 'WRONG'}):
                    self.assertFalse(cad_bridge.recover_executor()['executor_recovered'])
                    self.assertTrue(block.exists())
                with patch.object(cad_bridge, 'run_script', return_value={'success': True, 'result': 'CODEX_RECOVERY_PROBE_OK'}):
                    self.assertTrue(cad_bridge.recover_executor()['executor_recovered'])
                    self.assertFalse(block.exists())

    def test_mutation_of_packaged_original_is_rejected_before_cad(self):
        from library_api import transact
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'original').mkdir(); (root / 'component.json').write_text('{}')
            lib = root / 'original/test.SchLib'; lib.write_bytes(b'fixture')
            with self.assertRaisesRegex(ValueError, 'immutable'):
                transact(None, str(lib), 'TEST', None, None)


if __name__ == '__main__':
    unittest.main()
