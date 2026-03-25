# T3. Stage3 Prevalidation + Quality Signal Coverage

Date: 2026-03-25
Lane: T3 — Stage3 Prevalidation + Quality Signal Coverage
Status: survey-complete
Master Order: `docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md`
Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`

## 1. Lane Questions

1. What clarity/density failures can current prevalidation already catch?
2. What materially important blueprint blur is still invisible?
3. Is the current `quality_risk` signal too generic for operator action?

## 2. Evidence Surfaces Inspected

| File | Relevance |
|------|-----------|
| `unified_blueprint_validator.py` (1221 lines) | Primary — all Python prevalidation checks |
| `blueprint_ensemble.py` (ensemble generation + meta) | `_ensemble_meta`, `python_warnings`, `quality_risk` construction |
| `blueprint_constraint_compiler.py` (constraint block) | Inputs to prevalidation (must_focus, stop_line, fact_lock, capital_continuity) |
| `three_phase_blueprint_runtime.py` (runtime loop) | `quality_gate`, `quality_risk` propagation |
| `director_ensemble.py` (compare_and_select_blueprint) | Director LLM scoring criteria |
| `stage3_orchestrator.py` (orchestrator) | `_stage3_meta` construction, dashboard signals, downstream flow |
| `response_schemas.py` (BLUEPRINT_SCHEMA, DIRECTOR_AUDIT_SCHEMA) | Schema-level structural enforcement |
| `stage4_director_runtime.py` / `stage4_outcome_runtime.py` | Downstream `_stage3_meta` consumption |
| `projects/0324_00_/logs/artifacts/stage3/ep_0005/` | Artifact truth: actual blueprint structure |

## 3. Findings

### F-1. Current Prevalidation Check Inventory (7 check families)

The Python prevalidation layer in `UnifiedBlueprintValidator._python_pre_validate()` runs 7 check families:

| # | Check Family | Method | What It Catches | Severity |
|---|-------------|--------|-----------------|----------|
| 1 | **Structure** | `_collect_structure_prevalidation_issues` | Missing required fields (`scene_breakdown`, `integrated_scenario`), char length < 800, scene count < 3, scenes lacking `goal`/`summary` | MAJOR/MINOR |
| 2 | **Fidelity** | `_collect_fidelity_prevalidation_issues` | Arc relationship-change NPCs absent from `integrated_scenario` | MINOR |
| 3 | **Arc Compliance** | `_collect_arc_compliance_prevalidation_issues` | Stop-line violation (next-episode content leaking into current) | CRITICAL |
| 4 | **Continuity** | `_collect_continuity_prevalidation_issues` | Location discontinuity between prev_blueprint end_location and current start_location | MAJOR |
| 5 | **Fact-Lock Drift** | `_collect_fact_lock_drift_issues` | Location fact-lock violation, item-storage drift, ending-hook provenance reversal, institution name drift | MAJOR/CRITICAL |
| 6 | **Capital State Drift** | `_collect_capital_state_drift_issues` | Capital contradiction patterns (phantom capital, "still available" after committed) | MAJOR/CRITICAL |
| 7 | **Temporal Deictic Drift** | `_collect_temporal_deictic_drift_issues` | Absolute temporal references ("18년 전") in ending_hook or scenario tail | MAJOR |

Additionally, `_apply_dead_npc_advisory()` adds dead-NPC checks (CRITICAL) as a separate advisory.

### F-2. What Current Prevalidation Can Already Catch (Clarity/Density Subset)

From the clarity/density perspective, current checks cover:

- **Minimum volume floor**: `integrated_scenario` < 800 chars → MAJOR
- **Minimum scene count floor**: `scene_breakdown` < 3 scenes → MAJOR
- **Scene shallowness signal**: Scenes without `goal`/`summary` counted → MINOR advisory
- **Intent fidelity**: Arc relationship-change NPCs not mentioned → MINOR advisory
- **Stop-line contamination**: Next-episode content bleeding into current → CRITICAL

These are **necessary but insufficient** for clarity/density quality. They catch structural absence (missing fields, too few scenes, too short) but not **content vagueness within structurally present fields**.

### F-3. What Current Prevalidation Cannot See — THE BLIND SPOTS

**F-3a. Scene-level specificity blindness (HIGH IMPACT)**

The structure check counts scenes and checks for `goal`/`summary` field presence, but never evaluates whether those fields contain actionable specificity. A scene with `goal: "갈등 심화"` (deepen conflict) passes identically to `goal: "한시윤이 HMC투자증권 3층 트레이딩룸에서 WTI 선물 60달러 매수 주문을 넣지만 환율 급등으로 실질 마진이 2% 미만으로 떨어짐"`.

Evidence from `ep_0005` artifact: all 5 scenes have goal lengths of 15-23 chars and summary lengths of 35-44 chars. These are structurally present but could be equally thin regardless of content.

**No Python check measures:**
- goal/summary character length beyond mere presence
- action-verb density or concrete-noun ratio in scene descriptions
- per-scene `key_events` count or specificity
- whether `integrated_scenario` actually *covers* the scenes declared in `scene_breakdown`

**F-3b. integrated_scenario density blindness (HIGH IMPACT)**

The only density check is `len(integrated_scenario) < 800`. There is no:
- Per-scene proportional coverage check (e.g., 5 scenes but 80% of text covers scene_1)
- Named-entity density check (concrete NPC names, locations, numbers)
- Action-verb vs. abstract-adjective ratio
- Duplicate/boilerplate paragraph detection
- Scene-boundary coverage (whether all declared scenes actually appear in the narrative)

A 1500-char `integrated_scenario` that vaguely summarizes the whole episode in abstract terms passes identical to one with concrete per-scene blocking and specific character actions.

**F-3c. must_focus → integrated_scenario alignment blindness (MEDIUM IMPACT)**

The `must_focus` constraint block carries `key_events` from Arc. The fidelity check only inspects NPC names from `relationship_changes`, not whether `key_events` items actually appear in the blueprint. If Arc says "제5화 핵심: WTI 선물 매수, 환율 리스크 발견, 한신옥 접촉" but the blueprint talks about completely different events, nothing flags this.

**F-3d. Authority-surface drift blindness (MEDIUM IMPACT)**

No check compares whether `scene_breakdown` and `integrated_scenario` tell the same story. The `scene_breakdown` could describe scenes A-B-C-D-E while `integrated_scenario` narrates X-Y-Z. This is an authority-mixing artifact that prevalidation cannot see.

**F-3e. Ending hook depth/quality blindness (LOW-MEDIUM IMPACT)**

The temporal-deictic check catches absolute time references in `ending_hook`, but there is no check for:
- Ending hook length/presence (the Director compare prompt checks this, but Python prevalidation doesn't)
- Ending hook relevance to the episode's events
- Ending hook specificity vs. generic "다음이 기대된다" style hooks

### F-4. quality_risk Signal Analysis

**How quality_risk is constructed:**

```
quality_risk = bool(
    pipeline_result.get("quality_risk", False)
    or quality_gate_failed
)
```

Where:
- `pipeline_result["quality_risk"]` comes from `_build_python_warning_entries()` — True if ANY Python prevalidation issue exists (including MINOR ones)
- `quality_gate_failed` comes from `_apply_phase3_quality_gate()` — True if Director verdict is PASS but score < threshold (default 90)

**How quality_risk flows downstream:**

1. Annotated onto `blueprint["_stage3_meta"]["quality_risk"]`
2. Stage 4 Director runtime reads it → injects "[S3-META 경고]" advisory text
3. Stage 4 outcome runtime reads it → lowers V75-D inplace-repair streak threshold from 2 to 1
4. Recorded in quality_dashboard, session_logger, audit_event, JSONL

**The problem with quality_risk as a clarity/density signal:**

| Aspect | Assessment |
|--------|-----------|
| **Granularity** | Binary (True/False) — no severity gradient |
| **Root-cause specificity** | Indistinguishable: a MINOR scene-shallowness advisory and a CRITICAL dead-NPC violation both set quality_risk=True |
| **Operator actionability** | Operator sees "quality_risk=True" in dashboard but cannot distinguish "blueprint is vague" from "blueprint has a factual contradiction" without reading the full prevalidation issue list |
| **Downstream interpretation** | Stage 4 Director receives generic text "로직 모순·연속성 결함 가능성 높음" regardless of whether the actual risk was structural vagueness or factual error |
| **python_warnings visibility** | Up to 4 compact entries are forwarded to Director compare prompt, but only as advisory; the Director prompt does not specifically ask about density or clarity |

**Verdict: quality_risk is generic and operator-opaque for clarity/density.** It conflates factual-contradiction risk with structural-vagueness risk. The downstream Director advisory always says "로직 모순·연속성 결함 가능성" even when the actual issue is scene thinness or vagueness.

### F-5. Director LLM-Side Coverage

The Director compare prompt (`director_ensemble.py` L1577-1640) evaluates:
- 일관성·모순 (40%)
- Arc 준수 (35%)
- 연속성 (15%)
- 다음 화 연결 (10%)

**Missing from Director criteria:**
- Blueprint density or per-scene specificity is not a named evaluation axis
- `integrated_scenario` quality-of-writing or concreteness is not scored
- Scene structural coverage (whether all scenes in `scene_breakdown` actually appear in `integrated_scenario`) is not checked
- The REJECT threshold of "시나리오 1000자 미만" is extremely low (only catches very bare blueprints)

The Director prompt does mention "서사 밀도 부족" as a REJECT condition at 1000 chars, but this is a floor, not a quality gradient.

### F-6. Schema-Level Enforcement Gaps

`BLUEPRINT_SCHEMA` requires only 3 fields: `episode_number`, `scene_breakdown`, `integrated_scenario`. Other fields like `ending_hook`, `start_location`, `end_location`, `core_tension` are all optional.

`BLUEPRINT_SCENE_ENTRY_SCHEMA` allows `anyOf: [object, string]` — a scene entry can legally be a bare string with no structured fields at all.

This means the API-level schema provides almost no density enforcement. A blueprint with 5 string-only scenes and a 900-char `integrated_scenario` is schema-valid.

### F-7. Existing Density Checks Elsewhere (Not in Stage 3 Prevalidation)

`arc_draft_validator.py` has `_validate_tactical_episode_density()` and `_validate_tactical_action_density()` — but these are **Stage 2** arc-level checks, not Stage 3 blueprint checks.

`block_enricher.py` has `analyze_block_density()` — but this is a **narrative pipeline** component (Treatment/BI), not a runtime pipeline component.

No Stage 3 module currently imports or references any density analysis logic.

## 4. Confidence and Limits

| Claim | Confidence | Basis |
|-------|-----------|-------|
| 7 check families correctly enumerated | 98% | Full source read of `_python_pre_validate` |
| Scene specificity blindness confirmed | 97% | Code inspection + artifact inspection |
| integrated_scenario density blindness confirmed | 97% | Code inspection — only `len()` check exists |
| must_focus alignment blindness confirmed | 95% | Fidelity check only covers NPC names from `relationship_changes` |
| quality_risk is binary and untyped | 99% | Direct source read of construction and consumption |
| Director prompt lacks density/clarity axis | 95% | Full compare prompt read |
| Schema permits bare-string scenes | 99% | Direct `anyOf` in BLUEPRINT_SCENE_ENTRY_SCHEMA |

**Known limits of this survey:**
- Did not inspect every Director audit prompt variant (only `compare_and_select_blueprint`; the `audit_manuscript` prompt in `director_continuity.py` may have additional checks)
- Did not run a fresh live episode to observe real-time prevalidation output
- Canary_0325 Stage 3 artifacts not yet available for cross-reference

## 5. Summary of Blind Spots Ranked by Impact

| Rank | Blind Spot | Impact | Category |
|------|-----------|--------|----------|
| 1 | Scene goal/summary specificity not measured | HIGH | validation blind spot |
| 2 | integrated_scenario density not measured beyond char floor | HIGH | validation blind spot |
| 3 | must_focus key_events → blueprint alignment not checked | MEDIUM | validation blind spot |
| 4 | scene_breakdown ↔ integrated_scenario coherence not checked | MEDIUM | validation blind spot |
| 5 | quality_risk is binary/untyped — operator cannot distinguish vagueness from contradiction | MEDIUM | quality signal opacity |
| 6 | Director scoring has no density/clarity axis | MEDIUM | LLM-side gap |
| 7 | Schema allows bare-string scene entries with no structure | LOW-MEDIUM | schema looseness |
| 8 | Ending hook presence/quality not Python-checked | LOW | missing minor check |

## 6. Mandatory Final Lines

- Dominant limiter in this lane: **validation blind spot**
- Best bounded improvement candidate in this lane: **scene-specificity + scenario-density Python prevalidation checks (add 2 new check families to `_python_pre_validate`)**
- Should this lane alone trigger a new SSOT: **no**
