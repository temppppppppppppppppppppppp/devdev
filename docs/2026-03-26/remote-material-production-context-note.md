# Remote Material Production Context Note

Date: 2026-03-26
Status: final
Type: operating note
Scope: remote LLM material production context for BI/TR work
Audience: remote narrative/material-generation LLM

## 1. Purpose

This note fixes the current split of responsibilities:

- local workspace:
  - code
  - harness/runtime
  - validation/regression
  - consumer contract authority
- remote workspace / remote LLM:
  - BI/TR generation
  - static material improvement
  - candidate salvage work
  - genre-family material expansion

The remote side should assume:

- the local harness is the consumer authority
- the remote side should improve materials, not redesign the runtime
- material quality and material consumability are separate questions

## 2. Current Operating Split

### 2.1 Local owns

- code and runtime behavior
- Stage 0/1 ingress and normalization
- Stage 2/3/4 harness and validation logic
- tests, regression, probes, canaries
- consumer contract decisions

### 2.2 Remote owns

- BI/TR generation and revision
- static quality improvement
- salvage triage of quarantined materials
- genre-family material expansion
- making material outputs worth consuming

### 2.3 Remote should not assume

- that local code will be changed to fit weak materials
- that placeholder BI scaffolding is acceptable just because the pair parses
- that "consumable by harness" means "high-quality material"

## 3. Hard Truths As Of Now

### 3.1 Family-native ingress is working

Confirmed by:

- `docs/2026-03-26/genre-expansion-family-native-ingress-wave1-canary-report.md`

Practical meaning:

- current runtime can admit:
  - treatment `list`
  - treatment `dict.blocks`
  - treatment `dict.treatments`
- family-native raw inputs no longer need a new harness just to enter Stage 0/1/2

### 3.2 Wuxia is consumable now

Confirmed by:

- `docs/2026-03-26/genre-expansion-family-native-ingress-wave1-canary-report.md`
- `docs/2026-03-26/wuxia-combat-quality-probe-report.md`

Practical meaning:

- wuxia BI/TR can be produced remotely now
- combat-heavy Stage 2/3 windows already passed
- bounded verdict: wuxia combat is usable through Stage 3 blueprint scope

Not fully proven yet:

- long open-field multi-episode fight geography
- technique progression tracking
- broad Stage 4 combat proof across long windows

So the current rule is:

- remote may produce wuxia materials now
- but should prefer strong fight geography, injury carry-forward, and item continuity clues in the materials

### 3.3 Blockguide materials are the weaker lane right now

Confirmed by:

- `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`

Practical meaning:

- many business/urban-fantasy BI/TR pairs are consumable
- but the dominant weakness is not parser failure
- the dominant weakness is thin BI quality

Observed pattern:

- TR often has usable structure
- BI often becomes a thin auto-generated echo of TR
- this produces "consumable but weak" material

## 4. Current Consumer Contract Remote Must Respect

Remote should optimize materials for the current local consumer contract, not for an imagined future runtime.

### 4.1 Treatment expectations

Accepted shapes:

- raw `list`
- `dict.blocks`
- `dict.treatments`

Minimum practical rule:

- each block must carry real usable payload, not title-only shell text
- current harness can rebuild canonical `plot_roadmap` from TR

### 4.2 BI expectations

BI should not just restate the TR.

Good BI should:

- amplify protagonist engine
- sharpen NPC function and differentiation
- deepen conflict transitions
- carry useful Seeds / echo / payoff information
- clarify the growth resource / power axis

Bad BI pattern:

- auto-generated shell
- repeated boilerplate NPC blurbs
- placeholder HUD/state fields
- empty or dead Seeds
- no new structural leverage over TR

### 4.3 `protagonist_config`

The runtime can tolerate partial protagonist config, but better remote output should supply a stronger usable subset.

Helpful keys include:

- `world_origin`
- `incarnation_type`
- `pov`
- `external_pov_insert_policy`

Family-native keys may coexist and should not be flattened away.

## 5. Remote Quality Bar

Remote should judge materials on two layers:

1. consumability
2. narrative quality

Do not confuse them.

### 5.1 Consumable

Means:

- current harness can ingest the pair
- the TR yields a usable canonical roadmap
- the BI/TR pair survives current validation

### 5.2 High-quality

Means:

- strong premise / hook
- protagonist with a real engine
- measurable growth resource / power axis
- block-to-block progression density
- sceneability
- genre texture
- BI that adds information, not echo

## 6. The Main Failure Pattern To Avoid

Current dominant weak pattern:

`BI-auto-generated-thin-echo`

Symptoms:

- BI mirrors TR structure without adding depth
- NPC descriptions are generic and repeated
- Seeds are empty or dead
- FinanceHUD or equivalent state fields are placeholders
- block summaries are mechanism-only, not scene-rich
- emotional and relational progression exists as metadata only

If the remote side fixes only one thing, fix this.

## 7. Blockguide-Specific Guidance

### 7.1 What is currently true

No current blockguide quarantine candidate is `strong`.

Best salvage shortlist right now:

1. `chaebol_ent_empire`
2. `pantech_cyworld_reborn`
3. `empire_youngest_allsector`

Usable but mixed:

- `chaebol_ent_empire`
- `pantech_cyworld_reborn`
- `empire_youngest_allsector`
- `us_ai_exile_monopoly`
- `chaebol_allowance_zero`

Consumable but skeleton-likely:

- `defense_defect_engineer`
- `fallen_prince_buys_joseon`

### 7.2 What remote should do for blockguide

Priority is not raw volume.

Priority is:

- make BI actually amplify TR
- add scene meat
- add human friction and tactical specifics
- break repeated template language
- make protagonist and NPCs feel different

### 7.3 What remote should not do for blockguide

- do not mass-produce more thin BI wrappers
- do not rely on placeholder FinanceHUD or empty seeds
- do not produce blocks that are only business-outcome summary
- do not assume arithmetic progression alone is narrative density

## 8. Wuxia-Specific Guidance

### 8.1 What is currently true

Wuxia material production is now allowed.

Current bounded evidence says:

- ingress works
- Stage 2 works
- Stage 3 combat-heavy blueprints work

### 8.2 What remote should emphasize

- fight geography
- injury carry-forward
- weapon/item state
- tactical escalation
- technique identity
- power/realm progression

### 8.3 What remote should remember

Current risk seam is:

`cross-episode fight geography not structurally persisted`

So remote should make geography and continuity more explicit in the material itself, especially for:

- open-field battles
- multi-episode combat chains
- shifting positions and formations

## 9. Recommended Remote Production Strategy

### 9.1 For business/urban-fantasy families

Use this order:

1. improve top-3 salvage candidates first
2. repair BI thin-echo pattern
3. only then expand volume

### 9.2 For wuxia family

Use this order:

1. continue BI/TR production
2. bias materials toward combat continuity readiness
3. avoid assuming Stage 4 long-window combat is fully proven

### 9.3 For all families

Prefer:

- fewer materials with stronger sceneability

over:

- many structurally valid but narratively thin pairs

## 10. Remote Output Checklist

Before considering a material pair "done", remote should check:

- Is the premise commercially legible?
- Is the protagonist more than a label?
- Is the growth axis concrete?
- Can each block become an episode scene, not just a result summary?
- Does BI add real value beyond TR?
- Are NPCs differentiated?
- Are seeds/payoffs alive?
- Are key state fields populated instead of placeholder?

If the answer to several of these is no, the pair is probably only consumable, not good.

## 11. What Remote Should Send Back

Preferred return shape from remote work:

- work id / title
- family
- BI path
- TR path
- short quality self-assessment:
  - strong
  - usable but mixed
  - skeleton-likely
- one-line risk note

This helps the local side decide:

- direct probe
- local validation
- quarantine hold
- or ignore

## 12. Single Summary

The local side is now stable enough that remote should stop producing material that merely passes structure.

The current leverage is:

- respect the live local consumer contract
- produce family-native BI/TR that are actually sceneable
- for blockguide, fix BI thin-echo
- for wuxia, lean into combat continuity clarity

In short:

`Remote should optimize for consumable + narratively worth reading, not consumable-only.`
