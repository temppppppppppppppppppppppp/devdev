# MDH-T4: Bootstrap / History / Cache Helper Liveness Findings

> 작성일: 2026-03-13
> 작성자: `codex`
> 터미널: `T4`
> 트랙: `main_a.py` dormant helper / live consumer inventory audit
> 상태: `PASS 3 재감리 완료`
> 메모: 기존 OPUS 초안을 신뢰하지 않고, 코드/테스트/기존 문서/추가 probe를 다시 대조해 전면 재작성했다.

---

## 0. 조사 범위 재정의

### T4 범위 helper 최종 판정

| Helper | 정의 위치 | 실제 live consumer | 최종 상태 |
|--------|----------|--------------------|-----------|
| `_ignite_quad_cache_system()` | `main_a.py:1193-1336` | 없음 | **dead** |
| `_is_cache_alive()` | `main_a.py:1338-1346` | `_ignite_quad_cache_system()` 내부 3곳뿐 | **dead-chain** |
| `_load_v50_history()` | `main_a.py:2128-2141` | `_init_v50_modules()` → `_attach_agents()` → boot chain | **dormant** |
| `_restore_preset_registry()` | `main_a.py:379-389` | destructive op 복구 callback (`ProjectService`) | **bypassed-live** |
| `_init_diversity_engine()` | `main_a.py:953-1002` | caller 없음, 단 `Stage4` optional slot consumer는 존재 | **dead helper / cold live slot** |

### PASS2 제거된 비교 대상

| Helper | 판정 | 이유 |
|--------|------|------|
| `_reload_project_environment()` | 제거 | `boot()`에서 직접 1회 호출되고 (`main_a.py:1051-1052`), body도 실제 `.env` 재로딩과 API client 재바인딩을 수행한다. dormant/bypass/dead signal이 없어 finding으로 유지하지 않았다. |

### 참고용 live bootstrap helper

| Helper | 정의 위치 | 상태 |
|--------|----------|------|
| `boot()` | `main_a.py:1040+` | live entrypoint |
| `_reload_project_environment()` | `main_a.py:1018-1038` | live |
| `_attach_agents()` | `main_a.py:1966-2126` | live |
| `_init_core_agents()` | `main_a.py:1513+` | live |
| `_init_v50_modules()` | `main_a.py:1637-1964` | live |

---

## 1. 필수 근거 및 추가 검증

### 오더상 필수 근거

- `tests/test_stage_transition.py`
- `tests/test_project_service.py`
- `modules/core/services/project_service.py`
- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`

### 이번 재감리에서 추가로 본 근거

- `main_a.py`
- `tests/test_main_a_rollback.py`
- `tests/integration/test_patch_wiring.py`
- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `tests/test_bootstrap_status.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_orchestrator.py`
- `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`
- `docs/2026-03-13/MLW-T5-test-realism-regression-findings.md`
- `docs/2026-02-28/TF-31-style-pipeline-audit.md`

### PASS2 실행 검증

- `pytest tests/test_project_service.py tests/test_stage_transition.py -q` → `20 passed`
- `pytest tests/test_main_a_rollback.py tests/integration/test_patch_wiring.py -q` → `22 passed`
- `pytest tests/property/test_db_rollback_props.py tests/chaos/test_partial_commit.py -q` → `16 passed`
- ad hoc probe 1:
  - `_preset_state_raw=None`, 기존 `preset_registry='OLD'` 상태에서 `SovereignApp._restore_preset_registry(app)` 호출 결과 `preset_registry`가 그대로 `OLD`로 남았다.
- ad hoc probe 2:
  - `_preset_state_raw`에 실제 payload를 넣으면 `SovereignApp._restore_preset_registry(app)`가 `PresetRegistry` 인스턴스를 재구성했다.

---

## 2. PASS 기록

- PASS 1: 후보 6건 수집
  - `_ignite_quad_cache_system`
  - `_is_cache_alive`
  - `_load_v50_history`
  - `_restore_preset_registry`
  - `_init_diversity_engine`
  - `_reload_project_environment`
- PASS 2: 후보 1건 제거, 근거 교정 3건 수행
  - 기존 초안의 `StateService(preset_registry_restorer=...)` 표기는 오기였다. 실제 등록 대상은 `ProjectService` (`main_a.py:319-330`)다.
  - 라인 번호를 현재 트리 기준으로 전부 갱신했다.
  - `_init_diversity_engine()`는 “downstream consumer 불명”이 아니라, `Stage4Context`/`Stage4Orchestrator` 쪽 optional consumer가 살아 있는 cold-slot 문제로 재분류했다.
- PASS 3: 최종 5건 확정

### PASS2 제거 항목

| 후보 | 판정 | 이유 |
|------|------|------|
| `_reload_project_environment()` | 제거 | direct boot caller가 있고, project-local `.env`와 API client 재구성을 실제 수행한다. T4의 dormant/bypassed/dead inventory 대상이 아님. |

---

## 3. Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MDH-T4-001` | `P3` | retained | `main_a.py::_ignite_quad_cache_system` | V31 cache bootstrap helper는 현재 repo에서 live caller가 0건이다 |
| `MDH-T4-002` | `P3` | retained | `main_a.py::_is_cache_alive` | `_ignite_quad_cache_system` 내부에서만 호출되는 dead-chain helper다 |
| `MDH-T4-003` | `P2` | retained | `main_a.py::_load_v50_history` | boot chain이 실제로 도달하지만 body는 guard + `pass`뿐인 dormant stub이다 |
| `MDH-T4-004` | `P2` | retained | `main_a.py::_restore_preset_registry`, `modules/core/services/project_service.py` | destructive op 복구 callback으로는 live지만 boot에서는 동일 로직이 인라인으로 우회된다 |
| `MDH-T4-005` | `P2` | retained | `main_a.py::_init_diversity_engine`, `modules/core/stage4_context.py`, `modules/core/stage4_orchestrator.py` | helper caller는 0건인데 Stage4 optional consumer slot은 살아 있어 `diversity_engine` 공급 경로가 영구적으로 차갑다 |

---

## 4. 확정 Findings

### [MDH-T4-001] P3 | `_ignite_quad_cache_system()`은 V31 legacy dead helper다

1. ID
   - `MDH-T4-001`
2. Severity
   - `P3`
3. 현상 요약
   - `_ignite_quad_cache_system()`은 Writer/Analyst/Weaver 3개 에이전트용 cache metadata를 만들고 `sys_caches` anchor에 저장하는 V31 helper다.
   - repo 전역 재검색 결과, 현재 실행 트리에서 이 helper를 호출하는 production/test caller가 없다.
4. 코드 근거
   - 정의: `main_a.py:1193-1336`
   - repo 전역 검색 결과: `_ignite_quad_cache_system(`은 정의 1건만 잡히고, 나머지는 문서 참조다.
   - 현재 cache 인프라는 별도 agent-local 경로로 존재한다: `modules/domain/agents/base_agent.py:1770-1908`, `modules/domain/agents/writer.py:42,230`, `modules/domain/agents/analyst.py:175,881`, `modules/domain/agents/weaver.py:21,64`.
   - `tests/test_bootstrap_status.py:7-38`는 `_attach_agents()` bootstrap status를 검증하지만, 여기서도 `_ignite_quad_cache_system()`은 등장하지 않는다.
5. downstream 영향 경계
   - boot, project switch, rollback/rewind/wipe 어디에서도 이 helper를 통해 cache를 주입하지 않는다.
   - 따라서 이 helper의 persistence semantics는 별도 shared-helper 문서에서 중요하더라도, liveness 관점에서는 dead legacy path다.
6. 현재 테스트 근거 또는 테스트 부재
   - 이번에 실행한 58개 관련 테스트(`20 + 22 + 16`) 중 direct caller는 없다.
   - `_ignite_quad_cache_system()` 자체를 직접 호출하거나 `sys_caches` 재사용 path를 boot chain에서 잠그는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `already-covered-do-not-reopen`
   - `docs/2026-02-28/TF-31-style-pipeline-audit.md:134`가 이미 dead code로 지적했고, `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`도 coverage gap으로 남겼다.
   - 본 문서에서는 live consumer inventory ledger에 dead 상태를 잠그는 수준으로만 유지한다.
8. 권장 후속 조치
   - 제거 시 `_is_cache_alive()`와 함께 정리한다.
   - 유지한다면 `LEGACY / DEAD / V31` 표기를 명시해 현재 bootstrap path와 구분한다.

---

### [MDH-T4-002] P3 | `_is_cache_alive()`는 dead helper의 내부 callee일 뿐이다

1. ID
   - `MDH-T4-002`
2. Severity
   - `P3`
3. 현상 요약
   - `_is_cache_alive()`는 standalone health-check처럼 보이지만, 실제 caller는 `_ignite_quad_cache_system()` 내부 3곳뿐이다.
   - parent helper가 dead이므로 이 helper도 독립 live consumer를 갖지 못한다.
4. 코드 근거
   - 정의: `main_a.py:1338-1346`
   - caller: `main_a.py:1234`, `main_a.py:1260`, `main_a.py:1283`
   - 외부 caller는 repo 전역 검색에서 확인되지 않았다.
5. downstream 영향 경계
   - 이 helper를 제거해도 현재 runtime contract에는 영향이 없다.
   - `_ignite_quad_cache_system()`를 남기지 않는 한 health-check helper로서의 존재 이유가 없다.
6. 현재 테스트 근거 또는 테스트 부재
   - direct unit test 없음.
   - `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`도 `_is_cache_alive()`를 direct finding으로 채택하지 못하고 coverage gap으로만 남겼다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - 기존 문서는 broad `except Exception` 의미만 봤고, 이번 문서는 “독립 consumer가 전혀 없는 dead-chain helper”라는 liveness 분류를 확정한다.
8. 권장 후속 조치
   - `_ignite_quad_cache_system()`와 함께 제거하거나, parent helper가 부활하지 않는 한 신규 사용처를 만들지 않는다.

---

### [MDH-T4-003] P2 | `_load_v50_history()`는 live boot caller가 있는 dormant stub이다

1. ID
   - `MDH-T4-003`
2. Severity
   - `P2`
3. 현상 요약
   - `_load_v50_history()`는 dead가 아니다. `_init_v50_modules()` 끝에서 실제로 호출된다.
   - 그러나 helper body는 `if not V50_MODULES_AVAILABLE: return` 뒤 `pass`만 남아 있어, live caller가 도달해도 아무 것도 복원하지 않는다.
4. 코드 근거
   - caller: `_init_v50_modules()` 내부 `main_a.py:1955-1956`
   - helper body: `main_a.py:2128-2141`
   - `_attach_agents()`는 bootstrap 중 `_init_v50_modules()`를 호출한다: `main_a.py:2103-2114`
   - `tests/test_bootstrap_status.py:7-38`는 `_attach_agents()` bootstrap status contract를 검증하지만, `_init_v50_modules()`를 mock으로 대체하므로 `_load_v50_history()` 실효성은 잠그지 않는다.
5. downstream 영향 경계
   - 현재 boot chain은 “history restore helper가 존재하고 호출된다”는 인상을 주지만, 실제 복원 결과는 없다.
   - 향후 V50 모듈을 다시 살릴 때 이 stub를 실제 loader로 오인하면 history restore가 연결된 것으로 착시할 위험이 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - direct test 없음.
   - bootstrap status test는 `_attach_agents()`의 partial failure reporting만 본다. `_load_v50_history()`가 non-no-op인지 여부는 검증하지 않는다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`는 “no-op stub”을 coverage gap으로 남겼다. 본 문서는 caller live / body dormant라는 inventory 분류를 확정한다.
8. 권장 후속 조치
   - 재활성화 계획이 없으면 caller와 stub를 함께 제거한다.
   - 유지한다면 `# DORMANT: called from _init_v50_modules, currently no-op after V65 cleanup` 같은 명시 주석과 focused test를 추가한다.

---

### [MDH-T4-004] P2 | `_restore_preset_registry()`는 destructive-op callback으로 live지만 boot에서는 우회된다

1. ID
   - `MDH-T4-004`
2. Severity
   - `P2`
3. 현상 요약
   - `_restore_preset_registry()` helper 자체는 live다. 다만 live 경로는 boot가 아니라 destructive operation 복구 callback이다.
   - 반대로 `boot()`는 같은 preset restore 로직을 helper 호출 없이 인라인으로 복제해 사용한다. 즉 helper는 `bypassed-live`다.
4. 코드 근거
   - helper 정의: `main_a.py:379-389`
   - callback 등록: `main_a.py:319-330`에서 `ProjectService(..., preset_registry_restorer=self._restore_preset_registry, ...)`
   - callback 소비: `modules/core/services/project_service.py:94-96`
   - callback에 실제 도달하는 menu chain:
     - main menu dispatch `main_a.py:2280-2287`
     - thin delegate `_reset_stage_2()` `main_a.py:3155-3183`
     - thin delegate `_rewind_stage_2()` `main_a.py:3185-3215`
     - thin delegate `_rollback_episode()` `main_a.py:3217-3255`
     - thin delegate `_wipe_production_data()` `main_a.py:3257+`
     - 각 service 메서드의 `_restore_runtime_state()` 호출: `modules/core/services/project_service.py:192`, `259`, `347`, `404`
   - boot 인라인 복제본: `main_a.py:1080-1089`
5. downstream 영향 경계
   - rollback/reset/rewind/wipe 복구에서는 helper가 실제 mutation surface다.
   - project load boot path에서는 helper가 아니라 인라인 복제본이 동일 역할을 수행한다.
   - 따라서 preset restore semantics를 수정할 때 helper만 고쳐서는 boot path가 따라오지 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_main_a_rollback.py`는 thin delegate와 downstream cache invalidation을 검증해 destructive op entrypoint가 live임을 보여준다.
   - `tests/test_project_service.py`, `tests/integration/test_patch_wiring.py`, `tests/property/test_db_rollback_props.py`, `tests/chaos/test_partial_commit.py`는 모두 `preset_registry_restorer=None` 또는 callback 미검증 상태여서 실제 callback path는 잠기지 않는다.
   - ad hoc probe 결과:
     - `_preset_state_raw=None`이면 기존 `preset_registry`가 그대로 유지됐다.
     - payload가 있으면 `PresetRegistry` 인스턴스를 재구성했다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`는 stale preset leakage semantics를 다뤘다.
   - 이번 finding은 “실제 live consumer는 ProjectService callback이고, boot는 helper를 우회한다”는 liveness/consumer inventory를 확정한다.
8. 권장 후속 조치
   - boot의 preset restore 인라인 블록을 `self._restore_preset_registry()` 호출로 수렴시킨다.
   - destructive op tests에 `preset_registry_restorer` non-None case를 추가해 callback live path를 잠근다.
   - stale clear semantics fix는 별도 persistence remediation 트랙(`MPN-T1-001`)과 함께 처리한다.

---

### [MDH-T4-005] P2 | `_init_diversity_engine()` helper는 dead인데 Stage4 consumer slot은 살아 있다

1. ID
   - `MDH-T4-005`
2. Severity
   - `P2`
3. 현상 요약
   - `_init_diversity_engine()`는 caller가 전혀 없다.
   - 그런데 `Stage4Context.from_app()`는 `app.diversity_engine`을 추출하고, `Stage4Orchestrator`는 값이 있으면 Contrastive CoT를 주입한다.
   - 즉 helper는 dead인데, downstream optional consumer slot은 남아 있어 `diversity_engine` 공급 경로가 영구적으로 차가운 상태다.
4. 코드 근거
   - 초기 상태: `main_a.py:262`에서 `self.diversity_engine = None`
   - helper 정의와 유일한 non-None assignment: `main_a.py:953-1002`
   - repo 전역 검색 결과, `_init_diversity_engine(` caller는 없다.
   - `Stage4Context.from_app()` 추출: `modules/core/stage4_context.py:151-184`
   - `Stage4Orchestrator` optional consumer: `modules/core/stage4_orchestrator.py:767-773`
   - 테스트 측면에서도 non-None 공급자는 보이지 않는다:
     - `tests/test_stage4_orchestrator.py:68`
     - `tests/test_chief_writer.py:144`
     - `tests/e2e/test_retry_recovery_e2e.py:69`
     - `tests/test_main_a_stage_entry_contracts.py:40`
     - 위 4곳 모두 `app.diversity_engine = None`만 설정한다.
5. downstream 영향 경계
   - `Stage4`에는 optional branch가 남아 있지만, in-repo bootstrap/restore flow는 그 branch를 활성화할 공급자를 제공하지 않는다.
   - 따라서 현재 code surface는 “feature slot is live, provider helper is dead” 상태다. 이는 단순 dead export보다 강한 consumer mismatch다.
6. 현재 테스트 근거 또는 테스트 부재
   - `_init_diversity_engine()` direct test 없음.
   - `tests/test_stage4_context.py`는 `diversity_engine` slot 추출을 직접 pin하지 않는다.
   - `docs/2026-03-13/MLW-T5-test-realism-regression-findings.md`도 Stage4 `from_app()` blind spot에 `diversity_engine`을 포함시켰다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - 기존 문서는 Stage4 slot blind spot을 지적했지만, helper caller inventory와 연결해 “cold live slot”로 정리하지는 않았다.
8. 권장 후속 조치
   - 기능을 유지할 계획이면 `_init_diversity_engine()`를 실제 boot/stage4 entry path에 연결한다.
   - 기능을 접을 계획이면 helper와 `diversity_engine` slot expectation을 함께 정리해 cold branch를 제거한다.
   - 최소한 `Stage4Context.from_app()` / `Stage4Orchestrator`에 대한 non-None regression test를 추가한다.

---

## 5. Coverage Gap / Open Questions

| 항목 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `preset_registry_restorer` callback live path | direct test 부재 | `ProjectService._restore_runtime_state()`가 non-None restorer를 실제 호출하는 test |
| `_load_v50_history()` reactivation intent | 의도 불명 | V50 history restore를 다시 쓸 계획이 있는지 SSOT 문서화 |
| `sys_caches` historical anchor | cleanup 여부 미정 | dead helper 제거 시 anchor migration/cleanup 필요성 판단 |
| `diversity_engine` non-None path | direct test 부재 | boot/stage4 entry에서 real non-None injection test |

---

## 6. Helper Liveness Ledger

| Helper | 상태 | Finding ID |
|--------|------|-----------|
| `_ignite_quad_cache_system()` | `dead` | `MDH-T4-001` |
| `_is_cache_alive()` | `dead-chain` | `MDH-T4-002` |
| `_load_v50_history()` | `dormant` | `MDH-T4-003` |
| `_restore_preset_registry()` | `bypassed-live` | `MDH-T4-004` |
| `_init_diversity_engine()` | `dead helper / cold live slot` | `MDH-T4-005` |
| `_reload_project_environment()` | `live (removed from candidate set)` | — |
| `boot()` | `live` | — |
| `_attach_agents()` | `live` | — |
| `_init_core_agents()` | `live` | — |
| `_init_v50_modules()` | `live` | — |

## 7. PASS 요약

- PASS1 후보 `6건`
- PASS2 제거 `1건`
- PASS3 확정 `5건`
- 최종 요약: `PASS1 6 -> PASS2 remove 1 -> FINAL 5`

핵심 정리:

- cache 계열은 `_ignite_quad_cache_system` / `_is_cache_alive`가 모두 dead cluster다.
- history 계열은 `_load_v50_history()`가 live caller를 가지지만 body가 빈 dormant stub다.
- preset restore 계열은 `_restore_preset_registry()`가 destructive-op recovery에서는 live이나 boot에서는 우회된다.
- diversity 계열은 `_init_diversity_engine()` helper가 dead인데 Stage4 consumer slot은 살아 있어 cold live slot mismatch가 남는다.
