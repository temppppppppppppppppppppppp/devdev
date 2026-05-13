# 글도비 모델/프롬프트 캐싱 미팅 브리프

- Date: 2026-05-13
- Status: final, 3-pass audited
- Scope: 2026-05-13 오후 미팅 대비. 사용 모델, 프롬프트/컨텍스트 캐싱, 관련 운영 논점.
- Track: system order, survey/documentation only
- Canonical Path: `docs/2026-05-13/geuldobi-model-cache-meeting-brief-3pass-audit.md`
- Temp Mirror: not applicable. This is a meeting brief, not an execution SSOT.
- Baseline Commit: `294cbab3026b6b705f8e22bbc0155fc363724537`
- Baseline Dirty Summary: clean at start of investigation (`git status --short` output empty)
- Side-Effect Coverage: read-only code/docs/DB/log inspection plus this final document write; no code, DB, config, or runtime mutation
- Confidence: 96%

## 1. Executive Brief

회의에서 가장 먼저 잡아야 할 메시지는 이것입니다.

1. 현재 글도비 런타임의 주력 모델은 OpenAI가 아니라 Vertex AI 경유 Gemini입니다.
2. `config/models.yaml` 기준 주력 상위 모델은 `vertexai:gemini-3.1-pro-preview`, 저비용/보조 모델은 `vertexai:gemini-2.5-flash`, emergency fallback은 `vertexai:gemini-2.5-pro`입니다.
3. OpenAI provider는 코드상 존재하지만 `config/models.yaml`에서 `enabled: false`입니다.
4. 최근 대표 DB(`projects/0_카나리아/project_data.db`) 기준 캐싱은 실제로 작동했습니다: `llm_calls` 1,108건 중 input 33.3M tokens, cached 19.2M tokens, cached input share 약 57.7%.
5. 다만 캐시 생성 게이트가 `min_content_chars: 50000` 문자 기준이라, 공식 Vertex/Gemini token 기준보다 보수적으로 스킵하는 호출이 많습니다. 이 부분이 가장 즉시 논의할 만한 개선점입니다.
6. 비용 숫자는 내부 추정치로는 유용하지만, `gemini-3.1-pro-preview` 전용 가격표가 `MODEL_COSTS`에 없고 default 비용표로 계산됩니다. 외부 보고용 금액으로 쓰기 전 가격 테이블 갱신이 필요합니다.

## 2. Current Model / Provider Facts

### 2.1 Config SSOT

`config/models.yaml`이 모델 라우팅의 현재 SSOT입니다.

- Enabled providers:
  - `gemini`: enabled
  - `vertex_ai`: enabled, `auth_mode: auto`
  - `anthropic`: enabled
  - `openai`: disabled
  - `anthropic_vertex`: disabled
- Agent map:
  - `vertexai:gemini-3.1-pro-preview`: `analyst`, `chief_writer`, `blueprint_ensemble`, `three_phase_blueprint_generator`, `state_locked_arc_generator`, `four_phase_arc_generator`, `continuity_inspector`, `director`
  - `vertexai:gemini-2.5-flash`: `manager`, `block_enricher`, `preflight_checker`, `state_extractor`, `arc_corrector`, `arc_critic`, `consensus_validator`, `unified_arc_validator`, `unified_blueprint_validator`, `critic`, `weaver`, `writer`
- Fallback chain:
  - `vertexai:gemini-3.1-pro-preview` -> `vertexai:gemini-2.5-pro`
  - `vertexai:gemini-2.5-pro` -> `vertexai:gemini-2.5-flash`
  - `vertexai:gemini-2.5-flash` -> itself

Code anchors:

- `modules/core/models_config.py:15-20` defines inline fallback defaults only when YAML is absent/incomplete.
- `modules/core/models_config.py:124-144` loads `config/models.yaml`.
- `modules/core/llm_router.py:49-74` infers provider from model prefix.
- `modules/core/llm_router.py:177-190` fails loudly if a provider is disabled or unregistered.
- `modules/core/providers/openai_provider.py:116-128` uses OpenAI Responses API when enabled.

Meeting readout:

- If someone asks "what model are we using now?", answer: "Operationally Vertex/Gemini, mostly `vertexai:gemini-3.1-pro-preview` for high-reasoning stages and `vertexai:gemini-2.5-flash` for support lanes. OpenAI support is present but not active."
- If someone asks "can we switch to OpenAI?", answer: "Yes in architecture, but it is not a config-only production switch yet. We need model map, cost table, cache telemetry, prompt-cache controls, and validation."

### 2.2 OpenAI Comparison Point

Official OpenAI model docs currently recommend `gpt-5.5` as the flagship for complex reasoning/coding and smaller `gpt-5.4` variants for lower cost/latency. OpenAI prompt caching is automatic for recent models and can reduce latency/cost when long prompt prefixes repeat.

OpenAI-specific gaps in current repo if migration/comparison is raised:

- `config/models.yaml` has `openai.enabled: false`.
- `OpenAIProvider._build_request_kwargs()` passes only a narrow config set: `temperature`, `top_p`, `max_output_tokens`, `store`, and structured-output formatting.
- It does not currently pass `prompt_cache_key` or `prompt_cache_retention`.
- `OpenAIProvider.generate()` extracts `input_tokens`, `output_tokens`, `total_tokens`, but not nested `prompt_tokens_details.cached_tokens`.
- `BaseAgent._normalize_usage()` maps `input_tokens`/`output_tokens` to internal Gemini-style keys, but has no OpenAI cached-token bridge.

Implication:

- With OpenAI, caching could work automatically provider-side, but 글도비 would not yet report cache hits correctly in `llm_calls.cached_tokens` unless the adapter is extended.

Official source anchors:

- OpenAI Models: `https://developers.openai.com/api/docs/models`
- OpenAI Prompt Caching: `https://developers.openai.com/api/docs/guides/prompt-caching`

## 3. Current Caching Architecture

### 3.1 Two Cache Families

There are two different cache families in the codebase.

1. Legacy startup cache in `main_a.py`
   - `_ignite_quad_cache_system()` creates Writer / Analyst / Weaver caches.
   - Stores cache names in DB anchor `sys_caches`.
   - Uses TTL `86400s`.
   - Skips only when context text is under 1,500 chars.
   - Anchors: `main_a.py:1452-1499`, `main_a.py:1529-1566`, `main_a.py:1599-1610`.

2. Runtime context cache in `BaseAgent`
   - `_get_or_create_context_cache()` hashes content, namespaces by project/scope, checks model/provider lineage, and creates explicit Gemini/Vertex caches.
   - Default minimum is `config/system.yaml` `cache.min_content_chars: 50000`.
   - TTL is usually 600s for Stage3/Stage4 shared context; some direct calls use 1800s.
   - All attempts are written to `context_cache_attempts`; used/failed/bypassed cache calls are written to `llm_calls`.
   - Anchors: `modules/domain/agents/base_agent.py:2414-2418`, `base_agent.py:2494-2630`, `base_agent.py:2698-2878`, `base_agent.py:775-817`, `modules/core/db_manager.py:3564-3668`, `db_manager.py:3670-3728`.

### 3.2 Active Cache Surfaces

Primary explicit-cache surfaces:

- Stage2 arc ensemble:
  - Shared context = previous arc context + constraint block.
  - Anchor: `modules/domain/agents/arc_ensemble.py:1039-1047`.
- Stage3 blueprint ensemble:
  - Shared context = constraints + arc focus + previous info + HUD.
  - Stubbed prompt slots use `[context cached: refer to cached_content]` when cache exists.
  - Anchors: `modules/domain/agents/blueprint_ensemble.py:787-840`, `blueprint_ensemble.py:1421-1496`, `blueprint_ensemble.py:1498-1538`.
- Stage4 chief writer:
  - Shared context = `common_context`, strategy/output stay dynamic.
  - Anchor: `modules/domain/agents/chief_writer.py:795-806`, `chief_writer.py:1306-1327`.
- Director modules:
  - Multiple director-side cache callsites exist through `director_caching.py`, `director_continuity.py`, and `director_ensemble.py`.

### 3.3 Auth / Provider Gate

Explicit Vertex context cache is intentionally skipped if the active Google client says provider mode is `vertex_ai` and Vertex auth mode is `api_key`.

- Anchor: `modules/domain/agents/base_agent.py:2378-2383`.
- Google client metadata is attached in `modules/core/google_client_factory.py:135-139`.
- `build_google_genai_client()` chooses Vertex `api_key` vs `project_credentials` in `modules/core/google_client_factory.py:86-127`.

Meeting readout:

- If explicit cache is required, run mode must be checked: `GEULDOBI_PROVIDER_MODE=vertex_ai` plus `GEULDOBI_VERTEX_AUTH_MODE=project_credentials` is the safer production posture.
- Prior 2026-04-27 handoff already warned that API-key auth could override project/location credentials unless `GEULDOBI_VERTEX_AUTH_MODE=project_credentials` is set.

## 4. Live Evidence From `projects/0_카나리아`

Read-only DB query against:

- `projects/0_카나리아/project_data.db`
- Last `llm_calls` timestamp: `2026-04-30T03:56:30`
- Last `context_cache_attempts` timestamp: `2026-04-30T03:54:14`

### 4.1 Overall LLM / Cache Metrics

| Metric | Value |
| --- | ---: |
| `llm_calls` total | 1,108 |
| input tokens | 33,319,120 |
| output tokens | 3,465,008 |
| cached tokens | 19,224,405 |
| calls with cached tokens | 264 |
| cached input share | 57.7% |
| internal estimated cost | $54.1230 |

Model split:

| Model | Calls | Input | Cached | Cached Calls | Internal Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| `vertexai:gemini-3.1-pro-preview` | 1,000 | 32,325,111 | 19,197,119 | 260 | $51.2532 |
| `vertexai:gemini-2.5-pro` | 74 | 802,114 | 0 | 0 | $2.6898 |
| `vertexai:gemini-2.5-flash` | 34 | 191,895 | 27,286 | 4 | $0.1800 |

High-leverage stage/agent rows:

| Stage / Agent | Calls | Input | Cached | Cached Share | Internal Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage3 `blueprint_ensemble_generator` | 268 | 17,822,457 | 11,621,398 | 65.2% | $25.2787 |
| Stage4 `chief_writer` | 292 | 7,803,625 | 5,810,838 | 74.5% | $17.6551 |
| Stage4 `director` | 315 | 5,334,426 | 1,171,917 | 22.0% | $6.3013 |

Interpretation:

- Cache transport is not theoretical anymore; it is materially active.
- Stage3 and Chief Writer are the best proof points for "cache is helping".
- Director cache share is lower, probably because some Director calls are short/control-heavy rather than large-context calls.

### 4.2 Context Cache Attempts

| Outcome | Count |
| --- | ---: |
| total attempts | 228 |
| created | 76 |
| hit | 32 |
| skipped | 120 |
| error | 0 |
| bypassed | 0 |

Top skip buckets:

| Cache Type | Reason | Attempts | Min..Max Chars | Avg Chars |
| --- | --- | ---: | ---: | ---: |
| `blueprint_ensemble` | `content_too_short` | 45 | 2,644..49,854 | 20,568 |
| `blueprint` | `content_too_short` | 35 | 306..3,213 | 2,373 |
| `manuscript` | `content_too_short` | 15 | 4,070..40,429 | 28,246 |
| `director_ensemble` | `content_too_short` | 14 | 9,066..43,336 | 30,001 |
| `arc_ensemble` | `content_too_short` | 4 | 4,694..22,747 | 14,437 |

Interpretation:

- No cache-create error in this DB snapshot, which is good.
- The largest optimization target is not "cache broken"; it is "cache gate is probably skipping too conservatively".
- Several skipped contexts are 20k-49k characters. Official Vertex token minimums are lower than the current 50k-character gate, so these rows should be evaluated with real token counts.

## 5. External Cache/Model Facts To Know In Meeting

### 5.1 Vertex / Gemini

Official Vertex context caching docs say:

- Vertex supports implicit and explicit context caching for Gemini.
- `cachedContentTokenCount` in response metadata reports cached tokens.
- Implicit caching is enabled by default for Google Cloud projects.
- Explicit caching gives more control and a discount when existing context caches are referenced.
- Current Vertex limits list minimum cache token counts as 4,096 tokens for Gemini 3 / 3.1 models and 2,048 tokens for Gemini 2.0 / 2.5 models.
- Explicit cached text/blob maximum is 10 MB.

Official Gemini API docs say:

- Gemini 2.5+ has implicit caching by default.
- Explicit caching is useful when repeated large context should guarantee cost savings.
- Direct Gemini API docs list model-specific minimums such as Gemini 3 Pro Preview 4,096 tokens and Gemini 2.5 Flash 1,024 tokens.
- Cached content is treated as a prefix; standard rate/token limits still apply.

Official source anchors:

- Vertex Context Cache Overview: `https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview`
- Gemini API Context Caching: `https://ai.google.dev/gemini-api/docs/caching`

### 5.2 OpenAI

Official OpenAI prompt caching docs say:

- Prompt caching works automatically on recent models.
- Cache hits require exact prefix matches; static instructions/examples should be at the beginning, variable/user-specific content at the end.
- Caching starts for prompts of 1,024 tokens or more.
- `prompt_cache_key` can improve routing/cache hit rates for shared prefixes.
- `prompt_cache_retention` can request `in_memory` or `24h` retention on supported models.
- `cached_tokens` appears under usage prompt-token details.

OpenAI model docs currently position:

- `gpt-5.5` as flagship for complex reasoning/coding.
- `gpt-5.4-mini` / `gpt-5.4-nano` as lower-latency/lower-cost choices.

Meeting implication:

- OpenAI prompt caching is prefix/cache-key oriented. 글도비's current explicit cache design is Gemini/Vertex-specific and would not automatically map to OpenAI without adapter work.

## 6. Best Meeting Topics / Talking Points

### Topic A. Model Policy

Likely question:

- 현재 어떤 모델을 쓰고 있는지.

Prepared answer:

- Current runtime is Vertex/Gemini-first. Most Director/Blueprint/Chief Writer high-value lanes use `vertexai:gemini-3.1-pro-preview`; support lanes use `vertexai:gemini-2.5-flash`; fallback can drop to `vertexai:gemini-2.5-pro` and then Flash.

Decision points:

- Is `gemini-3.1-pro-preview` acceptable as the standard production/high-rigor model?
- Should proof runs pin a single model with `GEULDOBI_FORCE_GOOGLE_MODEL` to prevent silent fallback from invalidating evidence?
- Do we need a separate "cost mode" model map versus "quality proof mode" model map?
- If OpenAI is being considered, is the target a full migration, A/B benchmark, or only an additional fallback provider?

### Topic B. Cache Is Working, But The Gate Is Too Crude

Likely question:

- 프롬프트 캐싱 개선이 얼마나 의미 있는지.

Prepared answer:

- Recent DB evidence shows 19.2M cached tokens out of 33.3M input tokens, so cache is already a major lever. The next improvement is not building cache from zero; it is making skip decisions token-aware and making cache diagnostics first-class.

Decision points:

- Replace `min_content_chars: 50000` with provider/model-aware token thresholds.
- Add countTokens or a deterministic estimator before deciding `content_too_short`.
- Track `skipped_but_probably_cacheable` rows when content is large in characters but under the old gate.
- Keep explicit-cache TTL at 600s for per-episode ensemble fanout, but revisit 1800s/86400s only after storage-cost policy is clear.

### Topic C. Cache Telemetry / Dashboard

Likely question:

- 캐싱이 됐는지 어떻게 확인하는지.

Prepared answer:

- `context_cache_attempts` gives created/hit/skipped/error/bypassed with reason, content size, model, stage, ep. `llm_calls` gives `cached_tokens`, `context_cache_name`, and `context_cache_outcome`. These are enough for an operator dashboard.

Suggested dashboard fields:

- cached input share by stage/agent/model
- cache attempts by outcome/reason
- top skipped contexts by chars/token estimate
- cache-created-to-hit ratio by cache type
- stage cost with and without cached-token discount
- alert when cache errors appear or cached share suddenly drops

### Topic D. OpenAI / GPT Path

Likely question:

- GPT도 붙일 수 있는지, OpenAI prompt caching은 어떻게 볼지.

Prepared answer:

- The provider exists and uses Responses API, but config disables OpenAI today. To compare GPT fairly, we need to add model map entries, enable provider, pass prompt-cache controls if desired, and parse nested `cached_tokens` into existing telemetry.

Implementation prerequisites if this becomes action:

- Add `prompt_cache_key` and `prompt_cache_retention` passthrough to `OpenAIProvider`.
- Extract OpenAI usage `prompt_tokens_details.cached_tokens`.
- Add OpenAI models to cost table.
- Add deterministic tests for cache telemetry normalization.
- Run A/B on same Stage3/Stage4 canary windows rather than changing default production routing first.

### Topic E. Cost Accuracy

Likely question:

- 비용이 얼마 나오는지.

Prepared answer:

- Internal DB says recent representative project consumed about $54.12 estimated cost. Treat that as internal trend telemetry, not finance-grade external billing. The cost table has Gemini 2.5 and Claude entries, but not an explicit `gemini-3.1-pro-preview` price row, so 3.1 is likely falling through to default pricing.

Decision points:

- Update `MODEL_COSTS` for active 3.1 models after confirming current provider billing.
- Separate "usage telemetry" from "billing-authoritative numbers".
- Keep DB `llm_calls` as per-call usage source; avoid relying only on metrics JSON because older audits found crash-session undercount risk.

### Topic F. Prompt Quality vs Cache Savings

Likely question:

- 프롬프트를 줄이면 품질이 떨어지는지.

Prepared answer:

- Prior 2026-04-13 audits found concrete waste/duplication surfaces in Stage3 prompts, especially duplicated semantic context and retry feedback shape issues. Do not blindly compress context. First split static/cacheable contract, dynamic episode truth, and retry-only feedback into explicit slots, then measure reject/attempt rate.

Best next tranche:

- Token-aware cache gate first.
- Then prompt slot cleanup where prior audits already identified duplication.
- Then only after proof, consider model-tier changes.

## 7. Concrete Recommendations

Recommended meeting stance:

1. Keep the short-term default on Vertex/Gemini, because live evidence and cache telemetry already exist there.
2. Treat OpenAI as an A/B comparison track, not a same-day default migration.
3. Prioritize cache gate improvement over prompt rewrite: change from char threshold to model-aware token threshold.
4. Add OpenAI cached-token telemetry before any GPT cost/performance comparison.
5. Update cost table for active `gemini-3.1-pro-preview` before quoting dollar figures externally.
6. Use `projects/0_카나리아/project_data.db` as the concrete evidence sample in the meeting.
7. Ask for a clear decision: quality-first, cost-first, latency-first, or reliability-first. The optimal model/cache policy differs for each.

## 8. Suggested Meeting Questions

- 이번 논의의 목표를 비용 절감, 응답 속도, 품질 안정화 중 어디에 둘지.
- `gemini-3.1-pro-preview` 같은 preview 모델을 표준 운영 모델로 인정할지, proof run 전용으로 제한할지.
- 실행 증거를 엄격하게 남기는 run에서는 fallback을 허용할지, 단일 모델 pinning을 할지.
- Vertex explicit cache를 계속 쓸 경우, 운영 auth를 IAM/project credentials로 고정할지.
- OpenAI를 기본 전환, 벤치마크 비교, 장애 fallback 중 어떤 트랙으로 볼지.
- 캐시/비용 대시보드를 DB 기반으로 만들지, 외부 billing export와 대조하는 구조까지 원하는지.
- 프롬프트 최적화를 토큰 절감 목적만이 아니라 retry 품질 개선까지 포함해 볼지.

## 9. Action 후보

No code changes were made under this document. If this meeting turns into implementation work, smallest safe order is:

1. Cache audit script: per project DB에서 cache share / skipped reason / likely-cacheable bucket report.
2. Token-aware cache gate: `content_chars` gate를 provider/model token threshold 기반으로 교체.
3. OpenAI telemetry bridge: `cached_tokens` extraction and `prompt_cache_key` passthrough.
4. Cost table update: active Gemini 3.1 and any OpenAI target model rows.
5. A/B canary: same Stage3/Stage4 scope with model map variants.

## 10. 3-Pass Audit Record

### Pass 1 - Structure and Scope

PASS.

- Document type matches the request: meeting-prep brief, not execution SSOT.
- Scope covers model usage, prompt/context caching, OpenAI/Gemini comparison, telemetry, cost caveats, and likely meeting questions.
- Path policy is correct: canonical dated doc only, no temp mirror.
- Existing temp execution queue was inspected but not used because this request is independent survey/documentation work.

### Pass 2 - Evidence and Consistency

PASS.

- Model facts verified against `config/models.yaml`, `modules/core/models_config.py`, `modules/core/llm_router.py`, and provider adapters.
- Cache flow verified against `main_a.py`, `BaseAgent`, `blueprint_ensemble.py`, `arc_ensemble.py`, `chief_writer.py`, and DB sink methods.
- Live metrics verified via read-only SQLite query against `projects/0_카나리아/project_data.db`.
- Official external facts checked against OpenAI, Gemini API, and Vertex AI docs on 2026-05-13.
- Cost caveat included because `MODEL_COSTS` lacks an explicit `gemini-3.1-pro-preview` row.

### Pass 3 - Readability and Operating Use

PASS.

- The document starts with meeting-ready summary before evidence.
- Recommendations are separated from raw evidence.
- OpenAI comparison is framed as a possible track, not as current runtime truth.
- No implementation is implied as already done.
- Confidence remains above threshold because all major claims are bounded to inspected code, DB rows, or official docs.

Final confidence: 96%.
