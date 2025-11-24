#!/usr/bin/env python3
"""
Set GTK USER_POS hint AFTER Show() but before MainLoop.

Maybe wxPython's Show() is overriding our hint. Try setting it after.
"""

import wx

TARGET = (100, 100)

def set_gtk_hints(wx_frame):
    """Set GTK geometry hints with USER_POS."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk

        for win in Gtk.Window.list_toplevels():
            title = win.get_title()
            if title and wx_frame.GetTitle() in title:
                print(f"Found GtkWindow: {win}")

                geometry = Gdk.Geometry()
                geometry.min_width = 1
                geometry.min_height = 1
                win.set_geometry_hints(None, geometry, Gdk.WindowHints.USER_POS)
                win.move(*TARGET)
                print(f"Set USER_POS + move({TARGET})")
                return True

        return False
    except Exception as e:
        print(f"GTK hint failed: {e}")
        return False


class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="GTK Hint After Show", size=(200, 150))
        self.move_count = 0
        self.Bind(wx.EVT_MOVE, self.on_move)

    def on_move(self, event):
        self.move_count += 1
        pos = event.GetPosition()
        print(f"EVT_MOVE #{self.move_count}: ({pos.x}, {pos.y})")
        event.Skip()


app = wx.App()
frame = TestFrame()

print(f"Before Show: {frame.GetPosition()}")
frame.Show()
print(f"After Show: {frame.GetPosition()}")

# Process pending events
app.Yield()
print(f"After Yield: {frame.GetPosition()}")

# NOW set GTK hint
print("\nSetting GTK hint AFTER Show+Yield...")
set_gtk_hints(frame)
print(f"After GTK hint: {frame.GetPosition()}")

app.MainLoop()
