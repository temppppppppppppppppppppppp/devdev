# T1. Bible / Worldview Layer — Protagonist Overvaluation Owner Mapping

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: lane survey report
Canonical Path: `docs/2026-03-25/opus-protagonist-overvaluation/t1-bible-owner-mapping.md`
Source Order: `docs/2026-03-25/protagonist-overvaluation-staging-4terminal-master-order.md` (Lane T1)
Related Docs:
- `docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md`
- `docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md`

---

## 1. Survey Intent

Investigate whether **bible / worldview** is the right authoritative owner for protagonist high-evaluation (`주인공 고평가`) design — specifically the problem that current evaluation collapses into `big number → wow`, which becomes thin or awkward in upper-class / chaebol / business-power fiction.

## 2. Current State of the Bible Layer

### 2.1 What the bible layer currently owns

The bible/worldview layer is distributed across several systems:

**A. WorldStateManager** (`modules/core/world_state.py:90-113`)
- Tracks protagonist state: `name`, `location`, `assets`, `injuries`, `skills`
- Tracks NPC states, relationships, active plots, pressure vectors, world laws, motivations, promises
- **No praise-axis field exists.** The protagonist sub-object is purely physical/material state.
- `world_laws` is the closest structural slot (list of `{law, established_ep}`), but it tracks physics-level rules, not evaluation-design rules.

**B. PresetRegistry** (`modules/core/stage0/preset_registry.py:31-63`)
- Common fields: `name`, `age`, `goal`, `current_objective`, `relationships`, `location`, `reputation`, `secrets`, `injuries`
- Investment genre fields: `capital`, `liquid_cash`, `portfolio`, `network_level`, `investment_style`, `risk_tolerance`
- **`reputation` is a dict** — this is the closest structural slot to "how the world sees the protagonist." Currently populated as a raw dict with no schema for praise-axis typing.

**C. Genre Guard YAML** (`config/genres/investment.yaml:83-96`)
- `wealth_hierarchy`: 7-tier scale from 무일푼 to 글로벌재벌
- `wealth_action_limits`: guards what a protagonist at each wealth tier can plausibly do
- `realistic_return_rates`: plausible ranges per asset class (주식 max 100%/yr, 벤처투자 max 1000%/yr)
- **These are numeric realism guards, not praise-design rules.** They prevent impossible numbers, but do not define *how praise should feel at each tier.*

**D. WorkGuard work_identity** (`modules/core/genre_guards/work_guard.py:32-40`)
- `business_axes`: work-specific business evaluation axes
- `control_axes`: work-specific control/influence axes
- `forbidden_flattenings`: anti-patterns for generic/thin portrayal
- `mandatory_scene_engines`: required scene types (협상, 실사, IR 등)
- `mandatory_lexicon`: required vocabulary
- **`business_axes` and `control_axes` are the closest existing slots to praise-axis design**, but they are currently list[str] with no structured definition of what "good praise" looks like per axis.

**E. FactLedger** (`modules/core/fact_ledger.py`)
- Tracks numeric facts: `{value, unit, last_ep, established_value, established_ep}`
- **Purely forensic.** Records what happened, not what should be admired about it.

### 2.2 What the bible layer does NOT currently own

The bible layer has **no structured concept of**:

1. **Praise axes** — no schema defines what dimensions of protagonist competence are admirable in this work
2. **Praise quality rules** — no bible-level rule distinguishes "shallow wow" from "layered recognition"
3. **Admiration mode catalog** — no worldview document defines the available modes of protagonist-evaluation staging
4. **Observer competence tiers** — no bible-level schema defines which NPCs are competent enough to evaluate the protagonist meaningfully, and which NPCs exist to misread the situation
5. **Information-gap design vocabulary** — no worldview document defines what the protagonist knows that others don't, and how that gap creates admiration vs. mere surprise

### 2.3 Where does praise currently live?

Scattered across non-bible layers:

| Current location | What it does | Evidence |
|---|---|---|
| `ensemble.yaml:310` | `side_glimpse` preset — "조연 시점 주인공 칭송/반응" | Blueprint scene type, not bible rule |
| `analyst.yaml:176` | "조연 반응 (150자+): 주인공을 향한 세상의 오해, 경악, 착각" | Volume planning field, not bible rule |
| `director.yaml:122` | "전문가 반응 비례성" — VIP PB가 20억에 놀람→잘못, 3배 레버리지에 놀람→맞음 | Director evaluation criterion, not bible rule |
| `chief_writer.yaml:172-179` | D-Step2 독자 대리만족 — payoff, frustration-reward, growth perception | Manuscript writing guidance, not bible rule |
| `catharsis_timer.py:22-133` | Catharsis keyword weights — 감탄(1.0), 인정(1.0), 경악(1.0), 통쾌(1.0) | Python validation, not bible rule |
| WorkGuard `forbidden_flattenings` | Prevents generic flattening to "수익률/지표/M&A" language | Work-specific guard, not bible-level design |

**Key finding**: The system has rich machinery for *detecting* thin praise and *executing* reactions, but no bible-level authority that *defines* what praise should be.

## 3. Analysis: Should Bible Be The Authoritative Owner?

### 3.1 The case FOR bible as authoritative owner

**Strongest argument**: Praise-axis definitions are worldview-level facts.

In a chaebol/business-power work:
- "20억에 놀라는 VIP PB" is already detected as wrong (`director.yaml:122`)
- But the *reason* it's wrong is worldview-level: in this world, 20억 is routine for the class of people involved
- The Director currently enforces this, but the rule should originate from the bible

What the bible could define that no other layer can:

1. **Praise axes** — "In this work, admiration comes from: (a) information asymmetry exploitation, (b) structural positioning speed, (c) risk-sizing under pressure, (d) social hierarchy disruption"
2. **Threshold rules** — "A 100억 trade is routine; what matters is the *method*, the *timing*, and *who notices*"
3. **Observer competence map** — "Character X is an industry insider who should not be impressed by routine trades; Character Y is an outsider who can legitimately be shocked by scale"
4. **Forbidden praise patterns** — "Do not use raw number size as the primary source of admiration. Do not have all observers react uniformly."

These are worldview facts, not staging decisions. They don't change from episode to episode. They are the *constants* against which all downstream staging is measured.

### 3.2 The case AGAINST bible as sole authoritative owner

**Key limitation**: Bible can define *what* should be admired, but cannot stage *how* to deliver it.

Bible cannot own:
- POV switch timing (blueprint)
- Observer reaction pacing (blueprint/manuscript)
- Information-gap reveal ordering (blueprint)
- "Only one character understands" scene construction (blueprint)
- Tone/understatement in prose (manuscript)

Bible also cannot own:
- Arc-level admiration mode rotation ("this arc: quiet fear; next arc: public shock")
- That belongs to arc distribution (T2 lane)

### 3.3 Resolution: Bible is the authoritative definition owner, not the execution owner

The analogy:

| | Bible (worldview) | Arc | Blueprint | Manuscript |
|---|---|---|---|---|
| Praise axes | **defines** | distributes across arcs | stages in scenes | executes in prose |
| Observer competence | **defines** | assigns per arc | places in scenes | renders reactions |
| Threshold rules | **defines** | applies per arc context | enforces per scene | maintains in dialogue |
| Forbidden patterns | **defines** | inherits | inherits + adapts | inherits |

Bible is the **constitutional** layer — it says what the law is. Blueprint is the **staging** layer — it says how to enforce it in a specific episode. Manuscript is the **execution** layer — it renders it into prose.

## 4. What Bible Should Define (Recommended Schema)

### 4.1 Praise Axis Catalog

A bible-level YAML or JSON section defining the work's admiration dimensions:

```yaml
protagonist_evaluation:
  praise_axes:
    - axis: "정보 비대칭 활용"
      description: "남들이 모르는 정보를 확보하고, 그 정보로 결정적 순간에 행동하는 능력"
      high_quality_signals: ["소수만 이해하는 반응", "사후 발각 시 충격", "침묵 속 행동"]
      low_quality_signals: ["모든 관찰자가 동시에 감탄", "숫자 크기만으로 놀람", "해설자가 설명"]
    - axis: "구조적 사고력"
      description: "개별 거래가 아닌 전체 구조를 설계하는 능력"
      high_quality_signals: ["나중에야 전체 그림이 보임", "한 수가 세 수 뒤를 의미"]
      low_quality_signals: ["직접 설명", "독백으로 전략 해설"]
    - axis: "위험 감수와 배짱"
      description: "계산된 위험을 감수할 때 드러나는 담력과 판단력"
      high_quality_signals: ["전문가가 겁먹는 상황에서의 냉정함", "리스크를 즐기는 게 아니라 관리하는 모습"]
      low_quality_signals: ["무모한 도박이 성공", "결과만으로 칭찬"]
    - axis: "사회적 파장"
      description: "행동의 결과가 사회 구조에 미치는 충격파"
      high_quality_signals: ["간접적 파급 효과", "본인은 모르지만 세상이 바뀌기 시작", "시간차 인지"]
      low_quality_signals: ["뉴스 속보 + 감탄 대사", "모두가 동시에 놀람"]
```

### 4.2 Observer Competence Tiers

```yaml
  observer_tiers:
    - tier: "informed_insider"
      description: "업계 전문가, 주인공의 행동을 정확히 평가할 수 있는 인물"
      praise_pattern: "놀라지 않아야 할 것에 놀라지 않고, 진짜 놀라운 것에만 반응"
      example: "VIP PB가 20억 거래에는 덤덤, 3배 레버리지 타이밍에 소름"
    - tier: "partial_observer"
      description: "일부만 아는 인물 — 결과는 보지만 방법을 모르는 관찰자"
      praise_pattern: "규모에 놀라지만 진짜 이유를 모름 — 나중에 깨달을 때 2차 충격"
    - tier: "outsider"
      description: "업계 밖 인물 — 표면적 결과만 인지"
      praise_pattern: "숫자에 놀라는 것이 자연스럽지만, 이 반응이 주요 감탄 장치가 되면 안 됨"
    - tier: "antagonist"
      description: "적대자 — 주인공을 과소평가했다가 인정하거나 두려워하게 되는 인물"
      praise_pattern: "최초 경멸 → 불안 → 인정 or 공포 (단계적 변화만 유효)"
```

### 4.3 Forbidden Praise Patterns (Bible-Level)

```yaml
  forbidden_praise_patterns:
    - pattern: "big_number_wow"
      description: "숫자 크기 자체가 감탄의 주된 근거"
      example_bad: "'100억 수익이라니!' 하며 모든 인물이 경악"
      why_bad: "금액은 조건이지 방법이 아님. 업계인이 금액에만 놀라면 세계관 파괴."
    - pattern: "uniform_reaction"
      description: "모든 관찰자가 동일한 타이밍에 동일한 강도로 반응"
      example_bad: "회의실의 모든 사람이 숨을 죽이며 '대단하다' 연발"
      why_bad: "관찰자마다 이해 수준이 다르므로, 반응의 시차와 깊이도 달라야 함"
    - pattern: "narrator_hype"
      description: "서술자가 직접 주인공의 대단함을 해설"
      example_bad: "그의 판단은 누구도 따라올 수 없는 수준이었다."
      why_bad: "보여주기(show)가 아닌 알려주기(tell). 독자가 스스로 판단할 여지를 빼앗음."
    - pattern: "instant_recognition"
      description: "주인공의 능력이 행동 직후 즉시 인정됨"
      example_bad: "거래가 체결되자마자 '천재다' '전설이다' 반응"
      why_bad: "시간차 없는 인정은 독자의 '내가 먼저 알아챘다' 쾌감을 빼앗음"
```

### 4.4 Threshold Context Rules

```yaml
  evaluation_thresholds:
    - rule: "금액 자체는 감탄 근거가 아니다"
      detail: "이 작품의 세계에서 10억은 시작 자본이고, 100억은 중간 규모 거래다. 감탄은 금액이 아니라 방법·타이밍·구조에서 나와야 한다."
    - rule: "경지/레벨 자체는 감탄 근거가 아니다"
      detail: "무협/헌터에서 경지 돌파는 결과이지 감탄 대상이 아니다. 돌파 과정의 조건·위험·비용이 감탄 대상이다."
    - rule: "전문가 반응 비례성"
      detail: "해당 분야 전문가는 일상적 수준의 성과에 놀라지 않는다. 놀라려면 그 전문가의 기준에서 비상식적인 요소가 있어야 한다."
```

## 5. Owner Classification

### 5.1 Bible as authoritative owner: YES, for praise-axis definition

Bible should be the single source of truth for:
- What axes of competence deserve admiration in this work
- What observer competence tiers exist and how each tier should react differently
- What praise patterns are forbidden (bible-level, not per-episode)
- What threshold context makes certain reactions valid or invalid

Bible should NOT own:
- How to distribute admiration beats across arcs (→ arc distribution)
- How to stage specific scenes for admiration (→ blueprint)
- How to render reactions in prose (→ manuscript)

### 5.2 Relationship to existing systems

| Existing system | Current role | Proposed relationship to bible praise-axes |
|---|---|---|
| WorkGuard `business_axes` | Unstructured list of business evaluation axes | Should be populated FROM bible praise-axis catalog |
| WorkGuard `forbidden_flattenings` | Generic flattening detection | Should be supplemented by bible forbidden-praise patterns |
| Director `전문가 반응 비례성` | Director-level eval criterion | Correct enforcement point; should reference bible threshold rules |
| `side_glimpse` preset | Blueprint scene type for observer reactions | Correct staging tool; should reference bible observer-tier rules |
| `analyst.yaml` `조연 반응` | Volume planning slot | Correct planning tool; should reference bible praise-axis catalog |
| `catharsis_timer.py` | Python keyword detection | Python-only validation; does not need bible reference (too late) |

### 5.3 What bible does NOT need to own

- **Scene construction patterns** — "only one character realizes" is a blueprint device, not a worldview fact
- **POV switch mechanics** — staging tool, not worldview rule
- **Emotional pacing** — arc/blueprint concern
- **Prose tone** — manuscript concern

## 6. Tradeoff Notes

### 6.1 Risk: bible bloat

Adding praise-axis schema to the bible increases the context size for all downstream stages. Mitigation: keep the schema compact (top-level axes only, no scene-level instructions) and surface it selectively (e.g., WorkGuard already has `business_axes` — upgrade the schema, don't duplicate the surface).

### 6.2 Risk: premature precision

Defining praise axes at bible level before the system has enough live-run evidence of what works may lock in untested axioms. Mitigation: treat the initial praise-axis catalog as advisory (surfaced to Director and Blueprint, not hard-gated by Python). Upgrade to hard constraints only after canary validation.

### 6.3 Risk: enforcement gap

Bible can define praise rules, but if blueprint/manuscript don't receive them, they're dead code. Mitigation: wire bible praise-axes through the same path as existing WorkGuard fields — WorkGuard already flows into Director and blueprint prompts.

### 6.4 Benefit: single source of truth for "what counts as good praise"

Currently the `전문가 반응 비례성` rule lives in director.yaml, the `side_glimpse` pattern lives in ensemble.yaml, and the `조연 반응` requirement lives in analyst.yaml. These are all enforcement points for the same underlying worldview rule. A bible-level praise-axis catalog would unify the source.

## 7. Confidence

Estimated confidence: 96%

Why this clears the 95% gate:
- All claims are backed by live code/config evidence (file:line references)
- The structural gap (no bible-level praise-axis schema) is unambiguous — zero fields exist
- The owner classification (bible = definition, blueprint = staging, manuscript = execution) is consistent with the existing system's authority hierarchy
- The recommended schema builds on existing infrastructure (WorkGuard, observer presets) rather than proposing new systems

Limits:
- This survey does not predict whether adding praise-axis schema will measurably improve output quality
- The recommended schema is illustrative, not production-ready — actual axis definitions need work-specific calibration
- The interaction between bible-level praise rules and the existing `전문가 반응 비례성` criterion has not been tested in a live canary

---

Authoritative owner in this lane: Bible defines praise-axes (what dimensions deserve admiration, what patterns are forbidden, what observer competence tiers exist). Bible does not own staging or execution.

Best bounded next wave from this lane: Add `protagonist_evaluation` schema to WorkGuard work_identity (praise_axes, observer_tiers, forbidden_praise_patterns, evaluation_thresholds) — surfaced as advisory context to blueprint prompt and Director evaluation, not as Python hard gate.

Should Codex open an execution SSOT from this lane now: no — wait for all 4 lanes to merge and determine whether bible-level definition or blueprint-level staging is the higher-ROI first move.
