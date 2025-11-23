#!/usr/bin/env python3
"""
Test accessing GDK from wxPython to set user position hint.

wxPython on GTK uses GDK underneath. We can access the GDK window
and call set_user_position() or use geometry hints.
"""

import wx
import time

TARGET_POS = (100, 100)

class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wx + GDK Position Test", size=(200, 150))

        self.move_count = 0
        self.position_applied = False
        self.last_move_time = time.time()

        panel = wx.Panel(self)
        self.label = wx.StaticText(panel, label="", pos=(10, 10))

        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_SHOW, self.on_show)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(100)

        self.update_position()

    def try_gdk_user_position(self):
        """Try to set GDK user position hint via PyGObject."""
        try:
            import gi
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk

            # Get the X11 window ID from wxPython
            handle = self.GetHandle()
            print(f"  wx handle (XID): {handle}")

            if handle:
                # Get the GDK display and find our window
                display = Gdk.Display.get_default()
                print(f"  GDK display: {display}")

                # Try to get GdkWindow from X11 window ID
                # This is tricky - GDK doesn't have a direct XID->GdkWindow lookup
                # We need to use the default screen's root window or foreign window

                # Method 1: Try gdk_x11_window_foreign_new_for_display (if available)
                try:
                    from gi.repository import GdkX11
                    gdk_window = GdkX11.X11Window.foreign_new_for_display(display, handle)
                    if gdk_window:
                        print(f"  Got GdkX11Window: {gdk_window}")
                        gdk_window.move(*TARGET_POS)
                        print(f"  Called move({TARGET_POS})")
                        return True
                except Exception as e:
                    print(f"  GdkX11 method failed: {e}")

                # Method 2: Just use wx SetPosition after we know window is mapped
                print("  Falling back to wx.SetPosition")
                self.SetPosition(wx.Point(*TARGET_POS))
                return True

        except ImportError as e:
            print(f"  PyGObject not available: {e}")
        except Exception as e:
            print(f"  GDK access failed: {e}")

        return False

    def update_position(self):
        pos = self.GetPosition()
        size = self.GetSize()
        self.label.SetLabel(f"Position: ({pos.x}, {pos.y})\nSize: ({size.width}, {size.height})\nMoves: {self.move_count}")

    def on_move(self, event):
        self.move_count += 1
        pos = event.GetPosition()
        self.last_move_time = time.time()
        print(f"EVT_MOVE #{self.move_count}: position=({pos.x}, {pos.y}) applied={self.position_applied}")

        if not self.position_applied:
            wx.CallLater(100, self._check_and_apply_position)

        self.update_position()
        event.Skip()

    def _check_and_apply_position(self):
        if self.position_applied:
            return

        elapsed = time.time() - self.last_move_time
        if elapsed < 0.1:
            wx.CallLater(100, self._check_and_apply_position)
            print(f"  -> Waiting for WM to settle (last move {elapsed*1000:.0f}ms ago)")
            return

        self.position_applied = True
        pos_before = self.GetPosition()
        print(f"  -> WM settled at ({pos_before.x}, {pos_before.y}) after {self.move_count} moves")
        print(f"  -> Trying GDK user position method...")

        success = self.try_gdk_user_position()
        if not success:
            print(f"  -> GDK failed, using wx.SetPosition({TARGET_POS})")
            self.SetPosition(wx.Point(*TARGET_POS))

        pos_after = self.GetPosition()
        print(f"  -> After position set: ({pos_after.x}, {pos_after.y})")

    def on_show(self, event):
        pos = self.GetPosition()
        print(f"EVT_SHOW: position=({pos.x}, {pos.y}) shown={event.IsShown()}")
        event.Skip()

    def on_timer(self, event):
        self.update_position()


def main():
    print("Creating wx.App...")
    app = wx.App()

    print(f"Creating TestFrame (target position={TARGET_POS})...")
    frame = TestFrame()

    pos_before = frame.GetPosition()
    print(f"Before Show(): position=({pos_before.x}, {pos_before.y})")

    print("Calling Show()...")
    frame.Show()

    pos_after = frame.GetPosition()
    print(f"After Show(): position=({pos_after.x}, {pos_after.y})")

    print("Starting MainLoop...")
    app.MainLoop()

if __name__ == "__main__":
    main()
