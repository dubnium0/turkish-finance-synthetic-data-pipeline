---
name: dataset-release
description: Validate and export a reproducible three-field dataset release.
---

# Dataset release

1. Run tests, Ruff, `tcg validate`, and `automation/harness.py validate`.
2. Export accepted candidates only.
3. Confirm every JSONL row has exactly `id`, `messages`, and `tools`.
4. Confirm tool calls reference offered tools and satisfy their JSON Schemas.
5. Confirm each `group_id` maps to one split internally.
6. Inspect behavior, domain, and source distributions; volume alone is not quality.
7. Keep the pinned source revision and row counts in `work/manifest.json`.
8. Do not publish generated state, rejected candidates, credentials, or local SQLite files.
