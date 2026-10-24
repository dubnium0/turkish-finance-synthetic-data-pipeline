from tcg.models import Behavior, Candidate, Message, ToolCall, ToolDefinition, TrainingRecord
from tcg.validation import validate_candidate


def test_json_schema_rejects_wrong_argument_type():
    tool = ToolDefinition.model_validate(
        {
            "type": "function",
            "function": {
                "name": "get_history",
                "parameters": {
                    "type": "object",
                    "properties": {"date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}},
                    "required": ["date"],
                    "additionalProperties": False,
                },
            },
        }
    )
    record = TrainingRecord(
        id="TRFIN-TEST-DATE",
        messages=[
            Message(role="user", content="3 Nisan fiyatı?"),
            Message(
                role="assistant",
                tool_calls=[
                    ToolCall.model_validate(
                        {"function": {"name": "get_history", "arguments": {"date": "03/04/2025"}}}
                    )
                ],
            ),
        ],
        tools=[tool],
    )
    candidate = Candidate(
        record=record,
        behavior=Behavior.SINGLE_TOOL,
        domain="market_data",
        source_id="test",
        group_id="date",
    )

    checked = validate_candidate(candidate)
    assert checked.errors
    assert "does not match" in checked.errors[0]
