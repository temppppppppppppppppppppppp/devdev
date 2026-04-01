# Lane 1: Stage 2 Authority / Arc-State Contract Survey

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Lane: Opus Terminal 1
Role: Stage 2 authority / arc-state contract lane
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Master Order: `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-master-order.md`

## 1. Coverage

Surfaces inspected:

| Surface | Inspected | Method |
|---|---|---|
| `modules/core/stage2_orchestrator.py` | Yes | Code read (L1–1090+) |
| `modules/core/stage2_preflight_runtime.py` | Yes | Code read (L1–200) |
| `modules/core/stage2_validation_pipeline.py` | Yes | Code read (L1–500) |
| `modules/core/stage2_context.py` | Yes | Full read (372 lines) |
| `modules/core/stage2_finalizer.py` | Yes | Code read (L1–100, L1090–1340) |
| `modules/models/arc.py` | Yes | Full read (320 lines) |
| `modules/core/project_manager.py` (_save_arcs_to_txt) | Yes | Code read |
| `projects/0_0/plans/arcs/arc_001.txt` | Yes | Full read |
| `projects/0_0/plans/arcs/arc_002.txt` | Yes | Full read |
| `projects/0_0/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json` | Yes | Full read |
| `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json` | Yes | Full read |
| `0_temp.txt` | Yes | Navigational evidence (L1–200) |

## 2. Findings

### F-1. arc_drive.narrative_drive schema is unstable across arcs (FRAGILE)

**Evidence:**

arc_001 `arc_drive.narrative_drive` uses these top-level keys:
```
core_motivation, mission_objective, protagonist_desire,
narrative_tension, emotional_arc, core_scene_ratio,
foreshadowing_expansion, stakes_escalation, callback_integration,
active_villainy, short_term_commercial_goal, short_term_reward
```

arc_002 `arc_drive.narrative_drive` uses a different set:
```
current_arc_objective (with short_term_purpose, specific_trophy_reward,
core_scene_ratio_for_arc), long_term_objective, mission,
protagonist_lack_summary, active_villainy (different sub-structure)
```

**Impact:** Stage 3 blueprint generation and Stage 4 ChiefWriter context cannot rely on a stable field path for `mission_objective`, `protagonist_desire`, or `emotional_arc`. Consumers must use defensive `.get()` chains or fall back to text-level parsing. This is not guaranteed to produce consistent results.

**Source:** This is a Stage 2 source-authority weakness. The LLM generates arc_drive without a rigid schema enforcement. The code (`stage2_finalizer.py` L1113) simply assigns `refined_arc["arc_drive"] = arc_drive if arc_drive else {}` with no structural validation of the drive's inner shape.

**Severity:** FRAGILE. The content intent is consistently present (both arcs express mission/desire/tension) but the schema is free-form.

---

### F-2. state_changes.relationship_changes contains dual-record duplication (FRAGILE)

**Evidence (arc_001):**

The `state_changes.relationship_changes` array contains two kinds of entries:
1. Episode-specific entries: `{"episode": 1, "npc": "한정호", "from": "귀여운 막내", "to": "의외라는 시선"}`
2. Arc-level summary entries: `{"episode": null, "npc": "한정호 (아버지)", "from": "귀여운 막내", "to": "의외라는 시선", "trigger": "", "justification": ""}`

These are near-duplicates with different `episode` (concrete vs null) and different `npc` formats (`"한정호"` vs `"한정호 (아버지)"`).

**Impact:** StateTracker consumers that count relationship changes will double-count. NPC name matching across stages is complicated by the parenthetical format inconsistency. Stage 3/4 consumers that need per-episode attribution get unreliable episode linkage from null-episode entries.

**Source:** Stage 2 source-authority weakness. The FourPhase generator and the Analyst appear to emit different granularity records that are concatenated rather than merged.

**Severity:** FRAGILE. Not blocking—downstream StateTracker uses defensive dedup—but it degrades signal clarity.

---

### F-3. Tactical doc is rich but unstructured text (ADEQUATE with caveats)

**Evidence:** The `tactical_doc` field is a single string containing per-episode plans with structured markers (`[시작 상태]`, `[종료 상태]`). Example from arc_001:

```
제 1화: 깨어난 시간, 그리고 선언
[시작 상태] 위치: 2024년 원룸(기억) → 2006년 서울 성북동 본가...
<narrative text>
[종료 상태] 위치: 서울 성북동 본가 아버지 서재...
```

The content quality is high: each episode has concrete location, equipment, injuries, psychological state, and detailed narrative direction. **However**, this is text, not structured JSON. Stage 3 must parse the text to extract per-episode directives.

**Impact:** Stage 3's `three_phase_blueprint_generator` must correctly segment the tactical doc by episode and extract structured state from marker-delimited text. Any LLM parsing error here loses information. The `episode_details` field provides some structured backup, but it has only 2 event summary lines per episode—far less detail than the tactical doc's full narrative.

**Source:** Stage 2 design choice—not a defect. The tactical doc format is well-established and consistently structured.

**Severity:** ADEQUATE. The format is stable and consistently applied. Stage 3 has working parsers for it. Risk exists only in edge cases where marker patterns deviate.

---

### F-4. status_shadow mixes factual claims with prediction-only labeling (FRAGILE)

**Evidence:** The `StatusShadow` model docstring says:

> *** 경고: 모든 필드는 예측값. ground truth 사용 금지. ***

But arc_001 `status_shadow` contains:
```json
{
  "key_stat_change": "가용 유동성: 0원 → 2,000,000,000원 (법인 자본금 전환 완료), 그룹 내 정치적 영향력: 0 (완전한 배제)",
  "item_consumption": ["과거의 인맥 (승마계 스폰서십 영구 단절)", "어머니 명의 신탁 자산 조기 해지 페널티"]
}
```

`key_stat_change` reads as factual ("법인 자본금 전환 완료") rather than a prediction. The `item_consumption` list also describes definitive narrative events.

**Impact:** If Stage 3 or Stage 4 consumers treat `status_shadow` as advisory-only (per the model contract), they will miss the factual `key_stat_change` information. If they treat it as authoritative, they violate the SSOT contract.

**Source:** Stage 2 source-authority weakness. The LLM populates factual content into a prediction-labelled container.

**Severity:** FRAGILE. The SSOT boundary (`state_constraints.arc_end_state`) does carry the ground truth, but the status_shadow content muddies the signal-to-noise for downstream consumers.

---

### F-5. arc_002 re-introduces 박성호 as new NPC despite arc_001 introduction (MINOR)

**Evidence:**

- arc_001 `state_changes.npc_introductions`: `[{"episode": 2, "name": "박성호"}]`
- arc_002 `state_changes.npc_introductions`: `[{"episode": 5, "name": "박성호"}]`

**Impact:** StateTracker correctly deduplicates via NPC registry, so this does not cause runtime failure. However, it indicates that Stage 2's NPC tracking has a per-arc scope rather than a cross-arc cumulative scope at the point of arc generation. If Stage 4 uses npc_introductions as a signal for "first appearance" narrative beats, arc_002 would incorrectly signal 박성호's first appearance.

**Source:** Stage 2 source-authority weakness—the LLM generates each arc with limited cross-arc NPC memory at generation time. The post-generation StateTracker integration (`full_extract_from_arcs`) fixes this at the tracker level but not in the persisted artifact.

**Severity:** MINOR. StateTracker handles it. Artifact truth is slightly misleading but not blocking.

---

### F-6. Ensemble strategy varies between arcs without explicit justification (OBSERVATION)

**Evidence:**

- arc_001: selected strategy = `creative` (score 100, all three candidates scored 95–100)
- arc_002: selected strategy = `balanced` (score 90, conservative scored 95 higher but balanced was selected)

In arc_002, the `_ensemble_meta` shows `best_score: 90` and `best_strategy: "balanced"`, but conservative scored 95. The field `candidate_index: 1` indicates the second candidate was selected, not the highest-scoring one.

**Impact:** This appears to be the ensemble's diversity-weighted selection working as designed (avoiding creative-only monoculture). Not a defect—but the selection rationale is not persisted, which means Stage 3/4 consumers cannot verify why a lower-scoring strategy was preferred.

**Severity:** OBSERVATION. Not a weakness per se, but a transparency gap.

## 3. Non-Issues

### NI-1. State carryover (equipment, location) is deterministic and sound

The finalizer code (`stage2_finalizer.py` L1296–1323) enforces:
- `arc_start_state.equipment` is synced from the previous arc's `joint_docs.physical_inventory` after accounting for consumption
- First episode `[시작 상태]` text is synced to match the computed start state
- The `_compute_inventory_carryover()` function handles inheritance, consumption, and acquisition deterministically

Real artifact evidence confirms: arc_002 `state_constraints.arc_start_state.equipment` correctly matches arc_001's `joint_docs.physical_inventory`.

### NI-2. Timeline authority is concrete and consistent

Both arcs have concrete `state_changes.timeline` objects with year/month/day values:
- arc_001: 2006-01-05 to 2006-01-25
- arc_002: 2006-02-01 to 2006-02-28

The timeline continuity is correct: arc_002 picks up immediately after arc_001.

### NI-3. Validation pipeline is thorough

The pre-Director chain runs 7+ validators:
1. DraftValidator (structural field checks)
2. SelfReflector (self-critique)
3. Consensus (3-LLM vote)
4. FlowGuard (narrative flow)
5. DuplicateGuard (tactical doc and arc dedup)
6. ArcCorrector (auto-corrections)
7. ContinuityInspector (cross-arc consistency)
8. ConstraintDB validation

This is followed by Director PASS/REJECT judgment and the Pydantic `validate_arc()` ingress/egress normalization.

### NI-4. Episode count and boundary tracking are correct

`ep_start`, `ep_end`, `ep_count` are consistent across both arcs:
- arc_001: ep_start=1, ep_end=4, ep_count=4
- arc_002: ep_start=5, ep_end=9, ep_count=5

### NI-5. joint_docs provide concrete spatial and inventory authority

Both arcs have `joint_docs` with:
- `final_location`: concrete named places (not placeholder text)
- `physical_inventory`: specific named items
- `world_joint`: concrete world-state descriptions

## 4. Stage 2 Authority Table

| Field | Code Contract | Real 0_0 Quality | Stage3/4 Consumer Need | Status |
|---|---|---|---|---|
| `arc_no` / `ep_start` / `ep_end` | Required, validated by Pydantic | Concrete, correct | Episode assignment | **ADEQUATE** |
| `tactical_doc` | str, text-format with markers | Rich, detailed per-episode | Blueprint narrative source | **ADEQUATE** |
| `beat_sequence` | list[str] | Present, per-episode summaries | Episode arc construction | **ADEQUATE** |
| `state_constraints` | dict (ArcState start/end) | Correct, equipment-synced | Opening state, start inventory | **ADEQUATE** |
| `joint_docs` | dict (location, inventory, world) | Concrete named values | Spatial/inventory authority | **ADEQUATE** |
| `state_changes.timeline` | dict (start/end date objects) | Concrete dates, continuous | Temporal authority | **ADEQUATE** |
| `state_changes.relationship_changes` | list[dict] | Present but dual-record duplication | NPC relationship tracking | **FRAGILE** |
| `state_changes.npc_introductions` | list[dict] | Per-arc scope, not cumulative | NPC first-appearance tracking | **FRAGILE** |
| `arc_drive.narrative_drive` | dict, no rigid schema | Rich content, unstable schema | Mission/desire/tension for context | **FRAGILE** |
| `status_shadow` | dict, prediction-only contract | Mixes factual + prediction content | Advisory context | **FRAGILE** |
| `hybrid_composition` | dict | Present, defaults injected if missing | Pattern classification | **ADEQUATE** |
| `episode_details` | list[dict] | 2 items per episode, sparse | Structured event backup | **ADEQUATE** |
| `constraint_summary` | str | Present (arc_002), empty (arc_001) | Prohibition context | **ADEQUATE** |
| `pacing_decision` | dict | Present, concrete reasoning | Pacing guidance | **ADEQUATE** |
| `_ensemble_meta` | dict | Present, strategy+scores | Diagnostic only | **ADEQUATE** |

## 5. Stage 2 Ambiguity Table

| Ambiguity | Source | Downstream Risk | Mitigation Status |
|---|---|---|---|
| `arc_drive` inner schema varies per arc | LLM free-form generation, no finalizer schema enforcement | Stage 3/4 cannot reliably extract `mission_objective` or `emotional_arc` by field path | **Unmitigated** — consumers must use defensive fallback |
| `relationship_changes` dual records | FourPhase + Analyst generate different granularity | StateTracker double-count risk; NPC name format inconsistency | **Partially mitigated** — StateTracker dedups at extract time |
| `status_shadow` fact/prediction boundary | LLM generates factual content into prediction container | Consumers may miss facts or violate SSOT contract | **Unmitigated** — only docstring warns consumers |
| `npc_introductions` per-arc scope | LLM generates without cross-arc NPC memory at generation time | False "first appearance" signals in later arcs | **Mitigated at tracker level** — artifact truth remains misleading |
| `tactical_doc` text vs structured data | Design choice, not defect | Text parsing burden on Stage 3 | **Mitigated** — stable format, working parsers |
| Episode count not validated against tactical_doc episode count | Code sets ep_count from arc_source, tactical_doc is LLM-generated | Mismatch between declared ep_count and actual episodes in tactical_doc | **Partially mitigated** — validation pipeline checks but doesn't hard-reject |

## 6. Verdict

**stage2-fragile**

Stage 2 produces structurally rich, content-high-quality arc authority. The core fields (tactical_doc, state_constraints, joint_docs, timeline, beat_sequence, episode ranges) are concrete, correctly computed, and well-validated.

However, there are four schema/contract fragilities:

1. **arc_drive schema instability** — the most impactful. Stage 3/4 consumers cannot rely on stable field paths for narrative drive data.
2. **relationship_changes dual-record pattern** — manageable via StateTracker dedup but artifact truth is noisy.
3. **status_shadow fact/prediction boundary confusion** — the SSOT labeling contradicts the actual content.
4. **NPC introduction scope** — per-arc rather than cumulative, corrected at tracker level but not in persisted artifacts.

None of these are blocking. The real `0_0` artifacts demonstrate that Stage 2 content quality is sufficient for Stage 3 consumption. The fragilities create risk of information loss or misinterpretation during the Stage 2 → Stage 3 handoff, but they do not structurally prevent progression.

The correct diagnosis is: Stage 2 authority is content-sufficient but schema-fragile. The primary remediation seam is arc_drive schema enforcement in the Stage 2 finalizer.

## 7. Stop

read-only lane complete; no files mutated
