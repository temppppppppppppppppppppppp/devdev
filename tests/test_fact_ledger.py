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


def test_same_batch_death_blocks_followup_character_phase_updates():
    ledger = FactLedger(_EmptyStubDB())

    ledger.update_from_state_changes(
        3,
        {
            "npc_deaths": [{"name": "흑풍", "cause": "독살"}],
            "npc_injuries": [{"name": "흑풍", "state": "중상"}],
            "npc_movements": [{"name": "흑풍", "to": "남문"}],
            "npc_personality_changes": [{"name": "흑풍", "traits": "냉정"}],
            "npc_npc_relationships": [{"npc1": "흑풍", "npc2": "주인공", "relation": "협력"}],
        },
    )

    assert ledger.get_character("흑풍")["history"] == ["ep3: 사망 (원인: 독살)"]
    assert ledger.get_character("주인공") is None


def test_update_from_state_changes_applies_all_phase_families():
    ledger = FactLedger(_EmptyStubDB())

    ledger.update_from_state_changes(
        7,
        {
            "relationship_changes": [{"target": "연화", "from": "경계", "to": "동맹"}],
            "skill_acquisitions": [{"name": "천뢰검", "source": "비급"}],
            "major_items": [{"name": "흑룡패", "action": "획득"}],
            "inventory_counts": {"치유단": 2},
            "inventory_count_deltas": [{"name": "치유단", "from": 2, "to": 0}],
            "entity_destructions": [
                {"name": "혈맹", "type": "organization", "cause": "내분"},
                {"name": "북문", "type": "location", "cause": "화재"},
            ],
            "npc_injuries": [{"npc": "연화", "state": "경상"}],
            "npc_movements": [{"npc": "연화", "destination": "남문"}],
            "npc_personality_changes": [{"npc": "연화", "traits": "침착", "role": "조력자"}],
            "npc_npc_relationships": [{"npc1": "연화", "npc2": "백운", "relation": "동료"}],
        },
    )

    assert ledger.last_updated_ep == 7
    assert ledger.get_character("연화")["relationship"] == "동맹"
    assert ledger.get_character("연화")["role"] == "조력자"
    assert ledger.get_character("연화")["history"] == [
        "ep7: 관계 변화: 경계 -> 동맹",
        "ep7: 부상: 경상",
        "ep7: 이동: 남문",
        "ep7: 성격: 침착",
        "ep7: 백운와 관계: 동료",
    ]
    assert ledger.get_character("백운")["history"] == ["ep7: 연화와 관계: 동료"]
    assert ledger.get_item("천뢰검")["status"] == "습득"
    assert ledger.get_item("흑룡패")["status"] == "획득"
    assert ledger.get_item("치유단")["status"] == "분실"
    assert ledger.get_item("치유단")["quantity"] == 0
    assert ledger._ledger["organizations"]["혈맹"]["status"] == "destroyed"
    assert ledger._ledger["locations"]["북문"]["status"] == "destroyed"


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


def test_extract_numerical_facts_from_direct_financial_scalars():
    """[TF-C07] actual_truth direct finance scalars also sync into numbers."""
    ledger = FactLedger(_StubDB())
    state_changes = {
        "capital": 2_000_000_000,
        "total_assets": "23억",
        "wealth": "+20억",
        "market_insight": "매수 기회가 오고 있다",
    }

    ledger.update_from_state_changes(ep_num=15, state_changes=state_changes)

    nums = ledger._ledger["numbers"]
    assert nums["capital"]["value"] == 2_000_000_000
    assert nums["capital"]["unit"] == "won"
    assert nums["total_assets"]["value"] == 2_300_000_000
    assert nums["wealth"]["value"] == 2_000_000_000
    assert "market_insight" not in nums


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


class _BrokenLoadDB(_EmptyStubDB):
    def load_anchor(self, _name):
        raise RuntimeError("load fail")


def test_update_number_established_value_set():
    """[P0-2] 초기값이 established_value에 기록됨."""
    ledger = FactLedger(_EmptyStubDB())
    ledger.update_number("재산", 100, "냥", 1)
    assert ledger._ledger["numbers"]["재산"]["established_value"] == 100


def test_update_number_marks_asset_numbers_as_carryover_baseline():
    ledger = FactLedger(_EmptyStubDB())
    ledger.update_number("자본금", 100, "원", 1)

    entry = ledger.get_number("자본금")
    assert entry["authority_scope"] == "carryover_baseline"


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


def test_load_sets_degraded_contract_on_failure():
    ledger = FactLedger(_BrokenLoadDB())

    assert ledger.last_updated_ep == 0
    assert ledger.degraded is True
    assert ledger.degraded_reason == "load fail"


def test_load_empty_anchor_keeps_non_degraded_contract():
    ledger = FactLedger(_EmptyStubDB())

    assert ledger.degraded is False
    assert ledger.degraded_reason == ""


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
    assert "1억 원 (ep1) -> 10억 원 (ep12 carryover baseline)" in text


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
