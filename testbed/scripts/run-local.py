"""Run already-built local runtimes, await health, test, and clean up."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
commands = [
    ['dotnet', str(ROOT / 'runtimes/csharp/bin/Release/net8.0/CsharpApp.dll'), '--serve'],
    ['node', str(ROOT / 'runtimes/typescript/dist/runtimes/typescript/main.js'), '--serve'],
    [sys.executable, str(ROOT / 'runtimes/python/main.py'), '--serve'],
]

def main():
    processes = []
    log_dir = ROOT / 'testbed/artifacts'
    log_dir.mkdir(exist_ok=True)
    try:
        # Fail before starting anything if ports are already occupied.
        import socket
        for port in (8000, 8001, 8002):
            with socket.socket() as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('127.0.0.1', port))
        for command, runtime in zip(commands, ['csharp', 'typescript', 'python']):
            env = dict(os.environ, ASPNETCORE_URLS='http://127.0.0.1:8002', PORT='8001' if runtime == 'typescript' else '8000',
                       TYPESCRIPT_RELAY_URL='http://127.0.0.1:8001/relay', CSHARP_RELAY_URL='http://127.0.0.1:8002/relay')
            with (log_dir / f'{runtime}.log').open('w') as log:
                processes.append(subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
        deadline = time.monotonic() + 30
        for port in (8002, 8001, 8000):
            while True:
                if any(process.poll() is not None for process in processes):
                    raise RuntimeError(f'A runtime exited; inspect {log_dir}')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError(f'Health timeout on {port}; inspect {log_dir}')
                time.sleep(0.2)
        return subprocess.call([sys.executable, str(ROOT / 'testbed/tests/e2e_test.py')], cwd=ROOT,
                               env=dict(os.environ, PYTHON_RELAY_URL='http://127.0.0.1:8000/relay'))
    finally:
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()

if __name__ == '__main__':
    raise SystemExit(main())
