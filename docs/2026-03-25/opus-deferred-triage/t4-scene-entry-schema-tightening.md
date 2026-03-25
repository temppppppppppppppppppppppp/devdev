# T4 Lane Report: Schema Tightening For Scene-Entry Object-Only Enforcement

Date: 2026-03-25
Status: final
Document Type: triage lane report
Lane: T4
Canonical Path: `docs/2026-03-25/opus-deferred-triage/t4-scene-entry-schema-tightening.md`
Parent Order: `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md`

## 1. Lane Question

Is schema tightening for scene-entry object-only enforcement justified now, or is it too high-blast before more live evidence?

## 2. Investigated Surfaces

- `modules/core/response_schemas.py` L530-577 — Gemini JSON schema definition for scene entries
- `modules/models/blueprint.py` L29-50 — Pydantic `BlueprintScene` model and `Blueprint.scene_breakdown` type
- `modules/domain/agents/unified_blueprint_validator.py` L639-747, L1215-1308 — Python prevalidation scene checks
- `modules/validation/blocking_validator_scene_checks.py` L60-159 — Stage 4 blocking validator scene surface
- `modules/domain/agents/blueprint_constraint_compiler.py` L458-468 — constraint extraction from previous scenes
- `config/prompts/ensemble.yaml` L298-376 — prompt scene specification
- `projects/canary_0325/logs/artifacts/stage3/ep_0001..ep_0009/` — live canary evidence

## 3. Current Schema Tolerance State

The scene-entry schema accepts scenes as **either objects or strings** at three layers:

### Layer 1: Gemini response schema (`response_schemas.py:530-557`)

```python
BLUEPRINT_SCENE_ENTRY_SCHEMA = types.Schema(
    anyOf=[
        types.Schema(type=types.Type.OBJECT, properties={...}),
        types.Schema(type=types.Type.STRING),  # string fallback
    ],
)
```

The `anyOf` allows the Gemini API to return a scene as a plain string instead of a structured object.

### Layer 2: Pydantic model (`blueprint.py:50`)

```python
scene_breakdown: dict[str, BlueprintScene | str] = Field(default_factory=dict)
```

Accepts both `BlueprintScene` objects and raw strings. On Pydantic validation failure, `validate_blueprint()` returns the raw dict unchanged (graceful degradation, L76-86).

### Layer 3: Python prevalidation (`unified_blueprint_validator.py:719-723`)

```python
for scene_value in self._iter_scene_entries(scenes):
    if isinstance(scene_value, str):
        shallow_count += 1   # counted as shallow, but NOT rejected
        continue
```

String-only scenes increment `shallow_count` and produce a `MINOR` advisory. They are never blocked.

### Layer 4: Blocking validator (`blocking_validator_scene_checks.py:88-90`)

If scene extraction fails entirely, the check **skips** rather than fails:
```python
if scene_count == 0:
    return {"check": "scope_overflow", "passed": True, "reason": "씬 개수 추출 불가 - 체크 스킵"}
```

## 4. Canary Evidence: String Scenes Do Not Occur In Practice

Inspected all 9 canary episodes (EP1-EP9) from `canary_0325`:

| Episode | Total Scenes | Dict Scenes | String Scenes |
|---------|-------------|-------------|---------------|
| EP1     | 4           | 4           | 0             |
| EP2     | 5           | 5           | 0             |
| EP3     | 5           | 5           | 0             |
| EP4     | 4           | 4           | 0             |
| EP5     | 5           | 5           | 0             |
| EP6     | 5           | 5           | 0             |
| EP7     | 5           | 5           | 0             |
| EP8     | 5           | 5           | 0             |
| EP9     | 4           | 4           | 0             |

**Result: 0/42 scenes across 9 episodes are strings.** All scenes are well-structured dict objects with populated `goal` (15-29 chars), `summary` (33-54 chars), and standard fields.

## 5. Blast-Radius Assessment

Tightening the schema to object-only would touch:

1. **`response_schemas.py`**: Remove `types.Schema(type=types.Type.STRING)` from `BLUEPRINT_SCENE_ENTRY_SCHEMA.anyOf` — this changes the Gemini API contract that governs LLM output shape.

2. **`blueprint.py`**: Change `dict[str, BlueprintScene | str]` to `dict[str, BlueprintScene]` — this changes the Pydantic validation contract.

3. **`unified_blueprint_validator.py`**: The `isinstance(scene_value, str)` branch becomes dead code. Scene-specificity and scenario-density checks rely on `isinstance(scene_value, dict)` continuing to work.

4. **`blocking_validator_scene_checks.py`**: The dict coercion fallback at L143-145 would need to align.

5. **Regression surface**: Any test or downstream consumer that expects `BlueprintScene | str` in scene_breakdown would need updating.

**Blast radius: MEDIUM.** It crosses the Gemini API response schema, Pydantic model layer, and two validator surfaces. The schema change at the Gemini API layer is the highest-risk part — if any edge case (unusual genre, degraded LLM output, prompt variant) causes Gemini to fall back to string scenes, the tighter schema would force a generation error rather than graceful degradation.

## 6. ROI Assessment

**The string-fallback tolerance is not causing quality problems.** The canary shows zero string-only scenes across 42 scene entries. The Gemini API prompt and schema already effectively guide the LLM to produce structured objects.

Wave 1 landed explicit authority re-banding and density prevalidation. The self-audit wave landed prompt-level self-verification. Both changes operate on the assumption that scenes are objects (and they are in practice).

The remaining scene quality issues (thin goals, weak density) are addressed through:
- Wave 1 prevalidation: `_collect_scene_specificity_issues()` and `_collect_scenario_density_issues()` (both already landed)
- Self-audit wave: 7-item checklist including scene specificity items (already landed)

**Schema tightening would remove a safety net that is not causing harm, while introducing regression risk at the Gemini API boundary.**

## 7. Risk Of Premature Tightening

- The `anyOf: [OBJECT | STRING]` fallback was documented as a **compatibility feature** for `google-genai` API behavior (`response_schemas.py:573-576`).
- Removing it assumes the Gemini API will never produce string-typed scene entries under any configuration. This assumption has not been tested across model updates, temperature settings, or degraded-context scenarios.
- The graceful degradation pattern (`validate_blueprint()` returning raw dict on failure) is intentional and aligns with the workspace's Director-sovereignty principle — Python does not reject; Director decides.
- Tightening the schema now would provide zero measurable quality improvement (since string scenes are not occurring) while introducing a new failure mode.

## 8. Findings Summary

| Finding | Evidence |
|---------|----------|
| String-scene fallback exists at 3 layers | `response_schemas.py:557`, `blueprint.py:50`, `unified_blueprint_validator.py:721` |
| String scenes do not occur in canary | 0/42 scenes across 9 episodes are strings |
| Wave 1 prevalidation already covers thin scenes | `unified_blueprint_validator.py:1215-1308` |
| Self-audit checklist already covers scene specificity | `ensemble.yaml` 자가 검증 체크리스트 item 3-4 |
| Schema change crosses Gemini API boundary | `response_schemas.py` governs LLM output contract |
| Blast radius is medium (4 files, API boundary) | See Section 5 |
| Net quality improvement would be zero | No string scenes to eliminate |

## 9. Verdict

The string-fallback tolerance is a safety net, not a quality limiter. Live evidence shows it is never triggered. Removing it provides zero improvement while introducing risk at the Gemini API contract boundary. The real scene quality improvements have already landed through Wave 1 prevalidation and the self-audit wave.

This lane does not justify an execution SSOT now or after canary. If a future canary or genre variant produces actual string-only scenes, the topic can be revisited with concrete evidence.

---

Lane verdict: **no**
Best bounded next wave from this lane: **none**
Should Codex open an execution SSOT from this lane now: **no**
