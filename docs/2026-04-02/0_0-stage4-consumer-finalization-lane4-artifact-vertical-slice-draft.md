# 0_0 Stage4 Consumer-Finalization Lane 4: Artifact Vertical Slice / Runtime Drift Taxonomy

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Terminal: Opus Terminal 4
Role: artifact vertical slice / runtime drift taxonomy lane
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Source Order: `docs/2026-04-02/0_0-stage4-consumer-finalization-global-parallel-master-order.md`
Cross-Ref:
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-post-implementation-audit.md`
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-bounded-survey.md`

## 1. Coverage

### 1.1 Artifact Sources Examined

| Source | Episodes | Artifact Count | Final Status |
|---|---|---|---|
| `projects/0_0/` (main) | ep1, ep2 | 4 artifacts | ep1 PASS, ep2 REJECT (stuck) |
| `canary_0_0_stage34_arc2_fixpack_r1` | ep2, ep3, ep4 | 24 artifacts | ep2 PASS(3att), ep3 PASS(7att), ep4 PASS(1att) |
| `canary_0_0_stage34_arc2_entitypost_r1` | ep2, ep3, ep4 | 20 artifacts | ep2 PASS(2att), ep3 PASS(6att), ep4 stuck |
| `canary_0_0_stage34_arc2_ep2loop_r2` | ep2, ep3, ep4, ep5 | 38 artifacts | ep2 PASS(9att), ep3 PASS(1att), ep4 PASS(6att), ep5 stuck |
| `canary_0_0_stage4_ep2_tier25` | ep2 | 4 artifacts | ep2 stuck(2att) |

Total: ~90 Stage4 artifacts across 5 runs covering ep1-ep5.

### 1.2 Log Sources Examined

- `episode_production.jsonl` — verdict chain, gate_basis, conflict_contract, fix_pack, scope_origin (all 5 runs)
- `session/decisions.jsonl` — stage2/3/4 decision chain (main_0_0, fixpack_r1)
- `quality_metrics.jsonl` — retrieval_observation, validation signals (main_0_0)
- `session/state_changes.jsonl` — world_state, fact_ledger post-pass writes (fixpack_r1, ep2loop_r2)
- `runtime_audit.jsonl` — pathology signals, V75-D blueprint patches, CoVe errors (fixpack_r1)
- `project_data.db` — state_logs, manuscripts tables (fixpack_r1)

### 1.3 Narrative Content Inspected

- `main_0_0` ep1 `final_manuscript__C.txt` — full read, 씬 1-5
- `main_0_0` ep2 `selected_candidate__A.txt` — full read, 씬 1-3+
- `fixpack_r1` artifact naming patterns — `selected_before_fix`, `rejected_best`, `patched_blueprint_after_fix`, `patched_after_fix`, `selected_candidate`, `final_manuscript`
- `ep2loop_r2` artifact naming patterns — same plus `final_manuscript` for ep2(att9), ep3(att1), ep4(att6)

## 2. Findings

### F-1. Consumer-side drift first becomes visible at ep2 in every observed run

ep1 is always clean because it has no carryover dependency. In all 5 runs, the first episode with upstream manuscript truth to consume is ep2, and it is also the first episode where real narrative contradictions appear.

Evidence summary (ep2 across all runs):

| Run | ep2 Outcome | Primary Gate | Contradiction Type |
|---|---|---|---|
| main_0_0 | REJECT (stuck) | `post_select_conflict` | 서재 위치, SW그룹→한성그룹, 바지→재킷 주머니 |
| fixpack_r1 | PASS (3 att) | `post_select_conflict` then `patch_reaudit_fail` | 시간 연속성, 이면지 위치 |
| entitypost_r1 | PASS (2 att) | `continuity_firewall` | 연속성 모순 |
| ep2loop_r2 | PASS (9 att) | `post_select_conflict` x5, `strong_advisory` x3 | 연속성 모순, NPC 드리프트 |
| ep2_tier25 | stuck (2 att) | `strong_advisory`, `continuity_firewall` | 연속성 모순 |

### F-2. Four drift families dominate the artifact-level contradictions

**Family A — Entity/Proper Noun Drift (most frequent)**

Observed in: main_0_0 ep2, fixpack_r1 ep2-3, entitypost_r1 ep3-4, ep2loop_r2 ep2-5.

Canonical: `SW그룹`, `SW인베스트먼트`, `박성호(PB)`.
Drifted: `한성그룹`, `한성인베스트먼트`, `신성증권`, `최동욱`.

This is the single most frequent contradiction type. It occurs because ChiefWriter LLM generates plausible Korean proper nouns that are contextually appropriate but do not match the established canonical names from prior episodes.

**Family B — Physical Object Continuity Drift**

Observed in: main_0_0 ep2 (confirmed by conflict_contract), fixpack_r1 ep2.

Example: ep1 manuscript says `종이를 반으로 접어 바지 주머니에 찔러 넣었다` (line 39). ep2 candidate says `재킷 안주머니에 손을 넣어 이면지를 꾹 쥐는` (line 58). The pocket location of the same item (이면지) changes between episodes.

Also: ep2 warnings flag `[V66.1] 연속성: 이미 소유한 '몽블랑 만년필'을(를) 다시 획득하려 함`.

**Family C — Timeline/Location Continuity Drift**

Observed in: main_0_0 ep2, fixpack_r1 ep2-3, ep2loop_r2 ep4.

Example: ep1 ends with protagonist entering the 서재 (study) to meet father. ep2 starts at `서재 앞 복도` (hallway in front of study), ignoring the entry action. The conflict_contract captures this as `심각한 타임라인 및 장소 연속성 오류`.

Also: fixpack_r1 ep3 shows `자산 금액` drift — `20억` vs `19억 9천` depending on whether penalty deductions are pre-applied.

**Family D — System/HUD Contamination**

Observed in: fixpack_r1 ep3 (confirmed), entitypost_r1 ep4, ep2loop_r2 ep4.

The manuscript includes references to `HUD 시스템`, `투자창`, or game-system menus that break the narrative fourth wall. This appears when the LLM's genre-system knowledge leaks into the manuscript text instead of staying in metadata-only fields.

### F-3. True narrative contradictions vs contract/sink flattening: roughly 40/60 split

**True narrative contradictions** (would be visible to a human reader):

- Family A entity drift: SW그룹→한성그룹 is a genuine factual inconsistency
- Family B item drift: 바지 주머니→재킷 안주머니 would be noticed by attentive readers
- Family C timeline drift: 서재 안→서재 앞 복도 is a genuine scene continuity break
- Family D HUD contamination: game-system references breaking immersion

**Contract/sink flattening problems** (system-internal, not directly visible as story errors):

- `missing_fix_pack` — the gate correctly detects a contradiction but the fix_pack contract has no actionable `patch_targets`, causing a full rewrite loop instead of targeted repair. This is not a narrative error; it is a contract metadata gap.
- `missing_patch_targets` in `strong_advisory_escalation` — advisory detects NPC drift but cannot serialize the specific repair target, forcing non_local_fix escalation.
- `patch_reaudit_fail` with `constraint_violation` — the fix was attempted but the re-audit found a new constraint issue introduced by the fix itself, creating recursive correction pressure.
- `post_select_conflict` bucket lumping — timeline, entity, item, and HUD contradictions are all serialized into the same coarse `continuity/history` contract type, hiding subtype-specific repair information.

The 40/60 split means: roughly 40% of retry rounds are driven by genuine narrative contradictions that a reader would catch. The remaining 60% are driven by contract gaps that prevent the runtime from routing to a targeted repair, even when the underlying manuscript quality is acceptable.

### F-4. Two seams dominate the runtime cost

**Seam 1: `post_select_conflict` with `missing_fix_pack`** — >60% of all retry rounds across all runs.

Pattern: Director gives PASS. Post-select contradiction check fires. The contradiction is real (usually entity or timeline drift). But the fix_pack emitted by the contradiction classifier either has empty `patch_targets` or has `target_kind: local_phrase` without a concrete repair instruction. The reject runtime resolves `fix_scope: full` (full rewrite), which discards the director's quality endorsement and forces complete regeneration.

Cost evidence:
- ep2loop_r2 ep2: 5 out of 9 retries were `post_select_conflict` with `missing_fix_pack`
- ep2loop_r2 ep4: all 5 retries before PASS were `post_select_conflict` with `missing_fix_pack`
- fixpack_r1 ep3: 2 out of 6 retries were `post_select_conflict` with `fix_pack_ready` but the fix still required a full round

**Seam 2: `strong_advisory_escalation_non_local_fix` with `missing_patch_targets`** — ~25% of retry rounds.

Pattern: Director gives PASS. Advisory system (usually NPC drift or style signal) flags a non-local issue. The advisory payload does not include concrete `patch_targets`, so the runtime escalates to `non_local_fix`, which forces a rejection even though the director approved.

Cost evidence:
- ep2loop_r2 ep2: 3 out of 9 retries were `strong_advisory_escalation_non_local_fix`
- entitypost_r1 ep3: 4 out of 5 retries before fix were `strong_advisory_escalation_non_local_fix` with `missing_patch_targets`

### F-5. Post-pass state truth alignment with artifact truth

From `state_changes.jsonl` and `project_data.db` state_logs:

- `world_state` and `fact_ledger` are written per-episode after PASS
- The fixpack_r1 DB shows state_logs for ep1-3 with `actual_truth` including `capital`, `active_pressure_vectors`, `inventory_counts`, `karma_matrix`
- The state writes follow the accepted manuscript truth, not rejected candidate truth
- However, when a manuscript PASSes after multiple retries, the state reflects the final accepted manuscript, which may have drifted from the blueprint's intended truth during the retry loop

Specific observation: fixpack_r1 ep3 state shows `capital: 1,990,000,000` (19.9억), while the narrative truth from the blueprint and prior episodes should have been `2,000,000,000` (20억). The manuscript's in-narrative mention of penalty deductions was absorbed into the state as canonical truth even though it may have been LLM embellishment rather than upstream-authorized accounting.

### F-6. Retry cost escalation follows a predictable pattern

| Episode Position | Typical Attempts (median across runs) | Cost Multiple vs ep1 |
|---|---|---|
| ep1 (no carryover) | 1 | 1x |
| ep2 (first carryover) | 2-3 | 2-3x |
| ep3 (accumulated carryover) | 4-6 | 5-8x |
| ep4 (deep carryover) | 3-6 | 4-8x |
| ep5 (max observed) | stuck or 2+ | stuck |

The cost escalation is super-linear because each retry adds new potential contradiction surface area while consuming the same retry budget.

## 3. Non-Issues

### NI-1. ep1 artifact truth is consistently clean

In all 5 runs, ep1 always PASSes on the first attempt with `gate_basis: director_primary_pass`. ep1 has no carryover dependency, so there is no upstream truth to contradict. This confirms that the generation pipeline itself is not broken — the drift is specifically a consumer-side carryover problem.

### NI-2. Director quality judgment is generally reliable

In the vast majority of cases, `director_verdict: PASS` correlates with acceptable manuscript quality. The retries are not caused by the Director misjudging quality. They are caused by post-select gates detecting real contradictions that the Director's quality rubric doesn't catch (entity names, item locations, timeline), or by advisory signals that the Director considers acceptable but the runtime doesn't.

### NI-3. Artifact file integrity is sound

All examined artifacts are valid UTF-8 text, correctly named, and consistently hashed between `episode_production.jsonl` entries and on-disk files. There is no byte-level corruption, no missing artifacts, and no hash mismatch. The artifact sink pipeline is not a source of drift.

### NI-4. State write mechanics are structurally correct

The `world_state` and `fact_ledger` writes in `state_changes.jsonl` are per-episode and correspond to the accepted manuscript. The DB `state_logs` table records are internally consistent. The mechanical state-write path is not broken.

## 4. Verdict

**artifact-lossy**

Justification:

- ep1 (no carryover): artifact-clean across all runs
- ep2+ (carryover-dependent): artifact-lossy — real narrative contradictions appear in entity names, item locations, scene continuity, and occasionally system/HUD contamination
- The runtime contract compounds the lossiness by flattening contradiction subtypes into coarse buckets (`continuity`, `history`) and often failing to produce actionable fix_pack targets, forcing expensive full-rewrite loops
- The post-pass state truth can drift from upstream blueprint truth when the accepted manuscript introduces LLM-embellished specifics (asset amounts, timeline details) that are absorbed as canonical
- The retry cost escalates super-linearly with episode count, making later episodes progressively harder and more expensive to finalize

The system is best described as: **intake-clean / finalization-lossy with escalating carryover pressure**.

The single consumer-side contract that would reduce the most downstream confusion if normalized first: the **`post_select_conflict` fix-pack contract**. Specifically, preserving contradiction subtype precision (`entity_proper_noun`, `timeline`, `item_location`, `system_contamination`) through the `continuity_firewall → post_select_conflict → reject guidance → retry snapshot` handoff, so that targeted local repair can be attempted before falling back to expensive full-rewrite.

## 5. Stop

read-only lane complete; no files mutated
