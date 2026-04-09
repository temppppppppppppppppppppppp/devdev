"""[R5-1a] PreDirectorChecklist 원고 품질 체크 서브모듈.

PreDirectorChecklist에서 분리된 5개 원고 관련 체크:
- _check_dialogue_ratio: 대화/지문 비율 분석
- _measure_scene_reflection: 씬별 반영률 정량 측정
- _check_scene_density_balance: 씬 밀도 균등성 검사
- _check_high_impact_zone: 클라이맥스 씬 강화 체크
- _check_cliche_density: 클리셰 밀도 경고
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity
from modules.validation.dialogue_utils import count_dialogue_characters, count_dialogue_segments

if TYPE_CHECKING:
    from modules.core.pre_director_checklist import PreDirectorChecklist


class PreDirectorManuscriptChecker:
    """원고 품질 체크 담당 서브모듈."""

    def __init__(self, host: PreDirectorChecklist) -> None:
        self.host = host

    # ──────────────────────────────────────────────
    # 대화/지문 비율
    # ──────────────────────────────────────────────

    @staticmethod
    def _resolve_dialogue_ratio_target(context: dict[str, Any] | None = None) -> float:
        if not isinstance(context, dict):
            return 0.30

        raw_target = context.get("style_dialogue_ratio_target")
        if isinstance(raw_target, (int, float)):
            target = float(raw_target)
            if 0.0 <= target < 1.0:
                return target
        return 0.30

    def _check_dialogue_ratio(self, manuscript: str, context: dict[str, Any] | None = None) -> list[CheckItem]:
        """
        [V60.5] 대화/지문 비율 분석 및 구체적 가이드

        권장 비율:
        - 대화: 25-40%
        - 지문(서술): 60-75%
        """
        items = []

        dialogue_patterns = [
            r'"[^"]+?"',
            r"\u300c[^\u300d]+?\u300d",
            r"'[^']{5,}'",
        ]

        dialogue_chars = count_dialogue_characters(manuscript)

        total_chars = len(manuscript)
        if total_chars < 1000:
            return items

        dialogue_ratio = dialogue_chars / total_chars
        narrative_ratio = 1 - dialogue_ratio

        dialogue_count = manuscript.count('"') // 2 + manuscript.count("「")
        dialogue_count = count_dialogue_segments(manuscript)
        min_dialogue = self.host.MANUSCRIPT_REQUIRED["dialogue"][0]

        ideal_dialogue_ratio = self._resolve_dialogue_ratio_target(context)
        if ideal_dialogue_ratio <= 0.0:
            if dialogue_ratio > 0.12:
                excess_chars = int(dialogue_ratio * total_chars)
                items.append(
                    CheckItem(
                        category=CheckCategory.STRUCTURE,
                        name="대화 비율",
                        passed=True,
                        severity=CheckSeverity.WARNING,
                        message=(
                            f"대화 비율 높음: {dialogue_ratio:.0%} "
                            f"(스타일 목표 {ideal_dialogue_ratio:.0%}) "
                            f"→ 무대사/저대화 스타일 기준으로 대화 {excess_chars}자 축소 권장"
                        ),
                    )
                )
            else:
                items.append(
                    CheckItem(
                        category=CheckCategory.STRUCTURE,
                        name="대화/지문 비율",
                        passed=True,
                        severity=CheckSeverity.PASS,
                        message=(
                            f"대화/지문 비율 양호 (대화 {dialogue_ratio:.0%}, "
                            f"지문 {narrative_ratio:.0%}, 스타일 목표 {ideal_dialogue_ratio:.0%})"
                        ),
                    )
                )
            return items

        lower_recommended = max(0.18, ideal_dialogue_ratio - 0.08)
        upper_recommended = min(0.55, ideal_dialogue_ratio + 0.12)

        if dialogue_count < min_dialogue:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="대화 수",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"대화 부족: {dialogue_count}개 (최소 {min_dialogue}개)",
                )
            )
        elif dialogue_ratio < 0.15:
            needed_chars = int((max(0.20, lower_recommended) - dialogue_ratio) * total_chars)
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="대화 비율",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=(
                        f"대화 비율 심각 부족: {dialogue_ratio:.0%} "
                        f"(스타일 목표 {ideal_dialogue_ratio:.0%}, 현재 {dialogue_chars}자) "
                        f"→ 약 {needed_chars}자 대화 추가 필요"
                    ),
                )
            )
        elif dialogue_ratio < lower_recommended:
            needed_chars = int((ideal_dialogue_ratio - dialogue_ratio) * total_chars)
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="대화 비율",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=(
                        f"대화 비율 낮음: {dialogue_ratio:.0%} "
                        f"(스타일 목표 {ideal_dialogue_ratio:.0%}) "
                        f"→ {needed_chars}자 대화 추가 권장"
                    ),
                )
            )
        elif dialogue_ratio > upper_recommended:
            excess_chars = int((dialogue_ratio - ideal_dialogue_ratio) * total_chars)
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="대화 비율",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=(
                        f"대화 비율 과다: {dialogue_ratio:.0%} "
                        f"(스타일 목표 {ideal_dialogue_ratio:.0%}) "
                        f"→ 지문/묘사 {excess_chars}자 추가 권장"
                    ),
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.STRUCTURE,
                    name="대화/지문 비율",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=(
                        f"대화/지문 비율 양호 (대화 {dialogue_ratio:.0%}, "
                        f"지문 {narrative_ratio:.0%}, 스타일 목표 {ideal_dialogue_ratio:.0%})"
                    ),
                )
            )

        return items

    # ──────────────────────────────────────────────
    # 씬 반영률 측정
    # ──────────────────────────────────────────────

    def _measure_scene_reflection(self, manuscript: str, scene_breakdown: dict[str, Any]) -> dict[str, Any]:
        """
        [V60.5] 씬별 반영률 정량 측정

        각 씬이 원고에 얼마나 반영됐는지 0-100%로 측정.
        미반영 씬을 구체적으로 지적.
        """
        result: dict[str, Any] = {"per_scene": {}, "overall_ratio": 0, "weak_scenes": [], "check_items": []}

        if not scene_breakdown or not isinstance(scene_breakdown, dict):
            return result

        total_keywords = 0
        total_matched = 0
        weak_scenes = []

        for scene_key, scene_data in scene_breakdown.items():
            if isinstance(scene_data, dict):
                desc = scene_data.get("description", "")
                title = scene_data.get("title", "")
                full_text = f"{title} {desc}"
            else:
                full_text = str(scene_data)

            keywords = re.findall(r"[\w가-힣]{2,}", full_text)
            unique_keywords = list(dict.fromkeys(keywords))[:8]

            if not unique_keywords:
                continue

            matched = [kw for kw in unique_keywords if kw in manuscript]
            ratio = len(matched) / len(unique_keywords)

            result["per_scene"][scene_key] = {
                "ratio": ratio,
                "keywords": unique_keywords,
                "matched": matched,
                "missing": [kw for kw in unique_keywords if kw not in matched],
            }

            total_keywords += len(unique_keywords)
            total_matched += len(matched)

            if ratio < 0.3:
                weak_scenes.append(scene_key)

        result["overall_ratio"] = total_matched / total_keywords if total_keywords > 0 else 0
        result["weak_scenes"] = weak_scenes

        # [TF-1] 전체 씬 미반영(0/N) — 구조적 실패로 hard fail
        if len(weak_scenes) == len(scene_breakdown) and len(scene_breakdown) >= 3:
            result["check_items"].append(
                CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="전체 씬 미반영",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=(
                        f"전체 씬 미반영: {len(weak_scenes)}/{len(scene_breakdown)} 씬 반영률 30% 미만. "
                        "Blueprint 씬 구조가 원고에 전혀 반영되지 않았습니다. "
                        "각 씬을 '### 씬 N: 제목' 헤더로 구분하여 빠짐없이 작성하세요."
                    ),
                )
            )
            return result

        if weak_scenes:
            scene_keys = list(scene_breakdown.keys())
            high_impact_scenes = scene_keys[-2:] if len(scene_keys) >= 2 else scene_keys

            high_impact_weak = [s for s in weak_scenes if s in high_impact_scenes]
            other_weak = [s for s in weak_scenes if s not in high_impact_scenes]

            if high_impact_weak:
                # [TF-51] FAIL→WARNING: Python 키워드 매칭 오탐 과다, Director LLM 판단 위임
                result["check_items"].append(
                    CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="High Impact Zone 미반영",
                        passed=True,
                        severity=CheckSeverity.WARNING,
                        message=f"클라이맥스 씬 미반영: {', '.join(high_impact_weak)} (반영률 30% 미만) (Director 판단 위임)",
                    )
                )

            if len(other_weak) >= 2:
                # [TF-51] FAIL→WARNING: Python 키워드 매칭 오탐 과다, Director LLM 판단 위임
                result["check_items"].append(
                    CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="다수 씬 미반영",
                        passed=True,
                        severity=CheckSeverity.WARNING,
                        message=f"다수 씬 미반영: {', '.join(other_weak[:3])} (반영률 30% 미만) (Director 판단 위임)",
                    )
                )
            elif other_weak:
                result["check_items"].append(
                    CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="씬 미반영 경고",
                        passed=True,
                        severity=CheckSeverity.WARNING,
                        message=f"씬 반영 부족: {', '.join(other_weak)} (보충 권장)",
                    )
                )

        return result

    # ──────────────────────────────────────────────
    # [Gap-2] 씬 헤더 계약 검증
    # ──────────────────────────────────────────────

    _SCENE_HEADER_RE = re.compile(
        r"^#{1,3}\s+씬\s*(\d+)\s*[:\-]",
        re.MULTILINE,
    )

    def _check_scene_header_contract(self, manuscript: str, scene_breakdown: dict[str, Any]) -> list[CheckItem]:
        """[Gap-2] Blueprint 씬 3개 이상일 때 원고에 씬 헤더가 최소 절반 이상 존재하는지 검증."""
        items: list[CheckItem] = []
        if not scene_breakdown or not isinstance(scene_breakdown, dict):
            return items

        expected_count = len(scene_breakdown)
        if expected_count < 3:
            return items

        header_matches = list(self._SCENE_HEADER_RE.finditer(manuscript))
        found_headers = {
            int(match.group(1))
            for match in header_matches
            if match.group(1).isdigit()
        }
        found_count = len(found_headers)
        min_required_headers = (expected_count + 1) // 2

        if found_count == 0:
            items.append(
                CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="씬 헤더 부재",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=(
                        f"Blueprint {expected_count}개 씬 중 원고에 '### 씬 N: 제목' 헤더가 0개 발견됨. "
                        "모든 씬을 헤더로 구분하여 작성해야 합니다."
                    ),
                )
            )
        elif found_count < min_required_headers:
            items.append(
                CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="씬 헤더 부족",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=(
                        f"Blueprint {expected_count}개 씬 중 원고에 '### 씬 N:' 헤더가 {found_count}개만 발견됨. "
                        f"최소 {min_required_headers}개 이상 필요. 누락된 씬 헤더 보충 권장."
                    ),
                )
            )

        return items

    # ──────────────────────────────────────────────
    # 씬 밀도 균등성 + High Impact Zone
    # ──────────────────────────────────────────────

    def _check_scene_density_balance(self, manuscript: str, scene_breakdown: dict[str, Any]) -> list[CheckItem]:
        """
        [V60.4] 씬 밀도 균등성 검사

        원고를 균등 분할하여 각 구간의 씬 키워드 매칭 수를 비교.
        앞부분만 상세하고 뒷부분이 급하게 요약되는 패턴 감지.
        """
        items = []

        if not isinstance(scene_breakdown, dict) or not scene_breakdown or len(scene_breakdown) <= 1:
            return items

        scene_count = len(scene_breakdown)

        section_len = len(manuscript) // scene_count
        if section_len < 200:
            return items

        sections = []
        for i in range(scene_count):
            start = i * section_len
            end = (i + 1) * section_len if i < scene_count - 1 else len(manuscript)
            sections.append(manuscript[start:end])

        scene_keys = list(scene_breakdown.keys())
        section_densities = []

        for i, section in enumerate(sections):
            if i < len(scene_keys):
                scene_data = scene_breakdown[scene_keys[i]]
                if isinstance(scene_data, dict):
                    desc = scene_data.get("description", "")
                else:
                    desc = str(scene_data)

                keywords = re.findall(r"[\w가-힣]{2,}", str(desc))[:5]
                if keywords:
                    matched = sum(1 for kw in keywords if kw in section)
                    density = matched / len(keywords)
                else:
                    density = 0.5

                section_densities.append(density)

        if len(section_densities) < 2:
            return items

        mid_point = len(section_densities) // 2
        first_half_avg = sum(section_densities[:mid_point]) / mid_point
        second_half_avg = sum(section_densities[mid_point:]) / (len(section_densities) - mid_point)

        if first_half_avg > 0.3 and second_half_avg < 0.15:
            items.append(
                CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="씬 밀도 불균형",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"후반부 씬이 급하게 요약됨 (전반: {first_half_avg:.0%}, 후반: {second_half_avg:.0%})",
                )
            )
        elif first_half_avg > second_half_avg * 1.8:
            items.append(
                CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="씬 밀도 불균형 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"후반부 씬 밀도가 낮음 (전반: {first_half_avg:.0%}, 후반: {second_half_avg:.0%})",
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="씬 밀도 균등",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=f"씬 밀도 균등 (전반: {first_half_avg:.0%}, 후반: {second_half_avg:.0%})",
                )
            )

        high_impact_check = self._check_high_impact_zone(sections, section_densities, scene_count)
        items.extend(high_impact_check)

        return items

    def _check_high_impact_zone(
        self, sections: list[str], section_densities: list[float], scene_count: int
    ) -> list[CheckItem]:
        """
        [V60.5] 후반부 핵심 씬 강화 체크

        클라이맥스/전환 영역인 마지막 1-2개 씬에 대해 더 높은 기준 적용:
        - 밀도 기준 50% (일반 씬은 30%)
        - 분량 기준 600자 이상 (일반 씬은 500자)
        """
        items = []

        if scene_count < 2 or len(sections) < 2:
            return items

        late_zone_size = 1 if scene_count == 2 else 2
        high_impact_sections = sections[-late_zone_size:]
        high_impact_densities = section_densities[-late_zone_size:] if len(section_densities) >= late_zone_size else []
        late_scene_nums = list(range(scene_count - late_zone_size + 1, scene_count + 1))

        high_impact_lengths = [len(s) for s in high_impact_sections]
        short_high_impact = [i for i, length in enumerate(high_impact_lengths) if length < 600]

        if short_high_impact:
            scene_nums = [late_scene_nums[i] for i in short_high_impact]
            items.append(
                CheckItem(
                    category=CheckCategory.BLUEPRINT_MATCH,
                    name="후반부 핵심 씬 분량 부족",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"후반부 핵심 씬(Scene {', '.join(map(str, scene_nums))}) 분량 부족 - 각 600자 이상 권장",
                )
            )

        if high_impact_densities:
            low_density_high_impact = [i for i, d in enumerate(high_impact_densities) if d < 0.5]
            if len(low_density_high_impact) == len(high_impact_densities):
                detail = ", ".join(
                    f"Scene {late_scene_nums[i]}: {high_impact_densities[i]:.0%}" for i in range(len(high_impact_densities))
                )
                items.append(
                    CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="후반부 핵심 씬 밀도 부족",
                        passed=False,
                        severity=CheckSeverity.FAIL,
                        message=f"후반부 핵심 씬 전체 밀도 부족 ({detail}) - 절벽걸기 품질 저하",
                    )
                )
            elif low_density_high_impact:
                scene_num = late_scene_nums[low_density_high_impact[0]]
                density = high_impact_densities[low_density_high_impact[0]]
                items.append(
                    CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="후반부 핵심 씬 밀도 경고",
                        passed=True,
                        severity=CheckSeverity.WARNING,
                        message=f"Scene {scene_num} 밀도 부족 ({density:.0%}) - 후반부 체류 시간 보강 권장",
                    )
                )
            else:
                avg_high_density = sum(high_impact_densities) / len(high_impact_densities)
                items.append(
                    CheckItem(
                        category=CheckCategory.BLUEPRINT_MATCH,
                        name="후반부 핵심 씬 양호",
                        passed=True,
                        severity=CheckSeverity.PASS,
                        message=f"후반부 핵심 씬 밀도 양호 (평균 {avg_high_density:.0%})",
                    )
                )

        return items

    # ──────────────────────────────────────────────
    # 클리셰 밀도
    # ──────────────────────────────────────────────

    def _check_cliche_density(self, manuscript: str) -> list[CheckItem]:
        """
        [V60.6] 클리셰 밀도 경고

        진부한 표현 목록을 정의하고 빈도 측정.
        1000자당 3개 초과 시 WARNING, 5개 초과 시 FAIL.
        """
        items = []

        cliches = [
            "이를 악물",
            "주먹을 불끈",
            "심장이 쿵",
            "눈앞이 캄캄",
            "온몸이 굳",
            "식은땀이",
            "심장이 멎",
            "숨이 턱",
            "눈빛이 날카",
            "눈빛이 매서",
            "살기가 뿜",
            "섬광처럼",
            "번개처럼",
            "바람처럼",
            "유령처럼",
            "그림자처럼",
            "분노가 치밀",
            "피가 끓",
            "눈에서 불",
            "이성을 잃",
            "피가 거꾸로",
            "화가 머리끝",
            "분노로 떨",
            "천근만근",
            "살얼음판",
            "벼락같은",
            "폭풍같은",
            "산산조각",
            "박살이 나",
            "가슴이 찢어",
            "내공이 폭발",
            "진기가 요동",
            "경지에 오르",
            "깨달음을 얻",
            "하늘이 무너",
            "세상이 멈",
            "시간이 멈",
        ]

        total_count = 0
        found_cliches = []

        for cliche in cliches:
            count = manuscript.count(cliche)
            if count > 0:
                total_count += count
                found_cliches.append((cliche, count))

        density = (total_count / len(manuscript)) * 1000 if manuscript else 0

        if density > 5:
            top_cliches = sorted(found_cliches, key=lambda x: x[1], reverse=True)[:3]
            cliche_list = ", ".join([f"'{c[0]}'" for c in top_cliches])
            items.append(
                CheckItem(
                    category=CheckCategory.CLICHE_DENSITY,
                    name="클리셰 과다",
                    passed=False,
                    severity=CheckSeverity.FAIL,
                    message=f"클리셰 밀도 과다: {density:.1f}/1000자 ({cliche_list} 등) - 신선한 표현으로 교체 필요",
                )
            )
        elif density > 3:
            items.append(
                CheckItem(
                    category=CheckCategory.CLICHE_DENSITY,
                    name="클리셰 밀도 경고",
                    passed=True,
                    severity=CheckSeverity.WARNING,
                    message=f"클리셰 밀도 높음: {density:.1f}/1000자 - 일부 표현 교체 권장",
                )
            )
        else:
            items.append(
                CheckItem(
                    category=CheckCategory.CLICHE_DENSITY,
                    name="클리셰 밀도",
                    passed=True,
                    severity=CheckSeverity.PASS,
                    message=f"클리셰 밀도 양호: {density:.1f}/1000자",
                )
            )

        return items
