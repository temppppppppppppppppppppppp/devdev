# fallen_prince_buys_joseon TR Static Quality Audit

Date: 2026-03-27
Target: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
Method: direct artifact read, 9-axis evaluation, skeleton-specific deep dive, pantech comparison anchor
Confidence: 96%

---

## Findings

### Axis 1. Premise / Commercial Hook Persistence

전제 — 1936년 취리히에서 독살당한 대한제국 황족이 1907년으로 회귀, 합방 전 황실 자산을 빼돌리고 식민지 조선의 5대 병목(해운·보험·철도·은행·광산)을 장악해 실소유주가 된다.

7대단원 골격:
- ARC-01 (Block 1-10): 황실 금고를 빼돌리다 — 1907~1910 합방 직전
- ARC-02 (Block 11-20): 바다 위의 장부 — 1910~1914 해운 진출
- ARC-03 (Block 21-30): 전쟁이 낳은 화폐 — 1914~1918 1차대전 활용
- ARC-04 (Block 31-40): 등기부의 주인 — 1920s 식민지 토지/철도
- ARC-05 (Block 41-50): 대공황을 사냥하다 — 1929~1932
- ARC-06 (Block 51-60): 제국의 월세 — 1932~1937 수익 체계
- ARC-07 (Block 61-70): 조선을 산다 — 1937~1938 실소유주 선언

전제는 70블록에 걸쳐 **구조적으로 유지**된다. 각 아크가 시대별 역사 이벤트에 매핑되어 있고, deal_type이 아크별로 특색이 있다. 다만 이 '유지'는 **설계도 수준**이지 서사 수준이 아니다 — 아크 골격은 살아 있으나 블록 내부의 서술은 모두 동일 템플릿.

Score: **6/10** — 골격으로서 우수, 서사로서 미작동.

### Axis 2. Protagonist Engine Strength

이강윤의 엔진:
- 미래 지식 기반 자산 선점 (`knowledge_used` 필드: 블록별로 변주됨)
- 정체 노출 리스크 (열일곱 황자가 국제 금융을 너무 잘 앎)
- `execution_doctrine`: `"명분보다 병목, 충성보다 소유권, 독립보다 현금흐름을 먼저 쥔다"` — **70/70 동일**

치명적 약점:
- **regression_hint 0/70**: slip-up 메커니즘이 TR에 전혀 없음. 의심 누적/정체 위기가 서사에 부재.
- **execution_doctrine 1종**: 주인공 행동 원칙이 70블록에 걸쳐 단 하나의 문장. 성장도, 변화도, 갈등도 없음.
- **POV 100% 단일**: 이강윤 70/70.

Score: **3/10** — 설정은 매력적이나 TR 안에서 엔진이 작동하지 않음. 템플릿이 엔진을 죽임.

### Axis 3. Growth-Resource / Leverage Logic Clarity

자본 궤적: 4억 → 1조6,400억 (70블록)
- 패배 블록: 7/70 (10%) — pantech의 36%보다 낮지만 존재
- 평탄 블록: 2/70
- deal_type 70종 unique — **이 TR에서 가장 강한 축**
- leverage_used: 281개 항목 중 146개 unique (52% 고유율)

deal_type 샘플:
- ARC-01: 회귀 후 자산 선점 선언, 궁중 동선 은닉, 금고 분리 확보, 밀사 경로 전용, 소작료 현금화, 혼란기 운송, 화폐 전환 선매매, 비공식 송금 구조, 유학생 위장 출국, 합방 직전 장부 절단
- ARC-05: 폭락 매집 선언, 디폴트 담보 인수, 은행간 정산 횡단, 현금 유동 무기화, 창고증권 설계, ...

이것은 진짜 비즈니스 로직 변주다. 단순히 "투자했다/성공했다"가 아니라 시대별·병목별 구체적 금융 메커니즘이 매핑되어 있음.

Score: **8/10** — TR에서 가장 살릴 가치가 높은 축. 자본 로직과 deal_type이 실물.

### Axis 4. Block Progression Density

| Field | Front (1-35) avg | stdev | Back (36-70) avg | stdev |
|-------|-------------------|-------|-------------------|-------|
| context | 122 | 11 | 131 | 12 |
| solution | 151 | 9 | 159 | 10 |
| event_villain | 66 | **2** | 67 | **3** |
| reward | 89 | 7 | 96 | 6 |

event_villain stdev **2~3자** — 이것은 template slot-fill의 결정적 증거. 자연 서술이면 stdev 30+ 이상이 정상 (pantech context stdev 42 참조).

블록이 축소되지는 않음 (back half이 오히려 약간 김). 하지만 이는 템플릿 길이가 일정한 것이지 서사 밀도가 유지되는 것이 아님.

Score: **2/10** — 양적으로는 안정, 질적으로는 템플릿 균일.

### Axis 5. Sceneability

**이 TR의 가장 치명적인 축.**

5블록 샘플:

**Block 1** (1907, 경운궁):
> "강윤은 죽기 전에 본 계약서 문구와 독의 시간차를 기억한 채 금고부터 챙긴다. 헤이그 특사 실패, 한국은행 설립, 합방 시한을 미리 아는 회귀 지식를 앞세워 회귀 후 자산 선점 선언를 구조화하고, 황실 자산 장부 쪽 문서를 자신에게 유리한 순서로 재배치한다."

**Block 15** (1914, 런던):
> "강윤은 이미 잠가 둔 선복이 있어도 결제가 멈추면 배는 떠도 돈이 돌지 않는다는 현실을 맞는다. 전쟁위험요율, 잠수함전, 전시 보험 판례를 미리 알고 선복과 보험을 함께 산다.를 앞세워 전시 유동성 방어를 구조화하고, 선적금융 쪽 문서를 자신에게 유리한 순서로 재배치한다."

**Block 50** (1932, 경성/로테르담/취리히):
> "강윤은 값싸게 산 자산을 함부로 올려치지 않고, 연결해 둘 때만 진짜 제국이 된다고 본다. 대공황, 파운드 절하, 쌀값 하락, 창고증권 제도화를 미리 알고 공황을 사냥한다.를 앞세워 공황 자산 통합 포트폴리오를 구조화하고, 은행/금융 쪽 문서를 자신에게 유리한 순서로 재배치한다."

모든 블록이 동일 구조: `[첫 문장 고유] + [회귀 지식 나열] + "를 앞세워 [deal_type]를 구조화하고, [분야] 쪽 문서를 자신에게 유리한 순서로 재배치한다."`

- 구체적 오브젝트: **없음** (계약서, 장부, 금고가 언급되지만 추상적)
- 촉각/감각 디테일: **없음**
- 대화 마커: 문자열 검사에서는 70/70이지만, 실제 인용 대화는 **0/70** — "라고", "했다" 등은 간접 서술에서 나온 거짓 양성
- 공간 묘사: **없음** (장소명만 있고 공간이 없음)

**장면이 없다. 블록이 장면이 아니라 거래 요약 카드다.**

Score: **1/10** — pantech의 7/10과 비교 불가. 장면급 서술이 단 한 블록도 없음.

### Axis 6. Foreshadow / Callback Density

- Total foreshadows: 19 (0.27/block)
- Total callbacks: 19 (0.27/block)
- pantech 대비: 137 foreshadows, 82 callbacks (1.96/block, 1.17/block)

foreshadow 품질: 블록 번호가 구체적이고 교차 참조가 실재함.
- "Block 69에서 취리히 독살의 배후 문장이 다시 열린다"
- "Block 16의 중립국 계좌, Block 52의 스위스 비밀계좌는 모두 이 우회 경로를 확장한 결과다"

이 교차 참조는 **진짜 아키텍처**다. 량은 빈약하지만 질은 구조적.

Score: **4/10** — 교차 참조 실재하나 밀도가 pantech의 1/7 수준.

### Axis 7. Antagonist Roster Diversity

11 unique opponents / 70 blocks:
- 구도 겐이치: 18회 (26%)
- 에드워드 블레이크: 11회 (16%)
- 이토 마사유키: 8회
- 오쿠라 다카시: 8회
- 기타 7명: 25회

weakness_exploited: **5종 unique, 1종이 51/70 (73%) 차지**
> "실물과 권력을 보지만 장부 우선순위와 병목 결합이 만드는 지배력은 뒤늦게 이해한다." x51

적대자 이름은 11종이지만, 약점이 5종뿐이고 그 중 1종이 73%를 차지한다. 이는 실질적으로 **적대자가 1명**인 것과 같다 — 이름만 다르고 행동 패턴은 동일.

Score: **3/10** — 이름 변주는 있으나 실질 다양성 없음. pantech (68 unique opponents)과 비교 불가.

### Axis 8. Genre-Specific Texture (1907~1938 대한제국/일제강점기)

**이 축은 이 TR의 두 번째 강점이다.**

역사 이벤트 매핑:
- 31개 연도에 걸쳐 실제 역사 이벤트가 블록별로 바인딩
- 1907 헤이그 특사, 1910 합방, 1914 1차대전, 1920 전후 해운 붐 붕괴, 1929 대공황, 1937 중일전쟁
- source_binding으로 material_bank.db AH-* 소스 6개가 블록별 연결

장르 질감 샘플:
- "전쟁위험요율, 잠수함전, 전시 보험 판례" (Block 15)
- "동아권업주식회사 명목자본과 불입자본 괴리" (Block 30)
- "대공황, 파운드 절하, 쌀값 하락, 창고증권 제도화" (Block 50)
- "국가총동원 체제 아래 병목 자산의 협상력 극대화" (Block 70)

이 키워드들은 **실제 역사적 금융 메커니즘**이다. 추상이 아님. 문제는 이것들이 장면 안에서 살지 않고, 요약 카드에 키워드로만 나열된다는 점.

Score: **6/10** — 키워드 수준의 장르 질감은 우수. 서사적 발현은 0.

### Axis 9. Overall Structural Integrity

**Front/back 비교**:
- 밀도 차이 없음 (템플릿 균일)
- 장르 구체성은 아크별로 약간 변주 (ARC-01 황실, ARC-02 해운, ARC-05 대공황)
- 템플릿 오염률: event_villain 100%, solution 100%, stakes 100%

**Salvageable spine vs disposable template**:

| Element | Classification | Status |
|---------|---------------|--------|
| Title (70종) | **spine** | 살릴 가치 높음 |
| deal_type (70종) | **spine** | 살릴 가치 매우 높음 |
| Location (69종) | **spine** | 살릴 가치 높음 |
| historical_event mapping | **spine** | 살릴 가치 매우 높음 |
| source_binding (AH-* 소스) | **spine** | 살릴 가치 매우 높음 |
| capital_trajectory | **spine** | 살릴 가치 높음 |
| foreshadow cross-refs (19개) | **spine** | 살릴 가치 있음 (확장 필요) |
| relationship_delta (99개, 9 targets) | **spine** | 살릴 가치 있음 |
| ARC section_rotation (7 arcs) | **spine** | 살릴 가치 높음 |
| knowledge_used (블록별 변주) | **spine** | 살릴 가치 있음 |
| event_villain prose | **template** | 폐기 후 재작성 |
| solution prose | **template** | 폐기 후 재작성 |
| stakes prose | **template** | 폐기 후 재작성 |
| reward prose | **template** | 폐기 후 재작성 |
| execution_doctrine (1종) | **template** | 확장 필요 |
| weakness_exploited (1종 73%) | **template** | 재작성 |

Score: **4/10** — 뼈대가 진짜이므로 전면 폐기는 손실. 하지만 살은 전면 재작성.

---

## Skeleton-Specific Deep Dive

### Template Contamination Rate

| Field | Template % | Template Signature |
|-------|------------|-------------------|
| event_villain | **100%** | "X은 강윤이 Y로 Z 주도권을 넓히기 전에 문서와 인허가, 가격표를 먼저 잠그려 든다" |
| solution | **100%** | "~ 를 앞세워 [deal_type]를 구조화하고, [분야] 쪽 문서를 자신에게 유리한 순서로 재배치한다" |
| stakes | **100%** | "이번 X에서 밀리면 ~ 전체가 흔들리고, ~ 병목은 Y 쪽으로 넘어간다" |
| reward | **~90%** | "동원 가능 자본은 X에서 Y로 [변동]. [회귀 우위/병목 장악] 결과." |
| execution_doctrine | **100%** | "명분보다 병목, 충성보다 소유권, 독립보다 현금흐름을 먼저 쥔다." |
| weakness_exploited | **73%** | "실물과 권력을 보지만 장부 우선순위와 병목 결합이 만드는 지배력은 뒤늦게 이해한다." |
| context 첫 문장 | **0%** | 블록별 고유 — 이것이 spine의 핵심 |
| context 2-3문장 | **~80%** | "[역사 이벤트]의 여파를 [타이밍 활용]" 패턴 반복 |

**template contamination은 prose field에 국한.** structural field (title, deal_type, location, historical_event, source_binding, capital, foreshadow)는 깨끗.

### Salvageable Spine Inventory

spine 전체를 추출하면 다음과 같은 데이터셋이 된다:
- 70 unique titles with 7-arc structure
- 70 unique deal_types with business logic progression
- 69 unique locations spanning 경운궁→로테르담→취리히→런던→상하이→경성
- 31 historical years with event mapping
- 6 AH-* source bindings from material_bank.db
- Capital trajectory 4억→1조6,400억 with 7 setback points
- 19 foreshadow cross-references with concrete block numbers
- 99 relationship deltas across 9 NPC targets
- Genre-specific financial keywords per block (전환사채, 전쟁위험요율, 창고증권, 등기부 등)

이 spine은 **새 TR 생성의 구조 시트로 직접 사용 가능하다.** pantech_cyworld_reborn의 TR이 이런 spine 없이 처음부터 생성된 것과 비교하면, fallen_prince의 spine은 TR 재생성의 출발점으로서 매우 가치가 높다.

---

## Pantech Comparison Anchor

| Metric | pantech (mixed) | fallen_prince | Gap |
|--------|-----------------|---------------|-----|
| Context stdev | 42 | 12 | pantech의 1/3.5 |
| event_villain template | 0/70 | 70/70 | **치명적 격차** |
| solution template | 0/70 | 70/70 | **치명적 격차** |
| stakes template | 0/70 | 70/70 | **치명적 격차** |
| Opponent unique | 68/70 | 11/70 | pantech의 1/6 |
| weakness_exploited unique | ~68 | 5 | pantech의 1/14 |
| deal_type unique | 28/70 | 70/70 | fallen_prince가 2.5배 |
| Foreshadow count | 137 | 19 | pantech의 1/7 |
| Capital logic coherence | 9/10 | 8/10 | 유사 |
| Sceneability | 7/10 | 1/10 | **치명적 격차** |
| regression_hint | 70/70 | 0/70 | **완전 부재** |
| Historical event mapping | partial | 31 years | fallen_prince가 우수 |
| source_binding | 없음 | 6 AH-* | fallen_prince만 존재 |

pantech이 "usable spine but mixed"를 받은 이유: prose에서 장면이 살아 있었고 (sceneability 7/10), 템플릿 반복이 없었으며 (0/70), 적대자가 다양했다 (68/70).

fallen_prince는 이 세 축에서 모두 **1/10, 70/70, 11/70**이다. "mixed" 수준에 전혀 미치지 못한다.

---

## Overall Score

| Axis | Score |
|------|-------|
| 1. Premise / Hook | 6/10 |
| 2. Protagonist Engine | 3/10 |
| 3. Capital / Leverage Logic | 8/10 |
| 4. Block Density | 2/10 |
| 5. Sceneability | 1/10 |
| 6. Foreshadow / Callback | 4/10 |
| 7. Antagonist Diversity | 3/10 |
| 8. Genre Texture | 6/10 |
| 9. Structural Integrity | 4/10 |
| **Average** | **4.1/10** |

---

## What Clearly Works

1. **deal_type 70종 unique**: 이 TR의 최대 자산. 시대별·병목별 구체적 금융 메커니즘이 매핑됨.
2. **7대단원 × 역사이벤트 매핑**: 1907~1938 실제 역사 연표가 아크 구조와 정확히 연결.
3. **source_binding**: material_bank.db AH-* 소스 6개가 블록별로 바인딩 — 재생성 시 재료 접근 경로가 이미 있음.
4. **자본 궤적**: 4억→1조6,400억, 7회 패배, 비즈니스 로직 내적 정합.
5. **location 69종**: 경운궁→로테르담→취리히→런던→상하이→경성 범위의 공간 구조.
6. **foreshadow 교차참조**: 19개로 빈약하지만, 블록 번호가 구체적이고 구조적.

## What Is Broken

1. **event_villain/solution/stakes 100% 템플릿**: 장면이 아닌 거래 카드. Stage 4 입력으로 사용 불가.
2. **sceneability 0**: 구체적 오브젝트, 대화, 감각 묘사가 단 한 블록도 없음.
3. **regression_hint 0/70**: 회귀자 의심 누적이 TR에 전혀 없음.
4. **execution_doctrine 1종**: 주인공 성장/변화가 없음.
5. **weakness_exploited 1종 73%**: 적대자가 사실상 1명.
6. **opponent 11종**: pantech 68종 대비 1/6 수준.

---

## Final Classification

**Consumable but skeleton-likely.**

근거:
- TR은 structural spine으로서 가치가 있다 (deal_type, location, historical_event, source_binding, capital trajectory, foreshadow cross-ref).
- 하지만 prose field는 100% 템플릿이므로 **Stage 4 원고 입력으로 직접 사용할 수 없다.**
- pantech "mixed"와 비교하면, sceneability/template/opponent 3축에서 **치명적 격차**가 있어 "usable spine but mixed"에 해당하지 않는다.
- 전면 재생성은 spine을 낭비하므로 "regenerate TR first (전면)"에도 해당하지 않는다.

---

## Recommended Next Step

**spine-preserving TR densification** — 현재 TR의 spine element를 구조 시트로 보존하고, prose field(context, event_villain, solution, reward, stakes)만 재작성하는 제한적 재생성.

구체적으로:
1. **보존**: title, deal_type, location, time_span, historical_event, source_binding, capital_before/after/delta, foreshadow, callback, relationship_delta, section_rotation, emotional_beat, tension_level, pov_character, opponent.name
2. **재작성**: context (3문장 이상, 구체적 오브젝트 포함), event_villain (적대자별 고유 행동), solution (주인공의 구체적 행동과 결과), reward (거래 결과 + 서사적 의미), stakes (고유 문장)
3. **추가**: regression_hint (slip-up/suspicion 블록별), execution_doctrine 블록별 변주, weakness_exploited 적대자별 고유화
4. **확장**: foreshadow/callback 밀도 강화 (19→100+ 목표)

이 densification은 BI repair(Step 3)보다 **먼저** 수행해야 한다. BI repair는 TR의 prose를 입력으로 사용하므로, 템플릿 TR 위에 BI를 보강해도 Stage 2/3/4 품질이 올라가지 않는다.

### 다만:

래더 상 "consumable but skeleton-likely"는 "BI repair 진행 가능하나 주의" 판정이다. 만약 사용자가 BI repair를 먼저 원한다면 가능은 하지만, 이 경우 BI repair의 효과가 TR 템플릿에 의해 상쇄될 리스크를 감수해야 한다.

**권장 순서**: spine-preserving TR densification → BI repair → revival canary → 이후 래더 계속

---

- TR spine verdict: **skeleton-likely**
- BI-only repair viable now: **가능하지만 효과 제한적** — TR 템플릿이 Stage 2/3/4 품질 상한을 규정
- Should Codex prioritize TR densification: **yes**
- Regeneration scope: **spine-preserving densification** (전면 재생성 아님)

---

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: TR static audit
changed_files: docs/2026-03-27/fallen-prince-tr-static-quality-audit.md
next_unit: spine-preserving TR densification (recommended) or BI repair with caveats (user choice)
stop_reason: audit complete — verdict skeleton-likely, spine valuable but prose 100% template, densification needed before production pipeline
```
