# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — onedir build for incremental updates."""
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parent.parent

datas = [
    (str(root / "assets"), "assets"),
    (str(root / "src" / "data"), "src/data"),
    (str(root / "VERSION"), "."),
]

hiddenimports = [
    "pygame",
    "pygame.ce",
]

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="pepelny-sad",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pepelny-sad",
)
