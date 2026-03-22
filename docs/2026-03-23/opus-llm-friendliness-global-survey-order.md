Date: 2026-03-23
Status: final (3-pass audited, order scope)
Document Type: system-track survey order
Canonical Path: `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md`

Commit State:
- Baseline Commit: `203b328fb35633f9a23fe986862994c8b6dddab7`
- Baseline Dirty Summary: `dirty: 16 tracked, 3 untracked; hotspots: stage0/stage01 helpers, stage2/stage3/stage4 observability edits, tests, docs/2026-03-23/, .tmp_stage0_msg/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose
- Define a bounded Opus survey order for codebase-wide `LLM friendliness`, not general code quality.
- Evaluate whether the current production codebase is easy for an LLM to navigate, reason about, and modify safely after the long-function reduction campaign.
- Produce a ranked backlog of understanding hotspots without patching code during the survey.

This order is about comprehension cost, not stylistic polish.

## 2. Primary Questions
1. Can an LLM find the correct entry file and read order without replaying project history?
2. Can an LLM identify the authoritative owner for verdict, persistence, and operator-visible state quickly?
3. Are common contracts and payloads understandable without opening an excessive number of files?
4. Can an LLM follow console, audit, DB, and metrics sinks to explain `what happened` and `why`?
5. Are there high-friction areas where comments, naming, or tiny doc maps would help more than further refactor?

## 3. Scope
Included production areas:
- `main_a.py`
- `modules/core/**/*.py`
- `modules/domain/agents/**/*.py`
- `modules/validation/**/*.py`
- `modules/api/**/*.py`

Included navigation and governance surfaces:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md`

Included evaluation surfaces:
- entry routing and reading order
- owner/runtime/module boundaries
- verdict/persistence/logging ownership
- shared dict/dataclass/result contracts
- console/audit/DB observability paths
- local readability aids:
  - boundary comments
  - naming clarity
  - shell/core/sink separability

Excluded unless directly needed as evidence:
- narrative quality of generated content
- speculative architecture redesign
- performance tuning unrelated to comprehension
- large implementation plans beyond hotspots discovered by this survey

## 4. Required Evaluation Axes
Every finding must be mapped to one or more of these axes.

### Axis A. Navigation
- Can a cold reader determine where to start?
- Is reading order obvious across owner shell, runtime, and sink boundaries?
- Are there missing or stale orientation markers?

### Axis B. Authority
- Is the final owner of a decision or side effect easy to identify?
- Are authoritative shells distinguishable from semantic cores?
- Are stale wrappers or misleading delegations creating search noise?

### Axis C. Contract
- Are common result payloads, envelopes, or dict fields understandable?
- Are field names overloaded or context-dependent without explanation?
- Does a reader need to cross too many files to decode a contract?

### Axis D. Observability
- Can console, audit, DB, and metrics sinks be followed without guesswork?
- Is operator-facing state traceable from source structure?
- Are there places where a wait state or PASS/REJECT cause is difficult to locate?

### Axis E. Local Readability
- Does the function or module reveal its phases cleanly?
- Would a short boundary comment or clarifier materially reduce misunderstanding?
- Is the current name honest about mutation, I/O, or authority?

## 5. Severity And Fix-Type Rules
Each hotspot must receive:
- severity:
  - `P0`: comprehension hazard likely to cause wrong edits or wrong verdict tracing
  - `P1`: materially slows safe modification or debugging
  - `P2`: useful cleanup, but not blocking
- fix type:
  - `comment-only`
  - `doc-only`
  - `observability-only`
  - `boundary-refactor`
  - `contract-cleanup`
  - `ignore`

Never stop at a vague complaint like `hard to read`. The output must say why and what class of fix would address it.

## 6. Required Investigation Method
This order is survey-only. Do not patch code during the survey unless the survey itself is blocked by a compile or decode failure.

### Pass 1. Static Topology Map
- Use `docs/2026-03-23/llm-codebase-orientation-pack.md` as the starting map.
- Re-walk the live code and confirm or reject:
  - current reading order
  - current authority boundaries
  - current sink ownership
- Note any areas where the orientation pack is already stale or incomplete.

### Pass 2. Hotspot Grading
- Build a repo-wide hotspot list for LLM comprehension cost.
- Rank hotspots by:
  - breadth of impact
  - likelihood of wrong edits
  - authority ambiguity
  - contract ambiguity
  - observability ambiguity
- Produce at least:
  - `Top 20 comprehension hotspots`
  - `Top 10 quick wins`
  - `Top 10 no-action / already-settled zones`

### Pass 3. Recommendation Merge Audit
- For each hotspot, decide whether the right next step is:
  - no action
  - comment/doc improvement
  - observability improvement
  - bounded refactor
- Cross-check whether the issue is already covered by:
  - the orientation pack
  - recent pass/reject integrity survey
  - current init harness gates
- If a recommendation would change entry flow, owner authority, contract meaning, or sink topology, mark it as `orientation-pack-impacting`.

## 7. Mandatory Output Structure
The final survey report must contain all of the following sections.

1. `Executive Summary`
2. `Heatmap by Area`
   - `main_a.py`
   - Stage 0 / Stage 2 / Stage 3 / Stage 4
   - domain agents
   - validation
   - persistence / DB
   - governance docs
3. `Top 20 Comprehension Hotspots`
4. `Quick Wins`
   - comment-only
   - doc-only
   - observability-only
5. `Boundary Refactor Candidates`
6. `Orientation Pack Refresh Candidates`
7. `No-Action / Settled Areas`
8. `Confidence And Limits`

Each hotspot entry must include:
- file path
- line anchor
- affected axis
- severity
- why it is costly for LLM reasoning
- recommended fix type

## 8. Acceptance Criteria
This survey is complete only if:
- every P0/P1 item has a concrete file and line anchor
- every recommendation is assigned a fix type
- at least one explicit `no-action` list is produced to avoid over-refactor
- orientation-pack-impacting items are separated from local readability-only items
- the report states whether the codebase is now:
  - navigation-ready
  - authority-readable
  - contract-readable
  - observability-readable
  for an LLM, with a confidence score

## 9. Stop Rules
- Do not drift into general style review.
- Do not reopen the long-function campaign just because a file is still `100+ LOC`.
- Do not recommend refactor where comment/doc or observability fixes would solve the comprehension issue cheaper.
- Do not create execution SSOT or implementation roadmap unless the user explicitly asks to realize the findings.
- Do not duplicate already-settled guidance unless the live code clearly drifted.

## 10. Suggested Starting Path
1. Read:
   - `docs/2026-03-23/llm-codebase-orientation-pack.md`
   - `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md`
   - `docs/implementation/system-order-init-harness.md`
2. Walk the production spine:
   - `main_a.py`
   - Stage 0 / 2 / 3 / 4 owners
   - current runtime modules
3. Grade the first hotspot batch from:
   - entry routing
   - verdict ownership
   - persistence ownership
   - console/audit/DB traceability
4. Only after that, widen into cross-cutting agent and validator families.

## 11. Intended Report Path
- `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`

## 12. 3-Pass Audit Record
- Pass 1
  - confirmed scope is system-track survey-only and does not overreach into realization
- Pass 2
  - confirmed axes, severity, and fix-type rules are explicit enough to avoid vague style review
- Pass 3
  - confirmed outputs map directly to future implementation triage without forcing execution SSOT creation

## 13. Confidence
- Confidence: 98%
- Basis:
  - aligned with current orientation-pack and pass/reject survey artifacts
  - bounded to comprehension-specific questions rather than broad quality review
  - uses explicit stop rules to prevent scope creep
