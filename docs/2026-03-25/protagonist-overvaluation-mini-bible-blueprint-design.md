# Protagonist Overvaluation — Mini Bible Note + Blueprint-First Execution Design

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: bounded design note
Canonical Path: `docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-design.md`
Source Order: `docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-sequential-master-order.md`

Upstream Evidence:
- `docs/2026-03-25/protagonist-overvaluation-staging-4terminal-merge-audit.md`
- `docs/2026-03-25/opus-protagonist-overvaluation/t1-bible-owner-mapping.md`
- `docs/2026-03-25/opus-protagonist-overvaluation/t2-arc-distribution.md`
- `docs/2026-03-25/opus-protagonist-overvaluation/t3-blueprint-staging.md`
- `docs/2026-03-25/opus-protagonist-overvaluation/t4-manuscript-pov-info-gap.md`

---

## 1. Executive Summary

현 시스템의 주인공 고평가(protagonist overvaluation) 체계는 **"큰 숫자 → 와우"** 패턴에 편향된다. 이 패턴은 무협/헌터에서는 물리적 파괴력이라는 자연스러운 감탄 근거를 갖지만, 재벌/상류/비즈니스-파워 장르에서는 **금액 크기 = 감탄**이라는 얕은 구조로 회귀한다.

4-terminal 조사 결과, 소유권이 명확하게 분리되었다:

- **Bible**: 감탄 원칙 정의 (무엇이 감탄할 만한가)
- **Blueprint**: 감탄 실행 설계 (어떻게 장면으로 보여줄 것인가)
- **Arc**: 감탄 모드 분배 (아크마다 어떤 유형의 감탄을 쓸 것인가)
- **Manuscript**: 렌더링 전용 (이미 설계된 구조를 prose로 확장)

그러나 Bible 전체 스키마 개편은 현 시점에서 과중하다. 이 문서는 **mini bible note**(경량 원칙 정의)와 **blueprint-first execution guidance**(장면 수준 실행 지침)로 범위를 한정한 설계안이다.

---

## 2. Why "Big Number → Wow" Fails in Chaebol/Business-Power Stories

### 2.1 근본 원인

비즈니스-파워 장르에서 주인공의 핵심 성취는 **비물리적**이다:

- 전략적 선견 (strategic foresight)
- 정보 비대칭 활용 (information arbitrage)
- 사회적 위계 교란 (social hierarchy disruption)
- 계산된 리스크 감수 (risk calibration)

이런 성취는 "주변 환경을 파괴"하지 않기 때문에, 현재 POV 엔진(`writer_rules.json:66`)의 자동 trigger가 걸리지 않는다. Writer가 자의적으로 판단해야 하므로, LLM의 웹소설 학습 데이터 편향에 따라 **"100억 수익이라니!" + 전원 경악**으로 회귀한다.

### 2.2 실패 메커니즘 3가지

1. **금액 = 감탄 근거**: 이 작품 세계에서 10억은 시작 자본이고, 100억은 중간 규모 거래인데, 업계 전문가가 금액 자체에 놀라면 세계관이 파괴된다.
2. **균일 반응**: 모든 관찰자가 동일 타이밍에 동일 강도로 반응하면, 관찰자의 이해 수준 차이가 소멸된다.
3. **서술자 해설**: "그의 판단은 누구도 따라올 수 없는 수준이었다" — show가 아닌 tell. 독자의 "내가 먼저 알아챘다" 쾌감을 빼앗는다.

### 2.3 캐너리 근거 (canary_0325)

| 에피소드 | 감탄 품질 | 관찰 |
|---------|----------|------|
| EP5 | **HIGH** | PB가 4.5%-세금-수수료-인플레이션 분석에 "입술이 굳었다" — **방법**에 대한 반응 |
| EP7 | **MEDIUM-HIGH** | 형제의 경멸 → 주인공의 구체적 데이터 반박. 다만 "18년의 굴레를 벗어던진 자 특유의 압도적인 여유"는 author-tell |
| EP8 | **HIGH** | PB의 직업적 패닉 vs 주인공의 냉정. 시장 자체가 비인격적 검증자 역할 |

**패턴**: LLM이 때때로 분화된 감탄을 자발적으로 생성하지만, 체계적이지 않고 관찰자가 반복되며(박성호 PB 3회), 약한 에피소드에서는 서술자 해설로 회귀한다.

---

## 3. Mini Bible Note

### 설계 원칙

Mini bible note는 **기존 WorkGuard `work_identity` 구조 내에 수용 가능한 경량 정의**다. 새 스키마 계층을 도입하지 않으며, WorkGuard의 `business_axes`/`control_axes`/`forbidden_flattenings` 옆에 `protagonist_evaluation` 섹션을 추가하는 형태를 상정한다.

### 3.1 감탄 축 (Admiration Axes) — 4개

| 축 | 정의 | 고품질 신호 | 저품질 신호 |
|---|------|-----------|-----------|
| **방법론의 질** (Method Quality) | 남들이 못 하는 것을 **어떻게** 했는가 — 결과가 아니라 과정의 비범함 | 소수만 이해하는 반응, 사후 발각 시 충격, 침묵 속 행동 | 모든 관찰자가 동시 감탄, 숫자 크기만으로 놀람 |
| **조건부 역전** (Conditional Reversal) | 불리한 조건에서 출발하여 역전 — **갭**이 감탄의 근거 | 과소평가 → 반박 불가 성과 → 평가자의 재인식 | 처음부터 유리한 조건 → 당연한 성공 |
| **정보 비대칭** (Information Asymmetry) | 주인공만 아는 것이 있고, 그 격차가 행동의 가치를 결정 | 아는 자의 공포, 모르는 자의 오해, 시간차 깨달음 | 주인공이 직접 설명, 해설자가 대신 풀어줌 |
| **위계 충격** (Hierarchy Shock) | 사회적으로 "위"에 있는 인물이 주인공을 인정하도록 강제됨 | 경멸 → 불안 → 인정(단계적), 상위자의 계획 수정 | 즉각적 "천재" 선언, 무조건적 굴복 |

**주의**: 4축은 상호배타적이지 않다. 에피소드당 1~2축을 primary/secondary로 지정한다.

### 3.2 금지 칭송 패턴 (Forbidden Praise Patterns) — 4개

| 패턴 | 정의 | 왜 금지인가 |
|------|------|-----------|
| **big_number_wow** | 숫자 크기 자체가 감탄의 주된 근거 | 금액은 조건이지 방법이 아님. 업계인이 금액에만 놀라면 세계관 파괴 |
| **uniform_reaction** | 모든 관찰자가 동일 타이밍에 동일 강도로 반응 | 관찰자마다 이해 수준이 다르므로 반응의 시차와 깊이도 달라야 함 |
| **narrator_hype** | 서술자가 직접 주인공의 대단함을 해설 | Show가 아닌 tell. 독자가 스스로 판단할 여지를 빼앗음 |
| **instant_recognition** | 주인공의 능력이 행동 직후 즉시 인정됨 | 시간차 없는 인정은 독자의 "내가 먼저 알아챘다" 쾌감을 소멸시킴 |

### 3.3 관찰자 티어 (Observer Tiers) — 최소 정의

감탄의 품질은 **누가 감탄하는가**에 의존한다. 전원이 동일하게 놀라면 감탄이 평준화된다.

| 티어 | 정의 | 반응 원칙 |
|------|------|----------|
| **informed_insider** | 업계 전문가, 주인공의 행동을 정확히 평가할 수 있는 인물 | 놀라지 않아야 할 것에 놀라지 않고, 진짜 놀라운 것에만 반응 |
| **partial_observer** | 일부만 아는 인물 — 결과는 보지만 방법을 모르는 관찰자 | 규모에 놀라되, 진짜 이유를 모름 → 나중에 깨달을 때 2차 충격 |
| **outsider** | 업계 밖 인물 — 표면적 결과만 인지 | 숫자에 놀라는 것이 자연스러우나, 이 반응이 **주요** 감탄 장치가 되면 안 됨 |

**전문가 반응 비례성 원칙**: 해당 분야 전문가는 일상적 수준의 성과에 놀라지 않는다. 놀라려면 그 전문가의 기준에서 비상식적인 요소가 있어야 한다. (현재 `director.yaml:451`에 평가 기준으로만 존재 — bible note로 끌어올려 사전 지침화)

---

## 4. Blueprint-First Execution Layer

### 설계 원칙

Blueprint는 감탄이 **장면으로 실체화되는 지점**이다. Bible이 "무엇이 감탄할 만한가"를 정의하면, blueprint는 "어떻게 그 감탄을 독자에게 전달할 것인가"를 설계한다.

**적용 방식**: 기존 `ensemble.yaml`의 `BLUEPRINT_GENERATION_PROMPT`에 **prompt-level staging guidance** 추가. 스키마 변경 없이, 프롬프트 지침으로 LLM의 blueprint 생성 방향을 유도한다. 스키마 변경은 canary 근거 확보 후 판단한다.

### 4.1 관찰자 배정 (Observer Allocation)

Blueprint가 `scene_breakdown`에서 `characters`를 배정할 때:

- 주인공 고평가 장면에는 **반드시 평가 근거를 가진 관찰자**를 배정
- 관찰자의 observer tier를 암묵적으로 결정: 이 NPC가 informed_insider인지, partial_observer인지, outsider인지
- 같은 관찰자를 연속 에피소드에서 반복 사용 지양 (canary_0325에서 박성호 PB 3회 반복 관찰)
- 적대자(antagonist)의 단계적 인식 변화(경멸 → 불안 → 인정/공포)는 multi-episode arc에 걸쳐 배치

### 4.2 POV 전환 타이밍 (POV Shift Timing)

현재 POV 엔진(`writer_rules.json:66`)의 trigger는 물리적 파괴/초월에 고정되어 있다. Blueprint가 비물리적 장르에서 POV 전환 타이밍을 보조해야 한다:

- Blueprint의 scene design에서 "이 장면에서 관찰자 시점 삽입이 유효한 이유"를 명시
- 비물리적 trigger 후보: 전략적 판단이 밝혀지는 순간, 정보 우위가 드러나는 순간, 사회적 위계가 뒤집히는 순간
- POV 전환은 감탄의 **도구**이지 감탄 자체가 아니다 — 전환 자체가 목적이 되면 남발로 이어진다

### 4.3 정보 비대칭 설계 (Information Asymmetry)

감탄의 핵심 엔진은 **"아는 자와 모르는 자의 대조"**다. Blueprint에서 설계해야 하는 것:

- **이 장면에서 누가 무엇을 모르는가**: 명시적으로 정보 격차를 설정
- **정보 격차가 해소되는 순간은 언제인가**: reveal은 감탄의 climax — blueprint가 배치
- **착각 구조**: "few understand, many misread" — 소수의 아는 자만 주인공의 행동의 의미를 파악하고, 다수는 오독한다

현재 deprecated된 `architect_rules.json:55`의 "정보 격차 연출: 아는 자와 모르는 자 사이의 대조를 통해 착각 지수를 극대화하라"는 원칙의 실효성은 입증되었으나, 현행 prompt에서 탈락된 상태다. Blueprint prompt에 복원하되, 장르 한정 없는 범용 형태로.

### 4.4 공개 순서 (Reveal Ordering)

감탄이 "즉각적 인정"으로 전달되면 instant_recognition 금지 패턴에 해당한다. Blueprint에서 설계해야 할 reveal 순서:

1. **행동**: 주인공이 행동한다 (주인공 시점, 건조하게)
2. **오독**: 일부 관찰자가 오독한다 ("무모한 도박", "운이 좋았을 뿐")
3. **단서**: 소수의 informed_insider가 이상함을 감지한다 (불안, 침묵, 재평가)
4. **reveal**: 정보 격차가 해소된다 (시간차를 두고, 장면을 걸쳐)
5. **충격파**: 오독했던 관찰자들의 2차 반응 (선택적 — 모든 에피소드에 필요하지 않음)

Blueprint가 이 순서를 장면 설계에 반영하면, manuscript는 이를 prose로 확장하기만 하면 된다.

### 4.5 Show-Not-Tell 제약

Blueprint prompt에 명시할 제약:

- 주인공 고평가는 타 인물의 **"대단하다" 류 직접 발화**가 아닌, **행동 변화/계획 수정/침묵/경계심 강화**로 표현
- "단순 숫자 규모('100억!', '3배 레버리지!')로만 인상을 주는 것은 저급 칭송"
- 왜 그 판단이 어려운지, 왜 남들은 못 하는지를 **장면 구조**로 보여줄 것
- 감탄의 quality = 관찰자의 authority × 반응의 specificity × reveal의 timing gap

---

## 5. What Arc Can Carry Later

Arc는 **감탄 모드를 발명하는 곳이 아니라 분배하는 곳**이다. Bible이 감탄 축을 정의한 후, arc가 담당할 수 있는 것:

1. **아크별 primary 감탄 모드 선택**: "이번 아크는 '조건부 역전'이 주축, '정보 비대칭'이 보조"
2. **감탄 모드 로테이션 강제**: "연속 2 아크 이상 같은 primary 감탄 모드 금지" (기존 감정 곡선 로테이션 규칙과 동일 패턴)
3. **관찰자 클래스 배정**: 아크 단위로 "이 아크의 주요 평가자는 peer/superior/outsider 중 누구인가" 지정
4. **peak episode 배치**: 아크 내 어느 에피소드에서 감탄의 climax가 터지는지 사전 설계

**왜 지금이 아닌가**: Arc 스키마에 `admiration_design` 필드를 추가하려면 먼저 bible note의 감탄 축 정의가 확정되어야 한다. 감탄 축 없이 아크에 모드 선택을 시키면, LLM이 자의적으로 모드를 정의하게 되므로 bible-first 순서가 중요하다.

---

## 6. What Manuscript Must Not Be Asked To Invent

Manuscript는 **렌더링 레이어**다. 다음은 manuscript에게 요청하면 안 되는 것들:

| 항목 | 왜 manuscript가 발명하면 안 되는가 |
|------|--------------------------------------|
| **관찰자 선정** | Blueprint에 배정되지 않은 관찰자를 Writer가 급조하면 서사적 무게가 없다 |
| **정보 격차 구축** | "사실 이 인물은 모르고 있었는데..."를 manuscript에서 갑자기 만들면 개연성 파괴 |
| **감탄 모드 결정** | "이 에피소드는 전략적 선견 감탄"인지 "사회적 충격 감탄"인지는 arc/blueprint에서 결정해야 함 |
| **비물리적 POV trigger** | Blueprint에서 staging이 없으면 Writer가 자의적으로 POV 전환 시점을 판단 — 품질 편차 극대화 |
| **전문가 반응 기준** | NPC의 전문성 수준과 threshold가 upstream에서 설정되지 않으면 비례적 반응 불가 |

Manuscript가 **잘 하는 것** (upstream 설계가 있을 때):

- POV 문체 대비 (주인공의 건조한 내면 vs 관찰자의 격정적 해석)
- 대사 밀도 조절 ("대단하다"가 아닌 행동 변화로 감탄 렌더링)
- 무심한 복귀 (주인공이 주변의 경악을 무시하는 것 자체가 감탄 장치)

---

## 7. Best Bounded Future Wave If Canary Supports This Direction

Canary 결과가 이 설계 방향을 지지하면, 첫 실행 웨이브는 다음 2단계로 한정한다:

### Wave 1A: Mini Bible Note 실현

- WorkGuard `work_identity` 구조 내에 `protagonist_evaluation` 섹션 추가
- 내용: 감탄 축 4개 + 금지 칭송 패턴 4개 + 관찰자 티어 3개
- 적용 방식: WorkGuard → Director/Blueprint prompt에 surface (기존 `business_axes`/`forbidden_flattenings`와 동일 경로)
- Python hard gate 아님 — advisory context로 LLM에 전달
- 예상 blast radius: WorkGuard YAML + prompt injection 경로만

### Wave 1B: Blueprint Prompt Staging Guidance

- `ensemble.yaml`의 `BLUEPRINT_GENERATION_PROMPT`에 감탄 실행 지침 추가
- 내용: 관찰자 배정 원칙 + 정보 비대칭 설계 지시 + show-not-tell 제약 + reveal 순서 가이드
- 스키마 변경 없음 — prompt text만 확장
- 예상 blast radius: ensemble.yaml prompt section만

### 이후 웨이브 (Wave 1 canary 확인 후)

- Wave 2: Arc 스키마에 `admiration_design` 필드 추가 (bible note 확정 후)
- Wave 3: Writer 프롬프트의 비물리적 POV trigger 확장 + 반응 비례성 사전 지침 (blueprint staging 확정 후)
- Wave 4: `side_glimpse` preset 사용 가이드 분화 (observer tier × admiration mode) (선택적)

---

## 8. What Should Remain Deferred Until Canary Evidence Arrives

| 항목 | 왜 지금 결정하면 안 되는가 |
|------|-------------------------|
| **감탄 축의 최종 구성** | 4축이 적절한지, 장르별 축이 달라야 하는지는 실전 근거 필요 |
| **스키마 변경 여부** | Blueprint 스키마에 `evaluation_device` 필드를 추가할지는 prompt-only 방식의 효과를 먼저 측정해야 함 |
| **Arc 스키마 확장** | `admiration_design` 필드의 필수/선택 구분, mode taxonomy의 세분화는 bible note 확정 + 1차 canary 후 |
| **Writer POV trigger 확장** | 비물리적 trigger 추가의 실효성은 blueprint staging이 선행되어야 측정 가능 |
| **착각(misunderstanding) 메트릭 활성화** | `writer_rules.json:83`의 착각 증분 필드가 실제로 서사에 환류되는 경로 설계는 전체 파이프라인 안정화 후 |
| **Python hard gate 도입** | 감탄 패턴의 Python 검증(catharsis_timer 수준)은 advisory→hard gate 전환 근거가 canary에서 나와야 함 |
| **`side_glimpse` preset 재정의** | 현재 정의("대단해! 반응")를 분화할지, 사용 가이드만 추가할지는 canary에서 blueprint staging의 실효를 확인 후 판단 |

---

## 9. Confidence

Estimated confidence: 96%

근거:
- 모든 설계 판단은 4-terminal 조사(T1-T4) 및 merge audit의 합의에 기반
- 소유권 분류(bible=정의, blueprint=실행, arc=분배, manuscript=렌더링)는 기존 시스템의 권한 위계와 일치
- mini bible note의 범위는 기존 WorkGuard 구조 내 수용 가능하여 별도 스키마 계층 불필요
- blueprint prompt 확장은 스키마 무변경으로 blast radius 최소
- canary_0325의 EP5/EP7/EP8 근거로 LLM이 분화된 감탄을 생성 가능하되 체계적이지 않음을 확인

한계:
- mini bible note가 실제로 LLM의 감탄 품질을 측정 가능하게 개선하는지는 canary에서만 확인 가능
- 4축 taxonomy가 모든 장르에 범용 적용 가능한지는 비투자 장르 canary가 필요
- prompt-only 방식이 충분한지 스키마 변경이 필요한지는 1차 canary 후 판단

---

Mini bible note owner: WorkGuard `protagonist_evaluation` section
Blueprint-first execution owner: `ensemble.yaml` BLUEPRINT_GENERATION_PROMPT staging guidance
Should Codex open a narrative-design execution SSOT now: no
