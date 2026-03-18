# Stage 4 Director Facade Signature Drift — 9-Pass 감리 보고서

> **일시**: 2026-03-18
> **대상 에러**: `Director.select_and_judge_ensemble() got an unexpected keyword argument 'decision_core'`
> **영향**: Stage 4 원고 생산 전면 차단 (3회 연속 0화 생산)
> **코드 수정**: 금지 (조사 및 문서화만 수행)

---

## 1. 에러 요약

| 항목 | 내용 |
|------|------|
| **에러 유형** | Python TypeError (unexpected keyword argument) |
| **발생 위치** | `director.py:272` — Director.select_and_judge_ensemble() wrapper |
| **호출 원점** | `stage4_interview_round.py:2416-2432` |
| **발생 빈도** | Stage 4 진입 시 100% 재현 (3/3 Arc에서 동일 에러) |
| **영향 범위** | 모든 Stage 4 원고 생산 경로 차단 |

---

## 2. 근본 원인: Facade-Implementation Signature Drift

커밋 `f39e3fe8` (2026-03-17)에서 `director_ensemble.py`와 `stage4_interview_round.py`에 3개 파라미터가 추가되었으나, `director.py`의 facade wrapper가 동기화되지 않았다.

### 2.1 시그니처 비교

**director.py:272-286 (Facade wrapper) — 누락 3개**
```python
def select_and_judge_ensemble(
    self,
    ep_num,
    candidates,
    validation_results,
    blueprint,
    previous_ending,
    arc_pos=1,
    total_eps=5,
    retry_count=0,
    episode_digest="",
    mandatory_context="",
    prev_manuscripts_text="",
    story_context="",
):  # ← decision_core, candidate_evidence, reference_appendix 없음
```

**director_ensemble.py:1222-1239 (Implementation) — 존재**
```python
def select_and_judge_ensemble(
    self,
    ep_num: int,
    candidates: list,
    validation_results: list,
    blueprint: dict,
    previous_ending: str,
    arc_pos: int = 1,
    total_eps: int = 5,
    retry_count: int = 0,
    episode_digest: str = "",
    mandatory_context: str = "",
    decision_core: str = "",           # ← 존재
    candidate_evidence: str = "",      # ← 존재
    reference_appendix: str = "",      # ← 존재
    prev_manuscripts_text: str = "",
    story_context: str = "",
) -> dict:
```

### 2.2 호출 체인

```
stage4_interview_round.py:2416
  → self.ctx.agents["director"].select_and_judge_ensemble(
        ..., decision_core=..., candidate_evidence=..., reference_appendix=...)
  → director.py:272  ← TypeError 발생 (3개 파라미터 미정의)
  → director_ensemble.py:1222  ← 도달 불가
```

### 2.3 위임 호출도 미전달

`director.py:288-301`의 위임 호출에도 3개 파라미터가 전달되지 않음:
```python
return self._ensemble.select_and_judge_ensemble(
    ep_num, candidates, validation_results, blueprint, previous_ending,
    arc_pos, total_eps, retry_count, episode_digest,
    mandatory_context=mandatory_context,
    prev_manuscripts_text=prev_manuscripts_text,
    story_context=story_context,
    # ← decision_core, candidate_evidence, reference_appendix 미전달
)
```

---

## 3. 영향 범위 분석

### 3.1 에러 발생 경로

| 호출 위치 | 경로 | decision_core 전달 | 에러 발생 |
|-----------|------|-------------------|-----------|
| `stage4_interview_round.py:2416` | 1차 면담 (메인 생성) | **O** | **TypeError** |
| `stage4_interview_round.py:3728` | 재심사 (PASS_WITH_FIX) | X | 정상 |

- **1차 면담 경로**: 모든 원고 생성의 필수 통과 경로 → **전면 차단**
- **재심사 경로**: decision_core 미전달 → 에러는 없으나 기능 제약 (decision_core가 빈 문자열로 처리)

### 3.2 에러 처리 경로

1. `stage4_interview_round.py:2416` → TypeError 발생
2. InterviewRound.run()에 try-except 없음 → 상위 전파
3. `stage4_orchestrator.py:1706` → `🚨 Stage 4 V2 오류: {e}` 로깅
4. `main_a.py:4498-4512` → `✅ [Stage 4] 원고 완료 (0화 생산)` 출력
5. FrontierLag가 다음 Arc로 진행 → 동일 에러 반복

### 3.3 파이프라인 연쇄 영향

- Stage 2 (Arc 설계): 정상 — 3개 Arc 성공 (score 100/100/100)
- Stage 3 (Blueprint): 정상 — 11화 Blueprint 생성 완료
- **Stage 4 (원고 생산): 전면 차단 — 0화 생산**
- 비용: $6.19 소비 (162회 LLM 호출), 실질 산출물 0

---

## 4. 에러 미감지 원인 (테스트 커버리지 맹점)

### 4.1 테스트 분류

| 테스트 파일 | 호출 방식 | 버그 감지 |
|------------|----------|----------|
| `test_director_modules.py:1370` | `ensemble.select_and_judge_ensemble()` (직접, wrapper 우회) | **불가** |
| `test_director_modules.py:687` | `director.select_and_judge_ensemble()` (wrapper 경유, 3개 미전달) | **불가** |
| `test_stage4_interview_round.py:3336` | `ctx.agents["director"]` = **MagicMock** | **불가** |
| `test_a4_failure_pattern.py` | **MagicMock** | **불가** |
| `test_tf29_open_review.py` | **MagicMock** | **불가** |

### 4.2 맹점 요약

1. **Wrapper 경유 + 3개 파라미터 전달** 조합의 통합 테스트 부재
2. `test_stage4_interview_round.py`가 `ctx.agents["director"]`를 MagicMock으로 대체 → 실제 시그니처 검증 불가
3. `test_director_modules.py`의 facade 테스트가 decision_core를 전달하지 않음

---

## 5. 커밋 이력 추적

| 커밋 | 날짜 | 변경 내용 |
|------|------|----------|
| `f39e3fe8` | 2026-03-17 | director_ensemble.py, stage4_interview_round.py에 3개 파라미터 추가. **director.py 미수정** |

- `director_ensemble.py`: +220줄 (decision_core 파라미터 및 처리 로직 추가)
- `stage4_interview_round.py`: +694줄 (_director_input_packs 구성 및 호출부에 3개 파라미터 추가)
- `director.py`: **0줄 변경** (facade wrapper 미동기화)

---

## 6. 적대적 감리 결과 (반론 검증)

### 6.1 "동적 디스패치로 우회 가능" → **기각**
- Director 클래스에 `__getattr__`, `__call__`, 동적 메서드 디스패치 없음
- `**kwargs` catch-all 없음

### 6.2 "agents['director']가 Director가 아닐 수 있다" → **기각**
- `main_a.py:1754-1756`에서 `Director(...)` 인스턴스 직접 등록 확인

### 6.3 "런타임 monkey-patching 가능성" → **기각**
- `setattr`, 동적 메서드 교체 패턴 전무

### 6.4 "다른 Director 클래스일 수 있다" → **기각**
- 프로젝트 내 Director 클래스 2개, 활성 클래스는 `director.py:20`의 1개만

### 6.5 "Advisory 체인이 메서드를 수정" → **기각**
- Advisory 모듈은 데이터 반환만 수행, Director 메서드 수정 없음

### 6.6 "_director_input_packs KeyError 가능성" → **기각**
- `stage4_interview_round.py:2403-2407`에서 3개 키 명시적 초기화, KeyError 불가

---

## 7. 수정 방향 (참고용, 코드 수정 금지)

**수정 대상**: `modules/domain/agents/director.py:272-301`

**필요 변경**:
1. 시그니처에 `decision_core=""`, `candidate_evidence=""`, `reference_appendix=""` 추가
2. 위임 호출에 3개 파라미터 전달 추가

**필요 테스트 보강**:
- Director wrapper 경유 + 3개 파라미터 전달 통합 테스트 추가
- MagicMock 대신 실제 Director 인스턴스를 사용하는 시그니처 검증 테스트

---

## 8. 파일 인덱스

| 파일 | 역할 | 관련 라인 |
|------|------|----------|
| `modules/domain/agents/director.py` | Facade wrapper (**버그 위치**) | 272-301 |
| `modules/domain/agents/director_ensemble.py` | 실제 구현 (정상) | 1222-1239 |
| `modules/core/stage4_interview_round.py` | 호출부 (정상) | 2416-2432, 3728-3741 |
| `modules/core/stage4_orchestrator.py` | 에러 catch & 로깅 | 1705-1706 |
| `main_a.py` | Director 인스턴스 등록 | 1754-1756 |
| `config/prompts/director.yaml` | decision_core 템플릿 사용 | ENSEMBLE_STABLE_CONTEXT |

---

## 9. 감리 이력

| Pass | 유형 | 결과 |
|------|------|------|
| 1차 재조사 | 호출 경로 추적 | 3개 파라미터 누락 확인 |
| 2차 재조사 | 커밋 이력 분석 | f39e3fe8에서 facade 미동기화 확인 |
| 3차 재조사 | 영향 범위 분석 | 1차 면담 전면 차단, 테스트 맹점 확인 |
| 1차 감리 | 시그니처 실물 대조 | 재조사 결과 100% 일치 |
| 2차 감리 | 호출부 실물 대조 | 2개 호출점, 인자 목록 정합 |
| 3차 감리 | 에러 메시지 정합성 | Python 표준 형식, 처리 경로 정합 |
| 1차 적대적 감리 | 대안 경로 탐색 | 6개 반론 모두 기각 |
| 2차 적대적 감리 | 다른 원인 가능성 | 근본 원인 정밀 분류 (Facade Signature Drift) |
| 3차 적대적 감리 | 테스트 커버리지 맹점 | MagicMock 의존으로 버그 미감지 확인 |
