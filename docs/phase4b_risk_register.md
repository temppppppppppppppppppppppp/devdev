# Phase 4B Risk Register: 리스크 등록부

> 작성일: 2026-02-13
> SSOT: (1) 코드베이스 (커밋 `1b3de64`), (2) Phase 4B 문서군(`docs/phase4b_*.md`)
> 심각도 기준: CRITICAL(시스템 불능) > HIGH(기능 장애) > MEDIUM(품질 저하) > LOW(불편)

---

## 리스크 요약표

| ID | 리스크 | 심각도 | 확률 | 배치 | 탐지 | 대응 | 롤백 |
|----|--------|--------|------|------|------|------|------|
| R1 | 순환 import | HIGH | 중 | 4B-4,5 | py_compile | lazy import | 커밋 revert |
| R2 | Facade 스텁 시그니처 불일치 | CRITICAL | 중 | 전체 | 기존 테스트 | 시그니처 보존 규칙 | 커밋 revert |
| R3 | _rollback_episode 직접 SQL 이전 실패 | HIGH | 중 | 4B-3 | 수동 테스트 | raw_execute 화이트리스트 | DM 모듈 revert |
| R4 | V68 lazy init 결합 깨짐 | HIGH | 중 | 4B-4 | Stage 3 스모크 | self.app 경유 보존 | S3 orch revert |
| R5 | _attach_agents 속성 할당 경로 변경 | CRITICAL | 높 | 4B-5 | import 테스트 | app 참조 전달 | 전체 revert |
| R6 | V50 모듈 31개 optional 주입 복잡성 | MEDIUM | 중 | 4B-5 | 스모크 테스트 | DTO 묶기 | 4B-5 revert |
| R7 | Facade 스텁 과다로 main_a.py 여전히 비대 | LOW | 높 | 전체 | wc -l | 4C에서 제거 | 없음 |
| R8 | _generate_narrative_summary DB 위반 | MEDIUM | 낮 | 4B-2 | 단위 테스트 | db.commit() 교체 | 1줄 수정 |
| R9 | Stage 3 Blueprint 생성 12-파라미터 누락 | HIGH | 중 | 4B-4 | 스모크 테스트 | 파라미터 전수 검증 | S3 orch revert |
| R10 | 기존 테스트 883개 회귀 | MEDIUM | 낮 | 전체 | pytest 전체 | 즉시 수정 | 배치 revert |
| R11 | _shutdown_app DB 접근 경로 변경 | HIGH | 중 | 4B-5 | 수동 종료 테스트 | close() 메서드 사용 | 1줄 수정 |
| R12 | input() 호출이 추출 모듈에서 작동 안 함 | LOW | 낮 | 4B-3,4 | 수동 테스트 | 동일 패턴 유지 | 없음 |

---

## 상세 리스크

### R1: 순환 import 발생

| 항목 | 내용 |
|------|------|
| **심각도** | **HIGH** |
| **발생 확률** | 중 (4B-4, 4B-5에서 발생 가능) |
| **설명** | 추출 모듈이 `main_a.py`의 SovereignApp을 import하고, `main_a.py`가 추출 모듈을 import하면 순환 참조. 특히 `app_bootstrap.py` → `main_a.py` → `app_bootstrap.py` 경로 |
| **탐지** | `python -m py_compile` 실패, `python -c "from main_a import SovereignApp"` 실패 |
| **대응** | (1) 추출 모듈에서 SovereignApp import 금지 — `self.app` 타입 힌트는 `TYPE_CHECKING` 블록에서만 사용. (2) 순환 발견 시 함수 내 lazy import 전환 |
| **롤백** | 해당 배치 커밋 `git revert` |

```python
# 올바른 패턴 (순환 방지)
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main_a import SovereignApp

class AuditService:
    def __init__(self, app: "SovereignApp"):
        self.app = app
```

### R2: Facade 스텁 시그니처 불일치

| 항목 | 내용 |
|------|------|
| **심각도** | **CRITICAL** |
| **발생 확률** | 중 |
| **설명** | Facade 스텁의 파라미터 이름/기본값/순서가 원본과 다르면 기존 호출자(`stage2_orch`, `stage4_orch`)에서 `TypeError` 발생. 예: `_enrich_director_result`의 `content_length=0` 기본값 누락 시 |
| **탐지** | 기존 pytest 883개 실행 시 `TypeError` 발생으로 즉시 감지. 추가로 `grep -n "def _.*self.*return self\._" main_a.py` 결과와 원본 시그니처 대조 |
| **대응** | **시그니처 규칙 S1~S3** (`phase4b_compat_matrix.md` §2) 엄격 준수. 자동 검증: 원본 메서드의 `inspect.signature()` vs Facade 스텁의 `inspect.signature()` 비교 테스트 추가 |
| **롤백** | 해당 Facade 스텁 1줄 수정 |

### R3: _rollback_episode 직접 SQL 이전 실패

| 항목 | 내용 |
|------|------|
| **심각도** | **HIGH** |
| **발생 확률** | 중 |
| **설명** | `_rollback_episode`(`main_a.py:3957-4099`)은 직접 SQL 15건 포함. `DBAdapter.raw_execute()` 화이트리스트(`db_adapter.py:60`)는 `DELETE FROM`, `UPDATE`, `SELECT`만 허용. `DELETE FROM sqlite_sequence`(`main_a.py:4059`)가 걸릴 가능성 있음 |
| **탐지** | `tests/test_data_manager.py`에서 각 SQL 패턴의 `raw_execute()` 통과 확인 |
| **대응** | (1) `raw_execute()` 화이트리스트에 `DELETE FROM sqlite_sequence` 패턴 추가 검토. (2) 또는 `db_manager.py`에 `reset_sequence()` public 메서드 추가 |
| **롤백** | `data_manager.py` 모듈만 revert, Facade 스텁 제거 |

**관련 코드**:
- `db_adapter.py:55-65`: `_ALLOWED_SQL_PREFIXES = ("DELETE FROM", "UPDATE ", "SELECT ")`
- `main_a.py:4059`: `db.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN {seq_targets}")`

### R4: V68 lazy init 결합 깨짐

| 항목 | 내용 |
|------|------|
| **심각도** | **HIGH** |
| **발생 확률** | 중 |
| **설명** | `_stage_3_batch_blueprinting`(`main_a.py:3296-3349`)과 `_stage_4_v2_chief_writer`(`main_a.py:4350-4396`)의 lazy init 블록이 `self.state_tracker`, `self.world_state`, `self.fact_ledger`를 SovereignApp 인스턴스에 직접 할당. 추출 모듈에서 `self.app.state_tracker = StateTracker(...)` 형태로 변경해야 하는데, 이 경로가 깨지면 Stage 4에서 `AttributeError` |
| **탐지** | Stage 3 스모크 테스트: Blueprint 1화 생성. Stage 4 진입 시 `self.app.state_tracker` 접근 확인 |
| **대응** | 추출 모듈에서 `self.app.state_tracker = ...` 패턴 유지. `hasattr(self.app, "state_tracker")` 체크도 그대로 보존 |
| **롤백** | `stage3_orchestrator.py` revert |

### R5: _attach_agents 속성 할당 경로 변경

| 항목 | 내용 |
|------|------|
| **심각도** | **CRITICAL** |
| **발생 확률** | 높 |
| **설명** | `_attach_agents`(`main_a.py:1326-1738`, 413줄)은 `self.agents`, `self.state_tracker`, `self._feedback_system`, `self._prompt_builder` 등 15+ 속성을 SovereignApp에 직접 할당. 추출 후 `self.app.agents = {}` 형태로 변경해야 하며, 하나라도 누락하면 전체 시스템 기동 실패 |
| **탐지** | `python -c "from main_a import SovereignApp; app = SovereignApp()"` → `app._attach_agents()` 호출 후 `hasattr` 전수 검사 |
| **대응** | (1) 추출 전 `_attach_agents` 내 `self.xxx = ...` 전수 목록 생성 (`grep -n 'self\.\w\+ = ' main_a.py | sed -n '1326,1738p'`). (2) 추출 후 동일 grep으로 `self.app.xxx = ...` 전수 확인. (3) 속성 할당 수 불일치 시 즉시 중단 |
| **롤백** | Phase 4B 전체 `git revert` (부분 revert 불가 — bootstrap은 최후 배치) |

### R6: V50 모듈 31개 optional 주입 복잡성

| 항목 | 내용 |
|------|------|
| **심각도** | **MEDIUM** |
| **발생 확률** | 중 |
| **설명** | `_attach_agents`에서 초기화하는 V50 모듈 31개(`main_a.py:1506-1718` 범위)는 `try/except`로 감싸진 optional import. 추출 시 이 패턴을 그대로 보존해야 하며, 일부 모듈의 `self.app.xxx` 접근 패턴이 변경될 수 있음 |
| **탐지** | Stage 0→2→4 스모크 테스트에서 V50 모듈 사용 여부 확인 |
| **대응** | V50 모듈 초기화 블록을 그대로 이전. `try/except` 패턴 보존. 개별 모듈 실패 시 비차단 (`[V64.P4] OPTIONAL:` 주석 유지) |
| **롤백** | `app_bootstrap.py` revert |

### R7: Facade 스텁 과다

| 항목 | 내용 |
|------|------|
| **심각도** | **LOW** |
| **발생 확률** | 높 (확정) |
| **설명** | 66개 Facade 스텁 × 3줄 = ~200줄이 main_a.py에 잔류. `__init__`(78줄) + `_safe_commit`(23줄) + DI 조립(~50줄) + Facade(~200줄) = ~350줄. 목표 ~1,200줄보다 작지만, 가독성이 떨어질 수 있음 |
| **탐지** | `wc -l main_a.py` (4B 완료 후 ~1,200줄 이하 확인) |
| **대응** | Phase 4C에서 `self.app` 제거 시 Facade 스텁도 함께 제거됨. 일시적 상태 |
| **롤백** | 없음 (리스크 수용) |

### R8: _generate_narrative_summary DB 위반

| 항목 | 내용 |
|------|------|
| **심각도** | **MEDIUM** |
| **발생 확률** | 낮 |
| **설명** | `main_a.py:4278`의 `self.current_project.db.conn.commit()`은 DB 추상화 위반. `narrative_summary.py`로 추출 시 이를 `db.commit()` (DBManager public 메서드)로 교체 필요 |
| **탐지** | `tests/test_narrative_summary.py`에서 mock DB의 `commit()` 호출 확인 |
| **대응** | 추출 시 `self.app.current_project.db.conn.commit()` → `self.app.current_project.db.commit()` 1줄 교체 |
| **롤백** | 1줄 수정 |

### R9: Stage 3 Blueprint 생성 12-파라미터 누락

| 항목 | 내용 |
|------|------|
| **심각도** | **HIGH** |
| **발생 확률** | 중 |
| **설명** | `_stage_3_batch_blueprinting`에서 `agents["three_phase_bp"].generate()`를 호출할 때 12개 파라미터 전달(`main_a.py:3557-3572`). 추출 시 하나라도 누락하면 Stage 3 전체 실패 |
| **탐지** | Stage 3 스모크 테스트: 1화 Blueprint 생성. `TypeError: missing required argument` 즉시 감지 |
| **대응** | 추출 전 `generate()` 호출의 12개 파라미터 전수 목록 작성 (`ep_num`, `arc_data`, `prev_blueprint`, `prev_blueprints`, `max_retries`, `director`, `arc_idx`, `entity_registry`, `protagonist_name`, `protagonist_config`, `state_tracker`, `db`, `semantic_context`, `prev_manuscripts_text`). 추출 후 동일 파라미터 확인 |
| **롤백** | `stage3_orchestrator.py` revert |

**관련 코드** (`main_a.py:3557-3572`):
```python
blueprint, pipeline_result = self.agents["three_phase_bp"].generate(
    ep_num=working_ep,
    arc_data=arc_data,
    prev_blueprint=prev_blueprint,
    prev_blueprints=prev_blueprints[-30:],
    max_retries=4,
    director=self.agents["director"],
    arc_idx=arc_idx,
    entity_registry=entity_registry_for_stage3,
    protagonist_name=protagonist_name_for_stage3,
    protagonist_config=_bp_protagonist_config,
    state_tracker=getattr(self, "state_tracker", None),
    db=self.current_project.db,
    semantic_context=_bp_semantic_ctx,
    prev_manuscripts_text=_prev_ms_text_for_bp,
)
```

### R10: 기존 테스트 883개 회귀

| 항목 | 내용 |
|------|------|
| **심각도** | **MEDIUM** |
| **발생 확률** | 낮 |
| **설명** | Phase 4B는 신규 파일 추가 + main_a.py Facade 전환이므로 기존 테스트에 영향이 적음. 그러나 import 순서 변경이나 순환 참조로 일부 테스트가 깨질 수 있음 |
| **탐지** | `set PYTHONIOENCODING=utf-8 && pytest -x` (첫 실패 시 즉시 중단) |
| **대응** | 매 배치 커밋 전 `pytest` 전체 실행 필수. 5개 이상 회귀 시 해당 배치 revert |
| **롤백** | 해당 배치 `git revert` |

### R11: _shutdown_app DB 접근 경로 변경

| 항목 | 내용 |
|------|------|
| **심각도** | **HIGH** |
| **발생 확률** | 중 |
| **설명** | `_shutdown_app`(`main_a.py:1927-2020`)에서 `self.current_project.db.conn.close()`(`main_a.py:2006` 근처)를 직접 호출. 추출 후 이 경로가 변경되면 종료 시 DB 미닫힘 → 데이터 손실 가능 |
| **탐지** | 수동 종료 테스트: 메뉴 "5" 선택 후 DB 파일 잠금 해제 확인 |
| **대응** | `db.close()` (Phase 4A에서 추가된 `db_manager.py:298` 메서드) 사용으로 교체 |
| **롤백** | 1줄 수정 |

### R12: input() 호출이 추출 모듈에서 작동 안 함

| 항목 | 내용 |
|------|------|
| **심각도** | **LOW** |
| **발생 확률** | 낮 |
| **설명** | `_reset_stage_2`, `_rewind_stage_2`, `_rollback_episode`, `_wipe_production_data`에서 `input()` 호출로 사용자 확인. 추출 모듈에서도 `input()`은 동일하게 작동 (표준 라이브러리) |
| **탐지** | 수동 테스트 |
| **대응** | 패턴 그대로 유지. 향후 UI 서비스로 전환 가능하나 4B 범위 밖 |
| **롤백** | 없음 |

---

## 리스크 대응 우선순위

| 순위 | ID | 이유 |
|------|-----|------|
| 1 | R5 | CRITICAL + 높은 확률 — 전체 시스템 기동 불능 |
| 2 | R2 | CRITICAL + 중간 확률 — 호출 경로 깨짐 |
| 3 | R4 | HIGH + 중간 확률 — V68 핵심 시스템 결합 |
| 4 | R1 | HIGH + 중간 확률 — 순환 import |
| 5 | R3 | HIGH + 중간 확률 — 데이터 무결성 관련 |
| 6 | R9 | HIGH + 중간 확률 — Stage 3 완전 실패 |
| 7 | R11 | HIGH + 중간 확률 — 종료 시 데이터 손실 |
| 8 | R6 | MEDIUM + 중간 확률 — 복잡성 관리 |
| 9 | R10 | MEDIUM + 낮은 확률 — 테스트 회귀 |
| 10 | R8 | MEDIUM + 낮은 확률 — 1줄 수정으로 해결 |
| 11 | R7 | LOW — 일시적 상태 |
| 12 | R12 | LOW — 실질 리스크 없음 |
