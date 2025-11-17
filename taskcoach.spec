# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Task Coach
This creates a standalone Linux executable bundle
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all taskcoachlib modules
taskcoach_modules = collect_submodules('taskcoachlib')

# Collect data files (icons, help files, translations, etc.)
datas = []
datas += collect_data_files('taskcoachlib', include_py_files=True)

# Add specific data directories
if os.path.exists('taskcoachlib/help'):
    datas += [('taskcoachlib/help', 'taskcoachlib/help')]
if os.path.exists('taskcoachlib/i18n'):
    datas += [('taskcoachlib/i18n', 'taskcoachlib/i18n')]
if os.path.exists('icons.in'):
    datas += [('icons.in', 'icons.in')]

# Hidden imports that PyInstaller might miss
hiddenimports = taskcoach_modules + [
    'wx',
    'wx.lib',
    'wx.lib.agw',
    'wx.lib.agw.hypertreelist',
    'wx.lib.mixins',
    'wx.lib.mixins.listctrl',
    'twisted.internet.reactor',
    'twisted.internet.selectreactor',
    'twisted.python',
    'pypubsub',
    'six',
    'lxml',
    'lxml.etree',
    'chardet',
    'dateutil',
    'pyparsing',
    'numpy',
    'keyring',
    'keyring.backends',
    'secretstorage',
    'jeepney',
]

# Binaries - let PyInstaller auto-discover
binaries = []

a = Analysis(
    ['taskcoach.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PyQt5', 'PyQt6'],
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
    console=False,  # GUI application, no console
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
