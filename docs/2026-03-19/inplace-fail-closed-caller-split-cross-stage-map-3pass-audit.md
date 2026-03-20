# inplace-fail-closed-caller-split-cross-stage-map-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/inplace-fail-closed-caller-split-cross-stage-map-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 115`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/inplace-30kb-fallback-consistency-3pass-audit.md`
- `docs/2026-03-19/blueprint-inplace-30kb-fallback-consistency-3pass-audit.md`
- `docs/2026-03-19/stage3-blueprint-local-patch-routing-semantics-3pass-audit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage4_orchestrator.py`
- `tests/test_inplace_reliability.py`
- `tests/test_stage2_preflight.py`
- `tests/test_pass_with_fix.py`
- `tests/test_blueprint_patch_mode.py`
- `tests/test_v75b_escalation.py`
Scope:
- compress the current cross-stage semantics of local fail-closed `inplace` guards for Arc and Blueprint into one operator-facing map
- clarify where callers use same-attempt fallback, retry handoff, or bounded regeneration
- reduce ambiguity caused by OPUS-style over-compressed wording
- non-goal: redesign any patch policy or change runtime code in this document

---

## Pass 1. Structure and Scope

This note is intentionally comparative.

It covers only two local fail-closed families:
- Arc `_inplace_patch_arc()`
- Blueprint `_inplace_patch_blueprint()`

And only their immediate caller layers:
- Arc: `stage2_preflight`, `stage2_finalizer`
- Blueprint: `ThreePhaseBlueprintGenerator.generate()`, `Stage4Orchestrator` B-Light escalation

It does not cover:
- manuscript local patch policy
- Stage 4 hard guards for manuscript patching
- threshold retuning

Key operator question:
- when a local `inplace` patch path refuses input or fails, what does the next layer actually do, and where do Arc and Blueprint differ?

---

## Pass 2. Evidence and Consistency

### 1. Arc local guard and callers

Local contract:
- `_inplace_patch_arc()` is fail-closed at the function boundary
- oversized Arc JSON over `30KB` returns `None`

Caller split:
- `stage2_preflight`:
  `inplace 실패 -> 같은 시도 안에서 patch fallback`
- `stage2_finalizer`:
  `inplace 실패 -> REJECT -> retry`로 상위 루프에 위임

Meaning:
- the Arc local guard is stable
- the caller behavior is layer-dependent
- OPUS-style one-line summaries tend to hide this split

### 2. Blueprint local guard and callers

Local contract:
- `_inplace_patch_blueprint()` is also fail-closed at the function boundary
- oversized Blueprint JSON over `30KB` returns `None`

Caller split:
- `ThreePhaseBlueprintGenerator.generate()` initial retry path:
  `inplace 실패 -> 같은 시도 안에서 full rewrite fallback`
- `ThreePhaseBlueprintGenerator.generate()` `PASS_WITH_FIX` loop:
  `partial -> single-strategy regenerate`
  `full -> full regenerate`
  `F-2 high change_ratio -> warning-only`
- `Stage4Orchestrator` B-Light:
  `inplace 실패 -> bounded Blueprint regeneration 1회`

Meaning:
- Blueprint caller behavior is also layer-dependent
- but the split is still coherent once generation-layer and Stage 4 escalation-layer responsibilities are separated

### 3. The real pattern is "local fail-closed, caller fail-soft, but not uniformly"

Current live shape is not one universal ladder.

Accurate compression is:
- local `inplace` helpers are fail-closed
- callers decide whether fallback is:
  - same-attempt patch
  - same-attempt full rewrite
  - REJECT and outer retry
  - one bounded regeneration attempt

This is the important operator distinction.

The dangerous summary is:
- "`inplace` 실패 시 다음 단계로 자동 폴백"

Why that is unsafe:
- it is too vague
- it hides which layer owns the next action
- it encourages false assumptions that all repair lanes behave the same

### 4. Current safe map

Arc:
- local: fail-closed
- preflight: same-attempt patch fallback
- finalizer: REJECT -> retry

Blueprint:
- local: fail-closed
- Stage 3 initial retry: same-attempt full rewrite fallback
- Stage 3 `PASS_WITH_FIX`: `partial/full` regenerate routing, `F-2` warning-only
- Stage 4 B-Light: one-shot bounded regenerate

Conclusion:
- Arc and Blueprint are parallel in local guard philosophy
- they diverge at caller orchestration level
- that divergence is currently intentional enough to document, not flatten

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. The cross-stage truth is not "all inplace failures behave the same."

2. The correct operator mental model is:
- local helper = fail-closed
- caller layer = explicit fallback owner

3. OPUS confusion came mainly from compressing these owner-specific fallback paths into a single sentence.

### Safe operating rule from this audit

Do:
- describe fallback semantics per caller layer
- keep Arc and Blueprint local guard docs separate
- use this cross-stage map only as an operator compression layer

Do not:
- summarize Arc and Blueprint with one universal fallback ladder
- assume same-attempt fallback exists everywhere
- assume Stage 4 hard-guard semantics apply to Arc/Blueprint local patching

### Recommended next actions

1. When future summaries mention `inplace` fail-closed behavior, attach the caller layer explicitly.
2. Keep Stage 3 Blueprint routing and Stage 2 Arc caller split as separate regression-backed items.
3. If any layer is redesigned later, update this cross-stage map after the layer-specific doc changes first.

### Audit result

- runtime code change: not needed
- regression hardening: completed at the layer docs/tests
- documentation conclusion: local fail-closed `inplace` guards are stable, but caller fallback semantics are intentionally split by layer and must stay explicit
