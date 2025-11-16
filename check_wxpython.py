#!/usr/bin/env python3
"""
Script to verify wxPython installation and availability for PyInstaller.
Run this before attempting to build with PyInstaller.
"""
import sys
import os

def check_python_info():
    print("=" * 70)
    print("Python Environment Information")
    print("=" * 70)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python prefix: {sys.prefix}")
    print()

def check_wx_import():
    print("=" * 70)
    print("wxPython Import Test")
    print("=" * 70)
    try:
        import wx
        print(f"✓ wxPython imported successfully")
        print(f"  Version: {wx.__version__}")
        print(f"  Location: {wx.__file__}")
        return True
    except ImportError as e:
        print(f"✗ FAILED to import wxPython: {e}")
        return False

def check_wx_modules():
    print()
    print("=" * 70)
    print("wxPython Sub-modules Check")
    print("=" * 70)

    modules = [
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
        'wx.lib.masked',
    ]

    all_ok = True
    for mod in modules:
        try:
            __import__(mod)
            print(f"✓ {mod}")
        except ImportError as e:
            print(f"✗ {mod}: {e}")
            all_ok = False

    return all_ok

def check_other_deps():
    print()
    print("=" * 70)
    print("Other Dependencies Check")
    print("=" * 70)

    deps = [
        'pypubsub',
        'pubsub',
        'desktop3',
        'twisted',
        'chardet',
        'dateutil',
        'pyparsing',
        'lxml',
        'pyxdg',
        'keyring',
        'numpy',
        'lockfile',
        'gntp',
        'distro',
    ]

    for dep in deps:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} (missing)")

def main():
    check_python_info()

    wx_ok = check_wx_import()
    if not wx_ok:
        print()
        print("=" * 70)
        print("ERROR: wxPython is not available!")
        print("=" * 70)
        print("Please install wxPython:")
        print("  sudo apt-get install python3-wxgtk4.0")
        print()
        print("Or verify you're using the correct Python:")
        print(f"  Current: {sys.executable}")
        print(f"  Should be: /usr/bin/python3")
        sys.exit(1)

    modules_ok = check_wx_modules()

    check_other_deps()

    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    if wx_ok and modules_ok:
        print("✓ All wxPython checks passed!")
        print("  Ready to build with PyInstaller")
        sys.exit(0)
    else:
        print("✗ Some checks failed")
        print("  Fix the issues above before building")
        sys.exit(1)

if __name__ == '__main__':
    main()
