"""
[S3-FL/CC/TC] Stage 3 Blueprint State-Precision Reconciliation Guardrail Tests

Tests for:
- Tranche A: Fact-Lock Packet generation and prompt surfacing
- Tranche B: Capital-State Continuity Packet for investment genre
- Tranche C: Prevalidation fact reconciliation (provenance, item-state, capital, temporal-deictic)
"""

from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler
from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator

# ============================================================
# Tranche A: Fact-Lock Packet
# ============================================================


class TestFactLockPacket:
    """Fact-Lock Packet builder extracts settled facts from prior canon."""

    def test_empty_inputs_return_empty_packet(self):
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=None,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        assert result == {}

    def test_location_anchor_from_end_location(self):
        bp = {"end_location": "남궁세가 후원"}
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        location_anchors = [a for a in anchors if a["category"] == "위치"]
        assert len(location_anchors) == 1
        assert "남궁세가 후원" in location_anchors[0]["fact"]

    def test_location_anchor_from_scene_breakdown_fallback(self):
        bp = {
            "scene_breakdown": {
                "scene_1": {"location": "객잔"},
                "scene_3": {"location": "약방"},
                "scene_2": {"location": "시장 거리"},
            }
        }
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        location_anchors = [a for a in anchors if a["category"] == "위치"]
        assert len(location_anchors) == 1
        assert "약방" in location_anchors[0]["fact"]

    def test_time_anchor_from_ending_state_timeline(self):
        bp = {
            "ending_state": {"timeline": {"day": "3일차", "time": "야간"}},
        }
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        time_anchors = [a for a in anchors if a["category"] == "시간"]
        assert len(time_anchors) == 1
        assert "3일차" in time_anchors[0]["fact"]

    def test_time_anchor_falls_back_to_time_flow(self):
        bp = {"time_flow": "해질녘에서 한밤중으로"}
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        time_anchors = [a for a in anchors if a["category"] == "시간"]
        assert len(time_anchors) == 1
        assert "해질녘" in time_anchors[0]["fact"]

    def test_ending_hook_anchor(self):
        bp = {"ending_hook": "그의 눈앞에 나타난 검은 그림자"}
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        hook_anchors = [a for a in anchors if a["category"] == "엔딩훅"]
        assert len(hook_anchors) == 1
        assert "검은 그림자" in hook_anchors[0]["fact"]

    def test_protagonist_equipment_anchor(self):
        bp = {"protagonist_state": {"equipment": ["파천검", "해독환"]}}
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        equip_anchors = [a for a in anchors if a["category"] == "소지품"]
        assert len(equip_anchors) == 1
        assert "파천검" in equip_anchors[0]["fact"]

    def test_protagonist_injury_anchor_skips_none(self):
        bp = {"protagonist_state": {"injuries": "없음"}}
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        injury_anchors = [a for a in anchors if a["category"] == "부상"]
        assert len(injury_anchors) == 0

    def test_protagonist_injury_anchor_present(self):
        bp = {"protagonist_state": {"injuries": "왼팔 골절"}}
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        injury_anchors = [a for a in anchors if a["category"] == "부상"]
        assert len(injury_anchors) == 1
        assert "왼팔 골절" in injury_anchors[0]["fact"]

    def test_manuscript_item_storage_extraction(self):
        ms = "그는 비급을 금고에 넣었다. 이제 안전하다고 생각했다."
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint={},
            prev_manuscript_ending=ms,
            arc_data={},
            ep_num=2,
        )
        anchors = result.get("anchors", [])
        item_anchors = [a for a in anchors if a["category"] == "아이템위치"]
        assert len(item_anchors) >= 1
        assert any("비급" in a["fact"] and "금고" in a["fact"] for a in item_anchors)

    def test_compile_includes_fact_lock_in_block(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={"ep_start": 1, "ep_count": 5, "arc_no": 1, "tactical_doc": "제1화: 시작"},
            ep_num=2,
            prev_blueprint={"end_location": "객잔 2층"},
        )
        assert "fact_lock_packet" in block
        assert isinstance(block["fact_lock_packet"], dict)

    def test_compile_to_prompt_includes_fact_lock_section(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={"ep_start": 1, "ep_count": 5, "arc_no": 1, "tactical_doc": "제2화: 전개"},
            ep_num=2,
            prev_blueprint={"end_location": "남궁세가", "ending_hook": "어둠 속 그림자"},
        )
        prompt = compiler.compile_to_prompt(block)
        assert "FACT-LOCK" in prompt
        assert "남궁세가" in prompt

    def test_fact_lock_packet_merges_arc_and_prior_institution_truth(self):
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint={
                "integrated_scenario": "그는 대한그룹 회장의 서재에서 차갑게 통보를 들었다.",
            },
            prev_manuscript_ending="그는 은행 PB센터에서 마지막 서류를 정리했다.",
            arc_data={
                "state_constraints": {
                    "arc_start_state": {
                        "relationship": "대한그룹 한정호 회장의 막내아들",
                    }
                },
                "tactical_doc": "### 제 3화: 강남 PB센터와 법무법인을 오간다.",
            },
            ep_num=3,
        )

        institution_facts = [anchor["fact"] for anchor in result.get("anchors", []) if anchor.get("category") == "기관"]
        assert any("대한그룹" in fact for fact in institution_facts)
        assert any("PB센터" in fact for fact in institution_facts)

    def test_compile_to_prompt_includes_episode_progression_guard(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={
                "ep_start": 1,
                "ep_count": 4,
                "arc_no": 1,
                "tactical_doc": (
                    "### 제 3화: 씨앗을 심는 법\n"
                    "다음 날부터 그는 대한그룹의 법률 자문이 아닌 바깥 변호사를 만나 법인 설립을 진행하고 "
                    "PB센터에서 자산 현금화를 요청한다."
                ),
                "state_changes": {
                    "timeline": {
                        "start": {"year": 2006, "month": 1},
                        "end": {"year": 2006, "month": 1},
                    }
                },
            },
            ep_num=3,
            prev_blueprint={
                "time_flow": "2006년 1월, 다음 날 저녁",
                "scene_breakdown": {
                    "scene_2": {
                        "title": "독립 선언",
                        "location": "한정호 회장의 서재",
                        "characters": ["한시우", "한정호"],
                        "type": "dialogue_duel",
                    },
                    "scene_4": {
                        "title": "전장의 서막",
                        "location": "한시우의 방",
                        "characters": ["한시우"],
                        "type": "cliffhanger",
                    },
                },
            },
        )

        prompt = compiler.compile_to_prompt(block)
        assert "EPISODE PROGRESSION" in prompt
        assert "대한그룹" in prompt
        assert "겨울" in prompt
        assert "한정호 회장의 서재" in prompt

    def test_anchor_count_bounded_to_12(self):
        """Packet should not exceed 12 anchors even with many manuscript matches."""
        # Create manuscript with many item storage patterns
        ms = " ".join(f"그는 물건{i}을 장소{i}에 넣었다." for i in range(20))
        bp = {
            "end_location": "A",
            "time_flow": "T",
            "ending_hook": "H",
            "protagonist_state": {"equipment": ["E"], "injuries": "I"},
        }
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending=ms,
            arc_data={},
            ep_num=2,
        )
        assert len(result.get("anchors", [])) <= 12


# ============================================================
# Tranche A2: Opening-State Authority
# ============================================================


class TestOpeningStateAuthority:
    """Current-arc opening authority must outrank stale prior-blueprint state."""

    def test_compile_prefers_arc_start_state_over_stale_prev_blueprint(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={
                "ep_start": 11,
                "ep_count": 3,
                "arc_no": 3,
                "tactical_doc": "제11화: 개장 직전 브리핑",
                "state_constraints": {
                    "arc_start_state": {
                        "location": "Gangnam HQ",
                        "equipment": ["BlackBerry 7130", "Ecuador memo"],
                        "injuries": "없음",
                    }
                },
            },
            ep_num=11,
            prev_blueprint={
                "end_location": "Old Office",
                "scene_breakdown": {
                    "scene_1": {
                        "location": "Old Office",
                        "characters": ["대표", "비서"],
                    }
                },
                "protagonist_state": {
                    "equipment": ["Stale pager"],
                    "injuries": "왼팔 타박상",
                },
            },
        )

        assert block["continuity"]["location"] == "Gangnam HQ"
        assert block["inherited_state"]["equipment"] == ["BlackBerry 7130", "Ecuador memo"]
        assert block["inherited_state"]["injuries"] == "없음"

    def test_compile_prefers_prev_blueprint_state_within_arc(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={
                "ep_start": 7,
                "ep_count": 6,
                "arc_no": 2,
                "tactical_doc": "제9화: 포지션 진입",
                "state_constraints": {
                    "arc_start_state": {
                        "location": "본가 개인 서재",
                        "equipment": ["BlackBerry 7130", "Ecuador memo"],
                        "injuries": "없음",
                    }
                },
            },
            ep_num=9,
            prev_blueprint={
                "end_location": "한미증권 청담동 지점 15층 VIP룸",
                "scene_breakdown": {
                    "scene_4": {
                        "location": "한미증권 청담동 지점 15층 VIP룸",
                        "characters": ["한시우", "박성호"],
                    }
                },
                "protagonist_state": {
                    "equipment": ["가죽 서류가방", "WTI 포지션 주문표"],
                    "injuries": "오른손 타박상",
                },
            },
        )

        assert block["continuity"]["location"] == "한미증권 청담동 지점 15층 VIP룸"
        assert block["inherited_state"]["equipment"] == ["가죽 서류가방", "WTI 포지션 주문표"]
        assert block["inherited_state"]["injuries"] == "오른손 타박상"


# ============================================================
# Tranche B: Capital-State Continuity Packet
# ============================================================


class TestCapitalContinuityPacket:
    """Capital continuity packet only activates for investment genre."""

    def test_non_investment_genre_returns_empty(self):
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint={"ending_state": {"balance": "1억"}},
            prev_manuscript_ending="",
            arc_data={},
            genre="wuxia",
        )
        assert result == {}

    def test_investment_genre_extracts_balance(self):
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint={"ending_state": {"balance": "1억 2천만원"}},
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        assert len(fields) >= 1
        assert any("잔고" in f["label"] or "자본" in f["label"] for f in fields)

    def test_investment_genre_extracts_protagonist_capital(self):
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint={"protagonist_state": {"capital": "5천만원 잔여"}},
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        assert any("자본" in f["label"] for f in fields)

    def test_investment_genre_extracts_from_state_changes(self):
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint={},
            prev_manuscript_ending="",
            arc_data={
                "state_changes": {
                    "capital_changes": [
                        {"description": "삼성전자 매수", "amount": "3천만원"},
                    ]
                }
            },
            genre="investment",
        )
        fields = result.get("fields", [])
        assert len(fields) >= 1
        assert any("삼성전자" in f["value"] for f in fields)

    def test_investment_genre_manuscript_capital_extraction(self):
        ms = "그는 5000만원을 투자했다."
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint={},
            prev_manuscript_ending=ms,
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        assert any("투자" in f["label"] for f in fields)

    def test_deduplicates_by_label(self):
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint={
                "ending_state": {"balance": "1억"},
                "protagonist_state": {"balance": "1억"},
            },
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        labels = [f["label"] for f in fields]
        assert len(labels) == len(set(labels)), "Duplicate labels should be removed"

    def test_compile_includes_capital_continuity(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={"ep_start": 1, "ep_count": 5, "arc_no": 1, "tactical_doc": "제2화"},
            ep_num=2,
            prev_blueprint={"ending_state": {"balance": "1억"}},
            genre="investment",
        )
        assert "capital_continuity_packet" in block

    def test_compile_filters_future_capital_events_by_episode(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={
                "ep_start": 11,
                "ep_count": 3,
                "arc_no": 3,
                "tactical_doc": "제11화: 포지션 점검",
                "state_changes": {
                    "capital_changes": [
                        {"episode": 12, "description": "차익 실현", "amount": "5억"},
                        {"episode": 11, "description": "WTI 포지션 유지", "amount": "12.5억"},
                    ]
                },
            },
            ep_num=11,
            prev_blueprint={},
            genre="investment",
        )

        fields = block.get("capital_continuity_packet", {}).get("fields", [])
        values = [field.get("value", "") for field in fields]
        assert any("WTI 포지션 유지" in value for value in values)
        assert not any("차익 실현" in value for value in values)


# ============================================================
# Tranche C: Prevalidation Fact Reconciliation
# ============================================================


class TestFactLockDriftDetection:
    """Prevalidation detects fact-lock violations in candidate blueprints."""

    def test_no_issues_when_no_fact_lock(self):
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated="some text",
            constraint_block={},
        )
        assert issues == []

    def test_location_drift_detected(self):
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "위치", "fact": "직전 종료 위치: 남궁세가 후원"},
                ]
            }
        }
        blueprint = {"start_location": "화산파 연무장"}
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint=blueprint,
            integrated="화산파 연무장에서 시작하여...",
            constraint_block=constraint_block,
        )
        location_issues = [i for i in issues if i["category"] == "fact_lock_location"]
        assert len(location_issues) >= 1
        assert location_issues[0]["severity"] == "MAJOR"

    def test_location_no_false_positive_same_area(self):
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "위치", "fact": "직전 종료 위치: 남궁세가 후원"},
                ]
            }
        }
        blueprint = {"start_location": "남궁세가 정원"}
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint=blueprint,
            integrated="남궁세가 정원에서...",
            constraint_block=constraint_block,
        )
        location_issues = [i for i in issues if i["category"] == "fact_lock_location"]
        assert len(location_issues) == 0, "Same area prefix should not trigger"

    def test_item_storage_drift_detected(self):
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "아이템위치", "fact": "원고 확정: '비급' → '금고'에 보관/배치"},
                ]
            }
        }
        integrated = "주인공은 비급을 서랍에서 꺼내어 읽기 시작했다."
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated=integrated,
            constraint_block=constraint_block,
        )
        item_issues = [i for i in issues if i["category"] == "fact_lock_item"]
        assert len(item_issues) >= 1

    def test_item_storage_no_issue_when_correct_location(self):
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "아이템위치", "fact": "원고 확정: '비급' → '금고'에 보관/배치"},
                ]
            }
        }
        integrated = "주인공은 금고에서 비급을 꺼내어 읽기 시작했다."
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated=integrated,
            constraint_block=constraint_block,
        )
        item_issues = [i for i in issues if i["category"] == "fact_lock_item"]
        assert len(item_issues) == 0

    def test_provenance_drift_trust_flip(self):
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "엔딩훅", "fact": "직전 화 엔딩: 그녀에 대한 의심이 깊어졌다"},
                ]
            }
        }
        integrated = "깊은 신뢰를 바탕으로 그녀와 함께 길을 나섰다. " + "x" * 500
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated=integrated,
            constraint_block=constraint_block,
        )
        provenance_issues = [i for i in issues if i["category"] == "fact_lock_provenance"]
        assert len(provenance_issues) >= 1
        assert provenance_issues[0]["severity"] == "CRITICAL"

    def test_bounded_output(self):
        """Should not return more than 6 issues (expanded for institution drift)."""
        anchors = [{"category": "위치", "fact": f"직전 종료 위치: 장소{i}"} for i in range(10)]
        constraint_block = {"fact_lock_packet": {"anchors": anchors}}
        blueprint = {"start_location": "완전다른곳"}
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint=blueprint,
            integrated="x" * 100,
            constraint_block=constraint_block,
        )
        assert len(issues) <= 6


class TestCapitalStateDriftDetection:
    """Prevalidation catches capital/deployment contradictions."""

    def test_no_issues_when_no_capital_packet(self):
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated="아직 여유 자금이 있다",
            constraint_block={},
        )
        assert issues == []

    def test_detects_stale_availability_language(self):
        constraint_block = {"capital_continuity_packet": {"fields": [{"label": "잔고", "value": "이미 전액 투입"}]}}
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated="아직 여유 자금이 남아 있어 추가 투자를 고려했다.",
            constraint_block=constraint_block,
        )
        assert len(issues) >= 1
        assert issues[0]["severity"] == "CRITICAL"

    def test_detects_fresh_deploy_language(self):
        constraint_block = {
            "capital_continuity_packet": {"fields": [{"label": "투입 상태", "value": "전액 투입 완료"}]}
        }
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated="새로 투자할 종목을 찾기 시작했다.",
            constraint_block=constraint_block,
        )
        assert len(issues) >= 1

    def test_no_false_positive_without_contradiction(self):
        constraint_block = {"capital_continuity_packet": {"fields": [{"label": "잔고", "value": "5천만원"}]}}
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated="기존 포지션을 유지하며 시장을 관망했다.",
            constraint_block=constraint_block,
        )
        assert len(issues) == 0


class TestTemporalDeicticDriftDetection:
    """Prevalidation catches temporal-deictic ending-hook drift."""

    def test_no_issues_without_ending_hook(self):
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={},
        )
        assert issues == []

    def test_detects_large_temporal_offset_in_ending_hook(self):
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={"ending_hook": "18년 전의 기억이 떠올랐다"},
        )
        assert len(issues) >= 1
        assert issues[0]["category"] == "temporal_deictic"

    def test_ignores_small_temporal_offset(self):
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={"ending_hook": "3일 전 일을 떠올리며"},
        )
        assert len(issues) == 0

    def test_detects_future_memory_in_scenario_tail(self):
        scenario = "x" * 1000 + "그때 20년 전의 기억이 떠올렸다."
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={"integrated_scenario": scenario},
        )
        temporal_issues = [i for i in issues if i["category"] == "temporal_deictic"]
        assert len(temporal_issues) >= 1

    def test_allows_canonical_regressor_memory_anchor_from_arc_truth(self):
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={"ending_hook": "18년 후의 기억이 다시 떠올랐다"},
            arc_data={
                "constraint_summary": "주인공은 회귀자이며 18년 후의 기억을 투자 판단의 근거로 사용한다.",
                "bible_root": {"protagonist_config": {"incarnation_type": "회귀자"}},
            },
            constraint_block={"arc_constraint_summary": "18년 후의 기억은 정본 continuity anchor다."},
        )
        assert issues == []

    def test_regressor_identity_alone_does_not_allow_mismatched_large_temporal_offset(self):
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={"ending_hook": "99년 후의 기억이 떠올랐다"},
            arc_data={
                "constraint_summary": "주인공은 회귀자이며 18년 후의 기억을 투자 판단의 근거로 사용한다.",
                "bible_root": {"protagonist_config": {"incarnation_type": "회귀자"}},
            },
            constraint_block={"arc_constraint_summary": "18년 후의 기억은 정본 continuity anchor다."},
        )
        assert any(issue["category"] == "temporal_deictic" for issue in issues)

    def test_still_flags_unanchored_large_temporal_offset_without_arc_truth(self):
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={"ending_hook": "12년 후의 진실이 떠올랐다"},
            arc_data={"bible_root": {"protagonist_config": {"incarnation_type": "일반"}}},
            constraint_block={"arc_constraint_summary": "현재 화는 일반 스릴러 플롯이다."},
        )
        assert any(issue["category"] == "temporal_deictic" for issue in issues)

    def test_no_issue_for_normal_ending_hook(self):
        issues = UnifiedBlueprintValidator._collect_temporal_deictic_drift_issues(
            blueprint={"ending_hook": "그의 눈앞에 검은 그림자가 나타났다"},
        )
        assert len(issues) == 0


class TestIntegrationPrevalidate:
    """Full prevalidation pipeline includes new fact-reconciliation checks."""

    def _make_validator(self):
        """Create a minimal validator with no real LLM client."""

        class FakeContext:
            pass

        return UnifiedBlueprintValidator(FakeContext(), None, "test-model")

    def test_prevalidate_catches_provenance_drift(self):
        validator = self._make_validator()
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "엔딩훅", "fact": "직전 화 엔딩: 그에 대한 불신이 극에 달했다"},
                ]
            },
            "stop_line": {},
        }
        blueprint = {
            "scene_breakdown": {"s1": {"goal": "a"}, "s2": {"goal": "b"}, "s3": {"goal": "c"}},
            "integrated_scenario": "깊은 신뢰를 바탕으로 함께 나섰다. " + "x" * 1000,
        }
        result = validator._python_pre_validate(blueprint, constraint_block, None)
        categories = [i["category"] for i in result["issues"]]
        assert "fact_lock_provenance" in categories

    def test_prevalidate_catches_temporal_deictic(self):
        validator = self._make_validator()
        blueprint = {
            "scene_breakdown": {"s1": {"goal": "a"}, "s2": {"goal": "b"}, "s3": {"goal": "c"}},
            "integrated_scenario": "x" * 1000,
            "ending_hook": "25년 전의 비밀이 밝혀지려 한다",
        }
        result = validator._python_pre_validate(blueprint, {}, None)
        categories = [i["category"] for i in result["issues"]]
        assert "temporal_deictic" in categories

    def test_prevalidate_no_spurious_issues_for_clean_blueprint(self):
        validator = self._make_validator()
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "위치", "fact": "직전 종료 위치: 객잔"},
                ]
            },
            "stop_line": {},
        }
        blueprint = {
            "scene_breakdown": {"s1": {"goal": "a"}, "s2": {"goal": "b"}, "s3": {"goal": "c"}},
            "integrated_scenario": "객잔에서 아침을 맞이한 주인공은 " + "x" * 1000,
            "start_location": "객잔",
            "ending_hook": "다음 여정을 준비하며",
        }
        result = validator._python_pre_validate(blueprint, constraint_block, None)
        # Should have no fact-lock related issues
        fl_issues = [i for i in result["issues"] if i["category"].startswith("fact_lock")]
        assert len(fl_issues) == 0
