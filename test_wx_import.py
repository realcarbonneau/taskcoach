#!/usr/bin/env python3
"""Test which hypertreelist file is being imported."""

import sys
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path[:3]}")

try:
    import wx
    print(f"wx imported from: {wx.__file__}")
    print(f"wx version: {wx.version()}")

    import wx.lib.agw.hypertreelist as ht
    print(f"hypertreelist imported from: {ht.__file__}")

    # Check if our patch is present
    # Note: PaintItem is overridden in TreeListMainWindow, not in CustomTreeCtrl
    import inspect
    source = inspect.getsource(ht.TreeListMainWindow.PaintItem)

    if "Draw full row background BEFORE column loop to avoid clipping issues" in source:
        print("\n✓ PATCH IS PRESENT in loaded file!")
    else:
        print("\n✗ PATCH IS NOT PRESENT in loaded file!")

    if "TR_FILL_WHOLE_COLUMN_BACKGROUND" in source and "full row background was already drawn before column loop" in source:
        print("✓ Column loop skip logic is present!")
    else:
        print("✗ Column loop skip logic is missing!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
