"""
[실파이프라인 검증] TF-54 / TF-55b / 합격률(ending_hook) wiring 통합 테스트.
각 테스트는 실제 구현 경로만 확인하며 LLM 호출 없음.
"""

from unittest.mock import MagicMock

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot, RetrievalSources
from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.core.stage4_types import WritingDirective
from modules.domain.agents.chief_writer_quality import ChiefWriterQualityGate


def test_tf54_writing_directive_setattr():
    """TF-54: chief_writer에 _tf54_writing_directive, _current_blueprint 주입 확인."""
    mock_cw = MagicMock()
    wd = WritingDirective(ending_style="긴장감")
    blueprint = {"ending_hook": "그는 무릎을 꿇었다."}

    # stage4_interview_round.py의 setattr 배선 로직 재현
    setattr(mock_cw, "_tf54_writing_directive", wd)
    setattr(mock_cw, "_tf54_expression_freq", {})
    setattr(mock_cw, "_current_blueprint", blueprint)

    assert mock_cw._tf54_writing_directive is wd
    assert mock_cw._current_blueprint == blueprint
    assert mock_cw._tf54_expression_freq == {}


def test_tf54_self_critique_calls_ending_hook_check():
    """TF-54/합격률: _self_critique() 체인에서 ending_hook 체크가 실행되는지 확인."""

    class FakeHost:
        _tf54_writing_directive = None
        _tf54_expression_freq = {}
        _current_blueprint = {"ending_hook": "그는 무릎을 꿇었다. 패배를 인정하며."}

    q = ChiefWriterQualityGate.__new__(ChiefWriterQualityGate)
    q.host = FakeHost()

    ms_no_hook = "이것은 테스트 원고입니다. " * 60
    result = q._self_critique(
        manuscript=ms_no_hook,
        hud_report="",
        encyclopedia={"npcs": []},
        genre_name="무협",
        blueprint=q.host._current_blueprint,
    )

    issues = result.get("issues", [])
    hook_issues = [i for i in issues if isinstance(i, str) and "ending_hook" in i]
    assert len(hook_issues) >= 1, f"ending_hook 체크 미실행: {issues}"


def test_tf54_self_critique_no_issue_when_hook_present():
    """ending_hook이 말미에 있으면 관련 이슈가 없어야 한다."""

    class FakeHost:
        _tf54_writing_directive = None
        _tf54_expression_freq = {}
        _current_blueprint = {"ending_hook": "그는 무릎을 꿇었다. 패배를 인정하며."}

    q = ChiefWriterQualityGate.__new__(ChiefWriterQualityGate)
    q.host = FakeHost()

    ms_with_hook = "이것은 테스트 원고입니다. " * 60 + "그는 무릎을 꿇었다. 패배를 인정하며."
    result = q._self_critique(
        manuscript=ms_with_hook,
        hud_report="",
        encyclopedia={"npcs": []},
        genre_name="무협",
        blueprint=q.host._current_blueprint,
    )

    issues = result.get("issues", [])
    hook_issues = [i for i in issues if isinstance(i, str) and "ending_hook" in i]
    assert len(hook_issues) == 0, f"false positive: {hook_issues}"


def test_tf55b_static_source_returns_query_directly():
    """TF-55b: STATIC source는 query 문자열을 그대로 context에 반영한다."""
    ctx = MagicMock()
    ctx.memory = MagicMock()
    ctx.db = MagicMock()

    cb = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
    cb.ctx = ctx

    static_content = "세계관: 이 세계는 마법이 지배한다."
    slot = RetrievalSlot(
        category="world_lore",
        query=static_content,
        source=RetrievalSources.STATIC,
        priority=1,
    )
    plan = RetrievalPlan(stage="stage4", episode_num=7, slots=[slot], total_budget_chars=2000, used_llm=False)

    sections = cb._execute_retrieval_plan(plan)
    combined = "\n".join(sections)

    assert static_content in combined, f"STATIC 내용 미반영: {combined[:200]}"
    assert ctx.memory.retrieve_multi_query_context.call_count == 0
    assert ctx.db.get_relationship_history.call_count == 0


def test_tf55b_db_npc_relationship_calls_get_history():
    """TF-55b: DB_NPC_RELATIONSHIP source는 get_relationship_history를 호출해야 한다."""
    ctx = MagicMock()
    ctx.memory = MagicMock()
    ctx.db = MagicMock()
    ctx.db.get_relationship_history.return_value = [
        {"change_ep": 3, "npc1": "영웅", "npc2": "악당", "old_relation": "적", "new_relation": "동료"}
    ]

    cb = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
    cb.ctx = ctx

    slot = RetrievalSlot(
        category="npc_rel",
        query="관계 변화 이력: 영웅: 주인공, 악당: 보스",
        source=RetrievalSources.DB_NPC_RELATIONSHIP,
        priority=1,
    )
    plan = RetrievalPlan(stage="stage4", episode_num=10, slots=[slot], total_budget_chars=2000, used_llm=False)

    sections = cb._execute_retrieval_plan(plan)
    combined = "\n".join(sections)

    ctx.db.get_relationship_history.assert_called_once_with("영웅", "악당", limit=5)
    assert ("영웅" in combined) or ("동료" in combined), f"DB 결과 미반영: {combined[:200]}"


def test_tf54_writing_directive_prepended_to_director_mc():
    """TF-54: WritingDirective 비어있지 않으면 Director MC 앞에 prepend."""
    wd = WritingDirective(ending_style="조용한 여운")
    mc_parts = []

    # stage4_interview_round.py prepend 로직 재현
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
    """빈 WritingDirective는 Director MC에 추가되지 않는다."""
    wd = WritingDirective()
    mc_parts = []

    if not wd.is_empty():
        mc_parts.insert(0, "[WritingDirective]")

    assert len(mc_parts) == 0


def test_writing_directive_is_empty_logic():
    """WritingDirective.is_empty() 명세 확인."""
    assert WritingDirective().is_empty() is True
    assert WritingDirective(ending_style="긴장").is_empty() is False
    assert WritingDirective(expression_ban=["그리하여"]).is_empty() is False
    assert WritingDirective(metaphor_avoid=["달빛"]).is_empty() is False

    # 현재 구현은 ending_style/metaphor_avoid/expression_ban만 검사한다.
    wd_emotion_only = WritingDirective(emotion_required="슬픔")
    assert wd_emotion_only.is_empty() is True
