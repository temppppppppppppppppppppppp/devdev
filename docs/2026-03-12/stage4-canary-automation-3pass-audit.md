# Stage 4 Canary Automation 3-Pass Audit

작성일: 2026-03-12

대상:
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`

범위:
- canary 실행 자동화
- Stage4-only prep
- post-run summary / hard gate

비범위:
- 실제 canary 실행
- live rerun

## Pass 1. 계약 점검

초기 findings:

1. `from_ep`가 부분 rerun도 지원하는 것처럼 열려 있었지만, file/memory cleanup은 episode-scoped가 아니었다.
2. auto `hard_gates`가 운영 체크리스트보다 느슨했다.

조치:

- `from_ep != 1`이면 helper와 CLI가 실패하도록 잠갔다.
- `pass_rate_monitor_missing`, `final_sink_missing`, `lifecycle_sink_missing`, `lifecycle_missing_in_final_sinks`, `sink_alignment_summary_empty`, `sink_alignment_status != ok`를 hard error로 승격했다.

판정:
- 계약은 이제 `Stage4-only full rerun canary`로 명확하다.
- 부분 rerun canary는 문서와 코드 모두에서 비지원으로 정리됐다.

## Pass 2. 실행 경로 점검

검토 기준:
- 공식 boot 경로 사용 여부
- Stage 4 진입 경로 일치 여부
- 종료 시 save/flush 보장 여부

확인:

- runner는 `SovereignApp.boot()`을 사용하고 main menu loop만 우회한다.
- Stage 4 진입은 `app._stage_4_v2_chief_writer(limit_mode=False, target_ep=...)`로 고정된다.
- 종료 후 `pass_rate_monitor.save()`와 audit flush를 명시 호출한다.

추가 테스트:
- `tests/test_run_stage4_canary.py`
  - `run_canary()`가 save/flush/analyze를 호출하는지 검증
  - genre anchor 누락 시 즉시 실패하는지 검증

판정:
- 실행 경로는 ad-hoc inline harness보다 안전하다.

## Pass 3. 검증/운영 게이트 점검

검토 기준:
- prep 직후 fail-closed 여부
- runbook과 auto gate 일치 여부
- source/target 불변성

확인:

- `prepare` 후 [00_test_06](C:/Users/User/Desktop/글도비/projects/00_test_06)은 draft 0 / runtime summary missing / pass_rate_monitor missing / sink summary empty 상태로 `hard_gates.status=fail`이 된다.
- source project는 보존되고, target copy에서 blueprints만 유지된다.
- runbook의 hard gate와 auto `hard_gates`가 같은 방향으로 정렬됐다.

검증:

```text
pytest -q tests/test_stage4_canary_tools.py tests/test_run_stage4_canary.py tests/test_failure_analyzer.py tests/test_project_service.py
25 passed in 2.40s
```

실경로 확인:

```text
python scripts/run_stage4_canary.py analyze --project 00_test_06 --target-ep 4
```

결과:
- `hard_gates.status = fail`
- errors:
  - `draft_count_mismatch:0!=4`
  - `pass_rate_monitor_missing`
  - `sink_alignment_summary_empty`

이 상태는 prep 직후 정상이다.

## Residual

남은 리스크는 실행 전 상태에서 2개다.

1. 실제 canary run을 아직 태우지 않았으므로 runtime path의 end-to-end 실증은 남아 있다.
2. `PASS_WITH_FIX`를 실제로 밟는 structural inplace canary는 별도 케이스가 필요할 수 있다.

둘 다 현재 오더 기준으로는 `실행 이후 영역`이다.

## 최종 판정

- 코드 수정: 적절
- 문서 정합성: 적절
- 실행 직전 준비도: 충분
- 현재 확신도: `95%`

근거:
- 계약과 구현이 일치한다.
- helper/runner/test/runbook이 같은 범위를 말한다.
- prep/analyze 실경로 확인까지 끝났다.
- 남은 불확실성은 실제 canary 실행에서만 해소 가능한 부분으로 분리됐다.
