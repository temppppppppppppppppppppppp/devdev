# Runtime Observability Provenance Artifact Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: runtime observability, provenance, artifact sink blind spot audit
> 상태: `execution-ready`
> 조사 현황: `조사 완료`
> 목적: `main_a.py`, Stage 0~4 runtime, DB/JSONL/session/style-guide artifact가 operator-facing 증거 계층으로 같은 사실을 보존하는지 전면 전량 조사한다.
> 방식: `5-terminal 병렬`, 각 터미널 자체 `3PASS`, 통합본 `3PASS 재감리`

---

## 0. 문서 역할

- 이 문서는 runtime observability / provenance / artifact contract 조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서 코드 직접 수정은 금지한다.
- 모든 문서는 `UTF-8` 고정이다. 물음표 치환 흔적이나 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 control plane, facade shim, retry-feedback, persistence helper, Stage 4 log/full survey, viewpoint remediation를 각각 다뤘다. 그러나 아래 표면은 아직 `operator가 실제로 읽는 증거 계층` 관점의 독립 오더로 잠기지 않았다.

- `main_a.py` wrapper와 Stage3/4 context가 `session_logger`, audit summary, soft-failure relay를 실제 sink까지 전달하는지 여부
- `runtime_audit_summary.json`, `episode_production.jsonl`, `stage_attempts`, `director_selections`, `pass_rate_monitor.json`이 같은 attempt / verdict / rationale을 보존하는지 여부
- Stage 0 `style_guide.json` 및 POV provenance가 planning / validation / runtime summary와 같은 SSOT를 보는지 여부
- tagged audit summary, sync/parallel soft-failure relay, mojibake log literal처럼 테스트는 초록이지만 operator-facing surface는 잠기지 않은 영역
- runtime proof가 필요한 live rerun / canary / artifact refresh surface

관련 문서:

- `docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md`
- `docs/2026-03-13/logging-hardening-moderate-remediation-execution-ssot.md`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- `docs/2026-03-13/stage4-9ep-log-full-survey-3pass-final-audit.md`
- `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md`
- `docs/2026-03-13/viewpoint-mixed-pov-full-survey-3pass-final-audit.md`
- `docs/2026-03-13/viewpoint-primary-pov-external-insert-remediation-postfix-3pass-closure.md`

본 트랙은 개별 helper 품질 재감사가 아니라, `runtime evidence layers`를 하나의 SSOT로 잠그는 데 목적이 있다.

---

## 2. 공통 조사 규약

### 2.1 조사 모드

- `static`
- `read-only`
- `code-and-test verification`
- `source-report cross-check`
- `artifact-proof cross-check`
- `UTF-8 only`

### 2.2 병렬 실행 규칙

- 터미널 `T1` ~ `T5`는 병렬 수행을 전제로 한다.
- 각 터미널은 자기 결과 문서만 작성한다.
- 다른 터미널 결과 문서를 수정하지 않는다.
- 코드 직접 수정, 임시 patch, test 수정은 금지한다.
- 조사 중 발견한 의심 항목은 PASS 1 후보로만 기록하고 PASS 2 전 확정하지 않는다.

### 2.3 3PASS 프로토콜

#### PASS 1 - 표면 수집

- 담당 sink, helper, test, 기존 문서, runtime artifact를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- candidate마다 `wiring`, `persistence`, `artifact`, `provenance`, `utf8`, `runtime-proof` 태그를 붙인다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 문서 근거, artifact 근거를 함께 대조한다.
- 기존 문서에서 이미 닫힌 항목은 재오픈하지 않는다.
- 다만 기존 문서가 개별 sink 또는 개별 remediation만 다뤘고, 이번 항목이 `evidence-layer contract` 문제면 신규 finding으로 유지 가능하다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[ROP-TN-SEQ]` 형식으로 채택한다.
- 문서 말미에 `PASS1 후보 -> PASS2 제거 -> PASS3 확정` 요약을 남긴다.
- 미확정 사항은 `coverage gap` 또는 `open question`으로 분리한다.

### 2.4 finding 기록 형식

각 finding은 아래 8개 필드를 반드시 가진다.

1. ID
2. Severity (`P0`, `P1`, `P2`, `P3`)
3. 현상 요약
4. 코드 근거
5. downstream 영향 경계
6. 현재 테스트 근거 또는 테스트 부재
7. 기존 문서와의 중복 여부
8. 권장 후속 조치

### 2.5 Severity 기준

- `P0`: operator-facing evidence layer가 핵심 state를 거짓으로 남기거나 복구 불가능하게 훼손하는 경우
- `P1`: verdict/rationale/provenance/artifact linkage가 sink 사이에서 유의미하게 어긋나는 경우
- `P2`: observability thinness, sink blind spot, tagged callback drift, runtime-proof 부재, stale artifact SSOT
- `P3`: UTF-8/log literal 품질, operator-facing label drift, trace readability 저하

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | main_a wrapper -> context -> log sink wiring | `session_logger`, audit summary, Stage3/4 context wiring |
| T2 | soft-failure / audit / UTF-8 operator surface | validation soft-failure relay, tagged audit summary, mojibake log literal |
| T3 | structured sink alignment | `runtime_audit_summary.json`, `episode_production.jsonl`, `stage_attempts`, `director_selections`, `pass_rate_monitor.json` |
| T4 | Stage 0 / style_guide / POV provenance artifact | `style_guide.json`, Stage0 cache meta, POV provenance, planning/validation handoff |
| T5 | runtime proof / canary / regression surface | canary, rerun proof, artifact refresh, test blind spot, existing audit cross-check |

---

## 4. Terminal 1 - main_a Wrapper -> Context -> Log Sink Wiring

### 담당 범위

- `main_a.py`
  - Stage3/4 wrapper
  - `_session_logger`
  - audit summary / audit event related facade
- 직접 downstream
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/session_logger.py`

### 핵심 검사 포인트

1. `main_a.py` wrapper가 `session_logger`, audit callback, summary callback을 Stage3/4 real path에 빠짐없이 전달하는가
2. `from_app()` factory path와 manual context injection path가 서로 다른 observability surface를 만들지 않는가
3. Stage3/4 consumer가 `ctx`와 `self.app`를 섞어 보며 sink source를 이중화하지 않는가
4. `logging-hardening`이 요구한 `attempt_key`/decision rows contract가 wrapper 경계에서 조용히 꺼지지 않는가
5. wrapper regression test가 실제 sink wiring을 잠그는가

### 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_session_logger.py`

### 산출물

- `docs/2026-03-13/ROP-T1-main-a-context-log-wiring-findings.md`

---

## 5. Terminal 2 - Soft-Failure / Audit / UTF-8 Operator Surface

### 담당 범위

- `modules/validation/validation_orchestrator.py`
- `modules/core/soft_failure.py`
- `modules/core/failure_analyzer.py`
- `modules/core/artifact_logging.py`
- `main_a.py::_write_audit_summary`
- operator-facing log literal / label surface

### 핵심 검사 포인트

1. soft-failure relay가 helper direct-call이 아니라 sync/parallel 실제 예외 경로에서 sink로 surface되는가
2. tagged audit summary contract가 protocol / context green 뒤에 숨지 않는가
3. UTF-8 / mojibake log literal이 operator-facing 판단을 오염시키지 않는가
4. log / audit / soft-failure message payload가 runtime branch별로 일관적인가
5. 테스트가 helper 단위만 보고 real execution path observability는 놓치지 않는가

### 필수 근거

- `tests/test_validation_orchestrator_soft_failure.py`
- `tests/test_artifact_logging.py`
- `tests/test_sc6_observability.py`
- `tests/test_bridge_quality_summary.py`
- `docs/2026-03-13/main_a-facade-shim-detail-remediation-execution-ssot.md`

### 산출물

- `docs/2026-03-13/ROP-T2-soft-failure-audit-utf8-findings.md`

---

## 6. Terminal 3 - Structured Sink Alignment

### 담당 범위

- runtime artifact / sink
  - `logs/runtime_audit_summary.json`
  - `logs/episode_production.jsonl`
  - `project_data.db` (`stage_attempts`, `director_selections`)
  - `logs/pass_rate_monitor.json`
- 직접 관련 코드
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/artifact_logging.py`

### 핵심 검사 포인트

1. attempt-level sink alignment가 DB / JSONL / session log / summary 사이에서 유지되는가
2. `stage_attempts` thin sink 문제가 여전히 남아 DB 단독 포렌식을 막는가
3. `warnings`, `selection_reason`, `verdict_reason`, `artifact_path`, `candidate_key`, `attempt_key`가 동일 사실을 보존하는가
4. Stage3 / Stage4에서 sink strength 차이가 operator 오판을 만들지 않는가
5. 기존 log audit 문서의 판단과 현재 sink schema가 같은가

### 필수 근거

- `tests/test_director_feedback_loop.py`
- `tests/test_stage4_post_processor.py`
- `docs/2026-03-13/stage4-9ep-log-full-survey-3pass-final-audit.md`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- `docs/2026-03-13/stage3-10ep-log-remediation-postfix-3pass-closure.md`

### 산출물

- `docs/2026-03-13/ROP-T3-structured-sink-alignment-findings.md`

---

## 7. Terminal 4 - Stage 0 / Style Guide / POV Provenance Artifact

### 담당 범위

- `modules/core/stage0/__init__.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage01_helpers.py`
- `modules/core/project_support.py`
- 관련 artifact
  - `{project}/stage0_output/style_guide.json`
  - style cache meta

### 핵심 검사 포인트

1. `style_guide.json`와 style cache meta가 user-selected POV, extracted POV, effective POV, policy provenance를 정확히 보존하는가
2. Stage 0 artifact가 planning / validation / Stage 3 summary / Stage 4 summary와 같은 SSOT를 바라보는가
3. POV provenance가 runtime override로만 메워지고 persisted artifact는 stale하게 남지 않는가
4. mixed POV / external insert policy 보강 이후에도 artifact refresh proof가 필요한 프로젝트가 남아 있는가
5. Stage 0 artifact contract와 operator-facing summary/log field가 같은 naming과 의미를 공유하는가

### 필수 근거

- `tests/test_stage0_pov.py`
- `tests/test_stage0_work_guard_style_cache.py`
- `tests/test_project_support.py`
- `docs/2026-03-13/viewpoint-mixed-pov-full-survey-3pass-final-audit.md`
- `docs/2026-03-13/viewpoint-primary-pov-external-insert-remediation-postfix-3pass-closure.md`

### 산출물

- `docs/2026-03-13/ROP-T4-stage0-pov-styleguide-provenance-findings.md`

---

## 8. Terminal 5 - Runtime Proof / Canary / Regression Surface

### 담당 범위

- canary / rerun / follow-up audit 문서
- artifact refresh / live rerun proof
- 관련 regression test와 runtime checklist

### 핵심 검사 포인트

1. 코드와 테스트는 닫혔는데 runtime proof가 아직 필요한 surface가 무엇인지 분리 가능한가
2. canary / live rerun이 observability, provenance, artifact contract를 실제로 입증하는가
3. 기존 follow-up / postfix closure 문서가 runtime-only uncertainty를 남긴 경우 그 범위가 정확히 무엇인가
4. 동일 surface를 재조사해야 하는지, fresh proof만 있으면 되는지 구분 가능한가
5. 최종 통합 시 `code-closed / runtime-open / stale-artifact / sink-open` ledger를 재구성할 수 있는가

### 필수 근거

- `docs/2026-03-13/logging-hardening-moderate-followup-postfix-3pass-closure.md`
- `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md`
- `docs/2026-03-13/stage4-director-cw-log-informed-remediation-postfix-5pass-closure.md`
- `docs/2026-03-13/today-detail-sideeffect-connectivity-liverun-checklist.md`
- 관련 canary / follow-up test와 runtime artifact

### 산출물

- `docs/2026-03-13/ROP-T5-runtime-proof-regression-findings.md`

---

## 9. 명시적 제외 범위

아래는 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- Stage 2/3/4 생성 품질 그 자체
- boot/project binding control-plane 자체
- desktop risk gate / API security / Lite Mode
- remediation patch 작성
- unrelated global logging cleanup

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/ROP-T1-main-a-context-log-wiring-findings.md`
- `docs/2026-03-13/ROP-T2-soft-failure-audit-utf8-findings.md`
- `docs/2026-03-13/ROP-T3-structured-sink-alignment-findings.md`
- `docs/2026-03-13/ROP-T4-stage0-pov-styleguide-provenance-findings.md`
- `docs/2026-03-13/ROP-T5-runtime-proof-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/runtime-observability-provenance-artifact-detail-consolidated-findings.md`
- `docs/2026-03-13/runtime-observability-provenance-artifact-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 main_a, logging-hardening, stage4-log, viewpoint 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `operator-facing evidence-layer contract` 자체가 다른 책임 경계를 가지면 신규 `ROP-*` finding 가능
- 신규 finding에는 아래 중 하나를 반드시 적는다
  - `none`
  - `related-but-new-evidence-layer-surface`
  - `already-covered-do-not-reopen`

---

## 11. 실행 완료 판정

아래를 모두 만족해야 본 오더가 닫힌다.

1. T1 ~ T5 결과 문서가 모두 존재한다.
2. 각 문서가 `PASS1 -> PASS2 -> PASS3` 요약을 가진다.
3. 각 finding이 코드 근거, 테스트 근거, downstream 경계, 중복 여부를 모두 가진다.
4. 통합본이 `wiring / sink / artifact / provenance / runtime-proof` ledger를 재구성한다.
5. 통합본 3PASS 재감리가 최종 오탐 제거 여부와 SSOT 승격 가능성을 명시한다.

---

## 12. 초기 상태

- 본 오더 문서는 `execution-ready`다.
- 결과 문서와 통합 문서는 본 오더와 함께 생성되지만 초기 상태는 모두 `template / not executed`다.
- 조사 단계가 끝나기 전에는 확정 finding이 없는 상태로 본다.

---

## 13. 현재 조사 현황

- 기준일: `2026-03-13`
- 조사 현황: `조사 완료`
- 메모: 개별 조사 결과가 누적되고 있으나, operator-facing evidence-layer ledger를 재구성하는 통합본 및 `3PASS 재감리` 전 단계이므로 본 트랙은 계속 조사 중으로 관리한다.
