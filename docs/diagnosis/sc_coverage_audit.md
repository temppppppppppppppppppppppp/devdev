# SC (Smart Context Retrieval) 커버리지 감사 보고서

**작성일**: 2026-02-27
**대상**: `continuity_violation_scenarios.md` 전체 시나리오 vs SC 시스템 실제 커버리지
**결론**: 현 시스템은 단기 연속성(~10화)에 강하고 장기 기억(60화+)에 취약. 5대 핵심 갭 존재.

---

## 1. SC 시스템 구조 요약

### 1.1 아키텍처

```
ContextAdvisor            Stage4ContextBuilder              VecMemory
(쿼리 계획 생성)   →      (_execute_retrieval_plan)    →    (hybrid/dense/sparse 검색)
                                                           ↓
                          mandatory_context로 조립   ←      검색 결과 텍스트
```

### 1.2 데이터 흐름

| 단계 | 컴포넌트 | 역할 |
|------|---------|------|
| 계획 | `ContextAdvisor._build_stage4_slots()` | 휴리스틱 슬롯 생성 (최대 8개) |
| 보강 | `ContextAdvisor._llm_enrich_plan()` | arc boundary/reject retry/NPC 5+명 시 LLM 보강 |
| 실행 | `Stage4ContextBuilder._execute_retrieval_plan()` | 슬롯별 검색 수행 (hybrid/dense/npc) |
| 조립 | `build_mandatory_context()` | SC 결과를 mandatory_context 맨 앞에 배치 |

### 1.3 Stage4 슬롯 종류 (자동 생성)

| 슬롯 카테고리 | 쿼리 생성 방식 | 검색 소스 | 우선순위 |
|-------------|-------------|----------|---------|
| `prev_ending` | 직전 화 결말 텍스트 (260자) | VEC_MEMORY (hybrid) | 1 |
| `npc_history` | NPC 이름 최대 6명 나열 | DB_NPC_HISTORY (entity+vector) | 1 |
| `arc_tactical` | Arc tactical_doc 텍스트 (320자) | VEC_MEMORY (hybrid) | 2 |
| `scene_context` | Blueprint scene_breakdown 요약 | VEC_MEMORY (hybrid) | 2 |
| `unresolved_plot` | Arc plot_suspension 항목 3개 | VEC_MEMORY (hybrid) | 1 |
| `relationship_history` | state_changes 관계 변화 | VEC_MEMORY (hybrid) | 2 |
| `genre_context_N` | 장르별 고정 키워드 2개 | VEC_MEMORY (hybrid) | 3 |

### 1.4 검색 대상 데이터

VecMemory의 `episode_meta` 테이블에 저장되는 데이터:
- **summary**: 사건/인물/장소/결말 조합 요약 (~500자)
- **event_types**: 이벤트 유형 태그 (콤마 구분, ~500자)
- **entity_names**: 등장 인물 이름 (콤마 구분, ~1000자)
- **벡터 임베딩**: 원고 전문 기반 (gemini-embedding-001, 3072차원)

FTS5 인덱스: summary + event_types + entity_names 전문 검색

### 1.5 비-SC 경로 (항상 주입되는 정보)

| 데이터 소스 | 주입 위치 | 범위 |
|-----------|----------|------|
| **FactLedger.to_summary()** | mandatory_context 맨 앞 (insert(0)) | 전체 누적 (max 25K자) |
| **WorldState.get_summary()** | ep_ctx["world_state_summary"] | 현재 세계 상태 전체 (max 10K자) |
| **WorldState.get_long_term_anchor()** | prev_manuscripts_text 앞 (ep>=60) | 세계관 법칙 + NPC role_at_intro |
| **직전 3화 원고** | prev_manuscripts_text | ep-3 ~ ep-1 |
| **확장 Lookback** | mandatory_context | ep-10 ~ ep-4 (요약) |
| **Chain Link** | ep_ctx["chain_link_section"] | 직전 1화 연결고리 |
| **HUD 스냅샷** | 별도 주입 | 투자물 전용 자본금 |
| **TruthGate** | 사후 검증 (advisory) | 사망NPC/아이템/장소/스킬/카르마 |

### 1.6 예산 설정 (현재)

| 경로 | 예산 |
|------|-----|
| Stage4 SC | 100,000자 |
| Director SC | 50,000자 |
| 슬롯당 최소 | 3,000자 |
| 슬롯 최대 수 | 8개 |

---

## 2. 커버리지 매핑 표

### 2.1 장르 공통 시나리오 (PART 1)

| ID | 시나리오 유형 | SC 쿼리 생성? | 관련 화 검색? | LLM 전달? | 실제 방어 수단 | 갭 등급 |
|----|------------|-------------|-------------|----------|-------------|--------|
| **1-A** | 직업/신분 표류 | 부분 (NPC 이름으로 npc_history 슬롯) | **NPC 이름이 entity_names에 있으면 가능** | O (summary에 직업 있으면) | WorldState.role_at_intro + FactLedger | MEDIUM |
| **1-B** | 외모/신체 속성 역전 | 부분 (NPC history) | **외모 정보가 summary에 없으면 불가** | X (summary에 신체 정보 미포함) | WorldState.known_attrs (있으면) | **HIGH** |
| **1-C** | 사망자 부활 | X (SC 불필요) | N/A | N/A | **TruthGate + WorldState.dead_npcs** | OK |
| **2-A** | 금액 표류 | X (금액 쿼리 슬롯 없음) | X | X | **FactLedger.numbers** (financial_events 자동추출) | MEDIUM |
| **2-B** | 수량/물리량 모순 | X | X | X | FactLedger.numbers (power_level만) | **HIGH** |
| **2-C** | 시간/날짜 역행 | X | X | X | 없음 | **HIGH** |
| **3-A** | 인간관계 역전 | 부분 (relationship_history 슬롯) | **관계 변화가 state_changes에 있으면 가능** | 부분 | FactLedger.characters + WorldState.relationships | MEDIUM |
| **3-B** | 조직/세력 관계 역전 | X | X | X | FactLedger.organizations (제한적) | **HIGH** |
| **3-C** | 세계관 법칙 붕괴 | X (법칙 쿼리 슬롯 없음) | X | X | **WorldState.world_laws** (ep>=60 앵커) | MEDIUM |
| **4-A** | 미보유 아이템 사용 | X | X | X | **TruthGate.item_existence** | OK |
| **4-B** | 미습득 스킬 사용 | X | X | X | **TruthGate.skill_duplication** | OK |
| **4-C** | 부상/상태 무시 | X | X | X | FactLedger (npc_injuries) | MEDIUM |
| **5-A** | 정보 역설 (선지식) | X | X | X | 없음 | **HIGH** |
| **5-B** | 비밀 공유 범위 역전 | X | X | X | 없음 | **HIGH** |
| **6-A** | 시점 혼용 | X | X | X | ContinuityValidator (직전 화만) | LOW |
| **6-B** | 호칭 역전 | X | X | X | 없음 | LOW |
| **7-A** | 누적 표류 | X | X | X | 없음 (화별 변화 소폭) | **HIGH** |
| **7-B** | 회상 오염 | X | X | X | 없음 | **HIGH** |
| **7-C** | 부활+기억 역전 콤보 | 부분 | 부분 | 부분 | TruthGate (사망만) | MEDIUM |

### 2.2 장기 기억 시나리오 (PART 5)

| ID | 시나리오 유형 | SC 커버? | 실제 방어 수단 | 갭 등급 |
|----|------------|---------|-------------|--------|
| **L1** | NPC 속성 장기 표류 (50화+) | **부분** — NPC history 슬롯이 entity_names 매칭으로 과거 화를 찾지만, summary에 직업/나이/출신이 없으면 무의미 | WorldState.role_at_intro (직업만, 나이/출신 미저장) | **HIGH** |
| **L2** | 세계관 법칙 망각 (60화+) | **X** — 법칙 전용 쿼리 슬롯 없음 | WorldState.world_laws (앵커, ep>=60 주입) + FactLedger | MEDIUM |
| **L3** | 관계도 장기 표류 | **부분** — relationship_history 슬롯이 state_changes 기반, 점진적 변화는 감지 불가 | WorldState.relationships + FactLedger.characters | **HIGH** |
| **L4** | 수치 누적 표류 (143배) | **X** — 수치 전용 쿼리 없음 | FactLedger.numbers (financial_events/power_level만 자동 추출, 월급/나이 등 일반 수치 미추출) | **CRITICAL** |
| **L5** | 회상/플래시백 오염 | **X** — 과거 화 원문 비교 불가 | 없음 (원고 전문은 벡터 DB에 임베딩만 저장, 원문 미저장) | **HIGH** |
| **L6** | 정보 역설 장기형 | **X** — 논리 추론 필요 | 없음 (Python 감지 불가) | LOW (LLM 영역) |
| **L7** | 장기 서사 구조 붕괴 | **X** — Arc 단위 분석 필요 | 없음 | LOW (LLM 영역) |

---

## 3. 핵심 갭 목록 (5대)

### GAP-1: NPC 초기 속성 미보존 (CRITICAL)

**문제**: WorldState.role_at_intro는 "최초 역할"만 저장. 나이, 외모, 신체 특징, 출신 배경, 학력 등 NPC의 **고정 속성**이 체계적으로 저장되지 않음.

**영향 시나리오**: L1 전체 (#1~5), 1-A, 1-B
- "삼성 법무팀 변호사" → role_at_intro에 저장됨 (있으면)
- "키 162cm, 단신" → 미저장
- "52세" → 미저장
- "고졸, 현장직 출신" → 미저장
- "의족 착용자" → 미저장

**현재 상태**: WorldState.alive_npcs의 스키마에 `known_attrs` dict가 존재하지만, **자동 추출 로직이 없음**. state_changes에는 `npc_personality_changes`만 있고, 초기 신체/학력/나이 속성 추출 필드가 없음.

### GAP-2: 수치 팩트 자동 추출 범위 협소 (HIGH)

**문제**: FactLedger._extract_numerical_facts()는 `status_shadow` (내공), `financial_events` (투자), `power_level` (전투력) 3가지 경로만 자동 추출. **일반 수치**(월급, 나이, 건물 시세, 마나 상한 등)는 state_changes에 구조화된 필드가 없어 추출 불가.

**영향 시나리오**: 2-A, 2-B, 2-C, L4 전체 (#16~20)
- "월급 210만원" → state_changes에 해당 필드 없음 → FactLedger에 미등록
- "마력 상한 9999" → state_changes에 해당 필드 없음
- "나이 28세" → 미등록

**현재 상태**: FactLedger.update_number()는 수동 호출 API만 제공. LLM이 state_changes에 범용 수치를 넣을 구조(ex: `numerical_facts: [{key, value, unit}]`)가 없음.

### GAP-3: 과거 화 원문 비교 불가 (HIGH)

**문제**: VecMemory는 원고 전문의 **임베딩**만 저장. 원문 텍스트는 벡터 DB에 미저장. 따라서 SC 검색 결과는 summary(~500자) + event_types + entity_names만 반환. **과거 화에서 실제로 무슨 말을 했는지** 원문 수준 비교가 불가능.

**영향 시나리오**: L5 전체 (#21~25), 7-B
- "7화에서 A가 B를 구해줌" → summary에 "A가 B를 구함"이 있으면 검색 가능하지만, 실제 대사/묘사 수준 비교는 불가
- 회상 장면에서 과거 대사를 왜곡해도 감지 불가

**현재 상태**: episode_meta.summary는 ~500자. 원고 전문은 파일(drafts/ep_XXXX.txt) 또는 DB(manuscripts 테이블)에 있지만, SC가 이를 검색 대상으로 사용하지 않음. 확장 Lookback(ep-10~ep-4)은 첫 500자만 가져옴.

### GAP-4: 세계관 법칙 SC 슬롯 부재 (MEDIUM)

**문제**: SC 슬롯에 "세계관 법칙 검증" 전용 카테고리가 없음. WorldState.world_laws는 ep>=60에서만 `get_long_term_anchor()`로 주입되고, ep<60에서는 WorldState.get_summary() 안의 `[세계관 절대 법칙 -- 위반 금지]` 섹션에만 포함.

**영향 시나리오**: 3-C, L2 (#6~10)
- "마법은 왕족만 가능" → WorldState.world_laws에 등록되어 있으면 get_summary()에 포함
- 그러나 SC가 world_laws를 **검증 쿼리**로 벡터 검색하지 않음 → 법칙이 최초 언급된 화의 원문 맥락을 가져오지 못함

**현재 상태**: world_laws 앵커는 존재하지만, SC 쿼리와 연동되지 않음. 법칙 텍스트가 mandatory_context에 포함되므로 LLM이 참조할 수는 있지만, 법칙 위반 여부를 **적극적으로 검증**하는 경로는 없음.

### GAP-5: 시간/날짜 추적 체계 부재 (MEDIUM)

**문제**: 작중 시간(날짜, 요일, 계절, 캐릭터 나이)을 추적하는 전용 시스템이 없음. Chain Link에 `time_marker`와 `location`이 있지만 직전 1화만 커버. 누적 시간 계산이나 시간 역행 감지가 불가.

**영향 시나리오**: 2-C, L4 #20
- "11월 3일" → Chain Link에 저장될 수 있지만, 직전 화만
- "캐릭터 나이 28세" → 어디에도 체계적 저장 없음
- 화간 경과 시간 누적 → 추적 시스템 없음

---

## 4. 수정 플랜

### 4.1 플랜 A: NPC 초기 속성 보강 (GAP-1 대응)

**목표**: NPC의 고정 속성(나이, 외모, 신체, 학력, 출신)을 WorldState에 보존

**방안**:
1. Arc state_changes 스키마에 `npc_introductions` 필드 추가:
   ```json
   "npc_introductions": [
     {"name": "오민준", "age": 52, "job": "삼성 법무팀 변호사", "appearance": "키 180cm", "background": "서울대 법학과"}
   ]
   ```
2. WorldState.update_from_state_changes()에서 npc_introductions → alive_npcs.known_attrs 자동 갱신
3. known_attrs는 **최초 1회만 저장** (role_at_intro 패턴 — 덮어쓰지 않음)
4. get_long_term_anchor()에 known_attrs 포함 (현재도 구현되어 있으나 데이터 미유입)

**대원칙 검증**: Python은 수집만(LLM이 state_changes에 넣은 구조화 데이터를 옮기는 것), 판단 없음. OK.

**예산 영향**: known_attrs 30명 x 100자 = 3,000자 추가. 100K 예산 내 OK.

**구현 난이도**: LOW (기존 패턴 반복)

### 4.2 플랜 B: 범용 수치 팩트 추출 (GAP-2 대응)

**목표**: 월급, 나이, 건물 시세 등 일반 수치를 FactLedger에 자동 등록

**방안**:
1. Arc state_changes 스키마에 `numerical_facts` 범용 필드 추가:
   ```json
   "numerical_facts": [
     {"key": "주인공_월급", "value": 210, "unit": "만원", "context": "경리 초봉"},
     {"key": "이한결_나이", "value": 52, "unit": "세"}
   ]
   ```
2. FactLedger._extract_numerical_facts()에서 `numerical_facts` 배열 순회 → update_number() 호출
3. Arc/Blueprint LLM 프롬프트에 "작중 등장하는 수치(금액, 나이, 수량 등)를 numerical_facts에 기록하라" 지시 추가

**대원칙 검증**: LLM이 수치를 판단/추출 → Python이 수집/저장. OK.

**예산 영향**: FactLedger.to_summary()의 `[주요 수치]` 섹션에 추가. 15개 x 50자 = 750자. OK.

**구현 난이도**: MEDIUM (LLM 프롬프트 수정 + 스키마 확장)

### 4.3 플랜 C: 과거 화 원문 발췌 검색 (GAP-3 대응)

**목표**: SC 검색 결과에 과거 화 원문의 관련 구간을 포함

**방안**:
1. VecMemory.retrieve_*에서 ep_num을 찾은 후, DB의 manuscripts 테이블에서 해당 화 원문을 SUBSTR로 로드
2. 검색 쿼리 키워드와 매칭되는 문단을 추출 (keyword window 방식)
3. summary + **원문 발췌 200자** 형태로 SC 결과 반환
4. 예산 제한: 슬롯당 max_chars 내에서 원문 발췌 비중 조절

**대원칙 검증**: Python이 데이터 수집/포맷팅. OK.

**예산 영향**: 슬롯당 200자 추가 x 8슬롯 = 1,600자. OK.

**구현 난이도**: MEDIUM (VecMemory 검색 결과 포맷 변경)

**주의**: 이 플랜은 매우 효과적이지만, manuscripts 테이블에 원고가 저장되어 있어야 함. 현재 시스템에서 원고 저장 경로(파일 vs DB) 확인 필요.

### 4.4 플랜 D: 세계관 법칙 SC 슬롯 (GAP-4 대응)

**목표**: SC가 세계관 법칙을 적극적으로 검증 쿼리에 포함

**방안**:
1. `_build_stage4_slots()`에 `world_law_anchor` 슬롯 추가:
   - WorldState.get_world_laws()에서 법칙 텍스트 가져옴
   - 각 법칙을 쿼리로 벡터 검색 → 법칙이 최초 언급된 화의 맥락을 가져옴
2. 우선순위 1 (최고), max_chars = 법칙당 500자
3. 법칙 수가 0이면 슬롯 생성 안 함

**대원칙 검증**: Python이 데이터 수집. OK.

**예산 영향**: 법칙 5개 x 500자 = 2,500자. OK.

**구현 난이도**: LOW

### 4.5 플랜 E: 작중 시간 추적기 (GAP-5 대응)

**목표**: 작중 시간(날짜, 계절, 나이 증감)을 누적 추적

**방안**:
1. WorldState에 `timeline` 필드 추가:
   ```json
   "timeline": {
     "current_date": "11월 3일",
     "elapsed_days": 42,
     "season": "초겨울",
     "character_ages": {"주인공": 28}
   }
   ```
2. state_changes에 `time_delta` 필드 추가:
   ```json
   "time_delta": {"days": 3, "date_marker": "11월 6일"}
   ```
3. WorldState.update_from_state_changes()에서 timeline 자동 갱신
4. get_summary()에 timeline 섹션 포함

**대원칙 검증**: LLM이 time_delta 판단 → Python이 누적. OK.

**예산 영향**: ~200자. OK.

**구현 난이도**: MEDIUM (LLM 프롬프트 수정 필요)

---

## 5. 수정 우선순위

| 순위 | 플랜 | 갭 | 영향 시나리오 수 | 난이도 | ROI |
|------|-----|-----|---------------|-------|-----|
| **1** | B (범용 수치 팩트) | GAP-2 | 8개 (2-A,2-B,L4 전체) | MEDIUM | **최고** — 수치 표류는 가장 빈번한 실제 오류 |
| **2** | A (NPC 초기 속성) | GAP-1 | 7개 (1-A,1-B,L1 전체) | LOW | 높음 — 기존 known_attrs 활용 |
| **3** | D (세계관 법칙 슬롯) | GAP-4 | 5개 (3-C,L2 전체) | LOW | 높음 — 구현 간단, world_laws 이미 존재 |
| **4** | E (시간 추적) | GAP-5 | 3개 (2-C,L4#20) | MEDIUM | 중간 |
| **5** | C (원문 발췌) | GAP-3 | 5개 (L5 전체) | MEDIUM | 중간 — 효과 높지만 구현 비용도 높음 |

---

## 6. 감리 기준 검증

### 대원칙 위반 여부

- **"Python은 수집만, 판단은 LLM이"**: 모든 플랜에서 Python은 LLM이 state_changes에 넣은 구조화 데이터를 옮기거나, 검색 결과를 포맷팅하는 역할만 수행. **위반 없음.**
- **"팩트시트 수정 권한은 LLM만"**: NPC 속성(플랜 A), 수치(플랜 B), 시간(플랜 E)은 모두 LLM이 state_changes에 넣은 값을 Python이 저장. **위반 없음.**
- **"디렉터 주권주의"**: SC는 Writer/Director에게 참고 정보를 제공할 뿐, 합격/불합격 판정에 관여하지 않음. **위반 없음.**

### 예산 초과 위험

현재 Stage4 SC 예산: 100,000자.
플랜 전체 적용 시 추가: ~8,000자 (8% 증가). **초과 위험 없음.**

### 실현 가능성

- 플랜 A, D: **즉시 구현 가능** (기존 패턴 반복, 코드 20~50줄)
- 플랜 B, E: **LLM 프롬프트 수정 필요** (Arc/Blueprint 프롬프트에 필드 추가)
- 플랜 C: **VecMemory 수정 필요** (검색 결과 포맷 변경, manuscripts DB 접근 추가)

---

## 7. 현재 시스템의 강점 (이미 커버되는 영역)

현 시스템이 **잘 방어하는** 시나리오:

1. **사망자 부활 (1-C)**: TruthGate + WorldState.dead_npcs → CRITICAL 등급이지만 **이미 커버**
2. **미보유 아이템 사용 (4-A)**: TruthGate.item_existence → **커버**
3. **미습득 스킬 사용 (4-B)**: TruthGate.skill_duplication → **커버**
4. **파괴된 장소 방문**: TruthGate.location_existence → **커버**
5. **단기 연속성 (직전 3화)**: 직전 3화 원문 주입 → **강력한 커버**
6. **확장 단기 (4~10화 전)**: Lookback Digest → **부분 커버**
7. **장르 금지 용어**: GenreGuard 10종 → **커버**
8. **세계관 법칙 (ep>=60)**: WorldState.get_long_term_anchor() → **앵커 존재**

---

*이 문서는 `docs/diagnosis/continuity_violation_scenarios.md`의 전체 시나리오에 대한 SC 커버리지 감사 결과이다.*
*수정 플랜의 구현은 우선순위 순서대로 진행하되, 각 플랜은 독립적이므로 병렬 작업 가능.*
