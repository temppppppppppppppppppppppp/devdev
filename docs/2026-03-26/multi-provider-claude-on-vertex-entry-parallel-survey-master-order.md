# Multi-Provider Claude on Vertex Entry Parallel Survey Master Order

Date: 2026-03-26
Status: active
Type: system-track parallel survey master order
Scope: bounded pre-execution survey for `Claude on Vertex` entry after Gemini dual-backend proof

## 1. Purpose

This order exists because the next question is not just:

- "Can we call Claude somehow?"

It is:

- "Can we add Claude on Vertex without collapsing the clean `backend / family / capability` spine we just validated with Gemini?"

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
6. `docs/2026-03-26/multi-provider-spine-vertex-entry-compact-survey.md`
7. `docs/2026-03-26/multi-provider-vertex-live-operator-check-report.md`

## 3. Task

Run one bounded parallel compact survey for:

- `Claude on Vertex` entry feasibility
- current `anthropic_provider.py` reuse boundary
- capability asymmetry vs Claude direct
- observability/billing/runtime-launch survivability

Survey only. No code changes.

## 4. Primary Goal

Determine the smallest execution wave that can:

- admit `Claude on Vertex`
- preserve the existing multi-provider spine
- avoid a fake abstraction that treats Claude-on-Vertex as either:
  - just Anthropic direct with different credentials
  - or just another Gemini-style Vertex path

## 5. Hard Constraints

- Survey only. Do not patch code.
- Do not create execution SSOT yet.
- Do not touch `docs/temp/` or queue state.
- Keep scope bounded to provider/backend architecture and current runtime coupling.
- Do not broaden into desktop/UI redesign, broad billing redesign, or full Claude rollout across all lanes.
- Do not assume Claude direct and Claude on Vertex feature parity without code or official-doc evidence.
- Prefer live code truth plus current official contract notes over intuition.
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
- `1번은 identity, 2번은 adapter, 3번은 capability, 4번은 usage`
- `1/2/3/4 각 lane 문서만 쓰고, 1번이 마지막 merge`

Nested parallelism is also allowed inside each terminal, as long as it stays bounded to that lane.

Lane isolation rule:

- Lane A owns identity/config/routing
- Lane B owns provider adapter boundary
- Lane C owns request/response capability asymmetry
- Lane D owns usage/cost/env/observability

If one lane discovers a likely cross-lane dependency, it should:

- note it as dependency evidence
- avoid taking over the other lane's core conclusion

## 7. Output Ownership

To prevent overwrite collisions, each lane must write to its own lane-local survey file first.

Lane-local output files:

- Lane A -> `docs/2026-03-26/multi-provider-claude-on-vertex-lane-a-survey.md`
- Lane B -> `docs/2026-03-26/multi-provider-claude-on-vertex-lane-b-survey.md`
- Lane C -> `docs/2026-03-26/multi-provider-claude-on-vertex-lane-c-survey.md`
- Lane D -> `docs/2026-03-26/multi-provider-claude-on-vertex-lane-d-survey.md`

Only one synthesizer terminal may write the merged final report:

- merged final -> `docs/2026-03-26/multi-provider-claude-on-vertex-entry-compact-survey.md`

Direct lane-to-final overwrites are not allowed.

Accepted operating pattern:

1. each terminal surveys only its own lane
2. each terminal saves only its own lane-local survey file
3. one designated synthesizer terminal reads A/B/C/D lane files
4. only that synthesizer terminal writes the merged compact survey

## 8. Parallel Survey Lanes

The survey should be split into these lanes and then merged.

### Lane A. Identity / Config / Routing

Question:

- Can the current router/config identity admit `backend=anthropic_vertex, family=claude` cleanly, or is it still hardcoded around `anthropic_direct` and `google_vertex/gemini` only?

Inspect at minimum:

- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- any provider/model selection helpers

Must answer:

- whether current identity model already has room for `anthropic_vertex`
- whether a new provider registration is sufficient, or current routing shape blocks it
- what minimum config/routing delta Claude-on-Vertex actually needs

### Lane B. Provider Adapter Boundary

Question:

- Can `anthropic_provider.py` be cleanly extended/reused for Claude on Vertex, or is a separate adapter required?

Inspect at minimum:

- `modules/core/llm_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/openai_provider.py`

Must answer:

- what parts of Claude direct can be shared with Claude on Vertex
- what parts must diverge
- whether the right abstraction is:
  - extend `AnthropicProvider`
  - create `AnthropicVertexProvider`
  - or create a shared Claude substrate with two thin backends

### Lane C. Request / Response / Capability Asymmetry

Question:

- What capability asymmetry between Claude direct and Claude on Vertex is already relevant to this codebase?

Inspect at minimum:

- `modules/domain/agents/base_agent.py`
- `modules/core/llm_schema.py`
- `modules/core/response_schemas.py`
- current official-doc assumptions already reflected in `llm-multi-provider-context-note.md`

Must answer:

- structured output delta
- system prompt delta
- thinking/reasoning delta
- prompt cache delta
- message normalization delta
- what must be capability-gated before Claude on Vertex enters

### Lane D. Usage / Cost / Runtime Env / Observability

Question:

- If Claude on Vertex enters now, do usage/cost/runtime-launch fields stay coherent enough for operations?

Inspect at minimum:

- `modules/core/metrics_collector.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/process_runner.py`
- provider usage extraction paths

Must answer:

- whether current metrics path can distinguish:
  - `anthropic_direct`
  - `anthropic_vertex`
- whether env/runtime launch contract already has the right shape
- whether pricing/usage normalization is ready enough
- whether a small bounded observability addition is required in Wave 1

## 9. Required Evidence Surfaces

At minimum, the merged survey must use:

- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_schema.py`
- `modules/core/response_schemas.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/process_runner.py`
- `modules/core/metrics_collector.py`
- relevant tests such as router/provider usage tests if present

## 10. Required Investigation Questions

1. What is the dominant architecture risk if Claude on Vertex is added next?
2. Is the main bottleneck:
   - identity/config/routing
   - provider adapter shape
   - capability asymmetry
   - or usage/cost/runtime observability
3. What is the smallest bounded Wave 1 that makes `Claude on Vertex` real without poisoning future OpenAI / wider Claude work?
4. What must explicitly stay out of that Wave 1?
5. Should the next step be:
   - no action
   - one execution SSOT
   - one narrower follow-up survey

## 11. Required Output

Save one merged report to:

- `docs/2026-03-26/multi-provider-claude-on-vertex-entry-compact-survey.md`

Lane-local survey files must also be saved before merge:

- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-a-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-b-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-c-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-d-survey.md`

The merged report must:

- present findings first
- keep file/line anchors
- separate:
  - what is already Claude-on-Vertex-friendly
  - what is still Anthropic-direct-only
  - what must change for Claude on Vertex now
  - what should wait for later
- recommend exactly one next move

## 12. Mandatory Final Lines

- Dominant Claude-on-Vertex seam: `<short label>`
- Best next single move: `<short label>`
- Should Codex open an execution SSOT now: `yes / no`

## 13. Single Summary

This is a parallel survey because the problem is not one seam.

It spans:

- identity
- adapter boundary
- capability asymmetry
- usage/runtime observability

The correct next output is one merged compact survey, not code and not yet an execution SSOT.
