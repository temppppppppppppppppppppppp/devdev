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

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re
from modules.core.constants import ManuscriptLimits  # [V64.P4]


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
    items: List[CheckItem]
    fail_count: int
    warning_count: int
    summary: str
    blocking_reasons: List[str]  # FAIL 사유들


class PreDirectorChecklist:
    """사전 체크리스트 시스템"""

    # [V64.P4] 원고 최소/최대 길이 — ManuscriptLimits 참조
    MANUSCRIPT_LENGTH = {
        "min": ManuscriptLimits.MIN_LENGTH,
        "max": ManuscriptLimits.MAX_LENGTH,
        "warning_min": ManuscriptLimits.WARNING_LENGTH,
        "warning_max": 12000
    }

    # 블루프린트 최소 길이
    BLUEPRINT_LENGTH = {
        "min": 500,
        "scenario_min": 300
    }

    # 금지 패턴 (명백한 오류)
    FORBIDDEN_PATTERNS = {
        "manuscript": [
            (r'\[TODO\]', "TODO 마커가 남아있음"),
            (r'\[PLACEHOLDER\]', "플레이스홀더가 남아있음"),
            (r'제\s*\d+\s*화\s*끝', "화 끝 마커가 본문에 포함됨"),
            (r'```', "코드 블록 마커가 포함됨"),
            (r'\{[a-zA-Z_]+\}', "템플릿 변수가 치환되지 않음"),
        ],
        "blueprint": [
            (r'\[TODO\]', "TODO 마커가 남아있음"),
            (r'\{[a-zA-Z_]+\}', "템플릿 변수가 치환되지 않음"),
        ]
    }

    # 필수 요소 (원고)
    MANUSCRIPT_REQUIRED = {
        "dialogue": (4, "대화가 최소 4개 이상 있어야 함"),
        "paragraphs": (5, "문단이 최소 5개 이상 있어야 함"),
    }

    def __init__(self):
        self.enabled = True

    def check(
        self,
        content: str,
        content_type: str = "manuscript",
        context: Dict[str, Any] = None
    ) -> ChecklistResult:
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
                passed=True,
                items=[],
                fail_count=0,
                warning_count=0,
                summary="체크리스트 비활성화",
                blocking_reasons=[]
            )

        context = context or {}
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
            blocking_reasons=blocking_reasons
        )

    def _check_manuscript(
        self,
        manuscript: str,
        context: Dict[str, Any]
    ) -> List[CheckItem]:
        """원고 체크"""
        items = []

        # 1. 길이 체크
        length = len(manuscript)
        if length < self.MANUSCRIPT_LENGTH["min"]:
            items.append(CheckItem(
                category=CheckCategory.LENGTH,
                name="최소 길이",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"원고 길이 부족: {length}자 (최소 {self.MANUSCRIPT_LENGTH['min']}자)"
            ))
        elif length < self.MANUSCRIPT_LENGTH["warning_min"]:
            items.append(CheckItem(
                category=CheckCategory.LENGTH,
                name="권장 길이",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"원고가 다소 짧음: {length}자"
            ))
        else:
            items.append(CheckItem(
                category=CheckCategory.LENGTH,
                name="길이",
                passed=True,
                severity=CheckSeverity.PASS,
                message=f"길이 적절: {length}자"
            ))

        if length > self.MANUSCRIPT_LENGTH["max"]:
            items.append(CheckItem(
                category=CheckCategory.SCOPE,
                name="최대 길이",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"원고 길이 초과: {length}자 (최대 {self.MANUSCRIPT_LENGTH['max']}자)"
            ))
        elif length > self.MANUSCRIPT_LENGTH["warning_max"]:
            items.append(CheckItem(
                category=CheckCategory.SCOPE,
                name="권장 최대 길이",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"원고가 다소 김: {length}자"
            ))

        # 2. 구조 체크 - 대화 (V60.5 고도화: 비율 분석 및 구체적 가이드)
        dialogue_ratio_check = self._check_dialogue_ratio(manuscript)
        items.extend(dialogue_ratio_check)

        # 3. 구조 체크 - 문단
        paragraphs = [p for p in manuscript.split('\n\n') if p.strip()]
        min_paragraphs = self.MANUSCRIPT_REQUIRED["paragraphs"][0]
        if len(paragraphs) < min_paragraphs:
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="문단 수",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"문단 부족: {len(paragraphs)}개 (최소 {min_paragraphs}개)"
            ))
        else:
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="문단 수",
                passed=True,
                severity=CheckSeverity.PASS,
                message=f"문단 적절: {len(paragraphs)}개"
            ))

        # 4. 금지 패턴 체크
        for pattern, desc in self.FORBIDDEN_PATTERNS["manuscript"]:
            if re.search(pattern, manuscript, re.IGNORECASE):
                items.append(CheckItem(
                    category=CheckCategory.FORBIDDEN_PATTERNS,
                    name=desc,
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=desc
                ))

        # 5. Blueprint 매칭 체크 - [V60.5] 씬별 정량 측정으로 고도화
        blueprint = context.get("blueprint", {})
        if blueprint and isinstance(blueprint, dict):
            scene_breakdown = blueprint.get("scene_breakdown", {})
            if scene_breakdown:
                # [V60.5] 씬별 반영률 정량 측정
                scene_metrics = self._measure_scene_reflection(manuscript, scene_breakdown)
                items.extend(scene_metrics['check_items'])

                # 전체 반영률 기반 판정
                overall_ratio = scene_metrics['overall_ratio']
                if overall_ratio < 0.3:
                    items.append(CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="씬 반영",
                        passed=False,
                        severity=CheckSeverity.FAIL,
                        message=f"Blueprint 씬 반영 부족: {overall_ratio:.0%} (최소 30%)"
                    ))
                elif overall_ratio < 0.5:
                    items.append(CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="씬 반영",
                        passed=True,
                        severity=CheckSeverity.WARNING,
                        message=f"Blueprint 씬 반영 낮음: {overall_ratio:.0%}"
                    ))
                else:
                    items.append(CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="씬 반영",
                        passed=True,
                        severity=CheckSeverity.PASS,
                        message=f"Blueprint 씬 반영 양호: {overall_ratio:.0%}"
                    ))

                # [V60.4] 씬 밀도 균등성 검사
                scene_density_check = self._check_scene_density_balance(
                    manuscript, scene_breakdown
                )
                items.extend(scene_density_check)

            # 엔딩 훅 체크
            ending_hook = blueprint.get("ending_hook") or blueprint.get("cliffhanger", "")
            if ending_hook and isinstance(ending_hook, str) and len(ending_hook) > 5:
                hook_keywords = re.findall(r'[\w가-힣]{2,}', ending_hook)[:3]
                ending_part = manuscript[-600:] if len(manuscript) > 600 else manuscript

                if hook_keywords and not any(kw in ending_part for kw in hook_keywords):
                    items.append(CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="엔딩 훅",
                        passed=True,  # 경고만
                        severity=CheckSeverity.WARNING,
                        message="ending_hook이 원고 끝에서 감지되지 않음"
                    ))

        # 6. 범위 초과 체크
        blueprint = context.get("blueprint", {})
        if blueprint and isinstance(blueprint, dict):
            scene_count = len(blueprint.get("scene_breakdown", {}))
            if scene_count > 0:
                expected_max = scene_count * 1500 * 1.4  # 씬당 1500자 + 40% 여유
                if length > expected_max:
                    items.append(CheckItem(
                        category=CheckCategory.SCOPE,
                        name="범위 초과",
                        passed=True,  # 경고만
                        severity=CheckSeverity.WARNING,
                        message=f"예상 범위 초과: {length}자 (예상 최대 {int(expected_max)}자)"
                    ))

        # 7. 연속성 기본 체크
        prev_manuscript = context.get("prev_manuscript", "")
        if prev_manuscript and len(prev_manuscript) > 500:
            # 직전 화 마지막 500자에서 핵심 단어 추출
            prev_ending = prev_manuscript[-500:]
            prev_keywords = set(re.findall(r'[\w가-힣]{3,}', prev_ending))

            # 현재 화 시작 500자에서 단어 추출
            curr_start = manuscript[:500]
            curr_keywords = set(re.findall(r'[\w가-힣]{3,}', curr_start))

            overlap = len(prev_keywords & curr_keywords)
            if overlap < 2:
                items.append(CheckItem(
                    category=CheckCategory.CONTINUITY,
                    name="직전 화 연결",
                    passed=True,  # 경고만
                    severity=CheckSeverity.WARNING,
                    message="직전 화 엔딩과의 연결이 약함"
                ))

        # 8. [V60.4] 서사 폭주/정체 검사
        narrative_flow_check = self._check_narrative_flow(manuscript, context)
        items.extend(narrative_flow_check)

        # 9. [V60.5] NPC 행동 급변 검사
        npc_behavior_check = self._check_npc_behavior_jump(manuscript, context)
        items.extend(npc_behavior_check)

        # 10. [V60.6] 문장 다양성 검사
        sentence_variety_check = self._check_sentence_variety(manuscript)
        items.extend(sentence_variety_check)

        # 11. [V60.6] 긴장-이완 리듬 검증
        pacing_check = self._check_pacing_rhythm(manuscript)
        items.extend(pacing_check)

        # 12. [V60.6] 설정 키워드 사전 검증
        setting_check = self._check_setting_keywords(manuscript, context)
        items.extend(setting_check)

        # 13. [V60.6] 클리셰 밀도 경고
        cliche_check = self._check_cliche_density(manuscript)
        items.extend(cliche_check)

        return items

    def _check_narrative_flow(
        self,
        manuscript: str,
        context: Dict[str, Any]
    ) -> List[CheckItem]:
        """
        [V60.4] 서사 폭주/정체 검사

        - 폭주: 1~2개 문단에 모든 사건이 압축됨 (해결 키워드 조기 등장)
        - 정체: 3개 이상 문단에서 같은 상황 반복 (키워드 중복도 높음)
        """
        items = []
        paragraphs = [p.strip() for p in manuscript.split('\n\n') if p.strip() and len(p.strip()) > 50]

        if len(paragraphs) < 4:
            return items  # 문단이 너무 적으면 체크 불가

        # 서사 폭주 검사: 해결/결정 키워드가 초반에 집중
        resolution_keywords = [
            '해결', '해치', '처치', '물리', '승리', '성공', '완료', '끝',
            '제압', '쓰러뜨', '도망', '퇴치', '격파', '결판', '마무리',
            '달성', '완수', '정리', '종결', '마침내'
        ]

        # 문단 위치별 해결 키워드 카운트
        total_paragraphs = len(paragraphs)
        early_section = paragraphs[:total_paragraphs // 3]  # 앞 1/3
        late_section = paragraphs[2 * total_paragraphs // 3:]  # 뒤 1/3

        early_resolution_count = sum(
            1 for p in early_section
            for kw in resolution_keywords
            if kw in p
        )
        late_resolution_count = sum(
            1 for p in late_section
            for kw in resolution_keywords
            if kw in p
        )

        # 폭주 조건: 초반 해결 키워드가 후반보다 2배 이상 많고 3개 이상
        if early_resolution_count >= 3 and early_resolution_count > late_resolution_count * 2:
            items.append(CheckItem(
                category=CheckCategory.NARRATIVE_FLOW,
                name="서사 폭주",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"서사 폭주 감지: 초반에 해결 키워드 {early_resolution_count}개 집중 (사건을 더 잘게 쪼개라)"
            ))
        elif early_resolution_count >= 2 and early_resolution_count > late_resolution_count:
            items.append(CheckItem(
                category=CheckCategory.NARRATIVE_FLOW,
                name="서사 폭주 경고",
                passed=True,
                severity=CheckSeverity.WARNING,
                message="초반에 해결/결말 키워드가 많음 - 사건 진행 속도 점검 필요"
            ))

        # 서사 정체 검사: 연속 문단의 핵심 키워드 중복도
        def extract_keywords(text: str, n: int = 8) -> set:
            words = re.findall(r'[\w가-힣]{2,}', text)
            # 빈도순 상위 n개
            from collections import Counter
            counter = Counter(words)
            return set(word for word, _ in counter.most_common(n))

        repetition_count = 0
        for i in range(len(paragraphs) - 2):
            p1_kw = extract_keywords(paragraphs[i])
            p2_kw = extract_keywords(paragraphs[i + 1])
            p3_kw = extract_keywords(paragraphs[i + 2])

            # 3개 문단 연속으로 50% 이상 키워드 중복
            overlap_12 = len(p1_kw & p2_kw) / max(len(p1_kw), 1)
            overlap_23 = len(p2_kw & p3_kw) / max(len(p2_kw), 1)

            if overlap_12 >= 0.5 and overlap_23 >= 0.5:
                repetition_count += 1

        # 정체 조건: 연속 3문단 중복이 2회 이상
        if repetition_count >= 2:
            items.append(CheckItem(
                category=CheckCategory.NARRATIVE_FLOW,
                name="서사 정체",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"서사 정체 감지: {repetition_count}회 연속 반복 패턴 (인과적 전진을 확보하라)"
            ))
        elif repetition_count >= 1:
            items.append(CheckItem(
                category=CheckCategory.NARRATIVE_FLOW,
                name="서사 정체 경고",
                passed=True,
                severity=CheckSeverity.WARNING,
                message="유사한 내용이 연속되는 구간 존재 - 변화를 주어라"
            ))

        # 정상 흐름
        if not any(item.category == CheckCategory.NARRATIVE_FLOW for item in items):
            items.append(CheckItem(
                category=CheckCategory.NARRATIVE_FLOW,
                name="서사 흐름",
                passed=True,
                severity=CheckSeverity.PASS,
                message="서사 흐름 양호"
            ))

        return items

    def _check_npc_behavior_jump(
        self,
        manuscript: str,
        context: Dict[str, Any]
    ) -> List[CheckItem]:
        """
        [V60.5] NPC 행동 급변 검사 (Python-based)

        관계 상태 전환 규칙:
        - 허용: 멸시→무시→의심→경외→충성 (순차적 1~2단계)
        - 금지: 무시→충성, 멸시→경외 등 (2단계 이상 점프)

        continuity_inspector.py의 _check_relationship_jump()와 동일한 로직이지만
        LLM 호출 전 Python 기반으로 조기 감지하여 비용 절감.
        """
        items = []

        # 관계 상태 우선순위 (낮을수록 적대적)
        STATE_PRIORITY = {
            "멸시": 0, "경멸": 0, "무시": 1, "의심": 2, "경계": 2,
            "중립": 3, "호감": 3, "경외": 4, "존경": 4, "충성": 5, "복종": 5
        }

        # 허용된 전환 (1~2단계까지)
        ALLOWED_TRANSITIONS = {
            "멸시": ["무시", "의심"],
            "경멸": ["무시", "의심"],
            "무시": ["의심", "경계", "경외"],  # 무시→충성 직행 불가
            "의심": ["경계", "중립", "경외"],
            "경계": ["중립", "호감", "경외"],
            "중립": ["호감", "경외", "충성"],
            "호감": ["경외", "존경", "충성"],
            "경외": ["존경", "충성"],
            "존경": ["충성", "복종"],
        }

        # 관계 변화 키워드 패턴
        relationship_change_patterns = [
            # 급격한 긍정 변화 패턴
            (r'(?:멸시|무시|경멸)[\s\S]{0,50}?(?:충성|복종|존경)', "급격한 관계 상승"),
            (r'(?:한순간|갑자기|단번에)[\s\S]{0,30}?(?:충성|복종|무릎)', "순간적 복종"),
            (r'(?:눈빛이|태도가)[\s\S]{0,20}?(?:완전히|180도)[\s\S]{0,20}?(?:바뀌|달라)', "태도 급변"),
            # 비현실적 전환 묘사
            (r'(?:하룻밤|한 번|단 한마디)[\s\S]{0,30}?(?:충성|복종|따르)', "비현실적 충성"),
        ]

        detected_jumps = []

        for pattern, desc in relationship_change_patterns:
            matches = re.findall(pattern, manuscript, re.IGNORECASE)
            if matches:
                detected_jumps.append((desc, matches[0][:40] if matches else ""))

        # 이전 원고와 비교하여 NPC 상태 변화 추적
        prev_manuscript = context.get("prev_manuscript", "")
        if prev_manuscript:
            # 직전 화에서 언급된 NPC 태도
            prev_negative_npcs = re.findall(
                r'(?:그들은|병사들은|사병들은|무사들은)[\s\S]{0,50}?(?:멸시|무시|경멸|비웃)',
                prev_manuscript
            )

            # 현재 화에서 급격한 변화
            if prev_negative_npcs:
                curr_positive = re.findall(
                    r'(?:그들은|병사들은|사병들은|무사들은)[\s\S]{0,50}?(?:충성|존경|따르|복종)',
                    manuscript[:2000]  # 시작 부분에서 급변
                )
                if curr_positive:
                    detected_jumps.append(("직전 화 대비 급변", f"이전: 멸시/무시 → 현재: 충성/존경"))

        # blueprint에서 relationship_changes 확인
        blueprint = context.get("blueprint", {})
        if isinstance(blueprint, dict):
            rel_changes = blueprint.get("relationship_changes", [])
            if rel_changes:
                for change in rel_changes:
                    if isinstance(change, dict):
                        from_state = change.get("from", "")
                        to_state = change.get("to", "")

                        from_priority = STATE_PRIORITY.get(from_state, 3)
                        to_priority = STATE_PRIORITY.get(to_state, 3)

                        # 2단계 이상 점프 감지
                        if to_priority - from_priority > 2:
                            target = change.get("target", "NPC")
                            detected_jumps.append(
                                ("Blueprint 급변 설계", f"{target}: {from_state}→{to_state}")
                            )

        # 결과 생성
        if len(detected_jumps) >= 2:
            # 2개 이상 급변 감지 → FAIL
            details = "; ".join([f"{d[0]}" for d in detected_jumps[:3]])
            items.append(CheckItem(
                category=CheckCategory.NPC_BEHAVIOR,
                name="NPC 행동 급변",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"NPC 관계 급변 다수 감지: {details} (단계적 전환 필요)"
            ))
        elif detected_jumps:
            # 1개 급변 → WARNING
            desc, example = detected_jumps[0]
            items.append(CheckItem(
                category=CheckCategory.NPC_BEHAVIOR,
                name="NPC 행동 급변 경고",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"NPC 관계 급변 의심: {desc} - 정당화 장면 확인 필요"
            ))
        else:
            # 정상
            items.append(CheckItem(
                category=CheckCategory.NPC_BEHAVIOR,
                name="NPC 행동 일관성",
                passed=True,
                severity=CheckSeverity.PASS,
                message="NPC 관계 변화 양호"
            ))

        return items

    def _measure_scene_reflection(
        self,
        manuscript: str,
        scene_breakdown: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        [V60.5] 씬별 반영률 정량 측정

        각 씬이 원고에 얼마나 반영됐는지 0-100%로 측정.
        미반영 씬을 구체적으로 지적.

        Returns:
            {
                'per_scene': {scene_key: {'ratio': float, 'keywords': [...], 'matched': [...]}},
                'overall_ratio': float,
                'weak_scenes': [scene_keys...],
                'check_items': [CheckItem...]
            }
        """
        result = {
            'per_scene': {},
            'overall_ratio': 0,
            'weak_scenes': [],
            'check_items': []
        }

        if not scene_breakdown:
            return result

        total_keywords = 0
        total_matched = 0
        weak_scenes = []

        for scene_key, scene_data in scene_breakdown.items():
            # 씬 설명에서 키워드 추출
            if isinstance(scene_data, dict):
                desc = scene_data.get("description", "")
                title = scene_data.get("title", "")
                full_text = f"{title} {desc}"
            else:
                full_text = str(scene_data)

            keywords = re.findall(r'[\w가-힣]{2,}', full_text)
            # 중복 제거 및 상위 8개 선택
            unique_keywords = list(dict.fromkeys(keywords))[:8]

            if not unique_keywords:
                continue

            # 매칭 확인
            matched = [kw for kw in unique_keywords if kw in manuscript]
            ratio = len(matched) / len(unique_keywords)

            result['per_scene'][scene_key] = {
                'ratio': ratio,
                'keywords': unique_keywords,
                'matched': matched,
                'missing': [kw for kw in unique_keywords if kw not in matched]
            }

            total_keywords += len(unique_keywords)
            total_matched += len(matched)

            # 약한 씬 감지 (30% 미만 반영)
            if ratio < 0.3:
                weak_scenes.append(scene_key)

        # 전체 반영률 계산
        result['overall_ratio'] = total_matched / total_keywords if total_keywords > 0 else 0
        result['weak_scenes'] = weak_scenes

        # 약한 씬에 대한 체크 아이템 생성
        if weak_scenes:
            # High Impact Zone (마지막 2개 씬) 체크
            scene_keys = list(scene_breakdown.keys())
            high_impact_scenes = scene_keys[-2:] if len(scene_keys) >= 2 else scene_keys

            high_impact_weak = [s for s in weak_scenes if s in high_impact_scenes]
            other_weak = [s for s in weak_scenes if s not in high_impact_scenes]

            if high_impact_weak:
                result['check_items'].append(CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="High Impact Zone 미반영",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"클라이맥스 씬 미반영: {', '.join(high_impact_weak)} (반영률 30% 미만)"
                ))

            if len(other_weak) >= 2:
                result['check_items'].append(CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="다수 씬 미반영",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"다수 씬 미반영: {', '.join(other_weak[:3])} (반영률 30% 미만)"
                ))
            elif other_weak:
                result['check_items'].append(CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="씬 미반영 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"씬 반영 부족: {', '.join(other_weak)} (보충 권장)"
                ))

        return result

    def _check_scene_density_balance(
        self,
        manuscript: str,
        scene_breakdown: Dict[str, Any]
    ) -> List[CheckItem]:
        """
        [V60.4] 씬 밀도 균등성 검사

        원고를 균등 분할하여 각 구간의 씬 키워드 매칭 수를 비교.
        앞부분만 상세하고 뒷부분이 급하게 요약되는 패턴 감지.
        """
        items = []

        if not scene_breakdown or len(scene_breakdown) < 3:
            return items

        scene_count = len(scene_breakdown)

        # 원고를 씬 수만큼 균등 분할
        section_len = len(manuscript) // scene_count
        if section_len < 200:  # 분량이 너무 적으면 체크 불가
            return items

        sections = []
        for i in range(scene_count):
            start = i * section_len
            end = (i + 1) * section_len if i < scene_count - 1 else len(manuscript)
            sections.append(manuscript[start:end])

        # 각 씬별 키워드 추출 및 매칭
        scene_keys = list(scene_breakdown.keys())
        section_densities = []

        for i, section in enumerate(sections):
            if i < len(scene_keys):
                scene_data = scene_breakdown[scene_keys[i]]
                if isinstance(scene_data, dict):
                    desc = scene_data.get("description", "")
                else:
                    desc = str(scene_data)

                # 키워드 매칭 밀도 계산
                keywords = re.findall(r'[\w가-힣]{2,}', str(desc))[:5]
                if keywords:
                    matched = sum(1 for kw in keywords if kw in section)
                    density = matched / len(keywords)
                else:
                    density = 0.5  # 키워드 없으면 중립

                section_densities.append(density)

        if len(section_densities) < 3:
            return items

        # 전반부 vs 후반부 밀도 비교
        mid_point = len(section_densities) // 2
        first_half_avg = sum(section_densities[:mid_point]) / mid_point
        second_half_avg = sum(section_densities[mid_point:]) / (len(section_densities) - mid_point)

        # 불균형 감지: 전반부가 후반부의 2배 이상이면 경고
        if first_half_avg > 0.3 and second_half_avg < 0.15:
            items.append(CheckItem(
                category=CheckCategory.BLUEPRINT_MATCH,
                name="씬 밀도 불균형",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"후반부 씬이 급하게 요약됨 (전반: {first_half_avg:.0%}, 후반: {second_half_avg:.0%})"
            ))
        elif first_half_avg > second_half_avg * 1.8:
            items.append(CheckItem(
                category=CheckCategory.BLUEPRINT_MATCH,
                name="씬 밀도 불균형 경고",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"후반부 씬 밀도가 낮음 (전반: {first_half_avg:.0%}, 후반: {second_half_avg:.0%})"
            ))
        else:
            items.append(CheckItem(
                category=CheckCategory.BLUEPRINT_MATCH,
                name="씬 밀도 균등",
                passed=True,
                severity=CheckSeverity.PASS,
                message=f"씬 밀도 균등 (전반: {first_half_avg:.0%}, 후반: {second_half_avg:.0%})"
            ))

        # [V60.5] High Impact Zone (마지막 2개 씬) 강화 체크
        high_impact_check = self._check_high_impact_zone(sections, section_densities, scene_count)
        items.extend(high_impact_check)

        return items

    def _check_high_impact_zone(
        self,
        sections: List[str],
        section_densities: List[float],
        scene_count: int
    ) -> List[CheckItem]:
        """
        [V60.5] High Impact Zone (Scene 5-6) 강화 체크

        클라이맥스 영역인 마지막 2개 씬에 대해 더 높은 기준 적용:
        - 밀도 기준 50% (일반 씬은 30%)
        - 분량 기준 600자 이상 (일반 씬은 500자)
        """
        items = []

        if scene_count < 4 or len(sections) < 4:
            return items

        # 마지막 2개 씬 (High Impact Zone)
        high_impact_sections = sections[-2:]
        high_impact_densities = section_densities[-2:] if len(section_densities) >= 2 else []

        # 1. 분량 체크 (High Impact Zone은 각 600자 이상 권장)
        high_impact_lengths = [len(s) for s in high_impact_sections]
        short_high_impact = [i for i, length in enumerate(high_impact_lengths) if length < 600]

        if short_high_impact:
            scene_nums = [scene_count - 1 + i for i in short_high_impact]
            items.append(CheckItem(
                category=CheckCategory.BLUEPRINT_MATCH,
                name="High Impact Zone 분량 부족",
                passed=True,  # 경고만
                severity=CheckSeverity.WARNING,
                message=f"클라이맥스 씬(Scene {', '.join(map(str, scene_nums))}) 분량 부족 - 각 600자 이상 권장"
            ))

        # 2. 밀도 체크 (High Impact Zone은 50% 이상 권장)
        if high_impact_densities:
            low_density_high_impact = [
                i for i, d in enumerate(high_impact_densities) if d < 0.5
            ]
            if len(low_density_high_impact) == 2:
                # 두 씬 모두 밀도 부족
                items.append(CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="High Impact Zone 밀도 부족",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"클라이맥스 씬 전체 밀도 부족 (Scene 5: {high_impact_densities[0]:.0%}, Scene 6: {high_impact_densities[1]:.0%}) - 절벽걸기 품질 저하"
                ))
            elif low_density_high_impact:
                scene_num = scene_count - 1 + low_density_high_impact[0]
                density = high_impact_densities[low_density_high_impact[0]]
                items.append(CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="High Impact Zone 밀도 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"Scene {scene_num} 밀도 부족 ({density:.0%}) - 클라이맥스 보강 권장"
                ))
            else:
                # High Impact Zone 밀도 양호
                avg_high_density = sum(high_impact_densities) / len(high_impact_densities)
                items.append(CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="High Impact Zone 양호",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=f"클라이맥스 씬 밀도 양호 (평균 {avg_high_density:.0%})"
                ))

        return items

    def _check_dialogue_ratio(self, manuscript: str) -> List[CheckItem]:
        """
        [V60.5] 대화/지문 비율 분석 및 구체적 가이드

        권장 비율:
        - 대화: 25-40%
        - 지문(서술): 60-75%

        Returns:
            CheckItem 목록
        """
        items = []

        # 대화 추출 (큰따옴표, 꺾쇠 따옴표)
        dialogue_patterns = [
            r'"[^"]+?"',  # 큰따옴표
            r'「[^」]+?」',  # 꺾쇠 따옴표
            r"'[^']{5,}'"  # 작은따옴표 (5자 이상만)
        ]

        dialogue_chars = 0
        for pattern in dialogue_patterns:
            matches = re.findall(pattern, manuscript)
            for match in matches:
                dialogue_chars += len(match)

        total_chars = len(manuscript)
        if total_chars < 1000:
            return items  # 분량 너무 적으면 체크 불가

        dialogue_ratio = dialogue_chars / total_chars
        narrative_ratio = 1 - dialogue_ratio

        # 대화 수 (기존 로직 유지)
        dialogue_count = manuscript.count('"') // 2 + manuscript.count('「')
        min_dialogue = self.MANUSCRIPT_REQUIRED["dialogue"][0]

        # 비율 기반 판정
        ideal_dialogue_ratio = 0.30  # 30% 목표
        ratio_diff = ideal_dialogue_ratio - dialogue_ratio

        if dialogue_count < min_dialogue:
            # 대화 수 절대 부족
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="대화 수",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"대화 부족: {dialogue_count}개 (최소 {min_dialogue}개)"
            ))
        elif dialogue_ratio < 0.15:
            # 비율 심각하게 낮음 (15% 미만)
            needed_chars = int((0.20 - dialogue_ratio) * total_chars)
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="대화 비율",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"대화 비율 심각 부족: {dialogue_ratio:.0%} (현재 {dialogue_chars}자) → 약 {needed_chars}자 대화 추가 필요"
            ))
        elif dialogue_ratio < 0.22:
            # 비율 낮음 (22% 미만)
            needed_chars = int((0.25 - dialogue_ratio) * total_chars)
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="대화 비율",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"대화 비율 낮음: {dialogue_ratio:.0%} → {needed_chars}자 대화 추가 권장"
            ))
        elif dialogue_ratio > 0.50:
            # 비율 너무 높음 (50% 초과)
            excess_chars = int((dialogue_ratio - 0.40) * total_chars)
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="대화 비율",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"대화 비율 과다: {dialogue_ratio:.0%} → 지문/묘사 {excess_chars}자 추가 권장"
            ))
        else:
            # 적정 범위
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="대화/지문 비율",
                passed=True,
                severity=CheckSeverity.PASS,
                message=f"대화/지문 비율 양호 (대화 {dialogue_ratio:.0%}, 지문 {narrative_ratio:.0%})"
            ))

        return items

    def _check_blueprint(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> List[CheckItem]:
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
                items.append(CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="JSON 파싱",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message="Blueprint JSON 파싱 실패"
                ))
                return items

        # 1. 필수 필드 체크
        required_fields = ["integrated_scenario", "scene_breakdown"]
        for field in required_fields:
            if field not in bp or not bp[field]:
                items.append(CheckItem(
                    category=CheckCategory.REQUIRED_FIELDS,
                    name=f"필드: {field}",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"필수 필드 누락: {field}"
                ))
            else:
                items.append(CheckItem(
                    category=CheckCategory.REQUIRED_FIELDS,
                    name=f"필드: {field}",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=f"필드 존재: {field}"
                ))

        # 2. 시나리오 길이 체크
        scenario = bp.get("integrated_scenario", "")
        scenario_len = len(str(scenario))
        if scenario_len < self.BLUEPRINT_LENGTH["scenario_min"]:
            items.append(CheckItem(
                category=CheckCategory.LENGTH,
                name="시나리오 길이",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"시나리오 길이 부족: {scenario_len}자"
            ))

        # 3. 씬 개수 체크
        scene_breakdown = bp.get("scene_breakdown", {})
        scene_count = len(scene_breakdown)

        if scene_count < 3:
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="씬 개수",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"씬 부족: {scene_count}개 (최소 3개)"
            ))
        elif scene_count > 8:
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="씬 개수",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"씬 과다: {scene_count}개 (권장 4-7개)"
            ))
        else:
            items.append(CheckItem(
                category=CheckCategory.STRUCTURE,
                name="씬 개수",
                passed=True,
                severity=CheckSeverity.PASS,
                message=f"씬 적절: {scene_count}개"
            ))

        # 4. 금지 패턴 체크
        for pattern, desc in self.FORBIDDEN_PATTERNS["blueprint"]:
            if re.search(pattern, content_str, re.IGNORECASE):
                items.append(CheckItem(
                    category=CheckCategory.FORBIDDEN_PATTERNS,
                    name=desc,
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=desc
                ))

        # 5. 엔딩 훅 체크
        ending_hook = bp.get("ending_hook") or bp.get("cliffhanger", "")
        if not ending_hook:
            items.append(CheckItem(
                category=CheckCategory.REQUIRED_FIELDS,
                name="엔딩 훅",
                passed=True,
                severity=CheckSeverity.WARNING,
                message="ending_hook 없음"
            ))

        return items

    def _check_sentence_variety(self, manuscript: str) -> List[CheckItem]:
        """
        [V60.6] 문장 다양성 검사

        연속 문장 시작어 중복을 탐지.
        - 3회 연속: WARNING
        - 5회 연속: FAIL
        """
        items = []

        # 문장 분리 (마침표, 물음표, 느낌표 기준)
        sentences = re.split(r'[.?!]\s*', manuscript)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        if len(sentences) < 5:
            return items

        # 문장 시작어 추출 (첫 2-3어절)
        def get_starter(sentence: str) -> str:
            words = sentence.split()[:3]
            return ' '.join(words) if words else ''

        # 반복 패턴 체크
        common_starters = ['그는', '그녀는', '그것은', '그들은', '나는', '그가', '그녀가']
        max_consecutive = 0
        current_consecutive = 1
        current_starter = ''
        worst_starter = ''

        for i in range(1, len(sentences)):
            prev_starter = get_starter(sentences[i - 1])
            curr_starter = get_starter(sentences[i])

            # 시작어가 같거나 공통 패턴에 해당
            is_repeat = False
            for common in common_starters:
                if common in prev_starter and common in curr_starter:
                    is_repeat = True
                    current_starter = common
                    break

            if is_repeat:
                current_consecutive += 1
                if current_consecutive > max_consecutive:
                    max_consecutive = current_consecutive
                    worst_starter = current_starter
            else:
                current_consecutive = 1

        # 결과 생성
        if max_consecutive >= 5:
            items.append(CheckItem(
                category=CheckCategory.SENTENCE_VARIETY,
                name="문장 시작어 반복",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"문장 시작어 '{worst_starter}' {max_consecutive}회 연속 반복 (다양한 시작어 사용 필요)"
            ))
        elif max_consecutive >= 3:
            items.append(CheckItem(
                category=CheckCategory.SENTENCE_VARIETY,
                name="문장 시작어 반복 경고",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"문장 시작어 '{worst_starter}' {max_consecutive}회 연속 - 변화를 주어라"
            ))
        else:
            items.append(CheckItem(
                category=CheckCategory.SENTENCE_VARIETY,
                name="문장 다양성",
                passed=True,
                severity=CheckSeverity.PASS,
                message="문장 시작어 다양성 양호"
            ))

        return items

    def _check_pacing_rhythm(self, manuscript: str) -> List[CheckItem]:
        """
        [V60.6] 긴장-이완 리듬 검증

        원고를 3등분하여 각 구간의 액션/대화/묘사 비율 분포 체크.
        """
        items = []

        if len(manuscript) < 3000:
            return items

        # 3등분
        section_len = len(manuscript) // 3
        sections = [
            manuscript[:section_len],
            manuscript[section_len:section_len * 2],
            manuscript[section_len * 2:]
        ]

        # 각 구간별 요소 비율 계산
        def analyze_section(text: str) -> Dict[str, float]:
            total_len = len(text) if text else 1

            # 대화 (따옴표 내용)
            dialogue = re.findall(r'"[^"]+?"', text)
            dialogue_len = sum(len(d) for d in dialogue)

            # 액션 키워드
            action_keywords = [
                '공격', '피했', '막았', '내리', '찔렀', '베었', '때렸', '걷어',
                '달려', '뛰어', '굴렀', '피하', '날아', '충돌', '부딪', '쓰러'
            ]
            action_count = sum(text.count(kw) for kw in action_keywords)
            action_density = action_count / (total_len / 1000)  # per 1000 chars

            # 묘사 (형용사/부사 밀도 추정)
            desc_patterns = [
                r'[\w]+[은는이가]\s+[\w]+[다]',  # ~은 ~다 패턴
                r'처럼|같이|마치|듯|듯이',  # 비유
            ]
            desc_count = sum(len(re.findall(p, text)) for p in desc_patterns)

            return {
                'dialogue_ratio': dialogue_len / total_len,
                'action_density': action_density,
                'desc_count': desc_count
            }

        section_analysis = [analyze_section(s) for s in sections]

        # 불균형 감지
        action_densities = [s['action_density'] for s in section_analysis]
        dialogue_ratios = [s['dialogue_ratio'] for s in section_analysis]

        # 전체가 액션만 (모든 구간 액션 밀도 높음)
        if all(d > 5 for d in action_densities):
            items.append(CheckItem(
                category=CheckCategory.PACING,
                name="페이싱 불균형",
                passed=True,
                severity=CheckSeverity.WARNING,
                message="전체가 액션으로만 구성됨 - 이완 구간(대화/묘사) 추가 권장"
            ))
        # 전체가 대화만
        elif all(r > 0.5 for r in dialogue_ratios):
            items.append(CheckItem(
                category=CheckCategory.PACING,
                name="페이싱 불균형",
                passed=True,
                severity=CheckSeverity.WARNING,
                message="전체가 대화로만 구성됨 - 액션/묘사 구간 추가 권장"
            ))
        # 전체가 묘사만 (액션 없고 대화도 적음)
        elif all(d < 1 for d in action_densities) and all(r < 0.15 for r in dialogue_ratios):
            items.append(CheckItem(
                category=CheckCategory.PACING,
                name="페이싱 정체",
                passed=True,
                severity=CheckSeverity.WARNING,
                message="액션과 대화가 부족함 - 긴장감 있는 장면 추가 권장"
            ))
        # 중반부 액션 집중 (절정 구조는 OK)
        elif section_analysis[1]['action_density'] > max(action_densities[0], action_densities[2]) * 1.5:
            items.append(CheckItem(
                category=CheckCategory.PACING,
                name="페이싱 구조",
                passed=True,
                severity=CheckSeverity.PASS,
                message="중반부 클라이맥스 구조 양호"
            ))
        else:
            items.append(CheckItem(
                category=CheckCategory.PACING,
                name="페이싱",
                passed=True,
                severity=CheckSeverity.PASS,
                message="긴장-이완 리듬 양호"
            ))

        return items

    def _check_setting_keywords(
        self,
        manuscript: str,
        context: Dict[str, Any]
    ) -> List[CheckItem]:
        """
        [V60.6] 설정 키워드 사전 검증

        Bible/Encyclopedia에서 금지어(미등장 무공, 사망 NPC 등)와
        필수어(현재 소지품 등)를 추출하여 원고에서 체크.
        """
        items = []

        # context에서 설정 데이터 추출
        encyclopedia = context.get('encyclopedia', {})
        hud = context.get('hud', {}) or context.get('martial_hud', {})
        dead_npcs = context.get('dead_npcs', [])
        owned_items = context.get('owned_items', [])

        # 1. 사망 NPC 등장 체크
        if dead_npcs:
            for npc in dead_npcs[:10]:  # 최대 10명 체크
                npc_name = npc if isinstance(npc, str) else npc.get('name', '')
                if npc_name and len(npc_name) >= 2:
                    # 대화나 행동하는 패턴 체크 (단순 언급은 OK)
                    action_pattern = rf'{npc_name}[이가은는]\s*[\w]+[했다|말했|대답|웃|소리]'
                    if re.search(action_pattern, manuscript):
                        items.append(CheckItem(
                            category=CheckCategory.SETTING_KEYWORDS,
                            name="사망 NPC 등장",
                            passed=False,
                            severity=CheckSeverity.FAIL,
                            message=f"사망한 NPC '{npc_name}'가 행동/대화함 - 제거 필요"
                        ))

        # 2. 미습득 무공 사용 체크 (HUD 기반)
        if hud:
            known_skills = []
            if isinstance(hud, dict):
                known_skills = hud.get('skills', []) or hud.get('무공', []) or []

            # 무공 키워드 패턴
            skill_usage_patterns = [
                (r'([\w]{2,6})(결|초식|장법|검법|권법|각법)을?\s*(펼|시전|사용)', '무공 사용'),
                (r'([\w]{2,6})(공|력|기)을?\s*(운용|발휘|끌어)', '내공 사용'),
            ]

            for pattern, desc in skill_usage_patterns:
                matches = re.findall(pattern, manuscript)
                for match in matches:
                    skill_name = match[0] + match[1] if isinstance(match, tuple) else match
                    # 알려진 무공 목록에 없으면 경고
                    if known_skills and not any(skill_name in str(ks) for ks in known_skills):
                        # 일반적인 표현은 제외
                        generic_terms = ['검', '도', '권', '장', '내공', '진기', '기운']
                        if not any(g in skill_name for g in generic_terms):
                            items.append(CheckItem(
                                category=CheckCategory.SETTING_KEYWORDS,
                                name="미습득 무공 사용 의심",
                                passed=True,
                                severity=CheckSeverity.WARNING,
                                message=f"'{skill_name}' 사용 감지 - HUD에 없는 무공인지 확인 필요"
                            ))
                            break  # 하나만 경고

        # 3. 필수 소지품 언급 여부 (첫 500자에서)
        if owned_items and len(owned_items) > 0:
            first_section = manuscript[:800]
            main_item = owned_items[0] if isinstance(owned_items[0], str) else owned_items[0].get('name', '')
            if main_item and len(main_item) >= 2 and main_item not in first_section:
                # 주요 소지품이 초반에 언급되지 않음 - 경고만
                items.append(CheckItem(
                    category=CheckCategory.SETTING_KEYWORDS,
                    name="주요 소지품 미언급",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"주요 소지품 '{main_item}'가 초반에 언급되지 않음"
                ))

        # 정상인 경우
        if not any(item.category == CheckCategory.SETTING_KEYWORDS for item in items):
            items.append(CheckItem(
                category=CheckCategory.SETTING_KEYWORDS,
                name="설정 일관성",
                passed=True,
                severity=CheckSeverity.PASS,
                message="설정 키워드 검증 통과"
            ))

        return items

    def _check_cliche_density(self, manuscript: str) -> List[CheckItem]:
        """
        [V60.6] 클리셰 밀도 경고

        진부한 표현 목록을 정의하고 빈도 측정.
        1000자당 3개 초과 시 WARNING, 5개 초과 시 FAIL.
        """
        items = []

        # 클리셰 표현 목록
        cliches = [
            # 신체 반응
            '이를 악물', '주먹을 불끈', '심장이 쿵', '눈앞이 캄캄',
            '온몸이 굳', '식은땀이', '심장이 멎', '숨이 턱',
            # 시각적 묘사
            '눈빛이 날카', '눈빛이 매서', '살기가 뿜', '섬광처럼',
            '번개처럼', '바람처럼', '유령처럼', '그림자처럼',
            # 감정 표현
            '분노가 치밀', '피가 끓', '눈에서 불', '이성을 잃',
            '피가 거꾸로', '화가 머리끝', '분노로 떨',
            # 상투적 비유
            '천근만근', '살얼음판', '벼락같은', '폭풍같은',
            '산산조각', '박살이 나', '가슴이 찢어',
            # 무협 클리셰
            '내공이 폭발', '진기가 요동', '경지에 오르', '깨달음을 얻',
            '하늘이 무너', '세상이 멈', '시간이 멈'
        ]

        # 클리셰 카운트
        total_count = 0
        found_cliches = []

        for cliche in cliches:
            count = manuscript.count(cliche)
            if count > 0:
                total_count += count
                found_cliches.append((cliche, count))

        # 밀도 계산 (1000자당)
        density = (total_count / len(manuscript)) * 1000 if manuscript else 0

        # 결과 생성
        if density > 5:
            top_cliches = sorted(found_cliches, key=lambda x: x[1], reverse=True)[:3]
            cliche_list = ', '.join([f"'{c[0]}'" for c in top_cliches])
            items.append(CheckItem(
                category=CheckCategory.CLICHE_DENSITY,
                name="클리셰 과다",
                passed=False,
                severity=CheckSeverity.FAIL,
                message=f"클리셰 밀도 과다: {density:.1f}/1000자 ({cliche_list} 등) - 신선한 표현으로 교체 필요"
            ))
        elif density > 3:
            items.append(CheckItem(
                category=CheckCategory.CLICHE_DENSITY,
                name="클리셰 밀도 경고",
                passed=True,
                severity=CheckSeverity.WARNING,
                message=f"클리셰 밀도 높음: {density:.1f}/1000자 - 일부 표현 교체 권장"
            ))
        else:
            items.append(CheckItem(
                category=CheckCategory.CLICHE_DENSITY,
                name="클리셰 밀도",
                passed=True,
                severity=CheckSeverity.PASS,
                message=f"클리셰 밀도 양호: {density:.1f}/1000자"
            ))

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
