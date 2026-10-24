from collections import Counter

from tcg.live_cases import live_record_candidates
from tcg.models import Behavior
from tcg.settings import load_settings
from tcg.sources import load_tools, tool_map
from tcg.validation import validate_candidate


def _cases():
    settings = load_settings()
    return live_record_candidates(settings.system_prompt, tool_map(load_tools(settings)))


def test_live_records_cover_every_borsa_tool():
    cases = _cases()

    assert len(cases) == 115
    assert {case.behavior for case in cases} == {Behavior.NATURAL_LANGUAGE_ANSWER}
    assert len({case.record.id for case in cases}) == len(cases)
    assert {case.source_id for case in cases} == {"curated-live-v1"}
    assert Counter(case.behavior for case in cases) == {Behavior.NATURAL_LANGUAGE_ANSWER: 115}


def test_live_records_follow_call_result_answer_shape():
    for case in _cases():
        roles = [message.role for message in case.record.messages]
        assert roles == ["system", "user", "assistant", "tool", "assistant"]
        call_message = case.record.messages[2]
        assert call_message.content == ""
        assert len(call_message.tool_calls) == 1
        assert case.record.messages[3].tool_call_id == "c1"
        assert case.record.messages[3].content.strip()
        assert case.record.messages[4].content.strip()
        assert len(case.record.tools) == 1
        assert call_message.tool_calls[0].function.name == case.record.tools[0].function.name


def test_live_records_pass_schema_and_behavior_validation():
    failures = {
        case.record.id: validate_candidate(case).errors
        for case in _cases()
        if validate_candidate(case).errors
    }

    assert failures == {}
