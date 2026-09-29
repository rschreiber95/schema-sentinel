# Schema Sentinel

COP4934 Fall 2026 Senior Design Project.

## Two-service testbed seed

The first testbed slice sends one Protocol Buffers message through two small
services:

```text
client -> Python relay -> TypeScript relay -> Python relay -> client
```

Both runtimes read [`proto/testbed.proto`](proto/testbed.proto). The services
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
{"message_id":"demo-001","payload":"hello from Schema Sentinel","visited_services":["python","typescript"]}
```

Stop the testbed with `Ctrl+C`.

The generated language bindings are created inside the container images and
are not committed to the repository.
