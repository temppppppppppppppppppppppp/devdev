# ROP-T5 Runtime Proof / Canary / Regression Findings

작성일: 2026-03-13
상태: `completed`
담당 범위: `Terminal 5 - runtime proof / canary / regression surface`
조사 모드: `read-only`, `artifact cross-check`, `code-and-test verification`, `UTF-8 only`

## Scope

- required docs
  - `docs/2026-03-13/logging-hardening-moderate-followup-postfix-3pass-closure.md`
  - `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md`
  - `docs/2026-03-13/four-project-1arc-merged-remediation-followup-2pass-audit.md`
  - `docs/2026-03-13/stage4-director-cw-log-informed-remediation-postfix-5pass-closure.md`
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
  - `docs/2026-03-12/stage4-canary-execution-runbook.md`
  - `docs/2026-03-12/stage4-live-rerun-checklist.md`
  - `docs/2026-03-12/stage4-canary-pass-final-report.md`
  - `docs/2026-03-12/quality-warning-remediation-postfix-log-rerudit-report.md`
- code/test surface
  - `modules/core/stage4_canary_tools.py`
  - `scripts/run_stage4_canary.py`
  - `tests/test_run_stage4_canary.py`
  - `tests/test_stage4_canary_tools.py`
  - `tests/test_stage0_pov.py`
  - `tests/test_stage0_work_guard_style_cache.py`
  - `tests/test_project_support.py`
  - `tests/test_db_manager.py`
- runtime artifacts
  - `projects/기록용/00_test_06`
  - `projects/기록용/00_test_07`
  - `projects/기록용/00`
  - `projects/기록용/01`
  - `projects/기록용/03`
  - `projects/기록용/0w`

## Focused Regression

```text
pytest -q tests/test_run_stage4_canary.py tests/test_stage4_canary_tools.py tests/test_stage0_pov.py tests/test_stage0_work_guard_style_cache.py tests/test_project_support.py tests/test_db_manager.py
```

- 결과: `46 passed in 2.92s`

## PASS 1. 후보 수집

| Candidate | Confidence | Tags | 요약 |
|---|---|---|---|
| C1 | HIGH | `runtime-proof`, `sink`, `regression` | current canary gate가 2026-03-13 rationale/provenance sink contract를 직접 증명하는지 |
| C2 | HIGH | `artifact`, `provenance`, `runtime-proof` | archived canary 증거가 현재 워크스페이스 경로에서도 그대로 열리는지 |
| C3 | MED | `stale-artifact`, `provenance` | `00/01/03/0w` Stage 0 POV artifact refresh가 아직 필요한지 |
| C4 | MED | `runtime-proof`, `artifact` | `0w` continuity hardening proof가 fresh rerun 없이도 닫혔는지 |
| C5 | MED | `runtime-proof`, `artifact` | `03` integrity hardening proof가 fresh rerun 없이도 닫혔는지 |
| C6 | LOW | `runtime-proof`, `regression` | canary pre-run analyze가 fail-open으로 풀렸는지 |

## PASS 2. 교차 검증

### retained

- `C1`
  - `modules/core/stage4_canary_tools.py:86`는 canary summary를 `patch_trace_summary`, `sink_alignment_summary`, draft count, runtime summary, Stage 4 row count 위주로 만든다.
  - `modules/core/stage4_canary_tools.py:257`의 hard gate는 mismatch/file linkage를 막지만 `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives` 존재를 직접 gate하지 않는다.
  - `scripts/run_stage4_canary.py:83`는 `run -> analyze` 결과를 곧바로 canary 판정 payload로 사용한다.
  - archived proof `projects/기록용/00_test_07/logs/canary_summary.json:7,30,31,75,78`는 clean pass지만, 같은 project DB를 직접 조회하면 `stage_attempts.selection_reason` 조회가 `no such column: selection_reason`로 실패한다. 즉 canonical canary proof가 최신 rationale sink contract를 증명하지 못한다.
- `C2`
  - 실제 증거는 `projects/기록용/00_test_07` 아래에 남아 있다.
  - 그러나 `projects/기록용/00_test_07/logs/canary_summary.json:3`의 `project_root`는 여전히 `C:\Users\User\Desktop\글도비\projects\00_test_07`이다.
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md:43-45,192,219`와 `docs/2026-03-12/quality-warning-remediation-postfix-log-rerudit-report.md:35-36,102-103`도 동일한 old path를 직접 참조한다.
  - 현재 워크스페이스에서는 `projects\00_test_07`가 존재하지 않고 `projects\기록용\00_test_07`만 존재한다.

### removed / downgraded

- `C3`
  - `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md:46`와 `docs/2026-03-13/four-project-1arc-merged-remediation-followup-2pass-audit.md:49-50`가 이미 `E-1 POV artifact refresh proof`를 runtime-only로 남겨 두고 있다.
  - 실제 artifact도 그 판단과 일치했다. `projects/기록용/00|01|03|0w/stage0_output/style_guide.json`은 모두 `pov="1인칭"`만 있고 `selected_primary_pov`, `effective_primary_pov`, `external_pov_insert_policy`가 비어 있다.
  - `already-covered-do-not-reopen`
- `C4`
  - `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md:62`와 `docs/2026-03-13/four-project-1arc-merged-remediation-followup-2pass-audit.md:50`가 이미 `E-2 0w continuity proof`를 runtime-only로 분리했다.
  - archived `projects/기록용/0w/project_data.db`는 `ep_num=2 attempt1 REJECT -> attempt2 PASS` chain을 그대로 보존한다.
  - `already-covered-do-not-reopen`
- `C5`
  - `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md:78`와 `docs/2026-03-13/four-project-1arc-merged-remediation-followup-2pass-audit.md:48-50`가 이미 `03` fresh rerun proof를 runtime-only로 남겨 뒀다.
  - `projects/기록용/03/logs/runtime_audit_summary.json:8-9`에는 여전히 `data_missing=1`, `integrity_fail=1`이 남아 있다.
  - `already-covered-do-not-reopen`
- `C6`
  - archived prep-only sample `projects/기록용/00_test_06/logs/canary_summary.json:17-24`는 `status=fail`, `pass_rate_monitor_missing`, `sink_alignment_summary_empty`, `runtime_audit_summary_missing`로 fail-closed를 유지한다.
  - fail-open regression 의심은 기각한다.

## PASS 3. 확정 Findings

### [ROP-T5-001] canary green이 current rationale/provenance sink proof를 자동으로 닫지 못한다

- ID: `ROP-T5-001`
- Severity: `P2`
- 현상 요약:
  - 현행 canary canonical proof인 `projects/기록용/00_test_07/logs/canary_summary.json:7,30,31,75,78`은 `draft_count=4`, `stage4_attempts=4`, `director_stage4_rows=4`, `sink_alignment_summary.status="ok"`, `hard_gates.status="pass"`를 보여 준다.
  - 그러나 같은 run의 `projects/기록용/00_test_07/project_data.db`를 직접 점검하면 `stage_attempts`에서 `candidate_key`, `artifact_path`는 존재하지만 `selection_reason` 조회가 `sqlite3.OperationalError: no such column: selection_reason`로 실패한다.
  - 따라서 현재 canary pass는 `lineage/basic sink alignment` proof일 뿐, 2026-03-13 closure가 요구한 `selection_reason / verdict_reason / open_review / fix_scope_reasoning / runtime_advisory / retry_directives` live persistence proof가 아니다.
- 코드 근거:
  - `modules/core/stage4_canary_tools.py:86-151`
  - `modules/core/stage4_canary_tools.py:257-322`
  - `scripts/run_stage4_canary.py:83-114`
  - `docs/2026-03-13/logging-hardening-moderate-followup-postfix-3pass-closure.md:78-79`
  - `docs/2026-03-13/stage4-director-cw-log-informed-remediation-postfix-5pass-closure.md:96,105`
- downstream 영향 경계:
  - canary `pass`만으로는 March 13 이후 Stage 3/4 observability hardening의 operator-facing proof를 닫을 수 없다.
  - 특히 `stage_attempts` DB 단독 포렌식과 `episode_production`/session log 사이의 rationale linkage를 runtime에서 증명했다고 오판할 수 있다.
- 현재 테스트 근거 또는 테스트 부재:
  - focused regression `46 passed`
  - `tests/test_run_stage4_canary.py:7,33`는 `run_canary()`의 save/flush/analyze orchestration만 mocked path로 검증한다.
  - `tests/test_stage4_canary_tools.py:15,105`는 prep reset과 synthetic summary warn gate만 검증한다.
  - `tests/test_db_manager.py:331`는 rationale field persistence를 unit DB에서 검증하지만, canary hard gate와 결합된 end-to-end proof는 없다.
- 기존 문서와의 중복 여부:
  - `related-but-new-evidence-layer-surface`
  - 기존 closure 문서는 runtime-only proof 필요성을 적었지만, 이번 T5는 `existing canary artifact itself`가 최신 sink contract를 증명하지 못한다는 점을 artifact/DB 교차검증으로 확정했다.
- 권장 후속 조치:
  - fresh Stage 4 rerun 1회를 새 canary project로 다시 남기고, `stage_attempts` rationale/provenance 컬럼과 `episode_production` warning split을 함께 캡처한다.
  - 가능하면 canary analyze/hard gate에 `stage_attempts` rationale field presence 검사를 추가하거나, post-canary DB audit를 mandatory companion step으로 고정한다.

### [ROP-T5-002] archived proof reference가 current workspace path를 보존하지 못한다

- ID: `ROP-T5-002`
- Severity: `P3`
- 현상 요약:
  - 현재 실제 proof artifact는 `projects/기록용/00_test_07` 아래에 존재한다.
  - 하지만 `projects/기록용/00_test_07/logs/canary_summary.json:3`은 여전히 old live path인 `C:\Users\User\Desktop\글도비\projects\00_test_07`를 `project_root`로 기록한다.
  - 후속 audit 문서도 `projects/00_test_07/...` 절대 경로 링크를 그대로 사용한다.
  - 현재 워크스페이스 기준 `projects\00_test_07`는 존재하지 않고 `projects\기록용\00_test_07`만 존재하므로, operator는 manual remap 없이는 cited evidence를 바로 열 수 없다.
- 코드 근거:
  - `modules/core/stage4_canary_tools.py:139`
  - `docs/2026-03-12/stage4-canary-pass-final-report.md:8`
  - `docs/2026-03-12/quality-warning-remediation-postfix-log-rerudit-report.md:35-36,94,102-103`
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md:43-45,192,219`
- downstream 영향 경계:
  - operator-facing proof chain이 현재 workspace에서는 broken link가 된다.
  - 증거 자체는 남아 있지만, “어느 artifact를 기준으로 closure를 재판독해야 하는가”가 문서만으로는 즉시 복원되지 않는다.
- 현재 테스트 근거 또는 테스트 부재:
  - `tests/test_run_stage4_canary.py`
  - `tests/test_stage4_canary_tools.py`
  - 현재 canary regression surface에는 archive relocation, archived-proof index, documentation reference freshness를 검증하는 테스트가 없다.
- 기존 문서와의 중복 여부:
  - `none`
- 권장 후속 조치:
  - archived proof를 기준으로 재판독할 문서는 `projects/기록용/...` 경로로 refresh하거나, archive-stable proof index 문서를 추가한다.
  - canary closure 문서에서 절대 live path 대신 archive-safe locator를 함께 남기는 규칙이 필요하다.

## Runtime Proof Ledger

### code-closed

- logging summary line hardening
  - `docs/2026-03-13/logging-hardening-moderate-followup-postfix-3pass-closure.md:78-79`
- Stage 4 rationale/provenance hardening
  - `docs/2026-03-13/stage4-director-cw-log-informed-remediation-postfix-5pass-closure.md:96,105`
- Stage 2 integrity hardening tranche
  - `docs/2026-03-13/four-project-1arc-merged-remediation-followup-2pass-audit.md:14,48-50`

### runtime-open

- fresh Stage 3/4 rerun proving new summary lines and new rationale sink population
- `0w` continuity hardening proof
- `03` integrity debt reduction proof

### stale-artifact

- `projects/기록용/00_test_07` canary DB is usable for pre-March-13 lineage proof, but stale for the newer rationale sink contract
- `projects/기록용/00|01|03|0w/stage0_output/style_guide.json` still reflect old POV artifact contract
- archived proof documents still point to pre-archive `projects/00_test_07` path

### sink-open

- no retained live mismatch was found in archived canary sink alignment itself
- retained blind spot is proof coverage: current canary gate does not assert the newer rationale/provenance fields

## Observations

- `projects/기록용/00_test_06/logs/canary_summary.json:17-24` still demonstrates correct fail-closed behavior before run. T5에서는 canary fail-open regression을 찾지 못했다.
- `PowerShell -> python -` stdin으로 `기록용` path literal을 직접 넘기면 question-mark placeholder로 치환되어 보이는 경우가 있었지만, archived JSON/DB 파일 내용 자체는 UTF-8 정상이다. 이건 file-level mojibake가 아니라 terminal input encoding residue다.

## PASS 요약

- PASS1 후보: `6`
- PASS2 제거/하향: `4`
  - `C3`, `C4`, `C5`: existing SSOT runtime-only ledger로 유지, 재오픈 안 함
  - `C6`: fail-open 의심 기각
- PASS3 확정: `2`
  - `ROP-T5-001`
  - `ROP-T5-002`

최종 판정:

- runtime proof surface에는 새 code defect보다 `proof coverage gap`과 `stale evidence path drift`가 더 크다.
- 이미 닫힌 code tranche를 다시 열 이유는 없다.
- 다음 통합본에서는 `code-closed / runtime-open / stale-artifact / sink-open` ledger를 위 기준으로 재구성하면 된다.
