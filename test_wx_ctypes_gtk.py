#!/usr/bin/env python3
"""
Test using ctypes to directly call GTK functions on wxPython window.

This bypasses PyGObject and calls libgtk-3 directly.
"""

import wx
import ctypes
import time

TARGET_POS = (100, 100)

# Load GTK library
try:
    libgtk = ctypes.CDLL("libgtk-3.so.0")
    libgdk = ctypes.CDLL("libgdk-3.so.0")
    print("Loaded libgtk-3.so.0 and libgdk-3.so.0")
except OSError as e:
    print(f"Failed to load GTK libraries: {e}")
    libgtk = None
    libgdk = None


def get_gtk_widget_from_wx(wx_window):
    """Get the underlying GtkWidget pointer from a wx window."""
    # wxPython on GTK stores the widget pointer
    # We can try to access it via the internal _gtk_window attribute
    # or by using the GetHandle() which gives us the X11 window ID

    # Method 1: Try to get GTK widget via internal attribute
    try:
        if hasattr(wx_window, '_gtk_window'):
            return wx_window._gtk_window
    except:
        pass

    # Method 2: The widget pointer might be accessible differently
    # For now, we'll need to find another way
    return None


def set_gtk_user_pos_via_ctypes(xid, x, y):
    """Try to set USER_POS hint via ctypes."""
    if not libgtk:
        print("  GTK library not loaded")
        return False

    try:
        # We need to find the GtkWidget from the XID
        # This is tricky because GTK doesn't have a direct XID->GtkWidget lookup
        #
        # One approach: iterate through all toplevels via gtk_window_list_toplevels()

        # gtk_window_list_toplevels returns a GList*
        libgtk.gtk_window_list_toplevels.restype = ctypes.c_void_p
        toplevels = libgtk.gtk_window_list_toplevels()

        if toplevels:
            print(f"  Got toplevels list: {toplevels}")
            # This would require more complex GList iteration...
            # For now, let's try a simpler approach

        return False

    except Exception as e:
        print(f"  ctypes approach failed: {e}")
        return False


class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wx + ctypes GTK Test", pos=TARGET_POS, size=(200, 150))

        self.move_count = 0

        panel = wx.Panel(self)
        self.label = wx.StaticText(panel, label="", pos=(10, 10))

        self.Bind(wx.EVT_MOVE, self.on_move)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda e: self.update_label())
        self.timer.Start(100)

        self.update_label()

    def update_label(self):
        pos = self.GetPosition()
        self.label.SetLabel(f"Pos: ({pos.x}, {pos.y})\nMoves: {self.move_count}")

    def on_move(self, event):
        self.move_count += 1
        pos = event.GetPosition()
        print(f"EVT_MOVE #{self.move_count}: ({pos.x}, {pos.y})")
        self.update_label()
        event.Skip()


def main():
    print(f"Target position: {TARGET_POS}")
    print("="*50)

    app = wx.App()
    frame = TestFrame()

    # Get the X11 window ID
    xid = frame.GetHandle()
    print(f"X11 Window ID (XID): {xid}")

    # Try to set position hint via ctypes
    print("\nAttempting ctypes GTK approach...")
    set_gtk_user_pos_via_ctypes(xid, *TARGET_POS)

    print(f"\nShowing window...")
    frame.Show()

    pos = frame.GetPosition()
    print(f"After Show: ({pos.x}, {pos.y})")

    # Wait and observe
    for i in range(5):
        app.Yield()
        time.sleep(0.1)

    pos = frame.GetPosition()
    print(f"After settling: ({pos.x}, {pos.y})")
    print(f"Total moves: {frame.move_count}")

    print("\nStarting MainLoop...")
    app.MainLoop()

if __name__ == "__main__":
    main()
