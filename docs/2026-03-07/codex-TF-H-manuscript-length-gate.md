# Codex TF-H: Self-Critique 분량 재검사 게이트

> **근거 문서**: `docs/2026-03-07/TF-stage4-ep1-failure-audit.md`
> **P0 대상**: BUG-1 + BUG-2 + BUG-4 (신규)
> **대상 파일**: `modules/domain/agents/chief_writer_quality.py` (3곳) + `modules/domain/agents/chief_writer_prompts.py` (1곳 신규)
> **테스트**: `tests/test_chief_writer_quality.py` (신규 6~7개)
> **LLM 추가 호출**: 0회 (순수 Python 검사 + 기존 LLM 호출의 프롬프트 변경)
> **대원칙 준수**: Python은 수집만(분량은 객관 수치) + Director 주권 불변
> **확신도**: 99% — 4차 병렬 조사 + 코드 전량 교차 검증 완료

---

## 배경

projects/0001 Stage 4 Ep.1에서 CW가 12개 후보를 생성했으나 **전부 분량 미달** (최대 4,395자, 목표 5,000자). TF-G 게이트(L146)에서 1회 분량 감지 후 LLM 수정을 시도하지만, 수정 후 분량이 여전히 부족해도:

1. `_self_critique()` 루프에 분량 검사 항목이 없어 재감지 불가 (BUG-1)
2. `_fix_manuscript_issues()` 수정 후 분량 재검증이 없어 실패 미감지 (BUG-2)
3. **`_fix_manuscript_issues()` 프롬프트가 범용 교정용이라 분량 확장 방법을 모름 (BUG-4, 신규)**

결과: 3,000~4,400자 원고가 그대로 Director에 전달 -> V60.97 Python REJECT (30점) -> Director LLM 미호출.

### 실패 메커니즘 상세

```
CW 생성 (3,500자) — Gemini가 투자물 1화(회귀 직후 독백)에서 분량 미달 경향
  -> TF-G 게이트: "분량 부족" 감지 (L146, JSON 전체 < 5,000)
  -> _fix_manuscript_issues() 호출 (L157)
     -> 프롬프트: "발견된 문제를 수정하라" (범용, 분량 확장 지시 없음)  ← BUG-4
     -> LLM: 3,800자로 소폭 수정 (확장 방법 모름)
  -> self-critique 루프 진입 (L170)
     -> _self_critique(): 10개 검사 실행, 분량 검사 없음  ← BUG-1
     -> issues 0~2건 -> severity="low" -> break (탈출)
  -> _fix_manuscript_issues() 수정 후 분량 재검증 없음  ← BUG-2
  -> 3,800자 원고 그대로 Director에 전달
  -> V60.97: 모든 후보 < 4,000자 -> Python REJECT score=30 (LLM 미호출)
```

---

## 패치 1: BUG-1 — `_self_critique()`에 11번째 분량 검사 추가

### 위치

`chief_writer_quality.py` `_self_critique()` 메서드, L274 직후 (10번째 검사 `_check_system_term_exposure` 다음, L276 severity 판단 전)

### 코드

```python
        # 10. [메타 월] 집필 시스템 내부 용어 노출 체크
        issues.extend(self._check_system_term_exposure(content, genre_name))

        # 11. [TF-H] 분량 재검사 — self-critique 루프에서 분량 부족 재감지
        _min_len = int(ManuscriptLimits.MIN_LENGTH)   # 4,000
        _target_len = int(ManuscriptLimits.TARGET_LENGTH)  # 5,000
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

        # [Sweep46] 심각도 판단 — 1~2건은 "low" ...
```

### import

`ManuscriptLimits`가 이미 파일 상단에 import되어 있는지 확인. 없으면 추가:

```python
from modules.core.constants import ManuscriptLimits
```

### 동작 변경

| 원고 길이 | 기존 동작 | 패치 후 동작 |
|-----------|----------|------------|
| < 4,000자 | severity="low", 루프 탈출 | severity="high" (issues 1건+), **루프 계속** |
| 4,000~4,999자 | severity="low", 루프 탈출 | severity="medium" (issues 1건), 다른 이슈 2건+ 시 루프 계속 |
| >= 5,000자 | 통과 | 통과 (변경 없음) |

### severity 상호작용

L276~282의 기존 severity 판단 로직:
- issues >= 5 -> "high"
- issues >= 3 -> "medium"
- issues 1~2 -> "low"

분량 < 4,000자면 `severity="high"` 이슈 1건 추가. 다른 이슈와 합산되어:
- 분량(high) 1건만 -> 전체 severity="low" (1건) -> **BUT** apply_self_critique L190에서 break
- 이 문제를 해결하려면 **severity 판단 로직도 수정 필요**

### severity 판단 보정

L276~282를 다음과 같이 수정:

```python
        # [Sweep46] 심각도 판단
        # [TF-H] individual severity="high" 이슈가 1건이라도 있으면 전체 medium 이상 보장
        severity = "low"
        _has_high_issue = any(
            isinstance(i, dict) and i.get("severity") == "high"
            for i in issues
        )
        if len(issues) >= 5:
            severity = "high"
        elif len(issues) >= 3 or _has_high_issue:
            severity = "medium"
        # 1~2건이면서 high 없으면: severity="low" (기존 동작 유지)
```

**효과**: 분량 < 4,000자(severity="high" 이슈)이면 전체 severity가 최소 "medium" -> self-critique 루프에서 `_fix_manuscript_issues()` 호출 -> 분량 보강 재시도.

**주의**: 이 변경은 분량 외에도 `_check_system_term_exposure` 등 severity="high" 이슈 1건에도 적용됨. 기존에 meta_wall 1건만 있으면 severity="low"로 탈출했는데, 패치 후 severity="medium"으로 수정 시도. **이것은 의도된 개선** — TF-20-01에서 meta_wall도 TF-G 게이트에서 잡도록 설계했으나 self-critique 루프에서는 빠져나갔던 갭 해소.

---

## 패치 2: BUG-2 — `_fix_manuscript_issues()` 수정 후 분량 로깅

### 위치

`chief_writer_quality.py` `_fix_manuscript_issues()` 메서드, L732~733 사이 (JSON 파싱 성공 후, return 전)

### 코드

```python
            # JSON 유효성 검증
            try:
                _fixed_parsed = json.loads(fixed)
                # [TF-H] 수정 후 분량 로깅 — 재검증은 self-critique 루프가 담당
                _fixed_content = _fixed_parsed.get("content", "") if isinstance(_fixed_parsed, dict) else ""
                if isinstance(_fixed_content, str):
                    _fc_len = len(_fixed_content)
                    _min = int(ManuscriptLimits.MIN_LENGTH)
                    if _fc_len < _min:
                        logging.warning(
                            "[TF-H] 수정 후 분량 여전히 부족: %d자 < %d자",
                            _fc_len, _min,
                        )
                return fixed
```

### 설계 판단: 재시도 vs 로깅

**로깅만 수행, 재시도 안 함.** 이유:
- `_fix_manuscript_issues()` 내부에서 재귀 호출하면 LLM 비용 급증 (최악 case 무한루프)
- BUG-1 패치로 `_self_critique()` 루프에서 분량 재감지 -> `_fix_manuscript_issues()` 재호출이 **자연스럽게 발생**
- 역할 분리: `_fix_manuscript_issues()`는 1회 수정, 재시도 판단은 `apply_self_critique()` 루프가 담당

---

## 패치 3 (P0, 신규): BUG-4 — 분량 확장 전용 프롬프트 경로

### 근거

**2차 조사에서 발견된 핵심 갭**: `chief_writer_prompts.py` L174~199의 `get_fix_issues_prompt()`는:

```python
[Role] 원고 교정 전문가
[Task] 아래 원고에서 발견된 문제를 수정하라.
### 발견된 문제
{fix_instructions_text}       # ← "manuscript_length: 원고 길이 3500자 < 목표 5000자"
### 수정 대상 원고
{manuscript_escaped}
### 출력 형식
수정된 JSON 원고만 출력하라. 설명 없이 JSON만.
```

**문제**: "수정하라"만으로는 LLM이 분량을 **확장**하지 않음. 오탈자 교정·표현 수정 수준의 소폭 변경만 수행. 분량 확장은 **장면 추가·대화 확장·심리 묘사 보강** 등 구체적 지시가 필요.

추가로 `thinking_level="low"` (L727)는 thinking budget 2,048 토큰 → 출력 토큰과 경쟁하여 짧은 응답을 유도하는 구조적 원인.

### 위치 1: `chief_writer_prompts.py` — 신규 함수 추가

L199 (`get_fix_issues_prompt` 종료) 직후:

```python
def get_expand_length_prompt(
    *,
    current_length: int,
    target_length: int,
    manuscript_escaped: str,
    hud_report_escaped: str,
) -> str:
    """[TF-H] 분량 확장 전용 프롬프트.

    범용 교정 프롬프트와 달리, 분량 확장에 특화된 구체적 지시 제공.
    """
    _deficit = target_length - current_length
    return f"""
[Role] 웹소설 원고 확장 전문가
[Task] 아래 원고를 {target_length}자 이상으로 확장하라. 현재 {current_length}자 (부족분: {_deficit}자).

### 확장 규칙
1. 기존 내용을 절대 삭제하지 마라.
2. 각 씬에 대화를 최소 2개 추가하라 (인물 성격이 드러나는 대화).
3. 주인공의 내면 심리 묘사를 각 씬당 200자 이상 추가하라.
4. 배경/공간 묘사를 구체화하라 (오감: 시각, 청각, 촉각, 후각).
5. 액션이나 긴장 장면이 있다면 슬로우모션 기법으로 늘려라.
6. 반드시 {target_length}자 이상 출력하라. 부족하면 장면 전환 추가.

### 현재 HUD 상태 (참고)
{hud_report_escaped}

### 확장 대상 원고
{manuscript_escaped}

### 출력 형식
확장된 JSON 원고만 출력하라. 설명 없이 JSON만.
"""
```

### 위치 2: `chief_writer_quality.py` `_fix_manuscript_issues()` — 분기 추가

L713~725 사이, 프롬프트 생성부를 분기:

```python
        # [TF-H] 분량 부족이 주요 이슈면 확장 전용 프롬프트 사용
        _has_length_issue = any(
            isinstance(i, dict) and i.get("type") == "manuscript_length"
            for i in issues[:3]
        )

        if _has_length_issue:
            # 분량 확장 전용 경로 — 구체적 확장 지시 + thinking 예산 확대
            _content = ""
            try:
                _parsed = json.loads(manuscript)
                _content = _parsed.get("content", "") if isinstance(_parsed, dict) else manuscript
            except (json.JSONDecodeError, ValueError, TypeError):
                _content = manuscript
            prompt = get_expand_length_prompt(
                current_length=len(_content),
                target_length=int(ManuscriptLimits.TARGET_LENGTH),
                manuscript_escaped=self.host._escape_braces(manuscript),
                hud_report_escaped=self.host._escape_braces(hud_report[:500]),
            )
            _thinking = "medium"  # thinking 예산 확대 → 출력 토큰 충분 확보
        else:
            # [V65] 기존 범용 교정 프롬프트
            prompt = get_fix_issues_prompt(
                fix_instructions_text=chr(10).join(fix_instructions),
                hud_report_escaped=self.host._escape_braces(hud_report[:500]),
                manuscript_escaped=self.host._escape_braces(manuscript),
            )
            _thinking = "low"
```

그리고 L727의 `thinking_level="low"`를 `_thinking` 변수로 교체:

```python
        try:
            fixed = self.host.ask(prompt, temperature=0.5, thinking_level=_thinking)
```

### import 추가

`chief_writer_quality.py` 상단:

```python
from modules.domain.agents.chief_writer_prompts import get_expand_length_prompt
```

(`get_fix_issues_prompt`는 이미 import되어 있을 것)

### 설계 근거

| 항목 | 범용 교정 (기존) | 확장 전용 (신규) |
|------|-----------------|-----------------|
| 프롬프트 | "문제를 수정하라" | "N자 이상으로 확장하라" + 6개 구체 규칙 |
| thinking_level | "low" (2K tokens) | "medium" (8K tokens) |
| 출력 경향 | 소폭 수정 (오탈자/표현 교체) | 장면·대화·묘사 확장 |
| LLM 비용 | Flash 1회 | Flash 1회 (동일, thinking만 증가) |

---

## 패치 4 (선택): TF-G 게이트 분량 기준 정렬

### 현재 문제

TF-G 게이트(L146): `len(current_manuscript) < 5000` (TARGET 기준, JSON 전체 문자열)
V60.97(director_ensemble.py L588): `ManuscriptLimits.MIN_LENGTH` (4,000, content 기준)

**기준 불일치**: TF-G는 JSON 전체 길이 5,000, V60.97은 manuscript 필드 4,000.

### 조사 결과

2차 조사에서 확인: `candidate["manuscript"]`는 **순수 텍스트**(JSON 문자열이 아님). V60.97의 `len(c.get("manuscript") or "")`는 정확하게 content 길이를 측정.

TF-G 게이트의 `len(current_manuscript)`은 JSON 전체 문자열 길이이므로 content보다 항상 크다. 따라서 "JSON 전체 < 5,000이면 content는 확실히 < 5,000" → **false negative 없음**. 기존 동작 유지 가능.

**P2 유보.**

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `modules/domain/agents/chief_writer_quality.py` | (1) `_self_critique()` L274 뒤에 11번째 분량 검사 추가 (2) L276~282 severity 판단에 `_has_high_issue` 조건 추가 (3) `_fix_manuscript_issues()` L713 분량 이슈 분기 + thinking_level 변수화 (4) L732 뒤에 분량 로깅 추가 |
| `modules/domain/agents/chief_writer_prompts.py` | (5) `get_expand_length_prompt()` 신규 함수 추가 (L199 직후) |

**변경 파일 2개, 변경 지점 5곳.**

---

## 테스트 계획

### 신규 테스트 (`tests/test_chief_writer_quality.py` 또는 신규 파일)

| # | 테스트 | 검증 내용 |
|---|--------|----------|
| 1 | `test_self_critique_detects_short_manuscript` | content 3,000자 원고 -> issues에 `manuscript_length` 타입 포함, severity="high" |
| 2 | `test_self_critique_detects_medium_manuscript` | content 4,500자 원고 -> issues에 `manuscript_length` 타입 포함, severity="medium" |
| 3 | `test_self_critique_passes_long_manuscript` | content 5,500자 원고 -> issues에 `manuscript_length` 없음 |
| 4 | `test_severity_high_issue_promotes_to_medium` | issues 1건(severity="high") -> 전체 severity >= "medium" |
| 5 | `test_fix_manuscript_logs_short_result` | `_fix_manuscript_issues()` 반환값이 4,000자 미만 -> WARNING 로그 출력 |
| 6 | `test_fix_uses_expand_prompt_for_length_issue` | issues에 `manuscript_length` 포함 시 `get_expand_length_prompt` 호출 확인 |
| 7 | `test_fix_uses_generic_prompt_for_other_issues` | issues에 `manuscript_length` 없을 시 `get_fix_issues_prompt` 호출 확인 |

### 기존 테스트 영향

- 2차 조사에서 확인: 기존 테스트는 `call_count >= 1` 패턴 사용, severity exact match 없음 → **기존 테스트 깨짐 없음**
- `_self_critique()` 반환값에 issues 1건 추가 가능 → 기존 테스트 중 issues 개수를 exact match하는 것이 있으면 수정 필요 (없음 확인됨)

### 회귀 테스트

```bash
pytest tests/ -q --tb=short
```

기준선: 3,530 passed (2026-03-06 최종 확인)

---

## 대원칙 검증

| 대원칙 | 준수 여부 | 근거 |
|--------|----------|------|
| 1. Python은 수집만, 판단은 LLM | **준수** | 분량은 `len()` 객관 수치 — Python이 측정하고 issues 리스트에 추가만 함. 수정 판단/실행은 LLM(_fix_manuscript_issues)이 수행. 확장 프롬프트도 LLM에 구체적 지시를 제공할 뿐 |
| 2. 팩트시트 수정 권한은 LLM만 | **해당 없음** | 팩트시트 미변경 |
| 3. Director 주권주의 | **준수** | CW 내부 self-critique 강화일 뿐, Director 판정 로직 미변경. V60.97도 미변경 |
| 4. 사망 캐릭터 | **해당 없음** | |

---

## 위험 요소

| 위험 | 확률 | 완화 |
|------|------|------|
| self-critique 루프 무한 반복 | 낮음 | MAX_CRITIQUE_ROUNDS=3 상한 존재. L193~197 mid-round Rubric 3.5 조기 종료도 작동 |
| 분량 검사로 severity 인플레이션 | 중간 | severity="high" 이슈 1건 -> 전체 "medium"만. "high"까지 올리려면 5건+ 필요 (기존 로직 유지) |
| 기존 테스트 깨짐 | 낮음 | 2차 조사 확인: 기존 테스트 severity/issues exact match 없음 |
| LLM 비용 증가 | 낮음 | self-critique 루프 최대 2회 추가 (MAX=3). 확장 경로는 thinking="medium"이나 Flash 1회 (기존 "low"→"medium" 차이) |
| 확장 프롬프트 과도한 분량 생성 | 낮음 | ManuscriptLimits.MAX_LENGTH (15,000) 상한 + Director 심사에서 냉각. 과도한 확장은 품질 저하 → Director REJECT로 자연 방어 |
| thinking_level="medium" 토큰 경쟁 | 낮음 | Flash 모델 max_output_tokens 충분 (8,192 thinking + 출력). "low"(2K)에서 "medium"(8K)으로 올리면 오히려 출력 계획 시간 확보 → 더 나은 확장 |

---

## 확신도 평가

| 조사 항목 | 결과 | 확신 근거 |
|-----------|------|-----------|
| Arc 1 구조/수치 정합 | PASS | 4화 구성, investment_calc 일치 |
| Blueprint 1 구조 | PASS | 4씬, hook 완비, 긴장도 곡선 정상 |
| CW 프롬프트 분량 지시 | PASS | "5,000자 이상" 3곳 명시 (strategy instructions + WRITING_GUIDELINES) |
| TF-G 게이트 1차 감지 | PASS | L146 정상 작동 |
| `_self_critique()` 분량 항목 | **FAIL** | 10개 검사 중 분량 없음 → BUG-1 |
| `_fix_manuscript_issues()` 재검증 | **FAIL** | 수정 후 분량 체크 없음 → BUG-2 |
| `get_fix_issues_prompt()` 확장 능력 | **FAIL** | 범용 교정만, 분량 확장 지시 없음 → BUG-4 |
| `thinking_level` 토큰 경쟁 | **확인** | "low"=2K → 출력 축소 유도. "medium"으로 상향 필요 |
| V60.97 측정 정확도 | PASS | `candidate["manuscript"]` 순수 텍스트, MIN_LENGTH=4,000 정확 |
| Director LLM 호출 경로 | PASS | V60.97 설계 의도 (분량 미달 차단) |
| 12개 후보 전수 분량 미달 | **확인** | 일관된 패턴 — CW 구조적 문제 |
| 기존 테스트 호환성 | PASS | severity/issues exact match 테스트 없음 |

**종합 확신도: 99%** — 4차 병렬 조사(Arc/Blueprint/CW프롬프트/세션로그/V60.97경로/기존테스트/fix프롬프트/thinking_level) 전량 교차 검증 완료. BUG-1/BUG-2/BUG-4 3건이 분량 미달의 **필요충분 원인**:
- BUG-1이 재감지를 막고
- BUG-2가 실패를 은폐하고
- BUG-4가 확장 능력 자체를 없앤다

3건 전부 패치하면 self-critique 루프에서 분량 부족 재감지 → 확장 전용 프롬프트로 구체적 보강 → 최대 3회 반복. 4차 면담 4,395자 수준이면 1~2회 확장으로 5,000자 도달 가능성 높음.

---

## 실행 순서

1. `chief_writer_prompts.py`에 `get_expand_length_prompt()` 신규 함수 추가
2. `chief_writer_quality.py` 4곳 수정:
   - (a) `_self_critique()` L274 뒤에 11번째 분량 검사
   - (b) L276~282 severity 판단에 `_has_high_issue` 조건
   - (c) `_fix_manuscript_issues()` L713 분량 이슈 분기 + thinking_level 변수화
   - (d) L732 뒤에 분량 로깅
3. import 추가 (`get_expand_length_prompt`, `ManuscriptLimits` 확인)
4. 신규 테스트 7개 작성
5. `pytest tests/ -q` 전량 통과 확인
6. projects/0001 Stage 4 재실행으로 실전 검증 (선택)
