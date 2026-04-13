# Stage234 Context Memory / Vertex Live 3-Pass Audit

- Date: 2026-04-13
- Scope: audit of the context-memory and Vertex Live survey for the current Stage2/3/4 runtime stack
- Survey Under Audit: [stage234-context-memory-vertex-live-parallel-survey.md](./stage234-context-memory-vertex-live-parallel-survey.md)
- Final Confidence: 96%

## Pass 1

- Rechecked the local-code portion of the survey against current workspace truth.
- Reconfirmed the provider-layer split:
  - Anthropic direct is active for the main high-intelligence lanes
  - Vertex remains active for some Gemini/flash lanes
  - the provider layer itself is still mostly plain request/response generation

Result:

- the survey correctly describes the current stack as hybrid and provider-memory-light

## Pass 2

- Rechecked the memory substrate classification.
- Reconfirmed that the workspace already has meaningful app-managed memory:
  - DB truth
  - anchors
  - `VecMemory`
  - `ContextAdvisor`
  - cross-stage packets
  - session telemetry

Result:

- the survey correctly avoids the false claim that the system is "purely stateless"

## Pass 3

- Rechecked the external capability framing against official provider documentation.
- Reconfirmed the core distinction:
  - provider-native session/cache features exist
  - but they do not replace our hard-truth authority model

Result:

- the recommendation ordering is sound:
  1. internal capability cleanup
  2. Sonnet prompt caching
  3. provider-neutral session envelope
  4. optional Vertex Live sidecar later

## Final Judgment

The surveyed state and recommendation are stable enough to guide next implementation work.

The strongest conclusion remains:

- `Vertex Live API` is worth considering
- but it should not be the first or primary fix for our current context-memory pain
- the first practical gains are inside our own orchestration plus Sonnet-side prompt caching
