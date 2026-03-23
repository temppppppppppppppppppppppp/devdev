Date: 2026-03-23
Status: final (3-pass audited, order scope)
Document Type: system-track survey order
Canonical Path: `docs/2026-03-23/generation-coherence-deep-dive-order.md`
Temp Mirror Path: none
Source Planning Doc:
- `docs/2026-03-23/daily-roadmap-2026-03-23.md`

## 1. Purpose
- Define a bounded deep-dive order for the `Generator / Coherence` half of the 7-axis framework.
- Audit whether the generation pipeline:
  - writes well on first pass
  - maintains cross-episode coherence
  - retrieves selectively and economically
  - receives the right context before generation

This is a survey order, not an implementation plan.

## 2. Covered Axes
- Q1. 잘 쓰냐
- Q5. 잘 기억하냐
- Q6. 잘 찾냐
- Q7. 잘 받냐
  - Generator-side only

## 3. Scope
Included:
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/domain/agents/continuity_arc.py`
- `modules/validation/continuity_validator.py`
- `modules/domain/agents/state_tracker.py`
- `modules/core/vec_memory.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_context_packets.py`
- `modules/core/context_advisor.py`
- generator-facing prompt assembly and retrieval routing surfaces directly connected to those files

Excluded:
- Director verdict internals as a primary topic
- Stage 4 retry escalation policy as a primary topic
- broad live-run execution design
- implementation or refactor work

## 4. Primary Questions
1. Which generator paths are intended to succeed on first pass, and where do they structurally lose quality or diversity?
2. How are WorldState, FactLedger, continuity, and NPC state meant to preserve cross-episode coherence?
3. Which retrieval stores exist, and how is the routing decision made among them?
4. Which generator-side context fields are mandatory, optional, truncatable, or silently dropped?

## 5. Required Investigation Method

### Pass 1. Generation Quality Topology
- Map first-pass generation flow across:
  - ChiefWriter
  - Arc ensemble
  - Blueprint ensemble
- Identify where diversity, reuse, or prompt context can collapse before Director review.

### Pass 2. Coherence / Memory Integrity
- Trace long-horizon coherence through:
  - WorldState
  - FactLedger
  - continuity validators / inspectors
  - NPC and state tracker paths
- Identify where contradictions can evade detection or where memory updates can drift.

### Pass 3. Selective Retrieval + Context Reception
- Map retrieval stores and routing decisions.
- Confirm generator-side context injection completeness:
  - mandatory context
  - tier packets
  - lookback tiers
  - previous manuscript summaries
  - context advisor decisions
- Flag over-retrieval, under-retrieval, or field-loss / truncation hazards.

## 6. Mandatory Output Structure
The final deep-dive report section for this lane must include:
1. Executive Summary
2. First-Pass Generation Quality Map
3. Coherence / Memory Ownership Map
4. Selective Retrieval Routing Map
5. Generator Context Reception Map
6. Top Hotspots
7. Quick Wins
8. Refactor Candidates
9. Confidence And Limits

## 7. Acceptance Criteria
- every P0 / P1 issue has a file and line anchor
- generator-side Q7 findings are separated from Director-side context findings
- retrieval routing is explicitly described
- coherence ownership is explicitly mapped across state surfaces
- recommendations are labeled as:
  - comment-only
  - doc-only
  - observability-only
  - boundary-refactor
  - contract-cleanup
  - ignore

## 8. Stop Rules
- do not drift into Director verdict analysis unless directly required by a generator-side context gap claim
- do not patch code under this order
- do not reopen the long-function campaign based only on file size

## 9. Intended Report Integration
- primary integration target:
  - `docs/2026-03-23/director-pipeline-7axis-deep-dive.md`
- lane-local notes may be drafted during investigation, but final human-facing claims should land in the integrated 7-axis report

## 10. 3-Pass Audit Record
- Pass 1
  - scope bounded to generator / coherence axes and avoids Director-side verdict sprawl
- Pass 2
  - required maps make the lane concrete enough for Opus execution
- Pass 3
  - output and stop rules align with current workspace survey governance

## 11. Confidence
- Confidence: 98%
- Basis:
  - directly derived from the 7-axis roadmap
  - bounded enough for Opus execution without execution-SSOT inflation
