## LLM Knowwhere Retrieval Application Survey

Date: 2026-03-26
Status: final
Scope: current system-track runtime only; asks whether this workspace already applies the pattern "when the LLM needs information, it knows where to fetch it from authoritative sources" rather than relying on implicit parametric recall
Canonical Path: `docs/2026-03-26/llm-knowwhere-retrieval-application-survey.md`

Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: 14 tracked, 16 untracked; hotspots: docs/implementation/system-order-init-harness.md, modules/core/*, docs/2026-03-25/*, projects/canary_*`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Intent

The user question is not really "did we implement the exact paper title?" but "does the current system make the LLM find the right information when needed?"

For this survey I used the following working definition:

- `knowwhere` means the system routes generation to explicit sources or retrieval paths when facts are needed.
- the important split is `where to look` vs `how to write`.
- the closest paper framing is RAG / tool-use / act-then-observe, even if the exact paper name the user remembered as "SMA..." was not identified during this pass.

Closest research anchors:

- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (arXiv:2005.11401)
- Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models* (arXiv:2210.03629)
- Schick et al., *Toolformer: Language Models Can Teach Themselves to Use Tools* (arXiv:2302.04761)

Short interpretation:

- RAG says parametric memory alone is not enough; external memory should be queried.
- ReAct says reasoning should be interleaved with actions that gather outside information.
- Toolformer says the model should learn or be given a path for deciding when to call an external tool.

Against that bar, the current system is **partially yes, and one subsystem is already strongly aligned**.

## Pass 1. Inventory

### 1. Strongest candidate: Smart Context Retrieval (SC)

The strongest `knowwhere` implementation is the Smart Context Retrieval stack:

- `modules/core/context_advisor.py`
  - line 3 states the exact architectural split: `planning (what to retrieve), not execution (how to retrieve)`
  - line 348 defines `ContextAdvisor`
  - lines 513 and 539 expose `plan_stage4_retrieval()` and `plan_director_retrieval()`
  - lines 763-814 infer retrieval source from work-focus semantics and build source-aware slots
- `modules/core/vec_memory.py`
  - line 637 defines `retrieve_hybrid_context()`
  - lines 637-704 run dense KNN + sparse FTS + RRF fusion, then keyword fallback if empty
  - line 902 defines `retrieve_npc_context()`
  - lines 904-925 gather NPC-specific candidates and fall back to keyword retrieval if needed
  - lines 1040-1089 define keyword fallback and FTS search

This is the clearest "knowwhere" layer because the generation path is not asked to remember all prior story facts from weights alone. A planner picks slots, a retrieval executor resolves those slots, and the result is injected into the next LLM call.

### 2. Runtime wiring proves it is not dead code

The planner is actually wired into live runtime:

- `modules/core/sovereign_bootstrap_runtime.py:445`
  - bootstraps `owner.context_advisor = _v50["ContextAdvisor"]()`
- `config/settings/validation.yaml:178-192`
  - `smart_retrieval.enabled: true`
  - `stage2_enabled: true`
  - `stage3_enabled: true`
  - `stage4_enabled: true`
  - `director_enabled: true`
  - `retrieval_mode: hybrid`
- `modules/core/stage2_preflight.py:1095-1110`
  - Stage 2 uses `advisor.plan_stage2_retrieval(...)` when smart retrieval is enabled
- `modules/core/stage4_context_builder.py:1728-1757`
  - Stage 4 uses `advisor.plan_stage4_retrieval(...)` and then executes the plan
- `modules/core/stage4_director_runtime.py:897-921`
  - Director path also gates on smart retrieval flags and calls `advisor.plan_director_retrieval(...)`

Live runtime evidence also exists:

- `projects/canary_0326_stage3_telemetry/logs/session/ui_events.jsonl:40`
  - UI log shows `Context Advisor 활성화` on 2026-03-26
- `projects/canary_0326_stage3_telemetry/logs/quality_metrics.jsonl:1`
  - Stage 3 retrieval observation shows `advisor_path_used=true`, `planned_slots_count=3`, `source_counts={"vec_memory":2,"db_npc_history":1}`
- `projects/canary_0326_stage3_telemetry/logs/quality_metrics.jsonl:3`
  - next Stage 3 retrieval observation shows `planned_slots_count=4` with the same source-mix pattern
- `projects/canary_0325_stage4_wave2/logs/quality_metrics.jsonl:5`
  - Stage 4 retrieval observation shows `advisor_path_used=true`, `planned_slots_count=8`, and mixed sources `vec_memory`, `db_npc_history`, `static`, `db_npc_relationship`

That means the current answer is not just "there is retrieval code somewhere." It is active in recent March 25-26, 2026 canary runs.

### 3. Relation lookup is source-backed, not free-form memory

The second strong `knowwhere` component is relation retrieval:

- `modules/core/semantic_query_broker.py:2-7`
  - describes itself as `source-backed, read-only relationship lookups`
  - explicitly says Python gathers evidence from `WorldState / FactLedger / DB relationship edges`, then the caller decides how to consume it
- `modules/core/semantic_query_broker.py:175`
  - `should_build_relation_slice(...)`
- `modules/core/semantic_query_broker.py:217`
  - world-state evidence iterator
- `modules/core/semantic_query_broker.py:257`
  - fact-ledger evidence iterator
- `modules/core/semantic_query_broker.py:304`
  - DB relationship-edge evidence iterator
- `modules/core/semantic_query_broker.py:428`
  - `build_relation_slice(...)`
- `modules/core/stage4_context_builder.py:814-823`
  - Stage 4 actually instantiates `SemanticQueryBroker(...)` and requests a relation slice

This is again closer to `knowwhere` than `knowhow`: relation judgments are anchored to persisted sources instead of asking the model to "remember" who is close to whom.

### 4. Authority routing is explicit

There is also a quieter but important `knowwhere` pattern: the runtime knows which source is authoritative.

- `modules/core/stage4_context_builder.py:939`
  - `_filter_state_tracker_summaries_for_authority(...)`
- nearby logic suppresses arc-derived summaries when canonical persisted layers already cover the same surface
- `modules/core/stage4_immutable_fact_contract.py:1-10`
  - the immutable fact packet is declared `derived-only` and `never becomes a new authority owner`
- `modules/domain/agents/chief_writer_context.py:536-558`
  - Stage 4 prompt input is rebuilt from `blueprint`, `world_state_summary`, `fact_ledger_summary`, `chain_link_section`, and `prev_digest`

This is not retrieval in the search-engine sense, but it is still a `knowwhere` pattern: the system has explicit authority boundaries and does not treat every source as equally trustworthy.

### 5. Observability exists for retrieval quality

The retrieval path is observable rather than invisible:

- `modules/core/stage2_preflight.py:1179-1194`
  - records retrieval observations with `build_context_observation(...)`
- `modules/core/stage4_context_builder.py:1902-1919`
  - does the same for Stage 4
- `modules/core/quality_dashboard.py:200-218`
  - persists `retrieval_observation` records

This matters because a true `knowwhere` system should not only retrieve, but also expose when retrieval coverage was weak or partially lost.

## Pass 2. Semantic Classification

### A. Well-applied

These parts are genuinely well-applied:

1. `ContextAdvisor + VecMemory + stage wiring`
   - best match to the paper idea
   - planner decides where to look
   - executor resolves the source
   - generator receives the resulting evidence

2. `SemanticQueryBroker`
   - strong source-backed relation lookup
   - especially good for "relationship state / protagonist relation" type continuity

3. `Retrieval provenance / coverage observation`
   - the system records whether retrieval was used, how many slots were planned, which sources were hit, and whether any retrieval-derived section went missing

### B. Partially applied

These parts support the same philosophy but are not full `knowwhere` loops:

1. `Immutable Fact Contract`
   - good externalization of facts
   - but this is mostly Python-side fact compilation, not model-side search choice

2. `PromptLoader`
   - prompts come from explicit config files rather than inline code
   - this is SSOT/provenance hygiene, but not really evidence retrieval

### C. Not yet fully applied

This is where the answer becomes "yes, but not all the way":

1. The LLM itself does **not** autonomously decide to search
   - the planner is mostly Python heuristic logic
   - this is closer to `system knows where` than `model knows where`

2. Some planned retrieval still fails to survive into the final prompt
   - `projects/canary_0325_stage4_wave2/logs/quality_metrics.jsonl:5` shows Stage 4 planned `db_npc_relationship`, but `relation_slice_included=false` and `coverage_warnings=["missing_relation_slice"]`
   - in other words, the system knew a relation source should matter, but the final mandatory context still dropped that slice

3. Static slots are mixed into the same retrieval plan
   - `static` source is useful, but it is not true retrieval
   - this slightly inflates the appearance of `knowwhere` because some slots are prewritten hints, not dynamic lookup

## Pass 3. Verdict

### Final answer

**있다. 다만 "LLM이 스스로 도구를 호출해 찾는다" 수준보다는, "시스템이 LLM 대신 어디를 봐야 하는지 계획하고 가져다 준다" 수준에서 잘 적용돼 있다.**

The best evidence is the Smart Context Retrieval lane:

- source-aware planning exists
- hybrid retrieval exists
- relation-specific source lookup exists
- live canary runs from March 25-26, 2026 show the path is active

So if the user question is:

- "현 시스템이 정보가 필요할 때 잘 찾게 되어 있나?" -> **yes, partially and meaningfully**
- "그게 Toolformer/ReAct 같은 수준의 model-autonomous tool use냐?" -> **no, mostly not yet**

### Practical reading

For current runtime behavior, the system is strongest on:

- prior episode continuity
- NPC history lookup
- relation/history lookup from persisted stores
- deciding source authority between world state, fact ledger, DB history, and vector memory

It is weaker on:

- autonomous LLM search decisions
- guaranteeing every planned retrieval slice survives final prompt composition

## Tests and Evidence Quality

Relevant regression coverage exists:

- `tests/test_stage4_context_builder.py:2088`
  - semantic relation slice injection test
- `tests/test_stage4_context_builder.py:2159`
  - retrieval coverage warning surfacing test
- `tests/test_stage3_orchestrator.py:240`
  - Stage 3 observability includes `advisor_path_used`
- `tests/test_stage3_orchestrator.py:241`
  - Stage 3 observability includes `planned_slots_count`

## 3-Pass Audit

### Pass 1. Structure and scope

- document type matches request: survey
- scope is bounded to system runtime, not narrative pipeline
- includes strong / partial / missing classifications
- canonical save path is correct

### Pass 2. Evidence and consistency

- every major claim is tied to live code or live run logs
- no claim depends on stale temp execution docs
- runtime logs and code wiring agree that SC is active
- weak points are also evidenced, not inferred from preference

### Pass 3. Readability and operational use

- next reader can answer the user question directly
- evidence is concrete enough to re-audit
- conclusion separates "system-level knowwhere" from "model-autonomous knowwhere"

Confidence:

- Estimated confidence: 96%

## Source Links

External papers:

- RAG: https://arxiv.org/abs/2005.11401
- ReAct: https://arxiv.org/abs/2210.03629
- Toolformer: https://arxiv.org/abs/2302.04761

Primary workspace evidence:

- `modules/core/context_advisor.py`
- `modules/core/vec_memory.py`
- `modules/core/semantic_query_broker.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/quality_dashboard.py`
- `config/settings/validation.yaml`
- `projects/canary_0326_stage3_telemetry/logs/quality_metrics.jsonl`
- `projects/canary_0325_stage4_wave2/logs/quality_metrics.jsonl`
- `projects/canary_0326_stage3_telemetry/logs/session/ui_events.jsonl`
