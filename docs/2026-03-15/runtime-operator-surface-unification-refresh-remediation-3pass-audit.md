<!-- [완료] -->
# runtime-operator-surface-unification-refresh-remediation 3-Pass Audit

Date: 2026-03-15
Status: final
Canonical Follow-On: `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`
Temp Mirror Follow-On: `docs/temp/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `menu7 and backend-front lanes are now closed; OPUS project-scoped manuscript memo is excluded from the active queue`
Source Evidence:
- `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`
- `docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md`
- `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
- live source reads of `main_a.py`, `modules/core/services/ui_service.py`, `modules/core/studio_visualizer.py`, and `modules/core/services/project_service.py`

## 1. Intent
- Re-audit the active runtime/operator lane against the current workspace before any new patching.
- Confirm whether `TF-011` still represents action-bearing work after menu `7` and backend-front lanes were already realized.
- Decide whether the lane can proceed now with at least 95% confidence.

## 2. Pass 1. Scope And Structure
- The active lane is still correctly scoped:
  - included: `main_a.py`, `UIService`, `StudioVisualizer`, `ProjectService`, prompt-adjacent tests, and one prompt-authority architecture note
  - excluded: menu `7` Arc-count policy, desktop transport/reconnect, persistence finalization, and broad narrative/manuscript lanes
- The roadmap order is still coherent:
  - backend-front is already complete
  - runtime/operator remains the next active code lane
  - later manuscript-truth and residual TF follow-up lanes still depend on this prompt-surface cleanup by default
- The lane remains bounded:
  - this is no longer an emergency runtime repair lane
  - it is now a prompt-authority unification and documentation lane

Pass 1 judgment:
- pass

## 3. Pass 2. Live Evidence And Drift
- The core claim is still live in current source:
  - `main_a.py` still contains `11` raw `input(...)` sites
  - `modules/core/services/project_service.py` still contains `10` raw `input(...)` sites
  - `modules/core/services/ui_service.py` still contains one bounded fallback `input(...)`
  - `modules/core/studio_visualizer.py` still owns the two canonical `console.input(...)` surfaces (`menu()` and `prompt()`)
- Shared authority is only partial today:
  - `_get_int_input()` already delegates to `UIService`
  - destructive service prompts in `ProjectService` still bypass that shared authority
  - several `main_a.py` continuation/skip/pause prompts still bypass that shared authority
- Hidden telemetry is improved but not yet fully unified:
  - `StudioVisualizer.prompt()` emits `prompt` plus hidden `prompt_response`
  - `UIService.get_int_input()` emits hidden `[int_input_selected]`
  - direct raw prompts in `main_a.py` and `ProjectService` bypass both of those contracts
- One stale claim was found and bounded:
  - `docs/2026-03-15/codebase-global-post-remediation-uncertainty-contradiction-ledger.md` says bare `input()` calls in `main_a.py` are already zero
  - live source disproves that claim today, so the current lane must trust live code over that stale survey sentence

Pass 2 judgment:
- pass

## 4. Pass 3. Execution Readiness
- The lane is still actionable without widening scope:
  1. centralize `main_a.py` continuation/skip/pause prompts behind `UIService`
  2. inject the same prompt callbacks into `ProjectService`
  3. keep `UIService` as the shared authority for int/choice/confirm/pause semantics
  4. publish one architecture note that explains the prompt lifecycle across CLI and desktop broker mode
- The lane does not need to reopen desktop transport:
  - backend-front already closed prompt queueing, reconnect snapshot, and `getStatus` ownership
  - this lane can treat desktop prompt brokering as an external contract and only document how it fits the authority chain
- The lane is verifiable with bounded tests:
  - `UIService`
  - `StudioVisualizer`
  - `ProjectService`
  - FrontierLag prompt-path regressions

Pass 3 judgment:
- pass

## 5. Confidence And Save Gate
- Pass 1 structure and scope: pass
- Pass 2 live evidence and drift: pass
- Pass 3 execution readiness: pass
- Estimated confidence: `97%`
- Save decision: final save allowed
- Execution-start decision: proceed allowed

## 6. Audit Conclusion
- The active runtime/operator lane is still valid and should proceed now.
- The lane should be realized as a bounded prompt-authority consolidation plus one architecture note, not as another transport or persistence project.
- The strongest live defect is no longer menu `7` or desktop reconnect; it is the surviving raw prompt bypasses in `main_a.py` and `ProjectService`.
- The implementation should use live workspace evidence, not the stale post-remediation claim that `main_a.py` already has zero bare `input()` calls.

## 7. Post-Implementation Confirmation
- Landed:
  - `main_a.py` raw continuation/skip/pause prompts now route through `UIService`
  - `ProjectService` now accepts injected int/confirm/pause callbacks for the live runtime path
  - `UIService` now owns shared choice/confirm/pause helpers and emits fallback hidden `prompt_response` telemetry
  - `docs/2026-03-15/runtime-operator-prompt-authority-chain.md` now documents the CLI and desktop prompt lifecycle
- Verification result:
  - targeted py_compile passed
  - targeted pytest passed
- Closure decision:
  - the lane can be marked `closed` and removed from `docs/temp/`
