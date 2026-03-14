import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "test_material" / "ingest_i_materials.py"
REINGEST_MODULE_PATH = Path(__file__).resolve().parents[1] / "test_material" / "reingest_json_outputs.py"


def load_ingest_module():
    spec = importlib.util.spec_from_file_location("ingest_i_materials", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reingest_module():
    spec = importlib.util.spec_from_file_location("reingest_json_outputs", REINGEST_MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_payload(path: Path, title: str) -> None:
    path.write_text(
        json.dumps(
            {
                "source": "I-TEST",
                "title": title,
                "row_count_by_table": {
                    "events": 0,
                    "npcs": 0,
                    "crises": 0,
                    "sector_chains": 0,
                    "market_data": 0,
                },
                "total_rows": 0,
                "events": [],
                "npcs": [],
                "crises": [],
                "sector_chains": [],
                "market_data": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_load_payloads_skips_quarantined_material_pack(tmp_path):
    module = load_ingest_module()
    good = tmp_path / "i-good.json"
    quarantined = tmp_path / "i-bad.json"
    write_payload(good, "good")
    write_payload(quarantined, "bad")

    ledger = tmp_path / "material-quarantine-ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "path": quarantined.resolve().as_posix(),
                        "status": "quarantined",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    quarantine_paths = module.load_quarantined_paths(ledger)
    payloads, skipped = module.load_payloads(tmp_path, "i-*.json", quarantine_paths)

    assert [path.name for path, _payload in payloads] == ["i-good.json"]
    assert [path.name for path in skipped] == ["i-bad.json"]


def test_load_payloads_without_quarantine_ledger_keeps_all_packs(tmp_path):
    module = load_ingest_module()
    write_payload(tmp_path / "i-good.json", "good")
    write_payload(tmp_path / "i-bad.json", "bad")

    payloads, skipped = module.load_payloads(tmp_path, "i-*.json")

    assert [path.name for path, _payload in payloads] == ["i-bad.json", "i-good.json"]
    assert skipped == []


def test_reingest_filter_quarantined_files_skips_known_corrupt_pack(tmp_path):
    module = load_reingest_module()
    good = tmp_path / "i-good.json"
    quarantined = tmp_path / "i-bad.json"
    write_payload(good, "good")
    write_payload(quarantined, "bad")

    ledger = tmp_path / "material-quarantine-ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "path": quarantined.resolve().as_posix(),
                        "status": "quarantined",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    quarantine_paths = module.load_quarantined_paths(ledger)
    kept, skipped = module.filter_quarantined_files(
        [good, quarantined],
        quarantine_paths,
    )

    assert [path.name for path in kept] == ["i-good.json"]
    assert [path.name for path in skipped] == ["i-bad.json"]
