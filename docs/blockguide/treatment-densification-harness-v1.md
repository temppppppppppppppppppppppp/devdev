# Treatment Densification Harness v1.1 (v2 강화판)

> **목적**: 이미 70블록 스켈레톤이 완성된 TR draft를, 구조적 뼈대를 보존한 채 Block 1~6 수준의 서사 밀도로 끌어올리는 전용 하네스.
>
> **SSOT 위치**: `docs/blockguide/treatment-densification-harness-v1.md`
>
> **선행 조건**: `treatment-production-harness-v2.md`로 생산된 70블록 TR draft가 존재하고, BI 5-Pass 감리까지 통과한 상태에서, 내용적 밀도가 부족하다고 판정된 경우에만 진입한다.
>
> **관계**:
> - `treatment-planning-harness.md` → Phase 0 원천 (읽기 전용)
> - `treatment-production-harness-v2.md` → 밀도 게이트/차이 행렬/절대 금지 규칙 상속
> - `bi-production-harness-v1.md` → 덴시피케이션 완료 후 BI 재동기화 시 참조
> - 이 하네스는 `treatment-production-harness-v2.md`의 **후처리 확장**이지, 대체가 아니다

---

## 0A. 빠른 시작 (10단계 즉시 체크리스트)

1. `treatments/{work_id}_tr_block_070_draft.json` 존재 확인
2. `treatments/phase0/{work_id}_phase0_design.json` 존재 확인
3. `bible/{work_id}_bi.json` 존재 확인 (BI 5-Pass PASS 상태)
4. 덴시피케이션 진입 사유 확인 (4축 감사 보고서 or 밀도 게이트 FAIL 판정)
5. 잠금/재작성 필드 분류표(§1) 확인
6. 보조 입력 3종(§3~§5) 존재 확인 (없으면 먼저 생성)
7. 덴시피케이션 배치 플래너(§7) 작성
8. Block 1~6은 스킵 대상인지 확인 (이미 고밀도이면 잠금)
9. 첫 배치 실행 (§9)
10. 배치 감리 통과 후 다음 배치 진행 (§10~§11)

### 즉시 금지 3개

- 잠금 필드를 수정하면서 "밀도 개선"이라고 부르는 것 → REJECT
- 보조 입력 없이 "기억으로" 역사 이벤트/거물을 주입하는 것 → REJECT
- 70블록 일괄 재작성 → REJECT (배치 단위 순차 처리만 허용)

---

## 0B. 용어 정의

| 용어 | 정의 |
|------|------|
| **스켈레톤 블록** | `avg_bundle_chars < 350` 이거나, solution/event_villain/stakes 중 2개 이상이 다른 블록과 동일 문장 패턴인 블록 |
| **고밀도 블록** | `avg_bundle_chars >= 800`, 차이 행렬 29문항 전량 PASS, 블록 고유 event_villain/solution 보유 |
| **잠금 필드** | 덴시피케이션 과정에서 변경 금지인 구조적 필드 |
| **재작성 필드** | 덴시피케이션 대상인 서사 내용 필드 |
| **보조 입력** | 덴시피케이션 품질을 올리기 위해 phase0 외에 추가로 제공하는 참조 자료 |
| **밀도 스코어** | 블록 단위 정량 품질 점수 (§12 참조) |
| **DEN-candidate** | 덴시피케이션용 후보 블록 (기존 candidate와 구분) |
| **DEN-fixed** | 덴시피케이션용 교정 완료 블록 |

---

## 0C. 진입 게이트

덴시피케이션은 아래 **모두** 충족 시에만 진입한다.

1. `tr_block_070_draft.json` 70블록 존재
2. `phase0_design.json` 존재 + 최소 필수 시트 4종 완비
3. BI 5-Pass 감리 기통과 (구조적 정합성은 이미 확보)
4. 다음 중 하나 이상 해당:
   - 4축 감사에서 밀도/루즈함 축 FAIL 판정
   - `production_density_gate` 사후 재검 FAIL
   - 수동 감리에서 "스켈레톤 블록 과다" 판정
   - 차이 행렬 29문항 중 3개 이상 FAIL

---

## 0D. Family-Agnostic 보조 입력 인터페이스 (v2 추가)

이 하네스의 보조 입력 3종(§3~§5)은 `blockguide`(현판 비즈니스물) 기준으로 작성되었다.
다른 family(wuxguide 등)에서 덴시피케이션을 적용할 때는 아래 추상 계약만 지키면 된다.

| 슬롯 | 추상 계약 | blockguide 구체 예 | wuxguide 구체 예 |
|------|----------|-------------------|------------------|
| 보조 입력 1 | **시간축 사건 타임라인** — 작중 시간에 대응하는 구체 사건 배치 | 역사 이벤트 타임라인 (경제/사회) | 무공/비급 획득 타임라인 (경지 체계) |
| 보조 입력 2 | **외부 세력 풀** — 기존 내부 적대자를 보완하는 외부 거물 | 금융/정치/재벌 거물 풀 | 강호 세력/문파/마교 거물 풀 |
| 보조 입력 3 | **물리 자산 카탈로그** — 블록별 leverage/reward에 쓰이는 구체적 사물 | 계약서/증거/시스템 카탈로그 | 신병이기/영약/비급 카탈로그 |

공통 필수 필드:

- 각 항목에 `usable_blocks` 또는 `arc_range` 필수
- 각 항목에 `narrative_value` 또는 `narrative_leverage` 필수
- ARC당 최소 2건 할당

family별 구체 내용은 해당 family의 densification harness에서 정의한다.

---

## 1. 잠금/재작성 필드 분류

### 1.1 잠금 필드 (Structural Lock)

절대 변경 금지. 이 필드가 바뀌면 BI와의 정합성이 깨진다.

```
block_id
title
capital_before
capital_after
capital_delta
profit_loss
time_span.duration
time_span.in_story_time
section_rotation
pov_character
is_regressor
regression_type
incarnation_type
single_heir_policy
business_sector
```

### 1.2 조건부 잠금 필드 (Conditional Lock)

기본 잠금이나, 보조 입력에 근거가 있을 때 **§6 조건부 해제 절차**를 거쳐 수정 가능.

```
location.place          -- 장소가 너무 반복적일 때만 해제
location.type           -- 위와 동일
investment_type         -- 사업 유형 세분화 시 해제
```

### 1.3 재작성 필드 (Content Rewrite)

덴시피케이션 핵심 대상. 블록별로 완전히 새로 쓴다.

```
content.context
content.event_villain
content.solution
content.reward
stakes
power_shift.protagonist
power_shift.antagonist
relationship_delta[]     -- target/before/after 전량
foreshadow[]
callback[]
emotional_beat.type
emotional_beat.intensity
tension_level
genre_ext.method
genre_ext.deal_type
genre_ext.leverage_used[]
genre_ext.opponent{}
genre_ext.historical_event{}
genre_ext.time_pressure
genre_ext.knowledge_used
genre_ext.risk_level
genre_ext.success_pattern
genre_ext.special_ability{}
regression_ext.timeline_knowledge{}
regression_ext.butterfly_effect{}
regression_ext.death_flag{}
regression_ext.regression_hint{}
regression_ext.future_prep{}
regression_ext.execution_doctrine
```

### 1.4 분류표 검증

- 잠금 필드 수정 시도 → DEN-candidate 즉시 REJECT
- Python `check --densification-mode`로 잠금 필드 변경 여부 자동 탐지

---

## 2. 스켈레톤 진단 (20단계 중 1단계)

### 2.1 전 블록 스켈레톤 스캔

기존 TR draft 70블록을 대상으로 아래 지표를 산출한다.

```python
for block in tr_draft:
    bundle_chars = len(context + event_villain + solution + reward + stakes)
    is_skeleton = bundle_chars < 350
    template_score = measure_template_similarity(block, all_blocks)
    # template_score: 다른 블록과의 문장 유사도 (0.0~1.0)
```

**산출물**: `treatments/audit_reports/{work_id}_skeleton_diagnosis.json`

```json
{
  "total_blocks": 70,
  "skeleton_blocks": [7, 8, 9, ...],  // block_id 목록
  "high_density_blocks": [1, 2, 3, 4, 5, 6],
  "avg_bundle_chars_skeleton": 280,
  "avg_bundle_chars_high": 850,
  "template_similarity_avg": 0.87,
  "worst_template_clusters": [
    {"pattern": "event_villain 동일 구조", "affected_blocks": [7,8,9,...,70]},
    {"pattern": "solution 동일 구조", "affected_blocks": [7,8,9,...,70]},
    {"pattern": "relationship_delta 동일 문장", "affected_blocks": [10,15,20,...]}
  ],
  "skip_blocks": [1, 2, 3, 4, 5, 6],
  "rewrite_blocks": [7, 8, 9, ..., 70]
}
```

### 2.2 고밀도 블록 잠금 판정

Block 1~6처럼 이미 `avg_bundle_chars >= 800` + 차이 행렬 PASS인 블록은 **스킵 대상**으로 분류한다. 덴시피케이션하지 않는다.

---

## 3. 보조 입력 1: 역사 이벤트 타임라인 (20단계 중 2단계)

### 3.1 목적

작품의 시간축(2018.4~2022.10)에 실제 경제/사회 이벤트를 배치하여, 블록별 `historical_event`와 `time_pressure`의 구체적 근거를 제공한다.

### 3.2 형식

`treatments/preprocess/{work_id}/densification/historical_timeline.json`

```json
{
  "_description": "작중 시간축에 대응하는 실제 역사 이벤트",
  "events": [
    {
      "event_id": "HE-001",
      "date_range": "2018-03 ~ 2018-06",
      "event": "2018 상반기 최저임금 16.4% 인상 → 외식업/급식 인건비 급등",
      "sector_impact": ["급식", "외주 용역", "장례 의전"],
      "usable_blocks": [1, 2, 3, 4, 5],
      "narrative_leverage": "인건비 급등으로 기존 급식업체 이탈 → 주인공 진입 기회"
    },
    {
      "event_id": "HE-002",
      "date_range": "2018-07 ~ 2018-12",
      "event": "미중 무역전쟁 1차 관세 → 원자재/부자재 가격 불안정",
      "sector_impact": ["제조", "소모품", "세탁 원료"],
      "usable_blocks": [6, 7, 8, 9, 10],
      "narrative_leverage": "원가 불안정으로 장기 계약 유리 → 운영권 확보 레버리지"
    }
    // ... ARC당 최소 2~3건, 전체 15~20건
  ]
}
```

### 3.3 최소 요구

- ARC당 최소 2건 (7 ARC × 2 = 14건 이상)
- 실제 사건 기반 (허구 이벤트 금지)
- `sector_impact`가 해당 ARC의 `business_sector`와 연결
- `usable_blocks`가 해당 ARC의 블록 범위 내

### 3.4 작성 방법

사용자가 직접 작성하거나, LLM에 시간축 + 사업 영역을 제공하여 생성. 생성 후 반드시 사실 확인(fact-check) 1회.

---

## 4. 보조 입력 2: 외부 거물 풀 (20단계 중 3단계)

### 4.1 목적

기존 TR의 적대자가 내부 인물(서도윤/노현주/윤석진) + 현장 중간관리자에 집중되어 있는 문제를 해소. 후반 ARC(자본 100억+)에 적합한 외부 거물을 사전 설계한다.

### 4.2 형식

`treatments/preprocess/{work_id}/densification/external_opponent_pool.json`

```json
{
  "_description": "덴시피케이션용 외부 거물 풀",
  "opponents": [
    {
      "opp_id": "EXT-001",
      "name": "강태웅",
      "title": "한강은행 여신심사역",
      "sector": "금융",
      "arc_range": [5, 6, 7],
      "goal": "윤성그룹 계열사 여신 통제, 제로라인 독립 여신 차단",
      "rational_action": "여신 심사에서 제로라인의 매출 의존도를 문제 삼아 한도 축소",
      "information_state": "윤성그룹 내부 운영 구조를 외부에서 간접 파악",
      "weakness": "은행 내부 성과 평가가 신규 여신 건수 기준이라 대출 거절이 자신에게도 불리",
      "why_loses": "제로라인이 팩토링으로 은행 우회 경로를 확보하면 여신 카드의 가치 소멸"
    }
    // ... 최소 5명
  ]
}
```

### 4.3 최소 요구

- 총 5명 이상
- ARC-05 이후(자본 150억+)에 최소 3명 배치
- 기존 내부 인물(서도윤/노현주/윤석진)과 **중복 금지**
- 각 거물에 `goal`, `rational_action`, `information_state`, `weakness`, `why_loses` 필수 (planning harness 원칙 C 준수)
- 거물 유형 최소 3가지 (금융/정치/경쟁 재벌/미디어/규제기관 등)

### 4.4 기존 적대자와의 관계

외부 거물은 기존 내부 적대자와 **연합하거나 독립적으로** 움직일 수 있다. 덴시피케이션 시 기존 `genre_ext.opponent`를 외부 거물로 교체하거나 보조 적대자로 추가하는 것 모두 허용.

---

## 5. 보조 입력 3: 아이템/레버리지 카탈로그 (20단계 중 4단계)

### 5.1 목적

기존 KeyItems 2개(추상적)를 구체적 물리 아이템/문서/증거/시스템으로 확장. 블록별 `leverage_used`, `knowledge_used`, `content.reward`의 구체성을 올린다.

### 5.2 형식

`treatments/preprocess/{work_id}/densification/item_catalog.json`

```json
{
  "_description": "덴시피케이션용 아이템/레버리지 카탈로그",
  "items": [
    {
      "item_id": "ITM-001",
      "name": "윤성호텔 린넨실 출입기록 3개월치",
      "type": "evidence",
      "acquire_block": 11,
      "use_blocks": [12, 15],
      "narrative_value": "린넨 수량 vs 투숙객 수 불일치 → 서도윤 유령업체 장부 균열 증거",
      "expiry": "Block 20 이후 가치 소멸 (호텔 ARC 종료)"
    },
    {
      "item_id": "ITM-002",
      "name": "2019년 산업폐기물 단가 비교표",
      "type": "market_data",
      "acquire_block": 22,
      "use_blocks": [23, 25],
      "narrative_value": "경쟁 업체 대비 30% 고단가 계약의 증거 → 재계약 협상 레버리지",
      "expiry": null
    }
    // ... ARC당 최소 2개, 전체 15~20개
  ],
  "item_types": ["evidence", "contract", "market_data", "license", "system", "relationship", "intelligence"]
}
```

### 5.3 최소 요구

- 전체 15개 이상
- ARC당 최소 2개
- `type` 4종 이상 사용
- 각 아이템에 `acquire_block`, `use_blocks`, `narrative_value` 필수
- 추상적 아이템("경영 대시보드") 금지 — 구체적 실물/문서/데이터여야 함

---

## 6. 조건부 잠금 해제 절차 (20단계 중 5단계)

### 6.1 해제 가능 필드

`location.place`, `location.type`, `investment_type`

### 6.2 해제 조건

1. 4축 감사 보고서 또는 차이 행렬에서 해당 필드의 반복이 문제로 지적됨
2. 해제 근거 문서(`densification/conditional_unlock_log.md`)에 아래 기록:
   - 해제 대상 블록
   - 해제 사유 (구체적 차이 행렬 문항 번호)
   - 변경 전 값 → 변경 후 값
   - BI 재동기화 필요 여부
3. 사용자 승인 (자동 해제 금지)

### 6.3 해제 후 의무

- BI `plot_roadmap` 해당 블록의 동일 필드도 함께 수정
- 수정 후 BI PASS 2 (타이틀 시퀀스) 재검증

---

## 7. 덴시피케이션 배치 플래너 (20단계 중 6단계)

### 7.1 배치 구성 원칙

- **배치 크기: 3블록** (기존 production harness의 Batch 감리 단위와 동일)
- 고밀도 블록(skip_blocks)은 배치에서 제외
- 배치 순서: 아크 순서를 따름 (Block 7~10 → 11~13 → ...)
- 아크 경계를 배치가 넘지 않도록 함 (Block 9~10 + Block 11은 금지, Block 9~10은 2블록 배치)

### 7.2 배치 플랜 산출물

`treatments/preprocess/{work_id}/densification/batch_plan.json`

```json
{
  "total_rewrite_blocks": 64,
  "total_batches": 22,
  "batches": [
    {"batch_id": "DEN-001", "blocks": [7, 8, 9], "arc": "ARC-01", "status": "pending"},
    {"batch_id": "DEN-002", "blocks": [10], "arc": "ARC-01", "status": "pending"},
    {"batch_id": "DEN-003", "blocks": [11, 12, 13], "arc": "ARC-02", "status": "pending"},
    // ...
  ]
}
```

### 7.3 배치 실행 규칙

- 한 번에 1배치만 실행
- 배치 감리 PASS 후에만 다음 배치 진행
- 배치 내 블록은 순차 처리 (1블록씩 생성 → 검증 → 다음 블록)
- 배치 실패 시 해당 배치만 재실행 (이전 배치에 영향 없음)

---

## 8. Phase 0 보강 시트 (20단계 중 7단계)

### 8.1 목적

기존 phase0_design에 보조 입력 3종의 핵심 정보를 반영한 "보강 시트"를 별도로 생성. 원본 phase0_design은 수정하지 않는다.

### 8.2 산출물

`treatments/preprocess/{work_id}/densification/phase0_supplement.json`

```json
{
  "_description": "덴시피케이션 보강용 Phase 0 확장 시트",
  "source_phase0": "treatments/phase0/{work_id}_phase0_design.json",
  "historical_timeline_ref": "densification/historical_timeline.json",
  "external_opponent_pool_ref": "densification/external_opponent_pool.json",
  "item_catalog_ref": "densification/item_catalog.json",
  "arc_supplements": [
    {
      "arc": "ARC-01",
      "blocks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      "rewrite_blocks": [7, 8, 9, 10],
      "historical_events_assigned": ["HE-001", "HE-002"],
      "external_opponents_assigned": [],
      "items_assigned": ["ITM-001"],
      "weakness_pool_expansion": [
        "장례 의전업은 지자체 허가 갱신이 매년이라, 민원 1건으로 허가가 흔들린다"
      ],
      "deal_type_candidates": ["의전 독점 재계약", "장례 용품 직매입 전환", "셔틀 노선 통합권 확보"]
    }
    // ... 7개 아크 전체
  ]
}
```

### 8.3 보강 시트 검증

- 모든 `historical_events_assigned`가 `historical_timeline.json`에 존재
- 모든 `external_opponents_assigned`가 `external_opponent_pool.json`에 존재
- 모든 `items_assigned`가 `item_catalog.json`에 존재
- `rewrite_blocks`가 `skeleton_diagnosis.json`의 `rewrite_blocks`와 일치
- `weakness_pool_expansion`이 기존 weakness와 문장 유사도 0.5 미만

---

## 9. 블록 단위 덴시피케이션 (20단계 중 8단계)

### 9.1 실행 루틴 (1블록 기준)

```
[입력] 기존 스켈레톤 블록 + phase0 + 보강 시트 + 직전 2블록(고밀도 완성본)
  ↓
[사전 선언] §9.2의 10항 사전 선언
  ↓
[재작성] 재작성 필드 전량을 새로 작성
  ↓
[완성도 게이트] §9.1A 필수 필드 존재 확인 ← v2 추가
  ↓
[잠금 검증] 잠금 필드가 변경되지 않았는지 확인
  ↓
[자가 점검] §9.3의 Anti-Template 체크 12문항
  ↓
[골든 참조] §9.4의 골든 블록 참조 체크 ← v2 추가
  ↓
[저장] DEN-candidate로 저장
  ↓
[Python 교정] 자본 연속성/NPC before 리셋 등 기계적 교정
  ↓
[DEN-fixed 저장]
  ↓
[배치 내 다음 블록으로 이동]
```

### 9.1A 블록 완성도 게이트 (v2 추가)

JSON 생성 직후, Anti-Template 체크 전에 **필수 필드 존재 여부**를 확인한다.
하나라도 없으면 같은 블록을 즉시 재생성한다.

| # | 필드 | 확인 기준 | 미달 시 |
|---|------|----------|--------|
| CG-01 | `content.context` | 비어있지 않음, 50자 이상 | 재생성 |
| CG-02 | `content.event_villain` | 비어있지 않음, 100자 이상 | 재생성 |
| CG-03 | `content.solution` | 비어있지 않음, 100자 이상 | 재생성 |
| CG-04 | `content.reward` | 비어있지 않음, 50자 이상 | 재생성 |
| CG-05 | `stakes` | 비어있지 않음, 35자 이상 | 재생성 |
| CG-06 | `power_shift` | `protagonist`와 `antagonist` 모두 존재 | 재생성 |
| CG-07 | `relationship_delta` | 배열이고 길이 ≥ 2 | 재생성 |
| CG-08 | `foreshadow` | 객체 배열 존재 (빈 배열 허용). 각 원소: {"ref": N, "event": "서술"} | 재생성 |
| CG-09 | `callback` | 객체 배열 존재 (빈 배열 허용). 각 원소: {"ref": N, "event": "서술"} | 재생성 |
| CG-10 | `emotional_beat` | `type`과 `intensity` 모두 존재 | 재생성 |
| CG-11 | `tension_level` | 숫자, 1~10 | 재생성 |
| CG-12 | `location` | `place`와 `detail` 모두 존재 | 재생성 |
| CG-13 | `genre_ext` 또는 family HUD | family 필수 필드 존재 | 재생성 |

핵심 의미: **이 게이트는 밀도를 판정하는 것이 아니라, "블록의 형태가 완전한가"를 판정한다.** 밀도 판정은 Anti-Template(§9.3)과 밀도 스코어(§12)가 담당한다.

### 9.2 사전 선언 (블록 시작 전 필수 — v2: 6항→10항 확장)

블록 재작성 전에 아래 **10항**을 먼저 선언한다. 사전 선언 없이 JSON을 출력하면 무효 처리.

1. **이 블록의 고유 사건**: 스켈레톤과 다른 점 1문장
2. **이 블록의 적대자 행동과 합리적 이유**: planning harness 원칙 C의 `antagonist_model` 형식
3. **직전 2블록과의 차이**: solution/deal_type/weakness 중 무엇이 다른지
4. **이 블록에서 사용할 역사 이벤트** (있으면): `HE-XXX` ID
5. **이 블록에서 등장/사용할 아이템** (있으면): `ITM-XXX` ID
6. **regression_hint 고유화**: "의심한다" 외에 이 블록에서 구체적으로 어떤 slip-up이 발생하는지
7. **스켈레톤 대비 핵심 변화** (v2 추가): 원본 스켈레톤 블록과 이번 재작성의 핵심 차이를 1문장으로. "어떤 구체적 장면/인물/사물이 새로 생겼는가?" 단순 문장 확장은 변화로 보지 않는다.
8. **골든 블록 밀도 도달 자가 판정** (v2 추가): "이번 블록이 Block 1~6과 같은 밀도에 도달했는가?" YES/NO + 근거 1문장. NO이면 즉시 보강 후 재작성.
9. **보조 입력 주입 확인** (v2 추가): 이번 블록에 주입한 보조 입력 항목 ID를 열거. `HE-XXX`, `EXT-XXX`, `ITM-XXX` 중 0개이면 "해당 없음"이라 적되, 3배치 연속 0개이면 보강 시트를 재검토.
10. **잠금 필드 무변경 선언** (v2 추가): "잠금 필드 14개가 원본과 동일하다"를 1문장으로 선언. 확인하지 않고 선언하면 무효.

### 9.3 Anti-Template 체크 12문항

블록 재작성 후 즉시 자가 점검. 하나라도 FAIL이면 같은 블록 재작성.

| # | 문항 | FAIL 조건 |
|---|------|-----------|
| AT-01 | event_villain 첫 문장이 직전 3블록과 구조적으로 동일한가? | 동일 |
| AT-02 | solution 첫 문장에 "병목이 터질 순서를 다시 계산한다"가 포함되는가? | 포함 |
| AT-03 | stakes에 "[블록명]를 놓치면"이 패턴으로 시작하는가? | 시작 |
| AT-04 | power_shift에 "[블록명]를 통해"가 패턴으로 시작하는가? | 시작 |
| AT-05 | relationship_delta.after에 "같이 붙어도 돈이 되는 운영 파트너"가 포함되는가? | 포함 |
| AT-06 | regression_hint에 "정보 출처를 의심한다"만 있는가? | "의심한다"만 |
| AT-07 | emotional_beat.type이 직전 블록과 동일한가? | 동일 |
| AT-08 | deal_type이 직전 3블록 이내 재등장하는가? | 재등장 |
| AT-09 | leverage_used가 직전 3블록과 완전 동일 세트인가? | 동일 |
| AT-10 | execution_doctrine이 직전 5블록 이내 동일 문장인가? | 동일 |
| AT-11 | method가 직전 3블록과 동일한가? | 동일 |
| AT-12 | 조사 오류("반장로서", "양수을" 등)가 있는가? | 있음 |

### 9.4 골든 블록 참조 체크 (v2 추가)

Anti-Template 통과 후, DEN-candidate 저장 전에 **Block 1~6(또는 skip_blocks로 지정된 고밀도 블록)과의 밀도 비교**를 수행한다.

| # | 비교 항목 | 기준 | FAIL 시 |
|---|----------|------|---------|
| GR-01 | `avg_bundle_chars` | 이번 블록 ≥ 골든 블록 평균의 80% | 서사 내용 보강 후 재작성 |
| GR-02 | `relationship_delta` 대상 수 | 이번 블록 ≥ 2명 | NPC 추가 |
| GR-03 | `foreshadow + callback` 합계 | 이번 블록 ≥ 1건 | 복선 심기 또는 회수 추가 |
| GR-04 | `opponent` 구체성 | `name`, `weakness_exploited` 모두 비어있지 않음 | 적대자 정보 보강 |
| GR-05 | `stakes` 길이 | ≥ 50자 | 구체적 손실/위험 서술 보강 |

전 항목 PASS가 아니면 DEN-candidate로 저장하지 않는다.

핵심 의미: "Block 1~6 수준의 밀도"는 추상적 목표가 아니라 **측정 가능한 기준선**이다. 이 체크가 그 기준선을 강제한다.

### 9.5 출력 형식 강제 규칙 (v2 추가 — LLM 자동화 방지)

**원칙: "PASS"만 쓰면 무효. 반드시 수치와 근거를 함께 출력해야 인정.**

LLM은 자가 점검을 형식적으로 "전량 PASS"라고만 쓰고 넘어가려는 경향이 있다. 이를 방지하기 위해 아래 출력 형식을 **필수**로 강제한다. 형식이 없으면 해당 블록의 DEN-candidate를 인정하지 않는다.

#### A. 사전 선언 출력 형식

반드시 `### 사전 선언 — Block {N}` 헤더 아래에 10항을 자연어로 작성한다. JSON 출력 전에 이 블록이 없으면 JSON 자체를 무시한다.

```markdown
### 사전 선언 — Block {N}
1. 고유 사건: [1문장]
2. 적대자 행동/이유: [1~2문장]
3. 직전 차이: solution=[X→Y], deal_type=[X→Y], weakness=[X→Y]
4. 역사 이벤트: HE-XXX 또는 해당 없음
5. 아이템: ITM-XXX 또는 해당 없음
6. regression_hint: [구체적 slip-up]
7. 스켈레톤 대비 변화: [새로 생긴 장면/인물/사물]
8. 골든 밀도 도달: YES — [근거] / NO — [미달 사유]
9. 보조 입력 주입: HE-002, ITM-005 / 해당 없음 (연속 N배치)
10. 잠금 필드 무변경: 확인 완료 — [block_id/title/capital_before 등 3개 샘플 대조]
```

#### B. 완성도 게이트 출력 형식

반드시 수치와 함께 표로 출력한다. "재생성" 판정이 1개라도 있으면 JSON을 폐기하고 재작성.

```markdown
### 완성도 게이트 — Block {N}
| # | 필드 | 기준 | 실제 | 판정 |
|---|------|------|------|------|
| CG-01 | context | ≥50자 | 152자 | ✅ |
| CG-02 | event_villain | ≥100자 | 220자 | ✅ |
| ...
| CG-13 | genre_ext | 필수 필드 존재 | 전부 존재 | ✅ |
```

#### C. Anti-Template 체크 출력 형식

각 문항에 대해 PASS/FAIL + 근거 1문장을 출력한다. "전량 PASS" 한 줄은 무효.

```markdown
### Anti-Template 체크 — Block {N}
| # | 문항 | 판정 | 근거 |
|---|------|------|------|
| AT-01 | event_villain 구조 | ✅ | 직전 3블록은 "내부 반란" 구조, 이번은 "외부 M&A 방어" |
| AT-02 | solution 패턴 | ✅ | "정보 비대칭 활용" — 금지 패턴 미해당 |
| ...
| AT-12 | 조사 오류 | ✅ | 교정 완료, "로서/으로서" 확인 |
```

#### D. 골든 블록 참조 출력 형식

반드시 골든 블록 평균 수치와 이번 블록 수치를 병기한다.

```markdown
### 골든 블록 참조 — Block {N}
| # | 항목 | 골든 평균 | 이번 블록 | 비율 | 판정 |
|---|------|----------|----------|------|------|
| GR-01 | bundle_chars | 850자 | 780자 | 92% | ✅ |
| GR-02 | relationship_delta | 3명 | 2명 | - | ✅ |
| GR-03 | foreshadow+callback | 2건 | 1건 | - | ✅ |
| GR-04 | opponent name | 있음 | "서도윤" | - | ✅ |
| GR-05 | stakes 길이 | 80자 | 65자 | - | ✅ |
```

#### E. 위반 시 처리

- 위 A~D 형식 중 하나라도 누락되면 → DEN-candidate 불인정, 같은 블록 재시작
- "전량 PASS"만 적고 수치/근거가 없으면 → 무효, 재출력
- 연속 3블록 이상 모든 항목이 "✅ PASS"이면 → 밀도 스코어(§12)로 교차 검증 후 진짜 고밀도인지 확인

---

## 10. 배치 감리 (20단계 중 9단계)

### 10.1 3-Pass 배치 감리

배치(3블록) 완료 후 아래 감리를 수행한다.

**Pass 1: 잠금 무결성**
- 잠금 필드 14개가 원본과 100% 동일
- `capital_before(N) == capital_after(N-1)` 연속성 유지

**Pass 2: 밀도 비교**
- 배치 내 블록의 `avg_bundle_chars` vs 스켈레톤 원본
- 최소 2배 이상 증가 필수 (스켈레톤 280자 → 최소 560자, 목표 800자+)
- Anti-Template 12문항 전량 PASS

**Pass 3: 서사 차별성**
- 배치 내 3블록의 event_villain/solution/stakes가 서로 다른가?
- 직전 배치(DEN-N-1)의 마지막 블록과의 연속성 확인
- 보강 시트의 assigned 항목이 실제 반영되었는가?

**Pass 4: 37문항 차이 행렬 (v2 추가)**

배치 감리 시 production harness §3.4의 29문항 + 덴시피케이션 전용 8문항(§17) = **37문항 통합 차이 행렬**을 필수로 출력한다.

출력 형식:

```
| Block | beat_type | intensity | tension | deal_type | opponent | location | duration | capital_delta | 성장률 | success | DEN밀도 | 역사이벤트 | 거물등장 | 아이템사용 |
|-------|-----------|-----------|---------|-----------|----------|----------|----------|---------------|--------|---------|---------|-----------|---------|-----------|
```

자가 검증 규칙: production harness 29문항 + densification 8문항(DM-30~37) 전량 적용.
1개라도 FAIL이면 해당 블록만 재작성 후 행렬 재출력.

### 10.2 감리 결과 저장

`treatments/audit_reports/{work_id}_den_batch_NNN_audit.md`

배치 감리 보고서에는 반드시 아래를 포함:

1. 3-Pass + 차이 행렬 결과
2. 배치 내 각 블록의 밀도 스코어 (§12)
3. 골든 블록 참조 체크 결과 (§9.4)
4. 완성도 게이트 통과 여부 (§9.1A)

---

## 11. 아크 단위 중간 검증 (20단계 중 10단계)

10블록(1 ARC) 분량의 배치가 모두 완료될 때마다 아크 단위 검증을 수행한다.

### 11.1 아크 밀도 검증

| 지표 | 기준 |
|------|------|
| `avg_bundle_chars` (아크 평균) | >= 750 |
| `opponent_unique` (아크 내) | >= 3 |
| `deal_type_unique` (아크 내) | >= 5 |
| `historical_event_used` (아크 내) | >= 1 |
| `item_used` (아크 내) | >= 1 |
| `weakness_unique` (아크 내) | >= 3 |
| `template_similarity_avg` (아크 내) | < 0.3 |
| `emotional_beat_types` (아크 내) | >= 4종 |
| `defeat_block_present` | 최소 1개 |

### 11.2 아크 서사 검증

- 아크 입구/출구가 phase0 설계와 정합
- 아크 내 에스컬레이션 3축(경제 규모, 이해관계 복잡도, 비가역성) 중 최소 1축 상승
- 아크 내 패배 블록이 기계적 위치(정확히 5번째)가 아닌가?
- 외부 거물이 ARC-05 이후 최소 1명 등장하는가?

### 11.3 실패 시

아크 단위 검증 FAIL → 해당 아크의 가장 약한 배치만 재실행 (전체 아크 재실행이 아님)

---

## 12. 밀도 스코어 산출 (20단계 중 11단계)

### 12.1 블록별 밀도 스코어 (0~100)

```
density_score = (
    chars_score        * 0.20 +  # bundle_chars 기반 (800+ = 20점)
    villain_score      * 0.15 +  # event_villain 구체성/고유성
    solution_score     * 0.15 +  # solution 전술 차별성
    opponent_score     * 0.10 +  # opponent 정보 완비도 (5필드)
    historical_score   * 0.10 +  # historical_event 존재/구체성
    item_score         * 0.10 +  # leverage/item 활용도
    callback_score     * 0.10 +  # foreshadow/callback 진정성 (기계 패턴 아닌)
    regression_score   * 0.10    # regression_hint/butterfly_effect 고유성
)
```

### 12.2 등급

| 등급 | 점수 | 판정 |
|------|------|------|
| A | 85~100 | 출고 가능, Block 1~6 수준 |
| B | 70~84 | 출고 가능, 양호 |
| C | 50~69 | 조건부 출고, 권장 재작성 |
| D | 30~49 | 출고 불가, 필수 재작성 |
| F | 0~29 | 스켈레톤 수준, 반드시 재작성 |

### 12.3 출고 게이트

- 전 블록 D 이하 0개
- 전 블록 평균 70점 이상
- C 등급 블록 전체의 15% 이하

---

## 13. 회귀 설정 정합 보강 (20단계 중 12단계)

### 13.1 회귀 시점 공백 해소

4축 감사에서 지적된 C-01(회귀 시점 2006 vs 스토리 시작 2018) 문제를 해소한다.

**선택지**:
- (A) `protagonist_config.regression_point.return_year`를 2018로 수정 → 가장 단순
- (B) Block 0(프롤로그)를 추가하여 2006~2018 요약 → 블록 수가 71이 되므로 BI 재동기화 필요
- (C) phase0_supplement에 "2006~2018 기간 설정"을 추가하고, Block 1 context에서 1~2문장으로 언급 → 구조 변경 없이 해소

### 13.2 regression_hint 차별화 전략

70블록 "의심한다" 반복을 해소하기 위한 5단계 에스컬레이션:

| 단계 | 블록 범위 | regression_hint 패턴 |
|------|----------|---------------------|
| 1. 무의식적 위화감 | 1~14 | 주변 인물이 "타이밍이 좋다" 정도로 느끼는 수준. 구체적 의심 없음 |
| 2. 패턴 인식 | 15~28 | 한유림/노현주가 "우연이 너무 많다"고 기록하기 시작 |
| 3. 능동적 검증 | 29~42 | 윤석진이 재이의 과거 투자 이력을 역추적. 구체적 증거 수집 시도 |
| 4. 직접 대면 | 43~56 | 서도윤이 "어디서 이 정보를 얻었냐"고 직접 추궁. 재이의 위기 |
| 5. 전략적 활용 | 57~70 | 재이가 회귀 의심을 역으로 이용("내가 미래를 아는 것처럼 보이게"). 의심 자체가 레버리지 |

---

## 14. 복선-콜백 재구축 (20단계 중 13단계)

### 14.1 기존 복선 유지 + 신규 추가

- phase0의 기존 6개 복선(`seed_block`, `payoff_block`)은 **잠금** — 위치/회수 블록 변경 금지
- 덴시피케이션에서 추가할 수 있는 복선: **아크 내 단기 복선** (3~7블록 이내 회수)
- 단기 복선 추가 시 `foreshadow` 필드에 기입하고, 대응 `callback`도 반드시 배치 내에서 지정

### 14.1.1 foreshadow/callback 필드 형식

foreshadow[]와 callback[]은 string 배열이 아니라 **객체 배열**로 작성한다.

```json
"foreshadow": [
    {"ref": 31, "event": "서사적 사건 서술 (블록 번호 노출 금지)"}
],
"callback": [
    {"ref": 15, "event": "서사적 회수 서술 (블록 번호 노출 금지)"}
]
```

**블록 번호 본문 노출 금지**: TR 블록의 **모든 텍스트 필드**에 "B숫자", "Block 숫자", "블록 숫자" 패턴 금지.
대상: content.*, stakes, power_shift.*, relationship_delta[].before/after,
foreshadow[].event, callback[].event, genre_ext.*/regression_ext.* 내 텍스트 필드.
foreshadow/callback의 블록 참조는 ref 필드에만 기입한다.
이유: TR의 모든 텍스트가 downstream 원고 생성에 흐르므로 메타 번호의 작중 오염을 방지.

### 14.2 콜백 진정성 검증

기존 스켈레톤의 기계적 콜백("N-1블록에서 남긴 기준 메모를 이번 블록의 기준표로 꺼낸다")을 탐지하고 재작성.

**기계적 콜백 판별 기준**:
- 직전 블록만 참조 (1블록 거리)
- "기준 메모", "기준표", "다시 꺼낸다" 등 반복 어구
- 서사적 의미 없이 형식만 채운 콜백

재작성 시 콜백은 **구체적 서사 사건**을 참조해야 한다.

---

## 15. relationship_delta 개별화 (20단계 중 14단계)

### 15.1 문제

"같이 붙어도 돈이 되는 운영 파트너라고 본다"가 30회 반복.

### 15.2 해소 전략

- 각 NPC의 `relationship_delta.after`는 **해당 블록의 사건에 구체적으로 반응**해야 한다
- 동일 NPC라도 블록마다 관계의 다른 측면이 변화 (예: 신뢰 → 의존 → 경계 → 동맹 → 거래적 관계)
- planning harness의 **신용 잔고 시스템** 적용: 적립/인출이 눈에 보여야 함

### 15.3 검증

- 동일 `after` 문장이 3회 이상 등장하면 FAIL
- 70블록 전체 `relationship_delta.after` 고유 문장 비율 80% 이상

---

## 16. 감정 곡선 재설계 (20단계 중 15단계)

### 16.1 기존 문제

- `emotional_beat.type` 반복 (같은 ARC 내 동일 타입 연속)
- `tension_level`이 기계적 (ARC 시작=5, 중간=패배, 끝=8~9)

### 16.2 재설계 원칙

- production harness의 20종 감정 비트 목록 활용
- ARC 내 최소 4종 이상 사용
- tension_level은 잠금 필드가 아니므로 재작성 가능
- 패배 블록 직후의 tension 낙차 → 회복 곡선이 자연스러워야 함
- 최종 10블록(61~70)은 tension 7 이상 유지

---

## 17. 전체 차이 행렬 검증 (20단계 중 16단계)

전 블록 덴시피케이션 완료 후, production harness의 **차이 행렬 29문항**을 전수 적용한다.

### 17.1 추가 문항 (덴시피케이션 전용 8문항)

| # | 문항 | FAIL 조건 |
|---|------|-----------|
| DM-30 | historical_event null 비율 | 50% 초과 |
| DM-31 | 외부 거물 미등장 (ARC-05~07) | 0명 |
| DM-32 | 아이템/레버리지 카탈로그 미활용 비율 | 70% 초과 |
| DM-33 | regression_hint 5단계 에스컬레이션 미반영 | 미반영 |
| DM-34 | relationship_delta.after 동일 문장 3회 이상 | 존재 |
| DM-35 | 패배 블록이 정확히 아크 5번째에만 위치 | 전부 5번째 |
| DM-36 | 밀도 스코어 D등급 이하 존재 | 존재 |
| DM-37 | 조사 오류/문법 오류 잔존 | 존재 |

### 17.2 통과 기준

- 기존 29문항 + 추가 8문항 = 37문항 전량 PASS
- FAIL 문항이 있으면 해당 블록만 재작성 (전체 재실행 아님)

---

## 18. BI 재동기화 (20단계 중 17단계)

### 18.1 목적

덴시피케이션으로 TR의 재작성 필드가 변경되었으므로, BI의 `plot_roadmap`을 재동기화한다.

### 18.2 절차

1. 덴시피케이션 완료 TR draft를 원천으로 BI `plot_roadmap` 재복사
2. `FinanceHUD` 갱신 (TR 최종 `capital_after` 반영)
3. `Seeds` echo_count / harvested_ep 갱신
4. `KarmaMatrix` 채움
5. `HistoricalEvents` Block 16~70 보완
6. BI 5-Pass 감리 재실행

### 18.3 잠금 필드 무변경 확인

TR의 잠금 필드가 변경되지 않았으므로, BI PASS 2 (타이틀 시퀀스)와 PASS 3 (자본 동기화)는 자동 통과가 기대된다. 단, 반드시 재검증.

---

## 19. 최종 밀도 게이트 (20단계 중 18단계)

### 19.1 production_density_gate 재검

production harness의 원래 밀도 게이트를 덴시피케이션 완료 TR에 재적용한다.

| 지표 | 기준 | 스켈레톤 상태 | 목표 |
|------|------|-------------|------|
| `avg_bundle_chars` | >= 350 (P0) | ~280 | >= 800 |
| `critical_thin_blocks` | 0 | ~60 | 0 |
| `opponent_unique` | >= 8 | ~8 (이름은 다르나 실질 차이 없음) | >= 15 |
| `callback_ratio` | >= 0.65 | 형식적 | >= 0.65 (실질적) |
| `deal_type 종류` | >= 10 | ~10 (반복) | >= 15 |
| `deal_top_repetition` | <= 4 | ~7 | <= 4 |
| 단일 opponent 점유율 | <= 30% | ~25% | <= 20% |

### 19.2 통과 기준

- P0 게이트 전량 PASS (필수)
- P1 게이트 전량 PASS (권장, 1~2개 미달 허용)
- 밀도 스코어 전 블록 평균 70점 이상

---

## 20. 출고 및 상태 전이 (20단계 중 19~20단계)

### 20.1 단계 19: 최종 감리 보고서

`treatments/audit_reports/{work_id}_densification_final_report.md`

```markdown
# 덴시피케이션 최종 보고서

## 대상
- work_id: {work_id}
- 원본 스켈레톤 블록 수: N
- 덴시피케이션 블록 수: M
- 스킵 블록 수: K

## 밀도 변화
- avg_bundle_chars: 280 → 850 (+203%)
- opponent_unique: 8 → 16 (+100%)
- historical_event 비율: 3% → 60%
- 밀도 스코어 평균: 25 → 78

## 차이 행렬
- 기존 29문항: 전량 PASS
- 추가 8문항: 전량 PASS

## BI 재동기화
- 5-Pass 재감리: 전량 PASS

## 판정
- densification_gate: PASS / FAIL
```

### 20.2 단계 20: 상태 전이

| 시나리오 | 전이 |
|----------|------|
| PASS | TR draft를 `densified` 상태로 마킹. BI 재동기화 완료. 원고 생산 진입 가능 |
| 부분 FAIL | 실패 블록/아크만 재실행. 전체 재실행 불요 |
| 전면 FAIL | 덴시피케이션 접근 실패. phase0 보강 후 전면 리프로덕션(방안 A) 검토 |

### 20.3 산출물 목록 (전체)

```
treatments/preprocess/{work_id}/densification/
  ├── historical_timeline.json         (§3)
  ├── external_opponent_pool.json      (§4)
  ├── item_catalog.json                (§5)
  ├── conditional_unlock_log.md        (§6, 필요 시)
  ├── batch_plan.json                  (§7)
  ├── phase0_supplement.json           (§8)
  ├── skeleton_diagnosis.json          (§2)
  └── regression_escalation_plan.md    (§13)

treatments/audit_reports/
  ├── {work_id}_skeleton_diagnosis.json
  ├── {work_id}_den_batch_NNN_audit.md  (배치별)
  ├── {work_id}_den_arc_NN_audit.md     (아크별)
  └── {work_id}_densification_final_report.md
```

---

## 부록 A: 20단계 요약 체크리스트

| 단계 | 이름 | 섹션 | 산출물 |
|------|------|------|--------|
| 1 | 스켈레톤 진단 | §2 | skeleton_diagnosis.json |
| 2 | 역사 이벤트 타임라인 | §3 | historical_timeline.json |
| 3 | 외부 거물 풀 | §4 | external_opponent_pool.json |
| 4 | 아이템/레버리지 카탈로그 | §5 | item_catalog.json |
| 5 | 조건부 잠금 해제 | §6 | conditional_unlock_log.md |
| 6 | 배치 플래너 | §7 | batch_plan.json |
| 7 | Phase 0 보강 시트 | §8 | phase0_supplement.json |
| 8 | 블록 단위 덴시피케이션 | §9 | DEN-candidate/DEN-fixed 파일 |
| 9 | 배치 감리 | §10 | den_batch_NNN_audit.md |
| 10 | 아크 단위 중간 검증 | §11 | den_arc_NN_audit.md |
| 11 | 밀도 스코어 산출 | §12 | 블록별 점수 |
| 12 | 회귀 설정 정합 보강 | §13 | regression_escalation_plan.md |
| 13 | 복선-콜백 재구축 | §14 | foreshadow/callback 재작성 |
| 14 | relationship_delta 개별화 | §15 | delta 재작성 |
| 15 | 감정 곡선 재설계 | §16 | emotional_beat/tension 재작성 |
| 16 | 전체 차이 행렬 검증 | §17 | 37문항 결과 |
| 17 | BI 재동기화 | §18 | BI 갱신 + 5-Pass 재감리 |
| 18 | 최종 밀도 게이트 | §19 | density_gate 판정 |
| 19 | 최종 감리 보고서 | §20.1 | densification_final_report.md |
| 20 | 상태 전이 | §20.2 | densified 마킹 |

---

## 부록 B: 기존 하네스와의 관계

```
treatment-planning-harness.md
  │
  ▼
treatment-production-harness-v2.md
  │
  ├─ [정상 경로] → bi-production-harness-v1.md → 원고 생산
  │
  └─ [밀도 부족 판정] → treatment-densification-harness-v1.md (이 문서)
                            │
                            └─ [완료] → bi-production-harness-v1.md (BI 재동기화) → 원고 생산
```

---

## 부록 C: 컨텍스트 윈도우 대응 (v2 확장)

기본 규칙:

- 덴시피케이션 배치(3블록)는 production harness와 동일한 컨텍스트 관리를 따른다
- 배치 완료 시마다 즉시 `tr_block_070_draft.json`에 merge 저장
- 5배치(15블록)마다 중간 정합성 체크 권장
- context window 한계 도달 시 현재 배치 완료 후 저장, resume prompt 안내

### Resume Prompt 전문 (v2 추가)

compaction 또는 세션 전환 후 재진입 시 아래를 순서대로 재로드한다:

```
=== 덴시피케이션 Resume Prompt ===

1. 이 하네스 `treatment-densification-harness-v1.md`를 UTF-8로 다시 읽는다.
2. 아래 파일을 순서대로 UTF-8로 다시 연다:
   - `treatments/phase0/{work_id}_phase0_design.json`
   - `treatments/{work_id}_tr_block_070_draft.json` (원본 스켈레톤 + merge 완료분)
   - `treatments/preprocess/{work_id}/densification/batch_plan.json`
   - `treatments/preprocess/{work_id}/densification/phase0_supplement.json`
   - `treatments/preprocess/{work_id}/densification/historical_timeline.json`
   - `treatments/preprocess/{work_id}/densification/external_opponent_pool.json`
   - `treatments/preprocess/{work_id}/densification/item_catalog.json`
3. `batch_plan.json`에서 마지막 `status: "done"` 배치를 찾는다.
4. 해당 배치의 마지막 블록(DEN-fixed)을 직전 상태로 삼는다.
5. 다음 `status: "pending"` 배치의 첫 블록부터 재개한다.
6. 재개 첫 블록은 반드시 10항 사전 선언부터 시작한다.

=== 필수 확인 ===
- 직전 DEN-fixed 블록의 capital_after: ___
- 직전 DEN-fixed 블록의 마지막 NPC 관계 상태: ___
- 미회수 복선 목록: ___
- 현재 배치 ID: DEN-___
```

이 resume prompt를 따르지 않고 "기억으로" 재개하는 것은 무효다.

---

## 부록 D: 실행 순서 요약

```
진입 게이트 확인 (§0C)
  ↓
단계 1: 스켈레톤 진단 (§2)
  ↓
단계 2~4: 보조 입력 3종 생성 (§3~§5)  ← 병렬 가능
  ↓
단계 5: 조건부 잠금 해제 (§6)  ← 필요 시에만
  ↓
단계 6: 배치 플래너 (§7)
  ↓
단계 7: Phase 0 보강 시트 (§8)
  ↓
단계 8~10: 배치 순환 [블록 재작성 → 배치 감리 → 아크 검증] (§9~§11)
  ├─ 단계 11: 밀도 스코어 산출 (§12)  ← 배치마다
  ├─ 단계 12: 회귀 설정 보강 (§13)    ← 첫 배치 전 1회
  ├─ 단계 13: 복선-콜백 재구축 (§14)   ← 배치 내
  ├─ 단계 14: relationship_delta 개별화 (§15) ← 배치 내
  └─ 단계 15: 감정 곡선 재설계 (§16)   ← 배치 내
  ↓
단계 16: 전체 차이 행렬 검증 (§17)
  ↓
단계 17: BI 재동기화 (§18)
  ↓
단계 18: 최종 밀도 게이트 (§19)
  ↓
단계 19: 최종 감리 보고서 (§20.1)
  ↓
단계 20: 상태 전이 (§20.2)
```
