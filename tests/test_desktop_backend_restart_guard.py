import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_JS_PATH = ROOT / "geuldobi-desktop" / "src" / "main.js"
MAIN_JS = MAIN_JS_PATH.read_text(encoding="utf-8")


def _run_restart_limit_dialog(response_index: int, *, include_splash: bool) -> dict:
    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(MAIN_JS_PATH))}, "utf8");
const start = source.indexOf("let backendRestartCount = 0;");
const end = source.indexOf("function startBackend() {{", start);
if (start < 0 || end < 0) {{
  throw new Error("backend restart guard helpers not found");
}}
const helperSource = source.slice(start, end).trim();
const dialogCalls = [];
const logs = {{ debug: [], error: [], log: [] }};
const splashWindow = {{"name": "splash", "isDestroyed": () => false}};
const mainWindow = {{"name": "main", "isDestroyed": () => false}};
const context = {{
  splashWindow: {str(include_splash).lower()} ? splashWindow : null,
  mainWindow,
  dialog: {{
    showMessageBox: async (...args) => {{
      dialogCalls.push(args);
      return {{ response: {response_index} }};
    }},
  }},
  app: {{
    isQuitting: false,
    quitCalls: 0,
    quit() {{
      this.quitCalls += 1;
      this.isQuitting = true;
    }},
  }},
  backendProcess: null,
  console: {{
    error: (...args) => logs.error.push(args.map((arg) => String(arg)).join(" ")),
    log: (...args) => logs.log.push(args.map((arg) => String(arg)).join(" ")),
    warn() {{}},
  }},
  debugLog: (...args) =>
    logs.debug.push(
      args
        .map((arg) => (typeof arg === "string" ? arg : JSON.stringify(arg)))
        .join(" ")
    ),
}};
let startBackendCalls = 0;
context.startBackend = () => {{
  startBackendCalls += 1;
}};
vm.runInNewContext(
  helperSource +
    "\\nthis.__setCount = (value) => {{ backendRestartCount = value; }};" +
    "\\nthis.__getCount = () => backendRestartCount;" +
    "\\nthis.__run = handleBackendRestartLimitReached;",
  context
);
context.__setCount(2);
Promise.resolve(context.__run({{ code: 1, signal: null, attemptCount: 2 }})).then(() => {{
  const dialogArgs = dialogCalls[0];
  const owner = dialogArgs.length === 2 ? dialogArgs[0]?.name || null : null;
  const options = dialogArgs.length === 2 ? dialogArgs[1] : dialogArgs[0];
  process.stdout.write(
    JSON.stringify({{
      owner,
      options,
      logs,
      startBackendCalls,
      backendRestartCount: context.__getCount(),
      quitCalls: context.app.quitCalls,
      isQuitting: context.app.isQuitting,
    }})
  );
}});
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def test_backend_restart_limit_dialog_contract_is_wired_in_main_process():
    assert 'buttons: ["재시작 시도", "종료"]' in MAIN_JS
    assert 'title: "백엔드 연결 실패"' in MAIN_JS
    assert 'message: "백엔드가 반복적으로 종료되었습니다."' in MAIN_JS
    assert "void handleBackendRestartLimitReached({" in MAIN_JS
    assert 'console.error("[backend] max restarts reached, prompting user");' in MAIN_JS


def test_backend_restart_limit_retry_path_restarts_backend_from_dialog():
    payload = _run_restart_limit_dialog(0, include_splash=True)

    assert payload["owner"] == "splash"
    assert payload["options"]["buttons"] == ["재시작 시도", "종료"]
    assert payload["options"]["defaultId"] == 0
    assert payload["backendRestartCount"] == 0
    assert payload["startBackendCalls"] == 1
    assert payload["quitCalls"] == 0
    assert payload["isQuitting"] is False
    assert any("backend restart limit reached" in entry for entry in payload["logs"]["debug"])


def test_backend_restart_limit_quit_path_exits_app_when_user_declines_restart():
    payload = _run_restart_limit_dialog(1, include_splash=False)

    assert payload["owner"] == "main"
    assert "3회 연속" in payload["options"]["detail"]
    assert payload["backendRestartCount"] == 2
    assert payload["startBackendCalls"] == 0
    assert payload["quitCalls"] == 1
    assert payload["isQuitting"] is True
