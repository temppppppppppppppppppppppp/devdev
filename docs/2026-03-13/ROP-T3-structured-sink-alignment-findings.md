# ROP-T3 Structured Sink Alignment Findings

작성일: 2026-03-13  
담당 터미널: `T3`  
범위: `runtime_audit_summary.json`, `episode_production.jsonl`, `stage_attempts`, `director_selections`, `pass_rate_monitor.json`  
조사 모드: `read-only audit`, `code-and-test verification`, `artifact-proof cross-check`, `UTF-8 only`  
최종 판정: `retained P1 1건`, `retained P2 2건`, `coverage gap 2건`, 확신도 `93%`

## 조사 입력

- 코드
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/pass_rate_monitor.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/db_manager.py`
  - `modules/core/artifact_logging.py`
- 테스트
  - `tests/test_director_feedback_loop.py`
  - `tests/test_stage4_post_processor.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_failure_analyzer.py`
  - `tests/test_audit_service.py`
  - `tests/test_logging_enhancement.py`
  - `tests/test_db_manager.py`
- 기존 문서
  - `docs/2026-03-13/stage4-9ep-log-full-survey-3pass-final-audit.md`
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
  - `docs/2026-03-13/stage3-10ep-log-remediation-postfix-3pass-closure.md`
- 런타임 아티팩트
  - `projects/기록용/000__t`
  - `projects/기록용/00_test_07`
  - `projects/기록용/0w`

## 테스트 실행 결과

- 실행: `pytest -q tests/test_stage3_orchestrator.py tests/test_stage4_interview_round.py tests/test_stage4_orchestrator.py tests/test_failure_analyzer.py tests/test_audit_service.py tests/test_stage4_post_processor.py tests/test_director_feedback_loop.py tests/test_logging_enhancement.py tests/test_db_manager.py`
- 결과: `277 passed in 58.61s`

## PASS 1 후보 수집

- 후보 1: 현재 코드 기준 Stage 3는 `stage_attempts`와 `director_selections` 사이에 rationale strength 차이가 남아 있다.
- 후보 2: historical project의 Stage 3/4 sink가 세대별로 갈라져 있어 현재 문서와 실제 artifact를 같은 SSOT로 읽기 어렵다.
- 후보 3: `runtime_audit_summary.json`는 completion heartbeat만 남기고 attempt-level structured alignment는 보존하지 않는다.
- 후보 4: Stage 4 `PASS_WITH_FIX`에서 `candidate_key`와 `selection_candidate_key`가 달라 보이는 것은 sink drift일 수 있다.
- 후보 5: `failure_analyzer.sink_alignment_summary(stage=3)`가 Stage 3 lifecycle sink를 실제보다 더 깨끗하게 보이게 만들 수 있다.

## PASS 2 교차 검증

### 제거 1. Stage 4 `PASS_WITH_FIX`의 selection/final candidate 분리는 drift가 아니다

- `modules/core/stage4_interview_round.py:4388-4394`는 final artifact와 `selection_*` artifact를 의도적으로 이중 기록한다.
- `tests/test_stage4_interview_round.py:2112`와 `tests/test_stage4_interview_round.py:2189`도 이 dual-write를 명시적으로 잠근다.
- 따라서 `director_selections.candidate_key != stage_attempts.candidate_key` 자체는 PASS_WITH_FIX 경로의 설계 결과다.

### 제거 2. `000__t`의 Stage 4 thin sink를 current-code defect로 재오픈하지 않는다

- `docs/2026-03-13/stage4-9ep-log-full-survey-3pass-final-audit.md`는 `000__t` runtime을 기준으로 `stage_attempts` thin sink를 retained `P2`로 이미 기록했다.
- 현재 코드와 `projects/기록용/0w`는 더 rich한 Stage 4 `stage_attempts`를 남긴다.
- 따라서 이번 트랙에서 재확정할 문제는 “Stage 4가 지금도 thin하다”가 아니라 “artifact generation이 갈라져 SSOT가 세대 의존적이다”로 좁혀야 한다.

## PASS 3 확정 Findings

### [ROP-T3-001] Stage 3는 현재도 rationale SSOT가 단일 sink로 수렴하지 않는다

- ID: `[ROP-T3-001]`
- Severity: `P1`
- 현상 요약: 현재 코드와 최신 샘플 런(`projects/기록용/0w`)에서도 Stage 3는 `stage_attempts`와 `pass_rate_monitor`에 final lineage만 남기고, `selection_reason`/`verdict_reason`는 `director_selections`에만 남긴다. Stage 4는 현재 `stage_attempts`까지 rationale를 보존하는 반면, Stage 3는 여전히 “final artifact sink”와 “selection rationale sink”가 분리돼 있다.
- 코드 근거: `modules/core/stage3_orchestrator.py:1651-1735`는 Stage 3 selection payload에 `selection_reason`, `verdict_reason`, `attempt_key`, `candidate_key`, `artifact_path`를 조립한다. 그러나 실제 Stage 3 `save_stage_attempt()` 호출은 success path `modules/core/stage3_orchestrator.py:1376-1392`, reject path `modules/core/stage3_orchestrator.py:1888-1904`에서 rationale 필드를 넘기지 않는다. 반대로 Stage 4는 `modules/core/stage4_interview_round.py:4567-4590`에서 `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`를 `stage_attempts`에 직접 저장한다. 실제 artifact도 이를 따른다. `projects/기록용/0w/project_data.db`에서 `stage_attempts(stage=3)` 3건은 `selection_reason=''`, `verdict_reason=''`인데 `director_selections(stage=3)` 3건은 둘 다 비어 있지 않다.
- downstream 영향 경계: 운영자가 Stage 3를 `stage_attempts` 단독 또는 `pass_rate_monitor` 단독으로 보면 “왜 이 blueprint가 선택됐는가”를 복원할 수 없다. Stage 4와 달리 Stage 3만 별도 table join이 필수라서, stage 간 비교 보고서나 장애 분석이 final artifact 중심으로 편향된다.
- 현재 테스트 근거 또는 테스트 부재: `tests/test_stage3_orchestrator.py:279`는 Stage 3 `director_selections` persistence를 잠그고 `tests/test_stage3_orchestrator.py:778`은 attempt-level artifact linkage를 잠그지만, `stage_attempts(stage=3)`가 rationale field를 가져야 한다는 테스트는 없다. `tests/test_failure_analyzer.py`의 sink alignment 시나리오는 Stage 4 중심이고, Stage 3 lifecycle sink 정렬은 직접 잠그지 않는다. 이번 focused regression은 `277 passed`였다.
- 기존 문서와의 중복 여부: `related-but-new-evidence-layer-surface`
- 권장 후속 조치: Stage 3 contract를 둘 중 하나로 명시해야 한다. `1)` Stage 4처럼 `stage_attempts(stage=3)`에도 rationale를 넣어 단일 table SSOT를 맞추거나, `2)` `director_selections(stage=3)`를 mandatory evidence sink로 승격하고 모든 정렬 도구/문서에서 Stage 3는 해당 table join 없이는 완료 판정하지 않도록 규정해야 한다.

### [ROP-T3-002] historical runtime artifact는 세대별 structured sink가 달라 같은 문장을 다른 뜻으로 만든다

- ID: `[ROP-T3-002]`
- Severity: `P2`
- 현상 요약: 워크스페이스의 실 artifact는 최소 3세대로 갈라져 있다. `projects/기록용/00_test_07`의 Stage 3는 `stage_attempts` 4건 모두 `attempt_key/candidate_key/artifact_path`가 비어 있고 Stage 3 `pass_rate_monitor` 및 `director_selections`도 없다. `projects/기록용/000__t`는 Stage 3 final lineage는 갖지만 `director_selections(stage=3)=0`이다. `projects/기록용/0w`는 Stage 3 final lineage와 `director_selections(stage=3)=3`까지 갖는다. Stage 4도 `000__t`/`00_test_07` historical row는 migrated column이 생겨도 `selection_reason`/`verdict_reason`가 `0/n`으로 비어 있고, `0w`는 `3/3`으로 채워져 있다.
- 코드 근거: `modules/core/db_manager.py:60-68`는 `DBManager` 생성 시 `_boot_db()`를 실행하고, `modules/core/db_manager.py:554-610`는 `stage_attempts`에 새 column을 `ALTER TABLE`로 추가한다. 즉 current app boot는 old DB schema를 “현재 형태”로 보이게 만들지만, historical row의 missing rationale를 backfill하지는 못한다. current write path는 Stage 4에서 `modules/core/stage4_interview_round.py:4567-4590`, Stage 3 selection sink에서 `modules/core/stage3_orchestrator.py:1393-1407` 및 `modules/core/stage3_orchestrator.py:1905-1919`로 richer metadata를 쓰지만, old runtime row에는 소급 적용되지 않는다. 실제 artifact 교차 결과는 다음과 같다. `00_test_07` Stage 3: `stage_attempts=4`, `director_selections=0`, `pass_rate_stage3=0`, null `attempt_key=4/4`. `000__t` Stage 3: `stage_attempts=10`, `director_selections=0`, `pass_rate_stage3=10`. `0w` Stage 3: `stage_attempts=3`, `director_selections=3`, `pass_rate_stage3=3`. Stage 4 `stage_attempts` rationale populated 수는 `000__t=0/13`, `00_test_07=0/4`, `0w=3/3`이다.
- downstream 영향 경계: 운영자는 “`stage_attempts`가 thin하다”와 “`stage_attempts`가 rationale를 가진다”는 두 문장을 모두 볼 수 있는데, 둘 다 run generation에 따라 사실이다. 날짜나 generation 태그 없이 통합 문서를 읽으면 현재 코드 결함과 stale artifact debt를 구분하지 못하고 잘못된 remediation 우선순위를 세우기 쉽다.
- 현재 테스트 근거 또는 테스트 부재: `tests/test_stage4_interview_round.py:2112`, `tests/test_stage4_interview_round.py:2189`, `tests/test_db_manager.py:331`은 current rich schema를 검증한다. 반면 historical DB를 current boot 후 열었을 때 empty migrated column이 남는지, old Stage 3 row가 backfill 없이 비어 있는지는 테스트가 없다. 이번 focused regression은 current code-path만 green임을 보여 주고, stale artifact refresh proof는 제공하지 않는다.
- 기존 문서와의 중복 여부: `related-but-new-evidence-layer-surface`
- 권장 후속 조치: consolidated audit에서는 run date와 artifact generation을 먼저 선언해야 한다. historical project는 `stale-artifact`, fresh run은 `current-schema`로 ledger를 분리하고, old project를 SSOT 근거로 재사용하려면 backfill 또는 rerun artifact refresh를 별도 작업으로 취급해야 한다.

### [ROP-T3-003] `runtime_audit_summary.json`는 structured sink alignment를 대표하지 못한다

- ID: `[ROP-T3-003]`
- Severity: `P2`
- 현상 요약: `runtime_audit_summary.json`는 run completion heartbeat로는 유효하지만 attempt-level structured sink alignment를 보존하지 않는다. 실제로 `projects/기록용/000__t/logs/runtime_audit_summary.json`과 `projects/기록용/0w/logs/runtime_audit_summary.json`는 둘 다 `tag=stage4_complete`를 남기지만, 앞의 project는 historical thin rows를 품고 있고 뒤의 project는 current rich rows를 갖는다.
- 코드 근거: `modules/core/services/audit_service.py:71-102`가 쓰는 summary payload는 `tag`, `timestamp`, `total_events`, `counts`, `latest_event_type`, `recent_events`뿐이다. `attempt_key`, `candidate_key`, `artifact_path`, `selection_candidate_key`, lifecycle completeness, sink coverage 같은 structured digest는 없다. `tests/test_audit_service.py:87`은 summary file 생성과 `tag/total_events/counts`만 검증하고, `tests/test_stage4_orchestrator.py:121`은 Stage 4 completion 시 summary write 호출만 잠근다.
- downstream 영향 경계: 운영자가 `runtime_audit_summary.json`만 보고 “이 런은 structured sink까지 정상”이라고 판단하면 오판한다. 실제 structured provenance는 DB/JSONL/pass-rate/session log로 다시 내려가서 확인해야 하며, summary 자체는 그 pivot key를 제공하지 않는다.
- 현재 테스트 근거 또는 테스트 부재: summary 존재/호출 여부 테스트는 충분하지만, summary가 attempt-level sink digest를 포함해야 한다는 테스트는 없다. 이번 조사에서 UTF-8 깨짐이나 summary write failure는 보지 못했지만, completeness와 alignment를 보장하는 증거도 summary에는 없다.
- 기존 문서와의 중복 여부: `none`
- 권장 후속 조치: `runtime_audit_summary.json`의 역할을 명시적으로 둘 중 하나로 고정해야 한다. `1)` completion-only heartbeat로 격하하고 통합 문서에서 구조 증거로 사용하지 않거나, `2)` per-stage sink count, latest attempt_key, lifecycle completeness, latest artifact digest를 넣어 operator-facing summary contract로 승격한다.

## Coverage Gaps / Open Questions

- `modules/core/failure_analyzer.py:263-295`는 `sink_alignment_summary()`에서 `director_selections`를 Stage 2/4만 읽는다. 그래서 `projects/기록용/0w`처럼 Stage 3 `director_selections`가 실제로 있어도 automated summary는 Stage 3 coverage에 이를 반영하지 않는다. 이번 문서는 이를 tool blind spot으로 기록하지만, direct sink writer defect로는 승격하지 않았다.
- `DBManager`는 open 시점에 `stage_attempts` schema migration을 수행한다. 따라서 “프로젝트가 current code에 한 번이라도 열리기 전의 pristine schema”는 backup 또는 raw snapshot 없이는 영구 증명하기 어렵다. 이번 감사는 raw sqlite 조회와 current boot 후 상태를 함께 봤지만, immutable historical proof는 별도 보존 체계가 필요하다.

## PASS1 -> PASS2 -> PASS3 요약

- PASS1 후보: `5건`
- PASS2 제거: `2건`
- PASS3 확정: `3건`
- 확정 ID
  - `[ROP-T3-001]` `P1` Stage 3 rationale SSOT 비대칭
  - `[ROP-T3-002]` `P2` historical artifact generation split
  - `[ROP-T3-003]` `P2` runtime audit summary의 attempt-level blind spot

## 최종 결론

- current code 기준 Stage 4 structured sink는 Stage 3보다 강하다.
- 그러나 runtime evidence layer 전체는 아직 단일 SSOT가 아니다.
- 가장 큰 현재형 문제는 Stage 3 rationale가 여전히 단일 sink로 닫히지 않는 점이다.
- 가장 큰 historical 문제는 old project artifact가 current schema와 같은 이름의 sink를 다른 의미로 쓰고 있다는 점이다.
- `runtime_audit_summary.json`는 완료 신호로는 유효하지만, structured alignment 증거로는 불충분하다.
