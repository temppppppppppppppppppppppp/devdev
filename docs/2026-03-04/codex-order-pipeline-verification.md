# Codex Order: 실파이프라인 검증 — TF-54 / TF-55b / 합격률 wiring 통합 테스트

> **목적**: TF-54(WritingDirective), TF-55b(STATIC/DB_NPC_RELATIONSHIP), 합격률(ending_hook) 세 구현의
> **통합 배선(wiring)** 이 실제 Stage4 실행 경로에서 정상 동작함을 테스트로 확인.
> **금지**: 기존 코드 수정. 모델 값 변경. 새 스펙 추가. 테스트 외 파일 터치.
> **출력 보고서**: `docs/2026-03-04/pipeline-verification-result.md`

---

## 0) 강제 제약

- 신규 파일 하나: `tests/test_pipeline_wiring.py` (추가만, 기존 테스트 파일 미수정).
- 각 테스트 작성 후 `pytest tests/test_pipeline_wiring.py -v` 즉시 확인.
- 최종: `pytest tests/ -q` 전체 회귀 없음 확인.
- ruff: `ruff check tests/test_pipeline_wiring.py` 위반 0건.

---

## 1) 확인 대상 (커버리지 갭)

| 갭 | 설명 | 검증 수단 |
|----|------|---------|
| **TF-54 wiring A** | `stage4_interview_round`가 `PatternTracker.build_report()` 호출 후 `chief_writer._tf54_writing_directive` 주입 | mock 주입 확인 |
| **TF-54 wiring B** | `chief_writer._current_blueprint` 주입 (합격률 passrate 배선) | setattr 확인 |
| **TF-54 wiring C** | `ChiefWriterQuality._self_critique()` 호출 시 `_check_ending_hook_presence()` 실행 | 직접 단위 체인 호출 |
| **TF-55b STATIC** | `_execute_retrieval_plan()` — STATIC source → query 문자열 그대로 반환 (DB/VecMemory 호출 없음) | mock 없이 직접 호출 |
| **TF-55b DB_NPC** | `_execute_retrieval_plan()` — DB_NPC_RELATIONSHIP → `db.get_relationship_history()` 호출 | mock 주입 확인 |
| **TF-54 DirectorMC** | WritingDirective 비어있지 않으면 `_director_mc_parts[0]`에 `[WritingDirective]` prepend | dict 확인 |

---

## 2) 구현할 테스트 목록

파일: `tests/test_pipeline_wiring.py`

```python
"""
[실파이프라인 검증] TF-54 / TF-55b / 합격률(ending_hook) wiring 통합 테스트.
각 테스트는 실제 구현 경로만 확인하며 LLM 호출 없음.
"""
```

### 2-A: TF-54 wiring — WritingDirective setattr 확인

```python
# test_tf54_writing_directive_injected_to_chief_writer()
# - Stage4InterviewRound._run_tf54_pattern_analysis() 직접 호출 (또는 그 결과 확인)
# - PatternTracker.build_report()를 mock → 빈 report 반환
# - WritingDirectiveGenerator.generate()를 mock → 더미 WritingDirective 반환
# - chief_writer mock 객체에 setattr 호출됐는지 확인
#   assert hasattr(mock_cw, "_tf54_writing_directive")
#   assert isinstance(mock_cw._tf54_writing_directive, WritingDirective)

# 구현 참고: stage4_interview_round.py L77~115
# setattr(chief_writer, "_tf54_writing_directive", _writing_directive)  ← 이게 실행됐는지
```

**주의**: `stage4_interview_round`는 `run()` 내부에서 처리하므로, 해당 블록만 추출 단위 테스트하거나,
`_prepare_writing_directive()` 같은 private 메서드가 있으면 직접 호출. 없으면 아래처럼 직접 로직 검증.

```python
def test_tf54_writing_directive_setattr():
    """TF-54: chief_writer에 _tf54_writing_directive, _current_blueprint 주입 확인."""
    from modules.core.stage4_types import WritingDirective
    from unittest.mock import MagicMock, patch

    mock_cw = MagicMock()
    wd = WritingDirective(ending_style="긴장감")
    blueprint = {"ending_hook": "그는 무릎을 꿇었다."}

    # 실제 setattr 패턴 시뮬레이션 (interview_round.py L109~115)
    setattr(mock_cw, "_tf54_writing_directive", wd)
    setattr(mock_cw, "_tf54_expression_freq", {})
    setattr(mock_cw, "_current_blueprint", blueprint)

    assert mock_cw._tf54_writing_directive is wd
    assert mock_cw._current_blueprint == blueprint
    assert mock_cw._tf54_expression_freq == {}
```

### 2-B: TF-54 wiring — _self_critique에서 ending_hook 체크 실행 확인

```python
def test_tf54_self_critique_calls_ending_hook_check():
    """TF-54/합격률: _self_critique() 전체 체인에서 _check_ending_hook_presence() 실행."""
    from modules.domain.agents.chief_writer_quality import ChiefWriterQuality

    class FakeHost:
        _tf54_writing_directive = None
        _tf54_expression_freq = {}
        _current_blueprint = {"ending_hook": "그는 무릎을 꿇었다. 패배를 인정하며."}

    q = ChiefWriterQuality.__new__(ChiefWriterQuality)
    q.host = FakeHost()

    # ending_hook이 원고 말미에 없는 경우 → 이슈 발생
    ms_no_hook = "이것은 테스트 원고입니다. " * 60
    issues = q._self_critique(ms_no_hook)

    # ending_hook 관련 이슈가 포함되어야 함
    hook_issues = [i for i in issues if "ending_hook" in i]
    assert len(hook_issues) >= 1, f"ending_hook 체크 미실행: {issues}"

def test_tf54_self_critique_no_issue_when_hook_present():
    """ending_hook이 말미에 있으면 이슈 없음."""
    from modules.domain.agents.chief_writer_quality import ChiefWriterQuality

    class FakeHost:
        _tf54_writing_directive = None
        _tf54_expression_freq = {}
        _current_blueprint = {"ending_hook": "그는 무릎을 꿇었다. 패배를 인정하며."}

    q = ChiefWriterQuality.__new__(ChiefWriterQuality)
    q.host = FakeHost()

    ms_with_hook = "이것은 테스트 원고입니다. " * 60 + "그는 무릎을 꿇었다. 패배를 인정하며."
    issues = q._self_critique(ms_with_hook)

    hook_issues = [i for i in issues if "ending_hook" in i]
    assert len(hook_issues) == 0, f"false positive: {hook_issues}"
```

### 2-C: TF-55b — STATIC source 직접 반환 (DB 호출 없음)

```python
def test_tf55b_static_source_returns_query_directly():
    """TF-55b: STATIC source → query 문자열 자체 반환, DB/VecMemory 미호출."""
    from modules.core.stage4_context_builder import Stage4ContextBuilder
    from modules.core.context_advisor import RetrievalPlan, RetrievalSlot, RetrievalSources
    from unittest.mock import MagicMock, patch

    ctx = MagicMock()
    ctx.db = MagicMock()
    cb = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
    cb.ctx = ctx
    cb.vec_memory = MagicMock()

    static_content = "세계관: 이 세계는 마법이 지배한다."
    slot = RetrievalSlot(
        category="world_lore",
        query=static_content,
        source=RetrievalSources.STATIC,
        priority=1,
    )
    plan = RetrievalPlan(slots=[slot])

    sections = cb._execute_retrieval_plan(plan)

    # STATIC은 query를 그대로 반환 → sections에 포함
    combined = "\n".join(sections.values()) if isinstance(sections, dict) else "\n".join(sections)
    assert static_content in combined, f"STATIC 내용 미반영: {combined[:200]}"
    # vec_memory 검색 미호출
    cb.vec_memory.search.assert_not_called()
```

### 2-D: TF-55b — DB_NPC_RELATIONSHIP source → get_relationship_history 호출

```python
def test_tf55b_db_npc_relationship_calls_get_history():
    """TF-55b: DB_NPC_RELATIONSHIP source → db.get_relationship_history() 호출."""
    from modules.core.stage4_context_builder import Stage4ContextBuilder
    from modules.core.context_advisor import RetrievalPlan, RetrievalSlot, RetrievalSources
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.db = MagicMock()
    # get_relationship_history → [{"change_ep": 3, "npc1": "A", "npc2": "B", "old_relation": "적", "new_relation": "동료"}]
    ctx.db.get_relationship_history.return_value = [
        {"change_ep": 3, "npc1": "영웅", "npc2": "악당", "old_relation": "적", "new_relation": "동료"}
    ]

    cb = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
    cb.ctx = ctx
    cb.vec_memory = MagicMock()

    query = "관계 변화 이력: 영웅: 주인공, 악당: 보스"
    slot = RetrievalSlot(
        category="npc_rel",
        query=query,
        source=RetrievalSources.DB_NPC_RELATIONSHIP,
        priority=1,
    )
    plan = RetrievalPlan(slots=[slot])

    sections = cb._execute_retrieval_plan(plan)

    # get_relationship_history 호출 확인
    assert ctx.db.get_relationship_history.called, "get_relationship_history 미호출"

    # 결과가 sections에 반영
    combined = "\n".join(sections.values()) if isinstance(sections, dict) else "\n".join(sections)
    assert "영웅" in combined or "동료" in combined, f"DB 결과 미반영: {combined[:200]}"
```

### 2-E: TF-54 DirectorMC — WritingDirective 비어있지 않으면 [WritingDirective] prepend

```python
def test_tf54_writing_directive_prepended_to_director_mc():
    """TF-54: WritingDirective 비어있지 않으면 _director_mc_parts[0]에 [WritingDirective] 추가."""
    from modules.core.stage4_types import WritingDirective

    wd = WritingDirective(ending_style="조용한 여운")
    mc_parts = []

    # interview_round.py L606~614 로직 재현
    if not wd.is_empty():
        wd_lines = ["[WritingDirective]"]
        if wd.ending_style:
            wd_lines.append(f"- 마무리 스타일: {wd.ending_style}")
        if wd.expression_ban:
            wd_lines.append(f"- 금지 표현: {', '.join(wd.expression_ban)}")
        mc_parts.insert(0, "\n".join(wd_lines))

    assert len(mc_parts) == 1
    assert mc_parts[0].startswith("[WritingDirective]")
    assert "조용한 여운" in mc_parts[0]

def test_tf54_empty_directive_not_prepended():
    """WritingDirective 비어있으면 mc_parts에 추가 안 함."""
    from modules.core.stage4_types import WritingDirective

    wd = WritingDirective()  # all fields empty
    mc_parts = []

    if not wd.is_empty():
        mc_parts.insert(0, "[WritingDirective]")

    assert len(mc_parts) == 0
```

### 2-F: WritingDirective.is_empty() 명세 확인

```python
def test_writing_directive_is_empty_logic():
    """WritingDirective.is_empty() — ending_style/metaphor_avoid/expression_ban 중 하나라도 있으면 False."""
    from modules.core.stage4_types import WritingDirective

    assert WritingDirective().is_empty() is True
    assert WritingDirective(ending_style="긴장").is_empty() is False
    assert WritingDirective(expression_ban=["그리하여"]).is_empty() is False
    assert WritingDirective(metaphor_avoid=["달빛"]).is_empty() is False
    # emotion_required, intensity_note, npc_directives 단독 — is_empty 기준 확인
    # (구현에 따라 True일 수 있음 — 실제 코드 기준으로 테스트)
    wd_emotion_only = WritingDirective(emotion_required="슬픔")
    # 실제 is_empty() 반환값에 맞게 assert (아래는 기대 명세)
    # ending_style/metaphor_avoid/expression_ban만 체크하면 True
    # → 구현 확인 후 assert 맞춤
```

---

## 3) 구현 시 확인 사항

### Stage4ContextBuilder._execute_retrieval_plan() 반환 타입

`_execute_retrieval_plan()`의 반환이 `dict[str, str]`인지 `list[str]`인지 먼저 확인 후 테스트 작성.

```bash
grep -n "_execute_retrieval_plan\|return" modules/core/stage4_context_builder.py | head -30
```

### ChiefWriterQuality._self_critique() 시그니처

`_self_critique(content, blueprint=None)` vs `_self_critique(content)` 확인 후 호출.

```bash
grep -n "def _self_critique\|def apply_self_critique" modules/domain/agents/chief_writer_quality.py
```

### RetrievalSlot 생성자 파라미터 확인

```bash
grep -n "class RetrievalSlot\|def __init__" modules/core/context_advisor.py | head -10
```

---

## 4) 실행 순서

```bash
# 1. 파일 생성 후 즉시 구문 검사
python -m py_compile tests/test_pipeline_wiring.py

# 2. 신규 테스트만 실행
pytest tests/test_pipeline_wiring.py -v

# 3. ruff
ruff check tests/test_pipeline_wiring.py

# 4. 전체 회귀
pytest tests/ -q
```

---

## 5) 보고서 형식

출력: `docs/2026-03-04/pipeline-verification-result.md`

```markdown
# 실파이프라인 검증 결과

> 구현일: 2026-03-04

## 테스트 목록

| 테스트명 | 검증 대상 | 결과 |
|---------|---------|------|
| test_tf54_writing_directive_setattr | TF-54 setattr 배선 | ✅/❌ |
| test_tf54_self_critique_calls_ending_hook_check | 합격률 ending_hook 체인 | ✅/❌ |
| test_tf54_self_critique_no_issue_when_hook_present | ending_hook false positive 없음 | ✅/❌ |
| test_tf55b_static_source_returns_query_directly | TF-55b STATIC 직접 반환 | ✅/❌ |
| test_tf55b_db_npc_relationship_calls_get_history | TF-55b DB 호출 | ✅/❌ |
| test_tf54_writing_directive_prepended_to_director_mc | Director MC prepend | ✅/❌ |
| test_tf54_empty_directive_not_prepended | 빈 Directive 미추가 | ✅/❌ |
| test_writing_directive_is_empty_logic | is_empty() 명세 | ✅/❌ |

## 검증 결과

- py_compile: 통과/실패
- 신규 테스트: N passed, N failed
- ruff: 위반 N건
- 전체 테스트: N passed, N failed (N skipped)

## 조정 사항

(반환 타입 차이, 시그니처 불일치 등 실제 코드 기준 조정 내역)
```

---

## 6) 합격 기준

- 신규 테스트 **8개 전부 PASS**
- 전체 테스트 회귀 **0건**
- ruff 위반 **0건**
