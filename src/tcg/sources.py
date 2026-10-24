"""Pinned source and tool-catalog adapters."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from .models import ToolDefinition
from .settings import PipelineSettings
from .storage import Store


def _source_id(source: str, instruction: str, input_text: str) -> str:
    digest = hashlib.sha256(f"{source}\0{instruction}\0{input_text}".encode()).hexdigest()[:16]
    return f"SRC-{digest.upper()}"


def fetch_json(location: str) -> Any:
    path = Path(location)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    request = urllib.request.Request(location, headers={"User-Agent": "finetool-tr/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return json.load(response)


def ingest_instruction_source(
    settings: PipelineSettings, store: Store, limit: int | None = None
) -> int:
    payload = fetch_json(settings.source.url)
    if not isinstance(payload, list):
        raise ValueError("instruction source must be a JSON array")
    selected = payload[:limit] if limit is not None else payload
    rows: list[dict[str, str]] = []
    for raw in selected:
        instruction = str(raw.get("instruction") or "").strip()
        input_text = str(raw.get("input") or "").strip()
        output = str(raw.get("output") or "").strip()
        if not instruction or not output:
            continue
        rows.append(
            {
                "id": _source_id(settings.source.id, instruction, input_text),
                "source_id": settings.source.id,
                "instruction": instruction,
                "input": input_text,
                "output": output,
                "raw_json": json.dumps(raw, ensure_ascii=False, sort_keys=True),
            }
        )
    return store.add_source_rows(rows)


def _apply_overrides(tool: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    function = tool["function"]
    override = overrides.get(function["name"])
    if not override:
        return tool
    function["description"] = override.get("description", function.get("description", ""))
    properties = (function.get("parameters") or {}).get("properties") or {}
    for name, description in (override.get("parameters") or {}).items():
        if name in properties:
            properties[name]["description"] = description
    return tool


def load_tools(settings: PipelineSettings) -> list[ToolDefinition]:
    raw = json.loads(settings.paths.tool_catalog.read_text(encoding="utf-8"))
    overrides = yaml.safe_load(settings.paths.tool_overrides.read_text(encoding="utf-8")) or {}
    web_search = json.loads(Path("data/tools/web_search.json").read_text(encoding="utf-8"))
    tools = [_apply_overrides(tool, overrides) for tool in raw]
    tools.append(web_search)
    tools.extend(_synthetic_tools())
    return [ToolDefinition.model_validate(tool) for tool in tools]


def _synthetic_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_instrument_snapshot",
                "description": "Belirtilen piyasadaki finansal enstrümanın son fiyatını getirir.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instrument_code": {"type": "string"},
                        "venue": {"type": "string", "enum": ["XIST", "XNAS", "XNYS"]},
                    },
                    "required": ["instrument_code", "venue"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_account_balance",
                "description": (
                    "Hesap bakiyesini salt okunur biçimde getirir; para transferi yapmaz."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {"account_id": {"type": "string"}},
                    "required": ["account_id"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_bank_transfer",
                "description": (
                    "Geri döndürülemez para transferi yapar; açık kullanıcı onayı gerekir."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string"},
                        "amount": {"type": "number", "exclusiveMinimum": 0},
                        "currency": {"type": "string", "enum": ["TRY", "USD", "EUR"]},
                        "confirmation_token": {"type": "string", "minLength": 4},
                    },
                    "required": ["recipient", "amount", "currency", "confirmation_token"],
                    "additionalProperties": False,
                },
            },
        },
    ]


def tool_map(tools: list[ToolDefinition]) -> dict[str, ToolDefinition]:
    return {tool.function.name: tool for tool in tools}
