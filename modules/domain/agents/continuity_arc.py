"""
[V64.P3] ContinuityArcValidator — Arc 수준 연속성 검증 전담 모듈

ContinuityInspector God Object 분해의 첫 번째 모듈.
Stage 2에서 Arc 설계 후 Arc 간 + 단일 Arc 내 모순 검증을 담당.
inspector reference를 통해 BaseAgent 메서드(ask, _extract_json_robust 등)
및 공유 유틸리티(패턴, _is_same_item 등) 접근.
"""

import json
import logging
import re

# =================================================================
# [V49 NEW] Arc 수준 연속성 검증 프롬프트
# =================================================================
ARC_CONTINUITY_INSPECTION_PROMPT = """
[Role] Arc 수준 연속성 검증 전문가 (Arc Continuity Inspector)
[Task] 현재 Arc의 전술 설계가 이전 Arc들과 논리적으로 연결되는지, 그리고 단일 Arc 내에서 모순이 없는지 정밀 검증

### 📋 검증 대상: Arc {current_arc_no}
- 설정 화수: {ep_count}화 (제 {ep_start}화 ~ 제 {ep_end}화)
- 전술 설계서:
{tactical_doc}

- Joint Docs (Arc 종료 시점 상태):
{joint_docs}

- Status Shadow (예상 손실):
{status_shadow}

### 📜 이전 Arc 타임라인 (Arc 1 ~ Arc {prev_arc_count})
{prev_arcs_summary}

### 🎯 핵심 검증 항목

#### 1. Arc 간 아이템/무기 연속성 (Cross-Arc Item Timeline)
- 이전 Arc들에서 획득한 아이템이 현재 Arc에서 중복 획득되지 않는가?
- 이전 Arc의 joint_docs.physical_inventory에 명시된 아이템이 현재 Arc에서 연속적으로 소지되는가?
- 현재 Arc에서 새로 획득하려는 아이템이 이전에 이미 획득한 것과 동일하지 않은가?

#### 2. Arc 간 수여물/위상 연속성 (Cross-Arc Grant Timeline)
- 이전 Arc에서 수여받은 권한/패/직위가 현재 Arc에서 유지되는가?
- 이전 Arc에서 "복권"이나 "인정"을 받았다면, 현재 Arc에서 여전히 무시당하는 설정이 있는가?
- 정보 전파 시간을 고려해도 모순인 반응이 있는가?

#### 3. Arc 간 상태 연속성 (Cross-Arc State Timeline)
- 이전 Arc의 status_shadow(부상, 내공 소모)가 현재 Arc 도입부에 반영되는가?
- 부상 상태에서 갑자기 완전 회복된 것처럼 행동하지 않는가?
- 경지/무공 수준이 급격히 변화하지 않았는가?

#### 4. 단일 Arc 내 모순 (Intra-Arc Consistency) [V49 신규]
- 현재 Arc의 tactical_doc 내에서 앞뒤 화 사이에 모순이 없는가?
- 예: 제N화에서 획득한 아이템을 제N+2화에서 다시 획득하러 가는 설정
- 예: 제N화에서 부상을 입었는데 제N+1화에서 멀쩡하게 전투하는 설정
- 예: 제N화에서 설정된 무기 두께/특성이 제N+3화에서 모순되는 설정

#### 5. 설정 일관성 (Setting Consistency) [V49 신규]
- 아이템/무기의 물리적 특성(무게, 두께, 재질)이 Arc 내에서 일관되는가?
- 인물의 호칭/별호가 일관되게 사용되는가?
- 장소 이동이 물리적으로 가능한가?

### 🚨 판정 기준
- CRITICAL: 명백한 타임라인 오류 (중복 획득, 수여 전 소지) → 즉시 REJECT
- MAJOR: 심각한 연속성 오류 (상태 급변, 설정 충돌) → REJECT
- MINOR: 경미한 불일치 (반응 속도, 정보 전파) → WARNING으로 PASS 가능
- NONE: 연속성 문제 없음 → PASS

### [Chain-of-Thought Analysis]
다음 순서로 분석하십시오:

Step 1: 아이템/무기 타임라인 검증
- 이전 Arc들의 joint_docs에서 획득/소지 아이템 목록 추출
- 현재 Arc의 tactical_doc에서 획득하려는 아이템 추출
- 중복 획득 여부 판정

Step 2: 수여물/위상 타임라인 검증
- 이전 Arc들에서 수여/인정받은 것들 목록
- 현재 Arc에서의 NPC 반응이 일관적인지 확인
- 타임라인 모순 여부 판정

Step 3: 상태 연속성 검증
- 직전 Arc의 status_shadow 확인
- 현재 Arc 도입부의 상태 확인
- 급격한 변화 여부 판정

Step 4: 단일 Arc 내 모순 검증
- 현재 Arc의 각 화별 설정 추출
- 화 사이의 인과적 연결 확인
- 내부 모순 여부 판정

Step 5: 설정 일관성 검증
- 무기/아이템의 물리적 특성 일관성
- 인물 호칭/별호 일관성
- 장소 이동의 물리적 타당성

Step 6: [V61 NEW] Entity 명칭 일관성 검증
- Entity Registry가 제공된 경우, 등록된 정식 명칭과 현재 Arc의 명칭 비교
- 캐릭터: 이전 Arc에서 '팽무진'으로 확립되었는데 현재 '무진' 또는 '주인공'으로 표기되면 WARNING
- 조직/문파: '철혈문' vs '철혈파' 같은 미묘한 명칭 차이 탐지
- 장소: '무기고' vs '병기고' 같은 동일 장소의 다른 명칭 탐지
- 물품: '백근도' vs '거구도' 같은 동일 무기의 다른 명칭 탐지
- 기술/무공: '이화접목' vs '중검무봉' 같은 기술명 불일치 탐지
- Entity Registry:
{entity_registry}

Step 7: 최종 판정
- 위 6단계를 종합하여 PASS/REJECT 결정
- 위반 사항 목록 작성
- 수정 지시 작성

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "cross_arc_analysis": {{
        "items_acquired_before": ["이전 Arc들에서 획득한 아이템"],
        "items_in_current_arc": ["현재 Arc에서 획득/사용하려는 아이템"],
        "grants_received_before": ["이전 Arc들에서 수여받은 것들"],
        "status_from_prev_arc": "직전 Arc 종료 시 상태"
    }},
    "intra_arc_analysis": {{
        "internal_timeline": ["Arc 내 각 화별 핵심 사건"],
        "internal_contradictions": ["Arc 내부에서 발견된 모순"]
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
            "type": "duplicate_acquisition | premature_possession | state_discontinuity | intra_arc_contradiction | setting_inconsistency | entity_name_mismatch",
            "severity": "CRITICAL | MAJOR | MINOR",
            "item_or_subject": "문제 대상",
            "prev_arc": "이전 발생 Arc 번호 (Arc 간 모순인 경우)",
            "prev_ep": "이전 발생 화수 (Arc 내 모순인 경우)",
            "curr_ep": "현재 문제 화수",
            "description": "모순 설명",
            "evidence_prev": "이전 근거 텍스트",
            "evidence_curr": "현재 근거 텍스트"
        }}
    ],
    "warnings": ["MINOR 수준의 경고 목록"],
    "fix_instructions": "수정 지시 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""


# =================================================================
# [V49.2 NEW] Joint Docs 정밀 추출 프롬프트
# =================================================================
JOINT_DOCS_EXTRACTION_PROMPT = """
[Role] Arc 종료 상태 추출기 (Joint Docs Extractor)
[Task] Arc의 마지막 화(제 {last_ep}화) 내용을 분석하여 정확한 종료 상태를 추출하라.

### 📋 Arc {arc_no} 전술 설계서 (마지막 화 중심)
{last_ep_content}

### 🎯 추출 항목

#### 1. final_location (종료 시점 위치)
- 마지막 화가 끝나는 시점에 주인공이 위치한 **구체적인 장소**
- 예: "팽가 연무장", "무기고 앞", "가주 집무실"
- 단순히 "팽가"가 아닌 **세부 장소**까지 명시

#### 2. physical_inventory (물리적 소지품) [⚠️ 매우 중요]
- 마지막 화 종료 시점에 주인공이 **소지 중인 모든 핵심 물품**
- **🚨 핵심 원칙**: 무기, 패, 문서 등은 **명시적으로 버리거나 잃어버리지 않는 한 계속 소지 중**
- 예: 주인공이 제5화에서 "백근 대도"를 획득했고, 제8화까지 버린 언급이 없다면 → "백근 대도"는 여전히 소지 중
- 예시 목록: ["백근 대도", "철혈사자패", "비급서", "양피지 문서"]
- 소모품(영약 등)만 소모 처리, **무기/패/문서는 버리지 않으면 항상 포함**
- ❌ 빈 배열 `[]` 반환 금지 - 최소한 주무기와 핵심 아이템은 항상 포함

#### 3. world_joint (환경적 변화)
- 이 Arc가 끝나면서 **다음 Arc가 즉시 계승해야 할** 세계 상태
- 예: "팽가의 권력 구도가 뒤집힘", "청사가 가문 감옥에 수감됨"

### 🚨 추출 원칙
1. 추론하지 말고 **문서에 명시된 내용만** 추출하라
2. 획득 vs 소지 구분: 새로 획득한 것만이 아닌, 현재 소지 중인 모든 핵심 아이템
3. 마지막 화의 "(4) 연속성 체크포인트" 섹션이 있다면 우선 참조

[Output Format] JSON Only
{{
    "final_location": "종료 시점의 구체적 장소",
    "physical_inventory": ["소지품 1", "소지품 2", ...],
    "world_joint": "다음 Arc가 계승할 환경 변화",
    "extraction_confidence": "HIGH | MEDIUM | LOW",
    "extraction_notes": "추출 시 참고한 문서 내 근거 (선택)"
}}
"""


class ContinuityArcValidator:
    """
    [V64.P3] ContinuityInspector에서 분리된 Arc 수준 연속성 검증 모듈

    담당:
    - inspect_arc(): Stage 2에서 Arc 설계 후 호출 (메인 공개 API)
    - _inspect_intra_arc_only(): Arc 1 전용 내부 모순 검증
    - _extract_accurate_joint_docs(): Joint Docs 자동 추출/교정
    - _arc_python_precheck(): Python 기반 사전 정보 수집
    - _check_intra_arc_consistency(): 단일 Arc 내 모순 검증
    - _format_prev_arcs(): 이전 Arc들 포맷팅
    """

    def __init__(self, inspector) -> None:
        """
        Args:
            inspector: ContinuityInspector 인스턴스 (BaseAgent 상속, 공유 상태 접근용)
        """
        self._ci = inspector

    def inspect_arc(self, current_arc: dict, prev_arcs: list[dict], entity_registry: dict = None) -> dict:
        """
        [V49] Arc 수준 연속성 검증 실행

        Stage 2에서 Analyst가 Arc 설계 후, Director 검증 전에 호출

        Args:
            current_arc: 현재 Arc dict {arc_no, tactical_doc, joint_docs, status_shadow, ep_start, ep_end, ...}
            prev_arcs: 이전 Arc 리스트 [{arc_no, tactical_doc, joint_docs, ...}, ...]
            entity_registry: [V61] Entity Registry dict

        Returns:
            {decision, severity, violations, warnings, fix_instructions, entity_consistency}
        """
        arc_no = current_arc.get("arc_no", 0)

        # Arc 1은 이전 Arc가 없으므로 단일 Arc 내 모순만 검증
        if arc_no <= 1 or not prev_arcs:
            return self._inspect_intra_arc_only(current_arc)

        # 현재 Arc 데이터 추출
        tactical_doc = current_arc.get("tactical_doc", "")
        joint_docs = current_arc.get("joint_docs", {})
        status_shadow = current_arc.get("status_shadow", {})
        ep_start = current_arc.get("ep_start", 1)
        # [V60.73] ep_count 우선 참조
        ep_count = current_arc.get("ep_count", 5)
        ep_end = current_arc.get("ep_end", ep_start + ep_count - 1)

        if not tactical_doc:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "cross_arc_analysis": {},
                "intra_arc_analysis": {},
                "violations": [
                    {
                        "type": "missing_tactical_doc",
                        "severity": "CRITICAL",
                        "description": "Arc에 tactical_doc이 없습니다.",
                    }
                ],
                "warnings": [],
                "fix_instructions": "tactical_doc을 포함한 완전한 Arc를 설계하십시오.",
            }

        # ═══════════════════════════════════════════════════════════════
        # Phase 1: Python 기반 사전 정보 수집 (Advisory Only)
        # [V60.56] Python은 REJECT 권한 없음, 정보만 수집하여 LLM에게 전달
        # ═══════════════════════════════════════════════════════════════
        python_check = self._arc_python_precheck(current_arc, prev_arcs)

        # [V60.56] Python 검사 결과를 advisory로 변환
        python_advisory = python_check.get("critical_violations", [])
        if python_advisory:
            logging.info(f"📋 [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")
            for adv in python_advisory[:3]:
                logging.info(
                    f"- [{adv.get('type', '?')}] {adv.get('item_or_subject', adv.get('description', '?'))[:50]}"
                )

        # ═══════════════════════════════════════════════════════════════
        # Phase 1.5: Joint Docs Auto-Correction [V49.2 NEW]
        # ═══════════════════════════════════════════════════════════════
        corrected_joint_docs = self._extract_accurate_joint_docs(
            tactical_doc=tactical_doc, arc_no=arc_no, ep_end=ep_end, original_joint_docs=joint_docs
        )

        joint_docs_corrected = False
        if corrected_joint_docs and corrected_joint_docs != joint_docs:
            joint_docs = corrected_joint_docs
            joint_docs_corrected = True
            logging.info("🔧 [V49.2] Joint Docs 자동 수정 완료")

        # ═══════════════════════════════════════════════════════════════
        # Phase 1.6: Arc Start State Auto-Correction [V60.13 NEW]
        # ═══════════════════════════════════════════════════════════════
        start_state_corrected = False
        if prev_arcs:
            last_arc = prev_arcs[-1]
            prev_state = last_arc.get("state_constraints", {})
            prev_end = prev_state.get("arc_end_state", {})
            prev_joint = last_arc.get("joint_docs", {})
            prev_shadow = last_arc.get("status_shadow", {})

            correct_energy = prev_end.get("internal_energy")
            if correct_energy is None:
                loss_str = prev_shadow.get("internal_energy_loss", "0%")
                try:
                    loss = int(re.search(r"(\d+)", str(loss_str)).group(1))
                    correct_energy = max(0, 100 - loss)
                except (ValueError, AttributeError, TypeError):  # [V64.P4] energy parse failure
                    logging.warning(f"⚠️ [V60.73] internal_energy_loss 파싱 실패: '{loss_str}' → 50% 가정")
                    correct_energy = 50

            correct_injuries = prev_end.get("injuries") or prev_shadow.get("expected_injuries", "없음")
            correct_location = prev_end.get("location") or prev_joint.get("final_location", "알 수 없음")
            correct_equipment = prev_end.get("equipment") or prev_joint.get("physical_inventory", [])

            curr_state = current_arc.get("state_constraints", {})
            curr_start = curr_state.get("arc_start_state", {})

            needs_correction = (
                curr_start.get("internal_energy") != correct_energy
                or curr_start.get("injuries") != correct_injuries
                or curr_start.get("location") != correct_location
            )

            if needs_correction:
                corrected_start = {
                    "internal_energy": correct_energy,
                    "injuries": correct_injuries,
                    "location": correct_location,
                    "equipment": correct_equipment,
                }
                curr_state["arc_start_state"] = corrected_start
                current_arc["state_constraints"] = curr_state
                start_state_corrected = True
                logging.info(
                    f"🔧 [V60.13] Arc Start State 자동 수정 완료 (내공: {correct_energy}%, 부상: {correct_injuries})"
                )

        # ═══════════════════════════════════════════════════════════════
        # Phase 2: LLM 기반 정밀 검증
        # ═══════════════════════════════════════════════════════════════

        prev_arcs_summary = self._format_prev_arcs(prev_arcs)
        entity_registry_str = self._ci._format_entity_registry(entity_registry)

        prompt = ARC_CONTINUITY_INSPECTION_PROMPT.format(
            current_arc_no=arc_no,
            ep_count=ep_count,
            ep_start=ep_start,
            ep_end=ep_end,
            tactical_doc=self._ci._escape_braces(tactical_doc[:6000]),
            joint_docs=self._ci._escape_braces(json.dumps(joint_docs, ensure_ascii=False)),
            status_shadow=self._ci._escape_braces(json.dumps(status_shadow, ensure_ascii=False)),
            prev_arc_count=len(prev_arcs),
            prev_arcs_summary=self._ci._escape_braces(prev_arcs_summary),
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

            # [V70] critical_violations도 warnings로 병합 (Python은 REJECT 권한 없음, advisory만)
            if python_check.get("critical_violations"):
                result.setdefault("warnings", [])
                for _cv in python_check["critical_violations"]:
                    _cv_desc = (
                        _cv.get("description", _cv.get("item_or_subject", "알 수 없음"))
                        if isinstance(_cv, dict)
                        else str(_cv)
                    )
                    result["warnings"].append(f"[Python advisory] {_cv_desc}")

            # [V49.2] Joint Docs 자동 수정 정보 포함
            if joint_docs_corrected:
                result["corrected_joint_docs"] = joint_docs
                result.setdefault("warnings", [])
                if "[V49.2]" not in str(result.get("warnings", [])):
                    result["warnings"].append("[V49.2] joint_docs가 tactical_doc 기반으로 자동 수정됨")

            # [V60.13] Arc Start State 자동 수정 정보 포함
            if start_state_corrected:
                result["corrected_state_constraints"] = current_arc.get("state_constraints", {})
                result.setdefault("warnings", [])
                if "[V60.13]" not in str(result.get("warnings", [])):
                    result["warnings"].append(
                        "[V60.13] arc_start_state가 이전 Arc의 arc_end_state 기반으로 자동 수정됨"
                    )

            # [V60.13] intra_arc_contradiction은 WARNING으로 완화
            violations = result.get("violations", [])
            if not isinstance(violations, list):
                violations = []
            has_critical_cross_arc = any(
                v.get("type") in ["duplicate_acquisition", "premature_possession", "state_discontinuity"]
                and v.get("severity") in ["CRITICAL", "MAJOR"]
                for v in violations
                if isinstance(v, dict)
            )

            if result.get("decision") == "REJECT" and not has_critical_cross_arc:
                intra_only = violations and all(
                    isinstance(v, dict) and v.get("type") in ["intra_arc_contradiction", "setting_inconsistency"]
                    for v in violations
                )
                if intra_only and start_state_corrected:
                    result["decision"] = "PASS"
                    result["severity"] = "MINOR"
                    result.setdefault("warnings", [])
                    for v in violations:
                        if not isinstance(v, dict):
                            continue
                        result["warnings"].append(f"[완화됨] {v.get('type')}: {v.get('description', '')[:100]}")
                    result["violations"] = []
                    logging.warning("⚠️ [V60.13] intra-arc 오류 완화 → PASS (cross-arc 정상)")

            return result

        except Exception as e:
            logging.warning(f"🚨 [ContinuityInspector] Arc LLM 검증 실패: {e}")
            if python_check.get("warnings"):
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "cross_arc_analysis": python_check.get("cross_arc_timeline", {}),
                    "intra_arc_analysis": python_check.get("intra_arc_analysis", {}),
                    "violations": [],
                    "warnings": python_check["warnings"] + ["LLM 검증 실패 - 수동 확인 권장"],
                    "fix_instructions": "",
                }
            return {
                "decision": "PASS",
                "severity": "NONE",
                "violations": [],
                "warnings": ["Arc LLM 검증 실패 - 수동 확인 권장"],
                "fix_instructions": "",
            }

    def _inspect_intra_arc_only(self, current_arc: dict) -> dict:
        """[V49] Arc 1 또는 이전 Arc 없을 때 단일 Arc 내 모순만 검증"""
        arc_no = current_arc.get("arc_no", 1)
        tactical_doc = current_arc.get("tactical_doc", "")

        if not tactical_doc:
            return {
                "decision": "REJECT",
                "severity": "CRITICAL",
                "violations": [
                    {
                        "type": "missing_tactical_doc",
                        "severity": "CRITICAL",
                        "description": "Arc에 tactical_doc이 없습니다.",
                    }
                ],
                "warnings": [],
                "fix_instructions": "tactical_doc을 포함한 완전한 Arc를 설계하십시오.",
            }

        intra_violations = self._check_intra_arc_consistency(current_arc)

        if intra_violations:
            critical = [v for v in intra_violations if v.get("severity") == "CRITICAL"]
            if critical:
                return {
                    "decision": "REJECT",
                    "severity": "CRITICAL",
                    "intra_arc_analysis": {"internal_contradictions": intra_violations},
                    "violations": intra_violations,
                    "warnings": [],
                    "fix_instructions": self._generate_arc_fix_instructions(intra_violations),
                }
            else:
                return {
                    "decision": "PASS",
                    "severity": "MINOR",
                    "intra_arc_analysis": {"internal_contradictions": intra_violations},
                    "violations": [],
                    "warnings": [v.get("description", "") for v in intra_violations],
                    "fix_instructions": "",
                }

        return {"decision": "PASS", "severity": "NONE", "violations": [], "warnings": [], "fix_instructions": ""}

    # =================================================================
    # [V49.2 NEW] Joint Docs 자동 추출 메서드
    # =================================================================

    def _extract_accurate_joint_docs(
        self, tactical_doc: str, arc_no: int, ep_end: int, original_joint_docs: dict
    ) -> dict | None:
        """[V49.2] tactical_doc의 마지막 화 내용에서 정확한 joint_docs를 추출"""
        if not tactical_doc:
            return None

        last_ep_content = self._extract_last_episode_content(tactical_doc, ep_end)

        if not last_ep_content or len(last_ep_content) < 100:
            return original_joint_docs

        prompt = JOINT_DOCS_EXTRACTION_PROMPT.format(
            arc_no=arc_no, last_ep=ep_end, last_ep_content=self._ci._escape_braces(last_ep_content[:4000])
        )

        try:
            response = self._ci.ask(prompt, temperature=0.1)
            extracted = self._ci._extract_json_robust(response)

            if not isinstance(extracted, dict):
                return original_joint_docs

            if not extracted.get("final_location") and not extracted.get("physical_inventory"):
                return original_joint_docs

            confidence = extracted.get("extraction_confidence", "LOW")
            if confidence == "LOW":
                merged = original_joint_docs.copy() if isinstance(original_joint_docs, dict) else {}
                if extracted.get("final_location"):
                    merged["final_location"] = extracted["final_location"]
                if extracted.get("physical_inventory"):
                    merged["physical_inventory"] = extracted["physical_inventory"]
                if extracted.get("world_joint"):
                    merged["world_joint"] = extracted["world_joint"]
                return merged

            return {
                "final_location": extracted.get("final_location", ""),
                "physical_inventory": extracted.get("physical_inventory", []),
                "world_joint": extracted.get("world_joint", ""),
            }

        except Exception as e:
            logging.warning(f"⚠️ [V49.2] Joint Docs 추출 실패: {e}")
            return original_joint_docs

    def _extract_last_episode_content(self, tactical_doc: str, ep_end: int) -> str:
        """[V49.2] tactical_doc에서 마지막 화 내용만 추출"""
        patterns = [
            rf"\[제\s*{ep_end}화\s*전술\s*설계\]",
            rf"제\s*{ep_end}화[:\s]",
            rf"\[제{ep_end}화\]",
            rf"Beat\s*{ep_end}:",
        ]

        last_ep_start = -1
        for pattern in patterns:
            match = re.search(pattern, tactical_doc)
            if match:
                last_ep_start = match.start()
                break

        if last_ep_start < 0:
            cutoff = int(len(tactical_doc) * 0.7)
            return tactical_doc[cutoff:]

        return tactical_doc[last_ep_start:]

    def _arc_python_precheck(self, current_arc: dict, prev_arcs: list[dict]) -> dict:
        """[V49] Arc 수준 Python 기반 사전 검증"""
        critical_violations = []
        warnings = []

        current_arc_no = current_arc.get("arc_no", 0)
        tactical_doc = current_arc.get("tactical_doc", "")
        joint_docs = current_arc.get("joint_docs", {})

        # 이전 Arc들에서 획득한 아이템/수여물 추적
        acquired_items = {}
        granted_items = {}
        prev_inventory = {}
        prev_status = {}

        for arc in prev_arcs:
            arc_no = arc.get("arc_no", 0)
            arc_tactical = arc.get("tactical_doc", "")
            arc_joint = arc.get("joint_docs", {})
            arc_status = arc.get("status_shadow", {})
            arc_state_constraints = arc.get("state_constraints", {})

            # [V49.6] protagonist_items 우선 사용
            items_from_constraints = arc_state_constraints.get("protagonist_items", [])
            if not items_from_constraints:
                items_from_constraints = arc_state_constraints.get("items_acquired", [])

            if isinstance(items_from_constraints, list):
                filtered_items = self._ci._filter_distributed_items(
                    [i for i in items_from_constraints if i and isinstance(i, str) and 2 <= len(i) <= 30], arc_tactical
                )
                for item in filtered_items:
                    acquired_items[item] = arc_no
                    logging.info(f"📝 [V60.54 DEBUG] Arc {arc_no} 획득 기록: '{item}'")

            if not items_from_constraints:
                logging.info(f"⚠️ [V60.54 DEBUG] Arc {arc_no} state_constraints에 획득 아이템 없음")
                pass

            for pattern in self._ci.grant_patterns:
                matches = re.findall(pattern, arc_tactical)
                for item in matches:
                    item = item.strip()
                    if item and 2 <= len(item) <= 30:
                        granted_items[item] = arc_no

            inventory = arc_joint.get("physical_inventory", "")
            if isinstance(inventory, list):
                filtered_inv = self._ci._filter_distributed_items(
                    [i for i in inventory if i and isinstance(i, str) and 2 <= len(i) <= 30], arc_tactical
                )
                for item in filtered_inv:
                    acquired_items[item] = arc_no
            elif isinstance(inventory, str) and inventory:
                raw_inv = []
                for pattern in self._ci.acquire_patterns:
                    matches = re.findall(pattern, inventory)
                    for item in matches:
                        item = item.strip()
                        if item and 2 <= len(item) <= 30:
                            raw_inv.append(item)
                for item in self._ci._filter_distributed_items(raw_inv, arc_tactical):
                    acquired_items[item] = arc_no

            prev_inventory = arc_joint
            prev_status = arc_status

        # 현재 Arc에서 획득하려는 아이템 검색
        current_acquisitions = []
        current_state_constraints = current_arc.get("state_constraints", {})

        items_from_current = current_state_constraints.get("protagonist_items", [])
        if not items_from_current:
            items_from_current = current_state_constraints.get("items_acquired", [])

        if items_from_current:
            logging.info(f"📥 [V60.54 DEBUG] state_constraints 획득 아이템: {items_from_current}")

        if isinstance(items_from_current, list):
            for item in items_from_current:
                if item and isinstance(item, str) and 2 <= len(item) <= 30:
                    current_acquisitions.append(item)

        if not current_acquisitions:
            logging.info("⚠️ [V60.54 DEBUG] state_constraints에 획득 아이템 없음 - 패턴 검색 스킵")
            pass

        # ═══════════════════════════════════════════════════════════════
        # [V60.50] 이미 소지 중인 아이템은 중복 검사에서 제외
        # ═══════════════════════════════════════════════════════════════
        prev_inventory_items = []
        if isinstance(prev_inventory, dict):
            inv_list = prev_inventory.get("physical_inventory", [])
            if isinstance(inv_list, list):
                prev_inventory_items = [str(i) for i in inv_list if i]
            elif isinstance(inv_list, str) and inv_list:
                prev_inventory_items = [inv_list]

        current_joint = current_arc.get("joint_docs", {})
        current_inventory_items = []
        if isinstance(current_joint, dict):
            curr_inv = current_joint.get("physical_inventory", [])
            if isinstance(curr_inv, list):
                current_inventory_items = [str(i) for i in curr_inv if i]
            elif isinstance(curr_inv, str) and curr_inv:
                current_inventory_items = [curr_inv]

        # [V60.53] 사용 패턴 필터링
        usage_items = set()
        for pattern in self._ci.usage_patterns:
            matches = re.findall(pattern, tactical_doc)
            for item in matches:
                item = item.strip() if isinstance(item, str) else str(item)
                if item and 2 <= len(item) <= 30:
                    usage_items.add(item)

        if usage_items:
            logging.info(f"📦 [V60.54 DEBUG] 사용 패턴 감지: {list(usage_items)[:5]}")

        all_existing_items = prev_inventory_items + current_inventory_items + list(usage_items)

        logging.info(f"📦 [V60.54 DEBUG] Arc {current_arc_no} 중복 검사 시작")
        logging.info(f"- 현재 획득 후보: {current_acquisitions[:5] if current_acquisitions else '없음'}")
        logging.info(f"- 이전 소지품: {prev_inventory_items[:3] if prev_inventory_items else '없음'}")
        logging.info(f"- 현재 소지품: {current_inventory_items[:3] if current_inventory_items else '없음'}")
        logging.info(f"- 이전 Arc 획득 기록: {list(acquired_items.keys())[:5] if acquired_items else '없음'}")

        filtered_current_acquisitions = []
        for curr_item in current_acquisitions:
            is_already_owned = False
            for owned_item in all_existing_items:
                if self._ci._is_same_item(curr_item, owned_item):
                    logging.info(f"⏭️ 필터링: '{curr_item}' (이미 소지: '{owned_item}')")
                    is_already_owned = True
                    break
            if not is_already_owned:
                filtered_current_acquisitions.append(curr_item)

        current_acquisitions = filtered_current_acquisitions
        logging.info(f"- 필터링 후 획득 후보: {current_acquisitions if current_acquisitions else '없음'}")

        # 검증 1: 중복 획득
        for curr_item in current_acquisitions:
            for prev_item, prev_arc in acquired_items.items():
                is_same = self._ci._is_same_item(curr_item, prev_item)
                if is_same:
                    logging.warning("🚨 [V60.54] 중복 획득 감지!")
                    logging.info(f"- 현재 Arc: {current_arc_no}, 아이템: '{curr_item}'")
                    logging.info(f"- 이전 Arc: {prev_arc}, 아이템: '{prev_item}'")
                    critical_violations.append(
                        {
                            "type": "duplicate_acquisition",
                            "severity": "CRITICAL",
                            "item_or_subject": curr_item,
                            "prev_arc": prev_arc,
                            "description": f"'{prev_item}'은(는) 이미 Arc {prev_arc}에서 획득했습니다. "
                            f"Arc {current_arc_no}에서 다시 획득하려 합니다.",
                            "evidence_prev": f"Arc {prev_arc}에서 획득",
                            "evidence_curr": f"현재 Arc에서 '{curr_item}' 획득 시도",
                        }
                    )
                    break

        if not critical_violations:
            logging.info(f"✅ [V60.54] Arc {current_arc_no} 중복 획득 없음")

        # 검증 2: 단일 Arc 내 모순
        intra_violations = self._check_intra_arc_consistency(current_arc)
        for v in intra_violations:
            if v.get("severity") == "CRITICAL":
                critical_violations.append(v)
            else:
                warnings.append(v.get("description", ""))

        # 검증 3: 상태 연속성
        if prev_status:
            prev_injuries = prev_status.get("expected_injuries", "")
            if prev_injuries and prev_injuries not in ["없음", "경미", ""]:
                if "부상" not in tactical_doc and "회복" not in tactical_doc and "치료" not in tactical_doc:
                    warnings.append(
                        f"직전 Arc에서 '{prev_injuries}' 부상이 있었으나, 현재 Arc에서 부상/회복 관련 언급이 없습니다."
                    )

        cross_arc_timeline = {
            "items_acquired_before": list(acquired_items.keys()),
            "grants_received_before": list(granted_items.keys()),
            "items_in_current_arc": current_acquisitions,
            "prev_inventory": prev_inventory,
            "prev_status": prev_status,
        }

        intra_arc_analysis = {"internal_contradictions": [v.get("description", "") for v in intra_violations]}

        return {
            "critical_violations": critical_violations,
            "warnings": warnings,
            "cross_arc_timeline": cross_arc_timeline,
            "intra_arc_analysis": intra_arc_analysis,
        }

    def _check_intra_arc_consistency(self, arc: dict) -> list[dict]:
        """[V49] 단일 Arc 내 모순 검증"""
        violations = []
        tactical_doc = arc.get("tactical_doc", "")
        beat_sequence = arc.get("beat_sequence", [])
        ep_start = arc.get("ep_start", 1)

        if not tactical_doc:
            return violations

        ep_sections = {}
        section_pattern = r"\[제\s*(\d+)화[^\]]*\]"
        sections = re.split(section_pattern, tactical_doc)

        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    ep_num = int(sections[i])
                    ep_content = sections[i + 1]
                    ep_sections[ep_num] = ep_content

        arc_acquisitions = {}

        for ep_num, content in ep_sections.items():
            for pattern in self._ci.acquire_patterns:
                matches = re.findall(pattern, content)
                for item in matches:
                    item = item.strip()
                    if item and 2 <= len(item) <= 30:
                        if item in arc_acquisitions:
                            prev_ep = arc_acquisitions[item]
                            if ep_num != prev_ep:
                                violations.append(
                                    {
                                        "type": "intra_arc_contradiction",
                                        "severity": "CRITICAL",
                                        "item_or_subject": item,
                                        "prev_ep": prev_ep,
                                        "curr_ep": ep_num,
                                        "description": f"'{item}'을(를) 제{prev_ep}화에서 획득했는데, "
                                        f"제{ep_num}화에서 다시 획득하려 합니다. (Arc 내 모순)",
                                    }
                                )
                        else:
                            arc_acquisitions[item] = ep_num

        sorted_eps = sorted(ep_sections.keys())
        for i in range(len(sorted_eps) - 1):
            curr_ep = sorted_eps[i]
            next_ep = sorted_eps[i + 1]
            curr_content = ep_sections[curr_ep]
            next_content = ep_sections[next_ep]

            injury_pattern = r"(?:부상|상처|파열|골절|출혈|기절)"
            if re.search(injury_pattern, curr_content):
                action_pattern = r"(?:전투|격전|결투|비무|대결)"
                if re.search(action_pattern, next_content) and not re.search(r"(?:회복|치료|휴식)", next_content):
                    violations.append(
                        {
                            "type": "state_discontinuity",
                            "severity": "MINOR",
                            "item_or_subject": "부상 상태",
                            "prev_ep": curr_ep,
                            "curr_ep": next_ep,
                            "description": f"제{curr_ep}화에서 부상이 발생했으나, "
                            f"제{next_ep}화에서 회복 없이 격렬한 활동이 설정됨 (경고)",
                        }
                    )

            # [V49.2] 복장 일관성 검증
            curr_attire_fancy = re.search(r"(?:비단|명주|화려한)\s*(?:옷|의|포|복|차림)", curr_content)
            curr_attire_plain = re.search(r"(?:허름한|낡은|무명|삼베)\s*(?:옷|의|포|복|차림)", curr_content)
            next_attire_fancy = re.search(r"(?:비단|명주|화려한)\s*(?:옷|의|포|복|차림)", next_content)
            next_attire_plain = re.search(r"(?:허름한|낡은|무명|삼베)\s*(?:옷|의|포|복|차림)", next_content)

            attire_change_pattern = r"(?:옷|의복|복장|차림)(?:을|를)\s*(?:갈아입|바꾸|벗)"
            has_change_scene = re.search(attire_change_pattern, next_content)

            if curr_attire_fancy and next_attire_plain and not has_change_scene:
                violations.append(
                    {
                        "type": "setting_inconsistency",
                        "severity": "MAJOR",
                        "item_or_subject": "복장",
                        "prev_ep": curr_ep,
                        "curr_ep": next_ep,
                        "description": f"제{curr_ep}화에서 '화려한/비단 복장'이었으나, "
                        f"제{next_ep}화에서 복장 변경 장면 없이 '허름한 복장'으로 설정됨",
                    }
                )
            elif curr_attire_plain and next_attire_fancy and not has_change_scene:
                violations.append(
                    {
                        "type": "setting_inconsistency",
                        "severity": "MINOR",
                        "item_or_subject": "복장",
                        "prev_ep": curr_ep,
                        "curr_ep": next_ep,
                        "description": f"제{curr_ep}화에서 '허름한 복장'이었으나, "
                        f"제{next_ep}화에서 복장 변경 장면 없이 '화려한 복장'으로 설정됨 (경고)",
                    }
                )

        return violations

    def _format_prev_arcs(self, prev_arcs: list[dict]) -> str:
        """[V49] 이전 Arc들을 LLM용 타임라인 형식으로 변환"""
        summaries = []

        all_acquisitions = []
        all_grants = []

        for arc in prev_arcs:
            arc_no = arc.get("arc_no", "?")
            tactical_doc = arc.get("tactical_doc", "")
            joint_docs = arc.get("joint_docs", {})
            status_shadow = arc.get("status_shadow", {})
            state_constraints = arc.get("state_constraints", {})
            arc_end_state = state_constraints.get("arc_end_state", {})
            ep_start = arc.get("ep_start", "?")
            ep_end = arc.get("ep_end", "?")

            items = self._ci._extract_acquisitions(tactical_doc)
            grants = self._ci._extract_grants(tactical_doc)

            for item in items:
                all_acquisitions.append((arc_no, item))
            for grant in grants:
                all_grants.append((arc_no, grant))

            final_internal_energy = arc_end_state.get("internal_energy", status_shadow.get("internal_energy_loss", "?"))
            final_injuries = arc_end_state.get("injuries", status_shadow.get("expected_injuries", "없음"))
            final_location = arc_end_state.get("location", joint_docs.get("final_location", "미정"))
            final_equipment = arc_end_state.get("equipment", joint_docs.get("physical_inventory", []))

            summary = f"""
═══ Arc {arc_no} (제 {ep_start}화 ~ 제 {ep_end}화) ═══
[🔴 정확한 종료 상태 (state_constraints.arc_end_state) - 다음 Arc 시작점]
- 최종 내공: {final_internal_energy}% ← 다음 Arc는 이 값으로 시작해야 함
- 최종 부상: {final_injuries}
- 최종 위치: {final_location}
- 최종 소지품: {final_equipment}

[참고: joint_docs]
- 위치: {joint_docs.get("final_location", "미정")}
- 소지품: {joint_docs.get("physical_inventory", "미정")}
- 세계 변화: {joint_docs.get("world_joint", "미정")}

[참고: status_shadow]
- 내공 소모: {status_shadow.get("internal_energy_loss", "0%")}
- 예상 부상: {status_shadow.get("expected_injuries", "없음")}

[획득 아이템] {", ".join(items) if items else "없음"}
[수여물] {", ".join(grants) if grants else "없음"}

[핵심 전술 요약]
{tactical_doc[:1500] if tactical_doc else "없음"}...
"""
            summaries.append(summary)

        timeline_header = f"""
╔══════════════════════════════════════════════════════════════╗
║  전체 아이템/수여물 타임라인 (Arc 1 ~ Arc {len(prev_arcs)})  ║
╚══════════════════════════════════════════════════════════════╝

[📦 획득 아이템 타임라인]
{self._format_arc_timeline(all_acquisitions) if all_acquisitions else "- 없음"}

[🎖️ 수여물 타임라인]
{self._format_arc_timeline(all_grants) if all_grants else "- 없음"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        return timeline_header + "\n".join(summaries)

    def _format_arc_timeline(self, items: list[tuple]) -> str:
        """Arc 타임라인 항목을 포맷팅"""
        lines = []
        for arc_no, item in items:
            lines.append(f"- Arc {arc_no}: {item}")
        return "\n".join(lines)

    def _generate_arc_fix_instructions(self, violations: list[dict]) -> str:
        """Arc 위반 사항에 대한 수정 지시 생성"""
        instructions = []

        for v in violations:
            v_type = v.get("type", "")
            item = v.get("item_or_subject", "")
            prev_arc = v.get("prev_arc")
            prev_ep = v.get("prev_ep")
            curr_ep = v.get("curr_ep")

            if v_type == "duplicate_acquisition":
                if prev_arc:
                    instructions.append(
                        f"[중복 획득 수정] '{item}'은(는) 이미 Arc {prev_arc}에서 획득했습니다. "
                        f"현재 Arc에서는 '이미 소지 중'인 상태로 시작해야 합니다. "
                        f"다시 획득하는 장면을 삭제하고, 기존에 가지고 있던 것을 사용하는 것으로 수정하세요."
                    )
                else:
                    instructions.append(
                        f"[중복 획득 수정] '{item}'은(는) 이미 제{prev_ep}화에서 획득했습니다. "
                        f"제{curr_ep}화에서 다시 획득하는 설정을 삭제하세요."
                    )
            elif v_type == "intra_arc_contradiction":
                instructions.append(
                    f"[Arc 내 모순 수정] '{item}'이(가) 제{prev_ep}화와 제{curr_ep}화 사이에서 모순됩니다. "
                    f"해당 화차의 설정을 일관되게 수정하세요."
                )
            elif v_type == "state_discontinuity":
                instructions.append(
                    f"[상태 불연속 수정] 제{prev_ep}화에서 발생한 상태 변화가 "
                    f"제{curr_ep}화에서 반영되지 않았습니다. 회복/치료 장면을 추가하거나 "
                    f"상태에 맞는 행동으로 수정하세요."
                )
            elif v_type == "setting_inconsistency":
                instructions.append(
                    f"[설정 불일치 수정] '{item}'의 물리적 특성이 일관되지 않습니다. 설정을 통일하세요."
                )

        return "\n".join(instructions) if instructions else "위반 사항을 확인하고 수정하세요."
