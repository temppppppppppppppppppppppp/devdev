"""
[V60.80] Manuscript Validator - Python 기반 사전 검증기

Stage 4 "Director 주권주의" 아키텍처의 무료 사전 검증 레이어.
LLM 호출 없이 Python으로 빠르게 경고 포인트를 생성.

중요: REJECT 권한 없음! 경고만 생성하여 Director에게 "집중 검토 포인트"로 전달.
"""

import re
from typing import Dict, List, Optional


class ManuscriptValidator:
    """
    [V60.80] Python 기반 원고 사전 검증기

    역할:
    - 분량 체크 (경고만)
    - 씬 반영률 체크 (경고만)
    - 연속성 기초 체크 (경고만)
    - Blueprint 키워드 체크 (경고만)

    중요: REJECT 권한 없음! 모든 결과는 Director에게 "주의 깊게 볼 포인트"로 전달
    """

    # 분량 기준
    LENGTH_WARNING_THRESHOLD = 4500  # 이 미만이면 경고
    LENGTH_TARGET = 5000  # 목표 분량

    def __init__(self, context=None):
        self.context = context
        self._dead_npcs = set()  # 죽은 NPC 캐시

    def validate_candidate(
        self,
        manuscript: str,
        blueprint: dict,
        prev_manuscript: str = "",
        hud_report: str = "",
        strategy_name: str = ""
    ) -> Dict:
        """
        단일 후보 원고 검증

        Args:
            manuscript: 검증 대상 원고
            blueprint: Blueprint 데이터
            prev_manuscript: 직전 화 원고
            hud_report: 현재 HUD 상태

        Returns:
            {
                "warnings": List[str],  # 경고 목록
                "warning_count": int,
                "focus_points": List[str],  # Director 집중 검토 포인트
                "metrics": {
                    "length": int,
                    "scene_coverage": float,
                    "continuity_score": float
                }
            }
        """
        warnings = []
        focus_points = []
        metrics = {}

        # 1. 분량 체크
        length_result = self._check_length(manuscript)
        metrics["length"] = length_result["length"]
        if length_result["warnings"]:
            warnings.extend(length_result["warnings"])
            focus_points.append(f"분량 주의: {length_result['length']}자")

        # 2. 씬 반영률 체크
        scene_result = self._check_scene_coverage(manuscript, blueprint)
        metrics["scene_coverage"] = scene_result["coverage"]
        metrics["expected_scenes"] = scene_result["expected"]
        metrics["reflected_scenes"] = scene_result["reflected"]
        if scene_result["warnings"]:
            warnings.extend(scene_result["warnings"])
            if scene_result["missing_scenes"]:
                focus_points.append(f"씬 미반영 의심: {', '.join(scene_result['missing_scenes'][:3])}")

        # 3. 연속성 기초 체크
        continuity_result = self._check_basic_continuity(manuscript, prev_manuscript, hud_report)
        metrics["continuity_issues"] = continuity_result["issue_count"]
        if continuity_result["warnings"]:
            warnings.extend(continuity_result["warnings"])
            focus_points.extend(continuity_result["focus_points"])

        # 4. Blueprint 키워드 체크
        keyword_result = self._check_blueprint_keywords(manuscript, blueprint)
        if keyword_result["warnings"]:
            warnings.extend(keyword_result["warnings"])
            if keyword_result["missing_keywords"]:
                focus_points.append(f"핵심 키워드 누락 의심: {', '.join(keyword_result['missing_keywords'][:3])}")

        # 5. 후반부 품질 체크
        quality_result = self._check_ending_quality(manuscript)
        if quality_result["warnings"]:
            warnings.extend(quality_result["warnings"])

        return {
            "strategy": strategy_name,
            "warnings": warnings,
            "warning_count": len(warnings),
            "focus_points": focus_points,
            "metrics": metrics,
            "has_critical_warning": len(focus_points) >= 3  # 집중 검토 필요
        }

    def validate_all_candidates(
        self,
        candidates: List[Dict],
        blueprint: dict,
        prev_manuscript: str = "",
        hud_report: str = ""
    ) -> List[Dict]:
        """
        모든 후보 검증

        Args:
            candidates: Chief Writer가 생성한 후보 목록
            blueprint: Blueprint 데이터
            prev_manuscript: 직전 화 원고
            hud_report: 현재 HUD 상태

        Returns:
            List[Dict]: 각 후보별 검증 결과
        """
        results = []

        for candidate in candidates:
            manuscript = candidate.get("manuscript", "")
            strategy = candidate.get("strategy", "unknown")
            strategy_name = candidate.get("strategy_name", strategy)

            if not manuscript:
                results.append({
                    "strategy": strategy,
                    "warnings": ["원고 내용 없음"],
                    "warning_count": 1,
                    "focus_points": ["빈 원고"],
                    "metrics": {"length": 0, "scene_coverage": 0},
                    "has_critical_warning": True
                })
                continue

            result = self.validate_candidate(
                manuscript=manuscript,
                blueprint=blueprint,
                prev_manuscript=prev_manuscript,
                hud_report=hud_report,
                strategy_name=strategy_name
            )

            results.append(result)

        return results

    def _check_length(self, manuscript: str) -> Dict:
        """분량 체크"""
        length = len(manuscript) if manuscript else 0
        warnings = []

        if length < 4000:
            warnings.append(f"⚠️ 분량 심각 부족: {length}자 (최소 4,000자 필요)")
        elif length < self.LENGTH_WARNING_THRESHOLD:
            warnings.append(f"⚠️ 분량 부족: {length}자 (목표 {self.LENGTH_TARGET}자)")

        return {
            "length": length,
            "warnings": warnings
        }

    def _check_scene_coverage(self, manuscript: str, blueprint: dict) -> Dict:
        """씬 반영률 체크"""
        if not blueprint or not isinstance(blueprint, dict):
            return {
                "coverage": 100.0,
                "expected": 0,
                "reflected": 0,
                "missing_scenes": [],
                "warnings": []
            }

        warnings = []
        missing_scenes = []

        # Blueprint에서 씬 정보 추출
        scene_breakdown = blueprint.get("scene_breakdown", {})
        integrated_scenario = blueprint.get("integrated_scenario", "")

        # 씬 키워드 추출
        scene_keywords = {}
        expected_scenes = 0

        if isinstance(scene_breakdown, dict):
            for scene_key, scene_content in scene_breakdown.items():
                if not scene_key.lower().startswith("scene"):
                    continue
                expected_scenes += 1

                # 핵심 키워드 추출 (한글 2-5자 단어)
                if isinstance(scene_content, str):
                    keywords = re.findall(r'[가-힣]{2,5}', scene_content)
                    # 빈도 높은 키워드 제외 (조사, 일반어)
                    filtered = [k for k in keywords if k not in ['하다', '되다', '있다', '없다', '이다', '그리고', '하지만']]
                    scene_keywords[scene_key] = filtered[:5]

        if expected_scenes == 0:
            # scene_breakdown이 없으면 integrated_scenario에서 추정
            scene_markers = re.findall(r'\[(Core|Buffer|Cliffhanger|Scene)\s*\d*\]', integrated_scenario, re.IGNORECASE)
            expected_scenes = len(scene_markers) if scene_markers else 6

        # 반영률 계산
        reflected = 0
        for scene_key, keywords in scene_keywords.items():
            matched = sum(1 for k in keywords if k in manuscript)
            if len(keywords) == 0 or matched >= len(keywords) * 0.4:
                reflected += 1
            else:
                missing_scenes.append(scene_key)

        coverage = (reflected / expected_scenes * 100) if expected_scenes > 0 else 100.0

        if coverage < 70:
            warnings.append(f"⚠️ 씬 반영률 부족: {reflected}/{expected_scenes} ({coverage:.1f}%)")
        elif coverage < 85:
            warnings.append(f"⚠️ 씬 반영률 주의: {reflected}/{expected_scenes} ({coverage:.1f}%)")

        return {
            "coverage": round(coverage, 1),
            "expected": expected_scenes,
            "reflected": reflected,
            "missing_scenes": missing_scenes,
            "warnings": warnings
        }

    def _check_basic_continuity(self, manuscript: str, prev_manuscript: str, hud_report: str) -> Dict:
        """연속성 기초 체크"""
        warnings = []
        focus_points = []
        issue_count = 0

        if not manuscript:
            return {"warnings": [], "focus_points": [], "issue_count": 0}

        # 1. 죽은 NPC 체크 (이전 원고에서 "죽었다", "사망", "숨을 거두" 등 탐지)
        if prev_manuscript:
            death_patterns = [
                r'([가-힣]{2,4})[이가은는]\s*(?:죽었다|사망했다|숨을\s*거두|최후를\s*맞|절명)',
                r'([가-힣]{2,4})[의]\s*(?:시신|주검|유해)',
            ]
            for pattern in death_patterns:
                matches = re.findall(pattern, prev_manuscript)
                self._dead_npcs.update(matches)

            # 죽은 NPC가 현재 원고에서 말하거나 행동하면 경고
            for npc in self._dead_npcs:
                if len(npc) >= 2:
                    # 대화나 행동 패턴
                    alive_patterns = [
                        f'{npc}[이가은는]\\s*말했다',
                        f'{npc}[이가은는]\\s*웃',
                        f'"{npc}"[이가은는]',
                        f'{npc}[이가은는]\\s*(?:검을|칼을|창을)',
                    ]
                    for pattern in alive_patterns:
                        if re.search(pattern, manuscript):
                            warnings.append(f"⚠️ 죽은 NPC '{npc}' 활동 의심")
                            focus_points.append(f"연속성: 죽은 NPC '{npc}' 언급")
                            issue_count += 1
                            break

        # 2. HUD 상태 불일치 체크
        if hud_report:
            # 부상 상태 체크
            if "중상" in hud_report or "내상" in hud_report:
                # 중상인데 전력 질주/격렬한 전투 묘사
                intense_patterns = [
                    r'전력으로\s*(?:달렸다|질주|뛰어)',
                    r'온\s*힘을\s*다해',
                    r'맹렬하게\s*(?:공격|싸)',
                ]
                for pattern in intense_patterns:
                    if re.search(pattern, manuscript):
                        warnings.append("⚠️ 중상 상태에서 격렬한 활동 묘사")
                        focus_points.append("연속성: 부상 상태 불일치 의심")
                        issue_count += 1
                        break

            # 내공 고갈 상태 체크
            if "내공" in hud_report and ("0%" in hud_report or "고갈" in hud_report):
                qi_patterns = [
                    r'내공을\s*(?:끌어|운용|발출)',
                    r'진기를\s*(?:끌어|운용)',
                    r'기운을\s*(?:모아|집중)',
                ]
                for pattern in qi_patterns:
                    if re.search(pattern, manuscript):
                        warnings.append("⚠️ 내공 고갈 상태에서 내공 사용 묘사")
                        focus_points.append("연속성: 내공 상태 불일치 의심")
                        issue_count += 1
                        break

        return {
            "warnings": warnings,
            "focus_points": focus_points,
            "issue_count": issue_count
        }

    def _check_blueprint_keywords(self, manuscript: str, blueprint: dict) -> Dict:
        """Blueprint 핵심 키워드 체크"""
        if not blueprint or not isinstance(blueprint, dict):
            return {"warnings": [], "missing_keywords": []}

        warnings = []
        missing_keywords = []

        # 통합 시나리오에서 핵심 키워드 추출
        integrated = blueprint.get("integrated_scenario", "")
        if integrated:
            # 고유명사 추출 (작은따옴표로 감싸진 단어)
            proper_nouns = re.findall(r"'([가-힣]{2,6})'", integrated)
            # 중요 키워드 (대괄호 안)
            important = re.findall(r'\[([가-힣]{2,10})\]', integrated)

            check_keywords = list(set(proper_nouns + important))[:10]

            for keyword in check_keywords:
                if len(keyword) >= 2 and keyword not in manuscript:
                    missing_keywords.append(keyword)

        if missing_keywords:
            warnings.append(f"⚠️ Blueprint 핵심 키워드 미반영 의심: {', '.join(missing_keywords[:5])}")

        return {
            "warnings": warnings,
            "missing_keywords": missing_keywords
        }

    def _check_ending_quality(self, manuscript: str) -> Dict:
        """후반부/엔딩 품질 체크"""
        if not manuscript or len(manuscript) < 1000:
            return {"warnings": []}

        warnings = []

        # 마지막 500자 추출
        ending = manuscript[-500:]

        # 1. 급격한 마무리 패턴 체크
        abrupt_patterns = [
            r'이렇게.*끝났다',
            r'모든.*해결되었다',
            r'아무.*일.*없었다',
            r'평화롭게.*마무리',
        ]
        for pattern in abrupt_patterns:
            if re.search(pattern, ending):
                warnings.append("⚠️ 급격한 마무리 의심 (클리프행어 부재)")
                break

        # 2. 후반부 밀도 체크 (마지막 20%가 너무 짧은 문장들로만 구성)
        last_portion = manuscript[int(len(manuscript) * 0.8):]
        sentences = re.split(r'[.!?]\s*', last_portion)
        short_sentences = [s for s in sentences if len(s.strip()) < 15 and len(s.strip()) > 0]

        if len(short_sentences) > len(sentences) * 0.7:
            warnings.append("⚠️ 후반부 문장 밀도 급락 의심")

        return {"warnings": warnings}

    def format_warnings_for_director(self, validation_results: List[Dict]) -> str:
        """Director에게 전달할 경고 포맷 생성"""
        lines = ["### 📋 Python 사전 검증 결과 (참고용 - REJECT 권한 없음)"]
        lines.append("")

        for i, result in enumerate(validation_results):
            strategy = result.get("strategy", f"후보{i+1}")
            warning_count = result.get("warning_count", 0)
            metrics = result.get("metrics", {})

            lines.append(f"**[{strategy}]** 경고 {warning_count}개")
            lines.append(f"  - 분량: {metrics.get('length', 0)}자")
            lines.append(f"  - 씬 반영률: {metrics.get('scene_coverage', 0)}%")

            if result.get("focus_points"):
                lines.append("  - 집중 검토 포인트:")
                for point in result["focus_points"][:3]:
                    lines.append(f"    ⚠️ {point}")

            lines.append("")

        lines.append("---")
        lines.append("위 경고는 참고용입니다. 최종 판단은 Director가 내립니다.")

        return "\n".join(lines)
