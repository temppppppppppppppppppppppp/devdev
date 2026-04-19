# 0_0 Stage3 Opening Transition Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: closed (closure-review passed on 2026-04-19; the fresh bounded `ep13/ep17/ep18` carryover chain shows the Stage3 producer-side opening/carryover truth family is no longer front-active debt, and any broader downstream continuity residue now belongs to Stage4 consumer ownership rather than this sibling lane)
Canonical Path: `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` (removed during the 2026-04-19 closure cleanup)
Commit State:
- Baseline Commit: `eac3386ce3b19f720e6e12548721df5abe2ee755`
- Baseline Dirty Summary: `clean`
- Resume Commit: `029df1a74af89a7b5387c449f4723a5df0d000d4`
- Resume Drift Summary: `the 2026-04-19 queue controller is now authoritative; the Stage3 contract-tightening parent lane is closed, the later `ep13/ep17/ep18` carryover proof chain is now the live authority for this sibling lane, and the older proof-pending wording is historical queue residue rather than the current controller`
Source Survey Docs:
- `docs/2026-04-19/stage3-opening-transition-reactivation-refresh.md`
- `docs/2026-04-19/stage3-opening-transition-closure-review.md`
- `docs/2026-04-19/active-temp-execution-roadmap.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-ep13-cross-arc-carryover-proof.md`
- `docs/2026-04-02/0_0-stage34-ep2-focused-bounded-canary-audit.md`
- `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-run-audit.md`
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
- `docs/2026-04-07/cross-pc-implementation-handoff-context-2026-04-07.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-11/stage23-current-main-static-parallel-survey.md`
Evidence Artifacts:
- `projects/_canary/probe_a_stage3_ep13carry_ab_r2/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17bindingfix_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17receiptsem_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17schemafallback_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep18carry_r3/logs/stage3_canary_summary.json`
- `docs/2026-04-02/0_0-stage34-ep2-focused-bounded-canary-evidence.json`
- `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-run-evidence.json`
Side-Effect Coverage: covered

## 1. Answer First

이 lane의 첫 bounded tranche는 이제 landed 상태다.

핵심 변화는 `오프닝은 무조건 같은 장소 직접 연속`이라는 hard rule을 넣은 것이 아니라, Stage3가 아래 세 가지를 구분하는 구조 계약을 top-level blueprint에 정규화해 주도록 만든 점이다.

- `direct_continuation`
- `explicit_transition`
- `jump_opening`

이제 Stage4는 opening movement/path semantics를 prose와 직전 ending에서 과하게 추론하는 대신, `opening_transition.type`을 structured contract로 받는다. 다만 이번 tranche는 contract normalization + downstream transport까지만 다루며, broad Stage3 prompt retuning, canary/live proof, Stage4 opening logic 대형 재작성은 여전히 defer다.

## 2. Why This Exists

최근 ep2 bounded canary와 demo evidence가 공통으로 보여준 결론은 같다.

1. Stage3 blueprint 자체는 종종 high score로 통과한다.
2. 하지만 `EP1 ending -> EP2 opening`이 direct continuation인지, explicit movement/time cut인지, deliberate jump인지 BP가 구조화해 주지 않으면 Stage4가 과도하게 해석한다.
3. 그 결과 Stage4 opening continuity churn이 커지고, replay suppression과 spatial continuity hard-binding이 Stage4 쪽에 과부하로 남는다.

즉 이 lane의 owner는 `Stage4 repair`가 아니라 `Stage3/BP contract disambiguation`이다.

## 3. Scope

Included in this tranche:

- `start_location`, `time_flow`, `scene_1.location`, `scene_1.title` live owner re-audit
- Stage3-owned `opening_transition` contract normalization
- `direct continuation / explicit transition / jump opening` machine-readable split
- Stage4 mandatory context / IFC / V75-D blueprint repair guidance의 최소 intake transport
- response schema 노출과 validator-side mismatch detection

Excluded:

- broad Stage3 generator prompt retuning
- active Stage4 remediation stack 재우선화
- canary/live proof
- Stage2 redesign
- broad narrative schema rewrite

## 4. Live Findings

Pre-change re-audit 기준:

1. `start_location`, `time_flow`, `scene_1.location`, `scene_1.title`는 이미 Stage3 validation과 Stage4 consumer surfaces에 걸쳐 contract anchor로 쓰이고 있었다.
2. 하지만 `transition type` 자체는 구조 field가 아니라 Stage4-side prose inference burden으로 남아 있었다.
3. `Stage3`는 opening-anchor completeness와 `_stage3_meta` handoff를 이미 소유하고 있었기 때문에, 첫 tranche owner를 Stage3 normalization으로 두는 것이 가장 bounded했다.
4. `Stage4`는 새 owner가 아니라 downstream consumer로만 연결하는 편이 맞았다.

## 5. Hard Conclusions

1. 필요한 것은 same-place hard lock이 아니라 `설명 가능한 opening transition contract`다.
2. 첫 owner는 Stage4가 아니라 Stage3/blueprint normalization이어야 한다.
3. Stage4는 이 contract를 structured intake로 소비해야 하고, prose inference burden은 줄여야 한다.
4. 이 tranche는 repair runtime 본체를 다시 쓰는 lane이 아니라 contract/handoff lane이다.

## 6. Implementation Update (2026-04-07)

Landed bounded tranche:

- `modules/core/stage_cross_stage_contract.py`
  - shared opening-transition helper 추가
  - `direct_continuation`, `explicit_transition`, `jump_opening` 추론/정규화
- `modules/core/response_schemas.py`
  - `BLUEPRINT_SCHEMA`에 top-level `opening_transition` object 노출
- `modules/domain/agents/unified_blueprint_validator.py`
  - prevalidation 시작 시 `opening_transition` 정규화
  - 선언 타입이 opening anchors와 충돌하면 `opening_transition` binding issue로 표면화
- `modules/core/stage4_immutable_fact_contract.py`
  - IFC packet이 `opening_transition.type`을 함께 운반/렌더
- `modules/core/stage4_context_builder.py`
  - mandatory context가 structured `opening_transition.type`을 Stage4 opening authority로 노출
- `modules/core/stage4_orchestrator.py`
  - V75-D blueprint repair guidance가 `opening_transition.type`을 authoritative contract로 함께 전달

Execution shape kept bounded:

- broad generator prompt changes 없음
- Stage4 opening logic rewrite 없음
- DB/schema mutation 없음
- runtime/canary proof 없음

## 7. Remaining Deferred

- fresh canary/live proof
- Stage3 generator prompt 자체가 `opening_transition`을 더 직접 출력하도록 만드는 retuning
- `opening_transition.type`과 다른 Stage3/continuity surfaces 간의 더 강한 mismatch hardening
- richer Stage4 consumer adoption beyond context/IFC/V75-D intake

## 8. Acceptance Criteria

Tranche 1 기준:

1. blueprint가 top-level `opening_transition.type`을 구조적으로 가진다.
2. `direct_continuation / explicit_transition / jump_opening`이 Stage3 owner contract로 구분된다.
3. Stage4는 이 타입을 prose inference가 아니라 structured intake로 받는다.
4. 기존 `start_location / time_flow / scene_1.location / scene_1.title` 의미와 충돌하지 않는다.
5. broad Stage3 retuning이나 Stage4 rewrite 없이 bounded transport만 landed한다.
6. current-arc `arc_start_state` opening authority가 stale `prev_blueprint` opening state에 다시 눌리지 않는다.
7. investment `capital_continuity_packet`이 future-episode `capital_changes` / `financial_events`를 현재 화 authority처럼 조기 노출하지 않는다.

현재 판정:

- `1-7`: achieved
- runtime proof / closure: deferred

## 9. Queue Placement

이 lane은 이제 `partially_realized upstream contract lane`이다.

- active proof-deferred Stage4 front stack 아래
- `0_0-stage3-contract-tightening-remediation` 아래
- `0_0-stage234-cross-stage-contract-normalization-remediation` 다음 bounded child realization으로 처리됨
  - live-workspace 기준으로는 sibling follow-up까지 landed한 partial lane이며, 다음 useful artifact는 fresh proof wave다

## 10. Next Action

- 이 lane은 partial로 유지한다.
- fresh canary/live proof가 기본 다음 액션이었고, 2026-04-12 live rerun follow-up bounded sibling role is now also landed: the ep2 -> ep3 seam now carries tighter immediate-next-day / season-truth / blocked-scene-family support so replayed morning openings are not left to downstream Stage4 rejection alone.
  - bounded opening-authority / capital-boundary filtering follow-up은 이미 landed 상태로 취급한다.
- broad Stage3 prompt retuning은 proof 이후 tranche로 넘긴다.
  - parent `0_0-stage3-contract-tightening-remediation`와 함께 같은 proof wave 결과를 보고 다음 Stage3 opening follow-up 필요성을 다시 판정한다.

## 11. 3-Pass Audit

Pass 1. Structure/Scope
- pre-change owner audit 결과를 반영해 Stage3 normalization lane으로 scope를 재정의
- Stage4는 consumer-only intake로 제한
- non-goal을 broad retuning / big rewrite / canary 금지로 다시 고정

Pass 2. Evidence/Consistency
- `start_location`, `time_flow`, `scene_1.location`, `scene_1.title` live owner surfaces 재확인
- Stage3 validator / Stage4 context / IFC / V75-D intake가 실제 코드 anchor와 맞는지 대조
- roadmap와 cross-PC handoff가 가리키는 next unopened lane이 이 lane이었음을 재확인한 뒤 착수

Pass 3. Execution/Readability
- contract substrate -> Stage3 normalization -> Stage4 intake 순으로 bounded tranche를 landed
- overreach 제거: no broad prompt retuning, no Stage4 opening rewrite, no live proof
- next unopened lane 이동과 defer 잔여분을 명시

Confidence: `97%`

## 12. 2026-04-11 Current-Main Static Re-Audit Upgrade

Evidence basis:

- `docs/2026-04-11/stage23-current-main-static-parallel-survey.md`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage3_orchestrator.py`
- direct Stage2 -> Stage3 boundary guardrail tests on current `main@2b7cb64f`

Current-main findings:

1. `arc_start_state` is applied and can then be weakened again by stale `prev_blueprint.protagonist_state`.
2. `capital_continuity_packet` still reads finance event families without episode-boundary filtering.

Execution consequence:

- keep this as the owner for bounded opening-authority tightening rather than opening a new queue lane
- land, in order:
  1. authoritative `arc_start_state` intake for opening-state inheritance
  2. episode-boundary filtering for investment capital continuity packet construction
- only after that should proof or broader retuning become the next question inside this lane

Confidence for this upgrade: `96%`

## 13. 2026-04-11 Live-Workspace Opening-Authority Landing Update

Evidence basis:

- `modules/domain/agents/blueprint_constraint_compiler.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_clarity_density_wave1.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`

Live-workspace closures:

1. `arc_start_state` opening authority now outranks stale prior-blueprint protagonist-state inheritance.
2. opening location / equipment / injuries now preserve current-arc authority instead of being re-weakened by stale inherited state.
3. investment capital continuity now filters future-episode `capital_changes` / `financial_events` rather than leaking them into the current episode packet.

Execution consequence:

- keep this lane partial, but treat the previously reopened bounded sibling follow-up as landed on the live workspace
- make the next action the fresh proof wave rather than another immediate Stage3 opening patch

## 12. 2026-04-12 EP3 Live-Run Follow-up Role Clarification

Source docs:

- `docs/2026-04-12/stage234-ep3-continuity-replay-season-truth-live-run-followup-parallel-survey.md`
- `docs/2026-04-12/stage234-ep3-continuity-replay-season-truth-live-run-followup-3pass-audit.md`

Execution consequence:

1. keep the already landed opening-authority / capital-boundary filtering tranche as landed
2. treat the bounded sibling support slice as now landed inside `modules/domain/agents/blueprint_constraint_compiler.py`
3. record the landed sibling-owned support surfaces:
   - immediate-next-day opening truth
   - season/timeline carryover clarity (`2006년 1월` / winter context)
   - anti-replay opening disambiguation when the previous episode already consumed the analogous morning-start family
   - prompt-visible `episode_progression_packet` carryover for downstream Stage3 generation
4. keep the Stage3 parent lane as the primary owner of the fail-only ep3 slice; this sibling only supports the opening/progression seam
5. make the next action the bounded proof wave / rerun rather than another immediate Stage3 opening patch
- keep broader prompt retuning and stronger mismatch hardening deferred behind proof

Confidence for this landing update: `97%`

## 14. 2026-04-19 Reactivation Refresh

Evidence basis:

- `docs/2026-04-19/stage3-opening-transition-reactivation-refresh.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-ep13-cross-arc-carryover-proof.md`
- `projects/_canary/probe_a_stage3_ep13carry_ab_r2/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17bindingfix_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17receiptsem_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17schemafallback_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep18carry_r3/logs/stage3_canary_summary.json`

Refresh result:

1. the older `proof remains pending` wording is now stale queue text, not the live front controller
2. later bounded carryover proof now exists beyond the original `ep2 -> ep3` support slice:
   - `ep13 = PASS (94)`
   - `ep17 = PASS (90~96)` across the current late-opening proof family
   - `ep18 = PASS (94)`
3. the remaining aggregate `hard_gates.status = fail` line in those summaries is legacy warning residue:
   - `ep1_final_verdict:PASS_WITH_WARNING`
   - `ep9_final_verdict:PASS_WITH_WARNING`
4. the sibling boundary is now clearer:
   - producer-side opening / carryover truth belongs here
   - downstream continuity residue belongs to Stage4 consumer ownership

Execution consequence:

- do not keep this lane front-active just because the aggregate canary still remembers legacy warning residue
- treat the lane as closure-review ready

## 15. 2026-04-19 Closure Review

Evidence basis:

- `docs/2026-04-19/stage3-opening-transition-closure-review.md`
- `docs/2026-04-19/stage3-opening-transition-reactivation-refresh.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-ep13-cross-arc-carryover-proof.md`
- `projects/_canary/probe_a_stage3_ep13carry_ab_r2/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17bindingfix_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17receiptsem_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep17schemafallback_r1/logs/stage3_canary_summary.json`
- `projects/_canary/probe_a_stage3_ep18carry_r3/logs/stage3_canary_summary.json`

Closure result:

1. the bounded Stage3 opening-transition owner is now closed
2. the fresh carryover proof chain satisfies the lane's honest closure claim:
   - current producer-side opening / carryover truth is no longer front-active debt
   - the lane keeps its evidence as historical backing rather than active workload
3. the correct next queue owner is `0_0-stage4-consumer-contract-normalization-remediation`
4. reopening trigger stays narrow:
   - only reopen if fresh Stage3 evidence shows new bounded producer-side opening / carryover drift beyond the banked `ep13/ep17/ep18` chain
