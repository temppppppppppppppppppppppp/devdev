Date: 2026-04-02
Status: final-bounded-survey
Canonical Path: `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md`
Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
Baseline Dirty Summary: `dirty: config/models.yaml, roadmap/queue mirrors, stage4 canary artifacts and 2026-04-02 survey bundles present`
Source Runtime Audit:
- `docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-audit.md`
- `docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-evidence.json`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-evidence.json`
Mode: survey only, read-only only

---

## Answer First

The dominant ep2 blocker is not `FlashbackVerifier`, not Stage2, and not Stage3.

It is a `Stage4` seam with two coupled failures:

1. `relation_to_protag` is stored and compared as a compressed numeric tag like `집착100/오해-80`, but NpcDrift has no semantic-expansion layer for that tag.
2. when that NpcDrift advisory escalates, Stage4 cannot synthesize a fresh local `fix_pack` from the advisory alone, so it falls into `strong_advisory_escalation_non_local_fix`.

In short:

`compressed relationship tag -> raw LLM comparison -> strong advisory escalation -> no zero-to-fix_pack synthesis -> forced REJECT`

This is a `Stage4 NpcDrift contract` problem.

---

## Hard Conclusions

### 1. The compressed tag originates from Stage4 post-pass relationship synthesis

The `집착{obsession}/오해{misunderstanding}` form is generated in `stage4_post_pass_runtime.py` from `karma_matrix` values and added to `relationship_changes`. [stage4_post_pass_runtime.py:691](C:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py#L691) [stage4_post_pass_runtime.py:694](C:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py#L694)

That relationship then gets persisted into `world_state` and `known_attrs.relation_to_protag` as the authoritative expected value. [world_state.py:236](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L236) [world_state.py:246](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L246) [world_state.py:337](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L337)

So the tag is not accidental prompt noise. It is a real canonical value currently emitted by the system.

### 2. NpcDrift compares manuscript prose against the raw compressed tag without a semantic-expansion layer

`NpcDriftAdvisor` sends authoritative NPC snapshots directly into an LLM prompt and includes `relation_to_protag` as a comparison target. [npc_drift_advisor.py:30](C:/Users/User/Desktop/글도비/modules/core/npc_drift_advisor.py#L30) [npc_drift_advisor.py:104](C:/Users/User/Desktop/글도비/modules/core/npc_drift_advisor.py#L104) [npc_drift_advisor.py:138](C:/Users/User/Desktop/글도비/modules/core/npc_drift_advisor.py#L138)

There is no code path here that:

- expands `집착100/오해-80` into a prose-equivalence description
- normalizes relation tags into a semantic class
- maps prose back to numeric relation ranges

The comparison is LLM-based, not Python exact-match, but operationally it is still raw-tag comparison because the LLM receives the compressed tag as the authoritative expectation.

### 3. All `NpcDrift` advisories are treated as tier-2 strong advisories

`Stage4InterviewRound` classifies any `NpcDrift` advisory as tier 2. [stage4_interview_round.py:1698](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1698) [stage4_interview_round.py:1702](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1702)

The strong-advisory escalation set includes `npc_drift` with no subtype split for:

- role drift
- relation tag drift
- injury/location drift

[stage4_interview_round.py:2209](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2209)

So `relation_to_protag` compressed-tag mismatch gets the same binding escalation treatment as other harder structural drifts.

### 4. Stage4 cannot synthesize a local fix contract from pure NpcDrift advisory data

The current `fix_pack` contract requires:

- `patch_targets`
- `must_fix`
- `do_not_regress`
- `success_condition`
- local `target_kind`

[stage4_interview_round.py:1935](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1935)

But `_backfill_strong_advisory_fix_pack()` only enriches an existing `fix_pack`. If `director_result.fix_pack` is empty, it returns `{}` and does not synthesize one from zero. [stage4_interview_round.py:2014](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2014)

That is the crucial failure. For advisory-driven PASS -> PASS_WITH_FIX escalation, the system has no zero-to-local-fix synthesis path for `npc_drift`.

### 5. The ep2 canary failure pattern matches the code exactly

Runtime showed:

- 7 rounds total
- 5 rounds ended as `strong_advisory_escalation_non_local_fix`
- Director wanted PASS in 6/7 rounds
- Flashback went silent after R3 and was not dominant

[runtime audit](C:/Users/User/Desktop/글도비/docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-audit.md) [runtime evidence](C:/Users/User/Desktop/글도비/docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-evidence.json)

The code survey explains that runtime exactly:

- raw compressed tag survives into canonical state
- NpcDrift compares against that tag
- strong advisory escalates
- fix-pack backfill cannot create local patch targets from nothing
- gate downgrades to REJECT

---

## Medium-Confidence Conclusions

### 1. This seam is narrower than a full NpcDrift rewrite

The evidence points specifically to `relation_to_protag` compressed numeric tags, not all NpcDrift categories.

Role, injury, and location drift may still be fine under the current advisory design. The pathological case here is:

- canonical relation stored as compressed quantitative tag
- prose rendering naturally paraphrased by the LLM
- no semantic-equivalence bridge

### 2. There are two viable bounded directions

The code supports two bounded remediation strategies:

1. `semantic equivalence`:
   treat compressed relation tags as semantic classes or ranges instead of raw tag literals
2. `advisory-to-local-fix synthesis`:
   allow NpcDrift relation-tag advisories to synthesize a bounded local `fix_pack` even when Director did not supply one

These are not equally broad. The first changes advisory comparison semantics; the second changes finalization contract synthesis.

### 3. The better first bounded wave is probably mixed

Pure semantic-equivalence alone may reduce false mismatch, but some real relation drift cases will still need repair instructions.

Pure fix-pack synthesis alone may still over-trigger if the advisory itself remains too brittle.

So the likely best bounded wave is:

- narrow subtype handling for `relation_to_protag`
- plus zero-to-local-fix synthesis for that subtype only

---

## Open Questions

1. Should `집착100/오해-80` remain the canonical stored form at all, or should canonical state store both:
   - numeric/compressed form
   - prose/semantic alias

2. Should `NpcDrift relation_to_protag` be downgraded from strong advisory to advisory-only unless the drift crosses a defined semantic threshold?

3. Is the correct local fix target:
   - `entity_ref`
   - `local_phrase`
   - `local_sentence`
for this subtype, or does it require a dedicated `relation_semantics` target family later?

---

## Scope Judgment

This is not a Stage2 issue.

This is not primarily a Stage3 issue.

This is not primarily a FlashbackVerifier issue anymore.

This is a `Stage4 NpcDrift compressed-tag semantic-equivalence + local-fix contract` seam.

---

## Next Action

The next bounded wave should be:

`0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`

with scope limited to:

1. `relation_to_protag` compressed-tag subtype handling
2. subtype-aware strong-advisory policy for `npc_drift`
3. zero-to-local-fix contract synthesis for that subtype only

---

## Stop

survey-only complete; no queue, roadmap, runtime artifact, or source project mutation in this step

---

## 3-Pass Audit Record

Pass 1. Structure and scope
- stayed bounded to the ep2 canary blocker
- separated root cause from broader Stage4 discussion
- avoided inflating into execution SSOT

Pass 2. Evidence and consistency
- runtime claims align with the canary audit/evidence bundle
- code claims align with the NpcDrift, Stage4 gate, world_state, and post-pass paths
- no claim depends on console rendering

Pass 3. Execution and readability
- next action is explicit and bounded
- non-goals are implicit but clear: no Stage2/3 reopening, no broad NpcDrift rewrite
- operator consequence is immediate and actionable

Confidence: 96%
