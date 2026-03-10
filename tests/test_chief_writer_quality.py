"""[B-1-5] ChiefWriterQualityGate unit tests."""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from modules.core.constants import ManuscriptLimits
from modules.core.stage4_types import WritingDirective
from modules.domain.agents.chief_writer_quality import ChiefWriterQualityGate


def _make_host():
    host = MagicMock()
    host.ask = MagicMock(return_value='{"content":"fixed"}')
    host._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
    return host


def _tuple_string_constants(func, min_len=1):
    return [
        c
        for c in func.__code__.co_consts
        if isinstance(c, tuple) and len(c) >= min_len and all(isinstance(v, str) for v in c)
    ]


class TestQualityGateBasics:
    def test_quality_gate_init(self):
        host = _make_host()
        gate = ChiefWriterQualityGate(host)
        assert gate.host is host

    def test_sanitize_leakage_empty(self):
        gate = ChiefWriterQualityGate(_make_host())
        assert gate.sanitize_leakage("") == ""

    def test_sanitize_leakage_removes_banned_keys(self):
        gate = ChiefWriterQualityGate(_make_host())
        text = json.dumps(
            {
                "title": "t",
                "content": "c",
                "Beat 3": "remove",
                "future_hint": "remove",
                "next_episode": "remove",
            },
            ensure_ascii=False,
        )
        out = gate.sanitize_leakage(text)
        data = json.loads(out)
        assert "Beat 3" not in data
        assert "future_hint" not in data
        assert "next_episode" not in data
        assert data["content"] == "c"

    def test_sanitize_leakage_removes_english_parentheses(self):
        gate = ChiefWriterQualityGate(_make_host())
        out = gate.sanitize_leakage("검도(Sword)와 보법(Walk)")
        assert "Sword" not in out
        assert "Walk" not in out


class TestApplyAndCritique:
    def test_apply_self_critique_high_rubric_skip(self):
        """[TF-I08] rubric ≥ 3.5 + 구조적 이슈 없음 → 스킵"""
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = '{"content":"본문"}'
        with (
            patch.object(gate, "_evaluate_with_rubric", return_value=3.6),
            patch.object(
                gate,
                "_self_critique",
                return_value={"has_issues": False, "issues": [], "severity": "low"},
            ) as mock_critique,
        ):
            out = gate.apply_self_critique(manuscript, "hud", [], "genre", ep_num=2)
        assert out == manuscript
        # [TF-I08] 구조적 검사를 위해 1회 호출됨 (이슈 없으면 스킵)
        mock_critique.assert_called_once()

    def test_apply_self_critique_high_rubric_structural_issue_proceeds(self):
        """[TF-I08] rubric ≥ 3.5이지만 구조적 이슈 있으면 Self-Critique 진행"""
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = '{"content":"본문"}'
        structural_issue = {
            "has_issues": True,
            "issues": [{"type": "hud_contradiction", "severity": "medium", "description": "test"}],
            "severity": "medium",
        }
        with (
            patch.object(gate, "_evaluate_with_rubric", return_value=3.8),
            patch.object(gate, "_self_critique", return_value=structural_issue),
            patch.object(gate, "_fix_manuscript_issues", return_value=manuscript) as mock_fix,
        ):
            gate.apply_self_critique(manuscript, "hud", [], "genre", ep_num=2)
        # 구조적 이슈가 있으므로 수정 시도 + [TF-G] 분량 게이트에서도 호출
        assert mock_fix.call_count >= 1

    def test_apply_self_critique_low_rubric_runs(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = '{"content":"본문"}'
        with (
            patch.object(gate, "_evaluate_with_rubric", return_value=2.0),
            patch.object(
                gate, "_self_critique", return_value={"has_issues": False, "issues": [], "severity": "low"}
            ) as mock_critique,
            patch.object(gate, "_fix_manuscript_issues", return_value=manuscript) as mock_fix,
        ):
            out = gate.apply_self_critique(manuscript, "hud", [], "genre", ep_num=2)
        assert out == manuscript
        mock_critique.assert_called_once()
        # [TF-G] 분량 부족 게이트에서 _fix_manuscript_issues 호출될 수 있음 (test manuscript < 5000자)

    def test_self_critique_no_issues(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = json.dumps({"content": "가" * (int(ManuscriptLimits.TARGET_LENGTH) + 200)}, ensure_ascii=False)
        with (
            patch.object(gate, "_check_hud_consistency", return_value=[]),
            patch.object(gate, "_check_cliche_overuse", return_value=[]),
            patch.object(gate, "_check_justification_gaps", return_value=[]),
            patch.object(gate, "_check_npc_relationship", return_value=[]),
        ):
            out = gate._self_critique(manuscript, "", {"npcs": []}, "genre", ep_num=1)
        assert out["has_issues"] is False
        assert out["severity"] == "low"
        assert out["issues"] == []

    def test_self_critique_detects_short_manuscript(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = json.dumps({"content": "가" * (int(ManuscriptLimits.MIN_LENGTH) - 300)}, ensure_ascii=False)
        with (
            patch.object(gate, "_check_hud_consistency", return_value=[]),
            patch.object(gate, "_check_cliche_overuse", return_value=[]),
            patch.object(gate, "_check_justification_gaps", return_value=[]),
            patch.object(gate, "_check_npc_relationship", return_value=[]),
            patch.object(gate, "_check_writing_directive", return_value=[]),
            patch.object(gate, "_check_expression_freshness", return_value=[]),
            patch.object(gate, "_check_ending_hook_presence", return_value=[]),
            patch.object(gate, "_check_arithmetic_consistency", return_value=[]),
            patch.object(gate, "_check_system_term_exposure", return_value=[]),
        ):
            out = gate._self_critique(manuscript, "", {"npcs": []}, "genre", ep_num=1)
        length_issue = next((i for i in out["issues"] if i.get("type") == "manuscript_length"), None)
        assert length_issue is not None
        assert length_issue["severity"] == "high"
        assert out["severity"] == "medium"

    def test_self_critique_detects_medium_manuscript(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = json.dumps({"content": "가" * (int(ManuscriptLimits.MIN_LENGTH) + 500)}, ensure_ascii=False)
        with (
            patch.object(gate, "_check_hud_consistency", return_value=[]),
            patch.object(gate, "_check_cliche_overuse", return_value=[]),
            patch.object(gate, "_check_justification_gaps", return_value=[]),
            patch.object(gate, "_check_npc_relationship", return_value=[]),
            patch.object(gate, "_check_writing_directive", return_value=[]),
            patch.object(gate, "_check_expression_freshness", return_value=[]),
            patch.object(gate, "_check_ending_hook_presence", return_value=[]),
            patch.object(gate, "_check_arithmetic_consistency", return_value=[]),
            patch.object(gate, "_check_system_term_exposure", return_value=[]),
        ):
            out = gate._self_critique(manuscript, "", {"npcs": []}, "genre", ep_num=1)
        length_issue = next((i for i in out["issues"] if i.get("type") == "manuscript_length"), None)
        assert length_issue is not None
        assert length_issue["severity"] == "medium"

    def test_self_critique_passes_long_manuscript(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = json.dumps({"content": "가" * (int(ManuscriptLimits.TARGET_LENGTH) + 500)}, ensure_ascii=False)
        with (
            patch.object(gate, "_check_hud_consistency", return_value=[]),
            patch.object(gate, "_check_cliche_overuse", return_value=[]),
            patch.object(gate, "_check_justification_gaps", return_value=[]),
            patch.object(gate, "_check_npc_relationship", return_value=[]),
            patch.object(gate, "_check_writing_directive", return_value=[]),
            patch.object(gate, "_check_expression_freshness", return_value=[]),
            patch.object(gate, "_check_ending_hook_presence", return_value=[]),
            patch.object(gate, "_check_arithmetic_consistency", return_value=[]),
            patch.object(gate, "_check_system_term_exposure", return_value=[]),
        ):
            out = gate._self_critique(manuscript, "", {"npcs": []}, "genre", ep_num=1)
        assert not any(i.get("type") == "manuscript_length" for i in out["issues"])

    def test_severity_high_issue_promotes_to_medium(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = json.dumps({"content": "가" * (int(ManuscriptLimits.TARGET_LENGTH) + 500)}, ensure_ascii=False)
        with (
            patch.object(gate, "_check_hud_consistency", return_value=[]),
            patch.object(gate, "_check_cliche_overuse", return_value=[]),
            patch.object(gate, "_check_justification_gaps", return_value=[]),
            patch.object(gate, "_check_npc_relationship", return_value=[]),
            patch.object(gate, "_check_writing_directive", return_value=[]),
            patch.object(gate, "_check_expression_freshness", return_value=[]),
            patch.object(gate, "_check_ending_hook_presence", return_value=[]),
            patch.object(gate, "_check_arithmetic_consistency", return_value=[]),
            patch.object(
                gate,
                "_check_system_term_exposure",
                return_value=[{"type": "meta_wall", "description": "노출", "severity": "high"}],
            ),
        ):
            out = gate._self_critique(manuscript, "", {"npcs": []}, "genre", ep_num=1)
        assert out["severity"] == "medium"


class TestCheckerMethods:
    def test_check_hud_consistency(self):
        gate = ChiefWriterQualityGate(_make_host())
        groups = _tuple_string_constants(gate._check_hud_consistency, min_len=4)
        if len(groups) < 3:
            pytest.skip("keyword constants not found")
        weak_keywords, strong_actions, justification_kws = groups[0], groups[1], groups[2]
        hud_report = weak_keywords[0]
        content = strong_actions[0]
        # Ensure no justification keyword is present.
        for kw in justification_kws:
            content = content.replace(kw, "")
        issues = gate._check_hud_consistency(content, hud_report)
        assert any(i.get("type") == "hud_contradiction" for i in issues)

    def test_check_hud_consistency_none_hud_report(self):
        gate = ChiefWriterQualityGate(_make_host())
        issues = gate._check_hud_consistency("강한 액션 장면", None)
        assert issues == []

    def test_check_cliche_overuse(self):
        gate = ChiefWriterQualityGate(_make_host())
        issues = gate._check_cliche_overuse("plain content", "genre", ep_num=1)
        assert isinstance(issues, list)

    def test_check_cliche_overuse_recent(self):
        gate = ChiefWriterQualityGate(_make_host())
        with patch.object(gate, "_count_recent_cliches", return_value={"k1": 3, "k2": 4}):
            issues = gate._check_cliche_overuse("content", "genre", ep_num=10)
        assert any(i.get("type") == "cliche_overuse_recent" for i in issues)

    def test_check_writing_directive_detects_missing_emotion_required(self):
        gate = ChiefWriterQualityGate(_make_host())

        issues = gate._check_writing_directive("건조한 보고만 이어졌다.", WritingDirective(emotion_required="안도"))

        assert any(isinstance(i, dict) and i.get("type") == "emotion_required_missing" for i in issues)

    def test_check_writing_directive_accepts_present_emotion_required(self):
        gate = ChiefWriterQualityGate(_make_host())

        issues = gate._check_writing_directive("마침내 안도가 밀려왔다.", WritingDirective(emotion_required="안도"))

        assert not any(isinstance(i, dict) and i.get("type") == "emotion_required_missing" for i in issues)

    def test_check_temporal_logic_detects_conflicting_jump(self):
        gate = ChiefWriterQualityGate(_make_host())

        issues = gate._check_temporal_logic("곧바로 검을 뽑았다. 다음 날 그는 다시 같은 자리에서 웃었다.")

        assert any(i.get("type") == "temporal_logic_jump" for i in issues)

    def test_check_paragraph_structure_detects_dense_block(self):
        gate = ChiefWriterQualityGate(_make_host())
        dense = ("문장이다. " * 14).strip()

        issues = gate._check_paragraph_structure(dense)

        assert any(i.get("type") == "paragraph_structure_dense" for i in issues)

    def test_check_tonal_consistency_detects_blueprint_mismatch(self):
        gate = ChiefWriterQualityGate(_make_host())

        issues = gate._check_tonal_consistency(
            "그는 낄낄 웃으며 농담을 던지고 또 장난을 쳤다.",
            {"core_tension": "살벌한 긴장과 위기의 압박"},
            WritingDirective(),
        )

        assert any(i.get("type") == "tonal_inconsistency" for i in issues)

    def test_check_scene_transition_markers_detects_missing_markers(self):
        gate = ChiefWriterQualityGate(_make_host())
        content = (
            "한양의 밤은 차가웠다.\n\n"
            "그는 칼을 만지작거리며 숨을 골랐다.\n\n"
            "그리고 곧장 결전을 준비했다."
        )

        issues = gate._check_scene_transition_markers(content)

        assert any(i.get("type") == "scene_transition_marker_missing" for i in issues)

    def test_check_ai_tell_patterns_detects_stock_phrase_repetition(self):
        gate = ChiefWriterQualityGate(_make_host())
        content = (
            "어느새 복도 끝이 조용해졌다. 그는 숨을 삼켰다. "
            "어느새 방 안 공기가 식었다. 그녀도 숨을 삼켰다."
        )

        issues = gate._check_ai_tell_patterns(content)

        assert any(i.get("type") == "ai_tell_pattern_overuse" for i in issues)

    def test_check_ai_tell_patterns_detects_repeated_sentence_starters(self):
        gate = ChiefWriterQualityGate(_make_host())
        content = (
            "그는 천천히 문을 열었다. 그는 조용히 안을 살폈다. "
            "그는 다시 손끝을 움켜쥐었다. 그는 낮게 숨을 골랐다."
        )

        issues = gate._check_ai_tell_patterns(content)

        assert any(i.get("type") == "ai_tell_sentence_starter_repetition" for i in issues)

    def test_check_pov_consistency_critique_detects_mixed_without_scene_separator(self):
        host = _make_host()
        host.context = MagicMock()
        host.context.current_project = MagicMock()
        host.context.current_project.master_bible = {
            "MasterBible": {"protagonist_config": {"pov": "혼합", "name": "진우"}}
        }
        gate = ChiefWriterQualityGate(host)

        issues = gate._check_pov_consistency_critique(
            "나는 검을 들었다. 내가 앞으로 나섰다. 나는 숨을 골랐다. "
            "진우는 문을 밀었다. 진우가 복도를 바라봤다. 그는 다시 걸었다."
        )

        assert any(i.get("type") == "pov_consistency" for i in issues)

    def test_check_justification_gaps(self):
        gate = ChiefWriterQualityGate(_make_host())
        strings = [c for c in gate._check_justification_gaps.__code__.co_consts if isinstance(c, str)]
        tuples = _tuple_string_constants(gate._check_justification_gaps, min_len=2)
        if not tuples:
            pytest.skip("keyword constants not found")
        weak_keywords = [s for s in strings if s in {"나약", "중독"}]
        if not weak_keywords:
            pytest.skip("weak-state constants not found")

        # Tuples include overcome keywords and justification keywords.
        tuple_4 = next((t for t in tuples if len(t) == 4), None)
        tuple_5 = next((t for t in tuples if len(t) == 5), None)
        if tuple_4 is None or tuple_5 is None:
            pytest.skip("expected keyword tuples not found")

        hud_report = weak_keywords[0]
        content = tuple_4[0]
        for kw in tuple_5:
            content = content.replace(kw, "")
        issues = gate._check_justification_gaps(content, hud_report)
        assert any(i.get("type") == "justification_gap" for i in issues)

    def test_check_justification_gaps_none_hud_report(self):
        gate = ChiefWriterQualityGate(_make_host())
        issues = gate._check_justification_gaps("돌파에 성공했다.", None)
        assert issues == []

    def test_check_npc_relationship(self):
        gate = ChiefWriterQualityGate(_make_host())
        groups = _tuple_string_constants(gate._check_npc_relationship, min_len=3)
        if len(groups) < 2:
            pytest.skip("relationship constants not found")
        relationship_states, disrespect_keywords = groups[0], groups[1]
        npc_name = "청풍"
        encyclopedia = {"npcs": [{"name": npc_name, "relationship_state": relationship_states[0]}]}
        content = f"{npc_name} {disrespect_keywords[0]}"
        issues = gate._check_npc_relationship(content, encyclopedia)
        assert any(i.get("type") == "npc_relationship_inconsistency" for i in issues)


class TestFixAndRubric:
    def test_fix_manuscript_issues_calls_llm(self):
        host = _make_host()
        host.ask.return_value = '{"content":"fixed"}'
        gate = ChiefWriterQualityGate(host)
        result = gate._fix_manuscript_issues(
            '{"content":"orig"}',
            {"issues": [{"type": "x", "description": "desc"}]},
            "hud",
        )
        assert host.ask.called
        assert json.loads(result)["content"] == "fixed"

    def test_fix_manuscript_issues_fallback(self):
        host = _make_host()
        host.ask.side_effect = RuntimeError("llm down")
        gate = ChiefWriterQualityGate(host)
        manuscript = '{"content":"orig"}'
        result = gate._fix_manuscript_issues(
            manuscript,
            {"issues": [{"type": "x", "description": "desc"}]},
            "hud",
        )
        assert result == manuscript

    def test_fix_manuscript_logs_short_result(self, caplog):
        host = _make_host()
        host.ask.return_value = json.dumps({"content": "짧음"}, ensure_ascii=False)
        gate = ChiefWriterQualityGate(host)
        with caplog.at_level(logging.WARNING):
            result = gate._fix_manuscript_issues(
                '{"content":"orig"}',
                {"issues": [{"type": "x", "description": "desc"}]},
                "hud",
            )
        assert json.loads(result)["content"] == "짧음"
        assert any("[TF-H] 수정 후 분량 여전히 부족" in rec.message for rec in caplog.records)

    def test_fix_uses_expand_prompt_for_length_issue(self):
        host = _make_host()
        host.ask.return_value = '{"content":"expanded"}'
        gate = ChiefWriterQualityGate(host)
        with (
            patch("modules.domain.agents.chief_writer_quality.get_expand_length_prompt", return_value="expand prompt") as m_expand,
            patch("modules.domain.agents.chief_writer_quality.get_fix_issues_prompt", return_value="generic prompt") as m_generic,
        ):
            gate._fix_manuscript_issues(
                '{"content":"orig"}',
                {"issues": [{"type": "manuscript_length", "description": "짧음"}]},
                "hud",
            )
        m_expand.assert_called_once()
        m_generic.assert_not_called()
        host.ask.assert_called_with("expand prompt", temperature=0.5, thinking_level="medium")

    def test_fix_uses_generic_prompt_for_other_issues(self):
        host = _make_host()
        host.ask.return_value = '{"content":"fixed"}'
        gate = ChiefWriterQualityGate(host)
        with (
            patch("modules.domain.agents.chief_writer_quality.get_expand_length_prompt", return_value="expand prompt") as m_expand,
            patch("modules.domain.agents.chief_writer_quality.get_fix_issues_prompt", return_value="generic prompt") as m_generic,
        ):
            gate._fix_manuscript_issues(
                '{"content":"orig"}',
                {"issues": [{"type": "hud_contradiction", "description": "desc"}]},
                "hud",
            )
        m_generic.assert_called_once()
        m_expand.assert_not_called()
        host.ask.assert_called_with("generic prompt", temperature=0.5, thinking_level="low")

    def test_evaluate_with_rubric_short(self):
        gate = ChiefWriterQualityGate(_make_host())
        assert gate._evaluate_with_rubric("short", "genre") == 1.0

    def test_evaluate_with_rubric_good(self):
        gate = ChiefWriterQualityGate(_make_host())
        content = (
            '"A line of dialogue." A vivid scene opens by the river. '
            '"Another dialogue line." Bright wind moves over stones. '
            "Calm footwork and steel sparks shape the rhythm. "
            "Tension rises while choices tighten the scene."
        ) * 4
        score = gate._evaluate_with_rubric(content, "genre")
        assert 2.0 <= score <= 4.0


class TestRecentCliches:
    def test_count_recent_cliches(self):
        host = _make_host()
        gate = ChiefWriterQualityGate(host)
        keywords_groups = _tuple_string_constants(gate._count_recent_cliches, min_len=10)
        if not keywords_groups:
            pytest.skip("cliche keyword constants not found")
        keyword = keywords_groups[0][0]
        host._get_cached_manuscript = lambda ep: {"content": (keyword * 2) if ep in (8, 9) else "", "hud_snapshot": {}}
        result = gate._count_recent_cliches(ep_num=10, window=3)
        assert result
        assert keyword in result

    def test_count_recent_cliches_empty_cache(self):
        host = _make_host()
        host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
        gate = ChiefWriterQualityGate(host)
        result = gate._count_recent_cliches(ep_num=10, window=3)
        assert result == {}
