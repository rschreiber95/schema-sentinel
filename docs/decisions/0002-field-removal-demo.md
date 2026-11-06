# Decision 0002: Reproducible field-removal validation example

## Purpose and acceptance criteria

Extend the three-service testbed with a demonstration that must:

1. Build the existing v1 runtime sources and pass all four HTTP round trips.
2. Select the committed v2 bindings while retaining stale application accesses.
3. Observe a Python missing-field error and TypeScript/C# compiler errors about
   `name`/`Name`. Unrelated dependency or startup failures do not count.
4. Apply a checked-in reference repair proposal in the copied workspace.
5. Rebuild from clean compiler outputs and pass the v2 unit and round-trip tests.
   Each decoder must report exactly `entity_id`, preserving its input value.
   Negative controls reject incorrect intermediate values, missing runtimes,
   unexpected removed-field observations, changed returned values and wrong order.
6. Retain command exit codes, full logs, schema diff, repair diff and summary.

## Scope

`run_field_removal.py` uses copies under the ignored `testbed/artifacts/` tree.
Every invocation creates a fresh run directory. Installed Node dependencies are
copied; Python dependencies and the .NET package cache come from normal setup.
Existing testbed sources and previous evidence are preserved. Services use the
normal localhost ports and the existing runner's cleanup behavior.

The repair is an authored reference patch, not model output. No detector,
impact-locator, model, human acceptance measurement or merge is demonstrated.
The fixture also updates the test oracle to the explicit intended v2 behavior;
those expectations are reviewed code, not generated from a proposed repair.

The existing schema pair changes the package from `simulation.v1` to
`simulation.v2` as well as removing `name`. We reuse the committed generated
bindings rather than claiming to regenerate them or demonstrate a pure
same-package schema edit. No new dependency is introduced. This is an HTTP
validation example; the MVP's pub/sub transport remains separate work.

The existing baseline stays on v1. Passing this isolated proposal does not
approve or merge a schema migration into the project's normal services.
