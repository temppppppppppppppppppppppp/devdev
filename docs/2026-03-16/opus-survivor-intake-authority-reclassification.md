<!-- [참고자료] -->
<\!-- [참고자료] -->
# OPUS Survivor Intake Authority Reclassification

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/opus-survivor-intake-authority-reclassification.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: wide workspace code/docs changes already present; OPUS memo re-audit and survivor queue promotion in progress`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Docs:
- `docs/2026-03-15/opus/3pass-audit-master-summary.md`
- `docs/2026-03-15/opus/all-stage-deepdive-fix-candidates-ssot.md`
- `docs/2026-03-15/opus/all-subsystem-tf-consolidated-ssot.md`
- `docs/2026-03-15/opus/detail-subsystem-tf-consolidated-ssot.md`
- `docs/2026-03-15/opus/escalation-residual-tf-consolidated-ssot.md`
Evidence:
- `docs/2026-03-16/opus-survivor-intake-evidence.txt`
Confidence: `96%`

## 1. Intent
- Reclassify the OPUS memo bundle into live survivor leads vs excluded memo residue.
- Promote only the live-supported, still-open items into new canonical execution lanes.
- Keep contradicted, false-positive, already-closed, and unsampled claims out of direct patch authority.

## 2. Classification Rule
- `supported`: live code directly matches the claim strongly enough for promotion.
- `partial`: live code supports a narrower or lower-severity version than the original memo.
- `contradicted`: live code no longer matches a key premise in the memo.
- `closed/fp`: the memo's later reclassification or the current workspace already closes the claim.
- `unsampled`: not strong enough yet for promotion; keep as reference only.

## 3. Survivor Matrix

| ID | Source | Live Surface | Verdict | Promotion |
| --- | --- | --- | --- | --- |
| `S0-1` | stage deepdive | `modules/core/stage01_helpers.py:260-297` | supported | `persistence-context-authority-hardening` |
| `S3-1` | stage deepdive | `modules/core/stage3_orchestrator.py:1252-1256` | supported | `continuity-history-and-escalation-guardrails` |
| `S3-2` | stage deepdive | `modules/core/stage3_orchestrator.py:1216-1226` | supported | `continuity-history-and-escalation-guardrails` |
| `S4-4` | stage deepdive | `modules/core/stage4_interview_round.py:2862-2868` | supported | `continuity-history-and-escalation-guardrails` |
| `S4-5` | stage deepdive | `modules/core/stage4_interview_round.py:3011-3013` | supported | `continuity-history-and-escalation-guardrails` |
| `X-2` | stage deepdive | `modules/core/fact_ledger.py:114-119`; `modules/core/world_state.py:99-104` | supported | `persistence-context-authority-hardening` |
| `TF-BA-02` | subsystem | `modules/domain/agents/base_agent.py:1959-2081` | supported | `persistence-context-authority-hardening` |
| `TF-CM-03` | subsystem | `modules/domain/agents/continuity_manuscript.py:1056-1065` | supported | `continuity-history-and-escalation-guardrails` |
| `TF-FB-01` | detail subsystem | `modules/core/feedback_system.py:82-180` | supported | `director-feedback-decision-integrity-hardening` |
| `TF-FB-02` | detail subsystem | `modules/core/feedback_system.py:109-110` | supported | `director-feedback-decision-integrity-hardening` |
| `TF-DG-01` | detail subsystem | `modules/domain/agents/director_grading.py:686-688` | supported | `director-feedback-decision-integrity-hardening` |
| `TF-DG-02` | detail subsystem | `modules/domain/agents/director_grading.py:148-155` | supported | `director-feedback-decision-integrity-hardening` |
| `TF-S4CB-02` | detail subsystem | `modules/core/stage4_context_builder.py:1804-1816` | supported | `persistence-context-authority-hardening` |
| `TF-E3` | escalation residual | `modules/core/stage4_orchestrator.py:1353-1369` | supported | `continuity-history-and-escalation-guardrails` |
| `S2-2` | stage deepdive | `modules/core/stage2_finalizer.py:1093-1120` | partial | defer; narrower rollback issue only |

## 4. Excluded Matrix

| ID | Source | Current Reading | Operational Disposition |
| --- | --- | --- | --- |
| `S1-2` | stage deepdive | contradicted by existing `MAX_CONTEXT_VOLUMES = 3` sliding-window compression | excluded from patch queue |
| `S2-1` | stage deepdive | dead-code / false-positive path | excluded from patch queue |
| `X-3` | stage deepdive | false-positive / stale line citation | excluded from patch queue |
| `TF-E2` | escalation residual | stale rationale; current code already emits `V75-B` UI warnings | excluded from patch queue |
| `TF-SV-02` | detail subsystem | later CLOSED by current design intent and code comments | excluded from patch queue |
| `TF-PLV-01` | detail subsystem | dead branch / false-positive | excluded from patch queue |
| `TF-DE-02` | subsystem | later CLOSED in memo bundle and not re-opened by live spot check | excluded from patch queue |
| `TF-DE-09` | subsystem | design-tradeoff memo, not current execution target | excluded from patch queue |

## 5. Deferred Reference Set
- `unsampled` OPUS items remain historical memo leads only.
- `partial` items such as `S2-2` are not promoted until a narrower current-state survey confirms the remaining bug boundary.
- low-impact advisory-only collection-noise items stay out of the first survivor queue.

## 6. Promotion Outcome
- New canonical execution SSOTs:
  - `docs/2026-03-16/persistence-context-authority-hardening-execution-ssot.md`
  - `docs/2026-03-16/director-feedback-decision-integrity-hardening-execution-ssot.md`
  - `docs/2026-03-16/continuity-history-and-escalation-guardrails-execution-ssot.md`
- New canonical roadmap:
  - `docs/2026-03-16/opus-survivor-followup-execution-roadmap.md`
- Temp queue mirrors are created only for those three promoted execution SSOTs plus the single roadmap.

## 7. Operating Consequence
- The OPUS bundle stays as memo/reference material.
- The new survivor queue becomes the only live authority for any follow-up realization derived from that bundle.
- No item in the excluded matrix may be used as direct patch authority without a new current-state re-audit.
