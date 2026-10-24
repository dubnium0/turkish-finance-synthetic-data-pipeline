"""Deterministic first-pass routing for the Turkish finance instruction source."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Behavior


@dataclass(frozen=True)
class Classification:
    behavior: Behavior
    domain: str


_CURRENT = re.compile(
    r"\b(şu an|şimdi|bugün|güncel|en son|son fiyat|kaç tl|bu günlerde)\b", re.IGNORECASE
)
_SEARCH = re.compile(
    r"\b(yapılandır\w*|mevzuat|vergi|stopaj|yasal|zorunlu|ceza|kampanya|"
    r"bankadan bankaya|erken ödeme|tazminat|düzenleme)\b",
    re.IGNORECASE,
)
_CALC = re.compile(r"\d.*\b(kaç|hesapla|ne kadar|oranı)\b|\b(kaç|hesapla).*\d", re.IGNORECASE)
_GUIDANCE = re.compile(
    r"\b(mantıklı mı|yatırmalı mıyım|almalı mıyım|satmalı mıyım)\b", re.IGNORECASE
)
_VAGUE = re.compile(r"^(faiz|hisse|fon|kredi) (ne kadar|kaç)[?]?$", re.IGNORECASE)


def classify_instruction(instruction: str, input_text: str = "") -> Classification:
    text = " ".join(part for part in (instruction, input_text) if part).strip()
    if _VAGUE.search(text):
        return Classification(Behavior.CLARIFICATION, "financial_clarification")
    if _SEARCH.search(text) and not re.search(r"\b(nedir|ne demek)\b", text, re.IGNORECASE):
        return Classification(Behavior.WEB_SEARCH, "banking_regulation")
    if _GUIDANCE.search(text):
        return Classification(Behavior.CLARIFICATION, "financial_guidance")
    if _CALC.search(text):
        return Classification(Behavior.SIMPLE_CALCULATION, "financial_calculation")
    if _CURRENT.search(text):
        return Classification(Behavior.SINGLE_TOOL, "dynamic_finance")
    return Classification(Behavior.FINANCE_CONCEPT, "financial_literacy")
