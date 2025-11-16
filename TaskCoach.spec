# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Task Coach

import os
import sys
from pathlib import Path

# Get the application metadata
block_cipher = None

# Collect all taskcoachlib packages
taskcoach_packages = []
for root, dirs, files in os.walk('taskcoachlib'):
    if '__pycache__' not in root:
        package_path = root.replace(os.sep, '.')
        taskcoach_packages.append(package_path)

# Hidden imports that PyInstaller might miss
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

# Data files to include
datas = []

# Include icons
if os.path.exists('icons.in'):
    datas.append(('icons.in', 'icons.in'))

# Include i18n translations
if os.path.exists('taskcoachlib/i18n'):
    datas.append(('taskcoachlib/i18n', 'taskcoachlib/i18n'))

# Include help files
if os.path.exists('taskcoachlib/help'):
    datas.append(('taskcoachlib/help', 'taskcoachlib/help'))

# Include templates
if os.path.exists('templates.in'):
    datas.append(('templates.in', 'templates.in'))

a = Analysis(
    ['taskcoach.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Large packages we don't need
        'matplotlib',
        'PIL',
        'PyQt5',
        'PyQt6',
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'pandas',
        'scipy',
        'sklearn',
        'pytest',
        'test',
        'tests',
        '_pytest',
        # Testing frameworks
        'unittest2',
        'nose',
        # Documentation tools
        'sphinx',
        'docutils',
        # Build tools
        'setuptools._distutils',
        'distutils',
    ],
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
    name='TaskCoach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disabled UPX - it can cause hangs and slow builds
    console=False,  # GUI application, no console window
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
    upx=False,  # Disabled UPX - it can cause hangs and slow builds
    upx_exclude=[],
    name='TaskCoach',
)
