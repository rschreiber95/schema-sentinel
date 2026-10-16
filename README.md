# Schema Sentinel

UCF Senior Design project for testing schema changes across Python, TypeScript,
and C#. The testbed sends one Protobuf `Entity` through all three services and
checks that each service reads the same `entity_id` and `name`.

## Run locally

Install these tools, then reopen your terminal:

| Tool | Version |
| --- | --- |
| [Python](https://www.python.org/downloads/) | 3.10 or newer |
| [Node.js and npm](https://nodejs.org/en/download) | Node.js 22 or newer |
| [.NET SDK](https://dotnet.microsoft.com/en-us/download/dotnet/8.0) | 8.0 SDK |

Use the PR branch. For a new clone:

```sh
git clone --branch codex/SS-19-SS-20-SS-34-testbed https://github.com/rschreiber95/schema-sentinel.git
cd schema-sentinel
```

For an existing clone, update the PR branch first:

```sh
git fetch origin
git switch codex/SS-19-SS-20-SS-34-testbed
git pull --ff-only
```

### Windows (PowerShell or Command Prompt)

```powershell
py run_local.py
```

If `py` is unavailable, use `python run_local.py`.

### macOS and Linux

```sh
python3 run_local.py
```

The script installs the project dependencies, builds the runtimes, runs the unit
tests, and sends four test messages through Python -> TypeScript -> C#. It stops
the services when finished. Docker, Make, and Buf are not needed for this run.
The first run needs an internet connection to download dependencies.

The last line should be:

```text
PASS: 4 cases; all three decoders agree on stable fields; service trace verified separately
```

To repeat the checks without reinstalling dependencies, add `test` to the command.
To keep the services running for development, add `start`. Press Ctrl+C to stop them.

## Common setup problems

- **Missing `node`, `npm`, or `dotnet`:** install the tools above and reopen the
  terminal. For .NET, choose the **8.0 SDK**, not just the runtime.
- **Python is missing:** install Python. On Windows, enable its command-line
  shortcuts; on Linux, your distribution may also require `python3-venv`.
- **`run_local.py` is missing:** check out the PR branch and run from the folder
  containing this README.
- **A port is unavailable:** stop the program using ports 8000, 8001, or 8002.
- **A service fails:** check its log in `testbed/artifacts/`.

## Project files

- `proto/`: v1 has `entity_id` and `name`; v2 removes `name`.
- `generated/`: Protobuf bindings used by the runtimes.
- `runtimes/`: Python, TypeScript, and C# service code.
- `testbed/`: tests, logs, and the local service runner.

See [testbed development](testbed/README.md) for individual service commands and
optional Docker commands. The [impact locator guide](docs/impact-locator.md)
covers the separate Buf, Semgrep, and Tree-sitter prototype.
