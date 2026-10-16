"""Start the local services, run the test, and stop the services."""
import argparse
import os
from pathlib import Path
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

def stop_processes(processes):
    for process in processes:
        if process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', action='store_true', help='keep services running until Ctrl+C')
    args = parser.parse_args()
    processes = []
    log_dir = ROOT / 'testbed/artifacts'
    log_dir.mkdir(exist_ok=True)
    try:
        # Fail before starting anything if ports are already occupied.
        import socket
        for port in (8000, 8001, 8002):
            with socket.socket() as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind(('127.0.0.1', port))
                except OSError as error:
                    raise RuntimeError(f'Port {port} is unavailable. Stop the program using it and try again.') from error
        for command, runtime in zip(commands, ['csharp', 'typescript', 'python']):
            env = dict(os.environ, ASPNETCORE_URLS='http://127.0.0.1:8002', HOST='127.0.0.1', PORT='8001' if runtime == 'typescript' else '8000',
                       TYPESCRIPT_RELAY_URL='http://127.0.0.1:8001/relay', CSHARP_RELAY_URL='http://127.0.0.1:8002/relay')
            with (log_dir / f'{runtime}.log').open('w') as log:
                processes.append(subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT))
        deadline = time.monotonic() + 30
        for port in (8002, 8001, 8000):
            while True:
                if any(process.poll() is not None for process in processes):
                    failed = ['csharp', 'typescript', 'python'][next(i for i, process in enumerate(processes) if process.poll() is not None)]
                    raise RuntimeError(f'{failed} stopped during startup. See {log_dir / (failed + ".log")}')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError(f'Health timeout on {port}; inspect {log_dir}')
                time.sleep(0.2)
        if args.serve:
            print('Services are running:', flush=True)
            for runtime, port in [('Python', 8000), ('TypeScript', 8001), ('C#', 8002)]:
                print(f'  {runtime}: http://127.0.0.1:{port}/health', flush=True)
            print(f'Logs: {log_dir}\nPress Ctrl+C to stop all three services.', flush=True)
            while all(process.poll() is None for process in processes):
                time.sleep(0.5)
            raise RuntimeError(f'A service stopped. See the logs in {log_dir}')
        return subprocess.call([sys.executable, str(ROOT / 'testbed/tests/e2e_test.py')], cwd=ROOT,
                               env=dict(os.environ, PYTHON_RELAY_URL='http://127.0.0.1:8000/relay'))
    except (RuntimeError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        for log in sorted(log_dir.glob('*.log')):
            print(f'\n--- {log.name} ---\n' + log.read_text(encoding='utf-8', errors='replace')[-4000:], file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nServices stopped.')
        return 0
    finally:
        stop_processes(processes)

if __name__ == '__main__':
    raise SystemExit(main())
