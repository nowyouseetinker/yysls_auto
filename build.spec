# ruff: noqa
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for 游戏按键自动化工具.

Single-file EXE build, windowed mode (no console).
"""

from __future__ import annotations

# --- Analysis -----------------------------------------------------------
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pydirectinput',
        'keyboard',
        'json',
        'threading',
        'ctypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# --- PYZ (compiled pure-Python modules) ---------------------------------
pyz = PYZ(a.pure)

# --- EXE (single-file executable) ---------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='游戏按键自动化工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
