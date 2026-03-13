from pathlib import Path


PRELOAD = Path("geuldobi-desktop/src/preload.js").read_text(encoding="utf-8")
MAIN_JS = Path("geuldobi-desktop/src/main.js").read_text(encoding="utf-8")


def test_preload_exposes_work_guard_template_methods():
    assert "listWorkGuardTemplates" in PRELOAD
    assert "applyWorkGuardTemplate" in PRELOAD
    assert 'project:list-work-guard-templates' in PRELOAD
    assert 'project:apply-work-guard-template' in PRELOAD


def test_main_process_registers_work_guard_template_handlers():
    assert 'ipcMain.handle("project:list-work-guard-templates"' in MAIN_JS
    assert 'ipcMain.handle("project:apply-work-guard-template"' in MAIN_JS
    assert "function getWorkGuardLibraryDir()" in MAIN_JS
    assert "function resolveWorkGuardTemplatePath(templatePath)" in MAIN_JS


def test_preload_runkey_accepts_approval_id_for_risk_keys():
    assert "runKey: (key, subKey, inputs, approvalId = null)" in PRELOAD
    assert 'ipcRenderer.invoke("bridge:run", { key, subKey, inputs, approvalId })' in PRELOAD


def test_main_process_forwards_approval_id_to_backend_run_request():
    assert 'ipcMain.handle("bridge:run", async (_, { key, subKey, inputs, approvalId })' in MAIN_JS
    assert 'body.approval_id = approvalId.trim();' in MAIN_JS
