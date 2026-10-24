"""Canonical training and internal curation models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Behavior(StrEnum):
    SINGLE_TOOL = "single_tool"
    FINANCE_CONCEPT = "finance_concept"
    TOOL_AVAILABLE_BUT_UNNECESSARY = "tool_available_but_unnecessary"
    SIMPLE_CALCULATION = "simple_calculation"
    CLARIFICATION = "clarification"
    WEB_SEARCH = "web_search"
    SECURITY_CONFIRMATION = "security_confirmation"
    NO_SUITABLE_TOOL = "no_suitable_tool"
    UNSEEN_TOOL_SCHEMA = "unseen_tool_schema"
    SIMILAR_TOOL_SELECTION = "similar_tool_selection"
    PARALLEL_TOOLS = "parallel_tools"
    TOOL_RETRY = "tool_retry"
    TOOL_FAILURE_REPORT = "tool_failure_report"
    STALE_RESULT = "stale_result"
    SOURCE_CONFLICT = "source_conflict"
    NATURAL_LANGUAGE_ANSWER = "natural_language_answer"


class FunctionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["function"] = "function"
    function: FunctionDefinition


class FunctionCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    type: Literal["function"] = "function"
    function: FunctionCall


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

    @model_validator(mode="after")
    def validate_role_fields(self) -> Message:
        if self.role != "assistant" and self.tool_calls:
            raise ValueError("only assistant messages may contain tool_calls")
        if self.role == "assistant" and self.tool_calls and self.content.strip():
            raise ValueError("assistant tool-call message must have empty content")
        if self.role == "tool" and not self.tool_call_id:
            raise ValueError("tool message requires tool_call_id")
        if self.role != "tool" and self.tool_call_id is not None:
            raise ValueError("tool_call_id is only valid on tool messages")
        return self


class TrainingRecord(BaseModel):
    """The only schema exported for fine-tuning: id, messages, tools."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^TRFIN-[A-Za-z0-9_-]+$")
    messages: list[Message] = Field(min_length=2)
    tools: list[ToolDefinition] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_conversation(self) -> TrainingRecord:
        if not any(message.role == "user" for message in self.messages):
            raise ValueError("record requires a user message")
        if self.messages[-1].role != "assistant":
            raise ValueError("record must end with an assistant message")

        available = {tool.function.name for tool in self.tools}
        call_ids: set[str] = set()
        for message in self.messages:
            for call in message.tool_calls or []:
                if call.function.name not in available:
                    raise ValueError(f"tool call is not offered: {call.function.name}")
                if call.id:
                    if call.id in call_ids:
                        raise ValueError(f"duplicate tool call id: {call.id}")
                    call_ids.add(call.id)
            if message.role == "tool" and message.tool_call_id not in call_ids:
                raise ValueError(f"tool result references unknown call: {message.tool_call_id}")
        return self


class CandidateStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Candidate(BaseModel):
    """Minimal internal review state; never exported to model training data."""

    record: TrainingRecord
    behavior: Behavior
    domain: str
    source_id: str
    group_id: str
    status: CandidateStatus = CandidateStatus.PENDING
    errors: list[str] = Field(default_factory=list)
