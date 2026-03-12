# 시스템 전역 retained finding 실현 실행 계획

작성일: 2026-03-12  
인코딩: UTF-8  
기준 문서:
- `docs/2026-03-12/system-wide-full-audit-3pass-merged-final.md`
- `docs/2026-03-12/stage4-canary-log-audit.md`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`

## 0. 문서 역할

이 문서는 감사 문서를 대체하지 않는다.  
역할은 두 감사 문서에 남은 retained finding을 `실제 수정 착수 가능한 work package`로 바꾸는 것이다.

실행 원칙:
- 감사 문서는 증거 원본으로 동결한다.
- 낮은 확신 때문에 문제를 빼지 않는다.
- 반대로 이미 `rejected` 또는 `runtime-only`로 닫힌 항목은 이번 범위에 무단 재투입하지 않는다.
- canary blocker와 Stage 4 데이터 오염 경로를 우선 닫고, 문서/샘플 refresh는 그 다음에 한다.

이번 실행 계획의 직접 목표는 아래 5축이다.

1. canary/dirty 경로의 재현성, SSOT, 문서 충돌 제거
2. Stage 4 manuscript/state 계약 복구
3. Stage 4 lineage/sink/canary hard-gate 정합성 복구
4. structural patch 및 runtime defect 보수
5. telemetry/observability 및 artifact hygiene 보강

직접 비대상:
- Electron packaging 계약 변경
- `rejected`로 닫힌 기존 주장 재확대
- full/live rerun 선실행
- 코드 계약이 닫히기 전 tracked artifact 일괄 정리
- CW 전면 재설계

## 1. 3-Pass 재감리 결과

### Pass 1. retained finding 전량 매핑

| 출처 | finding | 심각도 | 처리 방식 | 배정 |
|---|---|---|---|---|
| system-wide F-01 | Stage 4 PASS_WITH_FIX `state_updates` merge 계약 드리프트 | P1 | 구현 | `WP-2` |
| system-wide F-02 | `docs/stage_map` 상태 원장 충돌 | P1 | 문서/계약 sync | `WP-1` |
| system-wide F-03 | dirty lineage/canary 경로의 untracked 의존성 | P1 | 구현+버전관리 정리 | `WP-1` |
| system-wide F-04 | 멀티-provider SSOT 드리프트 | P1 | 구현+문서 sync | `WP-1` |
| system-wide F-05 | TruthGate 회상 예외 줄 단위 갭 | P2 | 구현 | `WP-4` |
| system-wide F-06 | telemetry metrics/DB 비대칭 | P2 | 구현 | `WP-5` |
| system-wide F-07 | tracked `episode_production.jsonl` 샘플 drift | P2 | post-fix refresh | `WP-3`, `Phase G` |
| system-wide F-08 | soft-failure artifact residue | Observation | hygiene 정리 | `WP-5`, `Phase G` |
| canary F-01 | `revised_manuscript` wrapper 최종 저장 | P1 | 구현 | `WP-2` |
| canary F-02 | 투자물 canary에 무협 state schema 주입 가능성 | P1급 root candidate | 구현 | `WP-2` |
| canary F-03 | 현재 canary가 자기 계약 기준 FAIL | P1 umbrella | acceptance gate | `WP-2`, `WP-3`, `WP-5` |
| canary F-04 | candidate/artifact linkage drift | P1 | 구현 | `WP-3` |
| canary F-05 | local issue가 structural inplace로 라우팅되지 않음 | P2 | 구현 | `WP-4` |
| canary F-06 | patch lineage flag 의미 불일치 | P2 | 구현 | `WP-3` |
| canary F-07 | `runtime_audit_summary.json` 정보량 부족 | P2 | 구현 | `WP-5` |
| canary F-08 | `causal_graph` dual-write runtime bug | P2 | 구현 | `WP-4` |
| canary F-09 | downstream verifier 사후 수습 | 보조 신호 | root-cause 확인용 근거 유지 | `WP-2`, `WP-4` |
| canary F-10 | `TF-H` 반복 경고 | 보조 신호 | 후행 관찰 | `WP-5` |
| canary F-11 | canary test가 후행 결함을 충분히 못 덮음 | 보조 신호 | 테스트 보강 | `WP-2`~`WP-5` 공통 |

Pass 1 판정:
- 두 감사 문서의 retained/observation 항목은 전부 배정됐다.
- `canary F-03`는 독립 수정 항목이 아니라, `WP-2/3/5` 완료 후 닫혀야 하는 umbrella gate로 분류했다.
- 누락 항목은 없다.

### Pass 2. root finding 압축 및 선후관계 고정

중복을 합치면 실제 수정 묶음은 아래 5개다.

1. `WP-1 재현성/SSOT`: untracked canary stack, provider direct path, deprecated fallback, stage_map 충돌
2. `WP-2 Stage 4 manuscript/state 계약`: wrapper 저장, genre mapping drift, PASS_WITH_FIX state merge
3. `WP-3 Stage 4 lineage/canary 계약`: candidate key, artifact path, patch flag, tracked sample refresh
4. `WP-4 patch routing/runtime defect`: structural inplace routing, `causal_graph`, TruthGate
5. `WP-5 observability/hygiene`: runtime audit summary, DB telemetry parity, soft-failure residue, TF-H 관찰

선후관계:
- `WP-1`은 재현성 기반이므로 항상 먼저 한다.
- `WP-2`는 Stage 4 데이터 오염을 줄여 이후 lineage 분석의 기준을 안정화한다.
- `WP-3`은 `WP-2` 이후에 해야 canary hard-gate가 naming drift와 실제 오염을 구분할 수 있다.
- `WP-4`는 `WP-2`와 병행 가능하지만, patch trace 의미를 공유하므로 머지 시점은 `WP-3` 직전 또는 직후로 고정한다.
- `WP-5`는 observability 보강과 post-fix hygiene를 담당하므로 마지막에 묶는다.

### Pass 3. 누락/과잉 범위 점검

누락 없음:
- system-wide P1/P2 retained finding 전량 포함
- canary 확정 문제 전량 포함
- canary 보조 신호 중 구현 연결이 있는 항목 포함

과잉 범위 차단:
- `rejected`/`runtime-only` 항목은 재유입하지 않음
- Electron/UI는 non-finding으로 유지
- full/live rerun은 코드 계약이 닫히기 전 실행 금지

판정:
- 이 문서는 `execution-ready`다.
- 현재 기준 확신도는 `95%`다.
- 남은 5%는 실제 코드 변경 후 회귀 실행과 canary rerun에서만 닫을 수 있다.

## 2. Work Packages

### WP-1. 재현성 / SSOT / 문서 충돌 잠금

목적:
- canary helper stack을 dirty worktree 전용 상태에서 빼고, 코드/문서/설정 SSOT를 하나로 잠근다.

대상 파일:
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py`
- `modules/core/artifact_logging.py`
- `modules/core/logging_keys.py`
- `main_a.py`
- `config/models.yaml`
- `CLAUDE.md`
- `docs/stage_map/doc_status.md`
- `docs/stage_map/stage1.md`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`
- `tests/test_llm_router.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_stage4_canary_tools.py`

구현 요구:
- canary helper/runner/support module을 정식 tracked 경로로 잠근다.
- `_flash_ask_cb` direct path를 router 경로와 정렬하거나, 남겨야 한다면 문서의 예외 목록과 정확히 일치시킨다.
- `config/models.yaml` deprecated fallback entry와 `CLAUDE.md` SSOT 설명의 drift를 닫는다.
- `docs/stage_map/doc_status.md`와 `docs/stage_map/stage1.md`를 같은 상태로 맞춘다.
- runbook이 실제 canary helper/runner와 같은 hard gate를 설명하도록 유지한다.

acceptance:
- canary 관련 핵심 파일이 더 이상 “로컬 dirty 상태에서만 존재하는 전제”에 의존하지 않는다.
- provider routing과 fallback 문서가 코드와 같은 예외 집합을 쓴다.
- `docs/stage_map` 내부 직접 충돌이 사라진다.

예정 검증:
- `tests/test_llm_router.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_stage4_canary_tools.py`

### WP-2. Stage 4 manuscript/state 계약 복구

목적:
- Stage 4 patch 결과가 wrapper/장르 오염 없이 plain manuscript와 일관된 state update로 닫히게 한다.

대상 파일:
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/stage4_interview_round.py`
- `config/prompts/chief_writer.yaml`
- `tests/test_chief_writer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_pass_with_fix.py`

구현 요구:
- `revised_manuscript`를 unwrap 대상에 포함해 draft/artifact/DB/downstream prompt로 plain manuscript만 흐르게 한다.
- investment 계열 `genre name`과 `genre type`이 같은 내부 장르 코드로 정규화되게 한다.
- Stage 4 PASS_WITH_FIX 반복 경로의 `state_updates`가 overwrite가 아니라 계약된 merge 의미를 유지하게 한다.
- canary에서 확인된 downstream recovery(`actual_truth` 사후 보정)를 upstream 오염 은폐 수단으로 두지 않는다.

acceptance:
- Stage 4 patch 결과 저장물은 JSON wrapper가 아니라 manuscript text다.
- investment canary에서 `wuxia` fallback state schema가 주입되지 않는다.
- `PASS_WITH_FIX -> re-audit -> PASS/REJECT` 경로에서 `state_updates` 누적 계약이 유지된다.

예정 검증:
- `tests/test_chief_writer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_pass_with_fix.py`
- 필요 시 `tests/test_run_stage4_canary.py`

### WP-3. Stage 4 lineage / sink / canary hard-gate 정렬

목적:
- 동일 attempt가 sink마다 다른 이름과 다른 patch 의미를 남기지 않게 정리한다.

대상 파일:
- `modules/core/stage4_interview_round.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/failure_analyzer.py`
- `modules/core/artifact_logging.py`
- `modules/core/logging_keys.py`
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py`
- `projects/test_project/logs/episode_production.jsonl`
- `tests/test_failure_analyzer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_canary_tools.py`
- `tests/test_run_stage4_canary.py`

구현 요구:
- `candidate_key`의 canonical form을 하나로 고정하고 lifecycle/final sink가 같은 key를 쓰게 한다.
- artifact naming/path contract를 canonical form과 같은 규칙으로 맞춘다.
- `is_patch`, `flags.patch_mode`, `patch_trace.patch_strategy`, `structural_attempted`의 의미를 sink별로 동일하게 맞춘다.
- canary helper의 mismatch 집계가 실제 drift를 잡도록 유지하되, naming drift를 계약 밖 ambiguity로 남기지 않는다.
- 코드 계약이 닫힌 뒤 tracked sample artifact는 새 schema를 대표하도록 refresh한다.

acceptance:
- 동일 attempt가 sink마다 서로 다른 `candidate_key`/`artifact_path`를 남기지 않는다.
- canary hard gate가 실제 mismatch만 fail로 잡는다.
- patch lineage 관련 필드가 서로 모순되지 않는다.
- `projects/test_project/logs/episode_production.jsonl`이 최신 contract 대표 샘플이 된다.

예정 검증:
- `tests/test_failure_analyzer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_canary_tools.py`
- `tests/test_run_stage4_canary.py`

### WP-4. structural patch routing 및 runtime defect 보수

목적:
- local issue가 구조적 patch 경로를 타야 할 때 놓치지 않게 하고, Stage 4 후처리의 비치명 runtime bug를 닫는다.

대상 파일:
- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/truth_gate.py`
- `modules/core/db_manager.py`
- `tests/test_chief_writer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_graph_layer.py`
- `tests/test_lm_post1.py`

구현 요구:
- POV/국소 장면 수정 같은 Director feedback이 `unclassified_feedback`으로 낙하하지 않도록 patch focus 분류를 보강한다.
- structural inplace가 필요한 경우 `patch_trace`에 실제 시도 사실이 반영되게 한다.
- `causal_graph` dual-write가 문자열 payload에서 `.get` 예외를 내지 않게 입력 shape를 정규화한다.
- TruthGate 회상 예외가 같은 줄의 deceased 행동 검출까지 날려버리지 않게 line-level skip 규칙을 보수한다.

acceptance:
- canary 유형의 국소 수정 피드백이 structural patch 경로로 라우팅된다.
- `causal_graph dual-write 실패 (비치명)` 로그가 동일 원인으로 재발하지 않는다.
- TruthGate가 recall 예외가 있는 줄에서도 deceased 행동 검출을 놓치지 않는다.

예정 검증:
- `tests/test_chief_writer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_graph_layer.py`
- `tests/test_lm_post1.py`

### WP-5. observability / telemetry / hygiene 보강

목적:
- canary와 시스템 전역에서 남은 관측 공백을 채우고, post-fix 산출물 위생 정리를 완료한다.

대상 파일:
- `modules/core/services/audit_service.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- `modules/core/db_manager.py`
- `modules/core/soft_failure.py`
- `modules/core/stage4_post_processor.py`
- `modules/validation/validation_orchestrator.py`
- `MagicMock/`
- `tests/test_audit_service.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_base_agent.py`
- `tests/test_cost_tracking.py`
- `tests/test_db_manager.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_validation_orchestrator_soft_failure.py`

구현 요구:
- `runtime_audit_summary.json`가 completion tag뿐 아니라 event count와 핵심 집계를 유지하게 한다.
- metrics 계층과 DB `llm_calls` 사이의 token/cost observability 차이를 줄인다.
- soft-failure 경로 보호는 유지하되, worktree residue 정리 정책을 같이 확정한다.
- `TF-H` 반복 경고는 이번 phase에서 blocker로 올리지 않되, Stage 4 contract fix 후에도 지속되면 follow-up backlog로 승격한다.

acceptance:
- Stage 4 완료 시 runtime summary가 비어 있지 않다.
- DB와 metrics가 같은 호출의 핵심 token/cost 정보를 같은 수준으로 추적한다.
- `MagicMock/.../soft_failures.jsonl` 같은 residue가 다시 생기지 않도록 보호/정리 기준이 있다.

예정 검증:
- `tests/test_audit_service.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_base_agent.py`
- `tests/test_cost_tracking.py`
- `tests/test_db_manager.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_validation_orchestrator_soft_failure.py`

## 3. 순차 체크리스트

### Phase A. 기준선 동결
- [x] 감사 문서를 증거 원본으로 동결
- [x] 본 문서를 implementation SSOT로 사용
- [x] `rejected/runtime-only` 항목 재유입 금지

### Phase B. 재현성/SSOT 잠금
- [ ] `WP-1` 구현
- [ ] 관련 문서 sync
- [ ] canary helper/runbook/test 계약 동기화

### Phase C. Stage 4 데이터 계약 복구
- [ ] `WP-2` 구현
- [ ] wrapper/genre/state merge 회귀 테스트 추가

### Phase D. lineage/canary 정렬
- [ ] `WP-3` 구현
- [ ] tracked sample refresh 기준 확정

### Phase E. runtime defect 보수
- [ ] `WP-4` 구현
- [ ] patch routing/TruthGate/causal_graph 회귀 테스트 추가

### Phase F. observability/hygiene 보강
- [ ] `WP-5` 구현
- [ ] runtime summary/telemetry/residue 기준 정리

### Phase G. 통합 확인
- [ ] targeted regression 실행
- [ ] 문서 sync 최종 확인
- [ ] tracked sample/artifact refresh
- [ ] canary rerun은 blocker 해소 후 별도 승인 시점에만 수행

## 4. Done Definition

완료 조건:
- 두 감사 문서의 retained finding이 전부 코드 또는 문서 sync로 닫힌다.
- umbrella finding인 `canary F-03`가 실제로 닫힌다.
- tracked sample과 운영 문서가 새 계약을 대표한다.
- targeted regression이 녹색이다.
- full/live rerun 없이도 execution-ready 상태가 성립한다.

이번 문서의 최종 의미:
- 구현자는 이 문서만 보고 수정 착수 순서와 비대상 범위를 판단할 수 있어야 한다.
- 이후 추가 감리 문서는 이 계획을 기준으로 범위 이탈 여부만 판단하면 된다.
