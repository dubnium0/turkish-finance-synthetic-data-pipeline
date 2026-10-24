"""Gercek MCP sonuclariyla uretilmis canli kayitlar."""
# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    Behavior,
    Candidate,
    FunctionCall,
    Message,
    ToolCall,
    ToolDefinition,
    TrainingRecord,
)

_DOMAINS = {
    "search_symbol": "instrument_search",
    "get_profile": "company_profile",
    "get_quote": "market_quote",
    "get_historical_data": "price_history",
    "get_technical_analysis": "technical_analysis",
    "get_analyst_data": "analyst_ratings",
    "get_earnings": "earnings",
    "get_financial_statements": "financial_statements",
    "get_financial_ratios": "financial_ratios",
    "get_corporate_actions": "corporate_actions",
    "get_news": "kap_news",
    "screen_securities": "security_screening",
    "scan_stocks": "technical_screening",
    "compare_assets": "asset_comparison",
    "get_sector_comparison": "sector_comparison",
    "get_crypto_market": "crypto_market",
    "get_economic_calendar": "economic_calendar",
    "get_bond_yields": "bond_yields",
    "get_fund_data": "fund_data",
    "screen_funds": "fund_screening",
    "get_index_data": "index_data",
    "get_macro_data": "macro_inflation",
    "get_evds_data": "evds_series",
}

_SOURCE_ID = "curated-live-v1"
_RECORDS_PATH = Path("data/borsa_live_records.jsonl")


def live_record_candidates(
    system: str, tools: dict[str, ToolDefinition], records_path: Path = _RECORDS_PATH
) -> list[Candidate]:
    """Build candidates from live tool executions with grounded finals."""
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for line in records_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        tool = tools[row["tool"]]
        record = TrainingRecord(
            id=row["id"],
            messages=[
                Message(role="system", content=system),
                Message(role="user", content=row["user"]),
                Message(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            function=FunctionCall(name=row["tool"], arguments=row["arguments"]),
                        )
                    ],
                ),
                Message(role="tool", tool_call_id="c1", content=row["result"]),
                Message(role="assistant", content=row["final"]),
            ],
            tools=[tool],
        )
        candidates.append(
            Candidate(
                record=record,
                behavior=Behavior.NATURAL_LANGUAGE_ANSWER,
                domain=_DOMAINS.get(row["tool"], "market_data"),
                source_id=_SOURCE_ID,
                group_id=row["group_id"],
            )
        )
    return candidates
