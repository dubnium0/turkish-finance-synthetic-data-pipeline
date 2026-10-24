import pytest
from pydantic import ValidationError

from tcg.models import Message, ToolCall, ToolDefinition, TrainingRecord

TOOL = ToolDefinition.model_validate(
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Fiyat getirir.",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"],
            },
        },
    }
)


def test_training_record_rejects_unoffered_tool():
    with pytest.raises(ValidationError, match="tool call is not offered"):
        TrainingRecord(
            id="TRFIN-TEST-1",
            messages=[
                Message(role="user", content="Fiyat?"),
                Message(
                    role="assistant",
                    tool_calls=[
                        ToolCall.model_validate(
                            {
                                "function": {
                                    "name": "invented_tool",
                                    "arguments": {"symbol": "GARAN"},
                                }
                            }
                        )
                    ],
                ),
            ],
            tools=[TOOL],
        )


def test_assistant_cannot_mix_text_and_tool_call():
    with pytest.raises(ValidationError, match="must have empty content"):
        Message.model_validate(
            {
                "role": "assistant",
                "content": "Çağırıyorum",
                "tool_calls": [
                    {"type": "function", "function": {"name": "get_price", "arguments": {}}}
                ],
            }
        )
