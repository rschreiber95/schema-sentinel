# This READ.md describes the commands that are needed to run the schema-sentinel tool

# To run buf generate the IR needed for the diff:
buf build --path proto/v1 --as-file-descriptor-set -o v1.bin

&

buf build --path proto/v2 --as-file-descriptor-set -o v2.bin

# To do a diff of the two using buf(aka load the v1.bin and v2.bin into IR and diff them) run: 
buf breaking v2.bin --against v1.bin

# To emit machine-readable structural JSON, run with the --format json flag:
buf breaking v2.bin --against v1.bin --format json

# We can extract fields from this JSON, including 'DELETED', 'ADDED', etc using jq. i.e. DELETED_FIELD=$(buf breaking v2.bin --against v1.bin --format json | jq -r '.message' | grep -oP 'name "\K[^"]+')

# To run the impact_locator.py, enter:
python3 impact_locator.py

# The output should look like this:
Executing buf breaking v2.bin --against v1.bin ...
Found 1 impacted field definitions from Buf:
 - Message: Entity | Field: name (FIELD_SAME_NAME)

=== Running Semgrep Analysis ===
python_app/main.py
  12┆ print(f"Entity Name: {entity.name}")
      ───────> Usage of deleted/modified Protobuf field 'name' on 'Entity'

csharp_app/Program.cs
  18┆ Console.WriteLine(entity.Name);
      ───────> Usage of deleted/modified Protobuf field 'Name' on 'Entity'

=== Running Tree-Sitter AST Analysis ===
Searching ASTs for accesses to removed field: 'name' (C#: 'Name')
  └─ [Tree-Sitter Impact Match] python_app/main.py:12:28 -> Property 'name' accessed
  └─ [Tree-Sitter Impact Match] ts_app/main.ts:15:22 -> Property 'name' accessed
  └─ [Tree-Sitter Impact Match] csharp_app/Program.cs:18:30 -> Property 'Name' accessed


# To run the Makefile that generates language-specific protobuf code and runs the python, csharp, and ts programs:

make

# Or run individual runtimes
make run-python
make run-csharp
make run-ts





