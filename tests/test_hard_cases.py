from collections import Counter

from tcg.hard_cases import hard_case_candidates
from tcg.models import Behavior
from tcg.settings import load_settings
from tcg.sources import load_tools, tool_map
from tcg.validation import validate_candidate


def _cases():
    settings = load_settings()
    tools = tool_map(load_tools(settings))
    return hard_case_candidates(settings.system_prompt, tools), tools


def test_hard_cases_balance_security_and_unseen_schema():
    cases, _ = _cases()

    assert len(cases) == 16
    assert Counter(case.behavior for case in cases) == {
        Behavior.SECURITY_CONFIRMATION: 8,
        Behavior.UNSEEN_TOOL_SCHEMA: 8,
    }
    assert len({case.record.id for case in cases}) == len(cases)
    assert {case.source_id for case in cases} == {"curated-hard-v1"}


def test_hard_cases_pass_schema_and_behavior_validation():
    cases, _ = _cases()

    failures = {
        case.record.id: validate_candidate(case).errors
        for case in cases
        if validate_candidate(case).errors
    }
    assert failures == {}


def test_security_cases_offer_side_effect_tools_but_never_execute_them():
    cases, _ = _cases()
    security_cases = [case for case in cases if case.behavior == Behavior.SECURITY_CONFIRMATION]

    for case in security_cases:
        calls = [call for message in case.record.messages for call in (message.tool_calls or [])]
        assert calls == []
        assert len(case.record.tools) == 1
        parameters = case.record.tools[0].function.parameters
        assert "confirmation_token" in parameters["required"]


def test_unseen_cases_choose_novel_schema_over_familiar_distractors():
    cases, known_tools = _cases()
    unseen_cases = [case for case in cases if case.behavior == Behavior.UNSEEN_TOOL_SCHEMA]
    selected_names = set()

    for case in unseen_cases:
        calls = [call for message in case.record.messages for call in (message.tool_calls or [])]
        assert len(calls) == 1
        assert len(case.record.tools) >= 3
        selected_names.add(calls[0].function.name)
        assert calls[0].function.name not in known_tools

    assert len(selected_names) == len(unseen_cases)
