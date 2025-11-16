# -*- mode: python ; coding: utf-8 -*-
"""
TaskCoach PyInstaller Spec - NO BINARY SCANNING
This spec file SKIPS automatic DLL scanning to avoid the GitHub Actions hang

The hang occurs during "Looking for dynamic libraries" - by excluding
binaries from Analysis, we skip that step entirely.

We'll manually add required DLLs later if needed.
"""

import os

a = Analysis(
    ['taskcoach.pyw'],
    pathex=[],
    binaries=[],  # Empty - don't scan for binaries
    datas=[],
    hiddenimports=[
        # Minimal imports - let runtime handle the rest
        'wx',
        'twisted',
        'pubsub',
        'lxml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'test',
        'tests',
        'unittest',
    ],
    noarchive=False,
    optimize=0,
    # KEY: Don't scan for binaries automatically
    module_collection_mode={
        'wx': 'py',  # Only collect .py files, not binaries
        'numpy': 'py',
        'lxml': 'py',
    },
)

# IMPORTANT: Remove ALL binaries to skip DLL scanning
a.binaries = []

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
    upx=False,  # Disable UPX
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
    a.binaries,  # Will be empty
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='TaskCoach',
)
