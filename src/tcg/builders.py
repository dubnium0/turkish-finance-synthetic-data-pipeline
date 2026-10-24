"""Build canonical records from reviewed sources and deterministic behavior seeds."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from .classify import Classification
from .models import (
    Behavior,
    Candidate,
    FunctionCall,
    Message,
    ToolCall,
    ToolDefinition,
    TrainingRecord,
)


def _id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()[:12].upper()
    return f"TRFIN-{prefix}-{digest}"


def _group(value: str) -> str:
    return hashlib.sha256(value.lower().strip().encode()).hexdigest()[:16]


def _tool_call(name: str, arguments: dict, call_id: str | None = None) -> ToolCall:
    return ToolCall(id=call_id, function=FunctionCall(name=name, arguments=arguments))


def _record(
    record_id: str,
    system: str,
    user: str,
    assistant: Message,
    tools: Iterable[ToolDefinition] = (),
    middle: Iterable[Message] = (),
) -> TrainingRecord:
    return TrainingRecord(
        id=record_id,
        messages=[
            Message(role="system", content=system),
            Message(role="user", content=user),
            *middle,
            assistant,
        ],
        tools=list(tools),
    )


def build_instruction_candidate(
    row: dict[str, str],
    classification: Classification,
    system_prompt: str,
    tools: dict[str, ToolDefinition],
    reference_year: int,
) -> Candidate:
    question = " ".join(part for part in (row["instruction"], row["input"]) if part).strip()
    behavior = classification.behavior
    selected: list[ToolDefinition] = []

    if behavior == Behavior.WEB_SEARCH:
        domains = _official_domains(question)
        selected = [tools["web_search"]]
        assistant = Message(
            role="assistant",
            tool_calls=[
                _tool_call(
                    "web_search",
                    {
                        "query": f"{reference_year} Türkiye {question}",
                        "domains": domains,
                    },
                )
            ],
        )
    elif behavior == Behavior.SINGLE_TOOL:
        tool_name, arguments = _route_dynamic(question)
        selected = [tools[tool_name]]
        assistant = Message(role="assistant", tool_calls=[_tool_call(tool_name, arguments)])
    elif behavior == Behavior.CLARIFICATION:
        if any(term in question.casefold() for term in ("kredi", "borç", "nakit avans")):
            clarification = (
                "Tutarı, geri ödeme vadesini, uygulanacak faiz ve ücretleri ve "
                "değerlendirdiğiniz alternatifi belirtir misiniz?"
            )
            selected = []
        else:
            clarification = (
                "Karşılaştırmayı yapabilmem için ilgili ürün veya varlığı, tarih aralığını "
                "ve değerlendirmek istediğiniz ölçütü netleştirir misiniz?"
            )
            selected = [tools["get_quote"], tools["get_historical_data"]]
        assistant = Message(role="assistant", content=clarification)
    else:
        assistant = Message(role="assistant", content=row["output"])
        if behavior == Behavior.FINANCE_CONCEPT:
            selected = [tools["get_quote"]]
            behavior = Behavior.TOOL_AVAILABLE_BUT_UNNECESSARY

    record = _record(
        _id("IT", row["id"]),
        system_prompt,
        question,
        assistant,
        selected,
    )
    return Candidate(
        record=record,
        behavior=behavior,
        domain=classification.domain,
        source_id=row["source_id"],
        group_id=_group(row["instruction"]),
    )


def _official_domains(question: str) -> list[str]:
    low = question.lower()
    if any(word in low for word in ("vergi", "stopaj")):
        return ["gib.gov.tr", "resmigazete.gov.tr"]
    if any(word in low for word in ("kredi", "banka", "kart", "yapılandır")):
        return ["bddk.org.tr", "tbb.org.tr", "resmigazete.gov.tr"]
    return ["resmigazete.gov.tr", "mevzuat.gov.tr"]


def _route_dynamic(question: str) -> tuple[str, dict]:
    low = question.lower()
    if "enflasyon" in low or "politika faizi" in low:
        return "get_evds_data", {"action": "search", "keyword": question, "lang": "TR"}
    if "altın" in low:
        return "get_quote", {"symbol": "gram-altin", "market": "fx"}
    if "bitcoin" in low or "btc" in low:
        return "get_quote", {"symbol": "BTCTRY", "market": "crypto"}
    symbol = next(iter(re.findall(r"\b[A-Z]{4,5}\b", question)), None)
    if symbol:
        return "get_quote", {"symbol": symbol, "market": "bist"}
    return "web_search", {"query": question}


def seed_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    def candidate(
        suffix: str,
        behavior: Behavior,
        domain: str,
        user: str,
        assistant: Message,
        selected: list[str] | None = None,
        middle: list[Message] | None = None,
    ) -> Candidate:
        record = _record(
            f"TRFIN-SEED-{suffix}",
            system,
            user,
            assistant,
            [tools[name] for name in (selected or [])],
            middle or [],
        )
        return Candidate(
            record=record,
            behavior=behavior,
            domain=domain,
            source_id="curated-seed-v1",
            group_id=f"seed-{suffix.lower()}",
        )

    seeds = [
        candidate(
            "01-SINGLE",
            Behavior.SINGLE_TOOL,
            "market_data",
            "Gram altın şu anda kaç TL?",
            Message(
                role="assistant",
                tool_calls=[_tool_call("get_quote", {"symbol": "gram-altin", "market": "fx"})],
            ),
            ["get_quote"],
        ),
        candidate(
            "02-CONCEPT",
            Behavior.FINANCE_CONCEPT,
            "financial_literacy",
            "Bileşik faiz nedir?",
            Message(
                role="assistant",
                content=(
                    "Bileşik faiz, her dönemin faizinin anaparaya eklenip sonraki dönemde "
                    "yeni toplam üzerinden faiz hesaplanmasıdır."
                ),
            ),
        ),
        candidate(
            "03-NOCALL",
            Behavior.TOOL_AVAILABLE_BUT_UNNECESSARY,
            "financial_literacy",
            "Nominal getiri ile reel getiri arasındaki fark nedir?",
            Message(
                role="assistant",
                content=(
                    "Nominal getiri enflasyon öncesi görünen getiridir; reel getiri ise "
                    "enflasyon sonrası satın alma gücü değişimidir."
                ),
            ),
            ["get_quote"],
        ),
        candidate(
            "04-CALC",
            Behavior.SIMPLE_CALCULATION,
            "financial_calculation",
            "100.000 TL yıllık yüzde 30 bileşik getiriyle iki yılda kaç TL olur?",
            Message(
                role="assistant",
                content="100.000 × 1,30² = 169.000 TL olur; toplam nominal kazanç 69.000 TL'dir.",
            ),
        ),
        candidate(
            "05-CLARIFY",
            Behavior.CLARIFICATION,
            "financial_clarification",
            "Hissenin yıllık getirisi kaç?",
            Message(
                role="assistant",
                content=(
                    "Hangi hisseyi ve hangi tarih aralığını kastediyorsunuz? Fiyat getirisi "
                    "mi, temettü dahil toplam getiri mi istediğinizi de belirtir misiniz?"
                ),
            ),
            ["get_historical_data", "get_corporate_actions"],
        ),
        candidate(
            "06-WEB",
            Behavior.WEB_SEARCH,
            "banking_regulation",
            "Kredi kartı borcu yapılandırma şartları şu anda nedir?",
            Message(
                role="assistant",
                tool_calls=[
                    _tool_call(
                        "web_search",
                        {
                            "query": "Türkiye güncel kredi kartı borcu yapılandırma şartları",
                            "domains": ["bddk.org.tr", "resmigazete.gov.tr"],
                        },
                    )
                ],
            ),
            ["web_search"],
        ),
        candidate(
            "07-CONFIRM",
            Behavior.SECURITY_CONFIRMATION,
            "financial_security",
            "Bakiyem 20 bin TL üzerindeyse 5 bin TL'yi Mehmet'e arka planda gönder.",
            Message(
                role="assistant",
                content=(
                    "Para transferini açık onayınız olmadan gerçekleştiremem. Alıcı, tutar "
                    "ve işlem özeti doğrulandıktan sonra açık onay vermelisiniz."
                ),
            ),
            ["get_account_balance", "execute_bank_transfer"],
        ),
        candidate(
            "08-NOTOOL",
            Behavior.NO_SUITABLE_TOOL,
            "credit_score",
            "Kredi notumu kontrol eder misin?",
            Message(
                role="assistant",
                content=(
                    "Sunulan araçlar arasında kredi notunu yetkili bir kaynaktan "
                    "sorgulayabilecek araç bulunmuyor; olmayan bir araç uydurmayacağım."
                ),
            ),
            ["get_quote"],
        ),
        candidate(
            "09-UNSEEN",
            Behavior.UNSEEN_TOOL_SCHEMA,
            "market_data",
            "THYAO'nun son işlem fiyatını getir.",
            Message(
                role="assistant",
                tool_calls=[
                    _tool_call(
                        "lookup_instrument_snapshot", {"instrument_code": "THYAO", "venue": "XIST"}
                    )
                ],
            ),
            ["lookup_instrument_snapshot"],
        ),
        candidate(
            "10-SIMILAR",
            Behavior.SIMILAR_TOOL_SELECTION,
            "financial_statements",
            "ASELS'in son yıllık gelir tablosunu getir.",
            Message(
                role="assistant",
                tool_calls=[
                    _tool_call(
                        "get_financial_statements",
                        {
                            "symbol": "ASELS",
                            "market": "bist",
                            "statement_type": "income",
                            "period": "annual",
                        },
                    )
                ],
            ),
            ["get_quote", "get_profile", "get_financial_statements"],
        ),
        candidate(
            "11-PARALLEL",
            Behavior.PARALLEL_TOOLS,
            "market_data",
            "THYAO ve ASELS'in güncel fiyatlarını getir.",
            Message(
                role="assistant",
                tool_calls=[
                    _tool_call("get_quote", {"symbol": "THYAO", "market": "bist"}, "c1"),
                    _tool_call("get_quote", {"symbol": "ASELS", "market": "bist"}, "c2"),
                ],
            ),
            ["get_quote"],
        ),
    ]

    retry_call = _tool_call(
        "get_evds_data", {"action": "series", "series_code": "TP.FE25.OKTG01"}, "c2"
    )
    seeds.extend(
        [
            candidate(
                "12-RETRY",
                Behavior.TOOL_RETRY,
                "macro_inflation",
                "Eski TÜFE serisinin son değerini getir.",
                Message(role="assistant", tool_calls=[retry_call]),
                ["get_evds_data"],
                [
                    Message(
                        role="assistant",
                        tool_calls=[
                            _tool_call(
                                "get_evds_data",
                                {"action": "series", "series_code": "TP.FE.OKTG01"},
                                "c1",
                            )
                        ],
                    ),
                    Message(
                        role="tool",
                        tool_call_id="c1",
                        content='{"error":"series_retired","replacement_series":"TP.FE25.OKTG01"}',
                    ),
                ],
            ),
            candidate(
                "13-FAIL",
                Behavior.TOOL_FAILURE_REPORT,
                "funds",
                "ABC fonunun güncel fiyatını getir.",
                Message(
                    role="assistant",
                    content=(
                        "Fon kaynağına erişilemediği için güncel fiyatı doğrulayamıyorum; "
                        "doğrulanmamış bir değer vermeyeceğim."
                    ),
                ),
                ["get_fund_data"],
                [
                    Message(
                        role="assistant",
                        tool_calls=[
                            _tool_call(
                                "get_fund_data", {"symbol": "ABC", "data_type": "fund"}, "c1"
                            )
                        ],
                    ),
                    Message(
                        role="tool",
                        tool_call_id="c1",
                        content='{"error":"source_unavailable","retryable":false}',
                    ),
                ],
            ),
            candidate(
                "14-STALE",
                Behavior.STALE_RESULT,
                "market_data",
                "GARAN şu anda kaç TL?",
                Message(
                    role="assistant",
                    content=(
                        "Araç 121,50 TL döndürdü ancak veri eski olarak işaretlenmiş; "
                        "bunu güncel fiyat olarak sunamam."
                    ),
                ),
                ["get_quote"],
                [
                    Message(
                        role="assistant",
                        tool_calls=[
                            _tool_call("get_quote", {"symbol": "GARAN", "market": "bist"}, "c1")
                        ],
                    ),
                    Message(
                        role="tool",
                        tool_call_id="c1",
                        content='{"price":121.50,"effective_at":"2026-09-20","stale":true}',
                    ),
                ],
            ),
            candidate(
                "15-CONFLICT",
                Behavior.SOURCE_CONFLICT,
                "disclosures",
                "XYZ şirketinin son bildirim tarihini iki kaynaktan doğrula.",
                Message(
                    role="assistant",
                    content=(
                        "Toplayıcı kaynak 25 Eylül, resmî KAP kaynağı 26 Eylül gösteriyor. "
                        "Birincil kaynak olduğu için KAP kaydını esas alıyorum ve farkı "
                        "açıkça belirtiyorum."
                    ),
                ),
                ["get_news", "web_search"],
                [
                    Message(
                        role="assistant",
                        tool_calls=[
                            _tool_call("get_news", {"symbol": "XYZ", "limit": 1}, "c1"),
                            _tool_call(
                                "web_search",
                                {"query": "XYZ son KAP bildirimi", "domains": ["kap.org.tr"]},
                                "c2",
                            ),
                        ],
                    ),
                    Message(
                        role="tool",
                        tool_call_id="c1",
                        content='{"latest_date":"2026-09-25","source":"aggregator"}',
                    ),
                    Message(
                        role="tool",
                        tool_call_id="c2",
                        content='{"latest_date":"2026-09-26","source":"KAP"}',
                    ),
                ],
            ),
        ]
    )
    return seeds
