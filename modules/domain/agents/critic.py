"""
[V49.3 → V52.2] Critic Agent - 적대적 원고 비평 에이전트

Writer와 별도로 원고를 공격적으로 비판하여 품질을 향상시킵니다.
Writer의 self-critique보다 더 엄격한 기준으로 평가합니다.

V52.2 업데이트:
- 7가지 관점 심층 리뷰 (LLM 기반)
- PASS/REVISE/MAJOR_REVISE 권장사항
- Writer 피드백 자동 생성
"""

import json
import logging
import re

from modules.core.constants import ManuscriptLimits

from .base_agent import BaseAgent


class Critic(BaseAgent):
    """
    [V49.3] 적대적 비평 에이전트

    Writer가 생성한 원고를 독립적으로 비판하여 품질 문제를 지적합니다.
    Writer의 자기 비평보다 더 엄격한 기준을 적용합니다.

    Usage:
        critic = Critic(context, client)
        critique = critic.critique_manuscript(manuscript, hud_report, genre)
        if critique['severity'] == 'high':
            # 재작성 필요
    """

    def __init__(self, context, client, model_tier=None) -> None:
        super().__init__(context, client, model_tier)
        self._agent_name = "Critic"

    def critique_manuscript(self, manuscript: str, hud_report: str, genre: str, prev_manuscript: str = "") -> dict:
        """
        원고를 적대적으로 비평

        Args:
            manuscript: 비평할 원고 (JSON 문자열)
            hud_report: HUD 정보
            genre: 장르
            prev_manuscript: 직전 원고 (연속성 검증용)

        Returns:
            {
                "issues": [{"type": str, "severity": str, "description": str, "location": str}],
                "severity": "low" | "medium" | "high",
                "score": int (0-100),
                "recommendations": [str]
            }
        """
        logging.info("👹 [Critic] 적대적 비평 시작...")

        # JSON 파싱
        try:
            data = json.loads(manuscript)
            content = data.get("content", "")
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
            content = manuscript

        if not content or len(content) < 100:
            return {
                "issues": [
                    {"type": "empty", "severity": "critical", "description": "원고가 너무 짧음", "location": "전체"}
                ],
                "severity": "high",
                "score": 0,
                "recommendations": [f"최소 {ManuscriptLimits.MIN_LENGTH}자 이상의 원고 필요"],
            }

        # 다각도 비평 수행
        issues = []

        # 1. Show Don't Tell 비평
        sdt_issues = self._critique_show_dont_tell(content)
        issues.extend(sdt_issues)

        # 2. 문장 시작 다양성 비평
        starter_issues = self._critique_sentence_starters(content)
        issues.extend(starter_issues)

        # 3. 클리셰 비평
        cliche_issues = self._critique_cliches(content, genre)
        issues.extend(cliche_issues)

        # 4. HUD 일관성 비평
        hud_issues = self._critique_hud_consistency(content, hud_report)
        issues.extend(hud_issues)

        # 5. 연속성 비평 (직전 원고가 있을 경우)
        if prev_manuscript:
            continuity_issues = self._critique_continuity(content, prev_manuscript)
            issues.extend(continuity_issues)

        # 6. 대화 자연스러움 비평
        dialogue_issues = self._critique_dialogue(content)
        issues.extend(dialogue_issues)

        # 심각도 및 점수 계산
        severity, score = self._calculate_severity_score(issues)

        # 권장 사항 생성
        recommendations = self._generate_recommendations(issues, genre)

        result = {"issues": issues, "severity": severity, "score": score, "recommendations": recommendations}

        logging.info(f"👹 [Critic] 비평 완료: {len(issues)}건, 심각도={severity}, 점수={score}/100")

        return result

    def _critique_show_dont_tell(self, content: str) -> list:
        """Show Don't Tell 위반 검출"""
        issues = []

        # 직접 감정 표현 패턴
        direct_emotions = {
            "기뻤다": "감정을 행동/신체 반응으로",
            "슬펐다": "눈물, 떨림 등 신체 묘사로",
            "화났다": "주먹 쥠, 이 악문 등으로",
            "놀랐다": "눈 확대, 숨 멈춤 등으로",
            "두려웠다": "떨림, 식은땀 등으로",
            "경악했다": "동작/표정 묘사로",
            "분노했다": "신체 반응으로",
            "당황했다": "행동 묘사로",
            "감동했다": "신체 반응으로",
        }

        for emotion, suggestion in direct_emotions.items():
            count = content.count(emotion)
            if count >= 2:
                issues.append(
                    {
                        "type": "show_dont_tell",
                        "severity": "medium" if count < 4 else "high",
                        "description": f"'{emotion}' 직접 표현 {count}회 사용 → {suggestion}",
                        "location": "본문 전체",
                    }
                )

        return issues

    def _critique_sentence_starters(self, content: str) -> list:
        """문장 시작 다양성 검사"""
        issues = []

        # 문장 분리
        sentences = [s.strip() for s in re.split(r"[.!?]", content) if len(s.strip()) > 5]
        if len(sentences) < 10:
            return issues

        # 첫 2글자 추출
        starters = [s[:2] for s in sentences]

        # 반복 카운트
        from collections import Counter

        starter_counts = Counter(starters)

        # 과도한 반복 검출
        for starter, count in starter_counts.most_common(5):
            ratio = count / len(starters)
            if ratio > 0.15:  # 15% 초과 시 문제
                issues.append(
                    {
                        "type": "starter_repetition",
                        "severity": "medium" if ratio < 0.25 else "high",
                        "description": f"'{starter}'로 시작하는 문장 {count}회 ({ratio:.0%}) - 다양화 필요",
                        "location": "문장 시작부",
                    }
                )

        return issues

    def _critique_cliches(self, content: str, genre: str) -> list:
        """클리셰 과다 사용 검출"""
        issues = []

        # 장르별 클리셰 패턴
        cliche_patterns = {
            "무협": [
                ("피를 토하", "부상 표현 다양화"),
                ("살기", "적의 표현 다양화"),
                ("내공이 폭발", "파워업 표현 다양화"),
                ("검기", "무공 표현 다양화"),
                ("허름한 행색", "외모 묘사 다양화"),
                ("경외", "반응 묘사 다양화"),
                ("전율", "감정 표현 다양화"),
            ],
            "헌터": [
                ("마나가 폭발", "능력 표현 다양화"),
                ("스킬을 시전", "행동 표현 다양화"),
                ("레벨업", "성장 표현 다양화"),
            ],
            "투자": [
                ("주가가 폭등", "시장 표현 다양화"),
                ("대박", "성공 표현 다양화"),
            ],
        }

        patterns = cliche_patterns.get(genre, cliche_patterns["무협"])

        for pattern, suggestion in patterns:
            count = content.count(pattern)
            if count >= 3:
                issues.append(
                    {
                        "type": "cliche_overuse",
                        "severity": "low" if count < 5 else "medium",
                        "description": f"'{pattern}' {count}회 사용 - {suggestion}",
                        "location": "본문",
                    }
                )

        return issues

    def _critique_hud_consistency(self, content: str, hud_report: str) -> list:
        """HUD와 원고 일관성 검사"""
        issues = []

        # 부상 상태 체크
        injury_keywords = ["중상", "부상", "상처", "피를 흘리", "부러진"]
        has_injury = any(kw in hud_report for kw in injury_keywords)

        if has_injury:
            # 무리한 행동 체크
            strong_actions = ["일격에", "박살", "압도", "제압", "분쇄", "날아올라"]
            for action in strong_actions:
                if action in content:
                    # 정당화 키워드 체크
                    justifications = ["고통을 참", "억지로", "대가", "무리", "피를 흘리며"]
                    has_justification = any(j in content for j in justifications)

                    if not has_justification:
                        issues.append(
                            {
                                "type": "hud_inconsistency",
                                "severity": "high",
                                "description": f"부상 상태에서 '{action}' 행동 - 정당화 누락",
                                "location": "전투 장면",
                            }
                        )
                        break

        return issues

    def _critique_continuity(self, content: str, prev_content: str) -> list:
        """직전 원고와의 연속성 검사"""
        issues = []

        try:
            prev_data = json.loads(prev_content)
            prev_text = prev_data.get("content", "")
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
            prev_text = prev_content

        if not prev_text:
            return issues

        # 직전 원고 마지막 200자
        prev_ending = prev_text[-200:]

        # 위치 키워드 추출
        location_patterns = [r"(객잔|주점|광장|산|숲|강|절벽|동굴|방|전각|연무장)"]

        prev_locations = []
        for pattern in location_patterns:
            prev_locations.extend(re.findall(pattern, prev_ending))

        current_start = content[:200]
        current_locations = []
        for pattern in location_patterns:
            current_locations.extend(re.findall(pattern, current_start))

        # 위치 급변 체크
        if prev_locations and current_locations:
            if not any(loc in current_locations for loc in prev_locations):
                issues.append(
                    {
                        "type": "location_jump",
                        "severity": "medium",
                        "description": f"위치 급변: {prev_locations[0]} → {current_locations[0]} (이동 묘사 필요)",
                        "location": "도입부",
                    }
                )

        return issues

    def _critique_dialogue(self, content: str) -> list:
        """대화 자연스러움 검사"""
        issues = []

        # 대화 추출
        dialogues = re.findall(r'["\']([^"\']+)["\']', content)

        if len(dialogues) < 3:
            issues.append(
                {
                    "type": "dialogue_lack",
                    "severity": "low",
                    "description": "대화가 너무 적음 - 캐릭터 상호작용 추가 권장",
                    "location": "전체",
                }
            )
            return issues

        # 대화 길이 분석
        avg_length = sum(len(d) for d in dialogues) / len(dialogues)
        if avg_length > 100:
            issues.append(
                {
                    "type": "dialogue_long",
                    "severity": "low",
                    "description": f"평균 대사 길이 {avg_length:.0f}자 - 간결한 대화 권장",
                    "location": "대화문",
                }
            )

        # 반복 패턴 검출
        dialogue_starters = [d[:5] for d in dialogues if len(d) > 5]
        if len(dialogue_starters) > 5:
            from collections import Counter

            starter_counts = Counter(dialogue_starters)
            for starter, count in starter_counts.most_common(3):
                if count >= 3:
                    issues.append(
                        {
                            "type": "dialogue_repetition",
                            "severity": "low",
                            "description": f"대화 시작 '{starter}...' {count}회 반복",
                            "location": "대화문",
                        }
                    )

        return issues

    def _calculate_severity_score(self, issues: list) -> tuple:
        """심각도 및 점수 계산"""
        if not issues:
            return "low", 95

        severity_weights = {"low": 1, "medium": 3, "high": 5, "critical": 10}
        total_weight = sum(severity_weights.get(i["severity"], 1) for i in issues)

        # 점수 계산 (100점 만점)
        score = max(0, 100 - total_weight * 3)

        # 심각도 결정
        high_count = sum(1 for i in issues if i["severity"] in ["high", "critical"])
        medium_count = sum(1 for i in issues if i["severity"] == "medium")

        if high_count >= 2 or score < 60:
            severity = "high"
        elif high_count >= 1 or medium_count >= 3 or score < 75:
            severity = "medium"
        else:
            severity = "low"

        return severity, score

    def _generate_recommendations(self, issues: list, genre: str) -> list:
        """권장 사항 생성"""
        recommendations = []

        issue_types = [i["type"] for i in issues]

        if "show_dont_tell" in issue_types:
            recommendations.append("감정을 직접 서술하지 말고 행동/신체 반응으로 보여주세요")

        if "starter_repetition" in issue_types:
            recommendations.append("문장 시작을 다양화하세요 (주어 변경, 부사구로 시작 등)")

        if "cliche_overuse" in issue_types:
            recommendations.append("장르 클리셰를 줄이고 독창적인 표현을 사용하세요")

        if "hud_inconsistency" in issue_types:
            recommendations.append("캐릭터 상태(부상, 피로)를 행동에 반영하세요")

        if "location_jump" in issue_types:
            recommendations.append("위치 이동 시 이동 과정을 명시하세요")

        if "dialogue_lack" in issue_types:
            recommendations.append("캐릭터 간 대화를 추가하여 상호작용을 보여주세요")

        return recommendations[:5]  # 최대 5개

    def get_llm_critique(self, manuscript: str, hud_report: str, genre: str) -> dict:
        """
        LLM을 사용한 심층 비평 (비용 발생)

        Python 기반 비평으로 부족할 때 사용

        Args:
            manuscript: 원고
            hud_report: HUD 정보
            genre: 장르

        Returns:
            LLM 비평 결과
        """
        prompt = f"""
당신은 엄격한 소설 평론가입니다. 아래 원고를 공격적으로 비판하세요.

[장르]: {genre}
[주인공 상태]: {hud_report}

[원고]
{manuscript[:20000]}

[비평 기준]
1. "Show Don't Tell" - 감정을 직접 서술했는가?
2. 문장 다양성 - 문장 시작이 반복되는가?
3. 클리셰 - 진부한 표현이 과다한가?
4. HUD 일관성 - 캐릭터 상태가 행동에 반영되었는가?
5. 대화 자연스러움 - 대화가 자연스러운가?

[출력 형식] JSON Only
{{
    "overall_score": 0-100,
    "issues": [
        {{"type": "...", "severity": "low/medium/high", "description": "...", "quote": "문제 구절"}}
    ],
    "best_parts": ["잘 쓴 부분 인용"],
    "worst_parts": ["고쳐야 할 부분 인용"],
    "recommendations": ["구체적 개선 제안"]
}}
"""

        try:
            response = self.ask(prompt, temperature=0.3)
            return self._extract_json_robust(response)
        except Exception as e:
            logging.warning(f"❌ [Critic] LLM 비평 실패: {e}")
            return {}

    # ================================================================
    # [V52.2] 7가지 관점 심층 리뷰
    # ================================================================

    DEEP_REVIEW_PROMPT = """당신은 출판사의 수석 편집자입니다. 웹소설 원고를 날카롭게 비평하되,
건설적인 방향을 제시해야 합니다.

[원고]
{manuscript}

[설계도 (Blueprint)]
{blueprint}

[맥락 정보]
- 에피소드: {ep_num}화
- 장르: {genre}
- 직전 화 엔딩: {prev_ending}

다음 7가지 관점에서 원고를 분석하세요:

## 1. 서사 밀도 (Narrative Density)
- 장면당 사건 밀도가 적절한가?

## 2. 캐릭터 일관성 (Character Consistency)
- 캐릭터가 자신답게 행동하는가?

## 3. 대화 품질 (Dialogue Quality)
- 대화가 자연스럽고 캐릭터를 드러내는가?

## 4. 감정 흐름 (Emotional Arc)
- 독자의 감정을 적절히 유도하는가?

## 5. 긴장감 관리 (Tension Management)
- 클리프행어가 효과적인가?

## 6. 설계 준수 (Blueprint Adherence)
- Blueprint의 핵심 씬들이 모두 반영되었는가?

## 7. 상업성 (Commercial Appeal)
- 독자가 다음 화를 클릭하게 만드는가?

---

JSON 형식으로 응답:
```json
{{
    "scores": {{
        "narrative_density": 1-10,
        "character_consistency": 1-10,
        "dialogue_quality": 1-10,
        "emotional_arc": 1-10,
        "tension_management": 1-10,
        "blueprint_adherence": 1-10,
        "commercial_appeal": 1-10
    }},
    "overall_score": 1-10,
    "recommendation": "PASS|REVISE|MAJOR_REVISE",
    "strengths": ["강점1", "강점2"],
    "weaknesses": ["약점1", "약점2"],
    "revision_priority": [
        {{"issue": "문제점", "suggestion": "개선 방향"}}
    ],
    "specific_feedback": "Writer에게 전달할 구체적인 피드백"
}}
```"""

    def deep_review(
        self, manuscript: str, blueprint: dict, ep_num: int, genre: str = "무협", prev_ending: str = ""
    ) -> dict:
        """
        [V52.2] 7가지 관점 심층 리뷰

        Args:
            manuscript: 원고 텍스트
            blueprint: 블루프린트 딕셔너리
            ep_num: 에피소드 번호
            genre: 장르
            prev_ending: 직전 화 엔딩

        Returns:
            {
                "scores": {...},
                "overall_score": int,
                "recommendation": "PASS|REVISE|MAJOR_REVISE",
                "strengths": [...],
                "weaknesses": [...],
                "revision_priority": [...],
                "specific_feedback": str
            }
        """
        logging.info("🔍 [V52.2 Critic] 7가지 관점 심층 리뷰 중...")

        import json as json_module

        blueprint_text = json_module.dumps(blueprint, ensure_ascii=False, indent=2)[:10000] if blueprint else "없음"

        prompt = self.DEEP_REVIEW_PROMPT.format(
            manuscript=self._escape_braces(manuscript[:30000]),
            blueprint=self._escape_braces(blueprint_text),
            ep_num=ep_num,
            genre=genre,
            prev_ending=self._escape_braces(prev_ending[:500]) if prev_ending else "없음",
        )

        try:
            response = self.ask(prompt, temperature=0.2)
            result = self._extract_json_robust(response)

            if not result:
                return self._default_review_result()

            # 점수 기반 권장사항 보정
            overall = result.get("overall_score", 7)
            if overall >= 8:
                result["recommendation"] = "PASS"
            elif overall >= 6:
                result["recommendation"] = "REVISE"
            else:
                result["recommendation"] = "MAJOR_REVISE"

            logging.info(f"🔍 [V52.2 Critic] 완료: {overall}/10, 권장={result['recommendation']}")
            return result

        except Exception as e:
            logging.warning(f"❌ [V52.2 Critic] 심층 리뷰 실패: {e}")
            return self._default_review_result()

    def _default_review_result(self) -> dict:
        """기본 리뷰 결과"""
        return {
            "scores": {},
            "overall_score": 7,
            "recommendation": "PASS",
            "strengths": [],
            "weaknesses": [],
            "revision_priority": [],
            "specific_feedback": "",
        }

    def generate_revision_feedback(self, review_result: dict) -> str:
        """
        [V52.2] 리뷰 결과를 Writer 피드백 형태로 변환

        Args:
            review_result: deep_review 또는 critique_manuscript 결과

        Returns:
            Writer에게 전달할 피드백 문자열
        """
        recommendation = review_result.get("recommendation", "PASS")
        if recommendation == "PASS":
            return ""

        lines = ["[V52.2 Critic 피드백]"]

        # 점수 (deep_review용)
        overall = review_result.get("overall_score")
        if overall:
            lines.append(f"전체 점수: {overall}/10")

        # 점수 (critique_manuscript용)
        score = review_result.get("score")
        if score is not None:
            lines.append(f"품질 점수: {score}/100")

        # 약점
        weaknesses = review_result.get("weaknesses", [])
        if weaknesses:
            lines.append("\n[개선 필요]")
            for w in weaknesses[:3]:
                lines.append(f"- {w}")

        # 우선 수정 사항
        priorities = review_result.get("revision_priority", [])
        if priorities:
            lines.append("\n[수정 우선순위]")
            for i, p in enumerate(priorities[:3], 1):
                issue = p.get("issue", "") if isinstance(p, dict) else str(p)
                suggestion = p.get("suggestion", "") if isinstance(p, dict) else ""
                if suggestion:
                    lines.append(f"{i}. {issue}: {suggestion}")
                else:
                    lines.append(f"{i}. {issue}")

        # 권장 사항 (critique_manuscript용)
        recommendations = review_result.get("recommendations", [])
        if recommendations:
            lines.append("\n[권장 사항]")
            for r in recommendations[:3]:
                lines.append(f"- {r}")

        # 구체적 피드백
        specific = review_result.get("specific_feedback", "")
        if specific:
            lines.append(f"\n[편집자 코멘트]\n{specific}")

        return "\n".join(lines)

    def hybrid_review(
        self,
        manuscript: str,
        blueprint: dict,
        ep_num: int,
        genre: str = "무협",
        prev_manuscript: str = "",
        hud_report: str = "",
        use_llm: bool = True,
    ) -> dict:
        """
        [V52.2] Python 비평 + LLM 심층 리뷰 통합

        Args:
            manuscript: 원고 텍스트
            blueprint: 블루프린트
            ep_num: 에피소드 번호
            genre: 장르
            prev_manuscript: 직전 원고
            hud_report: HUD 정보
            use_llm: LLM 심층 리뷰 사용 여부

        Returns:
            통합 리뷰 결과
        """
        # 1. Python 기반 빠른 비평 (무료)
        python_result = self.critique_manuscript(
            manuscript=manuscript, hud_report=hud_report, genre=genre, prev_manuscript=prev_manuscript
        )

        # Python 비평에서 심각한 문제 발견 시 바로 반환
        if python_result.get("severity") == "high":
            python_result["recommendation"] = "MAJOR_REVISE"
            return python_result

        # 2. LLM 심층 리뷰 (선택적)
        if use_llm and python_result.get("severity") != "low":
            prev_ending = ""
            if prev_manuscript:
                try:
                    import json as json_module

                    prev_data = json_module.loads(prev_manuscript)
                    prev_ending = prev_data.get("content", "")[-300:]
                except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
                    prev_ending = prev_manuscript[-300:]

            llm_result = self.deep_review(
                manuscript=manuscript, blueprint=blueprint, ep_num=ep_num, genre=genre, prev_ending=prev_ending
            )

            # 결과 통합
            combined = {
                "python_issues": python_result.get("issues", []),
                "python_score": python_result.get("score", 0),
                "python_severity": python_result.get("severity", "low"),
                "llm_scores": llm_result.get("scores", {}),
                "overall_score": llm_result.get("overall_score", 7),
                "recommendation": llm_result.get("recommendation", "PASS"),
                "strengths": llm_result.get("strengths", []),
                "weaknesses": llm_result.get("weaknesses", []),
                "revision_priority": llm_result.get("revision_priority", []),
                "specific_feedback": llm_result.get("specific_feedback", ""),
                "recommendations": python_result.get("recommendations", []),
            }

            return combined

        # LLM 미사용 시 Python 결과만 반환
        if python_result.get("severity") == "medium":
            python_result["recommendation"] = "REVISE"
        else:
            python_result["recommendation"] = "PASS"

        return python_result
