from __future__ import annotations

import json
import sys
from pathlib import Path

import scripts.run_work_guard_v1 as runner


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_evaluate_work_guard_v1_passes_complete_shape(tmp_path):
    yaml_path = tmp_path / "demo.yaml"
    _write_yaml(
        yaml_path,
        "\n".join(
            [
                "work_identity:",
                "  work_id: demo_work",
                "  work_type: office_power",
                "  one_line_truth: 결재선 병목을 먼저 읽는 사원이 조직의 관문이 된다",
                "  tracking_slots:",
                "    - 결재선 위치 상승",
                "    - 재평가 전환",
                "  mandatory_scene_engines:",
                "    - 숨은 병목을 먼저 읽고 우회 상신하는 장면",
                "    - 활약 직후 태도 변화가 찍히는 장면",
                "  forbidden_flattenings:",
                "    - 회개물 스타트",
                "    - 비굴한 해명",
                "    - 자기연민 소비",
                "    - 활약 후 태도 변화 없음",
                "  protagonist_weapon:",
                "    - 결재선 병목을 먼저 읽는 판단",
                "  protagonist_evaluation:",
                "    admiration_axes:",
                "      - 먼저 읽음",
                "      - 결과로 인정 강제",
            ]
        ),
    )

    report = runner.evaluate_work_guard_v1(yaml_path, source="path")

    assert report["status"] == "pass"
    assert report["exit_code"] == runner.EXIT_PASS
    assert report["work_id"] == "demo_work"
    assert report["counts"]["tracking_slots"] == 2
    assert report["holds"] == []


def test_evaluate_work_guard_v1_holds_on_empty_required_lists(tmp_path):
    yaml_path = tmp_path / "demo.yaml"
    _write_yaml(
        yaml_path,
        "\n".join(
            [
                "work_identity:",
                "  work_id: demo_work",
                "  work_type: office_power",
                "  one_line_truth: 조직의 관문이 된다",
                "  tracking_slots: []",
                "  mandatory_scene_engines: []",
                "  forbidden_flattenings:",
                "    - 회개물 스타트",
                "  protagonist_weapon: []",
            ]
        ),
    )

    report = runner.evaluate_work_guard_v1(yaml_path, source="path")

    assert report["status"] == "hold"
    assert report["exit_code"] == runner.EXIT_HOLD
    hold_codes = {item["code"] for item in report["holds"]}
    assert "empty_tracking_slots" in hold_codes
    assert "empty_mandatory_scene_engines" in hold_codes
    assert "shallow_forbidden_flattenings" in hold_codes
    assert "empty_protagonist_weapon" in hold_codes


def test_evaluate_work_guard_v1_fails_on_missing_minimum_fields(tmp_path):
    yaml_path = tmp_path / "demo.yaml"
    _write_yaml(
        yaml_path,
        "\n".join(
            [
                "work_identity:",
                "  work_id: demo_work",
                "  work_type: office_power",
                "  tracking_slots:",
                "    - 결재선 위치 상승",
            ]
        ),
    )

    report = runner.evaluate_work_guard_v1(yaml_path, source="path")

    assert report["status"] == "fail"
    assert report["exit_code"] == runner.EXIT_FAIL
    failure_codes = {item["code"] for item in report["failures"]}
    assert "missing_one_line_truth" in failure_codes
    assert "missing_mandatory_scene_engines" in failure_codes
    assert "missing_forbidden_flattenings" in failure_codes
    assert "missing_protagonist_weapon" in failure_codes


def test_resolve_target_path_uses_work_id_library_resolution(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    work_guard_path = tmp_path / "work_guards" / "investment" / "demo.yaml"
    _write_yaml(work_guard_path, "work_identity:\n  work_id: demo\n")

    resolved, source = runner.resolve_target_path(path_value=None, work_id="demo", project_dir=None)

    assert source == "work_id"
    assert resolved == work_guard_path


def test_main_json_output_uses_project_dir_runtime_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    project_dir = tmp_path / "project_a"
    yaml_path = project_dir / "config" / "work_guard.yaml"
    _write_yaml(
        yaml_path,
        "\n".join(
            [
                "work_identity:",
                "  work_id: demo_project",
                "  work_type: blockguide",
                "  one_line_truth: 주인공이 병목을 관문으로 바꾼다",
                "  tracking_slots:",
                "    - 관문 전환",
                "    - 재평가 전환",
                "  mandatory_scene_engines:",
                "    - 먼저 읽고 공개 증명하는 장면",
                "    - 직후 서열 변화가 찍히는 장면",
                "  forbidden_flattenings:",
                "    - 회개물 스타트",
                "    - 비굴한 해명",
                "    - 자기연민 소비",
                "    - 활약 후 태도 변화 없음",
                "  protagonist_weapon:",
                "    - 병목을 먼저 읽는 판단",
            ]
        ),
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_work_guard_v1.py", "--project-dir", str(project_dir), "--json"],
    )

    exit_code = runner.main()
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == runner.EXIT_PASS
    assert payload["status"] == "pass"
    assert payload["source"] == "project_dir"
    assert payload["path"] == str(yaml_path)
