# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Task Coach Linux build
This creates a standalone Linux executable with all dependencies bundled.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all taskcoachlib submodules
taskcoach_hiddenimports = collect_submodules('taskcoachlib')

# Additional hidden imports that PyInstaller might miss
hidden_imports = [
    'twisted.internet.reactor',
    'twisted.internet.selectreactor',
    'wx',
    'wx.lib.masked',
    'wx.lib.pubsub',
    'pypubsub',
    'six',
    'desktop3',
    'chardet',
    'dateutil',
    'pyparsing',
    'lxml',
    'pyxdg',
    'keyring',
    'numpy',
    'lockfile',
    'gntp',
    'taskcoachlib.workarounds.monkeypatches',
] + taskcoach_hiddenimports

# Collect data files from taskcoachlib
datas = []

# Add i18n translations
if os.path.exists('taskcoachlib/i18n'):
    datas.append(('taskcoachlib/i18n', 'taskcoachlib/i18n'))

# Add templates
if os.path.exists('templates.in'):
    for template_file in os.listdir('templates.in'):
        if template_file.endswith('.tsktmpl'):
            datas.append((f'templates.in/{template_file}', 'templates.in'))

# Add icons
if os.path.exists('icons.in'):
    for icon_file in ['taskcoach.png', 'taskcoach.ico', 'splash.png']:
        icon_path = f'icons.in/{icon_file}'
        if os.path.exists(icon_path):
            datas.append((icon_path, 'icons.in'))

# Add help files if they exist
if os.path.exists('taskcoachlib/help'):
    datas.append(('taskcoachlib/help', 'taskcoachlib/help'))

# Add thirdparty modules
if os.path.exists('taskcoachlib/thirdparty'):
    datas.append(('taskcoachlib/thirdparty', 'taskcoachlib/thirdparty'))

a = Analysis(
    ['taskcoach.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
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
    name='taskcoach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons.in/taskcoach.png' if os.path.exists('icons.in/taskcoach.png') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='taskcoach',
)
