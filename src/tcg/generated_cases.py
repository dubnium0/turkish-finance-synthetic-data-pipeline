"""Load semantically reviewed records produced by the configured data-generation model."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import (
    Behavior,
    Candidate,
    FunctionCall,
    Message,
    ToolCall,
    ToolDefinition,
    TrainingRecord,
)

_SOURCE_ID = "curated-generated-v1"
_SOURCE_PATH = Path("data/generated/targeted_behavior_v1.jsonl")
_GENERATED_BEHAVIORS = {
    Behavior.CLARIFICATION,
    Behavior.NO_SUITABLE_TOOL,
    Behavior.WEB_SEARCH,
}


class GeneratedCase(BaseModel):
    """Versioned generation output with provenance kept outside training rows."""

    model_config = ConfigDict(extra="forbid")

    behavior: Literal["clarification", "no_suitable_tool", "web_search"]
    key: str = Field(pattern=r"^[a-z0-9-]+$")
    domain: str = Field(min_length=3)
    group_id: str = Field(pattern=r"^[a-z0-9-]+$")
    user: str = Field(min_length=8)
    assistant: str | None = None
    offered_tools: list[str] | None = None
    query: str | None = None
    domains: list[str] | None = None
    model: str = Field(min_length=3)
    generated_at: date

    @model_validator(mode="after")
    def validate_shape(self) -> GeneratedCase:
        behavior = Behavior(self.behavior)
        if behavior == Behavior.WEB_SEARCH:
            if self.assistant is not None or self.offered_tools is not None:
                raise ValueError(
                    "web_search source rows use query/domains, not assistant/offered_tools"
                )
            if not self.query or not self.domains:
                raise ValueError("web_search source row requires query and domains")
        else:
            if not self.assistant or not self.offered_tools:
                raise ValueError(
                    f"{behavior.value} source row requires assistant and offered_tools"
                )
            if self.query is not None or self.domains is not None:
                raise ValueError(f"{behavior.value} source row cannot contain query/domains")
        return self


def _load_rows(path: Path) -> list[GeneratedCase]:
    rows = [
        GeneratedCase.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    keys = [row.key for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Model üretim kaynağında yinelenen key var")
    groups = [(row.behavior, row.group_id) for row in rows]
    if len(groups) != len(set(groups)):
        raise ValueError("Model üretim kaynağında yinelenen behavior/group_id var")
    return rows


def generated_candidates(
    system: str,
    tools: dict[str, ToolDefinition],
    source_path: Path = _SOURCE_PATH,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for index, row in enumerate(_load_rows(source_path), start=1):
        behavior = Behavior(row.behavior)
        if behavior not in _GENERATED_BEHAVIORS:
            raise ValueError(f"Desteklenmeyen üretilmiş behavior: {behavior.value}")

        if behavior == Behavior.WEB_SEARCH:
            offered = [tools["web_search"]]
            turns = [
                Message(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            function=FunctionCall(
                                name="web_search",
                                arguments={"query": row.query, "domains": row.domains},
                            )
                        )
                    ],
                )
            ]
        else:
            offered = [tools[name] for name in row.offered_tools or []]
            turns = [Message(role="assistant", content=row.assistant or "")]

        candidates.append(
            Candidate(
                record=TrainingRecord(
                    id=f"TRFIN-generated-{index:04d}",
                    messages=[
                        Message(role="system", content=system),
                        Message(role="user", content=row.user),
                        *turns,
                    ],
                    tools=offered,
                ),
                behavior=behavior,
                domain=row.domain,
                source_id=_SOURCE_ID,
                group_id=f"{_SOURCE_ID}:{row.behavior}:{row.group_id}",
            )
        )
    return candidates
