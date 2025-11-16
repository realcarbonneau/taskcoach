# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect icon data files
icon_path = os.path.join(os.getcwd(), 'taskcoachlib', 'gui', 'icons')
icon_datas = []
if os.path.exists(icon_path):
    for root, dirs, files in os.walk(icon_path):
        for file in files:
            if file.endswith(('.png', '.ico', '.xpm', '.bmp')):
                src = os.path.join(root, file)
                dst = os.path.relpath(root, os.getcwd())
                icon_datas.append((src, dst))

# Collect help files
help_path = os.path.join(os.getcwd(), 'taskcoachlib', 'help')
help_datas = []
if os.path.exists(help_path):
    for root, dirs, files in os.walk(help_path):
        for file in files:
            src = os.path.join(root, file)
            dst = os.path.relpath(root, os.getcwd())
            help_datas.append((src, dst))

# Collect all data files
datas = icon_datas + help_datas

# Hidden imports - manually specified to avoid import issues during build
hiddenimports = [
    # wxPython core modules
    'wx',
    'wx._core',
    'wx._adv',
    'wx._html',
    'wx._grid',
    'wx._aui',
    'wx._dataview',
    'wx._xml',
    'wx._xrc',
    'wx.lib',
    'wx.lib.agw',
    'wx.lib.agw.hypertreelist',
    'wx.lib.agw.customtreectrl',
    'wx.lib.masked',
    'wx.lib.calendar',
    'wx.lib.mixins',
    'wx.lib.mixins.listctrl',
    'wx.lib.pubsub',
    'wx.html',
    'wx.grid',
    'wx.aui',
    # TaskCoach dependencies
    'pubsub',
    'pubsub.core',
    'pubsub.pub',
    'desktop3',
    'pyparsing',
    'twisted',
    'twisted.internet',
    'twisted.internet.protocol',
    'twisted.internet.defer',
    'chardet',
    'dateutil',
    'dateutil.parser',
    'dateutil.tz',
    'lxml',
    'lxml.etree',
    'pyxdg',
    'keyring',
    'keyring.backends',
    'numpy',
    'lockfile',
    'gntp',
    'distro',
    'six',
    'six.moves',
    # Required for Twisted/Zope
    'pkg_resources',
    'setuptools',
    'zope',
    'zope.interface',
    # TaskCoach modules
    'taskcoachlib',
    'taskcoachlib.workarounds',
    'taskcoachlib.workarounds.monkeypatches',
    'taskcoachlib.application',
    'taskcoachlib.config',
    'taskcoachlib.domain',
    'taskcoachlib.gui',
    'taskcoachlib.persistence',
    'taskcoachlib.i18n',
    'taskcoachlib.meta',
    'taskcoachlib.thirdparty',
]

a = Analysis(
    ['taskcoach.py'],
    pathex=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='taskcoach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
