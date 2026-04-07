# Stage4 Container And PWF Survey

Date: 2026-04-07
Status: final
Scope: system-track survey-only
Canonical Path: `docs/2026-04-07/stage4-container-and-pwf-survey.md`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Container Verdict

Stage4 has the strongest `dict` envelope usage in the surveyed runtime.

- Retrieval/context payload families are `TypedDict`.
  - `modules/core/stage4_context_builder.py:65-130`
- Interview/runtime shared carriers are dataclasses with nested dict/list fields.
  - `modules/core/stage4_types.py:15-88`
- Context packet assembly also uses dict-shaped inputs with list collections inside.
  - `modules/core/stage4_context_packets.py:28-84`
  - `modules/core/stage4_context_packets.py:140-191`
- Quantitative readback over targeted Stage4 files: `dict_literals=1467`, `list_literals=1232`, `TypedDict=10`.

Interpretation:

- Stage4 is not "list-first".
- It is `dict`-first with many nested lists for scenes, NPCs, history rows, and packet sections.

## 2. PWF Verdict

Stage4 PWF is a strict local-fix contract, not a diff contract.

- `PASS_WITH_FIX` is eligible only when `fix_scope == "inplace"` and a local-fixable `fix_pack` is ready.
  - `modules/core/stage4_interview_round.py:2082-2120`
- The fix pack itself is structured, not textual diff output:
  - `patch_targets`
  - `must_fix`
  - `do_not_regress`
  - `success_condition`
  - `target_kind`
  - `modules/core/stage4_interview_round.py:2122-2147`
- Strong advisory escalation is downgraded to `REJECT` when the local fix contract is not ready.
  - `modules/core/stage4_interview_round.py:2750-2778`
- The structural writer prompt explicitly says "target scene block only" and returns JSON `patched_blocks`.
  - `config/prompts/chief_writer.yaml:124-165`
  - `modules/domain/agents/chief_writer.py:1447-1468`
  - `modules/domain/agents/chief_writer.py:1482-1534`

This is the clearest proof that current Stage4 PWF is not diff-shaped:

- the model is instructed not to rewrite the full manuscript
- it must edit only selected scene blocks
- it must return scene-id keyed patch payloads

## 3. Cross-Cut Prompt Contract Evidence

Director-side prompt guidance also asks for concrete modification instructions rather than diff hunks.

- `re_slice_instruction`: `"제N화에서 X 대신 Y를 하라", "아이템 Z를 삭제하고 W로 대체하라"` style
  - `modules/domain/agents/director_prompts.py:295-302`

So the Stage4 repair stack is:

- Director instruction
- gate validation on locality
- fix pack construction
- scene-targeted patch payload

not:

- textual diff
- line-hunk patch
- generic "improve quality" without location or scope

## 4. Side-Effect Notes

Applicable side effects reviewed:

- gate semantics mutation around `fix_scope`
- repair eligibility downgrade from `PASS_WITH_FIX` to `REJECT`
- chief writer structural patch invocation
- patch trace / state update payload handling

## 5. 3-Pass Audit Record

### Pass 1. Structure and Scope

- Limited to Stage4 runtime carriers, gate semantics, and structural patch path.

### Pass 2. Evidence and Consistency

- PWF verdict was anchored to both gate code and prompt template, not only to log strings.

### Pass 3. Execution and Readability

- Final answer gives an operator-usable rule: Stage4 accepts only local, scene-targeted, contract-valid repairs; it does not use diff-style feedback.

Confidence: `98%`
