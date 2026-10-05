# Cross-runtime testbed

The testbed uses `../proto/v1/entity.proto` and the generated bindings in
`../generated/`. Runtime code lives only in `../runtimes/`; Docker and local runs
execute the same code. v2 is the deletion fixture for the change detector, not
the relay contract.

```text
client -> Python (:8000) -> TypeScript (:8001) -> C# (:8002) -> client
```

## Local workflow

From the repository root, with Python 3.10+, Node.js 22, and .NET 8 installed:

```bash
make setup
make test-local
```

The command builds both compiled runtimes, runs evidence unit tests, starts the
services, awaits their health checks, and stops them after the integration test.
Decoded field logs remain in `testbed/artifacts/{python,typescript,csharp}.log`.

For interactive development, run these in three terminals from the repository
root after `make setup` and `make build`:

```bash
ASPNETCORE_URLS=http://localhost:8002 dotnet run --no-build --configuration Release --project runtimes/csharp/CsharpApp.csproj -- --serve
PORT=8001 npm start --prefix runtimes/typescript -- --serve
PORT=8000 .venv/bin/python runtimes/python/main.py --serve
```

Then use a fourth terminal:

```bash
.venv/bin/python testbed/tests/e2e_test.py
curl http://localhost:8000/health
```

Stop each interactive service with Ctrl+C. Override `TYPESCRIPT_RELAY_URL` on
Python and `CSHARP_RELAY_URL` on TypeScript to change downstream addresses;
override `PYTHON_RELAY_URL` when running the test. C# uses `ASPNETCORE_URLS`.
The automated local runner deliberately uses ports 8000–8002 and localhost.

## Docker workflow

From the repository root:

```bash
make test-docker
```

Or run `./testbed/scripts/test-roundtrip.sh`. The script returns the test exit
code and tears down its Compose services. For an interactive session:

```bash
cd testbed
docker compose up --build
# In a second terminal:
docker compose --profile test run --rm roundtrip-test
# When finished:
docker compose --profile test down --remove-orphans
```

## Acceptance criteria

Four cases cover ordinary values, proto3 defaults, Unicode, and escaped text.
For each case, each runtime must report exactly the expected `entity_id` and
`name`, and the returned protobuf must preserve those fields. Observation order
must be Python, TypeScript, C#. The separate service trace must be exactly
`["python","typescript","csharp"]`.

Relays print structured JSON before forwarding. Response header
`X-Schema-Sentinel-Observations` carries those decoder observations; the test
prints the expected values, each decoder's values, and the trace.
`X-Service-Trace` carries the changing transport trace, leaving the canonical
Entity schema unchanged. These headers are trusted testbed evidence, not a
production audit system. The negative unit tests prove a wrong intermediate
observation fails even when the final payload is correct.
