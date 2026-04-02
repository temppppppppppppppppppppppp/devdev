# 0_0 Stage3 Static Lane 4: Artifact Drift Vertical Slice

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Lane: Opus Terminal 4 — artifact vertical slice / drift taxonomy
Master Order: `docs/2026-04-02/0_0-stage3-static-global-parallel-master-order.md`
Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
Related Evidence:
- `projects/0_0/logs/artifacts/stage3/ep_0005/attempt_06/final_blueprint__action_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0006/attempt_09/final_blueprint__dialogue_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0007/attempt_02/final_blueprint__dialogue_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/canary_0_0_stage3_arc2_semantic_r5/logs/artifacts/stage3/ep_0005/attempt_02/final_blueprint__dialogue_focused.json`
- `projects/canary_0_0_stage3_arc2_semantic_r5/logs/artifacts/stage3/ep_0006/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/canary_0_0_stage3_arc2_semantic_r5/logs/artifacts/stage3/ep_0009/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`

## 1. Coverage

### 1.1 Artifact Inventory

| EP | Main 0_0 Artifact | Canary r5 Artifact | Attempts (Main) | Attempts (Canary) |
|----|--------------------|--------------------|-----------------|-------------------|
| 5  | Yes (action_focused) | Yes (dialogue_focused) | 6 | 2 |
| 6  | Yes (dialogue_focused) | Yes (dialogue_focused) | 9 | 1 |
| 7  | Yes (dialogue_focused) | Yes (action_focused) | 2 | 2 |
| 8  | Yes (dialogue_focused) | Yes (action_focused) | 1 | 1 |
| 9  | **NO** | Yes (emotion_focused) | N/A | 1 |

### 1.2 Inspected Surfaces

- Stage2 arc_002 `tactical_doc` (canonical episode mission authority)
- Stage2 arc_002 `episode_details`, `state_constraints`, `state_changes`, `beat_sequence`
- Stage3 blueprint JSON: `integrated_scenario`, `scene_breakdown`, `protagonist_state`, `relationship_changes`, `ending_state`, `time_flow`
- Stage3 blueprint `_ensemble_meta.python_warnings`
- Stage3 plan text files (`plans/blueprints/blueprint_000X.txt`)
- Canary `canary_0_0_stage3_arc2_semantic_r5` full ep5-9 artifact set
- Stage3 semantic fidelity closure audit (2026-04-01)

### 1.3 Coverage Gaps

- No Stage4 artifacts exist for main 0_0 ep5-9 (Stage4 was paused by operator policy)
- No drafts/manuscripts exist for main 0_0 ep5-9
- The `0_1` contrast slice was not inspected (no `0_1` Stage3-capable arc_002 chain was found to be fully present)

## 2. Findings

### F-1. Off-Arc Invention — Dominant Drift Pathology (CRITICAL)

The single worst Stage3 drift category is **off-arc subplot invention**.

Evidence:

- **EP5 main** (attempt_06): Scenes 1 and 5 introduce 불량배 (thugs) performing a physical attack on the protagonist's opiistel. The arc tactical_doc for ep5 contains zero mention of physical violence, thugs, or break-ins. The arc ep5 is purely about "박성호 PB의 오만한 조언을 끊어내고 15억 원 규모의 WTI 3배 레버리지 매수를 지시하는 한시우."

- **EP6 main** (attempt_09): Scenes 1-2 continue the 불량배 subplot from ep5 with escalated violence (관절 꺾기, 벽면에 내리꽂기, 쇠파이프). Additionally invents two entirely new characters not in any arc source:
  - 태산개발 용역반장 최기태 — fictional crime figure
  - 제임스 강 (전 모건스탠리 애널리스트) — fictional information broker

- **EP7 main**: Begins "한시우가 정보원에게 에콰도르 진출을 지시하고 전화를 끊은 직후" — this opening is a direct continuation of ep6's invented 정보원 subplot, creating a cascade of drift.

- **EP8 main**: Scene 4 still references the invented 정보원 and 에콰도르 자산 매집 subplot.

The off-arc invention was not present in arc_002's tactical_doc at any point. It is a pure Stage3 fabrication.

**Canary fix evidence**: The `canary_0_0_stage3_arc2_semantic_r5` ep5 and ep6 artifacts contain NO 불량배 subplot. The closure audit confirms "no 취객/난입/멱살/무단침입/괴한/심부름센터/침입자 hit in final authoritative txt artifact." The code-level semantic fidelity remediation successfully eliminated this drift category.

### F-2. Institution Name Instability (MAJOR)

The securities firm where 박성호 PB works changes name across artifacts:

| Source | Institution Name |
|--------|-----------------|
| Arc tactical_doc (ep5) | 한미증권 |
| EP5 main blueprint (scene 4) | 신성증권 (used as competitive threat) |
| EP7/EP8 main blueprints | 신성증권 (used as 박성호's firm) |
| EP5 canary_r5 | 한국투자증권 (yet another name) |
| Python prevalidator flag on EP5 main | "확정 '신성증권' → blueprint '한미증권' 사용" |

Three different institution names appear across artifacts for the same entity. The python prevalidator treats 신성증권 as the established fact, but the arc tactical_doc itself uses 한미증권. The canary introduces a third name (한국투자증권). This is not a one-time typo but a structural failure in institution identity binding from Stage2 through Stage3.

### F-3. Timeline Compression and Scrambling (MAJOR)

The arc defines ep5-9 as spanning approximately one month (2월 초 ~ 2월 말).

| EP | Arc Timeline | Main Blueprint Timeline | Canary r5 Timeline |
|----|-------------|------------------------|--------------------|
| 5  | 2월 초 | "2006년 2월 28일 심야" | "2006년 2월 말의 심야" |
| 6  | (just after ep5) | "2006년 2월 초 새벽" | "2006년 2월 말의 심야" |
| 7  | 2월 중순 | "2006년 2월 초 새벽 동트기 전" | (not inspected) |
| 8  | 2월 말 | "2006년 2월 초 새벽" | (not inspected) |
| 9  | (arc end: 2월 말) | N/A | "2006년 2월 말 심야" |

Main artifacts compress all five episodes into a single night. EP5 main jumps directly to "2월 28일" (the arc end date), leaving no temporal room for ep6-9. EP7 and EP8 then reset backward to "2월 초," creating an impossible reverse timeline.

The canary_r5 ep5 also shows timeline misalignment ("2월 말" when the arc says "2월 초"), suggesting this drift category was NOT fixed by the semantic fidelity remediation.

### F-4. Numeric/Financial Drift (IMPORTANT)

| Fact | Arc Value | Main Blueprint Value | Notes |
|------|----------|---------------------|-------|
| WTI entry price | 60달러 선 | 63.50달러 (ep5) | 6% drift |
| WTI dip price | 59달러 후반 (ep7) | 62달러 (ep7) | 4% drift |
| Money framing | 15억 증거금 | 45억/60억 "규모" (ep6, ep8) | Confuses nominal with leveraged notional |
| 수익금 timing | 3억 at ep9 | 45억 mentioned at ep6 | Premature revenue projection |

The WTI price points and money amounts drift from arc specifications. The 45억 수익금 reference in ep6 is particularly harmful because it front-loads an ep9 payoff into ep6, collapsing the narrative tension arc.

### F-5. Invented Character Cascade (IMPORTANT)

Characters invented in one drifted episode carry forward as if established:

```
EP6 invents: 태산개발 용역반장 최기태, 제임스 강 (정보원)
     ↓
EP7 opens with: "정보원에게 에콰도르 진출을 지시하고 전화를 끊은 직후"
     ↓
EP8 scene 4: "에콰도르 자산 매집을 지시했던 정보원에게 전화"
```

Once an invented character survives one episode's validation, it becomes pseudo-established truth that contaminates subsequent episodes. The canary_r5 ep9 does NOT contain invented characters, confirming the canary remediation broke this cascade.

### F-6. Retry Count as Drift Severity Proxy (IMPORTANT)

| EP | Attempts (Main) | Attempts (Canary) | Primary Drift in Main |
|----|-----------------|-------------------|----------------------|
| 5  | 6 | 2 | Off-arc invention + institution + timeline |
| 6  | 9 | 1 | Off-arc invention + invented chars + timeline |
| 7  | 2 | 2 | Timeline + price + stale 정보원 reference |
| 8  | 1 | 1 | Mild institution drift + stale 정보원 |
| 9  | N/A | 1 | Clean |

EP6's 9 attempts is the worst signal in the entire arc. The validator repeatedly rejected off-arc invention but the ensemble could not produce a clean candidate until attempt 9 — and even then the final artifact still carries the 불량배 subplot. This suggests the generation prompt is actively driving the LLM toward off-arc invention, and the validator is fighting the generator rather than guiding it.

Post-remediation (canary_r5), ep6 passes on attempt 1. This confirms the remediation targeted the right failure mode.

## 3. Non-Issues

### N-1. Arc tactical_doc content is not the problem

The arc_002 `tactical_doc` provides specific, episode-level mission briefs with character interactions, dialogue tone, and emotional trajectory. These are detailed enough to produce faithful blueprints. The canary_r5 proves this: the same arc produces clean ep5-9 after Stage3 code changes. The upstream content is sufficient.

### N-2. Stage3 is not uniformly broken

EP8 main passed on attempt 1 with mostly-faithful content. EP7 main passed on attempt 2 with mild drift. The worst pathology concentrates in ep5-6 (the arc's first two episodes), suggesting Stage3 struggles most with the "cold start" of a new arc rather than continuation.

### N-3. Python prevalidator catches the drift

The `_ensemble_meta.python_warnings` correctly flagged fact_lock_institution (ep5), timeline mismatch (ep5), and tactical_semantic_fidelity (ep5 canary_r5 candidates). The detection exists; the issue is that detection doesn't prevent selection of drifted candidates when the candidate pool itself is contaminated.

### N-4. Blueprint plan text vs JSON are identical

The `.txt` blueprint plan files and the `.json` final_blueprint files contain the same `integrated_scenario` content. There is no discrepancy between the two output formats.

## 4. Verdict

**`first-drift-at-stage3`**

Rationale:

1. The arc_002 `tactical_doc` provides clear, specific episode missions. Stage2 production is content-sufficient (aligned with the Stage2 survey verdict).

2. The first material artifact drift — off-arc physical subplot invention, institution name instability, timeline scrambling, and invented characters — all originate at Stage3 blueprint generation.

3. The canary_0_0_stage3_arc2_semantic_r5 proves that Stage3 code-level remediation eliminates the worst drift pathology (off-arc invention). Retry counts drop from 6/9 to 2/1 for the previously-worst episodes.

4. Residual drift categories after remediation:
   - Timeline compression/misalignment (F-3) — NOT fixed
   - Institution name instability (F-2) — NOT fixed (possibly worse: third name introduced)
   - Stale `python_warnings` metadata on clean artifacts — observability debt

5. The dominant recurring drift taxonomy is:
   1. Off-arc invention (fixed by canary)
   2. Timeline compression (unfixed)
   3. Institution identity instability (unfixed)
   4. Invented character cascade (fixed by canary)
   5. Numeric/price drift (partially improved)

6. Stage3 is better described as **reinterpretation-heavy** in the main 0_0 artifacts, and **mixed (improved but unstable)** in the canary_r5 artifacts. It has not yet reached compiler-like status.

7. The evidence supports a long-term direction of **tighten Stage3 contracts** — specifically:
   - timeline binding from arc to blueprint (currently prose, needs machine enforcement)
   - institution/entity name locking (fact_lock exists but does not prevent generation-time drift)
   - episode-scope constraint enforcement (preventing cross-episode character cascade)

## 5. Stop

read-only lane complete; no files mutated
