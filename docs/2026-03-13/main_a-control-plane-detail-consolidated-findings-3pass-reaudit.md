# main_a Control Plane Detail Consolidated Findings 3PASS Reaudit

> 작성일: 2026-03-13
> 상태: `executed / pass-with-normalization-note`
> 대상 문서: `main_a-control-plane-detail-consolidated-findings.md`
> 조사 모드: `static / read-only / source-report cross-check / targeted code-and-test verification / UTF-8 only`
> 추가 검증:
> - `pytest -q tests/test_runtime_paths.py tests/test_project_support.py tests/test_project_manager_hud_helpers.py tests/test_resume_status.py tests/test_stage4_context.py tests/test_process_runner_stage0_inputs.py tests/test_run_validator.py` -> `112 passed in 2.37s`
> - `pytest -q tests/test_project_service.py tests/test_main_a_rollback.py tests/test_process_runner.py` -> `46 passed in 2.23s`
> - `pytest -q tests/test_stage3_orchestrator.py tests/test_run_stage4_canary.py tests/test_protocols_services.py` -> `78 passed in 2.60s`

## Executive Summary

통합본은 T1~T5 최종 ledger를 `15건`으로 정확히 재구성했고, 상위 위험군도 현재 코드와 표적 테스트에서 다시 확인됐다. boot/project binding, destructive op recovery, desktop/runner contract, Stage 3/4 entry drift는 모두 여전히 살아 있는 control-plane surface다.

이번 재감리에서 blocker로 본 것은 없다. 다만 소스 문서 그대로는 사소한 정규화가 하나 필요했다. `MCP-T2-01`, `MCP-T2-03`의 duplicate status가 오더 enum `none` 대신 자유서술 `none found`로 적혀 있어, 통합본에서는 `none`으로 정규화했다. 또 T2 원문은 다른 터미널과 달리 독립적인 pytest 실행 줄을 남기지 않았지만, 이번 재감리에서 관련 테스트를 직접 다시 돌려 근거를 보강했다.

결론적으로 통합본은 `pass-with-normalization-note` 상태로 SSOT 승격 가능하다. remediation 실행 오더는 이 재감리 문서와 통합본을 함께 기준으로 삼는 것이 맞다.

---

## Pass 1 - 소스 문서 완전성 검증

### P1-1. T1~T5 결과 문서와 PASS 요약은 모두 존재한다

직접 근거:

- T1: `PASS1 4 -> PASS2 제거 2 -> 최종 2`
- T2: `PASS1 4 -> PASS2 제거 1 -> 최종 3`
- T3: `PASS1 5 -> PASS2 제거 2 -> 최종 3`
- T4: `PASS1 6 -> PASS2 제거 3 -> 최종 3`
- T5: `PASS1 6 -> PASS2 제거 2 -> 최종 4`

판정:

- `confirmed`

해석:

- 오더의 `T1~T5 문서 존재`와 `PASS 요약 존재` 조건은 충족된다.
- source file absence나 PASS chain 누락 때문에 통합본이 막히는 구간은 없다.

### P1-2. 통합본 합계 `15건`은 source ledger에서 재구성된다

직접 근거:

- T1: `P1 2`
- T2: `P1 1 / P2 2`
- T3: `P2 2 / P3 1`
- T4: `P1 2 / P2 1`
- T5: `P1 1 / P2 2 / P3 1`

판정:

- `confirmed`

해석:

- 재구성 결과는 `P0 0 / P1 6 / P2 7 / P3 2 / total 15`다.
- 이번 통합 트랙에서는 cross-terminal dedupe로 삭제된 finding이 없다.
- 따라서 통합본의 grand total은 source ledger만으로 재현 가능하다.

### P1-3. source 문서는 사소한 정규화만 필요하다

직접 근거:

- T2의 `MCP-T2-01`, `MCP-T2-03`는 duplicate field에 `none found`를 사용한다.
- 오더가 허용한 duplicate enum은 `none`, `related-but-new-control-plane-surface`, `already-covered-do-not-reopen`이다.
- T2 문서는 required evidence를 적어 두었지만, T1/T3/T4/T5처럼 독립적인 pytest 실행 결과 줄은 남기지 않았다.

판정:

- `confirmed / non-blocking`

해석:

- 통합본에서 `none found -> none` 정규화만 하면 ledger SSOT로 사용하는 데 문제는 없다.
- T2 테스트 실행 줄 부재는 문서성 공백이지만, 이번 재감리의 추가 테스트 실행으로 보완 가능했다.

## Pass 2 - 상위 위험군 재검증

### P2-1. Boot / project binding 클러스터는 현재 코드에서 직접 재확인된다

직접 근거:

- `main_a.py:958-975`는 project `.env`를 먼저 로드한 뒤 `StudioSystem.boot_v20_project()`를 호출한다.
- `modules/core/project_manager.py:50`은 `ProjectContext.__init__`에서 경로 없는 `load_dotenv(override=True)`를 다시 호출한다.
- `main_a.py:235`, `main_a.py:3031`, `modules/core/system.py:37`은 boot control plane과 `ProjectContext`가 상대 `projects/` 경로를 직접 사용함을 보여 준다.
- `modules/core/runtime_paths.py:23`에는 별도의 `resolve_projects_root()` SSOT가 존재한다.
- `main_a.py:1637`, `main_a.py:1691`, `main_a.py:1705`, `main_a.py:1760`은 `_init_v50_modules()`의 legacy JSON fallback이 `_PROJECTS_DIR`를 직접 읽는 지점을 유지한다.
- 추가 검증 테스트: 첫 번째 pytest 묶음 `112 passed`.

판정:

- `confirmed`

해석:

- `MCP-T1-001`, `MCP-T1-002`, `MCP-T2-03`은 모두 현재 코드 기준으로 살아 있다.
- `T1-002`와 `T2-03`은 같은 root-binding 테마지만 서로 다른 control-plane surface라 분리 유지가 맞다.

### P2-2. Stage entry / DI / observability 클러스터도 여전히 유효하다

직접 근거:

- `main_a.py:2502-2554`는 `_get_max_episode_from_manuscripts()`와 `_show_resume_status()`가 서로 다른 manuscript source를 사용함을 보여 준다.
- `modules/core/project_manager.py:644-659`는 `get_latest_episode_number()`가 DB와 draft 파일을 함께 보는 hybrid getter임을 고정한다.
- `modules/core/stage4_post_processor.py:396-406`은 draft 파일 저장 실패를 비차단으로 처리한다.
- `modules/core/stage4_orchestrator.py:1413`은 interactive Stage 4 prompt floor를 `min_val=1`로 둔다.
- `modules/core/stage4_orchestrator.py:616`은 실제 stop condition이 loop 내부의 `next_ep > target_ep`임을 보여 준다.
- `modules/core/stage3_orchestrator.py:553-564`는 Stage 3이 `production_head + 1`을 floor로 삼는 대비 surface를 제공한다.
- `main_a.py:3424-3457`의 manual `Stage4Context(...)`에는 `session_logger=`가 없고, `modules/core/stage4_context.py:178`의 `from_app()`는 이를 포함한다.
- 추가 검증 테스트: `tests/test_stage3_orchestrator.py`, `tests/test_run_stage4_canary.py`, `tests/test_stage4_context.py` 포함 총 `190 passed`.

판정:

- `confirmed`

해석:

- `MCP-T3-01`, `MCP-T3-02`, `MCP-T3-03`, `MCP-T2-02`는 단순 보고서 추정이 아니라 현재 wrapper/context 코드로 재확인된다.
- 현재 테스트들은 대부분 green이지만, hybrid DB/file drift, completed target input, manual context propagation 같은 wrapper-level seam은 여전히 직접 잠그지 못한다.

### P2-3. Destructive op / shutdown 클러스터는 service와 app 경계 모두에서 유지된다

직접 근거:

- `modules/core/services/project_service.py:162`, `:222`, `:304`는 `reset_after(...)`를 성공 판정 전에 호출한다.
- `modules/core/db_manager.py:2283-2333`는 `reset_after()`가 자체 commit 경계를 가진다는 점을 유지한다.
- `main_a.py:3096-3100`, `main_a.py:3134-3138`은 rewind/rollback 성공 후 `foreshadow_tracker.clear()` 후속 처리를 수행한다.
- `modules/core/foreshadow_tracker.py:431`은 `save_to_db()`가 `DELETE FROM foreshadow`로 전체 삭제부터 시작함을 보여 준다.
- `main_a.py:2417`, `main_a.py:2421`은 `save_v20_anchor("bible")`, `save_anchor("genre_info")`가 예외 보호 없이 shutdown close 이전에 실행되는 지점이다.
- 추가 검증 테스트: `tests/test_project_service.py`, `tests/test_main_a_rollback.py`, `tests/test_process_runner.py` 포함 총 `46 passed`.

판정:

- `confirmed`

해석:

- `MCP-T4-001`, `MCP-T4-002`, `MCP-T4-003`은 서로 다른 failure mode를 가진다.
- 현재 테스트는 success path나 cancel gating은 잘 덮지만, `failure after commit`, `foreshadow preservation`, `shutdown anchor failure`는 여전히 direct regression이 비어 있다.

### P2-4. External contract drift와 regression trust gap도 재확인된다

직접 근거:

- `geuldobi-desktop/src/index.html:2781-2797`의 Stage 0 submenu 번호는 `1..6`으로 라벨링돼 있다.
- `modules/api/process_runner.py:599-606`, `:629-636`은 sub_key를 번역 없이 stdin에 주입하고 `5`일 때만 style cache 입력을 추가한다.
- `modules/api/run_validator.py:71-77`은 `7`을 허용하지 않는다.
- `modules/api/process_runner.py:597-599`, `:625-627`은 boot confirm `y`를 무조건 주입한다.
- `modules/protocols/app_services.py`의 `UIServiceProtocol`, `StateServiceProtocol`는 실제 `modules/core/services/ui_service.py`, `modules/core/services/state_service.py` 구현 범위와 의미가 다르다.
- `tests/test_resume_status.py:46-48`, `tests/test_sweep19.py`, `tests/test_frontend_stage0_connectivity.py`는 source-string assertion 의존을 유지한다.
- 추가 검증 테스트: `tests/test_process_runner_stage0_inputs.py`, `tests/test_run_validator.py`, `tests/test_protocols_services.py` 포함 총 `190 passed`.

판정:

- `confirmed`

해석:

- `MCP-T5-001`, `MCP-T5-002`, `MCP-T5-003`, `MCP-T5-004`는 실제 contract drift와 test-trust gap으로 유지된다.
- 현재 테스트가 green이라는 사실이 오히려 `semantic drift를 막지 못하는 녹색 신호`라는 원문 판단을 강화한다.

## Pass 3 - 통합 SSOT 승격 판정

### P3-1. 통합본은 control-plane remediation SSOT로 승격 가능하다

직접 근거:

- source 문서 5개와 통합 ledger가 모두 재구성 가능하다.
- 상위 위험군이 현재 코드와 재감리 test run에서 다시 확인됐다.
- grand total과 severity 합계에 재현 불가 구간이 없다.

판정:

- `pass-with-normalization-note`

해석:

- 이번 트랙은 OPUS 통합본처럼 grand total이 흔들리는 상태가 아니다.
- 사소한 enum 정규화만 반영하면 실행 기준 문서로 써도 된다.

### P3-2. coverage gap은 존재하지만 SSOT 승격 blocker는 아니다

직접 근거:

- 여러 finding이 공통적으로 direct regression 부재를 지적한다.
- 그러나 각 항목은 코드 근거와 existing test gap이 함께 고정돼 있어 "증거 부족"이 아니라 "회귀망 부족" 문제로 분류된다.

판정:

- `confirmed`

해석:

- 다음 단계는 조사 지속이 아니라 remediation와 regression test 추가다.
- 별도 remediation execution SSOT를 만드는 것이 자연스럽다.

## 보정 로그

| 항목 | 상태 | 메모 |
|------|------|------|
| `MCP-T2-01` duplicate status | corrected | source `none found`를 통합본에서 `none`으로 정규화 |
| `MCP-T2-03` duplicate status | corrected | source `none found`를 통합본에서 `none`으로 정규화 |
| T2 pytest 실행 줄 | noted | source 문서에는 독립 실행 결과 줄이 없었고, 재감리에서 관련 suite를 직접 재실행해 보강 |
| cross-terminal dedupe | none | 통합본 `15건`은 삭제 없이 전량 유지 |

## 최종 판정

- 최종 상태: `pass-with-normalization-note`
- 통합본 SSOT 승격: `가능`
- blocker: `없음`
- 후속 권장: `boot/root binding -> destructive ops/recovery -> desktop/runner contract -> stage entry/DI observability` 순으로 remediation execution 문서를 별도 작성
