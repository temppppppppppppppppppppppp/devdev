Date: 2026-03-24
Status: final
Document Type: raw evidence ledger (T7 lane)
Lane: Blueprint Synthesis / Integrated Scenario
Canonical Path: `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario-evidence.md`

---

# T7 Evidence Ledger: Blueprint Synthesis / Integrated Scenario

## E1. Blueprint Ensemble Prompt Assembly Path

Source: `modules/domain/agents/blueprint_ensemble.py`

### E1.1 Data Flow Into LLM Prompt

```
Stage3Orchestrator._build_stage3_blueprint_semantic_bundle()
  → _collect_stage3_smart_retrieval_bundle()  → semantic_ctx
  → _inject_stage3_treatment_block_context()  → treatment block (Wave 1 filtered)
  → _inject_stage3_timeline_advisory()        → timeline advisory
  → returns: _bp_semantic_ctx

Stage3Orchestrator passes to ThreePhaseBlueprintGenerator:
  ep_num, arc_data, constraint_block (from ConstraintCompiler),
  prev_blueprints, semantic_context=_bp_semantic_ctx, prev_manuscripts_text

ThreePhaseBlueprintRuntime._bootstrap_runtime_context():
  → initial_feedback = semantic_context + external_feedback

ThreePhaseBlueprintRuntime._run_phase2_generation():
  → calls generate_ensemble(arc_data, constraint_block, feedback=attempt_feedback, ...)

BlueprintEnsembleGenerator.generate_ensemble():
  → _prepare_blueprint_ensemble_context():
      arc_focus      ← _resolve_blueprint_arc_focus(ep_num, arc_data, constraint_block)
      constraints_str ← _format_constraints(constraint_block)
      prev_info      ← _format_prev_info_expanded(prev_blueprint, prev_blueprints, prev_manuscripts_text)
      hud_context    ← _build_hud_context(state_tracker, ep_num)
  → _run_blueprint_ensemble_workers():
      → _generate_single(ep_num, arc_focus, constraints_str, prev_info, feedback, ..., hud_context, genre, cache_name)
          → _build_blueprint_prompt_bundle():
              → PromptLoader.load("ensemble", "BLUEPRINT_GENERATION_PROMPT", arc_focus=..., constraints=..., prev_info=..., ...)
              → _ask_with_cached_context() → LLM generates blueprint JSON including integrated_scenario
```

Anchor: `blueprint_ensemble.py:251-289` (_prepare_blueprint_ensemble_context), `blueprint_ensemble.py:558-635` (_generate_single), `blueprint_ensemble.py:637-709` (_build_blueprint_prompt_bundle)

### E1.2 Key Finding: No Direct arc_data in LLM Prompt Path

`_generate_single()` receives only pre-formatted text: `arc_focus`, `constraints_str`, `prev_info`, `feedback`, `hud_context`, `strategy`, `protagonist_*`, `genre`, `cache_name`.

`_build_blueprint_prompt_bundle()` assembles BLUEPRINT_GENERATION_PROMPT from these text fields only.

`arc_data` dict is NOT accessible inside `_generate_single()` or `_build_blueprint_prompt_bundle()`.

Anchor: `blueprint_ensemble.py:558-572` (parameter list), `blueprint_ensemble.py:637-652` (parameter list)

---

## E2. `_resolve_blueprint_arc_focus()` Analysis

Source: `blueprint_ensemble.py:215-238`

```python
def _resolve_blueprint_arc_focus(self, ep_num, arc_data, constraint_block):
    arc_focus = constraint_block.get("must_focus", {}).get("content", "")
    if not arc_focus:
        arc_focus = extract_episode_tactical(
            arc_data.get("tactical_doc", ""),
            ep_num,
            episode_details=arc_data.get("episode_details"),
        )  # fallback_full=True (DEFAULT)

    episode_details = arc_data.get("episode_details") or []
    # ... prepends current ep details only (filtered by ep_num == current)
```

Priority path:
1. `must_focus.content` from constraint_block (per-episode, set by ConstraintCompiler._extract_episode_focus)
2. Fallback: `extract_episode_tactical()` with `fallback_full=True` (FULL tactical_doc if extraction fails)
3. Prepend: `episode_details[ep_num]` details only

Latent risk: if `must_focus.content` is empty AND regex extraction fails, the entire multi-episode `tactical_doc` is returned as `arc_focus`. This fallback is guarded by `must_focus.content` being almost always populated.

Anchor: `blueprint_ensemble.py:215-238`

Comparison: `blueprint_constraint_compiler.py:232-236` calls `extract_episode_tactical(..., fallback_full=False)` — safer.

---

## E3. `semantic_carryover` Pass-Through Evidence

Source: `blueprint_constraint_compiler.py:97`, `blueprint_ensemble.py:963-986`

### E3.1 Constraint Compiler Side

```python
# blueprint_constraint_compiler.py:97
semantic_carryover = self._normalize_semantic_carryover(arc_data.get("semantic_carryover"))
```

`_normalize_semantic_carryover()` (L654-699) truncates but does NOT episode-filter:
- `relationship_rationale`: up to 4 entries, 120 chars each
- `growth_justification`: 140 chars
- `foreshadow_anchors`: up to 3 entries, 120 chars each
- `continuity_checkpoints`: up to 4 entries, 80 chars each

No `ep_num` filter applied anywhere.

### E3.2 Blueprint Ensemble Formatting Side

```python
# blueprint_ensemble.py:963-986 (_format_constraints)
semantic_carryover = constraint_block.get("semantic_carryover")
if isinstance(semantic_carryover, dict) and semantic_carryover:
    lines.append("\n[Arc Semantic Carryover]")
    for entry in semantic_carryover.get("relationship_rationale", []) or []:
        ...  # relationship NPC: trigger text
    growth = ...  # growth_justification
    for anchor in (semantic_carryover.get("foreshadow_anchors", []) or [])[:3]:
        ...  # foreshadow: anchor text
    checkpoints = ...  # continuity_checkpoints
```

Formatted output appears in LLM prompt as `[Arc Semantic Carryover]` section.

### E3.3 Live Evidence: 00_001 Arc semantic_carryover Content

From `final_arc__balanced.json:155-183`:

```json
{
  "continuity_checkpoints": [
    "20억 자본금 확보 완료",                          ← ep3/ep4 end state
    "가족의 감시망에서 완전히 벗어남",                  ← ep2 end state
    "여의도 임시 사무실 계약 및 법인 설립 완료"         ← ep4 end state
  ],
  "foreshadow_anchors": [
    "저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화' 보도",  ← ep4 event
    "아버지가 '그룹 일은 형들이 알아서 할 거다'라고 발언",
    "한시우의 '그룹 돈은 한 푼도 안 받겠다'는 선언"
  ],
  "growth_justification": "미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보",  ← includes ep3 milestone
  "relationship_rationale": [
    {"npc": "한정호 (아버지)", "trigger": "독자적인 투자사 설립 및 자립 선언"},  ← ep2 event
    ...
  ]
}
```

All of this reaches ep1's blueprint prompt unfiltered via `_format_constraints()`.

---

## E4. ep1 Blueprint Overconsumption Evidence

Source: `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`

ep1 `integrated_scenario` (L34) contains:
- Scene 1-2: 회귀 + 편두통 (correctly ep1 scope per episode_details)
- Scene 3: 자산 정리 + "20억 원을 마련하기로 계산" (ep3 content)
- Scene 4: "법인 인감도장과 20억 예치 법인 계좌 OTP를 손에 쥐게 된다" (ep4 content)
- Scene 5: "이란 핵 문제 재점화" 뉴스 + WTI 투자 준비 (ep4 content)

ep1 `ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태" (ep3+ep4 content)

ep1 `protagonist_state.equipment`: ["SW인베스트먼트 법인 인감도장", "20억 예치 법인 계좌 OTP"] (ep4 content)

Match with `semantic_carryover` content:
- "20억 자본금 확보 완료" → appears in ep1 blueprint as completed in scenes 3-4
- "법인 설립 완료" → appears in ep1 blueprint scene 4
- "유가 상승세, 이란 핵 문제 재점화" → appears in ep1 blueprint scene 5

---

## E5. `_format_prev_info_expanded()` Check

Source: `blueprint_ensemble.py:1054-1101`

For ep1 (first episode): `prev_blueprint=None`, `prev_blueprints=[]` or `None`
- Returns "(첫 에피소드 - 이전 화 없음)"
- No inflation from previous blueprints for ep1

For ep2+: includes previous blueprint `integrated_scenario` text
- If ep1 overconsummed, ep2+ sees ep1's overconsummed content as continuity data
- This is downstream cascade propagation, not independent inflation

---

## E6. Wave 1 Treatment Block Fix Verification

Source: `stage3_orchestrator.py:1115-1171`

`_inject_stage3_treatment_block_context()` now:
- L1128-1132: Only allows `title`, `emotional_beat`, `foreshadow` fields
- L1137-1140: Under `content`, only allows `context` (removes `event_villain`, `solution`, `reward`, `power_shift`)
- L1152-1157: Adds structural guard header explaining event fields are removed

Verified: treatment block no longer injects future-episode events. ✅

---

## E7. BLUEPRINT_GENERATION_PROMPT Template

Source: `config/prompts/ensemble.yaml:250-389`

Template slot injection:
```yaml
{arc_focus}        → per-episode tactical content
{constraints}      → formatted constraint block (includes semantic_carryover)
{prev_info}        → previous blueprint/manuscript info
{hud_context}      → StateTracker HUD
{strategy_directive} → strategy + AI guardrail + feedback
{protagonist_*}    → name, instructions
{pov_constraint}   → POV policy
{reader_feedback}  → advisory feedback
```

The template itself does NOT add arc-global material. It faithfully renders what the code passes in.

---

## E8. `extract_episode_tactical()` Fallback Risk

Source: `modules/core/tactical_utils.py:31-73`

```python
def extract_episode_tactical(tactical_doc, ep_num, *, episode_details=None, fallback_full=True):
    # 1. episode_details → per-ep (CLEAN)
    # 2. regex → per-ep section (CLEAN)
    # 3. fallback → FULL tactical_doc if fallback_full=True (RISKY)
```

- ConstraintCompiler calls with `fallback_full=False` (L236) → safe
- BlueprintEnsemble calls with default `fallback_full=True` (L218) → latent risk
- Mitigated by `must_focus.content` being checked first (L216)

---

## E9. `inherited_state` Episode Scope Check

Source: `blueprint_constraint_compiler.py:445-503`

For ep1 (no prev_blueprint):
- L479-487: Reads `state_constraints.arc_start_state` → "개인 명의 예금통장, 신탁 펀드 증서, 승마 스폰서십 계약서"
- This is the arc START state, correctly scoped for ep1

`joint_docs.physical_inventory` (arc END state) is read at L453-459 but then overridden by `arc_start_state.equipment` at L487. ✅
