#!/usr/bin/env python3
"""
Test setting wx internal position + GTK hint together.

wxGTK's Show() calls gtk_window_move(m_x, m_y) which overrides GTK hints.
We need BOTH: wx internal position AND GTK USER_POS hint.
"""

import wx
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

TARGET = (100, 100)

class TestFrame(wx.Frame):
    def __init__(self):
        # Set position in constructor to set internal m_x, m_y
        super().__init__(None, title="Internal Pos + GTK Hint",
                        pos=TARGET, size=(200, 150))
        self.move_count = 0
        self.Bind(wx.EVT_MOVE, self.on_move)

    def on_move(self, event):
        self.move_count += 1
        pos = event.GetPosition()
        print(f"EVT_MOVE #{self.move_count}: ({pos.x}, {pos.y})")
        event.Skip()


print("Creating wx.App...")
app = wx.App()

print(f"\nCreating wx.Frame with pos={TARGET} in constructor...")
frame = TestFrame()

# Also set via SetPosition to ensure internal values are set
frame.SetPosition(TARGET)
print(f"After SetPosition: {frame.GetPosition()}")

# Now set GTK hint on top of wx internal position
print("\nSetting GTK USER_POS hint...")
for win in Gtk.Window.list_toplevels():
    title = win.get_title()
    if title and frame.GetTitle() in title:
        geometry = Gdk.Geometry()
        geometry.min_width = 1
        geometry.min_height = 1
        win.set_geometry_hints(None, geometry, Gdk.WindowHints.USER_POS)
        win.move(*TARGET)
        print(f"Set GTK USER_POS + move({TARGET})")
        break

print(f"\nBefore Show: {frame.GetPosition()}")
frame.Show()
print(f"After Show: {frame.GetPosition()}")

app.MainLoop()
