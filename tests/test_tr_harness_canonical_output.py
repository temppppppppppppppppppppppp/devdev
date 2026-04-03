from __future__ import annotations

import json

import scripts.tr_batch_harness as blockguide_harness
import scripts.wuxia_tr_batch_harness as wuxguide_harness


def _block(label: str) -> dict:
    return {
        "block_id": label,
        "title": f"{label} title",
        "content": {
            "context": f"{label} context",
            "event_villain": f"{label} villain",
            "solution": f"{label} solution",
            "reward": f"{label} reward",
        },
    }


def test_blockguide_write_json_emits_canonical_wrapper(tmp_path):
    output = tmp_path / "draft.json"

    blockguide_harness.write_json(output, [_block("Block 3")])
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["_schema"] == "tr.v1"
    assert payload["_total_blocks"] == 1
    assert payload["blocks"][0]["block_id"] == "Block 3"
    assert payload["blocks"][0]["block_no"] == 3


def test_wuxguide_write_json_emits_canonical_wrapper(tmp_path):
    output = tmp_path / "draft.json"

    wuxguide_harness.write_json(output, [_block("Block 4")])
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["_schema"] == "tr.v1"
    assert payload["_total_blocks"] == 1
    assert payload["blocks"][0]["block_id"] == "Block 4"
    assert payload["blocks"][0]["block_no"] == 4


def test_metrics_accept_wrapper_payloads_for_blockguide():
    metrics = blockguide_harness.compute_treatment_metrics(
        {
            "_schema": "tr.v1",
            "_total_blocks": 1,
            "blocks": [
                {
                    **_block("Block 1"),
                    "stakes": "stakes",
                    "genre_ext": {
                        "capital_before": "1억",
                        "capital_after": "2억",
                        "business_sector": "바이오",
                        "section_rotation": "시장",
                        "deal_type": "인수",
                        "method": "협상",
                        "opponent": {"name": "상대", "weakness_exploited": "느린 승인"},
                    },
                    "power_shift": {"protagonist": "up"},
                    "foreshadow": [],
                    "callback": [],
                    "regression_ext": {"is_regressor": False, "regression_type": "none"},
                }
            ],
        }
    )

    assert metrics["block_count"] == 1


def test_metrics_accept_wrapper_payloads_for_wuxguide():
    metrics = wuxguide_harness.compute_treatment_metrics(
        {
            "_schema": "tr.v1",
            "_total_blocks": 1,
            "blocks": [
                {
                    **_block("Block 1"),
                    "stakes": "stakes",
                    "genre_ext": {
                        "realm_before": "Body Tempering",
                        "realm_after": "Meridian Opening",
                        "internal_energy_before": 10,
                        "internal_energy_after": 12,
                        "faction_position": "outer disciple",
                        "jianghu_reputation": "unknown",
                        "enemy_pressure": "low",
                        "martial_art_gain": "sword insight",
                        "artifact_or_manual_gain": "none",
                        "opponent": {"name": "Iron Hall", "weakness_exploited": "wide stance"},
                        "success_pattern": "wins by timing",
                    },
                    "power_shift": {"protagonist": "up"},
                    "foreshadow": [],
                    "callback": [],
                    "regression_ext": {"is_regressor": False, "regression_type": "none"},
                    "emotional_beat": {"type": "resolve"},
                    "location": {"place": "yard"},
                }
            ],
        }
    )

    assert metrics["block_count"] == 1
