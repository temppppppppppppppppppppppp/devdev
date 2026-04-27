# Stage4 POST_SELECT_CONFLICT Parallel Investigation Dispatch

Date: 2026-04-27
Status: final after 3-pass document audit
Workspace: `C:\Users\wjjo\Desktop\글도비`
Repository: `temppppppppppppppppppppppp/devdev`
GitHub Issue: [#58 `[Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs`](https://github.com/temppppppppppppppppppppppp/devdev/issues/58)
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Baseline dirty summary: dirty only from pre-existing untracked documentation path `docs/2026-04-27/security-parallel-investigation/`; no tracked source dirty state was observed before creating this dispatch.
Document type: read-only parallel investigation order, not an execution SSOT and not a source-code patch order.
Temp queue policy: do not mirror this document into `docs/temp/`; create an execution SSOT later only after the terminal reports are synthesized.

## 1. Problem Frame

#58 tracks a concrete Stage4 bug shape:

- Stage4 is no longer primarily dying from process/runtime failure.
- The active blocker is repeated downstream continuity/history drift.
- The visible symptom is repeated `POST_SELECT_CONFLICT` rejects during 5-arc runs.
- The suspected root surfaces are Stage3/Stage4 handoff, context-cache, session/vector memory, persisted retry hydration, continuity authority packets, and stale or duplicated carryover into Stage4.

This wave is investigation only. It must not patch code, rewrite docs, restart a 5-arc run, mutate DBs, close GitHub issues, or create PRs.

## 2. Source Evidence

GitHub issue #58 states:

- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:79-93` shows Stage4 `ep9` stopped after two `POST_SELECT_CONFLICT` rejects and no PASS persisted.
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:121` names continuity carryover as the active Stage4 bottleneck.
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md:78-107` records the earlier Jan1/Jan3-style timeline contradiction failure shape.
- `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md:690-705` leaves T6/T7 continuity authority needing fresh multi-arc proof.

Direct local evidence confirmed for dispatch:

- Stage4 current live status:
  - `ep4`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep5`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep6`: `REJECT:LOGIC_ERROR | REJECT:CONSTRAINT_VIOLATION | REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep7`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep8`: `REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep9`: `REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT`
- The handoff explicitly interprets the current bottleneck as repeated carryover mistakes such as institution naming and duplicated continuation beats.
- Memory/cache transport was active in that run, but the handoff explicitly says this proves transport only, not final quality success.
- Existing stabilization docs say session memory and context caching are helper telemetry/performance systems, not the authority carrier for Jan1/Jan3-class drift.

## 3. Priority Shape

Run all ten terminals if possible. If fewer terminals are available, dispatch in this order:

1. T01 current-run forensic baseline.
2. T02 post-select conflict classifier and authority route.
3. T03 Stage3-to-Stage4 handoff and context packet lineage.
4. T04 continuity authority carrier audit.
5. T06 previous-attempt hydration and retry replay audit.
6. T08 focused regression gap design.
7. T05 memory/cache side-effect audit.
8. T07 context-cache lineage and stale source suppression audit.
9. T09 artifact truth and narrative contradiction sample audit.
10. T10 synthesis and execution-readiness map.

## 4. Global Rules For All Terminals

All terminals must follow these rules:

- Read `AGENTS.md` first enough to respect system-track, Director authority, UTF-8, Python-judgment limits, and pytest memory rules.
- Treat this as read-only investigation.
- Do not edit production code, tests, configs, docs outside your assigned report, DBs, GitHub issues, commits, branches, or PRs.
- The only allowed write is your assigned report path under `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`.
- Use UTF-8 for the report.
- Python and shell may collect facts, query DBs read-only, format evidence, and count rows. The LLM investigator must make the risk/meaning judgment.
- Do not let Python canaries become final narrative judgment. Canaries and tests are tripwires for Director review.
- Do not claim clean 5-arc readiness.
- Treat session memory, vector memory, and context cache as helper evidence unless code/docs prove a narrower authority contract.
- If inspecting generated manuscripts, blueprints, logs, or DB rows, cover artifact truth, metadata truth, and narrative truth separately.
- Do not bulk-open huge logs when narrower queries or filtered reads are enough.
- If running tests at all, run targeted low-memory shards only, never broad parallel pytest.

Required report schema:

```md
# TXX Report Title

## Scope

## Commands / Evidence

## Findings

## Root-Cause Candidates

## Regression / Test Candidates

## Dependencies On Other Terminals

## Open Questions

## Closure Recommendation
```

## 5. Terminal Dispatch Matrix

| Terminal | Focus | Primary Issue Surface | Save Path |
| --- | --- | --- | --- |
| T01 | Current-run forensic baseline | DB/log attempt rows and #58 evidence anchor | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-01-current-run-forensics.md` |
| T02 | Post-select conflict route | `POST_SELECT_CONFLICT` classification, Director/runtime route, reject persistence | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-02-postselect-conflict-route.md` |
| T03 | Stage3-to-Stage4 handoff | Stage3 output, Stage4 context packets, source lineage, episode boundary | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-03-stage3-stage4-handoff.md` |
| T04 | Continuity authority carriers | authoritative projection, pins, canaries, validators, state arbiter | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-04-continuity-authority-carriers.md` |
| T05 | Memory/cache helper side effects | session/vector memory writes, context advisor/compression, post-pass memory | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-05-memory-cache-side-effects.md` |
| T06 | Retry and previous-attempt hydration | persisted failed attempts, same-session filtering, retry feedback, prior-failure replay | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-06-retry-hydration-replay.md` |
| T07 | Context-cache lineage | cached context source lineage, stale cache suppression, BaseAgent/director caching | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-07-context-cache-lineage.md` |
| T08 | Regression gap design | institution naming drift, duplicated continuation beats, date drift, prior-failure replay tests | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-08-regression-gap-design.md` |
| T09 | Artifact truth sample | ep4-ep9 artifacts, blueprint/manuscript/attempt linkage, narrative contradiction samples | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-09-artifact-truth-samples.md` |
| T10 | Synthesis | merge T01-T09 into root-cause and execution-readiness map | `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-10-synthesis-map.md` |

## 6. Copy-Paste Prompts

### Prompt T01

```text
You are Terminal T01 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-01-current-run-forensics.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and Python-judgment rules.
- Read-only investigation only. Do not edit source, docs except your report, DBs, GitHub, or git state.
- Python may collect/query/format evidence, but you must make the interpretation.
- Do not claim clean 5-arc readiness.

Scope:
- Establish the factual current-run baseline behind #58.
- Inspect docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md, docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md, docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md.
- Locate the target project DB/log/artifact paths referenced by those docs, especially current run Stage4 ep4-ep9 attempt rows.
- If querying SQLite, open read-only and extract only attempt metadata needed for POST_SELECT_CONFLICT sequence, episode, attempt, verdict, reason, session id, timestamps, and available artifact pointers.
- Do not mutate DB files.

Suggested commands:
- python - <<'PY' with pathlib/sqlite3 read-only queries if DB path is found.
- git grep -n -i -E "POST_SELECT_CONFLICT|ep9|continuity carryover|context_cache_attempts|VecMem" -- docs/2026-04-27 docs/2026-04-26
- Get-ChildItem -Recurse -File projects -Filter project_data.db -ErrorAction SilentlyContinue | Select-Object -First 20 FullName

Report schema:
# T01 Current-Run Forensic Baseline
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T02

```text
You are Terminal T02 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-02-postselect-conflict-route.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and Python-judgment rules.
- Read-only investigation only. Do not edit source, docs except your report, DBs, GitHub, or git state.
- Do not let Python/post-select become final narrative judge in your recommendation.

Scope:
- Map where `POST_SELECT_CONFLICT` is produced, normalized, persisted, and surfaced to operators.
- Inspect at minimum: modules/core/stage4_postselect_runtime.py, modules/core/stage4_outcome_runtime.py, modules/core/stage4_reject_runtime.py, modules/core/stage4_interview_round.py, modules/core/stage4_orchestrator.py, modules/core/stage4_types.py, modules/core/db_manager.py, tests/test_stage4_orchestrator.py, tests/test_stage4_interview_round.py.
- Determine whether POST_SELECT_CONFLICT is detecting stale carryover correctly, over-triggering, or masking a more specific failure family.
- Identify authority layers: Director verdict, post-select route, runtime rejection, persisted attempt row, final settlement.

Suggested commands:
- git grep -n -i -E "POST_SELECT_CONFLICT|post_select|postselect|reject_reason|runtime_route|Director|stage_attempt|record_s4_attempt" -- modules/core tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py
- python -m py_compile modules/core/stage4_postselect_runtime.py modules/core/stage4_outcome_runtime.py modules/core/stage4_reject_runtime.py modules/core/stage4_interview_round.py modules/core/stage4_orchestrator.py

Report schema:
# T02 Post-Select Conflict Route
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T03

```text
You are Terminal T03 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-03-stage3-stage4-handoff.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and Python-judgment rules.
- Read-only investigation only. Do not edit source, docs except your report, DBs, GitHub, or git state.

Scope:
- Audit Stage3-to-Stage4 handoff and context packet lineage.
- Inspect at minimum: modules/core/stage3_context.py, modules/core/stage3_envelope_builder.py, modules/core/stage3_orchestrator.py, modules/core/stage4_context.py, modules/core/stage4_context_builder.py, modules/core/stage4_context_packets.py, modules/domain/agents/stage3_prompt_envelope.py, modules/domain/agents/stage3_retry_coordinator.py, modules/domain/agents/three_phase_blueprint_runtime.py.
- Determine whether stale arcs, stale blueprint state, old treatment/genre context, or wrong episode boundary can enter Stage4.
- Pay special attention to source-lineage checks, ordinal indexing, episode id/arc id boundaries, and fallback paths when Stage3 has prior failed attempts.

Suggested commands:
- git grep -n -i -E "lineage|source|episode|arc|blueprint|handoff|previous|retry|context|plot_roadmap|stale|cache" -- modules/core/stage3* modules/core/stage4_context* modules/domain/agents/stage3* modules/domain/agents/three_phase_blueprint_runtime.py tests/test_stage4_context_builder.py tests/test_stage2_stage3_episode_boundary_guardrail.py tests/test_stage2_stage3_semantic_carryover_guardrail.py

Report schema:
# T03 Stage3-To-Stage4 Handoff
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T04

```text
You are Terminal T04 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-04-continuity-authority-carriers.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and Python-judgment rules.
- Read-only investigation only. Do not edit source, docs except your report, DBs, GitHub, or git state.
- Remember: session memory and context cache are helper evidence, not authority carriers unless a narrower contract proves otherwise.

Scope:
- Map the authoritative continuity carriers that should prevent date, institution, continuation-beat, and prior-state drift.
- Inspect at minimum: modules/core/authoritative_continuity_projection.py, modules/core/continuity_canary.py, modules/core/continuity_pin_guard.py, modules/core/episode_state_arbiter.py, modules/core/stage4_immutable_fact_contract.py, modules/validation/continuity_validator.py, modules/domain/agents/continuity_arc.py, modules/domain/agents/continuity_blueprint.py, modules/domain/agents/continuity_inspector.py, modules/domain/agents/continuity_manuscript.py, modules/domain/agents/continuity_tracker.py, modules/domain/agents/director_continuity.py.
- Determine which continuity truth should be authoritative at Stage4 and whether Stage4 actually consumes it.

Suggested commands:
- git grep -n -i -E "authoritative|continuity|pin|immutable|state|date|institution|location|carry|projection|arbiter|validator|Director" -- modules/core/authoritative_continuity_projection.py modules/core/continuity* modules/core/episode_state_arbiter.py modules/core/stage4_immutable_fact_contract.py modules/validation modules/domain/agents/continuity* modules/domain/agents/director_continuity.py tests/test_authoritative_continuity_projection.py tests/test_continuity_canary.py tests/test_continuity_pin_guard.py tests/test_continuity_validator.py

Report schema:
# T04 Continuity Authority Carriers
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T05

```text
You are Terminal T05 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-05-memory-cache-side-effects.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and Python-judgment rules.
- Read-only investigation only. Do not edit source, docs except your report, DBs, GitHub, or git state.
- Do not promote memory/cache helper evidence into final narrative authority.

Scope:
- Audit session/vector memory and context-helper side effects that can influence future Stage4 context.
- Inspect at minimum: modules/core/session_memory_envelope.py, modules/core/vec_memory.py, modules/core/context_advisor.py, modules/core/context_compression.py, modules/core/narrative_context_formatter.py, modules/core/stage4_post_pass_runtime.py, modules/core/stage4_post_processor.py, modules/core/session_logger.py, tests/test_session_memory_envelope.py, tests/test_vec_memory.py, tests/test_memory_benchmark.py.
- Identify whether rejected, partially settled, stale, or cross-session content can enter memory/cache and later influence Stage4.
- Separate memory write timing from memory read/use timing.

Suggested commands:
- git grep -n -i -E "memor|VecMem|session|cache|context|retrieve|fallback|settled|reject|episode_meta|delete_episodes_from|stage4" -- modules/core/session_memory_envelope.py modules/core/vec_memory.py modules/core/context_advisor.py modules/core/context_compression.py modules/core/narrative_context_formatter.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py modules/core/session_logger.py tests/test_session_memory_envelope.py tests/test_vec_memory.py tests/test_memory_benchmark.py

Report schema:
# T05 Memory And Cache Side Effects
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T06

```text
You are Terminal T06 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-06-retry-hydration-replay.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and Python-judgment rules.
- Read-only investigation only. Do not edit source, docs except your report, DBs, GitHub, or git state.

Scope:
- Audit retry loops, previous-attempt hydration, and prior-failure replay paths.
- Inspect at minimum: modules/core/stage4_interview_round.py, modules/core/stage4_retry_runtime.py, modules/core/stage4_reject_runtime.py, modules/core/stage4_orchestrator.py, modules/core/db_manager.py, modules/core/failure_analyzer.py if present, tests/test_stage4_interview_round.py, tests/test_stage4_retry_runtime.py if present, tests/test_stage4_handoff_carryover_guardrail.py, tests/test_stage4_carryover_ceiling_handoff.py, tests/test_stage4_ep9_remediation.py.
- Determine whether failed attempts, rejection feedback, stale previous attempts, or same-episode rows from another session can be rehydrated into a new attempt.
- Specifically look for prior-failure replay that could cause duplicated continuation beats or repeated institution naming drift.

Suggested commands:
- git grep -n -i -E "previous_attempt|hydrate|retry|feedback|reject|same episode|session|attempt|carryover|POST_SELECT_CONFLICT|prior" -- modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py modules/core/stage4_reject_runtime.py modules/core/stage4_orchestrator.py modules/core/db_manager.py tests/test_stage4_interview_round.py tests/test_stage4_handoff_carryover_guardrail.py tests/test_stage4_carryover_ceiling_handoff.py tests/test_stage4_ep9_remediation.py

Report schema:
# T06 Retry Hydration And Prior-Failure Replay
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T07

```text
You are Terminal T07 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-07-context-cache-lineage.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and Python-judgment rules.
- Read-only investigation only. Do not edit source, docs except your report, DBs, GitHub, or git state.

Scope:
- Audit context-cache lineage and stale-source suppression.
- Inspect at minimum: modules/domain/agents/base_agent.py if tracked, modules/domain/agents/director_caching.py, modules/core/stage0_handoff.py, modules/core/stage4_context_packets.py, modules/core/stage4_context_builder.py, modules/core/stage3_orchestrator.py, modules/core/stage2_orchestrator.py, tests/test_base_agent.py, tests/test_audit_stage34_cache_gate_corpus.py, tests/test_audit_stage34_cache_proof.py, scripts/audit_stage34_cache_gate_corpus.py, scripts/audit_stage34_cache_proof.py.
- Determine whether cached prompt/context content can bypass updated lineage after Stage2/Stage3/Stage4 state changes.
- Identify if context cache might reintroduce stale institution names, old dates, or old continuation beats.

Suggested commands:
- git ls-files modules/domain/agents/base_agent.py modules/domain/agents/director_caching.py modules/core/stage0_handoff.py modules/core/stage4_context_packets.py modules/core/stage4_context_builder.py modules/core/stage3_orchestrator.py modules/core/stage2_orchestrator.py tests/test_base_agent.py scripts/audit_stage34_cache_gate_corpus.py scripts/audit_stage34_cache_proof.py
- git grep -n -i -E "cache|cached_context|lineage|source|stale|fingerprint|bypass|evict|context_cache|cachedContents|stage4" -- modules/domain/agents modules/core/stage0_handoff.py modules/core/stage4_context_packets.py modules/core/stage4_context_builder.py modules/core/stage3_orchestrator.py modules/core/stage2_orchestrator.py tests/test_base_agent.py scripts/audit_stage34_cache_gate_corpus.py scripts/audit_stage34_cache_proof.py

Report schema:
# T07 Context-Cache Lineage
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T08

```text
You are Terminal T08 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-08-regression-gap-design.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, Python-judgment, and pytest memory rules.
- Read-only investigation only. Do not edit source/tests/docs except your report.
- You may propose tests, but do not implement them.

Scope:
- Design focused regression candidates for #58.
- Inspect existing tests around Stage4 carryover, context, continuity, post-select, ep9 remediation, memory/cache, and Stage3/Stage4 boundaries.
- At minimum inspect: tests/test_stage4_handoff_carryover_guardrail.py, tests/test_stage4_carryover_ceiling_handoff.py, tests/test_stage4_ep9_remediation.py, tests/test_stage4_context_builder.py, tests/test_stage4_preflight_continuity.py, tests/test_stage2_stage3_episode_boundary_guardrail.py, tests/test_stage2_stage3_semantic_carryover_guardrail.py, tests/test_authoritative_continuity_projection.py, tests/test_continuity_pin_guard.py, tests/test_session_memory_envelope.py.
- Map existing coverage to four requested bug shapes: institution naming drift, duplicated continuation beats, date drift, and prior-failure replay.
- Recommend exact new test names, fixtures, and target modules without editing files.

Suggested commands:
- git grep -n -i -E "institution|date|continuation|carryover|previous|retry|POST_SELECT_CONFLICT|stale|session|lineage|ep9|continuity" -- tests/test_stage4_handoff_carryover_guardrail.py tests/test_stage4_carryover_ceiling_handoff.py tests/test_stage4_ep9_remediation.py tests/test_stage4_context_builder.py tests/test_stage4_preflight_continuity.py tests/test_stage2_stage3_episode_boundary_guardrail.py tests/test_stage2_stage3_semantic_carryover_guardrail.py tests/test_authoritative_continuity_projection.py tests/test_continuity_pin_guard.py tests/test_session_memory_envelope.py

Report schema:
# T08 Regression Gap Design
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T09

```text
You are Terminal T09 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-09-artifact-truth-samples.md

Rules:
- Read AGENTS.md first enough to follow system-track, Director authority, UTF-8, and artifact truth rules.
- Read-only investigation only. Do not edit source, generated artifacts, DBs, GitHub, or git state.
- If generated artifacts contain long creative text, quote only tiny excerpts needed to prove contradiction shape and otherwise summarize.

Scope:
- Inspect actual artifact truth for representative Stage4 POST_SELECT_CONFLICT episodes, ideally ep4-ep9 from the current GCP/Vertex handoff.
- Find the relevant project folder, DB rows, artifact paths, selected/rejected candidate texts, final manuscripts, blueprints, and settlement JSON if present.
- Build a small evidence table across:
  - artifact truth: file exists, UTF-8 decodes, hash/size if useful;
  - metadata truth: DB/log/summary row points to the artifact;
  - narrative truth: visible contradiction type, such as institution name drift, duplicated continuation beat, date drift, or prior-failure replay.
- Do not overclaim from one sample.

Suggested commands:
- Get-ChildItem -Recurse -File projects -ErrorAction SilentlyContinue | Select-String -Pattern "ep_0009|ep9|POST_SELECT_CONFLICT" -List
- Get-ChildItem -Recurse -File projects -Include "*ep_0009*","*rejected*","*selected*","*blueprint*" -ErrorAction SilentlyContinue | Select-Object -First 200 FullName,Length
- Use Python pathlib with explicit UTF-8 decode for any text artifact you cite.

Report schema:
# T09 Artifact Truth Samples
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T10

```text
You are Terminal T10 for the 글도비 #58 Stage4 POST_SELECT_CONFLICT parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Save your report to: docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-10-synthesis-map.md

Rules:
- Read AGENTS.md first enough to follow system-track, document, UTF-8, and Director authority rules.
- Read-only investigation only. Do not edit source, GitHub, git state, or reports from other terminals.
- You may read T01-T09 reports if present. Do not wait indefinitely if they are absent.
- Do not create an execution SSOT. Produce a synthesis map only.

Scope:
- Build a synthesis map for #58 from issue body, source docs, and any available T01-T09 reports.
- If T01-T09 are absent, create a pending-evidence matrix with the expected decision each terminal should unlock.
- Classify likely root-cause families:
  - Stage3/Stage4 handoff lineage failure;
  - continuity authority not consumed or not specific enough;
  - stale context-cache injection;
  - session/vector memory side-effect pollution;
  - previous-attempt hydration or retry feedback replay;
  - post-select classifier over-broadness;
  - actual artifact-level narrative contradiction not represented in structured state.
- Recommend whether the next step should be execution SSOT, additional survey, targeted tests first, or a fresh live-run proof gate.

Suggested commands:
- Get-ChildItem docs/2026-04-27/stage4-post-select-conflict-parallel-investigation -Force
- git grep -n -i -E "POST_SELECT_CONFLICT|carryover|continuity|session memory|context cache|stage4" -- docs/2026-04-26 docs/2026-04-27

Report schema:
# T10 #58 Synthesis Map
## Scope
## Commands / Evidence
## Findings
## Root-Cause Candidates
## Regression / Test Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

## 7. Merge Plan After Terminal Reports

After T01-T10 complete:

1. Collect all terminal reports from `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`.
2. Create a consolidated #58 survey or execution-readiness document in `docs/2026-04-27/`.
3. If implementation is warranted, create a canonical execution SSOT using `docs/implementation/execution-ssot-template.md`.
4. Only after that execution SSOT passes the document 3-pass audit at 95%+ confidence, mirror it into `docs/temp/`.
5. If multiple temp execution SSOT mirrors exist, update or create the aggregate roadmap before implementation.
6. GitHub issue #58 should receive milestone comments only at investigation completion, execution SSOT creation, PR creation, blocker discovery, and closure. Do not comment on every temp or local report update.

## 8. Non-Goals

- No source-code changes.
- No test implementation.
- No GitHub issue closure.
- No 5-arc live run restart.
- No DB mutation.
- No `docs/temp` execution mirror.
- No claim that #58 is fixed or that #57 is ready.

## 9. 3-Pass Document Audit

Pass 1 - structure and scope:

- PASS. The document is a parallel investigation dispatch, not an execution SSOT.
- PASS. #58 scope is explicit and bounded to Stage4 POST_SELECT_CONFLICT carryover drift.
- PASS. Ten terminals have unique report paths and non-overlapping primary scopes.
- PASS. `docs/temp` behavior is explicit: no mirror for this investigation-only dispatch.

Pass 2 - evidence and consistency:

- PASS. GitHub issue #58 body was fetched directly through the GitHub connector.
- PASS. Referenced source docs were read from the live workspace with explicit UTF-8 decoding for line evidence.
- PASS. Local code/test surfaces were discovered from tracked files and bounded grep output.
- PASS. This dispatch does not claim a fix, a root cause, or clean 5-arc readiness.

Pass 3 - execution and readability:

- PASS. Each prompt is copy-paste ready with scope, rules, suggested commands, and report schema.
- PASS. Reports write to separate files, avoiding parallel write conflicts.
- PASS. The merge plan describes how investigation can later promote into execution SSOT without polluting `docs/temp`.

Estimated operational confidence: 96%.

