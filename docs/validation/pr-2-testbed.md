# PR #2 integration validation — October 5, 2026

## Integration baseline

Merged `origin/main` at `c82fee7` into
`codex/SS-19-SS-20-SS-34-testbed`. The merge had no textual conflicts, but the
combined tree had two schemas and competing runtime implementations. The
integration keeps main's versioned Entity definitions, committed generated
bindings, and runtime entry points, adding relay modes to those entry points.
`git diff origin/main -- proto generated` is empty. The impact locator source
and descriptor fixtures from main are also unchanged.

## Checks

- `make setup`: Python dependency installation, locked npm install, .NET restore passed.
- `make test-local`: TypeScript build, C# Release build (zero warnings/errors),
  Python compile check, five evidence unit tests, and four three-runtime
  conformance cases passed without Docker.
- `make test-docker`: all images built, service health checks passed, all four
  conformance cases passed, exit code was zero, Compose containers cleaned up.
- `make run-all`: Python, C#, and TypeScript standalone v1 examples passed.
- All three standalone v2 examples passed without accessing the deleted name field.
- `npm audit --prefix runtimes/typescript`: no vulnerabilities reported.
- .NET transitive package vulnerability audit: no vulnerabilities reported.
- `bash -n testbed/scripts/test-roundtrip.sh` and `git diff --check`: passed.

Each integration case compares the actual decoded `entity_id` and `name` from
all three runtimes with the expected input, compares the returned protobuf,
and asserts the service trace separately. Cases cover ordinary values, empty
proto3 strings, Unicode including non-BMP characters, and escaped text.
Negative tests reject wrong intermediate values even if the final payload is
correct, a missing runtime, a changed returned payload, and a wrong trace.

Local validation used Python 3.13.7, Node.js 24.10.0, and a temporary .NET 8.0.425 SDK.
Docker uses Python 3.13, Node.js 22, and .NET 8. Active Protobuf libraries have
BSD-3-Clause licenses (Python protobuf, protobufjs, Google.Protobuf).

## Limits and follow-up

The optional Buf generation/change detector and Semgrep/Tree-sitter prototype
were not executed: their toolchain is not installed in this environment. The
canonical schemas, generated bindings, descriptor binaries, and impact locator
were preserved. Their commands and current limitations are documented in READ.md.

The integration contract is v1; v2 has standalone smoke coverage only. It does
not establish cross-version semantic compatibility or complete the twenty-case
schema-change benchmark. Decoder observations are small trusted HTTP metadata,
not production telemetry. Main's already-tracked root node_modules remain
unchanged and should be cleaned up in a separate agreed maintenance change.
