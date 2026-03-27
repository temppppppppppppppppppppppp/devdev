Date: 2026-03-27
Status: final (3-pass audited)
Document Type: 6-terminal merge-audit report
Canonical Path: `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-merge-audit.md`
Temp Mirror Path: none
Source Order: `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`
Source Survey Docs:
- `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral.md`
Evidence Artifacts:
- `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry-evidence.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict-evidence.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection-evidence.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state-evidence.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral-evidence.md`
- inline live recheck against `docs/temp/queue-state.json` and current `git status`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked llm_router/provider/context/validator surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked multi-provider docs, fact docs, anthropic_vertex provider scaffolding/tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

All 6 lane reports arrived and are usable for merge.

Merged judgment:
- the workspace is `navigation-ready`
- the workspace is `cheap-fix-first`
- the workspace is `mixed but tractable` on gimmick elegance
- there is `no merged P0`
- the dominant next-step shape is still `comment-only`, `doc-only`, `observability-only`, plus a few bounded `contract-cleanup` items
- the major structural issues remain deferred:
  - writer/context 35-parameter forwarding
  - technique/realm canonical authority and schema formalization
  - provider identity / usage normalization consolidation
  - `_god1_*` explicit handoff replacement

What improved versus the prior 2026-03-24 wave:
- the previous top Stage 4 hotspot, verdict-field precedence at `director_ensemble.py:1346-1354`, is now settled
- T6 reports that 7 of 10 prior peripheral hotspots are already resolved
- the fact-authority wave landed correctly and remains stable

What remains open:
- provider/router and observability still contain small but real duplication/drift traps
- writer/context injection precedence is still reconstructed from code order rather than one declared map
- genre/fact gimmicks remain strong in core authority but weak in prompt-visible rule declaration
- Stage 4 still contains one documented hidden side channel (`_god1_*`)

Queue state:
- `docs/temp/queue-state.json` is still `empty`
- no temp execution artifact was created in this turn

Execution promotion judgment for this turn:
- `not promoted`
- user asked only for the survey run and merge state, not realization

## 2. Lane Status Matrix

| Lane | Status | Confidence | Merge Verdict |
| --- | --- | --- | --- |
| T1 Navigation / Entry | final | 96% | valid; mixed elegance, mostly annotation/documentation gaps |
| T2 Provider / Router | final | 96% | valid; strongest contract-cleanup cluster |
| T3 Stage 4 Authority / Verdict | final | 96% | valid; mostly comment-only follow-up, prior P0 settled |
| T4 Writer / Context Injection | final | 96% | valid; one dominant structural deferral plus several cheap clarity wins |
| T5 Fact Authority / Genre State | final | 96% | valid; core authority strong, genre/rule declaration mixed |
| T6 Observability / Peripheral | final | 96% | valid; prior cleanup largely realized, a few narrow residuals remain |

## 3. Merged Priority Clusters

| Rank | Cluster | Lanes | Representative Anchors | Fix Shape | Merge Judgment |
| --- | --- | --- | --- | --- | --- |
| 1 | Injection / authority / navigation clarity | T1, T3, T4, T5 | `main_a.py:3794`, `stage3_orchestrator.py:701`, `stage4_post_pass_runtime.py:26`, `director_ensemble.py:976`, `stage4_retry_runtime.py:825`, `stage4_context_builder.py:996`, `stage4_context_builder.py:1600`, `world_state.py:764` | comment-only + doc-only | highest ROI; no behavior change needed |
| 2 | Provider identity and launch-contract honesty | T2, T6, T1 | `llm_generate.py:24-28`, `metrics_collector.py:97-110`, `metrics_collector.py:74-94`, `process_runner.py:809-817`, `providers/__init__.py:4,8` | comment-only + contract-cleanup + doc-only | second priority; most likely to mislead a cold LLM today |
| 3 | Genre / fact rule visibility and degradation truth | T5, T4 | `wuxia_guard.py:222-253`, `blocking_validator.py:91-113`, `state_tracker.py:1`, `stage3_orchestrator.py:1024` | doc-only + comment-only + observability-only | strong value, especially for wuxia and prompt-facing reasoning |
| 4 | Peripheral cleanup and governance metadata | T6, T1 | `docs/implementation/risk-approval-checklist.md:1`, `docs/implementation/release-gate-v1.md:1`, `tests/stage3_isolated_test/`, `tests/stage4_v2_test/`, `llm-codebase-orientation-pack.md` | doc-only + contract-cleanup | worthwhile, but below the first 3 clusters |

### Cluster 1. Injection / Authority / Navigation Clarity

Merged pattern:
- the architecture is mostly sound
- the problem is that key ownership or precedence rules are still implicit at the call site

Highest-value items:
1. T4 `stage4_context_builder.py:1600`
   - add a tier injection map comment so a cold LLM can see the stack without replaying insertion order
2. T4 `stage4_context_builder.py:996`
   - add prompt-facing authority precedence note tying authority statement to advisory suppression
3. T3 `stage4_post_pass_runtime.py:26`
   - mark thin delegates vs real post-pass authority boundary
4. T3 `director_ensemble.py:976`
   - annotate mutation footprint of the 4 quality-gate methods
5. T3 `stage4_retry_runtime.py:825`
   - declare retry lane priority explicitly
6. T1 `main_a.py:3794`
   - document Stage 4 lazy-init gateway and non-blocking `None` contract
7. T1 `stage3_orchestrator.py:701`
   - document why state is written back to `self.app`
8. T5 `world_state.py:764`
   - document what `get_canonical_constraints()` includes and what it does not

Merge verdict:
- this is the best first clarity wave if execution is requested later

### Cluster 2. Provider Identity and Launch-Contract Honesty

Merged pattern:
- outer provider architecture is elegant
- inner reasoning traps are small, real, and currently split across router, metrics, and launch code

Highest-value items:
1. T2 `llm_generate.py:24-28`
   - explain the backend/family overwrite as a compat belt and state adapters are authoritative
2. T2 + T6 `metrics_collector.py:97-110`
   - add interim comment that provider identity is inferred from model name prefix and must track router logic
3. T2 `modules/core/providers/__init__.py:4,8`
   - export `AnthropicVertexProvider`
4. T2 `process_runner.py:809-817`
   - add `OPENAI_API_KEY` passthrough
5. T6 `metrics_collector.py:74-94`
   - mark inline cost table as temporary and drift-prone

Merge verdict:
- this is the clearest `contract-cleanup` cluster
- still bounded
- does not justify a broad provider refactor by itself

### Cluster 3. Genre / Fact Rule Visibility and Degradation Truth

Merged pattern:
- core fact authority is strong
- what remains weak is prompt-visible explanation of genre rules, degradation, and source hierarchy

Highest-value items:
1. T5 `wuxia_guard.py:222-253`
   - expose justification patterns to the prompt so the LLM knows which bypass reasons are valid
2. T5 `stage3_orchestrator.py:1024`
   - document semantic-context assembly sources and authority tiers
3. T5 `blocking_validator.py:91-113`
   - explain that `passed=True + degraded=True` means the check did not really run cleanly
4. T5 `state_tracker.py:1`
   - add authority hierarchy comment block
5. T4 genre injection notes
   - document why genre gates live where they live until a future registry exists

Merge verdict:
- high value for narrative correctness and LLM reasoning
- still mostly cheap fixes
- one long-term structural gap remains: technique/realm canonical authority

### Cluster 4. Peripheral Cleanup and Governance Metadata

Merged pattern:
- most old peripheral clutter has already been removed
- residual items are narrow and safe

Highest-value items:
1. T6 stale test artifacts in `tests/stage3_isolated_test/` and `tests/stage4_v2_test/`
2. T6 metadata headers for `risk-approval-checklist.md` and `release-gate-v1.md`
3. T1 orientation pack refresh for Stage 4 runtimes and provider layer

Merge verdict:
- good hygiene cluster
- not the main story anymore

## 4. Merged Quick Wins

These are the merged top quick wins across all lanes.

1. `stage4_context_builder.py:1600`
- add a tier injection map comment
- why it ranks first:
  - touches the highest-search-cost writer/context surface
  - clarifies precedence without changing behavior

2. `main_a.py:3794`
- add a Stage 4 lazy-init gateway contract comment
- why it ranks second:
  - entry-path confusion multiplies downstream search cost

3. `director_ensemble.py:976`
- add `# Mutates:` annotations to the 4 quality-gate methods
- why it ranks third:
  - makes Stage 4 verdict shaping locally legible

4. `metrics_collector.py:97-110`
- add interim provider-identity comment linking this logic to router inference
- why it ranks fourth:
  - prevents router/metrics reasoning drift

5. `llm_generate.py:24-28`
- explain backend/family overwrite compat belt
- why it ranks fifth:
  - resolves the most confusing provider-lane reasoning trap

6. `wuxia_guard.py:222-253`
- expose justification patterns in the purism prompt
- why it ranks sixth:
  - directly reduces genre-rule guesswork by the LLM

7. `world_state.py:764`
- add canonical-constraints docstring explaining scope and exclusions
- why it ranks seventh:
  - sharpens fact-authority understanding for both Stage 3 and Stage 4 readers

## 5. Settled / Resolved / No-Action Areas

Do not reopen these as if they were still primary hotspots.

- T3 verdict-field precedence
  - `director_ensemble.py:1346-1354`
  - prior top hotspot is now settled
- T5 Wave 1 authority contract
  - authority statement, advisory suppression, dead-NPC pre-check
  - all verified live
- T6 prior cleanup wave
  - 7 of 10 old hotspots already resolved
- `db_manager.py` large-file concern
  - still large, but ToC-backed and currently navigable; not a merge priority
- provider protocol and adapter outer skeleton
  - `LLMRequest`, `LLMResponse`, router shape, adapter module split
  - not the main problem

## 6. Deferred Structural Risks

These remain real but should stay explicitly deferred until the user asks for realization.

1. Writer/context request-shape cleanup
- `chief_writer.py:566` and related forwarding chain
- 35-parameter chain remains the dominant structural inelegance in T4

2. Technique/realm canonical authority
- T5's biggest long-term risk
- requires new modeling, not just comments

3. State-change schema formalization
- `state_changes` and enum consistency across tracker surfaces
- valuable, but larger than a clarity wave

4. Provider identity / usage normalization consolidation
- shared identity function plus provider-boundary usage normalization
- worthwhile, but not needed to regain navigability

5. `_god1_*` handoff replacement
- still the only explicit hidden Stage 4 side channel
- documented, stable, deferable

## 7. Promotion Judgment

This merge turn does **not** create an execution SSOT.

Why:
- the user asked to continue the survey/merge flow, not to realize findings
- the worktree is already dirty in several live source areas
- the highest-confidence next step is still a compact clarity wave, but promotion should wait for an explicit execution ask

If execution is requested later, the best starting shape is:
- one compact `clarity-wave` doc covering Cluster 1 + the non-invasive part of Cluster 2
- keep structural deferrals out of that first wave

## 8. Confidence And Limits

Estimated confidence: **97%**

Basis:
- all 6 lane reports are in final state
- all 6 converge on:
  - `Navigation-ready: yes`
  - `Cheap-fix-first: yes`
  - `Boundary-refactor can wait: yes`
  - `Gimmick-elegance: mixed`
- the only clear prior-wave recheck items were verified:
  - Stage 4 verdict precedence settled
  - peripheral cleanup materially progressed
  - queue remains empty

Limits:
- this is a merge of static lane reports, not a live run
- T2 did not include a separate evidence file, only the final report
- lane-level confidence is uniform but not identical in scope depth; T1 and T6 cover large surfaces using bounded reading strategies
- no execution prioritization was tested against a fresh rerun

## 9. 3-Pass Audit Record

Pass 1. Structure and Scope
- fixed document type as `merge-audit report`
- kept scope at survey merge, not execution planning
- included source docs, evidence artifacts, queue state, and commit state
- PASS

Pass 2. Evidence and Consistency
- confirmed all 6 lane reports exist and are final
- confirmed queue remains empty
- merged only findings that remained open in lane outputs
- separated settled items from still-open clusters
- PASS

Pass 3. Actionability
- compressed 6 reports into 4 merged clusters
- produced one merged quick-win list
- withheld execution promotion because the user did not ask for realization
- kept structural issues explicitly deferred
- PASS
