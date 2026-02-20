"""Unit tests for FactLedger edge cases."""

from modules.core.fact_ledger import FactLedger


class _StubDB:
    def load_anchor(self, _name):
        return {
            "characters": {
                "정상생존": {"status": "alive"},
                "정상사망": {"status": "dead"},
                "깨진데이터": "not-a-dict",
            },
            "items": {},
            "locations": {},
            "organizations": {},
            "numbers": {},
            "last_updated_ep": 12,
        }

    def save_anchor(self, _name, _payload):
        return None


def test_get_stats_handles_non_dict_character_entries():
    ledger = FactLedger(_StubDB())

    stats = ledger.get_stats()

    assert stats["characters"] == 3
    assert stats["alive"] == 1
    assert stats["dead"] == 1


def test_get_dead_characters_handles_non_dict_entries():
    ledger = FactLedger(_StubDB())

    dead = ledger.get_dead_characters()

    assert dead == ["정상사망"]


def test_get_alive_characters_handles_non_dict_entries():
    ledger = FactLedger(_StubDB())

    alive = ledger.get_alive_characters()

    assert alive == ["정상생존"]


# ══════════════════════════════════════════════════════════════
# [TF-C07] 수치 팩트 자동 추출 테스트
# ══════════════════════════════════════════════════════════════


def test_extract_numerical_facts_from_state_changes():
    """[TF-C07] status_shadow + financial_events에서 수치 팩트 자동 추출"""
    ledger = FactLedger(_StubDB())
    state_changes = {
        "status_shadow": {
            "internal_energy_loss": 30,
            "internal_energy_remaining": 70,
        },
        "financial_events": [
            {"asset": "삼성전자", "price": 85000, "currency": "원"},
        ],
        "power_level": 45,
    }
    ledger.update_from_state_changes(ep_num=15, state_changes=state_changes)

    nums = ledger._ledger["numbers"]
    assert nums["내공_소모량"]["value"] == 30
    assert nums["내공_잔여"]["value"] == 70
    assert nums["삼성전자_price"]["value"] == 85000
    assert nums["삼성전자_price"]["unit"] == "원"
    assert nums["주인공_전투력"]["value"] == 45


def test_extract_numerical_facts_empty_safe():
    """[TF-C07] 빈 state_changes에서도 안전"""
    ledger = FactLedger(_StubDB())
    ledger.update_from_state_changes(ep_num=1, state_changes={})
    assert ledger._ledger["numbers"] == {}
    ledger.update_from_state_changes(ep_num=2, state_changes=None)
    assert ledger._ledger["numbers"] == {}
