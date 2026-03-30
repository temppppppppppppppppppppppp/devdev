import time

from modules.core.project_manager import ProjectContext


def _sample_arc(arc_no: int) -> dict:
    return {
        "arc_no": arc_no,
        "title": f"Arc {arc_no}",
        "ep_start": arc_no,
        "ep_end": arc_no,
        "ep_count": 1,
        "tactical_doc": f"제 {arc_no}화: 테스트",
        "beat_sequence": [],
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
