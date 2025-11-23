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
    """Log debug message with timestamp including milliseconds."""
    if _DEBUG_WINDOW_TRACKING:
        now = time.time()
        timestamp = time.strftime("%H:%M:%S", time.localtime(now))
        ms = int((now % 1) * 1000)
        print(f"[{timestamp}.{ms:03d}] WindowTracker: {msg}")


class WindowGeometryTracker:
    """Track and restore window geometry (position, size, maximized state).

    Single source of truth for DESIRED window state. While not ready, we keep
    trying to make the actual window match the desired state.

    State (desired, persisted):
        position: (x, y) - desired restore position
        size: (w, h) - desired restore size
        maximized: bool - desired maximize state

    State (in-memory):
        ready: bool - window matches desired state
        activated: bool - EVT_ACTIVATE has fired

    Rules:
        - While not ready: keep trying to achieve desired state
        - After ready: cache window changes back to state
        - Only cache position/size when not maximized and not iconized
    """

    def __init__(self, window, settings, section):
        self._window = window
        self._settings = settings
        self._section = section

        # === Desired state (persisted) ===
        self.position = None    # (x, y)
        self.size = None        # (w, h)
        self.maximized = False  # True if should be maximized

        # === In-memory state ===
        self.ready = False      # Window matches desired state
        self.activated = False  # EVT_ACTIVATE has fired

        # Position logging timer
        self._pos_log_timer = None
        self._pos_log_start_time = None

        # Check for Wayland
        self._on_wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland' or \
                          os.environ.get('WAYLAND_DISPLAY') is not None
        if self._on_wayland:
            _log_debug("Running on Wayland - window positioning blocked by compositor")

        # Set minimum size
        if isinstance(self._window, wx.Dialog):
            self._window.SetMinSize((400, 300))
        else:
            self._window.SetMinSize((600, 400))

        # Load desired state from file and apply to window
        self.load()

        # Bind event handlers
        self._window.Bind(wx.EVT_MOVE, self._on_move)
        self._window.Bind(wx.EVT_SIZE, self._on_size)
        self._window.Bind(wx.EVT_MAXIMIZE, self._on_maximize)
        self._window.Bind(wx.EVT_ACTIVATE, self._on_activate)

        # Start position logging for debugging
        self._start_position_logging()

    # === Settings I/O ===

    def _get_setting(self, setting):
        """Get value from settings file."""
        return self._settings.getvalue(self._section, setting)

    def _set_setting(self, setting, value):
        """Set value in settings file."""
        self._settings.setvalue(self._section, setting, value)

    # === State persistence ===

    def load(self):
        """Load desired state from settings file and apply to window."""
        x, y = self._get_setting("position")
        width, height = self._get_setting("size")
        self.maximized = self._get_setting("maximized")

        _log_debug(f"LOAD: pos=({x}, {y}) size=({width}, {height}) maximized={self.maximized}")

        # Enforce minimum size
        min_w, min_h = self._window.GetMinSize()
        width = max(width, min_w) if width > 0 else min_w
        height = max(height, min_h) if height > 0 else min_h

        # Store desired size
        self.size = (width, height)

        # Validate and set position
        if x == -1 and y == -1:
            # No saved position - let WM place it
            self._window.SetSize(width, height)
            self.position = None
            _log_debug(f"  No saved position, letting WM place window")
        else:
            validated = self._validate_position(x, y, width, height)
            if validated is None:
                # Position invalid - let WM place it
                self._window.SetSize(width, height)
                self.position = None
            else:
                x, y = validated
                self._window.SetSize(x, y, width, height)
                self.position = (x, y)
                _log_debug(f"  Set desired position={self.position}")

        _log_debug(f"  Set desired size={self.size}")
        _log_debug(f"  Set desired maximized={self.maximized}")

        if operating_system.isMac():
            self._window.SetClientSize((width, height))

    def save(self):
        """Save current state to settings file."""
        _log_debug(f"SAVE: pos={self.position} size={self.size} maximized={self.maximized}")

        self._set_setting("maximized", self.maximized)

        if self.position:
            self._set_setting("position", self.position)

        if self.size:
            self._set_setting("size", self.size)

    # === Window correction ===

    def _is_normal_state(self):
        """Return True if window is in normal state (not maximized, not iconized)."""
        return not self._window.IsMaximized() and not self._window.IsIconized()

    def check_and_correct(self):
        """Try to make window match desired state. Called while not ready."""
        if self.ready:
            return

        is_max = self._window.IsMaximized()
        is_icon = self._window.IsIconized()

        # If iconized, can't do anything
        if is_icon:
            return

        # If desired maximized
        if self.maximized:
            if is_max:
                # Already maximized - we're ready
                self._mark_ready()
            else:
                # Not yet maximized - first ensure position/size correct, then maximize
                pos = self._window.GetPosition()
                size = self._window.GetSize()
                pos_ok = self._check_position(pos)
                size_ok = self._check_size(size)

                if pos_ok and size_ok and self.activated:
                    # Position/size correct, now maximize
                    _log_debug(f"check_and_correct: position/size correct, now maximizing")
                    self._window.Maximize()
        else:
            # Desired not maximized - ensure position/size correct
            pos = self._window.GetPosition()
            size = self._window.GetSize()
            pos_ok = self._check_position(pos)
            size_ok = self._check_size(size)

            if pos_ok and size_ok and self.activated:
                self._mark_ready()

    def _check_position(self, pos):
        """Check and correct position. Returns True if position is OK."""
        if self.position is None:
            return True

        target_x, target_y = self.position
        if pos.x != target_x or pos.y != target_y:
            _log_debug(f"_check_position: ({pos.x}, {pos.y}) != target ({target_x}, {target_y}), correcting")
            self._window.SetPosition(wx.Point(target_x, target_y))
            return False
        return True

    def _check_size(self, size):
        """Check and correct size. Returns True if size is OK."""
        if self.size is None:
            return True

        target_w, target_h = self.size
        if size.width != target_w or size.height != target_h:
            _log_debug(f"_check_size: ({size.width}, {size.height}) != target ({target_w}, {target_h}), correcting")
            self._window.SetSize(target_w, target_h)
            return False
        return True

    def _mark_ready(self):
        """Mark window as ready - it now matches desired state."""
        elapsed = time.time() - self._pos_log_start_time

        self.ready = True
        _log_debug(f"WINDOW READY [{elapsed:.2f}s]: maximized={self.maximized} pos={self.position} size={self.size}")

        # Stop position logging
        if self._pos_log_timer:
            self._pos_log_timer.Stop()
            self._pos_log_timer = None

        # If not maximized, update state with actual final values
        if not self.maximized:
            pos = self._window.GetPosition()
            size = self._window.GetSize()
            self.position = (pos.x, pos.y)
            self.size = (size.width, size.height)
            _log_debug(f"  Final state: pos={self.position} size={self.size}")

    # === State updates from window (after ready) ===

    def cache_from_window(self):
        """Update state from window (only when in normal state)."""
        if self._is_normal_state():
            pos = self._window.GetPosition()
            size = self._window.GetSize()
            self.position = (pos.x, pos.y)
            if size.width > 100 and size.height > 100:
                self.size = (size.width, size.height)
            self.maximized = False
            _log_debug(f"cache_from_window: pos={self.position} size={self.size}")
        elif self._window.IsMaximized():
            self.maximized = True
            _log_debug(f"cache_from_window: maximized=True (restore values unchanged)")

    # === Event handlers ===

    def _on_move(self, event):
        """Handle window move."""
        if not self.ready:
            self.check_and_correct()
        else:
            self.cache_from_window()
        event.Skip()

    def _on_size(self, event):
        """Handle window resize."""
        if not self.ready:
            self.check_and_correct()
        else:
            self.cache_from_window()
        event.Skip()

    def _on_maximize(self, event):
        """Handle maximize/restore."""
        is_max = self._window.IsMaximized()
        _log_debug(f"EVT_MAXIMIZE: IsMaximized={is_max}")

        if not self.ready:
            self.check_and_correct()
        else:
            self.cache_from_window()
        event.Skip()

    def _on_activate(self, event):
        """Handle window activation."""
        if event.GetActive() and not self.activated:
            self.activated = True
            _log_debug(f"EVT_ACTIVATE: Window activated")
            self.check_and_correct()
        event.Skip()

    # === Position validation ===

    def _validate_position(self, x, y, width, height):
        """Validate position fits on a monitor. Returns (x, y) or None."""
        num_displays = wx.Display.GetCount()
        _log_debug(f"_validate_position: checking ({x}, {y}) against {num_displays} monitors")

        for i in range(num_displays):
            display = wx.Display(i)
            geometry = display.GetGeometry()
            _log_debug(f"  Monitor {i}: {geometry.x}, {geometry.y}, {geometry.width}x{geometry.height}")

            # Check if window is reasonably within this monitor
            if (geometry.x - width + 100 <= x <= geometry.x + geometry.width - 100 and
                geometry.y <= y <= geometry.y + geometry.height - 100):
                _log_debug(f"  Position valid for monitor {i}")

                # Ensure window doesn't go below monitor
                max_y = geometry.y + geometry.height - height - 50
                if y > max_y:
                    _log_debug(f"  Adjusting Y from {y} to {max_y}")
                    y = max(geometry.y, max_y)

                return (x, y)

        _log_debug(f"  Position ({x}, {y}) not valid for any monitor")
        return None

    # === Debug logging ===

    def _start_position_logging(self):
        """Start position logging for debugging."""
        self._pos_log_start_time = time.time()
        self._log_position_tick()

    def _log_position_tick(self):
        """Log current position until ready."""
        if not self._window or self.ready:
            self._pos_log_timer = None
            return

        elapsed = time.time() - self._pos_log_start_time
        pos = self._window.GetPosition()
        size = self._window.GetSize()
        is_max = self._window.IsMaximized()

        _log_debug(f"POS_LOG [{elapsed:.2f}s]: pos=({pos.x}, {pos.y}) size=({size.width}, {size.height}) max={is_max}")

        # Schedule next tick
        interval = 50 if elapsed < 1.0 else 500
        if elapsed < 10.0:
            self._pos_log_timer = wx.CallLater(interval, self._log_position_tick)


class WindowDimensionsTracker(WindowGeometryTracker):
    """Track the dimensions of the main window in the settings."""

    def __init__(self, window, settings):
        super().__init__(window, settings, "window")

        # Handle start iconized setting (Task Coach specific)
        if self._should_start_iconized():
            if operating_system.isMac() or operating_system.isGTK():
                self._window.Show()
            self._window.Iconize(True)
            if not operating_system.isMac() and self._get_setting("hidewheniconized"):
                wx.CallAfter(self._window.Hide)

    def _should_start_iconized(self):
        """Return whether the window should be opened iconized."""
        start_iconized = self._settings.get("window", "starticonized")
        return start_iconized == "Always"

    def save_position(self):
        """Save the position of the window in the settings."""
        self.save()
