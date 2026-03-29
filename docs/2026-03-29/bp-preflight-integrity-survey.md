# BP Preflight Integrity Survey

Date: 2026-03-29
Status: final (3-pass audited)
Scope: narrative pipeline — per-work episode production
Canonical Path: `docs/2026-03-29/bp-preflight-integrity-survey.md`

## 1. Scope and Intent

### What This Is

A **pre-canary blueprint integrity gate**.
Before a canary run consumes LLM budget on manuscript generation and Director review,
this survey compares the current episode's blueprint/frontier against prior-episode truth
to surface BP-origin conflicts that would otherwise cause predictable canary failures.

### What This Is Not

- Not a replacement for canary runs. Canary validates manuscript quality; this validates blueprint structural integrity.
- Not a quality review. Director sovereignty over narrative judgment is unaffected.
- Not a system-track order. This is a narrative pipeline operating standard, scoped to per-work episode production.
- Not a Stage 2/3 validation replacement. Stage 2 preflight and Stage 3 blueprint generation have their own validation chains. This survey sits between Stage 3 output and Stage 4 canary input.

### Why

The EP3 extreme-loop incident and prior canary waste cases share a common root: canary was launched on a blueprint that already contradicted settled truth. The canary faithfully produced manuscripts from a flawed blueprint, then Director faithfully rejected them, burning retry budget on a structurally unwinnable loop.

Catching these conflicts before canary launch is cheaper than catching them during canary retries.

## 2. Inputs

### Authority Preference (highest first)

| Priority | Source | Description | Access Path |
| --- | --- | --- | --- |
| 1 | Prior episode committed manuscript | The actual text that was accepted and committed | `projects/{project}/episodes/episode_NNNN.txt` |
| 2 | WorldStateManager snapshot | Post-commit world state after prior episode | `db.load_anchor("world_state")` |
| 3 | FactLedger snapshot | Cumulative numerical/factual truth | `db.load_anchor("fact_ledger")` |
| 4 | ChainLink for prior episode | Episode-to-episode continuity bridge | `db.load_anchor("chain_link_{ep}")` |
| 5 | Master Bible / BI | Project-level character and world definitions | `db.load_anchor("bible")` |
| 6 | Current episode blueprint | Stage 3 output for the episode about to be canary'd | `db.get_blueprint(ep_num)` or `blueprint_NNNN.txt` |
| 7 | Current treatment block metadata | If a treatment governs the current arc | `treatments/*.json` relevant block |

### Divergence Rule

This table defines retrieval preference, not blind truth override.

If the highest-priority manuscript truth conflicts with `world_state`, `fact_ledger`, or another persistent truth source, the survey must not silently pick one side and continue.
It must emit `TRUTH_SOURCE_DIVERGENCE` and surface:

- the conflicting sources
- the conflicting fact
- the affected blueprint obligation, if any
- the recommended next move:
  - `PATCH BP FIRST`
  - or `ESCALATE TO HUMAN`

The preflight gate is allowed to stop on source divergence. It is not allowed to hide storage drift behind a false clean pass.

### Minimum Required Inputs

- Prior episode committed manuscript (or world_state + fact_ledger if EP1)
- Current episode blueprint
- WorldStateManager snapshot

If any minimum input is missing or unparseable, the preflight survey cannot proceed and must report `INCOMPLETE_INPUTS` rather than a false pass.

## 3. Three-Layer Method

### Layer 1: Truth Ledger

Python extracts the following from prior-episode truth sources into a structured truth ledger.
No LLM judgment at this layer — extraction only.

| Category | What to Extract | Primary Source |
| --- | --- | --- |
| Completed Events | Events that already happened and cannot happen again as if new | WorldStateManager `timeline` + prior manuscript |
| Held Assets / Items | Items the protagonist currently possesses | WorldStateManager `active_items` + `protagonist.assets` |
| Disclosed Relationships | Relationship states already revealed to the reader | WorldStateManager `relationships` + `alive_npcs` |
| Cognitive / Recognition States | What characters know about each other | WorldStateManager `alive_npcs[].known_attrs` + prior manuscript |
| Settled Goal States | Goals already achieved, abandoned, or resolved | WorldStateManager `active_plots` (status=resolved) + `motivations` (status=resolved) |
| Character Status | Alive/dead, injury level, location | WorldStateManager `alive_npcs`, `dead_npcs`, `protagonist` |
| Established World Laws | Immutable rules of the story world | WorldStateManager `world_laws` |
| Numerical Facts | Quantified truths (power levels, currency, counts) | FactLedger `numbers` block |

Output: a flat JSON or markdown table, one row per fact, with source attribution and episode number.

### Layer 2: Blueprint Obligation Map

Python extracts the following from the current episode blueprint.
No LLM judgment at this layer — extraction only.

| Field | Source Key | Description |
| --- | --- | --- |
| Title | `blueprint.title` or integrated scenario heading | Episode title |
| Core Tension | `blueprint.core_tension` | Central dramatic question |
| Target Beat | `blueprint.target_beat` | The key narrative beat this episode must land |
| Scene Goals | `blueprint.scene_breakdown` | Per-scene objectives and expected outcomes |
| Expected Ending | `blueprint.expected_ending` | Target ending state |
| Relationship Changes | `blueprint.relationship_changes` | Planned NPC relationship transitions (from_state → to_state) |
| Protagonist Start State | `blueprint.protagonist_state` + `blueprint.start_location` | Where and how the protagonist begins this episode |
| Inventory Assumptions | Implicit items/assets the blueprint assumes the protagonist has | Derived from scene_breakdown + integrated_scenario |
| Time Flow | `blueprint.time_flow` | Expected time progression |

Output: a flat JSON or markdown table, one row per obligation.

### Layer 3: Delta / Conflict Family Map

**This layer is LLM-executed.** Python provides the truth ledger (Layer 1) and blueprint obligation map (Layer 2) as structured inputs. The LLM compares them and assigns each detected conflict to a conflict family (Section 4).

The LLM must:
1. Compare each blueprint obligation against the truth ledger
2. Identify contradictions, impossible assumptions, and structural mismatches
3. Classify each conflict into exactly one conflict family
4. Assess whether the conflict is a true structural problem or a harmless variation
5. Assign a risk tier (Section 5)

The LLM must not:
- Invent facts not present in the truth ledger
- Overwrite or reinterpret prior-episode truth
- Judge narrative quality, style, or artistic merit
- Make Director-level decisions about what should happen in the story

## 4. Conflict Families

### CF-1: Completed-Event Replay

The blueprint plans an event that already occurred and was committed as truth.
The event would read as a structural duplicate, not as an intentional callback or echo.

Examples:
- Blueprint plans "protagonist discovers the hidden cave" when EP5 already committed the cave discovery
- Blueprint plans "first meeting with NPC X" when NPC X was introduced in EP3

Distinguishing from harmless variation:
- A character revisiting a location is not replay; re-discovering it as if for the first time is.
- A callback or flashback that acknowledges the prior event is not replay; narrating it as a new event is.

### CF-2: Confirmed-State Regression

The blueprint assumes a character, item, or world state that contradicts the last committed state.

Examples:
- Blueprint assumes protagonist is uninjured when world_state records `injuries: "중상"`
- Blueprint assumes NPC X is alive when `dead_npcs` lists them
- Blueprint places protagonist in City A when world_state records `location: "City B"` with no travel event

### CF-3: Opening-Ending Mismatch

The blueprint's `start_location` or `protagonist_state` contradicts the prior episode's `expected_ending` or committed ending state.

Examples:
- Prior EP ended with protagonist imprisoned; current BP opens with protagonist at home with no escape event
- Prior EP ended mid-combat; current BP opens the next morning with no resolution

### CF-4: Inventory False Gap

The blueprint assumes the protagonist lacks an item they already possess, creating a false acquisition quest.
Conversely, the blueprint assumes the protagonist has an item they never acquired.

Examples:
- Blueprint plans "protagonist must find the jade pendant" when `active_items` already lists it
- Blueprint uses a weapon the protagonist never obtained and world_state does not record

Escalation note:
- If the false gap underpins `core_tension`, `target_beat`, `expected_ending`, or multiple scene goals, classify it as structurally blocking and route it as `HIGH`, not `MEDIUM`.

### CF-5: Role Regression

The blueprint assigns an NPC a role or relationship state that contradicts their established trajectory.

Examples:
- NPC X was elevated to ally in EP7; blueprint treats them as unknown stranger
- NPC Y was established as a faction leader; blueprint demotes them to minor bystander without cause

Escalation note:
- If the regressed role governs the episode's main tension, gatekeeping relationship, or ending condition, classify it as structurally blocking and route it as `HIGH`, not `MEDIUM`.

### CF-6: Target-Stage Regression

The blueprint's `target_beat` or `core_tension` duplicates or regresses a goal stage that was already resolved in prior episodes.

Examples:
- Blueprint's core_tension is "will protagonist pass the entrance exam" when the exam was already passed
- Blueprint's target_beat revisits a power-up milestone already achieved

### CF-7: Factual Detail Drift (advisory only)

Numerical or minor factual details in the blueprint don't match FactLedger records, but the mismatch is not structurally destructive.

Examples:
- Blueprint mentions "30 gold coins" when FactLedger records 28
- Blueprint references a technique name with slightly different wording

This family is advisory. It should be reported but does not independently trigger a high-risk tier. The distinction from CF-2 is: CF-2 involves structural state (alive/dead, location, injury) while CF-7 involves quantitative or naming details that don't break the narrative skeleton.

## 5. Risk Tiers and Routing

### Tier Assignment Rules

| Tier | Condition | Routing |
| --- | --- | --- |
| **LOW** | Zero conflicts, or only CF-7 advisory items | Proceed to canary. Attach CF-7 items as watchlist annotations if present. |
| **MEDIUM** | One or more CF-4 or CF-5 conflicts with limited blast radius (single scene, single NPC, not carrying `core_tension`, `target_beat`, or `expected_ending`) | Canary may proceed, but attach conflict watchlist to canary context so Director can compensate. Monitor canary retry rate. |
| **HIGH** | Any CF-1, CF-2, CF-3, or CF-6 conflict; OR any CF-4/CF-5 conflict that structurally underpins `core_tension`, `target_beat`, `expected_ending`, or multiple scene goals; OR two or more MEDIUM-tier conflicts in the same blueprint; OR `TRUTH_SOURCE_DIVERGENCE` in a fact that the blueprint depends on | **Do not launch canary.** Blueprint or frontier must be patched first. If patch is not feasible, escalate to human review. |

### Tier Escalation

- If a MEDIUM-tier canary produces 3+ retries on the conflicted scene, retroactively escalate to HIGH and halt.
- If the same conflict family recurs across consecutive episodes, escalate the family's base tier by one level for the next preflight.

### Ambiguity Rule

When the LLM cannot determine whether a detected delta is a true conflict or a harmless variation, it must classify it as MEDIUM rather than silently passing it. False positives are cheaper than false negatives at this gate.

## 6. Output Contract

The preflight survey must produce one output document (or structured JSON) containing exactly these sections:

### 6.1 Truth Ledger Summary

A compact table of prior-episode truth facts relevant to the current blueprint.
Maximum 40 rows. Prioritize facts that intersect with blueprint obligations.

Format per row:
```
| Fact | Category | Source EP | Source Anchor |
```

### 6.2 Blueprint Obligation Map

A compact table of current blueprint commitments.
One row per field from Layer 2.

Format per row:
```
| Obligation | Blueprint Field | Value Summary |
```

### 6.3 Conflict Family Table

One row per detected conflict. Empty table if no conflicts found.

Format per row:
```
| # | Conflict Family | Description | Truth Reference | Blueprint Reference | Severity |
```

### 6.4 Risk Tier

Single line: `LOW`, `MEDIUM`, or `HIGH` with one-sentence justification.

### 6.5 Recommended Next Move

Exactly one of:
- **PASS TO CANARY** — no blocking conflicts; canary may proceed.
- **PASS TO CANARY WITH WATCHLIST** — MEDIUM conflicts attached; canary proceeds with monitoring.
- **PATCH BP FIRST** — HIGH conflicts detected; specify which blueprint fields need correction before canary.
- **ESCALATE TO HUMAN** — conflicts are ambiguous or cross-cutting enough that automated patching is not safe.

### 6.6 Operator Notes (optional)

Free-text field for edge cases, caveats, or context that doesn't fit the structured sections.

### Output Size Target

The entire preflight output should be under 3,000 characters for LOW-tier results, under 5,000 characters for MEDIUM/HIGH. This is a gate check, not an essay.

## 7. Guardrails

### Division of Labor

- **Python** collects, extracts, and structures the truth ledger and blueprint obligation map. Python does not classify conflicts or assign risk tiers.
- **LLM** compares the two layers, classifies conflicts into families, distinguishes harmless variation from true replay/regression, and assigns risk tiers. LLM does not overwrite truth sources or modify blueprints.

### Sovereignty Boundaries

- This gate checks **structural integrity**, not **narrative quality**. Whether the story is good is Director's jurisdiction.
- The preflight survey does not replace Director's open_review, advisory chain, or Chief Writer judgment.
- A preflight PASS does not guarantee canary success. It means the blueprint is not structurally contradicting settled truth.
- A preflight HIGH does not mean the story concept is bad. It means the blueprint's assumptions don't match the world's current state.

### Truth Protection

- The preflight survey must never overwrite, amend, or reinterpret facts in WorldStateManager, FactLedger, or prior manuscripts.
- If a truth source appears incorrect, the survey reports the discrepancy but does not resolve it. Resolution is a separate human-authorized action.

### Variation vs Replay

- **Harmless variation**: a character revisits a place, references a past event, or echoes a prior theme intentionally. These are valid narrative tools.
- **True replay**: the blueprint narrates a previously committed event as if it never happened. This is a structural defect.
- The LLM must distinguish between these. When uncertain, classify as MEDIUM and flag for operator attention.

### Scope Limit

- This survey applies to a single episode's blueprint against the immediate prior episode plus persistent truth stores (`world_state`, `fact_ledger`, chain-link, and bible-backed continuity anchors). It is not a full-arc consistency audit.
- Cross-arc or multi-episode structural analysis is outside this gate's scope and belongs to higher-level review processes.

## 8. Recommended First Adoption

### Phase 1: Targeted Adoption

Apply the preflight survey only to:
- **EP2+ episodes** (EP1 has no prior-episode truth to compare against)
- **Episodes following a high-retry canary** (the prior episode's canary required 4+ retries, indicating the arc may carry forward structural issues)
- **Arc-boundary episodes** (first episode of a new arc, where blueprint assumptions about prior arc resolution are most likely to drift)

### Phase 2: Expanded Adoption

After Phase 1 demonstrates value (measured by reduction in canary retry rate for preflight'd episodes):
- Extend to all EP2+ episodes in active production
- Consider running preflight in parallel with blueprint generation's own validation to reduce wall-clock time

### Phase 3: Full Integration

If Phase 2 confirms consistent value:
- Make preflight a mandatory gate before any canary launch
- Integrate preflight output into canary context so Director has conflict awareness from the start
- Track preflight-to-canary correlation metrics for continuous calibration

### Adoption Guardrail

Do not jump to Phase 3 without evidence from Phase 1/2. The preflight gate adds latency and LLM cost. Its value must be demonstrated empirically before it becomes mandatory infrastructure.

## 9. Implementation Notes (non-binding)

These notes are design-time observations for whoever implements this survey. They are not commitments.

- Layer 1 extraction can reuse existing `WorldStateManager` snapshot and `FactLedger.summarize_fact_ledger_numbers_block()` rather than building new extractors.
- Layer 2 extraction can reuse existing blueprint Pydantic model field access.
- Layer 3 LLM call should be a single focused prompt with structured output (JSON), not a multi-turn conversation.
- The LLM call for Layer 3 can use a budget-tier model (e.g., Gemini Flash or Haiku) since the task is structured comparison, not creative generation.
- Preflight output should be saved alongside canary artifacts for post-hoc analysis of gate effectiveness.
- If `INCOMPLETE_INPUTS` is reported, the operator should fix the input problem rather than bypassing the gate.

## 10. 3-Pass Audit Record

### Pass 1. Scope and Method

- bounded the document to a pre-canary blueprint integrity gate rather than a full narrative-quality review
- kept the division of labor explicit: Python collects, LLM classifies
- PASS

### Pass 2. Risk and Truth Governance

- corrected authority handling so source conflicts emit `TRUTH_SOURCE_DIVERGENCE` instead of being silently overwritten
- tightened risk routing so structurally central CF-4/CF-5 cases escalate to `HIGH`
- widened the truth frame from immediate prior episode only to immediate prior episode plus persistent truth stores
- PASS

### Pass 3. Operator Readability and Adoption

- output contract is compact enough for gate use rather than essay-style review
- adoption path is staged, so the survey can prove value before becoming mandatory
- guardrails preserve Director sovereignty and fact ownership
- PASS

Estimated confidence: `97%`
