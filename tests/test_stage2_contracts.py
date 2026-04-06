from modules.core.stage2_contracts import merge_stage2_authoritative_packet


def test_merge_stage2_authoritative_packet_preserves_non_empty_authoritative_values():
    result = merge_stage2_authoritative_packet(
        {
            "world_joint": "llm-world",
            "status_shadow": {
                "expected_injuries": "llm-wound",
                "item_consumption": ["천풍검"],
            },
        },
        {
            "world_joint": "stale-world",
            "status_shadow": {
                "expected_injuries": "stale-wound",
                "item_consumption": [],
                "key_stat_change": "fallback-stat",
            },
            "final_location": "block-city",
        },
    )

    assert result == {
        "world_joint": "llm-world",
        "status_shadow": {
            "expected_injuries": "llm-wound",
            "item_consumption": ["천풍검"],
            "key_stat_change": "fallback-stat",
        },
        "final_location": "block-city",
    }


def test_merge_stage2_authoritative_packet_backfills_empty_authoritative_values():
    result = merge_stage2_authoritative_packet(
        {
            "world_joint": "",
            "status_shadow": {
                "item_consumption": [],
                "expected_injuries": "",
            },
        },
        {
            "world_joint": "stable-world",
            "status_shadow": {
                "item_consumption": ["망령패"],
                "expected_injuries": "none",
                "key_stat_change": "fallback-stat",
            },
        },
    )

    assert result == {
        "world_joint": "stable-world",
        "status_shadow": {
            "item_consumption": ["망령패"],
            "expected_injuries": "none",
            "key_stat_change": "fallback-stat",
        },
    }
