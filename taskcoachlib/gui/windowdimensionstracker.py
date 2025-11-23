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

import os
import wx
import time
from taskcoachlib import operating_system

# Debug logging for window position tracking (set to False to disable)
_DEBUG_WINDOW_TRACKING = True


def _log_debug(msg):
    """Log debug message with timestamp."""
    if _DEBUG_WINDOW_TRACKING:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] WindowTracker: {msg}")


class _Tracker:
    """Utility methods for setting and getting values from/to the settings."""

    def __init__(self, settings, section):
        self._settings = settings
        self._section = section

    def set_setting(self, setting, value):
        """Store the value for the setting in the settings."""
        self._settings.setvalue(self._section, setting, value)

    def get_setting(self, setting):
        """Get the value for the setting from the settings and return it."""
        return self._settings.getvalue(self._section, setting)


class WindowSizeAndPositionTracker(_Tracker):
    """Track the size and position of a window in the settings.

    Best practices followed:
    1. Save only on close (not on every EVT_MOVE/EVT_SIZE)
    2. Apply position after Show() for GTK compatibility
    3. Use Task Coach's existing settings system

    Note: On Wayland, window positioning is blocked by the compositor.
    This is a security feature and cannot be worked around.
    """

    def __init__(self, window, settings, section):
        super().__init__(settings, section)
        self._window = window
        self._is_maximized = False

        # Check for Wayland
        self._on_wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland' or \
                          os.environ.get('WAYLAND_DISPLAY') is not None
        if self._on_wayland:
            _log_debug("Running on Wayland - window positioning may be limited")

        # Set minimum size
        if isinstance(self._window, wx.Dialog):
            self._window.SetMinSize((400, 300))
        else:
            self._window.SetMinSize((600, 400))

        # Restore dimensions from settings
        self._restore_dimensions()

        # Track maximize state (needed because IsMaximized() can be unreliable at close)
        self._window.Bind(wx.EVT_MAXIMIZE, self._on_maximize)

    def _on_maximize(self, event):
        """Track maximize state changes."""
        self._is_maximized = True
        _log_debug("Window maximized")
        event.Skip()

    def _restore_dimensions(self):
        """Restore window dimensions from settings."""
        x, y = self.get_setting("position")
        width, height = self.get_setting("size")
        maximized = self.get_setting("maximized")

        _log_debug(f"RESTORE: pos=({x}, {y}) size=({width}, {height}) maximized={maximized}")

        # Enforce minimum size
        min_w, min_h = self._window.GetMinSize()
        width = max(width, min_w) if width > 0 else min_w
        height = max(height, min_h) if height > 0 else min_h

        # Handle position
        if x == -1 and y == -1:
            # No saved position - center on primary monitor
            _log_debug("  No saved position, centering")
            self._window.SetSize(width, height)
            self._window.Center()
        else:
            # Use saved position
            self._window.SetSize(x, y, width, height)

        if operating_system.isMac():
            self._window.SetClientSize((width, height))

        # Validate position is on screen
        self._validate_position()

        # Handle maximized state
        if maximized:
            self._window.Maximize()
            self._is_maximized = True

        pos = self._window.GetPosition()
        size = self._window.GetSize()
        _log_debug(f"  Applied: pos=({pos.x}, {pos.y}) size=({size.width}, {size.height})")

    def _validate_position(self):
        """Ensure window is visible on a display."""
        display_index = wx.Display.GetFromWindow(self._window)

        if display_index == wx.NOT_FOUND:
            _log_debug("  Window off-screen, centering")
            self._window.Center()
            return

        # Check if at least 50px is visible
        display = wx.Display(display_index)
        display_rect = display.GetGeometry()
        window_rect = self._window.GetRect()

        visible_left = max(window_rect.x, display_rect.x)
        visible_right = min(window_rect.x + window_rect.width,
                           display_rect.x + display_rect.width)
        visible_top = max(window_rect.y, display_rect.y)
        visible_bottom = min(window_rect.y + window_rect.height,
                            display_rect.y + display_rect.height)

        if (visible_right - visible_left) < 50 or (visible_bottom - visible_top) < 50:
            _log_debug("  Window barely visible, centering on display")
            self._window.Center()

    def apply_position_after_show(self):
        """Re-apply position after Show() for GTK.

        GTK may ignore SetSize() position before Show(). This re-applies
        the saved position after the window is visible.
        """
        x, y = self.get_setting("position")
        maximized = self.get_setting("maximized")

        if maximized or x == -1 or y == -1:
            return  # Nothing to re-apply

        current = self._window.GetPosition()
        _log_debug(f"apply_position_after_show: current=({current.x}, {current.y}) target=({x}, {y})")

        # Only re-apply if significantly different
        if abs(current.x - x) > 20 or abs(current.y - y) > 20:
            _log_debug(f"  Re-applying position ({x}, {y})")
            self._window.SetPosition(wx.Point(x, y))

            final = self._window.GetPosition()
            if abs(final.x - x) > 50 or abs(final.y - y) > 50:
                _log_debug(f"  WARNING: Position not applied (final={final.x}, {final.y})")
                if self._on_wayland:
                    _log_debug("  (Expected on Wayland - positioning blocked by compositor)")

    def save_state(self):
        """Save the current window state. Call when window is about to close."""
        maximized = self._window.IsMaximized() or self._is_maximized
        iconized = self._window.IsIconized()

        _log_debug(f"SAVE: maximized={maximized} iconized={iconized}")

        self.set_setting("maximized", maximized)

        if not iconized:
            pos = self._window.GetPosition()
            _log_debug(f"  position=({pos.x}, {pos.y})")
            self.set_setting("position", (pos.x, pos.y))

            if not maximized:
                size = (self._window.GetClientSize() if operating_system.isMac()
                        else self._window.GetSize())
                _log_debug(f"  size=({size.width}, {size.height})")
                self.set_setting("size", (size.width, size.height))

            # Save monitor index for multi-monitor support
            monitor = wx.Display.GetFromWindow(self._window)
            if monitor != wx.NOT_FOUND:
                self.set_setting("monitor_index", monitor)


class WindowDimensionsTracker(WindowSizeAndPositionTracker):
    """Track the dimensions of the main window in the settings."""

    def __init__(self, window, settings):
        super().__init__(window, settings, "window")

        # Handle start iconized setting (Task Coach specific)
        if self._should_start_iconized():
            if operating_system.isMac() or operating_system.isGTK():
                self._window.Show()
            self._window.Iconize(True)
            if not operating_system.isMac() and self.get_setting("hidewheniconized"):
                wx.CallAfter(self._window.Hide)

    def _should_start_iconized(self):
        """Return whether the window should be opened iconized."""
        start_iconized = self._settings.get("window", "starticonized")
        if start_iconized == "Always":
            return True
        if start_iconized == "Never":
            return False
        return self.get_setting("iconized")

    def save_position(self):
        """Save the position of the window in the settings.

        Called when window is about to close.
        """
        # Save iconized state (Task Coach specific)
        self.set_setting("iconized", self._window.IsIconized())

        # Save position/size/maximized via parent
        self.save_state()
