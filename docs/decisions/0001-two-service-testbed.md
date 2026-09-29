# Decision 0001: Seed the testbed with HTTP and Protocol Buffers

## Status

Accepted for the initial testbed seed.

## Context

SS-19 needs two small services in different languages that share one schema.
The transport is not the research question yet, and choosing a broker now would
add operational work before the team has a stable cross-runtime baseline.

SS-33 currently proposes a generated SISO enumeration catalog. That catalog is
useful schema input, but it does not define a message envelope that the services
can exchange. It is also still under review, so SS-19 should not depend on its
branch.

## Decision

- Define a minimal `TestbedMessage` in `testbed/proto/testbed.proto`.
- Send its binary Protocol Buffers representation over HTTP with the
  `application/x-protobuf` content type.
- Let the Python service accept the client request and forward it to the
  TypeScript service.
- Generate Python bindings during the container build and load the same schema
  dynamically in TypeScript.
- Keep generated bindings out of version control.

## Consequences

- The seed can be run with one Docker Compose command.
- A third runtime can implement the same small relay contract later.
- Formal round-trip assertions belong to SS-20 rather than this seed.
- The SISO enum catalog can be imported after SS-33 is merged and its naming and
  generated-file concerns are resolved.

## Follow-up

SS-34 adds C# as the third runtime. It uses the same HTTP relay contract and
the same schema, extending the route to `Python -> TypeScript -> C#` without
changing the message definition.
