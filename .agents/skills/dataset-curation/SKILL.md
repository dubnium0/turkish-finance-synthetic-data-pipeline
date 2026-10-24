---
name: dataset-curation
description: Import, classify, build, and review Turkish finance training records.
---

# Dataset curation

1. Read `.agents/skills/behavior-taxonomy/SKILL.md`; assign exactly one canonical behavior.
2. Pin every remote source revision in `config.yaml`.
3. Import source rows with `tcg ingest`; never copy remote answers directly into accepted output.
4. Classify the next assistant action using the taxonomy's decision order and transcript shape.
5. Build canonical `TrainingRecord` values only: `id`, `messages`, `tools`.
6. For no-call examples, include plausible distractor tools in a meaningful share of records.
7. Run `tcg validate`; inspect invalid records and behavior distribution.
8. Inspect candidates with `tcg review`, then approve reviewed IDs or a reviewed source explicitly.
   `tcg approve --all-valid` is allowed only after every valid candidate was semantically reviewed.
9. Keep paraphrases in one internal `group_id` so train/test leakage is impossible.
