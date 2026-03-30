from __future__ import annotations

from scripts.tr_batch_harness import build_prompt as build_blockguide_prompt, render_pattern_feedback_lines
from scripts.wuxia_tr_batch_harness import build_prompt as build_wuxguide_prompt


def test_blockguide_tr_prompt_includes_harness_digest_section() -> None:
    prompt = build_blockguide_prompt(
        draft_blocks=[],
        roadmap_blocks=None,
        meta={"title": "Demo", "genre": "investment", "protagonist": "Hero", "logline": "Grow the company."},
        start=1,
        batch_size=3,
        mode="flash",
    )

    assert "## Harness Digest" in prompt
    assert "- family: blockguide" in prompt
    assert "### Continuity Equalities" in prompt
    assert "capital_before == 직전 capital_after" in prompt


def test_wuxguide_tr_prompt_includes_harness_digest_section() -> None:
    prompt = build_wuxguide_prompt(
        draft_blocks=[],
        roadmap_blocks=None,
        meta={"title": "Demo", "genre": "wuxia", "protagonist": "Hero", "logline": "Climb the realm ladder."},
        start=1,
        batch_size=3,
        mode="flash",
    )

    assert "## Harness Digest" in prompt
    assert "- family: wuxguide" in prompt
    assert "### Lexicon Bans" in prompt
    assert "genre_ext.realm_before == previous realm_after" in prompt


def _make_history_block(block_no: int, opponent: str, weakness: str) -> dict:
    return {
        "block_id": f"Block {block_no}",
        "title": f"Block {block_no} title",
        "content": {
            "context": "x" * 120,
            "event_villain": "x" * 80,
            "solution": "x" * 120,
            "reward": "x" * 80,
        },
        "stakes": "x" * 50,
        "foreshadow": [f"Block {block_no + 1} clue."] if block_no < 10 else [],
        "callback": [f"Block {block_no - 1} clue."] if block_no > 1 else [],
        "genre_ext": {
            "opponent": {"name": opponent, "weakness_exploited": weakness},
            "deal_type": f"deal_{block_no}",
            "method": f"method_{block_no}",
            "section_rotation": "rotation",
        },
        "emotional_beat": {"type": "resolve" if block_no % 2 else "pressure"},
        "relationship_delta": [],
        "regression_ext": {},
    }


def test_pattern_feedback_lines_empty_for_no_history() -> None:
    assert render_pattern_feedback_lines([]) == []


def test_pattern_feedback_lines_includes_frequent_opponent() -> None:
    blocks = [_make_history_block(i, "Same Corp", f"weakness_{i}") for i in range(1, 11)]
    lines = render_pattern_feedback_lines(blocks)
    joined = "\n".join(lines)
    assert "## 패턴 피드백" in joined
    assert "Same Corp" in joined


def test_blockguide_prompt_includes_pattern_feedback_when_history_present() -> None:
    blocks = [_make_history_block(i, "Same Corp", f"weakness_{i}") for i in range(1, 6)]
    prompt = build_blockguide_prompt(
        draft_blocks=blocks,
        roadmap_blocks=None,
        meta={"title": "Demo", "genre": "investment", "protagonist": "Hero", "logline": "Grow."},
        start=6,
        batch_size=3,
        mode="flash",
    )
    assert "## 패턴 피드백" in prompt
    assert "Same Corp" in prompt
