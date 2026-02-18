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
