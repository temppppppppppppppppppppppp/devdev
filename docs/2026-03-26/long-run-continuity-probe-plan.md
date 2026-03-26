# Long-Run Continuity Probe Plan

Date: 2026-03-26
Type: compact static survey (survey-only, no code changes)
Scope: sparse milestone probe plan for long-range continuity verification
Prior Context: `docs/2026-03-26/scene-pattern-probe-operating-note.md`

## Findings

### Continuity System Boundaries

The system has five distinct persistence layers, each with a different effective range. Long-run continuity failures will surface where these ranges end or overlap poorly.

| Layer | Effective Range | Pruning Behavior | File Anchor |
|-------|----------------|-----------------|-------------|
| **Reference Anchors** | 30 episodes (all types); unlimited (critical types only) | At 1000+ anchors: keep 700 recent + critical-type older ones. `combat` is **not** a critical type. | `reference_anchor.py` L162, L272-280 |
| **FactLedger** | 100 history entries per entity; 50K char summary | Oldest entries pruned at 100 per entity | `fact_ledger.py` L123-124, L437 |
| **RetrospectiveValidator** | 10 episodes (configurable) | Hard lookback window; facts outside window are not checked | `retrospective_validator.py` L23-30, `validation_orchestrator.py` L738-743 |
| **WorldStateManager** | Unlimited (cumulative DB-backed) | Never pruned; 9-field cumulative document grows indefinitely | `world_state.py` L90-139 |
| **Cumulative Bible** | Unlimited (cumulative merge) | LRU cache but DB persists all episode bibles | `db_manager.py` L680-773 |

### Three Highest-Value Long-Run Continuity Seams

**Seam 1: RetrospectiveValidator lookback boundary (EP 10+)**

The RetrospectiveValidator (`retrospective_validator.py` L30) defaults to 10-episode lookback. At EP12, facts established in EP1 are outside the validation window. The validator checks four things — realm regression, relationship regression, item disappearance, resolved conflict recurrence — but only within the lookback window.

This means: a character who gained a sword in EP1 could lose it silently at EP13 without the validator catching it. The FactLedger and WorldState still hold the fact, but the validator won't cross-check it.

**Risk**: medium-high. The validator is the main automated consistency check. Everything outside its window relies on LLM context coherence alone.

**Seam 2: Reference anchor `combat` type pruning (EP 30+)**

`reference_anchor.py` L162: `critical_types = {"item", "injury", "power", "relationship", "revelation"}`. The `combat` type is NOT in the critical set. After 30 episodes, combat anchors (who fought whom, outcome) are pruned from the recent window. They survive in the anchor DB but are not surfaced to the LLM unless they happen to fall within the 700-recent window.

This means: a major battle outcome from EP5 could be forgotten by EP36. The WorldState may record the consequence (injuries, deaths), but the specific combat narrative anchor is gone.

**Risk**: medium. Combat outcomes are partially preserved through injury/power anchors (which ARE critical), but the "who defeated whom" narrative thread is lost.

**Seam 3: Cross-arc state carry-forward (arc boundary)**

At arc boundaries (typically every 4-5 episodes), the entity registry refreshes (`three_phase_blueprint_runtime.py` L62-63, `stage3_orchestrator.py`). State must carry forward through: cumulative bible, FactLedger, WorldState, and reference anchors. If any layer fails to persist a fact across the arc boundary, it's silently lost.

**Risk**: medium. The existing 8-episode canaries cross one arc boundary (Arc 1→Arc 2 at EP5). But no test has validated whether facts from early in Arc 1 survive into late Arc 2 or Arc 3.

### Best Sparse Milestone Windows

Given the system's natural boundaries and existing project state:

| Window | Episode Range | Target Seam | Cost Estimate | Duration Estimate |
|--------|--------------|-------------|--------------|-------------------|
| **A** | EP5 only (on existing EP1-EP4 project) | Cross-arc state carry-forward | ~$0.70 | ~12 min |
| **B** | EP8-EP12 (extend existing EP1-EP7 project) | Past-lookback boundary (EP1 facts at EP12) | ~$3.50 | ~1 hour |
| **C** | EP13-EP20 (extend after Window B passes) | Long-range cumulative growth + anchor pruning | ~$6.00 | ~2 hours |

**Window A** uses existing `00_0000001` (4 manuscripts, 8 blueprints). Generate EP5 manuscript and check whether EP1 injury state, item ownership, and NPC relationships carry across the arc boundary.

**Window B** uses existing `00_001` (7 manuscripts, 11 blueprints) or extends the Window A project. The target is EP12 — the first episode where EP1 facts fall outside the retrospective validator's 10-episode lookback. Plant a specific traceable fact in EP1 state (or verify an existing one), then check whether EP12 generation respects it.

**Window C** runs only after A and B pass. Extends to EP20 to test cumulative state growth, WorldState document size, and whether the FactLedger summary stays coherent as entity histories accumulate.

### Probe Types (Priority Order)

1. **Cross-arc state carry-forward** (Window A)
   - Verify: injury state, weapon ownership, NPC relationship, protagonist location
   - Method: compare EP4 ending state with EP5 opening context
   - Pass criteria: zero contradictions in the 4 tracked categories

2. **Old fact recall** (Window B)
   - Verify: can EP12 recall a fact established in EP1?
   - Target facts: protagonist's initial weapon, first NPC relationship, initial location
   - Method: check EP12 blueprint/manuscript for references to EP1 facts
   - Pass criteria: no silent contradiction; fact either correctly referenced or correctly absent

3. **Deferred plotline / foreshadowing recall** (Window B)
   - Verify: does the context advisor surface EP1 foreshadowing at EP12?
   - Method: check `unresolved_plot` retrieval slots in EP12 context
   - Pass criteria: any EP1 foreshadowing that hasn't been resolved appears in context

4. **Ownership / resource continuity** (Window B-C)
   - Verify: items acquired in early episodes persist through mid-run
   - Method: check FactLedger item entries at EP12/EP20
   - Pass criteria: no item silently dropped from FactLedger

5. **Long combat continuity** (Window C, only if wuxia project)
   - Verify: combat outcomes from EP5 are remembered at EP20
   - Method: check whether combat-type reference anchors survive past EP30 window
   - Pass criteria: combat-relevant facts (injuries, power shifts) are accessible even if combat narrative anchors are pruned

### Concrete Operator Sequence

```
Step 1: Window A — arc boundary probe
├── Source: 00_0000001 (EP1-EP4 manuscripts exist)
├── Action: run Stage 3+4 for EP5 only
├── Check: cross-arc state carry-forward
├── Cost: ~$0.70 / ~12 min
├── If PASS → Step 2
└── If FAIL → STOP, open execution SSOT for arc-boundary seam

Step 2: Window B — past-lookback probe
├── Source: extend from Step 1 result (or use 00_001)
├── Action: run Stage 3+4 for EP8-EP12
├── Check: old fact recall + foreshadowing recall + item continuity
├── Cost: ~$3.50 / ~1 hour
├── If PASS → Step 3
└── If FAIL → STOP, open execution SSOT for specific failing seam

Step 3: Window C — long-range cumulative probe
├── Source: extend from Step 2 result
├── Action: run Stage 3+4 for EP13-EP20
├── Check: cumulative state growth + anchor pruning + FactLedger coherence
├── Cost: ~$6.00 / ~2 hours
├── If PASS → consider full run promotion
└── If FAIL → open execution SSOT for specific failing seam

Step 4: Full run (only if Steps 1-3 pass)
├── Action: fresh EP1-EP20+ contiguous run
├── Purpose: validate that all seams interact correctly in a real chain
├── Cost: ~$15-20 / ~5 hours
└── This is promotion, not diagnosis
```

### When to Escalate to Full Run

A full contiguous run is justified only when ALL of:
1. Window A passes (arc boundary clean)
2. Window B passes (past-lookback recall clean)
3. Window C passes (long-range accumulation clean)
4. The operator wants to promote the project/genre from "probed" to "production-trusted"

A full run is NOT justified when:
- Any window fails (fix the seam first)
- The question is "does this specific seam work?" (use a targeted probe)
- The goal is cost estimation only (use Window A alone and extrapolate)

### Recommended 3-Window Sparse Sampling Plan

| # | Window | Source Project | Episodes to Run | Primary Question | Expected Evidence |
|---|--------|---------------|-----------------|------------------|-------------------|
| 1 | A | `00_0000001` | EP5 | Does arc-boundary state carry-forward work? | EP5 opening context vs EP4 ending state |
| 2 | B | extend from A | EP8-EP12 | Does EP1 recall work at EP12? | EP12 context for EP1 facts; retrospective validator output |
| 3 | C | extend from B | EP13-EP20 | Does cumulative state hold at scale? | WorldState size, FactLedger summary, anchor count |

Total sparse probe cost: ~$10 / ~3.5 hours
Full contiguous run cost: ~$15-20 / ~5 hours
Savings if a seam fails at Window A: ~$14-19

## Recommendation

**Start with Window A (arc boundary probe).** It is the cheapest (~$0.70), fastest (~12 min), and tests the most common long-range seam. If it fails, the failure is actionable without needing Windows B or C. If it passes, Window B follows to test the next boundary.

Do not open an execution SSOT yet. The probe plan itself is the deliverable. An execution SSOT should be opened only after a specific probe window fails and identifies a concrete seam to fix.

---

## 3-Pass Audit Notes

- Pass 1: scope bounded to probe plan design; five persistence layers identified with effective ranges and pruning behavior; three seams prioritized by risk and testability; file:line anchors for all system boundaries
- Pass 2: probe windows anchored to existing project state (`00_0000001` EP1-EP4, `00_001` EP1-EP7); cost estimates based on prior canary data ($0.70/ep Arc 2, $1.00/ep Arc 1); operator sequence is linear with explicit stop conditions
- Pass 3: recommendation is singular (start Window A); escalation rule is explicit; no scope creep into code changes or execution SSOT creation
- Confidence: 96%

---

- Best long-run first move: **arc boundary probe (Window A, EP5 on existing project)**
- Full long run as first step: **no**
- Should Codex open an execution SSOT now: **no**
