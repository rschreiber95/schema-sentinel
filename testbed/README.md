# Testbed development

Start with the [local setup instructions](../README.md). All commands below run
from the repository root.

## Start all services

Windows:

```powershell
py run_local.py start
```

macOS and Linux:

```sh
python3 run_local.py start
```

This builds the code and keeps all three services running. Dependencies must
already be installed by the first run. Press Ctrl+C to stop the services.

| Service | Health check |
| --- | --- |
| Python | http://127.0.0.1:8000/health |
| TypeScript | http://127.0.0.1:8001/health |
| C# | http://127.0.0.1:8002/health |

Open a health-check URL in your browser to confirm that a service is running.
Logs are saved in `testbed/artifacts/python.log`, `typescript.log`, and `csharp.log`.

To send the four test messages while the services are running, open a second terminal:

```powershell
# Windows
.venv\Scripts\python.exe testbed/tests/e2e_test.py
```

```sh
# macOS and Linux
.venv/bin/python testbed/tests/e2e_test.py
```

Each test checks the fields decoded by Python, TypeScript, and C#, the returned
message, and the service order. The cases use normal strings, empty strings,
Unicode, and escaped text.

## Run individual examples

These print one decoded entity and exit. They do not start servers.

```powershell
# Windows
.venv\Scripts\python.exe runtimes/python/main.py
```

```sh
# macOS and Linux
.venv/bin/python runtimes/python/main.py
```

These commands work on all three operating systems after setup and a build:

```sh
npm start --prefix runtimes/typescript
dotnet run --project runtimes/csharp/CsharpApp.csproj
```

Add `--version v2` to the Python command, `-- --v2` to the npm command, or
`-- --v2` to the dotnet command to use the existing name-removal example.
The HTTP test uses v1.

## Docker (optional)

With Docker Compose installed, run:

```sh
docker compose -f testbed/compose.yaml --profile test up --build --abort-on-container-exit --exit-code-from roundtrip-test
docker compose -f testbed/compose.yaml --profile test down --remove-orphans
```

The second command removes the test containers. On macOS and Linux,
`make test-docker` runs both steps automatically.
