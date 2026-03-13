# MDH-T4: Bootstrap / History / Cache Helper Liveness Findings

> 작성일: 2026-03-13
> 작성자: Claude Opus
> 터미널: T4
> 트랙: `main_a.py` dormant helper / live consumer inventory audit
> 상태: `PASS 3 확정`

---

## 0. 조사 범위

| Helper | 정의 위치 | 조사 결론 |
|--------|----------|-----------|
| `_ignite_quad_cache_system()` | `main_a.py:1148-1291` | **dead** |
| `_is_cache_alive()` | `main_a.py:1293-1301` | **dead** (sole consumer가 dead) |
| `_load_v50_history()` | `main_a.py:2083-2096` | **dormant** (caller 있으나 body가 no-op stub) |
| `_restore_preset_registry()` | `main_a.py:379-389` | **bypassed-live** (callback 등록됨 + boot 인라인 중복) |
| `_init_diversity_engine()` | `main_a.py:908-957` | **dead** |

추가 확인된 live bootstrap helper (참고):

| Helper | 정의 위치 | 상태 |
|--------|----------|------|
| `boot()` | `main_a.py:995-1118` | **live** (entry point) |
| `_attach_agents()` | `main_a.py:1921-2069` | **live** (boot→attach) |
| `_init_core_agents()` | `main_a.py:1468-1578` | **live** (attach→init) |
| `_init_v50_modules()` | `main_a.py:1592-1919` | **live** (attach→init) |
| `_reload_project_environment()` | `main_a.py:973-993` | **live** (boot→reload) |

---

## 1. 확정 Findings

---

### [MDH-T4-001] P3 | `_ignite_quad_cache_system()` — dead code, 호출부 0건

**현상 요약**

`_ignite_quad_cache_system()`(144줄)은 Gemini Context Cache API를 사용해 Writer/Analyst/Weaver 3개 에이전트에 캐시를 생성·주입하는 helper다. V31 시대 legacy이며, 현재 코드베이스 어디에서도 호출되지 않는다.

**코드 근거**

- 정의: `main_a.py:1148-1291`
- repo 전역 grep: 정의 1건 + 문서 참조만 존재. production/test caller **0건**.
- `tools2/project_full_source.md:3502`에 `self._ignite_quad_cache_system()` 호출이 남아 있으나, 이 파일은 snapshot 문서이며 실행 코드가 아님.

**downstream 영향 경계**

- 현재 캐싱은 `base_agent.py`의 Context Caching 인프라(L1599-1820)가 완전 대체. 5개 에이전트(ChiefWriter, ArcEnsemble, BlueprintEnsemble, DirectorEnsemble, DirectorContinuity)에 per-agent 캐시 적용 완료.
- `_ignite_quad_cache_system()` 삭제해도 production path에 영향 없음.

**현재 테스트 근거**

- 테스트 부재. `_ignite_quad_cache_system`을 직접 호출하는 test 0건.

**기존 문서와의 중복 여부**

- `already-covered-do-not-reopen`: `docs/2026-02-28/TF-31-style-pipeline-audit.md:134`에서 이미 "메서드 자체가 dead code — 호출부 0건" 확인.
- `MCP-T2-agent-bootstrap-di-findings.md:159`에서도 dead code로 기록하되 별도 finding으로 채택하지 않음.
- 본 finding은 live consumer inventory 관점에서 **dead** 확정을 SSOT로 잠그는 목적.

**권장 후속 조치**

- `_ignite_quad_cache_system()` 삭제 가능. 삭제 시 `_is_cache_alive()`도 함께 삭제.
- `sys_caches` anchor가 DB에 잔류할 수 있으나, anchor 자체가 read-only로 방치되므로 비차단.

---

### [MDH-T4-002] P3 | `_is_cache_alive()` — dead code, sole consumer가 dead

**현상 요약**

`_is_cache_alive()`는 Gemini Cache API health check helper다. 유일한 caller가 `_ignite_quad_cache_system()` 내부 3곳(L1189, L1215, L1238)이며, 해당 caller 자체가 dead code이므로 이 helper도 dead다.

**코드 근거**

- 정의: `main_a.py:1293-1301`
- caller: `_ignite_quad_cache_system()` 내부 3건만. 외부 caller 0건.

**downstream 영향 경계**

- 삭제 영향 없음.

**현재 테스트 근거**

- 테스트 부재. `MPN-T1-commit-preset-recovery-findings.md:175`에서도 "테스트 부재" 기록.

**기존 문서와의 중복 여부**

- `related-but-new-live-consumer-surface`: `MPN-T1-commit-preset-recovery-findings.md`에서 cache health check 관점으로 다뤘으나, liveness 분류는 본 문서가 최초.

**권장 후속 조치**

- `MDH-T4-001`과 함께 삭제.

---

### [MDH-T4-003] P2 | `_load_v50_history()` — dormant (caller live, body no-op)

**현상 요약**

`_load_v50_history()`는 `_init_v50_modules()` 끝(L1911)에서 호출되나, body가 `V50_MODULES_AVAILABLE` guard + `pass` 문만 남은 no-op stub이다. V65에서 V50.1~V51.1 모듈(tension_manager, dialogue_engine, subplot_weaver, reader_simulator, pacing_analyzer) 히스토리 로딩 로직이 삭제되었으며, 주석으로 "재연결 시 복원 가능"이 남아 있다.

**코드 근거**

- 정의: `main_a.py:2083-2096`
- caller: `main_a.py:1911` (`_init_v50_modules()` 내부)
- body 전문:
  ```python
  def _load_v50_history(self) -> None:
      if not V50_MODULES_AVAILABLE:
          return
      pass
  ```

**downstream 영향 경계**

- production path에서 호출되지만 아무 일도 하지 않음. 삭제해도 동작 변화 없음.
- 단, 주석에 "재연결 시 복원 가능" 의도가 명시되어 있으므로, 향후 V50 모듈 재활성화 계획이 있으면 placeholder로 유지할 수 있음.

**현재 테스트 근거**

- `_load_v50_history()` 직접 테스트 0건.
- `test_bootstrap_status.py`에서 `_init_v50_modules`를 MagicMock으로 대체해 간접적으로도 미검증.

**기존 문서와의 중복 여부**

- `related-but-new-live-consumer-surface`: `MCP-T2-agent-bootstrap-di-findings.md:160`에서 "No-op stub" 관측. 본 문서는 dormant 확정 분류가 목적.

**권장 후속 조치**

- V50 재활성화 계획 없으면 삭제 가능. caller(`_init_v50_modules` L1911)도 함께 제거.
- 재활성화 계획 있으면 placeholder 유지하되, `# DORMANT: V65 삭제, 재연결 시 복원` 주석 명시.

---

### [MDH-T4-004] P2 | `_restore_preset_registry()` — bypassed-live (callback + boot 인라인 중복)

**현상 요약**

`_restore_preset_registry()`는 두 가지 경로로 호출된다:
1. **callback 등록**: `main_a.py:328` — `StateService(preset_registry_restorer=self._restore_preset_registry)`로 주입. `ProjectService._restore_runtime_state()` (project_service.py:94-96)에서 rollback/reset/wipe 시 호출됨.
2. **boot 인라인**: `main_a.py:1035-1044` — `boot()` 메서드에서 동일 로직을 인라인으로 중복 구현.

helper 자체는 live이나, boot 경로에서는 인라인 복제본이 helper를 우회(bypass)한다.

**코드 근거**

- helper 정의: `main_a.py:379-389`
- callback 등록: `main_a.py:328`
- callback 소비: `project_service.py:94-96`
- boot 인라인: `main_a.py:1035-1044` (동일 로직, helper 미사용)

**downstream 영향 경계**

- rollback/reset/wipe 경로: callback → helper 호출 (live)
- boot 경로: 인라인 로직 직접 실행 (helper bypass)
- MPN-T1-001에서 지적: no-data/failure 시 stale preset 잔류 위험. 두 경로 모두 동일 결함.

**현재 테스트 근거**

- `preset_registry_restorer` callback 직접 테스트 0건 (`MPN-T1-commit-preset-recovery-findings.md:101` 확인).
- `test_project_service.py`: `preset_registry_restorer=None`으로 주입되어 callback 경로 미검증.
- `tests/chaos/test_partial_commit.py`: `preset_registry_restorer=None`.

**기존 문서와의 중복 여부**

- `related-but-new-live-consumer-surface`: `MPN-T1-001`에서 stale preset 누수 관점으로 다뤄짐. 본 문서는 "callback은 live이나 boot에서 bypass" 관점이 신규.

**권장 후속 조치**

- boot 인라인(L1035-1044)을 `self._restore_preset_registry()` 호출로 통합하여 중복 제거.
- no-data 경로에서 `self.preset_registry = None` 기본값 명시 (MPN-T1-001 권장사항과 동일).

---

### [MDH-T4-005] P3 | `_init_diversity_engine()` — dead code, 호출부 0건

**현상 요약**

`_init_diversity_engine()`(50줄)은 `NarrativeDiversityEngine`을 초기화하는 helper다. 정의만 존재하고 production/test 어디에서도 호출되지 않는다.

**코드 근거**

- 정의: `main_a.py:908-957`
- repo 전역 grep: 정의 1건만. caller 0건.
- `NarrativeDiversityEngine` 클래스 자체는 `modules/core/narrative_diversity.py`에 존재하고, 별도 test(`test_sweep26.py`, `test_tf3_tier1_genre_completeness.py`)에서 직접 생성·테스트되지만, `_init_diversity_engine()` helper를 거치지 않음.

**downstream 영향 경계**

- `self.diversity_engine` 속성을 설정하지만, 이 속성의 downstream consumer가 있는지는 별도 확인 필요. 현재 bootstrap chain(`boot→_attach_agents→_init_v50_modules`)에서 `_init_diversity_engine` 호출이 없으므로 `self.diversity_engine`은 미설정 상태.

**현재 테스트 근거**

- 테스트 부재.

**기존 문서와의 중복 여부**

- `none`: 기존 감리 문서에서 이 helper에 대한 언급 없음. 본 문서가 최초 dead 확정.

**권장 후속 조치**

- 삭제 가능. `NarrativeDiversityEngine` import(`main_a.py:54`)도 이 helper만 사용하면 함께 정리.
- 단, `NarrativeDiversityEngine`이 다른 곳에서 직접 사용되는지 확인 필요 (현재 main_a.py 내에서는 이 helper만 사용).

---

## 2. PASS 요약

### PASS 1 → PASS 2 → PASS 3

| PASS 1 후보 | PASS 2 결과 | PASS 3 확정 |
|------------|------------|------------|
| `_ignite_quad_cache_system` — dead 의심 | grep 전역 확인: caller 0건. 기존 문서(TF-31, MCP-T2)에서도 dead 관측. | **MDH-T4-001 확정 (P3, dead)** |
| `_is_cache_alive` — dead 의심 | sole consumer = `_ignite_quad_cache_system` (dead). 외부 caller 0건. | **MDH-T4-002 확정 (P3, dead)** |
| `_load_v50_history` — dormant 의심 | caller 1건(`_init_v50_modules:1911`) live. body = `pass`. V65 삭제 기록. | **MDH-T4-003 확정 (P2, dormant)** |
| `_restore_preset_registry` — live 의심 | callback 등록 live + boot 인라인 bypass 확인. test 0건. | **MDH-T4-004 확정 (P2, bypassed-live)** |
| `_init_diversity_engine` — dead 의심 | grep 전역 확인: caller 0건. 기존 문서 언급 없음. | **MDH-T4-005 확정 (P3, dead)** |

### Coverage Gap / Open Questions

| 항목 | 상태 | 비고 |
|------|------|------|
| `sys_caches` DB anchor 잔류 데이터 | open | `_ignite_quad_cache_system` 삭제 시 DB에 남은 anchor cleanup 필요 여부 |
| V50 모듈 재활성화 계획 | open | `_load_v50_history` placeholder 유지/삭제 판단 기준 |
| `NarrativeDiversityEngine` import 정리 | open | `_init_diversity_engine` 삭제 시 L54 import 공동 제거 가능 여부 |

---

## 3. Helper Liveness Ledger (T4 범위)

| Helper | 상태 | Finding ID |
|--------|------|-----------|
| `_ignite_quad_cache_system()` | **dead** | MDH-T4-001 |
| `_is_cache_alive()` | **dead** | MDH-T4-002 |
| `_load_v50_history()` | **dormant** | MDH-T4-003 |
| `_restore_preset_registry()` | **bypassed-live** | MDH-T4-004 |
| `_init_diversity_engine()` | **dead** | MDH-T4-005 |
| `boot()` | live | — |
| `_attach_agents()` | live | — |
| `_init_core_agents()` | live | — |
| `_init_v50_modules()` | live | — |
| `_reload_project_environment()` | live | — |
