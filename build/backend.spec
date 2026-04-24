# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the packaged FastAPI bridge."""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

hiddenimports = [
    # google AI (google-genai SDK)
    "google.genai",
    "google.genai.types",
    "google.generativeai",
    "google.ai.generativelanguage",
    # uvicorn internals
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    # FastAPI / Starlette
    "fastapi",
    "fastapi.responses",
    "starlette.responses",
    "starlette.routing",
    "starlette.middleware",
    # websockets
    "websockets",
    "websockets.legacy",
    "websockets.legacy.server",
    # Project modules
    "modules.api",
    "modules.api.bridge_server",
    "modules.api.process_runner",
    "modules.api.run_validator",
    "modules.api.risk_approval",
    "modules.api.prompt_broker",
    "modules.api.prompt_classifier",
]

a = Analysis(
    ["backend_entry.py"],
    pathex=[PROJECT_ROOT],
    hiddenimports=hiddenimports,
    datas=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="backend",
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="backend",
)
