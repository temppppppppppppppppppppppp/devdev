"""[R5-2c] PreDirectorChecklist style checker submodule."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity

if TYPE_CHECKING:
    from modules.core.pre_director_checklist import PreDirectorChecklist


class PreDirectorStyleChecker:
    """Sentence variety and pacing rhythm checks."""

    def __init__(self, host: PreDirectorChecklist) -> None:
        self.host = host

    def _check_sentence_variety(self, manuscript: str) -> list[CheckItem]:
        """
        [V60.6] 문장 다양성 검사

        연속 문장 시작어 중복을 탐지.
        - 3회 연속: WARNING
        - 5회 연속: FAIL
        """
        items = []

        # 문장 분리 (마침표, 물음표, 느낌표 기준)
        sentences = re.split(r"[.?!]\s*", manuscript)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        if len(sentences) < 5:
            return items

        # 문장 시작어 추출 (첫 2-3어절)
        def get_starter(sentence: str) -> str:
            words = sentence.split()[:3]
            return " ".join(words) if words else ""

        # 반복 패턴 체크
        common_starters = ["그는", "그녀는", "그것은", "그들은", "나는", "그가", "그녀가"]
        max_consecutive = 0
        current_consecutive = 1
        current_starter = ""
        worst_starter = ""

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
            items.append(
                CheckItem(
                    category=CheckCategory.SENTENCE_VARIETY,
                    name="문장 시작어 반복",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"문장 시작어 '{worst_starter}' {max_consecutive}회 연속 반복 (다양한 시작어 사용 필요)",
                )
            )
        elif max_consecutive >= 3:
            items.append(
                CheckItem(
                    category=CheckCategory.SENTENCE_VARIETY,
                    name="문장 시작어 반복 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"문장 시작어 '{worst_starter}' {max_consecutive}회 연속 - 변화를 주어라",
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.SENTENCE_VARIETY,
                    name="문장 다양성",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message="문장 시작어 다양성 양호",
                )
            )

        return items

    def _check_pacing_rhythm(self, manuscript: str) -> list[CheckItem]:
        """
        [V60.6] 긴장-이완 리듬 검증

        원고를 3등분하여 각 구간의 액션/대화/묘사 비율 분포 체크.
        """
        items = []

        if len(manuscript) < 3000:
            return items

        # 3등분
        section_len = len(manuscript) // 3
        sections = [manuscript[:section_len], manuscript[section_len : section_len * 2], manuscript[section_len * 2 :]]

        # 각 구간별 요소 비율 계산
        def analyze_section(text: str) -> dict[str, float]:
            total_len = len(text) if text else 1

            # 대화 (따옴표 내용)
            dialogue = re.findall(r'"[^"]+?"', text)
            dialogue_len = sum(len(d) for d in dialogue)

            # 액션 키워드
            action_keywords = [
                "공격",
                "피했",
                "막았",
                "내리",
                "찔렀",
                "베었",
                "때렸",
                "걷어",
                "달려",
                "뛰어",
                "굴렀",
                "피하",
                "날아",
                "충돌",
                "부딪",
                "쓰러",
            ]
            action_count = sum(text.count(kw) for kw in action_keywords)
            action_density = action_count / (total_len / 1000)  # per 1000 chars

            # 묘사 (형용사/부사 밀도 추정)
            desc_patterns = [
                r"[\w]+[은는이가]\s+[\w]+[다]",  # ~은 ~다 패턴
                r"처럼|같이|마치|듯|듯이",  # 비유
            ]
            desc_count = sum(len(re.findall(p, text)) for p in desc_patterns)

            return {
                "dialogue_ratio": dialogue_len / total_len,
                "action_density": action_density,
                "desc_count": desc_count,
            }

        section_analysis = [analyze_section(s) for s in sections]

        # 불균형 감지
        action_densities = [s["action_density"] for s in section_analysis]
        dialogue_ratios = [s["dialogue_ratio"] for s in section_analysis]

        # 전체가 액션만 (모든 구간 액션 밀도 높음)
        if all(d > 5 for d in action_densities):
            items.append(
                CheckItem(
                    category=CheckCategory.PACING,
                    name="페이싱 불균형",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message="전체가 액션으로만 구성됨 - 이완 구간(대화/묘사) 추가 권장",
                )
            )
        # 전체가 대화만
        elif all(r > 0.5 for r in dialogue_ratios):
            items.append(
                CheckItem(
                    category=CheckCategory.PACING,
                    name="페이싱 불균형",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message="전체가 대화로만 구성됨 - 액션/묘사 구간 추가 권장",
                )
            )
        # 전체가 묘사만 (액션 없고 대화도 적음)
        elif all(d < 1 for d in action_densities) and all(r < 0.15 for r in dialogue_ratios):
            items.append(
                CheckItem(
                    category=CheckCategory.PACING,
                    name="페이싱 정체",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message="액션과 대화가 부족함 - 긴장감 있는 장면 추가 권장",
                )
            )
        # 중반부 액션 집중 (절정 구조는 OK)
        elif section_analysis[1]["action_density"] > max(action_densities[0], action_densities[2]) * 1.5:
            items.append(
                CheckItem(
                    category=CheckCategory.PACING,
                    name="페이싱 구조",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message="중반부 클라이맥스 구조 양호",
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.PACING,
                    name="페이싱",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message="긴장-이완 리듬 양호",
                )
            )

        return items
