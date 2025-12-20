"""
Output tee for Task Coach - mirrors stdout/stderr to log file.

This module must be imported and initialized BEFORE any other imports
that might produce output (especially wx/GTK which load native libraries).

Architecture:
- Raw copy of stdout/stderr to both console and log file (like Unix tee)
- Any stderr output sets the error flag for exit popup
- No timestamps or formatting - just raw copy

Usage (in taskcoach.py, before other imports):
    from taskcoachlib.tee import init_tee
    init_tee()
"""

import os
import sys
import threading


# Module state
_log_file = None
_original_stdout_fd = None
_original_stderr_fd = None
_stdout_thread = None
_stderr_thread = None
_stop_event = None
_has_errors = False
_has_errors_lock = threading.Lock()


def _get_log_path():
    """Get the log file path with minimal dependencies."""
    if sys.platform == 'win32':
        # Windows: use USERPROFILE or HOMEPATH
        home = os.environ.get('USERPROFILE', os.environ.get('HOMEPATH', '.'))
        base = os.path.join(home, 'Documents', 'TaskCoach')
    elif sys.platform == 'darwin':
        # macOS: use ~/Library/Application Support
        home = os.path.expanduser('~')
        base = os.path.join(home, 'Library', 'Application Support', 'TaskCoach')
    else:
        # Linux/Unix: use XDG_DATA_HOME or ~/.local/share
        xdg_data = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        base = os.path.join(xdg_data, 'TaskCoach')

    # Ensure directory exists
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, 'taskcoachlog.txt')


def _tee_thread(pipe_read_fd, original_fd, log_file, is_stderr):
    """Thread that reads from pipe and writes to both console and log file."""
    global _has_errors

    stream_name = "stderr" if is_stderr else "stdout"

    try:
        while not _stop_event.is_set():
            try:
                data = os.read(pipe_read_fd, 4096)
                if not data:
                    break

                # Write to original console
                try:
                    os.write(original_fd, data)
                except OSError as e:
                    # Debug: write error to original fd
                    os.write(original_fd, f"[TEE {stream_name}] console write error: {e}\n".encode())

                # Write to log file (raw, no formatting)
                try:
                    log_file.write(data.decode('utf-8', errors='replace'))
                    log_file.flush()
                except Exception as e:
                    # Debug: write error to original fd
                    os.write(original_fd, f"[TEE {stream_name}] log write error: {e}\n".encode())

                # Set error flag if any stderr data
                if is_stderr:
                    with _has_errors_lock:
                        _has_errors = True

            except OSError:
                break
            except Exception:
                pass
    finally:
        try:
            os.close(pipe_read_fd)
        except Exception:
            pass


def init_tee():
    """Initialize stdout/stderr tee to log file.

    Call this as early as possible, before any imports that might
    produce output (especially wx/GTK).
    """
    global _log_file, _original_stdout_fd, _original_stderr_fd
    global _stdout_thread, _stderr_thread, _stop_event

    try:
        log_path = _get_log_path()
        _log_file = open(log_path, 'a', encoding='utf-8')
        _stop_event = threading.Event()

        # Debug: write startup message directly to log file
        _log_file.write(f"=== TEE INITIALIZED, log path: {log_path} ===\n")
        _log_file.flush()

        # Set up stdout tee
        _original_stdout_fd = os.dup(1)
        stdout_pipe_read, stdout_pipe_write = os.pipe()
        os.dup2(stdout_pipe_write, 1)
        os.close(stdout_pipe_write)
        sys.stdout = os.fdopen(1, 'w', buffering=1)

        _stdout_thread = threading.Thread(
            target=_tee_thread,
            args=(stdout_pipe_read, _original_stdout_fd, _log_file, False),
            daemon=True
        )
        _stdout_thread.start()

        # Set up stderr tee
        _original_stderr_fd = os.dup(2)
        stderr_pipe_read, stderr_pipe_write = os.pipe()
        os.dup2(stderr_pipe_write, 2)
        os.close(stderr_pipe_write)
        sys.stderr = os.fdopen(2, 'w', buffering=1)

        _stderr_thread = threading.Thread(
            target=_tee_thread,
            args=(stderr_pipe_read, _original_stderr_fd, _log_file, True),
            daemon=True
        )
        _stderr_thread.start()

    except Exception:
        # If tee setup fails, continue without it
        pass


def shutdown_tee():
    """Shutdown the tee and return whether errors occurred."""
    global _log_file, _original_stdout_fd, _original_stderr_fd
    global _stdout_thread, _stderr_thread, _stop_event

    # Signal threads to stop
    if _stop_event is not None:
        _stop_event.set()

    # Flush and close current stdout/stderr to signal EOF to threads
    # This closes the write end of the pipes
    try:
        sys.stdout.flush()
        sys.stdout.close()
    except Exception:
        pass

    try:
        sys.stderr.flush()
        sys.stderr.close()
    except Exception:
        pass

    # Wait for threads (they should exit now that pipes are closed)
    if _stdout_thread is not None:
        _stdout_thread.join(timeout=1.0)
        _stdout_thread = None
    if _stderr_thread is not None:
        _stderr_thread.join(timeout=1.0)
        _stderr_thread = None

    # Restore original stdout
    if _original_stdout_fd is not None:
        try:
            os.dup2(_original_stdout_fd, 1)
            os.close(_original_stdout_fd)
            sys.stdout = os.fdopen(1, 'w', buffering=1)
        except Exception:
            pass
        _original_stdout_fd = None

    # Restore original stderr
    if _original_stderr_fd is not None:
        try:
            os.dup2(_original_stderr_fd, 2)
            os.close(_original_stderr_fd)
            sys.stderr = os.fdopen(2, 'w', buffering=1)
        except Exception:
            pass
        _original_stderr_fd = None

    # Close log file
    if _log_file is not None:
        try:
            _log_file.close()
        except Exception:
            pass
        _log_file = None

    # Return error status
    with _has_errors_lock:
        return _has_errors


def has_errors():
    """Check if any errors occurred (any stderr output)."""
    with _has_errors_lock:
        return _has_errors
