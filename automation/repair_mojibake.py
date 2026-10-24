#!/usr/bin/env python3
"""Repair recoverable mojibake in curated live-data records."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from ftfy import fix_text

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    (ROOT / "data" / "borsa_live_records.jsonl", True),
    (ROOT / "data" / "tools" / "borsa_mcp.json", False),
)
MOJIBAKE_MARKERS = ("Ã", "Ä", "Å", "�")


def _repair_value(value, *, location: str):
    if isinstance(value, str):
        repaired = fix_text(value)
        if "�" in repaired:
            raise ValueError(f"{location}: unrecoverable Unicode marker")
        if any(marker in repaired for marker in MOJIBAKE_MARKERS):
            raise ValueError(f"{location}: mojibake remains after repair")
        return repaired, int(repaired != value)
    if isinstance(value, list):
        changed = 0
        repaired_items = []
        for index, item in enumerate(value):
            repaired, item_changes = _repair_value(item, location=f"{location}[{index}]")
            repaired_items.append(repaired)
            changed += item_changes
        return repaired_items, changed
    if isinstance(value, dict):
        changed = 0
        repaired_mapping = {}
        for key, item in value.items():
            repaired, item_changes = _repair_value(item, location=f"{location}.{key}")
            repaired_mapping[key] = repaired
            changed += item_changes
        return repaired_mapping, changed
    return value, 0


def _repair(path: Path, *, jsonl: bool, check: bool) -> tuple[int, int]:
    if jsonl:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        value = rows
    else:
        value = json.loads(path.read_text(encoding="utf-8"))
        rows = value if isinstance(value, list) else [value]
    repaired_rows, changed = _repair_value(value, location=str(path))

    if changed and not check:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            if jsonl:
                for row in repaired_rows:
                    stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            else:
                json.dump(repaired_rows, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)

    return len(rows), changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total_rows = 0
    total_changes = 0
    for path, jsonl in TARGETS:
        rows, changes = _repair(path, jsonl=jsonl, check=args.check)
        total_rows += rows
        total_changes += changes
        print(f"{path.relative_to(ROOT)}: rows={rows} changed_fields={changes}")

    if args.check and total_changes:
        print(f"repair required: {total_changes} field(s)")
        return 1
    print(f"checked_rows={total_rows} changed_fields={total_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
