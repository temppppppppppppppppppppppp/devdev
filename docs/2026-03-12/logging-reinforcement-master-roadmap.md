# 로깅 체계 보강 마스터 로드맵

문서 역할: `PASS_WITH_FIX / structural inplace / Stage 2~4 sink 계약 / logging analytics / rerun gate`를 하나의 로깅 보강 SSOT로 묶는다.

작성 기준일: 2026-03-12
현재 상태: `Phase 1~6 구현 완료`, `manual context 운영 규칙 / Stage 2·3 rich lifecycle gap 잔여`
현재 확신도: `95%`

## 1. 직접 대상
- `director_selections`
- `episode_production.jsonl`
- `stage_attempts`
- `pass_rate_monitor.json`
- `FailureAnalyzer`와 하위 consumer
- `PASS_WITH_FIX -> patch -> PASS/REJECT`의 초기/최종 verdict 분리
- structural inplace 관측성(`patch_trace`, `attempt_key`)

## 2. 비대상
- `CW generate_ensemble()` 중심의 일반 글쓰기 구조 변경
- full artifact snapshot 시스템의 전면 도입
- UI 전용 warning/debug 로그 정리
- unrelated logging cleanup

## 3. 2026-03-12 기준 구현 반영

### 3.1 새 기준선
- Stage 4 `episode_production.jsonl`은 `initial_verdict`, `final_verdict`, `initial_score`, `final_score`, `patch_trace`, `attempt_key`를 함께 남긴다.
- `ChiefWriter`는 `_last_inplace_patch_trace`에 `patch_strategy`, `patch_targets`, `fallback_reason`, `focus`, `structural_attempted`를 남긴다.
- `FailureAnalyzer.patch_trace_summary()`는 Stage 4 JSONL 기준으로 structural patch 결과를 집계한다.
- `FailureAnalyzer.sink_alignment_summary()`는 `attempt_key` 기준으로 `director_selections`, `episode_production.jsonl`, `stage_attempts`, `pass_rate_monitor.json`의 정합성을 자동 점검한다.
- `Stage3Orchestrator`는 external success set을 `PASS`, `PASS_WITH_WARNING`으로 제한한다.
- `PassRateMonitor`는 `attempt_key`, `final_verdict`, `patch_strategy`, `structural_attempted`를 optional field로 수용한다.
- `DBManager.get_recent_episode_scores()`는 더 이상 `director_selections`의 `PASS_WITH_FIX`를 pass-like로 읽지 않고, `stage_attempts`의 final verdict 기준으로 조회한다.
- Stage 2/3/4는 모두 `build_attempt_key()`를 통해 공통 `attempt_key` 규칙을 쓰고, 표준 런타임에서는 `current_project.metrics_session_id`를 suffix로 붙인다.

### 3.2 현재 sink 계약
| sink | 역할 | 현재 보장 | 남은 공백 |
| --- | --- | --- | --- |
| `director_selections` | 초기 Director 선택/판정 sink | 초기 verdict/score/reason, firewall metadata, `attempt_key` | final verdict 직접 저장 안 함 |
| `episode_production.jsonl` | Stage 4 round trace sink | initial/final split, `patch_trace`, round cost, `attempt_key` | Stage 4 전용, cross-stage artifact join 없음 |
| `stage_attempts` | 최종 stage attempt sink | final verdict/score/fix_scope/model/prompt_version/`attempt_key`, `candidate_key`, `content_hash`, `artifact_path` | Stage 2/3 rich lifecycle split 없음 |
| `pass_rate_monitor.json` | 경량 운영 모니터 sink | success boolean, duration/token, `attempt_key`, `final_verdict`, patch lineage | `initial_verdict` 직접 보관 안 함 |
| `FailureAnalyzer` | 운영 분석/집계 sink | final semantics 기반 pass rate, `patch_trace_summary()`, `sink_alignment_summary()`, artifact mismatch/file existence audit | Stage 2/3 rich lifecycle split 없음 |

## 4. 전수조사 결과 요약

### 4.1 닫힌 항목
- Stage 4 initial/final semantics split
- Stage 4 structural inplace 최소 관측성(`patch_trace`)
- Stage 2/3/4 공통 `attempt_key`
- Stage 3 `pass_rate_monitor` parity
- `PASS_WITH_FIX` pass-like legacy helper query 제거
- `pass_rate_monitor` final verdict granularity 보강

### 4.2 남은 항목
- Stage 4 외 Stage 2/3에는 `episode_production` 급의 rich lifecycle sink가 없다.
- `metrics_session_id`가 없는 비표준/manual context에서는 legacy key 형식으로 남을 수 있다.

## 5. Phase 로드맵

### Phase 1. sink 계약 고정
상태: `완료`

- 목표: sink별 역할과 initial/final semantics를 문서/코드에서 일치시킨다.
- 포함:
  - `director_selections`는 initial sink
  - `stage_attempts`와 `pass_rate_monitor`는 final sink
  - `episode_production.jsonl`은 Stage 4 lifecycle sink
- 성공 기준:
  - Stage 3/4와 FailureAnalyzer가 같은 final verdict 정의를 사용한다.

### Phase 2. legacy consumer 정리
상태: `완료`

- 목표: `PASS_WITH_FIX`를 final success처럼 읽는 consumer를 제거한다.
- 포함:
  - `DBManager.get_recent_episode_scores()` 정리
  - FailureAnalyzer pass-rate 의미 정렬
- 성공 기준:
  - final success 집계는 `PASS`, `PASS_WITH_WARNING`만 사용한다.

### Phase 3. stable linkage 최소화
상태: `완료`

- 목표: sink 간 deterministic join의 최소 단위로 `attempt_key`를 도입한다.
- 포함:
  - `director_selections`
  - `episode_production.jsonl`
  - `stage_attempts`
  - `pass_rate_monitor.json`
- 성공 기준:
  - 같은 attempt를 4개 sink에서 같은 key로 추적할 수 있다.

### Phase 4. monitor/stage_attempt uplift
상태: `완료`

- 목표: 운영 sink가 final verdict class와 patch lineage를 담게 만든다.
- 포함:
  - `PassRateMonitor` optional field 확대
  - Stage 3 writer parity
  - Stage 4 patch lineage 전달
- 성공 기준:
  - raw JSONL 없이도 monitor/DB에서 final verdict class와 patch lineage를 읽을 수 있다.

### Phase 5. rerun linkage hardening
상태: `완료`

- 목표: rerun 간에도 join 충돌 없이 운영 검증이 가능하게 한다.
- 포함:
  - `attempt_key`에 `metrics_session_id` 주입
  - `stage_attempts.session_id` 동시 반영
- 성공 기준:
  - 표준 런타임에서는 동일 `ep/arc/attempt`라도 rerun이 다르면 key가 충돌하지 않는다.

### Phase 6. artifact linkage
상태: `baseline 완료`

- 목표: attempt에서 candidate/artifact까지 추적 가능하게 만든다.
- 포함:
  - `candidate_key`
  - `content_hash`
  - `artifact_path`
- 성공 기준:
  - `director_selections`와 실제 manuscript/blueprint artifact를 deterministic join할 수 있다.
- 현재 구현:
  - `modules/core/artifact_logging.py`가 `logs/artifacts/...` snapshot을 기록한다.
  - Stage 2/3/4 writer가 `candidate_key`, `content_hash`, `artifact_path`를 final sink에 남긴다.
  - Stage 4 `episode_production.jsonl`도 같은 linkage를 기록한다.
  - `FailureAnalyzer.sink_alignment_summary()`가 `candidate_key`, `content_hash`, `artifact_path`, artifact file existence를 cross-sink로 점검한다.
- 잔여:
  - 비표준/manual context의 `metrics_session_id` 운영 규칙
  - Stage 2/3 rich lifecycle sink 보강

## 6. P0/P1/P2 우선순위

### P0 Correctness
- sink 역할 고정
- legacy `PASS_WITH_FIX` pass-like consumer 제거
- Stage 3/4 final semantics 정렬

### P1 Observability
- `attempt_key`
- `pass_rate_monitor` verdict/patch lineage 보강
- Stage 3 parity
- `patch_trace_summary()`
- `sink_alignment_summary()`

### P2 Rich Linkage
- `candidate_key`
- `content_hash`
- `artifact_path`

## 7. 성공 기준
- `PASS_WITH_FIX`의 초기 판단과 최종 결과를 sink별로 설명할 수 있다.
- Stage 4 structural inplace는 `patch_trace`와 `patch_trace_summary()`로 추적 가능하다.
- Stage 4/운영 sink 정합성은 `sink_alignment_summary()`로 자동 점검 가능하다.
- artifact linkage 정합성과 artifact file existence도 `sink_alignment_summary()`로 자동 점검 가능하다.
- final success 집계는 `PASS`, `PASS_WITH_WARNING`만 사용한다.
- Stage 2/3/4 attempt는 공통 `attempt_key`로 최소 join이 가능하다.
- Stage 2/3/4 final artifact는 `candidate_key`, `content_hash`, `artifact_path`로 추적 가능하다.

## 8. 관련 코드
- `modules/core/logging_keys.py`
- `modules/core/artifact_logging.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/db_manager.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/failure_analyzer.py`

## 9. 관련 문서
- `docs/2026-03-11/logging-system-audit-95.md`
- `docs/2026-03-12/pass-with-fix-master-roadmap.md`
- `docs/2026-03-12/pass-with-fix-improvement-execution-plan.md`
- `docs/2026-03-12/stage4-live-rerun-checklist.md`
- `docs/2026-03-12/logging-reinforcement-3pass-audit.md`
- `docs/2026-03-12/logging-reinforcement-execution-plan.md`
