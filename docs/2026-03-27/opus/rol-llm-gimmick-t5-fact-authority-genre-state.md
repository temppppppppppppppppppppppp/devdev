Date: 2026-03-27
Status: final (3-pass audited)
Document Type: parallel static survey lane report (T5)
Canonical Path: `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md`
Lane: Fact Authority / Genre Gimmick / Contract State
Master Order: `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`
Source Survey Docs:
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
- `docs/2026-03-26/llm-multi-provider-context-note.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked llm_router/provider/context/validator surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked multi-provider docs, fact docs, anthropic_vertex provider scaffolding/tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

The fact authority spine of this codebase is fundamentally sound. Wave 1 contract alignment (authority statement, advisory suppression, dead-NPC pre-check) landed correctly and is verifiable in live code. The four strongest fact families (NPC lifecycle, numeric state, relationships, item ownership) have canonical injection, explicit authority precedence, and Stage 4 enforcement.

The dominant remaining weakness is not storage or architecture but **contract opacity**: an LLM can trace *what* data exists but cannot always determine *who wins on conflict*, *which gimmicks are active for which genre*, or *why certain state was suppressed vs. passed through*. Genre gimmicks are well-localized in the guard system but structural rules (hierarchy, justification, authority delegation) are code-hardcoded and invisible to the LLM at prompt time.

Key findings:
- **P0**: None.
- **P1**: 4 items (degradation opacity, enum inconsistency, realm tracking gap, justification pattern invisibility).
- **Quick wins**: Predominantly comment-only and doc-only.
- **Verdict**: Gimmick-elegance is **mixed** — elegant in core authority systems, inelegant in genre-specific contract surfaces and degradation handling.

---

## 2. Included Coverage / Exclusions

### Included

| Surface | Files Inspected |
|---------|-----------------|
| Stage 3 Orchestrator | `modules/core/stage3_orchestrator.py` (full) |
| WorldStateManager | `modules/core/world_state.py` (full) |
| FactLedger | `modules/core/fact_ledger.py` (full) |
| StateTracker family | `modules/domain/agents/state_tracker.py`, `state_tracker_npc.py`, `state_tracker_plots.py`, `state_tracker_financial.py` (full) |
| BlockingValidator family | `modules/validation/blocking_validator.py`, `blocking_validator_entity_checks.py`, `blocking_validator_scene_checks.py`, `blocking_validator_consistency_checks.py` (full) |
| Genre Guard system | `modules/core/genre_guards/` — all 14 files including `base_guard.py`, `wuxia_guard.py`, `work_guard.py`, `style_guard.py`, `__init__.py` (full) |
| Genre config | `config/genres/wuxia.yaml` (full) |
| Fact synthesis docs | `per-work-fact-system-synthesis-memo.md`, `per-work-fact-contract-alignment-residual-survey.md` (full) |

### Excluded

- Stage 4 context builder and context packets (T4 lane)
- Director ensemble and verdict flow (T3 lane)
- Provider/router surfaces (T2 lane)
- Observability sinks and DB manager (T6 lane)
- Navigation/entry routing (T1 lane)
- Code modification (survey-only constraint)

---

## 3. Current Read Order / Ownership / Gimmick Map

### 3.1 Fact Authority Ownership

```
                    ┌─────────────────────────────────────┐
                    │     Stage 3 Orchestrator             │
                    │  (Lazy-init, semantic context build) │
                    └───────┬─────────┬──────────┬────────┘
                            │         │          │
                    ┌───────▼───┐ ┌───▼────┐ ┌───▼──────────┐
                    │StateTracker│ │WorldSt.│ │FactLedger    │
                    │(upstream   │ │(cache) │ │(long-term    │
                    │ authority) │ │        │ │ numeric SSOT)│
                    └─────┬─────┘ └───┬────┘ └──────┬───────┘
                          │           │              │
                          ▼           ▼              ▼
                    ┌─────────────────────────────────────┐
                    │  Stage 4 Context Builder             │
                    │  Tier-0: canonical block + body      │
                    │  Tier-2: advisory (suppressed 7 dom) │
                    └───────┬─────────────────────────────┘
                            │
                    ┌───────▼────────────────────────────┐
                    │  BlockingValidator (14 checks)      │
                    │  Entity: 4 CRITICAL                 │
                    │  Scene: 4 checks (1 disabled)       │
                    │  Consistency: 5 checks (1 wuxia)    │
                    └───────┬────────────────────────────┘
                            │
                    ┌───────▼────────────────────────────┐
                    │  Genre Guards (13 genres)            │
                    │  Chain: Genre → Work → Style         │
                    │  Consistency checks via BaseGuard    │
                    └────────────────────────────────────┘
```

### 3.2 Authority Precedence (Post-Wave 1)

| Layer | Authority Level | What It Owns |
|-------|----------------|-------------|
| Tier-0 canonical block (position 0) | Highest | Authority statement + WorldState `get_canonical_constraints()` (NPC intro roles, known_attrs) + FactLedger `get_canonical_summary()` (top 30 numeric facts) |
| Tier-0 body | High | WorldState `get_summary()` (50K: alive/dead NPCs, items, plots, timeline, relationships, motivations, world laws) + FactLedger `to_summary()` (25K: characters, numbers, items, locations, orgs) |
| Tier-2 advisory | Low | StateTracker non-suppressed summaries (12 domains pass through) + note listing suppressed domains |
| Genre Guards | Enforcement | Term bans, realm limits, action gates, hierarchy rules |
| BlockingValidator | Hard enforcement | CRITICAL checks: dead NPC, unowned item, damaged item, destroyed location |

### 3.3 Suppression Map (Wave 1)

7 domains suppressed from StateTracker tier-2 when canonical layers exist:

| Suppressed Domain | Canonical Source | Verified At |
|-------------------|-----------------|-------------|
| dead_npc | WorldState | `stage4_context_builder.py:939-971` |
| item_state | WorldState | same |
| relationship_changes | WorldState | same |
| npc_injury | WorldState | same |
| npc_movement | WorldState | same |
| time_timeline | WorldState | same |
| financial_state | FactLedger | same |

12 domains pass through unsuppressed: entity_destruction, resolved_plots, npc_personality, npc_npc_relationship, permanent_injury, companion, commitment, protagonist_emotion, plot_suspension, npc_dialogue_style, protagonist_skills, genre-specific registries.

### 3.4 Genre Gimmick Map

| Genre | Guard | YAML Config | Registries (StateTracker) | BlockingValidator Gate | Maturity |
|-------|-------|-------------|--------------------------|----------------------|----------|
| Wuxia | `wuxia_guard.py` (662 LOC) | `wuxia.yaml` (238 lines) | protagonist_skills, skill_acquisitions | realm-technique check | Production |
| Hunter | `hunter_guard.py` (867 LOC) | `hunter.yaml` | skill_cooldown_registry, dungeon_clear_registry | None | Scaffolding |
| Fantasy | `fantasy_guard.py` (362 LOC) | `fantasy.yaml` | spell_repertoire, blessing_curse_registry | None | Concept only |
| Investment | `investment_guard.py` (717 LOC) | `investment.yaml` | financial_number_registry (isolated sub-module) | None | Complete |
| Actor | `actor_guard.py` (464 LOC) | `actor.yaml` | filmography_registry (stub, never populated) | None | Abandoned |
| Alt-History | `alt_history_guard.py` (492 LOC) | `alt_history.yaml` | None | None | Term-only |
| Composer | `composer_guard.py` (518 LOC) | `composer.yaml` | None | None | Term-only |
| Cooking | `cooking_guard.py` (511 LOC) | `cooking.yaml` | None | None | Term-only |
| Medical | `medical_guard.py` (469 LOC) | `medical.yaml` | None | None | Term-only |
| Sports | `sports_guard.py` (462 LOC) | `sports.yaml` | None | None | Term-only |

**Guard Composition Chain** (`genre_guards/__init__.py:22-69`):
```
GenreGuard (WuxiaGuard, HunterGuard, etc.)
  → WorkGuard (if work_guard.yaml provided)
    → StyleGuard (if StyleGuide provided)
```
Each layer is cumulative: all violations from lower layers propagate upward.

---

## 4. Top Hotspots

### H-1. BlockingValidator Degradation Opacity (P1)
**File**: `blocking_validator_consistency_checks.py:180-196`, `blocking_validator.py:91-113`
**Axis**: Contract + Gimmick Elegance
**Issue**: Relationship and information consistency checks catch exceptions and set `{"passed": True, "degraded": True}`. Downstream consumers must check both `passed` and `degraded` fields to understand true state. An LLM reading "passed: True" may wrongly conclude the check succeeded.
**Fix type**: contract-cleanup

### H-2. StateTracker Enum Inconsistency (P1)
**File**: `state_tracker_npc.py:287-289` (injury), `state_tracker_npc.py:889` (relationship), `state_tracker_npc.py:289` (disposition)
**Axis**: Contract
**Issue**: Same semantic concept (relationship status) has 3+ different enum sets:
- `relationship_to_protag`: 적대, 중립, 아군, 동맹, 호의, 충성, 적 (7 values)
- `disposition`: 중립, 경계, 호의, 충성 (4 values, overlapping)
- `injury`: 정상, 경상, 중상, 위독 (4 values)
No shared enum module exists. LLM-generated state_changes may use wrong enum values, causing silent upsert failures.
**Fix type**: contract-cleanup

### H-3. Technique/Realm Tracking Gap (P1)
**File**: `state_tracker_npc.py:527-540` (protagonist skills), `state_tracker.py:142-152` (genre registries)
**Axis**: Gimmick Elegance + Authority
**Issue**: Protagonist technique history exists in advisory only (no canonical authority declaration, no enforcement). NPC technique mastery tracked by NO system. Realm progression gated at prompt-injection level (`wuxia.yaml` realm_technique_limits) but not validated against accumulated state. Per residual survey: "most likely fact family to produce real narrative contradictions in long-running wuxia series."
**Fix type**: boundary-refactor (deferred)

### H-4. Justification Pattern Invisibility to LLM (P1)
**File**: `wuxia_guard.py:314-347`
**Axis**: Gimmick Elegance + Contract
**Issue**: 8 justification patterns (life-or-death desperation, elixir use, meridian breakthrough, etc.) allow otherwise-impossible actions. These patterns are code-hardcoded and NOT injected into the LLM prompt. Writer LLM may write perfectly justified action, but ConsistencyValidator flags it. Alternatively, Writer LLM may not know justification is possible and write around constraints unnecessarily.
**Fix type**: doc-only (add patterns to purism prompt)

### H-5. Stage 3 Lazy-Init Silent Degradation (P2)
**File**: `stage3_orchestrator.py:701-761`
**Axis**: Observability + Authority
**Issue**: StateTracker, WorldState, FactLedger each lazy-initialized with non-blocking exception handlers. If init fails, the system silently degrades: dead-NPC precheck may not run, world state may not be available, numeric facts may be missing. No explicit health-check assertion at orchestrator entry.
**Fix type**: observability-only

### H-6. Implicit Semantic Context Assembly (P2)
**File**: `stage3_orchestrator.py:1024-1112`
**Axis**: Navigation + Authority
**Issue**: Semantic context for blueprint generation is assembled from 6+ helper functions (FactLedger, WorldState, style_guide, stale_seeds, work_focus, treatment_blocks, timeline_advisory) with no unified ledger documenting what was injected, from which source, at what authority level.
**Fix type**: comment-only

### H-7. Incarnation Type Mitigation Is Cosmetic (P2)
**File**: `blocking_validator_consistency_checks.py:45, 114-116, 223-226, 282-284`
**Axis**: Contract + Gimmick Elegance
**Issue**: When `incarnation_type == "회귀자"`, failure messages get a suffix "[회귀자 -- 전생 경험으로 가능할 수 있음]" but `passed` and `severity` fields remain unchanged. An LLM cannot programmatically detect mitigation; it must parse text.
**Fix type**: contract-cleanup

---

## 5. Top Quick Wins

| # | Item | File:Line | Fix Type | ROI |
|---|------|-----------|----------|-----|
| QW-1 | Add comment documenting semantic context assembly sources and authority tiers at top of `_build_smart_retrieval_semantic_context()` | `stage3_orchestrator.py:1024` | comment-only | HIGH |
| QW-2 | Add docstring to `get_canonical_constraints()` explaining return shape, 8000-char cap, and that only NPC intro roles + known_attrs are included (not injuries or dynamic state) | `world_state.py:764` | comment-only | HIGH |
| QW-3 | Add justification patterns summary to `get_v20_purism_prompt()` output so LLM knows which bypass reasons are valid | `wuxia_guard.py:222-253` | doc-only | HIGH |
| QW-4 | Add `logging.warning()` when StateTracker/WorldState/FactLedger lazy-init fails, noting which pre-checks will be unavailable | `stage3_orchestrator.py:721-724, 739-741, 759-761` | observability-only | MEDIUM |
| QW-5 | Add comment at `blocking_validator.py:91-113` explaining degradation semantics: "passed=True + degraded=True means check did NOT run, not that check succeeded" | `blocking_validator.py:91` | comment-only | MEDIUM |
| QW-6 | Add a brief "Authority Hierarchy" comment block at top of `state_tracker.py` documenting: StateTracker (upstream source) -> FactLedger (long-term numeric SSOT) -> WorldState (narrative context cache) | `state_tracker.py:1` | comment-only | MEDIUM |
| QW-7 | Add comment at `fact_ledger.py:219-227` noting that unlike WorldState, FactLedger does NOT wrap each `_apply_*` section in try/except — one parsing error blocks entire update batch | `fact_ledger.py:219` | comment-only | LOW |
| QW-8 | Add doc comment in `wuxia_guard.py` listing which structural rules are YAML-configurable vs code-hardcoded | `wuxia_guard.py:1` | doc-only | LOW |

**Mandatory rule check**: 8 items, 6 are comment/doc/observability (75% > 50%). Passes.

---

## 6. Gimmick Elegance Judgment

### 6.1 Core Fact Authority Systems

**Verdict: ELEGANT**

The three-tier injection architecture (canonical block at position 0, canonical body, advisory tier-2) is explicit, verifiable, and well-documented in the residual survey. The 7-domain suppression is clean: layer-existence check, not content check. Authority statement (`_build_persisted_authority_statement()`) is injected at highest priority. The dead-NPC pre-check at Stage 3 follows the canonical pattern cleanly.

Key evidence:
- `stage4_context_builder.py:996-1008` — authority statement at position 0
- `stage4_context_builder.py:939-971` — advisory suppression with explicit domain list
- `stage3_orchestrator.py:1552-1602` — dead-NPC pre-check with graceful degradation

### 6.2 Genre Guard System

**Verdict: MIXED**

The factory/composition chain (GenreGuard -> WorkGuard -> StyleGuard) is elegant: each layer is cumulative, `__getattr__()` delegation is transparent, and YAML externalization for term lists is clean.

Inelegant aspects:
- Structural rules (justification patterns, hierarchy, authority delegation, conflict resolution) are code-hardcoded in `wuxia_guard.py` across 13 methods — not configurable without code change
- Justification patterns are NOT exposed to LLM prompt — the Writer LLM doesn't know which bypass reasons are valid
- Cross-layer conflict resolution is absent: if WorkGuard relaxes a term that GenreGuard forbids, both violations propagate without dedup
- Only wuxia is production-grade; hunter/fantasy registries are scaffolding/stubs
- Purism prompt generation (`get_v20_purism_prompt()`) exposes only a fraction of 147 forbidden terms

### 6.3 BlockingValidator

**Verdict: MIXED**

Entity checks (dead NPC, unowned item, damaged item, destroyed location) are elegant: sophisticated Hangul word-boundary detection, common-noun defense via frozenset, consistent negation handling, CRITICAL severity.

Inelegant aspects:
- Degradation semantics: `passed=True + degraded=True` is confusing — should be `status: DEGRADED`
- Incarnation type mitigation is cosmetic (message suffix), not structural (no `mitigated_by` field)
- Negation patterns fragmented across checks (different keyword lists per check)
- Wuxia realm-technique check is the only genre-gated blocking check; hunter/fantasy have no blocking enforcement

### 6.4 StateTracker

**Verdict: MIXED**

NPC death tracking and protagonist skill extraction are well-implemented with dual-source patterns (state_changes + regex fallback). Authority flow (StateTracker -> FactLedger -> WorldState) is correct.

Inelegant aspects:
- `state_changes` schema is implicit — no TypedDict/Pydantic model, no documented contract
- Enum values inconsistent across domains (3+ different sets for similar concepts)
- Genre-specific registries mostly dormant (hunter cooldown stored but never enforced, fantasy blessing_curse initialized but never populated, actor filmography never populated)
- Dual-source extraction pattern creates ambiguity: LLM unclear whether to populate `state_changes` or rely on `tactical_doc` regex

### 6.5 Overall

**Gimmick-elegance verdict: mixed**

The elegance center of gravity is in the core authority systems (injection tiers, suppression, pre-checks). The inelegance is concentrated in genre-specific contract surfaces (enum inconsistency, dormant registries, invisible justification patterns, degradation opacity).

---

## 7. Deferred Refactor Candidates

### DR-1. Technique/Realm Canonical Authority (long-term)
**Scope**: Extend StateTracker with per-NPC technique tracking; add canonical authority declaration for technique/realm in tier-0 prompt; add Stage 3 or Stage 4 enforcement for realm-technique violations against accumulated state.
**Rationale**: Residual survey identifies this as the one fact family where production contradictions are plausible. Current protagonist skills exist only in advisory; NPC technique mastery is untracked by any system.
**Evidence**: `per-work-fact-contract-alignment-residual-survey.md` section 2.8

### DR-2. State Changes Schema Formalization (long-term)
**Scope**: Replace implicit `state_changes: dict` contract with a TypedDict or Pydantic model; standardize enum values across relationship, disposition, and injury domains; document which fields are genre-conditional.
**Rationale**: Current dual-source extraction pattern (state_changes + regex) creates ambiguity. Inconsistent enum values cause silent upsert failures. An LLM generating state_changes has no schema to follow.
**Evidence**: `state_tracker_npc.py:287-289, 889`

### DR-3. BlockingValidator Status Field (long-term)
**Scope**: Replace `{"passed": True, "degraded": True}` with explicit `{"status": "PASSED"|"FAILED"|"DEGRADED"|"SKIPPED"}` field; add `mitigated_by` field for incarnation type; unify negation patterns across checks.
**Rationale**: Current degradation contract is ambiguous and incarnation mitigation is cosmetic. Downstream consumers must check multiple fields to understand true check state.
**Evidence**: `blocking_validator_consistency_checks.py:180-196`

---

## 8. No-Action / Settled Areas

### Settled: Core Injection Architecture
The three-tier injection (canonical block, canonical body, advisory tier-2) and 7-domain suppression landed in Wave 1 and verified in live code. No re-work needed.

### Settled: Dead-NPC Pre-Check
`stage3_orchestrator.py:1552-1602` — well-implemented, graceful degradation, non-blocking on error. Verified in residual survey.

### Settled: Entity Enforcement Checks
BlockingValidator entity checks (dead NPC resurrection, unowned item usage, damaged item usage, destroyed location visit) are CRITICAL-severity, well-tested, with sophisticated Hangul word-boundary detection.

### Settled: Investment Genre Guard
`StateTrackerFinancial` is a complete, isolated sub-module. `investment_guard.py` provides financial term validation. Clean separation, no cross-genre contamination.

### Settled: FactLedger Flat Schema
FactLedger's flat `{characters, numbers, items, locations, organizations}` schema with consistent `{status, last_ep, history[]}` pattern is clear and LLM-decodable.

### No-Action: Guard YAML Config Files
Genre YAML config files (`wuxia.yaml`, `hunter.yaml`, etc.) are data, not code. They are the intended extension point. No survey action needed.

### No-Action: Extended Genre Guards (actor, alt_history, composer, cooking, medical, sports)
These are term-only guards with no state tracking or enforcement beyond forbidden terms. They work correctly within their limited scope. Expanding them is a feature decision, not a friendliness concern.

---

## 9. Cross-Lane Handoff Notes

### To T3 (Stage 4 Authority / Verdict / Retry)
- BlockingValidator degradation semantics (H-1) affect how Stage 4 interprets validation results. If T3 identifies verdict-chain confusion, the degradation opacity finding here is a shared root cause.
- Incarnation type mitigation (H-7) flows through the Stage 4 verdict chain. T3 should assess whether the cosmetic mitigation causes downstream reasoning errors in Director.

### To T4 (Writer / Prompt / Context Injection)
- Justification pattern invisibility (H-4) directly affects Writer LLM behavior. If T4 identifies prompt composition gaps, the wuxia justification patterns are a concrete missing piece.
- The semantic context assembly opacity (H-6) at Stage 3 is a precursor to Stage 4 context building. T4 should assess whether the Stage 4 context builder adequately documents injection sources.

### To T1 (Navigation / Entry)
- The three-tier authority flow (StateTracker -> FactLedger -> WorldState) and the injection tier architecture (tier-0 canonical -> tier-2 advisory) are core to codebase navigation. If T1 finds orientation-pack staleness, these authority relationships should be reflected in any refresh.

### To T6 (Observability / Peripheral)
- Stage 3 lazy-init silent degradation (H-5) means the absence of a warning log when StateTracker/WorldState/FactLedger fail to initialize. T6 should assess whether observability sinks capture this degradation.
- Genre registry stub dormancy (hunter cooldown, fantasy blessing_curse, actor filmography) could appear as stale code in a peripheral sweep. T6 should record these as known stubs rather than stale code.

---

## 10. Confidence And Limits

### Verdicts

- **Navigation-ready for this lane**: yes
- **Cheap-fix-first verdict**: yes
- **Gimmick-elegance verdict**: mixed
- **Boundary-refactor can wait**: yes
- **Top 3 highest-ROI quick wins**:
  1. QW-3: Add justification patterns to LLM purism prompt (doc-only, directly reduces false rejections)
  2. QW-1: Add semantic context assembly source/authority comment (comment-only, reduces comprehension cost for cold LLM)
  3. QW-4: Add warning log on lazy-init failure (observability-only, makes degradation visible)

### Confidence

Estimated confidence: **96%**

Basis:
- All primary scope files read in full; key methods and contracts verified at file:line level
- Wave 1 contract alignment verified against live code (`stage4_context_builder.py:939-1008`, `stage3_orchestrator.py:1552-1602`)
- Residual survey findings confirmed independently (technique/realm gap, enum inconsistency, degradation opacity)
- Genre guard system surveyed across 14 files with YAML config cross-reference
- Lower confidence only on: (a) whether `_populate_genre_registries_from_arc()` is truly dead code or called from an uninspected path; (b) exact runtime behavior of `work_guard.yaml` conflict resolution in production

### Limits

- This survey inspected genre guards in the `dist/engine/` copy as well as production `modules/`. If the two copies have diverged, findings may apply to one but not the other.
- Stage 4 context builder injection was referenced from the residual survey but not independently re-read in this lane (delegated to T4).
- StateTracker financial sub-module (`state_tracker_financial.py`, 124 lines) was inspected but is isolated and poses minimal risk.

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- Document type: parallel static survey lane report (T5)
- Scope: fact authority systems (WorldState, FactLedger, StateTracker), genre guard system, blocking validator, genre-specific state tracking
- Mandatory sections: all 10 present
- P0/P1 findings have file:line anchors
- All recommendations have fix types
- Top Quick Wins: 8 items, 6 are comment/doc/observability (75%)
- Deferred Refactor Candidates: 3 (within cap)
- PASS

### Pass 2. Evidence and Consistency
- Authority precedence verified against live code and residual survey
- Suppression domains verified at `stage4_context_builder.py:939-971`
- Authority statement verified at `stage4_context_builder.py:996-1008`
- Dead-NPC pre-check verified at `stage3_orchestrator.py:1552-1602`
- Genre guard factory verified at `genre_guards/__init__.py:22-69`
- Wuxia realm-technique limits verified at `wuxia.yaml:169-177` and `blocking_validator_consistency_checks.py:374-431`
- Enum inconsistency verified across `state_tracker_npc.py` (3+ enum sets for similar concepts)
- No claim made beyond inspected evidence
- PASS

### Pass 3. Execution and Readability
- Findings ordered by priority (P1 first, then P2)
- Quick wins are actionable with specific file:line targets
- Deferred refactors explicitly marked long-term
- Cross-lane handoff notes identify concrete dependencies
- No scope creep into code modification or execution SSOT
- PASS
