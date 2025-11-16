# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Task Coach - MINIMAL/FAST version
# This version SKIPS automatic DLL scanning to avoid the infinite hang

import os
import sys
from pathlib import Path

block_cipher = None

# Collect all taskcoachlib packages
taskcoach_packages = []
for root, dirs, files in os.walk('taskcoachlib'):
    if '__pycache__' not in root:
        package_path = root.replace(os.sep, '.')
        taskcoach_packages.append(package_path)

# Hidden imports
hiddenimports = [
    'taskcoachlib.i18n',
    'taskcoachlib.thirdparty._weakrefset',
    'wx',
    'wx._core',
    'wx._html',
    'wx._adv',
    'wx._aui',
    'wx._calendar',
    'wx._grid',
    'wx._stc',
    'wx.lib',
    'wx.lib.agw',
    'wx.lib.masked',
    'twisted',
    'pubsub',
    'pubsub.core',
] + taskcoach_packages

# Data files
datas = []
if os.path.exists('icons.in'):
    datas.append(('icons.in', 'icons.in'))
if os.path.exists('taskcoachlib/i18n'):
    datas.append(('taskcoachlib/i18n', 'taskcoachlib/i18n'))
if os.path.exists('taskcoachlib/help'):
    datas.append(('taskcoachlib/help', 'taskcoachlib/help'))
if os.path.exists('templates.in'):
    datas.append(('templates.in', 'templates.in'))

a = Analysis(
    ['taskcoach.py'],
    pathex=[],
    binaries=[],  # Empty - we'll let PyInstaller collect them but won't scan dependencies
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={
        # Disable binary dependency analysis - THIS IS THE KEY FIX
        'gi': {'module-versions': {}},
    },
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'PIL', 'PyQt5', 'PyQt6', 'tkinter',
        'IPython', 'jupyter', 'notebook', 'pandas', 'scipy', 'sklearn',
        'pytest', 'test', 'tests', '_pytest', 'unittest2', 'nose',
        'sphinx', 'docutils', 'setuptools._distutils', 'distutils',
        'antigravity', 'argparse', 'calendar', 'optparse', 'pdb',
        'pickletools', 'plistlib', 'pydoc', 'pydoc_data',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    # THE NUCLEAR OPTION - Skip DLL dependency analysis
    # This prevents the infinite hang at "Looking for dynamic libraries"
    # Trade-off: May miss some DLLs, but we can add them manually if needed
)

# Remove duplicate binaries (speed optimization)
a.binaries = list({x[0]: x for x in a.binaries}.values())

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TaskCoach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX disabled - causes hangs
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='TaskCoach',
)
