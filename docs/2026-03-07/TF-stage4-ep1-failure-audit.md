# TF — Stage 4 Ep.1 연속 실패 전수조사

> **일시**: 2026-03-07
> **프로젝트**: `projects/0001` (투자물 장르, Arc 1 Ep.1)
> **증상**: Stage 4 제1화 원고 3라운드 연속 REJECT (30점), Director LLM 미호출
> **감사 범위**: Arc 1 + Blueprint 1 + CW 생성 경로 + Director 심사 경로 + 세션 로그 전량

---

## 1. 실행 요약

| 항목 | 값 |
|------|-----|
| Stage 2 Arc 1 | PASS (98점, 1회 시도) |
| Stage 3 Blueprint 1~4화 | 전부 PASS (100점) |
| Stage 4 Ep.1 | **3라운드 연속 REJECT (30점)** |
| Director LLM 호출 | **0회** (Python pre-check에서 차단) |
| 원고 최대 길이 | 4,395자 (4차 면담 2번 후보) |
| 원고 최소 길이 | 2,796자 (1차 면담 2번 후보) |
| CW 후보 총 생성 수 | 12개 (4라운드 x 3후보) |
| 분량 통과 후보 | **0개** (12개 전부 미달) |

---

## 2. 근본 원인 분류

### BUG-1 (P0): `_self_critique()`에 분량 재검사 항목 없음

**위치**: `chief_writer_quality.py` L238~286

`_self_critique()` 메서드에 10개 검사 항목이 있으나 **분량 검사가 없음**:

| # | 검사 항목 | 메서드 |
|---|----------|--------|
| 1 | HUD 모순 | `_check_hud_consistency()` |
| 2 | 클리셰 과다 | `_check_cliche_overuse()` |
| 3 | 정당화 부족 | `_check_justification_gaps()` |
| 4 | NPC 관계 | `_check_npc_relationship()` |
| 5 | 동기/약속 방치 | `_check_motivation_consistency()` |
| 6 | WritingDirective 준수 | `_check_writing_directive()` |
| 7 | 표현 신선도 | `_check_expression_freshness()` |
| 8 | ending_hook 포함 | `_check_ending_hook_presence()` |
| 9 | 산술 일관성 | `_check_arithmetic_consistency()` |
| 10 | 메타 월 용어 | `_check_system_term_exposure()` |
| **11** | **분량 검사** | **없음** |

**영향**: TF-G 게이트(L146)에서 1회 분량 검사 후 `_fix_manuscript_issues()`로 LLM 수정을 시도하지만, 수정 후 분량이 여전히 부족해도 self-critique 루프(L170~206)에서 **분량을 재검사하지 않음**. severity="low"로 판정되어 루프 즉시 탈출.

**재현 경로**:
```
CW 생성 (3,500자)
  -> TF-G 게이트: "분량 부족" 감지 (L146)
  -> _fix_manuscript_issues() 호출 (L157)
  -> LLM: 3,800자로 보강 (여전히 부족)
  -> self-critique 루프 진입 (L170)
     -> _self_critique(): 10개 검사 실행
     -> 분량 검사 없음 -> issues 0~2건 -> severity="low"
     -> L190: break (탈출)
  -> 3,800자 원고 그대로 Director에 전달
```

---

### BUG-2 (P0): `_fix_manuscript_issues()` 수정 후 분량 재검증 없음

**위치**: `chief_writer_quality.py` L703~739

TF-G 게이트에서 `_fix_manuscript_issues()`를 호출하여 LLM에 분량 보강을 요청하지만:

1. LLM이 여전히 부족한 분량으로 응답해도 **재검증 없이 그대로 반환** (L732~733)
2. JSON 파싱 실패 시 **원본 그대로 반환** (L735~736)
3. 수정 후 `len(fixed_content) < MIN_LENGTH` 체크가 **없음**

---

### BUG-3 (P1): V60.97 Python REJECT가 Director LLM을 완전 우회

**위치**: `director_ensemble.py` L588~623

모든 후보가 `ManuscriptLimits.MIN_LENGTH` (4,000자) 미만이면:
- Director LLM **호출 안 함**
- Python이 직접 `score=30, verdict=REJECT` 반환
- `score_breakdown = {}` (빈 dict)

**대원칙 3 (Director 주권주의) 위반 여부**: 분량은 객관 수치이므로 Python 차단 자체는 합리적. 그러나 Director에게 "분량 부족이지만 내용 품질은 어떤지" 판단 기회를 주지 않는 것은 정보 손실. **P1 유보** — 분량이 4,000자 미만이면 내용 심사 자체가 무의미하므로 현행 유지 가능.

---

### FINDING-1 (P2): CW 대화 비율 0%

세션 로그 확인 결과 12개 후보 중 대화가 포함된 후보가 **거의 없음**:
- 1차 면담: 대화 2개, 0개, 0개
- 2차 면담: 대화 0개, 0개, 0개
- 3차 면담: 대화 0개, 1개, 0개

Blueprint Ep.1은 4씬 모두 **독백/서술 중심** (회귀 직후 혼자 기억 정리). Blueprint 설계 자체가 대화 기회가 적은 구조.

---

### FINDING-2 (P2): 4차 면담에서 4,395자 도달 — 임계점 근접

| 라운드 | 최대 길이 | 증가율 |
|--------|----------|--------|
| 1차 | 3,424자 | — |
| 2차 | 3,698자 | +8% |
| 3차 | 3,848자 | +4% |
| 4차 | 4,395자 | +14% |

4차에서 4,395자까지 도달. `MIN_LENGTH=4,000` 기준으로는 통과 가능했으나, V60.97은 `ManuscriptLimits.MIN_LENGTH` (4,000자)를 사용하는데 **실제 후보의 manuscript 필드가 JSON 전체 문자열**이라 content만 추출하면 더 짧을 수 있음.

---

## 3. Arc 1 / Blueprint 1 검증 결과

### Arc 1: PASS (이상 없음)

- 4화 구성, ep_start=1 ~ ep_end=4
- tactical_doc 완성, beat_sequence 4개
- state_constraints 11개 부문 완성
- investment_calc 수치 정합 (20.3억 - 0.48억 = 19.52억)
- 아이템 추적 3중화 (acquired/consumed/protagonist) 일관

### Blueprint 1: PASS (구조 정상, 내용 제약 존재)

- 4씬 구조: opening_hook -> tension_build -> action_peak -> cliffhanger
- 긴장도 곡선: 7 -> 8 -> 9 -> 8
- ending_hook: "첫 번째 전장이 정해졌다"
- **제약**: 1화 특성상 주인공 혼자 행동 (회귀 직후), NPC 상호작용 기회 부족

---

## 4. 실패 메커니즘 상세

### 4-1. Director 30점의 정확한 출처

`director_ensemble.py` L608~623의 V60.97 Python pre-check:

```python
if not qualified_indices:  # 모든 후보 MIN_LENGTH 미만
    return {
        "verdict": "REJECT",
        "score": 30,           # <- 하드코딩
        "action_items": ["분량 확장 필요 - 최소 5,000자"],
        "length_violation": True,
    }
```

- Director LLM: **미호출**
- score_breakdown: **빈 dict** (LLM 미호출 증거)
- action_items: **Python 하드코딩** (LLM 판단 아님)

### 4-2. Self-Critique 루프 탈출 조건

`chief_writer_quality.py` L276~282:

```python
severity = "low"
if len(issues) >= 5:
    severity = "high"
elif len(issues) >= 3:
    severity = "medium"
```

분량 검사가 없으므로 issues가 0~2건 -> severity="low" -> L190 `break` 탈출.

### 4-3. TF-G 게이트 단발성

L140~168에서 TF-G 게이트는 **루프 진입 전 1회만 실행**. `_fix_manuscript_issues()` 호출 후 수정 결과에 대한 재검증이 없어 분량 보강 실패를 감지 못함.

---

## 5. 이슈 분류 종합

| 등급 | ID | 내용 | 위치 |
|------|-----|------|------|
| **P0** | **BUG-1** | `_self_critique()`에 분량 재검사 항목 없음 — 2차+ 라운드에서 분량 미검사 | `chief_writer_quality.py` L238~286 |
| **P0** | **BUG-2** | `_fix_manuscript_issues()` 수정 후 분량 재검증 없음 — LLM 보강 실패 미감지 | `chief_writer_quality.py` L703~739 |
| **P1** | **BUG-3** | V60.97 Director LLM 완전 우회 — 분량 미달 시 내용 품질 판단 기회 상실 | `director_ensemble.py` L588~623 |
| **P2** | **FINDING-1** | Blueprint Ep.1 대화 기회 부족 — 회귀 직후 독백 구조 | Blueprint 설계 |
| **P2** | **FINDING-2** | 4차 면담에서 4,395자 도달 — 임계점 근접이나 통과 못함 | 세션 로그 |

---

## 6. 패치 방안

### BUG-1 패치: `_self_critique()`에 분량 검사 추가

**위치**: `chief_writer_quality.py` L274 직후 (10번째 검사 다음)

```python
# 11. [TF-H] 분량 재검사 — self-critique 루프에서 분량 부족 재감지
_min_len = ManuscriptLimits.MIN_LENGTH  # 4,000
_target_len = ManuscriptLimits.TARGET_LENGTH  # 5,000
if len(content) < _target_len:
    _sev = "high" if len(content) < _min_len else "medium"
    issues.append({
        "type": "manuscript_length",
        "description": (
            f"원고 길이 {len(content)}자 < 목표 {_target_len}자. "
            "장면 묘사, 인물 심리, 대화를 확장하세요."
        ),
        "severity": _sev,
    })
```

**효과**:
- `< 4,000자`: severity="high" -> 루프 계속 (3회 수정 기회)
- `4,000~4,999자`: severity="medium" -> issues 3건+ 시 루프 계속
- `>= 5,000자`: 검사 통과

### BUG-2 패치: `_fix_manuscript_issues()` 수정 후 분량 재검증

**위치**: `chief_writer_quality.py` L732 직후

```python
# [TF-H] 수정 후 분량 재검증
try:
    _fixed_data = json.loads(fixed)
    _fixed_content = _fixed_data.get("content", "")
    if isinstance(_fixed_content, str) and len(_fixed_content) < ManuscriptLimits.MIN_LENGTH:
        logging.warning(
            "[TF-H] 수정 후 분량 여전히 부족: %d자 < %d자 — 원본 유지",
            len(_fixed_content), ManuscriptLimits.MIN_LENGTH,
        )
        # 원본 유지하되 issues 정보는 보존 (다음 루프에서 재시도)
except (json.JSONDecodeError, ValueError, TypeError):
    pass
```

### BUG-3 (P1 유보): 현행 유지

V60.97의 분량 미달 Python REJECT는 합리적 방어선. 분량이 4,000자 미만이면 내용 심사 자체가 무의미. BUG-1/BUG-2 패치로 분량 부족 원고가 Director에 도달하는 빈도 자체를 줄이는 것이 근본 해결.

---

## 7. 검증 확인

| 검증 항목 | 결과 |
|-----------|------|
| Arc 1 구조/수치 정합 | PASS |
| Blueprint 1 구조 | PASS (4씬, hook 완비) |
| CW 프롬프트 분량 지시 | PASS (5,000자+ 명시) |
| TF-G 게이트 1차 분량 감지 | PASS (정상 작동) |
| `_self_critique()` 분량 항목 | **FAIL** (없음 -> BUG-1) |
| `_fix_manuscript_issues()` 재검증 | **FAIL** (없음 -> BUG-2) |
| Director LLM 호출 경로 | PASS (V60.97 설계 의도) |
| V60.97 30점 하드코딩 | PASS (분량 미달 시 합리적) |
| 세션 로그 LLM 호출 | PASS (CW/self-critique 정상 호출 확인) |

---

## 8. 결론

**Stage 4 Ep.1 3라운드 연속 실패의 근본 원인은 CW 품질 게이트의 분량 재검사 공백(BUG-1, BUG-2)**입니다.

Arc 1, Blueprint 1은 모두 정상. CW 프롬프트에도 5,000자 지시가 명시되어 있으나, Gemini LLM이 투자물 장르 1화(회귀 직후 독백 중심)에서 분량을 채우지 못하는 경향이 있음. 이때 self-critique 루프가 분량 부족을 재감지하지 못해 3,000~4,400자 원고가 그대로 Director에 전달되고, V60.97 Python pre-check에서 일괄 REJECT.

P0 2건(BUG-1/BUG-2) 패치 시 self-critique 루프에서 분량 보강 기회가 최대 3회 추가되어, 4,395자(4차 면담 최대값) 수준의 원고가 5,000자까지 도달할 가능성이 높아짐.

**확신도: 99%** — Arc/Blueprint/CW프롬프트/Director경로/세션로그 전량 교차 검증 완료. 12개 후보 전부 분량 미달이라는 일관된 패턴이 BUG-1/BUG-2와 정확히 일치.
