from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.domain.agents.chief_writer import ChiefWriter
from modules.validation.blocking_validator import BlockingValidator
from modules.validation.validation_orchestrator import ValidationOrchestrator


def _pass_check(*_args, **_kwargs):
    return {"check": "stub", "passed": True}


def test_blocking_validator_preserves_headerless_scene_advisory_records():
    validator = BlockingValidator(enable_justification_checks=False)
    for name in (
        "_check_dead_npc_resurrection",
        "_check_unowned_item_usage",
        "_check_destroyed_location_visit",
        "_check_minimum_length",
        "_check_required_scenes",
        "_check_scope_overflow",
        "_check_damaged_item_usage",
        "_check_relationship_consistency",
        "_check_information_consistency",
        "_check_wuxia_technique_realm_consistency",
        "_check_cliffhanger_ending",
    ):
        setattr(validator, name, _pass_check)

    validator._check_scene_completeness = lambda *_args, **_kwargs: {
        "check": "scene_completeness",
        "passed": True,
        "warning": "1/4 scenes materially weak (Director advisory)",
        "severity": "ADVISORY",
        "advisory_only": True,
        "authority": "director",
        "details": {
            "complete_scenes": 1,
            "total_scenes": 4,
            "incomplete": ["scene_2", "scene_3"],
            "min_scene_length": 300,
        },
        "suggestion": "Do not add visible scene headers; strengthen the scene body beats.",
    }

    result = validator.validate("synthetic manuscript", {"mode": "MANUSCRIPT"})

    assert result["passed"] is True
    assert any("scene_completeness" in warning for warning in result["warnings"])
    advisory = result["structured_advisories"][0]
    assert advisory["category"] == "scene_completeness"
    assert advisory["visible_markdown_headers_required"] is False
    assert advisory["markdown_header_required"] is False
    assert advisory["patch_targets"] == [
        "scene_2: strengthen semantic scene materialization",
        "scene_3: strengthen semantic scene materialization",
    ]
    assert advisory["patch_target_records"][0]["scene_id"] == "scene_2"
    assert advisory["patch_target_records"][0]["visible_markdown_headers_required"] is False


def test_validation_orchestrator_blocking_advisory_carries_structured_records():
    blocking_result = {
        "passed": True,
        "failures": [],
        "warnings": ["scene_completeness: weak"],
        "structured_advisories": [
            {
                "category": "scene_completeness",
                "message": "weak semantic materialization",
                "patch_target_records": [{"summary": "scene_2", "scene_id": "scene_2"}],
            }
        ],
    }

    advisory = ValidationOrchestrator._build_blocking_advisory(
        ValidationOrchestrator.__new__(ValidationOrchestrator),
        blocking_result,
    )

    assert advisory["structured_advisories"][0]["category"] == "scene_completeness"
    assert advisory["warnings"] == ["scene_completeness: weak"]


def test_stage4_blocking_advisory_records_reach_retry_evidence():
    ctx = SimpleNamespace(ui=SimpleNamespace(log=MagicMock()))
    rounder = Stage4InterviewRound(ctx)
    validation_result = {"warnings": [], "warning_count": 0, "focus_points": []}
    structured_advisory = {
        "category": "scene_completeness",
        "severity": "ADVISORY",
        "target_kind": "scene_structure",
        "message": "headerless scene body is under-materialized",
        "visible_markdown_headers_required": False,
        "patch_target_records": [{"summary": "scene_2", "scene_id": "scene_2"}],
    }

    rounder._apply_blocking_validator_advisories(
        validation_result=validation_result,
        bv_advisory_warnings=["scene_completeness: weak"],
        bv_structured_advisories=[structured_advisory],
        candidate_index=1,
        next_ep=15,
        round_num=0,
    )
    provenance = rounder._build_retry_feedback_provenance(
        director_result={"feedback": {}},
        director_feedback="",
        selected_validation=validation_result,
        round_num=1,
    )

    assert validation_result["structured_repair_advisories"][0]["patch_target_records"][0]["scene_id"] == "scene_2"
    assert "[SCENE] scene_completeness" in provenance["merged_feedback"]
    assert "scenes=scene_2" in provenance["merged_feedback"]
    assert "no visible Markdown scene headers required" in provenance["merged_feedback"]


def test_stage4_weak_transition_record_formats_as_structured_scene_evidence():
    rounder = Stage4InterviewRound(SimpleNamespace(ui=SimpleNamespace(log=MagicMock())))

    lines = rounder._structured_validation_evidence_lines(
        {
            "structured_repair_advisories": [
                {
                    "category": "scene_transition_marker_missing",
                    "severity": "low",
                    "target_kind": "transition",
                    "message": "weak transition evidence",
                    "patch_target_records": [
                        {
                            "summary": "transition after scene_1",
                            "scene_id": "scene_1",
                            "paragraph_span": {"start": 5, "end": 6},
                        }
                    ],
                }
            ]
        }
    )

    assert lines == [
        "[SCENE] scene_transition_marker_missing | low | transition | weak transition evidence | scenes=scene_1 | paragraph_spans=5-6"
    ]


def test_stage4_structured_repair_evidence_payload_preserves_candidate_records():
    rounder = Stage4InterviewRound(SimpleNamespace(ui=SimpleNamespace(log=MagicMock())))

    payload = rounder._build_stage4_structured_repair_evidence(
        [
            {
                "structured_repair_advisories": [
                    {
                        "category": "scene_completeness",
                        "severity": "ADVISORY",
                        "target_kind": "scene_structure",
                        "message": "scene body needs materialization",
                        "visible_markdown_headers_required": False,
                        "patch_target_records": [{"summary": "scene_2", "scene_id": "scene_2"}],
                    }
                ]
            }
        ]
    )

    assert payload["schema_version"] == "stage4_structured_repair_evidence_v1"
    assert payload["authority"] == "python_validation_companion"
    assert payload["advisory_count"] == 1
    assert payload["candidates"][0]["candidate_label"] == "A"
    assert payload["candidates"][0]["advisories"][0]["patch_target_records"][0]["scene_id"] == "scene_2"
    assert "Director remains final quality authority" in payload["authority_note"]
    assert "scenes=scene_2" in payload["candidates"][0]["evidence_lines"][0]


def test_fix_pack_guidance_preserves_patch_target_record_header_contract():
    writer = ChiefWriter.__new__(ChiefWriter)

    guidance = writer._build_fix_pack_guidance(
        {
            "target_kind": "scene_structure",
            "patch_target_records": [
                {
                    "summary": "scene_2 body",
                    "scene_id": "scene_2",
                    "target_kind": "scene_structure",
                    "visible_markdown_headers_required": False,
                    "repair_guidance": "Do not add visible scene headers; strengthen the transition and body beats.",
                }
            ],
            "must_fix": ["Strengthen scene_2 materialization."],
            "do_not_regress": ["Keep JSON output as one object."],
            "success_condition": "scene_2 is materially present without Markdown headers.",
        }
    )

    assert "patch_target_records" in guidance
    assert "scene_id=scene_2" in guidance
    assert "visible_markdown_headers_required=false" in guidance
    assert "Keep JSON output as one object." in guidance
