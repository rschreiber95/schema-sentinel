"""Demonstrate a field removal, real failures, and an authored repair in a copy."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from run_local import ROOT, check_tools, venv_python


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def require_field_failure(language, result):
    """An arbitrary broken build is not evidence of the intended removal."""
    patterns = {
        "python": r"(?:AttributeError|ValueError).*\bname\b",
        "typescript": r"error TS(?:2339|2353):[^\n]*['\"]name['\"]",
        "csharp": r"error CS(?:1061|0117):[^\n]*['\"]Name['\"]",
    }
    require(result.returncode != 0 and re.search(patterns[language], result.stdout),
            f"{language}: expected a missing-name failure; inspect the saved log.")


def switch_bindings(workspace):
    """Deliberately leave application field accesses stale after selecting v2."""
    replacements = {
        "runtimes/python/main.py": [('importlib.import_module(f"{version}.entity_pb2")',
                                     'importlib.import_module("v2.entity_pb2")', 1),
                                    ('importlib.import_module(f"{args.version}.entity_pb2")',
                                     'importlib.import_module("v2.entity_pb2")', 1)],
        "runtimes/typescript/main.ts": [('from "../../generated/ts/v1/entity"',
                                         'from "../../generated/ts/v2/entity"', 1)],
        "runtimes/csharp/main.cs": [('Simulation.V1.Entity', 'Simulation.V2.Entity', 2)],
    }
    for name, edits in replacements.items():
        path = workspace / name
        text = path.read_text(encoding="utf-8")
        for old, new, count in edits:
            require(text.count(old) == count, f"Source changed: review demo switch for {name}")
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8", newline="\n")


def schema_evidence(workspace, output):
    # Use the committed generated descriptors, not diagnostic prose or an LLM.
    sys.path.insert(0, str(workspace / "generated/python"))
    from v1.entity_pb2 import Entity as V1
    from v2.entity_pb2 import Entity as V2
    old = {f.number: (f.name, f.type) for f in V1.DESCRIPTOR.fields}
    new = {f.number: (f.name, f.type) for f in V2.DESCRIPTOR.fields}
    require(old == {1: ("entity_id", 9), 2: ("name", 9)} and new == {1: ("entity_id", 9)},
            "Demo requires the committed Entity schemas: entity_id retained, name removed.")
    record = {
        "case": "entity-name-removal", "removed_field": {"name": "name", "number": 2},
        "retained_field": "entity_id", "old_message": V1.DESCRIPTOR.full_name,
        "new_message": V2.DESCRIPTOR.full_name,
        "note": "Existing versioned fixtures also change the package; this is not a general change detector.",
    }
    save(output / "schema-change.json", record)
    before = (workspace / "proto/v1/entity.proto").read_text(encoding="utf-8")
    after = (workspace / "proto/v2/entity.proto").read_text(encoding="utf-8")
    diff = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                     fromfile="proto/v1/entity.proto", tofile="proto/v2/entity.proto"))
    (output / "schema-change.diff").write_text(diff, encoding="utf-8")
    print(diff, flush=True)
    return record


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def demonstrate(output, pause):
    tools = check_tools()
    require((ROOT / "runtimes/typescript/node_modules").is_dir(),
            "Dependencies missing. Run python3 run_local.py first (Windows: py run_local.py).")
    require(shutil.which("git"), "Git is required to check and apply the authored demo patch.")
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    report = {"status": "running", "repair_method": "authored reference patch; no model",
              "human_approval_required": True, "merged": False, "commands": []}
    report["source_revision"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report["source_sha256"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ("run_field_removal.py", "runtimes/python/main.py",
                     "runtimes/typescript/main.ts", "runtimes/csharp/main.cs",
                     "testbed/tests/e2e_test.py", "testbed/fixtures/field-removal/repair.patch")
    }
    started = time.monotonic()
    save(output / "report.json", report)

    def execute(label, args, *, success=True):
        command = [str(arg) for arg in args]
        result = subprocess.run(command, cwd=workspace, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                errors="replace", timeout=180,
                                env=dict(os.environ, GIT_CEILING_DIRECTORIES=str(output),
                                         PYTHONIOENCODING="utf-8", DOTNET_CLI_UI_LANGUAGE="en"))
        (output / (label + ".log")).write_text(result.stdout, encoding="utf-8")
        report["commands"].append({"step": label, "command": command, "exit_code": result.returncode})
        save(output / "report.json", report)
        if success:
            require(result.returncode == 0, f"{label} failed. See {output / (label + '.log')}")
        return result

    def checkpoint(message):
        if pause:
            input("\n" + message + " Press Enter to continue...")

    try:
        # Copy the actual PR sources. Build output and services belong to this copy.
        def ignore(folder, names):
            excluded = {"__pycache__", ".bin"}
            if Path(folder) == ROOT / "runtimes/csharp":
                excluded.update(("bin", "obj"))
            if Path(folder) == ROOT / "runtimes/typescript":
                excluded.add("dist")
            if Path(folder) == ROOT / "testbed":
                excluded.add("artifacts")
            return set(names) & excluded
        for name in ("proto", "generated", "runtimes", "testbed"):
            shutil.copytree(ROOT / name, workspace / name, ignore=ignore)
        shutil.copy2(ROOT / "run_local.py", workspace / "run_local.py")
        shutil.copy2(ROOT / "run_field_removal.py", workspace / "run_field_removal.py")

        print("\n1. BASELINE: v1 still has entity_id and name", flush=True)
        typescript_build = [tools["node"], "runtimes/typescript/node_modules/typescript/bin/tsc",
                            "--project", "runtimes/typescript/tsconfig.json"]
        execute("baseline-typescript", typescript_build)
        execute("baseline-csharp", [tools["dotnet"], "build", "runtimes/csharp/CsharpApp.csproj", "-c", "Release"])
        execute("baseline-unit", [sys.executable, "-m", "unittest", "discover", "-s", "testbed/tests", "-p", "test_*.py", "-v"])
        print("Baseline builds and unit tests passed.", flush=True)
        result = execute("baseline-roundtrip", [sys.executable, "testbed/scripts/run-local.py"])
        print(result.stdout, flush=True)
        checkpoint("Baseline passed. Next: select v2 bindings while keeping old field accesses.")

        print("\n2. BREAK: v2 removes name; application code still uses it", flush=True)
        report["change"] = schema_evidence(workspace, output)
        switch_bindings(workspace)
        probes = {
            "python": [sys.executable, "runtimes/python/main.py"],
            "typescript": typescript_build,
            "csharp": [tools["dotnet"], "build", "runtimes/csharp/CsharpApp.csproj", "-c", "Release"],
        }
        for language, args in probes.items():
            result = execute("broken-" + language, args, success=False)
            require_field_failure(language, result)
            lines = list(dict.fromkeys(line for line in result.stdout.splitlines()
                                      if re.search(r"AttributeError|ValueError|error TS|error CS", line)))
            print(f"[EXPECTED FAILURE] {language}\n" + "\n".join(lines), flush=True)
        # No failed compiler output is allowed to masquerade as a repaired build.
        for path in (workspace / "runtimes/typescript/dist", workspace / "runtimes/csharp/bin",
                     workspace / "runtimes/csharp/obj"):
            if path.exists():
                shutil.rmtree(path)
        checkpoint("All three languages exposed stale name references. Next: apply the authored repair.")

        print("\n3. REPAIR: apply the authored reference patch (no AI call)", flush=True)
        patch = ROOT / "testbed/fixtures/field-removal/repair.patch"
        shutil.copy2(patch, output / "repair.patch")
        report["repair_sha256"] = hashlib.sha256(patch.read_bytes()).hexdigest()
        execute("repair-check", ["git", "apply", "--check", str(patch)])
        execute("repair-apply", ["git", "apply", str(patch)])
        execute("repaired-typescript", typescript_build)
        execute("repaired-csharp", [tools["dotnet"], "build", "runtimes/csharp/CsharpApp.csproj", "-c", "Release"])
        execute("repaired-unit", [sys.executable, "-m", "unittest", "discover", "-s", "testbed/tests", "-p", "test_*.py", "-v"])
        print("Repaired builds and unit tests passed, including the v2 negative controls.", flush=True)
        # The normal runner now starts the repaired v2 services and independent v2 oracle.
        result = execute("repaired-roundtrip", [sys.executable, "testbed/scripts/run-local.py"])
        print(result.stdout, flush=True)
        report["status"] = "passed"
        print("PASS: baseline passed; 3/3 expected failures; repaired v2 passed.\n"
              "Repair remains a proposal for human review; nothing was merged.", flush=True)
    except BaseException as error:
        report.update(status="failed", error=str(error))
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        save(output / "report.json", report)
        print(f"\nEvidence: {output}\nRepair diff: {output / 'repair.patch'}", flush=True)


def main():
    sys.stdout.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pause", action="store_true", help="pause between stages for a live presentation")
    args = parser.parse_args()
    python = venv_python()
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        if not python.exists():
            print("Run python3 run_local.py first (Windows: py run_local.py).", file=sys.stderr)
            return 1
        return subprocess.call([str(python), str(Path(__file__).resolve()), *sys.argv[1:]])
    artifacts = ROOT / "testbed/artifacts/field-removal"
    artifacts.mkdir(parents=True, exist_ok=True)
    # Every run retains separate evidence. Never reset or delete a previous run.
    output = Path(tempfile.mkdtemp(prefix="run-", dir=artifacts))
    output.rmdir()  # demonstrate owns creation and requires a fresh directory.
    try:
        demonstrate(output, args.pause)
        return 0
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Stopped.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
