Date: 2026-03-27
Status: final
Document Type: system-track LLM-friendliness + gimmick-elegance lane survey report
Canonical Path: `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt.md`
- `docs/2026-03-26/llm-multi-provider-context-note.md`
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked llm_router/provider/context/validator surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked multi-provider docs, fact docs, anthropic_vertex provider scaffolding/tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## 1. Executive Summary

The Writer / Prompt / Context Injection lane has improved since the prior 2026-03-24 T3 survey but remains **mixed** in gimmick elegance. The Wave 1 per-work fact authority changes (authority statement, advisory suppression, immutable fact contract) are individually well-designed, but their integration into the prompt assembly pipeline adds more injection points without a unifying injection registry or declared tier map.

The two dominant elegance concerns are:

1. **Injection precedence is multi-layered but never declared as a single map.** Tier 0/1/2 membership is built by insertion order across 300+ lines of `_build_mandatory_context_seed()`, not by a declared priority model. A cold LLM must trace 4-5 file hops to reconstruct the full injection stack.

2. **The 35-parameter forwarding chain** remains the top contract inelegance. It was flagged in the prior survey and is unchanged.

The gimmicks that work well are: advisory suppression (`_filter_state_tracker_summaries_for_authority`), the YAML-SSOT prompt externalization, and the immutable fact contract module. These are explicit, localized, and traceable in 2-3 file hops.

| Axis | Status | Versus Prior Survey |
|---|---|---|
| Navigation | Ready | Stable -- ToC and delegation chain docs landed |
| Authority | Clear | Improved -- authority statement + advisory suppression added |
| Contract | Mixed | Unchanged -- 35-param forwarding still dominates |
| Observability | Good | Stable -- tier budget logging improved |
| Gimmick Elegance | Mixed | New gimmicks individually elegant; aggregate injection stack is accreted |
| Local Readability | Mixed | Minor improvement -- compat stubs documented but still present |

Navigation-ready for this lane: **yes**
Cheap-fix-first verdict: **yes**
Gimmick-elegance verdict: **mixed**
Boundary-refactor can wait: **yes**
Top 3 highest-ROI quick wins in this lane:
1. Add a tier injection map comment to `stage4_context_builder.py:1600` (comment-only)
2. Add prompt-facing authority precedence map to `stage4_context_builder.py:996` (comment-only)
3. Add escape-responsibility note to `chief_writer_prompts.py:50` (comment-only)

---

## 2. Included Coverage / Exclusions

### Included (Primary Scope)

| File | Path | Lines | Delta vs Prior |
|---|---|---|---|
| chief_writer.py | `modules/domain/agents/chief_writer.py` | 2,283 | +9 |
| chief_writer_context.py | `modules/domain/agents/chief_writer_context.py` | 604 | +24 |
| chief_writer_context_packets.py | `modules/domain/agents/chief_writer_context_packets.py` | 1,126 | +138 |
| chief_writer_prompts.py | `modules/domain/agents/chief_writer_prompts.py` | 298 | +13 |
| writer_template.py | `modules/core/writer_template.py` | 420 | 0 |
| prompt_builder.py | `modules/core/prompt_builder.py` | 968 | 0 |
| stage4_context_builder.py | `modules/core/stage4_context_builder.py` | 2,787 | +58 |
| stage4_context_packets.py | `modules/core/stage4_context_packets.py` | 802 | 0 |

Total: **9,288 lines** across 8 files (prior: 9,046; delta: +242).

Growth is concentrated in `chief_writer_context_packets.py` (+138, carryover ceiling section) and `stage4_context_builder.py` (+58, Wave 1 authority/suppression logic).

### Excluded

- `chief_writer_quality.py` (quality gate sub-module, not in primary scope)
- `writer_prompt_builders.py` (shared prompt utilities)
- `stage4_immutable_fact_contract.py` (imported by chief_writer_context.py; checked for injection contract only)
- Stage 4 interview/director/orchestrator files (T3 lane in this wave)
- Upstream callers in `stage4_interview_round.py`

---

## 3. Current Read Order / Ownership / Gimmick Map

### 3.1 Read Order

1. **`chief_writer_prompts.py`** (298 lines) -- YAML-SSOT prompt externalization
2. **`chief_writer_context.py`** (604 lines) -- CW prompt assembly orchestrator
3. **`chief_writer_context_packets.py`** (1,126 lines) -- bounded packet rendering
4. **`chief_writer.py`** (2,283 lines) -- ensemble engine + facade
5. **`writer_template.py`** (420 lines) -- blueprint-to-template structural mapping
6. **`prompt_builder.py`** (968 lines) -- SovereignApp-level prompt generation
7. **`stage4_context_builder.py`** (2,787 lines) -- episode-level context + tier composition
8. **`stage4_context_packets.py`** (802 lines) -- continuity/fact/relationship packet rendering

### 3.2 Ownership Map

| Concern | Owner | Gimmick? |
|---|---|---|
| Ensemble strategy selection + parallel generation | `chief_writer.py` `ChiefWriter` | No |
| CW prompt assembly (main template) | `chief_writer_context.py` `ChiefWriterContextBuilder.build_common_context()` | No |
| CW prompt template string | `chief_writer_prompts.py` `build_chief_writer_main_prompt()` | No |
| CW packet rendering (digest, guards, HUD, NPC freq) | `chief_writer_context_packets.py` `ChiefWriterContextPackets` | No |
| Tier 0/1/2 composition + budget trimming | `stage4_context_builder.py` `_compose_tiered_mandatory_context_with_headroom()` | **Yes** |
| Advisory suppression (7 domains) | `stage4_context_builder.py` `_filter_state_tracker_summaries_for_authority()` | **Yes** |
| Authority statement injection | `stage4_context_builder.py` `_build_persisted_authority_statement()` | **Yes** |
| Immutable fact contract packet | `chief_writer_context.py` -> `stage4_immutable_fact_contract.py` | **Yes** |
| Genre-specific injection gates | `stage4_context_builder.py` L1702-1718 (wuxia), `chief_writer_context.py` L226 (investment), L334-359 (incarnation) | **Yes** |
| Prompt-facing precedence (STEP 0.5) | `chief_writer_prompts.py` L129-135 (template prose) | **Yes** |
| Context budget trimming with protected indices | `stage4_context_builder.py` `_apply_context_budget()` L1145-1255 | **Yes** |
| Arc position / HI zone guides | `prompt_builder.py` `PromptBuilder` | No |
| Blueprint scene template structure | `writer_template.py` `WriterTemplate` | No |

### 3.3 Gimmick Map

| # | Gimmick | Owner File:Line | Elegance | Hops to Trace |
|---|---|---|---|---|
| G1 | Tier 0/1/2 injection model | `stage4_context_builder.py:1261-1378` | Mixed | 4-5 |
| G2 | Advisory suppression (7 domains) | `stage4_context_builder.py:939-971` | **Elegant** | 2 |
| G3 | Authority statement injection | `stage4_context_builder.py:996-1008` | **Elegant** | 2 |
| G4 | Immutable fact contract packet | `chief_writer_context.py:525-560` -> `stage4_immutable_fact_contract.py` | **Elegant** | 3 |
| G5 | Prompt-facing precedence (STEP 0.5) | `chief_writer_prompts.py:129-135` | Mixed | 1 (prose only) |
| G6 | Genre-specific injection gates | scattered (3 files, 3 patterns) | Mixed | 3-4 |
| G7 | Context budget trimming | `stage4_context_builder.py:1145-1255` | Mixed | 2 |
| G8 | Wuxia technique/realm authority clause | `stage4_context_builder.py:1702-1718` | Mixed | 2 |
| G9 | 35-parameter forwarding chain | `chief_writer.py:566` -> `chief_writer_context.py:114` -> `chief_writer_prompts.py:50` | **Inelegant** | 3 (identical signatures) |
| G10 | Genre code map duplication | `chief_writer.py:37` + `chief_writer_context.py:34` | **Inelegant** | 2 |

---

## 4. Top Hotspots

| # | File:Line | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|
| H1 | `stage4_context_builder.py:1600-1730` | Gimmick | **P1** | `_build_mandatory_context_seed()` builds tier0 through 6 sequential insertion blocks (canonical constraints, fact ledger, world state, timeline, continuity packet, authority clauses). Insertion order is the de facto tier membership, but no comment declares the resulting stack or explains why `insert(0, ...)` is used everywhere. | comment-only |
| H2 | `chief_writer.py:566-615` | Contract | **P1** | `generate_ensemble()` still has 35 keyword parameters. `_prepare_generate_ensemble_context()` (L289-324) takes the same 35. Three levels of identical parameter lists with no change since prior survey. | contract-cleanup |
| H3 | `stage4_context_builder.py:1145-1255` | Gimmick | **P1** | `_apply_context_budget()` has a 3-round trimming sequence (regular -> protected -> emergency). Protected indices are determined by string prefix matching (`"[작품 추적 슬롯 요약]"`, `"[SC:arc_semantic_carryover]"`). The precedence of what survives trimming is implicit in code order. | comment-only |
| H4 | `chief_writer_prompts.py:50-86` | Contract | **P1** | `build_chief_writer_main_prompt()` has 29 keyword parameters. Some are pre-escaped by caller, some are raw. No contract note distinguishes escape responsibility. The version tags ([V67], [V68], [IFC], [TF-2]) serve as provenance markers but not authority markers. | comment-only |
| H5 | `stage4_context_builder.py:1702-1718` | Gimmick | **P2** | Wuxia technique/realm authority clause is injected via ad-hoc string comparison (`_genre_name in ("무협", "wuxia")`). Other genre gates (investment, incarnation type) live in different files. No unified genre injection registry. | doc-only |
| H6 | `chief_writer.py:37-48` | Local Read | **P2** | `_CW_GENRE_CODE_MAP` (10 entries) duplicates a subset of `_GENRE_CODE_ALIASES` (20 entries) in `chief_writer_context.py`. `_CW_GENRE_CODE_MAP` has zero runtime references beyond its definition. | contract-cleanup |
| H7 | `chief_writer_context_packets.py:53-63` | Gimmick | **P2** | 4 delegate methods forward to `owner` via untyped `*args, **kwargs`. The delegation chain docstring at file top (L1-11) documents the ownership but does not list expected parameter types per delegate. | comment-only |
| H8 | `stage4_context_builder.py:35-106` | Contract | **P2** | 8 TypedDict definitions. Some field names overlap (`tier1_parts`, `tier2_parts` appear in 3 TypedDicts). No comment maps which TypedDict flows into which method. | comment-only |

---

## 5. Top Quick Wins

### Comment-Only

| # | Target | Action |
|---|---|---|
| QW-1 | `stage4_context_builder.py:1600` | Add a **tier injection stack map** comment before `_build_mandatory_context_seed()` explaining the resulting tier0 ordering: `canonical constraints > fact ledger > world state > timeline > authority statement > continuity packet > arc constraints > genre authority clauses`. This makes the de facto precedence explicit. |
| QW-2 | `stage4_context_builder.py:996` | Add a note to `_build_persisted_authority_statement()` explaining that this is the **prompt-facing authority declaration** and its relationship to the advisory suppression at L939. Together they form the Wave 1 authority contract. |
| QW-3 | `chief_writer_prompts.py:50` | Add docstring: "All string parameters are expected pre-escaped by the caller via `_escape_braces()`. Exceptions: `ep_num` (int), `common_rules`/`writing_guidelines` (YAML-loaded, no braces). Version tags ([V67], [V68], [IFC], [TF-2]) mark provenance, not authority." |
| QW-4 | `stage4_context_builder.py:1145` | Add a comment before `_apply_context_budget()` listing the trim precedence: "Regular sections trimmed first (ratio=0.7) -> protected sections trimmed gently (ratio=0.88) -> emergency pass if still over. Protected prefixes: `[작품 추적 슬롯 요약]`, `[SC:arc_semantic_carryover]`." |

### Doc-Only

| # | Target | Action |
|---|---|---|
| QW-5 | `docs/2026-03-23/llm-codebase-orientation-pack.md` section 9 | Add note: "Genre-specific injection gates are currently ad-hoc across 3 files (stage4_context_builder.py for wuxia authority, chief_writer_context.py for investment guidelines and incarnation type). No unified genre injection registry exists; each gate checks genre independently." |

### Contract-Cleanup

| # | Target | Action |
|---|---|---|
| QW-6 | `chief_writer.py:37-48` | Remove `_CW_GENRE_CODE_MAP` if confirmed unused (grep shows zero runtime references beyond definition). The canonical SSOT is `_GENRE_CODE_ALIASES` in `chief_writer_context.py`. |

**Rule check:** 6 quick wins. 4 comment-only + 1 doc-only = 5 (83%) cheap items. 1 contract-cleanup. More than half are comment/doc/observability. Minimum 5 met.

---

## 6. Gimmick Elegance Judgment

### Elegant Gimmicks

| Gimmick | Why Elegant |
|---|---|
| **G2: Advisory suppression** (`_filter_state_tracker_summaries_for_authority`) | One owner (stage4_context_builder.py:939). Explicit input: `summaries: dict[str, str]`. Explicit output: `(kept, suppressed)`. Precedence over neighboring domains is declared in the overlap_sources dict. Traceable in 2 hops. |
| **G3: Authority statement** (`_build_persisted_authority_statement`) | One owner (stage4_context_builder.py:996). Pure function with boolean inputs. Output is a structured authority text block. No side effects. |
| **G4: Immutable fact contract** (`build_packet` + `render_packet_for_cw`) | Separate module with clean API. Called from one site in chief_writer_context.py:525. Input contract explicit. 3 hops to trace. |

### Mixed Gimmicks

| Gimmick | Why Mixed |
|---|---|
| **G1: Tier 0/1/2 injection model** | The concept is sound (canonical > retrieval > advisory). But tier membership is determined by insertion position in a 130-line method, not by a declared schema. A cold LLM cannot determine tier membership without reading all insertion calls. |
| **G5: STEP 0.5 precedence** | Declares a clear rule in the prompt template (Opening Anchor > Immutable Facts > Structured scene > Advisory prose). But the template physically places sections in order of assembly, not in order of authority. The LLM-facing rule is correct; the code-facing assembly order is different. |
| **G6: Genre-specific gates** | Each individual gate (wuxia authority, investment guidelines, incarnation type) is simple and localized. But they live in 3 different files with 3 different patterns. No registry or pattern guides future genre additions. |
| **G7: Context budget trimming** | Functional and well-logged. But the protected-vs-regular distinction relies on string prefix matching, not a declared priority field on the section objects. |
| **G8: Wuxia technique/realm clause** | Correctly injected as a tier0 authority statement. But the genre check is ad-hoc (`_genre_name in ("무협", "wuxia")`) rather than using the established genre guard system. |

### Inelegant Gimmicks

| Gimmick | Why Inelegant |
|---|---|
| **G9: 35-parameter forwarding** | Three levels of identical keyword parameter lists (generate_ensemble -> _prepare_generate_ensemble_context -> build_common_context -> build_chief_writer_main_prompt). Survives by accretion. Each new feature (V67, V68, IFC, TF-49b, TF-54c) added 1-2 more params to all levels. Not composable, not localized. |
| **G10: Genre code map duplication** | `_CW_GENRE_CODE_MAP` (10 entries) in chief_writer.py has no runtime callers. `_GENRE_CODE_ALIASES` (20 entries) in chief_writer_context.py is the actual SSOT. The duplication survives from a legacy split. |

### Overall Gimmick-Elegance Verdict: **mixed**

The Wave 1 authority gimmicks (G2, G3, G4) are individually elegant. The aggregate injection pipeline (G1) is functional but not self-documenting. The parameter forwarding chain (G9) remains the dominant inelegance and is the only gimmick that would benefit from a structural fix rather than a comment.

---

## 7. Deferred Refactor Candidates

| # | Target | Action | Classification | Notes |
|---|---|---|---|---|
| DR-1 | `chief_writer.py:566` + L955 | Extract the 35 shared parameters into a `WriterEnsembleRequest` dataclass. Eliminates 3 levels of verbatim forwarding. | contract-cleanup, **long-term** | Blast radius: medium (stage4_interview_round.py callers must update). Highest ROI structural fix for this lane. Flagged in prior survey; still valid. |
| DR-2 | `stage4_context_builder.py:1600-1730` | Extract tier0 injection into a declarative tier-membership list: `[(priority, builder_fn, label)]`. Replace sequential `insert(0, ...)` calls with sorted composition. | boundary-refactor, **long-term** | Would make the injection stack self-documenting. Current functional behavior is correct; this is a comprehension aid. |
| DR-3 | Genre injection gates (3 files) | Centralize genre-specific injection decisions into the established genre guard system (`sys.guard`). Each guard could expose a `get_writer_authority_clauses()` method. | boundary-refactor, **defer** | Low urgency -- only 3 genre gates exist. Worth doing if genre expansion continues. |

**Rule check:** 3 deferred refactor candidates. Capped at 3. All marked long-term or defer.

---

## 8. No-Action / Settled Areas

| Area | Reason |
|---|---|
| `chief_writer_prompts.py` | Clean YAML-SSOT externalization. 10 small functions. No gimmick. No comprehension hazard. Settled. |
| `writer_template.py` | Self-contained dataclass design with Enum-based scene types. No gimmick. No delegation complexity. Settled. |
| `prompt_builder.py` section dividers | Already has `=====` section dividers at L82, L154, L546, L697, L767, L859. Pure vs app-dependent split documented in class docstring. Settled. |
| `stage4_context_builder.py` Navigation ToC (L4) | ToC was added since the prior survey. Lists major sections with descriptions. Settled. |
| `chief_writer_context_packets.py` delegation chain docstring (L1-11) | Added since prior survey. Clearly describes `ChiefWriter -> ChiefWriterContextBuilder -> ChiefWriterContextPackets` chain. Settled. |
| `chief_writer.py` delegation band header (L2144-2155) | Documents the 9 quality-gate forwarding stubs. Header explains facade pattern and "Do NOT add business logic here." Settled for comment-only; compat stub removal is a long-term concern. |
| `stage4_context_packets.py` | Clean delegation pattern. Continuity/relationship/fact packet rendering is well-structured with budget-based truncation. No new gimmick since prior survey. Settled. |
| `stage4_context_builder.py` TypedDicts (L35-106) | Well-typed contract surface. 8 TypedDict definitions with descriptive field names. Minor overlap is manageable. Settled (minor comment-only candidate at H8 but low priority). |

---

## 9. Cross-Lane Handoff Notes

### To T3 (Stage 4 Authority / Verdict / Retry Gimmicks)
- `stage4_interview_round.py` is the primary caller of `ChiefWriter.generate_ensemble()`. The 35-parameter interface (G9) is the T4 contract surface that T3 must assemble.
- `Stage4ContextBuilder.build_mandatory_context()` (L2340-2378) is called from `stage4_interview_round.py` and returns a `Stage4MandatoryContextPayload` TypedDict. This is the handoff point from T3's verdict/retry loop into T4's context assembly.

### To T5 (Fact Authority / Genre Gimmick / Contract State)
- G2 (advisory suppression) and G3 (authority statement) are the T4-side implementations of the per-work fact authority contract documented in `per-work-fact-contract-alignment-residual-survey.md`. T5 should verify that these injections match the residual survey's tier architecture.
- G8 (wuxia technique/realm authority) is a Wave 1 residual extension specific to the wuxia genre. T5's genre guard surfaces should note that this gate bypasses the guard system.

### To T2 (Provider / Router / Backend Elegance)
- No direct coupling. The writer/context lane is provider-neutral -- all LLM calls go through `BaseAgent.ask()` which routes via `llm_router`. The multi-provider work does not impact T4 contract surfaces.

### To T6 (Observability / Peripheral)
- `stage4_context_builder.py` has extensive budget/tier logging (`[S4:CTX]`, `[SC]`, `[CP]`, `[Phase1-L0]` prefixes). T6 should verify these log lines are coherent for operator truth reconstruction.

### To T1 (Navigation / Entry)
- The orientation pack (section 9) describes the dual context-builder pipeline. No update needed unless the tier injection map comment (QW-1) changes the documented architecture.

---

## 10. Confidence And Limits

**Overall confidence: 96%**

Breakdown:
- Navigation: 94%. ToC and delegation chain docs are in place. `stage4_context_builder.py` has a ToC but no mid-file section dividers beyond it.
- Authority: 93%. Wave 1 authority gimmicks are explicit and well-placed. The tier injection order is correct but implicit.
- Contract: 75%. The 35-parameter forwarding chain remains the dominant friction. No change since prior survey. TypedDicts are well-typed but under-documented.
- Gimmick Elegance: 80%. 3 elegant + 5 mixed + 2 inelegant. The aggregate injection pipeline works correctly but a cold LLM must reconstruct tier membership from insertion order.
- Observability: 92%. Budget logging is detailed. Context assembly has `logging.info` at major injection points.

Limits:
- `stage4_immutable_fact_contract.py` was checked only for its injection contract, not for internal implementation quality (out of T4 primary scope).
- `chief_writer_quality.py` is excluded from primary scope; the 9 forwarding stubs in chief_writer.py are assessed from the facade side only.
- The tier injection stack was reconstructed from live code reading, not from a runtime trace. Actual execution ordering may differ under error/fallback paths.

---

## 11. 3-Pass Audit Record

### Pass 1. Structure and Scope
- Verified all 10 mandatory report sections present.
- Scope matches T4 master order assignment.
- Gimmick map section (section 3.3) added per gimmick-elegance order requirements.
- Fix types assigned to all findings.
- Quick wins: 6 items, 5 (83%) are comment/doc/observability. Rule satisfied.
- Deferred refactors: 3 items, all marked long-term/defer. Cap satisfied.

### Pass 2. Evidence and Consistency
- Line counts verified against `wc -l` on all 8 files (total: 9,288).
- Prior survey findings cross-checked: landed items marked settled, open items retained.
- Gimmick elegance test applied to all 10 identified gimmicks per master order section 4.
- File:line anchors verified against live source.
- Tier injection ordering verified against `_build_mandatory_context_seed()` code path.

### Pass 3. Execution and Readability
- Report is survey-only. No code changes, no execution SSOT, no queue artifacts.
- Cross-lane handoff notes reference specific method signatures and line anchors.
- Verdicts are explicit per mandatory rules.
- No overreach into implementation recommendations beyond fix-type classification.
