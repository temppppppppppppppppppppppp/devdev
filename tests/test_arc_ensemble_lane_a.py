from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator


def _make_context():
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.db = MagicMock()
    ctx.db.load_anchor.return_value = {}
    ctx.current_project = SimpleNamespace(name="Lane A Project")
    ctx.project_name = "Lane A Project"
    return ctx


def _make_agent() -> ArcEnsembleGenerator:
    agent = ArcEnsembleGenerator(_make_context(), MagicMock())
    agent._operator_log = MagicMock()
    agent._build_strategy_execution_plan = MagicMock(side_effect=lambda items: [dict(item) for item in items])
    return agent


def _base_candidate(**overrides) -> dict:
    candidate = {
        "arc_no": 1,
        "ep_count": 3,
        "tactical_doc": "x" * 1800,
        "joint_docs": {"final_location": "A", "physical_inventory": [], "world_joint": ""},
        "state_constraints": {
            "arc_start_state": {"location": "A", "equipment": []},
            "arc_end_state": {"location": "B", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        },
        "state_changes": {
            "timeline": {"start": {}, "end": {}},
            "npc_deaths": [],
            "skill_acquisitions": [],
            "relationship_changes": [],
            "major_items": [],
            "resolved_plots": [],
        },
    }
    candidate.update(overrides)
    return candidate


def test_generate_ensemble_single_strategy_live_shell_routes_only_selected_strategy():
    agent = _make_agent()
    agent.max_workers = 1
    agent.strategies = [
        {"name": "conservative", "temperature": 0.3, "focus": "", "style": ""},
        {"name": "balanced", "temperature": 0.5, "focus": "", "style": ""},
        {"name": "creative", "temperature": 0.7, "focus": "", "style": ""},
    ]
    agent._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/arc"})
    agent._evaluate_candidate = MagicMock(return_value=(91, []))
    agent._generate_single = MagicMock(return_value=_base_candidate())

    best, candidates = agent.generate_ensemble(
        arc_no=4,
        ep_start=10,
        vol_strategy="",
        curr_block={"ep_count": 3},
        prev_arc_context="prev context",
        constraint_block="constraint",
        assets={},
        single_strategy="balanced",
        strategy_specific_feedback="tighten act 2",
        rejected_strategy="balanced",
    )

    assert best is None
    assert len(candidates) == 1
    assert agent._generate_single.call_count == 1
    kwargs = agent._generate_single.call_args.kwargs
    assert kwargs["strategy"]["name"] == "balanced"
    assert kwargs["strategy_feedback"] == "tighten act 2"


def test_qualify_candidates_by_tactical_length_keeps_longest_short_candidate():
    agent = _make_agent()

    shorter = _base_candidate(tactical_doc={"content": "a" * 400}, ep_count=3, _strategy="shorter")
    longer = _base_candidate(tactical_doc=["b" * 700], ep_count=3, _strategy="longer")

    qualified = agent._qualify_candidates_by_tactical_length([shorter, longer], fallback_ep_count=3)

    assert qualified == [longer]
    assert shorter["tactical_doc"] == "a" * 400
    assert longer["tactical_doc"] == "b" * 700


def test_apply_ensemble_metadata_strips_transient_scoring_fields():
    agent = _make_agent()
    director_candidates = [_base_candidate(_strategy="balanced", _score=88, _issues=["first issue"])]
    scored_candidates = director_candidates + [_base_candidate(_strategy="creative", _score=81, _issues=[])]

    agent._apply_ensemble_metadata(
        director_candidates,
        scored_candidates,
        {"max_similarity": 0.25, "warning": ""},
    )

    meta = director_candidates[0]["_ensemble_meta"]
    assert meta["all_scores"] == [("balanced", 88), ("creative", 81)]
    assert meta["candidate_index"] == 0
    assert meta["total_candidates"] == 1
    assert "_score" not in scored_candidates[0]
    assert "_issues" not in scored_candidates[1]


def test_build_single_arc_generation_context_uses_structured_current_block_authority_packet():
    agent = _make_agent()

    prompt_context = agent._build_single_arc_generation_context(
        curr_block={
            "block_id": "block_02",
            "title": "Branch Office Pressure",
            "ep_count": 3,
            "content": {"context": "The protagonist enters the branch office and faces pressure."},
            "block_theme": "escalation",
            "foreshadow": "a missing ledger",
        },
        prev_arc_context="previous context",
        constraint_block="constraint block",
        protagonist_config=None,
        entity_registry=None,
        genre="investment",
    )

    packet = prompt_context["curr_block_authority"]
    assert "CURRENT BLOCK DNA > BLOCK EVENT GUARD > PREVIOUS ARC CONTEXT > OPTIONAL EXTENSIONS" in packet
    assert '"title"' not in packet
    assert "- title: Branch Office Pressure" in packet
    assert "- block_premise: The protagonist enters the branch office and faces pressure." in packet


def test_arc_prompt_places_current_block_before_previous_arc_context():
    agent = _make_agent()
    prompt_context = agent._build_single_arc_generation_context(
        curr_block={
            "block_id": "block_02",
            "title": "Branch Office Pressure",
            "content": {"context": "The protagonist enters the branch office."},
        },
        prev_arc_context="PREV_ARC_CONTEXT",
        constraint_block="CONSTRAINT_BLOCK",
        protagonist_config=None,
        entity_registry=None,
        genre="investment",
    )

    prompt, _ = agent._build_single_arc_prompt_bundle(
        strategy={"name": "balanced", "focus": "focus", "style": "style"},
        prompt_context=prompt_context,
        constraint_block="CONSTRAINT_BLOCK",
        prev_arc_context="PREV_ARC_CONTEXT",
        curr_block={"title": "Branch Office Pressure"},
        pacing_signal_guide="",
        vol_strategy="",
        assets={},
        merged_feedback="",
        protagonist_name="Hero",
        genre="investment",
        arc_no=2,
        ep_start=5,
        ep_end=7,
        cache_name="",
    )

    block_idx = prompt.index("### [Current Block DNA]")
    guard_idx = prompt.index("### [Current Block Event Guard]")
    prev_idx = prompt.index("### [Previous Arc Context - carryover reference]")

    assert block_idx < prev_idx
    assert guard_idx < prev_idx


def test_arc_prompt_includes_carryover_authority_packet_section():
    agent = _make_agent()
    prev_arc_context = """[Carryover Authority Packet]
- next_arc_start_location: Gangnam HQ
- next_arc_start_equipment: ['BlackBerry 7100', 'Ecuador memo']
"""
    prompt_context = agent._build_single_arc_generation_context(
        curr_block={
            "block_id": "block_03",
            "title": "Late Night Desk",
            "content": {"context": "The protagonist works through the night."},
        },
        prev_arc_context=prev_arc_context,
        constraint_block="CONSTRAINT_BLOCK",
        protagonist_config=None,
        entity_registry=None,
        genre="investment",
    )

    prompt, _ = agent._build_single_arc_prompt_bundle(
        strategy={"name": "balanced", "focus": "focus", "style": "style"},
        prompt_context=prompt_context,
        constraint_block="CONSTRAINT_BLOCK",
        prev_arc_context=prev_arc_context,
        curr_block={"title": "Late Night Desk"},
        pacing_signal_guide="",
        vol_strategy="",
        assets={},
        merged_feedback="",
        protagonist_name="Hero",
        genre="investment",
        arc_no=3,
        ep_start=8,
        ep_end=10,
        cache_name="",
    )

    packet_idx = prompt.index("### [Carryover Authority Packet - authoritative next-arc opening state]")
    prev_idx = prompt.index("### [Previous Arc Context - carryover reference]")
    assert packet_idx < prev_idx
    assert "- next_arc_start_location: Gangnam HQ" in prompt
    assert "- next_arc_start_equipment: ['BlackBerry 7100', 'Ecuador memo']" in prompt


def test_evaluate_candidate_prefers_carryover_authority_packet_for_start_state():
    agent = _make_agent()
    candidate = _base_candidate(
        state_constraints={
            "arc_start_state": {"location": "Wrong Office", "equipment": ["Corporate seal"]},
            "arc_end_state": {"location": "B", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        }
    )
    prev_arc_context = """[Carryover Authority Packet]
- next_arc_start_location: Gangnam HQ
- next_arc_start_equipment: ['BlackBerry 7100', 'Ecuador memo']
"""

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context=prev_arc_context,
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert any("carryover authority 시작 위치 불일치" in issue for issue in issues)
    assert any("에콰도르 메모" in issue or "소지품" in issue for issue in issues)


def test_ensure_required_fields_backfills_episode_details_from_beat_sequence():
    agent = _make_agent()
    result = agent._ensure_required_fields(
        {
            "tactical_doc": "제 4화: 야간 점검\n제 5화: 장부 확인",
            "beat_sequence": ["야간 점검에서 이상 징후 포착", "장부 확인 후 반격 준비"],
            "joint_docs": {"final_location": "B", "physical_inventory": [], "world_joint": ""},
            "state_constraints": {
                "arc_start_state": {"location": "A", "equipment": []},
                "arc_end_state": {"location": "B", "equipment": []},
                "items_acquired": [],
                "items_consumed": [],
            },
            "state_changes": {
                "timeline": {"start": {}, "end": {}},
                "npc_deaths": [],
                "skill_acquisitions": [],
                "relationship_changes": [],
                "major_items": [],
                "resolved_plots": [],
            },
        },
        arc_no=2,
        ep_start=4,
        ep_end=5,
    )

    assert result["episode_details"] == [
        {"ep_num": 4, "details": ["야간 점검에서 이상 징후 포착"]},
        {"ep_num": 5, "details": ["장부 확인 후 반격 준비"]},
    ]


def test_ensure_required_fields_preserves_existing_episode_details_as_authority():
    agent = _make_agent()
    result = agent._ensure_required_fields(
        {
            "tactical_doc": "제 4화: 일반 전술 문장",
            "beat_sequence": ["beat fallback"],
            "episode_details": [{"ep_num": 4, "details": ["정확한 mission packet"]}],
            "joint_docs": {"final_location": "B", "physical_inventory": [], "world_joint": ""},
            "state_constraints": {
                "arc_start_state": {"location": "A", "equipment": []},
                "arc_end_state": {"location": "B", "equipment": []},
                "items_acquired": [],
                "items_consumed": [],
            },
            "state_changes": {
                "timeline": {"start": {}, "end": {}},
                "npc_deaths": [],
                "skill_acquisitions": [],
                "relationship_changes": [],
                "major_items": [],
                "resolved_plots": [],
            },
        },
        arc_no=2,
        ep_start=4,
        ep_end=4,
    )

    assert result["episode_details"] == [{"ep_num": 4, "details": ["정확한 mission packet"]}]


def test_evaluate_candidate_penalizes_missing_episode_details_mission_packet():
    agent = _make_agent()
    candidate = _base_candidate(
        ep_start=4,
        ep_end=6,
        ep_count=3,
        episode_details=[],
    )

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context="서사 시작점",
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert "canonical mission packet missing: episode_details" in issues


def test_evaluate_candidate_penalizes_incomplete_episode_details_coverage():
    agent = _make_agent()
    candidate = _base_candidate(
        ep_start=4,
        ep_end=6,
        ep_count=3,
        episode_details=[{"ep_num": 4, "details": ["첫 화 사건"]}],
    )

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context="서사 시작점",
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert any("episode_details mission packet coverage 부족" in issue for issue in issues)


def test_ensure_required_fields_syncs_joint_docs_from_arc_end_state_when_missing():
    agent = _make_agent()
    result = agent._ensure_required_fields(
        {
            "tactical_doc": "제 4화: 야간 점검",
            "episode_details": [{"ep_num": 4, "details": ["야간 점검"]}],
            "joint_docs": {"final_location": "", "physical_inventory": [], "world_joint": ""},
            "state_constraints": {
                "arc_start_state": {"location": "A", "equipment": ["시작 노트"]},
                "arc_end_state": {"location": "Gangnam HQ", "equipment": ["BlackBerry 7130", "에콰도르 메모"]},
                "items_acquired": [],
                "items_consumed": [],
            },
            "state_changes": {
                "timeline": {"start": {}, "end": {}},
                "npc_deaths": [],
                "skill_acquisitions": [],
                "relationship_changes": [],
                "major_items": [],
                "resolved_plots": [],
            },
        },
        arc_no=2,
        ep_start=4,
        ep_end=4,
    )

    assert result["joint_docs"]["final_location"] == "Gangnam HQ"
    assert result["joint_docs"]["physical_inventory"] == ["BlackBerry 7130", "에콰도르 메모"]


def test_evaluate_candidate_penalizes_tactical_meta_vocabulary():
    agent = _make_agent()
    candidate = _base_candidate(
        tactical_doc="Arc 2에서는 Block 3의 여파를 정리하고 Stage 2 결과를 검토한다." + ("x" * 1800),
        ep_start=4,
        ep_end=6,
        episode_details=[
            {"ep_num": 4, "details": ["첫 화 사건"]},
            {"ep_num": 5, "details": ["둘째 화 사건"]},
            {"ep_num": 6, "details": ["셋째 화 사건"]},
        ],
    )

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context="서사 시작점",
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert any("tactical_doc meta vocabulary leak" in issue for issue in issues)


def test_evaluate_candidate_penalizes_verbose_state_field_blob():
    agent = _make_agent()
    candidate = _base_candidate(
        ep_start=4,
        ep_end=6,
        episode_details=[
            {"ep_num": 4, "details": ["첫 화 사건"]},
            {"ep_num": 5, "details": ["둘째 화 사건"]},
            {"ep_num": 6, "details": ["셋째 화 사건"]},
        ],
        joint_docs={
            "final_location": "서울 강남구, 테헤란로의 허름한 오피스텔 15층. 아직 페인트 냄새도 가시지 않은 텅 빈 공간.",
            "physical_inventory": ["책상 위에 놓인 2006년형 최신 사양의 조립식 컴퓨터 본체와 모니터 2대, 법인 통장과 OTP 카드"],
            "world_joint": "",
        },
    )

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context="서사 시작점",
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert any("short canonical label" in issue or "sentence-style inventory blob" in issue for issue in issues)


def test_evaluate_candidate_penalizes_verbose_start_location_label():
    agent = _make_agent()
    agent._genre = "investment"
    candidate = _base_candidate(
        ep_start=4,
        ep_end=6,
        episode_details=[
            {"ep_num": 4, "details": ["첫 화 사건"]},
            {"ep_num": 5, "details": ["둘째 화 사건"]},
            {"ep_num": 6, "details": ["셋째 화 사건"]},
        ],
        state_constraints={
            "arc_start_state": {
                "location": "서울 강남, SW인베스트먼트 오피스, 아직 페인트 냄새가 남은 임시 작업 공간",
                "equipment": [],
            },
            "arc_end_state": {"location": "강남 HQ", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        },
    )

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context="서사 시작점",
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert "arc_start_state.location must be a short canonical label" in issues


def test_evaluate_candidate_penalizes_non_wuxia_state_noise():
    agent = _make_agent()
    agent._genre = "investment"
    candidate = _base_candidate(
        ep_start=4,
        ep_end=6,
        episode_details=[
            {"ep_num": 4, "details": ["첫 화 사건"]},
            {"ep_num": 5, "details": ["둘째 화 사건"]},
            {"ep_num": 6, "details": ["셋째 화 사건"]},
        ],
        state_constraints={
            "arc_start_state": {"location": "여의도 HQ", "equipment": [], "internal_energy": 100},
            "arc_end_state": {"location": "강남 HQ", "equipment": [], "realm": "후천"},
            "items_acquired": [],
            "items_consumed": [],
        },
    )

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context="서사 시작점",
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert any("non-wuxia state noise" in issue for issue in issues)


def test_evaluate_candidate_penalizes_investment_arithmetic_boundary_mismatch():
    agent = _make_agent()
    agent._genre = "investment"
    candidate = _base_candidate(
        arc_no=3,
        ep_start=11,
        ep_end=13,
        episode_details=[
            {"ep_num": 11, "details": ["유가 포지션을 점검한다."]},
            {"ep_num": 12, "details": ["차익 일부를 실현한다."]},
            {"ep_num": 13, "details": ["총자산 30억을 확인한다."]},
        ],
        state_constraints={
            "arc_start_state": {"location": "Gangnam HQ", "equipment": [], "total_assets": "28억"},
            "arc_end_state": {
                "location": "Gangnam HQ",
                "equipment": [],
                "capital": "17억 5천만원",
                "total_assets": "30억",
            },
            "investment_calc": {
                "transactions": [],
                "final_cash": "17억 5천만원",
                "final_total_assets": "30억",
            },
            "items_acquired": [],
            "items_consumed": [],
        },
    )

    score, issues = agent._evaluate_candidate(
        candidate,
        prev_arc_context=(
            "[Carryover Authority Packet]\n"
            "- next_arc_start_capital: 17억 5천만원\n"
            "- next_arc_start_total_assets: 23억\n"
        ),
        constraint_block="",
        prev_equipment=None,
        forbidden_items=[],
    )

    assert score < 100
    assert any("investment arithmetic warning:" in issue for issue in issues)
