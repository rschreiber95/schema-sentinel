# Decision 0001: Three-service Protobuf testbed

## Design

Use the existing `proto/v1/entity.proto` and generated bindings for all services.
Each runtime has one implementation in `runtimes/` that can run as a standalone
example or an HTTP service.

Messages follow this route:

```text
client -> Python -> TypeScript -> C# -> client
```

Each service decodes the message, records `entity_id` and `name`, and forwards
the serialized message. The test checks every service's values and the final
message against the input. Service order is checked separately.

HTTP keeps the testbed easy to run locally. The Python runner manages the
services on Windows, macOS, and Linux. Docker Compose uses the same sources.

## Scope

The HTTP test uses v1. The existing v2 schema remains a field-removal example
for change detection. Pub/sub and generated patch workflows are separate work.

Decoded values are returned in `X-Schema-Sentinel-Observations`. Service order
is returned in `X-Service-Trace`. Both are test metadata, outside the schema.
