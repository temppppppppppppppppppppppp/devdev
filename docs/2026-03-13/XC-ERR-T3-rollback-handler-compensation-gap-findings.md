# XC-ERR-T3: 롤백 핸들러 보상 갭

> 생성일: 2026-03-13
> 초점: `project_service.py` 롤백/리셋 + `db_manager.py` 트랜잭션 관리
> 방법론: 3-Pass

---

## 1. 롤백 작업 분석

### ProjectService 롤백 메서드 목록
| 메서드 | 라인 | 파괴 범위 |
|--------|------|----------|
| `reset_stage_2()` | L177-214 | Stage 2 전체 + 모든 다운스트림 |
| `rewind_stage_2()` | L216-282 | 지정 Arc 이후 + 다운스트림 |
| `rollback_episode()` | L284-372 | 지정 에피소드 이후 전체 |
| `wipe_production_data()` | L398-429 | 전체 프로덕션 데이터 |

### 공통 롤백 패턴
```
1. project.db.reset_after(target_ep, commit=False)  ← DB 데이터 삭제
2. _clear_stage2_metadata() / _clear_narrative_summary_anchors()  ← 부가 데이터 삭제
3. _safe_commit()  ← 트랜잭션 커밋
4. 인메모리 상태 갱신 (project.arcs = [], volumes = [])
5. _delete_draft_files_from_episode()  ← 파일시스템 삭제
6. memory.delete_episodes_from()  ← 벡터 DB 삭제
7. _restore_runtime_state()  ← 런타임 객체 롤백
```

---

## 2. Findings

### [XC-ERR-016] P1 | 롤백 중 _safe_commit 실패 후 인메모리 상태와 DB 불일치

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-016 |
| Severity | P1 |
| 현상 요약 | `reset_stage_2()`에서 `_safe_commit()` 실패 시 DB는 롤백되지만, 직전의 DELETE 쿼리 결과가 불확정 상태이며, 이미 실행된 `project.arcs = []` 등 인메모리 변경이 복원되지 않음 |
| 코드 근거 | `project_service.py:184-214` |
| 영향 경계 | 프로젝트 전체 — DB/인메모리 불일치로 이후 모든 Stage 동작 불안정 |
| 테스트 근거 | `test_project_service.py` — commit 실패 경로 테스트 있으나 인메모리 상태 검증은 제한적 |
| 기존 중복 여부 | MRL-T4 (commit-rollback-recovery-contract)와 부분 중첩 |
| 권장 후속 조치 | 인메모리 상태 변경을 commit 성공 후로 이동 (2h) |

**분석**: 현재 `reset_stage_2()` 흐름:
```python
# project_service.py:184-214
try:
    project.db.reset_after(1, commit=False)       # ① DB DELETE (미커밋)
    self._clear_stage2_metadata(project)           # ② 추가 DELETE
    self._clear_stage2_summary_anchors(project)    # ③ 추가 DELETE
    self._clear_narrative_summary_anchors(project)  # ④ 추가 DELETE
    project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")  # ⑤
    if not self._safe_commit():                    # ⑥ 커밋 시도
        self._ui.log("DB commit failed during Stage 2 reset")
        return False  # ← 여기서 반환, 그러나 ①-⑤의 DELETE가 이미 실행됨

    project.arcs = []  # ⑦ 인메모리 변경 (커밋 성공 후 — OK)
    ...
```

실제로 `project.arcs = []`는 커밋 성공 후에 실행되므로 이 부분은 양호. 그러나 `_safe_commit()` 실패 시:
- ①-⑤의 DELETE는 `conn`의 미커밋 트랜잭션에 남아있음
- `return False`만 하고 `conn.rollback()`을 호출하지 않음
- 다음 DB 작업 시 미커밋 DELETE가 여전히 유효

**실제 위험**: `_safe_commit()` 실패 후 `return False` 경로에서 `_rollback_open_transaction()`이 호출되지 않음. 단, 최외곽 `except Exception` 블록에서는 호출됨.

수정된 심각도: **P1** — `_safe_commit()` False 반환(예외 없이 실패) 시 미커밋 트랜잭션이 유령으로 남음.

---

### [XC-ERR-017] P2 | rewind_stage_2에서 동일한 commit 실패 → 미롤백 패턴

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-017 |
| Severity | P2 |
| 현상 요약 | `rewind_stage_2()`도 `_safe_commit()` 실패 시 `return False`만 반환하고 `_rollback_open_transaction()` 미호출 |
| 코드 근거 | `project_service.py:253-255` |
| 영향 경계 | XC-ERR-016과 동일 |
| 테스트 근거 | 제한적 |
| 기존 중복 여부 | XC-ERR-016 sister |
| 권장 후속 조치 | XC-ERR-016과 동일 패턴 수정 (1h) |

```python
# project_service.py:253-255
if not self._safe_commit():
    self._ui.log("DB commit failed during Stage 2 rewind")
    return False  # ← _rollback_open_transaction 미호출
```

---

### [XC-ERR-018] P2 | rollback_episode에서 동일한 commit 실패 → 미롤백 패턴

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-018 |
| Severity | P2 |
| 현상 요약 | `rollback_episode()`에서도 `_safe_commit()` 실패 시 동일 문제 |
| 코드 근거 | `project_service.py:344-346` |
| 영향 경계 | XC-ERR-016과 동일 |
| 테스트 근거 | 제한적 |
| 기존 중복 여부 | XC-ERR-016 sister |
| 권장 후속 조치 | XC-ERR-016과 동일 (1h) |

---

### [XC-ERR-019] P2 | _restore_runtime_state에서 EmotionTracker/StateDeltaTracker 롤백 실패 무보호

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-019 |
| Severity | P2 |
| 현상 요약 | `_restore_runtime_state()`에서 `emotion_tracker.rollback_to()`와 `state_delta_tracker.rollback_to()`가 try-except 없이 호출됨 — 예외 발생 시 이후 런타임 복원이 중단됨 |
| 코드 근거 | `project_service.py:84-92` |
| 영향 경계 | 롤백 후 런타임 상태 — emotion_tracker 실패 시 state_delta_tracker와 preset_registry 복원이 스킵 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | MRL-T4와 부분 중첩 |
| 권장 후속 조치 | try-except 추가 (WorldState/FactLedger와 동일 패턴 적용) (1h) |

```python
# project_service.py:84-92
if self._emotion_tracker_fn and callable(self._emotion_tracker_fn):
    tracker = self._emotion_tracker_fn()
    if tracker is not None and hasattr(tracker, "rollback_to"):
        tracker.rollback_to(target_ep)  # ← try-except 없음!

if self._state_delta_tracker_fn and callable(self._state_delta_tracker_fn):
    tracker = self._state_delta_tracker_fn()
    if tracker is not None and hasattr(tracker, "rollback_to"):
        tracker.rollback_to(target_ep)  # ← try-except 없음!
```

대조: WorldState(L72-75), FactLedger(L77-82), PresetRegistry(L94-98)는 모두 try-except로 보호됨.

---

### [XC-ERR-020] P2 | 파일시스템 삭제와 DB 커밋의 비원자성

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-020 |
| Severity | P2 |
| 현상 요약 | DB 커밋 성공 후 `_delete_draft_files_from_episode()`가 실행되므로, 파일 삭제 실패 시 DB는 롤백됐지만 파일은 남아있는 불일치 발생 |
| 코드 근거 | `project_service.py:198` (reset_stage_2), `project_service.py:266` (rewind), `project_service.py:352` (rollback) |
| 영향 경계 | 파일시스템/DB 불일치 — 저위험 (고아 파일은 무해) |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | MCP-T4와 부분 중첩 |
| 권장 후속 조치 | 현행 유지 — 고아 파일은 다음 실행 시 덮어씀 (0h) |

**분석**: 이는 본질적 트레이드오프. 파일 삭제를 DB 커밋 전에 하면, 커밋 실패 시 파일만 삭제된 역방향 불일치가 발생. 현재 순서(DB 커밋 → 파일 삭제)가 안전한 선택.

---

### [XC-ERR-021] P3 | VectorDB 삭제 실패가 완전 삼킴

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-021 |
| Severity | P3 |
| 현상 요약 | `memory.delete_episodes_from()` / `memory.delete_all_episodes()` 실패가 `except Exception` + UI 로그만으로 처리 — soft_failure 리포팅 없음 |
| 코드 근거 | `project_service.py:201-205`, `project_service.py:269-273`, `project_service.py:361-362`, `project_service.py:417-420` |
| 영향 경계 | 벡터 메모리 — 고아 임베딩이 남으면 이후 검색 품질 저하 가능 |
| 테스트 근거 | `# pragma: no cover - non-blocking UI path` 표시 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `report_soft_failure()` 추가 (0.5h) |

---

### [XC-ERR-022] P3 | _assert_rollback_invariants가 경고만 하고 조치 없음

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-022 |
| Severity | P3 |
| 현상 요약 | `_assert_rollback_invariants()`가 롤백 후 런타임 트래커의 불일치를 감지하지만 `logging.warning`만 — 자동 복구나 에러 발생 없음 |
| 코드 근거 | `project_service.py:374-396` |
| 영향 경계 | 롤백 후 런타임 상태 — 감지만 하고 교정하지 않음 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | MRL-T4와 관련 |
| 권장 후속 조치 | 불일치 감지 시 자동 재롤백 또는 UI 경고 (2h) |

---

### [XC-ERR-023] P3 | db_manager.reset_after 트랜잭션 실패 시 롤백 후 raise

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-023 |
| Severity | P3 (양호 — 정보성) |
| 현상 요약 | `db_manager.py:2332-2335`의 `reset_after()`는 실패 시 `conn.rollback()` + `raise`로 적절히 처리 |
| 코드 근거 | `db_manager.py:2332-2335` |
| 영향 경계 | N/A — 양호 패턴 |
| 테스트 근거 | 있음 |
| 기존 중복 여부 | N/A |
| 권장 후속 조치 | 없음 — 모범 사례 (0h) |

```python
# db_manager.py:2332-2335
except Exception as e:
    self.conn.rollback()
    logging.error("[B4-P1-4] reset_after(ep>=%s) 트랜잭션 실패 — rollback 수행: %s", target_ep, e)
    raise
```

---

## 3. 롤백 보상 매트릭스

| 구성요소 | 보상 방법 | 보호 여부 | 갭 |
|----------|----------|----------|-----|
| DB 데이터 (reset_after) | conn.rollback() | ✅ 양호 | - |
| DB 커밋 (safe_commit 실패) | _rollback_open_transaction | ⚠️ except 경로만 | **_safe_commit() False 경로 미보호** |
| 인메모리 arcs/volumes | 직접 할당 | ✅ 커밋 후 실행 | - |
| 파일시스템 drafts | unlink | ⚠️ 개별 OSError 로깅 | 비원자적 (수용 가능) |
| WorldState | rollback_to() | ✅ try-except | - |
| FactLedger | rollback_to() | ✅ try-except | - |
| EmotionTracker | rollback_to() | ❌ try-except 없음 | **XC-ERR-019** |
| StateDeltaTracker | rollback_to() | ❌ try-except 없음 | **XC-ERR-019** |
| PresetRegistry | restorer() | ✅ try-except | - |
| VectorDB | delete_episodes_from() | ⚠️ UI 로그만 | soft_failure 미리포팅 |

---

## 4. Pass 3 최종 판정

| Finding | Pass 1 | Pass 2 | Pass 3 최종 |
|---------|--------|--------|------------|
| XC-ERR-016 | P0 HIGH | P1 — 인메모리 변경은 커밋 후 확인 | **P1** — _safe_commit False 경로 미롤백은 실재 |
| XC-ERR-017 | P1 HIGH | P2 — sister 패턴 | **P2** |
| XC-ERR-018 | P1 HIGH | P2 — sister 패턴 | **P2** |
| XC-ERR-019 | P1 HIGH | P2 — 비차단 트래커 | **P2** — 다른 트래커 보호와 비대칭 |
| XC-ERR-020 | P2 MED | P3 하향 | **P2** — 비원자성 자체는 수용 가능 |
| XC-ERR-021 | P3 LOW | P3 확인 | **P3** |
| XC-ERR-022 | P3 LOW | P3 확인 | **P3** |
| XC-ERR-023 | INFO | INFO | **P3 (양호)** |
