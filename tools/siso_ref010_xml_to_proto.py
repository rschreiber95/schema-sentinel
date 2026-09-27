#!/usr/bin/env python3
"""Convert SISO-REF-010 XML enumeration tables to a Protocol Buffers .proto file.

Only <enum> and <enumrow> elements are emitted. Other REF-010 structures
(records, bitfields, COTs, dictionaries, etc.) are intentionally ignored.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

PROTO_KEYWORDS = {
    "syntax", "import", "weak", "public", "package", "option", "optional",
    "required", "repeated", "oneof", "map", "reserved", "to", "max",
    "enum", "message", "service", "rpc", "returns", "stream", "extensions",
    "extend", "group", "double", "float", "int32", "int64", "uint32",
    "uint64", "sint32", "sint64", "fixed32", "fixed64", "sfixed32",
    "sfixed64", "bool", "string", "bytes", "true", "false",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def ascii_text(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def words(text: str) -> list[str]:
    text = ascii_text(text)
    return re.findall(r"[A-Za-z0-9]+", text)


def pascal_name(text: str, fallback: str) -> str:
    parts = words(text)
    name = "".join(p[:1].upper() + p[1:] for p in parts) or fallback
    if name[0].isdigit():
        name = "E" + name
    if name.lower() in PROTO_KEYWORDS:
        name += "Enum"
    return name


def upper_snake(text: str, fallback: str = "VALUE") -> str:
    parts = words(text)
    name = "_".join(p.upper() for p in parts) or fallback
    if name[0].isdigit():
        name = "V_" + name
    if name.lower() in PROTO_KEYWORDS:
        name += "_VALUE"
    return name


def proto_comment(text: str) -> str:
    # Keep generated comments single-line and safe.
    return " ".join((text or "").replace("\r", " ").replace("\n", " ").split())


def decimal_int(value: str) -> int:
    # REF-010 values such as "0010" are decimal 10, not octal.
    return int(value.strip(), 10)


def unique_name(base: str, used: set[str], suffix: str) -> str:
    candidate = base
    if candidate not in used:
        used.add(candidate)
        return candidate
    candidate = f"{base}_{suffix}"
    n = 2
    while candidate in used:
        candidate = f"{base}_{suffix}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def convert(xml_path: Path, proto_path: Path, package: str) -> tuple[int, int]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    enum_elements = [child for child in root if local_name(child.tag) == "enum"]

    out: list[str] = [
        'syntax = "proto3";',
        "",
        f"package {package};",
        "",
        "// Generated from SISO-REF-010 XML.",
        "// Only REF-010 <enum>/<enumrow> tables are included.",
        "// SISO attribution: Reprinted with permission from SISO Inc.",
        "",
    ]

    used_enum_names: set[str] = set()
    # Protobuf enum values use the enclosing scope, so names must be unique
    # across all top-level enums in the same package. Keep description-only
    # names where possible and append _UID_<uid> only on an actual collision.
    used_global_value_names: set[str] = set()
    synthetic_zero_count = 0

    for enum_el in enum_elements:
        uid = enum_el.get("uid", "unknown")
        src_name = enum_el.get("name", f"Enum {uid}")
        size = enum_el.get("size")
        applicability = enum_el.get("applicability")

        enum_name = unique_name(
            pascal_name(src_name, f"Enum{uid}"), used_enum_names, f"Uid{uid}"
        )

        meta = [f"REF-010 UID {uid}", f'name: "{proto_comment(src_name)}"']
        if size:
            meta.append(f"size: {size} bit(s)")
        if applicability:
            meta.append(f"applicability: {proto_comment(applicability)}")
        out.append("// " + "; ".join(meta))
        out.append(f"enum {enum_name} {{")

        rows = [child for child in enum_el if local_name(child.tag) == "enumrow"]
        parsed_rows: list[tuple[int, str]] = []
        for row in rows:
            raw_value = row.get("value")
            if raw_value is None:
                continue
            value = decimal_int(raw_value)
            if not -(2**31) <= value <= 2**31 - 1:
                raise ValueError(
                    f"UID {uid} ({src_name}) has value {value}, outside protobuf enum int32 range"
                )
            parsed_rows.append((value, row.get("description", f"Value {raw_value}")))

        # proto3 requires the first enum value to be numeric zero.
        zero_rows = [r for r in parsed_rows if r[0] == 0]
        nonzero_rows = [r for r in parsed_rows if r[0] != 0]
        if zero_rows:
            ordered_rows = zero_rows + nonzero_rows
        else:
            synthetic_zero_count += 1
            out.append("  // Synthetic value required by proto3; not present in REF-010.")
            synthetic_name = unique_name("UNSPECIFIED", used_global_value_names, f"UID_{uid}")
            out.append(f"  {synthetic_name} = 0;")
            ordered_rows = parsed_rows

        used_value_names: set[str] = set()
        for value, description in ordered_rows:
            base = upper_snake(description)
            # First make the name unique inside this enum, then make it unique
            # across the package (required for top-level protobuf enums).
            local_value_name = unique_name(
                base, used_value_names, str(value).replace("-", "NEG")
            )
            value_name = unique_name(
                local_value_name, used_global_value_names, f"UID_{uid}"
            )
            out.append(f"  // {proto_comment(description)}")
            out.append(f"  {value_name} = {value};")

        out.append("}")
        out.append("")

    proto_path.write_text("\n".join(out), encoding="utf-8")
    return len(enum_elements), synthetic_zero_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert SISO-REF-010 XML enum tables to protobuf enums."
    )
    parser.add_argument("xml", type=Path, help="Input SISO-REF-010.xml")
    parser.add_argument("proto", type=Path, help="Output .proto path")
    parser.add_argument(
        "--package", default="siso.ref010", help="Protobuf package (default: siso.ref010)"
    )
    args = parser.parse_args()

    count, synthetic = convert(args.xml, args.proto, args.package)
    print(f"Wrote {count} enums to {args.proto}")
    print(f"Inserted synthetic zero values in {synthetic} enums for proto3 compatibility")


if __name__ == "__main__":
    main()
