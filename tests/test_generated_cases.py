import json
from collections import Counter
from pathlib import Path

from tcg.generated_cases import generated_candidates
from tcg.models import Behavior
from tcg.settings import load_settings
from tcg.sources import load_tools, tool_map
from tcg.validation import validate_candidate

_SOURCE = Path("data/generated/targeted_behavior_v1.jsonl")
_MODEL = "data-generation-model"


def _cases():
    settings = load_settings()
    return generated_candidates(settings.system_prompt, tool_map(load_tools(settings)))


def test_generated_source_has_expected_provenance_and_diversity():
    rows = [json.loads(line) for line in _SOURCE.read_text(encoding="utf-8").splitlines()]

    assert Counter(row["behavior"] for row in rows) == {
        "clarification": 30,
        "no_suitable_tool": 30,
        "web_search": 36,
    }
    assert {row["model"] for row in rows} == {_MODEL}
    assert {row["generated_at"] for row in rows} == {"2026-10-24"}
    assert len({row["key"] for row in rows}) == 96
    assert len({(row["behavior"], row["group_id"]) for row in rows}) == 96

    web_domains = Counter(row["domain"] for row in rows if row["behavior"] == Behavior.WEB_SEARCH)
    assert set(web_domains.values()) == {6}
    assert len(web_domains) == 6


def test_generated_candidates_pass_schema_and_behavior_validation():
    cases = _cases()
    failures = {
        case.record.id: validate_candidate(case).errors
        for case in cases
        if validate_candidate(case).errors
    }

    assert failures == {}
    assert {case.source_id for case in cases} == {"curated-generated-v1"}
    assert len({case.group_id for case in cases}) == len(cases) == 96


def test_generated_no_call_behaviors_do_not_call_tools():
    for case in _cases():
        calls = [call for message in case.record.messages for call in message.tool_calls or []]
        if case.behavior in {Behavior.CLARIFICATION, Behavior.NO_SUITABLE_TOOL}:
            assert calls == []
        elif case.behavior == Behavior.WEB_SEARCH:
            assert len(calls) == 1
            assert calls[0].function.name == "web_search"
