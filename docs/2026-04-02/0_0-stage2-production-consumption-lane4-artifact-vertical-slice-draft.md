# Lane 4: Real Artifact Vertical-Slice Draft

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Role: Opus Terminal 4 — real artifact vertical-slice lane
Mode: read-only survey
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`

## 1. Coverage

### Inspected Artifacts

| Project | Episode | Stage2 Arc | Stage3 Blueprint (plan) | Stage3 Blueprint (JSON) | Stage4 Manuscript | Coverage |
|---------|---------|-----------|------------------------|------------------------|-------------------|----------|
| 0_0 | ep5 | arc_002.txt + final_arc__balanced.json | blueprint_0005.txt | final_blueprint__action_focused.json (attempt_06) | N/A (not produced) | Stage2→Stage3 |
| 0_0 | ep6 | arc_002.txt + final_arc__balanced.json | blueprint_0006.txt | final_blueprint__dialogue_focused.json (attempt_09) | N/A (not produced) | Stage2→Stage3 |
| 0_0 | ep1 | arc_001.txt + final_arc__creative.json | blueprint_0001.txt | (not inspected in detail) | final_manuscript__C.txt (attempt_01) | Stage2→Stage4 (supplemental) |
| 0_1 | ep9 | **NOT PRESENT** | **NOT PRESENT** | **NOT PRESENT** | 리라이트v2_006_010.txt L345-463 | Stage4 only |
| 0_1 | ep13 | **NOT PRESENT** | **NOT PRESENT** | **NOT PRESENT** | 리라이트v2_011_015.txt L179-312 | Stage4 only |
| 0_1 | ep15 | **NOT PRESENT** | **NOT PRESENT** | **NOT PRESENT** | 리라이트v2_011_015.txt L444-564 | Stage4 only |

### Coverage Gaps

- **0_0 ep5-6**: Stage4 manuscripts do not exist for these episodes. Stage4 artifacts only exist for ep1-2. Full chain (Stage2→Stage3→Stage4) cannot be traced for ep5 or ep6.
- **0_1 ep9/13/15**: The entire Stage2→Stage3 artifact chain is absent. Project 0_1 contains only session logs, one blueprint (ep8), and compiled rewrite/manuscript files. Vertical slice for 0_1 is **Stage4-only** — no upstream tracing possible.
- **Supplemental**: 0_0 ep1 was added to provide a Stage2→Stage4 comparison, since ep5-6 lack Stage4.

---

## 2. Findings

### F-1. Stage3 is the primary drift introduction point (0_0 ep5)

**Stage2 Arc (ep5 beat)**: "박성호 PB의 오만한 조언을 끊어내고 15억 원 규모의 WTI 3배 레버리지 매수를 지시하는 한시우." Scene: quiet office, phone call, cold authority. NO physical action. WTI at 60달러 선. Timeline: 2006년 2월 초.

**Stage3 Blueprint (ep5)**: Strategy selected = `action_focused`. 5 scenes produced. Scenes 1 and 5 are **entirely invented physical fight sequences** (thug invasion, bone-breaking, wall-slamming, cliffhanger siege). WTI price drifted to 63.50달러. Timeline shifted to 2006년 2월 28일. Equipment item "미래 지표를 적어둔 이면지" invented (not in arc state_constraints).

| Stage2 Field | Stage2 Value | Stage3 Value | Drift |
|-------------|-------------|-------------|-------|
| WTI price | 60달러 선 횡보 | 63.50달러 부근 횡보 | +5.8% numeric drift |
| Timeline | 2006년 2월 초 | 2006년 2월 28일 심야 | ~4주 temporal drift |
| Physical action | None | 2 full action scenes (scenes 1, 5) | INVENTED |
| Equipment | 등기부등본, OTP, 잔고증명서 | +미래지표 이면지, +법인설립 접수증 | INVENTED items |
| Institution ref | 한미증권 (arc NPC intro) | 신성증권 (threat target) | Name drift (prevalidation caught) |
| Scene count | 1 beat description | 5 scenes | Structural expansion |

**Severity**: MAJOR — core beat survived but dramatic framework was reinterpreted from cerebral to action-thriller.

### F-2. Stage3 invents NPCs and subplots not authorized by Stage2 (0_0 ep6)

**Stage2 Arc (ep6 beat)**: "증거금 동결 후 호가창의 압박 속에서도 확고한 미래 지식으로 평정을 유지하며 에콰도르를 주시하는 한시우." Purely internal contemplation. No phone calls. No other characters.

**Stage3 Blueprint (ep6)**: Strategy = `dialogue_focused`. Scenes 1-2 continue the invented fight from ep5 (fight resolution, interrogation of thug leader). Scene 5 invents a phone call to "제임스 강 (전 모건스탠리 애널리스트)" — an NPC who does not exist in the arc. Also introduces "태산개발 용역반장 최기태" as the thug organizer.

| Item | Stage2 Authority | Stage3 Output | Drift |
|------|-----------------|--------------|-------|
| 제임스 강 NPC | NOT PRESENT | Introduced as informant, given dialogue | INVENTED |
| 최기태 NPC | NOT PRESENT | Named as thug boss | INVENTED |
| 불량배 무리 subplot | NOT PRESENT | 2 full scenes (from ep5 cliffhanger) | INVENTED (carried over) |
| 골드만삭스 채널 | NOT PRESENT | Explicit instruction to open GS route | INVENTED detail |
| 45억 원 수익금 | NOT PRESENT | Specific figure introduced | INVENTED number |

**Severity**: MAJOR — Stage3 treated the arc beat as a loose prompt rather than an authority contract.

### F-3. Python prevalidation catches partial drift but misses invented content

The Stage3 JSON `_ensemble_meta.python_warnings` field for ep5 contains two caught violations:

1. `fact_lock_institution`: "확정 '신성증권' → blueprint '한미증권' 사용" (CRITICAL)
2. `arc_timeline`: "ending_state.timeline 불일치: blueprint '2006년 1월의 심야' vs arc" (MAJOR)

But the system **did not catch**:
- Invention of 2 full action scenes with no arc basis
- Invention of NPCs not in arc `npc_introductions`
- Invention of equipment items not in arc `state_constraints`
- Numeric drift in WTI price (60→63.50)

For ep6, only a `scenario_density` MINOR warning was raised. The NPC inventions and fight subplot continuation were not flagged.

### F-4. Stage2 authority packets are structurally sound

The Stage2 arc JSON (`final_arc__balanced.json`) has well-organized fields:

- `tactical_doc`: per-episode prose with [시작 상태] / [종료 상태] bookends
- `beat_sequence`: concise per-episode beat summary
- `episode_details`: per-ep details array
- `state_changes`: npc_introductions, relationship_changes, timeline, resolved_plots
- `state_constraints`: arc_start_state / arc_end_state with equipment, injuries, location
- `constraint_summary`: forbidden items list
- `arc_drive`: narrative_drive with long-term/short-term objectives, antagonist plan
- `pacing_decision`: ep_count_reasoning, density_focus

These fields provide a clear, machine-readable authority packet. The problem is not that Stage2 output is ambiguous — it's that Stage3 doesn't consume these fields as hard constraints.

### F-5. Stage4 manuscript preserves core better than Stage3 blueprint (0_0 ep1 supplemental)

Comparing Stage2→Stage4 directly for ep1:
- Arc beat: "2024년 고독사 직후 2006년으로 회귀 자각 → 미래 경제 지식 정리 → 독립 선언"
- Stage4 manuscript: Preserves all three beats. Expands with sensory detail (디퓨저 향, 실크 침구, 마호가니 문), internal monologue, sibling confrontation dialogue. **Does NOT invent new subplots or NPCs.**
- Expansion is additive (texture, depth) rather than transformative (reframing the dramatic structure).

This suggests that Stage4's ChiefWriter is more faithful to upstream authority than Stage3's blueprint ensemble, at least for the inspected episodes.

### F-6. 0_1 project lacks Stage2→Stage3 artifact chain entirely

0_1 directory structure:
- `plans/blueprints/`: only `blueprint_0008.txt` (1 blueprint)
- `logs/`: session logs only — no `artifacts/stage2/`, no `artifacts/stage3/`, no `artifacts/stage4/`
- Compiled manuscript files: `리라이트v2_001_005.txt`, `리라이트v2_006_010.txt`, `리라이트v2_011_015.txt`
- Quality-control memo: `리라이트_메모.md`

Vertical slice for 0_1 ep9/13/15 is Stage4-only. The manuscripts themselves are remarkably high quality:
- Extremely detailed financial analysis (specific ISM indices, OECD data, CPI calculations, contract-level COMEX math)
- Rigorous internal logic chains (유가 → CPI → 실질금리 → 금)
- Disciplined NPC interactions (ep9: 최 수석 리스크관리팀 confrontation; ep13: 박성호 meta-conversation; ep15: gold entry + crash)
- NO invented physical violence, NO random NPC introductions

This contrast with 0_0's Stage3 drift is notable, but since 0_1 has no upstream artifacts, the drift path cannot be traced.

### F-7. Blueprint ensemble attempt counts suggest quality difficulty

- 0_0/ep5: `attempt_06` (6 attempts to produce acceptable blueprint)
- 0_0/ep6: `attempt_09` (9 attempts)
- ep5 JSON shows `total_candidates: 1` with `quality_risk: true`
- ep6 JSON shows `total_candidates: 3` with `quality_risk: true`

High attempt counts + quality_risk flags suggest the system itself recognized difficulty in producing acceptable blueprints, yet the accepted output still contains major drift.

---

## 3. Non-Issues

### N-1. Stage2 arc production is internally consistent

Both arc_001 and arc_002 have well-formed JSON, consistent beat↔tactical_doc↔episode_details mapping, and valid state_constraints. The arc authority packet structure is not fragile.

### N-2. Stage2 beat summaries are specific enough for downstream consumption

Each episode beat in the arc contains: character actions, financial specifics, emotional tone, and causal links. The beats are not vague — "박성호 PB의 오만한 조언을 끊어내고 15억 원 규모의 WTI 3배 레버리지 매수를 지시하는 한시우" is sufficiently directive.

### N-3. Stage2 constraint_summary and state_constraints are present and correct

Items forbidden, items acquired, start/end states, and NPC introductions are tracked. The problem is not missing constraints — it's unenforced constraints.

### N-4. 0_1 manuscript content quality is strong

Where Stage4 manuscripts exist (0_1 ep9/13/15), the content demonstrates detailed financial knowledge, disciplined plot progression, and consistent character voice. The quality issue is in the Stage3 transformation layer, not the final writing.

---

## 4. Verdict

**first-drift-at-stage3** (with caveats)

### Primary Evidence

For 0_0 ep5 and ep6, the first material drift occurs at Stage3 (blueprint ensemble), not at Stage2. Stage2 produces coherent, well-structured authority packets with specific beats, state constraints, and narrative directives. Stage3 reinterprets these as loose creative prompts rather than consuming them as hard contracts, resulting in:

- Invented subplots (physical violence not present in arc)
- Invented NPCs (제임스 강, 최기태, 불량배 무리)
- Invented equipment (미래지표 이면지)
- Numeric fact drift (WTI price, timeline)
- Tone/genre reframing (cerebral → action-thriller)

### Contributing Factors

1. **Ensemble strategy selection amplifies drift**: The `action_focused` strategy selected for ep5 caused it to inject physical action into a purely cerebral scene. The strategy selection mechanism appears to prioritize dramatic variety over authority preservation.

2. **Prevalidation catches facts but not inventions**: The python_warnings system detects institution name mismatches and timeline deviations, but does not detect the introduction of entirely new subplots, NPCs, or equipment not authorized by the arc.

3. **High attempt counts (6-9) without drift correction**: Multiple attempts were made but quality_risk remained true, and the selected outputs still contain major drift. The retry mechanism does not appear to specifically target arc-authority alignment.

### Caveats

- **0_1 artifacts are untraceable**: Cannot confirm or deny the drift pattern for 0_1, as the project lacks the Stage2→Stage3 artifact chain entirely.
- **0_0 Stage4 is only available for ep1-2**: Cannot confirm whether Stage4 would have amplified or corrected Stage3's drift for ep5-6.
- **Supplemental ep1 evidence suggests Stage4 is more faithful**: The Stage4 manuscript for ep1 preserves arc authority better than Stage3 blueprints, expanding with texture rather than inventing new content. This is a single data point and not conclusive.

---

## 5. Required Artifacts

### Vertical Slice Table: 0_0 ep5

| Layer | Source | Core Beat | Physical Action | NPCs | WTI Price | Timeline | Equipment |
|-------|--------|-----------|----------------|------|-----------|----------|-----------|
| Stage2 Arc | arc_002.txt/json | PB phone → 15억 매수 지시 | None | 박성호(introduced) | 60달러 선 | 2006년 2월 초 | 등기부등본, OTP, 잔고증명서 |
| Stage3 Blueprint | blueprint_0005 | PB phone → 15억 매수 ✓ | **2 fight scenes invented** | 박성호, **불량배(invented)** | **63.50달러** | **2006년 2월 28일** | +**이면지**, +**접수증** |
| Stage4 | N/A | — | — | — | — | — | — |

### Vertical Slice Table: 0_0 ep6

| Layer | Source | Core Beat | Physical Action | NPCs | New Concepts | Equipment |
|-------|--------|-----------|----------------|------|-------------|-----------|
| Stage2 Arc | arc_002.txt/json | 증거금 동결, 에콰도르 인지 | None | None (solo scene) | 에콰도르 옥시덴탈 해지 | Same as ep5 end state |
| Stage3 Blueprint | blueprint_0006 | 증거금 확인, 에콰도르 확정 ✓ | **Fight resolution (2 scenes)** | **제임스 강, 최기태(invented)** | +**GS 채널**, +**45억 수익금** | +**이면지** |
| Stage4 | N/A | — | — | — | — | — |

### Vertical Slice Table: 0_0 ep1 (supplemental)

| Layer | Source | Core Beat | Additions | NPCs | Invention |
|-------|--------|-----------|----------|------|-----------|
| Stage2 Arc | arc_001.txt/json | 회귀 자각 → 기억정리 → 독립선언 | Compact prose | 한정호, 한태준, 한태민 | None |
| Stage4 Manuscript | final_manuscript__C.txt | Same three beats preserved ✓ | Sensory expansion, inner monologue, 메이드 added | Same + **메이드** (minor) | Additive texture, not transformative |

### Vertical Slice Table: 0_1 ep9/13/15

| Episode | Source | Content Quality | Upstream Traceable? |
|---------|--------|-----------------|-------------------|
| ep9 | 리라이트v2_006_010.txt L345-463 | Detailed WTI analysis, 최 수석 confrontation, barrel-by-barrel math | **No** — no Stage2/3 artifacts exist |
| ep13 | 리라이트v2_011_015.txt L179-312 | Gold thesis explanation, CPI → 실질금리 chain, meta-dialogue with 박성호 | **No** |
| ep15 | 리라이트v2_011_015.txt L444-564 | COMEX gold entry, crash mechanics, margin call, position summary | **No** |

### First-Drift Ledger

| Episode | Stage2→Stage3 Drift | Stage3→Stage4 Drift | First Drift |
|---------|-------------------|-------------------|-------------|
| 0_0/ep5 | MAJOR: action scenes invented, numeric drift, timeline shift | N/A (no Stage4) | **Stage3** |
| 0_0/ep6 | MAJOR: NPCs invented, subplot continued, financial inflation | N/A (no Stage4) | **Stage3** |
| 0_0/ep1 | (not fully inspected) | MINOR: additive texture, no invention | **Stage3** (by pattern) |
| 0_1/ep9 | N/A (no Stage2) | N/A | **Untraceable** |
| 0_1/ep13 | N/A (no Stage2) | N/A | **Untraceable** |
| 0_1/ep15 | N/A (no Stage2) | N/A | **Untraceable** |

---

## 6. Stop

read-only lane complete; no files mutated
