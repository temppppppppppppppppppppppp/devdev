# 실파이프라인 감사 07 — 후속 시스템 패치 문서 (2026-03-08)

> **대상**: 감사 07 발견 사항 중 시스템 패치 필요 항목
> **제외**: ep_0015 재생성 (파이프라인 재실행으로 해결), CON-1~6 콘텐츠 모순 (Block/Treatment 설계로 해결)

---

## 완료된 패치

### BUG-1 [P0/CRITICAL] ✅ 완료

**`corrected_manuscript` 키 누락 → InPlace JSON 미파싱**

**수정 파일**: `modules/domain/agents/chief_writer.py`
- L843: 1단계 JSON 파싱에 `corrected_manuscript` 키 1순위 추가
- L901: `_unwrap_manuscript_text()` 2단계 폴백에도 `corrected_manuscript` + `patched_manuscript` 키 동기화

**감리**: 3회 완료, 3,650 passed

---

## 잔여 패치 대상

### WARN-2 [P2] 부상 상태 오탐 — 비전투 장르 injuries 검사 스킵

**증상**: `[V66.1] 부상 상태에서 무리한 행동 감지` 경고가 투자물에서 반복 발생. Director가 매번 기각.

**근본 원인**:
- `modules/validation/continuity_validator.py` L403-542 `_check_injury_continuity()` 메서드가 **장르 무관하게** 모든 장르에 동일한 부상 검사 적용
- L424-425: 부상 키워드 (`부상`, `상처`, `파열`, `골절` 등) 검사 — 장르 체크 없음
- L515-521: 정당화 패턴이 무협 전용 (`역근경`, `내공 운용`, `진기 순환`) — 투자물에서 정당화 불가능
- `genre_schema_builder.py`는 투자물에 `injuries` 필드를 생성하지 않으나, validator는 이를 무시

**수정 방향**:

```python
# continuity_validator.py L454 직후
# 비전투 장르(투자물/요리/배우/작곡/의료/대체역사/스포츠)는 부상 검사 스킵
_combat_genres = {"wuxia", "hunter", "fantasy"}
_genre = validation_context.get("genre", "wuxia")
if _genre not in _combat_genres:
    return {"passed": True, "violations": [], "warnings": []}
```

**수정 파일**:
1. `modules/validation/continuity_validator.py` L454 — 장르 조건부 분기 추가
2. 호출측(stage2/3/4 validator)에서 `genre` 파라미터 전달 확인

**테스트 추가**: 3건
- investment 장르 + 부상 키워드 → 경고 없음
- wuxia 장르 + 부상 + 정당화 없음 → 경고 발생
- fantasy 장르 + 부상 → 경고 발생

---

### WARN-3 [P2] "개미 자칭 불가" 오탐 — 정규식 과매칭

**증상**: `[V63.2] 직위에서 '개미' 자칭 불가` 경고가 투자물 ep6,9,13,14,15에서 반복. 주인공이 타인을 "개미"로 지칭한 것을 자칭으로 오인.

**근본 원인**:
- `modules/core/genre_guards/base_guard.py` L414 자칭 정규식:
  ```python
  self_address_patterns = [f"나는.*{title}", f"본좌.*{title}", f"소생.*{title}"]
  ```
- `나는.*개미` 패턴이 `"나는 개미들을 관찰했다"` (타인 지칭)에도 매칭
- 1인칭 문맥 vs 타인 지칭 표현 구분 로직 부재
- `investment_guard.py` L317-340에서 "개미"를 "무일푼"/"소시민" 직위 호칭으로 정의

**오탐 시나리오**:

| 원고 문장 | 패턴 매칭 | 현재 판정 | 올바른 판정 |
|---------|---------|---------|----------|
| "나는 개미다" | `나는.*개미` ✓ | REJECT | ✓ 자칭 |
| "나는 개미들을 이끈다" | `나는.*개미` ✓ | REJECT | ✗ 타인 지칭 |
| "개미들은 두려워한다" | `나는.*개미` ✗ | PASS | ✓ 타인 |

**수정 방향**: 문맥 윈도우 기반 타인 지칭 필터

```python
# base_guard.py L414 수정
self_address_patterns = [
    f"나는\\s{{0,5}}{title}(?:다|이다|입니다|야|인가)",  # "나는 개미다" (자칭 확정)
]
# 타인 지칭 제외 패턴
_exclusion_suffixes = ["들", "들을", "들의", "들과", "들은", "들이", "투자자"]
for match in re.finditer(pattern, manuscript):
    _context = manuscript[match.start():match.end() + 10]
    if any(suf in _context for suf in _exclusion_suffixes):
        continue  # 복수형/타인 지칭 → 오탐 필터링
```

**수정 파일**:
1. `modules/core/genre_guards/base_guard.py` L414 — 정규식 정밀화 + 타인 지칭 제외 로직

**테스트 추가**: 4건
- "나는 개미다" → 자칭 감지 (정상)
- "나는 개미들을 본다" → 오탐 필터링
- "개미처럼 행동한다" → 오탐 필터링
- 무협 장르 "나는 소협이다" → 자칭 감지 (정상)

---

### WARN-4 [P3] quality_metrics.jsonl Stage 4 score=0 — Director 점수 미전파

**증상**: Stage 4 PASS 항목의 quality_metrics.jsonl score가 전부 0. episode_production.jsonl에만 실제 점수 기록.

**근본 원인**:
- `stage4_post_processor.py` L1094: `final_state_updates.get("director_score", 0)` → **키 없음 → 0**
- `stage4_interview_round.py` L667: `score = director_result.get("score", 0)` → 로컬 변수로만 보존
- L1479: `final_state_updates = director_result.get("state_updates", {})` → Director state_updates에 score 미포함
- **Director가 반환하는 score는 최상위 키에 있으나, state_updates에 병합되지 않음**

**데이터 흐름**:
```
Director → {"score": 97, "state_updates": {...}}
                ↓                      ↓
    episode_production.jsonl ✅   quality_metrics.jsonl ❌
    (score=97 정상)               (state_updates에 score 없음 → 0)
```

**수정 방향**:

```python
# stage4_interview_round.py L1479 직후
final_state_updates = director_result.get("state_updates", {})
if isinstance(final_state_updates, dict) and score > 0:
    final_state_updates["director_score"] = score  # Director 점수 전파
```

**수정 파일**:
1. `modules/core/stage4_interview_round.py` L1479 — `director_score` 키 state_updates에 병합

**테스트 추가**: 2건
- PASS verdict 시 quality_metrics score > 0 확인
- PASS_WITH_FIX verdict 시에도 score 전파 확인

**영향**: quality_dashboard의 Stage 4 점수 추이 분석, score_regression 감지 정상화

---

## 패치 우선순위

| 순서 | ID | 심각도 | 유형 | 설명 | 상태 |
|------|-----|--------|------|------|------|
| ~~1~~ | BUG-1 | P0 | 코드 | `corrected_manuscript` 키 누락 | ✅ 완료 |
| 2 | WARN-4 | P3→P2 | 코드 | quality_metrics score=0 미전파 | **패치 대기** |
| 3 | WARN-2 | P2 | 코드 | 부상 상태 비전투 장르 오탐 | **패치 대기** |
| 4 | WARN-3 | P2 | 코드 | 개미 자칭 정규식 과매칭 | **패치 대기** |

> **WARN-4 우선순위 상향 (P3→P2)**: 모든 Stage 4 PASS의 quality_metrics 점수가 0으로 기록되어 품질 추이 분석이 불가능. 데이터 정합성 관점에서 P2 수준.

---

## 콘텐츠 모순 (시스템 패치 불가 — 참고용)

| ID | 내용 | 방지 방법 |
|-----|------|----------|
| CON-1 | 장비 수준 모순 (5화 설치 vs 10화 무시) | Block/Treatment 씬 설계 |
| CON-2 | 박성호 직함 (차장→팀장) | StateTracker→CW 전달 경로 점검 |
| CON-3 | 블랙베리 수량 (3대→4개) | FactLedger 수치 추적 |
| CON-4 | 1인칭/3인칭 혼재 (ep10) | V70 POV 체크 마지막 문장 커버리지 |
| CON-5 | 2006년 태블릿PC | 시대 고증 DB |
| CON-6 | 반복 패턴 6종 | WritingDirective(TF-54) 누적 분석 |
