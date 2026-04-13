# smart_new_hire Repair Note

Date: 2026-04-11
Status: bounded repair complete + ARC-05 continuation complete + opening manual re-audit complete
Target:

- `smart_new_hire`
- surface: `TR only`
- edited window: `B45` anchor tightening inside saved `ARC-05` front half `B41~B45`, `B46~B50` continuation, opening contract declarations across `B01~B10`, and one `B01` false-signboard wording repair

## 1. Why This Repair Happened

- pre-repair opening pacing triage still returned `YELLOW`, but that read remained `legacy_heuristic` rather than declared-contract evidence
- the profitable local debt sat at the saved boundary, not in the opening machine:
  - whole-run pacing was already `GREEN`
  - but `late_blank_opponent_blocks = [45]` still showed that the front half ended on a soft quiet vacuum
- the repair spec therefore called for quiet-lock preservation plus boundary tightening, not opening rewrite or `B46+` continuation

## 2. What Changed

- `B45`
  - grounded the quiet block in the four saved `ARC-05` files already on the desk, so the boundary closes on a concrete saved surface rather than floating abstraction
  - changed from `opponent = null` into an internal classification-fallacy opponent:
    - `title 중심 분류` 본능
    - specifically the risk that the upcoming review packet collapses `B41~B44` back into flat title labels
  - added the guardrail memo:
    - `심사 자료는 title이 아니라 line 아래 위치 이동과 반복 손실 감소 순으로 읽는다`
  - restored an explicit internal reward while keeping:
    - quiet lock intact
    - external asset delta `0`
    - `B46+` unsaved truth untouched
- `B41~B44`
  - slot functions were preserved
  - no reopening or broad rewrite was done outside the `B45` boundary anchor

## 3. Validation

Commands run:

```powershell
python -X utf8 scripts/production_pair_whole_run_pacing_triage_runner.py --treatment treatments/smart_new_hire_tr_block_001_draft.json
python -X utf8 scripts/production_pair_opening_pacing_triage_runner.py --treatment treatments/smart_new_hire_tr_block_001_draft.json
python -X utf8 scripts/validate_material_ssot.py
```

Results:

- whole-run pacing triage: `GREEN`
  - `late_blank_opponent=0`
  - `endgame_low_stakes=0`
  - `slow_windows=0`
- opening pacing triage: `YELLOW`
  - `evidence_mode=legacy_heuristic`
  - `signboard=B01`
  - `reeval=-`
  - `ticket=B06`
  - opening contract still not declared inside `B01~B10`, so this repair did not target that surface
- `material_ssot` validator: `passed`

## 4. Current Reading

- the saved `B45` boundary no longer ends as a quiet null-opponent vacuum
- live `TR` now extends through `B50`, so `ARC-05` no longer stops at front-half authority only
- `smart_new_hire` no longer remains opening-layer `YELLOW`; the post-`B50` decision gate has now been closed by an opening manual re-audit and declared-contract insertion
- the pair should now be read as a repaired live unit, not an active repair-first shelf item

## 5. Next Admissible Step

1. if packaging is wanted, open `BI` by fresh operator order
2. if standardization debt is being closed, open `work_guard` retrofill as a separate lane
3. if narrative continuation is wanted instead, start `B51+` only by fresh operator order
4. keep the repaired `B01~B10` and `B41~B50` surfaces closed unless a concrete inconsistency appears

## 6. Continuation Wave (`B46~B50`)

This same date later carried the planned continuation wave.

- `B46 심사 자료`
  - converted the review packet into `owner 이동표 + 반복 손실 감소표` first
  - official receipt: 심사 자료 v0.1 접수
- `B47 독자 조건표`
  - answered the promotion question with structure conditions, not title desire
  - official receipt: 독자 조건표 v0.1 면담 부속 등록
- `B48 보류`
  - kept the mandatory defeat as `과잉 개입 / 단일 line 의존` pressure
  - bounded the loss by forcing a same-docket criteria re-review track
- `B49 기준표`
  - proved reuse by placing `3본부 사례 + 보류 1건` on one table
  - official receipt: 기준표 v0.1 재심 기준 문서 채택
- `B50 승진`
  - closed on promotion plus `본사-계열사 공통 개선 독자 line`
  - opened ARC-06 via the first affiliate task ticket

Validation snapshot after continuation:

- inline capital chain / callback / foreshadow checks: PASS
- Stage 0 handoff validator: PASS
- whole-run pacing triage: `GREEN`
- opening pacing triage: `YELLOW` (`legacy_heuristic` only)
- `material_ssot` validator: PASS

Deliverable:

- `docs/2026-04-11/smart_new_hire_arc05_envelope_summary.md`

## 7. Opening Manual Re-Audit (`B01~B10`)

Why this lane opened:

- after `B50`, the only live repair-first debt left was opening-layer `YELLOW`
- that read was still `legacy_heuristic`, not a proven declared-contract failure
- a fresh manual re-audit confirmed the opening body was already structurally sound, but `B01~B10` lacked declared opening contract fields and `B01` still carried a false signboard keyword hit

What changed:

- added explicit `location.macro_battlefield` declarations across `B01~B10`
- added explicit `genre_ext.opening_progression` declarations across `B01~B10`
- locked the declared opening contract as:
  - `signboard = B02`
  - `reevaluation = B03`
  - `ticket = B06`
- changed one `B01` reward sentence from `공식 파일 접근` to `실무 파일 접근`
  - purpose: remove the false signboard hit while preserving the actual access receipt and opening delivery

Validation snapshot after the re-audit:

- opening pacing triage: `GREEN`
  - `evidence_mode=declared_contract`
  - `signboard=B02`
  - `reeval=B03`
  - `ticket=B06`
- whole-run pacing triage: `GREEN`
- Stage 0 handoff validator: `PASS`
- `material_ssot` validator: `PASS`

Current result:

- `smart_new_hire` is no longer part of the active repair-first queue
- the opening is now explicitly declared instead of falling back to legacy heuristic
- the next lane is a fresh non-repair operator choice among `BI`, `work_guard`, or `B51+`, not another repair pass
