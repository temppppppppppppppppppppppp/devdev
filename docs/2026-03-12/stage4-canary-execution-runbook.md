# Stage 4 Canary Execution Runbook

작성일: 2026-03-12

목적: Stage 4 limited canary를 반복 가능하게 실행하고, 종료 직후 go/no-go를 같은 기준으로 판정한다.

상위 문서:
- `docs/2026-03-12/stage4-canary-parallel-roadmap.md`
- `docs/2026-03-12/stage4-live-rerun-checklist.md`

## 범위

이 문서는 `1 arc / ep_0001~ep_0004` 기준 Stage 4 canary에만 적용한다.

현재 지원 범위:
- `Stage4-only full rerun`만 지원
- `from_ep > 1` 부분 rerun canary는 아직 지원하지 않음

즉 canary prep은 항상 `from_ep=1`로 본다.
CLI도 `from_ep != 1`이면 실패하도록 잠겨 있다.

## 대상

권장 baseline:
- source project: `00_test_02`
- target project: 새 canary copy (`00_test_07` 이상 권장)

제외:
- `00_test_03` 계열 flash-lite 혼입 baseline

## 표준 명령

### 1. Prepare

```powershell
python scripts/run_stage4_canary.py prepare --source-project 00_test_02 --target-project 00_test_07 --force
```

기대 결과:
- target copy 생성
- blueprints 유지
- manuscripts / Stage 4 stage_attempts / Stage 4 director_selections / drafts / logs / memory 정리
- `projects/00_test_07/logs/canary_prep.json` 생성

### 2. Pre-Run Analyze

```powershell
python scripts/run_stage4_canary.py analyze --project 00_test_07 --target-ep 4
```

기대 결과:
- `hard_gates.status == "fail"`
- 이유:
  - `draft_count=0`
  - `runtime_audit_summary_missing`
  - `pass_rate_monitor_missing`

이 상태가 정상이다. prep 직후에는 fail-closed가 맞다.

### 3. Run

```powershell
python scripts/run_stage4_canary.py run --project 00_test_07 --target-ep 4
```

기대 결과:
- Stage 4가 ep1~ep4를 생산
- 종료 후 `pass_rate_monitor.save()` 수행
- 종료 후 audit flush 수행
- `projects/00_test_07/logs/canary_summary.json` 갱신

### 4. Post-Run Analyze

```powershell
python scripts/run_stage4_canary.py analyze --project 00_test_07 --target-ep 4
```

## One-Shot 명령

```powershell
python scripts/run_stage4_canary.py full --source-project 00_test_02 --target-project 00_test_07 --target-ep 4 --force
```

주의:
- 이 명령은 `prepare -> run -> analyze`를 연속 수행한다.
- 중간 상태를 눈으로 확인하려면 개별 명령을 권장한다.

## Hard Gate

post-run canary는 아래를 만족해야 한다.

### Completion

- `draft_count == 4`
- `runtime_audit_tag == "stage4_complete"`

### Final Sink

- `pass_rate_monitor_exists == true`
- `stage4_attempts >= 4`
- `director_stage4_rows >= 4`

### Cross-Sink

- `runtime_audit_summary.total_events > 0`
- `sink_alignment_summary.final_verdict_mismatches == []`
- `sink_alignment_summary.final_score_mismatches == []`
- `sink_alignment_summary.initial_verdict_mismatches == []`
- `sink_alignment_summary.patch_strategy_mismatches == []`
- `sink_alignment_summary.candidate_key_mismatches == []`
- `sink_alignment_summary.selection_candidate_key_mismatches == []`
- `sink_alignment_summary.content_hash_mismatches == []`
- `sink_alignment_summary.artifact_path_mismatches == []`
- `sink_alignment_summary.artifact_metadata_missing == []`
- `sink_alignment_summary.artifact_missing_files == []`
- `sink_alignment_summary.legacy_key_attempts == 0`
- `sink_alignment_summary.final_sink_missing == {}`
- `sink_alignment_summary.lifecycle_missing_in_final_sinks == {}`

### Structural Inplace

`PASS_WITH_FIX`가 실제로 발생했을 때만 적용:

- `patch_trace_summary.avg_unchanged_ratio >= 0.70`
- 금지 fallback reason:
  - `missing_patched_blocks`
  - `no_usable_patched_blocks`
  - `patched_output_too_short`

`PASS_WITH_FIX`가 발생하지 않았다면:
- `patch_trace_summary` 비어 있어도 된다.
- 이 경우 mainline canary로 분류하고, structural inplace 검증은 별도 PWF-likely canary로 분리한다.

## 판정 규칙

### PASS

- `hard_gates.status == "pass"`

### WARN

- mainline canary 성공이지만 `patch_trace_summary`가 비어 있는 경우

### FAIL

아래 중 하나면 fail:

- `draft_count != 4`
- `runtime_audit_tag != "stage4_complete"`
- `pass_rate_monitor_exists == false`
- `sink_alignment_summary.status != "ok"`
- cross-sink mismatch 하나라도 존재
- final sink missing 하나라도 존재
- lifecycle sink missing 하나라도 존재
- lifecycle가 final sink에 안 닫힘
- artifact linkage/file existence mismatch 존재

## 실행 후 기록 템플릿

```text
project:
source baseline:
target canary:
started_at:
ended_at:
draft_count:
runtime_audit_tag:
stage4_attempts:
director_stage4_rows:
pass_rate_monitor_exists:
patch_trace_summary:
sink_alignment_summary.status:
hard_gates.status:
go/no-go:
notes:
```

## 현재 운영 판단

현재 기준으로 canary 전에 병렬 개발해야 할 큰 공백은 닫혔다.

남은 것은 2개다.

1. mainline canary 1회 실행
2. 필요 시 PWF-likely canary 1회 추가

즉 다음 액션은 개발보다 실행에 가깝다.
