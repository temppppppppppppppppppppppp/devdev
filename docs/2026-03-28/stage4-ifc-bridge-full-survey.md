## Stage 4 IFC Bridge Full Survey

Date: 2026-03-28
Status: final (3-pass audited)
Track: system
Type: bounded full-survey
Topic Slug: stage4-ifc-bridge

---

### 1. Scope and Intent

Central question:

`After the fake patch lane is closed, should Stage 4 reclassify IFC-shaped QUALITY_ISSUE retries into the logic-like escalation path?`

This survey is intentionally narrow.

It does not redesign Stage 4 generally, and it does not reopen the prior wave's patch-lane decision.

This document exists to lock the decision boundary for the next wave before any new escalation code is touched.

---

### 2. Context From the Prior Wave

The prior wave established and realized one narrow correction:

- fake `patch_revision` entry with a non-ready `fix_pack` was a real contract bug
- that lane is now fail-closed
- the `10` round ceiling remains unchanged

The new question is different:

- not "should Stage 4 retry less?"
- but "when a retry remains classified as `QUALITY_ISSUE`, is there a narrow IFC-shaped subset that should still count toward logic-like escalation?"

This distinction matters because:

- the prior bug was a routing bug
- the current question is an escalation semantics question

---

### 3. Evidence Sources

Primary code authority:

| File | Relevance |
|------|-----------|
| `modules/core/stage4_outcome_runtime.py:589-614` | Current logic-like counting gate |
| `modules/core/stage4_outcome_runtime.py:616-664` | Plateau advisory injection |
| `modules/core/stage4_outcome_runtime.py:665-709` | TF-29 repeated-bucket advisory |
| `modules/core/stage4_outcome_runtime.py:757-838` | Escalation entry and threshold application |
| `modules/core/stage4_outcome_runtime.py:840-899` | Retry pathology payload and fingerprint fields |

Primary prior-wave authority:

| File | Relevance |
|------|-----------|
| `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey.md` | Canonical prior-wave reasoning |
| `docs/2026-03-28/stage4-target-locked-patch-lane-execution-ssot.md` | Canonical prior-wave execution boundary |

Primary live evidence:

| Artifact | Relevance |
|----------|-----------|
| `projects/canary_0328_golden_s4_shadow/logs/episode_production.jsonl` | Repeated `quality_issue|fix_pack:missing_fix_pack` pathology, plateau, IFC-style reasoning |
| `projects/canary_0328_golden_new2_s4/logs/runtime_audit.jsonl` | Corroborating Stage 4 pathology signals in the same family |

Primary regression anchors:

| File | Relevance |
|------|-----------|
| `tests/test_stage4_orchestrator.py:2590-2653` | Existing post-select logic-like classification tests |
| `tests/test_stage4_orchestrator.py:2242-2319` | Existing escalation threshold boundary tests |

---

### 4. Current Logic-Like Counting Truth

Relevant function:

- `modules/core/stage4_outcome_runtime.py:589-614`

Current rule:

1. `LOGIC_ERROR` always counts toward `logic_error_streak`
2. `post_select_conflict` can also count, if the policy toggle allows it
3. ordinary `QUALITY_ISSUE` does not count and resets the streak to `0`

That means the system today has only two recognized logic-like lanes:

- explicit `LOGIC_ERROR`
- optional `post_select_conflict` bridge

There is no existing bridge for IFC-shaped `QUALITY_ISSUE`.

---

### 5. What the Live Evidence Actually Shows

The canary evidence does not justify a global `QUALITY_ISSUE -> logic-like` reclassification.

It does show a narrower pattern:

1. repeated pathology fingerprint:
   - `quality_issue|fix_pack:missing_fix_pack`
2. repeated flat score:
   - `score = 50`
3. plateau signal:
   - `plateau_detected = true`
4. IFC-style reasoning appears in `fix_scope_reasoning`
   - `[IFC] ... local patch instead of rewrite ...`
5. escalation stays off:
   - `repair_scope = "none"`
   - `escalation = "none"`
6. `firewall_triggered = false`

Direct evidence:

- [episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0328_golden_s4_shadow/logs/episode_production.jsonl)

Observed rows include:

- round 1: `QUALITY_ISSUE` + `fix_pack_reason = missing_fix_pack`
- round 2: same fingerprint + `plateau_detected = true`
- round 3+: same fingerprint plus IFC wording in `fix_scope_reasoning`

This proves:

- some IFC-shaped retries are currently invisible to the logic-like counter

It does **not** prove:

- every `QUALITY_ISSUE` should escalate
- blueprint regeneration is already the correct first answer

---

### 6. Safe Interpretation

The safe interpretation is narrow.

What is supported:

- there exists a bounded subset of `QUALITY_ISSUE` retries that behaves like a logic-like failure family
- that subset is characterized by repeated same-fingerprint failure plus IFC/plateau signals

What is not supported:

- global reclassification of all `QUALITY_ISSUE`
- direct blueprint escalation on first IFC advisory
- round-ceiling reduction as the primary fix

This means the next wave should not be:

- `QUALITY_ISSUE => LOGIC_ERROR`

It should be:

- `narrow IFC bridge => contributes to logic_error_streak under bounded conditions`

---

### 7. Decision Options

#### Option A. Global `QUALITY_ISSUE` reclassification

Rejected.

Why:

- too broad
- would drag ordinary style/engagement/length failures into logic-like repair
- not supported by inspected evidence

#### Option B. Direct IFC -> blueprint escalation

Rejected as a first move.

Why:

- blueprint escalation remains higher-risk logic
- the current workspace does not yet prove that blueprint regeneration is the right first answer for these cases
- the user explicitly flagged blueprint escalation as not fully trusted yet

#### Option C. Narrow IFC bridge into `logic_error_streak`

Recommended.

Why:

- smallest change that reflects the new evidence
- preserves the current `10`-round ceiling
- preserves existing threshold semantics
- does not force immediate blueprint repair
- only makes repeated IFC-shaped failures eligible for existing higher lanes sooner

---

### 8. Recommended Bridge Shape

The survey recommends a bounded bridge, not a global category rewrite.

Candidate bridge signature:

1. `error_category == "QUALITY_ISSUE"`
2. `reject_bucket == "quality_issue"`
3. one of:
   - explicit IFC marker in `fix_scope_reasoning`
   - future explicit IFC flag, if the system later adds one
4. at least one persistence signal:
   - `plateau_detected == true`
   - or repeated same pathology fingerprint in the current episode
5. no global category mutation at sink level

Important operating constraint:

- the bridge should affect only `logic_error_streak` counting
- it should **not** directly rewrite `error_category`

That keeps the system honest:

- sinks still say `QUALITY_ISSUE`
- escalation logic can still treat a bounded subset as logic-like

---

### 9. Likely Implementation Surface For the Next Wave

Primary code surface:

- `modules/core/stage4_outcome_runtime.py:589-614`

Likely shape:

- extract a helper for IFC-shaped `QUALITY_ISSUE` detection
- let `_should_count_reject_as_logic_like(...)` return true for that narrow helper

Secondary surface:

- `modules/core/stage4_outcome_runtime.py:840-899`

This already carries enough retry-pathology information to support the bridge:

- `error_category`
- `reject_bucket`
- `fix_pack_reason`
- `plateau_detected`
- `fix_scope_reasoning`

This suggests no sink-schema change is required in the first bridge wave.

Primary test surface:

- `tests/test_stage4_orchestrator.py:2590-2653`
- `tests/test_stage4_orchestrator.py:2242-2319`

New regression anchors should prove:

1. repeated IFC-shaped `QUALITY_ISSUE` can increment `logic_error_streak`
2. plain `QUALITY_ISSUE` without the IFC bridge signature still resets to `0`
3. threshold behavior itself stays unchanged

---

### 10. Excluded From This Decision

This survey explicitly excludes:

- lowering `retry.director_max_attempts`
- tuning V75-D thresholds
- tuning V75-B thresholds
- direct blueprint regeneration forcing
- sink-schema migration
- provider fallback redesign
- rewriting the TF-29 advisory family

Those are separate decisions.

---

### 11. Recommended Next Path

The next path should be:

1. write a bounded execution SSOT for `stage4-ifc-bridge`
2. keep the scope to a narrow bridge in `_should_count_reject_as_logic_like(...)`
3. add only the minimum tests needed to prove:
   - IFC-shaped repeated `QUALITY_ISSUE` can count
   - ordinary `QUALITY_ISSUE` still does not count
4. defer canary until after those tests pass

Operational summary:

`next wave = IFC bridge only`

not:

`next wave = escalation redesign`

---

### 12. Confidence

| Finding | Confidence | Basis |
|---------|------------|-------|
| Current logic-like counting excludes ordinary `QUALITY_ISSUE` | High | Direct code inspection in `stage4_outcome_runtime.py:589-614` |
| Existing bridge logic is limited to `LOGIC_ERROR` and optional `post_select_conflict` | High | Direct code inspection plus existing tests at `tests/test_stage4_orchestrator.py:2590-2653` |
| Live canaries show repeated `quality_issue|fix_pack:missing_fix_pack` with plateau and IFC wording | High | Direct log inspection in `projects/canary_0328_golden_s4_shadow/logs/episode_production.jsonl` |
| The evidence supports a narrow IFC bridge more than a global reclassification | Medium-High | Code + logs align, but no dedicated bridge exists yet |
| Direct blueprint escalation is already justified as the first next move | Low | Not established by inspected evidence |

---

### 13. 3-Pass Audit Record

#### Pass 1. Structure and Scope

- document type matches the current request: bounded survey for the next Stage 4 decision
- included and excluded surfaces are explicit
- the document is narrow enough to avoid reopening the prior patch-lane wave
- PASS

#### Pass 2. Evidence and Consistency

- core claims are tied to inspected code, tests, and live Stage 4 sinks
- no global `QUALITY_ISSUE` overclaim is made
- prior-wave context is carried forward without contradicting the realized patch-lane fix
- PASS

#### Pass 3. Execution and Readability

- the document points to a single next wave
- the recommended change shape is actionable
- guardrails prevent accidental escalation redesign scope creep
- PASS

Estimated confidence: `96%`
