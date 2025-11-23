#!/usr/bin/env python3
"""
Minimal wxPython window position test.
Tests if GTK honors SetPosition/SetSize for a simple window.

Key finding: Window managers ignore initial positions and use "Smart Placement".
Position must be set AFTER window is mapped to trigger GDK_HINT_USER_POS.
"""

import wx

TARGET_POS = (100, 100)

class TestFrame(wx.Frame):
    def __init__(self):
        # Create frame - DON'T set position here (WM will ignore it)
        super().__init__(None, title="Position Test", size=(200, 150))

        self.move_count = 0
        self.position_applied = False

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
        print(f"EVT_MOVE #{self.move_count}: position=({pos.x}, {pos.y}) applied={self.position_applied}")

        # If WM moved us and we haven't applied our position yet, apply it now
        if not self.position_applied:
            self.position_applied = True
            print(f"  -> Applying target position {TARGET_POS} via SetPosition...")
            self.SetPosition(wx.Point(*TARGET_POS))
            new_pos = self.GetPosition()
            print(f"  -> After SetPosition: ({new_pos.x}, {new_pos.y})")

        self.update_position()
        event.Skip()

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

    print("Starting MainLoop... (WM will move window, then we apply position)")
    app.MainLoop()

if __name__ == "__main__":
    main()
