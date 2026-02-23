"""[R5-2c] PreDirectorChecklist narrative checker submodule."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity

if TYPE_CHECKING:
    from modules.core.pre_director_checklist import PreDirectorChecklist


class PreDirectorNarrativeChecker:
    """Narrative flow, NPC behavior, and setting keyword checks."""

    def __init__(self, host: PreDirectorChecklist) -> None:
        self.host = host

    def _check_narrative_flow(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        """
        [V60.4] 서사 폭주/정체 검사

        - 폭주: 1~2개 문단에 모든 사건이 압축됨 (해결 키워드 조기 등장)
        - 정체: 3개 이상 문단에서 같은 상황 반복 (키워드 중복도 높음)
        """
        items = []
        paragraphs = [p.strip() for p in manuscript.split("\n\n") if p.strip() and len(p.strip()) > 50]

        if len(paragraphs) < 4:
            return items  # 문단이 너무 적으면 체크 불가

        # 서사 폭주 검사: 해결/결정 키워드가 초반에 집중
        resolution_keywords = [
            "해결",
            "해치",
            "처치",
            "물리",
            "승리",
            "성공",
            "완료",
            "끝",
            "제압",
            "쓰러뜨",
            "도망",
            "퇴치",
            "격파",
            "결판",
            "마무리",
            "달성",
            "완수",
            "정리",
            "종결",
            "마침내",
        ]

        # 문단 위치별 해결 키워드 카운트
        total_paragraphs = len(paragraphs)
        early_section = paragraphs[: total_paragraphs // 3]  # 앞 1/3
        late_section = paragraphs[2 * total_paragraphs // 3 :]  # 뒤 1/3

        early_resolution_count = sum(1 for p in early_section for kw in resolution_keywords if kw in p)
        late_resolution_count = sum(1 for p in late_section for kw in resolution_keywords if kw in p)

        # 폭주 조건: 초반 해결 키워드가 후반보다 2배 이상 많고 3개 이상
        if early_resolution_count >= 3 and early_resolution_count > late_resolution_count * 2:
            items.append(
                CheckItem(
                    category=CheckCategory.NARRATIVE_FLOW,
                    name="서사 폭주",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"서사 폭주 감지: 초반에 해결 키워드 {early_resolution_count}개 집중 (사건을 더 잘게 쪼개라)",
                )
            )
        elif early_resolution_count >= 2 and early_resolution_count > late_resolution_count:
            items.append(
                CheckItem(
                    category=CheckCategory.NARRATIVE_FLOW,
                    name="서사 폭주 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message="초반에 해결/결말 키워드가 많음 - 사건 진행 속도 점검 필요",
                )
            )

        # 서사 정체 검사: 연속 문단의 핵심 키워드 중복도
        def extract_keywords(text: str, n: int = 8) -> set:
            words = re.findall(r"[\w가-힣]{2,}", text)
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
            items.append(
                CheckItem(
                    category=CheckCategory.NARRATIVE_FLOW,
                    name="서사 정체",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"서사 정체 감지: {repetition_count}회 연속 반복 패턴 (인과적 전진을 확보하라)",
                )
            )
        elif repetition_count >= 1:
            items.append(
                CheckItem(
                    category=CheckCategory.NARRATIVE_FLOW,
                    name="서사 정체 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message="유사한 내용이 연속되는 구간 존재 - 변화를 주어라",
                )
            )

        # 정상 흐름
        if not any(item.category == CheckCategory.NARRATIVE_FLOW for item in items):
            items.append(
                CheckItem(
                    category=CheckCategory.NARRATIVE_FLOW,
                    name="서사 흐름",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message="서사 흐름 양호",
                )
            )

        return items

    def _check_npc_behavior_jump(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
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
            "멸시": 0,
            "경멸": 0,
            "무시": 1,
            "의심": 2,
            "경계": 2,
            "중립": 3,
            "호감": 3,
            "경외": 4,
            "존경": 4,
            "충성": 5,
            "복종": 5,
        }

        # 허용된 전환 (1~2단계까지)

        # 관계 변화 키워드 패턴
        relationship_change_patterns = [
            # 급격한 긍정 변화 패턴
            (r"(?:멸시|무시|경멸)[\s\S]{0,50}?(?:충성|복종|존경)", "급격한 관계 상승"),
            (r"(?:한순간|갑자기|단번에)[\s\S]{0,30}?(?:충성|복종|무릎)", "순간적 복종"),
            (r"(?:눈빛이|태도가)[\s\S]{0,20}?(?:완전히|180도)[\s\S]{0,20}?(?:바뀌|달라)", "태도 급변"),
            # 비현실적 전환 묘사
            (r"(?:하룻밤|한 번|단 한마디)[\s\S]{0,30}?(?:충성|복종|따르)", "비현실적 충성"),
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
                r"(?:그들은|병사들은|사병들은|무사들은)[\s\S]{0,50}?(?:멸시|무시|경멸|비웃)", prev_manuscript
            )

            # 현재 화에서 급격한 변화
            if prev_negative_npcs:
                curr_positive = re.findall(
                    r"(?:그들은|병사들은|사병들은|무사들은)[\s\S]{0,50}?(?:충성|존경|따르|복종)",
                    manuscript[:2000],  # 시작 부분에서 급변
                )
                if curr_positive:
                    detected_jumps.append(("직전 화 대비 급변", "이전: 멸시/무시 → 현재: 충성/존경"))

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
                            detected_jumps.append(("Blueprint 급변 설계", f"{target}: {from_state}→{to_state}"))

        # 결과 생성
        if len(detected_jumps) >= 2:
            # 2개 이상 급변 감지 → FAIL
            details = "; ".join([f"{d[0]}" for d in detected_jumps[:3]])
            items.append(
                CheckItem(
                    category=CheckCategory.NPC_BEHAVIOR,
                    name="NPC 행동 급변",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"NPC 관계 급변 다수 감지: {details} (단계적 전환 필요)",
                )
            )
        elif detected_jumps:
            # 1개 급변 → WARNING
            desc, example = detected_jumps[0]
            items.append(
                CheckItem(
                    category=CheckCategory.NPC_BEHAVIOR,
                    name="NPC 행동 급변 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"NPC 관계 급변 의심: {desc} - 정당화 장면 확인 필요",
                )
            )
        else:
            # 정상
            items.append(
                CheckItem(
                    category=CheckCategory.NPC_BEHAVIOR,
                    name="NPC 행동 일관성",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message="NPC 관계 변화 양호",
                )
            )

        return items

    def _check_setting_keywords(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]:
        """
        [V60.6] 설정 키워드 사전 검증

        Bible/Encyclopedia에서 금지어(미등장 무공, 사망 NPC 등)와
        필수어(현재 소지품 등)를 추출하여 원고에서 체크.
        """
        items = []

        # context에서 설정 데이터 추출
        context.get("encyclopedia", {})
        hud = context.get("hud", {}) or context.get("martial_hud", {})
        dead_npcs = context.get("dead_npcs", [])
        owned_items = context.get("owned_items", [])

        # 1. 사망 NPC 등장 체크
        if dead_npcs:
            for npc in dead_npcs[:10]:  # 최대 10명 체크
                npc_name = npc if isinstance(npc, str) else npc.get("name", "")
                if npc_name and len(npc_name) >= 2:
                    # 대화나 행동하는 패턴 체크 (단순 언급은 OK)
                    action_pattern = rf"{re.escape(npc_name)}[이가은는]\s*[\w]+(?:했다|말했|대답|웃|소리)"  # [V70] [] → (?:) 교체 + re.escape
                    if re.search(action_pattern, manuscript):
                        items.append(
                            CheckItem(
                                category=CheckCategory.SETTING_KEYWORDS,
                                name="사망 NPC 등장",
                                passed=False,
                                severity=CheckSeverity.FAIL,
                                message=f"사망한 NPC '{npc_name}'가 행동/대화함 - 제거 필요",
                            )
                        )

        # 2. 미습득 무공 사용 체크 (HUD 기반)
        if hud:
            known_skills = []
            if isinstance(hud, dict):
                known_skills = hud.get("skills", []) or hud.get("무공", []) or []

            # 무공 키워드 패턴
            skill_usage_patterns = [
                (r"([\w]{2,6})(결|초식|장법|검법|권법|각법)을?\s*(펼|시전|사용)", "무공 사용"),
                (r"([\w]{2,6})(공|력|기)을?\s*(운용|발휘|끌어)", "내공 사용"),
            ]

            for pattern, desc in skill_usage_patterns:
                matches = re.findall(pattern, manuscript)
                for match in matches:
                    skill_name = match[0] + match[1] if isinstance(match, tuple) else match
                    # 알려진 무공 목록에 없으면 경고
                    if known_skills and not any(skill_name in str(ks) for ks in known_skills):
                        # 일반적인 표현은 제외
                        generic_terms = ["검", "도", "권", "장", "내공", "진기", "기운"]
                        if not any(g in skill_name for g in generic_terms):
                            items.append(
                                CheckItem(
                                    category=CheckCategory.SETTING_KEYWORDS,
                                    name="미습득 무공 사용 의심",
                                    passed=True,
                                    severity=CheckSeverity.WARNING,
                                    message=f"'{skill_name}' 사용 감지 - HUD에 없는 무공인지 확인 필요",
                                )
                            )
                            break  # 하나만 경고

        # 3. 필수 소지품 언급 여부 (첫 500자에서)
        if owned_items and len(owned_items) > 0:
            first_section = manuscript[:800]
            main_item = owned_items[0] if isinstance(owned_items[0], str) else owned_items[0].get("name", "")
            if main_item and len(main_item) >= 2 and main_item not in first_section:
                # 주요 소지품이 초반에 언급되지 않음 - 경고만
                items.append(
                    CheckItem(
                        category=CheckCategory.SETTING_KEYWORDS,
                        name="주요 소지품 미언급",
                        passed=True,
                        severity=CheckSeverity.WARNING,
                        message=f"주요 소지품 '{main_item}'가 초반에 언급되지 않음",
                    )
                )

        # 정상인 경우
        if not any(item.category == CheckCategory.SETTING_KEYWORDS for item in items):
            items.append(
                CheckItem(
                    category=CheckCategory.SETTING_KEYWORDS,
                    name="설정 일관성",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message="설정 키워드 검증 통과",
                )
            )

        return items
