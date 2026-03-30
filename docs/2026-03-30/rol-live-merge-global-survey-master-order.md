# ROL Live-Merge Global Survey Master Order

Date: 2026-03-30
Status: draft-live-run-pending
Canonical Path: `docs/2026-03-30/rol-live-merge-global-survey-master-order.md`
Temp Mirror Path: `(none - operator order only; no temp mirror during active live run)`
Baseline Commit: `9ad4efcc`
Baseline Dirty Summary: `dirty: Stage 3 validator/tests touched, live 0_1 Stage 3/4 artifacts and logs advancing, several 2026-03-30 docs untracked`
Mode: `ROL live-merge`
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`

## 1. Purpose

This is the operator master order for a read-only, five-terminal global survey while a live Stage 4 run is still active.

Use this only for:
- repo-wide system-track survey work
- LLM friendliness
- harness reinforcement
- observability, regression, and operator ergonomics
- draft watchlists and evidence gathering during a live run

Do not use this order for:
- code changes
- DB writes
- artifact/manual repair
- temp queue cleanup
- final SSOT closure while the run is still active

## 2. Global Rules

All terminals must follow these rules:

1. Read-only only.
2. No code edits, no DB edits, no `docs/temp/` mutation.
3. Do not create canonical final survey conclusions while the live run is active.
4. Terminal outputs must not stop at terminal-only reports if findings exist.
5. Each terminal that finds any `action-bearing` item or non-trivial `watchlist` must save one lane draft note marked `draft-live-run-pending`.
6. If a terminal truly has only `non-issues`, it may stop at terminal output without saving a doc.
7. If a terminal absolutely needs a file artifact before conclusion, it may save raw evidence or a clearly marked draft note with `draft-live-run-pending`.
8. Prefer live code and active runtime evidence over stale docs.
9. Treat all findings as provisional until the live run reaches a terminal state.
10. Use absolute file paths and line references.
11. Split output into:
   - `action-bearing`
   - `watchlist`
12. Do not duplicate another terminal's scope.

Draft-note rule:
- lane draft notes are allowed during the active run
- they are not final surveys or closure claims
- they must be explicitly labeled `draft-live-run-pending`
- they should capture enough detail that the main terminal can merge without losing findings
- they must stay in `docs/2026-03-30/`, not `docs/temp/`

## 3. Output Contract Per Terminal

Each terminal should return exactly this shape in terminal output:

1. `Coverage`
- what it inspected
- what it intentionally excluded

2. `Action-Bearing`
- ordered by severity
- concise
- absolute file path + line refs

3. `Watchlist`
- lower-confidence or deferred items
- absolute file path + line refs

4. `Non-Issues`
- useful “looks fine” notes only if they reduce future duplicate work

5. `Stop`
- explicit line: `read-only lane complete; no files mutated`

If findings exist, each terminal should also save one draft note with this shape:

1. `Date`
2. `Status: draft-live-run-pending`
3. `Lane`
4. `Coverage`
5. `Action-Bearing`
6. `Watchlist`
7. `Non-Issues`
8. `Merge Notes`

## 4. Main Terminal Role

The main terminal is the aggregator and rolling-draft owner.

Main terminal responsibilities:
- launch the five lane orders
- collect terminal outputs
- ensure each finding-bearing lane saves a draft note
- maintain one rolling aggregate draft watchlist while the run is active
- avoid making final conclusions mid-run
- wait for the live Stage 4 run to finish before asking for merged canonical synthesis

The main terminal must not:
- patch code
- edit DB
- create execution SSOT mirrors
- refresh `docs/temp/execution-roadmap.md`

Recommended rolling aggregate draft path:
- `docs/2026-03-30/rol-live-merge-global-survey-rolling-watchlist.md`

Recommended lane draft paths:
- `docs/2026-03-30/rol-live-merge-global-survey-lane1-runtime-draft.md`
- `docs/2026-03-30/rol-live-merge-global-survey-lane2-agent-validator-draft.md`
- `docs/2026-03-30/rol-live-merge-global-survey-lane3-persistence-observability-draft.md`
- `docs/2026-03-30/rol-live-merge-global-survey-lane4-harness-regression-draft.md`
- `docs/2026-03-30/rol-live-merge-global-survey-lane5-operator-config-draft.md`

## 5. Terminal 1 Order

Use this as-is:

```text
글도비 시스템 오더. 넌 1번 터미널이다. 이번 턴은 `ROL live-merge global survey`의 `runtime/core/orchestration` lane만 read-only로 조사하라. 코드 수정 금지, DB 수정 금지, docs/temp 수정 금지, final canonical doc save 금지.

조사 범위:
- `main_a.py`
- `modules/core/*orchestrator*.py`
- runtime entry/control-flow spine
- retry loop, bootstrap, stage dispatch, headless/operator split

조사 테마:
- LLM 친화도
- branch density / long-function hotspot
- authority seam
- operator-visible runtime observability
- retry/recovery/control-flow confusion

반드시 볼 것:
- top-level entry flow
- Stage 2/3/4 orchestration seam
- interactive input이 runtime authority와 섞인 지점
- partial-init tolerated state

출력 형식:
1. Coverage
2. Action-Bearing
3. Watchlist
4. Non-Issues
5. `read-only lane complete; no files mutated`

문서 저장 규칙:
- action-bearing 또는 의미 있는 watchlist가 있으면
  `docs/2026-03-30/rol-live-merge-global-survey-lane1-runtime-draft.md`
  에 `Status: draft-live-run-pending`로 저장
- non-issue only면 문서 저장 생략 가능

절대 금지:
- 코드 수정
- final closure 문서 저장
- 다른 lane scope 침범
```

## 6. Terminal 2 Order

Use this as-is:

```text
글도비 시스템 오더. 넌 2번 터미널이다. 이번 턴은 `ROL live-merge global survey`의 `agent/validator/binding` lane만 read-only로 조사하라. 코드 수정 금지, DB 수정 금지, docs/temp 수정 금지, final canonical doc save 금지.

조사 범위:
- `modules/domain/agents/`
- Stage 2/3/4 validator, director binding, PASS/PASS_WITH_FIX/REJECT contract
- structured completeness / invariant / advisory-only seam

조사 테마:
- LLM 친화도
- advisory-only 검사
- binding 누락
- duplicated validation
- false positive risk
- generator vs validator vs selector 책임 분리

특히 볼 것:
- Stage 2 carryover/state integrity 관련 validator seam
- Stage 3 blueprint completeness / timeline / capital unit binding
- Stage 4 numeric/advisory vs binding seam

출력 형식:
1. Coverage
2. Action-Bearing
3. Watchlist
4. Non-Issues
5. `read-only lane complete; no files mutated`

문서 저장 규칙:
- action-bearing 또는 의미 있는 watchlist가 있으면
  `docs/2026-03-30/rol-live-merge-global-survey-lane2-agent-validator-draft.md`
  에 `Status: draft-live-run-pending`로 저장
- non-issue only면 문서 저장 생략 가능

절대 금지:
- 코드 수정
- final closure 문서 저장
- runtime artifact patch
```

## 7. Terminal 3 Order

Use this as-is:

```text
글도비 시스템 오더. 넌 3번 터미널이다. 이번 턴은 `ROL live-merge global survey`의 `persistence/observability/sink` lane만 read-only로 조사하라. 코드 수정 금지, DB 수정 금지, docs/temp 수정 금지, final canonical doc save 금지.

조사 범위:
- DB manager
- session logger
- runtime audit / jsonl / summary sink
- console / ui-visible output path
- artifact truth / metadata truth seam

조사 테마:
- authority sink가 어디인지
- duplicated sink / mismatch risk
- operator visibility gap
- rollback/recovery/compensation notes
- sink semantics drift

특히 볼 것:
- stage_attempts vs pass_rate_monitor vs episode_production 류 contract family
- console와 structured sink 사이 drift 가능성
- active run evidence를 어디까지 authoritative로 봐야 하는지

출력 형식:
1. Coverage
2. Action-Bearing
3. Watchlist
4. Non-Issues
5. `read-only lane complete; no files mutated`

문서 저장 규칙:
- action-bearing 또는 의미 있는 watchlist가 있으면
  `docs/2026-03-30/rol-live-merge-global-survey-lane3-persistence-observability-draft.md`
  에 `Status: draft-live-run-pending`로 저장
- non-issue only면 문서 저장 생략 가능

절대 금지:
- DB write
- 로그 정리/삭제
- final closure 판단
```

## 8. Terminal 4 Order

Use this as-is:

```text
글도비 시스템 오더. 넌 4번 터미널이다. 이번 턴은 `ROL live-merge global survey`의 `harness/test/canary/queue` lane만 read-only로 조사하라. 코드 수정 금지, DB 수정 금지, docs/temp 수정 금지, final canonical doc save 금지.

조사 범위:
- `docs/implementation/`
- `scripts/`의 canary / survey / queue / validator 계열
- `tests/`
- low-memory pytest / regression harness / smoke runner

조사 테마:
- 하네스 보강 ROI
- queue/process brittleness
- regression blind spot
- flaky/advisory-only test
- live-merge usability

특히 볼 것:
- temp queue와 active live run이 충돌하는 운영 지점
- test가 실제 defect family를 못 막는 구간
- harness가 문서상으론 맞는데 operator friction이 큰 지점

출력 형식:
1. Coverage
2. Action-Bearing
3. Watchlist
4. Non-Issues
5. `read-only lane complete; no files mutated`

문서 저장 규칙:
- action-bearing 또는 의미 있는 watchlist가 있으면
  `docs/2026-03-30/rol-live-merge-global-survey-lane4-harness-regression-draft.md`
  에 `Status: draft-live-run-pending`로 저장
- non-issue only면 문서 저장 생략 가능

절대 금지:
- docs/temp 변경
- queue cleanup
- script patch
```

## 9. Terminal 5 Order

Use this as-is:

```text
글도비 시스템 오더. 넌 5번 터미널이다. 이번 턴은 `ROL live-merge global survey`의 `UI/desktop/config/operator-ergonomics` lane만 read-only로 조사하라. 코드 수정 금지, DB 수정 금지, docs/temp 수정 금지, final canonical doc save 금지.

조사 범위:
- `UI/`
- `geuldobi-desktop/`
- `config/`
- model routing/config
- prompt maps
- bootstrap/env assumption

조사 테마:
- operator ergonomics
- model/provider ambiguity
- LLM 친화도
- config drift risk
- bootstrap confusion
- silent fallback or routing surprise

특히 볼 것:
- 어떤 설정이 operator에게 불투명한지
- LLM/provider/model 라우팅이 어디서 혼동되는지
- UI/desktop surface와 core runtime contract가 어긋나는 지점

출력 형식:
1. Coverage
2. Action-Bearing
3. Watchlist
4. Non-Issues
5. `read-only lane complete; no files mutated`

문서 저장 규칙:
- action-bearing 또는 의미 있는 watchlist가 있으면
  `docs/2026-03-30/rol-live-merge-global-survey-lane5-operator-config-draft.md`
  에 `Status: draft-live-run-pending`로 저장
- non-issue only면 문서 저장 생략 가능

절대 금지:
- config 수정
- app shell 수정
- live run에 영향 주는 action
```

## 10. Recommended Operator Sequence

1. Keep the live Stage 4 run untouched.
2. Open five terminals.
3. Paste Terminal 1 through Terminal 5 orders exactly.
4. Let each lane finish independently.
5. Collect outputs and lane draft docs in the main terminal.
6. Update the rolling aggregate draft if any lane reports findings.
7. Do not synthesize final canonical conclusions until the Stage 4 run reaches a terminal state.
8. After the run stops, request:
   - merged watchlist synthesis
   - or full post-run merge audit

## 11. Draft Follow-Up Names

If a post-run merged survey is requested later, recommended names are:

- master survey:
  - `docs/2026-03-30/rol-live-merge-global-survey-post-run-merge-audit.md`
- evidence manifest:
  - `docs/2026-03-30/rol-live-merge-global-survey-evidence-manifest.md`
- if action-bearing areas emerge:
  - area execution SSOTs in `docs/2026-03-30/`
- only after final audit:
  - corresponding execution mirrors in `docs/temp/`

## 12. 3-Pass Audit Record

Pass 1 - Structure and scope:
- document type matches operator master order
- five terminal lanes are disjoint
- live-merge constraints are explicit

Pass 2 - Evidence and consistency:
- path policy matches active harness rules
- no temp mirror requested during active run
- lane findings are not allowed to vanish into terminal-only output
- queue and live-run guardrails do not conflict

Pass 3 - Execution and readability:
- each lane is copy-paste ready
- ownership is clear
- merge path is explicit
- next operator step is explicit

Confidence:
- 97% for intended use as a live-run operator order
