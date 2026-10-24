"""Deterministic validation gates for canonical training records."""

from __future__ import annotations

from collections import Counter

import jsonschema

from .models import Behavior, Candidate, CandidateStatus

_CALL_BEHAVIORS = {
    Behavior.SINGLE_TOOL,
    Behavior.WEB_SEARCH,
    Behavior.UNSEEN_TOOL_SCHEMA,
    Behavior.SIMILAR_TOOL_SELECTION,
    Behavior.PARALLEL_TOOLS,
    Behavior.TOOL_RETRY,
    Behavior.TOOL_FAILURE_REPORT,
    Behavior.STALE_RESULT,
    Behavior.SOURCE_CONFLICT,
    Behavior.NATURAL_LANGUAGE_ANSWER,
}


def validate_candidate(candidate: Candidate) -> Candidate:
    errors: list[str] = []
    record = candidate.record
    offered = {tool.function.name: tool for tool in record.tools}
    calls = [call for message in record.messages for call in (message.tool_calls or [])]

    for call in calls:
        schema = offered[call.function.name].function.parameters
        try:
            jsonschema.validate(call.function.arguments, schema)
        except jsonschema.ValidationError as error:
            path = "/".join(str(item) for item in error.absolute_path) or "root"
            errors.append(f"{call.function.name}@{path}: {error.message}")

    if candidate.behavior in _CALL_BEHAVIORS and not calls:
        errors.append(f"{candidate.behavior.value} requires at least one tool call")
    if candidate.behavior == Behavior.PARALLEL_TOOLS:
        first_assistant_calls = next(
            (len(message.tool_calls or []) for message in record.messages if message.tool_calls), 0
        )
        if first_assistant_calls < 2:
            errors.append("parallel_tools requires at least two calls in one assistant turn")
    if candidate.behavior == Behavior.TOOL_RETRY and (
        len(calls) < 2 or not any(message.role == "tool" for message in record.messages)
    ):
        errors.append("tool_retry requires a failed result followed by another call")
    if (
        candidate.behavior
        in {
            Behavior.FINANCE_CONCEPT,
            Behavior.TOOL_AVAILABLE_BUT_UNNECESSARY,
            Behavior.SIMPLE_CALCULATION,
            Behavior.CLARIFICATION,
            Behavior.SECURITY_CONFIRMATION,
            Behavior.NO_SUITABLE_TOOL,
        }
        and calls
    ):
        errors.append(f"{candidate.behavior.value} must not call a tool")

    final = record.messages[-1]
    if not final.tool_calls and not final.content.strip():
        errors.append("final assistant response is empty")

    candidate.errors = errors
    candidate.status = CandidateStatus.INVALID if errors else CandidateStatus.VALID
    return candidate


def validate_collection(candidates: list[Candidate]) -> list[str]:
    errors: list[str] = []
    ids = Counter(candidate.record.id for candidate in candidates)
    duplicate_ids = sorted(key for key, count in ids.items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate ids: {', '.join(duplicate_ids[:5])}")
    return errors
