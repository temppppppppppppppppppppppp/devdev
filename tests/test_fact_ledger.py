"""Unit tests for FactLedger edge cases."""

from modules.core.fact_ledger import FactLedger, summarize_fact_ledger_numbers_block


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


def test_dead_character_updates_are_ignored_for_followup_state_changes():
    ledger = FactLedger(_EmptyStubDB())
    ledger.update_from_state_changes(1, {"npc_deaths": [{"name": "흑풍", "cause": "전투"}]})
    ledger.update_from_state_changes(
        2,
        {
            "npc_injuries": [{"name": "흑풍", "state": "중상"}],
            "npc_movements": [{"name": "흑풍", "to": "개봉"}],
            "npc_personality_changes": [{"name": "흑풍", "traits": "냉정"}],
            "npc_npc_relationships": [{"npc1": "흑풍", "npc2": "주인공", "relation": "협력"}],
        },
    )

    history = ledger.get_character("흑풍")["history"]
    assert history == ["ep1: 사망 (원인: 전투)"]


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


# ══════════════════════════════════════════════════════════════
# [P0-2] established_value 영구 보존 테스트
# ══════════════════════════════════════════════════════════════


class _EmptyStubDB:
    """빈 상태로 시작하는 StubDB (update_number 전용)."""

    def load_anchor(self, _name):
        return None

    def save_anchor(self, _name, _payload):
        return None

    def upsert_canonical_fact(self, **_kwargs):
        return None


class _BrokenSaveDB(_EmptyStubDB):
    def save_anchor(self, _name, _payload):
        raise RuntimeError("write fail")


def test_update_number_established_value_set():
    """[P0-2] 초기값이 established_value에 기록됨."""
    ledger = FactLedger(_EmptyStubDB())
    ledger.update_number("재산", 100, "냥", 1)
    assert ledger._ledger["numbers"]["재산"]["established_value"] == 100


def test_save_sets_degraded_contract_on_failure():
    ledger = FactLedger(_BrokenSaveDB())

    result = ledger.save()

    assert result is False
    assert ledger.last_save_ok is False
    assert ledger.last_save_error == "write fail"


def test_save_clears_degraded_contract_on_success():
    ledger = FactLedger(_EmptyStubDB())
    ledger.last_save_ok = False
    ledger.last_save_error = "stale error"

    result = ledger.save()

    assert result is True
    assert ledger.last_save_ok is True
    assert ledger.last_save_error is None


def test_update_number_established_value_not_overwritten():
    """[P0-2] 값 변경 시 established_value는 유지."""
    ledger = FactLedger(_EmptyStubDB())
    ledger.update_number("재산", 100, "냥", 1)
    ledger.update_number("재산", 500, "냥", 10)
    ledger.update_number("재산", 10000, "냥", 50)
    assert ledger._ledger["numbers"]["재산"]["established_value"] == 100
    assert ledger._ledger["numbers"]["재산"]["value"] == 10000


def test_established_value_survives_fifo_trim():
    """[P0-2] FIFO 트림 후에도 established_value 유지."""
    ledger = FactLedger(_EmptyStubDB())
    for ep in range(1, 112):
        ledger.update_number("내공", ep * 10, "단위", ep)
    entry = ledger._ledger["numbers"]["내공"]
    assert len(entry["history"]) == 100  # FIFO trim
    assert entry["established_value"] == 10  # ep1의 초기값 보존


def test_summarize_fact_ledger_numbers_block_reads_numbers_schema():
    ledger = {
        "numbers": {
            "자본금": {
                "value": "10억",
                "unit": "원",
                "established_value": "1억",
                "established_ep": 1,
                "last_ep": 12,
            }
        }
    }

    text = summarize_fact_ledger_numbers_block(ledger, max_items=5)

    assert "[팩트 원장 핵심 수치]" in text
    assert "자본금" in text
    assert "1억 원 (ep1) -> 10억 원 (ep12)" in text


def test_to_summary_includes_section_truncation_counters():
    ledger = FactLedger(_EmptyStubDB())
    ledger._ledger = {
        "characters": {
            **{f"생존{i}": {"status": "alive", "role": "역할", "established_ep": i} for i in range(35)},
            "사망A": {"status": "dead", "last_ep": 9, "history": ["사망: 결투 패배"]},
        },
        "items": {
            **{f"보유{i}": {"status": "보유", "owner": "주인공", "established_ep": i} for i in range(25)},
            **{f"분실{i}": {"status": "분실", "last_ep": i} for i in range(12)},
        },
        "locations": {f"장소{i}": {"status": "정상"} for i in range(12)},
        "organizations": {f"조직{i}": {"status": "활동중"} for i in range(11)},
        "numbers": {f"수치{i}": {"value": i, "last_ep": i} for i in range(18)},
        "last_updated_ep": 20,
    }

    summary = ledger.to_summary()

    assert "(총 35명 중 30명 표시)" in summary
    assert "(총 25개 중 20개 표시)" in summary
    assert "(총 12개 중 10개 표시)" in summary
    assert "(총 11개 중 10개 표시)" in summary
    assert "(총 18개 중 15개 표시)" in summary


def test_inventory_counts_update_item_quantity_and_summary():
    ledger = FactLedger(_EmptyStubDB())
    ledger.update_from_state_changes(
        ep_num=9,
        state_changes={
            "inventory_counts": {"트레이딩용 컴퓨터": 3},
            "inventory_count_deltas": [{"name": "트레이딩용 컴퓨터", "from": 2, "to": 3, "delta": 1}],
        },
    )

    entry = ledger._ledger["items"]["트레이딩용 컴퓨터"]
    assert entry["quantity"] == 3
    assert entry["status"] == "보유"
    summary = ledger.to_summary()
    assert "트레이딩용 컴퓨터 x3" in summary
