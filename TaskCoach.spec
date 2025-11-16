# -*- mode: python ; coding: utf-8 -*-

"""
TaskCoach PyInstaller spec file for Windows build
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all taskcoachlib packages
taskcoach_packages = collect_submodules('taskcoachlib')

# Additional hidden imports
hidden_imports = [
    'wx',
    'wx.lib',
    'wx.lib.agw',
    'wx.lib.agw.hypertreelist',
    'wx.lib.masked',
    'wx.lib.colourdb',
    'wx.lib.calendar',
    'wx.html',
    'wx.adv',
    'wx.grid',
    'wx.media',
    'wx.xml',
    'wx.xrc',
    'six',
    'desktop3',
    'pypubsub',
    'pubsub',
    'pubsub.core',
    'pubsub.core.topicmgr',
    'pubsub.core.topicdefnprovider',
    'twisted',
    'twisted.internet',
    'twisted.internet.reactor',
    'twisted.internet.selectreactor',
    'twisted.python',
    'chardet',
    'dateutil',
    'dateutil.parser',
    'pyparsing',
    'lxml',
    'lxml.etree',
    'lxml._elementpath',
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'numpy',
    'lockfile',
    'gntp',
    'distro',
    'WMI',
    'pythoncom',
    'pywintypes',
    'win32api',
    'win32com',
    'win32com.client',
    'win32com.shell',
] + taskcoach_packages

# Collect data files
datas = []

# Add i18n files
if os.path.exists('i18n.in'):
    for root, dirs, files in os.walk('i18n.in'):
        for file in files:
            if file.endswith('.po'):
                src = os.path.join(root, file)
                dst = 'i18n.in'
                datas.append((src, dst))

# Add templates
if os.path.exists('templates.in'):
    for root, dirs, files in os.walk('templates.in'):
        for file in files:
            if file.endswith('.tsktmpl') or file.endswith('.py'):
                src = os.path.join(root, file)
                dst = 'templates.in'
                datas.append((src, dst))

# Add icons
if os.path.exists('icons.in'):
    for root, dirs, files in os.walk('icons.in'):
        for file in files:
            if file.endswith(('.png', '.ico', '.icns', '.bmp', '.zip')):
                src = os.path.join(root, file)
                dst = 'icons.in'
                datas.append((src, dst))

# Add any other necessary data files
if os.path.exists('taskcoachlib/bin.in'):
    datas.append(('taskcoachlib/bin.in', 'taskcoachlib/bin.in'))

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
    name='TaskCoach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI application
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
    upx=True,
    upx_exclude=[],
    name='TaskCoach',
)
