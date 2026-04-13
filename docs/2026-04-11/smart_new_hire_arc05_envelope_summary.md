# smart_new_hire ARC-05 envelope summary

Date: 2026-04-11
Source: `treatments/smart_new_hire_tr_block_001_draft.json` (saved boundary: Block 50, ARC-05 full)
Authority: read-only extract. The TR file above is the binding truth. This summary is a convenience snapshot, not an authority.
Scope: Block 41-50 only (ARC-05 `본사 정치와 승진 심사`).
Companions: `docs/2026-04-09/smart_new_hire_arc01_envelope_summary.md` · `arc02_envelope_summary.md` · `arc03_envelope_summary.md` · `arc04_envelope_summary.md`.
Role: Block 41-50 self-audit (§1.1C 다섯 번째 10-block gate) deliverable.

## 1. Capital Chain (strict equality, Block 41-50)

| Block | Title | capital_delta |
|---|---|---|
| 41 | 후보표 | + 인사팀 승진 후보표 v1 공식 등재 + '공식 보고 서식 구조의 첫 owner' 프레임 |
| 42 | 누가 키웠나 | + 성장 경로 라벨 v0.1 6줄 구조 + sponsor claim 흡수 |
| 43 | 승진 과제 | + 승진 과제 공식 착수 + 본부별 adaptation 원칙 3개 |
| 44 | 공동권한의 대가 | + 자문 참여 조건 규칙 v0.1 공식 발신 + 직접 adaptation 주도 0건 유지 |
| 45 | 줄 하나의 무게 (quiet) | + 원칙표 v0.5 'title이 아닌 line 아래 위치' 조항 + 심사 자료 직전 금지선 메모 |
| 46 | 심사 자료 | + 승진 심사 자료 v0.1 공식 접수 (owner 이동표 + 반복 손실 감소표, title 열 후순위) |
| 47 | 독자 조건표 | + 독자 조건표 v0.1 공식 부속 등록 (승진 구조 / 독자 line 구조 분리) |
| 48 | 보류 (defeat) | + 승진·독자 line 결정 보류 + 기준표 재심 docket 확보 |
| 49 | 기준표 | + 기준표 v0.1 공식 채택 (3본부 사례 + 보류 1건 병렬) |
| 50 | 승진 | + 승진 발령 + 본사-계열사 공통 개선 독자 line 공식 출범 + 첫 계열사 과제 입장권 |

Block 41-50 capital chain strict equality: verified via UTF-8 inline readback and direct adjacent-string comparison on the live `TR`. Note: `scripts/block_continuity_checker.py` still resolves this work to a `..._block_070_draft.json` path, so the live 001 container was checked directly for this gate.

## 2. Cider Ledger (ARC-05)

| Block | has_cider | receipt_type | pain_only_exit | notes |
|---|---|---|---|---|
| 41 | true | visible_token | false | 승진 후보표 등재 + 인사팀장/승진 심사 실무자 등장 |
| 42 | true | visible_token | false | 성장 경로 라벨 6줄 구조 + sponsor claim 흡수 |
| 43 | true | reevaluation | false | 승진 과제 공식 착수 + 본사 공용 프레이밍 재명명 |
| 44 | true | reevaluation | false | 자문 참여 조건 규칙 v0.1 + 직접 adaptation 주도 0건 유지 |
| 45 | false | null | false | quiet block, `is_quiet_block: true`, 원칙표 v0.5 + 심사 자료 직전 금지선 메모 — Phase0 `quiet_blocks: [45]` lock |
| 46 | true | proof | false | 승진 심사 자료 v0.1 공식 접수, owner 이동표 + 반복 손실 감소표 앞장 고정 |
| 47 | true | reevaluation | false | 독자 조건표 v0.1 면담 기록 부속 등록, 승진 구조 / 독자 line 구조 분리 |
| 48 | false | null | false | defeat block, `is_defeat_block: true`, 승진·독자 line 동시 보류, 기준표 재심 docket 확보 — Phase0 `defeat_blocks: [48]` lock |
| 49 | true | proof | false | 기준표 v0.1 재심 기준 문서 채택, 3본부 사례 + 보류 1건 병렬 |
| 50 | true | next_gate_opening | false | 승진 발령 + 본사-계열사 공통 개선 독자 line + 첫 계열사 과제 입장권 |

Pain_only_exit 전 블록 `false` — contamination guard 준수.

## 3. Quiet / Defeat Audit

### 3.1 Quiet Block Audit (Block 45)

Phase0 lock: `ARC-05 quiet_blocks: [45]`.

- `is_quiet_block: true`, `has_cider: false`, `tension_level: 3`, `emotional_beat: reflection/4`
- 외부 자산 변화: 0
- 내부 자산 추가: 원칙표 v0.5 'title이 아닌 어느 line 아래 위치가 역할을 정의한다' 조항 + 심사 자료 직전 금지선 메모 + 반복 문제 패턴표 v0.1 `title vs line 아래 위치`
- quiet 경계가 blank-opponent softness로 끝나지 않도록 internal opponent(`title 중심 분류` 본능)를 명시

### 3.2 Defeat Block Audit (Block 48)

Phase0 lock: `ARC-05 defeat_blocks: [48]`.

- 공격 축: `과잉 개입` + `단일 line 의존`
- 공격 목적: 승진과 독자 line을 둘 다 보류시키되, 가능하면 나중에 분리 판정으로 끊어 먹는 것
- 결과: 승진·독자 line 동시 보류, 단 `재심 기준표 제출 후 동일 docket 재검토` 메모 확보
- 회수 경로:
  - Block 48: 보류 사유를 구조 항목으로 번역해 재심 docket 확보
  - Block 49: 성공 3건 + 보류 1건 병렬 기준표로 구조 재사용 가능성 증명
  - Block 50: 승진 여부와 독자 line 여부를 같은 문서에서 분리하지 못하게 고정

## 4. Callback / Foreshadow Matrix (ARC-05)

| Block | callback_sources | foreshadow_targets |
|---|---|---|
| 41 | 3, 10, 25, 27, 30, 40 | 46, 47, 48, 50 |
| 42 | 34, 40, 41 | 46, 47, 48, 50 |
| 43 | 35, 40, 42 | 44, 46, 47, 48, 50 |
| 44 | 30, 32, 34, 38, 39, 40, 43 | 47, 48, 49, 50 |
| 45 | 8, 13, 14, 25, 28, 34, 40, 41, 42, 43, 44 | 46, 47, 48, 49, 50 |
| 46 | 19, 35, 40, 42, 43, 44, 45 | 47, 48, 49, 50, 51 |
| 47 | 20, 30, 35, 38, 39, 42, 43, 44, 45, 46 | 48, 49, 50, 51, 52 |
| 48 | 17, 25, 37, 38, 44, 45, 46, 47 | 49, 50, 51, 52 |
| 49 | 24, 26, 28, 29, 34, 38, 40, 44, 45, 47, 48 | 50, 51, 52, 53 |
| 50 | 30, 38, 39, 40, 41, 42, 44, 45, 47, 48, 49 | 51, 52, 53, 60 |

Invariants: callback_sources backward-only (< block_no), foreshadow_targets forward-only (> block_no) — inline check `PASS`.

## 5. ARC-05 Exit State → ARC-06 Entry Gate

- 최종 자원 상태(`Block 50 capital_after`): 공동권한 실체 + budget pre-check + ARC-05 심사 진입 자산 + 승진 심사 자료 v0.1 + 독자 조건표 v0.1 + 보류 defeat의 재심 docket + 기준표 v0.1 + 승진 발령 + 본사-계열사 공통 개선 독자 line 공식 출범 + 첫 계열사 과제 입장권
- ARC-05 exit 조건(Phase0 locked `capital_target`): 공동권한 → 승진 + 독자 line ✅
- ARC-05 exit_function(Phase0 locked): 도혁은 승진과 함께 독자 라인을 얻는다 ✅
- ARC-06 entry_function(Phase0 locked): 도혁의 기준표가 계열사급 판에서도 먹히는지 검증하는 아크
- ARC-06 Block 51 slot: `첫 계열사` — 독자 라인을 들고 첫 계열사 개선 과제에 들어간다

## 6. Self-Audit Trail

Block 41-50 gate evidence (2026-04-11):

- inline A5 capital chain strict equality Block 41-50: PASS
- inline callback_sources backward-only: PASS
- inline foreshadow_targets forward-only: PASS
- Phase0 quiet lock `Block 45`: PASS
- Phase0 defeat lock `Block 48`: PASS
- metadata `_total_blocks=50 / _saved_block_boundary=50 / _next_continuation_boundary=51`: PASS
- Stage 0 handoff validator (`scripts/stage0_handoff_validator.py --work-id smart_new_hire`): PASS
- whole-run pacing triage: `GREEN`
- opening pacing triage: `YELLOW` (`legacy_heuristic` only, opening contract undeclared)
- `material_ssot` validator: PASS

Overall: ALL PASS for the Block 41-50 gate. Next decision is no longer continuation-by-default; it is the post-`B50` choice among `opening manual re-audit`, optional `BI`, or optional `work_guard` retrofill by fresh operator order.
