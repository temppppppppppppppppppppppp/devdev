"""
[Phase1-L0] Canonical Constraints 테스트
- canonical_facts DB round-trip
- FactLedger.get_canonical_summary() 안전성
- WorldState.get_canonical_constraints() 안전성
- 예산 준수 확인
"""


# ── 헬퍼: 최소 DBManager 인스턴스 생성 ──────────────────────────────


def _make_db(tmp_path):
    from modules.core.db_manager import DBManager

    return DBManager(tmp_path / "test.db")


# ── 1. FactLedger.get_canonical_summary() 안전성 ─────────────────────


def test_get_canonical_summary_empty_safe(tmp_path):
    """numbers 없을 때 빈 문자열 반환."""
    from modules.core.fact_ledger import FactLedger

    db = _make_db(tmp_path)
    fl = FactLedger(db)
    result = fl.get_canonical_summary()
    assert result == ""


def test_get_canonical_summary_with_numbers(tmp_path):
    """numbers 있으면 수치 요약 반환."""
    from modules.core.fact_ledger import FactLedger

    db = _make_db(tmp_path)
    fl = FactLedger(db)
    fl.update_number("주인공_전투력", 9000, "레벨", 10)
    result = fl.get_canonical_summary()
    assert "[수치 제약 (L0)]" in result
    assert "주인공_전투력" in result
    assert "9000" in result


def test_get_canonical_summary_max_chars(tmp_path):
    """max_chars 준수 확인."""
    from modules.core.fact_ledger import FactLedger

    db = _make_db(tmp_path)
    fl = FactLedger(db)
    for i in range(50):
        fl.update_number(f"key_{i:03d}", i * 1000, "원", i + 1)
    result = fl.get_canonical_summary(max_chars=200)
    assert len(result) <= 200


# ── 2. WorldState.get_canonical_constraints() 안전성 ─────────────────


def test_get_canonical_constraints_empty_safe(tmp_path):
    """alive_npcs 없을 때 빈 문자열 반환."""
    from modules.core.world_state import WorldStateManager

    db = _make_db(tmp_path)
    ws = WorldStateManager(db)
    result = ws.get_canonical_constraints()
    assert result == ""


def test_get_canonical_constraints_no_world_laws(tmp_path):
    """world_laws 없어도 NPC만 반환, 크래시 없음."""
    from modules.core.world_state import WorldStateManager

    db = _make_db(tmp_path)
    ws = WorldStateManager(db)
    ws._state["alive_npcs"]["테스트NPC"] = {
        "role_at_intro": "마을 촌장",
        "first_seen_ep": 1,
        "known_attrs": {"나이": {"value": "55", "changed_ep": 1}},
    }
    result = ws.get_canonical_constraints()
    assert "[캐릭터 고정 속성 (L0)]" in result
    assert "테스트NPC" in result
    assert "마을 촌장" in result


def test_canonical_budget_respected(tmp_path):
    """get_canonical_constraints max_chars 준수."""
    from modules.core.world_state import WorldStateManager

    db = _make_db(tmp_path)
    ws = WorldStateManager(db)
    for i in range(30):
        ws._state["alive_npcs"][f"NPC_{i:03d}"] = {
            "role_at_intro": f"역할_{i}",
            "first_seen_ep": i + 1,
            "known_attrs": {},
        }
    result = ws.get_canonical_constraints(max_chars=500)
    assert len(result) <= 500


# ── 3. DB round-trip ─────────────────────────────────────────────────


def test_upsert_and_get_canonical_facts(tmp_path):
    """canonical_facts DB round-trip."""
    db = _make_db(tmp_path)
    db.upsert_canonical_fact(
        fact_key="test_key",
        fact_type="numerical",
        value={"value": 100, "unit": "원"},
        first_ep=1,
        last_ep=5,
    )
    facts = db.get_canonical_facts()
    assert len(facts) == 1
    assert facts[0]["fact_key"] == "test_key"
    assert facts[0]["fact_type"] == "numerical"
    assert facts[0]["value"]["value"] == 100


def test_get_canonical_facts_filter_by_type(tmp_path):
    """fact_type 필터 동작 확인."""
    db = _make_db(tmp_path)
    db.upsert_canonical_fact("num_key", "numerical", 42, 1, 3)
    db.upsert_canonical_fact("npc_key", "npc_attr", "촌장", 1, 1)
    num_facts = db.get_canonical_facts(fact_type="numerical")
    assert len(num_facts) == 1
    assert num_facts[0]["fact_key"] == "num_key"
    all_facts = db.get_canonical_facts()
    assert len(all_facts) == 2


def test_update_number_syncs_to_db(tmp_path):
    """update_number() 호출 시 canonical_facts DB에 sync됨."""
    from modules.core.fact_ledger import FactLedger

    db = _make_db(tmp_path)
    fl = FactLedger(db)
    fl.update_number("수익률", 15.5, "%", 7)
    facts = db.get_canonical_facts(fact_type="numerical")
    keys = [f["fact_key"] for f in facts]
    assert "수익률" in keys
