# Block / Arc / Episode / Manuscript Semantics Survey

Date: 2026-03-30
Status: final
Document Type: bounded system semantics survey
Canonical Path: `docs/2026-03-30/block-arc-episode-manuscript-semantics-survey.md`
Temp Mirror Path: none
Confidence: 97%
Scope:
- `blockguide` narrative semantics
- Stage 2/3/4 runtime `arc` semantics
- BI metadata `episodes_per_arc`
- `block -> episode` realization boundary
- pacing impact from semantic drift
Out of Scope:
- immediate runtime patch execution
- `wuxguide` semantic redesign
- manuscript quality re-audit

Source Evidence:
- `docs/narrative-router/what-how-craft-harness.md`
- `docs/blockguide/treatment-planning-harness.md`
- `docs/blockguide/treatment-production-harness-v2.md`
- `docs/quickref/blockguide_production_quickref.md`
- `modules/core/constants.py`
- `modules/core/stage2_orchestrator.py`
- `modules/validation/validation_orchestrator.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/core/stage3_orchestrator.py`
- `scripts/build_bi_from_phase0_and_tr.py`
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`

---

## 1. Executive Verdict

현재 워크스페이스에는 `arc`가 최소 두 뜻으로 공존한다.

1. `blockguide arc` = `7개 대단원 중 1개`, 즉 `10블록 구조`
2. `runtime arc` = Stage 2/3/4가 다루는 `에피소드 묶음`

여기에 `block`은 `화`가 아니라 본래 `2~6화 분량의 서사 덩어리`로 설계되어 있는데, Stage 3 경계에서 `episode` 프롬프트가 `block` 전체 방향성을 너무 직접적으로 먹는 구간이 남아 있다.

즉 문제의 본질은 다음과 같다.

- `block = episode`로 SSOT가 정의된 것은 아니다
- 하지만 runtime seam 일부가 `block`을 사실상 `single-episode authority`처럼 소비하게 만든다
- `arc = 10블록`은 blockguide 설계 규약에서 왔고, Stage 2 runtime arc와 같은 말이 아니다
- 이름이 같아 충돌하며, 이 충돌이 pacing 저하와 boundary leak를 유발한다

---

## 2. Confirmed Definitions By Layer

### 2.1 Narrative / BlockGuide Layer

`block`은 `화`가 아니다.

- `what-how`는 `Block 1`을 이미 `2~6화권`으로 본다.
- 즉 block은 멀티-episode 단위의 이야기 덩어리다.

Evidence:

- `docs/narrative-router/what-how-craft-harness.md:124`
  - `1 block ~= 5화`
  - `Block 1`만 해도 이미 `2~6화권`

`arc`는 `10블록 대단원`이다.

Evidence:

- `docs/blockguide/treatment-planning-harness.md:758`
  - `7대단원 한 줄 골격`
- `docs/blockguide/treatment-planning-harness.md:759`
  - `대단원별 입구/출구`, `각 10블록 묶음`
- `docs/blockguide/treatment-production-harness-v2.md:430`
  - `7개 대단원(각 10블록)의 서사 골격`
- `docs/blockguide/treatment-production-harness-v2.md:484`
  - `JSON — 대단원 7개, 각 대단원에 10블록 슬롯 개요`

결론:

- `blockguide arc`는 runtime episode bundle이 아니라 `macro_arc`, `대단원`이다.

### 2.2 Stage 2/3/4 Runtime Layer

runtime `arc`는 `episode bundle`이다.

Evidence:

- `modules/core/constants.py:241`
  - `DEFAULT_EP_COUNT = 4`
- `modules/core/constants.py:328`
  - `EPISODES_PER_ARC = 4`
- `modules/core/stage2_orchestrator.py:23`
  - `DEFAULT_EP_COUNT = VolumeSettings.EPISODES_PER_ARC`
- `modules/core/stage2_orchestrator.py:276`
  - `return (ep_num - 1) // DEFAULT_EP_COUNT + 1`
- `modules/domain/agents/four_phase_arc_generator.py:505`
  - 고정보다 큰 사건은 `5화`
- `modules/domain/agents/four_phase_arc_generator.py:508`
  - 표준은 `4화`

결론:

- runtime `arc`는 `3~6화`, 기본 `4화` 단위의 episode bundle이다.

### 2.3 Runtime Drift Inside Stage 2/4

runtime도 한 목소리가 아니다. 일부는 아직 `5화 = 1아크`를 하드코딩한다.

Evidence:

- `modules/validation/validation_orchestrator.py:1645`
  - `arc_position = ep_num % 5  # 5화 = 1아크 기준`
- `modules/domain/agents/state_tracker_npc.py:1502`
  - `arc_no = (ep_num - 1) // 5 + 1`
- `modules/domain/agents/state_tracker_npc.py:1601`
  - 동일한 `5화 기준` fallback

결론:

- Stage 2 기본값은 이미 `4화 arc`로 이동했지만, validation/state tracking 일부는 여전히 `5화 arc`를 상정한다.
- 즉 `runtime arc` 내부에서도 의미 drift가 살아 있다.

### 2.4 BI Metadata Layer

BI는 여전히 `episodes_per_arc = 5`를 기록한다.

Evidence:

- `scripts/build_bi_from_phase0_and_tr.py:393-395`
  - `total_episodes = 350`
  - `episodes_per_arc = 5`
  - `arcs_per_volume = 5`
- `bible/0_bi_chaebol_ent_empire.json:16-18`
  - 동일하게 `episodes_per_arc = 5`

결론:

- BI 메타데이터는 `1 block ~= 1 runtime arc ~= 5 episodes`에 가까운 옛 가정을 유지한다.
- runtime 기본값 `4화 arc`와 BI 메타 `5화 arc`가 충돌한다.

### 2.5 Blueprint / Manuscript Layer

Blueprint와 Manuscript는 episode 단위다.

Evidence:

- `modules/api/bridge_server.py:331`
  - `BI -> TR -> Arc -> Blueprint -> Manuscript`
- `modules/models/blueprint.py`
  - blueprint model is episode artifact
- `modules/models/manuscript.py`
  - manuscript candidate is episode artifact
- `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md:214`
  - `5화 단위 arc 구조가 정상 작동`

결론:

- Stage 3/4는 본질적으로 per-episode pipeline이다.
- 여기서 말하는 `arc`는 `blockguide 대단원`이 아니라 episode grouping이다.

---

## 3. Where Pacing Drift Actually Happens

문제는 `block` 정의 자체보다 `episode prompt boundary`에서 더 크게 발생한다.

### 3.1 Confirmed Boundary Leak

기존 조사에서 이미 다음 세 가지가 확인됐다.

1. `state_changes` arc-wide dump
2. treatment block full-arc exposure
3. stop line under-coverage

Evidence:

- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md:27-30`
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md:47-50`

핵심 문장:

- `state_changes` unfiltered arc-wide dump
- `Treatment Block full-arc exposure`
- stop line blocks only next episode

### 3.2 Stage 3 Treatment Block Injection

Stage 3는 현재 episode blueprint를 만들면서 `plot_roadmap[arc_idx]`를 읽어 넣는다.

Evidence:

- `modules/core/stage3_orchestrator.py:1122-1167`

현재 상태는 과거보다 줄었지만, 여전히 `Arc 개요`, `title`, `emotional_beat`, `foreshadow`, `content.context`, `genre_ext`가 episode prompt 앞단에 주입된다.

이 구조의 의미:

- `block`은 원래 multi-episode 덩어리인데
- Stage 3 episode prompt는 그것을 `current episode authority`보다 강한 방향성으로 받아들일 수 있다
- 결과적으로 `한 에피소드가 block 전체를 선소비`하거나, 반대로 `block를 한 화처럼 축약`하는 왜곡이 생긴다

### 3.3 Why This Slows Pacing

느려지는 이유는 두 갈래다.

1. episode가 block 전체를 한 번에 먹으려다 과밀/누수/재수정이 생김
2. 반대로 LLM이 `block`을 single-episode beat처럼 오해하면, block 안에서 보여줘야 할 대표 스파이크를 episode 1개 분량으로 쪼개 버린다

즉 현재 문제는 단순히 `block = 화`라는 명시 정의 때문이 아니라,

- `block`과 `episode` 사이의 realization contract가 강하게 잠겨 있지 않고
- `arc`라는 이름이 두 의미를 동시에 가리키며
- Stage 3 boundary가 block overview를 episode prompt에 과투입하기 때문

---

## 4. Direct Answers To The Two Core Questions

### Q1. 현 하네스는 block를 화로 인식하나

정답: `SSOT는 아니다. 하지만 runtime seam 일부는 그렇게 행동한다.`

정확히는:

- `what-how`와 blockguide는 `block`을 `2~6화 덩어리`로 본다
- Stage 3/4는 episode 단위로 돈다
- 그런데 Stage 3가 `treatment block`을 episode prompt에 넣는 방식 때문에, episode generator가 `block`을 현재 episode의 직접 지시처럼 소비하는 경향이 생긴다

즉 명시 정의는 `block != episode`지만, 실행 체감은 일부 경로에서 `block ~= episode authority`로 흐른다.

### Q2. `arc = 10블록 구조`는 어디서 나왔나

정답: `blockguide planning/production SSOT`에서 나왔다.

정확히는:

- `7대단원`
- `각 대단원 10블록`
- `70블록 Phase 0`

이 세트가 blockguide 설계 규약이다.

이것은 Stage 2 runtime의 `4~5화 묶음 arc`와 같은 개념이 아니다.

---

## 5. Confirmed Semantic Collision Map

| Name now | Real meaning | Authority surface | Current issue |
| --- | --- | --- | --- |
| `block` | 2~6화 분량의 TR/BI 서사 덩어리 | `what-how`, `blockguide` | Stage 3가 episode prompt에 과투입 |
| `blockguide arc` | 10블록 macro structure, 즉 대단원 | planning / production harness | runtime arc와 이름 충돌 |
| `runtime arc` | 3~6화 episode bundle, 기본 4화 | Stage 2/3/4 code | 일부 모듈은 아직 5화 하드코딩 |
| `blueprint` | single episode design | Stage 3 | block overview에 오염됨 |
| `manuscript` | single episode prose | Stage 4 | upstream boundary 오류를 그대로 받음 |
| `BI episodes_per_arc` | 옛 5화 arc metadata | BI builder / BI JSON | runtime 4화 기본값과 충돌 |

---

## 6. System-Level Findings

### F1. `arc`라는 이름이 두 시스템에서 다른 뜻을 가진다

- `blockguide arc` = macro 10-block arc
- `runtime arc` = episode bundle

Severity: high

이름 분리가 없는 한, 새 하네스/조사/패치가 계속 같은 착시를 반복할 가능성이 높다.

### F2. runtime episode-per-arc SSOT가 하나로 잠겨 있지 않다

- constants/stage2는 기본 4화
- validation/state tracking/BI metadata는 5화 잔재

Severity: high

이건 단순 용어 문제가 아니라 실제 continuity / validation / volume math에 영향을 준다.

### F3. Stage 3 boundary가 `block -> episode` 매핑을 과도하게 암묵화한다

block 전체 방향성을 episode prompt에 과투입한다.

Severity: high

이 seam은 pacing drift와 future-state contamination을 동시에 일으킨다.

### F4. blockguide 문서 자체는 `block = 화`를 주장하지 않는다

즉 현재 문제가 생겼다고 해서 blockguide 철학이 처음부터 잘못 잠긴 것은 아니다.

Severity: medium

문제는 주로 runtime bridge semantics다.

### F5. `office_checkup_next_day_phase0_design.json`은 이 drift의 표면 증상이었다

증상:

- `ARC-01 대표 스파이크`를 `Block 1 spike`라고 부르던 용어 충돌
- ARC-01만 상세 10블록 슬롯, ARC-02~07은 입구/출구만 있는 반쪽 구조

이번 턴에서 이 파일은 다음처럼 정리했다.

- `ARC-01 대표 스파이크`로 용어 정정
- `ARC-02~07`에도 10블록 slot overview를 채워 `대단원 7개, 각 10블록 슬롯 개요` 계약에 맞춤

이는 symptom patch이지, runtime semantics의 근본 해결은 아니다.

---

## 7. Recommended Normalization

### 7.1 Rename The Two Arcs

권장:

- `blockguide arc` -> `macro_arc` 또는 `grand_arc`
- `runtime arc` -> `episode_arc`

적어도 survey/doc/order 층위에서는 더 이상 둘 다 `arc`라고만 부르지 않는다.

### 7.2 Lock A Single Episode-Arc SSOT

하나를 선택해야 한다.

선택지:

- `4화 기본`
- `5화 기본`

중요한 건 값 자체보다 `constants`, `validation`, `state_tracker`, `BI metadata`, `reverse_expander`가 모두 같은 값을 보게 만드는 것이다.

### 7.3 Clarify `block -> episode` Contract

권장 SSOT:

- `1 block = 2~6 episodes worth of story mass`
- `episode_arc = block realization window`, but not synonymous
- `episode_details` is current-episode hard authority
- `treatment block` is overview only, never current-episode event authority

### 7.4 Demote Treatment Block Injection Further

현재보다 더 약하게 써야 한다.

권장:

- `title`
- `theme`
- `promise`
- `open foreshadow`

이 정도까지만 episode generator에 주고,

- `solution`
- `reward`
- `event_villain`
- strong `genre_ext`

는 episode realization authority로 직접 쓰지 않게 해야 한다.

### 7.5 Separate Pacing Governance By Layer

- `block pacing`: what-how / blockguide
- `episode pacing`: Stage 2/3/4 runtime

현재는 둘이 섞여 있어 어느 쪽 문제인지 추적이 어려워진다.

---

## 8. Deployment Consequence

현재 상태에서 운영자가 가져가야 할 결론은 다음과 같다.

1. `blockguide`의 `10블록 대단원` 자체를 폐기할 근거는 없다.
2. pacing 저하의 직접 원인은 `block 정의`보다 `block -> episode boundary`와 `arc 의미 충돌`에 더 가깝다.
3. runtime 의미론 정리가 없으면, 앞으로도
   - block를 episode처럼 써 버리거나
   - episode arc를 blockguide arc로 착각하는 문서 drift
   - 4화/5화 arc math mismatch
   가 반복된다.

---

## 9. Suggested Next Work Item

다음 시스템 오더는 아래로 분리하는 것이 맞다.

`block-arc-episode-runtime-semantics-normalization`

최소 범위:

- terminology rename map 작성
- 4화/5화 episode-arc SSOT 통일
- Stage 3 treatment-block injection contract 재정의
- validation/state-tracker stale 5화 하드코딩 제거
- BI metadata `episodes_per_arc`와 runtime SSOT 정합화

이 작업은 narrative-pipeline 수정보다 `system-track bounded execution`으로 다루는 것이 맞다.
