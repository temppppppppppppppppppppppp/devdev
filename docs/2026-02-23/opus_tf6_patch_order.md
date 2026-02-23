# TF-6 Patch Order — 16건 확정 패치

> **작성**: Opus TF (2026-02-23)
> **실행**: Codex
> **베이스라인**: 2,377 passed, ruff 0 violations, commit `5e7f7c0`
> **감리 결과**: 18건 보고 → 16건 CONFIRMED, 2건 FALSE POSITIVE (TF-C-1, TF-F-1 제외)

---

## Codex 실행 규칙 (필독)

### 핵심 원칙
- **수동 중단 절대 금지** — #1부터 #16까지 전량 완료 후 최종 테스트까지 한 번에 끝낸다
- **중간 보고 금지** — 사용자에게 중간 보고 없이 끝까지 진행
- **인코딩**: 모든 파일 I/O는 **UTF-8**, 한글 깨짐 절대 금지
- **각 패치 후** `pytest tests/ -q` 회귀 확인 (2,377+ passed 유지)
- **5개 패치마다** 체크포인트(CP) 기록 → 진행 테이블 + CP 섹션 업데이트

### 컨텍스트 컴팩트 복구 절차
1. 이 문서(`docs/2026-02-23/opus_tf6_patch_order.md`)를 처음부터 다시 읽는다
2. 진행 테이블에서 마지막 ✅ 패치를 확인한다
3. 그 다음 미완료 패치부터 이어서 진행한다
4. **절대 처음부터 다시 시작하지 않는다**

### 금지 사항
- FALSE POSITIVE 2건(TF-C-1, TF-F-1) 수정 금지
- 패치 범위 밖 코드 변경 금지
- git push 금지 (커밋만 허용)

---

## 진행 테이블

| # | ID | 심각도 | 파일 | 상태 |
|---|-----|--------|------|------|
| 1 | TF-A-1 | HIGH | project_service.py | ✅ |
| 2 | TF-E-1 | HIGH | stage2_validation_pipeline.py | ✅ |
| 3 | TF-A-2 | MEDIUM | vec_memory.py | ✅ |
| 4 | TF-A-3 | MEDIUM | project_service.py | ✅ |
| 5 | TF-C-2 | MEDIUM | db_manager.py | ✅ |
| 6 | TF-D-1 | MEDIUM | base_agent.py | ✅ |
| 7 | TF-B-1 | MEDIUM | state_tracker.py + state_tracker_plots.py | ✅ |
| 8 | TF-B-2 | MEDIUM | db_manager.py | ✅ |
| 9 | TF-B-3 | MEDIUM | data_collector.py | ✅ |
| 10 | TF-G-1 | MEDIUM | stage4_interview_round.py | ✅ |
| 11 | TF-G-2 | MEDIUM | stage2_validation_pipeline.py | ✅ |
| 12 | TF-G-3 | MEDIUM | scoring_validator.py | ✅ |
| 13 | TF-G-4 | MEDIUM | base_agent.py | ✅ |
| 14 | TF-H-1 | MEDIUM | _ag_deep.py, _ag_scan.py, _scan_modules.py | ✅ |
| 15 | TF-H-2 | MEDIUM | check_blocks.py | ✅ |
| 16 | TF-H-3 | MEDIUM | tools2/apply_v3.py, tools2/automate_snack.py | ✅ |

---

## 체크포인트

| CP | 패치 범위 | 테스트 결과 | 완료 시각 |
|----|----------|------------|----------|
| CP-1 | #1 ~ #5 | pytest 2377 passed, ruff check/format 통과 | 2026-02-23 10:28:47 |
| CP-2 | #6 ~ #10 | pytest 2377 passed, ruff check/format 통과 | 2026-02-23 10:33:36 |
| CP-3 | #11 ~ #16 | pytest 2377 passed, ruff check/format 통과 | 2026-02-23 10:37:23 |

---

## P0: CRITICAL PATH (2건)

### #1. TF-A-1 — HUD 인메모리 선반영 방지 (HIGH)

**파일**: `modules/core/services/project_service.py`
**줄**: L144-152, L188

**문제**: `project.master_bible = bible_data` (L152)가 `_safe_commit()` (L188) 이전에 실행됨. 커밋 실패 시 인메모리 HUD가 DB와 불일치.

**현재 코드** (L143-152):
```python
                                if hud_key in bible_data["MasterBible"]:
                                    bible_data["MasterBible"][hud_key].setdefault("Protagonist", {})["actual_truth"] = (
                                        past_actual
                                    )
                                project.db.cursor.execute(
                                    "UPDATE anchors SET data = ? WHERE key = 'bible'",
                                    (json.dumps(bible_data, ensure_ascii=False),),
                                )
                                self._ui.log(f"   📉 [Rollback] HUD를 {target_ep - 1}화 시점으로 복구했습니다.")
                                project.master_bible = bible_data
```

**수정**: `project.master_bible = bible_data`를 `_safe_commit()` 성공 후로 이동.

```python
                                if hud_key in bible_data["MasterBible"]:
                                    bible_data["MasterBible"][hud_key].setdefault("Protagonist", {})["actual_truth"] = (
                                        past_actual
                                    )
                                project.db.cursor.execute(
                                    "UPDATE anchors SET data = ? WHERE key = 'bible'",
                                    (json.dumps(bible_data, ensure_ascii=False),),
                                )
                                self._ui.log(f"   📉 [Rollback] HUD를 {target_ep - 1}화 시점으로 복구했습니다.")
                                _pending_bible = bible_data  # 커밋 성공 후 반영
```

그리고 L188 `_safe_commit()` 성공 후에 반영:

**현재** (L187-190):
```python
            # 커밋
            if not self._safe_commit():
                self._ui.log("❌ DB 커밋 실패 — 롤백 중단 (파일/벡터 보존)")
                return False
```

**수정** (L187-192):
```python
            # 커밋
            if not self._safe_commit():
                self._ui.log("❌ DB 커밋 실패 — 롤백 중단 (파일/벡터 보존)")
                return False

            # [TF-A-1] 커밋 성공 후에만 인메모리 HUD 반영
            if _pending_bible is not None:
                project.master_bible = _pending_bible
```

**주의**: `_pending_bible` 변수를 rollback_episode() 메서드 상단(try 블록 진입 직후)에서 `_pending_bible = None`으로 초기화할 것.

**테스트**: `_safe_commit()` Mock → False 반환 시 `project.master_bible` 불변 확인.

---

### #2. TF-E-1 — 단일 에피소드 아크 Flow Guard 차단 해제 (HIGH)

**파일**: `modules/core/stage2_validation_pipeline.py`
**줄**: L626

**문제**: `max(3, ep_count)` → ep_count=1이어도 최소 3비트 강제. 의도적 단화/브리지 아크 차단.

**현재 코드** (L626):
```python
        if not isinstance(beats, list) or len(beats) < max(3, ep_count):
```

**수정**:
```python
        _min_beats = max(1, ep_count)  # [TF-E-1] 단일 에피소드 아크 허용
        if not isinstance(beats, list) or len(beats) < _min_beats:
```

**테스트**: `ep_count=1, beat_sequence=["단일 비트 내용을 충분히 길게 작성"]` → PASS 확인. 기존 테스트(`test_reject_insufficient_beats`)도 회귀 확인.

---

## P1: SHORT-TERM (4건)

### #3. TF-A-2 — VecMemory 삭제 예외 시 명시적 rollback (MEDIUM)

**파일**: `modules/core/vec_memory.py`
**줄**: L896-898

**현재 코드**:
```python
            except Exception as e:
                self._ui_log(f"[VecMemory] delete episodes failed (>={target_ep}): {e}")
                return 0
```

**수정**:
```python
            except Exception as e:
                # [TF-A-2] 명시적 rollback — memorize_v20_episode 관례와 통일
                try:
                    self._conn.rollback()
                except Exception:
                    pass
                self._ui_log(f"[VecMemory] delete episodes failed (>={target_ep}): {e}")
                return 0
```

**테스트**: DELETE 중 예외 강제 발생 → rollback 호출 확인 + 데이터 무변경 검증.

---

### #4. TF-A-3 — StateTracker 무효화를 서비스 레이어로 이전 (MEDIUM)

**파일**: `modules/core/services/project_service.py`
**줄**: L214 근처

**문제**: StateTracker 무효화가 main_a.py에만 의존. 서비스 직접 호출 시 stale 상태 잔존.

**현재 코드** (L213-214):
```python
            project._load_from_db()
```

**수정**: `rollback_episode()`에 콜백 주입 또는 반환값에 무효화 플래그 추가. 가장 간단한 방법은 생성자에 tracker 무효화 콜백을 받는 것:

project_service.py `__init__`에 `state_tracker_invalidator` 콜백 추가:
```python
def __init__(self, ..., state_tracker_invalidator=None):
    ...
    self._invalidate_tracker = state_tracker_invalidator
```

rollback_episode() L214 바로 뒤:
```python
            project._load_from_db()
            # [TF-A-3] StateTracker 무효화 — 호출부 무관하게 보장
            if self._invalidate_tracker:
                self._invalidate_tracker()
```

main_a.py에서 ProjectService 생성 시 콜백 전달:
```python
self._project_service = ProjectService(
    ...,
    state_tracker_invalidator=lambda: setattr(self, 'state_tracker', None),
)
```

main_a.py의 기존 `self.state_tracker = None` (L2783)은 제거하거나, 중복 방어로 유지해도 무방.

**테스트**: ProjectService.rollback_episode() 직접 호출 → 콜백 호출 확인.

---

### #5. TF-C-2 — transaction() 컨텍스트매니저 _lock 보호 (MEDIUM)

**파일**: `modules/core/db_manager.py`
**줄**: L1440-1472

**현재 코드** (L1440-1448):
```python
    @contextmanager
    def transaction(self) -> None:
        """[V44] 원자적 트랜잭션 보장 가드. 에러 타입별 롤백 및 세션 보호"""
        self._ensure_open()
        nested = self.conn.in_transaction
        try:
            if not nested:
                self.cursor.execute("BEGIN TRANSACTION")
            yield
```

**수정**:
```python
    @contextmanager
    def transaction(self) -> None:
        """[V44] 원자적 트랜잭션 보장 가드. 에러 타입별 롤백 및 세션 보호"""
        self._ensure_open()
        self._lock.acquire()  # [TF-C-2] begin/commit/rollback과 동일한 lock 보호
        nested = self.conn.in_transaction
        try:
            if not nested:
                self.cursor.execute("BEGIN TRANSACTION")
            yield
```

그리고 메서드 끝에 finally 추가 (기존 except 블록들 뒤):
```python
        except Exception as e:
            if not nested:
                self.conn.rollback()
            logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 트랜잭션 오류 - 롤백 수행: {e}")
            logging.info(f"→ 상세: {traceback.format_exc()[:300]}")
            raise DBError(str(e), original_error=e) from e
        finally:
            self._lock.release()  # [TF-C-2] lock 해제 보장
```

**테스트**: 다중 스레드 `with db.transaction()` 경쟁 쓰기 → 데이터 무결성 검증.

---

### #6. TF-D-1 — backup 응답 검증 키셋 확장 (MEDIUM)

**파일**: `modules/domain/agents/base_agent.py`
**줄**: L896-900

**현재 코드**:
```python
        # 핵심 필드 존재 검사 (최소 하나)
        key_fields = ["content", "tactical_doc", "integrated_scenario", "title", "state_updates"]
        has_key_field = any(f'"{field}"' in response for field in key_fields)
        if not has_key_field:
            return {"valid": False, "reason": "핵심 필드 없음"}
```

**수정**:
```python
        # 핵심 필드 존재 검사 (최소 하나) — Writer + Director/Validator 모두 포함
        key_fields = [
            "content", "tactical_doc", "integrated_scenario", "title", "state_updates",  # Writer 계열
            "decision", "score", "reason", "feedback", "conflicts",  # Director/Validator 계열
            "scores", "corrected_content", "beat_sequence", "arc_no",  # Analyst/Critic/Corrector 계열
        ]
        has_key_field = any(f'"{field}"' in response for field in key_fields)
        if not has_key_field:
            return {"valid": False, "reason": "핵심 필드 없음"}
```

**테스트**: `{"decision": "PASS", "score": 85}` 형태 응답이 valid 반환하는지 확인.

---

## P2: MEDIUM-TERM (10건)

### #7. TF-B-1 — resolved_plots 크기 상한 (MEDIUM)

**파일**: `modules/domain/agents/state_tracker.py` + `modules/domain/agents/state_tracker_plots.py`

**수정 (state_tracker.py)**: `resolved_plots` 선언 근처에 상한 추가:
```python
self.resolved_plots: list[dict] = []
self._resolved_plots_max: int = 500  # [TF-B-1]
```

**수정 (state_tracker_plots.py)**: append 직후 에비싱:
```python
self.tracker.resolved_plots.append(entry)
# [TF-B-1] 상한 초과 시 오래된 항목 제거
_max = getattr(self.tracker, "_resolved_plots_max", 500)
if len(self.tracker.resolved_plots) > _max:
    self.tracker.resolved_plots = self.tracker.resolved_plots[-_max:]
```

**테스트**: 600개 삽입 → len() <= 500 확인.

---

### #8. TF-B-2 — all_reveals 누적 상한 (MEDIUM)

**파일**: `modules/core/db_manager.py`
**줄**: L900-901 근처

**현재 코드**:
```python
cumulative["all_reveals"].extend(reveals)
```

**수정**:
```python
cumulative["all_reveals"].extend(reveals)
# [TF-B-2] 최근 500건만 유지 (에피소드 순 누적이므로 tail 보존)
_REVEALS_MAX = 500
if len(cumulative["all_reveals"]) > _REVEALS_MAX:
    cumulative["all_reveals"] = cumulative["all_reveals"][-_REVEALS_MAX:]
```

**테스트**: 600개 reveal 누적 → len() <= 500 확인.

---

### #9. TF-B-3 — feedback_log 인메모리 상한 (MEDIUM)

**파일**: `modules/core/data_collector.py`
**줄**: L350, L383

**수정 (L350)**: 초기화 시 deque 사용:
```python
from collections import deque
...
self.feedback_log: deque = deque(maxlen=200)  # [TF-B-3]
```

**수정 (L383)**: append는 동일 (deque가 자동 에비싱).

**테스트**: 300개 append → len() == 200 확인.

---

### #10. TF-G-1 — Interview Round 하드코딩 외부화 (MEDIUM)

**파일**: `modules/core/stage4_interview_round.py`
**줄**: L475, L479, L488

**수정**:
```python
_DEFAULT_SLOT_MAX = int(_threshold("smart_retrieval.slot_max_chars_default", 1500))
_MAX_NPCS_PER_SLOT = int(_threshold("smart_retrieval.max_npcs_per_slot", 5))
...
# L475:
_slot_max = int(getattr(_slot, "max_chars", 0) or 0) or _DEFAULT_SLOT_MAX
# L479:
_slot_npcs = _npc_roster[:_MAX_NPCS_PER_SLOT]
# L488:
if len(_slot_npcs) >= _MAX_NPCS_PER_SLOT:
```

**테스트**: validation.yaml에 값 설정 → 반영 확인.

---

### #11. TF-G-2 — Flow Guard 임계값 외부화 (MEDIUM)

**파일**: `modules/core/stage2_validation_pipeline.py`
**줄**: L626, L652, L688, L720

**수정**: 메서드 상단에서 `_threshold()` import 후 사용:
```python
from modules.validation.threshold_helper import _threshold
...
_MIN_BEATS_FLOOR = int(_threshold("scope.min_beats_floor", 1))
_MIN_AVG_WORDS = int(_threshold("scope.min_avg_words", 6))
_MIN_WORD_PER_BEAT = int(_threshold("scope.min_word_per_beat", 4))
_MIN_DIVERSITY = float(_threshold("scope.min_diversity", 0.6))
_MAX_STAGNATION = int(_threshold("scope.max_stagnation_hits", 3))
```

각 하드코딩 위치를 변수로 교체.

**주의**: `_MIN_BEATS_FLOOR`의 기본값은 `1`로 설정 (#2 TF-E-1 패치와 연동). 기존 `max(3, ep_count)` → `max(_MIN_BEATS_FLOOR, ep_count)`.

**테스트**: 기존 flow_guard 테스트 회귀 + yaml 변경 시 동작 변화 확인.

---

### #12. TF-G-3 — ScoringValidator 임계값 외부화 (MEDIUM)

**파일**: `modules/validation/scoring_validator.py`
**줄**: L107, L470, L473, L1108, L1121

**수정**: 모듈 상단 또는 클래스 초기화에서:
```python
_SANITIZE_MAX_CHARS = int(_threshold("scoring.sanitize_max_chars", 3000))
_CV_OPTIMAL_LOW = float(_threshold("scoring.cv_optimal_low", 0.35))
_CV_OPTIMAL_HIGH = float(_threshold("scoring.cv_optimal_high", 0.55))
_WUXIA_MARTIAL_MIN = int(_threshold("scoring.wuxia_martial_min", 3))
_HUNTER_SYSTEM_MIN = int(_threshold("scoring.hunter_system_min", 5))
```

각 하드코딩 위치를 변수로 교체.

**테스트**: 기존 scoring 테스트 회귀 확인.

---

### #13. TF-G-4 — BaseAgent 캐시/안전 상수 외부화 (MEDIUM)

**파일**: `modules/domain/agents/base_agent.py`
**줄**: L959, L1034, L1035, L1138, L1184

**수정**: `_SYSTEM_CFG` 활용 (이미 import됨):
```python
# L959:
_MAX_JSON_PAYLOAD = int(_SYSTEM_CFG.get("retry", {}).get("max_json_payload", 500_000))
# L1138:
_CONTEXT_CACHE_MAX = int(_SYSTEM_CFG.get("cache", {}).get("context_max_entries", 50))
# L1184:
_MIN_CACHE_CONTENT = int(_SYSTEM_CFG.get("cache", {}).get("min_content_chars", 50000))
```

L1034/L1035 (`MAX_DEPTH=20`, `_MAX_VISITS=100`)는 JSON 파서 내부 안전장치이므로 외부화보다 주석 강화로 충분:
```python
MAX_DEPTH = 20   # JSON 중첩 깊이 한계 (보안)
_MAX_VISITS = 100  # JSON 노드 방문 한계 (무한루프 방지)
```

**테스트**: system.yaml에 값 설정 → 반영 확인.

---

### #14. TF-H-1 — 루트 임시 스크립트 삭제 (MEDIUM)

**파일**: `_ag_deep.py`, `_ag_scan.py`, `_scan_modules.py`

**수정**: 3개 파일 삭제. 프로덕션 코드에서 import 없음 확인 완료 (감리에서 검증).

```bash
git rm _ag_deep.py _ag_scan.py _scan_modules.py
```

**테스트**: `pytest tests/ -q` 회귀 확인.

---

### #15. TF-H-2 — check_blocks.py 삭제 (MEDIUM)

**파일**: `check_blocks.py`

**수정**: 삭제. 6줄짜리 1회성 스크립트, 특정 데이터 파일에 하드코딩 의존.

```bash
git rm check_blocks.py
```

**테스트**: `pytest tests/ -q` 회귀 확인.

---

### #16. TF-H-3 — tools2 스크립트 절대경로 상대화 + 안전장치 (MEDIUM)

**파일**: `tools2/apply_v3.py`, `tools2/apply_v3_pt2.py`, `tools2/automate_snack.py`

**수정**: 절대경로를 상대경로로 변환, 입출력 파일 분리.

apply_v3.py / apply_v3_pt2.py:
```python
# 변경 전:
# with open('c:/Users/PC/Desktop/글도비/treatments/...json', ...)
# 변경 후:
import sys
_INPUT = sys.argv[1] if len(sys.argv) > 1 else "treatments/골든루트_tr_block_ALL_v3_snack_5060.json"
_OUTPUT = sys.argv[2] if len(sys.argv) > 2 else _INPUT.replace(".json", "_patched.json")
```

automate_snack.py:
```python
# 변경 전:
# automate_snack_culture('...v2_snack.json', '...v2_snack.json')  # 입출력 동일
# 변경 후:
_src = sys.argv[1] if len(sys.argv) > 1 else "treatments/골든루트_tr_block_ALL_v2_snack.json"
_dst = sys.argv[2] if len(sys.argv) > 2 else _src.replace(".json", "_out.json")
automate_snack_culture(_src, _dst)
```

**테스트**: `pytest tests/ -q` 회귀 확인.

---

## 커밋 전략

```
CP-1 (#1~#5) 완료 후: pytest + ruff
CP-2 (#6~#10) 완료 후: pytest + ruff
CP-3 (#11~#16) 완료 후: pytest + ruff → 최종 커밋
```

**커밋 메시지**:
```
fix(tf6): 롤백 원자성·상태 누적·트랜잭션 안전성 등 16건 패치

- P0: HUD 선반영 방지, 단일에피소드 아크 허용
- P1: VecMemory 명시적 rollback, StateTracker 콜백, transaction() lock, backup 키셋 확장
- P2: 상태 누적 상한(3건), 임계값 외부화(4건), 데드코드 정리(3건)
```

## 검증

```bash
pytest tests/ -q
python -m ruff check modules/ tests/ main_a.py
python -m ruff format --check modules/ tests/ main_a.py
```
