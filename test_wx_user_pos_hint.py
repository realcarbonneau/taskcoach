#!/usr/bin/env python3
"""
Test setting GDK_HINT_USER_POS on wxPython window BEFORE Show().

The key insight: wxWidgets calls gtk_window_move() but doesn't set
GDK_HINT_USER_POS explicitly. We need to set this hint before Show().
"""

import wx
import time

TARGET_POS = (100, 100)

def set_gtk_position_hint(wx_frame, x, y):
    """Set GTK position hint BEFORE showing the window."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk

        # Get the GTK widget pointer from wx
        # wxPython stores the GTK widget handle
        handle = wx_frame.GetHandle()

        if handle:
            # The handle is the X11 window ID, but we need the GtkWidget
            # Unfortunately, there's no direct way to get GtkWidget from XID
            #
            # Alternative approach: Use ctypes to call GTK functions directly
            # on the underlying GtkWindow
            print(f"  XID: {handle}")

            # We can try to access via GObject introspection
            # But wx doesn't expose the GtkWidget pointer directly

            # Let's try a different approach - find our window in GTK's list
            # This is hacky but might work
            for toplevel in Gtk.Window.list_toplevels():
                gdk_window = toplevel.get_window()
                if gdk_window:
                    # Compare XIDs
                    try:
                        from gi.repository import GdkX11
                        xid = GdkX11.X11Window.get_xid(gdk_window)
                        if xid == handle:
                            print(f"  Found matching GtkWindow: {toplevel}")
                            # Set geometry hints with USER_POS
                            geometry = Gdk.Geometry()
                            geometry.min_width = 1
                            geometry.min_height = 1
                            toplevel.set_geometry_hints(None, geometry, Gdk.WindowHints.USER_POS)
                            toplevel.move(x, y)
                            print(f"  Set USER_POS hint and moved to ({x}, {y})")
                            return True
                    except Exception as e:
                        print(f"  XID comparison failed: {e}")

            print("  Could not find matching GtkWindow")
            return False

    except Exception as e:
        print(f"  GTK hint setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


class TestFrame(wx.Frame):
    def __init__(self):
        # Set position in constructor - wx will call gtk_window_move
        super().__init__(None, title="wx + USER_POS Test", pos=TARGET_POS, size=(200, 150))

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

    pos1 = frame.GetPosition()
    print(f"After create: ({pos1.x}, {pos1.y})")

    # Try to set GTK hint BEFORE Show
    print("\nAttempting to set GTK USER_POS hint...")
    # Force window creation without showing
    frame.Show()
    frame.Hide()

    # Now try to set the hint
    set_gtk_position_hint(frame, *TARGET_POS)

    # Re-set position and show
    frame.SetPosition(wx.Point(*TARGET_POS))
    print(f"\nShowing window...")
    frame.Show()

    pos2 = frame.GetPosition()
    print(f"After Show: ({pos2.x}, {pos2.y})")

    # Wait a moment
    for i in range(5):
        app.Yield()
        time.sleep(0.1)

    pos3 = frame.GetPosition()
    print(f"After settling: ({pos3.x}, {pos3.y})")
    print(f"Total moves: {frame.move_count}")

    print("\nStarting MainLoop...")
    app.MainLoop()

if __name__ == "__main__":
    main()
