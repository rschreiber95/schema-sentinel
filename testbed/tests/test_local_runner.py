import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


local = load_script('local_cli', ROOT / 'run_local.py')
services = load_script('local_services', ROOT / 'testbed/scripts/run-local.py')
python_runtime = load_script('python_runtime', ROOT / 'runtimes/python/main.py')


class LocalRunnerTests(unittest.TestCase):
    def test_windows_uses_the_scripts_interpreter(self):
        self.assertEqual(local.venv_python(ROOT, 'win32'), ROOT / '.venv/Scripts/python.exe')

    def test_macos_and_linux_use_the_bin_interpreter(self):
        for platform in ('darwin', 'linux'):
            self.assertEqual(local.venv_python(ROOT, platform), ROOT / '.venv/bin/python')

    def test_missing_tools_fail_before_installation(self):
        with patch.object(local.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'Missing from PATH: node, npm, dotnet'):
                local.check_tools()

    def test_occupied_port_does_not_start_or_stop_other_programs(self):
        with patch('socket.socket') as socket, patch.object(services.subprocess, 'Popen') as spawn:
            socket.return_value.__enter__.return_value.bind.side_effect = OSError('in use')
            with patch.object(sys, 'argv', ['run-local.py']), contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(services.main(), 1)
            spawn.assert_not_called()
            self.assertIn('Port 8000 is unavailable', output.getvalue())

    def test_cleanup_stops_a_running_child_process(self):
        process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        try:
            services.stop_processes([process])
            self.assertIsNotNone(process.poll())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_python_server_starts_without_reverse_dns(self):
        with patch('socket.getfqdn', side_effect=AssertionError('DNS unavailable')):
            with python_runtime.RelayServer(('127.0.0.1', 0), python_runtime.Relay) as server:
                self.assertGreater(server.server_port, 0)


if __name__ == '__main__':
    unittest.main()
