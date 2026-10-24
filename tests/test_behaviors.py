from tcg.builders import seed_candidates
from tcg.models import Behavior
from tcg.settings import load_settings
from tcg.sources import load_tools, tool_map
from tcg.validation import validate_candidate


def test_seed_set_covers_behaviors_without_live_answer_traces():
    settings = load_settings()
    seeds = seed_candidates(settings.system_prompt, tool_map(load_tools(settings)))

    assert len(seeds) == 15
    assert {seed.behavior for seed in seeds} == set(Behavior) - {Behavior.NATURAL_LANGUAGE_ANSWER}


def test_all_seed_records_pass_schema_and_behavior_gates():
    settings = load_settings()
    seeds = seed_candidates(settings.system_prompt, tool_map(load_tools(settings)))

    failures = {
        seed.record.id: validate_candidate(seed).errors
        for seed in seeds
        if validate_candidate(seed).errors
    }
    assert failures == {}


def test_security_confirmation_never_executes_transfer():
    settings = load_settings()
    seeds = seed_candidates(settings.system_prompt, tool_map(load_tools(settings)))
    security = next(seed for seed in seeds if seed.behavior == Behavior.SECURITY_CONFIRMATION)

    calls = [call for message in security.record.messages for call in (message.tool_calls or [])]
    assert calls == []
    assert "açık onay" in security.record.messages[-1].content
