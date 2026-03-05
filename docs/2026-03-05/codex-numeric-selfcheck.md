# Codex Order: 전장르 수치 자기검증 (Numeric Self-Verification) — Stage 2/3/4

**작업 ID**: NS-1 (Stage 2/3/4 자기검증) + NS-1-P (PWF inplace 갭) + NS-2 (Block-WorldState 수치 교차검증)
**우선순위**: P0
**대상 파일**:
- `config/prompts/analyst.yaml` (Stage 2, NS-1)
- `config/prompts/blueprint_generator.yaml` (Stage 3, NS-1)
- `modules/domain/agents/chief_writer_quality.py` (Stage 4, NS-1)
- `modules/core/stage2_finalizer.py` (NS-1-P: inplace 갭, NS-2: Block-WorldState)
- `tests/` 내 적합한 파일 또는 `tests/test_numeric_selfcheck.py` 신규 생성

**테스트 기준선**: 3,351 passed (실패 없이 유지)

---

## 배경 및 문제

Arc 2 생성 시 LLM이 전술서에 **"WTI 원유 롱 포지션 600억 × 약 17.2% 상승 → 451억 수익"** 기술.
실제 계산: 600억 × 0.172 = **103.2억**. Director가 올바르게 REJECT했으나,
자기비판(Phase 4 Self-Critic) 단계에서 이미 통과됨 → 불필요한 Director REJECT 사이클 소모.

동일한 패턴이 Stage 3(Blueprint) 및 Stage 4(원고)에서도 독립적으로 발생 가능.

---

## 전체 아키텍처

```
Stage 2 Arc 생성
  └─ ANALYST_SELF_CRITIC_PROMPT (LLM) → 항목 7 강화 [NS-1-S2]
       "tactical_doc 내 모든 산술 표현 추출 → 단계별 재계산 → 5% 초과 시 FAIL"

Stage 3 Blueprint 생성
  └─ BLUEPRINT_PREFLIGHT_VALIDATE_PROMPT (LLM) → 항목 6 추가 [NS-1-S3]
       "blueprint scene 내 산술 표현 추출 → 재계산 → high severity로 FAIL"

Stage 4 원고 작성
  └─ chief_writer_quality._self_critique() (Python) → check 9 추가 [NS-1-S4]
       "_check_arithmetic_consistency(content) → 오류 시 issues에 추가 → CW 재작성 유도"
```

---

## 구현 명세 — [NS-1-S2] Stage 2

### 대상: `config/prompts/analyst.yaml` — `ANALYST_SELF_CRITIC_PROMPT`

**위치**: L563–568 (항목 7 전체 교체)

**교체 전**:
```yaml
  7. **[V60.10 신규] 수치 일관성 검사**:
     - 금액/재화가 화마다 맞는가? (획득-소모=잔여 계산 확인)
     - 핵심 수치 계산이 정확한가? (30-9=21, NOT 210)
     - 부상 부위가 화마다 일관되는가? (어깨 부상이 전완부로 바뀌면 FAIL)
     - 아이템 수량 변화가 산술적으로 맞는가? (5개-3개=2개)
     - 수치 계산 오류 발견 시 즉시 FAIL 처리
```

**교체 후**:
```yaml
  7. **[NS-1] 수치 자기검증 (전장르 공통)**:

     [절차] tactical_doc 전체를 스캔하여 아래 패턴에 해당하는 모든 산술 표현을 추출하라.
     추출된 표현이 없으면 이 항목은 SKIP (PASS 처리).
     추출된 표현이 있으면 각각 단계별로 재계산하여 결과와 비교하라.

     [감지 패턴 — 장르 무관]
     - 곱셈/수익: A × B = C, A × B% = C, A × (1+r) = C
       예) "600억 × 17.2% = 103억" / "내공 500에 3배 = 1,500"
     - 나눗셈/배율: A ÷ B = C배, A / B = C
       예) "1억 ÷ 0.1억 = 10배" / "엔트리 0.05달러 → 청산 0.70달러 → 14배"
     - 덧셈/잔액: A + B = C, A - B = C
       예) "자본금 19.5억 + 이익 18억 = 37.5억"
     - 레버리지: 증거금 A × N배 = 포지션 B
       예) "증거금 20억 × 3배 = 60억 포지션"
     - 수량 변화: 보유 A개 - 소모 B개 = 잔여 C개
       예) "영약 5개 - 3개 복용 = 2개 남음"
     - 비율 구성: 전체 A의 B% = C, 또는 C / A = B%
     - 누적 성장: 시작 A → 최종 B → 수익률 (B-A)/A × 100 = C%

     [판정 기준]
     - 재계산 결과와 서술 값의 차이가 5% 이하: PASS
     - 5% 초과: 즉시 FAIL. feedback에 "수치오류: [표현] 기재=[X] 실계산=[Y]" 명시
     - 부상 부위/장소 일관성 오류도 기존대로 FAIL 처리

     [주의] 단위 혼용(억/만/원/달러) 시 단위 통일 후 계산. "약 X억" 어림값은 서술값 그대로 사용.
```

**Output Format 추가** (L570–577, `final_arc` 앞에 삽입):
```yaml
      "numeric_selfcheck": [
          {{"expr": "600억 × 17.2%", "stated": "451억", "actual": "103.2억", "ok": false}},
          {{"expr": "20억 × 3배", "stated": "60억", "actual": "60억", "ok": true}}
      ],
```
규칙: 산술 없으면 `[]`. `ok: false` 1개이상 → `status: "FAIL"` 필수.

---

## 구현 명세 — [NS-1-S3] Stage 3

### 대상: `config/prompts/blueprint_generator.yaml` — `BLUEPRINT_PREFLIGHT_VALIDATE_PROMPT`

**위치**: L36–57 (검증 항목 5개 뒤에 항목 6 추가)

**추가 내용** (L57 `위 데이터를 대조하여` 윗줄에 삽입):
```yaml
  6. **[NS-1] Blueprint 산술 자기검증**:
     blueprint의 scene 설명, 씬 요약 텍스트에 등장하는 모든 산술 표현을 추출하여
     단계별로 재계산하라. 추출된 표현이 없으면 SKIP.
     재계산 결과와 기재값의 차이가 5%를 초과하면 severity="high", passed=false.
     - 감지 패턴: A × B = C, A × B% = C, A ÷ B = C배, A ± B = C, 배율/레버리지/수량 변화
     - 단위(억/만/달러/스탯포인트 등) 통일 후 계산
     - 오류 발견 시 issues에 "산술오류: [표현] 기재=[X] 실계산=[Y]" 형식으로 추가
```

**소비자 코드 확인**: `stage3_orchestrator.py` 또는 blueprint validator 호출부에서 `passed=false` + `severity="high"` 항목이 있으면 기존 로직대로 REJECT 또는 재시도 처리됨. 코드 변경 불필요.

---

## 구현 명세 — [NS-1-S4] Stage 4

### 대상: `modules/domain/agents/chief_writer_quality.py`

#### 1. `_self_critique()` 메서드에 check 9 추가 (L235 `# [Sweep46]` 직전)

```python
# 9. [NS-1] 산술 일관성 체크 (전장르 공통)
issues.extend(self._check_arithmetic_consistency(content))
```

#### 2. `_check_arithmetic_consistency(content: str) -> list` 메서드 추가

```python
def _check_arithmetic_consistency(self, content: str) -> list:
    """
    [NS-1] 원고 내 자유형식 산술 표현 추출 → Python 재계산 → 5% 초과 오류 감지.
    NC-1(FactLedger 교차)과 상보적: NC-1은 DB 기록 대조, 이 메서드는 산문 내 표현 자체 검증.
    대원칙 준수: 산술 판단(objective math)은 Python 허용 (NC-1 선례).
    """
    import re

    issues = []
    TOLERANCE = 0.05  # 5%

    # 한국어 숫자 단위 → float 변환 헬퍼
    def to_float(s: str) -> float | None:
        s = s.strip().replace(",", "").replace(" ", "")
        multipliers = {"조": 1e12, "억": 1e8, "만": 1e4}
        for unit, mult in multipliers.items():
            if unit in s:
                num_part = s.replace(unit, "")
                try:
                    return float(num_part) * mult
                except ValueError:
                    return None
        try:
            return float(s)
        except ValueError:
            return None

    def within_tolerance(stated: float, actual: float) -> bool:
        if actual == 0:
            return stated == 0
        return abs(stated - actual) / abs(actual) <= TOLERANCE

    # 패턴 1: A × N배 = B (예: "내공 500에 3배 = 1,500" / "20억 × 3배 = 60억")
    for m in re.finditer(
        r"([\d,]+(?:\.\d+)?(?:조|억|만)?)\s*[×x\*]\s*([\d,]+(?:\.\d+)?)배\s*[=→]\s*([\d,]+(?:\.\d+)?(?:조|억|만)?)",
        content,
    ):
        a, n, c = to_float(m.group(1)), to_float(m.group(2)), to_float(m.group(3))
        if None not in (a, n, c) and not within_tolerance(c, a * n):
            issues.append({
                "type": "arithmetic_error",
                "severity": "high",
                "description": f"산술오류: {m.group(0).strip()} — 기재={m.group(3)} 실계산={a * n / 1e8:.1f}억",
            })

    # 패턴 2: A × B% = C (예: "600억 × 17.2% = 103억")
    for m in re.finditer(
        r"([\d,]+(?:\.\d+)?(?:조|억|만)?)\s*[×x\*]\s*([\d,]+(?:\.\d+)?)%\s*[=→]\s*([\d,]+(?:\.\d+)?(?:조|억|만)?)",
        content,
    ):
        a, pct, c = to_float(m.group(1)), float(m.group(2)) / 100, to_float(m.group(3))
        if None not in (a, c) and not within_tolerance(c, a * pct):
            issues.append({
                "type": "arithmetic_error",
                "severity": "high",
                "description": f"산술오류: {m.group(0).strip()} — 기재={m.group(3)} 실계산={a * pct / 1e8:.1f}억",
            })

    # 패턴 3: 레버리지 — 증거금 A × N배 레버리지 = B
    for m in re.finditer(
        r"증거금\s*([\d,]+(?:\.\d+)?(?:조|억|만)?)\s*[×x\*]\s*([\d,]+(?:\.\d+)?)배\s*레버리지?\s*[=→]\s*([\d,]+(?:\.\d+)?(?:조|억|만)?)",
        content,
    ):
        a, n, c = to_float(m.group(1)), to_float(m.group(2)), to_float(m.group(3))
        if None not in (a, n, c) and not within_tolerance(c, a * n):
            issues.append({
                "type": "arithmetic_error",
                "severity": "high",
                "description": f"레버리지 오류: {m.group(0).strip()} — 기재={m.group(3)} 실계산={a * n / 1e8:.1f}억",
            })

    return issues
```

#### 3. `apply_self_critique()` 호출 시 변경 불필요
기존 flow: `_self_critique()` → issues 수집 → severity 판단 → 이슈 있으면 CW에 피드백으로 전달 → CW 재작성.
check 9도 동일 flow에 자동 편입됨.

---

## 테스트 명세

### [NS-1-S2] Stage 2 Self-Critic 테스트 (5개)

```python
# TC-NS-S2-1: 잘못된 곱셈 → status=FAIL
def test_s2_wrong_multiplication():
    """600억 × 17.2% = 451억 → FAIL"""

# TC-NS-S2-2: 올바른 곱셈 → status=PASS
def test_s2_correct_multiplication():
    """600억 × 17.2% = 103억 → PASS"""

# TC-NS-S2-3: 산술 없는 순수 서사 → PASS, numeric_selfcheck=[]
def test_s2_no_arithmetic():

# TC-NS-S2-4: 무협 내공 배수 오류 → FAIL (500 × 3배 = 2,000, 정답 1,500)
def test_s2_wuxia_energy_error():

# TC-NS-S2-5: 레버리지 오류 → FAIL (증거금 20억 × 5배 = 120억, 정답 100억)
def test_s2_leverage_error():
```

### [NS-1-S3] Stage 3 Preflight 테스트 (3개)

```python
# TC-NS-S3-1: Blueprint scene에 산술 오류 → passed=False, severity="high"
def test_s3_blueprint_arithmetic_error():

# TC-NS-S3-2: 올바른 Blueprint → passed=True
def test_s3_blueprint_arithmetic_correct():

# TC-NS-S3-3: 산술 없는 Blueprint → passed=True, issues=[]
def test_s3_blueprint_no_arithmetic():
```

### [NS-1-S4] Stage 4 CW Self-Critique 테스트 (4개)

```python
# TC-NS-S4-1: 원고에 "600억 × 17.2% = 451억" → issues에 arithmetic_error 포함
def test_s4_cw_selfcritique_catches_multiplication_error():
    from modules.domain.agents.chief_writer_quality import ChiefWriterQuality
    qc = ChiefWriterQuality.__new__(ChiefWriterQuality)
    manuscript = "포지션 600억에서 17.2% 수익이 났다. 600억 × 17.2% = 451억 원의 수익이 실현됐다."
    issues = qc._check_arithmetic_consistency(manuscript)
    assert len(issues) > 0
    assert issues[0]["type"] == "arithmetic_error"

# TC-NS-S4-2: 올바른 계산 → issues=[]
def test_s4_cw_selfcritique_passes_correct_arithmetic():
    manuscript = "600억 × 17.2% = 103억 원의 수익이 실현됐다."
    issues = qc._check_arithmetic_consistency(manuscript)
    assert issues == []

# TC-NS-S4-3: 산술 표현 없음 → issues=[]
def test_s4_cw_selfcritique_no_arithmetic():
    manuscript = "주인공은 어둠 속에서 칼을 뽑았다."
    assert qc._check_arithmetic_consistency(manuscript) == []

# TC-NS-S4-4: _self_critique()가 check 9를 실행하여 arithmetic_error issue 생성
def test_s4_self_critique_includes_arithmetic_check():
    # check 9 호출 확인: issues에 arithmetic_error 타입 존재
```

---

## 감리 포인트

구현 완료 후 아래를 확인하라:

1. **S2**: `analyst.yaml` L563–568 교체 + Output Format `numeric_selfcheck` 추가. YAML 문법 확인: `python -c "import yaml; yaml.safe_load(open('config/prompts/analyst.yaml'))"`
2. **S3**: `blueprint_generator.yaml`에 항목 6 추가. YAML 문법 확인.
3. **S4**: `chief_writer_quality.py`에 `_check_arithmetic_consistency()` 메서드 추가 + `_self_critique()` L235 앞에 check 9 삽입.
4. **테스트**: `pytest tests/ -q` → 3,351 → 3,363 passed (+12)
5. **Ruff**: `ruff check modules/ tests/` → 0 violations
6. **회귀 없음**: 기존 analyst/chief_writer/blueprint 관련 테스트 전량 PASS

---

---

## 구현 명세 — [NS-1-P] PASS_WITH_FIX inplace 산술 검증 갭

### 배경

PASS_WITH_FIX 라우팅 (stage2_finalizer.py L272-274):
```python
if _fix_scope in ("partial", "full"):
    break  # → REJECT → retry 경로 → plan_single_arc() 재실행 → Phase 4 self-critic 재실행 ✅
# inplace: _inplace_patch_arc() → Director 재심사만 → self-critic 미실행 ❌
```

- `partial/full` PASS_WITH_FIX → retry loop → `plan_single_arc()` → Phase 4 self-critic (NS-1-S2) **자동 재실행** → 이미 커버됨, 코드 변경 불필요
- `inplace` PASS_WITH_FIX → `_inplace_patch_arc()` 패치 후 Director 재심사만 → self-critic **미실행** → 패치로 생성된 새 산술 표현 검증 안 됨 → **갭**

### 대상: `modules/core/stage2_finalizer.py`

**위치**: `_patched` 성공 확인 직후 (L294 `if not _patched: break` 이후), Director 재심사(L332) 이전

**추가 코드**:
```python
# [NS-1-P] inplace 패치 후 산술 일관성 사전 검증 (Python-only, NC-1 선례)
_tactical_patched = _patched.get("tactical_doc", "") if isinstance(_patched, dict) else ""
if _tactical_patched:
    _arith_issues = _check_tactical_arithmetic(_tactical_patched)
    if _arith_issues:
        _arith_warn = "\n".join(f"  - {i}" for i in _arith_issues)
        logging.warning("[NS-1-P] inplace 패치 후 산술 오류 감지:\n%s", _arith_warn)
        # Director 재심사 story_context에 경고 주입 (Director가 인지하도록)
        _patch_ctx += (
            f"\n\n[NS-1-P 산술 경고 — 패치 후 검출]\n{_arith_warn}\n"
            "위 항목을 재심사 시 확인하고 오류가 있으면 REJECT 처리하세요."
        )
```

**모듈 상단 (import 블록 근처) 또는 파일 내 private 함수로 추가**:
```python
def _check_tactical_arithmetic(tactical_doc: str) -> list[str]:
    """
    [NS-1-P] tactical_doc 텍스트에서 산술 표현 추출 → Python 재계산.
    5% 초과 오차 시 오류 문자열 반환. LLM 0회 (NC-1 선례).
    """
    import re

    issues = []
    TOLERANCE = 0.05

    def to_num(s: str) -> float | None:
        s = s.strip().replace(",", "")
        for unit, mult in [("조", 1e12), ("억", 1e8), ("만", 1e4)]:
            if unit in s:
                try:
                    return float(s.replace(unit, "")) * mult
                except ValueError:
                    return None
        try:
            return float(s)
        except ValueError:
            return None

    def bad(stated, actual):
        if actual == 0:
            return stated != 0
        return abs(stated - actual) / abs(actual) > TOLERANCE

    # 패턴: A × N배 = C
    for m in re.finditer(
        r"([\d,]+(?:\.\d+)?(?:조|억|만)?)\s*[×x\*]\s*([\d,]+(?:\.\d+)?)배\s*[=→]\s*([\d,]+(?:\.\d+)?(?:조|억|만)?)",
        tactical_doc,
    ):
        a, n, c = to_num(m.group(1)), to_num(m.group(2)), to_num(m.group(3))
        if None not in (a, n, c) and bad(c, a * n):
            issues.append(f"산술오류: {m.group(0).strip()} (실계산={a*n/1e8:.1f}억)")

    # 패턴: A × B% = C
    for m in re.finditer(
        r"([\d,]+(?:\.\d+)?(?:조|억|만)?)\s*[×x\*]\s*([\d,]+(?:\.\d+)?)%\s*[=→]\s*([\d,]+(?:\.\d+)?(?:조|억|만)?)",
        tactical_doc,
    ):
        a, pct, c = to_num(m.group(1)), to_num(m.group(2)) / 100.0 if to_num(m.group(2)) else None, to_num(m.group(3))
        if None not in (a, pct, c) and bad(c, a * pct):
            issues.append(f"산술오류: {m.group(0).strip()} (실계산={a*pct/1e8:.1f}억)")

    return issues
```

### 테스트 (NS-1-P, 2개)

```python
# TC-NS-P-1: inplace 패치 후 오류 있는 tactical_doc → _patch_ctx에 [NS-1-P 산술 경고] 포함
def test_pwf_inplace_arithmetic_warning_injected_to_story_context():
    """inplace 패치 결과물에 산술 오류가 있으면 Director 재심사 story_context에 경고 주입"""
    # _patched["tactical_doc"] = "600억 × 17.2% = 451억"
    # → _patch_ctx에 "[NS-1-P 산술 경고]" 포함 확인

# TC-NS-P-2: inplace 패치 후 올바른 tactical_doc → 경고 없음, 정상 재심사
def test_pwf_inplace_no_arithmetic_warning_for_correct_doc():
    # _patched["tactical_doc"] = "600억 × 17.2% = 103억"
    # → _patch_ctx에 NS-1-P 경고 없음
```

---

## 구현 명세 — [NS-2] Block-WorldState 수치 교차검증

### 배경 및 갭 확인

Treatment 블록의 `genre_ext`는 LLM 컨텍스트로만 주입됨:
- Stage 3 TF9: `emotional_beat`, `foreshadow`, `genre_ext` → Blueprint context (advisory)
- Stage 4 V74: `genre_ext` → Director MC context + "⚠️ Treatment 목표와 합리적으로 연결" 경고 (advisory)

하지만 **Python 교차검증 없음**:
- Arc PASS 후 `arc.state_constraints.arc_end_state` 수치 vs `genre_ext.capital_after` (또는 `profit_loss`) 비교 없음
- WorldState가 treatment 목표에서 크게 벗어나도 감지 안 됨
- 다음 Arc 생성 시 이전 arc 실행 결과가 treatment 기대와 다른 상태로 출발 → 연속 오류 누적

### genre_ext 수치 필드 (투자물 예시, 전장르 공통 로직 적용)

```json
{
  "capital_before": "20억",
  "capital_after": "23억 (미실현 수익 포함)",
  "capital_delta": "+3억 (미실현)",
  "profit_loss": "+3억 (미실현)"
}
```

### 대상: `modules/core/stage2_finalizer.py`

**위치**: Arc PASS 처리 직후 (refined_arc가 최종 확정된 시점), `stage2_validation_pipeline.py`에서도 동일 시점에 호출 가능

**추가 Python 함수** (모듈 내 private 함수 또는 `numeric_consistency_checker.py`에 메서드 추가):

```python
def _check_block_worldstate_alignment(
    enriched_block: dict,
    refined_arc: dict,
    arc_no: int,
    threshold_pct: float = 0.30,  # 30% 허용 오차 (서사 변동 감안)
) -> list[str]:
    """
    [NS-2] treatment block genre_ext 목표 수치 vs arc arc_end_state 수치 교차검증.
    Python-only, LLM 0회. 30% 초과 괴리 시 경고 문자열 반환 (REJECT 강제 없음 — advisory).
    """
    warnings = []
    genre_ext = enriched_block.get("genre_ext", {}) if isinstance(enriched_block, dict) else {}
    if not isinstance(genre_ext, dict):
        return warnings

    arc_end = refined_arc.get("state_constraints", {}).get("arc_end_state", {})
    if not isinstance(arc_end, dict):
        return warnings

    def extract_num(s) -> float | None:
        """'23억' → 23e8, '1.2조' → 1.2e12, '+3억' → 3e8 등"""
        if not isinstance(s, str):
            return None
        import re
        # 괄호 내용 제거, 부호 무시
        clean = re.sub(r"\([^)]*\)", "", s).strip().lstrip("+-").strip()
        for unit, mult in [("조", 1e12), ("억", 1e8), ("만", 1e4)]:
            m = re.search(r"([\d,]+(?:\.\d+)?)" + unit, clean)
            if m:
                try:
                    return float(m.group(1).replace(",", "")) * mult
                except ValueError:
                    return None
        return None

    # capital_after vs arc_end_state.total_assets (필드명 후보: total_assets, assets, capital)
    target_capital = extract_num(genre_ext.get("capital_after", ""))
    actual_capital = None
    for key in ("total_assets", "assets", "capital", "total_capital"):
        val = arc_end.get(key)
        actual_capital = extract_num(str(val)) if val is not None else None
        if actual_capital is not None:
            break

    if target_capital and actual_capital:
        divergence = abs(target_capital - actual_capital) / target_capital
        if divergence > threshold_pct:
            warnings.append(
                f"[NS-2] Arc {arc_no} 자산 괴리: treatment 목표={genre_ext['capital_after']} "
                f"vs arc_end_state={actual_capital/1e8:.1f}억 (차이={divergence*100:.0f}%)"
            )

    return warnings
```

**호출 위치**: Arc PASS 확정 시점 (stage2_finalizer.py 또는 stage2_validation_pipeline.py의 PASS 처리 블록):

```python
# [NS-2] Block-WorldState 수치 교차검증 (advisory, REJECT 없음)
_block_ws_warns = _check_block_worldstate_alignment(enriched_block, refined_arc, global_arc_no)
if _block_ws_warns:
    for _w in _block_ws_warns:
        logging.warning(_w)
    # 다음 arc 생성 시 Director가 인지하도록 story_context에 보존
    # (stage2_validation_pipeline의 _story_context_accumulator에 추가하거나 DB 로깅)
    # 최소한: warning 로그로 남겨 FailureAnalyzer가 수집
```

**주의사항**:
- REJECT 강제 없음 — 서사 상 treatment 목표를 초과 달성하거나 미달할 수 있음 (대원칙: LLM 판단)
- 30% 임계값은 `validation.yaml`에 `ns2.block_worldstate_threshold: 0.30`으로 외부화 권장
- arc_end_state에 total_assets 필드가 없는 경우 경고 없이 스킵 (장르별 필드명 차이 허용)
- 투자물 전용이 아닌 전장르 대응: 무협은 "internal_energy_after" → "arc_end_state.internal_energy", 헌터물은 "rank_after" → "arc_end_state.rank" 등 동일 패턴 적용 가능 (확장 시 `genre_ext` 키명 정규화 필요, 이번 스코프 외)

### 테스트 (NS-2, 3개)

```python
# TC-NS-2-1: genre_ext capital_after="23억" vs arc_end_state total_assets="470억" → 경고 반환
def test_ns2_large_divergence_returns_warning():
    block = {"genre_ext": {"capital_after": "23억"}}
    arc = {"state_constraints": {"arc_end_state": {"total_assets": "470억"}}}
    warns = _check_block_worldstate_alignment(block, arc, arc_no=2)
    assert len(warns) > 0
    assert "NS-2" in warns[0]

# TC-NS-2-2: 허용 범위 내 괴리 → 경고 없음
def test_ns2_small_divergence_no_warning():
    block = {"genre_ext": {"capital_after": "23억"}}
    arc = {"state_constraints": {"arc_end_state": {"total_assets": "25억"}}}  # 8.7% 괴리
    warns = _check_block_worldstate_alignment(block, arc, arc_no=2)
    assert warns == []

# TC-NS-2-3: genre_ext 없는 블록 (무협 등) → 경고 없이 스킵
def test_ns2_no_genre_ext_skips_gracefully():
    block = {"title": "무협 블록", "emotional_beat": "내공 돌파"}
    arc = {"state_constraints": {"arc_end_state": {"internal_energy": 300}}}
    warns = _check_block_worldstate_alignment(block, arc, arc_no=1)
    assert warns == []
```

---

## 감리 포인트 (전체)

구현 완료 후 아래를 전량 확인하라:

1. **NS-1-S2**: analyst.yaml 항목 7 교체 + numeric_selfcheck output 추가. YAML 파싱 이상 없음.
2. **NS-1-S3**: blueprint_generator.yaml 항목 6 추가. YAML 파싱 이상 없음.
3. **NS-1-S4**: chief_writer_quality.py `_check_arithmetic_consistency()` 추가 + check 9 삽입.
4. **NS-1-P**: stage2_finalizer.py `_check_tactical_arithmetic()` 추가 + inplace 패치 직후 호출 + `_patch_ctx` 주입.
5. **NS-2**: `_check_block_worldstate_alignment()` 추가 + Arc PASS 시점에 호출 + warning 로깅.
6. **테스트**: `pytest tests/ -q` → 3,351 → 3,368+ passed (+17)
7. **Ruff**: 0 violations
8. **회귀**: 기존 stage2/stage4 관련 테스트 전량 PASS

---

## 스코프 외 (이번 작업에 포함하지 말 것)

- NC-1 (`numeric_consistency_checker.py`) 수정 — NC-1은 Stage 4 Director advisory 담당, S4 check 9는 CW 자기검증 담당. 역할 상보적, 중복 아님
- `analyst.py` 파이썬 소비자 코드 수정 — `status`/`feedback`/`revised_arc` 읽기 로직 무변경
- `final_arc` vs `revised_arc` 키 불일치 수정 — 별도 작업
- Stage 3 validator 호출 Python 코드 수정 — `passed=false` + `severity="high"` 처리는 기존 로직 그대로
- 새로운 LLM 호출 추가 — S4/NS-1-P/NS-2는 Python-only (NC-1 선례 준수), S2/S3는 기존 LLM 호출에 프롬프트 확장만
- NS-2 genre_ext 키명 정규화 (무협 internal_energy_after, 헌터 rank_after 등) — 투자물 우선, 전장르 확장은 별도 작업
- `validation.yaml`에 `ns2.block_worldstate_threshold` 외부화 — 선택적, 구현 편의에 따라 결정
