# Codex Order: 합격률 개선 — python_warnings 병목 해소

> **목적**: 1차 합격률 48.6% → 60%+, python_warnings 74% → 85%+
> **근거**: `episode_production.jsonl` 60건 분석 결과
>   - 주요 CrossVerify VIOLATION 2종:
>     1. `ending_hook 미반영` — 블루프린트 ending_hook 텍스트가 원고 말미에 없음
>     2. `씬 대화 0%` — 일부 씬에 대화 전무
>   - REJECT 에피소드(10건) 평균 python_warnings: 2.8/10
>   - `chief_writer.yaml`에 ending_hook 관련 규칙 없음 (현재 섹션 주입만)
> **금지**: 명세에 없는 파일 수정. 기존 검증 로직 변경. 모델 값 변경.

---

## 0) 강제 제약

- 각 Phase 완료 후 `python -m py_compile` 문법 검사 필수.
- `chief_writer_quality.py` 수정 시 기존 self-critique 체크 1~7번 보존.
- 출력 보고서: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/passrate-improvement-result.md`

---

## Phase 1: `config/prompts/chief_writer.yaml` — ending_hook + 씬 대화 규칙 추가

### 1-A: COMMON_RULES_SECTION 말미 (규칙 12, 13) 추가

기존 9~11번 규칙(TF-54) 다음에 추가:

```yaml
12. [품질] ending_hook 의무화: 블루프린트의 'ending_hook'에 지정된 문장 또는 장면을
    반드시 이번 화 **마지막 단락**에 포함하라. ending_hook이 없으면 마지막 씬을
    독자가 다음 화를 읽고 싶게 만드는 긴장감 있는 장면으로 마무리하라.
13. [품질] 씬별 대화 의무: 블루프린트에 나열된 각 씬에 최소 1개의 실제 대화(따옴표 포함)가
    있어야 한다. 대화 없이 서술·묘사만으로 구성된 씬은 CrossVerify 실패 원인이다.
```

### 1-B: `WRITING_RULES_SECTION` (또는 해당 섹션의 말미) 확인 후 없으면 COMMON_RULES_SECTION만 수정

**주의**: YAML 파일 구조를 먼저 확인 후, 규칙이 들어가는 올바른 섹션 키에 추가.

---

## Phase 2: `modules/domain/agents/chief_writer_quality.py` — self-critique 8번째 체크 추가

### 2-A: 기존 `_self_critique()` 메서드에서 `_check_writing_directive` 호출 부분 확인 후, 그 다음에 8번째 체크 추가

```python
# [합격률] 8번째 체크: ending_hook 포함 여부
issues.extend(self._check_ending_hook_presence(content, blueprint))
```

### 2-B: `_check_ending_hook_presence()` 메서드 추가

`_check_expression_freshness` 메서드 다음에 삽입:

```python
def _check_ending_hook_presence(self, manuscript: str, blueprint) -> list:
    """[합격률] ending_hook 텍스트가 원고 말미에 있는지 확인."""
    if not blueprint or not isinstance(blueprint, dict):
        return []
    ending_hook = str(blueprint.get("ending_hook", "") or "").strip()
    if not ending_hook or len(ending_hook) < 10:
        return []
    # 원고 마지막 500자에서 확인 (ending_hook은 말미에 있어야 함)
    tail = manuscript[-500:] if len(manuscript) > 500 else manuscript
    # 부분 일치 (ending_hook의 앞 20자가 포함되면 OK)
    key_fragment = ending_hook[:20]
    if key_fragment not in tail:
        return [f"ending_hook '{key_fragment}...' 이 원고 말미(마지막 500자)에서 발견되지 않음"]
    return []
```

### 2-C: `_self_critique()` 파라미터에 `blueprint=None` 추가

`_self_critique()` 메서드 시그니처에 `blueprint=None` 파라미터 추가 (이미 있으면 스킵).
`_self_critique()` 호출부(caller)에서 `blueprint=self.host._current_blueprint` 전달 — 이미 전달되고 있으면 스킵.

**주의**: `self.host._current_blueprint`가 없다면, `blueprint` 파라미터를 None으로 두고 self-critique 호출부를 먼저 확인.

---

## Phase 3: `modules/core/stage4_interview_round.py` — self-critique에 blueprint 전달 확인

`chief_writer_quality.py`의 `_self_critique()` 호출부를 찾아 blueprint 인자가 전달되는지 확인.

전달되지 않는다면:
```python
# 기존 호출부 예시:
# critique = quality.run_self_critique(manuscript=ms, ...)

# blueprint 추가:
# critique = quality.run_self_critique(manuscript=ms, blueprint=blueprint, ...)
```

**주의**: 호출 방식을 먼저 확인 후 결정. `run_self_critique`가 내부적으로 blueprint를 이미 갖고 있으면 수정 불필요.

---

## 최종 검증

```bash
# 1. py_compile
python -m py_compile modules/domain/agents/chief_writer_quality.py
python -m py_compile modules/core/stage4_interview_round.py

# 2. ending_hook 체크 동작 확인
python -c "
from modules.domain.agents.chief_writer_quality import ChiefWriterQuality

class FakeHost:
    _tf54_writing_directive = None
    _tf54_expression_freq = {}

q = ChiefWriterQuality.__new__(ChiefWriterQuality)
q.host = FakeHost()

ms_no_hook = '이것은 테스트 원고입니다. ' * 50
bp = {'ending_hook': '독이 퍼지기 시작했다. 그리고 그는 쓰러졌다.'}
result = q._check_ending_hook_presence(ms_no_hook, bp)
assert len(result) == 1, f'expected 1 issue, got {result}'

ms_with_hook = ms_no_hook + '독이 퍼지기 시작했다. 그리고 그는 쓰러졌다.'
result2 = q._check_ending_hook_presence(ms_with_hook, bp)
assert len(result2) == 0, f'expected 0 issues, got {result2}'
print('ending_hook 체크 정상')
"

# 3. ruff
ruff check modules/domain/agents/chief_writer_quality.py config/prompts/chief_writer.yaml

# 4. 전체 테스트
pytest tests/ -q
```

---

## 보고서 형식

출력 파일: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/passrate-improvement-result.md`

```markdown
# 합격률 개선 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| Phase | 파일 | 작업 | 완료 여부 |
|-------|------|------|---------|
| 1-A | chief_writer.yaml | COMMON_RULES 12~13 추가 | ✅/❌ |
| 2-A/B | chief_writer_quality.py | _check_ending_hook_presence 추가 | ✅/❌ |
| 2-C | chief_writer_quality.py | _self_critique blueprint 파라미터 | ✅/❌ |
| 3 | stage4_interview_round.py | blueprint 전달 확인/수정 | ✅/❌ |

## 주요 결정 사항

(blueprint 전달 방식, 기존 self-critique 호출 구조 등)

## 검증 결과

- py_compile: 통과/실패
- ending_hook 체크 단위 검증: 통과/실패
- ruff: 위반 N건
- 전체 테스트: N passed, N failed

## 체크리스트

- [ ] chief_writer.yaml 규칙 12~13 추가 (ending_hook + 씬 대화)
- [ ] _check_ending_hook_presence 부분 일치 (앞 20자) 방식
- [ ] 기존 self-critique 1~7번 체크 보존
- [ ] 전체 테스트 회귀 없음
```
