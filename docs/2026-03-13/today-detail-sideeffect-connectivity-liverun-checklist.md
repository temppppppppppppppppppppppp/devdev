# 오늘 디테일·사이드이펙트·연결·라이브런 체크리스트

- 작성일: 2026-03-13
- 상태: `working checklist`
- 문서 역할: 오늘 남은 `디테일 소거 -> 전 영역 side-effect 재조사 -> 프론트/백엔드 연결 재확인 -> limited canary -> live run 확장` 순서를 체크리스트로 고정한다.
- 핵심 목표:
  - `운영 건강도`를 다시 흔들 수 있는 detail defect와 side effect를 당일 내로 식별/정리한다.
  - frontend/backend/desktop 계약이 현재 backend 수정본과 다시 일치하는지 확인한다.
  - live run은 작은 스코프에서 먼저 검증하고, 깨끗할 때만 병렬 3arc로 확장한다.
  - Rubric 기반 품질 평가 체계에서 `Very Good 이상`에 도달한다.

## 1. 기준 문서

- `docs/2026-03-13/OPUS-TF-5terminal-remediation-execution-3pass-audit.md`
- `docs/2026-03-13/OPUS-TF-5terminal-remediation-execution-ssot.md`
- `docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`
- `docs/2026-03-12/stage4-live-rerun-checklist.md`

## 2. 오늘의 최종 목표

- [ ] open detail finding이 `오탐 제거 + 우선순위 재분류`까지 끝난 상태다.
- [ ] 코드 변경이 필요한 항목은 회귀 테스트와 함께 닫힌다.
- [ ] 전 영역 side-effect 재조사 후 신규 `P0/P1`이 없다.
- [ ] frontend/backend/desktop 연결 계약이 현재 코드 기준으로 다시 일치한다.
- [ ] limited canary 1회가 hard gate를 통과한다.
- [ ] Rubric 기반 품질 평가에서 `Very Good 이상`을 확보한다.

## 3. Phase A. 디테일 소거

- [ ] 디테일 전수조사 범위를 고정한다.
- [ ] open finding을 `true defect / false positive / already closed / low-priority residue`로 분류한다.
- [ ] `P0/P1` 후보는 코드 기준으로 다시 직접 확인한다.
- [ ] 수정이 필요한 항목은 바로 패치 후보로 묶는다.
- [ ] 항목별 근거 파일과 재현 경로를 기록한다.

완료 조건:

- [ ] 오늘 수정 대상과 비대상 범위가 분리돼 있다.
- [ ] disputed count가 아니라 retained open set 기준으로 움직인다.

## 4. Phase B. 전 영역 Side-Effect 재조사

- [ ] `Stage 0 -> Stage 2 handoff` 재점검
- [ ] `Stage 3/4 Director sovereignty` 재점검
- [ ] `HUD / FactLedger / Guard` 무결성 재점검
- [ ] `cross-sink` 정합성 재점검
- [ ] `병렬/race/thread safety` 재점검
- [ ] `soft failure residue / logging residue / dirty artifact` 재점검

세부 체크:

- [ ] `runtime_audit_summary`, `stage_attempts`, `director_selections`, `pass_rate_monitor`, `episode_production`이 서로 모순되지 않는다.
- [ ] `candidate_key_mismatches == []`
- [ ] `selection_candidate_key_mismatches == []`
- [ ] `artifact_path_mismatches == []`
- [ ] `final_verdict_mismatches == []`
- [ ] `final_score_mismatches == []`
- [ ] `MagicMock/.../soft_failures.jsonl` 같은 residue는 현재 활성 버그와 분리해 해석한다.
- [ ] `save_world_state_atomic` rollback 류 경고는 실제 재발 여부를 따로 추적한다.

완료 조건:

- [ ] 신규 `P0/P1` 없음
- [ ] 운영 해석을 흐리는 잔여 side effect가 문서상 분리돼 있다

## 5. Phase C. 프론트엔드 / 백엔드 / 데스크톱 연결 재확인

- [ ] bridge server 포트가 `8300`으로 일치한다.
- [ ] `/quality/summary` surface 일치
- [ ] `/quality/dashboard` surface 일치
- [ ] `/safe-ops/preview` surface 일치
- [ ] `/quality/review` surface 일치
- [ ] dev mode와 packaged mode가 같은 project root 규칙을 따른다.
- [ ] desktop이 `dist/backend`, `dist/engine`, `backend.exe`, `engine.exe` 계약을 유지한다.
- [ ] quality dashboard / safe ops / review가 desktop bridge에서 같은 backend를 본다.

완료 조건:

- [ ] frontend/backend contract drift 없음
- [ ] packaged/dev split으로 인한 별도 blocker 없음

## 6. Phase D. Limited Canary

원칙:

- [ ] 첫 검증은 `1 project / 1 arc / ep_0001~ep_0004`로 제한한다.
- [ ] 첫 런에서 바로 `4개 병렬 3arc`로 가지 않는다.
- [ ] 실패/중단 시 project와 로그를 삭제하지 않는다.

사전 체크:

- [ ] baseline project를 새 target project로 분리한다.
- [ ] 최소 회귀 테스트가 green이다.
- [ ] 현재 worktree snapshot을 남긴다.

Hard gate:

- [ ] `draft_count == 4`
- [ ] `runtime_audit_summary.tag == "stage4_complete"`
- [ ] `pass_rate_monitor_exists == true`
- [ ] `stage4_attempts >= 4`
- [ ] `director_stage4_rows >= 4`
- [ ] `sink_alignment_summary.status == "ok"`
- [ ] `candidate_key_mismatches == []`
- [ ] `selection_candidate_key_mismatches == []`
- [ ] `artifact_path_mismatches == []`
- [ ] `legacy_key_attempts == 0`

완료 조건:

- [ ] limited canary가 `PASS` 또는 해석 가능한 `WARN`으로 닫힌다.
- [ ] 원인 미분리 `FAIL` 없이 다음 단계로 넘어간다.

## 7. Phase E. Rubric 품질 목표

핵심 목표:

- [ ] Rubric 기반 품질 평가 결과가 `Very Good 이상`이다.

Rubric 체크 축:

- [ ] 플롯 응집력
- [ ] 연속성 / 인과 정합성
- [ ] 캐릭터 일관성
- [ ] POV / 시점 안정성
- [ ] 문체 / 가독성
- [ ] 엔딩 완성도

합격 기준:

- [ ] 전체 평균이 `Very Good` 이상
- [ ] 핵심 축 중 `Good 미만` 없음
- [ ] 치명 결함으로 인한 fail-close 항목 없음
- [ ] low-level polish가 아니라 reader-facing 완성도 기준으로 판정한다

## 8. Phase F. Live Run 확장 규칙

- [ ] `1개 1arc canary` 통과
- [ ] 그 다음 `1개 3arc`
- [ ] 그 다음 `2개 병렬 3arc`
- [ ] 마지막으로 `4개 병렬 3arc`

확장 조건:

- [ ] 이전 단계 hard gate를 통과했을 때만 다음 단계로 간다.
- [ ] correctness, side effect, 부하 이슈를 한 번에 섞지 않는다.
- [ ] 병렬 확장 후에도 sink mismatch와 저장 rollback 여부를 다시 본다.

## 9. 최종 Go / No-Go

- [ ] 디테일 소거 완료
- [ ] side-effect 재조사 완료
- [ ] frontend/backend/desktop 연결 확인 완료
- [ ] limited canary 통과
- [ ] Rubric `Very Good 이상`
- [ ] 병렬 3arc 확장 여부를 evidence 기반으로 결정

한 줄 운영 순서:

`디테일 소거 -> side-effect 재조사 -> 프론트/백 연결 재확인 -> limited canary -> Rubric Very Good 이상 확인 -> 3arc/병렬 확장`
