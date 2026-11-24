# Impact locator prototype

This is separate from the three-service testbed. It compares two schema
descriptors with Buf, then searches `runtimes/` for affected field accesses.
Use [README.md](../README.md) to run the testbed.

## Setup

Install Buf and Semgrep. Use a Python 3.11 environment for the analysis packages:

```sh
python -m pip install tree-sitter==0.21.3 tree-sitter-languages==1.10.2 PyYAML
```

The pinned Tree-sitter versions must be installed together. Run the following
from the repository root:

```sh
buf build --path proto/v1 --as-file-descriptor-set -o v1.bin
buf build --path proto/v2 --as-file-descriptor-set -o v2.bin
buf breaking v2.bin --against v1.bin --error-format json
python impact_locator.py
```

v2 removes `name` and changes the package, so Buf should report breaking
changes and return a nonzero exit code. The locator uses those diagnostics to
search the Python, TypeScript, and C# files. It is a prototype; its match accuracy
has not been measured.

The Protobuf bindings are already committed. If a schema changes, run
`buf generate` to regenerate them using the plugins in `buf.gen.yaml`.
