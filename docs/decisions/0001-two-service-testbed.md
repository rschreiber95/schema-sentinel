# Decision 0001: HTTP conformance testbed using canonical Entity schemas

## Status

Accepted for the initial testbed; updated after integration of main's shared
Protobuf and runtime implementation in PR #2.

## Context

The first seed used a separate TestbedMessage schema and two relay services;
SS-34 added C#. Main now contains versioned Entity schemas, generated bindings,
and Python, TypeScript, and C# runtime examples. Keeping both sets would produce
competing sources of truth. The current task requires preserving main's schemas
and verifying actual decoder agreement across all three runtimes.

## Decision

- Use main's `proto/v1/entity.proto` for the conformance route. Preserve
  `proto/v2/entity.proto` as the existing name-removal fixture for change detection.
- Preserve committed generated bindings and the three runtime entry points under
  `runtimes/`. Add a `--serve` mode to those entry points; remove duplicate
  testbed runtime code and the TestbedMessage schema.
- Send binary Entity over HTTP with `application/x-protobuf`. Keep the route
  Python -> TypeScript -> C# and record decoded values before forwarding.
- Return decoder observations as JSON in `X-Schema-Sentinel-Observations` and
  the changing trace in `X-Service-Trace`. Neither is a canonical schema field.
- Assert every decoder's stable fields and the returned payload against the
  expected input. Assert trace order separately. Exercise empty, Unicode, and
  escaped values; add negative tests for intermediate mismatches.
- Make local builds and process orchestration the Docker-free development path.
  Keep Compose as an optional one-command integration workflow using identical
  sources and bindings. Use main's .NET 8 target for C#.

## Consequences and limitations

This provides a reproducible three-language conformance baseline. It does not yet
implement pub/sub, schema propagation, patch generation, a validation dashboard,
or the twenty-case evaluation benchmark. v2 examples avoid accessing the removed
field, but v2 relay conformance is not implemented. The experimental impact
locator continues to inspect the canonical runtime directory.

Observation headers are small trusted test evidence, not scalable telemetry or a
security guarantee. Generated bindings are committed because main established
that workflow; regeneration requires Buf and its remote plugins. The inherited
tracked root node_modules are preserved during this integration; active runtime
dependencies are installed from the TypeScript lockfile under runtimes/typescript.
