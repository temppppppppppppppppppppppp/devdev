# 0_0 Stage4 Consumer-Finalization Global Bounded Survey

Date: 2026-04-02
Status: final (3-pass audited)
Document Type: bounded global survey
Canonical Path: `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
Temp Mirror Path: `(none - survey only)`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Baseline Dirty Summary: `dirty: active Stage4 docs/code/test deltas, prepared canary targets, temp roadmap/queue active`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane1-intake-truth-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane2-fixpack-finalization-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane3-postpass-state-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane4-artifact-vertical-slice-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-parallel-master-order.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`
- `projects/0_0/logs/episode_production.jsonl`
- `projects/canary_0_0_stage34_arc2_fixpack_r1/logs/episode_production.jsonl`
- `projects/canary_0_0_stage34_arc2_entitypost_r1/logs/episode_production.jsonl`
- `projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/episode_production.jsonl`
- `projects/canary_0_0_stage4_ep2_tier25/logs/canary_summary.json`
Side-Effect Coverage: covered

## 1. Answer-First

`Stage4`의 현재 본질은 `consumer/finalization split-truth-heavy`입니다.

정확히는:
- intake hierarchy 자체는 무질서하지 않다
- 하지만 intake truth가 prose flattening을 거친다
- finalization은 `fix_pack`과 `post_select_conflict`에서 bounded repair를 자주 `full rewrite`로 평탄화한다
- post-pass 이후에는 `final_state_updates`, `actual_truth`, `world_state`가 서로 다른 owner로 병존한다

즉 현재 `Stage4`의 주 부채는 `품질 생성`보다 `소비/최종화 계약`이다.

## 2. Hard Conclusions

1. `Stage4 intake`는 `authority-aware but prose-flattened`다.
   - Tier 0 authority stack은 코드상 분명하다.
   - 하지만 WorldState, FactLedger, chain_link, arc truth는 최종적으로 prose block으로 LLM에 들어간다.
   - 그래서 intake는 `intake-clean`이 아니라 `intake-mixed`다.

2. `post_select_conflict`가 현재 가장 큰 finalization flattening seam이다.
   - post-select conflict는 bounded local contradiction도 `fix_scope=full`로 강하게 눌러버리는 경향이 있다.
   - 이 경로에서 Director의 `inplace` 성격 fix scope와 runtime routing이 분리된다.

3. `fix_pack` truth는 단일 권위 source가 아니다.
   - Director-authored fix_pack과 runtime-backfilled fix_pack이 공존한다.
   - downstream consumer는 둘을 거의 같은 contract처럼 소비한다.
   - 즉 `어디를 어떻게 고칠지`가 단일 truth가 아니라 synthesized truth가 된다.

4. `Stage4 post-pass state truth`는 세 갈래로 갈라진다.
   - Director `final_state_updates`
   - Manager `actual_truth`
   - Python `WorldState`
   - 이 세 surface가 같은 episode reality를 설명하지만, 저장과 소비가 분리되어 있다.

5. 실제 artifact drift는 `ep2`부터 일관되게 보인다.
   - `ep1`은 carryover가 없어 모든 run에서 안정적이다.
   - `ep2+`부터 entity/proper noun, item continuity, timeline/location, system contamination이 나타난다.
   - 이는 Stage4가 carryover truth를 소비하고 finalization하는 방식의 문제를 뒷받침한다.

6. runtime cost를 가장 크게 올리는 seam은 두 개다.
   - `post_select_conflict + missing_fix_pack`
   - `strong_advisory_escalation_non_local_fix + missing_patch_targets`
   - 둘 다 좋은 candidate를 bounded local repair로 닫지 못하고, broad rewrite 쪽으로 밀어낸다.

## 3. Medium-Confidence Conclusions

1. `active_pressure_vectors`는 Stage4 state split를 키우는 보조 seam이다.
   - blueprint-derived vector가 manuscript-tail filter를 거쳐 `actual_truth`와 `world_state`에 주입된다.
   - Manager가 직접 authoring하지 않았는데 Manager truth surface 안에 같이 저장된다.

2. HUD와 operator-visible truth는 Manager audit 완료 전 잠시 Director truth를 먼저 반영할 수 있다.
   - 이건 항상 문제를 만들지는 않지만, operator가 보는 truth와 persisted truth가 시차를 가질 수 있다.

3. 현재 Stage4는 `intake-clean / finalization-clean`보다는 `intake-mixed / finalization-lossy`, 심하게 보면 `split-truth-heavy`에 가깝다.
   - lane 1은 intake architecture를 긍정적으로 봤다.
   - lane 3, 4는 post-pass and artifact truth 기준에서 split-truth를 더 강하게 지지한다.
   - 종합하면 전체 판정은 `split-truth-heavy`가 더 가깝다.

## 4. Open Questions

1. `actual_truth`와 `final_state_updates` 중 어떤 field family를 어느 owner에 고정할지 명시적 matrix가 아직 없다.
2. Tier 0 canonical truth가 context budget hard trim에서 실제로 얼마나 자주 잘리는지 정량 evidence는 아직 부족하다.
3. runtime-synthesized fix_pack을 별도 provenance field로 올릴지, 아니면 Director contract와 완전히 분리할지는 아직 미정이다.

## 5. Intake Truth

Stage4 intake는 생각보다 잘 정리돼 있다.

- canonical constraints
- continuity packet
- fact ledger summary
- timeline summary
- world state summary
- mandatory context seed
- arc constraint summary

이 순서와 suppress logic 자체는 건전하다.

문제는 이 authority hierarchy가 LLM에게 들어갈 때 거의 전부 prose가 된다는 점이다. 즉 Stage4 intake의 약점은 `hierarchy 부재`보다 `machine-readable authority loss`다.

## 6. Finalization Truth

Stage4 finalization은 현재 가장 큰 계약 부채 지점이다.

대표 seam:
- strong advisory가 PASS를 PASS_WITH_FIX, 다시 REJECT로 재분류
- post_select_conflict가 bounded repair와 rewrite-class contradiction를 비슷하게 취급
- authoritative_fix_scope는 남지만 실제 routing은 flattened `fix_scope`를 더 강하게 따른다

즉 finalization의 본체는 `quality gate failure`보다 `repair contract precision failure`다.

## 7. State Truth

PASS 이후의 truth는 하나가 아니다.

- Director가 본 `final_state_updates`
- Manager가 읽은 `actual_truth`
- Python이 저장하는 `world_state`

이 셋은 같은 episode truth를 설명하지만, owner와 persistence path가 다르다. 현재 Stage4는 이 셋을 reconcile하기보다 병치한다. 이 구조는 나중에 operator confusion, next-episode carryover drift, source-of-truth ambiguity를 만든다.

## 8. Artifact Truth

대표 vertical slice는 선명하다.

- `ep1`: clean
- `ep2`: first carryover contradiction
- `ep3-ep5`: same families repeat with escalating cost

주 drift family:
- entity / proper noun drift
- physical object continuity drift
- timeline / location drift
- system / HUD contamination

artifact 기준으로 보면, Stage4는 좋은 원고를 못 쓰는 것보다 `carryover contradiction을 bounded repair로 닫는 데 계속 실패하는 구조`가 더 크다.

## 9. Dominant Consumer-Side Contract Drifts

1. `post_select_fix_scope_flattening`
   - bounded contradiction subtype이 full rewrite로 평탄화된다.

2. `state_truth_triple_split`
   - final_state_updates / actual_truth / world_state가 reconciliation 없이 병존한다.

3. `intake_prose_flattening`
   - Tier 0 canonical truth가 prose-only로 Stage4 generation에 들어간다.

## 10. Combined Verdict

`Stage4`는 `split-truth-heavy finalization-loss` 상태다.

더 풀어 쓰면:
- intake는 mixed
- finalization은 lossy
- post-pass state는 split-truth-heavy
- artifact truth는 carryover 구간에서 loss가 누적된다

## 11. Next Action

다음 액션은 `Stage4 consumer-contract normalization` bounded execution SSOT다.

우선순위는 이 순서가 맞다.

1. `post_select_conflict` subtype + bounded repair contract normalization
2. `fix_pack` provenance / routing contract normalization
3. `final_state_updates` vs `actual_truth` owner boundary normalization

즉 지금 Stage4에서 더 필요한 것은 broad prompt retune이 아니라 `consumer-side contract normalization`이다.

## 12. 3-Pass Audit Record

Pass 1, structure and scope:

- survey type is correct
- scope stayed on Stage4 consumer/finalization only
- intake, finalization, state truth, and artifact truth were separated

Pass 2, evidence and consistency:

- lane verdicts were consistent enough to synthesize
- lane 3 confidence gap was bounded using lane 4 artifact evidence
- combined verdict was kept within inspected Stage4 surfaces only

Pass 3, execution and readability:

- answer-first conclusion is explicit
- dominant drifts and next action are operationally clear
- no queue or execution claims were overpromoted

Confidence: `96%`
