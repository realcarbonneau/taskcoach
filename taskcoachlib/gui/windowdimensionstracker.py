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


class TaskCoachConfigHandler:
    """Custom config handler that stores persistence data in Task Coach settings.

    This adapter allows wx.lib.agw.persist.PersistenceManager to use Task Coach's
    existing settings system instead of a separate file.

    The handler stores window geometry data in the [window] section of TaskCoach.ini
    using keys prefixed with 'persist_' to avoid conflicts with existing settings.
    """

    def __init__(self, settings):
        self._settings = settings
        self._section = "window"

    def SaveValue(self, key, value):
        """Save a value to Task Coach settings."""
        persist_key = f"persist_{key}"
        _log_debug(f"ConfigHandler.SaveValue: {persist_key} = {value}")
        self._settings.setvalue(self._section, persist_key, value)

    def RestoreValue(self, key):
        """Restore a value from Task Coach settings."""
        persist_key = f"persist_{key}"
        try:
            value = self._settings.getvalue(self._section, persist_key)
            _log_debug(f"ConfigHandler.RestoreValue: {persist_key} = {value}")
            return value
        except Exception:
            _log_debug(f"ConfigHandler.RestoreValue: {persist_key} not found")
            return None


class WindowDimensionsTracker:
    """Track the dimensions of the main window using wx.lib.agw.persist.PersistenceManager.

    This is the standard wxPython approach for window geometry persistence.
    PersistenceManager handles:
    - Cross-platform window geometry save/restore
    - Maximized/iconized state

    We add:
    - Custom config handler to use Task Coach's settings (not a separate file)
    - Multi-monitor support (track monitor index, handle config changes)
    - Post-Show() position re-application for GTK/X11 compatibility
    - Task Coach specific settings (iconized, starticonized)

    Platform notes:
    - X11: Full positioning support, but requires re-apply after Show()
    - Wayland: Positioning blocked by compositor (security feature)
    - Windows/macOS: Full support
    """

    def __init__(self, window, settings):
        self._window = window
        self._settings = settings
        self._persistence_manager = None
        self._config_handler = None

        # Check for Wayland
        self._on_wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland' or \
                          os.environ.get('WAYLAND_DISPLAY') is not None
        if self._on_wayland:
            _log_debug("Running on Wayland - window positioning blocked by compositor")

        # Set minimum size
        self._window.SetMinSize((600, 400))

        # Initialize PersistenceManager with Task Coach settings
        self._setup_persistence()

        # Handle start iconized setting (Task Coach specific)
        if self._should_start_iconized():
            if operating_system.isMac() or operating_system.isGTK():
                self._window.Show()
            self._window.Iconize(True)
            if not operating_system.isMac() and self._settings.getvalue("window", "hidewheniconized"):
                wx.CallAfter(self._window.Hide)

    def _setup_persistence(self):
        """Set up PersistenceManager with Task Coach's settings as backend."""
        # Create custom config handler that uses Task Coach settings
        self._config_handler = TaskCoachConfigHandler(self._settings)

        # Get persistence manager singleton
        self._persistence_manager = PM.PersistenceManager.Get()

        # Use our custom config handler (stores in TaskCoach.ini, not separate file)
        self._persistence_manager.SetConfigurationHandler(self._config_handler)

        # Set unique name for the window (required by PersistenceManager)
        self._window.SetName("TaskCoachMainWindow")

        # Register and restore window geometry
        _log_debug("Registering window with PersistenceManager")
        restored = self._persistence_manager.RegisterAndRestore(self._window)

        if not restored:
            _log_debug("No saved geometry found, centering window")
            self._window.Center()
        else:
            pos = self._window.GetPosition()
            size = self._window.GetSize()
            _log_debug(f"PersistenceManager restored: pos=({pos.x}, {pos.y}) size=({size.width}, {size.height})")

            # Validate and adjust for multi-monitor changes
            self._validate_monitor_position()

    def _validate_monitor_position(self):
        """Validate window is on a valid monitor, adjust if needed.

        Handles cases where:
        - Saved monitor no longer exists
        - Monitor configuration changed
        - Window would be off-screen
        """
        # Get saved monitor index (Task Coach specific, not from PersistenceManager)
        saved_monitor = self._settings.getvalue("window", "monitor_index")
        num_monitors = wx.Display.GetCount()

        _log_debug(f"Validating monitor: saved={saved_monitor}, available={num_monitors}")

        # Check if window is currently on a valid display
        current_display = wx.Display.GetFromWindow(self._window)

        if current_display == wx.NOT_FOUND:
            # Window is off-screen - move to saved monitor or primary
            _log_debug("  Window is off-screen")
            if saved_monitor is not None and 0 <= saved_monitor < num_monitors:
                target_display = wx.Display(saved_monitor)
            else:
                target_display = wx.Display(0)

            rect = target_display.GetGeometry()
            size = self._window.GetSize()
            x = rect.x + (rect.width - size.width) // 2
            y = rect.y + (rect.height - size.height) // 2
            _log_debug(f"  Moving to display {target_display}: ({x}, {y})")
            self._window.SetPosition(wx.Point(x, y))

        elif saved_monitor is not None and saved_monitor != current_display:
            # Window restored to different monitor than saved
            if 0 <= saved_monitor < num_monitors:
                _log_debug(f"  Window on monitor {current_display}, should be on {saved_monitor}")
                # Try to move to saved monitor (may not work on Wayland)
                target_display = wx.Display(saved_monitor)
                rect = target_display.GetGeometry()
                pos = self._window.GetPosition()
                size = self._window.GetSize()

                # Calculate position on target monitor (preserve relative position)
                current_rect = wx.Display(current_display).GetGeometry()
                rel_x = pos.x - current_rect.x
                rel_y = pos.y - current_rect.y
                new_x = rect.x + rel_x
                new_y = rect.y + rel_y

                # Ensure window fits on target monitor
                new_x = max(rect.x, min(new_x, rect.x + rect.width - size.width))
                new_y = max(rect.y, min(new_y, rect.y + rect.height - size.height))

                _log_debug(f"  Moving to saved monitor: ({new_x}, {new_y})")
                self._window.SetPosition(wx.Point(new_x, new_y))
            else:
                _log_debug(f"  Saved monitor {saved_monitor} no longer exists, keeping current")

    def _should_start_iconized(self):
        """Return whether the window should be opened iconized."""
        start_iconized = self._settings.get("window", "starticonized")
        if start_iconized == "Always":
            return True
        if start_iconized == "Never":
            return False
        return self._settings.getvalue("window", "iconized")

    def apply_position_after_show(self):
        """Re-apply position after Show() for GTK/X11 compatibility.

        On GTK/X11, SetPosition() before Show() may be ignored due to
        asynchronous window operations. This re-applies the saved position
        after the window is visible.

        On Wayland, this will have no effect (positioning blocked by compositor).
        """
        # Get the saved position from our config handler
        x = self._config_handler.RestoreValue("TaskCoachMainWindow/x")
        y = self._config_handler.RestoreValue("TaskCoachMainWindow/y")

        if x is None or y is None:
            _log_debug("apply_position_after_show: No saved position")
            return

        current = self._window.GetPosition()
        _log_debug(f"apply_position_after_show: current=({current.x}, {current.y}) target=({x}, {y})")

        # Only re-apply if significantly different
        if abs(current.x - x) > 20 or abs(current.y - y) > 20:
            _log_debug(f"  Re-applying position ({x}, {y})")
            self._window.SetPosition(wx.Point(x, y))

            final = self._window.GetPosition()
            _log_debug(f"  Final position: ({final.x}, {final.y})")

            if abs(final.x - x) > 50 or abs(final.y - y) > 50:
                if self._on_wayland:
                    _log_debug("  Position not applied (expected on Wayland)")
                else:
                    _log_debug("  WARNING: Position not applied correctly")

    def save_position(self):
        """Save the position of the window.

        Called when window is about to close. Saves both via PersistenceManager
        and Task Coach specific settings (monitor index, iconized state).
        """
        iconized = self._window.IsIconized()
        maximized = self._window.IsMaximized()
        pos = self._window.GetPosition()
        size = self._window.GetSize()
        monitor = wx.Display.GetFromWindow(self._window)

        _log_debug(f"save_position: iconized={iconized} maximized={maximized} monitor={monitor}")
        _log_debug(f"  pos=({pos.x}, {pos.y}) size=({size.width}, {size.height})")

        # Save Task Coach specific settings
        self._settings.setvalue("window", "iconized", iconized)
        if monitor != wx.NOT_FOUND:
            self._settings.setvalue("window", "monitor_index", monitor)
            _log_debug(f"  Saved monitor_index={monitor}")

        # Let PersistenceManager save the geometry via our custom handler
        if self._persistence_manager:
            self._persistence_manager.SaveAndUnregister(self._window)
            _log_debug("Saved geometry via PersistenceManager")


# Keep these for backward compatibility with dialogs that use the old API
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
    """Track the size and position of a dialog window.

    For dialogs, we use the simpler direct approach since they are
    typically modal and positioned relative to their parent.
    """

    def __init__(self, window, settings, section):
        super().__init__(settings, section)
        self._window = window
        self._is_maximized = False

        self._window.SetMinSize((400, 300))
        self._restore_dimensions()
        self._window.Bind(wx.EVT_MAXIMIZE, self._on_maximize)

    def _on_maximize(self, event):
        self._is_maximized = True
        event.Skip()

    def _restore_dimensions(self):
        """Restore window dimensions from settings."""
        x, y = self.get_setting("position")
        width, height = self.get_setting("size")
        maximized = self.get_setting("maximized")

        width = max(width, 400) if width > 0 else 400
        height = max(height, 300) if height > 0 else 300

        if x == -1 and y == -1:
            self._window.SetSize(width, height)
            self._window.Center()
        else:
            self._window.SetSize(x, y, width, height)

        if maximized:
            self._window.Maximize()
            self._is_maximized = True

    def apply_position_after_show(self):
        """No-op for dialogs."""
        pass

    def save_state(self):
        """Save the current window state."""
        maximized = self._window.IsMaximized() or self._is_maximized
        iconized = self._window.IsIconized()

        self.set_setting("maximized", maximized)

        if not iconized:
            pos = self._window.GetPosition()
            self.set_setting("position", (pos.x, pos.y))

            if not maximized:
                size = (self._window.GetClientSize() if operating_system.isMac()
                        else self._window.GetSize())
                self.set_setting("size", (size.width, size.height))
