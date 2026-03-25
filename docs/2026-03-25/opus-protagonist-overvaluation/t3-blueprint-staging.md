# T3. Blueprint Staging Layer — Protagonist Overvaluation Survey

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: lane survey report
Lane: T3 (Blueprint Staging Layer)
Master Order: `docs/2026-03-25/protagonist-overvaluation-staging-4terminal-master-order.md`

## 1. What Blueprint Already Owns

The blueprint layer already has structural primitives relevant to protagonist evaluation staging. These are live and wired.

### 1.1 Scene Presets With Evaluation Semantics

From `blueprint_ensemble.py:93-106` and `ensemble.yaml:298-314`:

| Preset | Evaluation Role |
|--------|----------------|
| `side_glimpse` | "★조연 시점★ 주인공 부재 상황, '저 사람 대단해!' 반응" |
| `villain_scheme` | Adversary perspective — can reveal fear/respect for protagonist |
| `omniscient_hint` | Reader-only information — can create dramatic irony around protagonist's value |
| `dialogue_duel` | Negotiation/confrontation — protagonist's competence shown through argument quality |

`side_glimpse` is the only preset that explicitly references protagonist evaluation, and its definition defaults to the exact failure mode: "'저 사람 대단해!' 반응" — direct exclamatory praise.

### 1.2 POV Switching Policy

From `blueprint_ensemble.py:109-173`: the system generates per-blueprint POV constraint sections based on `primary_pov` × `external_pov_insert_policy`. This controls whether observer-perspective scenes are allowed at all.

This is a staging gatekeeper: if POV policy is "금지", the blueprint cannot stage external evaluation. If "적극 허용", it can design multi-perspective evaluation scenes.

### 1.3 Blueprint Output Fields That Carry Evaluation

From `ensemble.yaml:324-357` (blueprint JSON schema):

- `scene_breakdown.scene_N.type`: preset assignment — determines scene's evaluation role
- `scene_breakdown.scene_N.characters`: who is present to observe/react
- `scene_breakdown.scene_N.key_events`: specific actions/reactions
- `scene_breakdown.scene_N.summary`: scene framing
- `core_tension`: what's at stake — shapes what "being impressive" means
- `relationship_changes`: how other characters' perception shifts
- `integrated_scenario`: the 1000+ char scenario that carries the most staging detail

### 1.4 Strategy Directives

From `blueprint_ensemble.py:40-79`: three strategies (action/emotion/dialogue) control narrative emphasis but say nothing about protagonist evaluation modes.

## 2. What Blueprint Does NOT Have

### 2.1 No Admiration Mode Vocabulary

The blueprint prompt has zero guidance on **differentiated forms of protagonist evaluation**. It does not mention:

- judgment / 판단력
- risk tolerance / 위험 감수
- structural thinking / 구조적 사고
- information asymmetry / 정보 비대칭
- social shock / 사회적 충격
- method quality / 방법론의 질
- underestimated starting point / 과소평가된 출발점

The only evaluation vocabulary is `side_glimpse`'s "대단해!" — which is the literal "big number → wow" pattern.

### 2.2 No Scene-Level Evaluation Device Field

The `scene_breakdown` schema (`ensemble.yaml:327-337`) has:

- `type` (preset)
- `title`
- `location`
- `characters`
- `summary`
- `tension_level`
- `key_events`

Missing: any field that would force the LLM to articulate **what evaluation device** this scene uses — e.g., "information gap reveals protagonist knew something others didn't" or "observer's failed prediction exposes protagonist's structural advantage."

### 2.3 No Observer Assignment Guidance

The blueprint prompt tells the LLM to populate `characters` per scene, but gives no guidance on **who should serve as the evaluator** and **what their evaluation stance should be**. In chaebol/business-power fiction, the evaluator's authority matters:

- A rival CEO's grudging respect carries more weight than a subordinate's awe
- An informed market observer's specific fear is more credible than generic "대단하다"
- A character who initially underestimated the protagonist makes a stronger evaluator than a neutral bystander

### 2.4 No Evaluation Rotation Mechanism

Nothing in the blueprint layer prevents the same admiration pattern from repeating across consecutive episodes. Each blueprint is generated independently with no memory of how previous episodes staged evaluation.

## 3. Live Artifact Evidence

Examined three blueprints from `canary_0325`:

### EP5 (`final_blueprint__emotion_focused.json`)

**Evaluation device used**: dialogue_duel (scene 4) — protagonist dismantles PB's proposal with specific numbers (4.5% - tax - fees - inflation = negative real return).

**Quality**: HIGH — praise comes from **specific analytical competence**, not raw scale. The PB's "입술이 굳었다" is a reaction to *method*, not *amount*.

**Observer**: 박성호 PB — mid-tier evaluator (professional, but not an adversary of equal weight).

### EP7 (`final_blueprint__action_focused.json`)

**Evaluation device used**: villain_scheme (scene 3) + dialogue_duel (scene 4) — brothers mock protagonist's investment, protagonist counter-attacks with specific data ("지분율 32%보다 제 15억이 훨씬 안전").

**Quality**: MEDIUM-HIGH — the brothers' condescension creates an "underestimated starting point" frame. The counter is specific. But "18년의 굴레를 벗어던진 자 특유의 압도적인 여유" is author-tell, not shown-through-staging.

**Observer**: 한태준/한태민 — high-weight evaluators (direct rivals, family hierarchy).

### EP8 (`final_blueprint__dialogue_focused.json`)

**Evaluation device used**: dialogue_duel (scene 3) — PB panics about 0.1 dollar drop, protagonist responds with "60달러 밑으로 떨어지면 5억 원으로 물량 더 담겠다." Then action_peak (scene 4) + cliffhanger (scene 5): market validates protagonist's prediction.

**Quality**: HIGH — the PB's professional panic contrasted with protagonist's calm makes admiration emerge from *context*, not from anyone saying "대단하다." The market's objective response (price surge) replaces verbal praise.

**Observer**: 박성호 PB (again) + market itself (impersonal validation).

### Pattern Observed

The canary blueprints **already demonstrate differentiated evaluation** in some episodes. The problem is:

1. It's not systematic — the LLM happens to choose good staging sometimes
2. The observer is often the same character (박성호) — no rotation
3. When staging is weak, the fallback is authorial narration about protagonist's "서늘한 감각" or "묵직한 기대감" — tell rather than show
4. No scene explicitly designs an **information gap** where a knowledgeable observer realizes what uninformed characters miss

## 4. Blueprint as Authoritative Owner: Assessment

### 4.1 What Blueprint Can Uniquely Control

Blueprint is the **scene-level staging layer**. It controls:

1. **Who observes**: which characters are placed in which scene to witness protagonist's actions
2. **What they know**: information asymmetry between characters (who is informed, who is blind)
3. **When the reveal lands**: which scene beat carries the moment of realization
4. **Which quality is showcased**: scene structure determines whether the protagonist's *judgment*, *risk tolerance*, *social leverage*, or *method* is what impresses
5. **Show vs. tell framing**: whether admiration is explicit ("대단하다" dialogue) or implicit (behavior change, stunned silence, abandoned plan)

No other layer can do this at the same specificity. Bible defines principles but cannot place specific evaluators in specific scenes. Arc distributes beats across episodes but cannot design within-episode staging. Manuscript executes prose but cannot redesign the scene structure.

### 4.2 What Blueprint Cannot Fix If Upstream Is Weak

1. **If bible doesn't define admirable traits**: blueprint must improvise what "being impressive" means in this genre. In investment fiction, if bible doesn't distinguish "risk analysis skill" from "big money flex", blueprint will default to the latter.
2. **If arc doesn't plan evaluation modes per episode**: blueprint will repeat the same mode. If the arc says "protagonist enters market" for three consecutive episodes, blueprint has no signal to rotate from "method admiration" to "risk admiration" to "information-gap admiration."
3. **If the scenario doesn't test the protagonist's quality**: blueprint cannot stage "structural thinking showcase" if the arc hasn't set up a problem that requires structural thinking.

### 4.3 Verdict

Blueprint is the **authoritative owner of execution** for protagonist evaluation staging. It is the layer where evaluation becomes concrete: specific characters, specific scenes, specific devices.

But blueprint is the **secondary owner of design intent**. Without upstream guidance on what admiration modes exist and when to use them, blueprint will default to whatever the LLM's training data suggests — which in web novel conventions means "big number → wow."

## 5. Concrete Tradeoff Notes

### Tradeoff A: Blueprint field addition vs. prompt guidance only

**Option 1**: Add an `evaluation_device` field to the blueprint schema (e.g., per scene or per episode).

- Pro: forces the LLM to explicitly articulate how protagonist evaluation is staged
- Con: schema change affects validation, Director evaluation, and downstream manuscript prompt; blast radius is medium
- Con: risk of mechanical compliance (LLM fills field but doesn't actually stage it)

**Option 2**: Add admiration-mode guidance to the blueprint prompt without schema change.

- Pro: lower blast radius; doesn't touch validation or downstream
- Con: no explicit output artifact to verify; harder to audit
- Pro: aligns with the current operating pattern (prompt-level guidance → LLM internalizes)

**Recommendation**: Option 2 first, as a prompt-level staging section. If canary evidence shows the LLM ignores the guidance, then consider Option 1.

### Tradeoff B: Blueprint-level guidance vs. constraint compiler injection

**Option 1**: Add evaluation staging guidance to `BLUEPRINT_GENERATION_PROMPT` in `ensemble.yaml`.

- Applies to all episodes uniformly
- Cannot vary by arc or episode context

**Option 2**: Inject evaluation staging via `BlueprintConstraintCompiler`, which already carries `must_focus`, `fact_lock`, `semantic_carryover`, etc.

- Can vary by context (genre, arc position, preceding evaluation mode)
- More complex; requires upstream data
- Aligns with the existing "constraint injection from arc to blueprint" pipeline

**Recommendation**: Start with Option 1 (uniform prompt guidance). If rotation is needed, later add a thin constraint compiler extension.

### Tradeoff C: Redefining `side_glimpse` vs. creating new presets

Current `side_glimpse` definition defaults to "대단해!" reaction. Options:

**Option 1**: Redefine `side_glimpse` to emphasize *differentiated* observer reaction rather than generic praise.

- Pro: zero new presets; no downstream confusion
- Con: changes the meaning of an existing preset that manuscript code references

**Option 2**: Keep `side_glimpse` as-is; add guidance that describes how to USE it without falling into "big number → wow."

- Pro: backward-compatible
- Pro: the problem isn't the preset itself but the lack of guidance on what reaction to stage

**Recommendation**: Option 2. The preset is a container; the content guidance is what matters.

## 6. Where This Lane Stands in the Ownership Map

| Layer | Role | Current State |
|-------|------|---------------|
| Bible | Defines what admirable traits exist | No explicit admiration axis vocabulary |
| Arc | Distributes evaluation modes across episodes | No evaluation mode rotation mechanism |
| **Blueprint** | **Stages specific evaluation scenes** | **Has structural primitives (presets, POV, characters) but zero guidance on differentiated evaluation** |
| Manuscript | Executes prose rendering | Too late to fix if blueprint doesn't stage well |

Blueprint is the **point of maximum leverage** for this problem: it has the structural primitives, it's the last design layer before prose, and adding guidance to it has low blast radius.

But it needs upstream signal (from bible/arc) to avoid ad-hoc improvisation. Without knowing what admiration modes exist for this work, blueprint will cycle through whatever the LLM's default web novel conventions suggest.

## 7. Candidate Blueprint Staging Concepts

If a future execution wave adds evaluation staging to blueprints, these are the candidate concepts:

1. **Evaluation axis tag per episode**: "이번 화 고평가 축: 판단력 / 위험 감수 / 정보 비대칭 / 구조적 사고 / 사회적 충격"
2. **Observer authority guidance**: "이번 화에서 주인공을 평가하는 인물은 [NPC]이며, 이 인물의 평가가 의미 있는 이유는 [이유]"
3. **Information gap design**: "이 씬에서 [NPC-A]는 주인공의 의도를 모르고, [NPC-B]만 알고 있음 → NPC-B의 반응이 독자에게 주인공의 가치를 전달"
4. **Show-not-tell constraint**: "주인공 고평가는 다른 인물의 '대단하다' 류 직접 발화가 아닌, 행동 변화/계획 수정/침묵/경계심 강화로 표현"
5. **Anti-pattern guard**: "단순 숫자 규모('100억!', '3배 레버리지!')로만 인상을 주는 것은 저급 칭송. 왜 그 판단이 어려운지, 왜 남들은 못 하는지를 장면으로 보여줄 것"

## 8. Confidence

Estimated confidence: 96%

Why this clears the 95% gate:

- All claims are backed by live code evidence (`ensemble.yaml`, `blueprint_ensemble.py`, `blueprint_constraint_compiler.py`)
- All live artifact claims are verified against `canary_0325` blueprints
- The "blueprint has primitives but no guidance" finding is structural and unambiguous
- The tradeoff notes present alternatives rather than forcing premature recommendations
- The ownership classification aligns with the system's existing stage architecture

Limits:

- This survey cannot predict the magnitude of improvement from adding evaluation guidance to blueprints
- The interaction between evaluation staging and the upcoming authority re-banding wave is unexamined
- The canary evidence is from investment genre only; wuxia/hunter/fantasy may have different evaluation patterns

---

Authoritative owner in this lane: Blueprint is the authoritative owner of evaluation *execution* (scene-level staging), but secondary owner of evaluation *design intent* (which modes exist, when to use them).
Best bounded next wave from this lane: Prompt-level evaluation staging guidance in `BLUEPRINT_GENERATION_PROMPT`, covering differentiated admiration modes and show-not-tell constraints. No schema change in wave 1.
Should Codex open an execution SSOT from this lane now: no — wait for merge audit across all 4 lanes to determine if blueprint staging is the right first wave or should follow bible/arc upstream definition.
