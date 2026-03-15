import json

from modules.core.stagewise_manuscript_truth_report import (
    build_stagewise_manuscript_truth_report,
    render_stagewise_manuscript_truth_markdown,
    write_stagewise_manuscript_truth_report,
)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_fixture_project(tmp_path):
    project = tmp_path / "fixture_project"

    _write_json(
        project / "logs" / "artifacts" / "stage2" / "arc_001" / "attempt_01" / "final_arc__creative.json",
        {
            "arc_no": 1,
            "title": "Arc One",
            "ep_start": 1,
            "ep_end": 4,
            "constraint_summary": "",
        },
    )
    _write_json(
        project / "logs" / "artifacts" / "stage2" / "arc_002" / "attempt_01" / "final_arc__balanced.json",
        {
            "arc_no": 2,
            "title": "Arc Two",
            "ep_start": 5,
            "ep_end": 8,
            "constraint_summary": "Do not reacquire the sealed ledger.",
        },
    )

    ep4_blueprint_path = project / "logs" / "artifacts" / "stage3" / "ep_0004" / "attempt_01" / "final_blueprint__dialogue_focused.json"
    ep5_blueprint_path = project / "logs" / "artifacts" / "stage3" / "ep_0005" / "attempt_01" / "final_blueprint__action_focused.json"
    _write_json(
        ep4_blueprint_path,
        {
            "title": "Episode Four",
            "ending_hook": "Attorney call lands at the end of the episode.",
            "expected_ending": "Legal pressure hook.",
        },
    )
    _write_json(
        ep5_blueprint_path,
        {
            "title": "Episode Five",
            "ending_hook": "Two operatives block the exit.",
            "expected_ending": "Physical threat hook.",
        },
    )

    decisions_path = project / "logs" / "session" / "decisions.jsonl"
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "stage3",
                        "ep_num": 4,
                        "result": "PASS",
                        "score": 100,
                        "meta": {
                            "candidate_key": "dialogue|focused",
                            "artifact_path": "logs/artifacts/stage3/ep_0004/attempt_01/final_blueprint__dialogue_focused.json",
                            "selection_reason": "Best local hook.",
                            "verdict_reason": "Attorney pressure lands cleanly.",
                        },
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "stage": "stage3",
                        "ep_num": 5,
                        "result": "PASS",
                        "score": 96,
                        "meta": {
                            "candidate_key": "action|focused",
                            "artifact_path": "logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__action_focused.json",
                            "selection_reason": "Strong threat hook.",
                            "verdict_reason": "Keeps the action moving.",
                        },
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    ep4_terminal_path = project / "logs" / "artifacts" / "stage4" / "ep_0004" / "attempt_03" / "patched_after_fix__A.txt"
    ep4_terminal_path.parent.mkdir(parents=True, exist_ok=True)
    ep4_terminal_path.write_text(
        "Episode 4 opening line\nEpisode 4 legal hook line\n[원고_끝]\n{{ \"patch_state_updates\": {} }}\n",
        encoding="utf-8",
    )

    ep5_terminal_path = project / "logs" / "artifacts" / "stage4" / "ep_0005" / "attempt_04" / "final_manuscript__C.txt"
    ep5_terminal_path.parent.mkdir(parents=True, exist_ok=True)
    ep5_terminal_path.write_text(
        "Episode 5 opening line\nEpisode 5 threat hook line\n",
        encoding="utf-8",
    )

    episode_production_path = project / "logs" / "episode_production.jsonl"
    episode_production_path.parent.mkdir(parents=True, exist_ok=True)
    episode_production_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "ep": 4,
                        "round": 2,
                        "candidate_key": "A|balanced",
                        "artifact_path": "logs/artifacts/stage4/ep_0004/attempt_03/patched_after_fix__A.txt",
                        "selection_artifact_path": "logs/artifacts/stage4/ep_0004/attempt_03/selected_candidate__A.txt",
                        "verdict": "PASS",
                        "final_verdict": "PASS",
                        "selection_reason": "Episode 4 continuity repaired.",
                        "verdict_reason": "Episode 4 now preserves the legal pressure hook.",
                        "open_review": "None",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "ep": 5,
                        "round": 2,
                        "candidate_key": "A|balanced",
                        "artifact_path": "logs/artifacts/stage4/ep_0005/attempt_03/rejected_best__A.txt",
                        "selection_artifact_path": "logs/artifacts/stage4/ep_0005/attempt_03/rejected_best__A.txt",
                        "verdict": "REJECT",
                        "final_verdict": "REJECT",
                        "selection_reason": "Still contradicts episode 4.",
                        "verdict_reason": "Blueprint still conflicts with episode 4 all-in ending.",
                        "open_review": "Continuity contradiction remains unresolved.",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "ep": 5,
                        "round": 3,
                        "candidate_key": "C|twist",
                        "artifact_path": "logs/artifacts/stage4/ep_0005/attempt_04/final_manuscript__C.txt",
                        "selection_artifact_path": "logs/artifacts/stage4/ep_0005/attempt_04/selected_candidate__C.txt",
                        "verdict": "PASS",
                        "final_verdict": "PASS",
                        "selection_reason": "Preserves episode 4 continuity.",
                        "verdict_reason": "Candidate C keeps episode 4 all-in continuity while preserving tension.",
                        "open_review": "Repair succeeds.",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return project


def test_build_stagewise_manuscript_truth_report_normalizes_terminal_truth(tmp_path):
    project = _build_fixture_project(tmp_path)

    report = build_stagewise_manuscript_truth_report(project, project_label="projects/fixture")

    assert report["artifact_counts"]["stage2_selected_arc_files"] == 2
    assert report["artifact_counts"]["stage3_selected_blueprint_files"] == 2
    assert report["artifact_counts"]["stage4_terminal_passes"] == 2
    assert report["stage2_arc_truth"][0]["constraint_summary_state"] == "blank"
    assert report["stage2_arc_truth"][1]["constraint_summary_state"] == "present"
    assert report["stage4_terminal_truth"][0]["terminal_artifact_kind"] == "patched_after_fix"
    assert report["stage4_terminal_truth"][0]["last_narrative_line"] == "Episode 4 legal hook line"
    assert report["stage4_terminal_truth"][1]["terminal_artifact_kind"] == "final_manuscript"
    continuity = report["continuity_handoff"]["episode_4_to_5"]
    assert continuity["contradiction_summary"] == "Blueprint still conflicts with episode 4 all-in ending."
    assert continuity["repair_summary"] == "Candidate C keeps episode 4 all-in continuity while preserving tension."
    assert continuity["ep5_pass_round"]["candidate_key"] == "C|twist"


def test_render_and_write_stagewise_manuscript_truth_report(tmp_path):
    project = _build_fixture_project(tmp_path)

    report = build_stagewise_manuscript_truth_report(project, project_label="projects/fixture")
    markdown = render_stagewise_manuscript_truth_markdown(report)

    assert "Episode 4 -> Episode 5 Continuity Repair" in markdown
    assert "patched_after_fix" in markdown
    assert "dialogue\\|focused" in markdown

    markdown_output = tmp_path / "report.md"
    json_output = tmp_path / "report.json"
    written = write_stagewise_manuscript_truth_report(
        project,
        markdown_output=markdown_output,
        json_output=json_output,
        project_label="projects/fixture",
    )

    assert written["project"] == "projects/fixture"
    assert markdown_output.exists()
    assert json_output.exists()
    assert "Episode 4 -> Episode 5 Continuity Repair" in markdown_output.read_text(encoding="utf-8")
    payload = json.loads(json_output.read_text(encoding="utf-8"))
    assert payload["project"] == "projects/fixture"
