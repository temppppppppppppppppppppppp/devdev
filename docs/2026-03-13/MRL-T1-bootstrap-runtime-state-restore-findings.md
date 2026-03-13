# [MRL-T1] Boot / Project Switch / Runtime State Restore Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`

---

## 조사 범위

- `main_a.py`
  - `boot()`
  - `_select_project()`
  - boot 이후 runtime object rebind / destructive-op wrapper
- 직접 downstream
  - `modules/core/project_manager.py`
  - `modules/core/project_support.py`
  - `modules/core/services/project_service.py`

## 필수 근거

- `tests/test_runtime_paths.py`
- `tests/test_project_support.py`
- `tests/test_project_service.py`
- `modules/core/project_manager.py`
- 추가 확인
  - `tests/test_main_a_boot_binding.py`
  - `tests/test_main_a_rollback.py`
  - `modules/core/system.py`
  - `modules/domain/agents/base_agent.py`
  - `docs/2026-03-13/MCP-T1-boot-project-binding-findings.md`
  - `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md`
  - `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md`
  - `docs/2026-03-13/MRL-T4-commit-rollback-recovery-contract-findings.md`

## 실행 로그

- `pytest -q tests/test_runtime_paths.py tests/test_project_support.py tests/test_project_service.py tests/test_main_a_boot_binding.py tests/test_main_a_rollback.py`
  - `37 passed in 1.96s`
- ad hoc verification 2건
  - `rg -n "self.current_project =" main_a.py`로 runtime project rebind 지점이 `boot()` 1회뿐인지 확인
  - temp project에서 `author_directives.txt`를 `OLD -> NEW`로 바꾼 뒤 `ProjectContext._load_from_db()`만 호출했을 때 `author_directives_after_load_from_db= OLD`로 남는지 확인

## PASS 기록

- PASS 1
  - 후보 4건 수집
  - boot/project binding 자체와 recovery graph의 책임 경계를 분리했다.
- PASS 2
  - 필수 테스트와 추가 boot/recovery wrapper 테스트를 교차 검증했다.
  - 기존 `MCP-T1`, `MRL-T4`와 대조해 root/env binding 또는 failure-policy 중복을 제거했다.
- PASS 3
  - PASS1 후보 4건 -> PASS2 제거 2건 -> 최종 2건

## Executive Summary

- 현재 runtime lifecycle은 `project selection -> boot rebind`와 `destructive-op -> runtime restore`가 같은 graph를 재구성하지 않는다.
- boot graph는 일부 객체를 `current_project`/`selected_genre` lambda로 동적 참조하고, 다른 객체는 프로젝트/DB/guard/log path를 boot 시점에 직접 캡처한다.
- recovery graph는 `ProjectContext._load_from_db()` 중심의 anchor reload라서 file-backed support contract(`author_directives`, work guard, prompt cache path 의미)는 boot 수준으로 다시 맞추지 못한다.

## PASS 2 제거 항목

| 후보 | 판정 | 이유 |
|----|----|----|
| `_state_tracker_loaded_arcs`가 destructive op 후 리셋되지 않아 다음 Stage 2가 stale tracker를 재사용한다 | 제거 | `main_a.py` wrapper가 `state_tracker = None`으로 비우고, `stage2_orchestrator.py:236-247`가 `ctx.state_tracker is None`이면 강제 재초기화한다. 현재 코드만으로 stale reuse는 확정되지 않았다. |
| boot 인라인 preset restore와 `_restore_preset_registry()` helper 중복이 곧바로 lifecycle defect다 | 제거 | helper 중복 자체는 사실이지만, stale preset 본체는 `MPN-T1-001`, boot/helper 중복 surface는 `MDH-T4-004`가 이미 다뤘다. 이번 T1 문서에서는 재오픈하지 않는다. |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MRL-T1-001 | P1 | retained | `main_a.py::boot`, `main_a.py::_select_project`, `main_a.py::_attach_agents`, `modules/core/system.py::boot_v20_project` | boot graph가 dynamic binding service와 boot-captured project object로 갈라져 restart-less project switch 계약이 없다 |
| MRL-T1-002 | P2 | retained | `modules/core/project_manager.py::_load_directives`, `_load_from_db`; `modules/core/services/project_service.py::_restore_runtime_state`; `main_a.py::boot` | runtime restore는 DB anchor만 재적재하고 file-backed support contract는 재구성하지 않아 boot와 recovery의 project context 의미가 다르다 |

---

## [MRL-T1-001] P1 | boot graph가 dynamic binding service와 boot-captured project object로 갈라져 restart-less project switch 계약이 없다

1. ID
   - `MRL-T1-001`
2. Severity
   - `P1`
3. 현상 요약
   - `boot()`는 project를 고른 뒤 `sys.project`, `current_project`, logger path, metrics session, memory, agents를 한 번에 결착한다.
   - 그런데 app 내부 객체는 같은 방식으로 project를 보지 않는다.
   - `AuditService`, `UIService`, `StateService`, `ProjectService`는 lambda를 통해 현재 `self.current_project`/`self.selected_genre`를 동적으로 읽는다.
   - 반면 `VecMemory`, `SessionLogger` retarget, `StudioLogger` retarget, agent 인스턴스들은 boot 시점의 `self.current_project`와 DB connection을 직접 캡처한다.
   - `_select_project()`는 단지 이름만 반환하고, boot 이후 이 mixed graph를 다시 결착하는 `switch_project()`류 helper는 없다.
4. 코드 근거
   - `main_a.py:295-330`
     - extracted service layer는 `project_fn=lambda: self.current_project`, `genre_fn=lambda: self.selected_genre` 형태로 동적 참조를 쓴다.
   - `main_a.py:1046-1163`
     - `boot()`는 `_reload_project_environment()`, `boot_v20_project()`, `current_project` 대입, logger/metrics retarget, prompt cache reset, guard/HUD/memory init, `_attach_agents()`를 한 번에 수행한다.
   - `main_a.py:1056`
     - `self.current_project = self.sys.project`
   - `main_a.py:259`
     - `self.current_project = None`
   - `rg -n "self.current_project =" main_a.py`
     - 위 두 줄 외 runtime project rebind 지점이 없다.
   - `main_a.py:1059-1073`
     - session/studio logger, metrics collector는 boot 시점 project path에 맞춰 한 번 retarget된다.
   - `main_a.py:1146-1152`
     - `VecMemory`는 boot 시점 `self.current_project.db.conn`과 lock을 직접 캡처한다.
   - `main_a.py:1557-1611`
     - 주요 agent는 모두 `Analyst(self.current_project, ...)`, `Writer(self.current_project, ...)` 형태로 boot 시점 project object를 직접 넘겨받는다.
   - `main_a.py:3134-3153`
     - `_select_project()`는 lexical project name만 반환한다.
   - `modules/core/system.py:26-39`
     - `boot_v20_project()`도 새 `ProjectContext` 생성 외 별도 live rebind ledger를 제공하지 않는다.
5. downstream 영향 경계
   - 현재 shipped flow는 project 선택이 boot 이전 1회라서 우연히 안전하다.
   - 그러나 같은 프로세스에서 project를 다시 고르거나 future UI/runner가 restart-less switch를 붙이면,
     - service/helper는 새 `current_project`를 보고
     - agent/memory/logger는 이전 project를 계속 보게 된다.
   - 그 결과 로그/metrics는 새 프로젝트로 떨어지는데 agent write/read는 옛 project DB/paths를 쓰는 split-brain이 생길 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_runtime_paths.py`, `tests/test_main_a_boot_binding.py`는 explicit project root와 초기 boot binding만 검증한다.
   - `tests/test_project_service.py`, `tests/test_main_a_rollback.py`는 destructive-op 이후 cache invalidation만 검증하며 project rebinding 자체는 보지 않는다.
   - same-process `project A -> project B` 전환 후 `service.current_project`, `agent.context`, `memory.conn`, logger path가 동시에 바뀌는지 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `duplicate status`: `related-but-new-runtime-lifecycle-surface`
   - `MCP-T1-002`는 project root SSOT 우회 문제를 다뤘다.
   - 이번 finding은 root 선택이 아니라, 일단 project가 정해진 뒤 runtime object graph가 half-dynamic / half-static으로 묶여 있어 restart-less switch semantics가 성립하지 않는다는 lifecycle surface다.
8. 권장 후속 조치
   - project switch를 지원하지 않을 거라면 `restart-only contract`를 명시적으로 잠그고, same-process switch 진입점을 만들지 않는다.
   - 지원할 거라면 `switch_project()` 같은 단일 helper에서 아래를 원자적으로 재결착해야 한다.
     - `sys.project`, `current_project`
     - logger / metrics / prompt cache
     - memory / agent instances
     - guard / HUD / preset registry / runtime trackers
   - 회귀 테스트를 추가한다.
     - `project A boot -> project B switch` 후 `ProjectService.project_fn()`, `writer.context`, `memory.conn`, session log dir가 모두 B를 가리키는지 확인

---

## [MRL-T1-002] P2 | runtime restore는 DB anchor만 재적재하고 file-backed support contract는 재구성하지 않아 boot와 recovery의 project context 의미가 다르다

1. ID
   - `MRL-T1-002`
2. Severity
   - `P2`
3. 현상 요약
   - `ProjectContext`는 init에서 두 종류의 state를 만든다.
     - DB anchor 기반 state: `master_bible`, `volumes`, `arcs`, `_preset_state_raw`, `karma_status`, `selected_tone`
     - file/support 기반 state: `author_directives`, 그리고 boot가 추가 주입하는 `genre`, `guard`, work-guard wrapping, prompt cache 의미
   - 하지만 destructive-op recovery는 `ProjectService._restore_runtime_state()` 안에서 `project._load_from_db()`만 다시 호출한다.
   - 따라서 recovery 후 project object는 DB anchor는 새 상태를 보지만, `author_directives` 같은 file-backed support contract와 boot 시점 guard/prompt binding은 그대로 남는다.
   - ad hoc 재현에서도 `author_directives.txt`를 `OLD -> NEW`로 바꾼 뒤 `_load_from_db()`만 호출하면 `author_directives_after_load_from_db= OLD`로 남았다.
4. 코드 근거
   - `modules/core/project_manager.py:85-86`
     - `ProjectContext.__init__`는 `_load_from_db()`와 `_load_directives()`를 둘 다 호출한다.
   - `modules/core/project_manager.py:114-120`
     - `_load_directives()`는 `config/author_directives.txt`를 읽어 `self.author_directives`를 채운다.
   - `modules/core/project_manager.py:121-173`
     - `_load_from_db()`는 DB anchors와 preset raw, tone만 복원한다. directives reload는 없다.
   - `modules/core/services/project_service.py:63-99`
     - `_restore_runtime_state()`는 `project._load_from_db()`와 tracker rollback만 수행한다.
   - `main_a.py:1075-1078`
     - boot만 `PromptLoader().invalidate_cache()`를 수행한다.
   - `main_a.py:1091-1138`
     - boot만 `current_project.genre`, `sys.guard`, `current_project.guard`, work-guard wrapping을 결착한다.
   - `modules/domain/agents/base_agent.py:559-564`
   - `modules/domain/agents/base_agent.py:1895-1900`
     - agent prompt wrapper는 `context.author_directives`를 live prompt에 직접 주입한다.
   - ad hoc verification
     - temp project에서 `author_directives.txt`를 다시 쓴 뒤 `ctx._load_from_db()`만 호출했을 때 `ctx.author_directives`는 갱신되지 않았다.
5. downstream 영향 경계
   - recovery 이후 same-process에서 author directives나 work-guard support asset이 바뀌어도 다음 stage prompt/validation은 boot 당시 contract를 계속 쓴다.
   - 즉 boot는 "full project contract"를 만들지만, recovery는 "anchor-only contract"만 만든다.
   - next-stage operator는 rollback/reset/wipe 후 같은 project를 계속 쓴다고 생각해도, support/config 변경은 full reboot 전까지 반영되지 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_project_support.py`는 support asset 해석 자체만 검증한다.
   - `tests/test_runtime_paths.py`는 `ProjectContext` 초기 생성 root/env semantics만 본다.
   - `tests/test_project_service.py`와 `tests/test_main_a_rollback.py`는 DB/file/vector cleanup 및 cache invalidation만 보고, recovery 후 `author_directives`, guard/work-guard, prompt loader state refresh 여부는 보지 않는다.
   - recovery가 boot와 같은 support contract를 다시 만든다는 회귀 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `duplicate status`: `none`
   - `MPN-T1-001`은 preset registry stale 문제를 다뤘고,
   - `MRL-T4-*`는 recovery failure policy를 다뤘다.
   - 이번 finding은 failure 여부와 무관하게, success path recovery가 boot 수준의 project support contract를 재구성하지 못한다는 T1 lifecycle surface다.
8. 권장 후속 조치
   - recovery 경로를 `anchor-only refresh`와 `full project contract refresh`로 명시적으로 분리한다.
   - destructive-op success 후에도 필요한 경우 아래를 선택적으로 다시 맞춘다.
     - `current_project._load_directives()`
     - project-specific prompt cache invalidation
     - guard/work-guard re-evaluation
   - 회귀 테스트를 추가한다.
     - `author_directives.txt` 변경 후 `_restore_runtime_state()` 또는 equivalent recovery path에서 prompt가 새 directives를 반영하는지 확인
     - `work_guard.yaml` 변경 후 next-stage validation이 새 guard contract를 보는지 확인

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| same-process project switch lifecycle | 테스트 부재 | `boot(A) -> switch(B)`에서 service/agent/memory/logger가 모두 같은 B를 보는지 확인 |
| recovery 후 support contract refresh | 테스트 부재 | `author_directives`, `work_guard`, PromptLoader cache가 rollback/reset/wipe 후 어떻게 갱신되는지 검증 |
| restart-only contract 명시 여부 | open | menu/API/desktop layer가 project switch를 반드시 process restart로 제한하는지 확인 |

## 마감 체크

- boot graph vs project switch graph 비교: 1건 확정
- normal boot vs runtime restore 의미 비교: 1건 확정
- `current_project`, `selected_genre`, logger, services partial update 여부 점검: 완료
- 기존 control-plane / destructive-op / persistence 문서 중복 제거: 완료

## 최종 판정

- 최종 retained finding: `2건`
  - `P0`: 0건
  - `P1`: 1건
  - `P2`: 1건
  - `P3`: 0건
- PASS1 후보 4건 -> PASS2 제거 2건 -> PASS3 확정 2건
- 본 문서는 `template / not executed`가 아니라 `PASS3 completed T1 finding set`이다.
