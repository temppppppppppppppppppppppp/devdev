import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_JS_PATH = ROOT / "geuldobi-desktop" / "src" / "main.js"
INDEX_HTML_PATH = ROOT / "geuldobi-desktop" / "src" / "index.html"
MAIN_JS = MAIN_JS_PATH.read_text(encoding="utf-8")
INDEX_HTML = INDEX_HTML_PATH.read_text(encoding="utf-8")


def _run_load_settings(settings_path: Path) -> dict:
    script = f"""
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(MAIN_JS_PATH))}, "utf8");
const start = source.indexOf("function buildDefaultDesktopSettings() {{");
const end = source.indexOf("function ensureFirstRunFlag() {{", start);
if (start < 0 || end < 0) {{
  throw new Error("settings recovery helpers not found");
}}
const helperSource = source.slice(start, end).trim();
const settingsPath = {json.dumps(str(settings_path))};
const captured = {{ error: [], warn: [] }};
const context = {{
  fs,
  path,
  SETTINGS_PATH: settingsPath,
  console: {{
    error: (...args) => captured.error.push(args.map((arg) => String(arg)).join(" ")),
    warn: (...args) => captured.warn.push(args.map((arg) => String(arg)).join(" ")),
  }},
}};
vm.runInNewContext(helperSource + "\\nthis.__result = loadDesktopSettingsFromDisk(SETTINGS_PATH);", context);
const persisted = fs.existsSync(settingsPath)
  ? JSON.parse(fs.readFileSync(settingsPath, "utf8"))
  : null;
process.stdout.write(JSON.stringify({{
  result: context.__result,
  persisted,
  logs: captured,
}}));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def test_main_process_restores_settings_from_valid_backup(tmp_path):
    settings_path = tmp_path / "settings.json"
    backup_path = tmp_path / "settings.json.bak"
    settings_path.write_text("{ broken", encoding="utf-8")
    backup_path.write_text(
        json.dumps(
            {
                "apiKey1": "live-key",
                "extraKeys": {"2": "backup-key"},
                "slackWebhook": "https://example.test/hook",
                "timeout": 120,
                "keyRotate": 7,
                "qualityGate": 88,
                "targetLength": 6100,
                "project": "alpha",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = _run_load_settings(settings_path)

    assert payload["result"]["recovery"]["status"] == "backup_restored"
    assert payload["result"]["apiKey1"] == "live-key"
    assert payload["result"]["project"] == "alpha"
    assert payload["persisted"]["apiKey1"] == "live-key"
    assert payload["persisted"]["extraKeys"] == {"2": "backup-key"}
    assert "recovery" not in payload["persisted"]


def test_main_process_factory_resets_when_primary_and_backup_are_both_corrupt(tmp_path):
    settings_path = tmp_path / "settings.json"
    backup_path = tmp_path / "settings.json.bak"
    settings_path.write_text("{ broken", encoding="utf-8")
    backup_path.write_text("{ backup broken", encoding="utf-8")

    payload = _run_load_settings(settings_path)

    assert payload["result"]["recovery"]["status"] == "factory_reset"
    assert payload["result"]["recovery"]["backupPath"] == str(backup_path)
    assert payload["persisted"] == {
        "apiKey1": "",
        "extraKeys": {},
        "slackWebhook": "",
        "timeout": 300,
        "keyRotate": 10,
        "qualityGate": 90,
        "targetLength": 5000,
        "project": "",
    }
    assert "recovery" not in payload["persisted"]


def test_renderer_announces_settings_recovery_states():
    assert 'recovery?.status === "factory_reset"' in INDEX_HTML
    assert 'setCurrentFocus("설정 초기화됨", "손상된 설정 파일을 기본값으로 복구했습니다. 필요시 API 키를 다시 입력하세요.");' in INDEX_HTML
    assert 'appendLog("[설정] 설정 파일 손상 감지 — 기본값으로 초기화되었습니다.");' in INDEX_HTML
    assert 'appendLog("[설정] 설정 파일 손상 감지 — .bak 백업에서 복구했습니다.");' in INDEX_HTML
