"""Deterministic Turkish financial-calculation training candidates."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .models import Behavior, Candidate, Message, TrainingRecord

_SOURCE_ID = "curated-calculation-v1"


def _tr_number(value: Decimal, digits: int = 2) -> str:
    quantum = Decimal(1).scaleb(-digits)
    raw = f"{value.quantize(quantum, rounding=ROUND_HALF_UP):,.{digits}f}"
    return raw.replace(",", "_").replace(".", ",").replace("_", ".")


def _candidate(
    index: int,
    domain: str,
    system: str,
    user: str,
    response: str,
) -> Candidate:
    suffix = f"{index:02d}"
    return Candidate(
        record=TrainingRecord(
            id=f"TRFIN-CALC-{suffix}",
            messages=[
                Message(role="system", content=system),
                Message(role="user", content=user),
                Message(role="assistant", content=response),
            ],
            tools=[],
        ),
        behavior=Behavior.SIMPLE_CALCULATION,
        domain=domain,
        source_id=_SOURCE_ID,
        group_id=f"calculation-{suffix}",
    )


def calculation_candidates(system: str) -> list[Candidate]:
    """Return arithmetic-only cases whose required inputs are entirely in the prompt."""

    simple_interest = Decimal("80000") * Decimal("0.24") * Decimal("0.5")
    annual_compound = Decimal("100000") * Decimal("1.30") ** 2
    monthly_compound = Decimal("50000") * Decimal("1.02") ** 12
    real_return = Decimal("1.40") / Decimal("1.25") - 1
    inflated_cost = Decimal("1200") * Decimal("1.15")
    portfolio_return = Decimal("0.60") * Decimal("0.20") + Decimal("0.40") * Decimal("-0.05")
    average_cost = (Decimal(100) * Decimal(50) + Decimal(50) * Decimal(70)) / Decimal(150)
    recovery_return = Decimal(1) / Decimal("0.90") - 1
    converted_try = Decimal("1250") * Decimal("32.40")
    net_investment = Decimal("10000") * Decimal("0.99")
    units = net_investment / Decimal("45")
    monthly_rate = Decimal("0.03")
    months = 12
    loan_payment = (
        Decimal("100000")
        * monthly_rate
        * (Decimal(1) + monthly_rate) ** months
        / ((Decimal(1) + monthly_rate) ** months - Decimal(1))
    )
    gross_interest = Decimal("200000") * Decimal("0.36") * Decimal(90) / Decimal(365)
    withholding = gross_interest * Decimal("0.05")
    net_interest = gross_interest - withholding
    cagr = Decimal("0.20")
    portfolio_total = Decimal("80000") + Decimal("20000")
    target_equity = portfolio_total * Decimal("0.60")
    equity_sale = Decimal("80000") - target_equity
    dividend_yield = Decimal("4.50") / Decimal("90")
    profit_margin = (Decimal("2400000") - Decimal("1800000")) / Decimal("2400000")
    break_even_units = Decimal("300000") / (Decimal("120") - Decimal("70"))
    gross_margin = (Decimal("750000") - Decimal("450000")) / Decimal("750000")
    current_ratio = Decimal("900000") / Decimal("600000")
    debt_to_equity = Decimal("1200000") / Decimal("800000")
    return_on_equity = Decimal("240000") / Decimal("1600000")
    earnings_per_share = (Decimal("5000000") - Decimal("500000")) / Decimal("3000000")
    price_earnings = Decimal("45") / Decimal("3")
    net_present_value = (
        Decimal("60000") / Decimal("1.10")
        + Decimal("60000") / Decimal("1.10") ** 2
        - Decimal("100000")
    )
    annuity_future_value = Decimal("5000") * (Decimal("1.01") ** 12 - Decimal(1)) / Decimal("0.01")
    present_value = Decimal("100000") / Decimal("1.25")
    bond_current_yield = Decimal("8000") / Decimal("95000")
    inventory_turnover = Decimal("1200000") / Decimal("300000")
    receivables_days = Decimal("250000") / Decimal("1500000") * Decimal(365)
    working_capital = Decimal("900000") - Decimal("620000")
    operating_leverage = Decimal("400000") / Decimal("250000")
    effective_tax_rate = Decimal("180000") / Decimal("900000")
    effective_annual_rate = Decimal("1.025") ** 12 - Decimal(1)
    nominal_monthly_rate = Decimal("0.36") / Decimal(12)
    thirty_day_interest = Decimal("100000") * Decimal("0.45") * Decimal(30) / Decimal(365)
    quarterly_future_value = Decimal("200000") * Decimal("1.10") ** 8
    loan_total_interest = Decimal("12000") * Decimal(12) - Decimal("100000")
    simple_credit_cost = Decimal("120000") / Decimal("100000") - Decimal(1)
    rule_of_72_years = Decimal(72) / Decimal(24)
    term_gross_interest = Decimal("300000") * Decimal("0.42") * Decimal(180) / Decimal(365)
    term_net_interest = term_gross_interest * (Decimal(1) - Decimal("0.075"))
    rate_scenario_low = Decimal("100000") * Decimal("1.02") ** 12
    rate_scenario_high = Decimal("100000") * Decimal("1.025") ** 12
    rate_scenario_difference = rate_scenario_high - rate_scenario_low
    annual_future_value = Decimal("250000") * Decimal("1.18") ** 3
    fx_round_trip_loss = Decimal("1000") * (Decimal("33") - Decimal("32"))
    fx_round_trip_rate = fx_round_trip_loss / (Decimal("1000") * Decimal("33"))
    eur_usd_cross = Decimal("35.20") / Decimal("32")
    export_receivable_try = Decimal("50000") * Decimal("37")
    forward_advantage = Decimal("100000") * (Decimal("34.50") - Decimal("32"))
    fx_nominal_return = Decimal("33") / Decimal("30") - Decimal(1)
    fx_real_return = (Decimal(1) + fx_nominal_return) / Decimal("1.08") - Decimal(1)
    mixed_portfolio_return = Decimal("0.40") * Decimal("0.15") + Decimal("0.60") * Decimal("0.05")
    exchange_gross_try = Decimal("2500") * Decimal("35")
    exchange_fee = exchange_gross_try * Decimal("0.002")
    exchange_net_try = exchange_gross_try - exchange_fee
    monthly_lump_future_value = Decimal("75000") * Decimal("1.015") ** 18
    target_monthly_saving = (
        Decimal("500000") * Decimal("0.01") / (Decimal("1.01") ** 24 - Decimal(1))
    )
    perpetuity_value = Decimal("60000") / Decimal("0.12")
    growing_perpetuity_value = Decimal("20000") / (Decimal("0.15") - Decimal("0.05"))
    project_npv = (
        Decimal("40000") / Decimal("1.12")
        + Decimal("50000") / Decimal("1.12") ** 2
        + Decimal("60000") / Decimal("1.12") ** 3
        - Decimal("120000")
    )
    payback_months = Decimal("120000") / Decimal("15000")
    kmh_kurus_interest = (
        Decimal("50000") / Decimal("1000") * (Decimal("1.14") / Decimal("100")) * Decimal(45)
    )
    kmh_tl_interest = Decimal("50000") / Decimal("1000") * Decimal("1.14") * Decimal(45)
    kmh_daily_rate_interest = Decimal("50000") * Decimal("0.0016") * Decimal(45)
    kmh_variable_balance_interest = Decimal("1.14") * (
        Decimal("20000") / Decimal("1000") * Decimal(10)
        + Decimal("50000") / Decimal("1000") * Decimal(20)
        + Decimal("10000") / Decimal("1000") * Decimal(15)
    )
    kmh_early_payment_interest = Decimal("75000") / Decimal("1000") * Decimal("1.25") * Decimal(12)
    kmh_used_balance_interest = Decimal("30000") / Decimal("1000") * Decimal("1.10") * Decimal(20)

    specs = [
        (
            "simple_interest",
            "80.000 TL, yıllık yüzde 24 basit faizle 6 ayda ne kadar faiz getirir?",
            (
                f"Basit faiz = 80.000 × %24 × 6/12 = {_tr_number(simple_interest)} TL. "
                f"Dönem sonu toplamı {_tr_number(Decimal('80000') + simple_interest)} TL olur."
            ),
        ),
        (
            "compound_interest",
            "100.000 TL yıllık yüzde 30 bileşik getiriyle iki yılda kaç TL olur?",
            (
                f"100.000 × 1,30² = {_tr_number(annual_compound)} TL. "
                f"Toplam nominal kazanç {_tr_number(annual_compound - Decimal('100000'))} TL'dir."
            ),
        ),
        (
            "compound_interest",
            "50.000 TL her ay yüzde 2 bileşik getiri sağlarsa 12 ay sonunda kaç TL olur?",
            (
                f"50.000 × 1,02¹² = {_tr_number(monthly_compound)} TL. "
                f"Nominal kazanç {_tr_number(monthly_compound - Decimal('50000'))} TL'dir."
            ),
        ),
        (
            "real_return",
            "Yatırımım yüzde 40 arttı, aynı dönemde enflasyon yüzde 25 oldu. Reel getiri kaç?",
            (
                f"Reel getiri = (1,40 / 1,25) - 1 = %{_tr_number(real_return * 100)}. "
                "Basitçe 40 - 25 yapmak yerine bileşik reel getiri formülü kullanılır."
            ),
        ),
        (
            "inflation",
            "Bugün 1.200 TL olan sepet yüzde 15 enflasyon sonrası kaç TL olur?",
            f"1.200 × 1,15 = {_tr_number(inflated_cost)} TL olur; artış 180,00 TL'dir.",
        ),
        (
            "portfolio_return",
            "Portföyün yüzde 60'ı yüzde 20 yükseldi, yüzde 40'ı yüzde 5 düştü. Toplam getiri kaç?",
            (
                "%60 × %20 + %40 × -%5 = %12 - %2 = "
                f"%{_tr_number(portfolio_return * 100)} portföy getirisi."
            ),
        ),
        (
            "average_cost",
            "50 TL'den 100, sonra 70 TL'den 50 hisse aldım. Ortalama maliyetim kaç TL?",
            (
                "Toplam maliyet = 100 × 50 + 50 × 70 = 8.500 TL. "
                f"8.500 / 150 = {_tr_number(average_cost)} TL/hisse."
            ),
        ),
        (
            "loss_recovery",
            (
                "Yüzde 10 değer kaybeden yatırımın eski seviyesine dönmesi için yüzde kaç "
                "yükselmesi gerekir?"
            ),
            (
                "Kalan değer başlangıcın %90'ıdır. Gerekli artış = 1 / 0,90 - 1 = "
                f"%{_tr_number(recovery_return * 100)}."
            ),
        ),
        (
            "currency_conversion",
            "Kurun 32,40 TL olduğu varsayımıyla 1.250 USD kaç TL eder?",
            f"1.250 × 32,40 = {_tr_number(converted_try)} TL eder.",
        ),
        (
            "fees",
            (
                "10.000 TL'nin yüzde 1'i işlem ücreti kesilirse, kalanla 45 TL'den kaç fon "
                "payı alınır?"
            ),
            (
                f"Net yatırım = 10.000 × 0,99 = {_tr_number(net_investment)} TL. "
                f"{_tr_number(net_investment)} / 45 = {_tr_number(units)} fon payı alınır."
            ),
        ),
        (
            "loan_payment",
            "100.000 TL kredi, aylık yüzde 3 faiz ve 12 eşit taksitle aylık kaç TL olur?",
            (
                "Eşit taksit formülü P×r×(1+r)ⁿ/((1+r)ⁿ-1) ile aylık ödeme "
                f"{_tr_number(loan_payment)} TL olur. Vergi ve ek ücretler hariçtir."
            ),
        ),
        (
            "deposit_interest",
            (
                "200.000 TL yüzde 36 yıllık basit faizle 90 gün dursun. Stopaj yüzde 5 ise "
                "net faiz kaç TL?"
            ),
            (
                f"Brüt faiz = 200.000 × %36 × 90/365 = {_tr_number(gross_interest)} TL. "
                f"Stopaj {_tr_number(withholding)} TL; net faiz {_tr_number(net_interest)} TL'dir."
            ),
        ),
        (
            "cagr",
            "100.000 TL üç yılda 172.800 TL oldu. Yıllık bileşik büyüme oranı kaç?",
            (f"Yıllık bileşik büyüme = (172.800 / 100.000)^(1/3) - 1 = %{_tr_number(cagr * 100)}."),
        ),
        (
            "portfolio_rebalancing",
            (
                "80.000 TL hisse ve 20.000 TL nakit olan portföyü yüzde 60 hisseye çekmek "
                "için ne yapmalıyım?"
            ),
            (
                f"Toplam portföy {_tr_number(portfolio_total)} TL; hedef hisse tutarı "
                f"{_tr_number(target_equity)} TL. Fiyat değişimi ve masraf yok varsayımıyla "
                f"{_tr_number(equity_sale)} TL hisse satıp nakde geçirmek gerekir."
            ),
        ),
        (
            "dividend_yield",
            "Hisse başına yıllık temettü 4,50 TL, fiyat 90 TL ise temettü verimi kaç?",
            f"Temettü verimi = 4,50 / 90 = %{_tr_number(dividend_yield * 100)}.",
        ),
        (
            "profit_margin",
            "Gelir 2,4 milyon TL, gider 1,8 milyon TL ise kâr marjı kaçtır?",
            (
                "Kâr = 2,4 - 1,8 = 0,6 milyon TL. Kâr marjı = 0,6 / 2,4 = "
                f"%{_tr_number(profit_margin * 100)}."
            ),
        ),
        (
            "break_even",
            (
                "Sabit gider 300.000 TL, birim satış fiyatı 120 TL ve birim değişken maliyet "
                "70 TL ise başabaş satış miktarı kaçtır?"
            ),
            (
                "Birim katkı payı = 120 - 70 = 50 TL. Başabaş miktarı = 300.000 / 50 = "
                f"{_tr_number(break_even_units)} birimdir."
            ),
        ),
        (
            "gross_margin",
            "Satışlar 750.000 TL, satışların maliyeti 450.000 TL ise brüt kâr marjı kaçtır?",
            (
                "Brüt kâr = 750.000 - 450.000 = 300.000 TL. Brüt kâr marjı = "
                f"300.000 / 750.000 = %{_tr_number(gross_margin * 100)}."
            ),
        ),
        (
            "current_ratio",
            "Dönen varlıklar 900.000 TL ve kısa vadeli borçlar 600.000 TL ise cari oran kaçtır?",
            (
                "Cari oran = dönen varlıklar / kısa vadeli borçlar = 900.000 / 600.000 = "
                f"{_tr_number(current_ratio)}."
            ),
        ),
        (
            "debt_to_equity",
            "Toplam borç 1,2 milyon TL, özkaynak 800.000 TL ise borç/özkaynak oranı kaçtır?",
            (
                "Borç/özkaynak = 1.200.000 / 800.000 = "
                f"{_tr_number(debt_to_equity)}; yani %{_tr_number(debt_to_equity * 100)}."
            ),
        ),
        (
            "return_on_equity",
            "Net kâr 240.000 TL, ortalama özkaynak 1,6 milyon TL ise ROE kaçtır?",
            (
                "ROE = net kâr / ortalama özkaynak = 240.000 / 1.600.000 = "
                f"%{_tr_number(return_on_equity * 100)}."
            ),
        ),
        (
            "earnings_per_share",
            (
                "Net kâr 5 milyon TL, imtiyazlı temettü 500.000 TL ve 3 milyon adi hisse "
                "varsa hisse başına kâr kaç TL'dir?"
            ),
            (
                "Hisse başına kâr = (5.000.000 - 500.000) / 3.000.000 = "
                f"{_tr_number(earnings_per_share)} TL."
            ),
        ),
        (
            "price_earnings",
            "Hisse fiyatı 45 TL ve hisse başına kâr 3 TL ise F/K oranı kaçtır?",
            f"F/K = fiyat / hisse başına kâr = 45 / 3 = {_tr_number(price_earnings)}.",
        ),
        (
            "net_present_value",
            (
                "100.000 TL başlangıç yatırımı iki yıl boyunca yıl sonunda 60.000 TL nakit "
                "üretecek. İskonto oranı yüzde 10 ise NBD kaç TL'dir?"
            ),
            (
                "NBD = 60.000/1,10 + 60.000/1,10² - 100.000 = "
                f"{_tr_number(net_present_value)} TL'dir."
            ),
        ),
        (
            "annuity_future_value",
            (
                "Her ay sonunda 5.000 TL yatırıp aylık yüzde 1 getiri elde edersem 12 ay "
                "sonunda birikim kaç TL olur?"
            ),
            (
                "Dönem sonu ödemeli anüite gelecekteki değeri = 5.000 × "
                f"((1,01¹²-1)/0,01) = {_tr_number(annuity_future_value)} TL."
            ),
        ),
        (
            "present_value",
            (
                "Bir yıl sonraki 100.000 TL'nin yıllık yüzde 25 iskonto oranıyla bugünkü "
                "değeri kaçtır?"
            ),
            (f"Bugünkü değer = 100.000 / 1,25 = {_tr_number(present_value)} TL'dir."),
        ),
        (
            "bond_current_yield",
            "Yıllık kuponu 8.000 TL, piyasa fiyatı 95.000 TL olan tahvilin cari getirisi kaçtır?",
            (
                "Cari getiri = yıllık kupon / piyasa fiyatı = 8.000 / 95.000 = "
                f"%{_tr_number(bond_current_yield * 100)}."
            ),
        ),
        (
            "inventory_turnover",
            (
                "Satışların maliyeti 1,2 milyon TL ve ortalama stok 300.000 TL ise stok "
                "devir hızı kaçtır?"
            ),
            (f"Stok devir hızı = 1.200.000 / 300.000 = {_tr_number(inventory_turnover)} kezdir."),
        ),
        (
            "receivables_days",
            (
                "Ortalama ticari alacak 250.000 TL, yıllık kredili satış 1,5 milyon TL ise "
                "ortalama tahsil süresi kaç gündür?"
            ),
            (f"Tahsil süresi = 250.000 / 1.500.000 × 365 = {_tr_number(receivables_days)} gündür."),
        ),
        (
            "working_capital",
            (
                "Dönen varlıklar 900.000 TL, kısa vadeli borçlar 620.000 TL ise net işletme "
                "sermayesi kaçtır?"
            ),
            (f"Net işletme sermayesi = 900.000 - 620.000 = {_tr_number(working_capital)} TL'dir."),
        ),
        (
            "operating_leverage",
            "Katkı payı 400.000 TL ve FVÖK 250.000 TL ise faaliyet kaldıraç derecesi kaçtır?",
            (
                "Faaliyet kaldıraç derecesi = katkı payı / FVÖK = 400.000 / 250.000 = "
                f"{_tr_number(operating_leverage)}."
            ),
        ),
        (
            "effective_tax_rate",
            (
                "Vergi öncesi kâr 900.000 TL ve vergi gideri 180.000 TL ise efektif vergi "
                "oranı kaçtır?"
            ),
            (f"Efektif vergi oranı = 180.000 / 900.000 = %{_tr_number(effective_tax_rate * 100)}."),
        ),
        (
            "effective_annual_interest",
            "Aylık yüzde 2,5 bileşik faizin efektif yıllık oranı kaçtır?",
            (f"Efektif yıllık oran = 1,025¹² - 1 = %{_tr_number(effective_annual_rate * 100)}."),
        ),
        (
            "nominal_monthly_interest",
            "Yıllık nominal faiz yüzde 36 ve aylık dönemlere bölünüyorsa aylık oran kaçtır?",
            (f"Aylık nominal oran = %36 / 12 = %{_tr_number(nominal_monthly_rate * 100)}."),
        ),
        (
            "daily_simple_interest",
            (
                "100.000 TL, yıllık yüzde 45 basit faizle 30 gün tutulursa brüt faiz kaç "
                "TL olur? Yılı 365 gün kabul et."
            ),
            (f"Brüt faiz = 100.000 × %45 × 30/365 = {_tr_number(thirty_day_interest)} TL'dir."),
        ),
        (
            "quarterly_compound_interest",
            ("200.000 TL, üç ayda bir yüzde 10 bileşik getiriyle iki yıl sonunda kaç TL olur?"),
            (
                "İki yılda 8 dönem vardır. Gelecek değer = 200.000 × 1,10⁸ = "
                f"{_tr_number(quarterly_future_value)} TL'dir."
            ),
        ),
        (
            "loan_total_cost",
            (
                "100.000 TL kredi için 12 ay boyunca ayda 12.000 TL ödersem toplam faiz ve "
                "maliyet farkı kaç TL olur?"
            ),
            (
                "Toplam ödeme = 12.000 × 12 = 144.000 TL. Anapara üzerindeki toplam fark "
                f"{_tr_number(loan_total_interest)} TL'dir."
            ),
        ),
        (
            "simple_credit_cost",
            (
                "100.000 TL alıp bir yıl sonra toplam 120.000 TL ödüyorsam basit yıllık "
                "maliyet kaçtır?"
            ),
            (
                "Basit maliyet oranı = 120.000 / 100.000 - 1 = "
                f"%{_tr_number(simple_credit_cost * 100)}."
            ),
        ),
        (
            "rule_of_72",
            "Yıllık yüzde 24 getiriyle para yaklaşık kaç yılda ikiye katlanır?",
            (
                "72 kuralına göre yaklaşık süre = 72 / 24 = "
                f"{_tr_number(rule_of_72_years)} yıldır. Bu yaklaşık bir kestirimdir."
            ),
        ),
        (
            "net_term_interest",
            (
                "300.000 TL yıllık yüzde 42 basit faizle 180 gün tutulursa ve faizden yüzde "
                "7,5 kesinti yapılırsa net faiz kaç TL olur?"
            ),
            (
                f"Brüt faiz = {_tr_number(term_gross_interest)} TL. %7,5 kesinti sonrası "
                f"net faiz = {_tr_number(term_net_interest)} TL'dir."
            ),
        ),
        (
            "interest_rate_scenario",
            (
                "100.000 TL'nin 12 ay boyunca aylık yüzde 2 yerine yüzde 2,5 bileşik getiri "
                "sağlaması dönem sonu tutarını ne kadar değiştirir?"
            ),
            (
                f"%2 senaryosu {_tr_number(rate_scenario_low)} TL, %2,5 senaryosu "
                f"{_tr_number(rate_scenario_high)} TL olur. Fark "
                f"{_tr_number(rate_scenario_difference)} TL'dir."
            ),
        ),
        (
            "annual_future_value",
            "250.000 TL yıllık yüzde 18 bileşik getiriyle üç yıl sonra kaç TL olur?",
            (f"Gelecek değer = 250.000 × 1,18³ = {_tr_number(annual_future_value)} TL'dir."),
        ),
        (
            "fx_spread",
            (
                "Bankanın dolar alış kuru 32 TL, satış kuru 33 TL. 1.000 USD alıp hemen "
                "geri satarsam kur değişmeden kaç TL kaybederim?"
            ),
            (
                f"Alış maliyeti 33.000 TL, geri satış geliri 32.000 TL; kayıp "
                f"{_tr_number(fx_round_trip_loss)} TL'dir. Maliyete göre oran "
                f"%{_tr_number(fx_round_trip_rate * 100)}."
            ),
        ),
        (
            "cross_exchange_rate",
            "EUR/TL 35,20 ve USD/TL 32,00 ise EUR/USD çapraz kuru kaçtır?",
            (f"EUR/USD = 35,20 / 32,00 = {_tr_number(eur_usd_cross, 4)} USD/EUR."),
        ),
        (
            "export_receivable",
            (
                "Üç ay sonra alınacak 50.000 EUR için beklenen kur 37 TL ise tahmini TL "
                "karşılığı kaçtır?"
            ),
            (f"Tahmini karşılık = 50.000 × 37 = {_tr_number(export_receivable_try)} TL'dir."),
        ),
        (
            "forward_hedge",
            (
                "100.000 USD alacağımı 34,50 TL forward kuruyla sabitledim. Vade spot kuru "
                "32 TL olursa hedge işlemi kaç TL fazla gelir sağlar?"
            ),
            (
                "Forward avantajı = 100.000 × (34,50 - 32,00) = "
                f"{_tr_number(forward_advantage)} TL'dir."
            ),
        ),
        (
            "foreign_exchange_return",
            "Doları 30 TL'den alıp 33 TL'den satarsam nominal getiri oranım kaçtır?",
            (f"Nominal getiri = 33 / 30 - 1 = %{_tr_number(fx_nominal_return * 100)}."),
        ),
        (
            "real_foreign_exchange_return",
            (
                "Döviz yatırımım yüzde 10 yükseldi, aynı dönemde enflasyon yüzde 8 oldu. "
                "Reel getiri kaçtır?"
            ),
            (f"Reel getiri = 1,10 / 1,08 - 1 = %{_tr_number(fx_real_return * 100)}."),
        ),
        (
            "foreign_exchange_exposure",
            (
                "Portföyün yüzde 40'ı dövizde ve yüzde 15 yükseldi; kalan yüzde 60'ı TL "
                "varlıklarda ve yüzde 5 yükseldi. Toplam getiri kaçtır?"
            ),
            (f"%40 × %15 + %60 × %5 = %6 + %3 = %{_tr_number(mixed_portfolio_return * 100)}."),
        ),
        (
            "exchange_fee",
            (
                "2.500 EUR'yu 35 TL kurdan bozduruyorum. İşlem tutarından yüzde 0,2 masraf "
                "kesilirse net kaç TL alırım?"
            ),
            (
                f"Brüt tutar {_tr_number(exchange_gross_try)} TL, masraf "
                f"{_tr_number(exchange_fee)} TL, net tutar {_tr_number(exchange_net_try)} TL'dir."
            ),
        ),
        (
            "monthly_lump_future_value",
            ("75.000 TL aylık yüzde 1,5 bileşik getiriyle 18 ay sonra kaç TL olur?"),
            (f"Gelecek değer = 75.000 × 1,015¹⁸ = {_tr_number(monthly_lump_future_value)} TL'dir."),
        ),
        (
            "sinking_fund_payment",
            (
                "Aylık yüzde 1 getiriyle 24 ay sonunda 500.000 TL biriktirmek için her ay "
                "sonunda kaç TL yatırmalıyım?"
            ),
            (
                "Aylık ödeme = 500.000 × 0,01 / (1,01²⁴ - 1) = "
                f"{_tr_number(target_monthly_saving)} TL'dir."
            ),
        ),
        (
            "perpetuity_value",
            (
                "Her yıl 60.000 TL ödeyen sabit bir nakit akışının iskonto oranı yüzde 12 "
                "ise değeri kaçtır?"
            ),
            (
                "Sonsuz sabit nakit akışı değeri = 60.000 / 0,12 = "
                f"{_tr_number(perpetuity_value)} TL'dir."
            ),
        ),
        (
            "growing_perpetuity_value",
            (
                "Gelecek yıl 20.000 TL ödeme yapacak, yılda yüzde 5 büyüyecek sürekli nakit "
                "akışının iskonto oranı yüzde 15 ise değeri kaçtır?"
            ),
            (
                "Büyüyen sonsuz nakit akışı değeri = 20.000 / (0,15 - 0,05) = "
                f"{_tr_number(growing_perpetuity_value)} TL'dir."
            ),
        ),
        (
            "discounted_cash_flow",
            (
                "120.000 TL yatırım; üç yıl sonunda sırasıyla 40.000, 50.000 ve 60.000 TL "
                "nakit üretecek. İskonto oranı yüzde 12 ise NBD kaçtır?"
            ),
            (
                "NBD = 40.000/1,12 + 50.000/1,12² + 60.000/1,12³ - 120.000 = "
                f"{_tr_number(project_npv)} TL'dir."
            ),
        ),
        (
            "payback_period",
            (
                "120.000 TL başlangıç yatırımı her ay 15.000 TL net nakit üretiyorsa basit "
                "geri ödeme süresi kaç aydır?"
            ),
            (f"Basit geri ödeme süresi = 120.000 / 15.000 = {_tr_number(payback_months)} aydır."),
        ),
        (
            "kmh_interest_per_thousand_kurus",
            (
                "KMH günlük faizi her 1.000 TL için 1,14 kuruş. 50.000 TL'yi 45 gün "
                "kullanırsam BSMV ve diğer vergiler hariç faiz kaç TL olur?"
            ),
            (
                "1,14 kuruş = 0,0114 TL'dir. Faiz = 50.000/1.000 × 0,0114 × 45 = "
                f"{_tr_number(kmh_kurus_interest)} TL'dir."
            ),
        ),
        (
            "kmh_interest_per_thousand_tl",
            (
                "KMH günlük faizi her 1.000 TL için 1,14 TL. 50.000 TL'yi 45 gün "
                "kullanırsam vergiler hariç faiz kaç TL olur?"
            ),
            (f"Faiz = 50.000/1.000 × 1,14 × 45 = {_tr_number(kmh_tl_interest)} TL'dir."),
        ),
        (
            "kmh_daily_percentage",
            (
                "KMH günlük basit faiz oranı yüzde 0,16. 50.000 TL'yi 45 gün kullanırsam "
                "vergiler hariç faiz kaç TL olur?"
            ),
            (f"Faiz = 50.000 × %0,16 × 45 = {_tr_number(kmh_daily_rate_interest)} TL'dir."),
        ),
        (
            "kmh_variable_balance",
            (
                "KMH faizi her 1.000 TL için günlük 1,14 TL. Bakiyeyi 20.000 TL ile 10 gün, "
                "50.000 TL ile 20 gün ve 10.000 TL ile 15 gün kullandım. Vergiler hariç "
                "toplam faiz kaç TL?"
            ),
            (
                "Faiz = 1,14 × (20 × 10 + 50 × 20 + 10 × 15) = "
                f"{_tr_number(kmh_variable_balance_interest)} TL'dir."
            ),
        ),
        (
            "kmh_early_repayment",
            (
                "KMH günlük faizi her 1.000 TL için 1,25 TL. 75.000 TL çekip 12 gün sonra "
                "kapatırsam vergiler hariç faiz kaç TL olur?"
            ),
            (f"Faiz = 75.000/1.000 × 1,25 × 12 = {_tr_number(kmh_early_payment_interest)} TL'dir."),
        ),
        (
            "kmh_used_balance_only",
            (
                "KMH limitim 100.000 TL ama yalnızca 30.000 TL kullandım. Her 1.000 TL için "
                "günlük faiz 1,10 TL ve kullanım 20 günse vergiler hariç faiz kaç TL olur?"
            ),
            (
                "Faiz limite değil kullanılan 30.000 TL'ye uygulanır: "
                f"30.000/1.000 × 1,10 × 20 = {_tr_number(kmh_used_balance_interest)} TL."
            ),
        ),
    ]
    return [
        _candidate(index, domain, system, user, response)
        for index, (domain, user, response) in enumerate(specs, start=1)
    ]
