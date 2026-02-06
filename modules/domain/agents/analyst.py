"""
#레거시 에이전트 - Analyst
=========================
Stage 2 진짜 주인: FourPhaseArcGenerator (four_phase_arc_generator.py)
이 Analyst의 plan_single_arc_v20은 FourPhase 실패 시 fallback으로만 사용됨.

여전히 사용되는 기능:
- plan_single_volume_v20: Stage 1 Volume Strategy
- enrich_raw_block_async: Raw block enrichment
- stitch_joints: Arc joints stitching
- get_lack_report: Lack report

#레거시 태그: Arc 생성 관련 코드
"""

import json
import re
import os
from .base_agent import BaseAgent
from .state_tracker import StateTracker
from modules.core.constants import HUDKeys
import asyncio

# [V49.4] Structured Output Schema
try:
    from modules.core.response_schemas import ARC_DESIGN_SCHEMA
    SCHEMA_ENABLED = True
except ImportError:
    SCHEMA_ENABLED = False
    ARC_DESIGN_SCHEMA = None

# =================================================================
# V25 고해상도 전략 프롬프트 정의 영역
# =================================================================

# 📂 analyst.py 내부 추가

POST_STITCH_REPAIR_PROMPT = """
[Role] 서사 무결성 용접공 (Causal Joint Welder)
[Task] 병렬 농축된 두 아크(A, B)의 결합부(Joint)를 검사하여 물리적 모순을 해결하고 인과율을 용접하라.

[📐 수술 대상: Joint N]
- Arc A (결말): {arc_a_joint}
- Arc B (도입): {arc_b_joint}

[🚨 용접 가이드라인]
1. 위치 동기화: A의 종료 위치와 B의 시작 위치가 다르면 A를 기준으로 B의 도입부를 수정하라.
2. 상태 보존: A에서 소모한 내공이나 입은 부상이 B의 도입부에 즉시 반영되었는지 확인하라.
3. 엔티티 고정: A에서 등장한 고유 명사(아이템, 지명, 인물 특징)가 B에서도 동일한 규격으로 유지되도록 문장을 보정하라.

[⚠️ Output Format - Strict JSON Only]
{{
    "status": "CLEAR" 또는 "REPAIRED",
    "repaired_joint_b": "모순이 해결된 Arc B의 새로운 도입부(context)",
    "entity_anchors": {{
        "명칭": "설정 내용",
        "..." : "..."
    }},
    "welding_report": "수정된 논리적 근거"
}}
"""


ENRICH_BLOCK_PROMPT_V30 = """
[Role] 서사 무결성 농축 엔진 (Sovereign Causal Enrichment Engine)
[Task] 입력된 '요약 블록'을 3배 농축하고, 다음 아크를 위한 '물리적 전제 조건'을 설계하여 JSON으로 반환하라.


### [🚨 SYSTEM RESTRICTION: NO CHATTER]
        1. 당신은 인간과 대화하는 것이 아니라 JSON 파서와 통신하는 서사 엔진이다.
        2. 답변의 첫 글자는 반드시 {{여야 하며, 마지막 글자는 반드시 }}여야 한다.
        3. 서문, 결문, 설명, 인사말을 단 한 단어라도 포함할 경우 시스템 오류로 간주한다.
        4. 오직 유효한 JSON 데이터만 출력하라.

{genre_prompt}

[🚨 V35.5 S-GRADE 농축 & 용접 강령]
1. 물리적 해상도: 무공의 충돌을 압력, 진동, 관성 등 물리 법칙으로 묘사하라.
2. 상태 그림자(Status Shadow): 이번 사건으로 인해 주인공이 입을 '예상 손실(내공 소모, 부상 부위, 소모한 영약)'을 수치와 텍스트로 산출하라.
3. 용접점 문서(Joint Docs): 이 아크가 끝나는 시점의 주인공 위치, 손에 든 물건, 주변 인물의 생사 여부를 '확정 팩트'로 정리하라.
4. 전략적 의도: 주인공이 이 사건을 통해 얻으려는 '이면의 목적'을 명시하여 지능형 캐릭터를 완성하라.

[🚨 BOUNDARY GUARD: 가변적 서사 이탈 엄금]
1. 미래 정보 오염 방지: 아래 제공된 [Next Block Context]에 명시된 고유 명사나 결과를 단 한 단어도 언급하지 마라.
2. 인과율 락(Lock): 주인공이 아직 얻지 못한 능력(Realm)이나 아이템을 사용하여 문제를 해결하는 '데우스 엑스 마키나'를 창조하지 마라.
3. 팩트 기반 증폭: 새로운 사건을 '창조'하지 말고, 기존 사건의 '물리적 마디'를 $0.1$초 단위로 쪼개어 서술하라.
4. HUD 동기화: 현재 주인공의 상태(Martial HUD)를 초과하는 무위 묘사 발견 시 해당 설계도는 즉시 파기된다.

[📚 V49.3 Few-Shot 학습 예시 - 반드시 참고할 것]

❌ [WRONG - 데우스 엑스 마키나 위반]:
"주인공은 아직 배우지 않은 '천마강신공'의 오의를 터득하여 절대 강자를 물리쳤다."
→ 문제: HUD에 '천마강신공'이 없는데 갑자기 사용. 개연성 제로.

✅ [CORRECT - 보유 능력 활용]:
"주인공은 최근 익힌 '쌍검연무'의 허점을 역으로 이용해 상대의 빈틈을 노렸다.
경지 차이를 지형지물과 기습으로 메웠다."
→ 올바름: HUD에 있는 '쌍검연무'만 사용. 약자가 강자를 이기는 논리적 근거 제시.

❌ [WRONG - 미래 정보 오염]:
"다음 아크에서 만날 '청풍검객'을 대비해 미리 해독약을 준비했다."
→ 문제: 아직 만나지 않은 NPC를 미리 알고 있음. 시간선 오염.

✅ [CORRECT - 현재 정보만 활용]:
"최근 강호에 독문이 활개친다는 소문을 듣고, 만약을 대비해 해독약을 챙겼다."
→ 올바름: 현재 시점에서 알 수 있는 정보만으로 행동의 근거 제시.

❌ [WRONG - 상태 무시]:
"중상을 입은 주인공이 다음 날 아무렇지 않게 비무 대회에 출전했다."
→ 문제: 부상 상태가 갑자기 사라짐. 연속성 붕괴.

✅ [CORRECT - 상태 반영]:
"아직 완치되지 않은 어깨를 감싸며 비무장에 올랐다.
상처가 열릴 위험을 감수한 필사의 선택이었다."
→ 올바름: 이전 상태를 명시적으로 계승하며 서사적 긴장감 추가.

[📦 경계선 데이터]
- [Previous]: {prev_context}
- [Next]: {next_context}
- [🎯 지정 복선]: {seeds_context}

[🎯 현재 농축 대상]
{curr_block}

[⚠️ Output Format - Strict JSON Only]
{{
    "block_id": "기존 ID 보존",
    "title": "기존 제목 보존",
    "content": {{
        "context": "농축된 배경 및 주인공의 전략적 의도",
        "event_villain": "빌런의 정체와 위기 지수(1-10)",
        "solution": "물리 법칙 기반의 정교한 해결책",
        "reward": "획득 자산 및 명성 변화"
    }},
    "joint_docs": {{
        "final_location": "아크 종료 시점의 구체적 장소",
        "physical_inventory": "현재 손에 쥐거나 몸에 지닌 핵심 물품",
        "world_joint": "다음 아크가 즉시 계승해야 할 환경적 변화"
    }},
    "status_shadow": {{
        "internal_energy_loss": "예상 소모량(%)",
        "expected_injuries": "부상 예상 부위 및 정도",
        "item_consumption": ["사용한 소모성 아이템 목록"]
    }}
}}
"""


#region // VOL

# [Stage 1] 10권 전략 수립용 프롬프트
PLAN_VOLUME_PROMPT_V25 = """
[Role] 무협 대서사 전략가 (High-Resolution Sovereign Strategist)
[Task] 제 {vol_no}권(25화 분량)의 전략 보고서를 2,500자 이상의 고밀도로 설계하라.

{genre_prompt}

[전체 구조 가이드 (Structured Context)]
{structured_context}

[🕒 이전 서사의 흐름 (Continuity)]
{previous_context}

[📐 설계할 권역 블록 (Target Blocks)]
{target_blocks}

[🧬 트리트먼트 원본 수혈 데이터 (Narrative Flesh)]
{treatment_raw_part}

[📦 가용 자산 정보 (Asset Library)]
{assets}

[🌍 V60.88 주인공 설정 (Protagonist Configuration)]
{protagonist_config}

[👤 V60.93 주인공 이름 - 반드시 이 이름만 사용!]
주인공 이름: {protagonist_name}
→ 전략 문서에서 반드시 '{protagonist_name}'을 사용하세요!
→ 다른 이름(이현, 강민수 등 임의 이름) 사용 금지!

---

### ⚖️ V25 서사 내면화 (Narrative Agency & Logic)
[CORE IDENTITY] 주인공 및 서사 기조
1. 회/빙/환 정체성 확립: 도입부에서 전생/각성 과정을 '장면'으로 시각화하여 당위성과 정서(복수, 생존 등)를 즉각 확보. 적응기는 너무 길지도, 빠르지도 않게 논리적으로 묘사.
2. 합리적 설계자: 주인공은 철저한 **'합리적 이기주의자'**이자 '능동적 설계자'. 모든 행동은 자신의 이익과 목적 달성을 위한 계산된 수싸움이며, 상황에 휩쓸리지 않고 판을 짠다.
3. Zero-Gap Continuity (직렬 연결): 이전 아크의 마지막 순간에서 단 1초의 생략 없이 즉시 연결(Chain Link). 지난 줄거리 요약 불가.
4. No Static Routine (동적 전개): 정적 루틴(식사, 단순 회상) 금지. 모든 판단과 대화는 이동, 전투, 대치 등 '동적 상황' 속에서 수행하여 밀도를 높인다.
5. Arc 1 필독: 작품의 시작인 경우, 독자가 모른다고 가정하고 상황과 서사의 필연성을 반드시 기술.
6. 당신은 최종 목적지를 향해 가고 있음을 잊지 마십시오. 직전 아크의 결과를 계승하여 현재 아크의 분량을 결정하고, 차후 전개가 자연스럽게 이어지도록 다리를 놓으십시오.


[🧠 V49.3 Chain-of-Thought: 단계별 사고 프로세스]
설계를 시작하기 전에 반드시 아래 단계를 순서대로 수행하라:

**Step 1: 현재 상태 확인**
- 주인공이 현재 보유한 능력 목록은 무엇인가?
- 주인공이 현재 소지한 아이템 목록은 무엇인가?
- 주인공의 현재 부상/내공 상태는 어떠한가?

**Step 2: 목표 분석**
- 이 권에서 주인공이 달성해야 할 목표는 무엇인가?
- 그 목표를 달성하기 위해 필요한 능력/아이템은 무엇인가?

**Step 3: 가능성 검증**
- Step 1의 보유 능력으로 Step 2의 목표가 달성 가능한가?
- 불가능하다면, 어떤 과정을 통해 필요한 것을 획득할 수 있는가?

**Step 4: 설계 조정**
- Step 3에서 불가능으로 판단되면, 목표를 조정하거나 획득 과정을 추가하라.
- "갑자기" 능력이 생기거나, "이미" 보유한 것을 재획득하는 설정은 금지한다.

[📜 V25 매니페스토: 6대 섹션 쿼터제 (Compact)]
1. **핵심 사건 (300자+)**: 권 전체를 관통하는 메인 플롯과 위기 전개.
2. **주인공 설계 (250자+)**: 능동적 목적의식과 판을 짜는 행동 원리(Agency).
3. **무위와 사이다 (100자+)**: 독자에게 카타르시스를 주는 결정적 무력 격차와 파괴력.
4. **인과 및 복선 (100자+)**: 개연성 확보를 위한 논리적 연결고리.
5. **획득 자산 (100자+)**: 결과적으로 얻게 되는 힘, 아이템, 세력.
6. **조연 반응 (150자+)**: 주인공을 향한 세상의 오해, 경악, 착각.

[Output Format] JSON Only
{{
    "vol_no": {vol_no},
    "strategy_doc": "반드시 '문자열'로만 작성하라. 섹션 구분은 [1. 주요 사건] 형태 사용. 이 문자열 내부에 쌍따옴표가 있다면 반드시 이스케이프 처리할 것. (1,000자 이상)",
    "cider_score": 60
}}
"""
#endregion



#region // ARC

# [Stage 2] 가변 페이싱 및 아키타입 통합 프롬프트
PLAN_ARC_PROMPT_V25 = """
[🚨 SYSTEM: HIGH-PRECISION HYBRID STRATEGIST]
{genre_prompt}

████████████████████████████████████████████████████████████████████████████████
█                                                                              █
█   🚨🚨🚨 [V60.38] tactical_doc 분량 필수 조건 - 위반 시 즉시 REJECT 🚨🚨🚨   █
█                                                                              █
█   ⚠️ tactical_doc 총 분량: 최소 (ep_count × 500)자 이상                      █
█   ⚠️ 각 화별 분량: 최소 500자 이상                                           █
█   ⚠️ 1,500자 미만 = CRITICAL REJECT (시스템 자동 거부)                        █
█   ⚠️ 2,000자 미만 = MAJOR 감점                                               █
█                                                                              █
█   💡 TIP: 각 화마다 공간묘사(100자) + 핵심사건(200자) + 상태변화(100자) +     █
█          인과관계(100자) = 최소 500자 확보                                    █
█                                                                              █
████████████████████████████████████████████████████████████████████████████████

### 🚨🚨🚨 0. [CRITICAL] 직전 Arc 종료 상태 - 절대 무시 금지 🚨🚨🚨
**아래 상태는 신성불가침의 진실이다. 이 상태를 무시하거나 리셋하면 즉시 REJECT된다.**

{prev_arc_context}

### 📊 [V60.95 고밀도 HUD - Arc 시작 전 주인공 상태]
{protagonist_hud_state}

**[V60.10 HARD LOCK] 위 상태에서 명시된:**
- 부상/내공: 회복 없이 활동 불가. 회복 장면 필수.
- 소지품: 이미 있으면 다시 획득 금지.
- 위치: 순간이동 금지, 이동 과정 명시.

═══════════════════════════════════════════════════════════════

### 📦 1. 서사 도구 및 자산 (Library & Assets)
- [아키타입]: {archetype_library}
- [원자 패턴]: 도입({intro_library}) / 전개({dev_library}) / 전환({trans_library}) / 결말({ending_library})
- [가용 자산]: {assets}

### 🔒 PROTAGONIST IDENTITY LOCK (V42 Immutable)
- 주인공 고유 이름: {protagonist_name}
- 이 이름은 작품 전체에서 절대 변경되지 않는 불변값이다.
- 위 인물 외를 주인공으로 서술하거나, 주인공 이름을 유사 명칭으로 대체하면 서사 무결성 파괴로 간주한다.

### 📐 2. 서사 맥락 및 연결 (Narrative Window)
- [🧭 대전략 나침반]: {strategic_compass}
- [🔗 전술 연결]: {prev_block} -> [🎯 현재 설계 대상: {curr_block}] -> {next_block}
- [🗺️ 전체 로드맵]: {full_roadmap}
- ⚠️ 직전 Arc 상태는 섹션 0번에서 이미 명시됨. 반드시 참조할 것.

### 🚨 2-1. 연속성 절대 준수 (CONTINUITY ABSOLUTE RULE) [V49.2]
**위 [🕒 실전 연표]에 명시된 직전 Arc의 종료 상태는 성경과 같은 불변의 진실이다.**

1. **소지품 연속성**: 직전 Arc에서 획득/소지한 아이템(무기, 패, 문서 등)은 현재 Arc 시작 시 반드시 소지하고 있어야 한다.
   - 이미 획득한 아이템을 다시 획득하러 가는 설정은 CRITICAL 위반이다.
   - 아이템 소지 상태를 명시적으로 언급하라.

2. **부상 연속성**: 직전 Arc에서 입은 부상/내공 소모는 현재 Arc 도입부에 반드시 반영되어야 한다.
   - 부상 상태에서 무리한 행동은 회복/치료 장면이 선행되어야 한다.
   - "갑자기 멀쩡해지는" 설정은 CRITICAL 위반이다.

3. **위상 연속성**: 직전 Arc에서 획득한 신분/권한/인정은 현재 Arc에서 일관되게 반영되어야 한다.
   - 이미 복권된 인물이 다시 무시당하는 설정은 MAJOR 위반이다.
   - 정보 전파 시간(반나절~하루)을 고려하여 반응을 설계하라.

4. **복장/장비 연속성**: 직전 Arc 종료 시점의 복장/장비 상태가 현재 Arc 시작 시 유지되어야 한다.
   - 화려한 복장에서 갑자기 허름한 복장으로 변경되려면 명확한 서사적 근거가 필요하다.

### 🔢 2-2. 내공 상태 누적 계산 규칙 (V49.6 NEW)
**내공은 Arc를 넘어 누적된다. 다음 공식을 반드시 준수하라:**

- Arc N 시작 내공 = Arc N-1 종료 내공
- Arc N 종료 내공 = Arc N 시작 내공 - (이번 Arc에서 소모한 내공)

**예시 계산:**
- Arc 1: 시작 100% → 소모 30% → 종료 70%
- Arc 2: 시작 70% (Arc 1 종료값 그대로!) → 소모 20% → 종료 50%
- Arc 3: 시작 50% → 회복 +30% (치료/운기조식) → 종료 80%

**🚨 CRITICAL 위반 사례:**
❌ Arc 1 종료 내공 70%인데 → Arc 2 시작을 100%로 설정 (리셋 금지)
❌ Arc 2에서 "내공 20% 소모"라고 했는데 → 종료 내공을 "50%"가 아닌 다른 값으로 기록
❌ Arc 2 시작 내공 70%인데 → "80% 소모"하여 음수 내공 발생

**회복 가능 조건 (명시적 서사 근거 필수):**
- 운기조식 장면 (최소 반나절~하루 필요, 최대 +20~30%)
- 영약/단약 복용 (아이템 소모 필수 기록)
- 비급/심법 수련 (최소 며칠~일주일 필요)

### 🧠 V49.3 Chain-of-Thought: Arc 설계 사고 프로세스
설계를 시작하기 전에 반드시 아래 단계를 순서대로 수행하라:

**Step 1: 직전 Arc 상태 확인**
- 직전 Arc 종료 시 주인공의 위치는 어디인가?
- 직전 Arc 종료 시 주인공이 소지한 아이템은 무엇인가?
- 직전 Arc 종료 시 주인공의 부상/내공 상태는 어떠한가?

**Step 2: 현재 Arc 도입부 설계**
- Step 1의 상태를 그대로 계승하여 첫 화를 시작하라.
- 위치 이동이 필요하면 이동 과정을 명시하라.
- 부상 회복이 필요하면 치료 장면을 선행하라.

**Step 3: 아이템/능력 사용 검증**
- 이 Arc에서 사용하려는 아이템이 Step 1에서 소지 중인가?
- 이 Arc에서 사용하려는 능력이 주인공이 이미 배운 것인가?
- NO라면 → 획득 과정을 먼저 설계하라.

**Step 4: 상태 변화 추적**
- 각 화에서 발생하는 상태 변화를 명시하라.
- Arc 종료 시 상태가 다음 Arc의 시작 조건이 됨을 인지하라.

### 🧬 3. 지정 복선 연출 미션 (Assigned Seeds Mission)
{assigned_seeds_info}

[복선 연출 필달 규칙]
1. **식립(Planting)**: 주인공의 시선이 아닌 '조연의 대사'나 '배경 묘사' 속에 은유적으로 숨길 것.
2. **강화(Echoing)**: 정체를 드러내지 않고 감각(소리, 진동, 문양 등)으로만 환기하여 독자의 기억을 자극할 것.
3. **회수(Harvesting)**: 주인공의 '능동적 판단'과 결합된 결정적 해결책(Solution)으로 연출하여 카타르시스를 극대화할 것.
4. **구체성**: 모든 복선은 반드시 `tactical_doc` 내의 구체적인 '씬(Scene) 이름'과 함께 처리 과정이 기술되어야 함.

### 🛠️ 4. 하이브리드 설계 및 페이싱 강령
1. **패턴 믹싱**: 주 패턴(Primary) 1개와 부 패턴(Secondary) 0~2개를 융합하여 서사의 다층적 구조를 형성하라.
    # 🚨 [Arc 1 특수 규칙]:
   - 만약 `arc_no`가 **1**인 경우, 반드시 `intro_library` 패턴 중 최소 1개를 선택하여 포함하라. (회빙환 정체성 확립)
   # 🚨 [Arc 50 특수 규칙]:
   - 만약 `arc_no`가 **50**인 경우, 반드시 `ending_library` 패턴 중 최소 1개를 선택하여 포함하라. (대서사시의 종지부 및 여운 형성)
2. **DNA 절대 준수**: {curr_block}에 명시된 핵심 사건과 보상은 반드시 포함하되, 방식만 패턴 라이브러리를 통해 변주하라.
3. **가변 페이싱**: Blitz(3~4화), Standard(5화), Epic(6~7화) 가이드에 따라 사건의 밀도를 판단하여 `ep_count`를 결정하라.
4. **합리적 이기주의**: 주인공은 전생/회빙환의 지식을 이용하여 상황을 의도적으로 지배하고 설계해야 함.
5. 번호 절대 준수: {curr_block}에 적힌 Block 번호나 회차 번호는 무시하라. 오직 시스템이 부여한 **{ep_start}**를 첫 번째 회차 번호로 사용하여 beat_sequence를 작성하라. 이를 어길 시 서사 무결성 파괴로 간주한다.

### 📚 V49.3 Arc 설계 Few-Shot 예시

❌ [WRONG - 아이템 중복 획득]:
"제3화: 주인공이 대도를 획득한다" (이미 Arc 1에서 획득함)
→ 문제: 직전 Arc에서 이미 소지한 아이템을 다시 획득. CRITICAL 위반.

✅ [CORRECT - 소지품 연속성]:
"제1화 도입: 허리에 찬 대도의 무게를 느끼며 객잔 문을 열었다."
→ 올바름: 이전 Arc에서 획득한 아이템 소지 상태를 명시적으로 계승.

❌ [WRONG - 부상 상태 무시]:
"제1화: 어제 중상을 입은 주인공이 곧바로 비무에 참가하여 압승했다."
→ 문제: 부상 상태에서 무리한 행동, 회복 과정 생략. CRITICAL 위반.

✅ [CORRECT - 부상 연속성]:
"제1화: 아직 아물지 않은 상처를 억지로 동여매고 비무장에 올랐다.
제2화: 상처가 벌어지며 피가 스며들었지만, 치료는 승부 후로 미뤘다."
→ 올바름: 부상 상태를 계승하고, 무리한 행동의 대가를 서사적으로 활용.

❌ [WRONG - 화 간 모순]:
"제2화: 검을 손에 쥐고 적진에 뛰어들었다"
"제3화: 검을 찾으러 무기고로 향했다"
→ 문제: 단일 Arc 내에서 아이템 상태 모순. MAJOR 위반.

✅ [CORRECT - 화 간 일관성]:
"제2화: 검을 손에 쥐고 적진에 뛰어들었다. 검이 부러지며 전투 종료."
"제3화: 부러진 검 대신 새 무기를 구하러 무기고로 향했다."
→ 올바름: 상태 변화에 명확한 서사적 근거 제시.

{special_instructions}  # 👈 [V27.6 핵심 슬롯] Arc 1/50 규칙이 이곳에 박힙니다.

### [🚨 SYSTEM RESTRICTION: NO CHATTER]
        1. 당신은 인간과 대화하는 것이 아니라 JSON 파서와 통신하는 서사 엔진이다.
        2. 답변의 첫 글자는 반드시 {{여야 하며, 마지막 글자는 반드시 }}여야 한다.
        3. 서문, 결문, 설명, 인사말을 단 한 단어라도 포함할 경우 시스템 오류로 간주한다.
        4. 오직 유효한 JSON 데이터만 출력하라.


### ⚠️ 출력 형식 (Strict JSON Only)
{{
    "arc_no": "{arc_no}",
    "hybrid_composition": {{
        "primary": "주 패턴 명칭",
        "secondary": ["부 패턴 리스트"],
        "mixing_logic": "패턴 조합 및 복선 연출 통합 전략"
    }},
    "pacing_decision": {{
        "chosen_pacing": "Blitz(3-4화) / Standard(5화) / Epic(6-7화) 중 선택",
        "reasoning": "사건 밀도와 긴장감 분석 근거"
    }},
    "ep_count": "{ep_count_suggestion} (시스템 추천) 또는 3~7 중 사건 밀도에 맞게 직접 결정",
    "ep_start": {ep_start},
    "ep_end": "ep_start + ep_count - 1 로 계산",
    "title": "에피소드 묶음 제목",
    "beat_sequence": [
        "제 N화: [패턴/비트] 구체적 실행 액션 및 복선 노출 지점",
        "..."
    ],
    "state_constraints": {{
        "arc_start_state": {{
            "location": "Arc 시작 시 주인공 위치",
            "equipment": ["소지 중인 무기/아이템 목록"],
            "injuries": "부상 상태 (정상/경상/중상)",
            "internal_energy": "내공 상태 (%)"
        }},
        "arc_end_state": {{
            "location": "Arc 종료 시 주인공 위치",
            "equipment": ["종료 시 주인공이 직접 소지하는 아이템만"],
            "injuries": "종료 시 부상 상태",
            "internal_energy": "종료 시 내공 상태 (%)"
        }},
        "protagonist_items": ["주인공이 직접 소지하게 되는 아이템만"],
        "distributed_items": ["주인공이 타인에게 지급/분배한 아이템"],
        "items_consumed": ["이 Arc에서 소모되는 아이템 (금전, 소모품 등)"],
        "relationship_changes": [
            {{"target": "NPC/집단명", "from": "이전 상태", "to": "변경 후 상태", "trigger": "변화 계기", "justification": "서사적 근거"}}
        ],
        "power_changes": {{
            "start_power": 30,
            "end_power": 35,
            "growth_justification": "성장 근거 (수련/비급/각성 등)"
        }},
        "foreshadowings": [
            {{"id": "복선ID", "type": "아이템/인물/사건/능력/비밀", "description": "복선 내용", "expected_payoff": "예상 회수 시점/방법"}}
        ],
        "continuity_checkpoints": [
            "제 N화: [상태 변화] 구체적 변화 내용"
        ]
    }},

    🚨🚨🚨 [V49.6 아이템 분류 규칙 - 필수 준수] 🚨🚨🚨

    ❌ 잘못된 예 (REJECT됨):
    - 주인공이 금화로 강철도를 구매해서 병사들에게 지급
    - items_acquired: ["강철도"]  ← 틀림! 병사들에게 준 것은 주인공 아이템이 아님

    ✅ 올바른 예:
    - 주인공이 금화로 강철도를 구매해서 병사들에게 지급
    - protagonist_items: []  ← 주인공이 직접 갖는 것 없음
    - distributed_items: ["강철도", "돈피 갑옷"]  ← 타인에게 지급
    - items_consumed: ["황금 일천 냥"]  ← 구매에 소모된 금전

    ✅ 올바른 예 2:
    - 주인공이 철혈사자패를 하사받아 허리에 참
    - protagonist_items: ["철혈사자패"]  ← 주인공이 직접 소지
    - distributed_items: []
    - items_consumed: []

    [핵심 구분법]
    - 주인공 허리/품속/손에 있으면 → protagonist_items
    - 타인에게 건네주면 → distributed_items
    - 사용해서 사라지면 → items_consumed

    🔧 [V49.7 품질 추적 필드 - 선택적 작성]

    ▶ relationship_changes (관계 변화):
    - target: 변화 대상 NPC/집단명 (예: "사병들", "팽가 장로들")
    - from: 이전 관계 상태 (적대/무시/의심/중립/경외/충성)
    - to: 변경 후 상태
    - trigger: 변화를 유발한 사건 (예: "비무 승리", "금화 지급")
    - justification: 서사적 근거 (급변 방지)

    예시:
    - 사병들이 "무시" → "경외"로 변하려면 trigger("비무 압승")와 justification("압도적 무력 목격") 필요

    ▶ power_changes (파워 스케일링):
    - start_power: Arc 시작 시 파워 (0-100)
    - end_power: Arc 종료 시 파워 (Arc당 최대 +20 권장)
    - growth_justification: 성장 근거 (수련/비급/영약/각성 중 하나)

    ▶ foreshadowings (복선 설치):
    - id: 복선 식별자 (예: "심마박동독", "가주_비밀")
    - type: 복선 유형 (아이템/인물/사건/능력/비밀/예언)
    - description: 복선 내용
    - expected_payoff: 예상 회수 시점/방법 (5 Arc 이내 권장),
    "tactical_doc": "단순 요약을 절대 금지한다. 제 {ep_start}화부터 {ep_end}화까지 '각 회차별'로 섹션을 명확히 분리하여 [제 N화 전술 설계] 형태로 작성하라.

    ████████████████████████████████████████████████████████████████████
    █ [V60.29] 화별 분할 필수 형식 - 위반 시 REJECT                      █
    ████████████████████████████████████████████████████████████████████

    🔴 반드시 아래 형식으로 각 화를 분리하라:

    [제 {ep_start}화 전술 설계]
    (최소 500자 이상의 상세 내용)
    - 공간 묘사: ...
    - 핵심 사건: ...
    - 상태 변화: ...

    [제 {ep_start}+1화 전술 설계]
    (최소 500자 이상의 상세 내용)
    ...

    (제 {ep_end}화까지 반복)

    🚨 검증 기준:
    - 각 화마다 [제 N화 전술 설계] 헤더 필수
    - 각 화 최소 300자 이상 (500자 권장)
    - 화 순서 연속 필수 ({ep_start}, {ep_start}+1, ..., {ep_end})
    - 화 누락 시 즉시 REJECT

    ████████████████████████████████████████████████████████████████████

    ████████████████████████████████████████████████████████████████████
    █ [V60.40] 화간 상태 체크포인트 - StateLocked 흡수                   █
    ████████████████████████████████████████████████████████████████████

    🔗 각 화는 반드시 아래 형식으로 상태를 추적하라:

    [제 N화 전술 설계]
    ▶ 시작 상태 (이전 화 종료 상태 계승):
       - 위치: {{이전 화 종료 위치}}
       - 내공: {{이전 화 종료 내공}}%
       - 부상: {{이전 화 종료 부상}}
       - 소지품: {{이전 화 종료 소지품}}

    (본문 전개 - 최소 400자)

    ▶ 종료 상태 (다음 화 시작 상태로 전달):
       - 위치: {{이 화 종료 위치}}
       - 내공: {{이 화 종료 내공}}% (±변화량 명시)
       - 부상: {{이 화 종료 부상}}
       - 획득: {{새로 획득한 아이템}}
       - 소모: {{사용/소모한 아이템}}

    ═══════════════════════════════════════════════════════════════════

    🔴 상태 체인 규칙:
    1. 제 {ep_start}화 시작 상태 = 이전 Arc 종료 상태 (state_constraints.arc_start_state)
    2. 제 N화 종료 상태 = 제 N+1화 시작 상태 (반드시 일치)
    3. 제 {ep_end}화 종료 상태 = state_constraints.arc_end_state

    🔴 검증 자동화:
    - 화간 상태 불일치 시 REJECT
    - 내공 변화량 합계 ≠ (시작-종료) 시 REJECT
    - 아이템 획득/소모 추적 불일치 시 REJECT

    ████████████████████████████████████████████████████████████████████

    🚨 [연속성 필수 반영 - V49.2]:
    - 제 {ep_start}화 도입부에 직전 Arc 종료 상태(소지품, 부상, 위치, 복장)를 명시적으로 반영하라.
    - 이미 획득한 아이템을 다시 획득하거나, 부상 상태를 무시하는 설정은 즉시 REJECT된다.
    - 예시: '대도를 허리에 찬 채로 시작', '아직 회복 중인 어깨 부상을 감싸며', '비단옷 차림 그대로'

    🔢 [수치 일관성 필수 규칙 - V60.10]:
    1. 금액/재화: 이전 화에서 획득한 금액을 명시적으로 인용 후 계산하라.
       ❌ "황금 삼천 냥 획득" → 다음 화 "이천 냥 소모" (총액 불명확)
       ✅ "황금 삼천 냥 획득" → 다음 화 "삼천 냥 중 천 냥 소모, 이천 냥 잔여"
    2. 내공/기력: 백분율 계산을 명시적으로 작성하라.
       ❌ "삼할(30%) 보유 → 구푼(9%) 소모 → 이십일 할(210%) 잔여" (산수 오류)
       ✅ "삼할(30%) 보유 → 구푼(9%) 소모 → 이할 일푼(21%) 잔여" (30-9=21)
    3. 부상 추적: 같은 부상의 부위는 Arc 끝까지 일관되게 유지하라.
       ❌ 제N화 "어깨를 스쳤다" → 제N+1화 "전완부 자상 치료" (부위 변경)
       ✅ 제N화 "어깨를 스쳤다" → 제N+1화 "어깨 상처가 아물어가며" (부위 일관)
       ※ 신규 부상은 "제N화에서 새로 입은 [부위] 부상"으로 명시
    4. 수량/개수: 아이템 수량 변화 시 계산 과정을 기록하라.
       ❌ "영약 다섯 알 획득" → "영약 복용 후 세 알 소모" → "남은 영약 네 알" (5-3≠4)
       ✅ "영약 다섯 알 획득" → "영약 세 알 복용" → "남은 영약 두 알" (5-3=2)

    각 회차별 섹션은 반드시 '3개 이상의 핵심 전술 비트(Tactical Beats)'로 구성되어야 하며, 각 비트는 아래 요소를 포함해야 한다:
    (1) 공간의 질감: 장소의 오감 데이터 (냄새, 온도, 소리, 기물 배치).
    (2) 인과의 마디: 인물의 행동이 상황을 반전시키는 0.1초 단위의 세부 공정. (단, 해당 화에 배정된 비트만 전개하고 다음 화 내용을 미리 쓰지 마라.)
    (3) 파동의 전이: 주인공의 행동에 대한 주변 인물들의 경악, 착각, 평판 변화 관찰 리포트.
    (4) 연속성 체크포인트: 해당 화에서 변경되는 상태(아이템 획득/소모, 부상/회복, 위상 변화)를 명시하라.

    [주의] 1개 회차당 최소 800자 이상의 재료를 투입하여, 전체 전술서 분량을 {ep_count} * 800자 이상으로 확보하라. 아키텍트가 10장면을 설계할 수 있는 '충분한 원재료'를 공급하는 것이 목적이다."
}}
"""

#endregion


#region // SELF CRITIC PROMPT
ANALYST_SELF_CRITIC_PROMPT = """
당신은 아크 설계안의 무결성을 검사하는 수석 감사관입니다.

[검사 항목 - 모두 통과해야 PASS]

1. **ep_count 밀도 검사**: 설정한 `ep_count`가 `tactical_doc`의 사건 밀도와 일치하는가?

2. **아키타입 비트 검사**: 패턴 라이브러리의 비트가 tactical_doc에 살아있는가?

3. **[V49.2 신규] 연속성 검사**:
   - 제 {ep_start}화 도입부에 직전 Arc 종료 상태(소지품, 부상, 위치)가 반영되어 있는가?
   - 이미 획득한 아이템을 다시 획득하려는 설정이 있는가? (있으면 FAIL)
   - 부상 상태에서 무리한 행동을 회복/치료 없이 하려는 설정이 있는가? (있으면 FAIL)
   - Arc 내에서 화 사이에 모순이 있는가? (있으면 FAIL)

4. **복장/장비 일관성 검사**:
   - 화마다 복장/장비 묘사가 모순되지 않는가?
   - 갑작스러운 복장 변경에 서사적 근거가 있는가?

5. **[V49.3 신규] state_constraints 일관성 검사**:
   - `state_constraints.arc_start_state`가 직전 Arc의 종료 상태와 일치하는가?
   - `items_acquired`에 있는 아이템이 `arc_end_state.equipment`에 포함되어 있는가?
   - `items_consumed`에 있는 아이템이 `arc_start_state.equipment`에 있었는가?
   - `continuity_checkpoints`가 `tactical_doc`의 상태 변화와 일치하는가?

6. **[V49.7 신규] 품질 추적 필드 검사**:
   - `relationship_changes`가 있으면 from→to 전이가 합리적인가? (무시→충성 직행 FAIL)
   - `power_changes`의 end_power - start_power가 20을 초과하면 FAIL (근거 없이 급성장)
   - `foreshadowings`가 있으면 expected_payoff가 5 Arc 이내인가? (너무 먼 복선 WARNING)

7. **[V60.10 신규] 수치 일관성 검사**:
   - 금액/재화가 화마다 맞는가? (획득-소모=잔여 계산 확인)
   - 내공 백분율 계산이 정확한가? (30%-9%=21%, NOT 210%)
   - 부상 부위가 화마다 일관되는가? (어깨 부상이 전완부로 바뀌면 FAIL)
   - 아이템 수량 변화가 산술적으로 맞는가? (5개-3개=2개)
   - 수치 계산 오류 발견 시 즉시 FAIL 처리

[Output Format - JSON Only]
{{
    "status": "PASS" 또는 "FAIL",
    "feedback": "수정 지시사항",
    "continuity_issues": ["발견된 연속성 문제 목록"],
    "state_constraint_issues": ["발견된 상태 제약 문제 목록"],
    "final_arc": {{ ... }}
}}
"""

#endregion


class Analyst(BaseAgent):
    """
    [V37 Sovereign Strategist - 0124 Manifesto]
    - 3대 지표 분석: 무력(Martial), 경제(Economy), 권위(Authority) 결핍 진단
    - 위버 동력 수혈: 주인공의 욕망을 점화할 '결핍 리포트' 생성
    - 서사 수술: ARC_RECONSTRUCTION을 통한 인과율 보정

    #레거시 노트:
    - Stage 2 Arc 생성: FourPhaseArcGenerator가 진짜 주인
    - plan_single_arc_v20: FourPhase 실패 시 fallback으로만 사용
    - Stage 1 Volume (plan_single_volume_v20): 여전히 활성
    """
    #region //volume planning
    def plan_single_volume_v20(self, vol_no, master_bible, treatment_raw_part, previous_volumes_context="", structured_context="", protagonist_name: str = None):
        """[Stage 1] 10권 전략 수립 (가공 데이터 보존 및 슬라이싱 단일화)"""
        bible_root = master_bible.get('MasterBible', master_bible)
        assets = bible_root.get('AssetLibrary', {})

        # [V61.2 Fix] 주인공 이름 추출 - 장르별 HUD 탐색
        if not protagonist_name:
            try:
                genre = getattr(self.context, 'genre', '') or ''
                protagonist_name = HUDKeys.get_protagonist_name(bible_root, genre)
            except Exception:
                protagonist_name = "주인공"

        # [V60.88] 주인공 설정 추출 (인지 목적, 제약 최소화)
        protagonist_config = bible_root.get('protagonist_config', {})
        world_origin = protagonist_config.get('world_origin', '원시인')
        incarnation_type = protagonist_config.get('incarnation_type', '회귀자')
        protagonist_config_text = f"- 세계 출신: {world_origin}\n- 환생 유형: {incarnation_type}"
        if world_origin == '원시인':
            protagonist_config_text += "\n⚠️ 현대 용어 사용 금지"
        else:
            protagonist_config_text += "\n📝 주인공은 현대 사회를 알고 있음"
        if incarnation_type == '회귀자':
            protagonist_config_text += "\n🔄 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)"
        elif incarnation_type == '빙의자':
            protagonist_config_text += "\n👤 원래 인물의 기억/관계를 의식"
        elif incarnation_type == '환생자':
            protagonist_config_text += "\n👶 전생의 기억이 있음"
        
        # 1. 권역 데이터 통합 추출 (Block 5개 단위)
        # treatment_raw_part가 리스트면 그대로 쓰고, 문자열이면 JSON으로 변환
        if isinstance(treatment_raw_part, str):
            try:
                treatment_data = json.loads(treatment_raw_part)
            except (json.JSONDecodeError, ValueError) as e:
                # [V44] JSON 파싱 실패 경고 추가
                print(f"      ⚠️ [Analyst] treatment 데이터 JSON 파싱 실패: {str(e)[:50]}")
                treatment_data = []  # 변환 실패 시 빈 리스트
        else:
            treatment_data = treatment_raw_part

        target_blocks = treatment_data 
        target_blocks_str = json.dumps(target_blocks, ensure_ascii=False, indent=2)

        # 2. 프롬프트 데이터 안전화 및 주입
        prompt = PLAN_VOLUME_PROMPT_V25.format(
            vol_no=vol_no,
            genre_prompt=self.context.guard.get_v20_purism_prompt(),
            structured_context=self._escape_braces(structured_context),
            previous_context=self._escape_braces(previous_volumes_context),
            target_blocks=self._escape_braces(target_blocks_str),
            treatment_raw_part=self._escape_braces(target_blocks_str),
            assets=self._escape_braces(json.dumps(assets, ensure_ascii=False)),
            protagonist_config=self._escape_braces(protagonist_config_text),  # [V60.88]
            protagonist_name=protagonist_name  # [V60.93]
        )
        
        response = self.ask(prompt, temperature=0.7)
        # [V60.2] DEBUG → 조건부 로깅 (프로덕션에서는 비활성화)
        if os.getenv("DEBUG_MODE", "").lower() == "true":
            print(f"\n--- [Vol {vol_no} AI Raw Response] ---\n{response[:500]}...\n")
        
        # 3. 🚨 결과물 정제 및 안전장치 가동
        result = self._extract_json_robust(response)

        # 🔥 [Vol Safety] AI가 전술(tactical) 키값을 줘도 전략(strategy)으로 강제 변환
        if 'tactical_doc' in result and 'strategy_doc' not in result:
            result['strategy_doc'] = result['tactical_doc']
        
        # [⬇️ 추가할 코드: 필수 키 누락 방지 가드]
        # AI가 cider_score를 누락했을 경우 기본값 0 또는 50을 할당하여 KeyError 방지
        if 'cider_score' not in result:
            print(f"      ⚠️ [Auto-Repair] Vol {vol_no}: 누락된 'cider_score'를 기본값(0)으로 보정했습니다.")
            result['cider_score'] = 0 
            
        # vol_no가 누락되었을 경우를 대비한 보정
        if 'vol_no' not in result:
            result['vol_no'] = vol_no

        # 🚨 [수정 포인트] 가공된 'result' 객체를 그대로 반환해야 합니다!
        return result
    #endregion
    
    #region //arc planning
        

    # ═══════════════════════════════════════════════════════════════
    # [V60] Arc 상태 계승 검증 메서드
    # ═══════════════════════════════════════════════════════════════

    def _validate_arc_state_continuity_v60(self, current_arc: dict, prev_arc: dict) -> dict:
        """
        [V60] 이전 Arc의 종료 상태가 현재 Arc의 시작 상태로 정확히 계승되었는지 검증

        Args:
            current_arc: 현재 Arc 설계 데이터
            prev_arc: 이전 Arc 설계 데이터

        Returns:
            {
                "valid": bool,
                "issues": list,
                "severity": "CRITICAL" | "WARNING" | "NONE",
                "auto_corrections": dict
            }
        """
        if not prev_arc or not isinstance(prev_arc, dict):
            return {"valid": True, "issues": [], "severity": "NONE", "auto_corrections": {}}

        issues = []
        auto_corrections = {}

        # 이전 Arc의 종료 상태
        prev_constraints = prev_arc.get('state_constraints', {})
        prev_end = prev_constraints.get('arc_end_state', {})
        prev_joint = prev_constraints.get('joint_docs', {})

        # 현재 Arc의 시작 상태
        curr_constraints = current_arc.get('state_constraints', {})
        curr_start = curr_constraints.get('arc_start_state', {})

        # 1. 위치 검증
        prev_location = prev_joint.get('final_location') or prev_end.get('location', '')
        curr_location = curr_start.get('location', '')
        if prev_location and curr_location and prev_location != curr_location:
            # 자동 보정 시도
            issues.append(f"CRITICAL: 위치 단절 - Arc 끝 '{prev_location}' → Arc 시작 '{curr_location}'")
            auto_corrections['location'] = prev_location

        # 2. 소지품 검증
        prev_inventory = prev_joint.get('physical_inventory', []) or prev_end.get('equipment', [])
        curr_inventory = curr_start.get('equipment', [])

        if isinstance(prev_inventory, str):
            prev_inventory = [prev_inventory] if prev_inventory else []
        if isinstance(curr_inventory, str):
            curr_inventory = [curr_inventory] if curr_inventory else []

        prev_set = set(prev_inventory) if prev_inventory else set()
        curr_set = set(curr_inventory) if curr_inventory else set()

        missing_items = prev_set - curr_set
        if missing_items:
            issues.append(f"CRITICAL: 아이템 손실 - {missing_items} (이전 Arc에서 소지 중이던 아이템)")
            auto_corrections['missing_items'] = list(missing_items)

        # 3. 내공/상태 검증
        prev_energy = prev_end.get('internal_energy', 0)
        curr_energy = curr_start.get('internal_energy', 0)

        try:
            prev_e = int(str(prev_energy).replace('%', '')) if prev_energy else 0
            curr_e = int(str(curr_energy).replace('%', '')) if curr_energy else 0

            # 회복 없이 증가는 위반 (30% 이상 급증)
            if curr_e > prev_e + 30:
                issues.append(f"WARNING: 내공 급증 감지 ({prev_e}% → {curr_e}%) - 회복 근거 필요")
        except (ValueError, TypeError):
            pass

        # 4. 부상 상태 검증
        prev_injuries = prev_end.get('injuries', []) or prev_end.get('status', '')
        curr_injuries = curr_start.get('injuries', []) or curr_start.get('status', '')

        if prev_injuries and not curr_injuries:
            if '중상' in str(prev_injuries) or '부상' in str(prev_injuries):
                issues.append(f"WARNING: 부상 상태 누락 - 이전 Arc 종료 시 '{prev_injuries}' 상태였으나 현재 Arc 시작에 반영 안 됨")

        # 심각도 결정
        critical_count = sum(1 for i in issues if i.startswith('CRITICAL'))
        if critical_count > 0:
            severity = "CRITICAL"
        elif issues:
            severity = "WARNING"
        else:
            severity = "NONE"

        return {
            "valid": critical_count == 0,
            "issues": issues,
            "severity": severity,
            "auto_corrections": auto_corrections
        }

    def _validate_tactical_doc_continuity_v60(self, tactical_doc: str, ep_count: int) -> dict:
        """
        [V60] Arc 내 화 간 연속성 검증 - 아이템/부상 상태 추적

        Args:
            tactical_doc: 전술 문서 텍스트
            ep_count: 예상 에피소드 수

        Returns:
            {
                "valid": bool,
                "issues": list,
                "item_tracking": dict,
                "injury_tracking": dict
            }
        """
        # [V60.36 FIX] tactical_doc이 dict인 경우 문자열로 변환
        if isinstance(tactical_doc, dict):
            tactical_doc = tactical_doc.get('tactical_doc', '') or str(tactical_doc)
        if not isinstance(tactical_doc, str):
            tactical_doc = str(tactical_doc) if tactical_doc else ''

        issues = []
        item_states = {}  # {item: 'acquired' | 'lost'}
        injury_states = {}  # {ep: 'injured' | 'recovered' | 'normal'}

        for i in range(1, ep_count + 1):
            # 각 화 섹션 추출
            pattern = rf'제\s*{i}\s*화.*?(?=제\s*{i+1}\s*화|$)'
            ep_match = re.search(pattern, tactical_doc, re.DOTALL | re.IGNORECASE)

            if not ep_match:
                continue

            section = ep_match.group(0)

            # 1. 아이템 획득 추적
            acquired_patterns = [
                r'(.+?)(?:을|를)\s*(?:획득|집어\s*들|뽑아\s*들|챙기|주워)',
                r'(.+?)(?:을|를)\s*(?:받|하사받|전달받|넘겨받)',
            ]
            for pattern in acquired_patterns:
                matches = re.findall(pattern, section)
                for item in matches:
                    item = item.strip()
                    if len(item) >= 2 and len(item) <= 15:
                        if item in item_states and item_states[item] == 'lost':
                            issues.append(f"EP{i}: 이미 잃어버린 '{item}' 재획득 시도")
                        item_states[item] = 'acquired'

            # 2. 아이템 손실 추적
            lost_patterns = [
                r'(.+?)(?:을|를)\s*(?:잃|파괴|손상|부러)',
                r'(.+?)(?:이|가)\s*(?:부러지|망가지|사라지)',
            ]
            for pattern in lost_patterns:
                matches = re.findall(pattern, section)
                for item in matches:
                    item = item.strip()
                    if len(item) >= 2 and len(item) <= 15:
                        if item not in item_states or item_states[item] != 'acquired':
                            issues.append(f"EP{i}: 미소지 아이템 '{item}' 손실 시도")
                        item_states[item] = 'lost'

            # 3. 부상 상태 추적
            if re.search(r'중상|부상|다치|피를 흘리', section):
                injury_states[i] = 'injured'
            elif re.search(r'회복|치료|완치|상처가 아물', section):
                injury_states[i] = 'recovered'
            else:
                injury_states[i] = 'normal'

            # 4. 부상 상태 연속성 검증
            if i > 1:
                prev_injury = injury_states.get(i - 1, 'normal')
                curr_injury = injury_states.get(i, 'normal')

                # 부상 상태에서 격렬한 행동
                if prev_injury == 'injured' and curr_injury == 'normal':
                    intense_actions = re.findall(r'전투|비무|격투|도약|비약|질주', section)
                    if len(intense_actions) >= 2:
                        issues.append(f"EP{i}: 부상 미회복 상태에서 과도한 행동 ({len(intense_actions)}회 격렬 행동)")

        return {
            "valid": len([i for i in issues if 'CRITICAL' in i or '재획득' in i or '미소지' in i]) == 0,
            "issues": issues,
            "item_tracking": item_states,
            "injury_tracking": injury_states
        }

    def _auto_correct_joint_docs_v60(self, tactical_doc: str, arc_data: dict) -> dict:
        """
        [V60] 마지막 화 내용에서 joint_docs 자동 추출하여 보정

        Args:
            tactical_doc: 전술 문서 텍스트
            arc_data: Arc 설계 데이터

        Returns:
            보정된 arc_data
        """
        # [V60.36 FIX] tactical_doc이 dict인 경우 문자열로 변환
        if isinstance(tactical_doc, dict):
            tactical_doc = tactical_doc.get('tactical_doc', '') or str(tactical_doc)
        if not isinstance(tactical_doc, str):
            tactical_doc = str(tactical_doc) if tactical_doc else ''

        # 마지막 화 섹션 추출
        ep_sections = re.findall(r'제\s*(\d+)\s*화.*?(?=제\s*\d+\s*화|$)', tactical_doc, re.DOTALL)
        if not ep_sections:
            return arc_data

        # 마지막 화 번호 및 내용 찾기
        last_match = list(re.finditer(r'제\s*(\d+)\s*화', tactical_doc))
        if not last_match:
            return arc_data

        last_ep_start = last_match[-1].start()
        last_section = tactical_doc[last_ep_start:]

        # 1. 최종 위치 추출
        location_patterns = [
            r'(?:도착|도달|들어서|위치한?)\s*(?:곳은?\s*)?([가-힣\w]+(?:전|관|각|루|궁|산|촌|장|성|문)?)',
            r'([가-힣\w]+(?:전|관|각|루|궁|산|촌|장|성|문))(?:에서|에|으로)\s*(?:향하|떠나|이동)',
        ]
        final_location = None
        for pattern in location_patterns:
            match = re.search(pattern, last_section[-500:])  # 마지막 500자에서 검색
            if match:
                final_location = match.group(1)
                break

        # 2. 최종 소지품 추출
        inventory_patterns = [
            r'(?:손에|허리에|품속에|등에)\s*([가-힣\w]+?)(?:을|를|이|가)?\s*(?:들고|쥐고|차고|지니)',
        ]
        final_inventory = []
        for pattern in inventory_patterns:
            matches = re.findall(pattern, last_section)
            for item in matches:
                if len(item) >= 2 and len(item) <= 15 and item not in final_inventory:
                    final_inventory.append(item)

        # 3. arc_data 보정
        if 'state_constraints' not in arc_data:
            arc_data['state_constraints'] = {}
        if 'joint_docs' not in arc_data['state_constraints']:
            arc_data['state_constraints']['joint_docs'] = {}

        joint_docs = arc_data['state_constraints']['joint_docs']

        if final_location:
            existing_location = joint_docs.get('final_location', '')
            if not existing_location or existing_location != final_location:
                print(f"      🔧 [V60] joint_docs 위치 보정: '{existing_location}' → '{final_location}'")
                joint_docs['final_location'] = final_location

        if final_inventory:
            existing_inventory = joint_docs.get('physical_inventory', [])
            if not existing_inventory:
                print(f"      🔧 [V60] joint_docs 소지품 보정: {final_inventory}")
                joint_docs['physical_inventory'] = final_inventory

        return arc_data

    def plan_single_arc_v20(self, arc_no, vol_strategy, prev_block, curr_block, next_block, ep_start,
                            prev_arc_context="", assets=None, full_roadmap="", assigned_seeds=None, feedback="", recent_patterns=None,
                            protagonist_name=None, state_tracker=None):  # [V60.32] 주인공 이름, [V60.95] state_tracker 추가
        """
        #레거시 - FourPhaseArcGenerator.generate()가 Stage 2 진짜 주인
        이 메서드는 FourPhase 실패 시 fallback으로만 호출됨.

        [V31 Sovereign] 3중 캐시 대응: 선 압축 후 설계 방식의 고해상도 전략 엔진
        - 캐시 존재 시: 지침 치환 후 서버 캐시 참조 (비용 90% 절감)
        - 호출 실패 시: 즉시 Full-Text로 자동 복구하여 서사 밀도 보존 (Fallback Safety)
        [V60] Arc 상태 계승 검증 + 화 간 모순 탐지 + Joint Docs 자동 보정
        """
        from google.genai import types
        import json

        # 1. [V38] 패턴 고착화 방지 (Negative Constraints)
        # "2번 이상 연속 사용 금지" -> 직전 패턴(Last Pattern) 재사용 원천 차단
        banned_msg = ""
        if recent_patterns and len(recent_patterns) > 0:
            last_pattern = recent_patterns[-1] # 가장 최근 사용한 패턴
            banned_msg = f"\n[🚨 ABSOLUTE BAN]: 직전에 사용된 서사 패턴 '{last_pattern}'의 재사용을 절대 금지한다. 반드시 다른 아키타입을 선택하여 서사의 변주를 주어라."
            
            # 만약 3회 이상 같은 계열(예: 전투)이 반복되었다면 추가 경고
            if len(recent_patterns) >= 2 and recent_patterns[-1] == recent_patterns[-2]:
                banned_msg += f"\n[🚨 WARNING]: 유사한 전개가 반복되고 있다. 이번 아크에서는 '전투'보다는 '정치', '미스터리', '기연' 등 완전히 다른 장르적 해법을 제시하라."

        # 2. 복선 데이터를 연출 미션 텍스트로 변환 (+ Ban Msg 통합)
        if assigned_seeds:
            mission_list = [f"- [{s.get('action', '지정')}] ID: {s.get('seed_id', 'N/A')} | 논리: {s.get('logic', 'N/A')}" for s in assigned_seeds]
            seeds_info = "### 🎯 이번 아크 서사 미션:\n" + "\n".join(mission_list) + banned_msg
        else:
            seeds_info = f"### 🎯 이번 아크 서사 미션:\n- 특이사항 없음 (순수 줄거리 전개 집중){banned_msg}"

        # 2. 페이싱 계산 (Pre-Compression 로직 유지)
        try:
            clean_arc_no = int(arc_no)
            vol_no = ((clean_arc_no - 1) // 5) + 1
        except (ValueError, TypeError):
            clean_arc_no, vol_no = arc_no, "Unknown"

        # [V60.31] 페이싱 계산 - Block 구조에 맞게 수정
        # [V60.62] 3가지 구조 모두 대응: flatten, nested content, plot_roadmap
        original_guess = 5
        if isinstance(curr_block, dict):
            content_parts = []

            # [V60.62] 1. 최상위 레벨에서 직접 추출 (LLM이 flatten된 구조로 반환)
            for key in ['context', 'event_villain', 'solution', 'reward']:
                if curr_block.get(key) and isinstance(curr_block.get(key), str):
                    content_parts.append(str(curr_block[key]))

            # 2. content 객체 내부에서 추출 (nested 구조)
            content_obj = curr_block.get('content', {})
            if isinstance(content_obj, dict):
                for key in ['context', 'event_villain', 'solution', 'reward']:
                    if content_obj.get(key):
                        content_parts.append(str(content_obj[key]))
            elif isinstance(content_obj, str):
                content_parts.append(content_obj)

            # 3. raw_data 필드에서 추출 (plot_roadmap 구조: force_sync_v25_dna 변환)
            raw_data = curr_block.get('raw_data', {})
            if isinstance(raw_data, dict):
                rd_content = raw_data.get('content', {})
                if isinstance(rd_content, dict):
                    for key in ['context', 'event_villain', 'solution', 'reward']:
                        if rd_content.get(key):
                            content_parts.append(str(rd_content[key]))
                if raw_data.get('title'):
                    content_parts.append(str(raw_data['title']))

            # 3. logic.title에서도 추출 (plot_roadmap 구조)
            logic = curr_block.get('logic', {})
            if isinstance(logic, dict) and logic.get('title'):
                content_parts.append(str(logic['title']))

            # 4. 최상위 title
            if curr_block.get('title'):
                content_parts.append(str(curr_block['title']))

            content_sample = " ".join(content_parts)
            content_len = len(content_sample)

            # 내용 길이/복잡도에 따라 화수 추정
            # - 500자 미만: 간단한 블록 → 3화
            # - 500~1000자: 표준 블록 → 4화
            # - 1000~1500자: 복잡한 블록 → 5화
            # - 1500자 이상: 매우 복잡 → 6화
            if content_len < 500:
                original_guess = 4  # → 3화
            elif content_len < 1000:
                original_guess = 5  # → 4화
            elif content_len < 1500:
                original_guess = 6  # → 5화
            else:
                original_guess = 7  # → 6화 (max)

        # 실제 타겟 화수는 추정치보다 1화 적게 잡아 긴장감 유도 (3~7화 제한)
        target_ep_count = max(3, min(7, original_guess - 1))

        # [V60.31] Block 빈약 경고 - 화당 200자 이상 권장
        # [V60.59] plot_roadmap 구조 대응: raw_data.content에서 추출
        min_content_per_ep = 200
        if isinstance(curr_block, dict):
            content_parts = []

            # [V60.62] 1. 최상위 레벨에서 직접 추출 (LLM이 flatten된 구조로 반환하는 경우)
            for key in ['context', 'event_villain', 'solution', 'reward']:
                if curr_block.get(key) and isinstance(curr_block.get(key), str):
                    content_parts.append(str(curr_block[key]))

            # 2. content 객체 내부에서 추출 (nested 구조인 경우)
            content_obj = curr_block.get('content', {})
            if isinstance(content_obj, dict):
                for key in ['context', 'event_villain', 'solution', 'reward']:
                    if content_obj.get(key):
                        content_parts.append(str(content_obj[key]))
            elif isinstance(content_obj, str):
                content_parts.append(content_obj)

            # 2. raw_data 필드에서 추출 (plot_roadmap 구조: force_sync_v25_dna 변환 결과)
            raw_data = curr_block.get('raw_data', {})
            if isinstance(raw_data, dict):
                rd_content = raw_data.get('content', {})
                if isinstance(rd_content, dict):
                    for key in ['context', 'event_villain', 'solution', 'reward']:
                        if rd_content.get(key):
                            content_parts.append(str(rd_content[key]))
                # raw_data 내 title도 검사
                if raw_data.get('title'):
                    content_parts.append(str(raw_data['title']))

            # 3. logic.title에서도 추출 (plot_roadmap 구조)
            logic = curr_block.get('logic', {})
            if isinstance(logic, dict) and logic.get('title'):
                content_parts.append(str(logic['title']))

            # 4. 최상위 title
            if curr_block.get('title'):
                content_parts.append(str(curr_block['title']))

            content_len = len(" ".join(content_parts))

            if content_len < target_ep_count * min_content_per_ep:
                print(f"      ⚠️ [V60.31] Block 빈약 경고: {content_len}자 / {target_ep_count}화 = 화당 {content_len//target_ep_count}자 (권장 200자+)")

        # 3. [V43] 장르별 라이브러리 로드 - 장르에 맞는 서사 패턴 사용
        current_genre = self._get_current_genre()
        lib_path = self._get_genre_library_path(current_genre)

        if lib_path.exists():
            try:
                lib_data = json.loads(lib_path.read_text(encoding='utf-8'))
                intro_lib_full = json.dumps(lib_data.get("intro_patterns", {}), ensure_ascii=False)
                dev_lib_full = json.dumps(lib_data.get("narrative_archetypes", {}), ensure_ascii=False)
                ending_lib_full = json.dumps(lib_data.get("ending_patterns", {}), ensure_ascii=False)
                trans_lib_full = json.dumps(lib_data.get("transition_patterns", {}), ensure_ascii=False)
                archetype_lib_full = dev_lib_full
                print(f"      📚 [Analyst] {current_genre} 장르 라이브러리 로드 완료")
            except Exception as e:
                print(f"      🚨 [Analyst] 라이브러리 파일 파싱 실패: {e}")
                # [V47 Fix] 빈 dict를 JSON 직렬화 - 이중 이스케이프 방지
                empty_json = json.dumps({}, ensure_ascii=False)
                intro_lib_full = dev_lib_full = ending_lib_full = trans_lib_full = archetype_lib_full = empty_json
        else:
            print(f"      ⚠️ [Analyst] {current_genre} 라이브러리 없음, 기본 사용")
            # 폴백: 기본 라이브러리 시도 [V45 Fix] 루트 config 경로 사용
            from pathlib import Path
            root_config = Path(__file__).parent.parent.parent.parent / "config"
            fallback_path = root_config / "prompts" / "analyst_libraries.json"
            if fallback_path.exists():
                try:
                    lib_data = json.loads(fallback_path.read_text(encoding='utf-8'))
                    intro_lib_full = json.dumps(lib_data.get("intro_patterns", {}), ensure_ascii=False)
                    dev_lib_full = json.dumps(lib_data.get("narrative_archetypes", {}), ensure_ascii=False)
                    ending_lib_full = json.dumps(lib_data.get("ending_patterns", {}), ensure_ascii=False)
                    trans_lib_full = json.dumps(lib_data.get("transition_patterns", {}), ensure_ascii=False)
                    archetype_lib_full = dev_lib_full
                    print(f"      📚 [Analyst] 기본 라이브러리 로드 완료")
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    # [V44] JSON 파싱 실패 경고 추가
                    print(f"      🚨 [Analyst] 기본 라이브러리 파싱 실패: {str(e)[:50]}")
                    # [V47 Fix] 빈 dict를 JSON 직렬화 - 이중 이스케이프 방지
                    empty_json = json.dumps({}, ensure_ascii=False)
                    intro_lib_full = dev_lib_full = ending_lib_full = trans_lib_full = archetype_lib_full = empty_json
            else:
                # [V47 Fix] 빈 dict를 JSON 직렬화 - 이중 이스케이프 방지
                empty_json = json.dumps({}, ensure_ascii=False)
                intro_lib_full = dev_lib_full = ending_lib_full = trans_lib_full = archetype_lib_full = empty_json

        # 3-1. [V42 + V60.32] 주인공 이름 결정 (파라미터 우선, 없으면 Bible 추출)
        final_protagonist_name = protagonist_name  # 파라미터로 받은 값 우선
        if not final_protagonist_name or final_protagonist_name == "주인공":
            try:
                bible_data = self.context.db.load_anchor('bible')
                if bible_data:
                    mb = bible_data.get('MasterBible', bible_data)
                    # [V61.2 Fix] 장르별 HUD 탐색
                    genre = getattr(self.context, 'genre', '') or ''
                    name = HUDKeys.get_protagonist_name(mb, genre)
                    if name and name != '주인공':
                        final_protagonist_name = name
            except Exception as e:
                print(f"      ⚠️ [Analyst] 주인공 이름 추출 실패, 기본값 사용: {e}")
        if not final_protagonist_name:
            final_protagonist_name = "주인공"
        protagonist_name = final_protagonist_name  # 이후 코드 호환

        # [V60.95] 고밀도 HUD 컨텍스트 구축
        hud_context = ""
        if state_tracker and ep_start > 1:
            try:
                prev_ep = ep_start - 1
                prev_state = state_tracker.get_state_at_episode(prev_ep) if hasattr(state_tracker, 'get_state_at_episode') else None
                if prev_state:
                    state_dict = prev_state.to_dict() if hasattr(prev_state, 'to_dict') else {}
                    hud_lines = [f"[Arc 시작 전 주인공 상태 - 제{prev_ep}화 종료 시점]"]
                    for k in ['location', 'hp', 'mp', 'martial_level', 'status', 'injuries']:
                        if k in state_dict and state_dict[k]:
                            hud_lines.append(f"  {k}: {state_dict[k]}")
                    items = state_dict.get('items', [])
                    if items:
                        hud_lines.append(f"  보유 아이템: {', '.join(items[:8])}")
                    hud_context = "\n".join(hud_lines)
            except Exception as e:
                hud_context = f"(HUD 로드 오류: {str(e)[:30]})"

        # 4. 공통 데이터셋 조립 (데이터 이스케이프 적용)
        safe_data = {
            "genre_prompt": self.context.guard.get_v20_purism_prompt(),
            "protagonist_name": protagonist_name,  # V42 LOCK
            "strategic_compass": self._escape_braces(vol_strategy),
            "prev_arc_context": self._escape_braces(prev_arc_context) or "시작점",
            "prev_block": self._escape_braces(json.dumps(prev_block, ensure_ascii=False)) if prev_block else "시작점",
            "curr_block": self._escape_braces(json.dumps(curr_block, ensure_ascii=False)),
            "next_block": self._escape_braces(json.dumps(next_block, ensure_ascii=False)),
            "assigned_seeds_info": self._escape_braces(seeds_info),
            "arc_no": clean_arc_no,
            "vol_no": vol_no,
            "ep_start": ep_start,
            "ep_end": ep_start + target_ep_count - 1,
            "ep_count": target_ep_count,  # [V60.36 FIX] 템플릿에서 사용하는 ep_count 추가
            "assets": self._escape_braces(json.dumps(assets, ensure_ascii=False)) if assets else "{}",
            "full_roadmap": self._escape_braces(full_roadmap),
            "protagonist_hud_state": self._escape_braces(hud_context) if hud_context else ""  # [V60.95] 고밀도 HUD
        }

        # 5. 설계 및 자기 비판 루프 (최대 3회 재시도)
        max_retries = 3
        # [V60.31] 가변 페이싱: 권장값만 제시, LLM이 사건 밀도로 최종 결정
        pacing_guide = f"시스템 권장: {target_ep_count}화 (Blitz:2-3 / Standard:3-4 / Epic:5-6 중 사건 밀도에 맞게 조정 가능)"
        current_feedback = feedback if feedback else pacing_guide
        final_arc_data = None

        for attempt in range(max_retries):
            # [V60.31] 템플릿의 ep_count_suggestion 변수를 동적으로 치환
            adjusted_prompt_tpl = PLAN_ARC_PROMPT_V25.replace("{ep_count_suggestion}", str(target_ep_count))
            
            # 6. [API 호출 분기 로직]
            try:
                if self.cache_name:
                    # ✅ Case A: 캐시 활성 시에만 지침을 치환하여 전송 (토큰 절약 핵심)
                    cache_safe_data = safe_data.copy()
                    placeholder = "[CACHED: Narrative Patterns Library Active - Refer to system memory]"
                    cache_safe_data.update({
                        "intro_library": placeholder, "dev_library": placeholder,
                        "ending_library": placeholder, "trans_library": placeholder,
                        "archetype_library": placeholder,
                        "special_instructions": f"\n[🚨 PACING GUIDE]: 권장 {target_ep_count}화 (사건 밀도에 따라 3~7화 범위 내 조정 가능)"
                    })
                    prompt = adjusted_prompt_tpl.format(**cache_safe_data)
                    if attempt > 0 or feedback: 
                        prompt += f"\n\n🚨 [FEEDBACK]: {current_feedback}"
                    
                    # [V49.4] Structured Output Schema 적용
                    # [V49.6] 온도 상향: 0.4 → 0.5 (추론력 강화)
                    config_params = {
                        "cached_content": self.cache_name,  # 🔥 캐시 참조
                        "temperature": 0.5,
                        "max_output_tokens": 8192,
                        "response_mime_type": "application/json"
                    }
                    if SCHEMA_ENABLED and ARC_DESIGN_SCHEMA:
                        config_params["response_schema"] = ARC_DESIGN_SCHEMA

                    response = self.client.models.generate_content(
                        model=self.primary_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(**config_params)
                    )
                    draft_result = self._extract_json_robust(response.text)
                else:
                    raise Exception("No Cache Found")

            except Exception as e:
                # ⚠️ Case B: 캐시가 없거나 호출 실패 시 즉시 Full-Text로 복구 (품질 보존)
                if self.cache_name:
                    print(f"      ⚠️ [Analyst] 캐시 호출 실패. 일반 모드 전환: {str(e)[:50]}")
                
                full_safe_data = safe_data.copy()
                full_safe_data.update({
                    "intro_library": self._escape_braces(intro_lib_full),
                    "dev_library": self._escape_braces(dev_lib_full),
                    "ending_library": self._escape_braces(ending_lib_full),
                    "trans_library": self._escape_braces(trans_lib_full),
                    "archetype_library": self._escape_braces(archetype_lib_full),
                    "special_instructions": f"\n[🚨 PACING GUIDE]: 권장 {target_ep_count}화 (사건 밀도에 따라 3~7화 범위 내 조정 가능)"
                })
                prompt = adjusted_prompt_tpl.format(**full_safe_data)
                if attempt > 0: prompt += f"\n\n🚨 [FEEDBACK]: {current_feedback}"

                # [V49.4] 일반 API 호출 (Structured Schema 적용)
                # [V49.7] 온도 점진적 상향: 0.5 → 0.6 → 0.7 (재시도 시 창의적 접근 유도)
                schema = ARC_DESIGN_SCHEMA if SCHEMA_ENABLED else None
                temp = 0.5 if attempt == 0 else (0.6 if attempt == 1 else 0.7)
                draft_result = self._extract_json_robust(self.ask(prompt, temperature=temp, response_schema=schema))

            # 7. [V60.31] 가변 페이싱: LLM이 결정한 ep_count 존중 (3~7 범위 내)
            llm_ep_count = draft_result.get("ep_count")
            if isinstance(llm_ep_count, str):
                # "4 (시스템 추천)" 같은 형태에서 숫자 추출
                import re
                match = re.search(r'(\d+)', str(llm_ep_count))
                llm_ep_count = int(match.group(1)) if match else target_ep_count
            elif not isinstance(llm_ep_count, int):
                llm_ep_count = target_ep_count

            # [V60.70] chosen_pacing과 ep_count 강제 동기화 (자기모순 방지)
            pacing_decision = draft_result.get("pacing_decision", {})
            chosen_pacing = pacing_decision.get("chosen_pacing", "") if isinstance(pacing_decision, dict) else ""
            chosen_pacing_lower = chosen_pacing.lower() if isinstance(chosen_pacing, str) else ""

            # chosen_pacing에 따른 ep_count 범위 강제
            if "epic" in chosen_pacing_lower:
                pacing_min, pacing_max = 6, 7
            elif "standard" in chosen_pacing_lower:
                pacing_min, pacing_max = 5, 5
            elif "blitz" in chosen_pacing_lower:
                pacing_min, pacing_max = 3, 4
            else:
                pacing_min, pacing_max = 3, 7  # 기본값

            # ep_count가 chosen_pacing 범위를 벗어나면 강제 조정
            if llm_ep_count < pacing_min or llm_ep_count > pacing_max:
                corrected_ep_count = max(pacing_min, min(pacing_max, llm_ep_count))
                print(f"      🔧 [V60.70] 자기모순 교정: chosen_pacing={chosen_pacing} 인데 ep_count={llm_ep_count} → {corrected_ep_count}화로 강제 조정")
                llm_ep_count = corrected_ep_count

            # 범위 제한 (3~7화)
            actual_ep_count = max(3, min(7, llm_ep_count))
            if actual_ep_count != target_ep_count:
                print(f"      📊 [V60.31] 가변 페이싱: 권장 {target_ep_count}화 → LLM 결정 {actual_ep_count}화")

            # 비트수를 LLM 결정 ep_count에 맞춤
            beats = draft_result.get("beat_sequence", [])
            if len(beats) != actual_ep_count:
                if len(beats) > actual_ep_count:
                    # 넘치는 비트는 마지막에 통합
                    combined = " / ".join(beats[actual_ep_count-1:])
                    beats = beats[:actual_ep_count-1] + [f"[통합 전개]: {combined}"]
                else:
                    # 부족한 비트는 서사 빌드업으로 채움
                    while len(beats) < actual_ep_count: beats.append("서사적 긴장감 고조 및 빌드업 수행")
                draft_result["beat_sequence"] = beats

            # 자기 비판 감사 (Self-Critic) 호출
            critic_input = f"{ANALYST_SELF_CRITIC_PROMPT}\n[Draft to Review]: {json.dumps(draft_result, ensure_ascii=False)}"
            audit_result = self._extract_json_robust(self.ask(critic_input, temperature=0.2))

            if audit_result.get("status") == "PASS":
                final_arc_data = draft_result
                final_arc_data["_actual_ep_count"] = actual_ep_count  # [V60.31] 가변 페이싱 결과 저장
                break
            current_feedback = audit_result.get("feedback", "밀도 및 개연성 보강 필요")

        # 8. 메타데이터 최종 동기화 및 반환 (인과율 유지)
        if not final_arc_data:
            final_arc_data = draft_result
            final_arc_data["_actual_ep_count"] = actual_ep_count  # [V60.31]

        # [V60.31] 가변 페이싱: LLM 결정 ep_count 사용
        final_ep_count = final_arc_data.get("_actual_ep_count", target_ep_count)
        final_arc_data.update({
            "arc_no": clean_arc_no,
            "vol_no": vol_no,
            "ep_start": ep_start,
            "ep_count": final_ep_count,
            "ep_end": ep_start + final_ep_count - 1
        })
        if "_actual_ep_count" in final_arc_data:
            del final_arc_data["_actual_ep_count"]  # 임시 키 제거
        self._normalize_arc_output(final_arc_data, ep_start, final_ep_count)

        # 9. [V49.3] StateTracker를 통한 상태 일관성 검증
        state_issues = self._validate_arc_with_state_tracker(final_arc_data)
        if state_issues:
            print(f"      ⚠️ [Analyst] StateTracker 검증 이슈 발견: {len(state_issues)}건")
            # 검증 이슈를 Arc 데이터에 첨부 (Director/ContinuityInspector 참조용)
            final_arc_data['state_tracker_issues'] = state_issues
            # Critical 이슈가 있으면 tactical_doc에 경고 주입
            critical_issues = [i for i in state_issues if i.get('severity') in ['critical', 'major']]
            if critical_issues:
                warning_text = "\n\n⚠️ [STATE TRACKER WARNING]:\n"
                for issue in critical_issues[:3]:  # 최대 3개
                    warning_text += f"- [{issue['severity'].upper()}] {issue['description']}\n"
                if 'tactical_doc' in final_arc_data and isinstance(final_arc_data['tactical_doc'], str):
                    final_arc_data['tactical_doc'] = warning_text + final_arc_data['tactical_doc']

        # ═══════════════════════════════════════════════════════════════
        # 10. [V60] Arc 상태 계승 검증 + 화 간 모순 탐지 + Joint Docs 보정
        # ═══════════════════════════════════════════════════════════════

        # 10-1. 이전 Arc 데이터 로드
        prev_arc_data = None
        if clean_arc_no > 1:
            try:
                arcs_anchor = self.context.db.load_anchor('arcs')
                if arcs_anchor and isinstance(arcs_anchor, dict):
                    prev_arc_data = arcs_anchor.get(f'arc_{clean_arc_no - 1}')
            except Exception as e:
                print(f"      ⚠️ [V60] 이전 Arc 로드 실패: {e}")

        # 10-2. Arc 상태 계승 검증
        if prev_arc_data:
            continuity_result = self._validate_arc_state_continuity_v60(final_arc_data, prev_arc_data)
            if continuity_result['issues']:
                print(f"      🔍 [V60] Arc 상태 계승 검증: {continuity_result['severity']}")
                for issue in continuity_result['issues'][:3]:
                    print(f"         - {issue}")

                # 자동 보정 적용
                if continuity_result['auto_corrections']:
                    if 'state_constraints' not in final_arc_data:
                        final_arc_data['state_constraints'] = {}
                    if 'arc_start_state' not in final_arc_data['state_constraints']:
                        final_arc_data['state_constraints']['arc_start_state'] = {}

                    start_state = final_arc_data['state_constraints']['arc_start_state']

                    if 'location' in continuity_result['auto_corrections']:
                        start_state['location'] = continuity_result['auto_corrections']['location']
                        print(f"      🔧 [V60] 시작 위치 자동 보정: {start_state['location']}")

                    if 'missing_items' in continuity_result['auto_corrections']:
                        existing = start_state.get('equipment', [])
                        if isinstance(existing, str):
                            existing = [existing] if existing else []
                        existing.extend(continuity_result['auto_corrections']['missing_items'])
                        start_state['equipment'] = list(set(existing))
                        print(f"      🔧 [V60] 시작 소지품 자동 보정: {start_state['equipment']}")

                # 검증 결과 첨부
                final_arc_data['v60_continuity_check'] = continuity_result

        # 10-3. Arc 내 화 간 모순 탐지
        tactical_doc = final_arc_data.get('tactical_doc', '')
        if tactical_doc:
            doc_continuity = self._validate_tactical_doc_continuity_v60(tactical_doc, final_ep_count)
            if doc_continuity['issues']:
                print(f"      🔍 [V60] 화 간 연속성 검증: {len(doc_continuity['issues'])}건 이슈")
                for issue in doc_continuity['issues'][:3]:
                    print(f"         - {issue}")

                # 경고 주입
                warning_text = "\n\n⚠️ [V60 CONTINUITY WARNING]:\n"
                for issue in doc_continuity['issues'][:5]:
                    warning_text += f"- {issue}\n"
                final_arc_data['tactical_doc'] = warning_text + tactical_doc

            final_arc_data['v60_doc_continuity'] = doc_continuity

        # 10-4. Joint Docs 자동 추출 보정
        if tactical_doc:
            final_arc_data = self._auto_correct_joint_docs_v60(tactical_doc, final_arc_data)

        return final_arc_data






    #endregion

    def _normalize_arc_output(self, arc_data, ep_start, ep_count):
        """아크 출력의 회차 표기 및 분량 메타를 정규화한다."""
        if not isinstance(arc_data, dict):
            return

        # 1) beat_sequence 회차 표기 강제 정규화 (잘못된 한글 서수 오타 방지)
        beats = arc_data.get("beat_sequence", [])
        if isinstance(beats, list):
            normalized = []
            for i, beat in enumerate(beats):
                expected_ep = ep_start + i
                if isinstance(beat, str):
                    # "제 X화" 접두를 제거하고 표준 접두로 재조립
                    m = re.match(r"^\s*제\s*.*?화[: ]\s*(.*)$", beat)
                    rest = m.group(1) if m else beat.strip()
                    normalized.append(f"제 {expected_ep}화: {rest}".strip())
                else:
                    normalized.append(beat)
            arc_data["beat_sequence"] = normalized

        # 1-1) tactical_doc 회차 헤더 정규화 (전술 설계 제목 오타 방지)
        tactical = arc_data.get("tactical_doc")
        if isinstance(tactical, str) and isinstance(ep_start, int) and isinstance(ep_count, int):
            expected_eps = list(range(ep_start, ep_start + ep_count))
            it = iter(expected_eps)

            def _repl(match):
                try:
                    n = next(it)
                except StopIteration:
                    return match.group(0)
                return f"[제 {n}화 전술 설계]"

            tactical = re.sub(r"\[제\s*.*?화 전술 설계\]", _repl, tactical)
            arc_data["tactical_doc"] = tactical

        # 2) 분량 메타 키를 ep_count로 통일 (중복/불일치 방지)
        length_keys = {"arc_length_chapters", "total_chapters_estimate", "arc_duration_episodes"}

        def _walk(node):
            if isinstance(node, dict):
                for k in list(node.keys()):
                    if k in length_keys:
                        node[k] = str(ep_count)
                    else:
                        _walk(node[k])
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(arc_data)

        # 3) 명칭/아이템 표준화 - Bible의 alias_map 기반 (V43: 하드코딩 제거)
        # 특정 작품에 종속된 하드코딩(팽명→팽무진, 대방도→혼철대도) 제거
        # 필요 시 Bible의 'alias_map' 또는 'name_corrections' 섹션에서 동적으로 로드
        pass  # 명칭 표준화는 Bible 데이터로 처리

    #region // master bible recovery
    def total_absolute_recovery_v20(self, draft_contents, treatment_content=""):
        """[Phase 0] 시점 기반 역사 복구 및 DNA Sync (풀 버전)"""
        
        # [🔥 중요] 원고가 너무 길 경우: 앞부분(설정) + 뒷부분(최신 상태) 병합
        compact_draft = ""
        if len(draft_contents) > 60000:
            compact_draft = draft_contents[:10000] + "\n\n...[중략: 서사 중간 생략]...\n\n" + draft_contents[-50000:]
        else:
            compact_draft = draft_contents

        template = """
        [Role] V20 서사 DNA 시퀀서 (DNA Sequencer & Auditor)
        [Task] 원고(역사)와 트리트먼트(설계)를 융합하여 1:1 무결성 '마스터 바이블'을 구축하라.
                **현재 시점의 물리적 진실과 세간의 인식을 엄격히 분리하고, 누락된 NPC 설정을 자율적으로 보완하라.**

        [🛡️ V20 시간선 정합성 절대 지침]
        1. **시점 인식**: 제공된 원고의 마지막 화수가 몇 화인지 파악하라.
        2. **HUD 분리 정산**: 
            - 만약 원고가 0화(또는 1화 시작 전)라면, 'MartialHUD'는 반드시 트리트먼트의 'Block 1' 시점의 비참한 초기 상태로 설정하라.
            - 주인공의 최종 목표(탈규의 경지, 무한 자금 등)는 절대 HUD에 넣지 말고, 'Final_Goal_State'라는 별도 섹션에 보관하라.
        3. **실시간 동기화**: 원고가 이미 진행 중이라면, '마지막 화'에서 묘사된 물리적 상태만을 HUD에 반영하라.

        [📑 원고 데이터 (Actual History)]
        {draft_data}

        [🧬 트리트먼트 소스 (Standard Source)]
        {treatment_data}

        [🚨 S-Grade 통합 정산 강령 - 단 하나의 조항도 누락 금지]
        1. **현재 시점 확정**: 원고의 마지막 화수를 기준으로 서사의 현 위치를 확정하라.
        2. **역사 기록 (RecoveredEvents)**: 원고의 핵심 사건을 각 화당 한 문장으로 압축하여 박제하라.
        3. **DNA 1:1 이식 (plot_roadmap)**: [🧬 트리트먼트]에 포함된 모든 Block(Block 1부터 마지막 Block까지)의 제목과 핵심 목표를 1:1로 이식하라.
        4. **HUD 추출 우선순위**: 주인공 상태는 원고 마지막 장면 근거, 원고 없으면 트리트먼트 Block 1 채택.
        5. **다층 HUD 정산**: actual_truth(진실)와 public_reputation(세간의 인식)을 철저히 분리하라.
        6. **자율적 로어 생성**: 조연의 무공/성격 누락 시 문파 설정에 근거해 개연성 있게 보완하라.
        7. **복선 관리 (Seeds)**: 5대 SEEDS를 규격에 맞춰 박제하고 원고 내 활성화 여부를 반영하라.

        [Output Format: JSON Only]
        {{
            "MasterBible": {{
                "MetaInfo": {{ "title": "...", "genre": "...", "logline": "..." }},
                "RecoveredEvents": [ {{ "ep": 1, "event": "...", "impact": "..." }} ],
                "MartialHUD": {{ 
                    "Protagonist": {{
                        "actual_truth": {{
                            "alias": "별호", 
                            "rank": "신분",
                            "realm": "물리적 경지", 
                            "internal_energy": "내공 수치", 
                            "martial_arts": ["보유 무공 목록"],
                            "equipment": "장비",
                            "wealth": "자금"
                        }},
                        "public_reputation": {{ 
                            "identity": "세간의 호칭", 
                            "realm": "인식상 경지" 
                        }},
                        "knowledge_map": {{ "knows_truth": [], "misled": [] }}
                    }}
                }},
                "Final_Goal_State": {{ "target_realm": "...", "target_wealth": "..." }},
                "AssetLibrary": {{ 
                    "Key_NPCs": [ {{ "name": "...", "role": "...", "desc": "..." }} ], 
                    "Key_Items": [] 
                }},
                "Seeds": [ {{ "id": "S-001", "category": "...", "description": "...", "status": "active" }} ],
                "plot_roadmap": [ {{ "block_no": 1, "logic": {{ "title": "...", "objective": "..." }} }} ]
            }}
        }}
        """
        # 3. 모든 동적 데이터에 _escape_braces 적용 후 주입
        prompt = template.format(
            draft_data=self._escape_braces(compact_draft),
            treatment_data=self._escape_braces(treatment_content[:15000])
        )

        response = self.ask(prompt, temperature=0.3) 
        return self._extract_json_robust(response)
    #endregion

    def design_volume_strategy(self, bible_context, roadmap_data):
        """[Stage 1] 50개 아크 배분 전략 (f-string 보안 패치 적용)"""
        
        # 1. 템플릿 정의 (JSON 예시 부분은 {{ }}로 이중 처리하여 .format 충돌 방지)
        template = """
        [Role] 전설적인 웹소설 기획자
        [Task] 50개 서사 블록을 분석하여 10권(Volumes) 분량의 분권 전략을 수립하라.
        
        [🚨 CRITICAL RULES]
        - 모든 응답은 반드시 지정된 JSON 스키마를 100% 준수해야 함.
        - 특히 'vol_no', 'title', 'start_arc', 'end_arc' 키는 하나라도 누락 시 데이터 주권이 파기됨.
        - 결과는 반드시 아래의 리스트 형식으로만 반환하라.
        
        [JSON Format Example]
        [ {{ "vol_no": 1, "title": "...", "start_arc": 1, "end_arc": 5 }}, ... ]
        [성경 정보]
        {bible_info}

        [로드맵]
        {roadmap_info}
        """

        # 2. 데이터 안전화 및 주입
        prompt = template.format(
            bible_info=self._escape_braces(json.dumps(bible_context, ensure_ascii=False)),
            roadmap_info=self._escape_braces(json.dumps(roadmap_data, ensure_ascii=False))
        )

        response = self.ask(prompt, temperature=0.5)
        return self._extract_json_robust(response)

    def plan_batch_arcs_v25(self, batch_no, vol_strategy, blueprint_str, prev_context, assets):
        """[V25 Patch] 배치 설계용 파라미터 강제 보정"""
        # 이 메서드는 구형 규격이므로, PLAN_ARC_PROMPT_V25 대신 내부 간이 프롬프트 사용 권장
        # 혹은 필요한 모든 더미 데이터를 생성하여 V25 프롬프트에 주입
        return self.plan_single_arc_v20(
            arc_no=batch_no, 
            vol_strategy=vol_strategy, 
            prev_block={}, 
            curr_block={"raw": blueprint_str}, 
            next_block={}, 
            ep_start=1, 
            prev_arc_context=prev_context, 
            assets=assets, 
            full_roadmap="Batch Mode"
        )




    async def enrich_raw_block_async(self, raw_block, prev_block=None, next_block=None, assigned_seeds=None, transfused_history=""):
        """[V35.5 Phase 2] safe_prev를 effective_prev로 진화시킨 농축 엔진"""
        
        # 1. 현재 블록 및 주변 블록 이스케이프 (기존 safe_prev 로직 포함)
        safe_curr = self._escape_braces(json.dumps(raw_block, ensure_ascii=False))
        safe_next = self._escape_braces(json.dumps(next_block, ensure_ascii=False)) if next_block else "서사 종결점"
        safe_seeds = self._escape_braces(json.dumps(assigned_seeds, ensure_ascii=False)) if assigned_seeds else "없음"

        # 2. 🚨 safe_prev의 진화: effective_prev (수혈 우선 순위 결정)
        # transfused_history(수혈된 실제 역사)가 있다면 그것을 최우선으로 사용합니다.
        if transfused_history and len(transfused_history) > 10:
            # 수혈 데이터는 이미 가공된 텍스트이므로 그대로 사용하거나 추가 이스케이프 적용
            effective_prev = f"[🚨 확정된 실제 과거 역사]:\n{transfused_history}"
        else:
            # 수혈 데이터가 없을 때만 원본 DNA(prev_block)를 변환하여 사용 (이것이 기존의 safe_prev 역할입니다)
            effective_prev = self._escape_braces(json.dumps(prev_block, ensure_ascii=False)) if prev_block else "서사 시작점"

        # 3. 프롬프트 조립
        # ENRICH_BLOCK_PROMPT_V30의 {prev_context} 자리에 effective_prev를 주입합니다.
        prompt = ENRICH_BLOCK_PROMPT_V30.format(
            genre_prompt=self.context.guard.get_v20_purism_prompt(),
            curr_block=safe_curr,
            prev_context=effective_prev, # 👈 safe_prev의 진화형
            next_context=safe_next,
            seeds_context=safe_seeds
        )

        # 4. 실행 루틴
        loop = asyncio.get_running_loop()
        try:
            raw_res = await loop.run_in_executor(None, lambda: self.ask(prompt, temperature=0.3))
            enriched_result = self._extract_json_robust(raw_res)
            
            # 메타데이터 보존 가드
            if "block_id" not in enriched_result: enriched_result["block_id"] = raw_block.get("block_id")
            if "title" not in enriched_result: enriched_result["title"] = raw_block.get("title")
                
            return enriched_result

        except Exception as e:
            print(f"      🚨 [Enrich Critical Error] {e}")
            return raw_block # 실패 시 원본 DNA 반환

    
    def analyze_context(self, mode="GENERAL", **kwargs):
        """
        [V35 Manifesto] 에이전트 간 조율 및 아크 긴급 수술 로직 (Surgery Room)
        """
        # 1. [V35] 아크 긴급 수술 모드 발동
        if mode == "ARC_RECONSTRUCTION":
            prev_arc = kwargs.get('prev_arc')
            curr_arc = kwargs.get('curr_arc')
            next_arc = kwargs.get('next_arc')
            feedback = kwargs.get('feedback')

            self.ui_log("👨‍⚕️ [Analyst] 아크 인과관계 수술 및 5배 농축 공정을 시작합니다.")

            # 🔧 [Guard] 이스케이프 누적 방지: tactical_doc만 안전 정규화
            def _normalize_tactical_doc_for_prompt(arc):
                if not arc or not isinstance(arc, dict):
                    return arc
                tactical = arc.get("tactical_doc")
                if isinstance(tactical, str):
                    normalized = tactical
                    # 이중 이스케이프를 단계적으로 완화
                    for _ in range(2):
                        normalized = normalized.replace("\\\\n", "\\n").replace("\\\\t", "\\t")
                    normalized = normalized.replace("\\n", "\n").replace("\\t", "\t")
                    if normalized != tactical:
                        arc = arc.copy()
                        arc["tactical_doc"] = normalized
                return arc

            prev_arc = _normalize_tactical_doc_for_prompt(prev_arc)
            curr_arc = _normalize_tactical_doc_for_prompt(curr_arc)
            next_arc = _normalize_tactical_doc_for_prompt(next_arc)

            # V35 수술실 전용 고밀도 프롬프트
            surgery_prompt = f"""
### [🚨 V35 매니페스토: 서사 인과관계 수술 지시서]
당신은 서사 구조의 모순을 해결하고 상업적 재미를 극대화하는 '서사 설계 전문 에이전트'입니다.
현재 아키텍트의 에피소드 설계가 디렉터에 의해 3회 연속 거부되었습니다. 
원인은 현재 아크의 '전술서(tactical_doc)' 내에 존재하는 논리적 결함 혹은 밀도 부족입니다.




#### 1. 3-Window 상황 진단 (데이터 주권 보호)
- [이전 아크(Past)]: {json.dumps(prev_arc, ensure_ascii=False) if prev_arc else "데이터 없음(도입부)"}
- [현재 수술 대상(Present)]: {json.dumps(curr_arc, ensure_ascii=False)}
- [이후 아크 목표(Future)]: {json.dumps(next_arc, ensure_ascii=False) if next_arc else "데이터 없음(종결부)"}

#### 2. 상위 에이전트(Director)의 비판 포인트
- 비판 내용: {feedback}

#### 3. 수술 강령 (Surgery Protocol)
1. **인과관계 용접(Causal Welding)**: 
   - '이전 아크'에서 확정된 물리적 상태(주인공의 경지, 보유 무기, 상처 부위, 현재 위치)가 '현재 아크'에서 모순 없이 유지되도록 강제하십시오. 
   - 예: '검'을 든 주인공이 갑자기 '창'을 휘두르는 식의 물리적 오류를 지시어 레벨에서 박멸하십시오.
2. **5배 농축(5x Density)**: 
   - 기존의 헐거운 `tactical_doc`을 5배 더 세밀하게 쪼개십시오. 
   - 아크 내 각 에피소드별로 '반드시 일어나야 할 물리적 인과'와 '절대 변하지 말아야 할 상태'를 체크포인트 형태로 명시하십시오.
   - 각 에피소드별 전술(tactical_doc)을 5배 더 세밀하게 쪼개되, 출력 제한을 고려하여 핵심 인과 마디(Causal Nodes) 위주로 기술하십시오.
3. **상업적 도파민 제어**: 
   - 논리적 정합성만 챙기다 지루해지지 않도록, 웹소설 특유의 장르적 재미(사이다, 반전, 주변의 착각 리액션)가 각 화의 '연결 절단면'에 배치되도록 전술을 재배치하십시오.

#### 4. 출력 규격 (Strict JSON Only)
- 반드시 기존 아크 JSON 구조를 유지하십시오.
- `tactical_doc` 필드에 위 수술 결과를 5배 농축하여 담으십시오.
- JSON 이외의 어떤 텍스트(설명, 인사말)도 절대 출력하지 마십시오.
- 답변의 시작은 반드시 '{'로 시작하고 '}'로 끝나야 합니다. 
- 토큰 제한으로 응답이 잘릴 경우를 대비하여, 가장 중요한 `tactical_doc`을 최상단에 배치하십시오.
"""
            # 3-pro급 모델 호출 (안정적인 수술을 위해 온도를 낮춤)
            raw_response = self.ask(surgery_prompt, temperature=0.3)
            
            # BaseAgent의 강건한 파싱 엔진 활용
            reconstructed_arc = self._extract_json_robust(raw_response)
            
            if reconstructed_arc and "tactical_doc" in reconstructed_arc:
                # 🆕 V35 수술 마크 삽입: 아키텍트가 이를 보고 '성경 모드'를 발동합니다.
                # 🔧 [V40.2 Fix] 원본 arc의 모든 필수 필드를 보존하여 데이터 손실 방지
                preserved_fields = [
                    'ep_start', 'ep_end', 'arc_no', 'ep_count', 'vol_no', 'title',
                    'beat_sequence', 'hybrid_composition', 'arc_drive',
                    'joint_docs', 'status_shadow'
                ]
                for field in preserved_fields:
                    if field not in reconstructed_arc and curr_arc.get(field) is not None:
                        reconstructed_arc[field] = curr_arc.get(field)

                # 필수 필드 강제 보장 (LLM이 생성하지 않은 경우)
                if not reconstructed_arc.get('ep_start'):
                    reconstructed_arc['ep_start'] = curr_arc.get('ep_start')
                if not reconstructed_arc.get('ep_end'):
                    reconstructed_arc['ep_end'] = curr_arc.get('ep_end')
                if not reconstructed_arc.get('arc_no'):
                    reconstructed_arc['arc_no'] = curr_arc.get('arc_no')
                if not reconstructed_arc.get('ep_count'):
                    reconstructed_arc['ep_count'] = curr_arc.get('ep_count',
                        (reconstructed_arc.get('ep_end', 4) - reconstructed_arc.get('ep_start', 1) + 1))
                if not reconstructed_arc.get('beat_sequence') and curr_arc.get('beat_sequence'):
                    reconstructed_arc['beat_sequence'] = curr_arc.get('beat_sequence')

                reconstructed_arc['v35_surgery'] = True
                reconstructed_arc['mixing_logic'] = "[V35 Emergency Surgery] 인과관계 용접 및 5배 농축 완료"

                self.ui_log(f"✅ [Analyst] Arc {reconstructed_arc.get('arc_no', '??')} 수술 및 마킹 완료.")
                return reconstructed_arc  # 마킹된 데이터를 리턴
            else:
                self.ui_log("🚨 [Error] 아크 수술 결과 JSON 파싱 실패 또는 키 누락.")
                return None

        # 2. 기존 일반 분석 모드 (필요 시 확장 가능)
        return {"status": "GENERAL_MODE_ACTIVE"}

    def ui_log(self, msg):
        """ProjectContext를 통한 UI 로그 출력"""
        if hasattr(self.context, 'ui') and hasattr(self.context.ui, 'log'):
            self.context.ui.log(msg)
        else:
            print(f"[Analyst] {msg}")

    def perform_v35_calibration(self, current_hud, target_arc):
        """[V35.5] 서사 목적에 맞게 주인공의 물리 수치를 강제 교정 및 개연성 부여"""

        # 1. [🚨 핵심 수술] 파이썬 논리를 문자열 밖으로 탈출시킴
        if isinstance(target_arc, dict):
            arc_title = target_arc.get('title', '알 수 없는 아크')
            arc_tactical = target_arc.get('tactical_doc', '전술 데이터 없음')
        else:
            # target_arc가 문자열(제목)로 넘어왔을 경우를 대비한 방어 로직
            arc_title = str(target_arc)
            arc_tactical = "세부 전술 데이터가 누락되었습니다. 현재 맥락에 맞춰 보정하십시오."

        # 2. 보정 메시지 생성
        calibration_msg = f"현재 주인공의 상태로는 아크의 목표인 '{arc_title}'을(를) 달성하는 것이 물리적으로 불가능합니다."

        calibration_prompt = f"""
        [🚨 SYSTEM ADAPTATION: BIBLE CALIBRATION]
        {calibration_msg}

        [현재 상태]: {json.dumps(current_hud, ensure_ascii=False)}
        [아크 목표 - 상세 전술]: {arc_tactical}
        
        [Task]
        1. **수치 보정**: 'internal_energy' 혹은 'realm' 등 15대 지표 중 보정이 필요한 항목과 수치를 결정하라.
        2. **서사적 패치**: 수치 상승에 대한 개연성(예: 숨겨진 기운의 폭발, 적의 방심, 지형지물 이용)을 300자 내외로 작성하라.
        
        [Output Format] JSON Only
        {{
            "calibrated_metrics": {{ "internal_energy": "새로운 수치", "realm": "새로운 경지" }},
            "narrative_patch": "상승의 정당성을 설명하는 집필용 지시어"
        }}
        """
        res = self.ask(calibration_prompt, temperature=0.3)
        return self._extract_json_robust(res)            
    


    def stitch_joints(self, joint_a, joint_b, context_b):
        """[V35.5 Phase 3] 두 아크 사이의 물리적 마디를 검사하고 용접함"""
        prompt = POST_STITCH_REPAIR_PROMPT.format(
            arc_a_joint=json.dumps(joint_a, ensure_ascii=False),
            arc_b_joint=json.dumps(joint_b, ensure_ascii=False)
        )
        
        # 용접은 정밀도가 중요하므로 온도를 0.1로 고정
        raw_res = self.ask(prompt, temperature=0.1)
        return self._extract_json_robust(raw_res)    
    

    def get_lack_report(self, martial_hud):
        """
        [V38.2 S-Grade] NoneType 방어막이 적용된 결핍 탐지 엔진
        """
        # 1. 입력 가드: 데이터가 없거나 딕셔너리가 아니면 즉시 기본값 반환
        if not martial_hud or not isinstance(martial_hud, dict):
            return {
                "lack_summary": "1. [무력]: 데이터 로드 실패\n2. [경제]: 분석 불가\n3. [권위]: HUD 누락",
                "raw_analysis": {"Martial": [], "Economy": [], "Authority": []}
            }

        actual = martial_hud.get('actual_truth', {})
        reputation = martial_hud.get('public_reputation', {})

        # 2. 🛡️ [핵심 수술] None 값을 빈 문자열로 강제 치환 (TypeError 방지)
        def safe_str(val):
            return str(val) if val is not None else ""

        # 3. 결핍 판단 기준 정의
        LACK_CRITERIA = {
            "Martial": [
                (safe_str(actual.get('realm')), ["삼류", "하수", "입문", "견습", "초보", "None"], "절대적 무위 부족"),
                (safe_str(actual.get('causal_injuries')), ["부상", "내상", "박살", "뒤엉킨", "독", "불구"], "신체적 기능 저하")
            ],
            "Economy": [
                (safe_str(actual.get('wealth')), ["0", "없음", "고갈", "빈털터리", "채무"], "사적 활동 자금 전멸"),
                (safe_str(actual.get('equipment')), ["무딘", "연습용", "녹슨", "평범한", "누더기"], "장비 해상도 저하")
            ],
            "Authority": [
                (safe_str(reputation.get('identity')), ["망나니", "개차반", "무시", "천덕꾸러기", "낙제생"], "사회적 신뢰도 결여")
            ]
        }

        # 4. 루프 분석 (여기서 any() 에러가 발생하던 구간을 안전하게 통과함)
        lack_analysis = {"Martial": [], "Economy": [], "Authority": []}
        
        for category, criteria_list in LACK_CRITERIA.items():
            for target_value, keywords, message in criteria_list:
                # target_value가 이제 무조건 문자열이므로 에러가 나지 않음
                if any(k in target_value for k in keywords):
                    lack_analysis[category].append(message)

        # 5. 출력 생성
        summary = (
            f"1. [무력]: {', '.join(lack_analysis['Martial']) if lack_analysis['Martial'] else '안정'}\n"
            f"2. [경제]: {', '.join(lack_analysis['Economy']) if lack_analysis['Economy'] else '안정'}\n"
            f"3. [권위]: {', '.join(lack_analysis['Authority']) if lack_analysis['Authority'] else '안정'}"
        )

        return {
            "lack_summary": summary,
            "raw_analysis": lack_analysis
        }

    def _get_current_genre(self) -> str:
        """
        [V43] 현재 장르를 감지하여 반환
        Guard에서 장르 정보를 추출하거나 기본값 반환
        """
        try:
            if hasattr(self.context, 'guard') and self.context.guard:
                # Guard의 get_genre_name()에서 장르 추출
                genre_name = self.context.guard.get_genre_name()
                if 'hunter' in genre_name.lower() or '헌터' in genre_name:
                    return 'hunter'
                elif 'invest' in genre_name.lower() or '투자' in genre_name:
                    return 'investment'
                elif 'wuxia' in genre_name.lower() or '무협' in genre_name:
                    return 'wuxia'
        except Exception as e:
            print(f"      ⚠️ [Analyst] 장르 감지 실패: {e}")

        return 'wuxia'  # 기본값

    def _get_genre_library_path(self, genre: str):
        """
        [V43] 장르에 맞는 라이브러리 파일 경로 반환
        [V45 Fix] 프로젝트 config가 아닌 루트 config 경로 사용
        """
        from pathlib import Path

        # 장르별 라이브러리 파일 매핑
        genre_library_map = {
            'wuxia': 'analyst_libraries.json',
            'hunter': 'analyst_libraries_hunter.json',
            'investment': 'analyst_libraries_investment.json'
        }

        lib_filename = genre_library_map.get(genre, 'analyst_libraries.json')

        # [V45 Fix] 루트 config 경로 사용 (modules/domain/agents/analyst.py -> 3단계 상위)
        root_config = Path(__file__).parent.parent.parent.parent / "config"
        return root_config / "prompts" / lib_filename

    def _validate_arc_with_state_tracker(self, arc_data: dict) -> list:
        """
        [V49.3] StateTracker를 사용하여 Arc 설계의 상태 일관성 검증

        Args:
            arc_data: Arc 전술 문서

        Returns:
            검증 이슈 목록 (빈 리스트면 문제 없음)
        """
        try:
            tracker = StateTracker()
            if not tracker.load_arc_design(arc_data):
                print("      ⚠️ [Analyst] StateTracker 로드 실패, 검증 스킵")
                return []

            # 타임라인 검증
            issues = tracker.validate_timeline()

            if issues:
                # DAG 시각화 출력 (디버깅용)
                print(tracker.get_dag_visualization())

            return issues

        except Exception as e:
            print(f"      ⚠️ [Analyst] StateTracker 검증 중 오류: {e}")
            return []

    def get_state_constraint_prompt(self, arc_no: int) -> str:
        """
        [V49.3] 이전 Arc들의 상태를 분석하여 제약 프롬프트 생성

        Architect/Writer에게 전달하여 상태 일관성 유지

        Args:
            arc_no: 현재 Arc 번호

        Returns:
            상태 제약 프롬프트 문자열
        """
        try:
            # DB에서 이전 Arc들 로드
            arcs_anchor = self.context.db.load_anchor('arcs')
            if not arcs_anchor:
                return ""

            prev_arcs = []
            for i in range(1, arc_no):
                arc_key = f"arc_{i}"
                if arc_key in arcs_anchor:
                    prev_arcs.append(arcs_anchor[arc_key])

            if not prev_arcs:
                return ""

            # 통합 StateTracker 생성
            from .state_tracker import create_tracker_from_arcs
            master_tracker = create_tracker_from_arcs(prev_arcs)

            # 제약 프롬프트 생성
            return master_tracker.generate_constraint_prompt()

        except Exception as e:
            print(f"      ⚠️ [Analyst] 상태 제약 프롬프트 생성 실패: {e}")
            return ""