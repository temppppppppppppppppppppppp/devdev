"""Stage2Optimizer regression tests."""

from modules.core.stage2_optimizer import ArcAutoCorrector


def test_remove_duplicate_items_normalizes_item_key():
    corrector = ArcAutoCorrector()
    arc = {
        "state_constraints": {
            "items_acquired": [
                {"item": "철검"},
                {"name": "벽력단"},
            ]
        }
    }
    prev_arcs = [
        {
            "state_constraints": {"items_acquired": ["철검"]},
            "joint_docs": {"physical_inventory": []},
        }
    ]

    corrected = corrector._remove_duplicate_items(arc, prev_arcs)

    assert corrected["state_constraints"]["items_acquired"] == ["벽력단"]
