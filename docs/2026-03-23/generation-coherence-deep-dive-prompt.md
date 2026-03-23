System-track survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/2026-03-23/daily-roadmap-2026-03-23.md
4. docs/2026-03-23/generation-coherence-deep-dive-order.md
5. docs/2026-03-23/llm-codebase-orientation-pack.md
6. docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md
7. docs/2026-03-23/fresh-run-3pass-audit-report.md

Task:
Run the Generator / Coherence deep-dive lane for the 7-axis framework.

Primary goal:
Audit whether the generation pipeline succeeds on first pass, preserves cross-episode coherence, retrieves selectively, and receives the right context before generation.

Hard constraints:
- This is survey-only. Do not patch code.
- Do not drift into Director verdict internals unless directly required by a generator-side context-gap claim.
- Do not reopen the long-function campaign based only on file size.
- Prefer live workspace evidence over stale survey claims.
- Fresh run already exists. Use it as supporting evidence, not as a reason to redesign the scope.

Scope:
- modules/domain/agents/chief_writer.py
- modules/domain/agents/arc_ensemble.py
- modules/domain/agents/blueprint_ensemble.py
- modules/domain/agents/chief_writer_context_packets.py
- modules/core/world_state.py
- modules/core/fact_ledger.py
- modules/domain/agents/continuity_arc.py
- modules/validation/continuity_validator.py
- modules/domain/agents/state_tracker.py
- modules/core/vec_memory.py
- modules/core/stage4_context_builder.py
- modules/core/stage4_context_packets.py
- modules/core/context_advisor.py

Covered axes:
- Q1. 잘 쓰냐
- Q5. 잘 기억하냐
- Q6. 잘 찾냐
- Q7. 잘 받냐
  - Generator-side only

Required method:
1. Generation quality topology
- Map first-pass generation flow across:
  - ChiefWriter
  - Arc ensemble
  - Blueprint ensemble
- Identify where diversity, reuse, or prompt context can collapse before Director review.

2. Coherence and memory integrity
- Trace long-horizon coherence through:
  - WorldState
  - FactLedger
  - continuity validators and inspectors
  - NPC and state tracker paths
- Identify where contradictions can evade detection or where memory updates can drift.

3. Selective retrieval and context reception
- Map retrieval stores and routing decisions.
- Confirm generator-side context injection completeness:
  - mandatory context
  - tier packets
  - lookback tiers
  - previous manuscript summaries
  - context advisor decisions
- Flag over-retrieval, under-retrieval, field loss, or truncation hazards.

Output:
Write the final lane report to:
docs/2026-03-23/generation-coherence-deep-dive-report.md

Mandatory report structure:
1. Executive Summary
2. First-Pass Generation Quality Map
3. Coherence / Memory Ownership Map
4. Selective Retrieval Routing Map
5. Generator Context Reception Map
6. Top Hotspots
7. Quick Wins
8. Refactor Candidates
9. Confidence And Limits

For every meaningful hotspot include:
- file path
- line anchor
- affected axis
- severity: P0 / P1 / P2
- why it is costly or risky
- recommended fix type:
  - comment-only
  - doc-only
  - observability-only
  - boundary-refactor
  - contract-cleanup
  - ignore

Acceptance criteria:
- every P0/P1 issue has a file and line anchor
- generator-side Q7 findings are separated from Director-side context findings
- retrieval routing is explicitly described
- coherence ownership is explicitly mapped across state surfaces
- stale findings already fixed in live code are explicitly called out as stale, not reopened
- include a confidence score
- apply 3-pass audit before final save

After writing the report, run:
- python scripts/check_utf8_hygiene.py docs/2026-03-23/generation-coherence-deep-dive-report.md
- python scripts/ops_validator.py

In your final response to me:
- summarize P0/P1 findings first
- then state whether generator/coherence ownership is readable
- then give confidence
- then list the highest-ROI next actions
- keep it concise and factual
