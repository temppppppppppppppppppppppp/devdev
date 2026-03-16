# Project 0_260316 Unified Execution SSOT

Date: 2026-03-16
Status: completed canonical
Canonical Path: `docs/2026-03-16/project-0-260316-execution-ssot.md`
Temp Mirror Path: `docs/temp/project-0-260316-execution-ssot.md` (removed after closure)
Commit State:
- Baseline Commit: `391c882c4f8653f4c162a329cd6b60e3a850fc59`
- Baseline Dirty Summary: `dirty: 1 tracked; hotspot: projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Companion System SSOT: `docs/2026-03-16/broken-feedback-loop-remediation-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-16/project-0-260316-3arc-run-stop-survey.md`
- `docs/2026-03-16/project-0-260316-stage4-continuity-and-codebase-survey.md`
- `docs/2026-03-16/project-0-260316-threat-carryover-delta-audit.md`
- `docs/2026-03-16/project-0-260316-pass-with-fix-firewall-survey.md`
- `docs/2026-03-16/project-0-260316-ai-slop-feedback-loop-survey.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-interruption-forensics.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-artifact-integrity-audit.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-resumability-assessment.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-3pass-audit.md`
Confidence After Merged 3-Pass Audit: `95%`
Authority Order:
1. live code + raw evidence
2. project-specific canonical surveys + OPUS freshrun bundle
3. companion system SSOT for shared broken feedback loop remediation authority
4. bounded inference
Refresh Context:
- this canonical closure doc already absorbed the earlier merged re-audit drift across live code, project evidence, and the companion broken-feedback bundle
- the commit-state block above reflects the latest doc-only closure hygiene re-audit, not the original execution turn
- this document owns `0_260316` recovery, stop-point, integrity, resumability, and regression authority
- the companion system SSOT owns bundle-wide remediation priority for shared broken feedback loop items

## Executive Verdict

- **Fact:** `0_260316` was a valid 3-arc Frontier Lag run, and the confirmed frontier at interruption time was `Arc 3 complete / Blueprint 11 complete / Manuscript 6 complete`.
- **Fact:** the stop point was `ep7 Stage 4 attempt 1`, immediately after three parallel Chief Writer POST requests were launched and while all three were waiting for response headers.
- **Fact:** the stop shape is a clean cut interruption. No ep7 manuscript row, episode_meta row, artifact directory, or partial Stage 4 output exists.
- **Inference:** user-side manual interruption such as `Ctrl+C` or equivalent process termination is the highest-confidence cause, but it is not established as fact.
- **Fact:** extant outputs are materially intact. `ep1` through `ep6` manuscripts, Stage 2/3/4 artifacts up to the frontier, and DB integrity all remain consistent; no corruption evidence was found.
- **Decision:** project recovery is operationally authorized from `ep7` via resume flow.
- **Decision:** project-specific remediation for `0_260316` is closed here after the bounded continuity substrate fixes, while shared broken-feedback follow-ups remain delegated to the companion system SSOT.

## Companion Boundary

- this document owns:
  - `ep7` stop point
  - artifact integrity
  - `Menu 7 이어가기` recovery decision
  - `0_260316`-specific Stage 4 risks
  - regression authority for shared findings
- the companion system SSOT owns:
  - `ai_slop` style feedback wiring
  - `npc_drift` structured retry handoff
  - `coverage_warning` explicit surfacing
  - `open_review` sidecar replay wording normalization
  - `FactLedger` hardening
  - reverse feedback automation
  - `dialogue_ratio` dynamic target linkage
  - `cost_log` runtime consumption
- shared items may appear here as project evidence, but remediation priority authority for them is externalized to the companion system SSOT

## Evidence Base

### Source Cluster A: Prior Canonical Surveys

- `docs/2026-03-16/project-0-260316-3arc-run-stop-survey.md`
- `docs/2026-03-16/project-0-260316-stage4-continuity-and-codebase-survey.md`
- `docs/2026-03-16/project-0-260316-pass-with-fix-firewall-survey.md`
- `docs/2026-03-16/project-0-260316-ai-slop-feedback-loop-survey.md`

### Source Cluster B: OPUS Freshrun Bundle

- `docs/2026-03-16/OPUS_freshrun-0_260316-evidence.txt`
- `docs/2026-03-16/OPUS_freshrun-0_260316-interruption-forensics.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-production-quality-review.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-artifact-integrity-audit.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-resumability-assessment.md`
- `docs/2026-03-16/OPUS_freshrun-0_260316-3pass-audit.md`

### Source Cluster C: Project Code Revalidation

- `main_a.py:4043-4096`
- `modules/core/stage4_context_builder.py:1759-1762`
- `modules/core/stage4_context_builder.py:2105-2480`
- `modules/core/stage4_orchestrator.py:485-527`
- `modules/core/stage4_orchestrator.py:1507-1540`
- `modules/core/stage4_interview_round.py:401-424`
- `modules/core/stage4_interview_round.py:3534-3560`
- `modules/core/stage4_interview_round.py:3977-4044`
- `modules/core/inventory_state.py:1-115`
- `modules/core/stage4_post_processor.py:304-367`
- `modules/core/stage4_post_processor.py:856-1169`
- `modules/core/stage4_post_processor.py:1299-1304`
- `modules/core/quality_signal_metrics.py:129-202`
- `modules/core/db_manager.py:2910-2940`
- `modules/core/quality_dashboard.py:137-147`
- `modules/api/bridge_server.py:1021-1036`
- `modules/domain/agents/chief_writer.py:799-920`
- `modules/domain/agents/chief_writer.py:1551-1669`
- `modules/core/world_state.py:237-299`
- `modules/core/fact_ledger.py:191-227`
- `modules/core/fact_ledger.py:278-312`
- `modules/validation/continuity_validator.py:274-423`
- `modules/validation/blocking_validator_entity_checks.py:149-179`

### Companion Canonical System Authority

- `docs/2026-03-16/broken-feedback-loop-remediation-execution-ssot.md`

## 3-Pass Audit

### Pass 1: Factual Reconciliation

| Topic | Merged Result | Basis |
| --- | --- | --- |
| Run mode | 3-arc Frontier Lag run | prior stop survey + OPUS evidence |
| Final completed frontier | Arc 3 / Blueprint 11 / Manuscript 6 | DB + artifact frontier + JSONL |
| Interruption timestamp | `2026-03-16 12:56:06` | session log tail, OPUS evidence |
| Interruption phase | ep7 Stage 4, 3 parallel POSTs waiting for response headers | session log tail |
| Stage 4 completed episodes | ep1-6 | manuscripts table + drafts + artifacts |
| Stage 4 attempt profile | 11 Stage 4 attempts total: 6 final PASS, 5 REJECT | OPUS evidence + prior survey scope normalization |
| Stage 4 total cost | `$4.7288` raw, reported as `$4.728` | `episode_production.jsonl` aggregate |
| Production quality average | `95.2` using final episode scores `98/90/96/98/90/99` | OPUS per-episode score table; this overrides any looser summary number |
| DB integrity | `PRAGMA integrity_check = ok` | prior survey + OPUS evidence |
| ep7 partial outputs | none | DB, JSONL, artifacts, drafts all clean |
| Shared broken-feedback scope split | validated | companion system SSOT audit + direct code revalidation |

Pass 1 result: all governing frontier, timestamp, count, cost, and scope-boundary claims were normalized and aligned.

### Pass 2: Conflict Resolution

| Topic | Prior Project View | Companion / External View | Resolution |
| --- | --- | --- | --- |
| Stop classification | abrupt interruption outside managed failure | clean cut interruption | **Resolved:** use `clean cut interruption` as fact |
| Exact cause | external interruption, cause unproven | `Ctrl+C` or manual stop most likely | **Resolved:** manual stop is the highest-confidence inference, not a fact |
| Artifact integrity | no corruption seen | integrity PASS, sink alignment minor only | **Resolved:** accept PASS integrity judgment |
| Resumability | recovery posture looked favorable, not yet merged into SSOT | `Menu 7 이어가기` recommended | **Resolved:** accept resumability as the operational decision |
| Structural system issue | Stage 4 authority/schema/gate problem remains | quality/integrity good, resume okay | **Resolved:** both stand; project recovery and system health are separate questions |
| `ep4 round 0` cause interpretation | local continuity issue existed, but exact token direction was not fully settled | some OPUS prose reversed the name direction | **Resolved:** canonical project truth is `한진호`; selected candidate drifted to `한태준` |
| `ep5 round 0` contamination scope | stale state and local location drift were both suspected | some OPUS prose overstated this as `blueprint_0005` contamination | **Resolved:** selected manuscript drift is confirmed; `blueprint_0005` itself is clean on the core office/`한미증권` handoff |
| `PASS_WITH_FIX` underuse | structure defects were already flagged | OPUS cost review implied several fixable reruns | **Resolved:** a narrow fixable-firewall subset exists (`ep4 r0`, `ep4 r1`, `ep5 r0`), and the bounded routing/payload fix is now landed in live code; `ep5 r2` remains outside it |
| AI-slop feedback visibility | not previously normalized as a separate SSOT finding | companion system SSOT normalizes core-vs-operator split | **Resolved:** companion system SSOT now closes the bounded runtime-core advisory gap via Director-mediated style/core warnings; this document keeps it only as project evidence |
| Broken feedback loop bundle scope | previously mixed into Lane B | companion system SSOT is broader than `0_260316` | **Resolved:** companion system SSOT owns remediation priority for shared bundle items; this document keeps project-only facts and risks |
| Quality average figure | previously not normalized in SSOT | OPUS prose and summary metadata were not fully consistent | **Resolved:** use raw final score arithmetic `95.2` |

Pass 2 result: project frontier and recovery posture are resolved. Shared broken-feedback items are now synchronized to the companion system SSOT instead of duplicated here as canonical system-wide remediation.

### Pass 3: Decision Completeness

- **Fact-labeled items** are limited to DB/artifact/log/code-backed claims.
- **Inference-labeled items** are limited to interruption mechanism interpretation.
- **Decision-labeled items** are limited to:
  - `Lane A`: project recovery from `ep7`
  - `Lane B`: project-specific Stage 4 remediation
  - companion handoff for shared broken-feedback remediation
- the document remains decision-complete for the next operator because it answers:
  - can `0_260316` resume without repair
  - which risks are project-specific versus delegated to the companion system SSOT

Pass 3 result: fit to guide project recovery and project-level regression ownership without re-opening the system-wide bundle authority question.

## Overlap Reconciliation

| Topic | Classification | Canonical Authority | Project Treatment |
| --- | --- | --- | --- |
| `ai_slop` feedback gap | `shared-consistent` | companion system SSOT | retained only as `0_260316` proof corpus; remediation status follows the companion system SSOT |
| `npc_drift` retry handoff | `shared-needs-wording-sync` | companion system SSOT | referenced here only as Stage 4 evidence |
| `open_review` | `shared-needs-wording-sync` | companion system SSOT | do not treat label replay and same-round handoff as the same path |
| `coverage_warning` explicit surfacing | `shared-needs-wording-sync` | companion system SSOT | referenced here only where it affects Stage 4 proof |
| `FactLedger` fragility | `system-only` | companion system SSOT | not promoted to a project-only canonical queue |
| `reverse_feedback` auto-trigger status | `system-only` | companion system SSOT | not restated here except as regression implications |
| `dialogue_ratio` style-target linkage | `system-only` | companion system SSOT | out of scope for project recovery authority |
| `cost_log` runtime reader gap | `system-only` | companion system SSOT | out of scope for project recovery authority |
| `ep7` stop point / integrity / resumability | `project-only` | this document | do not promote into system remediation authority |
| `Menu 7 이어가기`, `Arc 3 / Blueprint 11 / Manuscript 6` | `project-only` | this document | remain project facts only |

## Authority Reconciliation

- **Fact:** ep7 stopped after all three Chief Writer POST requests had been sent and before any response body or downstream commit path was recorded.
- **Inference:** `Ctrl+C` or another manual process stop is the best explanation because the cut is immediate, clean, and lacks traceback or timeout signatures.
- **Fact:** there is no evidence of output corruption. ep7 left no partial manuscript or partial Stage 4 artifact, and ep1-6 remain intact.
- **Fact:** the codebase still contains real project-relevant Stage 4 structural defects, but one bounded continuity fix is now landed:
  - `main_a.py:4043-4096` shows Stage 4 re-entry can rebuild `state_tracker` from arcs while `world_state` and `fact_ledger` load from DB.
  - `modules/core/stage4_context_builder.py:1759-1762` and `2105-2480` show `arc_tactical` still participates in writer-facing mandatory context and retrieval planning.
  - `modules/core/stage4_orchestrator.py:1507-1540` shows Director continuity still gets a thinner `story_context` than the broader writer-facing packet.
  - `modules/core/stage4_interview_round.py:3977-4044` now resolves `prev_hud` with persisted precedence: `manuscript.hud_snapshot -> state_logs.data.hud_snapshot -> state_logs.data.actual_truth -> live sys.hud.pro_root fallback`.
  - `modules/core/stage4_context_builder.py:920-1013` and `2339-2393` now suppress overlapping `state_tracker` summaries when `world_state`/`fact_ledger` canonical layers already cover the same domain, so arc-derived tracker summaries no longer outrank persisted continuity blocks inside Stage 4 mandatory context.
  - `modules/core/inventory_state.py:1-115`, `modules/core/stage4_post_processor.py:856-1169`, `modules/core/world_state.py:260-299`, and `modules/core/fact_ledger.py:204-227` now preserve count-aware inventory snapshots/deltas through `actual_truth`, `state_logs`, `world_state`, and `fact_ledger`.
  - `modules/validation/continuity_validator.py:305-423` now reads structured `inventory_counts` and warns on opening count drift such as persisted `3대` degrading to prose `2대`.
  - `modules/core/stage4_orchestrator.py:485-527` shows `컴퓨터` and `모니터` issue families are intentionally downgraded in preflight.
- **Fact:** `0_260316` exposed a separate local routing defect, and a bounded repair is now live: `modules/domain/agents/director_ensemble.py:1244-1571` adds a narrow `firewall_fixable` route plus structured `contradiction_details`, while `modules/core/stage4_interview_round.py:340-438`, `modules/core/stage4_interview_round.py:3505-3604`, `modules/core/stage4_interview_round.py:4681-4710`, and `modules/domain/agents/chief_writer.py:1748-1764` now carry that detail into retry, PASS_WITH_FIX patching, and recent-attempt history.
- **Fact:** shared broken-feedback topics such as `ai_slop`, `npc_drift`, `coverage_warning`, `open_review` replay, `FactLedger`, reverse feedback, `dialogue_ratio`, and `cost_log` are now canonically classified in the companion system SSOT and must not be re-authored here as independent system-wide queues.

Core reconciliation sentence:

> `resume 가능`은 `system issue resolved`와 동일어가 아니다.  
> This project is resumable, but the Stage 4 substrate is still not healthy enough to close the underlying engineering issue.

## Execution Decision

### Lane A: Project Recovery

**Decision:** default recovery path is `Menu 7 이어가기`.

**Applicability**
- single target only: project `0_260316`

**Preconditions**
- DB integrity is `ok`
- manuscripts exist for ep1-6
- blueprint exists for ep7
- no partial ep7 Stage 4 artifact exists
- missing `vec0` is treated as non-blocking for recovery

**Operational goal**
- resume from ep7 without data repair, rewind, or artifact cleanup

**Guardrails**
- do not declare the engineering issue resolved if ep7 resumes successfully
- do not rewrite ep1-6 as part of recovery
- treat any ep7 success as project recovery evidence, not as proof that Stage 4 authority mixing is fixed

### Lane B: Project-Specific System Remediation

**Decision:** treat project-specific remediation as closed here, while delegating shared broken-feedback bundle priority to the companion system SSOT.

**Why this lane is required**
- Stage 4 re-entry can mix arc-derived tracker state with DB-derived persisted state (`main_a.py:4043-4096`)
- Director continuity remains thinner than writer-facing context (`stage4_orchestrator.py:1507-1540`)
- `prev_hud` continuity now prefers persisted prior-episode truth, and overlapping `state_tracker` prompt summaries now defer to canonical persisted layers inside Stage 4 mandatory context; residual app-init object mixing still remains (`stage4_interview_round.py:3977-4044`, `stage4_context_builder.py:2339-2393`, `main_a.py:4043-4096`)
- bounded local-fix routing is now landed, but only for narrow name/title/location/banned-term cases (`director_ensemble.py:1244-1571`)
- contradiction payload now survives into retry and PASS_WITH_FIX feedback, but persisted-snapshot/authority issues still dominate the broader continuity risk (`stage4_interview_round.py:340-438`, `stage4_interview_round.py:3505-3604`, `stage4_interview_round.py:4681-4710`)
- count-aware inventory persistence, relationship carry-over, and threat carry-over are now landed as persisted canonical surfaces; severity policy remains a validated no-change (`inventory_state.py`, `stage4_post_processor.py`, `world_state.py`, `fact_ledger.py`, `stage4_context_builder.py`, `stage4_interview_round.py`, `continuity_validator.py`)
- preflight weakens office-state issues that matter in this project (`stage4_orchestrator.py:485-527`)

**Shared bundle boundary**
- `ai_slop` style digest
- `npc_drift` structured handoff
- `coverage_warning` explicit surfacing
- `open_review` label replay wording
- `FactLedger` hardening
- reverse feedback automation
- `dialogue_ratio` dynamic target linkage
- `cost_log` runtime consumption

The items above are canonicalized in the companion system SSOT and appear here only as shared regression evidence.

**Shared tranche start rule**
- before any companion system SSOT tranche starts, validate the then-current codebase first
- live code has higher authority than stale survey wording for tranche start
- only after that validity check passes should `0_260316` be used as the regression gate for shared findings

**Priority order**
1. ~~relationship delta durable persistence~~ → **completed** (state_log gate re-audited and fixed for `knowledge_map`-only cases)
2. ~~threat carry-over durable persistence~~ → **completed** (`active_pressure_vectors` now persists through `actual_truth/state_log/bible_delta/world_state` and re-enters Stage 4 continuity surfaces)
3. ~~preflight/validator severity 정책 수정~~ → **evaluated: no change needed** (inventory_count_drift in continuity_validator already structurally detects count drift; preflight genre-tolerance TF-49b is intentional; RelDrift advisory is operational)
4. use `0_260316` as the regression gate for companion system SSOT tranches

**Current loop delta (2026-03-16)**
- bounded implementation landed for `fixable-firewall routing + detailed contradiction payload persistence`
- `modules/domain/agents/director_ensemble.py:1244-1571` now promotes narrow local contradictions to `PASS_WITH_FIX` when the candidate is otherwise healthy (`score >= 80`, `continuity_contradiction >= 30`, `<= 3` local-fix contradictions)
- the same path now emits `contradiction_details`, and `modules/core/stage4_interview_round.py:340-438`, `modules/core/stage4_interview_round.py:3505-3604`, `modules/core/stage4_interview_round.py:4681-4710`, plus `modules/domain/agents/chief_writer.py:1748-1764` preserve that detail through retry feedback, PASS_WITH_FIX patching, and recent-attempt history
- bounded implementation also landed for `persisted prev_hud precedence` in the Stage 4 CV path
- `modules/core/stage4_interview_round.py:3977-4044` now resolves `prev_hud` from persisted sources before any live HUD fallback and records `prev_hud_source` for audit visibility
- bounded implementation also landed for `mandatory_context authority precedence` between `world_state/fact_ledger` and arc-derived `state_tracker` summaries
- `modules/core/stage4_context_builder.py:920-1013` and `2339-2393` now suppress overlapping tracker summaries such as dead-NPC, item-state, relationship, movement, injury, timeline, and financial blocks when canonical persisted layers are already present
- bounded implementation also landed for `inventory count-aware schema`
- `modules/core/inventory_state.py:1-115` now normalizes counted inventory strings/dicts into deterministic `inventory_counts` and `inventory_count_deltas`
- `modules/core/stage4_post_processor.py:856-1169` now threads those counts through `actual_truth`, `bible_delta`, `state_logs`, and the atomic `world_state` / `fact_ledger` save path
- `modules/core/world_state.py:260-299` and `modules/core/fact_ledger.py:204-227` now persist per-item quantities instead of name-only presence, and summaries surface `xN` counts
- `modules/validation/continuity_validator.py:305-423` now reads structured inventory counts and emits `inventory_count_drift` warnings when the opening prose explicitly shrinks a persisted count
- targeted verification passed:
  - `python -m pytest -q tests/test_inventory_state.py` -> `2 passed`
  - `python -m pytest -q tests/test_world_state_caps.py` -> `6 passed`
  - `python -m pytest -q tests/test_fact_ledger.py` -> `14 passed`
  - `python -m pytest -q tests/test_stage4_post_processor.py` -> `43 passed`
  - `python -m pytest -q tests/test_validation.py` -> `29 passed`
  - `python -m pytest -q tests/test_v75c_contradiction_firewall.py` -> `14 passed`
  - `python -m pytest -q tests/test_a4_failure_pattern.py` -> `6 passed`
  - `python -m pytest -q tests/test_stage4_interview_round.py -k "extract_fix_feedback or retry_feedback_provenance"` -> `3 passed`
  - `python -m pytest -q tests/test_stage4_interview_round.py -k "firewall_continuity_reject or firewall_numeric_reject"` -> `2 passed`
  - `python -m pytest -q tests/test_chief_writer.py -k "retry_history_feedback_is_included"` -> `1 passed`
  - `python -m pytest -q tests/test_stage4_cv_context.py` -> `20 passed`
  - `python -m pytest -q tests/test_stage4_interview_round.py` -> `80 passed`
  - `python -m pytest -q tests/test_stage4_context_builder.py` -> `51 passed`
  - `python -m pytest -q tests/test_stage4_orchestrator.py` -> `58 passed`
  - `python -m pytest -q tests/test_continuity_packet.py` -> `18 passed`
- bounded implementation also landed for `relationship delta durable persistence`
- `modules/core/stage4_post_processor.py:948-964` now generates relationship_changes as dict format `{npc, to, from}` instead of flat strings, matching what `world_state.py` and `fact_ledger.py` expect
- `modules/core/stage4_post_processor.py` now persists `relationship_changes` to `state_log_data` even when the audit only returned `knowledge_map_updates` and no `actual_truth`
- `modules/core/stage4_post_processor.py:1162-1172` now extracts `relationship_changes` from `bible_delta` as `_relationship_payload` (parallel to `_inventory_payload`)
- `modules/core/stage4_post_processor.py:1186-1190` and `1222-1226` now merge `_relationship_payload` into WorldState and FactLedger update calls
- the full pipeline is: generation (dict format) → bible_delta → state_log → extraction → WorldState.update_from_state_changes() → FactLedger.update_from_state_changes() → persisted summary → re-injection via Stage 4 context_builder
- bounded implementation now also landed for `threat carry-over durable persistence`
- `modules/core/stage4_post_processor.py` now derives `active_pressure_vectors` from blueprint end-state signals (`ending_hook`, `cliffhanger`, `expected_ending`), normalizes cue terms, and persists them through `actual_truth`, `state_log_data`, and `bible_delta`
- `modules/core/stage4_post_processor.py` now extracts `active_pressure_vectors` from `bible_delta/state_changes` during atomic metadata save and merges them into `WorldState.update_from_state_changes()`
- `modules/core/world_state.py` now treats `active_pressure_vectors` as a first-class canonical surface, persists the current episode's unresolved pressure set, replays it on rollback, and surfaces `[지속 압박/위협]` in the canonical summary
- `modules/core/stage4_context_builder.py` now keeps `[지속 압박/위협]` visible even in the condensed world-state summary path used when Continuity Packet entities are already injected
- `modules/core/stage4_interview_round.py` now merges persisted `active_pressure_vectors` into `prev_hud` resolution even when `manuscript.hud_snapshot` wins source precedence, so the continuity validator sees the same durable threat surface
- `modules/validation/continuity_validator.py` now emits `threat_carryover_drift` warnings when the opening drops all persisted pressure cues from the prior episode
- preflight/validator severity evaluated: no code change needed — `inventory_count_drift` (WARNING) in continuity_validator handles count drift structurally; TF-49b preflight genre-tolerance is intentional; `RelDrift` advisory (MAJOR) is already operational in Stage 4 interview round L4573-4619
- targeted verification passed:
  - `tests/test_stage4_post_processor.py` -> `45 passed` (+1 new: `test_active_pressure_vectors_flow_into_state_log_bible_and_world_state`)
  - `tests/test_world_state_caps.py` + `tests/test_world_state_manager.py` -> `9 passed`
  - `tests/test_validation.py` -> `30 passed`
  - `tests/test_stage4_cv_context.py` -> `21 passed`
  - `tests/test_stage4_interview_round.py` -> `80 passed`
  - `tests/test_stage4_context_builder.py` -> `52 passed`
  - `python -m ruff check ...` on touched producer/sink/validator files -> `All checks passed`
- project-specific system remediation status: `relationship` and `threat` carry-over are both closed; only non-project-specific follow-ups remain

**PASS_WITH_FIX subfinding**
- highest-confidence local-fix candidates in `0_260316` are `ep4 round 0`, `ep4 round 1`, and `ep5 round 0`
- `ep5 round 2` remains outside aggressive `PASS_WITH_FIX`; it behaved like a frontier/state conflict, not a one-line correction
- a narrow `fixable_firewall` lane is now live; do not relax Firewall globally beyond that bounded subset

**Shared broken-feedback subfinding**
- companion system SSOT now treats `ai_slop` / `ced_score` as Director-mediated advisory routing rather than telemetry-only runtime-core signals; this document keeps that authority external
- `npc_drift` and `coverage_warning` are shared Stage 4 evidence, but their bundle-wide remediation authority is externalized
- `dialogue_ratio` style-target linkage is now landed in the companion system SSOT and remains out of scope for project recovery authority
- `open_review` must remain split between same-round retry handoff and dead sidecar replay; this document does not collapse those paths

**Engineering stance**
- operational decision: resume 가능
- project-specific engineering decision: **resolved** — relationship persistence and threat carry-over now both use persisted canonical substrates
- bundle-wide broken feedback remediation authority: companion system SSOT

## Acceptance Criteria

### Project Recovery Closure

- ep7 resumes from the existing frontier
- no extra DB repair or artifact cleanup is required beforehand
- continuation is clean, meaning no ep7 partial remnants had to be reconciled first

### Project-Specific System Remediation Status

- [x] stale arc/state material can no longer override Tier 1 truth — mandatory_context authority precedence landed
- [x] continuity uses a persisted previous snapshot instead of live HUD state — prev_hud persisted precedence landed
- [x] `2 vs 3 computers` class drift becomes structurally detectable — inventory_count_drift in continuity_validator
- [x] relationship carry-over survives as durable state — relationship_changes dict pipeline landed (format fix + state_log + WorldState + FactLedger extraction, plus `knowledge_map`-only state_log persistence)
- [x] threat carry-over survives as durable state — `active_pressure_vectors` now persists via `actual_truth/state_log/bible_delta/world_state`, re-enters Stage 4 mandatory context, and emits `threat_carryover_drift` warnings when opening continuity drops it
- [x] fixable-firewall local contradictions no longer force unnecessary outer rounds — fixable_firewall routing landed
- companion system SSOT tranche work starts only after a current-code validity check confirms the shared assumptions still match live code
- companion system SSOT tranche changes validate against `0_260316` without altering the project recovery facts above

## Open Items

| Item | Status | Impact |
| --- | --- | --- |
| exact interruption mechanism | open | medium |
| `vec0` missing impact on retrieval quality | open | medium |
| `sink_alignment_final_authority_contract` AttributeError | known open | low |

Notes:
- draft/artifact hash-size mismatch for ep1 and ep5 is treated as a non-corrupt formatting-level difference, not a governing open issue
- Stage 4 quality is accepted as good enough for recovery judgment, but not as evidence that the substrate is healthy

## Document Contract

- this is the single canonical decision document for `0_260316` recovery and regression authority
- it separates **fact**, **inference**, and **decision**
- it keeps project recovery and project-specific remediation in one place
- shared broken-feedback bundle items defer to the companion system SSOT for remediation priority
- it is intended to be sufficient for the next implementer or operator without additional arbitration over what is settled vs still open
