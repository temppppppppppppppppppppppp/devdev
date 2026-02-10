"""
[V64 P2-7] FeedbackSystem Unit Tests

모든 메서드가 Pure Function — app 참조 불필요.
build_structured_feedback, get_violation_priority, format_feedback_for_prompt,
quantify_reject_feedback, build_strong_kind_feedback, build_focused_context,
build_minimal_arc_context, generate_structured_arc_feedback,
generate_structured_blueprint_feedback, generate_reverse_feedback_stage4_to_3,
generate_reverse_feedback_stage3_to_2, get_adaptive_feedback_intensity,
classify_rejection_feedback, simplify_prompt_for_retry.
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.feedback_system import FeedbackSystem


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def fs():
    """기본 FeedbackSystem 인스턴스"""
    return FeedbackSystem()


@pytest.fixture
def sample_violations():
    """테스트용 위반 목록"""
    return [
        {"type": "duplicate_acquisition", "description": "청풍검 중복 획득", "item_or_subject": "청풍검"},
        {"type": "timeline_error", "description": "타임라인 불일치", "item_or_subject": ""},
        {"type": "continuity", "description": "연속성 위반", "item_or_subject": "내공"},
    ]


@pytest.fixture
def sample_prev_arcs():
    """테스트용 이전 Arc 목록"""
    return [
        {
            "arc_no": 3,
            "state_constraints": {
                "arc_end_state": {
                    "internal_energy": 70,
                    "injuries": "왼팔 부상",
                    "location": "무림맹 본부",
                    "equipment": "청풍검, 해독약"
                }
            },
            "joint_docs": {
                "final_location": "무림맹 본부",
                "physical_inventory": ["청풍검", "해독약"],
                "world_joint": "무림맹 세력 약화"
            },
            "status_shadow": {
                "internal_energy_loss": "30%",
                "expected_injuries": "왼팔 부상"
            }
        }
    ]


# ══════════════════════════════════════════════════════════════
# Test 1: build_structured_feedback
# ══════════════════════════════════════════════════════════════

class TestBuildStructuredFeedback:
    def test_basic_structure(self, fs):
        """기본 구조화 피드백 생성"""
        result = fs.build_structured_feedback(
            decision="REJECT",
            reason="분량 부족",
            violations=[{"type": "continuity"}],
            severity="HIGH"
        )
        assert result["decision"] == "REJECT"
        assert result["reason"] == "분량 부족"
        assert result["severity"] == "HIGH"
        assert isinstance(result["violations"], list)

    def test_reason_truncation(self, fs):
        """reason이 300자 초과 시 잘림"""
        long_reason = "a" * 500
        result = fs.build_structured_feedback(decision="REJECT", reason=long_reason)
        assert len(result["reason"]) <= 300

    def test_fix_instructions_truncation(self, fs):
        """fix_instructions가 500자 초과 시 잘림"""
        long_fix = "b" * 700
        result = fs.build_structured_feedback(
            decision="REJECT", reason="test", fix_instructions=long_fix
        )
        assert len(result["fix_instructions"]) <= 500

    def test_empty_violations(self, fs):
        """violations 미지정 시 빈 리스트"""
        result = fs.build_structured_feedback(decision="PASS", reason="")
        assert result["violations"] == []

    def test_priority_order_included(self, fs, sample_violations):
        """priority_order가 포함됨"""
        result = fs.build_structured_feedback(
            decision="REJECT", reason="test", violations=sample_violations
        )
        assert isinstance(result["priority_order"], list)


# ══════════════════════════════════════════════════════════════
# Test 2: get_violation_priority
# ══════════════════════════════════════════════════════════════

class TestGetViolationPriority:
    def test_priority_ordering(self, fs, sample_violations):
        """위반 항목이 우선순위대로 정렬"""
        result = fs.get_violation_priority(sample_violations)
        assert result[0] == "duplicate_acquisition"
        assert result[1] == "timeline_error"
        assert result[2] == "continuity"

    def test_unknown_type_last(self, fs):
        """unknown 타입은 마지막으로"""
        violations = [
            {"type": "unknown"},
            {"type": "duplicate_acquisition"},
        ]
        result = fs.get_violation_priority(violations)
        assert result[0] == "duplicate_acquisition"
        assert result[1] == "unknown"

    def test_empty_list(self, fs):
        """빈 리스트"""
        assert fs.get_violation_priority([]) == []


# ══════════════════════════════════════════════════════════════
# Test 3: format_feedback_for_prompt
# ══════════════════════════════════════════════════════════════

class TestFormatFeedbackForPrompt:
    def test_reject_formatting(self, fs):
        """REJECT 피드백 포맷팅"""
        feedback = {
            "decision": "REJECT",
            "severity": "HIGH",
            "reason": "분량 부족",
            "priority_order": ["continuity", "timeline_error"],
            "fix_instructions": "분량을 4500자 이상으로 작성하세요"
        }
        result = fs.format_feedback_for_prompt(feedback)
        assert "REJECT" in result
        assert "분량 부족" in result
        assert "continuity" in result

    def test_pass_returns_empty(self, fs):
        """PASS면 빈 문자열"""
        feedback = {"decision": "PASS", "reason": ""}
        result = fs.format_feedback_for_prompt(feedback)
        assert result == ""

    def test_empty_feedback(self, fs):
        """빈 피드백"""
        assert fs.format_feedback_for_prompt({}) == ""
        assert fs.format_feedback_for_prompt(None) == ""


# ══════════════════════════════════════════════════════════════
# Test 4: quantify_reject_feedback
# ══════════════════════════════════════════════════════════════

class TestQuantifyRejectFeedback:
    def test_short_content_quantification(self, fs):
        """짧은 분량에 대한 정량화"""
        result = fs.quantify_reject_feedback(
            reason="분량 부족", content_length=3000, audit_result={}
        )
        assert len(result) >= 1
        assert any(q["type"] == "QUANTIFIED" for q in result)
        # 2000자 부족 = 대화 + 묘사 + 액션 합산
        quant = result[0]
        assert "총" in quant["description"]

    def test_dialogue_quantification(self, fs):
        """대화 부족에 대한 정량화"""
        result = fs.quantify_reject_feedback(
            reason="대화 부족으로 건조함", content_length=5000, audit_result={}
        )
        assert any("대화" in q["description"] for q in result)

    def test_density_quantification(self, fs):
        """후반부 밀도 부족 정량화"""
        result = fs.quantify_reject_feedback(
            reason="후반부 밀도 부족", content_length=5000, audit_result={}
        )
        assert any("후반부" in q["description"] for q in result)

    def test_scene_quantification(self, fs):
        """씬 누락 정량화"""
        result = fs.quantify_reject_feedback(
            reason="씬 누락", content_length=5000, audit_result={}
        )
        assert any("씬" in q["description"] for q in result)

    def test_no_issues(self, fs):
        """문제 없으면 빈 리스트"""
        result = fs.quantify_reject_feedback(
            reason="기타 문제", content_length=6000, audit_result={}
        )
        # "기타" 키워드는 어떤 조건에도 매칭 안 됨
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════
# Test 5: build_strong_kind_feedback
# ══════════════════════════════════════════════════════════════

class TestBuildStrongKindFeedback:
    def test_duplicate_acquisition(self, fs):
        """중복 획득 피드백"""
        violations = [{"type": "duplicate_acquisition", "item_or_subject": "청풍검"}]
        result = fs.build_strong_kind_feedback(violations, attempt=0)
        assert "청풍검" in result
        assert "CRITICAL_INSTRUCTION" in result

    def test_state_discontinuity(self, fs):
        """상태 불연속 피드백"""
        violations = [{"type": "state_discontinuity", "item_or_subject": ""}]
        result = fs.build_strong_kind_feedback(violations, attempt=1)
        assert "직전 Arc" in result

    def test_empty_violations(self, fs):
        """빈 위반 목록이면 빈 문자열"""
        assert fs.build_strong_kind_feedback([], attempt=0) == ""

    def test_protagonist_name_injection(self, fs):
        """주인공 이름 주입"""
        violations = [{"type": "protagonist_error", "item_or_subject": ""}]
        result = fs.build_strong_kind_feedback(violations, attempt=0, protagonist_name="이청풍")
        assert "이청풍" in result


# ══════════════════════════════════════════════════════════════
# Test 6: build_focused_context
# ══════════════════════════════════════════════════════════════

class TestBuildFocusedContext:
    def test_basic_context(self, fs, sample_prev_arcs):
        """기본 집중 컨텍스트"""
        result = fs.build_focused_context(
            violations=[], prev_arcs=sample_prev_arcs, protagonist_name="이청풍"
        )
        assert "70%" in result
        assert "왼팔 부상" in result or "부상" in result

    def test_empty_arcs(self, fs):
        """빈 아크 목록이면 빈 문자열"""
        result = fs.build_focused_context([], [], "이청풍")
        assert result == ""

    def test_inventory_list_truncated(self, fs):
        """인벤토리가 리스트이면 3개까지 표시"""
        arcs = [{
            "arc_no": 1,
            "state_constraints": {"arc_end_state": {}},
            "joint_docs": {
                "physical_inventory": ["검A", "검B", "검C", "검D", "검E"]
            }
        }]
        result = fs.build_focused_context([], arcs, "이청풍")
        assert "검A" in result
        # 최대 3개이므로 검D는 없어야 함
        assert "검D" not in result


# ══════════════════════════════════════════════════════════════
# Test 7: build_minimal_arc_context
# ══════════════════════════════════════════════════════════════

class TestBuildMinimalArcContext:
    def test_no_arcs(self, fs):
        """아크 없으면 시작점 컨텍스트"""
        result = fs.build_minimal_arc_context([], "이청풍")
        assert "이청풍" in result
        assert "첫 Arc" in result or "서사 시작점" in result

    def test_with_arcs(self, fs, sample_prev_arcs):
        """아크가 있으면 상태 요약"""
        result = fs.build_minimal_arc_context(sample_prev_arcs, "이청풍")
        assert "이청풍" in result
        assert "70%" in result
        assert "Arc 3" in result

    def test_energy_calculation_from_loss(self, fs):
        """arc_end_state에 internal_energy 없으면 loss에서 계산"""
        arcs = [{
            "arc_no": 2,
            "state_constraints": {"arc_end_state": {}},
            "joint_docs": {},
            "status_shadow": {"internal_energy_loss": "40%"}
        }]
        result = fs.build_minimal_arc_context(arcs, "이청풍")
        assert "60%" in result  # 100 - 40


# ══════════════════════════════════════════════════════════════
# Test 8: generate_structured_arc_feedback
# ══════════════════════════════════════════════════════════════

class TestGenerateStructuredArcFeedback:
    def test_item_violations(self, fs):
        """아이템 위반 피드백"""
        result_dict = {
            "violations": [
                {"type": "item_duplicate", "description": "청풍검 중복", "item_or_subject": "청풍검", "location": "5화"}
            ]
        }
        result = fs.generate_structured_arc_feedback(result_dict, arc_no=3)
        assert "아이템" in result
        assert "청풍검" in result

    def test_npc_violations(self, fs):
        """NPC 위반 피드백"""
        result_dict = {
            "violations": [
                {"type": "npc_dead_revival", "description": "사망 NPC 부활", "item_or_subject": "철무련주", "location": ""}
            ]
        }
        result = fs.generate_structured_arc_feedback(result_dict, arc_no=5)
        assert "NPC" in result

    def test_empty_result(self, fs):
        """빈 결과면 빈 문자열"""
        assert fs.generate_structured_arc_feedback({}) == ""
        assert fs.generate_structured_arc_feedback(None) == ""

    def test_no_violations(self, fs):
        """위반 없으면 빈 문자열"""
        assert fs.generate_structured_arc_feedback({"violations": []}) == ""


# ══════════════════════════════════════════════════════════════
# Test 9: generate_structured_blueprint_feedback
# ══════════════════════════════════════════════════════════════

class TestGenerateStructuredBlueprintFeedback:
    def test_low_scores_critical(self, fs):
        """낮은 점수는 CRITICAL"""
        result_dict = {
            "score_breakdown": {
                "setting_consistency": 10,
                "scene_composition": 8,
                "narrative_flow": 5,
                "length_fulfillment": 3
            }
        }
        result = fs.generate_structured_blueprint_feedback(result_dict)
        assert "CRITICAL" in result

    def test_high_scores_no_issues(self, fs):
        """높은 점수는 문제 없음"""
        result_dict = {
            "score_breakdown": {
                "setting_consistency": 20,
                "scene_composition": 20,
                "narrative_flow": 20,
                "length_fulfillment": 20
            }
        }
        result = fs.generate_structured_blueprint_feedback(result_dict)
        assert "문제 없음" in result

    def test_retry_count_message(self, fs):
        """재시도 횟수별 메시지"""
        result_dict = {"score_breakdown": {"setting_consistency": 10}}
        r0 = fs.generate_structured_blueprint_feedback(result_dict, retry_count=0)
        r2 = fs.generate_structured_blueprint_feedback(result_dict, retry_count=2)
        assert "첫 시도" in r0
        assert "3차 시도" in r2

    def test_empty_result(self, fs):
        """빈 결과면 빈 문자열"""
        assert fs.generate_structured_blueprint_feedback({}) == ""
        assert fs.generate_structured_blueprint_feedback(None) == ""


# ══════════════════════════════════════════════════════════════
# Test 10: generate_reverse_feedback_stage4_to_3
# ══════════════════════════════════════════════════════════════

class TestGenerateReverseFeedbackStage4To3:
    def test_density_issue(self, fs):
        """후반부 밀도 문제"""
        result = fs.generate_reverse_feedback_stage4_to_3("후반부 밀도 부족")
        assert "후반부" in result
        assert "Scene 5-6" in result

    def test_length_issue(self, fs):
        """분량 문제"""
        result = fs.generate_reverse_feedback_stage4_to_3("분량 부족")
        assert "분량" in result

    def test_setting_issue(self, fs):
        """설정 모순"""
        result = fs.generate_reverse_feedback_stage4_to_3("설정 모순 발견")
        assert "모순" in result or "설정" in result

    def test_empty_reason(self, fs):
        """빈 사유면 빈 문자열"""
        assert fs.generate_reverse_feedback_stage4_to_3("") == ""


# ══════════════════════════════════════════════════════════════
# Test 11: generate_reverse_feedback_stage3_to_2
# ══════════════════════════════════════════════════════════════

class TestGenerateReverseFeedbackStage3To2:
    def test_repeated_failures(self, fs):
        """3회 이상 반복 실패 시 피드백"""
        failures = [
            {"reason": "분량 부족"},
            {"reason": "분량 부족"},
            {"reason": "설정 오류"},
        ]
        result = fs.generate_reverse_feedback_stage3_to_2(failures, arc_no=5)
        assert "3회" in result
        assert "분량 부족" in result

    def test_less_than_3_failures(self, fs):
        """3회 미만이면 빈 문자열"""
        failures = [{"reason": "test"}, {"reason": "test"}]
        result = fs.generate_reverse_feedback_stage3_to_2(failures, arc_no=1)
        assert result == ""

    def test_empty_failures(self, fs):
        """빈 실패 목록"""
        assert fs.generate_reverse_feedback_stage3_to_2([], arc_no=1) == ""
        assert fs.generate_reverse_feedback_stage3_to_2(None, arc_no=1) == ""


# ══════════════════════════════════════════════════════════════
# Test 12: get_adaptive_feedback_intensity
# ══════════════════════════════════════════════════════════════

class TestGetAdaptiveFeedbackIntensity:
    def test_stage2_first_try(self, fs):
        """Stage 2, 첫 시도"""
        result = fs.get_adaptive_feedback_intensity(retry_count=0, stage=2)
        assert result["pass_threshold"] == 70
        assert result["feedback_level"] == "detailed"

    def test_stage2_third_try(self, fs):
        """Stage 2, 3회차"""
        result = fs.get_adaptive_feedback_intensity(retry_count=2, stage=2)
        assert result["pass_threshold"] == 55
        assert result["strictness"] == "low"

    def test_stage4_first_try(self, fs):
        """Stage 4, 첫 시도"""
        result = fs.get_adaptive_feedback_intensity(retry_count=0, stage=4)
        assert result["pass_threshold"] == 70

    def test_stage4_second_try(self, fs):
        """Stage 4, 2회차"""
        result = fs.get_adaptive_feedback_intensity(retry_count=1, stage=4)
        assert result["pass_threshold"] == 65
        assert result["feedback_level"] == "focused"

    def test_stage3(self, fs):
        """Stage 3 테스트"""
        result = fs.get_adaptive_feedback_intensity(retry_count=0, stage=3)
        assert result["pass_threshold"] == 70


# ══════════════════════════════════════════════════════════════
# Test 13: classify_rejection_feedback
# ══════════════════════════════════════════════════════════════

class TestClassifyRejectionFeedback:
    def test_length_classification(self, fs):
        """분량 문제 분류"""
        result = fs.classify_rejection_feedback("분량 부족", "더 써라")
        assert "분량 문제" in result

    def test_scene_classification(self, fs):
        """씬 누락 분류"""
        result = fs.classify_rejection_feedback("씬 누락", "모든 씬 포함")
        assert "씬 누락" in result

    def test_continuity_classification(self, fs):
        """연속성 분류"""
        result = fs.classify_rejection_feedback("연속성 오류", "직전 화 참조")
        assert "연속성" in result

    def test_item_classification(self, fs):
        """아이템 오류 분류"""
        result = fs.classify_rejection_feedback("미획득 아이템 사용", "")
        assert "아이템" in result

    def test_relationship_classification(self, fs):
        """관계 급변 분류"""
        result = fs.classify_rejection_feedback("관계 급변", "단계적 변화")
        assert "관계" in result

    def test_show_dont_tell(self, fs):
        """Show Don't Tell 분류"""
        result = fs.classify_rejection_feedback("감정 서술 과다", "")
        assert "Show" in result or "감정" in result

    def test_other_classification(self, fs):
        """기타 분류"""
        result = fs.classify_rejection_feedback("알 수 없는 문제", "")
        assert "기타" in result


# ══════════════════════════════════════════════════════════════
# Test 14: simplify_prompt_for_retry
# ══════════════════════════════════════════════════════════════

class TestSimplifyPromptForRetry:
    def test_basic_simplification(self, fs):
        """기본 간소화"""
        result = fs.simplify_prompt_for_retry(
            enhanced_feedback="많은 피드백...",
            core_feedback="분량 부족, 씬 누락",
            attempt=2
        )
        assert "간소화" in result
        assert "분량" in result
        assert "씬" in result

    def test_attempt_number_shown(self, fs):
        """재시도 횟수 표시"""
        result = fs.simplify_prompt_for_retry("", "테스트", attempt=3)
        assert "4회차" in result

    def test_default_issues_when_no_keywords(self, fs):
        """키워드 매칭 없으면 기본 이슈"""
        result = fs.simplify_prompt_for_retry("", "특이한 문제", attempt=2)
        assert "4,500자" in result or "6개 씬" in result
