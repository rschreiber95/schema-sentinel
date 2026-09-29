# Schema Sentinel

COP4934 Fall 2026 Senior Design Project.

## Two-service testbed seed

The testbed sends one Protocol Buffers message through small services written
in three languages:

```text
client -> Python relay -> TypeScript relay -> C# relay -> client
```

All runtimes read [`proto/testbed.proto`](proto/testbed.proto). The services
intentionally use a small HTTP transport so the team can focus on schema
behavior before choosing a larger messaging system.

### Run it

Requirements: Docker with Docker Compose.

```bash
docker compose up --build
```

After both services are healthy, run the demo from another terminal:

```bash
curl http://localhost:8000/demo
```

The response includes the original message and the two runtimes it visited:

```json
{"message_id":"demo-001","payload":"hello from Schema Sentinel","visited_services":["python","typescript","csharp"]}
```

Stop the testbed with `Ctrl+C`.

The generated language bindings are created inside the container images and
are not committed to the repository.

### Run the round-trip test

SS-20 adds a one-command check that serializes a known message, sends it
through both services, deserializes the result, and verifies every field:

```bash
./scripts/test-roundtrip.sh
```

The command exits unsuccessfully if any service is unhealthy, the message
cannot be decoded, any original field changes, or the service trace is not
exactly `python -> typescript -> csharp`.
