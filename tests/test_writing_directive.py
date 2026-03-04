"""[TF-54b,e] WritingDirectiveGenerator + WritingDirective 단위 테스트."""

from modules.core.pattern_tracker import PatternReport
from modules.core.stage4_types import WritingDirective
from modules.core.writing_directive_generator import WritingDirectiveGenerator


def test_writing_directive_is_empty():
    wd = WritingDirective()
    assert wd.is_empty()


def test_writing_directive_not_empty():
    wd = WritingDirective(ending_style="조용한여운")
    assert not wd.is_empty()


def test_parse_valid_json():
    gen = WritingDirectiveGenerator()
    raw = (
        '{"ending_style":"조용한여운","metaphor_avoid":["군사"],"metaphor_suggest":["음식"],'
        '"emotion_required":"안도","npc_directives":{},"intensity_note":"담담하게",'
        '"expression_ban":["사무실의 공기"]}'
    )
    wd = gen._parse_response(raw)
    assert wd.ending_style == "조용한여운"
    assert "군사" in wd.metaphor_avoid
    assert "사무실의 공기" in wd.expression_ban


def test_parse_json_with_markdown():
    gen = WritingDirectiveGenerator()
    raw = (
        '```json\n{"ending_style":"선언문","metaphor_avoid":[],"metaphor_suggest":[],'
        '"emotion_required":"","npc_directives":{},"intensity_note":"","expression_ban":[]}\n```'
    )
    wd = gen._parse_response(raw)
    assert wd.ending_style == "선언문"


def test_parse_empty_returns_empty():
    gen = WritingDirectiveGenerator()
    wd = gen._parse_response("")
    assert wd.is_empty()


def test_parse_invalid_json_returns_empty():
    gen = WritingDirectiveGenerator()
    wd = gen._parse_response("이것은 JSON이 아닙니다")
    assert wd.is_empty()


def test_generate_llm_failure_returns_empty():
    def failing_llm(prompt):
        raise RuntimeError("LLM 호출 실패")

    gen = WritingDirectiveGenerator()
    report = PatternReport()
    wd = gen.generate(report, {}, "투자", 5, failing_llm)
    assert wd.is_empty()


def test_generate_success():
    def mock_llm(prompt):
        return (
            '{"ending_style":"조용한여운","metaphor_avoid":["군사"],"metaphor_suggest":["음식"],'
            '"emotion_required":"안도","npc_directives":{"박성호":"유능한 모습"},"intensity_note":"담담하게",'
            '"expression_ban":["동공이 흔들"]}'
        )

    gen = WritingDirectiveGenerator()
    report = PatternReport()
    wd = gen.generate(report, {}, "투자", 5, mock_llm)
    assert not wd.is_empty()
    assert wd.ending_style == "조용한여운"
