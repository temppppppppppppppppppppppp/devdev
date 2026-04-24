"""PyInstaller entry point for the packaged FastAPI bridge."""

import os
import sys

PACKAGED_RUNTIME_MODEL = "source_bundle_primary"

if getattr(sys, "frozen", False):
    backend_dir = os.path.dirname(sys.executable)
    resources_dir = os.path.dirname(backend_dir)
    engine_root = os.path.join(resources_dir, "engine")
    python_path = os.path.join(resources_dir, "python-embed", "python.exe")
    workspace_root = os.environ.get("GEULDOBI_WORKSPACE") or os.getcwd()

    os.environ["GEULDOBI_ENGINE_ROOT"] = engine_root
    os.environ["GEULDOBI_PYTHON_PATH"] = python_path
    os.environ.setdefault("GEULDOBI_PACKAGED_RUNTIME_MODEL", PACKAGED_RUNTIME_MODEL)
    os.environ.setdefault("GEULDOBI_PROJECTS_ROOT", os.path.join(workspace_root, "projects"))

    # The packaged backend imports the live engine source bundle directly.
    for candidate in (engine_root, backend_dir):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)

import uvicorn  # noqa: E402

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        from modules.api.bridge_server import app  # noqa: E402

        uvicorn.run(app, host="127.0.0.1", port=8300, log_level="info")
    else:
        uvicorn.run(
            "modules.api.bridge_server:app",
            host="127.0.0.1",
            port=8300,
            log_level="info",
        )
