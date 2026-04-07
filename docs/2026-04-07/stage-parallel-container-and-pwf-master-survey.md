# Stage-Parallel Container And PWF Master Survey

Date: 2026-04-07
Status: final
Scope: system-track survey-only
Canonical Path: `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
Companion Stage Docs:
- `docs/2026-04-07/stage0-container-and-pwf-survey.md`
- `docs/2026-04-07/stage2-container-and-pwf-survey.md`
- `docs/2026-04-07/stage3-container-and-pwf-survey.md`
- `docs/2026-04-07/stage4-container-and-pwf-survey.md`
Queue Context:
- `docs/temp/execution-roadmap.md` is already the active temp controller for the current execution queue.
- This survey is documentation-only and does not modify the active temp queue.

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. User Questions

1. 우리는 현재 `list` 와 `dict` 중 무엇을 주로 사용하는가?
2. `PWF` 는 diff 스타일 피드백인가, 아니면 "어디를 어떻게 수정하라" 식의 수정 지시형 피드백인가?

## 2. Executive Verdict

- 전체 authoritative contract 기준으로는 `dict` envelope 우세다.
- `list` 는 반복 항목 payload에 광범위하게 쓰이지만, 대개 `dict` 안쪽의 반복 슬롯으로 들어간다.
- 유일하게 `list` 가 상대적으로 강하게 남아 있는 곳은 Stage0 raw `treatment` 런타임 경로다. 다만 canonical handoff는 `dict.blocks` 로 정규화된다.
- `PWF` 는 unified diff 또는 line-based patch text를 주는 방식이 아니다.
- 현재 구현은 `fix_scope` + `re_slice_instruction` + Stage4 `fix_pack` / `patch_targets` 기반의 local repair contract다.
- 즉, "몇 문단/몇 씬/어떤 필드를 어떤 방향으로 고쳐라" 쪽이 맞고, Stage4에서는 그 지시가 scene-targeted JSON patch payload까지 강화되어 있다.

## 3. Stage Matrix

| Stage | Container Verdict | PWF Verdict | Key Evidence |
| --- | --- | --- | --- |
| Stage0 | mixed runtime, but canonical handoff is `dict` with nested `blocks: list[...]` | no PWF loop | `modules/core/stage0/__init__.py`, `modules/core/stage0_handoff.py`, `modules/core/response_schemas.py` |
| Stage2 | `dict`-dominant | instruction-driven local patch only when `fix_scope=inplace` | `modules/core/stage2_orchestrator.py`, `modules/core/stage2_finalizer.py`, `modules/core/stage2_contracts.py` |
| Stage3 | `dict`-dominant with nested lists | instruction-driven local patch; `re_slice_instruction` preferred over generic feedback | `modules/models/blueprint.py`, `modules/domain/agents/unified_blueprint_validator.py`, `modules/domain/agents/three_phase_blueprint_runtime.py` |
| Stage4 | strongest `dict` envelope usage; lists remain nested collections | strict local-fix contract, not diff; requires `fix_scope=inplace` and ready `fix_pack` | `modules/core/stage4_context_builder.py`, `modules/core/stage4_interview_round.py`, `modules/domain/agents/chief_writer.py`, `config/prompts/chief_writer.yaml` |

## 4. Quantitative Readback

Targeted AST readback over authoritative stage files:

- Stage0: `dict_literals=353`, `list_literals=434`
- Stage2: `dict_literals=384`, `list_literals=278`, `TypedDict=8`
- Stage3: `dict_literals=420`, `list_literals=312`
- Stage4: `dict_literals=1467`, `list_literals=1232`, `TypedDict=10`

Interpretation:

- Raw syntax volume alone does not decide the contract.
- But Stage2-4 all show both syntactic and contract-level `dict` dominance.
- Stage0 is the only mixed outlier because generator/runtime code still carries raw list treatment handling while the canonical handoff layer wraps it back into `dict.blocks`.

## 5. Question-Level Answer

### Q1. List vs Dict

Current workspace practice is:

- authoritative cross-stage payloads: mostly `dict`
- repeated collections inside those payloads: mostly `list`
- Stage0 raw treatment path: still `list[dict]`
- Stage0 canonical treatment path: `dict` wrapper with `blocks: list[dict]`

So the short answer is:

- "주로 무엇을 신뢰해야 하느냐" 기준이면 `dict`
- "실제 내부 반복 데이터까지 포함한 체감 사용량" 기준이면 `dict` envelope + `list` collections의 혼합 구조

### Q2. PWF feedback style

Current PWF style is:

- not diff text
- not unified patch hunks
- explicit repair instructions plus bounded repair scope
- Stage2/3: `re_slice_instruction` string drives the local patch or regenerate route
- Stage4: `fix_pack.patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind` and `patched_blocks` JSON drive the local patch route

So the correct characterization is:

- `"뭐를 수정해라"`가 기본
- Stage3/4로 갈수록 `"어느 씬/어느 로컬 포인트를 수정해라"` 수준으로 더 구체화됨
- Stage4 structural patch는 사실상 "target scene block만 수정" 계약이다

## 6. Side-Effect Coverage

Applicable surfaces reviewed:

- Stage handoff payload contracts
- local patch loop eligibility rules
- operator-visible retry / patch logs
- Stage4 structural patch payload contract

Not primary for this order:

- DB write semantics
- artifact content truth beyond contract-bearing code paths
- live-run verification

## 7. Non-Goals

- This survey does not reprioritize the existing temp execution queue.
- This survey does not create execution SSOT mirrors.
- This survey does not patch runtime code.

## 8. 3-Pass Audit Record

### Pass 1. Structure and Scope

- Survey-only scope kept explicit.
- Active temp queue was inspected and recorded as context only.
- Stage split was fixed to Stage0 / Stage2 / Stage3 / Stage4 because no separate Stage1 contract surface was authoritative for these questions.

### Pass 2. Evidence and Consistency

- Answers were anchored to live code first, not stale survey text.
- Stage0 mixed-runtime conclusion was constrained by canonical wrapper evidence in `stage0_handoff` and `response_schemas`.
- Stage2/3/4 PWF conclusions were anchored to `fix_scope`, `re_slice_instruction`, `fix_pack`, and `patched_blocks` code paths.

### Pass 3. Execution and Readability

- Final answers were reduced to operator-usable decisions: trust `dict` envelopes; treat PWF as targeted repair contract, not diff.
- Stage companion docs were separated so later follow-up can drill into a single stage without re-reading the whole survey.

Confidence: `97%`
