# TF-LLM-Readability Audit — Pass 3: Completeness & Blind Spots

**Date**: 2026-03-20
**Auditor**: Adversarial Pass 3 (Opus)
**Target**: `docs/2026-03-20/TF-llm-readability-audit.md`
**Verdict**: **6 blind spots found, 2 HIGH severity.** The audit's 5.5/10 score is **over-generous** — corrected estimate is **4.5-5.0/10** when Korean-language opacity and indirection depth are factored in.

---

## Executive Summary

The original audit measured 7 quantitative axes and concluded LLM readability = 5.5/10. The measurement methodology is sound for what it measures. However, the audit implicitly assumes **English-centric LLM comprehension** and treats all comments, docstrings, and log messages as equally useful regardless of language. It also omits several structural complexity dimensions that directly impact LLM reasoning.

The 6 blind spots, in order of impact:

| # | Blind Spot | Severity | Score Impact |
|---|-----------|----------|-------------|
| BS-1 | Korean-dominant documentation | **HIGH** | Axis 5 (Naming/Docs): 7.0 -> **5.0-6.0** |
| BS-2 | Indirection depth / call fan-out | **HIGH** | New axis or compounds Axis 6 |
| BS-3 | Magic string implicit schemas | MEDIUM | Compounds Axis 3 (dict opacity) |
| BS-4 | Lazy imports obscuring dependencies | MEDIUM | Compounds Axis 7 (dynamic dispatch) |
| BS-5 | Log message language barrier | LOW | Minor compound with Axis 5 |
| BS-6 | Genre guard pattern regularity | LOW (positive) | Partially offsets Axis 6 weakness |

---

## BS-1: Korean-Dominant Documentation (HIGH)

### Finding

The audit's Axis 5 scored 7.0/10 for naming and documentation. It noted "한글 혼용 = 0, EXCELLENT" for variable names and measured docstring coverage at 68.1%. But it **never assessed the language of the documentation content itself**.

**Measured evidence:**

| Metric | Korean | English | Korean % |
|--------|--------|---------|----------|
| Inline comments (explanatory) | 5,151 | 839 | **86.0%** |
| Function/class docstrings | 2,659 | 243 | **91.6%** |
| Log messages | 1,337 | 581 | **69.7%** |
| Prompt template files with Korean | 57 / 66 | — | **86.4%** |
| YAML config values with Korean | 34 / 34 genre+prompt configs | — | ~100% |
| YAML config keys in Korean | 111 | 919 | 10.8% |

The codebase is **overwhelmingly Korean-documented**. 91.6% of docstrings and 86% of explanatory comments are in Korean.

### Domain terminology compounds the problem

The docstrings and comments contain **specialized Korean web-novel and wuxia terminology** that most LLMs have limited training data for:

| Term | Count in docstrings | LLM familiarity |
|------|-------------------|-----------------|
| 원고 (manuscript) | 271 | Moderate |
| 에피소드 (episode) | 201 | High (loanword) |
| 주인공 (protagonist) | 65 | Moderate |
| 블루프린트 (blueprint) | 35 | High (loanword) |
| 텐션 (tension) | 32 | High (loanword) |
| 복선 (foreshadowing) | 31 | Low |
| 무협 (wuxia/martial arts fiction) | 27 | Low-Moderate |
| 강호 (jianghu/martial world) | 16 | Low |
| 내공 (inner energy/qi) | 11 | Low |
| 회귀 (regression/time-travel trope) | 21 | Low (domain-specific meaning) |

Terms like 복선, 강호, 내공, and the domain-specific sense of 회귀 are unlikely to be correctly interpreted by most LLMs even if they understand general Korean.

### Impact on audit score

The audit said "이름으로 의도 추론은 대체로 가능" (intent inference from names is mostly possible). This is true — variable names are English and descriptive. But the audit conflated **naming quality** (English, good) with **documentation quality** (Korean, opaque to many LLMs). For an LLM that processes Korean poorly:

- 68.1% docstring coverage effectively drops to ~5.7% (English-only docstrings)
- 8.1% comment density effectively drops to ~1.1% (English-only comments)
- Prompt templates become partially opaque

**Corrected Axis 5 score**: 5.0-6.0 depending on LLM's Korean capability (Sonnet/Opus handle Korean well; smaller or non-multilingual models fail entirely).

### Does this change the audit's conclusions?

**Yes, partially.** The audit's overall narrative ("file-level readability is good") holds for naming, but the documentation safety net that the audit assumed exists (68% docstrings, 8% comments) is **language-gated**. For a Korean-capable LLM like Claude, the impact is moderate. For GPT-4 or code-specialized models with weaker Korean support, the impact is severe.

---

## BS-2: Indirection Depth / Call Fan-Out (HIGH)

### Finding

The audit measured **self.attr count per function** (Axis 6) and **dynamic dispatch** (Axis 7), but did not measure **how many distinct method calls a single function fans out to** or **how deep the call chain goes**. These are different: self.attr tells you about state coupling, but call fan-out tells you about **control flow comprehension burden**.

**Measured evidence for Stage4InterviewRound.run():**

| Metric | Value |
|--------|-------|
| Direct self.method() calls from run() | **32 unique methods** |
| Depth-2 call targets (methods called by those 32) | **59 unique methods** |
| Total methods in the call tree (depth 1+2) | **~75 unique methods** |

A single invocation of `run()` can reach 75+ internal methods within 2 hops. An LLM trying to understand "what happens when run() is called" must trace through **32 direct callees**, each of which calls 0-12 more methods.

**Comparison across orchestrators:**

| Method | Direct calls | Lines |
|--------|-------------|-------|
| Stage4InterviewRound.run() | 32 | 1,149 |
| SovereignApp._run_main_process() | 17 | 119 |
| SovereignApp._init_v50_modules() | 16 | 330 |
| Stage4InterviewRound._handle_reject() | 13 | 289 |
| Stage4Orchestrator._run_interview_loop() | 10 | 296 |

**Lazy imports compound this**: `stage4_interview_round.py` has **48 lazy imports** (the highest in the codebase). An LLM cannot even determine the full dependency set without reading every function body.

`main_a.py` has **75 lazy imports** — the single worst case. Its top-level imports show only 16 modules, but 75 more modules are hidden inside function bodies.

### Impact

This is a **separate readability dimension** that the audit did not capture. The audit's Axis 6 (self.attr) measures state coupling; this measures control-flow coupling. Stage4InterviewRound scores poorly on both, but the fan-out problem extends to files the audit rated as "OK" — e.g., `stage4_orchestrator.py` has only moderate self.attr usage but 20 lazy imports creating hidden dependencies.

**Recommended addition**: A new axis "Call Fan-Out / Dependency Transparency" scoring ~3.5/10 for the codebase, which would further depress the overall score.

### Does this change the audit's conclusions?

**Yes.** The audit identified Stage4InterviewRound.run as the worst case via variable tracking and dict opacity, but the indirection problem independently confirms that this function (and the Stage4 subsystem generally) is LLM-unreasonable. More importantly, it reveals that **even the orchestrator files the audit didn't flag** (stage4_orchestrator, main_a.py) have hidden complexity from lazy imports.

---

## BS-3: Magic String Implicit Schemas (MEDIUM)

### Finding

The audit correctly identified 12,734 blind dict accesses and noted TypedDict coverage <1%. But it didn't measure a subtler problem: **how many implicit schemas exist** (unique dict key strings) and **how widely they're coupled across files**.

**Measured evidence:**

| Metric | Value |
|--------|-------|
| Unique dict key strings | **2,122** |
| Total usages | **11,783** |
| Keys used in 5+ files | **237** |
| Keys used in 10+ files | **97** |
| Keys used in 20+ files | **36** |
| Top key: "name" | **59 files, 281 uses** |

The top 20 dict keys (used in 25-59 files each) constitute an **undocumented implicit schema** that spans the entire codebase. None of the top 20 most-used keys (`name`, `arc_no`, `ep_num`, `status`, `reason`, `score`, `state_constraints`, `tactical_doc`, `severity`, `description`, etc.) are defined as named constants — they exist only as bare string literals.

**17 of the top 20 dict keys are NOT defined as UPPER_CASE constants anywhere.** Only `description`, `location`, and `decision` happen to appear as constant values (and likely for unrelated purposes).

### Impact

This compounds the audit's Axis 3 finding but adds a new dimension: the problem is not just "LLM can't track dict keys in one function" — it's that **the same key string is an implicit contract across 30-60 files**, and there is no single source of truth for what keys a dict should contain. If an LLM reads `data.get("tactical_doc")` in one file, it has no way to find the 40 other files that also expect this key without a full-codebase search.

**The audit's Axis 3 score of 2.0/10 is already the lowest.** This finding doesn't lower it further but confirms that the L-2 recommendation (TypedDict) should also include **extracting the top 36 keys into named constants** as a prerequisite.

### Does this change the audit's conclusions?

**No, but strengthens them.** The L-2 recommendation is even more urgent than stated.

---

## BS-4: Lazy Imports Obscuring Dependencies (MEDIUM)

### Finding

The audit measured `getattr` (841) and `hasattr` (354) for dynamic dispatch but did not count **in-function imports** which similarly prevent static dependency analysis.

**Measured evidence:**

| Metric | Value |
|--------|-------|
| Total lazy imports | **318** |
| Files with lazy imports | **85 / ~295** (28.8%) |
| Worst: main_a.py | **75 lazy imports** (16 top-level) |
| Worst module: stage4_interview_round.py | **48 lazy imports** (7 top-level) |
| stage4_orchestrator.py | **25 lazy imports** |
| stage2_orchestrator.py | **11 lazy imports** |

An LLM reading `stage4_interview_round.py` sees 7 top-level imports, but 48 more modules are imported inside function bodies. This means:

1. The LLM cannot determine the full dependency graph from the top of the file
2. Each function body must be read to discover what modules it uses
3. Circular dependency avoidance (the likely reason for lazy imports) is invisible to the reader

### Impact

318 lazy imports across 85 files is a moderate structural issue. It compounds Axis 7 (dynamic dispatch) — `getattr` hides attribute resolution, and lazy imports hide module resolution. Together they create **1,513 points of static-analysis opacity** (1,195 dynamic dispatch + 318 lazy imports).

**Corrected Axis 7 (Dynamic Dispatch)**: The audit scored 4.5/10 based on 1,195 dynamic calls. Adding 318 lazy imports brings the opacity surface to 1,513, suggesting a corrected score of ~4.0/10.

### Does this change the audit's conclusions?

**Marginally.** The audit already identified dynamic dispatch as a weakness. Lazy imports are a contributing factor that specifically impacts the **same worst-case files** (stage4_interview_round, main_a.py).

---

## BS-5: Log Messages as Korean-Language Documentation (LOW)

### Finding

The codebase has **1,918 log calls**, of which **69.7% contain Korean text**. Log messages often serve as implicit documentation of intent and error conditions. For an LLM reading a `try/except` block, the log message is frequently the **only explanation** of what went wrong and why.

**Quality breakdown (all files):**

| Category | Count | % |
|----------|-------|---|
| Informative (contextual, >60 chars) | 893 | 46.6% |
| Moderate | 789 | 41.1% |
| Terse (<40 chars) | 236 | 12.3% |

46.6% of log messages are informative (good), but since 69.7% are Korean, the effective informative rate for a non-Korean LLM drops to ~14%.

### Impact

Low independent impact because log messages are supplementary, not primary documentation. However, in the **장함수 (long function)** context identified by the audit (Axis 4), log messages are often the only mid-function documentation. If those are Korean, the LLM loses even this weak signal.

### Does this change the audit's conclusions?

**No.** This is a minor compounding factor for BS-1.

---

## BS-6: Genre Guard Pattern Regularity (LOW — Positive Finding)

### Finding

The audit measured God Objects as the worst case for Axis 6 (function self-sufficiency) but did not assess **pattern regularity** — whether similar components follow predictable structures that LLMs can generalize from.

**Measured evidence (10 genre-specific guards):**

| Metric | Value |
|--------|-------|
| Common methods across all 10 guards | **7** (`__init__`, `get_genre_name`, `get_hierarchy_rules`, `get_impossible_actions`, `get_justification_patterns`, `get_v20_purism_prompt`, `run_deep_validation`) |
| Lines range | 349 (FantasyGuard) - 853 (HunterGuard) |
| Extra methods per guard | 3 (Fantasy) - 19 (Hunter) |
| 8/10 guards share `_should_check_english/numbers` + 7 more methods | ~14 common |

8 out of 10 genre guards (excluding Fantasy and Wuxia which have slightly different structures) share a **near-identical 14-method skeleton**: the 7 universal methods plus `_should_check_english`, `_should_check_numbers`, `get_technique_effect_rules`, `get_authority_hierarchy`, `get_delegation_patterns`, `get_hostile_action_types`, `get_resolution_patterns`.

### Impact

This is a **positive finding** the audit missed. Once an LLM understands one genre guard, it can accurately predict the structure of 7-8 others. The `BaseGuard` ABC defines 24 methods that all guards must implement, creating strong structural predictability.

**Nesting depth is another story**: The audit also didn't measure nesting depth. 35 files (12%) have max nesting depth >= 7, with `main_a.py` reaching depth **14**. This compounds variable tracking difficulty but wasn't captured by any of the 7 axes.

| Nesting depth | File count |
|--------------|-----------|
| 1-2 | 59 |
| 3-4 | 80 |
| 5-6 | 75 |
| **7+** | **35** |

### Does this change the audit's conclusions?

**Slightly positive offset for genre guards, slightly negative for nesting.** Net effect: neutral.

---

## Corrected Overall Assessment

### Original vs Corrected Scores

| Axis | Original | Corrected | Reason |
|------|----------|-----------|--------|
| Context Loading | 8.5 | **8.5** | No change |
| Type Annotations | 8.0 | **8.0** | No change |
| Dict Opacity | 2.0 | **2.0** | BS-3 confirms but doesn't lower further |
| Variable Tracking | 3.0 | **3.0** | No change |
| Naming/Docs | 7.0 | **5.0-6.0** | BS-1: 91.6% of docstrings in Korean |
| Function Self-Sufficiency | 5.5 | **5.0** | BS-2: call fan-out not captured |
| Dynamic Dispatch | 4.5 | **4.0** | BS-4: +318 lazy imports |
| *NEW: Call Fan-Out* | — | **3.5** | BS-2: 32 callees from run(), 75 at depth 2 |

### Corrected Overall Score

**For a Korean-fluent LLM (Claude Opus/Sonnet):**
```
(8.5 + 8.0 + 2.0 + 3.0 + 6.0 + 5.0 + 4.0 + 3.5) / 8 = 5.0
```

**For a Korean-limited LLM (code-specialized models):**
```
(8.5 + 8.0 + 2.0 + 3.0 + 5.0 + 5.0 + 4.0 + 3.5) / 8 = 4.9
```

Original: **5.5/10** -> Corrected: **4.9-5.0/10**

The directional conclusion is unchanged (the codebase is below average for LLM readability), but the gap is wider than the original audit suggested. The audit was slightly over-generous because it treated Korean documentation as fully equivalent to English documentation for LLM comprehension.

---

## Recommendations Added by Pass 3

### L-8 (HIGH): Extract top 36 cross-file dict keys as named constants

The 36 dict keys used in 20+ files (`name`, `arc_no`, `ep_num`, `status`, `reason`, `score`, etc.) should be defined in a single `modules/core/schema_keys.py` or similar. This enables both LLM comprehension and refactoring safety. This should precede L-2 (TypedDict), as TypedDict definitions will reference these keys.

### L-9 (MEDIUM): Audit lazy imports for consolidation

318 lazy imports across 85 files, with 48 in a single file. Many of these are `from modules.core.constants import X` or `import re` patterns that could safely move to top-level without circular import issues. A targeted sweep could reduce lazy imports from 318 to ~100 (circular-avoidance only).

### L-10 (MEDIUM): Add English-language summary comments in long functions

Given BS-1 (Korean documentation), adding brief English `# --- Phase N: purpose ---` section markers in the 23 functions with 500+ line variables would provide LLM-accessible documentation without replacing existing Korean comments. Cost: ~50 lines of comments for maximum readability ROI.

---

*This is an adversarial completeness audit. No code was modified. Measurements are AST-based and grep-based, applied to the production codebase at HEAD.*
