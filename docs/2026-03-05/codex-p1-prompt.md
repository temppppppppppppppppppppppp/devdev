# Codex P1 구현 오더

## 지시

`docs/2026-03-05/TF-LLM-ease-accuracy-improvement-spec.md`의 "코덱스 구현 오더" 섹션을 읽고,
**P1 오더 3건(TF-C, TF-G, TF-I)** 을 순서대로 구현하세요.

권장 순서: **TF-G → TF-I → TF-C** (독립 2건 먼저, 의존성 있는 TF-C 마지막)

---

## 대원칙 (CLAUDE.md 발췌 — 절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python 코드가 "이건 오류니까 감점" 같은 판단을 하면 안 됨.
2. **디렉터 주권주의** — Director(LLM)가 최종 품질 결정권. Python이 Director를 우회하면 안 됨.
3. **사망 캐릭터 금지 표현은 유지** — "사망 NPC 행동/대사 등장 금지" 같은 핵심 금지는 건드리지 마세요.

---

## 오더별 핵심 요약

---

### 오더 1: TF-G — Self-Critique 게이트 검사

**의존성**: 없음 (독립 실행 가능)

**변경 파일**: `modules/domain/agents/chief_writer_quality.py`

**할 일**:

`apply_self_critique()` (L67)의 `for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):` 루프 **직전**에 게이트 검사 블록 삽입.

현재 구조 (삽입 위치 참고용):
```python
current_manuscript = manuscript
total_issues_fixed = 0

# [V60.82] 조기 스킵 조건 - Rubric 점수로 사전 평가
rubric_score = self._evaluate_with_rubric(...)
...

for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):  # ← 이 직전에 삽입
```

**삽입할 코드**:
```python
# ── [TF-G] 게이트 검사: ending_hook + 분량 (severity="low" 탈출 방지) ──
_gate_issues: list[str] = []
if blueprint:
    _eh_issues = self._check_ending_hook_presence(current_manuscript, blueprint)
    if _eh_issues:
        _gate_issues.extend(_eh_issues)
if len(current_manuscript) < 5000:
    _gate_issues.append(f"분량 부족 ({len(current_manuscript)}자 < 5,000자)")

if _gate_issues:
    logging.info("[TF-G] 게이트 검사 실패 %d건: %s", len(_gate_issues), _gate_issues)
    try:
        current_manuscript = self._fix_issues(
            current_manuscript,
            {"issues": [{"severity": "high", "issue": g} for g in _gate_issues]},
            hud_report,
            genre_name,
        )
        total_issues_fixed += len(_gate_issues)
    except Exception as _ge:
        logging.warning("[TF-G] 게이트 수정 실패 (비치명): %s", _ge)
```

**주의**:
- `_fix_issues()` 시그니처를 반드시 먼저 읽고, 두 번째 인자 형식을 실제 시그니처에 맞게 전달
- 게이트 블록은 self-critique 루프 **밖** — 루프 내부 로직은 변경하지 말 것
- 게이트 실패 시 `except` 로 비치명 처리 — 예외가 나도 루프 진행

**검증**:
```bash
python -m py_compile modules/domain/agents/chief_writer_quality.py
pytest tests/ -q
```

**수용 기준**:
- [ ] ending_hook 미포함 시 게이트에서 수정 1회 시도 후 루프 진행
- [ ] 분량 5,000자 미만 시 게이트에서 수정 1회 시도 후 루프 진행
- [ ] 기존 self-critique 루프 (MAX_CRITIQUE_ROUNDS=3) 미변경
- [ ] 게이트 수정 실패 시 비치명 (`except`) — 루프 계속 진행

---

### 오더 2: TF-I — 피드백 전달 경로 명확화

**의존성**: 없음 (독립 실행 가능)

**변경 파일**: `modules/core/stage4_interview_round.py`

**할 일**:

`run()` 메서드에서 `_build_common_writer_kwargs()` 호출 직후 `_common_writer_kwargs` dict에 `director_feedback` 키를 추가합니다.

현재 코드 (참고용):
```python
# L269 근방:
mandatory_context, _common_writer_kwargs = self._build_common_writer_kwargs(...)
```

**삽입할 코드** (위 줄 직후):
```python
# [TF-I] Director 피드백을 common_writer_kwargs에 명시 전달
if director_feedback and director_feedback.strip():
    _common_writer_kwargs["director_feedback"] = director_feedback
```

**주의**:
- `director_feedback`은 `run()` 메서드 파라미터로 받아옴 (L215 시그니처 확인)
- 기존 PromptWeighter 경로 (`_weighted_injection` 관련 블록 L299-302)는 **절대 건드리지 말 것** — 이중 전달이지만 독립 경로, 충돌 없음
- `_build_common_writer_kwargs()` 시그니처 미변경

**검증**:
```bash
python -m py_compile modules/core/stage4_interview_round.py
pytest tests/test_pipeline_wiring.py -v
pytest tests/ -q
```

**수용 기준**:
- [ ] `_common_writer_kwargs["director_feedback"]` 키 존재 (director_feedback 비어있지 않을 때)
- [ ] 기존 PromptWeighter 주입 경로 (L299-302) 미변경
- [ ] `_build_common_writer_kwargs()` 시그니처 미변경

---

### 오더 3: TF-C — 스키마-프롬프트-규칙 3중 정합

**의존성**: TF-A 완료 후 실행 권장 (P0에서 완료됨 — NO-OP 재분류되어 실제 변경 없음. 독립 실행 가능)

**변경 1: `config/prompts/director.yaml`**

아래 2가지 지시 문구를 톤 다운합니다. **반드시 현재 파일을 먼저 읽어서 정확한 문구를 확인한 후 변경**하세요.

- NC-3 `consistency_checklist` 관련 지시:
  - 현재: "반드시 입력" (또는 유사 표현)
  - 변경: "가능하면 작성하세요. 미작성 시 별도 감점 없습니다"

- NC-1 `numeric_consistency_review` 관련 지시:
  - 현재: "각 항목에 AGREE/DISMISS로 반드시 응답" (또는 유사 표현)
  - 변경: "Python advisory를 참고하여 continuity_contradiction 점수에 직접 반영하세요. numeric_consistency_review 응답은 선택사항입니다"

YAML 수정 후 반드시 파싱 검증:
```bash
python -c "import yaml; yaml.safe_load(open('config/prompts/director.yaml', encoding='utf-8'))"
```

**변경 2: `modules/domain/agents/director_ensemble.py`**

**NC-1 AGREE 자동감점 블록 (L917-935) 수정**:

현재:
```python
if _nc_agree_count > 0:
    logging.warning("[NC-1] Director가 %d건 수치 모순 인정 → continuity_contradiction 감점 강제", _nc_agree_count)
    _sb = result.get("score_breakdown", {})
    if isinstance(_sb, dict):
        _cc_score = _sb.get("continuity_contradiction", 40)
        if isinstance(_cc_score, int | float):
            _cc_cap = max(0, 40 - _nc_agree_count * 8)
            if _cc_score > _cc_cap:
                logging.info("[NC-1] continuity_contradiction %d → %d (AGREE %d건)", ...)
                _sb["continuity_contradiction"] = _cc_cap
                _new_total = sum(v for v in _sb.values() if isinstance(v, int | float))
                if _new_total < score:
                    score = _new_total
```

변경 (자동감점 제거, 로깅만 유지):
```python
if _nc_agree_count > 0:
    # [TF-C] 자동감점 제거 — Director 주권 존중 (대원칙 3)
    # Director가 AGREE 시 continuity_contradiction에 직접 반영했을 것으로 간주
    logging.warning(
        "[NC-1] Director가 %d건 수치 모순 인정. "
        "continuity_contradiction에 직접 반영 여부는 Director 자율.",
        _nc_agree_count,
    )
```

**NC-1 미응답 감점 블록 (L943-957) 제거**:

현재:
```python
else:
    _mc = mandatory_context or ""
    if "[NumericConsistency" in _mc and "[NC-" in _mc:
        logging.warning("[NC-1] Director가 numeric_consistency_review를 생략함 — python_warnings 감점")
        _sb = result.get("score_breakdown", {})
        if isinstance(_sb, dict):
            _pw = _sb.get("python_warnings", 10)
            if isinstance(_pw, int | float) and _pw > 5:
                _sb["python_warnings"] = 5
                _new_total = sum(v for v in _sb.values() if isinstance(v, int | float))
                if _new_total < score:
                    score = _new_total
```

변경 (감점 제거, 로깅만):
```python
else:
    _mc = mandatory_context or ""
    if "[NumericConsistency" in _mc and "[NC-" in _mc:
        # [TF-C] 미응답 감점 제거 — Director 주권 존중 (선택사항으로 변경)
        logging.debug("[NC-1] Director가 numeric_consistency_review를 생략함 (선택사항, 감점 없음)")
```

**변경 3: `modules/core/response_schemas.py`**

`DIRECTOR_AUDIT_SCHEMA` (L136-138)의 `fix_scope_reasoning` description에 "(미작성 시 빈 문자열 허용)" 추가:

현재:
```python
"fix_scope_reasoning": types.Schema(
    type=types.Type.STRING,
    description="fix_scope 판단 근거: 어떤 문제의 조합이 이 수정 범위를 요구하는지 한 문장",
),  # [V73]
```

변경:
```python
"fix_scope_reasoning": types.Schema(
    type=types.Type.STRING,
    description="fix_scope 판단 근거: 어떤 문제의 조합이 이 수정 범위를 요구하는지 한 문장 (미작성 시 빈 문자열 허용)",
),  # [V73][TF-C]
```

같은 필드가 `STRATEGIC_AUDIT_SCHEMA` (L175 근방)에도 있으면 동일하게 적용.

**테스트 기대값 업데이트**:

`tests/test_numeric_consistency_checker.py` 또는 `tests/test_nc3_checklist.py`에서
NC-1 AGREE 시 감점 기대값 (cc_cap 계산)이 있는 테스트를 찾아 **감점 없음** 기준으로 수정.

```bash
pytest tests/test_numeric_consistency_checker.py -v
pytest tests/test_nc3_checklist.py -v
pytest tests/ -q
```

**수용 기준**:
- [ ] NC-1 AGREE 시 `_cc_cap` 강제 미적용 (자동감점 0, 로깅만 유지)
- [ ] NC-1 미응답 시 `python_warnings` 감점 없음 (debug 로그만)
- [ ] director.yaml NC-1/NC-3 지시가 "선택사항" 톤으로 변경됨
- [ ] response_schemas.py `fix_scope_reasoning` description에 미작성 허용 명시
- [ ] YAML 파싱 에러 없음
- [ ] 관련 테스트 기대값 업데이트 완료

---

## ⚠️ 인코딩 주의 (최우선)

이 프로젝트의 YAML/Python 파일은 **전량 UTF-8 (BOM 없음)** 입니다.

**필수 규칙**:
1. **파일 읽기/쓰기 시 반드시 UTF-8 인코딩 유지** — 한글 YAML 파일은 latin-1/cp949 읽으면 즉시 깨짐.
2. **BOM 삽입 금지** — `PromptLoader`가 BOM 처리 불가.
3. **줄바꿈: LF (`\n`)** — CRLF 변환 금지.
4. **수정 후 반드시 검증**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/prompts/director.yaml', encoding='utf-8'))"
   ```

---

## 검증 (전체)

```bash
# 구문 검사
python -m py_compile modules/domain/agents/chief_writer_quality.py
python -m py_compile modules/core/stage4_interview_round.py
python -m py_compile modules/domain/agents/director_ensemble.py
python -m py_compile modules/core/response_schemas.py

# YAML 파싱
python -c "import yaml; yaml.safe_load(open('config/prompts/director.yaml', encoding='utf-8'))"

# 단위 테스트
pytest tests/test_numeric_consistency_checker.py -v
pytest tests/test_nc3_checklist.py -v
pytest tests/test_pipeline_wiring.py -v

# 전체 테스트
pytest tests/ -q
```

**기준선: 3,348 passed**. 이보다 줄어들면 안 됨.
TF-C 테스트 기대값 변경으로 일부 테스트가 수정될 수 있음 — passed 수 자체가 유지되면 OK.

---

## 커밋

TF별 1커밋:
```
feat(TF-G): Self-Critique 게이트 검사 — ending_hook+분량 루프 전 사전 수정
feat(TF-I): 피드백 전달 경로 명확화 — common_writer_kwargs에 director_feedback 추가
feat(TF-C): 스키마-프롬프트-규칙 3중 정합 — NC-1/NC-3 Director 주권 존중 (자동감점 제거)
```

---

## 참고 파일

- **명세 전문**: `docs/2026-03-05/TF-LLM-ease-accuracy-improvement-spec.md` (오더 4~6 섹션)
- **P0 결과**: `docs/2026-03-05/codex-p0-prompt.md` (TF-D/E/A 완료 상태 확인)
- **CLAUDE.md**: 대원칙 + 현재 상태
- **주요 변경 대상**:
  - `modules/domain/agents/chief_writer_quality.py` (TF-G — 게이트 삽입)
  - `modules/core/stage4_interview_round.py` (TF-I — director_feedback dict 추가)
  - `config/prompts/director.yaml` (TF-C — NC-1/NC-3 톤 조절)
  - `modules/domain/agents/director_ensemble.py` (TF-C — 자동감점 제거)
  - `modules/core/response_schemas.py` (TF-C — fix_scope_reasoning description)
  - `tests/test_numeric_consistency_checker.py` + `tests/test_nc3_checklist.py` (TF-C 기대값)
