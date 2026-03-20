# TypedDict Helper Payload Live Re-Audit

Date: 2026-03-20
Status: completed
Canonical Path: `docs/2026-03-20/typed-dict-helper-payload-live-reaudit-3pass-audit.md`
Related Hint:
- `docs/2026-03-20/TF-static-complexity-audit.md` (low-trust static hint only)
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: ongoing stage/smoke/doc/project churn, low-trust intake bundle, prior closed decomposition tranche`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose
- Re-check whether `TypedDict` introduction is worth opening as a bounded execution queue.
- Reject repo-wide typing expansion and keep scope at high-ROI dict-heavy helper boundaries.

## 2. Live Findings
- No `TypedDict` definitions are present in `modules/` or `tests/`.
- `pyproject.toml` has `ruff` only; no `mypy` or `pyright` contract is active.
- The strongest immediate payoff is not raw LLM payload typing, but internal helper result payload typing in recently decomposed coordinator surfaces.

## 3. Why This Is Action-Bearing
- Recent long-function decomposition created stable helper boundaries.
- Those helpers still return plain `dict` and carry action strings, ready flags, counters, staged context fragments, or persistence-tail payloads.
- These are the narrowest places where `TypedDict` can improve:
  - key drift detection
  - branch readability
  - editor completion
  - follow-on refactor safety

## 4. What Not To Do
- do not open repo-wide `TypedDict` migration
- do not type raw blueprint/manuscript/LLM JSON surfaces first
- do not add a mandatory static checker gate in the same tranche
- do not change runtime semantics or payload shapes in this tranche

## 5. Recommended Shape
- introduce same-file `TypedDict` definitions near the relevant helpers
- type helper return payloads first
- keep input payloads mostly as `dict` unless the output contract is already stable
- treat static checking as report-only follow-up, not this tranche's prerequisite

## 6. Candidate Lanes
- Stage 2 finalizer helper payloads
- Stage 2 orchestrator helper payloads
- Stage 4 context-builder helper payloads

## 7. Judgment
- open a bounded execution queue
- keep the tranche at helper-payload boundaries only
- require an aggregate roadmap because there are `3` independent but related items

## 8. Confidence
- pass 1:
  - typing baseline and toolchain rechecked
- pass 2:
  - helper-return hotspots rechecked in live code
- pass 3:
  - repo-wide migration path explicitly rejected
- estimated confidence:
  - `0.96`
