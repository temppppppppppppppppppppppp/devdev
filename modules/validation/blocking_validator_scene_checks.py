"""[R5-2a] BlockingValidator scene checks submodule."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from modules.core.constants import ManuscriptLimits
from modules.validation.threshold_helper import _threshold

if TYPE_CHECKING:
    from modules.validation.blocking_validator import BlockingValidator


class BlockingValidatorSceneChecks:
    """Scene-level blocking checks for structure/completeness/cliffhanger."""

    def __init__(self, host: BlockingValidator) -> None:
        self.host = host

    def _check_minimum_length(self, manuscript: str, context: dict) -> dict:
        """최소 분량 체크"""
        mode = context.get("mode", "MANUSCRIPT")

        if mode == "BLUEPRINT":
            threshold = 500
        else:  # MANUSCRIPT
            threshold = ManuscriptLimits.MIN_LENGTH  # [V64.P4]

        length = len(manuscript)

        if length < threshold:
            return {
                "check": "minimum_length",
                "passed": False,
                "reason": f"분량 미달: {length}자 (최소 {threshold}자)",
                "severity": "CRITICAL",
                "current_length": length,
                "threshold": threshold,
            }

        return {"check": "minimum_length", "passed": True}

    def _check_required_scenes(self, manuscript: str, context: dict) -> dict:
        """필수 씬 포함 체크 (MANUSCRIPT 모드만)"""
        blueprint = context.get("blueprint", {})
        scene_breakdown = blueprint.get("scene_breakdown", {})

        if not scene_breakdown:
            # Blueprint 없으면 체크 불가 → 통과 처리
            return {"check": "required_scenes", "passed": True}

        # 최소 4개 장면이 원고에 반영되었는지 체크
        scene_count = len(scene_breakdown)
        min_required = 4

        # 각 Scene의 키워드가 원고에 있는지 체크
        scenes_found = 0
        for scene_name, scene_desc in scene_breakdown.items():
            # Scene 설명에서 핵심 키워드 추출 (간단한 휴리스틱)
            # 예: "주인공이 객잔에 도착" → ["객잔", "도착"]
            if isinstance(scene_desc, dict):  # [V70] dict 타입 방어
                scene_desc = scene_desc.get("description", scene_desc.get("content", str(scene_desc)))
            keywords = self.host.consistency_checks._extract_keywords(str(scene_desc))

            # 키워드 중 하나라도 원고에 있으면 Scene 반영됨
            if any(kw in manuscript for kw in keywords if kw):
                scenes_found += 1

        if scenes_found < min_required:
            return {
                "check": "required_scenes",
                "passed": False,
                "reason": f"필수 씬 누락: {scenes_found}/{scene_count} 반영 (최소 {min_required}개)",
                "severity": "HIGH",
                "scenes_found": scenes_found,
                "total_scenes": scene_count,
            }

        return {"check": "required_scenes", "passed": True}

    def _check_scope_overflow(self, manuscript: str, context: dict) -> dict:
        """
        [V49] 씬 범위 초과 체크 - Writer가 Blueprint 범위를 넘어서 과잉 생성하는 것을 방지

        [V55.5] 기준 강화: 1.3배 → 1.2배
        Blueprint에 6개 씬이 있는데 원고가 과잉 생성되면 REJECT
        - 씬당 평균 700-1200자 가정
        - 씬 개수 * 1500자 * 1.2배를 초과하면 범위 초과로 판단
        """
        blueprint = context.get("blueprint", {})
        blueprint_text = context.get("blueprint_text", "")  # 원본 텍스트

        # 1. 씬 개수 추출 (두 가지 방법 시도)
        scene_count = 0

        # 방법 1: scene_breakdown dict에서 추출
        scene_breakdown = blueprint.get("scene_breakdown", {})
        if scene_breakdown and isinstance(scene_breakdown, dict):
            scene_count = len(scene_breakdown)

        # 방법 2: blueprint_text에서 "## scene_" 패턴 카운트
        if scene_count == 0 and blueprint_text:
            scene_pattern = r"##\s*scene_\d+"
            matches = re.findall(scene_pattern, blueprint_text, re.IGNORECASE)
            scene_count = len(matches)

        # 방법 3: blueprint dict 자체에서 scenes 키 확인
        if scene_count == 0:
            scenes = blueprint.get("scenes", [])
            if isinstance(scenes, list):
                scene_count = len(scenes)

        # 씬 개수를 못 찾으면 체크 불가 → 통과
        if scene_count == 0:
            return {"check": "scope_overflow", "passed": True, "reason": "씬 개수 추출 불가 - 체크 스킵"}

        # 2. 원고 길이 vs 예상 범위 비교
        manuscript_length = len(manuscript)

        # 씬당 최대 허용 글자 수 (충분히 여유있게 설정)
        max_chars_per_scene = _threshold("scope.chars_per_scene", 1500)
        max_allowed_length = scene_count * max_chars_per_scene

        # 3. 범위 초과 판정
        if manuscript_length > max_allowed_length:
            overflow_ratio = manuscript_length / max_allowed_length

            # [V55.5] 1.2배 초과 시 REJECT (예: 6개 씬에 10800자 이상)
            if overflow_ratio > _threshold("scope.overflow_ratio", 1.2):
                return {
                    "check": "scope_overflow",
                    "passed": False,
                    "reason": f"Blueprint 범위 초과: {manuscript_length}자 (씬 {scene_count}개 기준 최대 {max_allowed_length}자, {overflow_ratio:.1f}배 초과)",
                    "severity": "HIGH",
                    "details": {
                        "manuscript_length": manuscript_length,
                        "scene_count": scene_count,
                        "max_allowed": max_allowed_length,
                        "overflow_ratio": round(overflow_ratio, 2),
                    },
                    "suggestion": "Writer가 Arc 전체를 한 화에 압축 생성한 것으로 보입니다. Blueprint의 씬 분해(Scene Breakdown)만 따라 작성하세요.",
                }

            # [V55.5] 1.0~1.2배는 경고만 (통과)
            return {
                "check": "scope_overflow",
                "passed": True,
                "warning": f"분량 약간 초과: {manuscript_length}자 (권장 {max_allowed_length}자 이하)",
                "overflow_ratio": round(overflow_ratio, 2),
            }

        return {"check": "scope_overflow", "passed": True}

    def _check_scene_completeness(self, manuscript: str, context: dict) -> dict:
        """
        [V59] 씬별 완성도 체크 - 각 씬이 최소 분량을 충족하는지 검증

        Blueprint의 각 씬에 대해:
        - 최소 300자 이상의 내용이 있어야 함
        - 너무 짧게 넘어가는 씬이 있으면 WARNING
        - 반 이상의 씬이 미달이면 REJECT
        """
        blueprint = context.get("blueprint", {})
        scene_breakdown = blueprint.get("scene_breakdown", {})

        if not scene_breakdown or not isinstance(scene_breakdown, dict):
            return {"check": "scene_completeness", "passed": True, "reason": "Blueprint 씬 정보 없음 - 체크 스킵"}

        scene_count = len(scene_breakdown)
        if scene_count == 0:
            return {"check": "scene_completeness", "passed": True}

        # 씬 키워드별로 원고 분할 시도
        scene_analysis = []
        min_scene_length = _threshold("scene.min_scene_length", 300)

        for scene_name, scene_desc in scene_breakdown.items():
            if isinstance(scene_desc, dict):  # [V70] dict 타입 방어
                scene_desc = scene_desc.get("description", scene_desc.get("content", str(scene_desc)))
            keywords = self.host.consistency_checks._extract_keywords(str(scene_desc), max_keywords=5)

            # 키워드 주변 텍스트 분량 측정
            found_length = 0
            for kw in keywords:
                if kw and kw in manuscript:
                    # 키워드 위치 찾기
                    idx = manuscript.find(kw)
                    if idx != -1:
                        # 키워드 전후 500자 범위를 해당 씬으로 간주
                        start = max(0, idx - 250)
                        end = min(len(manuscript), idx + 250)
                        found_length = max(found_length, end - start)

            scene_analysis.append(
                {"scene": scene_name, "found_length": found_length, "is_complete": found_length >= min_scene_length}
            )

        # 완성된 씬 비율 계산
        complete_scenes = sum(1 for s in scene_analysis if s["is_complete"])
        incomplete_scenes = [s for s in scene_analysis if not s["is_complete"] and s["found_length"] > 0]

        # 50% 이상 씬이 미달이면 REJECT
        if complete_scenes < scene_count * 0.5:
            return {
                "check": "scene_completeness",
                "passed": False,
                "reason": f"씬 완성도 부족: {complete_scenes}/{scene_count} 씬만 완성 (최소 50% 필요)",
                "severity": "HIGH",
                "details": {
                    "complete_scenes": complete_scenes,
                    "total_scenes": scene_count,
                    "incomplete": [s["scene"] for s in incomplete_scenes],
                    "min_scene_length": min_scene_length,
                },
                "suggestion": "각 씬에 충분한 분량(최소 300자)을 할당하세요. 특히 다음 씬이 부족합니다: "
                + ", ".join([s["scene"] for s in incomplete_scenes[:3]]),
            }

        # 일부 미달이면 WARNING (통과)
        if incomplete_scenes:
            return {
                "check": "scene_completeness",
                "passed": True,
                "warning": f"일부 씬 분량 부족: {len(incomplete_scenes)}개 씬이 300자 미만",
                "details": {"incomplete_scenes": [s["scene"] for s in incomplete_scenes]},
            }

        return {"check": "scene_completeness", "passed": True}

    def _check_cliffhanger_ending(self, manuscript: str, context: dict) -> dict:
        """
        [V59] 클리프행어 엔딩 필수 검증 - 연재물의 핵심 요소

        원고 마지막 부분(500자)에서 긴장감/기대감 요소 확인:
        - 위기 상황 암시
        - 의문/미스터리 제시
        - 새로운 인물/사건 등장
        - 결정적 순간 직전 중단

        Blueprint에 cliffhanger 지시가 있으면 필수 검증
        """
        blueprint = context.get("blueprint", {})

        # Blueprint에서 cliffhanger 관련 지시 확인
        cliffhanger_required = False
        cliffhanger_hint = ""

        # 다양한 키에서 cliffhanger 찾기
        for key in ["cliffhanger", "ending", "ending_hook", "episode_ending"]:
            if key in blueprint:
                value = blueprint.get(key, "")
                if value:
                    cliffhanger_required = True
                    cliffhanger_hint = str(value)[:100]
                    break

        # Blueprint에 명시적 cliffhanger 지시가 없으면 기본 체크만
        if not cliffhanger_required:
            # 기본 체크: 원고 끝이 너무 평이하면 경고
            ending_text = manuscript[-500:] if len(manuscript) > 500 else manuscript

            # 평이한 엔딩 패턴 (문제가 될 수 있음)
            flat_ending_patterns = [
                r"잠들었다[.。]?\s*$",
                r"잠이 들었다[.。]?\s*$",
                r"평화로웠다[.。]?\s*$",
                r"아무 일 없이[.。]?\s*$",
                r"무사히 끝났다[.。]?\s*$",
                r"돌아갔다[.。]?\s*$",
                r"끝이었다[.。]?\s*$",
            ]

            for pattern in flat_ending_patterns:
                if re.search(pattern, ending_text):
                    return {
                        "check": "cliffhanger_ending",
                        "passed": True,  # 경고만 (Blueprint 미지시 시)
                        "warning": "엔딩이 평이함 - 클리프행어 요소 권장",
                        "matched_pattern": pattern,
                        "suggestion": "독자의 다음 화 기대감을 위해 긴장감 있는 엔딩 추가 고려",
                        "cliffhanger_strength": 15,  # [V60.7] 평이한 엔딩 = 낮은 점수
                        "strength_grade": "D",
                    }

            return {
                "check": "cliffhanger_ending",
                "passed": True,
                "cliffhanger_strength": 50,  # [V60.7] 기본 통과 = 중간 점수
                "strength_grade": "B",
            }

        # Blueprint에 cliffhanger 지시가 있는 경우 필수 검증
        ending_text = manuscript[-800:] if len(manuscript) > 800 else manuscript

        # 클리프행어 긍정 패턴 (있어야 함)
        cliffhanger_patterns = [
            # 위기/긴장
            r"그때[,]?\s",
            r"순간[,]?\s",
            r"갑자기",
            r"돌연",
            r"느닷없이",
            r"바로\s+그때",
            # 등장/출현
            r"나타났다",
            r"등장했다",
            r"모습을\s+드러",
            r"그림자가",
            r"발소리가",
            # 의문/미스터리
            r'\?["\']?\s*$',  # 의문문으로 끝남
            r"누구[인지]?",
            r"무엇[인지]?",
            r"어째서",
            r"왜[?]",
            # 긴박함
            r"다가오고\s+있",
            r"시작이[었]?다",
            r"끝이\s+아니",
            r"시작에\s+불과",
            r"이제부터",
            # 반전/충격
            r"그러나",
            r"하지만",
            r"그런데",
            r"예상[과]?\s+달리",
            r"뜻밖에[도]?",
            # 대화 긴장
            r"말을\s+끊",
            r"입을\s+열",
            r"목소리가\s+들려",
        ]

        has_cliffhanger = False
        matched_patterns = []

        for pattern in cliffhanger_patterns:
            if re.search(pattern, ending_text):
                has_cliffhanger = True
                matched_patterns.append(pattern)

        # Blueprint의 cliffhanger 키워드가 반영되었는지도 체크
        if cliffhanger_hint:
            hint_keywords = self.host.consistency_checks._extract_keywords(cliffhanger_hint, max_keywords=5)
            hint_reflected = any(kw and kw in ending_text for kw in hint_keywords)
            if hint_reflected:
                has_cliffhanger = True

        if not has_cliffhanger:
            return {
                "check": "cliffhanger_ending",
                "passed": False,
                "reason": "Blueprint 지시된 클리프행어 누락",
                "severity": "MEDIUM",
                "details": {
                    "blueprint_cliffhanger": cliffhanger_hint,
                    "ending_excerpt": ending_text[-200:],
                },
                "suggestion": f"Blueprint에서 지시한 클리프행어를 원고 끝에 반영하세요: '{cliffhanger_hint}'",
                "quick_fixes": [
                    "위기 상황 암시로 마무리 (예: '그때, 문이 열렸다.')",
                    "의문문으로 마무리 (예: '과연 그의 정체는?')",
                    "새로운 인물 등장 암시 (예: '그림자가 다가오고 있었다.')",
                    "긴박한 상황 직전 중단 (예: '바로 그 순간이었다.')",
                ],
                "cliffhanger_strength": 0,  # [V60.7] 누락 = 0점
                "strength_grade": "F",
            }

        # [V60.7] Cliffhanger 강도 점수 계산
        strength_score = self._calculate_cliffhanger_strength(ending_text, matched_patterns, cliffhanger_hint)

        return {
            "check": "cliffhanger_ending",
            "passed": True,
            "cliffhanger_detected": True,
            "matched_patterns": matched_patterns[:3],  # 상위 3개만
            "cliffhanger_strength": strength_score,  # [V60.7] 0-100 강도 점수
            "strength_grade": self._get_strength_grade(strength_score),
        }

    def _calculate_cliffhanger_strength(
        self, ending_text: str, matched_patterns: list[str], blueprint_hint: str
    ) -> int:
        """
        [V60.7] Cliffhanger 강도 점수 계산 (0-100)

        점수 구성:
        - 기본 점수: 매칭된 패턴 수 × 15 (최대 60)
        - 위치 보너스: 마지막 100자 내 패턴 +20
        - Blueprint 힌트 반영 보너스: +15
        - 긴장감 키워드 보너스: +5 (각각)
        """
        score = 0

        # 1. 기본 점수: 패턴 매칭 수
        pattern_count = len(matched_patterns)
        score += min(pattern_count * 15, 60)

        # 2. 위치 보너스: 마지막 100자 내 패턴 존재
        last_100 = ending_text[-100:] if len(ending_text) > 100 else ending_text
        has_ending_pattern = False
        for pattern in matched_patterns:
            try:
                if re.search(pattern, last_100):
                    has_ending_pattern = True
                    break
            except re.error:
                continue

        if has_ending_pattern:
            score += 20

        # 3. Blueprint 힌트 반영 보너스
        if blueprint_hint:
            hint_keywords = [w for w in blueprint_hint.split() if len(w) >= 2][:5]
            reflected = sum(1 for kw in hint_keywords if kw in ending_text)
            if reflected > 0:
                score += min(reflected * 5, 15)

        # 4. 고강도 긴장 키워드 보너스
        high_tension_keywords = [
            "죽음",
            "위기",
            "절체절명",
            "최후",
            "비밀",
            "충격",
            "반전",
            "배신",
            "정체",
            "진실",
            "비극",
            "운명",
            "결전",
            "대결",
        ]
        tension_count = sum(1 for kw in high_tension_keywords if kw in ending_text)
        score += min(tension_count * 3, 15)

        return min(score, 100)

    def _get_strength_grade(self, score: int) -> str:
        """[V60.7] 강도 점수를 등급으로 변환"""
        if score >= 80:
            return "S"  # 매우 강함
        elif score >= 60:
            return "A"  # 강함
        elif score >= 40:
            return "B"  # 보통
        elif score >= 20:
            return "C"  # 약함
        else:
            return "D"  # 매우 약함
