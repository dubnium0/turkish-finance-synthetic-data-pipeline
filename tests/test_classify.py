import pytest

from tcg.classify import classify_instruction
from tcg.models import Behavior


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Bileşik faiz nedir?", Behavior.FINANCE_CONCEPT),
        ("100.000 TL yüzde 30 faizle iki yılda kaç TL olur?", Behavior.SIMPLE_CALCULATION),
        ("Kredi kartı yapılandırma şartları nelerdir?", Behavior.WEB_SEARCH),
        ("Gram altın şu an kaç TL?", Behavior.SINGLE_TOOL),
        ("Hisse ne kadar?", Behavior.CLARIFICATION),
        ("Bu faizle kredi çekip altın almak mantıklı mı?", Behavior.CLARIFICATION),
    ],
)
def test_instruction_routing(question, expected):
    assert classify_instruction(question).behavior == expected
