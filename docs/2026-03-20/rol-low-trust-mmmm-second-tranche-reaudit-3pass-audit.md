# ROL Low-Trust `docs/mmmm` Second-Tranche Re-Audit

Date: 2026-03-20
Status: completed
Canonical Path: `docs/2026-03-20/rol-low-trust-mmmm-second-tranche-reaudit-3pass-audit.md`
Related Intake Triage: `docs/2026-03-20/rol-low-trust-mmmm-intake-triage-3pass-audit.md`
Related Fresh-Run Merge Audit: `docs/2026-03-20/rol-global-post-run-merge-audit.md`
Commit State:
- Baseline Commit: `9a4f46a8f8193c42e236cf181e0151b26a3167b4`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose
- Re-open the deferred second tranche from `docs/mmmm/` as low-trust hints only.
- Re-check `T02`, `T04`, `T05`, and `T14` against current live code rather than collector wording.
- Decide whether any new bounded execution item should be opened now.

## 2. Validity Gate

Target Paths:
- `docs/mmmm/T02-stage2-orch-context-survey.md`
- `docs/mmmm/T04-stage3-pipeline-survey.md`
- `docs/mmmm/T05-stage4-orch-context-survey.md`
- `docs/mmmm/T14-validation-pipeline-survey.md`

Input Evidence Set:
- current live workspace code
- completed `docs/mmmm` low-trust intake triage
- empty temp queue state

Checks:
- `docs/temp/queue-state.json` reports `queue_mode=empty`
- second tranche files still exist under `docs/mmmm/`
- no newer canonical execution queue supersedes this re-check

Result:
- second-tranche re-audit is valid

## 3. Live Re-Check Summary

### 3.1 T02 Stage 2 Orchestration
- still live:
  - CLI-only manual recovery input remains in `modules/core/stage2_orchestrator.py`
  - backward-compatibility thin wrappers remain in `modules/core/stage2_orchestrator.py`
  - batch semaphore `5` remains hardcoded
- downgrade:
  - these are not fresh-run root causes
  - the interactive `input()` path is gated behind failure/manual-recovery CLI flow and does not fire in the standard desktop `target_arc_count=1` path
- judgment:
  - no new bounded item is justified from `T02` right now

### 3.2 T04 Stage 3 Pipeline
- still live:
  - `modules/core/stage3_orchestrator.py` still reaches `quality_dashboard`, `constraint_db`, and `stage_rejection_history` via `self.app`
  - `modules/core/quality_dashboard.py` still has singleton-lock-only protection, not per-record locks
  - `three_phase_bp.generate(max_retries=9)` remains hardcoded in Stage 3
- downgrade:
  - `quality_dashboard` race concerns remain latent; current production usage is still effectively single-instance and mostly non-parallel at the record site
  - `max_retries=9` is a policy/cost knob, not a newly sharpened defect
- strongest remaining signal:
  - Stage 3 scoring still truncates LLM scoring input to 3000 chars while manuscript limits are `4000/5000/15000`
- judgment:
  - `T04` contributes one actionable bounded candidate: scoring sanitize-window alignment

### 3.3 T05 Stage 4 Orchestration
- still live:
  - `_build_stage4_to_3_reverse_feedback()` still reaches `self.app._generate_reverse_feedback_stage4_to_3` directly
  - `mandatory_context` truncation comment still says `50,000` while live threshold is `400000`
  - operator log still says `Director 면담: 5번 기회` while live threshold is `10`
- downgrade:
  - these are correctness-of-surface and DI-cleanliness issues, not the current highest-ROI runtime defect
- judgment:
  - keep as doc/contract cleanup candidates; do not open a bounded queue item yet

### 3.4 T14 Validation Pipeline
- still live:
  - `modules/validation/scoring_validator.py` uses `sanitize_max_chars=3000`
  - `config/settings/validation.yaml` still pins the same value
  - `modules/core/constants.py` manuscript limits remain `MIN=4000`, `TARGET=5000`, `MAX=15000`
- downgraded:
  - parallel validation path gaps remain mostly latent because production entry does not appear to use `validate_parallel_sync_v59`
  - `_UNCONDITIONAL_PASS_FLOOR=85` remains a discoverability concern, not an urgent runtime issue
- judgment:
  - `T14` confirms the strongest bounded candidate from this tranche

## 4. Candidate Classification

| Candidate | Status | Reason |
| --- | --- | --- |
| Stage 3 scoring sanitize window too short | promote | active runtime behavior, bounded patch surface, clear manuscript-limit mismatch |
| Stage 4 reverse-feedback DI bypass | watchlist | real but low blast radius |
| Stage 4 stale `5번 기회` / `50,000자` strings | watchlist | operator wording drift only |
| Stage 2 CLI manual input path | watchlist | CLI-only recovery path, not current frontier blocker |
| Validation parallel-path gaps | no-action-now | appears test-only / latent |
| QualityDashboard per-record locking | watchlist | latent concurrency concern, not yet tied to current operator/runtime failures |

## 5. Recommended Next Item
- open a single bounded execution item for:
  - `Stage 3 scoring sanitize-window alignment`
- keep the rest as watchlist only

Why this one:
- it is live in production code
- it directly affects quality scoring coverage
- it has a small write surface
- it does not require a broad policy rewrite

## 6. Non-Promoted Findings
- `T02` wrappers, semaphore constants, and manual input paths are still valid inventory notes but are not promoted.
- `T05` DI bypass and stale operator strings should be revisited only if another Stage 4 hygiene pass is opened.
- `T14` parallel-path omissions remain latent until production actually adopts the parallel validation path.

## 7. Final Decision
- second-tranche low-trust re-audit is complete
- one new bounded execution item is justified
- no aggregate roadmap is required because the queue re-opens with a single item only

## 8. Confidence
- pass 1:
  - deferred tranche scope re-opened against current queue state
- pass 2:
  - collector claims re-checked against live code and current config
- pass 3:
  - action-bearing split reduced to one bounded candidate
- estimated confidence:
  - `0.96`
