System-track survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/2026-03-23/daily-roadmap-2026-03-23.md
4. docs/2026-03-23/director-verdict-deep-dive-order.md
5. docs/2026-03-23/llm-codebase-orientation-pack.md
6. docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md
7. docs/2026-03-23/fresh-run-3pass-audit-report.md

Task:
Run the Director-side deep-dive lane for the 7-axis framework.

Primary goal:
Audit whether the Director pipeline judges correctly, preserves verdict rationale, forwards fix and retry feedback coherently, and receives the right context at decision time.

Hard constraints:
- This is survey-only. Do not patch code.
- Do not drift into generator-quality or retrieval-quality analysis unless directly required by a Director-side feedback-loss claim.
- Do not reopen the long-function campaign based only on file size.
- Prefer live workspace evidence over stale survey claims.
- Fresh run already exists. Use it as supporting evidence, not as a reason to redesign the scope.

Scope:
- modules/core/stage4_director_runtime.py
- modules/domain/agents/director_ensemble.py
- modules/domain/agents/director_auditor.py
- modules/core/stage4_interview_round.py
- modules/core/stage4_retry_runtime.py
- modules/core/stage4_reject_runtime.py
- modules/domain/agents/four_phase_arc_runtime.py

Covered axes:
- Q2. 잘 고치냐
- Q3. 잘 판단하냐
- Q4. 잘 설명하냐
- Q7. 잘 받냐
  - Director-side only

Required method:
1. Verdict topology
- Map authoritative owner for:
  - candidate selection
  - PASS / PASS_WITH_FIX / REJECT verdict
  - score and gate basis
  - fix scope and retry instructions
- Separate owner shell from semantic core.

2. Feedback and retry trace
- Trace:
  - reject reason
  - verdict reason
  - fix scope
  - contradiction reasoning
  - retry feedback
from producer to consumer.
- Flag lossy transformation, silent truncation, field renaming, or explanation collapse.

3. Director context reception
- Confirm required Director-side context bundle is actually received.
- Inspect:
  - director input pack assembly
  - advisory joins
  - previous-manuscript expansion
  - validation-result joins
- Flag missing, reordered, or low-priority-important fields.

Output:
Write the final lane report to:
docs/2026-03-23/director-verdict-deep-dive-report.md

Mandatory report structure:
1. Executive Summary
2. Verdict Ownership Map
3. Gate Basis / Override Map
4. Fix / Retry Feedback Flow
5. Director Context Reception Map
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
- verdict ownership is explicitly mapped
- fix/retry chain is explicitly mapped
- Director-side Q7 findings are separated from generator-side context findings
- stale findings already fixed in live code are explicitly called out as stale, not reopened
- include a confidence score
- apply 3-pass audit before final save

After writing the report, run:
- python scripts/check_utf8_hygiene.py docs/2026-03-23/director-verdict-deep-dive-report.md
- python scripts/ops_validator.py

In your final response to me:
- summarize P0/P1 findings first
- then state whether Director verdict ownership is readable
- then give confidence
- then list the highest-ROI next actions
- keep it concise and factual
