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
    runtime_hooks=[],
    excludes=[
        'test',
        'tests',
        'unittest',
        # CRITICAL: Exclude ALL pywin32 to prevent runtime hooks from loading
        'win32com',
        'win32api',
        'win32con',
        'win32gui',
        'win32file',
        'win32event',
        'pywintypes',
        'pythoncom',
        'win32com.client',
        'win32com.shell',
        'wmi',
        # Also exclude these to prevent DLL scanning
        'comtypes',
        'numpy',  # numpy DLLs can also cause hangs
    ],
    # NOTE: optimize and module_collection_mode don't exist in PyInstaller 5.x
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
