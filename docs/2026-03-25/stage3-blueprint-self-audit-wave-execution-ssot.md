# Stage3 Blueprint Self-Audit Wave Execution SSOT

Date: 2026-03-25
Status: closed (closure-audited)
Document Type: execution SSOT
Canonical Path: `docs/2026-03-25/stage3-blueprint-self-audit-wave-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-blueprint-self-audit-wave-execution-ssot.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: canary_0325 live artifacts/logs, Wave 1 uncommitted edits to blueprint_ensemble.py + unified_blueprint_validator.py, 2026-03-25 survey/audit docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md`
- `docs/2026-03-25/pre-director-self-audit-stagewise-survey-order.md`
- `docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md` (Finding D: self-audit is secondary amplifier)
Evidence Artifacts:
- `config/prompts/ensemble.yaml` (BLUEPRINT_GENERATION_PROMPT — confirmed zero self-audit)
- `modules/core/constitutional_checker.py` (BLUEPRINT_CONSTITUTION B1-B5, dead code for Stage 3)
- `modules/domain/agents/blueprint_ensemble.py` (zero self-check references)
Side-Effect Coverage:
- Stage 3 blueprint generation prompt text only
- no Python code flow change
- no DB/JSONL schema change
- no Stage 2 or Stage 4 change
- no artifact naming change

## 1. Intent

Add the first prompt-level self-audit checklist to Stage 3 blueprint generation.

Stage 3 is the only major writer stage with zero in-prompt self-audit. Stage 2 has three active systems. Stage 4 has a multi-round post-generation Self-Critique loop. Stage 3 has nothing.

This wave closes a zero-to-one structural gap that the pre-director self-audit survey identified with 96% confidence.

Why now:
- Wave 1 (authority re-banding + density prevalidation) is closed
- the partial canary baseline is clean
- the gap is structural and unambiguous
- the implementation is bounded to prompt text only

## 2. Baseline Facts

From the survey report:

- `config/prompts/ensemble.yaml` `BLUEPRINT_GENERATION_PROMPT` ends with `반드시 유효한 JSON만 출력하세요` — no self-audit section anywhere
- `modules/domain/agents/blueprint_ensemble.py` has zero imports or references to `constitutional_checker`, `quality_amplifier`, `self_check`, or `자가 검증`
- `modules/core/constitutional_checker.py` has `BLUEPRINT_CONSTITUTION` (articles B1-B5) and `get_architect_constitution()` — designed for Stage 3 but never wired
- Stage 2 prompt self-audit has three active systems; Stage 3 has zero
- the checklist pattern is already proven in Stage 2 (checkbox `□` format)
- token budget: current `BLUEPRINT_GENERATION_PROMPT` is ~2,000-3,000 tokens; a bounded self-audit block adds ~150-250 tokens

### Design Decision: Inline Prompt vs Wire ConstitutionalChecker

Two approaches were evaluated:

**A. Wire `ConstitutionalChecker.get_architect_constitution()`** — requires adding `constitutional_checker` to Stage 3 context, passing through to `blueprint_ensemble.py`, calling during prompt assembly. 3+ file changes, new DI wiring.

**B. Inline self-audit checklist in `ensemble.yaml`** (selected) — one prompt template text edit. Zero code flow change. Clean canary attribution.

**Decision**: Approach B. The first self-audit insertion should be the smallest possible change. ConstitutionalChecker wiring is a credible follow-up if this wave shows positive signal.

## 3. Scope

Included:
- `config/prompts/ensemble.yaml` — `BLUEPRINT_GENERATION_PROMPT` self-audit insertion
- new test `tests/test_stage3_blueprint_self_audit_wave.py`

Excluded:
- `modules/domain/agents/blueprint_ensemble.py` — no Python code flow change
- `modules/core/constitutional_checker.py` — not wiring existing dead code in this wave
- `modules/core/stage3_context.py` — no context slot additions
- `modules/domain/agents/unified_blueprint_validator.py` — no prevalidation change
- Stage 2 or Stage 4 prompt changes
- Director prompt changes
- DB/JSONL schema, artifact naming, or persistence contract changes

## 4. Pass 1. Inventory Summary

Single content owner:
- `config/prompts/ensemble.yaml` — `BLUEPRINT_GENERATION_PROMPT` block

Supporting test:
- `tests/test_stage3_blueprint_self_audit_wave.py`

Insertion hotspot: after `### [필수 조건]` block (currently L369-376), before `### [V67] 모순 방지` block (L378).

## 5. Pass 2. Semantic Classification

Class A. Zero-to-one self-audit gap closure (this wave)
- a bounded checklist block in the prompt template
- derived from BLUEPRINT_CONSTITUTION B1-B5 articles plus density awareness
- explicit "verify before outputting" instruction

Class B. Deferred structural wiring
- ConstitutionalChecker Stage 3 wiring → later wave if canary positive
- Stage 4 in-prompt self-audit restoration → uncertain ROI, defer
- Stage 2 self-check compliance logging → low ROI, defer

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage 3 blueprint artifacts unchanged in schema or naming
  - blueprint content may improve if LLM self-checks before submission
- DB / schema / transaction boundaries:
  - no change
- JSONL / log / audit sinks:
  - no payload shape change
  - quality_risk frequency may shift if self-audit reduces prevalidation failures
- console / UI / operator output:
  - no change
- rollback / recovery / retry:
  - may reduce retry count if LLM catches issues before submission
  - no new Python verdict layer
- cache / global state:
  - context cache content changes slightly due to prompt text change
  - cache TTL and mechanism unchanged
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

Prompt-only change. No substrate requirements, contracts, or dependency constraints.

Insert a self-audit checklist section into `BLUEPRINT_GENERATION_PROMPT` in `config/prompts/ensemble.yaml`.

Placement: after `### [필수 조건]` section (L369-376), before `### [V67] 모순 방지` (L378).

Checklist design:
- question format matching Stage 2 pattern (checkbox `□` items)
- covers BLUEPRINT_CONSTITUTION B1-B5 articles in natural language
- adds density/clarity items aligned with Wave 1 prevalidation improvements
- explicit "verify all items before outputting JSON" instruction
- ~150-250 tokens, 7 items

## 8. Execution Tranches

### Tranche A. Self-Audit Checklist Insertion

Owner:
- `config/prompts/ensemble.yaml`

Problem:
- the blueprint LLM is never told to verify its own output before submission
- Stage 2 has three self-check systems; Stage 3 has zero

Required implementation shape:

Insert the following block into `BLUEPRINT_GENERATION_PROMPT`, after `### [필수 조건]` and before `### [V67] 모순 방지`:

```yaml
  ### [자가 검증 체크리스트 - JSON 출력 전 필수 확인]
  아래 항목을 모두 확인하고, 위반이 있으면 수정한 후 JSON을 출력하세요.

  □ 직전 화의 ending_hook/cliffhanger에서 자연스럽게 이어지는 오프닝인가?
  □ Blueprint에서 아직 획득하지 않은 아이템/무공을 사용하는 장면이 없는가?
  □ 씬 개수가 3~5개 범위이며, 각 씬에 구체적 사건/행동이 포함되어 있는가?
  □ integrated_scenario가 1000자 이상이고, 모든 씬의 핵심 장면이 구체적으로 서술되었는가?
  □ ending_hook이 존재하고 다음 화로의 긴장/궁금증을 만드는가?
  □ start_location이 직전 화의 end_location과 일치하는가?
  □ Arc tactical_doc 범위를 초과하는 사건(다음 화/다른 블록 내용)이 포함되지 않았는가?

  위 항목 중 하나라도 "아니오"면 해당 부분을 수정한 후 출력하세요.
```

Item derivation:
- item 1 → B2 (cliffhanger continuity)
- item 2 → B1 (unacquired item usage)
- item 3 → B3 (scene count) + density awareness
- item 4 → density/clarity (new, aligned with Wave 1 prevalidation)
- item 5 → B4 (ending_hook presence)
- item 6 → continuity (location match)
- item 7 → B5 (tactical_doc scope adherence)

Guardrails:
- do not restructure the overall prompt template layout
- do not add new template variables — the checklist is static text
- do not exceed ~250 tokens
- do not duplicate `### [필수 조건]` items — this is self-verification, not rule restatement
- Korean language matching the rest of the prompt

### Tranche B. Test Coverage

Owner:
- new file `tests/test_stage3_blueprint_self_audit_wave.py`

Required implementation shape:
- load `ensemble.yaml` `BLUEPRINT_GENERATION_PROMPT` via `PromptLoader`
- assert the self-audit checklist header `자가 검증 체크리스트` is present in the loaded prompt
- assert at least 5 `□` checkbox items exist
- assert the "수정한 후 출력" instruction is present
- no live LLM call required

## 9. Deferred Follow-Ups

Explicitly deferred:
- ConstitutionalChecker dynamic wiring for Stage 3 (approach A)
- Stage 4 in-prompt self-audit restoration
- Stage 2 self-check compliance logging
- self-audit reasoning field persistence
- self-audit compliance rate tracking

## 10. Acceptance Criteria

- `BLUEPRINT_GENERATION_PROMPT` in `ensemble.yaml` contains a `자가 검증 체크리스트` section
- the checklist covers: continuity, item consistency, scene specificity, scenario density, ending_hook, location, scope
- the checklist is placed between `[필수 조건]` and `[V67] 모순 방지`
- no new template variables are introduced
- the checklist is ~150-250 tokens (7 items)
- a targeted test verifies checklist presence
- zero Python code flow changes in any production module
- zero Stage 2, Stage 4, Director, DB, JSONL, or artifact naming changes

## 11. Verification Plan

- `python -c "import yaml; yaml.safe_load(open('config/prompts/ensemble.yaml', encoding='utf-8'))"` — YAML syntax check
- `python -c "from modules.core.prompt_loader import PromptLoader; p = PromptLoader(); t = p.load('ensemble', 'BLUEPRINT_GENERATION_PROMPT'); assert '자가 검증' in t, 'missing'; print('OK')"` — inline check
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_stage3_blueprint_self_audit_wave.py -q`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_prompt_loader.py -q` — regression
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_tier4_ensemble_caching.py -q` — regression
- `python scripts/check_utf8_hygiene.py config/prompts/ensemble.yaml tests/test_stage3_blueprint_self_audit_wave.py`

## 12. Guardrails

- Re-audit this canonical SSOT against the live workspace before patching.
- This is a prompt-only wave. Do not add Python code flow changes.
- Do not wire ConstitutionalChecker into Stage 3 in this wave.
- Do not reopen the closed Wave 1 clarity/density work.
- Do not add Stage 2, Stage 4, or Director prompt changes.
- Do not change DB schema, JSONL schema, artifact naming, or persistence contracts.
- Do not exceed ~250 tokens for the checklist section.
- Respect UTF-8 hygiene on all touched files.
- If prompt template variables or structure have drifted since baseline, re-verify placement before inserting.

## 13. Temp Queue Notes

- temp mirror path: `docs/temp/stage3-blueprint-self-audit-wave-execution-ssot.md`
- queue rule: this mirror becomes the active temp execution item if promoted
- cleanup condition: remove the temp mirror only after realization plus closure audit
- roadmap dependency: Wave 1 code changes must be committed before this wave executes

## 14. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 15. Opus Execution Order

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md
5. docs/2026-03-25/stage3-blueprint-self-audit-wave-execution-ssot.md

Task:
Implement the Stage 3 blueprint self-audit wave.

Primary goal:
Add a self-audit checklist to the Stage 3 blueprint generation prompt.

Hard constraints:
- Follow the execution SSOT exactly.
- Re-audit the SSOT against the live workspace before patching.
- Prompt-only wave. Do not add Python code flow changes.
- Do not wire ConstitutionalChecker.
- Do not open Stage 2, Stage 4, Director, DB, JSONL, or artifact changes.
- Workspace is dirty. Do not revert unrelated edits.
- Respect UTF-8 hygiene.
- Do not close the execution SSOT; Codex will audit and close it.

Implementation targets:
- config/prompts/ensemble.yaml (self-audit checklist insertion)
- tests/test_stage3_blueprint_self_audit_wave.py (new test)

Acceptance targets:
- BLUEPRINT_GENERATION_PROMPT contains 자가 검증 체크리스트 section with 7 checkbox items
- checklist placed between [필수 조건] and [V67] 모순 방지
- no new template variables, no Python code flow change
- targeted test passes
- regression tests pass

Required verification:
- python -c "import yaml; yaml.safe_load(open('config/prompts/ensemble.yaml', encoding='utf-8'))"
- set PYTHONIOENCODING=utf-8 && pytest tests/test_stage3_blueprint_self_audit_wave.py -q
- set PYTHONIOENCODING=utf-8 && pytest tests/test_prompt_loader.py -q
- set PYTHONIOENCODING=utf-8 && pytest tests/test_tier4_ensemble_caching.py -q
- python scripts/check_utf8_hygiene.py config/prompts/ensemble.yaml tests/test_stage3_blueprint_self_audit_wave.py
```

## 16. Closure Note

Closure Date: 2026-03-25
Closure Status: closed (closure-audited)

Realized scope:
- `config/prompts/ensemble.yaml`: `BLUEPRINT_GENERATION_PROMPT` now includes a bounded `자가 검증 체크리스트` block between `[필수 조건]` and `[V67] 모순 방지`
- `tests/test_stage3_blueprint_self_audit_wave.py`: targeted prompt-presence and placement coverage added

Verification rerun by Codex:
- `python -c "import yaml; yaml.safe_load(open('config/prompts/ensemble.yaml', encoding='utf-8'))"` -> `OK`
- `python -c "from modules.core.prompt_loader import PromptLoader; p=PromptLoader(); t=p.load('ensemble','BLUEPRINT_GENERATION_PROMPT'); assert '자가 검증 체크리스트' in t; print('OK')"` -> `OK`
- `pytest tests/test_stage3_blueprint_self_audit_wave.py -q` -> `13 passed`
- `pytest tests/test_prompt_loader.py -q` -> `29 passed`
- `pytest tests/test_tier4_ensemble_caching.py -q` -> `16 passed`
- `python scripts/check_utf8_hygiene.py config/prompts/ensemble.yaml tests/test_stage3_blueprint_self_audit_wave.py docs/2026-03-25/stage3-blueprint-self-audit-wave-execution-ssot.md docs/temp/stage3-blueprint-self-audit-wave-execution-ssot.md` -> clean
- `python scripts/sync_temp_queue_state.py` -> `ITEMS: 1 / MODE: single` before temp cleanup
- `python scripts/ops_validator.py` -> `errors=0 warnings=0` before temp cleanup

Residual risks:
- self-audit remains prompt-instruction only; real compliance still needs a fresh canary/live run
- checklist is static and does not consume dynamic constitutional context; ConstitutionalChecker wiring remains deferred
- this wave intentionally did not reopen Stage 2, Stage 4, Director, DB, JSONL, or artifact naming lanes
