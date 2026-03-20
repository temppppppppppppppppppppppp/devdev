# Stage2 LLM-Owned Ep Count Density Pacing Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage2-llm-owned-ep-count-density-pacing-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage2-llm-owned-ep-count-density-pacing-execution-ssot.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: large active workspace; hotspots include Stage2/3/4 agent files, geuldobi-desktop, tests, docs/2026-03-19, docs/2026-03-20`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/stage2-arc-pacing-compression-prompt-levers-3pass-audit.md`
- `docs/2026-03-20/stage2-llm-owned-ep-count-density-pacing-3pass-audit.md`
Evidence Artifacts:
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/core/response_schemas.py`
- `modules/core/stage2_validation_pipeline.py`
- `config/prompts/ensemble.yaml`
- `config/prompts/analyst.yaml`
Side-Effect Coverage: covered

## 1. Intent

Stage 2 Arc의 `ep_count`와 pacing 판단을 Python heuristic에서 LLM judgment로 이동한다.

목표는 두 가지다.

- `ep_count 판단은 LLM이 하고 Python은 guard만 하는 구조`
- `아이템/보상/실물 사건 자원이 적은 블록에서도 tactical density를 높이도록 high-density direction을 명시`

이 변경은 단순 `-1화` 보정보다 상위의 구조 수정이다.

## 2. Baseline Facts

- 현재 `four_phase_arc_generator._determine_ep_count()`가 먼저 `ep_count`를 정한다.
- 현재 `ArcEnsemble` prompt는 여전히 LLM이 `ep_count`를 고르는 듯 서술하지만, `ep_end`는 이미 Python이 계산해서 넣는다.
- 현재 구조는 mixed authority다.
- "늘어짐" complaint는 `ep_count` 자체뿐 아니라 `같은 ep_count 안에서 tactical_doc가 느슨하게 쓰이는 문제`와 연결돼 있다.
- analyst 계열에는 `chosen_pacing / ep_count_suggestion` precedent가 이미 존재한다.

## 3. Scope

Included:
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/arc_ensemble.py`
- `config/prompts/ensemble.yaml`
- `modules/core/response_schemas.py`
- `modules/core/stage2_validation_pipeline.py`
- Stage 2 관련 타깃 테스트

Excluded:
- Stage 3/4 pacing policy
- treatment block authoring rules
- blueprint phase pacing redesign
- desktop/UI surfaces

## 4. Pass 1. Inventory Summary

- ownership hotspot 1: `four_phase_arc_generator._determine_ep_count()`
- ownership hotspot 2: `arc_ensemble.generate_ensemble()` prompt assembly
- contract hotspot 3: `ARC_DESIGN_SCHEMA`
- validation hotspot 4: `stage2_validation_pipeline._stage2_flow_guard()`
- regression hotspot 5: `tests/test_four_phase_arc_generator.py`, `tests/test_stage2_pipeline.py`, Stage 2 prompt contract tests

## 5. Pass 2. Semantic Classification

- Class A. Ownership surfaces
  - `four_phase_arc_generator`
  - `arc_ensemble`
- Class B. Contract/schema surfaces
  - `response_schemas`
  - prompt template output contract
- Class C. Guard/verification surfaces
  - `stage2_validation_pipeline`
  - downstream ep span normalization logic
- Class D. Observability surfaces
  - pacing reasoning logs
  - audit metadata for later diagnosis

## 6. Side-Effect Map

- file writes / artifacts:
  - none directly
  - arc payload shape changes may affect later persisted artifacts indirectly
- DB / schema / transaction boundaries:
  - no direct DB schema change required for first tranche
  - optional audit metadata expansion may later affect JSONL/summary sinks
- JSONL / log / audit sinks:
  - pacing reasoning should be made more explicit than the current `pacing_reason` log line
- console / UI / operator output:
  - operator can benefit from `pace_mode / reasoning` visibility
- rollback / recovery / retry:
  - invalid LLM output must fall back to Python guard normalization
- cache / global state:
  - prompt cache keys may vary if density guide is injected
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### 7.1 Target split

- Python ownership to remove:
  - direct `ep_count` decision
- Python responsibilities to keep:
  - density/input signal collection
  - output guard
  - `ep_end` normalization
  - minimum beat/length guard
- LLM responsibilities to add:
  - `pace_mode`
  - `ep_count`
  - `pacing_reasoning`
  - `density_focus`

### 7.2 Recommended contract

Add a structured `pacing_decision` block to Arc output:

- `pace_mode`: `compressed(2~3) | standard(4~5) | expanded(6)`
- `ep_count_reasoning`: string
- `density_focus`: string

Keep `ep_count` as the final integer contract field.

### 7.3 High-density direction rule

Prompt must explicitly tell the Arc generator:

- low item/reward/resource blocks should not be stretched by idle explanation
- each episode must still advance at least one meaningful change
- repeated emotional explanation and setup-only beats should be reduced
- callback/foreshadow/payoff density should be raised when hard assets are sparse

## 8. Execution Tranches

1. Contract tranche
   - define final ownership split
   - add `pacing_decision` to schema and prompt contract
2. Prompt tranche
   - inject density signal summary and high-density direction into `ArcEnsemble`
   - stop pretending Python and LLM both own the same decision ambiguously
3. Guard tranche
   - demote `_determine_ep_count()` from chooser to fallback/guard role
   - normalize `ep_end`
   - handle invalid/missing pacing output
4. Verification tranche
   - update Stage 2 validation/flow tests
   - add pacing reasoning observability

## 9. Acceptance Criteria

- `ep_count` primary decision comes from LLM output, not Python heuristic
- Python still rejects or normalizes invalid ep count output safely
- prompt contains explicit high-density direction for low-resource blocks
- downstream `ep_end`, beat count, and tactical length contracts remain stable
- targeted regression tests cover ownership split and guard fallback

## 10. Verification Plan

- sequential pytest shards:
  - `tests/test_four_phase_arc_generator.py`
  - `tests/test_stage2_pipeline.py`
  - Stage 2 prompt contract / relevant Arc tests
- prompt contract inspection:
  - confirm `pacing_decision` and density guide are present
- syntax and hygiene:
  - `python scripts/check_utf8_hygiene.py ...`
  - `git diff --check ...`

## 11. Guardrails

- do not implement naive `ep_count - 1` hardcoding as the main fix
- do not leave mixed ownership where Python decides but prompt still claims LLM owns the choice
- do not remove Python guards for invalid LLM output
- do not widen scope into Stage 3/4 pacing semantics during this tranche
- do not turn this into total free-form LLM pacing without bounded schema and fallback

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition:
  - satisfied on closure; temp mirror removed after canonical closure update
- roadmap dependency:
  - none currently; single execution SSOT item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure

Closure Status:
- closed

Verification Evidence:
- `python -m pytest tests/test_tier4_ensemble_caching.py -q` -> `14 passed`
- `python -m pytest tests/test_llm_schema.py -q` -> `8 passed`
- `python -m pytest tests/test_four_phase_arc_generator.py -q` -> `15 passed`
- `python -m pytest tests/test_investment_math_wiring.py -q` -> `5 passed`
- `python -m pytest tests/test_stage2_pipeline.py -k "Stage2FlowGuard" -q` -> `7 passed, 75 deselected`
- `python scripts/check_utf8_hygiene.py docs/2026-03-20/stage2-llm-owned-ep-count-density-pacing-execution-ssot.md docs/temp/stage2-llm-owned-ep-count-density-pacing-execution-ssot.md` -> pass at realization time
- `git diff --check -- modules/domain/agents/four_phase_arc_generator.py modules/domain/agents/arc_ensemble.py modules/core/response_schemas.py config/prompts/ensemble.yaml docs/2026-03-20/stage2-llm-owned-ep-count-density-pacing-execution-ssot.md docs/temp/stage2-llm-owned-ep-count-density-pacing-execution-ssot.md` -> no errors; CRLF warnings only
- `python scripts/ops_validator.py` -> pass at realization time

Residual Risk:
- `pacing_decision` observability remains softer than ideal in operator-facing Stage 2 audit output.
- Live-run efficacy for `compressed=2~3 / standard=4~5 / expanded=6` should still be monitored by a later focused pacing audit.

Follow-Up:
- future optional tranche: expose `pacing_decision` more directly in Stage 2 audit/operator output
- temp mirror cleanup is complete; no further queue work remains for this item
