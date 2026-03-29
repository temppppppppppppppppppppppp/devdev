# Stage4 Decision Contract Matrix Full Survey

Date: 2026-03-28
Status: final (3-pass audited)
Track: system
Type: bounded full-survey
Topic Slug: stage4-decision-contract-matrix

---

## 1. Intent

This survey maps the live Stage 4 decision contract across:

- Director prompt contract
- Director authoritative output
- runtime normalization
- retry routing
- escalation counting
- operator observability

The question is not "why did one canary fail?" It is:

> Which Stage 4 decision contracts are real, which are only assumed, and which mismatches can still create hidden failure families?

This document is survey-only. It is not a redesign spec.

---

## 2. Evidence Sources

### Primary Code Surfaces

- `config/prompts/director.yaml`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/llm_router.py`

### Prior Audited/Executed Stage4 Documents

- `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey.md`
- `docs/2026-03-28/stage4-ifc-bridge-full-survey.md`
- `docs/2026-03-28/why-fix-pack-is-empty-full-survey.md`
- `docs/2026-03-28/why-fix-pack-is-empty-execution-ssot.md`

### Live Canary Evidence

- `projects/canary_0328_golden_new2_s4/logs/episode_production.jsonl`
- `projects/canary_0328_golden_new2_s4/logs/runtime_audit.jsonl`
- `projects/canary_0328_stage4_ifc_bridge_check/logs/episode_production.jsonl`
- `projects/canary_0328_stage4_ifc_bridge_check/logs/session/ui_events.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/session/decisions.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/episode_production.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/session/ui_events.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/session/llm_io.jsonl`

### Latest Critical Observations

- `TF-PATCH-GATE` is working: non-ready `fix_pack` no longer enters the fake patch lane.
- the latest prompt tightening for `REJECT + fix_scope in {"inplace","partial"} -> fix_pack required` did not clear the family
- the newest canary shows the upstream reason: authoritative Director decisions still emit blank `fix_scope`
- the same canary also shows a new seam: downstream pathology later reports `fix_scope="partial"` while authoritative decision sinks remain blank
- fallback observability is incomplete: failed Claude calls are visible, actual fallback-served Gemini calls are not coherently visible in the same sink surface

---

## 3. Current Decision Surface Map

```
director.yaml
  -> Director LLM raw JSON
  -> director_ensemble.py normalization
  -> stage4_director_runtime.py / stage4_interview_round.py gate semantics
  -> stage4_outcome_runtime.py reject/pass handling
  -> stage4_retry_runtime.py lane routing
  -> stage4_orchestrator.py round loop and escalation
```

Current field ownership is not cleanly separated:

| Layer | Field(s) | Observed behavior |
|------|----------|-------------------|
| Director prompt | `verdict`, `score`, `fix_scope`, `fix_pack` | contract exists but blank outputs still occur |
| Director authoritative decision sink | `fix_scope=""`, `repair_scope="none"`, `fix_pack={}` | latest canary rounds 0-3 |
| Retry pathology sink | later `fix_scope="partial"` | appears after IFC/retry shaping, not from authoritative decision |
| Retry routing | uses ready/non-ready contract and lane guards | fake patch lane now fail-closed |

This is the core survey finding:

> Stage 4 is no longer failing mainly because the patch lane was too permissive. It is now failing because authoritative decision fields and derived retry fields are not contractually aligned.

---

## 4. Already-Landed Controls

These are no longer open hypotheses.

### 4.1 TF-PATCH-GATE Landed and Proven

- `stage4_retry_runtime.py` now requires `fix_pack_contract.ready` before patch-style repair lanes
- canary evidence shows `[TF-PATCH-GATE] non-ready fix_pack -> patch blocked, rewrite used`
- conclusion:
  - the fake patch lane was real
  - it is now fail-closed
  - the remaining plateau is upstream of that gate

### 4.2 Narrow IFC Bridge Landed

- `stage4_outcome_runtime.py` now has a bounded bridge for IFC-shaped `QUALITY_ISSUE`
- the latest canary still showed `escalation=none`
- conclusion:
  - the bridge was worth landing
  - but this failure family did not satisfy the bridge conditions in a way that changed the run
  - therefore the remaining bottleneck is not "IFC bridge absent"

### 4.3 Prompt Tightening for REJECT-Side fix_pack Landed

- `director.yaml` now explicitly says `REJECT + fix_scope in {"inplace","partial"}` requires structured `fix_pack`
- latest canary still produced empty `fix_pack`
- authoritative decision sinks show why:
  - `fix_scope=""`
  - `repair_scope="none"`
  - `fix_pack={}`

Conclusion:

> The prompt tightening did not fail on a compliant `partial/inplace` row. It failed to fire because the upstream `fix_scope` row itself remained blank.

---

## 5. Confirmed Mismatch Inventory

### M-1. Authoritative `fix_scope` blank on REJECT blocks the repair contract

Confidence: HIGH

- prompt contract expects REJECT rows to still carry repair intent via `fix_scope`
- latest canary authoritative decision log shows:
  - `fix_scope=""`
  - `repair_scope="none"`
  - `fix_pack={}`
  - `gate_basis="director_primary_reject"`
- if `fix_scope` is blank, the new REJECT-side `fix_pack` mandate never triggers

Why it matters:

- `fix_pack empty` is no longer the deepest root cause
- the deeper root cause is that the authoritative decision row is incomplete before retry even begins

### M-2. Authoritative decision scope and derived retry scope drift apart

Confidence: HIGH

- `decisions.jsonl` keeps `fix_scope=""`
- later `episode_production.jsonl` pathology rows show `fix_scope="partial"`
- the same rows still show `repair_scope="none"` in authoritative decision entries

Interpretation:

- some downstream logic is effectively deriving or re-stamping scope-like meaning after the authoritative decision is already blank
- operators cannot tell whether `partial` came from the Director, a repair fallback, an IFC notice, or a contract-fail downgrade path

This is not just cosmetic. It breaks auditability.

### M-3. `missing_fix_pack` remains the dominant family, but it is now downstream of M-1

Confidence: HIGH

- five consecutive latest canary rounds stayed in `quality_issue|fix_pack:missing_fix_pack`
- after TF-PATCH-GATE, this no longer indicates a fake patch bug
- it now indicates that the authoritative decision failed to provide the minimum repair payload

This mismatch remains real, but the root-cause layer has moved up.

### M-4. Feedback snowball still creates a rejection spiral risk

Confidence: HIGH

- `retry_directives`, plateau advisories, TF-29 advisories, IFC notices, and prior evidence continue to accumulate across rounds
- latest UI evidence still shows layered historical warnings being prepended into later rounds

Interpretation:

- this does not directly prove that Python hard-rejects on dialogue ratio or style warnings
- it does prove that the Director receives increasingly negative context
- this remains a structural plateau amplifier even after patch-gating

### M-5. Fallback observability gap remains open

Confidence: HIGH

- `llm_io.jsonl` in the latest canary records Anthropic 400 failures only
- the same run's `episode_production.jsonl` records Gemini model token/cost breakdown
- therefore the sink surface is incomplete:
  - failed primary attempts are visible
  - successful fallback-served attempts are not coherently attributable in the same operator evidence path

This is an observability mismatch, not the proven root cause of the plateau. But it materially weakens canary interpretation.

### M-6. Narrow IFC bridge is partially correct but insufficient for this family

Confidence: MEDIUM-HIGH

- the code now supports a bounded IFC logic-like bridge
- latest canary still stayed in `escalation=none`
- evidence suggests the conjunction required by the bridge did not line up on the same rounds as the strongest IFC signal

Interpretation:

- not a rollback candidate
- not a proof that the bridge was wrong
- but not sufficient to close the current family

---

## 6. Non-Mismatches or Lower-Risk Observations

### O-1. TF-PATCH-GATE itself is not the current problem

- it is working
- it exposed the upstream defect family rather than creating it

### O-2. "Python advisory became hard reject today" is not supported by current evidence

- current failures still enter through `director_primary_reject`
- the latest evidence supports negative priming and scope-contract mismatch
- it does not support a new Python hard gate on dialogue ratio or style warnings

### O-3. Provider contamination matters, but it does not explain the whole family

- a Gemini-only rerun is still needed for clean interpretation
- however, provider contamination alone does not explain:
  - blank authoritative `fix_scope`
  - later derived `partial`
  - continued `missing_fix_pack`

---

## 7. Updated Operating Conclusions

### 7.1 The "decision-contract matrix" framing is still correct

The latest canary strengthened this, not weakened it.

Before the recent harness work:

- fake patch behavior masked the contract defect

After the recent harness work:

- fake patch was blocked
- REJECT-side fix-pack prompt tightening was added
- the pipeline still failed
- the remaining defect surfaced as `authoritative fix_scope blank`

That is exactly a contract-matrix problem.

### 7.2 The highest-risk remaining row is no longer `fix_pack` alone

The highest-risk row is now:

`verdict x authoritative fix_scope x required repair payload`

Why:

- `fix_pack` cannot be made reliable if the scope row that should trigger it is blank
- downstream `partial` evidence is not authoritative and should not be treated as if it were

### 7.3 Clean Gemini-only canary is still needed, but after the right setup

A clean rerun should:

- use Gemini Developer API only
- not touch Vertex
- not attempt Claude first
- preserve raw evidence for authoritative decision fields

But a clean rerun should validate the next fix. It should not substitute for the missing contract work.

---

## 8. Recommended Harness Priorities

### Priority 1. Authoritative `verdict x fix_scope` contract

Make the Director contract explicit and testable:

- REJECT must emit non-empty `fix_scope`
- PASS_WITH_FIX must emit non-empty `fix_scope`
- allowed enum remains bounded
- blank scope becomes an explicit contract violation, not silent drift

### Priority 2. Authoritative-vs-derived scope separation

Stop overloading one `fix_scope` label across different layers.

At minimum, operator evidence must distinguish:

- authoritative Director `fix_scope`
- derived retry or fallback repair scope

### Priority 3. Prompt/runtime consistency assertions

Lock these rows with tests:

- REJECT local-scope rows require scope + payload
- authoritative blank-scope decisions are surfaced as violations
- runtime does not silently rebrand blank authoritative scope as if it were Director-authored

### Priority 4. Fallback observability

Make fallback-served calls attributable in operator sinks.

This is not the next repair-policy change, but it is the next evidence-quality change.

### Priority 5. Feedback windowing

Still valid, but no longer the first move.

It remains a likely plateau amplifier, not the strongest newly confirmed contract break.

---

## 9. Recommended Next Execution Slice

The safest next implementation wave is:

1. tighten authoritative `fix_scope` emission rules
2. surface explicit `fix_scope` contract violations
3. separate authoritative scope from derived retry scope in logs/evidence

Deferred from this wave:

- global escalation redesign
- round ceiling changes
- broad lane-transition refactor
- fallback-system redesign
- feedback-windowing rollout

---

## 10. Confidence

### Section Confidence

- evidence inventory: HIGH
- patch-gate conclusion: HIGH
- authoritative blank `fix_scope` conclusion: HIGH
- authoritative-vs-derived scope drift: HIGH
- fallback observability gap: HIGH
- feedback snowball as plateau amplifier: HIGH
- IFC bridge insufficiency interpretation: MEDIUM-HIGH

### Overall Confidence

Estimated confidence: `97%`

Why this is above the final-save threshold:

- the newest canary did not weaken prior findings
- it added a sharper upstream seam
- the proposed next move is narrower than the draft survey's original priority list
- no newer evidence contradicts the contract-matrix framing

---

## 11. 3-Pass Audit Record

### Pass 1. Structure and Scope

- removed stale framing that treated M-1 as only a REJECT-side fix-pack problem
- updated the survey to the current workspace state after patch-gate, IFC bridge, and prompt tightening
- PASS

### Pass 2. Evidence and Causality

- latest canary evidence re-checked against:
  - `decisions.jsonl`
  - `episode_production.jsonl`
  - `ui_events.jsonl`
  - `llm_io.jsonl`
- causal ordering updated to:
  - authoritative blank scope
  - downstream drift
  - continuing empty repair payload
- PASS

### Pass 3. Actionability and Overclaim Control

- separated confirmed mismatches from observations
- kept provider contamination as a caveat, not a universal explanation
- narrowed the next execution wave to the highest-risk remaining contract row
- PASS
