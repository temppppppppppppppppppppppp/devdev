"""
[B-1-5] ChiefWriter Quality Gate ? Self-Critique + quality pipeline.
"""

import json
import logging
import re

from .chief_writer_prompts import get_fix_issues_prompt


class ChiefWriterQualityGate:
    """ChiefWriter? Self-Critique + ?? ?? ?? ????."""

    CLICHE_WINDOW = 10  # [Sweep3-E3] 클리셰 감지 윈도우 크기

    def __init__(self, host):
        self.host = host

    def sanitize_leakage(self, text: str) -> str:
        """
        [V60.81] Writer 출력 누수(Leakage) 방지용 사후 필터

        미래 씬 정보, 메타데이터 등 원고에 포함되면 안 되는 정보 제거
        """
        if not text:
            return text

        # 1. JSON 구조적 정제 시도
        try:
            clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()
            data = json.loads(clean_text)

            # 금지된 키 리스트 (누수 주범)
            banned_keys = [
                "Beat 3",
                "Beat 4",
                "continuation_text",
                "scene_summary",
                "future_hint",
                "next_episode",
                "spoiler",
            ]

            if isinstance(data, dict):
                for key in banned_keys:
                    if key in data:
                        del data[key]
                return json.dumps(data, ensure_ascii=False, indent=4)
        except (json.JSONDecodeError, ValueError) as e:
            logging.debug(f"[V66.3] ChiefWriter JSON 파싱 부분실패: {e}")

        # 2. 텍스트 라인 필터링 (비상 대책)
        filtered_lines = []
        for line in text.splitlines():
            if re.search(r'"(Beat \d+|continuation_text|future_hint)":', line):
                continue
            filtered_lines.append(line)

        text = "\n".join(filtered_lines)

        # 3. 영문 괄호 병기 제거: "윈도우(Windows)" → "윈도우"
        text = re.sub(r"([가-힣]+)\([A-Za-z][A-Za-z\s&\-\'\.,;:0-9]*\)", r"\1", text)

        return text

    def apply_self_critique(
        self, manuscript: str, hud_report: str, npcs: list, genre_name: str, ep_num: int = None
    ) -> str:
        """
        [V60.81] Self-Critique 다중 라운드 적용

        원고에 Self-Critique를 최대 3회 반복 실행하고, 문제가 있으면 수정 후 반환

        Args:
            manuscript: 원고 (JSON 문자열)
            hud_report: HUD 정보
            npcs: NPC 리스트
            genre_name: 장르
            ep_num: 에피소드 번호

        Returns:
            str: 검토 및 수정된 원고
        """
        encyclopedia = {"npcs": npcs}
        MAX_CRITIQUE_ROUNDS = 3

        current_manuscript = manuscript
        total_issues_fixed = 0

        # [V60.82] 조기 스킵 조건 - Rubric 점수로 사전 평가
        rubric_score = self._evaluate_with_rubric(current_manuscript, genre_name)
        if rubric_score >= 3.5:
            # 이미 품질 높음 - Self-Critique 스킵
            return current_manuscript

        for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
            critique_result = self._self_critique(current_manuscript, hud_report, encyclopedia, genre_name, ep_num)

            if not critique_result["has_issues"]:
                if round_num > 1:
                    logging.info(f"[ChiefWriter] Self-Critique R{round_num}: 완료 ({total_issues_fixed}건 수정)")
                break

            if critique_result["severity"] == "low":
                break

            # [V60.82] 라운드 중간 Rubric 체크 - 3.5 이상이면 조기 종료
            if round_num > 1:
                mid_score = self._evaluate_with_rubric(current_manuscript, genre_name)
                if mid_score >= 3.5:
                    break

            logging.info(
                f"[ChiefWriter] Self-Critique R{round_num}/{MAX_CRITIQUE_ROUNDS}: {len(critique_result['issues'])}건..."
            )
            current_manuscript = self._fix_manuscript_issues(current_manuscript, critique_result, hud_report)
            total_issues_fixed += len(critique_result["issues"])

        return current_manuscript

    def _self_critique(
        self, manuscript: str, hud_report: str, encyclopedia: dict, genre_name: str, ep_num: int = None
    ) -> dict:
        """
        [V60.81] Writer Self-Critic - 원고 자체 검토

        Returns:
            {
                "has_issues": bool,
                "issues": [...],
                "severity": "low" | "medium" | "high"
            }
        """
        # JSON 파싱
        try:
            data = json.loads(manuscript)
            content = data.get("content", "")
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
            content = manuscript

        issues = []

        # 1. HUD 모순 체크
        hud_issues = self._check_hud_consistency(content, hud_report)
        issues.extend(hud_issues)

        # 2. 클리셰 과다 체크
        cliche_issues = self._check_cliche_overuse(content, genre_name, ep_num)
        issues.extend(cliche_issues)

        # 3. 정당화 부족 체크
        justification_issues = self._check_justification_gaps(content, hud_report)
        issues.extend(justification_issues)

        # 4. NPC 관계 일관성 체크
        npc_issues = self._check_npc_relationship(content, encyclopedia)
        issues.extend(npc_issues)

        # 심각도 판단
        severity = "low"
        if len(issues) >= 3:
            severity = "high"
        elif len(issues) >= 1:
            severity = "medium"

        has_issues = len(issues) > 0

        return {"has_issues": has_issues, "issues": issues, "severity": severity}

    def _check_hud_consistency(self, content: str, hud_report: str) -> list:
        """HUD 모순 체크"""
        issues = []
        if not hud_report:
            return issues
        weak_keywords = ["나약", "중독", "부상", "중상", "쇠약", "기력고갈", "빈사"]
        strong_actions = ["일격에", "압도", "박살", "분쇄", "제압", "일도양단"]

        is_weak = any(kw in hud_report for kw in weak_keywords)
        has_strong_action = any(kw in content for kw in strong_actions)

        if is_weak and has_strong_action:
            justification_kws = ["발경", "기혈", "폭발", "전생", "대가", "고통", "각오", "최후"]
            has_justification = any(kw in content for kw in justification_kws)

            if not has_justification:
                issues.append(
                    {
                        "type": "hud_contradiction",
                        "description": "나약한 상태에서 강력한 행동, 정당화 부족",
                        "location": "본문",
                        "severity": "medium",
                    }
                )

        return issues

    def _check_cliche_overuse(self, content: str, genre_name: str, ep_num: int = None) -> list:
        """클리셰 과다 사용 체크"""
        issues = []

        # 최근 빈도 체크
        if ep_num is not None and ep_num > 1:
            recent_counts = self._count_recent_cliches(ep_num, content, window=self.CLICHE_WINDOW)

            overused = [f"'{keyword}' ({count}회)" for keyword, count in recent_counts.items() if count >= 3]

            if overused:
                issues.append(
                    {
                        "type": "cliche_overuse_recent",
                        "description": f"최근 클리셰 과용: {', '.join(overused[:3])}",
                        "location": "최근 10화",
                        "severity": "medium",
                        "recommendation": "다른 표현으로 다양화 필요",
                    }
                )

        # 무협 클리셰 패턴
        if genre_name == "무협":
            cliche_patterns = [
                ("무시", "별 볼일"),
                ("무시", "평범해"),
                ("허름", "행색"),
                ("조롱", "비웃"),
            ]

            cliche_count = 0
            for pattern1, pattern2 in cliche_patterns:
                if pattern1 in content and pattern2 in content:
                    cliche_count += 1

            if cliche_count >= 2:
                issues.append(
                    {
                        "type": "cliche_overuse",
                        "description": f"무협 클리셰 패턴이 {cliche_count}회 반복",
                        "location": "본문",
                        "severity": "low",
                    }
                )

        return issues

    def _check_justification_gaps(self, content: str, hud_report: str) -> list:
        """정당화 누락 체크"""
        issues = []
        if not hud_report:
            return issues
        constraints = []
        if "나약" in hud_report or "중독" in hud_report:
            constraints.append("physical")
        if "reputation" in hud_report.lower():
            rep_match = re.search(r"reputation[:\s]+(\d+)", hud_report, re.IGNORECASE)
            if rep_match and int(rep_match.group(1)) < 30:
                constraints.append("authority")

        if "physical" in constraints:
            overcome_keywords = ["이루어", "성공", "압도", "제압"]
            has_overcome = any(kw in content for kw in overcome_keywords)

            if has_overcome:
                just_kws = ["때문에", "덕분에", "활용", "방법", "대가"]
                has_just = any(kw in content for kw in just_kws)

                if not has_just:
                    issues.append(
                        {
                            "type": "justification_gap",
                            "description": "제약 극복 장면에 정당화 표현 부족",
                            "location": "본문",
                            "severity": "medium",
                        }
                    )

        return issues

    def _check_npc_relationship(self, content: str, encyclopedia: dict) -> list:
        """NPC 관계 일관성 체크"""
        issues = []

        npcs = encyclopedia.get("npcs", [])

        for npc in npcs:
            if not isinstance(npc, dict):
                continue

            name = npc.get("name", "")
            if not name or name not in content:
                continue

            relationship = npc.get("relationship_state", "중립")

            # 경외 상태인데 무시 표현이 있는가?
            if relationship in ["경외", "충성", "존경"]:
                disrespect_keywords = ["무시", "비웃", "조롱", "업신여"]
                for kw in disrespect_keywords:
                    if kw in content:
                        # NPC가 주인공을 무시하는 맥락인지 확인
                        context_pattern = f"{name}.*{kw}|{kw}.*{name}"
                        if re.search(context_pattern, content):
                            issues.append(
                                {
                                    "type": "npc_relationship_inconsistency",
                                    "description": f"'{name}'은 경외 상태인데 무시/조롱 표현 사용",
                                    "location": "본문",
                                    "severity": "medium",
                                }
                            )
                            break

        return issues

    def _fix_manuscript_issues(self, manuscript: str, critique_result: dict, hud_report: str) -> str:
        """
        [V60.81] 감지된 문제 수정

        LLM을 사용하여 문제점을 수정한 새 원고 반환
        """
        issues = critique_result.get("issues", [])
        if not issues:
            return manuscript

        # 수정 지시 구성
        fix_instructions = []
        for issue in issues[:3]:  # 최대 3개만 수정
            issue_type = issue.get("type", "unknown") if isinstance(issue, dict) else str(issue)
            issue_desc = issue.get("description", "") if isinstance(issue, dict) else ""
            fix_instructions.append(f"- {issue_type}: {issue_desc}")

        # [V65] 교정 프롬프트 함수 래핑 호출
        prompt = get_fix_issues_prompt(
            fix_instructions_text=chr(10).join(fix_instructions),
            hud_report_escaped=self.host._escape_braces(hud_report[:500]),
            manuscript_escaped=self.host._escape_braces(manuscript[:8000]),
        )
        try:
            fixed = self.host.ask(prompt, temperature=0.5, thinking_level="low")
            fixed = self.sanitize_leakage(fixed)

            # JSON 유효성 검증
            try:
                json.loads(fixed)
                return fixed
            except (json.JSONDecodeError, ValueError, TypeError):
                return manuscript  # 파싱 실패시 원본 유지
        except Exception as e:
            logging.warning(f"⚠️ [ChiefWriter] 수정 실패: {e}")
            return manuscript

    def _evaluate_with_rubric(self, manuscript: str, genre_name: str) -> float:
        """
        [V60.81] Rubric 기반 품질 평가

        Returns:
            float: 품질 점수 (1.0 ~ 4.0)
        """
        try:
            data = json.loads(manuscript)
            content = data.get("content", "")
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
            content = manuscript

        if not content or len(content) < 100:
            return 1.0

        scores = []

        # 1. 감정 표현 평가 (Show vs Tell)
        direct_emotions = ["기뻤다", "슬펐다", "화났다", "놀랐다", "두려웠다", "경악했다", "분노했다"]
        direct_count = sum(content.count(e) for e in direct_emotions)
        chars_per_1000 = len(content) / 1000
        direct_rate = direct_count / max(chars_per_1000, 1)

        if direct_rate <= 0.5:
            scores.append(4)
        elif direct_rate <= 1.5:
            scores.append(3)
        elif direct_rate <= 3.0:
            scores.append(2)
        else:
            scores.append(1)

        # 2. 문장 시작 다양성
        sentences = [s.strip() for s in re.split(r"[.!?]", content) if len(s.strip()) > 5]
        if sentences:
            starters = [s[:2] for s in sentences[:20]]
            unique_rate = len(set(starters)) / max(len(starters), 1)
            if unique_rate >= 0.7:
                scores.append(4)
            elif unique_rate >= 0.5:
                scores.append(3)
            elif unique_rate >= 0.3:
                scores.append(2)
            else:
                scores.append(1)
        else:
            scores.append(2)

        # 3. 대화 자연스러움 (대화 비율)
        dialogue_matches = re.findall(r'["\'].*?["\']', content)
        dialogue_chars = sum(len(d) for d in dialogue_matches)
        dialogue_ratio = dialogue_chars / max(len(content), 1)

        if 0.15 <= dialogue_ratio <= 0.40:
            scores.append(4)
        elif 0.10 <= dialogue_ratio <= 0.50:
            scores.append(3)
        elif dialogue_ratio > 0:
            scores.append(2)
        else:
            scores.append(1)

        # 4. 오감 묘사 균형
        sensory_keywords = {
            "visual": ["보였다", "빛", "색", "어둠", "그림자"],
            "auditory": ["소리", "울림", "침묵", "들렸다", "속삭"],
            "tactile": ["차가", "뜨거", "거친", "부드러", "통증"],
            "olfactory": ["냄새", "향기", "악취", "피비린"],
        }
        sensory_counts = {k: sum(content.count(w) for w in words) for k, words in sensory_keywords.items()}
        active_senses = sum(1 for c in sensory_counts.values() if c > 0)

        if active_senses >= 3:
            scores.append(4)
        elif active_senses >= 2:
            scores.append(3)
        elif active_senses >= 1:
            scores.append(2)
        else:
            scores.append(1)

        avg_score = sum(scores) / len(scores) if scores else 2.0
        return round(avg_score, 1)

    def _count_recent_cliches(self, ep_num: int, manuscript: str, window: int = 10) -> dict:
        """
        최근 N화에서 클리셰 빈도 카운트
        """
        cliche_keywords = [
            "피를 토하",
            "기세",
            "살기",
            "냉기",
            "검기",
            "압도",
            "전율",
            "경악",
            "창백",
            "경외",
            "무시",
            "조롱",
            "비웃",
            "허름",
        ]

        counts = {keyword: 0 for keyword in cliche_keywords}

        # [V60.82] 캐시 사용 (DB 직접 조회 대신)
        for i in range(max(1, ep_num - window), ep_num):
            cached = self.host._get_cached_manuscript(i)
            content = cached.get("content", "")
            if content:
                for keyword in cliche_keywords:
                    counts[keyword] += content.count(keyword)

        # 현재 원고도 체크
        for keyword in cliche_keywords:
            counts[keyword] += manuscript.count(keyword)

        return {k: v for k, v in counts.items() if v > 0}
