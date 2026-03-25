# T2. Arc Distribution Layer — Protagonist Overvaluation Survey

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: lane survey report
Canonical Path: `docs/2026-03-25/opus-protagonist-overvaluation/t2-arc-distribution.md`
Master Order: `docs/2026-03-25/protagonist-overvaluation-staging-4terminal-master-order.md`
Scope: narrative-design survey only — no code changes

## 1. Survey Question

Where should protagonist high-evaluation (`주인공 고평가`) beats be distributed across arcs, and should admiration modes rotate by arc?

## 2. Current Arc-Level Infrastructure for Protagonist Evaluation

### 2.1 Fields That Already Exist

| Field | Location | What It Does | Evaluation Coverage |
|-------|----------|-------------|-------------------|
| `tactical_doc` | arc JSON | Per-episode narrative breakdown (화당 500자+) | Describes WHAT happens, not HOW protagonist is perceived |
| `beat_sequence` | arc JSON | Per-episode event beats | Event sequence, not evaluation design |
| `hybrid_composition` | arc JSON | primary/secondary narrative pattern + mixing_logic | Pattern labels only — no admiration mode vocabulary |
| `satisfaction_score` | state_extractor (post-gen) | 1-10 reader satisfaction per episode | Measures intensity, not TYPE of satisfaction |
| `protagonist_agency` | state_extractor (post-gen) | 자력/협력/타인의존 | Measures independence, not how others perceive protagonist |
| `protagonist_emotion` | state_changes | Arc-end protagonist emotion | Protagonist's own feeling, not others' evaluation OF protagonist |
| `side_glimpse` preset | blueprint_ensemble SCENE_PRESETS | "조연 시점 전환 — '저 사람 대단해!' 반응" | Single undifferentiated preset — no mode variants |

**Evidence files**:
- `config/prompts/ensemble.yaml` L4-260 (arc prompt + schema)
- `modules/domain/agents/state_extractor.py` L35-57 (satisfaction_score, protagonist_agency)
- `modules/domain/agents/blueprint_ensemble.py` L93-103 (SCENE_PRESETS including side_glimpse)
- `modules/models/arc.py` L211 (hybrid_composition field)

### 2.2 Existing Arc-Level Beat Distribution Mechanisms

The arc prompt already distributes several narrative properties across episodes:

1. **감정 곡선 (Emotion Curve)**: "연속 3화 이상 같은 감정 톤 금지" — `ensemble.yaml` L29
2. **반전 포인트 (Reversal)**: "Arc 내 최소 1개" — `ensemble.yaml` L28
3. **캐릭터 선택의 순간 (Dilemma)**: "양쪽 다 손해인 딜레마에서 의미 있는 선택" 최소 1개 — `ensemble.yaml` L30
4. **전개 밀도 (Event Density)**: "매 화 최소 1건의 상황 변화" — `ensemble.yaml` L31
5. **공간 다양성**: 단일 장소 3화 이상 연속 금지 — `ensemble.yaml` L34
6. **인물 배치**: 주인공 혼자 등장 2화 이상 연속 금지 — `ensemble.yaml` L35

This proves the arc layer already has **vocabulary and enforcement patterns** for distributing narrative properties across episodes. But "admiration mode" is entirely absent from this vocabulary.

### 2.3 What Is NOT At The Arc Level

1. **No admiration mode field** — no way to specify whether this arc's protagonist high-evaluation comes from method/risk/judgment/information asymmetry/social shock
2. **No evaluation type rotation tracking** — no history of which admiration mode was used in prior arcs, so rotation can't be enforced
3. **No observer reaction allocation** — who witnesses the protagonist's achievement and from what angle is not pre-planned at arc level
4. **No reveal ordering** — when information asymmetry is deployed within an arc is not pre-designed
5. **No differentiation between numeric praise and structural praise** — `side_glimpse` is one preset with no mode variants; the arc can't tell blueprint to use "quiet fear from an informed observer" vs "social hierarchy shock"

## 3. The Core Problem at Arc Level

The current system conflates "protagonist feels good" with "protagonist is evaluated highly by the narrative."

- `satisfaction_score` measures reader catharsis intensity (1-10) — but a score of 9 from "earned $10 billion" and a score of 9 from "solved an unsolvable strategic puzzle with minimal resources" are indistinguishable.
- `protagonist_agency = 자력` tells us the protagonist solved it alone — but not whether the achievement was impressive because of method, risk, insight, or social impact.
- `hybrid_composition.primary` labels the narrative pattern (e.g., "투자 전략 서사") — but not what makes the protagonist's role in that pattern admirable.

In business-power / chaebol fiction specifically:
- "Big number → wow" is the default mode because the system has no alternative vocabulary
- The arc prompt demands "의미 있는 선택" (meaningful choice) and "갈등 구조" (conflict structure), which are necessary but not sufficient for differentiated admiration
- The treatment's `genre_ext` tracks capital progression numerically, which further biases toward numeric evaluation

## 4. Candidate Admiration Mode Taxonomy (Arc-Level)

If the arc layer were to distribute admiration modes, what would the modes be? Based on the master order's examples and the genres this system supports:

| Mode Label | Core Mechanism | When It Works Best | Genre Affinity |
|-----------|---------------|-------------------|----------------|
| **조건부 승리** (Conditional Victory) | Small resources, impossible method — the HOW matters more than the WHAT | Resource-constrained arcs, early-stage protagonist | Investment, Hunter |
| **출발점 역전** (Starting Point Reversal) | Underestimated starting point → outsized leverage — the GAP matters | Arc transitions, status change arcs | Chaebol, Investment |
| **위계 충격** (Hierarchy Shock) | Social hierarchy violated — people who "should" be above protagonist are below | Confrontation arcs, power structure arcs | Chaebol, Wuxia |
| **정보 공포** (Information Fear) | Only informed observers understand the danger/value — uninformed characters misread | Multi-POV arcs, reveal arcs | All genres |
| **판단 정밀도** (Judgment Precision) | Protagonist's analytical precision is the weapon — others see the result but not the reasoning | Strategy arcs, planning arcs | Investment, Chaebol |
| **리스크 흡수** (Risk Absorption) | Protagonist takes catastrophic risk that others won't touch — the courage is the admiration | Crisis arcs, bet-everything arcs | Investment, Hunter, Wuxia |

These are not exclusive — an arc could use a primary + secondary mode (analogous to `hybrid_composition`). But currently the system has no field to carry this.

## 5. Owner Mapping

### 5.1 What Arc Should Own

The arc is the **distribution layer** — it should own:

1. **Admiration mode selection per arc**: Which 1-2 modes from the taxonomy are active in this arc
2. **Rotation enforcement**: "연속 2 Arc 이상 같은 admiration mode 금지" (analogous to the 감정 곡선 rule)
3. **Observer role allocation**: Which NPC class or external entity is the evaluation source in this arc (peer/superior/subordinate/uninformed outsider)
4. **Reveal timing placement**: At which episode within the arc does the information gap resolve or the admiration peak land

### 5.2 What Arc Should NOT Own

The arc should not own:

1. **Admiration mode definitions** — what each mode means, what constitutes low-quality praise, what's banned → this is bible/worldview territory
2. **Scene-level staging** — POV switch timing, specific observer reaction shots, information gap execution → this is blueprint territory
3. **Prose-level execution** — dialogue understatement, reaction-shot pacing, "few characters understand, many misread" structures → this is manuscript territory

### 5.3 Where This Should Live in the Arc Schema

The most natural insertion point is alongside `hybrid_composition`, because:
- `hybrid_composition` already carries `primary`, `secondary`, `mixing_logic`
- An `admiration_design` or `evaluation_staging` field would follow the same pattern
- The arc prompt already teaches the LLM this primary/secondary/mixing vocabulary

Candidate schema shape (design-level only, not implementation):

```
"admiration_design": {
    "primary_mode": "조건부 승리 | 출발점 역전 | 위계 충격 | 정보 공포 | 판단 정밀도 | 리스크 흡수",
    "secondary_mode": "optional — 보조 감탄 축",
    "observer_class": "동료 | 상위자 | 하위자 | 외부인 | 정보약자",
    "peak_episode": N,
    "mode_reasoning": "왜 이 감탄 모드를 선택했는지"
}
```

This is a **design recommendation**, not a code change order.

## 6. Interaction With Existing Systems

### 6.1 satisfaction_score

If `admiration_design` exists at arc level, `satisfaction_score` remains useful as the intensity measure. The difference:
- `satisfaction_score = 9` + `admiration_design.primary_mode = 조건부 승리` → blueprint knows to stage "small resource, clever method" scenes
- `satisfaction_score = 9` + `admiration_design.primary_mode = 위계 충격` → blueprint knows to stage "social hierarchy violation" scenes
- Currently, `satisfaction_score = 9` alone → blueprint defaults to whatever the LLM improvises, which trends toward numeric praise

### 6.2 hybrid_composition

`hybrid_composition` and `admiration_design` are complementary, not redundant:
- `hybrid_composition` describes the NARRATIVE PATTERN (what kind of story structure)
- `admiration_design` describes the EVALUATION PATTERN (what makes the protagonist impressive in this arc)
- A "투자 전략 서사" (`hybrid_composition.primary`) could be staged as "조건부 승리" (small bet, impossible method) or "리스크 흡수" (catastrophic risk that pays off) — these produce very different blueprints

### 6.3 감정 곡선 Rule

The existing "연속 3화 이상 같은 감정 톤 금지" rule is a precedent for rotation enforcement. An analogous "연속 2 Arc 이상 같은 primary admiration mode 금지" rule would fit the same enforcement pattern. This is already wired into the arc prompt template structure.

### 6.4 side_glimpse Preset

The blueprint-level `side_glimpse` scene preset ("조연 시점 전환 — '저 사람 대단해!' 반응") is the current undifferentiated admiration device. If the arc specifies `admiration_design`, blueprint can differentiate side_glimpse into variants:
- `side_glimpse + 정보 공포` → observer realizes something terrifying that others don't see
- `side_glimpse + 위계 충격` → observer from a higher social class is forced to acknowledge protagonist
- `side_glimpse + 판단 정밀도` → observer traces back protagonist's decision chain and sees the precision

Without arc-level mode selection, this differentiation can't happen — blueprint has no upstream signal.

## 7. Tradeoff Notes

### 7.1 Arc-Level vs Per-Episode

Should admiration mode be set per-arc or per-episode?

**Per-arc** (recommended):
- Simpler schema, aligns with existing arc-level beat distribution
- Admiration mode is a strategic choice that should span multiple episodes (setup → reveal → reaction)
- Allows rotation enforcement at a manageable granularity

**Per-episode** (not recommended):
- Too granular — admiration mode needs setup time across episodes
- Would bloat `episode_details` or require a new per-episode field
- Rotation at per-episode level is too noisy to be meaningful

### 7.2 Mandatory vs Advisory

Should the LLM be required to fill `admiration_design`, or is it advisory?

**Recommendation: mandatory primary_mode, optional secondary/observer fields.**
- Primary mode is needed for downstream blueprint differentiation — without it, the field adds no value
- Secondary mode and observer_class are useful but can be left to blueprint's discretion
- `mode_reasoning` should be mandatory for the same reason `ep_count_reasoning` is mandatory — it forces the LLM to justify its choice

### 7.3 Token Cost

Adding `admiration_design` to the arc prompt schema adds ~100-150 tokens to the prompt template, and ~50-100 tokens to each candidate output. With 3 candidates per arc generation, total cost: ~250-450 extra tokens per arc. Minimal impact.

## 8. What Arc Cannot Do Alone

Even with `admiration_design`, the arc layer cannot:

1. **Define what "low-quality praise" means** — the arc LLM needs upstream principles from bible/worldview to know that "big number → wow" is banned or disfavored. Without this, the LLM will still default to numeric praise even if told to use "조건부 승리" mode, because it has no definition of what "조건부 승리" actually looks like vs what it should avoid.

2. **Stage the scene mechanics** — arc can say "이 Arc의 감탄 축은 정보 공포" but cannot specify POV switch timing, observer reaction shot placement, or information gap reveal ordering. That's blueprint territory.

3. **Execute prose-level tone** — "quiet fear from an informed observer" requires specific prose techniques (understatement, delayed reaction, indirect dialogue) that arc-level planning is too coarse to specify.

This makes arc the **secondary owner**, not the authoritative owner.

## 9. Confidence And Limits

Estimated confidence: 96%

Why this clears the 95% gate:
- All claims backed by live code/prompt evidence (file:line references)
- The absence of admiration mode vocabulary is structural and unambiguous (zero fields, zero prompt references)
- The existing beat distribution infrastructure (감정 곡선, 반전 포인트, etc.) proves the arc layer can carry this type of property
- The interaction analysis with satisfaction_score, hybrid_composition, and side_glimpse is grounded in actual schema and preset evidence

Limits:
- The 6-mode taxonomy is a design proposal, not validated against live generation
- Whether rotation enforcement improves output quality vs adding complexity is untested
- The optimal relationship between bible-defined principles and arc-level mode selection requires T1 survey findings to fully resolve

## 10. Final Lines

- Authoritative owner in this lane: **secondary owner** — arc distributes admiration modes but does not define them
- Best bounded next wave from this lane: **admiration mode schema design at arc level, after bible principles are defined** — analogous to how `hybrid_composition` was added alongside existing arc fields
- Should Codex open an execution SSOT from this lane now: **no** — this lane depends on T1 (bible principles) being resolved first, and the current priority wave (authority re-banding + density prevalidation) should close before adding new arc schema fields
