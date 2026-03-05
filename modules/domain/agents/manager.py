import json
import logging

from modules.core.genre_schema_builder import (
    build_actual_truth_schema,
    build_manager_genre_instructions,
    build_npc_hud_schema,
    is_wuxia,
)

from .base_agent import BaseAgent

# =================================================================
# V25 서사 정산 및 성경 업데이트(Manager) - 정밀 스키마 보존형
# =================================================================
UPDATE_STATE_PROMPT_V25 = """
[🚨 SYSTEM CRITICAL: S-GRADE DATA ADMINISTRATOR]
당신은 단순한 요약가가 아니라 '데이터 무결성 관리자'다.
원고를 분석하여 다음 세 가지 영역을 정밀하게 정산하라.


1. **무림 15대 지표 (MARTIAL_METRICS) 정산**:
   - `modules/core/constants.py`에 정의된 15대 표준 키를 엄격히 준수하라.
   - 변화가 있다면 반드시 `actual_truth` 내부에 반영하되, 수치형 데이터는 이전 상태를 계승하여 누적하라.
2. **로어 및 인과관계 기록**:
  - 신규 설정은 `new_lore`에, 사건의 인과는 `causal_links`에 담아라.

3. 원고에서 '영약', '수련', '새로운 초식'이 등장했는데 HUD 수치를 갱신하지 않는 것은 치명적인 직무유기다.
4. 이전 상태(current_state_json)와 비교하여 1이라도 변화가 있다면 반드시 actual_truth의 수치를 수정하라.
5. 특히 'internal_energy'와 'martial_arts' 리스트는 매 화 가장 정밀하게 감시되어야 한다.

[🚨 V45 장비(equipment) 정산 강령 - 주인공 & NPC 공통]
1. **equipment는 현재 소지 목록 전체를 배열로 출력하라** (증분이 아님)
2. 장비를 획득했으면: 기존 목록 + 새 장비 = 전체 목록 출력
3. 장비를 잃어버리거나 버렸으면: 해당 장비를 제외한 나머지 목록 출력
4. 장비를 교체했으면 (예: 철갑의 → 평복): 새 장비만 목록에 포함
5. 장비에 변화가 없으면: 기존 목록 그대로 출력 (생략 금지!)
6. 모든 장비를 잃어버렸으면: 빈 배열 [] 출력
예시:
- 이전: ["청강검", "철갑의"] → 철갑의를 벗고 평복 획득 → 출력: ["청강검", "평복"]
- 이전: ["단검"] → 검을 잃어버림 → 출력: []
6. 카르마 정산: 이번 화에서 주인공을 목격한 조연들의 '착각(오해)'이나 '집착' 정도를 0~100 사이의 수치로 정산하라.
  - 변화가 없다면 이전 수치를 유지하되, 주인공의 무위가 드러났다면 반드시 'value' 수치를 상향하라.
  - 형식: {"target": "이름", "value": 0~100, "obsession": 0~100}
7. 집필된 원고를 분석하여 주인공의 상태 변화, 강호의 소문, 새로 발견된 설정을 [MasterBible] 스키마에 맞춰 정밀하게 정산하십시오.

[🚨 V27.5 NPC 실시간 정산 강령]
1. 이번 화에서 조연(NPC)이 무공을 시전하거나 부상을 입었는가?
2. 만약 그렇다면 'new_lore' -> 'Key_NPCs' 리스트 내부에 해당 NPC의 이름과 'NPC_Martial_HUD' 객체를 포함하라.
3. 특히 'achievement_rate'는 조연의 깨달음 정도에 따라 1% 단위로 정밀하게 조정하라.
4. 조연이 입은 부상은 'current_status'에 기록하여 다음 화 전투에 반영되게 하라.
5. [V45] NPC가 새로운 무기/장비를 획득하거나 잃어버렸다면 'equipment' 필드에 현재 소지 장비 목록을 기록하라.
6. [V45] NPC 간에 아이템이 이전되었다면 (예: 주인공이 NPC에게 검을 줌) 반드시 양쪽의 equipment를 갱신하라.


### 🎯 V25 정산 핵심 지침
1. **이중 HUD 정산 (Dual-Layer HUD)**: actual_truth(진실)와 public_reputation(인식)을 분리하라.
2. **인식 지도(Knowledge Map) 동기화**: 진실을 아는 자와 오해하는 자를 구분하라.
3. **자산 라이브러리 확장**: 신규 NPC와 아이템 정보를 추출하라.
4. **복선(Seeds) 상태 관리**: 활성화된 복선의 회수 여부를 판별하라.

### ⚠️ 출력 형식 (JSON Only - 규격 미준수 시 시스템 파기)
{{
  "context_audit": {{
    "integrity_score": 0~100,
    "summary": "핵심 사건 요약",
    "evidence_check": "변화 근거"
  }},
  "state_updates": {{
    "location": "현재 위치",
    "actual_truth": {{
      "alias": "별호", "rank": "직위", "realm": "경지",
      "internal_energy": "숫자만 기입 (예: 60.0). '갑자' 단위는 60을 곱해서 환산하라.", "mental_method": "심법",
      "reputation": "명성", "public_image": "이미지",
      "equipment": ["현재 소지 장비 전체 목록을 배열로 기입"],
      "wealth": "자금", "token": "신물",
      "misunderstanding": "0~100 사이의 정수만 기입", "obsession": "누적된 현재 총 수치",
      "current_objective": "목표", "qi_nature": "진기성질", "causal_injuries": "내상상태",
      "inventory": [], "martial_arts": []
    }},
    "public_reputation": {{ "identity": "호칭", "realm": "인식경지", "perceived_power": "인식위력" }},
    "karma_matrix": [
      { "target": "NPC명", "value": 0, "obsession": 0}
    ]
  }},
  "knowledge_map_updates": {{ "new_witnesses": [], "new_misled": [] }},
  "new_lore": {{
    "Key_NPCs": [
      {{
        "name": "조연이름",
        "role": "역할",
        "desc": "성격/특징 보강",
        "NPC_Martial_HUD": {{
          "realm": "경지",
          "main_technique": "주력무공",
          "achievement_rate": "성취도%",
          "energy_level": "내공수준",
          "current_status": "현재상태(부상 등)",
          "combat_style": "무도십이류 성질(쾌/강/유 등)",
          "equipment": ["현재 소지 무기/장비 목록"]
        }}
      }}
    ],
    "Key_Items": []
  }},
  "recovered_seeds": [
    {{ "seed_id": "ID", "description": "회수 근거" }}
  ],
  "causal_links": []
}}

### 📊 정산 대상 데이터 (Input Data)
- 현재 회차: 제 {ep_num}화
- 집필된 원고 전문: {manuscript}
- 현재 HUD 상태 (JSON): {current_state_json}
- 활성화된 복선 목록: {active_seeds_json}
- 관련 로어 데이터: {lore_list_json}
- 최근 서사 요약: {causal_history}
"""


def _build_genre_manager_prompt(
    genre: str,
    critical_keys: list[str],
    ep_num: int,
    manuscript: str,
    current_state_json: str,
    lore_list_json: str,
    active_seeds_json: str,
    causal_history: str,
) -> str:
    """비무협 장르용 Manager 정산 프롬프트 생성."""
    genre_instructions = build_manager_genre_instructions(genre, critical_keys)
    actual_truth_schema = build_actual_truth_schema(genre, critical_keys)
    npc_hud_schema = build_npc_hud_schema(genre)

    return f"""[SYSTEM CRITICAL: S-GRADE DATA ADMINISTRATOR]
당신은 단순한 요약가가 아니라 '데이터 무결성 관리자'다.
원고를 분석하여 다음 영역을 정밀하게 정산하라.

{genre_instructions}

[V45 장비(equipment) 정산 강령 - 주인공 & NPC 공통]
1. **equipment는 현재 소지 목록 전체를 배열로 출력하라** (증분이 아님)
2. 장비를 획득했으면: 기존 목록 + 새 장비 = 전체 목록 출력
3. 장비를 잃어버리거나 버렸으면: 해당 장비를 제외한 나머지 목록 출력
4. 장비를 교체했으면: 새 장비만 목록에 포함
5. 장비에 변화가 없으면: 기존 목록 그대로 출력 (생략 금지!)
6. 모든 장비를 잃어버렸으면: 빈 배열 [] 출력

[V27.5 NPC 실시간 정산 강령]
1. 이번 화에서 조연(NPC)에게 주요 변화가 있었는가?
2. 만약 그렇다면 'new_lore' -> 'Key_NPCs' 리스트 내부에 해당 NPC의 이름과 HUD 객체를 포함하라.
3. NPC가 새로운 장비를 획득하거나 잃어버렸다면 'equipment' 필드에 현재 소지 장비 목록을 기록하라.

### V25 정산 핵심 지침
1. **이중 HUD 정산 (Dual-Layer HUD)**: actual_truth(진실)와 public_reputation(인식)을 분리하라.
2. **인식 지도(Knowledge Map) 동기화**: 진실을 아는 자와 오해하는 자를 구분하라.
3. **자산 라이브러리 확장**: 신규 NPC와 아이템 정보를 추출하라.
4. **복선(Seeds) 상태 관리**: 활성화된 복선의 회수 여부를 판별하라.

### 출력 형식 (JSON Only - 규격 미준수 시 시스템 파기)
{{{{
  "context_audit": {{{{
    "integrity_score": 0~100,
    "summary": "핵심 사건 요약",
    "evidence_check": "변화 근거"
  }}}},
  "state_updates": {{{{
    "location": "현재 위치",
{actual_truth_schema},
    "public_reputation": {{{{"identity": "호칭", "perceived_power": "인식 수준"}}}},
    "karma_matrix": [
      {{{{"target": "NPC명", "value": 0, "obsession": 0}}}}
    ]
  }}}},
  "knowledge_map_updates": {{{{"new_witnesses": [], "new_misled": []}}}},
  "new_lore": {{{{
    "Key_NPCs": [
      {{{{
        "name": "조연이름",
        "role": "역할",
        "desc": "성격/특징 보강",
{npc_hud_schema}
      }}}}
    ],
    "Key_Items": []
  }}}},
  "recovered_seeds": [
    {{{{"seed_id": "ID", "description": "회수 근거"}}}}
  ],
  "causal_links": []
}}}}

### 정산 대상 데이터 (Input Data)
- 현재 회차: 제 {ep_num}화
- 집필된 원고 전문: {manuscript}
- 현재 HUD 상태 (JSON): {current_state_json}
- 활성화된 복선 목록: {active_seeds_json}
- 관련 로어 데이터: {lore_list_json}
- 최근 서사 요약: {causal_history}
"""


class Manager(BaseAgent):
    def update_state_and_lore_v20(
        self,
        ep_num: int,
        manuscript: str,
        current_state: dict,
        lore_list: list,
        active_seeds: list,
        causal_history: str = "",
        genre: str = "wuxia",
        critical_keys: list | None = None,
    ) -> dict:
        """
        [V35.9 S-Grade] 정산 데이터 파싱 및 안전 전달 엔진
        - 무리한 내부 보정을 제거하여 main_a.py와의 충돌 방지
        """
        # 1. [V70] .replace() 치환에는 _escape_braces 불필요 (이중 이스케이프 제거)
        safe_ms = manuscript
        if not current_state:  # [V70] None/빈 dict 방어
            current_state = {}
        safe_state = json.dumps(current_state.get("actual_truth", current_state), ensure_ascii=False)
        safe_lore = json.dumps(lore_list, ensure_ascii=False)
        safe_seeds = json.dumps(active_seeds, ensure_ascii=False)
        safe_history = causal_history if causal_history else "기록 없음"

        # 2. [TF-45] 장르 분기: 무협은 기존 경로 100% 보존, 비무협은 새 스키마
        if is_wuxia(genre):
            # 기존 경로 — UPDATE_STATE_PROMPT_V25 상수 그대로 사용
            # [CrosscutR41] {manuscript}를 맨 마지막에 치환 — 원고 내 플레이스홀더 리터럴 이중 치환 방지
            full_prompt = (
                UPDATE_STATE_PROMPT_V25.replace("{ep_num}", str(ep_num))
                .replace("{current_state_json}", safe_state)
                .replace("{active_seeds_json}", safe_seeds)
                .replace("{lore_list_json}", safe_lore)
                .replace("{causal_history}", safe_history)
                .replace("{manuscript}", safe_ms)
            )
        else:
            # [TF-45] 비무협 경로 — 장르별 동적 프롬프트 생성
            full_prompt = _build_genre_manager_prompt(
                genre=genre,
                critical_keys=critical_keys or [],
                ep_num=ep_num,
                manuscript=safe_ms,
                current_state_json=safe_state,
                lore_list_json=safe_lore,
                active_seeds_json=safe_seeds,
                causal_history=safe_history,
            )

        # 3. 낮은 온도로 정밀 정산 요청
        response = self.ask(full_prompt, temperature=0.1)

        # 4. [V38.5 S-Grade Patch] 결과 파싱 후 즉시 반환 (main_a.py로 가공 위임)
        try:
            # AI가 준 데이터를 섣부르게 내부에서 가공(.get 호출 등)하지 않고
            # 가장 강력한 파싱 엔진의 결과물만 그대로 main_a.py의 방탄 로직으로 넘깁니다.
            return self._extract_json_robust(response)
        except Exception as e:
            logging.warning(f" [Manager Parsing Error] {e}")
            return {"parsing_error": True, "raw_response": response}

    def audit_for_consistency(self, manuscript: str, master_bible: dict) -> dict:
        """[Extra] 설정 충돌 검사 - 안전 패치 완료"""
        # 1. 중괄호 이스케이프로 파이썬 format 에러 방지
        safe_ms = self._escape_braces(manuscript)
        safe_bible = self._escape_braces(json.dumps(master_bible, ensure_ascii=False, indent=2))

        # 2. 프롬프트 구성
        prompt = f"""
        당신은 서사 무결성 감사관입니다. 원고와 성경 설정의 충돌을 검사하십시오.
        [MasterBible]: {safe_bible}
        [원고]: {safe_ms}
        충돌 시 "CRITICAL_ERROR", 통과 시 "CLEAR" 반환.
        """

        # 3. 낮은 온도로 엄격한 판정 요청
        return self.ask(prompt, temperature=0.1)
