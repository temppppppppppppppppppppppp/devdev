# Treatment Densification Harness v1 — Wuxguide (무협/선협 전용)

> **목적**: 이미 70블록 스켈레톤이 완성된 TR draft를, 구조적 뼈대를 보존한 채 Block 1~6 수준의 서사 밀도로 끌어올리는 전용 하네스.
>
> **SSOT 위치**: `docs/wuxguide/treatment-densification-harness-v1.md`
>
> **선행 조건**: `wuxia-production-harness.md`로 생산된 70블록 TR draft가 존재하고, BI 5-Pass 감리까지 통과한 상태에서, 내용적 밀도가 부족하다고 판정된 경우에만 진입한다.
>
> **관계**:
> - `wuxia-planning-harness.md` → Phase 0 원천 (읽기 전용)
> - `wuxia-production-harness.md` → 밀도 게이트/차이 행렬/절대 금지 규칙 상속
> - `wuxia-bi-production-harness.md` → 덴시피케이션 완료 후 BI 재동기화 시 참조
> - 이 하네스는 `wuxia-production-harness.md`의 **후처리 확장**이지, 대체가 아니다
> - `blockguide/treatment-densification-harness-v1.md` §0D의 family-agnostic 보조 입력 인터페이스를 준수한다

---

## 0A. 빠른 시작 (10단계 즉시 체크리스트)

1. `treatments/{work_id}_tr_block_070_draft.json` 존재 확인
2. `treatments/{work_id}_phase0_design.json` 존재 확인
3. `bible/{work_id}_bi.json` 존재 확인 (BI 5-Pass PASS 상태)
4. 덴시피케이션 진입 사유 확인 (4축 감사 or 밀도 게이트 FAIL)
5. 잠금/재작성 필드 분류표(§1) 확인
6. 무협 전용 보조 입력 3종(§3~§5) 존재 확인 (없으면 먼저 생성)
7. 덴시피케이션 배치 플래너(§7) 작성
8. Block 1~6은 스킵 대상인지 확인 (이미 고밀도이면 잠금)
9. 첫 배치 실행 (§9)
10. 배치 감리 통과 후 다음 배치 진행 (§10~§11)

### 즉시 금지 3개

- 잠금 필드를 수정하면서 "밀도 개선"이라고 부르는 것 → REJECT
- 보조 입력 없이 "기억으로" 무공/세력을 주입하는 것 → REJECT
- 70블록 일괄 재작성 → REJECT (배치 단위 순차 처리만 허용)

---

## 0B. 용어 정의

| 용어 | 정의 |
|------|------|
| **스켈레톤 블록** | `avg_bundle_chars < 350` 이거나, solution/event_villain/stakes 중 2개 이상이 다른 블록과 동일 문장 패턴인 블록 |
| **고밀도 블록** | `avg_bundle_chars >= 800`, 차이 행렬 전량 PASS, 블록 고유 event_villain/solution 보유 |
| **잠금 필드** | 덴시피케이션 과정에서 변경 금지인 구조적 필드 |
| **재작성 필드** | 덴시피케이션 대상인 서사 내용 필드 |
| **보조 입력** | 덴시피케이션 품질을 올리기 위해 phase0 외에 추가로 제공하는 참조 자료 |
| **밀도 스코어** | 블록 단위 정량 품질 점수 (§12 참조) |
| **DEN-candidate** | 덴시피케이션용 후보 블록 (기존 candidate와 구분) |
| **DEN-fixed** | 덴시피케이션용 교정 완료 블록 |
| **MartialHUD** | 경지/내공/무공/문파/강호 평판을 추적하는 무협 전용 성장 추적 시스템 |
| **경지** | realm — 무공 수련 단계 (예: 후천, 선천, 화경, 반허) |
| **내공** | internal_energy — 주인공이 축적한 내력 수치 |

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
   - 차이 행렬 문항 중 3개 이상 FAIL

---

## 1. 잠금/재작성 필드 분류 (MartialHUD 기반)

### 1.1 잠금 필드 (Structural Lock)

절대 변경 금지. 이 필드가 바뀌면 BI와의 정합성이 깨진다.

```
block_id
title
realm_before
realm_after
internal_energy_before
internal_energy_after
internal_energy_delta
time_span.duration
time_span.in_story_time
section_rotation
pov_character
faction_status.affiliation
faction_status.rank
martial_domain
```

### 1.2 조건부 잠금 필드 (Conditional Lock)

기본 잠금이나, 보조 입력에 근거가 있을 때 **§6 조건부 해제 절차**를 거쳐 수정 가능.

```
location.place          -- 장소가 너무 반복적일 때만 해제
location.detail         -- 위와 동일
faction_status.standing -- 문파 내 위상이 서사적으로 불합리할 때만 해제
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
relationship_delta[]      -- target/before/after 전량
foreshadow[]
callback[]
emotional_beat.type
emotional_beat.intensity
tension_level
martial_ext.strategy
martial_ext.action_type
martial_ext.technique_used[]
martial_ext.opponent{}
martial_ext.terrain_advantage
martial_ext.injury{}
martial_ext.breakthrough{}
martial_ext.leverage_used[]
martial_ext.risk_level
martial_ext.success_pattern
```

### 1.4 분류표 검증

- 잠금 필드 수정 시도 → DEN-candidate 즉시 REJECT
- 경지/내공의 before/after가 변경되면 BI 전체 경지 로드맵과 충돌

---

## 2. 스켈레톤 진단 (20단계 중 1단계)

### 2.1 전 블록 스켈레톤 스캔

기존 TR draft 70블록을 대상으로 아래 지표를 산출한다.

```python
for block in tr_draft:
    bundle_chars = len(context + event_villain + solution + reward + stakes)
    is_skeleton = bundle_chars < 350
    template_score = measure_template_similarity(block, all_blocks)
```

**산출물**: `treatments/audit_reports/{work_id}_skeleton_diagnosis.json`

### 2.2 고밀도 블록 잠금 판정

Block 1~6처럼 이미 `avg_bundle_chars >= 800` + 차이 행렬 PASS인 블록은 **스킵 대상**으로 분류한다.

---

## 3. 보조 입력 1: 무공/비급 획득 타임라인 (20단계 중 2단계)

### 3.1 목적

작품의 시간축에 주인공과 주변 인물의 무공 습득/경지 돌파 이벤트를 배치하여, 블록별 `strategy`, `technique_used`, `breakthrough`의 구체적 근거를 제공한다.

### 3.2 형식

`treatments/preprocess/{work_id}/densification/martial_timeline.json`

```json
{
  "_description": "작중 시간축에 대응하는 무공/경지 이벤트",
  "events": [
    {
      "event_id": "MA-001",
      "block_range": [1, 5],
      "event": "후천 무공 기초 수련 — 가문 전래 심법 '원양공'을 체내 소주천 완성까지 수련",
      "technique_gained": "원양공 1~3성",
      "realm_impact": "후천 초기 → 후천 중기",
      "narrative_leverage": "저급 무공이지만 체계적 수련으로 기반 탄탄, 내공 순환 효율 우위"
    },
    {
      "event_id": "MA-002",
      "block_range": [6, 10],
      "event": "비급 '빙심결' 획득 — 폐허가 된 고찰의 암벽 뒤 비밀실에서 발견",
      "technique_gained": "빙심결 입문",
      "realm_impact": "후천 중기 유지",
      "narrative_leverage": "빙화 속성의 내공이 원양공의 열속성과 상극 → 조화 문제가 장기 복선"
    }
  ]
}
```

### 3.3 최소 요구

- ARC당 최소 1건 (7 ARC × 1 = 7건 이상)
- 전체 15건 이상
- 작중 무공 체계에 기반 (설정에 없는 무공 날조 금지)
- 경지 돌파는 phase0의 `realm_progression` 로드맵과 정합
- 무공 습득 → 실전 사용까지의 블록 갭이 최소 3블록 (즉시 마스터 금지)

### 3.4 작성 방법

Phase 0의 경지 로드맵과 무공 목록을 기반으로 LLM이 작성. 작품 내 설정 자료(bible)와 대조 1회 필수.

---

## 4. 보조 입력 2: 강호 세력 풀 (20단계 중 3단계)

### 4.1 목적

기존 TR의 적대자가 문파 내부 인물이나 초반 악역에 집중되는 문제를 해소. 후반 ARC에 적합한 강호 외부 세력을 사전 설계한다.

### 4.2 형식

`treatments/preprocess/{work_id}/densification/jianghu_force_pool.json`

```json
{
  "_description": "덴시피케이션용 강호 세력 풀",
  "forces": [
    {
      "force_id": "JH-001",
      "name": "혈영문(血影門)",
      "type": "마교 분파",
      "leader": "혈영노(血影老) 적무량",
      "arc_range": [4, 5, 6],
      "goal": "중원 무림맹의 세력 약화를 위해 내부 분열 공작",
      "rational_action": "주인공의 문파에 위장 제자를 침투시켜 핵심 무공의 약점을 파악",
      "information_state": "주인공 문파의 외부 전력은 파악하나 내부 비전은 모름",
      "weakness": "혈영문 자체가 마교 본산의 지원 없이는 독립 유지 불가",
      "why_loses": "주인공이 마교 본산에 혈영문의 독자행동을 밀고 → 보급선 차단"
    }
  ]
}
```

### 4.3 최소 요구

- 총 5개 이상 세력
- ARC-04 이후 최소 3개 세력 배치
- 기존 초반 적대자와 **중복 금지**
- 각 세력에 `goal`, `rational_action`, `information_state`, `weakness`, `why_loses` 필수
- 세력 유형 최소 3가지 (정파/사파/마교/관부/상단/세가 등)

### 4.4 기존 적대자와의 관계

외부 세력은 기존 내부 적대자와 **연합하거나 독립적으로** 움직일 수 있다. 덴시피케이션 시 기존 `martial_ext.opponent`를 외부 세력 인물로 교체하거나 보조 적대자로 추가하는 것 모두 허용.

---

## 5. 보조 입력 3: 신병이기/영약/비급 카탈로그 (20단계 중 4단계)

### 5.1 목적

기존 TR의 추상적 보물/보상을 구체적 물리 아이템으로 확장. 블록별 `leverage_used`, `reward`, `technique_used`의 구체성을 올린다.

### 5.2 형식

`treatments/preprocess/{work_id}/densification/artifact_catalog.json`

```json
{
  "_description": "덴시피케이션용 신병이기/영약/비급 카탈로그",
  "artifacts": [
    {
      "artifact_id": "ART-001",
      "name": "한빙옥(寒冰玉)",
      "type": "영약 재료",
      "acquire_block": 8,
      "use_blocks": [12, 15],
      "narrative_value": "빙심결 수련의 부작용(한독 축적)을 해소하는 핵심 재료. 동시에 상대 독공 사용자의 약점",
      "expiry": "Block 20 이후 사용 시 효능 감소 (내력 증가로 한독 자체가 의미 약해짐)"
    },
    {
      "artifact_id": "ART-002",
      "name": "천기각 장부 사본",
      "type": "정보",
      "acquire_block": 22,
      "use_blocks": [23, 25, 30],
      "narrative_value": "무림맹 산하 천기각의 무공 평가 기록. 각 문파 비전의 약점이 적혀 있는 극비 문서",
      "expiry": null
    }
  ],
  "artifact_types": ["신병(무기)", "이기(도구)", "영약", "비급(무공서)", "정보", "인맥/증표", "영물"]
}
```

### 5.3 최소 요구

- 전체 15개 이상
- ARC당 최소 2개
- `type` 4종 이상 사용
- 각 아이템에 `acquire_block`, `use_blocks`, `narrative_value` 필수
- 추상적 아이템("강호의 힘") 금지 — 구체적 실물/문서/물질이어야 함

---

## 6. 조건부 잠금 해제 절차 (20단계 중 5단계)

### 6.1 해제 가능 필드

`location.place`, `location.detail`, `faction_status.standing`

### 6.2 해제 조건

1. 감사 보고서 또는 차이 행렬에서 해당 필드의 반복이 문제로 지적됨
2. 해제 근거 문서(`densification/conditional_unlock_log.md`)에 아래 기록:
   - 해제 대상 블록
   - 해제 사유 (구체적 차이 행렬 문항 번호)
   - 변경 전 값 → 변경 후 값
   - BI 재동기화 필요 여부
3. 사용자 승인 (자동 해제 금지)

### 6.3 해제 후 의무

- BI `plot_roadmap` 해당 블록의 동일 필드도 함께 수정
- 수정 후 BI PASS 2 재검증

---

## 7. 덴시피케이션 배치 플래너 (20단계 중 6단계)

### 7.1 배치 구성 원칙

- **배치 크기: 3블록** (기존 production harness와 동일)
- 고밀도 블록(skip_blocks)은 배치에서 제외
- 배치 순서: 아크 순서를 따름
- 아크 경계를 배치가 넘지 않도록 함

### 7.2 배치 플랜 산출물

`treatments/preprocess/{work_id}/densification/batch_plan.json`

### 7.3 배치 실행 규칙

- 한 번에 1배치만 실행
- 배치 감리 PASS 후에만 다음 배치 진행
- 배치 내 블록은 순차 처리
- 배치 실패 시 해당 배치만 재실행

---

## 8. Phase 0 보강 시트 (20단계 중 7단계)

### 8.1 목적

기존 phase0_design에 보조 입력 3종의 핵심 정보를 반영한 "보강 시트"를 별도로 생성. 원본 phase0_design은 수정하지 않는다.

### 8.2 산출물

`treatments/preprocess/{work_id}/densification/phase0_supplement.json`

```json
{
  "_description": "덴시피케이션 보강용 Phase 0 확장 시트 (무협)",
  "source_phase0": "treatments/{work_id}_phase0_design.json",
  "martial_timeline_ref": "densification/martial_timeline.json",
  "jianghu_force_pool_ref": "densification/jianghu_force_pool.json",
  "artifact_catalog_ref": "densification/artifact_catalog.json",
  "arc_supplements": [
    {
      "arc": "ARC-01",
      "blocks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      "rewrite_blocks": [7, 8, 9, 10],
      "martial_events_assigned": ["MA-001", "MA-002"],
      "jianghu_forces_assigned": [],
      "artifacts_assigned": ["ART-001"],
      "weakness_pool_expansion": [
        "문파 산문 수비가 야간에 취약하여, 짧은 시간 내 핵심 자료를 탈취당할 수 있다"
      ],
      "action_type_candidates": ["비무 도전", "문파 내 시험", "야간 습격 방어", "비급 해독"]
    }
  ]
}
```

### 8.3 보강 시트 검증

- 모든 `martial_events_assigned`가 `martial_timeline.json`에 존재
- 모든 `jianghu_forces_assigned`가 `jianghu_force_pool.json`에 존재
- 모든 `artifacts_assigned`가 `artifact_catalog.json`에 존재
- `rewrite_blocks`가 `skeleton_diagnosis.json`의 `rewrite_blocks`와 일치

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
[완성도 게이트] §9.1A 필수 필드 존재 확인
  ↓
[잠금 검증] 잠금 필드가 변경되지 않았는지 확인
  ↓
[자가 점검] §9.3의 Anti-Template 체크 14문항
  ↓
[골든 참조] §9.4의 골든 블록 참조 체크
  ↓
[저장] DEN-candidate로 저장
  ↓
[Python 교정] 경지/내공 연속성, NPC before 리셋 등 기계적 교정
  ↓
[DEN-fixed 저장]
  ↓
[배치 내 다음 블록으로 이동]
```

### 9.1A 블록 완성도 게이트

JSON 생성 직후 **필수 필드 존재 여부**를 확인한다. 하나라도 없으면 즉시 재생성.

| # | 필드 | 확인 기준 | 미달 시 |
|---|------|----------|--------|
| CG-01 | `content.context` | 비어있지 않음, 50자 이상 | 재생성 |
| CG-02 | `content.event_villain` | 비어있지 않음, 100자 이상 | 재생성 |
| CG-03 | `content.solution` | 비어있지 않음, 100자 이상 | 재생성 |
| CG-04 | `content.reward` | 비어있지 않음, 50자 이상 | 재생성 |
| CG-05 | `stakes` | 비어있지 않음, 35자 이상 | 재생성 |
| CG-06 | `power_shift` | `protagonist`와 `antagonist` 모두 존재 | 재생성 |
| CG-07 | `relationship_delta` | 배열, 길이 ≥ 2 | 재생성 |
| CG-08 | `foreshadow` | 객체 배열 존재. 각 원소: {"ref": N, "event": "서술"} | 재생성 |
| CG-09 | `callback` | 객체 배열 존재. 각 원소: {"ref": N, "event": "서술"} | 재생성 |
| CG-10 | `emotional_beat` | `type`과 `intensity` 모두 존재 | 재생성 |
| CG-11 | `tension_level` | 숫자, 1~10 | 재생성 |
| CG-12 | `location` | `place`와 `detail` 모두 존재 | 재생성 |
| CG-13 | `martial_ext` | `strategy`, `action_type`, `opponent`, `technique_used` 존재 | 재생성 |

### 9.2 사전 선언 (블록 시작 전 필수 — 10항)

블록 재작성 전에 아래 **10항**을 먼저 선언한다. 사전 선언 없이 JSON을 출력하면 무효 처리.

1. **이 블록의 고유 사건**: 스켈레톤과 다른 점 1문장
2. **이 블록의 적대자 행동과 합리적 이유**: 적대자가 왜 이 시점에 이 행동을 하는지
3. **직전 2블록과의 차이**: strategy/action_type/weakness 중 무엇이 다른지
4. **이 블록에서 사용할 무공/경지 이벤트** (있으면): `MA-XXX` ID
5. **이 블록에서 등장/사용할 아이템** (있으면): `ART-XXX` ID
6. **부상 연속성 확인**: 직전 블록에서 입은 부상이 있으면 이번 블록에서 어떻게 반영되는지. 부상 무시 금지.
7. **스켈레톤 대비 핵심 변화**: 원본 블록과 이번 재작성의 핵심 차이 1문장. "어떤 구체적 장면/인물/무공이 새로 생겼는가?"
8. **골든 블록 밀도 도달 자가 판정**: "이번 블록이 Block 1~6과 같은 밀도에 도달했는가?" YES/NO + 근거
9. **보조 입력 주입 확인**: `MA-XXX`, `JH-XXX`, `ART-XXX` 중 주입한 항목 열거. 3배치 연속 0개이면 보강 시트 재검토.
10. **잠금 필드 무변경 선언**: "잠금 필드가 원본과 동일하다"를 선언. 확인 없이 선언하면 무효.

### 9.3 Anti-Template 체크 14문항 (무협 전용)

블록 재작성 후 즉시 자가 점검. 하나라도 FAIL이면 같은 블록 재작성.

| # | 문항 | FAIL 조건 |
|---|------|-----------|
| AT-01 | event_villain 첫 문장이 직전 3블록과 구조적으로 동일한가? | 동일 |
| AT-02 | solution에 "내력을 끌어올려 일격에 쓰러뜨렸다" 패턴이 포함되는가? | 포함 |
| AT-03 | stakes에 "[무공명]을 놓치면" 패턴으로 시작하는가? | 시작 |
| AT-04 | power_shift에 "[전투명]를 통해" 패턴으로 시작하는가? | 시작 |
| AT-05 | relationship_delta.after에 "사형/사제로서 신뢰를 쌓았다" 패턴이 포함되는가? | 포함 |
| AT-06 | strategy가 "상대의 빈틈을 노려 일격한다"만 있는가? | 해당 패턴만 |
| AT-07 | emotional_beat.type이 직전 블록과 동일한가? | 동일 |
| AT-08 | action_type이 직전 3블록 이내 재등장하는가? | 재등장 |
| AT-09 | technique_used가 직전 3블록과 완전 동일 세트인가? | 동일 |
| AT-10 | strategy가 직전 5블록 이내 동일 문장인가? | 동일 |
| AT-11 | 적대자 약점이 직전 3블록과 동일한가? | 동일 |
| AT-12 | 조사 오류가 있는가? | 있음 |
| AT-13 | "경지를 돌파했다"가 5블록 이내 반복 등장하는가? | 등장 |
| AT-14 | "사부의 유언/가르침을 떠올렸다"가 5블록 이내 반복 등장하는가? | 등장 |

### 9.4 골든 블록 참조 체크

Anti-Template 통과 후, DEN-candidate 저장 전에 **Block 1~6과의 밀도 비교**.

| # | 비교 항목 | 기준 | FAIL 시 |
|---|----------|------|---------| 
| GR-01 | `avg_bundle_chars` | 이번 블록 ≥ 골든 블록 평균의 80% | 서사 보강 후 재작성 |
| GR-02 | `relationship_delta` 대상 수 | ≥ 2명 | NPC 추가 |
| GR-03 | `foreshadow + callback` 합계 | ≥ 1건 | 복선 추가 |
| GR-04 | `opponent` 구체성 | name, weakness 비어있지 않음 | 적대자 보강 |
| GR-05 | `stakes` 길이 | ≥ 50자 | 위험 서술 보강 |

### 9.5 출력 형식 강제 규칙 (LLM 자동화 방지)

**원칙: "PASS"만 쓰면 무효. 반드시 수치와 근거를 함께 출력해야 인정.**

LLM은 자가 점검을 형식적으로 "전량 PASS"라고만 쓰고 넘어가려는 경향이 있다. 이를 방지하기 위해 아래 출력 형식을 **필수**로 강제한다. 형식이 없으면 해당 블록의 DEN-candidate를 인정하지 않는다.

#### A. 사전 선언 출력 형식

반드시 `### 사전 선언 — Block {N}` 헤더 아래에 10항을 자연어로 작성한다. JSON 출력 전에 이 블록이 없으면 JSON 자체를 무시한다.

```markdown
### 사전 선언 — Block {N}
1. 고유 사건: [1문장]
2. 적대자 행동/이유: [1~2문장]
3. 직전 차이: strategy=[X→Y], action_type=[X→Y], weakness=[X→Y]
4. 무공/경지 이벤트: MA-XXX 또는 해당 없음
5. 아이템: ART-XXX 또는 해당 없음
6. 부상 연속성: [직전 부상 상태 → 이번 블록 반영 방법]
7. 스켈레톤 대비 변화: [새로 생긴 장면/인물/무공]
8. 골든 밀도 도달: YES — [근거] / NO — [미달 사유]
9. 보조 입력 주입: MA-002, ART-005 / 해당 없음 (연속 N배치)
10. 잠금 필드 무변경: 확인 완료 — [block_id/title/realm_before 등 3개 샘플 대조]
```

#### B. 완성도 게이트 출력 형식

반드시 수치와 함께 표로 출력한다. "재생성" 판정이 1개라도 있으면 JSON을 폐기하고 재작성.

```markdown
### 완성도 게이트 — Block {N}
| # | 필드 | 기준 | 실제 | 판정 |
|---|------|------|------|------|
| CG-01 | context | ≥50자 | 185자 | ✅ |
| CG-02 | event_villain | ≥100자 | 240자 | ✅ |
| ...
| CG-13 | martial_ext | 필수 필드 존재 | 전부 존재 | ✅ |
```

#### C. Anti-Template 체크 출력 형식

각 문항에 대해 PASS/FAIL + 근거 1문장을 출력한다. "전량 PASS" 한 줄은 무효.

```markdown
### Anti-Template 체크 — Block {N}
| # | 문항 | 판정 | 근거 |
|---|------|------|------|
| AT-01 | event_villain 구조 | ✅ | 직전 3블록은 "문파 내 비무" 구조, 이번은 "외부 세력 침입 방어" |
| AT-02 | solution 패턴 | ✅ | "지형 이용 전술" — 금지 패턴 미해당 |
| ...
| AT-13 | 경지 돌파 반복 | ✅ | 직전 5블록 내 돌파 0건 |
| AT-14 | 사부 유언 반복 | ✅ | 직전 5블록 내 등장 0건 |
```

#### D. 골든 블록 참조 출력 형식

반드시 골든 블록 평균 수치와 이번 블록 수치를 병기한다.

```markdown
### 골든 블록 참조 — Block {N}
| # | 항목 | 골든 평균 | 이번 블록 | 비율 | 판정 |
|---|------|----------|----------|------|------|
| GR-01 | bundle_chars | 850자 | 810자 | 95% | ✅ |
| GR-02 | relationship_delta | 3명 | 2명 | - | ✅ |
| GR-03 | foreshadow+callback | 2건 | 1건 | - | ✅ |
| GR-04 | opponent name | 있음 | "혈영노" | - | ✅ |
| GR-05 | stakes 길이 | 80자 | 72자 | - | ✅ |
```

#### E. 위반 시 처리

- 위 A~D 형식 중 하나라도 누락되면 → DEN-candidate 불인정, 같은 블록 재시작
- "전량 PASS"만 적고 수치/근거가 없으면 → 무효, 재출력
- 연속 3블록 이상 모든 항목이 "✅ PASS"이면 → 밀도 스코어(§12)로 교차 검증 후 진짜 고밀도인지 확인

---

## 10. 배치 감리 (20단계 중 9단계)

### 10.1 4-Pass 배치 감리

배치(3블록) 완료 후 아래 감리를 수행한다.

**Pass 1: 잠금 무결성**
- 잠금 필드 14개가 원본과 100% 동일
- `realm_before(N) == realm_after(N-1)` 연속성 유지
- `internal_energy_before(N) == internal_energy_after(N-1)` 연속성 유지

**Pass 2: 밀도 비교**
- 배치 내 블록의 `avg_bundle_chars` vs 스켈레톤 원본
- 최소 2배 이상 증가 필수 (목표 800자+)
- Anti-Template 14문항 전량 PASS

**Pass 3: 서사 차별성**
- 배치 내 3블록의 event_villain/solution/stakes가 서로 다른가?
- 직전 배치의 마지막 블록과의 연속성 확인
- 보강 시트의 assigned 항목이 실제 반영되었는가?

**Pass 4: 차이 행렬 (필수 출력)**

배치 감리 시 차이 행렬을 필수로 출력한다.

```
| Block | beat_type | intensity | tension | action_type | opponent | location | duration | realm_delta | 내공변화 | success | DEN밀도 | 무공이벤트 | 세력등장 | 아이템사용 |
|-------|-----------|-----------|---------|-------------|----------|----------|----------|-------------|---------|---------|---------|-----------|---------|-----------|
```

### 10.2 감리 결과 저장

`treatments/audit_reports/{work_id}_den_batch_NNN_audit.md`

배치 감리 보고서에는 반드시 아래를 포함:

1. 4-Pass 결과
2. 배치 내 각 블록의 밀도 스코어 (§12)
3. 골든 블록 참조 체크 결과 (§9.4)
4. 완성도 게이트 통과 여부 (§9.1A)

---

## 11. 아크 단위 중간 검증 (20단계 중 10단계)

10블록(1 ARC) 분량의 배치가 모두 완료될 때마다 아크 단위 검증.

### 11.1 아크 밀도 검증

| 지표 | 기준 |
|------|------|
| `avg_bundle_chars` (아크 평균) | >= 750 |
| `opponent_unique` (아크 내) | >= 3 |
| `action_type_unique` (아크 내) | >= 5 |
| `martial_event_used` (아크 내) | >= 1 |
| `artifact_used` (아크 내) | >= 1 |
| `weakness_unique` (아크 내) | >= 3 |
| `template_similarity_avg` (아크 내) | < 0.3 |
| `emotional_beat_types` (아크 내) | >= 4종 |
| `defeat_block_present` | 최소 1개 |

### 11.2 아크 서사 검증

- 아크 입구/출구가 phase0 설계와 정합
- 아크 내 에스컬레이션 3축(경지 성장, 강호 위상 상승, 위기 비가역성) 중 최소 1축 상승
- 아크 내 패배 블록이 기계적 위치(정확히 5번째)가 아닌가?
- 외부 강호 세력이 ARC-04 이후 최소 1개 등장하는가?

### 11.3 실패 시

아크 단위 검증 FAIL → 해당 아크의 가장 약한 배치만 재실행

---

## 12. 밀도 스코어 산출 (20단계 중 11단계)

### 12.1 블록별 밀도 스코어 (0~100)

```
density_score = (
    chars_score              * 0.20 +  # bundle_chars 기반 (800+ = 20점)
    villain_score            * 0.15 +  # event_villain 구체성/고유성
    solution_score           * 0.15 +  # solution 전술 차별성
    opponent_score           * 0.10 +  # opponent 정보 완비도
    realm_progression_score  * 0.10 +  # 경지/내공 변동 서사 정합
    martial_coherence_score  * 0.10 +  # 무공 사용/습득 정합성
    callback_score           * 0.10 +  # 복선/콜백 진정성
    injury_continuity_score  * 0.10    # 부상 연속성
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

### 12.4 가중치 산출 세부 (무협 전용)

**realm_progression_score (0~10)**:
- 경지 돌파가 phase0 로드맵과 정합하면 +5
- 돌파 리듬이 자연스러우면(정체기 존재, 계기 서술) +3
- 내공 수치 연속성 유지 +2

**martial_coherence_score (0~10)**:
- 사용 무공이 `martial_timeline`에 존재하면 +4
- 미습득 무공을 사용하지 않았으면 +3
- 무공 간 상생/상극 설정이 반영되면 +3

**injury_continuity_score (0~10)**:
- 직전 블록의 부상이 이번 블록에 반영되면 +5
- 부상 회복 서사가 있으면 +3
- 부상 무시가 0건이면 +2

---

## 13. 경지/부상/무공 정합 보강 (20단계 중 12단계)

### 13.1 경지 돌파 리듬 설계

무협물에서 경지 돌파는 독자 만족의 핵심이면서 동시에 가장 남용되기 쉬운 요소다.

**5단계 돌파 리듬**:

| 단계 | 블록 범위 | 경지 패턴 |
|------|----------|----------|
| 1. 기초 정립 | 1~14 | 첫 경지 확립, 기본 무공 체득. 돌파보다 기반 다지기 중심 |
| 2. 첫 도약 | 15~28 | 위기 속 각성으로 한 단계 돌파. 이후 안정화 필요 |
| 3. 정체와 깨달음 | 29~42 | 단순 수련으로는 돌파 불가. 실전/실패를 통한 깨달음 필수 |
| 4. 전환점 | 43~56 | 무공 체계 재편 또는 금기의 수련법. 대가(부상/관계 단절)가 따름 |
| 5. 완성 | 57~70 | 최종 경지 도달. "힘의 완성"이 아니라 "힘의 의미 이해"가 핵심 |

### 13.2 부상 연속성 규칙

- 전투에서 입은 부상은 최소 3블록 이상 영향을 준다
- 부상 무시(다음 블록에서 멀쩡) → 즉시 REJECT
- 중상은 최소 5블록, 치명상은 아크 전체에 영향
- 부상 회복에는 구체적 수단 필요 (영약/의원/시간)
- 부상 중 전투 시 performance 저하 서술 필수

### 13.3 무공 사용 정합성 규칙

- `martial_timeline`에 없는 무공을 사용하면 REJECT
- 습득 블록 이전에 사용하면 REJECT
- 입문 단계에서 절정 기술을 사용하면 REJECT
- 상생/상극 설정이 있으면 반드시 전투 결과에 반영

---

## 14. 복선-콜백 재구축 (20단계 중 13단계)

### 14.1 기존 복선 유지 + 신규 추가

- phase0의 기존 복선은 **잠금**
- 추가 가능: **아크 내 단기 복선** (3~7블록 이내 회수)
- 무협 특유 복선: 비급 힌트, 경지 장벽 복선, 부상/독 잠복 복선

### 14.1.1 foreshadow/callback 필드 형식

foreshadow[]와 callback[]은 string 배열이 아니라 **객체 배열**로 작성한다.

```json
"foreshadow": [
    {"ref": 25, "event": "서사적 사건 서술 (블록 번호 노출 금지)"}
],
"callback": [
    {"ref": 5, "event": "서사적 회수 서술 (블록 번호 노출 금지)"}
]
```

**블록 번호 본문 노출 금지**: TR 블록의 **모든 텍스트 필드**에 "B숫자", "Block 숫자", "블록 숫자" 패턴 금지.
대상: content.*, stakes, power_shift.*, relationship_delta[].before/after,
foreshadow[].event, callback[].event, martial_ext.strategy/success_pattern.
foreshadow/callback의 블록 참조는 ref 필드에만 기입한다.
이유: TR의 모든 텍스트가 downstream 원고 생성에 흐르므로 메타 번호의 작중 오염을 방지.

### 14.2 콜백 진정성 검증

기계적 콜백 탐지 후 재작성. 무협 전용 기계적 콜백 패턴:
- "직전 전투에서 깨달은 것을 이번 수련에 적용한다" (1블록 거리, 의미 없음)
- "사부의 말씀을 다시 떠올렸다" (반복 사용)

---

## 15. relationship_delta 개별화 (20단계 중 14단계)

### 15.1 문제

"사형/사제로서 신뢰를 쌓았다" 같은 패턴이 반복.

### 15.2 해소 전략

- 각 NPC의 `after`는 해당 블록의 사건에 구체적으로 반응
- 무협 관계 축: 사제/사형제 → 동맹/경쟁 → 은원/의리 → 생사교
- 관계 변화에는 구체적 계기가 필수 (전투 동반, 위기 구원, 배신, 비급 공유 등)

### 15.3 검증

- 동일 `after` 문장 3회 이상 등장 → FAIL
- 70블록 전체 `relationship_delta.after` 고유 문장 비율 80% 이상

---

## 16. 감정 곡선 재설계 (20단계 중 15단계)

### 16.1 무협 감정 비트 고유 목록

무협물에서 자주 쓰이는 감정 비트 유형:

```
각성, 분노, 결의, 고독, 의리, 비통, 복수심, 각오, 평정, 광기,
경외, 수치, 감사, 회한, 초탈, 아쉬움, 경계, 안도, 절박, 환희
```

### 16.2 재설계 원칙

- ARC 내 최소 5종 이상 사용
- tension_level은 재작성 가능
- 전투 블록 직후 반드시 감정 낙차 (고조 → 정리)
- 수련 블록은 tension 3~5 유지 (과열 금지)
- 최종 10블록은 tension 7 이상 유지

---

## 17. 전체 차이 행렬 검증 (20단계 중 16단계)

전 블록 덴시피케이션 완료 후, production harness 차이 행렬을 전수 적용한다.

### 17.1 추가 문항 (덴시피케이션 전용 8문항, 무협 적응)

| # | 문항 | FAIL 조건 |
|---|------|-----------|
| DM-30 | martial_event null 비율 | 50% 초과 |
| DM-31 | 외부 강호 세력 미등장 (ARC-04~07) | 0개 |
| DM-32 | 아이템/아티팩트 카탈로그 미활용 비율 | 70% 초과 |
| DM-33 | 경지 돌파 리듬 5단계 미반영 | 미반영 |
| DM-34 | relationship_delta.after 동일 문장 3회 이상 | 존재 |
| DM-35 | 패배 블록이 정확히 아크 5번째에만 위치 | 전부 5번째 |
| DM-36 | 밀도 스코어 D등급 이하 존재 | 존재 |
| DM-37 | 부상 무시 블록 존재 | 존재 |

### 17.2 통과 기준

- 전량 PASS
- FAIL 문항 있으면 해당 블록만 재작성

---

## 18. BI 재동기화 (20단계 중 17단계)

### 18.1 목적

덴시피케이션으로 TR 재작성 필드가 변경되었으므로, BI `plot_roadmap`을 재동기화한다.

### 18.2 절차

1. 덴시피케이션 완료 TR draft를 원천으로 BI `plot_roadmap` 재복사
2. `MartialHUD` 갱신 (TR 최종 `realm_after`, `internal_energy_after` 반영)
3. `Seeds` echo_count / harvested_ep 갱신
4. `KarmaMatrix` 채움
5. BI 5-Pass 감리 재실행

### 18.3 잠금 필드 무변경 확인

TR의 잠금 필드가 변경되지 않았으므로, BI 재감리는 자동 통과가 기대된다. 단, 반드시 재검증.

---

## 19. 최종 밀도 게이트 (20단계 중 18단계)

### 19.1 production_density_gate 재검

| 지표 | 기준 | 목표 |
|------|------|------|
| `avg_bundle_chars` | >= 350 (P0) | >= 800 |
| `critical_thin_blocks` | 0 | 0 |
| `opponent_unique` | >= 8 | >= 15 |
| `callback_ratio` | >= 0.65 | >= 0.65 (실질적) |
| `action_type 종류` | >= 10 | >= 15 |
| `action_type_top_repetition` | <= 4 | <= 4 |
| 단일 opponent 점유율 | <= 30% | <= 20% |

### 19.2 통과 기준

- P0 게이트 전량 PASS (필수)
- 밀도 스코어 전 블록 평균 70점 이상

---

## 20. 출고 및 상태 전이 (20단계 중 19~20단계)

### 20.1 단계 19: 최종 감리 보고서

`treatments/audit_reports/{work_id}_densification_final_report.md`

### 20.2 단계 20: 상태 전이

| 시나리오 | 전이 |
|----------|------|
| PASS | TR draft를 `densified` 상태로 마킹. BI 재동기화 완료. 원고 생산 진입 가능 |
| 부분 FAIL | 실패 블록/아크만 재실행 |
| 전면 FAIL | 덴시피케이션 접근 실패. phase0 보강 후 전면 리프로덕션 검토 |

### 20.3 산출물 목록 (전체)

```
treatments/preprocess/{work_id}/densification/
  ├── martial_timeline.json           (§3)
  ├── jianghu_force_pool.json         (§4)
  ├── artifact_catalog.json           (§5)
  ├── conditional_unlock_log.md       (§6, 필요 시)
  ├── batch_plan.json                 (§7)
  ├── phase0_supplement.json          (§8)
  ├── skeleton_diagnosis.json         (§2)
  └── realm_progression_plan.md       (§13)

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
| 2 | 무공/비급 타임라인 | §3 | martial_timeline.json |
| 3 | 강호 세력 풀 | §4 | jianghu_force_pool.json |
| 4 | 신병이기/영약 카탈로그 | §5 | artifact_catalog.json |
| 5 | 조건부 잠금 해제 | §6 | conditional_unlock_log.md |
| 6 | 배치 플래너 | §7 | batch_plan.json |
| 7 | Phase 0 보강 시트 | §8 | phase0_supplement.json |
| 8 | 블록 단위 덴시피케이션 | §9 | DEN-candidate/DEN-fixed |
| 9 | 배치 감리 | §10 | den_batch_NNN_audit.md |
| 10 | 아크 단위 중간 검증 | §11 | den_arc_NN_audit.md |
| 11 | 밀도 스코어 산출 | §12 | 블록별 점수 |
| 12 | 경지/부상/무공 정합 | §13 | realm_progression_plan.md |
| 13 | 복선-콜백 재구축 | §14 | 복선/콜백 재작성 |
| 14 | relationship_delta 개별화 | §15 | delta 재작성 |
| 15 | 감정 곡선 재설계 | §16 | emotional_beat/tension 재작성 |
| 16 | 전체 차이 행렬 검증 | §17 | 차이 행렬 결과 |
| 17 | BI 재동기화 | §18 | BI 갱신 + 5-Pass 재감리 |
| 18 | 최종 밀도 게이트 | §19 | density_gate 판정 |
| 19 | 최종 감리 보고서 | §20.1 | densification_final_report.md |
| 20 | 상태 전이 | §20.2 | densified 마킹 |

---

## 부록 B: 기존 하네스와의 관계

```
wuxia-planning-harness.md
  │
  ▼
wuxia-production-harness.md
  │
  ├─ [정상 경로] → wuxia-bi-production-harness.md → 원고 생산
  │
  └─ [밀도 부족 판정] → treatment-densification-harness-v1.md (이 문서)
                            │
                            └─ [완료] → wuxia-bi-production-harness.md (BI 재동기화) → 원고 생산
```

---

## 부록 C: 컨텍스트 윈도우 대응

기본 규칙:

- 덴시피케이션 배치(3블록)는 production harness와 동일한 컨텍스트 관리를 따른다
- 배치 완료 시마다 즉시 `tr_block_070_draft.json`에 merge 저장
- 5배치(15블록)마다 중간 정합성 체크 권장
- context window 한계 도달 시 현재 배치 완료 후 저장, resume prompt 안내

### Resume Prompt 전문

compaction 또는 세션 전환 후 재진입 시 아래를 순서대로 재로드한다:

```
=== 덴시피케이션 Resume Prompt (무협) ===

1. 이 하네스 `treatment-densification-harness-v1.md`를 UTF-8로 다시 읽는다.
2. 아래 파일을 순서대로 UTF-8로 다시 연다:
   - `treatments/{work_id}_phase0_design.json`
   - `treatments/{work_id}_tr_block_070_draft.json`
   - `treatments/preprocess/{work_id}/densification/batch_plan.json`
   - `treatments/preprocess/{work_id}/densification/phase0_supplement.json`
   - `treatments/preprocess/{work_id}/densification/martial_timeline.json`
   - `treatments/preprocess/{work_id}/densification/jianghu_force_pool.json`
   - `treatments/preprocess/{work_id}/densification/artifact_catalog.json`
3. `batch_plan.json`에서 마지막 `status: "done"` 배치를 찾는다.
4. 해당 배치의 마지막 블록(DEN-fixed)을 직전 상태로 삼는다.
5. 다음 `status: "pending"` 배치의 첫 블록부터 재개한다.
6. 재개 첫 블록은 반드시 10항 사전 선언부터 시작한다.

=== 필수 확인 ===
- 직전 DEN-fixed 블록의 realm_after: ___
- 직전 DEN-fixed 블록의 internal_energy_after: ___
- 직전 DEN-fixed 블록의 마지막 NPC 관계 상태: ___
- 미회수 복선 목록: ___
- 미해소 부상 목록: ___
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
  ├─ 단계 12: 경지/부상/무공 정합 (§13) ← 첫 배치 전 1회
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
