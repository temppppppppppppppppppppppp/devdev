from types import SimpleNamespace
from unittest.mock import patch

from modules.core.stage2_finalizer import _build_arc_dependency_advisory, _build_character_voice_advisory
from modules.core.stage3_orchestrator import _build_stale_seed_advisory
from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.domain.agents.four_phase_arc_generator import _build_extended_timeline_advisory


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


def _make_interview_round(db=None):
    return Stage4InterviewRound(_ns(current_project=_ns(db=db or _ns()), agents={}))


def _make_builder(*, db=None, world_state=None, fact_ledger=None):
    ctx = _ns(
        current_project=_ns(db=db or _ns()),
        world_state=world_state,
        fact_ledger=fact_ledger,
    )
    return Stage4ContextBuilder(ctx)


def _make_world_state(state: dict):
    return _ns(_state=state)


def _make_fact_ledger(ledger: dict):
    return _ns(_ledger=ledger)


def test_pacing_advisory_low_dialogue():
    db = _ns(
        get_recent_pacing_records=lambda **_: [
            {"dialogue_ratio": 0.10, "pacing_score": 60},
            {"dialogue_ratio": 0.08, "pacing_score": 55},
            {"dialogue_ratio": 0.05, "pacing_score": 50},
        ]
    )
    advisory = _make_interview_round(db)._build_db_pacing_advisory(db, next_ep=10)
    assert "대화 부족 추세" in advisory


def test_pacing_advisory_normal():
    db = _ns(
        get_recent_pacing_records=lambda **_: [
            {"dialogue_ratio": 0.30, "pacing_score": 65},
            {"dialogue_ratio": 0.32, "pacing_score": 68},
            {"dialogue_ratio": 0.31, "pacing_score": 70},
        ]
    )
    advisory = _make_interview_round(db)._build_db_pacing_advisory(db, next_ep=10)
    assert advisory == ""


def test_pacing_advisory_consecutive_decline():
    db = _ns(
        get_recent_pacing_records=lambda **_: [
            {"dialogue_ratio": 0.30, "pacing_score": 65},
            {"dialogue_ratio": 0.25, "pacing_score": 65},
            {"dialogue_ratio": 0.20, "pacing_score": 65},
            {"dialogue_ratio": 0.15, "pacing_score": 65},
            {"dialogue_ratio": 0.10, "pacing_score": 65},
        ]
    )
    advisory = _make_interview_round(db)._build_db_pacing_advisory(db, next_ep=10)
    assert "연속 하락" in advisory


def test_satisfaction_advisory_consecutive_frustration():
    db = _ns(
        get_recent_satisfaction_tags=lambda **_: [
            {"frustration_flag": 1, "protagonist_agency": "능동", "satisfaction_score": 7},
            {"frustration_flag": 1, "protagonist_agency": "능동", "satisfaction_score": 7},
            {"frustration_flag": 1, "protagonist_agency": "능동", "satisfaction_score": 7},
        ]
    )
    advisory = _make_interview_round(db)._build_db_satisfaction_advisory(db, next_ep=10)
    assert "좌절감 3화 연속" in advisory


def test_satisfaction_advisory_low_agency():
    db = _ns(
        get_recent_satisfaction_tags=lambda **_: [
            {"frustration_flag": 0, "protagonist_agency": "수동", "satisfaction_score": 6},
            {"frustration_flag": 0, "protagonist_agency": "능동", "satisfaction_score": 6},
            {"frustration_flag": 0, "protagonist_agency": "수동", "satisfaction_score": 6},
            {"frustration_flag": 0, "protagonist_agency": "능동", "satisfaction_score": 6},
            {"frustration_flag": 0, "protagonist_agency": "수동", "satisfaction_score": 6},
        ]
    )
    advisory = _make_interview_round(db)._build_db_satisfaction_advisory(db, next_ep=10)
    assert "에이전시 저조" in advisory


def test_satisfaction_advisory_normal():
    db = _ns(
        get_recent_satisfaction_tags=lambda **_: [
            {"frustration_flag": 0, "protagonist_agency": "능동", "satisfaction_score": 7},
            {"frustration_flag": 0, "protagonist_agency": "능동", "satisfaction_score": 8},
            {"frustration_flag": 0, "protagonist_agency": "능동", "satisfaction_score": 7},
        ]
    )
    advisory = _make_interview_round(db)._build_db_satisfaction_advisory(db, next_ep=10)
    assert advisory == ""


def test_arc_dependency_advisory_basic():
    db = _ns(
        get_arc_dependencies=lambda _arc_no: [
            {"from_arc_no": 1, "to_arc_no": 3, "dep_type": "causes", "description": "초기 복선 회수"}
        ]
    )
    advisory = _build_arc_dependency_advisory(db, arc_no=3)
    assert "[DB-3 Arc 의존성]" in advisory
    assert "Arc 1 → 현재" in advisory


def test_arc_dependency_advisory_empty():
    db = _ns(get_arc_dependencies=lambda _arc_no: [])
    advisory = _build_arc_dependency_advisory(db, arc_no=3)
    assert advisory == ""


def test_foreshadow_stale_seed_advisory():
    db = _ns(get_active_seeds=lambda: [{"content": "초반 투자 떡밥", "planted_ep": 5}])
    advisory = _build_stale_seed_advisory(db, next_ep=30)
    assert "25화 경과" in advisory


def test_foreshadow_recent_seed_no_advisory():
    db = _ns(get_active_seeds=lambda: [{"content": "최근 복선", "planted_ep": 25}])
    advisory = _build_stale_seed_advisory(db, next_ep=30)
    assert advisory == ""


def test_foreshadow_empty():
    db = _ns(get_active_seeds=lambda: [])
    advisory = _build_stale_seed_advisory(db, next_ep=30)
    assert advisory == ""


def test_canonical_facts_in_packet():
    db = _ns(
        get_canonical_facts=lambda fact_type=None: [
            {
                "fact_key": "자본금",
                "value": {"value": "10억", "unit": "원"},
                "first_ep": 1,
                "last_ep": 30,
                "confidence": "confirmed",
            }
        ]
    )
    builder = _make_builder(db=db)
    packet = builder.context_packets.build_continuity_packet(
        {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": "이번 화 자본금 운용"}
    )
    assert "정규 팩트 참조" in packet
    assert "자본금" in packet


def test_canonical_facts_no_match():
    db = _ns(
        get_canonical_facts=lambda fact_type=None: [
            {
                "fact_key": "자본금",
                "value": {"value": "10억", "unit": "원"},
                "first_ep": 1,
                "last_ep": 30,
                "confidence": "confirmed",
            }
        ]
    )
    builder = _make_builder(db=db)
    packet = builder.context_packets.build_continuity_packet(
        {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": "이번 화 감정선 강화"}
    )
    assert packet == ""


def test_reveals_advisory_basic():
    db = _ns(
        get_episode_bible=lambda ep: {"reveals": ["범인은 박대리"]} if ep == 15 else {}
    )
    advisory = _make_interview_round(db)._build_db_reveals_advisory(db, next_ep=20)
    assert "ep15: 범인은 박대리" in advisory


def test_reveals_advisory_empty():
    db = _ns(get_episode_bible=lambda ep: {})
    advisory = _make_interview_round(db)._build_db_reveals_advisory(db, next_ep=20)
    assert advisory == ""


def test_character_voice_stage2_injection():
    db = _ns(
        get_all_character_voices=lambda: [
            {"npc_name": "장천", "profile_data": '{"tone":"냉철","speech_pattern":"짧고 단호함"}'}
        ]
    )
    advisory = _build_character_voice_advisory(db)
    assert "장천: 냉철" in advisory


def test_character_voice_empty():
    db = _ns(get_all_character_voices=lambda: [])
    advisory = _build_character_voice_advisory(db)
    assert advisory == ""


def test_reflexion_director_advisory():
    ir = _make_interview_round()
    with patch("modules.core.reflexion_manager.ReflexionManager.get_top_patterns") as get_top_patterns:
        get_top_patterns.return_value = [
            {"pattern_type": "future_leak", "frequency": 5, "description": "미래 정보 누수 반복"}
        ]
        advisory = ir._build_db_reflexion_advisory(next_ep=25)
    assert "반복 실패 패턴" in advisory
    assert "future_leak" in advisory


def test_reflexion_below_threshold():
    ir = _make_interview_round()
    with patch("modules.core.reflexion_manager.ReflexionManager.get_top_patterns") as get_top_patterns:
        get_top_patterns.return_value = []
        advisory = ir._build_db_reflexion_advisory(next_ep=25)
    assert advisory == ""


def test_reflexion_early_episode():
    ir = _make_interview_round()
    with patch("modules.core.reflexion_manager.ReflexionManager.get_top_patterns") as get_top_patterns:
        advisory = ir._build_db_reflexion_advisory(next_ep=5)
    assert advisory == ""
    get_top_patterns.assert_not_called()


def test_timeline_extended_injection():
    db = _ns(
        get_timeline_range=lambda **_: [
            {"ep_no": ep, "story_date": f"2026-03-{ep:02d}", "elapsed_days": ep, "time_note": f"노트{ep}"}
            for ep in range(1, 11)
        ]
    )
    lines = _build_extended_timeline_advisory(db)
    assert lines
    assert "[DB-9 확장 타임라인" in lines[0]
    assert "ep10" in "\n".join(lines)


def test_timeline_short_skip():
    db = _ns(
        get_timeline_range=lambda **_: [
            {"ep_no": ep, "story_date": "", "elapsed_days": ep, "time_note": ""}
            for ep in range(1, 4)
        ]
    )
    lines = _build_extended_timeline_advisory(db)
    assert lines == []


def test_npc_history_with_reason():
    db = _ns(
        get_npc_history=lambda npc_name, limit=3: [
            {
                "episode_no": 18,
                "field_name": "location",
                "old_value": "한양",
                "new_value": "북해",
                "reason": "부상으로 인한 위치 이동",
            }
        ],
        get_canonical_facts=lambda fact_type=None: [],
    )
    world_state = _make_world_state(
        {"alive_npcs": {"장천": {"role": "검객"}}, "dead_npcs": {}, "active_items": {}, "active_plots": []}
    )
    builder = _make_builder(db=db, world_state=world_state)
    packet = builder.context_packets.build_continuity_packet(
        {"npcs": ["장천"], "items": [], "plots": [], "locations": [], "_full_text": ""}
    )
    assert "(부상으로 인한 위치 이동)" in packet


def test_npc_history_no_reason():
    db = _ns(
        get_npc_history=lambda npc_name, limit=3: [
            {
                "episode_no": 18,
                "field_name": "location",
                "old_value": "한양",
                "new_value": "북해",
                "reason": "",
            }
        ],
        get_canonical_facts=lambda fact_type=None: [],
    )
    world_state = _make_world_state(
        {"alive_npcs": {"장천": {"role": "검객"}}, "dead_npcs": {}, "active_items": {}, "active_plots": []}
    )
    builder = _make_builder(db=db, world_state=world_state)
    packet = builder.context_packets.build_continuity_packet(
        {"npcs": ["장천"], "items": [], "plots": [], "locations": [], "_full_text": ""}
    )
    assert "[변경 18화] location: 한양 → 북해" in packet
    assert "(부상으로 인한 위치 이동)" not in packet
