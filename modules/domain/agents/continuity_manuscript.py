"""
[V64.P3] ContinuityManuscriptValidator — 원고 수준 연속성 검증 전담 모듈

ContinuityInspector God Object 분해의 세 번째 모듈.
Stage 4에서 원고 검증 시 에피소드 간 연속성, 스킬 타임라인,
관계 히스토리 검증을 담당.
inspector reference를 통해 BaseAgent 메서드(ask, _extract_json_robust 등)
및 공유 유틸리티(패턴, _is_same_item 등) 접근.
"""

import logging
import re

# =================================================================
# [V49.1 NEW] Stage 4 원고 연속성 검증 프롬프트
# =================================================================
MANUSCRIPT_CONTINUITY_PROMPT = """
[Role] 원고 연속성 검증 전문가 (Manuscript Continuity Inspector)
[Task] Writer가 생성한 원고가 이전 원고들과 논리적으로 연결되고, Blueprint 설계를 준수하는지 정밀 검증

### 📋 검증 대상: 제 {current_ep}화 원고
{manuscript_excerpt}

### 📜 이전 원고 타임라인 (최근 {prev_count}화)
{prev_manuscripts_timeline}

### 📐 Blueprint 설계서 (현재 에피소드)
{blueprint_scenario}

### 🎯 핵심 검증 항목

#### 1. 아이템/무기 연속성 (이전 원고 대비)
- 이전 원고들에서 획득한 아이템만 사용하고 있는가?
- 이전 화 끝에서 소지하던 무기가 현재 화 시작에도 유지되는가?
- 획득하지 않은 아이템을 갑자기 사용하고 있지 않은가?

#### 2. 상태 연속성 (이전 원고 대비)
- 직전 화 끝의 부상/피로 상태가 현재 화에 반영되는가?
- 내공/경지가 급격히 변화하지 않았는가?
- 캐릭터의 신체적 상태가 자연스럽게 연결되는가?

#### 3. 관계 연속성 (이전 원고 대비)
- NPC와의 관계가 역행(경외→멸시, 적대→친밀)하지 않는가?
- 이전 사건으로 인한 평판 변화가 반영되는가?
- 정보 전파 시간을 고려해도 모순인 반응이 있는가?

#### 4. Blueprint 준수 여부
- Blueprint에 설계된 핵심 씬(Core Scene)이 원고에 반영되었는가?
- Blueprint의 Cliffhanger 엔딩이 원고 끝에 구현되었는가?
- 설계된 공간/시간 배경이 원고와 일치하는가?
- Blueprint 범위를 넘어선 과잉 생성이 없는가?

### 🚨 판정 기준
- CRITICAL: 명백한 모순 (없는 아이템 사용, 죽은 NPC 등장, 수여 전 소지)
- MAJOR: 심각한 불일치 (상태 급변, 설정 충돌, Blueprint 핵심 씬 누락)
- MINOR: 경미한 차이 (표현 방식, 세부 묘사 차이)
- NONE: 연속성 문제 없음

### [Chain-of-Thought Analysis]
다음 순서로 분석하십시오:

Step 1: 아이템/무기 추적
- 이전 원고들에서 획득한 아이템 목록 작성
- 현재 원고에서 사용/소지하는 아이템 확인
- 미획득 아이템 사용 여부 판정

Step 2: 상태 연속성 분석
- 직전 원고 종료 시점의 상태 확인
- 현재 원고 시작 시점의 상태 확인
- 급격한 변화 여부 판정

Step 3: 관계 일관성 분석
- 이전 원고들의 관계 변화 추적
- 현재 원고의 NPC 반응 확인
- 관계 역행 여부 판정

Step 4: Blueprint 준수 분석
- Blueprint 핵심 씬 목록 확인
- 원고에서 해당 씬 반영 여부 확인
- 누락/과잉 생성 여부 판정

Step 5: [V61 NEW] Entity 명칭 일관성 검증
- Entity Registry가 제공된 경우, 등록된 정식 명칭과 현재 원고의 명칭 비교
- 캐릭터명이 일관되게 사용되는지 확인 (예: '팽무진' vs '무진' vs '주인공')
- 조직/문파명, 장소명, 물품명, 기술명의 일관성 확인
- Entity Registry:
{entity_registry}

Step 6: 최종 판정
- 위 5단계를 종합하여 PASS/REJECT 결정
- 위반 사항 목록 작성
- 수정 지시 작성

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "continuity_analysis": {{
        "items_in_prev": ["이전 원고들에서 획득한 아이템"],
        "items_used_now": ["현재 원고에서 사용하는 아이템"],
        "items_used_correctly": true/false,
        "state_from_prev": "직전 원고 종료 시 상태",
        "state_in_current": "현재 원고 시작 시 상태",
        "state_consistent": true/false,
        "relationships_consistent": true/false
    }},
    "blueprint_alignment": {{
        "core_scenes_in_blueprint": ["Blueprint의 핵심 씬 목록"],
        "scenes_reflected_in_manuscript": ["원고에 반영된 씬 목록"],
        "scenes_reflected": 반영된_씬_개수,
        "total_scenes": 총_씬_개수,
        "cliffhanger_implemented": true/false,
        "missing_elements": ["누락된 요소 목록"],
        "excess_elements": ["과잉 생성된 요소 목록"]
    }},
    "entity_consistency": {{
        "mismatches": [
            {{
                "category": "character | organization | location | object | concept",
                "registered_name": "등록된 정식 명칭",
                "current_name": "현재 사용된 명칭",
                "severity": "CRITICAL | MAJOR | MINOR",
                "recommendation": "수정 권고"
            }}
        ]
    }},
    "violations": [
        {{
            "type": "unowned_item_usage" | "state_discontinuity" | "relationship_reversal" | "blueprint_violation",
            "severity": "CRITICAL" | "MAJOR" | "MINOR",
            "description": "위반 상세 설명",
            "evidence_prev": "이전 원고 근거",
            "evidence_curr": "현재 원고 근거"
        }}
    ],
    "warnings": ["MINOR 수준의 경고 목록"],
    "fix_instructions": "수정 지시 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""


# [V59] 스킬 관련 패턴 (클래스 레벨 상수)
SKILL_ACQUISITION_PATTERNS = [
    r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|결|공|권법|검법|장법|각법|신법|보법|심법|기공))['\"]?(?:을|를)\s*(?:익히|배우|습득|전수받|깨달|체득)",
    r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:초식|절초|절기|비기|오의))['\"]?(?:을|를)\s*(?:익히|배우|습득|전수받|터득)",
    r"(?:전수|가르침|지도).*?['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|공|결|술))['\"]?",
    r"비급.*?['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|공|결|심법))['\"]?",
]

SKILL_USAGE_PATTERNS = [
    r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|결|공|권법|검법|장법|각법|신법|보법))['\"]?(?:을|를)?\s*(?:펼치|시전|사용|발동|구사)",
    r"['\"]?([가-힣a-zA-Z0-9]{2,20}(?:초식|절초|절기|비기|오의))['\"]?(?:을|를)?\s*(?:펼치|날리|전개)",
    r"(?:내공|진기).*?['\"]?([가-힣a-zA-Z0-9]{2,20}(?:법|공|결))['\"]?",
]


class ContinuityManuscriptValidator:
    """
    [V64.P3] ContinuityInspector에서 분리된 원고 수준 연속성 검증 모듈

    담당:
    - inspect_manuscript(): Stage 4에서 원고 연속성 검증 (메인 공개 API)
    - inspect_manuscript_v59(): V59 강화 검증 (스킬 + 관계 타임라인)
    - _manuscript_python_precheck(): Python 사전 필터링
    - _check_relationship_jump(): 관계 급변 탐지
    - _check_villain_intelligence(): 악역 지능 보호
    - _check_time_flow(): 시간 흐름 검증
    - _check_reader_immersion(): 독자 몰입도 예측
    - _check_skill_timeline(): V59 스킬 타임라인
    - _track_relationship_history(): V59 관계 히스토리
    """

    def __init__(self, inspector) -> None:
        """
        Args:
            inspector: ContinuityInspector 인스턴스 (BaseAgent 상속, 공유 상태 접근용)
        """
        self._ci = inspector
        # [V67.1] incarnation_type 캐시 — 회귀자 오탐 방지
        self._incarnation_type = self._extract_incarnation_type()

    def _extract_incarnation_type(self) -> str:
        """[V67.1] master_bible에서 incarnation_type 추출 (graceful fallback)"""
        try:
            if hasattr(self._ci, "context") and self._ci.context:
                _bible = getattr(self._ci.context, "master_bible", None)
                if _bible:
                    _bible_root = _bible.get("MasterBible", _bible)
                    return _bible_root.get("protagonist_config", {}).get("incarnation_type", "")
        except Exception as e:
            logging.warning(f"[ContinuityManuscript] incarnation_type 추출 실패: {e}")
        return ""

    # =================================================================
    # 원고 Python 사전 검증에서 사용하는 패턴 (인스턴스에서 복사)
    # =================================================================
    ACQUISITION_PATTERNS = [
        r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:획득|챙기|얻|주워\s*들|가져)",
        r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:손에\s*넣|가져가|챙겨\s*들)",
    ]

    POSSESSION_PATTERNS = [
        r"품속.*?(.+?)(?:이|가)\s*(?:있|자리)",
        r"(.+?)(?:을|를)\s*(?:들어\s*보이|꺼내|쥐)",
        r"(?:쥔|든|멘)\s*(.+?)",
    ]

    def inspect_manuscript(
        self,
        current_ep: int,
        manuscript: str,
        blueprint: dict,
        prev_manuscripts: list[dict],
        hud_history: list[dict] = None,
        entity_registry: dict = None,
    ) -> dict:
        """
        [V49.1] 원고 연속성 검증 실행

        Args:
            current_ep: 현재 에피소드 번호
            manuscript: Writer가 생성한 원고 텍스트
            blueprint: 현재 에피소드 Blueprint dict
            prev_manuscripts: 이전 원고 리스트
            hud_history: HUD 스냅샷 히스토리 (선택적)
            entity_registry: [V61] Entity Registry dict

        Returns:
            {decision, severity, continuity_analysis, blueprint_alignment, entity_consistency, violations, warnings, fix_instructions}
        """
        # 1화는 이전 원고가 없으므로 Blueprint 준수만 체크
        if current_ep <= 1 or not prev_manuscripts:
            return self._check_blueprint_only(current_ep, manuscript, blueprint)

        # 원고가 비어있으면 REJECT
        if not manuscript or len(manuscript.strip()) < 500:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "continuity_analysis": {},
                "entity_consistency": {},
                "blueprint_alignment": {},
                "violations": [
                    {
                        "type": "empty_manuscript",
                        "severity": "CRITICAL",
                        "description": "원고가 비어있거나 너무 짧습니다.",
                    }
                ],
                "warnings": [],
                "fix_instructions": "최소 500자 이상의 원고를 생성하십시오.",
            }

        # ═══════════════════════════════════════════════════════════════
        # Phase 1: Python 기반 사전 필터링
        # ═══════════════════════════════════════════════════════════════
        python_check = self._manuscript_python_precheck(current_ep, manuscript, prev_manuscripts, blueprint)

        python_advisory = python_check.get("critical_violations", [])
        if python_advisory:
            logging.info(f"📋 [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")

        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증
        # ═══════════════════════════════════════════════════════════════

        prev_timeline = self._format_prev_manuscripts(prev_manuscripts)

        blueprint_scenario = blueprint.get("integrated_scenario", "")
        if not blueprint_scenario:
            blueprint_scenario = str(blueprint.get("scene_breakdown", {}))

        manuscript_excerpt = manuscript[:4000] if len(manuscript) > 4000 else manuscript
        entity_registry_str = self._ci._format_entity_registry(entity_registry)

        prompt = MANUSCRIPT_CONTINUITY_PROMPT.format(
            current_ep=current_ep,
            manuscript_excerpt=self._ci._escape_braces(manuscript_excerpt),
            prev_count=len(prev_manuscripts),
            prev_manuscripts_timeline=self._ci._escape_braces(prev_timeline[:6000]),
            blueprint_scenario=self._ci._escape_braces(blueprint_scenario[:2000]),
            entity_registry=self._ci._escape_braces(entity_registry_str),
        )

        try:
            response = self._ci.ask(prompt, temperature=0.1)
            result = self._ci._extract_json_robust(response)

            if not isinstance(result, dict):
                logging.warning("⚠️ [V60.74] JSON 파싱 실패 - 수동 검수 권장")
                result = {
                    "decision": "PASS",
                    "severity": "NONE",
                    "continuity_analysis": {},
                    "entity_consistency": {},
                    "blueprint_alignment": {},
                    "violations": [],
                    "warnings": ["[V60.74] LLM 응답 파싱 실패 - 수동 검수 필요"],
                    "confidence": 0.0,
                    "parsing_error": True,
                }

            if python_check.get("warnings"):
                result.setdefault("warnings", [])
                # [Sweep53] dict warnings → str 변환 (LLM result["warnings"]는 list[str])
                result["warnings"].extend(
                    w.get("description", str(w)) if isinstance(w, dict) else w for w in python_check["warnings"]
                )

            # [Sweep54] critical_violations도 warnings로 병합 (inspect_arc와 동일 패턴)
            if python_check.get("critical_violations"):
                result.setdefault("warnings", [])
                for _cv in python_check["critical_violations"]:
                    _cv_desc = (
                        _cv.get("description", _cv.get("item_or_subject", "알 수 없음"))
                        if isinstance(_cv, dict)
                        else str(_cv)
                    )
                    result["warnings"].append(f"[Python advisory] {_cv_desc}")

            return result

        except Exception as e:
            logging.warning(f"🚨 [ContinuityInspector] 원고 LLM 검증 실패: {e}")
            if python_check.get("warnings"):
                _warnings = list(python_check["warnings"])
                _warnings.append("LLM 검증 실패 - 수동 확인 권장")
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "degraded": True,
                    "degraded_reason": str(e),
                    "continuity_analysis": python_check.get("timeline", {}),
                    "entity_consistency": {},
                    "blueprint_alignment": {},
                    "violations": [],
                    "warnings": _warnings,
                    "fix_instructions": "LLM 검증 실패 - Python 사전 검증만 수행됨",
                }
            return {
                "decision": "PASS",
                "severity": "MINOR",
                "degraded": True,
                "degraded_reason": str(e),
                "continuity_analysis": {},
                "entity_consistency": {},
                "blueprint_alignment": {},
                "violations": [],
                "warnings": ["LLM 검증 실패 - 수동 확인 권장"],
                "fix_instructions": "",
            }

    def get_prev_manuscripts(self, current_ep: int, window: int = 5) -> list[dict]:
        """DB에서 이전 원고들을 조회하는 헬퍼 메서드"""
        prev_manuscripts = []

        if not hasattr(self._ci, "context") or not self._ci.context:
            return prev_manuscripts

        start_ep = max(1, current_ep - window)

        for ep in range(start_ep, current_ep):
            try:
                ms = self._ci.context.db.get_manuscript(ep)
                if ms and isinstance(ms, dict):
                    prev_manuscripts.append(
                        {"ep_num": ep, "content": ms.get("content", ""), "title": ms.get("title", "")}
                    )
            except Exception as e:
                logging.warning(f"⚠️ [ContinuityInspector] 제{ep}화 원고 조회 실패: {e}")

        return prev_manuscripts

    def _manuscript_python_precheck(
        self, current_ep: int, manuscript: str, prev_manuscripts: list[dict], blueprint: dict
    ) -> dict:
        """[V49.1] 원고 연속성 Python 기반 사전 필터링"""
        critical_violations = []
        warnings = []

        # 1. 이전 원고들에서 아이템 추출
        all_acquired_items = set()
        last_ep_items = set()
        last_ep_state = ""

        for prev_ms in prev_manuscripts:
            prev_content = prev_ms.get("content", "")
            ep_num = prev_ms.get("ep_num", 0)

            for pattern in self.ACQUISITION_PATTERNS:
                matches = re.findall(pattern, prev_content)
                for match in matches:
                    item = match.strip() if isinstance(match, str) else match[0].strip() if match else ""
                    if item and len(item) >= 2:
                        all_acquired_items.add(item)
                        if ep_num == current_ep - 1:
                            last_ep_items.add(item)

            if ep_num == current_ep - 1:
                last_ep_state = prev_content[-500:] if len(prev_content) > 500 else prev_content

        # 2. 현재 원고에서 사용 아이템 추출
        used_items = set()
        for pattern in self.POSSESSION_PATTERNS:
            matches = re.findall(pattern, manuscript)
            for match in matches:
                item = match.strip() if isinstance(match, str) else match[0].strip() if match else ""
                if item and len(item) >= 2:
                    used_items.add(item)

        # 3. 미획득 아이템 사용 체크
        for item in used_items:
            if item and not self._is_item_acquired(item, all_acquired_items):
                if item not in ["무기", "검", "도", "창", "활", "손", "발", "몸", "눈", "입"]:
                    critical_violations.append(
                        {
                            "type": "unowned_item_usage",
                            "severity": "CRITICAL",
                            "item_or_subject": item,
                            "description": f"'{item}'은(는) 이전 원고에서 획득한 기록이 없습니다.",
                        }
                    )

        # 4. 부상 상태 연속성 체크
        injury_keywords = ["부상", "중상", "피를 흘", "쓰러", "기절", "골절", "찢어"]
        recovery_keywords = ["멀쩡", "회복", "완치", "상처가 아물"]

        prev_injured = any(kw in last_ep_state for kw in injury_keywords)
        current_start = manuscript[:500] if len(manuscript) > 500 else manuscript
        current_recovered = any(kw in current_start for kw in recovery_keywords)

        if prev_injured and current_recovered:
            warnings.append(
                {
                    "type": "rapid_recovery",
                    "severity": "MINOR",
                    "description": "직전 화에서 부상 상태였으나 현재 화 시작에서 회복된 것처럼 묘사됨",
                }
            )

        # 5. Blueprint 핵심 씬 반영 체크
        scene_breakdown = blueprint.get("scene_breakdown", {})
        if scene_breakdown and isinstance(scene_breakdown, dict):
            core_scenes = [k for k, v in scene_breakdown.items() if "[Core]" in str(v)]
            reflected_count = 0

            for scene_key in core_scenes:
                scene_desc = scene_breakdown.get(scene_key, "")
                keywords = self._extract_keywords(scene_desc)
                if any(kw in manuscript for kw in keywords if kw):
                    reflected_count += 1

            if core_scenes and reflected_count < len(core_scenes) // 2:
                critical_violations.append(
                    {
                        "type": "blueprint_violation",
                        "severity": "MAJOR",
                        "description": f"Blueprint 핵심 씬 {len(core_scenes)}개 중 {reflected_count}개만 반영됨",
                    }
                )

        # 6. [V49.5] 관계 급변 탐지
        relationship_issues = self._check_relationship_jump(prev_manuscripts, manuscript)
        for issue in relationship_issues:
            if issue.get("severity") == "MAJOR":
                critical_violations.append(issue)
            else:
                warnings.append(issue)

        # 7. [V49.5] 악역 지능 보호
        villain_issues = self._check_villain_intelligence(prev_manuscripts, manuscript)
        for issue in villain_issues:
            if issue.get("severity") == "CRITICAL":
                critical_violations.append(issue)
            else:
                warnings.append(issue)

        # 8. [V49.5] 시간 흐름 검증
        time_issues = self._check_time_flow(prev_manuscripts, manuscript)
        warnings.extend(time_issues)

        # 9. [V49.5] 독자 몰입도 예측
        immersion_issues = self._check_reader_immersion(prev_manuscripts, manuscript, current_ep)
        warnings.extend(immersion_issues)

        return {
            "critical_violations": critical_violations,
            "warnings": warnings,
            "timeline": {"acquired_items": list(all_acquired_items), "used_items": list(used_items)},
        }

    def _is_item_acquired(self, item: str, acquired_items: set[str]) -> bool:
        """아이템이 이미 획득되었는지 확인"""
        if item in acquired_items:
            return True
        for acquired in acquired_items:
            if item in acquired or acquired in item:
                return True
        return False

    def _check_relationship_jump(self, prev_manuscripts: list[dict], manuscript: str) -> list[dict]:
        """
        [V49.5] 관계 급변 탐지

        [V67.1] 회귀자 incarnation_type 인식: 전생 관계 재연으로 급변 설명 가능
        """
        warnings = []
        # [V67.1] 회귀자 맥락 접미사
        _regressor_suffix = " [회귀자 — 전생 관계 재연 가능]" if self._incarnation_type == "회귀자" else ""

        RELATIONSHIP_KEYWORDS = {
            "멸시": ["멸시", "비웃", "하찮", "하인 취급", "깔보", "경멸", "조롱", "무시당"],
            "무시": ["무시", "대수롭지", "관심 없", "신경 쓰지", "거들떠보지"],
            "의심": ["의심", "수상", "이상하", "믿을 수 없", "의구심", "진심인가"],
            "경외": ["경외", "두려워", "떨며", "감히 못", "공포", "벌벌", "존경", "눈빛이 달라"],
            "충성": ["충성", "주군", "목숨 바쳐", "명을 따르", "따르겠", "주군님", "만세"],
        }

        STATE_PRIORITY = {"멸시": 0, "무시": 1, "의심": 2, "경외": 3, "충성": 4}

        ALLOWED_TRANSITIONS = {
            "멸시": ["무시", "의심"],
            "무시": ["의심", "경외"],
            "의심": ["경외", "무시"],
            "경외": ["충성", "의심"],
            "충성": ["경외"],
        }

        GROUP_KEYWORDS = ["사병", "무사들", "병사들", "부하들", "수하들", "호위", "교두", "장로들"]

        prev_states = {}
        for prev_ms in prev_manuscripts:
            content = prev_ms.get("content", "")
            for group in GROUP_KEYWORDS:
                if group in content:
                    idx = content.rfind(group)
                    context = content[max(0, idx - 300) : min(len(content), idx + 300)]
                    for state, keywords in RELATIONSHIP_KEYWORDS.items():
                        if any(kw in context for kw in keywords):
                            prev_states[group] = state
                            break

        current_states = {}
        for group in GROUP_KEYWORDS:
            if group in manuscript:
                idx = manuscript.find(group)
                context = manuscript[max(0, idx - 300) : min(len(manuscript), idx + 300)]
                for state, keywords in RELATIONSHIP_KEYWORDS.items():
                    if any(kw in context for kw in keywords):
                        current_states[group] = state
                        break

        for group, current_state in current_states.items():
            if group in prev_states:
                prev_state = prev_states[group]
                if current_state != prev_state:
                    allowed = ALLOWED_TRANSITIONS.get(prev_state, [])
                    if current_state not in allowed:
                        jump_distance = abs(STATE_PRIORITY.get(current_state, 0) - STATE_PRIORITY.get(prev_state, 0))
                        severity = "MAJOR" if jump_distance >= 2 else "MINOR"
                        warnings.append(
                            {
                                "type": "relationship_jump",
                                "severity": severity,
                                "description": f"'{group}'의 관계가 '{prev_state}'→'{current_state}'로 급변함 (점프 거리: {jump_distance}단계). "
                                f"'{prev_state}'에서 허용된 전환: {allowed}. "
                                f"중간 단계(예: 경외)를 거치는 묘사 필요.{_regressor_suffix}",
                            }
                        )

        return warnings

    def _check_villain_intelligence(self, prev_manuscripts: list[dict], manuscript: str) -> list[dict]:
        """[V49.5] 악역 지능 보호 - [V55.5] 2회 이상 과소평가 → CRITICAL"""
        issues = []

        UNDERESTIMATE_KEYWORDS = [
            "철부지",
            "객기",
            "어린 놈",
            "망나니",
            "한심",
            "우습",
            "내버려 둬",
            "방심",
            "신경 쓸 것 없",
            "겁줄 것 없",
            "어차피",
            "알아서 망할",
            "제풀에 지쳐",
        ]

        VIGILANT_KEYWORDS = ["의심", "경계", "감시", "조사", "확인", "주시", "예의주시", "눈여겨", "수상", "이상하"]

        LEARNING_KEYWORDS = [
            "다음엔",
            "이번엔",
            "대비",
            "각오",
            "반드시",
            "두 번 다시",
            "실수를 반복",
            "방심했던",
            "얕보았던 게",
            "조심해야",
        ]

        underestimate_count = 0
        vigilant_found = False
        learning_found = False

        for prev_ms in prev_manuscripts:
            content = prev_ms.get("content", "")
            if any(kw in content for kw in UNDERESTIMATE_KEYWORDS):
                underestimate_count += 1
            if any(kw in content for kw in VIGILANT_KEYWORDS):
                vigilant_found = True
            if any(kw in content for kw in LEARNING_KEYWORDS):
                learning_found = True

        current_underestimate = any(kw in manuscript for kw in UNDERESTIMATE_KEYWORDS)
        current_vigilant = any(kw in manuscript for kw in VIGILANT_KEYWORDS)
        current_learning = any(kw in manuscript for kw in LEARNING_KEYWORDS)

        if current_underestimate and underestimate_count >= 1 and not vigilant_found and not current_vigilant:
            if not learning_found and not current_learning:
                issues.append(
                    {
                        "type": "stupid_villain",
                        "severity": "CRITICAL",
                        "description": f"악역이 주인공을 {underestimate_count + 1}회 연속 과소평가 중. "
                        f"'어리석은 악역' 클리셰로 서사 몰입도 저하. "
                        f"최소 1회는 경계/의심 또는 '다음엔 대비하겠다'는 학습 반응 필요.",
                        "fix_suggestion": "악역이 주인공에게 당한 후 '이 녀석, 만만치 않군...' 또는 "
                        "'다음엔 반드시 대비하겠다' 같은 학습 반응 추가",
                    }
                )
            else:
                issues.append(
                    {
                        "type": "stupid_villain",
                        "severity": "MINOR",
                        "description": f"악역이 주인공을 {underestimate_count + 1}회 과소평가 (학습 반응 감지됨). "
                        f"지속적인 과소평가 주의.",
                    }
                )

        return issues

    def _check_time_flow(self, prev_manuscripts: list[dict], manuscript: str) -> list[dict]:
        """[V49.5] 시간 흐름 검증"""
        warnings = []

        TIME_PASS_KEYWORDS = ["다음 날", "이틀 후", "며칠 후", "일주일", "한 달", "다음날 아침"]
        SAME_DAY_KEYWORDS = ["그날 밤", "같은 날", "그 시각", "잠시 후", "얼마 지나지 않아"]
        MAJOR_EVENT_KEYWORDS = [
            "전투",
            "혈투",
            "습격",
            "잠입",
            "도박장",
            "연회",
            "대결",
            "비무",
            "암살",
            "폭발",
            "화재",
        ]
        INJURY_KEYWORDS = ["부상", "중상", "피를 흘", "골절", "탈골", "찢어", "터져"]
        RECOVERY_KEYWORDS = ["회복", "치료", "요양", "휴식", "쉬"]

        if prev_manuscripts:
            last_ms = prev_manuscripts[-1]
            last_content = last_ms.get("content", "")

            last_had_event = any(kw in last_content for kw in MAJOR_EVENT_KEYWORDS)
            last_had_injury = any(kw in last_content[-1000:] for kw in INJURY_KEYWORDS)

            current_same_day = any(kw in manuscript[:500] for kw in SAME_DAY_KEYWORDS)
            current_time_passed = any(kw in manuscript[:500] for kw in TIME_PASS_KEYWORDS)
            current_has_event = any(kw in manuscript for kw in MAJOR_EVENT_KEYWORDS)
            current_has_recovery = any(kw in manuscript[:500] for kw in RECOVERY_KEYWORDS)

            if last_had_event and current_has_event and current_same_day and not current_time_passed:
                warnings.append(
                    {
                        "type": "unrealistic_timeline",
                        "severity": "MINOR",
                        "description": "연속된 대형 이벤트가 같은 날에 발생. "
                        "시간 경과 묘사 또는 체력적 한계 묘사 권장.",
                    }
                )

            if last_had_injury and current_has_event and not current_has_recovery and not current_time_passed:
                warnings.append(
                    {
                        "type": "injury_ignored",
                        "severity": "MINOR",
                        "description": "직전 화에서 부상 후 회복/시간 경과 없이 대형 이벤트 진행. "
                        "응급처치, 회복 묘사, 또는 무리하는 대가 묘사 권장.",
                    }
                )

        event_count = sum(1 for kw in MAJOR_EVENT_KEYWORDS if kw in manuscript)
        if event_count >= 3:
            warnings.append(
                {
                    "type": "event_overload",
                    "severity": "MINOR",
                    "description": f"한 화에 대형 이벤트가 {event_count}개 이상. "
                    f"집중도 분산 위험. 일부를 다음 화로 분리 권장.",
                }
            )

        return warnings

    def _check_reader_immersion(self, prev_manuscripts: list[dict], manuscript: str, current_ep: int) -> list[dict]:
        """
        [V49.5] 독자 몰입도 예측

        [V67.1] 회귀자 incarnation_type 인식: 전생 지식 기반 빠른 성장/능력 사용 맥락 추가
        """
        warnings = []
        # [V67.1] 회귀자 맥락 접미사
        _regressor_suffix = (
            " [회귀자 — 전생 지식으로 설명 가능할 수 있음]" if self._incarnation_type == "회귀자" else ""
        )

        # 1. 공짜 파워업 감지
        POWERUP_KEYWORDS = ["경지 상승", "돌파", "각성", "깨달음", "내공 증가", "실력 향상", "한 수 위"]
        COST_KEYWORDS = ["대가", "희생", "고통", "부작용", "한계", "무리", "피를 토", "쓰러"]

        has_powerup = any(kw in manuscript for kw in POWERUP_KEYWORDS)
        has_cost = any(kw in manuscript for kw in COST_KEYWORDS)

        if has_powerup and not has_cost:
            warnings.append(
                {
                    "type": "free_powerup",
                    "severity": "MINOR",
                    "description": f"파워업/성장이 묘사되었으나 대가/고통 묘사 없음. "
                    f"'공짜 파워업' 느낌 방지를 위해 대가 묘사 권장.{_regressor_suffix}",
                }
            )

        # 2. 갑작스러운 능력 사용
        ABILITY_KEYWORDS = ["비전", "절기", "비급", "암기", "독문", "가전"]

        current_abilities = [kw for kw in ABILITY_KEYWORDS if kw in manuscript]
        if current_abilities and prev_manuscripts:
            prev_all_text = " ".join(m.get("content", "") for m in prev_manuscripts)
            new_abilities = [a for a in current_abilities if a not in prev_all_text]

            if new_abilities and current_ep > 3:
                warnings.append(
                    {
                        "type": "sudden_ability",
                        "severity": "MINOR",
                        "description": f"이전에 언급 없던 능력 갑자기 등장: {new_abilities}. "
                        f"복선이나 기연 묘사 없이 등장하면 '설정 추가' 느낌.{_regressor_suffix}",
                    }
                )

        # 3. 주인공 무쌍 과다
        WIN_KEYWORDS = ["쓰러뜨", "제압", "격파", "승리", "이겼", "물리쳤", "쓰러졌다"]
        STRUGGLE_KEYWORDS = ["위기", "궁지", "밀리", "고전", "위험", "절체절명"]

        win_count = sum(1 for kw in WIN_KEYWORDS if kw in manuscript)
        has_struggle = any(kw in manuscript for kw in STRUGGLE_KEYWORDS)

        if win_count >= 3 and not has_struggle:
            warnings.append(
                {
                    "type": "effortless_victory",
                    "severity": "MINOR",
                    "description": f"다수의 승리({win_count}회) 묘사가 있으나 고전/위기 묘사 없음. "
                    f"긴장감 저하 우려. 최소 1회 위기 상황 권장.",
                }
            )

        # 4. 연속 행운
        LUCK_KEYWORDS = ["마침", "우연히", "때마침", "운 좋게", "다행히", "공교롭게"]
        luck_count = sum(1 for kw in LUCK_KEYWORDS if kw in manuscript)

        if luck_count >= 2:
            warnings.append(
                {
                    "type": "excessive_luck",
                    "severity": "MINOR",
                    "description": f"우연/행운 표현이 {luck_count}회 사용됨. "
                    f"'작가 편의' 느낌 방지를 위해 인과관계 강화 권장.",
                }
            )

        return warnings

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> list[str]:
        """텍스트에서 핵심 키워드 추출"""
        pattern = r"[가-힣]{2,}"
        words = re.findall(pattern, text)

        stopwords = {
            "것이다",
            "있다",
            "없다",
            "하다",
            "되다",
            "이다",
            "그",
            "저",
            "이",
            "그것",
            "저것",
            "이것",
            "때문",
            "그래서",
            "하지만",
            "그러나",
        }
        keywords = [w for w in words if w not in stopwords and len(w) >= 2]

        return keywords[:max_keywords]

    def _format_prev_manuscripts(self, prev_manuscripts: list[dict]) -> str:
        """이전 원고들을 LLM용 타임라인 형식으로 변환"""
        lines = []

        for ms in prev_manuscripts:
            ep_num = ms.get("ep_num", 0)
            content = ms.get("content", "")
            title = ms.get("title", f"제{ep_num}화")

            if len(content) > 1500:
                excerpt = content[:700] + "\n...(중략)...\n" + content[-500:]
            else:
                excerpt = content

            lines.append(f"### 제 {ep_num}화: {title}")
            lines.append(excerpt)
            lines.append("")

        return "\n".join(lines)

    def _check_blueprint_only(self, current_ep: int, manuscript: str, blueprint: dict) -> dict:
        """1화 또는 이전 원고 없을 때 Blueprint 준수만 체크"""
        scene_breakdown = blueprint.get("scene_breakdown", {})

        if not scene_breakdown or not isinstance(scene_breakdown, dict):
            return {
                "decision": "PASS",
                "severity": "NONE",
                "continuity_analysis": {},
                "entity_consistency": {},
                "blueprint_alignment": {"note": "Blueprint 없음"},
                "violations": [],
                "warnings": [],
                "fix_instructions": "",
            }

        total_scenes = len(scene_breakdown)
        reflected = 0
        missing = []

        for scene_key, scene_desc in scene_breakdown.items():
            keywords = self._extract_keywords(str(scene_desc))
            if any(kw in manuscript for kw in keywords if kw):
                reflected += 1
            else:
                missing.append(scene_key)

        severity = "NONE"
        decision = "PASS"

        if reflected < total_scenes // 2:
            severity = "MAJOR"
            decision = "REJECT"
        elif missing:
            severity = "MINOR"

        return {
            "decision": decision,
            "severity": severity,
            "continuity_analysis": {},
            "entity_consistency": {},
            "blueprint_alignment": {
                "scenes_reflected": reflected,
                "total_scenes": total_scenes,
                "missing_elements": missing,
            },
            "violations": [
                {
                    "type": "blueprint_violation",
                    "severity": severity,
                    "description": f"씬 {total_scenes}개 중 {reflected}개만 반영",
                }
            ]
            if decision == "REJECT"
            else [],
            "warnings": [f"누락된 씬: {missing}"] if missing and decision == "PASS" else [],
            "fix_instructions": f"다음 씬을 원고에 반영하세요: {missing}" if missing else "",
        }

    def _generate_manuscript_fix_instructions(self, violations: list[dict]) -> str:
        """원고 위반 사항에 대한 수정 지시 생성"""
        instructions = []

        for v in violations:
            v_type = v.get("type", "")
            item = v.get("item_or_subject", "")

            if v_type == "unowned_item_usage":
                instructions.append(
                    f"[미획득 아이템 사용 수정] '{item}'은(는) 이전 원고에서 획득한 기록이 없습니다. "
                    f"해당 아이템 사용 장면을 삭제하거나, 이전에 획득한 것으로 설정을 수정하세요."
                )
            elif v_type == "state_discontinuity":
                instructions.append(
                    "[상태 불연속 수정] 직전 화 상태가 현재 화에 연속되지 않습니다. "
                    "캐릭터의 부상/회복 상태를 이전 화와 일관되게 수정하세요."
                )
            elif v_type == "relationship_reversal":
                instructions.append(
                    "[관계 역행 수정] NPC와의 관계가 이전 원고와 모순됩니다. "
                    "관계 변화에 대한 서사적 근거를 추가하거나 반응을 수정하세요."
                )
            elif v_type == "blueprint_violation":
                instructions.append(
                    "[Blueprint 미준수] 설계된 핵심 씬이 원고에 반영되지 않았습니다. "
                    "Blueprint의 scene_breakdown에 명시된 씬들을 원고에 포함시키세요."
                )

        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."

    # ═══════════════════════════════════════════════════════════════════════════
    # [V59] 스킬 사용 타임라인 추적
    # ═══════════════════════════════════════════════════════════════════════════

    def _check_skill_timeline(self, current_ep: int, manuscript: str, prev_manuscripts: list[dict]) -> dict:
        """[V59] 스킬 사용 타임라인 검증"""
        violations = []
        warnings = []
        skill_timeline = {}

        for prev_ms in prev_manuscripts:
            prev_content = prev_ms.get("content", "")
            ep_num = prev_ms.get("ep_num", 0)

            for pattern in SKILL_ACQUISITION_PATTERNS:
                matches = re.findall(pattern, prev_content)
                for skill in matches:
                    skill = skill.strip() if isinstance(skill, str) else ""
                    if skill and len(skill) >= 2:
                        if skill not in skill_timeline:
                            skill_timeline[skill] = ep_num

        for pattern in SKILL_ACQUISITION_PATTERNS:
            matches = re.findall(pattern, manuscript)
            for skill in matches:
                skill = skill.strip() if isinstance(skill, str) else ""
                if skill and len(skill) >= 2:
                    if skill not in skill_timeline:
                        skill_timeline[skill] = current_ep

        used_skills = set()
        for pattern in SKILL_USAGE_PATTERNS:
            matches = re.findall(pattern, manuscript)
            for skill in matches:
                skill = skill.strip() if isinstance(skill, str) else ""
                if skill and len(skill) >= 2:
                    used_skills.add(skill)

        for skill in used_skills:
            generic_terms = ["내공", "진기", "기력", "무공", "검법", "권법", "장법"]
            if skill in generic_terms:
                continue

            is_acquired = False
            acquired_ep = None

            for known_skill, acq_ep in skill_timeline.items():
                if self._is_same_skill(skill, known_skill):
                    is_acquired = True
                    acquired_ep = acq_ep
                    break

            if not is_acquired:
                if current_ep > 5:
                    violations.append(
                        {
                            "type": "unlearned_skill_usage",
                            "severity": "MAJOR",
                            "skill": skill,
                            "description": f"'{skill}'은(는) 이전에 습득한 기록이 없습니다. "
                            f"배우지 않은 무공/스킬 사용은 연속성 오류입니다.",
                        }
                    )
                else:
                    warnings.append(
                        {
                            "type": "unlearned_skill_usage",
                            "severity": "MINOR",
                            "skill": skill,
                            "description": f"'{skill}' 사용됨 (습득 장면 권장)",
                        }
                    )

        return {"violations": violations, "warnings": warnings, "skill_timeline": skill_timeline}

    def _is_same_skill(self, skill1: str, skill2: str) -> bool:
        """두 스킬이 같은 것인지 판단"""
        skill1 = skill1.strip().lower()
        skill2 = skill2.strip().lower()

        if skill1 == skill2:
            return True

        if skill1 in skill2 or skill2 in skill1:
            return True

        keywords1 = set(re.findall(r"[가-힣]{2,}", skill1))
        keywords2 = set(re.findall(r"[가-힣]{2,}", skill2))

        stopwords = {"법", "공", "결", "술", "식", "초"}
        keywords1 -= stopwords
        keywords2 -= stopwords

        common = keywords1 & keywords2
        if len(common) >= 1 and (len(keywords1) <= 2 or len(keywords2) <= 2):
            return True

        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # [V59] 관계 변화 히스토리 추적 강화
    # ═══════════════════════════════════════════════════════════════════════════

    def _track_relationship_history(self, current_ep: int, manuscript: str, prev_manuscripts: list[dict]) -> dict:
        """
        [V59] 관계 변화 히스토리 추적 강화

        [V67.1] 회귀자 incarnation_type 인식: 전생 관계 재연으로 급변 설명 가능
        """
        violations = []
        warnings = []
        relationship_history = {}
        # [V67.1] 회귀자 맥락 접미사
        _regressor_suffix = " [회귀자 — 전생 관계 재연 가능]" if self._incarnation_type == "회귀자" else ""

        STATE_KEYWORDS = {
            "사망": ["죽었", "숨이 끊", "사망", "절명", "목숨을 잃", "숨을 거두"],
            "굴복": ["굴복", "용서를", "목숨을 구걸", "바닥을 기", "살려주", "복종", "무릎"],
            "충성": ["충성", "주군", "목숨 바쳐", "명을 따르", "따르겠", "만세", "주군님"],
            "경외": ["경외", "두려워", "떨며", "감히 못", "공포", "벌벌", "존경", "눈빛이 달라"],
            "의심": ["의심", "수상", "이상하", "믿을 수 없", "의구심", "진심인가", "정체가"],
            "무시": ["무시", "대수롭지", "관심 없", "신경 쓰지", "거들떠보지", "하찮"],
            "적대": ["적대", "원수", "죽이겠", "공격", "증오", "살의", "적의"],
        }

        STATE_ORDER = ["적대", "무시", "의심", "중립", "경외", "충성"]

        NPC_KEYWORDS = [
            "사병",
            "무사들",
            "병사들",
            "부하들",
            "수하들",
            "호위",
            "교두",
            "장로들",
            "가주",
            "대장로",
            "청사",
            "가솔들",
            "문주",
            "총관",
        ]

        def infer_state_from_context(npc: str, content: str) -> str:
            if npc not in content:
                return "알 수 없음"
            idx = content.find(npc)
            context = content[max(0, idx - 300) : min(len(content), idx + 300)]
            for state, keywords in STATE_KEYWORDS.items():
                if any(kw in context for kw in keywords):
                    return state
            return "중립"

        for prev_ms in prev_manuscripts:
            prev_content = prev_ms.get("content", "")
            ep_num = prev_ms.get("ep_num", 0)
            for npc in NPC_KEYWORDS:
                if npc in prev_content:
                    state = infer_state_from_context(npc, prev_content)
                    if state != "알 수 없음":
                        if npc not in relationship_history:
                            relationship_history[npc] = []
                        relationship_history[npc].append((ep_num, state))

        current_states = {}
        for npc in NPC_KEYWORDS:
            if npc in manuscript:
                state = infer_state_from_context(npc, manuscript)
                if state != "알 수 없음":
                    current_states[npc] = state
                    if npc not in relationship_history:
                        relationship_history[npc] = []
                    relationship_history[npc].append((current_ep, state))

        for npc, history in relationship_history.items():
            if len(history) < 2:
                continue

            prev_ep, prev_state = history[-2] if len(history) >= 2 else (0, "무시")
            curr_ep, curr_state = history[-1]

            if prev_state == curr_state:
                continue

            if prev_state in STATE_ORDER and curr_state in STATE_ORDER:
                prev_idx = STATE_ORDER.index(prev_state)
                curr_idx = STATE_ORDER.index(curr_state)
                jump_distance = abs(curr_idx - prev_idx)

                if jump_distance >= 2:
                    violations.append(
                        {
                            "type": "relationship_jump",
                            "severity": "MAJOR",
                            "npc": npc,
                            "from_state": prev_state,
                            "to_state": curr_state,
                            "from_ep": prev_ep,
                            "to_ep": curr_ep,
                            "jump_distance": jump_distance,
                            "description": f"'{npc}'의 관계가 제{prev_ep}화 '{prev_state}'에서 "
                            f"제{curr_ep}화 '{curr_state}'로 {jump_distance}단계 급변. "
                            f"중간 단계(예: {STATE_ORDER[prev_idx + 1] if prev_idx < len(STATE_ORDER) - 1 else prev_state})를 거치는 묘사 필요.{_regressor_suffix}",
                        }
                    )
                elif jump_distance == 1:
                    warnings.append(
                        {
                            "type": "relationship_change",
                            "severity": "INFO",
                            "npc": npc,
                            "description": f"'{npc}' 관계: {prev_state}→{curr_state} (정상 전환)",
                        }
                    )

        return {"relationship_history": relationship_history, "violations": violations, "warnings": warnings}

    def inspect_manuscript_v59(
        self,
        current_ep: int,
        manuscript: str,
        blueprint: dict,
        prev_manuscripts: list[dict],
        hud_history: list[dict] = None,
    ) -> dict:
        """[V59] 강화된 원고 연속성 검증 (스킬 + 관계 타임라인 포함)"""
        base_result = self.inspect_manuscript(current_ep, manuscript, blueprint, prev_manuscripts, hud_history)

        skill_check = self._check_skill_timeline(current_ep, manuscript, prev_manuscripts)
        rel_check = self._track_relationship_history(current_ep, manuscript, prev_manuscripts)

        all_violations = (
            base_result.get("violations", []) + skill_check.get("violations", []) + rel_check.get("violations", [])
        )
        all_warnings = base_result.get("warnings", []) + skill_check.get("warnings", []) + rel_check.get("warnings", [])

        if any(v.get("severity") in ["CRITICAL", "MAJOR"] for v in all_violations):
            final_decision = "REJECT"
            final_severity = "CRITICAL" if any(v.get("severity") == "CRITICAL" for v in all_violations) else "MAJOR"
        else:
            final_decision = base_result.get("decision", "PASS")
            final_severity = base_result.get("severity", "NONE")

        return {
            **base_result,
            "decision": final_decision,
            "severity": final_severity,
            "violations": all_violations,
            "warnings": all_warnings,
            "v59_skill_timeline": skill_check.get("skill_timeline", {}),
            "v59_relationship_history": rel_check.get("relationship_history", {}),
            "fix_instructions": self._generate_v59_fix_instructions(all_violations)
            if all_violations
            else base_result.get("fix_instructions", ""),
        }

    def _generate_v59_fix_instructions(self, violations: list[dict]) -> str:
        """[V59] 위반 사항에 대한 수정 지시 생성"""
        instructions = []

        for v in violations:
            v_type = v.get("type", "")

            if v_type == "unlearned_skill_usage":
                skill = v.get("skill", "")
                instructions.append(
                    f"[V59 스킬 연속성] '{skill}'은(는) 습득 기록 없이 사용됨. "
                    f"해당 스킬의 습득 장면을 이전 원고에 추가하거나, "
                    f"현재 원고에서 '이전에 배운'으로 언급하세요."
                )
            elif v_type == "relationship_jump":
                npc = v.get("npc", "")
                from_state = v.get("from_state", "")
                to_state = v.get("to_state", "")
                instructions.append(
                    f"[V59 관계 연속성] '{npc}'의 '{from_state}'→'{to_state}' 급변. "
                    f"중간 단계를 묘사하거나, 급변의 서사적 근거를 추가하세요."
                )
            else:
                instructions.append(self._generate_manuscript_fix_instructions([v]))

        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."
