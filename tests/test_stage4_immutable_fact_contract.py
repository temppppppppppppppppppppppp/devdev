"""Targeted tests for modules.core.stage4_immutable_fact_contract.

Covers:
- packet build from blueprint/state
- violation classification
- rewrite escalation logic
- actor reference normalization
- relationship_changes normalization
- CW prompt rendering
"""

from modules.core.stage4_immutable_fact_contract import (
    VIOLATION_COMMITTED_STATE_REGRESSION,
    VIOLATION_COMPLETED_EVENT_REPLAY,
    VIOLATION_METADATA_REFERENCE_SHAPE,
    VIOLATION_OPENING_ANCHOR_DRIFT,
    VIOLATION_SCENE_OBLIGATION_MISSING,
    ImmutableFactPacket,
    build_packet,
    classify_violation_family,
    normalize_actor_reference,
    normalize_relationship_changes,
    render_packet_for_cw,
    render_violation_summary,
    should_escalate_to_rewrite,
)

# ── build_packet ─────────────────────────────────────────────────


class TestBuildPacket:
    def test_empty_inputs(self):
        packet = build_packet()
        assert packet.is_empty()

    def test_opening_anchor_from_blueprint(self):
        bp = {
            "start_location": "강남 5성급 호텔",
            "time_flow": "오전 11시 -> 오후 1시",
            "opening_transition": {"type": "explicit_transition", "signals": ["location_shift"]},
            "scene_breakdown": {
                "scene_1": {
                    "title": "호텔 라운지의 만남",
                    "location": "라운지 카페",
                    "goal": "첫 대면",
                },
                "scene_2": {
                    "title": "세단 이동",
                    "goal": "이동 중 대화",
                },
            },
        }
        packet = build_packet(blueprint=bp)
        assert not packet.is_empty()
        assert packet.start_location == "강남 5성급 호텔"
        assert packet.start_time_flow == "오전 11시 -> 오후 1시"
        assert packet.scene_1_title == "호텔 라운지의 만남"
        assert packet.scene_1_location == "라운지 카페"
        assert packet.opening_transition_type == "explicit_transition"

    def test_scene_obligations_extracted(self):
        bp = {
            "scene_breakdown": {
                "scene_1": {"title": "씬1", "goal": "목표1", "location": "장소1"},
                "scene_2": {"title": "씬2", "summary": "요약2"},
            }
        }
        packet = build_packet(blueprint=bp)
        assert len(packet.scene_obligations) == 2
        assert packet.scene_obligations[0].goal == "목표1"
        assert packet.scene_obligations[1].goal == "요약2"

    def test_blueprint_metadata_completeness_flag(self):
        bp = {
            "scene_breakdown": {
                "scene_1": {"title": "씬1"},  # no goal/summary
                "scene_2": {"title": "씬2", "goal": "목표"},
            }
        }
        packet = build_packet(blueprint=bp)
        assert not packet.blueprint_metadata_complete

    def test_committed_state_facts_from_ledger(self):
        ledger = "- 자본금: 38억\n- 매출: 10억\n- 기타 정보"
        packet = build_packet(fact_ledger_summary=ledger)
        assert any("38억" in f for f in packet.committed_state_facts)

    def test_completed_events_from_digest(self):
        digest = "- 투자 계약 완료\n- 일반 대화\n- NPC 처단 성공"
        packet = build_packet(prev_digest=digest)
        assert len(packet.completed_event_facts) >= 2

    def test_prev_ending_bridge_truncation(self):
        long_text = "a" * 1000
        packet = build_packet(prev_manuscript_ending=long_text)
        assert len(packet.prev_ending_bridge) == 500

    def test_committed_state_english_capital_won(self):
        """[Wave1-B] English-form 'capital ... won' must yield committed-state facts."""
        ledger = "- capital: 2000000000.0 won\n- misc note"
        packet = build_packet(fact_ledger_summary=ledger)
        assert any("capital" in f for f in packet.committed_state_facts)

    def test_committed_state_english_balance_account_fund(self):
        """[Wave1-B] English labels balance/account/fund must be recognized."""
        ledger = "- account balance: 500000 won\n- fund allocation: 30%\n- unrelated note"
        packet = build_packet(fact_ledger_summary=ledger)
        assert len(packet.committed_state_facts) >= 2

    def test_committed_state_korean_still_works(self):
        """[Wave1-B] Existing Korean keywords must not regress."""
        ledger = "- 자본금: 38억\n- 계좌 잔고: 10억\n- 기타 정보"
        packet = build_packet(fact_ledger_summary=ledger)
        assert any("38억" in f for f in packet.committed_state_facts)
        assert any("잔고" in f for f in packet.committed_state_facts)

    def test_completed_events_investment_verbs(self):
        """[Wave1-C] Investment-fiction verbs must yield completed-event facts."""
        digest = "- 증권 계좌 개설\n- 인프라 구축\n- 2억 이체\n- 투자 계약 체결"
        packet = build_packet(prev_digest=digest)
        assert len(packet.completed_event_facts) >= 4

    def test_completed_events_wuxia_no_regression(self):
        """[Wave1-C] Existing wuxia/action verbs must not regress."""
        digest = "- 적장군 처단 성공\n- 비급 습득\n- 관문 돌파"
        packet = build_packet(prev_digest=digest)
        assert len(packet.completed_event_facts) >= 3

    def test_committed_state_ownership_keywords(self):
        """[Wave2-A] Entity-ownership lines must yield committed-state facts."""
        ledger = (
            "- OTP 발생기 (보유, 소유: 주인공, ep3)\n- SW인베스트먼트 법인 인감 (획득, 소유: 주인공, ep4)\n- 일반 메모"
        )
        packet = build_packet(fact_ledger_summary=ledger)
        assert len(packet.committed_state_facts) >= 2
        assert any("소유" in f for f in packet.committed_state_facts)
        assert any("법인" in f for f in packet.committed_state_facts)

    def test_committed_state_personal_entity_keywords(self):
        """[Wave2-A] Personal/entity attribution lines must be recognized."""
        ledger = "- 개인 명의 파생 계좌 (보유, ep3)\n- SW인베스트먼트 (활동중, 수장: 한시윤)"
        packet = build_packet(fact_ledger_summary=ledger)
        assert len(packet.committed_state_facts) >= 2

    def test_committed_state_wave1_monetary_no_regression(self):
        """[Wave2-A] Wave 1 monetary keywords must not regress."""
        ledger = "- capital: 2000000000.0 won\n- 자본금: 38억\n- 계좌 잔고: 10억"
        packet = build_packet(fact_ledger_summary=ledger)
        assert len(packet.committed_state_facts) >= 3

    def test_completed_events_procedural_keywords(self):
        """[Wave2-B] Procedural-completion verbs must yield completed-event facts."""
        digest = "- 계좌 세팅 완료\n- OTP 수령\n- 법인 인감 발급\n- 법인 설립 완료\n- 사무실 입주\n- HTS 접속 확인"
        packet = build_packet(prev_digest=digest)
        assert len(packet.completed_event_facts) >= 6

    def test_completed_events_procedural_from_chain_link(self):
        """[Wave2-B] Chain-link procedural lines must also be extracted."""
        chain = "- 계좌 세팅 완료 (ep3)\n- OTP 수령 (ep3)\n- 일반 정보"
        packet = build_packet(chain_link_section=chain)
        assert len(packet.completed_event_facts) >= 2

    def test_completed_events_wave1_investment_no_regression(self):
        """[Wave2-B] Wave 1 investment verbs must not regress."""
        digest = "- 증권 계좌 개설\n- 인프라 구축\n- 2억 이체\n- 투자 계약 체결"
        packet = build_packet(prev_digest=digest)
        assert len(packet.completed_event_facts) >= 4

    def test_chain_link_carryover_fields_are_extracted(self):
        chain = (
            "### [ChainLink Carryover Contract]\n"
            "- carryover_cliffhanger: 전화가 오기 직전 멈칫했다.\n"
            "- carryover_pending_actions: 전화를 받기, 현관으로 이동하기\n"
            "- carryover_location: 서재 앞 복도\n"
            "- carryover_time_marker: 직후"
        )
        packet = build_packet(chain_link_section=chain)
        assert packet.carryover_cliffhanger == "전화가 오기 직전 멈칫했다."
        assert packet.carryover_pending_actions == "전화를 받기, 현관으로 이동하기"
        assert packet.carryover_location == "서재 앞 복도"
        assert packet.carryover_time_marker == "직후"

    def test_chain_link_soft_carryover_fields_are_extracted(self):
        chain = (
            "### [V68-Soft] 직전 화 soft carryover 참고 - 자연 회복/명시적 전환 허용\n"
            "- soft_physical_state: 신경계 피로 Moderate\n"
            "- soft_carryover_pending_actions: 전화를 받기, 현관으로 이동하기"
        )
        packet = build_packet(chain_link_section=chain)
        assert packet.soft_physical_state == "신경계 피로 Moderate"
        assert packet.soft_carryover_pending_actions == "전화를 받기, 현관으로 이동하기"


# ── classify_violation_family ────────────────────────────────────


class TestClassifyViolationFamily:
    def test_opening_anchor_drift(self):
        families = classify_violation_family(rejection_reason="시작 장소 불일치 감지")
        assert VIOLATION_OPENING_ANCHOR_DRIFT in families

    def test_committed_state_regression(self):
        families = classify_violation_family(rejection_reason="자본금 수치 모순: 38억 vs 20억")
        assert VIOLATION_COMMITTED_STATE_REGRESSION in families

    def test_completed_event_replay(self):
        families = classify_violation_family(rejection_reason="이미 완료된 전투를 다시 서술")
        assert VIOLATION_COMPLETED_EVENT_REPLAY in families

    def test_scene_obligation_missing(self):
        families = classify_violation_family(rejection_reason="씬 완성도 부족: 0/5 씬만 완성")
        assert VIOLATION_SCENE_OBLIGATION_MISSING in families

    def test_empty_patch_targets_alone_not_enough(self):
        """Empty patch targets alone should not synthesize a violation family."""
        families = classify_violation_family(rejection_reason="일반 피드백", patch_targets_empty=True)
        assert len(families) == 0

    def test_empty_patch_targets_with_hard_evidence(self):
        """Empty patches + hard fact evidence in rejection reason → classification."""
        families = classify_violation_family(rejection_reason="자본금 수치 모순", patch_targets_empty=True)
        assert VIOLATION_COMMITTED_STATE_REGRESSION in families

    def test_no_families_for_generic_feedback(self):
        families = classify_violation_family(rejection_reason="문체가 다소 약합니다")
        assert len(families) == 0

    def test_fix_pack_heuristic(self):
        families = classify_violation_family(
            rejection_reason="issues found",
            fix_pack={"patch_targets": ["시작 장소 교정"]},
        )
        assert VIOLATION_OPENING_ANCHOR_DRIFT in families

    def test_metadata_reference_shape(self):
        families = classify_violation_family(rejection_reason="unhashable type: 'dict'")
        assert VIOLATION_METADATA_REFERENCE_SHAPE in families


# ── should_escalate_to_rewrite ───────────────────────────────────


class TestShouldEscalateToRewrite:
    def test_hard_fact_plus_empty_patches(self):
        assert should_escalate_to_rewrite(
            violation_families=[VIOLATION_OPENING_ANCHOR_DRIFT],
            patch_targets_empty=True,
        )

    def test_consecutive_empty_patches(self):
        assert should_escalate_to_rewrite(
            violation_families=[],
            consecutive_empty_patches=2,
        )

    def test_rewrite_biased_plus_one_empty(self):
        assert should_escalate_to_rewrite(
            violation_families=[VIOLATION_COMMITTED_STATE_REGRESSION],
            consecutive_empty_patches=1,
        )

    def test_no_escalation_for_local_issues(self):
        assert not should_escalate_to_rewrite(
            violation_families=[VIOLATION_SCENE_OBLIGATION_MISSING],
            patch_targets_empty=False,
            consecutive_empty_patches=0,
        )

    def test_no_escalation_empty_families(self):
        assert not should_escalate_to_rewrite(
            violation_families=[],
            patch_targets_empty=False,
            consecutive_empty_patches=0,
        )


# ── normalize_actor_reference ────────────────────────────────────


class TestNormalizeActorReference:
    def test_string_passthrough(self):
        assert normalize_actor_reference("김철수") == "김철수"

    def test_string_strip(self):
        assert normalize_actor_reference("  김철수  ") == "김철수"

    def test_dict_with_name(self):
        assert normalize_actor_reference({"name": "김철수", "role": "비서"}) == "김철수"

    def test_dict_with_npc(self):
        assert normalize_actor_reference({"npc": "이영희"}) == "이영희"

    def test_dict_with_target(self):
        assert normalize_actor_reference({"target": "박대리"}) == "박대리"

    def test_dict_fallback_first_string(self):
        assert normalize_actor_reference({"role": "비서", "title": "과장"}) == "비서"

    def test_list_first_element(self):
        assert normalize_actor_reference(["김철수", "이영희"]) == "김철수"

    def test_none_returns_empty(self):
        assert normalize_actor_reference(None) == ""

    def test_nested_dict_in_list(self):
        assert normalize_actor_reference([{"name": "김철수"}]) == "김철수"


# ── normalize_relationship_changes ───────────────────────────────


class TestNormalizeRelationshipChanges:
    def test_normal_list(self):
        changes = [{"npc": "김철수", "to": "동맹", "from": "적대"}]
        result = normalize_relationship_changes(changes)
        assert len(result) == 1
        assert result[0] == {"npc": "김철수", "to": "동맹", "from": "적대"}

    def test_dict_npc_scalarized(self):
        changes = [{"npc": {"name": "김철수", "role": "비서"}, "to": "목격자", "from": ""}]
        result = normalize_relationship_changes(changes)
        assert result[0]["npc"] == "김철수"

    def test_dict_to_scalarized(self):
        changes = [{"npc": "김철수", "to": {"status": "목격자", "detail": "직접 봄"}, "from": ""}]
        result = normalize_relationship_changes(changes)
        assert isinstance(result[0]["to"], str)
        assert "목격자" in result[0]["to"]

    def test_empty_npc_filtered(self):
        changes = [{"npc": "", "to": "관계"}]
        result = normalize_relationship_changes(changes)
        assert len(result) == 0

    def test_non_list_returns_empty(self):
        assert normalize_relationship_changes(None) == []
        assert normalize_relationship_changes("not a list") == []

    def test_non_dict_entries_filtered(self):
        changes = [{"npc": "김철수", "to": "동맹"}, "invalid", 123]
        result = normalize_relationship_changes(changes)
        assert len(result) == 1

    def test_target_key_fallback(self):
        changes = [{"target": "이영희", "to": "적대"}]
        result = normalize_relationship_changes(changes)
        assert result[0]["npc"] == "이영희"


# ── render_packet_for_cw ─────────────────────────────────────────


class TestRenderPacketForCW:
    def test_empty_packet_returns_empty(self):
        packet = ImmutableFactPacket()
        assert render_packet_for_cw(packet) == ""

    def test_opening_anchor_rendered(self):
        packet = ImmutableFactPacket(
            start_location="강남 호텔",
            start_time_flow="오전 11시",
            opening_transition_type="explicit_transition",
        )
        rendered = render_packet_for_cw(packet)
        assert "강남 호텔" in rendered
        assert "오전 11시" in rendered
        assert "불변" in rendered
        assert "불합격" in rendered
        assert "opening transition type: explicit_transition" in rendered

    def test_committed_state_facts_rendered(self):
        packet = ImmutableFactPacket(committed_state_facts=["자본금: 38억"])
        rendered = render_packet_for_cw(packet)
        assert "38억" in rendered

    def test_incomplete_metadata_warning(self):
        packet = ImmutableFactPacket(
            start_location="호텔",
            blueprint_metadata_complete=False,
        )
        rendered = render_packet_for_cw(packet)
        assert "불완전" in rendered

    def test_prev_ending_bridge_rendered_with_opening_anchor(self):
        packet = ImmutableFactPacket(
            start_location="서재 앞 복도",
            prev_ending_bridge="서재 앞 복도에서 현관 쪽으로 발을 옮겼다.",
        )
        rendered = render_packet_for_cw(packet)
        assert "직전 화 종료 브리지" in rendered
        assert "현관 쪽으로 발을 옮겼다" in rendered

    def test_chain_link_carryover_rendered_with_opening_anchor(self):
        packet = ImmutableFactPacket(
            start_location="서재 앞 복도",
            carryover_cliffhanger="전화가 오기 직전 멈칫했다.",
            carryover_pending_actions="전화를 받기, 현관으로 이동하기",
            carryover_location="서재 앞 복도",
            carryover_time_marker="직후",
        )
        rendered = render_packet_for_cw(packet)
        assert "carryover cliffhanger to resolve or explicitly transition from: 전화가 오기 직전 멈칫했다." in rendered
        assert "carryover location to honor or explicitly transition from: 서재 앞 복도" in rendered
        assert "carryover time_marker to honor or explicitly advance from: 직후" in rendered
        assert (
            "carryover pending_actions to resolve before new thread or explicitly transition away: "
            "전화를 받기, 현관으로 이동하기"
        ) in rendered
        assert "다른 장소/시간 또는 다른 시점 opening이 필요하면" in rendered
        assert "무전환으로 덮어쓰거나, 직전 화에서 이미 끝난 행동을 opening에서 다시 재연하면 즉시 불합격." in rendered

    def test_soft_chain_link_carryover_renders_as_reference_only(self):
        packet = ImmutableFactPacket(
            start_location="서재 앞 복도",
            soft_carryover_pending_actions="전화를 받기, 현관으로 이동하기",
            soft_physical_state="신경계 피로 Moderate",
        )
        rendered = render_packet_for_cw(packet)
        assert "soft carryover pending_actions reference: 전화를 받기, 현관으로 이동하기" in rendered
        assert "soft physical_state reference: 신경계 피로 Moderate" in rendered
        assert "carryover pending_actions to resolve before new thread or explicitly transition away" not in rendered


# ── render_violation_summary ─────────────────────────────────────


class TestRenderViolationSummary:
    def test_empty(self):
        assert render_violation_summary([]) == ""

    def test_single_family(self):
        summary = render_violation_summary([VIOLATION_OPENING_ANCHOR_DRIFT])
        assert "시작계약위반" in summary

    def test_multiple_families(self):
        summary = render_violation_summary(
            [
                VIOLATION_OPENING_ANCHOR_DRIFT,
                VIOLATION_COMMITTED_STATE_REGRESSION,
            ]
        )
        assert "시작계약위반" in summary
        assert "확정상태회귀" in summary
