<!-- [완료] -->
# Menu7 Desired Arc Input Contract Remediation 3-Pass Audit

Date: 2026-03-15
Status: final
Canonical Follow-On: `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
Temp Mirror Follow-On: `docs/temp/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: harness/test edits plus unrelated investment/style/pdf/log artifacts and untracked projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `menu7 interactive desired-total prompt landed in main_a.py with targeted FrontierLag test refresh and harness regression retention`
Source Evidence:
- `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-evidence.txt`
- `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
- `main_a.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`
- `tests/test_auto_frontier_lag_harness.py`
- `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
- `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`

## 1. Intent
- Re-audit the realized menu `7` execution item after implementation.
- Confirm that the delivered behavior matches the compact SSOT contract: one prompt at entry, desired-total semantics, immediate start, and prompt-free harness bypass.
- Close the item honestly with bounded verification evidence and explicit residual risk notes.

## 2. Pass 1. Structure And Scope
- Document type is correct:
  - this is a post-implementation 3-pass audit for a compact execution SSOT
- Scope is explicit:
  - included: menu `7` Arc-count prompt contract, requested-limit mapping, targeted FrontierLag tests, harness bypass behavior, queue/roadmap closure state
  - excluded: shutdown/persistence work, backend-front transport work, broad prompt-authority refactors, manual CLI smoke beyond targeted tests
- Output set is coherent:
  - canonical execution SSOT updated to closure state
  - aggregate roadmap refreshed
  - temp mirror scheduled for removal after validator pass

Pass 1 judgment:
- pass

## 3. Pass 2. Evidence And Consistency
- Current code truth matches the requested contract:
  - `main_a.py` now calls `_get_int_input(...)` exactly once on the interactive menu `7` path when `batch_size_override` is absent
  - the prompted value is stored in `requested_arc_limit`
  - the initial and subsequent `target_count` values are clamped to the remaining requested limit
  - `batch_size_override` still bypasses the prompt path
- Targeted tests were refreshed accordingly:
  - `tests/test_one_stop_frontier_lag_auto_continue.py` now asserts one interactive `_get_int_input(...)` call on normal paths
  - a dedicated interactive requested-limit stop test was added
  - `tests/test_auto_frontier_lag_harness.py -k frontier` still passes, proving harnessed prompt-free behavior remains intact
- Verification commands executed in this turn:
  - `python -m py_compile main_a.py tests/test_one_stop_frontier_lag_auto_continue.py tests/test_auto_frontier_lag_harness.py`
  - `python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py`
  - `python -m pytest tests/test_auto_frontier_lag_harness.py -k frontier`

Pass 2 judgment:
- pass

## 4. Pass 3. Execution Shape
- Closure decision is actionable:
  - acceptance criteria for the menu `7` contract are satisfied by code plus targeted tests
  - the item can be marked `closed`
- Queue impact is clear:
  - the menu `7` lane remains historically explicit in the roadmap
  - runtime/operator surface unification no longer needs to own menu `7` Arc-count semantics
  - the temp mirror can be removed once the roadmap mirror is refreshed and validation passes
- Residual risk is bounded and disclosed:
  - no fresh manual CLI smoke was run in this turn
  - remaining prompt-authority and backend-front work stays in separate queue items

Pass 3 judgment:
- pass

## 5. Confidence And Save Gate
- Pass 1 structure and scope: pass
- Pass 2 evidence and consistency: pass
- Pass 3 execution and readability: pass
- Estimated confidence: `97%`
- Save decision: final save allowed

## 6. Audit Conclusion
- The menu `7` desired-total Arc contract has been implemented and verified with targeted regression coverage.
- The canonical execution SSOT should now be marked `closed`.
- The aggregate roadmap should record menu `7` as `completed`, and its temp mirror should be removed after validator-confirmed queue refresh.
