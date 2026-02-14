# Phase 3-5B: 수정 모드 (Score-based Patch Mode) 청사진

> **문서 상태**: 설계 확정 — 코드 구현 전 승인 필수
> **작성일**: 2026-02-14
> **전제**: Phase 4D(sqlite-vec 마이그레이션) 완료, Phase 4C(DI 전환) 완료
> **참고**: `참고자료.md` 3-D (L1276~1327), `내일작업.md` Step 5-B

---

## 1. 배경 / 문제 정의

현재 Stage 4의 REJECT 경로는 Director 점수와 무관하게 **항상 전면 재작성**(full rewrite)을 수행한다.

```
Round 0: generate_ensemble() → 3후보 → Director 심사
Round 1: REJECT → regenerate_with_feedback() → 3후보 (전면 재작성)
Round 2: REJECT → regenerate_with_feedback() → 3후보 (전면 재작성)
```

**문제점**:
- 70점짜리 원고도 30점짜리와 동일한 전면 재작성 → 기존 장점(문체, 구조, 복선) 소실
- 재작성 결과가 원본보다 나빠질 수 있음 (품질 역전)
- 토큰 비용 동일 소모 (수정 가능한 원고에도 전량 재생산)

---

## 2. 목표 / 비목표

### 목표
- Stage 4에서 점수 50~80 구간의 REJECT에 대해 **패치 모드**(원본 보존 + 지적사항만 수정) 도입
- Director 피드백을 프롬프트에 원본 원고와 함께 전달하여 **최소 수정** 유도
- 패치 실패 시 기존 full rewrite로 자동 폴백

### 비목표 (이번 범위 제외)
- Stage 2 (Arc/Blueprint) 패치 모드 → 향후 별도 Phase
- 수정 diff 뷰 UI → 향후 5-F에서 구현
- 품질 정책(후보 수, 심사 루프, 판정 규칙) 변경 → **절대 금지**
- Stage 2 로직 변경 (로깅 포함) → **금지**

---

## 3. 정책 고정 (절대 변경 금지)

> 아래 5개 정책은 Phase 3-5B 전체 구현 기간 동안 절대 변경할 수 없다.
> 변경이 필요하면 별도 문서로 제안하고 승인 후에만 진행.

| # | 정책 | 근거 |
|---|------|------|
| P1 | **후보 수 3개 유지** — 패치 모드도 앙상블 3후보 생성 | Director 심사 파이프라인 호환성 |
| P2 | **심사 루프(3라운드) / 판정 규칙(adaptive threshold) 불변** | 기존 품질 보장 체계 보존 |
| P3 | **Stage 2 로직 변경 금지** — 로깅 훅도 제외 | 변경 범위 최소화 |
| P4 | **허용 코드 파일**: `stage4_orchestrator.py`, `chief_writer.py`, `chief_writer.yaml`, `constants.py` 만 | 영향 범위 제한 |
| P5 | **문서 승인 전 코드 구현 금지** — 이 청사진이 승인된 후에만 코드 작업 | 설계-구현 분리 |

---

## 4. 허용 / 금지 파일 범위

### 수정 허용 (4건)

| 파일 | 변경 내용 |
|------|----------|
| `modules/core/constants.py` | `PatchModeThresholds` 클래스 + `AuditEvents` 3건 추가 |
| `modules/domain/agents/chief_writer.py` | `patch_with_feedback()` 메서드 추가 |
| `config/prompts/chief_writer.yaml` | `PATCH_MODE_PROMPT` 템플릿 추가 |
| `modules/core/stage4_orchestrator.py` | REJECT 경로에 점수 기반 분기 로직 추가 |

### 신규 생성 허용 (1건)

| 파일 | 내용 |
|------|------|
| `tests/test_stage4_orchestrator.py` | 패치 모드 단위 테스트 |

### 수정 금지

| 파일 | 사유 |
|------|------|
| `modules/core/stage2_orchestrator.py` | 정책 P3 |
| `modules/domain/agents/chief_writer_prompts.py` | PromptLoader/YAML 경로만 사용 |
| `modules/domain/agents/director_*.py` | Director 판정 로직 불변 |
| `modules/validation/*.py` | 검증 파이프라인 불변 |
| 기타 `.py` / `.yaml` (config 포함) | 범위 외 |

---

## 5. 분기 규칙 명세

### Stage 4 Interview Loop 분기

```
interview_round == 0:
    → generate_ensemble()  (기존 동작, 변경 없음)

interview_round == 1:
    previous_attempt["score"] >= 50:
        → patch_with_feedback()  (패치 모드, 3후보)
        → 실패 시(빈 리스트) → regenerate_with_feedback() 폴백
    previous_attempt["score"] < 50:
        → regenerate_with_feedback()  (기존 동작)

interview_round == 2:
    → regenerate_with_feedback()  (기존 동작, score 무관)
```

### 점수 구간 정의

| 구간 | 조건 | 동작 |
|------|------|------|
| **D등급** | score < 50 | 전면 재작성 (기존) |
| **C등급** | 50 <= score < 80 | **패치 모드** (round 1에서만) |
| **B+등급** | score >= 80 | Director가 PASS 판정 → 이 경로 미도달 |

### patch_with_feedback() 계약

```python
async def patch_with_feedback(
    self,
    original_manuscript: str,   # 패치 대상 원본
    feedback: dict,             # Director 피드백
    # ... generate_ensemble과 동일한 나머지 파라미터
) -> list[dict]:
    """3후보 반환. 실패 시 빈 리스트."""
```

- PromptLoader로 `PATCH_MODE_PROMPT` 로드 (chief_writer.yaml)
- 원본 원고 + Director 피드백을 `director_feedback` 파라미터로 포맷
- 내부적으로 `generate_ensemble()` 호출 → **3후보 생성** (P1 준수)
- 실패 시 빈 리스트 반환 → 호출측에서 full rewrite 폴백

### REJECT 경로 변경 (stage4_orchestrator.py)

현재 REJECT 처리 (L1288-1302)에 `best_manuscript` 저장 추가:
```python
previous_attempt = {
    "strategy": selected,
    "rejection_reason": director_feedback,
    "action_items": action_items,
    "score": score,
    "best_manuscript": director_result.get("selected_candidate", {}).get("manuscript", ""),
}
```

---

## 6. 프롬프트 설계 (chief_writer.yaml)

```yaml
PATCH_MODE_PROMPT: |
  [패치 모드: 원본 보존 + 지적사항만 수정]

  당신은 웹소설 교정 전문가입니다.
  아래 원본 원고를 기반으로, Director의 피드백에서 지적된 부분만 최소한으로 수정하세요.

  ## 패치 규칙
  1. 원고의 전체 구조, 문체, 장점을 보존
  2. Director가 지적한 문제점만 정확히 수정
  3. 수정하지 않는 부분은 원문 그대로 유지
  4. 글자 수는 원본과 유사하게 유지 (+-500자)
  5. 캐릭터 성격, 관계, 세계관 설정은 절대 변경 금지

  ## Director 피드백
  {feedback_text}

  ## 원본 원고 (이 원고를 기반으로 수정하세요)
  {original_manuscript}

  전면 재작성하지 마세요. 지적된 부분만 고치세요.
```

---

## 7. 테스트 계획

### 필수 테스트 파일: `tests/test_stage4_orchestrator.py`

| 테스트 ID | 시나리오 | 검증 |
|-----------|----------|------|
| `test_patch_mode_entry` | score=65, round=1 | `patch_with_feedback()` 호출됨, 3후보 반환 |
| `test_patch_fallback_to_rewrite` | score=65, round=1, patch 빈 리스트 | `regenerate_with_feedback()` 폴백 호출 |
| `test_low_score_full_rewrite` | score=30, round=1 | `regenerate_with_feedback()` 직접 호출, patch 미호출 |
| `test_round2_always_rewrite` | score=70, round=2 | `regenerate_with_feedback()` 직접 호출, score 무관 |
| `test_round0_always_generate` | round=0 | `generate_ensemble()` 호출, 분기 없음 |
| `test_previous_attempt_stores_manuscript` | REJECT 발생 | `previous_attempt["best_manuscript"]` 존재 |

### 기존 회귀 테스트

| 파일 | 검증 |
|------|------|
| `tests/test_chief_writer.py` | ChiefWriter 기존 동작 불변 |
| `tests/test_stage2_pipeline.py` | Stage 2 파이프라인 불변 |
| `tests/test_stage3_orchestrator.py` | Stage 3 불변 |

---

## 8. 검증 게이트

```bash
# Gate 1: 구문 검증 (py_compile)
python -m py_compile modules/core/constants.py
python -m py_compile modules/domain/agents/chief_writer.py
python -m py_compile modules/core/stage4_orchestrator.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 테스트 (신규 + 회귀)
set PYTHONIOENCODING=utf-8
pytest tests/test_stage4_orchestrator.py -v
pytest tests/test_chief_writer.py tests/test_stage2_pipeline.py tests/test_stage3_orchestrator.py -v

# Gate 4: pre-commit (ruff + ruff-format)
pre-commit run --files modules/core/constants.py modules/domain/agents/chief_writer.py modules/core/stage4_orchestrator.py config/prompts/chief_writer.yaml
```

---

## 9. 커밋 분할 전략

**단일 커밋** (변경 파일 5개로 원자적 단위):

```
feat(Phase 3-5B): Stage4 점수 기반 패치 모드 도입

- constants.py: PatchModeThresholds(REWRITE=50, PATCH=80) + AuditEvents 3건
- chief_writer.py: patch_with_feedback() 3후보 앙상블
- chief_writer.yaml: PATCH_MODE_PROMPT 템플릿
- stage4_orchestrator.py: REJECT 경로 분기 (score>=50 + round==1 → 패치)
- tests/test_stage4_orchestrator.py: 패치 진입/폴백/저점/라운드2 테스트
```

---

## 10. 롤백 플랜

패치 모드 장애 시 즉시 롤백 가능:

1. **코드 롤백**: `git revert <commit>` — 단일 커밋이므로 원자적 롤백
2. **런타임 비활성화**: `PatchModeThresholds.REWRITE = 999` 로 임시 비활성화 (패치 조건 미충족 → 항상 full rewrite)
3. **영향 범위**: Stage 4 REJECT round 1에서만 작동 → round 0/2 및 PASS 경로 무관

---

## 11. 향후 확장 (이번 범위 외)

| 항목 | 시기 | 비고 |
|------|------|------|
| Stage 2 패치 모드 (Arc/Blueprint) | Phase 3-5B' | 별도 설계 필요 |
| 수정 diff 뷰 UI | Phase 5-F | `difflib.unified_diff()` 활용 |
| 패치 품질 메트릭 수집 | Phase 5-D | patch vs rewrite 성공률 비교 |
| 패치 round 확장 (round 2에도 적용) | 데이터 수집 후 결정 | 현재는 보수적 적용 |
