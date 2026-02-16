"""[B-1-5] ChiefWriterQualityGate unit tests."""

import json
from unittest.mock import MagicMock, patch

import pytest

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
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = '{"content":"본문"}'
        with (
            patch.object(gate, "_evaluate_with_rubric", return_value=3.6),
            patch.object(gate, "_self_critique") as mock_critique,
        ):
            out = gate.apply_self_critique(manuscript, "hud", [], "genre", ep_num=2)
        assert out == manuscript
        mock_critique.assert_not_called()

    def test_apply_self_critique_low_rubric_runs(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = '{"content":"본문"}'
        with (
            patch.object(gate, "_evaluate_with_rubric", return_value=2.0),
            patch.object(
                gate, "_self_critique", return_value={"has_issues": False, "issues": [], "severity": "low"}
            ) as mock_critique,
            patch.object(gate, "_fix_manuscript_issues") as mock_fix,
        ):
            out = gate.apply_self_critique(manuscript, "hud", [], "genre", ep_num=2)
        assert out == manuscript
        mock_critique.assert_called_once()
        mock_fix.assert_not_called()

    def test_self_critique_no_issues(self):
        gate = ChiefWriterQualityGate(_make_host())
        manuscript = json.dumps({"content": "clean content"}, ensure_ascii=False)
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

    def test_check_cliche_overuse(self):
        gate = ChiefWriterQualityGate(_make_host())
        issues = gate._check_cliche_overuse("plain content", "genre", ep_num=1)
        assert isinstance(issues, list)

    def test_check_cliche_overuse_recent(self):
        gate = ChiefWriterQualityGate(_make_host())
        with patch.object(gate, "_count_recent_cliches", return_value={"k1": 3, "k2": 4}):
            issues = gate._check_cliche_overuse("content", "genre", ep_num=10)
        assert any(i.get("type") == "cliche_overuse_recent" for i in issues)

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
        result = gate._count_recent_cliches(ep_num=10, manuscript=keyword * 2, window=3)
        assert result
        assert keyword in result

    def test_count_recent_cliches_empty_cache(self):
        host = _make_host()
        host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
        gate = ChiefWriterQualityGate(host)
        result = gate._count_recent_cliches(ep_num=10, manuscript="", window=3)
        assert result == {}
