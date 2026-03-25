# T4. Manuscript / POV / Information-Gap Execution Layer

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: lane survey report
Canonical Path: `docs/2026-03-25/opus-protagonist-overvaluation/t4-manuscript-pov-info-gap.md`
Source Order: `docs/2026-03-25/protagonist-overvaluation-staging-4terminal-master-order.md` (T4)
Related Docs:
- `docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md`
- `docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md`

## 1. Findings

### Finding 1. Manuscript has a powerful but genre-locked POV rendering engine

The current manuscript layer owns a well-structured "Sovereign Shift" POV engine (`config/prompts/writer_rules.json` L65-71) that is the system's primary tool for protagonist high-evaluation rendering:

- **POV Trigger**: "주인공의 행동 결과가 주변 환경을 **파괴**하거나 조연의 상식을 **초월**하는 '경악의 순간'" (L66)
- **Dynamic Observer Selection**: 1순위 고위직, 2순위 적대자, 3순위 무시하던 자 (L67)
- **Contrast Rendering**: 주인공 파트는 건조·이성적 ("설계자의 문체"), 관찰자 파트는 격정적·과잉해석 ("천해의 이치", "신의 한 수") (L68-70)
- **Indifferent Return**: 관찰자 경악 정점에서 주인공 시점 복귀, 반응 무시하고 이득 챙김 (L71)

이 엔진은 **무협/헌터 장르에서는 효과적**이다. 주인공이 물리적 파괴력을 발휘하면 자연스럽게 trigger가 걸리고, 관찰자 POV 전환을 통해 "big number"가 아닌 "주변의 경악과 착각"으로 고평가가 렌더링된다.

**문제**: trigger 조건 자체가 **물리적 파괴/초월**에 고정되어 있다. 재벌/상류/비즈니스-파워 장르에서 주인공의 핵심 성취는:

- 전략적 선견 (strategic foresight)
- 정보 비대칭 활용 (information arbitrage)
- 사회적 위계 충격 (social hierarchy disruption)
- 리스크 보정력 (risk calibration)

이런 성취는 "주변 환경을 파괴"하지 않으므로 현재 POV 엔진이 자동 trigger되지 않는다. 비즈니스 장르에서는 Writer가 POV 전환 타이밍을 스스로 판단해야 하는데, 판단 기준이 없다.

**Evidence**:
- `writer_rules.json:66` — trigger 정의
- `writer_rules.json:77` — "대조의 미학" 또한 "부서진 팔"/"처절한 상태" 등 물리적 비용 전제
- `blueprint_ensemble.py:101` — `side_glimpse` 설명도 "주인공 부재 상황, '저 사람 대단해!' 반응"으로 범용적이지만, 실제 trigger/context는 물리 중심

### Finding 2. Satisfaction Guide는 방향은 맞지만 감탄 모드를 분화하지 않는다

`chief_writer.yaml:172-179` Satisfaction Guide Section:

```
1. 보상 시점: 독자가 쾌감·성취감을 느낄 장면 (경지 돌파, 강자 제압, 자산 성장 등)
2. 좌절-보상 균형
3. 주인공 성장: 주인공의 유능함·성장을 독자가 체감할 수 있는 씬
```

Director의 장르별 보상 예시(`director.yaml:488-492`):

```
무협: 경지 돌파, 강자 제압, 비급 획득, 강호 위상 상승
투자: 의사결정 보상, 자산 성장, 정보 선점 쾌감
```

이 예시들은 모두 **결과 중심**(result-oriented)이다. "무엇을 달성했는가"는 있지만, "어떻게 달성하는 과정이 독자에게 감탄을 주는가"(method-oriented)는 없다.

비즈니스-파워 장르에서 "자산 성장"이라는 결과만으로는 thin praise("돈이 늘었다 → 대단하다")가 된다. 독자가 감탄하려면:

- 남들이 보지 못한 것을 봤다 (정보 격차)
- 동일 조건에서 남들은 틀린 판단을 했다 (판단력 격차)
- 위험을 감수한 방식 자체가 비범했다 (리스크 구조)
- 성취의 파급이 예상 밖이었다 (사회적 충격)

이런 **감탄 모드 분화**(admiration mode differentiation)가 manuscript 프롬프트에 없으므로, Writer는 "큰 숫자 → 감탄"으로 회귀한다.

### Finding 3. 정보 격차 연출은 deprecated된 blueprint 지침에만 존재하고, manuscript에는 대응 지침이 없다

정보 격차(information gap) 연출은 protagonist high-evaluation의 핵심 도구다. "아는 자와 모르는 자 사이의 대조"가 "착각 지수"를 극대화한다.

- **deprecated 아키텍트 규칙**: `deprecated/architect_rules.json:55` — "정보 격차 연출: 아는 자와 모르는 자 사이의 대조를 통해 '착각 지수'를 극대화하라"
- **deprecated High Impact Zone**: `deprecated/architect_rules.json:62` — "현장 조연들의 구체적인 기대치, 오해 상태, 평소의 멸시적 내면을 묘사 재료로 풍부하게 수혈하라"

이 지침은 현재 시스템의 blueprint prompt(`ensemble.yaml`)에 직접적 대응이 없고, manuscript prompt에도 없다. Writer에게 "정보 격차를 활용하라"는 명시적 지시가 없는 상태다.

현재 writer_rules.json의 POV 엔진은 **정보 격차의 결과**(관찰자의 경악)만 렌더링하지, **정보 격차의 구축**(누가 무엇을 모르는지)은 upstream에 의존한다.

**Evidence**:
- `deprecated/architect_rules.json:55` — 정보 격차 연출 (현재 미사용)
- `deprecated/architect_rules.json:62` — High Impact Zone 조연 심리 수혈 (현재 미사용)
- `ensemble.yaml` — 현행 blueprint prompt에 "정보 격차" 관련 지시 없음
- `writer_rules.json` — 현행 manuscript prompt에 "정보 격차" 관련 지시 없음

### Finding 4. "few understand, many misread" 구조는 Arc 레벨에서 설계되어야 manuscript에서 실행 가능하다

Arc 레벨 analyst prompt에 이미 관련 지침이 있다:

- `analyst.yaml:176` — "조연 반응 (150자+): 주인공을 향한 세상의 오해, 경악, 착각"
- `analyst.yaml:553` — "파동의 전이: 주인공의 행동에 대한 주변 인물들의 경악, 착각, 평판 변화 관찰 리포트"

이 재료가 arc → blueprint → manuscript로 흘러올 때, manuscript는 이를 렌더링할 수 있다. 그러나:

1. **Arc에서 "착각 구조"가 얼마나 구체적으로 설계되는지는 arc 품질에 의존**한다. "오해, 경악, 착각"이라는 3어 지시만으로는 "누가, 무엇을, 왜 오해하는지"까지 설계되지 않는다.
2. **Blueprint에서 scene별로 "이 관찰자는 X를 모르고 Y를 안다"가 명시되지 않으면**, manuscript Writer는 범용적 "대단하다" 반응만 쓸 수 있다.
3. **Manuscript는 구조를 발명하기엔 너무 늦은 레이어**다. Writer의 역할은 이미 설계된 구조를 prose로 확장하는 것이다.

### Finding 5. 착각계 서사 패턴 라이브러리는 Arc 레벨에 풍부하지만, manuscript 렌더링 지침과 연결되지 않는다

모든 장르에 "착각 고조형" 패턴이 이미 정의되어 있다:

- **무협**: "무심한 행동 → 주변의 경악 → 신화적 해석 → 주인공의 당황 → 지위 공고화" (`analyst_libraries.json:7`)
- **투자**: "낮은 평가 → 과소평가 투자 → 대박 터짐 → 무시하던 자들 경악 → 위상 상승" (`analyst_libraries_investment.json:23`)
- **헌터**: "낮은 랭크 위장 → 무시당함 → 실력 노출 → 경악과 후회 → 위상 급상승" (`analyst_libraries_hunter.json:24`)
- **요리**: "초라한 외관 식당 → 무시당함 → 요리 맛봄 → 경악과 극찬 → 입소문 폭발" (`analyst_libraries_cooking.json:23`)

이 패턴들은 모두 **같은 5-beat 구조**(과소평가 → 무시 → 실력 노출 → 경악 → 위상 상승)를 공유한다. 이 구조 자체는 건전하지만:

- Arc에서 이 패턴이 선택되더라도, **manuscript Writer에게 "이 에피소드는 착각 고조형"이라는 정보가 전달되지 않는다**
- Blueprint에서 scene preset으로 `side_glimpse`가 배정되더라도, Writer는 "왜 이 관찰자가 놀라야 하는지"의 설계 의도를 모른다
- 결과적으로 Writer는 "경악"의 quality를 스스로 결정해야 하며, 이때 "큰 숫자 → 대단해" 회귀가 일어난다

### Finding 6. State_updates에 "착각(misunderstanding)" 메트릭이 있으나 활용되지 않는다

`writer_rules.json:83` — "착각(misunderstanding), 집착(obsession)은 절대값이 아닌 증분으로 표기하라 (예: +50, -10)"

이 메트릭은 주인공에 대한 주변의 오해 수준을 정량화할 수 있는 인프라다. 그러나:

- 이 수치를 읽고 "착각이 N이니 이번 화에서 착각 폭발 장면을 넣으라"는 지시가 없다
- Blueprint에서 이 수치를 참조하지 않는다
- 결과적으로 기록만 되고 서사에 환류되지 않는 dead metric이다

### Finding 7. 전문가 반응 비례성(Director) — 현재 시스템의 유일한 "질적 감탄 보정" 장치

`director.yaml:451` — "전문 직업 캐릭터(PB, 의사, 셰프, 선수, 무인 등)가 자기 분야의 일상적 상황에 과잉 반응하고 있지 않은가? (예: VIP PB가 20억에 놀람→잘못, 3배 레버리지에 놀람→맞음)"

이것은 현재 시스템에서 **유일하게 감탄의 질을 통제하려는 지침**이다. "무엇에 놀라는 것이 합리적인가"를 장르 전문성 기준으로 판단한다.

그러나 이 지침은 **Director 평가 단계**에 있다. 이미 manuscript가 "VIP PB가 20억에 놀라는" 장면을 써버린 뒤에야 Director가 감점하는 구조다. Manuscript Writer에게 사전에 "이 NPC는 이 수준에는 놀라지 않는다"는 정보가 없다.

## 2. Owner Mapping

### Manuscript is a SECONDARY OWNER — not the authoritative owner

| 기능 | Manuscript 역할 | 실행 가능 여부 | 조건 |
|------|----------------|---------------|------|
| POV 전환 렌더링 | **강함** — Sovereign Shift 엔진 | 가능 | Trigger 조건이 장르 맞으면 |
| Contrast Rendering (문체 대비) | **강함** — 건조/격정 대비 | 가능 | 관찰자가 blueprint에 배정되어 있으면 |
| 정보 격차 구축 | **약함** — 구조 발명은 Writer 역할 아님 | 불가 | Blueprint에서 "누가 뭘 모르는지" 설계 필수 |
| 감탄 모드 선택 | **없음** — Writer에게 모드 정보 안 옴 | 불가 | Arc/Blueprint에서 모드 지정 필수 |
| 반응 비례성 판단 | **약함** — Writer에게 NPC 전문성 정보 부족 | 부분 가능 | NPC 프로필이 충분하면 |
| 대사 절제/과잉 조율 | **강함** — prose 문체 제어 | 가능 | 지침만 있으면 |
| Reveal 순서 배치 | **약함** — Blueprint scene order에 종속 | 부분 가능 | Scene 내부 순서만 자유 |

**결론**: Manuscript는 이미 설계된 고평가 구조를 **prose로 확장·렌더링하는 실행 레이어**다. 구조의 설계(누가 뭘 오해하는지, 어떤 감탄 모드인지, 정보 격차는 어디서 발생하는지)는 반드시 upstream(bible/arc/blueprint)에서 와야 한다.

## 3. What Manuscript Does Well (too-late가 아닌 영역)

1. **POV 문체 대비**: 주인공의 건조한 내면 vs. 관찰자의 격정적 해석 — 이것은 manuscript 고유 강점이다. Blueprint가 "관찰자 A를 배정"하기만 하면, Writer가 문체 대비를 실행할 수 있다.

2. **대사 밀도 조절**: "대단하다"를 직접 말하지 않고, 관찰자의 행동 변화(목소리 떨림, 자세 교정, 눈빛 변화)로 감탄을 렌더링하는 것은 manuscript의 역할이다.

3. **무심한 복귀**: 주인공이 주변의 경악을 무시하는 것 자체가 "큰 숫자 칭찬"을 대체하는 가장 효과적인 manuscript 장치다. 이미 writer_rules.json에 규칙이 있다.

4. **착각 증분 추적**: state_updates의 misunderstanding 필드가 장기적으로 활용되면, manuscript 레벨에서도 "착각 폭발 시점"을 인지할 수 있다 (현재는 미활용).

## 4. What Is Too Late At Manuscript (upstream 필수)

1. **관찰자 선정**: Blueprint에 관찰 가능한 NPC가 배정되지 않으면, Writer가 급조한 관찰자는 서사적 무게가 없다.

2. **정보 격차 구축**: "A는 알고 B는 모른다"는 arc/blueprint에서 설계되어야 한다. Manuscript에서 갑자기 "사실 이 인물은 모르고 있었는데..."를 만들면 개연성이 무너진다.

3. **감탄 모드 결정**: "이 에피소드는 전략적 선견 감탄"인지 "사회적 충격 감탄"인지는 arc에서 결정되어야 한다. Manuscript에서 결정하면 arc 설계와 충돌한다.

4. **비물리적 POV trigger**: 비즈니스 장르에서 "경악의 순간"이 물리적 파괴가 아닌 경우, blueprint에서 "여기서 POV 전환하라"는 staging이 없으면 Writer가 자의적으로 판단해야 한다.

5. **전문가 반응 기준**: NPC의 전문성 수준과 해당 NPC가 놀라야 할 threshold가 blueprint/bible에서 설정되지 않으면, Writer가 비례적 반응을 쓸 수 없다.

## 5. Concrete Tradeoff Notes

### Manuscript-level fix vs. Blueprint-level fix

| 접근 | 장점 | 단점 |
|------|------|------|
| Writer 프롬프트에 감탄 모드 지침 추가 | 빠른 적용, 적은 코드 변경 | 설계 없이 렌더링만 개선 → 구조적 한계 |
| Blueprint에 감탄 설계 필드 추가 | 구조적 해결, Writer에게 명확한 재료 제공 | Blueprint prompt 확장 필요 |
| Bible에 감탄 축(admiration axes) 정의 | 전 장르 일관성, 장기 효과 | 가장 느린 적용, 기존 bible 구조 확장 필요 |

### Writer prompt 수준에서 할 수 있는 bounded improvement

Writer 프롬프트에 아래를 추가하면 "manuscript-only" 개선이 가능하나, 효과 상한이 있다:

- **감탄 렌더링 금지 패턴**: "숫자 직접 언급 → 감탄" 금지, "행동/결과의 함의를 관찰자가 해석"하는 방식 권장
- **비물리적 POV trigger 확장**: "전략적 판단이 밝혀지는 순간", "정보 우위가 드러나는 순간"도 trigger 조건에 추가
- **반응 비례성 사전 지침**: NPC 프로필에 명시된 전문성 수준을 참조하라는 지시

그러나 이런 manuscript-only fix는 **upstream에서 "어떤 감탄인지"를 설계해주지 않으면** Writer가 스스로 판단해야 하므로, 품질 편차가 크다.

## 6. Classification

| 분류 | 판정 |
|------|------|
| **Authoritative owner** | ❌ — Manuscript는 authoritative owner가 아니다 |
| **Secondary owner** | ✅ — 렌더링/실행 레이어로서 secondary owner |
| **Too-late layer** | 부분적 ✅ — 구조 설계(정보 격차, 감탄 모드, 관찰자 선정)는 too-late |

## 7. Confidence

Estimated confidence: 96%

근거:
- 모든 claim은 live code evidence(file:line)에 기반
- POV 엔진의 물리 편향은 trigger 정의 문장에서 직접 확인
- Satisfaction Guide의 결과 중심성은 장르별 예시에서 직접 확인
- 정보 격차 지침의 부재는 현행 prompt + deprecated prompt 비교로 확인
- 착각 메트릭의 미활용은 writer_rules.json ↔ blueprint prompt 크로스 확인

한계:
- 실제 live run에서 Writer가 비물리적 장르에서 POV 전환을 얼마나 자발적으로 하는지는 미확인
- "큰 숫자 → 감탄" 회귀의 빈도는 산출물 전수조사가 필요하나 본 survey 범위 밖

---

Authoritative owner in this lane: none — manuscript는 secondary owner이며, protagonist overvaluation의 authoritative 설계권은 upstream(bible/blueprint)에 있다
Best bounded next wave from this lane: Writer 프롬프트의 비물리적 POV trigger 확장 + 감탄 렌더링 금지 패턴 추가 (단, blueprint-level 감탄 설계가 선행되어야 실효성 확보)
Should Codex open an execution SSOT from this lane now: no
