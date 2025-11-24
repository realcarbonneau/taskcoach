#!/usr/bin/env python3
"""
Test using GTK geometry hints to set USER_POS before showing window.

According to GTK docs, setting Gdk.WindowHints.USER_POS tells the WM
that the position was user-specified and should be honored.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

TARGET_POS = (100, 100)
TARGET_SIZE = (200, 150)

class TestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="GTK Geometry Hints Test")

        self.move_count = 0

        # Set position BEFORE showing
        self.move(*TARGET_POS)
        self.set_default_size(*TARGET_SIZE)

        # Set geometry hints with USER_POS flag
        # This tells WM: "user specified this position, respect it"
        geometry = Gdk.Geometry()
        geometry.min_width = 50
        geometry.min_height = 50
        self.set_geometry_hints(None, geometry, Gdk.WindowHints.USER_POS | Gdk.WindowHints.USER_SIZE)

        print(f"Set geometry hints with USER_POS | USER_SIZE")

        # Create label
        self.label = Gtk.Label()
        self.add(self.label)

        # Connect signals
        self.connect("configure-event", self.on_configure)
        self.connect("realize", self.on_realize)
        self.connect("map", self.on_map)

        # Update timer
        GLib.timeout_add(100, self.update_label)

    def on_realize(self, widget):
        gdk_window = self.get_window()
        if gdk_window:
            pos = gdk_window.get_position()
            print(f"on_realize: position={pos}")

    def on_map(self, widget):
        pos = self.get_position()
        print(f"on_map: position={pos}")

    def on_configure(self, widget, event):
        self.move_count += 1
        print(f"configure-event #{self.move_count}: position=({event.x}, {event.y})")
        return False

    def update_label(self):
        pos = self.get_position()
        size = self.get_size()
        self.label.set_text(f"Position: {pos}\nSize: {size}\nMoves: {self.move_count}")
        return True


def main():
    print(f"Target position: {TARGET_POS}")
    print("Using Gdk.WindowHints.USER_POS to request WM honors position\n")

    win = TestWindow()
    win.connect("destroy", Gtk.main_quit)

    pos_before = win.get_position()
    print(f"Before show_all(): position={pos_before}")

    win.show_all()

    pos_after = win.get_position()
    print(f"After show_all(): position={pos_after}")

    print("\nStarting Gtk.main()...")
    Gtk.main()

if __name__ == "__main__":
    main()
