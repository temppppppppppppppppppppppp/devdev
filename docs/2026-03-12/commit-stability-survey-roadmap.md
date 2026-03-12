# 최신 커밋 전후 변동성 전수조사 로드맵

작성일: 2026-03-12
현재 기준선:
- 최신 커밋: `b3cfa0e` (`feat: TF-IPG InPlace Patch Guard 강화 + Control-Treatment 감사 + 신규 모듈/테스트 보강`)
- 비교 기준: `HEAD` 커밋 상태 vs 현재 dirty worktree
- 현재 목적: 최신 커밋 전후 변동성에 대한 안정성 확보, 전반적 `P0/P1`급 에러 탐지, canary 실행 전 조사 완료

상위 참고 문서:
- `docs/2026-03-12/pass-with-fix-master-roadmap.md`
- `docs/2026-03-12/logging-reinforcement-master-roadmap.md`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`
- `docs/2026-03-12/stage4-canary-automation-3pass-audit.md`
- `docs/2026-03-12/stage4-live-rerun-checklist.md`

## 1. 문서 목적

이 문서는 canary 실행 전 수행할 `전수조사`의 작업 순서와 점검 체크리스트를 고정한다.

직접 목표:
- 최신 커밋 전후로 들어온 대규모 변경이 `계약`, `저장`, `관측`, `분석`, `canary 자동화`에 불안정성을 남기지 않았는지 확인
- `P0/P1`급 에러가 남아 있는지 체계적으로 탐색
- 조사 결과를 `수정 없이` 문서화하고, 이후 canary go/no-go 판단의 근거를 준비

## 2. 강제 원칙

이번 전수조사에서는 아래를 강제로 적용한다.

- `문서 인코딩 UTF-8 고정`
- `코드 수정 금지`
- `테스트 추가 금지`
- `스키마 변경 금지`
- `canary run/full/live rerun 금지`
- 허용 범위는 `읽기`, `diff`, `로그/DB 점검`, `테스트 실행`, `문서 작성`만 한정
- 모든 findings에는 `근거`를 붙인다.
- 근거는 최소 1개 이상 `코드 위치`, `테스트 파일`, `로그/DB 산출물`, `실행 명령 결과` 중 하나로 남긴다.
- 전수조사 종료 후 반드시 `3-pass 감리`를 수행해 오탐을 줄인다.

즉, 이번 단계의 산출물은 `발견사항`, `증거`, `우선순위`, `실행 준비도`이며, 코드 변화는 포함하지 않는다.

## 3. 전수조사 범위

직접 조사 대상:
- `PASS_WITH_FIX / structural inplace / Stage 3·4 verdict semantics`
- `director_selections / episode_production.jsonl / stage_attempts / pass_rate_monitor.json`
- `FailureAnalyzer.patch_trace_summary()` / `FailureAnalyzer.sink_alignment_summary()`
- `attempt_key / metrics_session_id / candidate_key / content_hash / artifact_path`
- `stage4_canary_tools.py` / `run_stage4_canary.py`
- 관련 회귀 테스트군과 최근 문서군

비대상:
- `CW generate_ensemble()` 중심 일반 글쓰기 구조 재설계
- UI/배포 경로 전반 감사
- live rerun 실행

## 4. 현재 리스크 기준선

현재 worktree는 `HEAD` 대비 대규모 변경 상태다.

핵심 변동 축:
- `PASS_WITH_FIX` semantics 정리
- `Stage 4` final score/label 정합성
- `ChiefWriter inplace_patch()` structural path
- logging reinforcement
- artifact linkage
- canary automation

초기 위험 가설:
- `P0`: final verdict/score 저장 불일치, sink 간 join 불능, canary hard gate fail-open, rerun-safe key 충돌, artifact lineage 상실
- `P1`: 문서 계약과 코드 동작의 미세 불일치, monitor/failure analyzer 집계 왜곡, 테스트 커버리지 hole, manual path 운영 규칙 부재

## 5. 실행 순서

아래 Phase를 순서대로 진행한다. 앞 Phase를 닫기 전 다음 Phase로 넘어가지 않는다.

### Phase 0. 조사 기준선 고정

목표:
- 조사 범위와 비교 기준을 고정
- 이후 증거 수집이 흔들리지 않도록 기준점을 잠금

체크리스트:
- [ ] `git log --oneline --decorate -n 5`로 최신 커밋 기준선 기록
- [ ] `git status --short`로 dirty worktree 파일 목록 기록
- [ ] `git diff --stat HEAD`로 변경량 기록
- [ ] 이번 조사에서 `코드 수정 금지`가 유지되는지 재확인
- [ ] canary 실행 금지 상태가 유지되는지 재확인

권장 명령:
```powershell
git log --oneline --decorate -n 5
git status --short
git diff --stat HEAD
```

완료 기준:
- 조사 문서에 `기준 커밋`, `dirty 범위`, `금지 범위`가 명시되어 있다.

### Phase 1. 최신 커밋 전후 변경 인벤토리

목표:
- `b3cfa0e` 전후로 들어온 변경을 기능군으로 묶고, 불안정성이 큰 축을 추린다.

체크리스트:
- [ ] `git diff --name-only HEAD`로 현재 변경 파일 목록 확보
- [ ] 변경 파일을 아래 묶음으로 분류
- [ ] `PASS_WITH_FIX / structural inplace`
- [ ] `logging / analytics / sink alignment`
- [ ] `attempt_key / artifact linkage`
- [ ] `canary automation`
- [ ] `문서 / 실행 체크리스트 / 감사 문서`
- [ ] 대형 diff 파일 우선순위 지정

우선 조사 대상 파일:
- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/failure_analyzer.py`
- `modules/core/db_manager.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py`
- 대응 테스트 파일 전부

완료 기준:
- 변경 파일이 기능군별로 정리되어 있고, `P0/P1` 가능성이 높은 파일이 상단에 배치되어 있다.

### Phase 2. 계약 및 semantics 정합성 감사

목표:
- 문서, 코드, 테스트, 런타임 산출물이 같은 계약을 말하는지 확인

핵심 질문:
- `PASS_WITH_FIX`는 최종 성공 verdict가 아니라 transient/internal verdict로 정렬되어 있는가
- Stage 3 external success set이 `PASS_WITH_FIX`를 외부 성공으로 노출하지 않는가
- Stage 4 `PASS_WITH_FIX -> patch -> PASS` 후 final score/quality label/stage_attempt가 재심사 결과와 일치하는가
- `PASS_WITH_WARNING` 예외가 문서와 코드에서 동일하게 취급되는가

체크리스트:
- [ ] `pass-with-fix-master-roadmap.md`와 관련 코드의 verdict 계약 비교
- [ ] `pass-with-fix-phase1-execution-spec.md`와 테스트 기대값 비교
- [ ] `stage3_orchestrator.py` success set 확인
- [ ] `stage4_interview_round.py` final verdict/score/label 저장 순서 확인
- [ ] `test_pass_with_fix.py`, `test_stage3_orchestrator.py`, `test_stage4_interview_round.py` 커버리지 확인

권장 명령:
```powershell
rg -n "PASS_WITH_FIX|PASS_WITH_WARNING|final_verdict|final_score|director_score|_director_quality_labels" modules tests docs/2026-03-12
```

완료 기준:
- semantics 불일치 여부가 `문서 기준`, `코드 기준`, `테스트 기준`으로 각각 정리되어 있다.

### Phase 3. logging / analytics / sink 정합성 감사

목표:
- sink 역할 분리가 실제 구현과 일치하는지, cross-sink join이 안정적인지 확인

핵심 질문:
- `director_selections`는 초기 판단 sink로만 쓰이는가
- `episode_production.jsonl`은 Stage 4 lifecycle trace로 일관된가
- `stage_attempts`와 `pass_rate_monitor.json`은 final sink로 일관된가
- `FailureAnalyzer.sink_alignment_summary()`가 실제 mismatch를 과소판정하지 않는가
- `PASS_WITH_FIX`가 분석 계층에서 pass-like로 재유입되지 않는가

체크리스트:
- [ ] `logging-reinforcement-master-roadmap.md`와 구현 비교
- [ ] `failure_analyzer.py`의 `patch_trace_summary()` / `sink_alignment_summary()` 로직 검토
- [ ] `db_manager.py` 최근 episode score query가 final semantics 기준인지 검토
- [ ] `pass_rate_monitor.py`가 final verdict / patch lineage를 충분히 담는지 검토
- [ ] `attempt_key`, `candidate_key`, `content_hash`, `artifact_path`의 sink별 존재 여부 점검
- [ ] `legacy_key_attempts`와 `artifact_missing_files`가 fail-close로 취급되는지 점검

권장 명령:
```powershell
rg -n "attempt_key|candidate_key|content_hash|artifact_path|patch_trace|sink_alignment_summary|legacy_key_attempts" modules tests
```

완료 기준:
- sink별 역할, 누락 가능성, mismatch 가능성이 표 형태로 정리되어 있다.

### Phase 4. structural inplace / ChiefWriter 경로 감사

목표:
- `CW 일반 글쓰기 본체`가 아니라 `inplace_patch()` 경로가 실제 설계 의도와 맞는지 검증

핵심 질문:
- structural path는 local issue에서만 제한적으로 사용되는가
- global issue는 partial/full 쪽으로 안전하게 우회되는가
- whole-text fallback 사유가 명확하고 과도하지 않은가
- `patch_trace`가 structural attempt와 fallback reason을 충분히 설명하는가

체크리스트:
- [ ] `chief_writer.py`의 local/global 라우팅 확인
- [ ] `chief_writer.yaml` structural patch prompt 확인
- [ ] `stage4_interview_round.py`가 patch trace를 손실 없이 전달하는지 확인
- [ ] `test_chief_writer.py`, `test_inplace_reliability.py`, `test_stage4_interview_round.py` 커버리지 확인
- [ ] `CW 일반 생성 구조 비대상` 원칙이 문서와 구현에서 깨지지 않는지 확인

권장 명령:
```powershell
rg -n "inplace_patch|patch_trace|structural|fallback_reason|local issue|global issue|generate_ensemble" modules tests config/prompts
```

완료 기준:
- structural inplace가 `보조 수정 경로`로만 동작한다는 근거가 확보되어 있다.

### Phase 5. canary 자동화 및 실행 안전성 감사

목표:
- canary 실행 직전까지의 자동화가 fail-close이며 문서와 동일한 gate를 적용하는지 확인

핵심 질문:
- `from_ep != 1`이 코드와 문서 모두에서 막혀 있는가
- `prepare -> analyze`만으로 fail-closed 상태 확인이 가능한가
- `run` 경로가 `pass_rate_monitor.save()` / audit flush / post-analyze를 빠뜨리지 않는가
- auto hard gate가 운영 runbook보다 느슨하지 않은가

체크리스트:
- [ ] `stage4-canary-execution-runbook.md`와 `stage4_canary_tools.py` / `run_stage4_canary.py` 비교
- [ ] `test_stage4_canary_tools.py` / `test_run_stage4_canary.py` 커버리지 확인
- [ ] `prepare` / `analyze` 경로가 현재 기준 fail-close인지 확인
- [ ] canary 관련 문서가 `run/full 금지` 상태와 충돌하지 않는지 확인

권장 명령:
```powershell
rg -n "from_ep|hard_gates|pass_rate_monitor.save|_flush_audit_buffer|analyze_canary|run_canary" modules scripts tests docs/2026-03-12
```

완료 기준:
- canary 자동화는 `실행 직전` 기준으로 모순 없이 닫혀 있고, 남은 리스크가 문서화되어 있다.

### Phase 6. P0/P1 테스트 전수 재검토

목표:
- 최신 변경 축을 덮는 테스트군이 실제로 존재하는지, 고위험 hole이 남았는지 확인

권장 테스트 묶음:
```powershell
pytest -q tests/test_pass_with_fix.py tests/test_stage4_interview_round.py tests/test_stage3_orchestrator.py tests/test_failure_analyzer.py tests/test_chief_writer.py tests/test_inplace_reliability.py tests/test_stage4_canary_tools.py tests/test_run_stage4_canary.py tests/test_db_manager.py tests/test_stage2_finalizer.py tests/test_stage2_preflight_helpers.py tests/test_v55_modules.py
```

체크리스트:
- [ ] PASS_WITH_FIX semantics 회귀 테스트 통과 여부 확인
- [ ] Stage 4 final score/label 회귀 테스트 통과 여부 확인
- [ ] FailureAnalyzer / sink alignment 회귀 테스트 통과 여부 확인
- [ ] canary automation 테스트 통과 여부 확인
- [ ] artifact linkage / attempt_key 관련 테스트 통과 여부 확인
- [ ] 테스트 결과에서 flaky 또는 미검증 hole이 있는지 기록

완료 기준:
- `P0/P1` 리스크가 테스트로 덮였는지 여부가 파일 단위로 정리되어 있다.

### Phase 7. 전수조사 판정 및 후속 작업 분리

목표:
- 발견사항을 severity별로 정리하고, canary 전 조치 필요 항목과 canary 후 조치 가능 항목을 분리

체크리스트:
- [ ] 발견사항을 `P0 / P1 / P2 / observation`으로 분류
- [ ] `canary 전 필수 해결` 항목 식별
- [ ] `canary 이후 처리 가능` 항목 식별
- [ ] `문서만 수정하면 되는 항목`과 `코드 수정이 필요한 항목` 분리
- [ ] 후속 실행 문서에 반영할 변경점 정리

완료 기준:
- 조사 종료 시점에 `바로 canary 가능한지`, `아직 막혀 있는지`를 한 줄로 판정할 수 있다.

### Phase 8. 3-pass 감리 및 오탐 제거

목표:
- 전수조사 findings를 다시 훑어 오탐을 줄이고, 근거 밀도를 높인 뒤 최종 판정을 닫는다.

감리 원칙:
- Pass 1: `계약/문서/코드`가 같은 문제를 말하는지 다시 대조
- Pass 2: `테스트/로그/DB/실행 결과`가 findings를 실제로 지지하는지 확인
- Pass 3: `중복 findings`, `추정성 주장`, `우선순위 과대평가`를 제거

체크리스트:
- [ ] 모든 `P0/P1` findings에 증거 링크 또는 명령 결과가 붙어 있는지 확인
- [ ] 문서 근거만 있고 코드/테스트/로그 근거가 없는 항목을 재검토
- [ ] 같은 문제를 다른 이름으로 중복 기재한 항목을 병합
- [ ] `추정`과 `확정`을 구분 표시
- [ ] `P0`로 분류했지만 실제로는 `P1` 또는 `observation`인 항목이 없는지 재판정
- [ ] 최종적으로 `canary blocking` 항목만 남겼는지 확인

완료 기준:
- 최종 findings 목록에서 각 항목의 `severity`, `근거`, `권고 조치`가 명확하다.
- 3-pass 후에도 남는 항목만 최종 감사 문서로 승격된다.

## 6. P0 / P1 판정 규칙

`P0` 예시:
- final verdict/score가 sink마다 다름
- `attempt_key` 또는 artifact linkage가 cross-sink join을 깨뜨림
- canary hard gate가 fail-open
- stage result 저장이 silent corruption을 일으킬 가능성

`P1` 예시:
- 문서 계약과 테스트 기대값이 부분 충돌
- final sink는 맞지만 monitor/analyzer 해석이 약간 다름
- manual path 운영 규칙이 불명확
- 구조 patch 관측성이 충분치 않음

판정 원칙:
- `P0` 발견 시 canary readiness는 즉시 `blocked`
- `P1`만 남았으면 문서화 후 canary 전 처리 여부를 별도 판단

## 7. 조사 산출물

이번 로드맵을 따라 전수조사를 끝내면 아래 문서를 남긴다.

- `전수조사 감사 문서` 1건
- `P0/P1 findings 목록` 1건
- `canary 전 필수 조치 목록` 1건
- `3-pass 감리 문서` 1건
- `근거 부록 또는 evidence index` 1건
- 필요 시 `실행 문서 개정안` 1건

## 8. 종료 조건

아래를 모두 만족하면 이번 전수조사를 닫는다.

- 산출 문서는 `UTF-8`로 저장됨
- `코드 수정 없이` 조사 완료
- 최신 커밋 전후 변동 축이 문서로 재구성됨
- `P0/P1` 판단 근거가 증거와 함께 남음
- 조사 후 `3-pass 감리`가 완료됨
- 감리 후 오탐성 findings가 정리됨
- canary 실행 전 필요한 조치와 불필요한 조치가 분리됨
- 이후 작업자가 이 문서만 보고 순차적으로 점검을 재현할 수 있음

## 9. 조사 시작용 초간단 체크리스트

- [ ] Phase 0 기준선 캡처
- [ ] Phase 1 변경 인벤토리 작성
- [ ] Phase 2 verdict semantics 감사
- [ ] Phase 3 logging / sink 정합성 감사
- [ ] Phase 4 structural inplace 감사
- [ ] Phase 5 canary 자동화 감사
- [ ] Phase 6 테스트 전수 재검토
- [ ] Phase 7 findings 분류 및 canary readiness 판정
- [ ] Phase 8 3-pass 감리 및 오탐 제거
