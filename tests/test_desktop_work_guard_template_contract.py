from pathlib import Path


PRELOAD = Path("geuldobi-desktop/src/preload.js").read_text(encoding="utf-8")
MAIN_JS = Path("geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
CONTROL_PLANE_JS = Path("geuldobi-desktop/src/desktop_control_plane_contract.js").read_text(encoding="utf-8")


def test_preload_exposes_work_guard_template_methods():
    assert "listWorkGuardTemplates" in PRELOAD
    assert "applyWorkGuardTemplate" in PRELOAD
    assert 'project:list-work-guard-templates' in CONTROL_PLANE_JS
    assert 'project:apply-work-guard-template' in CONTROL_PLANE_JS


def test_main_process_registers_work_guard_template_handlers():
    assert "ipcMain.handle(IPC_CHANNELS.project.listWorkGuardTemplates" in MAIN_JS
    assert "ipcMain.handle(IPC_CHANNELS.project.applyWorkGuardTemplate" in MAIN_JS
    assert "function getWorkGuardLibraryDir()" in MAIN_JS
    assert "function resolveWorkGuardTemplatePath(templatePath)" in MAIN_JS


def test_preload_runkey_accepts_approval_id_for_risk_keys():
    assert "runKey: (key, subKey, inputs, approvalId = null)" in PRELOAD
    assert "ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.runKey, { key, subKey, inputs, approvalId })" in PRELOAD
    assert 'run: "bridge:run"' in CONTROL_PLANE_JS


def test_main_process_forwards_approval_id_to_backend_run_request():
    assert "ipcMain.handle(IPC_CHANNELS.bridge.run, async (_, { key, subKey, inputs, approvalId })" in MAIN_JS
    assert 'body.approval_id = approvalId.trim();' in MAIN_JS
