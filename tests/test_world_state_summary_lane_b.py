from modules.core.world_state import WorldStateManager


class _WorldStateDB:
    def load_anchor(self, _name):
        return None

    def save_anchor(self, _name, _payload):
        return None


def _build_manager():
    return WorldStateManager(_WorldStateDB())


def test_npc_importance_prefers_companion_then_relation_then_role():
    manager = _build_manager()

    assert manager._npc_importance(("동행", {"companion": True})) == 3
    assert manager._npc_importance(("관계", {"relation": "동료"})) == 2
    assert manager._npc_importance(("역할", {"role": "조연"})) == 1
    assert manager._npc_importance(("기타", {})) == 0


def test_build_summary_npc_sections_preserves_known_attr_and_truncation_contract():
    manager = _build_manager()
    manager._state.update(
        {
            "alive_npcs": {
                "노사부": {
                    "role": "사부",
                    "relation": "동료",
                    "companion": True,
                    "known_attrs": {
                        "injury": {"value": "안대"},
                        "location": {"value": "서울시청"},
                        "permanent_injuries": {"value": "왼팔 장애"},
                    },
                },
                **{f"npc{i}": {"role": "조연"} for i in range(30)},
            },
            "dead_npcs": {f"dead{i}": {"ep": i, "cause": "사망"} for i in range(21)},
        }
    )

    sections = manager._build_summary_npc_sections()
    text = "\n\n".join(sections)

    assert "[생존 NPC (30명) (총 31명 중 30명 표시)]" in text
    assert "노사부: 사부 / 관계=동료" in text
    assert "부상=안대" in text
    assert "위치기록=서울시청" in text
    assert "영구부상=왼팔 장애" in text
    assert "[사망 NPC (20명) (총 21명 중 20명 표시) -- 절대 등장 금지]" in text


def test_build_summary_world_tail_sections_preserves_section_order_and_suffixes():
    manager = _build_manager()
    manager._state.update(
        {
            "destroyed": [{"name": f"장소{i}", "type": "장소", "ep": i} for i in range(11)],
            "active_plots": [{"plot": f"플롯{i}", "since_ep": i} for i in range(11)],
            "active_pressure_vectors": [
                {"text": "해독제를 찾지 못하면 독이 퍼진다."},
                {"text": "추격대가 성문을 포위했다."},
            ],
            "world_laws": [{"law": "사망자는 회상/언급만 허용", "established_ep": 1}],
            "timeline": [{"ep": i, "description": f"{i}일 경과"} for i in range(6)],
        }
    )

    sections = manager._build_summary_world_tail_sections()
    text = "\n\n".join(sections)

    assert "[파괴된 장소/조직 (총 11개 중 10개 표시) -- 복구 불가]" in text
    assert "[진행 중 플롯 (총 11개 중 10개 표시)]" in text
    assert "[지속 압박/위협]" in text
    assert "해독제를 찾지 못하면 독이 퍼진다." in text
    assert "[세계관 절대 법칙 -- 위반 금지]" in text
    assert "[시간 흐름 (최근) (총 6개 중 5개 표시)]" in text


def test_get_summary_stitches_helper_sections_and_truncates():
    manager = _build_manager()
    manager._state["last_updated_ep"] = 12
    manager._build_summary_protagonist_sections = lambda: ["[주인공]\n" + ("A" * 60)]
    manager._build_summary_npc_sections = lambda: ["[생존 NPC]\n" + ("B" * 60)]
    manager._build_summary_relation_and_inventory_sections = lambda: []
    manager._build_summary_world_tail_sections = lambda: ["[시간 흐름]\n" + ("C" * 60)]

    summary = manager.get_summary(max_chars=120)

    assert summary.startswith("=== 세계 상태 (제12화 기준) ===")
    assert "...(세계 상태 요약 일부 생략)" in summary
