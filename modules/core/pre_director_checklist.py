"""
[V53.4] Pre-Director Checklist (사전 체크리스트)
Director 호출 전 Python 기반 필수 항목 체크

핵심: 명백한 실패를 LLM 호출 전에 차단하여 비용 절감

원리:
1. 원고/블루프린트 기본 무결성 검사
2. 필수 요소 존재 여부 확인
3. 명백한 위반 사항 감지
4. FAIL 시 Director 호출 없이 즉시 반려

비용: $0 (Python만 사용)

사용:
    checker = PreDirectorChecklist()
    result = checker.check(
        content=manuscript,
        content_type="manuscript",
        context={"blueprint": bp, "arc_data": arc}
    )
    if not result.passed:
        # Director 호출 없이 재생성
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import ManuscriptLimits  # [V64.P4]
from modules.core.scene_obligation_heuristics import (
    build_blueprint_scene_profile,
    estimate_scene_flex_budget,
    measure_manuscript_scene_materialization,
)
from modules.domain.agents.scene_cardinality_contract import evaluate_stage3_scene_cardinality


class CheckCategory(Enum):
    """체크 카테고리"""

    LENGTH = "length"
    STRUCTURE = "structure"
    CONTINUITY = "continuity"
    BLUEPRINT_MATCH = "blueprint_match"
    REQUIRED_FIELDS = "required_fields"
    FORBIDDEN_PATTERNS = "forbidden_patterns"
    SCOPE = "scope"
    NARRATIVE_FLOW = "narrative_flow"  # [V60.4] 서사 흐름
    NPC_BEHAVIOR = "npc_behavior"  # [V60.5] NPC 행동 급변
    SENTENCE_VARIETY = "sentence_variety"  # [V60.6] 문장 다양성
    PACING = "pacing"  # [V60.6] 긴장-이완 리듬
    SETTING_KEYWORDS = "setting_keywords"  # [V60.6] 설정 키워드
    CLICHE_DENSITY = "cliche_density"  # [V60.6] 클리셰 밀도


class CheckSeverity(Enum):
    """체크 결과 심각도"""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class CheckItem:
    """개별 체크 항목"""

    category: CheckCategory
    name: str
    passed: bool
    severity: CheckSeverity
    message: str


@dataclass
class ChecklistResult:
    """체크리스트 결과"""

    passed: bool
    items: list[CheckItem]
    fail_count: int
    warning_count: int
    summary: str
    blocking_reasons: list[str]  # FAIL 사유들


class PreDirectorChecklist:
    """사전 체크리스트 시스템"""

    _GENERIC_LOCATION_TOKENS = {
        "호텔",
        "라운지",
        "카페",
        "룸",
        "방",
        "실",
        "로비",
        "홀",
        "건물",
        "내부",
        "외부",
        "입구",
        "출구",
        "복도",
        "통로",
        "스위트룸",
        "프라이빗",
    }

    # [V64.P4] 원고 최소/최대 길이 — ManuscriptLimits 참조
    MANUSCRIPT_LENGTH = {
        "min": ManuscriptLimits.MIN_LENGTH,
        "max": ManuscriptLimits.MAX_LENGTH,
        "warning_min": ManuscriptLimits.WARNING_LENGTH,
        "warning_max": 12000,
    }

    # 블루프린트 최소 길이
    BLUEPRINT_LENGTH = {"min": 500, "scenario_min": 300}

    # 금지 패턴 (명백한 오류)
    FORBIDDEN_PATTERNS = {
        "manuscript": [
            (r"\[TODO\]", "TODO 마커가 남아있음"),
            (r"\[PLACEHOLDER\]", "플레이스홀더가 남아있음"),
            (r"제\s*\d+\s*화\s*끝", "화 끝 마커가 본문에 포함됨"),
            (r"```", "코드 블록 마커가 포함됨"),
            (r"\{[a-zA-Z_]+\}", "템플릿 변수가 치환되지 않음"),
        ],
        "blueprint": [
            (r"\[TODO\]", "TODO 마커가 남아있음"),
            (r"\{[a-zA-Z_]+\}", "템플릿 변수가 치환되지 않음"),
        ],
    }

    # 필수 요소 (원고)
    MANUSCRIPT_REQUIRED = {
        "dialogue": (4, "대화가 최소 4개 이상 있어야 함"),
        "paragraphs": (5, "문단이 최소 5개 이상 있어야 함"),
    }

    def __init__(self) -> None:
        self.enabled = True
        self._manuscript_checker = None  # [R5-1a] lazy sub-module
        self._narrative_checker = None  # [R5-2c] lazy sub-module
        self._style_checker = None  # [R5-2c] lazy sub-module

    @property
    def manuscript_checker(self):
        """[R5-1a] 원고 품질 체크 서브모듈 (lazy init)."""
        if self._manuscript_checker is None:
            from modules.core.pre_director_manuscript_checker import PreDirectorManuscriptChecker

            self._manuscript_checker = PreDirectorManuscriptChecker(self)
        return self._manuscript_checker

    @property
    def narrative_checker(self):
        """[R5-2c] 서사 흐름 체크 서브모듈 (lazy init)."""
        if self._narrative_checker is None:
            from modules.core.pre_director_narrative_checker import PreDirectorNarrativeChecker

            self._narrative_checker = PreDirectorNarrativeChecker(self)
        return self._narrative_checker

    @property
    def style_checker(self):
        """[R5-2c] 문체 품질 체크 서브모듈 (lazy init)."""
        if self._style_checker is None:
            from modules.core.pre_director_style_checker import PreDirectorStyleChecker

            self._style_checker = PreDirectorStyleChecker(self)
        return self._style_checker

    def check(self, content: str, content_type: str = "manuscript", context: dict[str, Any] = None) -> ChecklistResult:
        """
        체크리스트 실행

        Args:
            content: 검사할 콘텐츠
            content_type: "manuscript" 또는 "blueprint"
            context: 참조 컨텍스트 (blueprint, arc_data 등)

        Returns:
            ChecklistResult
        """
        if not self.enabled:
            return ChecklistResult(
                passed=True, items=[], fail_count=0, warning_count=0, summary="체크리스트 비활성화", blocking_reasons=[]
            )

        context = context or {}
        content = content or ""
        items = []

        if content_type == "manuscript":
            items.extend(self._check_manuscript(content, context))
        elif content_type == "blueprint":
            items.extend(self._check_blueprint(content, context))

        # 결과 집계
        fail_count = sum(1 for item in items if item.severity == CheckSeverity.FAIL)
        warning_count = sum(1 for item in items if item.severity == CheckSeverity.WARNING)
        blocking_reasons = [item.message for item in items if item.severity == CheckSeverity.FAIL]

        passed = fail_count == 0

        if passed and warning_count == 0:
            summary = "✅ 모든 체크 통과"
        elif passed:
            summary = f"⚠️ 경고 {warning_count}건 (통과)"
        else:
            summary = f"❌ 실패 {fail_count}건, 경고 {warning_count}건"

        return ChecklistResult(
            passed=passed,
            items=items,
            fail_count=fail_count,
            warning_count=warning_count,
            summary=summary,
            blocking_reasons=blocking_reasons,
        )

    def _check_manuscript(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        """원고 체크"""
        items = []
        items.extend(self._check_manuscript_length(manuscript))
        items.extend(self.manuscript_checker._check_dialogue_ratio(manuscript, context))
        items.extend(self._check_manuscript_paragraphs(manuscript))
        items.extend(self._check_manuscript_forbidden_patterns(manuscript))
        items.extend(self._check_manuscript_blueprint_alignment(manuscript, context))
        items.extend(self._check_manuscript_scope(manuscript, context))
        items.extend(self._check_manuscript_prev_linkage(manuscript, context))
        items.extend(self._run_manuscript_quality_checks(manuscript, context))
        # [IFC] Immutable fact packet-aware opening anchor check
        items.extend(self._check_immutable_fact_opening(manuscript, context))

        return items

    def _check_manuscript_length(self, manuscript: str) -> list[CheckItem]:
        items = []
        length = len(manuscript)

        if length < self.MANUSCRIPT_LENGTH["min"]:
            items.append(
                CheckItem(
                    category=CheckCategory.LENGTH,
                    name="최소 길이",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"원고 길이 부족: {length}자 (최소 {self.MANUSCRIPT_LENGTH['min']}자)",
                )
            )
        elif length < self.MANUSCRIPT_LENGTH["warning_min"]:
            items.append(
                CheckItem(
                    category=CheckCategory.LENGTH,
                    name="권장 길이",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"원고가 다소 짧음: {length}자",
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.LENGTH,
                    name="길이",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=f"길이 적절: {length}자",
                )
            )

        if length > self.MANUSCRIPT_LENGTH["max"]:
            items.append(
                CheckItem(
                    category=CheckCategory.SCOPE,
                    name="최대 길이",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"원고 길이 초과: {length}자 (최대 {self.MANUSCRIPT_LENGTH['max']}자)",
                )
            )
        elif length > self.MANUSCRIPT_LENGTH["warning_max"]:
            items.append(
                CheckItem(
                    category=CheckCategory.SCOPE,
                    name="권장 최대 길이",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"원고가 다소 김: {length}자",
                )
            )

        return items

    def _check_manuscript_paragraphs(self, manuscript: str) -> list[CheckItem]:
        items = []
        paragraphs = [p for p in manuscript.split("\n\n") if p.strip()]
        min_paragraphs = self.MANUSCRIPT_REQUIRED["paragraphs"][0]

        if len(paragraphs) < min_paragraphs:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="문단 수",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"문단 부족: {len(paragraphs)}개 (최소 {min_paragraphs}개)",
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="문단 수",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=f"문단 적절: {len(paragraphs)}개",
                )
            )

        return items

    def _check_manuscript_forbidden_patterns(self, manuscript: str) -> list[CheckItem]:
        items = []

        for pattern, desc in self.FORBIDDEN_PATTERNS["manuscript"]:
            if re.search(pattern, manuscript, re.IGNORECASE):
                items.append(
                    CheckItem(
                        category=CheckCategory.FORBIDDEN_PATTERNS,
                        name=desc,
                        passed=False,
                        severity=CheckSeverity.FAIL,
                        message=desc,
                    )
                )

        return items

    def _check_manuscript_blueprint_alignment(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        items = []
        blueprint = context.get("blueprint", {})

        if blueprint and isinstance(blueprint, dict):
            scene_breakdown = blueprint.get("scene_breakdown", {})
            if scene_breakdown and isinstance(scene_breakdown, dict):
                # [Gap-2] 씬 헤더 계약 검증
                items.extend(self.manuscript_checker._check_scene_header_contract(manuscript, scene_breakdown))

                # [V60.5] 씬별 반영률 정량 측정
                scene_metrics = self.manuscript_checker._measure_scene_reflection(manuscript, scene_breakdown)
                items.extend(scene_metrics["check_items"])

                # 전체 반영률 기반 판정
                materialization = measure_manuscript_scene_materialization(manuscript, blueprint)
                overall_ratio = materialization.overall_ratio
                if materialization.scene_count <= 3:
                    if materialization.reflected_scenes == 0:
                        items.append(
                            CheckItem(
                                category=CheckCategory.BLUEPRINT_MATCH,
                                name="씬 반영",
                                passed=True,
                                severity=CheckSeverity.WARNING,
                                message=(
                                    f"저씬 구조 핵심 의무 장면화 약함: {materialization.reflected_scenes}/"
                                    f"{materialization.scene_count} 씬, 후반부 핵심 씬 체류 부족 (Director 판단 위임)"
                                ),
                            )
                        )
                    else:
                        items.append(
                            CheckItem(
                                category=CheckCategory.BLUEPRINT_MATCH,
                                name="씬 반영",
                                passed=True,
                                severity=CheckSeverity.PASS,
                                message=(
                                    f"저씬 구조 핵심 의무 장면화 양호: {materialization.reflected_scenes}/"
                                    f"{materialization.scene_count} 씬, 후반부 핵심 씬 체류 "
                                    f"{'유지' if materialization.tail_scene_reflected else '보통'}"
                                ),
                            )
                        )
                elif overall_ratio < 0.3:
                    # [TF-51] FAIL→WARNING 다운그레이드: Python 키워드 매칭 오탐 과다,
                    # Director(LLM)가 Blueprint 원문 대조로 씬 커버리지 판단
                    items.append(
                        CheckItem(
                            category=CheckCategory.BLUEPRINT_MATCH,
                            name="씬 반영",
                            passed=True,
                            severity=CheckSeverity.WARNING,
                            message=f"Blueprint 씬 반영 부족: {overall_ratio:.0%} (최소 30%) (Director 판단 위임)",
                        )
                    )
                elif overall_ratio < 0.5:
                    items.append(
                        CheckItem(
                            category=CheckCategory.BLUEPRINT_MATCH,
                            name="씬 반영",
                            passed=True,
                            severity=CheckSeverity.WARNING,
                            message=f"Blueprint 씬 반영 낮음: {overall_ratio:.0%}",
                        )
                    )
                else:
                    items.append(
                        CheckItem(
                            category=CheckCategory.BLUEPRINT_MATCH,
                            name="씬 반영",
                            passed=True,
                            severity=CheckSeverity.PASS,
                            message=f"Blueprint 씬 반영 양호: {overall_ratio:.0%}",
                        )
                    )

                # [V60.4] 씬 밀도 균등성 검사
                scene_density_check = self.manuscript_checker._check_scene_density_balance(manuscript, scene_breakdown)
                items.extend(scene_density_check)

            # [TF-2] Opening-Anchor 대조 — blueprint 시작 장소/시간과 원고 첫 600자 비교
            _start_loc = blueprint.get("start_location", "")
            if _start_loc and isinstance(_start_loc, str) and len(_start_loc) >= 2:
                _opening_text = manuscript[:600] if len(manuscript) > 600 else manuscript
                _loc_keywords = re.findall(r"[\w가-힣]{2,}", _start_loc)[:5]
                _loc_matched = [kw for kw in _loc_keywords if kw in _opening_text]
                _specific_keywords = [kw for kw in _loc_keywords if kw not in self._GENERIC_LOCATION_TOKENS]
                _specific_matched = [kw for kw in _specific_keywords if kw in _opening_text]
                if _loc_keywords and (len(_loc_matched) == 0 or (_specific_keywords and len(_specific_matched) == 0)):
                    # [Gap-1] 일반 장소명만 겹치고 핵심 앵커가 전부 사라진 경우도 hard fail
                    _fail_basis = (
                        f"핵심 위치 토큰 0/{len(_specific_keywords)}개"
                        if _specific_keywords and len(_specific_matched) == 0
                        else f"0/{len(_loc_keywords)}개"
                    )
                    items.append(
                        CheckItem(
                            category=CheckCategory.BLUEPRINT_MATCH,
                            name="시작 장소 불일치",
                            passed=False,
                            severity=CheckSeverity.FAIL,
                            message=(
                                f"Blueprint 시작 장소 '{_start_loc[:60]}' 키워드가 원고 첫 600자에서 "
                                f"{_fail_basis} 발견됨 — 시작 계약 완전 위반"
                            ),
                        )
                    )
                elif len(_loc_matched) < max(1, len(_loc_keywords) // 2):
                    # 부분 불일치 → WARNING (Director 판단 위임)
                    items.append(
                        CheckItem(
                            category=CheckCategory.BLUEPRINT_MATCH,
                            name="시작 장소 불일치",
                            passed=True,
                            severity=CheckSeverity.WARNING,
                            message=(
                                f"Blueprint 시작 장소 '{_start_loc[:60]}' 키워드가 원고 첫 600자에서 "
                                f"{len(_loc_matched)}/{len(_loc_keywords)}개만 발견됨 (Director 판단 위임)"
                            ),
                        )
                    )

            ending_hook = blueprint.get("ending_hook") or blueprint.get("cliffhanger", "")
            if ending_hook and isinstance(ending_hook, str) and len(ending_hook) > 5:
                hook_keywords = re.findall(r"[\w가-힣]{2,}", ending_hook)[:3]
                ending_part = manuscript[-600:] if len(manuscript) > 600 else manuscript

                if hook_keywords and not any(kw in ending_part for kw in hook_keywords):
                    items.append(
                        CheckItem(
                            category=CheckCategory.BLUEPRINT_MATCH,
                            name="엔딩 훅",
                            passed=True,  # 경고만
                            severity=CheckSeverity.WARNING,
                            message="ending_hook이 원고 끝에서 감지되지 않음",
                        )
                    )

        return items

    def _check_manuscript_scope(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        items = []
        length = len(manuscript)
        blueprint = context.get("blueprint", {})

        if blueprint and isinstance(blueprint, dict):
            _sb = blueprint.get("scene_breakdown", {})
            scene_count = len(_sb) if isinstance(_sb, dict | list) else 0  # [TF-R2-S3-01]
            if scene_count > 0:
                profile = build_blueprint_scene_profile(blueprint)
                expected_max = estimate_scene_flex_budget(
                    scene_count=scene_count,
                    total_keywords=profile.total_keywords if profile.scene_count == scene_count else 0,
                    tail_keyword_count=profile.tail_keyword_count if profile.scene_count == scene_count else 0,
                )
                if length > expected_max:
                    items.append(
                        CheckItem(
                            category=CheckCategory.SCOPE,
                            name="범위 초과",
                            passed=True,  # 경고만
                            severity=CheckSeverity.WARNING,
                            message=f"의무 밀도 보정 예상 범위 초과: {length}자 (예상 최대 {int(expected_max)}자)",
                        )
                    )

        return items

    def _check_manuscript_prev_linkage(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        items = []
        prev_manuscript = context.get("prev_manuscript", "")

        if prev_manuscript and len(prev_manuscript) > 500:
            # 직전 화 마지막 500자에서 핵심 단어 추출
            prev_ending = prev_manuscript[-500:]
            prev_keywords = set(re.findall(r"[\w가-힣]{3,}", prev_ending))

            # 현재 화 시작 500자에서 단어 추출
            curr_start = manuscript[:500]
            curr_keywords = set(re.findall(r"[\w가-힣]{3,}", curr_start))

            overlap = len(prev_keywords & curr_keywords)
            if overlap < 2:
                items.append(
                    CheckItem(
                        category=CheckCategory.CONTINUITY,
                        name="직전 화 연결",
                        passed=True,  # 경고만
                        severity=CheckSeverity.WARNING,
                        message="직전 화 엔딩과의 연결이 약함",
                    )
                )

        return items

    def _check_immutable_fact_opening(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        """[IFC] Check manuscript opening against immutable fact packet anchors.

        If the blueprint specifies a start_location, verify the manuscript's
        first 600 chars contain a related keyword. This catches the most
        common hard-fact drift (e.g., Gangnam blueprint → Yeouido manuscript).
        """
        items: list[CheckItem] = []
        blueprint = context.get("blueprint")
        if not isinstance(blueprint, dict):
            return items

        start_loc = str(blueprint.get("start_location", "") or "").strip()
        if not start_loc or len(start_loc) < 2:
            return items

        ms_head = manuscript[:600]
        # Extract location keywords (2+ char Korean substrings from start_loc)
        loc_keywords = re.findall(r"[가-힣]{2,}", start_loc)
        if not loc_keywords:
            return items

        # Check if any significant location keyword appears in the opening
        found = any(kw in ms_head for kw in loc_keywords if len(kw) >= 2)
        if not found:
            items.append(
                CheckItem(
                    category=CheckCategory.CONTINUITY,
                    name="시작 장소 불변 계약",
                    passed=True,  # WARNING only — Director is final judge
                    severity=CheckSeverity.WARNING,
                    message=f"[IFC] 원고 시작부가 Blueprint 시작 장소({start_loc})와 불일치 가능",
                )
            )

        return items

    def _run_manuscript_quality_checks(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        items = []
        items.extend(self.narrative_checker._check_narrative_flow(manuscript, context))
        items.extend(self.narrative_checker._check_npc_behavior_jump(manuscript, context))
        items.extend(self.style_checker._check_sentence_variety(manuscript))
        items.extend(self.style_checker._check_pacing_rhythm(manuscript))
        items.extend(self.narrative_checker._check_setting_keywords(manuscript, context))
        items.extend(self.manuscript_checker._check_cliche_density(manuscript))
        return items

    # [R5-2c] Backward-compatible thin wrappers
    def _check_narrative_flow(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        return self.narrative_checker._check_narrative_flow(manuscript, context)

    def _check_npc_behavior_jump(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        return self.narrative_checker._check_npc_behavior_jump(manuscript, context)

    def _check_sentence_variety(self, manuscript: str) -> list[CheckItem]:
        return self.style_checker._check_sentence_variety(manuscript)

    def _check_pacing_rhythm(self, manuscript: str) -> list[CheckItem]:
        return self.style_checker._check_pacing_rhythm(manuscript)

    def _check_setting_keywords(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        return self.narrative_checker._check_setting_keywords(manuscript, context)

    def _check_blueprint(self, content: str, context: dict[str, Any]) -> list[CheckItem]:
        """블루프린트 체크"""
        items = []

        # Blueprint가 dict인지 확인
        if isinstance(content, dict):
            bp = content
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = content
            try:
                bp = json.loads(content)
            except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse failure
                bp = {}
                items.append(
                    CheckItem(
                        category=CheckCategory.STRUCTURE,
                        name="JSON 파싱",
                        passed=False,
                        severity=CheckSeverity.FAIL,
                        message="Blueprint JSON 파싱 실패",
                    )
                )
                return items

        # 1. 필수 필드 체크
        required_fields = ["integrated_scenario", "scene_breakdown"]
        for field in required_fields:
            if field not in bp or not bp[field]:
                items.append(
                    CheckItem(
                        category=CheckCategory.REQUIRED_FIELDS,
                        name=f"필드: {field}",
                        passed=False,
                        severity=CheckSeverity.FAIL,
                        message=f"필수 필드 누락: {field}",
                    )
                )
            else:
                items.append(
                    CheckItem(
                        category=CheckCategory.REQUIRED_FIELDS,
                        name=f"필드: {field}",
                        passed=True,
                        severity=CheckSeverity.PASS,
                        message=f"필드 존재: {field}",
                    )
                )

        # 2. 시나리오 길이 체크
        scenario = bp.get("integrated_scenario", "")
        scenario_len = len(str(scenario))
        if scenario_len < self.BLUEPRINT_LENGTH["scenario_min"]:
            items.append(
                CheckItem(
                    category=CheckCategory.LENGTH,
                    name="시나리오 길이",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"시나리오 길이 부족: {scenario_len}자",
                )
            )

        # 3. 씬 개수 체크
        scene_breakdown = bp.get("scene_breakdown", {})
        if not isinstance(scene_breakdown, dict):
            scene_breakdown = {}
        scene_gate_passed, scene_count, scene_reason, scene_feedback = evaluate_stage3_scene_cardinality(
            scene_breakdown,
            scenario,
        )

        if not scene_gate_passed:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="씬 개수",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"{scene_reason} - {scene_feedback}" if scene_feedback else scene_reason,
                )
            )
        elif scene_count <= 3:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="씬 개수",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"저씬수 예외 허용: {scene_count}개 (밀도/구체성 기준 충족)",
                )
            )
        elif scene_count > 8:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="씬 개수",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"씬 과다: {scene_count}개 (권장 4-7개)",
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="씬 개수",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=f"씬 적절: {scene_count}개",
                )
            )

        # 4. 금지 패턴 체크
        for pattern, desc in self.FORBIDDEN_PATTERNS["blueprint"]:
            if re.search(pattern, content_str, re.IGNORECASE):
                items.append(
                    CheckItem(
                        category=CheckCategory.FORBIDDEN_PATTERNS,
                        name=desc,
                        passed=False,
                        severity=CheckSeverity.FAIL,
                        message=desc,
                    )
                )

        # 5. 엔딩 훅 체크
        ending_hook = bp.get("ending_hook") or bp.get("cliffhanger", "")
        if not ending_hook:
            items.append(
                CheckItem(
                    category=CheckCategory.REQUIRED_FIELDS,
                    name="엔딩 훅",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message="ending_hook 없음",
                )
            )

        return items

    def get_feedback(self, result: ChecklistResult) -> str:
        """체크리스트 결과를 피드백 문자열로 변환"""
        if result.passed and result.warning_count == 0:
            return ""

        lines = ["[V53.4 Pre-Director Checklist]"]
        lines.append(result.summary)

        if result.blocking_reasons:
            lines.append("\n❌ 차단 사유:")
            for reason in result.blocking_reasons:
                lines.append(f"  - {reason}")

        warning_items = [item for item in result.items if item.severity == CheckSeverity.WARNING]
        if warning_items:
            lines.append("\n⚠️ 경고:")
            for item in warning_items[:3]:
                lines.append(f"  - {item.message}")

        return "\n".join(lines)
