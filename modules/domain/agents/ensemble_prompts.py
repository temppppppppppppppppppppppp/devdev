"""[V64.P4] Ensemble 프롬프트 템플릿 외부화.

ArcEnsembleGenerator, BlueprintEnsembleGenerator의
대형 프롬프트 문자열을 코드 로직에서 분리.
"""

# -- Arc Ensemble Prompts (from arc_ensemble.py) --  [V64.P4]

ENSEMBLE_ARC_PROMPT = """
[V60.11 ENSEMBLE ARC GENERATOR - {strategy_name} 전략]

##############################################################
# 🔒 [V60.18] 주인공 정보 - 반드시 이 이름을 사용!
##############################################################
주인공 이름: {protagonist_name}
→ tactical_doc에서 반드시 '{protagonist_name}'을 사용하세요!
→ 다른 이름(이현, 강민수 등)은 절대 사용 금지!
{protagonist_instructions}
##############################################################

##############################################################
# 🚨🚨🚨 [V60.13] 최우선 금지 사항 - 위반 시 즉시 REJECT 🚨🚨🚨
##############################################################
{prohibition_summary}
##############################################################

### 생성 전략
{strategy_focus}
스타일: {strategy_style}

### [V63] 서사 흥미 설계 (필수)
1. **갈등 구조**: 이 Arc의 핵심 갈등 정의. 외적 갈등(적/장애물)과 내적 갈등(딜레마/성장통) 모두 포함.
2. **반전 포인트**: Arc 내 최소 1개의 독자 예측을 벗어나는 전개 포함. (아군 배신, 적의 도움, 해결이라 생각한 갈등이 더 큰 위기의 시작 등)
3. **감정 곡선**: 연속 3화 이상 같은 감정 톤 금지.
4. **캐릭터 선택의 순간**: 주인공이 양쪽 다 손해인 딜레마에서 의미 있는 선택을 하는 장면 최소 1개.

### [🚨 ABSOLUTE CONSTRAINTS - 위반 시 0점]

████████████████████████████████████████████████████████████████████████████████
█   🚨 [V60.38] tactical_doc 분량 필수 - 위반 시 즉시 REJECT                   █
█   ⚠️ 총 분량: 최소 (ep_count × 500)자 이상                                   █
█   ⚠️ 1,500자 미만 = CRITICAL REJECT (시스템 자동 거부)                        █
████████████████████████████████████████████████████████████████████████████████

⚠️ CRITICAL: tactical_doc 내용과 state_constraints는 반드시 일치해야 합니다!
- 이전 Arc 종료 시 내공이 70%이면, tactical_doc에서도 "내공 70%" 또는 "7할의 내공"으로 표현
- "2할" "20%" 같은 다른 수치 사용 금지
- 부상 상태도 state_constraints.arc_start_state와 동일하게 표현

{constraint_block}

### [이전 Arc 상태 - 반드시 계승]
{prev_arc_context}

### [현재 블록 DNA]
{curr_block}

{genre_ext_guide}

### [Volume 전략]
{vol_strategy}

### [AssetLibrary]
{assets}

### [피드백 (있다면)]
{feedback}

{entity_registry_section}

### [V62.2] 🩹 주인공 자연 회복 원칙 (전 장르 공통)
- 주인공은 소설 주인공이다. 힐링팩터가 있다. 절대 약해지지 않는다.
- 아크 시작: 부상="없음", 내공=100%. 예외 없음.
- 화별 내공 규칙:
  · 한 화 안에서 긴장/전투로 소모 가능 (최저 60%까지만)
  · 다음 화 시작 시 반드시 90% 이상으로 회복
  · 내공이 화를 거듭하며 떨어지기만 하는 것은 절대 금지
  · 주인공은 점점 강해진다. 내공은 우상향이 기본이다.
- 부상: Arc 내 일시적 피로/타박 허용, 다음 화면 회복됨. 만성화 금지.
- arc_end_state: injuries="없음", internal_energy=100
- status_shadow: expected_injuries="없음", internal_energy_loss="0%"

### [V60.40] 화간 상태 체크포인트 필수
각 화는 반드시 시작 상태와 종료 상태를 명시하라:
- 시작 상태: 위치, 내공%, 부상, 소지품 (이전 화 종료 상태 기반 + 자연 회복 적용)
- 종료 상태: 위치, 내공%, 부상, 획득/소모 아이템
- ⚠️ 내공이 화를 넘기며 계속 떨어지는 패턴은 REJECT 사유임

### [Output JSON Schema]
{{
    "arc_no": {arc_no},
    "ep_count": "3~7 중 사건 밀도에 맞게 결정",
    "ep_start": {ep_start},
    "ep_end": {ep_end},
    "title": "Arc 제목",
    "tactical_doc": "[V60.40] 각 화마다 시작/종료 상태 체크포인트 필수. 화당 500자 이상. '제 N화:' 형식으로 화별 명확 구분",
    "beat_sequence": ["제 N화: 핵심 비트", ...],
    "hybrid_composition": {{
        "primary": "주 서사 패턴",
        "secondary": ["부 패턴"],
        "mixing_logic": "패턴 조합 전략"
    }},
    "state_constraints": {{
        "arc_start_state": {{
            "location": "시작 위치 (이전 Arc 종료 위치와 동일해야 함)",
            "equipment": ["소지품 (이전 Arc 종료 시 소지품과 동일)"],
            "injuries": "부상 상태 (이전 Arc 부상 계승)",
            "internal_energy": 내공_퍼센트
        }},
        "arc_end_state": {{
            "location": "종료 위치",
            "equipment": ["종료 시 소지품"],
            "injuries": "종료 시 부상",
            "internal_energy": 내공_퍼센트
        }},
        "items_acquired": ["새로 획득 아이템 (이전에 없던 것만)"],
        "items_consumed": ["소모 아이템"],
        "grants_received": ["수여받은 것"]
    }},
    "joint_docs": {{
        "final_location": "Arc 종료 시 정확한 위치",
        "physical_inventory": ["종료 시 소지품 전체 목록"],
        "world_joint": "다음 Arc가 계승할 세계 변화"
    }},
    "status_shadow": {{
        "internal_energy_loss": "N%",
        "expected_injuries": "부상 상태",
        "item_consumption": ["소모된 아이템"]
    }},
    "state_changes": {{
        "timeline": {{
            "start": {{"표현": "Arc 시작 시점 (예: year, month, period 등 장르별)"}},
            "end": {{"표현": "Arc 종료 시점"}}
        }},
        "npc_deaths": [
            {{"name": "사망한 NPC 이름", "episode": N, "cause": "사망 원인"}}
        ],
        "skill_acquisitions": [
            {{"name": "습득한 무공/기술", "episode": N, "source": "습득 경위(비급/전수/깨달음)"}}
        ],
        "relationship_changes": [
            {{"npc": "NPC 이름", "from": "이전 관계(적/중립/아군)", "to": "변경 후 관계", "episode": N}}
        ],
        "major_items": [
            {{"name": "중요 아이템", "episode": N, "action": "획득/소모/분실"}}
        ],
        "resolved_plots": [
            {{"plot": "완결된 갈등/사건 이름", "resolution": "해결 방법", "episode": N}}
        ],
        "npc_injuries": [
            {{"name": "NPC명", "episode": N, "state": "경상/중상/위독", "cause": "부상 원인"}}
        ],
        "npc_movements": [
            {{"name": "NPC명", "episode": N, "from": "출발지", "to": "도착지"}}
        ],
        "entity_destructions": [
            {{"name": "파괴된 조직/장소명", "type": "organization|location", "cause": "파괴 원인", "episode": N}}
        ],
        "npc_personality_changes": [
            {{"name": "NPC명", "traits": "성격 특성 요약", "motivation": "주요 동기", "episode": N}}
        ],
        "npc_npc_relationships": [
            {{"npc1": "NPC_A", "npc2": "NPC_B", "relation": "동맹|적대|사제|부자|연인", "episode": N}}
        ],
        "time_markers": [
            {{"type": "elapsed_time|season|time_of_day|specific_date", "description": "시간 표현 (예: 3일 경과, 겨울, 새벽)", "episode": N}}
        ],
        "permanent_injuries": [
            {{"name": "NPC명", "type": "amputation|blindness|scar|disfigurement", "description": "왼팔 절단/실명/흉터 등", "episode": N}}
        ],
        "companion_changes": [
            {{"name": "NPC명", "action": "join|leave", "episode": N, "reason": "합류/이탈 사유"}}
        ],
        "commitments": [
            {{"parties": ["A", "B"], "description": "3일 후 금 100냥 상환", "episode": N}}
        ],
        "protagonist_emotion": {{"emotion": "비통", "trigger": "부모 사망", "episode": N}},
        "npc_dialogue_profiles": [
            {{"name": "NPC명", "speech_style": "말투 특징", "catchphrase": "습관적 표현", "episode": N}}
        ],
        "financial_events": {{
            "exchange_rates": [
                {{"value": 숫자, "episode": N, "context": "환율 설명"}}
            ],
            "total_assets": [
                {{"value": "금액 문자열", "episode": N, "context": "평가액 설명"}}
            ],
            "leverage": [
                {{"value": 숫자, "episode": N, "context": "레버리지 설명"}}
            ],
            "key_transactions": [
                {{"type": "매수/매도/인수/청산", "target": "대상", "amount": "금액", "episode": N}}
            ]
        }}
    }}
}}

⚠️ [V61] state_changes 필수 작성:
- timeline: Arc의 시작/종료 시점 필수 기록 (장르별 표현 사용)
  - 투자물: {{"year": 2000, "month": 3}}, 무협: {{"period": "대회 3일차", "season": "초여름"}}
  - 헌터물: {{"day": "각성 후 15일차", "event_marker": "첫 던전 클리어 직후"}}
  - 판타지: {{"era": "마왕 부활 후 2년", "event": "왕국 멸망 직전"}}
- 이번 Arc에서 NPC가 죽으면 반드시 npc_deaths에 기록
- 주인공이 무공을 배우면 반드시 skill_acquisitions에 기록
- 관계 변화(적→아군 등)가 있으면 relationship_changes에 기록
- resolved_plots: 이번 Arc에서 완결된 갈등/사건을 기록 (예: 인수전 완료, 적 조직 괴멸 등)
- [V63] npc_injuries: NPC가 부상당하면 상태 기록 (경상/중상/위독)
- [V66] entity_destructions: 조직 괴멸/장소 파괴 해당 시 반드시 기록 (이후 재등장 방지, 빈 배열도 가능)
- [V66] npc_personality_changes: NPC 성격/동기 변화 해당 시 반드시 기록 (성격 일관성 유지, 빈 배열도 가능)
- [V66] npc_npc_relationships: NPC 간 관계 해당 시 반드시 기록 (동맹/적대/사제 등, 빈 배열도 가능)
- [V66.1] time_markers: Arc 내 시간 흐름 마커 반드시 기록 (경과 시간, 계절, 시각, 특정 날짜)
- [V66.1] permanent_injuries: NPC 절단/실명/흉터 등 영구 부상 해당 시 반드시 기록 (이후 묘사 일관성 유지)
- [V66.1] companion_changes: NPC가 주인공 일행에 합류/이탈할 때 반드시 기록 (동행자 실종 방지)
- [V66.1] commitments: 약속/맹세/빚 발생 시 반드시 기록 (미이행 약속 추적)
- [V66.1] protagonist_emotion: Arc 종료 시 주인공 감정 상태 기록 (감정 급변 방지, 없으면 빈 객체 {{}})
- [V66.3] npc_dialogue_profiles: NPC 고유 말투/캐치프레이즈 해당 시 반드시 기록 (대화 스타일 일관성 유지, 빈 배열도 가능)
- [V63] npc_movements: NPC가 장소를 이동하면 출발지/도착지 기록
- [V63.1] financial_events: 투자/재벌물에서 환율, 자산, 레버리지, 거래 내역 기록 (비투자 장르는 빈 객체 {{}})
- 해당 사항 없으면 빈 배열 [] 또는 빈 객체 {{}}로 표시

반드시 유효한 JSON만 출력하세요.
"""


# -- Blueprint Ensemble Prompts (from blueprint_ensemble.py) --  [V64.P4]

# Blueprint 생성 프롬프트 템플릿
BLUEPRINT_GENERATION_PROMPT = """
[V60.80 BLUEPRINT ENSEMBLE - {strategy_display}]

당신은 웹소설 에피소드 설계 전문가입니다.
Arc 전술서를 바탕으로 제{ep_num}화 Blueprint를 설계하세요.

╔══════════════════════════════════════════════════════════════╗
║ 🔒 [V61] 주인공 정보 - 반드시 이 이름을 사용하세요!           ║
╠══════════════════════════════════════════════════════════════╣
║ 주인공 이름: {protagonist_name}                               ║
║ → 모든 씬에서 '{protagonist_name}'만 사용하세요               ║
║ → '주인공', '그', '청년' 등 대명사 사용 금지                  ║
╠══════════════════════════════════════════════════════════════╣
{protagonist_instructions}
╚══════════════════════════════════════════════════════════════╝

### [Arc 전술서 - 이번 화 핵심]
{arc_focus}

### [제약 조건]
{constraints}

{strategy_directive}

### [이전 화 정보]
{prev_info}

### [V60.95 고밀도 HUD - 주인공 상태]
{hud_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{pov_constraint}

### [V60.98 씬 프리셋 - 장면/화자 전환 연출]
각 씬에 적합한 프리셋을 선택하세요. 시점 전환을 통해 다채로운 연출이 가능합니다.

| 프리셋 | 용도 |
|--------|------|
| opening_hook | 화 시작, 독자 유입 |
| daily_routine | 일상 묘사, 세계관 노출 |
| tension_build | 긴장감 축적 |
| action_peak | 전투/액션 클라이맥스 |
| emotional_reveal | 감정 폭발, 내면 묘사 |
| dialogue_duel | 설전/협상/대립 |
| villain_scheme | ★악역 시점★ 음모 노출 (예: 악당이 함정 준비) |
| side_glimpse | ★조연 시점★ 주인공 칭송/반응 (예: "저 사람 대체 뭐지?") |
| flashback | 과거 회상 |
| omniscient_hint | ★전지적 시점★ 복선 암시 (예: "그는 아직 몰랐다...") |
| cliffhanger | 화 끝 훅 |
| resolution | 갈등 해소, 정리 |

💡 시점 전환 팁:
- 악당 음모 씬 → villain_scheme (악역 시점으로 위협감 부여)
- 주인공 활약 직후 → side_glimpse (조연 시점으로 "대단해!" 반응)
- 떡밥 투척 → omniscient_hint (전지적 시점으로 독자에게만 정보 제공)

### [출력 형식 - 반드시 JSON만 출력]

{{
    "ep_num": {ep_num},
    "title": "에피소드 제목 (10자 이내)",
    "scene_breakdown": {{
        "scene_1": {{
            "type": "opening_hook",
            "title": "씬 제목",
            "location": "장소",
            "characters": ["등장인물1", "등장인물2"],
            "summary": "씬 요약 (50자 이내)",
            "tension": 5,
            "key_events": ["이벤트1", "이벤트2"]
        }},
        "scene_2": {{"type": "tension_build", ...}},
        "scene_3": {{"type": "action_peak", ...}},
        "scene_4": {{"type": "cliffhanger", ...}}
    }},
    "integrated_scenario": "전체 에피소드 시나리오 (1000자 이상, 씬별 흐름을 자연스럽게 연결)",
    "start_location": "시작 위치",
    "end_location": "종료 위치",
    "time_flow": "시간 흐름 (예: 오전 → 저녁)",
    "ending_hook": "다음 화 연결 훅 (50자 이내)",
    "protagonist_state": {{
        "mood": "감정 상태",
        "injuries": "부상 상태",
        "equipment": ["소지품"]
    }},
    "ending_state": {{
        "location": "이 화 종료 시 정확한 위치",
        "timeline": {{"표현": "종료 시점 (장르별: year/month, period/season 등)"}},
        "protagonist_status": "종료 시 주인공 상태 요약"
    }}
}}

### [V63] 독자 경험 설계
각 씬의 목표 독자 감정:
- 놀라움 / 분노→쾌감(사이다) / 감동 / 긴장 / 궁금증
전체 씬에서 최소 3가지 이상 서로 다른 감정 반응을 유발할 것.
마지막 씬은 반드시 긴장 또는 궁금증으로 끝낼 것 (클리프행어).

### [필수 조건]
1. scene_breakdown은 최소 3개, 최대 5개 씬
2. integrated_scenario는 최소 1000자 이상
3. 이전 화 종료 위치에서 시작해야 함 (위치 불연속 절대 금지!)
4. 정지선(다음 화 내용)을 침범하지 말 것
5. [V60.98] 각 씬에 반드시 type(프리셋) 필드 포함할 것
6. [V60.98] 시점 전환 프리셋(villain_scheme, side_glimpse, omniscient_hint)은 상황에 맞게 적극 활용
7. [V61.5] ending_state 필수 - 다음 화 시작점 정보 (location, timeline, protagonist_status)

### [V67] 모순 방지 - 절대 준수 사항
위에 제공된 [이전 화 정보]에는 이전 에피소드의 Blueprint와 원고가 포함되어 있습니다.
다음 사항을 절대 위반하지 마세요:
1. **사망 캐릭터 재등장 금지**: 이전 원고/Blueprint에서 사망한 캐릭터를 다시 등장시키지 마세요.
2. **이벤트 반복 금지**: 이미 발생한 이벤트(전투, 만남, 획득 등)를 동일하게 반복하지 마세요.
3. **위치/시간 연속성**: 이전 화 종료 시점의 위치와 시간에서 자연스럽게 이어져야 합니다.
4. **아이템/능력 연속성**: 이전에 획득하지 않은 아이템이나 능력을 사용하지 마세요.
5. **관계 연속성**: 이전 원고에서 확립된 캐릭터 관계(적/아군/중립)를 임의로 바꾸지 마세요.
6. **정보 연속성**: 주인공이 아직 모르는 정보를 알고 있는 것처럼 행동시키지 마세요.

반드시 유효한 JSON만 출력하세요.
"""
