# Field-removal demo: presenter guide

This demonstrates the validation workflow using the real three-runtime sources:
working v1 -> stale code with v2 bindings -> authored repair -> working v2.
It is a reference repair, not an AI-generated patch or an integrated locator demo.

## Prepare before the meeting

Open the PR #2 checkout in VS Code with **File -> Open Folder**. For a fresh clone:

```sh
git clone https://github.com/rschreiber95/schema-sentinel.git
cd schema-sentinel
git switch codex/SS-19-SS-20-SS-34-testbed
```

Choose **Terminal -> New Terminal**. Run these commands from the project root:

```sh
# macOS / Linux
python3 run_local.py
python3 run_field_removal.py
```

```powershell
# Windows
py run_local.py
py run_field_removal.py
```

The first command installs dependencies, builds the baseline and tests it.
The second rehearses the complete demo without pausing. Both must exit successfully.
Setup requires Python 3.10+, Node.js 22+, the .NET 8 SDK and Git. There is no new
package to install for the demo. No Docker, Buf, model or API key is required.
Do setup beforehand; package installation should not be part of the live talk.

Stop any earlier `run_local.py start` session with Ctrl+C. The demo needs ports
8000, 8001 and 8002. It stops its own services after each round trip. Each run
creates a separate evidence directory and leaves the normal v1 sources intact.

## Live walkthrough (about five minutes)

1. Open `proto/v1/entity.proto` and `proto/v2/entity.proto` side by side.
   Point at `string name = 2;` in v1 and its absence in v2. Mention that these
   existing fixtures also use different package names (`simulation.v1`/`v2`).
   Say: "We want to retain entity_id and remove name from the application contract."

2. In the terminal, run:

   ```sh
   python3 run_field_removal.py --pause
   ```

   On Windows, use `py run_field_removal.py --pause`.

3. At the first pause, point to the first message's decoded values from all three
   services and `PASS: 4/4 round-trip cases passed.`
   Say: "This is the working baseline. Each runtime decoded the same ID and name;
   the returned message and service order are checked too."

4. Press **Enter**. The demo prints the schema diff, switches the copied sources
   to the existing v2 bindings and leaves their old field accesses in place.
   At the second pause, point to `[EXPECTED FAILURE]` for each language:
   Python's missing `name` field, TypeScript's property/object-literal errors,
   and C#'s missing `Name` property errors.
   Say: "Changing the schema bindings alone leaves application references broken."

5. While paused, open `testbed/fixtures/field-removal/repair.patch` in VS Code.
   Show the removal of the old reads and construction values and the v2 imports.
   The patch also switches the test oracle to the explicit v2 contract.
   Say: "This is a prepared reference repair. I am demonstrating how we validate
   a repair; this run does not ask an LLM to create it."

6. Return to the terminal and press **Enter**. The patch is checked and applied
   only to the copied workspace. Fresh TypeScript/C# builds, unit tests and
   another four HTTP round trips must pass. Point to the first message:
   every runtime now reports only `entity_id`, with the input value preserved.
   The final summary must be:

   ```text
   PASS: baseline passed; 3/3 expected failures; repaired v2 passed.
   ```

7. The terminal prints the evidence directory. Open its `report.json` and, if
   useful, `broken-python.log`, `broken-typescript.log`, `broken-csharp.log` or
   `repaired-roundtrip.log`. Say: "The proposal keeps its repair diff and test
   evidence together for human review. Passing tests does not merge it."

## What the evidence establishes

- Real application code breaks when selected v2 bindings lack the old field.
- The authored repair builds and preserves the retained ID across three decoders.
- Four v2 cases cover ordinary text, empty strings, Unicode and escaped text.
- Negative controls reject wrong intermediate/returned values, missing services,
  wrong service order and an unexpected `name` observation in v2.
- The demo requires an actual missing-field diagnostic; unrelated tool failures
  cannot count as a successful breaking-change demonstration.

The generated bindings are already committed; this demo does not regenerate
them. It does not measure impact recall, model performance, manual propagation
time, human review time or legacy-wire/mixed-version compatibility. Its elapsed
time includes demo setup and, in pause mode, presentation pauses.

## Evidence and fallback

Every run is retained under `testbed/artifacts/field-removal/run-*/`:

| File | Purpose |
| --- | --- |
| `schema-change.diff`, `schema-change.json` | Explicit schema example and descriptor check |
| `broken-*.log` | Full missing-field failures before repair |
| `repair.patch` | Authored repair applied to this run |
| `baseline-*.log`, `repaired-*.log` | Builds, unit tests and round-trip evidence |
| `report.json` | Status, source hashes, command exit codes and elapsed demo time |
| `workspace/` | Copied sources with the repair applied |

If a live run is blocked by occupied ports or a machine setup issue, show the
logs from the successful rehearsal or download the operating-system evidence
artifact from the PR's GitHub Actions run. Clearly call it a recorded run.
Do not describe a failed or interrupted live run as passing.
