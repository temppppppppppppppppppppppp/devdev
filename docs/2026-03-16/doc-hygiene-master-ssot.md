# 문서 위생 조사 SSOT (2026-03-16)

> 조사 기준: 코드베이스 정적 분석 (Grep/Glob/Read). pytest 미사용.
> 조사 범위: docs/2026-03-14, 03-15, 03-16 전량 (~210파일)
> 3pass 재감리 완료. 오탐 1건 수정 (X-2 FactLedger: 미완→완료 상향).

---

## 요약 통계

| 상태 | 건수 | 비율 |
|------|------|------|
| [완료] | 30 | 68% |
| [폐기] | 4 | 9% |
| [참고자료] | 2 | 5% |
| [추적필요] | 3 | 7% |
| [미완] | 1 | 2% |
| (부모 따라감) | ~170 | — |

**핵심**: execution-ssot 44건 중 실질 미완은 1건뿐 (스크립트 파일 누락).

---

## A. 03-14 execution-ssot (11건) — 전량 [완료]

| # | 파일 | 상태 |
|---|------|------|
| 1 | db-bootstrap-migration-noise-remediation-execution-ssot.md | [완료] |
| 2 | desktop-control-plane-surface-hardening-execution-ssot.md | [완료] |
| 3 | encoding-boundary-mojibake-refresh-remediation-execution-ssot.md | [완료] |
| 4 | frontier-lag-nonstop-contract-remediation-execution-ssot.md | [완료] |
| 5 | investment-epub-gemini-corpus-execution-ssot.md | [완료] |
| 6 | regression-canary-surface-rationalization-execution-ssot.md | [완료] |
| 7 | residual-print-ui-log-db-full-survey-3pass-execution-ssot.md | [완료] |
| 8 | runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md | [완료] |
| 9 | runtime-bootstrap-orchestration-hardening-execution-ssot.md | [완료] |
| 10 | stage0-operator-surface-contract-hardening-execution-ssot.md | [완료] |
| 11 | auto-frontier-lag-n-arc-test-harness-ssot.md | [완료] |

## B. 03-15 execution-ssot (14건)

| # | 파일 | 상태 | 비고 |
|---|------|------|------|
| 1 | backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md | [완료] | |
| 2 | backend-front-control-plane-connectivity-remediation-execution-ssot.md | [폐기] | #1에 의해 대체 |
| 3 | frontierlag-nonstop-utf8-hygiene-remediation-execution-ssot.md | [완료] | menu7 정책은 #5가 최종 |
| 4 | interactive-prompt-contract-refresh-execution-ssot.md | [완료] | menu7 정책은 #5가 최종 |
| 5 | menu7-desired-arc-input-contract-remediation-execution-ssot.md | [완료] | |
| 6 | persistence-observability-boundary-remediation-execution-ssot.md | [폐기] | #7에 의해 대체 |
| 7 | persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md | [완료] | |
| 8 | post-remediation-unqueued-survey-followups-execution-ssot.md | [완료] | TF-012~020 전량 처리 |
| 9 | runtime-operator-surface-unification-refresh-remediation-execution-ssot.md | [완료] | |
| 10 | runtime-operator-surface-unification-remediation-execution-ssot.md | [폐기] | #9에 의해 대체 |
| 11 | source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md | [완료] | |
| 12 | source-text-utf8-hygiene-remediation-execution-ssot.md | [폐기] | #11에 의해 대체 |
| 13 | stagewise-manuscript-truth-and-narrative-continuity-followup-execution-ssot.md | [미완] | `scripts/generate_stagewise_manuscript_truth_report.py` 누락 |
| 14 | 원고_모순방지_3pass_감리_및_개선_execution_ssot.md | [추적필요] | blocked 상태, TF-MS 전량 pending |

## C. 03-16 execution-ssot + report (9건)

| # | 파일 | 상태 | 비고 |
|---|------|------|------|
| 1 | continuity-history-and-escalation-guardrails-execution-ssot.md | [완료] | |
| 2 | director-feedback-decision-integrity-hardening-execution-ssot.md | [완료] | |
| 3 | legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md | [완료] | |
| 4 | persistence-context-authority-hardening-execution-ssot.md | [완료] | X-2 관측성 추가 확인 |
| 5 | stage4-menu7-arc-transition-enter-skip-remediation-execution-ssot.md | [완료] | |
| 6 | opus-survivor-followup-execution-roadmap.md | [완료] | 3개 lane 전량 완료 |
| 7 | manuscript-contradiction-audit-master-report.md | [추적필요] | P0-P3 제안만, 코드 변경 없음 |
| 8 | legacy-manuscript-contradiction-synthesis-master-report.md | [완료] | 추진 1건 실행 확인 |
| 9 | legacy-manuscript-contradiction-manual-survey-and-current-risk-assessment.md | [추적필요] | 평가 문서, 실행 미착수 |

## D. TF 평가 + Opus Deepdive (10건)

| # | 파일 | 상태 | 비고 |
|---|------|------|------|
| 1 | tf-013-db-connection-pooling-evaluation.md | [완료] | NO-GO 결정 |
| 2 | tf-017-jsonl-sink-consolidation-evaluation.md | [완료] | NO-GO 결정 |
| 3 | tf-018-di-context-slot-audit-evaluation.md | [완료] | NO-GO 결정 |
| 4 | tf-020-test-coverage-mapping-report.md | [참고자료] | 커버리지 스냅샷 |
| 5 | tf-014-console-print-audit.md | [완료] | GO, 코드 반영 확인 |
| 6 | tf-015-ruff-auto-fix.md | [완료] | GO, ruff 0 |
| 7 | tf-016-ruff-manual-fix.md | [완료] | GO, noqa 확인 |
| 8 | tf-019-guard-chain-config-validation.md | [완료] | GO, 코드 반영 확인 |
| 9 | opus/all-stage-deepdive-fix-candidates-ssot.md | [완료] | 3pass 재감리: X-2 관측성 추가 확인 |
| 10 | opus/3pass-audit-master-summary.md | [참고자료] | 연구 메모, 실행 권한 아님 |

## E. 나머지 파일 상태 규칙 (~170건)

| 유형 | 규칙 | 기본 상태 |
|------|------|-----------|
| 3pass-audit | 부모 execution-ssot 상태를 따라감 | 부모와 동일 |
| evidence (txt/json) | 부모 문서 존재 확인 → 부모 상태 따라감 | [참고자료] |
| survey / deep-global-survey | 실행 항목 아님, 조사 산출물 | [참고자료] |
| inventory / side-effects / entrypoints | raw evidence | [참고자료] |
| opus/ 개별 deepdive (16건) | 마스터(D-9)를 따라감 | [참고자료] |
| cross-cut / uncertainty-ledger | 메타 분석 | [참고자료] |
| execution-roadmap | 부모 execution-ssot들 상태 따라감 | 부모 전량 완료 시 [완료] |
| 승인요청서-방어논리-전항목.md | 단독 참고 문서 | [참고자료] |
| vertex-ai-gemini-tuning-cost-risk-note.md | 비용/리스크 메모 | [참고자료] |

---

## 미결 항목 (액션 필요)

### 1. [미완] stagewise-manuscript-truth 스크립트 누락
- **문서**: 03-15 #13
- **누락**: `scripts/generate_stagewise_manuscript_truth_report.py`
- **모듈은 존재**: `modules/core/stagewise_manuscript_truth_report.py`
- **조치**: 스크립트 생성 또는 문서에서 해당 주장 제거

### 2. [추적필요] 원고 모순방지 TF-MS 전량 pending
- **문서**: 03-15 #14
- **상태**: blocked, 프로젝트 스코프 한정
- **조치**: 3아크런 결과 확인 후 TF-MS 필요성 재평가

### 3. [추적필요] manuscript-contradiction P0-P3 제안
- **문서**: 03-16 #7
- **상태**: 75개 모순 식별, 개선 제안만 존재
- **조치**: 3아크런 결과에서 모순 재현 여부로 우선순위 결정

### 4. [추적필요] legacy-manuscript 리스크 평가
- **문서**: 03-16 #9
- **상태**: 5개 리스크 표면 식별, 실행 미착수
- **조치**: 레거시 원고 사용 계획이 있을 때만 활성화

---

## 3pass 재감리 기록

| Pass | 작업 | 결과 |
|------|------|------|
| Pass 1 | 4개 에이전트 병렬 교차검증 (44 핵심 문서) | 초안 태그 부착 |
| Pass 2 | 의심 항목 재검증 (스크립트 누락, X-2 FactLedger) | X-2: 미완→완료 상향 (관측성 추가 확인) |
| Pass 3 | 부모-자식 매핑 + 최종 확정 | 오탐 0건, 누락 0건 |
