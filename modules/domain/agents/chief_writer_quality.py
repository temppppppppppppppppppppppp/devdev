"""
[B-1-5] ChiefWriter Quality Gate ? Self-Critique + quality pipeline.
"""

import json
import logging
import re

from modules.core.constants import ManuscriptLimits
from modules.validation.threshold_helper import _threshold

from .chief_writer_prompts import get_expand_length_prompt, get_fix_issues_prompt


class ChiefWriterQualityGate:
    """ChiefWriter 품질 게이트 — 자기비판 + 클리셰/정당화/NPC/동기/산술 체크."""

    CLICHE_WINDOW = _threshold("quality.cliche_window", 10)  # [TF-5-04] validation.yaml 외부화
    AI_TELL_PHRASES = (
        "어느새",
        "말 그대로",
        "그야말로",
        "숨을 삼켰다",
        "시선을 돌렸다",
        "잠시 말을 잃었다",
        "입꼬리를 올렸다",
    )

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

    def _extract_content_text(self, manuscript: str) -> str:
        try:
            data = json.loads(manuscript)
            content = data.get("content", "") if isinstance(data, dict) else manuscript
        except (json.JSONDecodeError, ValueError, TypeError):
            content = manuscript

        if isinstance(content, list):
            return "\n".join(str(item) for item in content)
        if isinstance(content, dict):
            return content.get("text", "") or json.dumps(content, ensure_ascii=False)
        if isinstance(content, str):
            return content
        return str(content or "")

    def apply_self_critique(
        self,
        manuscript: str,
        hud_report: str,
        npcs: list,
        genre_name: str,
        ep_num: int = None,
        motivations: list = None,
        promises: list = None,
        blueprint=None,
        directive=None,
        expression_freq: dict | None = None,
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
        if blueprint is None:
            blueprint = getattr(self.host, "_current_blueprint", None)
        if directive is None:
            directive = getattr(self.host, "_tf54_writing_directive", None)
        if expression_freq is None:
            expression_freq = getattr(self.host, "_tf54_expression_freq", None)
        if not isinstance(expression_freq, dict):
            expression_freq = {}

        current_manuscript = manuscript
        total_issues_fixed = 0
        current_content_length = len(self._extract_content_text(current_manuscript))

        # [V60.82] 조기 스킵 조건 - Rubric 점수로 사전 평가
        rubric_score = self._evaluate_with_rubric(current_manuscript, genre_name)
        if rubric_score >= 3.5 and current_content_length >= int(ManuscriptLimits.MIN_LENGTH):
            # [TF-I08] 구조적 적신호 확인 — rubric 높아도 구조 문제 있으면 스킵 금지
            _structural = self._self_critique(
                current_manuscript,
                hud_report,
                encyclopedia,
                genre_name,
                ep_num,
                motivations,
                promises,
                blueprint,
                directive,
                expression_freq,
            )
            _medium_plus = [
                i
                for i in _structural.get("issues", [])
                if isinstance(i, dict) and i.get("severity") in ("medium", "high")
            ]
            if not _medium_plus:
                return current_manuscript
            logging.info(
                "[ChiefWriter] Rubric %.1f ≥ 3.5이나 구조적 이슈 %d건 — Self-Critique 진행",
                rubric_score,
                len(_medium_plus),
            )

        # ── [TF-G] 게이트 검사: ending_hook + 분량 (severity="low" 탈출 방지) ──
        _gate_issues: list[str] = []
        if blueprint:
            _eh_issues = self._check_ending_hook_presence(current_manuscript, blueprint)
            if _eh_issues:
                _gate_issues.extend(_eh_issues)
        if len(current_manuscript) < 5000:
            _gate_issues.append(f"분량 부족 ({len(current_manuscript)}자 < 5,000자)")

        # [TF-20-01] meta_wall 단독 1건도 severity="low" 탈출 방지
        _meta_issues = self._check_system_term_exposure(current_manuscript, genre_name)
        if _meta_issues:
            _gate_issues.extend(_meta_issues)

        if _gate_issues:
            logging.info("[TF-G] 게이트 검사 실패 %d건: %s", len(_gate_issues), _gate_issues)
            try:
                current_manuscript = self._fix_manuscript_issues(
                    current_manuscript,
                    {
                        "has_issues": True,
                        "issues": [{"severity": "high", "issue": g} for g in _gate_issues],
                        "severity": "high",
                    },
                    hud_report,
                )
                total_issues_fixed += len(_gate_issues)
            except Exception as _ge:
                logging.warning("[TF-G] 게이트 수정 실패 (비치명): %s", _ge)

        for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
            critique_result = self._self_critique(
                current_manuscript,
                hud_report,
                encyclopedia,
                genre_name,
                ep_num,
                motivations,
                promises,
                blueprint,
                directive,
                expression_freq,
            )

            if not critique_result["has_issues"]:
                if round_num > 1:
                    logging.info(f"[ChiefWriter] Self-Critique R{round_num}: 완료 ({total_issues_fixed}건 수정)")
                    self.host._operator_log(
                        f"✅ [Writer] Self-Critique 완료 ({total_issues_fixed}건 수정)",
                        meta={"issues_fixed": total_issues_fixed, "round_num": round_num},
                    )
                break

            if critique_result["severity"] == "low":
                break

            # [V60.82] 라운드 중간 Rubric 체크 - 3.5 이상이면 조기 종료
            if round_num > 1:
                mid_score = self._evaluate_with_rubric(current_manuscript, genre_name)
                current_content_length = len(self._extract_content_text(current_manuscript))
                if mid_score >= 3.5 and current_content_length >= int(ManuscriptLimits.MIN_LENGTH):
                    break

            logging.info(
                f"[ChiefWriter] Self-Critique R{round_num}/{MAX_CRITIQUE_ROUNDS}: {len(critique_result['issues'])}건..."
            )
            self.host._operator_log(
                f"🔧 [Writer] Self-Critique R{round_num}: {len(critique_result['issues'])}건 수정 중...",
                meta={"round_num": round_num, "issue_count": len(critique_result["issues"])},
            )
            current_manuscript = self._fix_manuscript_issues(current_manuscript, critique_result, hud_report)
            total_issues_fixed += len(critique_result["issues"])

        return current_manuscript

    def _self_critique(
        self,
        manuscript: str,
        hud_report: str,
        encyclopedia: dict,
        genre_name: str,
        ep_num: int = None,
        motivations: list = None,
        promises: list = None,
        blueprint=None,
        directive=None,
        expression_freq: dict | None = None,
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

        # 5. [B-4] 주인공 동기/약속 방치 체크
        if motivations or promises:
            motivation_issues = self._check_motivation_consistency(content, motivations or [], promises or [])
            issues.extend(motivation_issues)

        # 6. [TF-54e] WritingDirective 준수 체크
        issues.extend(self._check_writing_directive(content, directive))

        # 7. [TF-54e] 표현 신선도 체크
        issues.extend(self._check_expression_freshness(content, expression_freq or {}))

        # 8. [AI-TELL] 상투적 반응구/문장 스타터 반복 체크
        issues.extend(self._check_ai_tell_patterns(content))

        # 9. [합격률] ending_hook 포함 여부 체크
        issues.extend(self._check_ending_hook_presence(content, blueprint))

        # 10. [NS-1] Detect arithmetic inconsistencies in manuscript claims.
        issues.extend(self._check_arithmetic_consistency(content))

        # 11. [메타 월] 집필 시스템 내부 용어 노출 체크
        issues.extend(self._check_system_term_exposure(content, genre_name))

        # 12. [QI-1-A5] 엔딩 참신성 체크 — 직전 화 엔딩과 유사한 엔딩 반복 방지
        issues.extend(self._check_ending_novelty(content, directive))

        # 13. [QI-QM-1] self-critique 내부 시간 논리 보강
        issues.extend(self._check_temporal_logic(content))

        # 14. [QI-QM-1] self-critique 내부 문단 구조 보강
        issues.extend(self._check_paragraph_structure(content))

        # 15. [QI-QM-1] Blueprint 대비 톤 일관성 보강
        issues.extend(self._check_tonal_consistency(content, blueprint, directive))

        # 16. [QI-POV] POV 일관성 자가 점검
        issues.extend(self._check_pov_consistency_critique(content))

        # 17. [QI-QM-5] 씬 전환 마커 점검
        issues.extend(self._check_scene_transition_markers(content))

        # 11. [TF-H] 분량 재검사 — self-critique 루프에서 분량 부족 재감지
        _min_len = int(ManuscriptLimits.MIN_LENGTH)
        _target_len = int(ManuscriptLimits.TARGET_LENGTH)
        if len(content) < _target_len:
            _sev = "high" if len(content) < _min_len else "medium"
            issues.append(
                {
                    "type": "manuscript_length",
                    "description": (
                        f"원고 길이 {len(content)}자 < 목표 {_target_len}자. "
                        "장면 묘사, 인물 심리, 대화를 확장하세요."
                    ),
                    "severity": _sev,
                }
            )

        # [Sweep46] 심각도 판단
        # [TF-H] high 이슈 1건이라도 있으면 전체 severity를 최소 medium으로 보정
        severity = "low"
        _has_high_issue = any(isinstance(i, dict) and i.get("severity") == "high" for i in issues)
        if len(issues) >= 5:
            severity = "high"
        elif len(issues) >= 3 or _has_high_issue:
            severity = "medium"
        # 1~2건: severity="low", has_issues=True → apply_self_critique에서 break

        has_issues = len(issues) > 0

        return {"has_issues": has_issues, "issues": issues, "severity": severity}

    def _resolve_expected_pov(self) -> tuple[str, str]:
        """MasterBible 기준 예상 POV/주인공명을 조회한다."""
        try:
            _ctx = getattr(self.host, "context", None)
            _project = getattr(_ctx, "current_project", None) if _ctx else None
            _mb = getattr(_project, "master_bible", None) or getattr(_ctx, "master_bible", None) or {}
            _mb_root = _mb.get("MasterBible", _mb) if isinstance(_mb, dict) else {}
            _protag = _mb_root.get("protagonist_config", {}) if isinstance(_mb_root, dict) else {}
            _pov = str(_protag.get("pov", "") or "").strip()
            _name = str(_protag.get("name", "") or "").strip()
            return _pov, _name
        except Exception:
            return "", ""

    def _check_pov_consistency_critique(self, content: str) -> list[dict]:
        """PreLLM POV 규칙을 Self-Critique에도 재사용한다."""
        if not content:
            return []

        _pov, _protagonist_name = self._resolve_expected_pov()
        if not _pov:
            return []

        try:
            from modules.validation.pre_llm_validator import PreLLMValidator

            _validator = PreLLMValidator(pov=_pov, protagonist_name=_protagonist_name)
            _result = _validator._check_pov_consistency(content)
        except Exception as _pov_err:
            logging.debug("[ChiefWriter] POV self-critique 실패 (비치명): %s", _pov_err)
            return []

        if not isinstance(_result, dict) or not _result.get("has_issue"):
            return []

        return [
            {
                "type": "pov_consistency",
                "description": str(_result.get("description", "시점 일관성 의심") or "시점 일관성 의심"),
                "severity": "medium",
            }
        ]

    def _check_system_term_exposure(self, content: str, genre: str = "") -> list:
        """[메타 월] 집필 시스템 내부 용어 원고 노출 감지.

        [TF-4T-B] 의료/미용 장르에서 'Stage N 암', 'treatment' 는 정상 표현이므로 제외.
        """
        import re as _re

        if not content:
            return []

        _MEDICAL_GENRES = {"의료", "병원", "의학", "medical", "hospital"}
        _genre_lower = genre.lower()
        is_medical = any(g in _genre_lower for g in _MEDICAL_GENRES)

        if is_medical:
            # Stage\s+\d+(암 스테이징)과 treatment(시술명) 제외
            _SYSTEM_TERM_RE = _re.compile(
                r"\b(Block\s+\d+|Blueprint)\b",
                _re.IGNORECASE,
            )
        else:
            _SYSTEM_TERM_RE = _re.compile(
                r"\b(Block\s+\d+|Stage\s+\d+|Blueprint|treatment)\b",
                _re.IGNORECASE,
            )
        # [C-1] 'Arc 종료/시작' 같은 메타 표현 감지 (대문자 Arc만)
        _ARC_META_RE = _re.compile(r"\bArc(?:\s+\d+)?\b")

        m = _SYSTEM_TERM_RE.search(content) or _ARC_META_RE.search(content)
        if m:
            return [
                {
                    "type": "meta_wall",
                    "description": (
                        f"시스템 용어 '{m.group()}' 원고 노출 — "
                        "세계관 내 표현으로 대체하세요 "
                        "(예: '처음 원유 투자할 때', '지난번 거래 초반에')"
                    ),
                    "severity": "high",
                }
            ]
        return []

    def _check_arithmetic_consistency(self, content: str) -> list:
        """[NS-1] Check obvious arithmetic expressions for consistency."""
        issues = []
        if not content:
            return issues

        tolerance = 0.05  # 5%

        def to_num(token: str) -> float | None:
            if not isinstance(token, str):
                return None
            cleaned = re.sub(r"\([^)]*\)", "", token).strip()
            cleaned = cleaned.replace(",", "").replace(" ", "")
            cleaned = re.sub(r"(원|달러|명|개)$", "", cleaned)
            if not cleaned:
                return None

            sign = 1.0
            if cleaned[0] in "+-":
                if cleaned[0] == "-":
                    sign = -1.0
                cleaned = cleaned[1:]

            multipliers = {"조": 1e12, "억": 1e8, "만": 1e4}
            for unit, mult in multipliers.items():
                if unit in cleaned:
                    num_part = cleaned.split(unit, 1)[0]
                    try:
                        return sign * float(num_part) * mult
                    except ValueError:
                        return None

            try:
                return sign * float(cleaned)
            except ValueError:
                return None

        def within_tolerance(stated: float, actual: float) -> bool:
            if actual == 0:
                return stated == 0
            return abs(stated - actual) / abs(actual) <= tolerance

        def compact(value: float) -> str:
            if abs(value) >= 1e8:
                return f"{value / 1e8:.1f}" + "억"
            return f"{value:.4g}"

        num_with_unit = r"[\d,]+(?:\.[\d]+)?(?:조|억|만)?"
        mul_op = r"(?:[xX×*]|곱)"
        eq_op = r"(?:=|는|은|:)"
        bae = "배"

        mult_pattern = re.compile(
            rf"(?P<a>{num_with_unit})\s*{mul_op}\s*"
            rf"(?P<b>[\d,]+(?:\.[\d]+)?)\s*{bae}?\s*{eq_op}\s*"
            rf"(?P<c>{num_with_unit})"
        )
        pct_pattern = re.compile(
            rf"(?P<a>{num_with_unit})\s*{mul_op}\s*"
            rf"(?P<pct>[\d,]+(?:\.[\d]+)?)%\s*{eq_op}\s*"
            rf"(?P<c>{num_with_unit})"
        )
        add_sub_pattern = re.compile(
            rf"(?P<a>{num_with_unit})\s*(?P<op>[+-])\s*"
            rf"(?P<b>{num_with_unit})\s*=\s*"
            rf"(?P<c>{num_with_unit})"
        )

        for match in mult_pattern.finditer(content):
            a = to_num(match.group("a"))
            b = to_num(match.group("b"))
            stated = to_num(match.group("c"))
            if None in (a, b, stated):
                continue
            actual = a * b
            if not within_tolerance(stated, actual):
                expr = match.group(0).strip()
                issues.append(
                    {
                        "type": "arithmetic_error",
                        "description": f"Arithmetic mismatch: {expr} stated={match.group('c')} actual={compact(actual)}",
                        "location": "numeric expression",
                        "severity": "high",
                    }
                )

        for match in pct_pattern.finditer(content):
            a = to_num(match.group("a"))
            pct = to_num(match.group("pct"))
            stated = to_num(match.group("c"))
            if None in (a, pct, stated):
                continue
            actual = a * (pct / 100.0)
            if not within_tolerance(stated, actual):
                expr = match.group(0).strip()
                issues.append(
                    {
                        "type": "arithmetic_error",
                        "description": f"Arithmetic mismatch: {expr} stated={match.group('c')} actual={compact(actual)}",
                        "location": "numeric expression",
                        "severity": "high",
                    }
                )

        for match in add_sub_pattern.finditer(content):
            a = to_num(match.group("a"))
            b = to_num(match.group("b"))
            stated = to_num(match.group("c"))
            if None in (a, b, stated):
                continue
            actual = a + b if match.group("op") == "+" else a - b
            if not within_tolerance(stated, actual):
                expr = match.group(0).strip()
                issues.append(
                    {
                        "type": "arithmetic_error",
                        "description": f"Arithmetic mismatch: {expr} stated={match.group('c')} actual={compact(actual)}",
                        "location": "numeric expression",
                        "severity": "high",
                    }
                )

        return issues

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
            recent_counts = self._count_recent_cliches(ep_num, window=self.CLICHE_WINDOW)

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
                        # [Sweep-Codex] re.escape: NPC 이름에 regex 특수문자 방어
                        esc_name = re.escape(name)
                        context_pattern = f"{esc_name}.*{kw}|{kw}.*{esc_name}"
                        if re.search(context_pattern, content, re.DOTALL):
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

    def _check_motivation_consistency(self, content: str, motivations: list, promises: list) -> list:
        """[B-4] 주인공 동기/약속 방치 감지 — 키워드 레벨 체크."""
        issues = []
        if not content:
            return issues

        # 활성 동기 키워드 체크
        active_mots = [
            m
            for m in (motivations or [])
            if isinstance(m, dict) and m.get("status") not in ("resolved", "완료") and m.get("text")
        ]
        for mot in active_mots[:5]:
            _kws = [w for w in mot["text"].split()[:4] if len(w) >= 2]
            if _kws and not any(kw in content for kw in _kws):
                issues.append(
                    {
                        "type": "motivation_abandoned",
                        "description": f"동기 '{mot['text'][:30]}' 키워드 미등장 (방치 의심)",
                        "severity": "low",
                    }
                )
                break  # 1건만 보고

        # 미이행 약속 당사자 등장 시 약속 미언급
        pending = [
            p
            for p in (promises or [])
            if isinstance(p, dict) and p.get("status") in ("pending", None, "") and p.get("text")
        ]
        for p in pending[:3]:
            involved = [n for n in [p.get("promiser", ""), p.get("promisee", "")] if n and len(n) >= 2]
            if involved and any(n in content for n in involved):
                _pkws = [w for w in p["text"].split()[:3] if len(w) >= 2]
                if _pkws and not any(kw in content for kw in _pkws):
                    issues.append(
                        {
                            "type": "promise_unacknowledged",
                            "description": f"미이행 약속 당사자 등장 중 약속 미언급: '{p['text'][:30]}'",
                            "severity": "low",
                        }
                    )
                    break
        return issues

    def _check_writing_directive(self, manuscript: str, directive) -> list:
        """[TF-54e] WritingDirective 위반 여부 점검."""
        if directive is None:
            return []
        emotion_required = str(getattr(directive, "emotion_required", "") or "").strip()
        if hasattr(directive, "is_empty") and directive.is_empty() and not emotion_required:
            return []

        issues = []
        expression_ban = list(getattr(directive, "expression_ban", []) or [])
        for expr in expression_ban:
            if expr and expr in manuscript:
                issues.append(
                    {
                        "type": "expression_ban_violation",
                        "description": f"금지 표현 '{expr}' 사용됨",
                        "severity": "medium",
                    }
                )

        tail = manuscript[-200:] if len(manuscript) > 200 else manuscript
        ending_style = str(getattr(directive, "ending_style", "") or "")
        if "조용한여운" in ending_style and any(
            kw in tail for kw in ["시작이었다", "서막이 올랐다", "전쟁이 시작", "사냥이 시작"]
        ):
            issues.append(
                {
                    "type": "ending_style_violation",
                    "description": "ending_style '조용한여운' 지시인데 선언문으로 종결",
                    "severity": "medium",
                }
            )

        if emotion_required:
            emotion_keywords = [
                kw for kw in re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", emotion_required) if len(kw) >= 2
            ] or [emotion_required]
            emotion_window = manuscript[-1200:] if len(manuscript) > 1200 else manuscript
            if not any(keyword in emotion_window for keyword in emotion_keywords[:3]):
                issues.append(
                    {
                        "type": "emotion_required_missing",
                        "description": f"emotion_required '{emotion_required}'가 원고 후반 감정선에 반영되지 않음",
                        "severity": "medium",
                    }
                )

        return issues

    def _check_expression_freshness(self, manuscript: str, expression_freq: dict) -> list:
        """[TF-54e] 고빈도 표현의 재등장 여부 점검."""
        if not isinstance(expression_freq, dict) or not expression_freq:
            return []

        issues = []
        for expr, freq in expression_freq.items():
            try:
                _freq = int(freq)
            except (ValueError, TypeError):
                _freq = 0
            if _freq >= 3 and expr and str(expr) in manuscript:
                issues.append(
                    {
                        "type": "expression_freshness_repetition",
                        "description": f"반복 표현 '{str(expr)[:20]}' 이번 화에도 사용 (직전 {_freq}회)",
                        "severity": "low",
                    }
                )
        return issues

    def _check_ai_tell_patterns(self, content: str) -> list[dict]:
        """상투적 AI 반응구와 문장 스타터 반복을 advisory-only로 탐지한다."""
        if not content:
            return []

        issues: list[dict] = []

        phrase_hits = {
            phrase: content.count(phrase)
            for phrase in self.AI_TELL_PHRASES
            if content.count(phrase) >= 2
        }
        if phrase_hits:
            top_hits = sorted(phrase_hits.items(), key=lambda item: (-item[1], item[0]))[:3]
            labels = ", ".join(f"{phrase} x{count}" for phrase, count in top_hits)
            issues.append(
                {
                    "type": "ai_tell_pattern_overuse",
                    "description": f"상투적 반응구/접속구 반복 감지: {labels}",
                    "severity": "low",
                }
            )

        starters: dict[str, int] = {}
        first_tokens: dict[str, int] = {}
        sentences = [chunk.strip(" \"'“”‘’") for chunk in re.split(r"(?<=[.!?…])\s+|\n+", content) if chunk.strip()]
        for sentence in sentences:
            tokens = re.findall(r"[가-힣A-Za-z]{2,}", sentence)
            if not tokens:
                continue
            first_token = tokens[0]
            first_tokens[first_token] = first_tokens.get(first_token, 0) + 1
            if len(tokens) >= 2:
                starter = " ".join(tokens[:2])
                starters[starter] = starters.get(starter, 0) + 1

        repeated_starters = [(starter, count) for starter, count in starters.items() if count >= 3]
        if not repeated_starters:
            repeated_starters = [(token, count) for token, count in first_tokens.items() if count >= 4]
        if repeated_starters:
            top_starters = sorted(repeated_starters, key=lambda item: (-item[1], item[0]))[:3]
            labels = ", ".join(f"{starter} x{count}" for starter, count in top_starters)
            issues.append(
                {
                    "type": "ai_tell_sentence_starter_repetition",
                    "description": f"문장 스타터가 지나치게 단조롭게 반복됨: {labels}",
                    "severity": "low",
                }
            )

        return issues

    def _check_ending_hook_presence(self, manuscript: str, blueprint) -> list:
        """[합격률+QI-1-A2] ending_hook 의미가 원고 말미에 반영되었는지 키워드 매칭으로 확인."""
        if not blueprint or not isinstance(blueprint, dict):
            return []
        ending_hook = str(blueprint.get("ending_hook", "") or "").strip()
        if not ending_hook or len(ending_hook) < 10:
            return []
        # 원고 마지막 500자에서 확인 (ending_hook은 말미에 있어야 함)
        tail = manuscript[-500:] if len(manuscript) > 500 else manuscript
        # [QI-1-A2] 리터럴 매칭 → 키워드 매칭 전환
        keywords = [w for w in re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", ending_hook) if len(w) >= 2]
        top_keywords = keywords[:5]
        if len(top_keywords) < 2:
            return []  # 키워드 부족 → 검사 스킵
        matched = sum(1 for kw in top_keywords if kw in tail)
        if matched < 2:
            return [
                {
                    "type": "missing_ending_hook",
                    "description": (
                        f"ending_hook 키워드({', '.join(top_keywords[:3])}...) 중 "
                        f"{matched}개만 원고 말미에서 발견됨 (최소 2개 필요)"
                    ),
                    "severity": "medium",
                }
            ]
        return []

    def _check_ending_novelty(self, manuscript: str, directive) -> list:
        """[QI-1-A5] 엔딩 참신성 체크 — 직전 화 엔딩 문구와 3-gram 자카드 유사도 비교."""
        if not directive or not manuscript:
            return []
        avoid_phrases = list(getattr(directive, "ending_avoid_phrases", []) or [])
        if not avoid_phrases:
            return []

        tail = manuscript[-50:].strip() if len(manuscript) > 50 else manuscript.strip()
        if len(tail) < 10:
            return []

        # 3-gram 생성
        def _ngrams(text: str, n: int = 3) -> set[str]:
            return {text[i : i + n] for i in range(max(0, len(text) - n + 1))}

        tail_grams = _ngrams(tail)
        if not tail_grams:
            return []

        for phrase in avoid_phrases[-3:]:
            phrase_grams = _ngrams(str(phrase))
            if not phrase_grams:
                continue
            intersection = len(tail_grams & phrase_grams)
            union = len(tail_grams | phrase_grams)
            if union > 0 and intersection / union > 0.6:
                return [
                    {
                        "type": "ending_repetition",
                        "description": (
                            f"엔딩 문구가 직전 화와 유사합니다 (유사도 {intersection / union:.0%}). "
                            "다른 유형의 엔딩(수사의문문·감각묘사·대사 중단·상황 반전)을 시도하세요."
                        ),
                        "severity": "medium",
                    }
                ]
        return []

    def _check_temporal_logic(self, content: str) -> list:
        """같은 단락 내 상충되는 시간 점프가 겹치는지 점검."""
        if not content:
            return []

        immediate_markers = ("곧바로", "즉시", "잠시 후", "곧", "이내")
        long_jump_markers = ("다음 날", "며칠 후", "한참 후", "몇 시간 후", "몇 주 후", "한 달 후", "이틀 뒤")
        for paragraph in [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]:
            has_immediate = any(marker in paragraph for marker in immediate_markers)
            has_long_jump = any(marker in paragraph for marker in long_jump_markers)
            if has_immediate and has_long_jump:
                return [
                    {
                        "type": "temporal_logic_jump",
                        "description": "같은 단락 안에서 즉시 진행과 장시간 점프가 함께 나타남",
                        "severity": "medium",
                    }
                ]
        return []

    def _check_paragraph_structure(self, content: str) -> list:
        """과도하게 긴 벽돌 문단을 탐지한다."""
        if not content:
            return []

        paragraphs = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
        if not paragraphs:
            return []

        for paragraph in paragraphs:
            sentence_count = len([s for s in re.split(r"[.!?\n]|[다요]\s", paragraph) if s.strip()])
            if len(paragraph) >= 1000 and sentence_count >= 12:
                return [
                    {
                        "type": "paragraph_structure_dense",
                        "description": "문단이 지나치게 길어 호흡이 막힘 (줄바꿈/장면 분리 필요)",
                        "severity": "medium",
                    }
                ]
            if len(paragraph) >= 700 and sentence_count >= 8:
                return [
                    {
                        "type": "paragraph_structure_dense",
                        "description": "벽돌 문단 가능성 — 줄바꿈 또는 대사 분리 검토 필요",
                        "severity": "low",
                    }
                ]
            if sentence_count >= 12:
                return [
                    {
                        "type": "paragraph_structure_dense",
                        "description": "단일 문단에 문장이 과도하게 몰려 있어 호흡이 막힘",
                        "severity": "low",
                    }
                ]
        return []

    def _check_tonal_consistency(self, content: str, blueprint, directive) -> list:
        """Blueprint 핵심 긴장/감정선과 정반대 톤이 과도한지 점검."""
        if not content:
            return []

        target_texts = []
        if isinstance(blueprint, dict):
            for key in ("core_tension", "emotional_arc", "target_beat", "expected_ending"):
                value = blueprint.get(key)
                if isinstance(value, str) and value.strip():
                    target_texts.append(value)
        intensity_note = str(getattr(directive, "intensity_note", "") or "").strip()
        if intensity_note:
            target_texts.append(intensity_note)
        if not target_texts:
            return []

        target = " ".join(target_texts)
        tension_markers = ("긴장", "위기", "절박", "압박", "불안", "분노", "살벌", "비장")
        soft_markers = ("안도", "잔잔", "따뜻", "다정", "평온", "평화", "포근")
        comic_markers = ("낄낄", "키득", "농담", "장난", "우스꽝", "능청")
        violent_markers = ("피", "살기", "참혹", "절규", "비명", "광기")

        if any(marker in target for marker in tension_markers):
            comic_hits = sum(content.count(marker) for marker in comic_markers)
            if comic_hits >= 2:
                return [
                    {
                        "type": "tonal_inconsistency",
                        "description": "Blueprint 긴장 톤 대비 코미디 톤이 과도하게 섞임",
                        "severity": "medium",
                    }
                ]

        if any(marker in target for marker in soft_markers):
            violent_hits = sum(content.count(marker) for marker in violent_markers)
            if violent_hits >= 3:
                return [
                    {
                        "type": "tonal_inconsistency",
                        "description": "Blueprint 잔잔/안도 톤 대비 과격한 정서가 과다함",
                        "severity": "medium",
                    }
                ]

        return []

    def _check_scene_transition_markers(self, content: str) -> list:
        """장면 전환 시 시간/장소 마커가 부족한지 점검."""
        if not content:
            return []

        scene_blocks = [block.strip() for block in re.split(r"\n{2,}|\n\*\*\*\n", content) if block.strip()]
        if len(scene_blocks) < 3:
            return []

        place_markers = ("에서", "으로", "안으로", "밖으로", "도착", "향했다", "들어섰다", "돌아왔다")
        time_markers = ("다음 날", "그날 밤", "잠시 후", "며칠 후", "아침", "저녁", "새벽", "오후")
        missing_count = 0

        for block in scene_blocks[1:]:
            head = " ".join(re.split(r"[.!?\n]", block)[:2]).strip()
            has_place = any(marker in head for marker in place_markers)
            has_time = any(marker in head for marker in time_markers)
            if not has_place and not has_time:
                missing_count += 1

        if missing_count >= 2:
            return [
                {
                    "type": "scene_transition_marker_missing",
                    "description": "복수 장면 전환에서 시간/장소 마커가 부족함",
                    "severity": "medium",
                }
            ]
        if missing_count == 1:
            return [
                {
                    "type": "scene_transition_marker_missing",
                    "description": "장면 전환부의 시간/장소 마커가 약함",
                    "severity": "low",
                }
            ]
        return []

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

        # [TF-H] 분량 부족 이슈면 확장 전용 프롬프트 사용
        _has_length_issue = any(
            isinstance(i, dict) and i.get("type") == "manuscript_length"
            for i in issues[:3]
        )

        if _has_length_issue:
            _content = ""
            try:
                _parsed = json.loads(manuscript)
                _content = _parsed.get("content", "") if isinstance(_parsed, dict) else manuscript
            except (json.JSONDecodeError, ValueError, TypeError):
                _content = manuscript
            if not isinstance(_content, str):
                _content = str(_content) if _content is not None else ""
            prompt = get_expand_length_prompt(
                current_length=len(_content),
                target_length=int(ManuscriptLimits.TARGET_LENGTH),
                manuscript_escaped=self.host._escape_braces(manuscript),
                hud_report_escaped=self.host._escape_braces(hud_report[:500]),
            )
            _thinking = "low"
        else:
            # [V65] 기존 범용 교정 프롬프트
            prompt = get_fix_issues_prompt(
                fix_instructions_text=chr(10).join(fix_instructions),
                hud_report_escaped=self.host._escape_braces(hud_report[:500]),
                manuscript_escaped=self.host._escape_braces(manuscript),  # [TF-I09] 전문 전달 (8000자 절삭 제거)
            )
            _thinking = "low"
        try:
            fixed = self.host.ask(prompt, temperature=0.5, thinking_level=_thinking)
            fixed = self.sanitize_leakage(fixed)

            # JSON 유효성 검증
            try:
                _fixed_parsed = json.loads(fixed)
                _fixed_content = _fixed_parsed.get("content", "") if isinstance(_fixed_parsed, dict) else ""
                if isinstance(_fixed_content, str):
                    _fc_len = len(_fixed_content)
                    _min = int(ManuscriptLimits.MIN_LENGTH)
                    if _fc_len < _min:
                        logging.warning(
                            "[TF-H] 수정 후 분량 여전히 부족: %d자 < %d자",
                            _fc_len,
                            _min,
                        )
                return fixed
            except (json.JSONDecodeError, ValueError, TypeError):
                logging.info("[ChiefWriter] Fix manuscript JSON parse failed, preserving original")
                return manuscript  # 파싱 실패시 원본 유지
        except Exception as e:
            logging.warning(f" [ChiefWriter] 수정 실패: {e}")
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
            # [TypeSafety] content가 dict/list일 수 있음 → 문자열 변환
            if isinstance(content, list):
                content = "\n".join(str(item) for item in content)
            elif isinstance(content, dict):
                content = content.get("text", "") or json.dumps(content, ensure_ascii=False)
            elif not isinstance(content, str):
                content = str(content) if content else ""
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
        # [Sweep49] 문장 끝 구두점 뒤 공백/줄바꿈으로 분리 (소수점 오분리 방지)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if len(s.strip()) > 5]
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
        # [Sweep45] 한국어 따옴표(\u201c\u201d) + ASCII 따옴표 모두 매칭
        dialogue_matches = re.findall(r'["\u201c].*?["\u201d]|[\'\u2018].*?[\'\u2019]', content)
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

    def _count_recent_cliches(self, ep_num: int, window: int = 10) -> dict:
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

        # [TF-R2-S4-I08] 현재 원고 제외 — 이전 에피소드만 기준선
        return {k: v for k, v in counts.items() if v > 0}
