#!/usr/bin/env python3
"""
Apply the working GTK approach to wxPython.

The GTK tests worked by setting USER_POS hint + move() BEFORE show.
Do the same for wxPython's underlying GTK window.
"""

import wx
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

TARGET = (100, 100)

app = wx.App()
frame = wx.Frame(None, title="wx like GTK", size=(200, 150))

# Find our GTK window in the list of toplevels
for win in Gtk.Window.list_toplevels():
    if win.get_title() == "wx like GTK":
        print(f"Found GtkWindow: {win}")

        # Do exactly what the working GTK tests did:
        geometry = Gdk.Geometry()
        geometry.min_width = 1
        geometry.min_height = 1
        win.set_geometry_hints(None, geometry, Gdk.WindowHints.USER_POS)
        win.move(*TARGET)

        print(f"Set USER_POS hint and moved to {TARGET}")
        break

frame.Show()
app.MainLoop()
