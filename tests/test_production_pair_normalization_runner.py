from __future__ import annotations

import scripts.production_pair_normalization_runner as runner


def _phase0_payload() -> dict:
    return {
        "project": {"title_ko": "골든 루트", "format": "investment"},
        "work_identity_surface": {
            "work_id": "golden_route",
            "title": "골든 루트",
            "commercial_label": "골든 카나리아",
            "slug_aliases": ["카나리아 테스트"],
        },
        "phase0_design": {
            "arcs": [],
            "npc_timeline": [],
            "foreshadow_map": [],
            "opponent_transition_plan": [],
        },
    }


def _canonical_bi(*, title: str) -> dict:
    return {
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {
                    "title": title,
                    "commercial_label": "골든 카나리아",
                    "slug_aliases": ["카나리아 테스트"],
                }
            }
        }
    }


def test_inspect_naming_surface_accepts_alias_titles_inside_phase0_surface() -> None:
    findings: list[runner.Finding] = []
    counts: dict[str, int] = {}
    notes: list[str] = []

    status, resolution, canonical_title, observed_bi_title = runner.inspect_naming_surface(
        phase0_data=_phase0_payload(),
        canonical_bi=_canonical_bi(title="골든 카나리아"),
        untouched_historical=True,
        findings=findings,
        counts=counts,
        notes=notes,
    )

    assert status == "alias-surface"
    assert resolution == "phase0.work_identity_surface"
    assert canonical_title == "골든 루트"
    assert observed_bi_title == "골든 카나리아"
    assert counts["naming_surface_available"] == 1
    assert counts["naming_allowed_title_count"] == 3
    assert [finding.code for finding in findings] == ["BI-NAMING-ALIAS-SURFACE"]
    assert "골든 카나리아 -> 골든 루트" in notes[0]


def test_inspect_naming_surface_flags_titles_outside_phase0_surface() -> None:
    findings: list[runner.Finding] = []
    counts: dict[str, int] = {}
    notes: list[str] = []

    status, resolution, canonical_title, observed_bi_title = runner.inspect_naming_surface(
        phase0_data=_phase0_payload(),
        canonical_bi=_canonical_bi(title="완전 다른 제목"),
        untouched_historical=True,
        findings=findings,
        counts=counts,
        notes=notes,
    )

    assert status == "drifting"
    assert resolution == "phase0.work_identity_surface"
    assert canonical_title == "골든 루트"
    assert observed_bi_title == "완전 다른 제목"
    assert counts["naming_surface_available"] == 1
    assert counts["naming_allowed_title_count"] == 3
    assert [finding.code for finding in findings] == ["BI-NAMING-DRIFT"]
    assert "완전 다른 제목 vs 골든 루트" in notes[0]
