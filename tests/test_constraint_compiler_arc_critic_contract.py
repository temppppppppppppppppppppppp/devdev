from modules.domain.agents.arc_critic import ARC_CRITIQUE_PROMPT, ArcCritic
from modules.domain.agents.constraint_compiler import ConstraintCompiler


def test_constraint_compiler_prefers_explicit_empty_protagonist_items_over_legacy_alias():
    compiler = ConstraintCompiler()
    prev_arcs = [
        {
            "arc_no": 1,
            "state_constraints": {
                "protagonist_items": [],
                "items_acquired": ["stale-only-item"],
                "items_consumed": [],
            },
        }
    ]

    result = compiler._collect_all_items(prev_arcs)

    assert "stale-only-item" not in result


def test_constraint_compiler_extract_current_state_prefers_arc_end_equipment_authority():
    compiler = ConstraintCompiler.__new__(ConstraintCompiler)
    last_arc = {
        "joint_docs": {"final_location": "부산", "physical_inventory": ["stale-ledger"], "world_joint": "stable"},
        "state_constraints": {
            "arc_end_state": {
                "location": "시장",
                "equipment": [],
                "capital": "3억원",
                "total_assets": "7억원",
                "portfolio_position": "현금 보유",
            }
        },
    }

    state = compiler._extract_current_state(last_arc, state_extractor_result=None)

    assert state["location"] == "시장"
    assert state["equipment"] == []


def test_constraint_compiler_checklist_uses_canonical_protagonist_items_language():
    compiler = ConstraintCompiler()
    text = compiler.compile(
        prev_arcs=[
            {
                "arc_no": 1,
                "state_constraints": {"protagonist_items": ["장부"], "items_consumed": []},
                "joint_docs": {"final_location": "시장", "physical_inventory": ["장부"], "world_joint": "stable"},
            }
        ]
    )

    assert "protagonist_items(legacy alias: items_acquired)" in text


def test_arc_critic_prompt_uses_canonical_protagonist_items_language():
    assert "protagonist_items(legacy alias: items_acquired)" in ARC_CRITIQUE_PROMPT


def test_arc_critic_remove_items_falls_back_to_legacy_items_acquired_when_canonical_missing():
    critic = ArcCritic.__new__(ArcCritic)
    arc = {"state_constraints": {"items_acquired": ["fallback-only-item", "keep-item"]}}
    critique = {"auto_fixes": {"remove_items": ["fallback-only-item"]}}

    fixed = critic._apply_auto_fixes(arc, critique)

    assert fixed["state_constraints"]["items_acquired"] == ["keep-item"]
