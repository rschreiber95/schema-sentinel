# Experimental change and impact workflow

Run these commands from the repository root. Buf, Semgrep, and Python analysis
dependencies are separate from the runtime test dependencies. The legacy
`tree_sitter_languages` package expects `tree-sitter==0.21.3`; use a compatible
Python environment (for example Python 3.11) and install:

```bash
python -m pip install tree-sitter==0.21.3 tree-sitter-languages==1.10.2 PyYAML
```

Install Buf and Semgrep separately, then regenerate descriptor fixtures:

```bash
make descriptors
buf breaking v2.bin --against v1.bin --error-format json
python impact_locator.py
```

v1 contains `entity_id` and `name`; v2 removes `name` and changes the package.
Buf should report breaking changes (a nonzero exit is expected). The prototype
extracts field names from Buf diagnostics, generates Semgrep rules, and scans
`runtimes/` with Semgrep and Tree-sitter. It is experimental: it does not yet
provide measured recall, complete classification, or production error handling.
The example paths are now `runtimes/python/main.py`,
`runtimes/typescript/main.ts`, and `runtimes/csharp/main.cs`.

For runtime examples, builds, and the cross-runtime tests, follow [README.md](README.md).
`make generate` runs the existing Buf plugins to regenerate committed bindings;
normal runtime development uses the bindings already in the repository.
