from __future__ import annotations

from scripts.tr_batch_harness import build_prompt as build_blockguide_prompt
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
