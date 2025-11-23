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
import wx.lib.agw.persist as PM
import time
from taskcoachlib import operating_system

# Debug logging for window position tracking (set to False to disable)
_DEBUG_WINDOW_TRACKING = True


def _log_debug(msg):
    """Log debug message with timestamp."""
    if _DEBUG_WINDOW_TRACKING:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] WindowTracker: {msg}")


class WindowDimensionsTracker:
    """Track the dimensions of the main window using wx.lib.agw.persist.

    This uses wxPython's built-in PersistenceManager which handles all the
    edge cases for window geometry persistence automatically:
    - GTK positioning quirks
    - Multi-monitor support
    - Maximized/iconized state
    - AUI perspectives (if enabled)

    Note: On Wayland, window positioning is blocked by the compositor.
    This is a security feature and cannot be worked around.
    """

    def __init__(self, window, settings):
        self._window = window
        self._settings = settings
        self._persistence_manager = None

        # Check for Wayland
        wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland' or \
                  os.environ.get('WAYLAND_DISPLAY') is not None
        if wayland:
            _log_debug("Running on Wayland - window positioning may be limited")

        # Set minimum size
        self._window.SetMinSize((600, 400))

        # Initialize PersistenceManager
        self._setup_persistence()

        # Handle start iconized setting (Task Coach specific)
        if self._should_start_iconized():
            if operating_system.isMac() or operating_system.isGTK():
                self._window.Show()
            self._window.Iconize(True)
            if not operating_system.isMac() and settings.getvalue("window", "hidewheniconized"):
                wx.CallAfter(self._window.Hide)

    def _setup_persistence(self):
        """Set up the PersistenceManager for this window."""
        # Get persistence manager singleton
        self._persistence_manager = PM.PersistenceManager.Get()

        # Use Task Coach's data directory for persistence file
        data_dir = self._settings.pathToDataDir()
        persistence_file = os.path.join(data_dir, "window_geometry.ini")
        _log_debug(f"Persistence file: {persistence_file}")

        # Configure persistence manager
        self._persistence_manager.SetPersistenceFile(persistence_file)

        # IMPORTANT: Set unique name for the window
        self._window.SetName("TaskCoachMainWindow")

        # Register and restore window geometry
        _log_debug("Registering window with PersistenceManager")
        if not self._persistence_manager.RegisterAndRestore(self._window):
            _log_debug("No saved geometry found, using defaults")
            # Center on screen if no saved position
            self._window.Center()
        else:
            _log_debug(f"Restored geometry: pos={self._window.GetPosition()}, size={self._window.GetSize()}")

    def _should_start_iconized(self):
        """Return whether the window should be opened iconized."""
        start_iconized = self._settings.get("window", "starticonized")
        if start_iconized == "Always":
            return True
        if start_iconized == "Never":
            return False
        # Check saved iconized state
        return self._settings.getvalue("window", "iconized")

    def apply_position_after_show(self):
        """Re-apply position after Show() if needed.

        PersistenceManager should handle this automatically, but we provide
        this method for compatibility with existing code.
        """
        _log_debug(f"apply_position_after_show: pos={self._window.GetPosition()}, size={self._window.GetSize()}")

    def save_position(self):
        """Save the position of the window.

        Called when window is about to close.
        """
        iconized = self._window.IsIconized()
        maximized = self._window.IsMaximized()

        _log_debug(f"save_position: iconized={iconized} maximized={maximized}")
        _log_debug(f"  pos={self._window.GetPosition()}, size={self._window.GetSize()}")

        # Save Task Coach specific settings
        self._settings.setvalue("window", "iconized", iconized)

        # Let PersistenceManager save the geometry
        if self._persistence_manager:
            self._persistence_manager.SaveAndUnregister(self._window)
            _log_debug("Saved geometry via PersistenceManager")


# Keep the old class names for backward compatibility with dialogs
class _Tracker(object):
    """Utility methods for setting and getting values from/to the settings."""

    def __init__(self, settings, section):
        super().__init__()
        self._settings = settings
        self._section = section

    def set_setting(self, setting, value):
        """Store the value for the setting in the settings."""
        self._settings.setvalue(self._section, setting, value)

    def get_setting(self, setting):
        """Get the value for the setting from the settings and return it."""
        return self._settings.getvalue(self._section, setting)


class WindowSizeAndPositionTracker(_Tracker):
    """Track the size and position of a dialog window.

    For dialogs, we use a simpler approach since PersistenceManager
    is primarily designed for top-level frames.
    """

    def __init__(self, window, settings, section):
        super().__init__(settings, section)
        self._window = window
        self._is_maximized = False

        # Set minimum size for dialogs
        self._window.SetMinSize((400, 300))

        # Restore dimensions
        self._restore_dimensions()

        # Track maximize state
        self._window.Bind(wx.EVT_MAXIMIZE, self._on_maximize)

    def _on_maximize(self, event):
        """Track maximize state changes."""
        self._is_maximized = True
        event.Skip()

    def _restore_dimensions(self):
        """Restore window dimensions from settings."""
        x, y = self.get_setting("position")
        width, height = self.get_setting("size")

        _log_debug(f"Dialog restoring: pos=({x}, {y}) size=({width}, {height})")

        # Enforce minimum size
        width = max(width, 400)
        height = max(height, 300)
        if width <= 0 or height <= 0:
            width, height = 400, 300

        # Position relative to parent
        parent = self._window.GetParent()
        if parent and (x == -1 or y == -1):
            parent_rect = parent.GetScreenRect()
            x = parent_rect.x + (parent_rect.width - width) // 2
            y = parent_rect.y + (parent_rect.height - height) // 2

        self._window.SetSize(x, y, width, height)

        if self.get_setting("maximized"):
            self._window.Maximize()
            self._is_maximized = True

    def apply_position_after_show(self):
        """No-op for dialogs - position is set in _restore_dimensions."""
        pass

    def save_state(self):
        """Save the current window state."""
        maximized = self._window.IsMaximized() or self._is_maximized
        iconized = self._window.IsIconized()

        self.set_setting("maximized", maximized)

        if not maximized and not iconized:
            pos = self._window.GetPosition()
            size = (
                self._window.GetClientSize()
                if operating_system.isMac()
                else self._window.GetSize()
            )
            self.set_setting("position", pos)
            self.set_setting("size", size)
