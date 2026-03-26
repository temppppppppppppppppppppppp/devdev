# Multi-Provider Spine + Vertex Entry Parallel Survey Master Order

Date: 2026-03-26
Status: active
Type: system-track parallel survey master order
Scope: bounded pre-execution survey for today's Vertex entry under a multi-provider spine

## 1. Purpose

This order exists because today's question is not just:

- "Can we make Vertex work?"

It is:

- "Can we make Vertex work today without creating a Gemini-only shape that becomes painful when Claude/OpenAI enter soon?"

The survey must therefore be:

- system-track
- survey-only
- bounded
- parallelized by code seam

This is **not** an execution SSOT.
This is the pre-execution parallel survey that should decide whether one bounded Wave 1 execution SSOT is now justified.

## 2. Read Order

Read these files first, in this exact order:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/document-3pass-audit-harness.md`
4. `docs/2026-03-26/llm-multi-provider-context-note.md`
5. `docs/2026-03-26/multi-provider-spine-vertex-entry-operating-note.md`

## 3. Task

Run one bounded parallel compact survey for:

- multi-provider spine readiness
- today's `Gemini on Vertex` entry
- near-term `Claude` / later `OpenAI` survivability

Survey only. No code changes.

## 4. Primary Goal

Determine the smallest execution wave that can:

- admit `Gemini on Vertex` now
- avoid hardening the app into another Gemini-only architecture
- keep a clean path for near-term `Claude` and later `OpenAI`

## 5. Hard Constraints

- Survey only. Do not patch code.
- Do not create execution SSOT yet.
- Do not touch `docs/temp/` or queue state.
- Keep scope bounded to provider/backend architecture and current runtime coupling.
- Do not broaden into desktop/UI redesign, billing redesign, or full provider rollout.
- Do not assume Claude/OpenAI feature parity without code evidence.
- Prefer live code truth over prior intuition.
- If confidence < 95%, do not recommend implementation.

## 6. Parallel Topology

This order assumes up to **4 terminals** are available.

Default terminal assignment:

- Terminal 1 -> Lane A
- Terminal 2 -> Lane B
- Terminal 3 -> Lane C
- Terminal 4 -> Lane D

Shorthand operator phrasing is allowed and should be understood directly.

Examples:

- `1번은 A, 2번은 B, 3번은 C, 4번은 D`
- `터미널 1/2 먼저, 3/4는 뒤에`
- `1번은 identity, 2번은 BaseAgent, 3번은 provider, 4번은 usage`

Nested parallelism is also allowed inside each terminal, as long as it stays bounded to that lane.

This means:

- terminal-level parallelism across A/B/C/D is allowed
- terminal-local sub-parallel evidence gathering is also allowed
- but file ownership and question ownership must stay separated by lane

Accepted interpretation:

- `parallel of parallel`
- one terminal may read/check multiple files in parallel inside its own lane
- no terminal should silently reopen another lane's core question

Lane isolation rule:

- Lane A owns identity/config/routing
- Lane B owns BaseAgent/request construction
- Lane C owns provider adapter boundary
- Lane D owns usage/cost/telemetry normalization

If one lane discovers a likely cross-lane dependency, it should:

- note it as dependency evidence
- avoid taking over the other lane's core conclusion

## 7. Output Ownership

To prevent overwrite collisions, each lane must write to its own lane-local survey file first.

Lane-local output files:

- Lane A -> `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-a-survey.md`
- Lane B -> `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-b-survey.md`
- Lane C -> `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-c-survey.md`
- Lane D -> `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-d-survey.md`

Only one synthesizer terminal may write the merged final report:

- merged final -> `docs/2026-03-26/multi-provider-spine-vertex-entry-compact-survey.md`

Direct lane-to-final overwrites are not allowed.

Accepted operating pattern:

1. each terminal surveys only its own lane
2. each terminal saves only its own lane-local survey file
3. one designated synthesizer terminal reads A/B/C/D lane files
4. only that synthesizer terminal writes the merged compact survey

If shorthand operator phrasing is used, the synthesizer should also be named explicitly.

Examples:

- `1번은 A, 2번은 B, 3번은 C, 4번은 D, 1번이 마지막 merge`
- `1/2/3/4 각 lane 문서만 쓰고, 4번이 최종 compact survey 합치기`
- `merge는 1번만`

## 8. Parallel Survey Lanes

The survey should be split into these lanes and then merged.

### Lane A. Identity / Config / Routing

Question:

- Does the current model identity shape cleanly separate `backend`, `family`, and `capability`, or is it still too flat for Vertex/Claude/OpenAI?

Inspect at minimum:

- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- any provider/model selection helpers

Must answer:

- how `vertex` is currently represented
- whether `vertex` is treated as backend or flat provider peer
- whether today's Vertex entry can be done without distorting future identity shape

### Lane B. BaseAgent Coupling / Request Construction

Question:

- How Gemini-native is the dominant request path right now?

Inspect at minimum:

- `modules/domain/agents/base_agent.py`
- schema/request assembly call sites
- thinking/caching/json-mode construction paths

Must answer:

- which request config pieces are still Gemini-native
- what minimum provider-neutral request contract already exists
- what minimum decoupling is required before or during Vertex entry

### Lane C. Provider Adapter Boundary

Question:

- Are provider adapters and provider-neutral contracts already strong enough for `Gemini on Vertex`, and what would later Claude/OpenAI add?

Inspect at minimum:

- `modules/core/llm_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/openai_provider.py`

Must answer:

- whether `vertex_provider` is really "Gemini on Vertex" only or a broader abstraction
- where request compilation belongs
- what capability asymmetry is already visible in code

### Lane D. Usage / Cost / Telemetry Normalization

Question:

- If Vertex enters now, do usage/cost fields stay coherent enough for later multi-provider operation?

Inspect at minimum:

- `modules/core/metrics_collector.py`
- usage extraction in provider adapters
- `modules/domain/agents/base_agent.py`
- `modules/api/process_runner.py`

Must answer:

- how usage is currently normalized
- whether token/cost fields are Gemini-shaped or provider-neutral enough
- whether today's Vertex entry risks hidden observability drift

## 9. Required Evidence Surfaces

At minimum, the merged survey must use:

- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_schema.py`
- `modules/core/response_schemas.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/process_runner.py`
- `modules/core/metrics_collector.py`
- relevant tests such as router/provider usage tests if present

## 10. Required Investigation Questions

1. What is the dominant architecture risk if Vertex is added quickly today?
2. Is the main bottleneck:
   - model identity flattening
   - BaseAgent Gemini-native request construction
   - weak provider boundary
   - or usage/cost normalization
3. What is the smallest bounded Wave 1 that makes `Gemini on Vertex` real without poisoning future Claude/OpenAI work?
4. What must explicitly stay out of Wave 1?
5. Should the next step be:
   - no action
   - one execution SSOT
   - one narrower follow-up survey

## 11. Required Output

Save one merged report to:

- `docs/2026-03-26/multi-provider-spine-vertex-entry-compact-survey.md`

Lane-local survey files must also be saved before merge:

- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-a-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-b-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-c-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-d-survey.md`

The merged report must:

- present findings first
- keep file/line anchors
- separate:
  - what is already multi-provider-friendly
  - what is still Gemini-native
  - what must change for Vertex entry now
  - what should wait for later providers
- recommend exactly one next move

## 12. Mandatory Final Lines

- Dominant multi-provider seam: `<short label>`
- Best next single move: `<short label>`
- Should Codex open an execution SSOT now: `yes / no`

## 13. Single Summary

This is a parallel survey because the problem is not one seam.

It spans:

- identity
- request construction
- provider boundary
- usage normalization

The correct next output is one merged compact survey, not code and not yet an execution SSOT.
