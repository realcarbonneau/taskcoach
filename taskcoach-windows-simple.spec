# -*- mode: python ; coding: utf-8 -*-
"""
SIMPLIFIED TaskCoach PyInstaller Spec - Minimal Configuration
Use this if the full spec hangs during build

Usage:
    pyinstaller taskcoach-windows-simple.spec
"""

import os

# Minimal hidden imports - only what's absolutely necessary
hiddenimports = [
    # Core wxPython (let PyInstaller auto-detect the rest)
    'wx',

    # Core dependencies
    'twisted',
    'pubsub',
    'lxml',

    # Windows-specific (only if on Windows)
    'win32api',
    'win32con',
    'win32gui',
    'win32com',
    'pywintypes',
]

a = Analysis(
    ['taskcoach.pyw'],
    pathex=[],
    binaries=[],
    datas=[],  # Let PyInstaller auto-detect data files
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules to reduce scan time
        'unittest',
        'pytest',
        'nose',
        'test',
        'tests',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TaskCoach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to speed up build
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons.in/taskcoach.ico' if os.path.exists('icons.in/taskcoach.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX
    upx_exclude=[],
    name='TaskCoach',
)
