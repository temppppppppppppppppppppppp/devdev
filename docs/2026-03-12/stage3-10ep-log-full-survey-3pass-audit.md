# 000__t Stage 3 10화 로그 전수조사 3Pass 감리 보고서

작성일: 2026-03-12  
대상 프로젝트: `projects/000__t`  
조사 범위: Stage 3 10화 생산 로그, DB, blueprint 산출물, stage3 artifact, 관련 코드 surface

## Executive Summary

- 최종 판정: `runtime success / observability debt 1건 / observation 2건`
- 생산 결과는 정상이다. `stage3_complete`, `db_commit=10`, `blueprint_success=10`, blueprint 파일 10건, stage3 artifact 10건이 서로 맞는다.
- retained finding은 `P1 1건`이다. Stage 3에서 Director 비교 선택이 실제로 수행됐지만 `director_selections` 테이블에는 Stage 3 row가 저장되지 않는다.
- `P0`는 없다. Traceback, Exception, FAIL, rollback, artifact missing, mojibake는 이번 조사 기준으로 확인되지 않았다.
- 감리 확신도는 `95%`다. 이 값은 `감리 판단의 확신도`이지 `시스템 무결함 100%`를 뜻하지 않는다.

## 조사 근거

- 세션 로그: `projects/000__t/logs/session_20260312_225025.log`
- 런타임 요약: `projects/000__t/logs/runtime_audit_summary.json`
- 품질 로그: `projects/000__t/logs/quality_metrics.jsonl`
- DB: `projects/000__t/project_data.db`
- blueprint 산출물: `projects/000__t/plans/blueprints/blueprint_0001.txt` ~ `blueprint_0010.txt`
- stage3 artifact: `projects/000__t/logs/artifacts/stage3/ep_0001/...` ~ `ep_0010/...`
- 교차검증 코드:
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/db_manager.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `tests/test_stage3_orchestrator.py`
  - `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-report-OPUS.md`

## 기준선

- 최신 Stage 3 세션 로그는 `session_20260312_225025.log`다.
- `runtime_audit_summary.json`은 `tag=stage3_complete`를 기록한다.
- `counts.db_commit=10`, `counts.blueprint_success=10`이다.
- DB `stage_attempts WHERE stage = 3`는 총 10행이며 verdict는 전부 `PASS`다.
- 점수 분포는 `99, 100, 100, 100, 98, 100, 100, 99, 100, 100`이다.
- blueprint 파일 수 10건, stage3 final artifact 수 10건으로 정합성이 맞는다.

## Pass 1: 사실 수집

### 1. 런타임 성공 여부

- 세션 로그에서 Stage 3 실행은 10화까지 끊김 없이 진행됐다.
- `runtime_audit_summary.json` 기준 종료 태그는 `stage3_complete`다.
- DB commit 수와 blueprint success 수가 모두 10으로 일치한다.
- stage3 `stage_attempts`는 10건 모두 `PASS`다.

### 2. 산출물 정합성

- `plans/blueprints` 아래 blueprint 파일이 10건 존재한다.
- `logs/artifacts/stage3/.../final_blueprint__*.json`도 10건 존재한다.
- DB `stage_attempts`의 `artifact_path`는 실제 artifact 경로와 일치한다.

### 3. 품질 로그 상태

- `quality_metrics.jsonl`에서 Stage 3 validation row는 10건이다.
- 점수는 DB와 동일하게 `98~100` 범위다.
- validation warnings는 10화 전부 `0`이다.
- Stage 3 retrieval observation은 10건 존재한다.
- 모든 row에서 `advisor_path_used=true`다.
- 모든 row에서 `planned_slots_count=3 또는 4`다.
- 모든 row에서 `work_focus_present=false`, `tracking_slots_count=0`, `registry_profiles_count=0`, `relation_slice_included=false`, `protected_summary_survived=false`다.

## Pass 2: 교차 검증

### 1. Director 비교 선택 실행 여부

- 세션 로그에는 Episode 1~10 전 구간에 `Director 비교 선택 모드`가 반복적으로 남아 있다.
- 예시 라인:
  - `session_20260312_225025.log:259`
  - `session_20260312_225025.log:389`
  - `session_20260312_225025.log:516`
  - `session_20260312_225025.log:643`
  - `session_20260312_225025.log:794`
  - `session_20260312_225025.log:925`
  - `session_20260312_225025.log:1048`
  - `session_20260312_225025.log:1179`
  - `session_20260312_225025.log:1354`
  - `session_20260312_225025.log:1481`
- Episode 4에서는 후보 1이 분량 미달로 REJECT 처리된 뒤 후보 2가 선택됐다. 이는 filtering이 실제로 작동했음을 보여준다.

### 2. Stage 3 observability 필드 저장 여부

- 과거 문서에서 문제였던 `save_stage_attempt()`의 `duration_ms` / `advisory_flags` 누락은 현재 기준으로 재현되지 않았다.
- `stage3_orchestrator.py`는 `save_stage_attempt(..., duration_ms=_duration_ms, advisory_flags=_observability_flags or None)`를 호출한다.
- DB `stage_attempts` row도 advisory_flags를 실제로 보유한다.
- 따라서 이 축은 기존 finding이 아니라 `closed`로 보는 것이 맞다.

### 3. director_selections 저장 여부

- DB `director_selections WHERE stage = 3` count는 `0`이다.
- 반면 로그와 `stage_attempts`는 Stage 3 Director 선택이 실제로 일어났음을 보여준다.
- `db_manager.py`에는 `save_director_selection()`이 존재한다.
- 그러나 `stage3_orchestrator.py`에서는 `save_stage_attempt()`는 호출하지만 `save_director_selection()` 호출은 없다.
- 이 불일치는 Stage 3 selection lifecycle이 DB에 완전하게 남지 않는다는 뜻이다.

### 4. retrieval observation의 sparse profile 해석

- `work_focus_present=false`, `tracking_slots_count=0`, `registry_profiles_count=0`, `relation_slice_included=false`는 10화 전부 동일하다.
- 이 패턴만으로 곧바로 결함으로 올리지는 않았다.
- 이유:
  - `tests/test_stage3_orchestrator.py`는 `work_focus_present=false` case를 허용한다.
  - `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-report-OPUS.md`도 경량 설정에서는 동일 패턴이 가능하다고 적고 있다.
- 따라서 이번 감리에서는 `Observation`으로만 남긴다.

## Pass 3: 오탐 제거

### 1. runtime failure 오탐 제거

- `Traceback`, `Exception`, `FAIL`, rollback, artifact missing은 세션 로그와 산출물에서 확인되지 않았다.
- `fallback_entry`, `npc ... fallback=true`는 vector/npc retrieval degrade path 로그다.
- 현재 evidence만으로는 Stage 3 실패나 결함으로 승격할 수 없다.

### 2. mojibake 오탐 제거

- PowerShell 표시상 한글이 깨져 보이는 구간이 있었지만 Python 직접 판독으로 재검증했다.
- `plans/blueprints/blueprint_0001.txt`의 `U+FFFD` count는 `0`이다.
- `logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json`의 `U+FFFD` count도 `0`이다.
- 따라서 이번 Stage 3 산출물 기준 mojibake는 retained finding이 아니다.

### 3. warning log 과대해석 제거

- `[BPEnsemble] 3개 후보 병렬 생성 중...`와 `[V60.85] Director 비교 선택 모드`가 `WARNING` severity로 남는다.
- 그러나 이 둘은 실제 실패 이벤트가 아니라 정상 control-flow 로그다.
- 이는 `운영 가시성 debt`이지 runtime correctness 결함은 아니다.

## Retained Findings

### P1. Stage 3 Director selection lifecycle이 DB `director_selections`에 저장되지 않음

- 깨진 계약:
  - Stage 3에서 Director 비교 선택이 수행되면 사후 감리용 selection lifecycle도 DB에 남아야 한다.
- 직접 근거:
  - 세션 로그에 Episode 1~10 전체 `Director 비교 선택 모드` 존재
  - DB `stage_attempts(stage=3)` 10건 존재, verdict 모두 `PASS`
  - DB `director_selections(stage=3)` count는 `0`
  - `db_manager.py`에는 `save_director_selection()` 구현 존재
  - `stage3_orchestrator.py`에서는 `save_stage_attempt()`만 호출하고 `save_director_selection()` 호출 없음
- 반대 근거 검토:
  - `stage_attempts`에 candidate_key/content_hash/artifact_path/advisory_flags가 남으므로 selection 결과 일부는 복원 가능하다.
  - 그러나 candidate 간 비교 reasoning, selection lifecycle, direct selection ledger는 복원되지 않는다.
- 왜 오탐이 아닌가:
  - 단순 로그 부재가 아니라, 로그/DB/코드 세 층 모두가 같은 gap를 가리킨다.
- 사용자 영향:
  - Stage 3 후보 비교 사후 감리, selection drift 분석, audit replay가 Stage 4보다 약하다.
- 런타임 blocker 여부:
  - 아니다. 생산 성공 자체를 막지는 않는다.
- 최종 상태:
  - `confirmed`

## Observations

### Observation 1. 정상 control-flow가 WARNING severity로 기록됨

- `blueprint_ensemble.py`의 후보 병렬 생성 안내와 `unified_blueprint_validator.py`의 Director 비교 선택 시작 안내가 `WARNING`으로 남는다.
- log scan 시 false alarm을 늘리지만 동작 결함은 아니다.

### Observation 2. Stage 3 retrieval observation은 sparse profile이지만 현재 evidence로는 defect로 승격 불가

- `advisor_path_used=true`, `planned_slots_count=3/4`, `vector_context_chars=2795~3031`인 점은 의미 있는 semantic context가 실제로 들어갔음을 보여준다.
- 동시에 `work_focus_present=false`, `tracking_slots_count=0`, `registry_profiles_count=0`, `relation_slice_included=false`가 전 화수 공통이다.
- 현재 테스트와 운영 문서가 이 패턴을 허용하므로 이번 조사에서는 `Observation`으로만 유지한다.

## 제외된 오탐

- `Stage 3 runtime crash`
- `artifact missing`
- `mojibake in blueprint/artifact payload`
- `save_stage_attempt observability 필드 누락`

## 확신도 Ledger

- `70`: 로그, DB, blueprint, artifact 전수 인벤토리 완료
- `+10`: runtime summary, DB commit, blueprint count, artifact count 교차 일치
- `+10`: 코드-로그-DB 삼중 근거 확보
- `+5`: mojibake / runtime failure / observability 오탐 제거 완료
- 최종: `95`

## 최종 판단

- `000__t`의 Stage 3 10화 생산은 성공적으로 완료됐다.
- 현재 evidence 기준으로 Stage 3 산출물은 Stage 4 진행을 막는 runtime blocker를 보이지 않는다.
- 다만 `director_selections(stage=3)` 부재는 post-mortem 품질을 낮추는 명확한 observability debt다.
- 따라서 최종 판정은 `진행 가능 / retained P1 1건 / P0 없음`이다.

## 비고

- 이번 턴은 읽기 전용 로그 감리와 문서 작성만 수행했다.
- 코드 수정, 테스트 실행, rerun은 하지 않았다.
