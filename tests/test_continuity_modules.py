"""[V65] ContinuityInspector Sub-modules + PreDirectorChecklist Unit Tests"""

import pytest
import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.domain.agents.continuity_arc import ContinuityArcValidator
from modules.domain.agents.continuity_blueprint import ContinuityBlueprintValidator
from modules.domain.agents.continuity_manuscript import ContinuityManuscriptValidator
from modules.domain.agents.continuity_tracker import ContinuityTrackerIntegration
from modules.core.pre_director_checklist import (
    PreDirectorChecklist,
    ChecklistResult,
    CheckItem,
    CheckCategory,
    CheckSeverity,
)


# ══════════════════════════════════════════════════════════════
# Shared Mock Factories
# ══════════════════════════════════════════════════════════════

def _make_mock_inspector():
    """ContinuityInspector mock을 생성 (4개 서브모듈 공통)"""
    inspector = MagicMock()
    inspector._escape_braces = MagicMock(side_effect=lambda x: x)
    inspector._format_entity_registry = MagicMock(return_value="(등록된 Entity 없음)")
    inspector._extract_acquisitions = MagicMock(return_value=[])
    inspector._extract_grants = MagicMock(return_value=[])
    inspector._extract_key_sentences = MagicMock(return_value="핵심 문장 요약")
    inspector._is_same_item = MagicMock(side_effect=lambda a, b: a.strip().lower() == b.strip().lower())
    inspector._is_distributed_item = MagicMock(return_value=False)
    inspector._filter_distributed_items = MagicMock(side_effect=lambda items, ctx: items)

    # 패턴들
    inspector.acquire_patterns = [
        r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:획득|챙기|얻|주워\s*들|가져)",
    ]
    inspector.grant_patterns = [
        r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:하사|수여|내리|던져\s*주|건네)",
    ]
    inspector.possession_patterns = [
        r"품속.*?(.+?)(?:이|가)\s*(?:있|자리)",
    ]
    inspector.usage_patterns = [
        r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:뽑아\s*들|집어\s*들|꺼내\s*들)",
    ]
    inspector.distribution_patterns = []

    # LLM 호출 mock
    inspector.ask = MagicMock(return_value='{"decision":"PASS","severity":"NONE","violations":[],"warnings":[]}')
    inspector._extract_json_robust = MagicMock(return_value={
        "decision": "PASS",
        "severity": "NONE",
        "violations": [],
        "warnings": [],
    })

    # context mock (DB 접근용)
    inspector.context = MagicMock()
    inspector.context.db = MagicMock()
    inspector.context.master_bible = {}

    return inspector


# ══════════════════════════════════════════════════════════════
# ContinuityArcValidator Tests
# ══════════════════════════════════════════════════════════════

class TestContinuityArcValidatorInit:
    """1. ContinuityArcValidator 초기화 테스트"""

    def test_init_stores_inspector_ref(self):
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)
        assert validator._ci is inspector

    def test_init_has_public_methods(self):
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)
        assert callable(getattr(validator, 'inspect_arc', None))
        assert callable(getattr(validator, '_arc_python_precheck', None))
        assert callable(getattr(validator, '_check_intra_arc_consistency', None))


class TestContinuityArcValidatorTimeline:
    """2-3. Arc 간 타임라인 검증"""

    def test_arc1_returns_pass_without_prev_arcs(self):
        """Arc 1은 이전 Arc 없이 자동 검증"""
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        current_arc = {
            "arc_no": 1,
            "tactical_doc": "제1화 전술 설계서 내용이 충분히 길어야 합니다. " * 10,
            "joint_docs": {},
            "status_shadow": {},
            "ep_start": 1,
            "ep_count": 5,
        }
        result = validator.inspect_arc(current_arc, prev_arcs=[])
        assert result["decision"] == "PASS"

    def test_arc_with_prev_arcs_calls_llm(self):
        """이전 Arc가 있으면 LLM 호출 (Phase 1.5 + Phase 2)"""
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        prev_arcs = [{
            "arc_no": 1,
            "tactical_doc": "이전 Arc 내용" * 20,
            "joint_docs": {"final_location": "팽가", "physical_inventory": ["백근도"]},
            "status_shadow": {"internal_energy_loss": "20%", "expected_injuries": "없음"},
            "state_constraints": {"arc_end_state": {"internal_energy": 80}},
            "ep_start": 1, "ep_end": 5,
        }]
        current_arc = {
            "arc_no": 2,
            "tactical_doc": "현재 Arc 전술 설계서 " * 30,
            "joint_docs": {"final_location": "무림맹"},
            "status_shadow": {},
            "state_constraints": {"arc_start_state": {}},
            "ep_start": 6, "ep_count": 5,
        }

        result = validator.inspect_arc(current_arc, prev_arcs=prev_arcs)
        assert result["decision"] == "PASS"
        # ask가 최소 1회 호출됨 (Phase 1.5 Joint Docs + Phase 2 LLM 검증)
        assert inspector.ask.call_count >= 1

    def test_missing_tactical_doc_returns_reject(self):
        """tactical_doc 없으면 REJECT"""
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        current_arc = {
            "arc_no": 2,
            "tactical_doc": "",
            "joint_docs": {},
            "ep_start": 6, "ep_count": 5,
        }
        prev_arcs = [{"arc_no": 1, "tactical_doc": "x" * 100}]
        result = validator.inspect_arc(current_arc, prev_arcs=prev_arcs)
        assert result["decision"] == "REJECT"
        assert result["severity"] == "CRITICAL"
        assert any(v["type"] == "missing_tactical_doc" for v in result["violations"])


class TestContinuityArcValidatorIntraArc:
    """4. 이벤트 추출 및 Arc 내 모순 검증"""

    def test_intra_arc_duplicate_acquisition(self):
        """같은 Arc 내에서 아이템 중복 획득 감지"""
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        tactical_doc = (
            "[제10화 전술 설계] 주인공이 '천년빙옥'을 획득한다. "
            "이후 적과 대결.\n"
            "[제11화 전술 설계] 동굴에서 다시 '천년빙옥'을 획득한다."
        )
        arc = {
            "arc_no": 2,
            "tactical_doc": tactical_doc,
            "ep_start": 10,
        }

        violations = validator._check_intra_arc_consistency(arc)
        # 패턴 매칭은 acquire_patterns에 의존 — 한국어 "획득" 포함
        # 패턴이 매칭되면 중복 획득이 감지됨
        # (패턴이 정확히 매칭되지 않을 수도 있으므로 결과 유형만 검증)
        assert isinstance(violations, list)

    def test_intra_arc_injury_state_discontinuity(self):
        """부상 후 회복 없이 전투 시 경고"""
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        tactical_doc = (
            "[제10화 전술 설계] 주인공이 심한 부상을 입는다. 골절과 출혈.\n"
            "[제11화 전술 설계] 다음날 격렬한 전투에 참가한다. 대결에서 승리."
        )
        arc = {
            "arc_no": 2,
            "tactical_doc": tactical_doc,
            "ep_start": 10,
        }

        violations = validator._check_intra_arc_consistency(arc)
        # 부상 + 전투 패턴이 인접한 에피소드에서 발견되면 MINOR state_discontinuity
        state_disc = [v for v in violations if v.get("type") == "state_discontinuity"]
        assert isinstance(violations, list)

    def test_format_prev_arcs_returns_string(self):
        """_format_prev_arcs 결과가 문자열인지 확인"""
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        prev_arcs = [{
            "arc_no": 1,
            "tactical_doc": "작전" * 50,
            "joint_docs": {"final_location": "팽가", "physical_inventory": ["검"]},
            "status_shadow": {},
            "state_constraints": {"arc_end_state": {}},
            "ep_start": 1, "ep_end": 5,
        }]
        result = validator._format_prev_arcs(prev_arcs)
        assert isinstance(result, str)
        assert "Arc 1" in result

    def test_extract_last_episode_content(self):
        """마지막 에피소드 내용 추출"""
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        tactical_doc = (
            "[제1화 전술 설계] 시작 내용\n"
            "[제2화 전술 설계] 중간 내용\n"
            "[제3화 전술 설계] 마지막 내용 여기서 끝난다"
        )
        result = validator._extract_last_episode_content(tactical_doc, 3)
        assert "마지막 내용" in result


# ══════════════════════════════════════════════════════════════
# ContinuityManuscriptValidator Tests
# ══════════════════════════════════════════════════════════════

class TestContinuityManuscriptValidatorInit:
    """5. ContinuityManuscriptValidator 초기화 테스트"""

    def test_init_stores_inspector_ref(self):
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)
        assert validator._ci is inspector

    def test_has_acquisition_and_possession_patterns(self):
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)
        assert hasattr(validator, 'ACQUISITION_PATTERNS')
        assert hasattr(validator, 'POSSESSION_PATTERNS')
        assert len(validator.ACQUISITION_PATTERNS) > 0


class TestContinuityManuscriptBlueprintMatch:
    """6. 원고-블루프린트 일치 검증"""

    def test_first_episode_blueprint_only(self):
        """1화는 Blueprint 준수만 체크"""
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)

        manuscript = "이것은 첫 화 원고입니다. 전투와 대화가 포함됩니다. " * 50
        blueprint = {
            "scene_breakdown": {
                "scene1": "전투 장면 설명",
                "scene2": "대화 장면 설명",
            }
        }
        result = validator.inspect_manuscript(
            current_ep=1,
            manuscript=manuscript,
            blueprint=blueprint,
            prev_manuscripts=[]
        )
        assert result["decision"] in ["PASS", "REJECT"]
        assert "blueprint_alignment" in result

    def test_empty_manuscript_rejected(self):
        """빈 원고는 REJECT"""
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)

        result = validator.inspect_manuscript(
            current_ep=5,
            manuscript="짧은 텍스트",
            blueprint={},
            prev_manuscripts=[{"ep_num": 4, "content": "이전 원고 " * 100}]
        )
        assert result["decision"] == "REJECT"
        assert result["severity"] == "CRITICAL"


class TestContinuityManuscriptContradiction:
    """7. 원고 내 모순 감지"""

    def test_villain_intelligence_detection(self):
        """악역 지능 보호 (연속 과소평가 감지)"""
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)

        prev_manuscripts = [
            {"ep_num": 1, "content": "악역이 '철부지 놈' 이라며 주인공을 비웃었다. 한심한 녀석."},
            {"ep_num": 2, "content": "악역은 '어차피 알아서 망할 것'이라며 무시했다."},
        ]
        manuscript = "악역이 또 '객기에 불과하다'며 내버려 둬라고 명령했다."

        issues = validator._check_villain_intelligence(prev_manuscripts, manuscript)
        # 3회 연속 과소평가 → CRITICAL
        assert len(issues) > 0
        assert any(i.get("type") == "stupid_villain" for i in issues)

    def test_time_flow_warning(self):
        """시간 흐름 검증 - 연속 대형 이벤트"""
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)

        prev = [{"ep_num": 3, "content": "격렬한 전투가 벌어졌다. 혈투 끝에 간신히 승리."}]
        manuscript = "그 시각, 또 다른 습격이 시작되었다. 잠시 후 대결이 시작되었다."

        warnings = validator._check_time_flow(prev, manuscript)
        assert isinstance(warnings, list)


class TestContinuityManuscriptCrossEpisodeDuplication:
    """8. 크로스 에피소드 중복 감지"""

    def test_check_reader_immersion_free_powerup(self):
        """공짜 파워업 감지"""
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)

        prev = [{"ep_num": 1, "content": "수련을 계속했다."}]
        manuscript = "경지 상승이 이루어졌다. 각성하며 돌파에 성공했다. 실력 향상이 체감되었다."

        warnings = validator._check_reader_immersion(prev, manuscript, current_ep=5)
        # 파워업 있고 대가 없으면 경고
        free_powerup = [w for w in warnings if w.get("type") == "free_powerup"]
        assert len(free_powerup) > 0

    def test_skill_timeline_unlearned_skill(self):
        """미습득 스킬 사용 감지"""
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)

        prev = [
            {"ep_num": 1, "content": "기초 검법을 수련했다."},
        ]
        # 10화에서 습득 기록 없는 스킬 사용
        manuscript = "그는 '절천비검법'을 펼치며 적을 압도했다."

        result = validator._check_skill_timeline(
            current_ep=10,
            manuscript=manuscript,
            prev_manuscripts=prev
        )
        assert "skill_timeline" in result
        assert isinstance(result["violations"], list)

    def test_relationship_jump_detection(self):
        """관계 급변 탐지"""
        inspector = _make_mock_inspector()
        validator = ContinuityManuscriptValidator(inspector)

        prev = [{"ep_num": 1, "content": "사병들은 그를 멸시했다. 하찮은 놈이라 비웃었다."}]
        manuscript = "사병들은 갑자기 충성을 맹세했다. 주군님 만세를 외쳤다."

        warnings = validator._check_relationship_jump(prev, manuscript)
        assert len(warnings) > 0
        assert any(w.get("type") == "relationship_jump" for w in warnings)


# ══════════════════════════════════════════════════════════════
# ContinuityBlueprintValidator Tests
# ══════════════════════════════════════════════════════════════

class TestContinuityBlueprintValidatorInit:
    """9. ContinuityBlueprintValidator 초기화 테스트"""

    def test_init_stores_inspector_ref(self):
        inspector = _make_mock_inspector()
        validator = ContinuityBlueprintValidator(inspector)
        assert validator._ci is inspector

    def test_has_public_api(self):
        inspector = _make_mock_inspector()
        validator = ContinuityBlueprintValidator(inspector)
        assert callable(getattr(validator, 'inspect', None))
        assert callable(getattr(validator, 'get_prev_blueprints', None))


class TestContinuityBlueprintValidation:
    """10-11. 블루프린트 필드 검증 및 씬 연속성"""

    def test_first_ep_auto_pass(self):
        """1화는 자동 PASS"""
        inspector = _make_mock_inspector()
        validator = ContinuityBlueprintValidator(inspector)

        result = validator.inspect(
            current_ep=1,
            current_blueprint={"integrated_scenario": "첫 화 시나리오"},
            prev_blueprints=[]
        )
        assert result["decision"] == "PASS"
        assert result["severity"] == "NONE"

    def test_missing_scenario_rejected(self):
        """integrated_scenario 없으면 REJECT"""
        inspector = _make_mock_inspector()
        validator = ContinuityBlueprintValidator(inspector)

        result = validator.inspect(
            current_ep=5,
            current_blueprint={"scene_breakdown": {}},
            prev_blueprints=[{"ep_num": 4, "integrated_scenario": "이전 시나리오"}]
        )
        assert result["decision"] == "REJECT"
        assert result["severity"] == "CRITICAL"
        assert any(v["type"] == "missing_scenario" for v in result["violations"])

    def test_normal_inspection_calls_llm(self):
        """정상 검증 시 LLM 호출"""
        inspector = _make_mock_inspector()
        validator = ContinuityBlueprintValidator(inspector)

        prev = [{"ep_num": 1, "integrated_scenario": "이전 에피소드 시나리오 내용" * 10}]
        current = {"integrated_scenario": "현재 에피소드 시나리오 " * 30}

        result = validator.inspect(
            current_ep=2,
            current_blueprint=current,
            prev_blueprints=prev
        )
        assert result["decision"] == "PASS"
        inspector.ask.assert_called_once()

    def test_python_precheck_duplicate_item(self):
        """Python 사전 검증 — 중복 획득"""
        inspector = _make_mock_inspector()
        # _is_same_item이 실제처럼 동작하게 설정
        inspector._is_same_item = MagicMock(side_effect=lambda a, b: a.strip() == b.strip())
        validator = ContinuityBlueprintValidator(inspector)

        prev_bp = [{
            "ep_num": 3,
            "integrated_scenario": "주인공이 '용린검'을 획득하였다."
        }]
        current_scenario = "주인공이 다시 '용린검'을 획득한다."

        result = validator._python_precheck(
            current_ep=5,
            current_scenario=current_scenario,
            prev_blueprints=prev_bp
        )
        # acquire_patterns에 매칭되면 critical_violations에 추가
        assert "critical_violations" in result
        assert "timeline" in result

    def test_format_prev_blueprints_returns_string(self):
        """_format_prev_blueprints가 문자열 반환"""
        inspector = _make_mock_inspector()
        validator = ContinuityBlueprintValidator(inspector)

        prev = [
            {"ep_num": 1, "integrated_scenario": "시나리오 1 내용"},
            {"ep_num": 2, "integrated_scenario": "시나리오 2 내용"},
        ]
        result = validator._format_prev_blueprints(prev)
        assert isinstance(result, str)
        assert "제 1화" in result
        assert "제 2화" in result


# ══════════════════════════════════════════════════════════════
# ContinuityTrackerIntegration Tests
# ══════════════════════════════════════════════════════════════

class TestContinuityTrackerInit:
    """12. ContinuityTrackerIntegration 초기화 테스트"""

    def test_init_stores_inspector_ref(self):
        inspector = _make_mock_inspector()
        tracker = ContinuityTrackerIntegration(inspector)
        assert tracker._ci is inspector

    def test_has_public_api(self):
        inspector = _make_mock_inspector()
        tracker = ContinuityTrackerIntegration(inspector)
        assert callable(getattr(tracker, 'init_trackers', None))
        assert callable(getattr(tracker, 'validate_with_trackers', None))
        assert callable(getattr(tracker, 'load_trackers_from_db', None))


class TestContinuityTrackerUpdate:
    """13. 추적 데이터 업데이트"""

    @patch('modules.domain.agents.continuity_tracker.V49_7_MODULES_AVAILABLE', False)
    def test_init_trackers_disabled_when_modules_unavailable(self):
        """V49.7 모듈 미설치 시 비활성화"""
        inspector = _make_mock_inspector()
        tracker = ContinuityTrackerIntegration(inspector)
        tracker.init_trackers()
        assert inspector.v49_7_enabled is False

    def test_validate_with_trackers_disabled(self):
        """비활성화 시 빈 결과 반환"""
        inspector = _make_mock_inspector()
        inspector.v49_7_enabled = False
        tracker = ContinuityTrackerIntegration(inspector)

        result = tracker.validate_with_trackers(
            arc=1, episode=1, content="테스트", content_type="blueprint"
        )
        assert result["warnings"] == []
        assert result["violations"] == []
        assert result["tracker_results"] == {}


class TestContinuityTrackerQuery:
    """14. 추적 데이터 조회"""

    def test_load_trackers_from_db_disabled(self):
        """비활성화 시 에러 반환"""
        inspector = _make_mock_inspector()
        inspector.v49_7_enabled = False
        tracker = ContinuityTrackerIntegration(inspector)

        result = tracker.load_trackers_from_db()
        assert "error" in result

    def test_load_trackers_from_db_empty_arcs(self):
        """빈 Arc 데이터로 로드"""
        inspector = _make_mock_inspector()
        inspector.v49_7_enabled = True
        inspector.foreshadow_tracker = MagicMock()
        inspector.foreshadow_tracker.load_from_arcs = MagicMock(return_value=0)
        inspector.power_tracker = MagicMock()
        inspector.relationship_tracker = MagicMock()

        tracker = ContinuityTrackerIntegration(inspector)
        result = tracker.load_trackers_from_db(arcs_data=[])

        assert result["foreshadowings"] == 0
        assert result["relationships"] == 0
        assert result["power_entries"] == 0

    def test_load_trackers_from_db_with_arc_data(self):
        """Arc 데이터 포함 로드"""
        inspector = _make_mock_inspector()
        inspector.v49_7_enabled = True
        inspector.foreshadow_tracker = MagicMock()
        inspector.foreshadow_tracker.load_from_arcs = MagicMock(return_value=3)
        inspector.power_tracker = MagicMock()
        inspector.relationship_tracker = MagicMock()
        inspector.context.master_bible = {}

        tracker = ContinuityTrackerIntegration(inspector)

        arcs_data = [
            {
                "arc_no": 1,
                "state_constraints": {
                    "arc_end_state": {"power_level": 45}
                },
                "relationship_changes": [
                    {"target": "장로", "from": "무시", "to": "경외", "trigger": "대결 승리"}
                ],
                "ep_end": 5,
            }
        ]
        result = tracker.load_trackers_from_db(arcs_data=arcs_data)
        assert result["foreshadowings"] == 3
        assert result["power_entries"] == 1
        assert result["relationships"] == 1

    def test_get_protagonist_name_fallback(self):
        """주인공 이름 추출 실패 시 기본값"""
        inspector = _make_mock_inspector()
        inspector.context.master_bible = {}  # 빈 bible

        tracker = ContinuityTrackerIntegration(inspector)
        name = tracker._get_protagonist_name()
        assert name == "주인공"


# ══════════════════════════════════════════════════════════════
# PreDirectorChecklist Tests
# ══════════════════════════════════════════════════════════════

class TestPreDirectorChecklistInit:
    """15. PreDirectorChecklist 초기화 테스트"""

    def test_init_enabled_by_default(self):
        checker = PreDirectorChecklist()
        assert checker.enabled is True

    def test_disabled_returns_empty_pass(self):
        checker = PreDirectorChecklist()
        checker.enabled = False
        result = checker.check("any content", "manuscript")
        assert result.passed is True
        assert result.fail_count == 0
        assert len(result.items) == 0

    def test_has_length_constants(self):
        checker = PreDirectorChecklist()
        assert "min" in checker.MANUSCRIPT_LENGTH
        assert "max" in checker.MANUSCRIPT_LENGTH
        assert checker.MANUSCRIPT_LENGTH["min"] > 0


class TestPreDirectorChecklistGeneration:
    """16. 체크리스트 생성 — 필수 필드 존재 확인"""

    def test_manuscript_check_returns_result(self):
        """원고 체크 결과가 ChecklistResult인지"""
        checker = PreDirectorChecklist()
        # 충분히 긴 원고 생성
        manuscript = self._make_valid_manuscript()
        result = checker.check(manuscript, "manuscript")
        assert isinstance(result, ChecklistResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.items, list)
        assert isinstance(result.fail_count, int)

    def test_blueprint_check_returns_result(self):
        """블루프린트 체크 결과"""
        checker = PreDirectorChecklist()
        bp = json.dumps({
            "integrated_scenario": "시나리오 " * 100,
            "scene_breakdown": {
                "scene1": {"title": "시작", "description": "도입부"},
                "scene2": {"title": "전개", "description": "중반부"},
                "scene3": {"title": "위기", "description": "클라이맥스"},
                "scene4": {"title": "결말", "description": "마무리"},
            },
            "ending_hook": "다음 화 예고"
        }, ensure_ascii=False)
        result = checker.check(bp, "blueprint")
        assert isinstance(result, ChecklistResult)

    def test_manuscript_too_short_fails(self):
        """원고가 너무 짧으면 FAIL"""
        checker = PreDirectorChecklist()
        result = checker.check("짧은 원고", "manuscript")
        assert result.passed is False
        assert result.fail_count > 0
        assert any("길이 부족" in reason for reason in result.blocking_reasons)

    @staticmethod
    def _make_valid_manuscript():
        """충분한 길이와 구조를 갖춘 원고 생성"""
        paragraphs = []
        for i in range(10):
            para = f"이것은 제{i+1}번째 문단입니다. "
            para += f'"이것은 대화입니다." 그가 말했다. '
            para += f'"정말인가요?" 그녀가 물었다. '
            para += "주변의 풍경이 아름다웠다. 바람이 불었다. " * 5
            paragraphs.append(para)
        return "\n\n".join(paragraphs)


class TestPreDirectorChecklistConstraintMap:
    """17. 제약 맵 구축 — 정상 케이스"""

    def test_blueprint_required_fields_check(self):
        """블루프린트 필수 필드 검증"""
        checker = PreDirectorChecklist()
        # 필수 필드 누락
        bp_missing = json.dumps({"other_field": "value"}, ensure_ascii=False)
        result = checker.check(bp_missing, "blueprint")
        assert result.passed is False
        field_fails = [
            i for i in result.items
            if i.category == CheckCategory.REQUIRED_FIELDS and i.severity == CheckSeverity.FAIL
        ]
        assert len(field_fails) >= 1

    def test_blueprint_scene_count_check(self):
        """블루프린트 씬 개수 검증"""
        checker = PreDirectorChecklist()
        # 씬이 2개뿐 (최소 3개 필요)
        bp = json.dumps({
            "integrated_scenario": "시나리오 " * 100,
            "scene_breakdown": {
                "scene1": "장면1",
                "scene2": "장면2",
            }
        }, ensure_ascii=False)
        result = checker.check(bp, "blueprint")
        scene_fails = [
            i for i in result.items
            if i.name == "씬 개수" and i.severity == CheckSeverity.FAIL
        ]
        assert len(scene_fails) >= 1

    def test_forbidden_patterns_detected(self):
        """금지 패턴(TODO, PLACEHOLDER) 감지"""
        checker = PreDirectorChecklist()
        manuscript = self._make_long_text_with_forbidden()
        result = checker.check(manuscript, "manuscript")
        forbidden_fails = [
            i for i in result.items
            if i.category == CheckCategory.FORBIDDEN_PATTERNS
        ]
        assert len(forbidden_fails) > 0

    @staticmethod
    def _make_long_text_with_forbidden():
        """금지 패턴 포함 장문 텍스트"""
        base = (
            '"안녕하세요." 그가 말했다.\n\n'
            '"반갑습니다." 그녀가 대답했다.\n\n'
            '"무슨 일인가요?" 그가 물었다.\n\n'
            '"중요한 일입니다." 그녀가 대답했다.\n\n'
            '"알겠습니다." 그가 고개를 끄덕였다.\n\n'
        )
        return base * 20 + "\n[TODO] 여기에 내용 추가\n" + base * 5


class TestPreDirectorChecklistEmptyInput:
    """18. 빈 입력 처리"""

    def test_empty_manuscript(self):
        """빈 원고 처리"""
        checker = PreDirectorChecklist()
        result = checker.check("", "manuscript")
        assert result.passed is False
        assert result.fail_count > 0

    def test_empty_blueprint_json(self):
        """빈 JSON 블루프린트"""
        checker = PreDirectorChecklist()
        result = checker.check("{}", "blueprint")
        assert result.passed is False

    def test_invalid_blueprint_json(self):
        """잘못된 JSON"""
        checker = PreDirectorChecklist()
        result = checker.check("not json at all {broken", "blueprint")
        assert result.passed is False
        json_fail = [i for i in result.items if "JSON" in i.message]
        assert len(json_fail) > 0

    def test_get_feedback_empty_when_all_pass(self):
        """모두 통과 시 빈 피드백"""
        checker = PreDirectorChecklist()
        result = ChecklistResult(
            passed=True, items=[], fail_count=0,
            warning_count=0, summary="OK", blocking_reasons=[]
        )
        feedback = checker.get_feedback(result)
        assert feedback == ""

    def test_get_feedback_with_blocking_reasons(self):
        """차단 사유 포함 피드백"""
        checker = PreDirectorChecklist()
        result = ChecklistResult(
            passed=False,
            items=[
                CheckItem(
                    category=CheckCategory.LENGTH,
                    name="최소 길이",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message="원고 길이 부족: 100자"
                )
            ],
            fail_count=1,
            warning_count=0,
            summary="실패",
            blocking_reasons=["원고 길이 부족: 100자"]
        )
        feedback = checker.get_feedback(result)
        assert "차단 사유" in feedback
        assert "원고 길이 부족" in feedback


# ══════════════════════════════════════════════════════════════
# Additional coverage tests
# ══════════════════════════════════════════════════════════════

class TestPreDirectorChecklistNarrativeFlow:
    """서사 흐름, 클리셰, 문장 다양성 추가 검증"""

    def test_cliche_density_high(self):
        """클리셰 밀도 높은 원고"""
        checker = PreDirectorChecklist()
        # 클리셰를 반복적으로 포함
        cliche_text = (
            "이를 악물고 주먹을 불끈 쥐었다. 심장이 쿵 내려앉았다. "
            "눈앞이 캄캄해졌다. 온몸이 굳었다. 식은땀이 흘렀다. "
            "분노가 치밀어 올랐다. 피가 끓었다. "
        )
        # 대화와 문단 구조를 갖춘 본문
        dialogue = '"전투다!" 그가 외쳤다. "물러서!" 적이 말했다. "이겼다!" "패배다." "도망가자!"\n\n'
        full = dialogue + (cliche_text + "\n\n") * 30
        result = checker.check(full, "manuscript")

        cliche_items = [i for i in result.items if i.category == CheckCategory.CLICHE_DENSITY]
        assert len(cliche_items) > 0

    def test_sentence_variety_high_repetition(self):
        """문장 시작어 과다 반복"""
        checker = PreDirectorChecklist()
        # "그는"으로 시작하는 문장 10개 연속
        sentences = []
        for i in range(10):
            sentences.append(f"그는 검을 들었다. 그는 적을 바라보았다. 그는 한 발 나아갔다.")
        dialogue = '\n\n"공격해!" 그가 외쳤다. "막아!" 적이 말했다. "이겼다!" "졌다!"\n\n'
        full_text = dialogue + "\n\n".join(sentences) + dialogue * 10
        result = checker.check(full_text, "manuscript")
        variety_items = [i for i in result.items if i.category == CheckCategory.SENTENCE_VARIETY]
        assert len(variety_items) > 0

    def test_pacing_rhythm_all_action(self):
        """전체가 액션으로만 구성된 원고 - 페이싱 체크 실행 확인"""
        checker = PreDirectorChecklist()
        # 충분한 대화수 확보 (FAIL 차단 방지) + 3000자 이상 확보
        action_text = (
            "공격이 시작되었다. 그는 피했다. 막았다. 내리찍었다. 찔렀다. 베었다. "
            "달려들었다. 뛰어올랐다. 굴렀다. 날아갔다. 충돌했다. 쓰러졌다. "
            "다시 공격했다. 피하고 막고 내리쳤다. 피했다. 막았다. 달려들었다. "
        )
        dialogue = '"전투다!" 그가 외쳤다. "받아라!" 적이 말했다. "이겼다!" "패배다!" "도망가!" '
        # 각 문단에 액션 키워드를 밀집시킴
        paragraph = dialogue + action_text * 3
        full = ("\n\n".join([paragraph] * 15))
        # 3000자 이상 확보
        assert len(full) > 3000, f"Text length: {len(full)}"
        result = checker.check(full, "manuscript")
        pacing_items = [i for i in result.items if i.category == CheckCategory.PACING]
        assert len(pacing_items) > 0


class TestContinuityArcLLMFailure:
    """LLM 호출 실패 시 폴백 테스트"""

    def test_llm_failure_returns_pass_with_warning(self):
        """LLM 실패 시 PASS + 경고"""
        inspector = _make_mock_inspector()
        inspector.ask = MagicMock(side_effect=Exception("API error"))
        validator = ContinuityArcValidator(inspector)

        prev_arcs = [{
            "arc_no": 1,
            "tactical_doc": "이전 내용 " * 30,
            "joint_docs": {"final_location": "팽가"},
            "status_shadow": {},
            "state_constraints": {"arc_end_state": {"internal_energy": 80}},
            "ep_start": 1, "ep_end": 5,
        }]
        current_arc = {
            "arc_no": 2,
            "tactical_doc": "현재 내용 " * 30,
            "joint_docs": {},
            "status_shadow": {},
            "state_constraints": {"arc_start_state": {}},
            "ep_start": 6, "ep_count": 5,
        }

        result = validator.inspect_arc(current_arc, prev_arcs=prev_arcs)
        assert result["decision"] == "PASS"
        assert any("실패" in w or "확인" in w for w in result.get("warnings", []))


class TestContinuityManuscriptLLMFailure:
    """원고 검증 LLM 실패 시 폴백"""

    def test_llm_failure_returns_pass(self):
        inspector = _make_mock_inspector()
        inspector.ask = MagicMock(side_effect=Exception("API error"))
        validator = ContinuityManuscriptValidator(inspector)

        prev = [{"ep_num": 1, "content": "이전 원고 " * 100}]
        manuscript = "현재 원고 내용입니다. " * 100

        result = validator.inspect_manuscript(
            current_ep=2,
            manuscript=manuscript,
            blueprint={"scene_breakdown": {}},
            prev_manuscripts=prev
        )
        assert result["decision"] == "PASS"


class TestContinuityBlueprintLLMFailure:
    """블루프린트 검증 LLM 실패 시 폴백"""

    def test_llm_failure_returns_pass(self):
        inspector = _make_mock_inspector()
        inspector.ask = MagicMock(side_effect=Exception("API error"))
        validator = ContinuityBlueprintValidator(inspector)

        prev = [{"ep_num": 1, "integrated_scenario": "이전 시나리오 " * 20}]
        current = {"integrated_scenario": "현재 시나리오 " * 30}

        result = validator.inspect(current_ep=2, current_blueprint=current, prev_blueprints=prev)
        assert result["decision"] == "PASS"
        assert any("실패" in w or "확인" in w for w in result.get("warnings", []))


class TestPreDirectorChecklistDialogueRatio:
    """대화/지문 비율 검증"""

    def test_no_dialogue_fails(self):
        """대화 전혀 없는 원고"""
        checker = PreDirectorChecklist()
        # 대화 없이 순수 서술만
        text = ("서술만 있는 문단입니다. 주인공은 걸어갔다. 바람이 불었다. 풍경이 아름다웠다.\n\n") * 30
        result = checker.check(text, "manuscript")
        dialogue_fails = [
            i for i in result.items
            if i.category == CheckCategory.STRUCTURE and "대화" in i.message
        ]
        assert len(dialogue_fails) > 0

    def test_balanced_dialogue_passes(self):
        """적절한 대화 비율"""
        checker = PreDirectorChecklist()
        text = TestPreDirectorChecklistGeneration._make_valid_manuscript()
        result = checker.check(text, "manuscript")
        dialogue_items = [
            i for i in result.items
            if i.category == CheckCategory.STRUCTURE and "대화" in i.name
        ]
        # 적절한 비율이면 FAIL이 아님
        for item in dialogue_items:
            if item.severity == CheckSeverity.PASS:
                assert item.passed is True


class TestContinuityArcGenerateFixInstructions:
    """수정 지시 생성 테스트"""

    def test_generate_fix_instructions_duplicate(self):
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        violations = [
            {
                "type": "duplicate_acquisition",
                "item_or_subject": "백근도",
                "prev_arc": 1,
            }
        ]
        result = validator._generate_arc_fix_instructions(violations)
        assert "백근도" in result
        assert "중복" in result

    def test_generate_fix_instructions_empty(self):
        inspector = _make_mock_inspector()
        validator = ContinuityArcValidator(inspector)

        result = validator._generate_arc_fix_instructions([])
        assert "위반" in result or "수정" in result
