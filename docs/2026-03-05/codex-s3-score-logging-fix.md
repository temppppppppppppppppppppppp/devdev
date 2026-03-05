# Codex 구현 오더: S3-SCORE — Stage 3 stage_attempts score 0 버그 수정

## 배경 (읽기 전용 — 수정 금지)

실파이프라인(`02_20250305`) Stage 3 Blueprint 20건 전부 PASS했으나
`stage_attempts` 테이블의 `score` 컬럼이 전부 **0**.

`quality_metrics.jsonl`에는 96~100점이 정상 기록되어 있어
두 로그 소스 간 불일치 확인.

### 근본 원인

`three_phase_blueprint_generator.py`의 정상 PASS 경로:
```python
# L423 — phases 서브딕셔너리에는 저장
pipeline_result["phases"]["generate"]["selected_score"] = _score   # ✅ 저장됨

# L442 — verdict는 저장
pipeline_result["final_verdict"] = verdict                          # ✅ 저장됨

# ⚠️ last_score는 미설정 — 오직 L653 긴급 폴백 경로에서만 세팅
pipeline_result["last_score"] = _last_score  # L653, 긴급 폴백만
```

`stage3_orchestrator.py`의 `stage_attempts` insert (PASS L733, REJECT L1012):
```python
_score = pipeline_result.get("last_score", 0)  # last_score 없으면 0 → 항상 0
```

반면 출력용 print(L683)에는 이미 올바른 폴백이 구현되어 있음:
```python
# L682-684 — 출력용은 phases 폴백 있음 (정상)
_bp_score = pipeline_result.get(
    "last_score", pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)
)
```

→ **출력(print)은 정상, DB 저장만 0**.

---

## 대원칙 (CLAUDE.md 발췌 — 절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python이 score를 임의 보정하면 안 됨. 있는 값을 올바른 키에서 읽는 것만.
2. **디렉터 주권주의** — score 값 자체 변경 없음. 기록 경로만 수정.
3. 테스트 기준선: **3,387 passed + 0 xfailed** (`pytest tests/ -q` 기준)

---

## 변경 파일 (2개)

| 파일 | 변경 내용 |
|------|----------|
| `modules/domain/agents/three_phase_blueprint_generator.py` | PASS 경로에서 `pipeline_result["last_score"]` 설정 추가 |
| `modules/core/stage3_orchestrator.py` | `stage_attempts` insert 두 곳의 `_score` 폴백 보강 (방어적 2중 수정) |

---

## 구현 스펙

### 수정 1 (근본 수정) — `three_phase_blueprint_generator.py`

**위치**: L442 `pipeline_result["final_verdict"] = verdict` 바로 다음 줄

기존:
```python
if verdict in ("PASS", "PASS_WITH_FIX"):  # [TF-32-S3]
    self.stats["phase3_pass"] += 1
    pipeline_result["final_verdict"] = verdict  # [TF-32-S3] PASS or PASS_WITH_FIX 보존
    logging.info(f"✅ [Phase 3] {verdict} - 제{ep_num}화 Blueprint 생성 완료")
    print(f"   ✅ [Phase 3] {verdict} (score={_score})")
```

변경 후:
```python
if verdict in ("PASS", "PASS_WITH_FIX"):  # [TF-32-S3]
    self.stats["phase3_pass"] += 1
    pipeline_result["final_verdict"] = verdict  # [TF-32-S3] PASS or PASS_WITH_FIX 보존
    pipeline_result["last_score"] = _score  # [S3-SCORE] stage_attempts 기록용
    logging.info(f"✅ [Phase 3] {verdict} - 제{ep_num}화 Blueprint 생성 완료")
    print(f"   ✅ [Phase 3] {verdict} (score={_score})")
```

---

### 수정 2 (방어적 수정) — `stage3_orchestrator.py` L733 (PASS 경로)

기존:
```python
_score = pipeline_result.get("last_score", 0)
if not isinstance(_score, int):
    try:
        _score = int(_score)
    except (ValueError, TypeError):
        _score = 0
```

변경 후:
```python
_score = pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)
if not isinstance(_score, int):
    try:
        _score = int(_score)
    except (ValueError, TypeError):
        _score = 0
```

---

### 수정 3 (방어적 수정) — `stage3_orchestrator.py` L1012 (REJECT 경로)

기존:
```python
_score = pipeline_result.get("last_score", 0)
if not isinstance(_score, int):
    try:
        _score = int(_score)
    except (ValueError, TypeError):
        _score = 0
```

변경 후:
```python
_score = pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)
if not isinstance(_score, int):
    try:
        _score = int(_score)
    except (ValueError, TypeError):
        _score = 0
```

---

## 구현 시 주의사항

1. **`_score` 값 자체를 바꾸지 말 것** — `blueprint_generator` 내부에서 이미 계산된 `_score`를 그대로 기록. 보정·클램프 금지.
2. **L683 (print용 폴백)은 건드리지 말 것** — 이미 정상 동작 중. 중복 수정 불필요.
3. **수정 2·3은 수정 1이 실패할 경우의 방어선** — 양쪽 모두 적용할 것 (한쪽만 하면 안 됨).
4. `pipeline_result.get("last_score") or ...` 패턴 사용 이유: `last_score=0`(실제 0점)과 `last_score` 미존재(None)를 구분하지 않아도 됨 — 0점 Blueprint는 REJECT되므로 PASS 경로에서 0이 나올 수 없음.

---

## 테스트 요구사항

신규 파일: `tests/test_s3_score_logging.py` (3개)

### 테스트 1: PASS 경로에서 last_score 세팅 확인

```python
def test_s3_score_pass_path_sets_last_score():
    """three_phase_blueprint_generator PASS 경로에서 pipeline_result['last_score']가 세팅됨."""
    # three_phase_blueprint_generator.py 소스에서 PASS 분기 내 last_score 세팅 확인 (소스 검사)
    import pathlib
    src = pathlib.Path("modules/domain/agents/three_phase_blueprint_generator.py").read_text(encoding="utf-8")
    # "PASS" 분기 내에 last_score 설정이 있어야 함
    assert 'pipeline_result["last_score"] = _score' in src
    # last_score 세팅이 final_verdict 세팅과 같은 블록 안에 있어야 함
    pass_block_idx = src.index('pipeline_result["final_verdict"] = verdict')
    last_score_idx = src.index('pipeline_result["last_score"] = _score')
    # last_score 세팅이 final_verdict 직후 N줄 이내
    assert abs(last_score_idx - pass_block_idx) < 300, "last_score 세팅이 final_verdict와 너무 멀리 떨어짐"
```

### 테스트 2: stage3_orchestrator PASS 경로 폴백 확인

```python
def test_s3_score_orchestrator_pass_has_fallback():
    """stage3_orchestrator PASS 경로의 _score 추출이 phases 폴백을 포함함."""
    import pathlib
    src = pathlib.Path("modules/core/stage3_orchestrator.py").read_text(encoding="utf-8")
    # PASS 경로 stage_attempts insert 직전 _score 계산에 phases 폴백이 있어야 함
    assert 'phases' in src and 'selected_score' in src
    # "last_score") or pipeline_result.get("phases" 패턴 확인
    assert 'pipeline_result.get("last_score") or pipeline_result.get("phases"' in src
```

### 테스트 3: pipeline_result 로직 유닛 테스트

```python
def test_s3_score_extraction_logic():
    """pipeline_result에 last_score 없을 때 phases 폴백으로 score 추출."""
    # 실제 로직 인라인 재현
    def extract_score(pipeline_result):
        _score = pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)
        if not isinstance(_score, int):
            try:
                _score = int(_score)
            except (ValueError, TypeError):
                _score = 0
        return _score

    # last_score 없고 phases에 있는 경우
    pr1 = {"phases": {"generate": {"selected_score": 95}}}
    assert extract_score(pr1) == 95

    # last_score 있는 경우 (우선)
    pr2 = {"last_score": 88, "phases": {"generate": {"selected_score": 95}}}
    assert extract_score(pr2) == 88

    # 둘 다 없는 경우
    pr3 = {}
    assert extract_score(pr3) == 0
```

---

## 완료 기준

- [ ] `three_phase_blueprint_generator.py` PASS 분기에 `pipeline_result["last_score"] = _score` 추가
- [ ] `stage3_orchestrator.py` PASS/REJECT 두 곳 모두 `phases` 폴백 보강
- [ ] 신규 테스트 3개 PASS
- [ ] `pytest tests/ -q` → **3,387 passed 이상, xfailed 0** 유지
- [ ] `ruff check modules/domain/agents/three_phase_blueprint_generator.py modules/core/stage3_orchestrator.py` 0 violations

---

## 감리 포인트

1. `pipeline_result["last_score"] = _score`가 `if verdict in ("PASS", "PASS_WITH_FIX"):` 블록 **내부**에 있는지 (블록 외부면 REJECT 경로도 덮어씀)
2. 수정 2·3이 **각각 독립적인 try/except** 블록 내에서 올바른 라인을 수정했는지 (PASS 경로와 REJECT 경로 혼동 금지)
3. L683 print용 폴백 라인이 **변경되지 않았는지**
4. 테스트 3에서 `pr2`의 `last_score=88`이 `phases.selected_score=95`보다 **우선** 반환되는지
5. 기준선 테스트 수(3,387) 이상 통과 확인
