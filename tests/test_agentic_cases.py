from collections import Counter

from tcg.agentic_cases import agentic_candidates
from tcg.models import Behavior
from tcg.settings import load_settings
from tcg.sources import load_tools, tool_map
from tcg.validation import validate_candidate

_AGENTIC_BEHAVIORS = {
    Behavior.CLARIFICATION,
    Behavior.SECURITY_CONFIRMATION,
    Behavior.PARALLEL_TOOLS,
    Behavior.TOOL_RETRY,
    Behavior.TOOL_FAILURE_REPORT,
    Behavior.STALE_RESULT,
    Behavior.SOURCE_CONFLICT,
}


def _cases():
    settings = load_settings()
    tools = tool_map(load_tools(settings))
    return agentic_candidates(settings.system_prompt, tools)


def test_agentic_cases_balance_underrepresented_behaviors():
    cases = _cases()

    assert len(cases) == 56
    assert Counter(case.behavior for case in cases) == {
        behavior: 8 for behavior in _AGENTIC_BEHAVIORS
    }
    assert len({case.record.id for case in cases}) == len(cases)
    assert {case.source_id for case in cases} == {"curated-agentic-v1"}


def test_agentic_cases_pass_schema_and_behavior_validation():
    failures = {
        case.record.id: validate_candidate(case).errors
        for case in _cases()
        if validate_candidate(case).errors
    }

    assert failures == {}


def test_agentic_tool_results_link_to_calls_and_end_in_grounded_answers():
    for case in _cases():
        calls = {
            call.id
            for message in case.record.messages
            for call in (message.tool_calls or [])
            if call.id is not None
        }
        results = {
            message.tool_call_id for message in case.record.messages if message.role == "tool"
        }

        assert results <= calls
        assert case.record.messages[-1].role == "assistant"
        assert case.record.messages[-1].content


def test_confirmation_cases_offer_authorized_tools_without_executing_them():
    confirmations = [case for case in _cases() if case.behavior == Behavior.SECURITY_CONFIRMATION]

    for case in confirmations:
        calls = [call for message in case.record.messages for call in (message.tool_calls or [])]
        assert calls == []
        assert len(case.record.tools) == 1
        assert "confirmation_token" in case.record.tools[0].function.parameters["required"]


def test_retry_cases_correct_arguments_and_finish_after_success():
    retries = [case for case in _cases() if case.behavior == Behavior.TOOL_RETRY]

    for case in retries:
        calls = [
            call.function.arguments
            for message in case.record.messages
            for call in (message.tool_calls or [])
        ]
        assert len(calls) == 2
        assert calls[0] != calls[1]
        assert len([message for message in case.record.messages if message.role == "tool"]) == 2
