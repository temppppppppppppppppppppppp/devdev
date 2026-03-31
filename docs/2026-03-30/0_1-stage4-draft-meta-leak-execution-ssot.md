# 0_1 Stage4 Draft Meta Leak Execution SSOT

Date: 2026-03-30
Status: active-partial
Scope: reader-facing scene-header / bracket-cue leak only
Canonical Survey: `docs/2026-03-30/0_1-stage4-draft-meta-leak-bounded-survey.md`
Temp Mirror Path: deferred

Commit State:
- Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
- Baseline Dirty Summary: `dirty: tracked stage4 runtime files/tests plus live-run logs/db artifacts and EP8 docs; active python main_a.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Governing Decision

이 execution SSOT는 `scene scaffold는 내부에서 유지하되 reader-facing final manuscript에는 남기지 않는다`를 기준으로 한다.

즉:

- Writer prompt의 구조화 scene draft는 유지
- Director / pre-director의 내부 scene contract도 당장은 유지
- 최종 DB manuscript / draft export 직전에서만 reader-facing normalization 수행

## 2. Execution Lanes

### Lane 1. Runtime normalization patch

Status: done

Target:
- `modules/core/stage4_post_processor.py`

Implemented:
- `_normalize_reader_facing_manuscript()`
- `_is_stage_cue_line()`
- `_SCENE_HEADER_LINE_RE`
- `_STANDALONE_STAGE_CUE_RE`
- `process_pass_result()` 초반에 normalization 주입

Contract:
- first `### 씬` header는 제거
- subsequent `### 씬` header는 `***`로 치환
- standalone bracket cue line은 plain cue line으로 정규화
- 저장/sidecar/export는 모두 normalized manuscript 사용

### Lane 2. Regression and hygiene

Status: done

Touched tests:
- `tests/test_stage4_post_processor.py`

Added coverage:
- `test_normalize_reader_facing_manuscript_strips_scene_headers_and_brackets`
- `test_process_pass_result_persists_normalized_reader_facing_manuscript`

Adjusted coverage:
- `test_chain_link_fn_called`
  - normalization 이후 chain-link extractor가 normalized manuscript를 받는 contract로 expectation 갱신

Validation:
- `python -m pytest tests/test_stage4_post_processor.py tests/test_stage4_pass_artifact_contract.py -q`
  - `86 passed`
- `ruff check modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`
  - pass
- `python scripts/check_utf8_hygiene.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`
  - pass

### Lane 3. Existing artifact backfill

Status: deferred-post-run

Authority:
- `projects/0_1/project_data.db` `manuscripts`
- `projects/0_1/drafts/ep_*.txt` is export mirror

Reason deferred:
- execution 시점에 `python main_a.py` live process가 active
- 사용자 지시: `런 중이야 db를 바로 수정하지는 마`

Deferred action:
1. live run 종료 확인
2. `manuscripts` authoritative read-back
3. same normalization contract로 `ep_0001`~`ep_0008` backfill
4. draft export sync
5. DB/txt read-back verification

### Lane 4. Fresh run confirmation

Status: pending-after-restart

Goal:
- 다음 Stage 4 PASS artifact에서 `### 씬` header와 bracket cue line이 draft/DB에 재유입되지 않는지 확인

Evidence to inspect:
- new `stage_attempts`
- new manuscript DB row
- exported `drafts/ep_XXXX.txt`

## 3. Non-Goals

- writer prompt contract 전면 재설계
- pre-director scene-header checker 제거
- scene count contract 변경
- docs/temp queue 갱신

## 4. Explicit Answers

### 4.1 `***` 장면 전환 기호로 써도 되나

이번 bounded patch에서는 `된다`.

- 첫 장면 title header는 독자용 결과물에 불필요하므로 제거
- 이후 장면 전환은 reader-facing 최소 표식으로 `***` 사용

### 4.2 씬은 꼭 4분할인가

`정확히 4분할`은 아니다.

- Director minimum은 `4개 이상`
- calibration 선호 구간은 `4~7`

이번 문제의 본질은 scene count가 아니라 `scene scaffold leak`이다.

## 5. Current Go / No-Go

- code patch completion: `go`
- docs canonical save: `go`
- existing DB/draft backfill now: `no-go`
  - live run active
- post-run backfill: `go`

## 6. Closure Rule

이 항목은 아직 closure 상태가 아니다.

closure 조건:
1. live run 종료
2. `0_1` manuscript authoritative backfill 완료
3. export sync 완료
4. fresh Stage 4 artifact 1건 이상에서 leak 미재발 확인

## 7. 3-Pass Audit Note

- Pass 1: survey evidence와 code realization 일치 확인
- Pass 2: test/hygiene/ruff 검증 결과 반영
- Pass 3: live-run guardrail과 deferred lane 상태 재확인

Confidence: 0.97
