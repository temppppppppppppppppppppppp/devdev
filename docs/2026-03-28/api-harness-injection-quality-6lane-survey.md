# API Harness Injection Quality 6-Lane Survey

Date: 2026-03-28
Mode: survey-only
Scope: assess whether giving harness documents more directly to live LLM API requests would improve prose quality or pipeline quality, and identify the smallest high-ROI experiment path. No code changes or live runs were performed in this turn.
Temp Queue Note: `docs/temp/execution-roadmap.md` is active for other system-track execution items, but it does not govern this survey-only order.

Commit State:
- Baseline Commit: `8f6e16f9995aed633a6de64a045c2a0184831668`
- Baseline Dirty Summary: `dirty: 9 tracked; hotspots: config/models.yaml, modules/api/process_runner.py, modules/domain/agents/base_agent.py, scripts/run_gold_manuscript_benchmark.py, tests/*`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Recommendation Snapshot

- default decision: do not inject raw harness or `AGENTS.md` markdown into every live API call
- better candidate: compile a small stage-specific harness digest and inject it only into narrow narrative-generation or evaluation surfaces
- highest-ROI pilot surfaces: planning/TR/BI prompt bundles, and optionally Director or scoring-review lanes
- lowest-ROI surfaces: desktop `/run` transport, control-plane metadata, and the full writer manuscript path by default
- why: current prompt authority already lives in `config/prompts`, project prompt JSON, mandatory context, reference anchors, validators, and cached agent context
- measurement path already exists: gold manuscript benchmark, quality dashboard, retrieval observation, and bounded soak canary
- next execution step: open one compact execution SSOT only if implementation is approved after this survey

## Question

The practical question is not simply "should the API receive the harness?" It is:

1. does the current system already encode most harness intent elsewhere
2. if not, where is the missing signal actually hurting quality
3. what is the smallest injection form that adds signal without bloating cost, latency, or prompt noise

This survey used six lanes:

1. current harness-to-API truth
2. current harness role in the runtime
3. current quality authority surfaces
4. API and control-plane insertion seams
5. measurement and experiment surfaces
6. token, cache, and latency risk

## Lane 1. Current Harness-to-API Truth

Live narrative routing carries harness paths as metadata, not prompt payload. `NarrativeRoute` stores `integrated_order_path`, `planning_path`, `production_path`, and `bi_path`, and the router returns those fields directly from the family plugin at `modules/narrative_router/router.py:88-103` and `modules/narrative_router/router.py:157-169`. The legacy CLI router does the same through `next_harness` at `scripts/narrative_router.py:39-49` and `scripts/narrative_router.py:147-155`.

The TR dispatch seam also resolves a harness script, not a markdown document body. `scripts/narrative_tr_batch.py:42-57` resolves the family contract and builds a subprocess command around `family.contract.tr.harness_script`. The family plugin contract points that field at `scripts/tr_batch_harness.py` or `scripts/wuxia_tr_batch_harness.py` at `modules/narrative_router/families/blockguide.py:38-57`.

Actual live prompt authority is elsewhere. `PromptLoader` resolves prompt text from `config/prompts/*.yaml` at `modules/core/prompt_loader.py:42-55` and `modules/core/prompt_loader.py:169-203`. `main_a.py:1480-1497` builds quad-agent cache context from `writer_rules.json`, `analyst_libraries.json`, and `weaver_rules.json`, then `main_a.py:1528-1534` persists that context as cached content. Live model calls then forward `contents` and `config` as-is through `modules/core/llm_generate.py:9-44` and `modules/core/providers/gemini_provider.py:11-16`.

Conclusion: no direct harness-document injection into live LLM API requests was found in the inspected runtime path.

## Lane 2. What Harnesses Currently Do

The current harness layer acts as operator guidance, routing metadata, and script-controller surface. `NarrativeFamilyPlugin.document_paths()` returns only stored document paths at `modules/narrative_router/families/base.py:12-40`. The family contract is descriptive: it names planning, production, BI, and TR harness locations, plus the TR harness script path, at `modules/narrative_router/families/blockguide.py:38-70`.

The actual TR harness scripts expose CLI command families such as `prompt`, `check`, and `merge`, and write reports or merged JSON drafts. See `scripts/tr_batch_harness.py:1361-1390` and `scripts/wuxia_tr_batch_harness.py:1111-1140`. In the inspected sections, they behave like bounded batch-production tools, not live model prompt injectors.

Stage detection tests also treat the router as a filesystem-and-contract classifier rather than a prompt-authority source. See `tests/test_wuxia_narrative_router_and_bi.py:195-219`.

Conclusion: current harnesses are mainly process and orchestration artifacts. They are not presently the authoritative live prompt layer.

## Lane 3. Where Quality Authority Actually Lives Today

The current writer path already assembles a dense structured prompt from runtime context. `modules/domain/agents/writer.py:76-96` collects prompt context, and `modules/domain/agents/writer.py:155-182` includes pattern logic, reference anchors, genre rules, mandatory context, justification guidance, HUD trend, and NPC-frequency warning. `modules/domain/agents/writer.py:216-252` then builds the final task prompt with blueprint, realtime state, previous ending, arc tactics, and pattern guidance. If a cache exists, the live call uses cached content plus the task prompt at `modules/domain/agents/writer.py:271-286`.

The review side is also not thin. `modules/validation/scoring_validator.py:53-60` defines weighted score axes, `modules/validation/scoring_validator.py:145-153` combines deterministic and LLM-evaluated scores, and `modules/validation/scoring_validator.py:193-279` runs article-based narrative evaluation against the manuscript plus dynamic context. `modules/validation/advisory_validator.py:41-70` adds heuristic improvement suggestions, and `modules/validation/advisory_validator.py:127-151` optionally asks the model for expression improvements. `modules/domain/agents/manuscript_validator.py:20-27` and `modules/domain/agents/manuscript_validator.py:82-176` provide a Python-first warning layer before Director review.

`main_a.py:1480-1497` and `main_a.py:1528-1534` show that writer, analyst, and weaver already receive persistent cached context from prompt and rule files, not from harness docs.

Conclusion: raw harness markdown would mostly duplicate existing instruction sources on the hot path. The only likely unique value is not the full document body, but a distilled subset of hard stage rules that current prompt contracts do not yet encode explicitly.

## Lane 4. API and Control-Plane Insertion Seams

There is a technically easy transport seam if a future experiment wants to pass a harness-derived payload from desktop to backend. The public API contract already allows an open-ended `inputs` object at `docs/implementation/api-contract-v1.yaml:383-399`. The desktop preload bridge forwards `key`, `subKey`, `inputs`, and `approvalId` at `geuldobi-desktop/src/preload.js:40-42`, and the main Electron process relays the run request through bridge fetch at `geuldobi-desktop/src/main.js:722-777` and `geuldobi-desktop/src/main.js:779-780`. The backend parses `inputs` and passes it straight to `ProcessRunner.start()` at `modules/api/bridge_server.py:2327-2385`.

That seam is transport only. `ProcessRunner` already reserves some `inputs` keys for stdin shaping and env injection, including `stdin_lines`, `project_index`, `genre_index`, API keys, and webhook or Vertex env fields at `modules/api/process_runner.py:703-778` and `modules/api/process_runner.py:780-810`. The control-plane contract explicitly defines `/status` and `/quality/dashboard` as companion snapshots, not durable authority, at `modules/api/control_plane_contract.py:7-15` and `modules/api/control_plane_contract.py:41-66`.

Conclusion: a harness payload can be transported through `/run`, but that is a plumbing seam, not proof that the payload belongs on the quality-critical prompt path.

## Lane 5. Measurement and Experiment Surfaces

The workspace already has enough measurement surface to test the hypothesis without inventing a net-new observability stack.

`QualityDashboard` records validation, score, quality-signal, and retrieval-observation history at `modules/core/quality_dashboard.py:24-44`, `modules/core/quality_dashboard.py:69-86`, `modules/core/quality_dashboard.py:127-143`, and `modules/core/quality_dashboard.py:200-228`. That is enough for per-stage quality-delta tracking if a new prompt variant is introduced.

The benchmark lane already exists. `scripts/run_gold_manuscript_benchmark.py:27-56` builds a manuscript-only benchmark package, `scripts/run_gold_manuscript_benchmark.py:95-117` can generate candidate continuations with models, and `scripts/run_gold_manuscript_benchmark.py:159-180` emits comparison results. The prior survey at `docs/2026-03-27/gold-manuscript-benchmark-mvp-survey-3pass-audit.md:1-19` and `docs/2026-03-27/gold-manuscript-benchmark-mvp-survey-3pass-audit.md:171-178` already concluded that a compact benchmark MVP is viable and survey-complete.

The soak harness lane is also present. `scripts/run_auto_frontier_lag_harness.py:82-117` defines bounded soak overrides for model tier, manuscript length, and heavy-path toggles; `scripts/run_auto_frontier_lag_harness.py:196-255` exposes those seams in CLI; `scripts/run_auto_frontier_lag_harness.py:455-478` persists soak-profile metadata into the run manifest. Tests cover reduced-length all-flash profiles and restore behavior at `tests/test_auto_frontier_lag_harness.py:261-336` and `tests/test_auto_frontier_lag_harness.py:339-400`.

The current limitation is known. The earlier soak survey explicitly states that the current harness can prove liveness and sink alignment but does not yet read or score `episode_bibles`, `state_logs`, or `world_state` at `docs/2026-03-27/frontier-lag-soak-canary-compact-survey.md:156-186`.

Conclusion: an A/B experiment is already practical for prose and continuity quality. A deeper long-memory/state-retention claim still needs an expanded observability lane.

## Lane 6. Token, Cache, and Latency Risk

The stack is tolerant of large prompt text, which is useful for flexibility but risky for indiscriminate harness injection.

Prompt gating is char-based and happens after assembly. `BaseAgent` uses `ContextLimits.MAX_CONTEXT_CHARS` at `modules/domain/agents/base_agent.py:186-187`; the prompt size gate truncates only after the full prompt exists at `modules/domain/agents/base_agent.py:312-330`; and the same gate is applied to the wrapped ask prompt at `modules/domain/agents/base_agent.py:806-816` and cached-context ask path at `modules/domain/agents/base_agent.py:2155-2160`. The SSOT default remains very large at `config/settings/validation.yaml:76` and `modules/core/constants.py:136-165`.

Context caching is also sticky. `config/system.yaml:15-19` sets a high output budget and `config/system.yaml:36-39` sets cache minimum content at 50,000 characters. `BaseAgent` caches large text when above the threshold at `modules/domain/agents/base_agent.py:2070-2108`, while `main_a.py:1528-1534` creates 24-hour quad-agent cached content from writer, analyst, or weaver context. If raw harness docs are appended carelessly, they can become part of a long-lived cached context rather than a one-off experiment input.

Provider behavior is not perfectly normalized. Anthropic clamps sync `max_tokens` to its local maximum at `modules/core/providers/anthropic_provider.py:67-79`, while the OpenAI provider forwards caller-provided output caps at `modules/core/providers/openai_provider.py:41-55`. The router and helper layers do not add source-aware prompt budgeting; they forward `contents` and `config` through `modules/core/llm_generate.py:18-44`.

Conclusion: raw harness injection has medium-to-high risk of context dilution, silent truncation, cache pollution, higher spend, and inconsistent backend behavior before any quality gain is proven.

## Synthesis

The inspected evidence does not support a blanket "give the API the harness" strategy. The current runtime already has several denser and more stage-localized instruction sources than the harness docs:

- prompt YAML under `config/prompts`
- project prompt JSON such as `writer_rules.json`
- runtime mandatory context
- reference anchors
- genre guards
- validator and Director review layers
- cached agent context

That means raw harness markdown is likely to be mostly redundant text on the hot path. The likely upside is not "more words" but "missing rules made explicit." The right target is therefore a compiled harness digest, not the raw document.

The digest should be small, stage-local, and structured. A minimal first version should contain only:

- `family`
- `stage`
- `hard_prohibitions`
- `required_outputs`
- `acceptance_gates`
- `stage_specific_must_do`
- `stage_specific_must_not_do`

Even that digest should not be injected everywhere. The most plausible high-ROI surfaces are:

- planning/TR/BI prompt bundle generation
- Director or scoring-review prompts when judging structure or compliance

The least plausible surfaces are:

- desktop bridge `/run` metadata by itself
- full raw writer prompt on every manuscript generation call
- cached quad-agent context without a prior A/B result

## Recommended Experiment Shape

If implementation is approved, the smallest defensible experiment is three-arm, bounded, and measured:

1. baseline: current prompt stack only
2. raw-harness arm: inject raw markdown once, only to falsify the naive hypothesis quickly
3. digest arm: inject a structured stage-specific harness digest

Measure with:

- gold manuscript benchmark for continuity and relative prose quality
- quality dashboard metrics for per-stage pass and score drift
- retrieval observation for prompt-source coverage change
- soak harness only for bounded liveness and stability checks, not as sole proof of narrative quality

Success should require improvement in at least one narrative metric without unacceptable regression in latency, token usage, or prompt truncation incidence.

## Side-Effect Coverage

- file writes: inspected benchmark outputs, harness manifests, reports, and survey-doc save path; no runtime file mutation performed in this turn
- DB writes: inspected only; no new DB write path exercised
- JSONL and audit sinks: inspected control-plane provenance and quality-metric surfaces; no new sink mutation performed
- console and UI surfaces: inspected desktop bridge, `/run`, `/status`, and bridge transport flow
- rollback and recovery: inspected soak override restoration and harness boundedness through existing tests and survey docs
- cache and global state: inspected BaseAgent context cache and quad-agent cached-content paths
- config and env mutation: inspected `ProcessRunner` env injection and benchmark credential loading paths
- non-applicable in this turn: no live run, no canary execution, no code realization

## Final Decision

The evidence supports a narrow yes and a broad no.

- broad no: do not feed raw harness documents into all live API calls
- narrow yes: test a compact structured harness digest on a small number of stage-specific prompt surfaces

That path is more likely to raise quality than raw markdown injection because it adds missing rule signal without paying the full redundancy and context-budget penalty.

## 3-Pass Audit

Pass 1, structure and scope:
- the document stayed survey-only
- scope, exclusions, queue note, and commit-state metadata are explicit
- PASS

Pass 2, evidence and consistency:
- claims were tied to inspected runtime code, contracts, prior survey docs, and tests
- canonical and temp semantics are not mixed because no execution SSOT was opened
- PASS

Pass 3, execution and readability:
- the document ends in an actionable recommendation and a bounded experiment shape
- it avoids escalating directly into implementation while still naming a viable next execution step
- PASS

Confidence: 0.96
Final decision: save approved
