# today roadmap 참고 문서 잔여물 실행 SSOT

작성일: 2026-03-12  
인코딩: UTF-8  
역할: 참고 문서 재감리 후 남은 실질 잔여물만 실행 단위로 바꾼 단일 SSOT  
상태: `execution-ready`

## 0. 소스 문서

- `docs/2026-03-12/today-roadmap-reference-docs-rerudit-3pass-audit.md`
- `docs/2026-03-12/today-code-health-ui-build-roadmap.md`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`
- `docs/2026-03-12/stage4-canary-log-audit.md`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`
- `docs/2026-03-12/roadmap-external-full-survey-3pass-audit.md`
- `docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md`
- `docs/2026-03-12/TF-S3-context-contract-audit.md`
- `docs/2026-03-12/TF-VERTEX-migration-full-audit.md`

## 1. 문서 역할

이 문서는 감사 문서를 대체하지 않는다.  
역할은 감사에서 살아남은 open item만 오늘의 실행 순서와 acceptance 기준으로 고정하는 것이다.

실행 원칙:

1. `runtime gate`와 `code-level P1`를 먼저 닫는다.
2. `P2`는 P1을 방해하지 않는 선에서 묶어서 처리한다.
3. `Observation`은 이번 문서에서 구현 의무로 승격하지 않는다.
4. `today roadmap`이 상위 운영 SSOT이고, 본 문서는 그 하위의 `reference-remediation SSOT`다.

## 2. 최종 실행 범위

### E-1. Metrics / Artifact safety

목표:
- `BUG-PRICE-1` 해소
- artifact snapshot write failure가 Stage 전체 실패로 전파되지 않도록 방어
- direct unit-test gap을 `artifact_logging`, `logging_keys` 기준으로 닫기

대상 파일:
- `modules/core/metrics_collector.py`
- `modules/core/artifact_logging.py`
- `modules/core/logging_keys.py`
- 관련 테스트 파일 신규/보강

acceptance:
- `gemini-2.5-pro` `cache_read` 단가가 감사 문서 기준과 일치한다.
- artifact write 실패가 soft-failure 또는 fail-safe 형태로 흡수된다.
- `artifact_logging`, `logging_keys` direct regression이 존재한다.

### E-2. Stage 3 observability closure

목표:
- Stage 3에서 사후 재구성이 어려운 관측성 갭 2건을 닫는다.

대상 파일:
- `modules/core/stage3_orchestrator.py`
- `modules/core/db_manager.py`
- `modules/protocols/db_repository.py`
- 관련 테스트

구현 범위:
- `_bp_semantic_ctx`는 전문 저장이 아니라도 source summary / chars / source flags 수준 메타를 남긴다.
- `save_stage_attempt()`에는 Stage 3에서도 `duration_ms`, `failure_category`, `advisory_flags`와 동급의 분석 필드가 빠지지 않게 맞춘다.

acceptance:
- Stage 3 attempt row만 보고도 semantic context 존재 여부와 주요 source footprint를 복원할 수 있다.
- Stage 2/3/4 stage_attempt 관측성 필드가 이유 없이 비대칭으로 비지 않는다.

### E-3. Stage 4 context contract closure

목표:
- Stage 4 local patch / re-audit 경로의 context loss를 줄인다.

대상 파일:
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/chief_writer.py`
- 관련 테스트

구현 범위:
- local patch 입력에서 `fix_scope_reasoning`, `open_review`, `action_items`의 균형을 맞춘다.
- Stage 4 re-audit story_context에 누적 patch provenance를 주입한다.

acceptance:
- local patch loop가 `action_items`만 남고 자유 리뷰/수정 범위 근거를 잃지 않는다.
- Stage 4 re-audit는 Stage 2와 비슷한 수준으로 patch history를 story_context에 받는다.

### E-4. Runtime proof gates

목표:
- 지금까지의 static closure를 실제 런타임 gate로 닫는다.

실행 순서:
1. limited Stage 4 canary rerun
2. packaged build chain 실행
3. packaged smoke 확인

세부 단계:
- canary: `prepare -> run -> analyze`
- build: `backend -> engine -> Electron --dir`
- smoke: project list/create, run path, quality dashboard, safe ops preview, review path

acceptance:
- canary summary에서 `candidate_key_mismatches == []`
- canary summary에서 `artifact_path_mismatches == []`
- `pass_rate_monitor_missing` 없음
- packaged desktop에서 project root split 재현 안 됨
- packaged desktop이 `backend`, `engine`, `python-embed` 자원으로 정상 부팅

### E-5. 문서 closure

목표:
- 실행 후 감사 문서들을 현재 코드 기준으로 다시 닫는다.

필수 산출물:
- `stage4-canary-pass-final-report.md` 또는 동등한 canary closure 문서
- UI/desktop rerudit 최종본
- 필요 시 today roadmap 상태 업데이트

## 3. 실행 순서

1. `E-1 Metrics / Artifact safety`
2. `E-2 Stage 3 observability closure`
3. `E-3 Stage 4 context contract closure`
4. `E-4 Runtime proof gates`
5. `E-5 문서 closure`

## 4. 명시적 비범위

- full/live rerun
- 대규모 UI 리디자인
- Vertex migration 자체 실행
- WorkGuard wizard 같은 선택 기능 확장
- historical observation 정리만을 위한 대청소

## 5. 종료 조건

이 문서는 아래가 만족될 때 닫힌다.

1. code-level P1이 0건이다.
2. Stage 3/Stage 4 context/observability P2가 실행 대상 기준으로 닫혔다.
3. limited canary가 방어 가능한 `PASS` 또는 `WARN`으로 닫힌다.
4. packaged build smoke가 통과한다.
5. 후속 감사 문서가 `open P0/P1/P2 없음`으로 다시 닫힌다.
