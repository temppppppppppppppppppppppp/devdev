# 000__t Stage 3 10화 로그 감리 후속 수정 실행 SSOT

작성일: 2026-03-12  
대상 프로젝트: `projects/000__t`  
기준 감사 문서: `docs/2026-03-12/stage3-10ep-log-full-survey-3pass-audit.md`

## Summary

- 이번 실행 SSOT는 Stage 3 10화 로그 감리에서 남은 retained finding `P1 1건`만 수정 대상으로 고정한다.
- 대상 문제는 `Stage 3 Director 비교 선택 lifecycle이 DB director_selections(stage=3)에 저장되지 않는 observability debt`다.
- `runtime success` 자체는 이미 확보됐으므로, 이번 수정은 생산 로직 변경이 아니라 `audit persistence 보강`에 국한한다.
- `BPEnsemble/Director 비교 선택 WARNING severity`와 `retrieval sparse profile`은 이번 수정 범위에서 제외한다. 둘 다 observation이지 blocker가 아니다.

## Broken Contract

- 현재 계약:
  - Stage 3에서 Director 비교 선택이 수행되면, 최종 선택 결과는 `stage_attempts(stage=3)`에 저장된다.
- 깨진 계약:
  - 후보 비교 lifecycle과 선택 reasoning을 복원할 수 있는 `director_selections(stage=3)` row는 저장되지 않는다.
- 목표 계약:
  - Stage 3 Director 비교 선택이 발생한 경우, Stage 4와 동일한 계열의 최소 selection ledger가 `director_selections`에 저장되어야 한다.

## Scope

- 포함:
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/db_manager.py`
  - 필요한 경우 Stage 3 selection payload를 만드는 helper surface
  - Stage 3 관련 회귀 테스트
- 제외:
  - Stage 3 scoring/rubric 로직 변경
  - blueprint 후보 생성 로직 변경
  - WARNING 로그 severity 조정
  - retrieval context enrichment 변경
  - Stage 4 로직 변경

## Required Outcome

- Episode 1~10과 같은 Stage 3 run에서 Director 비교 선택이 일어났다면 `director_selections(stage=3)` row가 남아야 한다.
- 최소 저장 필드는 아래를 포함해야 한다.
  - `stage`
  - `ep_num`
  - `attempt_key`
  - `selected_candidate_key`
  - `selected_content_hash`
  - `selected_artifact_path`
  - `verdict`
  - `score`
  - 가능한 범위의 selection reasoning / advisory warnings
- 기존 `stage_attempts(stage=3)` 저장은 유지해야 한다.
- Stage 3 runtime success path의 기존 산출물, score, candidate_key, artifact_path 계약을 깨뜨리면 안 된다.

## Change Package

### E-1. Stage 3 selection persistence hook 추가

- `stage3_orchestrator.py`에서 Director 비교 선택 직후 Stage 3 selection payload를 조립한다.
- `save_stage_attempt()`와 별도로 `save_director_selection()` 또는 동등한 Stage 3 저장 경로를 호출한다.
- 저장 시 `stage=3`를 명시한다.

### E-2. Stage 3/Stage 4 selection schema 정렬

- Stage 3에서 저장하는 필드명이 Stage 4 `director_selections`와 불필요하게 어긋나지 않게 맞춘다.
- Stage 3에 존재하지 않는 필드는 비워두되, schema drift를 새로 만들지 않는다.

### E-3. Non-blocking persistence 정책 재확인

- 저장 실패가 blueprint 생산 성공을 뒤집지 않도록 정책을 유지한다.
- 다만 failure는 감리 가능한 로그로 남아야 한다.

### E-4. Regression proof 추가

- Stage 3 run 또는 mock pipeline 기준으로 `director_selections(stage=3)` row 생성 여부를 검증하는 회귀를 넣는다.
- `stage_attempts`와 `director_selections`의 `attempt_key/candidate_key/artifact_path` alignment를 확인한다.

## Acceptance Criteria

- `stage_attempts(stage=3)`는 기존처럼 저장된다.
- `director_selections(stage=3)`가 Stage 3 비교 선택 실행 시 생성된다.
- `attempt_key`, `candidate_key`, `artifact_path`가 두 sink 사이에서 합리적으로 일치한다.
- 기존 Stage 3 test suite 및 관련 회귀에서 score/candidate selection drift가 없어야 한다.
- Stage 3 로그 감리 기준 retained finding이 `closed`로 내려가야 한다.

## Verification

- 우선 회귀:
  - `tests/test_stage3_orchestrator.py`
  - Stage 3 selection persistence를 직접 검증하는 신규 또는 보강 테스트
- 보조 검증:
  - mock DB에서 `director_selections(stage=3)` row count 확인
  - `attempt_key`, `candidate_key`, `artifact_path` alignment 확인

## Non-Goals

- 이번 수정으로 Stage 3 retrieval observation sparse profile을 없애는 것
- 이번 수정으로 운영 로그 warning severity를 정리하는 것
- Stage 3를 처음부터 rerun하는 것

## Final Deliverable

- 코드 수정
- 관련 회귀 테스트
- 수정 후 3-pass 감리 결과
- 최종 판단: `closed` 또는 `residual observation only`
