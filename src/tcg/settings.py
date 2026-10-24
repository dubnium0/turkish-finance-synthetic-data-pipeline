"""Project configuration loading."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SourceSettings(BaseModel):
    id: str
    url: str
    revision: str


class PathSettings(BaseModel):
    state_db: Path = Path("state/project.sqlite")
    work_dir: Path = Path("work")
    tool_catalog: Path = Path("data/tools/borsa_mcp.json")
    tool_overrides: Path = Path("data/tools/borsa_overrides.tr.yaml")


class PipelineSettings(BaseModel):
    project_name: str = "Finetool-TR"
    system_prompt: str
    source: SourceSettings
    paths: PathSettings = Field(default_factory=PathSettings)
    split_seed: int = 42
    splits: dict[str, float] = Field(
        default_factory=lambda: {"train": 0.8, "validation": 0.1, "test": 0.1}
    )


def load_settings(path: str | Path = "config.yaml") -> PipelineSettings:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return PipelineSettings.model_validate(raw)
