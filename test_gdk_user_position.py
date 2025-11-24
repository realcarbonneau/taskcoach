#!/usr/bin/env python3
"""
Test using gdk_window_set_user_position() to tell WM to honor position.

This sets the USPosition hint in X11, which tells the window manager
that the user explicitly specified this position and it should be honored.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import time

TARGET_POS = (100, 100)
TARGET_SIZE = (200, 150)

class TestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="GDK User Position Test")
        self.set_default_size(*TARGET_SIZE)

        self.move_count = 0
        self.position_applied = False

        # Create label to show position
        self.label = Gtk.Label()
        self.add(self.label)

        # Connect signals
        self.connect("configure-event", self.on_configure)
        self.connect("realize", self.on_realize)
        self.connect("show", self.on_show)

        # Update timer
        GLib.timeout_add(100, self.update_label)

    def on_realize(self, widget):
        """Called when window is realized (has a GDK window)."""
        gdk_window = self.get_window()
        pos = gdk_window.get_position() if gdk_window else (0, 0)
        print(f"on_realize: gdk_window={gdk_window} position={pos}")

        if gdk_window:
            # THIS IS THE KEY: Tell WM this is a user-specified position
            print(f"  -> Calling set_user_position({TARGET_POS})")
            gdk_window.move(*TARGET_POS)
            # Mark as user position - this sets USPosition hint
            # Note: In GTK3, move() after realize should set this automatically
            # But we can also try set_geometry_hints
            geometry = Gdk.Geometry()
            geometry.min_width = 100
            geometry.min_height = 100
            self.set_geometry_hints(None, geometry, Gdk.WindowHints.USER_POS)

            pos_after = gdk_window.get_position()
            print(f"  -> After move: position={pos_after}")

    def on_show(self, widget):
        pos = self.get_position()
        print(f"on_show: position={pos}")

    def on_configure(self, widget, event):
        self.move_count += 1
        print(f"configure-event #{self.move_count}: position=({event.x}, {event.y}) size=({event.width}, {event.height})")
        return False

    def update_label(self):
        pos = self.get_position()
        size = self.get_size()
        self.label.set_text(f"Position: {pos}\nSize: {size}\nMoves: {self.move_count}")
        return True  # Continue timer


def main():
    print("Creating GTK application...")
    print(f"Target position: {TARGET_POS}")

    win = TestWindow()
    win.connect("destroy", Gtk.main_quit)

    print("Before show()...")
    win.show_all()
    print("After show()...")

    pos = win.get_position()
    print(f"Position after show_all(): {pos}")

    print("Starting Gtk.main()...")
    Gtk.main()

if __name__ == "__main__":
    main()
