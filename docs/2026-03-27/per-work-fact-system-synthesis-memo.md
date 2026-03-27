# Per-Work Fact System Synthesis Memo

Date: 2026-03-27
Status: final
Type: system-track synthesis memo (survey synthesis only, no code changes)
Canonical Path: `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
Inputs:
- `docs/2026-03-27/per-work-registry-need-compact-survey.md`
- `docs/2026-03-27/per-work-fact-contract-authority-compact-survey.md`

## Findings

The core problem is **not** a missing per-work storage layer.

The core problem is a narrower combination:
- **ownership/authority declaration is still partly implicit**
- **LLM injection precedence is partly implicit**
- **a few fact classes remain under-modeled**
- but **the codebase already has enough storage/index layers**

In other words, the current system is closer to:
- `storage sufficient`
- `authority mostly sufficient`
- `prompt-facing contract clarity insufficient`

This means the next move should not be "add a new registry system first."
It should be "clarify authority and injection rules first, then extend specific fields only if real failures appear."

## What Current Systems Already Do Well

The two surveys converge on the same picture: the system already carries substantial per-work fact state across multiple layers.

Already strong:
- Static identity and protagonist/world setup are seeded from BI and persist through runtime context.
- Realized state is already tracked in persisted layers:
  - `FactLedger`
  - `WorldState`
  - `Reference Anchors`
- Extracted and derived state already exists:
  - `StateTracker`
  - `Entity Registry`
  - `ImmutableFactPacket`
- Long-gap continuity is already proven to a meaningful degree.
  - EP1 facts survived to EP12 with no contradiction in the lookback probe.
- Wuxia combat continuity is already stronger than feared for:
  - injury carry-forward
  - weapon/item continuity
  - realm gating
  - combat/injury anchors

Practical synthesis:
- The system already behaves like a distributed per-work fact system.
- The problem is not "there is nowhere to store facts."
- The problem is "the same fact may exist in multiple layers without a sufficiently explicit prompt-facing precedence rule."

## Where Authority Is Already Clear

The authority survey found explicit, code-level suppression and precedence in important domains.

Already clear:
- `WorldState > StateTracker` for:
  - dead NPCs
  - item state
  - relationship changes
  - NPC injury
  - NPC movement
  - timeline
- `FactLedger > StateTracker` for financial/numeric state
- `BI` remains authoritative for protagonist identity, world origin, and genre/static setup
- `Director` remains final quality authority

This matters because it means the system is not authority-free chaos. The spine already exists.

## Where Authority Is Still Unclear

The unresolved seams are not broad. They are specific.

Main unclear seams:
- **BI -> FactLedger numeric handoff**
  - BI defines initial numbers
  - FactLedger defines runtime-evolved numbers
  - the runtime mostly behaves correctly by recency
  - but the LLM is not told that precedence explicitly enough
- **Reference Anchors vs WorldState overlap**
  - both can speak about related event/state domains
  - operationally they usually agree
  - but reconciliation is more inferred than contractually stated
- **Stage 3 advisory vs Stage 4 canonical**
  - Stage 3 sees canonical state
  - but treats it as guidance, not a hard pre-check
  - some contradictions are still caught later than ideal

These are authority-contract issues, not storage absence.

## Where Injection Priority Is Still Unclear

The second survey makes the important distinction that current injection order is mostly sensible, but still partly implicit.

What is already good:
- hard constraints appear before softer narrative context
- canonical constraint packets already outrank looser summaries
- continuity packet and NPC boundary block are high in the stack

What is still unclear:
- whether the LLM is explicitly told:
  - "runtime numeric facts override BI initial numeric facts"
  - "persisted realized state outranks extracted advisory summaries"
- whether Stage 3 should enforce a small subset of Stage 4 canonical impossibility checks earlier

So the gap is less:
- "wrong ordering"

and more:
- "insufficiently explicit ordering rule"

That pushes the recommendation toward contract clarification, not a new registry layer.

## Where a Registry-Like Layer Might Actually Be Justified

The registry survey is clear that a brand-new per-work registry system is not justified right now.

Still, a registry-like concept is justified in a narrower sense for under-modeled fact classes:
- technique usage history within a sustained fight
- explicit organization/sect membership edges
- cross-episode fight geography
- cross-episode tactical escalation state

But these are best understood as:
- **field-level extensions to existing systems**
- not a mandate for an 8th or 9th fact authority layer

So the synthesis view is:
- a "registry-like slice" may be justified for some special fact domains
- a "new general registry system" is not justified by current evidence

## Alternative Solutions To Registry

The surveys support at least three lighter alternatives.

### 1. Contract-only clarification

Add explicit prompt-facing authority statements such as:
- runtime numeric facts supersede BI seed numbers
- persisted realized state supersedes extracted advisory summaries

This is the lightest intervention.

### 2. Stage-3 pre-check tightening

Move a few high-value impossibility checks earlier:
- dead NPC active-role assignment
- possibly other clearly impossible canonical conflicts

This reduces wasted Stage 4 cycles without adding storage.

### 3. Field extension within current layers

If and only if future probes show real drift:
- add `fight_geography`
- add `technique_usage_log`
- add explicit membership edges

These can live inside existing systems such as:
- `WorldState`
- `StateTracker`
- `Reference Anchors`

### 4. Full registry layer

This is currently the least justified option because:
- current layers already overlap heavily
- a new registry would increase write-back coordination cost
- the demonstrated failures are contract and precedence issues first

## Recommended Direction

**contract-only**

More precisely:
- explicit authority clarification first
- minimal Stage 3 pre-check alignment second
- no new per-work registry system yet

Why this is the right direction:
- both surveys reject the idea that storage/index is the primary missing piece
- both surveys point to implicit authority and prompt precedence as the real seam
- both surveys show that current runtime layers already hold enough information for most fact classes

So the recommended architecture direction is:
- do not add a new generalized registry layer now
- sharpen the authority contract around the layers that already exist

## Lightest Viable Next Step

**one design memo**

That memo should narrowly define:
- fact ownership by layer
- prompt-facing precedence rules
- which Stage 3 checks should become earlier hard guards
- which future gaps, if any, deserve field-level extensions

It should not yet:
- open a broad execution SSOT
- introduce a new registry store
- redesign all persistence surfaces

## Final Synthesis

If this topic is framed as:
- "Do we need a per-work registry?"

the answer is:
- **not yet**

If it is framed as:
- "Do we need to tighten per-work fact contract alignment and injection precedence?"

the answer is:
- **yes**

So the best reading is:
- the next problem to solve is **contract clarity**
- not **storage proliferation**

## 3-Pass Audit Record

Pass 1. Structure and Scope
- synthesis memo type matches request
- scope stays at survey synthesis only
- registry and non-registry options are both considered
- no execution planning creep
- PASS

Pass 2. Evidence and Consistency
- synthesis stays within claims made by the two input surveys
- no new authority claims added beyond surveyed evidence
- distinction between storage/index problems and authority problems is explicit
- recommendation aligns with both surveys:
  - registry need low
  - contract/alignment issue real but not execution-ready
- PASS

Pass 3. Execution and Readability
- findings-first structure
- current strengths vs unresolved seams separated
- alternative solutions to registry explicitly listed
- one direction and one next step only
- PASS

Estimated confidence: 97%

---

- Recommended direction: contract-only
- Dominant unresolved seam: prompt-facing authority precedence remains implicit
- Should Codex open an execution SSOT now: no
