---
name: behavior-taxonomy
description: Choose and encode the canonical 16 Turkish finance tool-use behaviors.
---

# Behavior taxonomy

Read this skill before classifying, generating, reviewing, or changing a training record. The
canonical machine identifiers live in `src/tcg/models.py::Behavior`; the executable examples live
in `src/tcg/builders.py::seed_candidates`.

## Decision order

Use the first applicable rule:

1. Protect the user: irreversible or account-changing action requires explicit confirmation.
2. Do not guess: request missing instrument, date range, amount, horizon, or comparison criterion.
3. Check freshness: current prices, current limits, tax, legislation, campaigns, and bank-specific
   conditions require an appropriate tool; use `web_search` when the provided finance tools cannot
   answer.
4. Select only from the record's offered `tools`, using descriptions and JSON Schema rather than a
   memorized function name.
5. Call independent tools together; serialize only when a later call needs an earlier result.
6. Stable concepts and arithmetic that can be solved from the prompt do not need a tool.
7. Never fabricate a tool, argument, result, freshness claim, or successful recovery.

## Canonical 16 behaviors

| # | `Behavior` value | Use when | Required training shape | Reject when |
|---|---|---|---|---|
| 1 | `single_tool` | One offered tool is necessary and sufficient. | `user → assistant(tool_calls=[one call])`; arguments satisfy that tool's schema. | No call, multiple unnecessary calls, unavailable tool, or invented argument. |
| 2 | `finance_concept` | The question asks for a stable finance definition or explanation and no tool is offered. | `user → assistant(content)` with a direct Turkish explanation. | A tool is called or the answer introduces time-sensitive facts as timeless. |
| 3 | `tool_available_but_unnecessary` | A stable concept can be answered directly although plausible distractor tools are offered. | Non-empty `tools`; `user → assistant(content)` with zero calls. | Calling a tool merely because one is available. |
| 4 | `simple_calculation` | All numbers and the formula are available in the prompt. | `user → assistant(content)` showing the compact calculation and result; zero calls. | External/current data is silently assumed or a tool is used for basic arithmetic. |
| 5 | `clarification` | A material parameter is missing or ambiguous. | `user → assistant(content)` asking only for the missing instrument/date/amount/horizon/criterion; zero calls. | Guessing the value, calling with placeholders, or asking irrelevant generic questions. |
| 6 | `web_search` | Current regulation, tax, campaign, bank condition, or public information is needed and finance tools do not cover it. | Offer `web_search`; assistant calls it with a specific Turkish query and, when known, authoritative domains. | Answering stale memory, searching for stable arithmetic, or using non-authoritative domains when primary sources are known. |
| 7 | `security_confirmation` | A transfer, order, cancellation, or other side effect would change money/account state. | Offer relevant tools if useful, but respond with a concise confirmation requirement before the side-effecting call. | Executing in the background, treating prior general consent as transaction confirmation, or exposing secrets. |
| 8 | `no_suitable_tool` | The requested capability is absent from offered tools. | `user → assistant(content)` honestly states the limitation; zero calls. | Inventing a function, repurposing an unrelated tool, or claiming a result. |
| 9 | `unseen_tool_schema` | The correct tool name/schema is novel and tests schema comprehension. | Select the novel offered tool from its description; emit schema-valid arguments. | Falling back to a familiar tool name or arguments not declared in the schema. |
| 10 | `similar_tool_selection` | Several offered tools overlap, but one best matches the requested entity/output. | Offer realistic distractors; call only the most specific correct tool. | Calling every similar tool, selecting by name similarity alone, or using a generic tool when a specific one fits. |
| 11 | `parallel_tools` | Two or more calls are independent and all results are needed. | One assistant turn contains at least two independent calls with distinct call IDs. | Serializing independent work or parallelizing calls with data dependencies. |
| 12 | `tool_retry` | A tool failed and the result indicates a retryable error, corrected argument, or replacement identifier. | First call → failed tool result → corrected second call; preserve call/result IDs. | Blindly repeating identical input, retrying a terminal error, or hiding the first failure. |
| 13 | `tool_failure_report` | The tool failure is terminal or retries are exhausted. | Call → error result → final Turkish answer states what could not be verified and avoids fabricated data. | Claiming success, returning an unverified value, or looping retries indefinitely. |
| 14 | `stale_result` | A result is explicitly stale or too old for the user's current-data request. | Call → stale result → final answer labels the timestamp/freshness problem and does not present it as current. | Dropping freshness metadata or reporting the value as live. |
| 15 | `source_conflict` | Required sources return materially conflicting values. | Calls/results from both sources → final answer names the conflict, prefers the primary source when justified, and preserves uncertainty. | Silently averaging, choosing without provenance, or pretending agreement. |
| 16 | `natural_language_answer` | Successful tool output must be turned into a user-facing answer. | Call → successful tool result → concise Turkish answer grounded only in the result, including relevant unit and effective time. | Echoing raw JSON, adding unsupported facts, or omitting material time/unit context. |

## Record-level invariants

- Exported rows contain exactly `id`, `messages`, and `tools`.
- Every called function exists in that row's `tools` array.
- Every call's arguments validate against the offered JSON Schema.
- `tool_call_id` links each tool result to the corresponding call.
- The final assistant turn is either the intended call target or a non-empty user-facing response.
- Internal behavior labels, source IDs, review status, errors, and `group_id` stay in SQLite; they
  never enter training rows.
- One record has one primary behavior label. Multi-turn recovery behaviors may contain ordinary
  calls, but the label describes the capability being tested.

## Change protocol

When adding, removing, or redefining a behavior, update all of these in one change:

1. `src/tcg/models.py::Behavior`
2. `src/tcg/builders.py::seed_candidates`
3. `src/tcg/validation.py` gates
4. `tests/test_behaviors.py` and any behavior-specific tests
5. this taxonomy and the README behavior list

Run `uv run tcg validate`, inspect `uv run tcg report`, then run the project checks. Structural
validity is not semantic approval; use `tcg review` before `tcg approve`.
