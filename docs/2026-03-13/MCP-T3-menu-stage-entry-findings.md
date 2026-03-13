# [MCP-T3] Menu / Stage Entry Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 finalized`
> 조사 모드: `static / read-only / code-and-test verification`
> 기준 오더: `main_a-control-plane-detail-full-survey-audit-order.md`
> 실행 검증: `pytest -q tests/test_resume_status.py tests/test_stage_transition.py tests/test_stage3_orchestrator.py tests/test_run_stage4_canary.py` = `74 passed`, `pytest -q tests/test_stage4_context.py` = `31 passed`

---

## 조사 범위

- `main_a.py`: `_run_main_process()`, `_show_resume_status()`, `_stage_2_arcs()`, `_stage_3_batch_blueprinting()`, `_stage_4_v2_chief_writer()`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- 교차 검증 보강:
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/project_manager.py`

## 필수 근거

- `tests/test_resume_status.py`
- `tests/test_stage_transition.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_run_stage4_canary.py`
- 추가 교차 근거:
  - `tests/test_stage4_context.py`
  - `docs/2026-03-13/T3-stage3-4-pipeline-audit-report.md`
  - `docs/2026-03-13/D-T3-detail-tests-audit.md`

## PASS 기록

### PASS 1 - 초벌 스캔

- `main_a.py` T3 진입점과 `stage2/3/4_context.py`, `stage3/4_orchestrator.py`, `stage4_post_processor.py`를 전량 대조했다.
- 후보 5건을 뽑았다.
  - 후보 A: 메인 메뉴 번호/라벨/실제 분기 드리프트
  - 후보 B: resume 표기와 Stage 2/3 manuscript head 기준 드리프트
  - 후보 C: Stage 4 `limit_mode=True` 입력 범위 드리프트
  - 후보 D: Stage 4 manual context 주입이 factory 계약을 일부 누락
  - 후보 E: wrapper-level 회귀 부재

### PASS 2 - 교차 검증

- 후보 A는 제거했다.
  - `_run_main_process()`의 `3 -> _stage_3_batch_blueprinting()`, `4 -> _stage_4_v2_chief_writer(limit_mode=True)` 매핑은 정적으로 일치했다.
- 후보 E는 coverage gap으로 하향했다.
  - 현재 테스트는 wrapper-level 실행 대신 source-string/직접 orchestrator 검증이 중심이다.
- 후보 B/C/D는 코드 근거와 테스트 부재가 함께 고정되어 retained finding으로 유지했다.
- 기존 문서 중복 여부를 대조했다.
  - `T3-stage3-4-pipeline-audit-report.md`의 Stage 3/4 내부 알고리즘 finding은 재오픈하지 않았다.
  - `one-stop` 문서의 explicit `target_ep` 경로는 유지하되, 이번 finding은 `main_a.py`의 interactive wrapper 경계만 새로 채택했다.

### PASS 3 - 최종 확정

- PASS1 후보 `5건`
- PASS2 제거 `2건`
- 최종 확정 `3건`

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 | duplicate status |
|----|-----|------|-----------|------|------------------|
| `MCP-T3-01` | `P2` | confirmed | `main_a.py`, `stage3_orchestrator.py`, `project_manager.py`, `stage4_post_processor.py` | resume 배너와 Stage 2/3 manuscript head 기준이 서로 달라 non-blocking file save 실패 뒤에 drift가 난다 | `none` |
| `MCP-T3-02` | `P2` | confirmed | `main_a.py`, `stage4_orchestrator.py` | 메뉴 `4번` Stage 4는 이미 완료된 회차를 target으로 입력해도 사전 차단하지 못하고 늦게 no-op 처리한다 | `related-but-new-control-plane-surface` |
| `MCP-T3-03` | `P3` | confirmed | `main_a.py`, `stage4_context.py`, `stage4_interview_round.py`, `stage4_post_processor.py` | `main_a.py`의 manual Stage 4 context 주입이 `session_logger`를 누락해 Stage 4 session logging이 꺼진다 | `related-but-new-control-plane-surface` |

## Findings

### [MCP-T3-01] P2 | resume 표기와 Stage 2/3 manuscript head 계산이 같은 소스를 보지 않는다

- ID: `MCP-T3-01`
- Severity: `P2`
- 현상 요약:
  - `main_a.py`의 resume 배너는 `current_project.get_latest_episode_number()`를 써서 manuscript progress를 표시한다.
  - 반면 Stage 2/3 진입은 `_get_max_episode_from_manuscripts()`를 통해 `drafts/*.txt`만 스캔한다.
  - Stage 4 post-process는 DB 커밋 뒤 draft 파일 저장 실패를 `비차단`으로 처리하므로, DB row만 있고 draft 파일은 없는 reachable state가 생긴다.
  - 그 상태에서 메뉴 배너와 Stage 2/3의 실제 head 계산이 갈라진다.
- 코드 근거:
  - `main_a.py:2502-2521` `_get_max_episode_from_manuscripts()`는 draft 파일만 읽는다.
  - `main_a.py:2531-2554` `_show_resume_status()`는 `current_project.get_latest_episode_number()` 기반으로 manuscript head를 표시한다.
  - `modules/core/project_manager.py:644-659` `get_latest_episode_number()`는 DB와 draft 파일 중 큰 값을 택하는 hybrid getter다.
  - `modules/core/stage3_orchestrator.py:525-533` Stage 3 `production_head`는 `get_latest_blueprint_number()`와 file-only manuscript head의 `max(...)`로 결정된다.
  - `modules/core/stage4_post_processor.py:396-406` draft 파일 저장 실패는 경고만 남기고 진행한다.
- downstream 영향 경계:
  - `_show_resume_status()`가 보여주는 manuscript progress
  - `_stage_2_arcs()`의 manuscript-detected warning 경계
  - `_stage_3_batch_blueprinting()`의 시작 floor 및 target prompt 의미
  - 운영자는 "원고가 여기까지 있다"는 배너를 보고도 Stage 2/3가 다른 기준으로 움직이는 상황을 맞게 된다.
- 현재 테스트 근거 또는 테스트 부재:
  - 실행 검증한 `tests/test_resume_status.py`는 정상 로그 문구와 `_show_resume_status()` 호출 존재만 본다.
  - `tests/test_stage3_orchestrator.py`는 `_get_max_episode_from_manuscripts`를 `0`으로 stub 하며 hybrid/file drift를 전혀 만들지 않는다.
  - `tests/test_stage_transition.py`는 state tracker sync만 재현한다.
  - draft 파일 저장 실패 후 resume/stage-entry 의미가 갈라지는 focused regression은 없다.
- 기존 문서와의 중복 여부:
  - `duplicate status: none`
  - 기존 Stage 3/4 내부 감사는 blueprint/manuscript 알고리즘과 테스트 구조를 다뤘고, 이번 항목처럼 `main_a.py` resume banner와 entry floor의 source mismatch는 직접 채택하지 않았다.
- 권장 후속 조치:
  - manuscript head의 SSOT를 하나로 고정한다.
  - 가장 단순한 방향은 Stage 2/3도 `current_project.get_latest_episode_number() - 1`을 쓰게 맞추는 것이다.
  - 최소 회귀로 `DB manuscript 존재 + draft file 누락` 케이스를 추가해 resume banner와 Stage 2/3 entry floor가 같은 값을 보게 잠가야 한다.

### [MCP-T3-02] P2 | 메뉴 `4번` Stage 4 interactive target 입력이 현재 생산 head를 반영하지 않는다

- ID: `MCP-T3-02`
- Severity: `P2`
- 현상 요약:
  - 메인 메뉴 `4번`은 항상 `_stage_4_v2_chief_writer(limit_mode=True)`로 들어간다.
  - 그런데 Stage 4 session prepare는 `limit_mode=True`일 때 `min_val=1`로 target episode를 받는다.
  - 이미 `n`화까지 원고가 있는 프로젝트에서도 `1..n` 같은 완료 구간을 입력할 수 있고, 이 값은 즉시 reject되지 않는다.
  - 실제 reject는 `_run_interview_loop()` 내부에서 `next_ep > target_ep` 조건으로 뒤늦게 no-op 종료할 때 발생한다.
- 코드 근거:
  - `main_a.py:2170` 메뉴 `4`는 `_stage_4_v2_chief_writer(limit_mode=True)`를 호출한다.
  - `modules/core/stage4_orchestrator.py:1400-1414` interactive Stage 4 prompt는 `min_val=1`, `max_val=total_planned_ep`로 고정돼 있다.
  - `modules/core/stage4_orchestrator.py:613-617` 실제 stop condition은 loop 내부의 `if target_ep and next_ep > target_ep`다.
  - 대조 기준으로 `modules/core/stage3_orchestrator.py:548-555` Stage 3는 `min_val=production_head + 1`로 현재 head를 반영한다.
- downstream 영향 경계:
  - `main_a.py` 메뉴 기반 수동 Stage 4 진입
  - 잘못된 target 입력이 "실패"가 아니라 "이미 목표 도달" no-op로 보이므로 운영자가 실제 실행 여부를 오해할 수 있다.
  - 향후 interactive `limit_mode=True` 경로를 재사용하는 wrapper가 생기면 같은 drift를 상속한다.
- 현재 테스트 근거 또는 테스트 부재:
  - 실행 검증한 `tests/test_run_stage4_canary.py`는 `limit_mode=False, target_ep=...` explicit target 경로만 검증한다.
  - `tests/test_resume_status.py`는 Stage 4 entry에 `_show_resume_status()`가 있다는 source-string만 본다.
  - `tests/test_stage4_orchestrator.py`에는 `limit_mode=True` prompt floor나 "이미 완료된 target 입력"을 검증하는 케이스가 없다.
- 기존 문서와의 중복 여부:
  - `duplicate status: related-but-new-control-plane-surface`
  - `one-stop-frontier-lag` 및 `one-stop-lookahead` 문서는 explicit `target_ep` wrapper 경로를 닫았고, 이번 finding은 그 밖의 main menu interactive path를 대상으로 한다.
- 권장 후속 조치:
  - interactive Stage 4 prompt에 `current_written = current_project.get_latest_episode_number() - 1`를 반영한다.
  - prompt 자체도 `현재 {current_written}화 / 최대 {total_planned_ep}화` 형태로 바꾸고, `min_val=current_written + 1`로 잠가야 한다.
  - 이미 완료된 범위라면 style guide 로드 전에 early-return하는 focused regression을 추가한다.

### [MCP-T3-03] P3 | `main_a.py`의 Stage 4 manual context 주입이 `session_logger`를 누락한다

- ID: `MCP-T3-03`
- Severity: `P3`
- 현상 요약:
  - `main_a.py`는 boot 시 `_session_logger`를 만들고 프로젝트별 log dir도 설정한다.
  - 그러나 `_stage_4_v2_chief_writer()`는 `Stage4Context.from_app(self)`를 쓰지 않고 `Stage4Context(...)`를 수동 조립한다.
  - 이 수동 조립에서 `session_logger` 인자가 빠져 있다.
  - Stage 4 interview round와 post-processor는 `ctx.session_logger`가 있을 때만 decision/state-change row를 남기므로, menu/canary Stage 4 진입에서는 해당 sink가 조용히 꺼진다.
- 코드 근거:
  - `main_a.py:266-275` boot 시 `_session_logger`를 생성하고 BaseAgent global에도 연결한다.
  - `main_a.py:980` 프로젝트 선택 뒤 `_session_logger.set_log_dir(...)`를 호출한다.
  - `main_a.py:3432-3457` manual `Stage4Context(...)` 구성에는 `session_logger=`가 없다.
  - `modules/core/stage4_context.py:160-178` factory path `Stage4Context.from_app()`는 `session_logger=getattr(app, "_session_logger", None)`를 포함한다.
  - `modules/core/stage4_interview_round.py:1766-1782`와 `modules/core/stage4_post_processor.py:1181-1218`는 `ctx.session_logger`를 읽어 Stage 4 decision/state-change를 기록한다.
- downstream 영향 경계:
  - `main_a.py` 메뉴 경유 Stage 4 실행
  - `scripts/run_stage4_canary.py`가 호출하는 `app._stage_4_v2_chief_writer(...)` 경로
  - `session/decisions.jsonl` 계열의 Stage 4 observability
  - 데이터 생산 자체는 계속되지만, logging-hardening이 기대한 Stage 4 session trace가 control-plane 경계에서 누락된다.
- 현재 테스트 근거 또는 테스트 부재:
  - 실행 검증한 `tests/test_stage4_context.py`는 `Stage4Context.from_app()`의 pass-rate/callback/conditional-module 추출을 통과시킨다.
  - 그러나 `main_a.SovereignApp._stage_4_v2_chief_writer()`가 manual context를 만들 때 `session_logger`를 전파하는지 보는 테스트는 없다.
  - 실행 검증한 `74 passed` T3 필수 회귀군도 이 wrapper-level drift를 덮지 못한다.
- 기존 문서와의 중복 여부:
  - `duplicate status: related-but-new-control-plane-surface`
  - 기존 logging-hardening 문서는 `session_logger` sink 자체와 attempt-key 전파를 다뤘고, 이번 항목은 그 sink가 `main_a.py` wrapper에서 빠지는 control-plane 누락이다.
- 권장 후속 조치:
  - Stage 4 wrapper는 `Stage4Context.from_app(self)`를 기본으로 쓰고, lazy-init된 `state_tracker/world_state/fact_ledger`와 `conditional_modules`만 보정하는 방식으로 바꾼다.
  - 최소 수정으로는 manual constructor에 `session_logger=getattr(self, "_session_logger", None)`를 추가한다.
  - `main_a` wrapper를 직접 호출해 `ctx.session_logger`가 살아 있는지 검증하는 regression을 추가한다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `_run_main_process()` 메뉴 dispatch 자체 | 직접 회귀 없음 | 실제 menu choice `3/4/5/44/77/88/99` 분기 호출을 검증하는 wrapper-level test |
| Stage 4 `limit_mode=True` 입력 경계 | 부재 | `현재 원고가 있는 상태에서 target_ep < next_ep` 입력 시 prompt floor/early-return을 확인하는 test |
| resume banner vs Stage 2/3 manuscript head source 정합성 | 부재 | `DB manuscript 있음 + draft file 없음` 상태에서 `_show_resume_status()`와 Stage 2/3 entry floor를 함께 검증하는 test |
| Stage 4 manual context propagation | 부재 | `main_a.SovereignApp._stage_4_v2_chief_writer()` 호출 후 `ctx.session_logger`와 callback 세트가 유지되는지 확인하는 test |

## 마감 체크

- 메뉴 번호/분기 정합성 검증: 완료
- resume 상태 계산 검증: 완료
- `limit_mode`, `target_ep` contract 검증: 완료
- thin delegate correctness 검증: 완료
- PASS1 후보 `5건 -> PASS2 제거 2건 -> 최종 3건`: 완료
