---
name: tool-schema-onboarding
description: Add real or synthetic MCP-compatible tool schemas without teaching name memorization.
---

# Tool schema onboarding

1. Preserve function and parameter identifiers exactly as runtime exposes them.
2. Keep the full JSON Schema: required fields, types, enums, patterns, bounds, and
   `additionalProperties`.
3. Translate only human-readable descriptions through the overrides file.
4. Add schema variants with different names and argument names for the same financial intent.
5. Every expected call must reference a tool offered in that record.
6. Validate arguments against the raw schema with `jsonschema`.
7. Put unseen names/signatures in validation or test groups to measure schema-based transfer.
8. Never treat a fabricated but unavailable function name as a valid call.
