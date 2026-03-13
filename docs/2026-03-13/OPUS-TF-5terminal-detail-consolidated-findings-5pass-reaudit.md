# OPUS TF 2차 디테일 감사 통합본 5PASS 재감리

- 작성일: 2026-03-13
- 대상 문서: `OPUS-TF-5terminal-detail-consolidated-findings.md`
- 조사 모드: static / read-only / source-report cross-check / targeted code-and-test verification
- 최종 상태: `pass-with-ledger-correction`
- 최종 확신도: `95%`

## Executive Summary

이번 5PASS 재감리 결과, 2차 디테일 감사 통합본은 최종 SSOT로 사용할 수 있는 수준까지 올라왔다. `T1`, `T3` 누락 문서는 복원·신규 작성됐고, 기존 `T2`, `T4`, `T5`와 합쳐 **총 42건**의 ledger를 재구성할 수 있었다.

다만 원문을 그대로 PASS시키지는 않았다. 재감리 과정에서 아래 3가지는 보정했다.

- `D-T1-004`의 원래 구두 요약 중 "`reflexion_memory` CREATE 부재"는 오탐으로 제거했다.
- `D-T5` 문서의 `P2` 본문 헤더는 `10건`으로 적혀 있지만 실제 집계는 `11건`이다.
- `T3` 오더의 `xfail 68개` 전제는 현재 트리와 맞지 않는다. 현재 마커는 `0건`이다.

이 보정 이후의 최종 결론은 다음이다.

- **최종 ledger 42건은 재구성 가능**
- **상위 위험군(P1 2건, 핵심 P2군)은 실코드/실테스트로 직접 재확인됨**
- **현 시점에서 95% 확신도로 최종 문서 승격 가능**

## Pass 1 - 소스 리포트 완전성 검증

### P1-1. T1~T5 소스 문서가 모두 존재하고 합계가 재구성된다

직접 근거:

- `D-T1-detail-infra-audit.md`: 4건
- `D-T2-detail-agents-models-audit.md`: 6건
- `D-T3-detail-tests-audit.md`: 5건
- `D-T4-config-contract-ssot-audit-report.md`: 5건
- `OPUS-TF-5terminal-detail-T5-findings.md`: 22건

판정:

- `confirmed`

해석:

- `4 + 6 + 5 + 5 + 22 = 42`로 통합 ledger를 문서만으로 재구성할 수 있다.

### P1-2. Severity 합계도 모순 없이 재구성된다

직접 근거:

- `P1 = 2` (`D-T5-001`, `D-T5-002`)
- `P2 = 20`
- `P3 = 20`

판정:

- `confirmed`

해석:

- 디테일 세트에는 `P0`가 없다.
- 고위험 실행 우선순위는 Desktop 보안/진입점 문제와 테스트/계약/DB 경계 문제로 압축된다.

## Pass 2 - T1 복원분 코드 검증

### P2-1. `D-T1-001`은 진탐이다

직접 근거:

- `modules/core/error_helper.py`의 외부 import는 실사용 경로가 아니라 usage 예시 수준에 머문다.
- 실제 소프트 실패 경로는 `soft_failure.py`를 따라 `artifact_logging.py`, `failure_analyzer.py`, `session_logger.py`, `stage4_post_processor.py`로 연결된다.

판정:

- `confirmed`

### P2-2. `D-T1-002` mojibake는 실코드에서 직접 확인된다

직접 근거:

- `modules/core/stage0/__init__.py:309-317`에 깨진 한글 문자열이 그대로 남아 있다.
- 동일 정책 메뉴가 `normalize_external_pov_insert_policy()`로 후처리되므로 로직 자체는 유지된다.

판정:

- `confirmed`

### P2-3. `D-T1-004`는 범위를 좁혀야 진탐이다

직접 근거:

- `modules/core/reflexion_manager.py:99`, `115`에서 `self.context.db.conn.commit()` 직접 호출.
- `modules/core/db_manager.py:1039-1047`의 `execute_update()`는 commit을 수행하지 않음.
- 반면 `modules/core/db_manager.py:268-280`에는 `reflexion_memory` 테이블 DDL이 존재.

판정:

- `confirmed-with-correction`

해석:

- 문제는 "DDL 부재"가 아니라 "DBManager API 우회"다.
- 이 보정을 반영한 현재 `D-T1-004`는 진탐이다.

## Pass 3 - T3 신규 문서 테스트 검증

### P3-1. `D-T3-01` handoff 계약 테스트 부재는 진탐이다

직접 근거:

- `tests/` 전역에서 Stage3 출력과 Stage4 입력을 한 번에 묶는 handoff 테스트가 확인되지 않았다.
- `tests/test_stage3_orchestrator.py`는 Stage3 결과 stub 검증에 집중하고,
- `tests/test_stage4_context_builder.py`, `tests/test_stage4_orchestrator.py`는 부분 blueprint나 빈 dict 경로 검증이 중심이다.

판정:

- `confirmed`

### P3-2. `D-T3-02` advisory 병렬 테스트 우회는 진탐이다

직접 근거:

- `tests/test_stage4_interview_round.py:288`에서 `_run_advisory_chain`이 `MagicMock`으로 대체된다.
- 프로덕션 `modules/core/stage4_interview_round.py:3704-3726`은 `ThreadPoolExecutor`, `as_completed`, `timeout=60`을 사용한다.

판정:

- `confirmed`

### P3-3. `D-T3-03`, `D-T3-04`의 환경 의존 skip도 진탐이다

직접 근거:

- `tests/e2e/test_l3_stage2_realproject.py`, `test_l3_stage3_smoke.py`, `test_l3_stage4_smoke.py`는 `REAL_PROJECT_DB` 부재 시 skip.
- `tests/e2e/test_l3_golden_route.py`는 treatment/bible 자산 부재 시 skip.
- `tests/integration/test_pipeline_smoke.py`는 sqlite-vec/VecMemory 상태에 따라 skip.

판정:

- `confirmed`

### P3-4. `D-T3-05` xfail ledger 드리프트는 현재 기준 사실이다

직접 근거:

- 오더는 `xfail 68개`를 전제로 한다.
- 현재 `tests/*.py`에서 `xfail` 마커 grep 결과는 `0건`.

판정:

- `confirmed-with-scope-note`

해석:

- "68개가 전부 수정 완료"까지는 입증 못 한다.
- 하지만 "현재 xfail 마커가 68개 남아 있다"는 상태가 아니라는 점은 확정 가능하다.

## Pass 4 - 기존 T2/T4/T5 표본 재검증

### P4-1. `D-T2-01`, `D-T2-02` dead agent는 실코드에서 재확인된다

직접 근거:

- `main_a.py:1497`에 `critic` 인스턴스화.
- `main_a.py:1522`에 `arc_critic` 인스턴스화.
- 프로덕션 코드 범위에서 `agents["critic"]`, `agents["arc_critic"]` 직접 사용처는 재확인되지 않았다.

판정:

- `confirmed`

### P4-2. `D-T4-01` API contract 누락 4건은 실코드에서 재확인된다

직접 근거:

- `modules/api/bridge_server.py`에 아래 엔드포인트 존재:
  - `/quality/summary`
  - `/quality/dashboard`
  - `/safe-ops/preview`
  - `/quality/review`
- `docs/implementation/api-contract-v1.yaml`에는 해당 경로가 보이지 않는다.

판정:

- `confirmed`

### P4-3. `D-T5-001`, `D-T5-002`는 상위 위험군으로 유지 가능하다

직접 근거:

- `geuldobi-desktop/package.json`의 실제 진입점은 `"main": "src/main.js"`.
- `geuldobi-desktop/src/main.js`에만 `project:list-work-guard-templates`, `project:apply-work-guard-template` 핸들러가 있다.
- `geuldobi-desktop/src/index.html`에는
  - CSP `script-src 'unsafe-inline'`
  - `connect-src ... https://generativelanguage.googleapis.com`
  - 렌더러 `fetch("https://generativelanguage.googleapis.com/...")`
  가 함께 존재한다.

판정:

- `confirmed`

## Pass 5 - ledger 정리와 최종 확신도

### R1. 최종 합계 42건은 SSOT로 사용 가능하다

직접 근거:

- 문서별 건수와 severity 분포가 모두 재구성된다.
- 미해결 duplicate ledger는 발견되지 않았다.

상태:

- `accepted`

### R2. `D-T5`의 P2 헤더는 오타로 간주하고 `11건`으로 보정해야 한다

직접 근거:

- 상단 집계표는 `P2 = 11`.
- 본문 ID도 `D-T5-003`부터 `D-T5-013`까지 `11건`.
- section header만 `10건`으로 표기.

상태:

- `accepted-as-ledger-correction`

### R3. 잔여 불확실성은 5% 이내다

근거:

- 상위 위험군과 핵심 P2군을 직접 코드/테스트로 재검증했다.
- T1 복원분의 오탐 1건을 제거해 범위를 정제했다.
- T3 신규 문서는 현 트리 기준으로 직접 스캔해 작성했다.

잔여 리스크:

- T3의 "229개 전수"를 실제 pytest 동적 실행으로 다시 돌리지는 않았다.
- xfail 68개 이력은 현재 tree만으로 역사 복원이 불가능하다.
- 기존 `D-T5` 원문 파일의 내부 헤더 오타는 소스 파일 자체에는 남아 있다.

판정:

- `95% confidence achieved`

## 최종 baseline

### 확정 가능

- `P0 = 0`
- `P1 = 2`
- `P2 = 20`
- `P3 = 20`
- `총 42건`

### 최우선 실행군

- `D-T5-001` 중복 `main.js` 정리
- `D-T5-002` 렌더러 직접 API 호출 제거
- `D-T4-01` API contract 문서 동기화
- `D-T1-004` DB commit API 일관화
- `D-T3-01`, `D-T3-02` 교차 단계/병렬 경로 테스트 보강

## 결론

2차 디테일 감사는 이제 문서 누락 없이 닫혔다. 최종 참조 우선순위는 다음 순서가 적절하다.

1. `OPUS-TF-5terminal-detail-consolidated-findings-5pass-reaudit.md`
2. `OPUS-TF-5terminal-detail-consolidated-findings.md`
3. 터미널별 원본 리포트 `D-T1`~`D-T5`

