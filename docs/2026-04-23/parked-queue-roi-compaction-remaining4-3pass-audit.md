# Parked Queue ROI Compaction Remaining4 3-Pass Audit

Date: 2026-04-23
Status: final (codebase-centered ROI re-audit of the 4 remaining parked lanes; `stage0-treatment-enrich-retirement-remediation` and `0_0-stage4-interview-round-owner-surface-reduction-remediation` are retired from the visible queue, leaving a 2-item parked board)
Canonical Path: `docs/2026-04-23/parked-queue-roi-compaction-remaining4-3pass-audit.md`
Baseline Commit: `30b9436fc3a5c3fcc3f6397bf23bfe45d24af918`
Baseline Dirty Summary: `dirty: prior queue-compaction docs and temp mirrors already in flight; no unrelated project-data cleanup performed`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Docs:
- `docs/2026-04-23/active-temp-execution-roadmap.md`
- `docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md`
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
- `docs/2026-04-02/stage0-treatment-enrich-retirement-remediation-execution-ssot.md`
- `docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
- `modules/core/stage01_helpers.py`
- `main_a.py`
- `modules/core/stage0_handoff.py`
- `modules/core/project_manager.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/providers/vertex_provider.py`
Side-Effect Coverage: documentation only

## 1. Intent

Re-audit the 4 remaining parked items against current code truth and current ROI, then remove any lane whose debt is still real but no longer deserves visible temp-queue authority.

## 2. Code Truth Snapshot

- `stage234-session-memory-max-utilization` still maps to live producer substrate:
  - core producer roles route through `vertexai:gemini-*`
  - `BaseAgent` still owns a live context-cache substrate
  - `VertexAIProvider` still surfaces `cached_content_token_count`
  - Stage4 and Stage2 still expose retry-memory surfaces that have not been normalized
- `stage0-bi-tr-production-harness-normalization-remediation` still maps to active runtime debt:
  - Stage0 explicitly declares `db_anchor:bible` as the runtime handoff owner
  - `force_sync_v25_dna()` is still framed in code as a compatibility bridge
  - Stage2 still bootstraps from the runtime handoff path rather than from a raw BI artifact
- `stage0-treatment-enrich-retirement-remediation` is now an explicitly demoted utility:
  - the legacy Stage0 path presents it as a non-canonical semantic rewrite utility
  - execution remains opt-in only
  - output is written to separate `*_enriched.json`, while the original treatment remains canonical
- `0_0-stage4-interview-round-owner-surface-reduction-remediation` still maps to real complexity debt:
  - current AST recount leaves `Stage4InterviewRound` at `170` methods
  - `6` methods are `120+ LOC`
  - `3` methods are `180+ LOC`
  - but the debt is structure-only and not a hidden runtime blocker

## 3. Decision

Keep visible:

1. `stage234-session-memory-max-utilization`
2. `stage0-bi-tr-production-harness-normalization-remediation`

Retire to historical backing:

1. `stage0-treatment-enrich-retirement-remediation`
2. `0_0-stage4-interview-round-owner-surface-reduction-remediation`

## 4. Why Two Lanes Were Retired

### `stage0-treatment-enrich-retirement-remediation`

- the code already demotes it to opt-in, non-canonical utility behavior
- the output already stays off the canonical treatment path
- the remaining work is operator-choice hygiene, not active runtime debt

### `0_0-stage4-interview-round-owner-surface-reduction-remediation`

- the complexity debt is real, but it is architecture debt rather than a current functional blocker
- there is no fresh Stage4 consumer lane that requires opening a new extraction tranche now
- leaving it visible would overstate near-term execution value relative to the two more operationally relevant lanes

## 5. Resulting Board Meaning

- the visible temp queue should now represent only the highest-leverage shared substrate lane and the still-real Stage0 runtime handoff lane
- architecture-only refactor debt and already-demoted utility retirement debt stay preserved canonically, but do not occupy live board space

## Pass 1

- each of the 4 remaining parked items was checked against live code, not only older queue text
- the compaction decision distinguished `still real debt` from `still deserves visible queue authority`

## Pass 2

- the keep vs retire split is internally consistent with the code surfaces:
  - session-memory remains shared cross-stage substrate debt
  - Stage0 BI/TR remains active runtime handoff debt
  - Stage0 enrich is already explicitly non-canonical utility debt
  - Stage4 owner-surface remains pure architecture debt

## Pass 3

- the resulting 2-item board is smaller and more honest
- canonical SSOTs preserve the retired context without pretending those lanes are near-term execution work
- ClickUp can now mirror a 2-item parked board instead of a 4-item mixed board

Confidence: 98/100
