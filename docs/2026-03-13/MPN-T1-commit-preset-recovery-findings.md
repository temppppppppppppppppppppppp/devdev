# [MPN-T1] Commit / Preset Recovery Findings

> 작성일: 2026-03-13
> 상태: `3pass executed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-persistence-narrative-detail-full-survey-audit-order.md`

---

## 조사 범위

- `main_a.py`
  - `_restore_preset_registry()`
  - `_safe_commit()`
  - `_safe_commit_async()`
  - `_is_cache_alive()`
- `modules/core/services/project_service.py`

## 필수 근거

- `tests/test_project_service.py`
- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- 추가 확인
  - `modules/core/db_manager.py`
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage3_context.py`
  - `modules/core/stage3_orchestrator.py`
  - `docs/2026-02-23/opus_tf6_system_audit_order.md`
  - `docs/2026-02-23/opus_tf6_patch_order.md`
  - `docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md`
  - `docs/2026-03-13/MCP-T4-destructive-ops-recovery-findings.md`

## PASS 기록

- PASS 1: 완료
  - 후보 5건 수집
  - `_restore_preset_registry`, cache persistence, sync/async commit semantics, cache health-check, legacy overlap 여부를 분리했다.
- PASS 2: 완료
  - 관련 테스트 `28 passed in 5.08s`
  - ad hoc verification 3건 수행
    - `_restore_preset_registry()` no-data 경로가 기존 `preset_registry`를 유지하는지 확인
    - `_ignite_quad_cache_system()`에서 `save_anchor=False`여도 성공 로그/캐시 주입이 이어지는지 확인
    - `_ignite_quad_cache_system()`에서 `_safe_commit=False`여도 성공 로그/캐시 주입이 이어지는지 확인
  - `TF-6`, `OPUS-TF-T1`, `MCP-T4`와 중복 여부 교차 검증
- PASS 3: 완료
  - PASS1 후보 5건 -> PASS2 제거 3건 -> 최종 2건

## Executive Summary

- `preset_state`가 없거나 파싱에 실패하는 경로에서 `app.preset_registry`가 비워지지 않아 이전 프로젝트 프리셋이 다음 프로젝트/복구 경로로 누수될 수 있다.
- `sys_caches` 저장 경로는 `save_anchor()`와 `_safe_commit()`의 `False` 반환을 모두 무시하고 성공 로그와 cache injection을 진행한다.

## PASS 2 제거 항목

| 후보 | 판정 | 이유 |
|----|----|----|
| `_safe_commit_async()`가 sync 버전과 다른 rollback 의미를 가질 가능성 | 제거 | `main_a.py:401-412`는 `asyncio.to_thread(self._safe_commit)`만 호출하고, `DBManager`가 `check_same_thread=False`로 연결을 연다. 현재 코드 범위에서는 별도 비동기 전용 실패 surface를 확인하지 못했다. |
| `_safe_commit()`의 direct `conn.commit()` 자체를 신규 finding으로 승격 | 제거 | `docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md:100-170`에 direct commit/protocol drift가 이미 정리돼 있다. 이번 T1에서는 그 위에 얹힌 shared helper 오용 surface만 유지했다. |
| `_is_cache_alive()`의 broad `except Exception` | 제거 | 현재 helper 의도는 best-effort cache probe이며, 이 자체만으로 persistence corruption이나 consumer misread가 발생하는 증거는 부족했다. coverage gap으로만 남긴다. |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MPN-T1-001 | P2 | retained | `main_a.py` / `_restore_preset_registry`, project load preset restore | no-data/parse-fail 경로가 기존 `app.preset_registry`를 유지해 project switch/rollback 뒤 stale preset이 누수될 수 있음 |
| MPN-T1-002 | P2 | retained | `main_a.py` / `_ignite_quad_cache_system`, `_safe_commit` | `save_anchor()`와 `_safe_commit()`의 `False` 반환을 무시해 cache metadata 저장 실패 후에도 성공 로그와 cache injection이 발생함 |

---

## [MPN-T1-001] P2 | `_restore_preset_registry()` no-data/failure 경로가 stale preset을 유지한다

**현상 요약**

`_restore_preset_registry()`는 복원 원본이 없으면 즉시 `return`하고, 파싱 실패도 warning만 남긴 채 끝난다. 프로젝트 로드 경로도 동일하게 `_ps_raw is not None`일 때만 `self.preset_registry`를 갱신한다. 따라서 이전 프로젝트에서 이미 채워진 `app.preset_registry`가 새 프로젝트의 `preset_state` 부재 또는 파손 상황에서도 그대로 남는다.

**코드 근거**

- `main_a.py:363-375`
  - `_restore_preset_registry()`는 `_ps_raw is None`이면 `self.preset_registry`를 건드리지 않고 반환한다.
  - `from_json(...)` 실패도 log-only 처리이며 stale object를 비우지 않는다.
- `main_a.py:1000-1009`
  - 프로젝트 로드 시에도 `_ps_raw is not None` 조건 안에서만 `self.preset_registry`를 덮어쓴다.
- `modules/core/services/project_service.py:94-98`
  - rollback/reset/wipe 복구 경로에서 `preset_registry_restorer`를 non-blocking으로 호출한다.
- `modules/core/stage2_context.py:214-244`
- `modules/core/stage3_context.py:103-116`
- `modules/core/stage2_orchestrator.py:187-189`
- `modules/core/stage3_orchestrator.py:626-632`
  - Stage 2/3 consumer는 `app.preset_registry`를 그대로 context/state tracker 입력으로 소비한다.

**downstream 영향 경계**

- 프로젝트 전환 직후 `preset_state`가 없는 프로젝트를 열면 이전 프로젝트의 프리셋 조합이 새 프로젝트의 Stage 2/3에 주입될 수 있다.
- rollback/wipe 후 `preset_state`가 비정상인 경우에도 helper는 성공처럼 진행되고, `StateTracker(preset_registry=app.preset_registry, ...)`가 stale 스키마를 잡는다.
- 결과적으로 active field, NPC field schema, prompt schema가 현재 프로젝트가 아니라 직전 프로젝트 기준으로 남을 수 있다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_project_service.py`, `tests/property/test_db_rollback_props.py`, `tests/chaos/test_partial_commit.py` 어디에도 `preset_registry_restorer` callback 또는 `_restore_preset_registry()` 자체 검증이 없다.
- ad hoc verification:
  - `current_project._preset_state_raw=None`, 기존 `preset_registry='OLD'` 상태에서 `SovereignApp._restore_preset_registry(app)` 호출 결과 `preset_registry`가 그대로 `OLD`로 남았다.
- 현재 테스트는 rollback invariant warning과 destructive op success/cancel 위주이며, preset restore lifecycle은 비어 있다.

**기존 문서와의 중복 여부**

- `duplicate status`: `related-but-new-shared-helper-surface`
- 관련 문서:
  - `docs/2026-02-23/opus_tf7_k_audit.md`의 `TF-7-K-1`은 "preset_state 복원 경로 부재"를 다뤘다.
  - 이번 finding은 복원 경로가 추가된 뒤에도 `no-data/failure -> stale clear 없음`이 남은 shared helper surface다.

**권장 후속 조치**

- `_restore_preset_registry()`와 프로젝트 로드 경로 둘 다에서 복원 시도 전 `self.preset_registry = None`을 기본값으로 명시한다.
- `preset_state` 부재와 malformed `preset_state`를 구분해 log하고, 실패 시 stale object를 유지하지 않도록 한다.
- 회귀 테스트를 추가한다.
  - 프로젝트 A 로드 후 프로젝트 B(`preset_state` 없음) 로드 시 `app.preset_registry is None`
  - rollback path에서 malformed `preset_state`를 주입해도 stale preset이 남지 않는지 확인

---

## [MPN-T1-002] P2 | cache persistence 경로가 bool 실패 신호를 무시하고 성공처럼 진행된다

**현상 요약**

`_ignite_quad_cache_system()`은 `save_anchor("sys_caches", cache_info)`와 `_safe_commit()`를 연달아 호출하지만, 둘 다 `bool` 반환값을 검사하지 않는다. 현재 `try/except`는 예외만 잡으므로, `save_anchor()`가 `False`를 반환하거나 `_safe_commit()`이 rollback 후 `False`를 반환해도 success log, `CACHE_CREATED` audit, agent cache injection이 그대로 수행된다.

**코드 근거**

- `main_a.py:1226-1249`
  - `save_anchor("sys_caches", cache_info)` 반환값 무시
  - `_safe_commit()` 반환값 무시
  - 이어서 `"캐시 정보 DB 저장 완료"` log, `AuditEvents.CACHE_CREATED`, `agents[*].cache_name = ...` 수행
- `main_a.py:377-399`
  - `_safe_commit()`은 예외를 삼키고 `True/False`만 반환한다. caller가 반환값을 검사하지 않으면 실패가 surface되지 않는다.
- `modules/core/db_manager.py:1542-1562`
  - `save_anchor()`도 예외를 warning으로 삼키고 `False`를 반환한다.
  - non-nested 경로에서는 내부에서 이미 `self.commit()`까지 수행하므로 `_safe_commit()`은 별도의 권위 있는 저장 확인이 아니다.

**downstream 영향 경계**

- 현재 세션에서는 `writer/analyst/weaver.cache_name`이 주입되어 cache reuse가 가능한 것처럼 보이지만, `sys_caches` anchor가 실제로 저장되지 않았을 수 있다.
- 다음 재시작에서는 `main_a.py:1151-1255`가 `sys_caches` anchor를 못 읽어 cache lifecycle이 끊기고, operator는 이전 성공 로그/Audit 때문에 저장이 된 것으로 오인할 수 있다.
- shared helper 관점에서 `_safe_commit()`의 성공 여부가 persistence contract가 아니라 단순 best-effort boolean인데, 호출부는 이를 "저장 완료" 의미로 오용한다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_project_service.py`, `tests/property/test_db_rollback_props.py`, `tests/chaos/test_partial_commit.py`는 cache persistence 경로를 전혀 다루지 않는다.
- repo 내 테스트 검색 결과 `_ignite_quad_cache_system()`, `_is_cache_alive()`, `sys_caches` anchor save-failure path를 직접 검증하는 테스트가 없다.
- ad hoc verification:
  - `save_anchor=False`, `_safe_commit=True`로 구성한 synthetic app에서 `"💾 [System] 캐시 정보 DB 저장 완료"` 로그와 `writer/analyst/weaver.cache_name` 주입이 모두 발생했다.
  - `save_anchor=True`, `_safe_commit=False`로 구성한 synthetic app에서도 동일한 성공 로그와 cache injection이 발생했다.

**기존 문서와의 중복 여부**

- `duplicate status`: `none`

**권장 후속 조치**

- `save_anchor_ok = self.current_project.db.save_anchor(...)`와 `commit_ok = self._safe_commit()`를 분리해 둘 다 `True`일 때만 success log/audit/cache injection을 수행한다.
- `save_anchor()`가 이미 non-nested commit을 수행하는 계약을 유지할지, 아니면 `_safe_commit()` 단일 경계로 정리할지 한 경로로 고정한다.
- 회귀 테스트를 추가한다.
  - `save_anchor=False`면 success log와 cache injection이 없어야 함
  - `_safe_commit=False`면 `CACHE_CREATED` audit가 기록되지 않아야 함

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `_restore_preset_registry()` no-data / malformed path | 테스트 부재 | 프로젝트 전환과 rollback 후 stale preset 미유지 regression test |
| `preset_registry_restorer` service callback | direct test 부재 | `ProjectService._restore_runtime_state()`가 callback failure와 no-data를 어떻게 처리하는지 보는 unit test |
| `_ignite_quad_cache_system()` failure signals | 테스트 부재 | `save_anchor=False`, `_safe_commit=False`, `_is_cache_alive()` transient failure를 분리 검증하는 unit test |
| `_safe_commit_async()` helper 자체 | direct test 부재 | `False` propagation, exception-to-False, sync delegation을 검증하는 helper-level async test |
| `_is_cache_alive()` health check | 테스트 부재 | cache API error vs dead cache vs empty cache name을 구분하는 test |

## 마감 체크

- `_safe_commit()` 실패 시 인메모리/DB drift 경계: cache lifecycle 쪽 1건 확정
- `_safe_commit_async()`와 sync 의미 비교: 신규 retained 없음
- `_restore_preset_registry()` recovery vs mutation helper 경계: stale preset 1건 확정
- cache alive 판정 오용 여부: 단독 finding 없음, coverage gap으로 유지

## 최종 판정

- 최종 retained finding: `2건`
  - `P0`: 0건
  - `P1`: 0건
  - `P2`: 2건
  - `P3`: 0건
- 본 문서는 `template / not executed`가 아니라 `executed T1 finding set`이다.
