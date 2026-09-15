import importlib.util
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from core.bounty_worker.identity import inspect_httpx, MARKER
from core.bounty_worker.runner import run_bounded
from core.bounty_worker.fixture import demo

class WorkerTests(unittest.TestCase):
    def inspect(self, content):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'httpx'
            path.write_bytes(content); path.chmod(0o755)
            return inspect_httpx(path)

    def test_python_client_rejected(self):
        r = self.inspect(b'#!/usr/bin/python3\nfrom httpx import main\n')
        self.assertEqual(r['identity'], 'python-httpx-client')
        self.assertFalse(r['recon_available'])

    def test_static_marker_is_not_readiness(self):
        r = self.inspect(b'\x7fELF' + MARKER)
        self.assertTrue(r['recon_available'])
        self.assertFalse(r['ready_for_live_testing'])

    def test_unknown_rejected(self):
        self.assertFalse(self.inspect(b'#!/bin/sh\necho httpx')['recon_available'])

    def test_missing_rejected(self):
        self.assertFalse(inspect_httpx('/no-such-r2-file')['recon_available'])

    def test_identity_does_not_execute(self):
        with patch('subprocess.Popen', side_effect=AssertionError('No execution')):
            self.inspect(b'#!/usr/bin/python3\nimport httpx\n')

    def run_code(self, code, **kwargs):
        return run_bounded([sys.executable, '-I', '-c', code], **kwargs)

    def test_nonzero(self):
        self.assertEqual(self.run_code('raise SystemExit(7)')['state'], 'failed')

    def test_timeout(self):
        self.assertEqual(self.run_code('import time; time.sleep(10)', timeout=.15)['state'], 'timeout')

    def test_output_cap(self):
        r = self.run_code('print("x"*10000)', output_limit=100)
        self.assertEqual(r['state'], 'output_limit'); self.assertEqual(r['bytes'], 100)

    def test_pre_cancelled(self):
        event = threading.Event(); event.set()
        with patch('subprocess.Popen', side_effect=AssertionError('No execution')):
            self.assertEqual(self.run_code('print(1)', cancel=event)['state'], 'cancelled')

    def test_running_cancelled(self):
        event = threading.Event()
        timer = threading.Timer(.15, event.set); timer.start()
        try:
            self.assertEqual(self.run_code('import time; time.sleep(10)', cancel=event)['state'], 'cancelled')
        finally:
            timer.cancel(); timer.join()

    def test_inherited_pipe_deadline(self):
        code = 'import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(10)"])'
        self.assertEqual(self.run_code(code, timeout=.2)['state'], 'timeout')

    def test_local_fixture(self):
        result = demo()
        self.assertTrue(result['passed'])
        self.assertEqual(result['fixture_requests'], 1)
        self.assertEqual(result['external_targets_tested'], 0)

    def test_route_preserves_snapshot(self):
        fake_fastapi = types.ModuleType('fastapi')
        class Router:
            def get(self, path):
                return lambda fn: fn
        fake_fastapi.APIRouter = Router
        fake_snapshot = types.ModuleType('core.src.cognition.platform_status')
        original = {'environment': 'kali', 'capabilities': {'httpx': True, 'nmap': True}}
        fake_snapshot.snapshot = lambda: original
        import core
        route = next(Path(p)/'src/routes/platform_status.py' for p in core.__path__
                     if (Path(p)/'src/routes/platform_status.py').exists())
        with patch.dict(sys.modules, {'fastapi': fake_fastapi, 'core.src.cognition.platform_status': fake_snapshot}):
            spec = importlib.util.spec_from_file_location('r2_test_route', route)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with patch.object(module, 'inventory', return_value={'httpx': {'recon_available': False}}):
            result = module.platform_status()
        self.assertFalse(result['capabilities']['httpx'])
        self.assertTrue(result['capabilities']['nmap'])
        self.assertTrue(original['capabilities']['httpx'])

if __name__ == '__main__':
    unittest.main()
