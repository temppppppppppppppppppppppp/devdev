"""
[V64.P3] ContinuityBlueprintValidator — Blueprint 수준 연속성 검증 전담 모듈

ContinuityInspector God Object 분해의 두 번째 모듈.
Stage 3에서 Blueprint 생성 후 에피소드 간 연속성 검증을 담당.
inspector reference를 통해 BaseAgent 메서드(ask, _extract_json_robust 등)
및 공유 유틸리티(패턴, _is_same_item 등) 접근.
"""

import logging
import re

# =================================================================
# Blueprint 연속성 검증 프롬프트 (기존 CONTINUITY_INSPECTION_PROMPT)
# =================================================================
CONTINUITY_INSPECTION_PROMPT = """
[Role] 연속성 검증 전문가 (Continuity Inspector) - 전체 타임라인 분석
[Task] 현재 블루프린트가 제1화부터 지금까지의 전체 서사와 논리적으로 연결되는지 정밀 검증

### 📋 검증 대상
- 현재 에피소드: 제 {current_ep}화
- 현재 블루프린트 시나리오:
{current_scenario}

### 📜 전체 에피소드 타임라인 (제1화 ~ 제{prev_count}화)
{prev_summaries}

### 🎯 핵심 검증 항목 (전체 타임라인 기준)

#### 1. 아이템/무기 타임라인 검증 (전체 에피소드 추적)
- 제1화부터 현재까지 획득한 모든 아이템 목록을 추적하라
- 이미 획득한 아이템을 다시 획득하려 하는가?
- 아직 획득하지 않은 아이템을 소지하고 있는가?
- 무기/장비 소지 상태가 연속적인가?

#### 2. 수여물/신물 타임라인 검증 (전체 에피소드 추적)
- 공식 수여물(패, 권한, 직위 등)의 정확한 수여 시점을 추적하라
- 수여 시점 이전 에피소드에서 소지/사용 묘사가 있으면 CRITICAL 위반
- 수여 시점 이후 에피소드에서는 소지 상태로 시작해야 함

#### 3. 캐릭터 상태 연속성 (전체 서사 흐름)
- 부상 상태가 급격히 회복되지 않았는가?
- 내공/경지가 급격히 변화하지 않았는가?
- 이전 에피소드에서 발생한 상태 변화가 누적되고 있는가?

#### 4. 인물 반응 개연성 (전체 관계 변화 추적)
- 특정 에피소드에서 인정받거나 위상이 변화했다면, 이후 반응이 일관적인가?
- 정보 전파 시간(몇 시진, 하루 등)을 고려해도 모순인가?
- 관계 역행(경외→멸시)이 발생하면 WARNING

### 🚨 판정 기준
- CRITICAL: 명백한 타임라인 오류 (획득 전 소지, 수여 전 보유) → 즉시 REJECT
- MAJOR: 심각한 연속성 오류 (무기 리셋, 상태 급변) → REJECT
- MINOR: 경미한 불일치 (반응 개연성) → WARNING으로 PASS 가능
- NONE: 연속성 문제 없음 → PASS

### [Chain-of-Thought Analysis]
다음 순서로 분석하십시오:

Step 1: 아이템/무기 추적
- 이전 에피소드들에서 획득한 아이템 목록 작성
- 현재 블루프린트에서 획득하려는 아이템 확인
- 중복 획득 여부 판정

Step 2: 수여물 타임라인 분석
- 이전 에피소드들에서 공식 수여된 것들 목록
- 현재 블루프린트에서 소지/사용하는 수여물 확인
- 타임라인 모순 여부 판정

Step 3: 상태 연속성 분석
- 직전 에피소드 종료 시점의 상태 확인
- 현재 블루프린트 시작 시점의 상태 확인
- 급격한 변화 여부 판정

Step 4: 반응 개연성 분석
- 이전 사건들로 인한 관계/평판 변화 확인
- 현재 블루프린트의 NPC 반응 확인
- 불일치 여부 판정

Step 5: [V61 NEW] Entity 명칭 일관성 검증
- Entity Registry가 제공된 경우, 등록된 정식 명칭과 현재 블루프린트의 명칭 비교
- 캐릭터: 이전 에피소드에서 '팽무진'으로 확립되었는데 현재 '무진' 또는 '주인공'으로 표기되면 WARNING
- 조직/문파: '철혈문' vs '철혈파' 같은 미묘한 명칭 차이 탐지
- 장소: '무기고' vs '병기고' 같은 동일 장소의 다른 명칭 탐지
- 물품: '백근도' vs '거구도' 같은 동일 무기의 다른 명칭 탐지
- 기술/무공: '이화접목' vs '중검무봉' 같은 기술명 불일치 탐지
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
    "timeline_analysis": {{
        "items_acquired_before": ["이전에 획득한 아이템 목록"],
        "items_acquired_now": ["현재 획득하려는 아이템 목록"],
        "grants_received_before": ["이전에 수여받은 것들"],
        "grants_used_now": ["현재 사용/소지하는 수여물"]
    }},
    "entity_consistency": {{
        "registered_entities": {{"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}},
        "current_entities": {{"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}},
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
            "type": "duplicate_acquisition | premature_possession | state_discontinuity | reaction_mismatch | entity_name_mismatch",
            "severity": "CRITICAL | MAJOR | MINOR",
            "item_or_subject": "문제 대상",
            "prev_ep": "이전 발생 에피소드",
            "description": "모순 설명",
            "evidence_prev": "이전 에피소드 근거 텍스트",
            "evidence_curr": "현재 블루프린트 근거 텍스트"
        }}
    ],
    "warnings": ["MINOR 수준의 경고 목록"],
    "fix_instructions": "수정 지시 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""


class ContinuityBlueprintValidator:
    """
    [V64.P3] ContinuityInspector에서 분리된 Blueprint 수준 연속성 검증 모듈

    담당:
    - inspect(): Stage 3에서 Blueprint 생성 후 호출 (메인 공개 API)
    - _python_precheck(): Python 기반 사전 정보 수집
    - _format_prev_blueprints(): 이전 Blueprint 포맷팅
    - get_prev_blueprints(): DB 조회 헬퍼
    """

    def __init__(self, inspector) -> None:
        """
        Args:
            inspector: ContinuityInspector 인스턴스 (BaseAgent 상속, 공유 상태 접근용)
        """
        self._ci = inspector

    def inspect(
        self,
        current_ep: int,
        current_blueprint: dict,
        prev_blueprints: list[dict],
        hud_history: list[dict] = None,
        entity_registry: dict = None,
    ) -> dict:
        """
        블루프린트 연속성 검증 실행

        Args:
            current_ep: 현재 에피소드 번호
            current_blueprint: 현재 블루프린트 dict
            prev_blueprints: 이전 에피소드 블루프린트 리스트
            hud_history: HUD 스냅샷 히스토리 (선택적)
            entity_registry: [V61] Entity Registry dict

        Returns:
            {decision, severity, violations, warnings, fix_instructions, entity_consistency}
        """
        # 1화는 이전 에피소드가 없으므로 자동 PASS
        if current_ep <= 1 or not prev_blueprints:
            return {
                "decision": "PASS",
                "severity": "NONE",
                "timeline_analysis": {},
                "violations": [],
                "warnings": [],
                "fix_instructions": "",
            }

        # 현재 시나리오 추출
        current_scenario = current_blueprint.get("integrated_scenario", "")
        if isinstance(current_scenario, dict):
            current_scenario = str(current_scenario)
        if not current_scenario:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "timeline_analysis": {},
                "violations": [
                    {
                        "type": "missing_scenario",
                        "severity": "CRITICAL",
                        "description": "블루프린트에 integrated_scenario가 없습니다.",
                    }
                ],
                "warnings": [],
                "fix_instructions": "integrated_scenario를 포함한 완전한 블루프린트를 생성하십시오.",
            }

        # ═══════════════════════════════════════════════════════════════
        # Phase 1: Python 기반 사전 정보 수집 (Advisory Only)
        # ═══════════════════════════════════════════════════════════════
        python_check = self._python_precheck(current_ep, current_scenario, prev_blueprints)

        python_advisory = python_check.get("critical_violations", [])
        if python_advisory:
            logging.info(f"📋 [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")

        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증
        # ═══════════════════════════════════════════════════════════════

        prev_summaries = self._format_prev_blueprints(prev_blueprints)
        entity_registry_str = self._ci._format_entity_registry(entity_registry)

        prompt = CONTINUITY_INSPECTION_PROMPT.format(
            current_ep=current_ep,
            current_scenario=self._ci._escape_braces(current_scenario[:4000]),
            prev_count=len(prev_blueprints),
            prev_summaries=self._ci._escape_braces(prev_summaries),
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
                    "violations": [],
                    "warnings": ["[V60.74] LLM 응답 파싱 실패 - 수동 검수 필요"],
                    "confidence": 0.0,
                    "parsing_error": True,
                }

            # Python 검증 결과 병합
            if python_check.get("warnings"):
                result.setdefault("warnings", [])
                result["warnings"].extend(python_check["warnings"])

            return result

        except Exception as e:
            logging.warning(f"🚨 [ContinuityInspector] LLM 검증 실패: {e}")
            if python_check.get("warnings"):
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "timeline_analysis": python_check.get("timeline", {}),
                    "violations": [],
                    "warnings": python_check["warnings"],
                    "fix_instructions": "LLM 검증 실패 - Python 사전 검증만 수행됨",
                }
            return {
                "decision": "PASS",
                "severity": "NONE",
                "violations": [],
                "warnings": ["LLM 검증 실패 - 수동 확인 권장"],
                "fix_instructions": "",
            }

    def _python_precheck(self, current_ep: int, current_scenario: str, prev_blueprints: list[dict]) -> dict:
        """Python 기반 사전 검증 (빠른 필터링)"""
        critical_violations = []
        warnings = []

        acquired_items = {}
        granted_items = {}

        for bp in prev_blueprints:
            ep_num = bp.get("ep_num", 0)
            scenario = bp.get("integrated_scenario", "")
            if isinstance(scenario, dict):
                scenario = str(scenario)

            for pattern in self._ci.acquire_patterns:
                matches = re.findall(pattern, scenario)
                for item in matches:
                    item = item.strip()
                    if item and 2 <= len(item) <= 30:
                        acquired_items[item] = ep_num

            for pattern in self._ci.grant_patterns:
                matches = re.findall(pattern, scenario)
                for item in matches:
                    item = item.strip()
                    if item and 2 <= len(item) <= 30:
                        granted_items[item] = ep_num

        current_acquisitions = []
        for pattern in self._ci.acquire_patterns:
            matches = re.findall(pattern, current_scenario)
            for item in matches:
                item = item.strip()
                if item and 2 <= len(item) <= 30:
                    current_acquisitions.append(item)

        current_possessions = []
        for pattern in self._ci.possession_patterns:
            matches = re.findall(pattern, current_scenario)
            for item in matches:
                item = item.strip()
                if item and 2 <= len(item) <= 30:
                    current_possessions.append(item)

        # 검증 1: 중복 획득
        for curr_item in current_acquisitions:
            for prev_item, prev_ep in acquired_items.items():
                if self._ci._is_same_item(curr_item, prev_item):
                    critical_violations.append(
                        {
                            "type": "duplicate_acquisition",
                            "severity": "CRITICAL",
                            "item_or_subject": curr_item,
                            "prev_ep": prev_ep,
                            "description": f"'{prev_item}'은(는) 이미 제{prev_ep}화에서 획득했습니다. "
                            f"제{current_ep}화에서 다시 획득하려 합니다.",
                            "evidence_prev": f"제{prev_ep}화에서 획득",
                            "evidence_curr": f"현재 '{curr_item}' 획득 시도",
                        }
                    )
                    break

        # 검증 2: 미수여 소지
        grant_keywords = ["패", "권", "인장", "직위", "자격", "서"]

        for possession in current_possessions:
            for keyword in grant_keywords:
                if keyword in possession:
                    was_granted = False
                    granted_ep = None
                    for granted_item, g_ep in granted_items.items():
                        if keyword in granted_item:
                            was_granted = True
                            granted_ep = g_ep
                            break

                    if not was_granted:
                        critical_violations.append(
                            {
                                "type": "premature_possession",
                                "severity": "CRITICAL",
                                "item_or_subject": possession,
                                "prev_ep": None,
                                "description": f"'{possession}'을(를) 소지하고 있으나, "
                                f"이전 에피소드에서 수여받은 기록이 없습니다.",
                                "evidence_prev": "수여 기록 없음",
                                "evidence_curr": f"현재 '{possession}' 소지/사용",
                            }
                        )
                    break

        timeline = {
            "items_acquired_before": list(acquired_items.keys()),
            "grants_received_before": list(granted_items.keys()),
            "items_acquired_now": current_acquisitions,
            "items_possessed_now": current_possessions,
        }

        return {"critical_violations": critical_violations, "warnings": warnings, "timeline": timeline}

    def _format_prev_blueprints(self, prev_blueprints: list[dict]) -> str:
        """[V48.1] 전체 블루프린트를 LLM용 타임라인 형식으로 변환"""
        summaries = []

        all_acquisitions = []
        all_grants = []
        all_status_changes = []

        for bp in prev_blueprints:
            ep_num = bp.get("ep_num", "?")
            scenario = bp.get("integrated_scenario", "")
            if isinstance(scenario, dict):
                scenario = str(scenario)

            items = self._ci._extract_acquisitions(scenario)
            grants = self._ci._extract_grants(scenario)
            key_sentences = self._ci._extract_key_sentences(scenario)

            for item in items:
                all_acquisitions.append((ep_num, item))
            for grant in grants:
                all_grants.append((ep_num, grant))

            summary = f"""
═══ 제 {ep_num}화 ═══
[핵심 사건]
{key_sentences[:2000]}

[획득 아이템] {", ".join(items) if items else "없음"}
[수여물] {", ".join(grants) if grants else "없음"}
"""
            summaries.append(summary)

        timeline_header = f"""
╔══════════════════════════════════════════════════════════════╗
║  전체 아이템/수여물 타임라인 (제1화 ~ 제{len(prev_blueprints)}화)  ║
╚══════════════════════════════════════════════════════════════╝

[📦 획득 아이템 타임라인]
{self._format_timeline(all_acquisitions) if all_acquisitions else "- 없음"}

[🎖️ 수여물 타임라인]
{self._format_timeline(all_grants) if all_grants else "- 없음"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        return timeline_header + "\n".join(summaries)

    def _format_timeline(self, items: list[tuple]) -> str:
        """타임라인 항목을 포맷팅"""
        lines = []
        for ep, item in items:
            lines.append(f"- 제{ep}화: {item}")
        return "\n".join(lines)

    def get_prev_blueprints(self, current_ep: int, window: int = None) -> list[dict]:
        """DB에서 이전 블루프린트들을 조회하는 헬퍼 메서드"""
        prev_blueprints = []

        if not hasattr(self._ci, "context") or not self._ci.context:
            return prev_blueprints

        start_ep = 1 if window is None else max(1, current_ep - window)

        for ep in range(start_ep, current_ep):
            try:
                bp = self._ci.context.get_blueprint(ep)
                if bp and isinstance(bp, dict):
                    prev_blueprints.append(
                        {
                            "ep_num": ep,
                            "integrated_scenario": bp.get("integrated_scenario", ""),
                            "scene_breakdown": bp.get("scene_breakdown", {}),
                        }
                    )
            except Exception as e:
                logging.warning(f"⚠️ [ContinuityInspector] 제{ep}화 블루프린트 조회 실패: {e}")

        return prev_blueprints

    def _generate_fix_instructions(self, violations: list[dict]) -> str:
        """위반 사항에 대한 수정 지시 생성"""
        instructions = []

        for v in violations:
            v_type = v.get("type", "")
            item = v.get("item_or_subject", "")
            prev_ep = v.get("prev_ep")

            if v_type == "duplicate_acquisition":
                instructions.append(
                    f"[중복 획득 수정] '{item}'은(는) 이미 제{prev_ep}화에서 획득했습니다. "
                    f"현재 에피소드에서는 '이미 소지 중'인 상태로 시작해야 합니다. "
                    f"다시 획득하는 장면을 삭제하고, 기존에 가지고 있던 것을 사용하는 것으로 수정하세요."
                )
            elif v_type == "premature_possession":
                instructions.append(
                    f"[미수여 소지 수정] '{item}'은(는) 아직 수여받지 않았습니다. "
                    f"해당 수여물을 소지/사용하는 묘사를 삭제하거나, "
                    f"먼저 수여받는 장면이 있는 에피소드 이후로 이동시키세요."
                )
            elif v_type == "state_discontinuity":
                instructions.append(
                    "[상태 불연속 수정] 캐릭터 상태가 급격히 변화했습니다. "
                    "변화에 대한 서사적 근거를 추가하거나, 이전 상태를 유지하세요."
                )

        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."
