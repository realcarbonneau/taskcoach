"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import wx
from taskcoachlib import operating_system


class _Tracker(object):
    """Utility methods for setting and getting values from/to the settings."""

    def __init__(self, settings, section):
        super().__init__()
        self.__settings = settings
        self.__section = section

    def set_setting(self, setting, value):
        self.__settings.setvalue(self.__section, setting, value)

    def get_setting(self, setting):
        return self.__settings.getvalue(self.__section, setting)


class WindowSizeAndPositionTracker(_Tracker):
    """Track the size and position of a window in the settings.

    DESIGN: This tracker defers position setting until explicitly called via
    apply_saved_position(). This allows the caller to set the position AFTER
    AUI LoadPerspective() completes (which would otherwise override the position).

    Usage:
        tracker = WindowDimensionsTracker(window, settings)
        # ... initialize AUI, load perspective ...
        tracker.apply_saved_position()  # Apply position after AUI init
    """

    def __init__(self, window, settings, section):
        super().__init__(settings, section)
        self._window = window

        # Load saved values but don't apply position yet (AUI will override)
        self._saved_x, self._saved_y = self.get_setting("position")
        self._saved_width, self._saved_height = self.get_setting("size")
        self._saved_maximized = self.get_setting("maximized")

        # Only set SIZE initially (position will be set later)
        self._apply_size_only()

    def _apply_size_only(self):
        """Apply only size, not position. Position applied later via apply_saved_position()."""
        width, height = self._saved_width, self._saved_height

        # Enforce minimum size
        min_width, min_height = (400, 300) if isinstance(self._window, wx.Dialog) else (600, 400)
        width = max(width, min_width)
        height = max(height, min_height)

        self._window.SetMinSize((min_width, min_height))
        self._window.SetSize(width, height)

        if operating_system.isMac():
            self._window.SetClientSize((width, height))

    def apply_saved_position(self):
        """Apply saved position. Call this AFTER AUI LoadPerspective() completes."""
        x, y = self._saved_x, self._saved_y
        width, height = self._saved_width, self._saved_height

        # Enforce minimum size
        min_width, min_height = (400, 300) if isinstance(self._window, wx.Dialog) else (600, 400)
        width = max(width, min_width)
        height = max(height, min_height)

        # Handle default position
        if x == -1 and y == -1:
            x, y = 50, 50

        print(f"[WindowTracker] Applying saved position: ({x}, {y}) size: ({width}, {height})")

        # Set position and size
        self._window.SetPosition(wx.Point(x, y))

        if self._saved_maximized:
            self._window.Maximize()

        # Validate window is visible
        self._validate_visibility()

        # Now bind event handlers for saving on close
        # (We DON'T save on every EVT_SIZE/EVT_MOVE - only on close)

    def _validate_visibility(self):
        """Ensure window is visible on some display."""
        display_index = wx.Display.GetFromWindow(self._window)
        if display_index == wx.NOT_FOUND:
            # Window is off-screen, move to safe position
            print("[WindowTracker] Window off-screen, moving to (50, 50)")
            self._window.SetPosition(wx.Point(50, 50))

    def save_position(self):
        """Save current window position and size. Called on close."""
        if self._window.IsIconized():
            self.set_setting("iconized", True)
            return

        self.set_setting("iconized", False)

        pos = self._window.GetPosition()
        size = self._window.GetSize()
        maximized = self._window.IsMaximized()

        print(f"[WindowTracker] Saving: pos=({pos.x}, {pos.y}) size=({size.width}, {size.height}) maximized={maximized}")

        if not maximized:
            self.set_setting("position", (pos.x, pos.y))
            self.set_setting("size", (size.width, size.height))

        self.set_setting("maximized", maximized)


class WindowDimensionsTracker(WindowSizeAndPositionTracker):
    """Track the dimensions of the main window."""

    def __init__(self, window, settings):
        super().__init__(window, settings, "window")
        self.__settings = settings

    def __start_iconized(self):
        """Determine if we should start iconized."""
        start_iconized_setting = self.get_setting("starticonized")
        if start_iconized_setting == "Always":
            return True
        elif start_iconized_setting == "Never":
            return False
        else:  # 'WhenClosedIconized'
            return self.get_setting("iconized")

    def apply_saved_position(self):
        """Apply saved position and handle iconized state."""
        # Check if we should start iconized
        if self.__start_iconized():
            if operating_system.isMac() or operating_system.isGTK():
                self._window.Show()
            self._window.Iconize(True)
            if not operating_system.isMac() and self.get_setting("hidewheniconized"):
                wx.CallAfter(self._window.Hide)
        else:
            # Apply saved position
            super().apply_saved_position()

    def save_position(self):
        """Save position and iconized state."""
        iconized = self._window.IsIconized()
        self.set_setting("iconized", iconized)

        if not iconized:
            super().save_position()
