import json
from pathlib import Path

from scripts.mojibake_global_survey import survey


def test_survey_quarantines_historical_archive_from_active_baseline(tmp_path):
    archived = tmp_path / "projects" / "archive" / "logs" / "bad.log"
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text("archive ?? mojibake\n", encoding="utf-8")

    active = tmp_path / "modules" / "live_bad.py"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text("print('live ?? mojibake')\n", encoding="utf-8")

    manifest_path = tmp_path / "docs" / "2026-03-13" / "mojibake-archive-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "path": "projects/archive/logs/bad.log",
                        "status": "historical-corrupt-archive",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report = survey(tmp_path, sample_limit=1)

    assert report["summary"]["archive_manifest_path"] == "docs/2026-03-13/mojibake-archive-manifest.json"
    assert report["summary"]["quarantined_archive_file_count"] == 1
    assert report["summary"]["suspicious_file_count"] == 1
    assert report["suspicious_files"][0]["path"] == "modules/live_bad.py"
    assert report["quarantined_archive_files"] == [
        {
            "path": "projects/archive/logs/bad.log",
            "status": "historical-corrupt-archive",
            "exists": True,
        }
    ]


def test_survey_without_manifest_keeps_all_suspicious_files_active(tmp_path):
    archived = tmp_path / "projects" / "archive" / "logs" / "bad.log"
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text("archive ?? mojibake\n", encoding="utf-8")

    active = tmp_path / "modules" / "live_bad.py"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text("print('live ?? mojibake')\n", encoding="utf-8")

    report = survey(tmp_path, sample_limit=1)

    assert report["summary"]["archive_manifest_path"] == ""
    assert report["summary"]["quarantined_archive_file_count"] == 0
    assert report["summary"]["suspicious_file_count"] == 2
    assert sorted(row["path"] for row in report["suspicious_files"]) == [
        "modules/live_bad.py",
        "projects/archive/logs/bad.log",
    ]


def test_survey_quarantines_material_assets_from_active_baseline(tmp_path):
    quarantined_material = tmp_path / "test_material" / "json_outputs" / "bad-pack.json"
    quarantined_material.parent.mkdir(parents=True, exist_ok=True)
    quarantined_material.write_text('{"title":"?? material"}\n', encoding="utf-8")

    active = tmp_path / "modules" / "live_bad.py"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text("print('live ?? mojibake')\n", encoding="utf-8")

    ledger_path = tmp_path / "docs" / "2026-03-13" / "material-quarantine-ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "path": "test_material/json_outputs/bad-pack.json",
                        "status": "quarantined",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report = survey(tmp_path, sample_limit=1)

    assert report["summary"]["material_quarantine_ledger_path"] == "docs/2026-03-13/material-quarantine-ledger.json"
    assert report["summary"]["quarantined_material_file_count"] == 1
    assert report["summary"]["suspicious_file_count"] == 1
    assert report["suspicious_files"][0]["path"] == "modules/live_bad.py"
    assert report["quarantined_material_files"] == [
        {
            "path": "test_material/json_outputs/bad-pack.json",
            "status": "quarantined",
            "exists": True,
        }
    ]


def test_survey_ignores_generated_refresh_reports_from_active_baseline(tmp_path):
    generated_report = tmp_path / "docs" / "2026-03-14" / "mojibake-global-survey-refresh.json"
    generated_report.parent.mkdir(parents=True, exist_ok=True)
    generated_report.write_text('{"text":"live ' + ("?" * 2) + ' noise"}\n', encoding="utf-8")

    active = tmp_path / "modules" / "live_bad.py"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text("print('live ?? mojibake')\n", encoding="utf-8")

    report = survey(tmp_path, sample_limit=1)

    assert report["summary"]["suspicious_file_count"] == 1
    assert report["summary"]["excluded_generated_report_pattern"] == "mojibake-global-survey-*.json"
    assert report["suspicious_files"][0]["path"] == "modules/live_bad.py"
