## Stage 4 Target-Locked Patch Lane Full Survey

Date: 2026-03-28
Status: final (3-pass audited)
Track: system
Type: bounded full-survey
Topic Slug: stage4-target-locked-patch-lane
Audit Order: `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey-audit-order.md`

---

### 1. Scope and Intent

Central question:

`Can Stage 4 be made safer and more deterministic by enforcing a target-locked patch contract before any escalation logic is expanded?`

This survey is bounded to the Stage 4 patch lane. It does not redesign Stage 4 broadly.

This final audited version keeps the draft's core finding, but corrects one important overclaim:

- the live canaries were **not** zero-contamination provider baselines
- however they still expose a valid routing and contract bug in the Stage 4 patch lane

Primary operating interpretation:

- keep the `10` round ceiling for now
- stop fake patch lanes first
- treat escalation changes as follow-up work, not the first intervention

---

### 2. Evidence Sources

Primary code authority:

| File | Purpose |
|------|---------|
| `modules/core/stage4_retry_runtime.py` | Retry lane routing and patch/rewrite dispatch |
| `modules/core/stage4_interview_round.py` | fix_pack contract validation and retry generation path |
| `modules/core/stage4_reject_runtime.py` | reject bucket shaping and fix_scope mutation |
| `modules/core/stage4_outcome_runtime.py` | logic-like counting and escalation thresholds |
| `modules/domain/agents/chief_writer.py` | `patch_with_feedback()` and `inplace_patch()` implementation |
| `modules/domain/agents/chief_writer_inplace_local_ops.py` | deterministic local-op edit lane |
| `config/settings/stage4_policy_digest.json` | Stage 4 policy overrides |
| `config/settings/validation.yaml` | retry ceiling and patch thresholds |

Primary test authority:

| File | Relevance |
|------|-----------|
| `tests/test_stage4_interview_round.py` | Existing retry/patch routing expectations |
| `tests/test_stage4_orchestrator.py` | Stage 4 retry policy coverage |
| `tests/test_chief_writer_inplace_local_ops.py` | deterministic local patch lane coverage |

Primary live evidence:

| Project | Use |
|---------|-----|
| `projects/canary_0328_golden_s4_shadow` | Main live reproduction of repeated Stage 4 patch-lane failure |
| `projects/canary_0328_golden_new2_s4` | Corroborating live reproduction of the same failure fingerprint |

Supporting evidence only:

| Project | Use |
|---------|-----|
| `projects/canary_0328_golden_new_s4` | Shows that higher repair lanes can fire in some runs; not proof that blueprint repair was required in the shadow run |

---

### 3. Current Routing Map

#### 3.1 Master router

Function:

- `modules/core/stage4_retry_runtime.py:831-912`

The relevant routing truth is:

1. Lane 1 `inplace_local_repair`
- requires `fix_scope == "inplace"`
- requires `fix_pack_contract.ready == True`
- dispatches to `chief_writer.inplace_patch(...)`

2. Lane 2 `patch_revision`
- can activate when `fix_scope in ("inplace", "partial")`
- can also activate in certain `post_select_conflict` paths
- does **not** require `fix_pack_contract.ready == True`
- dispatches to `chief_writer.patch_with_feedback(...)`

3. Lane 3 `rewrite_regenerate`
- activates when Lane 1 and Lane 2 do not produce candidates
- dispatches to `chief_writer.regenerate_with_feedback(...)`

Critical code lines:

- `modules/core/stage4_retry_runtime.py:881-889`
- `modules/core/stage4_retry_runtime.py:997-1018`
- `modules/core/stage4_retry_runtime.py:1037`

#### 3.2 Proven routing gap

The most important routing defect in this survey:

- `use_inplace` checks `fix_pack_contract.get("ready")`
- `use_patch` does not

This means Stage 4 can label a retry as `patch_revision` and call `patch_with_feedback(...)` even when:

- `fix_pack = {}`
- `fix_pack_reason = "missing_fix_pack"`
- no concrete patch targets exist

This is the fake patch lane.

#### 3.3 Existing regression anchor

There is already a test that shows missing fix-pack can still route to patch:

- `tests/test_stage4_interview_round.py:3204`
- `test_retry_inplace_requires_fix_pack_and_routes_to_patch`

That test is currently useful as a regression anchor, but it also confirms the gap.

---

### 4. Fix-Pack Contract Truth Table

#### 4.1 Contract readiness

Function:

- `modules/core/stage4_interview_round.py:1698-1715`

`fix_pack_contract.ready` is false when any of the required fields are missing.

Required readiness inputs:

| Field | Needed for ready |
|-------|------------------|
| `patch_targets` | Yes |
| `must_fix` | Yes |
| `do_not_regress` | Yes |
| `success_condition` | Yes |
| `target_kind` | Yes and must be valid |

Observed failure reasons include:

| Reason | Meaning |
|--------|---------|
| `missing_fix_pack` | fix_pack absent or empty |
| `missing_patch_targets` | no concrete targets |
| `missing_must_fix` | no explicit must-fix list |
| `missing_do_not_regress` | no regression guard |
| `missing_success_condition` | no success definition |

#### 4.2 Enforcement asymmetry

The contract is enforced in some places and bypassed in others.

| Surface | Contract enforced? |
|---------|--------------------|
| PASS_WITH_FIX entry | Yes |
| Inplace retry lane | Yes |
| Reject-side inplace downgrade | Yes |
| Lane 2 `patch_revision` entry | No |

This asymmetry is why the system can reject a non-ready fix_pack for true inplace editing, but still accept it for the pseudo-patch lane.

#### 4.3 Practical implication

The contract today answers:

- "Can we do deterministic/local editing?"

It does **not** answer:

- "Should we still call something patch if there is nothing concrete to patch?"

That missing answer is the bug.

---

### 5. Patch Semantics Map

#### 5.1 `inplace_patch()`

Relevant surfaces:

- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_inplace_local_ops.py`

Current semantics:

| Path | Real behavior |
|------|---------------|
| deterministic local-op lane | true local edit with Python-applied replace operations |
| fallback `inplace_patch` lane | constrained rewrite, not deterministic patching |

So `inplace_patch()` is now mixed:

- best case: true local edit
- fallback case: constrained rewrite

#### 5.2 `patch_with_feedback()`

Function:

- `modules/domain/agents/chief_writer.py:1907-1955`

Current semantics:

- builds a patch-style prompt
- then calls `generate_ensemble(...)`
- uses `single_strategy=<previous selected strategy>`

So this is **not** true patching.

Correct classification:

- bounded regeneration

#### 5.3 Semantic mismatch

The router treats Lane 2 as a patch lane.
The implementation treats Lane 2 as bounded regeneration.

That mismatch becomes dangerous when Lane 2 is allowed to run without a ready fix_pack contract.

---

### 6. Failure Taxonomy

#### 6.1 Categories used in this survey

| Category | Meaning |
|----------|---------|
| A. Target-locked contract failure | fix_pack is empty or unusable, so no concrete edit target exists |
| B. Patch-lane routing failure | system still chooses a patch-labeled lane despite non-ready contract |
| C. Escalation candidate | a higher repair lane may be warranted, but this is not proven as the first move |
| D. Provider contamination | provider-side failures contaminate interpretation of live runs |

#### 6.2 What the live canaries actually prove

Both live canaries repeatedly show:

- `error_category = "QUALITY_ISSUE"`
- `reject_bucket = "quality_issue"`
- `fix_pack_reason = "missing_fix_pack"`
- `score = 50`
- `firewall_triggered = false`
- `escalation = "none"`

That is strong evidence for:

- A. target-locked contract failure
- B. patch-lane routing failure

It is only partial evidence for:

- C. escalation candidate

because the runs did not prove that blueprint repair was the first correct answer; they only proved the current patch lane was wrong.

#### 6.3 Provider caveat

The draft version claimed zero provider failures in the live canaries. That was incorrect.

Observed in:

- `projects/canary_0328_golden_s4_shadow/logs/session/llm_io.jsonl`
- `projects/canary_0328_golden_new2_s4/logs/session/llm_io.jsonl`

Observed failure class:

- Anthropic `invalid_request_error`
- low-credit / unavailable call failures

Therefore:

- the live canaries are not clean zero-contamination baselines
- policy-superiority claims must stay conservative

But the core bug claim survives, because the persistent Stage 4 sink data still shows the same empty-fix-pack patch loop.

---

### 7. Live Canary Interpretation

#### 7.1 `canary_0328_golden_s4_shadow`

Main signals:

1. repeated `score = 50`
2. repeated `fix_pack_reason = "missing_fix_pack"`
3. repeated `QUALITY_ISSUE`
4. repeated `patch_revision`
5. no `firewall_triggered`
6. `shadow_clipped = true`

Interpretation:

- this run is useful as a bug reproduction
- it is not a clean proof that the round ceiling should change
- it does show that Stage 4 stayed in the wrong repair lane

#### 7.2 `canary_0328_golden_new2_s4`

Main signals:

- reproduced the same `missing_fix_pack` plus `patch_revision` loop
- reached `stage4_retry_shadow_compare`
- ended with `final_result = "SKIP"`
- recorded `shadow_clipped = true`
- did not advance into a useful multi-episode comparison

Interpretation:

- useful corroboration of the same bug
- weak as a superiority experiment

#### 7.3 IFC / escalation reading

The live sinks show IFC-style advisory text in `fix_scope_reasoning`, while:

- `error_category` stays `QUALITY_ISSUE`
- `firewall_triggered` stays false

Relevant code:

- `modules/core/stage4_outcome_runtime.py:596-613`
- `modules/core/stage4_outcome_runtime.py:806-819`

What is proven:

- current escalation counting is centered on logic-like classification
- the shadow/new2 runs did not bridge from `QUALITY_ISSUE` into that logic-like path

What is **not** yet proven:

- that IFC reclassification should be the first code change

The safer read is:

- fix the fake patch lane first
- investigate IFC-to-escalation bridging second

---

### 8. Recommended Bounded Next Step

#### 8.1 Preferred operating conclusion

The evidence supports this operating conclusion:

`keep the 10-round ceiling, but forbid fake patch lanes and strengthen target-locked obedience before touching escalation`

This matches the strongest proven defect with the smallest blast radius.

#### 8.2 Ranked bounded options

1. **Fail-closed Lane 2 gate on a ready fix_pack contract**
- block `patch_revision` unless `fix_pack_contract.ready == True`

2. **Narrow the `patch_with_feedback()` contract**
- if it remains in the system, treat it honestly as bounded regeneration
- do not let it run under a patch label when no concrete targets exist

3. **Add explicit regression coverage**
- expand the retry test surface around `tests/test_stage4_interview_round.py:3204`
- assert that empty fix_pack no longer silently qualifies for normal patch routing

4. **Follow-up investigation only: IFC-to-logic-like bridge**
- after fake patch lanes are fixed, evaluate whether IFC-style `QUALITY_ISSUE` rounds should count toward escalation

#### 8.3 Smallest safe implementation

The smallest safe implementation is:

- add a readiness gate to Lane 2 in `modules/core/stage4_retry_runtime.py:889-902`

Conceptually:

```text
Before:
  use_patch may activate with fix_scope in ("inplace", "partial")
  even when fix_pack_contract.ready is false

After:
  use_patch requires fix_pack_contract.ready == true
```

This directly closes the proven contract gap.

#### 8.4 Not recommended as first move

Do not make these the first patch:

- lower the round ceiling
- tune V75-D thresholds
- force earlier blueprint escalation

Those moves change behavior more broadly than the evidence justifies.

---

### 9. Open Questions

1. Why does Director-side fix_pack generation fail completely on these arcs?

2. Is there a narrower minimum contract for Lane 2 than full `ready == true`, or should Lane 2 require full readiness?

3. Should `patch_with_feedback()` be renamed to reflect bounded regeneration semantics?

4. Should IFC-style advisories inside `QUALITY_ISSUE` count as logic-like for escalation purposes?

5. If Lane 2 is fail-closed, what is the right non-patch fallback:
- rewrite-regenerate
- explicit skip to higher repair lane
- or a separate fact-patch lane

---

### 10. Confidence

| Finding | Confidence | Basis |
|---------|------------|-------|
| Lane 2 does not check fix_pack readiness | High | Direct code inspection in `stage4_retry_runtime.py:881-889` |
| `patch_with_feedback()` is bounded regeneration, not true local patching | High | Direct code inspection in `chief_writer.py:1907-1955` |
| Live canaries expose a real routing/contract failure | High | Repeated `missing_fix_pack` + `patch_revision` + flat `score=50` in Stage 4 sinks |
| Live canaries are provider-contaminated, not clean baselines | High | `llm_io.jsonl` contains Anthropic low-credit / invalid-request failures |
| IFC-style advisory appeared while escalation stayed off | High | `runtime_audit.jsonl` and `episode_production.jsonl` both show this pattern |
| `QUALITY_ISSUE` likely bypasses current logic-like escalation counting | Medium-High | Direct code plus sink data, but no dedicated IFC bridge exists yet |
| Fail-closed Lane 2 gating is the safest first code move | Medium-High | Smallest change that directly addresses the proven gap |
| Blueprint repair is already proven to be the right first answer for the shadow/new2 runs | Low | Not established by the current evidence |

