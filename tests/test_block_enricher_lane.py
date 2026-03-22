from unittest.mock import MagicMock, patch

from modules.domain.agents.block_enricher import BlockEnricher


def _make_enricher() -> BlockEnricher:
    enricher = BlockEnricher.__new__(BlockEnricher)
    enricher._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    return enricher


def test_enrich_block_retries_validation_and_director_with_truncated_tail_context():
    enricher = _make_enricher()
    enricher.analyze_block_density = MagicMock(
        return_value={"needs_enrichment": True, "density_score": 0.2, "missing_elements": ["scene"]}
    )

    initial_result = {
        "block_id": "B2",
        "content": {
            "context": "HEAD-VALIDATE\n" + ("A" * 70000) + "\nTAIL-VALIDATE",
            "event_villain": "적",
            "solution": "해결",
            "reward": "보상",
        },
    }
    validation_retry_result = {
        "block_id": "B2",
        "content": {
            "context": "HEAD-DIRECTOR\n" + ("B" * 70000) + "\nTAIL-DIRECTOR",
            "event_villain": "적2",
            "solution": "해결2",
            "reward": "보상2",
        },
    }
    director_retry_result = {
        "block_id": "B2",
        "content": {
            "context": "final",
            "event_villain": "적3",
            "solution": "해결3",
            "reward": "보상3",
        },
    }

    prompts = []
    ask_results = iter([initial_result, validation_retry_result, director_retry_result])

    def _fake_ask(prompt, temperature=0.7):
        prompts.append((prompt, temperature))
        return next(ask_results)

    enricher.ask = _fake_ask
    enricher._validate_enrichment = MagicMock(
        side_effect=[
            {"validation_result": "FAIL", "issues": ["tail issue"]},
            {"validation_result": "PASS", "issues": []},
        ]
    )
    enricher._director_audit_block = MagicMock(
        side_effect=[
            {"decision": "REJECT", "total_score": 45, "critical_issues": ["director issue"], "feedback": "fix it"},
            {"decision": "PASS", "total_score": 90},
        ]
    )

    result = enricher.enrich_block(
        current_block={"block_id": "B2", "content": {"context": "short"}},
        reference_block={"block_id": "B1", "content": {"context": "ref"}},
        prev_block={"block_id": "B1"},
        next_block={"block_id": "B3"},
    )

    assert result["enriched"] is True
    assert result["block"] == director_retry_result
    assert result["validation"]["validation_result"] == "PASS"
    assert result["director_audit"]["decision"] == "PASS"
    assert [temp for _, temp in prompts] == [0.7, 0.5, 0.4]
    assert "TAIL-VALIDATE" in prompts[1][0]
    assert "TAIL-DIRECTOR" in prompts[2][0]
    assert "...(중간 생략)..." in prompts[1][0]
    assert "...(중간 생략)..." in prompts[2][0]


def test_enrich_block_stops_on_invalid_validation_retry_payload():
    enricher = _make_enricher()
    current_block = {"block_id": "B2", "content": {"context": "short"}}
    enricher.analyze_block_density = MagicMock(
        return_value={"needs_enrichment": True, "density_score": 0.2, "missing_elements": ["scene"]}
    )
    enricher.ask = MagicMock(
        side_effect=[
            {
                "block_id": "B2",
                "content": {"context": "draft", "event_villain": "적", "solution": "해결", "reward": "보상"},
            },
            {"parsing_error": True},
        ]
    )
    enricher._validate_enrichment = MagicMock(return_value={"validation_result": "FAIL", "issues": ["fix"]})
    enricher._director_audit_block = MagicMock()

    result = enricher.enrich_block(
        current_block=current_block,
        reference_block={"block_id": "B1", "content": {"context": "ref"}},
        prev_block={"block_id": "B1"},
        next_block={"block_id": "B3"},
    )

    assert result == {"enriched": False, "reason": "재시도 LLM 결과 구조 불량", "block": current_block}
    assert enricher._director_audit_block.call_count == 0


def test_enrich_all_blocks_parallel_preserves_reference_and_tracks_skip_failure_stats():
    enricher = _make_enricher()
    treatment_blocks = [
        {"block_id": "B1", "content": {"context": "ref"}},
        {"block_id": "B2", "content": {"context": "thin-2"}},
        {"block_id": "B3", "content": {"context": "dense-3"}},
        {"block_id": "B4", "content": {"context": "thin-4"}},
    ]
    enrich_map = {
        "B2": {"enriched": True, "block": {"block_id": "B2+", "content": {"context": "enriched"}}},
        "B4": {"enriched": False, "reason": "농축 실패", "block": treatment_blocks[3]},
    }

    enricher.analyze_block_density = MagicMock(
        side_effect=[
            {"needs_enrichment": True},
            {"needs_enrichment": False},
            {"needs_enrichment": True},
        ]
    )
    enricher.enrich_block = MagicMock(side_effect=lambda current_block, **_: enrich_map[current_block["block_id"]])
    enricher._check_causal_errors = MagicMock(return_value=[])

    with patch("modules.domain.agents.block_enricher.time.sleep", return_value=None):
        result = enricher.enrich_all_blocks_parallel(
            treatment_blocks=treatment_blocks,
            protagonist_name="Hero",
            genre="wuxia",
            batch_size=1,
        )

    assert result["enriched_blocks"] == [
        treatment_blocks[0],
        {"block_id": "B2+", "content": {"context": "enriched"}},
        treatment_blocks[2],
        treatment_blocks[3],
    ]
    assert result["statistics"] == {
        "total": 4,
        "enriched_count": 1,
        "skipped_count": 2,
        "failed_count": 1,
        "causal_fixes": 0,
    }
    assert result["causal_issues_found"] == 0


def test_enrich_all_blocks_parallel_uses_enriched_prev_block_for_causal_fix():
    enricher = _make_enricher()
    treatment_blocks = [
        {"block_id": "B1", "content": {"context": "ref"}},
        {"block_id": "B2", "content": {"context": "thin-2"}},
        {"block_id": "B3", "content": {"context": "thin-3"}},
    ]
    enriched_b2 = {"block_id": "B2+", "content": {"context": "carry", "reward": "reward-2"}}
    first_b3 = {"block_id": "B3+", "content": {"context": "draft", "reward": "reward-3"}}
    fixed_b3 = {"block_id": "B3*", "content": {"context": "fixed", "reward": "reward-3-fixed"}}

    enricher.analyze_block_density = MagicMock(side_effect=[{"needs_enrichment": True}, {"needs_enrichment": True}])

    def _fake_enrich_block(current_block, **_kwargs):
        if current_block["block_id"] == "B2":
            return {"enriched": True, "block": enriched_b2}
        return {"enriched": True, "block": first_b3}

    enricher.enrich_block = MagicMock(side_effect=_fake_enrich_block)
    enricher._check_causal_errors = MagicMock(return_value=[{"block_index": 2, "issue": "carryover missing"}])
    enricher._re_enrich_with_causal_fix = MagicMock(return_value={"enriched": True, "block": fixed_b3})

    with patch("modules.domain.agents.block_enricher.time.sleep", return_value=None):
        result = enricher.enrich_all_blocks_parallel(
            treatment_blocks=treatment_blocks,
            protagonist_name="Hero",
            genre="wuxia",
            batch_size=1,
        )

    assert result["enriched_blocks"] == [treatment_blocks[0], enriched_b2, fixed_b3]
    assert result["statistics"] == {
        "total": 3,
        "enriched_count": 2,
        "skipped_count": 1,
        "failed_count": 0,
        "causal_fixes": 1,
    }
    assert result["causal_issues_found"] == 1
    assert enricher._re_enrich_with_causal_fix.call_args.kwargs["enriched_prev_block"] is enriched_b2
