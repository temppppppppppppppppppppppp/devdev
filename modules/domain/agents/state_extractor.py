"""
V61.0 State Extractor Agent
이전 Arc/Episode에서 핵심 상태 정보를 구조화하여 추출

Purpose:
- LLM이 무시하기 쉬운 문자열 컨텍스트를 구조화된 JSON으로 변환
- 다음 Arc 설계 시 명확한 제약으로 주입
- Flash 모델로 빠르고 저렴하게 실행
- [V61] Entity Registry 추출 - 고유명사 일관성 추적
"""

import json
import logging

from modules.core.prompt_loader import SafeDict

from .base_agent import BaseAgent

SATISFACTION_TAG_PROMPT = """
[Role] 독자 만족도 분석 전문가
[Task] 아래 원고를 읽고 독자 대리만족 관점에서 태그를 분류하라.

### [🚨 SYSTEM RESTRICTION: JSON ONLY]
1. 답변의 첫 글자는 반드시 {{, 마지막 글자는 반드시 }}
2. 설명, 인사말, 서문 절대 금지
3. 오직 유효한 JSON만 출력

### [원고 — 제{ep_num}화]
{manuscript}

### [분류 기준]
1. **primary_tag** (6개 중 택1):
   - "성취": 주인공이 승리·목표 달성·강자 제압·경지 돌파
   - "성장": 주인공의 능력·지위·관계가 눈에 띄게 향상
   - "전투": 전투/대결이 중심이나 승패 미확정 또는 고전
   - "이행": 다음 사건으로의 전환·이동·준비 구간
   - "일상": 수련·교류·휴식 등 일상 묘사 중심
   - "좌절": 주인공이 패배·손실·위기에 처함

2. **satisfaction_score** (1~10):
   독자가 이 에피소드에서 느낄 쾌감·성취감 예상치.
   - 1~3: 좌절·무력감 위주
   - 4~6: 보통 (일상/이행/고전)
   - 7~10: 쾌감·카타르시스 (성취/성장/대역전)

3. **protagonist_agency** (3개 중 택1):
   - "자력": 주인공이 자기 능력으로 해결 (60% 이상)
   - "협력": 동료와 함께 해결
   - "타인의존": 타인의 도움·구출에 의존

### [출력 형식]
{{
    "primary_tag": "성취|성장|전투|이행|일상|좌절",
    "satisfaction_score": 1-10,
    "protagonist_agency": "자력|협력|타인의존"
}}
"""

STATE_EXTRACTION_PROMPT = """
[Role] 서사 상태 추출 전문가 (State Extraction Specialist)
[Task] 아래 Arc 데이터에서 다음 Arc 설계에 필요한 핵심 상태 정보를 추출하라.

### [🚨 SYSTEM RESTRICTION: JSON ONLY]
1. 답변의 첫 글자는 반드시 {{, 마지막 글자는 반드시 }}
2. 설명, 인사말, 서문 절대 금지
3. 오직 유효한 JSON만 출력

### [Arc 데이터]
{arc_data}

### [추출 대상]
1. **부상 상태 (injuries)**
   - 현재 부상 목록과 심각도
   - 필요한 회복 기간 (일 단위)
   - 회복 조건 (운기조식, 치료 등)

2. **내공 상태 (internal_energy)**
   - 현재 내공 퍼센트
   - 소모된 내공
   - 회복에 필요한 시간

3. **소지품 (inventory)**
   - 현재 소지 중인 아이템 전체 목록
   - 이번 Arc에서 새로 획득한 아이템
   - 소모/파손된 아이템

4. **위치 (location)**
   - 현재 위치
   - 이동 경로 (있다면)

5. **신분/권한 (status)**
   - 획득한 패/직위/권한
   - 변화된 사회적 위상

6. **관계 변화 (relationships)**
   - 호감도 상승한 NPC
   - 적대 관계가 된 NPC
   - 사망/퇴장한 NPC

7. **절대 금지 목록 (forbidden)**
   - 이미 획득했으므로 다시 획득 불가한 아이템
   - 이미 해결했으므로 다시 등장 불가한 문제
   - 이미 수여받았으므로 다시 받을 수 없는 권한

8. **[V61] 고유명사 레지스트리 (entity_registry)**
   이번 Arc에서 등장한 모든 고유명사를 추출하라. 장르 무관 범용 카테고리 사용.

   - **character**: 인물 (NPC, 적, 동료, 조연 - 주인공 제외)
   - **organization**: 조직/집단 (문파, 길드, 회사, 산적단, 세력)
   - **location**: 장소 (지역, 던전, 건물, 영역)
   - **object**: 물건 (무기, 아이템, 도구, 신물) - inventory와 별개로 명칭 추적용
   - **concept**: 개념 (무공, 스킬, 깨달음, 경지, 비급, 기술명)

   각 항목에는 name, context(등장 맥락), arc_no를 포함하라.

### [Output Format - JSON Only]
{{
    "arc_no": {arc_no},
    "protagonist_state": {{
        "injuries": [
            {{"name": "부상명", "severity": "심각도", "recovery_days": 숫자, "recovery_method": "회복방법"}}
        ],
        "internal_energy": {{
            "current_percent": 숫자,
            "consumed_this_arc": 숫자,
            "recovery_needed_days": 숫자
        }},
        "location": {{
            "current": "현재 위치",
            "can_move_immediately": true/false,
            "movement_constraint": "이동 제약 사유"
        }}
    }},
    "inventory": {{
        "current_items": ["소지품 목록"],
        "acquired_this_arc": ["이번 Arc 획득 아이템"],
        "consumed_or_lost": ["소모/분실 아이템"]
    }},
    "status": {{
        "titles": ["직위/칭호"],
        "authorities": ["권한"],
        "social_standing": "사회적 위상 설명"
    }},
    "relationships": {{
        "improved": ["호감 상승 NPC"],
        "worsened": ["관계 악화 NPC"],
        "deceased": ["사망 NPC"]
    }},
    "forbidden_in_next_arc": {{
        "cannot_acquire_again": ["다시 획득 불가 아이템"],
        "cannot_receive_again": ["다시 수여받을 수 없는 것"],
        "resolved_problems": ["해결된 문제"]
    }},
    "next_arc_constraints": {{
        "must_start_with": "다음 Arc 도입부 필수 요소",
        "recovery_scene_required": true/false,
        "min_time_skip_days": 숫자,
        "mandatory_items_in_possession": ["반드시 소지해야 할 아이템"]
    }},
    "entity_registry": {{
        "characters": [
            {{"name": "인물명", "role": "역할(적/동료/조연 등)", "context": "등장 맥락"}}
        ],
        "organizations": [
            {{"name": "조직명", "type": "유형(문파/산적단/세력 등)", "context": "등장 맥락"}}
        ],
        "locations": [
            {{"name": "장소명", "type": "유형(지역/건물/영역 등)", "context": "등장 맥락"}}
        ],
        "objects": [
            {{"name": "물건명", "type": "유형(무기/도구/신물 등)", "context": "등장 맥락"}}
        ],
        "concepts": [
            {{"name": "개념명", "type": "유형(무공/깨달음/경지 등)", "context": "등장 맥락"}}
        ]
    }}
}}
"""


class StateExtractor(BaseAgent):
    """
    V60.10 상태 추출 에이전트

    이전 Arc의 종료 상태를 구조화된 JSON으로 추출하여
    다음 Arc 설계 시 명확한 제약으로 활용
    """

    def __init__(self, context, client, model_tier: str = None):
        """
        [V60.24] StateExtractor 초기화 - Gemini 3 Flash (추출용)

        Args:
            context: ProjectContext
            client: genai.Client
            model_tier: 사용할 모델 (V60.24: Flash로 변경 - 추출 작업)
        """
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent에서 자동 설정: gemini-3-flash → gemini-2.5-flash)
        # [V62.5] 상태 캐시: arc_no → extract_state 결과 (PASS된 Arc는 불변)
        self._state_cache: dict[int, dict] = {}

    def extract_state(self, arc_data: dict) -> dict:
        """
        단일 Arc에서 상태 추출

        Args:
            arc_data: Arc 데이터 (tactical_doc, joint_docs, status_shadow 포함)

        Returns:
            구조화된 상태 정보 dict
        """
        arc_no = arc_data.get("arc_no", "Unknown")

        # [V62.5] 캐시 히트 확인 - PASS된 Arc 데이터는 불변
        cache_key = arc_no if isinstance(arc_no, int) else hash(str(arc_no))
        if cache_key in self._state_cache:
            return self._state_cache[cache_key]

        # Arc 데이터 정리
        # [V60.13 FIX] state_constraints.arc_end_state 포함
        cleaned_data = {
            "arc_no": arc_no,
            "tactical_doc": (
                "\n".join(f"{k}: {v}" for k, v in (arc_data.get("tactical_doc") or {}).items())
                if isinstance(arc_data.get("tactical_doc"), dict)
                else (arc_data.get("tactical_doc") or "")
            )[:20000],  # Gemini 대용량 컨텍스트 활용
            "joint_docs": arc_data.get("joint_docs", {}),
            "status_shadow": arc_data.get("status_shadow", {}),
            "state_constraints": arc_data.get("state_constraints", {}),  # [V60.13] arc_end_state 포함
            "beat_sequence": arc_data.get("beat_sequence", []),
        }

        prompt = STATE_EXTRACTION_PROMPT.format_map(
            SafeDict(
                arc_data=self._escape_braces(json.dumps(cleaned_data, ensure_ascii=False, indent=2)),
                arc_no=arc_no,
            )
        )

        try:
            result = self.ask(prompt, temperature=0.2, thinking_level="low")

            if isinstance(result, str):
                result = self._extract_json_robust(result)  # [V70] bare json.loads → robust 파서

            # 필수 필드 검증
            result = self._validate_and_fix_result(result, arc_data)

            # [V62.5] 캐시 저장
            self._state_cache[cache_key] = result
            return result

        except Exception as e:
            logging.warning(f"[StateExtractor] LLM 추출 실패 (fallback 사용): {e}")
            # 실패 시 기본 추출 (Python 기반)
            result = self._fallback_extraction(arc_data)
            # [V62.5] 폴백 결과도 캐시 (재호출 시 LLM 재시도 방지)
            self._state_cache[cache_key] = result
            return result

    def invalidate_cache(self, arc_no=None):
        """캐시 무효화. arc_no 지정 시 해당 키만, None이면 전체."""
        if arc_no is not None:
            cache_key = arc_no if isinstance(arc_no, int) else hash(str(arc_no))
            self._state_cache.pop(cache_key, None)
        else:
            self._state_cache.clear()

    def extract_cumulative_state(self, arcs: list[dict]) -> dict:
        """
        여러 Arc의 누적 상태 추출

        [V61.1] Entity Registry도 전체 Arc에서 누적

        Args:
            arcs: Arc 데이터 리스트 (시간순)

        Returns:
            누적된 상태 정보 + 누적 entity_registry
        """
        if not arcs:
            return self._empty_state()

        # [V62.5] 캐시 통계 로깅
        total_count = len(arcs)
        cached_count = 0
        for a in arcs:
            ano = a.get("arc_no", "Unknown")
            key = ano if isinstance(ano, int) else hash(str(ano))
            if key in self._state_cache:
                cached_count += 1
        if cached_count > 0:
            logging.info(
                f"⚡ [V62.5] StateExtractor 캐시: {cached_count}/{total_count} Arc 캐시 히트 (LLM {total_count - cached_count}회만 호출)"
            )

        # 마지막 Arc 기준으로 추출
        latest_arc = arcs[-1]
        # Cache 오염 방지: 누적 상태 계산은 최신 Arc 상태의 사본에서만 수행
        current_state = dict(self.extract_state(latest_arc))

        # 전체 Arc에서 획득한 아이템 누적
        all_acquired = []
        all_grants = []

        # [V61.1] 전체 Arc에서 Entity 누적
        cumulative_entities = {
            "characters": {},  # name -> entity dict
            "organizations": {},
            "locations": {},
            "objects": {},
            "concepts": {},
        }

        for arc_idx, arc in enumerate(arcs):
            arc_no = arc.get("arc_no", arc_idx + 1)
            joint = arc.get("joint_docs", {})
            inventory = joint.get("physical_inventory", "")

            # 아이템 추출
            if isinstance(inventory, str):
                items = [i.strip() for i in inventory.split(",") if i.strip()]
                all_acquired.extend(items)
            elif isinstance(inventory, list):
                all_acquired.extend(inventory)

            # 수여물 추출
            tactical = arc.get("tactical_doc", "")
            if isinstance(tactical, dict):  # [V70] dict → str 변환
                tactical = "\n".join(str(v) for v in tactical.values() if v)
            elif not isinstance(tactical, str):
                tactical = str(tactical) if tactical else ""
            grants = self._extract_grants_from_text(tactical)
            all_grants.extend(grants)

            # 사망 NPC 추출
            if "deceased" in str(tactical).lower() or "사망" in tactical:
                # 간단한 추출 로직
                pass

            # [V61.1] Arc별 entity_registry 추출 및 누적
            arc_state = self.extract_state(arc)
            arc_entities = arc_state.get("entity_registry", {})

            for category in ["characters", "organizations", "locations", "objects", "concepts"]:
                category_entities = arc_entities.get(category, [])
                if not isinstance(category_entities, list):
                    continue

                for entity in category_entities:
                    if isinstance(entity, dict):
                        name = entity.get("name", "")
                    elif isinstance(entity, str):
                        name = entity
                        entity = {"name": name}
                    else:
                        continue

                    if not name:
                        continue

                    # 기존에 없으면 추가 (first_appearance 설정)
                    if name not in cumulative_entities[category]:
                        entity["first_appearance"] = f"Arc {arc_no}"
                        cumulative_entities[category][name] = entity
                    # 기존에 있으면 정보 보강 (alias 등)
                    else:
                        existing = cumulative_entities[category][name]
                        # alias 병합
                        if "aliases" in entity:
                            existing_aliases = existing.get("aliases", [])
                            for alias in entity.get("aliases", []):
                                if alias not in existing_aliases:
                                    existing_aliases.append(alias)
                            existing["aliases"] = existing_aliases

        # 중복 제거
        current_state["cumulative"] = {
            "all_acquired_items": list({str(x) if isinstance(x, dict) else x for x in all_acquired}),
            "all_grants_received": list({str(x) if isinstance(x, dict) else x for x in all_grants}),
            "total_arcs_completed": len(arcs),
        }

        # [V61.1] 누적된 entity_registry를 리스트 형태로 변환
        current_state["entity_registry"] = {
            category: list(entities.values()) for category, entities in cumulative_entities.items()
        }

        return current_state

    def generate_constraint_prompt(self, state: dict) -> str:
        """
        추출된 상태를 Analyst 프롬프트용 제약 텍스트로 변환

        Args:
            state: extract_state() 결과

        Returns:
            프롬프트에 주입할 제약 텍스트
        """
        protagonist = state.get("protagonist_state", {})
        inventory = state.get("inventory", {})
        forbidden = state.get("forbidden_in_next_arc", {})
        constraints = state.get("next_arc_constraints", {})

        lines = [
            "=" * 60,
            "🚨🚨🚨 [V60.10 STATE LOCK - 위반 시 즉시 REJECT] 🚨🚨🚨",
            "=" * 60,
            "",
            "### 1. 부상/내공 상태 (RECOVERY REQUIRED)",
        ]

        injuries = protagonist.get("injuries", [])
        if not isinstance(injuries, list):
            injuries = []
        if injuries:
            for inj in injuries:
                if not isinstance(inj, dict):
                    continue
                lines.append(
                    f"   - {inj.get('name', '?')}: {inj.get('severity', '?')} "
                    f"(회복 {inj.get('recovery_days', '?')}일 필요)"
                )
        else:
            lines.append("   - 없음")

        energy = protagonist.get("internal_energy", {})
        if not isinstance(energy, dict):
            energy = {"current_percent": int(energy) if isinstance(energy, int | float) else 100}
        lines.append(
            f"   - 내공: {energy.get('current_percent', 100)}% (회복 {energy.get('recovery_needed_days', 0)}일 필요)"
        )

        lines.append("")
        lines.append("### 2. 현재 소지품 (MUST HAVE)")
        current_items = inventory.get("current_items", [])
        if current_items:
            for item in current_items:
                lines.append(f"   - {item}")
        else:
            lines.append("   - 없음")

        lines.append("")
        lines.append("### 3. 절대 금지 (CANNOT DO)")
        cannot_acquire = forbidden.get("cannot_acquire_again", [])
        if cannot_acquire:
            lines.append("   [다시 획득 불가]")
            for item in cannot_acquire:
                lines.append(f"   ❌ {item}")

        cannot_receive = forbidden.get("cannot_receive_again", [])
        if cannot_receive:
            lines.append("   [다시 수여받기 불가]")
            for item in cannot_receive:
                lines.append(f"   ❌ {item}")

        lines.append("")
        lines.append("### 4. 다음 Arc 필수 사항")
        if constraints.get("recovery_scene_required"):
            lines.append(f"   ✅ 회복 장면 필수 (최소 {constraints.get('min_time_skip_days', 1)}일)")
        if constraints.get("must_start_with"):
            lines.append(f"   ✅ 도입부: {constraints.get('must_start_with')}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _validate_and_fix_result(self, result: dict, original_arc: dict) -> dict:
        """결과 검증 및 보정"""

        # protagonist_state 보정
        if "protagonist_state" not in result:
            result["protagonist_state"] = {}

        ps = result["protagonist_state"]
        if "injuries" not in ps:
            ps["injuries"] = []
        if "internal_energy" not in ps:
            ps["internal_energy"] = {"current_percent": 100, "consumed_this_arc": 0}
        if "location" not in ps:
            joint = original_arc.get("joint_docs", {})
            ps["location"] = {"current": joint.get("final_location", "알 수 없음"), "can_move_immediately": True}

        # inventory 보정
        if "inventory" not in result:
            result["inventory"] = {}

        inv = result["inventory"]
        if "current_items" not in inv:
            joint = original_arc.get("joint_docs", {})
            raw_inv = joint.get("physical_inventory", "")
            if isinstance(raw_inv, str):
                inv["current_items"] = [i.strip() for i in raw_inv.split(",") if i.strip()]
            elif isinstance(raw_inv, list):
                inv["current_items"] = raw_inv
            else:
                inv["current_items"] = []

        # forbidden 보정
        if "forbidden_in_next_arc" not in result:
            result["forbidden_in_next_arc"] = {
                "cannot_acquire_again": inv.get("current_items", []),
                "cannot_receive_again": [],
                "resolved_problems": [],
            }

        # next_arc_constraints 보정
        if "next_arc_constraints" not in result:
            injuries = ps.get("injuries", [])
            if not isinstance(injuries, list):
                injuries = []
            energy = ps.get("internal_energy", {})
            if not isinstance(energy, dict):
                energy = {"current_percent": int(energy) if isinstance(energy, int | float) else 100}

            recovery_needed = bool(injuries) or energy.get("current_percent", 100) < 50
            min_days = max([inj.get("recovery_days", 0) for inj in injuries if isinstance(inj, dict)] + [0])

            result["next_arc_constraints"] = {
                "must_start_with": "이전 상태 계승" if recovery_needed else None,
                "recovery_scene_required": recovery_needed,
                "min_time_skip_days": min_days,
                "mandatory_items_in_possession": inv.get("current_items", []),
            }

        # [V61] entity_registry 보정
        if "entity_registry" not in result:
            result["entity_registry"] = self._empty_entity_registry()
        else:
            # 각 카테고리 존재 확인
            er = result["entity_registry"]
            for cat in ["characters", "organizations", "locations", "objects", "concepts"]:
                if cat not in er:
                    er[cat] = []

        return result

    def _fallback_extraction(self, arc_data: dict) -> dict:
        """LLM 실패 시 Python 기반 추출"""

        joint = arc_data.get("joint_docs", {})
        shadow = arc_data.get("status_shadow", {})
        # [V60.13 FIX] arc_end_state 우선 사용
        state_constraints = arc_data.get("state_constraints", {})
        arc_end_state = state_constraints.get("arc_end_state", {})

        # 소지품 추출
        raw_inv = joint.get("physical_inventory", "")
        if isinstance(raw_inv, str):
            current_items = [i.strip() for i in raw_inv.split(",") if i.strip()]
        elif isinstance(raw_inv, list):
            current_items = raw_inv
        else:
            current_items = []

        # 부상 추출 - arc_end_state 우선
        injuries_raw = arc_end_state.get("injuries") or shadow.get("expected_injuries", "")
        injuries = []
        if injuries_raw and injuries_raw != "없음":
            injuries.append(
                {"name": injuries_raw[:50], "severity": "unknown", "recovery_days": 3, "recovery_method": "운기조식"}
            )

        # 내공 추출 - arc_end_state 우선
        if arc_end_state.get("internal_energy") is not None:
            raw_energy = arc_end_state["internal_energy"]
            try:  # [V70] string/float 안전 변환
                current_energy = (
                    int(raw_energy)
                    if isinstance(raw_energy, int | float)
                    else int(str(raw_energy).replace("%", "").strip())
                )
            except (ValueError, TypeError):
                current_energy = 50
            loss_percent = 100 - current_energy
        else:
            energy_loss = shadow.get("internal_energy_loss", "0%")
            try:
                loss_percent = int(str(energy_loss).replace("%", "").strip())
                current_energy = 100 - loss_percent
            except (ValueError, AttributeError, TypeError):  # [V64.P4] energy parse failure
                # [V60.73] 보수적 기본값 50 (파싱 실패 시 만땅 가정 위험)
                logging.warning(f"⚠️ [V60.73] internal_energy_loss 파싱 실패: '{energy_loss}' → 50% 가정")
                loss_percent = 50
                current_energy = 50

        return {
            "arc_no": arc_data.get("arc_no", "Unknown"),
            "protagonist_state": {
                "injuries": injuries,
                "internal_energy": {
                    "current_percent": current_energy,
                    "consumed_this_arc": loss_percent,
                    "recovery_needed_days": loss_percent // 10,
                },
                "location": {
                    "current": joint.get("final_location", "알 수 없음"),
                    "can_move_immediately": not bool(injuries),
                },
            },
            "inventory": {
                "current_items": current_items,
                "acquired_this_arc": [],
                "consumed_or_lost": shadow.get("item_consumption", []),
            },
            "forbidden_in_next_arc": {
                "cannot_acquire_again": current_items,
                "cannot_receive_again": [],
                "resolved_problems": [],
            },
            "next_arc_constraints": {
                "recovery_scene_required": bool(injuries) or loss_percent > 30,
                "min_time_skip_days": max([i.get("recovery_days", 0) for i in injuries] + [0]),
                "mandatory_items_in_possession": current_items,
            },
            # [V61.1] Python regex fallback으로 entity 추출 (LLM 실패 시)
            "entity_registry": self._fallback_entity_extraction(
                str(arc_data.get("tactical_doc", "")) + " " + str(joint)
            ),
        }

    def _empty_entity_registry(self) -> dict:
        """[V61] 빈 Entity Registry 반환"""
        return {"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}

    def _empty_state(self) -> dict:
        """빈 상태 반환"""
        return {
            "arc_no": 0,
            "protagonist_state": {
                "injuries": [],
                "internal_energy": {"current_percent": 100, "consumed_this_arc": 0},
                "location": {"current": "시작점", "can_move_immediately": True},
            },
            "inventory": {"current_items": [], "acquired_this_arc": [], "consumed_or_lost": []},
            "forbidden_in_next_arc": {"cannot_acquire_again": [], "cannot_receive_again": [], "resolved_problems": []},
            "next_arc_constraints": {
                "recovery_scene_required": False,
                "min_time_skip_days": 0,
                "mandatory_items_in_possession": [],
            },
            "entity_registry": self._empty_entity_registry(),
        }

    def _extract_grants_from_text(self, text: str) -> list[str]:
        """텍스트에서 수여물 추출"""
        import re

        grants = []

        patterns = [
            r"([가-힣]+패)[를을]?\s*(?:하사|수여|받|얻)",
            r"([가-힣]+권)[를을]?\s*(?:위임|부여|받|얻)",
            r"([가-힣]+직|[가-힣]+장)[에으로]?\s*(?:임명|취임)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            grants.extend(matches)

        return list(set(grants))

    def _fallback_entity_extraction(self, text: str) -> dict:
        """
        [V61.1] Python regex 기반 Entity 추출 (LLM 실패 시 fallback)

        tactical_doc, joint_docs 등에서 고유명사를 패턴 매칭으로 추출
        """
        import re

        entities = {"characters": [], "organizations": [], "locations": [], "objects": [], "concepts": []}

        if not text or not isinstance(text, str):
            return entities

        # ═══════════════════════════════════════════════════════════════
        # 1. 캐릭터 추출 (이름 패턴)
        # ═══════════════════════════════════════════════════════════════
        # 한글 이름 패턴: 2~4글자 (성+이름)
        char_patterns = [
            r"([가-힣]{2,4})(?:이|가|은|는|을|를|와|과|의|에게|한테|로부터)\s",  # 조사 앞 이름
            r"(?:노|고|용|악|적|협객|검객|무사|협사|소협|대협|장로|문주|가주|종주|제자|사형|사제|사매|사숙|도장|대사|법사|방주|당주|주군|공자|소저)\s+([가-힣]{2,4})",  # 호칭 뒤 이름
            r"([가-힣]{2,4})\s*(?:노|선생|장로|문주|가주|종주|대협|소협)",  # 이름 뒤 호칭
        ]

        found_chars = set()
        for pattern in char_patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                name = m.strip() if isinstance(m, str) else m
                # 일반 단어 필터링
                if len(name) >= 2 and name not in ["그것", "이것", "저것", "무엇", "어디", "여기", "저기", "누구"]:
                    found_chars.add(name)

        # 명시적 캐릭터 언급
        explicit_char = re.findall(r"(?:등장인물|캐릭터|NPC)[:：]\s*([가-힣]{2,4})", text)
        found_chars.update(explicit_char)

        entities["characters"] = [{"name": c, "role": "extracted", "first_appearance": "unknown"} for c in found_chars]

        # ═══════════════════════════════════════════════════════════════
        # 2. 조직 추출 (문파/세력 패턴)
        # ═══════════════════════════════════════════════════════════════
        org_patterns = [
            r"([가-힣]{2,6}(?:문|파|방|단|회|맹|련|종|가|당|세|교|군|대))",  # ~문, ~파, ~방 등
            r"([가-힣]{2,8}(?:문파|세력|조직|가문|단체|연맹|동맹))",  # 명시적 조직
            r"(?:정파|사파|마교|흑도|백도|무림|강호)의?\s*([가-힣]{2,6})",  # 무림 관련
        ]

        found_orgs = set()
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            found_orgs.update(matches)

        entities["organizations"] = [
            {"name": o, "type": "extracted", "first_appearance": "unknown"} for o in found_orgs
        ]

        # ═══════════════════════════════════════════════════════════════
        # 3. 장소 추출
        # ═══════════════════════════════════════════════════════════════
        loc_patterns = [
            r"([가-힣]{2,8}(?:산|성|촌|진|루|각|전|관|당|원|궁|부|현|주|도|강|호|해))",  # 지명 접미사
            r"([가-힣]{2,6}(?:객잔|주막|여관|시장|광장|거리|골목|동굴|폐허|절벽))",  # 장소 유형
            r"(?:에서|에|으로|로)\s*([가-힣]{2,8}(?:산|성|촌|전|관|당|원))",  # 조사 뒤 장소
        ]

        found_locs = set()
        for pattern in loc_patterns:
            matches = re.findall(pattern, text)
            found_locs.update(matches)

        entities["locations"] = [{"name": l, "type": "extracted", "first_appearance": "unknown"} for l in found_locs]

        # ═══════════════════════════════════════════════════════════════
        # 4. 물품/아이템 추출
        # ═══════════════════════════════════════════════════════════════
        obj_patterns = [
            r"([가-힣]{2,8}(?:검|도|창|봉|편|권|갑|의|환|단|서|비급|병기|무기|보물|신물|영약|영단))",  # 무기/아이템
            r"([가-힣]{2,6}(?:패|표|령|인|부|증))",  # 신표류
            r"(?:획득|입수|수령|전수받은?)\s*([가-힣]{3,10})",  # 획득 문맥
        ]

        found_objs = set()
        for pattern in obj_patterns:
            matches = re.findall(pattern, text)
            found_objs.update(matches)

        entities["objects"] = [{"name": o, "type": "extracted", "first_appearance": "unknown"} for o in found_objs]

        # ═══════════════════════════════════════════════════════════════
        # 5. 개념/무공 추출
        # ═══════════════════════════════════════════════════════════════
        concept_patterns = [
            r"([가-힣]{2,10}(?:공|결|법|술|식|초|장|권|검|도|보|신공|심법|비급|무공|무학|절학|비전))",  # 무공명
            r"([가-힣]{2,8}(?:경지|경계|단계|층|성|화경|선천|후천|절정|화경|현경))",  # 경지
            r"(?:수련|전수|깨달|익힌?)\s*([가-힣]{3,10})",  # 수련 문맥
        ]

        found_concepts = set()
        for pattern in concept_patterns:
            matches = re.findall(pattern, text)
            found_concepts.update(matches)

        entities["concepts"] = [{"name": c, "type": "extracted", "first_appearance": "unknown"} for c in found_concepts]

        return entities

    # ===== [D Step 3] 에피소드 만족도 태깅 =====

    _VALID_TAGS = frozenset({"성취", "성장", "전투", "이행", "일상", "좌절"})
    _VALID_AGENCY = frozenset({"자력", "협력", "타인의존"})

    def extract_satisfaction_tag(self, manuscript: str, ep_num: int) -> dict:
        """에피소드의 만족도 태그를 LLM으로 추출한다.

        Returns:
            {
                "ep_num": int,
                "primary_tag": "성취"|...|"좌절",
                "satisfaction_score": 1~10,
                "protagonist_agency": "자력"|"협력"|"타인의존",
                "frustration_flag": bool,
            }
        """
        prompt = SATISFACTION_TAG_PROMPT.format_map(
            SafeDict(
                ep_num=ep_num,
                manuscript=self._escape_braces(manuscript[:20000]),
            )
        )

        try:
            result = self.ask(prompt, temperature=0.2, thinking_level="low")
            if isinstance(result, str):
                result = self._extract_json_robust(result)
            return self._validate_satisfaction_tag(result, ep_num)
        except Exception as e:
            logging.warning("[D Step 3] 만족도 태깅 LLM 실패 (fallback): %s", e)
            return self._fallback_satisfaction_tag(manuscript, ep_num)

    def _validate_satisfaction_tag(self, raw: dict, ep_num: int) -> dict:
        """LLM 결과를 검증하고 정규화한다."""
        if not isinstance(raw, dict):
            return self._fallback_satisfaction_tag("", ep_num)

        tag = raw.get("primary_tag", "일상")
        if tag not in self._VALID_TAGS:
            tag = "일상"

        score = raw.get("satisfaction_score", 5)
        try:
            score = max(1, min(10, int(score)))
        except (ValueError, TypeError):
            score = 5

        agency = raw.get("protagonist_agency", "자력")
        if agency not in self._VALID_AGENCY:
            agency = "자력"

        return {
            "ep_num": ep_num,
            "primary_tag": tag,
            "satisfaction_score": score,
            "protagonist_agency": agency,
            "frustration_flag": tag == "좌절",
        }

    def _fallback_satisfaction_tag(self, manuscript: str, ep_num: int) -> dict:
        """LLM 실패 시 Python 키워드 기반 fallback."""
        text = manuscript[:3000] if manuscript else ""

        # 키워드 기반 분류
        achievement_kw = ["승리", "성공", "돌파", "제압", "획득", "달성", "격파"]
        growth_kw = ["성장", "깨달", "각성", "수련", "향상", "진급", "레벨"]
        frustration_kw = ["패배", "좌절", "실패", "위기", "절망", "추락", "상실"]
        combat_kw = ["전투", "교전", "대결", "공격", "방어", "검격", "일격"]

        a_count = sum(1 for kw in achievement_kw if kw in text)
        g_count = sum(1 for kw in growth_kw if kw in text)
        f_count = sum(1 for kw in frustration_kw if kw in text)
        c_count = sum(1 for kw in combat_kw if kw in text)

        scores = {"성취": a_count, "성장": g_count, "좌절": f_count, "전투": c_count}
        best = max(scores, key=scores.get) if max(scores.values()) > 0 else "일상"

        score_map = {"성취": 8, "성장": 7, "전투": 5, "이행": 5, "일상": 5, "좌절": 3}

        return {
            "ep_num": ep_num,
            "primary_tag": best,
            "satisfaction_score": score_map.get(best, 5),
            "protagonist_agency": "자력",
            "frustration_flag": best == "좌절",
        }
