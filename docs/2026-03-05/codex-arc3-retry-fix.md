# Codex Order: ARC-RETRY — Stage2 Arc 재시도 루프 버그 수정

**작업 ID**: ARC-RETRY
**우선순위**: P0 (Director REJECT 시 재시도가 전혀 안 됨)
**영향 범위**: Stage 2 Arc 설계 전체 (FourPhase 경로)

---

## 버그 요약

Director가 Arc를 REJECT해도 재시도 없이 즉시 "최종 설계 실패"로 종료됨.
`max_attempts=10`이지만 실제로 1회만 시도됨.

실증 로그:
```
[V60.77] FourPhase-Director 대면 1/5
→ Director audit: REJECT (score=66, 3/3 votes)
→ [V60.77] Director 피드백 → FourPhase 전달 2/5   ← 2회차 피드백 세팅
→ [Critical] Arc 3 최종 설계 실패.               ← 재시도 없이 종료
```

---

## 원인 분석

### `modules/core/stage2_finalizer.py` — L1053 (근본 원인)

Director REJECT 처리 마지막에 `"action": "next"` 반환:

```python
return {
    "action": "next",           # ← 문제: "retry"여야 함
    "last_refined_context": last_refined_context,
    "current_ep_start": current_ep_start,
    "current_feedback": current_feedback,
    "director_feedback_for_fourphase": director_feedback_for_fourphase,
    "st_snapshot": st_snapshot,
    ...
}
```

### `modules/core/stage2_orchestrator.py` — L651

```python
elif _fin["action"] == "next":
    break   # ← "next"를 받으면 즉시 루프 탈출 → 재시도 없음
```

---

## 수정 명세

### 수정 1 — `modules/core/stage2_finalizer.py`

Director REJECT 경로 맨 끝 return의 `"next"` → `"retry"` 로 변경.

**변경 전** (약 L1053):
```python
        return {
            "action": "next",
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
```

**변경 후**:
```python
        return {
            "action": "retry",
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
```

`"next"` 반환은 이 코드 경로 외에 없음 — 변경 영향 범위 최소.

### 수정 2 — `modules/core/stage2_orchestrator.py` (방어 코드)

`"next"` action이 혹시라도 다른 경로에서 발생할 경우를 대비해
break 대신 attempt 증가 후 continue로 변경.

**변경 전** (L651):
```python
                    elif _fin["action"] == "next":
                        break
```

**변경 후**:
```python
                    elif _fin["action"] == "next":
                        attempt += 1
                        continue
```

---

## 테스트 명세

`tests/test_arc_retry.py` (신규 또는 기존 적합 파일에 추가):

```python
# TC-RETRY-1: Director REJECT → finalizer가 "retry" 반환하는지 확인
def test_finalizer_returns_retry_on_director_reject():
    """Director REJECT 시 action='retry' 반환 확인."""
    from modules.core.stage2_finalizer import Stage2Finalizer
    # finalizer의 _handle_director_reject 또는 run_finalize 내부에서
    # Director REJECT 시 반환값 action이 "retry"인지 검증
    # Mock Director → REJECT 결과 주입 → action 확인
    ...
    assert result["action"] == "retry"

# TC-RETRY-2: "next" action이 orchestrator에서 loop break 대신 continue하는지 확인
def test_orchestrator_next_action_does_not_break_loop():
    """action='next' 수신 시 루프가 계속되는지 확인."""
    ...
```

---

## 감리 포인트

1. `pytest tests/ -q` → **3,370 passed** (기준선 유지)
2. `ruff check modules/` → 0 violations
3. `stage2_finalizer.py` 내 `"action": "next"` 잔존 여부 확인:
   ```
   grep -n '"action": "next"' modules/core/stage2_finalizer.py
   ```
   → 0건이어야 함
4. `stage2_orchestrator.py` L651 근방: `break` 제거 확인

---

## 주의: LOG-EMOJI 패치 진행 중

`LOG-EMOJI` 패치(codex-log-emoji-strip.md)가 병행 작업 중.
해당 파일들의 `logging.*()` 호출에서 이모지가 제거된 상태일 수 있음.

**신규 코드 작성 시**: `logging.*()` 호출에 이모지 사용 금지.
ASCII 태그(`[OK]`, `[FAIL]`, `[WARN]` 등)만 사용.

---

## 스코프 외

- NS-1 FourPhase 산술 자기검증 추가 — 이번 스코프 제외.
  Director가 이미 잡고 있고 (Arc 3 REJECT 정상 동작),
  **재시도만 작동하면 Director 피드백으로 수정됨**.
  별도 오더 필요 시 추후 작성.
