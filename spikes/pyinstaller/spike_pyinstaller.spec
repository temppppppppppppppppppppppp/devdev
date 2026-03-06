# -*- mode: python ; coding: utf-8 -*-
"""스파이크 1 PyInstaller spec.

sqlite-vec의 vec0.dll(Windows) / vec0.so(Linux) C 확장을
one-file exe에 포함하기 위해 binaries에 명시한다.

빌드 방법:
    cd spikes/pyinstaller
    pyinstaller spike_pyinstaller.spec

결과물: dist/spike_pyinstaller.exe
"""

import os
import sys

import sqlite_vec as _sv

_SQLITE_VEC_DIR = os.path.dirname(_sv.__file__)

# Windows: vec0.dll, Linux/macOS: vec0.so
_EXT = ".dll" if sys.platform == "win32" else ".so"
_VEC0_PATH = os.path.join(_SQLITE_VEC_DIR, f"vec0{_EXT}")

if not os.path.exists(_VEC0_PATH):
    raise FileNotFoundError(
        f"sqlite-vec 바이너리를 찾을 수 없습니다: {_VEC0_PATH}\n"
        f"sqlite_vec 패키지 경로: {_SQLITE_VEC_DIR}"
    )

block_cipher = None

a = Analysis(
    ["spike_pyinstaller.py"],
    pathex=[],
    # sqlite_vec C 확장을 번들의 sqlite_vec/ 하위에 배치
    binaries=[(_VEC0_PATH, "sqlite_vec")],
    # sqlite_vec __init__.py 등 Python 파일은 hiddenimports로 커버
    datas=[],
    hiddenimports=["sqlite_vec"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="spike_pyinstaller",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX 압축 비활성화 — 확장 DLL 손상 방지
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,        # stdout 출력 보이도록 console 모드
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
