"""Curated multi-turn finance-agent training candidates."""
# ruff: noqa: E501

from __future__ import annotations

import json
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

_SOURCE_ID = "curated-agentic-v1"


def _call(name: str, arguments: dict[str, Any], call_id: str) -> ToolCall:
    return ToolCall(id=call_id, function=FunctionCall(name=name, arguments=arguments))


def _result(call_id: str, payload: dict[str, Any]) -> Message:
    return Message(
        role="tool",
        tool_call_id=call_id,
        content=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )


def _candidate(
    suffix: str,
    behavior: Behavior,
    domain: str,
    system: str,
    user: str,
    tools: Iterable[ToolDefinition],
    messages: Iterable[Message],
) -> Candidate:
    return Candidate(
        record=TrainingRecord(
            id=f"TRFIN-AGENTIC-{suffix}",
            messages=[
                Message(role="system", content=system),
                Message(role="user", content=user),
                *messages,
            ],
            tools=list(tools),
        ),
        behavior=behavior,
        domain=domain,
        source_id=_SOURCE_ID,
        group_id=f"agentic-{suffix.lower()}",
    )


def _side_effect_tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
) -> ToolDefinition:
    return ToolDefinition(
        function=FunctionDefinition(
            name=name,
            description=(
                f"{description} İşlem hesap durumunu değiştirir ve işleme özel açık onay "
                "belirteci gerektirir."
            ),
            parameters={
                "type": "object",
                "properties": {
                    **properties,
                    "confirmation_token": {
                        "type": "string",
                        "minLength": 8,
                        "description": "Doğrulanan işlem özeti için tek kullanımlık onay belirteci.",
                    },
                },
                "required": [*required, "confirmation_token"],
                "additionalProperties": False,
            },
        )
    )


def _clarification_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    specs = [
        (
            "CLARIFY-01",
            "equity_return",
            "Bu hissenin yıllık getirisi kaç?",
            "Hangi hisseyi ve hangi tarih aralığını kastediyorsunuz? Fiyat getirisi mi, temettü dahil toplam getiri mi istediğinizi de belirtir misiniz?",
            ["get_historical_data", "get_corporate_actions"],
        ),
        (
            "CLARIFY-02",
            "fund_comparison",
            "Yatırım fonlarını karşılaştırır mısın?",
            "Hangi fon kodlarını, hangi tarih aralığında ve getiri, risk ya da portföy dağılımından hangisine göre karşılaştırmamı istersiniz?",
            ["get_fund_data", "compare_assets"],
        ),
        (
            "CLARIFY-03",
            "real_return",
            "Enflasyona göre ne kadar kazandım?",
            "Başlangıç ve bitiş tarihlerini, başlangıç tutarını ve dönem sonu portföy değerini belirtir misiniz?",
            ["get_macro_data", "get_evds_data"],
        ),
        (
            "CLARIFY-04",
            "fixed_income_guidance",
            "Tahvil benim için mantıklı mı?",
            "Vade hedefinizi, likidite ihtiyacınızı, kabul edebileceğiniz faiz riskini ve değerlendirdiğiniz tahvilin kodunu belirtir misiniz?",
            ["get_bond_yields"],
        ),
        (
            "CLARIFY-05",
            "foreign_exchange_return",
            "Dolar ne kadar değişmiş?",
            "Hangi başlangıç ve bitiş tarihlerini, hangi dolar kurunu ve değişimi TL tutarı mı yoksa yüzde olarak mı istediğinizi belirtir misiniz?",
            ["get_historical_data", "get_evds_data"],
        ),
        (
            "CLARIFY-06",
            "dividends",
            "Temettüleri göster.",
            "Hangi şirket veya şirketler için ve hangi yıl ya da tarih aralığındaki temettüleri istediğinizi belirtir misiniz?",
            ["get_corporate_actions"],
        ),
        (
            "CLARIFY-07",
            "financial_statements",
            "Bilançosu nasıl?",
            "Hangi şirketi, yıllık mı çeyreklik mi dönemi ve borçluluk, likidite ya da kârlılık ölçütlerinden hangisini incelememi istersiniz?",
            ["get_financial_statements", "get_financial_ratios"],
        ),
        (
            "CLARIFY-08",
            "portfolio_rebalancing",
            "Portföyümü yeniden dengele.",
            "Mevcut varlıklarınızı ve ağırlıklarını, hedefinizi, yatırım ufkunuzu ve kabul edebileceğiniz risk düzeyini belirtir misiniz?",
            ["get_quote", "compare_assets"],
        ),
    ]
    return [
        _candidate(
            suffix,
            Behavior.CLARIFICATION,
            domain,
            system,
            user,
            [tools[name] for name in selected],
            [Message(role="assistant", content=answer)],
        )
        for suffix, domain, user, answer, selected in specs
    ]


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
            "limit_price": {"type": ["number", "null"], "exclusiveMinimum": 0},
        },
        ["symbol", "side", "quantity", "order_type"],
    )
    crypto = _side_effect_tool(
        "initiate_crypto_withdrawal",
        "Kripto varlığı harici cüzdana çeker.",
        {
            "asset": {"type": "string"},
            "amount": {"type": "number", "exclusiveMinimum": 0},
            "network": {"type": "string"},
            "address": {"type": "string", "minLength": 12},
        },
        ["asset", "amount", "network", "address"],
    )
    deposit = _side_effect_tool(
        "redeem_term_deposit",
        "Vadeli mevduatı vadesinden önce kapatır.",
        {
            "deposit_id": {"type": "string"},
            "redeem_all": {"type": "boolean"},
        },
        ["deposit_id", "redeem_all"],
    )
    card_limit = _side_effect_tool(
        "set_card_spending_limit",
        "Kredi kartı harcama limitini değiştirir.",
        {
            "card_id": {"type": "string"},
            "new_limit": {"type": "number", "exclusiveMinimum": 0},
            "currency": {"type": "string", "const": "TRY"},
        },
        ["card_id", "new_limit", "currency"],
    )
    credit = _side_effect_tool(
        "accept_credit_offer",
        "Bağlayıcı kredi teklifini kabul eder.",
        {"offer_id": {"type": "string"}},
        ["offer_id"],
    )
    beneficiary = _side_effect_tool(
        "register_transfer_beneficiary",
        "IBAN'ı kayıtlı alıcı listesine ekler.",
        {
            "label": {"type": "string", "minLength": 1},
            "iban": {"type": "string", "pattern": "^TR[0-9A-Z]{24}$"},
        },
        ["label", "iban"],
    )
    statement = _side_effect_tool(
        "dispatch_account_statement",
        "Hesap ekstresini belirtilen e-posta adresine gönderir.",
        {
            "account_id": {"type": "string"},
            "period": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$"},
            "recipient_email": {"type": "string", "format": "email"},
        },
        ["account_id", "period", "recipient_email"],
    )
    specs = [
        (
            "CONFIRM-01",
            "market_order",
            "Portföyümdeki 120 THYAO hissesinin tamamını piyasa emriyle sat.",
            "120 adet THYAO'nun piyasa emriyle satılmasını istiyorsunuz. Gerçekleşme fiyatı işlem anında değişebilir. Bu işlemi göndermemi açıkça onaylıyor musunuz?",
            order,
        ),
        (
            "CONFIRM-02",
            "bank_transfer",
            "TR120006200000000012345678 hesabına 35.000 TL gönder.",
            "TR120006200000000012345678 IBAN'ına 35.000 TL gönderilecek. Alıcıyı ve tutarı doğruladıysanız transferi göndermemi açıkça onaylıyor musunuz?",
            transfer,
        ),
        (
            "CONFIRM-03",
            "crypto_withdrawal",
            "0,25 ETH'yi 0x1234567890abcdef adresine Ethereum ağıyla çek.",
            "0,25 ETH, Ethereum ağı üzerinden 0x1234567890abcdef adresine çekilecek. Yanlış adres geri döndürülemez kayba yol açabilir. İşlemi açıkça onaylıyor musunuz?",
            crypto,
        ),
        (
            "CONFIRM-04",
            "term_deposit",
            "VD-4821 numaralı vadeli hesabımın tamamını bugün boz.",
            "VD-4821 numaralı vadeli mevduatın tamamı vadesinden önce kapatılacak ve faiz kaybı oluşabilir. İşlemi açıkça onaylıyor musunuz?",
            deposit,
        ),
        (
            "CONFIRM-05",
            "card_limit",
            "KART-27 limitimi 180.000 TL yap.",
            "KART-27 için harcama limiti 180.000 TL olarak değiştirilecek. Bu hesap değişikliğini açıkça onaylıyor musunuz?",
            card_limit,
        ),
        (
            "CONFIRM-06",
            "credit_offer",
            "KRD-908 teklifini kabul et.",
            "KRD-908 kredi teklifinin kabulü bağlayıcı bir borç doğurur. Teklif koşullarını ve toplam geri ödemeyi incelediyseniz kabul işlemini açıkça onaylıyor musunuz?",
            credit,
        ),
        (
            "CONFIRM-07",
            "beneficiary_management",
            "TR330006100519786457841326 IBAN'ını Kira Ev Sahibi adıyla kaydet.",
            "TR330006100519786457841326 IBAN'ı “Kira Ev Sahibi” adıyla kayıtlı alıcılara eklenecek. IBAN ve etiketi doğruladıysanız işlemi açıkça onaylıyor musunuz?",
            beneficiary,
        ),
        (
            "CONFIRM-08",
            "financial_privacy",
            "HESAP-4 hesabımın 2026-08 ekstresini mali@ornek.com adresine gönder.",
            "HESAP-4 hesabının 2026-08 ekstresi mali@ornek.com adresine gönderilecek. Bu finansal veri paylaşımını açıkça onaylıyor musunuz?",
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
            [tool],
            [Message(role="assistant", content=answer)],
        )
        for suffix, domain, user, answer, tool in specs
    ]


def _parallel_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    specs = [
        (
            "PARALLEL-01",
            "market_and_rates",
            "GARAN'ın güncel fiyatını ve Türkiye 10 yıllık tahvil getirisini birlikte getir.",
            (
                "get_quote",
                {"symbol": "GARAN", "market": "bist"},
                {"price": 128.4, "currency": "TRY", "effective_at": "2026-09-28T15:30:00+03:00"},
            ),
            (
                "get_bond_yields",
                {"country": "TR"},
                {"ten_year_percent": 29.8, "effective_at": "2026-09-28"},
            ),
            "28 Eylül 2026 verilerine göre GARAN 128,40 TL, Türkiye 10 yıllık tahvil getirisi yüzde 29,8.",
        ),
        (
            "PARALLEL-02",
            "disclosures",
            "ASELS'in son yıllık gelir tablosunu ve son KAP haberini getir.",
            (
                "get_financial_statements",
                {
                    "symbol": "ASELS",
                    "market": "bist",
                    "statement_type": "income",
                    "period": "annual",
                    "last_n": 1,
                },
                {"period": "2025", "revenue_try": 120000000000, "source": "financial_statements"},
            ),
            (
                "get_news",
                {"symbol": "ASELS", "limit": 1},
                {
                    "title": "Yeni iş ilişkisi",
                    "published_at": "2026-09-28T09:15:00+03:00",
                    "source": "KAP",
                },
            ),
            "Son yıllık gelir tablosunda 2025 geliri 120 milyar TL. Son KAP bildirimi 28 Eylül 2026 saat 09.15'te yayımlanan “Yeni iş ilişkisi”.",
        ),
        (
            "PARALLEL-03",
            "funds_and_inflation",
            "TI2 fonunun son fiyatını ve son açıklanan yıllık TÜFE'yi getir.",
            (
                "get_fund_data",
                {"symbol": "TI2", "data_type": "fund"},
                {"price": 3.8421, "currency": "TRY", "effective_at": "2026-09-27"},
            ),
            (
                "get_macro_data",
                {"data_type": "inflation", "region": "tr", "inflation_type": "tufe", "limit": 1},
                {"annual_percent": 31.2, "period": "2026-08"},
            ),
            "TI2'nin 27 Eylül 2026 tarihli pay fiyatı 3,8421 TL; 2026 Ağustos için son açıklanan yıllık TÜFE yüzde 31,2.",
        ),
        (
            "PARALLEL-04",
            "equity_and_dividends",
            "TUPRS'ın güncel fiyatını ve 2026 temettülerini göster.",
            (
                "get_quote",
                {"symbol": "TUPRS", "market": "bist"},
                {"price": 172.6, "currency": "TRY", "effective_at": "2026-09-28T15:25:00+03:00"},
            ),
            (
                "get_corporate_actions",
                {"symbol": "TUPRS", "market": "bist", "year": 2026},
                {"dividends": [{"payment_date": "2026-04-03", "gross_try_per_share": 7.4}]},
            ),
            "TUPRS 28 Eylül 2026 saat 15.25 itibarıyla 172,60 TL. Araç 2026 için hisse başına brüt 7,40 TL ve 3 Nisan ödeme tarihli temettü gösteriyor.",
        ),
        (
            "PARALLEL-05",
            "earnings_and_analysts",
            "AAPL'ın son kâr verisini ve analist tavsiyelerini getir.",
            (
                "get_earnings",
                {"symbol": "AAPL", "market": "us"},
                {"period": "2026-Q2", "eps_usd": 1.72, "reported_at": "2026-07-30"},
            ),
            (
                "get_analyst_data",
                {"symbol": "AAPL", "market": "us"},
                {"buy": 24, "hold": 9, "sell": 2, "effective_at": "2026-09-27"},
            ),
            "AAPL'ın 2026 ikinci çeyrek hisse başına kârı 1,72 USD. 27 Eylül 2026 analist dağılımı 24 al, 9 tut ve 2 sat.",
        ),
        (
            "PARALLEL-06",
            "macro_calendar",
            "Bu haftaki yüksek önem düzeyindeki Türkiye verilerini ve güncel gram altını getir.",
            (
                "get_economic_calendar",
                {"country": "TR", "importance": "high", "period": "this_week"},
                {"events": [{"name": "Politika faizi kararı", "at": "2026-10-01T14:00:00+03:00"}]},
            ),
            (
                "get_quote",
                {"symbol": "gram-altin", "market": "fx"},
                {"price": 5112.3, "currency": "TRY", "effective_at": "2026-09-28T15:32:00+03:00"},
            ),
            "Bu haftanın yüksek önem düzeyindeki Türkiye olayı 1 Ekim 2026 saat 14.00 politika faizi kararı. Gram altın 28 Eylül saat 15.32 itibarıyla 5.112,30 TL.",
        ),
        (
            "PARALLEL-07",
            "company_health",
            "THYAO'nun şirket profilini ve kapsamlı finansal oranlarını getir.",
            (
                "get_profile",
                {"symbol": "THYAO", "market": "bist"},
                {"sector": "Ulaştırma", "industry": "Havayolları", "effective_at": "2026-09-28"},
            ),
            (
                "get_financial_ratios",
                {"symbol": "THYAO", "market": "bist", "ratio_set": "comprehensive"},
                {"price_earnings": 4.8, "debt_to_equity": 1.35, "period": "2026-Q2"},
            ),
            "THYAO, ulaştırma sektöründe havayolu şirketi. 2026 ikinci çeyrek verileriyle F/K 4,8 ve borç/özkaynak 1,35.",
        ),
        (
            "PARALLEL-08",
            "cross_market",
            "Bitcoinin BtcTurk fiyatını ve ABD enflasyonunun son değerini getir.",
            (
                "get_quote",
                {"symbol": "BTCTRY", "market": "crypto", "exchange": "btcturk"},
                {"price": 2350000, "currency": "TRY", "effective_at": "2026-09-28T15:35:00+03:00"},
            ),
            (
                "get_macro_data",
                {"data_type": "inflation", "region": "us", "limit": 1},
                {"annual_percent": 2.7, "period": "2026-08"},
            ),
            "BtcTurk'te Bitcoin 28 Eylül 2026 saat 15.35 itibarıyla 2.350.000 TL. ABD yıllık enflasyonu 2026 Ağustos döneminde yüzde 2,7.",
        ),
    ]
    candidates = []
    for suffix, domain, user, first, second, answer in specs:
        first_name, first_args, first_result = first
        second_name, second_args, second_result = second
        candidates.append(
            _candidate(
                suffix,
                Behavior.PARALLEL_TOOLS,
                domain,
                system,
                user,
                [tools[first_name], tools[second_name]],
                [
                    Message(
                        role="assistant",
                        tool_calls=[
                            _call(first_name, first_args, "c1"),
                            _call(second_name, second_args, "c2"),
                        ],
                    ),
                    _result("c1", first_result),
                    _result("c2", second_result),
                    Message(role="assistant", content=answer),
                ],
            )
        )
    return candidates


def _retry_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    specs = [
        (
            "RETRY-01",
            "macro_inflation",
            "TCMB'nin eski TÜFE serisinin son değerini getir.",
            "get_evds_data",
            {"action": "series", "series_code": "TP.FE.OKTG01"},
            {"error": "series_retired", "retryable": True, "replacement_series": "TP.FE25.OKTG01"},
            {"action": "series", "series_code": "TP.FE25.OKTG01", "period": "1mo"},
            {"series_code": "TP.FE25.OKTG01", "value": 3321.45, "period": "2026-08"},
            "Eski seri kullanımdan kalktığı için aracın önerdiği TP.FE25.OKTG01 serisiyle yeniden sorguladım. 2026 Ağustos değeri 3.321,45.",
        ),
        (
            "RETRY-02",
            "instrument_resolution",
            "THYAA'nın güncel fiyatını getir.",
            "get_quote",
            {"symbol": "THYAA", "market": "bist"},
            {"error": "symbol_not_found", "retryable": True, "suggested_symbol": "THYAO"},
            {"symbol": "THYAO", "market": "bist"},
            {
                "symbol": "THYAO",
                "price": 318.5,
                "currency": "TRY",
                "effective_at": "2026-09-28T15:30:00+03:00",
            },
            "THYAA bulunamadı; aracın önerdiği THYAO ile yeniden sorguladım. THYAO 28 Eylül 2026 saat 15.30 itibarıyla 318,50 TL.",
        ),
        (
            "RETRY-03",
            "market_resolution",
            "GARAN'ın güncel fiyatını getir.",
            "get_quote",
            {"symbol": "GARAN", "market": "us"},
            {"error": "market_mismatch", "retryable": True, "suggested_market": "bist"},
            {"symbol": "GARAN", "market": "bist"},
            {
                "symbol": "GARAN",
                "price": 128.4,
                "currency": "TRY",
                "effective_at": "2026-09-28T15:30:00+03:00",
            },
            "GARAN ABD piyasasında bulunamadı; aracın önerdiği BIST piyasasıyla yeniden sorguladım. Fiyat 28 Eylül 2026 saat 15.30 itibarıyla 128,40 TL.",
        ),
        (
            "RETRY-04",
            "fund_resolution",
            "Tİİ fonunun son fiyatını getir.",
            "get_fund_data",
            {"symbol": "Tİİ", "data_type": "fund"},
            {"error": "invalid_fund_code", "retryable": True, "normalized_symbol": "TI2"},
            {"symbol": "TI2", "data_type": "fund"},
            {"symbol": "TI2", "price": 3.8421, "currency": "TRY", "effective_at": "2026-09-27"},
            "Türkçe karakterli kod geçersizdi; aracın normalleştirdiği TI2 koduyla yeniden sorguladım. 27 Eylül 2026 pay fiyatı 3,8421 TL.",
        ),
        (
            "RETRY-05",
            "disclosures",
            "KAP bildirim 1234567'nin tam metnini getir.",
            "get_news",
            {"news_id": "1234567", "page": 1},
            {
                "error": "canonical_url_required",
                "retryable": True,
                "canonical_url": "https://www.kap.org.tr/tr/Bildirim/1234567",
            },
            {"news_id": "https://www.kap.org.tr/tr/Bildirim/1234567", "page": 1},
            {
                "title": "Özel durum açıklaması",
                "published_at": "2026-09-27T18:10:00+03:00",
                "page": 1,
            },
            "Araç kanonik KAP adresini istedi; önerilen adresle yeniden sorguladım. Bildirim, 27 Eylül 2026 saat 18.10 tarihli “Özel durum açıklaması”.",
        ),
        (
            "RETRY-06",
            "market_history",
            "THYAO'nun 28 Eylül 2026 gün sonu verisini getir.",
            "get_historical_data",
            {
                "symbol": "THYAO",
                "market": "bist",
                "start_date": "2026-09-28",
                "end_date": "2026-09-28",
            },
            {
                "error": "session_not_closed",
                "retryable": True,
                "last_complete_session": "2026-09-25",
            },
            {
                "symbol": "THYAO",
                "market": "bist",
                "start_date": "2026-09-25",
                "end_date": "2026-09-25",
            },
            {"date": "2026-09-25", "close": 316.8, "currency": "TRY"},
            "28 Eylül seansı henüz kapanmadığı için aracın belirttiği son tamamlanmış seans olan 25 Eylül'ü sorguladım. Kapanış 316,80 TL.",
        ),
        (
            "RETRY-07",
            "crypto_market",
            "BtcTurk'te BTCTRY fiyatını getir.",
            "get_quote",
            {"symbol": "BTCTRY", "market": "crypto", "exchange": "coinbase"},
            {"error": "pair_not_supported", "retryable": True, "supported_exchange": "btcturk"},
            {"symbol": "BTCTRY", "market": "crypto", "exchange": "btcturk"},
            {"price": 2350000, "currency": "TRY", "effective_at": "2026-09-28T15:35:00+03:00"},
            "BTCTRY Coinbase'de desteklenmediği için aracın belirttiği BtcTurk ile yeniden sorguladım. Fiyat 28 Eylül 2026 saat 15.35 itibarıyla 2.350.000 TL.",
        ),
        (
            "RETRY-08",
            "financial_statements",
            "ASELS'in 2023 ikinci çeyrek gelir tablosunu getir.",
            "get_financial_statements",
            {
                "symbol": "ASELS",
                "market": "bist",
                "statement_type": "income",
                "period": "quarterly",
                "last_n": 4,
            },
            {"error": "period_out_of_window", "retryable": True, "minimum_last_n": 16},
            {
                "symbol": "ASELS",
                "market": "bist",
                "statement_type": "income",
                "period": "quarterly",
                "last_n": 16,
            },
            {"period": "2023-Q2", "revenue_try": 9140000000, "source": "financial_statements"},
            "İlk sorgunun dönem penceresi yetersizdi; aracın belirttiği 16 çeyreklik pencereyle yeniden sorguladım. ASELS'in 2023 ikinci çeyrek geliri 9,14 milyar TL.",
        ),
    ]
    candidates = []
    for suffix, domain, user, name, first_args, error, second_args, success, answer in specs:
        candidates.append(
            _candidate(
                suffix,
                Behavior.TOOL_RETRY,
                domain,
                system,
                user,
                [tools[name]],
                [
                    Message(role="assistant", tool_calls=[_call(name, first_args, "c1")]),
                    _result("c1", error),
                    Message(role="assistant", tool_calls=[_call(name, second_args, "c2")]),
                    _result("c2", success),
                    Message(role="assistant", content=answer),
                ],
            )
        )
    return candidates


def _failure_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    specs = [
        (
            "FAIL-01",
            "funds",
            "ABC fonunun güncel fiyatını getir.",
            "get_fund_data",
            {"symbol": "ABC", "data_type": "fund"},
            {"error": "source_unavailable", "retryable": False},
            "Fon kaynağına erişilemediği için ABC'nin güncel fiyatını doğrulayamıyorum; doğrulanmamış bir değer vermeyeceğim.",
        ),
        (
            "FAIL-02",
            "market_data",
            "GARAN'ın güncel fiyatını getir.",
            "get_quote",
            {"symbol": "GARAN", "market": "bist"},
            {"error": "market_feed_closed", "retryable": False},
            "Piyasa veri akışı kapalı olduğu için GARAN'ın güncel fiyatını doğrulayamıyorum.",
        ),
        (
            "FAIL-03",
            "macro_data",
            "Son politika faizi değerini getir.",
            "get_evds_data",
            {"action": "series", "series_code": "TP.APIFON4", "period": "1mo"},
            {"error": "authorization_required", "retryable": False},
            "EVDS veri erişimi yetkilendirme gerektirdiği için son politika faizi değerini doğrulayamıyorum.",
        ),
        (
            "FAIL-04",
            "financial_statements",
            "XYZ'nin son bilançosunu getir.",
            "get_financial_statements",
            {"symbol": "XYZ", "market": "bist", "statement_type": "balance", "period": "annual"},
            {"error": "issuer_not_found", "retryable": False},
            "XYZ koduyla bir ihraççı bulunamadığı için bilanço veremiyorum; şirket kodunu doğrulamak gerekir.",
        ),
        (
            "FAIL-05",
            "disclosures",
            "THYAO'nun son KAP bildirimini getir.",
            "get_news",
            {"symbol": "THYAO", "limit": 1},
            {"error": "upstream_timeout", "retryable": False, "attempts": 3},
            "KAP kaynağı üç denemeden sonra da yanıt vermedi; THYAO'nun son bildirimini doğrulayamıyorum.",
        ),
        (
            "FAIL-06",
            "bond_yields",
            "Güncel Türkiye tahvil getirilerini getir.",
            "get_bond_yields",
            {"country": "TR"},
            {"error": "publication_unavailable", "retryable": False},
            "Tahvil getirisi yayını kullanılamadığı için güncel oranları doğrulayamıyorum.",
        ),
        (
            "FAIL-07",
            "corporate_actions",
            "TUPRS'ın 2026 temettülerini getir.",
            "get_corporate_actions",
            {"symbol": "TUPRS", "market": "bist", "year": 2026},
            {"error": "data_license_block", "retryable": False},
            "Kurumsal işlem verisi lisans kısıtı nedeniyle alınamadı; 2026 temettülerini doğrulanmış veri olarak sunamam.",
        ),
        (
            "FAIL-08",
            "analyst_data",
            "AAPL için güncel analist tavsiyelerini getir.",
            "get_analyst_data",
            {"symbol": "AAPL", "market": "us"},
            {"error": "provider_service_ended", "retryable": False},
            "Analist veri sağlayıcısının hizmeti sona erdiği için AAPL için güncel tavsiye dağılımını doğrulayamıyorum.",
        ),
    ]
    return [
        _candidate(
            suffix,
            Behavior.TOOL_FAILURE_REPORT,
            domain,
            system,
            user,
            [tools[name]],
            [
                Message(role="assistant", tool_calls=[_call(name, arguments, "c1")]),
                _result("c1", error),
                Message(role="assistant", content=answer),
            ],
        )
        for suffix, domain, user, name, arguments, error, answer in specs
    ]


def _stale_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    specs = [
        (
            "STALE-01",
            "market_data",
            "GARAN şu anda kaç TL?",
            "get_quote",
            {"symbol": "GARAN", "market": "bist"},
            {"price": 121.5, "currency": "TRY", "effective_at": "2026-09-20", "stale": True},
            "Araç 121,50 TL döndürdü ancak veri 20 Eylül 2026 tarihli ve eski olarak işaretlenmiş; bunu güncel fiyat olarak sunamam.",
        ),
        (
            "STALE-02",
            "foreign_exchange",
            "Dolar kuru şu anda kaç TL?",
            "get_quote",
            {"symbol": "USD", "market": "fx"},
            {"price": 39.8, "currency": "TRY", "effective_at": "2026-08-31", "stale": True},
            "Araç 39,80 TL gösteriyor ancak sonuç 31 Ağustos 2026 tarihli ve güncelliğini yitirmiş; mevcut kur olarak kullanılamaz.",
        ),
        (
            "STALE-03",
            "funds",
            "TI2'nin güncel pay fiyatı nedir?",
            "get_fund_data",
            {"symbol": "TI2", "data_type": "fund"},
            {"price": 3.71, "currency": "TRY", "effective_at": "2026-09-10", "stale": True},
            "TI2 için 3,71 TL sonucu 10 Eylül 2026 tarihli ve eski; güncel pay fiyatı olarak sunamam.",
        ),
        (
            "STALE-04",
            "bond_yields",
            "Türkiye 10 yıllık tahvil getirisi şu an kaç?",
            "get_bond_yields",
            {"country": "TR"},
            {"ten_year_percent": 31.4, "effective_at": "2026-09-01", "stale": True},
            "Yüzde 31,4 değeri 1 Eylül 2026 tarihli ve araç tarafından eski işaretlenmiş; mevcut 10 yıllık getiri olarak doğrulanmış değil.",
        ),
        (
            "STALE-05",
            "analyst_data",
            "ASELS için güncel analist tavsiyesi nedir?",
            "get_analyst_data",
            {"symbol": "ASELS", "market": "bist"},
            {"buy": 8, "hold": 3, "sell": 1, "effective_at": "2025-12-31", "stale": True},
            "Analist dağılımı 31 Aralık 2025 tarihli ve güncel değil; bugünkü tavsiye görünümü olarak aktaramam.",
        ),
        (
            "STALE-06",
            "economic_calendar",
            "Bugünkü önemli Türkiye verileri neler?",
            "get_economic_calendar",
            {"country": "TR", "importance": "high", "period": "today"},
            {
                "events": [{"name": "TÜFE", "at": "2026-09-03T10:00:00+03:00"}],
                "generated_at": "2026-09-03",
                "stale": True,
            },
            "Takvim 3 Eylül 2026'da üretilmiş ve bugünü yansıtmıyor; listedeki TÜFE olayını bugünkü etkinlik olarak sunamam.",
        ),
        (
            "STALE-07",
            "company_profile",
            "THYAO'nun güncel sektör ve çalışan bilgisini getir.",
            "get_profile",
            {"symbol": "THYAO", "market": "bist"},
            {
                "sector": "Ulaştırma",
                "employees": 31000,
                "effective_at": "2024-12-31",
                "stale": True,
            },
            "Profilde sektör Ulaştırma ve çalışan sayısı 31.000 görünüyor; ancak çalışan verisi 31 Aralık 2024 tarihli olduğundan güncel sayı olarak kullanılamaz.",
        ),
        (
            "STALE-08",
            "crypto_market",
            "Bitcoin BtcTurk'te şu anda kaç TL?",
            "get_quote",
            {"symbol": "BTCTRY", "market": "crypto", "exchange": "btcturk"},
            {
                "price": 2280000,
                "currency": "TRY",
                "effective_at": "2026-09-27T09:00:00+03:00",
                "stale": True,
            },
            "2.280.000 TL sonucu 27 Eylül 2026 saat 09.00 tarihli ve eski işaretlenmiş; anlık BtcTurk fiyatı olarak sunamam.",
        ),
    ]
    return [
        _candidate(
            suffix,
            Behavior.STALE_RESULT,
            domain,
            system,
            user,
            [tools[name]],
            [
                Message(role="assistant", tool_calls=[_call(name, arguments, "c1")]),
                _result("c1", result),
                Message(role="assistant", content=answer),
            ],
        )
        for suffix, domain, user, name, arguments, result, answer in specs
    ]


def _conflict_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    specs = [
        (
            "CONFLICT-01",
            "dividends",
            "TUPRS'ın 2026 temettü tutarını şirket verisi ve KAP'tan doğrula.",
            (
                "get_corporate_actions",
                {"symbol": "TUPRS", "market": "bist", "year": 2026},
                {"gross_try_per_share": 7.2, "source": "aggregator"},
            ),
            (
                "get_news",
                {"symbol": "TUPRS", "limit": 5},
                {"gross_try_per_share": 7.4, "source": "KAP", "published_at": "2026-03-10"},
            ),
            "Toplayıcı hisse başına brüt 7,20 TL, resmî KAP bildirimi 7,40 TL gösteriyor. Birincil kaynak olduğu için KAP'taki 7,40 TL'yi esas alıyorum ve uyuşmazlığı koruyorum.",
        ),
        (
            "CONFLICT-02",
            "macro_inflation",
            "Ağustos yıllık TÜFE'yi iki kaynaktan doğrula.",
            (
                "get_macro_data",
                {"data_type": "inflation", "region": "tr", "inflation_type": "tufe", "limit": 1},
                {"annual_percent": 31.0, "period": "2026-08", "source": "cached_provider"},
            ),
            (
                "get_evds_data",
                {
                    "action": "series",
                    "series_code": "TP.FE25.OKTG01",
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-31",
                },
                {"annual_percent": 31.2, "period": "2026-08", "source": "TCMB_EVDS"},
            ),
            "Önbellekli sağlayıcı yüzde 31,0, TCMB EVDS yüzde 31,2 gösteriyor. Resmî EVDS kaynağını esas alıyorum; kaynaklar arasında 0,2 puan fark var.",
        ),
        (
            "CONFLICT-03",
            "funds",
            "TI2'nin son pay fiyatını araç ve resmî TEFAS kaynağından kontrol et.",
            (
                "get_fund_data",
                {"symbol": "TI2", "data_type": "fund"},
                {
                    "price": 3.8421,
                    "currency": "TRY",
                    "effective_at": "2026-09-27",
                    "source": "aggregator",
                },
            ),
            (
                "web_search",
                {"query": "TI2 27 Eylül 2026 pay fiyatı", "domains": ["tefas.gov.tr"]},
                {
                    "price": 3.846,
                    "currency": "TRY",
                    "effective_at": "2026-09-27",
                    "source": "TEFAS",
                },
            ),
            "Toplayıcı 3,8421 TL, resmî TEFAS sonucu 3,8460 TL gösteriyor. Birincil kaynak olduğu için TEFAS değerini esas alıyorum; farkın nedenini doğrulayamıyorum.",
        ),
        (
            "CONFLICT-04",
            "bond_yields",
            "Türkiye 10 yıllık tahvil getirisini iki kaynaktan doğrula.",
            (
                "get_bond_yields",
                {"country": "TR"},
                {
                    "ten_year_percent": 29.8,
                    "effective_at": "2026-09-28T15:00:00+03:00",
                    "source": "market_provider",
                },
            ),
            (
                "web_search",
                {
                    "query": "Türkiye 10 yıllık devlet tahvili gösterge getiri 28 Eylül 2026",
                    "domains": ["borsaistanbul.com"],
                },
                {
                    "ten_year_percent": 29.6,
                    "effective_at": "2026-09-28T15:00:00+03:00",
                    "source": "Borsa İstanbul",
                },
            ),
            "Piyasa sağlayıcısı yüzde 29,8, Borsa İstanbul yüzde 29,6 gösteriyor. Aynı zaman için kaynaklar çatışıyor; birincil kaynak olan Borsa İstanbul değerini esas alıyorum.",
        ),
        (
            "CONFLICT-05",
            "foreign_exchange",
            "TCMB referans dolar kuru ile piyasa dolar fiyatını karşılaştır.",
            (
                "get_quote",
                {"symbol": "USD", "market": "fx"},
                {
                    "price": 42.15,
                    "currency": "TRY",
                    "effective_at": "2026-09-28T15:30:00+03:00",
                    "source": "market",
                },
            ),
            (
                "get_evds_data",
                {"action": "series", "series_code": "TP.DK.USD.A.YTL", "period": "1mo"},
                {
                    "value": 42.02,
                    "currency": "TRY",
                    "effective_at": "2026-09-28",
                    "source": "TCMB_EVDS",
                },
            ),
            "Piyasa fiyatı 42,15 TL, TCMB referans kuru 42,02 TL. Bunlar farklı tanımlara sahip iki değer; referans kur sorusu için TCMB'yi esas alıyor, piyasa fiyatıyla eşitmiş gibi sunmuyorum.",
        ),
        (
            "CONFLICT-06",
            "financial_statements",
            "ASELS'in 2025 gelirini finansal tablo ve haberden doğrula.",
            (
                "get_financial_statements",
                {
                    "symbol": "ASELS",
                    "market": "bist",
                    "statement_type": "income",
                    "period": "annual",
                    "last_n": 1,
                },
                {"revenue_try": 120000000000, "period": "2025", "source": "audited_statement"},
            ),
            (
                "get_news",
                {"symbol": "ASELS", "limit": 10},
                {"revenue_try": 118500000000, "period": "2025", "source": "press_summary"},
            ),
            "Denetlenmiş finansal tablo 120 milyar TL, basın özeti 118,5 milyar TL gelir gösteriyor. Aynı dönem için çatışma var; denetlenmiş tabloyu esas alıyorum.",
        ),
        (
            "CONFLICT-07",
            "crypto_market",
            "Bitcoinin BtcTurk ve Coinbase fiyatlarını karşılaştır.",
            (
                "get_quote",
                {"symbol": "BTCTRY", "market": "crypto", "exchange": "btcturk"},
                {
                    "price": 2350000,
                    "currency": "TRY",
                    "effective_at": "2026-09-28T15:35:00+03:00",
                    "source": "BtcTurk",
                },
            ),
            (
                "get_quote",
                {"symbol": "BTC-USD", "market": "crypto", "exchange": "coinbase"},
                {
                    "price": 55800,
                    "currency": "USD",
                    "effective_at": "2026-09-28T15:35:00+03:00",
                    "source": "Coinbase",
                },
            ),
            "BtcTurk 2.350.000 TL, Coinbase 55.800 USD gösteriyor. Para birimleri ve işlem yerleri farklı olduğu için değerleri ortalamıyorum; doğrudan fiyat çatışması olarak yorumlamak için aynı kura çevirmek gerekir.",
        ),
        (
            "CONFLICT-08",
            "earnings",
            "AAPL'ın son EPS değerini sonuç ve şirket açıklamasından doğrula.",
            (
                "get_earnings",
                {"symbol": "AAPL", "market": "us"},
                {"eps_usd": 1.7, "period": "2026-Q2", "source": "aggregator"},
            ),
            (
                "web_search",
                {"query": "Apple 2026 Q2 diluted EPS official results", "domains": ["apple.com"]},
                {"eps_usd": 1.72, "period": "2026-Q2", "source": "Apple investor relations"},
            ),
            "Toplayıcı 1,70 USD, Apple'ın resmî açıklaması 1,72 USD seyreltilmiş EPS gösteriyor. Birincil şirket açıklamasındaki 1,72 USD'yi esas alıyorum.",
        ),
    ]
    candidates = []
    for suffix, domain, user, first, second, answer in specs:
        first_name, first_args, first_result = first
        second_name, second_args, second_result = second
        selected = [tools[first_name]]
        if second_name != first_name:
            selected.append(tools[second_name])
        candidates.append(
            _candidate(
                suffix,
                Behavior.SOURCE_CONFLICT,
                domain,
                system,
                user,
                selected,
                [
                    Message(
                        role="assistant",
                        tool_calls=[
                            _call(first_name, first_args, "c1"),
                            _call(second_name, second_args, "c2"),
                        ],
                    ),
                    _result("c1", first_result),
                    _result("c2", second_result),
                    Message(role="assistant", content=answer),
                ],
            )
        )
    return candidates


def agentic_candidates(system: str, tools: dict[str, ToolDefinition]) -> list[Candidate]:
    """Return reviewed-style multi-turn cases for seven underrepresented behaviors."""

    return [
        *_clarification_candidates(system, tools),
        *_security_candidates(system),
        *_parallel_candidates(system, tools),
        *_retry_candidates(system, tools),
        *_failure_candidates(system, tools),
        *_stale_candidates(system, tools),
        *_conflict_candidates(system, tools),
    ]
