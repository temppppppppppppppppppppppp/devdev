"""
[V60.80] Manuscript Validator - Python 기반 사전 검증기

Stage 4 "Director 주권주의" 아키텍처의 무료 사전 검증 레이어.
LLM 호출 없이 Python으로 빠르게 경고 포인트를 생성.

중요: REJECT 권한 없음! 경고만 생성하여 Director에게 "집중 검토 포인트"로 전달.
"""

import json
import logging
import re
import time

from modules.core.constants import ManuscriptLimits  # [V64.P4]


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

    # [V64.P4] 분량 기준 — ManuscriptLimits 참조
    LENGTH_WARNING_THRESHOLD = ManuscriptLimits.WARNING_LENGTH
    LENGTH_TARGET = ManuscriptLimits.TARGET_LENGTH

    # [V63.3] 클래스 레벨 regex 상수 (매 호출마다 re.compile 방지)
    _ITEM_LOSS_PATTERNS = [
        re.compile(r"([가-힣]{2,6})[을를]\s*(?:잃어|버렸|떨어뜨|빼앗[기겼]|놓[쳐았]|던져\s*버)"),
        re.compile(r"([가-힣]{2,6})[이가]\s*(?:부서[졌지]|파괴[되됐]|산산조각|깨[졌져]|부러[졌져])"),
    ]
    _ITEM_RECOVERY_PATTERNS = [
        re.compile(r"([가-힣]{2,6})[을를]\s*(?:되찾|주[워웠]|다시\s*집|회수|건져)"),
    ]
    _ITEM_USE_PATTERNS = [
        re.compile(r"([가-힣]{2,6})[을를]\s*(?:뽑[아았]|들[어었]|휘[둘두]|잡[아았]|꺼[내냈])"),
        re.compile(r"([가-힣]{2,6})[으로]?\s*(?:내려[쳤치]|찔[렀러]|베[었어]|막[았아])"),
    ]
    _SCENE_KEYWORD_PATTERN = re.compile(r"[가-힣]{2,5}")
    _SCENE_MARKER_PATTERN = re.compile(r"\[(Core|Buffer|Cliffhanger|Scene)\s*\d*\]", re.IGNORECASE)
    _PROPER_NOUN_PATTERN = re.compile(r"'([가-힣]{2,6})'")
    _IMPORTANT_KEYWORD_PATTERN = re.compile(r"\[([가-힣]{2,10})\]")
    _WORD_PATTERN = re.compile(r"[가-힣]{2,}")

    def __init__(self, context=None, genre_type: str = "wuxia", llm_client=None):
        self.context = context
        self._genre_type = genre_type  # [V63.1] 장르 타입 (투자물 전용 체크 분기용)
        self._llm_client = llm_client  # [V63.1.1] LLM 검증용 (Optional)
        self._dead_npcs = set()  # 죽은 NPC 캐시
        # [V67.1] incarnation_type 캐시 — 오탐 방지용
        self._incarnation_type = self._extract_incarnation_type()

    def _extract_incarnation_type(self) -> str:
        """[V67.1] master_bible에서 incarnation_type 추출 (graceful fallback)"""
        try:
            if self.context and hasattr(self.context, "master_bible") and self.context.master_bible:
                _bible_root = self.context.master_bible.get("MasterBible", self.context.master_bible)
                return _bible_root.get("protagonist_config", {}).get("incarnation_type", "")
        except Exception:
            pass
        return ""

    def validate_candidate(
        self,
        manuscript: str,
        blueprint: dict,
        prev_manuscript: str = "",
        hud_report: str = "",
        strategy_name: str = "",
        recent_manuscripts: list[dict] = None,  # [V62.7] 크로스 에피소드 씬 중복 검사용
    ) -> dict:
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

        # 6. [V62.6] 원고 내부 자기모순 체크
        intra_result = self._check_intra_contradictions(manuscript)
        if intra_result["warnings"]:
            warnings.extend(intra_result["warnings"])
            focus_points.extend(intra_result["focus_points"])

        # 7. [V62.7] 크로스 에피소드 씬 중복 검사
        if recent_manuscripts:
            dedup_result = self._check_cross_episode_duplication(manuscript, recent_manuscripts)
            if dedup_result["warnings"]:
                warnings.extend(dedup_result["warnings"])
                focus_points.extend(dedup_result["focus_points"])

        # 8. [V63.1] 메타 참조 / 4벽 파괴 체크
        meta_result = self._check_meta_references(manuscript)

        # 9. [V63.1] 호칭 일관성 체크
        honorific_result = self._check_honorific_consistency(manuscript, prev_manuscript, recent_manuscripts)

        # 10. [V63.1] 금융 숫자 체크 (투자물만)
        financial_warnings = []
        financial_focus = []
        if self._genre_type == "investment":
            financial_result = self._check_financial_numbers(manuscript, recent_manuscripts)
            financial_warnings = financial_result.get("warnings", [])
            financial_focus = financial_result.get("focus_points", [])

        # [V63.1.1] LLM 2차 검증: 체크 #8~#10의 Python 경고 오탐 필터링
        v631_warnings = meta_result.get("warnings", []) + honorific_result.get("warnings", []) + financial_warnings
        v631_focus = meta_result.get("focus_points", []) + honorific_result.get("focus_points", []) + financial_focus

        if v631_warnings and self._llm_client:
            verified = self._llm_verify_warnings(
                warnings=v631_warnings, manuscript_excerpt=manuscript[:3000], check_type="combined"
            )
            warnings.extend(verified)
            # focus_points: 검증 후 경고가 남아있으면 포함
            if verified:
                focus_points.extend(v631_focus)
        else:
            warnings.extend(v631_warnings)
            focus_points.extend(v631_focus)

        return {
            "strategy": strategy_name,
            "warnings": warnings,
            "warning_count": len(warnings),
            "focus_points": focus_points,
            "metrics": metrics,
            "has_critical_warning": len(focus_points) >= 3,  # 집중 검토 필요
        }

    # [B-2] DraftValidator Protocol 적합화
    validate = validate_candidate

    def validate_all_candidates(
        self,
        candidates: list[dict],
        blueprint: dict,
        prev_manuscript: str = "",
        hud_report: str = "",
        recent_manuscripts: list[dict] = None,  # [V62.7]
    ) -> list[dict]:
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

            # 타입 안전성 보장 - manuscript가 문자열이 아닌 경우 변환
            if not isinstance(manuscript, str):
                if isinstance(manuscript, list):
                    manuscript = "\n".join(str(item) for item in manuscript)
                else:
                    manuscript = str(manuscript) if manuscript else ""

            if not manuscript:
                results.append(
                    {
                        "strategy": strategy,
                        "warnings": ["원고 내용 없음"],
                        "warning_count": 1,
                        "focus_points": ["빈 원고"],
                        "metrics": {"length": 0, "scene_coverage": 0},
                        "has_critical_warning": True,
                    }
                )
                continue

            result = self.validate_candidate(
                manuscript=manuscript,
                blueprint=blueprint,
                prev_manuscript=prev_manuscript,
                hud_report=hud_report,
                strategy_name=strategy_name,
                recent_manuscripts=recent_manuscripts,
            )

            results.append(result)

        return results

    def _check_length(self, manuscript: str) -> dict:
        """분량 체크"""
        length = len(manuscript) if manuscript else 0
        warnings = []

        if length < ManuscriptLimits.MIN_LENGTH:  # [V64.P4]
            warnings.append(f"⚠️ 분량 심각 부족: {length}자 (최소 {ManuscriptLimits.MIN_LENGTH}자 필요)")
        elif length < self.LENGTH_WARNING_THRESHOLD:
            warnings.append(f"⚠️ 분량 부족: {length}자 (목표 {self.LENGTH_TARGET}자)")

        return {"length": length, "warnings": warnings}

    def _check_scene_coverage(self, manuscript: str, blueprint: dict) -> dict:
        """씬 반영률 체크"""
        if not blueprint or not isinstance(blueprint, dict):
            return {"coverage": 100.0, "expected": 0, "reflected": 0, "missing_scenes": [], "warnings": []}

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
                    keywords = self._SCENE_KEYWORD_PATTERN.findall(scene_content)
                    # 빈도 높은 키워드 제외 (조사, 일반어)
                    filtered = [
                        k for k in keywords if k not in ["하다", "되다", "있다", "없다", "이다", "그리고", "하지만"]
                    ]
                    scene_keywords[scene_key] = filtered[:5]

        if expected_scenes == 0:
            # scene_breakdown이 없으면 integrated_scenario에서 추정
            scene_markers = self._SCENE_MARKER_PATTERN.findall(integrated_scenario)
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
            "warnings": warnings,
        }

    def _check_basic_continuity(self, manuscript: str, prev_manuscript: str, hud_report: str) -> dict:
        """연속성 기초 체크"""
        warnings = []
        focus_points = []
        issue_count = 0

        if not manuscript:
            return {"warnings": [], "focus_points": [], "issue_count": 0}

        # 1. 죽은 NPC 체크 (이전 원고에서 "죽었다", "사망", "숨을 거두" 등 탐지)
        if prev_manuscript:
            death_patterns = [
                r"([가-힣]{2,4})[이가은는]\s*(?:죽었다|사망했다|숨을\s*거두|최후를\s*맞|절명)",
                r"([가-힣]{2,4})[의]\s*(?:시신|주검|유해)",
            ]
            for pattern in death_patterns:
                matches = re.findall(pattern, prev_manuscript)
                self._dead_npcs.update(matches)

            # 죽은 NPC가 현재 원고에서 말하거나 행동하면 경고
            for npc in self._dead_npcs:
                if len(npc) >= 2:
                    npc_esc = re.escape(npc)
                    # 대화나 행동 패턴
                    alive_patterns = [
                        f"{npc_esc}[이가은는]\\s*말했다",
                        f"{npc_esc}[이가은는]\\s*웃",
                        f'"{npc_esc}"[이가은는]',
                        f"{npc_esc}[이가은는]\\s*(?:검을|칼을|창을)",
                    ]
                    for pattern in alive_patterns:
                        if re.search(pattern, manuscript):
                            warnings.append(f"⚠️ 죽은 NPC '{npc}' 활동 의심")
                            focus_points.append(f"연속성: 죽은 NPC '{npc}' 언급")
                            issue_count += 1
                            break

        # 2. HUD 상태 불일치 체크
        if hud_report:
            # [V67.1] 회귀자 맥락 접미사
            _regressor_ctx = " [회귀자 — 전생 경험으로 가능할 수 있음]" if self._incarnation_type == "회귀자" else ""

            # 부상 상태 체크
            if "중상" in hud_report or "내상" in hud_report:
                # 중상인데 전력 질주/격렬한 전투 묘사
                intense_patterns = [
                    r"전력으로\s*(?:달렸다|질주|뛰어)",
                    r"온\s*힘을\s*다해",
                    r"맹렬하게\s*(?:공격|싸)",
                ]
                for pattern in intense_patterns:
                    if re.search(pattern, manuscript):
                        warnings.append(f"⚠️ 중상 상태에서 격렬한 활동 묘사{_regressor_ctx}")
                        focus_points.append("연속성: 부상 상태 불일치 의심")
                        issue_count += 1
                        break

            # 내공 고갈 상태 체크
            if "내공" in hud_report and ("0%" in hud_report or "고갈" in hud_report):
                qi_patterns = [
                    r"내공을\s*(?:끌어|운용|발출)",
                    r"진기를\s*(?:끌어|운용)",
                    r"기운을\s*(?:모아|집중)",
                ]
                for pattern in qi_patterns:
                    if re.search(pattern, manuscript):
                        warnings.append(f"⚠️ 내공 고갈 상태에서 내공 사용 묘사{_regressor_ctx}")
                        focus_points.append("연속성: 내공 상태 불일치 의심")
                        issue_count += 1
                        break

        return {"warnings": warnings, "focus_points": focus_points, "issue_count": issue_count}

    def _check_blueprint_keywords(self, manuscript: str, blueprint: dict) -> dict:
        """Blueprint 핵심 키워드 체크"""
        if not blueprint or not isinstance(blueprint, dict):
            return {"warnings": [], "missing_keywords": []}

        warnings = []
        missing_keywords = []

        # 통합 시나리오에서 핵심 키워드 추출
        integrated = blueprint.get("integrated_scenario", "")
        if integrated:
            # 고유명사 추출 (작은따옴표로 감싸진 단어)
            proper_nouns = self._PROPER_NOUN_PATTERN.findall(integrated)
            # 중요 키워드 (대괄호 안)
            important = self._IMPORTANT_KEYWORD_PATTERN.findall(integrated)

            check_keywords = list(set(proper_nouns + important))[:10]

            for keyword in check_keywords:
                if len(keyword) >= 2 and keyword not in manuscript:
                    missing_keywords.append(keyword)

        if missing_keywords:
            warnings.append(f"⚠️ Blueprint 핵심 키워드 미반영 의심: {', '.join(missing_keywords[:5])}")

        return {"warnings": warnings, "missing_keywords": missing_keywords}

    def _check_ending_quality(self, manuscript: str) -> dict:
        """후반부/엔딩 품질 체크"""
        if not manuscript or len(manuscript) < 1000:
            return {"warnings": []}

        warnings = []

        # 마지막 500자 추출
        ending = manuscript[-500:]

        # 1. 급격한 마무리 패턴 체크
        abrupt_patterns = [
            r"이렇게.*끝났다",
            r"모든.*해결되었다",
            r"아무.*일.*없었다",
            r"평화롭게.*마무리",
        ]
        for pattern in abrupt_patterns:
            if re.search(pattern, ending):
                warnings.append("⚠️ 급격한 마무리 의심 (클리프행어 부재)")
                break

        # 2. 후반부 밀도 체크 (마지막 20%가 너무 짧은 문장들로만 구성)
        last_portion = manuscript[int(len(manuscript) * 0.8) :]
        sentences = re.split(r"[.!?]\s*", last_portion)
        short_sentences = [s for s in sentences if len(s.strip()) < 15 and len(s.strip()) > 0]

        if len(short_sentences) > len(sentences) * 0.7:
            warnings.append("⚠️ 후반부 문장 밀도 급락 의심")

        return {"warnings": warnings}

    # ── [V62.6] 원고 내부 자기모순 검사 ──────────────────────────────

    def _check_intra_contradictions(self, manuscript: str) -> dict:
        """
        [V62.6] 원고 내부 자기모순 검사

        같은 원고 안에서 앞뒤가 맞지 않는 모순을 탐지:
        - 잃어버린/파괴된 아이템을 다시 사용
        - 쓰러진/사망한 NPC가 갑자기 활동
        - 부상당한 부위를 치료 없이 멀쩡히 사용

        REJECT 권한 없음 - 경고만 생성하여 Director에게 전달

        [V67.1] 회귀자 incarnation_type 인식: 모순 경고에 전생 지식 맥락 추가
        """
        if not manuscript or len(manuscript) < 500:
            return {"warnings": [], "focus_points": []}

        warnings = []
        flagged = set()  # 중복 경고 방지
        # [V67.1] 회귀자 맥락 접미사
        _regressor_suffix = (
            " [회귀자 설정 — 전생 지식으로 설명 가능할 수 있음]" if self._incarnation_type == "회귀자" else ""
        )

        # --- 1. 아이템 상태 모순 --- [V63.3] 클래스 레벨 상수 참조
        item_loss_patterns = self._ITEM_LOSS_PATTERNS
        item_recovery_patterns = self._ITEM_RECOVERY_PATTERNS
        item_use_patterns = self._ITEM_USE_PATTERNS

        lost_items = {}  # item_name -> position
        for pattern in item_loss_patterns:
            for m in pattern.finditer(manuscript):
                name = m.group(1)
                if len(name) >= 2:
                    lost_items[name] = m.start()

        recovered_items = {}
        for pattern in item_recovery_patterns:
            for m in pattern.finditer(manuscript):
                recovered_items[m.group(1)] = m.start()

        for pattern in item_use_patterns:
            for m in pattern.finditer(manuscript):
                name = m.group(1)
                if name in lost_items and name not in flagged:
                    loss_pos = lost_items[name]
                    use_pos = m.start()
                    if use_pos > loss_pos:
                        rec_pos = recovered_items.get(name, -1)
                        if not (loss_pos < rec_pos < use_pos):
                            warnings.append(f"⚠️ 내부 모순: '{name}'을(를) 잃었으나 이후 다시 사용{_regressor_suffix}")
                            flagged.add(name)

        # --- 2. NPC 상태 모순 ---
        npc_down_patterns = [
            re.compile(
                r"([가-힣]{2,4})[이가은는]\s*"
                r"(?:쓰러[졌져]|의식을\s*잃|기절[했해]|죽[었어]|숨을\s*거[두둔]|절명|사망)"
            ),
        ]
        npc_recovery_patterns = [
            re.compile(
                r"([가-힣]{2,4})[이가은는]\s*"
                r"(?:깨어[났나]|의식을\s*되찾|일어[났나서섰]|눈을\s*[떴뜨])"
            ),
        ]
        npc_active_patterns = [
            re.compile(
                r"([가-힣]{2,4})[이가은는]\s*"
                r"(?:말했|소리[쳤치]|외[쳤치]|웃[었어으]|공격[했해]|달[려렸]|검을\s*들|칼을\s*들)"
            ),
        ]

        downed_npcs = {}
        for pattern in npc_down_patterns:
            for m in pattern.finditer(manuscript):
                name = m.group(1)
                if len(name) >= 2:
                    downed_npcs[name] = m.start()

        recovered_npcs = {}
        for pattern in npc_recovery_patterns:
            for m in pattern.finditer(manuscript):
                recovered_npcs[m.group(1)] = m.start()

        for pattern in npc_active_patterns:
            for m in pattern.finditer(manuscript):
                name = m.group(1)
                if name in downed_npcs and name not in flagged:
                    down_pos = downed_npcs[name]
                    active_pos = m.start()
                    if active_pos > down_pos:
                        rec_pos = recovered_npcs.get(name, -1)
                        if not (down_pos < rec_pos < active_pos):
                            warnings.append(f"⚠️ 내부 모순: '{name}'이(가) 쓰러졌으나 이후 활동{_regressor_suffix}")
                            flagged.add(name)

        # --- 3. 부상/신체 상태 모순 ---
        injury_pattern = re.compile(
            r"(왼팔|오른팔|왼손|오른손|왼쪽\s*다리|오른쪽\s*다리|왼다리|오른다리)"
            r"[이가을를에]?\s*"
            r"(?:부러[졌져]|골절|절단|찢[어겼]|관통[당되]|으스러[졌져])"
        )
        heal_pattern = re.compile(
            r"(?:치료|치유|회복|약을\s*(?:먹|바[르랐]|복용)|"
            r"상처[가이]?\s*(?:나았|아물|회복)|붕대|지혈)"
        )

        injured_parts = {}
        for m in injury_pattern.finditer(manuscript):
            part = m.group(1).replace(" ", "")
            injured_parts[part] = m.start()

        heal_positions = [m.start() for m in heal_pattern.finditer(manuscript)]

        for part, injury_pos in injured_parts.items():
            part_key = f"injury_{part}"
            if part_key in flagged:
                continue

            # 부상 부위별 사용 패턴
            if "팔" in part or "손" in part:
                use_re = re.compile(
                    r"양손[으로]*\s*(?:들|잡|쥐|검을)|양팔[을로]*\s*(?:벌|들)|"
                    + re.escape(part)
                    + r"[으로]*\s*(?:들|잡|쥐|휘둘|내려[쳤치])"
                )
            elif "다리" in part:
                use_re = re.compile(re.escape(part) + r"[으로]*\s*(?:걸[었어]|뛰|달[렸려]|차[았올]|밟)")
            else:
                continue

            for m in use_re.finditer(manuscript):
                if m.start() > injury_pos:
                    healed = any(injury_pos < hp < m.start() for hp in heal_positions)
                    if not healed:
                        warnings.append(f"⚠️ 내부 모순: '{part}' 부상 후 치료 없이 사용{_regressor_suffix}")
                        flagged.add(part_key)
                        break

        focus_points = []
        if warnings:
            focus_points.append(f"내부 모순 의심: {len(warnings)}건")

        return {"warnings": warnings, "focus_points": focus_points}

    # ═══════════════════════════════════════════════════════════════
    # [V63.1.1] Python 경고 LLM 2차 검증
    # ═══════════════════════════════════════════════════════════════

    def _llm_verify_warnings(
        self, warnings: list[str], manuscript_excerpt: str, check_type: str = "general"
    ) -> list[str]:
        """
        [V63.1.1] Python regex 경고를 LLM으로 2차 검증.

        오탐 필터링: regex가 잡은 경고를 LLM이 문맥 읽고 진짜/가짜 분류.
        gemini-2.5-flash 사용 (0.0 temp, JSON 응답).
        실패 시 원본 경고 그대로 반환 (안전한 폴백).

        Args:
            warnings: Python 체크가 생성한 경고 문자열 목록
            manuscript_excerpt: 원고 발췌 (검증 문맥용, 3000자 제한)
            check_type: "meta" | "honorific" | "financial" | "combined"

        Returns:
            LLM이 확인한 경고만 포함된 목록 (오탐 제거)
        """
        if not self._llm_client or not warnings:
            return warnings

        try:
            from google.genai import types as _types

            numbered = "\n".join(f"{i + 1}. {w}" for i, w in enumerate(warnings))
            prompt = (
                f"다음은 소설 원고에서 Python regex로 자동 탐지한 경고 목록입니다.\n"
                f"각 경고가 실제 문제인지, 문맥상 정상(오탐)인지 판단해주세요.\n\n"
                f"판단 기준:\n"
                f"- '작가가' 등이 실제 등장인물 이름이거나 대사 속 표현이면 오탐\n"
                f"- '다음 회' 등이 작중 인물의 대화면 오탐\n"
                f"- 호칭 불일치가 관계 변화(격식→친밀)로 설명 가능하면 오탐\n"
                f"- 금융 수치 변동이 서사적 사건(경제 위기 등)으로 설명되면 오탐\n\n"
                f"[원고 발췌]\n{manuscript_excerpt[:3000]}\n\n"
                f"[Python 경고 목록]\n{numbered}\n\n"
                f'JSON으로 반환: {{"verified": [진짜 문제인 경고 번호], '
                f'"rejected": [오탐인 경고 번호]}}'
            )

            # [V63.3] 중복 딜레이 제거 (직접 API 호출이므로 최소 지연만)
            time.sleep(0.1)
            response = self._llm_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=_types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=512,
                    response_mime_type="application/json",
                ),
            )

            result = json.loads(response.text)
            # [Sweep55] LLM이 list 반환 시 dict 보장
            if isinstance(result, list):
                result = result[0] if result and isinstance(result[0], dict) else {}
            if not isinstance(result, dict):
                result = {}
            verified_indices = result.get("verified", [])

            if isinstance(verified_indices, list):
                # 1-indexed → 0-indexed로 변환하여 해당 경고만 반환
                verified = []
                for idx in verified_indices:
                    if isinstance(idx, int) and 1 <= idx <= len(warnings):
                        verified.append(warnings[idx - 1])

                filtered_count = len(warnings) - len(verified)
                if filtered_count > 0:
                    logging.info(f"🔍 [V63.1.1] 경고 오탐 필터링: {filtered_count}/{len(warnings)}건 제거 (LLM 검증)")

                return verified

        except Exception as e:
            logging.warning(f"⚠️ [V63.1.1] LLM 경고 검증 실패, Python 결과 그대로 사용: {str(e)[:60]}")

        return warnings  # 실패 시 원본 그대로 반환

    def format_warnings_for_director(self, validation_results: list[dict]) -> str:
        """Director에게 전달할 경고 포맷 생성"""
        lines = ["### 📋 Python 사전 검증 결과 (참고용 - REJECT 권한 없음)"]
        lines.append("")

        for i, result in enumerate(validation_results):
            strategy = result.get("strategy", f"후보{i + 1}")
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

    # ═══════════════════════════════════════════════════════════════
    # [V62.7] 크로스 에피소드 씬 중복 검사
    # ═══════════════════════════════════════════════════════════════

    SCENE_DEDUP_NGRAM_SIZE = 5  # 5-gram (연속 5단어)
    SCENE_DEDUP_THRESHOLD = 0.15  # 15% 이상 겹치면 WARNING
    SCENE_DEDUP_MIN_WORDS = 50  # 최소 단어 수

    def _check_cross_episode_duplication(self, manuscript: str, recent_manuscripts: list[dict]) -> dict:
        """
        [V62.7] 크로스 에피소드 씬 중복 검사

        현재 원고의 5-gram을 최근 N화 원고들과 비교.
        15% 이상 겹치면 WARNING 생성.

        Args:
            manuscript: 현재 원고
            recent_manuscripts: [{"ep_num": int, "content": str}, ...]

        Returns:
            {"warnings": [...], "focus_points": [...]}
        """
        if not manuscript or not recent_manuscripts:
            return {"warnings": [], "focus_points": []}

        # 현재 원고 n-gram 추출
        words = self._WORD_PATTERN.findall(manuscript)
        if len(words) < self.SCENE_DEDUP_MIN_WORDS:
            return {"warnings": [], "focus_points": []}

        ngram_size = self.SCENE_DEDUP_NGRAM_SIZE
        current_ngrams = set()
        for i in range(len(words) - ngram_size + 1):
            current_ngrams.add(tuple(words[i : i + ngram_size]))

        if not current_ngrams:
            return {"warnings": [], "focus_points": []}

        warnings = []
        focus_points = []

        for prev in recent_manuscripts:
            ep_num = prev.get("ep_num", "?")
            prev_text = prev.get("content", "")
            if not prev_text or len(prev_text) < 200:
                continue

            prev_words = self._WORD_PATTERN.findall(prev_text)
            if len(prev_words) < self.SCENE_DEDUP_MIN_WORDS:
                continue

            prev_ngrams = set()
            for i in range(len(prev_words) - ngram_size + 1):
                prev_ngrams.add(tuple(prev_words[i : i + ngram_size]))

            if not prev_ngrams:
                continue

            overlap = current_ngrams & prev_ngrams
            overlap_ratio = len(overlap) / len(current_ngrams)

            if overlap_ratio >= self.SCENE_DEDUP_THRESHOLD:
                sample = list(overlap)[:2]
                sample_str = ", ".join(" ".join(ng) for ng in sample)
                warnings.append(
                    f"[V62.7] 제{ep_num}화와 씬 중복: "
                    f"{overlap_ratio:.0%} ({len(overlap)}/{len(current_ngrams)} 5-gram) "
                    f"- 예: '{sample_str[:50]}'"
                )
                focus_points.append(f"씬 중복: 제{ep_num}화와 {overlap_ratio:.0%} 겹침")

        return {"warnings": warnings, "focus_points": focus_points}

    # ═══════════════════════════════════════════════════════════════
    # [V63.1] 메타 참조 / 4벽 파괴 검사
    # ═══════════════════════════════════════════════════════════════

    META_PATTERNS = [
        re.compile(r"EP\s*\d+", re.IGNORECASE),  # "EP 6", "EP12"
        re.compile(r"에피소드\s*\d+"),  # "에피소드 12"
        re.compile(r"제\s*\d+\s*화에서"),  # "제6화에서" (나레이션 내)
        re.compile(r"(?:작가|저자|독자|필자)[가이은는]"),  # "작가가", "독자는"
        re.compile(r"(?:다음\s*회|이전\s*회|지난\s*화)"),  # "다음 회", "이전 회"
        re.compile(r"(?:복선|떡밥)[을를이가]"),  # 메타 서사 용어
    ]

    def _check_meta_references(self, manuscript: str) -> dict:
        """
        [V63.1] 메타 참조 / 4벽 파괴 탐지

        "EP 6에서", "에피소드 12", "작가가", "다음 회" 등
        소설 텍스트 내에 메타 나레이션이 섞여 들어간 것을 탐지.
        """
        if not manuscript or len(manuscript) < 100:
            return {"warnings": [], "focus_points": []}

        warnings = []
        focus_points = []

        for pattern in self.META_PATTERNS:
            matches = list(pattern.finditer(manuscript))
            for m in matches:
                match_text = m.group(0)
                pos = m.start()
                # 대사 내 사용은 제외: 앞뒤 50자 내에 " 짝이 있으면 대사로 간주
                window_start = max(0, pos - 50)
                window_end = min(len(manuscript), pos + len(match_text) + 50)
                window = manuscript[window_start:window_end]
                quote_count = window.count('"')
                if quote_count >= 2:
                    continue  # 대사 내 사용은 OK

                warnings.append(f"[V63.1] 메타 참조 의심: '{match_text}' (4벽 파괴/에피소드 번호 노출)")

        if warnings:
            focus_points.append(f"메타 참조: {len(warnings)}건 탐지")

        return {"warnings": warnings, "focus_points": focus_points}

    # ═══════════════════════════════════════════════════════════════
    # [V63.1] 호칭 일관성 검사
    # ═══════════════════════════════════════════════════════════════

    HONORIFIC_PATTERN = re.compile(
        r'"[^"]*?'  # 대사 시작
        r"([가-힣]{1,4}"
        r"(?:님|씨|아|야|이사님|부사장님|전무님|사장님|회장님|형님|형|누나|언니|오빠))"
        r"[.!?,\s]"  # 호칭 뒤 구분자
    )
    # 서술부: ~라고 불렀다 / ~이라 칭했다
    HONORIFIC_NARRATION_PATTERN = re.compile(r"([가-힣]{2,6})[이라]고?\s*(?:불렀|칭했|호칭)")

    def _check_honorific_consistency(
        self,
        manuscript: str,
        prev_manuscript: str = "",
        recent_manuscripts: list[dict] = None,
    ) -> dict:
        """
        [V63.1] 동일 캐릭터 호칭 불일치 탐지

        같은 캐릭터에 대해 다른 호칭이 사용되면 WARNING.
        3개 이상 불일치 시 focus_point 승격.
        """
        if not manuscript or len(manuscript) < 200:
            return {"warnings": [], "focus_points": []}

        warnings = []
        focus_points = []

        # 현재 원고 + 최근 원고들에서 호칭 맵 구축
        all_texts = [("현재", manuscript)]
        if prev_manuscript:
            all_texts.append(("직전", prev_manuscript))
        if recent_manuscripts:
            for rm in recent_manuscripts[:3]:  # 최근 3화만
                content = rm.get("content", "")
                ep = rm.get("ep_num", "?")
                if content:
                    all_texts.append((f"제{ep}화", content))

        # 전체 호칭 맵: {base_name: set(honorific_suffixed)}
        global_map: dict[str, set] = {}

        for label, text in all_texts:
            # 대사 내 호칭 추출
            for m in self.HONORIFIC_PATTERN.finditer(text):
                honorific = m.group(1)
                # base_name 추출: 호칭 접미사 제거
                base = re.sub(
                    r"(님|씨|아|야|이사님|부사장님|전무님|사장님|회장님|형님|형|누나|언니|오빠)$", "", honorific
                )
                if base and len(base) >= 1:
                    global_map.setdefault(base, set()).add(honorific)
            # 서술부 호칭
            for m in self.HONORIFIC_NARRATION_PATTERN.finditer(text):
                honorific = m.group(1)
                base = re.sub(
                    r"(님|씨|아|야|이사님|부사장님|전무님|사장님|회장님|형님|형|누나|언니|오빠)$", "", honorific
                )
                if base and len(base) >= 1:
                    global_map.setdefault(base, set()).add(honorific)

        # 불일치 탐지
        inconsistency_count = 0
        for base, honorifics in global_map.items():
            if len(honorifics) >= 2:
                samples = ", ".join(sorted(honorifics)[:4])
                warnings.append(f"[V63.1] 호칭 불일치: '{base}' → {samples}")
                inconsistency_count += 1

        if inconsistency_count >= 3:
            focus_points.append(f"호칭 불일치: {inconsistency_count}건")

        return {"warnings": warnings, "focus_points": focus_points}

    # ═══════════════════════════════════════════════════════════════
    # [V63.1] 금융 숫자 체크 (투자물 전용)
    # ═══════════════════════════════════════════════════════════════

    # 환율 추출 패턴
    _RATE_PATTERNS = [
        re.compile(r"환율[이가은는]?\s*([\d,]+)\s*원"),
        re.compile(r"([\d,]+)\s*원[을를이가]?\s*(?:돌파|붕괴|돌파하|선)"),
        re.compile(r"1\s*달러[에가]\s*([\d,]+)\s*원"),
    ]
    # 산술 패턴: X억 달러 = Y조/억 원
    _ARITHMETIC_PATTERNS = [
        re.compile(
            r"([\d,.]+)\s*억?\s*달러.*?"
            r"(?:약|=|환산|현재\s*환율로)\s*"
            r"([\d,.]+)\s*(조|억)\s*(?:원|원에)"
        ),
    ]
    # 주요 수치 패턴
    _LEVERAGE_PATTERN = re.compile(r"레버리지[를을]?\s*(\d+)\s*배")
    _ASSET_PATTERN = re.compile(r"총\s*(?:평가\s*)?자산[:]?\s*([\d,]+)\s*(조|억)")
    _YIELD_PATTERN = re.compile(r"수익률\s*([\d,.]+)\s*%")

    @staticmethod
    def _parse_number(s: str) -> float:
        """쉼표 제거 후 float 변환"""
        try:
            return float(s.replace(",", ""))
        except (ValueError, AttributeError):
            return 0.0

    def _extract_exchange_rates(self, text: str) -> list[float]:
        """텍스트에서 환율 수치 추출"""
        rates = []
        for pat in self._RATE_PATTERNS:
            for m in pat.finditer(text):
                val = self._parse_number(m.group(1))
                if 500 < val < 50000:  # 합리적 범위
                    rates.append(val)
        return rates

    def _check_financial_numbers(
        self,
        manuscript: str,
        recent_manuscripts: list[dict] = None,
    ) -> dict:
        """
        [V63.1] 투자물 전용 금융 숫자 체크

        Phase 1: 산술 교차 검증 (달러 × 환율 ≈ 원화)
        Phase 2: Cross-Episode 환율/레버리지 수치 비교
        """
        if not manuscript or len(manuscript) < 200:
            return {"warnings": [], "focus_points": []}

        warnings = []
        focus_points = []

        # ── Phase 1: 산술 교차 검증 ──
        for pat in self._ARITHMETIC_PATTERNS:
            for m in pat.finditer(manuscript):
                dollar_raw = self._parse_number(m.group(1))
                won_raw = self._parse_number(m.group(2))
                unit = m.group(3)

                if dollar_raw <= 0 or won_raw <= 0:
                    continue

                # 단위 정규화 (억 단위 기준)
                won_in_billion = won_raw * 10000 if unit == "조" else won_raw

                # 현재 원고에서 환율 추출
                rates = self._extract_exchange_rates(manuscript)
                if rates:
                    avg_rate = sum(rates) / len(rates)
                    # dollar_raw 억달러 × avg_rate 원/달러 = 억원
                    expected_won_billion = dollar_raw * avg_rate
                    ratio = won_in_billion / expected_won_billion if expected_won_billion > 0 else 0

                    if ratio < 0.5 or ratio > 2.0:  # ±100% 허용 (소설 특성상 넓게)
                        warnings.append(
                            f"[V63.1] 금액 산술 의심: {dollar_raw}억$ × 환율 {avg_rate:.0f}원 "
                            f"≠ {won_raw}{unit}원 (비율 {ratio:.2f})"
                        )

        # ── Phase 2: Cross-Episode 수치 비교 ──
        if recent_manuscripts:
            curr_rates = self._extract_exchange_rates(manuscript)
            curr_lev_matches = self._LEVERAGE_PATTERN.findall(manuscript)
            curr_leverages = [int(x) for x in curr_lev_matches]

            for prev in recent_manuscripts:
                ep_num = prev.get("ep_num", "?")
                prev_text = prev.get("content", "")
                if not prev_text:
                    continue

                # 환율 비교: 급변 탐지 (30% + 300원 이상)
                prev_rates = self._extract_exchange_rates(prev_text)
                if curr_rates and prev_rates:
                    curr_max = max(curr_rates)
                    prev_max = max(prev_rates)
                    diff_ratio = abs(curr_max - prev_max) / prev_max if prev_max > 0 else 0
                    if diff_ratio > 0.3 and abs(curr_max - prev_max) > 300:
                        warnings.append(
                            f"[V63.1] 환율 급변 의심: 제{ep_num}화 {prev_max:.0f}원 → "
                            f"현재 {curr_max:.0f}원 (변동 {diff_ratio:.0%})"
                        )

                # 레버리지 비교
                prev_lev_matches = self._LEVERAGE_PATTERN.findall(prev_text)
                prev_leverages = [int(x) for x in prev_lev_matches]
                if curr_leverages and prev_leverages:
                    if max(curr_leverages) != max(prev_leverages):
                        warnings.append(
                            f"[V63.1] 레버리지 불일치: 제{ep_num}화 {max(prev_leverages)}배 "
                            f"→ 현재 {max(curr_leverages)}배"
                        )

        if len(warnings) >= 2:
            focus_points.append(f"금융 수치 이상: {len(warnings)}건")

        return {"warnings": warnings, "focus_points": focus_points}
