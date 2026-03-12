# 로깅 체계 보강 실행 계획

문서 역할: [logging-reinforcement-master-roadmap.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/logging-reinforcement-master-roadmap.md)를 구현 단위로 쪼갠 실행 메모  
기준 상태: 2026-03-12 현재 코드/테스트 반영 기준

## 1. 실행 원칙
- `CW 일반 글쓰기 구조`는 이번 로깅 보강의 직접 대상이 아니다.
- `PASS_WITH_FIX / structural inplace / Stage 2~4 sink 정합성`이 우선 범위다.
- 새 필드는 기본적으로 backward-compatible optional field로 추가한다.
- 운영 판단은 raw 로그 단건이 아니라 `attempt_key` 기준 cross-sink 정합성으로 본다.

## 2. 완료된 Work Package

### WP-L1. sink inventory
상태: `완료`

- writer path 정리
  - `save_director_selection()`
  - `_append_episode_log()`
  - `save_stage_attempt()`
  - `record_attempt()`
- reader path 정리
  - `FailureAnalyzer`
  - `DBManager.get_recent_episode_scores()`
  - rerun checklist

### WP-L2. legacy `PASS_WITH_FIX` consumer 정리
상태: `완료`

- `DBManager.get_recent_episode_scores()`를 final sink 기준으로 전환
- final success semantics를 `PASS`, `PASS_WITH_WARNING`로 고정

### WP-L3. `attempt_key` schema
상태: `완료`

- 공통 helper: `modules/core/logging_keys.py`
- 반영 sink:
  - `director_selections`
  - `episode_production.jsonl`
  - `stage_attempts`
  - `pass_rate_monitor.json`
- Stage 2/3/4 writer가 같은 규칙을 사용한다.

### WP-L3b. rerun-safe `attempt_key`
상태: `완료`

- `main_a.py`가 `current_project.metrics_session_id`를 주입한다.
- Stage 2/3/4 writer가 같은 값을 `attempt_key` suffix와 `stage_attempts.session_id`에 반영한다.
- 표준 런타임에서는 rerun 간 `ep/arc/attempt` 충돌이 나지 않는다.

### WP-L5. `pass_rate_monitor.json` schema uplift
상태: `완료`

- 추가 필드:
  - `attempt_key`
  - `final_verdict`
  - `patch_strategy`
  - `structural_attempted`

### WP-L6. `stage_attempts` parity uplift
상태: `완료`

- 완료:
  - Stage 2/3/4 공통 `attempt_key`
  - Stage 3 `pass_rate_monitor` writer parity
  - Stage 4 final semantics 반영
- 추가 완료:
  - `candidate_key`
  - `content_hash`
  - `artifact_path`
  - Stage 2/3/4 final sink artifact linkage

### WP-L7. 운영 cross-check 자동화
상태: `완료`

- 구현:
  - `FailureAnalyzer.patch_trace_summary()`
  - `FailureAnalyzer.sink_alignment_summary()`
  - rerun checklist의 cross-sink 확인 절차
- 목적:
  - `attempt_key` 기준으로 `director_selections`, `episode_production.jsonl`, `stage_attempts`, `pass_rate_monitor.json`이 같은 attempt를 설명하는지 자동 점검

## 3. 남은 Work Package

### WP-L4. artifact linkage
우선순위: `중간`
상태: `완료`

- 목표:
  - attempt -> candidate -> artifact를 deterministic join 가능하게 만든다.
- 권장 필드:
  - `candidate_key`
  - `content_hash`
  - `artifact_path`
- 완료 기준:
  - `director_selections` 또는 final sink에서 실제 manuscript/blueprint artifact를 직접 따라갈 수 있다.
- 현재 구현:
  - `modules/core/artifact_logging.py` snapshot writer
  - Stage 2/3/4 final sink linkage 기록
  - Stage 4 lifecycle sink linkage 기록
  - `FailureAnalyzer.sink_alignment_summary()` artifact mismatch/file existence 감사
- 잔여:
  - 비표준/manual context 운영 규칙 명시

## 4. 권장 실행 순서
1. 비표준/manual context `metrics_session_id` 운영 규칙 명문화
2. cross-sink 자동 감사의 운영 스크립트화 또는 CI 연동
3. Stage 2/3 rich lifecycle sink 보강 여부 결정

## 5. 테스트/검증 게이트

### 5.1 필수 테스트
- `pytest -q tests/test_failure_analyzer.py tests/test_pass_with_fix.py tests/test_stage4_interview_round.py tests/test_chief_writer.py tests/test_inplace_reliability.py tests/test_stage3_orchestrator.py tests/test_stage2_finalizer.py tests/test_stage2_preflight_helpers.py tests/test_db_manager.py tests/test_v55_modules.py`

### 5.2 코드 검색 게이트
- `rg -n "verdict IN \\('PASS', 'PASS_WITH_FIX'\\)|PASS_WITH_FIX pass-like|pass-like" modules/core tests docs`
- `rg -n "attempt_key|final_verdict|patch_strategy|structural_attempted|sink_alignment_summary" modules/core tests`

### 5.3 limited rerun hard gate
- `draft_count=4`
- `runtime_audit_summary.tag=stage4_complete`
- `sink_alignment_summary().status == "ok"` 또는 `warn` 항목 전부가 명시적 예외로 문서화되어 있다.
- `sink_alignment_summary().final_verdict_mismatches == []`
- `sink_alignment_summary().final_score_mismatches == []`
- `sink_alignment_summary().candidate_key_mismatches == []`
- `sink_alignment_summary().selection_candidate_key_mismatches == []`
- `sink_alignment_summary().content_hash_mismatches == []`
- `sink_alignment_summary().artifact_path_mismatches == []`
- `sink_alignment_summary().artifact_metadata_missing == []`
- `sink_alignment_summary().artifact_missing_files == []`
- `sink_alignment_summary().legacy_key_attempts == 0` for standard runtime canary
- `patch_trace_summary().avg_unchanged_ratio >= 0.70`
- 금지 fallback reason:
  - `missing_patched_blocks`
  - `no_usable_patched_blocks`
  - `patched_output_too_short`

## 6. 완료 기준
- sink 계약이 문서와 코드에서 일치한다.
- legacy `PASS_WITH_FIX` pass-like consumer가 로깅 계층에 남아 있지 않다.
- Stage 2/3/4 attempt를 공통 key로 추적할 수 있다.
- 운영 문서가 `patch_trace_summary()`와 `sink_alignment_summary()`를 hard gate로 사용한다.
- 미완 범위가 `manual context 운영 규칙`과 `Stage 2/3 rich lifecycle gap`으로 명확히 격리되어 있다.
