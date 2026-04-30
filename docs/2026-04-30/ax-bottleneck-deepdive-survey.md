# AX팀 제공 자료 제작 및 3pass 감리 - 병목 딥다이브 Survey

Date: 2026-04-30

Branch: `codex/ax-review-packet-3pass`

HEAD: `ae57b439 Refresh ops queue state`

Related issue: `#145 AX팀 제공 자료 제작 및 3pass 감리`

Status: 3pass audited survey packet v0.1

## 0. Executive Summary

AX팀에 먼저 전달할 핵심은 "AI 티 나는 문장 polish"가 아니라 Stage4 수렴 비용, 권한층 혼선, stale lineage, token/cache/model 구조다.

현재 시스템은 0_카나리아 15화까지 usable first-draft를 생산했지만, 이 성과는 비싼 retry/repair/post-select loop를 통과해서 얻은 결과다. 즉 "생산 가능"은 증명됐고, "비용/지연/판정 해석 가능성/품질 수렴"이 다음 병목이다.

Top bottleneck ranking:

1. Stage4 convergence cost: post-select conflict와 full rewrite retry가 최대 병목.
2. Authority-layer conflation: Director verdict, runtime route verdict, settled attempt verdict가 운영상 섞여 보임.
3. Stage3/Stage4 lineage freshness: stale frontier/blueprint/accepted manuscript linkage가 재오염과 retry를 유발할 수 있음.
4. Token/model/cache architecture: pro-model 장문 context, 3-way writer ensemble, fallback/cache miss가 지연과 비용을 키움.
5. Ops SSOT drift: GitHub issue, `docs/temp`, ClickUp, historical handoff만 믿으면 stale 판단으로 빠질 수 있음.
6. Anti-AI-slop/prose polish: 실제 독자-facing 문제지만, 앞 1-4번이 먼저 풀려야 polish가 안정적으로 먹힘.

AX팀에는 "살려 주세요"보다 아래처럼 물어야 한다.

- Stage4 post-select conflict를 full rewrite로 닫는 현재 정책이 비용 대비 맞는가?
- Director 의미 판단과 deterministic runtime gate를 어떤 계약으로 분리해야 하는가?
- 3-way writer ensemble, 10-round cap, 65k output cap, large context budget, cache policy를 어떻게 줄이면 품질 손실 없이 latency/cost가 내려가는가?
- anti-AI-slop은 upstream prompt/rubric, Director review, export formatter, separate polish pass 중 어디에 둬야 하는가?

## 1. Evidence Scope

This document is based on read-only evidence collection.

Used evidence classes:

- Live code/config: `modules/`, `config/models.yaml`, `config/system.yaml`, `config/settings/validation.yaml`.
- Live DB: `projects/0_카나리아/project_data.db`, read-only SQLite queries.
- Live logs: `projects/0_카나리아/logs/episode_production.jsonl`.
- Local artifact stats: `projects/0_카나리아/drafts/ep_*.txt`, local combined manuscript variants.
- Recent dated docs: `docs/2026-04-28/`, `docs/2026-04-29/`, `docs/2026-04-30/`.
- Historical queue surfaces: GitHub issue references, `docs/temp`, ClickUp sync state, treated as context only unless live-confirmed.

Important exclusions:

- No code edits were made for this survey.
- No original `projects/0_카나리아` artifacts were modified.
- Raw prompts, raw `llm_io.jsonl`, full manuscript text, and secret-like local material should not be sent to AX without redaction.
- Python was used for data collection/aggregation only. Semantic priority and bottleneck judgment remain an LLM/Director-side conclusion.

Residual evidence caveats:

- GitHub/ClickUp live state was not re-synced in this packet.
- Some local manuscript/checklist artifacts are untracked and should be labeled "local evidence snapshot", not canonical production truth.
- The packet is a bottleneck survey, not a fresh full live-run validation.

## 2. System Composition

AX-facing high-level architecture:

```text
Material / project inputs
  - treatments, bible, phase/tr/bi material
  - project DB and prior stage artifacts
  - runtime config and model routing

        |
        v

main_a.py / stage orchestrators
  - Stage2/Stage3 planning, blueprint, validation, carryover
  - Stage4 episode drafting and settlement

        |
        v

Stage4 production loop
  1. context assembly and cache lookup
  2. ChiefWriter candidate generation / ensemble
  3. pre-Director validation and warning collection
  4. Director review
  5. PASS / REJECT / PASS_WITH_FIX normalization
  6. PASS_WITH_FIX patch and re-audit loop
  7. post-select continuity/history checks
  8. retry routing, full rewrite, inplace repair, or settlement

        |
        v

Persistence and observability
  - SQLite: stage_attempts, llm_calls, context_cache_attempts, cost_log
  - JSONL logs: episode_production, runtime audit, llm IO
  - artifact tree: rejected/final attempts, post-pass evidence
  - draft text files and combined manuscript exports
```

Runtime authority shape:

```text
Director semantic judgment
        |
        v
Python/runtime route gates
  - quality floor
  - PASS_WITH_FIX contract enforcement
  - deterministic continuity/history post-select checks
  - dead-character / hard invariant checks
        |
        v
settled attempt verdict
  - PASS
  - REJECT
  - EMPTY
  - retry route / settlement route
```

The current bottleneck is not that one of these layers exists. The bottleneck is that AX/operator views can collapse them into one "verdict", making retry behavior hard to reason about.

## 3. Main Data Flow

### 3.1 Stage4 Episode Flow

1. Stage4 orchestrator opens an episode round.
2. Mandatory context, manuscript history, blueprint/carryover material, and retrieval context are assembled.
3. ChiefWriter generates candidates, often through an ensemble path.
4. Prevalidation and advisory lanes collect warnings before Director review.
5. Director emits a semantic verdict and repair guidance.
6. Runtime normalizes the verdict:
   - low-score PASS can become REJECT route;
   - invalid/nonlocal PASS_WITH_FIX can become REJECT;
   - repair scope can be widened.
7. Positive verdicts go through post-select checks.
8. Post-select conflict can downgrade a provisional PASS/PWF result to REJECT and often routes to full rewrite.
9. PASS results enter post-pass settlement and artifact persistence.

### 3.2 Observability Flow

Primary observability surfaces:

- `stage_attempts`: attempt-level verdict, episode, duration, failure category, failure layer, artifact path, advisory flags.
- `llm_calls`: model, agent, prompt/response token counts, cached tokens, duration, success/error, cost estimate.
- `context_cache_attempts`: cache creation/hit/skipped states and content size.
- `episode_production.jsonl`: higher-level runtime events such as `STAGE4_RETRY_PATHOLOGY`, `V75-D_INPLACE`, `V75-B_FULL_REGEN`, post-select conflict details.

AX packet should prefer DB/log aggregate extracts over raw prompts or raw manuscript.

## 4. Model Information

Live config evidence:

- `config/models.yaml` routes pro-heavy roles to `vertexai:gemini-3.1-pro-preview`.
- Key pro roles include `analyst`, `chief_writer`, `blueprint_ensemble`, `three_phase_blueprint_generator`, `state_locked_arc_generator`, `four_phase_arc_generator`, `continuity_inspector`, and `director`.
- Fallback chain includes `vertexai:gemini-3.1-pro-preview -> vertexai:gemini-2.5-pro -> vertexai:gemini-2.5-flash`.
- `config/system.yaml` sets `api.max_output_tokens: 65536` and `api.timeout: 300`.
- `config/settings/validation.yaml` sets `retry.director_max_attempts: 10`.
- `config/settings/validation.yaml` sets `scoring.quality_gate_score: 90`.

AX questions on model policy:

- What is the exact Vertex AI billing for `vertexai:gemini-3.1-pro-preview`, including thought tokens, cache create/read/storage, and large-context pricing?
- Is one multi-candidate request cheaper/faster than three parallel ChiefWriter calls?
- Should `max_output_tokens` be lowered by role?
- Should Stage4 round cap stay at 10, align to old operator wording 5, or adopt an intermediate cap?
- Should local char-count heuristics be replaced with provider `count_tokens` before routing/caching?

## 5. Live Bottleneck Evidence

### 5.1 Stage4 attempt ledger

Read-only DB query from `projects/0_카나리아/project_data.db`.

Stage4 attempt verdicts:

| verdict | attempts | episode range | total duration ms |
| --- | ---: | --- | ---: |
| REJECT | 22 | ep3-ep14 | 10,181,454 |
| PASS | 15 | ep1-ep15 | 6,785,731 |
| EMPTY | 1 | ep8 | 341,467 |

Retry-heavy episodes:

| episode | attempts | verdict path | dominant categories |
| ---: | ---: | --- | --- |
| 5 | 6 | REJECT x5 -> PASS | LOGIC_ERROR, POST_SELECT_CONFLICT, CONSTRAINT_VIOLATION |
| 10 | 5 | REJECT x4 -> PASS | CONSTRAINT_VIOLATION, POST_SELECT_CONFLICT, LOGIC_ERROR |
| 12 | 5 | REJECT x4 -> PASS | POST_SELECT_CONFLICT, QUALITY_ISSUE |
| 7 | 4 | REJECT x3 -> PASS | POST_SELECT_CONFLICT |
| 8 | 3 | REJECT -> EMPTY -> PASS | POST_SELECT_CONFLICT |
| 9 | 3 | REJECT x2 -> PASS | POST_SELECT_CONFLICT |

Gate semantics distribution:

| gate basis | count |
| --- | ---: |
| post_select_conflict | 14 |
| director_primary_pass | 9 |
| patch_reaudit_pass | 6 |
| continuity_firewall | 5 |
| director_primary_reject | 3 |
| blank / not captured | 1 |

Interpretation:

The strongest live signal is post-select conflict after generation and Director review. This is expensive because the system has already spent tokens to produce and judge a candidate before the downstream gate rejects it.

### 5.2 Stage4 LLM cost and latency ledger

Read-only DB query from `llm_calls where stage=4`.

Totals:

| calls | input tokens | output tokens | cached tokens | estimated cost USD | avg duration ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 653 | 13,402,078 | 1,566,917 | 6,987,784 | 24.404141 | 48,819.6 |

Top agent/model cost rows:

| agent | model | calls | total tokens | estimated cost USD | avg ms | non-success |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| chief_writer | vertexai:gemini-3.1-pro-preview | 269 | 8,878,731 | 16.017692 | 82,647.4 | 17 |
| director | vertexai:gemini-3.1-pro-preview | 271 | 4,939,301 | 5.549227 | 20,547.3 | 12 |
| chief_writer | vertexai:gemini-2.5-pro | 23 | 368,672 | 1.637426 | 64,770.3 | 0 |
| director | vertexai:gemini-2.5-pro | 44 | 490,294 | 0.752089 | 27,352.6 | 0 |

Interpretation:

ChiefWriter and Director dominate Stage4 cost. The likely optimization target is not a generic "use cheaper model everywhere" change. It is role-specific: candidate generation, judging, post-select checks, PWF repair, and full rewrite retry need separate budgets and stop conditions.

### 5.3 Cache evidence

Stage4 context cache attempts:

| agent | cache type | outcome | count | content chars |
| --- | --- | --- | ---: | ---: |
| chief_writer | manuscript | created | 35 | 3,742,256 |
| director | director_ensemble | created | 22 | 1,685,173 |
| director | director_ensemble | skipped | 14 | 420,016 |
| director | manuscript | skipped | 14 | 384,157 |
| director | director_ensemble | hit | 7 | 506,020 |
| director | blueprint | skipped | 2 | 4,128 |
| chief_writer | manuscript | skipped | 1 | 39,526 |

Interpretation:

Caching exists and helps, but hit ratio and cache lineage policy are not yet enough to make Stage4 cheap. AX should inspect whether cache thresholds, TTL, model-exact cache keys, fallback behavior, and direct router bypasses are cost-positive.

### 5.4 Runtime log signal

`episode_production.jsonl` evidence:

- 91 records.
- `STAGE4_RETRY_PATHOLOGY`: 23 records.
- `post_select_conflict` gate basis: 30 records.
- `POST_SELECT_CONFLICT` error category: 30 records.
- `V75-D_INPLACE`: 7 records.
- `V75-B_FULL_REGEN`: 2 records.

Interpretation:

The log signal agrees with the DB: Stage4 convergence and post-select conflict are the dominant runtime pathology, not only a document-roadmap opinion.

### 5.5 Prose / anti-AI-slop signal

Local artifact stats:

| artifact | chars | lines | paragraphs | headers | bracket lines | lines >120 | lines >200 | paragraphs >400 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0_합본.txt` | 96,047 | 2,555 | 1,003 | 0 | 1 | 151 | 38 | 5 |
| `0_합본_anti_ai_slop패스.txt` | 88,695 | 2,927 | 1,124 | 0 | 1 | 95 | 4 | 0 |
| `0_합본_문체숨통패스.txt` | 91,279 | 2,843 | 1,105 | 0 | 1 | 115 | 7 | 1 |

Draft stats:

- 15 draft files.
- 15 markdown title headers in draft files.
- 3 standalone bracket cue lines across drafts.

Interpretation:

Anti-AI-slop and line/paragraph readability are real product issues. However, they are downstream polish unless they reveal an upstream state/genre/rubric defect. Blind Python rewriting is risky; AX should help decide whether this belongs in upstream generation prompt, Director rubric, export formatter, or a separate LLM polish pass.

## 6. Bottleneck Register

### B1. Stage4 convergence and post-select conflict

Evidence:

- 22 Stage4 REJECT attempts and 1 EMPTY attempt before 15 final PASS attempts.
- 14 DB attempts with `gate_basis=post_select_conflict`.
- 30 log records with `POST_SELECT_CONFLICT` category or `post_select_conflict` gate basis.
- Retry-heavy episodes ep5, ep7, ep8, ep9, ep10, ep12.

Why this matters:

Post-select conflict runs after expensive candidate generation and Director judgment. If it routes to full rewrite too often, the system pays for work that is later discarded.

AX asks:

- Should post-select conflict always be fail-closed full rewrite?
- Can post-select checks become earlier, cheaper, or confidence-tiered?
- Can bounded patch be used for some conflict subtypes without violating continuity?
- What telemetry is needed to distinguish true semantic contradiction from validator/check exception?

### B2. Authority-layer conflation

Evidence:

- Director PASS-like output can be route-normalized by runtime gates.
- Quality floor can route low-score PASS to REJECT.
- PASS_WITH_FIX contract enforcement can widen repair or reject invalid local fixes.
- Post-select can downgrade a provisional positive verdict.

Why this matters:

Operators and dashboards need to know whether "reject" came from Director semantics, deterministic safety, post-select continuity, or settlement policy. Otherwise "Director passed but system retried" looks like contradiction rather than layered control.

AX asks:

- Should every attempt expose `director_verdict`, `runtime_route_verdict`, and `settled_attempt_verdict`?
- Which deterministic gates are allowed to overrule Director?
- Should score floor be Director-owned quality judgment or deterministic route safety?
- What should UI/operator copy say when a provisional PASS is downgraded?

### B3. Stage3/Stage4 lineage and stale frontier

Evidence:

- Historical handoffs around #120/#121/#57 are partially stale against current closure state.
- Frontier/accepted manuscript linkage remains a root trust concern.
- Current ops guidance says live code/DB/log/artifact evidence outranks historical issue/temp roadmap text.

Why this matters:

If Stage4 drafts are generated from stale frontier, stale blueprint, or stale accepted manuscript context, post-select and continuity gates will keep catching defects late.

AX asks:

- What fingerprint should invalidate cached context after accepted manuscript changes?
- Should cache lineage include run id, artifact revision, upstream stage state, and accepted manuscript hash?
- Can stale-frontier detection run before expensive generation?

### B4. Token, model, cache, and timeout architecture

Evidence:

- Stage4: 653 LLM calls, 13.4M input tokens, 1.57M output tokens, 6.99M cached tokens, estimated cost $24.40.
- `max_output_tokens` is 65,536 globally.
- Stage4 Director max attempts is 10.
- ChiefWriter and Director pro calls dominate cost.

Why this matters:

Cost is concentrated enough to optimize surgically. A generic model downgrade could reduce quality; a role-aware policy could reduce waste while preserving quality.

AX asks:

- Which calls need `gemini-3.1-pro-preview` and which can move to flash/pro fallback?
- Should writer ensemble be replaced by one multi-candidate call?
- Should max output and thinking budgets be role-specific?
- What cache policy is actually cost-positive on Vertex for Korean long-form context?

### B5. Observability and SSOT drift

Evidence:

- `docs/temp` mirrors are not canonical by themselves.
- ClickUp is human-facing summary, not SSOT.
- GitHub issues can lag live code/DB/log evidence.
- Recent historical docs correctly explain lineage but may no longer be current truth.

Why this matters:

AX will receive a distorted picture if the packet is assembled from issue labels or old roadmaps rather than live evidence.

AX asks:

- What minimal dashboard should exist for per-episode Stage4 convergence?
- Should each rejected attempt show gate layer, cost, duration, and retry route?
- What fields are required to separate API latency, retry sleep, continuation, cache write/read, and fallback hops?

### B6. Anti-AI-slop and prose polish

Evidence:

- Draft headers and bracket cues exist in draft/export surfaces.
- Combined manuscript variants show line/paragraph readability can be improved.
- The current slop metric is narrow and does not prove prose quality.

Why this matters:

This is the visible reader-quality layer. It should be fixed, but not by blind deterministic rewrite that can damage prose or semantic continuity.

AX asks:

- Should polish be a separate LLM pass after Stage4 settlement?
- Should Director rubric include anti-slop/paragraph rhythm checks earlier?
- Which signals are hard gates, and which are editorial advisories?
- Can sanitized before/after excerpts be shared for review?

## 7. AX Share Packet Proposal

Recommended packet to AX:

1. `ax-system-architecture.md`
   - high-level architecture diagram
   - stage roles
   - authority layering

2. `ax-data-flow.md`
   - Stage4 data flow
   - DB/log/artifact observability flow
   - retry and settlement flow

3. `ax-model-cost-ledger.md`
   - model routing table
   - Stage4 cost/call aggregate
   - cache evidence
   - concrete billing questions

4. `ax-bottleneck-register.md`
   - B1-B6 bottlenecks
   - evidence and questions
   - recommended investigation order

5. Optional redacted appendix
   - per-episode attempt ledger
   - sanitized rejected/final pair snippets
   - no raw prompt, no full manuscript, no secrets

## 8. Recommended Next Work Order

Recommended next action:

1. Build the AX packet from this survey as separate docs.
2. Add sanitized aggregate tables only.
3. Do not include full manuscript or raw prompt/log text unless explicitly approved.
4. Ask AX to focus first on B1-B4:
   - Stage4 convergence/post-select;
   - verdict authority split;
   - lineage/cache invalidation;
   - model/token/cache/cost policy.
5. Treat anti-AI-slop as the first downstream editorial optimization after B1-B4 are understood.

## 9. 3pass Audit Log

### Pass 1 - Factual Alignment

Checks:

- Branch and HEAD were rechecked: `codex/ax-review-packet-3pass`, `ae57b439`.
- Stage4 attempt/cost/cache figures were regenerated from read-only SQLite queries.
- Log category counts were regenerated from `episode_production.jsonl`.
- Model/config claims were anchored to live config search results.

Result:

- PASS.
- Confidence: 96%.
- Residual risk: no fresh live run was executed; figures describe the current local DB/log snapshot.

### Pass 2 - Governance and Safety

Checks:

- System-track order and document-save rule applied.
- Python used only for data collection/aggregation.
- No code or project artifacts were modified.
- Untracked manuscript/checklist artifacts are labeled as local evidence, not canonical SSOT.
- Raw prompts, raw manuscript, raw `llm_io.jsonl`, and secret-like data are excluded from AX sharing recommendation.

Result:

- PASS.
- Confidence: 96%.
- Residual risk: external GitHub/ClickUp state was not live-synced in this packet.

### Pass 3 - Usefulness for AX Team

Checks:

- The document covers AX's requested surfaces: system composition, data flow, model information.
- The bottleneck register maps each finding to concrete AX questions.
- The ranking separates root pipeline bottlenecks from downstream prose polish.
- The packet proposal avoids overloading AX with raw internal artifacts while preserving enough evidence to diagnose cost/latency/token problems.

Result:

- PASS.
- Confidence: 95%.
- Residual risk: AX may request a sanitized fixture or additional call-level traces after first review.

Final document status:

- 3pass complete.
- Overall confidence: 95%.
- Ready to serve as the source survey for AX-facing packet documents.
