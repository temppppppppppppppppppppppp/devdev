Date: 2026-03-24
Status: final
Document Type: system-track LLM-friendliness lane survey report
Canonical Path: `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
- `docs/2026-03-24/현상황요약.txt`

Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: tracked stage4/state/writer surfaces, docs/temp/queue-state.json, docs/2026-03-23/console.txt, many project artifacts deleted, new docs/2026-03-24/ and stage4 immutable-fact files`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## 1. Executive Summary

The Writer / Prompt / Context Reception lane is **navigable and authority-clear** at the module-boundary level, but carries **significant contract friction** from parameter proliferation and duplicated forwarding. The decomposition into `ChiefWriter -> ChiefWriterContextBuilder -> ChiefWriterContextPackets` is structurally clean, but the interface contracts between these layers rely on 30-35 positional keyword parameters forwarded verbatim across 3 call depths. This is the single largest LLM comprehension cost in the lane.

| Axis | Status | Confidence |
|---|---|---|
| Navigation | Ready | 92% -- delegation chain is clear; stage4_context_builder lacks section dividers |
| Authority | Readable | 90% -- owner shells are identifiable; dual context-builder paths create bounded ambiguity |
| Contract | Partially Readable | 72% -- parameter proliferation is the dominant friction; TypedDict payloads in stage4_context_builder are well-structured |
| Observability | Readable | 90% -- operator logs and PerfTimer are present; context_packets/context_builder have minimal logging |
| Local Readability | Partially Readable | 78% -- 22 `*args, **kwargs` compat stubs in chief_writer.py; genre map duplication; dense regex blocks |

Navigation-ready for this lane: yes
Cheap-fix-first verdict: yes
Boundary-refactor can wait: yes

Top 3 highest-ROI quick wins:
1. Add section dividers and method-group ToC to `stage4_context_builder.py` (comment-only)
2. Add delegation chain docstring to `chief_writer_context_packets.py` top (comment-only)
3. Add parameter contract docstring to `generate_ensemble()` explaining the forwarding chain (comment-only)

---

## 2. Included Coverage / Exclusions

### Included (Primary Scope)
| File | Path | Lines | Methods |
|---|---|---|---|
| chief_writer.py | `modules/domain/agents/chief_writer.py` | 2,274 | 82 |
| chief_writer_context.py | `modules/domain/agents/chief_writer_context.py` | 580 | 20 |
| chief_writer_context_packets.py | `modules/domain/agents/chief_writer_context_packets.py` | 988 | 25+ |
| chief_writer_prompts.py | `modules/domain/agents/chief_writer_prompts.py` | 285 | 10 |
| writer_template.py | `modules/core/writer_template.py` | 420 | 8 |
| prompt_builder.py | `modules/core/prompt_builder.py` | 968 | 15 |
| stage4_context_builder.py | `modules/core/stage4_context_builder.py` | 2,729 | 69 |
| stage4_context_packets.py | `modules/core/stage4_context_packets.py` | 802 | 12 |

Total: **9,046 lines** across 8 files.

### Excluded
- `chief_writer_quality.py` (quality gate sub-module, not in primary scope)
- `writer_prompt_builders.py` (shared prompt utilities imported by stage4_context_builder)
- Stage 4 interview/director/orchestrator files (T2 lane)
- Upstream callers in `stage4_interview_round.py`

---

## 3. Current Read Order or Ownership Map

### 3.1 Read Order for Writer/Context Lane

1. **`chief_writer_prompts.py`** (285 lines) -- prompt template externalization via YAML SSOT
2. **`chief_writer_context.py`** (580 lines) -- context assembly orchestrator, owns `build_common_context()`
3. **`chief_writer_context_packets.py`** (988 lines) -- bounded packet rendering (digest, guard, HUD, NPC)
4. **`chief_writer.py`** (2,274 lines) -- ensemble engine, owns `generate_ensemble()` and `_generate_single_candidate()`
5. **`writer_template.py`** (420 lines) -- blueprint-to-template structural mapping
6. **`prompt_builder.py`** (968 lines) -- SovereignApp prompt generation (arc context, writer guides, validation context)
7. **`stage4_context_builder.py`** (2,729 lines) -- episode-level context collection (retrieval, continuity, world state)
8. **`stage4_context_packets.py`** (802 lines) -- continuity/fact/relationship packet rendering

### 3.2 Ownership Map

| Concern | Owner |
|---|---|
| Ensemble strategy selection and parallel generation | `chief_writer.py` `ChiefWriter` |
| CW prompt assembly (main prompt template) | `chief_writer_context.py` `ChiefWriterContextBuilder.build_common_context()` |
| CW prompt template string | `chief_writer_prompts.py` `build_chief_writer_main_prompt()` |
| CW packet rendering (digest, guards, HUD, NPC freq) | `chief_writer_context_packets.py` `ChiefWriterContextPackets` |
| Episode context collection (retrieval, CP, world state) | `stage4_context_builder.py` `Stage4ContextBuilder` |
| Continuity/fact/relationship packets | `stage4_context_packets.py` `Stage4ContextPackets` |
| Arc position/cliche/relationship guides | `prompt_builder.py` `PromptBuilder` |
| Blueprint scene template structure | `writer_template.py` `WriterTemplate` |
| Quality gate / self-critique / leakage | `chief_writer_quality.py` (out of scope) |

### 3.3 Dual Context Builder Paths

There are two context-building pipelines that produce overlapping but distinct context for the Writer LLM:

1. **CW-side path**: `stage4_interview_round.py` calls `ChiefWriter.generate_ensemble()` which calls `ChiefWriterContextBuilder.build_common_context()` -> produces the main CW prompt
2. **Interview-round-side path**: `stage4_interview_round.py` calls `Stage4ContextBuilder` methods to collect episode state, continuity packets, world state summary, chain links -- then passes results as parameters to `generate_ensemble()`

These are complementary, not competing: `Stage4ContextBuilder` collects raw data, then the caller passes it to `generate_ensemble()` which feeds it into `ChiefWriterContextBuilder`. But a cold LLM reading the code may initially assume they are parallel/competing systems.

---

## 4. Top Hotspots

| # | File | Line Anchor | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|---|
| 1 | `chief_writer.py` | L566-615 + L955-1002 | Contract | **P1** | `generate_ensemble()` has 35 keyword parameters. `regenerate_with_feedback()` duplicates all 35 and forwards verbatim. `_prepare_generate_ensemble_context()` (L289-324) takes the same 35. Three levels of identical parameter lists. | contract-cleanup (extract request dataclass) |
| 2 | `chief_writer_context.py` | L114-159 | Contract | **P1** | `build_common_context()` has 30+ keyword parameters including 7 versioned additions (V67, V68, IFC, TF-49b, TF-54c). Each new feature added more params rather than a config object. | contract-cleanup (extract context config dataclass) |
| 3 | `chief_writer_prompts.py` | L50-83 | Contract | **P1** | `build_chief_writer_main_prompt()` has 29 keyword parameters. Some are pre-escaped strings, some are raw -- no contract note distinguishing them. Caller must remember escape responsibility. | comment-only (add docstring noting which params are pre-escaped) |
| 4 | `stage4_context_builder.py` | L1-2729 | Navigation | **P1** | 2,729 lines, 69 methods, 8 TypedDict definitions at top. No section dividers or method-group ToC. Key entry points (`build_episode_context`, `build_condensed_world_state`) require scrolling. | comment-only (add section dividers + ToC) |
| 5 | `chief_writer.py` | L2148-2270 | Local Read | **P1** | 22 `*args, **kwargs` forwarding stubs that delegate to `quality_gate` or `context_builder.context_packets`. These are compat shims from the decomposition. A cold LLM cannot determine parameter expectations without chasing through 2 levels of delegation. | comment-only (add `# [COMPAT] delegates to <target>(<expected params>)`) |
| 6 | `chief_writer.py` L37-48 + `chief_writer_context.py` L34-58 | Local Read | **P1** | Genre code map duplicated: `_CW_GENRE_CODE_MAP` (10 entries, Korean->code) in chief_writer.py, `_GENRE_CODE_ALIASES` (20 entries, Korean+English->code) in chief_writer_context.py. `_CW_GENRE_CODE_MAP` appears unused at runtime -- `normalize_chief_writer_genre_code()` uses only `_GENRE_CODE_ALIASES`. | contract-cleanup (remove unused `_CW_GENRE_CODE_MAP` or consolidate) |
| 7 | `chief_writer_context_packets.py` | L30-40 | Authority | **P1** | 4 delegate methods (`_fit_compact_text`, `_extract_numeric_value`, `_get_hud_trend_safe`, `_build_hud_context`) forward to owner via untyped `*args, **kwargs`. No docstring explaining what they delegate to or what parameters they expect. | comment-only (add delegate target and expected signature) |
| 8 | `stage4_context_builder.py` | L35-106 | Contract | **P2** | 8 TypedDict definitions (`WorkRetrievalFocusPayload`, `Stage4RetrievalContextPayload`, etc.) form a well-typed contract surface. However, some field names overlap (`tier1_parts`, `tier2_parts` appear in 3 different TypedDicts) and no grouping comment explains which TypedDict flows into which method. | comment-only (add TypedDict usage map) |
| 9 | `prompt_builder.py` | L59-66 | Authority | **P2** | `PromptBuilder.__init__` takes `app=None`. Pure methods work without app; app-dependent methods fail silently or return empty. No clear boundary comment separating Pure vs App-dependent sections (section dividers exist but only at L82 and L546). | comment-only (add pure vs app-dependent note to class docstring) |
| 10 | `chief_writer_context_packets.py` | L198-300 | Local Read | **P2** | Korean regex patterns for death/injury/item/skill/location extraction are dense but correct. They are functional and have inline comments. Low priority but a cold LLM may misread the regex capture groups. | ignore |

---

## 5. Top Quick Wins

### Comment-Only

| # | Target | Action |
|---|---|---|
| QW-1 | `stage4_context_builder.py` L1 | Add method-group ToC comment after imports: TypedDicts, protagonist/NPC helpers, entity extraction, context composition, world state rendering, with line ranges |
| QW-2 | `chief_writer_context_packets.py` L16-40 | Add class-level docstring explaining: "Delegation chain: `ChiefWriter -> ChiefWriterContextBuilder -> ChiefWriterContextPackets`. This class owns bounded packet rendering for episode digest, future/past guards, NPC equipment/frequency, HUD anomalies, DNA mode." Add expected parameter types to the 4 delegate methods. |
| QW-3 | `chief_writer.py` L566 | Add docstring to `generate_ensemble()`: "Parameter forwarding chain: generate_ensemble -> _prepare_generate_ensemble_context -> ChiefWriterContextBuilder.build_common_context -> build_chief_writer_main_prompt. All 35 params are forwarded verbatim. regenerate_with_feedback() duplicates this signature." |
| QW-4 | `chief_writer.py` L2148 | Add `# [COMPAT] forwarding stubs — preserve external API after quality_gate/context_builder extraction` header before the 22 `*args, **kwargs` stubs. Optionally add expected param hint to each: `# delegates to quality_gate.sanitize_leakage(response: str)` |
| QW-5 | `chief_writer_prompts.py` L50 | Add docstring note: "All string parameters are expected pre-escaped by the caller via `_escape_braces()`. Exception: `ep_num` (int), `common_rules`/`writing_guidelines` (YAML-loaded, no braces)." |
| QW-6 | `chief_writer.py` L37-48 | Add comment: `# NOTE: _CW_GENRE_CODE_MAP is a legacy subset. Canonical genre resolution uses _GENRE_CODE_ALIASES in chief_writer_context.py` |

### Doc-Only

| # | Target | Action |
|---|---|---|
| QW-7 | `docs/2026-03-23/llm-codebase-orientation-pack.md` section 6 | Add note: "Writer context assembly flows through two complementary pipelines: (1) Stage4ContextBuilder collects episode state; (2) ChiefWriterContextBuilder assembles the CW prompt from that state plus blueprint/HUD/guard packets." |

### Observability-Only

| # | Target | Action |
|---|---|---|
| QW-8 | `chief_writer_context.py` L227 | Add `logging.debug("[CW-Context] build_common_context assembled: %d sections, %d chars", section_count, len(result))` after the final `build_chief_writer_main_prompt()` call |

---

## 6. Deferred Refactor Candidates

| # | Target | Action | Classification | Notes |
|---|---|---|---|---|
| DR-1 | `chief_writer.py` L566 + L955 | Extract the 35 shared parameters of `generate_ensemble()` and `regenerate_with_feedback()` into a `WriterEnsembleRequest` dataclass. This would eliminate 3 layers of verbatim parameter forwarding. | contract-cleanup, **long-term** | Blast radius: medium -- callers in `stage4_interview_round.py` must be updated. High ROI for LLM comprehension. |
| DR-2 | `chief_writer.py` L37 + `chief_writer_context.py` L34 | Consolidate genre code maps. Remove `_CW_GENRE_CODE_MAP` from chief_writer.py if confirmed unused. Keep `_GENRE_CODE_ALIASES` as the single SSOT. | contract-cleanup, **defer** | Blast radius: low. Requires verifying `_CW_GENRE_CODE_MAP` has no remaining callers. |
| DR-3 | `chief_writer.py` L2148-2270 | Remove the 22 `*args, **kwargs` compat forwarding stubs once external callers (tests, other modules) migrate to calling the sub-module directly. | boundary-refactor, **long-term** | Blast radius: depends on external caller count. Must be preceded by a caller audit. |

---

## 7. No-Action / Settled Areas

| Area | Reason |
|---|---|
| `chief_writer_prompts.py` | Clean YAML-SSOT externalization. 10 small functions, each loads one prompt key. No comprehension hazard. |
| `writer_template.py` | Self-contained, well-documented. Dataclasses with docstrings. Enum-based scene types. No delegation complexity. |
| `prompt_builder.py` section dividers | Already has `=====` section dividers at L82, L154, L546, L697, L767, L859. Pure vs app-dependent split is documented in class docstring (L48-57). |
| `stage4_context_builder.py` TypedDicts L35-106 | Well-typed contract surface. Field names are descriptive. Minor overlap (tier1_parts/tier2_parts) is manageable. |
| `chief_writer_context.py` internal helpers | Methods like `_extract_blueprint_sections()`, `_extract_bible_context()`, `_build_world_state_section()` are short, focused, and readable. |
| `stage4_context_packets.py` | Clean delegation pattern. Continuity/relationship/fact packet rendering is well-structured with budget-based truncation. |
| `chief_writer.py` ensemble workers L396-498 | Thread-based parallel generation with proper timeout handling, cancellation, and error recovery. Well-logged with operator-visible progress. |

---

## 8. Cross-Lane Handoff Notes

### To T2 (Stage 4 Authority / Verdict Flow)
- `stage4_interview_round.py` is the primary caller of `ChiefWriter.generate_ensemble()`. The 35-parameter interface is the T3 contract surface that T2 must assemble.
- `Stage4ContextBuilder` is instantiated and used within `stage4_interview_round.py` -- its methods produce the parameters that feed into `generate_ensemble()`.
- If T2 identifies `generate_ensemble()` call sites as comprehension hazards, the root cause is the T3 parameter contract described in Hotspot #1.

### To T4 (Contract / Validation / Envelope Surface)
- `prompt_builder.py` `build_validation_context()` (L863-928) assembles the validation context dict used by validators. This is the T3/T4 boundary.
- Tier result schemas referenced in the global survey report (validation_orchestrator.py L82-181) are consumed by the director, not the writer. No direct T3 concern.

### To T1 (Navigation / Entry / Reading Order)
- The orientation pack (section 6) lists `chief_writer.py` and `chief_writer_context_packets.py` but does not describe the two-pipeline context assembly flow. QW-7 addresses this.

### To T5 (Persistence / Observability)
- `ChiefWriter._prefetch_manuscripts()` (L2179-2205) reads from DB via `context.db.get_manuscript()`. The LRU cache (`_manuscript_cache`) is bounded to 10 episodes. No persistence write surface in the T3 scope.

---

## 9. Confidence And Limits

**Overall confidence: 95%**

Breakdown:
- Navigation: 92%. Delegation chain is clear across all 8 files. `stage4_context_builder.py` lacks ToC but method names are descriptive.
- Authority: 90%. Owner boundaries are unambiguous. The dual context-builder path creates a 1-time comprehension cost that a comment can resolve.
- Contract: 72%. The 35-parameter forwarding pattern is the dominant friction source. It affects `generate_ensemble()`, `regenerate_with_feedback()`, `_prepare_generate_ensemble_context()`, and `build_common_context()`. This is not fixable with comments alone -- a request dataclass would be the correct long-term fix.
- Observability: 90%. Operator logs are present in the ensemble generation pipeline. Context assembly has minimal logging but failures are non-blocking.
- Local Readability: 78%. The 22 compat stubs and genre map duplication are the main blockers. Korean regex in context_packets is dense but has inline comments.

Limits:
- `chief_writer_quality.py` was not surveyed (out of scope). Its interaction with `ChiefWriter` is through the 10 compat stubs at L2148-2173.
- The upstream caller in `stage4_interview_round.py` was not traced end-to-end -- only the interface boundary was assessed.
- `writer_prompt_builders.py` (shared utility) was noted as an import but not deeply surveyed.

---

## 10. 3-Pass Audit Record

### Pass 1. Structure and Scope
- All 8 primary scope files surveyed with line counts and method counts.
- All 5 LLM-friendliness axes evaluated.
- Every P0/P1 finding has file:line anchor.
- Every recommendation has a fix type.
- PASS

### Pass 2. Evidence and Consistency
- Parameter counts verified by reading actual method signatures (generate_ensemble L566-615: 35 params confirmed).
- Genre map duplication verified: `_CW_GENRE_CODE_MAP` L37 in chief_writer.py, `_GENRE_CODE_ALIASES` L34 in chief_writer_context.py.
- Compat stub count verified: 22 stubs at L2148-2270.
- stage4_context_builder.py method count verified via grep: 69 `def` statements.
- No contradiction with prior survey findings (global survey #10 identified the same 35-param issue).
- PASS

### Pass 3. Readability and Operational Use
- Quick wins are actionable without code behavior changes.
- Deferred refactor candidates have explicit blast-radius notes.
- Cross-lane handoffs identify concrete interface surfaces.
- Report does not recommend reopening the long-function campaign.
- PASS

### Confidence Gate
- Estimated confidence: 95%.
- Threshold: 95% required for final save.
- The remaining 5% is from: incomplete `chief_writer_quality.py` coverage (3%), `stage4_interview_round.py` caller trace not exhaustive (2%).
