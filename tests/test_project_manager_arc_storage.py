import time

from modules.core.project_manager import ProjectContext


def _sample_arc(arc_no: int) -> dict:
    return {
        "arc_no": arc_no,
        "title": f"Arc {arc_no}",
        "ep_start": arc_no,
        "ep_end": arc_no,
        "ep_count": 1,
        "tactical_doc": f"Episode {arc_no} tactical test",
        "beat_sequence": [],
    }


def _sample_arc_with_authority_packet(arc_no: int) -> dict:
    return {
        **_sample_arc(arc_no),
        "joint_docs": {
            "final_location": "Gangnam HQ",
            "physical_inventory": ["Ecuador memo", "BlackBerry 7100"],
            "world_joint": "WTI and Ecuador news watch",
        },
        "state_constraints": {
            "arc_start_state": {
                "location": "Yeouido SOHO office",
                "equipment": ["Corporate seal", "BlackBerry 7100"],
            },
            "arc_end_state": {
                "location": "Gangnam HQ",
                "equipment": ["BlackBerry 7100", "Ecuador memo"],
            },
            "items_acquired": ["Ecuador memo"],
            "items_consumed": ["Trading fee 1500000 KRW"],
        },
    }


def test_save_v20_anchor_arcs_exports_only_after_db_success(tmp_path):
    project = ProjectContext("arc_storage", root_dir=tmp_path)
    try:
        project.db.save_anchor = lambda stage, data: False

        assert project.save_v20_anchor("arcs", [_sample_arc(1)]) is False
        assert not (project.paths.plans_arcs / "arc_001.txt").exists()
    finally:
        project.close()


def test_save_v20_anchor_arcs_skips_rewriting_unchanged_export(tmp_path):
    project = ProjectContext("arc_storage", root_dir=tmp_path)
    try:
        assert project.save_v20_anchor("arcs", [_sample_arc(1)]) is True
        arc_path = project.paths.plans_arcs / "arc_001.txt"
        first_mtime = arc_path.stat().st_mtime_ns

        time.sleep(0.02)
        assert project.save_v20_anchor("arcs", [_sample_arc(1)]) is True

        assert arc_path.stat().st_mtime_ns == first_mtime
    finally:
        project.close()


def test_project_context_reloads_authoritative_arc_payloads(tmp_path):
    project = ProjectContext("arc_storage", root_dir=tmp_path)
    try:
        assert project.save_v20_anchor("arcs", [_sample_arc(2), _sample_arc(1)]) is True
    finally:
        project.close()

    reloaded = ProjectContext("arc_storage", root_dir=tmp_path)
    try:
        assert [arc["arc_no"] for arc in reloaded.arcs] == [1, 2]
    finally:
        reloaded.close()


def test_save_v20_anchor_arcs_export_includes_authoritative_carryover_packet(tmp_path):
    project = ProjectContext("arc_storage", root_dir=tmp_path)
    try:
        assert project.save_v20_anchor("arcs", [_sample_arc_with_authority_packet(2)]) is True
        arc_path = project.paths.plans_arcs / "arc_002.txt"
        rendered = arc_path.read_text(encoding="utf-8")

        assert "[Carryover Authority Packet]" in rendered
        assert "- start_location: Yeouido SOHO office" in rendered
        assert "- end_location: Gangnam HQ" in rendered
        assert "- start_equipment: ['Corporate seal', 'BlackBerry 7100']" in rendered
        assert "- end_equipment: ['BlackBerry 7100', 'Ecuador memo']" in rendered
        assert "- items_acquired: ['Ecuador memo']" in rendered
        assert "- items_consumed: ['Trading fee 1500000 KRW']" in rendered
        assert "- world_joint: WTI and Ecuador news watch" in rendered
    finally:
        project.close()


def test_save_v20_anchor_arcs_prefers_arc_end_state_over_stale_joint_docs_inventory(tmp_path):
    project = ProjectContext("arc_storage", root_dir=tmp_path)
    try:
        arc = _sample_arc_with_authority_packet(3)
        arc["joint_docs"]["physical_inventory"] = ["Ghost token"]
        arc["state_constraints"]["arc_end_state"]["equipment"] = ["BlackBerry 7100", "Ecuador memo"]
        assert project.save_v20_anchor("arcs", [arc]) is True

        rendered = (project.paths.plans_arcs / "arc_003.txt").read_text(encoding="utf-8")
        assert "- end_equipment: ['BlackBerry 7100', 'Ecuador memo']" in rendered
        assert "- end_equipment: ['Ghost token']" not in rendered
    finally:
        project.close()
