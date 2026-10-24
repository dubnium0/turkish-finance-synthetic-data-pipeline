from tcg.calculation_cases import calculation_candidates
from tcg.models import Behavior
from tcg.settings import load_settings
from tcg.validation import validate_candidate


def test_calculation_cases_are_unique_arithmetic_only_records():
    cases = calculation_candidates(load_settings().system_prompt)

    assert len(cases) == 62
    assert len({case.record.id for case in cases}) == len(cases)
    assert {case.source_id for case in cases} == {"curated-calculation-v1"}
    assert {case.behavior for case in cases} == {Behavior.SIMPLE_CALCULATION}
    assert len({case.domain for case in cases}) >= 58

    for case in cases:
        assert case.record.tools == []
        assert not any(message.tool_calls for message in case.record.messages)
        assert case.record.messages[-1].content


def test_calculation_cases_pass_behavior_validation():
    cases = calculation_candidates(load_settings().system_prompt)

    failures = {
        case.record.id: validate_candidate(case).errors
        for case in cases
        if validate_candidate(case).errors
    }
    assert failures == {}
