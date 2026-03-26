# Good Webnovel Corpus Usage / No-Code Integration Survey

Date: 2026-03-26
Type: static survey
Scope: whether a large corpus of good webnovel manuscripts is already used in the current system, and how it can be used without code changes
Mode: survey-only, no code changes

## Evidence Surfaces Inspected

| Surface | Path | Key Lines |
|---------|------|-----------|
| Stage 0 style corpus ingest/extract | `modules/core/stage0/style_extractor.py` | L27-65, L321, L469-544, L676, L1005-1086 |
| Stage 0 operator flow | `modules/core/stage0/__init__.py` | L740-764, L807-915 |
| Style guide load/summary helpers | `modules/core/project_support.py` | L95-115, L216-257 |
| Stage 2 compact style summary | `modules/core/stage2_preflight.py` | L458-466 |
| Stage 3 style-guide advisory | `modules/core/stage3_orchestrator.py` | L238-243, L1241-1243 |
| Stage 4 style/reference loading | `modules/core/stage4_orchestrator.py` | L31-45, L2095-2151, L2290-2293 |
| ChiefWriter context/prompt injection | `modules/domain/agents/chief_writer_context.py` | L122-140, L255, L571-574 |
| ChiefWriter prompt template | `modules/domain/agents/chief_writer_prompts.py` | L190-193 |
| Reference-anchor path | `modules/domain/agents/writer.py` | L174-202, L220 |
| Reference-anchor prompt format | `modules/core/reference_anchor.py` | L287-312 |
| Style-based validation | `modules/core/genre_guards/style_guard.py` | L23-40, L95-141 |
| Stage 0 style-reference tests | `tests/test_stage0_work_guard_style_cache.py` | L115, L180 |
| Stage 4 style-reference tests | `tests/test_stage4_orchestrator.py` | L717, L749 |

## Findings

### F1. Yes — the system already uses external manuscript corpora today

The current codebase already has a first-class path for feeding large amounts of good webnovel text into the system. The active path is:

`config/style_references/<genre>/<work_name>/*.txt`  
`-> Stage 0 reference analysis`  
`-> StyleGuide + anti-AI patterns + exemplary passages + reference_excerpt`  
`-> Stage 2 / Stage 3 / Stage 4 / StyleGuard`

This is not speculative. It is already implemented and operator-exposed:

- `StyleExtractor.prepare_reference_manuscripts()` loads workspace references and, for investment, can sync packaged references into the workspace (`style_extractor.py` L321-347).
- `StyleExtractor.extract_from_references()` merges many episode texts, analyzes them, caches the result in `style_guide.json`, and returns a `StyleGuide` object (`style_extractor.py` L1005-1086).
- `StageZeroManager.run_reference_analysis()` is an operator-facing flow that explicitly says it analyzes reference manuscripts and persists the resulting style guide (`stage0/__init__.py` L807-915).

### F2. The current system uses the corpus mainly as style/reference input, not as hard truth

What the corpus currently becomes:

- style DNA
- POV contract hints
- anti-AI patterns
- forbidden expressions
- exemplary passages
- reference excerpt for ChiefWriter

This is visible in `StyleGuide` itself:

- `anti_ai_patterns`
- `forbidden_expressions`
- `exemplary_passages`
- `reference_excerpt`
- `reference_works`

all exist as first-class fields in `StyleGuide` (`style_extractor.py` L27-65).

What it does **not** currently become:

- authoritative state ledger
- continuity SSOT
- hard factual contract
- vector-memory truth source

In other words, the corpus is currently used as a `style / voice / anti-pattern / exemplar` substrate, not as a `state / causality / authority` substrate.

### F3. The corpus already influences multiple downstream stages

This is not limited to Stage 0 storage.

1. `Stage 2`
   - `stage2_preflight.py` builds a compact style-guide summary for Analyst context (`L458-466`).
2. `Stage 3`
   - `stage3_orchestrator.py` prepends a style-guide advisory into blueprint semantic context (`L238-243`, `L1241-1243`).
3. `Stage 4`
   - `stage4_orchestrator.py` loads the saved style guide anchor, extracts `reference_excerpt`, clamps it, and carries both into the session payload (`L2095-2151`, `L2290-2293`).
   - `chief_writer_context.py` passes both the style guide and a rendered `## 참고 원고 발췌` section into the main ChiefWriter prompt (`L255`, `L571-574`).
   - `chief_writer_prompts.py` has a dedicated `문체 DNA 가이드` section that includes this payload (`L190-193`).
4. `Validation`
   - `StyleGuard` consumes `anti_ai_patterns`, `forbidden_expressions`, and target sentence-length distribution derived from `StyleGuide` and warns on drift (`style_guard.py` L23-40, L95-141).

So the answer to "are we already using it" is not just "yes, a little." It is `yes, through several real production lanes`.

### F4. The current design is extract-and-distribute, not raw-corpus retrieval

The observed pattern is:

- Stage 0 reads the raw corpus
- Stage 0 compresses it into structured style artifacts
- later stages consume summary/excerpt forms

Important evidence:

- `extract_from_drafts()` samples up to 1,000,000 chars, performs statistics, curation, rhythm analysis, optional LLM qualitative analysis, and builds a `reference_excerpt` from the sampled text (`style_extractor.py` L469-544, L676-720).
- `Stage 4` then clamps the excerpt again to the runtime budget (`stage4_orchestrator.py` L31-45).

This means the system is already designed to handle a lot of text, but by `compressing it before runtime`, not by dragging the full corpus into every generation call.

### F5. ReferenceAnchor is related, but it is not the same thing as your external corpus

There is also a `ReferenceAnchor` system, but it serves a different purpose.

- `ReferenceAnchor` extracts structured anchors from already-produced manuscripts and builds a mandatory reference prompt (`reference_anchor.py` L287-312).
- `writer.py` injects this prompt into writing contexts when available (`writer.py` L185-202, L220).

This is a runtime memory / continuity support path.
It is **not** the same as “I have a huge external corpus of good webnovels.”

So:

- external corpus -> Stage 0 style/reference pipeline
- produced internal manuscripts -> ReferenceAnchor runtime memory

### F6. I did not find a live vector-embedding path for the external corpus

Targeted code search found the `style_references` / `StyleGuide` / `reference_excerpt` family in:

- Stage 0
- project support helpers
- Stage 2/3/4 prompt/context surfaces
- style validation

I did **not** find evidence that this external corpus is currently wired as a first-class vector-retrieval or semantic-memory substrate.

This is an inference from the inspected usage distribution, not a claim that vector infrastructure does not exist anywhere in the codebase. The narrower claim is:

`the external good-webnovel corpus is currently wired as a style/reference input, not as a vector-backed truth/retrieval input.`

## What You Can Already Do Right Now Without Code Changes

### Current no-code operator path

1. Organize the corpus as UTF-8 `.txt` episodes under:
   - `config/style_references/<genre>/<work_name>/0001.txt`
   - `config/style_references/<genre>/<work_name>/0002.txt`
   - ...
2. Run Stage 0 `스타일 레퍼런스 분석`.
3. Let Stage 0 generate and persist `style_guide.json`.
4. Use the resulting project normally.
   - Stage 2 gets a compact style summary.
   - Stage 3 gets a compact style/anti-AI advisory.
   - Stage 4 gets style guide + reference excerpt.
   - validation can use style-derived warning criteria.

Evidence:

- operator flow: `stage0/__init__.py` L740-915
- packaged investment reference sync test: `tests/test_stage0_work_guard_style_cache.py` L115
- POV contract propagation test: `tests/test_stage0_work_guard_style_cache.py` L180
- saved-style Stage 4 load test: `tests/test_stage4_orchestrator.py` L717

### Best way to structure a large corpus under the current design

The current implementation is more likely to work well if you split the corpus by:

- genre/family
- tone/voice cluster
- POV compatibility

than if you dump every “good webnovel” into one giant mixed bucket.

Why:

- `StyleGuide` extracts a single condensed style contract.
- mixed POV / mixed tone / mixed paragraph rhythm will collapse into a blur.
- Stage 0 samples and compresses; it does not preserve all distinct voices as independent runtime profiles.

So the good current use is:

- `investment/high-tension-first-person`
- `investment/corporate-cool-third-person`
- `actor/industry-snappy-mixed-pov`

style banks, not a universal everything-bucket.

## What This Corpus Is Good For Under The Current Architecture

| Use | Current Fit | Why |
|-----|-------------|-----|
| Style DNA extraction | High | Already implemented in Stage 0 |
| Anti-AI pattern mining | High | Already stored and used by `StyleGuard` |
| Exemplary passage curation | High | Already extracted into `exemplary_passages` |
| Stage 4 voice/reference support | High | `reference_excerpt` already injected |
| POV and paragraph rhythm biasing | Medium-High | Present, but compressed into one guide |
| Genre exemplar bank | Medium | Achievable now via curation and folder discipline |
| Hard continuity truth | Low / wrong fit | Corpus text is not authoritative state |
| Ledger/resource truth | Low / wrong fit | Should stay in fact/state contracts |
| Vector semantic truth retrieval | Not currently wired | No direct live path found in inspected surfaces |

## What This Corpus Should Not Be Asked To Do

The surveyed code does **not** support using your external corpus as the main answer to:

- "what is the protagonist's exact current state"
- "what happened in the previous episode"
- "what account currently owns the money"
- "what is the authoritative continuity truth"

Those should remain in:

- blueprint/state packets
- fact ledger / immutable fact contracts
- prior-episode continuity artifacts

If you push the corpus into those jobs, it stops being a style/reference bank and starts competing with the real authority layers.

## Best Future Expansion Directions

No code changes were requested, so these are design observations only.

### Safe future direction

- Keep external manuscripts as a `style/reference corpus`.
- Expand curation quality, not authority scope.
- Add more genre/family-specific banks instead of one mega-bank.

### Higher-ROI future uses

- genre-family exemplar banks
- protagonist voice banks
- scene-type exemplar banks
  - negotiation
  - daily-life slice
  - public humiliation / reversal
  - boardroom / agency / guild / sect reaction
- anti-pattern banks by genre

### Bad future direction

- turning external corpus into state-truth authority
- using webnovel corpus as carry-forward ledger
- mixing style corpus with continuity SSOT

## Single Recommendation

If you already have a lot of good webnovel text, `yes, you can use it now`, and the natural no-code path is:

`external corpus -> Stage 0 style reference analysis -> saved StyleGuide -> Stage 2/3/4 + StyleGuard`

The highest-ROI operator move is not new code. It is:

1. curate the corpus by genre/family/voice
2. place it under `config/style_references/<genre>/...`
3. run Stage 0 style-reference analysis
4. treat the result as style/reference support, not continuity truth

---

## 3-Pass Audit Notes

- Pass 1: confirmed current usage surfaces across Stage 0, Stage 2, Stage 3, Stage 4, ReferenceAnchor, and StyleGuard
- Pass 2: separated “already active now” from “possible future use” and explicitly separated external corpus from internal runtime anchor memory
- Pass 3: checked that the final recommendation stays no-code and does not overclaim vector or hard-truth integration
- Confidence: 97%

---

- Current usage status: **active** (Stage 0 style/reference ingest -> downstream style summary/excerpt/guard use)
- Best no-code usage path: **Stage 0 style-reference analysis via `config/style_references/<genre>/...`**
- Should Codex open an execution SSOT now: **no**
