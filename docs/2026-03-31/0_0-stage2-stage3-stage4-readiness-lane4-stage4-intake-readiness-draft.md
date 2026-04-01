# Lane 4: Stage 4 Intake-Readiness Survey Draft

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Role: Stage 4 intake-readiness lane (Opus Terminal 4)
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Master Order: `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-master-order.md`

---

## 1. Coverage

### Code surfaces inspected

| File | Scope |
|------|-------|
| `modules/core/stage4_orchestrator.py` L719-838, L1061-1148 | blueprint loading, preflight validation, round context assembly |
| `modules/core/stage4_context_builder.py` L1-700, L2114-2282 | episode base/state payload, blueprint entity extraction, mandatory context assembly |
| `modules/core/stage4_immutable_fact_contract.py` full | IFC packet building, violation classification, prompt rendering |
| `modules/core/stage4_interview_round.py` L960-1003, L2330-2430, L2800-2945 | writer blueprint normalization, common writer kwargs, round execution |
| `modules/core/stage4_types.py` full | _RoundContext dataclass (31 fields), _InterviewRoundResult, WritingDirective |
| `modules/domain/agents/chief_writer_context.py` full | CW context builder, IFC section integration, opening anchor extraction |
| `modules/domain/agents/chief_writer_context_packets.py` L1-200 | CW packet assembly (prev digest, future/past guards, HUD, DNA) |

### Artifact surfaces inspected

| Artifact | Evidence |
|----------|----------|
| `stage3/ep_0001/attempt_01/final_blueprint__action_focused.json` | 5 scenes, all fields present, start_location + time_flow populated |
| `stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` | 5 scenes, start_location properly chains from ep_0001 ending |
| `stage3/ep_0005/attempt_06/final_blueprint__action_focused.json` | CRITICAL fact-lock violation (신성증권→한미증권), MAJOR timeline mismatch, 6 attempts |
| `stage3/ep_0006/attempt_09/final_blueprint__dialogue_focused.json` | MINOR density warning, 9 attempts to produce |
| `stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` | 0 issues, cleanest blueprint |
| `stage4/ep_0001/attempt_01/final_manuscript__C.txt` | 5 scenes, follows blueprint scene order, opening anchor respected |
| `stage4/ep_0002/attempt_01/selected_candidate__A.txt` | 5 scenes, ep_0001 ending properly bridged |

---

## 2. Findings

### F-1. Stage 4 Intake Contract: Blueprint Field Consumption Map

Stage 4 consumes blueprints through three distinct intake chains:

**Chain A — IFC (Immutable Fact Contract) packet building** (`stage4_immutable_fact_contract.py:build_packet`)

| IFC Section | Blueprint field consumed | Hardness | Present in 0_0? |
|-------------|------------------------|----------|-----------------|
| §1 Opening Anchor — start_location | `blueprint["start_location"]` | HARD — violation = immediate reject | ✅ All 5 blueprints |
| §1 Opening Anchor — time_flow | `blueprint["time_flow"]` | HARD — violation = immediate reject | ✅ All 5 blueprints |
| §1 Opening Anchor — scene_1 title | `blueprint["scene_breakdown"]["scene_1"]["title"]` | HARD | ✅ All 5 blueprints |
| §1 Opening Anchor — scene_1 location | `blueprint["scene_breakdown"]["scene_1"]["location"]` | HARD | ✅ All 5 blueprints |
| §4 Scene Obligations — goal | `scene["goal"]` or `scene["summary"]` | HARD — used as must_materialize fallback | ✅ All scenes |
| §4 Scene Obligations — location | `scene["location"]` | SOFT | ✅ All scenes |
| §4 Scene Obligations — must_materialize | `scene["must_materialize"]` | HARD — **design intent** | ❌ NEVER populated by Stage 3 |
| §4 Scene Obligations — must_not_erase | `scene["must_not_erase"]` | SOFT — no fallback | ❌ NEVER populated by Stage 3 |
| §6 Upstream flags — metadata completeness | `scene["goal"]` or `scene["summary"]` existence check | FLAG | ✅ All scenes have goal |

**Chain B — Writer prompt construction** (`chief_writer_context.py:build_common_context`)

| Prompt section | Blueprint field consumed | Priority | Present in 0_0? |
|----------------|------------------------|----------|-----------------|
| Scene breakdown (JSON dump) | `blueprint["scene_breakdown"]` | PRIMARY — structured contract for CW | ✅ Always present |
| Opening Anchor [TF-2] | `start_location`, `time_flow`, `scene_1.title`, `scene_1.summary`, `scene_1.location` | HARD — ⛔ markers in prompt | ✅ Always present |
| Integrated scenario advisory | `integrated_scenario_advisory` or `integrated_scenario` | LOW — "discard if conflicts with hard canon" | ✅ Always present |
| Ending hook | `ending_hook` | MEDIUM | ✅ Always present |
| IFC section | Built from Chain A | HARD — "override local plausibility" | ✅ Built from present fields |

**Chain C — Context builder entity extraction** (`stage4_context_builder.py:_extract_blueprint_entities`)

| Entity type | Blueprint fields consumed | Purpose | Present in 0_0? |
|-------------|--------------------------|---------|-----------------|
| NPCs | `scene_breakdown.*.characters`, `scene_breakdown.*.npcs`, `npc_roster`, `key_npcs` | Retrieval plan, NPC boundary block | ✅ `characters` always present |
| Items | `protagonist_state.equipment`, via full-text scan | Item guard, future guard | ✅ Always present |
| Plots | `core_tension`, `expected_ending` via full-text scan | Plot retrieval | ✅ Always present |
| Locations | `start_location`, `scene.*.location`, `end_location` | Ambient NPC hints [TF-J] | ✅ Always present |

### F-2. IFC Structural Gap: `must_materialize` and `must_not_erase` Never Populated

The IFC dataclass `SceneObligation` has fields `must_materialize` and `must_not_erase` designed to carry explicit scene-level hard constraints. Stage 4's `_extract_scene_obligations` (L236-257) reads these:

```python
must_materialize=str(scene.get("must_materialize", "") or scene.get("goal", "") or "").strip(),
must_not_erase=str(scene.get("must_not_erase", "") or "").strip(),
```

In all 5 inspected `0_0` blueprints, `must_materialize` and `must_not_erase` are **absent from every scene**. The fallback chain works as follows:
- `must_materialize` → falls back to `goal` → **adequate** (all scenes have `goal`)
- `must_not_erase` → falls back to empty string → **structural gap** (no negative-constraint data reaches CW)

**Impact**: The IFC currently tells CW what each scene MUST do (via goal fallback) but has NO data on what each scene MUST NOT undo. This is a design-intent gap in the Stage 3 → Stage 4 handoff contract.

### F-3. Preflight Validation is Fail-Open

The blueprint preflight validator (`stage4_orchestrator.py` L719-783) is explicitly designed as fail-open:

```python
_pass_result = {"passed": True, "issues": [], "summary": "", "patched_blueprint": None}
# ... all exceptions → return _pass_result
```

This means:
- Even if the LLM detects CRITICAL fact-lock violations (as ep_0005's `신성증권→한미증권` drift), the preflight can still pass the blueprint through
- The preflight only runs for `ep_num >= 2` and requires a feature flag
- If the LLM call fails, the blueprint passes without any check

This is a **designed safety valve** (not a bug) — Stage 4 prefers to attempt writing and let the Director judge, rather than blocking on upstream issues. But it means Stage 4 has NO hard gate against factually contaminated blueprints from Stage 3.

### F-4. High-Attempt Blueprints Signal Upstream Difficulty

| Episode | Stage 3 attempts | Prevalidation warnings | Assessment |
|---------|-----------------|----------------------|------------|
| ep_0001 | 1 | MINOR (density) | Clean intake |
| ep_0002 | 1 | MINOR (density) | Clean intake |
| ep_0005 | **6** | **CRITICAL** (fact-lock) + **MAJOR** (timeline) | Contaminated intake |
| ep_0006 | **9** | MINOR (density) | High churn, adequate output |
| ep_0008 | 1 | 0 | Cleanest intake |

ep_0005 is the most concerning: after 6 attempts, the surviving blueprint still has a CRITICAL fact-lock violation and a MAJOR timeline mismatch. This means:
- Stage 3 validator was unable to resolve the `신성증권 vs 한미증권` institutional name conflict in 6 rounds
- Stage 3 validator was unable to align the timeline (blueprint says "2006년 1월의 심야" while arc says "2월 말")
- Only 1 candidate survived out of the ensemble — the quality floor was barely met

### F-5. Stage 4 Round Context is Structurally Complete

The `_RoundContext` dataclass requires 31 fields. Analysis of the assembly chain:

| Field category | Fields | Source | Populated from Stage 2/3? |
|---------------|--------|--------|--------------------------|
| Blueprint-derived | blueprint, arc_data, arc_pos, total_ep_in_arc, arc_tactical | DB (blueprint + arc) | ✅ Yes |
| Prior state | prev_text, prev_ending, prev_manuscripts_text, episode_digest | DB (manuscripts) | ✅ Yes (after ep 1 runs) |
| HUD/inventory | hud_report, current_inventory, current_martial_arts, dead_npcs | HUD + cumulative bible | ✅ Yes |
| World state | world_state_summary, chain_link_section, item_acquisition_timeline | WorldState/ChainLink/DB | ✅ Yes |
| Prompt supplements | purism_prompt, npc_equipment_summary, effective_anti_trope, intro_dna | Guard + Bible | ✅ Yes |
| Mandatory context | reference_anchor_prompt, mandatory_context, justification_prompt, reflexion_prompt | Context builder | ✅ Yes |
| Session-level | chief_writer, validators (4), story_context, style_guide, genre_name | Orchestrator | ✅ Yes |
| Preflight | preflight_advisory | Preflight LLM | ✅ Yes (fail-open) |

No structural gaps in field population were observed. All 31 fields have clear sources.

### F-6. ep_0001 Manuscript Faithfully Follows Blueprint Intake

Cross-checking the ep_0001 final manuscript against the blueprint:

| Blueprint contract | Manuscript compliance |
|-------------------|----------------------|
| start_location: "2006년 본가 저택 한시우의 침실" | ✅ "저택 침실" header, matches |
| time_flow: "아침 기상 직후 -> 오전" | ✅ Manuscript starts at awakening |
| scene_1: "2006년의 천장" — 회귀 자각 | ✅ Scene 1 opens with regression consciousness |
| scene_2: "기억의 활자화" — 지표 기록 | ✅ Scene 2 has economic data writing |
| scene_3: "엇갈리는 시선" — 형제 대면 | ✅ Scene 3 has 한태준/한태민 encounter |
| scene_4: "절연과 선언" — 독립 선언 | ✅ Scene 4 has "독립하겠습니다" declaration |
| scene_5: "첫 번째 타깃" — 자본 확보 개시 | ✅ Scene 5 has 한국투자증권 call |
| ending_hook: "엄지손가락이 통화 버튼을 짓눌렀다" | ⚠️ Manuscript ends with phone scene but richer narration |
| protagonist_state.equipment: [이면지, 휴대전화] | ✅ Both items present in manuscript |

Assessment: Stage 4 intake worked correctly for ep_0001. The IFC/TF-2 opening anchor constraint was respected. All 5 scenes were materialized in blueprint order.

### F-7. ep_0002 Manuscript Properly Chains from ep_0001

The ep_0002 blueprint `start_location` is "본가 저택 서재 앞 복도" — exactly where ep_0001 ended. The manuscript opens at this location with the phone call to 박성호. This confirms the Stage 2 → Stage 3 → Stage 4 chain link is working for early episodes.

---

## 3. Non-Issues

### NI-1. Blueprint structural shape is adequate

All 5 inspected blueprints have the required top-level structure Stage 4 expects:
- `scene_breakdown` (dict with scene_1...scene_N)
- `start_location`, `time_flow`
- `ending_hook`, `ending_state`, `protagonist_state`, `relationship_changes`
- `core_tension`, `expected_ending`, `pacing_notes`, `target_beat`
- `integrated_scenario`

Stage 4 is NOT receiving authority in the wrong shape.

### NI-2. Opening anchor fields are always populated

`start_location` and `time_flow` are present in every inspected blueprint. The IFC opening anchor section will always be populated. This is the highest-priority Stage 4 intake contract and it is satisfied.

### NI-3. Scene breakdown per-scene fields are structurally complete

Every scene in every inspected blueprint has: `title`, `goal`, `summary`, `location`, `characters`, `key_events`, `tension_level`. The optional `content` field is empty in most early episodes but is not required by Stage 4.

### NI-4. The writer blueprint normalization is sound

`_normalize_writer_blueprint` (L977-1003) deep-copies the blueprint, sanitizes UI contamination markers, and demotes `integrated_scenario` to advisory priority. This is a sensible protection layer that prevents blueprint prose from overriding structured scene contracts.

### NI-5. NPC roster collection is robust

`_collect_npc_roster` (L276-341) checks 8 arc `state_changes` sub-fields plus 3 blueprint key pools, with fallback across `name`, `npc`, `source`, `target`, `npc_name`. No NPC extraction fragility observed.

---

## 4. Verdict: intake-fragile

### Diagnosis

Stage 4's intake system is structurally sound in terms of field consumption, prompt assembly, and blueprint normalization. The 31-field `_RoundContext` is fully populated from available sources. The IFC (Immutable Fact Contract) correctly extracts opening anchors, scene obligations, committed state facts, and completed event facts.

However, the intake is **fragile** in the following respects:

**Primary fragility (upstream contamination passthrough)**:
- Stage 4's preflight is fail-open by design
- Stage 3 blueprints with CRITICAL fact-lock violations (ep_0005: 신성증권→한미증권) and MAJOR timeline mismatches pass into Stage 4 without blocking
- Stage 4 relies entirely on the Director LLM to catch upstream factual contamination at review time, which is a soft gate
- High-attempt blueprints (ep_0005: 6 attempts, ep_0006: 9 attempts) signal that Stage 3 is already struggling upstream, and the surviving blueprints may represent the least-bad option rather than a structurally sound one

**Secondary fragility (IFC gap)**:
- The IFC `must_not_erase` field is never populated by Stage 3, meaning Stage 4's negative-constraint enforcement is structurally absent
- The IFC `must_materialize` field falls back to `goal`, which works but is weaker than explicit materialization requirements
- This gap is a Stage 3 → Stage 4 contract weakness, not a Stage 4 intake defect

**Not the primary problem**:
- Stage 4 intake expectations are NOT too demanding
- Blueprint structural shape is NOT the issue
- Opening anchor, scene breakdown, and entity extraction are all working correctly

### Right diagnosis for 0_0

The answer to the master order question "Which diagnosis is correct?" is:

**Stage 4 is getting authority, but some of it is factually contaminated and the handoff contract has structural gaps.**

Specifically:
1. For early episodes (ep_0001, ep_0002, ep_0008): Stage 2/3 are structurally sufficient, Stage 4 intake works correctly, manuscripts follow blueprints faithfully
2. For mid-arc episodes under pressure (ep_0005, ep_0006): Stage 3 struggles to produce fact-consistent blueprints within the allowed attempt budget, and the surviving blueprints carry factual contamination that Stage 4 must absorb and correct at the Director level
3. The IFC negative-constraint gap (`must_not_erase`) means Stage 4 cannot enforce "don't undo X" obligations even if Stage 3 were to identify them

This is not a Stage 4-only defect. The correct framing is: Stage 3 sometimes passes contaminated blueprints that Stage 4's fail-open intake cannot block, and the Stage 3 → Stage 4 contract is missing explicit negative-constraint fields that the IFC was designed to consume.

---

## 5. Required Artifacts

### Stage4 Intake Contract Table

| Contract layer | What Stage 4 expects | Hard/Soft | Status in 0_0 |
|---------------|---------------------|-----------|--------------|
| Blueprint existence | `get_blueprint(ep)` returns non-None | HARD — blocks if absent | ✅ Present for all episodes |
| Arc data existence | Arc with matching ep_start/ep_end | HARD — blocks if absent | ✅ Present |
| IFC Opening Anchor | `start_location` + `time_flow` + `scene_1.{title,location}` | HARD — ⛔ in prompt | ✅ Always present |
| IFC Scene Obligations | `scene.{goal,summary,location}` per scene | HARD — ⛔ in prompt | ✅ Always present |
| IFC must_materialize | `scene.must_materialize` | HARD (design) | ❌ Never populated (falls back to goal) |
| IFC must_not_erase | `scene.must_not_erase` | SOFT | ❌ Never populated (no fallback) |
| Preflight validation | LLM check vs world_state + fact_ledger | SOFT — fail-open | ⚠️ Runs but does not block |
| Blueprint consistency | No fact-lock or timeline violations | EXPECTED | ⚠️ ep_0005 has CRITICAL + MAJOR violations |
| Writer prompt sections | scene_breakdown, integrated_scenario, ending_hook | MEDIUM | ✅ Always present |
| Entity extraction | characters/npcs per scene, protagonist_state | MEDIUM | ✅ Always present |
| Previous manuscript | prev_text, prev_ending from DB | HARD for ep > 1 | ✅ Present after ep 1 |
| World state | world_state_summary from WorldStateManager | MEDIUM | ✅ Present |
| Chain link | chain_link_section from DB | MEDIUM | ✅ Present when available |

### Missing-Authority Handoff Table

| Authority gap | Source | Impact on Stage 4 | Remediation seam |
|--------------|--------|-------------------|------------------|
| `must_not_erase` never populated | Stage 3 generator does not emit this field | CW has no explicit negative constraints per scene; can only rely on committed_state_facts for "don't undo" enforcement | Stage 3 blueprint generator should emit `must_not_erase` per scene |
| `must_materialize` never populated | Stage 3 generator does not emit this field | IFC falls back to `goal`, which is adequate but less specific | Stage 3 should emit explicit materialization requirements |
| Fact-lock violations in surviving blueprints | Stage 3 validator cannot resolve some fact conflicts within attempt budget | Stage 4 Director must catch and reject factually wrong manuscripts; wastes Stage 4 attempt budget | Stage 3 validator should hard-block CRITICAL fact-lock violations |
| Timeline mismatches | Stage 3 generator/validator misaligns with arc timeline | IFC opening anchor may encode wrong time; CW writes from wrong temporal position | Stage 3 validator should enforce arc timeline alignment |
| High-attempt blueprints (low candidate survival) | Stage 3 ensemble struggles with complex mid-arc constraints | Only 1 of 3 candidates survives; surviving candidate may be lowest-quality acceptable | Stage 2 arc constraints may need decomposition for mid-arc episodes |

---

read-only lane complete; no files mutated
