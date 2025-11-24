#!/usr/bin/env python3
"""
Minimal wxPython window position test.
Tests if GTK honors SetPosition/SetSize for a simple window.

Key finding: Window managers ignore initial positions and use "Smart Placement".
Position must be set AFTER window is mapped to trigger GDK_HINT_USER_POS.

Usage:
  python3 test_window_position.py           # Normal mode with MainLoop
  python3 test_window_position.py --no-loop # Test WITHOUT MainLoop (uses Yield)
"""

import wx
import sys
import time

TARGET_POS = (100, 100)

class TestFrame(wx.Frame):
    def __init__(self):
        # Create frame - DON'T set position here (WM will ignore it)
        super().__init__(None, title="Position Test", size=(200, 150))

        self.move_count = 0
        self.position_applied = False
        self.last_move_time = time.time()

        # Add a panel with position info
        panel = wx.Panel(self)
        self.label = wx.StaticText(panel, label="", pos=(10, 10))

        # Update position display
        self.update_position()

        # Bind move event to track position changes
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_SHOW, self.on_show)

        # Timer to continuously update position
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(100)  # Update every 100ms

    def update_position(self):
        pos = self.GetPosition()
        size = self.GetSize()
        self.label.SetLabel(f"Position: ({pos.x}, {pos.y})\nSize: ({size.width}, {size.height})\nMoves: {self.move_count}")

    def on_move(self, event):
        self.move_count += 1
        pos = event.GetPosition()
        self.last_move_time = time.time()
        print(f"EVT_MOVE #{self.move_count}: position=({pos.x}, {pos.y}) applied={self.position_applied}")

        # Don't apply immediately - wait for WM to finish all its moves
        # Schedule a delayed check instead (debounce)
        if not self.position_applied:
            wx.CallLater(100, self._check_and_apply_position)

        self.update_position()
        event.Skip()

    def _check_and_apply_position(self):
        """Apply position only after WM has stopped moving the window (debounce)."""
        if self.position_applied:
            return

        # If a move happened in the last 100ms, wait more
        elapsed = time.time() - self.last_move_time
        if elapsed < 0.1:
            wx.CallLater(100, self._check_and_apply_position)
            print(f"  -> Waiting for WM to settle (last move {elapsed*1000:.0f}ms ago)")
            return

        self.position_applied = True
        pos_before = self.GetPosition()
        print(f"  -> WM settled at ({pos_before.x}, {pos_before.y}) after {self.move_count} moves")
        print(f"  -> Applying target position {TARGET_POS}...")
        self.SetPosition(wx.Point(*TARGET_POS))
        pos_after = self.GetPosition()
        print(f"  -> After SetPosition: ({pos_after.x}, {pos_after.y})")

    def on_show(self, event):
        pos = self.GetPosition()
        print(f"EVT_SHOW: position=({pos.x}, {pos.y}) shown={event.IsShown()}")
        event.Skip()

    def on_timer(self, event):
        self.update_position()


def test_without_mainloop(app, frame):
    """Test position behavior WITHOUT entering MainLoop.
    Uses Yield() to process pending events manually."""
    print("\n=== Testing WITHOUT MainLoop ===")
    print("Using wx.Yield() to process events manually...")

    for i in range(20):  # 2 seconds of yielding
        time.sleep(0.1)
        app.Yield()  # Process pending events
        pos = frame.GetPosition()
        print(f"[{i*0.1:.1f}s] After Yield(): position=({pos.x}, {pos.y}) moves={frame.move_count}")

    print("\n=== End test (no MainLoop was ever started) ===")
    print(f"Final position: {frame.GetPosition()}")
    print(f"Total moves: {frame.move_count}")


def main():
    no_loop = '--no-loop' in sys.argv

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

    if no_loop:
        test_without_mainloop(app, frame)
    else:
        print("Starting MainLoop... (WM will move window, then we apply position)")
        app.MainLoop()

if __name__ == "__main__":
    main()
