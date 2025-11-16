# -*- mode: python ; coding: utf-8 -*-
"""
TaskCoach PyInstaller Spec File for Windows
Modern replacement for py2exe

Usage:
    pyinstaller taskcoach-windows.spec

This will create:
    dist/TaskCoach/TaskCoach.exe (windowed, no console)
    dist/TaskCoach/_internal/* (dependencies)
"""

import os
import sys

# Collect data files
def collect_data_files():
    """Collect icons, translations, templates, etc."""
    datas = []

    # Icons
    if os.path.exists('taskcoachlib/gui/icons.py'):
        datas.append(('taskcoachlib/gui/icons.py', 'taskcoachlib/gui'))

    # Translations (i18n)
    if os.path.exists('taskcoachlib/i18n'):
        for item in os.listdir('taskcoachlib/i18n'):
            if item.endswith('.py') and len(item) in [5, 6, 8]:  # xx.py, xxx.py, xx_XX.py
                datas.append((f'taskcoachlib/i18n/{item}', 'taskcoachlib/i18n'))

    # Templates
    if os.path.exists('taskcoachlib/persistence/xml/templates.py'):
        datas.append(('taskcoachlib/persistence/xml/templates.py',
                     'taskcoachlib/persistence/xml'))

    return datas

# Hidden imports (modules imported dynamically)
hiddenimports = [
    # wxPython submodules
    'wx',
    'wx.lib',
    'wx.lib.agw',
    'wx.lib.agw.aui',
    'wx.lib.agw.piectrl',
    'wx.lib.agw.hypertreelist',
    'wx.adv',
    'wx.grid',
    'wx.html',

    # i18n modules (imported dynamically by language code)
    'taskcoachlib.i18n',

    # Windows-specific (comment out for Linux builds)
    'win32api',
    'win32con',
    'win32gui',
    'win32file',
    'win32event',
    'win32com',
    'win32com.client',
    'win32com.shell',
    'pywintypes',
    'wmi',

    # Core dependencies
    'twisted',
    'twisted.internet',
    'twisted.python',
    'pubsub',
    'pubsub.core',
    'lxml',
    'numpy',
    'chardet',
    'keyring',
    'lockfile',
    'gntp',
    'dateutil',

    # Optional but commonly used
    'igraph',
]

# Binaries to exclude (reduce size)
excludes = [
    # Test modules
    'unittest',
    'pytest',
    'nose',

    # Unused GUI frameworks
    'PyQt4',
    'PyQt5',
    'PyKDE4',
    'tkinter',

    # Development tools
    'IPython',
    'matplotlib',
    'pandas',
]

a = Analysis(
    ['taskcoach.pyw'],  # Use .pyw on Windows for windowed app
    pathex=[],
    binaries=[],
    datas=collect_data_files(),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    upx=True,  # Compress with UPX
    console=False,  # Windowed app (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons.in/taskcoach.ico',  # Windows icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TaskCoach',
)
