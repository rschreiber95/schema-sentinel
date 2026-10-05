# Schema Sentinel

UCF Senior Design project exploring safe, AI-assisted propagation of canonical
schema changes across software runtimes. Generated patches require validation
and human review; this repository does not implement the full proposed pipeline.

The current baseline includes versioned Protobuf `Entity` schemas, generated
Python/TypeScript/C# bindings, small runtime examples and HTTP relays, a
cross-runtime conformance test, and an experimental Buf/Semgrep/Tree-sitter
impact locator.

## Develop and test locally (Docker optional)

Install Python 3.10+, Node.js 22 with npm, and the .NET 8 SDK. From the repository root:

```bash
make setup
make test-local
```

`setup` creates `.venv`, installs locked TypeScript dependencies in
`runtimes/typescript`, and restores the C# project. `test-local` builds the
runtimes, runs the evidence unit tests, starts all three relays, waits for health,
runs four conformance cases, and stops its processes. Ports 8000–8002 must be free.
Runtime logs with decoded field values are saved in `testbed/artifacts/`.

Run the standalone examples:

```bash
make run-all
# Or: make run-python / make run-ts / make run-csharp
.venv/bin/python runtimes/python/main.py --version v2
npm start --prefix runtimes/typescript -- --v2
dotnet run --project runtimes/csharp/CsharpApp.csproj -- --v2
```

To develop a relay independently, see [testbed/README.md](testbed/README.md).

## Run the full test with Docker

Install Docker with Compose, then run from the repository root:

```bash
make test-docker
```

This builds the same runtime sources, runs the integration test, returns its exit
status, and removes the Compose containers. Local language toolchains are not
required for this route. No Docker dependency is required for local development.

## Canonical schema and conformance

- `proto/v1/entity.proto`: `simulation.v1.Entity` has `entity_id` and `name`.
- `proto/v2/entity.proto`: `simulation.v2.Entity` keeps `entity_id` and removes `name`.
- `generated/`: the committed language bindings from `main`; `buf generate`
  regenerates them when the schema changes (requires Buf and network access).
- `runtimes/`: the single implementation per language, supporting standalone
  examples for v1/v2 and the v1 HTTP relay.
- `testbed/`: orchestration, Dockerfiles, and tests; it defines no competing schema.

The integration route is `client -> Python -> TypeScript -> C# -> client`.
Every relay prints and returns an observation of the fields it actually decoded.
The test compares every runtime's `entity_id` and `name` with the same expected
values and also checks the final payload. The changing service trace is asserted
separately as HTTP metadata. Empty strings, Unicode, and escaped text are included.
This is a v1 conformance baseline, not a claim that v1 and v2 are semantically
interchangeable. The transport is intentionally small HTTP, not yet pub/sub.

See [READ.md](READ.md) for the experimental change/impact workflow and
[the architecture decision](docs/decisions/0001-two-service-testbed.md).
