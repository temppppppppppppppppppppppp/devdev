# Codex F — 투자물 수치 검산 시스템 (Python 역산 + Flash 검산 에이전트)

> **일시**: 2026-03-07
> **근거**: stage2-depth-audit-09 P0 5건 (LLM 레버리지 산술 오류)
> **목표**: 투자물 장르 Arc의 수치 정합성을 Python + LLM 하이브리드로 검증
> **대원칙**: Python은 산술 역산(수집), Flash LLM은 서술-수치 의미 검증(판단), Director가 최종 결정(주권)

---

## 0. 문제 정의

LLM이 레버리지 수익 계산 시 `가격변동률 × 레버리지배수`를 정확히 수행하지 못하고 "원금의 ~100% 수익"으로 단순화. projects/0001에서 P0 5건 발생:

| Arc | Arc 주장 | 정확 계산 | 괴리 |
|-----|---------|----------|------|
| Arc 3 Ep.9 | 총자산 28억 | 25.8억 | 2.2억 |
| Arc 3 Ep.11 | 청산수익 5.2억 | 4.72억 | 4,800만 |
| Arc 4 Ep.13 | 현금 15.2억 | 20.4억 | 5.2억 |
| Arc 4 Ep.17 | 청산수익 5억 | 1.45억 | 3.55억 |
| Arc 5 Ep.18 | 최종 50.13억 | ~39억 | ~11억 |

Director가 Arc 2~3에서는 감지했으나 Arc 4~5에서 놓침 (100점 PASS).

---

## 1. 아키텍처

```
Arc JSON 생성 (LLM)
    │
    ▼
[Step A] investment_calc 구조화 필드 (스키마 강제)
    │
    ▼
[Step F-1] InvestmentArithmeticChecker (Python-only)
    │  - 구조화 필드에서 역산: (exit-entry)/entry × leverage × principal
    │  - tactical_doc 자유 서술에서 regex 추출 (폴백)
    │  - 현금 내역 합산 검증
    │  - 결과: list[dict] advisory
    │
    ▼
[Step F-2] InvestmentMathVerifier (Flash LLM 1회)
    │  - 입력: Arc 전문 + Python 역산 결과
    │  - 검산: 자유 서술 수치 추출 + 서술-수치 의미 모순 ("횡보" vs 4.25억)
    │  - 결과: list[dict] advisory
    │
    ▼
[Step F-3] Director advisory 주입
    │  - compare_and_select_arc(advisory=...) 파라미터에 합산 주입
    │  - Director가 최종 판정 (대원칙 3)
    ▼
PASS / REJECT / PASS_WITH_FIX
```

---

## 2. Step A — Arc 스키마에 investment_calc 구조화 필드 추가

### 2-1. 파일: `modules/core/response_schemas.py`

`ARC_STATE_CONSTRAINTS_SCHEMA` 내에 `investment_calc` 선택 필드 추가:

```python
# [F-A] 투자물 수치 검산용 구조화 필드 (optional)
"investment_calc": types.Schema(
    type=types.Type.OBJECT,
    description="투자물 장르: 에피소드별 투자 거래 명세. Python 검산에 사용.",
    properties={
        "transactions": types.Schema(
            type=types.Type.ARRAY,
            description="해당 Arc 내 투자 거래 목록",
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "ep_no": types.Schema(type=types.Type.INTEGER, description="에피소드 번호"),
                    "asset": types.Schema(type=types.Type.STRING, description="자산명 (예: 'WTI 원유', '금 선물')"),
                    "action": types.Schema(type=types.Type.STRING, description="매수/매도/청산"),
                    "entry_price": types.Schema(type=types.Type.NUMBER, description="진입가 (달러/원 등)"),
                    "exit_price": types.Schema(type=types.Type.NUMBER, description="청산가 (미청산 시 0)"),
                    "leverage": types.Schema(type=types.Type.NUMBER, description="레버리지 배수 (없으면 1)"),
                    "principal": types.Schema(type=types.Type.NUMBER, description="투자 원금 (원화, 원 단위)"),
                    "stated_profit": types.Schema(type=types.Type.NUMBER, description="서술한 수익/손실 (원화, 원 단위. 손실은 음수)"),
                },
                required=["ep_no", "asset", "action", "entry_price", "leverage", "principal"],
            ),
        ),
        "final_cash": types.Schema(type=types.Type.NUMBER, description="Arc 종료 시 현금 보유액 (원 단위)"),
        "final_total_assets": types.Schema(type=types.Type.NUMBER, description="Arc 종료 시 총자산 (원 단위)"),
    },
),
```

### 2-2. 파일: `config/prompts/analyst.yaml` (또는 `ensemble.yaml`)

Arc 생성 프롬프트에 `investment_calc` 작성 지시 추가:

```yaml
# [F-A] 투자물 장르 수치 검산 필드
투자물 장르일 경우, state_constraints에 investment_calc 필드를 반드시 포함하라:
- transactions: 이 Arc에서 발생하는 모든 투자 거래를 배열로 기록
  - entry_price: 매수 시점 가격 (달러 등 원자산 단위)
  - exit_price: 청산 시점 가격 (미청산이면 0)
  - leverage: 레버리지 배수 (없으면 1)
  - principal: 투자 원금 (원화 원 단위)
  - stated_profit: 서술한 수익금 (원화 원 단위, 손실은 음수)
- final_cash: Arc 종료 시 현금 (원 단위)
- final_total_assets: Arc 종료 시 총자산 (원 단위)

[검산 공식] 수익 = 원금 x (청산가 - 진입가) / 진입가 x 레버리지배수
stated_profit은 이 공식의 결과와 일치해야 한다.
```

### 2-3. ~~`modules/core/genre_schema_builder.py`~~ → 수정 불필요

> **감리 2차 결론**: `genre_schema_builder.py`는 프롬프트 텍스트 스니펫을 반환하는 함수이며, Gemini `response_schema` 객체를 조작하지 않음. `investment_calc`는 `response_schemas.py`(§2-1)에 직접 추가하면 LLM이 구조화 필드로 반환하므로 충분. 비투자물 장르에서 `investment_calc`는 optional이라 무시됨.

### 2-4. 조건

- `investment_calc`는 **투자물 장르 전용**, optional 필드
- 비투자물 장르에서는 스키마에 포함하지 않음
- LLM이 미작성 시 → Step F-1이 tactical_doc regex 폴백으로 처리

---

## 3. Step F-1 — InvestmentArithmeticChecker (Python-only)

### 3-1. 신규 파일: `modules/core/investment_arithmetic_checker.py`

```python
class InvestmentArithmeticChecker:
    """
    [Codex F-1] 투자물 장르 수치 Python 역산 검증기.

    Arc의 investment_calc 구조화 필드 또는 tactical_doc 자유 서술에서
    투자 거래를 추출하고 산술 검산. LLM 0회, advisory-only.
    """

    def __init__(self, tolerance: float = 0.15):
        """
        Args:
            tolerance: 허용 괴리율 (기본 15%). 초과 시 advisory 생성.
        """

    def check(
        self,
        arc: dict,
        arc_no: int,
        *,
        prev_arc_end_state: dict | None = None,
    ) -> list[dict]:
        """
        Arc의 투자 수치를 Python으로 검산.

        Returns:
            list[dict]: [{"check": "investment_arithmetic", "severity": "MAJOR"/"MINOR", "text": "..."}]
        """
```

### 3-2. 검사 항목 (5개)

| # | 검사 | 로직 | severity |
|---|------|------|----------|
| 1 | **레버리지 수익 역산** | `expected = principal × (exit-entry)/entry × leverage`. `\|stated - expected\| / expected > tolerance` → 경고 | MAJOR |
| 2 | **현금 내역 합산** | `prev_cash + Σ(회수액) - Σ(신규투자) = final_cash`. 괴리 > 5% → 경고 | MAJOR |
| 3 | **총자산 합산** | `final_cash + Σ(포지션 평가액) = final_total_assets`. 괴리 > 5% → 경고 | MAJOR |
| 4 | **Arc 경계 자본 연속성** | `prev_arc_end_state.total_assets == current_arc_start_state.total_assets`. 괴리 > 1% → 경고 | CRITICAL |
| 5 | **레버리지 배수 합리성** | leverage > 10 또는 < 1(매도 아닌 경우) → 경고 | MINOR |

### 3-3. regex 폴백 (investment_calc 미작성 시)

tactical_doc 자유 서술에서 추출:

```python
# 진입/청산가 패턴
_PRICE_RE = re.compile(
    r"(\d[\d,.]*)\s*달러.*?(\d[\d,.]*)\s*달러",
    re.DOTALL,
)

# 레버리지 패턴
_LEVERAGE_RE = re.compile(r"(\d+)\s*배\s*레버리지|레버리지\s*(\d+)\s*배")

# 원금 패턴 (한국어 금액)
_PRINCIPAL_RE = re.compile(r"(\d[\d,.]*)\s*(?:억|만)\s*(?:원)?\s*(?:매수|투자|진입|증거금)")

# 수익 패턴
_PROFIT_RE = re.compile(r"(?:수익|이익|확정)\s*(?:약\s*)?(\d[\d,.]*)\s*(?:억|만)\s*원")
```

추출 실패 시 → 해당 검사 스킵 (비차단).

### 3-4. 반환 포맷

기존 NC-1과 동일:
```python
{
    "check": "investment_arithmetic",
    "severity": "MAJOR",  # CRITICAL / MAJOR / MINOR
    "text": "[F-1] Arc 4 Ep.17: 금 1/3 청산 수익 과대. 620→680달러 × 3배 × 5억 = 수익 1.45억 (서술: 5억, 괴리 245%)"
}
```

---

## 4. Step F-2 — InvestmentMathVerifier (Flash LLM 1회)

### 4-1. 신규 파일: `modules/core/investment_math_verifier.py`

```python
class InvestmentMathVerifier:
    """
    [Codex F-2] 투자물 수치 Flash LLM 검산 에이전트.

    Python 역산 결과 + Arc 전문을 Flash에 전달하여:
    1. Python이 놓친 자유 서술 수치 추출 + 검산
    2. "횡보" 같은 서술과 수치 변동의 의미 모순 판단
    3. 현금 흐름 전체 추적 (에피소드 단위)

    Flash 1회 호출. advisory-only.
    """

    def __init__(self, llm_ask: Callable[[str], str] | None = None):
        """
        Args:
            llm_ask: Flash LLM 호출 콜백. None이면 검사 스킵.
        """

    def verify(
        self,
        tactical_doc: str,
        python_results: list[dict],
        arc_no: int,
        *,
        genre: str = "investment",
    ) -> list[dict]:
        """
        Flash LLM 1회 호출로 종합 검산.

        Returns:
            list[dict]: [{"check": "investment_math_llm", "severity": ..., "text": ...}]
        """
```

### 4-2. Flash 프롬프트

```yaml
# config/prompts/investment_math_verifier.yaml

VERIFY_PROMPT: |
  당신은 투자 소설의 수치 검산 전문가입니다.

  [Arc 전문]
  {tactical_doc}

  [Python 검산 결과]
  {python_results}

  다음을 수행하세요:

  1. **수치 추출**: Arc 전문에서 모든 투자 거래를 추출하세요.
     - 자산명, 진입가, 청산가, 레버리지, 원금, 서술된 수익

  2. **산술 검산**: 각 거래에 대해 다음 공식으로 검산하세요.
     수익 = 원금 × (청산가 - 진입가) / 진입가 × 레버리지배수
     서술된 수익과 계산 결과의 괴리율을 보고하세요.

  3. **현금 흐름 추적**: 에피소드 순서대로 현금 잔고를 추적하세요.
     이전 현금 + 회수액 - 신규 투자 = 다음 현금
     서술된 현금과 계산 결과의 괴리를 보고하세요.

  4. **서술-수치 정합성**: 다음 모순이 있는지 확인하세요.
     - "횡보/보합/정체" 서술인데 자산이 10%+ 변동
     - "급등/폭등" 서술인데 자산 변동 5% 미만
     - "소폭/미미한" 서술인데 수억 원 변동

  5. **Python 결과 확인**: Python이 보고한 괴리가 정당한지 판단하세요.
     - Python이 놓친 추가 오류가 있으면 보고하세요.
     - Python 오탐(false positive)이 있으면 "FP" 표시하세요.

  JSON 배열로 응답하세요:
  ```json
  [
    {
      "ep_no": 17,
      "issue": "금 1/3 청산 수익 과대",
      "expected": "1.45억",
      "stated": "5억",
      "severity": "MAJOR",
      "category": "leverage_calc"
    }
  ]
  ```

  category 종류: leverage_calc, cash_flow, total_assets, narrative_mismatch, python_fp
  severity 종류: CRITICAL, MAJOR, MINOR

  오류가 없으면 빈 배열 []을 반환하세요.
```

### 4-3. JSON 파싱

WritingDirectiveGenerator 패턴 참조 — 3-step fallback:
1. 전체 JSON 파싱
2. `[...]` 범위 추출 파싱
3. 실패 → 빈 리스트 반환 (비치명)

### 4-4. 호출 방식

```python
# Stage 2 배선에서:
def _flash_ask(prompt: str) -> str:
    """Flash 모델 1회 호출 콜백."""
    return gemini_call(prompt, model=AIModels.FLASH)

verifier = InvestmentMathVerifier(llm_ask=_flash_ask)
llm_results = verifier.verify(tactical_doc, python_results, arc_no)
```

---

## 5. Step F-3 — Stage 2 배선

> **감리 1차 P0 수정**: 배선 위치를 `stage2_validation_pipeline.py`에서 `four_phase_arc_generator.py`로 변경. NC-1 `check_tactical_doc()`은 Stage 2에 없음. 실제 advisory 주입 경로는 Phase 2.55 NS-3-B 직후 → `compare_and_select_arc(advisory=...)`.

### 5-1. 파일: `modules/domain/agents/four_phase_arc_generator.py`

Phase 2.55 (NS-3-B) 직후, Phase 2.6 (`compare_and_select_arc`) 직전에 F-1 + F-2 삽입.

> **감리 2차 P1 수정**: (1) `prev_end_state` → `prev_arcs[-1]`에서 추출. (2) 복수 후보(all_candidates) 전수 검사 — NS-3-B 패턴과 동일. (3) `genre_schema_builder.py` 수정 불필요 → §2-3 삭제, `response_schemas.py` 직접 추가로 충분. (4) `stage2_context.py` 슬롯 불필요 → inline 생성.

```python
# Phase 2.55 — 기존 NS-3-B advisory (all_candidates 순회)
ns3b_advisory = ""
for _cand in all_candidates:
    _adv = _check_arc_vs_block_targets(_cand, curr_block, arc_no)
    if _adv:
        ns3b_advisory += _adv + "\n"

# Phase 2.56 — [F] 투자물 수치 검산 (투자물 장르 전용, 후보별 전수)
investment_advisory = []
if self._genre == "investment":
    from modules.core.investment_arithmetic_checker import InvestmentArithmeticChecker
    _f1 = InvestmentArithmeticChecker.from_yaml()  # validation.yaml에서 임계값 로드

    # prev_arc_end_state 추출: prev_arcs가 있으면 마지막 Arc의 arc_end_state
    _prev_end = {}
    if prev_arcs:
        _prev_end = prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {})

    # 각 후보별 F-1 검사
    for _idx, _cand in enumerate(all_candidates):
        _td = _cand.get("tactical_doc", "")
        _f1_results = _f1.check(_cand, arc_no, prev_arc_end_state=_prev_end)

        # [F-2] Flash 검산 (F-1 결과 + tactical_doc)
        if self._flash_ask is not None and _f1_results:
            from modules.core.investment_math_verifier import InvestmentMathVerifier
            _f2 = InvestmentMathVerifier(llm_ask=self._flash_ask)
            _f2_results = _f2.verify(_td, _f1_results, arc_no)
            _f1_results.extend(_f2_results)

        # 후보 태깅
        for _r in _f1_results:
            _r["candidate_idx"] = _idx
        investment_advisory.extend(_f1_results)
```

### 5-1b. Flash 콜백 DI 경로

> **감리 1차 P1 수정**: `_flash_ask` 콜백의 주입 경로를 명시.

`four_phase_arc_generator.py`의 `__init__`에 `flash_ask` 파라미터 추가:

```python
def __init__(self, ..., flash_ask: Callable[[str], str] | None = None):
    self._flash_ask = flash_ask
```

호출자 (`arc_ensemble.py` 또는 `stage2_orchestrator.py`)에서 DI:

```python
# arc_ensemble.py 또는 stage2_orchestrator.py에서:
from modules.core.constants import AIModels

def _make_flash_ask():
    """Flash 모델 1회 호출 콜백 생성."""
    def _ask(prompt: str) -> str:
        return gemini_generate(prompt, model=AIModels.FLASH)
    return _ask

generator = FourPhaseArcGenerator(..., flash_ask=_make_flash_ask())
```

`validation.yaml`의 `investment_math.flash_enabled: false`이면 `flash_ask=None` 전달 → F-2 스킵.

### 5-2. Director advisory 주입

기존 `compare_and_select_arc(advisory=...)` 파라미터에 합산:

```python
# Phase 2.6 — 기존 NS-3-B advisory + F advisory 합산
all_advisory = ns3b_advisory
if investment_advisory:
    formatted = _format_investment_advisory(investment_advisory)
    all_advisory += "\n" + formatted

director.compare_and_select_arc(
    candidates=candidates,
    arc_no=arc_no,
    ...,
    advisory=all_advisory,
)
```

### 5-3. advisory 포맷팅

```python
def _format_investment_advisory(results: list[dict]) -> str:
    """F-1/F-2 결과를 Director advisory 문자열로 포맷."""
    if not results:
        return ""
    lines = ["[MAJOR · InvestmentMathVerifier] 투자 수치 검산 결과:"]
    for r in results:
        severity = r.get("severity", "MINOR")
        text = r.get("text", r.get("issue", ""))
        lines.append(f"  [{severity}] {text}")
    return "\n".join(lines)
```

---

## 6. DI / 설정 외부화

### 6-1. validation.yaml 추가

```yaml
investment_math:
  python_tolerance: 0.15        # F-1 괴리 허용률 (15%)
  cash_tolerance: 0.05          # 현금 합산 허용률 (5%)
  total_assets_tolerance: 0.05  # 총자산 합산 허용률 (5%)
  arc_boundary_tolerance: 0.01  # Arc 경계 자본 허용률 (1%)
  max_leverage: 10              # 레버리지 상한
  flash_enabled: true           # F-2 Flash 호출 활성화
```

### 6-2. ~~Stage2Context 확장~~ → 불필요

> **감리 2차 결론**: §5-1에서 `InvestmentArithmeticChecker`와 `InvestmentMathVerifier`를 Phase 2.56에서 inline 생성하므로 `Stage2Context` 슬롯 추가 불필요. `FourPhaseArcGenerator`는 `Stage2Context`를 경유하지 않고 자체 `context`를 사용.

---

## 7. 테스트 계획

### 7-1. F-1 Python 역산 (12개)

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | 정상 거래 (괴리 0%) | advisory 0건 |
| 2 | 수익 과대 (괴리 30%) | MAJOR advisory |
| 3 | 현금 합산 불일치 | MAJOR advisory |
| 4 | 총자산 합산 불일치 | MAJOR advisory |
| 5 | Arc 경계 자본 불연속 | CRITICAL advisory |
| 6 | 레버리지 > 10 | MINOR advisory |
| 7 | investment_calc 미작성 → regex 폴백 | 정상 추출 |
| 8 | regex 추출 실패 → 비차단 | advisory 0건, 에러 없음 |
| 9 | entry_price = 0 (ZeroDivision 방어) | advisory 0건, 에러 없음 |
| 10 | entry_price = exit_price (수익 0) | advisory 0건 (정상) |
| 11 | 음수 수익 (공매도/손실) | stated_profit < 0 정상 처리 |
| 12 | 단위 혼용 (억/만/원) | parse_num 정확한 변환 |

### 7-2. F-2 Flash 검산 (5개)

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | 정상 Arc + Python 0건 | LLM도 0건 |
| 2 | "횡보" + 큰 수익 | narrative_mismatch MAJOR |
| 3 | Python FP 판정 | category=python_fp |
| 4 | llm_ask=None → 스킵 | advisory 0건 |
| 5 | JSON 파싱 실패 → 비차단 | 빈 리스트 |

### 7-3. 통합 배선 (4개)

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | 투자물 장르 → F-1+F-2 실행 | advisory Director에 도달 |
| 2 | 비투자물 장르 → F 스킵 | advisory 0건 |
| 3 | projects/0001 Arc 4 재현 | P0 감지 (수익 5억 vs 1.45억) |
| 4 | flash_enabled=false → F-2 스킵 | F-1만 실행 |

### 7-4. 회귀 테스트

기존 3,614 passed 유지 확인.

---

## 8. 수정 파일 목록

| 파일 | 변경 내용 | 신규/수정 |
|------|----------|----------|
| `modules/core/investment_arithmetic_checker.py` | F-1 Python 역산 검증기 | **신규** |
| `modules/core/investment_math_verifier.py` | F-2 Flash 검산 에이전트 | **신규** |
| `config/prompts/investment_math_verifier.yaml` | Flash 프롬프트 | **신규** |
| `modules/core/response_schemas.py` | investment_calc 스키마 추가 | 수정 |
| ~~`modules/core/genre_schema_builder.py`~~ | ~~투자물 장르 investment_calc 동적 추가~~ | **불필요** (감리 2차) |
| `config/prompts/analyst.yaml` | investment_calc 작성 지시 + 검산 공식 | 수정 |
| `modules/domain/agents/four_phase_arc_generator.py` | Phase 2.56 F-1+F-2 호출 배선 + `__init__` flash_ask DI | 수정 |
| `modules/domain/agents/arc_ensemble.py` (또는 `stage2_orchestrator.py`) | flash_ask 콜백 생성 및 DI 주입 | 수정 |
| `config/settings/validation.yaml` | investment_math 섹션 추가 | 수정 |
| ~~`modules/core/stage2_context.py`~~ | ~~슬롯 추가~~ | **불필요** (감리 2차) |
| `tests/test_investment_arithmetic_checker.py` | F-1 테스트 12개 | **신규** |
| `tests/test_investment_math_verifier.py` | F-2 테스트 5개 | **신규** |
| `tests/test_investment_math_wiring.py` | 통합 배선 테스트 4개 | **신규** |

---

## 9. 실행 순서

```
Step 1: response_schemas.py + analyst.yaml
        → investment_calc 스키마 및 프롬프트 추가

Step 2: investment_arithmetic_checker.py + 테스트 12개
        → Python 역산 검증기 구현 + 단위 테스트

Step 3: investment_math_verifier.yaml + investment_math_verifier.py + 테스트 5개
        → Flash 검산 에이전트 구현 + 단위 테스트

Step 4: four_phase_arc_generator.py + arc_ensemble.py + validation.yaml
        → Phase 2.56 배선 + flash_ask DI + 설정 외부화 + 통합 테스트 4개

Step 5: 회귀 테스트 (pytest tests/ -q → 3,614+ passed)

Step 6: 감리 3회
```

---

## 10. 리스크 및 제약

| 리스크 | 대응 |
|--------|------|
| LLM이 investment_calc 필드를 채우지 않음 | regex 폴백으로 tactical_doc에서 추출. 둘 다 실패 시 비차단 |
| Flash 산술도 틀림 | Python 역산(F-1)이 1차 방어선. Flash(F-2)는 서술-수치 의미 모순 감지 전담 |
| 비투자물 장르에 오작동 | 장르 체크로 투자물만 활성화. `self._genre == "investment"` 가드 (단일 키, dead branch 없음) |
| 프롬프트 토큰 증가 | tactical_doc 최대 ~3,000자, Flash 비용 ~$0.02/Arc |
| advisory 과다 → Director 노이즈 | MINOR는 3건 이상일 때만 합산 표시. CRITICAL/MAJOR만 개별 표시 |
| Stage 4 원고 수치 검증 중복 | Stage 4는 기존 NC-1 `_check_leverage_return_pct`가 원고 본문 대상 커버. F는 Stage 2 Arc tactical_doc 대상으로 보완적 역할. 중복 아님 |

---

## 11. 성공 기준

1. projects/0001 Arc 4~5 **P0 5건 전량 감지** (Python + Flash 합산)
2. 비투자물 장르에서 **오작동 0건**
3. 기존 테스트 **3,614+ passed** 유지
4. Flash 비용 **Arc당 $0.03 이하**
5. 감리 3회 PASS
