"""Curated high-risk safety and schema-transfer training candidates."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import (
    Behavior,
    Candidate,
    FunctionCall,
    FunctionDefinition,
    Message,
    ToolCall,
    ToolDefinition,
    TrainingRecord,
)

_SOURCE_ID = "curated-hard-v1"


def _tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
) -> ToolDefinition:
    return ToolDefinition(
        function=FunctionDefinition(
            name=name,
            description=description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        )
    )


def _side_effect_tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
) -> ToolDefinition:
    return _tool(
        name,
        f"{description} İşlem geri döndürülemez; işleme özel açık onay belirteci gerekir.",
        {
            **properties,
            "confirmation_token": {
                "type": "string",
                "minLength": 8,
                "description": (
                    "Kullanıcının bu işlem özeti için verdiği tek kullanımlık onay belirteci."
                ),
            },
        },
        [*required, "confirmation_token"],
    )


def _call(name: str, arguments: dict[str, Any]) -> ToolCall:
    return ToolCall(function=FunctionCall(name=name, arguments=arguments))


def _candidate(
    suffix: str,
    behavior: Behavior,
    domain: str,
    system: str,
    user: str,
    assistant: Message,
    tools: Iterable[ToolDefinition],
) -> Candidate:
    return Candidate(
        record=TrainingRecord(
            id=f"TRFIN-HARD-{suffix}",
            messages=[
                Message(role="system", content=system),
                Message(role="user", content=user),
                assistant,
            ],
            tools=list(tools),
        ),
        behavior=behavior,
        domain=domain,
        source_id=_SOURCE_ID,
        group_id=f"hard-{suffix.lower()}",
    )


def _security_candidates(system: str) -> list[Candidate]:
    transfer = _side_effect_tool(
        "submit_wire_transfer",
        "Belirtilen alıcıya banka transferi gönderir.",
        {
            "recipient_iban": {"type": "string", "pattern": "^TR[0-9A-Z]{24}$"},
            "amount": {"type": "number", "exclusiveMinimum": 0},
            "currency": {"type": "string", "enum": ["TRY", "USD", "EUR"]},
        },
        ["recipient_iban", "amount", "currency"],
    )
    order = _side_effect_tool(
        "place_equity_order",
        "Borsaya gerçek hisse emri iletir.",
        {
            "symbol": {"type": "string", "minLength": 2},
            "side": {"type": "string", "enum": ["buy", "sell"]},
            "quantity": {"type": "integer", "minimum": 1},
            "order_type": {"type": "string", "enum": ["market", "limit"]},
        },
        ["symbol", "side", "quantity", "order_type"],
    )
    crypto = _side_effect_tool(
        "initiate_crypto_withdrawal",
        "Kripto varlığı harici cüzdana çeker.",
        {
            "asset": {"type": "string", "minLength": 2},
            "amount": {"type": "number", "exclusiveMinimum": 0},
            "network": {"type": "string", "minLength": 2},
            "address": {"type": "string", "minLength": 12},
        },
        ["asset", "amount", "network", "address"],
    )
    deposit = _side_effect_tool(
        "redeem_term_deposit",
        "Vadeli mevduatı vadesinden önce kapatır.",
        {"deposit_id": {"type": "string"}, "redeem_all": {"type": "boolean"}},
        ["deposit_id", "redeem_all"],
    )
    card_limit = _side_effect_tool(
        "set_card_spending_limit",
        "Kredi kartı harcama limitini değiştirir.",
        {
            "card_id": {"type": "string"},
            "new_limit": {"type": "number", "exclusiveMinimum": 0},
            "currency": {"type": "string", "enum": ["TRY"]},
        },
        ["card_id", "new_limit", "currency"],
    )
    loan = _side_effect_tool(
        "accept_credit_offer",
        "Bağlayıcı kredi teklifini kabul eder.",
        {"offer_id": {"type": "string"}},
        ["offer_id"],
    )
    beneficiary = _side_effect_tool(
        "register_transfer_beneficiary",
        "IBAN'ı kayıtlı ve güvenilir alıcı listesine ekler.",
        {
            "label": {"type": "string", "minLength": 1},
            "iban": {"type": "string", "pattern": "^TR[0-9A-Z]{24}$"},
        },
        ["label", "iban"],
    )
    statement = _side_effect_tool(
        "dispatch_account_statement",
        "Hesap ekstresini üçüncü taraf e-posta adresine gönderir.",
        {
            "account_id": {"type": "string"},
            "period": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$"},
            "recipient_email": {"type": "string", "format": "email"},
        },
        ["account_id", "period", "recipient_email"],
    )

    specs = [
        (
            "SEC-01",
            "bank_transfer",
            (
                "Bakiyem 100.000 TL'yi geçtiği anda fazlasını bu IBAN'a otomatik gönder; "
                "bir daha sorma."
            ),
            (
                "Gelecekte oluşacak tutar için peşinen onay kabul edemem. Her transferde "
                "alıcı, kesin tutar ve para birimi gösterildikten sonra işleme özel açık "
                "onay gerekir."
            ),
            transfer,
        ),
        (
            "SEC-02",
            "market_order",
            ("THYAO yüzde 5 düşünce benim adıma otomatik 1.000 lot al; bunu sürekli yetki say."),
            (
                "Sürekli yetkiyle piyasa emri veremem. Koşul gerçekleştiğinde fiyat, miktar, "
                "emir türü ve tahmini toplam tutar yeniden gösterilip açık onayınız alınmalıdır."
            ),
            order,
        ),
        (
            "SEC-03",
            "crypto_withdrawal",
            ("Hesabıma kripto gelir gelmez tamamını mesajdaki cüzdana çek; ağ önemli değil."),
            (
                "Kripto çekimini otomatik yapamam. Varlık, kesin miktar, ağ ve adres birlikte "
                "doğrulanmalı; yanlış ağ geri döndürülemez kayba yol açabileceği için ayrıca "
                "açık onay vermelisiniz."
            ),
            crypto,
        ),
        (
            "SEC-04",
            "term_deposit",
            "Vadeli hesabı gerektiğinde bozarsın, faiz kaybını sormana gerek yok.",
            (
                "Vadeli hesabı genel bir izinle bozamam. Kesilecek getiri, kapanacak mevduat "
                "ve hesaba geçecek net tutar gösterildikten sonra bu işleme özel açık onay "
                "gerekir."
            ),
            deposit,
        ),
        (
            "SEC-05",
            "card_limit",
            "Kart limitimi banka ne kadar izin veriyorsa arka planda en yükseğe çıkar.",
            (
                "Belirsiz ve kalıcı bir limit artışını arka planda yapamam. Kart, yeni kesin "
                "limit ve etkileri gösterildikten sonra işleme özel açık onay vermelisiniz."
            ),
            card_limit,
        ),
        (
            "SEC-06",
            "credit_offer",
            "Bana uygun bir kredi teklifi çıkarsa otomatik kabul et, sözleşmeyi sonra okurum.",
            (
                "Kredi teklifini önceden verilmiş genel izinle kabul edemem. Tutar, vade, faiz, "
                "toplam geri ödeme ve ücretler gösterildikten sonra bağlayıcı kabul için açık "
                "onay gerekir."
            ),
            loan,
        ),
        (
            "SEC-07",
            "beneficiary_management",
            "Mesajlarımda geçen bütün IBAN'ları otomatik olarak güvenilir alıcı listeme ekle.",
            (
                "Mesajlardan alıcı çıkarıp otomatik kaydedemem. Her alıcı adı ve IBAN ayrı "
                "ayrı doğrulanmalı ve kayıt işlemi için açık onay verilmelidir."
            ),
            beneficiary,
        ),
        (
            "SEC-08",
            "financial_privacy",
            (
                "Her ay bütün hesap ekstrelerimi muhasebecime otomatik e-postala; adresi "
                "rehberden bul."
            ),
            (
                "Finansal ekstreleri belirsiz bir alıcıya otomatik gönderemem. Hesap, dönem ve "
                "açık e-posta adresi doğrulanmalı; kişisel veri paylaşımı için işleme özel "
                "onay vermelisiniz."
            ),
            statement,
        ),
    ]
    return [
        _candidate(
            suffix,
            Behavior.SECURITY_CONFIRMATION,
            domain,
            system,
            user,
            Message(role="assistant", content=response),
            [tool],
        )
        for suffix, domain, user, response, tool in specs
    ]


def _unseen_candidates(system: str, known_tools: dict[str, ToolDefinition]) -> list[Candidate]:
    unseen_specs = [
        (
            "UNSEEN-01",
            "instrument_resolution",
            "Türk Hava Yolları adını XIST sembolüne çöz.",
            _tool(
                "resolve_asset_handle",
                "Serbest metin varlık adını belirtilen borsanın tanımlayıcısına çözer.",
                {
                    "query_text": {"type": "string", "minLength": 2},
                    "venue_code": {"type": "string", "enum": ["XIST", "XNAS", "XNYS"]},
                    "output_namespace": {"type": "string", "enum": ["ticker", "isin"]},
                },
                ["query_text", "venue_code", "output_namespace"],
            ),
            {"query_text": "Türk Hava Yolları", "venue_code": "XIST", "output_namespace": "ticker"},
            ["search_symbol", "get_quote"],
        ),
        (
            "UNSEEN-02",
            "fixed_income",
            "TRT240728T15 tahvilinin gelecek kupon tarihlerini getir.",
            _tool(
                "read_coupon_ledger",
                "Bir borçlanma aracının kupon ödeme takvimini ISIN üzerinden getirir.",
                {
                    "security_isin": {"type": "string", "pattern": "^[A-Z]{2}[A-Z0-9]{10}$"},
                    "after_date": {"type": "string", "format": "date"},
                    "max_entries": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                ["security_isin", "after_date", "max_entries"],
            ),
            {"security_isin": "TRT240728T15", "after_date": "2026-09-28", "max_entries": 8},
            ["get_bond_yields", "get_quote"],
        ),
        (
            "UNSEEN-03",
            "funds",
            "AFA fonunun 28 Eylül 2026 tarihindeki varlık sınıfı dağılımını getir.",
            _tool(
                "inspect_fund_allocation_slice",
                "TEFAS fon portföyünü belirli gün ve gruplama ekseninde döndürür.",
                {
                    "fund_code": {"type": "string", "pattern": "^[A-Z]{3}$"},
                    "as_of_date": {"type": "string", "format": "date"},
                    "group_by": {"type": "string", "enum": ["asset_class", "currency", "issuer"]},
                },
                ["fund_code", "as_of_date", "group_by"],
            ),
            {"fund_code": "AFA", "as_of_date": "2026-09-28", "group_by": "asset_class"},
            ["get_fund_data", "get_profile"],
        ),
        (
            "UNSEEN-04",
            "market_session",
            "28 Eylül 2026 saat 15.30'da Borsa İstanbul hangi işlem evresindeydi?",
            _tool(
                "read_exchange_phase",
                "Verilen zaman damgasında borsanın işlem evresini ve açık/kapalı durumunu getirir.",
                {
                    "venue": {"type": "string", "enum": ["XIST", "XNAS", "XNYS"]},
                    "at_time": {"type": "string", "format": "date-time"},
                },
                ["venue", "at_time"],
            ),
            {"venue": "XIST", "at_time": "2026-09-28T15:30:00+03:00"},
            ["get_quote", "get_historical_data"],
        ),
        (
            "UNSEEN-05",
            "deposit_rates",
            "250.000 TL için 32 günlük banka mevduat tekliflerini karşılaştır.",
            _tool(
                "collect_deposit_rate_cards",
                "Tutar, para birimi ve vadeye göre güncel banka mevduat tekliflerini getirir.",
                {
                    "principal": {"type": "number", "exclusiveMinimum": 0},
                    "currency_code": {"type": "string", "enum": ["TRY", "USD", "EUR"]},
                    "maturity_days": {"type": "integer", "minimum": 1, "maximum": 366},
                },
                ["principal", "currency_code", "maturity_days"],
            ),
            {"principal": 250000, "currency_code": "TRY", "maturity_days": 32},
            ["compare_assets", "get_bond_yields"],
        ),
        (
            "UNSEEN-06",
            "disclosures",
            "ASELS'in 2026 başından beri yayımladığı finansal rapor paketlerini bul.",
            _tool(
                "locate_disclosure_packets",
                (
                    "İhraççı, belge sınıfı ve başlangıç tarihine göre resmî bildirim "
                    "paketlerini bulur."
                ),
                {
                    "issuer_code": {"type": "string", "minLength": 2},
                    "document_classes": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["financial_report", "material_event", "governance"],
                        },
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "published_since": {"type": "string", "format": "date"},
                },
                ["issuer_code", "document_classes", "published_since"],
            ),
            {
                "issuer_code": "ASELS",
                "document_classes": ["financial_report"],
                "published_since": "2026-01-01",
            },
            ["get_news", "get_financial_statements"],
        ),
        (
            "UNSEEN-07",
            "fixed_income_risk",
            "TRT240728T15 için yüzde 32,5 getiriyle modifiye duration ve konveksiteyi hesapla.",
            _tool(
                "estimate_bond_risk_metrics",
                (
                    "Tahvili ISIN ve getiri oranıyla fiyatlayıp seçilen faiz riski "
                    "ölçülerini hesaplar."
                ),
                {
                    "security_isin": {"type": "string", "pattern": "^[A-Z]{2}[A-Z0-9]{10}$"},
                    "settlement_date": {"type": "string", "format": "date"},
                    "yield_percent": {"type": "number", "minimum": -10, "maximum": 200},
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["modified_duration", "convexity", "dv01"],
                        },
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                },
                ["security_isin", "settlement_date", "yield_percent", "metrics"],
            ),
            {
                "security_isin": "TRT240728T15",
                "settlement_date": "2026-09-28",
                "yield_percent": 32.5,
                "metrics": ["modified_duration", "convexity"],
            },
            ["get_bond_yields", "get_financial_ratios"],
        ),
        (
            "UNSEEN-08",
            "tax_lots",
            "PORTFOY-7 hesabındaki THYAO vergi lotlarını 2026 sonuna kadar FIFO ile özetle.",
            _tool(
                "summarize_tax_lot_inventory",
                (
                    "Portföydeki alış lotlarını seçilen maliyet yöntemine göre tarihsel "
                    "olarak özetler."
                ),
                {
                    "portfolio_ref": {"type": "string", "minLength": 3},
                    "instrument": {"type": "string", "minLength": 2},
                    "cost_method": {"type": "string", "enum": ["FIFO", "LIFO", "AVERAGE"]},
                    "through_date": {"type": "string", "format": "date"},
                },
                ["portfolio_ref", "instrument", "cost_method", "through_date"],
            ),
            {
                "portfolio_ref": "PORTFOY-7",
                "instrument": "THYAO",
                "cost_method": "FIFO",
                "through_date": "2026-12-31",
            },
            ["get_historical_data", "get_financial_statements"],
        ),
    ]

    candidates: list[Candidate] = []
    for suffix, domain, user, unseen_tool, arguments, distractor_names in unseen_specs:
        offered = [unseen_tool, *(known_tools[name] for name in distractor_names)]
        candidates.append(
            _candidate(
                suffix,
                Behavior.UNSEEN_TOOL_SCHEMA,
                domain,
                system,
                user,
                Message(role="assistant", tool_calls=[_call(unseen_tool.function.name, arguments)]),
                offered,
            )
        )
    return candidates


def hard_case_candidates(system: str, known_tools: dict[str, ToolDefinition]) -> list[Candidate]:
    """Return deterministic, reviewable cases humans commonly under-specify."""

    return [*_security_candidates(system), *_unseen_candidates(system, known_tools)]
