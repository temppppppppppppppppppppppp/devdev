# Why Fix Pack Is Empty — Full Survey

Date: 2026-03-28
Status: final (3-pass audited)
Track: system
Type: bounded full-survey
Topic Slug: why-fix-pack-is-empty
Audit Order: `docs/2026-03-28/why-fix-pack-is-empty-full-survey-audit-order.md`

---

## 1. Scope and Question

This survey answers one bounded question:

> Where does `fix_pack` become empty in Stage 4, and did today's contract-hardening / harness-like changes create that failure family or only expose it?

Included surfaces:

- `config/prompts/director.yaml`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `projects/canary_0328_golden_new2_s4/logs/`
- `projects/canary_0328_stage4_ifc_bridge_check/logs/`
- `projects/canary_0328_golden_new_s4/logs/`

Excluded:

- blueprint redesign
- retry ceiling changes
- IFC escalation redesign beyond what was already implemented
- canary runner redesign
- broader Director feedback-snowball remediation

This survey stops at root-cause ranking and a bounded next move. It does not enter realization code changes.

---

## 2. Evidence Basis

Primary failing evidence:

- `projects/canary_0328_golden_new2_s4/logs/runtime_audit.jsonl`
- `projects/canary_0328_golden_new2_s4/logs/session/llm_io.jsonl`
- `projects/canary_0328_stage4_ifc_bridge_check/logs/session/ui_events.jsonl`
- `projects/canary_0328_stage4_ifc_bridge_check/logs/episode_production.jsonl`

Comparison evidence:

- `projects/canary_0328_golden_new_s4/logs/runtime_audit.jsonl`

Code anchors checked during audit:

- `config/prompts/director.yaml`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`

Observability caveat:

- In the inspected failing canaries, `session/llm_io.jsonl` preserves failed Anthropic Director calls with `response=""`.
- The raw successful fallback decision payload was not available in the evidence inspected here.
- For this survey, the authoritative truth comes from parsed runtime sinks (`runtime_audit.jsonl`, `ui_events.jsonl`) and code, not from raw Director output text.

---

## 3. End-to-End Lifecycle Summary

| Stage | Location | What happens |
|------|------|------|
| Prompt contract | `config/prompts/director.yaml` | Defines `fix_scope`, `fix_pack`, verdict semantics |
| LLM parse | `director_ensemble.py` | Extracts Director JSON payload |
| Ensemble normalization | `director_ensemble.py` | `_normalize_fix_pack()` returns `{}` only when all meaningful fields are empty |
| Gate normalization | `stage4_interview_round.py` | Re-normalizes `fix_pack`, derives `repair_scope`, enforces PASS_WITH_FIX contract |
| Contract evaluation | `stage4_interview_round.py` | `ready=True` requires non-empty `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, and valid `target_kind` |
| Retry routing | `stage4_retry_runtime.py` | `TF-PATCH-GATE` blocks patch lane when `fix_pack_contract.ready != True` |
| Pathology logging | `stage4_outcome_runtime.py` | Records `fix_pack_reason` such as `missing_fix_pack` or `missing_patch_targets` |

Key audit result:

- `fix_pack` is not being emptied by retry routing.
- It is already empty, or contract-insufficient, before retry routing makes its decision.

---

## 4. Findings

### 4.1 Primary root cause: prompt-runtime contract mismatch

The strongest fix-pack mandate in `config/prompts/director.yaml` is tied to `PASS_WITH_FIX`, not to `REJECT`.

Prompt facts checked:

- `PASS_WITH_FIX` explicitly says `fix_scope="inplace"` plus structured `fix_pack` is mandatory.
- `REJECT` says repair is needed and should be classified by `fix_scope`.
- `[TF-25-02]` says scores below `90` must be `REJECT`.

Runtime facts checked:

- Stage 4 targeted repair lanes expect a ready `fix_pack` whenever the repair is local or bounded.
- `stage4_retry_runtime.py` now enforces that expectation instead of allowing fake patching.

Practical outcome:

- In the failing canaries, the Director keeps returning `score=50`, which keeps the verdict in `REJECT`.
- Under the current prompt contract, `REJECT` has weak or implicit `fix_pack` obligations.
- The runtime still expects a concrete `fix_pack` for local targeted repair.

This is the core mismatch:

> Prompt-side contract treats rich `fix_pack` as primarily a `PASS_WITH_FIX` artifact, while runtime-side repair logic expects it whenever `REJECT` still claims `inplace` or `partial` repair scope.

### 4.2 Empty fix_pack originates upstream of normalization

`director_ensemble.py` and `stage4_interview_round.py` both normalize fix packs with the same logic:

- if all meaningful fields are empty, normalization returns `{}`
- if any meaningful field survives, the dict is preserved

Comparison evidence matters here.

In `projects/canary_0328_golden_new_s4/logs/runtime_audit.jsonl` there are cases such as:

- `fix_pack_reason = "missing_patch_targets"`
- `fix_pack_ready = false`

That only happens when a non-empty fix pack survives normalization but still fails the readiness contract.

So:

- normalization is not the main cause of `missing_fix_pack`
- normalization is correctly preserving partial payloads when the Director emits them
- the failing canaries show the more upstream case: no meaningful payload survives at all

### 4.3 Today's fail-closed changes exposed the defect; they did not create it

Today's relevant changes were:

- `TF-PATCH-GATE` in `stage4_retry_runtime.py`
- `patch_with_feedback()` fail-closed contract narrowing
- narrow IFC bridge in `stage4_outcome_runtime.py`

What the failing canaries show after those changes:

- `projects/canary_0328_golden_new2_s4/logs/runtime_audit.jsonl` records repeated `quality_issue|fix_pack:missing_fix_pack`
- `projects/canary_0328_stage4_ifc_bridge_check/logs/session/ui_events.jsonl` records repeated:
  - `[TF-PATCH-GATE] non-ready fix_pack -> patch 차단, rewrite 경로 사용`
  - `[TF-29] '연출' 유형 REJECT N연속`

That is exposure, not creation.

Before the fail-closed gate, the system could still route into a patch-labeled lane without a ready contract. That fake patch lane acted as a noisy masker. Once the gate started blocking it, the real upstream defect became visible: the Director often had no usable fix-pack payload to begin with.

### 4.4 Secondary contributing factors

Two secondary factors remain relevant, but neither outranks the prompt-runtime mismatch.

First:

- failing canaries show `fix_scope=""` early, then `fix_scope="partial"` later, while `fix_pack_reason` stays `missing_fix_pack`
- that means the Director is willing to say "partial repair" without supplying the repair contract needed for it

Second:

- the comparison canary proves the Director can sometimes emit partial fix-pack structure
- but it often omits exactly the fields the runtime needs most: `patch_targets` and `must_fix`

So there are two separate failure bands:

1. `missing_fix_pack`
2. `missing_patch_targets` / contract-insufficient partial fix pack

The first is the current blocker. The second is the likely next defect family once the first is fixed.

---

## 5. Root-Cause Ranking

| Rank | Candidate | Judgment | Confidence |
|------|------|------|------|
| 1 | Director prompt only makes full `fix_pack` mandatory for `PASS_WITH_FIX`, while `TF-25-02` forces `REJECT` under 90 | Primary root cause | High |
| 2 | `REJECT + fix_scope in {inplace, partial}` is allowed without an equally explicit `fix_pack` requirement | Contributing contract contradiction | High |
| 3 | Director can emit some fix-pack structure but often misses `patch_targets` / `must_fix` | Secondary contributor | Medium |
| 4 | `_normalize_fix_pack()` strips valid payloads | Rejected | High |
| 5 | Today's harness-like changes created the empty-fix-pack bug | Rejected; they exposed it | High |

---

## 6. Recommended Bounded Next Step

The safest next move is:

> Tighten the Director prompt contract so that `REJECT + fix_scope in {"inplace", "partial"}` must also emit a fully structured `fix_pack`.

Why this is the right next step:

- it keeps "Python collects, LLM decides" intact
- it fixes the mismatch at the prompt boundary, not by adding more Python heuristics
- it does not lower the `90` score floor
- it does not redesign retry ceilings or escalation policy
- it directly targets the failure family that today's fail-closed change revealed

Not recommended as the first move:

- relaxing `fix_pack` readiness in Python
- lowering the score floor to make `PASS_WITH_FIX` easier
- retry ceiling tuning
- new blueprint escalation logic
- more canaries before the prompt contract is corrected

---

## 7. Answer To The Original Causality Question

Yes, the harness-like / fail-closed shift helped us find the defect.

But the accurate statement is:

> Today's contract-hardening did not create empty `fix_pack`. It removed the fake patch escape route that had been masking an older prompt-runtime contract mismatch.

That is why the new canary looked worse while still being diagnostically better.

---

## 8. Residual Open Questions

These remain open, but they do not block the bounded next step.

1. Are successful fallback Director raw responses intentionally not preserved, or only missing in these canaries?
2. Once the prompt is tightened, will the Director reliably fill all five required fields, or will the next dominant failure family become `missing_patch_targets`?
3. Is the repeated `score=50` a real assessment or a floor/default behavior in this failure band?

---

## 9. 3-Pass Audit Record

### Pass 1. Structure and Scope

- survey type matches the request
- included and excluded surfaces are explicit
- the document stays bounded to `fix_pack` lifecycle and causality
- PASS

### Pass 2. Evidence and Consistency

- canary log paths were re-checked
- prompt/runtime claims were re-matched against current code and prompt text
- the document now distinguishes:
  - `missing_fix_pack`
  - `missing_patch_targets`
  - fail-closed exposure versus bug creation
- overclaim about raw Director output was trimmed to the inspected evidence only
- PASS

### Pass 3. Execution and Readability

- the survey ends in one bounded next move
- non-goals are explicit
- the document is actionable without inflating into redesign
- PASS

Estimated confidence: `96%`

