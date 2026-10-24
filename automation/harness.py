#!/usr/bin/env python3
"""Small project-local harness status and structural validation commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = [
    Path("AGENTS.md"),
    Path("README.md"),
    Path("config.yaml"),
    Path("capability/profile.json"),
    Path("capability/evals.json"),
    Path("data/tools/borsa_mcp.json"),
    Path("src/tcg/models.py"),
]
SKILLS = {
    "behavior-taxonomy",
    "dataset-curation",
    "tool-schema-onboarding",
    "financial-safety-review",
    "dataset-release",
}


def validate() -> dict:
    missing = [str(path) for path in REQUIRED if not path.exists()]
    actual_skills = {path.parent.name for path in Path(".agents/skills").glob("*/SKILL.md")}
    missing_skills = sorted(SKILLS - actual_skills)

    from tcg.models import Behavior

    taxonomy_path = Path(".agents/skills/behavior-taxonomy/SKILL.md")
    taxonomy = taxonomy_path.read_text(encoding="utf-8") if taxonomy_path.exists() else ""
    missing_behaviors = [
        behavior.value for behavior in Behavior if f"`{behavior.value}`" not in taxonomy
    ]
    return {
        "valid": not missing and not missing_skills and not missing_behaviors,
        "missing_files": missing,
        "missing_skills": missing_skills,
        "missing_behaviors": missing_behaviors,
    }


def status() -> dict:
    database = Path("state/project.sqlite")
    result = {
        "database": "ready" if database.exists() else "not_initialized",
        "exports": sorted(path.name for path in Path("work").glob("*.jsonl"))
        if Path("work").exists()
        else [],
    }
    if database.exists():
        from tcg.pipeline import report
        from tcg.settings import load_settings

        result["curation"] = report(load_settings())
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status", "validate"))
    args = parser.parse_args()
    result = status() if args.command == "status" else validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
