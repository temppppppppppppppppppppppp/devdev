# 0_1 Stage4 EP9 Remediation Post-Patch Bounded Survey

Date: 2026-03-30
Status: final (3-pass audited, 96% confidence)
Document Type: bounded post-patch survey
Canonical Path: `docs/2026-03-30/0_1-stage4-ep9-remediation-postpatch-bounded-survey.md`
Temp Mirror Path: none
Commit State:
- Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
- Baseline Dirty Summary: `dirty: tracked changes in 0_temp.txt, Stage 4 runtime/test/docs, project 0_1 logs/db, blueprint_0008; untracked 2026-03-30 docs/scripts/artifacts and tests/test_stage4_ep9_remediation.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Docs:
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep9-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-03-30/0_1-stage4-ep9-remediation-postpatch-evidence.json`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/session/ui_events.jsonl`
- `projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01..06`
Side-Effect Coverage: covered

## 1. Answer-First

추가 survey 결론은 다음이다.

1. static code 기준으로 EP9의 주 root-cause lane은 닫혔다.
   - `NpcDrift`는 이제 stale `role_at_intro` 단독이 아니라 current-truth ladder를 읽고, `state_tracker.position`을 read-only overlay로 우선 반영한다.
   - anchor: `modules/core/world_state.py:49`, `modules/core/world_state.py:1358`, `modules/core/stage4_interview_round.py:5098`, `modules/core/stage4_interview_round.py:5149`, `modules/core/npc_drift_advisor.py:104`

2. 하지만 “해결 완료”라고 부를 단계는 아직 아니다.
   - fresh EP9 live rerun이 없어서 persisted sink 기준 closure는 입증되지 않았다.
   - 현재 artifact truth는 여전히 `attempt_01..06`만 있고, `ui_events`의 최신 `TF-4` / `TF-PATCH-GATE` / `QR-7` rows도 전부 `stage=null`, `ep_num=null`인 pre-patch run 흔적이다.

3. 남은 문제는 새 root blocker가 아니라 follow-up seam이다.
   - 가장 큰 잔여 observability gap은 attempt 4의 핵심 경로였던 `TF-35 patch re-audit`가 아직도 unattributed라는 점이다.
   - 그 외 `PASS_WITH_FIX` loop lifecycle, `TF-29`, `A-4`, `CoVe` 경고도 일부 bare `ui.log`로 남아 있다.

4. 추가로, stale role truth 패턴은 `NpcDrift` 밖에서는 완전히 정리되지 않았다.
   - `TruthGate`의 `npc_role_consistency`는 아직 `role_at_intro`를 기준으로 비교한다.
   - 장기 설정 anchor도 여전히 `최초 역할`을 전면에 둔다.

즉 이번 패치는 `EP9 root cause remediation`으로는 맞지만, `Stage 4 post-patch closure`로 부르려면 live rerun과 follow-up observability/truth-source audit가 한 번 더 필요하다.

## 2. Hard Conclusions

### 2.1 Static Closure Of The Main EP9 Lane

`NpcDrift` authority seam은 live code에서 실제로 바뀌었다.

- `modules/core/world_state.py:49`
  - `_resolve_authoritative_npc_role()`가 `known_attrs.position -> role -> role_at_intro` 순으로 읽는다.
- `modules/core/world_state.py:1358`
  - `get_npc_role_snapshot()`가 `authoritative_role`과 `authoritative_role_source`를 노출한다.
- `modules/core/stage4_interview_round.py:5098`
  - `_build_npc_drift_snapshots()`가 `state_tracker.npc_registry.position`을 read-only overlay로 섞는다.
- `modules/core/stage4_interview_round.py:5149`
  - `_advisory_npc_drift()`가 world_state raw snapshot 대신 overlay된 snapshot을 사용한다.
- `modules/core/npc_drift_advisor.py:104`
  - 프롬프트 포맷이 `현재기준역할`을 우선 쓰고 `초기참고역할`은 보조로 내린다.
- `modules/core/npc_drift_advisor.py:129`
  - prompt body도 authoritative comparison wording으로 바뀌었다.

이건 root-cause survey가 지적한 `NpcDrift false positive` seam에 정확히 맞는 패치다.

### 2.2 Persisted Runtime Closure Is Not Yet Proven

fresh rerun evidence는 없다.

- `projects/0_1/logs/artifacts/stage4/ep_0009/` 아래 attempt dir는 아직 `attempt_01..06`만 있다.
- `projects/0_1/logs/session/ui_events.jsonl`에서 최신 marker row는 아래 그대로다.
  - `TF-4`: `2026-03-30T20:08:13`, `stage=null`, `ep_num=null`
  - `TF-PATCH-GATE`: `2026-03-30T19:38:24`, `stage=null`, `ep_num=null`
  - `QR-7`: `2026-03-30T19:48:41`, `stage=null`, `ep_num=null`

따라서 현재 상태는 `code fixed, persisted rerun proof pending`이다.

### 2.3 Observability Fix Is Partial, Not Complete

이번 wave는 highest-value marker만 복구했다.

복구된 핵심:
- `TF-4`
- `TF-PATCH-GATE`
- `QR-7`

남은 EP9-relevant bare path:
- `modules/core/stage4_retry_runtime.py:669`
- `modules/core/stage4_retry_runtime.py:673`

위 두 줄은 attempt 4의 `patch_reaudit_fail` 관련 `TF-35` 경로다. 이번 EP9 root-cause 문맥에서 이건 operator reconstruction 가치가 높지만, main blocker는 아니다.

## 3. Medium-Confidence Conclusions

### 3.1 TruthGate Still Carries The Old Role Baseline Pattern

`modules/core/truth_gate.py:358`은 아직:

- `original_role = snap.get("role_at_intro", "")`

를 사용한다.

즉 `NpcDrift`에서는 stale truth source를 줄였지만, `TruthGate`의 `npc_role_consistency` path는 같은 family의 오래된 baseline semantics를 유지하고 있다.

왜 medium confidence인가:
- 이 path는 `manuscript` drift가 아니라 `state_updates.npc_updates` 직접 변경을 보는 lane이다.
- EP9 survey의 주 실패 family는 `NpcDrift`였지 `TruthGate`가 아니었다.
- 그래서 `same bug class remains elsewhere`는 맞지만, `EP9 current blocker`라고 단정할 수준은 아니다.

### 3.2 Long-Term Anchor Still Front-Loads Intro Role

`modules/core/world_state.py:1406`, `modules/core/world_state.py:1416`은 장기 앵커에서 아직 `최초 역할`을 전면 표기한다.

다만 이건 `known_attrs.position`도 함께 보여 주기 때문에 immediate gate bug는 아니다. 그래도 non-gating prompt consumer가 stale role language를 먼저 읽을 가능성은 남는다.

### 3.3 Persisted World-State Anchor Is Still Thin For 박성호

`project_data.db`의 `world_state` anchor는 존재하지만, 현 read-back 시점에는 `alive_npcs["박성호"]`가 없다.

이 사실이 의미하는 바:
- 이번 patch가 `state_tracker` overlay에 의존해 live run 중에는 안전할 가능성이 높다.
- 반면 cold-start / saved-anchor-only diagnostic path는 여전히 under-modeled일 수 있다.

이것도 EP9 current blocker라고 부르긴 어렵지만, live rerun 전까지는 residual uncertainty로 남는다.

## 4. Residual Gap Matrix

| Area | Current Status | Evidence | Operational Meaning |
| --- | --- | --- | --- |
| `NpcDrift` truth source | closed in static code | `world_state.py:49`, `world_state.py:1358`, `stage4_interview_round.py:5098`, `npc_drift_advisor.py:104` | EP9 root false positive seam corrected |
| fake `PASS_WITH_FIX` seam | already landed before this survey | existing Lane2 tests still pass | not a new blocker |
| retry markers `TF-4` / `TF-PATCH-GATE` / `QR-7` | fixed in static code | new tests + line anchors | highest-value EP9 diagnosis path covered |
| patch re-audit `TF-35` attribution | open | `stage4_retry_runtime.py:669`, `stage4_retry_runtime.py:673` | attempt 4 still not losslessly queryable by `stage/ep` |
| full `PASS_WITH_FIX` lifecycle attribution | open | `stage4_retry_runtime.py:138`, `:344`, `:370`, `:754`, `:776`, `:817` | follow-up observability lane |
| repeated-bucket / contradiction advisories | open | `stage4_outcome_runtime.py:737`, `:796` | long reject-streak diagnosis still partial |
| `TruthGate` role consistency authority | open | `truth_gate.py:358` | same stale-baseline family survives outside NpcDrift |
| live rerun proof | absent | only `attempt_01..06` exist | no persisted closure proof yet |

## 5. Side-Effect Survey

### 5.1 File / Artifact Truth

- touched production files:
  - `modules/core/world_state.py`
  - `modules/core/npc_drift_advisor.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_outcome_runtime.py`
- new targeted test:
  - `tests/test_stage4_ep9_remediation.py`
- byte-level evidence:
  - file hashes and byte counts captured in raw evidence JSON
  - UTF-8 read-back passed on all touched files

### 5.2 DB / Persistence Truth

- DB schema change: none
- `world_state` anchor exists, but current saved anchor still lacks `박성호`
- no new persisted EP9 attempt after patch is visible yet

### 5.3 JSONL / Operator Sink Truth

static sink path improved, but persisted rows are still pre-patch artifacts.

- important distinction:
  - code truth: fixed for `TF-4`, `TF-PATCH-GATE`, `QR-7`
  - sink truth: still shows old null-attribution rows because no rerun happened

### 5.4 Rollback / Retry / Recovery

- retry routing semantics were not widened beyond the existing remediation intent
- no new rollback mechanism was added
- no new DB/file sink family was introduced

### 5.5 Config / Bootstrap / Global State

- no config or env mutation
- no new singleton/cache layer
- one residual uncertainty remains:
  - live correctness now partly depends on `state_tracker` overlay when persisted `world_state` is incomplete

## 6. Verification Readout

Passed:

- `py_compile` on touched production/test files
- `python scripts/check_utf8_hygiene.py` on touched production/test files
- `pytest tests/test_stage4_ep9_remediation.py -q`
- `pytest tests/test_npc_drift_advisor.py tests/test_lmi_known_attrs_sync.py -q`
- `pytest tests/test_stage4_interview_round.py -q -k "resolve_retry_lane_routing or npc_drift_returns_all_items_without_truncation"`
- `pytest tests/test_stage4_orchestrator.py -q -k "apply_reject_score_trend_advisory or analyze_reject_round"`
- `pytest tests/test_stage4_lane2_binding_contract.py tests/test_stage4_advisory_escalation_seam.py -q`
- `ruff check` on touched production/test files

Not done:

- fresh EP9 live rerun
- persisted `ui_events` / DB / attempt artifact post-patch verification

## 7. Open Questions

1. fresh EP9 rerun 없이 이 lane을 `resolved`로 올릴 수 있는가?
   - 현재 답은 `no`가 맞다.

2. `TruthGate`도 `authoritative_role` semantics로 옮길 것인가?
   - 같은 stale-baseline family가 남아 있다.

3. retry observability를 어디까지 복구할 것인가?
   - 최소 follow-up은 `TF-35`
   - full follow-up이면 `PASS_WITH_FIX lifecycle + TF-29 + A-4 + CoVe`

4. orientation pack refresh가 필요한가?
   - 이번 patch는 shared contract field(`authoritative_role`)와 operator observability path를 바꿨다.
   - 따라서 closure 전에 orientation-pack refresh 필요 판정이 타당하다.

## 8. Operating Consequence

현재 가장 정확한 운영 판정은 아래다.

- `EP9 remediation code patch`: landed
- `EP9 persisted closure`: not yet proven
- `next highest-value action`: bounded fresh EP9 rerun + post-run merge audit
- `next patch wave if needed`: EP9 root-cause 재수선이 아니라 follow-up observability / truth-source normalization wave

## 9. 3-Pass Audit Summary

Pass 1. Structure and scope
- post-patch bounded survey로 문서 타입과 범위를 고정했다.

Pass 2. Evidence and consistency
- live code, tests, DB anchor, `ui_events`, attempt artifact dir를 교차 확인했다.

Pass 3. Execution/readability
- “무엇이 닫혔고, 무엇이 아직 안 닫혔는가”를 operator action 기준으로 재정렬했다.

Confidence: 96%
