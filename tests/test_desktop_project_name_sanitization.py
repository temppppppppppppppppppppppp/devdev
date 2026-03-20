import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_JS_PATH = ROOT / "geuldobi-desktop" / "src" / "main.js"
MAIN_JS = MAIN_JS_PATH.read_text(encoding="utf-8")


def _run_sanitize_project_name(value: str) -> str:
    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(MAIN_JS_PATH))}, "utf8");
const start = source.indexOf("function sanitizeProjectName(name) {{");
const end = source.indexOf("function getProjectRoot(projectName) {{", start);
if (start < 0 || end < 0) {{
  throw new Error("sanitizeProjectName definition not found");
}}
const fnSource = source.slice(start, end).trim();
const context = {{ __input: {json.dumps(value)} }};
vm.runInNewContext(fnSource + "\\nthis.__result = sanitizeProjectName(__input);", context);
process.stdout.write(JSON.stringify(context.__result));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def test_main_process_project_name_sanitizer_uses_whitelist_and_dot_guard():
    assert "/^\\.+$/.test(normalized)" in MAIN_JS
    assert 'replace(/[^a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ_\\- ]/g, "_")' in MAIN_JS


def test_sanitize_project_name_blocks_dot_sequences():
    assert _run_sanitize_project_name("..") == ""
    assert _run_sanitize_project_name("...") == ""


def test_sanitize_project_name_preserves_safe_names():
    assert _run_sanitize_project_name("정상") == "정상"
    assert _run_sanitize_project_name("test_project") == "test_project"


def test_sanitize_project_name_rewrites_path_traversal_tokens():
    assert _run_sanitize_project_name("../../etc") == "______etc"
    assert _run_sanitize_project_name('bad<>:"/\\|?*name') == "bad_________name"
