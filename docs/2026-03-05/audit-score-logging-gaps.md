# Score Logging 감사 보고서

> 작성: 2026-03-05
> 계기: Stage 3 `stage_attempts.score` 전부 0 발견 → 전 스테이지 확장 감사

---

## 요약

| Stage | PASS_WITH_FIX 흐름 | stage_attempts score | 기타 로그 score |
|-------|-------------------|---------------------|----------------|
| Stage 2 | ✅ 정상 | ✅ `audit.get("score")` 직접 참조 | — |
| Stage 3 | ✅ 정상 | ✅ **수정 완료** (S3-SCORE) | ⚠️ session_logger 0 고정 |
| Stage 4 | ✅ 정상 | ⚠️ PWF 재심사 전 원본 score | — |

기능 오작동: **없음**. 전부 기록 불일치.

---

## 수정 완료 — S3-SCORE (2026-03-05)

### 원인
`three_phase_blueprint_generator.py` 정상 PASS 경로에서
`pipeline_result["last_score"]`가 미설정 (긴급 폴백 L653에서만 세팅).

`stage3_orchestrator.py`의 `save_stage_attempt`가 `last_score`만 참조
→ `stage_attempts.score` 항상 0.

### 수정
- `three_phase_blueprint_generator.py` L443: PASS 분기에 `pipeline_result["last_score"] = _score` 추가 (근본 수정)
- `stage3_orchestrator.py` L733/L1014: `phases.generate.selected_score` 폴백 추가 (방어)

### 검증
테스트 기준선: 3,387 → **3,390 passed**, ruff 0 violations.

---

## 잔여 갭 (기록 불일치, 기능 무관)

### GAP-1: Stage 3 session_logger score=0

**위치**: `stage3_orchestrator.py` L720, L1001

```python
# PASS 경로 L720, REJECT 경로 L1001 — 둘 다 동일
score=pipeline_result.get("last_score", 0)  # phases 폴백 없음 → 0
```

`stage_attempts` DB는 수정됐으나 `session_logger.log_decision`(→ `decisions.jsonl`)은 미수정.

**영향**: `decisions.jsonl`의 stage3 score 필드가 0. `stage_attempts` DB를 주로 활용하므로 실질 영향 없음.

**수정법 (2줄)**: L720, L1001의 `pipeline_result.get("last_score", 0)` →
`pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)`

**우선순위**: P2 — 스킵. Stage 4 데이터 축적 후 일괄 정리.

---

### GAP-2: Stage 4 PASS_WITH_FIX 재심사 후 score 불일치

**흐름**:
```
Director 판정 → score=91 (PASS_WITH_FIX)
  → _execute_pass_with_fix_loop
    → inplace patch → 재심사 → score=95 (PASS)
  → 반환: (verdict, manuscript, state_updates, director_result, director_feedback)
     ↑ score 미포함
→ run()의 score 변수 = 원본 91 그대로
→ save_stage_attempt(score=91)  ← 재심사 95 아님
```

**위치**: `stage4_interview_round.py`
- `_execute_pass_with_fix_loop()` 반환 튜플에 score 없음
- `_InterviewRoundResult` dataclass에 score 필드 없음
- run() L639 `score = director_result.get("score", 0)` 이후 갱신 경로 없음

**영향**: `stage_attempts.score`가 재심사 전 원본값. 실제 합격 원고의 최종 점수와 수 점 차이날 수 있음.

**수정법**:
1. `_execute_pass_with_fix_loop` 반환 튜플에 `_re_s` (재심사 score) 추가
2. 호출부에서 `score` 갱신
3. 또는 `_InterviewRoundResult`에 `score: int = 0` 필드 추가

**우선순위**: P2 — 스킵. Stage 4 데이터가 쌓이면 실제 차이 확인 후 판단.

---

## 참고: 각 스테이지 score 소스

| Stage | save_stage_attempt score 소스 | 신뢰도 |
|-------|------------------------------|--------|
| Stage 2 | `audit.get("score", 0)` — Director audit dict 직접 | ✅ 높음 |
| Stage 3 | `pipeline_result.get("last_score") or phases.generate.selected_score` | ✅ 수정 후 정상 |
| Stage 4 | `score` (run() 지역변수, Director 1차 판정값) | ⚠️ PWF 재심사 시 원본 |

## 참고: Stage 4 PASS_WITH_FIX 흐름 정상 확인 항목

- `_execute_pass_with_fix_loop` inplace patch → `select_and_judge_ensemble` 재심사 ✅
- fix_scope `partial/full` → break → retry 루프 위임 ✅
- PF-3: PASS_WITH_FIX 3회 소진 시 마지막 패치본 채택 (REJECT 패치본은 채택 안 함) ✅
- SCM 단일 후보 경고 + score≥95→90 보정 — 재심사 시도 트리거됨 (의도된 동작) ✅
- `duration_ms`: `_round_start_ts` 기준 정상 계측 ✅
