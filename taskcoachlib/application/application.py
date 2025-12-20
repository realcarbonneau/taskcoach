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

# This module works around bugs in third party modules, mostly by
# monkey-patching so import it first
from taskcoachlib import workarounds  # pylint: disable=W0611
from taskcoachlib import patterns, operating_system
from taskcoachlib.i18n import _
from pubsub import pub
from taskcoachlib.config import Settings
import locale
import logging
import os
import sys
import time
import wx
import calendar
import re
import threading
import subprocess


# ============================================================================
# Logging Setup
# ============================================================================
#
# Task Coach uses Python's logging module for Python diagnostic output,
# plus stderr capture for native library errors (GTK, pixman, etc.).
#
# Architecture:
#   - FileHandler: Logs everything (DEBUG+) to taskcoachlog.txt
#   - ErrorTracker: Custom handler that tracks if any ERROR+ occurred
#   - StderrCapture: Intercepts stderr for native C library output
#   - The error popup only shows if ErrorTracker.has_errors is True
#
# Usage:
#   logger.debug("Version info...")   -> Goes to file only
#   logger.info("Startup complete")   -> Goes to file only
#   logger.error("Something broke!")  -> Goes to file AND sets has_errors=True
#   Native stderr (GTK-CRITICAL etc)  -> Goes to file AND sets has_errors=True
#
# This replaces the old RedirectedOutput hack that captured stdout/stderr.
# ============================================================================

# Create the main logger for Task Coach
logger = logging.getLogger('taskcoach')
logger.setLevel(logging.DEBUG)

# Will be initialized by init_logging() when we know the log file path
_file_handler = None
_error_tracker = None
_stderr_capture = None
_log_file = None  # Direct file handle for stderr capture


class ErrorTracker(logging.Handler):
    """Custom handler that tracks if any ERROR-level (or higher) messages occurred.

    This handler doesn't output anything - it just sets a flag when an error
    is logged. The flag is checked on application exit to decide whether to
    show the error popup.

    Thread-safe: uses a lock for the has_errors flag.
    """

    def __init__(self):
        super().__init__(level=logging.ERROR)
        self._has_errors = False
        self._lock = threading.Lock()

    @property
    def has_errors(self):
        with self._lock:
            return self._has_errors

    def set_error(self):
        """Mark that an error has occurred (called by StderrCapture)."""
        with self._lock:
            self._has_errors = True

    def emit(self, record):
        with self._lock:
            self._has_errors = True


class StderrCapture:
    """Captures stderr output from native libraries (GTK, pixman, etc.).

    Native C libraries write directly to stderr, bypassing Python's logging.
    This class intercepts stderr to:
    1. Log all stderr output to the log file
    2. Detect error patterns and set ErrorTracker.has_errors
    3. Also write to original stderr (for terminal visibility)

    Error patterns detected:
    - GTK-CRITICAL, GTK-WARNING, Gtk-CRITICAL, etc.
    - *** BUG ***
    - CRITICAL, ERROR (case-insensitive)
    - assertion ... failed
    - Segmentation fault, SIGSEGV, etc.
    """

    # Patterns that indicate a real error (not just debug info)
    ERROR_PATTERNS = [
        r'CRITICAL',
        r'ERROR',
        r'\*\*\* BUG \*\*\*',
        r'assertion.*failed',
        r'Segmentation fault',
        r'SIGSEGV',
        r'SIGABRT',
        r'core dumped',
    ]

    def __init__(self, original_stderr, log_file, error_tracker):
        self._original_stderr = original_stderr
        self._log_file = log_file
        self._error_tracker = error_tracker
        self._lock = threading.Lock()
        # Compile patterns for efficiency
        self._error_regex = re.compile(
            '|'.join(self.ERROR_PATTERNS),
            re.IGNORECASE
        )

    def write(self, text):
        """Write to log file and original stderr, checking for errors."""
        if not text:
            return

        with self._lock:
            # Write to log file with timestamp
            try:
                import datetime
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._log_file.write(f"{timestamp} [STDERR] {text}")
                if not text.endswith('\n'):
                    self._log_file.write('\n')
                self._log_file.flush()
            except Exception:
                pass  # Don't crash on logging failure

            # Write to original stderr (for terminal visibility)
            try:
                if self._original_stderr:
                    self._original_stderr.write(text)
                    self._original_stderr.flush()
            except Exception:
                pass

            # Check for error patterns
            if self._error_regex.search(text):
                self._error_tracker.set_error()

    def flush(self):
        """Flush both log file and original stderr."""
        with self._lock:
            try:
                self._log_file.flush()
            except Exception:
                pass
            try:
                if self._original_stderr:
                    self._original_stderr.flush()
            except Exception:
                pass

    def fileno(self):
        """Return file descriptor for compatibility."""
        if self._original_stderr:
            return self._original_stderr.fileno()
        raise OSError("No file descriptor available")

    def isatty(self):
        """Check if original stderr is a TTY."""
        try:
            return self._original_stderr and self._original_stderr.isatty()
        except Exception:
            return False


def init_logging():
    """Initialize the logging system.

    Sets up:
    - FileHandler: Always logs DEBUG+ to taskcoachlog.txt
    - StreamHandler: When running from TTY, also logs to stdout
    - ErrorTracker: Tracks if any ERROR+ occurred (for popup decision)
    - StderrCapture: Captures native library stderr (GTK, pixman errors)
    - Exception hook: Logs uncaught exceptions

    Called early in Application.init().
    """
    global _file_handler, _error_tracker, _stderr_capture, _log_file

    log_path = os.path.join(Settings.pathToDocumentsDir(), "taskcoachlog.txt")

    # Create formatter for all handlers
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler - always logs everything to file
    _file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(formatter)
    logger.addHandler(_file_handler)

    # Stream handler - also log to stdout when running from terminal
    try:
        isatty = sys.stdout.isatty()
    except AttributeError:
        isatty = False

    if isatty:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Error tracker - tracks if any ERROR+ occurred (for popup decision)
    _error_tracker = ErrorTracker()
    logger.addHandler(_error_tracker)

    # Capture stderr for native library output (GTK, pixman, etc.)
    # These bypass Python's logging module, writing directly to stderr.
    # We need a separate file handle because logging.FileHandler owns its handle.
    _log_file = open(log_path, 'a', encoding='utf-8')
    _stderr_capture = StderrCapture(sys.stderr, _log_file, _error_tracker)
    sys.stderr = _stderr_capture

    # Log session start marker
    logger.debug("=" * 60)
    logger.debug("Task Coach session started")
    logger.debug("=" * 60)

    # Install exception hook to log uncaught exceptions
    _original_excepthook = sys.excepthook

    def logging_excepthook(exc_type, exc_value, exc_traceback):
        """Log uncaught exceptions before they crash the app."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log keyboard interrupts as errors
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        # Also call the original hook (for faulthandler etc.)
        _original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = logging_excepthook


def shutdown_logging():
    """Check if errors occurred and show popup if needed, then close handlers.

    Called from Application.quitApplication().
    """
    global _file_handler, _error_tracker, _stderr_capture, _log_file

    # Restore original stderr before closing log file
    if _stderr_capture:
        sys.stderr = _stderr_capture._original_stderr
        _stderr_capture = None

    if _error_tracker and _error_tracker.has_errors:
        log_path = os.path.join(Settings.pathToDocumentsDir(), "taskcoachlog.txt")

        # Close file handlers before showing popup (releases file lock)
        if _file_handler:
            _file_handler.close()
            logger.removeHandler(_file_handler)
        if _log_file:
            _log_file.close()
            _log_file = None

        if operating_system.isWindows():
            wx.MessageBox(
                _(
                    'Errors have occured. Please see "taskcoachlog.txt" in your "My Documents" folder.'
                ),
                _("Error"),
                wx.OK,
            )
        else:
            wx.MessageBox(
                _('Errors have occured. Please see "%s"') % log_path,
                _("Error"),
                wx.OK,
            )
    else:
        # No errors, just close the file handlers
        if _file_handler:
            _file_handler.close()
            logger.removeHandler(_file_handler)
        if _log_file:
            _log_file.close()
            _log_file = None


def _log_gui_environment():
    """Log GUI environment details for debugging window positioning issues."""
    logger.debug("=" * 60)
    logger.debug("GUI ENVIRONMENT INFO")
    logger.debug("=" * 60)

    # wx platform details (more detailed than basic wx.version())
    logger.debug(f"wx.PlatformInfo: {wx.PlatformInfo}")

    # Platform-specific info
    if sys.platform == 'win32':
        _log_windows_environment()
    elif sys.platform == 'darwin':
        _log_macos_environment()
    else:
        _log_linux_environment()

    # Display/monitor info (cross-platform)
    try:
        num_displays = wx.Display.GetCount()
        logger.debug(f"Number of displays: {num_displays}")
        for i in range(num_displays):
            display = wx.Display(i)
            geom = display.GetGeometry()
            client = display.GetClientArea()
            # Get DPI/scaling if available
            try:
                ppi = display.GetPPI()
                logger.debug(f"  Display {i}: geometry={geom.x},{geom.y} {geom.width}x{geom.height}  "
                             f"client_area={client.x},{client.y} {client.width}x{client.height}  "
                             f"PPI={ppi.x}x{ppi.y}")
            except Exception:
                logger.debug(f"  Display {i}: geometry={geom.x},{geom.y} {geom.width}x{geom.height}  "
                             f"client_area={client.x},{client.y} {client.width}x{client.height}")
    except Exception as e:
        logger.debug(f"Display info unavailable: {e}")

    logger.debug("=" * 60)


def _log_windows_environment():
    """Log Windows-specific GUI environment info."""
    import platform

    # Windows version
    logger.debug(f"Windows Version: {platform.win32_ver()[0]} {platform.win32_ver()[1]}")
    logger.debug(f"Windows Edition: {platform.win32_edition()}")

    # DPI awareness
    try:
        import ctypes
        awareness = ctypes.windll.shcore.GetProcessDpiAwareness(0)
        awareness_names = {0: 'Unaware', 1: 'System', 2: 'PerMonitor'}
        logger.debug(f"DPI Awareness: {awareness_names.get(awareness, awareness)}")
    except Exception as e:
        logger.debug(f"DPI Awareness: unavailable ({e})")

    # DWM (Desktop Window Manager) composition
    try:
        import ctypes
        dwm_enabled = ctypes.c_bool()
        ctypes.windll.dwmapi.DwmIsCompositionEnabled(ctypes.byref(dwm_enabled))
        logger.debug(f"DWM Composition: {'Enabled' if dwm_enabled.value else 'Disabled'}")
    except Exception as e:
        logger.debug(f"DWM Composition: unavailable ({e})")

    # System DPI
    try:
        import ctypes
        hdc = ctypes.windll.user32.GetDC(0)
        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
        ctypes.windll.user32.ReleaseDC(0, hdc)
        logger.debug(f"System DPI: {dpi_x}x{dpi_y} (scale: {dpi_x/96*100:.0f}%)")
    except Exception as e:
        logger.debug(f"System DPI: unavailable ({e})")


def _log_macos_environment():
    """Log macOS-specific GUI environment info."""
    import platform

    # macOS version
    mac_ver = platform.mac_ver()
    logger.debug(f"macOS Version: {mac_ver[0]}")
    logger.debug(f"Architecture: {mac_ver[2]}")

    # Check if running under Rosetta (Apple Silicon)
    try:
        result = subprocess.run(['sysctl', '-n', 'sysctl.proc_translated'],
                               capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip() == '1':
            logger.debug("Rosetta 2: Yes (x86_64 on ARM)")
        else:
            logger.debug("Rosetta 2: No (native)")
    except Exception:
        pass

    # Retina/scaling info via system_profiler (slow but comprehensive)
    try:
        result = subprocess.run(
            ['system_profiler', 'SPDisplaysDataType', '-json'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            displays = data.get('SPDisplaysDataType', [{}])[0].get('spdisplays_ndrvs', [])
            for i, disp in enumerate(displays):
                res = disp.get('_spdisplays_resolution', 'unknown')
                retina = disp.get('spdisplays_retina', 'unknown')
                logger.debug(f"  macOS Display {i}: {res} Retina={retina}")
    except Exception:
        pass

    # Window server info
    try:
        result = subprocess.run(['defaults', 'read', 'com.apple.WindowServer'],
                               capture_output=True, text=True, timeout=2)
        # Just check if it runs - detailed parsing would be verbose
        if result.returncode == 0:
            logger.debug("WindowServer: accessible")
    except Exception:
        pass


def _log_linux_environment():
    """Log Linux/GTK-specific GUI environment info."""
    # Session type
    session_type = os.environ.get('XDG_SESSION_TYPE', 'unknown')
    logger.debug(f"XDG_SESSION_TYPE: {session_type}")
    logger.debug(f"WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'not set')}")
    logger.debug(f"DISPLAY: {os.environ.get('DISPLAY', 'not set')}")

    # Desktop environment
    desktop = os.environ.get('XDG_CURRENT_DESKTOP',
              os.environ.get('DESKTOP_SESSION', 'unknown'))
    logger.debug(f"Desktop Environment: {desktop}")

    # GTK version (if available)
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        logger.debug(f"GTK Version: {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}")
    except Exception as e:
        logger.debug(f"GTK Version: unavailable ({e})")

    # GDK backend
    try:
        gdk_backend = os.environ.get('GDK_BACKEND', 'auto')
        logger.debug(f"GDK_BACKEND: {gdk_backend}")
    except Exception:
        pass

    # Window manager detection
    wm_name = "unknown"
    wm_version = "unknown"

    # Try wmctrl first
    try:
        result = subprocess.run(['wmctrl', '-m'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Name:'):
                    wm_name = line.split(':', 1)[1].strip()
                    break
    except Exception:
        pass

    # Try xprop for WM info
    if wm_name == "unknown":
        try:
            result = subprocess.run(
                ['xprop', '-root', '-notype', '_NET_WM_NAME', '_NET_SUPPORTING_WM_CHECK'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '_NET_WM_NAME' in line and '=' in line:
                        wm_name = line.split('=', 1)[1].strip().strip('"')
                        break
        except Exception:
            pass

    # Try getting WM version from common WMs
    wm_lower = wm_name.lower()
    try:
        if 'openbox' in wm_lower:
            result = subprocess.run(['openbox', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.split('\n')[0]
        elif 'mutter' in wm_lower or 'gnome' in wm_lower:
            result = subprocess.run(['mutter', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.strip()
        elif 'kwin' in wm_lower:
            result = subprocess.run(['kwin_x11', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.split('\n')[0]
        elif 'xfwm' in wm_lower:
            result = subprocess.run(['xfwm4', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.split('\n')[0]
        elif 'marco' in wm_lower:
            result = subprocess.run(['marco', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.strip()
        elif 'metacity' in wm_lower:
            result = subprocess.run(['metacity', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.strip()
        elif 'i3' in wm_lower:
            result = subprocess.run(['i3', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.split('\n')[0]
        elif 'sway' in wm_lower:
            result = subprocess.run(['sway', '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                wm_version = result.stdout.strip()
    except Exception:
        pass

    logger.debug(f"Window Manager: {wm_name}")
    logger.debug(f"WM Version: {wm_version}")


# pylint: disable=W0404


class wxApp(wx.App):
    def __init__(self, sessionCallback, reopenCallback, *args, **kwargs):
        self.sessionCallback = sessionCallback
        self.reopenCallback = reopenCallback
        self.__shutdownInProgress = False
        super().__init__(*args, **kwargs)

    def MacReopenApp(self):
        self.reopenCallback()

    def OnInit(self):
        if operating_system.isWindows():
            self.Bind(wx.EVT_QUERY_END_SESSION, self.onQueryEndSession)
        # NOTE: stdout/stderr redirection removed.
        # Now using Python's logging module instead - see init_logging().
        return True

    def onQueryEndSession(self, event=None):
        if not self.__shutdownInProgress:
            self.__shutdownInProgress = True
            self.sessionCallback()

        if event is not None:
            event.Skip()


class Application(object, metaclass=patterns.Singleton):
    """
    Main application class for Task Coach.

    DESIGN NOTE (Twisted Removal - 2024):
    Previously used Twisted's wxreactor to integrate Twisted's event loop with
    wxPython. This has been replaced with native wxPython functionality:
    - wxreactor.install() → removed (wx.App.MainLoop() used directly)
    - reactor.registerWxApp() → removed (not needed)
    - reactor.run() → wx.App.MainLoop()
    - reactor.stop() → wx.App.ExitMainLoop() via EVT_CLOSE handlers
    - reactor.callLater() → wx.CallLater() (in scheduler.py)

    This simplifies the event loop architecture and eliminates potential
    race conditions between two event loops.
    """
    def __init__(self, options=None, args=None, **kwargs):
        self._options = options
        self._args = args
        # NOTE: Twisted initialization removed - using native wx event loop
        self.__wx_app = wxApp(
            self.on_end_session, self.on_reopen_app, redirect=False
        )
        self.init(**kwargs)

        if operating_system.isGTK():
            if self.settings.getboolean("feature", "usesm2"):
                from taskcoachlib.powermgt import xsm

                class LinuxSessionMonitor(xsm.SessionMonitor):
                    def __init__(self, callback):
                        super().__init__()
                        self._callback = callback
                        self.setProperty(xsm.SmCloneCommand, sys.argv)
                        self.setProperty(xsm.SmRestartCommand, sys.argv)
                        self.setProperty(xsm.SmCurrentDirectory, os.getcwd())
                        self.setProperty(xsm.SmProgram, sys.argv[0])
                        self.setProperty(
                            xsm.SmRestartStyleHint, xsm.SmRestartNever
                        )

                    def saveYourself(
                        self, saveType, shutdown, interactStyle, fast
                    ):  # pylint: disable=W0613
                        if shutdown:
                            wx.CallAfter(self._callback)
                        self.saveYourselfDone(True)

                    def die(self):
                        pass

                    def saveComplete(self):
                        pass

                    def shutdownCancelled(self):
                        pass

                self.sessionMonitor = LinuxSessionMonitor(
                    self.on_end_session
                )  # pylint: disable=W0201
            else:
                self.sessionMonitor = None

        calendar.setfirstweekday(
            dict(monday=0, sunday=6)[self.settings.get("view", "weekstart")]
        )

    # NOTE: initTwisted(), stopTwisted(), and registerApp() methods removed.
    # Previously used Twisted's wxreactor for event loop integration.
    # Now using native wx.App.MainLoop() which is simpler and more reliable.
    # See class docstring for migration details.

    def _log_version_info(self):
        """Log version info for debugging - called early in init() before any GUI."""
        from taskcoachlib import meta
        import platform

        # Log version info at startup for debugging
        if meta.git_commit_hash:
            logger.debug(f"Task Coach {meta.version_full} (commit {meta.git_commit_hash})")
        else:
            logger.debug(f"Task Coach {meta.version_full}")
        logger.debug(f"Python {sys.version}")
        logger.debug(f"wxPython {wx.version()}")
        logger.debug(f"Platform: {platform.platform()}")

        # Log GTK/glibc info on Linux
        if platform.system() == 'Linux':
            try:
                import ctypes
                libc = ctypes.CDLL('libc.so.6')
                gnu_get_libc_version = libc.gnu_get_libc_version
                gnu_get_libc_version.restype = ctypes.c_char_p
                logger.debug(f"glibc {gnu_get_libc_version().decode()}")
            except (OSError, AttributeError):
                pass  # glibc version detection may fail

        # Log zeroconf version (used for iPhone sync)
        try:
            import zeroconf
            logger.debug(f"zeroconf {zeroconf.__version__}")
        except ImportError:
            pass  # zeroconf is optional

    def start(self):
        """Call this to start the Application."""
        from taskcoachlib import meta

        if self.settings.getboolean("version", "notify"):
            self.__version_checker = meta.VersionChecker(self.settings)
            self.__version_checker.start()
        if self.settings.getboolean("view", "developermessages"):
            self.__message_checker = meta.DeveloperMessageChecker(
                self.settings
            )
            self.__message_checker.start()
        self.__copy_default_templates()

        # Enable wxPython debug logging on GTK to help diagnose crashes
        # This helps identify which wx events/callbacks were active when segfaults occur
        # Only visible when running from terminal, doesn't affect GUI-only users
        if operating_system.isGTK():
            wx.Log.SetActiveTarget(wx.LogStderr())
            wx.Log.SetLogLevel(wx.LOG_Info)
            wx.Log.SetVerbose(True)

        self.mainwindow.Show()
        # Position correction is handled automatically by WindowDimensionsTracker
        # via EVT_MOVE detection until EVT_ACTIVATE fires (window ready for input)
        # Use native wxPython main loop instead of Twisted reactor
        # NOTE: Previously used reactor.run() with wxreactor integration.
        # Now using wx.App.MainLoop() directly for simpler event handling.
        self.__wx_app.MainLoop()

    def __copy_default_templates(self):
        """Copy default templates that don't exist yet in the user's
        template directory."""
        from taskcoachlib.persistence import getDefaultTemplates

        template_dir = self.settings.pathToTemplatesDir()
        if (
            len(
                [
                    name
                    for name in os.listdir(template_dir)
                    if name.endswith(".tsktmpl")
                ]
            )
            == 0
        ):
            for name, template in getDefaultTemplates():
                filename = os.path.join(template_dir, name + ".tsktmpl")
                if not os.path.exists(filename):
                    # Decode bytes to string for text mode writing
                    template_str = template.decode('utf-8') if isinstance(template, bytes) else template
                    open(filename, "w", encoding="utf-8").write(template_str)

    def init(self, loadSettings=True, loadTaskFile=True):
        """Initialize the application. Needs to be called before
        Application.start()."""
        # Initialize the logging system first
        init_logging()

        # Log version/environment info for debugging
        self._log_version_info()
        _log_gui_environment()

        self.__init_config(loadSettings)
        self.__init_language()
        self.__init_domain_objects()
        self.__init_application()

        # Check file lock BEFORE creating main window to avoid dialog/focus issues
        # This is done early because showing dialogs after main window creation
        # causes GTK focus fighting and dialog disappearing issues
        # Note: INI file lock is already checked in __init_config() above
        self.__early_lock_result = None  # None=no file, 'ok'=proceed, 'break'=break lock, 'skip'=don't open file
        if loadTaskFile:
            self.__check_file_lock_early()
            # If user said "No" to break lock, we continue but don't open the file
            # (program starts with no file open, like a fresh start)

        from taskcoachlib import gui, persistence

        gui.init()
        # pylint: disable=W0201
        self.taskFile = persistence.LockedTaskFile(
            poll=not self.settings.getboolean("file", "nopoll")
        )
        self.__auto_saver = persistence.AutoSaver(self.settings)
        self.__auto_exporter = persistence.AutoImporterExporter(self.settings)
        self.__auto_backup = persistence.AutoBackup(self.settings)
        self.iocontroller = gui.IOController(
            self.taskFile, self.displayMessage, self.settings
        )
        self.mainwindow = gui.MainWindow(
            self.iocontroller, self.taskFile, self.settings
        )
        self.__wx_app.SetTopWindow(self.mainwindow)
        self.__init_spell_checking()
        if not self.settings.getboolean("file", "inifileloaded"):
            self.__warn_user_that_ini_file_was_not_loaded()
        if loadTaskFile:
            self.iocontroller.openAfterStart(self._args, self.__early_lock_result)
        self.__register_signal_handlers()
        self.__create_mutex()
        self.__create_task_bar_icon()
        wx.CallAfter(self.__show_tips)

    def __check_file_lock_early(self):
        """Check file lock before main window creation.

        This avoids GTK dialog/focus issues by showing any lock dialogs
        before any windows exist.
        """
        from taskcoachlib import persistence, meta

        # Get filename from args or last file
        if self._args:
            filename = self._args[0].decode(sys.getfilesystemencoding())
        else:
            filename = self.settings.get("file", "lastfile")

        if not filename or not os.path.exists(filename):
            self.__early_lock_result = None
            return

        # Try to check if file is locked
        lock_file_path = filename + ".lock"
        try:
            import fasteners
            lock = fasteners.InterProcessLock(lock_file_path)
            acquired = lock.acquire(blocking=False)
            if acquired:
                # Not locked - release and proceed normally
                lock.release()
                self.__early_lock_result = 'ok'
                return
            else:
                # File is locked - show dialog BEFORE main window
                result = wx.MessageBox(
                    _(
                        """Cannot open %s because it is locked.

This means either that another instance of TaskCoach
is running and has this file opened, or that a previous
instance of Task Coach crashed. If no other instance is
running, you can safely break the lock.

Break the lock?"""
                    ) % filename,
                    _("%s: file locked") % meta.name,
                    style=wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT,
                )
                if result == wx.YES:
                    self.__early_lock_result = 'break'
                else:
                    # User said No - don't open file, start with empty/new
                    self.__early_lock_result = 'skip'
        except Exception:
            # Lock check failed (e.g., network drive) - proceed normally
            self.__early_lock_result = 'ok'

    def __init_config(self, load_settings):
        from taskcoachlib import config

        ini_file = self._options.inifile if self._options else None
        # pylint: disable=W0201
        self.settings = config.Settings(load_settings, ini_file)
        # Make settings accessible via wx.GetApp() for dialogs that need it
        self.__wx_app.settings = self.settings

    def __init_language(self):
        """Initialize the current translation."""
        from taskcoachlib import i18n

        i18n.Translator(self.determine_language(self._options, self.settings))

    @staticmethod
    def determine_language(
        options, settings, locale=locale
    ):  # pylint: disable=W0621
        language = None
        if options:
            # User specified language or .po file on command line
            language = options.pofile or options.language
        if not language:
            # Get language as set by the user via the preferences dialog
            language = settings.get("view", "language_set_by_user")
        if not language:
            # Get language as set by the user or externally (e.g. PortableApps)
            language = settings.get("view", "language")
        if not language:
            # Use the user's locale
            language = locale.getdefaultlocale()[0]
            if language == "C":
                language = None
        if not language:
            # Fall back on what the majority of our users use
            language = "en_US"
        return language

    def __init_domain_objects(self):
        """Provide relevant domain objects with access to the settings."""
        from taskcoachlib.domain import task, attachment

        task.Task.settings = self.settings
        attachment.Attachment.settings = self.settings

    def __init_application(self):
        from taskcoachlib import meta

        self.__wx_app.SetAppName(meta.name)
        self.__wx_app.SetVendorName(meta.author)
        # Set WM_CLASS for Linux app grouping (must match StartupWMClass in .desktop)
        self.__wx_app.SetClassName("taskcoach")
        # Set AppUserModelID for Windows 7+ taskbar grouping
        if operating_system.isWindows():
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "org.taskcoach.TaskCoach"
                )
            except (ImportError, AttributeError, OSError):
                pass  # Not on Windows or API not available

    def __init_spell_checking(self):
        self.on_spell_checking(
            self.settings.getboolean("editor", "maccheckspelling")
        )
        pub.subscribe(
            self.on_spell_checking, "settings.editor.maccheckspelling"
        )

    def on_spell_checking(self, value):
        if (
            operating_system.isMac()
            and not operating_system.isMacOsXMountainLion_OrNewer()
        ):
            wx.SystemOptions.SetOptionInt(
                "mac.textcontrol-use-spell-checker", value
            )

    def __register_signal_handlers(self):
        """Register signal handlers for clean shutdown.

        DESIGN NOTE (Twisted Removal - 2024):
        Previously used Twisted's reactor which properly handled SIGINT.
        Now using Python's signal module with direct cleanup.

        Key challenges with native wxPython:
        1. Python signal handlers only run when main thread has control
        2. GUI event loops block in C code, preventing signal delivery
        3. Must save settings before exit

        Solution:
        - Custom signal handler uses wx.CallAfter for clean shutdown
        - Periodic timer wakes event loop so Python can check signals
        """
        import signal

        def handle_signal(signum, frame):
            """Handle SIGINT/SIGTERM by scheduling clean shutdown."""
            # Use CallAfter to run shutdown in the main event loop
            # This ensures proper cleanup of wx resources
            wx.CallAfter(self.quitApplication)

        # Register SIGINT/SIGTERM handlers for Unix
        if not operating_system.isWindows():
            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)

            # Start a timer to periodically wake the event loop
            # This allows Python to check for pending signals
            self._signal_check_timer = wx.Timer()
            self._signal_check_timer.Start(500)  # Check every 500ms

        if operating_system.isWindows():
            import win32api  # pylint: disable=F0401

            def quit_adapter(*args):
                # The handler is called from something that is not the main thread, so we can't do
                # much wx-related
                event = threading.Event()

                def quit():
                    try:
                        self.quitApplication()
                    finally:
                        event.set()

                wx.CallAfter(quit)
                event.wait()
                return True

            win32api.SetConsoleCtrlHandler(quit_adapter, True)

    @staticmethod
    def __create_mutex():
        """On Windows, create a mutex so that InnoSetup can check whether the
        application is running."""
        if operating_system.isWindows():
            import ctypes
            from taskcoachlib import meta

            ctypes.windll.kernel32.CreateMutexA(None, False, meta.filename)

    def __create_task_bar_icon(self):
        if self.__can_create_task_bar_icon():
            from taskcoachlib.gui import taskbaricon, menu

            self.taskBarIcon = taskbaricon.TaskBarIcon(
                self.mainwindow,  # pylint: disable=W0201
                self.taskFile.tasks(),
                self.settings,
            )
            self.taskBarIcon.setPopupMenu(
                menu.TaskBarMenu(
                    self.taskBarIcon,
                    self.settings,
                    self.taskFile,
                    self.mainwindow.__dict__.get("viewer"),
                )
            )

    def __can_create_task_bar_icon(self):
        try:
            from taskcoachlib.gui import taskbaricon  # pylint: disable=W0612

            return True
        except ImportError:
            return False  # TaskBarIcon not available on this platform

    def __show_tips(self):
        if self.settings.getboolean("window", "tips"):
            from taskcoachlib import help  # pylint: disable=W0622

            help.showTips(self.mainwindow, self.settings)

    def __warn_user_that_ini_file_was_not_loaded(self):
        from taskcoachlib import meta

        reason = self.settings.get("file", "inifileloaderror")
        wx.MessageBox(
            _("Couldn't load settings from TaskCoach.ini:\n%s") % reason,
            _("%s file error") % meta.name,
            style=wx.OK | wx.ICON_ERROR,
        )
        self.settings.setboolean("file", "inifileloaded", True)  # Reset

    def displayMessage(self, message):
        self.mainwindow.displayMessage(message)

    def on_end_session(self):
        self.mainwindow.setShutdownInProgress()
        self.quitApplication(force=True)

    def on_reopen_app(self):
        self.taskBarIcon.onTaskbarClick(None)

    def save_all_settings(self):
        """Save all settings to disk. Called on normal exit and signal handlers.

        This is the single place for saving settings, ensuring consistency
        between normal close, Ctrl-C, and other exit paths.
        """
        try:
            # Remember what the user was working on
            if hasattr(self, 'taskFile'):
                self.settings.set("file", "lastfile", self.taskFile.lastFilename())
            # Save window position, size, perspective
            if hasattr(self, 'mainwindow'):
                self.mainwindow.save_settings()
            # Write settings to disk
            self.settings.save()
            # Release ini file lock after saving
            self.settings.release_ini_lock()
        except Exception:
            pass  # Best effort - don't prevent exit

    def quitApplication(self, force=False):
        if not self.iocontroller.close(force=force):
            return False
        self.save_all_settings()
        if hasattr(self, "taskBarIcon"):
            self.taskBarIcon.RemoveIcon()
        if self.mainwindow.bonjourRegister is not None:
            self.mainwindow.bonjourRegister.stop()
        # Stop notification timers to prevent crashes during shutdown
        from taskcoachlib.notify.notifier_universal import NotificationCenter
        NotificationCenter().cleanup()
        from taskcoachlib.domain import date

        date.Scheduler().shutdown()
        wx.EventLoop.GetActive().ProcessIdle()

        # For PowerStateMixin
        self.mainwindow.OnQuit()

        if operating_system.isGTK() and self.sessionMonitor is not None:
            self.sessionMonitor.stop()

        # Check if errors occurred and show popup if needed, then close log file
        shutdown_logging()

        # NOTE: stopTwisted() call removed - no longer using Twisted reactor.
        # wxPython's MainLoop exits naturally when all windows are closed.
        # Explicitly close the main window to trigger exit.
        # Set shutdown flag so onClose() won't veto or recurse into quitApplication.
        self.mainwindow.setShutdownInProgress()
        self.mainwindow.Close()
        return True
