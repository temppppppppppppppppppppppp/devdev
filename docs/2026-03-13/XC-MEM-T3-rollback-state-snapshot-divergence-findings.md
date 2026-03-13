# XC-MEM-T3: 롤백 중 상태 스냅샷 분기 — 상세 분석

> 날짜: 2026-03-13
> Track: XC-MEM / Target: T3
> 대상: `modules/core/services/project_service.py`, `modules/core/world_state.py`, `modules/core/fact_ledger.py`

---

## 1. 분석 범위

`ProjectService._restore_runtime_state()`에서 `world_state`와 `fact_ledger`가 독립적으로 롤백될 때, 한쪽만 실패하여 두 상태가 어긋나는(divergence) 시나리오를 검사한다.

---

## 2. 코드 증거

### 2.1 _restore_runtime_state() 전문

```python
# project_service.py:63-98
def _restore_runtime_state(self, target_ep: int) -> None:
    project = self._project_fn()
    if hasattr(project, "_load_from_db"):
        project._load_from_db()
    if self._invalidate_tracker:
        self._invalidate_tracker()

    world_state = self._world_state_fn() if self._world_state_fn else None
    if world_state is not None and hasattr(world_state, "rollback_to"):
        try:
            world_state.rollback_to(target_ep)              # (A)
        except Exception as exc:
            self._ui.log(f"   [WorldState] rollback_to failed: {exc}")

    fact_ledger = self._fact_ledger_fn() if self._fact_ledger_fn else None
    if fact_ledger is not None and hasattr(fact_ledger, "rollback_to"):
        try:
            fact_ledger.rollback_to(target_ep)              # (B)
        except Exception as exc:
            self._ui.log(f"   [FactLedger] rollback_to failed: {exc}")

    # emotion_tracker, state_delta_tracker, preset_registry도 동일 패턴
```

**(A)가 성공하고 (B)가 실패하면**, world_state는 `target_ep` 이전 상태로 복원되었으나, fact_ledger는 이전(롤백 전) 상태를 유지한다.

### 2.2 rollback_to() 실패 경로 분석

**WorldStateManager.rollback_to()** (`world_state.py:1133-1174`):
```python
def rollback_to(self, target_ep: int) -> None:
    self._state = json.loads(json.dumps(self._INIT_STATE, ensure_ascii=False))  # 초기화
    try:
        all_bibles = self.db.get_all_episode_bibles()       # DB 조회
    except Exception as e:
        all_bibles = None                                    # 폴백
    if all_bibles is not None:
        for bible in all_bibles:
            ep = bible.get("ep_num", 0)
            if ep >= target_ep:
                break
            sc = bible.get("state_changes", {})
            if sc:
                self.update_from_state_changes(ep, sc)       # 리플레이
    ...
    self.save()                                              # DB 저장
```

**FactLedger.rollback_to()** (`fact_ledger.py:686-729`):
```python
def rollback_to(self, target_ep: int) -> None:
    self._ledger = self._empty_ledger()                      # 초기화
    try:
        all_bibles = self.db.get_all_episode_bibles()        # 동일 DB 조회
    except Exception as e:
        all_bibles = None
    if all_bibles is not None:
        for bible in all_bibles:
            ep = bible.get("ep_num", 0)
            if ep >= target_ep:
                break
            sc = bible.get("state_changes", {})
            if sc:
                self.update_from_state_changes(ep, sc)       # 리플레이
            self.update_from_bible_delta(ep, bible)           # 추가: bible delta
    ...
    self.save()                                              # DB 저장
```

### 2.3 분기 시나리오

두 메서드 모두 동일한 `self.db.get_all_episode_bibles()` DB 호출을 사용한다. 그러나 실패 지점이 다를 수 있다:

| 시나리오 | WorldState | FactLedger | 결과 |
|----------|-----------|------------|------|
| 정상 | 성공 | 성공 | 동기화 |
| DB 조회 실패 | 폴백(개별 조회) | 폴백(개별 조회) | 동기화 (동일 DB) |
| WS 리플레이 중 예외 | 부분 리플레이 + save | 정상 | **분기** |
| FL 리플레이 중 예외 | 정상 | 부분 리플레이 + save | **분기** |
| WS save 실패 | 메모리 복원 O, DB 미반영 | 정상 | **분기** (재시작 시 복원) |

### 2.4 리플레이 중 예외 가능성

WorldState의 `update_from_state_changes()` (L110-500+)는 섹션별 `try/except`로 래핑되어 있어 개별 섹션 실패가 전체를 중단시키지 않는다. 하지만 `json.loads()` 호출 중 깨진 데이터가 있으면 `_load_or_init()`에서 예외가 발생할 수 있다.

FactLedger의 `update_from_state_changes()`는 별도의 섹션별 `try/except` 없이 단일 흐름이므로, 중간 항목에서 예외 발생 시 나머지 항목이 처리되지 않는다.

### 2.5 DB 커밋 타이밍

`_restore_runtime_state()`는 `project_service.py`의 각 파괴적 연산 내부에서 **DB 커밋 이후**에 호출된다:

```python
# project_service.py:312-364 (rollback_episode)
    project.db.reset_after(target_ep, commit=False)
    ...
    if not self._safe_commit():                    # DB 커밋
        return False
    ...
    self._restore_runtime_state(target_ep)         # 커밋 후 호출
```

따라서 `_restore_runtime_state()`가 실패해도 DB 레벨의 롤백은 이미 완료된 상태이다. 문제는 **인메모리 상태**만의 불일치이며, 앱 재시작 시 DB에서 재로드하면 정합성이 복원된다.

---

## 3. Finding

### [XC-MEM-T3-001] P2 | world_state/fact_ledger 독립 롤백 시 부분 실패 허용

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-001 |
| Severity | P2 |
| 현상 요약 | `_restore_runtime_state()`에서 world_state와 fact_ledger의 `rollback_to()`가 독립 `try/except`로 실행되어, 한쪽만 실패 시 인메모리 상태가 어긋남. 다음 에피소드 생산 시 모순 데이터가 advisory에 전달될 수 있음 |
| 코드 근거 | `project_service.py:70-82` — `world_state.rollback_to()`와 `fact_ledger.rollback_to()` 각각 독립 `try/except`. 실패해도 호출자(`rollback_episode` 등)는 `True` 반환 |
| 영향 경계 | Stage 4 advisory 체인 (TruthGate가 world_state 참조, NumericDriftAdvisor가 fact_ledger 참조). 앱 재시작 시 자동 복구 |
| 테스트 근거 | `tests/test_project_service.py`는 정상 롤백만 검증. world_state 성공 + fact_ledger 실패 시나리오 테스트 없음 |
| 기존 중복 여부 | `MRL-T4-commit-rollback-recovery-contract-findings.md:69`에서 "rollback 실패 시 app cache와 DB 어긋남" 지적 있음. **동일 영역이나 world_state/fact_ledger 분기 구체화는 신규** |
| 권장 후속 조치 | (1) `_restore_runtime_state()`에서 한쪽 실패 시 양쪽 모두 재초기화(INIT_STATE) 적용 (1h). (2) 또는 실패 시 반환값을 caller에 전달하여 경고 표시 (0.5h) |

### [XC-MEM-T3-002] P2 | _restore_runtime_state() 실패가 파괴적 연산 성공으로 보고

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-002 |
| Severity | P2 |
| 현상 요약 | `_restore_runtime_state()` 내부의 모든 예외가 UI 로그만 찍고 무시됨. 호출자(`rollback_episode` 등)는 이미 `True`를 반환하기 직전이므로, 사용자는 성공으로 인식하나 인메모리 상태는 불완전 |
| 코드 근거 | `project_service.py:70-98` — 5개 tracker 각각의 `try/except`가 `self._ui.log()`만 호출하고 예외를 삼킴. `rollback_episode()` L364에서 `_restore_runtime_state(target_ep)` 호출 직후 L365 "Success" 로그 |
| 영향 경계 | 사용자 인식과 실제 상태의 불일치. `_assert_rollback_invariants()` (L374-396)가 emotion_tracker와 state_delta_tracker만 검증하고 world_state/fact_ledger는 검증하지 않음 |
| 테스트 근거 | `_assert_rollback_invariants()` 테스트 없음 |
| 기존 중복 여부 | `MRL-T4-commit-rollback-recovery-contract-findings.md:84`에서 "post-commit recovery helper 예외가 cache invalidation을 건너뛰게 한다" 지적. 본 finding은 구체적으로 world_state/fact_ledger 범위를 특정 |
| 권장 후속 조치 | `_assert_rollback_invariants()`에 world_state/fact_ledger `last_updated_ep` 검증 추가 (1h) |

### [XC-MEM-T3-003] P3 | episode_bibles 리플레이 중 섹션별 에러 핸들링 비대칭

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-003 |
| Severity | P3 |
| 현상 요약 | WorldState의 `update_from_state_changes()`는 섹션별 `try/except`로 부분 실패를 허용하나, FactLedger의 동일 메서드는 단일 흐름이어서 중간 실패 시 나머지가 처리되지 않음. 롤백 리플레이 시 두 시스템의 데이터 범위가 달라질 수 있음 |
| 코드 근거 | `world_state.py:158-500+` — 8개 섹션 각각 독립 `try/except`. `fact_ledger.py:129-400+` — 섹션별 `try/except` 유무 확인 필요하나 구조가 다름 |
| 영향 경계 | 롤백 리플레이 정합성 |
| 테스트 근거 | 리플레이 중 부분 실패 시나리오 테스트 없음 |
| 기존 중복 여부 | 기존 finding에 동일 지적 없음 |
| 권장 후속 조치 | FactLedger.update_from_state_changes()에 섹션별 try/except 추가하여 WorldState와 동일한 에러 복원력 확보 (2h) |

---

## 4. 종합 판정

T3 영역의 핵심 위험은 **부분 롤백 실패가 silent하게 허용되는 구조**이다. DB 레벨의 롤백은 `_safe_commit()` 이전에 완료되므로 데이터 손실은 없으나, 인메모리 상태의 불일치가 다음 에피소드 생산에 전파될 수 있다. 앱 재시작이 자연적 복구 메커니즘이지만, 사용자가 롤백 후 바로 생산을 이어가면 문제 발생 가능.
