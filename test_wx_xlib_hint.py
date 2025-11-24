#!/usr/bin/env python3
"""
Test using Xlib to set PPosition/USPosition hints directly on X11 window.

This sets the WM_NORMAL_HINTS property with USPosition flag before
the window manager processes the window.
"""

import wx
import time
import os

TARGET_POS = (100, 100)

def set_x11_position_hints(xid, x, y):
    """Set X11 WM_NORMAL_HINTS with USPosition flag."""
    try:
        from Xlib import X, display, Xatom
        from Xlib.protocol import rq

        # Connect to X display
        disp = display.Display(os.environ.get('DISPLAY', ':0'))
        print(f"  Connected to X display: {disp.get_display_name()}")

        # Get the window object
        window = disp.create_resource_object('window', xid)
        print(f"  Got X window: {window}")

        # Get current size hints
        try:
            hints = window.get_wm_normal_hints()
            print(f"  Current hints: {hints}")
        except:
            hints = None

        # Define the size hints structure
        # flags: bit 0 = USPosition (user specified position)
        #        bit 2 = PPosition (program specified position)
        USPosition = 1 << 0
        USSize = 1 << 1
        PPosition = 1 << 2
        PSize = 1 << 3

        # Set new hints with USPosition flag
        new_hints = {
            'flags': USPosition | PPosition,
            'min_width': 0,
            'min_height': 0,
            'max_width': 0,
            'max_height': 0,
            'width_inc': 0,
            'height_inc': 0,
            'min_aspect': (0, 0),
            'max_aspect': (0, 0),
            'base_width': 0,
            'base_height': 0,
            'win_gravity': 1,  # NorthWest
        }

        window.set_wm_normal_hints(new_hints)
        print(f"  Set WM_NORMAL_HINTS with USPosition flag")

        # Also move the window
        window.configure(x=x, y=y)
        print(f"  Configured window position to ({x}, {y})")

        disp.sync()
        print("  Synced with X server")

        return True

    except ImportError:
        print("  python-xlib not installed. Install with: pip install python-xlib")
        return False
    except Exception as e:
        print(f"  Xlib approach failed: {e}")
        import traceback
        traceback.print_exc()
        return False


class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wx + Xlib Hint Test", pos=TARGET_POS, size=(200, 150))

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

    # Create frame but don't show yet
    frame = TestFrame()

    # Show briefly to get the X window ID, then hide
    frame.Show()
    frame.Hide()

    xid = frame.GetHandle()
    print(f"\nX11 Window ID (XID): {xid}")

    # Set X11 hints BEFORE showing
    print("\nSetting X11 position hints via Xlib...")
    success = set_x11_position_hints(xid, *TARGET_POS)

    if success:
        print("\nHints set successfully!")
    else:
        print("\nHints setting failed, trying wx.SetPosition fallback...")
        frame.SetPosition(wx.Point(*TARGET_POS))

    # Now show for real
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
