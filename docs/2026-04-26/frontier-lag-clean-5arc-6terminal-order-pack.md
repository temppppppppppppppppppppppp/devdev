# Frontier Lag Clean 5-Arc 6-Terminal Order Pack

Date: 2026-04-26
Status: final after embedded 3-pass audit
Document Type: system-track multi-terminal order pack
Canonical Path: `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
Temp Mirror: not applicable; this is an order pack, not an execution SSOT queue item
Baseline Commit: `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
Baseline Dirty Summary:
- `M 0_temp.txt`
- `?? docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `?? projects/0_골든카나리아/`

## 1. Purpose

This document is a self-contained order pack for six parallel Codex terminals.

The command objective is not immediate implementation. The objective is to make the next clean 5-arc Frontier Lag run feasible by producing evidence-backed designs for:

- why the previous run stopped
- whether session memory and context caching are actually applied
- how to prevent upstream-to-downstream continuity drift before it causes repeated retries
- how to record any continuity bridge in DB without letting Python decide narrative truth
- how to separate process success from objective success in unattended run reporting

## 2. Common Context For Every Terminal

Read these first:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md`
4. `docs/2026-04-25/stage234-session-memory-resume-context.md`
5. This order pack

Current known run facts:

- The live run process exited cleanly with exit code `0`.
- The requested objective was 5 arc advances.
- Actual result was `arcs_advanced=1`, `requested_limit_hit=false`, `stop_reason=stage3_user_abort`.
- The direct failure was Stage3 ep4 attempt 10.
- Stage3 ep4 was not a low-score failure. The Director-selected candidate had `PASS_WITH_FIX` and score `95`, but downstream binding/prevalidation ended with `FAILED`.
- The conflict was timeline authority drift: Blueprint candidate surface stayed around `2006년 1월 1일`, while the arc state required `2006년 1월 3일`.
- The terminal failed Stage3 attempt had no final artifact path/hash because unresolved binding issues blocked emergency fallback.
- The current system has Stage4 `session_memory_envelope` evidence, but Stage2/Stage3 do not currently carry the same envelope surface in the observed run.
- The current system has context-cache infrastructure and DB telemetry. In the observed run, explicit `context_cache_attempts` were logged, but all direct attempts were skipped as `content_too_short`; provider-level `llm_calls.cached_tokens` still showed some cached-token evidence.

Important local evidence surfaces:

- `projects/0_골든카나리아/project_data.db`
- `projects/0_골든카나리아/logs/auto_frontier_lag_worker_result.json`
- `projects/0_골든카나리아/logs/auto_frontier_lag_analysis.json`
- `projects/0_골든카나리아/logs/auto_frontier_lag_failure_digest.json`
- `projects/0_골든카나리아/logs/pass_rate_monitor.json`
- `projects/0_골든카나리아/logs/runtime_audit.jsonl`
- `projects/0_골든카나리아/logs/runtime_audit_summary.json`
- `projects/0_골든카나리아/logs/session_20260426_171125.log`
- `projects/0_골든카나리아/logs/session/decisions.jsonl`
- `projects/0_골든카나리아/logs/session/llm_io.jsonl`
- `projects/0_골든카나리아/plans/arcs/arc_002.txt`
- `projects/0_골든카나리아/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `modules/core/session_memory_envelope.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/db_bootstrap_runtime.py`
- `modules/core/db_manager.py`
- `main_a.py`
- `scripts/run_auto_frontier_lag_harness.py`

If a terminal sees mojibake in console output, do not patch Korean text from console rendering. Use byte-level UTF-8 reads or Python `Path.read_text(encoding="utf-8")`.

## 3. Non-Negotiable Governance

- Python collects, formats, and records evidence only. Python must not decide whether a narrative fact is right or wrong.
- Fact and continuity correction authority belongs to LLM/Director, not Python.
- Director remains final quality authority. Analyst, Chief Writer, validators, and automation may only surface evidence or proposals.
- Do not implement code changes unless explicitly assigned after the research/design phase.
- Do not treat provider-native memory or context cache as authoritative truth.
- Do not weaken validation merely to make a 5-arc run pass.
- Do not silently auto-edit factsheets, arcs, blueprints, or manuscripts.
- If a proposed bridge changes canonical story truth, it must be recorded as a proposal and submitted to Director authority.

## 4. Subagent Policy

Each terminal should use subagents by default when its environment supports them.

Minimum pattern:

- Spawn at least two subagents for independent sidecar checks.
- Keep one immediate blocking path local in the parent terminal.
- Do not duplicate subagent work with parent work unless verification is necessary.
- Require subagents to return concrete file paths, row keys, and line anchors.
- If subagents are unavailable, emulate with two local bounded passes and label them `local-pass-a` and `local-pass-b`.

Subagent prompts must include:

- the common context from sections 2 and 3
- the assigned terminal lane
- a strict read-only instruction unless implementation is explicitly assigned
- a requirement to distinguish evidence from inference

## 5. Shared Output Rules

Each terminal produces one lane report:

- Terminal 1: `docs/2026-04-26/frontier-lag-clean-5arc-lane-a-failure-forensics.md`
- Terminal 2: `docs/2026-04-26/frontier-lag-clean-5arc-lane-b-memory-cache-audit.md`
- Terminal 3: `docs/2026-04-26/frontier-lag-clean-5arc-lane-c-methodology-research.md`
- Terminal 4: `docs/2026-04-26/frontier-lag-clean-5arc-lane-d-continuity-bridge-design.md`
- Terminal 5: `docs/2026-04-26/frontier-lag-clean-5arc-lane-e-clean-harness-design.md`
- Terminal 6: `docs/2026-04-26/frontier-lag-clean-5arc-lane-f-governance-audit.md`

Each report should include:

- `Scope`
- `Evidence`
- `Findings`
- `Risks`
- `Recommendation`
- `Subagent Cross-Check`
- `3-Pass Mini Audit`

Do not create `docs/temp/` execution mirrors. Headquarters will synthesize a separate execution SSOT later if implementation is approved.

## 6. Terminal 1 Prompt - Lane A Failure Forensics

Copy this into Terminal 1:

```text
You are Terminal 1 / Lane A: Failure Forensics for the Frontier Lag clean 5-arc effort.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md
- docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md

Use subagents by default. Assign one subagent to DB/source lineage and one subagent to log/artifact lineage. Keep the immediate local task as the final contradiction map.

Task:
Trace exactly where the Stage3 ep4 Jan1 vs Jan3 contradiction entered and why it survived until attempt 10.

Required evidence:
- project_data.db stage_attempts row for Stage3 ep4 terminal failure
- director_selections for the same attempt key
- llm_io.jsonl and decisions.jsonl entries around Stage3 ep4
- pass_rate_monitor.json entry around Stage3 ep4
- runtime_audit.jsonl blueprint failure event
- Stage2 arc2 artifact and plans/arcs/arc_002.txt
- any Stage3 ep4 prompt/candidate surfaces that still exist

Output:
Write docs/2026-04-26/frontier-lag-clean-5arc-lane-a-failure-forensics.md.

Rules:
- Read-only. Do not patch code.
- Separate evidence from inference.
- Do not claim Python judged narrative truth; identify exactly which component recorded or routed each outcome.
- If raw candidates are missing, say so and identify the observability gap.
```

## 7. Terminal 2 Prompt - Lane B Memory And Cache Audit

Copy this into Terminal 2:

```text
You are Terminal 2 / Lane B: Session Memory and Context Cache Audit.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md
- docs/2026-04-25/stage234-session-memory-resume-context.md
- docs/2026-04-24/stage234-session-memory-fresh-reaudit-3pass-audit.md
- docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md

Use subagents by default. Assign one subagent to code/test surfaces and one subagent to the observed 5-arc DB/log telemetry. Keep the parent terminal responsible for the stage-by-stage verdict table.

Task:
Determine whether session memory and context caching are actually applied in the current main workspace and in the observed 5-arc run.

Required evidence:
- modules/core/session_memory_envelope.py
- Stage4 integration points in stage4_interview_round/stage4_orchestrator/stage4_reject_runtime
- BaseAgent context-cache implementation
- db_bootstrap_runtime/db_manager context-cache tables and save methods
- tests covering session memory and context cache
- observed run DB counts for stage_attempts.advisory_flags containing session_memory_envelope/cache_lineage
- observed run DB counts for context_cache_attempts and llm_calls.cached_tokens

Output:
Write docs/2026-04-26/frontier-lag-clean-5arc-lane-b-memory-cache-audit.md.

Rules:
- Read-only. Do not patch code.
- Classify each stage as applied, partially applied, not applied, or telemetry-only.
- Do not treat cache hits as story memory.
- Explicitly state whether memory/cache could have prevented the Jan1 vs Jan3 failure.
```

## 8. Terminal 3 Prompt - Lane C External Methodology Research

Copy this into Terminal 3:

```text
You are Terminal 3 / Lane C: External Methodology Research.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md

Use subagents by default. Assign one subagent to official OpenAI documentation and one subagent to primary papers. Keep the parent terminal responsible for mapping the findings back to this codebase.

Task:
Research external methodology for clean long-running LLM pipelines and convert it into practical principles for a clean 5-arc Frontier Lag run.

Allowed sources:
- Official OpenAI documentation for prompt caching, conversation state, and accuracy optimization
- Primary papers only for long-context and agent-memory methods

Required topics:
- prompt caching
- conversation state / previous-response style state
- evals and accuracy optimization
- Lost in the Middle
- Reflexion
- Generative Agents
- MemGPT
- Self-RAG

Output:
Write docs/2026-04-26/frontier-lag-clean-5arc-lane-c-methodology-research.md.

Rules:
- Use citations with URLs.
- Do not overfit to vendor-native hidden memory.
- Convert external advice into no more than seven workspace-applicable principles.
- Explicitly distinguish cost/latency caching from truth/continuity memory.
```

Reference starting points:

- OpenAI Prompt Caching: `https://platform.openai.com/docs/guides/prompt-caching`
- OpenAI Conversation State: `https://platform.openai.com/docs/guides/conversation-state`
- OpenAI Accuracy Optimization: `https://platform.openai.com/docs/guides/optimizing-llm-accuracy`
- Lost in the Middle: `https://arxiv.org/abs/2307.03172`
- Reflexion: `https://arxiv.org/abs/2303.11366`
- Generative Agents: `https://arxiv.org/abs/2304.03442`
- MemGPT: `https://arxiv.org/abs/2310.08560`
- Self-RAG: `https://arxiv.org/abs/2310.11511`

## 9. Terminal 4 Prompt - Lane D Continuity Bridge Design

Copy this into Terminal 4:

```text
You are Terminal 4 / Lane D: Continuity Bridge Design.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md
- docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md
- modules/core/session_memory_envelope.py

Use subagents by default. Assign one subagent to DB schema/telemetry design and one subagent to Director-authority workflow design. Keep the parent terminal responsible for the final bridge packet contract.

Task:
Design a continuity bridge packet that runs between upstream and downstream stages to prevent downstream accidents like Jan1 vs Jan3 before 10 retries are wasted.

Required design properties:
- Python collects and formats candidate contradictions only.
- LLM/Director decides whether a continuity bridge is valid.
- The bridge is preventive, not a license to silently rewrite story truth.
- All bridge proposals and applied decisions are DB-auditable.
- The packet is stage-agnostic enough for S2->S3 and S3->S4, but can start with the Stage3 ep4 timeline case.

Minimum packet fields:
- bridge_id
- source_stage
- target_stage
- work_id/project_id
- arc_num
- ep_num
- authority_source
- observed_downstream_candidate
- observed_conflict
- proposed_bridge
- allowed_fix_scope
- director_verdict
- director_reason
- applied_status
- applied_artifact_key
- created_at
- source_hashes

Output:
Write docs/2026-04-26/frontier-lag-clean-5arc-lane-d-continuity-bridge-design.md.

Rules:
- Read-only design only. Do not patch code.
- Include where the DB table or JSON payload would live.
- Include how this interacts with session_memory_envelope without replacing it.
- Include a Jan1 vs Jan3 worked example.
```

## 10. Terminal 5 Prompt - Lane E Clean Harness Design

Copy this into Terminal 5:

```text
You are Terminal 5 / Lane E: Clean 5-Arc Harness Design.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md
- docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md
- scripts/run_auto_frontier_lag_harness.py
- main_a.py
- tests/test_one_stop_frontier_lag_auto_continue.py

Use subagents by default. Assign one subagent to process/result semantics and one subagent to HIL policy/test coverage. Keep the parent terminal responsible for the final harness policy matrix.

Task:
Design how to make a clean 5-arc run unambiguous and operator-safe.

Required topics:
- Separate process_success from objective_success.
- Stop showing worker status success as if the requested 5-arc objective passed.
- Distinguish real operator stop from no-input/default stop.
- Define Stage3 failure policy options: stop, skip, quarantine.
- Define strict-quality run vs survey-run behavior.
- Define final analyzer root-cause naming.

Output:
Write docs/2026-04-26/frontier-lag-clean-5arc-lane-e-clean-harness-design.md.

Rules:
- Read-only design only. Do not patch code.
- Preserve strict default behavior unless the design explicitly introduces an opt-in survey policy.
- Do not weaken Director/validation authority for throughput.
- Include test cases that should exist before implementation.
```

## 11. Terminal 6 Prompt - Lane F Governance Audit

Copy this into Terminal 6:

```text
You are Terminal 6 / Lane F: Adversarial Governance Audit.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md
- docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md

Use subagents by default. Assign one subagent to Python-vs-LLM authority risk and one subagent to persistence/factsheet mutation risk. Keep the parent terminal responsible for the final P0-P3 risk classification.

Task:
Adversarially audit the proposed clean 5-arc direction before implementation.

Required questions:
- Could a continuity bridge accidentally make Python the narrative judge?
- Could a bridge packet silently become a factsheet auto-edit?
- Could Director authority be bypassed by prevalidation, cache, or harness policy?
- Could skip/quarantine policy hide real quality failures?
- Could DB telemetry make advisory evidence look authoritative?
- Could session memory or context cache introduce stale cross-run truth?

Output:
Write docs/2026-04-26/frontier-lag-clean-5arc-lane-f-governance-audit.md.

Rules:
- Read-only audit only. Do not patch code.
- Use P0-P3 severity labels.
- Include mitigations for every P0-P2 risk.
- End with a go/no-go recommendation for creating an execution SSOT.
```

## 12. Headquarters Synthesis After All Six Reports

After all six lane reports exist, Headquarters should synthesize one execution SSOT only if the combined evidence reaches at least 95% confidence.

Expected execution SSOT candidates:

- `docs/2026-04-26/frontier-lag-continuity-bridge-execution-ssot.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-harness-execution-ssot.md`

Likely implementation order if approved:

1. Add terminal failed-attempt diagnostic snapshot for Stage3 failures.
2. Add `process_success` vs `objective_success` result semantics.
3. Add HIL decision source telemetry.
4. Add continuity bridge packet DB schema and read-only proposal generation.
5. Add Director bridge adjudication before repeated downstream retries.
6. Run focused tests.
7. Run one bounded fresh Frontier Lag validation.

Do not implement from this order pack directly. Implement only after the synthesized execution SSOT passes its own 3-pass audit.

## 13. Embedded 3-Pass Mini Audit

Pass 1 - structure and scope: PASS.

The document is an order pack, not an execution SSOT. It includes common context, lane ownership, output paths, prompts, source surfaces, and boundaries. It does not create a temp queue artifact.

Pass 2 - evidence and consistency: PASS.

The known facts match the observed post-run audit and local telemetry already inspected: process exit success, objective failure, Stage3 ep4 timeline contradiction, partial session-memory application, and context-cache telemetry with skipped direct attempts plus provider cached tokens.

Pass 3 - execution readability: PASS.

Each terminal has a copyable prompt, required read order, subagent policy, report path, and non-implementation boundary. Headquarters synthesis is explicitly deferred until all lane reports exist.

Estimated confidence: 96%.
