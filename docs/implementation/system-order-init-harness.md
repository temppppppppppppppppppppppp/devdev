# System Order Init Harness

Date: 2026-03-14
Status: active
Applies To: all system-track orders
Governance Map:
- `docs/implementation/operations-governance-map.md`
Global Survey Contract:
- `docs/implementation/codebase-global-survey-coverage-contract.md`
Deep Survey Harness:
- `docs/implementation/deep-global-integrity-survey-harness.md`

## 1. Purpose
- Provide the first-read startup routine for system-track work.
- Keep `AGENTS.md` focused on routing and invariants, not long operational procedures.
- Decide which downstream harnesses must be loaded before work starts.
- Serve as the entry point for the bounded `Recursive Ops Loop`.
- Treat `Recursive Ops Loop`, `ROL`, and `rol` as the same operating alias.

Downstream companion harnesses:
- `docs/implementation/system-order-preflight-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
- `docs/implementation/temp-execution-queue-roadmap-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/evidence-manifest-harness.md`
- `docs/implementation/ops-validator-harness.md`
- `docs/implementation/execution-closure-harness.md`
- `docs/implementation/exception-registry-harness.md`
- `docs/implementation/process-health-scorecard-harness.md`
- `docs/implementation/system-supervisor-harness.md`
- `docs/implementation/stale-reference-sweep-harness.md`
Available templates:
- `docs/implementation/execution-ssot-template.md`
- `docs/implementation/execution-roadmap-template.md`
- `docs/implementation/execution-closure-template.md`
- `docs/implementation/evidence-manifest-template.md`
- `docs/implementation/execution-exception-template.md`
- `docs/implementation/process-health-scorecard-template.md`
- `docs/implementation/deep-global-survey-template.md`
- `docs/implementation/cross-cut-integrity-matrix-template.md`
- `docs/implementation/uncertainty-contradiction-ledger-template.md`
Available contracts and checklists:
- `docs/implementation/canonical-naming-contract.md`
- `docs/implementation/commit-state-minimal-contract.md`
- `docs/implementation/temp-queue-state-contract-v1.json`
- `docs/implementation/temp-queue-state-template.json`
- `docs/implementation/queue-priority-rubric.md`
- `docs/implementation/single-ssot-roadmap-contract.md`
- `docs/implementation/evidence-triangulation-contract.md`
- `docs/implementation/integrity-confidence-scoring-contract.md`

## 2. When To Use
Read this harness first for any system-track order involving:
- codebase investigation
- bug fixing
- refactor or remediation
- runtime, DB, logging, UI, desktop, or process-runner work
- system audits, surveys, execution SSOTs, or roadmap-driven implementation

Do not use this harness for narrative-pipeline orders.

## 3. Startup Routine

### Step 1. Confirm Track
- Confirm the request is system-track, not narrative-pipeline.
- If the task is narrative-pipeline, stop here and use the blockguide flow instead.
- If the user says `ROL` or `rol`, interpret it as the bounded `Recursive Ops Loop`.
- If the user says `global`, `repo-wide`, `전역`, or `전역 전체`, load the global survey coverage contract unless the request narrows scope.
- Treat `ROL 전역 전체 전수조사` as deep integrity survey mode by default unless the user explicitly asks for a lighter pass.
- Treat `ROL 전수조사-실전테스트 병행`, `ROL live-merge`, or equivalent fresh-live-run-plus-survey wording as live-merge survey mode.

- If the user asks for a `supervisor`, `boss`, `상사`, `사수`, blunt operator review, or explicit banmal review mode, load `docs/implementation/system-supervisor-harness.md` in addition to the normal survey or queue harnesses.

### Step 2. Inspect Active Temp Queue
- Inspect `docs/temp/` before doing substantial work.
- Check for:
  - `*-execution-ssot.md`
  - `execution-roadmap.md`
  - `queue-state.json`

Queue interpretation:
- no execution mirrors: no active temp execution queue
- one execution mirror: single pending or active realization item
- two or more execution mirrors: aggregate roadmap required
- roadmap present: treat the roadmap as the controlling execution queue artifact

### Step 3. Determine Operating Mode
Choose one mode before proceeding.

Mode A. Queue Realization
- use when the request is effectively "continue", "execute", "realize", or a direct implementation request tied to queued execution docs
- if `docs/temp/execution-roadmap.md` exists, follow it first

Mode B. Survey / Audit / Execution-Doc Production
- use when the request is to inspect, survey, audit, classify, inventory, or write execution docs before patching
- load the survey/execution harness next

Mode B1. Live-Run Merge Survey
- use when the request intentionally combines a fresh live run with parallel survey or audit work
- load the survey/execution harness first, then `docs/implementation/live-run-merge-survey-harness.md`
- treat mid-run artifacts as provisional evidence until the run reaches a terminal state

Mode C. Direct Focused Patch
- use when the request is a narrow code change and no broader survey or active temp queue should govern it
- still respect document-save and temp-queue rules if new execution docs are created during the work

### Step 3B. Apply Complexity / Refactor Gate
- Before substantial system-track implementation, classify the intended work as one of:
  - complexity-regression prevention
  - same-file long-function reduction
  - owner-surface / boundary refactor
  - fresh-run validation after cleanup
- If the touched production code would introduce or preserve a new `180+ LOC` function without a bounded-shell justification, stop and restructure before proceeding.
- If the current repo state already has `180+ = 0` or `200+ = 0`, do not keep defaulting to helper extraction. Re-check whether the higher ROI is:
  - owner-surface reduction
  - module/runtime boundary cleanup
  - contract normalization
  - fresh run plus fail-only bugfix
- If a hot owner class is already above the live direct-method pressure line, prefer family-level module split over adding more same-file helpers unless the helper extraction clearly reduces both LOC risk and owner pressure.
- For time-boxed work after the high-risk long-function bands are cleared, prefer `snapshot -> fresh run -> fail-only stabilization` over opening a new broad refactor wave.
- **LLM 가독성 원칙** — 프로덕션 코드는 LLM이 읽고 추론하기 편하도록 최대한 배려한다.
  - 함수·메서드는 단일 책임, 명확한 이름, 짧은 본문을 유지한다.
  - 암묵적 부작용, 깊은 중첩, 먼 거리의 상태 변이를 피한다.
  - 분기·조건이 많을수록 early return·guard clause로 평탄화한다.
  - 이 원칙은 사람 가독성과 상충하지 않는다 — LLM이 읽기 쉬운 코드는 사람도 읽기 쉽다.

### Step 3C. Apply Orientation Pack Impact Gate
- Use `docs/2026-03-23/llm-codebase-orientation-pack.md` as the lightweight codebase navigation map for entry flow, authority, contract, and observability understanding.
- Before or after substantial system-track code changes, explicitly check whether the touched area changes any orientation-pack surfaces:
  - top-level reading order or entry routing
  - authoritative owner or runtime/module boundary
  - verdict, persistence, or logging sink ownership
  - shared contract field names or field meaning
  - operator observability path across console, audit, DB, or summary sinks
- If any of those surfaces changed, refresh the canonical orientation pack before closure and treat that refresh as a human-facing doc update under the normal 3-pass plus 95% confidence gate.
- Do not force an orientation-pack refresh for purely local bugfixes, narrow comment-only edits, or cosmetic output changes that do not alter navigation, authority, contract, or sink topology.

### Step 3D. Apply Code 3-Pass Gate For Long-Function / Boundary Work
- For substantial same-file long-function reduction, owner-surface refactor, runtime/module split, sink relocation, or observability changes, do not treat the patch as complete until a code-side 3-pass audit finishes.
- Use this code 3-pass sequence:
  - Pass 1. Pre-change authority/sink audit
    - name the authoritative owner
    - name the touched contract or payload boundary
    - name the touched side effects:
      - console
      - audit
      - DB
      - metrics
      - file or artifact sinks
  - Pass 2. Post-change diff audit
    - confirm the same authority still owns the decision unless the change intentionally moved it
    - confirm no sink silently disappeared, duplicated, or became unreachable
    - confirm no dead wrapper, duplicate definition, or stale compat shell was introduced
  - Pass 3. Verification audit
    - run targeted compile/test validation
    - run UTF-8 hygiene when touched files are text/code/doc/config
    - run fresh live or operator-path verification when the change affects operator-facing flow, verdict visibility, or runtime observability
- Reuse active survey evidence or existing hotspot/audit docs for Pass 1 when available; do not regenerate broad survey artifacts just to satisfy the gate.
- Lightweight local bugfixes or comment-only edits may use a reduced form, but any change that touches authority, persistence, or operator-observability should use the full gate.

Bounded-loop rule:
- do not escalate from survey-only into implementation unless the user asked for it
- do not escalate from execution-doc production into realization unless the user asked for it
- do not generate roadmap or closure artifacts when queue conditions do not require them
- codebase-global survey bundles may still generate tranche survey docs, area execution SSOT docs, and an aggregate roadmap as documentation outputs without being treated as implementation

### Step 3A. Capture Minimal Commit State
- For substantial survey, re-audit, execution-SSOT, or roadmap work, capture the minimal commit-state anchor early.
- Use `docs/implementation/commit-state-minimal-contract.md`.
- Record:
  - `Baseline Commit`
  - `Baseline Dirty Summary`
- When resuming or revalidating later in a different work phase, refresh:
  - `Resume Commit`
  - `Resume Drift Summary`
- Keep this bounded. Prefer short summaries over raw git transcript dumps.

### Step 4. Load Required Companion Harnesses
- For survey, audit, execution SSOT, remediation-plan, or residual-inventory work:
  - read `docs/implementation/system-full-survey-execution-harness.md`
- For survey or audit work intentionally paired with a fresh live run:
  - read `docs/implementation/live-run-merge-survey-harness.md`
- For codebase-wide global survey intent:
  - read `docs/implementation/codebase-global-survey-coverage-contract.md`
  - read `docs/implementation/deep-global-integrity-survey-harness.md`
- For high-rigor startup checks before substantial work:
  - read `docs/implementation/system-order-preflight-harness.md`
- For turning multiple evidence inputs into one execution doc:
  - read `docs/implementation/execution-synthesis-harness.md`
- For active temp execution queue or roadmap work:
  - read `docs/implementation/temp-execution-queue-roadmap-harness.md`
- For creating or updating human-facing docs:
  - read `docs/implementation/document-3pass-audit-harness.md`
- For recording minimal git workspace anchors on ROL docs:
  - read `docs/implementation/commit-state-minimal-contract.md`
- For reusable evidence indexing:
  - read `docs/implementation/evidence-manifest-harness.md`
- For queue validation or canonical/mirror integrity checks:
  - read `docs/implementation/ops-validator-harness.md`
- For closing realized queue items or clearing temp:
  - read `docs/implementation/execution-closure-harness.md`
- For explicit allowlists or temporary rule bypasses:
  - read `docs/implementation/exception-registry-harness.md`
- For operational status reporting:
  - read `docs/implementation/process-health-scorecard-harness.md`
- For supervisor-style multi-survey synthesis, operator-facing prioritization, or requested banmal/direct review mode:
  - read `docs/implementation/system-supervisor-harness.md`
- For governance migrations or stale authority cleanup:
  - read `docs/implementation/stale-reference-sweep-harness.md`
- For future specialized system harnesses:
  - load only the harnesses directly relevant to the order

### Step 5. Apply Queue Precedence
- If there is an active temp roadmap and the user is asking to continue realization work, use the roadmap order rather than ad hoc file order.
- If there are multiple temp execution docs and no roadmap yet, create the roadmap before implementing.
- When building or refreshing a roadmap, use `docs/implementation/queue-priority-rubric.md` for ordering.
- Before starting code modification from an execution SSOT or roadmap, re-run the document 3-pass audit plus the 95% confidence gate on the governing canonical doc against the current workspace state.
- If the user explicitly redirects to a different system task, follow the user but note that the temp queue remains pending.

### Step 6. Apply Document Rules
- Human-facing docs follow the 3-pass save gate plus a confidence gate of at least 95% before final save.
- Canonical execution docs live in `docs/YYYY-MM-DD/`.
- Execution mirrors in `docs/temp/` are queue copies, not canonical files.
- In live-merge survey mode, raw evidence and explicit draft watchlists may be saved before the run completes, but canonical conclusions, execution SSOT mirrors, roadmap closure, and final remediation claims wait until post-run merge audit.
- Use the dedicated document-audit harness for the detailed pass procedure.
- Run `python scripts/ops_validator.py` after material execution-doc or roadmap changes.
- Run `python scripts/validate_deep_global_survey_bundle.py --survey-doc <canonical-master-survey-doc>` after material deep-global survey updates.
- Run `python scripts/sync_temp_queue_state.py` when the live temp queue should be materialized for operators or tooling.
- Use the closure harness before deleting temp queue artifacts.

### Step 7. Apply Pytest Memory Cleanup
- Treat `scripts/run_pytest_lowmem.py` logs as disposable execution artifacts, not durable authority.
- If `pytest` or the low-memory runner is interrupted, times out, or appears stuck after the last expected shard, inspect live `python` processes by command line.
- Terminate only the orphaned pytest runner and its pytest child processes.
- Do not terminate unrelated `python` processes such as IDE language servers, notebooks, or user-owned background jobs.
- After extracting the needed pass/fail evidence, clean stale `logs/pytest_lowmem/` directories so later turns do not inherit false-live test state.

## 4. Decision Matrix

| Situation | Action |
| --- | --- |
| System order + no temp execution docs | proceed normally |
| System order + one temp execution doc + user asks to implement/continue | use that execution doc as active queue item |
| System order + multiple temp execution docs | create or refresh aggregate roadmap first |
| System order + active roadmap + user asks to continue | follow roadmap |
| System order + survey request | read survey/execution harness and produce survey docs first |
| System order + fresh live run paired with survey | read survey/execution harness plus live-run-merge harness; final SSOT only after run completion |
| Narrative order | do not use this harness |

## 5. Non-Goals
- This harness does not define the detailed 3-pass survey method.
- This harness does not replace the survey/execution harness.
- This harness does not replace narrative blockguide rules.

## 6. Guardrails
- Do not skip temp-queue inspection for system-track work.
- Do not let a stale temp mirror override the canonical dated execution doc.
- Do not inflate `AGENTS.md` with long procedural duplication that belongs here.
- Do not start multi-item realization without checking whether a roadmap already exists.
- Treat UTF-8 integrity as a workspace-wide invariant for touched text/code/doc/config files.
- If a touched file shows invalid UTF-8, a triple-question placeholder, `U+FFFD`, non-ASCII-adjacent `?`, or suspicious Hangul/CJK mixed-script mojibake, stop and repair the source boundary before continuing.
