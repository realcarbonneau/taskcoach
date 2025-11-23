#!/usr/bin/env python3
"""
Compare GTK events in pure GTK vs wxPython.

Log ALL GTK signals to see what wxPython does differently.
"""

import wx
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

TARGET = (100, 100)

def monitor_gtk_window(wx_frame):
    """Find and monitor the GtkWindow for all events."""
    for win in Gtk.Window.list_toplevels():
        title = win.get_title()
        if title and wx_frame.GetTitle() in title:
            print(f"Monitoring GtkWindow: {win}")

            # Connect to GTK signals
            win.connect("configure-event", lambda w, e: print(f"  GTK configure-event: ({e.x}, {e.y})") or False)
            win.connect("map", lambda w: print(f"  GTK map: {w.get_position()}"))
            win.connect("map-event", lambda w, e: print(f"  GTK map-event") or False)
            win.connect("show", lambda w: print(f"  GTK show"))
            win.connect("realize", lambda w: print(f"  GTK realize"))

            # Try to intercept position changes
            def on_notify(obj, pspec):
                if 'position' in pspec.name.lower() or 'allocation' in pspec.name.lower():
                    print(f"  GTK notify: {pspec.name}")
            win.connect("notify", on_notify)

            return win
    return None


class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="GTK Monitor Test", size=(200, 150))
        self.move_count = 0
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_SHOW, self.on_show)

    def on_move(self, event):
        self.move_count += 1
        pos = event.GetPosition()
        print(f"wx EVT_MOVE #{self.move_count}: ({pos.x}, {pos.y})")
        event.Skip()

    def on_size(self, event):
        size = event.GetSize()
        print(f"wx EVT_SIZE: ({size.width}, {size.height})")
        event.Skip()

    def on_show(self, event):
        print(f"wx EVT_SHOW: shown={event.IsShown()}")
        event.Skip()


print("Creating wx.App...")
app = wx.App()

print("\nCreating wx.Frame...")
frame = TestFrame()

print("\nMonitoring GTK window...")
gtk_win = monitor_gtk_window(frame)

if gtk_win:
    # Set USER_POS hint
    geometry = Gdk.Geometry()
    geometry.min_width = 1
    geometry.min_height = 1
    gtk_win.set_geometry_hints(None, geometry, Gdk.WindowHints.USER_POS)
    gtk_win.move(*TARGET)
    print(f"Set USER_POS + move({TARGET})")

print(f"\nBefore Show: {frame.GetPosition()}")
print("Calling Show()...")
frame.Show()
print(f"After Show: {frame.GetPosition()}")

print("\nStarting MainLoop...")
app.MainLoop()
